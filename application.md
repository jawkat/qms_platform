# QMS Platform — Architecture universelle

## Concept

Plateforme multi-module avec **switch HSE ↔ Qualité**. L'utilisateur est soit dans le monde HSE, soit dans le monde Qualité. Un bouton en haut de la page permet de basculer.

Si l'entreprise n'a qu'un seul module, le switch est grisé.

## Structure des dossiers

```
app/
├── main/              # Landing, dashboard (filtré par domaine)
├── entreprises/       # CRUD entreprises, billing
├── users/             # Utilisateurs, rôles
├── admin/             # Super admin
├── support/           # Tickets
├── demo/              # Démo
├── actions/           # CAPA universel (HSE + Qualité)
├── documents/         # GED centralisée (ProofMaster)
├── audits/            # Audits (HSE + Qualité)
├── indicateurs/       # Indicateurs
├── conformite/        # HSE uniquement (évaluation textes)
├── textes/            # HSE uniquement (textes réglementaires)
├── qualite/           # Qualité uniquement
├── services/          # Services partagés
├── utils/             # Utilitaires partagés
├── models/            # Modèles SQLAlchemy
└── templates/         # Templates globaux
```

## Modèles universels

### ActionCorrective (CAPA)

```python
class ActionCorrective(db.Model):
    id              # PK
    entreprise_id   # FK → Entreprise (tenant scope)
    domaine         # 'hse' | 'qualite'

    description
    cause_identifiee
    type_action     # corrective, preventive, curative, periodique
    priorite        # basse, moyenne, haute, critique
    statut          # A_FAIRE, EN_COURS, REALISE, SOLDE, ANNULE

    responsable_id  # FK → Utilisateur
    date_echeance
    date_realisation

    efficacite, commentaire_efficacite, critere_efficacite
    rca_pourquoi1..5, rca_conclusion
    est_recurrente, frequence, parent_action_id

    source_type     # 'evaluation_article', 'audit', 'reclamation', 'nc_qualite', NULL
    source_id       # ID de l'entité source (NULL = action libre)

    date_creation

    proof_references → ProofReference (entity_type='action_corrective')
```

### ProofMaster (Document)

```python
class ProofMaster(db.Model):
    id              # PK
    entreprise_id   # FK → Entreprise
    domaine         # 'hse' | 'qualite'

    nom_fichier     # Nom original
    type            # extension/mime
    chemin          # Chemin relatif (local) ou clé S3
    taille_bytes
    hash_fichier    # SHA256 (déduplication)

    description
    validite        # Date d'expiration
    categorie       # 'procedure', 'instruction', 'formulaire', 'preuve', 'certificat'...
    version         # '1', '2', 'V3'...
    statut          # ACTIF, REMPLACE, ARCHIVE

    upload_par      # FK → Utilisateur
    date_creation
    date_modification
    remplace_preuve_id  # Auto-référence (versioning)
    extra_metadata  # JSON
    reference_count # Compteur de liens

    references → ProofReference
    uploader → Utilisateur
```

### ProofReference

```python
class ProofReference(db.Model):
    id
    proof_master_id     # FK → ProofMaster
    entity_type         # 'action_corrective', 'evaluation_article', 'audit'...
    entity_id           # ID de l'entité
    date_attached
    attached_by         # FK → Utilisateur
    validite_override
    description_override
    extra_metadata

    UniqueConstraint(proof_master_id, entity_type, entity_id)
```

## Plan de migration (étapes)

```
Step 1 : Modèles universels + base clean
Step 2 : ProofService partagé (extraire de conformite)
Step 3 : Blueprint Documents centralisé
Step 4 : Switch domaine + sidebar modulaire
Step 5 : Permissions Qualité + Blueprint Qualité
Step 6 : MinIO pour stockage externalisé
```

Chaque étape est **opérationnelle** — l'app tourne et on peut s'arrêter à n'importe quelle étape.

## Utilisateurs et rôles

- **Super admin** : tout voir, tout modifier, gérer les entreprises
- **Manager** : toutes les permissions HSE + Qualité
- **Pilote** : pilotage, risques, revue de direction
- **Auditeur** : audits HSE + Qualité
- **Consultant** : consultation

## Permissions

Module `actions` : actions.voir, actions.cree, actions.modifier, actions.supprimer
Module `conformite` : conformite.voir, conformite.modifier
Module `textes` : textes.voir, textes.modifier
Module `documents` : documents.voir, documents.upload, documents.archiver
Module `qualite` : qualite.voir, qualite.gerer_risques, qualite.gerer_haccp, ...

## Switch domaine

Stocké en session : `session['domaine_actif']` → 'hse', 'qualite'

Filtre toutes les requêtes sur les modèles partagés (actions, documents, audits).
