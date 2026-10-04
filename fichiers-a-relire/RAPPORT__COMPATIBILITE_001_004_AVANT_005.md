# RAPPORT — Compatibilité technique des migrations 001–004 avant `005_depenses.sql`

**Date** : 2026-10-04 · **Dépôt** : `main` = `origin/main` = `7e744f2`, arbre propre avant et après la vérification.
**Périmètre** : contrôle technique final, sans audit métier. Le SQL réellement présent dans `src-tauri/migrations/metier/` (001 à 004) est la référence ; les documents V3.13 et `CADRAGE__005_depenses.md` fournissent les décisions comparées.
**Méthode** : lecture des quatre migrations, puis expériences SQL **temporaires** hors dépôt (SQLite 3.45.1). Aucun fichier du dépôt n'a été modifié ; `005_depenses.sql`, `005a`, `005b` et tout test permanent n'ont pas été créés (§9).

**Légende des natures** : *Règle documentée* · *Décision validée* · *Déduction technique* · *Proposition* · *À valider*.

---

## CONCLUSION (résumé)

> **GO** pour concevoir et écrire `005_depenses.sql`. Elle ne dépend d'aucune structure créée ou modifiée par `005a` ou `005b` : elle ne référence que la clé primaire `id` de `fournisseurs` (002), de `bons_commande` (004) et de `categories_depenses` (001), ainsi que le type `DEP` déjà accepté par `numerotation_sequences` (001). Aucun bloquant d'ordre des migrations.
>
> **Trois points de couverture** sont à consigner dans le contenu (encore *proposé*) de `005a` et `005b`, **sans effet sur 005** : voir §3.3 (G-1 et G-2) et §4.3 (G-3). Ils ne remettent en cause ni l'ordre officiel ni aucune décision.

---

## 1. État réel des migrations 001–004 (éléments qui comptent pour 005)

### 1.1 Tables et objets utiles à Dépenses

| Migration | Objet réel | Détail utile à 005 |
|---|---|---|
| `001_initial.sql` | `numerotation_sequences` | `type_objet IN ('CLI','FOU','DEV','BCD','ACP','FAC','AVO','PVR','DEP')` : **`DEP` est déjà accepté** ; `annee BETWEEN 0 AND 99` ; TR-95 (compteur non décroissant) ; TR-96 (004) interdit le DELETE |
| `001_initial.sql` | `categories_depenses` | `id` PK AUTOINCREMENT, `code` UNIQUE, `libelle`, `actif` 0/1, `ordre`. **Aucune ligne insérée** par 001–004 |
| `001_initial.sql` | `clients` | `statut IN ('actif','archive','a_rattacher')`, CHECK `a_rattacher ⇒ origine='import'`, `idx_clients_statut`. **Aucun trigger** sur la table |
| `002_fournisseurs.sql` | `fournisseurs` | `id` PK AUTOINCREMENT ; `statut IN ('actif','archive')` NOT NULL sans défaut ; `idx_fournisseurs_statut` ; **aucun trigger**. Son en-tête prévoit que la protection de suppression sera la FK `RESTRICT` de `depenses.fournisseur_id` |
| `003_devis.sql` | `devis` | `numero` NOT NULL UNIQUE ; `statut IN ('en_attente','accepte','refuse','annule')` (pas de `brouillon`) ; `frozen_at` ; pas de colonne de révision |
| `003_devis.sql` | `devis_lignes`, `devis_ligne_garanties` | FK `devis_id` et `ligne_id` en **`CASCADE`** ; aucun trigger DELETE sur `devis` |
| `004_bons_commande.sql` | `bons_commande` | `devis_id INTEGER NOT NULL UNIQUE REFERENCES devis RESTRICT` (un devis = un BC) ; `statut IN ('en_cours','termine','annule')` ; `cancelled_at`, `motif_annulation`, `frozen_at`, `date_100_facture` |
| `004_bons_commande.sql` | `bc_lignes`, `bc_ligne_garanties` | `bc_lignes.bc_id` RESTRICT ; `devis_ligne_id` UNIQUE ; `UNIQUE(bc_id, ordre)` ; `bc_ligne_garanties.ligne_id` **CASCADE** |

### 1.2 Triggers existants

| Migration | Triggers |
|---|---|
| 001 | TR-90 (×2, `import_anomalies`), TR-95 (`numerotation_sequences`) |
| 002 | aucun |
| 003 | `tr_01_devis_numero_immuable` ; `tr_10_devis_modifiable`, `tr_10_devis_refuse_annule`, `tr_10_devis_gele` ; `tr_14_devis_frozen_at` ; `tr_11_*` ×6 (lignes et garanties) |
| 004 | `tr_01_bons_commande_numero_immuable` ; `tr_12_bons_commande_modifiable`, `_gele`, `_annule` ; `tr_14_bons_commande_frozen_at` ; `tr_17_bons_commande_insert` ; `tr_19_bons_commande_no_delete` ; `tr_18_devis_statut_avec_bc` (posé sur `devis`) ; `tr_13_*` ×6 ; `tr_96_numerotation_sequences_no_delete` |

### 1.3 Faits SQL qui conditionnent Dépenses

| Fait (SQL réel) | Constat |
|---|---|
| Un BC `annule` est **terminal** (`tr_12_bons_commande_annule` : seuls `updated_at` et le rattachement d'un client sont modifiables) | La règle ne protège que les **UPDATE de `bons_commande`**. Insérer ou rattacher une ligne de `depenses` ne touche pas `bons_commande` : **un BC annulé reste une cible valide** (vérifié, §9) |
| `tr_19_bons_commande_no_delete` : un BC ne se supprime jamais | Cohérent avec `depenses.bc_id` FK `RESTRICT` |
| 001–004 ne contiennent **aucun** `BEGIN`/`COMMIT`/`PRAGMA` exécutable (seuls les `BEGIN` de corps de triggers) | Compatible avec la règle « `user_version` écrit par le runner dans la transaction » |
| Les en-têtes 001–004 disent « `user_version = N` posé par le runner **après** succès » | Règle plus ancienne que D-55 (« dans la transaction, avant `COMMIT` »). Les fichiers étant immuables, l'en-tête reste ; **sans conflit** : pour les rangs 1 à 4, rang = numéro de fichier (valeurs 1, 2, 3, 4), donc une base déjà migrée à `user_version = 4` est lue correctement par la chaîne par rangs. Le runner n'existe pas encore (V-5) |

---

## 2. Écarts avec V3.13

Format : **fichier — objet — référence V3.13 — impact sur 005 — migration porteuse**. Les lignes renvoient au tableau §4.19 du modèle V3.13.

| # | Fichier — objet | Référence V3.13 / décision | Impact sur 005 | Migration porteuse |
|---|---|---|---|---|
| E-1 | `002` — `fournisseurs.statut` + `idx_fournisseurs_statut` | INV-183, E-12 (fournisseurs permanents, sans archive) ; §4.19 l.2 ; PT-3 | **Aucun.** 005 ne lit ni ne présuppose `fournisseurs.statut`. Aucune règle de Dépenses ne repose sur une archive (R6, R7 du cadrage : tout fournisseur reste sélectionnable) | **M-A / 005a** |
| E-2 | `001` — `clients.statut`, CHECK `a_rattacher`, `idx_clients_statut` | INV-183 ; §4.19 l.1 ; PT-3 | Aucun (`depenses` ne référence pas `clients`) | **M-A** (reconstruction) |
| E-3 | `001`/`002` — aucune garde DELETE ni immutabilité du `code` sur `clients`/`fournisseurs` | INV-183 ; §4.19 l.3 ; PT-4 | Aucun : la FK `RESTRICT` de `depenses.fournisseur_id` protège déjà le fournisseur référencé (comme le prévoit l'en-tête de 002) | **M-A** |
| E-4 | `003` — `devis.numero NOT NULL`, pas de `brouillon` | INV-180 ; §4.19 l.4 ; PT-2 | Aucun | **M-A** (reconstruction de `devis`) |
| E-5 | `003` — `tr_10_*` et `tr_11_*` (devis non modifiable après acceptation gelée, `refuse` non rouvrable) | INV-182, INV-196 ; §4.19 l.5, 6, 9 ; PT-2, PT-17, PT-21 | Aucun | **M-A** |
| E-6 | `003` — `devis_lignes.devis_id`, `devis_ligne_garanties.ligne_id` en CASCADE ; pas de garde DELETE sur `devis` | Q11, Q12, INV-06 ; §4.19 l.7 ; PT-5 | Aucun | **M-A** |
| E-7 | `003` — pas de révisions | INV-196 ; §4.19 l.21 ; PT-21 | Aucun | **M-A** (`devis.revision`, `revision_en_cours`, `devis_revisions`) |
| E-8 | `003`/`004` — `frozen_at` (devis et BC), TR-14, CHECK associés | PT-8 (**ouvert**) ; §4.19 l.8, 16 | **Aucun** : le cadrage 005 (§ « gelé ») n'écrit rien dans `bons_commande` et aucune règle de dépense ne dépend de `frozen_at` | M-A pour le devis (rangée dans le contenu proposé) ; **BC : aucune migration attribuée tant que PT-8 est ouvert** |
| E-9 | `004` — `bons_commande.devis_id UNIQUE NOT NULL` | INV-187 (1 BC → N devis) ; §4.19 l.10 ; PT-6 | **Aucun** : 005 ne référence que `bons_commande(id)`, jamais `devis_id` | **M-B / 005b** |
| E-10 | `004` — `remise_*`, `acompte_*` portés par le BC | INV-189, INV-192 ; §4.19 l.11 ; PT-7 | Aucun | **M-B** |
| E-11 | `004` — `tr_12_*` : BC annulé figé jusqu'aux caches | INV-188 ; §4.19 l.12 ; PT-16 | Aucun (cf. §1.3) | **M-B** |
| E-12 | `004` — `tr_13_*`, `tr_17`, `tr_18` lisent `bons_commande.devis_id` | PT-6 ; §4.19 l.13, 14, 15 | Aucun | **M-B** |
| E-13 | `004` — `bc_ligne_garanties.ligne_id` CASCADE | PT-5 ; §4.19 l.17 | Aucun | **M-B** |
| E-14 | `001` — numérotation : compteur SQL restauré par un rollback | PT-1 (tranché), INV-179 ; §4.19 l.19 | Aucun DDL : 005 ne crée ni ne modifie `numerotation_sequences` ; la réservation est une règle de **service** | Service (pas de migration) |
| E-15 | Tests 001–004 | §4.19 l.20 | Les tests de 003/004 vérifiant l'absence de `depenses` ne sont pas touchés | À adapter avec M-A / M-B |

**Aucun écart ne contredit un besoin de 005.** Les écarts ne concernent que des objets que 005 ne lit pas.

---

## 3. Corrections couvertes par 005a (M-A, rang 6)

*Contenu de M-A = proposition (PT-20, non validée). Place dans la chaîne = décision validée (D-55).*

### 3.1 Tableau demandé

| Élément | Migration historique concernée | Problème actuel | Correction prévue | Migration responsable |
|---|---|---|---|---|
| `fournisseurs.statut` + index | 002 | statut `actif/archive` | `DROP INDEX idx_fournisseurs_statut` puis `ALTER TABLE … DROP COLUMN statut`, sans reconstruction (PT-3) | 005a |
| `clients.statut`, CHECK, index | 001 | statut `actif/archive/a_rattacher` | reconstruction de `clients` (protocole §5) (PT-3) | 005a |
| Gardes `clients` / `fournisseurs` | 001, 002 | suppression et modification du `code` possibles | triggers DELETE refusé + `code` immuable (PT-4) | 005a |
| `devis.numero`, statut `brouillon` | 003 | numéro obligatoire | reconstruction de `devis` (PT-2) | 005a |
| `tr_10_*`, `tr_11_*` | 003 | `refuse` non rouvrable ; `accepte` non gelé modifiable | réécriture (PT-2, PT-17, PT-21) | 005a |
| CASCADE `devis_lignes`/`garanties`, DELETE devis | 003 | suppression d'un devis numéroté possible | `BEFORE DELETE` sur `devis` (brouillon seulement) ; cascade limitée au brouillon (PT-5) | 005a |
| Révisions | 003 (absentes) | pas de `revision`, pas de `devis_revisions` | `devis.revision`, `revision_en_cours`, table `devis_revisions` + TR-100 (PT-21) | 005a |
| `frozen_at` devis, TR-14 | 003 | gel progressif | adaptation (PT-8, ouvert) | 005a (à valider) |

### 3.2 Vérifications effectuées

| Vérification (SQLite 3.45.1, FK activées, `depenses` présente) | Résultat |
|---|---|
| `DROP COLUMN fournisseurs.statut` **sans** `DROP INDEX` préalable | **Refusé** (ordre `DROP INDEX` puis `DROP COLUMN` obligatoire) |
| `DROP INDEX` puis `DROP COLUMN` avec `depenses.fournisseur_id` qui référence `fournisseurs` | **Réussi** ; `foreign_key_check` vide ; FK de `depenses` intacte ; insertion d'une dépense avec fournisseur encore acceptée ; 3 triggers et 4 index de `depenses` intacts |
| `DROP COLUMN clients.statut` direct | **Refusé** (CHECK et index) → reconstruction réellement nécessaire |
| Reconstruction de `clients` **sans** retirer d'abord les triggers dépendants | **Échoue** au `RENAME` (`error in trigger tr_10_devis_refuse_annule: no such table: main.clients`) ; rollback complet, schéma inchangé |
| Reconstruction de `clients` **avec** retrait des triggers dépendants (protocole §5) | **Réussit** ; `foreign_key_check` vide |

### 3.3 Points de couverture à consigner (non bloquants pour 005)

**G-1 — La reconstruction de `clients` oblige M-A à retraiter deux triggers de 004 rangés en M-B.**
- *Fait mesuré* : quatre triggers lisent `clients.statut` : `tr_10_devis_refuse_annule` et `tr_10_devis_gele` (003, rangés en M-A), mais aussi **`tr_12_bons_commande_gele` et `tr_12_bons_commande_annule` (004, §4.19 l.12 les range en M-B)**. Une fois `statut` retiré, ils sont **recréables mais plus exécutables** : la création réussit, le déclenchement échoue (`no such column: statut`, vérifié sur un `UPDATE devis`).
- *Conséquence* : M-A (rang 6) doit retirer puis **recréer** `tr_12_*_gele` et `tr_12_*_annule` sans la clause `a_rattacher`, sinon le schéma au rang 6 est inutilisable pour `bons_commande` jusqu'à M-B.
- *Nature* : déduction technique de INV-183 (suppression de `a_rattacher`) ; ce n'est pas une nouvelle règle métier. L'adaptation de fond (PT-16) reste dans M-B.
- *Impact 005* : aucun.

**G-2 — La reconstruction de `devis` oblige M-A à retraiter `tr_17` et `tr_18` de 004.**
- *Fait mesuré* : `DROP TABLE devis` supprime avec elle `tr_18_devis_statut_avec_bc` (posé sur `devis`), et le `RENAME` échoue tant que `tr_17_bons_commande_insert` (posé sur `bons_commande`, lit `devis`) n'est pas retiré. Même cas pour les six `tr_11_*` (couverts par M-A).
- *Conséquence* : M-A doit recréer `tr_17` et `tr_18` au rang 6 avec la logique actuelle (`bons_commande.devis_id` existe encore à ce rang) ; M-B les réécrit ensuite (§4.19 l.14, 15).
- *Nature* : déduction technique du protocole de reconstruction (conventions §5, étape « supprimer les triggers dépendants, y compris ceux d'autres tables »).
- *Impact 005* : aucun.

**Où le consigner** : dans le contenu proposé de M-A (§17.1 du modèle, ligne `005a`) et dans le futur écran de validation de PT-20. **Aucune modification documentaire n'a été faite par ce rapport.**

---

## 4. Corrections couvertes par 005b (M-B, rang 7)

### 4.1 Tableau demandé

| Élément | Migration historique concernée | Problème actuel | Correction prévue | Migration responsable |
|---|---|---|---|---|
| `bons_commande.devis_id UNIQUE NOT NULL` | 004 | 1 devis = 1 BC | table `bc_devis`, reprise des liens, reconstruction de `bons_commande` sans `devis_id` (PT-6) | 005b |
| `remise_*`, `acompte_*` | 004 | une remise et un acompte par BC | par devis (PT-7) | 005b |
| `tr_12_*` | 004 | BC annulé figé jusqu'aux caches | adaptation (PT-16) | 005b |
| `tr_13_*` | 004 | lit `devis_id` ; INSERT refusé si gelé/annulé | adaptation (PT-6, PT-8) | 005b |
| `tr_17_bons_commande_insert` | 004 | lit `devis_id` | lecture via `bc_devis` (PT-6) | 005b |
| `tr_18_devis_statut_avec_bc` | 004 | lit `bons_commande.devis_id` | réécriture via le lien (PT-6) | 005b |
| `bc_ligne_garanties.ligne_id` | 004 | CASCADE | `RESTRICT` par reconstruction (PT-5) | 005b |
| `bc_lignes UNIQUE(bc_id, ordre)` | 004 | — | **aucune structure à changer** (§4.19 l.18) | — |
| `frozen_at` du BC | 004 | gel progressif | PT-8 (ouvert) | non attribuée |

### 4.2 Vérifications effectuées

| Vérification (reconstruction de `bons_commande` sans `devis_id`, `depenses` et `bc_lignes` présentes) | Résultat |
|---|---|
| Protocole §5 (FK OFF, retrait des triggers dépendants, copie des `id`, `DROP`, `RENAME`) | **Réussit** ; `sqlite_sequence` conservée (2 → 2) ; `foreign_key_check` vide |
| `depenses.bc_id` après M-B | référence toujours `bons_commande(id)` **ON DELETE RESTRICT** ; `bc_id` inexistant refusé ; `bc_id` existant accepté |
| 3 triggers de `depenses` (TR-01, TR-101, TR-102) après M-B | **intacts** : aucun ne référence `bons_commande` |
| `DROP TABLE bons_commande` avec FK actives | **Refusé** (`FOREIGN KEY constraint failed`) → `foreign_keys=OFF` hors transaction obligatoire |
| `RENAME` sans retrait des triggers dépendants | **Échoue** (`error in trigger tr_18_devis_statut_avec_bc: no such table: main.bons_commande`) |
| Colonne `devis_id` après M-B | retirée ; 005 ne la référence pas |

Triggers que le protocole retire puis recrée pour reconstruire `bons_commande` (mesure) : 7 propres à la table (`tr_01`, `tr_12`×3, `tr_14`, `tr_17`, `tr_19`) et 7 posés ailleurs (`tr_18` sur `devis`, `tr_13`×6).

### 4.3 Point de couverture à consigner (non bloquant pour 005)

**G-3 — Trois triggers du BC ne sont nommés dans aucune ligne de §4.19.** `tr_01_bons_commande_numero_immuable`, `tr_14_bons_commande_frozen_at` et `tr_19_bons_commande_no_delete` sont supprimés avec la table et doivent être recréés par M-B (identiques ou adaptés selon PT-8). Le protocole les recrée implicitement, mais ils ne figurent pas dans la liste du contenu proposé. À ajouter à la ligne `005b`. **Impact 005 : aucun** (`tr_19` est même cohérent avec le `RESTRICT` de `depenses.bc_id`).

---

## 5. Dépendances de 005

### 5.1 Dépendances réelles du DDL de `depenses` (transcription temporaire du cadrage)

| Dépendance | Cible | Créée par | Rang | Stable à travers 005a/005b ? |
|---|---|---|---|---|
| `fournisseur_id` → `fournisseurs(id)` ON DELETE RESTRICT | clé primaire | 002 | 2 | **Oui** : M-A fait seulement `DROP INDEX` + `DROP COLUMN statut`, sans reconstruction |
| `bc_id` → `bons_commande(id)` ON DELETE RESTRICT | clé primaire | 004 | 4 | **Oui** : M-B reconstruit la table mais conserve `id` ; nom et clé inchangés (vérifié) |
| `categorie_id` → `categories_depenses(id)` ON DELETE RESTRICT | clé primaire | 001 | 1 | **Oui** : jamais modifiée |
| numéro `DEP-nnnnn-yy` | `numerotation_sequences` (type `DEP`) | 001 | 1 | **Oui** : service ; aucun DDL |

### 5.2 Ce que 005 ne doit pas lire (vérifié dans le DDL transcrit)

Aucune occurrence de `statut`, `devis_id`, `frozen_at`, `a_rattacher`, `clients`, `bc_devis`. Le DDL ne contient ni `BEGIN`/`COMMIT` de fichier, ni `PRAGMA`, ni `INSERT`, ni reconstruction de table. Les triggers de `depenses` (TR-01, TR-101, TR-102) ne lisent **aucune autre table**.

### 5.3 Contrôles demandés

| Contrôle | Résultat |
|---|---|
| 005 appliquée **après 004 et avant 005a/005b** | **OK** (rang 5), 32/32 vérifications OK |
| DDL de 005 valide aussi si exécuté **après** 005a/005b (aucune dépendance cachée dans l'autre sens) | **OK** (avec des correctives simulées) |
| BC `annule` : création et rattachement ultérieur d'une dépense | **OK** (aucun trigger de 004 n'est déclenché par un INSERT/UPDATE sur `depenses`) |
| Dépense annulée immuable (TR-102), DELETE refusé (TR-101), unicité du `numero` | **OK** |
| Aucune règle de Dépenses ne repose sur une archive fournisseur | **OK** (R6/R7, cadrage §3.1 ; 005 ne lit pas `fournisseurs.statut`) |

**Note pour le futur `test_005`** (cadrage, déjà prévue) : tant que 002 impose `fournisseurs.statut NOT NULL`, les fixtures du test doivent fournir cette valeur sans la commenter. Après M-A, la colonne disparaît : les fixtures du test 005 (chaîne 001 → 005 seulement) restent valides, mais toute campagne de test sur la chaîne complète devra insérer les fournisseurs **sans** `statut`.

---

## 6. Vérification de l'ordre des migrations

### 6.1 Chaîne et rangs

| Rang = `user_version` | Fichier | Nature | Dépend de (rangs) |
|---|---|---|---|
| 1 | `001_initial.sql` | tranche | — |
| 2 | `002_fournisseurs.sql` | tranche | 1 |
| 3 | `003_devis.sql` | tranche | 1 |
| 4 | `004_bons_commande.sql` | tranche | 1, 3 |
| 5 | `005_depenses.sql` | tranche | 1, 2, 4 |
| 6 | `005a_corrections_v313.sql` | corrective M-A | 1, 2, 3, 4, 5 |
| 7 | `005b_bc_multi_devis.sql` | corrective M-B | 3, 4, 6 (et 5 par la FK `depenses.bc_id`) |
| 8 à 12 | `006` à `010` | tranches (non conçues) | ≥ 7 |

Les rangs 8 à 12 (006 à 010) ne sont pas conçus : seule la contrainte d'ordre est vérifiée (elles viennent après 005b et peuvent donc supposer le schéma corrigé).

### 6.2 Résultats de la simulation (runner par rangs, N = 7, correctives simulées)

| Vérification | Résultat |
|---|---|
| Base neuve 001 → 005b : `user_version = 7`, `foreign_key_check` vide | **OK** |
| Base ayant appliqué 001–004 (`user_version = 4`) puis suite 5, 6, 7 : `user_version = 7` | **OK** |
| Schéma (`sqlite_master`) identique entre base neuve et base 001–004 + suite | **OK** (55 objets) |
| Réexécution sur une base à 7 : rien appliqué | **OK** |
| Base à rang 9 > N = 7 : refus, aucune migration appliquée | **OK** |
| Graphe de dépendances : acyclique, chaque dépendance de rang strictement inférieur | **OK** |
| Conflit entre tranche métier et corrective | **Aucun** (005 n'utilise que des clés primaires stables) |

**Limite à connaître** : `005a` et `005b` n'existent pas. Les deux scripts simulés (retrait de `fournisseurs.statut` ; reconstruction de `bons_commande` sans `devis_id`) servent uniquement à éprouver l'ordre, les rangs et la stabilité des FK de Dépenses ; ils ne valident pas le contenu de M-A/M-B (PT-20 reste à valider). L'égalité de schéma « neuve / 001–004 + suite » démontre la logique par rangs, non la qualité des futures correctives.

### 6.3 Points techniques de l'ordre

- Dans la même transaction que la migration : `user_version` avant `COMMIT` ; un échec annule aussi le rang. Le fichier ne contient ni `BEGIN`/`COMMIT` ni `PRAGMA` (conventions §5, D-55). Le runner n'existe pas (V-5) : cette vérification suppose son comportement documenté.
- `PRAGMA foreign_keys=OFF` doit être posé **hors transaction** avant les reconstructions de M-A et M-B (le protocole le prévoit) ; `recursive_triggers=ON` reste obligatoire.
- SQLite : `STRICT` (≥ 3.37) est déjà exigé par 001, ce qui implique `DROP COLUMN` (≥ 3.35) disponible. **La version minimale embarquée dans Tauri reste inconnue (V-7)** : non bloquant pour 005, à confirmer avant 005a.

---

## 7. Éventuels blocages

| Type | Constat |
|---|---|
| **Bloquant d'ordre des migrations** | **Aucun.** Aucune correction de 002, 003 ou 004 n'est nécessaire avant 005 |
| Bloquant de contenu pour 005 | **Aucun** |
| Points de couverture de 005a/005b | **G-1, G-2, G-3** (§3.3, §4.3) : à consigner dans le contenu proposé de M-A/M-B ; sans effet sur 005 |
| Ouverts hors 005, hérités | PT-8 (`frozen_at` du BC, sans migration attribuée) ; V-5 (runner) ; V-6 (bases V6 avec données) ; V-7 (version SQLite minimale) ; PT-20 (contenu de M-A/M-B à valider) ; adaptation des tests 001–004 (§4.19 l.20) |

---

## 8. Conclusion

# **GO** — `005_depenses.sql` peut être conçue et écrite

- Elle s'applique proprement après 004, au rang 5, et reste valide si 005a/005b sont appliquées après ou avant elle.
- Elle ne dépend d'aucune structure que 005a ou 005b crée, retire ou reconstruit : uniquement les clés primaires `id` de `fournisseurs`, `bons_commande` et `categories_depenses`, et le type `DEP` de `numerotation_sequences`.
- La reconstruction de `bons_commande` par M-B ne casse ni `depenses.bc_id` ni les triggers de `depenses` ; la suppression de `fournisseurs.statut` par M-A ne casse pas `depenses.fournisseur_id`.
- Un BC annulé reste une cible valide d'une dépense (création et rattachement ultérieur).
- L'ordre officiel 001 → 005 → 005a → 005b → 006 → … → 010 n'est pas modifié.

**Avant d'écrire 005a (et non avant 005)** : consigner G-1, G-2 et G-3 dans le contenu proposé de M-A et M-B, et lever V-7 et PT-8 si M-A/M-B doivent y toucher.

---

## 9. Traçabilité des vérifications

| Point | Détail |
|---|---|
| Fichiers du dépôt modifiés | **Aucun** ; `git status` vide avant la rédaction du présent rapport ; **aucun commit, aucun push** |
| Fichiers créés dans le dépôt | **Uniquement ce rapport** |
| Fichiers temporaires | tous dans un répertoire de travail hors dépôt (transcription temporaire du cadrage pour 005, scripts d'expériences, bases jetables) ; **aucun test permanent** |
| 005 sur 001–004 | 32 vérifications sur 32 OK (fixtures réelles de `test_004` importées sans écriture) : application, FK, numérotation `DEP`, BC annulé, TR-101, TR-102 |
| Simulations M-A / M-B | 25 vérifications OK sur 27. Les deux écarts sont des **erreurs de mon test, pas de schéma** : (1) la recréation des triggers à l'identique **réussit** et c'est leur **déclenchement** qui échoue (re-mesuré : `no such column: statut`) ; (2) la détection de `BEGIN` a pris pour une transaction le `BEGIN` des corps de triggers |
| Chaîne par rangs | 9 vérifications OK sur 9 ; un contrôle de présence de `BEGIN`/`PRAGMA` dans 001–004 a signalé à tort les mêmes `BEGIN` de triggers, recontrôlé par une recherche ciblée (`BEGIN IMMEDIATE/TRANSACTION`, `COMMIT`, `PRAGMA` : **aucune occurrence**) |
| Non vérifié | contenu réel de `005a`/`005b` (inexistants) ; reconstruction de `devis` jusqu'au `foreign_key_check` (hors dépendances de Dépenses) ; runner réel (V-5) ; SQLite minimal embarqué (V-7) |

**Risque** : si M-A est écrite sans retraiter `tr_12_*`, `tr_17` et `tr_18` (G-1, G-2), le schéma au rang 6 compile mais échoue au premier `UPDATE` sur `devis` ou `bons_commande`, et la panne n'apparaît qu'au déclenchement.
**Micro-amélioration** : consigner G-1 à G-3 dans le contenu proposé de M-A/M-B (§17.1 du modèle) avant de rédiger `005a`, avec un test qui déclenche chaque trigger recréé.
