import json
import re
import secrets
import hashlib
from datetime import datetime, timedelta
from flask import render_template, flash, redirect, url_for, request, current_app, jsonify
from flask_login import login_required, current_user
from markupsafe import Markup, escape
from app import db, csrf
from app.utils.text_renderer import render_article_content
from app.models import (
    TexteReglementaire, TexteVersion, Article, Secteur, Domaine,
    ExigenceType, NiveauRisqueType,
)
from app.textes import textes
from app.utils.permissions import system_admin_required


REFERENTIEL_CHOICES = [
    ('maroc', 'Marocain'),
    ('eu', 'EU'),
    ('codex', 'Codex'),
    ('iso', 'ISO'),
    ('ifs', 'IFS'),
    ('brc', 'BRC'),
    ('autre', 'Autre'),
]
REFERENTIEL_LABELS = dict(REFERENTIEL_CHOICES)


def _normalize_column_name(value):
    text = re.sub(r'[^a-z0-9]', '', str(value or '').strip().lower())
    return text


def _parse_bool_like(value, default=False):
    if value is None or str(value).strip() == '':
        return default
    text = str(value).strip().lower()
    if text in {'1', 'true', 'vrai', 'oui', 'yes', 'y'}:
        return True
    if text in {'0', 'false', 'faux', 'non', 'no', 'n'}:
        return False
    return default


def _parse_json_date(value):
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


def _normalize_referentiel(value):
    referentiel = (value or '').strip().lower()
    if not referentiel:
        return None
    return referentiel if referentiel in REFERENTIEL_LABELS else None


def _pick_row_value(row, *candidate_keys):
    if not isinstance(row, dict) or not candidate_keys:
        return None
    normalized_map = {_normalize_column_name(key): key for key in row.keys()}
    for candidate in candidate_keys:
        source_key = normalized_map.get(_normalize_column_name(candidate))
        if source_key is None:
            continue
        value = row.get(source_key)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def _normalize_article_keywords(value):
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


def _map_exigence(value):
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


def _map_niveau_risque(value):
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


def _process_json_bundle_payload(payload, dry_run=False, link_to_enterprise=False):
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
        type_obligation = str(row.get('TYPE_OBLIGATION') or '').strip()
        if type_obligation:
            exigence_value = type_obligation
        else:
            exigence_value = 'OBLIGATION' if _parse_bool_like(row.get('OBLIGATION'), default=False) else 'INFORMATION'
        articles_data.append({
            'article_uid': str(row.get('ARTICLE_UID') or '').strip() or f"ART-{row_idx:05d}",
            'numero_article': row.get('numero_article'),
            'article_code': article_raw or None,
            'contenu': contenu_raw or None,
            'exigence_type': exigence_value,
            'niveau_risque': _pick_row_value(row, 'RISQUE', 'NIVEAU_RISQUE'),
            'resume_article': str(_pick_row_value(row, 'RESUME', 'RESUME_ARTICLE') or '').strip() or None,
            'acteur': str(_pick_row_value(row, 'ACTEUR', 'acteur') or '').strip() or None,
            'domaine': str(_pick_row_value(row, 'DOMAINE', 'domaine') or '').strip() or None,
            'mots_cles': _normalize_article_keywords(_pick_row_value(row, 'MOTS_CLES', 'MOTS CLES', 'mots_cles')),
            'preuve_conformite': str(
                _pick_row_value(row, 'PREUVE_CONFORMITE', 'preuve_conformite', 'PREUVE') or ''
            ).strip() or None,
            'explication_detaillee': str(
                _pick_row_value(row, 'EXPLICATION_DETAILLEE', 'explication_detaillee', 'EXPLICATION') or ''
            ).strip() or None,
        })
    code = str(texte_data.get('code') or '').strip()
    titre = str(texte_data.get('titre') or '').strip()
    type_texte = str(texte_data.get('type') or '').strip().lower()
    numero_version = str(version_data.get('numero_version') or '').strip()
    date_publication = _parse_json_date(version_data.get('date_publication'))
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
        return {
            'success': True, 'errors': [], 'warnings': warnings,
            'summary': {'articles': 0}, 'texte_id': existing_texte.id,
        }
    article_rows = []
    article_numbers = set()
    for idx, item in enumerate(articles_data, start=1):
        contenu = str(item.get('contenu') or '').strip()
        if not contenu:
            warnings.append(f"articles[{idx}].contenu manquant - ligne ignoree")
            continue
        exigence_member, exigence_error = _map_exigence(item.get('exigence_type'))
        risque_member, risque_error = _map_niveau_risque(item.get('niveau_risque'))
        if exigence_error:
            warnings.append(f"articles[{idx}].exigence_type: {exigence_error} - ligne ignoree")
            continue
        if risque_error:
            warnings.append(f"articles[{idx}].niveau_risque: {risque_error} - ligne ignoree")
            continue
        numero_article = item.get('numero_article')
        if numero_article is not None:
            try:
                numero_article = int(numero_article)
            except (TypeError, ValueError):
                numero_article = None
        if numero_article is not None:
            if numero_article in article_numbers:
                errors.append(f"articles[{idx}].numero_article duplique ({numero_article})")
                continue
            article_numbers.add(numero_article)
        article_rows.append({
            'article_uid': item['article_uid'],
            'numero_article': numero_article,
            'article_code': item.get('article_code'),
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
    if not article_rows and not warnings:
        warnings.append("Aucun article valide detecte dans 'rows'.")
    summary = {'articles': len(article_rows), 'warnings': len(warnings)}
    if errors:
        return {'success': False, 'errors': errors, 'warnings': warnings, 'summary': summary}
    if dry_run:
        return {'success': True, 'errors': [], 'warnings': warnings, 'summary': summary}
    try:
        texte = TexteReglementaire(
            code=code,
            titre=titre,
            description=str(texte_data.get('description') or '').strip() or None,
            type=type_texte,
            domaine=str(texte_data.get('domaine') or '').strip() or None,
            sousdomaine=str(texte_data.get('sousdomaine') or '').strip() or None,
            theme=str(texte_data.get('theme') or '').strip() or None,
            referentiel=_normalize_referentiel(texte_data.get('referentiel')),
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
        preambule_value = _pick_row_value(version_data, 'preambule', 'introduction', 'intro')
        preambule = str(preambule_value or '').strip() or None
        version = TexteVersion(
            texte_id=texte.id,
            numero_version=numero_version,
            date_publication=date_publication,
            statut=str(version_data.get('statut') or 'active').strip() or 'active',
            commentaire_version=str(version_data.get('commentaire_version') or '').strip() or None,
            preambule=preambule,
            cree_par=current_user.id,
        )
        db.session.add(version)
        db.session.flush()
        texte.version_active_id = version.id
        for item in article_rows:
            raw_contenu = str(item['contenu'] or '')
            if raw_contenu:
                rendered = render_article_content(raw_contenu)
                contenu_clean = Markup(rendered)
            else:
                contenu_clean = None
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
        db.session.commit()
        if link_to_enterprise and current_user.entreprise_id and version:
            from app.models import EntrepriseTexte
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
                    responsable_id=current_user.id,
                )
                db.session.add(et)
                db.session.commit()
                warnings.append(f"Texte lie a l'entreprise pour evaluation.")
        return {
            'success': True, 'errors': [], 'warnings': warnings,
            'summary': summary, 'texte_id': texte.id,
        }
    except Exception as exc:
        db.session.rollback()
        return {
            'success': False, 'errors': [str(exc)], 'warnings': warnings,
            'summary': summary,
        }


def _process_json_bundle_entries(payload_entries, dry_run=False, link_to_enterprise=False):
    successes = []
    failures = []
    total_articles = 0
    for entry in payload_entries:
        filename = entry.get('filename') or 'fichier.json'
        payload = entry.get('payload') or {}
        result = _process_json_bundle_payload(payload, dry_run=dry_run, link_to_enterprise=link_to_enterprise)
        if result['success']:
            successes.append({'filename': filename, 'result': result, 'payload': payload})
            total_articles += int((result.get('summary') or {}).get('articles') or 0)
            continue
        excerpt = '; '.join((result.get('errors') or [])[:3])
        failures.append(f"{filename}: {excerpt}")
    return {
        'successes': successes,
        'failures': failures,
        'total_articles': total_articles,
    }


_pending_json_import_store = {}


@textes.route('/import_json', methods=['GET', 'POST'])
@login_required
@system_admin_required
@csrf.exempt
def import_json():
    if request.method == 'POST':
        all_files = request.files.getlist('files')
        valid_files = [f for f in all_files if f and f.filename and f.filename.strip()]
        if not valid_files:
            flash('Aucun fichier JSON fourni.', 'danger')
            return redirect(url_for('textes.import_json'))
        payloads = []
        for f in valid_files:
            try:
                content = f.read()
                payload = json.loads(content.decode('utf-8-sig'))
                if not isinstance(payload, dict):
                    flash(f'{f.filename}: objet JSON racine attendu.', 'danger')
                    return redirect(url_for('textes.import_json'))
                payloads.append({'filename': f.filename.strip(), 'payload': payload})
            except json.JSONDecodeError as exc:
                flash(f'{f.filename}: JSON invalide: {exc}', 'danger')
                return redirect(url_for('textes.import_json'))
        link_to_enterprise = request.form.get('link_to_enterprise') == '1'
        preview = request.form.get('preview')
        if preview:
            processing_summary = _process_json_bundle_entries(payloads, dry_run=True)
            if processing_summary['failures']:
                flash(f"Erreurs de preview: {'; '.join(processing_summary['failures'][:3])}", 'danger')
                return redirect(url_for('textes.import_json'))
            token = secrets.token_urlsafe(24)
            _pending_json_import_store[token] = {
                'created_at': datetime.utcnow(),
                'user_id': current_user.id,
                'payloads': payloads,
                'link_to_enterprise': link_to_enterprise,
                'summary': {
                    'files': len(processing_summary['successes']),
                    'articles': processing_summary['total_articles'],
                },
            }
            textes_list = TexteReglementaire.query.all()
            domaines = Domaine.query.order_by(Domaine.nom).all()
            return render_template(
                'textes/import_preview.html',
                token=token,
                summary=_pending_json_import_store[token]['summary'],
                payloads=payloads,
                textes_list=textes_list,
                domaines=domaines,
                link_to_enterprise=link_to_enterprise,
            )
        link_to_enterprise = request.form.get('link_to_enterprise') == '1'
        processing_summary = _process_json_bundle_entries(payloads, dry_run=False, link_to_enterprise=link_to_enterprise)
        if not processing_summary['successes']:
            flash(f"Aucun import effectue: {'; '.join(processing_summary['failures'][:3])}", 'danger')
            return redirect(url_for('textes.import_json'))
        flash(
            f"Import JSON termine: {len(processing_summary['successes'])} fichier(s), "
            f"{processing_summary['total_articles']} article(s) cree(s).",
            'success',
        )
        if processing_summary['failures']:
            flash(f"Fichier(s) en erreur: {'; '.join(processing_summary['failures'][:3])}", 'warning')
        if len(processing_summary['successes']) == 1:
            return redirect(url_for('textes.detail', texte_id=processing_summary['successes'][0]['result']['texte_id']))
        return redirect(url_for('textes.index'))
    domaines = Domaine.query.order_by(Domaine.nom).all()
    return render_template('textes/import_json.html', domaines=domaines)


@textes.route('/import_json/confirm', methods=['POST'])
@login_required
@system_admin_required
@csrf.exempt
def confirm_import_json():
    token = (request.form.get('preview_token') or '').strip()
    if not token:
        flash('Token de preview manquant.', 'danger')
        return redirect(url_for('textes.import_json'))
    pending = _pending_json_import_store.get(token)
    if not pending:
        flash('Preview expiree ou introuvable.', 'warning')
        return redirect(url_for('textes.import_json'))
    if pending.get('user_id') != current_user.id:
        flash('Preview invalide pour cet utilisateur.', 'danger')
        return redirect(url_for('textes.import_json'))
    payloads = pending.get('payloads') or []
    link_to_enterprise = pending.get('link_to_enterprise', False)
    _pending_json_import_store.pop(token, None)
    processing_summary = _process_json_bundle_entries(payloads, dry_run=False, link_to_enterprise=link_to_enterprise)
    if not processing_summary['successes']:
        flash(f"Aucun import effectue: {'; '.join(processing_summary['failures'][:3])}", 'danger')
        return redirect(url_for('textes.import_json'))
    flash(
        f"Import confirme: {len(processing_summary['successes'])} fichier(s), "
        f"{processing_summary['total_articles']} article(s) cree(s).",
        'success',
    )
    if processing_summary['failures']:
        flash(f"Fichier(s) en erreur: {'; '.join(processing_summary['failures'][:3])}", 'warning')
    if len(processing_summary['successes']) == 1:
        return redirect(url_for('textes.detail', texte_id=processing_summary['successes'][0]['result']['texte_id']))
    return redirect(url_for('textes.index'))


@textes.route('/import_json/template')
@login_required
@system_admin_required
def download_json_template():
    sample = {
        'schema_version': '1.0',
        'texte': {
            'code': 'TXT-JSON-001',
            'titre': 'Exemple texte import JSON',
            'description': 'Template JSON universel compact',
            'type': 'loi',
            'domaine': 'HSE',
            'sousdomaine': 'Conformite',
            'theme': 'Reglementation',
            'referentiel': 'maroc',
            'secteurs': ['Industrie', 'Agroalimentaire'],
        },
        'version': {
            'numero_version': '1',
            'date_publication': '2026-01-15',
            'statut': 'active',
            'commentaire_version': 'Import initial JSON',
            'preambule': 'Preambule du texte...',
        },
        'rows': [
            {
                'ARTICLE': '1',
                'numero_article': 1,
                'CONTENU': 'Mettre en place une procedure de controle hebdomadaire.',
                'TYPE_OBLIGATION': 'OBLIGATION',
                'ACTEUR': 'employeur',
                'DOMAINE': 'HSE',
                'RISQUE': 'MOYEN',
                'MOTS_CLES': ['controle', 'procedure', 'registre'],
                'RESUME': 'Controle hebdomadaire obligatoire.',
                'PREUVE_CONFORMITE': 'Registre signe + rapports.',
                'EXPLICATION_DETAILLEE': 'Cet article impose un controle hebdomadaire formalise.',
            },
            {
                'ARTICLE': '2',
                'numero_article': 2,
                'CONTENU': 'Conserver les rapports 5 ans.',
                'TYPE_OBLIGATION': 'RECOMMANDATION',
                'ACTEUR': 'employeur',
                'DOMAINE': 'HSE',
                'RISQUE': 'FAIBLE',
                'MOTS_CLES': ['archivage', 'conservation'],
                'RESUME': 'Conservation documentaire recommandee.',
                'PREUVE_CONFORMITE': "Politique d'archivage + preuve de sauvegarde.",
                'EXPLICATION_DETAILLEE': "Cette ligne illustre un enregistrement simple.",
            },
        ],
    }
    response = current_app.response_class(
        json.dumps(sample, ensure_ascii=True, indent=2),
        mimetype='application/json',
    )
    response.headers['Content-Disposition'] = 'attachment; filename="modele_import_texte.json"'
    return response
