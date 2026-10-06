# BATORYA Essentiel V6 — Conventions techniques et de code

**Version : 0.6 (en relecture, 2026-10-04) — document évolutif**  
**Périmètre : conventions techniques de développement V6**

## 1. Objet

Ce document définit les conventions techniques applicables au code de BATORYA Essentiel V6.

Il complète les documents de référence fonctionnels et architecturaux. Il ne remplace ni le CDC, ni le modèle de données SQLite, ni le registre des invariants, ni le modèle métier.

Son objectif est de maintenir une arborescence cohérente et prévisible pendant l’implémentation.

Le document est volontairement évolutif : les conventions seront complétées au fur et à mesure de l’avancement réel du développement, sans créer prématurément une architecture non nécessaire.

## 2. Documents de référence

Avant toute implémentation ou modification structurelle, les références suivantes doivent être considérées dans cet ordre de priorité métier et architectural :

1. `docs/specifications/cdc-fonctionnel-architectural-v6.md`
2. `docs/conception/modèle-données-sqlite-v6-v3.13.md` (V3.13 en relecture ; dernier modèle validé : V3.12)
3. `docs/conception/invariants.md`
4. `docs/conception/modèle-métier-V6.md`
5. `docs/décisions/cdc-errata-v6.md` pour la traçabilité historique uniquement.

Une convention de code ne peut pas contredire ces documents.

## 3. Règle générale de création des fichiers

Un nouveau fichier ne doit pas être créé à un emplacement arbitraire.

Pour chaque nouveau fichier, son nom et son emplacement doivent être cohérents avec :

- sa responsabilité ;
- la couche à laquelle il appartient ;
- la convention déjà établie pour le module concerné ;
- les conventions présentes dans ce document.

Si une nouvelle catégorie de fichier ou une nouvelle branche d’arborescence devient nécessaire, elle est d’abord définie dans ce document avant de devenir une convention permanente.

Les fichiers temporaires de travail ne doivent pas être ajoutés au dépôt sous un nom ambigu ou générique.

## 4. Arborescence technique actuelle

L’arborescence technique actuellement validée est volontairement minimale :

```text
src-tauri/
├── migrations/
│   ├── machine/
│   │   └── 001_initial.sql
│   └── metier/
│       ├── 001_initial.sql
│       ├── 002_fournisseurs.sql
│       ├── 003_devis.sql
│       └── 004_bons_commande.sql
│
└── tests/
    ├── machine/
    │   └── test_premier_demarrage.py
    └── metier/
        ├── test_001_initial.py
        ├── test_002_fournisseurs.py
        ├── test_003_devis.py
        └── test_004_bons_commande.py
```

Cette arborescence sera complétée lorsque les premières implémentations Rust, SQLite métier et interfaces applicatives seront réellement introduites.

Aucune arborescence supplémentaire n’est imposée à ce stade sans besoin concret.

## 5. Migrations SQLite

Les migrations SQLite sont versionnées et séquentielles.

La migration initiale de `machine.db` est :

```text
src-tauri/migrations/machine/001_initial.sql
```

Règles :

- l'ordre des migrations est celui d'une **chaîne ordonnée et figée** ; le **rang** d'une migration dans cette chaîne (et non le préfixe de son nom de fichier) est la version du schéma (voir « Chaîne ordonnée, rang et `user_version` » ci-dessous) ;
- le nom d’une migration déjà créée ne doit jamais être changé pour convenance ;
- une migration déjà appliquée n’est pas réécrite pour modifier rétroactivement le schéma ;
- une évolution de schéma donne lieu à une nouvelle migration ; **c'est aussi le cas d'une correction structurelle décidée après coup** : lorsqu'une décision métier validée contredit une migration déjà appliquée (écarts listés au §4.19 du modèle de données V3.13), la migration existante n'est jamais réécrite ; la correction est portée par une migration ultérieure (par exemple reconstruction d'une table dans SQLite, réécriture d'un trigger), après passage du modèle à la version correspondante ;
- les migrations ne contiennent pas de logique métier applicative ;
- le runner de migrations est responsable de la transaction et de la mise à jour de `PRAGMA user_version`, effectuée **dans la même transaction que la migration, avant son `COMMIT`** (voir « Transaction et `user_version` ») ; ce runner **n'existe pas encore** : il relève d'un chantier technique distinct des tranches métier (décision V-5) ;
- une migration ne doit pas introduire de trigger ou de contrainte qui contredit les invariants ou les responsabilités explicitement attribuées aux services.

### Migrations de la base métier

La base métier a ses propres migrations, séparées de celles de `machine.db` :

```text
src-tauri/migrations/metier/001_initial.sql
src-tauri/migrations/metier/002_fournisseurs.sql
src-tauri/migrations/metier/003_devis.sql
src-tauri/migrations/metier/004_bons_commande.sql
```

Ces quatre fichiers sont les seules migrations métier **existantes** (rangs 1 à 4). Les migrations suivantes sont décrites dans la chaîne ordonnée ci-dessous ; elles n'existent pas encore.

Règles :

- une migration correspond à une tranche du schéma définie dans le suivi des migrations du modèle de données SQLite ; elle contient les tables de la tranche, avec leurs triggers et leurs index ;
- la première migration métier s’appelle `001_initial.sql`. Il n'existe que **deux catégories** de migrations métier, distinguées par leur nom (décision V-2) :
  - une **tranche métier** : `NNN_<objet>.sql` (trois chiffres, objet en minuscules sans accent) ; elle porte les tables d'un objet métier ; son préfixe `NNN` est son **étiquette de tranche** dans l'ordre métier réservé (001 → 010) ;
  - une **migration corrective** : `NNNx_<objet>.sql` (trois chiffres suivis d'**une lettre minuscule**, objet en minuscules sans accent) ; elle corrige ou fait évoluer le schéma déjà livré sans être une tranche métier. Le préfixe `NNN` est celui de la **dernière tranche exécutée avant elle** ; la lettre ordonne les correctives rattachées à la même tranche (`005a` avant `005b`, `005b` avant `005c`). Exemples prévus : `005a_corrections_v313.sql`, `005b_bc_multi_devis.sql` (M-A et M-B) et `005c_bc_annule_caches_financiers.sql` (D-56) ne sont **pas** des tranches supplémentaires : elles ne consomment aucun numéro de tranche et ne décalent aucune tranche ;
  - aucune autre catégorie de nom n'existe (pas de « migration technique » nommée à part, pas de suffixe libre) ;
- le modèle de données SQLite passe à la version suivante et est mis à jour **avant** la création ou la modification d’une migration ; l’en-tête de la migration cite la version du modèle ;
- une migration n’insère **aucune donnée métier initiale** : listes de référence, catalogue par défaut et singletons relèvent du jeu de données d’installation ou du service d’initialisation (l’emplacement du jeu de données sera défini dans ce document lorsqu’il sera introduit). La **copie technique** de données existantes lors d'une reconstruction de table est distincte et permise (voir « Données dans une migration ») ;
- noms SQL : triggers `tr_<NN>_<table>_<règle>` où `NN` est le numéro `TR-NN` du modèle ; index `idx_<table>_<colonnes>` ; les contraintes `UNIQUE` de colonnes restent déclarées dans la table ;
- chaque migration métier est livrée avec son test (section 7).
- le dépôt existant (migrations, tests, anciens modèles) est une **matière d'audit**, non une vérité normative : en cas de contradiction avec une décision métier validée, la décision prévaut et l'écart est documenté avant toute correction.

### Chaîne ordonnée, rang et `user_version`

*Nature : décisions V-1 à V-5 validées le 2026-10-04 (règles de versionnement) ; l'algorithme de sélection est une Déduction technique de ces règles. Le runner n'existant pas, rien de ce qui suit n'est encore exécuté ; les tests existants (001–004) émulent le runner et posent `PRAGMA user_version = {numéro}`, ce qui est exact pour les rangs 1 à 4.*

**Chaîne ordonnée de la base métier.** La liste ci-dessous est la liste de référence. Le **rang** est la position dans la liste (à partir de 1) :

| Rang | Fichier | Catégorie | État |
|---|---|---|---|
| 1 | `001_initial.sql` | tranche | livrée |
| 2 | `002_fournisseurs.sql` | tranche | livrée |
| 3 | `003_devis.sql` | tranche | livrée |
| 4 | `004_bons_commande.sql` | tranche | livrée |
| 5 | `005_depenses.sql` | tranche (Dépenses) | prévue, non créée |
| 6 | `005a_corrections_v313.sql` | corrective (M-A) | prévue, non créée ; contenu en proposition (modèle §17.1, PT-20) |
| 7 | `005b_bc_multi_devis.sql` | corrective (M-B) | prévue, non créée ; contenu en proposition |
| 8 | `005c_bc_annule_caches_financiers.sql` | corrective (D-56) | livrée (test T-47) ; adaptation de `tr_12_bons_commande_annule` (modèle §17.1, PT-16) |
| 9 | `006_facturation.sql` | tranche (Facturation) | prévue |
| 10 | `007_reglements.sql` | tranche (Règlements) | prévue |
| 11 | `008_garanties.sql` | tranche (Garanties) | prévue |
| 12 | `009_pv.sql` | tranche (PV) | prévue |
| 13 | `010_planification.sql` | tranche (Planification) | prévue |

- L'**ordre métier réservé** des tranches est 001 Initial → 002 Fournisseurs → 003 Devis → 004 Bons de commande → 005 Dépenses → 006 Facturation → 007 Règlements → 008 Garanties → 009 PV → 010 Planification (V-1). Les noms des tranches 006 à 010 sont des **réservations** d'ordre ; l'intitulé exact du fichier sera fixé à sa création, avec le modèle (§17.1).
- Les correctives M-A et M-B s'exécutent **après 005 et avant 006** (V-4) ; la corrective 005c (D-56) s'exécute après 005b et avant 006.
- Une corrective future suit la même règle : une `010a_*` aurait le rang 14.
- Le rang d'une migration **n'est pas son numéro de fichier** : `006_facturation.sql` a le rang 9 (`005c_bc_annule_caches_financiers.sql` a le rang 8).
- La chaîne de `machine.db` est **distincte** (son propre `user_version`, sa propre liste) ; elle ne comporte aujourd'hui que `machine/001_initial.sql` (rang 1). Les règles ci-dessous s'y appliquent de la même façon.

**`PRAGMA user_version` = rang de la dernière migration appliquée** (0 = base vierge). Exemple : `user_version = 7` signifie que les **sept premières** migrations de la chaîne ont été appliquées, `005b_bc_multi_devis.sql` incluse ; la suivante à appliquer est de rang 8 (`005c_bc_annule_caches_financiers.sql`). Il n'existe **aucune seconde source de vérité** (pas de `schema_version` dans chaque fichier, pas de colonne de suivi) : la liste ordonnée fait foi.

**Invariants de la chaîne (append-only).** Dès qu'une migration est livrée :
1. elle n'est jamais renommée, supprimée, ni déplacée dans la liste ; son rang est définitif ;
2. une nouvelle migration est **ajoutée à la fin** de la liste uniquement ; aucune migration n'est insérée entre deux migrations déjà livrées ;
3. l'historique est immuable : les anciens contenus ne sont jamais réécrits (déjà posé ci-dessus) ;
4. ces règles sont nécessaires au déterminisme : pour une même base à un rang donné, la même suite de migrations doit s'appliquer sur toute installation et à chaque restauration.

*Conséquence documentaire* : tant qu'aucune de 005/005a/005b/005c/006… n'est livrée, la liste du tableau ci-dessus peut encore être ajustée par décision ; **après livraison d'une migration, cette ligne est figée**. La ligne de la corrective `005c` (rang 8) est figée : la migration est livrée.

**Algorithme de sélection des migrations à appliquer** (installation, mise à jour de l'application, restauration). Soit `k` = `PRAGMA user_version` de la base, `N` = rang maximal supporté par l'application (longueur de sa liste) :
1. si `k > N` : **refus** (base produite par une version plus récente de l'application) ; aucune écriture ;
2. sinon, appliquer **une par une, dans l'ordre**, les migrations de rang `k+1` à `N` ; chacune dans sa propre transaction (voir ci-dessous) ;
3. si l'une échoue, elle est annulée entièrement (y compris `user_version`) ; les suivantes ne sont pas tentées ; la base reste au rang de la dernière migration réussie ;
4. si `k = N`, il n'y a rien à appliquer.

*Hors périmètre* : la forme exécutable de la liste (manifeste du runner) et son emplacement, la déclaration au runner qu'une migration est une reconstruction (qui exige `foreign_keys=OFF`, voir le protocole ci-dessous), le contrôle automatique que l'ordre de la liste correspond à l'ordre lexicographique des noms de fichiers (**proposition** de test de garde) : ils relèvent du chantier runner (V-5), à concevoir et à tester séparément.

### Transaction et `user_version`

*Nature : règle validée (décision du 2026-10-04) ; déduction vérifiée (expérience T1 : `user_version` est transactionnel — un `ROLLBACK` restaure l'ancienne valeur, un `COMMIT` conserve la nouvelle).*

La mise à jour de `PRAGMA user_version` est effectuée **dans la même transaction que la migration, avant son `COMMIT`**. Séquence d'une migration :

```text
BEGIN → exécution du SQL de la migration → contrôles → PRAGMA user_version = nouveau_rang → COMMIT
```

- un échec (SQL ou contrôle) entraîne un `ROLLBACK` intégral : le schéma **et** `user_version` reviennent à leur valeur d'avant ;
- cette règle supprime la fenêtre où un arrêt entre le `COMMIT` et l'écriture de `user_version` laisserait une base migrée avec un rang périmé (la migration serait alors rejouée au démarrage suivant) ;
- `nouveau_rang` est le **rang** de la migration dans la chaîne, jamais son préfixe de fichier ;
- les fichiers de migration restent sans `BEGIN`, `COMMIT` ni `PRAGMA` : tout ce paragraphe est de la responsabilité du runner. Les en-têtes de 001–004 indiquent « `user_version` posé par le runner après succès » ; ils sont **immuables** (migrations livrées) et doivent se lire désormais selon cette règle. De même, les fonctions d'application des tests 001–004 (émulation du runner : `COMMIT` puis `PRAGMA user_version = {numéro}`) restent inchangées : elles décrivent l'ancien ordre « après succès » et un rang égal au numéro de fichier (exact pour les rangs 1 à 4) ; l'écriture dans la transaction et le rang des migrations suivantes seront exercés par les tests du runner (chantier V-5) et par les helpers des tests des futures migrations, qui poseront le **rang**.

### Protocole de reconstruction de table

*Nature : convention technique générale (Déduction technique), établie par expérience sur SQLite 3.45.1 avec le DDL réel de 001–004 (données synthétiques : mécanique uniquement). La version minimale du SQLite embarqué n'est pas fixée par la documentation ; `STRICT` impose au moins 3.37 et `DROP COLUMN` au moins 3.35 — **à confirmer** (point ouvert, V-7).*

*Quand reconstruire.* SQLite n'a pas d'`ALTER COLUMN`. On reconstruit une table lorsque la modification ne s'exprime pas autrement : retrait d'une colonne portée par un `CHECK` de table ou une contrainte `UNIQUE`, passage `NOT NULL` → nullable, changement d'une clause `ON DELETE`. Lorsque `ALTER TABLE … DROP COLUMN` suffit (colonne sans `CHECK` de table, sans `UNIQUE`/`PRIMARY KEY`, sans index — l'index est d'abord supprimé), **on ne reconstruit pas** : moins de risque, aucun effet sur les clés étrangères entrantes.

*Pourquoi `foreign_keys=OFF` est indispensable, et hors transaction.* Avec `foreign_keys=ON`, `DROP TABLE` sur une table parente soit échoue (lignes enfants protégées par une FK `RESTRICT`), soit supprime **silencieusement** les lignes enfants liées en `ON DELETE CASCADE` (vérifié : `devis_lignes` perdues en supprimant `devis`). Ce n'est donc pas un confort : sans `OFF`, la reconstruction d'un parent est soit impossible, soit destructrice. Or `PRAGMA foreign_keys` est **sans effet à l'intérieur d'une transaction** (aucune erreur, aucun changement) : le réglage doit être posé **avant** `BEGIN` et vérifié.

*Protocole en 17 étapes* (les étapes 4 à 11 sont le SQL de la migration ; les autres relèvent du runner) :

1. **Hors transaction**, `PRAGMA foreign_keys = OFF`.
2. **Hors transaction**, relire `PRAGMA foreign_keys` : la valeur doit être `0`. Sinon, abandon avant toute écriture.
3. `BEGIN IMMEDIATE`.
4. Supprimer (`DROP TRIGGER`) **tous les triggers qui référencent la table reconstruite**, y compris ceux posés sur **d'autres tables** (exemple réel : `tr_18_devis_statut_avec_bc`, posé sur `devis`, référence `bons_commande`). Sans cela, le renommage de l'étape 9 échoue (« error in trigger … no such table »).
5. Créer la nouvelle table sous un nom provisoire, avec sa structure cible complète (contraintes, `CHECK`, FK).
6. Copier les données : `INSERT INTO nouvelle (colonnes) SELECT … FROM ancienne`, en **conservant strictement les `id`** (colonne `id` copiée explicitement) : les clés étrangères entrantes ne sont pas modifiées. Les triggers de la table n'étant pas encore recréés, la copie ne déclenche aucune garde (voulu : c'est une copie technique, pas une écriture métier).
7. **`sqlite_sequence` explicite** : relever avant la copie la valeur de `sqlite_sequence` de l'ancienne table, puis garantir après la copie que la nouvelle valeur est **supérieure ou égale** (mise à jour ou insertion de la ligne). Une reconstruction « naïve » peut la **faire régresser** (vérifié : 2 → 1), ce qui permettrait de réattribuer l'`id` d'une ligne supprimée et violerait **INV-04** (un `id` n'est jamais réutilisé). La monotonie de `sqlite_sequence` est une **exigence du protocole**, pas une option.
8. `DROP TABLE` de l'ancienne table (ses index et ses triggers propres disparaissent avec elle).
9. `ALTER TABLE nouvelle RENAME TO ancienne` : les **noms de table sont conservés**, les FK entrantes (qui désignent le nom) restent valides.
10. Recréer les **index** de la table.
11. Recréer les **triggers** supprimés à l'étape 4 et ceux de la table (dans leur forme cible), y compris sur les autres tables.
12. `PRAGMA foreign_key_check` : le résultat doit être **vide**.
13. **Échec** (erreur à l'une des étapes 4 à 12, ou résultat non vide à l'étape 12) : `ROLLBACK` **intégral** (schéma, données, `sqlite_sequence`, `user_version`) ; le runner remet `foreign_keys=ON` (étape 16) et signale l'échec ; la base est inchangée (vérifié : orphelin injecté ⇒ `ROLLBACK`, base et `user_version` inchangés).
14. Écrire `PRAGMA user_version = nouveau_rang` **dans la transaction**.
15. `COMMIT`.
16. **Hors transaction**, `PRAGMA foreign_keys = ON`.
17. Relire `PRAGMA foreign_keys` : la valeur doit être `1` (FK effectivement actives) avant de rendre la connexion à l'application.

*Plusieurs tables dans une même migration corrective* : une seule transaction et une seule séquence `OFF` … `ON` ; chaque table suit les étapes 4 à 11 ; l'étape 12 contrôle l'ensemble.

*Limites.* Les expériences ont employé des lignes synthétiques (contrôles désactivés pour la mécanique) : le protocole doit être rejoué par un test de la migration corrective concernée, sur des données représentatives, avant livraison. La déclaration au runner qu'une migration est une reconstruction est à concevoir (V-5).

### Données dans une migration

Trois cas se distinguent ; **aucune nouvelle catégorie métier** n'est créée par cette distinction :

| Cas | Statut | Exemple |
|---|---|---|
| **Données métier initiales** (listes de référence, catalogue par défaut, singletons, séquences) | **interdit** dans une migration d'installation ; relève du jeu de données d'installation ou du service d'initialisation | catégories par défaut ; `numerotation_sequences` ; singletons de `machine.db` |
| **Copie technique** de données existantes lors d'une reconstruction | **permise** : `INSERT INTO nouvelle_table (…) SELECT … FROM ancienne_table`, ids conservés ; aucune valeur inventée ni calculée par une règle métier | reconstruction de `clients`, `devis`, `bons_commande` |
| **Migration de données volontaire** (transformer des lignes existantes d'une façon qui change leur forme) | **permise seulement** si elle est décidée explicitement, documentée dans le modèle (source, règle, contrôle) et testée sur la chaîne | reprise des liens `bons_commande.devis_id` vers `bc_devis` (M-B) — contenu en proposition, non validé |

Une migration n'insère donc jamais de ligne « métier » nouvelle ; elle ne fait que recopier ou transformer fidèlement les lignes existantes.

### Restauration d'une sauvegarde plus ancienne

Une restauration applique **la même chaîne qu'une installation** (voir « Algorithme de sélection »). Les « migrations nécessaires » sont celles dont le **rang** est strictement supérieur au `user_version` de la copie restaurée :
1. lire `user_version` = `k` de la sauvegarde (sur une copie temporaire) ;
2. si `k > N` : **refus** (la sauvegarde provient d'une version plus récente de l'application) ;
3. sinon appliquer, sur la copie, les migrations de rang `k+1` à `N`, dans l'ordre, chacune selon la règle « Transaction et `user_version` » (et, le cas échéant, le protocole de reconstruction) ;
4. puis les contrôles `integrity_check`, `foreign_key_check` et les requêtes `CK-xx` habituels.

Déterminisme : grâce à la chaîne figée en append-only, une même sauvegarde produit le même schéma sur toute installation. Une sauvegarde de rang `k` ne dépend jamais des numéros de fichiers.

## 6. machine.db

`machine.db` est distincte de la base métier.

Elle ne contient aucune donnée commerciale ou métier.

Les responsabilités actuellement définies comprennent notamment :

- compte local ;
- licence ;
- état des services BATORYA ;
- racines de stockage ;
- préférences de sauvegarde ;
- état Gmail ;
- high-water de numérotation.

Les secrets ne sont pas stockés dans `machine.db` lorsqu’ils doivent résider dans le coffre sécurisé du système d’exploitation.

L’initialisation des singletons de `machine.db` relève du service d’initialisation au premier démarrage. La migration `001_initial.sql` ne crée aucune ligne de singleton.

## 7. Tests

Les tests sont regroupés par responsabilité.

Le test actuellement défini pour le premier démarrage de `machine.db` est :

```text
src-tauri/tests/machine/test_premier_demarrage.py
```

Les tests des migrations métier sont :

```text
src-tauri/tests/metier/test_001_initial.py
src-tauri/tests/metier/test_002_fournisseurs.py
src-tauri/tests/metier/test_003_devis.py
```

Pour les migrations métier : un fichier de test par migration, dans `src-tauri/tests/metier/`, nommé `test_<nom de la migration>.py` ; les méthodes de test portent le nom de l’invariant vérifié (`test_INV_xx_…`), conformément au registre des invariants.

Les connexions de test appliquent les mêmes réglages que les connexions applicatives (« Réglages de connexion SQLite », §9), dont `PRAGMA recursive_triggers=ON` posé **explicitement**. Chaque fichier de test de migration contient un contrôle que ce réglage est effectivement actif et, lorsque la migration porte des triggers de protection applicables, un test ciblé vérifiant qu'`INSERT OR REPLACE` ne les contourne pas.

Un test doit avoir un nom explicite permettant d’identifier directement le comportement vérifié.

Les tests ne doivent pas devenir une seconde spécification contradictoire : lorsqu’un comportement est modifié volontairement, le test correspondant doit être mis en cohérence avec la décision et les documents de référence.

### 7.1 Campagne de mutation des migrations métier

Chaque nouvelle tranche de migration métier doit être accompagnée de sa campagne de mutation sur la migration et son fichier de test.

L'objectif est de terminer la campagne avec **0 survivant non qualifié**. Un survivant peut uniquement être conservé lorsqu'il est démontré et documenté comme mutant équivalent ou inatteignable ; il ne doit pas être laissé sans qualification.

Cette campagne complète les tests fonctionnels classiques : un résultat « tous les tests passent » ne suffit pas à considérer la couverture de la tranche comme sécurisée.

Lorsqu'une correction est apportée à une migration déjà existante, les tests de cette tranche doivent être rejoués et la campagne de mutation concernée doit être réévaluée avant de poursuivre sur une nouvelle tranche.

Lorsque les tests d'une tranche déjà intégrée sont modifiés sans que sa migration change (par exemple le renforcement des tests 001–003 par `recursive_triggers=ON`), une **nouvelle campagne de mutation** (0 survivant non qualifié) doit être exécutée **avant l'intégration** des tests modifiés.

## 8. Séparation des responsabilités

Principe général V6 :

```text
UI
 ↓
Services applicatifs
 ↓
Règles métier / domaine
 ↓
Repositories
 ↓
SQLite
```

Les détails de cette séparation seront précisés lorsque les premières couches applicatives seront implémentées.

Principe déjà fixé :

- l’UI ne doit pas porter seule des règles métier critiques ;
- l’UI ne doit pas accéder directement aux bases SQLite pour contourner les services ou repositories ;
- les règles métier ne doivent pas être dupliquées dans plusieurs interfaces ;
- les accès aux données doivent rester centralisés dans les responsabilités prévues à cet effet.

## 9. SQLite et accès aux données

Les règles de données définies par le modèle SQLite et les invariants constituent la référence.

Une contrainte déjà portée par SQLite ne doit pas être recréée inutilement dans plusieurs couches uniquement pour « faire pareil ».

Inversement, une règle explicitement définie comme garde de service ne doit pas être déplacée arbitrairement dans un trigger SQLite.

La responsabilité de chaque règle doit rester conforme au modèle de données et aux invariants.

### Réglages de connexion SQLite

Chaque ouverture de connexion pose les réglages suivants, hors des migrations (qui ne contiennent aucun `PRAGMA`) :

- `PRAGMA foreign_keys=ON` ;
- `PRAGMA journal_mode=WAL` ;
- `PRAGMA synchronous=FULL` ;
- `PRAGMA busy_timeout` défini ;
- `PRAGMA recursive_triggers=ON`.

`recursive_triggers=ON` est obligatoire : sans lui, `INSERT OR REPLACE` supprime la ligne existante **sans déclencher** ses triggers `BEFORE DELETE`, ce qui contourne les gardes de non-suppression et d'immutabilité (vérifié). Les tests de migration doivent ouvrir leur connexion avec ces mêmes réglages.

### Écritures interdites ou encadrées

### `ON DELETE` et conservation des objets

- Les clés étrangères sont en `ON DELETE RESTRICT` par défaut ; aucune clause `ON UPDATE`.
- Chaque `ON DELETE` est **examiné relation par relation** : `CASCADE` uniquement pour des données strictement dépendantes, sans valeur historique autonome, et seulement tant que le parent est supprimable (brouillon de devis, prestation du catalogue). On ne met pas `RESTRICT` partout : la suppression d'un brouillon doit rester possible.
- Tout objet portant un numéro définitif est conservé : aucune suppression, `numero` immuable. Les gardes en base (triggers de suppression et d'immutabilité) sont des mécanismes à concevoir par migration (modèle de données V3.13 §4.19 et §8, PT-4, PT-5, propositions).
- Les clients et fournisseurs ne sont jamais supprimés, archivés ni désactivés ; ils n'ont pas de statut.

- `INSERT OR REPLACE` et `REPLACE` sont **interdits**. On utilise `INSERT`, `UPDATE` ou un UPSERT explicitement maîtrisé (`INSERT … ON CONFLICT(…) DO UPDATE`) ; `INSERT OR IGNORE` reste permis lorsque l'idempotence est voulue (singletons de `machine.db`, création des garanties).
- Raison : préserver les garanties apportées par les triggers et éviter les suppressions implicites.
- Cette interdiction est une **convention technique** : elle n'est pas imposée mécaniquement (aucun contrôle du mot `REPLACE`) ; les tests vérifient le comportement de protection (§7). Un REPLACE ne déclenche pas les triggers `UPDATE` (par exemple TR-95) : `numerotation_sequences` est donc aussi protégée par `tr_96_numerotation_sequences_no_delete` (TR-96, migration 004), effectif face au REPLACE grâce à `recursive_triggers=ON`. Les migrations déjà appliquées restent immuables : une protection manquante s'ajoute par une migration ultérieure.
- Un contrôle qui compare des lignes de plusieurs tables n'est jamais un `CHECK` ni un trigger de miroir : c'est une requête de contrôle `CK-xx` (modèle de données §14).
- Les requêtes de contrôle `CK-xx` sont exécutées après un import et après une restauration, y compris CK-13 (cohérence devis ↔ BC). CK-13 est un contrôle diagnostique : il ne corrige rien.
- Restauration : si un contrôle d'intégrité obligatoire échoue ou si CK-13 retourne une incohérence, la restauration est considérée comme échouée ; l'état restauré ne devient pas l'état de travail validé et la sauvegarde de sécurité créée avant la restauration permet le retour à l'état précédent. Le détail technique relève du module Sauvegarde / Restauration.
- Restauration d'une sauvegarde plus ancienne : mêmes règles qu'une installation — refus si `user_version` > rang maximal supporté, sinon application dans l'ordre des migrations de rang `k+1` à `N` (§5, « Restauration d'une sauvegarde plus ancienne »).

## 10. Nommage

Les noms doivent être explicites et cohérents avec le vocabulaire métier V6.

Il est interdit d’introduire des synonymes techniques ou fonctionnels simplement pour varier les noms d’un même concept.

Le vocabulaire du domaine doit notamment respecter les termes définis dans le CDC V6.1 et le modèle métier : client, devis, BC, facture, acompte, situation, solde, avoir, règlement, PV, garantie, prestation, fournisseur, dépense, planification, etc.

Les conventions détaillées de nommage Rust, TypeScript, React et SQL seront ajoutées avant la création des premières séries importantes de fichiers dans ces technologies.

## 11. Pas d’anticipation architecturale

V6 ne doit pas être sur-architecturé.

Ne pas créer prématurément :

- des couches sans responsabilité réelle ;
- des abstractions génériques sans second usage ;
- des modules vides uniquement pour préparer une architecture hypothétique ;
- des systèmes de plugins ou d’extensions non demandés ;
- des mécanismes destinés à BATORYA Entreprise.

BATORYA Entreprise est hors périmètre de V6 et ne doit pas influencer les choix d’implémentation d’Essentiel.

## 12. Évolution du document

Ce document est un référentiel vivant.

Une convention n’est ajoutée que lorsqu’elle est :

- nécessaire ;
- suffisamment claire ;
- compatible avec les documents de référence ;
- utile à plusieurs fichiers ou modules, ou nécessaire pour éviter une dérive d’architecture.

Les conventions détaillées seront donc ajoutées au moment où l’implémentation les rend nécessaires.

## 13. Règle de travail avec les assistants de développement

Lorsqu’un assistant de développement produit un nouveau fichier, il doit respecter l’arborescence et les conventions déjà définies.

Il ne doit pas :

- renommer arbitrairement un fichier existant ;
- déplacer un fichier existant sans raison architecturale explicite ;
- créer une nouvelle couche uniquement pour résoudre localement un problème ;
- modifier un document de référence sans signaler précisément la modification ;
- introduire une fonctionnalité hors du périmètre V6.

Lorsqu’un emplacement ou une convention n’est pas encore défini, l’assistant peut proposer une solution, mais celle-ci doit être validée avant de devenir une convention du projet.
