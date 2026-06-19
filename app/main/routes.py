from flask import render_template, redirect, url_for, session, request, abort, jsonify, Response
from flask_login import login_required, current_user
from app import db
from app.models import Entreprise, ActionCorrective, ProofMaster, Audit, Utilisateur, Indicateur, Ticket, SubscriptionPlan
from app.main import main
from app.utils.domaine_switch import set_domaine_actif
from app.utils.permissions import has_permission
from app.models import Notification
from datetime import date
import platform


@main.route('/health')
def health():
    try:
        db.session.execute(db.text('SELECT 1'))
        db_status = 'ok'
    except Exception:
        db_status = 'error'
    return jsonify({
        'status': 'ok',
        'database': db_status,
        'python': platform.python_version(),
        'flask': '2.3.3',
    })


@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.tableau_de_bord'))
    slots_json = '{}'
    plans = SubscriptionPlan.query.order_by(SubscriptionPlan.price_mad).all()
    try:
        from app.demo.routes import _generer_creneaux_libres, _slots_to_json, _grouper_par_jour
        creneaux = _generer_creneaux_libres()
        creneaux_par_jour = _grouper_par_jour(creneaux)
        slots_json = _slots_to_json(creneaux_par_jour)
    except Exception:
        pass

    all_features = {}
    for p in plans:
        if p.features:
            for k, v in p.features.items():
                if v and k not in all_features:
                    all_features[k] = True

    features_icons = {
        'veille_reglementaire': {'icon': 'fas fa-satellite-dish', 'color': '#06b6d4', 'bg': 'rgba(6,182,212,.1)'},
        'notifications_reglementaires_par_email': {'icon': 'fas fa-envelope', 'color': '#f59e0b', 'bg': 'rgba(245,158,11,.1)'},
        'export_excel_pdf_des_rapports': {'icon': 'fas fa-file-export', 'color': '#10b981', 'bg': 'rgba(16,185,129,.1)'},
        'evaluation_des_textes_iso_brc_ifs': {'icon': 'fas fa-clipboard-check', 'color': '#3b82f6', 'bg': 'rgba(59,130,246,.1)'},
        'support': {'icon': 'fas fa-headset', 'color': '#8b5cf6', 'bg': 'rgba(139,92,246,.1)'},
        'analytics_avances_tableaux_de_bord': {'icon': 'fas fa-chart-bar', 'color': '#ec4899', 'bg': 'rgba(236,72,153,.1)'},
        'formation_onboarding_dedies': {'icon': 'fas fa-graduation-cap', 'color': '#06b6d4', 'bg': 'rgba(6,182,212,.1)'},
    }
    features_desc = {
        'veille_reglementaire': 'Suivez les évolutions réglementaires et recevez des alertes personnalisées.',
        'notifications_reglementaires_par_email': 'Notifications automatiques par email pour ne rien manquer.',
        'export_excel_pdf_des_rapports': 'Exportez vos rapports et tableaux de bord en PDF et Excel.',
        'evaluation_des_textes_iso_brc_ifs': 'Évaluez vos textes réglementaires (ISO, BRC, IFS…).',
        'support': 'Assistance technique dédiée et réactive.',
        'analytics_avances_tableaux_de_bord': 'Tableaux de bord avancés et indicateurs de performance.',
        'formation_onboarding_dedies': 'Formation et accompagnement pour votre équipe.',
    }

    features = []
    for k in all_features:
        meta = features_icons.get(k, {'icon': 'fas fa-check', 'color': '#6b7280', 'bg': 'rgba(107,114,128,.1)'})
        features.append({
            'icon': meta['icon'],
            'color': meta['color'],
            'bg': meta['bg'],
            'title': k.replace('_', ' ').title(),
            'description': features_desc.get(k, ''),
        })

    features_labels = {k: k.replace('_', ' ').title() for k in all_features}

    return render_template('landing.html', slots_json=slots_json, plans=plans, features=features, features_labels=features_labels)


@main.route('/tableau-de-bord')
@login_required
@has_permission('actions.voir')
def tableau_de_bord():
    entreprise = db.session.get(Entreprise, current_user.entreprise_id)
    domaine = session.get('domaine_actif', 'hse')
    return render_template('main/dashboard.html', entreprise=entreprise, domaine=domaine)


@main.route('/api/stats')
@login_required
@has_permission('actions.voir')
def api_stats():
    domaine = session.get('domaine_actif', 'hse')
    eid = current_user.entreprise_id
    today = date.today()

    total_actions = ActionCorrective.query.filter_by(
        entreprise_id=eid, domaine=domaine
    ).count()

    actions_en_cours = ActionCorrective.query.filter_by(
        entreprise_id=eid, domaine=domaine, statut='EN_COURS'
    ).count()

    actions_en_retard = ActionCorrective.query.filter(
        ActionCorrective.entreprise_id == eid,
        ActionCorrective.domaine == domaine,
        ActionCorrective.statut.notin_(['SOLDE', 'ANNULE']),
        ActionCorrective.date_echeance < today,
    ).count()

    total_documents = ProofMaster.query.filter_by(
        entreprise_id=eid, domaine=domaine, statut='ACTIF'
    ).count()

    total_audits = Audit.query.filter_by(
        entreprise_id=eid, domaine=domaine
    ).count()

    total_users = Utilisateur.query.filter_by(
        entreprise_id=eid
    ).count()

    return jsonify(
        total_actions=total_actions,
        actions_en_cours=actions_en_cours,
        actions_en_retard=actions_en_retard,
        total_documents=total_documents,
        total_audits=total_audits,
        total_users=total_users,
    )


@main.route('/switch-domaine/<domaine>')
@login_required
def switch_domaine(domaine):
    if domaine not in ('hse', 'qualite'):
        abort(400)
    entreprise = db.session.get(Entreprise, current_user.entreprise_id)
    modules = entreprise.modules_actifs or ['hse']
    if domaine not in modules:
        abort(403)
    set_domaine_actif(domaine)
    return redirect(request.referrer or url_for('main.tableau_de_bord'))


@main.route('/api/notifications')
@login_required
def api_notifications():
    notifs = Notification.query.filter_by(utilisateur_id=current_user.id)\
        .order_by(Notification.lu.asc(), Notification.date_envoi.desc()).limit(20).all()
    return jsonify([{
        'id': n.id,
        'type': n.type,
        'message': n.message,
        'date_envoi': n.date_envoi.isoformat() if n.date_envoi else None,
        'lu': n.lu,
    } for n in notifs])


@main.route('/api/notifications/<int:id>/read', methods=['POST'])
@login_required
def api_notification_read(id):
    notif = Notification.query.filter_by(id=id, utilisateur_id=current_user.id).first_or_404()
    notif.lu = True
    db.session.commit()
    return jsonify({'success': True})


@main.route('/api/notifications/read-all', methods=['POST'])
@login_required
def api_notification_read_all():
    Notification.query.filter_by(utilisateur_id=current_user.id, lu=False).update({'lu': True})
    db.session.commit()
    return jsonify({'success': True})


@main.route('/search')
@login_required
def search():
    q = request.args.get('q', '').strip()
    results = {}
    if q:
        pattern = f'%{q}%'
        eid = current_user.entreprise_id

        actions = ActionCorrective.query.filter(
            ActionCorrective.entreprise_id == eid,
            ActionCorrective.description.ilike(pattern)
        ).limit(10).all()
        if actions:
            results['Actions'] = [{'id': a.id, 'title': a.description[:80], 'url': url_for('actions.detail_action', action_id=a.id)} for a in actions]

        audits = Audit.query.filter(
            Audit.entreprise_id == eid,
            db.or_(Audit.type.ilike(pattern), Audit.commentaire.ilike(pattern))
        ).limit(10).all()
        if audits:
            results['Audits'] = [{'id': a.id, 'title': a.type or f'Audit #{a.id}', 'url': url_for('audit.detail', audit_id=a.id)} for a in audits]

        from app.models import TexteReglementaire
        textes = TexteReglementaire.query.filter(TexteReglementaire.titre.ilike(pattern)).limit(10).all()
        if textes:
            results['Textes'] = [{'id': t.id, 'title': t.titre, 'url': url_for('textes.detail', texte_id=t.id)} for t in textes]

        indicateurs = Indicateur.query.filter(Indicateur.nom.ilike(pattern)).limit(10).all()
        if indicateurs:
            results['Indicateurs'] = [{'id': i.id, 'title': i.nom, 'url': url_for('indicateurs.detail', indicateur_id=i.id)} for i in indicateurs]

        tickets = Ticket.query.filter(
            Ticket.entreprise_id == eid,
            Ticket.description.ilike(pattern)
        ).limit(10).all()
        if tickets:
            results['Tickets'] = [{'id': t.id, 'title': t.sujet or t.description[:80], 'url': url_for('support.detail_ticket', ticket_id=t.id)} for t in tickets]

    return render_template('main/search.html', results=results, query=q)


@main.route('/api/alerts/trigger', methods=['POST'])
@login_required
def api_trigger_alerts():
    """Déclenche manuellement les alertes (admin only)."""
    if not current_user.role or not current_user.role.est_systeme:
        abort(403)
    from app.services.alert_engine import run_daily_alerts
    results = run_daily_alerts()
    return jsonify({'success': True, 'results': results})


@main.route('/export/<module>')
@login_required
def export_module(module):
    """Export Excel pour un module donné."""
    from app.services.report_service import (
        export_actions_excel, export_audits_excel, export_nc_excel, export_risques_excel
    )
    eid = current_user.entreprise_id
    domaine = session.get('domaine_actif', 'hse')

    exporters = {
        'actions': lambda: export_actions_excel(eid, domaine),
        'audits': lambda: export_audits_excel(eid, domaine),
        'nc': lambda: export_nc_excel(eid, domaine),
        'risques': lambda: export_risques_excel(eid),
    }
    if module not in exporters:
        abort(404)
    return exporters[module]()
