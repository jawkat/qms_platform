from flask import render_template, redirect, url_for, session, request, abort, jsonify, Response
from flask_login import login_required, current_user
from app import db
from app.models import Entreprise, ActionCorrective, ProofMaster, Audit, Utilisateur, Indicateur, Ticket, SubscriptionPlan
from app.main import main
from app.utils.domaine_switch import set_domaine_actif
from app.utils.permissions import has_permission
from app.models import Notification
from app.schemas.users import NotificationSchema
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


@main.route('/force-error')
@login_required
def force_error():
    """Route de test pour simulate une erreur 500."""
    raise Exception("Test de remontée d'incident technique (Bug Bug !)")


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

    features = [
        {'icon': 'fas fa-satellite-dish', 'color': '#06b6d4', 'bg': 'rgba(6,182,212,.1)',
         'title': 'Veille réglementaire & Conformité',
         'description': 'Textes légaux, normes ISO, évaluation de conformité avec alertes personnalisées.'},
        {'icon': 'fas fa-exclamation-triangle', 'color': '#ef4444', 'bg': 'rgba(239,68,68,.1)',
         'title': 'Non-Conformités & CAPA',
         'description': 'Déclaration des écarts, analyse Ishikawa, actions correctives et préventives.'},
        {'icon': 'fas fa-clipboard-check', 'color': '#8b5cf6', 'bg': 'rgba(139,92,246,.1)',
         'title': 'Audits & Inspections',
         'description': 'Programmes d\'audit, checklists, constatations et rapports de clôture.'},
        {'icon': 'fas fa-graduation-cap', 'color': '#10b981', 'bg': 'rgba(16,185,129,.1)',
         'title': 'Formations & Compétences',
         'description': 'Catalogue, sessions, présences, habilitations et matrice de polyvalence.'},
        {'icon': 'fas fa-folder-open', 'color': '#f59e0b', 'bg': 'rgba(245,158,11,.1)',
         'title': 'GED & Documentation',
         'description': 'Dépôt, versions, workflow d\'approbation, diffusion contrôlée et archivage.'},
        {'icon': 'fas fa-hard-hat', 'color': '#f97316', 'bg': 'rgba(249,115,22,.1)',
         'title': 'HSE & Environnement',
         'description': 'Incidents, EPI, DUERP, aspects environnementaux et gestion des déchets.'},
        {'icon': 'fas fa-utensils', 'color': '#ec4899', 'bg': 'rgba(236,72,153,.1)',
         'title': 'HACCP & Sécurité Aliments',
         'description': 'CCP, PRP, analyse des dangers, traçabilité, allergènes et plan de contrôle.'},
        {'icon': 'fas fa-chart-bar', 'color': '#3b82f6', 'bg': 'rgba(59,130,246,.1)',
         'title': 'Performance & Tableaux de bord',
         'description': 'KPI en temps réel, rapports automatiques, export PDF/Excel et tendances.'},
        {'icon': 'fas fa-project-diagram', 'color': '#14b8a6', 'bg': 'rgba(20,184,166,.1)',
         'title': 'Processus & Workflow',
         'description': 'Cartographie BPMN, fiches processus, workflows automatisés et validation.'},
        {'icon': 'fas fa-users', 'color': '#6366f1', 'bg': 'rgba(99,102,241,.1)',
         'title': 'RH QHSE & Compétences',
         'description': 'Employés, organigramme, affectations, EPI et suivi RH qualité.'},
        {'icon': 'fas fa-truck', 'color': '#a855f7', 'bg': 'rgba(168,85,247,.1)',
         'title': 'Fournisseurs & Achats',
         'description': 'Évaluation, homologation, suivi performance et non-conformités fournisseurs.'},
        {'icon': 'fas fa-calendar-alt', 'color': '#e11d48', 'bg': 'rgba(225,29,72,.1)',
         'title': 'Planification & Échéances',
         'description': 'Calendrier global, audits, formations, inspections et rappels automatiques.'},
    ]

    features_labels = {}
    for p in plans:
        if p.features:
            for k in p.features:
                if k not in features_labels:
                    features_labels[k] = k.replace('_', ' ').title()

    return render_template('landing.html', slots_json=slots_json, plans=plans, features=features, features_labels=features_labels)


@main.route('/tableau-de-bord')
@login_required
@has_permission('actions.voir')
def tableau_de_bord():
    entreprise = db.session.get(Entreprise, current_user.entreprise_id)
    domaine = session.get('domaine_actif', 'hse')
    return render_template('main/dashboard.html', entreprise=entreprise, domaine=domaine)


@main.get('/api/stats')
@login_required
@has_permission('actions.voir')
def api_stats():
    """Statistiques globales du tableau de bord"""
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

    return {
        'total_actions': total_actions,
        'actions_en_cours': actions_en_cours,
        'actions_en_retard': actions_en_retard,
        'total_documents': total_documents,
        'total_audits': total_audits,
        'total_users': total_users,
    }


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


@main.get('/api/notifications')
@login_required
@main.response(200, NotificationSchema(many=True))
def api_notifications():
    """Liste de vos notifications les plus récentes"""
    return Notification.query.filter_by(utilisateur_id=current_user.id)\
        .order_by(Notification.lu.asc(), Notification.date_envoi.desc()).limit(20).all()


@main.get('/api/notifications/unread-count')
@login_required
def api_notifications_unread_count():
    """Nombre de notifications non lues"""
    count = Notification.query.filter_by(
        utilisateur_id=current_user.id, lu=False
    ).count()
    return {'unread': count}


@main.post('/api/notifications/<int:id>/read')
@login_required
def api_notification_read(id):
    """Marquer une notification comme lue"""
    notif = Notification.query.filter_by(id=id, utilisateur_id=current_user.id).first_or_404()
    notif.lu = True
    db.session.commit()
    return {'success': True}


@main.post('/api/notifications/read-all')
@login_required
def api_notification_read_all():
    """Marquer toutes les notifications comme lues"""
    Notification.query.filter_by(utilisateur_id=current_user.id, lu=False).update({'lu': True})
    db.session.commit()
    return {'success': True}


@main.route('/notifications/<int:id>/open')
@login_required
def notification_open(id):
    notif = Notification.query.filter_by(id=id, utilisateur_id=current_user.id).first_or_404()
    notif.lu = True
    db.session.commit()

    import re
    m = re.search(r'\[TICKET:(\d+)\]', notif.message or '')
    if m:
        return redirect(url_for('support.detail_ticket', ticket_id=int(m.group(1))))
    m = re.search(r'\[INCIDENT:(\d+)\]', notif.message or '')
    if m:
        return redirect(url_for('hse.incidents'))

    return redirect(url_for('main.index'))


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
