# AUDIT — Conformité du SQL de la chaîne complète (001 → 009a → 009b) aux décisions métier validées — révision G

**Date** : 2026-10-17 · **Nature** : document de travail (relecture), non officiel, aucun fichier sous `docs/` modifié · **Remplace** l'audit de la révision F (même objet) · **Référence intangible** : décisions métier validées (révision F : 2.1 à 2.4, 3.1 à 3.4, 4 ; décisions du 2026-10-17 11:47 ; règles du registre d'invariants ; règle stricte d'annulation du BC du 2026-10-13, voir `RAPPORT__comparaison_009a_BC_et_009b_acompte_garanties.md`). **Cette révision n'est pas validée.**

## 1. Changements de la révision G par rapport à la révision F

| # | Changement | Où |
|---|---|---|
| G1 | **Garde de cumul retirée** : la règle ajoutée par l'audit F (un acompte ne porte pas la facturation nette à 100 % si l'acompte prévu du marché est < 100 %) était une interprétation, ni nécessaire ni validée. Supprimée du SQL, des tests (2 tests et 1 mutation) et de tous les documents de travail | `009b`, `test_009b`, modèle SQLite §3.2 et TR-22, invariants INV-57 et journal |
| G2 | **Ordre des factures** : « une facture d'acompte ne peut pas être émise après une facture de situation ». Le SQL livré (006) ne refusait l'acompte qu'**après un solde** : la règle est ajoutée à `tr_22_factures_acompte` (message `INV-58`) | `009b`, classe `OrdreDesFactures` |
| G3 | **Corrective renommée** `009a_acompte_garanties_manuelles` → `009b_…` (rang 14) ; la corrective d'annulation du BC (TR-103) est intégrée au rang 13 sous le nom `009a_bc_annulation_interdite_si_facture` ; 010 passe au rang 15 | comparaison dans le rapport dédié |
| G4 | **Consignation officielle de travail** : « contractuel courant après moins-value » = **À CONCEVOIR** (§4, point 1) | modèle métier § 8, modèle SQLite §3.2 et PT-12, ce document |
| G5 | Documents alignés sur la règle stricte d'annulation du BC (INV-44, D-05, E-07, E-15, D-35, D-46, C-19, modèle métier, CDC amendement E-15) | voir le rapport de comparaison, §4 |

### Vérification que le retrait de la garde ne réintroduit aucune contradiction

| Règle de facturation | Contrôle SQL après retrait | Contradiction ? |
|---|---|---|
| Acompte ≤ acompte prévu du devis accepté ; `aucun` ⇒ aucun acompte | `tr_22_factures_acompte` (CASE sur `acompte_type`, centimes, HALF_UP) | non |
| Acompte facultatif ; situations sans acompte préalable | aucun trigger n'exige un acompte | non |
| Aucun acompte après situation ni après solde | `tr_22_factures_acompte` (nouveau pour la situation ; 006 pour le solde) | non |
| Un seul acompte actif par devis (INV-52) ; devis rattaché au BC (INV-189) | inchangé | non |
| Facturation nette ≤ contractuel (INV-57) | inchangé | non |
| Acompte prévu à 100 % intégralement facturé : autorisé, pas de clôture automatique | aucun trigger ne modifie le BC ; ni solde (INV-55 : 0.00 refusé ; INV-58 : positif refusé) ni situation (< 100 %) n'est possible ensuite | non |
| Aucun solde à 0 € | `tr_22_factures_solde` | non |
| Situation jamais à 100 % | `tr_22_factures_situation` | non |
| « Seul un solde valide clôture le cycle » quand l'acompte prévu < 100 % | **conséquence arithmétique, sans règle supplémentaire** : avec un acompte unique par devis, plafonné à son acompte prévu, et placé avant toute situation, les acomptes seuls ne peuvent pas atteindre 100 % du contractuel lorsque l'acompte prévu du marché est < 100 % | non (test `acompte_prevu_inferieur_a_100_les_acomptes_seuls_ne_peuvent_pas_atteindre_100`) |
| Avoir total sur un acompte, puis nouvel acompte (INV-185) | inchangé, **sauf** s'il existe une situation : l'ordre prime (« émise » = existante) | interprétation à confirmer (test `une_situation_deja_creditee_reste_une_situation_emise…`) |
| BC à deux devis, devis rattaché après une situation | son acompte prévu ne peut plus être facturé (ordre global au BC) | conséquence de la règle d'ordre, **à confirmer** (test `consequence_de_l_ordre_sur_un_bc_a_deux_devis…`) |

## 2. Méthode

1. Schéma réel du **rang 14** extrait d'une base construite par l'émulation du runner (001 → 009, puis 009a au rang 13, puis 009b au rang 14) ; tous les triggers, contraintes et index actifs ont été relus. 75 triggers au rang 14.
2. **Rejeu différentiel** des 1 110 tests de 006, 007, 008 et 009 sur une base portée au rang 14. Les écarts nouveaux par rapport à la révision F sont tous expliqués par G2 (acompte après situation) ou par TR-103 (BC annulé et facturé fabriqué par les anciens tests, exacts à leur rang d'origine) ; aucune régression inexpliquée. Les tests livrés ne sont pas modifiés.
3. Tests : `test_009b_acompte_garanties_manuelles.py` (98 tests, base réellement migrée au rang 14) et `test_009a_bc_annulation_interdite_si_facture.py` (50 tests, dont le garde de chaîne qui rejoue 009b sur une base peuplée).
4. **Mutations** : 23 sabotages (18 sur 009b, 5 sur `tr_103`) : 22 détectés, 1 équivalent (les avoirs ne comptent pas dans `tr_103` : un avoir exige déjà une facture d'origine non avoir sur le même BC).

## 3. Tableau de conformité

Légende résultat : **C** conforme · **C\*** conforme après correction d'une corrective (009a ou 009b) · **S** règle de service (non portable en SQL) · **AC** À CONCEVOIR (empêche l'implémentation complète).
Noms de tests : `test_009b_…` (classes `Acompte`, `OrdreDesFactures`, `SituationEtSolde`, `AvoirsMotifs`, `ContractuelFinal`, `GarantiesManuelles`, `Retraits`, `SuiviActif`, `Chaine`, `Donnees`, `NonRegression`) et `test_009a_…` (groupes A à I).

| # | Décision validée | Implémentation SQL réelle (chaîne finale) | Tests | Résultat | Correction nécessaire |
|---|---|---|---|---|---|
| 1 | **2.1** Facture d'acompte ≤ acompte prévu du devis accepté ; 1 000 € : prévu 30 % → 300 max (200 ok, 350 refusé), prévu 100 % → 1 000 max, aucun prévu → aucune facture d'acompte | `tr_22_factures_acompte` (009b, remplace 006) : CASE sur `devis.acompte_type` (aucun / montant / pourcentage HALF_UP en centimes) | `Acompte` : prévu_30, prévu_100, aucun, montant, arrondi_HALF_UP, deux devis ; `OrdreDesFactures` : plafond conservé | **C\*** | 006 ne contrôlait que ≤ total du devis |
| 2 | **2.1** Acompte facultatif ; situations sans acompte préalable | Aucun trigger n'exige un acompte | `Acompte` : facultatif ; `OrdreDesFactures` : facultatif ; `SituationEtSolde` : aucune_exigence | **C** | — |
| 3 | **2.1** Acompte à 100 % autorisé s'il est prévu à 100 % : ni blocage ni confirmation spéciale | Seul le plafond du devis s'applique | `Acompte` : prévu_100 ; `OrdreDesFactures` : prévu_100 (×2) | **C** | Confirmation de la révision E retirée de tous les documents |
| 4 | **Décision du 2026-10-17** — Une facture d'acompte ne peut pas être émise après une facture de situation | `tr_22_factures_acompte` (009b), message `INV-58: aucun acompte apres une situation` ; **006 ne portait que « après un solde »** | `OrdreDesFactures` : aucun_acompte_après_une_situation, situation_déjà_créditée, conséquence_deux_devis ; mutations « acompte après situation permis » et « ordre limité aux soldes » | **C\*** | G2 ; deux interprétations signalées (« émise » = existante ; ordre global au BC) |
| 5 | INV-52 Un acompte actif par devis ; INV-189 devis rattaché au BC ; INV-58 aucun acompte après un solde | `tr_22_factures_acompte` (repris de 006) | `Acompte` : règles_antérieures ; `OrdreDesFactures` : après_un_solde ; `AvoirsMotifs` : sur_acompte | **C** | — |
| 6 | **2.2** Une situation ne porte jamais le cumul à 100 % (nette après < contractuel) | `tr_22_factures_situation` (009b) | `SituationEtSolde` : jamais_100 %, cumul_avec_acompte | **C\*** | 006 admettait `≤` |
| 7 | **2.3** Acompte prévu < 100 % : seul un solde valide (> 0) clôture le cycle | `tr_22_factures_solde` (solde > 0, INV-55) ; **aucune garde de cumul supplémentaire** ; l'impossibilité d'atteindre 100 % par les seuls acomptes est une conséquence arithmétique du plafond, de l'acompte unique par devis et de l'ordre | `OrdreDesFactures` : seul_un_solde_valide_clôture, les_acomptes_seuls_ne_peuvent_pas_atteindre_100, aucune_règle_de_cumul_supplémentaire (le trigger ne contient que les contrôles validés) | **C** | G1 : garde retirée |
| 8 | **2.3** Acompte prévu 100 % intégralement facturé : autorisé, pas de clôture automatique, pas de solde à 0 € ; suite À CONCEVOIR | Aucun trigger ne modifie le BC ; solde à 0.00 refusé (INV-55), solde positif refusé (INV-58), situation refusée (INV-57) | `OrdreDesFactures` : acompte_prévu_100 (BC à un devis et à deux devis) | **C** pour l'existant ; suite = **AC** | § 4 point 2 |
| 9 | **2.4** Distinguer plafond d'acompte / limite des situations / clôture | Trois contrôles distincts dans `tr_22` (acompte, situation, solde) | tests ci-dessus | **C\*** | Documents réécrits (métier §10-§12, INV-57) |
| 10 | INV-55 Aucun solde à 0.00 | `tr_22_factures_solde` ; le `CHECK` de 006 est conservé (reconstruire `factures` n'est pas justifié) | `SituationEtSolde` : aucun_solde_à_0 ; `Donnees` : solde_0_00_historique | **C\*** | Un solde à 0.00 **historique** reste en base, immuable (TR-20) |
| 11 | **2.4** / INV-58 Solde = contractuel **final** − nette avant solde ; avoirs « prestations non réalisées » sur solde non refacturables | `tr_22_factures_solde` (009b) : Σ devis − Σ avoirs `prestation_non_realisee` d'origine solde − nette | `ContractuelFinal` : 7 tests | **C\*** | A3 de la révision F |
| 12 | **2.4** Contractuel **courant** = accepté − réductions acceptées non annulées (moins-values) | **Non modélisé** : aucune table de réductions ; les triggers lisent le montant accepté | `ContractuelFinal` : limite documentée | **AC** | **Consigné officiellement À CONCEVOIR, voir § 4 point 1** : le calcul du contractuel courant après moins-value n'est pas entièrement implémenté ; la partie ne peut pas être déclarée conforme |
| 13 | INV-76 Motif d'avoir obligatoire en liste fermée | `tr_23_factures_avoir` (009b) + CHECK 006 (motif non vide) | `AvoirsMotifs` : liste fermée, hors liste, absent | **C\*** | A1 ; avoirs historiques au motif libre conservés |
| 14 | INV-76 Un avoir sur acompte ne corrige qu'une erreur | `tr_23_factures_avoir` | `AvoirsMotifs` : sur_acompte | **C\*** | A2 |
| 15 | INV-76 Avoir « prestations non réalisées » sur situation : aucune réduction automatique ; correction d'erreur : aucune réduction | Formule du solde : seuls les avoirs d'origine solde sont déduits ; `tr_51_bc_ligne_retraits_garantie_insert` (R2) | `ContractuelFinal` : avoir_sur_situation ; `Retraits` : sur_situation, erreur | **C** | — |
| 16 | INV-76 Σ avoirs ≤ origine ; origine non avoir ; même BC ; avoir possible sur BC annulé/terminé | `tr_23_factures_avoir` (repris), `tr_16_factures_bc` | `AvoirsMotifs` : règles_antérieures ; `NonRegression` | **C** | — |
| 17 | INV-58 Un avoir partiel ne rouvre pas la facturation ; un avoir total permet une nouvelle facture du même type ; aucun acompte/situation après un solde même crédité | `tr_22_factures_*` ; `tr_99_bc_devis_apres_solde` | `ContractuelFinal` : avoir_partiel ; `Acompte` : règles_antérieures | **C** | Exception d'ordre : voir ligne 4 (situation) |
| 18 | INV-187 Aucun devis après un solde (même crédité) | `tr_99_bc_devis_apres_solde` | `OrdreDesFactures` : seul_un_solde_valide_clôture | **C** | — |
| 19 | **Règle stricte du 2026-10-13** — INV-44 : aucun BC ne passe à `annule` dès qu'une facture existe (acompte prévu sans facture : annulation permise) | `tr_103_bons_commande_annulation_facturee` (009a) | `test_009a_…` : groupes A à I (50 tests : tous types de facture, réglée ou non, avoir total, acompte prévu, rollback, REPLACE/UPSERT, BC déjà annulé, non-régression, garde de chaîne) | **C\*** | Rédaction documentaire **à valider** (statut § 4 point 8) ; aucun SQL livré ne portait cette règle |
| 20 | RAF, reste dû, CA engagé (dérivés non persistés) | Aucun objet SQL ; calculs de service | — | **S** | Valeurs dérivées (modèle §3.2, §3.6) ; leur calcul après moins-value dépend de la ligne 12 |
| 21 | **3.1** Garanties déclenchées manuellement, indépendamment du solde, du cycle, du paiement | `garanties.facture_declenchement_id` nullable ; `tr_51_garanties_insert` sans condition d'état ; 008 ne crée aucune garantie automatiquement | `GarantiesManuelles` : sans_facture, avant_le_solde, date_libre, BC annulé/terminé, ancienne voie | **C\*** | 008 : référence de facture obligatoire (NOT NULL) levée par reconstruction |
| 22 | **3.1** Périmètre = périmètre contractuel réel ; une prestation retirée ne peut plus être déclenchée | `bc_ligne_retraits_garantie` + garde G5 de `tr_51_garanties_insert` | `Retraits` : prestation_retirée_ne_peut_plus_être_déclenchée | **C\*** | — |
| 23 | **3.2** Matrice : avoir d'erreur → aucun retrait ; « non réalisées » sur situation → aucun retrait automatique ; « non réalisées » sur solde → retrait à lui seul ; moins-value totale → retrait | `tr_51_bc_ligne_retraits_garantie_insert` : R1, R2, R3 ; `UNIQUE(bc_ligne_id)` | `Retraits` (matrice, désignation par ligne d'avoir, aucun double retrait, autre BC) | **C** pour l'avoir ; moins-value : **S** | La moins-value n'a aucune source en base (ligne 12) : le service écrit le retrait `moins_value` |
| 24 | **3.3** Avertissement avant validation d'une moins-value (ou avoir) sur une prestation dont la garantie est déjà déclenchée | Aucun (interface/service) ; la vue `v_garanties_suivi_actif` permet de détecter le cas | — | **S** | — |
| 25 | **3.3** Moins-value totale confirmée : seule la ligne de suivi de cette prestation sort du suivi actif ; historique traçable | Table append-only `bc_ligne_retraits_garantie` (TR-50) ; suivi actif = vue sans retrait ; `garanties` jamais modifiée | `SuiviActif` ; `Retraits` : seule_cette_ligne… | **C\*** | A5 (vue) |
| 26 | **3.3** Moins-value partielle : ne supprime pas tout le suivi (détail À CONCEVOIR) | Aucun trigger ne supprime ni ne modifie une garantie ; le service n'écrit pas de retrait pour un cas partiel | `Retraits` : immuabilité ; `GarantiesManuelles` : unicité_et_immuabilité | **C** pour la garantie préservée ; détail = **AC** | § 4 point 4 |
| 27 | **3.3** Une opération annulée ou non validée ne modifie pas le suivi | Un retrait par avoir exige l'avoir existant (R2, R3, CHECK) | `SuiviActif` : opération_non_validée, retrait_par_avoir_sans_avoir_valide | **C** pour les avoirs ; annulation d'une réduction acceptée = **AC** | § 4 point 5 |
| 28 | **3.4** Le modèle permet : identifier les prestations, associer une garantie à une prestation, déclencher sans solde, exclure les prestations retirées, retirer une seule ligne de suivi, conserver la traçabilité | `bc_lignes`, `bc_ligne_garanties(ligne_id)`, `garanties(bc_ligne_id)`, `bc_ligne_retraits_garantie`, vue du suivi actif | `Chaine` (schéma exact), `SuiviActif`, `Retraits` | **C\*** | Migration corrective 009b |
| 29 | INV-87 Garantie immuable, `date_declenchement` immuable | `tr_50_garanties_*` recréés à l'identique | `Chaine` : triggers_recréés ; `GarantiesManuelles` | **C** | — |
| 30 | INV-134 Aucune garantie importée | Garde G3 de `tr_51_garanties_insert` | `GarantiesManuelles` : G1_G3 | **C** | — |
| 31 | **4** Écarts de 006 (acompte vs total devis ; situation jusqu'à 100 % ; solde 0 €) | Corrigés par 009b | lignes 1, 6, 10 | **C\*** | — |
| 32 | **4** Écarts de 008 (génération au premier solde ; facture de déclenchement obligatoire ; tests liant garanties au solde ; schéma bloquant le retrait par prestation) | Génération : 008 SQL n'en contenait aucune (service) ; facture : nullable ; retrait : table dédiée ; tests 006/008 annotés (ils décrivent les rangs 9 à 12) | `Chaine`, `Donnees`, `GarantiesManuelles` | **C\*** | — |
| 33 | **4** Migration testée sur base déjà migrée, données préservées, contraintes non désactivées globalement | 009b : gardes `foreign_keys=0` et `user_version=13`, copie technique avec ids, `sqlite_sequence`, `foreign_key_check`, `integrity_check`, ROLLBACK intégral ; 009a : un seul `CREATE TRIGGER`, aucune donnée | `Chaine` (atomicité, protocole), `Donnees` ; 009a groupes A et D | **C** | — |

## 4. Points À CONCEVOIR et points à arbitrer

### Consignation officielle de travail — « contractuel courant après moins-value » : À CONCEVOIR

1. **Aucun mécanisme de stockage des réductions n'est actuellement conçu ni validé** (PT-12). Sont indécidés : ce qu'une réduction porte (montant, quantité, prix), total ou partielle, son articulation avec l'exécution, la date et le motif d'annulation d'une réduction.
2. **Le calcul du contractuel courant après moins-value ne peut donc pas être considéré comme entièrement implémenté.** En base, le contractuel lu par les triggers est le montant accepté ; seul le contractuel *final* déduit les avoirs « prestations non réalisées » d'origine solde.
3. **La conception du mécanisme de réduction est une dépendance** avant de pouvoir déclarer conformes : le solde, la limite des situations, le plafond de facturation, le reste à facturer et le CA engagé après moins-value.
4. **Le mécanisme ne doit être ni inventé ni implémenté sans cadrage et validation préalables.**
5. **Comportement actuel sûr** : aucune réduction ne peut exister en base ; un solde calculé par le service avec une réduction est refusé par `tr_22_factures_solde` plutôt qu'accepté à tort.

Cette consignation figure aussi dans : modèle métier V6 § 8 ; modèle de données SQLite §3.2 et ligne PT-12 ; journal des invariants ; ce document. Rien n'est écrit sous `docs/`.

### Autres points

2. **Cycle après un acompte prévu à 100 % intégralement facturé** : clôture explicite éventuelle, état final du BC, « 100 % facturé » et `date_100_facture`. Aucun mécanisme n'est déduit.
3. **Reste à facturer nul sans solde par moins-value** : mécanisme de clôture non décidé (dépend du point 1).
4. **Moins-value ou avoir partiel sur une prestation suivie** : sort du suivi, granularité, périmètre résiduel.
5. **Annulation d'une réduction dont le retrait de garantie est déjà acté** (dépend du point 1).
6. **Mécanisme, granularité et date du déclenchement manuel** des garanties (service).
7. **Retrait définitif de `facture_declenchement_id`** (colonne historique conservée, nullable).
8. **Règle stricte d'annulation du BC** : arbitrage du 2026-10-13 non consigné dans le dépôt avant cette révision ; intégrée aux documents de travail et au SQL (009a) **sous réserve de validation** ; non intégrés : cascade BC → devis, passages d'import (INV-169), CDC §17 dans `docs/`, erratum de support et numéros (voir rapport de comparaison §4).
9. **Interprétations de la règle d'ordre** : « émise » = existante, même créditée ; ordre global au BC (un devis rattaché après une situation ne peut plus facturer d'acompte).

## 5. Choix techniques à relire

- Deux correctives successives (009a puis 009b) plutôt qu'une seule : voir le rapport de comparaison, §5.
- La vue `v_garanties_suivi_actif` : nom proposé, hors familles d'identifiants officiels. `TR-103` est repris de la proposition du 2026-10-13 ; aucun autre identifiant officiel (INV, TR, CK, D, E, T) n'est créé.
- Le retrait par avoir désigne la prestation par une ligne de l'avoir référençant la ligne de BC (`facture_lignes.bc_ligne_id`).
- Rangs : 010 → 15 ; `010a_*` → 16 ; 011 → 16 ; `011a_*` → 17. Le diff documentaire `DIFF_DOC__010_historique_planification.diff` (010 = rang 13, 011 = rang 14) est à réémettre : non fait ici.

## 6. Vérifications non réalisables ici

Exécution par le **vrai runner Rust** (inexistant : les tests l'émulent) ; moteur SQLite embarqué de l'application ; état des bases locales de développement (`PRAGMA user_version` attendu ≤ 12) ; services (annulation du BC, émission des factures, déclenchement des garanties) absents du dépôt.
