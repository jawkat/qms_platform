PERMISSION_CATALOG = {
    'users': [
        ('users.voir', 'Voir la liste des utilisateurs'),
        ('users.cree', 'Creer un utilisateur'),
        ('users.modifier', 'Modifier un utilisateur'),
        ('users.supprimer', 'Supprimer un utilisateur'),
    ],
    'actions': [
        ('actions.voir', 'Voir les actions'),
        ('actions.cree', 'Creer une action'),
        ('actions.modifier', 'Modifier une action'),
        ('actions.supprimer', 'Supprimer une action'),
    ],
    'documents': [
        ('documents.voir', 'Voir la bibliotheque documents'),
        ('documents.upload', 'Uploader un document'),
        ('documents.archiver', 'Archiver/Supprimer un document'),
        ('documents.workflow', 'Soumettre/Approuver/Rejeter (workflow documentaire)'),
    ],
    'textes': [
        ('textes.voir', 'Voir les textes reglementaires'),
        ('textes.modifier', 'Modifier les textes'),
    ],
    'conformite': [
        ('conformite.voir', 'Voir les evaluations'),
        ('conformite.modifier', 'Evaluer les articles'),
    ],
    'entreprises': [
        ('entreprises.voir', 'Voir les entreprises'),
        ('entreprises.cree', 'Creer une entreprise'),
        ('entreprises.modifier', 'Modifier une entreprise'),
        ('entreprises.supprimer', 'Supprimer une entreprise'),
    ],
    'facturation': [
        ('facturation.voir', 'Voir la facturation'),
        ('facturation.gerer', 'Gerer les paiements'),
    ],
    'plans': [
        ('plans.voir', 'Voir les plans d abonnement'),
        ('plans.gerer', 'Gerer les plans d abonnement'),
    ],
    'secteur': [
        ('secteur.voir', 'Voir les secteurs'),
        ('secteur.cree', 'Creer un secteur'),
        ('secteur.modifier', 'Modifier/Supprimer un secteur'),
        ('secteur.gerer_textes', 'Gerer les textes lies aux secteurs'),
    ],
    'entreprise_textes': [
        ('entreprise_textes.lier', 'Lier/Delier des textes'),
        ('entreprise_textes.evaluate', 'Lancer des evaluations'),
    ],
    'support': [
        ('support.voir', 'Voir les tickets'),
        ('support.cree', 'Creer un ticket'),
        ('support.fermer', 'Fermer un ticket'),
    ],
    'indicateurs': [
        ('indicateurs.voir', 'Voir les indicateurs'),
        ('indicateurs.cree', 'Creer un indicateur'),
        ('indicateurs.modifier', 'Modifier/Supprimer un indicateur'),
    ],
    'admin': [
        ('admin.voir_roles', 'Gerer les roles et permissions'),
    ],
    'audit': [
        ('audit.voir', 'Voir les audits'),
        ('audit.cree', 'Creer un audit'),
        ('audit.modifier', 'Modifier un audit'),
    ],
    'fournisseurs': [
        ('fournisseurs.voir', 'Voir les fournisseurs'),
        ('fournisseurs.gerer', 'Gerer les fournisseurs'),
    ],
    'formations': [
        ('formations.voir', 'Voir les formations'),
        ('formations.gerer', 'Gerer les formations'),
    ],
    'reclamations': [
        ('reclamations.voir', 'Voir les reclamations'),
        ('reclamations.gerer', 'Gerer les reclamations'),
    ],
    'qualite': [
        ('qualite.voir', 'Voir le tableau de bord qualite'),
        ('qualite.gerer_risques', 'Gerer les risques et opportunites'),
        ('qualite.gerer_clients', 'Gerer les reclamations clients'),
        ('qualite.gerer_fournisseurs', 'Gerer les fournisseurs'),
        ('qualite.gerer_formations', 'Gerer les formations'),
        ('qualite.gerer_equipements', 'Gerer les equipements'),
        ('qualite.gerer_controle', 'Gerer le controle qualite'),
        ('qualite.gerer_revue', 'Gerer la revue de direction'),
    ],
    'haccp': [
        ('haccp.voir', 'Voir le tableau de bord HACCP'),
        ('haccp.gerer_processus', 'Gerer les processus et diagrammes'),
        ('haccp.gerer_produits', 'Gerer les produits et recettes'),
        ('haccp.gerer_dangers', 'Gerer l analyse des dangers'),
        ('haccp.gerer_ccp', 'Gerer les CCP et limites critiques'),
        ('haccp.gerer_enregistrements', 'Gerer les enregistrements CCP'),
        ('haccp.gerer_prp', 'Gerer les programmes prerequis'),
        ('haccp.gerer_tracabilite', 'Gerer la tracabilite'),
        ('haccp.gerer_fournisseurs', 'Gerer les fournisseurs'),
        ('haccp.gerer_formations', 'Gerer les formations'),
        ('haccp.gerer_reclamations', 'Gerer les reclamations clients'),
        ('haccp.gerer_rappels', 'Gerer les rappels produits'),
    ],
    'nonconformites': [
        ('nonconformites.voir', 'Voir les non-conformites'),
        ('nonconformites.gerer', 'Gerer les non-conformites'),
        ('nonconformites.valider_cloture', 'Valider la cloture des non-conformites'),
    ],
    'ishikawa': [
        ('ishikawa.voir', 'Voir les analyses Ishikawa'),
        ('ishikawa.gerer', 'Gerer les analyses Ishikawa'),
    ],
    'hse': [
        ('hse.voir_incidents', 'Voir les incidents et accidents'),
        ('hse.gerer_incidents', 'Gerer les incidents et accidents'),
        ('hse.voir_epi', 'Voir les EPI'),
        ('hse.gerer_epi', 'Gerer les EPI'),
        ('hse.voir_inspections', 'Voir les inspections'),
        ('hse.gerer_inspections', 'Gerer les inspections'),
        ('hse.voir_permis', 'Voir les permis de travail'),
        ('hse.gerer_permis', 'Gerer les permis de travail'),
        ('hse.voir_risques', 'Voir les risques HSE'),
        ('hse.gerer_risques', 'Gerer les risques HSE'),
    ],
}

PERMISSION_INDEX = {}
for module, perms in PERMISSION_CATALOG.items():
    for code, desc in perms:
        PERMISSION_INDEX[code] = {'description': desc, 'module': module}

DEFAULT_ENTERPRISE_ROLE_PERMISSIONS = {
    'Manager': (
        'users.voir', 'users.cree', 'users.modifier',
        'actions.voir', 'actions.cree', 'actions.modifier',
        'documents.voir', 'documents.upload', 'documents.archiver', 'documents.workflow',
        'textes.voir', 'textes.modifier',
        'conformite.voir', 'conformite.modifier',
        'secteur.voir', 'secteur.cree', 'secteur.modifier', 'secteur.gerer_textes',
        'entreprise_textes.lier', 'entreprise_textes.evaluate',
        'support.voir', 'support.cree', 'support.fermer',
        'indicateurs.voir', 'indicateurs.cree', 'indicateurs.modifier',
        'audit.voir', 'audit.cree', 'audit.modifier',
        'qualite.voir', 'qualite.gerer_risques',
        'qualite.gerer_clients', 'qualite.gerer_fournisseurs',
        'qualite.gerer_formations', 'qualite.gerer_equipements',
        'qualite.gerer_controle', 'qualite.gerer_revue',
        'haccp.voir', 'haccp.gerer_processus', 'haccp.gerer_produits',
        'haccp.gerer_dangers', 'haccp.gerer_ccp', 'haccp.gerer_enregistrements',
        'haccp.gerer_prp', 'haccp.gerer_tracabilite',
        'haccp.gerer_fournisseurs', 'haccp.gerer_formations',
        'haccp.gerer_reclamations', 'haccp.gerer_rappels',
        'fournisseurs.voir', 'fournisseurs.gerer',
        'formations.voir', 'formations.gerer',
        'reclamations.voir', 'reclamations.gerer',
        'nonconformites.voir', 'nonconformites.gerer', 'nonconformites.valider_cloture',
        'hse.voir_incidents', 'hse.gerer_incidents', 'hse.voir_epi', 'hse.gerer_epi',
        'hse.voir_inspections', 'hse.gerer_inspections', 'hse.voir_permis', 'hse.gerer_permis',
        'hse.voir_risques', 'hse.gerer_risques',
        'ishikawa.voir', 'ishikawa.gerer',
        'entreprises.voir', 'entreprises.cree', 'entreprises.modifier',
        'facturation.voir', 'facturation.gerer',
        'plans.voir', 'plans.gerer',
    ),
    'Auditeur': (
        'actions.voir',
        'documents.voir',
        'textes.voir',
        'conformite.voir',
        'audit.voir', 'audit.cree',
        'qualite.voir',
    ),
    'Responsable operationnel': (
        'actions.voir', 'actions.cree',
        'documents.voir', 'documents.upload',
        'conformite.voir', 'conformite.modifier',
        'qualite.voir',
    ),
    'Consultant': (
        'actions.voir',
        'documents.voir',
        'textes.voir',
        'conformite.voir',
        'audit.voir',
        'qualite.voir',
    ),
}


def iter_permission_rows():
    for module, perms in PERMISSION_CATALOG.items():
        for code, desc in perms:
            yield code, desc, module


def is_known_permission(code):
    return code in PERMISSION_INDEX


def get_permission_definition(code):
    return PERMISSION_INDEX.get(code)


def get_default_enterprise_role_permissions():
    return DEFAULT_ENTERPRISE_ROLE_PERMISSIONS
