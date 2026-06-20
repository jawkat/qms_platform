from app import create_app, db
from app.models.auth import Utilisateur, Role

app = create_app()
with app.app_context():
    users = Utilisateur.query.all()
    print("-" * 50)
    for u in users:
        role_name = u.role.nom if u.role else 'No Role'
        is_sys = u.role.est_systeme if u.role else False
        print(f"User: {u.email} | Role: {role_name} | System: {is_sys}")
    print("-" * 50)
