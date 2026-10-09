# PLAN DE REMÉDIATION 001–008 — octet NUL dans les colonnes validées par `GLOB`, `json_valid` ou un mécanisme assimilé

**Statut : PLAN, à valider par Rémy. Aucune migration 001–008 n'est modifiée ; aucune migration nouvelle n'est écrite ; rien n'est appliqué.**
Date : 2026-10-10. Dépôt : HEAD `a9fd50f` + fichiers 008/009 non suivis. Base d'analyse : l'inventaire de `COMPLEMENT_ANALYSE__009_pv__controle_nul.md` §1 (137 colonnes évaluées, **90 vulnérables**, 21 tables). SQLite 3.45.1.
Légende : **FAIT** = observé par exécution ; **HYPOTHÈSE** = non vérifié (services Rust/TS, runner et base de production hors du dépôt analysé).

---

## 0. Ce qu'il faut retenir

1. 90 colonnes de 21 tables acceptent un octet NUL suivi d'une queue : 41 horodatages, 26 décimaux, 17 JSON, 4 numéros, 2 codes.
2. **Le risque métier est très inégal.** Les numéros/codes (6) et les décimaux « DL » (10) concentrent le risque ; les horodatages (41) sont, pour 32 d'entre eux, remplis par `DEFAULT` et sont les moins exposés.
3. **Aucune migration existante n'est réécrite** (conventions techniques : « une migration déjà appliquée n'est pas réécrite », la correction passe par une migration ultérieure). La correction de 001–008 est donc nécessairement une **nouvelle migration** (reconstruction de table ou triggers de garde) ou une mesure hors schéma (service, détection).
4. Plusieurs tables sont **immuables après écriture** (triggers `no_update`, `numero_immuable`, gel) : une valeur fautive déjà stockée ne se répare pas par `UPDATE`. Une correction préventive pèse donc plus lourd qu'une correction après coup.
5. Une migration corrective peut **échouer au démarrage** sur une base contenant déjà une valeur fautive (copie de reconstruction refusée par le nouveau CHECK) : la requête de détection de l'annexe doit précéder toute migration.
6. Je recommande un **séquencement en vagues** (§5) : détection et validation de service d'abord (sans schéma), gardes ciblées (numéros, codes, décimaux DL, JSON) ensuite, le reste en acceptation documentée ou par reconstruction groupée si une reconstruction est de toute façon décidée.

---

## 1. Classement par classe de colonnes

| Classe | Colonnes | Écriture normale | Ce que provoque un NUL (FAIT / HYPOTHÈSE) | Réparable par `UPDATE` ? | Risque métier | Priorité |
|---|---:|---|---|---|---|:--:|
| **Numéros** (`devis`, `bons_commande`, `factures`, `depenses` `.numero`) | 4 | service de numérotation (valeur construite) ; numéro importé libre (INV-131) | **FAIT** : `PVR-…␀junk`-type accepté sur chaque table (essais sur clone STRICT du CHECK réel) ; deux numéros « identiques » à l'affichage coexistent malgré `UNIQUE` (comparaison binaire) ; `yy` lu avant le NUL | **non** : triggers `*_numero_immuable` / `no_update` | **ÉLEVÉ** : identité légale du document (INV-20, INV-27), unicité apparente faussée, export/impression tronqués | **P1** |
| **Codes** (`clients.code`, `fournisseurs.code`) | 2 | service de codification | **FAIT** : `CLI-0001␀` accepté et coexiste avec `CLI-0001` | **non** : `*_code_immuable` | **ÉLEVÉ** (même mécanisme) | **P1** |
| **Décimaux « DL »** (quantités, prix unitaires, remises de lignes ; `prestations.prix_unitaire_ht`) | 10 | saisie utilisateur validée par le service | **FAIT** : aucun `GLOB` positif ; NUL **au début, au milieu, final, + queue** acceptés (`INSERT` réel sur `prestations`) ; `CAST('␀12.50' AS REAL)` vaut **0.0**, `CAST('1␀2.50' AS REAL)` vaut **1.0** : la valeur calculée diffère silencieusement de la valeur affichée | selon la table (triggers de verrouillage existants ; `facture_lignes` : `no_update`) | **ÉLEVÉ** : montant ou quantité lus à 0 / tronqués, totaux faux | **P1** |
| **Décimaux « D2 »** (montants `0.00`, totaux, avancements ; 16 colonnes) | 16 | service | **FAIT** : NUL final / + queue acceptés (précédent documenté : cadrage 007 §6 (2)) ; NUL au début / milieu refusés ; le `CAST` en centimes lit la partie conforme | selon la table | **MOYEN** : la valeur lue est la valeur conforme ; reste une donnée non conforme stockée (export, comparaison de chaînes) | **P2** |
| **JSON** (snapshots, `legacy_data`, `contenu`, `donnees`) | 17 | sérialisation par le service | **FAIT** : `json_valid('{}␀junk')` = 1 ; **HYPOTHÈSE** : un lecteur JSON strict (Rust) refuserait le texte entier (« trailing characters ») → document illisible | **non** pour les snapshots gelés, `devis_revisions` (`no_update`) | **MOYEN à ÉLEVÉ** : preuve du contenu émis (snapshots) rendue illisible ou ambiguë ; disponibilité plutôt qu'intégrité | **P2** |
| **Horodatages** (`*_at`) | 41 dont 32 avec `DEFAULT strftime` | `DEFAULT` pour 32 ; service pour 9 (`bons_commande` ×3, `devis` ×2, `depenses`, `reglements`, `devis_revisions.valide_at`, `import_anomalies.traite_at`) | **FAIT** : NUL final / + queue acceptés ; **HYPOTHÈSE** : comparaisons de chaînes (`<`, tri) faussées (`x␀` > `x`) | selon la table | **FAIBLE** (32 colonnes, `DEFAULT` ne produit jamais de NUL) à **MOYEN** (9 colonnes écrites par le service : chronologie, gel) | **P3** |

(† = colonne remplie par `DEFAULT` ; ‡ = famille décimale DL ; voir le tableau §3.)

---

## 2. Modes de correction possibles

| Mode | Contenu | Ce que ça garantit | Limites | Vérifié ici |
|---|---|---|---|---|
| **M1 — Validation de service** | refuser tout octet NUL en entrée (Rust/TS) pour tout texte persisté, et dans le sérialiseur JSON | aucune écriture applicative ne produit de NUL | ne protège pas contre un autre écrivain (import, SQL direct, bug) ; **le code des services n'est pas dans le dépôt analysé** (non vérifiable) | non (hors dépôt) |
| **M2 — Détection** (diagnostic CK) | requête en lecture seule `instr(CAST(col AS BLOB), x'00') > 0` sur les 90 colonnes (annexe) | inventaire des valeurs fautives déjà stockées ; pré-condition de M3/M4 | ne prévient rien | **FAIT** : 0 ligne sur base saine ; 3 lignes détectées sur 3 NUL injectés (`clients.code`, `.created_at`, `.legacy_data`) |
| **M3 — Triggers de garde** (nouvelle migration) | `BEFORE INSERT` et `BEFORE UPDATE OF <colonnes>` par table : `WHEN instr(CAST(NEW.c AS BLOB), x'00') > 0 … RAISE(ABORT, …)` | refus à l'écriture, sans reconstruire la table ; attrape aussi `INSERT OR REPLACE` et l'UPSERT | n'agit pas sur les lignes existantes ; ajoute jusqu'à 42 triggers (INV-/TR- à attribuer, modèle à mettre à jour) ; interaction avec les triggers d'immuabilité existants à tester ; hors du texte des CHECK | **FAIT** (sondage sur `clients`) : insertion avec `code`/`legacy_data` à NUL refusée avec le message du trigger, valeur conforme acceptée |
| **M4 — Reconstruction avec CHECK complété** (nouvelle migration, protocole 005a) | `length(CAST(c AS BLOB)) = n` (formats fixes), `instr(…) = 0` (JSON, décimaux, …) ajoutés aux CHECK existants | correction **au même niveau que 009** (CHECK) ; toutes les voies d'écriture | lourd : 21 tables dont `devis`, `bons_commande`, `factures` (nombreux triggers, index, FK) ; `foreign_keys=OFF` hors transaction ; `sqlite_sequence` à préserver ; la copie échoue si une ligne existante viole le nouveau CHECK | non exécuté (aucune migration écrite) |
| **M5 — Acceptation documentée** | consigner la limite sur le modèle de cadrage 007 §6 (2), avec test témoin | décision explicite et traçable | le défaut subsiste | — |

---

## 3. Les 90 colonnes, table par table

† = remplie par `DEFAULT` · ‡ = famille décimale DL · « UPDATE gardé » = nombre de triggers `BEFORE UPDATE` existants sur la table (immuabilité, gel, états) à reconsidérer pour toute réparation.

| Table | Fichier(s) | Numéros / codes | Décimaux | JSON | Horodatages | Total | UPDATE gardé |
|---|---|---|---|---|---|---:|---|
| `bc_devis` | 005b | — | — | — | `created_at†` | 1 | oui (1) |
| `bc_ligne_garanties` | 005b (antérieur : 004) | — | — | — | `created_at†` | 1 | oui (1) |
| `bc_lignes` | 004 | — | `prix_unitaire_ht‡`, `quantite‡`, `remise_valeur‡`, `total_ht` | — | `created_at†`, `updated_at†` | 6 | oui (1) |
| `bons_commande` | 005b (antérieur : 004) | `numero` | `avancement†`, `montant_contractuel_ht`, `montant_deja_facture_ht†` | `chantier_snapshot`, `client_snapshot`, `entreprise_snapshot`, `legacy_data` | `cancelled_at`, `completed_at`, `created_at†`, `frozen_at`, `updated_at†` | 13 | oui (4) |
| `categories_depenses` | 001 | — | — | — | `created_at†`, `updated_at†` | 2 | non |
| `categories_prestations` | 001 | — | — | — | `created_at†`, `updated_at†` | 2 | non |
| `clients` | 005a (antérieur : 001) | `code` | — | `legacy_data` | `created_at†`, `updated_at†` | 4 | oui (1) |
| `depenses` | 005 | `numero` | `montant` | — | `cancelled_at`, `created_at†`, `updated_at†` | 5 | oui (2) |
| `devis` | 005a | `numero` | `acompte_valeur`, `remise_valeur`, `total_ht` | `chantier_snapshot`, `client_snapshot`, `entreprise_snapshot`, `legacy_data` | `cancelled_at`, `created_at†`, `frozen_at`, `updated_at†` | 12 | oui (11) |
| `devis_ligne_garanties` | 003 | — | — | — | `created_at†` | 1 | oui (1) |
| `devis_lignes` | 003 | — | `prix_unitaire_ht‡`, `quantite‡`, `remise_valeur‡`, `total_ht` | — | `created_at†`, `updated_at†` | 6 | oui (1) |
| `devis_revisions` | 005a | — | `total_ht` | `contenu` | `created_at†`, `valide_at` | 4 | oui (1) |
| `facture_lignes` | 006 | — | `avancement_cumule_pct`, `avancement_precedent_pct`, `montant_ht`, `prix_unitaire_ht‡`, `quantite‡`, `remise_valeur‡` | — | `created_at†` | 7 | oui (1) |
| `factures` | 006 | `numero` | `montant_deja_facture_ht`, `total_ht` | `chantier_snapshot`, `client_snapshot`, `entreprise_snapshot`, `legacy_data` | `created_at†` | 8 | oui (1) |
| `fournisseurs` | 002 | `code` | — | — | `created_at†`, `updated_at†` | 3 | oui (1) |
| `garanties` | 008 | — | — | — | `created_at†` | 1 | oui (1) |
| `import_anomalies` | 001 | — | — | `donnees` | `created_at†`, `traite_at` | 3 | oui (1) |
| `numerotation_sequences` | 001 | — | — | — | `created_at†`, `updated_at†` | 2 | oui (1) |
| `prestation_garanties` | 001 | — | — | — | `created_at†` | 1 | non |
| `prestations` | 001 | — | `prix_unitaire_ht‡` | `legacy_data` | `created_at†`, `updated_at†` | 4 | non |
| `reglements` | 007 | — | `montant` | `legacy_data` | `cancelled_at`, `created_at†` | 4 | oui (2) |

Total : 90 colonnes.

---

## 4. Conséquences pour les bases ayant déjà appliqué 001–008

**Constat documentaire.** Les conventions techniques interdisent de réécrire une migration appliquée (une évolution ou une correction structurelle passe par une migration ultérieure) et indiquent que le runner « n'existe pas encore ». *HYPOTHÈSE : aucune base de production n'a encore appliqué 001–008 ; à confirmer par Rémy.* Dans ce cas seul l'ordre de la chaîne compte ; dans le cas contraire, tout ce qui suit s'applique.

1. **Modifier 001–008 en place** : interdit par la convention, et sans effet sur les bases déjà migrées → schémas divergents entre bases neuves et bases migrées, et tests comparant bases neuves et bases migrées à reprendre. **Non recommandé.**
2. **Migration corrective ultérieure** (M3 ou M4) : toutes les bases convergent vers le même schéma. Points d'attention :
   - **Pré-contrôle obligatoire** : exécuter M2 avant. S'il remonte des lignes, la migration M4 échouerait à la copie (nouveau CHECK) et, la migration étant transactionnelle, la base resterait au rang précédent : l'application ne démarrerait plus tant que la donnée n'est pas corrigée.
   - **Lignes fautives déjà stockées** : M3 ne les corrige pas ; leur réparation par `UPDATE` est bloquée par les triggers d'immuabilité (numéros, codes, snapshots gelés, `no_update`). Il faudrait, dans la migration, une étape explicite et décidée (suppression/recréation temporaire du trigger, ou correction pendant la copie de M4). Toute modification d'un numéro ou d'un document émis est une **décision métier**, pas technique.
   - **Reconstruction (M4)** : protocole 005a (`foreign_keys=OFF` hors transaction, reconstruction, `sqlite_sequence`, triggers et index recréés) ; la déclaration « migration de reconstruction » au runner doit exister (conventions) ; test de non-régression de chaque table reconstruite.
   - **Rang et numérotation** : la chaîne est « ordonnée et figée » ; une migration corrective occupe un rang. Elle doit être placée **avant ou après la tranche 010** par décision explicite (non commencée ici).
   - **Tests** : les suites 001–008 restent inchangées ; les tests de 009 (groupe J : « 009 n'altère ni le schéma ni les gardes de 001 à 008 ») fixent le périmètre de 009 et ne s'appliquent pas à une migration ultérieure, qui aura sa propre suite.
3. **Aucune donnée valide n'est modifiée** par M2, M3 ou M4 ; seule une valeur contenant un NUL est concernée.
4. **Performance** : négligeable (une fonction scalaire par écriture).

---

## 5. Séquencement proposé (à arbitrer)

| Vague | Contenu | Schéma modifié ? | Colonnes |
|---|---|:--:|---|
| **V0** | M2 (détection, annexe) intégrée aux diagnostics ; M1 (validation de service) à demander côté application | non | 90 |
| **V1** | M3 ou M4 sur les colonnes **P1** | oui (nouvelle migration) | 6 numéros/codes + 10 décimaux DL = 16 colonnes (tables `devis`, `bons_commande`, `factures`, `depenses`, `clients`, `fournisseurs`, `devis_lignes`, `bc_lignes`, `facture_lignes`, `prestations`) |
| **V2** | M3 ou M4 sur les colonnes **P2** | oui | 16 décimaux D2 + 17 JSON |
| **V3** | M5 (acceptation documentée) ou M3 groupé pour les **P3** | selon décision | 41 horodatages |

Si une reconstruction groupée (M4) est de toute façon décidée, regrouper V1 à V3 en une seule migration évite d'ouvrir plusieurs fois les mêmes tables.

---

## 6. Points à arbitrer

1. **P-1** — Y a-t-il des bases de production (ou de recette) ayant déjà appliqué 001–008 ? (conditionne §4)
2. **P-2** — Mode retenu pour P1 : M3 (triggers) ou M4 (reconstruction) ? Et pour P2/P3 ?
3. **P-3** — Les services écrivent-ils `created_at`/`updated_at` explicitement, ou toujours via `DEFAULT` ? (conditionne l'exposition de 32 colonnes)
4. **P-4** — Position de la migration corrective par rapport à la tranche 010.
5. **P-5** — Que faire d'une ligne fautive déjà stockée dans une table immuable (décision métier) ?
6. **P-6** — Faut-il documenter la limite par M5 pour les colonnes non traitées (modèle de cadrage 007 §6) ?

---

## Annexe — requête de détection M2 (lecture seule ; 90 colonnes)

Vérifiée : 0 ligne sur une base saine ; détecte les lignes fautives (3 sur 3 dans l'essai). Résultat attendu sur une base conforme : aucune ligne.

```sql
-- Détection (lecture seule) : lignes dont une colonne vulnérable contient un octet NUL. Résultat attendu : toutes les lignes à 0.
SELECT * FROM (
  SELECT 'bc_devis.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM bc_devis WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'bc_ligne_garanties.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM bc_ligne_garanties WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'bc_lignes.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM bc_lignes WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'bc_lignes.prix_unitaire_ht' AS colonne, COUNT(*) AS lignes_avec_nul FROM bc_lignes WHERE instr(CAST(prix_unitaire_ht AS BLOB), x'00') > 0
  UNION ALL SELECT 'bc_lignes.quantite' AS colonne, COUNT(*) AS lignes_avec_nul FROM bc_lignes WHERE instr(CAST(quantite AS BLOB), x'00') > 0
  UNION ALL SELECT 'bc_lignes.remise_valeur' AS colonne, COUNT(*) AS lignes_avec_nul FROM bc_lignes WHERE instr(CAST(remise_valeur AS BLOB), x'00') > 0
  UNION ALL SELECT 'bc_lignes.total_ht' AS colonne, COUNT(*) AS lignes_avec_nul FROM bc_lignes WHERE instr(CAST(total_ht AS BLOB), x'00') > 0
  UNION ALL SELECT 'bc_lignes.updated_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM bc_lignes WHERE instr(CAST(updated_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'bons_commande.avancement' AS colonne, COUNT(*) AS lignes_avec_nul FROM bons_commande WHERE instr(CAST(avancement AS BLOB), x'00') > 0
  UNION ALL SELECT 'bons_commande.cancelled_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM bons_commande WHERE instr(CAST(cancelled_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'bons_commande.chantier_snapshot' AS colonne, COUNT(*) AS lignes_avec_nul FROM bons_commande WHERE instr(CAST(chantier_snapshot AS BLOB), x'00') > 0
  UNION ALL SELECT 'bons_commande.client_snapshot' AS colonne, COUNT(*) AS lignes_avec_nul FROM bons_commande WHERE instr(CAST(client_snapshot AS BLOB), x'00') > 0
  UNION ALL SELECT 'bons_commande.completed_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM bons_commande WHERE instr(CAST(completed_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'bons_commande.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM bons_commande WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'bons_commande.entreprise_snapshot' AS colonne, COUNT(*) AS lignes_avec_nul FROM bons_commande WHERE instr(CAST(entreprise_snapshot AS BLOB), x'00') > 0
  UNION ALL SELECT 'bons_commande.frozen_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM bons_commande WHERE instr(CAST(frozen_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'bons_commande.legacy_data' AS colonne, COUNT(*) AS lignes_avec_nul FROM bons_commande WHERE instr(CAST(legacy_data AS BLOB), x'00') > 0
  UNION ALL SELECT 'bons_commande.montant_contractuel_ht' AS colonne, COUNT(*) AS lignes_avec_nul FROM bons_commande WHERE instr(CAST(montant_contractuel_ht AS BLOB), x'00') > 0
  UNION ALL SELECT 'bons_commande.montant_deja_facture_ht' AS colonne, COUNT(*) AS lignes_avec_nul FROM bons_commande WHERE instr(CAST(montant_deja_facture_ht AS BLOB), x'00') > 0
  UNION ALL SELECT 'bons_commande.numero' AS colonne, COUNT(*) AS lignes_avec_nul FROM bons_commande WHERE instr(CAST(numero AS BLOB), x'00') > 0
  UNION ALL SELECT 'bons_commande.updated_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM bons_commande WHERE instr(CAST(updated_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'categories_depenses.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM categories_depenses WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'categories_depenses.updated_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM categories_depenses WHERE instr(CAST(updated_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'categories_prestations.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM categories_prestations WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'categories_prestations.updated_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM categories_prestations WHERE instr(CAST(updated_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'clients.code' AS colonne, COUNT(*) AS lignes_avec_nul FROM clients WHERE instr(CAST(code AS BLOB), x'00') > 0
  UNION ALL SELECT 'clients.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM clients WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'clients.legacy_data' AS colonne, COUNT(*) AS lignes_avec_nul FROM clients WHERE instr(CAST(legacy_data AS BLOB), x'00') > 0
  UNION ALL SELECT 'clients.updated_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM clients WHERE instr(CAST(updated_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'depenses.cancelled_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM depenses WHERE instr(CAST(cancelled_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'depenses.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM depenses WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'depenses.montant' AS colonne, COUNT(*) AS lignes_avec_nul FROM depenses WHERE instr(CAST(montant AS BLOB), x'00') > 0
  UNION ALL SELECT 'depenses.numero' AS colonne, COUNT(*) AS lignes_avec_nul FROM depenses WHERE instr(CAST(numero AS BLOB), x'00') > 0
  UNION ALL SELECT 'depenses.updated_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM depenses WHERE instr(CAST(updated_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis.acompte_valeur' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis WHERE instr(CAST(acompte_valeur AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis.cancelled_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis WHERE instr(CAST(cancelled_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis.chantier_snapshot' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis WHERE instr(CAST(chantier_snapshot AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis.client_snapshot' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis WHERE instr(CAST(client_snapshot AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis.entreprise_snapshot' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis WHERE instr(CAST(entreprise_snapshot AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis.frozen_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis WHERE instr(CAST(frozen_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis.legacy_data' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis WHERE instr(CAST(legacy_data AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis.numero' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis WHERE instr(CAST(numero AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis.remise_valeur' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis WHERE instr(CAST(remise_valeur AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis.total_ht' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis WHERE instr(CAST(total_ht AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis.updated_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis WHERE instr(CAST(updated_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis_ligne_garanties.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis_ligne_garanties WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis_lignes.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis_lignes WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis_lignes.prix_unitaire_ht' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis_lignes WHERE instr(CAST(prix_unitaire_ht AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis_lignes.quantite' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis_lignes WHERE instr(CAST(quantite AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis_lignes.remise_valeur' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis_lignes WHERE instr(CAST(remise_valeur AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis_lignes.total_ht' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis_lignes WHERE instr(CAST(total_ht AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis_lignes.updated_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis_lignes WHERE instr(CAST(updated_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis_revisions.contenu' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis_revisions WHERE instr(CAST(contenu AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis_revisions.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis_revisions WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis_revisions.total_ht' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis_revisions WHERE instr(CAST(total_ht AS BLOB), x'00') > 0
  UNION ALL SELECT 'devis_revisions.valide_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM devis_revisions WHERE instr(CAST(valide_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'facture_lignes.avancement_cumule_pct' AS colonne, COUNT(*) AS lignes_avec_nul FROM facture_lignes WHERE instr(CAST(avancement_cumule_pct AS BLOB), x'00') > 0
  UNION ALL SELECT 'facture_lignes.avancement_precedent_pct' AS colonne, COUNT(*) AS lignes_avec_nul FROM facture_lignes WHERE instr(CAST(avancement_precedent_pct AS BLOB), x'00') > 0
  UNION ALL SELECT 'facture_lignes.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM facture_lignes WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'facture_lignes.montant_ht' AS colonne, COUNT(*) AS lignes_avec_nul FROM facture_lignes WHERE instr(CAST(montant_ht AS BLOB), x'00') > 0
  UNION ALL SELECT 'facture_lignes.prix_unitaire_ht' AS colonne, COUNT(*) AS lignes_avec_nul FROM facture_lignes WHERE instr(CAST(prix_unitaire_ht AS BLOB), x'00') > 0
  UNION ALL SELECT 'facture_lignes.quantite' AS colonne, COUNT(*) AS lignes_avec_nul FROM facture_lignes WHERE instr(CAST(quantite AS BLOB), x'00') > 0
  UNION ALL SELECT 'facture_lignes.remise_valeur' AS colonne, COUNT(*) AS lignes_avec_nul FROM facture_lignes WHERE instr(CAST(remise_valeur AS BLOB), x'00') > 0
  UNION ALL SELECT 'factures.chantier_snapshot' AS colonne, COUNT(*) AS lignes_avec_nul FROM factures WHERE instr(CAST(chantier_snapshot AS BLOB), x'00') > 0
  UNION ALL SELECT 'factures.client_snapshot' AS colonne, COUNT(*) AS lignes_avec_nul FROM factures WHERE instr(CAST(client_snapshot AS BLOB), x'00') > 0
  UNION ALL SELECT 'factures.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM factures WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'factures.entreprise_snapshot' AS colonne, COUNT(*) AS lignes_avec_nul FROM factures WHERE instr(CAST(entreprise_snapshot AS BLOB), x'00') > 0
  UNION ALL SELECT 'factures.legacy_data' AS colonne, COUNT(*) AS lignes_avec_nul FROM factures WHERE instr(CAST(legacy_data AS BLOB), x'00') > 0
  UNION ALL SELECT 'factures.montant_deja_facture_ht' AS colonne, COUNT(*) AS lignes_avec_nul FROM factures WHERE instr(CAST(montant_deja_facture_ht AS BLOB), x'00') > 0
  UNION ALL SELECT 'factures.numero' AS colonne, COUNT(*) AS lignes_avec_nul FROM factures WHERE instr(CAST(numero AS BLOB), x'00') > 0
  UNION ALL SELECT 'factures.total_ht' AS colonne, COUNT(*) AS lignes_avec_nul FROM factures WHERE instr(CAST(total_ht AS BLOB), x'00') > 0
  UNION ALL SELECT 'fournisseurs.code' AS colonne, COUNT(*) AS lignes_avec_nul FROM fournisseurs WHERE instr(CAST(code AS BLOB), x'00') > 0
  UNION ALL SELECT 'fournisseurs.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM fournisseurs WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'fournisseurs.updated_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM fournisseurs WHERE instr(CAST(updated_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'garanties.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM garanties WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'import_anomalies.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM import_anomalies WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'import_anomalies.donnees' AS colonne, COUNT(*) AS lignes_avec_nul FROM import_anomalies WHERE instr(CAST(donnees AS BLOB), x'00') > 0
  UNION ALL SELECT 'import_anomalies.traite_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM import_anomalies WHERE instr(CAST(traite_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'numerotation_sequences.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM numerotation_sequences WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'numerotation_sequences.updated_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM numerotation_sequences WHERE instr(CAST(updated_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'prestation_garanties.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM prestation_garanties WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'prestations.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM prestations WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'prestations.legacy_data' AS colonne, COUNT(*) AS lignes_avec_nul FROM prestations WHERE instr(CAST(legacy_data AS BLOB), x'00') > 0
  UNION ALL SELECT 'prestations.prix_unitaire_ht' AS colonne, COUNT(*) AS lignes_avec_nul FROM prestations WHERE instr(CAST(prix_unitaire_ht AS BLOB), x'00') > 0
  UNION ALL SELECT 'prestations.updated_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM prestations WHERE instr(CAST(updated_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'reglements.cancelled_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM reglements WHERE instr(CAST(cancelled_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'reglements.created_at' AS colonne, COUNT(*) AS lignes_avec_nul FROM reglements WHERE instr(CAST(created_at AS BLOB), x'00') > 0
  UNION ALL SELECT 'reglements.legacy_data' AS colonne, COUNT(*) AS lignes_avec_nul FROM reglements WHERE instr(CAST(legacy_data AS BLOB), x'00') > 0
  UNION ALL SELECT 'reglements.montant' AS colonne, COUNT(*) AS lignes_avec_nul FROM reglements WHERE instr(CAST(montant AS BLOB), x'00') > 0
) WHERE lignes_avec_nul > 0;
```
