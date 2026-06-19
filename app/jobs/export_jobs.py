import csv
import io
import json
from datetime import datetime
from flask import current_app
from app import db
from app.models import ActionCorrective, EvaluationArticle, EntrepriseTexte


def export_actions_csv(entreprise_id):
    actions = ActionCorrective.query.filter_by(entreprise_id=entreprise_id).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Description', 'Statut', 'Priorite', 'Date echeance', 'Date creation'])
    for a in actions:
        writer.writerow([
            a.id,
            a.description,
            a.statut_label,
            a.priorite,
            a.date_echeance.isoformat() if a.date_echeance else '',
            a.date_creation.isoformat() if a.date_creation else '',
        ])
    return output.getvalue()


def export_conformite_json(entreprise_id):
    textes = EntrepriseTexte.query.filter_by(entreprise_id=entreprise_id).all()
    data = []
    for et in textes:
        evaluations = EvaluationArticle.query.filter_by(entreprise_texte_id=et.id).all()
        data.append({
            'texte_id': et.id,
            'texte_version_id': et.texte_version_id,
            'score_conformite': et.score_conformite,
            'statut_evaluation': et.statut_evaluation,
            'evaluations': [{
                'article_id': e.article_id,
                'conforme': e.conforme.name if e.conforme else None,
                'observation': e.observation,
                'date_evaluation': e.date_evaluation.isoformat() if e.date_evaluation else None,
            } for e in evaluations],
        })
    return json.dumps(data, ensure_ascii=False, indent=2)
