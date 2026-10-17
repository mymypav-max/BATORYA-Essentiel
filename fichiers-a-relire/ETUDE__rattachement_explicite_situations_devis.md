# ÉTUDE DE CONCEPTION — Rattachement explicite des situations aux devis

**BATORYA Essentiel V6** · 2026-10-17 · document d'étude, **aucun fichier du dépôt modifié**, aucune migration, aucun test, aucun patch, rien sous `docs/`. Attend la validation humaine avant toute implémentation.

**Base de référence** : dépôt GitHub `mymypav-max/batorya-essentiel`, branche principale, dernier commit **35c055b (2026-10-17 16:44)**, cloné en lecture seule. Chaîne de migrations réellement présente : **001 → 009** (`006_facturation.sql` incluse). Les migrations `009a` et `009b` **n'existent pas dans l'arbre** : elles ne sont déposées que sous forme de patch (`fichiers-a-relire/consignation-V3.14-h.patch`), non appliqué.

---

## 1. État actuel (observé)

### 1.1 Ce que le SQL de GitHub contient réellement

| Objet | Fait observé | Source |
|---|---|---|
| `factures` | `devis_id` n'existe que pour l'**acompte** (`CHECK (type='acompte') = (devis_id IS NOT NULL)`). Une situation n'a **pas** de `devis_id`. Elle porte `situation_numero` (ordinal par BC, unique par BC) et `montant_deja_facture_ht` | `006_facturation.sql` l.91-158 |
| `tr_22_factures_acompte` (006) | contrôle : devis rattaché au BC, aucun acompte après un solde, un acompte actif par devis, ≤ total du devis, nette ≤ contractuel. **Aucune règle sur les situations** | 006 l.345-373 |
| Effet constaté | acompte **accepté** sur le devis A après une situation sur A, et accepté sur le devis B (sonde de lecture, §6.2) | sonde |
| `bc_devis` | `devis_id` UNIQUE (un devis ↔ un seul BC), `UQ(bc_id, rang)`, `created_at`. **UPDATE et DELETE refusés** (INV-184). Insertion : devis `accepte`, même client, BC non annulé (INV-40, INV-48, INV-188), aucun solde (INV-187) | 005b l.426-450, 006 l.483 |
| `bc_lignes` | `devis_ligne_id` **NOT NULL UNIQUE** : chaque ligne de BC désigne une ligne de devis, donc un devis. Insertion refusée si le devis n'est pas rattaché au BC (INV-175). UPDATE/DELETE refusés (INV-186) | 004, 005b l.474-495 |
| `facture_lignes` | `bc_ligne_id` (FK), `type_ligne ∈ {prestation, synthese, deduction, avancement}`. Une situation **n'accepte que** `avancement` et `deduction` (`synthese` refusée). Lignes immuables (INV-53) | 006 l.159-258, l.449-470 |
| Lignes d'avancement | « une ligne par ligne de BC applicable » : **service**, non imposée par le SQL. Contrôlée après coup par CK-16 (définie dans `test_006`), qui juge « applicable » une ligne de BC par **`bc_lignes.created_at <= factures.created_at`** | 006 l.33-47 ; `test_006` l.154-158 |
| Horodatages déjà utilisés | CK-14 (devis rattaché après un solde : `s.created_at < l.created_at`) et CK-16 : **diagnostics seulement**, jamais un trigger bloquant dans la chaîne de GitHub | `test_006` |

### 1.2 Ce que la règle « actuelle » est vraiment

La règle « aucun acompte après une situation, par devis » **n'est pas dans la chaîne de GitHub**. Elle n'existe que dans la proposition de la révision G (patch h, non appliqué, migration `009b`). Elle y est traduite par une **comparaison d'horodatages** : la situation « couvre » un devis si `factures.created_at >= bc_devis.created_at` de ce devis (ex æquo = refus). C'est cette dépendance que l'étude cherche à supprimer.

### 1.3 Cardinalité situation ↔ devis (vérifiée dans les sources)

- **Une situation peut couvrir plusieurs devis.** Elle est « **globale au BC** : elle porte sur l'ensemble du périmètre contractuel actuellement accepté (tous les devis rattachés) » (modèle métier §12 ; INV-190). CK-17 agrège d'ailleurs ses lignes **par devis**.
- **Un devis peut être couvert par plusieurs situations** (S1, S2, S3… successives).
- Cardinalité résultante : **N–N**. Avec la règle validée (globale), la situation n°k couvre exactement les devis rattachés **au moment de son émission**.
- Aucune source ne décrit une situation limitée à un **sous-ensemble** des devis rattachés. Le texte de la demande parle d'une situation « rattachée au devis A » ; il ne contredit pas INV-190 si on lit « couvre A », mais la formulation laisse ouverte la question d'une situation partielle (voir §7, M1). Je ne l'ai pas tranchée.

### 1.4 Contradiction découverte dans les sources (à ne pas résoudre par supposition)

| Source | Ce qu'elle dit des lignes d'une situation |
|---|---|
| `docs/` : INV-62 (`docs/conception/invariants.md` l.104) et modèle de données V3.12 (l.390) ; INV-62 des documents de travail (GitHub et révision G) ; modèle métier §11 | une situation = **1 ligne `synthese`**, sans référence à une ligne de BC |
| `006_facturation.sql` (livré) et ses tests | une situation = **lignes `avancement`** (une par ligne de BC) + `deduction` ; **`synthese` refusée** |
| Décision validée du 2026-10-17 (D), revue de travail | les lignes d'avancement sont des **situations « historiques »** ; la règle « ne décide pas de la composition des lignes des nouvelles situations, qui reste conforme à INV-62, INV-190 » |

Conséquence directe pour cette étude : **la relation situation ↔ devis qu'on pourrait lire dans les lignes d'avancement n'est pas portée par les décisions validées pour les nouvelles situations.** Elle existe dans le SQL livré, mais son statut documentaire est « historique ». Il serait donc fragile de bâtir la règle d'acompte dessus. C'est la raison pour laquelle je ne recommande pas d'utiliser les lignes comme source de la relation (option A, §3).

Autre divergence mineure notée (sans effet sur cette étude) : `CADRAGE__006` décrit des colonnes `situation_mode`, `situation_valeur_saisie`, `avancement_cumule_pct` sur `factures` ; le 006 livré n'en a aucune (PT-11 reste À CONCEVOIR).

### 1.5 Services applicatifs

Le dépôt **ne contient aucun service** (pas de `src-tauri/src`). Tout ce qui suit sur les services est donc un **contrat à respecter par les futurs services**, pas du code existant.

---

## 2. Proposition technique recommandée — option B : table de liaison minimale, additive

### 2.1 Structure (provisoire, non officielle)

Une table `situation_devis` (nom proposé, hors familles d'identifiants officiels) :

| Colonne | Rôle |
|---|---|
| `facture_id` | FK → `factures(id)` `RESTRICT` ; la facture doit être de type `situation` |
| `devis_id` | FK → `devis(id)` `RESTRICT` |

- **Clé primaire** `(facture_id, devis_id)` : un devis n'est déclaré qu'une fois par situation.
- **Index** sur `devis_id` (c'est la colonne lue par la règle d'acompte).
- **Pas de statut, pas de colonne de traçabilité, pas d'horodatage** (aucune justification métier). Variante possible : `created_at` par convention de tables, **jamais lu** par une règle (choix technique T2).
- Table `STRICT`, comme le reste de la base.

### 2.2 Contraintes d'intégrité

Comme dans le projet (« ni CHECK ni trigger inter-tables » sauf triggers de garde), les contrôles inter-tables sont des **triggers BEFORE INSERT** :

1. la facture désignée est de type `situation` ;
2. le devis est **rattaché au BC de la situation** (existence d'une ligne `bc_devis` avec le même `bc_id`). Cela empêche toute déclaration incohérente (devis d'un autre BC, devis non rattaché) sans comparer d'horodatages ;
3. **UPDATE et DELETE refusés** (immuabilité de l'historique, même esprit qu'INV-53 et INV-184) ; le `DELETE` implicite d'un `INSERT OR REPLACE` est couvert par `recursive_triggers=ON` (D-39).

Aucun nouvel identifiant officiel (INV, TR, CK, D, E, T) : les messages réutiliseraient INV-190 / INV-53 / INV-189 existants.

### 2.3 Création de la relation à l'émission d'une situation

Dans la **même transaction** `BEGIN IMMEDIATE` que l'émission (déjà exigée par 006 pour la facture et ses lignes) : après la facture et ses lignes, le service insère **une ligne `situation_devis` par devis rattaché au BC à cet instant** (lecture de `bc_devis` du BC). Un échec en cours de route annule tout (ROLLBACK) : aucune relation orpheline.

### 2.4 Exploitation par le trigger d'acompte

La règle « aucun acompte après une situation » devient, **par devis** : refuser l'acompte du devis D s'il existe une ligne `situation_devis` pour D. Les devis étant uniques à un BC, aucune jointure sur le BC n'est nécessaire. Le contrôle **sort entièrement des horodatages** : disparaissent la comparaison `created_at` et l'interprétation « ex æquo = refus ». Les autres contrôles de `tr_22_factures_acompte` (rattachement INV-189, après un solde, un acompte actif par devis INV-52, plafond de l'acompte prévu du devis, total du devis, nette ≤ contractuel) restent **tels quels** : le plafond reste calculé à partir du devis concerné seul.

### 2.5 Ce que cela donne sur l'exemple de référence

Devis A 1 000 € avec situation S1 ; devis B 500 € rattaché ensuite.
- `situation_devis` contient (S1, A). L'ajout de B **n'écrit rien** : S1 ne couvre pas B (règle 5), S1 n'est pas modifiée (règle de l'exemple, déjà garantie par `tr_20`/`tr_21`).
- Acompte sur B : autorisé (si plafond et autres règles respectés). Acompte sur A : refusé.
- Situation S2 émise ensuite : (S2, A) et (S2, B). L'acompte sur B (ou son renouvellement après avoir total) est alors refusé.

---

## 3. Alternatives (seulement celles qui ont un intérêt réel)

### A — Lire la relation dans les lignes d'avancement existantes (aucune nouvelle structure)

La relation existe déjà de façon indirecte : ligne d'avancement → ligne de BC → ligne de devis → devis. **Sonde de lecture réalisée** : S1 « couvre » {A} et, après rattachement de B, couvre toujours {A}.

| Avantages | Inconvénients |
|---|---|
| aucune table, aucun backfill, aucune divergence possible entre deux sources | contredit la lecture documentaire (§1.4) : pour les nouvelles situations, la source validée est **une ligne de synthèse** ; relation indirecte (3 jointures) ; **une situation sans ligne** (acceptée par le SQL, sonde ci-dessous) ne couvre rien ; CK-16 reste fondé sur les horodatages |

Non recommandée comme source de vérité, **mais utile comme preuve de rétro-remplissage** (§5).

### C — Jalon ordinal sur `bc_devis` (« numéro de la dernière situation au rattachement »)

Une colonne sur `bc_devis`, validée par SQL à l'insertion (égale au plus grand `situation_numero` du BC à cet instant, ou 0). Une situation n°k couvre un devis si k est supérieur au jalon. Aucune écriture à l'émission des situations, aucune relation « oubliable ».

| Avantages | Inconvénients |
|---|---|
| garantie SQL la plus forte (rien à oublier à l'émission ; le jalon est vérifié) ; aucune CK d'exhaustivité nécessaire | **modifie une table livrée (005b)** et remplace son trigger d'insertion ; tous les helpers de tests qui insèrent dans `bc_devis` sont à adapter ; **ne sait exprimer que la situation globale** (impossible si une situation partielle devenait légitime, M1) ; historique : jalon inconnu (NULL) pour l'existant, non prouvable ; exige que `situation_numero` soit imposé strictement croissant par le SQL (aujourd'hui seulement unique) |

À retenir si le métier confirme que la situation est **toujours globale** et accepte de toucher `bc_devis`.

### Écartées

Un `devis_id` sur `factures` pour les situations (impossible : une situation couvre plusieurs devis) ; un statut ou une table d'historique (aucune justification métier) ; un maintien des horodatages (contraire à la règle 6).

---

## 4. Conséquences sur les services et sur les contrôles SQLite

| Cas demandé | Comportement attendu | Mécanisme |
|---|---|---|
| 1. Émission d'une situation pour un devis | la facture, ses lignes **et** une ligne `situation_devis` par devis rattaché sont écrites ensemble | **service** (une transaction) ; SQL : FK, PK, triggers d'insertion (§2.2) |
| 2. Ajout d'un devis B au BC après la situation | `bc_devis` reçoit B ; `situation_devis` et la situation **ne bougent pas** | `bc_devis` inchangé ; immuabilité (tr_20, tr_21, nouveaux triggers) |
| 3. Acompte sur B | autorisé si les autres règles sont respectées ; `devis_id` = B exclusivement | `tr_22_factures_acompte` (existence dans `situation_devis`) |
| 4. Acompte sur A, déjà couvert | refusé (`INV-58`, « sur ce devis ») | `tr_22_factures_acompte` |
| 5. Nouvelles situations | couvrent tous les devis rattachés à leur émission | service + triggers d'insertion de `situation_devis` |
| 6. Modification ou suppression d'un rattachement de devis | **n'existe pas** : `bc_devis` et `bc_lignes` sont immuables (INV-184, INV-186) ; `situation_devis` serait immuable ; un avoir sur une situation ne change pas la couverture | triggers existants + nouveaux |
| 7. Échec de l'émission d'une situation | aucune ligne `situation_devis` ne subsiste | ROLLBACK de la transaction du service (FK ⇒ pas d'orphelin) |

**Limite assumée, identique à celle de 006 pour les lignes** : SQLite ne peut pas imposer qu'une situation **ait** toutes ses lignes `situation_devis` au COMMIT. Si le service en oublie une, la situation ne couvre pas le devis et l'acompte correspondant serait accepté à tort. Parades : transaction unique du service ; test d'atomicité ; **diagnostic** à définir (voir M4/T4). Cette limite existe aussi pour A et n'existe pas pour C.

**Ne pas déplacer dans l'interface** : le refus d'acompte reste dans le trigger ; le service peut le précontrôler pour un message clair, mais n'est pas la garantie.

**Import** : non traité ici, comme demandé ; l'application de conversion devra fournir les lignes `situation_devis` des situations historiques au format V6.

---

## 5. Stratégie de migration corrective

### 5.1 Où placer le changement

`009a` et `009b` ne sont **pas livrées** (absentes de l'arbre de GitHub). Deux voies, à arbitrer (T3) :

- **(i) Intégrer à la `009b` avant sa livraison** : la condition d'ordre y est encore la version à horodatages, jamais validée ; aucune renumérotation ; aucune migration livrée modifiée (001-009 intactes). Mélange toutefois un sujet de plus dans une migration déjà large.
- **(ii) Nouvelle corrective `009c`** (rang 15) : isole le sujet ; **décale 010 au rang 16** (et `010a`/`011` à 17/…), donc renumérote une seconde fois les documents de travail. À éviter sans besoin.

Dans les deux cas : **pas de migration 010**, aucune migration de 001 à 009 modifiée.

### 5.2 Base V6 existante dotée de situations (anciennes migrations)

Les factures, lignes et situations restent **intactes** (immuables). Pour les situations déjà enregistrées, la relation peut être reconstituée **seulement si elle est prouvable** :

| Situation existante | Preuve disponible | Traitement possible |
|---|---|---|
| a des lignes d'avancement sur les lignes de BC du devis D | lignes → ligne de BC → ligne de devis → D | rétro-remplissage de (S, D) : **prouvé**, sans horodatage |
| n'a **aucune ligne**, ou des lignes sur une partie seulement des devis rattachés | aucune | **non reconstituable de façon fiable** : options ci-dessous, aucune choisie |

Options pour le non-reconstituable (décision métier, M4) :
1. ne rien écrire (la situation ne couvre aucun devis : acompte permis partout, risque d'acompte après situation sur du **déjà** existant) ;
2. écrire (S, D) pour tous les devis aujourd'hui rattachés (prudent, mais **non prouvé** : peut bloquer à tort un devis ajouté après S) ;
3. écrire (S, D) selon l'ordre des `created_at` (seule trace chronologique, mais c'est exactement la déduction par horodatage que la règle 6 interdit) ;
4. ne rien écrire et **lister** ces situations par un diagnostic pour arbitrage humain, puis corriger par une donnée explicite.

On ne sait pas s'il existe des bases V6 réelles contenant des situations : le dépôt ne contient aucune base, et les seules situations connues sont celles fabriquées par les tests.

---

## 6. Plan de tests et risques de régression

### 6.1 Tests proposés (non écrits, non exécutés)

| # | Test | Attendu |
|---|---|---|
| 1 | situation sur A puis acompte sur B (même BC) | autorisé si plafond et autres règles respectés |
| 2 | situation sur A puis acompte sur A | refusé `INV-58` |
| 3 | ajout de B après la situation | `situation_devis` et lignes de S1 strictement inchangées |
| 4 | S1 {A}, S2 {A, B} puis S3 : périmètres différents | acompte refusé sur A ; sur B refusé seulement après S2 |
| 5 | rattachements incohérents : devis d'un autre BC, devis non rattaché, facture qui n'est pas une situation | refus par trigger |
| 6 | atomicité : échec en cours d'émission (SAVEPOINT puis ROLLBACK) | ni facture, ni lignes, ni `situation_devis` |
| 7 | immuabilité : UPDATE, DELETE, `INSERT OR REPLACE` sur `situation_devis` | refusés |
| 8 | situation créditée par avoir total | la couverture demeure (interprétation M2) |
| 9 | situation à 0 % de progression | couvre le devis (interprétation M2) |
| 10 | régression : plafond d'acompte indépendant par devis, un acompte actif par devis, rattachement INV-189, aucun acompte après un solde, nette ≤ contractuel | inchangés |
| 11 | mutations : retirer la condition ; condition au niveau du BC ; condition sur un autre devis ; PK absente | toutes détectées |
| 12 | rejeu de l'existant sur la chaîne complète | aucun écart nouveau |
| 13 | rétro-remplissage (si adopté) : situation avec lignes ⇒ rangées déduites ; sans lignes ⇒ aucune rangée inventée | conforme à l'option arbitrée |

### 6.2 Réellement exécuté dans cette étude

Uniquement des **sondes de lecture** (hors dépôt, jetables) sur la chaîne 001-009 **telle que sur GitHub** :
1. S1 émise sur A : les lignes d'avancement désignent {A} ; après rattachement de B, S1 désigne toujours {A}, ses lignes inchangées, CK-16 vide.
2. SQL de GitHub : acompte accepté sur A **et** sur B après S1 (aucune règle d'ordre dans 006).
3. Une situation sans ligne est acceptée par le SQL, ne désigne aucun devis, et CK-16 signale 3 lignes manquantes.
4. `facture_lignes` et `bc_devis` : UPDATE et DELETE refusés (INV-53, INV-184).

Ces sondes **ne testent pas la solution proposée**. La suite complète exécutée plus tôt dans la session (2 042 tests verts) porte sur la **variante à horodatages** de la révision G, pas sur celle-ci.

**Limites de l'environnement** : pas de runner Rust (les tests l'émulent), pas de service applicatif dans le dépôt, SQLite de test ≠ SQLite embarqué, aucune base locale réelle.

### 6.3 Risques de régression

- **~10 tests de `test_009b`** (les 8 nouveaux cas d'ordre par devis, plus `aucun_acompte_apres_une_situation` et `une_situation_deja_creditee…`) fabriquent des situations brutes sans lignes ni couverture : ils devraient déclarer la couverture. L'assistant `rattacher_a` (lien daté) et le test d'ex æquo disparaîtraient.
- Les fabriques de tests qui émettent des situations (`emettre_situation`) **ne créeraient pas** de couverture tant qu'on ne les adapte pas : les tests d'ordre pourraient alors passer à tort. À traiter en même temps.
- Documents de travail : INV-58, TR-22, modèle §3.2 (réécrire la condition sans horodatage), INV-190 (couverture), signalement de la contradiction INV-62.
- Aucun impact sur 001-009, ni sur la numérotation, ni sur les données existantes.

---

## 7. Points restant à arbitrer

### Décisions métier

| # | Question | Pourquoi elle compte |
|---|---|---|
| **M1** | Une situation est-elle **toujours globale** (tous les devis rattachés à l'émission) ou peut-elle être **limitée à certains devis** ? | Détermine B vs C : seule B sait exprimer une situation partielle. Les sources validées disent « globale » ; la formulation de la demande n'est pas explicite |
| **M2** | Une situation **entièrement créditée** (avoir total) ou **à 0 %** de progression « couvre-t-elle » encore le devis ? | Interprétation retenue : oui (« émise » = existante). Non confirmée pour le 0 % |
| **M3** | **Contradiction INV-62 / docs ↔ 006** : une nouvelle situation compte-t-elle des lignes d'avancement ou une seule ligne de synthèse ? | Décide si les lignes peuvent servir de preuve (rétro-remplissage) et si 006 est conforme sur ce point |
| **M4** | Traitement des situations existantes **non reconstituables** (§5.2, options 1 à 4) | Aucune option n'est choisie par l'étude |

### Choix techniques

| # | Choix |
|---|---|
| T1 | Nom de la table (provisoire) |
| T2 | `created_at` sur la table de liaison ou non (jamais lu par une règle) |
| T3 | Intégrer à `009b` (i) ou ajouter `009c` (ii) |
| T4 | Diagnostic d'exhaustivité (situation sans couverture pour un devis rattaché avant elle) : sa définition de « rattaché avant elle » exigerait les horodatages **en diagnostic seulement** ; acceptable, ou renoncer à ce diagnostic |
| T5 | Exiger ou non, côté SQL, que `situation_numero` soit strictement croissant (utile seulement pour C) |

---

## 8. Verdict

- **Cohérence avec les sources** : la solution B est cohérente avec les règles validées du §2 de la demande, additive (aucune table livrée modifiée), indépendante de la composition des lignes de situation et sans horodatage dans la règle bloquante. Elle exprime la cardinalité N–N sans la présupposer.
- **Prête à être soumise à validation** : **oui sur le plan technique**, sous réserve des arbitrages **M1 à M4**. Informations manquantes : existence éventuelle de bases V6 avec situations réelles ; confirmation du périmètre global ou partiel d'une situation.
- **Deux points à signaler dès maintenant** : (1) la règle d'ordre n'existe pas dans la chaîne de GitHub, seulement dans le patch h ; (2) la contradiction INV-62 / 006 (§1.4) existe indépendamment de cette étude et mérite sa propre décision.

## Recommandation

Adopter **B** (table de liaison minimale `situation_devis`, immuable, écrite par le service à l'émission, lue par `tr_22_factures_acompte`), après réponses à **M1 à M4**, en l'intégrant à la `009b` tant qu'elle n'est pas livrée. Si le métier confirme que la situation est **toujours globale** et accepte de toucher `bc_devis`, **C** offre une garantie SQL plus forte au prix d'une table livrée modifiée. Ne pas retenir A comme source de vérité. **Aucune implémentation avant validation.**
