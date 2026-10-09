# RAPPORT DE MUTATION 007 — Règlements

Périmètre : `src-tauri/migrations/metier/007_reglements.sql` (251 lignes ; 1 table STRICT, 3 index, 6 triggers).
Suite évaluée : `src-tauri/tests/metier/test_007_reglements.py` (279 tests, 608 sous-tests) rejouée en entier, arrêt au premier échec.
Aucun fichier 001–006 ni document officiel n'est touché. Les outils (`mut007.py`, `genmut007.py`, `diff007.py`, `equiv007.py`) sont des outils de travail hors dépôt ; ils sont dérivés de `mut006.py` / `diff006.py`.

## 1. Résultat final (SQL final, tests finaux)

| | Total | Tués | Invalides | Délais dépassés | Survivants |
|---|---:|---:|---:|---:|---:|
| **Tous mutants** | **1 244** | **1 217** | **0** | **0** | **27** |
| Triggers (`tr_30` → `tr_33`, suppression, `WHEN`, `WHERE`, `RAISE`, événement, table) | 1 067 | 1 046 | 0 | 0 | 21 |
| Hors triggers (CHECK, énumérations, NOT NULL, DEFAULT, STRICT, AUTOINCREMENT, FK, index) | 177 | 171 | 0 | 0 | 6 |

1 270 mutants générés, 26 doublons de texte éliminés → 1 244 distincts. Tous les survivants sont qualifiés **équivalents démontrés** (§4) ; **aucune lacune métier SQL** ; les **lacunes réelles de test** découvertes en cours de route (§3) sont corrigées et ne figurent plus parmi les survivants.

| Famille | Mutants | Survivants |
|---|---:|---:|
| Table / CHECK (arbre `AND`/`OR`, opérateurs, GLOB, littéraux, `substr`, `date()`) | 123 | 6 |
| Table / listes `IN` (énumérations) | 12 | 0 |
| Table / NOT NULL, DEFAULT, STRICT, AUTOINCREMENT, FK | 15 | 0 |
| Table / index (suppression, colonne, unicité) | 27 | 0 |
| Trigger / suppression d'un trigger | 6 | 0 |
| Trigger / clause et région `WHEN` | 81 | 1 |
| Trigger / région `WHERE` (conjoncts, opérateurs, littéraux, colonnes, `NEW`/`OLD`, `EXISTS`/`IS`) | 829 | 3 |
| Trigger / agrégats et conversions (COALESCE, SUM, CAST) | 56 | 10 |
| Trigger / arithmétique et jointures (min/max, ±, JOIN) | 22 | 7 |
| Trigger / instructions `RAISE` (ABORT→IGNORE/FAIL/ROLLBACK, message, suppression, toujours vrai) | 43 | 0 |
| Trigger / événement, moment (BEFORE→AFTER), table | 30 | 0 |

## 2. Générateur (par rapport à 006)

Opérateurs repris de `mut006.py` : suppression de trigger / index, `UNIQUE`→non unique, CHECK (désactivé, conjoncts, disjoncts, arbre complet, séparateurs `AND`↔`OR` — y compris `OR` en fin de ligne —, littéraux de famille, opérateurs de comparaison, `IS [NOT] NULL`, GLOB), `NOT NULL`, `DEFAULT`, `STRICT`, `AUTOINCREMENT`, listes `IN` (retrait d'un jeton, ajout de `'zzz'`), FK, `date(x) IS x`→`=`, régions de triggers (`WHEN`, chaque `WHERE`), `COALESCE`, `CAST(REPLACE …)`, `NEW`→`OLD`, colonnes alias.qualifiées, `EXISTS`/`NOT EXISTS`, `IS`/`IS NOT`, `LIMIT`, `substr`, instructions `RAISE` retirées ou rendues inconditionnelles, événement et table du trigger.

Ajouts et corrections pour 007 (écarts relevés pendant la campagne, tous corrigés avant les chiffres finaux) :
- **Sous-requêtes imbriquées** : le découpage cherchait le premier `WHERE` *textuel* d'une parenthèse au lieu du premier `WHERE` de niveau 0 ; il produisait 4 mutants invalides et manquait des mutations de conjoncts de sous-requêtes. Corrigé (`find_top`), mutation « condition entière → 1 / 0 » ajoutée.
- **Clause `WHEN` non mutée** : les triggers de 007 écrivent `WHEN` en début de ligne (le motif exigeait un espace avant) — la clause `WHEN` de `tr_31` (×2) et `tr_33` n'était pas mutée. Corrigé : +81 mutants, qui ont révélé 9 vraies lacunes de test (§3).
- Opérateurs propres à 007 : `min`↔`max`, `max(0,·)`→`max(1,·)`, `SUM`→`MAX`/`COUNT`, `+`↔`−`, `JOIN`→`LEFT JOIN`/`CROSS JOIN`, `RAISE(ABORT)`→`IGNORE`/`FAIL`/`ROLLBACK`, colonne d'index remplacée, index rendu unique, `NOT NULL` suivi d'un saut de ligne.
- Cache de migration : chaîne 001–006 (rang 9) sérialisée une fois par processus, seule 007 est rejouée ; 2 workers.

## 3. Lacunes réelles découvertes et corrigées (tests uniquement)

Aucune lacune « métier » dans le SQL : le SQL de 007 n'a pas changé entre la première et la dernière passe.

| # | Mutants concernés | Lacune de test | Correction (groupe T) |
|---|---|---|---|
| 1 | `in_plus` sur `type`, `mode`, `origine` (3) | aucun test n'insérait un jeton inconnu simple | `test_T49_T_un_jeton_inconnu_est_refuse_pour_type_mode_et_origine` |
| 2 | `tr_32` : `legacy_id`/`legacy_data` comparés à `cancelled_at` (2) | aucune annulation d'un règlement **importé** (legacy non nul) n'était acceptée dans les tests | annulation d'un encaissement / remboursement importé ; colonnes legacy figées |
| 3 | filtres de type redondants avec `tr_30` dans `tr_31` (×3) et `tr_33` (×2) (5) | aucun test de défense en profondeur si `tr_30` est contourné | 5 tests : remboursement / encaissement parasites ne faussent ni plafonds ni garde |
| 4 | `tr_33` : clause `WHEN` (conjoncts, séparateurs, `NEW.cancelled_at`, `when_off`) (9) | aucun test d'un `UPDATE` sans changement sur un encaissement actif « protégé », ni d'un `UPDATE` d'un encaissement déjà annulé dans cet état | 4 tests (no-op accepté, `INV-70` et non `INV-75` sur annulé, remboursement non évalué par `tr_33`, modification d'un remboursement = `INV-70`) |

Historique des passes : (1) 1 109 mutants, 1 070 tués, 4 invalides, 35 survivants ; (2) générateur corrigé : 1 139 mutants, 1 103 tués, 36 survivants ; (3) 10 tests ajoutés : 10 tués → 26 survivants ; (4) clause `WHEN` mutée : +81 mutants, 71 tués, 10 survivants → 4 tests ajoutés : 9 tués, 1 équivalent ; (5) **passe finale complète** (index mutés en plus) : 1 244 mutants, 1 217 tués, 0 invalide, 27 survivants.

## 4. Qualification individuelle des 27 survivants

Méthode : (a) justification structurelle ; (b) **fuzz différentiel** `diff007.py` — SQL d'origine contre mutant, mêmes 250 séquences pseudo-aléatoires en lockstep (≈ 83 opérations chacune : encaissements, avoirs, remboursements, annulations, règlements nés annulés, `UPDATE`/`DELETE`/`INSERT OR REPLACE`, mauvaises cibles), comparaison des codes `INV-xx` et des états dérivés (`reste_du`, `crédit`) : **20 768 opérations par mutant, 0 divergence pour chacun des 27** ; (c) **preuves exhaustives** sur domaine borné avec l'arithmétique réelle de SQLite (`equiv007.py`). Le harnais n'est pas aveugle : 5 mutants témoins non équivalents divergent (de 14 à 210 scénarios sur 250).

| S01 | `check_disjunct L91.1` | `-    cancelled_at     TEXT    CHECK (cancelled_at IS NULL OR cancelled_at GLOB`<br>`+    cancelled_at     TEXT    CHECK (0 OR cancelled_at GLOB` | Équivalent démontré (E1) |
| S02 | `check_disjunct L93.1` | `-    motif_annulation TEXT    CHECK (motif_annulation IS NULL OR motif_annulation <> ''),`<br>`+    motif_annulation TEXT    CHECK (0 OR motif_annulation <> ''),` | Équivalent démontré (E1) |
| S03 | `check_disjunct L98.1` | `-    legacy_data      TEXT    CHECK (legacy_data IS NULL OR json_valid(legacy_data)),`<br>`+    legacy_data      TEXT    CHECK (0 OR json_valid(legacy_data)),` | Équivalent démontré (E1) |
| S04 | `check_tree L91.G0.OR1->0` | `-    cancelled_at     TEXT    CHECK (cancelled_at IS NULL OR cancelled_at GLOB`<br>`+    cancelled_at     TEXT    CHECK ( 0  OR cancelled_at GLOB` | Équivalent démontré (E1) |
| S05 | `check_tree L93.G0.OR1->0` | `-    motif_annulation TEXT    CHECK (motif_annulation IS NULL OR motif_annulation <> ''),`<br>`+    motif_annulation TEXT    CHECK ( 0  OR motif_annulation <> ''),` | Équivalent démontré (E1) |
| S06 | `check_tree L98.G0.OR1->0` | `-    legacy_data      TEXT    CHECK (legacy_data IS NULL OR json_valid(legacy_data)),`<br>`+    legacy_data      TEXT    CHECK ( 0  OR json_valid(legacy_data)),` | Équivalent démontré (E1) |
| S07 | `tr_31_reglements_remboursement R1 coalesce0#1` | `-                        > (SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 0)`<br>`+                        > (SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 1)` | Équivalent démontré (E2) |
| S08 | `tr_31_reglements_remboursement R1 coalesce0#2` | `-                          - min((SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 0)`<br>`+                          - min((SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 1)` | Équivalent démontré (E2) |
| S09 | `tr_31_reglements_remboursement R1 coalesce_drop#1` | `-                        > (SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 0)`<br>`+                        > (SELECT SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER))` | Équivalent démontré (E2) |
| S10 | `tr_31_reglements_remboursement R1 coalesce_drop#2` | `-                          - min((SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 0)`<br>`+                          - min((SELECT SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER))` | Équivalent démontré (E2) |
| S11 | `tr_33_reglements_annulation R1 coalesce0#1` | `-                      AND (SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 0)`<br>`+                      AND (SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 1)` | Équivalent démontré (E3) |
| S12 | `tr_33_reglements_annulation R1 coalesce0#3` | `-                                       - ((SELECT COALESCE(SUM(CAST(REPLACE(r.montant, '.', '') AS INTEGER)), 0)`<br>`+                                       - ((SELECT COALESCE(SUM(CAST(REPLACE(r.montant, '.', '') AS INTEGER)), 1)` | Équivalent démontré (E3) |
| S13 | `tr_33_reglements_annulation R1 coalesce_drop#1` | `-                      AND (SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 0)`<br>`+                      AND (SELECT SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER))` | Équivalent démontré (E3) |
| S14 | `tr_33_reglements_annulation R1 coalesce_drop#2` | `-                          - min((SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 0)`<br>`+                          - min((SELECT SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER))` | Équivalent démontré (E3) |
| S15 | `tr_33_reglements_annulation R1 coalesce_drop#3` | `-                                       - ((SELECT COALESCE(SUM(CAST(REPLACE(r.montant, '.', '') AS INTEGER)), 0)`<br>`+                                       - ((SELECT SUM(CAST(REPLACE(r.montant, '.', '') AS INTEGER))` | Équivalent démontré (E3) |
| S16 | `tr_33_reglements_annulation R1 coalesce_drop#4` | `-                        < (SELECT COALESCE(SUM(CAST(REPLACE(r.montant, '.', '') AS INTEGER)), 0)`<br>`+                        < (SELECT SUM(CAST(REPLACE(r.montant, '.', '') AS INTEGER))` | Équivalent démontré (E3) |
| S17 | `tr_31_reglements_remboursement R1 join_cross#1` | `-     WHERE EXISTS (SELECT 1 FROM factures a JOIN factures o ON o.id = a.origine_facture_id`<br>`+     WHERE EXISTS (SELECT 1 FROM factures a CROSS JOIN factures o ON o.id = a.origine_facture_id` | Équivalent démontré (E4) |
| S18 | `tr_31_reglements_remboursement R1 join_cross#2` | `-                               FROM reglements r JOIN factures a2 ON a2.id = r.facture_id`<br>`+                               FROM reglements r CROSS JOIN factures a2 ON a2.id = r.facture_id` | Équivalent démontré (E4) |
| S19 | `tr_31_reglements_remboursement R1 join_left#1` | `-     WHERE EXISTS (SELECT 1 FROM factures a JOIN factures o ON o.id = a.origine_facture_id`<br>`+     WHERE EXISTS (SELECT 1 FROM factures a LEFT JOIN factures o ON o.id = a.origine_facture_id` | Équivalent démontré (E4) |
| S20 | `tr_31_reglements_remboursement R1 join_left#2` | `-                               FROM reglements r JOIN factures a2 ON a2.id = r.facture_id`<br>`+                               FROM reglements r LEFT JOIN factures a2 ON a2.id = r.facture_id` | Équivalent démontré (E4) |
| S21 | `tr_33_reglements_annulation R1 join_cross#1` | `-                             FROM reglements r JOIN factures a2 ON a2.id = r.facture_id`<br>`+                             FROM reglements r CROSS JOIN factures a2 ON a2.id = r.facture_id` | Équivalent démontré (E4) |
| S22 | `tr_33_reglements_annulation R1 join_left#1` | `-                             FROM reglements r JOIN factures a2 ON a2.id = r.facture_id`<br>`+                             FROM reglements r LEFT JOIN factures a2 ON a2.id = r.facture_id` | Équivalent démontré (E4) |
| S23 | `tr_31_reglements_remboursement R1 col#11 origine_facture_id->id` | `-                                   FROM factures av WHERE av.origine_facture_id = o.id),`<br>`+                                   FROM factures av WHERE av.id = o.id),` | Équivalent démontré (E5) |
| S24 | `tr_31_reglements_remboursement R1.G2.WHERE->1` | `-                                   FROM factures av WHERE av.origine_facture_id = o.id),`<br>`+                                   FROM factures av WHERE  1),` | Équivalent démontré (E5) |
| S25 | `tr_31_reglements_remboursement R1.G0.AND2->1` | `-                    WHERE a.id = NEW.facture_id AND a.type = 'avoir'`<br>`-                      AND CAST(REPLACE(NEW.montant, '.', '') AS INTEGER)`<br>`+                    WHERE a.id = NEW.facture_id AND  1  AND CAST(REPLACE(NEW.montant, '.', '') AS INTEGER)` | Équivalent démontré (E6) |
| S26 | `tr_33_reglements_annulation R1 max0_1#1` | `-                                max(0, CAST(REPLACE(o.total_ht, '.', '') AS INTEGER)`<br>`+                                max(1, CAST(REPLACE(o.total_ht, '.', '') AS INTEGER)` | Équivalent démontré (sous invariant) (E7) |
| S27 | `tr_33_reglements_annulation R0.G0.AND1->1` | `-WHEN OLD.type = 'encaissement' AND OLD.cancelled_at IS NULL AND NEW.cancelled_at IS NOT NULL`<br>`+WHEN  1  AND OLD.cancelled_at IS NULL AND NEW.cancelled_at IS NOT NULL` | Équivalent démontré (E8) |

Justifications par classe :

**E1 — Équivalent démontré.** `CHECK (x IS NULL OR f(x))` → `CHECK (0 OR f(x))` : un CHECK n'échoue que si l'expression vaut 0. Pour `x` NULL, `f(x)` (GLOB, `<>`, `json_valid`) vaut NULL, donc `0 OR NULL = NULL` : accepté, comme `1`. Pour `x` non NULL les deux expressions sont identiques. Vérifié sur 16 valeurs par colonne (`equiv007.py` : 0 divergence) et en différentiel (20 768 opérations, 0 divergence).

**E2 — Équivalent démontré.** `COALESCE(SUM(av.total_ht), 0)` sur `factures av WHERE av.origine_facture_id = o.id`, dans une requête où `o` est l'origine de l'avoir `a` visé (jointure `o.id = a.origine_facture_id`) : l'ensemble contient au moins `a` ; `SUM` n'est donc jamais NULL et la valeur par défaut est inatteignable. 0 divergence en différentiel.

**E3 — Équivalent démontré.** Sous-requête agrégée dont la valeur par défaut n'influence jamais le prédicat `Σav − min(Σav, …) < Σremb` : (#1, #2 : Σav) si la facture n'a aucun avoir, Σremb = 0 et le premier membre vaut 0 (original), `1 − min(1, …) ∈ {0, 1}` ou NULL (mutants) : jamais `< 0` ; (#3 : Σ encaissements actifs) l'ensemble contient toujours `OLD` (encaissement actif en cours d'annulation) : jamais vide ; (#4 : Σ remboursements) sans remboursement actif, `LHS < 0` (faux car LHS ≥ 0) ou `LHS < NULL` (NULL) : même absence de refus. 0 divergence en différentiel.

**E4 — Équivalent démontré.** `LEFT JOIN` : le `WHERE` filtre ensuite sur une colonne de la table de droite (`a2.origine_facture_id = o.id`) ou la ligne de droite existe toujours (`o` : `type='avoir' ⇔ origine_facture_id NOT NULL` par CHECK 006 + FK) : la jointure externe dégénère en jointure interne. `CROSS JOIN … ON` : en SQLite `CROSS JOIN` est une jointure interne dont seul l'ordre de boucles est imposé au planificateur (documentation SQLite) : même résultat. 0 divergence en différentiel.

**E5 — Équivalent démontré.** Le terme remplacé n'intervient que dans `min(S′, max(0, M − enc))` avec `S′ ≥ Σav` (S′ = M ou Σ de toutes les factures) : si Σav ≥ M − enc le `min` vaut `max(0, M − enc)` dans les deux cas ; sinon le crédit est ≤ 0 dans les deux cas et aucun remboursement ≥ 0.01 n'est accepté. Vérifié sur 341 796 états (`equiv007.py`, 0 divergence ; témoin S′ = 0 : 54 418 divergences) et en différentiel (0 divergence).

**E6 — Équivalent démontré.** `a.type = 'avoir'` est redondant avec la jointure `o.id = a.origine_facture_id` : par le CHECK de 006 `(type = 'avoir') = (origine_facture_id IS NOT NULL)`, seule une ligne d'avoir a une origine ; une facture hors avoir ne joint rien. Un remboursement sur une facture hors avoir reste refusé par `tr_30`. 0 divergence en différentiel.

**E7 — Équivalent démontré (sous invariant).** `max(0, M − (enc − OLD.montant))` → `max(1, …)` : les deux termes diffèrent seulement si `M − (enc − OLD.montant) ≤ 0`, c'est-à-dire `enc ≥ M + OLD.montant > M`, état que `tr_31` interdit (Σ encaissements actifs ≤ M − Σ avoirs ≤ M). Vérifié sur 22 113 états conformes à l'invariant (0 divergence) ; hors invariant les deux divergent (témoin : 1 001 divergences), ce qui prouve que la preuve n'est pas vide. Le seul moyen de les distinguer est de supprimer `tr_31` (SQL contourné), état hors périmètre d'un garde de 007. 0 divergence en différentiel.

**E8 — Équivalent démontré.** `OLD.type = 'encaissement'` retiré de la clause `WHEN` : pour un remboursement, `OLD.facture_id` est un avoir `o` ; aucun avoir n'a pour origine un avoir (INV-76, trigger de 006) donc Σav(o) = 0 et Σremb(o) = 0 : le prédicat se réduit à `0 < 0`, faux. La garde ne peut pas se déclencher sur un remboursement. 0 divergence en différentiel (opération `annul_r` incluse).

Aucun survivant n'est classé « équivalent » sans l'une de ces justifications. Deux classes (E7, E6) reposent sur un invariant garanti par un autre garde ou par 006 ; elles sont donc équivalentes **dans les états atteignables** et non sur toute base arbitraire (une base dont `tr_31` ou le CHECK de 006 auraient été retirés sort du périmètre).

## 5. Limites de la méthode

- Un mutant tué par un test n'est pas un mutant « prouvé faux » ; un survivant équivalent n'est pas un test manquant — la qualification ci-dessus sépare les deux.
- Le fuzz différentiel est un outil de preuve par échantillon (graine fixe) ; il n'est utilisé qu'en complément d'une justification structurelle, et d'une preuve exhaustive pour les trois cas arithmétiques.
- Les limites connues hors mutation (saturation int64, octet NUL dans un montant, conversion STRICT) sont documentées dans le cadrage §6 et testées par témoin.
