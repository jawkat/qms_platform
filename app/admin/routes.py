from flask import render_template
from flask_login import login_required, current_user
from app.admin import admin


@admin.route('/')
@login_required
def dashboard():
    if not current_user.role or not current_user.role.est_systeme:
        from flask import abort
        abort(403)
    return render_template('admin/dashboard.html')
