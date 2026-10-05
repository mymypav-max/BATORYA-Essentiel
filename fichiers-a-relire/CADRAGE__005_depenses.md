# CADRAGE — 005b_bc_multi_devis (M-B, rang 7)

Statut : **décisions Q-A à Q-D arbitrées par Rémy (2026-10-05)** — voir section 9. Le SQL est écrit conformément à ces arbitrages.
Dépôt audité : `main` = `origin/main` = `b0a3a8d` (001 → 005a identiques à GitHub, 541 tests verts).
Documents de référence : ceux de `fichiers-a-relire/` (versions `MAJ__*`, V3.13). `docs/` contient encore les anciennes versions V3.12 : **non utilisé comme référence**.

Légende des natures : **[DOC]** règle documentée (source citée) · **[VAL]** décision déjà validée · **[DED]** déduction technique · **[PROP]** proposition (non validée dans les documents) · **[À VALIDER]** décision demandée.

---

## 0. Contradictions et écarts à signaler avant de figer le SQL

| # | Constat | Sources | Traitement proposé |
|---|---|---|---|
| C1 | **INV-175** dit que le service copie dans le BC la liste S du devis, *remise et acompte compris*. Le modèle §4.7 / §4.19 l.11 / PT-7 **retire** `remise_*` et `acompte_*` de `bons_commande` (portés par chaque devis). Un BC à N devis n'a pas une remise unique. | INV-175 ; modèle §4.7, §4.19 l.11 ; INV-189, INV-192 | Suivre §4.7 (retrait). **[À VALIDER] Q-A.** |
| C2 | Le tableau §17.1 place `devis_origine_id` dans M-A et dit que M-B en dépend. **005a (poussée) ne l'a pas créé** (arbitrage « Conservateur »). La colonne n'existe pas au rang 6. | modèle §17.1 ; en-tête de 005a ; tests 005a (`assertNotIn("devis_origine_id")`) | **Décision (contre-relecture 2026-10-05) : non créée** (voir §6). |
| C3 | Le brief demande de tester « ajout refusé après solde » et « avoir ultérieur ne rouvre pas ». **Aucune table de facture n'existe avant 006** : ces deux règles ne peuvent pas être garanties ni testées dans le schéma 005b. | INV-187 (« ne dépend d'aucune définition technique de facturé à 100 % »), INV-43 (`date_100_facture` n'intervient pas dans le rattachement), modèle §4.7 (tableau SQL/service/CK : « — (tranche Facturation) ») | Règle de **service** + **CK-14**. Les tests 005b vérifient que le SQL **ne** porte **pas** cette règle (aucun cache ne ferme le BC). Voir §3. |
| C4 | Vocabulaire : le brief dit « validée/finalisée », INV-187 dit « **rédigée/validée** » (plus tôt, donc plus strict). | INV-187, E-16 | Employer « rédigée/validée » (texte validé). |
| C5 | TR-17 « lecture du devis via le lien (PT-6) » est **impossible à l'INSERT du BC** : le lien `bc_devis` n'existe pas encore (il référence le BC). La vérification « le BC naît d'un devis accepté, du même client » ne peut donc plus se faire sur `bons_commande`. | modèle §8 (TR-17, TR-99) | Elle passe sur **TR-99** (INSERT du lien, y compris rang 1). Conséquence : un BC peut exister sans lien dans la transaction de création. **Décision (contre-relecture) : accepté comme conséquence normale de la reconstruction ; aucun trigger bloquant.** CK-14 (tel que spécifié) ne couvre pas « BC sans aucun devis lié » : **formalisé dans CK-14** (écart documentaire à reporter dans le modèle §14) ; tests `ControlesCK`. |
| C6 | **Q4 / INV-186 / INV-36** (contenu contractuel du BC immuable *dès sa création*) contredit 004 : tant que le BC n'est pas gelé, `tr_12_bons_commande_modifiable` ne protège que `id`, `devis_id`, `created_at` ; lignes et garanties de lignes sont modifiables/supprimables avant gel (régénération, INV-38 ancien). Vérifié par essai au rang 6. | 004 `tr_12_*`, `tr_13_*` ; INV-36, INV-38, INV-186 ; modèle TR-12, TR-13 | 005b aligne sur Q4 (voir §4). |
| C7 | 005a (en-tête) renvoie **PT-16** (caches d'un BC annulé après avoir) à M-B ; PT-16 est « À CONCEVOIR / à confirmer ». | en-tête 005a ; PT-16 | **[À VALIDER] Q-C.** |
| C9 | Le modèle §14 range « `montant_contractuel_ht` = Σ `total_ht` des devis rattachés » à **deux endroits** : dans la définition détaillée de **CK-13** et le tableau §4.19 (« contractuel = Σ `total_ht` … **CK-13** »), et dans le résumé en tête de §14 sous **CK-14**. | modèle §14 (résumé et paragraphe CK-13), §4.19 | **Classé CK-13** (2 sources contre 1, et CK-13 = miroir de S, INV-175, INV-39). CK-14 = rattachement : BC sans lien, devis dans un seul BC, devis lié accepté et du même client, lien postérieur à l'annulation, solde (006). Le résumé de §14 est à corriger dans le modèle (hors périmètre). |
| C8 | Le modèle donne `date_acceptation` du BC = devis d'origine (PT-7) ; la migration ne peut pas le vérifier ni le corriger. | INV-176, modèle §4.7 | Aucune action SQL ; CK-13. |

---

## 1. Audit du modèle actuel devis → BC (rang 6)

Relation : **1 devis → 1 BC**, portée par `bons_commande.devis_id INTEGER NOT NULL UNIQUE REFERENCES devis(id) ON DELETE RESTRICT` (004, `CREATE TABLE bons_commande`). Le `UNIQUE` n'est **pas** le seul obstacle. Obstacles, vérifiés dans le SQL et par essais :

| # | Obstacle | Où | Preuve |
|---|---|---|---|
| O1 | `devis_id` `NOT NULL UNIQUE` : un deuxième BC pour le même devis est refusé ; surtout, il n'existe **aucune place** pour un 2ᵉ devis dans un BC (un BC porte une seule colonne `devis_id`). | 004 | `UNIQUE constraint failed: bons_commande.devis_id` |
| O2 | `tr_13_bc_lignes_insert/update` : `dl.devis_id <> b.devis_id` ⇒ une ligne de BC ne peut venir que **du** devis du BC. | 004 | essai : ligne d'un autre devis refusée (INV-175) |
| O3 | `tr_13_bc_lignes_insert` (et garanties) : INSERT refusé si `frozen_at IS NOT NULL OR statut='annule'` ⇒ aucun rattachement après gel. | 004 | essai : BC gelé refuse la ligne |
| O4 | `tr_12_bons_commande_gele` : `montant_contractuel_ht` immuable après gel ⇒ le contractuel ne peut pas augmenter au rattachement. | 004/005a | essai : refus |
| O5 | `tr_17_bons_commande_insert` lit `d.id = NEW.devis_id` (devis accepté, même client). | 004/005a | — |
| O6 | `tr_18_devis_statut_avec_bc` lit `b.devis_id = OLD.id`. | 004/005a | — |
| O7 | `remise_*`, `acompte_*` + 8 CHECK sur `bons_commande` : une seule remise/un seul acompte par BC. | 004 | — |
| O8 | `tr_12_*` (3 triggers) référencent `devis_id`, `remise_*`, `acompte_*`. | 004/005a | — |

**Non-obstacles (vérifiés, aucune modification)** : `bc_lignes.devis_ligne_id UNIQUE` (une ligne de devis n'apparaît qu'une fois : règle voulue, INV-175) ; `bc_lignes UNIQUE(bc_id, ordre)` (le service numérote à la suite, §4.19 l.18) ; `devis` (accepté donc verrouillé, INV-181) ; `devis_revisions` (FK vers `devis` seulement) ; `depenses.bc_id` (FK `RESTRICT` vers `bons_commande(id)`, 005, conservée par le renommage) ; `bc_ligne_garanties` (lien par `ligne_id` seulement).

Comportement devis : après acceptation, le devis est verrouillé (005a `tr_10_devis_verrouille`) ; il ne quitte `accepte` que si son BC est annulé (`tr_18`). Les révisions (`devis.revision`, `devis_revisions`) concernent **le même devis** et ne sont possibles qu'en `en_attente` (INV-196) : sans rapport avec le multi-devis.

---

## 2. Modèle cible minimal

**[DOC] modèle §4.7 (PT-6, proposition) + [VAL] E-16/INV-187.** Une seule table nouvelle :

`bc_devis` : `id` PK AUTOINCREMENT · `bc_id` NN FK→`bons_commande` RESTRICT · `devis_id` NN **UNIQUE** FK→`devis` RESTRICT · `rang` INTEGER NN `>= 1` · `created_at` TS NN · `UNIQUE(bc_id, rang)`. STRICT. Jamais modifiée ni supprimée.

Pourquoi une table et pas `devis.bc_id` **[DED]** : le devis accepté est verrouillé (INV-181) ; le lien est posé *après* l'acceptation, donc une colonne de `devis` obligerait à rouvrir le verrou. Pourquoi pas plus : pas de table générique, pas d'avenant ; chaque devis garde son numéro, son statut, ses révisions, ses dates (aucune colonne de `devis` touchée). `rang` : 1 = devis d'origine (§4.7).

`bons_commande` reconstruite : retrait de `devis_id` ; retrait de `remise_*`/`acompte_*` **si Q-A = retirer**. Tout le reste inchangé (dont `frozen_at` et ses deux CHECK, PT-8 resté « Conservateur »).

Aucune colonne ajoutée à `bc_lignes` (voir §5).

---

## 3. Règle de rattachement et « solde rédigé/validé »

**[VAL] INV-187, E-16, Q17, Q23 corrigé.** Un devis accepté crée un BC ou rejoint un BC existant du même client, tant que le solde n'est pas rédigé/validé ; un avoir sur le solde ne rouvre pas ; un BC annulé ne reçoit rien.

Matérialisation dans le schéma actuel — **aucun champ existant n'est un marqueur fiable** :
- `date_100_facture` : cache « date d'émission du premier solde actif », **sort en cas d'avoir total** (INV-43, PT-9) ; INV-43 dit expressément qu'elle « n'intervient pas dans la règle de rattachement ».
- `statut = 'termine'` : cache, revient à `en_cours` après avoir (« retour_en_cours », modèle §4.7).
- `frozen_at` : gel progressif **retiré** (INV-33/34 retirés le 2026-10-03) ; sort non tranché (PT-8) ; aucune règle V3.13 ne dit quand il est posé.
- Les factures n'existent pas avant 006.

⇒ **[DED]** La règle « tant que le solde n'est pas rédigé/validé » est une **règle de service** (porte du rattachement) contrôlée par **CK-14** ; elle ne peut pas être garantie par le schéma 005b (modèle §4.7, tableau : « — (tranche Facturation) ; un trigger ne pourra être ajouté qu'avec la tranche Facturation »). Ne pas inventer de champ. 006 devra la poser (index/trigger sur les factures de solde).

Ce que le SQL 005b garantit (TR-99, **[DOC]** modèle §8) : à l'INSERT du lien, devis `accepte`, même `client_id` que le BC, BC non annulé ; UPDATE et DELETE du lien refusés ; un devis dans un seul BC (UNIQUE).
**[VAL] Q-D** : le `rang` est un ordre d'association, pas un invariant métier : `rang >= 1` et `UNIQUE(bc_id, rang)` seulement ; **aucune contiguïté, aucune valeur imposée** (rang 1 non exigé), aucune renumérotation des données existantes.

---

## 4. Compatibilité avec le BC verrouillé (004 + 005a)

Distinction du brief : **ajouter un devis** (permis) / **modifier le contenu d'un devis intégré** (interdit : le devis est `accepte`, verrouillé par 005a ; 005b ne touche à aucun trigger de `devis` sauf `tr_18`, recréé).

Triggers de `bons_commande` (tous perdus avec la table, à recréer) :

| Trigger 004/005a | Sort 005b | Nature |
|---|---|---|
| `tr_01_bons_commande_numero_immuable` | recréé identique (G-3) | [DOC] |
| `tr_12_bons_commande_modifiable` | **supprimé** : fusionné dans le trigger de contenu contractuel ci-dessous | [VAL] Q4/INV-186 |
| `tr_12_bons_commande_gele` | **remplacé** par `tr_12_bons_commande_contrat` : BC **non annulé**, gelé ou non — immuables : `id`, `client_id`, snapshots (6 colonnes), `date_acceptation`, `created_at`, `origine`, `legacy_*` ; **modifiable** : `montant_contractuel_ht` (rattachement), caches, `date_debut`, `date_fin`, annulation, `frozen_at`, `updated_at` ; plus de `devis_id`/`remise_*`/`acompte_*` | [VAL] Q4 ; [DOC] modèle TR-12 |
| `tr_12_bons_commande_annule` | recréé sans `devis_id` (+ sans `remise_*`/`acompte_*` si Q-A) ; PT-16 (caches) reporté à 006 (Q-C) | [DOC] / [VAL] Q-A, Q-C |
| `tr_14_bons_commande_frozen_at` | recréé identique (PT-8 conservateur) | [VAL] |
| `tr_17_bons_commande_insert` | **réduit** à l'état de naissance (les deux contrôles sur le devis passent à TR-99, C5) | [DOC] modèle TR-17/TR-99 |
| `tr_19_bons_commande_no_delete` | recréé identique (G-3) | [DOC] |

Triggers hors `bons_commande` à retirer puis recréer (référencent `bons_commande`) :
- `tr_18_devis_statut_avec_bc` (sur `devis`) : réécrit via `bc_devis` (« devis rattaché ne quitte `accepte` que si son BC est annulé », aucune cascade) — [DOC] TR-18.
- `tr_13_bc_lignes_insert/update/delete` : INSERT seulement si BC non annulé **et** ligne de devis appartenant à un devis lié à ce BC ; **UPDATE et DELETE toujours refusés** — [DOC] modèle TR-13 ; [VAL] Q4.
- `tr_13_bc_ligne_garanties_insert/update/delete` : INSERT seulement si BC non annulé ; UPDATE/DELETE toujours refusés.
- Le test de gel dans INSERT de lignes/garanties (`frozen_at IS NOT NULL`) : **[VAL] Q-B** : seul un BC annulé refuse l'INSERT.

Nouveau : `tr_99_bc_devis_insert`, `tr_99_bc_devis_no_update`, `tr_99_bc_devis_no_delete` (BEFORE, convention du dépôt ; avec `recursive_triggers=ON`, le DELETE implicite d'un `INSERT OR REPLACE` est refusé).

Non-régression 005a : G-1 (clients : `tr_12_*` sans clause `a_rattacher`) — la clause n'est pas réintroduite ; G-2 (`tr_17`, `tr_18` lisent des colonnes existantes) — recréés avec le schéma 005b ; G-3 (`tr_01`, `tr_14`, `tr_19`) — recréés. Les 28 triggers de 005a hors BC ne sont pas touchés, hormis `tr_18` qui n'est pas un trigger de 005a mais de 004 recréé par 005a.

---

## 5. Lignes de BC

- **Aucune colonne nouvelle** sur `bc_lignes` **[DED]** : le devis d'une ligne s'obtient par `devis_ligne_id → devis_lignes.devis_id` (UNIQUE, RESTRICT) ; l'appartenance au BC par `bc_devis`. Ajouter `devis_id` dupliquerait une information déjà portée (risque d'incohérence) — pas de « justification documentaire ou technique précise » (brief §5).
- Plusieurs devis contribuent aux lignes d'un BC : `UNIQUE(bc_id, ordre)` ne l'empêche pas (numérotation à la suite par le service, §4.19 l.18).
- **Garanties** : `bc_ligne_garanties.ligne_id ON DELETE CASCADE` → `RESTRICT` (PT-5, §4.19 l.17, dans le contenu M-B) exige de reconstruire `bc_ligne_garanties`. Effet de comportement nul (DELETE de ligne/garantie toujours refusé après 005b). **[VAL] Q-C : inclus.**
- Miroir ligne à ligne : jamais en trigger (INV-175, modèle §4.7) ; CK-13.

---

## 6. Devis, révisions, `devis_origine_id`

- Révision = même devis, même numéro, `revision >= 1` ; devis supplémentaire = **nouvel objet** avec son propre numéro DEV, statut, historique, révisions, acompte. Aucune colonne de `devis` ni de `devis_revisions` n'est modifiée par 005b ; aucune unicité de `devis` n'est touchée.
- Un devis supplémentaire est un devis comme un autre (numéro unique DEV) ; son lien au BC est **exclusivement** `bc_devis`.
- **Décision explicite : `devis_origine_id` n'est pas créé en 005b.**
  - Aucun besoin métier ou technique supplémentaire démontré pour 005b.
  - Le rattachement historique est conservé dans `bc_devis` ; le premier devis historique d'un BC se lit par son lien repris (rang initial : `ORDER BY rang LIMIT 1`).
  - Aucune colonne supplémentaire dans `bons_commande` ni dans `devis` (l'ajouter obligerait aussi à modifier les listes d'immutabilité des triggers `tr_10_devis_*` de 005a : risque de régression).
  - Toute introduction future de `devis_origine_id` nécessitera une décision dédiée.
  - Verrouillé par `test_DECISION_devis_origine_id_n_est_cree_nulle_part` (aucune table, aucun objet, aucun code SQL de 005b).

---

## 7. Compatibilité avec 006 (Facturation) — sans l'implémenter

006 doit distinguer les devis d'un BC, leurs acomptes (INV-189 : « lié à son devis d'origine »), les situations et le solde. 005b préserve : l'identité de chaque devis (numéro, acompte prévu `devis.acompte_*`, remise `devis.remise_*`) ; le lien devis ↔ BC et l'ordre de rattachement (`bc_devis`) ; les lignes de BC reliées à leur ligne de devis ; `bons_commande.id` inchangé (FK `depenses.bc_id`). Rien de 006 n'est créé.

---

## 8. Classement de chaque règle (SQL / trigger / service / CK)

| Règle | Mécanisme | Source |
|---|---|---|
| Un devis dans un seul BC | **SQL** `UNIQUE(devis_id)` | PT-6 |
| Lien jamais modifié/supprimé | **trigger** TR-99 | PT-6 |
| Devis `accepte`, même client, BC non annulé, à l'INSERT du lien | **trigger** TR-99 | modèle §8 |
| `rang` ≥ 1, `UNIQUE(bc_id, rang)` (pas de contiguïté : Q-D) | **SQL** | PT-6 ; Q-D |
| Solde rédigé/validé ⇒ plus de devis ; avoir ne rouvre pas | **service** + **CK-14** (+ SQL en 006) | INV-187 |
| Contractuel = Σ `total_ht` des devis liés | **service** + **CK-13** (C9) | INV-39, modèle §4.19 |
| Copie 1:1 lignes/garanties, miroir de S | **service** + **CK-13** | INV-175 |
| BC sans aucun devis lié dans `bc_devis` | **CK-14** (formalisé ; aucun trigger) | C5 |
| Devis lié non accepté (BC non annulé) ; client du devis ≠ client du BC ; lien postérieur à l'annulation du BC | **CK-14** (diagnostic, en plus des triggers TR-18 / TR-99) | modèle §14 |
| Règle générale | intégrité structurelle → SQL ; cohérence inter-tables → diagnostic CK ; orchestration → service | modèle §4.19, D-36 |
| Contenu contractuel du BC immuable ; lignes/garanties immuables | **triggers** TR-12, TR-13 | Q4, INV-186 |
| Devis lié ne quitte `accepte` que si BC annulé | **trigger** TR-18 | INV-175 |
| Naissance du BC (`en_cours`, caches à zéro) | **trigger** TR-17 + CHECK | INV-40 |
| BC jamais supprimé | **trigger** TR-19 + FK RESTRICT | INV-174 |

---

## 9. Protocole de reconstruction (conventions §5) et décisions

Étapes SQL du fichier (gardes `foreign_keys = 0` et `user_version = 6`, comme 005a ; aucun BEGIN/COMMIT/PRAGMA d'écriture ; `user_version = 7` posé par le runner dans la transaction) :
1. `DROP TRIGGER` : tous ceux qui référencent `bons_commande` (tr_18 sur `devis` ; tr_13 ×6 sur lignes/garanties ; ceux de `bons_commande` partent avec la table).
2. `CREATE TABLE bc_devis`.
3. `CREATE TABLE bons_commande_new` (structure cible) ; copie `INSERT … SELECT` en conservant `id`, numéros, dates, caches, `created_at`/`updated_at` ; `sqlite_sequence` monotone ; reprise des liens : `INSERT INTO bc_devis (bc_id, devis_id, rang, created_at) SELECT id, devis_id, 1, created_at FROM bons_commande ORDER BY id` (**[VAL] Q-D** : migration de données volontaire, conventions §5).
4. `DROP TABLE bons_commande` ; `RENAME` ; recréation des index (`idx_bons_commande_client_id`, `idx_bons_commande_statut`) ; (si Q-C : même chose pour `bc_ligne_garanties`).
5. Recréation des triggers. Contrôles du runner : `foreign_key_check` vide, `integrity_check` ok, `user_version = 7`.
6. **Garde anti-perte [VAL] Q-A** : si Q-A = retirer, refus (CHECK de table temporaire, lecture seule) de la migration si un BC existant a `remise_*`/`acompte_*` différents de ceux de son devis, car l'information ne serait plus récupérable.

Aucune ligne métier n'est insérée en dehors de la reprise des liens existants (1 ligne `bc_devis` par BC existant).

### Décisions arbitrées (2026-10-05)

| Id | Sujet | Décision |
|---|---|---|
| Q-A | `remise_*`/`acompte_*` de `bons_commande` | **Retirer**, avec garde anti-perte (la migration refuse de s'exécuter si un BC existant diffère de son devis) |
| Q-B | Gel et rattachement | `frozen_at` ne ferme pas le rattachement : INSERT de lignes/garanties refusé **seulement** si le BC est annulé |
| Q-C | Périmètre | **PT-5 inclus** (`bc_ligne_garanties` en RESTRICT) ; **PT-16 reporté** (006) : `tr_12_bons_commande_annule` garde la liste actuelle, moins les colonnes retirées |
| Q-D | Reprise des liens | Oui, 1 ligne `bc_devis` par BC existant (`rang >= 1`, `created_at` du BC) ; `UNIQUE(bc_id, rang)` ; **pas** de rang contigu ni imposé |
| — | `devis_origine_id` | **Non créé** (décision explicite, §6) |

---

## 10. Vérification

### 10.1 Passe initiale (2026-10-05)
- Campagne de mutation : 703 mutants du SQL (+ 7 du runner de test, + 11 manuels). 88 survivants au premier passage ; 50 tués par les tests ajoutés ensuite (égalité des définitions de `bons_commande` et `bc_ligne_garanties` avec 004 hors colonnes retirées, STRICT par `pragma_table_list`, valeurs non uniformes et trou d'identifiants dans la base peuplée) ; 38 restants, tous équivalents, redondants ou non testables.
- Limite connue, commune à 003 et 004 : la condition « solde rédigé/validé » (INV-187, Q23) n'est portée par aucune donnée avant 006 ; elle reste une règle de service contrôlée par CK-14.

### 10.2 Contre-relecture (2026-10-05) — aucune modification du SQL
- **SQL 005b inchangé** : seuls ce cadrage et le fichier de tests sont modifiés.
- Tests ajoutés : `ControlesCK` (11 : CK-13 et CK-14 vides sur données cohérentes, « BC sans aucun devis lié » diagnostiqué par CK-14 sans trigger, contractuel ≠ Σ classé CK-13, lignes non copiées, devis annulé / non accepté, autre client, lien postérieur à l'annulation, devis dans plusieurs BC impossible, requêtes en lecture seule, résultat sur une base migrée) et `ArbitragesRelecture` (6 : Q-A sans normalisation ni perte, Q-B cinq cas, Q-D reprise exacte sans renumérotation ni contiguïté, `devis_origine_id` absent).
- Test de diagnostic CK-13/CK-14 de la classe multi-devis remplacé par `ControlesCK` (classement corrigé, C9).
- Fixture d'annulation du BC : `cancelled_at` postérieur aux `created_at` par défaut, pour que le diagnostic « lien postérieur à l'annulation » ne dépende pas de l'horloge.
- Suite 005b : 153 tests verts ; cumul 001–005b : 694 tests verts ; `integrity_check` = ok et `foreign_key_check` vide (base fraîche et base migrée peuplée).
