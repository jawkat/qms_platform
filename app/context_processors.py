# =============================================================================
# QMS Platform — Context Processors
# =============================================================================
"""
Injecte des variables globales dans tous les templates Jinja2.

Ce module fournit :
1. Le sidebar dynamique (basé sur les modules activés)
2. Les variables globales (date, domaine, modules actifs)
3. Les utilitaires de requête (update_query_param)
4. La logique de highlighting du lien actif dans le sidebar

Architecture :
    Chaque requête Flask passe par inject_globals() qui retourne
    un dict de variables disponibles dans TOUS les templates.

    Les sections du sidebar sont générées par le PluginManager
    (depuis la session 2.0) qui utilise les manifests enregistrés.

Auteur : QMS Platform Team
Version : 2.0.0 (plugin-based sidebar)
"""

from datetime import datetime, date
from urllib.parse import urlencode
from flask import request
from app.models import Entreprise
from app.services.subscription_service import get_enterprise_lifecycle_status, get_payment_status
from app.utils.domaine_switch import get_domaine_actif


# =============================================================================
# Utilitaires de requête
# =============================================================================

def update_query_param(req, key, val):
    """
    Ajoute ou modifie un paramètre de query string.

    Args:
        req: Objet request Flask
        key: Clé du paramètre
        val: Nouvelle valeur (None pour supprimer)

    Returns:
        String de query string encodée

    Exemple :
        update_query_param(request, 'page', '2')  # ?page=2
        update_query_param(request, 'page', None)  # supprime ?page=
    """
    params = req.args.copy()
    if val is None or val == '':
        params.pop(key, None)
    else:
        params[key] = str(val)
    return urlencode(params)


# =============================================================================
# Sidebar — Génération dynamique
# =============================================================================

def _build_sidebar(current_user, modules_actifs):
    """
    Génère les sections du sidebar pour les 23 modules.

    Utilise le PluginManager (architecture modulaire) qui gère
    l'activation/désactivation des modules par entreprise.

    Args:
        current_user: Utilisateur Flask-Login courant
        modules_actifs: Liste des modules activés (unused, gardé pour compat)

    Returns:
        Liste de sections pour le template sidebar
    """
    from app.core import plugin_manager
    is_systeme = (current_user.is_authenticated and
                 current_user.role and current_user.role.est_systeme)
    is_manager = (current_user.is_authenticated and 
                 current_user.is_manager)
    eid = current_user.entreprise_id if current_user.is_authenticated else None
    return plugin_manager.get_sidebar_sections(
        entreprise_id=eid or 0,
        is_systeme=is_systeme,
        is_manager=is_manager
    )





# =============================================================================
# Sidebar — Détection du lien actif
# =============================================================================

def sidebar_is_active(item, endpoint):
    """
    Détermine si un élément du sidebar doit être marqué comme actif.

    Logique de matching :
    1. Si 'active_endpoints' est défini → match exact sur la liste
    2. Si 'active_prefix' est défini → match par préfixe de l'endpoint
    3. Sinon → match exact sur l'endpoint

    Args:
        item: Dict de l'élément sidebar (endpoint, active_prefix, etc.)
        endpoint: Endpoint Flask courant

    Returns:
        True si l'élément correspond à la page courante
    """
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


# =============================================================================
# Context Processor principal
# =============================================================================

def inject_globals():
    """
    Injecte les variables globales dans TOUS les templates Jinja2.

    Cette fonction est enregistrée comme context_processor dans create_app().
    Elle retourne un dict dont les clés sont accessibles directement
    dans les templates : {{ variable }}

    Variables injectées :
    - modules_actifs: Liste des modules activés pour l'entreprise
    - domaine_actif: Domaine courant ('hse' ou 'qualite')
    - has_switch: Si True, l'utilisateur peut basculer entre domaines
    - entreprise: Objet Entreprise (si authentifié)
    - sidebar_sections: Sections du sidebar pour le template
    - sidebar_is_active: Fonction de détection du lien actif
    - update_query_param: Utilitaire de query string
    - now: Datetime UTC courant
    - today: Date courante
    """
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
            lifecycle = get_enterprise_lifecycle_status(entreprise)
            pay_status = get_payment_status(entreprise)
            due = getattr(entreprise, 'abonnement_prochaine_echeance', None)
            days_remaining = (due - date.today()).days if due else None
            ctx.update({
                'domaine_actif': domaine,
                'modules_actifs': modules,
                'has_switch': len(modules) > 1,
                'entreprise': entreprise,
                'subscription_lifecycle': lifecycle,
                'subscription_pay_status': pay_status,
                'subscription_due_date': due,
                'subscription_days_remaining': days_remaining,
            })

    try:
        ctx['sidebar_sections'] = _build_sidebar(current_user, ctx['modules_actifs'])
    except Exception:
        pass
    ctx['sidebar_is_active'] = sidebar_is_active
    ctx['now'] = datetime.utcnow()
    ctx['today'] = date.today()
    return ctx
