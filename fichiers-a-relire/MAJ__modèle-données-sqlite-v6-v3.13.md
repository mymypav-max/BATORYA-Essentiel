# BATORYA Essentiel — Modèle de données SQLite V6 — V3.13

**Statut** : révision **V3.13 en relecture, non validée** (2026-10-03) ; la V3.12 reste la dernière version validée. Prérequis aux migrations SQL (suivi des migrations : §17.1)
**Base** : V3.4 + audit V3.4 + arbitrages de Rémy Pavy du 2026-09-29 ; révisions V3.6 (migration V2 externalisée) et V3.7 (high-water) du 2026-09-30 ; révisions V3.8 (`machine.db`), V3.9 (DDL de la première tranche métier), V3.10 (fournisseurs et règle de rattachement tardif des dépenses aux BC), V3.11 (DDL Devis, rattachement client et contrôles de dates) et V3.12 (conception de la tranche Bons de commande, réglages de connexion SQLite) du 2026-10-01 ; **révision V3.13 : intégration des arbitrages métier Q1–Q27 et A–D du 2026-10-03** (errata E-10 à E-20)
**Version courante** : V3.13 (en relecture). Elle remplacera `modèle-données-sqlite-v6-v3.12.md` à sa validation ; la V3.12 décrit l'état des migrations 001 à 004 déjà intégrées et reste la référence de ce qui est **appliqué**. Les mentions V3.4 à V3.12 ci-dessous désignent l'historique du document.
**Pièces obligatoires du modèle** : ce document + `invariants.md` + `cdc-errata-v6.md`

**Marquage des énoncés (V3.13)** — trois natures qui ne se confondent jamais :
- **[VALIDÉ]** : règle métier décidée par Rémy (INV-179 à INV-196, errata E-10 à E-20, décisions D-40 à D-54 ; tranche Dépenses : INV-197 à INV-201, cadrage 005) ;
- **[DÉDUIT]** : contrainte technique déduite d'une règle validée ;
- **[PT-xx]** : **proposition technique** (catalogue au §19) pour implémenter une règle validée — **non validée** tant qu'elle n'est pas explicitement acceptée ; **[À CONCEVOIR]** : question technique ouverte. Une proposition n'est jamais une règle métier.

Les migrations 001 à 004 sont **appliquées et immuables** : elles décrivent l'état du 2026-10-02. Lorsqu'elles contredisent une décision validée, la décision prévaut et l'écart est listé au **§4.19** ; la correction est portée par des migrations ultérieures (PT-20), jamais par une réécriture de 001–004. Le dépôt existant est une matière d'audit, non la vérité métier.

---

## 0. Règle anti-régression (à lire en premier)

Le risque principal des versions V3.1 à V3.4 a été la **perte de règles déjà validées** à chaque réécriture.
À partir de la V3.5 :

1. Toute règle de ce document porte un identifiant `INV-xx` défini dans `invariants.md`.
2. Toute nouvelle version du modèle est **contrôlée contre `invariants.md`** avant validation : aucun INV ne disparaît sans décision écrite (« INV-xx retiré, motif, date »).
3. Toute règle nouvelle reçoit un INV, une garde (SQL / trigger / service / contrôle) et un test du même nom.
4. Le DDL est la source exécutable ; ce document reste la source des décisions.

### Historique des versions

| Version | Apport principal |
|---|---|
| V3.3 | Séparation `machine.db`, garanties snapshotées, `UNIQUE(devis_id)`, errata |
| V3.4 | Gel, facturation nette, formules d'avoir, restauration en 9 étapes |
| **V3.5** | Terminé redéfini, garde-fous financiers rétablis, colonnes exhaustives, `sequence_high_water`, registre INV (le « mode migration par `origine` » de la première rédaction est supprimé en V3.6) |
| **V3.6** (2026-09-30) | **Migration V2 externalisée** : V2 JSON → convertisseur externe → `import-v6.json` → import standard V6. Suppression du mode migration, de `migration_rapports`, de `migration_quarantaine` et de `migration_id` ; une seule exemption (format du `numero` historique) ; compteurs transmis par le fichier (D-21 à D-26, E-09) |
| **V3.7** (2026-09-30) | **Numérotation** : `max_attribue` ne diminue jamais, le trou éventuel est accepté et journalisé (§11.4, INV-25, D-27, T-24) ; D-22, D-23, D-24 validées ; intitulés et statuts alignés sur la V3.7 ; audit fonctionnel et modèle métier alignés sur ce document |
| **V3.8** (2026-10-01) | **`machine.db`** (§5) : compte local obligatoire au premier démarrage (`utilisateur_local.identifiant` UNIQUE NOT NULL, `mot_de_passe_hash` NOT NULL) ; `preferences_sauvegarde.frequence_jours` remplacée par `frequence_minutes` (défaut 30) avec sauvegarde automatique et à la fermeture activées par défaut ; singletons créés par le service d'initialisation (`INSERT OR IGNORE`), jamais par le DDL ; aucun trigger dans `machine.db` (INV-25 et INV-106 restent des gardes de service) ; test T-25 ; D-28 à D-30, INV-171, INV-172 |
| **V3.9** (2026-10-01) | **DDL de la première tranche métier** (`src-tauri/migrations/metier/001_initial.sql`) : `import_anomalies`, `numerotation_sequences`, listes de référence, `clients`, catalogue (`prestations`, `prestation_garanties`) ; TR-90 et TR-95 ; précisions de DDL du §4.17 et clarifications de rédaction (§2.1, §2.5, §4.1, §9, §17) sans règle ni décision nouvelle ; suivi des migrations (§17.1) ; test T-26 |
| **V3.10** (2026-10-01) | **Fournisseurs et dépenses — cadrage métier** : fournisseurs dans la tranche suivante ; fournisseur archivé non sélectionnable pour une nouvelle dépense ; BC à 100 % conservant une fenêtre normale de 30 jours pour les nouvelles dépenses, puis rattachement tardif possible après confirmation simple ; décision D-31 et invariant INV-103 |
| **V3.11** (2026-10-01) | **Devis — DDL de la tranche T-28** : `devis`, `devis_lignes`, `devis_ligne_garanties` ; rattachement exceptionnel d'un client `a_rattacher` sur devis refusé/annulé ou gelé ; suppression physique permise tant qu'aucun BC n'existe ; contrôle des dates réelles renforcé avec `date(x) IS x` ; test T-28 |
| **V3.12** (2026-10-01) | **Bons de commande — conception de la tranche (migration 004) et réglages SQLite** : ordre des tranches Devis → BC → Dépenses → Facturation → Règlements → Garanties → PV → Planification (D-34) ; BC annulé terminal et jamais supprimé physiquement, garanti en base (TR-19, `bc_lignes.bc_id` en `RESTRICT`, D-35) ; cohérence devis ↔ BC : le service construit la cohérence, les triggers (TR-17, TR-18) ne portent que des invariants locaux, CK-13 est un contrôle diagnostique, y compris à la restauration (D-36) ; dates du BC : `date_creation` = jour d'enregistrement, `date_acceptation` héritée du devis (D-37) ; borne d'année 2001–2099 limitée aux dates de numérotation annuelle, au niveau du service (D-38) ; devis à 0.00 € non acceptable (INV-178, D-36) ; `PRAGMA recursive_triggers=ON` et `INSERT OR REPLACE` interdit par convention (D-39), complétés par le trigger `tr_96_numerotation_sequences_no_delete` posé par la migration 004 (aucun DELETE sur `numerotation_sequences`), tests 001–003 renforcés (§17.1) ; `UNIQUE(devis_ligne_id)`, état de naissance du BC, caches écrits en un seul UPDATE ; import d'un BC annulé et aucune garantie de ligne importée ; motifs GLOB explicites. Corrections de rédaction : T-27 et T-28 du §13.3, 11 triggers de `003`, « TR-01 bis » retiré des triggers (règle de service), garanties de ligne de devis à l'import, références V3.10 ; test T-29 |
| **V3.13** (2026-10-03, **en relecture**) | **Arbitrages métier Q1–Q27 et A–D** (errata E-10 à E-20 ; INV-179 à INV-196 ; D-40 à D-54) : **un numéro n'est jamais attribué deux fois** (un trou après crash ou rollback est acceptable, jamais récupéré ; analyse du mécanisme `numerotation_sequences` + `machine.db` révisée au §11.4 ; mécanisme PT-1 **tranché le 2026-10-03** : réservation committée avant la création de l'objet) ; devis `brouillon` sans numéro, devis `en_attente` numéroté **modifiable** par **révisions** (E-20, INV-196 ; stockage PT-21 « archive JSON raffinée » validé sur le principe), devis accepté verrouillé, devis refusé verrouillé et rouvrable ; clients et fournisseurs sans statut (conservation permanente, `a_rattacher` supprimé) ; ON DELETE examiné relation par relation ; BC regroupant plusieurs devis (lien devis ↔ BC, PT-6) ; BC annulé sans cascade vers les devis ; fin de l'annulation de facture, correction par avoir (PT-9) ; situation globale au BC en pourcentage ou en montant ; couche d'exécution et remise globale au prorata (principes validés, schéma **À CONCEVOIR**) ; dépenses annulables ; historique métier ; **propositions techniques PT-1 à PT-21 (§19) : PT-1 tranché, PT-21 validé sur le principe, les autres non validées** ; migrations 001–004 inchangées, écarts listés au §4.19 ; **versionnement des migrations (2026-10-04, D-55)** : `user_version` = rang dans une chaîne ordonnée figée, tranches `NNN_<objet>` et correctives `NNNx_<objet>` (M-A/M-B = `005a`/`005b`, après 005 et avant 006), protocole de reconstruction de table (conventions §5) ; **alignements Dépenses (2026-10-04, cadrage 005)** : montant de la dépense = montant HT strictement positif, `date_depense` définie, règle des 30 jours limitée aux BC non annulés, principe d'exclusion des dépenses annulées reconnu (INV-200 ; PT-14 limité aux formules détaillées), INV-197 à INV-201 |

---

## 1. Principes généraux [INV-01 à INV-08]

- SQLite local = source de vérité. Les PDF, exports et sauvegardes en sont dérivés.
- Flux : `UI React → services applicatifs → domaine → repositories → SQLite`. L'UI n'exécute jamais de SQL.
- **Accès SQLite exclusivement côté Rust (Tauri)**. Pas de SQLite WASM/OPFS : WAL, Backup API et `VACUUM INTO` y sont indisponibles.
- Deux bases : **base métier** (sauvegardée/restaurée) et **`machine.db`** (jamais sauvegardée, jamais restaurée).
- Aucune donnée métier n'est envoyée au service distant (licence, mises à jour, référentiels uniquement).
- Toute opération métier multi-tables est **une seule transaction** ; une opération partielle est interdite.
- SQLite ≥ 3.37 requis (tables `STRICT`, `RETURNING`). **Toutes les tables sont `STRICT`.**
- Réglages de connexion, à chaque ouverture : `foreign_keys=ON`, `journal_mode=WAL`, `synchronous=FULL`, `busy_timeout` défini, **`recursive_triggers=ON`**. [INV-07, D-39]
  - `recursive_triggers=ON` est obligatoire : sans lui, `INSERT OR REPLACE` supprime la ligne existante **sans déclencher** ses triggers `BEFORE DELETE` (vérifié), ce qui contourne les gardes de non-suppression et d'immutabilité. Le réglage n'a d'effet que sur la base métier (`machine.db` n'a aucun trigger, §5), mais il est posé à l'identique à chaque ouverture.
  - `INSERT OR REPLACE` et `REPLACE` sont **interdits par convention** (conventions techniques §9) : on utilise `INSERT`, `UPDATE` ou un UPSERT explicitement maîtrisé (`ON CONFLICT … DO UPDATE`, `INSERT OR IGNORE` lorsque l'idempotence est voulue). Raison : préserver les garanties apportées par les triggers et éviter toute suppression implicite.
  - L'interdiction est une **convention technique** : elle n'est pas imposée mécaniquement (aucun contrôle du mot `REPLACE`, la fonction SQL `REPLACE(x, …)` des motifs de calcul restant évidemment permise) ; les tests vérifient le **comportement de protection** : avec `recursive_triggers=ON`, un `INSERT OR REPLACE` est refusé par les triggers `BEFORE DELETE` applicables (TR-90, TR-11 du devis, TR-19 du BC).
  - **Protection de `numerotation_sequences`** [INV-22] : un REPLACE ne déclenche pas les triggers `UPDATE` (vérifié). `tr_95_numerotation_sequences_no_decrease` protège donc la non-diminution de `dernier_numero` lors d'un `UPDATE` seulement. `001_initial.sql` étant une migration déjà appliquée, donc immuable, la migration 004 ajoute le trigger correctif `tr_96_numerotation_sequences_no_delete` (TR-96), qui refuse tout `DELETE` sur `numerotation_sequences`. Il protège un DELETE direct et, avec `recursive_triggers=ON`, la suppression implicite que fait `INSERT OR REPLACE` avant de réinsérer une valeur plus faible (sans `recursive_triggers=ON`, le REPLACE contourne TR-96 : le réglage reste obligatoire). L'upsert de l'attribution `INSERT … ON CONFLICT … DO UPDATE` reste autorisé. Tant que la migration 004 n'est pas appliquée, cette protection n'existe pas en base : seules la convention D-39 et le high-water de `machine.db` (INV-25, aucun numéro réutilisé) jouent.
- Migrations de schéma : fichiers numérotés (`001_initial.sql`…) sous `src-tauri/migrations/machine/` et `src-tauri/migrations/metier/` (conventions techniques §5), chacun dans une transaction ; `PRAGMA user_version` = **rang** de la dernière migration appliquée dans la chaîne ordonnée (conventions techniques §5, « Chaîne ordonnée, rang et `user_version` »), écrit **dans la même transaction que la migration, avant son `COMMIT`** (décisions V-1 à V-5 du 2026-10-04, D-55). `machine.db` a ses propres migrations, sa propre chaîne et son propre `user_version`.
- **Migrations appliquées immuables** : une migration déjà appliquée n'est jamais réécrite (conventions techniques §5) ; les corrections structurelles décidées en V3.13 (§4.19) seront portées par des migrations **ultérieures** (PT-20), des **correctives** `NNNx_<objet>.sql` rattachées à la dernière tranche exécutée avant elles (D-55) ; la chaîne est **figée en append-only** après livraison (aucun renommage, aucune suppression, aucun réordonnancement ; ajout en fin de liste seulement). [INV-08]
- Deux mécanismes distincts : **migration de schéma** (V6.n → V6.n+1) et **import de données** (fichier `import-v6.json` produit par un convertisseur externe à partir de l'unique sauvegarde V2 ; V6 ne lit jamais le format V2 ; la V5 n'a jamais été distribuée). Voir §10.

---

## 2. Conventions techniques

### 2.1 Identifiants et clés

- `id INTEGER PRIMARY KEY AUTOINCREMENT` sur toutes les tables référencées (jamais de réutilisation d'id). [INV-04]
- Le numéro métier (`numero`, `code`) n'est jamais une clé étrangère.
- FK : `ON DELETE RESTRICT` par défaut ; **chaque `ON DELETE` est examiné relation par relation** (Q12, D-44, INV-05) : `CASCADE` uniquement pour des données strictement dépendantes, sans valeur historique autonome, et seulement tant que le parent est supprimable. **État des migrations 001–004 (immuables)** : `CASCADE` sur `devis_lignes.devis_id`, `devis_ligne_garanties.ligne_id`, `bc_ligne_garanties.ligne_id` et `prestation_garanties.prestation_id` ; `bc_lignes.bc_id` en `RESTRICT`. **Examen V3.13** : voir §4.19 et PT-5 (`devis_lignes` et `devis_ligne_garanties` : CASCADE acceptable seulement pour la suppression d'un **brouillon**, avec une garde de suppression ; `bc_ligne_garanties` : `RESTRICT` proposé ; `prestation_garanties` : CASCADE conservé). Aucune clause `ON UPDATE`. [INV-05]
- Les liens polymorphes `historique.entite_id` et `documents.entite_id` (discriminant `type_entite`) et `urssaf_corrections.source_id` (discriminant `source_type`) n'ont pas de FK : leur discriminant est une énumération fermée (§2.5) et l'existence est vérifiée par le service et par les requêtes de contrôle. **Exception** : `import_anomalies.entite_id` est aussi un lien polymorphe sans FK (CK-09), mais son `type_entite` n'est pas une énumération fermée du modèle (§4.17, point 7).

### 2.2 Dates et timestamps [INV-10]

| Notation | Type | Format | Contrôle |
|---|---|---|---|
| **D** | TEXT | `YYYY-MM-DD` | `GLOB` + `date(x) IS x` (date réelle ; `date(x)=x` est insuffisant car un CHECK acceptant NULL laisse passer certaines dates invalides) |
| **TS** | TEXT | `YYYY-MM-DDTHH:MM:SS.SSSZ` (UTC) | `GLOB` |
| **DL_LOCAL** | TEXT | `YYYY-MM-DD` ou `YYYY-MM-DDTHH:MM` (heure locale, planning uniquement) | `GLOB` |

Les colonnes `*_at` sont des TS. Les colonnes `date_*` sont des D. Une date métier n'est jamais déduite d'un TS.
Le « jour courant » (retards, garanties, `date_creation` d'un devis ou d'un BC créé dans V6) est la date **locale** de l'entreprise.

- **Borne d'année de numérotation (2001–2099)** : le contrôle SQL des dates reste `GLOB` + `date(x) IS x` (forme et existence calendaire) et **ne porte aucune borne d'année**. Une borne **2001–2099** s'applique **uniquement**, au niveau du **service** (jamais un CHECK), aux dates dont l'année est exploitée par les conventions de numérotation annuelle `yy` : création du devis, enregistrement du BC, émission de la facture, réception du PV, date de la dépense (modèle métier §2.2). Motif : `yy = 00` est impossible dans `numerotation_sequences` (`annee = 0` est réservé à CLI/FOU, §4.2), donc les années 2000 et 2100 ne sont pas supportées pour les objets numérotés par année. Les autres dates (validité, acceptation, refus, échéances, dates historiques ou importées, dates de planning…) ne subissent aucune borne d'année autre que la validité calendaire. [INV-177, D-38]
- **Motifs `GLOB`** : `GLOB` de SQLite n'a **pas** de quantificateur `{n}` (`'BCD-[0-9]{5}-[0-9]{2}'` ne reconnaît pas `BCD-00001-26`). Tout format est écrit explicitement, par exemple `'BCD-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'`.

### 2.3 Familles décimales [INV-11, INV-12, INV-14]

Aucun `REAL` pour un montant. Tout est TEXT canonique, contrôlé par `CHECK`.

| Famille | Contenu | Règle | Signe |
|---|---|---|---|
| **D2** | montants finaux | exactement 2 décimales (`1250.50`, `0.00`) | ≥ 0 |
| **D2S** | montants signés | idem D2, préfixe `-` autorisé, `-0.00` interdit | signé |
| **DL** | précision libre : `quantite`, `prix_unitaire_ht`, remise « montant » de ligne, taux | sans zéro de fin (`10`, `3.333`, `0.5`) ; `0` autorisé seul | ≥ 0 |
| **P2** | pourcentages | 2 décimales, 0.00 à 100.00 | ≥ 0 |

Motifs de référence (le DDL les instancie) :

```
D2 : x GLOB '[0-9]*.[0-9][0-9]' AND x NOT GLOB '*[^0-9.]*' AND x NOT GLOB '*.*.*' AND x NOT GLOB '0[0-9]*'
DL : x <> '' AND x NOT GLOB '*[^0-9.]*' AND x NOT GLOB '*.*.*' AND x NOT GLOB '.*'
     AND x NOT GLOB '*.' AND x NOT GLOB '*.*0' AND x NOT GLOB '0[0-9]*'
P2 : D2 AND CAST(REPLACE(x,'.','') AS INTEGER) BETWEEN 0 AND 10000
```

**Arithmétique en SQL** : uniquement par conversion en centimes entiers, `CAST(REPLACE(x,'.','') AS INTEGER)`, valable pour D2 et D2S. Jamais `CAST … AS REAL` pour calculer, `SUM()` ou `ORDER BY` sur un TEXT décimal. Seule exception : comparaisons de **bornes** (taux DL entre 0 et 100). Les triggers financiers utilisent ces centimes.

Négatifs autorisés uniquement : `facture_lignes.montant_ht` (type `deduction`), `urssaf_periodes.ca_encaisse`, `urssaf_periodes.ecart`, `urssaf_details.base`, `urssaf_periode_encaissements.montant_retenu`.

### 2.4 Blocs de colonnes communs

- **BLOC-IMP** (traçabilité des données issues de `import-v6.json`, §10) : `origine TEXT NOT NULL DEFAULT 'v6' CHECK(origine IN ('v6','import'))`, `legacy_id TEXT NULL` (`ref` de l'objet dans le fichier), `legacy_data TEXT NULL CHECK(json_valid)` (données sources non représentables en colonnes, jamais interprétées par V6). Contrainte : `origine='v6'` ⇒ `legacy_id`, `legacy_data` (et `legacy_numero`) NULL. **BLOC-IMP+** ajoute `legacy_numero TEXT NULL` (ancien code ou numéro, seulement s'il diffère de `numero`) ; réservé à `clients` et `bons_commande`. Le bloc n'existe que sur les tables que le contrat d'import peut alimenter (clients, prestations, devis, bons_commande, factures, reglements, pv). `migration_id` n'existe plus. [INV-136]
- **BLOC-SNAP** : `client_snapshot`, `entreprise_snapshot`, `chantier_snapshot` (TEXT `json_valid`, NOT NULL) + `*_snapshot_version INTEGER NOT NULL` (version du **format** du JSON). [INV-30]
  - client : nom, prénom, adresse, cp/ville, tél, email.
  - entreprise : identité, forme juridique, nom commercial, adresse, tél, email, SIREN/SIRET, autres identifiants, IBAN/BIC **si affichés**, mention commerciale, conditions commerciales et particulières, délai de paiement, modes de règlement.
  - chantier : adresse, cp/ville.

### 2.5 Énumérations fermées

Toute liste ci-dessous est un `CHECK(x IN (...))`. Ajouter une valeur = migration de schéma.

| Domaine | Valeurs |
|---|---|
| `origine` | `v6`, `import` |
| statut client / fournisseur | **aucun** (E-12, INV-183) : les colonnes `statut` de `clients` et `fournisseurs` (001, 002) sont supprimées par migration (PT-3) |
| `type_prestation` | `fourniture`, `pose`, `fourniture_pose` |
| `unite` | `u`, `ens`, `ml`, `m2`, `m3` (D-13) |
| `remise_type` | `aucune`, `pourcentage`, `montant` |
| `acompte_type` | `aucun`, `pourcentage`, `montant` |
| `garantie_type` | `parfait_achevement`, `biennale`, `decennale` |
| statut devis | `brouillon`, `en_attente`, `accepte`, `refuse`, `annule` (ajout de `brouillon` : PT-2 ; transition `refuse → en_attente` : PT-17) |
| statut BC | `en_cours`, `termine`, `annule` |
| `factures.type` | `acompte`, `situation`, `solde`, `avoir` |
| `facture_lignes.type_ligne` | `prestation`, `synthese`, `deduction` |
| `reglements.type` | `encaissement`, `remboursement` |
| `reglements.mode` | `especes`, `cheque`, `virement`, `carte`, `autre` |
| `pv.type` | `reception_sans_reserves`, `reception_avec_reserves`, `levee_reserves` |
| `planning.type_evenement` | `intervention`, `travaux`, `rendez_vous_client`, `reunion`, `appel`, `administratif`, `conge`, `indisponibilite`, `autre` |
| `documents.type_entite` | `devis`, `facture`, `pv` |
| `documents.type_document` | `devis`, `acompte`, `situation`, `solde`, `avoir`, `pv` |
| `historique.type_entite` | `client`, `fournisseur`, `prestation`, `devis`, `bc`, `facture`, `reglement`, `depense`, `pv`, `garantie`, `planning_evenement`, `bc_note`, `urssaf_periode`, `urssaf_correction`, `document`, `import`, `restauration` |
| `historique.type_evenement` | **Liste V3.12** : `creation`, `modification`, `acceptation`, `refus`, `annulation`, `gel`, `emission`, `reglement`, `annulation_reglement`, `remboursement`, `avoir`, `passage_termine`, `retour_en_cours`, `declenchement_garantie`, `rattachement_client`, `declaration_urssaf`, `correction_urssaf`, `import`, `restauration`. **V3.13 (PT-15, à fixer par migration)** : ajouter `validation` (finalisation du devis), `reouverture`, `revision_demarree`, `revision_validee`, `revision_abandonnee` (PT-21), `rattachement_devis`, les événements d'exécution significatifs et, selon PT-14, l'annulation de dépense ; `gel` et `rattachement_client` n'ont plus d'objet dans le cycle V3.13 |
| `historique.acteur` | `utilisateur`, `systeme`, `import` |
| statut URSSAF période | `a_declarer`, `declaree`, `a_verifier` |
| `urssaf_profil.periodicite` | `mensuelle`, `trimestrielle` |
| `urssaf_periode_encaissements.traitement` | `retenu`, `exclu` |
| `urssaf_corrections.champ` | `ca_encaisse`, `cotisations`, `cfp`, `montant_declare` |
| `urssaf_corrections.type_correction` | `ecart_detecte`, `resolution` |
| `urssaf_corrections.source_type` | `reglement`, `facture`, `referentiel`, `manuel` |
| `import_anomalies.categorie` | `a_verifier`, `non_importe` |
| `import_anomalies.statut` | `a_traiter`, `traite` |
| `type_objet` (séquences) | `CLI`, `FOU`, `DEV`, `BCD`, `ACP`, `FAC`, `AVO`, `PVR`, `DEP` |

Exception à la règle ci-dessus : `import_anomalies.type_entite` n'est pas une énumération fermée du modèle (texte non vide, valeurs définies par le contrat d'import ; §2.1, §4.17 point 7).

---

## 3. Formules de référence

Elles sont **la** définition. Tout écran, service ou trigger les réutilise ; aucune n'est réécrite ailleurs. [INV-13, INV-56 à INV-58, INV-73]

### 3.1 Calcul commercial [INV-13, INV-39]

- `remise_ligne` : type `montant` → valeur (montant total de la ligne, DL) ; type `pourcentage` → `quantite × prix × pct / 100` (exact).
- `montant_ligne = arrondi( quantite × prix_unitaire_ht − remise_ligne )` : **un seul arrondi par ligne**.
- `remise_globale` : `pourcentage` → `arrondi(Σ lignes × pct / 100)` ; `montant` → valeur (D2).
- `total_ht = Σ montant_ligne − remise_globale`. `montant_contractuel_ht` du BC = Σ des `total_ht` des devis qui lui sont rattachés (chaque devis garde sa propre remise globale et n'est jamais recalculé, INV-39, INV-192) ; pour un BC à un seul devis il est égal à `devis.total_ht` (INV-175).
- `acompte_prevu = arrondi(contractuel × pct / 100)` ou montant fixe ; toujours ≤ contractuel.
- **Arrondi HALF_UP** : demi vers le haut en valeur absolue (`0.125 → 0.13`, `-0.125 → -0.13`).
- Pourcentages saisis à 2 décimales.

### 3.2 Facturation

```
facturation_nette = Σ acomptes + Σ situations + Σ soldes − Σ avoirs
```
Les factures validées ne sont ni annulées ni supprimées (E-14, INV-185) : la V3.12 ne comptait que les factures « actives » (`cancelled_at IS NULL`) ; la notion d'« actif » éventuellement conservée (facture entièrement neutralisée par un avoir total) est une **proposition** (PT-9). Tous les avoirs réduisent la facturation nette. [INV-56]

**Situation** — [VALIDÉ] globale au BC, sur le périmètre contractuel actuellement accepté (Σ des devis rattachés) ; saisie en pourcentage **ou** en montant ; cohérence raisonnée en montants cumulés [INV-57, INV-190] :
```
mode pourcentage : situation.montant = arrondi(contractuel × cumul% / 100) − facturation_nette_avant_situation
situation.montant_deja_facture_ht   = facturation_nette_avant_situation
facturation_nette_apres_situation  ≤ contractuel
```
Sont conservés et figés après validation : le **mode de saisie**, la **valeur saisie**, l'**avancement** et le **montant HT facturé**. **Ce que désigne exactement la valeur saisie en mode montant (montant de la situation ou valeur cumulée réalisée) et les colonnes correspondantes : À CONCEVOIR (PT-11).**

**Solde** [INV-58] :
```
solde.total_ht = contractuel − facturation_nette_avant_solde     (≥ 0, 0.00 autorisé)
```

- Un **solde à 0.00** est autorisé (100 % déjà couvert par acomptes et situations). Il reste l'événement de clôture de facturation.
- Dès qu'un **solde est rédigé/validé** : nouvel acompte interdit, nouvelle situation interdite, et **un avoir partiel ne rouvre pas la facturation**. Un **avoir total** sur une facture permet de la remplacer par une nouvelle facture **du même type** avec un **nouveau numéro** (arbitrage B, INV-185) ; la facture initiale et son avoir restent conservés. Avant solde, un avoir sur acompte ou situation réduit la facturation nette et libère donc un montant refacturable (cas C-09).
- « 100 % facturé » = **présence d'un solde** : définition de calcul, utilisée pour l'avancement, `date_100_facture` et le suivi des garanties. **Elle n'intervient pas dans la règle de rattachement d'un devis à un BC** (INV-187), qui ne dépend que de la rédaction/validation du solde et de l'état du BC.
- Un acompte est **lié à son devis** (INV-189, PT-10) ; la facturation nette et le contractuel se consolident au niveau du BC.


### 3.3 Paiement [INV-72 à INV-75]

Pour une facture hors avoir de montant `M` :
```
encaisse    = Σ encaissements actifs
absorbe     = min( Σ avoirs actifs de la facture , max(0, M − encaisse) )
reste_du    = max(0, M − encaisse − absorbe)
credit      = Σ avoirs actifs − absorbe − Σ remboursements actifs      (calculé par facture d'origine, jamais < 0)
```
Le crédit se calcule **par facture d'origine** ; un remboursement peut viser n'importe quel avoir actif de cette origine.

Garde-fous :
- encaissement ≤ `reste_du` ; aucun encaissement sur un avoir ;
- remboursement ≤ `credit` ; remboursement uniquement sur un avoir actif ;
- Σ avoirs actifs ≤ `M` de l'origine ;
- annulation d'un encaissement refusée si elle rend `credit` < Σ remboursements actifs.

### 3.4 États dérivés (jamais persistés) [INV-60]

**Facture hors avoir**
- `etat_paiement` : `reglee` si `reste_du = 0` (même sans encaissement, ex. solde 0.00 ou couvert par avoirs) ; sinon `partiellement_reglee` si `encaisse > 0` ; sinon `en_attente`. L'état « annulée » n'existe plus (E-14) ; l'état d'une facture entièrement créditée est à définir (PT-9).
- `en_retard` (indicateur transversal) : `reste_du > 0` ∧ `date_echeance < aujourd'hui`. Une facture peut être `partiellement_reglee` **et** en retard.

**Avoir** : `credit_disponible` si `credit > 0` ; `solde` sinon. Jamais « en retard ». Un avoir n'est pas annulable (E-14).

**Garantie** : `a_surveiller` (avant échéance) / `echue` (après `date_fin_suivi`), dérivé, libellé toujours « Suivi interne BATORYA — date indicative ».

### 3.5 Fin du BC et rattachement tardif des dépenses [INV-42, INV-43, INV-103]

```
BC termine  ⇔  solde actif  ET  Σ reste_du des factures actives hors avoir = 0
```
(La notion d'« actif », fondée sur `cancelled_at` en V3.12, est à redéfinir : PT-9.)
- Un solde à 0.00 ne rend **pas** le BC terminé tant qu'une situation ou un acompte reste dû.
- L'avoir n'est pas un encaissement ; il intervient uniquement via `absorbe` (il réduit le reste dû). Un BC dont toute la dette est absorbée par des avoirs, sans autre dette, a `Σ reste_du = 0` (cas C-10).
- Passage `en_cours → termine` : `completed_at` = instant du recalcul. Passage `termine → en_cours` (annulation d'un règlement) : `completed_at = NULL`, événement d'historique `retour_en_cours`.
- `date_100_facture` = date d'émission du **premier solde actif**. Conservée lors d'un avoir partiel, d'un règlement, d'un remboursement. Son sort lorsque le solde est entièrement neutralisé par un avoir total puis remplacé par un nouveau solde est **À CONCEVOIR (PT-9)** (la V3.12 la remettait à `NULL` à l'annulation du solde, mécanisme supprimé par E-14). Elle **n'intervient pas** dans la règle de rattachement d'un devis (INV-187).
- `date_100_facture` (état courant du BC) ≠ `garanties.date_declenchement` (premier déclenchement historique). Les deux peuvent diverger volontairement.
- Pour un **BC non annulé**, à compter de `date_100_facture`, les dépenses peuvent être rattachées normalement au BC pendant **30 jours calendaires**. À l'issue de cette période, le BC est considéré comme **clôturé pour les nouvelles dépenses**.
- Une dépense peut néanmoins être rattachée après cette clôture : le service affiche une confirmation indiquant depuis combien de jours le BC est clôturé et demande « Êtes-vous sûr de vouloir ajouter cette dépense sur ce BC ? ». Une confirmation positive suffit ; il n'existe ni procédure de déblocage, ni autorisation supplémentaire, ni durée maximale de rattachement tardif.
- **Exception : BC annulé** [VALIDÉ — cadrage 005, INV-199]. La clôture à 30 jours et la confirmation ne s'appliquent pas à un BC annulé : aucun délai ni confirmation, quelle que soit `date_100_facture` ; une dépense peut y être créée ou lui être rattachée ultérieurement. Une modification de dépense qui conserve le même BC n'est pas un nouveau rattachement ; si le BC change, la règle s'évalue sur le BC cible, au moment de l'opération.
- La clôture des dépenses n'affecte ni le statut financier du BC, ni son historique, ni les dépenses déjà rattachées.
- Cette règle des 30 jours est une **règle de service** (INV-103) : elle n'est portée par aucun trigger SQL. Le BC n'expose que `date_100_facture`.

### 3.6 CA engagé [INV-45]

Pour les BC `en_cours` uniquement (BC annulés exclus) :
```
engage = max(0, (contractuel − Σ avoirs actifs) − (Σ encaissements actifs − Σ remboursements actifs))
CA engagé = Σ engage
```
CA encaissé et CA prévisionnel restent distincts et calculés (aucune colonne).

### 3.7 Ordre de recalcul du service financier [INV-164]
Après toute opération financière (facture, annulation, avoir, règlement, remboursement), le service recalcule **dans cet ordre**, dans la même transaction, sans jamais laisser un cache intermédiaire incohérent : les caches du BC sont **écrits en un seul `UPDATE`** (les CHECK de cohérence des caches du §4.7 seraient sinon violés entre deux écritures, par exemple à l'annulation d'un solde : `termine` ⇒ `date_100_facture`). L'ordre ci-dessous est l'ordre de **calcul** :
1. factures actives ; 2. facturation nette ; 3. montant restant ; 4. avancement ; 5. état 100 % ; 6. `date_100_facture` ; 7. reste dû du solde ; 8. état `termine` / `en_cours` ; 9. CA engagé.

### 3.8 Exécution et remise globale [INV-186, INV-191, INV-192] — principes validés, schéma À CONCEVOIR

**Règles métier validées (Q22, Q25, Q26, arbitrage D)**
- Le **contractuel** (devis accepté, lignes du BC) et l'**exécution** sont deux niveaux distincts : le devis accepté n'est jamais réécrit et le contenu contractuel du BC n'est jamais modifié rétroactivement (INV-186).
- BATORYA ne suit pas l'avancement physique automatiquement : l'utilisateur renseigne l'état réel connu.
- Une ligne peut être réalisée, partiellement réalisée par quantité, totalement abandonnée, ou avoir une quantité ou un prix unitaire d'exécution différents du contractuel lorsque le métier le justifie (exemple Q22 : 10 × 100 € → 7 réalisés à 100 € et 3 abandonnés, ou 10 réalisés à 80 €).
- L'exécution distingue au minimum **contractuel / exécuté / abandonné / restant / facturé / payé**.
- Partie abandonnée : plus à réaliser, plus à facturer, visible historiquement ; si elle avait été facturée, la correction passe par un avoir (exemple Q25 : 4 000 € contractuels, 2 000 € réalisés, 2 000 € abandonnés).
- Une augmentation de périmètre ou un travail supplémentaire passe par un nouveau devis accepté rattaché au BC (INV-187), jamais par la modification du devis (Q26).
- **Remise globale** : attachée au contrat initial, jamais recalculée sur le devis ; en cas d'exécution partielle, répartie **au prorata de la valeur exécutée/facturée**. Exemple : contractuel 10 000 €, remise 1 000 €, net 9 000 €, abandon 2 000 € → exécuté 8 000 €, remise affectée 800 €, net exécuté 7 200 € ; le devis reste à 10 000 € avec sa remise de 1 000 €. Règle métier BATORYA (pratique comparable aux logiciels BTP), non obligation légale.

**À CONCEVOIR / PROPOSITIONS (non validées — aucune n'est une règle métier)** : schéma de la couche d'exécution (modèles A, B, C, PT-12) ; bornes éventuelles sur prix ou quantités exécutés (par exemple « prix exécuté ≤ prix contractuel » : proposition à étudier, non retenue comme règle) ; formule exacte de la « base facturable » ; formule détaillée de répartition de la remise et tous ses cas particuliers (PT-13). **Aucune table, colonne ni contrainte d'exécution n'est créée** tant que ces points ne sont pas conçus et testés.

---

## 4. Base métier — tables

Notation : `PK` = clé primaire autoincrement ; `NN` = NOT NULL ; `UQ` = UNIQUE ; `FK→t` = clé étrangère RESTRICT sauf mention.
`created_at`/`updated_at` sont des TS NN. `+IMP` = BLOC-IMP, `+IMP+` = BLOC-IMP+ (§2.4).

### 4.1 Import (créée en premier)

**`import_anomalies`** : `id` PK · `type_entite` TEXT NN non vide, sans énumération fermée (§2.1, §4.17 point 7) · `entite_id` INTEGER NULL (objet V6 concerné, polymorphe, contrôlé par CK-09) · `ref_source` TEXT NN (`ref` dans `import-v6.json`) · `categorie` NN (`a_verifier` | `non_importe`) · `motif` NN · `donnees` TEXT NULL `json_valid` · `statut` NN défaut `a_traiter` · `created_at` · `traite_at` TS.
CHECK : `(statut='a_traiter') = (traite_at IS NULL)` ; `categorie='a_verifier'` ⇒ `entite_id` NN ; `categorie='non_importe'` ⇒ `entite_id` NULL ∧ `donnees` NN. Jamais supprimée ; seuls `statut` et `traite_at` évoluent (TR-90). [INV-130, INV-163, INV-165]
Tables **supprimées** de la V3.5 (D-22, V3.6) : `migration_rapports` (la trace de l'import est l'événement `import` de `historique`, §10.7) et `migration_quarantaine` (remplacée par `import_anomalies`, sans FK vers un lot d'import).

### 4.2 Séquences [INV-20 à INV-27]

**`numerotation_sequences`** : `id` PK · `type_objet` NN · `annee` INTEGER NN défaut 0 (année sur 2 chiffres, `0` pour CLI/FOU) · `dernier_numero` INTEGER NN défaut 0 · `derniere_date` D NULL (dernière date de numérotation, FAC/ACP/AVO) · `created_at` · `updated_at`.
`UQ(type_objet, annee)` · `CHECK((type_objet IN ('CLI','FOU')) = (annee=0))` · plafond : `dernier_numero BETWEEN 0 AND 99999` (documents), `0 AND 9999` (CLI/FOU). `dernier_numero` ne peut que croître (TR-95 lors d'un `UPDATE`) et la ligne de séquence ne se supprime jamais (TR-96, posé par la migration 004 ; avec `recursive_triggers=ON`, il couvre aussi le REPLACE, §1).
Attribution (dans la transaction de création du document) :
`INSERT … ON CONFLICT(type_objet, annee) DO UPDATE SET dernier_numero = dernier_numero + 1 RETURNING dernier_numero`. Dépassement du plafond = erreur métier explicite.
**Priorité absolue [VALIDÉ — INV-179, D-54]** : un numéro définitif n'est **jamais attribué deux fois**. Un numéro peut être consommé sans objet (crash ou rollback pendant la finalisation) ; ce trou est acceptable et **n'est jamais récupéré** : le compteur ne revient pas en arrière. Mécanisme **tranché le 2026-10-03 (PT-1)** : réservation du numéro committée **avant** la création de l'objet, avec double garde — compteur de `numerotation_sequences` (source primaire) et `sequence_high_water` de `machine.db` (détection d'une base métier régressée) — détaillé au §11.4.

### 4.3 Référentiels de listes

**`categories_prestations`** : `id` PK · `code` UQ NN · `libelle` NN · `actif` INTEGER NN (0/1) · `ordre` INTEGER · TS.
**`categories_depenses`** : idem. Contenu initial : liste de la décision D-18 (modifiable par l'utilisateur).
Les listes de référence et le catalogue par défaut sont livrés par le **jeu de données d'installation** (D-14, §10.1), jamais par une migration de schéma : le DDL ne crée aucune ligne (§4.17).

### 4.4 Clients et fournisseurs [INV-183, E-12, D-43]

**Règle métier validée** : un client ou un fournisseur est **créé, modifié, conservé**. Une fois son code attribué : il ne peut pas être supprimé, son code est immuable, il reste définitivement en base. Il n'existe **ni** archivage, désarchivage, statut actif/inactif, suppression logique, **`a_rattacher`**, ni mécanisme de réactivation (un client sans activité depuis des années reste simplement dans la base). L'interface peut filtrer et rechercher ; ce n'est pas un état persistant.

**`clients`** (cible V3.13) : `id` PK · `code` UQ NN · `nom` NN · `prenom` · `adresse` · `cpville` · `tel` · `email` · `notes` · TS · +IMP+. **Aucune colonne `statut`.**
- Format `code` : `CLI-0001`, sans exception (le convertisseur recode les codes historiques, l'ancien code va dans `legacy_numero`).
- Conservation : DELETE refusé et `code` immuable — garde en base à concevoir (PT-4) ; la FK `RESTRICT` des documents ne protège qu'un client référencé. Les données de profil restent modifiables ; les documents historiques conservent leurs snapshots (INV-30).
- Le « rattachement de client » (réaffectation de `client_id` depuis un client `a_rattacher`) **n'existe plus** (INV-49 retiré). Un client importé dont l'identité est ambiguë : PT-3.

**`fournisseurs`** (cible V3.13) : `id` PK · `code` UQ NN · `nom` NN · `adresse` · `cpville` · `tel` · `email` · `notes` · TS. Format `FOU-0001`. **Aucune colonne `statut`** : tout fournisseur reste sélectionnable pour une nouvelle dépense ; un fournisseur référencé n'est jamais supprimé (FK `RESTRICT` de `depenses.fournisseur_id`), et la garde PT-4 couvre aussi un fournisseur non référencé.

*(Écarts avec les migrations 001/002 — colonnes `statut`, CHECK `a_rattacher ⇒ origine='import'`, index `idx_clients_statut` / `idx_fournisseurs_statut`, absence de garde de suppression et d'immutabilité du code : voir §4.19.)*

### 4.5 Catalogue

**`prestations`** : `id` PK · `reference` UQ NN · `designation` NN · `description` · `categorie_id` NN FK→categories_prestations · `unite` NN · `type_prestation` NN · `prix_unitaire_ht` DL NN · `actif` INTEGER NN (0/1) · TS · +IMP.
Désactivée, jamais supprimée si utilisée. ELE-008 (Cat6) n'est pas dans le catalogue V6 : le catalogue par défaut compte 204 prestations (V5.16 moins ELE-008). [INV-06, INV-37, INV-166]

**`prestation_garanties`** : `id` PK · `prestation_id` NN FK **CASCADE** · `garantie_type` NN · `created_at`. `UQ(prestation_id, garantie_type)`.
Valeurs **par défaut** du catalogue ; jamais source historique. La durée dérive du type (pas de colonne durée).

### 4.6 Devis

**`devis`** : `id` PK · `numero` UQ, **NULL tant que `statut='brouillon'`** (PT-2) · `client_id` NN FK→clients · BLOC-SNAP (client, entreprise, chantier) · `date_creation` D NN · `date_validite` D · `date_acceptation` D · `date_refus` D · `objet` · `notes` · `statut` NN (§2.5) · `revision` INTEGER NULL ≥ 1 (**dernière révision validée ; NULL = version initiale**, PT-21) · `revision_en_cours` INTEGER NN défaut 0 (PT-21) · `remise_type` NN défaut `aucune` · `remise_valeur` · `acompte_type` NN défaut `aucun` · `acompte_valeur` · `total_ht` D2 NN · `frozen_at` TS (**sort : PT-8**) · `cancelled_at` TS · `motif_refus` · `motif_annulation` · `devis_origine_id` NULL FK→devis (devis supplémentaire, PT-7) · TS · +IMP.
CHECK :
- (inchangés) `(remise_type='aucune') = (remise_valeur IS NULL)` ; format selon type (P2 ou D2) ; idem `acompte` ; `statut='accepte'` ⇒ `date_acceptation` NN ; `(statut='annule') = (cancelled_at IS NOT NULL)` ; `cancelled_at` ⇒ `motif_annulation` NN ; `date_validite >= date_creation`.
- `statut='refuse'` ⇒ `date_refus` NN (V3.12) : **à revoir avec la réouverture** (PT-17 : sort de `date_refus` et `motif_refus` après `refuse → en_attente`).
- *(PT-21)* `revision IS NULL OR revision >= 1` ; `revision_en_cours IN (0,1)` ; `revision_en_cours = 1` ⇒ `statut='en_attente'` ; `statut='brouillon'` ⇒ `revision IS NULL` ∧ `revision_en_cours = 0`. **`client_id` immuable après finalisation** (INV-180) : règle portée par TR-10 réécrit.
- **V3.13 (PT-2)** : `(statut='brouillon') = (numero IS NULL)` ; format du numéro conditionné par `origine='v6'` ∧ `numero IS NOT NULL` ; l'année du numéro est celle de la **date de numérotation** du devis (date de validation, à fixer : PT-2).

**Cycle de vie du devis [VALIDÉ — INV-180 à INV-182, INV-196, E-10, E-11, E-20]** :
`brouillon` → *(finalisation : numéro définitif attribué et consommé, INV-179)* → `en_attente` → `accepte` | `refuse` | `annule` ; `refuse → en_attente` (réouverture, numéro inchangé).
- **Brouillon** : persistant, sans numéro définitif, librement modifiable (lignes, garanties de ligne, remises, snapshots), **supprimable tant qu'il n'a jamais été finalisé** — c'est le seul devis supprimable. La suppression d'un brouillon emporte ses lignes et leurs garanties de ligne (données strictement dépendantes, sans valeur historique autonome : PT-5).
- **Finalisation** : attribution du numéro `DEV-xxxxx-YY`, consommation définitive de ce numéro, passage à `en_attente`.
- **`en_attente`** : le devis est numéroté et **reste modifiable** (le client peut demander des ajustements) ; son numéro ne change jamais ; une modification ne crée pas de nouveau numéro. Les modifications d'un devis numéroté s'inscrivent dans le système de **révisions** (ci-dessous).
- **`accepte`** : le devis et sa dernière version sont **verrouillés** : aucune modification directe (lignes, garanties de ligne, remises, acompte prévu, client, chantier, snapshots, total). Seuls évoluent le statut, les dates et motifs liés au statut, et `updated_at` (garde : TR-10 réécrit, PT-2, PT-8). Art. 1193 du Code civil et documentation DGCCRF vérifiés par Rémy ; une évolution du périmètre passe par un nouveau devis accepté rattachable au même BC (INV-187). Aucun module « avenant ».
- **`refuse`** : conservé avec son numéro et **verrouillé** ; peut être **rouvert** (`refuse → en_attente`), le numéro restant identique ; une fois `en_attente`, il est de nouveau modifiable. Refus et réouverture sont tracés dans l'historique (INV-182). **`annule`** : terminal.
- Le devis n'est **plus un « point d'édition » du BC** : le BC est construit par copie, à sa création ou au rattachement d'un devis **accepté** (INV-38 modifié). Aucun statut ni colonne n'est créé pour des raisons seulement techniques (Q14).

**Révisions de devis [VALIDÉ — INV-196, E-20] — stockage : PT-21 « archive JSON raffinée », validé sur le principe le 2026-10-03**

*Règles métier validées*
- Le devis initial est la **version initiale**. Ce n'est **pas** une « révision 0 » : aucune mention métier ni d'interface de « Révision 0 ». Les révisions commencent à **Révision 1** : version initiale → Révision 1 → Révision 2 → Révision 3… Le numéro `DEV-00042` reste strictement identique pendant toute la vie du devis ; l'affichage est « DEV-00042 » (version initiale) puis « DEV-00042 — Révision 1 », « Révision 2 »…
- Une révision est une **nouvelle version complète** du devis, jamais une version par frappe ni par modification élémentaire. Une **phase de révision** commence, après confirmation de l'utilisateur, sur un devis `en_attente` ; elle se termine par une **validation** ou un **abandon**.
- **Toute modification du contenu présenté au client ou ayant un impact quantitatif ou financier** (lignes, quantités, prix, remises, descriptions, prestations, garanties présentées, notes imprimées…) exige une phase de révision. Une modification **technique** sans impact sur le contenu métier présenté ne crée pas artificiellement de révision.
- **`notes`** : si elles font partie du contenu présenté au client, elles appartiennent à la révision et sont historisées avec elle.
- **`client_id`** : après la finalisation et l'attribution du numéro définitif, il est **immuable** ; changer de client exige un nouveau devis.
- **Révision abandonnée** : une révision commencée mais jamais validée ne devient pas une version historique ; aucun numéro de révision n'est consommé ; le devis revient **exactement** à sa dernière version validée.
- **Validation sans modification significative** : refusée ou abandonnée ; elle ne crée pas de révision.
- **Refus ou annulation pendant une révision** : la révision non validée est abandonnée ; le contenu historique reste celui de la dernière version validée ; aucun état intermédiaire non validé ne devient une référence historique.
- Une nouvelle révision part **toujours de la dernière version validée**. Reprendre une ancienne révision comme base **n'est pas implémenté** à ce stade.
- Pendant une révision en cours, la **dernière version validée reste la référence contractuelle et historique** ; les restitutions destinées à représenter le devis validé (PDF, exports, montants validés) utilisent cette version ; l'interface distingue clairement la version validée de la version en cours de modification. À l'acceptation, la dernière version validée est la version contractuelle : le devis est verrouillé et `devis.revision` l'identifie (aucune colonne équivalente dans `bc_devis`).

*Modèle retenu — PT-21 (validé sur le principe ; les détails de représentation ci-dessous sont des propositions techniques)*
- **Tables vivantes** (`devis`, `devis_lignes`, `devis_ligne_garanties`) : elles portent la version courante — la dernière version validée lorsque `revision_en_cours = 0`, la version en modification lorsque `revision_en_cours = 1`. Totaux, index, copie vers le BC et requêtes existantes restent inchangés.
- **Table `devis_revisions`** (append-only) : un **snapshot complet** de chaque version validée, **y compris la version initiale**.
- **Représentation de la version initiale [DÉCISION FIGÉE — 2026-10-03]** : **`revision IS NULL`**. Version initiale : `revision IS NULL` ; Révision 1 : `revision = 1` ; Révision 2 : `revision = 2` ; etc. **Il n'existe jamais de Révision 0**, ni stockée ni affichée. `ordre_version` n'est **pas** retenu. L'ordre chronologique des versions est : NULL (version initiale), puis 1, 2, 3… Le `0` de `COALESCE(revision, 0) + 1` est **uniquement une valeur technique de calcul**, jamais une valeur métier stockée.
- **Protections obligatoires (futur DDL, non créé)** :
  - `CHECK (revision IS NULL OR revision >= 1)` sur `devis`, `devis_revisions` et `documents` ;
  - `UNIQUE(devis_id, revision)` sur `devis_revisions` ;
  - **index unique partiel** `UNIQUE(devis_id) WHERE revision IS NULL` : une seule version initiale par devis (SQLite considère deux NULL comme distincts dans un `UNIQUE` ordinaire) ;
  - **contrôle (TR-10 à la finalisation, CK-15)** : un devis dont le `statut` n'est plus `brouillon` possède son snapshot de version initiale (NULL désigne à la fois « brouillon sans version » et « version initiale » ; seul `statut` les distingue) ;
  - TR-100 : numérotation consécutive sans trou ni doublon.
- **Règles d'écriture SQL** : aucune requête métier n'utilise `revision = NULL` ni `revision = ?` avec un paramètre pouvant être NULL (aucune erreur, mais jamais de résultat). La recherche de la version initiale utilise `IS NULL`, ou `IS ?` quand le paramètre est une valeur optionnelle. Le calcul de la prochaine révision utilise explicitement `COALESCE`.
- **Requêtes canoniques (couche repository/service ; aucune vue pour l'instant)** :
  ```sql
  -- version initiale
  SELECT * FROM devis_revisions WHERE devis_id = :id AND revision IS NULL;
  -- dernière version validée (une seule requête de référence, centralisée dans le repository)
  SELECT r.* FROM devis d
  JOIN devis_revisions r ON r.devis_id = d.id AND r.revision IS d.revision
  WHERE d.id = :id AND d.statut <> 'brouillon';
  -- numéro de la révision en cours / prochaine révision
  SELECT COALESCE(revision, 0) + 1 FROM devis WHERE id = :id;
  -- document d'une version (paramètre NULL = version initiale)
  SELECT * FROM documents WHERE type_entite = 'devis' AND entite_id = :id AND revision IS :revision;
  ```
  Une vue `v_devis_version_validee` n'est **pas** créée ; elle ne pourra être introduite que si l'implémentation réelle démontre un gain significatif de sécurité ou de simplicité.
- **Colonnes de `devis`** : `revision` = numéro de la dernière révision validée (NULL tant qu'aucune révision n'a été validée) ; `revision_en_cours` (0/1). Aucune colonne `revision_acceptee` : ni dans `bc_devis`, ni sous un autre nom (redondante avec `devis.revision` d'un devis accepté, donc verrouillé).
- **`devis_revisions`** : `id` PK · `devis_id` NN FK→devis `RESTRICT` · `revision` INTEGER NULL (≥ 1 ; **NULL = version initiale**) · `schema_contenu` INTEGER NN ≥ 1 (version du format de `contenu`) · `contenu` TEXT NN, `json_valid` et `json_type(contenu) = 'object'` · `total_ht` D2 NN (dénormalisé pour les listes) · `valide_at` TS NN · `created_at`. Unicité : `UQ(devis_id, revision)` pour les révisions numérotées + **index unique partiel** `(devis_id) WHERE revision IS NULL` (SQLite considère deux NULL comme distincts : l'index garantit une seule version initiale par devis).
- **Contenu du snapshot** (restitution historique sans dépendre du catalogue ni des données liées) : les trois snapshots client, entreprise, chantier avec leurs versions ; `objet` ; `notes` (si présentées au client) ; `date_validite` ; remise globale ; acompte prévu ; `total_ht` ; toutes les lignes (`ordre`, `reference_prestation`, `designation`, `description`, `quantite`, `unite`, `prix_unitaire_ht`, remise, `type_prestation`, `total_ht`, `prestation_id` **à titre purement informatif, sans contrainte de clé**) ; les garanties de chaque ligne. *Limite* : le texte des clauses de garantie et le gabarit du PDF viennent de l'application ; pour la présentation exacte au client, le PDF généré et son `hash` (table `documents`) restent la preuve.
- **Propre au devis courant** (hors snapshot) : `id`, `numero`, `date_creation`, `client_id` (immuable après finalisation), `statut`, `date_acceptation`, `date_refus`, `motif_refus`, `cancelled_at`, `motif_annulation`, `created_at`, `updated_at`, `origine`, `legacy_id`, `legacy_data`, `revision`, `revision_en_cours`. Ces colonnes évoluent sans phase de révision.
- **Écritures par le service**, dans la transaction de chaque événement :
  - **finalisation** : écrit le snapshot de la version initiale (`revision` NULL) ;
  - **démarrer une phase de révision** (après confirmation) : `revision_en_cours := 1` uniquement ; aucune ligne d'archive, aucun numéro consommé ;
  - **valider** : écrit le snapshot `COALESCE(revision, 0) + 1`, puis `devis.revision := ce numéro` et `revision_en_cours := 0` ;
  - **abandonner** : restaure les tables vivantes depuis le snapshot de la dernière version validée et remet `revision_en_cours := 0` ; `revision` est inchangé.
- **Écriture du snapshot** : une seule requête SQL (`INSERT … SELECT json_object(…)`) construit le contenu depuis les tables vivantes, afin que le snapshot soit égal à la version vivante par construction ; CK-15 réutilise la même requête.
- **Validation sans modification significative** : le service compare le contenu canonique vivant au snapshot de la dernière version validée ; identique ⇒ validation refusée (ou phase abandonnée), aucune révision créée.
- **Acceptation** : possible seulement si `revision_en_cours = 0` (garde de service, trigger possible) ; le contenu vivant est alors égal au snapshot de la dernière version validée.
- **PDF** : `documents.revision` INTEGER NULL (`CHECK (revision IS NULL OR revision >= 1)` ; **NULL = version initiale** pour un document de devis, et **NULL = sans version** pour les autres types ; `CHECK (type_entite = 'devis' OR revision IS NULL)`), posé à l'INSERT. `numero_version` **n'est pas** le numéro de révision : plusieurs générations techniques d'un même PDF peuvent exister sans constituer de nouvelles révisions.
- **Contrôles** : TR-100 (append-only, §8) et CK-15 (§14).
- **Pourquoi pas des tables relationnelles versionnées** : reconstruction des trois tables de `003`, modification de TR-10/TR-11/TR-18 et de `bc_lignes.devis_ligne_id`, et tout consommateur devrait filtrer la version.

*Cas particuliers (déduits des règles validées ; propositions techniques cohérentes)*
- **Devis refusé puis rouvert** : retour à `en_attente` sur la même version, `revision_en_cours = 0` ; toute modification exige ensuite une nouvelle phase de révision. La révision suivante porte le numéro suivant la dernière révision validée.
- **Devis accepté ou transformé en BC** : verrouillé ; aucune révision (une évolution du périmètre passe par un nouveau devis, INV-187).
- **Devis importé** : le snapshot de sa version initiale est écrit à l'import ; s'il est `en_attente`, il suit le cycle normal.

*Points techniques restant à valider (non tranchés)*
1. **`notes` sont-elles imprimées sur le devis ?** (fait à confirmer ; par défaut incluses dans le snapshot).
2. **Comparaison « modification significative »** : contenu canonique ; normalisation éventuelle (espaces, casse) ; refus ou abandon automatique : décision d'interface.
3. **PDF** : génération après le `COMMIT` de la validation, depuis le snapshot ; lien `documents.revision`.
4. **Triggers** (TR-10, TR-11 en liste blanche, TR-100) et ordre des lignes dans `json_group_array` selon la version de SQLite embarquée.
5. Libellés des événements d'historique (PT-15) : `revision_demarree`, `revision_validee`, `revision_abandonnee`.
*(Clos le 2026-10-03 : représentation de la version initiale par `revision IS NULL`, `ordre_version` non retenu, aucune vue.)*


**Devis rattaché à un BC** [INV-175, INV-187, D-47] : un devis rattaché ne quitte `accepte` que si son BC est `annule` (TR-18, lecture via le lien devis ↔ BC : PT-6). **L'annulation d'un BC n'annule pas ses devis** (E-15) : un devis rattaché garde son statut, son historique et ses lignes. `date_acceptation` est la date contractuelle d'acceptation (D-37). **Un devis à `0.00` € ne peut pas être accepté** : règle du service d'acceptation, sans CHECK (INV-178, D-36) ; un devis à 0.00 € reste possible dans les autres statuts.

**Suppression** [INV-06, INV-180, Q11] : seul un devis **`brouillon`** (sans numéro définitif) peut être supprimé physiquement. Tout devis numéroté est conservé, quel que soit son statut : la suppression est refusée par une garde en base (PT-5) ; la FK `RESTRICT` du lien devis ↔ BC (PT-6) protège en outre tout devis rattaché. *(Écart avec D-33 et `003_devis.sql` — « un devis sans BC peut être supprimé ; lignes et garanties en CASCADE » : voir §4.19.)*

**`devis_lignes`** : `id` PK · `devis_id` NN FK (**CASCADE** en `003` ; cible : PT-5, cascade limitée à la suppression d'un brouillon) · `ordre` INTEGER NN ≥ 1 · `prestation_id` NULL FK→prestations · `reference_prestation` · `designation` NN · `description` · `quantite` DL NN (> 0) · `unite` NN · `prix_unitaire_ht` DL NN · `remise_type` NN · `remise_valeur` · `type_prestation` NN · `total_ht` D2 NN · TS.
`UQ(devis_id, ordre)`. Ligne libre : `prestation_id IS NULL` (aucune pseudo-prestation, aucun `type_ligne='libre'`). La ligne est un snapshot : le catalogue ne la modifie jamais. Réordonnancement : régénération des lignes dans la transaction (ou passage par des `ordre` temporaires).

**`devis_ligne_garanties`** : `id` PK · `ligne_id` NN FK→devis_lignes (**CASCADE** en `003` ; cible : PT-5) · `garantie_type` NN · `created_at`. `UQ(ligne_id, garantie_type)`.

### 4.7 Bons de commande [INV-38, INV-40, INV-46, INV-173 à INV-176, INV-186 à INV-189]

Structure **cible V3.13**. Les règles métier sont INV-186 à INV-189 ; les éléments structurels marqués **[PT-6, PT-7, PT-8]** sont des propositions techniques non validées.

**`bons_commande`** : `id` PK · `numero` UQ NN · `client_id` NN FK→clients · BLOC-SNAP (client, entreprise, chantier : snapshots du BC) · `date_creation` D NN (jour d'enregistrement du BC dans BATORYA) · `date_acceptation` D NN (date contractuelle du devis d'origine, PT-7) · `date_debut` D · `date_fin` D · `montant_contractuel_ht` D2 NN (Σ `total_ht` des devis rattachés, INV-39) · **caches** : `montant_deja_facture_ht` D2 NN défaut `0.00`, `avancement` P2 NN défaut `0.00`, `date_100_facture` D, `statut` NN défaut `en_cours`, `completed_at` TS · `cancelled_at` TS · `motif_annulation` · `frozen_at` TS (**sort : PT-8**) · TS · +IMP+.
**Retraits par rapport à `004` [PT-6, PT-7]** : `devis_id` (`UNIQUE NOT NULL` : le BC n'a plus un devis unique, le lien devient la table `bc_devis`) ; `remise_type`/`remise_valeur` et `acompte_type`/`acompte_valeur` (portés par **chaque devis**, qui garde sa remise globale et son acompte prévu : INV-189, INV-192).

**`bc_devis`** *(PROPOSITION PT-6, table nouvelle)* : `id` PK · `bc_id` NN FK→bons_commande `RESTRICT` · `devis_id` NN **UQ** FK→devis `RESTRICT` · `rang` INTEGER NN ≥ 1 (ordre de rattachement ; rang 1 = devis d'origine) · `created_at` TS. `UQ(bc_id, rang)`. Un devis n'appartient qu'à **un** BC ; un BC peut avoir **plusieurs** devis (1 → N). Jamais supprimée ni modifiée (une relation historique ne change jamais de cible, INV-184). Triggers minimaux proposés : à l'INSERT, devis `accepte`, même client que le BC, BC non annulé ; UPDATE et DELETE refusés. La condition « aucun solde rédigé/validé » porte sur les factures (tranche ultérieure) : **règle de service** à la porte du rattachement (INV-187), contrôlée par CK-14 ; un trigger ne pourra être ajouté qu'avec la tranche Facturation.

**Règle de rattachement d'un devis à un BC [VALIDÉ — INV-187, Q17, Q23 corrigé, arbitrage C]**
- Un devis accepté soit **crée un nouveau BC** (premier devis), soit **rejoint un BC existant** du même client.
- Le rattachement est possible **tant que la facture de solde n'a pas été rédigée/validée** : un acompte déjà émis, une ou plusieurs situations déjà émises ne ferment pas le BC ; plusieurs devis acceptés peuvent rejoindre le même BC.
- Dès que le solde est rédigé/validé, le BC est clôturé commercialement : aucun nouveau devis ne peut lui être rattaché ; **un avoir ultérieur sur le solde ne le rouvre pas** ; un nouveau BC est nécessaire.
- Un **BC annulé** ne reçoit aucun nouveau devis.
- Le rattachement copie dans le BC les lignes et les garanties de ligne du devis (mêmes contenus, INV-175, INV-86), met à jour `montant_contractuel_ht` et écrit un événement d'historique `rattachement_devis` (INV-194), dans une seule transaction. Les documents déjà émis ne sont pas réécrits.
- Chaque devis reste individuellement identifiable ; un devis supplémentaire peut référencer le devis initial (`devis_origine_id`, PT-7), sans diff stocké.
- *Déduit (aucune règle nouvelle)* : l'ajout d'un devis augmente le contractuel du BC ; les factures déjà émises ne sont pas modifiées ; une situation ultérieure se calcule sur le nouveau contractuel avec la facturation nette antérieure (montants cumulés, INV-190).

`remise_*` et `acompte_*` (portés par le devis) : mêmes CHECK que ceux du §4.6.
CHECK de `bons_commande` :
- `(statut='termine') = (completed_at IS NOT NULL)` ; `termine` ⇒ `date_100_facture` NN.
- `(statut='annule') = (cancelled_at IS NOT NULL)` ; `cancelled_at` ⇒ `motif_annulation` NN et non vide.
- `date_fin >= date_debut` si les deux existent.
- Cohérence **sûre** des caches : `date_100_facture` NN ⇒ `avancement = '100.00'` (suppose que les caches s'écrivent en un seul `UPDATE`, §3.7, INV-164). Les conditions `termine ⇒ frozen_at NN` et `date_100_facture NN ⇒ frozen_at NN` de `004` dépendent du sort de `frozen_at` (PT-8).
- **Pas** de CHECK `montant_deja_facture_ht <= montant_contractuel_ht` (INV-46).
- Format `numero GLOB 'BCD-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'` ∧ `substr(numero,11,2)=substr(date_creation,3,2)`, **sans condition sur `origine`** (le convertisseur génère les numéros de BC ; l'ancien numéro éventuel va dans `legacy_numero`).
- BLOC-IMP+ : `origine='v6'` ⇒ `legacy_id`, `legacy_data`, `legacy_numero` NULL ; `legacy_numero` NULL ou différent de `numero` (INV-136).
- Aucun CHECK entre `date_acceptation` et `date_creation`, et aucun CHECK inter-tables (CK-13 et CK-14 sont des requêtes de contrôle, §14).

**Dates** [INV-176, D-37] :
- `date_creation` = date locale du jour de la création (enregistrement) du BC ; immuable (TR-01) ; **son année détermine le `yy` du numéro `BCD`**.
- `date_acceptation` = date contractuelle d'acceptation, **copiée exactement** de `devis.date_acceptation` du **devis d'origine** (PT-7) ; chaque devis rattaché conserve la sienne.
- Les deux dates ont des rôles distincts et peuvent différer. **Il n'existe aucune règle générale d'ordre entre elles.**
- Pour un BC importé, les deux dates sont des faits fournis par le fichier (§10.3) ; la borne d'année de numérotation (§2.2) concerne `date_creation` ; son traitement à l'import relève du contrat d'import (P-04).

**État de naissance** [INV-40] : un BC naît `statut='en_cours'`, avec `cancelled_at`, `completed_at`, `motif_annulation` et `date_100_facture` NULL, `montant_deja_facture_ht='0.00'` et `avancement='0.00'` (`frozen_at` NULL en `004` : PT-8). Garde SQL : défauts de colonnes, TR-17 (refuse tout autre état de naissance) et CHECK `statut ⇔ completed_at / cancelled_at`. Un BC importé naît dans le même état ; ses caches sont ensuite recalculés par le service (INV-169).

**Cycle de vie** [INV-173, INV-174, INV-188, D-35, D-46] :
- `en_cours` ↔ `termine` : caches recalculés par le service financier (§3.5, événement `retour_en_cours`).
- **`annule`** [VALIDÉ — E-15] : **terminal** (jamais `en_cours`, jamais réactivé). Le BC annulé est **conservé** avec son numéro, ses devis (**non annulés automatiquement**), factures, règlements, avoirs, dépenses et historique. Il ne reçoit plus de nouvel acompte, de nouvelle situation, de nouveau solde ni de nouveau devis ; son contenu contractuel reste intact. Les opérations de correction de documents existants (avoirs) restent possibles et peuvent faire évoluer ses caches : **TR-12 (« BC annulé : `client_id` et `updated_at` seulement ») est à adapter** (PT-16).
- **Aucun BC n'est jamais supprimé physiquement**. Garde en base : TR-19, FK `RESTRICT` sur toutes les tables qui référencent le BC et `recursive_triggers=ON` (§1). Le service n'émet jamais de DELETE sur `bons_commande`.
- **Annulation** [INV-44 modifié] : possible quel que soit l'état de la facturation (aucun refus fondé sur les factures, situations ou encaissements existants) ; règle de service avec motif obligatoire et événement d'historique ; **aucune cascade vers les devis**.

**Caches** : `montant_deja_facture_ht` (= facturation nette), `avancement`, `statut`, `completed_at`, `date_100_facture` sont des **caches** recalculés par **un seul service financier**, dans la même transaction que l'opération, **en un seul `UPDATE`**. La source de vérité est `factures + reglements`. [INV-46, INV-164]
`avancement` = facturation nette / contractuel (P2) ; **100.00 si solde actif**. Il mesure la facturation, jamais l'avancement physique ni l'exécution (§3.8).

**Cohérence structurelle devis ↔ BC** [INV-175, D-36, D-47] :
- **Liste S** (données structurantes de chaque devis rattaché) : `client_id` ; `total_ht` ; `remise_*` ; `acompte_*` ; les trois snapshots et leurs versions ; `date_acceptation` ; les lignes (1:1, tous les champs) ; les garanties de ligne.
- **Règle du miroir** : à la création du BC **et à chaque rattachement**, la partie de S relative au devis est copiée **exactement** dans le BC (`bc_lignes`, `bc_ligne_garanties`). Le devis étant `accepte`, donc verrouillé (INV-181), S ne change plus : il n'y a plus de régénération du BC (INV-38 modifié) et la cohérence est stable. Le BC conserve ses propres snapshots (ceux de sa création) ; ceux de chaque devis restent portés par le devis.
- **Un devis rattaché ne quitte `accepte` que si son BC est `annule`** (TR-18, lecture via `bc_devis`). L'annulation du BC ne déclenche **aucune** annulation de devis.
- Pas de trigger de miroir ligne à ligne : pendant la transaction de rattachement, l'état intermédiaire est momentanément incomplet (devis lié, lignes pas encore recopiées) ; un tel trigger refuserait une opération valide. La dérive éventuelle est détectée par CK-13 (§14).

| Règle | SQLite | Service | CK |
|---|---|---|---|
| Format, unicité, année du numéro | CHECK + UNIQUE | calcule `yy` depuis `date_creation` | CK-01, CK-02 |
| `numero`, `date_creation` immuables | TR-01, TR-12 | — | — |
| Un devis appartient à au plus un BC | `UNIQUE(devis_id)` de `bc_devis` (PT-6) | lit le lien existant avant d'allouer un numéro | CK-14 |
| Au rattachement : devis `accepte`, même client, BC non annulé ; état de naissance | trigger du lien (PT-6) et TR-17 | vérifie, fournit les valeurs | CK-13 |
| Au rattachement : aucun solde rédigé/validé (INV-187) | — (tranche Facturation) | oui | CK-14 |
| Contractuel = Σ `total_ht`, copie des données, caches initialisés | — | **construit** la cohérence dans la transaction | **CK-13** |
| Miroir de S après création | — (devis verrouillé) | un seul chemin d'écriture | **CK-13** |
| Le devis rattaché ne quitte `accepte` que si son BC est `annule` | TR-18 | — | CK-13 |
| Ligne de BC liée à une ligne d'un devis **du BC**, 1:1 | `UNIQUE(devis_ligne_id)`, TR-13 | copie | CK-13 |
| Contenu contractuel du BC immuable, BC annulé terminal | TR-12, TR-13 (`frozen_at` / TR-14 : PT-8) | — | — |
| Suppression d'un BC | TR-19, FK `RESTRICT`, `recursive_triggers=ON` | n'émet aucun DELETE | — |
| Caches, `termine`, `date_100_facture` | CHECK de cohérence sûrs | un seul UPDATE | CK-06 |
| Annulation du BC (INV-44, INV-188) | — | oui, sans condition de facturation, sans cascade | — |
| Année 2001–2099 des dates de numérotation seulement (D-38) | — | oui (jamais un CHECK ; import : P-04) | — |
| Devis à 0.00 € non acceptable (INV-178) | — | oui (service d'acceptation) | CK-13 (contractuel > 0) |

**Partage des rôles à la création et au rattachement** [D-36, D-47] : le **service** construit la cohérence (vérifie le devis accepté et l'éligibilité du BC, copie les données contractuelles, crée le BC ou le lien, initialise ou met à jour les caches, dans une seule transaction) ; les **triggers** garantissent les invariants propres au BC et au lien ; **CK-13** et **CK-14** détectent ensuite les divergences inter-tables, en diagnostic. Ni CHECK ni trigger inter-tables.

**`bc_lignes`** : mêmes colonnes que `devis_lignes` + `bc_id` NN FK→bons_commande **`RESTRICT`** + `devis_ligne_id` NN **UQ** FK→devis_lignes (`RESTRICT`).
`UQ(bc_id, ordre)` ; `UQ(devis_ligne_id)` : un BC ne contient jamais deux fois la même ligne de devis, et une ligne de devis n'appartient qu'à un seul BC. `ordre` est l'ordre dans le BC : les lignes d'un devis rattaché sont ajoutées **à la suite**, sans renumérotation des lignes existantes. **Pas de colonne `active`.** Les lignes d'un BC ne sont ni modifiées ni supprimées (INV-186) ; elles ne sont **insérées** que par la création du BC ou le rattachement d'un devis (TR-13 : la ligne de devis doit appartenir à un devis **rattaché à ce BC**, PT-6 ; BC non annulé). Aucune facture ne référence une ligne BC avant la première facture, donc aucun conflit avec `facture_lignes.bc_ligne_id` (`RESTRICT`). [INV-38, INV-168]
**`bc_ligne_garanties`** : `id` PK · `ligne_id` NN FK→bc_lignes (**CASCADE** en `004` ; **cible `RESTRICT`** : plus de régénération donc plus de cascade utile, PT-5) · `garantie_type` NN · `created_at`. `UQ(ligne_id, garantie_type)`. Seule source des garanties du BC (§4.10) : copiées de `devis_ligne_garanties` à la création du BC ou au rattachement du devis, **jamais lues du catalogue** (INV-37) ; un BC importé n'en a aucune (INV-134, D-16).

**BC historique annulé (import)** : reconstruit comme en fonctionnement normal, sans contournement : devis `accepte` → BC inséré `en_cours` (état de naissance, TR-17) avec ses lignes → factures éventuelles tant que le BC est `en_cours` → annulation du BC. **Le devis reste `accepte`** sauf si le fichier le déclare annulé (aucune cascade, INV-169). Les faits à fournir et l'ordre exact relèvent du contrat d'import (P-04, §10.5).

### 4.8 Facturation

**`factures`** : `id` PK · `numero` UQ NN · `type` NN · `bc_id` NN FK→bons_commande · `client_id` NN FK→clients · `devis_id` NULL FK→devis (devis d'origine d'un acompte, INV-189, **PT-10**) · BLOC-SNAP (client, entreprise, chantier) · `objet` · `date_emission` D NN · `date_echeance` D · `total_ht` D2 NN · `situation_numero` INTEGER · `avancement_cumule_pct` P2 · `montant_deja_facture_ht` D2 · *(mode de saisie et valeur saisie d'une situation : **PT-11**)* · `origine_facture_id` NULL FK→factures · `motif_avoir` · `created_at` · +IMP.
**Pas de `updated_at`, pas de `statut`, pas de `total_ttc`.** **Retraits [VALIDÉ — E-14, INV-185 ; mécanisme PT-9]** : `cancelled_at` et `motif_annulation` (une facture validée n'est jamais annulée ni rouverte ; elle est corrigée par un avoir).
CHECK :
- `(type='avoir') = (origine_facture_id IS NOT NULL)` ; `type='avoir'` ⇒ `motif_avoir` NN ∧ `date_echeance` NULL ; `type<>'avoir'` ⇒ `date_echeance` NN ∧ `motif_avoir` NULL ; `date_echeance >= date_emission`.
- `(type='situation') = (situation_numero IS NOT NULL) = (avancement_cumule_pct IS NOT NULL) = (montant_deja_facture_ht IS NOT NULL)` (à compléter par PT-11).
- `total_ht <> '0.00'` sauf `type='solde'` (acompte, situation, avoir > 0 ; solde ≥ 0).
- `origine='v6'` ⇒ préfixe selon type (`acompte→ACP-`, `avoir→AVO-`, `situation|solde→FAC-`), format `xxx-nnnnn-yy`, année = `substr(date_emission,3,2)`.

**Aucun brouillon persistant** [INV-185] : la facture est créée, numérotée et validée dans une seule transaction ; l'abandon d'une préparation avant l'émission ne crée aucun objet ; le numéro n'est attribué qu'à l'émission (INV-179, D-54).

**Unicité** : les trois index uniques partiels de la V3.12 (`uq_facture_acompte_actif`, `uq_facture_solde_actif`, `uq_situation_actif`, tous `WHERE cancelled_at IS NULL`) sont **obsolètes**. Les règles métier restent : un seul acompte par devis, un seul solde par BC, une situation par numéro ; **un avoir total permet une nouvelle facture du même type** (arbitrage B). Comment exprimer « actif » sans `cancelled_at` (état dérivé « entièrement créditée », contrôle par trigger ou par service, index partiels impossibles sur un état dérivé) : **À CONCEVOIR (PT-9)**. Le tableau d'avancement des acomptes d'un BC à plusieurs devis (un acompte par devis) relève de PT-10.

`client_id` d'une facture ne change jamais (plus de rattachement de client, E-12).


**`facture_lignes`** : `id` PK · `facture_id` NN FK→factures (RESTRICT) · `ordre` NN ≥ 1 · `bc_ligne_id` NULL FK→bc_lignes · `reference_prestation` · `designation` NN · `description` · `quantite` DL NN · `unite` NN · `prix_unitaire_ht` DL NN · `remise_type` NN · `remise_valeur` · `type_ligne` NN · `montant_ht` D2S NN · `created_at`.
`UQ(facture_id, ordre)`. `type_ligne='deduction'` ⇔ `montant_ht` négatif ; pour une déduction : `quantite='1'`, `prix_unitaire_ht` = valeur absolue, `montant_ht = −arrondi(quantite × prix)`. [INV-62]
Composition :
- **acompte** : 1 ligne `synthese`, montant = `total_ht`.
- **situation** : 1 ligne `synthese`, montant = montant de la situation (le cumul % et le déjà-facturé restent sur la facture).
- **solde** : lignes `prestation` copiées des lignes BC, puis lignes `deduction` (facturation nette antérieure, et remise globale de chaque devis rattaché) ; `Σ = total_ht`, y compris `0.00`. Composition en présence d'une exécution (§3.8) : PT-12.
- **avoir** : lignes positives (`prestation` ou `synthese`).

Contrôle `Σ facture_lignes.montant_ht = factures.total_ht` : par le service à l'émission **et** par requête de contrôle CK-05 (SQLite ne peut pas l'imposer en fin de transaction). Aucune exemption, y compris pour les données importées. [INV-54]

### 4.9 Règlements

**`reglements`** : `id` PK · `facture_id` NN FK→factures · `type` NN · `date_evenement` D NN · `montant` D2 NN (`<> '0.00'`) · `mode` NN · `reference` · `note` · `cancelled_at` TS · `motif_annulation` · `created_at` · +IMP.
CHECK `(cancelled_at IS NULL) = (motif_annulation IS NULL)`. Jamais supprimé ; seules `cancelled_at` et `motif_annulation` peuvent être renseignées, une seule fois. Un remboursement porte sur un **avoir** (`facture_id` = l'avoir) ; il n'y a pas de colonne `avoir_id`. **Un règlement correspond à une seule facture** (`facture_id` obligatoire) ; une facture peut recevoir plusieurs règlements ; un virement couvrant plusieurs factures est réparti explicitement par facture, sans règlement multi-factures (Q20, Q27). [INV-70, INV-71]

### 4.10 Garanties

**`garanties`** : `id` PK · `bc_id` NN FK→bons_commande · `bc_ligne_id` NN FK→bc_lignes · `garantie_type` NN · `date_declenchement` D NN · `date_fin_suivi` D NN · `facture_declenchement_id` NN FK→factures · `created_at`.
`UQ(bc_ligne_id, garantie_type)` (aucune garantie n'est importée : elles naissent uniquement de la facturation V6, INV-134). CHECK `date_fin_suivi > date_declenchement`. Pas de colonne statut. Aucun UPDATE ni DELETE. [INV-85 à INV-90]

Création : à l'émission d'un solde actif, le service lit `bc_ligne_garanties` du BC et insère `INSERT OR IGNORE` (idempotent, la première date est conservée). `date_declenchement` = date d'émission de ce solde. `date_fin_suivi` = +1 an / +2 ans / +10 ans ; 29 février → 28 février si l'année cible n'est pas bissextile. Un avoir (même total) sur le solde, un règlement ne suppriment ni ne modifient une garantie. Un BC importé n'a aucune ligne `bc_ligne_garanties` (INV-134, D-16) : il ne génère aucune garantie native, faute de garantie de ligne à lire.

**Plusieurs devis sur un BC [VALIDÉ — principe du CDC §24 inchangé ; INV-86, INV-87]** : tout devis rattaché l'ayant été **avant** la rédaction du solde (INV-187), toutes les lignes du BC existent, et leurs garanties de ligne ont été copiées, au premier solde : la règle de déclenchement (premier solde actif) fonctionne sans adaptation. Une ligne de devis modifiée (brouillon) garde le principe existant ; une ligne **entièrement supprimée** n'existe plus, donc sa garantie liée non plus (conséquence de la suppression, non une règle nouvelle). **Aucun nouveau système de garantie** n'est créé.

### 4.11 PV

**`pv`** : `id` PK · `numero` UQ NN · `bc_id` NN FK→bons_commande · `type` NN · `date_reception` D NN · BLOC-SNAP (chantier, client, entreprise) · `observations` · `reserves` · `origine_pv_id` NULL FK→pv · `suffixe` INTEGER · `created_at` · +IMP.
CHECK :
- `(type='levee_reserves') = (origine_pv_id IS NOT NULL) = (suffixe IS NOT NULL)` ; `suffixe BETWEEN 1 AND 99`.
- `(reserves IS NOT NULL) = (type='reception_avec_reserves')`.
`UQ(origine_pv_id, suffixe)`. TR-41 : l'origine est un PV `reception_avec_reserves` **du même BC** ; une levée ne référence jamais une levée ; `suffixe = max + 1` ; `numero` de la levée = `numero` de l'origine + `-` + suffixe sur 2 chiffres. Le PV est facultatif et ne conditionne ni le solde, ni Terminé, ni les garanties. Plusieurs PV initiaux par BC ne sont pas interdits. Immuable dès l'INSERT (aucun UPDATE, aucun DELETE). [INV-95 à INV-97]

### 4.12 Dépenses, planning, notes

**`depenses`** : `id` PK · `numero` UQ NN · `fournisseur_id` NULL FK · `bc_id` NULL FK · `date_depense` D NN · `montant` D2 NN (**strictement positif**, `montant > 0` : D2 exclut tout négatif et `<> '0.00'` exclut zéro ; **montant HT** de la dépense : montant économique unique, exact au centime, sans TVA ni montant TTC) · `categorie_id` NN FK→categories_depenses · `description` NN · `piece_jointe_chemin` · `piece_jointe_racine_id` INTEGER (les deux ou aucun) · `notes` · *(annulation : `cancelled_at`, `motif_annulation`, **PT-14**)* · TS.
Ni statut de paiement, ni échéance, ni règlement fournisseur. Une dépense ne réduit jamais le CA URSSAF. **Dépense annulable [VALIDÉ — INV-193, E-19, Q7]** : une dépense active peut être corrigée (erreur de saisie) ; elle peut être annulée lorsqu'elle ne doit plus participer aux calculs métier ; une dépense annulée reste physiquement en base, conserve son numéro, son historique et ses relations (BC, fournisseur, catégorie), et est exclue des **calculs actifs** — totaux de dépenses, marges, analyses économiques, indicateurs actifs — et reste consultable dans l'historique (principe validé : INV-200 ; formules détaillées de chaque analyse : non spécifiées ici, PT-14) ; aucune suppression d'une dépense numérotée. L'annulation n'est pas un statut de paiement. Une dépense annulée est totalement immuable et l'annulation est irréversible (INV-197). **`date_depense` [VALIDÉ — INV-201]** : date métier attribuée à la dépense par l'utilisateur ; elle est proposée par défaut avec la date du jour, mais l'utilisateur peut saisir une date antérieure correspondant à la date métier réelle de la dépense. Elle est distincte de `created_at`, date technique de création de l'objet. Il n'existe ni date de facture, ni échéance, ni date de paiement. Elle est modifiable tant que l'année (yy) du numéro ne change pas ; si une correction exigeait une autre année, la dépense est annulée puis ressaisie sous un nouveau numéro : jamais de renumérotation. Plus de fournisseur archivé (INV-183). Pour `bc_id` d'un **BC non annulé**, si `date_du_jour > date_100_facture + 30 jours`, le service demande une confirmation avant rattachement ; une confirmation positive permet le rattachement sans limite de durée (règle de service, aucun trigger). **Une dépense peut être créée sur un BC annulé, lui être rattachée ultérieurement ou y rester liée** (D5 de l'audit de conservation, INV-188) : pour un BC annulé, aucun délai ni confirmation ; une modification qui conserve le même BC n'est pas un nouveau rattachement (INV-199). [INV-100, INV-103, INV-193, INV-197 à INV-201]

**`planning_evenements`** : `id` PK · `type_evenement` NN · `bc_id` NULL FK · `titre` NN · `date_debut` DL_LOCAL NN · `date_fin` DL_LOCAL NN · `journee_entiere` INTEGER NN (0/1) · `lieu` · `description` · TS.
CHECK : `journee_entiere=1` ⇒ deux dates `YYYY-MM-DD` ; sinon `YYYY-MM-DDTHH:MM` ; `date_fin >= date_debut` ; `type IN ('intervention','travaux')` ⇒ `bc_id` NN ; `type IN ('conge','indisponibilite')` ⇒ `bc_id` NULL. Aucun mapping de types à prévoir : aucune donnée de planning n'est importée (P-01).
Aucun effet sur le statut du BC. Le **Gantt lit `bons_commande.date_debut/date_fin`**, pas cette table ; un BC sans dates n'a pas de barre Gantt. [INV-101]

**`bc_notes`** : `id` PK · `bc_id` NN FK · `contenu` NN · TS. Modifiables et supprimables ; ne touchent aucun montant. Table créée hors de la migration 004 (tranche BC).

### 4.13 Documents

**`documents`** : `id` PK · `type_entite` NN · `entite_id` INTEGER NN · `type_document` NN · `numero_version` INTEGER NN ≥ 1 · `racine_stockage_id` INTEGER NN (référence **logique** vers `machine.db.stockage_racines`, pas de FK possible) · `chemin_relatif` NN · `nom_fichier` NN · `hash` TEXT (SHA-256 hex du contenu réellement présent) · `created_at`.
`UQ(type_entite, entite_id, type_document, numero_version)`. Seul `chemin_relatif` est modifiable (déplacement de statut). Une régénération crée une **nouvelle version**. Aucun DELETE. Le BC n'a pas de document. [INV-105 à INV-108]

### 4.14 Historique

**`historique`** : `id` PK · `type_entite` NN · `entite_id` INTEGER NULL · `bc_id` NULL FK · `type_evenement` NN · `acteur` NN défaut `utilisateur` · `donnees` JSON · `created_at` TS NN.
Append-only : aucun UPDATE, aucun DELETE. Pas de `updated_at`. **Historique métier utile [VALIDÉ — INV-194, Q15]** : il permet de comprendre quoi, quand, avant/après lorsque pertinent, pourquoi lorsque nécessaire et, lorsque l'information existe, qui ; aucune journalisation de chaque frappe. Événements significatifs : création, **validation**, refus, **réouverture**, annulation (devis, BC, dépense), **rattachement d'un devis à un BC**, événements d'exécution significatifs, émission et avoir, règlement et son annulation, remboursement, passage à `termine` et retour à `en_cours`, déclenchement de garantie, déclaration/correction URSSAF, import, restauration, annulation automatique supprimée (plus d'acompte annulé par le système). L'énumération exacte des `type_evenement` est une proposition (PT-15, §2.5). [INV-110, INV-111]

### 4.15 Paramètres

**`parametres_entreprise`** (singleton, `CHECK(id=1)`) : `id` · `forme_juridique` · `nom_entrepreneur` · `prenom_entrepreneur` · `nom_commercial` · `adresse` · `cpville` · `tel` · `email` · `siren` (9 chiffres si renseigné) · `siret` (14 chiffres si renseigné) · `identifiant_complementaire` · `iban` · `bic` · `afficher_coordonnees_bancaires` INTEGER NN (0/1) · `delai_paiement_jours` INTEGER NN (0 à 60) · `modes_reglement_defaut` JSON · `mention_commerciale` · `conditions_commerciales` · `conditions_particulieres` · `version` INTEGER NN défaut 1 · TS.
Valeurs **courantes** : elles ne reconstruisent jamais un document historique (snapshots). Les mentions légales obligatoires ne peuvent pas être retirées par paramétrage.

### 4.16 URSSAF [INV-120 à INV-127]

**`urssaf_referentiels`** : `id` PK · `version` UQ NN · `date_debut_effet` D UQ NN · `schema_version` INTEGER NN · `donnees` JSON NN · `source` · `created_at`.
Append-only. `date_debut_effet` strictement supérieure à toutes les précédentes (TR-80). La fin d'effet = début de la version suivante (aucun chevauchement possible). Une version future peut être importée avant son entrée en vigueur. Version applicable à une période = celle en vigueur à `date_debut` de la période.

**`urssaf_profil`** : `id` PK · `date_debut_activite` D NN · `date_effet` D UQ NN · `periodicite` NN · `acre_active` INTEGER NN (0/1) · `date_debut_acre` D · `created_at`.
Append-only, une ligne par changement. `date_debut_activite` identique sur toutes les lignes (TR-81). CHECK `acre_active=1` ⇒ `date_debut_acre` NN. Statut, secteur et activité sont fixes par le CDC (micro-entrepreneur, travaux BTP, prestation de services) et ne sont pas stockés.

**`urssaf_periodes`** : `id` PK · `profil_id` NN FK→urssaf_profil · `referentiel_version_id` NN FK→urssaf_referentiels · `date_debut` D UQ NN · `date_fin` D UQ NN · `periodicite` NN (snapshot) · `statut` NN défaut `a_declarer` · `ca_encaisse` D2S NN · `cotisations` D2 NN · `cfp` D2 NN · `montant_declare` D2 · `date_declaration` D · `ecart` D2S · `locked_at` TS · TS.
CHECK : `date_debut <= date_fin` ; `(locked_at IS NOT NULL) = (statut <> 'a_declarer')` ; `statut='declaree'` ⇒ `montant_declare`, `date_declaration`, `ecart` NN ; `ecart = montant_declare − (cotisations + cfp)` (calculé à la déclaration, jamais modifié).
Une période à CA nul existe (`0.00`). La première période peut être partielle. Non-chevauchement par TR-82. **Une fois verrouillée, seuls `statut` (`declaree` ↔ `a_verifier`) et `updated_at` peuvent changer.**

**`urssaf_details`** : `id` PK · `periode_id` **UQ** NN FK · `base` D2S NN · `taux_cotisations` DL NN · `taux_cfp` DL NN · `acre_applicable` INTEGER NN (0/1) · `regle_acre` TEXT (règle réellement appliquée) · `calcul_snapshot` JSON NN · `schema_version` INTEGER NN · `created_at`.
Une seule source du `ca_encaisse` : la période. Pas de `referentiel_version_id` ici (il est sur la période). Remplaçable tant que la période n'est pas verrouillée ; figé ensuite.

**`urssaf_periode_encaissements`** : `id` PK · `periode_id` NN FK · `reglement_id` NULL FK→reglements · `facture_id` NULL FK→factures (avoir) · `date_evenement` D NN · `montant_retenu` D2S NN · `traitement` NN · `created_at`.
CHECK `(reglement_id IS NULL) <> (facture_id IS NULL)`. `UQ(periode_id, reglement_id) WHERE reglement_id IS NOT NULL` · `UQ(periode_id, facture_id) WHERE facture_id IS NOT NULL`. TR-84 : `facture_id` désigne un avoir.
Dates : encaissement → `date_evenement` du règlement ; remboursement → date du remboursement ; avoir → date d'émission. Signe : encaissement +, remboursement −, avoir −, si le référentiel l'exige. `traitement='exclu'` = événement examiné mais écarté par la réglementation.
Invariant : `ca_encaisse = Σ montant_retenu` des lignes `retenu` (CK-08). Régénérable tant que la période n'est pas verrouillée. Un événement postérieur touchant une période verrouillée **ne modifie pas ces lignes** : il crée une correction.

**`urssaf_corrections`** : `id` PK · `periode_id` NN FK · `champ` NN · `ancienne_valeur` NN · `nouvelle_valeur` NN · `type_correction` NN · `source_type` NN · `source_id` INTEGER · `motif` NN · `acteur` NN · `created_at`.
CHECK `(source_type IN ('reglement','facture')) = (source_id IS NOT NULL)`. Append-only.
Cycle : événement touchant une période verrouillée → ligne `ecart_detecte` + statut `a_verifier`. Sortie de `a_verifier` : ligne `resolution` (nouveau montant déclaré ou constat d'absence d'écart) + statut `declaree`.

### 4.17 Précisions de DDL de `metier/001_initial.sql` (V3.9) [INV-04, INV-05, INV-14, INV-20 à INV-22, INV-27, INV-130, INV-136]
> **Mise à jour V3.13 (2026-10-03)** : cette sous-section décrit la migration 001 telle qu'appliquée. Les écarts avec les arbitrages du 2026-10-03 (`statut` et `a_rattacher` des clients, absence de garde de suppression, etc.) sont listés au §4.19 ; ils se corrigent par migration ultérieure, jamais en réécrivant 001.


Cette sous-section ne crée **aucune règle ni décision nouvelle** : elle fixe la traduction SQL des §2 à §4.5, §8 et §9 pour la première tranche métier.

1. **Périmètre de la migration** : `import_anomalies`, `numerotation_sequences`, `categories_prestations`, `categories_depenses`, `clients`, `prestations`, `prestation_garanties` ; triggers TR-90 et TR-95 ; index `clients(statut)`, `prestations(categorie_id)`, `prestations(actif)`, `import_anomalies(categorie, statut)`. `fournisseurs` n'est pas dans cette tranche : il constitue la tranche suivante, avant `devis`, `bons_commande` puis `depenses`.
2. **Aucune ligne insérée** par la migration (listes de référence, catalogue par défaut, séquences) : jeu de données d'installation (§4.3) ; les séquences naissent à la première attribution (§4.2) ou à l'import (§10.6).
3. **Textes obligatoires non vides** : `code`, `nom`, `libelle`, `reference`, `designation`, `ref_source`, `motif`, `type_entite` (CHECK `<> ''`). Les textes facultatifs ne sont pas contrôlés.
4. **Familles et listes** : `prix_unitaire_ht` en famille DL (§2.3) ; `actif` ∈ (0, 1) ; `statut` client, `unite`, `type_prestation`, `garantie_type`, `categorie`/`statut` d'anomalie : listes fermées du §2.5 (`CHECK … IN (…)`).
5. **Code client** : `CHECK code GLOB 'CLI-[0-9][0-9][0-9][0-9]'`, **sans exception d'origine** (D-01, INV-20, INV-27). `statut = 'a_rattacher'` ⇒ `origine = 'import'` ; `legacy_numero` NULL ou différent de `code` (INV-136).
6. **BLOC-IMP** (`clients`, `prestations`) : `origine IN ('v6','import')` ; `origine = 'v6'` ⇒ `legacy_id`, `legacy_data` (et `legacy_numero` pour `clients`) NULL ; `legacy_data` JSON valide si présent. Aucune contrainte supplémentaire (en particulier, `legacy_id` n'est pas rendu obligatoire ni unique).
7. **`import_anomalies`** : `type_entite` est un texte non vide **sans CHECK `IN (…)`** : c'est l'exception explicite à la règle d'énumération fermée des liens polymorphes (§2.1). Motifs : la table est alimentée uniquement à l'import (INV-163) ; une anomalie `non_importe` décrit une donnée que V6 ne représente pas, donc hors des types d'entités V6 ; le modèle (§2.5, §4.1, §10.7) n'en définit pas la liste. Les valeurs admises sont définies par le contrat `import-v6.json` (point P-04) et vérifiées par le lecteur strict (INV-153) ; CK-09 contrôle l'existence de `entite_id` pour les anomalies `a_verifier`. TR-90 : DELETE interdit ; UPDATE autorisé uniquement pour la transition `a_traiter` → `traite` (colonnes `statut` et `traite_at`, une seule fois). Aucune FK (lien polymorphe, contrôlé par CK-09).
8. **`numerotation_sequences`** : `annee BETWEEN 0 AND 99` ; plafond `dernier_numero` 9 999 (CLI/FOU) ou 99 999 (documents) en CHECK ; TR-95 : `dernier_numero` ne diminue jamais lors d'un `UPDATE` (la migration 001 reste inchangée ; l'interdiction du DELETE est ajoutée par TR-96 dans la migration 004, §4.18). Création/attribution : `INSERT (type_objet, annee, dernier_numero) VALUES (?, ?, 1) ON CONFLICT(type_objet, annee) DO UPDATE SET dernier_numero = dernier_numero + 1, updated_at = … RETURNING dernier_numero` ; au plafond, le CHECK refuse l'écriture (le service la traduit en erreur métier explicite).
9. **`prestation_garanties`** : FK `prestation_id` en CASCADE (INV-05) ; l'index de `UQ(prestation_id, garantie_type)` couvre la FK (pas d'index séparé).
10. **Point ouvert (P-04)** : le contrat d'import accepte un bloc `categories_prestations` dont chaque objet porte un `ref` copié dans `legacy_id`, alors que BLOC-IMP n'existe pas sur `categories_prestations` (§2.4). Le DDL suit le §2.4 (pas de BLOC-IMP sur les listes). La suite (ajouter BLOC-IMP aux catégories, ou ne pas conserver le `ref`) est à trancher avec le schéma JSON.

### 4.18 Précisions de DDL de `metier/004_bons_commande.sql` (V3.12) [INV-04 à INV-06, INV-10, INV-20, INV-23, INV-31, INV-36, INV-40, INV-46, INV-48, INV-136, INV-173 à INV-176]
> **Mise à jour V3.13 (2026-10-03)** : cette sous-section décrit la migration 004 telle qu'appliquée (un BC = un devis, `bons_commande.devis_id`, gel, régénération, exception `a_rattacher`). Plusieurs de ces éléments sont dépassés par les arbitrages (BC multi-devis, plus de régénération, annulation sans cascade) : voir §4.19 et §17.1 (M-B, propositions). 004 reste immuable.


Cette sous-section fixe la traduction SQL des §2, §4.6, §4.7, §6, §7.2 et §8 pour la tranche Bons de commande. Elle ne crée **aucune règle nouvelle** : les règles sont aux sections citées. Le fichier `004_bons_commande.sql` et son test (T-29) sont intégrés au dépôt et couverts par la campagne de mutation décrite au §17.1.

1. **Périmètre** : `bons_commande`, `bc_lignes`, `bc_ligne_garanties` ; 15 triggers (dont `tr_96`, posé sur `numerotation_sequences` comme TR-18 l'est sur `devis`) ; 3 index. Hors tranche : `bc_notes`, `depenses`, `factures`, `reglements`, `garanties`, `pv` (aucune FK ni aucun trigger de la migration ne les anticipe ; ces tables référenceront `bons_commande` dans leur propre migration).
2. **Généralités** : tables `STRICT` ; aucune ligne insérée ; aucune clause `ON UPDATE` ; `PRAGMA user_version = 4` posé par le runner ; textes obligatoires non vides (`motif_annulation` s'il est renseigné) ; `origine` défaut `v6` ; `created_at` et `updated_at` défaut instant UTC en millisecondes, contrôlés par `GLOB` ; familles décimales et dates comme en 003 (`GLOB` explicites, `date(x) IS x`, jamais `date(x) = x`).
3. **Colonnes et CHECK** : §4.7. `statut` ∈ (`en_cours`, `termine`, `annule`), défaut `en_cours`. Le numéro suit le motif `GLOB` explicite du §4.7, sans condition d'origine.
4. **Triggers** (15). Nommage `tr_<NN>_<table>_<règle>`, message `RAISE(ABORT, 'INV-xx: …')` ; un trigger `BEFORE` s'exécute avant les CHECK, donc un écart d'état de naissance remonte avec le message `INV-xx` du trigger :

| Trigger | TR | Règle |
|---|---|---|
| `tr_01_bons_commande_numero_immuable` | TR-01 | UPDATE : `numero` et `date_creation` immuables |
| `tr_12_bons_commande_modifiable` | TR-12 | UPDATE d'un BC non gelé et non annulé : `id`, `devis_id`, `created_at` immuables |
| `tr_12_bons_commande_gele` | TR-12 | UPDATE d'un BC gelé : liste blanche du §7.2 (caches, `date_debut`, `date_fin`, `cancelled_at`, `motif_annulation`, `client_id` de rattachement, `updated_at`) |
| `tr_12_bons_commande_annule` | TR-12 | UPDATE d'un BC annulé, gelé ou non : `client_id` de rattachement et `updated_at` seulement |
| `tr_14_bons_commande_frozen_at` | TR-14 | `frozen_at` : NULL → valeur, jamais l'inverse |
| `tr_17_bons_commande_insert` | TR-17 | INSERT : devis `accepte` ; `client_id` = celui du devis ; état de naissance (invariants locaux ; ni comparaison complète avec le devis, ni contrôle du contractuel : service et CK-13) |
| `tr_13_bc_lignes_insert`, `_update`, `_delete` | TR-13 | refus si le BC est gelé ou annulé ; INSERT et UPDATE : la ligne de devis appartient au devis du BC |
| `tr_13_bc_ligne_garanties_insert`, `_update`, `_delete` | TR-13 | refus si le BC de la ligne parente est gelé ou annulé |
| `tr_19_bons_commande_no_delete` | TR-19 | DELETE toujours refusé |
| `tr_18_devis_statut_avec_bc` | TR-18 | sur `devis`, UPDATE de `statut` : un devis ayant un BC ne quitte `accepte` que si ce BC est `annule` |
| `tr_96_numerotation_sequences_no_delete` | TR-96 | sur `numerotation_sequences`, DELETE toujours refusé, message `RAISE(ABORT, 'INV-22: numerotation_sequences ne se supprime jamais')` (comme `tr_95`, dont le message est `INV-22: numerotation_sequences.dernier_numero ne diminue jamais`) : protège un DELETE direct et, avec `recursive_triggers=ON`, la suppression implicite de `INSERT OR REPLACE` ; complète `tr_95` (UPDATE) sans modifier `001_initial.sql` |

   Lorsque la suppression d'une garantie de ligne résulte d'un `CASCADE`, la ligne parente est déjà supprimée au moment où le trigger enfant s'exécute : la garde repose alors sur `tr_13_bc_lignes_delete`, qui refuse la suppression de la ligne si le BC est gelé ou annulé.
5. **Index** : `idx_bons_commande_client_id`, `idx_bons_commande_statut`, `idx_bc_lignes_prestation_id`. `numero`, `devis_id`, `bc_lignes.devis_ligne_id`, `bc_lignes(bc_id, ordre)` et `bc_ligne_garanties(ligne_id, garantie_type)` sont couverts par leur `UNIQUE`.
6. **Aucune FK vers une table absente** : une FK vers une table inexistante échoue même avec une valeur NULL ; les FK des tables futures vers `bons_commande` sont créées avec ces tables.
7. **Hors SQL (service)** : attribution du numéro (séquence `BCD`, année de `date_creation`, upsert `RETURNING`, high-water), copie des snapshots, de la remise, de l'acompte, de `date_acceptation`, des lignes et des garanties, écriture des caches, contrôle de la borne d'année des dates de numérotation (2001–2099, §2.2) et du devis à 0.00 €, miroir devis ↔ BC, règle d'annulation.
8. **Livraison** : `test_004_bons_commande.py` (T-29, §13.3) et campagne de mutation avec 0 survivant non qualifié (conventions techniques §7.1).

### 4.19 Écarts entre l'existant (migrations 001–004) et la V3.13 [PT-20]

Les migrations 001–004 sont appliquées et immuables. Le tableau liste, pour chaque mécanisme, le comportement actuel, la règle attendue et la correction nécessaire (migrations **correctives** M-A et M-B, §17.1 ; leur **contenu** reste une **proposition** non validée ; leur **place** dans la chaîne est validée : après la tranche 005 et avant la tranche 006, D-55). Les reconstructions de table suivent le protocole de reconstruction des conventions techniques §5.

| # | Fichier / table / mécanisme | Comportement actuel | Règle attendue | Correction nécessaire |
|---|---|---|---|---|
| 1 | `001` `clients.statut`, CHECK `a_rattacher ⇒ origine='import'`, `idx_clients_statut` | `actif`/`archive`/`a_rattacher` | aucun statut (INV-183) | M-A : reconstruire `clients` sans `statut` ni index, avec le protocole de reconstruction (PT-3) |
| 2 | `002` `fournisseurs.statut`, `idx_fournisseurs_statut` | `actif`/`archive` | aucun statut | M-A : supprimer l'index `idx_fournisseurs_statut`, puis supprimer la colonne (`DROP INDEX` puis `ALTER TABLE … DROP COLUMN`) — **sans reconstruction de `fournisseurs`** (vérifié sur SQLite 3.45.1 avec le DDL de 002, y compris avec une table `depenses` qui référence `fournisseurs`) (PT-3) |
| 3 | `001`/`002` : aucune garde de suppression ni d'immutabilité du `code` | suppression acceptée si non référencé ; code modifiable | conservation permanente, code immuable | M-A : triggers DELETE refusé et code immuable (PT-4) |
| 4 | `003` `devis.numero NOT NULL UNIQUE`, CHECK de statut sans `brouillon` | numéro obligatoire dès la création | brouillon sans numéro (INV-180) | M-A : reconstruire `devis` avec le protocole de reconstruction (pas d'`ALTER COLUMN` en SQLite) (PT-2) |
| 5 | `003` `tr_10_devis_modifiable`, `tr_10_devis_gele`, `tr_10_devis_refuse_annule` | modifiable si `en_attente` (**conforme**) ou `accepte` non gelé (**non conforme**) ; `refuse`/`annule` immuables (**`refuse` non rouvrable : non conforme**) | brouillon libre ; `en_attente` modifiable ; `accepte` verrouillé ; `refuse` verrouillé et rouvrable ; révisions (PT-21) | M-A : réécrire les triggers (PT-2, PT-17, PT-21) |
| 6 | `003` TR-11 (`devis_lignes`, `devis_ligne_garanties`) | refuse selon gel / statut (lignes modifiables en `en_attente` et `accepte` non gelé) | lignes libres en `brouillon` et en `en_attente` ; refusées en `accepte`, `refuse`, `annule` | M-A : réécrire |
| 7 | `003` `devis_lignes.devis_id` et `devis_ligne_garanties.ligne_id` en `CASCADE` ; aucun trigger DELETE sur `devis` | suppression de tout devis sans BC, quel que soit son statut, lignes perdues (contourne `tr_11_*_delete`) | seul le brouillon est supprimable (Q11, Q12) | M-A : `BEFORE DELETE` sur `devis` (brouillon seulement) ; cascade limitée au brouillon (PT-5) |
| 8 | `003` `frozen_at` (devis), TR-14, CHECK `frozen_at ⇒ accepte/annule` | gel progressif | devis verrouillé dès la validation | PT-8 |
| 9 | `003` `date_refus`, `motif_refus`, CHECK `refuse ⇒ date_refus` | sortie de `refuse` impossible | réouverture (INV-182) | PT-17 |
| 10 | `004` `bons_commande.devis_id UNIQUE NOT NULL` | 1 devis = 1 BC | 1 BC → N devis, 1 devis → 1 BC (INV-187) | M-B : table `bc_devis`, reprise des liens existants `bons_commande.devis_id` vers `bc_devis`, reconstruction de `bons_commande` pour retirer la colonne (colonne `UNIQUE` : `DROP COLUMN` impossible) (PT-6) |
| 11 | `004` `bons_commande.remise_*`, `acompte_*` | une remise et un acompte par BC | par devis (INV-189, INV-192) | M-B (PT-7) |
| 12 | `004` TR-12 (`devis_id` immuable ; gelé : liste blanche ; annulé : `client_id` et `updated_at`) | BC annulé figé jusqu'aux caches | caches recalculables après un avoir sur BC annulé (INV-188) | M-B : adapter (PT-16) |
| 13 | `004` TR-13 (`dl.devis_id <> b.devis_id` ; INSERT refusé si BC gelé ou annulé) | pas de lignes ajoutées après gel | ajout par rattachement de devis tant que le solde n'est pas rédigé | M-B : adapter (PT-6, PT-8) |
| 14 | `004` TR-17 (devis `accepte`, `client_id` du devis, naissance incl. `frozen_at`) | lit `devis_id` | lecture via `bc_devis` | M-B (PT-6) |
| 15 | `004` TR-18 `tr_18_devis_statut_avec_bc` (via `bons_commande.devis_id`) | un devis lié à un BC ne quitte `accepte` que si le BC est `annule` | idem, sans cascade, lecture via le lien | M-B : réécrire (PT-6) |
| 16 | `004` `frozen_at` du BC, TR-14, CHECK `termine ⇒ frozen_at`, `date_100_facture ⇒ frozen_at` | gel progressif | contenu contractuel stable dès la création | PT-8 |
| 17 | `004` `bc_ligne_garanties.ligne_id` en `CASCADE` | cascade depuis la ligne | pas de régénération : plus de cascade utile | M-B : `RESTRICT` — adaptation de `bc_ligne_garanties` par reconstruction (la clause `ON DELETE` ne se modifie pas en place) (PT-5) |
| 18 | `004` `bc_lignes` `UQ(bc_id, ordre)` | ordre unique par BC (un seul devis) | lignes de plusieurs devis dans un BC | aucune structure à changer ; le service numérote à la suite (PT-6) |
| 19 | `001` `numerotation_sequences`, TR-95, TR-96 ; spécification high-water (§5, §11.4) | compteur SQL posé dans la transaction de l'objet (restauré par un rollback) ; high-water écrit avant COMMIT ; l'attribution ne lit que le compteur : **un numéro réservé peut être réattribué après un rollback propre** (S1) ; un high-water absent n'est pas traité | aucun doublon, aucun numéro réservé réutilisé, trou accepté jamais récupéré | aucun DDL : correction de la spécification de service (PT-1, tranché le 2026-10-03) |
| 20 | Tests `001`–`004` | voir le rapport de mise à jour (références à `a_rattacher`, `statut`, CASCADE, `DELETE FROM devis`, `frozen_at`, `devis_id`) | cohérents avec V3.13 | adapter ou remplacer avec M-A et M-B ; nouvelle campagne de mutation (conventions §7.1) |
| 21 | (nouveau) | aucune table de révisions | `devis.revision` (NULL = version initiale), `devis.revision_en_cours`, table `devis_revisions`, `client_id` immuable après finalisation (INV-196, INV-180) ; la colonne `documents.revision` (§4.6) relève de la **future tranche Documents** | M-A : ajouts sur `devis` et `devis_revisions` (PT-21, validé sur le principe) ; **`documents` n'existe pas dans 001–004 : `documents.revision` n'est pas une tâche de M-A** |

---

## 5. `machine.db` (hors sauvegarde) [INV-02, INV-150 à INV-152, INV-171, INV-172]

Fichier séparé, `user_version` propre, migrations `machine/001_initial.sql`. **Aucune donnée commerciale.**
Les **secrets** (clé de licence, jetons Gmail) vivent dans le **coffre système** du système d'exploitation ; `machine.db` ne contient que des états non secrets et des références.

| Table | Colonnes |
|---|---|
| `utilisateur_local` (`id=1`) | `identifiant` TEXT NN UQ (non vide), `nom` (facultatif), `prenom` (facultatif), `mot_de_passe_hash` NN (encodage complet argon2id, jamais en clair), `deblocage_token_hash`, `deblocage_expire_at` (NULL ensemble), TS |
| `licence` (`id=1`) | `identifiant_installation` NN, `empreinte_machine_hash`, `derniere_verification_ok_at`, `derniere_tentative_at`, `grace_debut_at`, TS |
| `services_etat` (`id=1`) | `derniere_communication_ok_at`, `mise_a_jour_disponible`, TS |
| `stockage_racines` | `id` PK · `chemin_absolu` UQ NN · `actif` (0/1, index unique partiel `WHERE actif=1`) · TS |
| `preferences_sauvegarde` (`id=1`) | `auto_active` NN défaut 1, `frequence_minutes` INTEGER NN défaut 30 (≥ 1), `sauvegarde_fermeture` NN défaut 1, `derniere_sauvegarde_at` NULL, `derniere_sauvegarde_statut` NULL (`succes` / `echec`) ; `at` et `statut` NULL tant qu'aucune sauvegarde n'a eu lieu, renseignés ensemble ensuite |
| `gmail_etat` (`id=1`) | `connecte`, `compte_email`, `connecte_at` |
| `sequence_high_water` | `type_objet`, `annee`, `max_attribue`, `updated_at` ; PK `(type_objet, annee)` |

- **`stockage_racines`** : jamais supprimée. Changer de dossier de travail **crée une nouvelle racine active** ; les documents existants gardent leur racine. `chemin_absolu` n'est modifiable que par l'opération explicite de **remappage** (restauration sur une autre machine, dossier déplacé). [INV-106]
- **`sequence_high_water`** : plus haut numéro réservé par `(type_objet, annee)`, écrit par le service **avant** la création de l'objet (§11.4, PT-1 tranché) ; ne diminue jamais (`MAX`, garde de service, pas de trigger dans `machine.db`, D-30) ; il détecte une base métier régressée (restauration) et complète le compteur de la base métier. [INV-25, INV-179]
- **Aucun trigger dans `machine.db`** : INV-25 (`max_attribue` ne diminue jamais) et INV-106 (racines jamais supprimées) restent des **gardes de service** (D-30). L'identifiant d'installation n'a pas de garde d'immutabilité en base.

### 5.1 Initialisation au premier démarrage [INV-171, INV-172]
- Le DDL (`machine/001_initial.sql`) **ne crée aucune ligne**. Le service d'initialisation de `machine.db` crée les singletons `id=1` avec `INSERT OR IGNORE` : il n'écrase jamais une ligne existante (second démarrage, restauration d'une base métier, changement de version).
- `services_etat`, `gmail_etat` (`connecte=0`) et `preferences_sauvegarde` (valeurs par défaut du DDL : sauvegarde automatique activée, toutes les 30 minutes, sauvegarde à la fermeture activée, `derniere_sauvegarde_*` NULL) sont créées sans intervention de l'utilisateur. `licence` est créée avec un `identifiant_installation` généré par le service.
- **Compte local** : la création du compte (`identifiant` + mot de passe, `nom` et `prenom` facultatifs) est obligatoire au premier démarrage ; tant que `utilisateur_local` est vide, seul l'écran de création du compte est accessible. Le mot de passe est haché (argon2id) avant toute écriture ; `mot_de_passe_hash` n'accepte que l'encodage argon2id. [INV-171]
- `stockage_racines` (création à la sélection du dossier de travail, §11.5) et `sequence_high_water` (première attribution ou import, §10.6, §11.4) n'ont pas de singleton : leurs lignes sont créées par leur service.

---

## 6. Numérotation [INV-20 à INV-27]

| Objet | Format V6 | Séquence | Date qui donne l'année |
|---|---|---|---|
| Client | `CLI-0001` | CLI (année 0) | — |
| Fournisseur | `FOU-0001` | FOU (année 0) | — |
| Devis | `DEV-00001-26` (**attribué à la validation**, pas au brouillon : PT-2) | DEV | date de numérotation du devis (date de validation, PT-2 ; `date_creation` en V3.12) |
| BC | `BCD-00001-26` | BCD | `date_creation` |
| Acompte | `ACP-00001-26` | ACP | `date_emission` |
| Situation | `FAC-00001-26` | FAC | `date_emission` |
| Solde | `FAC-00001-26` | FAC (partagée avec situation) | `date_emission` |
| Avoir | `AVO-00001-26` | AVO | `date_emission` |
| PV initial | `PVR-00001-26` | PVR | `date_reception` |
| Levée de réserves | `PVR-00001-26-01`, `-02`… | suffixe = max + 1 par PV d'origine | — |
| Dépense | `DEP-00001-26` | DEP | `date_depense` |

- Le compteur repart à 1 chaque année ; la séquence est déterminée par l'année de la date métier. Plafond 99 999 (documents) et 9 999 (CLI/FOU) : erreur explicite au-delà. Années supportées pour les dates de numérotation : 2001 à 2099 (§2.2, INV-177, D-38).
- **BC** : le `yy` de `BCD-nnnnn-yy` est l'année de `bons_commande.date_creation` (jour d'enregistrement du BC), qui peut différer de l'année de `date_acceptation` ; le devis garde son propre `yy` (année de `devis.date_creation`). Rien de propre au BC dans le high-water ni à la restauration (§11.4). [INV-176]
- **Un numéro définitif n'est jamais attribué deux fois [VALIDÉ — INV-179, E-13, D-54].** Un numéro peut être consommé sans objet (crash ou rollback pendant la finalisation) : ce trou est acceptable et **n'est jamais récupéré** ; le compteur ne revient pas en arrière. Après COMMIT comme après réservation, un numéro n'est jamais réattribué, même après annulation de l'objet. Un objet non numéroté (devis brouillon, INV-180) ne consomme aucun numéro ; le devis reçoit son numéro à la finalisation. Il n'existe pas de facture brouillon (INV-185).
- **L'année (yy) d'une date de numérotation ne change jamais.** Pour le devis, la date de numérotation est fixée **à la finalisation** (PT-2) ; une fois numéroté, elle est immuable. `date_creation` (BC) est immuable ; `date_validite` reste modifiable. `date_depense` est modifiable dans la même année.
- **Chronologie continue** : pour ACP, FAC, AVO uniquement, `date_emission >= numerotation_sequences.derniere_date` de la séquence (TR-02). Elle ne s'applique pas à DEV, BCD, PVR, DEP.
- **Numéros historiques importés** : les devis, factures et PV `origine='import'` gardent le `numero` déjà remis au client (seule exemption de format, §10.4, INV-131) ; les contrôles de format de ces trois tables ne s'appliquent qu'à `origine='v6'`. BC et codes clients importés reçoivent du convertisseur des numéros au format V6 (ancien code dans `legacy_numero`, D-01).
- **Séquences importées** : le fichier d'import fournit `dernier_numero` (et `derniere_date`) par clé ; V6 en initialise `numerotation_sequences` et `sequence_high_water` ; un numéro sauté est acceptable, un numéro attribué n'est jamais réutilisé (§10.6, INV-135). Les clients et fournisseurs ne sont jamais supprimés (INV-183) ; leurs codes sont donc définitivement attribués dès la création.

---

## 7. Gel, cycle de vie et immutabilité [INV-31 à INV-36, INV-53]

### 7.1 Verrouillage et gel [INV-180 à INV-182, INV-186 ; remplace le « gel commercial » de la V3.12 — PT-8]

**Règle métier validée.** Le devis **accepté** est **verrouillé** (ainsi que sa dernière version), indépendamment de toute facturation : aucune modification directe de son contenu (INV-181) ; un devis `refuse` est verrouillé et rouvrable ; un devis `en_attente` numéroté reste modifiable par révisions (INV-196). Le contenu contractuel du BC est **stable dès sa création** et pendant tout son cycle, y compris lors du rattachement d'un devis supplémentaire, qui **ajoute** des lignes sans modifier les existantes (INV-186, INV-187). Il n'y a donc plus de modification du devis ou du BC après facturation à protéger par un « gel progressif ».

**Conséquences à traiter (PT-8, non validé)** : le mécanisme `frozen_at` de la V3.12 (posé par TR-15 au premier encaissement d'acompte, à la première situation ou au solde, sur devis et BC ; TR-14 ; CHECK `frozen_at ⇒ accepte/annule`, `termine ⇒ frozen_at`, `date_100_facture ⇒ frozen_at`) répondait au besoin « le devis/BC reste modifiable jusqu'au premier événement financier ». Ce besoin disparaît. Deux options techniques : (a) **suppression** de `frozen_at` et de TR-14/TR-15 (migration corrective, y compris retrait des CHECK qui l'utilisent) ; (b) **conservation** de la colonne comme marqueur d'information (« premier événement financier »), sans effet sur l'éditabilité. Choix non fait. La suppression automatique d'un acompte non réglé lors d'une modification de devis/BC (E-01, D-32) **n'existe plus** : plus de modification possible, donc plus d'annulation automatique.

### 7.2 Colonnes modifiables (cible V3.13)

| Table | Brouillon | Validé / en cours | Verrouillé / terminal |
|---|---|---|---|
| `devis` | brouillon : tout sauf `id`, `created_at` ; `numero` posé à la finalisation (PT-2) ; `client_id` immuable après finalisation | `en_attente` : contenu modifiable par révisions (PT-21) ; `revision`, `revision_en_cours` ; statut, dates et motifs liés au statut ; `updated_at` | `accepte` / `refuse` : statut, dates et motifs liés au statut, `updated_at` seulement ; `refuse → en_attente` autorisé ; `annule` terminal |
| `devis_lignes`, `devis_ligne_garanties` | insertion, modification, suppression | `en_attente` : insertion, modification, suppression (révisions) | aucune en `accepte`, `refuse`, `annule` |
| `bons_commande` (non annulé) | — (pas de brouillon de BC) | caches (`montant_deja_facture_ht`, `avancement`, `date_100_facture`, `statut`, `completed_at`), `montant_contractuel_ht` (au rattachement d'un devis), `date_debut`, `date_fin`, `cancelled_at`, `motif_annulation`, `updated_at` | — |
| `bons_commande` **annulé** (terminal) | — | `updated_at` ; **caches recalculables après avoir sur document existant** (PT-16) | — |
| `bc_lignes`, `bc_ligne_garanties` | — | **insertion seule**, par la création du BC ou le rattachement d'un devis (BC non annulé) ; ni UPDATE ni DELETE | aucune |
| `factures` | — (jamais brouillon) | aucune modification (ni annulation, ni rattachement de client : E-12, E-14) | aucune |
| `facture_lignes` | insertion dans la transaction d'émission uniquement | aucune | aucune |
| `reglements` | — | `cancelled_at`, `motif_annulation` (une fois) | — |
| `depenses` | — | modifiable tant que non annulée ; `cancelled_at`, `motif_annulation` (PT-14) | non annulée → annulée, une fois |
| `clients`, `fournisseurs` | — | tout sauf `id`, `code`, `created_at` ; **jamais supprimés** | — |
| `pv`, `garanties`, `historique` | — | aucune | aucune |
| `documents` | — | `chemin_relatif` | — |

Aucun `DELETE` n'est autorisé sur `bons_commande`, quel que soit l'état (TR-19, INV-174). Seul un devis `brouillon` peut être supprimé (INV-180). Un devis rattaché à un BC ne quitte `accepte` que si ce BC est annulé (TR-18, INV-175, INV-187) ; l'annulation du BC n'entraîne aucune annulation de devis (INV-188).

---


## 8. Triggers et index uniques [INV-05, INV-52, INV-53]

Les triggers ne servent que là où un `CHECK` ne suffit pas. Ils lèvent `RAISE(ABORT, 'INV-xx: …')` avec l'identifiant de l'invariant. Ils ne sont **exemptés pour aucune origine** : les données importées les traversent comme toute écriture V6 (INV-131).

| ID | Table / événement | Règle | INV |
|---|---|---|---|
| TR-01 | devis, BC, factures, pv, dépenses / UPDATE | `numero` immuable **une fois attribué** (devis brouillon : `numero` NULL puis attribué à la validation, PT-2) ; année de la date de numérotation immuable ; `date_creation` immuable (BC) | 23, 180 |
| TR-02 | factures / INSERT | ACP/FAC/AVO : `date_emission >= derniere_date` ; mise à jour de `derniere_date` | 24 |
| TR-10 | devis / UPDATE | **à réécrire (PT-2, PT-17, PT-21)** : brouillon libre ; `en_attente` : contenu modifiable **seulement si `revision_en_cours = 1`**, numéro et `client_id` immuables ; `accepte` et `refuse` : seulement statut, dates et motifs liés au statut, `updated_at` ; `refuse → en_attente` autorisé ; `annule` terminal ; transitions de `revision_en_cours` encadrées (validation : `revision` passe au numéro suivant et le snapshot existe déjà) ; acceptation refusée si `revision_en_cours = 1`. L'exception 003 « rattachement d'un client `a_rattacher` » disparaît avec le statut (INV-183). *(V3.12 : modifiable si `en_attente`, ou `accepte` non gelé)* | 31, 36, 180, 181, 182, 196 |
| TR-11 | devis_lignes, devis_ligne_garanties / INSERT, UPDATE, DELETE | **à réécrire (PT-2, PT-5, PT-21), en liste blanche** : autorisé seulement si le devis est `brouillon`, ou `en_attente` avec `revision_en_cours = 1` ; refusé dans tous les autres cas | 36, 180, 181, 196 |
| TR-12 | bons_commande / UPDATE | **à adapter (PT-6, PT-16)** : `id`, `created_at`, `numero`, `date_creation` immuables ; contenu contractuel (snapshots, `date_acceptation`) immuable ; `montant_contractuel_ht` modifiable seulement au rattachement d'un devis ; BC annulé terminal : seuls `updated_at` et les caches (après avoir sur document existant) évoluent. *(V3.12 : `devis_id` immuable, annulé : `client_id` et `updated_at` seulement)* | 36, 173, 186, 188 |
| TR-13 | bc_lignes, bc_ligne_garanties / INSERT, UPDATE, DELETE | **à adapter (PT-6, PT-8)** : INSERT seulement par création du BC ou rattachement d'un devis, BC non annulé, ligne de devis appartenant à un **devis rattaché à ce BC** ; UPDATE et DELETE toujours refusés. *(V3.12 : interdit si BC gelé ou annulé ; ligne du devis unique du BC)* | 36, 173, 175, 186 |
| TR-14 | devis, BC / UPDATE | `frozen_at` : NULL → valeur, jamais l'inverse — **obsolète si `frozen_at` est supprimé (PT-8)** | 34 |
| TR-15 | factures (situation, solde) et reglements (encaissement sur acompte) / AFTER INSERT | **obsolète (PT-8)** : pose de `frozen_at` et événement `gel` ; l'événement `gel` est retiré du catalogue (PT-15). *(planifié, jamais créé)* | 33 |
| TR-16 | factures / INSERT | **BC `en_cours` et non annulé pour acompte, situation, solde** ; `client_id` = celui du BC ; un **avoir** sur facture existante reste possible sur BC `annule` (PT-16 ; sur BC `termine` : à confirmer) | 47, 48, 188 |
| TR-17 | bons_commande / INSERT | devis `accepte` ; `client_id` = celui du devis ; état de naissance (§4.7) ; lecture du devis via le lien devis ↔ BC (PT-6) ; invariants locaux uniquement (la construction de la cohérence est au service, le diagnostic à CK-13) | 40, 48 |
| TR-18 | devis / UPDATE de `statut` | **à réécrire (PT-6)** : un devis rattaché à un BC (via `bc_devis`) ne quitte `accepte` que si ce BC est `annule` ; **aucune cascade** BC → devis | 175, 188 |
| TR-19 | bons_commande / DELETE | toujours interdit | 174 |
| TR-97 *(proposé, PT-4)* | clients, fournisseurs / DELETE, UPDATE de `code` | DELETE refusé ; `code` immuable | 183 |
| TR-98 *(proposé, PT-5)* | devis / DELETE | seul un devis `brouillon` est supprimable ; sinon refusé | 180 |
| TR-99 *(proposé, PT-6)* | bc_devis / INSERT, UPDATE, DELETE | INSERT : devis `accepte`, même client que le BC, BC non annulé ; UPDATE et DELETE refusés | 187 |
| TR-100 *(proposé, PT-21)* | devis_revisions / INSERT, UPDATE, DELETE | UPDATE et DELETE interdits (append-only) ; INSERT : le snapshot de la version initiale (`revision IS NULL`) une seule fois, puis `revision = max + 1` consécutif (`COALESCE(MAX(revision), 0) + 1`, comparaison par `IS`), seulement si le devis est `en_attente` avec `revision_en_cours = 1` ; l'index unique partiel garde en plus une seule version initiale | 196 |
| TR-20 | factures / UPDATE | **à réécrire** : aucun UPDATE (la facture validée est immuable, y compris `client_id` ; plus d'annulation) | 53, 185 |
| TR-21 | factures, facture_lignes / DELETE, facture_lignes / UPDATE | interdits | 6, 53 |
| TR-22 | factures / INSERT | acompte ≤ contractuel ; **un acompte par devis (PT-10)** ; situation : nette après ≤ contractuel et cumul cohérent ; solde = formule 3.2 ; aucun acompte/situation/solde si un solde est actif ; **unicité « active » : PT-9** | 55 à 58, 189 |
| TR-23 | factures / INSERT (avoir) | origine non avoir, même BC ; Σ avoirs ≤ montant origine ; aucun nouveau solde par avoir **hors avoir total (arbitrage B : une nouvelle facture reste possible après avoir total)** ; ne rouvre pas le BC aux devis (INV-187) | 58, 76, 185 |
| TR-24 | factures / UPDATE `cancelled_at` | **obsolète** : l'annulation de facture n'existe plus (E-14, INV-185). Le rôle de contrôle de cohérence glisse vers les règles de l'avoir (TR-23 : avoir total, avoir sur avoir interdit) *(planifié, jamais créé)* | 61, 77 |
| TR-30 | reglements / INSERT | encaissement → facture hors avoir active ; remboursement → avoir actif | 71 |
| TR-31 | reglements / INSERT | encaissement ≤ `reste_du` ; remboursement ≤ `credit` | 72, 74 |
| TR-32 | reglements / UPDATE, DELETE | UPDATE limité à `cancelled_*` une fois ; DELETE interdit | 70 |
| TR-33 | reglements / UPDATE `cancelled_at` | annulation d'encaissement refusée si `credit` < Σ remboursements actifs | 75 |
| TR-40 | pv / UPDATE, DELETE | interdits | 96 |
| TR-41 | pv / INSERT | levée : origine `reception_avec_reserves`, même BC, pas de levée sur levée ; suffixe et numéro cohérents | 96 |
| TR-50 | garanties / UPDATE, DELETE | interdits | 87 |
| TR-60 | historique / UPDATE, DELETE | interdits | 110 |
| TR-70 | documents / UPDATE, DELETE | UPDATE limité à `chemin_relatif` ; DELETE interdit | 105 |
| TR-80 | urssaf_referentiels / INSERT, UPDATE, DELETE | append-only ; `date_debut_effet` > toutes les précédentes | 121 |
| TR-81 | urssaf_profil / INSERT, UPDATE, DELETE | append-only ; `date_debut_activite` constante | 122 |
| TR-82 | urssaf_periodes / INSERT, UPDATE | non-chevauchement ; période verrouillée : seuls `statut` et `updated_at` | 123, 125 |
| TR-83 | urssaf_details, urssaf_periode_encaissements / INSERT, UPDATE, DELETE | interdits si la période est verrouillée | 126 |
| TR-84 | urssaf_periode_encaissements / INSERT | `facture_id` désigne un avoir ; `reglement_id` non annulé | 124 |
| TR-85 | urssaf_corrections / UPDATE, DELETE | interdits | 125 |
| TR-90 | import_anomalies / DELETE, UPDATE | DELETE interdit ; UPDATE limité à `statut` et `traite_at` (une fois) | 130 |
| TR-95 | numerotation_sequences / UPDATE | `dernier_numero` ne diminue jamais ; message `INV-22: numerotation_sequences.dernier_numero ne diminue jamais` | 22 |
| TR-96 | numerotation_sequences / DELETE | toujours refusé (direct, ou implicite par `INSERT OR REPLACE` si `recursive_triggers=ON`) ; posé par la migration 004 car 001 est immuable ; message `INV-22: numerotation_sequences ne se supprime jamais` | 22 |

Index uniques (hors UNIQUE de colonne, déclarés dans la table : `bons_commande.numero`, `bc_devis.devis_id` *(PT-6)*, `bc_lignes.devis_ligne_id`, …) : `uq_facture_acompte_actif`, `uq_facture_solde_actif`, `uq_situation_actif` *(obsolètes dans leur forme `WHERE cancelled_at IS NULL` ; remplacement : PT-9)*, `pv(origine_pv_id, suffixe)`, `garanties(bc_ligne_id, garantie_type)`, `documents(type_entite, entite_id, type_document, numero_version)`, `urssaf_periodes(date_debut)`, `urssaf_periodes(date_fin)`, `urssaf_periode_encaissements` (deux index partiels), `urssaf_details(periode_id)`.

Rappel : les caches du BC et la création des garanties sont faits par le **service**, pas par des triggers.
Autres règles de **service** sans trigger : règle des 30 jours des dépenses (INV-103), annulation du BC sans condition de facturation et sans cascade (INV-44, INV-188), rattachement d'un devis à un BC tant qu'aucun solde n'est rédigé/validé (INV-187), borne d'année des dates de numérotation (2001–2099 : INV-177, D-38), devis à 0.00 € non acceptable (INV-178), miroir devis ↔ BC après la création (INV-38, INV-175, contrôlé par CK-13).
Chaque trigger et chaque index est créé par la migration de la tranche qui crée sa table (§17.1) ; les écarts entre ces triggers déjà posés (001–004) et la V3.13 sont corrigés par des **migrations ultérieures** (§4.19, §17.1), jamais en réécrivant 001–004. Détail de la V3.12 : TR-90 et TR-95 par `metier/001_initial.sql` ; TR-01, TR-10, TR-11 et TR-14 du devis par `003_devis.sql` ; TR-01, TR-12, TR-13, TR-14, TR-17 et TR-19 du BC, ainsi que TR-18 (posé sur `devis`, mais qui suppose la table `bons_commande`) et TR-96 (posé sur `numerotation_sequences`, table de 001 qui reste inchangée), par `004_bons_commande.sql`.

---

## 9. Index

Un index **par clé étrangère** (l'index d'un `UNIQUE` qui commence par la FK en tient lieu : `prestation_garanties`, lignes et garanties de lignes de devis et de BC), plus les index de recherche :

- prestations(categorie_id) · prestations(actif) *(les index `clients(statut)` et `fournisseurs(statut)` de la V3.12 disparaissent avec les colonnes, §4.4)*
- devis(client_id) · devis(statut) · devis(date_creation) · devis_lignes(devis_id, ordre) · devis_lignes(prestation_id)
- bons_commande(client_id) · bons_commande(statut) · bc_devis(bc_id, rang) *(UNIQUE)* · bc_devis(devis_id) *(UNIQUE)* · devis(devis_origine_id) *(PT-7)* · factures(devis_id) *(PT-10)* · bc_lignes(bc_id, ordre) *(UNIQUE)* · bc_lignes(devis_ligne_id) *(UNIQUE)* · bc_lignes(prestation_id)
- factures(bc_id) · factures(client_id) · factures(origine_facture_id) · factures(type, date_echeance) · factures(date_emission)
- facture_lignes(facture_id, ordre) · facture_lignes(bc_ligne_id)
- reglements(facture_id) · reglements(date_evenement) · reglements(type)
- garanties(bc_id) · garanties(bc_ligne_id) · garanties(facture_declenchement_id) · garanties(date_fin_suivi)
- pv(bc_id) · pv(origine_pv_id)
- depenses(bc_id) · depenses(fournisseur_id) · depenses(categorie_id) · depenses(date_depense)
- planning_evenements(bc_id) · planning_evenements(date_debut) · planning_evenements(date_fin)
- bc_notes(bc_id) · documents(type_entite, entite_id)
- historique(bc_id) · historique(type_entite, entite_id) · historique(created_at)
- urssaf_periodes(profil_id) · urssaf_periodes(referentiel_version_id) · urssaf_periode_encaissements(periode_id) · (reglement_id) · (facture_id) · urssaf_corrections(periode_id)
- import_anomalies(categorie, statut)

---

## 10. Import de `import-v6.json` [INV-130, INV-131, INV-133 à INV-136, INV-153, INV-154, INV-161, INV-163, INV-165, INV-169, INV-170]

*(Révision V3.6 du 2026-09-30 : ce chapitre remplace l'ancien « Migration V2 → V6 ». Les règles de transformation propres à la V2 ne sont plus dans le modèle : elles sont portées par le convertisseur externe. Décision D-21, erratum E-09.)*

```
sauvegarde JSON V2  →  convertisseur externe  →  import-v6.json  →  import standard V6
   (source unique)      (porte toute la V2)      (contrat d'entrée)   (valide et insère)
```

### 10.1 Principes
- **V6 ne connaît pas la V2.** Aucun lecteur V2, aucun moteur de migration V2, aucune adaptation du schéma aux structures ou incohérences V2. La seule migration historique est la sauvegarde JSON V2 de l'unique utilisateur historique ; la V5 n'a jamais été distribuée et la V5.16 reste une référence fonctionnelle, technique et de catalogue, jamais une source. [INV-144]
- **Le seul format d'entrée est `import-v6.json`**, conforme au contrat du §10.3. Tout fichier non conforme est rejeté en bloc (lecteur strict : JSON invalide, `format` ou `contrat_version` inconnus, clé inconnue, référence croisée introuvable, montant hors précision, violation d'un CHECK ou d'un trigger). Il n'y a ni tolérance, ni réparation, ni quarantaine côté V6. [INV-153]
- **Deux temps** : (1) validation complète sans aucune écriture (*dry-run*) qui affiche les comptages et les anomalies déclarées ; (2) après confirmation, insertion dans **une seule transaction**, base métier **vide** uniquement (aucun client, devis, facture). Toute erreur annule tout. [INV-154]
- **Aucune exemption de règle métier** : l'import traverse les mêmes CHECK, triggers et index uniques que toute écriture V6, sans drapeau de session. Une seule exemption existe (format du `numero` historique, §10.4). [INV-131]
- **Règles de service** : la validation applique aussi `total_ht` > 0.00 pour tout devis `accepte` ou ayant un BC [INV-178]. La borne d'année 2001–2099 ne concerne que les dates de numérotation (§2.2, D-38) ; son application à l'import est définie par le contrat (P-04) et n'ajoute aucune limitation aux autres dates historiques.
- **Les valeurs dérivées ne sont jamais lues du fichier** : caches du BC (`statut`, `avancement`, `montant_deja_facture_ht`, `date_100_facture`, `completed_at`), `frozen_at` s'il subsiste (PT-8), états dérivés du §3.4. V6 les recalcule (§3.7). [INV-169]
- **Sources jamais modifiées**, aucune donnée supprimée en silence : ce que le convertisseur ne peut pas représenter est déclaré dans `anomalies` et conservé (§10.7). [INV-130]
- **Catalogue** : l'import n'ajoute pas le catalogue par défaut V6 ; le catalogue est celui du fichier (D-14). Les référentiels livrés avec V6 (listes fermées, catégories de dépenses D-18, référentiel URSSAF) sont initialisés comme pour toute installation.

### 10.2 Répartition des responsabilités

| Sujet | Convertisseur externe (hors V6) | V6 (import standard) |
|---|---|---|
| Lecture de la sauvegarde V2 | enveloppe, anciennes structures, clés optionnelles, colonnes décalées, renommages | ne lit jamais le format V2 |
| Normalisation | unités (D-13), statuts, types de ligne, catégories, dates, textes | vérifie les énumérations fermées du §2.5 |
| Catalogue, clients | catalogue V2, clients déduits des devis, rapprochements, recodage des codes | vérifie unicité et FK (aucun statut de client : `a_rattacher` n'existe plus, INV-183, E-12) |
| Devis, BC, factures | reconstruction des BC et des lignes, totaux et arrondis, composition des factures, snapshots (dont entreprise), `date_acceptation` estimée | applique toutes les formules du §3 et tous les triggers (dont TR-17 et TR-18) ; recalcul des caches |
| Paiements | traduction des statuts de paiement en règlements, factures sans statut | règles TR-30/31 comme en fonctionnement normal |
| PV, URSSAF | rattachement des PV à un BC ; saisies URSSAF V2 laissées hors du fichier | PV : TR-40/41 ; aucune donnée URSSAF acceptée (INV-161) |
| Compteurs historiques | récupération, réconciliation avec les numéros présents, conversion en `sequences` | initialise séquences et `sequence_high_water` (§10.6) |
| Anomalies | déclaration dans `anomalies` (`a_verifier`, `non_importe`) ; avertissements informatifs et rapport détaillé dans son propre rapport | stocke `import_anomalies`, affiche le bandeau (§10.7) |

Les règles de transformation V2 → `import-v6.json` (mapping complet, décisions D-13, D-15, D-16, D-17, D-19 et anciens INV-132, 155 à 160, 162) vivent dans le futur document `docs/migration/convertisseur-v2-vers-import-v6.md`. Le journal de `invariants.md` conserve l'énoncé de chaque règle transférée.

### 10.3 Contrat d'entrée `import-v6.json` (principes ; le schéma JSON détaillé est le point P-04)
- **Enveloppe** : `format` = `"import-v6"` ; `contrat_version` (entier) ; `genere_par` (nom et version du convertisseur) ; `genere_le` (timestamp) ; `source` (type, version et date de la sauvegarde d'origine, informatifs) ; `controles` (totaux de contrôle, §10.8).
- **Blocs acceptés** : `parametres_entreprise`, `categories_prestations`, `clients`, `prestations`, `devis` (avec `lignes`), `bons_commande` (avec `lignes`), `factures` (avec `lignes`), `reglements`, `pv`, `sequences`, `anomalies`.
- **Blocs refusés** : `fournisseurs`, `depenses`, `garanties` (et garanties de ligne), planning, notes, documents, `historique`, `urssaf_*`. La V2 ne les fournit pas ; les garanties naissent uniquement de la facturation V6 (INV-134) ; le profil URSSAF est saisi au premier lancement et aucune période n'est calculée avant (INV-161). Ouvrir un bloc supplémentaire = nouvelle `contrat_version`.
- **Lignes** : les lignes de devis et de BC du fichier ne portent aucune garantie de ligne ; `devis_ligne_garanties` et `bc_ligne_garanties` restent vides pour les objets importés. [INV-134, D-16]
- **Objets** : chaque objet porte un `ref` (identifiant local au fichier, unique par bloc) copié dans `legacy_id` ; les références croisées se font par `ref` ; V6 attribue les `id`. Optionnels : `legacy_data` (JSON, données sources non représentables en colonnes, jamais interprétées par V6) et `legacy_numero` (clients et BC seulement).
- **Faits saisis, pas valeurs dérivées** : statut d'un devis, dates, annulations, règlements, snapshots complets (BLOC-SNAP obligatoire), montants sous forme de chaînes décimales à la précision de leur famille (INV-15).
- **Numéros** : BC et codes clients au format V6 ; devis, factures et PV peuvent garder leur numéro historique (§10.4).
- **Cycle de vie importé (V3.13)** : un devis importé arrive dans l'un des statuts `en_attente`, `accepte`, `refuse`, `annule` — jamais `brouillon` (statut des seuls devis natifs non validés, INV-180) ; il est un devis numéroté : modifiable s'il est `en_attente`, verrouillé s'il est `accepte` ou `refuse` ; le snapshot de sa **version initiale** (`revision` NULL) est écrit par le service à l'import (PT-21). Un BC importé est rattaché à son devis (un seul devis dans la V2 : lien `bc_devis` de rang 1, PT-6) ; l'annulation d'un BC importé n'entraîne aucune annulation de devis (INV-188). Aucun client n'est importé avec un statut : un client à l'identité ambiguë est importé tel quel, jamais « à rattacher » (PT-3, variante : deux clients et une anomalie `a_verifier`). Une facture V2 « annulée » est représentée par la facture et un avoir total (PT-19, contrat à écrire dans le document du convertisseur).

### 10.4 Exemption unique : numéros historiques [INV-131]
Les devis, factures (acompte, situation, solde, avoir) et PV `origine='import'` conservent le `numero` qu'ils portaient quand ils ont été remis au client : un numéro déjà émis ne change jamais. Pour eux seulement, le format, le préfixe et l'année du `numero` ne sont pas contrôlés (non vide, unique, immuable par TR-01). Les CHECK de format restent conditionnés par `origine='v6'` sur `devis`, `factures` et `pv` uniquement.
**Tout le reste est appliqué sans exception** : `date_echeance >= date_emission`, `Σ lignes = total_ht`, caps d'acompte / situation / encaissement / remboursement / avoir (TR-22, 23, 31), chronologie ACP/FAC/AVO (TR-02), `bc_lignes.devis_ligne_id` NN, `garanties` NN. Un fichier qui viole une de ces règles est rejeté ; le convertisseur corrige ou déclare la donnée en `non_importe` avant génération.
Les index uniques ne sont pas exemptés non plus (deux acomptes actifs, deux BC pour un devis).

### 10.5 Ordre d'import
paramètres entreprise → catégories → clients → prestations → **devis en `en_attente` (+ lignes)** → puis application du statut final du devis → BC (+ lignes) → factures (+ lignes), insérées par `date_emission` puis `ref` croissants (TR-02 actif) → règlements par `date_evenement` croissante → PV → `sequences` → `anomalies` → recalcul des caches (§3.7) → CK-01 à CK-13 et totaux de contrôle → événement `import` dans `historique`.
TR-11 interdit l'insertion de lignes ou de garanties sur un devis déjà `refuse` ou `annule`. L'import doit donc construire le devis en `en_attente`, insérer ses lignes, puis poser le statut final et ses dates associées dans une étape distincte. Le gel est posé par TR-15 lors de l'insertion des factures et règlements, comme en fonctionnement normal. Un BC est inséré `en_cours` puis recalculé (`termine` si les conditions du §3.5 sont remplies).
**BC historique annulé** : il se reconstruit sans contournement du modèle. Le devis est porté à `accepte` ; le BC est inséré `en_cours` avec ses lignes (TR-17 exige un devis `accepte`) ; ses factures éventuelles sont insérées tant qu'il est `en_cours` (TR-16) ; le BC est ensuite annulé. **Le devis reste `accepte`** (aucune cascade, INV-188) sauf si le fichier le déclare explicitement `annule`, auquel cas le passage à `annule` est autorisé après l'annulation du BC (TR-18 adapté : BC d'abord). Rien n'est prévu dans la migration 004 pour contourner ces étapes ; l'ordre exact et les faits requis (dates, motif d'annulation) sont définis dans le contrat (P-04). `date_creation` et `date_acceptation` des BC importés sont des faits du fichier.

### 10.6 Séquences et numéros [INV-135, INV-25]
- Le convertisseur récupère les compteurs historiques V2 compatibles, les réconcilie avec les numéros réellement présents et les transmet dans `sequences` sous la forme `{type_objet, annee, dernier_numero, derniere_date}` (`derniere_date` pour ACP, FAC, AVO). Ces valeurs sont compatibles avec la numérotation V6 (§6).
- V6 initialise `numerotation_sequences` à partir de ces valeurs et `sequence_high_water.max_attribue := dernier_numero` pour chaque clé. Une clé absente vaut 0.
- Validation : `dernier_numero` ≥ plus grand numéro au format V6 du fichier pour la même clé (CLI/FOU : `annee = 0`), ≤ plafond (99 999 ; 9 999 pour CLI/FOU) ; `derniere_date` ≥ toute `date_emission` de la même clé.
- **Un numéro sauté est acceptable ; un numéro déjà attribué n'est jamais réutilisé.** Les numéros historiques hors format V6 (§10.4) n'alimentent pas les séquences.

### 10.7 Anomalies et traçabilité [INV-130, INV-163, INV-165]
- `anomalies` : `{type_entite, ref, categorie, motif, donnees}`. **`a_verifier`** : objet importé que l'utilisateur doit contrôler (`ref` obligatoire, `entite_id` renseigné à l'import) ; **`non_importe`** : donnée que le convertisseur n'a pas pu représenter, conservée en consultation dans `donnees`, sans objet métier créé.
- Tant qu'il existe une anomalie `a_verifier` au statut `a_traiter`, le tableau de bord affiche le bandeau « N éléments importés à vérifier » ; l'utilisateur la passe à `traite` (par exemple en saisissant le règlement d'une facture importée).
- Une facture importée non réglée est une facture ordinaire : elle compte dans la facturation, le reste dû et le CA engagé, jamais dans le CA encaissé ni l'URSSAF tant qu'aucun règlement n'est saisi (D-19). Aucun code V6 spécifique.
- Les avertissements purement informatifs (valeur normalisée, date estimée) restent dans le rapport du convertisseur : V6 ne les stocke pas.
- L'import écrit un événement `import` dans `historique` (acteur `import`) : `contrat_version`, convertisseur, source, comptages par bloc, nombre d'anomalies, empreinte SHA-256 du fichier.

### 10.8 Contrôles de fin d'import [INV-133]
Le bloc `controles` du fichier déclare comptages par bloc, Σ `total_ht` des factures actives et Σ `reste_du` attendu. V6 les compare aux valeurs recalculées ; tout écart, ou tout échec de CK-01 à CK-13, annule l'import complet. Après import : profil URSSAF à renseigner (message, pas une erreur).

### 10.9 Tests : deux périmètres séparés [INV-170]
- **Tests du convertisseur** (identifiants `TC-xx`, définis dans le document du convertisseur) : lecture de la V2, réparations, mapping, réconciliation des compteurs.
- **Tests de validation et d'import V6** (T-16, T-21, T-22 du §13) : jeu `import-v6.json` de référence, rejet atomique, séquences. Aucun test V6 ne lit un fichier V2.

---

## 11. Sauvegarde, restauration, dossier de travail [INV-140 à INV-144]

### 11.1 Sauvegarde
- Copie **cohérente** de la base métier par l'API Backup de SQLite ou `VACUUM INTO`. Jamais de copie brute du fichier en mode WAL.
- Le fichier ne contient **que** la base métier ; `machine.db` n'y est jamais.
- Un seul moteur pour sauvegarde manuelle, automatique et à la fermeture. Le dossier `Sauvegardes/` est créé à la première sauvegarde, sous la racine active.
- Préférences par défaut (`machine.db`, D-29) : sauvegarde automatique activée toutes les **30 minutes** (`frequence_minutes`), sauvegarde à chaque fermeture activée ; `derniere_sauvegarde_statut` NULL avant la première sauvegarde.
- JSON = **export** (consultation, archivage). Ce n'est pas un format de restauration. Une sauvegarde JSON V2 n'est pas restaurable dans V6 : elle est l'entrée du convertisseur externe, qui produit un `import-v6.json` (§10, INV-144).

### 11.2 Restauration
1. sélectionner la sauvegarde ;
2. valider le fichier ;
3. lire `user_version` (= `k`, rang de la dernière migration appliquée) : **refus** si `k` est supérieur au rang maximal supporté `N` de l'application ;
4. copier dans un fichier temporaire et y appliquer, **dans l'ordre**, les migrations de rang `k+1` à `N` (mêmes règles qu'une installation, conventions techniques §5 : une transaction par migration, `user_version` écrit avant le `COMMIT`) ;
5. `PRAGMA integrity_check` ;
6. `PRAGMA foreign_key_check` ;
7. **sauvegarde de sécurité** de la base courante ;
8. remplacement atomique de la base métier ;
9. contrôles post-restauration (requêtes CK du §14, dont **CK-13** devis ↔ BC), puis réouverture.

**Échec de la restauration** : si un contrôle d'intégrité obligatoire échoue, ou si CK-13 retourne une incohérence, la restauration est considérée comme **échouée** ; l'état restauré ne devient pas l'état de travail validé, et la sauvegarde de sécurité créée à l'étape 7 permet le retour à l'état précédent. Le détail technique (ordre exact, message, mode de retour) relève du module Backup/Restore ; aucune quarantaine ni récupération complexe n'est introduite ici.

`machine.db` reste inchangée : mot de passe local, licence, identifiant d'installation, racines et dossier de travail sont conservés. Événement `restauration` écrit dans `historique` après le remplacement.

### 11.3 Documents après restauration
Un `racine_stockage_id` inconnu de la machine courante rend les documents concernés « non localisables » : consultation des métadonnées possible, écran de **remappage** des racines proposé. Une restauration ne rend jamais BATORYA inutilisable parce qu'elle vient d'un autre ordinateur.

### 11.4 Numéros déjà émis et `sequence_high_water` [INV-25, INV-179, D-54] — règle validée ; mécanisme **PT-1 tranché le 2026-10-03**

Ce paragraphe sépare : (1) la règle métier validée ; (2) le mécanisme précédemment spécifié ; (3) son analyse selon l'ordre de priorité validé ; (4) le mécanisme retenu ; (5) ses garanties et limites ; (6) les détails d'implémentation restant à préciser.

**1. Règle métier validée (INV-179, D-54, E-13)**
- **Un numéro définitif ne doit jamais être attribué deux fois.** C'est la priorité absolue.
- Un numéro peut être consommé sans objet si un crash ou un rollback survient pendant la finalisation (exemple : `DEV-00041` existe, `DEV-00042` n'existe pas, `DEV-00043` est attribué ensuite). **Ce trou est acceptable et n'est jamais récupéré.** Interdit : `DEV-00042` attribué à un premier objet puis réattribué à un autre.
- Ordre de priorité des analyses : (1) absence absolue de doublon ; (2) impossibilité de réutiliser un numéro réservé ou consommé ; (3) protection contre rollback, crash et redémarrage ; (4) protection contre la restauration d'une ancienne base ; (5) un trou n'est jamais « récupéré » si cela augmente le risque de doublon. **Le compteur ne revient jamais en arrière.**
- *Cette règle remplace la lecture du premier envoi (« un rollback ne doit rien consommer, le numéro peut être réattribué »), abandonnée.*

**2. Mécanisme précédemment spécifié (V3.12)**
- Dans la transaction de création, le service incrémente `numerotation_sequences` par upsert (`INSERT … ON CONFLICT DO UPDATE … RETURNING`) : un rollback restaure ce compteur.
- Avant le COMMIT de la base métier, le service écrit `max(max_attribue, numéro)` dans `sequence_high_water` (`machine.db`).
- Restauration : `dernier_numero := max(restauré, max_attribue)` et `max_attribue := max(...)` ; avertissement listant les numéros « consommés » absents de la sauvegarde. Démarrage normal : `max_attribue > dernier_numero` est conservé et le trou journalisé (D-27). Import : `max_attribue := dernier_numero` du fichier (§10.6).

**3. Analyse selon les priorités (simulations)**

| Cas | Déroulé | Résultat | Conforme ? |
|---|---|---|---|
| S1 | upsert → n ; high-water := n ; **rollback propre** ; l'application continue sans redémarrer | le compteur SQL est restauré à n−1 ; l'attribution ne lit que ce compteur : **n est attribué à un autre objet** | **Non** (faille F1) |
| S2 | comme S1, puis redémarrage | compteur relevé à n ; prochain numéro n+1 ; trou n | Oui |
| S3 | high-water := n ; crash avant COMMIT | même état qu'en S2 | Oui |
| S4 | high-water := n ; COMMIT | `dernier_numero = max_attribue = n` | Oui |
| S5 | `machine.db` absente, neuve ou remplacée ; base métier plus ancienne | high-water vide : un numéro émis après la sauvegarde peut être réattribué | **Non** (faille F2, limite en 5) |
| S6 | échec d'écriture du high-water | si l'attribution continue : numéro non réservé | **Non** (faille F3) |

Conforme sans changement : `UNIQUE(numero)` par table (FAC partagé dans `factures`), TR-95, TR-96, formules de restauration et d'import. **Rejetées par la règle validée** : α (écrire le high-water après le COMMIT) et ρ (abaisser l'excédent au démarrage).

**4. Mécanisme retenu (PT-1 — tranché le 2026-10-03) : réservation committée avant l'objet**
Une seule fonction de service d'attribution, appelée **hors de toute transaction ouverte** :
1. `BEGIN IMMEDIATE` sur la base métier (verrou d'écriture conservé jusqu'au point 5).
2. Lire `c` (compteur, 0 si absent) et `h` (`max_attribue`, 0 si absent) ; `n = max(c, h) + 1` ; au-delà du plafond (99 999 / 9 999) : `ROLLBACK`, erreur, rien n'est écrit.
3. Dans `machine.db` : `max_attribue = MAX(max_attribue, n)` (upsert), validé durablement (`synchronous=FULL`). Échec : `ROLLBACK`, aucun numéro, aucun objet (**blocage**).
4. Dans la base métier : `dernier_numero = MAX(dernier_numero, n)` (upsert ; TR-95 n'interdit que les diminutions).
5. `COMMIT` : la réservation est acquise, **indépendante de l'objet**.
6. L'objet est créé dans une **transaction distincte** avec le numéro `n` ; un rollback de cet objet ne touche plus au compteur.
7. Le numéro n'est affiché ni remis (PDF, e-mail) avant le `COMMIT` de l'objet.
Après un rollback ou un crash aux points 3 à 6, `max(c, h) ≥ n` : le prochain numéro est au moins `n+1` (trou journalisé, jamais récupéré). Aucun DDL ; aucun trigger dans `machine.db` (D-30).

**5. Garanties et limites**
- Garanties : aucun numéro d'objet réattribué en cas de rollback avant COMMIT, de crash (avant COMMIT, après réservation, après COMMIT), de redémarrage, de `machine.db` perdue ou remplacée par une ancienne copie (tant que la base métier est à jour), de restauration de la base métier (tant que `machine.db` est intacte) ou de deux attributions concurrentes (le verrou d'écriture sérialise lecture, calcul et réservation). Dernier rempart : `UNIQUE(numero)`.
- **Limite irréductible (inhérente, acceptée le 2026-10-03)** : base métier restaurée plus ancienne **et** `machine.db` perdue ou remplacée en même temps (nouveau poste, par exemple). Aucune des deux bases ne contient alors la trace des numéros postérieurs à la sauvegarde ; un doublon est possible pour ces numéros. Protection minimale : à la restauration et au démarrage, si le high-water est vide ou inférieur au compteur alors que la base est non vide, **avertir** et relever `h := max(h, c, plus grand numéro présent dans les tables)`.
- Cas résiduel théorique sans effet visible : crash exactement entre les points 3 et 5 ; `n` n'est alors ni dans `c` ni dans `h` et peut être réutilisé, mais il n'a jamais été attribué à un objet ni remis.

**6. Détails d'implémentation restant à préciser (non des décisions métier)**
- Plancher complémentaire par balayage des PDF du dossier de documents : **le nommage des fichiers doit porter le numéro** (à vérifier) ; plancher saisi à la main en dernier recours.
- **Une seule instance** de l'application par dossier de travail (verrou).
- `synchronous=FULL` sur la connexion `machine.db`.
- Garde-fou : refus d'appeler l'attribution depuis une connexion déjà en transaction.
- Journalisation du trou (emplacement, libellé).

- **Import de `import-v6.json`** *(inchangé)* : `max_attribue` initialisé aux `dernier_numero` du fichier (§10.6).
- **Restauration** *(inchangée)* : voir point 2.


### 11.5 Changement de dossier de travail
BATORYA propose une sauvegarde immédiate, réalisée dans l'**ancien** dossier ; aucune copie automatique d'anciens fichiers ou d'anciennes sauvegardes ; nouvelle racine active dans `machine.db` ; SQLite ne bouge pas.

---

## 12. Licence, Gmail, erreurs [INV-150 à INV-152, INV-171]

- Vérification de licence tous les 3 mois ; en cas d'échec, message CDC §41 et **15 jours** d'utilisation complète ; ensuite : consultation et exports seuls, création, modification, suppression et facturation bloquées ; une vérification réussie rétablit tout. Ces états vivent dans `machine.db`.
- Les e-mails sont toujours envoyés manuellement ; jamais de faux envoi si Gmail n'est pas configuré ou si l'envoi a échoué.
- `ErrorService` ne crée aucune table métier ; le rapport est copiable/enregistrable et envoyable manuellement à `batorya.app@outlook.fr`.

---

## 13. Cas chiffrés de référence (à traduire en tests SQL/domaine)

| Cas | Données | Résultat attendu |
|---|---|---|
| C-01 | ~~Contractuel 1000.00 ; acompte 200.00 émis, non encaissé~~ | **OBSOLÈTE (E-10, INV-181, PT-8)** : plus de gel progressif ni d'annulation automatique d'acompte ; le devis accepté est verrouillé dans tous les cas (voir C-30). Conservé pour traçabilité. |
| C-02 | Acompte encaissé 50.00 (partiel) | `reste_du` acompte = 150.00 ; `etat_paiement = partiellement_reglee` *(la mention « gel immédiat » de la V3.12 est supprimée, PT-8)* |
| C-03 | Acompte 200.00 actif ; situation cumul 60 % | cible 600.00 ; nette avant = 200.00 ; **situation = 400.00** ; nette = 600.00 |
| C-04 | Nette avant solde = 600.00 | **solde = 400.00** ; `date_100_facture` = date du solde ; garanties créées |
| C-05 | Acompte payé 200, situation payée 400, solde payé 250 | `reste_du` solde 150.00 ; BC `en_cours` ; après +150.00 : Σ reste = 0 ⇒ **BC `termine`** |
| C-06 | Facture 1000.00, encaissé 600.00, avoir 500.00 | `absorbe = min(500, 400) = 400` ; `reste_du = 0.00` ; `credit = 100.00` ; remboursement max 100.00 |
| C-07 | Solde 400.00 impayé, avoir 100.00 | `reste_du` solde 300.00 ; aucun nouveau solde ; `date_100_facture` et garanties inchangées |
| C-08 | Acompte 200 + situation 800 = 1000 ; solde émis | **solde 0.00** ; 100 % facturé ; BC non terminé tant que l'acompte ou la situation reste due |
| C-09 | Contractuel 1000 ; acompte 200 ; situation 400 (cumul 60 %) ; avoir 100 sur la situation | nette = 500.00 ; nouvelle situation cumul 60 % = 600.00 − 500.00 = **100.00** refacturable |
| C-10 | Solde 400.00 impayé, avoir 400.00, autres factures payées | `reste_du` solde 0.00, Σ reste = 0 ⇒ BC `termine` (l'avoir absorbé réduit le reste dû) ; **aucun encaissement URSSAF** |
| C-11 | `reste_du` 150.00 ; encaissement 200.00 | refusé (TR-31) |
| C-12 | Annulation d'un encaissement alors que `credit` < Σ remboursements | refusée (TR-33) |
| C-13 | Facture 1000.00 payée ; avoir 100.00 ; remboursement 100.00 | `credit = 0.00` ; CA engagé du BC (contractuel 1000) = max(0, 900 − 900) = 0.00 |
| C-14 | 3.333 × 10 | ligne = 33.33 |
| C-15 | 2.5 × 10.005 | 25.0125 → 25.01 |
| C-16 | 0.125 et −0.125 | 0.13 et −0.13 (HALF_UP en valeur absolue) |
| C-17 | Ligne 100.00, remise 10 % | 90.00 |
| C-18 | Restauration d'une sauvegarde plus ancienne (FAC-00007-26 déjà émise, base restaurée à 00005) | séquence FAC-26 = 7 ; prochain numéro 00008 |
| C-19 | ~~Situation annulée, puis BC : annulation directe demandée~~ | **OBSOLÈTE (E-14, E-15)** : une situation ne s'annule plus (avoir) et l'annulation d'un BC n'est conditionnée par aucune facturation (voir C-36) |
| C-20 | ~~Solde annulé (impayé) puis réémis~~ | **OBSOLÈTE (E-14)** : remplacé par : avoir total sur le solde, puis nouvelle facture de solde avec nouveau numéro (arbitrage B) ; garanties inchangées ; `date_100_facture` à définir (PT-9). Voir C-33 |
| C-21 | BC arrivé à 100 % il y a 20 jours ; nouvelle dépense rattachée | rattachement normal, sans confirmation |
| C-22 | BC arrivé à 100 % il y a 45 jours ; nouvelle dépense rattachée | message indiquant que le BC est clôturé depuis 15 jours ; confirmation positive → rattachement accepté |
| C-23 | Devis accepté (`total_ht` 1000.00, `date_acceptation` 2026-09-25) ; BC créé le 2026-10-01 | `date_creation` = 2026-10-01 ; `date_acceptation` = 2026-09-25 (copie exacte) ; numéro `BCD-nnnnn-26` ; contractuel 1000.00 ; naissance : `en_cours`, caches `0.00`, non gelé |
| C-24 | Devis accepté le 2026-12-30 ; BC enregistré le 2027-01-02 | `date_acceptation` = 2026-12-30 ; `date_creation` = 2027-01-02 ; numéro `BCD-nnnnn-27` (séquence `BCD`, année 27) |
| C-25 | Devis à 0.00 € ; acceptation demandée | refusée par le service d'acceptation ; aucun BC créé |
| C-26 | BC annulé : tentative de repasser `en_cours`, de modifier le montant, une ligne ou le client ; tentative de rattacher un nouveau devis | modifications refusées (TR-12, TR-13) ; rattachement refusé (INV-187) ; *(V3.12 : « rattachement d'un client `a_rattacher` accepté » supprimé, E-12)* |
| C-27 | `DELETE` d'un BC (en cours, gelé ou annulé) ; `INSERT OR REPLACE` sur un BC existant | refusés dans tous les cas (TR-19, `recursive_triggers=ON`) |
| C-28 | Devis rattaché à un BC `en_cours` : passage à `refuse` ou `annule` ; puis annulation du BC | premier refusé (TR-18) ; l'annulation du BC est acceptée et **le devis reste `accepte`** (aucune cascade, INV-188) ; l'annulation ultérieure du devis par l'utilisateur, si elle est voulue, est alors permise (TR-18 : BC annulé) |
| C-29 | Base importée ou restaurée où le client, le total ou le statut du BC diffère de son devis | détecté par CK-13 (import : annulé ; restauration : échouée, §11.2) |
| C-30 | Devis `brouillon` : création, modification de ses lignes, suppression ; puis finalisation ; puis modification en `en_attente` ; puis acceptation et tentative de modifier une ligne, une remise, le client | brouillon : aucun numéro consommé, suppression acceptée ; finalisation : numéro `DEV-xxxxx-YY` attribué, passage à `en_attente` ; `en_attente` : modifiable, numéro inchangé ; DELETE refusé dès la finalisation ; `accepte` : toute modification de contenu refusée (INV-180, INV-181, INV-196, PT-2, PT-5) |
| C-31 | Devis refusé puis rouvert, puis modifié | `refuse` verrouillé (modification refusée) ; `refuse → en_attente`, numéro inchangé, contenu inchangé, événements `refus` puis `reouverture` (INV-182, PT-17) ; modifiable ensuite ; un devis `annule` ne se rouvre pas |
| C-32 | Client ou fournisseur : DELETE ; modification du `code` ; recherche d'un statut `archive` ou `a_rattacher` | DELETE refusé, code immuable, aucune colonne `statut` (INV-183, PT-3, PT-4) |
| C-33 | Facture validée : tentative d'annulation ; avoir total (acompte, situation ou solde) ; nouvelle facture du même type | annulation inexistante ; l'avoir total est accepté ; une nouvelle facture reçoit un **nouveau numéro** ; aucune facture brouillon n'existe (INV-185, arbitrage B, PT-9) |
| C-34 | BC avec devis A (acompte et 1 situation émis) ; devis B accepté du même client, rattaché avant tout solde | rattachement accepté ; contractuel = Σ `total_ht` (A, B) ; lignes et garanties de B copiées à la suite ; événement `rattachement_devis` ; un acompte distinct par devis (INV-187, INV-189, PT-6, PT-10) |
| C-35 | Solde rédigé/validé ; devis C accepté à rattacher ; avoir total sur le solde ; nouvelle tentative | rattachement refusé dans les deux cas : l'avoir ne rouvre pas le BC ; un BC annulé refuse aussi tout devis (INV-187) |
| C-36 | Annulation d'un BC portant acompte payé, situations et encaissements | acceptée (motif obligatoire) ; devis, factures, règlements, dépenses et historique conservés ; devis **non annulés** ; aucun nouvel acompte/situation/solde ; avoir sur document existant possible (INV-188, PT-16) |
| C-37 | Situation globale d'un BC à deux devis, saisie en % puis en montant | calcul en montants cumulés (acomptes et facturation nette antérieurs), jamais de double facturation ; mode, valeur saisie, avancement et montant HT conservés et figés (INV-190, PT-11) |
| C-38 | Q22 : ligne 10 × 100 € → 7 réalisés à 100 € et 3 abandonnés, ou 10 réalisés à 80 € ; Q25 : 4 000 € contractuels, 2 000 € réalisés, 2 000 € abandonnés | contractuel inchangé ; exécuté, abandonné, restant distinguables ; **chiffrage à valider selon le modèle d'exécution retenu (PT-12, À CONCEVOIR)** |
| C-39 | Remise globale : contractuel 10 000 €, remise 1 000 €, abandon 2 000 € | exécuté 8 000 € ; remise affectée 800 € ; net exécuté 7 200 € ; le devis reste à 10 000 € avec sa remise (INV-192 ; formule détaillée : PT-13) |
| C-40 | Dépense active annulée ; puis dépense créée sur un BC annulé | dépense annulée conservée avec numéro et relations, exclue des calculs actifs (principe : INV-200 ; formules détaillées : PT-14) ; la création sur BC annulé est acceptée (INV-193) |
| C-41 | Révisions : `DEV-00042` finalisé (version initiale) ; démarrage d'une phase de révision après confirmation ; plusieurs modifications de lignes ; validation (Révision 1) ; nouvelle phase puis validation (Révision 2) ; abandon d'une troisième phase ; relecture de chaque version ; acceptation | `DEV-00042` identique tout du long ; version initiale sans mention de révision, puis Révision 1 et Révision 2 ; une seule révision par phase (pas une par ligne) ; aucune « Révision 0 » ; chaque snapshot relu strictement identique à la version validée ; la phase abandonnée ne crée aucun snapshot, ne consomme aucun numéro (le suivant reste Révision 3) et rend le devis exactement à la Révision 2 ; acceptation refusée pendant `revision_en_cours=1` ; après acceptation, `devis.revision` identifie la version contractuelle (INV-196, PT-21) |
| C-42 | Trou de numérotation : `DEV-00041` existe ; crash ou rollback pendant la finalisation du suivant ; redémarrage ; nouvelle finalisation | le numéro `DEV-00042` n'est jamais réattribué ; `DEV-00043` est attribué ; trou journalisé, non récupéré ; sans redémarrage après un rollback propre, le numéro suivant est aussi > 42 (INV-179, D-54, PT-1 tranché) |

### 13.2 Tests d'intégrité T-01 à T-20 (repris de la V3.4 §99) [INV-167]

À couvrir avant le passage au DDL. T-01 à T-03 sont des tests de concurrence (deux transactions simultanées).

| Test | Énoncé | INV |
|---|---|---|
| T-01 | deux rattachements simultanés du même devis à deux BC → un seul réussit (`UNIQUE(devis_id)` de `bc_devis`, PT-6) | INV-40, INV-187 |
| T-02 | deux acomptes simultanés pour le même devis → un seul réussit (mécanisme d'unicité : PT-9, PT-10) | INV-52, INV-189 |
| T-03 | deux soldes simultanés pour le même BC → un seul réussit (mécanisme d'unicité : PT-9) | INV-52 |
| T-04 | restauration → mot de passe local inchangé | INV-142 |
| T-05 | restauration → licence inchangée | INV-142 |
| T-06 | restauration → dossier de travail inchangé | INV-142 |
| T-07 | modification du catalogue → garantie contractuelle inchangée | INV-37 |
| T-08 | ~~modification du BC après acompte non encaissé → acompte annulé~~ **OBSOLÈTE** (E-10) | ~~INV-35~~ |
| T-09 | ~~premier encaissement → gel irréversible~~ **OBSOLÈTE** (PT-8) | ~~INV-33, INV-34~~ |
| T-10 | ~~situation → gel~~ **OBSOLÈTE** (PT-8) | ~~INV-33~~ |
| T-11 | ~~solde → gel~~ **OBSOLÈTE** (PT-8) | ~~INV-33~~ |
| T-12 | avoir → pas de réouverture du cycle de facturation | INV-58 |
| T-13 | ~~annulation d'un avoir → recalcul financier~~ **OBSOLÈTE** (E-14 : un avoir n'est plus annulable) | ~~INV-79~~ |
| T-14 | avoir total sur le solde → garantie conservée | INV-87 |
| T-15 | levée de réserves → uniquement depuis un PV avec réserves | INV-96 |
| T-16 | import d'un `import-v6.json` de référence → reste dû recalculé = totaux de contrôle du fichier (V3.4 : « migration V2 → comparaison du reste dû ») | INV-133 |
| T-17 | période URSSAF verrouillée → modification directe refusée | INV-125 |
| T-18 | correction URSSAF → historique conservé | INV-125, INV-126 |
| T-19 | facture → somme des lignes égale au total | INV-54 |
| T-20 | numéro → jamais réattribué | INV-22 |

### 13.3 Tests ajoutés : validation et import V6 (T-21 à T-23), numérotation (T-24) — 2026-09-30 ; premier démarrage `machine.db` (T-25), DDL de la première tranche métier (T-26), fournisseurs (T-27), devis (T-28) — 2026-10-01 ; bons de commande (T-29) — V3.12 ; **propositions de tests T-30 à T-43 — V3.13 (2026-10-03)** [INV-170, INV-25, INV-171, INV-172, INV-04, INV-05, INV-14, INV-20, INV-21, INV-22, INV-130, INV-136, INV-173 à INV-195]

Ces tests ne lisent jamais un fichier V2. Les tests du convertisseur (`TC-xx`) sont définis dans son propre document.

| Test | Énoncé | INV |
|---|---|---|
| T-21 | `import-v6.json` non conforme (clé inconnue, `ref` introuvable, montant hors précision, règle de trigger violée) → rejet total, base métier inchangée | INV-153, INV-154 |
| T-22 | séquences importées → `numerotation_sequences` et `sequence_high_water` initialisés ; premier numéro V6 = `dernier_numero + 1` ; aucun numéro attribué réutilisé ; un saut accepté | INV-135, INV-25 |
| T-23 | import sur base non vide refusé ; document `origine='import'` au numéro historique accepté, même numéro en `origine='v6'` refusé | INV-131, INV-154 |
| T-24 | numérotation (PT-1 tranché) : rollback propre de la création de l'objet **sans redémarrage** → numéro réservé jamais réattribué (S1) ; crash entre la réservation et le COMMIT, puis redémarrage → trou journalisé, prochain numéro > numéro perdu (S3) ; échec d'écriture du high-water → aucun numéro, aucun objet (S6) ; `machine.db` vide ou ancienne copie, base métier à jour → aucun doublon ; appel depuis une transaction ouverte refusé ; injection de panne à chaque étape de la fonction : `max(c, h)+1` supérieur à tout numéro vu ; aucun numéro réutilisé dans aucun cas. | INV-25, INV-22, INV-179 |
| T-25 | premier démarrage sur `machine.db` vierge : `user_version=1`, aucune ligne après la migration ; initialisation → `licence`, `services_etat`, `gmail_etat` (`connecte=0`), `preferences_sauvegarde` (1, 30, 1, NULL, NULL) créées avec `id=1` ; création du compte (identifiant, hash argon2id, nom/prénom facultatifs) ; compte sans identifiant, identifiant vide ou hash non argon2id refusé ; second démarrage : `INSERT OR IGNORE` ne modifie ni le compte, ni `identifiant_installation`, ni les préférences changées ; aucun trigger dans la base | INV-171, INV-172, INV-151, INV-08 |
| T-26 | migration `metier/001_initial.sql` sur base vide : `user_version=1` posé par le runner, 7 tables `STRICT` sans aucune ligne, 3 triggers, `foreign_key_check` vide ; `id` jamais réutilisé ; `numerotation_sequences` : attribution par upsert, plafonds 99 999 / 9 999, TR-95 (aucune diminution), `annee=0` ⇔ CLI/FOU ; `import_anomalies` : CHECK de catégorie, TR-90 (DELETE refusé, seule transition `a_traiter` → `traite`) ; `clients` : code `CLI-NNNN` sans exception, `a_rattacher` ⇒ `import`, BLOC-IMP+ ; `prestations` : DL, listes fermées, BLOC-IMP ; suppression d'une prestation → `prestation_garanties` supprimées en CASCADE seulement | INV-04, INV-05, INV-14, INV-20, INV-21, INV-22, INV-130, INV-136 |
| T-27 | `test_002_fournisseurs.py` — DDL de la tranche Fournisseurs : `fournisseurs` (code `FOU-NNNN`, statut `actif`/`archive`, aucune donnée initiale, aucune FK) ; séquence FOU (`annee=0`, plafond 9 999, numéro jamais réutilisé) ; high-water hors base métier | INV-04, INV-05, INV-06, INV-10, INV-20, INV-21, INV-22, INV-25, INV-100 |
| T-28 | `test_003_devis.py` — DDL de la tranche Devis : `devis`, `devis_lignes`, `devis_ligne_garanties` ; 11 triggers (TR-01, TR-10, TR-11, TR-14) et 4 index ; numéro `DEV` (format, année de `date_creation`, immuabilité, numéro historique libre en `origine='import'`) ; dates réelles (`GLOB` + `date(x) IS x`) ; familles décimales ; BLOC-SNAP et BLOC-IMP ; rattachement d'un client `a_rattacher` ; suppression d'un devis sans BC en CASCADE ; non-régression de 001 et 002 | INV-04, INV-05, INV-06, INV-10, INV-11, INV-14, INV-20, INV-21, INV-22, INV-23, INV-30, INV-31, INV-34, INV-36, INV-37, INV-49, INV-131, INV-134, INV-136 |
| T-29 | `test_004_bons_commande.py` (à écrire avec la migration 004), par groupes : **création et naissance** (BC valide, chaque écart d'état refusé, devis non `accepte`, client différent, second BC pour un devis) ; **FK et suppression** (devis avec BC non supprimable, devis sans BC supprimé en CASCADE, DELETE d'un BC refusé quel que soit l'état, `INSERT OR REPLACE` refusé avec `recursive_triggers=ON`, `bc_lignes.bc_id` en `RESTRICT`, aucun `ON UPDATE`) ; **numérotation** (format `GLOB` explicite, année issue de `date_creation` et non de `date_acceptation`, immuabilité, unicité, séquence `BCD`, plafond, TR-95) ; **protection de la séquence** (les messages de `tr_95` et `tr_96` portent tous deux `INV-22` : chaque assertion vérifie aussi le libellé, « ne diminue jamais » pour TR-95 et « ne se supprime jamais » pour TR-96, afin de distinguer les deux protections ; TR-96 : `DELETE` direct d'une séquence refusé ; `INSERT OR REPLACE` avec un `dernier_numero` inférieur refusé, la ligne existante restant intacte ; vérification que la valeur existante de `dernier_numero` n'a pas diminué ; `UPDATE` diminuant le compteur toujours refusé par TR-95 ; l'upsert maîtrisé `INSERT … ON CONFLICT(type_objet, annee) DO UPDATE` reste autorisé lorsqu'il augmente correctement le compteur, ainsi que l'`INSERT` d'une nouvelle séquence ; témoin : sans `recursive_triggers=ON`, TR-96 refuse le DELETE direct mais pas le REPLACE) ; **lignes** (`UNIQUE(bc_id, ordre)`, `UNIQUE(devis_ligne_id)`, ligne d'un autre devis refusée, familles décimales, régénération, index `prestation_id`) ; **états** (CHECK de statut avec variantes NULL, BC annulé terminal avec l'exception du rattachement, cohérence sûre des caches, caches écrits en un seul UPDATE) ; **gel** (liste blanche du §7.2, irréversibilité, lignes et garanties figées si le BC est gelé ou annulé) ; **devis ↔ BC** (TR-18 : sortie d'`accepte` refusée, autorisée si le BC est annulé ; CK-13 vide sur données cohérentes et détectant chaque divergence provoquée, dont contractuel ≠ `total_ht` que TR-17 ne refuse pas ; comportements de 003 sans BC inchangés sur la chaîne 001 → 004) ; **garanties de ligne** (unicité, CASCADE depuis la ligne, immuabilité, indépendance du catalogue) ; **import** (BLOC-IMP+, `legacy_numero = numero` refusé, numéro hors format refusé même en `origine='import'`) ; **dates et timestamps** (calendrier exhaustif, `date_fin >= date_debut` avec NULL) ; **précision monétaire** D2 et P2 ; **cas limites** (FK vers une table future absente, `recursive_triggers`). Campagne de mutation : 0 survivant non qualifié (conventions techniques §7.1) | INV-04 à INV-06, INV-10, INV-14, INV-20 à INV-23, INV-31, INV-34, INV-36, INV-37, INV-40, INV-46, INV-48, INV-22, INV-136, INV-164, INV-173 à INV-176 |
| T-30 | numérotation : deux attributions concurrentes → deux numéros distincts ; base métier restaurée plus ancienne avec `machine.db` intacte → pas de doublon ; `machine.db` vide face à une base métier non vide → avertissement et relèvement prudent (limite du §11.4) ; `UNIQUE(numero)` ; abandon d'un brouillon sans numéro | INV-179, INV-22, INV-25 |
| T-31 | réouverture `refuse → en_attente` : numéro et contenu inchangés ; `refuse` verrouillé tant qu'il n'est pas rouvert ; `annule` terminal ; événements `refus` et `reouverture` | INV-182 |
| T-32 | devis `brouillon` : numéro NULL, lignes modifiables, suppression acceptée ; devis finalisé : DELETE refusé, contenu modifiable en `en_attente` ; devis `accepte` : modification de contenu refusée ; `CHECK (statut='brouillon') = (numero IS NULL)` | INV-180, INV-181 |
| T-33 | clients et fournisseurs : DELETE refusé, `code` immuable, aucune colonne `statut` ; `INSERT OR REPLACE` couvert par `recursive_triggers=ON` | INV-183 |
| T-34 | rattachement multi-devis : même client, devis `accepte`, BC non annulé, aucun solde ; copie des lignes et garanties ; contractuel = Σ `total_ht` ; refus après solde, y compris après avoir ; CK-13 et CK-14 | INV-187, INV-189 |
| T-35 | BC annulé : conserve devis (non annulés), factures, dépenses, historique ; refuse acompte, situation, solde, devis ; avoir sur document existant | INV-188 |
| T-36 | facture validée : aucun UPDATE/DELETE ; aucune facture brouillon ; avoir total puis nouvelle facture du même type avec nouveau numéro | INV-185 |
| T-37 | `ON DELETE` examiné par relation : CASCADE limitée au brouillon de devis (PT-5) ; `bc_ligne_garanties` RESTRICT ; objet numéroté jamais supprimé ; relation historique jamais redirigée | INV-05, INV-06, INV-184 |
| T-38 | situation globale d'un BC multi-devis (% et montant) en montants cumulés ; valeurs figées (PT-11) | INV-190 |
| T-39 | exécution et remise globale : à écrire **après** conception de PT-12 et PT-13 (cas C-38, C-39 comme exemples d'entrée) | INV-191, INV-192 |
| T-40 | dépense annulée : conservée, exclue des calculs actifs (INV-200 ; PT-14 pour le détail des formules) ; création sur BC annulé acceptée | INV-193, INV-200 |
| T-41 | historique métier : événements significatifs écrits ; table append-only (PT-15) | INV-194 |
| T-42 | révisions (PT-21) : snapshot de la version initiale écrit à la finalisation (un seul par devis) ; démarrage, validation (Révision 1, 2…) et relecture ; modification de contenu refusée hors phase de révision ; abandon : tables vivantes = dernier snapshot validé, aucun snapshot créé, numéro non consommé ; validation sans modification significative refusée ; refus et annulation pendant une révision : abandon ; `client_id` immuable après finalisation ; `devis_revisions` append-only ; acceptation refusée si `revision_en_cours=1` ; devis accepté : aucune phase de révision ; devis importé : snapshot de la version initiale ; `documents.revision` jamais substitué à `numero_version` ; CK-15 vide sur données cohérentes et détectant chaque divergence provoquée | INV-196, INV-180, INV-181 |
| T-43 | **représentation de la version initiale (`revision IS NULL`, décision figée)** — tests futurs, non écrits : (1) `revision = 0` refusé par `CHECK (revision IS NULL OR revision >= 1)` ; (2) exactement une version initiale par devis est possible ; (3) une deuxième version initiale est refusée (index unique partiel `WHERE revision IS NULL`) ; (4) la version initiale est retrouvée par `IS NULL`, y compris avec un paramètre NULL lié (`IS ?`) ; (5) la dernière version validée est retrouvée par la requête canonique lorsque `devis.revision IS NULL` ; (6) la prochaine révision depuis la version initiale vaut 1 (`COALESCE`) ; (7) les révisions suivantes valent 2, 3… ; (8) une séquence avec trou est refusée (TR-100) ; (9) la même révision ne peut être créée deux fois (`UNIQUE(devis_id, revision)`) ; (10) `documents.revision` : NULL pour la version initiale d'un document de devis, 1, 2… ensuite, jamais 0 ; (11) NULL signifie « version initiale » uniquement pour un document de devis, et « sans version » pour les autres types (`type_entite <> 'devis'` ⇒ NULL) ; en complément : un devis sorti de `brouillon` sans snapshot initial est détecté (TR-10, CK-15) ; une requête écrite avec `revision = NULL` ne retrouve rien (test témoin de la règle d'écriture) | INV-196 |

**Adaptation des tests existants (migrations 001–004, §4.19)** : T-27 (statut `actif`/`archive` des fournisseurs) et les tests `a_rattacher` de 001 ; T-28 (`rattachement d'un client a_rattacher`, « suppression d'un devis sans BC en CASCADE », TR-10/TR-11 selon la V3.12, `frozen_at`) ; T-29 (`second BC pour un devis`, « devis sans BC supprimé en CASCADE », `devis_id`, régénération, gel et liste blanche du §7.2, « BC annulé terminal avec l'exception du rattachement », `bc_ligne_garanties` CASCADE). Les migrations 001–004 restant immuables, ces tests décrivent l'état de chaque migration prise isolément ; les comportements V3.13 sont testés sur la chaîne complète avec M-A et M-B (propositions, §17.1) ; nouvelle campagne de mutation sur les triggers réécrits.

---

## 14. Ce que SQLite ne garantit pas (contrôlé par service + requêtes CK)

| Règle | Garde |
|---|---|
| `Σ facture_lignes = total_ht`, `Σ lignes = total` de devis/BC | service à l'émission + CK-05 |
| Montants exacts de situation et de solde | service (formules §3) + tests C-03/C-04 |
| Caches BC (`statut`, `avancement`, `date_100_facture`, …) | service financier unique, en un seul UPDATE + CK-06 |
| Miroir devis ↔ BC à la création **et à chaque rattachement** (liste S, lignes 1:1, garanties de ligne, statuts, contractuel = Σ `total_ht`) | service (INV-38, INV-187) + **CK-13**, requête de diagnostic : jamais un CHECK, jamais un trigger |
| Aucun devis rattaché après la rédaction/validation du solde (INV-187) | service (porte du rattachement) + **CK-14** ; trigger possible avec la tranche Facturation |
| Unicité « active » d'acompte / solde / situation sans `cancelled_at` | **À CONCEVOIR (PT-9)** : service, trigger, ou état dérivé |
| Exécution et remise globale (INV-191, INV-192) | **À CONCEVOIR (PT-12, PT-13)** : rien de garanti en base tant que le schéma n'existe pas |
| Conservation des clients/fournisseurs ; suppression d'un devis `brouillon` seulement | triggers proposés TR-97, TR-98 (PT-4, PT-5) |
| Année 2001–2099 des seules dates de numérotation (D-38) | service (import : contrat P-04) |
| Devis à 0.00 € non acceptable (INV-178) | service d'acceptation, et validation d'import |
| Suppression d'un BC | TR-19 + FK `RESTRICT` + `recursive_triggers=ON` ; le service n'émet aucun DELETE |
| `date_echeance = date_emission + délai du snapshot` | service |
| Création idempotente des garanties | service + `UQ` |
| Existence des `entite_id` polymorphes, `racine_stockage_id` | CK-09, CK-10 |
| Recalcul des périodes URSSAF | service ; `ca_encaisse = Σ retenu` : CK-08 |
| Insertion de lignes de facture hors transaction d'émission | service ; détection CK-05 |

Requêtes de contrôle exécutées : en test, après import, après restauration, et sur demande :
CK-01 numéros uniques, et conformes au format V6 sauf devis/factures/PV `origine='import'` · CK-02 séquences ≥ max des numéros au format V6 · CK-03 FK (`foreign_key_check`) · CK-04 factures sans lignes · CK-05 `Σ lignes = total_ht` · CK-06 caches BC = recalcul · CK-07 garanties d'un BC ayant un solde actif · CK-08 `ca_encaisse` = Σ retenu · CK-09 `entite_id` existants · CK-10 racines de documents connues · CK-11 périodes URSSAF sans chevauchement · CK-12 (à l'import) totaux de contrôle du fichier = totaux recalculés · CK-13 cohérence devis ↔ BC · CK-14 rattachement multi-devis (un devis dans un seul BC ; devis rattachés `accepte`, du même client que le BC ; aucun devis rattaché après un solde ; `montant_contractuel_ht` = Σ `total_ht` des devis rattachés).

**CK-13** est une **requête de contrôle**, pas une contrainte : un `CHECK` ne compare pas des lignes d'autres tables. Elle renvoie les lignes en violation de la règle du miroir (INV-175), **pour chaque devis rattaché à un BC via `bc_devis` (PT-6)** : `client_id` différent entre devis et BC ; `montant_contractuel_ht` ≠ Σ `total_ht` des devis rattachés ; `remise_*`, `acompte_*`, snapshots (contenus et versions) ou `date_acceptation` du devis d'origine différents ; lignes ou garanties de ligne non identiques (1:1) ; devis rattaché `annule` alors que son BC n'est pas `annule` ; devis `accepte` sans BC ; contractuel à `0.00`. *(V3.12 : « BC `annule` sans devis `annule` » est **supprimé** — l'annulation d'un BC n'annule pas ses devis, INV-188.)* **CK-14** (nouvelle, V3.13) vérifie le rattachement multi-devis : un devis dans un seul BC ; aucun devis rattaché après la rédaction du solde du BC (tranche Facturation) ; BC non annulé pour tout rattachement postérieur à son annulation. Ces requêtes sont exécutées après import (un résultat non vide annule l'import), après restauration (étape 9 du §11.2 : une incohérence fait échouer la restauration), dans les tests et sur demande. Elles ne modifient jamais les données.

**CK-15** (nouvelle, PT-21) : requête de contrôle des révisions. Pour tout devis dont le `statut` n'est plus `brouillon` : **le snapshot de version initiale (`revision IS NULL`) existe**, puis un snapshot par révision numérotée de 1 à `revision`, sans trou ; si `revision_en_cours = 0`, le contenu vivant (devis, lignes, garanties de ligne) est identique au snapshot de la dernière version validée (même requête que l'écriture du snapshot) ; un devis `accepte`, `refuse` ou `annule` a `revision_en_cours = 0`.

---

## 15. Décisions ajoutées par cette rédaction (D-01 à D-20 validées le 2026-09-29 ; D-21 à D-27 du 2026-09-30 ; D-28 à D-31 du 2026-10-01 ; D-32 et D-33 du 2026-10-01 ; D-34 à D-39 du 2026-10-01, audit BC ; **D-40 à D-54 du 2026-10-03, arbitrages Q1–Q27 et A–D ; D-55 du 2026-10-04, versionnement des migrations**)

| ID | Décision par défaut | Alternative | Statut |
|---|---|---|---|
| D-01 | Codes clients importés au format `CLI-0001…` (sans exception dans V6), ancien code en `legacy_numero` ; recodage fait par le convertisseur (il n'y a pas de fournisseur à importer) | conserver `CLI-001` V2 (ambiguïté avec `CLI-0001`) | **Validée** 2026-09-29 ; exécution transférée au convertisseur (D-21) |
| D-02 | Timestamps en TEXT ISO UTC `…SSS Z` (retour à la V3.3) | entiers Unix ms | **Validée** 2026-09-29 |
| D-03 | Types de planning : `intervention` et `travaux` rétablis (CDC §26), `bc_id` obligatoire ; `conge`/`indisponibilite` sans BC | types V3.4 seuls | **Validée** 2026-09-29 |
| D-04 | Secrets (licence, jetons Gmail) dans le coffre système ; `machine.db` = états non secrets | tout dans `machine.db` | **Validée** 2026-09-29 |
| D-05 | **[REMPLACÉE le 2026-10-03 par D-46 / E-15]** Annulation directe du BC **interdite** dès qu'une facture autre qu'un acompte non réglé existe (V3.4 conservé), plus strict que CDC §17 (voir errata E-07) | autoriser avec solde impayé et sans situation | **Validée** 2026-09-29 |
| D-06 | Avoirs absorbant toute la dette : BC `termine` si Σ reste dû = 0 (formule appliquée à la lettre) | exiger au moins un encaissement | **Tranchée** par l'arbitrage 1 (2026-09-29) |
| D-07 | `situation_numero` rétabli sur `factures` (PDF reproductible) | dérivé au rendu | **Validée** 2026-09-29 |
| D-08 | `delai_paiement_jours` entre 0 et 60 | plage libre | **Validée** 2026-09-29 |
| D-09 | Remise « montant » de ligne = montant total de la ligne (non unitaire) | remise unitaire | **Validée** 2026-09-29 |
| D-10 | `urssaf_referentiels.date_debut_effet` strictement croissante | insertion rétroactive autorisée | **Validée** 2026-09-29 |
| D-11 | `historique.acteur` (`utilisateur`/`systeme`/`import`) remplace `auteur` | colonne `auteur` libre | **Validée** 2026-09-29 |
| D-12 | Catégories de dépenses en table `categories_depenses` | énumération CHECK | **Validée** 2026-09-29 |
| D-13 | Unités V6 : `u`, `ens`, `ml`, `m2`, `m3` (liste fermée, reste dans V6) ; normalisation V2 (`m²`/`M2`→`m2`, `U`→`u`, `mL`→`ml`, `forfait`→`ens` ; inconnue → `u` + avertissement) | liste ouverte, autres unités (`h`, `kg`…) | **Validée** 2026-09-29 ; normalisation transférée au convertisseur (D-21) |
| D-14 | Catalogue par défaut V6 (204 prestations, ELE-008 exclue) chargé seulement en « nouvelle installation » (jeu de données, pas migration de schéma) ; import de `import-v6.json` = catalogue du fichier, sans catalogue par défaut, sur base vide seulement (la réparation du catalogue V2 est faite par le convertisseur) | charger les deux (collisions de codes `PLO-001`, `ELE-001`, `PEI-001`, `ISO-001`) | **Validée** 2026-09-29 |
| D-15 | `date_acceptation` V2 estimée = date de la première facture liée, à défaut date du devis ; `date_refus` = date du devis | quarantaine des devis sans date | **Validée** 2026-09-29 ; règle transférée au convertisseur (D-21) |
| D-16 | Aucune garantie créée pour les BC déjà soldés en V2 (côté V6 : le contrat n'accepte aucune garantie, `garanties` sans exemption) ; liste dans le rapport du convertisseur | créer les garanties depuis la date du solde | **Tranchée** 2026-09-29 : aucune garantie recréée ; liste transférée au convertisseur (D-21) |
| D-17 | Statut inconnu et non vide (devis, facture, conformité PV) → jamais importé avec une valeur par défaut : le convertisseur le déclare en `non_importe` (V6 n'a plus de quarantaine, il rejette tout fichier non conforme) | import avec valeur par défaut | **Validée** 2026-09-29 ; règle transférée au convertisseur (D-21) |
| D-18 | Catégories de dépenses initiales (table `categories_depenses`, modifiables) : Matériaux, Sous-traitance, Location de matériel, Carburant et déplacements, Outillage et consommables, Assurances, Frais administratifs et comptabilité, Autre | énumération figée | **Validée** 2026-09-29 |
| D-19 | Facture V2 sans statut → importée non réglée, comptée dans la facturation, le reste dû et le CA engagé (pas dans le CA encaissé ni l'URSSAF), listée « À vérifier » (anomalie `a_verifier` du fichier, bandeau du tableau de bord côté V6, §10.7) | quarantaine | **Validée** 2026-09-29 ; production de l'anomalie par le convertisseur, affichage par V6 |
| D-20 | **[COMPLÉTÉE le 2026-10-03 : plus de régénération du BC (INV-38 modifié) ; `bc_ligne_garanties` → RESTRICT proposé, PT-5]** Lignes de BC : pas de colonne `active`, régénération avant gel, lignes de facture en `RESTRICT` (écart 1 de §18) | rétablir `active`, `updated_at` et identifiants stables (V3.4) | **Validée** 2026-09-29 |
| D-21 | **Migration V2 externalisée** : V2 JSON → convertisseur externe → `import-v6.json` → import standard V6. V6 ne lit pas la V2, n'adapte pas son schéma à la V2 ; V5.16 n'est pas une source | moteur de migration V2 dans V6 (V3.5, §10 ancien) | **Validée** 2026-09-30 (brief Rémy) — erratum E-09 |
| D-22 | `migration_rapports` supprimée (trace = événement `import` de `historique`) ; `migration_quarantaine` remplacée par `import_anomalies` (`a_verifier`, `non_importe`), sans lot d'import | conserver les deux tables génériques | **Validée** 2026-09-30 (intégrée au modèle V3.6 et confirmée par Rémy) |
| D-23 | BLOC-MIG devient BLOC-IMP : `origine` (`v6`/`import`), `legacy_id` (= `ref` du fichier), `legacy_data` ; `migration_id` supprimé ; `legacy_numero` seulement sur `clients` et `bons_commande` ; bloc retiré de `fournisseurs`, `garanties`, `depenses` | garder `migration_id` et le bloc partout | **Validée** 2026-09-30 (intégrée au modèle V3.6 et confirmée par Rémy) |
| D-24 | Exemption unique : `numero` historique libre pour devis, factures et PV `origine='import'` (numéro déjà remis au client) ; toutes les autres exemptions sont supprimées (échéance, Σ lignes, caps, chronologie, NOT NULL) | tout renuméroter au format V6 (`legacy_numero`) | **Validée** 2026-09-30 (intégrée au modèle V3.6 et confirmée par Rémy) |
| D-25 | Lecteur strict : fichier non conforme rejeté en bloc, jamais réparé ni mis en quarantaine par V6 ; valeurs dérivées (caches BC, gel) jamais lues du fichier | lecteur tolérant (V3.5) | **Validée** 2026-09-30 (brief Rémy) |
| D-26 | Compteurs V2 compatibles récupérés par le convertisseur, transmis dans `sequences` ; V6 initialise séquences et high-water ; un saut est acceptable, aucune réutilisation | séquences V6 vides après migration (V3.5) | **Validée** 2026-09-30 (brief Rémy) |
| D-27 | **[BUT CONSERVÉ — mécanisme précisé et tranché le 2026-10-03 : voir §11.4, D-54, PT-1]** `max_attribue` ne diminue jamais automatiquement ; s'il dépasse `dernier_numero` au démarrage, il est conservé, le trou est accepté et journalisé (corrige la contradiction du §11.4 de la V3.6). *Le premier envoi du 2026-10-03 (alternatives α/ρ) est abandonné.* | abaisser `max_attribue` à `dernier_numero` (risque de réattribuer un numéro déjà attribué) | **Validée** 2026-09-30 (brief Rémy) |
| D-28 | Compte local **obligatoire** au premier démarrage : `utilisateur_local.identifiant` TEXT NOT NULL UNIQUE (non vide), `mot_de_passe_hash` NOT NULL (argon2id) ; `nom` et `prenom` facultatifs | profil local facultatif, mot de passe facultatif (V3.7) | **Validée** 2026-10-01 (réponse de Rémy) |
| D-29 | Préférences de sauvegarde par défaut : automatique activée, toutes les 30 minutes (`frequence_minutes` NOT NULL défaut 30, remplace `frequence_jours`), sauvegarde à la fermeture activée ; `derniere_sauvegarde_statut` NULL avant la première sauvegarde, puis `succes` / `echec` | fréquence en jours, sauvegarde automatique désactivée par défaut | **Validée** 2026-10-01 (réponse de Rémy) |
| D-30 | `machine.db` sans trigger : INV-25 et INV-106 restent des gardes de service (conforme au registre) ; pas de garde d'immutabilité sur `identifiant_installation` ; singletons jamais insérés par le DDL, créés par le service d'initialisation (`INSERT OR IGNORE`) | triggers de protection en base ; singletons insérés par la migration | **Validée** 2026-10-01 (réponse de Rémy) |
| D-31 | **Dépenses tardives sur BC non annulés** : à compter de `date_100_facture`, rattachement normal pendant 30 jours calendaires ; passé ce délai, le BC est considéré clôturé pour les nouvelles dépenses mais reste toujours rattachable après une confirmation simple indiquant le nombre de jours écoulés ; aucun déblocage, autorisation ou délai maximal supplémentaire ; **un BC annulé n'est pas concerné** : aucun délai ni confirmation (INV-199, cadrage 005) | blocage définitif après 30 jours ; procédure de déblocage dédiée | **Validée** 2026-10-01 (réponse de Rémy) |
| D-32 | **[SANS OBJET depuis le 2026-10-03 : `a_rattacher` supprimé, E-12 / D-43]** **Rattachement client sur devis** : un devis `refuse`, `annule` ou gelé reste immuable sauf réaffectation de `client_id` lorsque l'ancien client est `a_rattacher` ; snapshots et autres données restent inchangés | interdire le rattachement après refus/annulation | **Validée** 2026-10-01 |
| D-33 | **[REMPLACÉE le 2026-10-03 par D-41 / D-44 : seul un devis `brouillon` est supprimable ; E-10]** **Suppression d'un devis sans BC** : suppression physique autorisée ; lignes et garanties en cascade. Dès qu'un BC existe, la FK future `bons_commande.devis_id` en `RESTRICT` protège le devis | interdire toute suppression physique par trigger | **Validée** 2026-10-01 |
| D-34 | **Ordre des tranches de migration métier** : Devis → BC → Dépenses → Facturation (factures) → Règlements → Garanties → PV → Planification. Les autres éléments (documents, paramètres, historique, URSSAF) ne sont pas positionnés dans cet ordre : ils seront traités dans leur contexte propre. Les dépenses ne dépendent que des BC, des fournisseurs (002) et des catégories (001) | ordre de la V3.11 : BC → factures → règlements → garanties → PV → dépenses → planning | **Validée** 2026-10-01 (réponse de Rémy, audit BC) |
| D-35 | **[MODIFIÉE le 2026-10-03 : exception « rattachement client `a_rattacher` » supprimée ; annulation sans condition ni cascade, D-46]** **Cycle de vie du BC** : un BC `annule` est terminal (jamais `en_cours`, jamais réactivé, aucune modification commerciale ; seule exception : rattachement d'un client `a_rattacher`) ; aucun BC n'est jamais supprimé physiquement, garanti en base (TR-19, FK `RESTRICT`, `bc_lignes.bc_id` en `RESTRICT`) ; l'annulation est la seule sortie sans facturation complète | BC annulé réactivable ; suppression d'un BC sans facture ; `bc_lignes.bc_id` en CASCADE (V3.11) | **Validée** 2026-10-01 (réponse de Rémy, audit BC et C-R3) |
| D-36 | **[MODIFIÉE le 2026-10-03 : un BC peut avoir plusieurs devis (D-47) ; plus de régénération]** **Cohérence devis ↔ BC** : un devis ayant un BC ne quitte `accepte` que si ce BC est `annule` (TR-18) ; les données structurantes (liste S) restent identiques côté devis et côté BC, maintenues par le service (copie exacte, mêmes versions) ; à la création, le **service** construit la cohérence (vérifie le devis accepté, copie les données contractuelles, crée le BC, initialise les caches, dans la transaction) ; le SQL ne porte que des invariants locaux du BC (TR-17 : devis `accepte`, `client_id`, état de naissance) et TR-18 ; **CK-13** est un contrôle diagnostique inter-tables (après import, à la restauration, en test, à la demande), jamais un CHECK ni un trigger ; ni trigger de miroir ligne à ligne ; un devis à `0.00` € ne peut pas être accepté (service, INV-178) | triggers de synchronisation continue ; CHECK inter-tables ; comparaison complète BC ↔ devis dans TR-17 | **Validée** 2026-10-01 (réponse de Rémy, audit BC et C-R2) ; formulation précisée le 2026-10-02 (seconde passe) |
| D-37 | **Dates du BC** : `date_creation` = date du jour de l'enregistrement du BC (son année détermine le `yy` du numéro `BCD`) ; `date_acceptation` = date contractuelle héritée exactement du devis ; elles peuvent différer ; aucune règle d'ordre entre elles | `date_creation` = `date_acceptation` ; règle `date_acceptation >= date_creation` | **Validée** 2026-10-01 (réponse de Rémy, audit BC et C-R1) |
| D-38 | **Périmètre de la borne 2001–2099** : la borne ne concerne que les dates dont l'année est exploitée par les conventions de numérotation annuelle (`yy`), au niveau du **service** là où elle est nécessaire ; aucune contrainte générale sur les autres dates, aucune limitation artificielle des dates historiques ou importées, aucun CHECK, aucun changement de la validation calendaire `GLOB` + `date(x) IS x` | borne sur toutes les dates de type D ; CHECK d'année dans le DDL | Périmètre corrigé le 2026-10-02 (seconde passe, instruction de Rémy) ; **Validée** avec la migration 004 le 2026-10-02 |
| D-39 | **Écritures SQLite** : `PRAGMA recursive_triggers=ON` fait partie des PRAGMA de connexion ; `INSERT OR REPLACE` et `REPLACE` sont interdits par convention (`INSERT`, `UPDATE` ou UPSERT explicitement maîtrisé) | laisser `recursive_triggers` désactivé (un REPLACE supprime la ligne sans déclencher les triggers `BEFORE DELETE`) ; s'en remettre à la seule convention pour `numerotation_sequences` (précision technique : TR-96, migration 004) | **Validée** 2026-10-01 (réponse de Rémy, C-R3) ; précisée le 2026-10-02 par TR-96 |
| D-40 | **Remplacée par D-54** (numérotation : « jamais attribué deux fois ») — la lecture « consommé au COMMIT, un rollback ne consomme rien » du premier envoi est abandonnée. Conservé de D-40 : un objet non numéroté (brouillon) ne consomme aucun numéro | — | **Remplacée** 2026-10-03 (second envoi) |
| D-41 | **Cycle de vie du devis** : `brouillon` (sans numéro, modifiable, supprimable tant que jamais finalisé) → finalisation (numéro `DEV-xxxxx-YY` attribué et consommé) → `en_attente` (**numéroté et modifiable**, numéro inchangé) → `accepte` (verrouillé, dernière version) / `refuse` (verrouillé, rouvrable vers `en_attente`, même numéro) ; aucun module « avenant » ; nouveau devis pour un travail supplémentaire (art. 1193 du Code civil et documentation DGCCRF vérifiés par Rémy). *Précisé par D-53.* | devis `en_attente` verrouillé dès sa validation (lecture du premier envoi, abandonnée) | **Validée** 2026-10-03 (Q3, Q4, Q5, Q10, Q14, Q17, arbitrage A ; second envoi) |
| D-42 | **Références historiques stables** : un numéro attribué est immuable ; une relation historique ne change jamais silencieusement de cible ; tout objet numéroté est conservé | suppression des objets non utilisés | **Validée** 2026-10-03 (Q9, Q10, Q16) |
| D-43 | **Clients et fournisseurs** : conservation permanente, code immuable, ni archivage, ni actif/inactif, ni suppression, ni `a_rattacher` | archivage et rattachement de client (D-32) | **Validée** 2026-10-03 (Q2, Q13) |
| D-44 | **`ON DELETE` examiné relation par relation** : pas de `RESTRICT` partout (la suppression d'un brouillon doit rester possible) ; CASCADE réservée aux données strictement dépendantes sans valeur historique autonome | RESTRICT systématique | **Validée** 2026-10-03 (Q12) ; mécanismes : PT-5 |
| D-45 | **Facture validée** : aucun brouillon persistant ; jamais annulée ni supprimée ; correction par avoir ; nouvelle facture après avoir total (arbitrage B) | annulation de facture (E-14 remplace) | **Validée** 2026-10-03 (Q8, B) ; mécanisme : PT-9 |
| D-46 | **BC annulé** : conservé avec ses devis (non annulés automatiquement), factures, avoirs, dépenses et historique ; plus de cycle commercial normal ; annulation sans condition de facturation | cascade vers les devis ; annulation conditionnée à la facturation (D-05) | **Validée** 2026-10-03 (Q18, Q21, correction PT-6) |
| D-47 | **Plusieurs devis sur un BC** : rattachement tant que le solde n'est pas rédigé/validé ; un avoir ultérieur ne rouvre pas ; garanties : principe du CDC §24 inchangé, ligne supprimée = plus de garantie | un devis par BC ; « facturé à 100 % » comme porte | **Validée** 2026-10-03 (Q17, Q23 corrigé) ; mécanisme : PT-6, PT-7 |
| D-48 | **Acompte par devis ; situation globale au BC en % ou en montant ; un règlement = une facture** | acompte unique par BC ; règlement multi-factures | **Validée** 2026-10-03 (Q19, Q20, Q24, Q27, arbitrage C) ; mécanismes : PT-10, PT-11 |
| D-49 | **Exécution distincte du contractuel ; remise globale au prorata de la valeur exécutée/facturée** (principes) | réécriture du devis ; remise recalculée | **Principes validés** 2026-10-03 (Q22, Q25, Q26, arbitrage D) ; **schéma et formules À CONCEVOIR** (PT-12, PT-13) |
| D-50 | **Dépense** : corrigeable puis annulable ; conservée ; sans fournisseur archivé | suppression ; aucune annulation | **Validée** 2026-10-03 (Q7) ; mécanisme : PT-14 |
| D-51 | **Historique métier utile** (quoi, quand, avant/après, pourquoi, qui) | journal exhaustif | **Validée** 2026-10-03 (Q15) ; catalogue d'événements : PT-15 |
| D-52 | **Pointage salarié hors périmètre** d'Essentiel V6 (BATORYA Entreprise) ; rien n'est créé | module de pointage | **Validée** 2026-10-03 (INV-195) |
| D-53 | **Précisions du cycle de vie et révisions** : le devis `en_attente` n'est plus un point à décider (numéroté, modifiable). Le devis initial est la **version initiale**, **jamais une « révision 0 »** ; les révisions commencent à Révision 1. Toute modification du contenu présenté au client ou à impact quantitatif/financier crée une phase de révision ; une modification technique sans impact n'en crée pas. `notes` imprimées = contenu de la révision. `client_id` immuable après finalisation. Révision abandonnée = jamais historique, aucun numéro consommé, retour exact à la dernière version validée. Validation sans modification significative : pas de révision. Refus ou annulation pendant une révision : révision abandonnée. `documents.revision` identifie la version ; `numero_version` ne la remplace pas. `bc_devis.revision_acceptee` supprimée (redondante). Pas de reprise d'une ancienne révision à ce stade. **Stockage : A raffiné — tables vivantes + `devis_revisions` append-only (snapshots complets)** | pas de révision ; révision par modification élémentaire ; « révision 0 » ; tables relationnelles versionnées | **Validée** 2026-10-03 (second envoi pour les règles ; troisième envoi pour le stockage sur le principe et les 10 décisions) ; **représentation de la version initiale figée le 2026-10-03 : `revision IS NULL`** (`ordre_version` non retenu, aucune vue) ; autres détails = propositions |
| D-54 | **Numérotation — priorité absolue** : un numéro définitif n'est jamais attribué deux fois ; un trou après crash ou rollback est acceptable et n'est jamais récupéré ; le compteur ne revient pas en arrière après un rollback. Ordre des priorités : aucun doublon, aucun numéro réservé réutilisé, protection rollback/crash/redémarrage, protection contre la restauration d'une ancienne base, trous non récupérés. **Mécanisme : PT-1 (tranché le 2026-10-03 : réservation committée avant l'objet, double garde compteur + high-water)** | α, ρ (rejetées) ; compteur restauré par rollback et réattribué (première lecture) | Règle **validée** 2026-10-03 (second envoi) ; mécanisme **tranché** 2026-10-03 (PT-1) |
| D-55 | **Versionnement des migrations** (V-1 à V-5) : ordre métier réservé 001 → 010 ; deux catégories de noms, tranche `NNN_<objet>.sql` et corrective `NNNx_<objet>.sql` (rattachée à la dernière tranche exécutée avant elle) ; **`PRAGMA user_version` = rang** dans la chaîne ordonnée, pas numéro de fichier ; chaîne **append-only** ; `user_version` écrit dans la transaction de la migration avant `COMMIT` ; M-A et M-B = correctives `005a`/`005b` après 005 et avant 006 ; protocole de reconstruction de table et évolution du runner = chantier technique distinct de 005 | numérotation séquentielle simple (tranches renumérotées) ; `schema_version` dans chaque fichier (seconde source de vérité) | **Validée** 2026-10-04 (réponse de Rémy) |

**Décisions existantes complétées par la V3.12** (leur énoncé d'origine reste valable) :
- **D-16** : en plus de l'absence de garantie native, le contrat n'accepte aucune garantie de ligne ; un BC importé n'a aucun `bc_ligne_garanties` (INV-134). La contradiction de la V3.11 (§10.5 : « devis (+ lignes + garanties de ligne) ») est corrigée.
- **D-20** : `bc_lignes.bc_id` passe de `CASCADE` à `RESTRICT` (écart à l'énoncé d'INV-05 et au §4.7 de la V3.11, tracé au journal de `invariants.md`, D-35) et `UNIQUE(devis_ligne_id)` s'ajoute à `UNIQUE(bc_id, ordre)`. L'absence de colonne `active` et la régénération avant gel sont inchangées.
- **D-31** : inchangée sur le fond ; la règle des 30 jours est une règle de service (INV-103) et n'est plus présentée comme un trigger (« TR-01 bis » retiré du §8). Précisée le 2026-10-04 : elle ne vise que les BC non annulés (INV-199, cadrage 005).
- **D-33** : la FK `bons_commande.devis_id` est précisée (`UNIQUE`, `RESTRICT`, sans `ON UPDATE`) ; le devis d'un BC, même annulé, n'est jamais supprimable (D-35).
- **V3.13 (2026-10-03)** — D-05, D-32, D-33 : remplacées ou sans objet (voir marques en tête de ligne) ; D-20 et D-35/D-36 : complétées ; D-27 : but conservé, mécanisme à corriger (PT-1) ; D-40 à D-54 : ajoutées.

### Points à figer avant le DDL (P-xx)
- **P-01** *(clos)* : unités figées par D-13 ; catégories de prestations = 13 du catalogue par défaut V5.16 + `Revêtement` ; le mapping des types de planning est sans objet (aucune donnée de planning n'est importée) ; liste initiale des catégories de dépenses figée par D-18.
- **P-02** *(clos sur l'échantillon)* : quantités et prix unitaires V2 ≤ 2 décimales ; totaux V2 non arrondis jusqu'à 5 décimales et artefacts flottants ⇒ INV-15. Le convertisseur refait la mesure sur la sauvegarde réelle ; V6 rejette tout montant hors précision (INV-15).
- **P-04** *(ouvert)* : schéma JSON détaillé du contrat `import-v6.json` (champs, types, exemples) ; à écrire avec le document du convertisseur, avant l'implémentation de l'import. Bloque l'import, pas le DDL des tables (D-22 est validée : `import_anomalies` est figée). Deux points y sont ajoutés par la V3.9 (§4.17, points 7 et 10) : liste des valeurs admises de `import_anomalies.type_entite` (définie par le contrat, sans CHECK en base), et sort du `ref` des objets du bloc `categories_prestations` (BLOC-IMP absent des listes). La V3.12 y ajoute (§4.7, §10.5) : reconstruction d'un BC historique annulé sans contournement du modèle, `date_creation` et `date_acceptation` des BC importés comme faits du fichier, règle de service appliquée à la validation (devis `accepte` > 0.00 €) et traitement de la borne d'année de numérotation (D-38).
- **P-03** *(clos)* : une prestation V5.16 porte une seule garantie ; le modèle multi-garanties est conservé, le catalogue par défaut n'en utilise qu'une.

---

## 16. Matrice de non-régression (règles déjà perdues une fois)

| Règle perdue ou fragilisée dans une version | Rétablie ici |
|---|---|
| Garde-fous d'avoir, d'encaissement, d'annulation (V3.3 → V3.4) | INV-61, 72, 74 à 77 · TR-22 à TR-33 |
| `UNIQUE(bons_commande.devis_id)`, index partiels acompte/solde (V3.3 → V3.4) | INV-40, 52 |
| `origine` et `migration_id` sur devis/BC/factures/PV (V3.4) | §2.4 (BLOC-IMP : `origine` conservé, `migration_id` supprimé par D-23), INV-136 |
| Colonnes `total_ht` du devis, `devis_ligne_id` (V3.4) | §4.6, §4.7 |
| Snapshots entreprise, mentions, conditions, délai (V3.1 → V3.2) | INV-30, 32 |
| Quarantaine → traçabilité d'import (`import_anomalies`), restauration, `user_version` (V3.1 → V3.2) | INV-130, 165, 141, 08 |
| Exemptions `origine='migration'` de la première rédaction V3.5 (supprimées le 2026-09-30) | INV-131 (exemption unique), §10.4 |
| Machine vs sauvegarde (V3.1 → V3.2, V3.3) | INV-02, 141 |
| Séquences : `annee` NULL cassant l'UNIQUE (V3.2) | INV-21 (`annee` défaut 0) |
| Numéro de PV initial sans suffixe (V2) | INV-26, 96 |
| Formules d'avoir et de crédit | INV-73 à 77 |
| `INSERT OR REPLACE` contournait la garde de non-suppression (découvert à l'audit BC, V3.12) | INV-07 (`recursive_triggers=ON`), INV-174, TR-19, conventions techniques §9, D-39 |
| Caches écrits en plusieurs UPDATE : CHECK de cohérence violés entre deux écritures (V3.12) | INV-46, INV-164 (un seul UPDATE), §4.7 |
| BC annulé modifiable ou réactivable ; BC supprimable (V3.11 : `bc_lignes.bc_id` en CASCADE) | INV-173, INV-174, TR-12, TR-19, D-35 |
| Dérive silencieuse devis ↔ BC après la création (INV-48 limité à l'INSERT) | INV-175, TR-17, TR-18, CK-13, D-36 |
| Un numéro réservé pouvait être réattribué après un rollback propre (le compteur SQL revient en arrière alors que le high-water est déjà écrit) — F1, découvert à l'audit du 2026-10-03 ; `machine.db` perdue : F2 | INV-179, D-54, §11.4 (S1–S6), PT-1 (tranché), C-42, T-24, T-30 |
| Sentinelles du dépôt contredisant une décision validée (statut client, annulation de facture, gel, cascade BC → devis, CASCADE sur devis) | INV-180 à INV-195, E-10 à E-20, §4.19 (écarts → migrations ultérieures) |
| « Facturé à 100 % » érigé en règle d'accès au BC (proposition retirée) | INV-187 : le seul critère est le solde rédigé/validé |
| Garanties transformées en nouveau mécanisme | INV-86, INV-87 : principe du CDC §24 inchangé |

---

## 17. Critères de sortie de la V3.13 et suivi des migrations

Le modèle est prêt pour le DDL lorsque :
1. chaque INV de `invariants.md` a une garde désignée et un nom de test ; les tests T-01 à T-20 (§13.2) et T-21 à T-29 (§13.3) sont écrits, ainsi que les tests proposés T-30 à T-43 lorsque leur mécanisme (PT) est conçu ; T-29 (BC) est intégré avec la migration 004 ;
2. D-01 à D-12 sont validées (fait le 2026-09-29) ; D-13 à D-17 sont validées (fait le 2026-09-29) ; D-21 à D-27 validées (2026-09-30) ; D-28 à D-31 validées (2026-10-01) ; D-32 et D-33 validées (2026-10-01) ; D-34 à D-39 validées (2026-10-01) ; D-40 à D-54 : règles métier validées le 2026-10-03, mécanismes techniques en propositions PT-1 à PT-21 (§19) ; D-55 validée (2026-10-04, versionnement des migrations) ;
3. D-18, D-19 et D-20 sont validées (P-01 soldé, fait) ; D-16 est tranchée (aucune garantie recréée, fait) ;
4. les errata E-01 à E-20 sont au fichier `cdc-errata-v6.md` ;
5. l'ordre du DDL est : `machine/001` (indépendant) puis métier : import_anomalies → séquences → listes → clients/fournisseurs → catalogue → devis → BC → dépenses → facturation (factures) → règlements → garanties → PV → planification (D-34). Documents, paramètres, historique et URSSAF ne sont pas positionnés dans cet ordre : ils seront traités dans leur contexte propre. Chaque tranche est une migration distincte, accompagnée de ses triggers, de ses index et de ses tests ; le modèle passe à la version suivante **avant** chaque migration (§17.1). Les correctives (`NNNx`) s'intercalent selon la chaîne du §17.1 sans changer cet ordre.

### 17.1 Suivi des migrations

| Rang | Migration | Contenu | Modèle | Test |
|---|---|---|---|---|
| (`machine.db`) 1 | `src-tauri/migrations/machine/001_initial.sql` | `machine.db` : 7 tables (§5) | V3.8 | T-25 |
| 1 | `src-tauri/migrations/metier/001_initial.sql` | `import_anomalies`, `numerotation_sequences`, `categories_prestations`, `categories_depenses`, `clients`, `prestations`, `prestation_garanties` ; TR-90, TR-95 | V3.9 | T-26 |
| 2 | `src-tauri/migrations/metier/002_fournisseurs.sql` | `fournisseurs` ; aucun trigger ; `idx_fournisseurs_statut` | V3.10 | T-27 |
| 3 | `src-tauri/migrations/metier/003_devis.sql` | `devis`, `devis_lignes`, `devis_ligne_garanties` ; 11 triggers ; 4 index | V3.11 | T-28 |
| 4 | `src-tauri/migrations/metier/004_bons_commande.sql` | `bons_commande`, `bc_lignes`, `bc_ligne_garanties` ; 15 triggers dont TR-96 sur `numerotation_sequences` ; 3 index | V3.12 | T-29 |

**Chaîne ordonnée de la base métier (D-55, validée le 2026-10-04 ; référence : conventions techniques §5)** — le **rang** est la version du schéma (`PRAGMA user_version`), pas le numéro de fichier. Les rangs 5 à 12 ne sont **pas créés** :

| Rang | Fichier | Catégorie | Contenu |
|---|---|---|---|
| 5 | `005_depenses.sql` | tranche métier | Dépenses (cadrage `CADRAGE__005_depenses.md`) |
| 6 | `005a_corrections_v313.sql` | corrective (M-A) | contenu **proposé** ci-dessous |
| 7 | `005b_bc_multi_devis.sql` | corrective (M-B) | contenu **proposé** ci-dessous |
| 8 | `006_facturation.sql` | tranche métier | Facturation (nom exact fixé à la création) |
| 9 | `007_reglements.sql` | tranche métier | Règlements |
| 10 | `008_garanties.sql` | tranche métier | Garanties |
| 11 | `009_pv.sql` | tranche métier | PV |
| 12 | `010_planification.sql` | tranche métier | Planification |

Une corrective future `010a_*` aurait le rang 13. Exemple : `user_version = 7` ⇒ 001 à 004, 005, 005a et 005b appliquées.

**Migrations correctives M-A et M-B (PT-20 ; place dans la chaîne validée, contenu PROPOSÉ et non validé, fichiers non créés)** : les migrations 001–004 étant appliquées et immuables, les écarts du §4.19 se corrigent par des migrations nouvelles, après passage du modèle à la version correspondante (conventions §5). M-A et M-B sont des **correctives** : elles ne sont pas des tranches métier, ne consomment aucun numéro de tranche et s'exécutent **après 005 et avant 006** (D-55). Le protocole de reconstruction de table et les évolutions du runner sont un **chantier technique distinct** de la tranche 005 (conventions §5).

| Migration proposée | Contenu proposé | Source |
|---|---|---|
| `metier/005a_corrections_v313.sql` (M-A, rang 6) | reconstruction de `clients` sans `statut` ; retrait de `fournisseurs.statut` par `DROP INDEX` puis `DROP COLUMN`, **sans reconstruction** de `fournisseurs` (PT-3) ; gardes DELETE / `code` immuable (PT-4) ; reconstruction de `devis` avec statut `brouillon` et `numero` nullable, `devis_origine_id`, adaptation de `frozen_at`/TR-14 (PT-2, PT-7, PT-8) ; réécriture de TR-10/TR-11 (PT-2, PT-17, PT-21) ; colonnes `devis.revision`, `devis.revision_en_cours`, table `devis_revisions` + TR-100 (PT-21, validé sur le principe ; la colonne `documents.revision` relève de la future tranche Documents, **pas de M-A**) ; garde DELETE sur `devis` et cascade limitée au brouillon (PT-5) | §4.19 lignes 1 à 9 |
| `metier/005b_bc_multi_devis.sql` (M-B, rang 7) | création de `bc_devis` ; migration des liens existants `bons_commande.devis_id` vers `bc_devis` ; reconstruction de `bons_commande` (retrait de `devis_id`, `remise_*`, `acompte_*`) ; adaptation de TR-12, TR-13, TR-17, TR-18 ; adaptation de `bc_ligne_garanties` (`RESTRICT`) (PT-5, PT-6, PT-7, PT-16) | §4.19 lignes 10 à 18 |

*Numérotation des fichiers et ordre : validés le 2026-10-04 (D-55) ; contenu des correctives : propositions.* L'ordre des tranches de D-34 reste celui des tranches métier : 001 Initial → 002 Fournisseurs → 003 Devis → 004 Bons de commande → **005 Dépenses** → **006 Facturation** → 007 Règlements → 008 Garanties → 009 PV → 010 Planification. **Aucune tranche n'est renumérotée.** M-A (`005a`) puis M-B (`005b`) s'exécutent entre 005 et 006. L'ordre des correctives entre elles (M-A avant M-B) est celui du tableau ; une dépendance dure de M-B envers M-A n'est démontrée que pour un éventuel `devis.devis_origine_id` (PT-7, non validé). La couche d'exécution (PT-12, PT-13) vient après la Facturation, une fois conçue. Aucun fichier de migration, aucun test et aucun code n'est modifié par la présente mise à jour documentaire.

Tranches suivantes (ordre du critère 5) : dépenses, facturation (factures), règlements, garanties, PV, planification.

**Tests 001–003 renforcés (copies en relecture, `fichiers-a-relire/`)** : chaque connexion de test pose explicitement `PRAGMA recursive_triggers=ON` ; un test vérifie que le réglage est actif ; un test ciblé vérifie qu'`INSERT OR REPLACE` ne contourne pas les triggers de protection applicables (001 : TR-90 ; 002 : CHECK de `fournisseurs` et TR-90 de la pile ; 003 : TR-11 lignes et garanties). Les migrations 001–003 ne sont pas modifiées. Nombre de tests : 001 = 28 (26 + 2), 002 = 18 (16 + 2), 003 = 68 (65 + 3). Les copies ont été exécutées dans une copie de travail hors dépôt ; les tests du dépôt GitHub n'ont pas été exécutés.

**Campagne de mutation des tests renforcés 001–003** (2026-10-02, copie de travail hors dépôt, migrations 001–003 inchangées, tests à 28 / 18 / 68) — critère de la conventions techniques §7.1 : **0 survivant non qualifié**. 001 : 267 mutants, 255 tués, 10 survivants (8 équivalents, 2 inatteignables), 2 non viables (erreur de syntaxe) ; 002 : 19 mutants, 19 tués, 0 survivant ; 003 : trois passes complémentaires (448, 275 et 128 mutants) ne laissent que des survivants équivalents (condition redondante, `NULL` accepté par un `CHECK`, `BEFORE` ↔ `AFTER` avec `RAISE(ABORT)`) ou inatteignables (valeur de `statut` hors de la liste fermée, client toujours présent). Aucun survivant réel : aucun test n'a eu besoin d'être renforcé davantage. La campagne est à rejouer si les fichiers de test déposés dans le dépôt diffèrent de ces copies.

---

## 18. Concordance V3.4 → V3.5 (historique documentaire, conservée telle quelle en V3.9)

La V3.4 comptait 102 sections courtes ; la V3.5 les regroupe en 17 chapitres (elle est plus longue : ≈ 10 000 mots contre ≈ 6 650). Chaque section de la V3.4 a été relue une à une ; aucune n'a été supprimée.

| Section V3.4 | Emplacement V3.5 |
|---|---|
| §1 Principes | §1 · INV-01, 07, 09 |
| §2 Séparation métier / machine | §1, §5 · INV-02, 142 |
| §3 Identifiants | §2.1 · INV-04 |
| §4 Dates et heures | §2.2 · INV-10 |
| §5 Décimales | §2.3 · INV-11 à 14 |
| §6 Calcul commercial | §3.1 · INV-13, 15 |
| §7 Snapshots | §2.4 (BLOC-SNAP) · §7 · INV-30 à 32 |
| §8 Paramètres entreprise | §4.15 |
| §9 Utilisateur local | §5 · INV-151 |
| §10-11 Clients, fournisseurs | §4.4 · INV-06 |
| §12-13 Prestations, catégories | §4.3, §4.5 · INV-166 (ELE-008) |
| §14-15 Garanties du catalogue et snapshotées | §4.5, §4.6, §4.7 · INV-86 |
| §16-17 Devis et lignes | §4.6 |
| §18-20 Création du BC, BC, lignes de BC | §4.7 · INV-38, 40 · **voir écarts 1 et 10** |
| §21-22 Gel, acompte non réglé | §7.1 · INV-33 à 36 |
| §23-26 Factures, snapshots, lignes, composition | §4.8 · INV-53 à 55, 62 |
| §27-31 Facturation nette, situation, solde, avancement, 100 % | §3.2, §3.5 · INV-43, 56 à 58 |
| §32-34 Garanties générées, garanties, dates | §4.10 · INV-85 à 90 |
| §35-38 Règlements, statut, avoirs, annulation d'un avoir | §3.3, §3.4, §4.9 · INV-60, 70 à 80 |
| §39-41 Fin du BC, annulation du solde, annulation du BC | §3.5 · INV-42, 44 · **voir écart 2** |
| §42-43 PV, levée de réserves | §4.11 · INV-96, 97 |
| §44-46 Planification, événements, Gantt | §4.12 · INV-101 · E-03 |
| §47 Dépenses | §4.12 · INV-100 |
| §48 CA engagé | §3.6 · INV-45 |
| §49-50 Documents, racines de stockage | §4.13, §5 · INV-105 à 108 |
| §51 Historique | §4.14 · INV-110, 111 |
| §52-58 URSSAF | §4.16 · INV-120 à 127 |
| §59-61 Migration, quarantaine, mode migration | §4.1, §10.4 · INV-130, 131, 136 · **modifiés le 2026-09-30 (écart 6)** |
| §62-68 Numérotation | §4.2, §6 · INV-20 à 27 |
| §69-72 Migration des factures, garanties, catalogue, contrôle | Règles de transformation : futur `docs/migration/convertisseur-v2-vers-import-v6.md` ; côté V6 : §10.3 à §10.8 · **voir écarts 4 et 6** |
| §73-74 Idempotence, intégrité référentielle | §8, §9 · INV-05, 52 |
| §75-79 Immutabilités, `cancelled_at` | §7.2 · INV-53, 70 |
| §80 Notes BC | §4.12 · INV-102 |
| §81-83 Licence, Gmail, ErrorService | §12 · INV-150 à 152 |
| §84-86 Sauvegarde, restauration, dossier de travail | §11 · INV-140 à 144 |
| §87-88 SQLite, migrations de schéma | §1 · INV-07, 08 |
| §89 Contrôles SQL critiques | §8, §14 |
| §90, 93 Cache BC, ordre de recalcul | §3.7 · INV-46, 164 · **rétabli** |
| §91 Historique financier | §4.14 · INV-110 |
| §92 Cohérence des factures | INV-54 · CK-05 |
| §94 Règle de terminaison | §3.5 · INV-42 · **redéfinie, voir écart 2** |
| §95 Règle des garanties | INV-85, 87 |
| §96-97 Données migrées, quarantaine | §10.7 · INV-130, 165 · **rétabli, puis adapté à `import_anomalies` (écart 6)** |
| §98 Errata | `cdc-errata-v6.md` (chemin d'origine `docs/decisions/cdc-errata-v6.md`) |
| §99 Tests d'intégrité | §13.2 · T-01 à T-20 · **rétabli** |
| §100 Index essentiels | §9 (les 20 index d'origine + un index par FK) |
| §101 Source de vérité par domaine | §1, §4.7 · INV-01, 46 |
| §102 État de préparation au DDL | §17 |

### Écarts assumés par rapport à la V3.4
1. **Lignes de BC** : la V3.4 prévoyait `bc_lignes.active`, `updated_at` et des identifiants stables. La V3.5 supprime `active` et régénère les lignes avant gel (§4.7, INV-38) *(V3.13 : plus de régénération, le contenu du BC est stable dès sa création)*. Ce changement vient du point « lignes de BC / lignes de facture » de l'audit V3.4 ; il reste sûr parce qu'aucune facture ne référence une ligne BC avant le gel et que `facture_lignes.bc_ligne_id` est en `RESTRICT`. **Validé** par Rémy (D-20, 2026-09-29) ; contrainte associée : INV-168.
2. **BC terminé** : la V3.4 disait « solde actif et reste dû du solde = 0 ». Arbitrage 1 du 2026-09-29 : Σ reste dû des factures actives hors avoir = 0.
3. **Types de planning** : `intervention` et `travaux` rétablis (CDC §26, D-03) ; ils manquaient à la V3.4.
4. **Migration** : la source est la V2 (la V5 n'a jamais été distribuée) ; `complete → solde` sans objet ; les règles V2 (D-13 à D-19) sont désormais portées par le convertisseur (écart 6).
5. **Timestamps** : TEXT ISO UTC (D-02).
6. **Migration V2 externalisée (2026-09-30, V3.6)** : la première rédaction de la V3.5 embarquait un mode migration dans SQLite (`origine='migration'`, exemptions, `migration_rapports`, `migration_quarantaine`, compteurs jamais importés). Elle est remplacée par le flux V2 JSON → convertisseur externe → `import-v6.json` → import V6 (§10, D-21 à D-26, E-09). Retirés : mode migration, exemptions sauf le format du `numero` historique, `migration_id`, les deux tables de migration, le lecteur V2 tolérant. Aucune autre règle métier validée n'est modifiée ; en revanche `garanties.bc_ligne_id`, `garanties.facture_declenchement_id` et `bc_lignes.devis_ligne_id` sont NOT NULL sans condition, et les CHECK d'échéance, de format BC/CLI et de Σ lignes n'ont plus de condition d'origine.
7. **Numérotation (2026-09-30, V3.7)** : la V3.6 abaissait `max_attribue` à `dernier_numero` au démarrage normal, ce qui pouvait réattribuer un numéro déjà attribué. Corrigé : `max_attribue` ne diminue jamais, le trou est accepté et journalisé (§11.4, D-27, INV-25, T-24). Aucun nouveau mécanisme de numérotation. *(V3.13 : ce correctif est lui-même à réexaminer, le trou pouvant naître d'un rollback ou d'un crash avant COMMIT, contraire à D-40 ; PT-1, non tranché.)*
8. **`machine.db` (2026-10-01, V3.8)** : compte local obligatoire avec identifiant (D-28), préférences de sauvegarde en minutes avec valeurs par défaut (D-29), aucun trigger dans `machine.db` et singletons créés par le service d'initialisation (D-30). Le DDL `machine/001_initial.sql` est aligné sur ce §5.
9. **Première tranche métier (2026-10-01, V3.9)** : traduction SQL de `import_anomalies`, des séquences, des listes, des clients et du catalogue ; aucune règle nouvelle (§4.17). Le jeu de données d'installation (listes, catalogue par défaut) reste hors migration.
10. **Bons de commande (2026-10-01, V3.12)** : conception de la tranche 004 à partir des décisions de l'audit BC (D-34 à D-39). Écarts par rapport à la V3.11 : `bc_lignes.bc_id` passe de `CASCADE` à `RESTRICT` (un BC n'est jamais supprimé ; écart à INV-05 et au §4.7 de la V3.11, tracé au journal des invariants) ; `bc_lignes.devis_ligne_id` devient `UNIQUE` ; `bons_commande.date_creation` n'est plus « = date d'acceptation » (la date contractuelle est héritée du devis, D-37) ; le BC annulé devient terminal (D-35). Corrections de rédaction sans effet sur le schéma : « TR-01 bis » retiré de la liste des triggers (règle de service), garanties de ligne de devis retirées de l'ordre d'import (§10.5), T-27 et T-28 replacés au §13.3, nombre de triggers de `003` (11), références V3.10, motifs `GLOB` sans quantificateur `{n}`. Précision technique (application de D-39, sans nouvelle décision) : `tr_96_numerotation_sequences_no_delete` dans la migration 004, car `UPDATE` seul ne protège pas `numerotation_sequences` d'un REPLACE et `001_initial.sql` est immuable.

11. **Arbitrages métier du 2026-10-03 (V3.13)** : Q1–Q27 et arbitrages A à D (errata E-10 à E-20, INV-179 à INV-196, D-40 à D-54). Le dépôt existant (migrations 001–004, tests, modèle V3.12) a été traité comme **matière d'audit** et non comme vérité normative : chaque contradiction avec une décision validée est signalée (§4.19) et la décision prévaut. Ne sont pas réécrits : les migrations 001–004 ; les corrections structurelles sont portées par des migrations ultérieures (PT-20).
12. **Ce que la V3.13 ne tranche pas** : le schéma de la couche d'exécution et la formule de remise (PT-12, PT-13), la définition technique de « facture active » sans annulation (PT-9) et le sort de `frozen_at` (PT-8). Ce sont des propositions ou des points à concevoir, jamais des règles métier.

---

## 19. Propositions techniques (PT-1 à PT-21) — PT-1 tranché, PT-21 validé sur le principe

Ces éléments sont des **propositions de conception** nées de la mise en œuvre des décisions métier du 2026-10-03. **Sauf PT-1 (tranché) et PT-21 (validé sur le principe), le 2026-10-03, aucune n'est une décision de Rémy.** Chacune distingue la règle métier validée qu'elle sert, la proposition, et le point précis restant ouvert. Tant qu'une proposition n'est pas validée (ou tranchée), aucune migration, aucun test ni aucun code ne l'implémente.

| PT | Règle métier servie (validée) | Proposition technique | Point ouvert |
|---|---|---|---|
| PT-1 | INV-179, D-54 (un numéro n'est jamais attribué deux fois ; trou accepté, jamais récupéré) | **TRANCHÉ le 2026-10-03** : réservation committée avant l'objet — `n = max(compteur, high-water) + 1` sous `BEGIN IMMEDIATE`, high-water écrit durablement (blocage si échec), compteur posé à `n` et committé, puis objet créé dans une transaction distincte ; trou journalisé — §11.4. α et ρ rejetées | Détails d'implémentation (§11.4 point 6) ; limite irréductible acceptée (base métier restaurée + `machine.db` perdue) ; D-27, INV-25, §5, T-24 alignés dans cette révision |
| PT-2 | INV-180, INV-181 | Statut `brouillon` ; `numero` NULL jusqu'à la finalisation ; `CHECK (statut='brouillon') = (numero IS NULL)` ; date de numérotation = date de finalisation ; TR-10 réécrit (brouillon libre, `en_attente` modifiable, `accepte` et `refuse` verrouillés) | Date de numérotation exacte ; impact sur `date_creation` et `date_validite` ; reconstruction de `devis` |
| PT-3 | INV-183 | Retrait de `statut` et `a_rattacher` de `clients`/`fournisseurs` (`clients` : reconstruction ; `fournisseurs` : `DROP INDEX` puis `DROP COLUMN`, sans reconstruction) ; client importé ambigu → deux clients + `import_anomalies` `a_verifier` | Choix entre « deux clients + anomalie » et import tel quel ; reconstruction de `clients` (FK entrantes) selon le protocole des conventions §5 |
| PT-4 | INV-183, INV-06 | Triggers : DELETE refusé, `code` immuable (`REPLACE` couvert par `recursive_triggers=ON`) | Portée exacte (clients, fournisseurs, autres numérotés) |
| PT-5 | INV-05, INV-180, INV-184 | `devis_lignes`/`devis_ligne_garanties` en CASCADE seulement avec garde `BEFORE DELETE` sur `devis` (brouillon seulement) ; `bc_ligne_garanties` en RESTRICT ; `prestation_garanties` CASCADE conservée | Reconstruction de tables pour changer une clause `ON DELETE` (SQLite) |
| PT-6 | INV-187, INV-188 | Table `bc_devis` (`UNIQUE(devis_id)`, `rang`) ; trigger minimal (devis `accepte`, même client, BC non annulé) ; condition « aucun solde » portée par le service ; **aucune cascade d'annulation** | Migration des liens existants ; snapshots du BC lorsque des devis de chantiers différents sont rattachés |
| PT-7 | INV-175, INV-176, INV-189, INV-192 | `devis_origine_id` ; `date_acceptation` du BC = devis d'origine ; remise et acompte prévus portés par chaque devis | Retrait des colonnes `bons_commande.remise_*`/`acompte_*` (migration) |
| PT-8 | INV-181, INV-186 | Sort de `frozen_at`, TR-14, TR-15 et des CHECK `termine ⇒ gelé` : suppression ou conservation informative | **Choix non fait** ; CHECK de 004 impactés |
| PT-9 | INV-185, arbitrage B | Factures sans `cancelled_at` ; « actif » redéfini (par ex. non entièrement créditée) ; unicité par service/trigger plutôt que par index partiels ; règle de `date_100_facture` | Définition de « actif » ; **correction d'un avoir erroné : À CONCEVOIR** |
| PT-10 | INV-189 | `factures.devis_id` ; un acompte par (BC, devis) | Tableau d'avancement des acomptes d'un BC à plusieurs devis |
| PT-11 | INV-190 | Colonnes de situation : mode, valeur saisie, avancement, montant HT, base figée | **Ce que désigne la valeur « montant » (cumulé ou de la période) : À CONCEVOIR** |
| PT-12 | INV-191 | Modèles d'exécution A (état modifiable + historique), B (déclarations append-only), C (quantités/prix seulement sur les lignes de facture) | Modèle non choisi ; bornes prix/quantité ; formule de « base facturable » |
| PT-13 | INV-192 | Formule détaillée de répartition de la remise au prorata | Cas particuliers ; arrondis (D2) |
| PT-14 | INV-193 | `depenses.cancelled_at`/`motif_annulation` ; exclusions des totaux (**principe d'exclusion validé : INV-200**) | Formules détaillées des calculs concernés (le principe d'exclusion n'est plus ouvert) |
| PT-15 | INV-194 | Catalogue d'événements : ajout `validation`, `reouverture`, `rattachement_devis`, événements d'exécution ; retrait de `gel`, `rattachement_client` | Énumération exacte (§2.5) |
| PT-16 | INV-188 | TR-16/INV-47 : pas de nouvel acompte/situation/solde sur BC annulé ; avoirs et règlements sur documents existants possibles ; adaptation de TR-12 (caches après avoir) | **Avoir sur un BC `termine` : à confirmer** |
| PT-17 | INV-182 | Transition `refuse → en_attente` via TR-10 réécrit | Sort de `date_refus` et `motif_refus` à la réouverture |
| PT-18 | INV-86, INV-87 (principe du CDC §24 inchangé) | **Aucun mécanisme** : la suppression complète d'une ligne de devis brouillon supprime avec elle ses garanties de ligne ; une ligne modifiée suit le principe existant | Aucun — conséquence de la suppression, non une règle à arbitrer |
| PT-19 | INV-185 | Import d'une facture V2 « annulée » = facture + avoir total | Contrat à écrire (document du convertisseur) |
| PT-20 | Méthode (dépôt = matière d'audit) | Migrations correctives M-A et M-B sans réécrire 001–004 (§4.19, §17.1) | **Numérotation et ordre : validés le 2026-10-04 (D-55)** — `005a`/`005b`, rangs 6 et 7, entre 005 et 006. Reste à valider : contenu exact et découpage de M-A et M-B |
| PT-21 | INV-196 (révisions) | **Validé sur le principe le 2026-10-03** (« A raffiné ») ; **représentation de la version initiale figée : `revision IS NULL`** : tables vivantes + `devis_revisions` append-only (snapshots complets, version initiale incluse, `revision` NULL = version initiale), `devis.revision`, `devis.revision_en_cours`, TR-100, CK-15 (M-A) et `documents.revision` (future tranche Documents, §4.6) ; **aucune** `bc_devis.revision_acceptee` — §4.6 | `notes` imprimées ? ; comparaison « modification significative » ; PDF après COMMIT ; triggers en liste blanche ; événements d'historique |

### 19.1 Points techniques ouverts (à ne pas confondre avec des arbitrages métier)
- Détails d'implémentation de la numérotation (PT-1 tranché : nommage des PDF, instance unique, journalisation du trou) ; détails du stockage des révisions (PT-21 validé sur le principe ; représentation `revision IS NULL` figée : `notes` imprimées, comparaison de contenu, PDF après COMMIT, triggers) ; sort de `frozen_at` (PT-8) ; définition de « actif » sans annulation et correction d'un avoir erroné (PT-9) ; signification de la valeur « montant » d'une situation (PT-11) ; modèle d'exécution, bornes et formules (PT-12, PT-13) ; avoir sur un BC `termine` (PT-16) ; `date_refus`/`motif_refus` à la réouverture (PT-17) ; snapshots du BC lorsque des devis de chantiers différents sont rattachés (PT-6) ; ordre et découpage des migrations (PT-20).
- **Une seule confirmation d'usage possible** : un devis `en_attente` numéroté peut-il être corrigé sur place **sans** révision (PT-21 propose que non) ? Le point « devis `en_attente` verrouillé » est **clos** : il est modifiable (INV-181, INV-196). L'annulation d'un BC est appliquée sans précondition de facturation (la confirmation d'usage relève du service).
