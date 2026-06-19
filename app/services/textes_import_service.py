import json
import re
import hashlib
from datetime import datetime
from flask import current_app
from markupsafe import Markup
from app import db
from app.utils.text_renderer import render_article_content
from app.models import (
    TexteReglementaire, TexteVersion, Article, Secteur, Domaine,
    ExigenceType, NiveauRisqueType,
)


REFERENTIEL_CHOICES = {
    'maroc': 'Marocain', 'eu': 'EU', 'codex': 'Codex',
    'iso': 'ISO', 'ifs': 'IFS', 'brc': 'BRC', 'autre': 'Autre',
}
REFERENTIEL_LABELS = dict(REFERENTIEL_CHOICES)


def normalize_column_name(value):
    return re.sub(r'[^a-z0-9]', '', str(value or '').strip().lower())


def parse_bool_like(value, default=False):
    if value is None or str(value).strip() == '':
        return default
    text = str(value).strip().lower()
    if text in {'1', 'true', 'vrai', 'oui', 'yes', 'y'}:
        return True
    if text in {'0', 'false', 'faux', 'non', 'no', 'n'}:
        return False
    return default


def parse_json_date(value):
    if value is None or str(value).strip() == '':
        return None
    text = str(value).strip()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m', '%Y'):
        try:
            dt = datetime.strptime(text, fmt)
            if fmt in ('%Y', '%Y-%m'):
                dt = dt.replace(day=1)
            return dt.date()
        except ValueError:
            continue
    return None


def normalize_referentiel(value):
    referentiel = (value or '').strip().lower()
    if not referentiel:
        return None
    return referentiel if referentiel in REFERENTIEL_LABELS else None


def pick_row_value(row, *candidate_keys):
    if not isinstance(row, dict) or not candidate_keys:
        return None
    normalized_map = {normalize_column_name(key): key for key in row.keys()}
    for candidate in candidate_keys:
        source_key = normalized_map.get(normalize_column_name(candidate))
        if source_key is None:
            continue
        value = row.get(source_key)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def normalize_article_keywords(value):
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        keywords = [str(item).strip() for item in value if str(item).strip()]
        return keywords or None
    text = str(value).strip()
    if not text:
        return None
    if text.startswith('[') and text.endswith(']'):
        try:
            parsed = json.loads(text)
        except Exception:
            parsed = None
        if isinstance(parsed, list):
            keywords = [str(item).strip() for item in parsed if str(item).strip()]
            return keywords or None
    keywords = [part.strip() for part in re.split(r'[,;]+', text) if part.strip()]
    return keywords or [text]


def map_exigence(value):
    text = str(value or '').strip().upper()
    mapping = {
        'OBLIGATION': ExigenceType.OBLIGATION,
        'OBLIGATOIRE': ExigenceType.OBLIGATION,
        'RECOMMANDATION': ExigenceType.RECOMMANDATION,
        'RECOMMANDE': ExigenceType.RECOMMANDATION,
        'INTERDICTION': ExigenceType.INTERDICTION,
        'INTERDIT': ExigenceType.INTERDICTION,
        'INFORMATION': ExigenceType.INFORMATION,
        'DEFINITION': ExigenceType.DEFINITION,
    }
    result = mapping.get(text)
    return result, None if result else (None, f"'{value}' non reconnu")


def map_niveau_risque(value):
    text = str(value or '').strip().upper()
    mapping = {
        'FAIBLE': NiveauRisqueType.FAIBLE,
        'MOYEN': NiveauRisqueType.MOYEN,
        'ELEVE': NiveauRisqueType.ELEVE,
        'ELEVÉ': NiveauRisqueType.ELEVE,
        'CRITIQUE': NiveauRisqueType.CRITIQUE,
    }
    result = mapping.get(text)
    return result, None if result else (None, f"'{value}' non reconnu")


def process_json_bundle_payload(payload, current_user_id, dry_run=False, link_to_enterprise=False):
    from app.models import EntrepriseTexte
    errors = []
    warnings = []
    texte_data = payload.get('texte') if isinstance(payload.get('texte'), dict) else {}
    version_data = payload.get('version') if isinstance(payload.get('version'), dict) else {}
    rows_data = None
    for key in ('rows', 'records', 'lignes', 'articles'):
        candidate = payload.get(key)
        if isinstance(candidate, list):
            rows_data = candidate
            break
    if rows_data is None:
        rows_data = []
    if not rows_data:
        errors.append("Le payload JSON doit contenir un tableau 'rows' ou 'articles' non vide.")
    articles_data = []
    for row_idx, row in enumerate(rows_data, start=1):
        if not isinstance(row, dict):
            errors.append(f"rows[{row_idx}] invalide: objet attendu")
            continue
        article_raw = str(row.get('ARTICLE') or '').strip()
        contenu_raw = str(row.get('CONTENU') or '').strip()
        if not article_raw and not contenu_raw:
            continue
        articles_data.append({
            'article_uid': str(row.get('ARTICLE_UID') or '').strip() or f"ART-{row_idx:05d}",
            'numero_article': row.get('numero_article'),
            'contenu': contenu_raw or None,
            'exigence_type': _resolve_exigence(row),
            'niveau_risque': pick_row_value(row, 'RISQUE', 'NIVEAU_RISQUE'),
            'resume_article': str(pick_row_value(row, 'RESUME', 'RESUME_ARTICLE') or '').strip() or None,
            'acteur': str(pick_row_value(row, 'ACTEUR', 'acteur') or '').strip() or None,
            'domaine': str(pick_row_value(row, 'DOMAINE', 'domaine') or '').strip() or None,
            'mots_cles': normalize_article_keywords(pick_row_value(row, 'MOTS_CLES', 'MOTS CLES', 'mots_cles')),
            'preuve_conformite': str(pick_row_value(row, 'PREUVE_CONFORMITE', 'preuve_conformite', 'PREUVE') or '').strip() or None,
            'explication_detaillee': str(pick_row_value(row, 'EXPLICATION_DETAILLEE', 'explication_detaillee', 'EXPLICATION') or '').strip() or None,
        })
    return _save_bundle(texte_data, version_data, articles_data, current_user_id, errors, warnings, dry_run, link_to_enterprise)


def _resolve_exigence(row):
    type_obligation = str(row.get('TYPE_OBLIGATION') or '').strip()
    if type_obligation:
        return type_obligation
    return 'OBLIGATION' if parse_bool_like(row.get('OBLIGATION'), default=False) else 'INFORMATION'


def _save_bundle(texte_data, version_data, articles_data, current_user_id, errors, warnings, dry_run, link_to_enterprise):
    from app.models import EntrepriseTexte
    code = str(texte_data.get('code') or '').strip()
    titre = str(texte_data.get('titre') or '').strip()
    type_texte = str(texte_data.get('type') or '').strip().lower()
    numero_version = str(version_data.get('numero_version') or '').strip()
    date_publication = parse_json_date(version_data.get('date_publication'))
    if not code:
        errors.append('texte.code obligatoire')
    if not titre:
        errors.append('texte.titre obligatoire')
    if not type_texte:
        errors.append('texte.type obligatoire')
    if not numero_version:
        errors.append('version.numero_version obligatoire')
    if not date_publication:
        warnings.append('version.date_publication invalide ou manquante')
    if errors:
        return {'success': False, 'errors': errors, 'warnings': warnings, 'summary': {'articles': 0}}
    existing_texte = TexteReglementaire.query.filter_by(code=code).first()
    if existing_texte:
        warnings.append(f"texte.code deja existant ({code}) - import saute.")
        return {'success': True, 'errors': [], 'warnings': warnings, 'summary': {'articles': 0}, 'texte_id': existing_texte.id}
    article_rows = []
    article_numbers = set()
    for idx, item in enumerate(articles_data, start=1):
        contenu = str(item.get('contenu') or '').strip()
        if not contenu:
            warnings.append(f"articles[{idx}].contenu manquant - ligne ignoree")
            continue
        exigence_member, exigence_error = map_exigence(item.get('exigence_type'))
        risque_member, risque_error = map_niveau_risque(item.get('niveau_risque'))
        if exigence_error:
            warnings.append(f"articles[{idx}].exigence_type: {exigence_error} - ligne ignoree")
            continue
        if risque_error:
            warnings.append(f"articles[{idx}].niveau_risque: {risque_error} - ligne ignoree")
            continue
        article_rows.append({
            'numero_article': item.get('numero_article'),
            'contenu': contenu,
            'exigence_type': exigence_member or ExigenceType.INFORMATION,
            'niveau_risque': risque_member or NiveauRisqueType.MOYEN,
            'resume_article': item.get('resume_article'),
            'acteur': item.get('acteur'),
            'domaine': item.get('domaine'),
            'mots_cles': item.get('mots_cles'),
            'preuve_conformite': item.get('preuve_conformite'),
            'explication_detaillee': item.get('explication_detaillee'),
        })
    summary = {'articles': len(article_rows), 'warnings': len(warnings)}
    if errors or dry_run:
        return {'success': len(errors) == 0, 'errors': errors, 'warnings': warnings, 'summary': summary}
    try:
        texte, version = _create_texte_and_version(texte_data, version_data, code, titre, type_texte, numero_version, date_publication)
        _create_articles(version, article_rows)
        db.session.commit()
        if link_to_enterprise:
            _link_to_enterprise(version, current_user_id)
        return {'success': True, 'errors': [], 'warnings': warnings, 'summary': summary, 'texte_id': texte.id}
    except Exception as exc:
        db.session.rollback()
        return {'success': False, 'errors': [str(exc)], 'warnings': warnings, 'summary': summary}


def _create_texte_and_version(texte_data, version_data, code, titre, type_texte, numero_version, date_publication):
    texte = TexteReglementaire(
        code=code, titre=titre,
        description=str(texte_data.get('description') or '').strip() or None,
        type=type_texte,
        domaine=str(texte_data.get('domaine') or '').strip() or None,
        sousdomaine=str(texte_data.get('sousdomaine') or '').strip() or None,
        theme=str(texte_data.get('theme') or '').strip() or None,
        referentiel=normalize_referentiel(texte_data.get('referentiel')),
    )
    db.session.add(texte)
    db.session.flush()
    sectors_raw = texte_data.get('secteurs') or []
    if isinstance(sectors_raw, list):
        existing_sectors = {(s.nom or '').strip().lower(): s for s in Secteur.query.all()}
        for raw_name in sectors_raw:
            name = str(raw_name or '').strip()
            if not name:
                continue
            key = name.lower()
            sector = existing_sectors.get(key)
            if not sector:
                sector = Secteur(nom=name)
                db.session.add(sector)
                db.session.flush()
                existing_sectors[key] = sector
            if sector not in texte.secteurs:
                texte.secteurs.append(sector)
    preambule = str(pick_row_value(version_data, 'preambule', 'introduction', 'intro') or '').strip() or None
    version = TexteVersion(
        texte_id=texte.id, numero_version=numero_version, date_publication=date_publication,
        statut=str(version_data.get('statut') or 'active').strip() or 'active',
        commentaire_version=str(version_data.get('commentaire_version') or '').strip() or None,
        preambule=preambule,
    )
    db.session.add(version)
    db.session.flush()
    texte.version_active_id = version.id
    return texte, version


def _create_articles(version, article_rows):
    for item in article_rows:
        raw_contenu = str(item['contenu'] or '')
        contenu_clean = Markup(render_article_content(raw_contenu)) if raw_contenu else None
        article = Article(
            texte_version_id=version.id,
            numero_article=item['numero_article'],
            contenu=contenu_clean,
            exigence_type=item['exigence_type'],
            niveau_risque=item['niveau_risque'],
            resume_article=item['resume_article'],
            explication_detaillee=item.get('explication_detaillee'),
            preuve_conformite=item.get('preuve_conformite'),
            acteur=item.get('acteur'),
            domaine=item.get('domaine'),
            mots_cles=item.get('mots_cles'),
            hash_contenu=hashlib.sha256(raw_contenu.encode('utf-8')).hexdigest(),
        )
        db.session.add(article)


def _link_to_enterprise(version, user_id):
    from app.models import EntrepriseTexte
    from flask_login import current_user
    if not current_user.is_authenticated or not current_user.entreprise_id:
        return
    existing_link = EntrepriseTexte.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        texte_version_id=version.id,
    ).first()
    if not existing_link:
        et = EntrepriseTexte(
            entreprise_id=current_user.entreprise_id,
            texte_version_id=version.id,
            statut_obligation='VOLONTAIRE',
            motif_obligation='Import JSON',
            mode_evaluation='EVALUATION_ADHOC',
            responsable_id=user_id,
        )
        db.session.add(et)
