# =============================================================================
# QMS Platform — Plugin Manager
# =============================================================================
"""
Système de gestion des plugins modulaires.

Ce module implémente un registre central qui découvre, charge et gère
l'activation/désactivation des modules métier de la plateforme QMS.

Architecture :
    ┌─────────────────────────────────────────────────────┐
    │                  PluginManager                      │
    │                                                     │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
    │  │ Module   │  │ Module   │  │ Module   │  ...     │
    │  │ Registry │  │ Registry │  │ Registry │         │
    │  └──────────┘  └──────────┘  └──────────┘         │
    │       ↑               ↑              ↑              │
    │  ┌────┴────┐   ┌─────┴─────┐  ┌─────┴─────┐      │
    │  │ Module  │   │ Module    │  │ Module    │      │
    │  │ HACCP   │   │ HSE       │  │ Qualité   │      │
    │  └─────────┘   └───────────┘  └───────────┘      │
    └─────────────────────────────────────────────────────┘

Usage :
    from app.core.plugin_manager import plugin_manager

    # Enregistrer un module
    plugin_manager.register(HaccpModule)

    # Vérifier si un module est actif
    if plugin_manager.is_active('haccp', entreprise_id=1):
        ...

    # Lister les modules actifs
    active = plugin_manager.get_active_modules(entreprise_id=1)

Auteur : QMS Platform Team
Version : 1.0.0
"""

import logging
from typing import Dict, List, Optional, Set, Type
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes — Structure de configuration d'un module
# =============================================================================

@dataclass
class ModuleManifest:
    """
    Descripteur complet d'un module QMS.

    Chaque module doit fournir un manifest qui décrit :
    - Son identifiant unique et nom d'affichage
    - Sa catégorie (qualite, hse, haccp, etc.)
    - Les modules dont il dépend
    - Les permissions qu'il introduit
    - Les événements qu'il émet/consomme
    - Les paramètres configurables

    Attributes:
        name: Identifiant technique unique (ex: 'haccp', 'hse')
        display_name: Nom d'affichage dans l'UI (ex: 'HACCP / ISO 22000')
        version: Numéro de version sémantique
        description: Description courte du module
        icon: Classe Font Awesome (ex: 'fa-utensils')
        category: Catégorie logique ('qualite', 'hse', 'haccp', 'admin', 'core')
        requires: Liste des modules requis pour fonctionner
        permissions: Liste des codes de permissions introduits
        events_emit: Événements que ce module publie
        events_consume: Événements que ce module consomme
        settings: Paramètres configurables avec valeurs par défaut
        menu_position: Position dans le sidebar (ordre d'affichage)
        visible: Si False, le module n'apparaît pas dans le menu
    """
    name: str
    display_name: str
    version: str = '1.0.0'
    description: str = ''
    icon: str = 'fa-puzzle-piece'
    category: str = 'general'
    requires: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    events_emit: List[str] = field(default_factory=list)
    events_consume: List[str] = field(default_factory=list)
    settings: Dict = field(default_factory=dict)
    menu_position: int = 100
    visible: bool = True


@dataclass
class ModuleState:
    """
    État d'activation d'un module pour une entreprise donnée.

    Un module peut être :
    - 'active': Entièrement fonctionnel
    - 'inactive': Désactivé mais installé
    - 'error': En erreur (dépendances manquantes)
    - 'loading': En cours de chargement

    Attributes:
        manifest: Descripteur du module
        enabled_modules: Ensemble des modules activés par entreprise
        settings_overrides: Paramètres personnalisés par entreprise
    """
    manifest: ModuleManifest
    enabled_modules: Set[int] = field(default_factory=set)
    settings_overrides: Dict[int, Dict] = field(default_factory=dict)


# =============================================================================
# Plugin Manager — Registre central des modules
# =============================================================================

class PluginManager:
    """
    Gestionnaire central des modules QMS.

    Ce singleton gère :
    1. L'enregistrement des modules (register)
    2. La vérification des dépendances (check_dependencies)
    3. L'activation/désactivation par entreprise (enable/disable)
    4. La récupération des modules actifs (get_active_modules)
    5. Le dispatch d'événements inter-modules (emit/consume)

    Exemple d'utilisation :

        # Au démarrage de l'app
        plugin_manager = PluginManager()
        plugin_manager.register(HaccpModule.manifest)

        # Dans un route
        @blueprint.route('/haccp/')
        def index():
            if not plugin_manager.is_active('haccp', current_user.entreprise_id):
                abort(403)
            ...

    Thread-safety: Le PluginManager n'est PAS thread-safe. Il est conçu
    pour être initialisé une seule fois au démarrage de l'application Flask.
    Les opérations runtime (is_active, get_active) sont read-only et sûres.
    """

    def __init__(self):
        """Initialise le registre vide."""
        self._modules: Dict[str, ModuleManifest] = {}
        self._event_handlers: Dict[str, List[callable]] = {}
        self._aliases: Dict[str, str] = {
            'risques': 'qualite',
        }
        logger.debug("PluginManager initialized")

    # -------------------------------------------------------------------------
    # Enregistrement de modules
    # -------------------------------------------------------------------------

    def register(self, manifest: ModuleManifest) -> None:
        """
        Enregistre un module dans le registre central.

        Cette méthode est appelée au démarrage de l'application pour chaque
        module disponible. Elle valide les dépendances et enregistre le manifest.

        Args:
            manifest: Descripteur du module à enregistrer

        Raises:
            ValueError: Si un module avec le même nom est déjà enregistré
            ValueError: Si une dépendance requise n'est pas disponible
        """
        if manifest.name in self._modules:
            raise ValueError(
                f"Module '{manifest.name}' already registered. "
                f"Duplicate registration is not allowed."
            )

        # Vérifier que les dépendances sont disponibles
        for dep in manifest.requires:
            if dep not in self._modules:
                raise ValueError(
                    f"Module '{manifest.name}' requires '{dep}' which is not registered. "
                    f"Register '{dep}' before '{manifest.name}'."
                )

        self._modules[manifest.name] = manifest
        logger.info(
            "Module registered: %s v%s (%s)",
            manifest.name, manifest.version, manifest.display_name
        )

    def unregister(self, name: str) -> None:
        """
        Désinstalle un module du registre.

        Attention : Cette méthode ne vérifie pas si d'autres modules
        dépendent de celui qu'on supprime.

        Args:
            name: Identifiant du module à supprimer
        """
        if name in self._modules:
            del self._modules[name]
            logger.info("Module unregistered: %s", name)

    # -------------------------------------------------------------------------
    # Consultation du registre
    # -------------------------------------------------------------------------

    def get_manifest(self, name: str) -> Optional[ModuleManifest]:
        """
        Récupère le manifest d'un module par son identifiant.

        Args:
            name: Identifiant du module

        Returns:
            Le manifest ou None si le module n'existe pas
        """
        return self._modules.get(name)

    def get_all_manifests(self) -> List[ModuleManifest]:
        """
        Retourne tous les manifests enregistrés, triés par position menu.

        Returns:
            Liste des manifests triés
        """
        return sorted(
            self._modules.values(),
            key=lambda m: (m.category, m.menu_position)
        )

    def get_by_category(self, category: str) -> List[ModuleManifest]:
        """
        Retourne tous les modules d'une catégorie donnée.

        Args:
            category: Catégorie à filtrer ('qualite', 'hse', 'haccp', etc.)

        Returns:
            Liste des manifests de la catégorie
        """
        return [
            m for m in self._modules.values()
            if m.category == category
        ]

    # -------------------------------------------------------------------------
    # Activation / Désactivation par entreprise
    # -------------------------------------------------------------------------

    def _resolve_name(self, name: str) -> str:
        """Résout un nom de module via les alias de compatibilité."""
        return self._aliases.get(name, name)

    def is_active(self, module_name: str, entreprise_id: int) -> bool:
        """
        Vérifie si un module est actif pour une entreprise donnée.

        Cette méthode est le point d'entrée principal pour les routes
        et les context processors qui doivent vérifier l'accès.

        Args:
            module_name: Identifiant du module
            entreprise_id: ID de l'entreprise

        Returns:
            True si le module est actif pour cette entreprise
        """
        resolved = self._resolve_name(module_name)
        if resolved not in self._modules:
            return False

        manifest = self._modules[resolved]

        # Vérifier les dépendances
        for dep in manifest.requires:
            if not self.is_active(dep, entreprise_id):
                return False

        # Vérifier dans la base de données
        from app import db
        from app.models.entreprise import Entreprise
        entreprise = db.session.get(Entreprise, entreprise_id)
        if not entreprise:
            return False

        active_modules = entreprise.modules_actifs or []
        resolved_active = {self._resolve_name(n) for n in active_modules}
        return resolved in resolved_active

    def get_active_modules(self, entreprise_id: int) -> List[ModuleManifest]:
        """
        Retourne tous les modules actifs pour une entreprise.

        Args:
            entreprise_id: ID de l'entreprise

        Returns:
            Liste des manifests des modules actifs
        """
        from app import db
        from app.models.entreprise import Entreprise
        entreprise = db.session.get(Entreprise, entreprise_id)
        if not entreprise:
            return []

        raw_names = entreprise.modules_actifs or []
        active_names = {self._resolve_name(n) for n in raw_names}
        return [
            m for m in self._modules.values()
            if m.name in active_names
        ]

    def get_sidebar_sections(self, entreprise_id: int, is_systeme: bool = False) -> List[Dict]:
        """
        Génère les sections du sidebar organisées par module métier.

        Chaque module (HSE, HACCP, Qualité, etc.) a sa propre section qui
        n'apparaît que si le module est activé pour l'entreprise.
        Le "Général" contient les fonctionnalités transverses toujours visibles.

        Args:
            entreprise_id: ID de l'entreprise
            is_systeme: Si True, inclut la section Administration

        Returns:
            Liste de sections pour le template sidebar
        """
        sections = []

        active = self.get_active_modules(entreprise_id)
        active_names = {m.name for m in active}

        # --- ADMINISTRATION (admin système uniquement) ---
        if is_systeme:
            sections.append({
                'id': 'admin', 'title': 'Administration', 'icon': 'fa-crown', 'items': [
                    {'endpoint': 'admin.dashboard', 'icon': 'fa-chart-pie', 'label': 'Dashboard'},
                    {'endpoint': 'admin.utilisateurs', 'icon': 'fa-users-cog', 'label': 'Utilisateurs'},
                    {'endpoint': 'admin.admin_tickets', 'icon': 'fa-headset', 'label': 'Tickets'},
                    {'endpoint': 'entreprises.index', 'icon': 'fa-building', 'label': 'Entreprises'},
                    {'endpoint': 'admin.plans', 'icon': 'fa-crown', 'label': 'Plans',
                     'active_endpoints': ['admin.plans', 'plans.index']},
                    {'endpoint': 'textes.index', 'icon': 'fa-scroll', 'label': 'Textes & Normes',
                     'active_prefix': 'textes.', 'exclude_prefix': 'textes.library'},
                    {'endpoint': 'textes.import_json', 'icon': 'fa-file-import', 'label': 'Import JSON',
                     'active_prefix': 'textes.import'},
                    {'endpoint': 'veille.index', 'icon': 'fa-satellite-dish', 'label': 'Veille',
                     'active_prefix': 'veille.'},
                ]
            })

        # --- GÉNÉRAL (toujours visible — socle commun) ---
        general_items = [
            {'endpoint': 'main.tableau_de_bord', 'icon': 'fa-chart-line', 'label': 'Tableau de bord'},
            {'endpoint': 'main.search', 'icon': 'fa-search', 'label': 'Recherche'},
            {'endpoint': 'actions.liste_actions', 'icon': 'fa-tasks', 'label': 'Actions / CAPA',
             'active_prefix': 'actions.'},
            {'endpoint': 'nonconformites.index', 'icon': 'fa-exclamation-triangle', 'label': 'Non-conformités',
             'active_prefix': 'nonconformites.'},
        ]
        if 'ged' in active_names:
            general_items.append({
                'endpoint': 'documents.gestion', 'icon': 'fa-folder-open', 'label': 'Documents',
                'active_prefix': 'documents.',
            })
        general_items.extend([
            {'endpoint': 'audit.index', 'icon': 'fa-clipboard-check', 'label': 'Audits',
             'active_prefix': 'audit.'},
            {'endpoint': 'secteur.liste_secteurs', 'icon': 'fa-layer-group', 'label': 'Secteurs',
             'active_prefix': 'secteur.'},
        ])
        sections.append({
            'id': 'general', 'title': 'Général', 'icon': 'fa-th-large',
            'items': general_items,
        })

        # --- QUALITÉ / ISO 9001 (si qualite, hse ou haccp actif) ---
        if 'qualite' in active_names or 'hse' in active_names or 'haccp' in active_names:
            qualite_items = [
                {'endpoint': 'qualite.risques', 'icon': 'fa-exclamation-triangle', 'label': 'Risques',
                 'active_prefix': 'qualite.risques'},
                {'endpoint': 'qualite.equipements', 'icon': 'fa-tools', 'label': 'Équipements',
                 'active_prefix': 'qualite.equipements'},
                {'endpoint': 'qualite.controle', 'icon': 'fa-flask', 'label': 'Contrôle qualité',
                 'active_prefix': 'qualite.controle'},
                {'endpoint': 'qualite.revue', 'icon': 'fa-chart-pie', 'label': 'Revue de direction',
                 'active_prefix': 'qualite.revue'},
            ]
            qualite_items.append({
                'endpoint': 'indicateurs.index', 'icon': 'fa-chart-bar', 'label': 'Indicateurs',
                'active_prefix': 'indicateurs.',
            })
            qualite_items.append({
                'endpoint': 'processus.index', 'icon': 'fa-project-diagram', 'label': 'Processus & BPMN',
                'active_prefix': 'processus.',
            })
            qualite_items.append({
                'endpoint': 'workflow_engine.index', 'icon': 'fa-cogs', 'label': 'Workflows',
                'active_prefix': 'workflow_engine.',
            })
            qualite_items.append({
                'endpoint': 'change_management.index', 'icon': 'fa-exchange-alt', 'label': 'Changements',
                'active_prefix': 'change_management.',
            })
            qualite_items.append({
                'endpoint': 'ishikawa.index', 'icon': 'fa-fish', 'label': 'Ishikawa',
                'active_prefix': 'ishikawa.',
            })
            sections.append({
                'id': 'qualite', 'title': 'Qualité / ISO 9001', 'icon': 'fa-certificate',
                'items': qualite_items,
            })

        # --- HACCP / ISO 22000 (si activé) ---
        if 'haccp' in active_names:
            sections.append({
                'id': 'haccp', 'title': 'HACCP / ISO 22000', 'icon': 'fa-utensils', 'items': [
                    {'endpoint': 'haccp.tableau_de_bord', 'icon': 'fa-chart-pie', 'label': 'Tableau de bord'},
                    {'endpoint': 'haccp.processus', 'icon': 'fa-industry', 'label': 'Processus'},
                    {'endpoint': 'haccp.produits', 'icon': 'fa-box', 'label': 'Produits'},
                    {'endpoint': 'haccp.dangers', 'icon': 'fa-biohazard', 'label': 'Analyse dangers'},
                    {'endpoint': 'haccp.ccp', 'icon': 'fa-exclamation-triangle', 'label': 'CCP'},
                    {'endpoint': 'haccp.enregistrements', 'icon': 'fa-clipboard-check', 'label': 'Enregistrements'},
                    {'endpoint': 'haccp.prp', 'icon': 'fa-hand-sparkles', 'label': 'PRP'},
                    {'endpoint': 'haccp.tracabilite', 'icon': 'fa-sitemap', 'label': 'Traçabilité'},
                    {'endpoint': 'haccp.rappels', 'icon': 'fa-exclamation-circle', 'label': 'Rappels produits'},
                ]
            })

        # --- HSE / ISO 45001 (si activé) ---
        if 'hse' in active_names:
            hse_items = [
                {'endpoint': 'hse.tableau_de_bord', 'icon': 'fa-chart-pie', 'label': 'Tableau de bord',
                 'active_prefix': 'hse.tableau_de_bord'},
                {'endpoint': 'hse.incidents', 'icon': 'fa-bug', 'label': 'Incidents',
                 'active_prefix': 'hse.incidents'},
                {'endpoint': 'hse.epi_liste', 'icon': 'fa-hard-hat', 'label': 'EPI',
                 'active_prefix': 'hse.epi'},
                {'endpoint': 'hse.inspections', 'icon': 'fa-clipboard-check', 'label': 'Inspections',
                 'active_prefix': 'hse.inspections'},
                {'endpoint': 'hse.permis_travail', 'icon': 'fa-file-signature', 'label': 'Permis de travail',
                 'active_prefix': 'hse.permis'},
            ]
            sections.append({
                'id': 'hse', 'title': 'HSE / ISO 45001', 'icon': 'fa-hard-hat',
                'items': hse_items,
            })

        # --- ENVIRONNEMENT / ISO 14001 (si activé) ---
        if 'environnement' in active_names:
            sections.append({
                'id': 'environnement', 'title': 'Environnement / ISO 14001', 'icon': 'fa-leaf', 'items': [
                    {'endpoint': 'environnement.index', 'icon': 'fa-leaf', 'label': 'Aspects environnementaux',
                     'active_prefix': 'environnement.'},
                ]
            })

        # --- VEILLE RÉGLEMENTAIRE (si hse ou qualite activé) ---
        if 'hse' in active_names or 'qualite' in active_names:
            sections.append({
                'id': 'veille', 'title': 'Veille réglementaire', 'icon': 'fa-satellite-dish', 'items': [
                    {'endpoint': 'textes.library_all', 'icon': 'fa-book', 'label': 'Bibliothèque',
                     'active_prefix': 'textes.library'},
                    {'endpoint': 'conformite.index', 'icon': 'fa-clipboard-list', 'label': 'Conformité',
                     'active_prefix': 'conformite.'},
                ]
            })

        # --- FORMATIONS & COMPÉTENCES (si activé) ---
        if 'formations' in active_names:
            sections.append({
                'id': 'formations', 'title': 'Formations & Compétences', 'icon': 'fa-graduation-cap', 'items': [
                    {'endpoint': 'formations.index', 'icon': 'fa-graduation-cap', 'label': 'Formations',
                     'active_prefix': 'formations.'},
                ]
            })

        # --- FOURNISSEURS (si activé) ---
        if 'fournisseurs' in active_names:
            sections.append({
                'id': 'fournisseurs', 'title': 'Fournisseurs & Achats', 'icon': 'fa-truck', 'items': [
                    {'endpoint': 'fournisseurs.index', 'icon': 'fa-truck', 'label': 'Fournisseurs',
                     'active_prefix': 'fournisseurs.'},
                ]
            })

        # --- RÉCLAMATIONS (si activé) ---
        if 'reclamations' in active_names:
            sections.append({
                'id': 'reclamations', 'title': 'Réclamations clients', 'icon': 'fa-headset', 'items': [
                    {'endpoint': 'reclamations.index', 'icon': 'fa-headset', 'label': 'Réclamations',
                     'active_prefix': 'reclamations.'},
                ]
            })

        # --- MAINTENANCE (si activé) ---
        if 'maintenance' in active_names:
            sections.append({
                'id': 'maintenance', 'title': 'Maintenance', 'icon': 'fa-tools', 'items': [
                    {'endpoint': 'maintenance.index', 'icon': 'fa-tools', 'label': 'Équipements & interventions',
                     'active_prefix': 'maintenance.'},
                ]
            })

        # --- LABORATOIRE (si activé) ---
        if 'laboratoire' in active_names:
            sections.append({
                'id': 'laboratoire', 'title': 'Laboratoire', 'icon': 'fa-flask', 'items': [
                    {'endpoint': 'laboratoire.index', 'icon': 'fa-flask', 'label': 'Plans d\'analyse',
                     'active_prefix': 'laboratoire.'},
                ]
            })

        # --- PLANIFICATION (si activé) ---
        if 'planification' in active_names:
            sections.append({
                'id': 'planification', 'title': 'Planification', 'icon': 'fa-calendar-alt', 'items': [
                    {'endpoint': 'planification.index', 'icon': 'fa-calendar-alt', 'label': 'Événements & calendrier',
                     'active_prefix': 'planification.'},
                ]
            })

        # --- RÉUNIONS & REVUES (si activé) ---
        if 'reunions' in active_names:
            sections.append({
                'id': 'reunions', 'title': 'Réunions & Revues', 'icon': 'fa-handshake', 'items': [
                    {'endpoint': 'reunions.index', 'icon': 'fa-handshake', 'label': 'Réunions',
                     'active_prefix': 'reunions.'},
                ]
            })

        # --- RH QHSE (si activé) ---
        if 'rh_qhse' in active_names:
            sections.append({
                'id': 'rh_qhse', 'title': 'RH QHSE', 'icon': 'fa-users', 'items': [
                    {'endpoint': 'rh_qhse.index', 'icon': 'fa-users', 'label': 'Employés & suivi RH',
                     'active_prefix': 'rh_qhse.'},
                ]
            })

        # --- CONNAISSANCES (si activé) ---
        if 'connaissances' in active_names:
            sections.append({
                'id': 'connaissances', 'title': 'Connaissances', 'icon': 'fa-brain', 'items': [
                    {'endpoint': 'connaissances.index', 'icon': 'fa-brain', 'label': 'REX & FAQ',
                     'active_prefix': 'connaissances.'},
                ]
            })

        # --- URGENCES (si activé) ---
        if 'urgences' in active_names:
            sections.append({
                'id': 'urgences', 'title': 'Gestion des urgences', 'icon': 'fa-ambulance', 'items': [
                    {'endpoint': 'urgences.index', 'icon': 'fa-ambulance', 'label': 'Plans & exercices',
                     'active_prefix': 'urgences.'},
                ]
            })

        # --- MON COMPTE (toujours présent) ---
        sections.append({
            'id': 'compte', 'title': 'Mon compte', 'icon': 'fa-user', 'items': [
                {'endpoint': 'users.profile', 'icon': None, 'label': None, 'is_profile': True},
                {'endpoint': 'facturation.index', 'icon': 'fa-credit-card', 'label': 'Facturation',
                 'active_prefix': 'facturation.'},
                {'endpoint': 'plans.index', 'icon': 'fa-crown', 'label': 'Mon abonnement',
                 'active_prefix': 'plans.'},
                {'endpoint': 'support.mes_tickets', 'icon': 'fa-ticket-alt', 'label': 'Mes tickets',
                 'active_prefix': 'support.'},
                {'endpoint': 'users.logout', 'icon': 'fa-sign-out-alt', 'label': 'Déconnexion',
                 'is_logout': True},
            ]
        })

        return sections

    def _get_module_sidebar_items(self, module_name: str) -> List[Dict]:
        """Fallback — les items sont maintenant dans get_sidebar_sections."""
        return []

    # -------------------------------------------------------------------------
    # Système d'événements inter-modules
    # -------------------------------------------------------------------------

    def on(self, event_name: str, handler: callable) -> None:
        """
        Enregistre un handler pour un événement donné.

        Args:
            event_name: Nom de l'événement (ex: 'nc.created', 'document.approved')
            handler: Fonction à appeler quand l'événement est émis
        """
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(handler)
        logger.debug("Event handler registered for '%s'", event_name)

    def emit(self, event_name: str, data: Dict = None) -> None:
        """
        Émet un événement vers tous les handlers enregistrés.

        Args:
            event_name: Nom de l'événement
            data: Données transmises aux handlers
        """
        handlers = self._event_handlers.get(event_name, [])
        for handler in handlers:
            try:
                handler(data or {})
            except Exception as e:
                logger.error(
                    "Error in event handler for '%s': %s",
                    event_name, str(e), exc_info=True
                )

    # -------------------------------------------------------------------------
    # Validation et diagnostics
    # -------------------------------------------------------------------------

    def validate_all(self) -> List[str]:
        """
        Valide l'intégrité de tous les modules enregistrés.

        Returns:
            Liste des erreurs trouvées (vide si tout est OK)
        """
        errors = []

        for name, manifest in self._modules.items():
            # Vérifier les dépendances
            for dep in manifest.requires:
                if dep not in self._modules:
                    errors.append(
                        f"Module '{name}' depends on '{dep}' which is not registered"
                    )

            # Vérifier la cohérence des permissions
            for perm in manifest.permissions:
                if '.' not in perm:
                    errors.append(
                        f"Module '{name}' has invalid permission format: '{perm}' "
                        f"(expected 'module.action')"
                    )

        return errors

    def get_stats(self) -> Dict:
        """
        Retourne des statistiques sur le registre.

        Returns:
            Dictionnaire avec les stats
        """
        return {
            'total_modules': len(self._modules),
            'categories': {
                cat: len(self.get_by_category(cat))
                for cat in set(m.category for m in self._modules.values())
            },
            'total_permissions': sum(
                len(m.permissions) for m in self._modules.values()
            ),
            'total_events': len(self._event_handlers),
        }


# =============================================================================
# Instance globale — Singleton partagé
# =============================================================================

plugin_manager = PluginManager()


# =============================================================================
# Decorator pour les routes protégées par module
# =============================================================================

def module_active(module_name: str):
    """
    Décorateur qui vérifie qu'un module est actif avant d'exécuter la route.

    Usage :
        @blueprint.route('/haccp/')
        @module_active('haccp')
        def index():
            ...

    Args:
        module_name: Identifiant du module requis
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_login import current_user
            from flask import abort

            if not current_user.is_authenticated:
                abort(401)

            if not plugin_manager.is_active(module_name, current_user.entreprise_id):
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Nécessaire pour le decorator
from functools import wraps
