from flask import render_template, redirect, url_for, session, request, abort, jsonify, Response, current_app
from flask_login import current_user
from app import db
from app.models import Entreprise, ActionCorrective, ProofMaster, Audit, Utilisateur, Indicateur, Ticket, SubscriptionPlan
from app.main import main
from app.utils.permissions import access_required
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

    # Diagnostic mail
    mail_config = {
        'server': current_app.config.get('MAIL_SERVER', ''),
        'port': current_app.config.get('MAIL_PORT', ''),
        'sender': current_app.config.get('MAIL_DEFAULT_SENDER', ''),
        'suppress': current_app.config.get('MAIL_SUPPRESS_SEND', False),
    }
    try:
        from redis import Redis
        r = Redis.from_url(current_app.config.get('REDIS_URL', 'redis://localhost:6379/0'))
        r.ping()
        redis_status = 'ok'
    except Exception:
        redis_status = 'error'

    return jsonify({
        'status': 'ok',
        'database': db_status,
        'redis': redis_status,
        'mail': mail_config,
        'python': platform.python_version(),
        'flask': '2.3.3',
    })


@main.route('/force-error')
@access_required()
def force_error():
    """Route de test pour simulate une erreur 500."""
    raise Exception("Test de remontée d'incident technique (Bug Bug !)")


@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.tableau_de_bord'))

    plans = []
    slots_json = '{}'
    features_labels = {}
    try:
        import json as _json
        plans = SubscriptionPlan.query.order_by(SubscriptionPlan.price_mad).all()
        for p in plans:
            if isinstance(p.features, str):
                try:
                    p.features = _json.loads(p.features)
                except (_json.JSONDecodeError, TypeError):
                    p.features = {}
            if p.features:
                for k in p.features:
                    if not k.startswith('_vis_') and k not in features_labels:
                        features_labels[k] = k.replace('_', ' ').title()

        from app.demo.routes import _generer_creneaux_libres, _slots_to_json, _grouper_par_jour
        creneaux = _generer_creneaux_libres()
        creneaux_par_jour = _grouper_par_jour(creneaux)
        slots_json = _slots_to_json(creneaux_par_jour)
    except Exception:
        pass

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

    return render_template('landing.html', slots_json=slots_json, plans=plans, features=features, features_labels=features_labels)


@main.route('/tableau-de-bord')
@access_required(permission='actions.voir')
def tableau_de_bord():
    entreprise = db.session.get(Entreprise, current_user.entreprise_id)
    return render_template('main/dashboard.html', entreprise=entreprise)


@main.get('/api/dashboard/alerts')
@access_required(permission='actions.voir')
def api_dashboard_alerts():
    """Alertes agrégées pour le tableau de bord : notifications, échéances, approbations, expirations."""
    from datetime import date, timedelta
    from app.models import ActionCorrective, ProofMaster
    today = date.today()

    entreprise_id = current_user.entreprise_id
    is_admin = current_user.role and current_user.role.est_systeme
    is_manager = is_admin or current_user.is_manager

    # Notifications (filtrées technique pour non-admin)
    notif_q = Notification.query
    if is_manager:
        notif_q = notif_q.join(Utilisateur, Notification.utilisateur_id == Utilisateur.id)\
                          .filter(Utilisateur.entreprise_id == entreprise_id)
    else:
        notif_q = notif_q.filter_by(utilisateur_id=current_user.id)
    if not is_admin:
        notif_q = notif_q.filter(Notification.categorie != 'technique')
    recent_notifications = notif_q.order_by(
        Notification.lu.asc(), Notification.date_envoi.desc()
    ).limit(20).all()

    # Actions en retard (assignées au user, ou toutes si manager)
    action_q = ActionCorrective.query.filter(
        ActionCorrective.statut.notin_(['SOLDE', 'ANNULE']),
        ActionCorrective.date_echeance < today,
    )
    if is_manager:
        action_q = action_q.filter(ActionCorrective.entreprise_id == entreprise_id)
    else:
        action_q = action_q.filter(ActionCorrective.responsable_id == current_user.id)
    overdue_actions = action_q.count()

    # Échéances dans les 7 jours
    upcoming_q = ActionCorrective.query.filter(
        ActionCorrective.statut.notin_(['SOLDE', 'ANNULE']),
        ActionCorrective.date_echeance.between(today, today + timedelta(days=7)),
    )
    if is_manager:
        upcoming_q = upcoming_q.filter(ActionCorrective.entreprise_id == entreprise_id)
    else:
        upcoming_q = upcoming_q.filter(ActionCorrective.responsable_id == current_user.id)
    upcoming_actions = upcoming_q.count()

    # Documents en attente d'approbation
    pending_approvals = ProofMaster.query.filter_by(
        workflow_statut='soumis',
        workflow_approbateur_id=current_user.id,
    ).count()

    # Documents expirés / en expiration (30 jours)
    expired_docs = ProofMaster.query.filter(
        ProofMaster.statut == 'ACTIF',
        ProofMaster.validite < today,
    )
    expiring_docs = ProofMaster.query.filter(
        ProofMaster.statut == 'ACTIF',
        ProofMaster.validite.between(today, today + timedelta(days=30)),
    )
    if is_manager:
        expired_docs = expired_docs.filter(ProofMaster.entreprise_id == entreprise_id)
        expiring_docs = expiring_docs.filter(ProofMaster.entreprise_id == entreprise_id)

    return {
        'notifications': [
            {
                'id': n.id,
                'type': n.type,
                'message': n.message,
                'categorie': n.categorie,
                'urgence': n.urgence,
                'lu': n.lu,
                'date_envoi': n.date_envoi.isoformat() if n.date_envoi else None,
                'entite_type': n.entite_type,
                'entite_id': n.entite_id,
                'utilisateur_id': n.utilisateur_id,
            }
            for n in recent_notifications
        ],
        'overdue_actions': overdue_actions,
        'upcoming_actions': upcoming_actions,
        'pending_approvals': pending_approvals,
        'expired_docs': expired_docs.count(),
        'expiring_docs': expiring_docs.count(),
    }


@main.get('/api/stats')
@access_required(permission='actions.voir')
def api_stats():
    """Statistiques globales du tableau de bord"""
    today = date.today()

    total_actions = ActionCorrective.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).count()

    actions_en_cours = ActionCorrective.query.filter_by(
        entreprise_id=current_user.entreprise_id, statut='EN_COURS'
    ).count()

    actions_en_retard = ActionCorrective.query.filter(
        ActionCorrective.entreprise_id == current_user.entreprise_id,
        ActionCorrective.statut.notin_(['SOLDE', 'ANNULE']),
        ActionCorrective.date_echeance < today).count()

    total_documents = ProofMaster.query.filter_by(
        entreprise_id=current_user.entreprise_id, statut='ACTIF'
    ).count()

    total_audits = Audit.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).count()

    total_users = Utilisateur.query.count()

    return {
        'total_actions': total_actions,
        'actions_en_cours': actions_en_cours,
        'actions_en_retard': actions_en_retard,
        'total_documents': total_documents,
        'total_audits': total_audits,
        'total_users': total_users,
    }


@main.get('/api/notifications')
@access_required()
@main.response(200, NotificationSchema(many=True))
def api_notifications():
    """Liste de vos notifications les plus récentes (filtrées par rôle)."""
    q = Notification.query.filter_by(utilisateur_id=current_user.id)
    if not current_user.role or not current_user.role.est_systeme:
        q = q.filter(Notification.categorie != 'technique')
    return q.order_by(Notification.lu.asc(), Notification.date_envoi.desc()).limit(20).all()


@main.get('/api/notifications/unread-count')
@access_required()
def api_notifications_unread_count():
    """Nombre de notifications non lues (filtré par rôle)."""
    q = Notification.query.filter_by(utilisateur_id=current_user.id, lu=False)
    if not current_user.role or not current_user.role.est_systeme:
        q = q.filter(Notification.categorie != 'technique')
    return {'unread': q.count()}


@main.post('/api/notifications/<int:id>/read')
@access_required()
def api_notification_read(id):
    """Marquer une notification comme lue"""
    notif = Notification.query.filter_by(id=id, utilisateur_id=current_user.id).first_or_404()
    notif.lu = True
    db.session.commit()
    return {'success': True}


@main.post('/api/notifications/read-all')
@access_required()
def api_notification_read_all():
    """Marquer toutes les notifications comme lues"""
    Notification.query.filter_by(utilisateur_id=current_user.id, lu=False).update({'lu': True})
    db.session.commit()
    return {'success': True}


def _classify_notification_domain(notification_type, message):
    type_key = (notification_type or '').strip().lower()
    text = (message or '').strip().lower()
    if type_key in ('incident', 'accident', 'presqu_accident'):
        return 'incident'
    if type_key in ('action', 'overdue', 'echeance') or 'action' in text:
        return 'action'
    if 'évaluation' in text or 'evaluation' in text or 'preuve' in text or 'conformité' in text or 'conformite' in text:
        return 'evaluation'
    if 'mise à jour réglementaire' in text or 'mise a jour reglementaire' in text or 'texte' in text or 'réglementaire' in text or 'reglementaire' in text:
        return 'texte'
    if 'document' in text or type_key == 'document':
        return 'document'
    if 'formation' in text:
        return 'formation'
    if 'haccp' in text:
        return 'haccp'
    if 'ticket' in text or 'support' in text:
        return 'ticket'
    if 'maintenance' in text:
        return 'maintenance'
    if 'audit' in text:
        return 'audit'
    return type_key or 'info'


@main.get('/notifications/quick')
@access_required()
def quick_notifications():
    from sqlalchemy import or_
    limit_raw = (request.args.get('limit') or '8').strip()
    try:
        limit = max(1, min(int(limit_raw), 20))
    except ValueError:
        limit = 8
    scope = (request.args.get('scope') or 'general').strip().lower()
    if scope not in {'general', 'incident', 'all'}:
        scope = 'general'
    base_query = Notification.query.filter_by(utilisateur_id=current_user.id)
    if scope == 'incident':
        base_query = base_query.filter(Notification.type == 'incident')
    elif scope == 'general':
        base_query = base_query.filter(or_(Notification.type.is_(None), Notification.type != 'incident'))
    if not current_user.role or not current_user.role.est_systeme:
        base_query = base_query.filter(Notification.categorie != 'technique')
    notifications = base_query.order_by(Notification.date_envoi.desc()).limit(limit).all()
    unread_count = base_query.filter_by(lu=False).count()
    payload = []
    for notification in notifications:
        domain = _classify_notification_domain(notification.type, notification.message)
        payload.append({
            'id': notification.id,
            'type': notification.type or 'info',
            'domain': domain,
            'message': notification.message or '',
            'lu': bool(notification.lu),
            'date_envoi': notification.date_envoi.isoformat() if notification.date_envoi else None,
            'date_label': notification.date_envoi.strftime('%d/%m/%Y %H:%M') if notification.date_envoi else '',
        })
    return jsonify({'success': True, 'unread_count': unread_count, 'notifications': payload})


@main.post('/notifications/read-all')
@access_required()
def mark_all_notifications_read():
    from sqlalchemy import or_
    Notification.query.filter(
        Notification.utilisateur_id == current_user.id,
        Notification.lu.is_(False),
        or_(Notification.type.is_(None), Notification.type != 'incident'),
    ).update({'lu': True}, synchronize_session=False)
    db.session.commit()
    return jsonify({'success': True, 'unread_count': 0})


@main.post('/notifications/incidents/read-all')
@access_required()
def mark_all_incident_notifications_read():
    if not current_user.role or not current_user.role.est_systeme:
        return jsonify({'success': False, 'error': 'unauthorized'}), 403
    Notification.query.filter(
        Notification.utilisateur_id == current_user.id,
        Notification.lu.is_(False),
        Notification.type == 'incident',
    ).update({'lu': True}, synchronize_session=False)
    db.session.commit()
    return jsonify({'success': True, 'unread_count': 0})


ENTITY_ROUTE_MAP = {
    'ticket':          ('support.detail_ticket',        'ticket_id'),
    'incident':        ('hse.incidents',                None),
    'accident':        ('hse.incidents',                None),
    'presqu_accident': ('hse.incidents',                None),
    'action':          ('actions.detail_action',         'action_id'),
    'document':        ('documents.detail',              'proof_id'),
    'nonconformite':   ('nonconformites.index',          None),
}

@main.route('/notifications/<int:id>/open')
@access_required()
def notification_open(id):
    notif = Notification.query.filter_by(id=id, utilisateur_id=current_user.id).first_or_404()
    notif.lu = True
    db.session.commit()

    # 1. Routing via entite_type / entite_id
    if notif.entite_type and notif.entite_id:
        route = ENTITY_ROUTE_MAP.get(notif.entite_type)
        if route:
            endpoint, param = route
            kwargs = {param: notif.entite_id} if param else {}
            return redirect(url_for(endpoint, **kwargs))

    # 2. Fallback par regex dans le message (rétrocompatibilité)
    import re
    m = re.search(r'\[TICKET:(\d+)\]', notif.message or '')
    if m:
        return redirect(url_for('support.detail_ticket', ticket_id=int(m.group(1))))
    m = re.search(r'\[INCIDENT:(\d+)\]', notif.message or '')
    if m:
        return redirect(url_for('hse.incidents'))

    # 3. Notifications "Bug applicatif" → journal de sécurité avec détail incident
    if notif.message and 'Bug applicatif' in notif.message:
        import re
        m = re.search(r'Ref:\s*([a-f0-9-]+)', notif.message or '')
        if m:
            ref = m.group(1)
            from app.models import JournalSecurite
            incident = JournalSecurite.query.filter(
                JournalSecurite.details.cast(db.String).contains(ref)
            ).first()
            if incident:
                return redirect(url_for('admin.securite', incident_id=incident.id))
        return redirect(url_for('admin.securite'))

    # 4. Dernier recours : tableau de bord
    return redirect(url_for('main.index'))


@main.route('/notifications')
@access_required()
def notifications():
    q = Notification.query.filter_by(utilisateur_id=current_user.id)
    if not current_user.role or not current_user.role.est_systeme:
        q = q.filter(Notification.categorie != 'technique')
    notifs = q.order_by(Notification.date_envoi.desc()).all()
    return render_template('main/notifications.html', notifications=notifs)


@main.route('/search')
@access_required()
def search():
    q = request.args.get('q', '').strip()
    results = {}
    if q:
        pattern = f'%{q}%'
        actions = ActionCorrective.query.filter(
            ActionCorrective.description.ilike(pattern)
        ).limit(10).all()
        if actions:
            results['Actions'] = [{'id': a.id, 'title': a.description[:80], 'url': url_for('actions.detail_action', action_id=a.id)} for a in actions]

        audits = Audit.query.filter(
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
            Ticket.sujet.ilike(pattern)
        ).limit(10).all()
        if tickets:
            results['Tickets'] = [{'id': t.id, 'title': t.sujet or t.description[:80], 'url': url_for('support.detail_ticket', ticket_id=t.id)} for t in tickets]

    return render_template('main/search.html', results=results, query=q)


@main.route('/api/alerts/trigger', methods=['POST'])
@access_required()
def api_trigger_alerts():
    """Déclenche manuellement les alertes (admin only)."""
    if not current_user.role or not current_user.role.est_systeme:
        abort(403)
    from app.services.alert_engine import run_daily_alerts
    results = run_daily_alerts()
    return jsonify({'success': True, 'results': results})


@main.route('/export/<module>')
@access_required()
def export_module(module):
    """Export Excel pour un module donne."""
    from app.services.report_service import (
        export_actions_excel, export_audits_excel, export_nc_excel, export_risques_excel
    )

    exporters = {
        'actions': lambda: export_actions_excel(current_user.entreprise_id),
        'audits': lambda: export_audits_excel(current_user.entreprise_id),
        'nc': lambda: export_nc_excel(current_user.entreprise_id),
        'risques': lambda: export_risques_excel(current_user.entreprise_id),
    }
    if module not in exporters:
        abort(404)
    return exporters[module]()


@main.route('/suspended')
@access_required()
def suspended():
    from app.models import Entreprise
    from app.services.subscription_service import get_enterprise_lifecycle_status
    entreprise = db.session.get(Entreprise, current_user.entreprise_id)
    lifecycle = get_enterprise_lifecycle_status(entreprise) if entreprise else 'inconnu'
    return render_template('main/suspended.html', entreprise=entreprise, lifecycle=lifecycle), 403
