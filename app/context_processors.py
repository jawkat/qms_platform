from datetime import datetime, date
from flask import session
from app.models import Entreprise
from app.utils.domaine_switch import get_domaine_actif


def inject_globals():
    from flask import current_app
    from flask_login import current_user
    ctx = {}

    if current_user.is_authenticated and current_user.entreprise_id:
        entreprise = Entreprise.query.get(current_user.entreprise_id)
        if entreprise:
            modules = entreprise.modules_actifs or ['hse']
            domaine = get_domaine_actif(entreprise)
            ctx.update({
                'domaine_actif': domaine,
                'modules_actifs': modules,
                'has_switch': len(modules) > 1,
                'entreprise': entreprise,
            })

    ctx['now'] = datetime.utcnow()
    ctx['today'] = date.today()
    return ctx
