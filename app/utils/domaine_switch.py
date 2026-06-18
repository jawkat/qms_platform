from flask import session

DOMAINES = {'hse', 'qualite'}


def get_domaine_actif(entreprise):
    modules = entreprise.modules_actifs or ['hse']
    if len(modules) == 1:
        return modules[0]
    domaine = session.get('domaine_actif')
    if domaine in modules:
        return domaine
    return modules[0]


def set_domaine_actif(domaine):
    if domaine in DOMAINES:
        session['domaine_actif'] = domaine
