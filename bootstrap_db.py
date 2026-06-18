#!/usr/bin/env python3
"""Bootstrap the database with default data."""
import os
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'sqlite:///data.db')

from app import create_app, db
from app.models import (
    Domaine, TexteReglementaire, TexteVersion, Article,
    Permission, RolePermission, Role, Utilisateur,
    Entreprise, Secteur,
)
from app.utils.subscriptions import _seed_default_plans
from app.utils.permission_catalog import iter_permission_rows


def bootstrap():
    app = create_app()
    with app.app_context():
        db.create_all()

        # 1. Domaines par défaut
        print('Création des domaines...')
        domaines = ['HSE', 'Environnement', 'Sécurité', 'Qualité', 'Social']
        for nom in domaines:
            if not Domaine.query.filter_by(nom=nom).first():
                db.session.add(Domaine(nom=nom, description=f'Domaine {nom}'))
                print(f'  + Domaine {nom}')
        db.session.commit()

        # 2. Plans d'abonnement
        print('Création des plans d\'abonnement...')
        _seed_default_plans()
        print('  + Plans créés')

        # 3. Rôles par défaut
        print('Création des rôles...')
        roles_data = [
            ('System Admin', True, False, 'Administrateur système avec tous les accès'),
            ('Manager', False, True, 'Gestionnaire d\'entreprise'),
            ('Auditeur', False, True, 'Auditeur interne/externe'),
            ('Responsable operationnel', False, True, 'Opérateur terrain'),
            ('Consultant', False, True, 'Consultant externe'),
        ]
        roles = {}
        for nom, est_sys, perso, desc in roles_data:
            role = Role.query.filter_by(nom=nom).first()
            if not role:
                role = Role(nom=nom, est_systeme=est_sys, personnalisable=perso, description=desc)
                db.session.add(role)
                db.session.flush()
                print(f'  + Rôle {nom}')
            roles[nom] = role
        db.session.commit()

        # 4. Permissions depuis le catalogue
        print('Création des permissions...')
        for code, desc, module in iter_permission_rows():
            if not Permission.query.filter_by(code=code).first():
                db.session.add(Permission(code=code, description=desc, module=module))
                print(f'  + Permission {code}')
        db.session.commit()

        # 5. Assigner les permissions aux rôles entreprise
        print('Affectation des permissions aux rôles...')
        role_perms = {
            'Manager': [
                'users.voir', 'users.cree', 'users.modifier',
                'actions.voir', 'actions.cree', 'actions.modifier',
                'documents.voir', 'documents.upload', 'documents.archiver',
                'textes.voir', 'textes.modifier',
                'conformite.voir', 'conformite.modifier',
                'audit.voir', 'audit.cree', 'audit.modifier',
                'qualite.voir', 'qualite.gerer_risques', 'qualite.gerer_haccp',
                'qualite.gerer_clients', 'qualite.gerer_fournisseurs',
                'qualite.gerer_formations', 'qualite.gerer_equipements',
                'qualite.gerer_controle', 'qualite.gerer_revue',
            ],
            'Auditeur': [
                'actions.voir', 'documents.voir', 'textes.voir',
                'conformite.voir', 'audit.voir', 'audit.cree', 'qualite.voir',
            ],
            'Responsable operationnel': [
                'actions.voir', 'actions.cree', 'documents.voir', 'documents.upload',
                'conformite.voir', 'conformite.modifier', 'qualite.voir',
            ],
            'Consultant': [
                'actions.voir', 'documents.voir', 'textes.voir',
                'conformite.voir', 'audit.voir', 'qualite.voir',
            ],
        }
        for nom, perm_codes in role_perms.items():
            role = roles.get(nom)
            if not role:
                continue
            for code in perm_codes:
                perm = Permission.query.filter_by(code=code).first()
                if not perm:
                    continue
                existing = RolePermission.query.filter_by(
                    role_id=role.id, permission_id=perm.id,
                ).first()
                if not existing:
                    db.session.add(RolePermission(role_id=role.id, permission_id=perm.id, autorise=True))
        db.session.commit()
        print('  + Permissions affectées')

        # 6. Secteurs d'activité
        print('Création des secteurs...')
        secteurs_data = [
            ('Agroalimentaire', 'Industrie agroalimentaire'),
            ('Chimie', 'Industrie chimique et pétrochimique'),
            ('BTP', 'Bâtiment et travaux publics'),
            ('Énergie', 'Secteur de l\'énergie'),
            ('Santé', 'Secteur de la santé'),
        ]
        for nom, desc in secteurs_data:
            if not Secteur.query.filter_by(nom=nom).first():
                db.session.add(Secteur(nom=nom, description=desc))
                print(f'  + Secteur {nom}')
        db.session.commit()

        # 7. Admin utilisateur
        print('Création de l\'utilisateur admin...')
        admin_role = roles.get('System Admin')
        if not Utilisateur.query.filter_by(email='admin@qmsplatform.ma').first():
            admin = Utilisateur(
                nom='Admin', prenom='System',
                email='admin@qmsplatform.ma', actif=True,
                role_id=admin_role.id,
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print('  + Utilisateur admin@qmsplatform.ma créé')
        else:
            print('  ~ Utilisateur admin déjà existant')
        db.session.commit()

        # 8. Demo entreprise
        print('Création de l\'entreprise démo...')
        if not Entreprise.query.filter_by(nom='Demo SARL').first():
            db.session.add(Entreprise(nom='Demo SARL', pays='Maroc', taille='PME'))
            print('  + Entreprise Demo SARL créée')
        db.session.commit()

        print()
        print('✓ Base de données initialisée avec succès.')


if __name__ == '__main__':
    bootstrap()
