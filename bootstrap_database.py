"""Bootstrap de la base : permissions, rôles, entreprise par défaut, admin."""

from app import create_app, db
from app.models import Permission, Role, RolePermission, Utilisateur, Entreprise, SubscriptionPlan, EntrepriseRole
from datetime import datetime, date
import os
import secrets
from flask_migrate import stamp
from app.utils.permission_catalog import iter_permission_rows


def _run_migrations():
    """Ajoute les colonnes manquantes si la table existe déjà (migration sans Alembic)."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())

    if 'entreprise' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('entreprise')}
        with db.engine.connect() as conn:
            if 'telephone' not in cols:
                conn.execute(text('ALTER TABLE entreprise ADD COLUMN telephone VARCHAR(20)'))
            if 'periode_essai_jours' not in cols:
                conn.execute(text('ALTER TABLE entreprise ADD COLUMN periode_essai_jours INTEGER DEFAULT 14'))
            if 'date_debut_essai' not in cols:
                conn.execute(text('ALTER TABLE entreprise ADD COLUMN date_debut_essai TIMESTAMP'))
            conn.commit()

    if 'utilisateur' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('utilisateur')}
        with db.engine.connect() as conn:
            if 'telephone' not in cols:
                conn.execute(text('ALTER TABLE utilisateur ADD COLUMN telephone VARCHAR(20)'))
            conn.commit()

    if 'processus_haccp' in existing_tables:
        with db.engine.connect() as conn:
            if 'haccp_processus' not in existing_tables:
                conn.execute(text('ALTER TABLE processus_haccp RENAME TO haccp_processus'))
                result = conn.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='haccp_processus'"
                ))
                new_cols = {row[0] for row in result}
                if 'type_danger' not in new_cols:
                    conn.execute(text("ALTER TABLE haccp_processus ADD COLUMN type_danger VARCHAR(20) DEFAULT 'biologique'"))
                if 'description' not in new_cols:
                    conn.execute(text('ALTER TABLE haccp_processus ADD COLUMN description TEXT'))
                if 'frequence_surveillance' not in new_cols:
                    conn.execute(text('ALTER TABLE haccp_processus ADD COLUMN frequence_surveillance VARCHAR(100)'))
                if 'num_ccp' not in new_cols:
                    conn.execute(text('ALTER TABLE haccp_processus ADD COLUMN num_ccp VARCHAR(10)'))
                print("-> Table 'processus_haccp' renommée en 'haccp_processus' avec colonnes ajoutées.")
            else:
                conn.execute(text('DROP TABLE IF EXISTS processus_haccp CASCADE'))
                print("-> Table obsolète 'processus_haccp' supprimée (déjà remplacée par 'haccp_processus').")
            conn.commit()

    if 'proof_master' in existing_tables:
        cols = {c['name'] for c in inspector.get_columns('proof_master')}
        with db.engine.connect() as conn:
            if 'dossier_id' not in cols:
                conn.execute(text('ALTER TABLE proof_master ADD COLUMN dossier_id INTEGER REFERENCES dossier(id) ON DELETE SET NULL'))
                conn.execute(text('CREATE INDEX ix_proof_master_dossier_id ON proof_master(dossier_id)'))
            if 'type_document_id' not in cols:
                conn.execute(text('ALTER TABLE proof_master ADD COLUMN type_document_id INTEGER REFERENCES type_document(id) ON DELETE SET NULL'))
            if 'workflow_statut' not in cols:
                conn.execute(text("ALTER TABLE proof_master ADD COLUMN workflow_statut VARCHAR(30) DEFAULT 'brouillon'"))
                conn.execute(text('CREATE INDEX ix_proof_master_workflow_statut ON proof_master(workflow_statut)'))
            if 'workflow_approbateur_id' not in cols:
                conn.execute(text('ALTER TABLE proof_master ADD COLUMN workflow_approbateur_id INTEGER REFERENCES utilisateur(id)'))
            if 'date_soumission' not in cols:
                conn.execute(text('ALTER TABLE proof_master ADD COLUMN date_soumission TIMESTAMP'))
            if 'date_approbation' not in cols:
                conn.execute(text('ALTER TABLE proof_master ADD COLUMN date_approbation TIMESTAMP'))
            if 'numero_document' not in cols:
                conn.execute(text('ALTER TABLE proof_master ADD COLUMN numero_document VARCHAR(50)'))
            if 'mots_cles' not in cols:
                conn.execute(text('ALTER TABLE proof_master ADD COLUMN mots_cles VARCHAR(500)'))
            if 'notes' not in cols:
                conn.execute(text('ALTER TABLE proof_master ADD COLUMN notes TEXT'))
            conn.commit()


def init_db():
    app = create_app()
    with app.app_context():
        _run_migrations()

        # Créer les tables si elles n'existent pas
        db.create_all()

        # Créer l'entreprise par défaut
        entreprise = Entreprise.query.filter_by(nom="Entreprise par défaut").first()
        if not entreprise:
            entreprise = Entreprise(
                nom="Entreprise par défaut",
                taille="PME",
                pays="Maroc",
                date_inscription=date.today(),
                modules_actifs=['hse', 'qualite', 'haccp', 'ged'],
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

        # Permissions aux rôles par défaut (globales + entreprise par défaut)
        from app.utils.permission_catalog import get_default_enterprise_role_permissions
        default_perms = get_default_enterprise_role_permissions()
        for role in created_roles:
            perms_to_add = default_perms.get(role.nom, ())
            for code in perms_to_add:
                perm = Permission.query.filter_by(code=code).first()
                if not perm:
                    continue
                # Globale (toutes les entreprises)
                if not RolePermission.query.filter_by(
                    role_id=role.id, permission_id=perm.id, entreprise_id=None
                ).first():
                    db.session.add(RolePermission(
                        role_id=role.id, permission_id=perm.id,
                        entreprise_id=None, autorise=True
                    ))
                # Entreprise par défaut
                if not RolePermission.query.filter_by(
                    role_id=role.id, permission_id=perm.id, entreprise_id=entreprise.id
                ).first():
                    db.session.add(RolePermission(
                        role_id=role.id, permission_id=perm.id,
                        entreprise_id=entreprise.id, autorise=True
                    ))
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
