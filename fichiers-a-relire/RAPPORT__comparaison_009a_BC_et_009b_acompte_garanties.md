# RAPPORT — Comparaison des deux propositions « 009a » et consolidation (révision G)

**Date** : 2026-10-17 · **Nature** : document de travail (relecture), non officiel ; aucun fichier sous `docs/` n'est modifié ; aucune migration livrée (001 à 009) n'est modifiée ; la tranche 010 n'est pas démarrée. **Cette consolidation n'est pas validée** : elle est proposée pour relecture.

## 1. Ce qui a été examiné (contenu réel, pas seulement les noms)

| Proposition | Fichiers lus en entier | Identité |
|---|---|---|
| **(a)** révision F — corrective « acompte, garanties manuelles » | `009a_acompte_garanties_manuelles.sql` (devenue `009b_…`) et son test | créée à la révision F, jamais intégrée à `main` |
| **(b)** proposition du 2026-10-13 — annulation du BC, TR-103 | `RAPPORT_FINAL__009a_proposition_finale_v2.md` (116 lignes), `PLAN_MAJ_DOC__009a_regle_annulation_bc.md` (V2) et `_V3.md` (238 lignes), `PROPOSITION_DIFF__009a_V2_bc_annulation_interdite_si_facture.diff` (762 lignes : migration + 50 tests) | diff V2 appliqué sur le dépôt de travail ; blobs obtenus `e89b51e` (migration) et `511ce9f` (test), **identiques** à ceux du diff ; depuis, **l'en-tête et le trigger ont été modifiés** (révision G, règle du 2026-10-17 à 14:34 : net nul après avoirs ; voir §4 et §5) |

Les fichiers V1 cités par le rapport final (`RAPPORT__009a_…`, `RAPPORT_COMPLEMENT__009a_…`, `PROPOSITION_DIFF__009a_bc_annulation_interdite_si_facture.diff`) **ne sont pas dans le dépôt de travail** : seul le V2 a pu être lu. Le rapport final indique que le trigger est identique entre V1 et V2.

## 2. Règles métier et objets SQL couverts

| | (a) 009b — facturation et garanties | (b) 009a — annulation du BC |
|---|---|---|
| **Règles métier** | plafond de l'acompte sur l'acompte prévu du devis ; aucun acompte après un solde **ni après une situation sur le même devis** (ajout du 2026-10-17, ordre apprécié par devis à 14:34) ; situation < 100 % ; solde > 0 et = contractuel final − nette ; motif d'avoir en liste fermée ; avoir « prestations non réalisées » interdit sur acompte ; garanties à déclenchement manuel ; retrait ciblé d'une prestation ; suivi actif | un BC ne passe à `annule` que si **chacune** de ses factures (acompte, situation, solde) a un net nul après avoirs (règle du 2026-10-17 à 14:34 ; réglée ou non : le règlement n'est pas le critère ; l'avoir est le moyen de ramener une facture à zéro) ; un acompte **prévu** sans facture ne bloque pas ; une émission refusée ou défaite par rollback ne bloque pas ; les BC déjà annulés ne sont pas touchés |
| **Objets SQL créés** | table `bc_ligne_retraits_garantie` (+ 2 index) ; triggers `tr_50_bc_ligne_retraits_garantie_update/no_delete`, `tr_51_bc_ligne_retraits_garantie_insert` ; vue `v_garanties_suivi_actif` | trigger `tr_103_bons_commande_annulation_facturee` (seul objet) |
| **Objets SQL remplacés** | triggers `tr_22_factures_acompte/situation/solde`, `tr_23_factures_avoir`, `tr_51_garanties_insert` ; table `garanties` reconstruite (`facture_declenchement_id` nullable) | aucun |
| **Tables lues** | `factures`, `devis`, `bc_devis` (dont `created_at` du lien, pour l'ordre par devis), `bc_lignes`, `garanties`… | `factures` (colonnes `bc_id`, `type`, `total_ht`, `origine_facture_id`) |
| **Tables écrites / reconstruites** | `garanties` (reconstruction, ids et `sqlite_sequence` préservés) | aucune ; aucune donnée |
| **Rang proposé** | 13 (F) puis **14** | 13 |
| **Tests** | 106 (`test_009b_acompte_garanties_manuelles.py`) | 57 (`test_009a_bc_annulation_interdite_si_facture.py`) |

## 3. Différences, chevauchements, incompatibilités

| # | Constat | Gravité | Traitement |
|---|---|---|---|
| 1 | **Conflit de nom et de rang** : les deux se nomment `009a` et visent le rang 13 | bloquant | résolu par suffixes successifs (§5) |
| 2 | **Aucun objet SQL commun** : (a) ne touche ni `bons_commande` ni `tr_103` ; (b) ne touche ni `factures` ni `garanties` | — | indépendantes ; chacune peut être retirée sans modifier l'autre |
| 3 | **Dépendance de (b) vis-à-vis de (a)** : `tr_103` lit `factures.bc_id` ; (a) remplace seulement des triggers de `factures`, jamais la table | nulle | le test de garde de chaîne de (b) rejoue (a) comme « migration suivante » sur une base peuplée : le trigger reste identique et effectif |
| 4 | **Reconstruction de table** : (a) reconstruit `garanties` (FK vers `bons_commande`) mais ne reconstruit pas `bons_commande`, donc ne supprime pas `tr_103` | à surveiller | vérifié (test de garde de (b) et test « seuls les triggers annoncés changent » de (a)) |
| 5 | **Documents de travail** : la règle de (b) (stricte le 2026-10-13, ramenée au net nul après avoirs le 2026-10-17) est **contraire** à E-15 / INV-44 / D-46 / modèle métier § Annulation tels qu'ils étaient consignés (« annulation sans condition de facturation », 2026-10-03). Elle est aussi contraire à `docs/` (exception « acompte non réglé » de D-05, INV-44, E-07, CDC §17) | **élevée** | alignement minimal des documents de travail dans cette révision (INV-44, E-15, E-07, D-05, D-35, D-46, C-19, CDC amendement E-15, modèle métier § Annulation) ; `docs/` non touché |
| 6 | **Anciens tests de 006, 007 et 008** : plusieurs fabriquent un BC *annulé et facturé* (matrice « état du BC par type de facture », `test_CK06_ignore_les_BC_annules`, `test_BC_annule_aucune_creation_de_facture_malgre_un_reglement`, `test_T50_H_un_BC_annule_apres_le_solde_conserve_ses_garanties`…). Ils restent exacts **à leur rang d'origine** (9 à 12) ; rejoués au rang 14, ils échouent sur `INV-44` tant que les factures de l'état fabriqué ne sont pas ramenées à zéro | attendu | non modifiés (migrations et tests livrés immuables) ; états inatteignables après 009a pour de nouvelles données, possibles seulement pour des données historiques |
| 7 | **Règle d'ordre « aucun acompte après situation »** ajoutée à (a), **par devis** : les mêmes anciens tests de 006 qui émettent un acompte après une situation sur le même devis échouent au rang 14 (`INV-58`) | attendu | décision du 2026-10-17 ; second devis rattaché après la situation : permis (§6) |
| 8 | **Numéros** : (b) introduit `TR-103` (premier numéro libre) ; aucun conflit avec (a), qui reprend TR-22, TR-23, TR-50, TR-51 existants | — | `TR-103` repris tel quel, présenté comme « proposé par la 009a du 2026-10-13, non officiel » |
| 9 | **Rang de 010 et 011** : le rapport de (b) décale 010 au rang 14 et 011 au rang 15 ; (a) décalait 010 au rang 14 à la révision F | élevée | consolidation : 010 → **15**, 011 → **16**, `010a_*` → **16**, `011a_*` → **17** |
| 10 | **Garde `user_version`** : (a) exigeait 12, ce qui aurait écarté (b) | bloquant sans correction | (a) devenue 009b exige 13 et pose 14 |

Aucune incompatibilité *technique* n'existe entre les deux migrations. Les incompatibilités sont documentaires (ligne 5) et d'ordonnancement des rangs (lignes 1, 9, 10).

## 4. Statut de la règle d'annulation (règle du 2026-10-17 à 14:34, qui remplace la règle stricte du 2026-10-13)

**Mise à jour du 2026-10-17 (14:34) :** le propriétaire du produit a **précisé et validé** la règle : un BC facturé n'est annulable que si chaque facture a été ramenée à zéro par des avoirs (le règlement n'étant pas le critère). Elle **remplace** la règle stricte (« interdite dès qu'une facture existe ; un avoir total ne rétablit jamais le droit »), qui n'est donc plus appliquée ; le trigger `tr_103` n'est plus identique à celui de la proposition du 2026-10-13. Le paragraphe ci-dessous retrace l'historique de la proposition.

Le rapport final de (b) la présente comme décidée le 2026-10-13 (messages de 06:57, 07:29 et 08:08) ; le plan V3 précise lui-même que **cette formulation n'est consignée dans aucun fichier du dépôt** et qu'elle contredit `docs/` (D-05, INV-44, E-07, CDC §17). Les documents de travail de la V3.13 disaient l'inverse (E-15). Cette révision a donc **aligné les documents de travail sur la règle d'annulation**, parce que (i) elle est postérieure à E-15, (ii) elle a été confirmée, et (iii) laisser le SQL de (b) en contradiction avec INV-44 aurait rendu la chaîne non conforme. Cette lecture est **réversible sans toucher à (a)** : retirer `009a_bc_annulation_interdite_si_facture.sql`, son test, et rétablir les textes d'INV-44 / E-15 / D-05 / D-46 suffit (le rang de 009b redeviendrait 13).

**Non intégrés, à arbitrer** (liste du plan V3, aucun nouvel identifiant officiel n'est créé) : cascade BC → devis (C1 : le SQL livré ne cascade pas, les textes officiels l'imposent) ; passages d'import « BC historique annulé » (INV-169, modèle V3.12 l.366 et l.717) ; CDC §17 l.512 et l.543 dans `docs/` ; erratum de support (E-21 proposé) et numéros T / C ; flux d'annulation automatique d'un acompte (INV-35) ; texte `docs/` en général.

## 5. Solution recommandée : conserver les deux, en deux migrations successives

| Rang | Fichier | Contenu | Remarque |
|---|---|---|---|
| 13 | `009a_bc_annulation_interdite_si_facture.sql` | `tr_103` seul | trigger **corrigé le 2026-10-17 (14:34)** : net nul après avoirs, par facture (la proposition V2 refusait dès qu'une facture existait) ; même nom, même événement, même transition |
| 14 | `009b_acompte_garanties_manuelles.sql` | facturation + garanties | ex-« 009a » de la révision F ; garde `user_version = 13`, pose 14 ; garde de cumul retirée ; règle d'ordre ajoutée, **par devis** |
| 15 | `010_planification.sql` | prévue, non créée | décalée de 14 à 15 |

**Pourquoi cette solution** : (1) les deux corrections sont nécessaires et indépendantes ; aucune ne doit disparaître pour résoudre un nom ; (2) le précédent `005a`, `005b`, `005c` montre que plusieurs correctives après une même tranche reçoivent des suffixes successifs ; (3) un fichier par sujet garde le retour arrière simple (la règle stricte est la plus exposée à contestation documentaire) ; (4) (b) étant plus ancienne (2026-10-13) et la plus petite (un trigger), elle précède ; (5) l'ordre des deux est sans effet de comportement (aucun objet commun).

**Alternatives écartées** : un fichier unique (mélange deux sujets, retour arrière difficile) ; 009b avant 009a (aucun avantage, contredit l'ancienneté) ; abandonner (b) ou (a) (perte d'une règle nécessaire).

## 6. Conséquences

- **Numéros de migration et tranche 010** : 010 passe au rang 15 (et non 14), 011 au rang 16, `010a_*` au rang 16, `011a_*` au rang 17. **010 n'est pas démarrée.** Le diff documentaire validé `DIFF_DOC__010_historique_planification.diff` écrit encore « 010 (rang 13), 011 (rang 14) » : il devra être réémis avec ces rangs, comme le prévoit le plan V3 §6.4 et §7 (non fait ici : lot documentaire distinct, hors `docs/`).
- **Bases de développement** : toute base à `user_version ≥ 13` ne rejouerait pas 009a ni 009b au bon rang ; toute base à `user_version = 13` issue d'un 009a local différent est un conflit. **Non vérifiable ici** (aucune base versionnée) : contrôle à faire de ton côté (`PRAGMA user_version;` ≤ 12 attendu).
- **Règle d'ordre sur un BC à deux devis (validée le 2026-10-17 à 14:34)** : l'ordre s'apprécie **par devis**. Les situations étant globales au BC (aucun `devis_id`, INV-190), le SQL détermine qu'une situation couvre un devis par la chronologie déjà utilisée par le modèle (CK-14, CK-16) : `factures.created_at` de la situation ≥ `bc_devis.created_at` du devis. Un second devis rattaché après la situation peut donc recevoir son acompte (rattaché exclusivement à lui, plafond = son acompte prévu, historique du premier devis non bloquant) ; une situation émise ensuite le couvre et interdit un nouvel acompte. **Interprétation signalée** : à égalité d'horodatage, la situation est réputée couvrir le devis (refus). Aucun mécanisme nouveau n'est créé.
- **Avoir total sur une situation** : une situation créditée reste une situation émise pour l'ordre (les factures sont immuables) ; interprétation signalée dans le test.

## 7. Vérifications effectuées

| Contrôle | Résultat |
|---|---|
| Tests (b) `test_009a_bc_annulation_interdite_si_facture.py` sur la chaîne contenant (a) comme migration suivante | 57 OK |
| Tests (a) `test_009b_acompte_garanties_manuelles.py` au rang 14 | 106 OK |
| Rejeu différentiel des 1 110 tests de 006 à 009 sur le rang 14 | aucune régression inexpliquée ; les écarts relèvent des règles de 009b (motif d'avoir, situation < 100 %, plafond d'acompte, solde > 0), de `INV-58` (acompte après situation sur le même devis), de `INV-44` (BC annulé et facturé à net non nul fabriqué par les anciens tests) ou de la réapplication d'une migration sur une base déjà migrée (« table … already exists », artefact du rejeu) |
| Mutations | 35 sabotages (23 sur 009b dont 7 sur l'ordre par devis, le plafond par devis et l'unicité ; 12 sur `tr_103` : règle stricte, exceptions par type, avoir contrôlé comme une facture, net global du BC au lieu du net par facture, absence d'avoirs, une seule facture contrôlée…) : **35 détectés** |
| Suite complète | voir le compte rendu |

## 8. Ce qui n'a pas pu être vérifié

Le vrai runner Rust (inexistant : les tests l'émulent) ; le moteur SQLite embarqué ; l'état des bases locales ; le contenu des fichiers V1 de (b) ; les messages d'origine du 2026-10-13 (source primaire non conservée dans le dépôt).
