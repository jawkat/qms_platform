import logging
from contextvars import ContextVar
import sqlalchemy as sa
from sqlalchemy import event
from app import db

logger = logging.getLogger(__name__)

current_entreprise_id = ContextVar('current_entreprise_id', default=None)
current_is_system_admin = ContextVar('current_is_system_admin', default=False)


def set_current_entreprise(eid, is_system_admin=False):
    current_entreprise_id.set(eid)
    current_is_system_admin.set(is_system_admin)


def clear_current_entreprise():
    current_entreprise_id.set(None)
    current_is_system_admin.set(False)


def get_current_entreprise():
    return current_entreprise_id.get()


def tenant_get_or_404(model, obj_id):
    from flask import abort
    eid = current_entreprise_id.get()
    if current_is_system_admin.get():
        obj = db.session.get(model, obj_id)
    else:
        try:
            obj = model.query.filter_by(id=obj_id, entreprise_id=eid).first()
        except Exception:
            obj = db.session.get(model, obj_id)
    if not obj:
        abort(404)
    return obj


def _collect_tables(from_element):
    """Récupère récursivement toutes les tables d'une clause FROM."""
    if isinstance(from_element, sa.Table):
        return [from_element]
    if isinstance(from_element, sa.Join):
        return _collect_tables(from_element.left) + _collect_tables(from_element.right)
    if isinstance(from_element, sa.sql.Alias):
        return _collect_tables(from_element.element)
    if isinstance(from_element, sa.Select):
        tables = []
        for f in from_element.froms:
            tables.extend(_collect_tables(f))
        return tables
    return []


def _discover_scoped_models():
    """Découvre dynamiquement tous les modèles avec entreprise_id NOT NULL.

    Exclut les tables de jonction (EntrepriseSecteur) et les modèles
    dont entreprise_id est nullable (RolePermission, Ticket).
    Utilisateur est ajouté manuellement car son entreprise_id est nullable
    mais doit être filtré pour les utilisateurs non-admin.
    """
    EXCLUDED_NAMES = {'EntrepriseSecteur'}

    models = []
    for mapper in db.Model.registry.mappers:
        model = mapper.class_
        if model.__name__ in EXCLUDED_NAMES:
            continue
        try:
            columns = [c for c in mapper.columns if c.key == 'entreprise_id']
        except Exception:
            continue
        if columns and not columns[0].nullable:
            models.append(model)

    from app.models import Utilisateur
    models.append(Utilisateur)

    logger.info("Découverte auto — %d modèles scopés", len(models))
    return models


SCOPED_MODELS = []


def init_tenant_scope(app):
    global SCOPED_MODELS
    SCOPED_MODELS = _discover_scoped_models()

    def _add_global_tenant_scope(orm_execute_state):
        eid = current_entreprise_id.get()
        if eid is None:
            return
        if current_is_system_admin.get():
            return
        if not orm_execute_state.is_select:
            return

        stmt = orm_execute_state.statement

        tables_in_query = set()
        for f in stmt.froms:
            tables_in_query.update(_collect_tables(f))

        for model_cls in SCOPED_MODELS:
            try:
                if model_cls.__table__ in tables_in_query:
                    stmt = stmt.where(model_cls.__table__.c.entreprise_id == eid)
            except Exception:
                pass

        orm_execute_state.statement = stmt

    from sqlalchemy.orm import Session as SASession
    event.listen(SASession, 'do_orm_execute', _add_global_tenant_scope, named=True)
