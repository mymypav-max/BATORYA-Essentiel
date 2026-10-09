# RAPPORT DE MUTATION 008 — Garanties

Périmètre : `src-tauri/migrations/metier/008_garanties.sql` (143 lignes ; 1 table STRICT, 3 index explicites + 1 index de `UNIQUE`, 3 triggers).
Suite évaluée : `src-tauri/tests/metier/test_008_garanties.py` (254 tests, 899 sous-tests) rejouée en entier, arrêt au premier échec.
Aucun fichier 001–007, aucun cadrage, aucun document officiel n'est touché. Les outils (`mut008.py`, `genmut008.py`, `diff008.py`, `equiv008.py`, `equiv008b.py`) sont des outils de travail hors dépôt, dérivés de ceux de 007.
Rien n'a été commité ni poussé.

## 1. Résultat final (SQL final, tests finaux)

| | Total | Tués | Invalides | Délais dépassés | Survivants |
|---|---:|---:|---:|---:|---:|
| **Tous mutants** | **454** | **439** | **4** | **0** | **11** |

476 mutants générés, 22 doublons de texte éliminés → 454 distincts. Les 11 survivants sont qualifiés **équivalents démontrés** (§4), chacun individuellement ; **aucune lacune métier dans le SQL** (le SQL n'a pas changé entre la première et la dernière passe) ; les lacunes réelles de test découvertes en route (§3) sont corrigées par des tests.

| Famille | Mutants | Tués | Invalides | Survivants |
|---|---:|---:|---:|---:|
| Table / CHECK (arbre `AND`/`OR`, opérateurs, GLOB, littéraux, `substr`, `CASE`, `printf`, `CAST`, `date()`) | 121 | 115 | 0 | 6 |
| Table / colonnes, listes `IN`, NOT NULL, DEFAULT, STRICT, AUTOINCREMENT, FK, UNIQUE | 42 | 42 | 0 | 0 |
| Index (suppression, colonne remplacée, unicité) | 27 | 27 | 0 | 0 |
| Trigger / suppression d'un trigger | 3 | 3 | 0 | 0 |
| Trigger `tr_51` / région `WHERE` des gardes G1–G4 (conjoncts, opérateurs, littéraux, colonnes, `NEW`/`OLD`, `EXISTS`) | 192 | 192 | 0 | 0 |
| Trigger / instruction `RAISE` (ABORT→IGNORE/FAIL/ROLLBACK, message, suppression, permutation) | 38 | 38 | 0 | 0 |
| Trigger / table cible | 12 | 8 | 4 | 0 |
| Trigger / forme `FOR EACH ROW` | 3 | 0 | 0 | 3 |
| Trigger / autres (opérateur `IS`→`=`, moment BEFORE→AFTER, `UPDATE OF`) | 16 | 14 | 0 | 2 |
| **Total** | **454** | **439** | **4** | **11** |

Historique des passes (même générateur) : (1) 430 tués / 20 survivants ; (2) 431 / 19 ; (3) après ajout des tests du §3 : **439 / 11**, confirmé sur le fichier final de 254 tests (dernière passe, deux exécutions : suite complète, puis suite sans le groupe A « chaîne »).

**Passe « sans groupe A »** (tests de DDL/structure exclus, pour isoler les kills purement structurels) : 412 tués, 38 survivants = les 11 survivants ci-dessous + **27 mutants tués uniquement par le groupe A** (§4 bis).

## 2. Générateur

Opérateurs repris de 006/007 : suppression de trigger / index, `UNIQUE`, CHECK (désactivé, conjoncts, arbre complet, séparateurs `AND`↔`OR`, littéraux de famille, comparaisons, `GLOB` vidé / chiffre retiré), listes `IN` (retrait / ajout d'un jeton), `NOT NULL`, `DEFAULT`, `STRICT`, `AUTOINCREMENT`, FK (cible, `CASCADE`/`SET NULL`/`NO ACTION`, suppression), index (colonne remplacée, unicité), triggers (région `WHERE` découpée au niveau 0, conjoncts → `1`, colonnes `NEW`/`OLD`, `NOT EXISTS`→`EXISTS`, `IS`→`=`, messages, `RAISE(ABORT)`→`IGNORE`/`FAIL`/`ROLLBACK`, instruction supprimée, BEFORE→AFTER, table cible, `UPDATE OF`).

Opérateurs propres à 008 (G5 et dates) : `CAST(... AS INTEGER)` retiré / `TEXT` / `REAL` / `NUMERIC` ; `substr(d,1,4)`, `substr(d,6,5)`, `substr(d,5)` décalés ; durées `1/2/10` modifiées et `WHEN` permutés ; `'02-29'`/`'-02-28'` ; `printf('%04d')` → autres formats ; `+`→`-` ; `date(x) IS x`→`date(x) = x` ; `CASE WHEN` inversé ; formule `DEFAULT` de `created_at` ; `FOR EACH ROW` dupliqué.

Fonctionnement : chaîne 001–007 (rang 10) sérialisée une fois par processus, seule 008 est rejouée ; 2 workers ; mutants invalides = migration qui échoue à la création ou à la première utilisation du témoin.

## 3. Lacunes réelles découvertes et corrigées (tests uniquement, SQL inchangé)

| # | Mutants concernés | Lacune de test | Correction |
|---|---|---|---|
| 1 | `in_plus` sur `garantie_type` (`IN (…, 'zzz')`) | aucun test n'insérait un jeton de type inconnu simple : la liste `IN` est la seule garde | tests « jeton de type inconnu refusé » (dont table témoin sans liste `IN` qui prouve que la formule G5 seule l'accepte) |
| 2 | conjoncts `GLOB` des CHECK de dates | croyance fausse « GLOB redondant avec `date(x) IS x` » : `date('now')` lève une `OperationalError` dans un CHECK s'il est atteint ; `date(x)` produit des chaînes d'année négative pour les jours juliens < 1721060 | tests `'now'`/`'NOW'`/`'Now'` (CHECK et garde G4) ; le conjoncte GLOB placé en premier court-circuite `date('now')` |
| 3 | `default_fmt`, `default_expr` (`created_at`) | le DEFAULT n'était tué que par un test de DDL | test comportemental : `created_at` par défaut = instant UTC courant au format `...Z` |
| 4 | `strict_off`, `not_null` | tués seulement par un test de DDL | tests STRICT sur messages (`cannot store TEXT value in INTEGER column`) |
| 5 | `autoinc#1` | idem | test : un `id` supprimé-échoué n'est jamais réutilisé (AUTOINCREMENT, INSERT ignoré qui avance la séquence) |
| 6 | `tr_51` / `RAISE` (mutants tués seulement par un test de DDL avant correction) | un seul statement par test d'échec | test `RAISE(ABORT)` multi-lignes : un `INSERT` de plusieurs lignes dont une seule est fautive n'écrit aucune ligne ; `INSERT OR IGNORE` n'ignore ni un trigger ni une FK |
| 7 | `tr_50_update` | UPSERT / `INSERT OR REPLACE` / `UPDATE` sans effet | test des trois contournements (aucune ligne modifiée, base identique avant/après) |
| 8 | `drop_index`, `index_col_swap` | aucune vérification d'usage des index | test `EXPLAIN QUERY PLAN` : chaque FK est couverte par un index de tête ; l'index de `date_fin_suivi` est utilisé pour la recherche des échéances |
| 9 | année 300 | quirk SQLite (`0300-02-29` accepté par `date()`) non documenté dans un test | test LIMITE explicite (comportement du moteur consigné, aucune borne SQL ajoutée, INV-177) |

## 4. Qualification individuelle des 11 survivants

Méthode : (a) justification structurelle ; (b) **preuve exhaustive** sur le domaine entier avec le moteur SQLite réel, accompagnée de **témoins non équivalents qui divergent** (la preuve n'est pas vide) ; (c) fuzz différentiel A (corpus de 649 533 triplets `(type, début, fin)`) et B (250 scénarios métier en lockstep, 32 822 opérations, mêmes graines pour l'original et le mutant). Aucun survivant n'est classé « équivalent » sans l'une de ces justifications.

| # | Mutant | Modification | Classe |
|---|---|---|---|
| S01 | `date_is_to_eq#2` | L69 `date(date_declenchement) IS date_declenchement` → `= date_declenchement` | E1 |
| S02 | `date_is_to_eq#3` | L71 `date(date_fin_suivi) IS date_fin_suivi` → `=` | E1 |
| S03 | `cast_drop#1 L82` | `CAST(substr(d,1,4) AS INTEGER)` → `(substr(d,1,4))` | E2 |
| S04 | `cast_as_TEXT#1 L82` | `AS INTEGER` → `AS TEXT` | E2 |
| S05 | `check_substr L82#1` | `substr(d,1,4)` → `substr(d,1,5)` | E3 |
| S06 | `check_substr L82#2` | `substr(d,6,5)` → `substr(d,6,6)` | E3 |
| S07 | `tr_51 is_to_eq#1` | G3 : `g.garantie_type IS NEW.garantie_type` → `=` | E4 |
| S08 | `tr_51 is_to_eq#2` | G4 : `f.date_emission IS NEW.date_declenchement` → `=` | E4 |
| S09 | `tr_50_garanties_update for_each_row_dup` | `FOR EACH ROW` ajouté | E5 |
| S10 | `tr_50_garanties_no_delete for_each_row_dup` | idem | E5 |
| S11 | `tr_51_garanties_insert for_each_row_dup` | idem | E5 |

**E1 — Équivalent démontré (`IS` → `=` dans un CHECK de date).** `x IS y` vaut 0 si `date(x)` est NULL, tandis que `x = y` vaut NULL et un CHECK n'échoue que sur 0 : le mutant accepterait donc une chaîne passant le `GLOB` mais pour laquelle `date()` est NULL (mois 13, jour 32…). Cette ouverture est fermée par l'autre CHECK de la même ligne : (#2) un début « invalide » donne une fin de même `MM-JJ` (formule G5), donc invalide aussi, et refusée par le CHECK **non muté** de `date_fin_suivi` ; (#3) la fin est égale à la formule d'un début, lui-même validé par le CHECK **non muté** de `date_declenchement` ; si la fin dépasse l'année 9999, elle ne passe pas le `GLOB` (conjoncte de gauche, évalué avant `date()`). Preuves : **E-C** — acceptation de la table réelle sur **tous** les 13 860 000 triplets (année 0000–9999 × mois 00–13 × jour 00–32 × 3 types, fin = formule, seule valeur acceptable par G5) : 10 952 531 acceptés pour l'original et les deux mutants, 0 divergence ; **E-D** — `date(x) = x` contre `IS` sur tous les mois/jours 00–99 (années échantillon, dont négatives) : 0 divergence sur les chaînes acceptées par la table complète ; différentiel A : 0 divergence sur 649 533 triplets. Témoin : `check_conjunct L69.2` (retrait du second conjoncte) diverge (10 975 242 acceptés, 198 divergences en différentiel A), donc le domaine discrimine bien. **Équivalence relative à la table complète** (les deux CHECK de dates conservés), pas à une colonne isolée.

**E2 — Équivalent démontré (`CAST` de l'année).** sur toute ligne acceptée, `substr(d,1,4)` est une chaîne de 4 chiffres (`GLOB` de `date_declenchement`, conjonction des CHECK) ; l'addition `+ CASE …` convertit la chaîne numérique en entier de la même façon que le `CAST` ; `CAST(… AS TEXT)` ne change rien à une valeur déjà TEXT. `printf('%04d', …)` reçoit le même entier. **E-A** : toutes les 10 957 278 évaluations (dates 0000-01-01 → 9999-12-31 × 3 types) : 0 divergence ; différentiel A : 0 divergence. Témoins `substr(d,1,3)`, `substr(d,6,4)`, `substr(d,2)` : respectivement 10 956 180, 7 278 et 10 950 000 divergences.

**E3 — Équivalent démontré (`substr` élargi).** (#1) `substr(d,1,5)` : le 5ᵉ caractère est `-` ; `CAST('2026-' AS INTEGER)` = 2026 (SQLite lit le préfixe numérique), donc même année. (#2) `substr(d,6,6)` : sur une date `AAAA-MM-JJ` de 10 caractères, `substr(d,6,5)` et `substr(d,6,6)` sont `MM-JJ`, la seule différence étant le caractère suivant, inexistant : le résultat reste `MM-JJ` (aucune chaîne valide n'a plus de 10 caractères). **E-A** : 10 957 278 évaluations chacun, 0 divergence ; différentiel A : 0 divergence. Les chaînes hors format sont refusées par le `GLOB` avant que G5 ne puisse accepter.

**E4 — Équivalent démontré (`IS` → `=` dans la garde).** `garantie_type` (de `bc_ligne_garanties`) et `date_emission` (de `factures`) sont `NOT NULL`. Si `NEW.garantie_type` / `NEW.date_declenchement` est NULL (un trigger `BEFORE` s'exécute avant le contrôle `NOT NULL`), `x = NULL` vaut NULL, `x IS NULL` vaut 0 : dans les deux cas le `WHERE` du `NOT EXISTS` ne renvoie aucune ligne, la garde lève le **même** message (INV-86 / INV-87). Si la valeur n'est pas NULL, `IS` et `=` coïncident. Vérifié dans le schéma réel (colonnes `NOT NULL`) ; différentiel B : 32 822 opérations par mutant, 0 divergence (messages comparés).

**E5 — Équivalent démontré (`FOR EACH ROW` dupliqué).** `FOR EACH ROW` est le comportement par défaut de SQLite (aucun trigger `FOR EACH STATEMENT`) ; le mot-clé ajouté ne change ni la sémantique ni le plan. Contrôle syntaxique (même arbre d'exécution) ; différentiel B : 0 divergence.

## 4 bis. Mutants tués uniquement par le groupe A (tests de structure)

27 mutants ne sont tués par aucun test comportemental ; ils sont tués par les tests de DDL/structure (groupe A) :

| Mutants | Nombre | Test tueur | Nature |
|---|---:|---|---|
| `drop_index` ×3 | 3 | `test_T50_A_atomicite_un_echec_n_importe_ou_annule_tout` (liste des index) | index absent : aucun effet fonctionnel, effet de performance (§9 du modèle) |
| `index_col_swap` (colonne d'index remplacée) | 21 | `test_T50_A_chaque_cle_etrangere_est_couverte_par_un_index_de_tete` (+ EQP) | index inutilisable pour la FK / l'échéance : performance |
| `cast_as_REAL#1`, `cast_as_NUMERIC#1` | 2 | `test_T50_A_le_fichier_ne_contient_que_des_creations_sans_transaction_ni_pragma_ni_donnee` (texte du fichier) | **comportementalement équivalents** : `printf('%04d', réel)` tronque, et les entiers 0–9 999 + 10 sont exacts en flottant ; différentiel A : 0 divergence sur 649 533 triplets |
| `tr_50_garanties_no_delete before_after` | 1 | `test_T50_A_les_triggers_de_008_sont_before_et_ne_font_que_garder` | `AFTER DELETE` + `RAISE(ABORT)` donne le même résultat observable (ligne conservée, même message) ; différentiel B : 0 divergence ; tué par la règle de DDL « tous les triggers sont BEFORE » |

Ce sont des kills **structurels** assumés (règle de conception : index par FK, triggers BEFORE), non des preuves de comportement. Pour les 3 `drop_index` + 21 `index_col_swap`, l'effet réel (performance) est vérifié par `EXPLAIN QUERY PLAN`, pas seulement par le texte.

## 4 ter. Mutants invalides (4)

`tr_51_garanties_insert table garanties→{factures, bons_commande, bc_lignes, bc_ligne_garanties}` : le trigger `BEFORE INSERT` posé sur une autre table référence `NEW.bc_ligne_id` (`no such column`) — le mutant fait échouer la première écriture du témoin ; non comptabilisé comme tué ni survivant.

## 4 quater. Remarque : redondance fonctionnelle des CHECK de dates

Dans la table complète, plusieurs mutants de CHECK (`check_conjunct L69.1`, `L71.1`, `check_tree …AND1->1`, `ident#1`, `check_op L76 > → >=`) sont **indiscernables à l'acceptation** sur les triplets où la fin est la formule exacte (E-C : 0 divergence), parce que G5 impose déjà `fin = f(début)` : ils sont néanmoins **tués** par les tests, qui isolent chaque CHECK (`temoin()` = table 008 sans G5 ni `tr_51`) et vérifient donc chaque garde indépendamment. La défense en profondeur est volontaire (cadrage : CHECK de format sur chaque date).

## 5. Limites de la méthode

- Un mutant tué n'est pas « prouvé faux » ; un survivant équivalent n'est pas un test manquant — la qualification sépare les deux.
- Les preuves E-A, E-C sont **exhaustives** sur leur domaine (dates 0000–9999, mois 00–13, jours 00–32) avec le SQLite du dépôt de test ; les différentiels A et B sont des preuves **par échantillon** (graines fixes) et ne sont utilisés qu'en complément d'une justification structurelle ou d'une preuve exhaustive.
- Les équivalences E1 et E4 sont **relatives** au reste du schéma (CHECK de dates conservés ; colonnes `NOT NULL` de 004/006) : une base dont ces contraintes auraient été retirées sort du périmètre d'une migration 008.
- Quirks du moteur documentés et testés, non corrigés en SQL (aucune borne d'année métier, INV-177) : `0300-02-29` accepté par `date()` (année 300) ; chaînes d'année négative pour les jours juliens < 1721060 ; `date('now')` non déterministe dans un CHECK (levé en `OperationalError` si atteint).
- Une partie des kills est textuelle (groupe A, §4 bis) ; `sql_temoin` (base sans G5 ni `tr_51`) dépend de la forme du fichier.
- Le groupe O (post-condition C1–C8 du service §4.1, émulée en test faute de service Rust dans le dépôt de migrations) compte 51 tests ; la mutation ne porte que sur le SQL, pas sur l'émulation du service.
