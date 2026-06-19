# =============================================================================
# QMS Platform — All 23 Module Manifests
# =============================================================================
"""
Registre central des 23 modules de la plateforme QMS universelle.

Chaque module est un manifest qui définit :
- Son identifiant et nom d'affichage
- Sa catégorie
- Les modules dont il dépend
- Les permissions qu'il introduit
- Sa position dans le sidebar

Modules :
 01. pilotage        — Tableau de bord global, KPI, objectifs stratégiques
 02. ged             — Gestion électronique des documents
 03. veille          — Veille réglementaire & conformité
 04. processus       — Processus & workflows
 05. audits          — Audits internes/fournisseurs
 06. risques         — Risques & opportunités
 07. nc_capa         — Non-conformités & CAPA
 08. formations      — Formations & compétences
 09. rh_qhse         — Ressources humaines QHSE
 10. haccp           — HACCP / ISO 22000
 11. hse             — HSE / ISO 45001
 12. environnement   — Environnement / ISO 14001
 13. maintenance     — Maintenance
 14. laboratoire     — Laboratoire / qualité analytique
 15. fournisseurs    — Fournisseurs & achats
 16. performance     — Performance & KPI
 17. planification   — Planification & calendrier
 18. reunions        — Réunions & revues
 19. support         — Support & incidents
 20. notifications   — Notifications
 21. admin           — Administration
 22. connaissances   — Gestion des connaissances
 23. urgences        — Gestion des urgences

Auteur : QMS Platform Team
Version : 2.0.0
"""

from app.core.plugin_manager import ModuleManifest, plugin_manager


# =============================================================================
# 01. PILOTAGE — Tableau de bord global, KPI, objectifs stratégiques
# =============================================================================
PILOTAGE_MANIFEST = ModuleManifest(
    name='pilotage',
    display_name='Pilotage',
    version='1.0.0',
    description='Tableau de bord global, KPI & indicateurs, objectifs stratégiques, '
                'plans d\'action globaux, suivi des performances, alertes, '
                'reporting automatique, calendrier global.',
    icon='fa-tachometer-alt',
    category='pilotage',
    requires=[],
    permissions=['pilotage.voir', 'pilotage.gerer'],
    events_emit=['pilotage.kpi_alert', 'pilotage.objectif_reached'],
    events_consume=['nc.declared', 'audit.completed', 'action.overdue'],
    menu_position=10,
)

# =============================================================================
# 02. GED — Gestion électronique des documents
# =============================================================================
GED_MANIFEST = ModuleManifest(
    name='ged',
    display_name='GED / Documents',
    version='1.0.0',
    description='Création/dépôt, classification, versions, workflow d\'approbation, '
                'diffusion contrôlée, accusé de lecture, archivage légal, '
                'recherche avancée, modèles, documents obsolètes, gestion des accès.',
    icon='fa-folder-open',
    category='ged',
    requires=[],
    permissions=[
        'documents.voir', 'documents.upload', 'documents.workflow',
        'documents.archiver', 'documents.diffuser',
    ],
    events_emit=['document.uploaded', 'document.approved', 'document.archived',
                 'document.read', 'document.obsolete'],
    events_consume=[],
    menu_position=20,
)

# =============================================================================
# 03. VEILLE RÉGLEMENTAIRE & CONFORMITÉ
# =============================================================================
VEILLE_MANIFEST = ModuleManifest(
    name='veille',
    display_name='Veille Réglementaire',
    version='1.0.0',
    description='Bibliothèque réglementaire, textes légaux, normes ISO, '
                'exigences clients, suivi des mises à jour, alertes, '
                'évaluation de conformité, matrice, preuves, plans de mise en conformité.',
    icon='fa-satellite-dish',
    category='conformite',
    requires=[],
    permissions=[
        'textes.voir', 'textes.gerer',
        'conformite.voir', 'conformite.gerer',
    ],
    events_emit=['veille.update_available', 'conformite.evaluated', 'conformite.non_compliant'],
    events_consume=[],
    menu_position=30,
)

# =============================================================================
# 04. PROCESSUS & WORKFLOWS
# =============================================================================
PROCESSUS_MANIFEST = ModuleManifest(
    name='processus',
    display_name='Processus & Workflows',
    version='1.0.0',
    description='Cartographie des processus, fiches, interactions, BPMN, '
                'workflows automatisés, formulaires dynamiques, validation '
                'multi-niveaux, SOP, automatisation des tâches.',
    icon='fa-project-diagram',
    category='processus',
    requires=[],
    permissions=[
        'processus.voir', 'processus.gerer',
        'workflow_engine.voir', 'workflow_engine.gerer',
    ],
    events_emit=['processus.created', 'processus.updated',
                 'workflow.started', 'workflow.validated', 'workflow.rejected'],
    events_consume=[],
    menu_position=40,
)

# =============================================================================
# 05. AUDITS
# =============================================================================
AUDITS_MANIFEST = ModuleManifest(
    name='audits',
    display_name='Audits',
    version='1.0.0',
    description='Programme d\'audit, planification, audits internes/fournisseurs, '
                'checklists, constatations, non-conformités d\'audit, rapports, '
                'suivi des actions, efficacité des actions.',
    icon='fa-clipboard-check',
    category='qualite',
    requires=[],
    permissions=[
        'audit.voir', 'audit.gerer', 'audit.valider',
    ],
    events_emit=['audit.planned', 'audit.completed', 'audit.nc_found'],
    events_consume=[],
    menu_position=50,
)

# =============================================================================
# 06. RISQUES & OPPORTUNITÉS
# =============================================================================
RISQUES_MANIFEST = ModuleManifest(
    name='qualite',
    display_name='Qualité / ISO 9001',
    version='1.0.0',
    description='Système de management de la qualité ISO 9001 : risques, contexte, '
                'équipements, contrôle qualité, revue de direction, indicateurs, '
                'processus, workflows, Ishikawa, gestion des changements.',
    icon='fa-certificate',
    category='qualite',
    requires=[],
    permissions=['qualite.voir', 'qualite.gerer_risques'],
    events_emit=['risk.identified', 'risk.treated'],
    events_consume=[],
    menu_position=60,
)

# =============================================================================
# 07. NON-CONFORMITÉS & CAPA
# =============================================================================
NC_CAPA_MANIFEST = ModuleManifest(
    name='nc_capa',
    display_name='Non-Conformités & CAPA',
    version='1.0.0',
    description='Déclaration, classification, analyse des causes, actions correctives '
                'et préventives, suivi CAPA, vérification efficacité, clôture.',
    icon='fa-exclamation-triangle',
    category='qualite',
    requires=[],
    permissions=[
        'nonconformites.voir', 'nonconformites.gerer',
        'actions.voir', 'actions.gerer',
    ],
    events_emit=['nc.declared', 'nc.validated', 'capa.action_added', 'action.overdue'],
    events_consume=['audit.nc_found'],
    menu_position=70,
)

# =============================================================================
# 08. FORMATIONS & COMPÉTENCES
# =============================================================================
FORMATIONS_MANIFEST = ModuleManifest(
    name='formations',
    display_name='Formations & Compétences',
    version='1.0.0',
    description='Plan de formation, catalogue, sessions, inscriptions, présences, '
                'évaluations, certificats, matrice des compétences, habilitations, '
                'autorisations, polyvalence, expiration des habilitations.',
    icon='fa-graduation-cap',
    category='qualite',
    requires=[],
    permissions=['formations.voir', 'formations.gerer'],
    events_emit=['formation.completed', 'formation.expiring'],
    events_consume=[],
    menu_position=80,
)

# =============================================================================
# 09. RESSOURCES HUMAINES QHSE
# =============================================================================
RH_QHSE_MANIFEST = ModuleManifest(
    name='rh_qhse',
    display_name='RH QHSE',
    version='1.0.0',
    description='Employés, organigramme, affectations, EPI attribués, '
                'intégration nouveaux employés, suivi RH lié QHSE.',
    icon='fa-users',
    category='rh',
    requires=[],
    permissions=['rh.voir', 'rh.gerer'],
    events_emit=['rh.employee_joined', 'rh.epi_expiring'],
    events_consume=[],
    menu_position=90,
)

# =============================================================================
# 10. HACCP / ISO 22000
# =============================================================================
HACCP_MANIFEST = ModuleManifest(
    name='haccp',
    display_name='HACCP / ISO 22000',
    version='1.0.0',
    description='Produits & matières premières, diagrammes de fabrication, '
                'analyse des dangers, PRP, OPRP, CCP, limites critiques, '
                'surveillance, enregistrements, traçabilité, rappels, '
                'allergènes, nettoyage, corps étrangers, plan de contrôle.',
    icon='fa-utensils',
    category='haccp',
    requires=[],
    permissions=[
        'haccp.voir', 'haccp.gerer_processus', 'haccp.gerer_produits',
        'haccp.gerer_ccp', 'haccp.gerer_prp', 'haccp.gerer_tracabilite',
    ],
    events_emit=['haccp.ccp_non_conforme', 'haccp.rappel_produit', 'haccp.danger_identifie'],
    events_consume=[],
    menu_position=100,
)

# =============================================================================
# 11. HSE / ISO 45001
# =============================================================================
HSE_MANIFEST = ModuleManifest(
    name='hse',
    display_name='HSE / ISO 45001',
    version='1.0.0',
    description='Incidents, accidents, presqu\'accidents, analyse des causes, '
                'évaluation SST, DUERP, EPI, permis de travail, inspections, '
                'rondes, FDS, urgences, exercices, plans d\'urgence.',
    icon='fa-hard-hat',
    category='hse',
    requires=[],
    permissions=[
        'hse.voir', 'hse.gerer_incidents', 'hse.gerer_epi',
        'hse.gerer_inspections', 'hse.gerer_permis',
    ],
    events_emit=['hse.incident_declared', 'hse.inspection_completed', 'hse.epi_expiring'],
    events_consume=[],
    menu_position=110,
)

# =============================================================================
# 12. ENVIRONNEMENT / ISO 14001
# =============================================================================
ENVIRONNEMENT_MANIFEST = ModuleManifest(
    name='environnement',
    display_name='Environnement / ISO 14001',
    version='1.0.0',
    description='Aspects et impacts environnementaux, déchets, émissions, '
                'consommations (eau, énergie), plan de réduction, '
                'suivi environnemental, conformité environnementale.',
    icon='fa-leaf',
    category='environnement',
    requires=[],
    permissions=['environnement.voir', 'environnement.gerer'],
    events_emit=['environnement.alert_threshold', 'environnement.report_ready'],
    events_consume=[],
    menu_position=120,
)

# =============================================================================
# 13. MAINTENANCE
# =============================================================================
MAINTENANCE_MANIFEST = ModuleManifest(
    name='maintenance',
    display_name='Maintenance',
    version='1.0.0',
    description='Équipements, fiches machines, maintenance préventive/corrective, '
                'plans de maintenance, interventions, pièces de rechange, '
                'historique maintenance.',
    icon='fa-wrench',
    category='maintenance',
    requires=[],
    permissions=['maintenance.voir', 'maintenance.gerer'],
    events_emit=['maintenance.intervention_planned', 'maintenance.equipment_down'],
    events_consume=[],
    menu_position=130,
)

# =============================================================================
# 14. LABORATOIRE / QUALITÉ ANALYTIQUE
# =============================================================================
LABORATOIRE_MANIFEST = ModuleManifest(
    name='laboratoire',
    display_name='Laboratoire',
    version='1.0.0',
    description='Plans d\'analyse, échantillons, résultats, contrôle MP/PF, '
                'certificats d\'analyse, libération des lots, tendances qualité.',
    icon='fa-flask',
    category='qualite',
    requires=[],
    permissions=['laboratoire.voir', 'laboratoire.gerer'],
    events_emit=['laboratoire.result_ready', 'laboratoire.non_conforme'],
    events_consume=[],
    menu_position=140,
)

# =============================================================================
# 15. FOURNISSEURS & ACHATS
# =============================================================================
FOURNISSEURS_MANIFEST = ModuleManifest(
    name='fournisseurs',
    display_name='Fournisseurs & Achats',
    version='1.0.0',
    description='Base fournisseurs, évaluation, homologation, suivi performance, '
                'non-conformités fournisseurs, contrats, cahiers des charges.',
    icon='fa-truck',
    category='qualite',
    requires=[],
    permissions=['fournisseurs.voir', 'fournisseurs.gerer'],
    events_emit=['supplier.evaluated', 'supplier.nc'],
    events_consume=[],
    menu_position=150,
)

# =============================================================================
# 16. PERFORMANCE & KPI
# =============================================================================
PERFORMANCE_MANIFEST = ModuleManifest(
    name='performance',
    display_name='Performance & KPI',
    version='1.0.0',
    description='Tableaux de bord, indicateurs qualité/HSE/HACCP, '
                'rapports automatiques, analyse des tendances, comparatifs.',
    icon='fa-chart-bar',
    category='performance',
    requires=[],
    permissions=['indicateurs.voir', 'indicateurs.gerer'],
    events_emit=['kpi.threshold_reached', 'kpi.report_generated'],
    events_consume=[],
    menu_position=160,
)

# =============================================================================
# 17. PLANIFICATION
# =============================================================================
PLANIFICATION_MANIFEST = ModuleManifest(
    name='planification',
    display_name='Planification',
    version='1.0.0',
    description='Calendrier global, planification des audits, formations, '
                'inspections, maintenances, échéances réglementaires, '
                'visites médicales, rappels automatiques.',
    icon='fa-calendar-alt',
    category='planification',
    requires=[],
    permissions=['planification.voir', 'planification.gerer'],
    events_emit=['planification.event_soon', 'planification.overdue'],
    events_consume=[],
    menu_position=170,
)

# =============================================================================
# 18. RÉUNIONS & REVUES
# =============================================================================
REUNIONS_MANIFEST = ModuleManifest(
    name='reunions',
    display_name='Réunions & Revues',
    version='1.0.0',
    description='Réunions qualité/HACCP/sécurité, revues de direction, '
                'ordres du jour, comptes rendus, actions issues, '
                'suivi des décisions.',
    icon='fa-handshake',
    category='qualite',
    requires=[],
    permissions=['reunions.voir', 'reunions.gerer'],
    events_emit=['reunion.completed', 'reunion.action_assigned'],
    events_consume=[],
    menu_position=180,
)

# =============================================================================
# 19. SUPPORT & INCIDENTS
# =============================================================================
SUPPORT_MANIFEST = ModuleManifest(
    name='support',
    display_name='Support & Incidents',
    version='1.0.0',
    description='Tickets utilisateurs, centre d\'aide, FAQ interne, '
                'gestion des demandes, SLA support.',
    icon='fa-life-ring',
    category='support',
    requires=[],
    permissions=['support.voir', 'support.gerer'],
    events_emit=['ticket.created', 'ticket.escalated'],
    events_consume=[],
    menu_position=190,
)

# =============================================================================
# 20. NOTIFICATIONS
# =============================================================================
NOTIFICATIONS_MANIFEST = ModuleManifest(
    name='notifications',
    display_name='Notifications',
    version='1.0.0',
    description='Emails automatiques, SMS, alertes internes, '
                'notifications mobile, rappels d\'échéances.',
    icon='fa-bell',
    category='core',
    requires=[],
    permissions=['notifications.voir'],
    events_emit=['notification.sent'],
    events_consume=[
        'document.approved', 'nc.created', 'audit.planned',
        'formation.expiring', 'action.overdue', 'hse.epi_expiring',
    ],
    visible=False,
)

# =============================================================================
# 21. ADMINISTRATION
# =============================================================================
ADMIN_MANIFEST = ModuleManifest(
    name='admin',
    display_name='Administration',
    version='1.0.0',
    description='Utilisateurs, rôles & permissions, entreprises, sites/usines, '
                'modules activés, paramètres système, logs & audit système, '
                'plans & abonnements.',
    icon='fa-crown',
    category='admin',
    requires=[],
    permissions=[
        'admin.voir', 'admin.gerer', 'admin.users', 'admin.roles',
        'admin.entreprises', 'admin.system',
    ],
    events_emit=['admin.module_toggled', 'admin.user_created'],
    events_consume=[],
    visible=False,
)

# =============================================================================
# 22. GESTION DES CONNAISSANCES
# =============================================================================
CONNAISSANCES_MANIFEST = ModuleManifest(
    name='connaissances',
    display_name='Connaissances',
    version='1.0.0',
    description='Retours d\'expérience (REX), leçons apprises, '
                'base documentaire technique, FAQ interne, bonnes pratiques.',
    icon='fa-book-open',
    category='qualite',
    requires=[],
    permissions=['connaissances.voir', 'connaissances.gerer'],
    events_emit=['rex.published', 'faq.updated'],
    events_consume=[],
    menu_position=200,
)

# =============================================================================
# 23. GESTION DES URGENCES
# =============================================================================
URGENCES_MANIFEST = ModuleManifest(
    name='urgences',
    display_name='Gestion des Urgences',
    version='1.0.0',
    description='Plans d\'urgence, cellule de crise, exercices d\'évacuation, '
                'gestion incidents majeurs, main courante.',
    icon='fa-bolt',
    category='urgences',
    requires=[],
    permissions=['urgences.voir', 'urgences.gerer'],
    events_emit=['urgence.declared', 'urgence.drill_planned'],
    events_consume=[],
    menu_position=210,
)


# =============================================================================
# Enregistrement de tous les modules
# =============================================================================

ALL_MANIFESTS = [
    PILOTAGE_MANIFEST,
    GED_MANIFEST,
    VEILLE_MANIFEST,
    PROCESSUS_MANIFEST,
    AUDITS_MANIFEST,
    RISQUES_MANIFEST,
    NC_CAPA_MANIFEST,
    FORMATIONS_MANIFEST,
    RH_QHSE_MANIFEST,
    HACCP_MANIFEST,
    HSE_MANIFEST,
    ENVIRONNEMENT_MANIFEST,
    MAINTENANCE_MANIFEST,
    LABORATOIRE_MANIFEST,
    FOURNISSEURS_MANIFEST,
    PERFORMANCE_MANIFEST,
    PLANIFICATION_MANIFEST,
    REUNIONS_MANIFEST,
    SUPPORT_MANIFEST,
    NOTIFICATIONS_MANIFEST,
    ADMIN_MANIFEST,
    CONNAISSANCES_MANIFEST,
    URGENCES_MANIFEST,
]


def register_all_modules():
    """
    Enregistre les 23 modules auprès du PluginManager.
    Idempotent — les modules déjà enregistrés sont ignorés.
    """
    import logging
    logger = logging.getLogger(__name__)

    for manifest in ALL_MANIFESTS:
        try:
            plugin_manager.register(manifest)
        except ValueError:
            pass

    errors = plugin_manager.validate_all()
    for error in errors:
        logger.warning("Module validation: %s", error)

    stats = plugin_manager.get_stats()
    logger.info(
        "Registered %d modules (%d permissions, %d events)",
        stats['total_modules'], stats['total_permissions'], stats['total_events']
    )
