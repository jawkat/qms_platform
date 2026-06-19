# QMS Platform — Architectural Reference

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Directory Structure](#2-directory-structure)
3. [Application Factory & Bootstrap](#3-application-factory--bootstrap)
4. [Blueprint Registration Convention](#4-blueprint-registration-convention)
5. [Model Architecture](#5-model-architecture)
6. [Route Patterns](#6-route-patterns)
7. [Template Architecture](#7-template-architecture)
8. [Permission & RBAC System](#8-permission--rbac-system)
9. [Multi-Tenant Isolation](#9-multi-tenant-isolation)
10. [Domain Switching (HSE / Qualité)](#10-domain-switching-hse--qualité)
11. [Proof / Attachment System](#11-proof--attachment-system)
12. [Service Layer](#12-service-layer)
13. [Utility Layer](#13-utility-layer)
14. [Action System](#14-action-system)
15. [Notification System](#15-notification-system)
16. [Subscription & Quota System](#16-subscription--quota-system)
17. [Frontend Conventions](#17-frontend-conventions)
18. [Common Patterns & Gotchas](#18-common-patterns--gotchas)

---

## 1. Project Overview

Multi-tenant SaaS platform for QMS (Quality Management System) / HSE / Qualité compliance management.

**Tech Stack:**
- Python 3.10, Flask 2.3.3, SQLAlchemy 2.0.23, PostgreSQL 16
- Jinja2 templates, Bootstrap 5.3.2, FontAwesome 6.5.1
- Flask-Migrate (Alembic), Flask-Login, Flask-Mail, Flask-WTF (CSRF)
- MinIO for file storage
- Docker Compose for local dev (port 5005)

**Key Features:**
- Multi-tenant with per-entreprise user isolation
- Domain switching (HSE / Qualité) — session-based
- Full RBAC with granular permissions
- GED (Gestion Électronique de Documents) via ProofMaster/ProofReference
- Regulatory text monitoring (Veille)
- HACCP module
- Non-Conformité unified model across HSE/Qualité/HACCP
- Audit, Ishikawa, Indicateurs, Tickets, etc.

---

## 2. Directory Structure

```
qms_platform/
├── app/
│   ├── __init__.py              # App factory: db, migrate, login, csrf, mail, blueprints
│   ├── context_processors.py    # inject_globals: domaine_actif, modules_actifs, has_switch
│   ├── actions/                 # Blueprint: actions correctives
│   ├── admin/                   # Blueprint: admin panel
│   ├── audit/                   # Blueprint: audits
│   ├── conformite/              # Blueprint: conformité (réglementaire / textes)
│   ├── demo/                    # Blueprint: demo booking
│   ├── documents/               # Blueprint: GED (dossiers, documents)
│   ├── entreprise_textes/       # Blueprint: enterprise-specific texts
│   ├── entreprises/             # Blueprint: enterprise settings
│   ├── facturation/             # Blueprint: billing
│   ├── haccp/                   # Blueprint: HACCP module
│   ├── hse/                     # Blueprint: HSE module
│   ├── indicateurs/             # Blueprint: indicators
│   ├── ishikawa/                # Blueprint: Ishikawa analysis
│   ├── main/                    # Blueprint: landing pages, public routes
│   ├── models/                  # All SQLAlchemy models (22 files)
│   ├── nonconformites/          # Blueprint: unified NC management
│   ├── plans/                   # Blueprint: subscription plans
│   ├── qualite/                 # Blueprint: Qualité module
│   ├── secteur/                 # Blueprint: sectors
│   ├── services/                # Business logic layer (11 files)
│   ├── static/                  # Static assets (CSS, JS, images)
│   ├── support/                 # Blueprint: support/tickets
│   ├── templates/               # Base layout + shared templates
│   ├── textes/                  # Blueprint: regulatory texts
│   ├── users/                   # Blueprint: user management
│   ├── utils/                   # Utilities (10 files)
│   └── veille/                  # Blueprint: regulatory watch
├── migrations/                  # Alembic migrations
├── config.py                    # Flask configuration
├── docker-compose.yml           # PostgreSQL + app containers
├── REFACTORING_PLAN.md          # Known refactoring items
├── SKILL_REFERENCE.md           # This file
├── application.md               # Older architecture overview
├── requirements.txt             # Python dependencies
└── run.py                       # Entry point
```

---

## 3. Application Factory & Bootstrap

**File:** `app/__init__.py:19-98`

```python
def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    # ...
    init_tenant_scope(app)
    # Register blueprints (see section 4)
    # before_request: set_tenant()
    # context_processor: inject_globals
```

**Key points:**
- Extensions are module-level singletons (`db`, `migrate`, `login_manager`, `csrf`, `mail`)
- `csrf.init_app(app)` is called but `WTF_CSRF_ENABLED = False` in config — CSRF is **disabled**
- `login_manager.login_view = 'users.login'`
- All blueprints registered explicitly in `create_app()`
- `before_request` sets tenant context from `current_user.entreprise_id`

---

## 4. Blueprint Registration Convention

Two patterns for blueprint registration:

### With `url_prefix` (most modules)
```python
app.register_blueprint(actions_bp, url_prefix='/actions')
app.register_blueprint(qualite_bp, url_prefix='/qualite')
```

### Without `url_prefix` (routes define their own prefix)
```python
app.register_blueprint(conformite_bp)     # routes start with /
app.register_blueprint(entreprise_textes_bp)
app.register_blueprint(demo_bp)
```

Blueprint variable names follow convention: `{module}_bp` or `{module}s` (e.g., `users as users_bp`, `main as main_bp`).

**Blueprint registration order** (30 total):
| Blueprint | Prefix | Module |
|-----------|--------|--------|
| `main_bp` | `/` | Landing pages |
| `entreprises_bp` | `/entreprises` | Enterprise management |
| `users_bp` | `/users` | User management |
| `actions_bp` | `/actions` | Corrective actions |
| `documents_bp` | `/documents` | GED |
| `conformite_bp` | **none** | Conformité (routes start with /) |
| `qualite_bp` | `/qualite` | Qualité module |
| `admin_bp` | `/admin` | Admin panel |
| `support_bp` | `/support` | Support/tickets |
| `textes_bp` | `/textes` | Regulatory texts |
| `audit_bp` | `/audit` | Audits |
| `indicateurs_bp` | `/indicateurs` | Indicators |
| `secteur_bp` | `/secteur` | Sectors |
| `entreprise_textes_bp` | **none** | Enterprise texts |
| `demo_bp` | **none** | Demo booking |
| `veille_bp` | `/veille` | Regulatory watch |
| `haccp_bp` | `/haccp` | HACCP |
| `nonconformites_bp` | `/nonconformites` | Unified NC |
| `hse_bp` | `/hse` | HSE module |
| `ishikawa_bp` | `/ishikawa` | Ishikawa analysis |
| `facturation_bp` | `/facturation` | Billing |
| `plans_bp` | `/plans` | Subscription plans |

---

## 5. Model Architecture

**Location:** `app/models/` — 22 files, ~1147 total lines.

### Model files and their main entities:

| File | Models | Key Points |
|------|--------|------------|
| `auth.py` | `Permission`, `RolePermission`, `Role`, `EntrepriseRole`, `Utilisateur` | User model: `has_permission()`, `entreprise_id` FK |
| `entreprise.py` | `Entreprise`, `HistoriquePaiement`, `SubscriptionPlan`, `Secteur`, `EntrepriseSecteur` | `modules_actifs` JSON, `abonnement_type` FK to plan |
| `actions.py` | `ActionCorrective`, `ActionStatusEnum` | `source_type`/`source_id` polymorphic, `domaine`, `est_recurrente` |
| `proofs.py` | `ProofMaster`, `ProofReference` | Central GED + attachment links |
| `ged.py` | `Dossier`, `TypeDocument`, `WorkflowLog`, `HistoriqueDocument` | Folder structure, document types, workflow audit |
| `conformite.py` | `EvaluationArticle`, `ExigenceType`, `NiveauRisqueType`, `ApplicabiliteEnum`, `ConformiteEnum`, `EntrepriseTexte`, `HistoriqueEvaluation` | Evaluation + enum types |
| `textes.py` | `Domaine`, `TexteReglementaire`, `TexteVersion`, `Article` | Regulatory texts with versioning |
| `audit.py` | `Audit`, `AuditObservation`, `ChecklistModele`, `ChecklistItem`, `AuditChecklistReponse` | Audit + checklist system |
| `indicateurs.py` | `Indicateur`, `IndicateurValeur` | KPI tracking |
| `ticket.py` | `Ticket`, `MessageTicket` | Support tickets |
| `systeme.py` | `Notification`, `JournalSecurite`, `TacheSysteme` | System-level models |
| `demo.py` | `Disponibilite`, `CreneauDemo` | Demo booking |
| `qualite.py` | `Risque`, `ReclamationClient`, `Fournisseur`, `Formation`, `Equipement`, `ControleQualite`, `RevueDirection` | Qualité module entities |
| `nonconformite.py` | `NonConformite` | Unified NC model with `domaine` polymorphic |
| `hse.py` | `Incident`, `EPI`, `Inspection`, `InspectionItem`, `PermisTravail` | HSE module entities |
| `ishikawa.py` | `AnalyseIshikawa`, `CauseIshikawa` | Root cause analysis |
| `competence.py` | `Competence`, `FormationParticipant` | Competency tracking |
| `historique_fournisseur.py` | `EvaluationFournisseur`, `HistoriqueFournisseur` | Supplier evaluation |
| `echeancier.py` | `ObligationReglementaire` | Regulatory obligation calendar |
| `veille.py` | `SourceReglementaire`, `Veille` | Regulatory watch |
| `haccp.py` | Re-exports everything from `app.haccp.models` | HACCP models |
| `__init__.py` | Imports & re-exports all models | Import target for `from app.models import ...` |

### Common model patterns:

**Tenant isolation columns:**
```python
entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
```

**Domain column:**
```python
domaine = db.Column(db.String(20), default='hse', nullable=False)
```

**Timestamp columns:**
```python
date_creation = db.Column(db.DateTime, default=datetime.utcnow)
date_modification = db.Column(db.DateTime, onupdate=datetime.utcnow)
```

**JSON metadata:**
```python
metadata = db.Column(db.JSON, default=dict)
```

**Polymorphic references (used in ActionCorrective, ProofReference):**
```python
source_type = db.Column(db.String(50), nullable=False)  # e.g., 'evaluation', 'audit'
source_id = db.Column(db.Integer, nullable=False)
```

### Enum patterns:
```python
class ConformiteEnum(str, enum.Enum):
    CONFORME = 'conforme'
    NON_CONFORME = 'non_conforme'
    SANS_OBJET = 'sans_objet'
    NON_EVALUE = 'non_evalue'

# Usage: column defaults and validation
conforme = db.Column(db.Enum(ConformiteEnum), default=ConformiteEnum.NON_EVALUE)
```

**IMPORTANT GOTCHA:** Setting an enum column to an empty string `''` will crash because SQLAlchemy cannot look up `''` as an enum member. Always use truthy checks (`if value:` not `if value is not None:`) when assigning from form data.

---

## 6. Route Patterns

### Two Access Control Patterns

**Pattern A — `@has_permission()` decorator (preferred for conformité, plans):**
```python
from app.utils.permissions import has_permission

@blueprint.route('/<int:evaluation_id>', methods=['GET', 'POST'])
@login_required
@has_permission('conformite.voir')
def evaluation_detail(evaluation_id):
    # ...
```

**Pattern B — Manual check function (used in haccp, qualite, hse):**
```python
def _check_haccp_access():
    entreprise = db.session.get(Entreprise, current_user.entreprise_id)
    if not entreprise or 'haccp' not in (entreprise.modules_actifs or []):
        abort(403)
    if not current_user.has_permission('haccp.voir', current_user.entreprise_id):
        abort(403)

@blueprint.route('/')
@login_required
def tableau_de_bord():
    _check_haccp_access()
    return render_template('haccp/tableau_de_bord.html')
```

### API Response Patterns

**Form POST → redirect:**
```python
if request.method == 'POST':
    # ... process form ...
    db.session.commit()
    flash('Message de succès.', 'success')
    return redirect(url_for('conformite.evaluation_detail', evaluation_id=eval_id))
```

**AJAX endpoint → JSON:**
```python
@blueprint.route('/api/proofs/<int:evaluation_id>')
@login_required
@has_permission('conformite.voir')
def list_proofs(evaluation_id):
    refs = ProofReference.query.filter_by(entity_type='evaluation', entity_id=evaluation_id).all()
    return jsonify([...])
```

**AJAX POST → JSON:**
```python
@blueprint.route('/api/evaluation/<int:evaluation_id>/save', methods=['POST'])
@login_required
def auto_save(evaluation_id):
    data = request.get_json()
    # ...
    db.session.commit()
    return jsonify({'success': True})
```

**IMPORTANT:** For AJAX POST endpoints, the server must return `jsonify(...)` for AJAX requests. If the server returns a redirect, the client will get HTML and show "Erreur réseau". Always check for `X-Requested-With` header or use `request.get_json()` and return JSON.

---

## 7. Template Architecture

**Base layout:** `app/templates/layout.html`

**Inheritance:**
```html
{% extends "layout.html" %}
{% block page_title %}Titre de la page{% endblock %}
{% block content %}
  ...
{% endblock %}
{% block scripts %}
  <script>// page-specific JS</script>
{% endblock %}
```

### What layout.html provides:

- **Sidebar** (collapsible on mobile) with module navigation links
- **Top navbar** with notification bell + title
- **Flash messages** (Bootstrap alerts, auto-dismiss)
- **Domain switch dropdown** (HSE / Qualité) — only shown when `has_switch` is True
- **Bootstrap 5.3.2** + **FontAwesome 6.5.1** from CDN
- `togglePassword()`, `updatePasswordStrength()` JS helpers
- Notification polling JS (checks `/api/notifications/unread-count` every 30s)

### Template organization:
Templates are stored in each module's `templates/` subdirectory:
- `app/conformite/templates/conformite/*.html`
- `app/haccp/templates/haccp/*.html`
- etc.

### Context variables available in all templates (from `app/context_processors.py`):
```python
{
    'domaine_actif': session.get('domaine_actif', 'hse'),
    'modules_actifs': current_user.entreprise.modules_actifs if current_user.is_authenticated else [],
    'has_switch': current_user.entreprise and len(current_user.entreprise.modules_actifs or []) > 1,
    'is_landing': request.endpoint and request.endpoint.startswith('main.'),
    'current_route': request.endpoint or '',
}
```

---

## 8. Permission & RBAC System

### Permission Model (`app/models/auth.py`)

- **`Permission`**: `code` (unique, e.g., `'conformite.voir'`), `label`, `module`, `description`
- **`Role`**: `nom`, `est_systeme` (bool), `est_defaut` (bool)
- **`RolePermission`**: `role_id`, `permission_id` — many-to-many
- **`EntrepriseRole`**: `entreprise_id`, `role_id`, `utilisateur_id` — user's role within an enterprise
- **`Utilisateur`**: `role` (relationship to `Role`), `has_permission(permission_code, entreprise_id)` method

### Permission Catalog (`app/utils/permission_catalog.py`)

Central definition of all permissions and default role-permission mappings:
```python
PERMISSION_CATALOG = {
    'conformite.voir': {'label': 'Voir Conformité', 'module': 'conformite'},
    'conformite.modifier': {'label': 'Modifier Conformité', 'module': 'conformite'},
    # ...
}

DEFAULT_ENTERPRISE_ROLE_PERMISSIONS = {
    'administrateur': ['*'],  # wildcard = all permissions
    'gestionnaire': ['conformite.voir', 'conformite.modifier', ...],
    'lecteur': ['conformite.voir', ...],
}
```

### Permission Decorator (`app/utils/permissions.py`)

```python
def has_permission(*permission_codes):
    """Decorator that checks current_user.has_permission() for any of the given codes."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            for code in permission_codes:
                if current_user.has_permission(code, current_user.entreprise_id):
                    return f(*args, **kwargs)
            abort(403)
        return decorated
    return decorator
```

---

## 9. Multi-Tenant Isolation

**File:** `app/utils/tenant_scope.py`

Uses Python `contextvars.ContextVar` for request-scoped tenant:

```python
_current_entreprise_id: ContextVar[int] = ContextVar('current_entreprise_id', default=0)

def set_current_entreprise(entreprise_id, is_admin=False):
    _current_entreprise_id.set(entreprise_id)

def get_current_entreprise_id():
    return _current_entreprise_id.get()

def tenant_get_or_404(model, ident):
    """Fetch a model instance scoped to current tenant."""
    obj = db.session.get(model, ident)
    if not obj or not hasattr(obj, 'entreprise_id') or obj.entreprise_id != get_current_entreprise_id():
        abort(404)
    return obj
```

**Usage in `app/__init__.py:87-93`:**
```python
@app.before_request
def set_tenant():
    if current_user.is_authenticated and current_user.entreprise_id:
        is_admin = current_user.role and current_user.role.est_systeme
        set_current_entreprise(current_user.entreprise_id, is_admin)
```

**Important:** Tenant filtering in queries is NOT automatic — you must manually filter by `entreprise_id`:
```python
items = MyModel.query.filter_by(entreprise_id=get_current_entreprise_id()).all()
```

---

## 10. Domain Switching (HSE / Qualité)

**File:** `app/utils/domaine_switch.py` + `app/context_processors.py`

Stored in `session`:
```python
session['domaine_actif'] = domaine  # 'hse' or 'qualite'
```

Context processor injects:
- `domaine_actif` — current domain
- `modules_actifs` — list of enabled domains for this enterprise
- `has_switch` — True if more than 1 domain enabled

Many templates conditionally show content based on `domaine_actif`:
```html
{% if domaine_actif == 'hse' %}
  <li><a href="/hse/incidents">Incidents</a></li>
{% endif %}
```

Models use `domaine` column for domain-specific records:
```python
domaine = db.Column(db.String(20), default='hse', nullable=False)
```

---

## 11. Proof / Attachment System

**Central GED system with polymorphic attachments.**

### Models (`app/models/proofs.py`):

**`ProofMaster`** — the canonical document record (GED):
```python
class ProofMaster(db.Model):
    __tablename__ = 'proof_master'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    domaine = db.Column(db.String(20), default='hse')
    nom_fichier = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(20))
    taille_bytes = db.Column(db.Integer)
    chemin = db.Column(db.String(500), nullable=False)
    hash_fichier = db.Column(db.String(64), index=True)
    statut = db.Column(db.String(20), default='ACTIF')
    description = db.Column(db.Text)
    categorie = db.Column(db.String(100))
    date_validite = db.Column(db.Date)
    # ...
```

**`ProofReference`** — polymorphic link between any entity and a ProofMaster:
```python
class ProofReference(db.Model):
    __tablename__ = 'proof_reference'
    id = db.Column(db.Integer, primary_key=True)
    proof_master_id = db.Column(db.Integer, db.ForeignKey('proof_master.id'), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)   # e.g., 'evaluation', 'audit', 'action'
    entity_id = db.Column(db.Integer, nullable=False)
    # ...
    proof = db.relationship('ProofMaster')
```

### Service (`app/services/proof_service.py`):

`ProofService` provides:
- `compute_file_hash(file_path)` — SHA-256
- `create_or_reuse_proof(...)` — dedup by hash, copies file to MinIO or local storage
- `attach_proof(proof_master_id, entity_type, entity_id)` — creates ProofReference
- `detach_proof(reference_id)` — removes ProofReference (preserves ProofMaster)
- `get_proofs_for_entity(entity_type, entity_id)` — query helper

**Legacy code in `conformite_service.py`** still references a deleted `Document` model and has `ALLOWED_UPLOAD_ROOTS`. This code path will crash at runtime if called.

---

## 12. Service Layer

**Location:** `app/services/` — 11 files.

| Service File | Purpose |
|-------------|---------|
| `proof_service.py` | File hash dedup, upload, attach/detach proofs |
| `action_service.py` | Recurring action generation (hebdomadaire/mensuel/trimestriel/annuel) |
| `notification_service.py` | Notification send/validate/mark-read |
| `conformite_service.py` | **Legacy** — references deleted `Document` model, cleanup needed |
| `backup_service.py` | DB + file backups |
| `export_service.py` | Data export (CSV, etc.) |
| `import_service.py` | Data import |
| `minio_service.py` | MinIO/S3 file storage abstraction |
| `quota_middleware.py` | Quota enforcement checks |
| `subscription_service.py` | Subscription lifecycle management |
| `proof_expiration_service.py` | **Legacy** — references deleted `Document` model |

**Pattern:** Services are either classes with `@staticmethod` methods (e.g., `ProofService`, `ActionService`) or module-level functions (e.g., `notification_service.py`).

---

## 13. Utility Layer

**Location:** `app/utils/` — 10 files.

| File | Purpose |
|------|---------|
| `tenant_scope.py` | ContextVar-based tenant isolation |
| `permissions.py` | `@has_permission()` decorator |
| `permission_catalog.py` | `PERMISSION_CATALOG` dict + `DEFAULT_ENTERPRISE_ROLE_PERMISSIONS` |
| `domaine_switch.py` | Domain switching helpers |
| `subscriptions.py` | Subscription plan defaults + quota lookup |
| `notifications.py` | `create_notification()`, `send_action_reminder_email()` |
| `observability.py` | Structured logging with request_id, business event logging, `JournalSecurite` recording |
| `text_renderer.py` | `render_article_content()` — plain text → styled HTML for article display |
| `__init__.py` | Package init (empty) |

---

## 14. Action System

**Model:** `app/models/actions.py` — `ActionCorrective`

**Key fields:**
- `source_type` / `source_id` — polymorphic link back to origin (e.g., `'evaluation'`, `'audit'`, `'nonconformite'`)
- `domaine` — `'hse'` or `'qualite'`
- `statut` — `ActionStatusEnum`: `OUVERTE`, `EN_COURS`, `RESOLUE`, `FERMEE`, `ANNULEE`
- `est_recurrente` / `frequence` — for recurring actions
- `date_echeance`, `date_resolution`

**Service:** `app/services/action_service.py` — `ActionService.generate_next_occurrence(action)`

---

## 15. Notification System

**Model:** `app/models/systeme.py` — `Notification`
- Fields: `utilisateur_id`, `message`, `type` (info/warning/success/danger), `lu` (bool), `lien`, `date_creation`

**Service:** `app/services/notification_service.py`
- `validate_notification_ids()` — validation
- `send_notifications()` — batch fetch + validate + send + mark-read
- `_send_single_notification()` — send via mail (placeholder)

**Utility:** `app/utils/notifications.py`
- `create_notification(user_id, message, type)` — quick create + commit

**Frontend:** Notification polling in `layout.html`:
- Fetches `/api/notifications/unread-count` every 30s
- Shows badge with unread count
- Dropdown menu with notification list
- "Mark all read" link

---

## 16. Subscription & Quota System

**Models:**
- `SubscriptionPlan` — plan_key, label, max_users, max_documents, max_open_actions, max_storage_mb, trial_days, price_mad, features (JSON), is_active
- `Entreprise` — `abonnement_type` (FK to plan_key), `abonnement_prochaine_echeance`, `statut`, `abonnement_paye`

**Utility:** `app/utils/subscriptions.py`
- `DEFAULT_SUBSCRIPTION_PLANS` — hardcoded Essential/Professional/Premium tiers
- `_seed_default_plans()` — seeds DB on first run
- `get_subscription_plan(plan_key)` — lookup (hardcoded first, then DB)
- `get_subscription_quota_limit(plan_key, quota_name)` — quota check helper
- `get_subscription_user_limit(plan_key)` — user limit helper

**Service:** `app/services/subscription_service.py` — subscription lifecycle
**Middleware:** `app/services/quota_middleware.py` — quota enforcement

**Blueprint:** `app/plans/` — CRUD for plans, API endpoints, subscription management UI

---

## 17. Frontend Conventions

### CSS/Styling
- Bootstrap 5.3.2 classes throughout
- FontAwesome 6.5.1 for icons
- Custom CSS in `app/static/css/`
- The sidebar uses a collapsible `.sidebar.show` class for mobile

### JavaScript patterns
- **Inline in templates** (most common): JS at bottom of template in `{% block scripts %}`
- **Pattern for AJAX operations:**
  ```javascript
  fetch('/api/endpoint', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'},
    body: JSON.stringify(data)
  })
  .then(r => r.json())
  .then(data => { /* ... */ })
  .catch(err => { alert('Erreur réseau'); });
  ```
- **Auto-save** (evaluation_detail): uses `setInterval()` with debounce, POSTs partial data
- **Data loading:** functions like `loadProofs()`, `loadActions()` called on page load, fetch data and render into DOM

### Common UI patterns
- **Tabs:** Bootstrap nav-tabs with `tab-content`/`tab-pane`
- **Modals:** Bootstrap modals for confirmations, forms, proof attachment
- **Flash messages:** Flash from server → auto-dismissing Bootstrap alerts
- **Toolbar:** Button groups at top of page (Sauvegarder, Valider, etc.)
- **Badges:** For enum statuses (conforme=success, non_conforme=danger, etc.)

---

## 18. Common Patterns & Gotchas

### RESOLVED: Deleted `Document` model
The old `Document` model was deleted. All references have been migrated to `ProofMaster`/`ProofReference`:
- `app/services/proof_expiration_service.py` — now uses `ProofMaster`
- `app/services/conformite_service.py` — now uses `ProofMaster`/`ProofReference`
- `app/services/subscription_service.py` — renamed `_get_storage_size_for_proofs`

### Enum assignment
Setting `db.Enum` column to `''` (empty string) crashes with `KeyError`. Use truthy checks:
```python
# WRONG:
if valeur is not None:  # '' passes this check
    obj.colonne = valeur

# RIGHT:
if valeur:  # '' fails this check
    obj.colonne = valeur
```

### AJAX needs `X-Requested-With`
All AJAX POST requests should include `'X-Requested-With': 'XMLHttpRequest'` header. Server routes that handle both form POST and AJAX POST should use `request.get_json()` or `request.headers.get('X-Requested-With')` to distinguish and return JSON for AJAX.

### Relationship backref naming
SQLAlchemy `back_populates` must match on both sides. E.g.:
- `Article.version = relationship('TexteVersion', back_populates='articles')`
- `TexteVersion.articles = relationship('Article', back_populates='version')`

If a relationship exists on one side but not the other, you'll get:
`Mapper 'Mapper[TexteVersion(texte_version)]' has no property 'articles'`

### Tenant filtering
Tenant isolation is NOT automatic — you must manually filter all queries:
```python
MyModel.query.filter_by(entreprise_id=current_user.entreprise_id).all()
```
The `tenant_get_or_404()` helper exists for single-instance lookups.

### Module activation
Enterprise must have the domain in `modules_actifs` JSON for that module's routes to be accessible. The haccp, qualite, and hse modules check this explicitly.

### Blueprints without url_prefix
Modules registered **without** `url_prefix` (conformite, entreprise_textes, demo) have routes that may start with `/` — be careful of route conflicts. Their `Blueprint(__name__)` already includes a prefix in the route definitions.

### Migration state
There are no migration files yet in `migrations/` directory — the app uses `db.create_all()` or fresh DB creation. Alembic/Flyway is set up but unused.

### Testing
Tests are runnable, 131 pass (2 pre-existing failures unrelated to recent changes). Test infrastructure location TBD (search for `test_*.py`).
