# ÉTUDE DE CONCEPTION — Rattachement explicite des situations aux devis (révision 2)

**Nature** : document de travail (relecture). Étude de conception uniquement. **Non officiel.**
**Date** : 2026-10-18 · **Remplace** la première version de l'étude (2026-10-17, commit 7de3cc6).
**Périmètre respecté** : aucune migration, aucun test du dépôt, aucun code applicatif, aucun fichier sous `docs/`, aucun patch d'implémentation, aucune tranche lancée. Seul ce fichier est révisé.
**Statut des orientations** : M1 à M4 (demande du 2026-10-18 02:43) sont des **orientations de travail**, pas des décisions officielles de BATORYA. Elles ne le deviennent qu'après validation humaine. Les identifiants (nom de table, `TR-xx`, `INV-xx`, `CK-xx`) cités ici sont **provisoires**.

---

## 1. État réel du dépôt et références consultées

### 1.1 Dépôt GitHub (cloné à neuf le 2026-10-18)

- `main` = **7de3cc6** (2026-10-17 21:54, ajout de la première version de cette étude, identique octet pour octet à celle que j'avais livrée).
- Chaîne métier présente dans `src-tauri/migrations/metier/` : `001_initial`, `002_fournisseurs`, `003_devis`, `004_bons_commande`, `005_depenses`, `005a_corrections_v313`, `005b_bc_multi_devis`, `005c_bc_annule_caches_financiers`, `006_facturation`, `007_reglements`, `008_garanties`, `009_pv` (rangs 1 à 12).
- **`009a_bc_annulation_interdite_si_facture` (rang 13) et `009b_acompte_garanties_manuelles` (rang 14) n'existent pas dans l'arborescence.** Elles n'existent que sous forme de texte dans les fichiers `fichiers-a-relire/consignation-V3.14*.patch` (jusqu'au patch `h`). Rien n'indique qu'elles aient été intégrées : je ne le suppose pas.
- Aucune base de données dans le dépôt (SQL, tests, documents seulement).
- La règle « aucun acompte après une situation sur le même devis » **n'est pas dans le SQL de GitHub** : le `tr_22_factures_acompte` livré (006, l.345) ne contient aucune règle d'ordre situation → acompte. Constaté par sonde : après une situation S1 sur A, un acompte sur A **est accepté** par la chaîne GitHub. Cette règle n'existe que dans le patch `h` (009b), réalisée **avec des horodatages**.

### 1.2 Références consultées (ligne = fichier tel qu'il est sur GitHub)

| Sujet | Source | Ce qu'elle dit |
|---|---|---|
| Hiérarchie documentaire | `docs/conception/conventions-techniques-v6.md` §2, l.16-26 | Ordre : 1 CDC, 2 modèle SQLite (V3.12 validé), 3 `invariants.md`, 4 modèle métier, 5 errata (traçabilité). « Une convention de code ne peut pas contredire ces documents. » |
| Règles de migration | même fichier, §5, l.70-108 | Numérotation séquentielle ; migration appliquée jamais réécrite ; **le modèle SQLite est mis à jour avant** la création d'une migration ; « une migration n'insère aucune ligne » ; triggers nommés `tr_<NN>_<table>_<règle>` (NN = TR du modèle) ; chaque migration livrée avec son test |
| Pas de sur-architecture | même fichier, §11, l.233-246 | Pas de mécanisme sans besoin réel |
| Composition des lignes d'une situation | `docs/conception/invariants.md` l.104 (INV-62) ; `docs/conception/modèle-données-sqlite-v6-v3.12.md` l.390 ; `docs/conception/modèle-métier-V6.md` §11 l.336 | **1 ligne `synthese`** ; le cumul % et le déjà-facturé restent sur la facture |
| Même sujet, documents en relecture | `fichiers-a-relire/MAJ__invariants.md` l.100 ; `MAJ__modèle-données-sqlite-v6-v3.13.md` l.516 ; `MAJ__modèle-métier-V6.md` l.377 | Identique (INV-62 : « situation = 1 ligne `synthese` », précision « composition avec exécution : PT-11, PT-12 ») |
| Situation globale au BC | `MAJ__invariants.md` l.221 (INV-190), l.96 (INV-57) ; `MAJ__modèle-métier-V6.md` §12 l.391 ; `MAJ__modèle-données-sqlite-v6-v3.13.md` l.184, l.1197 (D-48), l.1394 (PT-11) | « calculée au niveau global du BC sur l'ensemble du périmètre contractuel **actuellement** accepté (tous les devis rattachés) » ; colonnes : **PT-11 À CONCEVOIR** |
| Plusieurs devis sur un BC | `MAJ__modèle-métier-V6.md` l.269 ; `MAJ__modèle-données-sqlite-v6-v3.13.md` l.433 | Un acompte ou des situations déjà émis **ne ferment pas** le BC ; l'ajout d'un devis augmente le contractuel, **les factures déjà émises ne sont pas modifiées**, une situation ultérieure se calcule sur le nouveau contractuel |
| Situation et annulation du BC | `docs/specifications/cdc-fonctionnel-architectural-v6.md` l.516, 520-524 | « Une Situation émise, **même annulée**, interdit toujours l'annulation directe du BC » |
| SQL livré, lignes de situation | `006_facturation.sql` en-tête l.1-50 ; `tr_22_facture_lignes_insert` l.449+ | situation → `avancement` ou `deduction` seulement ; **`synthese` refusée** ; en-tête : « décisions de l'étape d'implémentation (situations ligne par ligne) » |
| SQL livré, montant | `006_facturation.sql` l.145 | `CHECK (type = 'solde' OR total_ht <> '0.00')` ; `M > 0` est une règle de service (en-tête l.42) |
| Décision de travail du 2026-10-17 (D) | `consignation-V3.14-h.patch` l.447 et l.587 (texte), l.55 et l.36 (règle d'ordre des acomptes) | Lignes `avancement` = « situation historique » ; ne décide pas de la composition des nouvelles situations, qui reste conforme à INV-62 / INV-190. Règle d'acompte du 2026-10-17 14:34 |

### 1.3 Nuance documentaire importante (à ne pas perdre)

**INV-190, la formule « situation globale au BC », PT-11 et D-48 n'existent pas dans `docs/`.** Le registre officiel `docs/conception/invariants.md` s'arrête à INV-179. Ces éléments vivent dans les documents de travail `MAJ__*` (modèle V3.13 « en relecture, non validée » selon l'en-tête du registre MAJ ; D-48 y est marquée « Validée 2026-10-03 »). Dans `docs/`, le modèle métier §12 (l.344-362) donne la formule `contractuel × cumul % − facturation nette antérieure` sans écrire « globale ». Cela reste cohérent (le contractuel est celui du BC), mais **la cohérence de M1 avec « INV-190 » est établie sur les documents de travail, pas sur le corpus officiel**. À signaler à la validation.

---

## 2. Orientations métier retenues (à valider)

### M1 — Une situation couvre tous les devis rattachés au BC à son émission

- **Vérification des sources** : INV-190 et §12 disent « périmètre contractuel actuellement accepté (tous les devis rattachés) » ; l.433 du modèle V3.13 : une situation ultérieure se calcule sur le nouveau contractuel, les factures déjà émises ne changent pas. L'orientation M1 est **cohérente** avec ces textes.
- **Nuance** : ces textes définissent le **périmètre du calcul du montant**. Aucun ne définit une **relation de « couverture »** ni ne relie une situation à la règle d'ordre des acomptes. Le mot « couvre » et la règle « aucun acompte après une situation sur ce devis » viennent des règles de travail du 2026-10-17 14:34, consignées **uniquement** dans le patch `h`. Il faudra donc les inscrire (INV-58 étendu ou nouvel INV, au choix de la validation) et non seulement s'appuyer sur INV-190.
- **Exemple de référence** : A rattaché, S1 émise, B rattaché ensuite → S1 couvre {A} (pour toujours) ; S2 émise après B couvre {A, B}.
- **Exclu** : tout mécanisme de sélection d'un sous-ensemble de devis par situation. Le périmètre est « tous les devis rattachés à l'instant de l'émission », jamais un choix.

### M2 — Existence d'une situation = émission

- Une situation émise reste une situation pour la règle des acomptes, **quel que soit** son montant net après avoirs et son pourcentage.
- **Conséquence sur les sources** :
  - le CDC (l.516) retient déjà « émise, même annulée » pour l'annulation du BC. Nuance : la règle du 2026-10-17 14:34 (patch `h`, INV-44 / TR-103) permet d'annuler un BC dont **chaque** facture est ramenée à zéro par des avoirs, ce qui est plus souple que le texte du CDC. Les deux règles sont distinctes (annulation du BC / acompte) ; je ne les confonds pas, mais l'écart CDC ↔ règle 14:34 reste à arbitrer par ailleurs (§7, H6) ;
  - le SQL livré dérive un état « neutralisée » (`total_ht` crédité en totalité par des avoirs) et l'utilise dans d'autres triggers (situation de référence pour l'avancement, solde). **Le trigger d'acompte ne doit pas réutiliser ce filtre.** C'est le seul endroit où M2 pourrait être violé par inadvertance ; le test 4 le garde.
  - la table de couverture (§3) ne lit ni les avoirs, ni les montants, ni les pourcentages : M2 est satisfaite **par construction**.
- **Cas « 0 % » — constat qui ne figure pas dans le prompt** : le SQL livré impose `total_ht <> '0.00'` pour toute facture hors solde, et le service impose `M > 0`. **Une situation dont le montant est 0.00 (avancement global 0 %) ne peut donc pas exister aujourd'hui.** Ce qui est possible : une situation de montant > 0 qui **couvre** un devis dont l'avancement propre est 0 % (l'avancement porte sur d'autres devis). Le test 5 est reformulé en conséquence (§6). Autoriser une situation de montant nul changerait une règle de calcul / comptable : **hors périmètre**, soumis à décision (H1).

### M3 — Voir §4.

### M4 — Voir §5.

---

## 3. Modèle technique recommandé — option B (table de liaison explicite)

Option B retenue comme référence. Le nom `situation_devis` est **provisoire**. Les alternatives A et C ne sont gardées qu'en §3.8.

### 3.1 Structure (provisoire)

```sql
CREATE TABLE situation_devis (               -- nom provisoire, non officiel
    facture_id INTEGER NOT NULL REFERENCES factures (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    devis_id   INTEGER NOT NULL REFERENCES devis    (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    PRIMARY KEY (facture_id, devis_id)
) STRICT, WITHOUT ROWID;
CREATE INDEX idx_situation_devis_devis_id ON situation_devis (devis_id);
```

- **Clé** : `(facture_id, devis_id)` — une ligne n'a aucune identité propre ; la clé composite interdit le doublon. L'index sur `devis_id` sert le trigger d'acompte et les contrôles RESTRICT.
- **Pas de `bc_id`** : il serait redondant et pourrait diverger ; le BC se déduit de la facture.
- **Pas d'horodatage** : la date d'émission est celle de la facture. Une colonne `created_at` éventuelle (convention de tables du modèle) ne servirait à aucune règle ; à trancher à la mise à jour du modèle (§7, H5).
- Les conventions imposent `STRICT` (en-tête 006) ; le `WITHOUT ROWID` combiné est possible. La forme exacte (clé composite ou `id` de substitution) sera alignée sur le modèle SQLite lors de sa mise à jour — c'est une décision de présentation, pas de fond.

### 3.2 Contrôles d'intégrité en base — et ce qu'ils garantissent (sonde exécutée)

Les clés étrangères seules garantissent seulement l'**existence** de la facture et du devis. **Elles n'empêchent ni de lier une facture qui n'est pas une situation, ni un devis étranger au BC.** Il faut des triggers (style du projet) :

| Contrôle | Mécanisme | Résultat de la sonde |
|---|---|---|
| La facture est une situation | `BEFORE INSERT` : refus si `factures.type <> 'situation'` | lien vers un acompte : **refusé** |
| Le devis appartient au BC de la facture | `BEFORE INSERT` : refus si `(factures.bc_id, devis_id)` absent de `bc_devis` | lien vers un devis d'un autre BC : **refusé** |
| Pas de doublon | PK | **refusé** |
| Couverture immuable | `BEFORE UPDATE` et `BEFORE DELETE` : refus | UPDATE / DELETE : **refusés** ; `INSERT OR REPLACE` avec `recursive_triggers=ON` : **refusé** |
| Facture ou devis couvert non supprimable | FK `RESTRICT` + triggers existants | `DELETE` facture : refusé (INV-06, tr_21) ; `DELETE` devis : refusé (INV-180) |
| Le type de la facture ne change plus | `tr_20` (factures immuables) existant | acquis |
| L'appartenance au BC ne change plus | INV-184 (`bc_devis` immuable) existant | acquis |

Alternative écartée : une clé étrangère composite `(bc_id, devis_id) → bc_devis` exigerait un `UNIQUE(bc_id, devis_id)` absent de `bc_devis` (qui n'a que `UNIQUE(devis_id)` et `UNIQUE(bc_id, rang)`) **et** une colonne `bc_id` redondante. Elle toucherait une table livrée pour un gain que les triggers donnent déjà.

### 3.3 Enregistrement de la couverture à l'émission

Dans la **même transaction** `BEGIN IMMEDIATE` que celle de l'émission (déjà exigée par 006 pour `situation_numero`) :

1. calculs et contrôles du service ;
2. `INSERT` de la facture de type `situation` ;
3. `INSERT` des lignes de facture (quelle que soit leur composition, §4) ;
4. **une seule instruction** : `INSERT INTO situation_devis (facture_id, devis_id) SELECT :facture, devis_id FROM bc_devis WHERE bc_id = :bc` ;
5. `COMMIT`.

- L'`INSERT … SELECT` fige « tous les devis rattachés à cet instant » : **aucune liste passée en paramètre, donc aucun sous-ensemble possible côté service** (exigence M1).
- Le verrou d'écriture pris dès `BEGIN IMMEDIATE` sérialise l'émission et tout rattachement de devis : B est soit rattaché **avant** (donc couvert), soit **après** le `COMMIT` (donc non couvert). Aucun entrelacement possible.

### 3.4 Atomicité de l'émission

Toute erreur entre 2 et 4 déclenche `ROLLBACK` : ni facture, ni lignes, ni couverture. Sonde : dans un `SAVEPOINT`, facture de S2 + deux liens, puis `ROLLBACK TO` → S2 n'existe plus, le nombre de couvertures est revenu à sa valeur initiale. Remarque : le compteur de numérotation (high-water dans `machine.db`) n'est pas dans la même base ; un échec peut laisser un **trou de numérotation**, que le CDC accepte (l.590). Le test 9 ne doit donc pas exiger la réutilisation du numéro.

### 3.5 Trigger d'acompte (remplace la règle à horodatages du patch `h`)

Dans `tr_22_factures_acompte` (nom existant conservé) :

```sql
SELECT RAISE(ABORT, 'INV-58: aucun acompte apres une situation sur ce devis')
 WHERE EXISTS (SELECT 1 FROM situation_devis c WHERE c.devis_id = NEW.devis_id);
```

- Refuse l'acompte sur un devis **déjà couvert** par au moins une situation émise.
- **Indépendant** des avoirs, du montant, du pourcentage, des horodatages : plus de cas d'égalité d'horodatage (le patch `h` devait décider « ex æquo = refus »).
- N'affecte pas les acomptes émis **avant** la situation, ni un devis rattaché **après** (sonde : acompte sur B autorisé après S1 {A}).
- Les autres contrôles du trigger (plafond d'acompte prévu, plafond contractuel, solde actif…) restent inchangés.

### 3.6 Ajout ultérieur d'un devis

Le rattachement (`bc_devis`) n'écrit pas dans la table de couverture ; il reste soumis à INV-187 / INV-188 inchangés. S1 reste {A} pour toujours (sonde : après rattachement de B, S1 couvre toujours uniquement A). La prochaine situation, par l'`INSERT … SELECT`, couvre {A, B} (sonde : S2 {A, B}).

### 3.7 Immutabilité et limites de ce que SQLite garantit

Effets de l'immutabilité (factures, `bc_devis`, couverture) :

- une couverture **erronée mais valide** (devis réellement rattaché) est **permanente** : elle bloquerait à vie l'acompte du devis concerné. Seule une migration corrective, avec décision humaine, pourrait y remédier. Le risque est réduit par la conception « une instruction, aucun paramètre » (§3.3) et par les tests ;
- une couverture **omise** n'est pas réparable par `UPDATE`, mais peut encore l'être par un `INSERT` tardif (voir ci-dessous).

**SQLite ne peut pas** (limite comparable à celle déjà assumée par 006 pour les lignes) :

1. exiger à l'`COMMIT` qu'une situation ait au moins une ligne de couverture (sonde : une situation sans couverture est acceptée) ;
2. garantir que la couverture est **complète** (tous les devis rattachés) ;
3. distinguer l'`INSERT` de l'émission d'un `INSERT` tardif sans horodatage (sonde : une couverture ajoutée après coup sur une situation existante est acceptée). Je ne propose pas d'horodatage pour le bloquer.

**Détection (contrôles de diagnostic, jamais bloquants)** — identifiants à attribuer par la validation :

| Contrôle | Principe | Utilise des horodatages ? |
|---|---|---|
| D1 | situation sans aucune couverture | non |
| D2 | pour deux situations d'un même BC (`situation_numero` croissant), la couverture de la plus récente contient celle de l'ancienne (les rattachements ne font que croître) | non |
| D3 *(optionnel, à décider)* | devis rattaché avant l'émission d'une situation mais absent de sa couverture | **oui** (`bc_devis.created_at` ≤ `factures.created_at`) |

D1 et D2 sont sans horodatage. D3 est le seul à voir l'omission partielle sur la **dernière** situation (invisible de D1 et D2). Justification de son utilité : détecter une panne de service. Justification de sa séparation : en cas d'égalité d'horodatage, il ne peut que signaler « à examiner » ; il **ne décide jamais** d'un refus. Son inclusion est une décision humaine (§7, H4). `bc_devis.rang` n'est pas utilisable comme garde : 005b le définit comme ordre d'association « ni contigu ni imposé ».

### 3.8 Alternatives (rappel)

- **A** — lire la couverture dans les lignes d'avancement : **rejetée comme source de vérité** (statut « historique » des lignes d'avancement, §4 ; une situation sans ligne n'a aucune couverture déductible — sonde). Peut servir de **preuve** lors d'une décision humaine sur une base peuplée (§5).
- **C** — jalon ordinal sur `bc_devis` : garantie SQL plus forte mais modifie une table livrée et ne vaut que pour des situations strictement globales. Écartée : B suffit, sans toucher aux tables livrées.

---

## 4. Contradiction documents ↔ migration 006 (M3)

### 4.1 Hiérarchie applicable

Conventions §2 : CDC (silencieux sur la composition des lignes de situation) > modèle SQLite V3.12 > `invariants.md` > modèle métier > errata. **Les trois niveaux qui parlent (modèle SQLite l.390, INV-62 l.104, modèle métier l.336) disent la même chose : 1 ligne `synthese`.** La migration 006 est un code d'implémentation placé sous ces documents. La phrase « une convention de code ne peut pas contredire ces documents » vise les conventions ; je l'étends **par analogie** à une migration (la migration implémente le modèle, et §5 impose de mettre le modèle à jour avant elle) ; c'est une extension, pas un texte explicite. L'en-tête de 006 invoque des « décisions de l'étape d'implémentation » (situations ligne par ligne) qui **ne figurent dans aucun document de la hiérarchie**.

### 4.2 La contradiction, en clair

| | Documents (docs/ et MAJ) | SQL livré (006) |
|---|---|---|
| Lignes d'une situation | **1 ligne `synthese`** | **`avancement`** (une par ligne de BC) **+ `deduction`**, `synthese` **refusée** |
| Où vit le cumul % | sur la **facture** (colonnes, PT-11 À CONCEVOIR) | sur **chaque ligne** d'avancement ; **aucune** colonne cumul / mode / valeur saisie sur `factures` |

Décision de travail du 17/10 (D) : les lignes `avancement` désignent des situations **historiques** ; la règle ne décide pas de la composition des **nouvelles** situations, qui reste conforme à INV-62 / INV-190. Elle ne figure que dans le patch `h` et les documents de travail, pas dans `docs/`.

**Les sources confirment-elles l'orientation M3 ?** Oui sur le fond : les trois niveaux hiérarchiques, les documents MAJ et la décision D vont dans le même sens. **Non sur le traitement** : aucune source ne dit ce que devient `avancement` à l'insertion après correction, ni comment représenter le cumul %. Voir 4.5.

### 4.3 Séparation des deux sujets

- **Couverture situation ↔ devis** (§3) : relation entre une facture-situation et des devis. N'a besoin ni des lignes, ni de leur type : elle fonctionne que la situation porte `avancement` (historique), `synthese` (nouveau) ou rien (sonde : une situation sans ligne est acceptée par 006).
- **Composition des lignes** : contenu d'une facture. N'intervient pas dans la règle d'acompte.

Les deux se corrigent **séparément**. Les triggers concernés sont différents : 009b réécrit des triggers de `factures` (`tr_22_factures_*`, `tr_23_factures_avoir`) ; M3 toucherait `tr_22_facture_lignes_insert` (006, l.449).

### 4.4 Ce qu'une correction M3 devrait produire (orientation, non décidée)

Pour qu'une **nouvelle** situation conforme à INV-62 soit acceptée : `situation → synthese` (une ligne, montant = montant de la situation) et la représentation du cumul %, du mode de saisie et de la valeur saisie **sur la facture** (documents MAJ l.497 : `avancement_cumule_pct` sur `factures`).

Deux niveaux possibles, **sans que je tranche** :

- **M3-α, minimal** : autoriser aussi `synthese` pour une situation dans `tr_22_facture_lignes_insert` (DROP / CREATE TRIGGER). Le SQL **accepte** alors la composition documentée. Limite : il **n'impose** pas INV-62, car une nouvelle situation à lignes `avancement` reste acceptée (rien ne distingue « historique » de « nouveau ») ; la continuité du cumul % par ligne, aujourd'hui portée par le contrôle INV-190 sur `avancement_precedent_pct`, n'a plus de support pour les situations à ligne unique.
- **M3-β, complet** : colonnes de situation sur `factures` (mode, valeur saisie, cumul %), contrôle de continuité du cumul % sur la facture, refus de `avancement` pour les nouvelles situations. Exige de **concevoir PT-11** (« ce que désigne la valeur *montant* : cumulé ou de la période »), aujourd'hui À CONCEVOIR, et probablement une reconstruction de `factures` (tables immuables, protocole `foreign_keys = OFF`).

### 4.5 Migrations et tests concernés (aucun créé ni modifié)

| Élément | Concerné par | Remarque |
|---|---|---|
| `006_facturation.sql` (immuable) | matrice de `tr_22_facture_lignes_insert`, contrôle INV-190 sur `avancement_precedent_pct`, colonnes de `facture_lignes`, index unique d'avancement ; absence des colonnes de situation | ne se modifie pas ; correction = migration corrective ultérieure |
| Migration corrective M3 | rang **15** (« 010 » dans la numérotation du projet) ou après | **hors périmètre** : ni 010 ni suivantes ; exige validation, PT-11 et mise à jour préalable du modèle |
| `test_006_facturation.py` (309 tests) | `test_INV_62_une_situation_ne_porte_que_des_lignes_d_avancement_et_de_deduction` (l.2605) à inverser ; familles `T48_D`, `T48_E` (oracle CK-17), `T48_I`, `T48_M`, `T48_N`, `T48_Q`, `T48_R`, `INV_190_*` ; 143 occurrences de « avancement » | les tests livrés ne se modifient pas ; écarts à traiter par rejeu différentiel comme pour 009a / 009b |
| Aide `emettre_situation` (test_006 l.379) | construit des lignes `avancement` ; réutilisée par les tests 007 et 008 | un changement d'aide se propage à ces fichiers |
| CK-16 / CK-17 (définis dans test_006) | supposent des lignes `avancement` | à redéfinir ou limiter aux situations historiques |
| Tests 009b du patch `h` (ordre des acomptes) | construisent des situations brutes sans ligne ni couverture | à adapter à B (§6), indépendamment de M3 |

### 4.6 Dépendances empêchant une correction totalement séparée

1. **PT-11 (À CONCEVOIR)** : sans lui, M3-β ne peut pas être spécifié ; M3-α reste possible mais incomplet.
2. **Marqueur « historique »** : le SQL ne distingue pas aujourd'hui une situation historique d'une nouvelle. `factures.origine IN ('v6','import')` existe, mais ne couvre que les imports, pas d'éventuelles situations créées sous 006. Décision humaine (H2).
3. **Ordre imposé par les conventions** : modèle SQLite mis à jour **avant** toute migration.
4. **006 immuable** : la correction passe obligatoirement par une migration corrective placée après la chaîne.

**Le volet couverture (§3) ne dépend d'aucun de ces points** : il peut être validé et implémenté sans M3.

---

## 5. Stratégie de migration et données historiques (M4)

### 5.1 Placement

Faits : 009b (patch `h`, 466 lignes, rang 14) ne crée aucune table, remplace des triggers (`DROP TRIGGER` / `CREATE TRIGGER`), et utilise déjà des gardes d'exécution en tables TEMP. Elle n'est **pas livrée**. 001 à 009 ne sont pas touchées.

**Recommandation : intégrer la couverture dans 009b avant sa livraison** : table + index + trois triggers de couverture + réécriture de la condition d'ordre de `tr_22_factures_acompte` (la condition à horodatages disparaît) + la garde du §5.2.

Pas de 009c par défaut, parce que :
- la règle d'acompte de 009b **dépend** de la table : la séparer reviendrait à créer dans 009b une règle à horodatages que la 009c remplacerait immédiatement, dans la même chaîne non livrée ;
- rien dans le contenu de 009b n'impose la séparation (aucun objet partagé avec la couverture hors `tr_22_factures_acompte`).

**Condition de bascule** : si 009b est livrée ou appliquée avant la validation de cette étude, la couverture ne peut plus y entrer ; elle irait dans la migration suivante (rang 15, numérotation « 010 »), à ne créer qu'après décision explicite, en remplaçant alors la règle à horodatages. Le coût d'une intégration dans 009b : retravailler les tests 009b d'ordre (une dizaine) et relancer la campagne de mutation sur 009b.

Ordre de travail imposé : validation de l'étude → mise à jour du modèle SQLite (avec TR / INV attribués) → patch 009b révisé et tests → rejeu complet.

### 5.2 Situations préexistantes (M4)

**Faits établis** : le dépôt ne contient aucune base ; selon le propriétaire du produit, l'environnement local n'en contient pas d'autre ; l'import V2 sera précédé d'une application de conversion distincte. **Je n'ai vérifié aucune base réelle et je ne le prétends pas.**

**Recommandation (minimale)** : la migration qui crée la couverture **exige une base sans situation préexistante** et s'arrête avec un message explicite si `factures` contient au moins une ligne de type `situation`. Garde en lecture seule, même modèle que les gardes de 009b (tables TEMP, aucune trace).

Justification :

| Solution | Verdict |
|---|---|
| **Garde bloquante (retenue)** | Conforme aux faits (aucune base connue) ; n'invente aucun lien ; coût quasi nul ; transforme un risque silencieux en arrêt explicite |
| Détecter les situations « non reconstituables » et migrer les autres | Exige de définir « reconstituable » (probablement via les lignes `avancement`, dont le statut est précisément contesté en §4) : dispositif complexe sans besoin établi — exclu par la consigne |
| Laisser les situations existantes sans couverture | Rouvre silencieusement le défaut (acompte accepté après situation sur le même devis) |
| Rétro-remplir avec les devis actuellement rattachés | **Fabrique** des liens (un devis rattaché après l'émission serait réputé couvert) — interdit |

**Risque résiduel si une base à situations apparaissait** : la garde empêche l'application, mais le problème de fond (couverture non reconstituable) **n'est pas résolu**. **Conduite à tenir** : ne pas appliquer la migration ; sauvegarder la base ; lister les situations concernées en lecture seule ; faire arbitrer par le propriétaire du produit, cas par cas, quelles preuves sont acceptables (historique de rattachement, lignes d'avancement le cas échéant). Aucun mécanisme n'est conçu ici pour ce cas hypothétique. Les conventions disent qu'une migration « n'insère aucune ligne » (§5) ; 005b a toutefois rétro-rempli `bc_devis`, donc un rétro-remplissage ne serait pas interdit par précédent, mais il faudrait le justifier, et ici aucune règle sûre n'existe.

**Imports** : aucun mécanisme spécifique n'est conçu. Simple constat : la règle ne dépend pas de `origine` ; tout chemin qui crée une situation (service, conversion, import) doit enregistrer sa couverture.

---

## 6. Tests à prévoir

**Aucun de ces tests n'est écrit ni exécuté.** Seule la sonde ci-dessous a été exécutée (§6.2). Les tests 1 à 12 couvrent la demande ; 13 à 15 sont ajoutés.

### 6.1 Tests proposés (statut : proposés, non écrits, non exécutés)

| # | Test | Attendu |
|---|---|---|
| 1 | S1 sur A, puis acompte sur A | refusé (INV-58) |
| 2 | S1 sur A, rattachement de B, acompte sur B | autorisé si plafonds et autres règles respectés |
| 3 | Rattachement A et B, puis nouvelle situation | couvre A et B ; une situation antérieure garde sa couverture |
| 4 | Situation entièrement créditée par avoir(s) | couverture inchangée ; acompte sur le devis toujours refusé |
| 5a | Situation de montant > 0 couvrant un devis dont l'avancement propre est 0 % | couverture de ce devis présente ; acompte refusé |
| 5b | *(conditionnel à H1)* situation de montant 0.00 | **refusée aujourd'hui** (CHECK + M > 0) ; test à n'écrire que si H1 change la règle |
| 6 | Couverture vers un devis d'un autre BC | refusée |
| 7 | Couverture vers une facture non situation (acompte, solde, avoir) | refusée |
| 8 | UPDATE, DELETE, `INSERT OR REPLACE` (`recursive_triggers=ON`) sur la couverture ; DELETE de la facture ou du devis couvert | refusés |
| 9 | Échec injecté entre l'`INSERT` facture et l'`INSERT … SELECT` de couverture | aucune situation, aucune ligne, aucune couverture après `ROLLBACK` ; trou de numérotation toléré |
| 10 | Plafond d'acompte prévu, plafond contractuel du devis et du BC, acompte après solde, une seule garantie, etc. | aucune régression (rejeu des tests 006, 007, 008, 009, 009a, 009b) |
| 11 | *(conditionnel à M3)* cohérence avec INV-62 : une nouvelle situation à 1 ligne `synthese` est acceptée ; `avancement` traité selon la décision H2 | à définir après décision |
| 12 | Rejeu de la chaîne complète 001 → 009a → 009b depuis une base vide et depuis une base au rang 12 ; vérification que 001 à 009 sont inchangées (empreintes comparées à GitHub) ; campagne de mutation | tout vert, `user_version` attendu |
| 13 | Garde M4 : base à une situation | migration refusée, base inchangée ; base sans situation : acceptée |
| 14 | Indépendance vis-à-vis des horodatages : mêmes `created_at` au milliseconde près, ou ordre inversé | même résultat que les tests 1 et 2 |
| 15 | Diagnostics D1 et D2 (et D3 si retenu) | signalent une situation sans couverture, une couverture non monotone ; D3 ne bloque jamais |

Adaptation des tests 009b du patch `h` : la dizaine de tests d'ordre qui fabriquent des situations brutes devront inscrire la couverture ; le test « ex æquo d'horodatage = refus » disparaît.

### 6.2 Réellement exécuté dans cette étude (hors dépôt, jetable)

Sondes de lecture / mémoire sur la chaîne GitHub 001-009, **avec le DDL provisoire de §3 chargé en mémoire seulement** (aucun fichier du dépôt écrit) :

- chaîne GitHub : S1 sans couverture déductible hors lignes ; après rattachement de B, S1 inchangée ; **acompte sur A accepté après S1** (règle absente de GitHub) ; CK-16 signale 3 lignes manquantes sur une situation sans ligne ; UPDATE / DELETE sur `facture_lignes` et `bc_devis` refusés (INV-53, INV-184) ;
- DDL provisoire : lien S1 → A accepté ; lien vers un acompte refusé ; lien vers un devis d'un autre BC refusé ; UPDATE, DELETE, `INSERT OR REPLACE` refusés ; doublon refusé ; DELETE de la facture / du devis couvert refusé ; S2 couvre {A, B} ; `ROLLBACK` : ni S2 ni couverture ; trigger d'acompte d'essai : acompte sur A refusé, couverture de S1 intacte ; **limites constatées** : une situation sans couverture est acceptée, et une couverture peut être ajoutée après coup.

Ces sondes **ne valident pas** la solution : elles confirment les comportements SQLite décrits, rien de plus.

### 6.3 Risques de régression

- Réécriture de `tr_22_factures_acompte` dans 009b : relancer les 106 tests 009b et la mutation.
- La table de couverture est neuve : aucun impact sur 001 à 009.
- Les triggers à `RAISE(ABORT)` suivent le style existant ; ne pas utiliser `INSERT OR IGNORE` dans le service (masquerait un doublon).

---

## 7. Risques résiduels et points nécessitant une décision humaine

**Risques résiduels**
- Omission ou ajout tardif de couverture non empêchés par SQLite (§3.7) ; atténués par l'`INSERT … SELECT`, les tests et D1-D3.
- Couverture erronée mais valide : permanente.
- Désalignement des numéros officiels : TR / INV / CK à attribuer à la validation, rien n'est numéroté ici.
- Corpus officiel en retard sur les documents de travail (INV-190, PT-11, D-48 absents de `docs/`).

**Points à arbitrer**

| # | Question |
|---|---|
| H1 | « Situation à 0 % » = devis couvert à 0 % d'avancement propre (possible) ou situation de montant 0.00 (impossible aujourd'hui) ? Le second cas change une règle comptable / de calcul. |
| H2 | M3 : (a) conception de PT-11 ; (b) M3-α puis M3-β, ou directement β ; (c) après correction, le SQL accepte-t-il encore `avancement` à l'insertion, et avec quel marqueur « historique » ? |
| H3 | Valider le principe « une situation couvre tous les devis rattachés à l'émission » et le formaliser dans les documents (INV-58 étendu ou nouvel INV) ; promouvoir en `docs/` ce qui est aujourd'hui seulement dans les MAJ. |
| H4 | Inclure ou non le diagnostic D3 (horodatage, non bloquant). |
| H5 | Forme finale de la table (clé composite ou `id`), colonne `created_at` éventuelle, nom et numéros. |
| H6 | Écart CDC §17 (« situation émise, même annulée, interdit l'annulation directe ») ↔ règle du 2026-10-17 14:34 (annulation permise si tout est ramené à zéro). |
| H7 | Confirmer que 009a et 009b n'ont été ni livrées ni appliquées ailleurs (condition du placement dans 009b). |
| H8 | Garde M4 bloquante : validée, ou autre conduite préférée si une base à situations existe. |

---

## 8. Recommandation finale

**Volet couverture (M1, M2, M4, placement dans 009b)** : le cadrage est **prêt à être soumis à validation**. Il repose sur une table de liaison, un `INSERT … SELECT` unique dans la transaction d'émission, un trigger d'acompte sans horodatage, une garde de migration, et un plan de tests de 15 cas. Conditions : trancher H3, H5, H7, H8, et H1 pour le test 5.

**Volet M3 (composition des lignes)** : le **diagnostic** est prêt (contradiction établie, hiérarchie confirmée, tests et migrations concernés listés). **La correction n'est pas prête** : elle dépend de PT-11 et de H2. Elle est séparable du volet couverture.

**Aucune implémentation n'est autorisée par cette étude.** Séquence : validation humaine → mise à jour du modèle SQLite → 009b révisée et tests → rejeu complet. Rien n'est validé tant que ce n'est pas implémenté et testé.
