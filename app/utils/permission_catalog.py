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
    'qualite': [
        ('qualite.voir', 'Voir le tableau de bord qualite'),
        ('qualite.gerer_risques', 'Gerer les risques et opportunites'),
        ('qualite.gerer_haccp', 'Gerer le plan HACCP'),
        ('qualite.gerer_clients', 'Gerer les reclamations clients'),
        ('qualite.gerer_fournisseurs', 'Gerer les fournisseurs'),
        ('qualite.gerer_formations', 'Gerer les formations'),
        ('qualite.gerer_equipements', 'Gerer les equipements'),
        ('qualite.gerer_controle', 'Gerer le controle qualite'),
        ('qualite.gerer_revue', 'Gerer la revue de direction'),
        ('qualite.gerer_nonconformites', 'Gerer les non-conformites qualite'),
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
        'qualite.voir', 'qualite.gerer_risques', 'qualite.gerer_haccp',
        'qualite.gerer_clients', 'qualite.gerer_fournisseurs',
        'qualite.gerer_formations', 'qualite.gerer_equipements',
        'qualite.gerer_controle', 'qualite.gerer_revue',
        'qualite.gerer_nonconformites',
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
