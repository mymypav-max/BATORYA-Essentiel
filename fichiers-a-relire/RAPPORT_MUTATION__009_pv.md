# RAPPORT DE MUTATION 009 — PV

Périmètre : `src-tauri/migrations/metier/009_pv.sql` (170 lignes ; 1 table STRICT, 1 index explicite + 2 index de `UNIQUE`, 3 triggers).
Suite évaluée : `src-tauri/tests/metier/test_009_pv.py` (255 tests, 669 sous-tests) rejouée en entier, arrêt au premier échec (`-f`).
Aucun fichier 001–008, aucun cadrage, aucun document officiel n'est touché. Les outils (`mut009.py`, `genmut009.py`, `equiv009.py`, `classify009.py`) sont des outils de travail hors dépôt, dérivés de ceux de 008.
Rien n'a été commité ni poussé.

## 1. Résultat final (SQL final, tests finaux)

| | Total | Tués | Invalides | Délais dépassés | Survivants |
|---|---:|---:|---:|---:|---:|
| **Tous mutants** | **692** | **670** | **3** | **0** | **19** |

839 mutants générés, 147 doublons de texte éliminés → 692 distincts. Les 19 survivants sont qualifiés **équivalents démontrés** (§4), chacun individuellement. **Aucune lacune métier dans le SQL** (le SQL n'a pas changé entre la première et la dernière passe) ; les lacunes réelles de test découvertes en route (§3) sont corrigées par des tests uniquement.

| Famille | Mutants | Tués | Invalides | Survivants |
|---|---:|---:|---:|---:|
| Table / CHECK (arbre `AND`/`OR`, opérateurs, `GLOB`, littéraux, `substr`, `BETWEEN`, `json_valid`, `date()`) | 280 | 267 | 1 | 12 |
| Table / colonnes, types, listes `IN`, `NOT NULL`, `DEFAULT`, `STRICT`, `AUTOINCREMENT`, FK, `UNIQUE` | 70 | 70 | 0 | 0 |
| Index (suppression, colonne remplacée, unicité) | 10 | 10 | 0 | 0 |
| Suppression d'un trigger | 3 | 3 | 0 | 0 |
| Trigger `tr_40` (immuabilité) — toutes opérations | 60 | 58 | 0 | 2 |
| Trigger `tr_41` / `RAISE`, messages, instructions (suppression, permutation) | 58 | 58 | 0 | 0 |
| Trigger `tr_41` / `WHEN` et gardes G1–G4 (conjoncts, opérateurs, littéraux, colonnes, `EXISTS`, `MAX`+1, `printf`) | 204 | 199 | 0 | 5 |
| Trigger `tr_41` / forme, événement, table cible | 7 | 5 | 2 | 0 |
| **Total** | **692** | **670** | **3** | **19** |

Historique des passes (même générateur) :
1. première passe : 842 générés / 695 distincts → 649 tués, 3 invalides, **43 survivants** (19 équivalents + 21 lacunes de test + 3 mutants `plus1` ne portant que sur du texte de commentaire) ;
2. correction de l'opérateur `plus1` (mutations tombant dans un commentaire écartées : 695 → 692 distincts) et ajout des tests du §3 (lignes 1 à 3) : 670 tués, 3 invalides, **19 survivants** ;
3. après ajout de 6 tests de fin de campagne (§3, ligne 4 : FK `RESTRICT` sans triggers, sémantique `ABORT` des gardes) : **résultat identique (670 / 3 / 19, mêmes 19 survivants)**, confirmé sur le fichier final de 255 tests.

**Passe « sans groupe A »** (classe `Chaine`, tests de DDL/structure, exclue — pour isoler les kills purement structurels) : 658 tués, 3 invalides, 31 survivants = les 19 survivants ci-dessous + **12 mutants tués uniquement par le groupe A** (§4 bis).

## 2. Générateur

Opérateurs repris de 006/007/008 : suppression de trigger / index, `UNIQUE`, CHECK (désactivé, conjoncts, arbre complet, séparateurs `AND`↔`OR`, littéraux de famille, comparaisons, `GLOB` vidé / chiffre retiré), listes `IN` (retrait / ajout d'un jeton), `NOT NULL`, `DEFAULT`, `STRICT`, `AUTOINCREMENT`, FK (cible, `CASCADE`/`SET NULL`/`NO ACTION`, suppression), index (colonne remplacée, unicité), triggers (région `WHERE` découpée au niveau 0, conjoncts → `1`, colonnes `NEW`/`OLD`, `NOT EXISTS`→`EXISTS`, `IS`→`=`, messages, `RAISE(ABORT)`→`IGNORE`/`FAIL`/`ROLLBACK`, instruction supprimée, BEFORE→AFTER, table cible, `UPDATE OF`, `FOR EACH ROW` dupliqué).

Opérateurs propres à 009 : `GLOB` du numéro initial (`PVR-nnnnn-yy`) et du `created_at` : chaque `[0-9]` remplacé par `?`, par une lettre, dupliqué ; chaque `-` remplacé / supprimé ; queue `*` ajoutée ; `substr(numero, 11, 2)` et `substr(date_reception, 3, 2)` décalés ou élargis ; `COALESCE(MAX(suffixe), 0) + 1` → `+ 0`, `+ 2`, `- 1`, `MAX`→`COUNT`/`MIN`, `COALESCE` retiré ; `printf('%02d')` → autres formats ; jointure parasite `FROM pv o, pv x` (alias de table) ; `IS`→`=` ; bornes du suffixe ; `json_valid` retiré ; `date(x) IS x` → `=`.

Fonctionnement : chaîne 001–008 (rang 11) sérialisée une fois par processus, seule 009 est rejouée ; 2 workers ; mutants invalides = migration qui échoue à la création ou à la première utilisation du témoin.
L'attribution « tueur » du moteur est le **premier** test en échec, pas l'ensemble des tests qui tuent le mutant.

## 3. Lacunes réelles découvertes et corrigées (tests uniquement, SQL inchangé)

| # | Mutants concernés | Lacune de test | Correction |
|---|---|---|---|
| 1 | 17 mutants `glob_digit_to_any` sur le `GLOB` de `created_at` (chiffres à `?`) | aucun test ne faisait varier chaque position du format de `created_at` | `test_T51_B_chaque_position_de_created_at_est_controlee` (une valeur invalide par position) |
| 2 | 3 mutants sur les chiffres centraux du numéro initial V6 (positions 5 à 7) | seuls le premier et le dernier chiffre du `nnnnn` étaient exercés | `test_T51_B_chaque_chiffre_du_numero_initial_v6_est_controle_individuellement` |
| 3 | `in_plus L80` (jeton sentinelle `'zzz'` ajouté à une liste `IN` de `type` / `origine`) | aucun test d'un jeton hors liste simple : la liste `IN` est la seule garde | `test_T51_B_valeur_sentinelle_hors_liste_pour_type_et_origine` |
| 4 | `fk_cascade#1`, `RAISE(FAIL)` ×5, `RAISE(ROLLBACK)` ×2, `unique_col_add +bc_id` (tués au départ par la seule structure) | la FK n'était pas isolée des triggers ; la sémantique `ABORT` n'était pas observée | tests de fin de campagne : FK `RESTRICT` sur base sans triggers (immédiat et `defer_foreign_keys=ON`), `ABORT` de chaque garde (transaction toujours ouverte, écritures précédentes conservées, aucune ligne d'une instruction multi-lignes écrite), unicité `(origine, suffixe)` indépendante du BC, de la date et du numéro |

Constat de moteur consigné par un test (SQLite 3.45) : avec `PRAGMA defer_foreign_keys=ON`, une suppression qui viole une FK `RESTRICT` n'est refusée qu'au `COMMIT` (et non à l'instruction) ; l'effet reste un refus sans suppression.

## 4. Qualification individuelle des 19 survivants

Méthode : (a) justification structurelle ; (b) **preuve exhaustive** sur le domaine entier avec le moteur SQLite réel (script `equiv009.py`, sortie : « TOUT EST OK »), accompagnée de **témoins non équivalents qui divergent** (la preuve n'est pas vide). Aucun survivant n'est classé « équivalent » sans l'une de ces justifications.

| # | Mutant | Modification | Classe |
|---|---|---|---|
| S01 | `check_substr L111#1` | `substr(numero, 11, 2)` → `substr(numero, 11, 3)` | E2 |
| S02 | `glob_digit_to_any#1.0` L82 | 1ᵉʳ chiffre de l'année du `GLOB` de `date_reception` → `?` | E1 |
| S03 | `glob_digit_to_any#1.1` L82 | 2ᵉ chiffre → `?` | E1 |
| S04 | `glob_digit_to_any#1.2` L82 | 3ᵉ chiffre → `?` | E1 |
| S05 | `glob_digit_to_any#1.3` L82 | 4ᵉ chiffre → `?` | E1 |
| S06 | `glob_digit_to_any#1.5` L82 | 1ᵉʳ chiffre du mois → `?` | E1 |
| S07 | `glob_digit_to_any#1.6` L82 | 2ᵉ chiffre du mois → `?` | E1 |
| S08 | `glob_digit_to_any#1.8` L82 | 1ᵉʳ chiffre du jour → `?` | E1 |
| S09 | `glob_digit_to_any#1.9` L82 | 2ᵉ chiffre du jour → `?` | E1 |
| S10 | `glob_tail#1` L82 | `*` ajouté en queue du `GLOB` de date | E1 |
| S11 | `glob_digit_to_any#1.10` L111 | 1ᵉʳ chiffre de `yy` du numéro → `?` | E3 |
| S12 | `glob_digit_to_any#1.11` L111 | 2ᵉ chiffre de `yy` du numéro → `?` | E3 |
| S13 | `tr_41 printf_fmt#1` | `printf('%02d', ...)` → `printf('%02i', ...)` (G4) | E4 |
| S14 | `tr_41 alias_table#1` | G1 : `FROM pv o` → `FROM pv o, pv x` | E5 |
| S15 | `tr_41 alias_table#2` | G2 : idem | E5 |
| S16 | `tr_41 alias_table#3` | G4 : idem | E5 |
| S17 | `tr_41 is_to_eq#1` | G2 : `o.bc_id IS NEW.bc_id` → `=` | E6 |
| S18 | `tr_40_pv_no_update for_each_row_dup` | `FOR EACH ROW` ajouté | E7 |
| S19 | `tr_40_pv_no_delete for_each_row_dup` | idem | E7 |

**E1 — Équivalent démontré (`GLOB` de date affaibli).** Le CHECK de `date_reception` est la conjonction `GLOB … AND date(x) IS x`. Toute chaîne `x` telle que `date(x) IS x` est une image de `date()` : sur l'ensemble des **5 373 485 jours juliens (0 .. 5 373 484)**, `date()` produit soit 3 652 425 chaînes conformes au `GLOB` strict `AAAA-MM-JJ`, soit 1 721 060 chaînes d'année négative de la forme `-AAAA-MM-JJ` (11 caractères, `-` en tête) ; hors domaine, `date()` renvoie `NULL`, et `NULL IS x` est faux pour `x` non `NULL`. Aucune des **10 variantes affaiblies** (dont les 9 survivants) ne reconnaît ces 1 721 060 chaînes d'année négative (0 / 0 / 0 selon variante, tête et queue comprises) : la conjonction affaiblie accepte donc exactement les mêmes chaînes que la conjonction stricte (vérifié sur 15 candidats × 5 variantes mal formés : 0 divergence). Témoin : le `GLOB` affaibli **seul** diverge du `GLOB` strict ; c'est la conjonction avec `date(x) IS x` qui rend l'affaiblissement équivalent. **Équivalence relative au CHECK conservé `date(x) IS x`**, pas à un `GLOB` isolé.

**E2 — Équivalent démontré (`substr(numero, 11, 3)`).** Sur toute chaîne acceptée par le `GLOB` du numéro initial `PVR-nnnnn-yy`, les positions 11 et 12 sont les deux derniers caractères et la chaîne n'a pas de 13ᵉ caractère ; `substr(numero, 11, 3) = substr(numero, 11, 2)` (le 3ᵉ caractère n'existe pas). Prouvé sur 2 400 chaînes acceptées par le `GLOB`, **queues après un octet NUL comprises** (`GLOB` et `substr` s'arrêtent au NUL). Témoin : un décalage de position (10) diverge.

**E3 — Équivalent démontré (chiffres de `yy` à `?`).** Le CHECK impose `substr(numero, 11, 2) = substr(date_reception, 3, 2)` ; les deux caractères de `substr(date_reception, 3, 2)` sont des chiffres (CHECK de date, E1). Remplacer `[0-9]` par `?` aux positions 11 ou 12 du `GLOB` du numéro ne change donc pas l'ensemble des lignes acceptées. Prouvé sur **6 760 000 couples (numéro, date valide)** par variante : 0 divergence. Témoin : sans l'égalité `substr(...)`, le `?` diverge.

**E4 — Équivalent démontré (`%02i` ≡ `%02d`).** `i` et `d` sont synonymes dans `printf` de SQLite. Prouvé sur 101 001 entiers (0 divergence) ; témoin : `printf('%d', 1)` diverge de `printf('%02d', 1)`.

**E5 — Équivalent démontré (jointure `pv o, pv x` sous `NOT EXISTS`).** Si la table `pv` contient au moins une ligne (c'est le cas dès qu'une ligne `o` satisfait le prédicat), le produit cartésien avec `pv x` conserve l'existence d'une ligne `o` ; si `pv` est vide, `EXISTS` est faux dans les deux formes. Prouvé sur toutes les tables de 0 à 3 lignes (61 240 évaluations) : 0 divergence ; témoin : avec une table **vide** dans la jointure (autre table que `pv`) le résultat diverge — c'est pourquoi `table pv->bons_commande` est un mutant distinct (invalide, §4 ter), non un équivalent.

**E6 — Équivalent démontré (`IS` → `=` dans G2).** `o.bc_id` est `NOT NULL`. Si `NEW.bc_id` est `NULL` (un trigger `BEFORE` s'exécute avant le contrôle `NOT NULL`), `o.bc_id = NULL` vaut `NULL` et `o.bc_id IS NULL` vaut 0 : dans les deux cas le `WHERE` du `NOT EXISTS` ne renvoie aucune ligne et G2 lève le **même** message. Prouvé sur 30 620 évaluations, `NEW.bc_id` `NULL` compris : 0 divergence.

**E7 — Équivalent démontré (`FOR EACH ROW` dupliqué).** `FOR EACH ROW` est le comportement par défaut de SQLite (aucun `FOR EACH STATEMENT`) ; le mot-clé ajouté ne change ni la sémantique ni le plan. (Sur `tr_41`, le même mutant est **invalide** : `FOR EACH ROW` placé avant `WHEN` est une erreur de syntaxe.)

## 4 bis. Mutants tués uniquement par le groupe A (tests de structure)

12 mutants ne sont tués par aucun test comportemental ; ils sont tués par les tests de DDL/structure (groupe A, classe `Chaine`) :

| Mutants | Nombre | Test tueur | Nature |
|---|---:|---|---|
| `drop_index idx_pv_bc_id` | 1 | `test_T51_A_atomicite_un_echec_n_importe_ou_annule_tout` (liste des index) | index absent : aucun effet fonctionnel, effet de performance |
| `index_col_swap idx_pv_bc_id` (colonne remplacée : `id`, `type`, `origine_pv_id`, `created_at`, `numero`, `date_reception`, `suffixe`, `origine`) | 8 | `test_T51_A_chaque_cle_etrangere_est_couverte_par_un_index_de_tete` (+ EQP `test_T51_A_les_requetes_de_suivi_utilisent_les_index_prevus`) | l'index ne couvre plus la FK `bc_id` : performance |
| `fk_noaction#1`, `fk_noaction#2` (`RESTRICT` → `NO ACTION` sur `bc_id` / `origine_pv_id`) | 2 | `test_T51_A_deux_cles_etrangeres_en_restrict_sans_on_update` | **comportementalement indiscernables sur SQLite 3.45** pour une FK non différable : `NO ACTION` et `RESTRICT` refusent tous deux à l'instruction, et tous deux au `COMMIT` sous `defer_foreign_keys=ON` (constaté). Kill structurel assumé (le cadrage impose `RESTRICT`) ; équivalence **non démontrée pour une autre version du moteur** |
| `unique_col_add#1 +type` (`UNIQUE (origine_pv_id, suffixe)` → `(…, type)`) | 1 | `test_T51_A_index_exacts_unicite_et_aucun_index_redondant` | équivalent sous le CHECK « levée ⇔ origine renseignée » : toute ligne à `origine_pv_id` non `NULL` a `type = 'levee_reserves'`, et les lignes à origine `NULL` ne sont jamais en conflit (`NULL` distinct) ; kill par la liste exacte des index |

Ce sont des kills **structurels** assumés (règle de conception : un index par FK, FK `RESTRICT`, unicité exacte), non des preuves de comportement. L'effet de performance de `idx_pv_bc_id` est vérifié par `EXPLAIN QUERY PLAN`, pas seulement par le texte du DDL. (La passe sans groupe A comptait 21 mutants de ce type avant l'ajout des tests de fin de campagne ; 9 sont désormais tués aussi par des tests comportementaux : `fk_cascade#1`, `RAISE(FAIL)` ×5, `RAISE(ROLLBACK)` ×2, `unique_col_add +bc_id`, etc.)

## 4 ter. Mutants invalides (3)

| Mutant | Cause |
|---|---|
| `check_tree L105.G1.sep1 AND->OR` | `syntax error near ")"` : le remplacement produit un CHECK mal formé |
| `tr_41_pv_insert table pv->bons_commande` | `no such column: NEW.type` : le trigger `BEFORE INSERT` posé sur une autre table référence une colonne inexistante |
| `tr_41_pv_insert for_each_row_dup` | `syntax error near "FOR"` : `FOR EACH ROW` avant `WHEN` |

Non comptabilisés comme tués ni survivants.

## 5. Limites de la méthode

- Un mutant tué n'est pas « prouvé faux » ; un survivant équivalent n'est pas un test manquant — la qualification sépare les deux.
- Les preuves E1–E6 sont **exhaustives** sur leur domaine (jours juliens 0 .. 5 373 484 ; tables de 0 à 3 lignes ; entiers 0 .. 101 000 ; couples numéro × date) avec la bibliothèque SQLite de l'environnement de test (3.45.1). Aucun différentiel par échantillon n'a été utilisé en remplacement d'une preuve.
- E1 et E3 sont **relatives** au reste du schéma (CHECK `date(x) IS x` conservé) ; E6 l'est à `NOT NULL` de `bc_id` ; E5 à la forme des gardes. Une base dont ces contraintes auraient été retirées sort du périmètre d'une migration 009.
- **Limite non corrigée, commune à tous les CHECK `GLOB` de la chaîne** : `GLOB` et `substr` s'arrêtent au premier octet NUL ; un `numero` ou un `created_at` avec queue après un NUL passe le CHECK de format. Constaté et consigné par un test (groupe K), non corrigé en SQL (aucune règle documentaire ne l'exige).
- Constats de moteur documentés et testés, non corrigés en SQL (aucune borne d'année métier, INV-177 / D-38) : `date()` produit des chaînes d'année négative pour les jours juliens < 1721060 ; un PV initial daté de 2000 ou 2100 est accepté par le SQL (CT-7), refusé par le service.
- Limites des sondes du cadrage §3.6 : `INSERT … SELECT`, UPSERT (`DO UPDATE` / `DO NOTHING`), `INSERT OR REPLACE` / `OR IGNORE` sont testés (groupes D et E) ; **la protection contre `INSERT OR REPLACE` dépend de `recursive_triggers=ON`** (D-39) — un test témoin montre qu'avec `OFF` un remplacement par `id` passe ; TR-19 est examiné chaîne complète (`test_T51_F_suppression_d_un_bc_portant_un_pv_refusee_chaine_complete_TR_19`), puis la FK `RESTRICT` seule sur base sans triggers. Aucune de ces garanties n'est présentée comme valable hors de ces réglages de connexion.
- **Règles de service émulées en test, non mutées** : réservation du numéro (PT-1, `T.ATTRIBUER`), plafond 99 999, borne d'année 2001–2099 (INV-177), absence de séquence pour les levées. La mutation ne porte que sur le SQL, pas sur l'émulation. La 100ᵉ levée est refusée par le CHECK avec un message SQL brut (CT-6) ; un message explicite du service (PR-5) n'est pas implémenté ni présenté comme requis.
- Points sans règle documentaire, constatés par des tests nommés « constat » et **non présentés comme des règles** : QO-1 (statut du BC), QO-3 (cohérence de dates), QO-4 (non-vacuité de `reserves`), PR-3 (pas de format imposé au numéro d'une levée), Z-8 (levée V6 sur origine `origine='import'` à numéro libre).
- Import V2 : aucun PV V2 n'est importé (décision de Rémy) ; aucune exception de numérotation ni parcours d'import V2 n'existent (vérification statique dans le groupe H). Les mécanismes génériques `origine='import'` prévus par le cadrage sont conservés et testés comme tels.
- Une partie des kills est textuelle (groupe A, §4 bis).
