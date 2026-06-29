# Plan de Réalisation — Modules HSE (Suivi d'Implémentation)

## Vue d'ensemble

6 modules à implémenter/enrichir dans le cadre du périmètre HSE. Chaque module suit l'architecture standardisée : `BaseModel` → `AutoSchema` → `BaseResource` → `Blueprint` → `Template`.

| Phase | Module | Statut | Fichiers |
|-------|--------|--------|----------|
| 1 | 🔥 Extincteurs & RIA | ⬜ Planifié | 15 |
| 2 | ☣️ Produits dangereux / FDS | ⬜ Planifié | 13 |
| 3 | 🚶 Visites sécurité (Safety Walk) | ⬜ Planifié | 13 |
| 4 | 🔔 Notifications (enrichissement) | ⬜ Planifié | 1 |
| 5 | 🚨 Incident (enrichissement) | ⬜ Planifié | 4 |
| 6 | 🦺 Distribution EPI | ⬜ Planifié | 5 |

**Légende statut :** ⬜ Planifié | 🟡 En cours | ✅ Terminé | 🔴 Bloqué

---

## Phase 1 : Gestion des extincteurs & RIA

**Priorité :** Haute
**Objectif :** Suivi des extincteurs (numéro, type, emplacement, contrôles, recharges, expiration) et RIA (Robinet d'Incendie Armé) avec notifications automatiques.

### 1.1 Modèle — `app/models/extincteurs.py` ⬜

```python
class Extincteur(BaseModel):
    __tablename__ = 'extincteur'
    numero              = db.Column(db.String(50), nullable=False, unique=True)
    type_extincteur     = db.Column(db.String(30), nullable=False)  # poudre, co2, eau, mousse, chimique seche
    capacite            = db.Column(db.String(20))                   # 2kg, 5kg, 6L, 9L
    emplacement         = db.Column(db.String(200))
    zone                = db.Column(db.String(100))
    date_achat          = db.Column(db.Date)
    date_derniere_recharge = db.Column(db.Date)
    date_dernier_controle  = db.Column(db.Date)
    date_prochain_controle = db.Column(db.Date)
    date_expiration       = db.Column(db.Date)
    statut              = db.Column(db.String(20), default='conforme')  # conforme, a_controler, hors_service
    observations        = db.Column(db.Text)

class ControleExtincteur(db.Model, TimestampMixin):
    __tablename__ = 'controle_extincteur'
    extincteur_id   = db.Column(db.Integer, db.ForeignKey('extincteur.id'), nullable=False)
    date_controle   = db.Column(db.Date, nullable=False)
    type_controle   = db.Column(db.String(30))   # mensuel, semestriel, annuel
    conforme        = db.Column(db.Boolean, default=True)
    observations    = db.Column(db.Text)
    controleur_id   = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))

class RIA(BaseModel):
    __tablename__ = 'ria'
    numero              = db.Column(db.String(50), nullable=False, unique=True)
    emplacement         = db.Column(db.String(200))
    zone                = db.Column(db.String(100))
    diametre            = db.Column(db.String(20))   # DN19, DN25, DN33
    longueur_raccord    = db.Column(db.String(20))
    date_dernier_controle = db.Column(db.Date)
    date_prochain_controle = db.Column(db.Date)
    debit_pression      = db.Column(db.String(50))
    statut              = db.Column(db.String(20), default='conforme')
    observations        = db.Column(db.Text)
```

- [ ] Créer le fichier `app/models/extincteurs.py`
- [ ] Ajouter les imports dans `app/models/__init__.py`
- [ ] Générer la migration `flask db migrate -m "add extincteurs and ria tables"`

### 1.2 Schema — `app/schemas/extincteurs.py` ⬜

```python
class ExtincteurSchema(AutoSchema):
    class Meta:
        model = Extincteur
        load_instance = True
        include_fk = True

class ControleExtincteurSchema(AutoSchema):
    class Meta:
        model = ControleExtincteur
        load_instance = True
        include_fk = True

class RIASchema(AutoSchema):
    class Meta:
        model = RIA
        load_instance = True
        include_fk = True
```

- [ ] Créer le fichier `app/schemas/extincteurs.py`
- [ ] Ajouter les imports dans `app/schemas/__init__.py`

### 1.3 Blueprint — `app/extincteurs/__init__.py` ⬜

```python
from flask_smorest import Blueprint
blueprint = Blueprint('extincteurs', __name__, template_folder='templates',
                      description='Gestion extincteurs, RIA et contrôles périodiques')
from . import routes
```

- [ ] Créer `app/extincteurs/__init__.py`
- [ ] Créer `app/extincteurs/routes/__init__.py` → `from . import extincteurs, ria, controles`
- [ ] Créer le dossier `app/extincteurs/templates/extincteurs/`

### 1.4 Routes — `app/extincteurs/routes/extincteurs.py` ⬜

| Méthode | URL | Fonction | Description |
|---------|-----|----------|-------------|
| GET | `/` | `index()` | Dashboard extincteurs |
| GET | `/extincteurs` | `extincteurs_liste()` | Page liste |
| GET | `/api/extincteurs` | `api_extincteurs()` | JSON liste (BaseResource) |
| POST | `/api/extincteurs/create` | `api_extincteurs_create()` | Créer |
| POST | `/api/extincteurs/<id>/update` | `api_extincteurs_update()` | Modifier |
| POST | `/api/extincteurs/<id>/delete` | `api_extincteurs_delete()` | Supprimer |
| POST | `/api/extincteurs/<id>/controle` | `api_ajouter_controle()` | Ajouter contrôle |
| GET | `/api/extincteurs/<id>/controles` | `api_historique_controles()` | Historique contrôles |
| GET | `/api/stats` | `api_stats()` | Statistiques module |

- [ ] Créer le fichier routes
- [ ] Implémenter `ExtincteurResource(BaseResource)`
- [ ] Implémenter toutes les routes

### 1.5 Routes — `app/extincteurs/routes/ria.py` ⬜

| Méthode | URL | Fonction |
|---------|-----|----------|
| GET | `/ria` | `ria_liste()` |
| GET | `/api/ria` | `api_ria()` |
| POST | `/api/ria/create` | `api_ria_create()` |
| POST | `/api/ria/<id>/update` | `api_ria_update()` |
| POST | `/api/ria/<id>/delete` | `api_ria_delete()` |

- [ ] Créer le fichier routes
- [ ] Implémenter `RIAResource(BaseResource)`

### 1.6 Templates ⬜

| Template | Description |
|----------|-------------|
| `app/extincteurs/templates/extincteurs/index.html` | Dashboard avec KPIs (nb conformes, à contrôler, expirés) |
| `app/extincteurs/templates/extincteurs/extincteurs.html` | Liste + CRUD modal |
| `app/extincteurs/templates/extincteurs/ria.html` | Liste RIA + CRUD modal |
| `app/extincteurs/templates/extincteurs/controles.html` | Historique contrôles par extincteur |

- [ ] Créer `index.html` (KPI cards + alertes)
- [ ] Créer `extincteurs.html` (table + modal create/edit)
- [ ] Créer `ria.html` (table + modal create/edit)
- [ ] Créer `controles.html` (table historique)

### 1.7 Manifest & Enregistrement ⬜

```python
EXTINCTEURS_MANIFEST = ModuleManifest(
    name='extincteurs',
    display_name='Extincteurs & RIA',
    version='1.0.0',
    description='Gestion extincteurs, RIA, contrôles périodiques et recharges',
    icon='fa-fire-extinguisher',
    category='hse',
    permissions=['extincteurs.voir', 'extincteurs.gerer'],
    events_emit=['extincteur.controle_due', 'extincteur.expiration'],
    menu_position=130,
)
```

- [ ] Ajouter manifest dans `app/core/manifests.py` + `ALL_MANIFESTS`
- [ ] Enregistrer blueprint dans `app/blueprints_registry.py` → `url_prefix='/extincteurs'`
- [ ] Ajouter section sidebar dans `app/core/plugin_manager.py` → `get_sidebar_sections()`
- [ ] Ajouter permissions dans `app/utils/permission_catalog.py`

### 1.8 Notifications ⬜

- [ ] Intégrer dans `alert_engine.py` : `_alert_extincteurs_a_controle()`
- [ ] Logique : extincteurs avec `date_prochain_controle < today` ou `date_expiration < today`
- [ ] Notification aux responsables sécurité

---

## Phase 2 : Produits dangereux / FDS

**Priorité :** Haute
**Objectif :** Inventaire des produits chimiques dangereux avec gestion des FDS (Fiches de Données de Sécurité), pictogrammes GHS, compatibilité.

### 2.1 Modèle — `app/models/produits_dangereux.py` ⬜

```python
class ProduitDangereux(BaseModel):
    __tablename__ = 'produit_dangereux'
    nom                 = db.Column(db.String(200), nullable=False)
    numero_cas          = db.Column(db.String(20))
    numero_ue           = db.Column(db.String(20))
    fournisseur         = db.Column(db.String(200))
    quantite            = db.Column(db.Float)
    unite               = db.Column(db.String(20))   # kg, L, mL
    localisation        = db.Column(db.String(200))
    zone_stockage       = db.Column(db.String(100))
    type_danger         = db.Column(db.String(50))   # inflammable, toxique, corrosif, irritant, oxysant
    pictogrammes        = db.Column(db.JSON, default=list)  # ['GHS02', 'GHS05', ...]
    risques             = db.Column(db.Text)
    mesures_prevention  = db.Column(db.Text)
    compatibilite       = db.Column(db.Text)          # Produits incompatibles
    statut              = db.Column(db.String(20), default='actif')
    date_derniere_verif = db.Column(db.Date)

class FDS(BaseModel):
    __tablename__ = 'fds'
    produit_id          = db.Column(db.Integer, db.ForeignKey('produit_dangereux.id'), nullable=False)
    version             = db.Column(db.String(20))
    date_fabrication    = db.Column(db.Date)
    date_revision       = db.Column(db.Date)
    fichier             = db.Column(db.String(500))   # chemin PDF FDS
    fournisseur_fds     = db.Column(db.String(200))
    statut              = db.Column(db.String(20), default='valide')  # valide, expire, en_attente
```

- [ ] Créer le fichier `app/models/produits_dangereux.py`
- [ ] Ajouter les imports dans `app/models/__init__.py`
- [ ] Générer la migration

### 2.2 Schema — `app/schemas/produits_dangereux.py` ⬜

- [ ] `ProduitDangereuxSchema(AutoSchema)` — Meta: model, load_instance, include_fk
- [ ] `FDSSchema(AutoSchema)` — Meta: model, load_instance, include_fk
- [ ] Ajouter imports dans `app/schemas/__init__.py`

### 2.3 Blueprint — `app/produits_dangereux/__init__.py` ⬜

- [ ] Créer `app/produits_dangereux/__init__.py`
- [ ] Créer `app/produits_dangereux/routes/__init__.py` → `from . import produits, fds`
- [ ] Créer le dossier `app/produits_dangereux/templates/produits_dangereux/`

### 2.4 Routes — `app/produits_dangereux/routes/produits.py` ⬜

| Méthode | URL | Fonction |
|---------|-----|----------|
| GET | `/` | `index()` — Dashboard |
| GET | `/produits` | `produits_liste()` — Page liste |
| GET | `/api/produits` | `api_produits()` — JSON liste |
| POST | `/api/produits/create` | `api_produits_create()` |
| POST | `/api/produits/<id>/update` | `api_produits_update()` |
| POST | `/api/produits/<id>/delete` | `api_produits_delete()` |
| GET | `/api/stats` | `api_stats()` |

- [ ] Créer le fichier routes
- [ ] Implémenter `ProduitDangereuxResource(BaseResource)`

### 2.5 Routes — `app/produits_dangereux/routes/fds.py` ⬜

| Méthode | URL | Fonction |
|---------|-----|----------|
| GET | `/fds` | `fds_liste()` — Page FDS |
| GET | `/api/fds` | `api_fds()` — JSON liste |
| POST | `/api/fds/create` | `api_fds_create()` |
| POST | `/api/fds/<id>/update` | `api_fds_update()` |
| POST | `/api/fds/<id>/delete` | `api_fds_delete()` |
| POST | `/api/produits/<id>/fds` | `api_upload_fds()` — Upload FDS PDF |

- [ ] Créer le fichier routes
- [ ] Implémenter `FDSResource(BaseResource)`
- [ ] Route upload via StorageService

### 2.6 Templates ⬜

| Template | Description |
|----------|-------------|
| `index.html` | Dashboard : nb produits, alertes FDS expirées, pictogrammes |
| `produits.html` | Liste produits + CRUD modal (champs GHS) |
| `fds.html` | Liste FDS + upload PDF |

- [ ] Créer `index.html`
- [ ] Créer `produits.html`
- [ ] Créer `fds.html`

### 2.7 Manifest & Enregistrement ⬜

```python
PRODUITS_DANGEREUX_MANIFEST = ModuleManifest(
    name='produits_dangereux',
    display_name='Produits Dangereux / FDS',
    version='1.0.0',
    description='Inventaire produits chimiques, FDS, pictogrammes GHS, compatibilité',
    icon='fa-skull-crossbones',
    category='hse',
    permissions=['produits_dangereux.voir', 'produits_dangereux.gerer'],
    events_emit=['fds.expiration'],
    menu_position=140,
)
```

- [ ] Ajouter manifest dans `app/core/manifests.py`
- [ ] Enregistrer blueprint dans `app/blueprints_registry.py` → `url_prefix='/produits-dangereux'`
- [ ] Ajouter section sidebar dans `app/core/plugin_manager.py`
- [ ] Ajouter permissions dans `app/utils/permission_catalog.py`

### 2.8 Notifications ⬜

- [ ] Intégrer dans `alert_engine.py` : `_alert_fds_expiration()`
- [ ] Logique : FDS avec `statut='valide'` et `date_revision < today` ou `date_revision < today+30`

---

## Phase 3 : Visites sécurité (Safety Walk)

**Priorité :** Haute
**Objectif :** Tournées terrain avec constatations, non-conformités, photos, actions immédiates. Distinct des inspections génériques.

### 3.1 Modèle — `app/models/visites_securite.py` ⬜

```python
class VisiteSecurite(BaseModel):
    __tablename__ = 'visite_securite'
    titre                   = db.Column(db.String(200), nullable=False)
    date_visite             = db.Column(db.Date, nullable=False)
    zone                    = db.Column(db.String(200))
    visiteur_id             = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    description             = db.Column(db.Text)
    statut                  = db.Column(db.String(20), default='en_cours')  # en_cours, terminee, validee
    photos                  = db.Column(db.JSON, default=list)
    nb_non_conformites      = db.Column(db.Integer, default=0)
    nb_actions_immediates   = db.Column(db.Integer, default=0)

class NonConformiteVisite(db.Model, TimestampMixin):
    __tablename__ = 'non_conformite_visite'
    visite_id           = db.Column(db.Integer, db.ForeignKey('visite_securite.id'), nullable=False)
    description         = db.Column(db.Text, nullable=False)
    risque              = db.Column(db.String(50))   # faible, moyen, eleve, critique
    photo               = db.Column(db.String(500))
    action_immédiate    = db.Column(db.Text)
    responsable_id      = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    statut              = db.Column(db.String(20), default='ouverte')  # ouverte, en_cours, cloturee
    date_echeance       = db.Column(db.Date)
```

- [ ] Créer le fichier `app/models/visites_securite.py`
- [ ] Ajouter les imports dans `app/models/__init__.py`
- [ ] Générer la migration

### 3.2 Schema — `app/schemas/visites_securite.py` ⬜

- [ ] `VisiteSecuriteSchema(AutoSchema)` — avec `enfants = fields.Nested(NonConformiteVisiteSchema, many=True, dump_only=True)`
- [ ] `NonConformiteVisiteSchema(AutoSchema)`
- [ ] Ajouter imports dans `app/schemas/__init__.py`

### 3.3 Blueprint — `app/visites_securite/__init__.py` ⬜

- [ ] Créer `app/visites_securite/__init__.py`
- [ ] Créer `app/visites_securite/routes/__init__.py` → `from . import visites, non_conformites`
- [ ] Créer le dossier `app/visites_securite/templates/visites_securite/`

### 3.4 Routes — `app/visites_securite/routes/visites.py` ⬜

| Méthode | URL | Fonction |
|---------|-----|----------|
| GET | `/` | `index()` — Dashboard |
| GET | `/visites` | `visites_liste()` — Page liste |
| GET | `/visites/<id>` | `visite_detail()` — Détile visite + NC |
| GET | `/api/visites` | `api_visites()` — JSON liste |
| POST | `/api/visites/create` | `api_visites_create()` |
| POST | `/api/visites/<id>/update` | `api_visites_update()` |
| POST | `/api/visites/<id>/delete` | `api_visites_delete()` |
| POST | `/api/visites/<id>/valider` | `api_visite_valider()` — Valider la visite |
| POST | `/api/visites/<id>/photos` | `api_visite_photos()` — Upload photos |
| GET | `/api/stats` | `api_stats()` |

- [ ] Créer le fichier routes
- [ ] Implémenter `VisiteSecuriteResource(BaseResource)`

### 3.5 Routes — `app/visites_securite/routes/non_conformites.py` ⬜

| Méthode | URL | Fonction |
|---------|-----|----------|
| POST | `/api/visites/<id>/nc` | `api_ajouter_nc()` — Ajouter NC à une visite |
| POST | `/api/nc/<id>/update` | `api_nc_update()` — Modifier NC |
| POST | `/api/nc/<id>/delete` | `api_nc_delete()` — Supprimer NC |
| POST | `/api/nc/<id>/cloturer` | `api_nc_cloturer()` — Clôturer NC |

- [ ] Créer le fichier routes

### 3.6 Templates ⬜

| Template | Description |
|----------|-------------|
| `index.html` | Dashboard : nb visites, NC ouvertes, taux clôture, dernières visites |
| `visites.html` | Liste visites + CRUD modal |
| `detail.html` | Détail visite : infos + tableau NC + upload photos + actions |

- [ ] Créer `index.html`
- [ ] Créer `visites.html`
- [ ] Créer `detail.html`

### 3.7 Manifest & Enregistrement ⬜

```python
VISITES_SECURITE_MANIFEST = ModuleManifest(
    name='visites_securite',
    display_name='Visites Sécurité (Safety Walk)',
    version='1.0.0',
    description='Tournées terrain, constatations, non-conformités, actions immédiates',
    icon='fa-walking',
    category='hse',
    permissions=['visites_securite.voir', 'visites_securite.gerer'],
    events_emit=['visite.nc_declaree'],
    menu_position=150,
)
```

- [ ] Ajouter manifest dans `app/core/manifests.py`
- [ ] Enregistrer blueprint dans `app/blueprints_registry.py` → `url_prefix='/visites-securite'`
- [ ] Ajouter section sidebar dans `app/core/plugin_manager.py`
- [ ] Ajouter permissions dans `app/utils/permission_catalog.py`

---

## Phase 4 : Notifications (Enrichissement)

**Priorité :** Moyenne
**Objectif :** Ajouter 4 nouveaux types d'alertes automatiques dans le daily alert engine.

### 4.1 Modifier `app/services/alert_engine.py` ⬜

Nouvelles fonctions à ajouter :

```python
def _alert_audits_a_realiser():
    """Audits planifiés dans les 7 prochains jours non démarrés."""
    # Query Audit WHERE date_audit BETWEEN today AND today+7 AND resultat_global IS NULL

def _alert_formations_a_renouveler():
    """Certifications formations expirées ou expirant < 30 jours."""
    # Query FormationParticipant WHERE certifie=True AND date_expiration < today+30

def _alert_epi_a_remplacer():
    """EPI avec date_peremption dépassée ou prochain_controle < today."""
    # Query EPI WHERE date_peremption < today OR prochain_controle < today

def _alert_extincteurs_a_controle():
    """Extincteurs avec date_prochain_controle < today ou date_expiration < today."""
    # Query Extincteur WHERE statut != 'hors_service' AND (date_prochain_controle < today OR date_expiration < today)
```

Intégration dans `run_daily_alerts()` :
```python
results['audits_a_realiser'] = _alert_audits_a_realiser()
results['formations_renouveler'] = _alert_formations_a_renouveler()
results['epi_a_remplacer'] = _alert_epi_a_remplacer()
results['extincteurs_controle'] = _alert_extincteurs_a_controle()
```

- [ ] Ajouter `_alert_audits_a_realiser()`
- [ ] Ajouter `_alert_formations_a_renouveler()`
- [ ] Ajouter `_alert_epi_a_remplacer()`
- [ ] Ajouter `_alert_extincteurs_a_controle()`
- [ ] Intégrer dans `run_daily_alerts()`
- [ ] Tester le job RQ `run_alerts_job()`

---

## Phase 5 : Déclaration d'incident (Enrichissement)

**Priorité :** Moyenne
**Objectif :** Ajouter upload de photos et champ dédié "Actions immédiates".

### 5.1 Modifier `app/models/hse.py` ⬜

Ajouter au modèle `Incident` :
```python
actions_immediates = db.Column(db.Text)
photos = db.Column(db.JSON, default=list)  # Liste de chemins de fichiers
```

- [ ] Ajouter `actions_immediates` au modèle Incident
- [ ] Ajouter `photos` au modèle Incident
- [ ] Générer la migration

### 5.2 Modifier `app/schemas/hse.py` ⬜

- [ ] Ajouter `actions_immediates` dans `IncidentSchema`
- [ ] Ajouter `photos` dans `IncidentSchema` (dump_only)

### 5.3 Modifier `app/hse/routes/incidents.py` ⬜

Nouvelle route :
```python
@blueprint.post('/api/incidents/<int:item_id>/photos')
@access_required(module='hse', permission='hse.gerer_incidents')
def api_incident_photos(item_id):
    """Upload photo pour un incident"""
    # Utiliser StorageService pour stocker le fichier
    # Ajouter le chemin à incident.photos (JSON list)
```

- [ ] Ajouter route upload photos
- [ ] Utiliser `StorageService` existant pour le stockage

### 5.4 Modifier `app/hse/templates/hse/incidents.html` ⬜

- [ ] Ajouter champ textarea "Actions immédiates" dans le formulaire
- [ ] Ajouter zone drag & drop pour upload photos
- [ ] Afficher photos existantes dans le détail

### 5.5 Migration ⬜

- [ ] Générer la migration `flask db migrate -m "enrich incident with photos and actions_immediates"`

---

## Phase 6 : Distribution EPI

**Priorité :** Standard
**Objectif :** Historique des distributions EPI par employé avec suivi des retours.

### 6.1 Modèle — ajout dans `app/models/hse.py` ⬜

```python
class DistributionEPI(BaseModel):
    __tablename__ = 'distribution_epi'
    epi_id              = db.Column(db.Integer, db.ForeignKey('epi.id'), nullable=False)
    utilisateur_id      = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    date_distribution   = db.Column(db.Date, nullable=False)
    quantite            = db.Column(db.Integer, default=1)
    distribue_par_id    = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_retour         = db.Column(db.Date)
    motif               = db.Column(db.Text)
    statut              = db.Column(db.String(20), default='actif')  # actif, retourne, perime
    observation         = db.Column(db.Text)

    epi = db.relationship('EPI')
    utilisateur = db.relationship('Utilisateur', foreign_keys=[utilisateur_id])
    distribue_par = db.relationship('Utilisateur', foreign_keys=[distribue_par_id])
```

- [ ] Ajouter `DistributionEPI` dans `app/models/hse.py`
- [ ] Ajouter imports dans `app/models/__init__.py`
- [ ] Générer la migration

### 6.2 Schema — ajout dans `app/schemas/hse.py` ⬜

```python
class DistributionEPISchema(AutoSchema):
    class Meta:
        model = DistributionEPI
        load_instance = True
        include_fk = True
    epi = fields.Nested(EPISchema, dump_only=True)
    utilisateur = fields.Nested('UtilisateurSchema', dump_only=True)
```

- [ ] Ajouter `DistributionEPISchema` dans `app/schemas/hse.py`

### 6.3 Routes — ajout dans `app/hse/routes/epi.py` ⬜

| Méthode | URL | Fonction |
|---------|-----|----------|
| GET | `/api/epi/<id>/distributions` | `api_epi_distributions()` — Historique |
| POST | `/api/epi/<id>/distribute` | `api_epi_distribute()` — Enregistrer distribution |
| POST | `/api/distributions/<id>/retour` | `api_distribution_retour()` — Enregistrer retour |
| GET | `/api/employes/<id>/epi` | `api_employe_epi()` — EPI d'un employé |

- [ ] Ajouter `DistributionEPIResource(BaseResource)`
- [ ] Ajouter les 4 routes

### 6.4 Template — modifier `app/hse/templates/hse/epi.html` ⬜

- [ ] Ajouter 2ème onglet "Distributions" dans la page
- [ ] Tableau historique distributions avec filtres
- [ ] Modal pour enregistrer une distribution
- [ ] Bouton "Retour" par ligne
- [ ] Vue "EPI par employé"

### 6.5 Migration ⬜

- [ ] Générer la migration `flask db migrate -m "add distribution_epi table"`

---

## Check-list transversale

### Par module, vérifier :

- [ ] Modèle hérite de `BaseModel` (ou `db.Model + TimestampMixin` pour les sous-objets)
- [ ] `__tablename__` en snake_case singulier
- [ ] Schema hérite de `AutoSchema` avec `load_instance=True, include_fk=True`
- [ ] Blueprint init avec `from flask_smorest import Blueprint` + `template_folder='templates'`
- [ ] Routes init avec imports de tous les sous-modules
- [ ] Routes utilisent `@access_required(module='...', permission='...')`
- [ ] Decorator order : `@blueprint.get/post` → `@access_required` → `@blueprint.arguments` → `@blueprint.response`
- [ ] Templates extends `layout.html` avec blocks `title`, `content`, `scripts`
- [ ] JS utilise `fetch()` avec `url_for()` pour les APIs
- [ ] Modal create/edit avec pattern `UPDATE.replace('0', id)`
- [ ] Manifest ajouté dans `ALL_MANIFESTS`
- [ ] Blueprint enregistré dans `blueprints_registry.py`
- [ ] Section sidebar ajoutée dans `plugin_manager.py`
- [ ] Permissions ajoutées dans `permission_catalog.py`
- [ ] Migration générée et testée
- [ ] Notifications intégrées dans `alert_engine.py` si applicable

### Commandes de test :

```bash
# Générer migration
flask db migrate -m "description"

# Appliquer migration
flask db upgrade

# Lancer le serveur
python run.py

# Tester les APIs
curl http://localhost:5005/hse/api/incidents
curl http://localhost:5005/extincteurs/api/extincteurs
curl http://localhost:5005/produits-dangereux/api/produits
curl http://localhost:5005/visites-securite/api/visites

# Tester le daily alert engine
flask shell -c "from app.services.alert_engine import run_daily_alerts; print(run_daily_alerts())"
```

---

## Fichiers modifiés existants (résumé)

| Fichier | Modifications |
|---------|---------------|
| `app/models/__init__.py` | + imports Extincteur, RIA, ControleExtincteur, ProduitDangereux, FDS, VisiteSecurite, NonConformiteVisite, DistributionEPI |
| `app/models/hse.py` | + DistributionEPI, + actions_immediates/photos sur Incident |
| `app/schemas/__init__.py` | + imports nouveaux schemas |
| `app/schemas/hse.py` | + DistributionEPISchema, + champs IncidentSchema |
| `app/hse/routes/epi.py` | + routes distribution |
| `app/hse/routes/incidents.py` | + route upload photos |
| `app/services/alert_engine.py` | + 4 nouvelles alertes |
| `app/core/manifests.py` | + 3 manifests (extincteurs, produits_dangereux, visites_securite) |
| `app/blueprints_registry.py` | + 3 blueprints |
| `app/core/plugin_manager.py` | + 3 sections sidebar |
| `app/utils/permission_catalog.py` | + permissions nouvelles |

## Fichiers créés (résumé)

| Fichier | Module |
|---------|--------|
| `app/models/extincteurs.py` | Extincteurs |
| `app/models/produits_dangereux.py` | Produits dangereux |
| `app/models/visites_securite.py` | Visites sécurité |
| `app/schemas/extincteurs.py` | Extincteurs |
| `app/schemas/produits_dangereux.py` | Produits dangereux |
| `app/schemas/visites_securite.py` | Visites sécurité |
| `app/extincteurs/__init__.py` | Extincteurs |
| `app/extincteurs/routes/__init__.py` | Extincteurs |
| `app/extincteurs/routes/extincteurs.py` | Extincteurs |
| `app/extincteurs/routes/ria.py` | Extincteurs |
| `app/extincteurs/templates/extincteurs/*.html` (×4) | Extincteurs |
| `app/produits_dangereux/__init__.py` | Produits dangereux |
| `app/produits_dangereux/routes/__init__.py` | Produits dangereux |
| `app/produits_dangereux/routes/produits.py` | Produits dangereux |
| `app/produits_dangereux/routes/fds.py` | Produits dangereux |
| `app/produits_dangereux/templates/produits_dangereux/*.html` (×3) | Produits dangereux |
| `app/visites_securite/__init__.py` | Visites sécurité |
| `app/visites_securite/routes/__init__.py` | Visites sécurité |
| `app/visites_securite/routes/visites.py` | Visites sécurité |
| `app/visites_securite/routes/non_conformites.py` | Visites sécurité |
| `app/visites_securite/templates/visites_securite/*.html` (×3) | Visites sécurité |
| `migrations/versions/xxx_add_extincteurs_ria.py` | Extincteurs |
| `migrations/versions/xxx_add_produits_dangereux_fds.py` | Produits dangereux |
| `migrations/versions/xxx_add_visites_securite.py` | Visites sécurité |
| `migrations/versions/xxx_add_distribution_epi.py` | EPI |
| `migrations/versions/xxx_enrich_incident.py` | Incident |

**Total : ~45 fichiers créés, ~11 fichiers modifiés**
