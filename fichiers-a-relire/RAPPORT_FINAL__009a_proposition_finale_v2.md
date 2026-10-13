# RAPPORT FINAL — Corrective 009a (proposition V2) : rang 13, TR-103, test de garde

**Date** : 2026-10-13 · **Base** : `main` 74adb2f (vérifiée à jour) · **Nature** : proposition non officielle, dépôt exclusif dans `fichiers-a-relire/`.
**Conservés en l'état** : `RAPPORT__009a_…md`, `RAPPORT_COMPLEMENT__009a_…md`, `PROPOSITION_DIFF__009a_bc_annulation_interdite_si_facture.diff` (blob `7e9d3e34…`, recalculé : identique).
**Aucune modification** de `docs/` ni des migrations livrées ; aucun commit, aucun push. Un clone neuf de `main` avec le diff V2 n'a que deux fichiers ajoutés.

## 1. Verdict

**La proposition V2 est prête pour une validation finale sur le plan technique.** Trois conditions restent avant l'intégration (§9) : la vérification des bases de développement (je ne peux pas la faire d'ici), l'autorisation du lot documentaire, et cinq décisions documentaires.

## 2. Livrables

| Fichier | Contenu |
|---|---|
| `PROPOSITION_DIFF__009a_V2_bc_annulation_interdite_si_facture.diff` (blob `0d11cc71…`, 762 lignes, 2 fichiers ajoutés) | migration 009a + 50 tests ; **remplace** le diff V1, qui reste disponible pour comparaison |
| `PLAN_MAJ_DOC__009a_regle_annulation_bc.md` | liste ligne par ligne des modifications documentaires, dans l'ordre hiérarchique |
| ce rapport | rang, bases de développement, chaîne, nommage, garde, vérifications |

**Différences V1 → V2**
- **SQL** : le trigger est **identique au caractère près** ; seul l'en-tête change (rang 13 décidé, TR-103 définitif, distinction acompte prévu / facture d'acompte, émission échouée, absence d'import de BC annulé, suppression de la phrase sur la « règle inverse » du modèle V3.13).
- **Tests** : 40 → **50** (+3 de couverture, +7 de garde de chaîne ; une assertion d'ordre ajoutée à un test existant ; le test d'import est réécrit sans changer de comportement).

## 3. Rang 13 et bases de développement

**Vérifié dans le dépôt** : `main` est la seule branche ; aucune migration 010 ou supérieure n'existe ; aucun fichier de base (`.db`, `.sqlite`) n'est versionné ; aucun code ne pose `user_version` (le runner n'existe pas, V-5) ; aucun texte ne pose `user_version = 13`.
**Non vérifiable** : l'état réel de tes bases locales. L'ordinateur lié n'est pas connecté à cette session (l'appel au pont a échoué). Une base de développement ne peut être au rang 13 que si tu y as appliqué à la main un fichier local « 010 » absent du dépôt.

**Vérification à faire de ton côté**, pour chaque base de développement :
`sqlite3 <base>.db "PRAGMA user_version;"` — toute valeur **≤ 12** est sans conflit (009a s'appliquera au rang 13). Toute valeur **≥ 13** est un conflit à traiter avant l'intégration.

**Conflit documenté** (simulé hors dépôt, `scratchpad/conflit_base_dev.py`). Une base au rang 13 ayant appliqué un 010 local :
1. n'a pas `tr_103` (009a n'a jamais été jouée) ;
2. le runner (rangs k+1 à N) ne rejoue pas le rang 13 ; au rang 14 il tenterait de rejouer 010 sur une base qui l'a déjà, donc échec « table existante » avec ROLLBACK, ou répétition silencieuse si 010 est idempotent ;
3. ses schémas diffèrent de ceux d'une chaîne neuve.

**Solution sûre, sans réécrire ni déplacer de migration livrée** (aucune migration livrée n'est au rang 13) :
- **Base jetable** : la recréer par la chaîne 1 → 14. C'est la solution la plus simple.
- **Base à conserver** : une seule transaction `BEGIN IMMEDIATE` ; vérifier `user_version = 13` et l'absence de `tr_103` ; exécuter l'instruction `CREATE TRIGGER` de 009a ; poser `PRAGMA user_version = 14` ; `COMMIT`. Simulée : après cette procédure, le schéma est **identique** à celui d'une chaîne neuve 001 → 009a → 010, `integrity_check` = ok et `foreign_key_check` vide. **Condition** : le 010 local doit être strictement le 010 final ; à contrôler en comparant `sqlite_master` avec une base neuve.

Aucune autre action n'est nécessaire côté dépôt.

## 4. Chaîne après correction

| Rang | Migration | État | Dépendances |
|---|---|---|---|
| 1 à 4 | `001` à `004` | livrées | — |
| 5 | `005_depenses` | livrée | BC, fournisseurs |
| 6 | `005a_corrections_v313` | livrée (garde `user_version = 5`) | devis, BC |
| 7 | `005b_bc_multi_devis` | livrée (garde `user_version = 6`) | `bc_devis` |
| 8 | `005c_bc_annule_caches_financiers` | livrée (D-56) | `tr_12` |
| 9 à 12 | `006_facturation`, `007_reglements`, `008_garanties`, `009_pv` | livrées | BC, factures |
| **13** | **`009a_bc_annulation_interdite_si_facture`** | **proposée (V2)** | `bons_commande`, `factures` ; rien ne dépend d'elle |
| **14** (était 13) | `010_planification` | prévue, non créée | `planning_evenements.bc_id` → BC |
| **15** (était 14) | `011_historique` | validée dans le diff 011 seulement | `historique.bc_id` → BC |
| — | corrective « contrôle NUL » 001–008 | non planifiée (P-4) | reconstruirait des tables, dont `bons_commande` |
| 16 | `011a_*` hypothétique (était 15) | — | exige 010 et 011 livrées |

Chaîne `machine.db` : inchangée (rang 1, `user_version` propre).

## 5. Identifiant du trigger : nom définitif

**`tr_103_bons_commande_annulation_facturee`** (TR-103).
- Convention (conventions techniques l.106) : `tr_<NN>_<table>_<règle>`, `NN` = numéro `TR-NN` du modèle.
- **Aucun conflit** : le plus grand numéro posé par une migration ou cité dans `docs/`, `fichiers-a-relire/` et les cadrages est **102** ; `tr_103` et `TR-103` n'existent nulle part ; le nom complet est unique (SQLite exige un nom unique, pas un numéro unique : `tr_99` est déjà porté par quatre triggers).
- 010 et 011 ne réservent aucun TR-NN (011 utilise TR-60, D-60 exclut tout trigger d'historisation) : leurs éventuels triggers prendront 104 et suivants.
- **Alternative écartée** : réutiliser TR-12 (`bons_commande`, « BC annulé : seuls `client_id` et `updated_at` »). TR-12 règle ce qui est modifiable *après* annulation ; la nouvelle règle porte sur la *transition vers* l'annulation. Les mêler changerait la définition d'un trigger validé.
- **Conséquence** : le modèle doit inscrire la ligne TR-103 (plan §3.2).

## 6. Test de garde de chaîne (groupe I, 7 tests : 2 contrôles et 5 témoins)

**Principe** : le trigger vit sur `bons_commande` ; une reconstruction de cette table (protocole 005a) le supprime silencieusement. Deux niveaux :
- **Contrôle dynamique** (autoritaire) : sur une base du rang 13 **peuplée** (BC portant une facture), chaque migration livrée après 009a est rejouée par l'émulation du runner ; après chacune, la définition du trigger dans `sqlite_master` doit être identique à celle de 009a **et** l'annulation du BC facturé doit rester refusée (`INV-44`). Aujourd'hui aucune migration ne suit 009a : le test s'activera de lui-même à l'arrivée de 010.
- **Contrôle statique** (alerte précoce, message lisible) : toute migration suivante qui supprime ou renomme `bons_commande`, ou supprime le trigger, doit contenir un `CREATE TRIGGER` identique.
- **Témoins** (5) : une migration qui supprime le trigger, une reconstruction sans recréation, une recréation altérée, une recréation identique (acceptée), une migration qui vide `factures` sans toucher au trigger (le refus devient inopérant avec une définition intacte) et une migration sans rapport (non signalée).

**Limites** : la reconstruction de `factures` ne supprime pas le trigger ; elle n'est donc couverte que par le contrôle dynamique (donc seulement si les fabriques de données de test restent valides sur le schéma suivant : le futur auteur de 010 adaptera les fabriques, c'est voulu). Le contrôle statique est une heuristique sur le texte SQL.

## 7. Évaluation des trois tests de couverture et du commentaire d'import

| Point du rapport précédent | Décision | Justification |
|---|---|---|
| Acompte prévu sans facture ne bloque pas | **Ajouté** (`…un_acompte_prevu_au_devis_sans_facture_n_empeche_pas_l_annulation`) | n'était testé que *avec* facture ; vérifie aussi que le BC n'a aucune colonne d'acompte et que le devis garde son acompte prévu (montant et pourcentage) |
| Facture d'acompte réglée ou non | **Ajouté** (`…une_facture_d_acompte_bloque_qu_elle_soit_reglee_ou_non`) | seul le cas non réglé existait |
| Émission échouée ou défaite par rollback | **Ajouté** (`…une_emission_echouee_ou_defaite_par_rollback_n_est_pas_une_facture_existante`) | émission refusée, `ROLLBACK TO`, `ROLLBACK` ; présente dans la transaction, la facture bloque |
| Commentaire du test d'import (PT-19, BC annulé importé) | **Réécrit** et test renommé (`test_009a_H_un_BC_importe_et_facture_ne_s_annule_pas`) | le comportement testé est inchangé ; le commentaire dit désormais qu'aucun import de BC annulé n'est prévu et qu'aucune exception n'existe. Il reste utile : `G_une_facture_importee…` ne teste pas un BC importé avec `legacy_numero` |

## 8. Résultats de vérification

| Contrôle | Résultat |
|---|---|
| Tests 009a | **50 OK** (V1 : 40) |
| Suite complète, fichier par fichier | métier **1 916** + machine **13** = **1 929 OK**, 0 échec (V1 : 1 919) |
| Diff V2 sur clone neuf de `main` | `git apply --check` OK ; le fichier de tests passe (50) ; `docs/` inchangé |
| Corps du trigger V1 / V2 | identique (comparaison de texte) |
| Mutations du SQL (8) | 7 tuées ; **1 équivalent** (M2 « les avoirs ne comptent pas ») : un avoir exige une facture d'origine non avoir sur le même BC (`tr_23`) et les factures ne se suppriment pas, donc aucun BC ne porte *seulement* des avoirs |
| Mutations des tests de garde (4) | 4 tuées (contrôle statique inactif, définition non vérifiée, refus non vérifié, recréation altérée acceptée) |
| Mutants propres aux nouveaux tests | M4 (un acompte prévu bloque) est tué par le test d'acompte prévu ; M7 (une facture réglée ne bloque pas) l'est par le seul test de facture réglée |
| Contrôles complémentaires (27, rapport précédent) | 27 OK sur le SQL, inchangé |

## 9. Hypothèses non vérifiées

1. **Bases de développement** : état réel de `user_version` (§3).
2. **Runner** : le comportement du futur runner est supposé conforme aux conventions §5 (aucun code à lire) ; les tests l'émulent.
3. **Documents en relecture** : je ne sais pas quels éléments de `fichiers-a-relire/MAJ__*` (E-10 à E-20, TR-97 à TR-100, D-40 à D-54) seront retenus dans V3.14 ; la numérotation de E-21 et des futurs T-xx / C-xx en dépend.
4. **Numéros de ligne** du plan : valables à 74adb2f ; à revérifier avant application.
5. **Données historiques** : aucun BC annulé et facturé n'est censé exister (aucun import, aucun runner) ; la requête de détection est fournie dans les tests mais je n'ai aucune base réelle à interroger.

## 10. Ce qui empêche encore l'intégration

1. **Vérifier les `user_version` de tes bases de développement** (§3) ; en cas de rang ≥ 13, appliquer la solution de §3.
2. **Autoriser le lot documentaire** du plan (CDC §17, D-05, INV-44, E-07 / E-21, modèle métier, rangs de la chaîne, diff 011 de remplacement, D-61). La migration cite D-05 et INV-44 : tant que ces textes portent l'exception « acompte non réglé », elle les contredit.
3. **Trancher les décisions du plan §6** : E-21 ou E-15 seul ; statut de D-46 ; sort d'INV-188 / INV-173 / D-56 pour les BC annulés avant 009a ; numéros T-xx, C-xx, E-xx ; calendrier du report des rangs (au moment de l'intégration de 009a, pas avant).
4. **Traiter à part le flux INV-35** (acompte annulé automatiquement, annulation de facture) : non intégré à cette corrective.

*Risque* : si une base de développement est déjà au rang 13, 009a n'y sera jamais appliquée et le trou (BC annulable malgré une facture) y subsiste sans erreur visible.
*Micro-amélioration* : faire contrôler par le futur runner, au démarrage, la présence des triggers de garde connus (au minimum `tr_103`) en plus du `user_version`.
