"""Bootstrap de la base : permissions, rôles, entreprise par défaut, admin."""

from app import create_app, db
from app.models import Permission, Role, RolePermission, Utilisateur, Entreprise, SubscriptionPlan, EntrepriseRole
from datetime import datetime, date
import os
import secrets
from flask_migrate import stamp
from app.utils.permission_catalog import iter_permission_rows


def init_db():
    app = create_app()
    with app.app_context():
        # Créer les tables si elles n'existent pas
        db.create_all()

        # Marquer la version Alembic
        try:
            stamp(revision='head')
        except Exception:
            pass

        # Créer l'entreprise par défaut
        entreprise = Entreprise.query.filter_by(nom="Entreprise par défaut").first()
        if not entreprise:
            entreprise = Entreprise(
                nom="Entreprise par défaut",
                taille="PME",
                pays="Maroc",
                date_inscription=date.today(),
                modules_actifs=['hse'],
                statut="Actif"
            )
            db.session.add(entreprise)
            db.session.commit()

        # Créer les permissions
        for code, description, module in iter_permission_rows():
            if not Permission.query.filter_by(code=code).first():
                permission = Permission(code=code, description=description, module=module)
                db.session.add(permission)
        db.session.commit()

        # Créer le rôle Administrateur (super admin)
        role_admin = Role.query.filter_by(nom='Administrateur').first()
        if not role_admin:
            role_admin = Role(
                nom='Administrateur',
                description='Accès complet au système',
                est_systeme=True,
                personnalisable=False,
                date_creation=datetime.utcnow()
            )
            db.session.add(role_admin)
            db.session.commit()

        # Toutes les permissions au rôle admin
        for permission in Permission.query.all():
            if not RolePermission.query.filter_by(
                role_id=role_admin.id, permission_id=permission.id, entreprise_id=None
            ).first():
                rp = RolePermission(
                    role_id=role_admin.id, permission_id=permission.id,
                    entreprise_id=None, autorise=True
                )
                db.session.add(rp)
        db.session.commit()

        # Créer les rôles par défaut
        default_roles = ['Manager', 'Auditeur', 'Responsable operationnel', 'Consultant']
        created_roles = []
        for role_name in default_roles:
            role = Role.query.filter_by(nom=role_name).first()
            if not role:
                role = Role(
                    nom=role_name,
                    description=f'Rôle {role_name}',
                    est_systeme=False,
                    personnalisable=True,
                    date_creation=datetime.utcnow()
                )
                db.session.add(role)
                db.session.commit()
            created_roles.append(role)

        # Lier les rôles à l'entreprise
        for role in created_roles:
            if not EntrepriseRole.query.filter_by(entreprise_id=entreprise.id, role_id=role.id).first():
                er = EntrepriseRole(entreprise_id=entreprise.id, role_id=role.id)
                db.session.add(er)

        # Permissions aux rôles par défaut
        from app.utils.permission_catalog import get_default_enterprise_role_permissions
        default_perms = get_default_enterprise_role_permissions()
        for role in created_roles:
            perms_to_add = default_perms.get(role.nom, ())
            for code in perms_to_add:
                perm = Permission.query.filter_by(code=code).first()
                if not perm:
                    continue
                if not RolePermission.query.filter_by(
                    role_id=role.id, permission_id=perm.id, entreprise_id=entreprise.id
                ).first():
                    rp = RolePermission(
                        role_id=role.id, permission_id=perm.id,
                        entreprise_id=entreprise.id, autorise=True
                    )
                    db.session.add(rp)
        db.session.commit()

        # Créer l'utilisateur admin
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@qmsplatform.ma')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        admin = Utilisateur.query.filter_by(email=admin_email).first()
        if not admin:
            admin = Utilisateur(
                nom='Admin', prenom='System', email=admin_email,
                actif=True, role_id=role_admin.id, entreprise_id=entreprise.id,
                date_creation=datetime.utcnow()
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            # Lier aussi l'entreprise role
            if not EntrepriseRole.query.filter_by(entreprise_id=entreprise.id, role_id=role_admin.id).first():
                er = EntrepriseRole(entreprise_id=entreprise.id, role_id=role_admin.id)
                db.session.add(er)
            db.session.commit()

        # Créer les plans d'abonnement
        from app.utils.subscriptions import _seed_default_plans
        try:
            _seed_default_plans()
        except Exception:
            pass

        print("Base initialisée avec succès !")
        print(f"Admin: {admin_email} / {admin_password}")


if __name__ == '__main__':
    init_db()
