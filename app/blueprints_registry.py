def register_blueprints(app, api):
    """
    Enregistre tous les blueprints de l'application.
    """
    # --- Core (toujours actifs) ---
    from .main import main as main_bp
    from .users import users as users_bp
    from .admin import admin as admin_bp
    from .support import support as support_bp
    from .entreprises import entreprises as entreprises_bp

    api.register_blueprint(main_bp)
    api.register_blueprint(users_bp, url_prefix='/users')
    api.register_blueprint(admin_bp, url_prefix='/admin')
    api.register_blueprint(support_bp, url_prefix='/support')
    api.register_blueprint(entreprises_bp, url_prefix='/entreprises')

    # --- GED & Documents ---
    from .documents import blueprint as documents_bp
    api.register_blueprint(documents_bp, url_prefix='/documents')

    # --- Qualité ---
    from .actions import blueprint as actions_bp
    from .audit import blueprint as audit_bp
    from .indicateurs import blueprint as indicateurs_bp
    from .qualite import blueprint as qualite_bp
    from .nonconformites import blueprint as nonconformites_bp
    from .reclamations import blueprint as reclamations_bp
    from .fournisseurs import blueprint as fournisseurs_bp
    from .formations import blueprint as formations_bp
    from .ishikawa import blueprint as ishikawa_bp

    api.register_blueprint(actions_bp, url_prefix='/actions')
    api.register_blueprint(audit_bp, url_prefix='/audit')
    api.register_blueprint(indicateurs_bp, url_prefix='/indicateurs')
    api.register_blueprint(qualite_bp, url_prefix='/qualite')
    api.register_blueprint(nonconformites_bp, url_prefix='/nonconformites')
    api.register_blueprint(reclamations_bp, url_prefix='/reclamations')
    api.register_blueprint(fournisseurs_bp, url_prefix='/fournisseurs')
    api.register_blueprint(formations_bp, url_prefix='/formations')
    api.register_blueprint(ishikawa_bp, url_prefix='/ishikawa')

    # --- Objectifs qualité ---
    from .objectifs import blueprint as objectifs_bp
    api.register_blueprint(objectifs_bp, url_prefix='/objectifs')

    # --- HSE ---
    from .hse import blueprint as hse_bp
    from .textes import textes as textes_bp
    from .veille import veille as veille_bp
    from .conformite import blueprint as conformite_bp
    from .secteur import secteur as secteur_bp
    from .entreprise_textes import entreprise_textes as entreprise_textes_bp

    api.register_blueprint(hse_bp, url_prefix='/hse')
    api.register_blueprint(textes_bp, url_prefix='/admin/textes')
    api.register_blueprint(veille_bp, url_prefix='/admin/veille')
    api.register_blueprint(conformite_bp, url_prefix='/conformite')
    api.register_blueprint(secteur_bp, url_prefix='/secteur')
    api.register_blueprint(entreprise_textes_bp, url_prefix='/entreprise-textes')

    # --- HACCP ---
    from .haccp import blueprint as haccp_bp
    api.register_blueprint(haccp_bp, url_prefix='/haccp')

    # --- Processus & Workflows ---
    from .processus import blueprint as processus_bp
    from .change_management import blueprint as change_management_bp
    from .workflow_engine import blueprint as workflow_engine_bp

    api.register_blueprint(processus_bp, url_prefix='/processus')
    api.register_blueprint(change_management_bp, url_prefix='/change-management')
    api.register_blueprint(workflow_engine_bp, url_prefix='/workflow-engine')

    # --- Facturation & Plans ---
    from .facturation import facturation as facturation_bp
    from .plans import plans as plans_bp

    api.register_blueprint(facturation_bp, url_prefix='/facturation')
    api.register_blueprint(plans_bp, url_prefix='/plans')

    # --- Démo ---
    from .demo import demo as demo_bp
    api.register_blueprint(demo_bp, url_prefix='/demo')

    # --- Nouveaux modules ---
    from .environnement.routes import blueprint as environnement_bp
    from .maintenance.routes import blueprint as maintenance_bp
    from .laboratoire.routes import blueprint as laboratoire_bp
    from .planification.routes import blueprint as planification_bp
    from .reunions.routes import blueprint as reunions_bp
    from .rh_qhse.routes import blueprint as rh_qhse_bp
    from .connaissances.routes import blueprint as connaissances_bp
    from .urgences.routes import blueprint as urgences_bp

    api.register_blueprint(environnement_bp, url_prefix='/environnement')
    api.register_blueprint(maintenance_bp, url_prefix='/maintenance')
    api.register_blueprint(laboratoire_bp, url_prefix='/laboratoire')
    api.register_blueprint(planification_bp, url_prefix='/planification')
    api.register_blueprint(reunions_bp, url_prefix='/reunions')
    api.register_blueprint(rh_qhse_bp, url_prefix='/rh-qhse')
    api.register_blueprint(connaissances_bp, url_prefix='/connaissances')
    api.register_blueprint(urgences_bp, url_prefix='/urgences')
