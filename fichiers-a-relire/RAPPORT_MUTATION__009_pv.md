# RAPPORT DE MUTATION 009 — PV

Périmètre : `src-tauri/migrations/metier/009_pv.sql` (175 lignes ; 1 table STRICT, 1 index explicite + 2 index de `UNIQUE`, 3 triggers) **après la correction du contrôle d'octets NUL (D1–D3, validée par Rémy le 2026-10-10)**.
Suite évaluée : `src-tauri/tests/metier/test_009_pv.py` (268 tests, 940 sous-tests) rejouée en entier, arrêt au premier échec (`-f`).
Aucun fichier 001–008, aucun cadrage, aucun document officiel n'est touché. Outils de campagne et de preuve : `fichiers-a-relire/outils_mutation_009/` (hors `src-tauri/`, non versionnés dans le dépôt de l'application ; empreintes en §6). **Cette campagne remplace intégralement celle de la version précédente du rapport (SQL sans contrôle d'octets, 255 tests, 692 mutants), qui n'est plus valable pour le SQL livré.**
Rien n'a été commité ni poussé.

## 1. Résultat final (SQL final, tests finaux)

| | Total | Tués | Invalides | Délais dépassés | Survivants |
|---|---:|---:|---:|---:|---:|
| **Tous mutants** | **797** | **770** | **3** | **0** | **24** |

966 mutants générés, 169 doublons de texte éliminés → 797 distincts. Les 24 survivants sont qualifiés **équivalents démontrés** (§4), chacun individuellement, par un script qui lit le SQL du dépôt ; ils sont rapprochés **mécaniquement** (texte identique, correspondance 1 pour 1) des survivants de la campagne (§4, §6). **Le SQL a changé après la campagne initiale** (correction NUL D1–D3) : la campagne a été relancée **en entier** sur le SQL et les tests finaux.

| Famille | Mutants | Tués | Invalides | Survivants |
|---|---:|---:|---:|---:|
| CHECK / contrôles d'octets (longueur, NUL) et CAST | 68 | 68 | 0 | 0 |
| Index (suppression, colonne remplacée, unicité) | 10 | 10 | 0 | 0 |
| Suppression d'un trigger | 3 | 3 | 0 | 0 |
| Table / CHECK (arbre AND/OR, opérateurs, GLOB, littéraux, substr, between, json_valid, date()) | 317 | 299 | 1 | 17 |
| Table / colonnes, types, listes IN, NOT NULL, DEFAULT, STRICT, AUTOINCREMENT, FK, UNIQUE | 70 | 70 | 0 | 0 |
| Trigger tr_40 (immuabilité) — toutes opérations | 60 | 58 | 0 | 2 |
| Trigger tr_41 / RAISE, messages, instructions (suppression, permutation) | 58 | 58 | 0 | 0 |
| Trigger tr_41 / WHEN et gardes G1–G4 (conjoncts, opérateurs, littéraux, colonnes, EXISTS, MAX+1, printf) | 204 | 199 | 0 | 5 |
| Trigger tr_41 / forme, événement, table cible | 7 | 5 | 2 | 0 |
| **Total** | **797** | **770** | **3** | **24** |

Historique des passes :
1. campagne initiale (SQL sans contrôle d'octets, 255 tests) : 839 générés / 692 distincts → 670 tués, 3 invalides, 19 survivants équivalents (version précédente du rapport) ;
2. après la correction NUL, **essai 1** (outil `mut009b.py` v1, 803 distincts) : 752 tués, **27 invalides**, 24 survivants. Les 24 mutants invalides supplémentaires venaient d'un **défaut de l'outil** : les opérateurs `cast_*` supposaient `CAST(… AS INTEGER)` (hérités de 006/007) et produisaient `CAST(x AS BLOB AS TEXT)` ou `(x AS BLOB)` ; ils n'étaient donc pas des mutants valides. Sortie brute conservée (`essai1_outil_v1_defaut_CAST__mut009_complete.log`) ;
3. **essai 2, définitif** (outil corrigé, ces opérateurs ne présupposent plus le type d'origine) : 797 distincts → **770 tués, 3 invalides, 24 survivants** ; les 3 invalides sont ceux de la campagne initiale (§4 ter) ; les 24 survivants sont les 19 de la campagne initiale + 5 nouveaux (S20–S24, §4).

**Passe « sans groupe A »** (classe `Chaine` exclue, tests de DDL/structure) : 758 tués, 3 invalides, 36 survivants = les 24 survivants + **12 mutants tués uniquement par le groupe A** (§4 bis, mêmes 12 que dans la campagne initiale).
**Passe « sans groupe A ni test témoin de texte »** (en plus, `test_T51_K_TEMOIN_sans_les_controles_de_longueur_et_d_octet_nul_les_valeurs_a_queue_passent` exclu) : 744 tués, 3 invalides, 50 survivants = les 36 + **14 mutants tués uniquement par ce test témoin de texte** (§4 quater).

## 2. Générateur

Opérateurs repris de 006/007/008 : suppression de trigger / index, `UNIQUE`, CHECK (désactivé, conjoncts, arbre complet, séparateurs `AND`↔`OR`, littéraux de famille, comparaisons, `GLOB` vidé / chiffre retiré), listes `IN` (retrait / ajout d'un jeton), `NOT NULL`, `DEFAULT`, `STRICT`, `AUTOINCREMENT`, FK (cible, `CASCADE`/`SET NULL`/`NO ACTION`, suppression), index (colonne remplacée, unicité), triggers (région `WHERE` découpée au niveau 0, conjoncts → `1`, colonnes `NEW`/`OLD`, `NOT EXISTS`→`EXISTS`, `IS`→`=`, messages, `RAISE(ABORT)`→`IGNORE`/`FAIL`/`ROLLBACK`, instruction supprimée, BEFORE→AFTER, table cible, `UPDATE OF`, `FOR EACH ROW` dupliqué).

Opérateurs propres à 009 : `GLOB` du numéro initial (`PVR-nnnnn-yy`) et du `created_at` : chaque `[0-9]` remplacé par `?`, par une lettre, dupliqué ; chaque `-` remplacé / supprimé ; queue `*` ajoutée ; `substr(numero, 11, 2)` et `substr(date_reception, 3, 2)` décalés ou élargis ; `COALESCE(MAX(suffixe), 0) + 1` → `+ 0`, `+ 2`, `- 1`, `MAX`→`COUNT`/`MIN`, `COALESCE` retiré ; `printf('%02d')` → autres formats ; jointure parasite `FROM pv o, pv x` (alias de table) ; `IS`→`=` ; bornes du suffixe ; `json_valid` retiré ; `date(x) IS x` → `=`.

Fonctionnement : chaîne 001–008 (rang 11) sérialisée une fois par processus, seule 009 est rejouée ; 2 workers ; mutants invalides = migration qui échoue à la création ou à la première utilisation du témoin.
L'attribution « tueur » du moteur est le **premier** test en échec, pas l'ensemble des tests qui tuent le mutant.

Opérateurs propres à la correction NUL (ajoutés à `mut009b.py` ; avec la correction des opérateurs `cast_*` et le SQL plus long, le total passe de 839 à 966 mutants générés) : `length(CAST(x AS BLOB)) = N` → constante ±1 et 0, `<>`, `<=`, `>=`, `<`, `>`, `length(x)` (sans `CAST`), `CAST(x AS TEXT)`, `IS NOT NULL`, conjoncte remplacé par `1`, `AND`→`OR` ; `instr(CAST(x AS BLOB), x'00') = 0` → `<> 0`, `>= 0`, `= 1`, `x'01'`, `x'0000'`, sans `CAST`, `CAST(x AS TEXT)`, `IS NOT NULL`, conjoncte remplacé par `1`, `AND`→`OR`. Les opérateurs `cast_*` génériques sont rendus indépendants du type d'origine (voir §1, essai 1).


## 3. Lacunes réelles découvertes et corrigées (tests ; puis correction SQL pour l'octet NUL)

| # | Mutants concernés | Lacune de test | Correction |
|---|---|---|---|
| 1 | 17 mutants `glob_digit_to_any` sur le `GLOB` de `created_at` (chiffres à `?`) | aucun test ne faisait varier chaque position du format de `created_at` | `test_T51_B_chaque_position_de_created_at_est_controlee` (une valeur invalide par position) |
| 2 | 3 mutants sur les chiffres centraux du numéro initial V6 (positions 5 à 7) | seuls le premier et le dernier chiffre du `nnnnn` étaient exercés | `test_T51_B_chaque_chiffre_du_numero_initial_v6_est_controle_individuellement` |
| 3 | `in_plus L80` (jeton sentinelle `'zzz'` ajouté à une liste `IN` de `type` / `origine`) | aucun test d'un jeton hors liste simple : la liste `IN` est la seule garde | `test_T51_B_valeur_sentinelle_hors_liste_pour_type_et_origine` |
| 4 | `fk_cascade#1`, `RAISE(FAIL)` ×5, `RAISE(ROLLBACK)` ×2, `unique_col_add +bc_id` (tués au départ par la seule structure) | la FK n'était pas isolée des triggers ; la sémantique `ABORT` n'était pas observée | tests de fin de campagne : FK `RESTRICT` sur base sans triggers (immédiat et `defer_foreign_keys=ON`), `ABORT` de chaque garde (transaction toujours ouverte, écritures précédentes conservées, aucune ligne d'une instruction multi-lignes écrite), unicité `(origine, suffixe)` indépendante du BC, de la date et du numéro |
| 5 | défaut de SQL (pas seulement de test) : `GLOB`, `substr`, `length()` de TEXT et `json_valid` s'arrêtent au premier octet NUL ; un `numero` initial V6 ou un `created_at` suivi d'un NUL, et un JSON contenant un NUL brut, étaient acceptés | — | **SQL** : D1 (`length(CAST(numero AS BLOB)) = 12`), D2 (`length(CAST(created_at AS BLOB)) = 24`), D3 (`instr(CAST(c AS BLOB), x'00') = 0` sur les quatre champs JSON ; l'échappement JSON `\u0000` reste valide). **Tests** : 14 définitions ajoutées dont 1 remplace le test-constat (net +13 : 255 → 268) ; groupes B et K |

Constat de moteur consigné par un test (SQLite 3.45) : avec `PRAGMA defer_foreign_keys=ON`, une suppression qui viole une FK `RESTRICT` n'est refusée qu'au `COMMIT` (et non à l'instruction) ; l'effet reste un refus sans suppression.

Efficacité des tests sur la correction : les 68 mutants de la famille « contrôles d'octets (longueur, NUL) et CAST » sont tous tués ; 54 par au moins un autre test que le témoin de texte, **14 seulement par ce test témoin** (§4 quater).

## 4. Qualification individuelle des 24 survivants

Méthode : (a) justification structurelle ; (b) **preuve exhaustive ou à domaine borné** évaluée par le moteur SQLite réel (3.45.1) par `preuves_equivalence_009.py`, qui **lit `009_pv.sql` dans le dépôt** : chaque survivant est une substitution textuelle sur ce fichier (si l'ancre n'y figure pas exactement une fois, le script s'arrête), les CHECK comparés sont extraits du DDL créé, les triggers sont exécutés tels que créés, et chaque famille a un **témoin non équivalent** qui diverge (11 témoins) ; (c) `rapprochement_survivants_registre.py` vérifie que le SQL muté de chaque entrée du registre est **identique octet pour octet** à celui d'un survivant de la campagne, et inversement (24 ↔ 24 ; 14 ↔ 14 pour §4 quater). Aucun survivant n'est classé « équivalent » sans l'une de ces justifications. Cette preuve **ne remplace pas la campagne** : elle ne démontre pas qu'il n'existe pas d'autres survivants (c'est la campagne qui les énumère).

| # | Mutant | Modification | Classe |
|---|---|---|---|
| S01 | `check_substr L114#1 substr(numero, 11, 3)` | `substr(numero, 11, 2)` → `substr(numero, 11, 3)` | E2 |
| S02 | `glob_digit_to_any#1.0 L82` | 1ᵉʳ chiffre de l'année du `GLOB` de `date_reception` → `?` | E1 |
| S03 | `glob_digit_to_any#1.1 L82` | 2ᵉ chiffre de l'année du `GLOB` de `date_reception` → `?` | E1 |
| S04 | `glob_digit_to_any#1.2 L82` | 3ᵉ chiffre de l'année du `GLOB` de `date_reception` → `?` | E1 |
| S05 | `glob_digit_to_any#1.3 L82` | 4ᵉ chiffre de l'année du `GLOB` de `date_reception` → `?` | E1 |
| S06 | `glob_digit_to_any#1.5 L82` | 1ᵉʳ chiffre du mois du `GLOB` de `date_reception` → `?` | E1 |
| S07 | `glob_digit_to_any#1.6 L82` | 2ᵉ chiffre du mois du `GLOB` de `date_reception` → `?` | E1 |
| S08 | `glob_digit_to_any#1.8 L82` | 1ᵉʳ chiffre du jour du `GLOB` de `date_reception` → `?` | E1 |
| S09 | `glob_digit_to_any#1.9 L82` | 2ᵉ chiffre du jour du `GLOB` de `date_reception` → `?` | E1 |
| S10 | `glob_tail#1 L82` | `*` ajouté en queue du `GLOB` de date | E1 |
| S11 | `glob_digit_to_any#1.10 L114` | 1ᵉʳ chiffre de `yy` du numéro → `?` | E3 |
| S12 | `glob_digit_to_any#1.11 L114` | 2ᵉ chiffre de `yy` du numéro → `?` | E3 |
| S13 | `tr_41_pv_insert printf_fmt#1 %02i` | `printf('%02d', …)` → `printf('%02i', …)` (G4) | E4 |
| S14 | `tr_41_pv_insert alias_table#1` | G1 : `FROM pv o` → `FROM pv o, pv x` | E5 |
| S15 | `tr_41_pv_insert alias_table#2` | G2 : idem | E5 |
| S16 | `tr_41_pv_insert alias_table#3` | G4 : idem | E5 |
| S17 | `tr_41_pv_insert is_to_eq#1` | G2 : `o.bc_id IS NEW.bc_id` → `=` | E6 |
| S18 | `tr_40_pv_no_update for_each_row_dup` | `FOR EACH ROW` ajouté | E7 |
| S19 | `tr_40_pv_no_delete for_each_row_dup` | idem | E7 |
| S20 | `check_disjunct L99.1` | `legacy_data IS NULL OR (…)` → `0 OR (…)` | **E8 (nouveau)** |
| S21 | `check_tree L99.G0.OR1->0` | même modification (écriture ` 0 `) | **E8 (nouveau)** |
| S22 | `glob_tail#1 L114` | `*` ajouté en queue du `GLOB` du numéro initial | **E9 (nouveau)** |
| S23 | `glob_tail#1 L118` | `*` ajouté en queue du `GLOB` de `created_at` | **E9 (nouveau)** |
| S24 | `glob_head#1 L118` | `*` ajouté en tête du `GLOB` de `created_at` | **E9 (nouveau)** |

**E1 — Équivalent démontré (`GLOB` de date affaibli).** Le CHECK de `date_reception` est la conjonction `GLOB … AND date(x) IS x`. Toute chaîne `x` telle que `date(x) IS x` est une image de `date()` : sur l'ensemble des **5 373 485 jours juliens (0 .. 5 373 484)**, `date()` produit soit 3 652 425 chaînes conformes au `GLOB` strict `AAAA-MM-JJ`, soit 1 721 060 chaînes d'année négative `-AAAA-MM-JJ` ; hors domaine `date()` renvoie `NULL` et `NULL IS x` est faux pour `x` non `NULL`. Aucune des variantes affaiblies ne reconnaît ces chaînes d'année négative : la conjonction affaiblie accepte exactement les mêmes chaînes (0 divergence sur les 5 373 485 points et sur 18 candidats mal formés, dont queues après NUL). Témoin W1 : sans `date(x) IS x`, 3 divergences. **Équivalence relative au CHECK conservé `date(x) IS x`** (le script s'arrête si cette prémisse disparaît du SQL).

**E2 — Équivalent démontré (`substr(numero, 11, 3)`).** Le CHECK du numéro initial impose le `GLOB` `PVR-nnnnn-yy` **et** `length(CAST(numero AS BLOB)) = 12` : les positions 11 et 12 sont les deux derniers caractères et il n'existe pas de 13ᵉ octet, queue après NUL comprise ; `substr(numero, 11, 3)` = `substr(numero, 11, 2)`. Prouvé sur **240 000 couples (numéro, date)** dont 400 acceptés, queues après NUL comprises : 0 divergence. Témoin W2 (`substr(numero, 10, 2)`) : 400 divergences.

**E3 — Équivalent démontré (chiffres de `yy` à `?`).** Le CHECK impose `substr(numero, 11, 2) = substr(date_reception, 3, 2)` ; les deux caractères de `substr(date_reception, 3, 2)` sont des chiffres (CHECK de date, E1). Remplacer `[0-9]` par `?` aux positions 11 ou 12 du `GLOB` du numéro ne change donc pas l'ensemble des lignes acceptées. Prouvé sur **6 760 000 couples (numéro, date valide)** par variante (10 000 acceptés) : 0 divergence. Témoin W3 (sans l'égalité avec l'année) : 2 390 000 divergences.

**E4 — Équivalent démontré (`%02i` ≡ `%02d`).** `i` et `d` sont synonymes dans `printf` de SQLite. Prouvé sur 101 001 entiers, plus 300 tentatives de levée successives (suffixes 1 à 100, numéros conformes et mal formés) exécutées par le trigger réel : 0 divergence. Témoin W4 (`%d`) : 309 divergences.

**E5 — Équivalent démontré (jointure `pv o, pv x` sous `NOT EXISTS`).** Si la table `pv` contient au moins une ligne satisfaisant le prédicat, le produit cartésien avec `pv x` conserve l'existence d'une ligne `o` ; si `pv` est vide, `EXISTS` est faux dans les deux formes. Prouvé sur **156 états de 0 à 3 PV × 8 316 tentatives de levée** exécutées par les triggers réels : 0 divergence. Témoin W5 (jointure avec une table **vide** d'une autre table) : 83 divergences — c'est pourquoi `table pv->bons_commande` est un mutant distinct (invalide, §4 ter).

**E6 — Équivalent démontré (`IS` → `=` dans G2).** `o.bc_id` est `NOT NULL`. Si `NEW.bc_id` est `NULL` (un trigger `BEFORE` s'exécute avant le contrôle `NOT NULL`), `o.bc_id = NULL` vaut `NULL` et `o.bc_id IS NULL` vaut 0 : dans les deux cas le `WHERE` du `NOT EXISTS` ne renvoie aucune ligne et G2 lève le même message. Prouvé sur les mêmes 156 états × 8 316 tentatives, `NEW.bc_id` `NULL` compris : 0 divergence. Témoin W6 (`IS NOT`) : 83 divergences.

**E7 — Équivalent démontré (`FOR EACH ROW` dupliqué).** `FOR EACH ROW` est le comportement par défaut de SQLite (aucun `FOR EACH STATEMENT`) ; le mot-clé ajouté ne change ni la sémantique ni le plan. Prouvé par différentiel sur 1 047 tentatives d'`UPDATE` / `DELETE` / `REPLACE` : 0 divergence ; témoin W7 (`UPDATE OF observations`) : 432 divergences. (Sur `tr_41`, le même mutant est **invalide** : `FOR EACH ROW` avant `WHEN` est une erreur de syntaxe.)

**E8 — Équivalent démontré, NOUVEAU (S20, S21 : `legacy_data IS NULL` → `0`).** Un CHECK n'échoue que si son expression vaut 0 ; `NULL` le satisfait. Pour `legacy_data` `NULL`, l'original vaut `1` ; le mutant vaut `0 OR (json_valid(NULL) AND instr(CAST(NULL AS BLOB), x'00') = 0)` = `0 OR (NULL AND NULL)` = `NULL` : accepté dans les deux cas. Pour une valeur non `NULL`, `legacy_data IS NULL` vaut 0, comme le littéral. Prouvé sur 20 valeurs (NULL, JSON valide, invalide, NUL brut, `\u0000` échappé) : 0 divergence ; les valeurs du CHECK sur `NULL` sont affichées (`1` et `NULL`). Témoin W8 (`IS NULL` → `1`, accepte tout JSON invalide) : 11 divergences. **Équivalence relative à la logique à trois valeurs de SQL.**
*Origine de ce survivant (divergence à signaler)* : dans la campagne initiale, ce mutant (`check_disjunct L98.1`) était tué par `test_T51_B_origine_import_legacy_optionnels_et_json_controle`, uniquement parce que l'assertion `ko_f(C_LEGACY_JSON, …)` compare le **texte du message de contrainte** à `legacy_data IS NULL OR json_valid(legacy_data)`. Le diff de tests validé réduit cette clé à `json_valid(legacy_data)` (le texte du CHECK a changé) : le message du mutant la contient encore, d'où deux survivants. *Option proposée (non appliquée)* : `C_LEGACY_JSON = "legacy_data IS NULL OR (json_valid(legacy_data)"` — vérifié sur copie jetable : 268 tests OK, S20 et S21 tués (par le texte du message, non par le comportement : ils restent équivalents).

**E9 — Équivalent démontré, NOUVEAU (S22 : `*` en queue du `GLOB` du numéro ; S23 : `*` en queue de celui de `created_at` ; S24 : `*` en tête de celui de `created_at`).** Le contrôle d'octets D1/D2 rend ces modifications redondantes. Le `GLOB` exige au moins 12 (resp. 24) caractères ASCII, donc au moins 12 (resp. 24) octets avant tout NUL, et le CHECK impose exactement 12 (resp. 24) octets : une queue (S22, S23) ou un préfixe (S24) autorisé par `*` serait vide, y compris quand un NUL ou un caractère multi-octets (`é`) occupe une position. Prouvé sur 43 824 évaluations du CHECK du numéro (substitutions d'un à deux caractères sur 6 symboles dont NUL, `é`, `*`, troncatures, queues, 2 dates, 3 combinaisons origine/type, branche `import` comprise) et 18 594 évaluations de celui de `created_at` : 0 divergence. Témoins W9 (`*` en queue **et** contrôle d'octets retiré) : 680 divergences ; W9b (`= 12` → `>= 12`) : 170. **Équivalence relative à D1/D2** : le script s'arrête si `length(CAST(numero AS BLOB)) = 12` ou `length(CAST(created_at AS BLOB)) = 24` disparaît du CHECK. Avant la correction NUL, ces trois mutants étaient tués comportementalement (queue acceptée) ; leur survie est la conséquence attendue de D1/D2.

## 4 bis. Mutants tués uniquement par le groupe A (tests de structure)

12 mutants ne sont tués par aucun test comportemental (passe « sans groupe A » : 36 survivants = 24 + ces 12 ; liste identique à la campagne initiale) ; ils sont tués par les tests de DDL/structure (groupe A, classe `Chaine`) :

| Mutants | Nombre | Test tueur | Nature |
|---|---:|---|---|
| `drop_index idx_pv_bc_id` | 1 | `test_T51_A_atomicite_un_echec_n_importe_ou_annule_tout` (liste des index) | index absent : aucun effet fonctionnel, effet de performance |
| `index_col_swap idx_pv_bc_id` (colonne remplacée : `id`, `type`, `origine_pv_id`, `created_at`, `numero`, `date_reception`, `suffixe`, `origine`) | 8 | `test_T51_A_chaque_cle_etrangere_est_couverte_par_un_index_de_tete` (+ EQP `test_T51_A_les_requetes_de_suivi_utilisent_les_index_prevus`) | l'index ne couvre plus la FK `bc_id` : performance |
| `fk_noaction#1`, `fk_noaction#2` (`RESTRICT` → `NO ACTION` sur `bc_id` / `origine_pv_id`) | 2 | `test_T51_A_deux_cles_etrangeres_en_restrict_sans_on_update` | **comportementalement indiscernables sur SQLite 3.45** pour une FK non différable : `NO ACTION` et `RESTRICT` refusent tous deux à l'instruction, et tous deux au `COMMIT` sous `defer_foreign_keys=ON` (constaté). Kill structurel assumé (le cadrage impose `RESTRICT`) ; équivalence **non démontrée pour une autre version du moteur** |
| `unique_col_add#1 +type` (`UNIQUE (origine_pv_id, suffixe)` → `(…, type)`) | 1 | `test_T51_A_index_exacts_unicite_et_aucun_index_redondant` | équivalent sous le CHECK « levée ⇔ origine renseignée » : toute ligne à `origine_pv_id` non `NULL` a `type = 'levee_reserves'`, et les lignes à origine `NULL` ne sont jamais en conflit (`NULL` distinct) ; kill par la liste exacte des index |

Ce sont des kills **structurels** assumés (règle de conception : un index par FK, FK `RESTRICT`, unicité exacte), non des preuves de comportement. L'effet de performance de `idx_pv_bc_id` est vérifié par `EXPLAIN QUERY PLAN`, pas seulement par le texte du DDL. (Historique : la passe sans groupe A de la campagne initiale comptait 21 mutants de ce type avant l'ajout des tests de fin de campagne ; 9 sont devenus aussi tués par des tests comportementaux : `fk_cascade#1`, `RAISE(FAIL)` ×5, `RAISE(ROLLBACK)` ×2, `unique_col_add +bc_id`, etc.)

## 4 ter. Mutants invalides (3)

| Mutant | Cause |
|---|---|
| `check_tree L106.G1.sep1 AND->OR` | `syntax error near ")"` : le remplacement produit un CHECK mal formé |
| `tr_41_pv_insert table pv->bons_commande` | `no such column: NEW.type` : le trigger `BEFORE INSERT` posé sur une autre table référence une colonne inexistante |
| `tr_41_pv_insert for_each_row_dup` | `syntax error near "FOR"` : `FOR EACH ROW` avant `WHEN` |

Non comptabilisés comme tués ni survivants.

## 4 quater. Mutants tués uniquement par le test témoin de texte (14)

Ces 14 mutants comptent parmi les 770 tués, mais **le seul test qui les tue est `test_T51_K_TEMOIN_sans_les_controles_de_longueur_et_d_octet_nul_les_valeurs_a_queue_passent`**, qui vérifie la présence **textuelle** des conjoncts D1–D3 dans le DDL (passe « sans groupe A ni témoin K » : 50 survivants = 36 + ces 14). Ce sont des kills **textuels** assumés, non des preuves de comportement ; ils sont qualifiés comme les survivants (mêmes outils, 14 ↔ 14 avec la campagne) :

| # | Mutant | Modification | Classe |
|---|---|---|---|
| K01 | `nul_len#1 numero `<= 12`` | `length(CAST(numero AS BLOB)) = 12` → `<= 12` | E9 |
| K02 | `nul_len#2 created_at `<= 24`` | `… = 24` → `<= 24` | E9 |
| K03 | `nul_instr client_snapshot` | `instr(CAST(client_snapshot AS BLOB), x'00')` → `instr(client_snapshot, x'00')` | E10 |
| K04 | `cast_as_TEXT#1 L85` | `CAST(client_snapshot AS BLOB)` → `CAST(client_snapshot AS TEXT)` | E10 |
| K05 | `cast_drop#1 L85` | `CAST(client_snapshot AS BLOB)` → `(client_snapshot)` | E10 |
| K06 | `nul_instr entreprise_snapshot` | `instr(CAST(entreprise_snapshot AS BLOB), x'00')` → `instr(entreprise_snapshot, x'00')` | E10 |
| K07 | `cast_as_TEXT#1 L87` | `CAST(entreprise_snapshot AS BLOB)` → `CAST(entreprise_snapshot AS TEXT)` | E10 |
| K08 | `cast_drop#1 L87` | `CAST(entreprise_snapshot AS BLOB)` → `(entreprise_snapshot)` | E10 |
| K09 | `nul_instr chantier_snapshot` | `instr(CAST(chantier_snapshot AS BLOB), x'00')` → `instr(chantier_snapshot, x'00')` | E10 |
| K10 | `cast_as_TEXT#1 L89` | `CAST(chantier_snapshot AS BLOB)` → `CAST(chantier_snapshot AS TEXT)` | E10 |
| K11 | `cast_drop#1 L89` | `CAST(chantier_snapshot AS BLOB)` → `(chantier_snapshot)` | E10 |
| K12 | `nul_instr legacy_data` | `instr(CAST(legacy_data AS BLOB), x'00')` → `instr(legacy_data, x'00')` | E10 |
| K13 | `cast_as_TEXT#1 L99` | `CAST(legacy_data AS BLOB)` → `CAST(legacy_data AS TEXT)` | E10 |
| K14 | `cast_drop#1 L99` | `CAST(legacy_data AS BLOB)` → `(legacy_data)` | E10 |

**E9 (K01, K02)** : `length(…) <= N` ≡ `= N`, car le `GLOB` du même CHECK impose déjà au moins N octets (voir E9). **E10 (K03–K14)** : sur SQLite 3.45.1, `instr(TEXT, x'00')` compare les octets comme `instr(CAST(TEXT AS BLOB), x'00')` ; `CAST(… AS TEXT)` et la forme sans `CAST` sont aussi équivalents. Prouvé sur 59 valeurs par colonne (NULL, JSON valide/invalide, NUL brut en toute position, `\u0000` échappé, `0x01`, caractère multi-octets) : 0 divergence ; témoin W10 (`x'01'` à la place de `x'00'`) : 11 divergences. **L'équivalence E10 est relative à la version du moteur** : le `CAST(… AS BLOB)` est conservé dans le SQL précisément pour ne pas dépendre de ce comportement ; la version de SQLite embarquée par Tauri n'a pas été vérifiée.

## 5. Limites de la méthode

- Un mutant tué n'est pas « prouvé faux » ; un survivant équivalent n'est pas un test manquant — la qualification sépare les deux.
- Les preuves E1–E4 sont **exhaustives** sur leur domaine (jours juliens 0 .. 5 373 484 ; entiers −1 000 .. 100 000 ; alphabet² × années) ; E5–E7 portent sur tous les états de 0 à 3 PV et sur des séries de tentatives choisies ; E8–E10 portent sur des **domaines bornés** de valeurs choisies (substitutions d'un à deux caractères, troncatures, queues avec NUL, multi-octets, NULL), complétés par un argument structurel. Elles sont évaluées par SQLite 3.45.1 ; **aucune n'est établie pour une autre version du moteur** (E10 en dépend explicitement).
- E1 et E3 sont **relatives** au reste du schéma (CHECK `date(x) IS x` conservé) ; E6 l'est à `NOT NULL` de `bc_id` ; E5 à la forme des gardes ; E8 à la logique à trois valeurs ; E9 aux contrôles d'octets D1/D2 ; E10 à la version du moteur. Une base dont ces contraintes auraient été retirées sort du périmètre d'une migration 009.
- **Octet NUL — corrigé dans 009, limite subsistante hors 009.** `GLOB`, `substr`, `length()` de TEXT et `json_valid` s'arrêtent au premier octet NUL. 009 contrôle donc la longueur en octets (`length(CAST(x AS BLOB))` = 12 pour le numéro d'un PV initial V6, = 24 pour `created_at`) et refuse l'octet NUL brut dans `client_snapshot`, `entreprise_snapshot`, `chantier_snapshot` et `legacy_data` ; l'échappement JSON `\u0000` reste valide. Le cadrage 009 ne contenait pas de décision sur ce point (il prévoyait seulement des tests de données malformées, §5 point 8 et groupe K) ; INV-20 et le type TS du modèle définissent le format. **Restent hors correction, par décision de périmètre** : `origine='import'` (numéro libre, INV-27 / INV-131 inchangés ; un NUL d'un tel numéro se propage à la levée par G4, constaté par `test_T51_K_CONSTAT_origine_import_numero_libre_avec_octet_nul_accepte_Z8`, Z-8), la levée (PR-3 : aucun CHECK de format) et les migrations 001–008 (plan de remédiation distinct).
- Constats de moteur documentés et testés, non corrigés en SQL (aucune borne d'année métier, INV-177 / D-38) : `date()` produit des chaînes d'année négative pour les jours juliens < 1721060 ; un PV initial daté de 2000 ou 2100 est accepté par le SQL (CT-7), refusé par le service.
- Limites des sondes du cadrage §3.6 : `INSERT … SELECT`, UPSERT (`DO UPDATE` / `DO NOTHING`), `INSERT OR REPLACE` / `OR IGNORE` sont testés (groupes D et E) ; **la protection contre `INSERT OR REPLACE` dépend de `recursive_triggers=ON`** (D-39) — un test témoin montre qu'avec `OFF` un remplacement par `id` passe ; TR-19 est examiné chaîne complète (`test_T51_F_suppression_d_un_bc_portant_un_pv_refusee_chaine_complete_TR_19`), puis la FK `RESTRICT` seule sur base sans triggers. Aucune de ces garanties n'est présentée comme valable hors de ces réglages de connexion.
- **Règles de service émulées en test, non mutées** : réservation du numéro (PT-1, `T.ATTRIBUER`), plafond 99 999, borne d'année 2001–2099 (INV-177), absence de séquence pour les levées. La mutation ne porte que sur le SQL, pas sur l'émulation. La 100ᵉ levée est refusée par le CHECK avec un message SQL brut (CT-6) ; un message explicite du service (PR-5) n'est pas implémenté ni présenté comme requis.
- Points sans règle documentaire, constatés par des tests nommés « constat » et **non présentés comme des règles** : QO-1 (statut du BC), QO-3 (cohérence de dates), QO-4 (non-vacuité de `reserves`), PR-3 (pas de format imposé au numéro d'une levée), Z-8 (levée V6 sur origine `origine='import'` à numéro libre).
- Import V2 : aucun PV V2 n'est importé (décision de Rémy) ; aucune exception de numérotation ni parcours d'import V2 n'existent (vérification statique dans le groupe H). Les mécanismes génériques `origine='import'` prévus par le cadrage sont conservés et testés comme tels.
- Une partie des kills est textuelle : groupe A (§4 bis, 12 mutants) et test témoin des conjoncts NUL (§4 quater, 14 mutants). La campagne les compte comme tués ; les passes de contrôle les isolent.
- **Reproductibilité** : l'outil de campagne (`mut009b.py`) et les scripts de preuve sont hors de `src-tauri/` ; leur présence dans le dépôt est à décider (voir le bilan). La campagne se rejoue avec `python3 -B mut009b.py RACINE DOSSIER_TRAVAIL` (≈ 8 min, 2 processus) ; le lien entre preuves et SQL se rejoue avec `preuves_equivalence_009.py RACINE` (≈ 3,5 min) puis `rapprochement_survivants_registre.py` (§6). Une évolution du SQL rend les ancres du registre caduques : le script s'arrête, et la campagne doit être relancée.

## 6. Empreintes et rejeu

| Pièce | sha256 |
|---|---|
| `009_pv.sql` (final, 175 lignes) | `764a2d302969f471bad2e6770f57454eff7659ebd886e5c6aa6be14509d84cb3` |
| `test_009_pv.py` (final, 268 tests, 940 sous-tests) | `4d56721107285773f12920224c2f83ded43f7aeb74b96a8909ef57beaeb59f04` |
| `mut009b.py` (campagne définitive) | `2cc9f2b6561fb5cc6b8d06e9818b72b4e300584be2bed75e4a42817259e5c6d6` |
| `genmut009b.py` | `047f54a265ec92f5fa1cb335d92c0f336ab60f6822263bc262c71a0a6d7fa894` |
| `classify009b.py` | `be4a436dda8f43135f3094da42d4e5abee30b6c9299e48d4e7c90f7bb8377d12` |
| `preuves_equivalence_009.py` | `72d2e99af9ad8e818585442488d420649a3be83629e69c8cbcac8f17b90ec6a7` |
| `rapprochement_survivants_registre.py` | `1d56db5637a53000c7dfbebcc411f9c70f518a54ede7f627f77cbfc847f162a7` |
| `mut009_v0_campagne_initiale.py` (outil de la campagne initiale, pour mémoire) | `d8dcd8636731be016ee7010218437fcebba2b725e66e011c1b44d91714bbd589` |

Rejeu (depuis la racine du dépôt contenant `src-tauri/`, outils dans `fichiers-a-relire/outils_mutation_009/`) :
```
python3 -B outils_mutation_009/mut009b.py . /tmp/mut009_travail            # campagne complète
MUT_EXCLUDE=Chaine python3 -B outils_mutation_009/mut009b.py . /tmp/m_sansA   # passe sans groupe A
python3 -B outils_mutation_009/preuves_equivalence_009.py .                # preuves liées au SQL (TOUT EST OK)
python3 -B outils_mutation_009/rapprochement_survivants_registre.py . outils_mutation_009/mut009b.py /tmp/mut009_travail/survivors009.txt /tmp/m_sansA/survivors009.txt /tmp/m_sansAK/survivors009.txt   # BIJECTION OK
```
Sorties brutes de cette campagne : `fichiers-a-relire/sorties_brutes_009_nul/`.
