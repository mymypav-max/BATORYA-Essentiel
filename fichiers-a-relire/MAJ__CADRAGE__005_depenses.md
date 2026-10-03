# BATORYA Essentiel V6 — Cadrage de la tranche 005 « Dépenses »

> **Mise à jour documentaire du 2026-10-03 (en relecture) — ce cadrage est en partie caduc.** Les arbitrages Q1–Q27 (errata E-10 à E-20, invariants INV-179 à INV-196, modèle SQLite V3.13) remplacent les hypothèses suivantes de ce cadrage, qui restent visibles à titre d'historique :
> - **fournisseur archivé non sélectionnable** (règles R6/R7 et §3.1) : **caduc** — plus de statut ni d'archivage des fournisseurs (E-12, INV-183) ;
> - **absence d'annulation d'une dépense** (DDL du §2.1 sans `cancelled_at`/`motif_annulation`, proposition « suppression physique » de la question Q3, INV-181 proposé) : **caduque** — une dépense est corrigeable puis **annulable**, conservée avec son numéro, exclue des totaux concernés, jamais supprimée (E-19, INV-193 ; mécanisme PT-14). La question **Q2 (dépense sur BC annulé)** est tranchée dans le même sens que sa proposition : création et rattachement possibles ;
> - **BC annulé** : une dépense peut être créée sur un BC annulé et y rester liée (D5 de l'audit de conservation, INV-188) ; la règle des 30 jours sur un BC annulé reste une règle de service à confirmer ;
> - **cascades et suppressions** : `ON DELETE` examiné par relation (INV-05) ; aucun objet numéroté supprimé (INV-06) ;
> - la **numérotation de la dépense** suit INV-179 (un numéro n'est jamais attribué deux fois ; un trou est acceptable et jamais récupéré, D-54 ; mécanisme PT-1 non validé).
> Les numéros d'invariants « INV-179 et suivants » proposés au §4.3 sont **déjà attribués** à d'autres règles (INV-179 à INV-196, section N du registre v7) : toute règle nouvelle de Dépenses prendra INV-197 et suivants (INV-196 : révisions de devis). Aucun fichier officiel, aucune migration, aucun test n'a été modifié.

**Statut** : proposition de cadrage, **à valider** avant toute écriture de `005_depenses.sql` et de `test_005_depenses.py`. Aucun fichier officiel, aucune migration, aucun test et aucun code applicatif n'ont été modifiés.
**Base de l'audit** : dépôt `mymypav-max/BATORYA-Essentiel`, branche `main`, état `548f61f` (migrations 001–004 intégrées ; `004_bons_commande.sql` et son test identiques aux fichiers relus, 150 tests).
**Sources lues en entier ou par recherche exhaustive** : `docs/README.md`, `audit-fonctionnel-v5.16-v6.md`, `invariants.md`, `modèle-données-sqlite-v6-v3.12.md`, `modèle-métier-V6.md`, `cdc-errata-v6.md`, `cdc-fonctionnel-architectural-v6.md`, `conventions-techniques-v6.md`, migrations 001 à 004 et leurs tests. La recherche porte sur tous les termes du brief (annexe A).

Légende des références : « Modèle » = modèle de données SQLite V3.12 ; « Métier » = modèle métier V6 ; « CDC » = cahier des charges ; « INV » = `invariants.md` ; « D-xx », « C-xx », « TR-xx », « CK-xx » = identifiants du modèle.

---

## 0. Synthèse

| | Proposition |
|---|---|
| Tables | **1** : `depenses` (les catégories sont déjà dans 001, les fournisseurs dans 002, les BC dans 004) |
| Triggers | **1** : TR-01 sur `depenses` (`numero` et année de `date_depense` immuables). Aucun autre trigger, aucun trigger sur les tables des tranches précédentes |
| Index | **4** (Modèle §9) : `bc_id`, `fournisseur_id`, `categorie_id`, `date_depense` ; `numero` est couvert par son `UNIQUE` |
| TVA | **Aucune** : `montant` unique, D2, « montant réellement payé (franchise de TVA) ». Ni taux, ni montant TVA, ni TTC (CDC §2 : TVA exclue ; Métier §18 ; Modèle §4.12) |
| Import | **Aucune donnée de dépense dans `import-v6.json`** : `depenses` est un bloc refusé (Modèle §10.3), D-23 retire BLOC-IMP des dépenses. Contredit la partie « import » du brief : voir A-1 et Q1 |
| Statut | **Aucun** (ni payé, ni annulé, ni archivé) : justifié par Métier §18, CDC §28, Audit §9 |
| Règles de service | 30 jours / confirmation (INV-103, D-31), fournisseur archivé non sélectionnable (INV-100), borne d'année 2001–2099 de `date_depense` (INV-177), attribution du numéro `DEP` |
| Règle manquante | **Dépense sur BC annulé** : aucun document ne la définit (le Modèle §4.12 la renvoie expressément à cette tranche). Proposition en Q2 ; **elle n'a aucun effet sur le DDL** |
| Pré-requis documentaire | Le modèle doit passer en **V3.13 avant** la migration (conventions §5) : liste en annexe B |
| Décisions à valider | **9** (section 9), dont 3 structurantes : Q1 (import), Q2 (BC annulé), Q3 (suppression d'une dépense) |

---

## 1. Cadrage métier de Dépenses

### 1.1 Ce que les documents établissent (règles existantes)

| # | Règle | Source |
|---|---|---|
| R1 | Une dépense est une **charge enregistrée**, servant à l'**analyse de gestion et de marge** ; elle ne réduit **jamais** le CA URSSAF | CDC §28, §29 ; Métier §17, §18 ; INV-100, INV-120 ; Audit §9 |
| R2 | Une dépense est **globale** (sans BC) **ou rattachée à un BC** | CDC §15, §28 ; Métier §18 ; Modèle §4.12 |
| R3 | Un fournisseur est **facultatif** (« lorsque nécessaire ») et référencé **par identifiant** | CDC §28 ; Métier §18, §19 ; INV-100 |
| R4 | **Aucune gestion du paiement** : ni statut payé/non payé, ni échéance, ni règlement fournisseur, ni dépenses à payer | CDC §2 (exclus), §28 ; Métier §18 ; Modèle §4.12 ; INV-100 |
| R5 | `montant` = montant réellement payé, **franchise de TVA**, 2 décimales exactes, jamais `0.00` | CDC « Règles de calcul » (dépenses citées parmi les montants à 2 décimales) ; Métier §2.1, §18 ; Modèle §4.12, §2.3 (D2) |
| R6 | Un fournisseur **archivé** reste consultable (historique conservé sur les dépenses existantes) mais **n'est pas sélectionnable pour une nouvelle dépense** ; règle de service | Modèle §4.4, §4.12 ; Métier §17, §19 ; INV-100 ; en-tête de `002_fournisseurs.sql` |
| R7 | Un fournisseur **ayant un historique n'est jamais supprimé** : il est archivé. Garde SQL : FK `depenses.fournisseur_id` en `RESTRICT` | Métier §19 ; Audit §10 ; INV-05, INV-06 ; en-tête de 002 |
| R8 | **Règle des 30 jours** : à compter de `date_100_facture`, rattachement normal pendant 30 jours calendaires ; ensuite le BC est « clôturé pour les nouvelles dépenses » mais reste **toujours rattachable** après une **confirmation simple** ; ni déblocage, ni autorisation, ni délai maximal. **Règle de service, aucun trigger**. Cas C-21 (20 jours : normal), C-22 (45 jours : message « clôturé depuis 15 jours », confirmation, rattachement accepté) | CDC §15 ; Métier §17 ; Modèle §3.5, §4.12, D-31 ; INV-103 |
| R9 | La clôture des dépenses n'affecte ni le statut financier du BC, ni son historique, ni les dépenses déjà rattachées. Le BC n'expose que `date_100_facture` | Modèle §3.5 |
| R10 | Numéro `DEP-00001-yy`, séquence `DEP`, `yy` = année de `date_depense` ; jamais réutilisé ; trous acceptables ; plafond 99 999 ; pas de chronologie continue (TR-02 ne concerne pas DEP) | Modèle §6 ; INV-20, INV-22, INV-24 |
| R11 | `numero` immuable ; `date_depense` **modifiable tant que l'année (yy) ne change pas** | Modèle §4.12, §6, §8 (TR-01) ; INV-23 |
| R12 | Borne d'année **2001–2099** sur `date_depense` : contrôle du **service**, jamais un CHECK | Modèle §2.2 ; INV-177 ; D-38 |
| R13 | Catégorie obligatoire, issue de `categories_depenses` (liste modifiable : ordre, état actif ; contenu initial D-18, jeu de données d'installation) | Modèle §4.3, §4.12 ; D-12, D-18 ; Métier §4.2 |
| R14 | Pièce jointe facultative : `piece_jointe_chemin` et `piece_jointe_racine_id`, « les deux ou aucun » | Modèle §4.12 |
| R15 | `description` obligatoire ; `notes` facultatif ; `created_at`, `updated_at` | Modèle §4.12 ; Métier §18 |
| R16 | Les dépenses **ne dépendent que des BC, des fournisseurs (002) et des catégories (001)** : aucune autre FK | D-34 |
| R17 | `depenses` **n'est pas importable** : bloc refusé de `import-v6.json`, BLOC-IMP retiré des dépenses, les fournisseurs ne sont pas importés non plus | Modèle §10.3, D-23 ; CDC §18 (numérotation) ; en-tête de 002 |
| R18 | FK en `RESTRICT`, jamais de `ON UPDATE`, `id` AUTOINCREMENT, tables `STRICT`, `recursive_triggers=ON`, `INSERT OR REPLACE` interdit par convention | Modèle §1, §2.1 ; INV-04, INV-05, INV-07, D-39 |
| R19 | Index : `depenses(bc_id)`, `(fournisseur_id)`, `(categorie_id)`, `(date_depense)` | Modèle §9 |
| R20 | TR-01 couvre explicitement les dépenses (« numero immuable ; année de la date de numérotation immuable ») | Modèle §8 |

### 1.2 Ce que les documents ne disent pas (silences, traités en section 6 et 9)

1. **Dépense sur BC annulé** : renvoyée « à la conception de la tranche Dépenses » (Modèle §4.12). Aucune autre source (CDC §17 « Conséquences de l'annulation », INV-44, INV-45, INV-173 n'en parlent).
2. **Suppression d'une dépense** : INV-06 et Métier §2.4 énumèrent les entités jamais supprimées ; les dépenses n'y figurent pas. Rien n'autorise ni n'interdit la suppression.
3. **Modification du rattachement** (changer de BC, détacher) et **modification du fournisseur** d'une dépense existante.
4. **Catégorie inactive** : sélectionnable ou non pour une nouvelle dépense.
5. **Journalisation dans `historique`** : `depense` existe dans l'énumération `historique.type_entite`, mais aucun événement de dépense n'est dans la liste des événements obligatoires (Modèle §4.14, INV-110).
6. **Sens exact de `date_depense`** (date de la facture fournisseur ou date du paiement) : le Métier dit « date » et « montant réellement payé ».

### 1.3 Réponses aux points du brief

| Point du brief | Réponse documentaire |
|---|---|
| Dépenses globales | R2 : `bc_id` NULL, aucune règle propre au-delà de R5–R15 (section 4) |
| Dépenses liées à un fournisseur | R3, R6, R7 |
| Dépenses rattachées à un BC | R8, R9, R16 ; états du BC en section 3.2 |
| Dépenses liées à un BC annulé | **Silence** (1.2 n°1) → Q2 |
| Dates de facture | Aucune « date de facture » n'existe pour une dépense. `date_100_facture` est une colonne du **BC** (date d'émission de son premier solde actif, INV-43) : elle sert seulement de point de départ aux 30 jours. La seule date métier d'une dépense est `date_depense` (R10–R12). La « date de saisie » est `created_at` (TS UTC), pas une date métier (Modèle §2.2) |
| Délais d'attachement | R8 (service) |
| TVA | **Absente** par conception (R5) |
| Montants | D2, > 0, 2 décimales exactes, pas de calcul ni d'arrondi (saisie directe) ; pas de montant négatif (INV-14 : la liste des négatifs autorisés exclut les dépenses) |
| Import des anciennes données | R17 : hors contrat `import-v6.json` actuel (A-1, Q1) |
| Numérotation DEP | R10, R11, R12 |
| Statuts | Aucun (R4) |
| Suppression / modification | Modification : R11 ; suppression : silence (Q3) |
| Archivage | Pas d'archivage d'une dépense ; archivage des fournisseurs (R6, R7) et état actif des catégories (R13) |
| Traçabilité d'import | Sans objet (R17) : ni `origine`, ni `legacy_*`, aucune ligne `import_anomalies` pour les dépenses |
| Sauvegarde / restauration | La dépense est dans la base métier sauvegardée ; contrôles post-restauration en section 5 ; pièce jointe : racine possiblement « non localisable » (Modèle §11.3) |
| Invariants et contrôles inter-tables | Section 4 et section 5 |

---

## 2. Modèle de données proposé

### 2.1 Table `depenses` (Modèle §4.12, traduction SQL)

| Colonne | Type | Contraintes | Source |
|---|---|---|---|
| `id` | INTEGER | PK AUTOINCREMENT | INV-04 |
| `numero` | TEXT | NOT NULL UNIQUE ; `GLOB 'DEP-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'` | INV-20, R10 |
| `fournisseur_id` | INTEGER | NULL ; FK → `fournisseurs(id)` **ON DELETE RESTRICT** | R3, R7 |
| `bc_id` | INTEGER | NULL ; FK → `bons_commande(id)` **ON DELETE RESTRICT** | R2 |
| `date_depense` | TEXT (D) | NOT NULL ; `GLOB` aaaa-mm-jj **et** `date(x) IS x` ; **aucune borne d'année** | INV-10, INV-177 |
| `montant` | TEXT (D2) | NOT NULL ; motif D2 ; `<> '0.00'` | R5, INV-11, INV-14 |
| `categorie_id` | INTEGER | NOT NULL ; FK → `categories_depenses(id)` **ON DELETE RESTRICT** | R13 |
| `description` | TEXT | NOT NULL ; `<> ''` | R15 |
| `piece_jointe_chemin` | TEXT | NULL ; si présent `<> ''` | R14 |
| `piece_jointe_racine_id` | INTEGER | NULL ; **sans FK** (référence logique vers `machine.db.stockage_racines`, comme `documents.racine_stockage_id`) | R14, Modèle §4.13 |
| `notes` | TEXT | NULL, non contrôlé | R15 |
| `created_at`, `updated_at` | TEXT (TS) | NOT NULL ; défaut instant UTC ms ; `GLOB` | Modèle §2.2 |

CHECK de table :
- `substr(numero, 11, 2) = substr(date_depense, 3, 2)` — l'année du numéro est celle de `date_depense`, **sans condition d'origine** (la table n'a pas d'`origine`, R17) ;
- `(piece_jointe_chemin IS NULL) = (piece_jointe_racine_id IS NULL)` — « les deux ou aucun ».

Ce que le DDL **ne contient pas**, volontairement : `origine`, `legacy_id`, `legacy_data`, `legacy_numero` (R17) ; `statut`, `cancelled_at`, `motif_annulation` (R4) ; `taux_tva`, `montant_tva`, `montant_ttc` (R5) ; `date_facture`, `date_echeance`, `date_paiement` (R4, aucune règle ne les prévoit) ; borne d'année 2001–2099 (R12) ; contrôle fournisseur actif / catégorie active / règle des 30 jours / BC annulé (service) ; `frozen_at` (une dépense n'est jamais gelée : aucune règle).

### 2.2 Clés étrangères et suppressions

| FK | ON DELETE | Conséquence |
|---|---|---|
| `fournisseur_id` → `fournisseurs` | RESTRICT | un fournisseur référencé par une dépense ne peut pas être supprimé (R7) ; il est archivé par le service |
| `bc_id` → `bons_commande` | RESTRICT | cohérent avec D-35 : un BC n'est jamais supprimé (TR-19) ; la FK est redondante en pratique mais obligatoire (INV-05, Modèle §9 : un index par FK) |
| `categorie_id` → `categories_depenses` | RESTRICT | une catégorie utilisée ne se supprime pas (le service la désactive : `actif = 0`) |

Aucun `CASCADE`, aucun `ON UPDATE`. Aucune FK vers une table absente : `bons_commande` (004), `fournisseurs` (002) et `categories_depenses` (001) existent.

### 2.3 Trigger (1)

| Trigger | TR | Règle | Message |
|---|---|---|---|
| `tr_01_depenses_numero_immuable` — `BEFORE UPDATE OF numero, date_depense ON depenses`, `WHEN NEW.numero IS NOT OLD.numero OR substr(NEW.date_depense,3,2) IS NOT substr(OLD.date_depense,3,2)` | TR-01 | `numero` immuable ; l'année de `date_depense` ne change jamais (la date reste modifiable dans la même année) | `INV-23: depenses.numero et l'annee de date_depense sont immuables` |

Cette formulation a été **prototypée** (hors dépôt) : changement d'année refusé, changement de jour dans la même année accepté, changement de `numero` refusé.

### 2.4 Index (4)

`idx_depenses_bc_id`, `idx_depenses_fournisseur_id`, `idx_depenses_categorie_id`, `idx_depenses_date_depense` (Modèle §9). `numero` : index automatique de son `UNIQUE`. Total constaté sur le prototype : 4 index nommés + 1 index automatique.

### 2.5 Hors tranche (rien n'est anticipé)

Aucune table `historique`, `documents`, `factures`, `reglements`, `garanties`, `pv`, `planning_evenements`, `bc_notes`, `urssaf_*`. Aucune table de lien générique. Aucune colonne de cache sur `bons_commande` (pas de « total des dépenses » : l'analyse de marge est calculée, jamais stockée, CDC §29 / Métier §17).

---

## 3. Relations et règles de rattachement

### 3.1 Dépense ↔ Fournisseur

| Sujet | Règle proposée | Niveau |
|---|---|---|
| Obligatoire ? | **Non** (`fournisseur_id` NULL admis : carburant, achat sans fournisseur référencé) | SQL (colonne NULL) |
| Nouvelle dépense | fournisseur `actif` uniquement (R6) | **Service** (INV-100) ; pas de trigger (aligné sur l'en-tête de 002) |
| Fournisseur archivé ensuite | les dépenses existantes **conservent** leur fournisseur ; aucune modification en cascade | SQL (aucun trigger sur `fournisseurs`) |
| Modifier la dépense sans toucher au fournisseur | permis, même si le fournisseur est archivé | Service (Q4) |
| Changer le fournisseur d'une dépense existante | permis (aucune règle d'immutabilité), **vers un fournisseur actif** ; retirer le fournisseur (NULL) permis | Service (Q4) — silence des documents |
| Suppression physique du fournisseur | impossible tant qu'une dépense le référence (FK RESTRICT) ; le service archive | SQL + Service |
| Suppression de la dépense puis du fournisseur | possible si plus aucune dépense ne le référence (le « fournisseur ayant un historique » est apprécié par le service) | Service |

### 3.2 Dépense ↔ BC

Le **gel** (`frozen_at`) n'est pas un statut : les statuts d'un BC sont `en_cours`, `termine`, `annule` (Modèle §2.5). Le gel est orthogonal et **sans effet** sur le rattachement : une dépense n'écrit rien dans `bons_commande` (donc TR-12 et TR-14 ne sont jamais déclenchés par un rattachement).

| État du BC | Nouvelle dépense / nouveau rattachement | Source |
|---|---|---|
| `en_cours`, `date_100_facture` NULL | libre | R8 |
| `en_cours`, 100 % facturé depuis ≤ 30 jours | libre, sans confirmation (C-21) | R8 |
| `en_cours`, 100 % facturé depuis > 30 jours (dès le 31ᵉ jour : `date_du_jour > date_100_facture + 30 jours`) | **confirmation simple** ; message « Ce BC est clôturé depuis X jours. Êtes-vous sûr de vouloir ajouter cette dépense sur ce BC ? » avec **X = jours écoulés − 30** (C-22 : 45 jours → 15) | R8 |
| `termine` | **même règle**, `date_100_facture` y est toujours renseignée (CHECK de 004) : aucune règle propre à `termine` | R8, 004 |
| gelé (non annulé) | aucun effet | — |
| `annule` | **non défini par les documents** → Q2 (proposition : confirmation de service, sans trigger) | silence |

Précisions :
- le « jour courant » est la **date locale** de l'entreprise (Modèle §2.2) ; la comparaison se fait en jours calendaires, la règle porte sur la **date du rattachement**, pas sur `date_depense` ;
- `date_100_facture` peut repasser à NULL (annulation du solde) puis prendre la date d'un nouveau solde (INV-43) : la règle s'évalue sur la valeur courante, sans effet sur les dépenses déjà rattachées (R9) ;
- un BC annulé a en principe `date_100_facture` NULL (l'annulation d'un BC ayant un solde actif est interdite, D-05 / INV-44) ; le SQL de 004 ne le garantit pas, c'est le service ;
- **ce qui s'applique à un « nouveau rattachement »** : création avec `bc_id`, passage de NULL à un BC, passage d'un BC à un autre. **Ne déclenchent pas la règle** : modification des autres colonnes d'une dépense déjà rattachée, détachement (`bc_id` → NULL) — Q4.

| Évènement sur le BC | Effet sur les dépenses rattachées |
|---|---|
| modification du devis/BC avant gel (régénération des lignes) | aucun (`bons_commande.id` stable ; INV-168) |
| rattachement d'un client `a_rattacher` (`client_id`) | aucun (la dépense n'a pas de client) |
| passage `termine` ↔ `en_cours` | aucun |
| annulation du BC | **aucun** : les dépenses déjà rattachées restent rattachées (le BC et ses dépenses ne sont jamais supprimés ; pas de cascade) |
| suppression du BC | impossible (TR-19, D-35) |

### 3.3 Dépense ↔ Catégorie

`categorie_id` obligatoire. Une catégorie utilisée n'est pas supprimée (RESTRICT) ; elle est désactivée. Une catégorie **inactive** n'est pas proposée pour une nouvelle dépense : par analogie avec le fournisseur archivé, **règle de service** à valider (Q5, silence des documents).

### 3.4 Autres relations

| Relation | Décision |
|---|---|
| Pièce jointe → racine de stockage | référence logique sans FK ; **CK-10 doit couvrir** `depenses.piece_jointe_racine_id` (aujourd'hui limité aux documents) ; après restauration sur une autre machine : racine « non localisable », remappage (Modèle §11.3) |
| Pièce jointe → table `documents` | **non** : `documents.type_entite` n'admet que `devis`, `facture`, `pv` ; la pièce jointe d'une dépense reste dans ses deux colonnes |
| Dépense → `historique` | non définie (Q6) ; la table `historique` n'existe pas encore (tranche ultérieure), aucun lien SQL |
| Dépense → URSSAF | aucune (INV-120) |
| Dépense → client | aucune ; le client d'un BC n'est pas copié sur la dépense |

---

## 4. Dépense globale et liste des invariants

### 4.1 Dépense globale (`bc_id` NULL)

Règles propres : **aucune** au-delà de R5–R15. Pas de règle des 30 jours, pas de règle BC annulé. Elle entre dans les analyses globales de marge et dans aucune analyse par BC. Passer de globale à rattachée = « nouveau rattachement » (3.2). Détacher une dépense = la rendre globale (Q4). Le numéro `DEP` est identique dans les deux cas.

### 4.2 Invariants existants applicables

INV-04, INV-05, INV-06 (fournisseur), INV-07, INV-10, INV-11, INV-14, INV-20, INV-21, INV-22 (dont TR-95 et TR-96 de 004, **non modifiés**), INV-23 (TR-01), INV-24 (n'est pas applicable à DEP), INV-100, INV-103, INV-120, INV-177, D-31, D-34, D-38, D-39.

### 4.3 Invariants nouveaux proposés (numéros suivants disponibles : INV-179 et suivants)

| INV (proposé) | Énoncé | Garde | Test (nom) |
|---|---|---|---|
| INV-179 | Une dépense a un `montant` strictement positif en D2 (jamais `0.00`, jamais négatif) ; sa pièce jointe est renseignée en entier (chemin et racine) ou pas du tout | SQL (CHECK) | `test_INV_179_montant_positif_D2`, `test_INV_179_piece_jointe_chemin_et_racine` |
| INV-180 | **Dépense et BC annulé** (contenu : Q2) | SVC (+ CK éventuel selon Q2) | `test_INV_180_*` (SQL : témoin négatif — le SQL n'interdit pas ; service : tests Rust) |
| INV-181 | Une dépense peut être supprimée physiquement (aucun statut ni annulation) ; son numéro n'est jamais réattribué (INV-22) ; la suppression n'affecte ni le BC, ni le fournisseur, ni la catégorie (contenu : Q3) | SVC, SQL (aucun CASCADE entrant) | `test_INV_181_suppression_n_affecte_ni_bc_ni_fournisseur` |
| INV-182 | Une catégorie de dépense inactive n'est pas sélectionnable pour une nouvelle dépense (contenu : Q5) | SVC | test de service (hors SQL) |

INV-103 est **inchangé** ; ses cas C-21 et C-22 sont déjà au Modèle §13.1. INV-100 est **inchangé** ; la précision « modification d'une dépense existante » (Q4) s'y ajoute en commentaire, sans changer son sens.

---

## 5. Répartition SQL / trigger / service / CK-13

| Règle | CHECK / UNIQUE / FK | Trigger | Service | Contrôle CK |
|---|---|---|---|---|
| Format `DEP-nnnnn-yy`, unicité | CHECK GLOB + UNIQUE | — | attribution : upsert `RETURNING`, `annee` = yy de `date_depense`, high-water avant COMMIT (mécanisme PT-1 non validé) | CK-01, CK-02 (à étendre à `depenses`) |
| Année du numéro = année de `date_depense` | CHECK `substr` | TR-01 (message INV-23) | — | CK-01 |
| `numero` immuable, année de `date_depense` immuable | — | **TR-01** | — | — |
| `date_depense` : date réelle | CHECK GLOB + `date(x) IS x` | — | — | — |
| Borne 2001–2099 de `date_depense` | **jamais un CHECK** (D-38) | — | **oui** (création et modification) | — |
| `montant` D2, > 0 | CHECK | — | saisie à 2 décimales | — |
| Pièce jointe : les deux ou aucun | CHECK | — | stockage du fichier | CK-10 (à étendre) |
| Fournisseur existant | FK RESTRICT | — | — | CK-03 |
| Fournisseur **actif** pour une nouvelle dépense / un changement | — | **non** (aligné 002) | **oui** (INV-100) | — |
| Catégorie existante | FK RESTRICT | — | — | CK-03 |
| Catégorie **active** | — | — | oui (Q5) | — |
| BC existant | FK RESTRICT | — | — | CK-03 |
| Règle des 30 jours + confirmation | — | **non** (D-31, INV-103) | **oui** | — |
| Dépense sur BC annulé | — | **non** dans la proposition | oui (Q2) | aucun nouveau CK |
| Détachement / changement de BC | — | — | oui (Q4) | — |
| Suppression d'une dépense | pas de garde | — | oui (confirmation, pièce jointe, Q3) | — |
| Pas de statut de paiement, pas d'échéance | **absence de colonne** | — | — | — |
| Dépense ne réduit pas le CA URSSAF | — | — | oui (calcul URSSAF) | — |
| Import | **aucun** (R17) | — | — | CK-12 sans objet pour les dépenses |

**CK-13** reste le diagnostic devis ↔ BC : il **n'est pas étendu** aux dépenses (aucune incohérence inter-tables propre aux dépenses n'est détectable de façon utile ; la FK et CK-03 couvrent l'existence des parents). **Pas de nouveau CK** n'est proposé ; en revanche CK-01, CK-02, CK-03 et CK-10 doivent explicitement viser `depenses` pour la restauration (Modèle §11.2 étape 9, §14).

Pourquoi un seul trigger : la règle des 30 jours et le fournisseur archivé sont expressément des règles de service (INV-103, INV-100, en-tête de 002). Les autres rapprochements (BC annulé, catégorie active) sont du même type : décider de leur donner un trigger serait une décision nouvelle, à valider (Q2 option C).

---

## 6. Points ambigus ou contradictoires trouvés

| # | Point | Constat | Proposition |
|---|---|---|---|
| A-1 | **Import des dépenses** | Le brief demande « quelles données de dépenses doivent pouvoir être fournies par `import-v6.json` ». Les documents disent l'inverse : bloc `depenses` **refusé** (Modèle §10.3 : « La V2 ne les fournit pas »), BLOC-IMP **retiré** des dépenses (D-23), « les fournisseurs ne sont pas importés » (CDC §18), et ouvrir un bloc supplémentaire = nouvelle `contrat_version` | Q1. Recommandation : confirmer, pas de BLOC-IMP. **Coût d'une décision tardive** : ajouter plus tard `origine`/`legacy_*` avec leur CHECK de cohérence impose de **reconstruire la table** (une migration ultérieure ne peut pas ajouter ce CHECK de table par `ALTER`) ; et des dépenses importables exigeraient aussi d'importer les fournisseurs |
| A-2 | **Dépense sur BC annulé** | Renvoyée à cette tranche (Modèle §4.12) ; aucune règle ailleurs. INV-173 liste les modifications commerciales **du BC** : le rattachement d'une dépense n'en modifie aucune | Q2 |
| A-3 | **Suppression d'une dépense** | Silence (INV-06, Métier §2.4 ne la citent pas). Or une dépense n'a **ni statut ni annulation** : sans suppression, une saisie erronée ne peut être corrigée que par modification ; et l'année de `date_depense` ne pouvant pas changer, une erreur d'année ne se corrige que par suppression + nouvelle saisie | Q3 |
| A-4 | **TR-01 face à un REPLACE** (conséquence de A-3) | Si la suppression est permise, aucun trigger `BEFORE DELETE` ne protège la table : un `INSERT OR REPLACE` portant l'`id` d'une dépense remplace la ligne **en changeant le `numero` et en remettant `created_at` à zéro, sans déclencher TR-01** (vérifié sur prototype avec `recursive_triggers=ON`). TR-01 est donc une garde contre l'`UPDATE`, pas contre le remplacement. Le Modèle §1 fonde la protection contre `INSERT OR REPLACE` sur les triggers `BEFORE DELETE` (TR-90, TR-11, TR-19) et sur la convention INV-07 : `depenses` n'en aurait pas. La vraie protection de « numéro jamais réutilisé » est la séquence (INV-22, TR-95/TR-96) et CK-02 | À consigner dans le modèle ; test témoin (documenté, pas de faux sentiment de protection). Si une immutabilité forte est voulue, il faut interdire la suppression, donc créer un mécanisme d'annulation (hors décision R4) |
| A-5 | **Modification du rattachement / du fournisseur** | Silence | Q4 |
| A-6 | **Catégorie inactive** | Le Métier donne un « état actif » aux catégories mais ne dit pas qu'une catégorie inactive est non sélectionnable (il le dit pour le fournisseur et la prestation) | Q5 |
| A-7 | **« Date de facture »** (brief) | Aucune date de facture sur une dépense ; `date_100_facture` est celle du BC (INV-43). Le sens de `date_depense` (facture ou paiement) n'est pas précisé : « montant réellement payé » oriente vers la date de dépense effective | À préciser dans le modèle métier (libellé), sans effet SQL |
| A-8 | **« BC gelé » comme statut** (brief) | Les statuts d'un BC sont `en_cours`, `termine`, `annule` ; `gele` est le drapeau `frozen_at` | Aucune règle de dépense liée au gel (3.2) |
| A-9 | **« Clôturé depuis X jours »** | CDC §15 et Métier §17 ne définissent pas X ; le cas C-22 le fixe (45 jours → 15 jours) | X = jours écoulés − 30 ; à inscrire dans INV-103 ou le Métier §17 |
| A-10 | **Journalisation** | `historique.type_entite` contient `depense` mais aucun événement obligatoire de dépense (Modèle §4.14, INV-110) | Q6 |
| A-11 | **Dépense négative** (avoir fournisseur, remboursement reçu) | INV-14 exclut les dépenses des montants négatifs ; V6 ne peut donc pas représenter un avoir fournisseur | Limite connue à documenter ; pas de contournement dans 005 |
| A-12 | **Statuts documentaires périmés** | `docs/README.md` et `invariants.md` (en-tête) disent « V3.12 en relecture, non validée », alors que le Modèle la dit « validée après intégration de la migration 004 » ; `modèle-métier-V6.md` se dit « aligné sur la V3.11 » et renvoie à « SQLite V3.10 » ; `conventions-techniques-v6.md` §4, §5, §7 ne listent que 001–003 ; Modèle §4.12 dit toujours « sera déterminé lors de la conception de la tranche Dépenses » ; Modèle §17.1 : ligne vide qui coupe le tableau avant la ligne 004 | Annexe B |
| A-13 | **CK-10** | Libellé limité aux « racines de documents » | Étendre aux pièces jointes de dépenses |

---

## 7. Proposition de structure de `005_depenses.sql`

Emplacement : `src-tauri/migrations/metier/005_depenses.sql` ; `PRAGMA user_version = 5` posé par le runner ; ni `BEGIN/COMMIT` ni `PRAGMA` ; aucune ligne insérée ; en-tête citant le **modèle V3.13**.

```text
1. En-tête : références (Modèle §2, §3.5, §4.12, §6, §8 TR-01, §9, §10.3, §17.1) ; invariants (INV-04, 05, 06, 10, 11, 14, 20,
   21, 22, 23, 100, 103, 177, 179 à 182) ; décisions (D-12, D-18, D-23, D-31, D-34, D-38, D-39, D-40 à D-4x) ;
   précisions de DDL ; ce qui relève du service ; notes du runner.
2. Table depenses (STRICT) — colonnes et CHECK de la section 2.1.
3. Trigger tr_01_depenses_numero_immuable (TR-01).
4. Index idx_depenses_bc_id, idx_depenses_fournisseur_id, idx_depenses_categorie_id, idx_depenses_date_depense.
```

Esquisse de la table (non destinée à être copiée telle quelle) :

```sql
CREATE TABLE depenses (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    numero                 TEXT    NOT NULL UNIQUE CHECK (numero GLOB 'DEP-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'),
    fournisseur_id         INTEGER REFERENCES fournisseurs (id) ON DELETE RESTRICT,
    bc_id                  INTEGER REFERENCES bons_commande (id) ON DELETE RESTRICT,
    date_depense           TEXT    NOT NULL CHECK (date_depense GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
                                                   AND date(date_depense) IS date_depense),
    montant                TEXT    NOT NULL CHECK (montant GLOB '[0-9]*.[0-9][0-9]' AND montant NOT GLOB '*[^0-9.]*'
                                                   AND montant NOT GLOB '*.*.*' AND montant NOT GLOB '0[0-9]*'
                                                   AND montant <> '0.00'),
    categorie_id           INTEGER NOT NULL REFERENCES categories_depenses (id) ON DELETE RESTRICT,
    description            TEXT    NOT NULL CHECK (description <> ''),
    piece_jointe_chemin    TEXT    CHECK (piece_jointe_chemin IS NULL OR piece_jointe_chemin <> ''),
    piece_jointe_racine_id INTEGER,
    notes                  TEXT,
    created_at             TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at             TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    CHECK (substr(numero, 11, 2) = substr(date_depense, 3, 2)),
    CHECK ((piece_jointe_chemin IS NULL) = (piece_jointe_racine_id IS NULL)),
    CHECK (created_at GLOB '…TS…'), CHECK (updated_at GLOB '…TS…')
) STRICT;
```

Remarques de rédaction : `DEP-00000-yy` est accepté par le motif (comme `BCD-00000-yy` en 004) ; la séquence démarre à 1. Une séquence `DEP` avec `annee = 0` est refusée par `numerotation_sequences` (constaté) : l'année 2000 est donc impossible côté séquence, ce que garantit la borne de service (INV-177).

---

## 8. Proposition de structure de `test_005_depenses.py`

Emplacement : `src-tauri/tests/metier/test_005_depenses.py`, test **T-30** du Modèle §13.3. Connexion : `foreign_keys=ON`, `recursive_triggers=ON` posés explicitement, chaîne **001 → 005** appliquée. Noms `test_INV_xx_…`. Les tests de 003 et 004 qui vérifient l'absence de `depenses` appliquent seulement 001–003 / 001–004 : ils ne sont **pas** touchés.

| Groupe | Contenu | Tests (estim.) |
|---|---|---|
| Migration et objets | `PRAGMA recursive_triggers` actif ; 1 table `STRICT`, colonnes exactes (types, NOT NULL, défauts), aucune ligne, 1 trigger, 4 index (noms et colonnes), plan de requête utilisant les index, `foreign_key_check` vide, aucune colonne `origine`/`legacy_*`/`statut`/TVA/échéance, tables 001–004 inchangées (non-régression) | 8 |
| Création | dépense minimale valide ; globale ; avec fournisseur ; avec BC ; avec pièce jointe ; défauts de `created_at`/`updated_at` | 6 |
| Numérotation | format `GLOB` explicite ; année = année de `date_depense` (et non l'année courante) ; séquence `DEP` par année ; plafond 99 999 ; numéro non réutilisé après suppression (séquence) ; `DEP` avec `annee = 0` refusé ; TR-95 / TR-96 inchangés ; UPSERT d'attribution autorisé ; `derniere_date` non utilisée | 9 |
| TR-01 | `numero` immuable ; changement d'année refusé (message `INV-23`) ; changement dans la même année accepté ; chaque clause du `WHEN` isolée ; autres colonnes librement modifiables ; témoin A-4 : un REPLACE ne déclenche pas TR-01 (assertion documentée) | 8 |
| Domaine : dates | calendrier exhaustif (comme 004), `date(x) IS x`, absence de borne 2001–2099 (années 1900, 2000, 2100 acceptées en SQL — règle de service) | 4 |
| Domaine : montants | D2 valides/invalides (`0.00`, `1.5`, `-1.00`, `1a.00`, `1.2.50`, `01.00`, `""`, NULL, float) ; pas de TVA | 5 |
| Domaine : textes et pièce jointe | `description` vide/NULL ; chemin vide ; chemin sans racine et inversement ; deux ou aucun | 5 |
| FK et suppressions | `fournisseur_id`, `bc_id`, `categorie_id` inexistants refusés ; suppression d'un fournisseur / d'une catégorie / d'un BC référencés refusée (RESTRICT, TR-19) ; suppression de la dépense permise (si Q3) sans effet sur les parents ; `INSERT OR REPLACE` : comportement documenté | 8 |
| Rattachement BC (témoins de répartition) | le SQL **accepte** un rattachement à un BC `en_cours`, 100 % depuis 20 / 45 jours, `termine`, gelé, **annulé** — c'est le service qui décide ; rattachement ne modifie pas `bons_commande` (aucun trigger TR-12/TR-14 déclenché) ; changement et détachement de `bc_id` | 7 |
| Fournisseur / catégorie (témoins) | le SQL accepte un fournisseur archivé et une catégorie inactive (règles de service, témoins négatifs) ; archivage d'un fournisseur sans effet sur ses dépenses | 4 |
| Identifiants décalés | clients, fournisseurs, catégories, BC, dépenses avec des `id` tous différents pour détecter une confusion d'identifiants | 3 |
| Contrôles de restauration | requêtes CK-01/02/03 (réutilisables) sur `depenses` : détectent un doublon de numéro, une séquence en retard sur un numéro présent, une FK orpheline (base corrompue volontairement hors contrainte) | 4 |
| **Total estimé** | | **≈ 70** |

Les règles de service (30 jours, confirmation, fournisseur actif, catégorie active, BC annulé, borne 2001–2099) sont vérifiées **côté SQL par des témoins négatifs** (le SQL ne les impose pas). Leurs vrais tests appartiennent aux services Rust, hors de cette tranche.

**Campagne de mutation (conventions §7.1)** : mutants générique (CHECK, tokens, `IN`, `NOT NULL`, `UNIQUE`, FK, `IS`/`IS NOT`, `OLD`/`NEW`, `date(x) IS x`) **et** extension propre à 005 : confusion d'identifiants entre colonnes, clauses du `WHEN` de TR-01, conjoncts D2 (jeu de caractères, double point, zéros de tête, `0.00`), `substr` du numéro et de la date, « les deux ou aucun » de la pièce jointe. Objectif : **0 survivant non qualifié**. Survivants attendus à qualifier (mêmes classes qu'en 004) : `date_depense GLOB` redondant avec `date(x) IS x` ; clause « année » de TR-01 redondante avec le CHECK `substr` quand `numero` est inchangé (tuée seulement par la vérification du message `INV-23`) ; disjonctions qui laissent passer `NULL` (`piece_jointe_chemin IS NULL OR …`) ; borne basse d'un pourcentage (sans objet ici : pas de P2).

---

## 9. Décisions à valider avant l'écriture du SQL

Numérotation provisoire : D-40 et suivants (D-39 est la dernière du modèle).

| # | Question | Options | Recommandation | Effet sur le DDL |
|---|---|---|---|---|
| **Q1** | **Import (A-1).** Confirmer que `depenses` (et `fournisseurs`) restent hors `import-v6.json` (contrat v1) : pas de BLOC-IMP sur `depenses`, aucune ligne `import_anomalies` pour les dépenses | (a) confirmer D-23 / §10.3 ; (b) rendre les dépenses importables : BLOC-IMP+ sur `depenses`, bloc `fournisseurs` aussi, nouvelle `contrat_version`, numéros DEP V6 fournis par le convertisseur, ordre d'import à compléter | **(a)** : la V2 ne fournit pas de dépenses (Modèle §10.3), D-23 est validée, CDC §18 aussi. Si (b) est envisagé un jour, le dire **maintenant** : le choix change la table | **Oui** (colonnes `origine`, `legacy_*` et leurs CHECK) |
| **Q2** | **Dépense sur BC annulé.** Un BC annulé est terminal (INV-173) mais le rattachement d'une dépense ne modifie aucune colonne du BC. Des frais engagés avant l'annulation (matériaux commandés) ou après (frais de reprise) restent des charges du dossier | (A) **refus** par le service : nouvelle dépense impossible sur un BC annulé (dépense déjà rattachée conservée) ; (B) **confirmation simple** par le service, sur le modèle de D-31 ; (C) refus **en SQL** par un trigger (`BEFORE INSERT` et `BEFORE UPDATE OF bc_id` quand `bc_id` change, BC `annule`) — stable car « annulé » est terminal | **(B)**, par cohérence avec D-31 (Rémy a refusé tout blocage définitif) et avec l'objet des dépenses (analyse de marge : les charges d'un BC annulé comptent). (A) est la lecture stricte. (C) donnerait une garantie SQL mais ajoute un trigger inter-tables que rien ne demande | **Non** pour (A) et (B) ; (C) ajoute 1 trigger |
| **Q3** | **Suppression physique d'une dépense** (A-3, A-4) | (a) permise, sans garde SQL ; (b) interdite (trigger `BEFORE DELETE`), ce qui exige un mécanisme d'annulation (statut ou `cancelled_at`), non prévu par R4 | **(a)** : aucun statut n'existe ; les trous de numérotation sont acceptés ; la correction d'une année erronée n'a pas d'autre voie. Le service confirme la suppression, gère la pièce jointe orpheline, et le numéro n'est jamais réattribué | **Non** pour (a) ; (b) ajoute colonnes et triggers |
| **Q4** | **Modification d'une dépense existante** : changer ou retirer le fournisseur, changer de BC, détacher | Tout permis ; toute **nouvelle** cible est soumise aux règles d'une nouvelle dépense (fournisseur actif, 30 jours, Q2) ; détachement et conservation d'un fournisseur archivé non modifié : libres. Variante : figer fournisseur et BC après création | **Libre avec règles de nouvelle cible** (rien dans les documents n'immobilise ces champs) | Non |
| **Q5** | **Catégorie inactive** non sélectionnable pour une nouvelle dépense (ou un changement de catégorie) | oui / non | **oui** (service), comme pour le fournisseur archivé | Non |
| **Q6** | **Historique** : journaliser création / modification / suppression des dépenses ? | oui (événements à ajouter à INV-110) / non (rien d'obligatoire aujourd'hui) | **non obligatoire** en 005 (la table `historique` n'existe pas ; événements à définir avec sa tranche) | Non |
| **Q7** | **TR-01** : immutabilité limitée à `numero` et l'année de `date_depense` (Modèle §8). Faut-il aussi protéger `id` et `created_at` ? | non (règle documentée) / oui (comme TR-12 de 004) | **non** : aucune règle ne le demande | 0 ou 1 clause de plus |
| **Q8** | **Pièce jointe** : seul le « les deux ou aucun » est contrôlé en SQL ; format du chemin (relatif, sans `..`) et existence de la racine : service et CK-10 étendu | oui / ajouter des CHECK de chemin | **oui** (service + CK-10) : INV-106 parle de « chemin relatif » sans motif SQL | Non |
| **Q9** | **Contrôles** : étendre CK-01, CK-02, CK-03 et CK-10 à `depenses` ; pas de nouveau CK ; CK-13 inchangé | oui / créer un CK-14 de cohérence des dépenses | **oui, sans CK-14** | Non |

**Ordre conseillé** : Q1 et Q3 conditionnent le DDL et le test ; Q2 conditionne un éventuel trigger et INV-180 ; Q4 à Q9 se règlent par défaut sans toucher au SQL.

---

## Annexe A — Recherche exhaustive (termes du brief)

Les documents ont été interrogés sur : *dépense, depense, DEP-, fournisseur, TVA, franchise, supprim\*, annul\*, 30 jours, date_100_facture, clôtur\*, import, legacy, origine, archiv\*, restauration, CK-, TR-, INV-100, INV-103, INV-177*. Résultats utiles :

- **Dépenses** : CDC §2, §15, §28, §29 ; Métier §2.1, §2.2, §4.2, §17, §18, §19 ; Modèle §2.2, §2.5, §3.5, §4.3, §4.4, §4.12, §6, §8, §9, §10.3, §13.1 (C-21, C-22), §15 (D-12, D-18, D-23, D-31, D-34, D-38), §17 ; INV-14, INV-20, INV-23, INV-100, INV-103, INV-120, INV-177 ; Audit §9, §10 ; conventions §5 à §7.
- **TVA** : CDC §2 (« absence de gestion de TVA », TVA exclue, §périmètre final), Métier en-tête et §18, Audit §6, Modèle §4.12 : **aucune colonne, aucune règle de calcul**.
- **Import** : CDC §18, §42 ; Modèle §10.1 à §10.9, D-23 ; INV-130 à INV-136, INV-153, INV-154 ; en-tête de 002.
- **Suppression** : INV-06 ; Métier §2.4, §3, §4.1, §19 ; Modèle §7, §4.4 ; aucune mention pour les dépenses.
- **BC annulé** : CDC §17 ; INV-44, INV-45, INV-173, INV-174 ; Modèle §4.7, §4.12 ; aucune mention des dépenses, hors le renvoi explicite du §4.12.
- **Code** : migrations 001 (`categories_depenses`, `numerotation_sequences` — `DEP` déjà dans la liste fermée), 002 (en-tête : règle de service pour le fournisseur archivé ; FK `RESTRICT` annoncée), 004 (`date_100_facture`, statuts, TR-12/13/14/17/19, TR-96) ; tests 001–004 (aucun test de dépense ; 003 et 004 vérifient seulement l'absence de la table sur leur chaîne).

## Annexe B — Impact documentaire (à reporter, **rien n'a été modifié**)

Avant d'écrire `005_depenses.sql` (conventions §5 : le modèle passe à la version suivante **avant** la migration) :

| Fichier | Correction nécessaire |
|---|---|
| `modèle-données-sqlite-v6-v3.12.md` → **V3.13** | §0 (historique) ; §4.12 (retirer « sera déterminé lors de la conception de la tranche Dépenses », y consigner Q2 à Q8, A-4, A-11) ; nouveau §4.19 « Précisions de DDL de `metier/005_depenses.sql` » ; §8 (note TR-01 : table `depenses`, REPLACE) ; §13.3 (T-30) ; §14 (CK-01, 02, 03, 10) ; §15 (D-40 et suivants) ; §17.1 (ligne 005 ; corriger la ligne vide qui coupe le tableau avant la ligne 004) |
| `invariants.md` | INV-179 à INV-182 ; journal ; rattacher le registre à la V3.13 ; corriger « V3.12 en relecture, non validé » |
| `modèle-métier-V6.md` | §18 : rattachement, BC annulé, suppression, sens de `date_depense` ; §17 : définition de X ; en-tête : version du modèle SQLite (V3.11 / V3.10 périmés) |
| `conventions-techniques-v6.md` | §4, §5, §7 : ajouter 004 et 005 |
| `docs/README.md` | statut de la V3.12 / V3.13 |
| `cdc-fonctionnel-architectural-v6.md` | §15 / §17 / §28 : règle du BC annulé, seulement si Q2 est validée ; la formulation « depuis X jours » |

---

**Risque** : l'option Q2 (B) est une règle nouvelle, absente des documents, proposée par cohérence avec D-31 ; si Rémy retient (A) ou (C), le texte du service et d'INV-180 changent (et, pour (C), un trigger s'ajoute).
**Micro-amélioration** : valider Q1 et Q3 d'abord — ce sont les deux seules décisions qui modifient le contenu de la table, le reste se règle sans toucher au SQL.
