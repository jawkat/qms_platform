# Manuel des Fonctionnalités — QMS Platform

> **Dernière mise à jour** : 2026-06-24
> **Version** : 1.0.0
> Ce document recense l'ensemble des fonctionnalités granulaires de la plateforme QMS, classées par module et par profil utilisateur. Il est mis à jour à chaque ajout ou modification de fonctionnalité.

---

## Table des matières

1. [Système de rôles et permissions](#1-système-de-rôles-et-permissions)
2. [Authentification & Gestion des utilisateurs](#2-authentification--gestion-des-utilisateurs)
3. [Tableau de bord & Navigation](#3-tableau-de-bord--navigation)
4. [Administration système](#4-administration-système)
5. [Veille réglementaire & Textes](#5-veille-réglementaire--textes)
6. [Conformité réglementaire](#6-conformité-réglementaire)
7. [Actions Correctives](#7-actions-correctives)
8. [Audits](#8-audits)
9. [GED & Documents](#9-ged--documents)
10. [Non-Conformités & CAPA](#10-non-conformités--capa)
11. [Indicateurs & Objectifs](#11-indicateurs--objectifs)
12. [Formations & Compétences](#12-formations--compétences)
13. [Fournisseurs](#13-fournisseurs)
14. [Réclamations clients](#14-réclamations-clients)
15. [Ishikawa (Analyse causes)](#15-ishikawa-analyse-causes)
16. [HSE — Incidents, EPI, Inspections, Permis](#16-hse--incidents-epi-inspections-permis)
17. [HSE — DUER & Dangers SST](#17-hse--duer--dangers-sst)
18. [HACCP & Sécurité Alimentaire](#18-haccp--sécurité-alimentaire)
19. [Processus & BPMN](#19-processus--bpmn)
20. [Change Management](#20-change-management)
21. [Workflow Engine](#21-workflow-engine)
22. [Facturation & Abonnements](#22-facturation--abonnements)
23. [Secteurs](#23-secteurs)
24. [Entreprises](#24-entreprises)
25. [Support (Tickets)](#25-support-tickets)
26. [Notifications](#26-notifications)
27. [Modules avancés](#27-modules-avancés)

---

## 1. Système de rôles et permissions

### Profils utilisateurs

| Profil | Description | Accès RBAC |
|--------|-------------|------------|
| **Admin Système** | Administrateur technique de la plateforme. `role.est_systeme = True` | **Bypass total** — accède à tout sans vérification de permission |
| **Manager** | Administrateur d'entreprise. `role.nom = 'Manager'` | Accès à toutes les permissions **sauf** `admin.*` et `textes.modifier` |
| **Auditeur** | Auditeur qualité/HSE | Permissions dédiées (audit, conformité, indicateurs) |
| **Responsable opérationnel** | Chef d'équipe / responsable de zone | Permissions opérationnelles (actions, HSE, HACCP) |
| **Consultant** | Consultant externe | Permissions en lecture + évaluation limitée |
| **Employé** | Utilisateur standard | Permissions minimales (lecture, déclaration incidents) |

### Logique de permissions

- `admin.*` → Réservé Admin Système uniquement
- `textes.modifier` → Admin Système uniquement (Manager ne peut PAS modifier les textes réglementaires)
- `textes.voir` → Manager etbelow peuvent lire les textes
- Toute permission `*.voir` → Lecture
- Toute permission `*.gerer` ou `*.modifier` → Écriture/Modification
- Toute permission `*.supprimer` → Suppression
- Toute permission `*.cree` → Création

---

## 2. Authentification & Gestion des utilisateurs

**Blueprint** : `users` — **URL** : `/users/`

### Fonctionnalités publiques (sans authentification)

| Fonctionnalité | Route | Méthode | Rôle requis |
|----------------|-------|---------|-------------|
| Connexion | `/users/login` | GET/POST | Public |
| Inscription (création entreprise + manager) | `/users/register` | GET/POST | Public |
| Mot de passe oublié | `/users/forgot-password` | GET/POST | Public |
| Réinitialisation mot de passe (via token) | `/users/reset-password/<token>` | GET/POST | Public (token valide) |

### Fonctionnalités authentifiées

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste des utilisateurs | `/users/` | GET | `users.voir` | ✅ | ✅ | ❌ |
| Créer un utilisateur | `/users/create` | GET/POST | `users.cree` | ✅ | ✅ | ❌ |
| Profil personnel | `/users/profile` | GET/POST | Authentifié | ✅ | ✅ | ✅ |
| Changer mot de passe | `/users/change-password` | GET/POST | Authentifié | ✅ | ✅ | ✅ |
| Activer/Désactiver un utilisateur | `/users/<id>/toggle-status` | POST | `users.modifier` | ✅ | ✅ | ❌ |
| Réinitialiser mot de passe d'un utilisateur | `/users/<id>/reset-password` | POST | `users.modifier` | ✅ | ✅ | ❌ |
| Déconnexion | `/users/logout` | GET | Authentifié | ✅ | ✅ | ✅ |
| Préférences de notifications | `/users/notifications/preferences` | GET/POST | Authentifié | ✅ | ✅ | ✅ |

---

## 3. Tableau de bord & Navigation

**Blueprint** : `main` — **URL** : `/`

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Page d'accueil / Landing | `/` | GET | Public | ✅ | ✅ | ✅ |
| Tableau de bord | `/tableau-de-bord` | GET | `actions.voir` | ✅ | ✅ | ✅ |
| API alertes dashboard | `/api/dashboard/alerts` | GET | `actions.voir` | ✅ (toutes) | ✅ (entreprise) | ✅ (assignées) |
| API stats globales | `/api/stats` | GET | `actions.voir` | ✅ | ✅ | ✅ |
| ~~Switch domaine HSE/Qualite~~ | ~~`/switch-domaine/<domaine>`~~ | - | **SUPPRIME** | **SUPPRIME** | **SUPPRIME** |
| Notifications (page) | `/notifications` | GET | Authentifié | ✅ | ✅ | ✅ |
| API notifications | `/api/notifications` | GET | Authentifié | ✅ | ✅ | ✅ |
| API compte notifications non lues | `/api/notifications/unread-count` | GET | Authentifié | ✅ | ✅ | ✅ |
| Marquer notification lue | `/api/notifications/<id>/read` | POST | Authentifié | ✅ | ✅ | ✅ |
| Marquer toutes comme lues | `/api/notifications/read-all` | POST | Authentifié | ✅ | ✅ | ✅ |
| Ouvrir notification (redirection) | `/notifications/<id>/open` | GET | Authentifié | ✅ | ✅ | ✅ |
| Recherche globale | `/search` | GET | Authentifié | ✅ | ✅ | ✅ |
| Export Excel par module | `/export/<module>` | GET | Authentifié | ✅ | ✅ | ✅ |
| Déclencher alertes manuellement | `/api/alerts/trigger` | POST | Admin Système | ✅ | ❌ | ❌ |
| Health check | `/health` | GET | Public | ✅ | ✅ | ✅ |
| Page suspension | `/suspended` | GET | Authentifié | ✅ | ✅ | ✅ |

---

## 4. Administration système

**Blueprint** : `admin` — **URL** : `/admin/`

> **Toutes les routes admin sont réservées à l'Admin Système** (`@admin_required` — vérifie `role.est_systeme == True`)

### Dashboard Admin

| Fonctionnalité | Route | Méthode | Admin | Manager | User |
|----------------|-------|---------|-------|---------|------|
| Dashboard admin (stats globales) | `/admin/` | GET | ✅ | ❌ | ❌ |

### Gestion des entreprises

| Fonctionnalité | Route | Méthode | Admin | Manager | User |
|----------------|-------|---------|-------|---------|------|
| Liste des entreprises | `/admin/entreprises` | GET | ✅ | ❌ | ❌ |
| Détail entreprise | `/admin/entreprises/<eid>` | GET | ✅ | ❌ | ❌ |
| Mettre à jour entreprise | `/admin/entreprises/<eid>/update` | POST | ✅ | ❌ | ❌ |
| Suspendre/Réactiver entreprise | `/admin/entreprises/<eid>/suspendre` | POST | ✅ | ❌ | ❌ |
| API quotas entreprise | `/admin/entreprises/<eid>/api/quota` | GET | ✅ | ❌ | ❌ |
| API paiements entreprise | `/admin/entreprises/<eid>/api/paiements` | GET | ✅ | ❌ | ❌ |
| Enregistrer paiement | `/admin/entreprises/<eid>/api/paiements/create` | POST | ✅ | ❌ | ❌ |

### Gestion des rôles et permissions

| Fonctionnalité | Route | Méthode | Admin | Manager | User |
|----------------|-------|---------|-------|---------|------|
| Liste des rôles | `/admin/roles` | GET | ✅ | ❌ | ❌ |
| Créer un rôle | `/admin/roles/create` | POST | ✅ | ❌ | ❌ |
| Éditer un rôle | `/admin/roles/<id>/edit` | GET | ✅ | ❌ | ❌ |
| Mettre à jour un rôle | `/admin/roles/<id>/update` | POST | ✅ | ❌ | ❌ |
| Supprimer un rôle | `/admin/roles/<id>/delete` | POST | ✅ | ❌ | ❌ |
| Catalogue des permissions | `/admin/permissions` | GET | ✅ | ❌ | ❌ |

### Gestion des utilisateurs (admin)

| Fonctionnalité | Route | Méthode | Admin | Manager | User |
|----------------|-------|---------|-------|---------|------|
| Liste tous les utilisateurs | `/admin/utilisateurs` | GET | ✅ | ❌ | ❌ |
| Activer/Désactiver un utilisateur | `/admin/utilisateurs/<id>/toggle` | POST | ✅ | ❌ | ❌ |
| Réinitialiser mot de passe | `/admin/utilisateurs/<id>/reset-password` | POST | ✅ | ❌ | ❌ |

### Gestion des tickets (admin side)

| Fonctionnalité | Route | Méthode | Admin | Manager | User |
|----------------|-------|---------|-------|---------|------|
| Liste de tous les tickets | `/admin/tickets` | GET | ✅ | ❌ | ❌ |
| Détail ticket | `/admin/tickets/<id>` | GET | ✅ | ❌ | ❌ |
| Répondre à un ticket | `/admin/tickets/<id>/message` | POST | ✅ | ❌ | ❌ |
| Changer statut ticket | `/admin/tickets/<id>/statut` | POST | ✅ | ❌ | ❌ |

### Sécurité & Journal

| Fonctionnalité | Route | Méthode | Admin | Manager | User |
|----------------|-------|---------|-------|---------|------|
| Journal de sécurité | `/admin/securite` | GET | ✅ | ❌ | ❌ |
| Résoudre un incident | `/admin/securite/<id>/resolve` | POST | ✅ | ❌ | ❌ |
| Résoudre tous les incidents | `/admin/securite/resolve-all` | POST | ✅ | ❌ | ❌ |
| Supprimer un incident | `/admin/securite/<id>/delete` | POST | ✅ | ❌ | ❌ |
| Supprimer tous les incidents | `/admin/securite/delete-all` | POST | ✅ | ❌ | ❌ |
| Détail incident (JSON) | `/admin/securite/<id>/detail` | GET | ✅ | ❌ | ❌ |

### Notifications (admin)

| Fonctionnalité | Route | Méthode | Admin | Manager | User |
|----------------|-------|---------|-------|---------|------|
| Vue admin notifications | `/admin/notifications` | GET | ✅ | ❌ | ❌ |
| Envoyer une notification | `/admin/notifications/send` | POST | ✅ | ❌ | ❌ |
| Supprimer une notification | `/admin/notifications/<id>/delete` | POST | ✅ | ❌ | ❌ |
| Supprimer toutes les notifications | `/admin/notifications/delete-all` | POST | ✅ | ❌ | ❌ |
| Marquer toutes comme lues | `/admin/notifications/mark-all-read` | POST | ✅ | ❌ | ❌ |

### Plans d'abonnement

| Fonctionnalité | Route | Méthode | Admin | Manager | User |
|----------------|-------|---------|-------|---------|------|
| Gestion des plans | `/admin/plans` | GET | ✅ | ❌ | ❌ |
| Seed plans par défaut | `/admin/plans/seed` | POST | ✅ | ❌ | ❌ |
| Supprimer un plan | `/admin/plans/<id>/delete` | POST | ✅ | ❌ | ❌ |
| Mettre à jour un plan (API) | `/admin/plans/api/<id>/update` | POST | ✅ | ❌ | ❌ |

### Services & Diagnostics

| Fonctionnalité | Route | Méthode | Admin | Manager | User |
|----------------|-------|---------|-------|---------|------|
| Page services/diagnostics | `/admin/services` | GET | ✅ | ❌ | ❌ |
| Test email | `/admin/mail-test` | GET | ✅ | ❌ | ❌ |
| Envoyer email de test | `/admin/mail-test/send` | POST | ✅ | ❌ | ❌ |

### Sauvegardes

| Fonctionnalité | Route | Méthode | Admin | Manager | User |
|----------------|-------|---------|-------|---------|------|
| Liste des sauvegardes | `/admin/backups` | GET | ✅ | ❌ | ❌ |
| Créer une sauvegarde | `/admin/backups/create` | POST | ✅ | ❌ | ❌ |
| Restaurer une sauvegarde | `/admin/backups/<file>/restore` | POST | ✅ | ❌ | ❌ |
| Supprimer une sauvegarde | `/admin/backups/<file>/delete` | POST | ✅ | ❌ | ❌ |

---

## 5. Veille réglementaire & Textes

### 5.1 Textes réglementaires (Admin Système)

**Blueprint** : `textes` — **URL** : `/admin/textes/`

> Toutes les opérations CRUD sur les textes sont **réservées à l'Admin Système** (`@system_admin_required`)

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste des textes | `/admin/textes/` | GET | `textes.voir` | ✅ | ✅ (lecture) | ✅ (lecture) |
| Détail texte | `/admin/textes/<id>` | GET | `textes.voir` | ✅ | ✅ (redirect version) | ✅ (redirect version) |
| Créer un texte | `/admin/textes/create` | GET/POST | `textes.modifier` | ✅ | ❌ | ❌ |
| Modifier un texte | `/admin/textes/<id>/edit` | GET/POST | `textes.modifier` | ✅ | ❌ | ❌ |
| Supprimer un texte | `/admin/textes/<id>/delete` | POST | `textes.modifier` | ✅ | ❌ | ❌ |
| API liste textes | `/admin/textes/api/liste` | GET | `textes.voir` | ✅ | ✅ | ✅ |
| API créer texte (JSON) | `/admin/textes/api/create` | POST | `textes.modifier` | ✅ | ❌ | ❌ |
| API modifier texte (JSON) | `/admin/textes/api/<id>/update` | POST | `textes.modifier` | ✅ | ❌ | ❌ |
| API supprimer texte (JSON) | `/admin/textes/api/<id>/delete` | POST | `textes.modifier` | ✅ | ❌ | ❌ |

### 5.2 Versions de textes

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Détail version | `/admin/textes/version/<id>` | GET | `textes.voir` | ✅ | ✅ | ✅ |
| Créer une version | `/admin/textes/<id>/version/create` | GET/POST | `textes.modifier` | ✅ | ❌ | ❌ |
| Modifier une version | `/admin/textes/version/<id>/edit` | GET/POST | `textes.modifier` | ✅ | ❌ | ❌ |
| Supprimer une version | `/admin/textes/version/<id>/delete` | POST | `textes.modifier` | ✅ | ❌ | ❌ |
| API créer version | `/admin/textes/api/<id>/version/create` | POST | `textes.modifier` | ✅ | ❌ | ❌ |
| API modifier version | `/admin/textes/api/version/<id>/update` | POST | `textes.modifier` | ✅ | ❌ | ❌ |
| API supprimer version | `/admin/textes/api/version/<id>/delete` | POST | `textes.modifier` | ✅ | ❌ | ❌ |

### 5.3 Articles

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Détail article (évaluation) | `/admin/textes/bibliotheque/article/<id>` | GET/POST | `textes.voir` | ✅ | ✅ | ✅ |
| Créer un article | `/admin/textes/version/<id>/article/create` | GET/POST | `textes.modifier` | ✅ | ❌ | ❌ |
| Modifier un article | `/admin/textes/article/<id>/edit` | GET/POST | `textes.modifier` | ✅ | ❌ | ❌ |
| Supprimer un article | `/admin/textes/article/<id>/delete` | POST | `textes.modifier` | ✅ | ❌ | ❌ |
| API créer article | `/admin/textes/api/version/<id>/article/create` | POST | `textes.modifier` | ✅ | ❌ | ❌ |
| API modifier article | `/admin/textes/api/article/<id>/update` | POST | `textes.modifier` | ✅ | ❌ | ❌ |
| API supprimer article | `/admin/textes/api/article/<id>/delete` | POST | `textes.modifier` | ✅ | ❌ | ❌ |
| Évaluer un article (conformité) | `/admin/textes/bibliotheque/article/<id>` | POST | `textes.voir` | ✅ | ✅ | ✅ |
| Attacher preuve à un article | `/admin/textes/bibliotheque/article/<id>/proof/attach` | POST | `textes.voir` | ✅ | ✅ | ✅ |
| Liste preuves d'un article | `/admin/textes/bibliotheque/article/<id>/proof/liste` | GET | `textes.voir` | ✅ | ✅ | ✅ |
| Ajouter action depuis article | `/admin/textes/bibliotheque/article/<id>/action/add` | POST | `textes.voir` | ✅ | ✅ | ✅ |
| Liste actions d'un article | `/admin/textes/bibliotheque/article/<id>/actions` | GET | `textes.voir` | ✅ | ✅ | ✅ |

### 5.4 Bibliothèque de textes

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Tous les textes | `/admin/textes/bibliotheque` | GET | `textes.voir` | ✅ | ✅ | ✅ |
| Nouveaux textes | `/admin/textes/bibliotheque/nouveaux-textes` | GET | `textes.voir` | ✅ | ✅ | ✅ |
| Mises à jour récentes | `/admin/textes/bibliotheque/mises-a-jour-recentes` | GET | `textes.voir` | ✅ | ✅ | ✅ |
| Dashboard veille | `/admin/textes/bibliotheque/veille-dashboard` | GET | `textes.voir` | ✅ | ✅ | ✅ |
| Preuves de conformité | `/admin/textes/bibliotheque/preuves` | GET | `textes.voir` | ✅ | ✅ | ✅ |
| Upload preuve | `/admin/textes/bibliotheque/preuves/upload` | POST | `textes.voir` | ✅ | ✅ | ✅ |
| Télécharger preuve | `/admin/textes/bibliotheque/preuves/<id>/download` | GET | `textes.voir` | ✅ | ✅ | ✅ |
| Supprimer preuve | `/admin/textes/bibliotheque/preuves/<id>/supprimer` | POST | `textes.voir` | ✅ | ✅ | ✅ |
| Non-conformités veille | `/admin/textes/bibliotheque/non-conformites` | GET | `textes.voir` | ✅ | ✅ | ✅ |

### 5.5 Import JSON

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Import JSON (page) | `/admin/textes/import_json` | GET/POST | Admin Système | ✅ | ❌ | ❌ |
| Preview import | `/admin/textes/import_json` (POST preview) | POST | Admin Système | ✅ | ❌ | ❌ |
| Confirmer import | `/admin/textes/import_json/confirm` | POST | Admin Système | ✅ | ❌ | ❌ |
| Statut import (polling) | `/admin/textes/import_json/status/<job_id>` | GET | Admin Système | ✅ | ❌ | ❌ |
| Page pending import | `/admin/textes/import_json/pending/<job_id>` | GET | Admin Système | ✅ | ❌ | ❌ |
| Télécharger template JSON | `/admin/textes/import_json/template` | GET | Admin Système | ✅ | ❌ | ❌ |

### 5.6 Sources de veille réglementaire

**Blueprint** : `veille` — **URL** : `/admin/veille/`

> Réservé Admin Système (`@system_admin_required`)

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Dashboard veille | `/admin/veille/` | GET | `textes.voir` | ✅ | ❌ | ❌ |
| Détail veille | `/admin/veille/<id>` | GET | `textes.voir` | ✅ | ❌ | ❌ |
| API liste veilles | `/admin/veille/api/liste` | GET | `textes.voir` | ✅ | ❌ | ❌ |
| API créer veille | `/admin/veille/api/create` | POST | `textes.modifier` | ✅ | ❌ | ❌ |
| API modifier veille | `/admin/veille/api/<id>/update` | POST | `textes.modifier` | ✅ | ❌ | ❌ |
| API supprimer veille | `/admin/veille/api/<id>/delete` | POST | `textes.modifier` | ✅ | ❌ | ❌ |
| API liste sources | `/admin/veille/api/sources` | GET | `textes.voir` | ✅ | ❌ | ❌ |
| API créer source | `/admin/veille/api/source/create` | POST | `textes.modifier` | ✅ | ❌ | ❌ |
| API supprimer source | `/admin/veille/api/source/<id>/delete` | POST | `textes.modifier` | ✅ | ❌ | ❌ |

---

## 6. Conformité réglementaire

**Blueprint** : `conformite` — **URL** : `/conformite/`

### 6.1 Textes attribués à l'entreprise

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste textes attribués | `/conformite/` | GET | `conformite.voir` | ✅ | ✅ | ✅ |
| Attribuer un texte | `/conformite/attribuer` | POST | `conformite.modifier` | ✅ | ✅ | ❌ |
| Mettre à jour attribut | `/conformite/<id>/update` | POST | `conformite.modifier` | ✅ | ✅ | ❌ |
| Supprimer attribut | `/conformite/<id>/delete` | POST | `conformite.modifier` | ✅ | ✅ | ❌ |
| API liste | `/conformite/api/liste` | GET | `conformite.voir` | ✅ | ✅ | ✅ |
| Recherche conformité | `/conformite/search` | GET | `conformite.voir` | ✅ | ✅ | ✅ |

### 6.2 Évaluations de conformité

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Détail évaluation | `/conformite/evaluation/<id>` | GET/POST | `conformite.voir` | ✅ | ✅ | ✅ |
| Ajouter action depuis évaluation | `/conformite/evaluation/<id>/action/add` | POST | `conformite.modifier` | ✅ | ✅ | ❌ |
| Liste actions d'une évaluation | `/conformite/evaluation/<id>/actions` | GET | `conformite.voir` | ✅ | ✅ | ✅ |
| Attacher preuve | `/conformite/evaluation/<id>/proof/attach` | POST | `conformite.modifier` | ✅ | ✅ | ❌ |
| Liste preuves | `/conformite/evaluation/<id>/proof/liste` | GET | `conformite.voir` | ✅ | ✅ | ✅ |
| Détacher preuve | `/conformite/evaluation/<id>/proof/<id>/detach` | POST | `conformite.modifier` | ✅ | ✅ | ❌ |

### 6.3 Non-conformités HSE

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste non-conformités | `/conformite/nonconformites` | GET | `conformite.voir` | ✅ | ✅ | ✅ |
| API non-conformités | `/conformite/api/nonconformites` | GET | `conformite.voir` | ✅ | ✅ | ✅ |

### 6.4 Preuves de conformité

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Gestion des preuves | `/conformite/preuves/gestion` | GET | `conformite.voir` | ✅ | ✅ | ✅ |
| Mettre à jour preuve | `/conformite/preuves/<id>/mettre_a_jour` | POST | `documents.upload` | ✅ | ✅ | ❌ |
| Archiver preuve | `/conformite/preuves/<id>/archiver` | POST | `documents.archiver` | ✅ | ✅ | ❌ |
| Supprimer preuve | `/conformite/preuves/<id>/supprimer` | POST | `documents.archiver` | ✅ | ✅ | ❌ |

---

## 7. Actions Correctives

**Blueprint** : `actions` — **URL** : `/actions/`

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste des actions | `/actions/` | GET | `actions.voir` | ✅ | ✅ | ✅ |
| Détail / Modifier une action | `/actions/<id>` | GET/POST | `actions.modifier` | ✅ | ✅ | ✅ (si assigné) |
| Créer une action (API) | `/actions/api/create` | POST | `actions.cree` | ✅ | ✅ | ❌ |
| API liste actions | `/actions/api/liste` | GET | `actions.voir` | ✅ | ✅ | ✅ |
| Modifier une action (API) | `/actions/<id>/api/update` | POST | `actions.modifier` | ✅ | ✅ | ✅ (si assigné) |
| Changer statut | `/actions/<id>/status` | POST | `actions.modifier` | ✅ | ✅ | ✅ (si assigné) |
| Attacher preuve | `/actions/<id>/proof/attach` | POST | `actions.modifier` | ✅ | ✅ | ✅ (si assigné) |
| Détacher preuve | `/actions/<id>/proof/detach/<ref_id>` | POST | `actions.modifier` | ✅ | ✅ | ❌ |
| Liste preuves | `/actions/<id>/proof/liste` | GET | `actions.modifier` | ✅ | ✅ | ✅ (si assigné) |
| Supprimer action | `/actions/<id>/delete` | POST | `actions.supprimer` | ✅ | ✅ | ❌ |
| Export CSV | `/actions/api/export` | GET | `actions.voir` | ✅ | ✅ | ✅ |

---

## 8. Audits

**Blueprint** : `audit` — **URL** : `/audit/`

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste des audits | `/audit/` | GET | `audit.voir` | ✅ | ✅ | ✅ |
| Détail audit | `/audit/<id>` | GET | `audit.voir` | ✅ | ✅ | ✅ |
| Créer un audit (API) | `/audit/creer` | POST | `audit.modifier` | ✅ | ✅ | ❌ |
| API liste audits | `/audit/api/liste` | GET | `audit.voir` | ✅ | ✅ | ✅ |
| Modifier un audit | `/audit/<id>/update` | POST | `audit.modifier` | ✅ | ✅ | ❌ |
| Supprimer un audit | `/audit/<id>/delete` | POST | `audit.modifier` | ✅ | ✅ | ❌ |
| Ajouter observation | `/audit/<id>/observation/add` | POST | `audit.modifier` | ✅ | ✅ | ❌ |
| Supprimer observation | `/audit/<id>/observation/<obs_id>/delete` | POST | `audit.modifier` | ✅ | ✅ | ❌ |
| Export CSV | `/audit/api/export` | GET | `audit.voir` | ✅ | ✅ | ✅ |

---

## 9. GED & Documents

**Blueprint** : `documents` — **URL** : `/documents/`

> Le module GED doit être activé dans `modules_actifs` de l'entreprise

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Dashboard GED | `/documents/` | GET | `documents.voir` | ✅ | ✅ | ✅ |
| Upload document | `/documents/upload` | POST | `documents.upload` | ✅ | ✅ | ❌ |
| Détail document | `/documents/<id>/detail` | GET | `documents.voir` | ✅ | ✅ | ✅ |
| Télécharger document | `/documents/<id>/download` | GET | `documents.voir` | ✅ | ✅ | ✅ |
| Mettre à jour métadonnées | `/documents/<id>/mettre_a_jour` | POST | `documents.upload` | ✅ | ✅ | ❌ |
| Nouvelle version | `/documents/<id>/nouvelle-version` | POST | `documents.upload` | ✅ | ✅ | ❌ |
| Soumettre pour approbation | `/documents/<id>/soumettre` | POST | `documents.workflow` | ✅ | ✅ | ❌ |
| Approuver document | `/documents/<id>/approuver` | POST | `documents.workflow` | ✅ | ✅ (si approbateur) | ❌ |
| Rejeter document | `/documents/<id>/rejeter` | POST | `documents.workflow` | ✅ | ✅ (si approbateur) | ❌ |
| Demander révision | `/documents/<id>/demander-revision` | POST | `documents.workflow` | ✅ | ✅ | ❌ |
| Archiver document | `/documents/<id>/archiver` | POST | `documents.archiver` | ✅ | ✅ | ❌ |
| Restaurer document | `/documents/<id>/restaurer` | POST | `documents.archiver` | ✅ | ✅ | ❌ |
| Supprimer document | `/documents/<id>/supprimer` | POST | `documents.archiver` | ✅ | ✅ | ❌ |
| API liste documents | `/documents/api/liste` | GET | `documents.voir` | ✅ | ✅ | ✅ |
| API recherche avancée | `/documents/api/recherche` | GET | `documents.voir` | ✅ | ✅ | ✅ |
| API documents actifs | `/documents/api/actives` | GET | `documents.voir` | ✅ | ✅ | ✅ |

### Gestion des dossiers

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Arborescence dossiers | `/documents/api/dossiers` | GET | `documents.voir` | ✅ | ✅ | ✅ |
| Créer dossier | `/documents/api/dossiers/create` | POST | `documents.upload` | ✅ | ✅ | ❌ |
| Renommer dossier | `/documents/api/dossiers/<id>/rename` | POST | `documents.upload` | ✅ | ✅ | ❌ |
| Déplacer dossier | `/documents/api/dossiers/<id>/move` | POST | `documents.upload` | ✅ | ✅ | ❌ |
| Supprimer dossier | `/documents/api/dossiers/<id>/delete` | POST | `documents.archiver` | ✅ | ✅ | ❌ |

### Types de documents

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| API types | `/documents/api/types` | GET | `documents.voir` | ✅ | ✅ | ✅ |
| Créer type | `/documents/api/types/create` | POST | `documents.upload` | ✅ | ✅ | ❌ |
| Modifier type | `/documents/api/types/<id>/update` | POST | `documents.upload` | ✅ | ✅ | ❌ |
| Supprimer type | `/documents/api/types/<id>/delete` | POST | `documents.archiver` | ✅ | ✅ | ❌ |

---

## 10. Non-Conformités & CAPA

**Blueprint** : `nonconformites` — **URL** : `/nonconformites/`

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste non-conformités | `/nonconformites/` | GET | `nonconformites.voir` | ✅ | ✅ | ✅ |
| API CRUD (liste, créer, modifier, supprimer) | `/nonconformites/api/*` | GET/POST | `nonconformites.voir` / `nonconformites.gerer` | ✅ | ✅ | ✅ (selon perm) |
| Valider clôture | `/nonconformites/api/<id>/valider-cloture` | POST | `nonconformites.valider_cloture` | ✅ | ✅ | ❌ |
| Statistiques | `/nonconformites/api/stats` | GET | `nonconformites.voir` | ✅ | ✅ | ✅ |

---

## 11. Indicateurs & Objectifs

### 11.1 Indicateurs

**Blueprint** : `indicateurs` — **URL** : `/indicateurs/`

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste indicateurs | `/indicateurs/` | GET | `indicateurs.voir` | ✅ | ✅ | ✅ |
| Détail indicateur | `/indicateurs/<id>` | GET | `indicateurs.voir` | ✅ | ✅ | ✅ |
| API liste | `/indicateurs/api/liste` | GET | `indicateurs.voir` | ✅ | ✅ | ✅ |
| Créer indicateur | `/indicateurs/api/create` | POST | `indicateurs.cree` | ✅ | ✅ | ❌ |
| Modifier indicateur | `/indicateurs/api/update/<id>` | POST | `indicateurs.modifier` | ✅ | ✅ | ❌ |
| Supprimer indicateur | `/indicateurs/api/delete/<id>` | POST | `indicateurs.modifier` | ✅ | ✅ | ❌ |
| Ajouter valeur | `/indicateurs/api/valeur/add` | POST | `indicateurs.modifier` | ✅ | ✅ | ❌ |

### 11.2 Objectifs qualité

**Blueprint** : `objectifs` — **URL** : `/objectifs/`

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste objectifs | `/objectifs/` | GET | `indicateurs.voir` | ✅ | ✅ | ✅ |
| API CRUD | `/objectifs/api/*` | GET/POST | `indicateurs.voir` / `indicateurs.cree` | ✅ | ✅ | ✅ (selon perm) |
| Statistiques | `/objectifs/api/stats` | GET | `indicateurs.voir` | ✅ | ✅ | ✅ |

---

## 12. Formations & Compétences

**Blueprint** : `formations` — **URL** : `/formations/`

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste formations | `/formations/` | GET | `formations.voir` | ✅ | ✅ | ✅ |
| Participants | `/formations/participants` | GET | `formations.voir` | ✅ | ✅ | ✅ |
| Matrice compétences | `/formations/matrice` | GET | `formations.voir` | ✅ | ✅ | ✅ |
| Certifications | `/formations/certifications` | GET | `formations.voir` | ✅ | ✅ | ✅ |
| API CRUD formations | `/formations/api/*` | GET/POST | `formations.voir` / `formations.gerer` | ✅ | ✅ | ✅ (selon perm) |
| API compétences | `/formations/api/competences` | GET | `formations.voir` | ✅ | ✅ | ✅ |
| Créer compétence | `/formations/api/competences/create` | POST | `formations.gerer` | ✅ | ✅ | ❌ |
| Supprimer compétence | `/formations/api/competences/<id>/delete` | POST | `formations.gerer` | ✅ | ✅ | ❌ |
| API certifications | `/formations/api/certifications` | GET | `formations.voir` | ✅ | ✅ | ✅ |
| API calendrier | `/formations/api/calendrier` | GET | `formations.voir` | ✅ | ✅ | ✅ |
| API stats | `/formations/api/stats` | GET | `formations.voir` | ✅ | ✅ | ✅ |
| API participants | `/formations/api/participants/<id>` | GET | `formations.voir` | ✅ | ✅ | ✅ |
| Créer participant | `/formations/api/participants/create` | POST | `formations.gerer` | ✅ | ✅ | ❌ |
| Modifier participant | `/formations/api/participants/<id>/update` | POST | `formations.gerer` | ✅ | ✅ | ❌ |
| Supprimer participant | `/formations/api/participants/<id>/delete` | POST | `formations.gerer` | ✅ | ✅ | ❌ |
| Matrice compétences (API) | `/formations/api/matrice` | GET | `formations.voir` | ✅ | ✅ | ✅ |
| Évaluer compétence | `/formations/api/matrice/create` | POST | `formations.gerer` | ✅ | ✅ | ❌ |
| Modifier évaluation | `/formations/api/matrice/<id>/update` | POST | `formations.gerer` | ✅ | ✅ | ❌ |
| Supprimer évaluation | `/formations/api/matrice/<id>/delete` | POST | `formations.gerer` | ✅ | ✅ | ❌ |

---

## 13. Fournisseurs

**Blueprint** : `fournisseurs` — **URL** : `/fournisseurs/`

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste fournisseurs | `/fournisseurs/` | GET | `fournisseurs.voir` | ✅ | ✅ | ✅ |
| API CRUD | `/fournisseurs/api/*` | GET/POST | `fournisseurs.voir` / `fournisseurs.gerer` | ✅ | ✅ | ✅ (selon perm) |
| Statistiques | `/fournisseurs/api/stats` | GET | `fournisseurs.voir` | ✅ | ✅ | ✅ |
| Évaluer fournisseur | `/fournisseurs/api/<id>/evaluer` | POST | `fournisseurs.gerer` | ✅ | ✅ | ❌ |

---

## 14. Réclamations clients

**Blueprint** : `reclamations` — **URL** : `/reclamations/`

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste réclamations | `/reclamations/` | GET | `reclamations.voir` | ✅ | ✅ | ✅ |
| API CRUD | `/reclamations/api/*` | GET/POST | `reclamations.voir` / `reclamations.gerer` | ✅ | ✅ | ✅ (selon perm) |
| Statistiques | `/reclamations/api/stats` | GET | `reclamations.voir` | ✅ | ✅ | ✅ |
| Analyse Pareto | `/reclamations/api/pareto` | GET | `reclamations.voir` | ✅ | ✅ | ✅ |

---

## 15. Ishikawa (Analyse causes)

**Blueprint** : `ishikawa` — **URL** : `/ishikawa/`

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste analyses | `/ishikawa/` | GET | `ishikawa.voir` | ✅ | ✅ | ✅ |
| API liste | `/ishikawa/api/liste` | GET | `ishikawa.voir` | ✅ | ✅ | ✅ |
| Créer analyse | `/ishikawa/api/creer` | POST | `ishikawa.gerer` | ✅ | ✅ | ❌ |
| Modifier analyse | `/ishikawa/api/<id>/modifier` | POST | `ishikawa.gerer` | ✅ | ✅ | ❌ |
| Supprimer analyse | `/ishikawa/api/<id>/supprimer` | POST | `ishikawa.gerer` | ✅ | ✅ | ❌ |

---

## 16. HSE — Incidents, EPI, Inspections, Permis

**Blueprint** : `hse` — **URL** : `/hse/`

### 16.1 Incidents

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Dashboard HSE | `/hse/` | GET | `hse.voir_incidents` | ✅ | ✅ | ✅ |
| Liste incidents | `/hse/incidents` | GET | `hse.voir_incidents` | ✅ | ✅ | ✅ |
| API liste | `/hse/api/incidents` | GET | `hse.voir_incidents` | ✅ | ✅ | ✅ |
| Créer incident | `/hse/api/incidents/create` | POST | `hse.voir_incidents` | ✅ | ✅ | ✅ |
| Modifier incident | `/hse/api/incidents/<id>/update` | POST | `hse.voir_incidents` | ✅ | ✅ | ✅ |
| Supprimer incident | `/hse/api/incidents/<id>/delete` | POST | `hse.voir_incidents` | ✅ | ✅ | ❌ |
| Arbre des causes | `/hse/incidents/<id>/causes` | GET | `hse.voir_incidents` | ✅ | ✅ | ✅ |
| API causes | `/hse/api/incidents/<id>/causes` | GET | `hse.voir_incidents` | ✅ | ✅ | ✅ |
| Créer cause | `/hse/api/incidents/<id>/causes/create` | POST | `hse.gerer_incidents` | ✅ | ✅ | ❌ |
| Modifier cause | `/hse/api/causes/<id>/update` | POST | `hse.gerer_incidents` | ✅ | ✅ | ❌ |
| Supprimer cause | `/hse/api/causes/<id>/delete` | POST | `hse.gerer_incidents` | ✅ | ✅ | ❌ |

### 16.2 EPI (Équipements de Protection Individuelle)

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste EPI | `/hse/epi` | GET | `hse.voir_incidents` | ✅ | ✅ | ✅ |
| API CRUD EPI | `/hse/api/epi/*` | GET/POST | `hse.voir_incidents` | ✅ | ✅ | ✅ |

### 16.3 Inspections

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste inspections | `/hse/inspections` | GET | `hse.voir_incidents` | ✅ | ✅ | ✅ |
| API CRUD inspections | `/hse/api/inspections/*` | GET/POST | `hse.voir_incidents` | ✅ | ✅ | ✅ |

### 16.4 Permis de travail

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste permis | `/hse/permis-travail` | GET | `hse.voir_incidents` | ✅ | ✅ | ✅ |
| API CRUD permis | `/hse/api/permis-travail/*` | GET/POST | `hse.voir_incidents` | ✅ | ✅ | ✅ |

### 16.5 Statistiques HSE

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Stats HSE | `/hse/api/stats` | GET | `hse.voir_incidents` | ✅ | ✅ | ✅ |

---

## 17. HSE — DUER & Dangers SST

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Page DUER | `/hse/duer` | GET | `hse.voir_duer` | ✅ | ✅ | ✅ |
| API unités de travail | `/hse/api/unites-travail` | GET | `hse.voir_duer` | ✅ | ✅ | ✅ |
| Créer unité de travail | `/hse/api/unites-travail/create` | POST | `hse.gerer_duer` | ✅ | ✅ | ❌ |
| Modifier unité | `/hse/api/unites-travail/<id>/update` | POST | `hse.gerer_duer` | ✅ | ✅ | ❌ |
| Supprimer unité | `/hse/api/unites-travail/<id>/delete` | POST | `hse.gerer_duer` | ✅ | ✅ | ❌ |
| API dangers SST | `/hse/api/dangers-sst` | GET | `hse.voir_duer` | ✅ | ✅ | ✅ |
| Créer danger | `/hse/api/dangers-sst/create` | POST | `hse.gerer_duer` | ✅ | ✅ | ❌ |
| Modifier danger | `/hse/api/dangers-sst/<id>/update` | POST | `hse.gerer_duer` | ✅ | ✅ | ❌ |
| Supprimer danger | `/hse/api/dangers-sst/<id>/delete` | POST | `hse.gerer_duer` | ✅ | ✅ | ❌ |
| API évaluations risques | `/hse/api/evaluations-risques` | GET | `hse.voir_duer` | ✅ | ✅ | ✅ |
| Créer évaluation risque | `/hse/api/evaluations-risques/create` | POST | `hse.gerer_duer` | ✅ | ✅ | ❌ |
| Modifier évaluation | `/hse/api/evaluations-risques/<id>/update` | POST | `hse.gerer_duer` | ✅ | ✅ | ❌ |
| Supprimer évaluation | `/hse/api/evaluations-risques/<id>/delete` | POST | `hse.gerer_duer` | ✅ | ✅ | ❌ |
| Stats DUER | `/hse/api/duer/stats` | GET | `hse.voir_duer` | ✅ | ✅ | ✅ |

---

## 18. HACCP & Sécurité Alimentaire

**Blueprint** : `haccp` — **URL** : `/haccp/`

> Module HACCP autonome. Les opérations CRUD utilisent `auto_register_crud` avec permissions `haccp.voir` (lecture) et `haccp.gerer_*` (écriture granulaire par entité).

### Entités et permissions

| Entité | Permission lecture | Permission écriture | Admin | Manager | User |
|--------|-------------------|---------------------|-------|---------|------|
| Processus HACCP | `haccp.voir` | `haccp.gerer_processus` | ✅ | ✅ | ✅ (selon perm) |
| Produits | `haccp.voir` | `haccp.gerer_produits` | ✅ | ✅ | ✅ (selon perm) |
| Analyse dangers | `haccp.voir` | `haccp.gerer_dangers` | ✅ | ✅ | ✅ (selon perm) |
| CCP (Points Critiques) | `haccp.voir` | `haccp.gerer_ccp` | ✅ | ✅ | ✅ (selon perm) |
| Enregistrements CCP | `haccp.voir` | `haccp.gerer_enregistrements` | ✅ | ✅ | ✅ (selon perm) |
| PRP (Programmes Prérequis) | `haccp.voir` | `haccp.gerer_prp` | ✅ | ✅ | ✅ (selon perm) |
| OPRP | `haccp.voir` | `haccp.gerer_prp` | ✅ | ✅ | ✅ (selon perm) |
| Enregistrements OPRP | `haccp.voir` | `haccp.gerer_enregistrements` | ✅ | ✅ | ✅ (selon perm) |
| Traçabilité lots | `haccp.voir` | `haccp.gerer_tracabilite` | ✅ | ✅ | ✅ (selon perm) |
| Rappels produits | `haccp.voir` | `haccp.gerer_rappels` | ✅ | ✅ | ✅ (selon perm) |

### Pages HACCP

| Fonctionnalité | Route | Template | Admin | Manager | User |
|----------------|-------|----------|-------|---------|------|
| Tableau de bord | `/haccp/` | `haccp/tableau_de_bord.html` | ✅ | ✅ | ✅ |
| Processus | `/haccp/processus` | `haccp/processus.html` | ✅ | ✅ | ✅ |
| Produits | `/haccp/produits` | `haccp/produits.html` | ✅ | ✅ | ✅ |
| Analyse dangers | `/haccp/dangers` | `haccp/dangers.html` | ✅ | ✅ | ✅ |
| CCP | `/haccp/ccp` | `haccp/ccp.html` | ✅ | ✅ | ✅ |
| Enregistrements CCP | `/haccp/enregistrements` | `haccp/enregistrements.html` | ✅ | ✅ | ✅ |
| PRP | `/haccp/prp` | `haccp/prp.html` | ✅ | ✅ | ✅ |
| OPRP | `/haccp/oprp` | `haccp/oprp.html` | ✅ | ✅ | ✅ |
| Enregistrements OPRP | `/haccp/enregistrements-oprp` | `haccp/enregistrements_oprp.html` | ✅ | ✅ | ✅ |
| Traçabilité | `/haccp/tracabilite` | `haccp/tracabilite.html` | ✅ | ✅ | ✅ |
| Rappels produits | `/haccp/rappels` | `haccp/rappels.html` | ✅ | ✅ | ✅ |

### API HACCP

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Stats HACCP | `/haccp/api/stats` | GET | `haccp.voir` | ✅ | ✅ | ✅ |
| CRUD pour chaque entité | `/haccp/api/<entité>/*` | GET/POST | `haccp.voir` / `haccp.gerer_*` | ✅ | ✅ | ✅ (selon perm) |

---

## 19. Processus & BPMN

**Blueprint** : `processus` — **URL** : `/processus/`

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste processus | `/processus/` | GET | `processus.voir` | ✅ | ✅ | ✅ |
| API CRUD processus | `/processus/api/*` | GET/POST | `processus.voir` / `processus.gerer` | ✅ | ✅ | ✅ (selon perm) |
| Statistiques | `/processus/api/stats` | GET | `processus.voir` | ✅ | ✅ | ✅ |
| Éditeur BPMN | `/processus/<id>/bpmn` | GET | `processus.voir` | ✅ | ✅ | ✅ |
| API get BPMN XML | `/processus/api/<id>/bpmn` | GET | `processus.voir` | ✅ | ✅ | ✅ |
| API sauvegarder BPMN | `/processus/api/<id>/bpmn` | POST | `processus.gerer` | ✅ | ✅ | ❌ |
| API générer BPMN | `/processus/api/<id>/bpmn/generate` | POST | `processus.gerer` | ✅ | ✅ | ❌ |
| API importer BPMN | `/processus/api/<id>/bpmn/import` | POST | `processus.gerer` | ✅ | ✅ | ❌ |

---

## 20. Change Management

**Blueprint** : `change_management` — **URL** : `/change-management/`

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste demandes | `/change-management/` | GET | `change_management.voir` | ✅ | ✅ | ✅ |
| API liste | `/change-management/api/liste` | GET | `change_management.voir` | ✅ | ✅ | ✅ |
| API stats | `/change-management/api/stats` | GET | `change_management.voir` | ✅ | ✅ | ✅ |
| Créer demande | `/change-management/api/creer` | POST | `change_management.gerer` | ✅ | ✅ | ❌ |
| Modifier demande | `/change-management/api/<id>/modifier` | POST | `change_management.gerer` | ✅ | ✅ | ❌ |
| Supprimer demande | `/change-management/api/<id>/supprimer` | POST | `change_management.gerer` | ✅ | ✅ | ❌ |

---

## 21. Workflow Engine

**Blueprint** : `workflow_engine` — **URL** : `/workflow-engine/`

### Modèles de workflow

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Page principale | `/workflow-engine/` | GET | `workflow_engine.voir` | ✅ | ✅ | ✅ |
| API liste modèles | `/workflow-engine/api/modeles` | GET | `workflow_engine.voir` | ✅ | ✅ | ✅ |
| API détail modèle | `/workflow-engine/api/modeles/<id>` | GET | `workflow_engine.voir` | ✅ | ✅ | ✅ |
| Créer modèle | `/workflow-engine/api/modeles/creer` | POST | `workflow_engine.gerer` | ✅ | ✅ | ❌ |
| Supprimer modèle | `/workflow-engine/api/modeles/<id>/supprimer` | POST | `workflow_engine.gerer` | ✅ | ✅ | ❌ |

### Instances de workflow

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| API liste instances | `/workflow-engine/api/instances` | GET | `workflow_engine.voir` | ✅ | ✅ | ✅ |
| API détail instance | `/workflow-engine/api/instances/<id>` | GET | `workflow_engine.voir` | ✅ | ✅ | ✅ |
| Créer instance | `/workflow-engine/api/instances/creer` | POST | `workflow_engine.gerer` | ✅ | ✅ | ❌ |
| Valider étape | `/workflow-engine/api/instances/<id>/valider` | POST | `workflow_engine.gerer` | ✅ | ✅ | ✅ (si validateur) |
| Rejeter étape | `/workflow-engine/api/instances/<id>/rejeter` | POST | `workflow_engine.gerer` | ✅ | ✅ | ✅ (si validateur) |
| Annuler instance | `/workflow-engine/api/instances/<id>/annuler` | POST | `workflow_engine.gerer` | ✅ | ✅ | ❌ |
| Stats | `/workflow-engine/api/stats` | GET | `workflow_engine.voir` | ✅ | ✅ | ✅ |
| Instances en retard | `/workflow-engine/api/retard` | GET | `workflow_engine.voir` | ✅ | ✅ | ✅ |

---

## 22. Facturation & Abonnements

**Blueprint** : `facturation` — **URL** : `/facturation/`

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Page facturation | `/facturation/` | GET | `facturation.voir` | ✅ | ✅ | ❌ |
| API infos entreprise | `/facturation/api/infos` | GET | `facturation.voir` | ✅ | ✅ | ❌ |
| API historique paiements | `/facturation/api/paiements` | GET | `facturation.voir` | ✅ | ✅ | ❌ |
| Enregistrer paiement | `/facturation/api/paiements/create` | POST | `facturation.gerer` | ✅ | ✅ | ❌ |
| Mettre à jour infos facturation | `/facturation/api/update` | POST | `facturation.gerer` | ✅ | ✅ | ❌ |

---

## 23. Secteurs

**Blueprint** : `secteur` — **URL** : `/secteur/`

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste secteurs | `/secteur/` | GET | `secteur.voir` | ✅ | ✅ | ✅ |
| Détail secteur | `/secteur/<id>` | GET | `secteur.voir` | ✅ | ✅ | ✅ |
| Admin textes-secteurs | `/secteur/admin/textes` | GET | `secteur.gerer_textes` | ✅ | ❌ | ❌ |
| Éditer textes d'un secteur | `/secteur/admin/textes/<id>/edit_secteurs` | GET | `secteur.gerer_textes` | ✅ | ❌ | ❌ |
| Définir secteurs d'un texte | `/secteur/admin/textes/<id>/set_secteurs` | POST | `secteur.gerer_textes` | ✅ | ❌ | ❌ |
| Créer secteur | `/secteur/create` | GET/POST | `secteur.cree` | ✅ | ✅ | ❌ |
| Modifier secteur | `/secteur/<id>/edit` | GET/POST | `secteur.modifier` | ✅ | ✅ | ❌ |
| Supprimer secteur | `/secteur/<id>/delete` | POST | `secteur.modifier` | ✅ | ✅ | ❌ |
| Supprimer tous les secteurs | `/secteur/delete_all` | POST | `secteur.modifier` | ✅ | ✅ | ❌ |

---

## 24. Entreprises

**Blueprint** : `entreprises` — **URL** : `/entreprises/`

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Liste entreprises | `/entreprises/` | GET | Authentifié | ✅ | ✅ | ✅ |
| Créer entreprise | `/entreprises/create` | GET/POST | `entreprises.cree` | ✅ | ❌ | ❌ |
| Éditer entreprise | `/entreprises/<id>/edit` | GET/POST | Authentifié | ✅ | ✅ (la sienne) | ❌ |
| Renvoyer email bienvenue | `/entreprises/<id>/resend-welcome-email` | POST | `entreprises.modifier` | ✅ | ✅ | ❌ |
| API liste | `/entreprises/api/liste` | GET | Authentifié | ✅ | ✅ | ✅ |
| API détail | `/entreprises/api/<id>/detail` | GET | Authentifié | ✅ | ✅ | ✅ |
| API modifier | `/entreprises/api/<id>/update` | POST | `entreprises.modifier` | ✅ | ✅ | ❌ |
| API supprimer | `/entreprises/api/<id>/delete` | POST | `entreprises.supprimer` | ✅ | ❌ | ❌ |
| Mon entreprise (management) | `/entreprises/mon-entreprise` | GET | `entreprises.modifier` | ✅ | ✅ | ❌ |

---

## 25. Support (Tickets)

**Blueprint** : `support` — **URL** : `/support/`

### Côté utilisateur

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Mes tickets | `/support/` | GET | `support.voir` | ✅ | ✅ | ✅ |
| Créer un ticket | `/support/creer` | GET/POST | `support.cree` | ✅ | ✅ | ✅ |
| Détail ticket | `/support/<id>` | GET | `support.voir` | ✅ | ✅ | ✅ |
| Ajouter message | `/support/<id>/message` | POST | `support.voir` | ✅ | ✅ | ✅ |
| Fermer ticket | `/support/<id>/fermer` | POST | `support.fermer` | ✅ | ✅ | ✅ (si créateur) |
| API liste tickets | `/support/api/liste` | GET | `support.voir` | ✅ | ✅ | ✅ |

### Côté admin (voir section 4)

---

## 26. Notifications

Les notifications sont gérées via plusieurs mécanismes :

| Fonctionnalité | Route | Méthode | Rôle requis |
|----------------|-------|---------|-------------|
| Préférences de notification | `/users/notifications/preferences` | GET/POST | Authentifié |
| Bell notifications (API) | `/main/api/notifications` | GET | Authentifié |
| Compteur non lues | `/main/api/notifications/unread-count` | GET | Authentifié |
| Marquer lue | `/main/api/notifications/<id>/read` | POST | Authentifié |
| Marquer toutes lues | `/main/api/notifications/read-all` | POST | Authentifié |
| Page notifications | `/main/notifications` | GET | Authentifié |
| Ouvrir notification | `/main/notifications/<id>/open` | GET | Authentifié |
| Admin notifications | `/admin/notifications` | GET | Admin Système |
| Envoyer notification | `/admin/notifications/send` | POST | Admin Système |
| Déclencher alertes manuellement | `/main/api/alerts/trigger` | POST | Admin Système |

---

## 27. Modules avancés

Ces modules utilisent le pattern `auto_register_crud` avec les permissions `{module}.voir` (lecture) et `{module}.gerer` (écriture).

### 27.1 Environnement (ISO 14001)

**Blueprint** : `environnement` — **URL** : `/environnement/`

| Fonctionnalité | Route | Permission | Admin | Manager | User |
|----------------|-------|------------|-------|---------|------|
| Page principale | `/environnement/` | `environnement.voir` | ✅ | ✅ | ✅ |
| API CRUD aspects | `/environnement/api/*` | `environnement.voir` / `environnement.gerer` | ✅ | ✅ | ✅ (selon perm) |
| Stats | `/environnement/api/stats` | `environnement.voir` | ✅ | ✅ | ✅ |

### 27.2 Maintenance

**Blueprint** : `maintenance` — **URL** : `/maintenance/`

| Fonctionnalité | Route | Permission | Admin | Manager | User |
|----------------|-------|------------|-------|---------|------|
| Page principale | `/maintenance/` | `maintenance.voir` | ✅ | ✅ | ✅ |
| API CRUD équipements/interventions | `/maintenance/api/*` | `maintenance.voir` / `maintenance.gerer` | ✅ | ✅ | ✅ (selon perm) |
| Stats | `/maintenance/api/stats` | `maintenance.voir` | ✅ | ✅ | ✅ |

### 27.3 Laboratoire

**Blueprint** : `laboratoire` — **URL** : `/laboratoire/`

| Fonctionnalité | Route | Permission | Admin | Manager | User |
|----------------|-------|------------|-------|---------|------|
| Page principale | `/laboratoire/` | `laboratoire.voir` | ✅ | ✅ | ✅ |
| API CRUD plans/échantillons/résultats | `/laboratoire/api/*` | `laboratoire.voir` / `laboratoire.gerer` | ✅ | ✅ | ✅ (selon perm) |
| Stats | `/laboratoire/api/stats` | `laboratoire.voir` | ✅ | ✅ | ✅ |

### 27.4 Planification

**Blueprint** : `planification` — **URL** : `/planification/`

| Fonctionnalité | Route | Permission | Admin | Manager | User |
|----------------|-------|------------|-------|---------|------|
| Page principale | `/planification/` | `planification.voir` | ✅ | ✅ | ✅ |
| API CRUD événements | `/planification/api/*` | `planification.voir` / `planification.gerer` | ✅ | ✅ | ✅ (selon perm) |
| Calendrier | `/planification/api/calendrier` | `planification.voir` | ✅ | ✅ | ✅ |
| Stats | `/planification/api/stats` | `planification.voir` | ✅ | ✅ | ✅ |

### 27.5 Réunions

**Blueprint** : `reunions` — **URL** : `/reunions/`

| Fonctionnalité | Route | Permission | Admin | Manager | User |
|----------------|-------|------------|-------|---------|------|
| Page principale | `/reunions/` | `reunions.voir` | ✅ | ✅ | ✅ |
| API CRUD réunions/actions | `/reunions/api/*` | `reunions.voir` / `reunions.gerer` | ✅ | ✅ | ✅ (selon perm) |
| Stats | `/reunions/api/stats` | `reunions.voir` | ✅ | ✅ | ✅ |

### 27.6 RH QHSE

**Blueprint** : `rh_qhse` — **URL** : `/rh-qhse/`

| Fonctionnalité | Route | Permission | Admin | Manager | User |
|----------------|-------|------------|-------|---------|------|
| Page principale | `/rh-qhse/` | `rh.voir` | ✅ | ✅ | ✅ |
| API CRUD employés | `/rh-qhse/api/*` | `rh.voir` / `rh.gerer` | ✅ | ✅ | ✅ (selon perm) |
| Stats | `/rh-qhse/api/stats` | `rh.voir` | ✅ | ✅ | ✅ |

### 27.7 Connaissances (REX & FAQ)

**Blueprint** : `connaissances` — **URL** : `/connaissances/`

| Fonctionnalité | Route | Permission | Admin | Manager | User |
|----------------|-------|------------|-------|---------|------|
| Page principale | `/connaissances/` | `connaissances.voir` | ✅ | ✅ | ✅ |
| API CRUD REX | `/connaissances/api/*` | `connaissances.voir` / `connaissances.gerer` | ✅ | ✅ | ✅ (selon perm) |
| Stats | `/connaissances/api/stats` | `connaissances.voir` | ✅ | ✅ | ✅ |

### 27.8 Urgences

**Blueprint** : `urgences` — **URL** : `/urgences/`

| Fonctionnalité | Route | Permission | Admin | Manager | User |
|----------------|-------|------------|-------|---------|------|
| Page principale | `/urgences/` | `urgences.voir` | ✅ | ✅ | ✅ |
| API CRUD plans/exercices/main courante | `/urgences/api/*` | `urgences.voir` / `urgences.gerer` | ✅ | ✅ | ✅ (selon perm) |
| Stats | `/urgences/api/stats` | `urgences.voir` | ✅ | ✅ | ✅ |

### 27.9 Entreprise Textes (Liaison entreprise-texte)

**Blueprint** : `entreprise_textes` — **URL** : `/entreprise-textes/`

| Fonctionnalité | Route | Méthode | Permission | Admin | Manager | User |
|----------------|-------|---------|------------|-------|---------|------|
| Lier texte à entreprise | `/entreprise-textes/link` | POST | `entreprise_textes.lier` | ✅ | ✅ | ❌ |
| Toggle lien (lier/délier) | `/entreprise-textes/toggle_link` | GET/POST | `entreprise_textes.lier` | ✅ | ✅ | ❌ |
| Lancer évaluation | `/entreprise-textes/evaluate` | POST | `conformite.modifier` | ✅ | ✅ | ❌ |

---

## Annexe A : Résumé des permissions par module

| Module | Permission lecture | Permission écriture |
|--------|-------------------|---------------------|
| Actions | `actions.voir` | `actions.cree`, `actions.modifier`, `actions.supprimer` |
| Audit | `audit.voir` | `audit.modifier` |
| Documents (GED) | `documents.voir` | `documents.upload`, `documents.workflow`, `documents.archiver` |
| Indicateurs | `indicateurs.voir` | `indicateurs.cree`, `indicateurs.modifier` |
| Formations | `formations.voir` | `formations.gerer` |
| Fournisseurs | `fournisseurs.voir` | `fournisseurs.gerer` |
| Réclamations | `reclamations.voir` | `reclamations.gerer` |
| Non-conformités | `nonconformites.voir` | `nonconformites.gerer`, `nonconformites.valider_cloture` |
| Ishikawa | `ishikawa.voir` | `ishikawa.gerer` |
| HSE Incidents | `hse.voir_incidents` | `hse.gerer_incidents` |
| HSE DUER | `hse.voir_duer` | `hse.gerer_duer` |
| HACCP | `haccp.voir` | `haccp.gerer_processus`, `haccp.gerer_produits`, `haccp.gerer_dangers`, `haccp.gerer_ccp`, `haccp.gerer_enregistrements`, `haccp.gerer_prp`, `haccp.gerer_tracabilite`, `haccp.gerer_rappels` |
| Conformité | `conformite.voir` | `conformite.modifier` |
| Textes | `textes.voir` | `textes.modifier` (Admin Système uniquement) |
| Secteur | `secteur.voir` | `secteur.cree`, `secteur.modifier`, `secteur.gerer_textes` |
| Processus | `processus.voir` | `processus.gerer` |
| Change Management | `change_management.voir` | `change_management.gerer` |
| Workflow | `workflow_engine.voir` | `workflow_engine.gerer` |
| Utilisateurs | `users.voir` | `users.cree`, `users.modifier` |
| Entreprises | `entreprises.voir` | `entreprises.cree`, `entreprises.modifier`, `entreprises.supprimer` |
| Support | `support.voir` | `support.cree`, `support.fermer` |
| Facturation | `facturation.voir` | `facturation.gerer` |
| Environnement | `environnement.voir` | `environnement.gerer` |
| Maintenance | `maintenance.voir` | `maintenance.gerer` |
| Laboratoire | `laboratoire.voir` | `laboratoire.gerer` |
| Planification | `planification.voir` | `planification.gerer` |
| Réunions | `reunions.voir` | `reunions.gerer` |
| RH QHSE | `rh.voir` | `rh.gerer` |
| Connaissances | `connaissances.voir` | `connaissances.gerer` |
| Urgences | `urgences.voir` | `urgences.gerer` |

## Annexe B : Template mapping

| Module | Templates |
|--------|-----------|
| Textes | `textes/index.html`, `textes/detail.html`, `textes/version_detail.html`, `textes/texte_form.html`, `textes/version_form.html`, `textes/article_form.html`, `textes/article_detail.html`, `textes/library.html`, `textes/veille_dashboard.html`, `textes/veille_preuves.html`, `textes/veille_non_conformites.html`, `textes/import_json.html`, `textes/import_preview.html`, `textes/import_pending.html` |
| Veille | `veille/index.html`, `veille/detail.html` |
| Conformité | `conformite/index.html`, `conformite/evaluation_detail.html`, `conformite/nonconformites.html`, `conformite/search_results.html`, `conformite/preuves_alertes_centre.html` |
| Actions | `actions/liste.html`, `actions/detail.html` |
| Audit | `audit/index.html`, `audit/detail.html` |
| Documents | `documents/gestion.html`, `documents/detail.html` |
| HSE | `hse/tableau_de_bord.html`, `hse/incidents.html`, `hse/epi.html`, `hse/inspections.html`, `hse/permis_travail.html`, `hse/duer.html`, `hse/causes.html` |
| HACCP | `haccp/tableau_de_bord.html`, `haccp/processus.html`, `haccp/produits.html`, `haccp/dangers.html`, `haccp/ccp.html`, `haccp/enregistrements.html`, `haccp/prp.html`, `haccp/oprp.html`, `haccp/enregistrements_oprp.html`, `haccp/tracabilite.html`, `haccp/rappels.html` |
| Indicateurs | `indicateurs/index.html`, `indicateurs/detail.html` |
| Formations | `formations/index.html`, `formations/participants.html`, `formations/matrice.html`, `formations/certifications.html` |
| Fournisseurs | `fournisseurs/index.html` |
| Réclamations | `reclamations/index.html` |
| Ishikawa | `ishikawa/index.html` |
| Non-conformités | `nonconformites/index.html` |
| Processus | `processus/index.html`, `processus/bpmn_editor.html` |
| Change Management | `change_management/index.html` |
| Workflow | `workflow_engine/index.html` |
| Facturation | `facturation/index.html` |
| Support | `support/tickets.html`, `support/ticket_detail.html`, `support/creer_ticket.html` |
| Secteur | `secteur/liste.html`, `secteur/consulter.html`, `secteur/admin_textes.html`, `secteur/_form.html`, `secteur/_manage_secteurs_form.html` |
| Environnement | `environnement/index.html` |
| Maintenance | `maintenance/index.html` |
| Laboratoire | `laboratoire/index.html` |
| Planification | `planification/index.html` |
| Réunions | `reunions/index.html` |
| RH QHSE | `rh_qhse/index.html` |
| Connaissances | `connaissances/index.html` |
| Urgences | `urgences/index.html` |
| Admin | `admin/dashboard.html`, `admin/entreprises.html`, `admin/entreprise_detail.html`, `admin/roles.html`, `admin/role_edit.html`, `admin/permissions.html`, `admin/utilisateurs.html`, `admin/tickets.html`, `admin/ticket_detail.html`, `admin/securite.html`, `admin/notifications.html`, `admin/mail_test.html`, `admin/plans.html`, `admin/services.html`, `admin/backups.html` |

---

## Notes de mise a jour

### 2026-06-24 : Suppression du switch domaine HSE/Qualite

**Contexte** : L'architecture initiale utilisait un switch binaire `domaine_actif = 'hse' | 'qualite'` pour filtrer les donnees. Avec l'architecture multi-modules (23 modules), ce concept est obsolete.

**Changements effectues** :
- Route `/switch-domaine/<domaine>` supprimee
- Variable `domaine_actif` retiree du context processor
- Variable `has_switch` retiree du context processor
- Toutes les routes qui filtraient par `domaine` utilisent maintenant `entreprise_id` (multi-tenant)
- `utils/domaine_switch.py` supprime completement

**Impact** : Aucun — chaque module est independant et scope par `entreprise_id`.
