import logging
from contextvars import ContextVar
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
        obj = model.query.filter_by(id=obj_id, entreprise_id=eid).first()
    if not obj:
        abort(404)
    return obj


def init_tenant_scope(app):
    from app.models import ActionCorrective, ProofMaster, Audit, \
        IndicateurValeur, EntrepriseTexte, EvaluationArticle, EntrepriseRole, Utilisateur

    SCOPED_MODELS = {
        Utilisateur: lambda cls: cls.entreprise_id == current_entreprise_id.get(),
        ActionCorrective: lambda cls: cls.entreprise_id == current_entreprise_id.get(),
        ProofMaster: lambda cls: cls.entreprise_id == current_entreprise_id.get(),
        Audit: lambda cls: cls.entreprise_id == current_entreprise_id.get(),
        IndicateurValeur: lambda cls: cls.entreprise_id == current_entreprise_id.get(),
        EntrepriseTexte: lambda cls: cls.entreprise_id == current_entreprise_id.get(),
        EntrepriseRole: lambda cls: cls.entreprise_id == current_entreprise_id.get(),
    }

    def _add_global_tenant_scope(orm_execute_state):
        eid = current_entreprise_id.get()
        if eid is None:
            return
        if current_is_system_admin.get():
            return
        if not orm_execute_state.is_select:
            return

        from sqlalchemy.orm import with_loader_criteria
        for model_cls, filter_fn in SCOPED_MODELS.items():
            try:
                orm_execute_state.statement = orm_execute_state.statement.options(
                    with_loader_criteria(model_cls, filter_fn, include_aliases=True)
                )
            except Exception:
                logger.debug("Could not apply tenant scope to %s", model_cls)

    from sqlalchemy.orm import Session as SASession
    event.listen(SASession, 'do_orm_execute', _add_global_tenant_scope, named=True)
