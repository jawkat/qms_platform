# Résolution des conflits Git — Rebase `cef56c3` ← `4a3159d`

## Contexte

Deux commits ont divergé sur `master` :

| Commit | Message | Provenance |
|---|---|---|
| `cef56c3` | *veille reglementaire et gestion des preuves* | **Distant (origin/master)** |
| `4a3159d` | *refacoring code* | **Local** |

Le rebase a appliqué le commit distant d'abord, puis tenté d'appliquer le commit local par‑dessus. 7 conflits sont survenus parce que les deux commits modifiaient les mêmes fichiers de routes.

## Stratégie de résolution

**Tous les conflits ont été résolus en gardant la version locale (`4a3159d`)** car :
- Les changements locaux sont plus récents (refactoring `@access_required` + `BaseResource`)
- Les changements distants (veille réglementaire, notifications) concernent d'autres fichiers sans conflit

---

## Fichiers en conflit (7)

### 1. `app/systeme/routes.py`

**Distant** : Ajoute des routes pour la veille réglementaire et la gestion des preuves.
**Local** : Refactoring complet (`@access_required`, `BaseResource`).
**Résolution** : Gardé local. Les fonctionnalités de veille réglementaire sont dans d'autres fichiers.

---

### 2. `app/notifications/routes.py`

**Distant** : Ajoute des routes de notifications.
**Local** : Refactoring des décorateurs et helpers.
**Résolution** : Gardé local.

---

### 3. `app/conformite/routes/general.py`

**Distant** : Modifications mineures sur les routes conformité.
**Local** : Refactoring `@access_required` + `BaseResource`.
**Résolution** : Gardé local.

---

### 4. `app/conformite/routes/evaluation.py`

**Distant** : Modifications mineures sur l'évaluation conformité.
**Local** : Refactoring `@access_required` + `BaseResource`.
**Résolution** : Gardé local.

---

### 5. `app/haccp/routes.py`

**Distant** : Modifications sur les routes HACCP.
**Local** : Refactoring complet (ce fichier a été réécrit à 76 %).
**Résolution** : Gardé local.

---

### 6. `app/formations/routes.py`

**Distant** : Modifications sur les routes formations.
**Local** : Refactoring `@access_required` + `BaseResource`.
**Résolution** : Gardé local.

---

### 7. `app/qualite/routes/risques.py`

**Distant** : Modifications sur les routes risques qualité.
**Local** : Refactoring `@access_required` + `BaseResource`.
**Résolution** : Gardé local.

---

## Fichiers résiduels (amendés après le rebase)

Après le rebase, certains fichiers de routes n'avaient pas été inclus dans le commit final à cause d'un état corrompu du rebase-apply. Ils ont été rattrapés par amend successifs :

| Fichier | Problème | Correctif |
|---|---|---|
| `app/laboratoire/routes/__init__.py` | Non inclus dans le commit rebasé | Amendé |
| `app/maintenance/routes/__init__.py` | Non inclus dans le commit rebasé | Amendé |
| `app/planification/routes/__init__.py` | Non inclus dans le commit rebasé | Amendé |
| `app/reunions/routes/__init__.py` | Non inclus dans le commit rebasé | Amendé |
| `app/connaissances/routes/__init__.py` | Non inclus dans le commit rebasé | Amendé |
| `app/urgences/routes/__init__.py` | Non inclus dans le commit rebasé | Amendé |
| `app/rh_qhse/routes/__init__.py` | Non inclus dans le commit rebasé | Amendé |
| `.gitignore` | `venv/` manquant dans `.gitignore` | Ajouté |

Tous ces fichiers ont le même pattern de refactoring :
```python
# AVANT (distant)
-@login_required
-@module_active('xxx')
-@has_permission('xxx.gerer')
-def api_supprimer(item_id):
-    item = Modele.query.filter_by(id=item_id).first_or_404()
-    db.session.delete(item)
-    db.session.commit()
-    return {'success': True}

# APRÈS (local)
+@access_required(module='xxx', permission='xxx.gerer')
+def api_supprimer(item_id):
+    return XxxResource.delete_resource(item_id)
```

---

## Fichiers distants conservés (sans conflit)

Les fichiers suivants viennent uniquement du commit distant `cef56c3` et ont été conservés intacts :

- `app/main/templates/main/notifications.html` — Nouveau template
- `app/services/notification_service.py` — Nouveau service
- `app/schemas/base.py`, `competence.py`, `haccp.py`, `ishikawa.py`, `partages.py`, `nonconformite.py` — Nouveaux schémas
- `tests/test_notification_service.py` — Nouveaux tests
- Modifications dans `app/admin/`, `app/models/auth.py`, `app/extensions.py`, etc.

---

## Fichiers locaux ajoutés (sans conflit)

Les fichiers suivants viennent uniquement du commit local et ont été ajoutés :

- `app/utils/tenant_scope.py` — Auto‑découverte des modèles scopés
- `app/utils/base_resource.py` — Classe `BaseResource`
- `app/utils/permissions.py` — Décorateur `access_required`
- `app/jobs/textes_import_jobs.py` — Import JSON asynchrone RQ
- `app/textes/templates/textes/import_pending.html` — Page statut polling
- `tests/test_tenant_scope.py` — Tests tenant scope
- `tests/test_textes_import_jobs.py` — Tests import jobs
- `ARCHITECTURE_PLAN.md` — Documentation architecture

---

## Problèmes rencontrés

1. **Stale cache Docker** : Après modification des jobs, les conteneurs `qms_worker` et `qms_app` doivent être redémarrés (`docker restart`) car le cache Python des modules importés reste actif tant que le processus n'est pas relancé.

2. **Rebase-apply corrompu** : Le répertoire `.git/rebase-apply` est resté après la fin du rebase à cause d'un `git am --continue` intempestif. Résolu en supprimant manuellement `.git/rebase-apply/`.

3. **`venv/` ajouté au staging** : Le commit distant incluait des fichiers du répertoire `venv/` qui ont été propagés lors du rebase. Résolu en :
   - Unstagant `venv/` avec `git reset HEAD venv/`
   - Ajoutant `venv/` au `.gitignore`
   - Amendant le commit final

---

## Vérification

Pour vérifier que tout est correct :

```bash
# Voir la différence avec origin/master
git diff origin/master HEAD --stat

# Vérifier qu'aucun fichier venv n'est traqué
git ls-files | grep venv

# Voir les fichiers du commit distant
git log --oneline cef56c3 --stat

# Voir les fichiers du commit local
git log --oneline 4a3159d --stat
```

Le commit final est `81113f1 refacoring code`.
