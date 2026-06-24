from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import current_user
from app.utils.permissions import access_required, system_admin_required
from app.admin import admin
from app import db
from app.models import (
    Permission, Role, RolePermission, EntrepriseRole,
    Utilisateur
)
from app.utils.permission_catalog import iter_permission_rows, PERMISSION_CATALOG, DEFAULT_ENTERPRISE_ROLE_PERMISSIONS


@admin.route('/roles')
@access_required()
@system_admin_required
def roles():
    roles = Role.query.order_by(Role.nom).all()
    permissions = list(iter_permission_rows())
    rps = RolePermission.query.filter_by(entreprise_id=None).all()
    role_perms = {}
    for rp in rps:
        perm = db.session.get(Permission, rp.permission_id)
        if perm:
            role_perms.setdefault(rp.role_id, set()).add(perm.code)
    return render_template('admin/roles.html', roles=roles, permissions=permissions,
                           permission_catalog=PERMISSION_CATALOG,
                           DEFAULT_ENTERPRISE_ROLE_PERMISSIONS=DEFAULT_ENTERPRISE_ROLE_PERMISSIONS,
                           role_perms=role_perms)


@admin.route('/roles/create', methods=['POST'])
@access_required()
@system_admin_required
def role_create():
    nom = request.form.get('nom', '').strip()
    description = request.form.get('description', '').strip()
    if not nom:
        flash('Le nom du rôle est requis.', 'danger')
        return redirect(url_for('admin.roles'))
    existing = Role.query.filter_by(nom=nom).first()
    if existing:
        flash('Un rôle avec ce nom existe déjà.', 'danger')
        return redirect(url_for('admin.roles'))
    role = Role(nom=nom, description=description, personnalisable=True, cree_par=current_user.id)
    db.session.add(role)
    db.session.flush()
    permission_codes = request.form.getlist('permissions')
    for code in permission_codes:
        perm = Permission.query.filter_by(code=code).first()
        if perm:
            rp = RolePermission(role_id=role.id, permission_id=perm.id, autorise=True)
            db.session.add(rp)
    db.session.commit()
    flash(f'Rôle "{nom}" créé avec succès.', 'success')
    return redirect(url_for('admin.roles'))


@admin.route('/roles/<int:role_id>/edit')
@access_required()
@system_admin_required
def role_edit(role_id):
    role = db.session.get(Role, role_id)
    if not role:
        abort(404)
    rps = RolePermission.query.filter_by(role_id=role.id, entreprise_id=None).all()
    role_perm_set = set()
    for rp in rps:
        perm = db.session.get(Permission, rp.permission_id)
        if perm:
            role_perm_set.add(perm.code)
    return render_template('admin/role_edit.html', role=role,
                           role_perm_set=role_perm_set,
                           permission_catalog=PERMISSION_CATALOG)


@admin.route('/roles/<int:role_id>/update', methods=['POST'])
@access_required()
@system_admin_required
def role_update(role_id):
    role = db.session.get(Role, role_id)
    if not role:
        abort(404)
    description = request.form.get('description', '').strip()
    if description:
        role.description = description
    selected_codes = set(request.form.getlist('permissions'))
    existing_rps = RolePermission.query.filter_by(role_id=role.id, entreprise_id=None).all()
    for rp in existing_rps:
        perm = db.session.get(Permission, rp.permission_id)
        if perm and perm.code not in selected_codes:
            db.session.delete(rp)
        elif perm and perm.code in selected_codes:
            selected_codes.discard(perm.code)
    for code in selected_codes:
        perm = Permission.query.filter_by(code=code).first()
        if perm:
            rp = RolePermission(role_id=role.id, permission_id=perm.id, entreprise_id=None, autorise=True)
            db.session.add(rp)
    db.session.commit()
    flash(f'Rôle "{role.nom}" mis à jour.', 'success')
    return redirect(url_for('admin.roles'))


@admin.route('/roles/<int:role_id>/delete', methods=['POST'])
@access_required()
@system_admin_required
def role_delete(role_id):
    role = db.session.get(Role, role_id)
    if not role:
        abort(404)
    if not role.personnalisable:
        flash('Ce rôle système ne peut pas être supprimé.', 'danger')
        return redirect(url_for('admin.roles'))
    if Utilisateur.query.filter_by(role_id=role.id).count() > 0:
        flash('Ce rôle est attribué à des utilisateurs.', 'danger')
        return redirect(url_for('admin.roles'))
    RolePermission.query.filter_by(role_id=role.id).delete()
    EntrepriseRole.query.filter_by(role_id=role.id).delete()
    db.session.delete(role)
    db.session.commit()
    flash(f'Rôle "{role.nom}" supprimé.', 'success')
    return redirect(url_for('admin.roles'))


@admin.route('/permissions')
@access_required()
@system_admin_required
def permissions():
    perms = list(iter_permission_rows())
    return render_template('admin/permissions.html', permissions=perms,
                           permission_catalog=PERMISSION_CATALOG)
