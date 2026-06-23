# Architecture Refactoring Plan — CRUD Générique, Décorateur Unifié & Services

## Executive Summary

Standardiser les ~20 blueprints de l'application sur un socle commun : `BaseResource` (CRUD générique), `@access_required` (décorateur unifié permission + module), et `BaseService` renforcé. Objectif : éliminer les répétitions, réduire les bugs, et uniformiser les patterns.

---

## Problèmes Identifiés

| Problème | Exemple | Impact |
|----------|---------|--------|
| 4+ lignes de décorateurs par route | `@login_required` + `@has_permission()` + `@module_access_required()` | Duplication dans 20+ modules |
| CRUD identique écrit N fois | `first_or_404()`, `setattr` loop, `db.session.delete/commit` | 50+ lignes de boilerplate par module |
| `entreprise_id` oublié par endroits | Certains `api_create()` ne l'assignent pas | Fuite multi-tenant |
| Décorateurs mélangés | `has_permission` vs `module_access_required` | Incohérence, lecture difficile |
| Pas de séparation claire | API/HTML mélangés dans le même fichier | Difficile à tester et maintenir |

---

## Phase 1: BaseResource CRUD Générique

### `app/utils/base_resource.py`

```python
class BaseResource:
    """Generic CRUD for any SQLAlchemy model with tenant scoping & field protection."""

    model = None           # SQLAlchemy model class (required)
    schema = None          # smorest Schema for serialization (required)
    create_schema = None   # defaults to schema
    update_schema = None   # defaults to schema (partial)
    permission_voir = None # 'module.voir'
    permission_gerer = None # 'module.gerer'
    module_name = None     # optional: 'haccp' for module_access_required
    protected_fields = {'id', 'entreprise_id', 'date_creation'}
    sort_field = 'date_creation'
    sort_dir = 'desc'
    search_fields = []     # list of column names for ILIKE search
    filter_fields = {}     # {query_param: column_name} for exact filters
    tenant_field = 'entreprise_id'  # column to scope per tenant

    @classmethod
    def list(cls):
        ...

    @classmethod
    def create(cls, data):
        ...

    @classmethod
    def update(cls, data, item_id):
        ...

    @classmethod
    def delete(cls, item_id):
        ...
```

---

## Phase 2: Décorateur `@access_required` Unifié

### `app/utils/permissions.py` — Ajouter

```python
def access_required(permission=None, module=None):
    """
    Décorateur unique qui vérifie :
    1. Authentification
    2. Activation du module (si module_name fourni)
    3. Permission (si fournie)
    """
```

Remplace les 3 décorateurs : `@login_required`, `@has_permission()`, `@module_access_required()`

---

## Phase 3: Port des Modules (par ordre)

| Ordre | Module | Routes | Priorité |
|-------|--------|--------|----------|
| 1 | Formations | 16 endpoints (4 entities) | Démo claire |
| 2 | NonConformites | 4 endpoints | Déjà uniforme |
| 3 | HACCP | ~30 endpoints (9 entities) | Volume significatif |
| 4 | HSE | ~20 endpoints | Représentatif |
| 5 | Environnement | ~10 endpoints | Pattern récent |
| 6-15 | Reste (maintenance, laboratoire, planification, etc.) | ~100 endpoints | Automatisé |

---

## Phase 4: Services Métier (Extension BaseService)

Créer des services spécifiques pour les opérations non-CRUD (stats, calendrier, certifications, workflow).

---

## Phase 5: Séparation API/HTML

- Routes HTML → `blueprint.route('/')` restent dans `routes.py`
- Routes API → déplacées vers `api.py` optionnellement
- Objectif : évolutif, pas obligatoire immédiatement

---

## Execution Order

```
Phase 1a: BaseResource     → app/utils/base_resource.py
Phase 1b: @access_required → app/utils/permissions.py (+)
Phase 2:  Port formations  → app/formations/routes.py (refactor)
Phase 3:  Port nonconformites → app/nonconformites/routes.py (refactor)
Phase 4:  Port haccp       → app/haccp/routes.py (refactor)
Phase 5:  Update tests     → tests/test_formations.py (+ gardes)
Phase 6:  Port remaining modules
```
