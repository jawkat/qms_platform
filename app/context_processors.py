from datetime import datetime, date
from urllib.parse import urlencode
from flask import request
from app.models import Entreprise
from app.utils.domaine_switch import get_domaine_actif


def update_query_param(req, key, val):
    params = req.args.copy()
    if val is None or val == '':
        params.pop(key, None)
    else:
        params[key] = str(val)
    return urlencode(params)


def _build_sidebar(current_user, modules_actifs):
    sections = []

    # -- Administration (systeme only) --
    if current_user.is_authenticated and current_user.role and current_user.role.est_systeme:
        sections.append({
            'id': 'admin', 'title': 'Administration', 'icon': 'fa-crown',
            'items': [
                {'endpoint': 'admin.dashboard', 'icon': 'fa-chart-pie', 'label': 'Dashboard'},
                {'endpoint': 'admin.utilisateurs', 'icon': 'fa-users-cog', 'label': 'Utilisateurs'},
                {'endpoint': 'admin.admin_tickets', 'icon': 'fa-headset', 'label': 'Tickets'},
                {'endpoint': 'admin.demo_creneaux', 'icon': 'fa-calendar-alt', 'label': 'Démo'},
                {'endpoint': 'entreprises.index', 'icon': 'fa-building', 'label': 'Entreprises'},
                {'endpoint': 'admin.plans', 'icon': 'fa-crown', 'label': 'Plans',
                 'active_endpoints': ['admin.plans', 'plans.index']},
            ]
        })

    # -- General --
    general_items = [
        {'endpoint': 'main.tableau_de_bord', 'icon': 'fa-chart-line', 'label': 'Tableau de bord'},
        {'endpoint': 'main.search', 'icon': 'fa-search', 'label': 'Recherche'},
        {'endpoint': 'actions.liste_actions', 'icon': 'fa-tasks', 'label': 'Mes actions',
         'active_prefix': 'actions.'},
        {'endpoint': 'nonconformites.index', 'icon': 'fa-exclamation-triangle', 'label': 'Non-conformités',
         'active_prefix': 'nonconformites.'},
    ]
    if 'ged' in modules_actifs:
        general_items.append({
            'endpoint': 'documents.gestion', 'icon': 'fa-folder-open', 'label': 'Documents',
            'active_prefix': 'documents.',
        })
    general_items.append({'endpoint': 'audit.index', 'icon': 'fa-clipboard-check', 'label': 'Audits',
                          'active_prefix': 'audit.'})
    general_items.append({'endpoint': 'indicateurs.index', 'icon': 'fa-chart-bar', 'label': 'Indicateurs',
                          'active_prefix': 'indicateurs.'})
    sections.append({
        'id': 'general', 'title': 'Général', 'icon': 'fa-th-large',
        'items': general_items,
    })

    # -- HSE --
    if 'hse' in modules_actifs:
        sections.append({
            'id': 'hse', 'title': 'HSE', 'icon': 'fa-hard-hat',
            'items': [
                {'endpoint': 'textes.library_all', 'icon': 'fa-book', 'label': 'Bibliothèque HSE',
                 'active_prefix': 'textes.library'},
                {'endpoint': 'textes.index', 'icon': 'fa-scroll', 'label': 'Textes HSE',
                 'active_prefix': 'textes.', 'exclude_prefix': 'textes.library'},
                {'endpoint': 'conformite.index', 'icon': 'fa-clipboard-list', 'label': 'Suivi conformité',
                 'active_prefix': 'conformite.'},
                {'endpoint': 'conformite.preuves_gestion', 'icon': 'fa-shield-alt', 'label': 'Preuves de conformité'},
                {'endpoint': 'conformite.search', 'icon': 'fa-search', 'label': 'Recherche conformité'},
                {'endpoint': 'veille.index', 'icon': 'fa-satellite-dish', 'label': 'Veille réglementaire',
                 'active_prefix': 'veille.'},
                {'endpoint': 'hse.incidents', 'icon': 'fa-bug', 'label': 'Incidents & Accidents',
                 'active_prefix': 'hse.incidents'},
                {'endpoint': 'hse.epi_liste', 'icon': 'fa-hard-hat', 'label': 'EPI',
                 'active_prefix': 'hse.epi'},
                {'endpoint': 'hse.inspections', 'icon': 'fa-clipboard-check', 'label': 'Inspections',
                 'active_prefix': 'hse.inspections'},
                {'endpoint': 'hse.permis_travail', 'icon': 'fa-file-signature', 'label': 'Permis de travail',
                 'active_prefix': 'hse.permis'},
            ]
        })

    # -- HACCP --
    if 'haccp' in modules_actifs:
        sections.append({
            'id': 'haccp', 'title': 'HACCP', 'icon': 'fa-utensils',
            'items': [
                {'endpoint': 'haccp.tableau_de_bord', 'icon': 'fa-chart-pie', 'label': 'Tableau de bord'},
                {'endpoint': 'haccp.processus', 'icon': 'fa-industry', 'label': 'Processus'},
                {'endpoint': 'haccp.produits', 'icon': 'fa-box', 'label': 'Produits'},
                {'endpoint': 'haccp.dangers', 'icon': 'fa-biohazard', 'label': 'Analyse dangers'},
                {'endpoint': 'haccp.ccp', 'icon': 'fa-exclamation-triangle', 'label': 'CCP'},
                {'endpoint': 'haccp.enregistrements', 'icon': 'fa-clipboard-check', 'label': 'Enregistrements'},
                {'endpoint': 'haccp.prp', 'icon': 'fa-hand-sparkles', 'label': 'PRP'},
                {'endpoint': 'haccp.tracabilite', 'icon': 'fa-sitemap', 'label': 'Traçabilité'},
                {'endpoint': 'fournisseurs.index', 'icon': 'fa-truck', 'label': 'Fournisseurs',
                 'active_prefix': 'fournisseurs.'},
                {'endpoint': 'formations.index', 'icon': 'fa-graduation-cap', 'label': 'Formations',
                 'active_prefix': 'formations.'},
                {'endpoint': 'reclamations.index', 'icon': 'fa-headset', 'label': 'Réclamations',
                 'active_prefix': 'reclamations.'},
                {'endpoint': 'haccp.rappels', 'icon': 'fa-exclamation-circle', 'label': 'Rappels'},
            ]
        })

    # -- Qualite --
    if 'qualite' in modules_actifs:
        sections.append({
            'id': 'qualite', 'title': 'Qualité', 'icon': 'fa-certificate',
            'items': [
                {'endpoint': 'qualite.risques', 'icon': 'fa-exclamation-triangle', 'label': 'Risques',
                 'active_prefix': 'qualite.risques'},
                {'endpoint': 'reclamations.index', 'icon': 'fa-headset', 'label': 'Réclamations clients',
                 'active_prefix': 'reclamations.'},
                {'endpoint': 'fournisseurs.index', 'icon': 'fa-truck', 'label': 'Fournisseurs',
                 'active_prefix': 'fournisseurs.'},
                {'endpoint': 'formations.index', 'icon': 'fa-graduation-cap', 'label': 'Formations',
                 'active_prefix': 'formations.'},
                {'endpoint': 'qualite.equipements', 'icon': 'fa-tools', 'label': 'Équipements',
                 'active_prefix': 'qualite.equipements'},
                {'endpoint': 'qualite.controle', 'icon': 'fa-flask', 'label': 'Contrôle qualité',
                 'active_prefix': 'qualite.controle'},
                {'endpoint': 'qualite.revue', 'icon': 'fa-chart-pie', 'label': 'Revue de direction',
                 'active_prefix': 'qualite.revue'},
            ]
        })

    # -- Assistance --
    sections.append({
        'id': 'assistance', 'title': 'Assistance', 'icon': 'fa-life-ring',
        'items': [
            {'endpoint': 'support.mes_tickets', 'icon': 'fa-ticket-alt', 'label': 'Mes tickets'},
        ]
    })

    # -- Mon compte --
    sections.append({
        'id': 'compte', 'title': 'Mon compte', 'icon': 'fa-user',
        'items': [
            {'endpoint': 'users.profile', 'icon': None, 'label': None, 'is_profile': True},
            {'endpoint': 'facturation.index', 'icon': 'fa-credit-card', 'label': 'Facturation',
             'active_prefix': 'facturation.'},
            {'endpoint': 'plans.index', 'icon': 'fa-crown', 'label': 'Mon abonnement',
             'active_prefix': 'plans.'},
            {'endpoint': 'users.logout', 'icon': 'fa-sign-out-alt', 'label': 'Déconnexion', 'is_logout': True},
        ]
    })

    return sections


def sidebar_is_active(item, endpoint):
    if not endpoint:
        return False
    if item.get('is_logout'):
        return False
    if item.get('active_endpoints'):
        return endpoint in item['active_endpoints']
    if item.get('active_prefix'):
        if not endpoint.startswith(item['active_prefix']):
            return False
        if item.get('exclude_prefix') and endpoint.startswith(item['exclude_prefix']):
            return False
        return True
    return endpoint == item['endpoint']


def inject_globals():
    from flask import current_app
    from flask_login import current_user
    ctx = {
        'modules_actifs': [],
        'domaine_actif': 'hse',
        'has_switch': False,
        'update_query_param': update_query_param,
        'sidebar_sections': [],
    }

    if current_user.is_authenticated and current_user.entreprise_id:
        entreprise = Entreprise.query.get(current_user.entreprise_id)
        if entreprise:
            modules = entreprise.modules_actifs or ['hse']
            domaine = get_domaine_actif(entreprise)
            ctx.update({
                'domaine_actif': domaine,
                'modules_actifs': modules,
                'has_switch': len(modules) > 1,
                'entreprise': entreprise,
            })

    ctx['sidebar_sections'] = _build_sidebar(current_user, ctx['modules_actifs'])
    ctx['sidebar_is_active'] = sidebar_is_active
    ctx['now'] = datetime.utcnow()
    ctx['today'] = date.today()
    return ctx
