# QMS Platform Refactoring Plan — Unified Non-Conformité Module

## Executive Summary

Consolidate three separate Non-Conformité systems (HSE, Qualité, HACCP) into a single unified model and module, while adding GED to the activatable modules list.

---

## Current State Analysis

| System | Model | Table | Routes | Template |
|--------|-------|-------|--------|----------|
| HSE | None (derived from `EvaluationArticle`) | `evaluation_article` | `conformite/routes/evaluation.py:148-258` | `conformite/nonconformites.html` |
| Qualité | `NonConformiteQualite` | `non_conformite_qualite` | `qualite/routes.py:583-651` | `qualite/nonconformites.html` |
| HACCP | `NonConformiteHaccp` | `haccp_non_conformite` | `haccp/routes.py:550-609` | `haccp/nonconformites.html` |

---

## Phase 1: Unified NonConformite Model

### New File: `app/models/nonconformite.py`

```python
from app import db
from datetime import datetime, date
from enum import Enum


class DomaineNC(Enum):
    HSE = 'hse'
    QUALITE = 'qualite'
    HACCP = 'haccp'


class StatutNC(Enum):
    OUVERTE = 'ouverte'
    EN_COURS = 'en_cours'
    CLOTUREE = 'cloturee'


class NonConformite(db.Model):
    __tablename__ = 'nonconformite'

    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    domaine = db.Column(db.String(20), nullable=False, index=True)  # hse | qualite | haccp

    # Common fields
    reference = db.Column(db.String(50))
    date_nc = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.Text, nullable=False)
    action_corrective = db.Column(db.Text)
    responsable_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    statut = db.Column(db.String(20), default='ouverte')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    # Qualité-specific (also useful for HSE)
    produit_processus = db.Column(db.String(200))

    # HSE-specific: link back to the evaluation that generated this NC
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation_article.id'), nullable=True)

    # HACCP-specific fields (nullable, only used when domaine='haccp')
    source = db.Column(db.String(50))       # ccp, audit, reclamation, interne, prp
    cause = db.Column(db.Text)
    delai = db.Column(db.Date)
    cloture_le = db.Column(db.Date)
    efficacite_verifiee = db.Column(db.Boolean, default=False)

    # Relationships
    entreprise = db.relationship('Entreprise', backref=db.backref('nonconformites', lazy='dynamic'))
    responsable = db.relationship('Utilisateur', foreign_keys=[responsable_id])
    evaluation = db.relationship('EvaluationArticle', foreign_keys=[evaluation_id],
                                 backref=db.backref('nonconformites', lazy='dynamic'))
```

**Why this design:**
- Single table with `domaine` discriminator replaces 3 separate tables
- HACCP fields are nullable — only populated when `domaine='haccp'`
- `evaluation_id` links HSE NCs back to their source evaluation
- `produit_processus` serves both Qualité and general use cases
- Indexes on `entreprise_id` + `domaine` for fast filtered queries

### Update `app/models/__init__.py`

Add import:
```python
from .nonconformite import NonConformite, DomaineNC, StatutNC
```

Remove old imports:
```python
# Remove: NonConformiteQualite from qualite import
# HACCP NC is imported via `from .haccp import *` — no change needed there yet
```

---

## Phase 2: Unified Permissions

### Modify `app/utils/permission_catalog.py`

**Remove** from existing modules:
```python
# Remove these lines:
('qualite.gerer_nonconformites', 'Gerer les non-conformites qualite'),  # line 70
('haccp.gerer_nonconformites', 'Gerer les non-conformites'),             # line 80
```

**Add** new unified section:
```python
'nonconformites': [
    ('nonconformites.voir', 'Voir les non-conformites'),
    ('nonconformites.gerer', 'Gerer les non-conformites'),
],
```

**Update `DEFAULT_ENTERPRISE_ROLE_PERMISSIONS`:**
- Manager: replace `qualite.gerer_nonconformites` and `haccp.gerer_nonconformites` with `nonconformites.voir`, `nonconformites.gerer`
- Auditeur: add `nonconformites.voir`
- Responsable operationnel: add `nonconformites.voir`, `nonconformites.gerer`
- Consultant: add `nonconformites.voir`

---

## Phase 3: Unified Routes

### New File: `app/nonconformites/__init__.py`

```python
from flask import Blueprint
blueprint = Blueprint('nonconformites', __name__, template_folder='templates')
from . import routes
```

### New File: `app/nonconformites/routes.py`

Key endpoints:

| Route | Method | Purpose |
|-------|--------|---------|
| `/nonconformites` | GET | List page (adaptive template) |
| `/nonconformites/api` | GET | JSON list filtered by `?domaine=hse` etc. |
| `/nonconformites/api/create` | POST | Create NC (domaine auto-detected from session or param) |
| `/nonconformites/api/<id>/update` | POST | Update NC |
| `/nonconformites/api/<id>/delete` | POST | Delete NC |
| `/nonconformites/api/stats` | GET | Stats per domaine |

**Route logic:**
- Access guard: check `nonconformites.voir` permission
- `domaine` param on list/create filters by active module
- HSE NCs: allow viewing linked `evaluation_id` details
- HACCP fields: only validated/saved when `domaine='haccp'`
- Qualité fields: only validated when `domaine='qualite'`

**Example route structure:**
```python
from flask import render_template, request, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.models.nonconformite import NonConformite
from app.models.entreprise import Entreprise
from app.nonconformites import blueprint
from app.utils.auth import has_permission
from datetime import date, datetime


def _check_nc_access():
    if not current_user.has_permission('nonconformites.voir', current_user.entreprise_id):
        abort(403)


@blueprint.route('/')
@login_required
@has_permission('nonconformites.voir')
def index():
    return render_template('nonconformites/index.html')


@blueprint.route('/api')
@login_required
@has_permission('nonconformites.voir')
def api_list():
    _check_nc_access()
    eid = current_user.entreprise_id
    domaine = request.args.get('domaine')
    statut = request.args.get('statut')
    search = request.args.get('q', '').strip()

    q = NonConformite.query.filter_by(entreprise_id=eid)
    if domaine:
        q = q.filter_by(domaine=domaine)
    if statut:
        q = q.filter_by(statut=statut)
    if search:
        like = f'%{search}%'
        q = q.filter(db.or_(
            NonConformite.description.ilike(like),
            NonConformite.reference.ilike(like),
        ))
    items = q.order_by(NonConformite.date_creation.desc()).all()
    return jsonify([_serialize_nc(r) for r in items])


@blueprint.route('/api/create', methods=['POST'])
@login_required
@has_permission('nonconformites.gerer')
def api_create():
    data = request.get_json()
    domaine = data.get('domaine', 'qualite')
    # Validate domaine matches active module
    # Create record with appropriate fields
    ...


def _serialize_nc(nc):
    result = {
        'id': nc.id, 'domaine': nc.domaine,
        'reference': nc.reference,
        'date_nc': nc.date_nc.isoformat() if nc.date_nc else None,
        'description': nc.description,
        'action_corrective': nc.action_corrective,
        'responsable_id': nc.responsable_id,
        'responsable': f'{nc.responsable.prenom} {nc.responsable.nom}' if nc.responsable else '',
        'statut': nc.statut,
        'date_creation': nc.date_creation.isoformat() if nc.date_creation else None,
    }
    if nc.domaine == 'qualite':
        result['produit_processus'] = nc.produit_processus
    if nc.domaine == 'hse':
        result['evaluation_id'] = nc.evaluation_id
    if nc.domaine == 'haccp':
        result.update({
            'source': nc.source, 'cause': nc.cause,
            'delai': nc.delai.isoformat() if nc.delai else None,
            'cloture_le': nc.cloture_le.isoformat() if nc.cloture_le else None,
            'efficacite_verifiee': nc.efficacite_verifiee,
        })
    return result
```

### Register in `app/__init__.py`

Add:
```python
from .nonconformites import blueprint as nonconformites_bp
app.register_blueprint(nonconformites_bp, url_prefix='/nonconformites')
```

---

## Phase 4: Unified Template

### New File: `app/nonconformites/templates/nonconformites/index.html`

Adaptive template that:
1. Shows a **domaine tab bar** (HSE | Qualité | HACCP) — only showing tabs for active modules
2. Displays **statistics cards** (ouvertes, en cours, clôturées, total) — filtered by active tab
3. **Conditional form fields** in the modal:
   - Always visible: reference, date, description, action corrective, responsable, statut
   - Qualité tab: shows `produit_processus` field
   - HSE tab: shows linked evaluation info (read-only)
   - HACCP tab: shows source, cause, délai, clôturé le, efficacité vérifiée
4. Table columns adapt per tab
5. Uses same JS fetch pattern as existing templates

**Template structure:**
```html
{% extends 'layout.html' %}
{% block title %}Non-conformités{% endblock %}
{% block content %}
<div class="container-fluid">
  <!-- Domaine tabs -->
  <ul class="nav nav-tabs mb-3" id="ncTabs">
    {% if 'hse' in modules_actifs %}
    <li class="nav-item">
      <a class="nav-link active" data-domaine="hse" href="#">HSE</a>
    </li>
    {% endif %}
    {% if 'qualite' in modules_actifs %}
    <li class="nav-item">
      <a class="nav-link" data-domaine="qualite" href="#">Qualité</a>
    </li>
    {% endif %}
    {% if 'haccp' in modules_actifs %}
    <li class="nav-item">
      <a class="nav-link" data-domaine="haccp" href="#">HACCP</a>
    </li>
    {% endif %}
  </ul>

  <!-- Stats cards -->
  <!-- Table with adaptive columns -->
  <!-- Modal with conditional fields per domaine -->
</div>
{% endblock %}
{% block scripts %}
<script>
let currentDomaine = 'hse';
// Tab switching, fetch with ?domaine= param
// Modal show/hide fields based on domaine
</script>
{% endblock %}
```

---

## Phase 5: Database Migration

### New Migration: `migrations/versions/xxxx_unify_nonconformite.py`

**Step 1: Create new table**
```python
def upgrade():
    op.create_table('nonconformite',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('entreprise_id', sa.Integer, sa.ForeignKey('entreprise.id'), nullable=False, index=True),
        sa.Column('domaine', sa.String(20), nullable=False, index=True),
        sa.Column('reference', sa.String(50)),
        sa.Column('date_nc', sa.Date, nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('action_corrective', sa.Text),
        sa.Column('responsable_id', sa.Integer, sa.ForeignKey('utilisateur.id')),
        sa.Column('statut', sa.String(20), default='ouverte'),
        sa.Column('date_creation', sa.DateTime),
        sa.Column('produit_processus', sa.String(200)),
        sa.Column('evaluation_id', sa.Integer, sa.ForeignKey('evaluation_article.id'), nullable=True),
        sa.Column('source', sa.String(50)),
        sa.Column('cause', sa.Text),
        sa.Column('delai', sa.Date),
        sa.Column('cloture_le', sa.Date),
        sa.Column('efficacite_verifiee', sa.Boolean, default=False),
    )
    op.create_index('ix_nc_entreprise_domaine', 'nonconformite', ['entreprise_id', 'domaine'])
```

**Step 2: Migrate data from `non_conformite_qualite`**
```python
def migrate_qualite_nc():
    """Copy Qualité NCs into unified table."""
    op.execute("""
        INSERT INTO nonconformite (entreprise_id, domaine, reference, date_nc, description,
            action_corrective, responsable_id, statut, date_creation, produit_processus)
        SELECT entreprise_id, 'qualite', reference, date_nc, description,
            action_corrective, responsable_id, statut, date_creation, produit_processus
        FROM non_conformite_qualite
    """)
```

**Step 3: Migrate data from `haccp_non_conformite`**
```python
def migrate_haccp_nc():
    """Copy HACCP NCs into unified table."""
    op.execute("""
        INSERT INTO nonconformite (entreprise_id, domaine, reference, date_nc, description,
            action_corrective, responsable_id, statut, date_creation,
            source, cause, delai, cloture_le, efficacite_verifiee)
        SELECT entreprise_id, 'haccp', reference, date_nc, description,
            action_corrective, responsable_id, statut, date_creation,
            source, cause, delai, cloture_le, efficacite_verifiee
        FROM haccp_non_conformite
    """)
```

**Step 4: Migrate HSE NCs from EvaluationArticle**
```python
def migrate_hse_nc():
    """Create NC records from NON_CONFORME evaluations."""
    op.execute("""
        INSERT INTO nonconformite (entreprise_id, domaine, date_nc, description,
            responsable_id, statut, date_creation, evaluation_id)
        SELECT et.entreprise_id, 'hse',
            COALESCE(ea.date_evaluation::date, CURRENT_DATE),
            COALESCE(ea.observation, 'NC dérivée de l''évaluation article ' || a.numero_article),
            ea.evalue_par, 'ouverte', ea.date_evaluation, ea.id
        FROM evaluation_article ea
        JOIN entreprise_texte et ON ea.entreprise_texte_id = et.id
        JOIN article a ON ea.article_id = a.id
        WHERE ea.conforme = 'NON_CONFORME'
    """)
```

**Step 5: Drop old tables (separate migration for safety)**
```python
def drop_old_tables():
    op.drop_table('non_conformite_qualite')
    op.drop_table('haccp_non_conformite')
```

---

## Phase 6: Route Deprecation & Redirects

### Modify existing route files to redirect to unified module:

**`app/conformite/routes/evaluation.py`** — Replace NC routes (lines 148-258):
```python
@blueprint.route('/nonconformites')
@login_required
@has_permission('conformite.voir')
def nonconformites():
    return redirect(url_for('nonconformites.index', domaine='hse'))
```

**`app/qualite/routes.py`** — Replace NC routes (lines 583-651):
```python
@blueprint.route('/nonconformites')
@login_required
def nonconformites():
    return redirect(url_for('nonconformites.index', domaine='qualite'))

# Remove all api_nonconformites* routes
```

**`app/haccp/routes.py`** — Replace NC routes (lines 550-619):
```python
@blueprint.route('/nonconformites')
@login_required
def nonconformites():
    return redirect(url_for('nonconformites.index', domaine='haccp'))

# Remove all api_nonconformites* routes
```

---

## Phase 7: Sidebar Navigation Update

### Modify `app/templates/layout.html`

**Remove** individual NC links from each module section:
- Line 244-248: Remove `conformite.nonconformites` link from HSE section
- Line 308-310: Remove `haccp.nonconformites` link from HACCP section  
- Line 372-374: Remove `qualite.nonconformites` link from Qualité section

**Add** unified NC link in the **common section** (after line 213, before module sections):
```html
<li class="nav-item mb-1">
  <a class="nav-link {% if request.endpoint and request.endpoint.startswith('nonconformites.') %}active{% endif %}"
     href="{{ url_for('nonconformites.index') }}">
    <i class="fas fa-exclamation-triangle me-2"></i><span>Non-conformités</span>
  </a>
</li>
```

**Alternatively**, add NC link to each module section that links to the unified module with the right `domaine` param:
- HSE section: `href="{{ url_for('nonconformites.index', domaine='hse') }}"`
- HACCP section: `href="{{ url_for('nonconformites.index', domaine='haccp') }}"`
- Qualité section: `href="{{ url_for('nonconformites.index', domaine='qualite') }}"`

---

## Phase 8: Add GED to Activatable Modules

### Modify `app/models/entreprise.py` (line 12)
```python
# Change default:
modules_actifs = db.Column(db.JSON, default=lambda: ['hse'])
# No change needed — 'ged' is added per-entreprise via admin panel
```

### Verify GED module access guard exists

The GED module (documents) is already registered as `documents_bp`. Check if it has an access guard similar to `_check_haccp_access()`. If not, add one:

**`app/documents/routes.py`** — Add access check:
```python
def _check_ged_access():
    entreprise = db.session.get(Entreprise, current_user.entreprise_id)
    if not entreprise or 'ged' not in (entreprise.modules_actifs or []):
        abort(403)
```

### Add GED section to sidebar (if not present)

Check `layout.html` for existing documents/GED section. The sidebar already has a common "Documents" link — verify it works when 'ged' is in modules_actifs.

### Update admin module management

The admin panel for managing entreprise modules should include 'ged' as an option. Check `app/admin/` routes and templates.

---

## Phase 9: Cleanup Old Models (Post-Migration)

After verifying data migration is correct:

1. **`app/models/qualite.py`**: Remove `NonConformiteQualite` class (lines 99-111)
2. **`app/haccp/models.py`**: Remove `NonConformiteHaccp` class (lines 159-176)
3. **`app/models/__init__.py`**: Remove `NonConformiteQualite` from qualite import
4. **Update HACCP imports** in `app/haccp/routes.py` line 8: Remove `NonConformiteHaccp` from import
5. **Update Qualité imports** in `app/qualite/routes.py` line 5: Remove `NonConformiteQualite` from import

---

## Phase 10: Verification Checklist

### Functional Tests
- [ ] Create NC for each domaine (HSE, Qualité, HACCP)
- [ ] Verify HSE NCs link back to evaluation_article
- [ ] Verify HACCP-specific fields are saved/displayed correctly
- [ ] Verify Qualité produit_processus field works
- [ ] Tab switching filters data correctly
- [ ] Statistics cards update per tab
- [ ] Search works across all domaines
- [ ] Permissions enforce correctly (voir vs gerer)

### Data Integrity
- [ ] All existing Qualité NCs migrated correctly
- [ ] All existing HACCP NCs migrated correctly
- [ ] All HSE NON_CONFORME evaluations converted to NCs
- [ ] Old tables dropped without data loss

### Module Activation
- [ ] GED module appears in admin panel
- [ ] When 'ged' is in modules_actifs, documents section is accessible
- [ ] When 'ged' is not in modules_actifs, documents section is hidden/403

### Route Redirects
- [ ] Old URLs redirect to unified module
- [ ] No broken links in sidebar

---

## File Change Summary

| Action | File | Purpose |
|--------|------|---------|
| **CREATE** | `app/models/nonconformite.py` | Unified NC model |
| **CREATE** | `app/nonconformites/__init__.py` | New blueprint |
| **CREATE** | `app/nonconformites/routes.py` | Unified CRUD routes |
| **CREATE** | `app/nonconformites/templates/nonconformites/index.html` | Adaptive template |
| **CREATE** | `migrations/versions/xxxx_unify_nonconformite.py` | Migration |
| **MODIFY** | `app/models/__init__.py` | Add NonConformite import |
| **MODIFY** | `app/__init__.py` | Register nonconformites blueprint |
| **MODIFY** | `app/utils/permission_catalog.py` | Add nonconformites.voir/gerer |
| **MODIFY** | `app/templates/layout.html` | Update sidebar NC links |
| **MODIFY** | `app/conformite/routes/evaluation.py` | Redirect old NC route |
| **MODIFY** | `app/qualite/routes.py` | Redirect old NC routes, remove API |
| **MODIFY** | `app/haccp/routes.py` | Redirect old NC routes, remove API |
| **MODIFY** | `app/models/qualite.py` | Remove NonConformiteQualite |
| **MODIFY** | `app/haccp/models.py` | Remove NonConformiteHaccp |
| **MODIFY** | `app/models/entreprise.py` | Verify modules_actifs supports 'ged' |

---

## Execution Order

1. Create unified model (`app/models/nonconformite.py`)
2. Update model imports (`app/models/__init__.py`)
3. Create blueprint (`app/nonconformites/__init__.py`)
4. Create routes (`app/nonconformites/routes.py`)
5. Create template (`app/nonconformites/templates/nonconformites/index.html`)
6. Register blueprint (`app/__init__.py`)
7. Update permissions (`app/utils/permission_catalog.py`)
8. Update sidebar (`app/templates/layout.html`)
9. Generate and run migration
10. Verify data migration
11. Add redirects to old routes
12. Remove old NC models and routes
13. Verify GED module activation
14. Run full test suite
