# BATORYA Essentiel — Modèle de données SQLite V6 — V3.10

**Statut** : modèle consolidé, prérequis aux migrations SQL (suivi des migrations : §17.1)
**Base** : V3.4 + audit V3.4 + arbitrages de Rémy Pavy du 2026-09-29 ; révisions V3.6 (migration V2 externalisée) et V3.7 (high-water) du 2026-09-30 ; révision V3.8 (`machine.db`), révision V3.9 (DDL de la première tranche métier) et révision V3.10 (fournisseurs et règle de rattachement tardif des dépenses aux BC) du 2026-10-01
**Version courante** : V3.10 (les mentions V3.4 / V3.5 / V3.6 / V3.7 / V3.8 ci-dessous désignent l'historique du document)
**Pièces obligatoires du modèle** : ce document + `invariants.md` + `cdc-errata-v6.md`

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

---

## 1. Principes généraux [INV-01 à INV-08]

- SQLite local = source de vérité. Les PDF, exports et sauvegardes en sont dérivés.
- Flux : `UI React → services applicatifs → domaine → repositories → SQLite`. L'UI n'exécute jamais de SQL.
- **Accès SQLite exclusivement côté Rust (Tauri)**. Pas de SQLite WASM/OPFS : WAL, Backup API et `VACUUM INTO` y sont indisponibles.
- Deux bases : **base métier** (sauvegardée/restaurée) et **`machine.db`** (jamais sauvegardée, jamais restaurée).
- Aucune donnée métier n'est envoyée au service distant (licence, mises à jour, référentiels uniquement).
- Toute opération métier multi-tables est **une seule transaction** ; une opération partielle est interdite.
- SQLite ≥ 3.37 requis (tables `STRICT`, `RETURNING`). **Toutes les tables sont `STRICT`.**
- Réglages de connexion, à chaque ouverture : `foreign_keys=ON`, `journal_mode=WAL`, `synchronous=FULL`, `busy_timeout` défini.
- Migrations de schéma : fichiers numérotés (`001_initial.sql`…) sous `src-tauri/migrations/machine/` et `src-tauri/migrations/metier/` (conventions techniques §5), chacun dans une transaction, `PRAGMA user_version` mis à jour après succès. `machine.db` a ses propres migrations et son propre `user_version`.
- Deux mécanismes distincts : **migration de schéma** (V6.n → V6.n+1) et **import de données** (fichier `import-v6.json` produit par un convertisseur externe à partir de l'unique sauvegarde V2 ; V6 ne lit jamais le format V2 ; la V5 n'a jamais été distribuée). Voir §10.

---

## 2. Conventions techniques

### 2.1 Identifiants et clés

- `id INTEGER PRIMARY KEY AUTOINCREMENT` sur toutes les tables référencées (jamais de réutilisation d'id). [INV-04]
- Le numéro métier (`numero`, `code`) n'est jamais une clé étrangère.
- FK : `ON DELETE RESTRICT` par défaut. `ON DELETE CASCADE` uniquement pour : lignes → parent **avant gel**, `*_ligne_garanties`, `prestation_garanties`. [INV-05]
- Les liens polymorphes `historique.entite_id` et `documents.entite_id` (discriminant `type_entite`) et `urssaf_corrections.source_id` (discriminant `source_type`) n'ont pas de FK : leur discriminant est une énumération fermée (§2.5) et l'existence est vérifiée par le service et par les requêtes de contrôle. **Exception** : `import_anomalies.entite_id` est aussi un lien polymorphe sans FK (CK-09), mais son `type_entite` n'est pas une énumération fermée du modèle (§4.17, point 7).

### 2.2 Dates et timestamps [INV-10]

| Notation | Type | Format | Contrôle |
|---|---|---|---|
| **D** | TEXT | `YYYY-MM-DD` | `GLOB` + `date(x)=x` (date réelle) |
| **TS** | TEXT | `YYYY-MM-DDTHH:MM:SS.SSSZ` (UTC) | `GLOB` |
| **DL_LOCAL** | TEXT | `YYYY-MM-DD` ou `YYYY-MM-DDTHH:MM` (heure locale, planning uniquement) | `GLOB` |

Les colonnes `*_at` sont des TS. Les colonnes `date_*` sont des D. Une date métier n'est jamais déduite d'un TS.
Le « jour courant » (retards, garanties) est la date **locale** de l'entreprise.

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
| statut client | `actif`, `archive`, `a_rattacher` |
| statut fournisseur | `actif`, `archive` |
| `type_prestation` | `fourniture`, `pose`, `fourniture_pose` |
| `unite` | `u`, `ens`, `ml`, `m2`, `m3` (D-13) |
| `remise_type` | `aucune`, `pourcentage`, `montant` |
| `acompte_type` | `aucun`, `pourcentage`, `montant` |
| `garantie_type` | `parfait_achevement`, `biennale`, `decennale` |
| statut devis | `en_attente`, `accepte`, `refuse`, `annule` |
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
| `historique.type_evenement` | `creation`, `modification`, `acceptation`, `refus`, `annulation`, `gel`, `emission`, `reglement`, `annulation_reglement`, `remboursement`, `avoir`, `passage_termine`, `retour_en_cours`, `declenchement_garantie`, `rattachement_client`, `declaration_urssaf`, `correction_urssaf`, `import`, `restauration` |
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
- `total_ht = Σ montant_ligne − remise_globale`. `montant_contractuel_ht` du BC = même formule sur `bc_lignes`.
- `acompte_prevu = arrondi(contractuel × pct / 100)` ou montant fixe ; toujours ≤ contractuel.
- **Arrondi HALF_UP** : demi vers le haut en valeur absolue (`0.125 → 0.13`, `-0.125 → -0.13`).
- Pourcentages saisis à 2 décimales.

### 3.2 Facturation

```
facturation_nette = Σ acomptes actifs + Σ situations actives + solde actif − Σ avoirs actifs
```
(« actif » = `cancelled_at IS NULL`.) Tous les avoirs actifs réduisent la facturation nette. [INV-56]

```
situation.montant  = arrondi(contractuel × cumul% / 100) − facturation_nette_avant_situation
situation.montant_deja_facture_ht = facturation_nette_avant_situation
facturation_nette_apres_situation ≤ contractuel

solde.total_ht = contractuel − facturation_nette_avant_solde     (≥ 0, 0.00 autorisé)
```
[INV-57, INV-58]

- Un **solde à 0.00** est autorisé (100 % déjà couvert par acomptes et situations). Il reste l'événement de clôture de facturation.
- Dès qu'un **solde actif** existe : nouvel acompte interdit, nouvelle situation interdite, et **aucun avoir ne rouvre la facturation** (pas de nouveau solde). Avant solde, un avoir sur acompte ou situation réduit la facturation nette et libère donc un montant refacturable (cas C-09).
- « 100 % facturé » = **présence d'un solde actif**, indépendamment de la somme nette.

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
- encaissement ≤ `reste_du` ; aucun encaissement sur une facture annulée ni sur un avoir ;
- remboursement ≤ `credit` ; remboursement uniquement sur un avoir actif ;
- Σ avoirs actifs ≤ `M` de l'origine ;
- annulation d'un encaissement refusée si elle rend `credit` < Σ remboursements actifs.

### 3.4 États dérivés (jamais persistés) [INV-60]

**Facture hors avoir**
- `etat_paiement` : `annulee` si `cancelled_at` ; sinon `reglee` si `reste_du = 0` (même sans encaissement, ex. solde 0.00 ou couvert par avoirs) ; sinon `partiellement_reglee` si `encaisse > 0` ; sinon `en_attente`.
- `en_retard` (indicateur transversal) : non annulée ∧ `reste_du > 0` ∧ `date_echeance < aujourd'hui`. Une facture peut être `partiellement_reglee` **et** en retard.

**Avoir** : `annule` ; `credit_disponible` si `credit > 0` ; `solde` sinon. Jamais « en retard ».

**Garantie** : `a_surveiller` (avant échéance) / `echue` (après `date_fin_suivi`), dérivé, libellé toujours « Suivi interne BATORYA — date indicative ».

### 3.5 Fin du BC et rattachement tardif des dépenses [INV-42, INV-43, INV-103]

```
BC termine  ⇔  solde actif  ET  Σ reste_du des factures actives hors avoir = 0
```
- Un solde à 0.00 ne rend **pas** le BC terminé tant qu'une situation ou un acompte reste dû.
- L'avoir n'est pas un encaissement ; il intervient uniquement via `absorbe` (il réduit le reste dû). Un BC dont toute la dette est absorbée par des avoirs, sans autre dette, a `Σ reste_du = 0` (cas C-10).
- Passage `en_cours → termine` : `completed_at` = instant du recalcul. Passage `termine → en_cours` (annulation d'un règlement ou d'un avoir) : `completed_at = NULL`, événement d'historique `retour_en_cours`.
- `date_100_facture` = date d'émission du **premier solde actif**. Conservée lors d'un avoir, d'un règlement, d'un remboursement. Remise à `NULL` **uniquement** à l'annulation du solde. Si un nouveau solde est émis ensuite, elle prend la date de ce nouveau solde.
- `date_100_facture` (état courant du BC) ≠ `garanties.date_declenchement` (premier déclenchement historique). Les deux peuvent diverger volontairement.
- À compter de `date_100_facture`, les dépenses peuvent être rattachées normalement au BC pendant **30 jours calendaires**. À l'issue de cette période, le BC est considéré comme **clôturé pour les nouvelles dépenses**.
- Une dépense peut néanmoins être rattachée après cette clôture : le service affiche une confirmation indiquant depuis combien de jours le BC est clôturé et demande « Êtes-vous sûr de vouloir ajouter cette dépense sur ce BC ? ». Une confirmation positive suffit ; il n'existe ni procédure de déblocage, ni autorisation supplémentaire, ni durée maximale de rattachement tardif.
- La clôture des dépenses n'affecte ni le statut financier du BC, ni son historique, ni les dépenses déjà rattachées.

### 3.6 CA engagé [INV-45]

Pour les BC `en_cours` uniquement (BC annulés exclus) :
```
engage = max(0, (contractuel − Σ avoirs actifs) − (Σ encaissements actifs − Σ remboursements actifs))
CA engagé = Σ engage
```
CA encaissé et CA prévisionnel restent distincts et calculés (aucune colonne).

### 3.7 Ordre de recalcul du service financier [INV-164]
Après toute opération financière (facture, annulation, avoir, règlement, remboursement), le service recalcule **dans cet ordre**, dans la même transaction, sans jamais laisser un cache intermédiaire incohérent :
1. factures actives ; 2. facturation nette ; 3. montant restant ; 4. avancement ; 5. état 100 % ; 6. `date_100_facture` ; 7. reste dû du solde ; 8. état `termine` / `en_cours` ; 9. CA engagé.

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
`UQ(type_objet, annee)` · `CHECK((type_objet IN ('CLI','FOU')) = (annee=0))` · plafond : `dernier_numero BETWEEN 0 AND 99999` (documents), `0 AND 9999` (CLI/FOU). `dernier_numero` ne peut que croître (TR-95).
Attribution (dans la transaction de création du document) :
`INSERT … ON CONFLICT(type_objet, annee) DO UPDATE SET dernier_numero = dernier_numero + 1 RETURNING dernier_numero`. Dépassement du plafond = erreur métier explicite.

### 4.3 Référentiels de listes

**`categories_prestations`** : `id` PK · `code` UQ NN · `libelle` NN · `actif` INTEGER NN (0/1) · `ordre` INTEGER · TS.
**`categories_depenses`** : idem. Contenu initial : liste de la décision D-18 (modifiable par l'utilisateur).
Les listes de référence et le catalogue par défaut sont livrés par le **jeu de données d'installation** (D-14, §10.1), jamais par une migration de schéma : le DDL ne crée aucune ligne (§4.17).

### 4.4 Clients et fournisseurs

**`clients`** : `id` PK · `code` UQ NN · `nom` NN · `prenom` · `adresse` · `cpville` · `tel` · `email` · `notes` · `statut` NN défaut `actif` · TS · +IMP+.
- Format `code` : `CLI-0001`, sans exception (le convertisseur recode les codes historiques, l'ancien code va dans `legacy_numero`).
- `statut='a_rattacher'` ⇒ `origine='import'`.
- Rattachement d'un client `a_rattacher` : réaffectation de `client_id` (devis, BC, factures) vers le client cible, événement `rattachement_client`. C'est la **seule** modification de `client_id` autorisée sur une facture ou un document gelé (TR-20). Les snapshots ne changent pas.
- Jamais supprimé s'il a un historique ; il est archivé.

**`fournisseurs`** : `id` PK · `code` UQ NN · `nom` NN · `adresse` · `cpville` · `tel` · `email` · `notes` · `statut` NN · TS. Format `FOU-0001`. `statut` ∈ (`actif`,`archive`) ; un fournisseur `archive` reste disponible pour l'historique mais ne peut pas être sélectionné pour une nouvelle dépense. Un fournisseur ayant un historique est archivé, jamais supprimé.

### 4.5 Catalogue

**`prestations`** : `id` PK · `reference` UQ NN · `designation` NN · `description` · `categorie_id` NN FK→categories_prestations · `unite` NN · `type_prestation` NN · `prix_unitaire_ht` DL NN · `actif` INTEGER NN (0/1) · TS · +IMP.
Désactivée, jamais supprimée si utilisée. ELE-008 (Cat6) n'est pas dans le catalogue V6 : le catalogue par défaut compte 204 prestations (V5.16 moins ELE-008). [INV-06, INV-37, INV-166]

**`prestation_garanties`** : `id` PK · `prestation_id` NN FK **CASCADE** · `garantie_type` NN · `created_at`. `UQ(prestation_id, garantie_type)`.
Valeurs **par défaut** du catalogue ; jamais source historique. La durée dérive du type (pas de colonne durée).

### 4.6 Devis

**`devis`** : `id` PK · `numero` UQ NN · `client_id` NN FK→clients · BLOC-SNAP (client, entreprise, chantier) · `date_creation` D NN · `date_validite` D · `date_acceptation` D · `date_refus` D · `objet` · `notes` · `statut` NN · `remise_type` NN défaut `aucune` · `remise_valeur` · `acompte_type` NN défaut `aucun` · `acompte_valeur` · `total_ht` D2 NN · `frozen_at` TS · `cancelled_at` TS · `motif_refus` · `motif_annulation` · TS · +IMP.
CHECK :
- `(remise_type='aucune') = (remise_valeur IS NULL)` ; format selon type (P2 ou D2) ; idem `acompte`.
- `statut='accepte'` ⇒ `date_acceptation` NN ; `refuse` ⇒ `date_refus` NN ; `(statut='annule') = (cancelled_at IS NOT NULL)` ; `cancelled_at` ⇒ `motif_annulation` NN.
- `frozen_at` NN ⇒ `statut IN ('accepte','annule')`.
- `date_validite >= date_creation`.
- `origine='v6'` ⇒ `numero GLOB 'DEV-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'` ∧ `substr(numero,11,2)=substr(date_creation,3,2)`.

Un devis est modifiable si `en_attente`, ou `accepte` et non gelé (CDC §14). `refuse` et `annule` : immuables. [INV-31, INV-36]

**`devis_lignes`** : `id` PK · `devis_id` NN FK **CASCADE** · `ordre` INTEGER NN ≥ 1 · `prestation_id` NULL FK→prestations · `reference_prestation` · `designation` NN · `description` · `quantite` DL NN (> 0) · `unite` NN · `prix_unitaire_ht` DL NN · `remise_type` NN · `remise_valeur` · `type_prestation` NN · `total_ht` D2 NN · TS.
`UQ(devis_id, ordre)`. Ligne libre : `prestation_id IS NULL` (aucune pseudo-prestation, aucun `type_ligne='libre'`). La ligne est un snapshot : le catalogue ne la modifie jamais. Réordonnancement : régénération des lignes dans la transaction (ou passage par des `ordre` temporaires).

**`devis_ligne_garanties`** : `id` PK · `ligne_id` NN FK→devis_lignes **CASCADE** · `garantie_type` NN · `created_at`. `UQ(ligne_id, garantie_type)`.

### 4.7 Bons de commande

**`bons_commande`** : `id` PK · `numero` UQ NN · `devis_id` **UQ** NN FK→devis · `client_id` NN FK→clients · BLOC-SNAP (client, entreprise, chantier) · `date_creation` D NN (= date d'acceptation) · `date_acceptation` D NN · `date_debut` D · `date_fin` D · `montant_contractuel_ht` D2 NN · `remise_type` NN · `remise_valeur` · `acompte_type` NN · `acompte_valeur` · **caches** : `montant_deja_facture_ht` D2 NN défaut `0.00`, `avancement` P2 NN défaut `0.00`, `date_100_facture` D, `statut` NN défaut `en_cours`, `completed_at` TS · `cancelled_at` TS · `motif_annulation` · `frozen_at` TS · TS · +IMP+.
CHECK :
- `(statut='termine') = (completed_at IS NOT NULL)` ; `termine` ⇒ `date_100_facture` NN.
- `(statut='annule') = (cancelled_at IS NOT NULL)` ; `cancelled_at` ⇒ `motif_annulation` NN.
- `date_fin >= date_debut` si les deux existent.
- Format `BCD-nnnnn-yy` et année cohérente avec `date_creation`, sans exception (le convertisseur génère les numéros de BC ; l'ancien numéro éventuel va dans `legacy_numero`).

`montant_deja_facture_ht` (= facturation nette), `avancement`, `statut`, `completed_at`, `date_100_facture` sont des **caches** recalculés par **un seul service financier**, dans la même transaction que l'opération. La source de vérité est `factures + reglements`. [INV-46]
`avancement` = facturation nette / contractuel (P2) ; **100.00 si solde actif**. Il mesure la facturation, jamais l'avancement physique.

**`bc_lignes`** : mêmes colonnes que `devis_lignes` + `bc_id` NN FK **CASCADE** + `devis_ligne_id` NN FK→devis_lignes.
`UQ(bc_id, ordre)`. **Pas de colonne `active`.** Avant gel, les lignes sont régénérées depuis le devis ; après gel, elles ne bougent plus. Aucune facture ne référence une ligne BC avant le gel, donc aucun conflit avec `facture_lignes.bc_ligne_id` (RESTRICT). Ordre de régénération : supprimer `bc_lignes` puis modifier `devis_lignes` puis recopier.
**`bc_ligne_garanties`** : comme `devis_ligne_garanties`, `ligne_id → bc_lignes` CASCADE.

Le devis est le **seul point d'édition** : toute modification avant gel régénère `bc_lignes`, garanties de lignes, `montant_contractuel_ht` et snapshots du BC dans la même transaction. [INV-38]

### 4.8 Facturation

**`factures`** : `id` PK · `numero` UQ NN · `type` NN · `bc_id` NN FK→bons_commande · `client_id` NN FK→clients · BLOC-SNAP (client, entreprise, chantier) · `objet` · `date_emission` D NN · `date_echeance` D · `total_ht` D2 NN · `situation_numero` INTEGER · `avancement_cumule_pct` P2 · `montant_deja_facture_ht` D2 · `origine_facture_id` NULL FK→factures · `motif_avoir` · `cancelled_at` TS · `motif_annulation` · `created_at` · +IMP.
**Pas de `updated_at`, pas de `statut`, pas de `total_ttc`.**
CHECK :
- `(type='avoir') = (origine_facture_id IS NOT NULL)` ; `type='avoir'` ⇒ `motif_avoir` NN ∧ `date_echeance` NULL ; `type<>'avoir'` ⇒ `date_echeance` NN ∧ `motif_avoir` NULL ; `date_echeance >= date_emission`.
- `(type='situation') = (situation_numero IS NOT NULL) = (avancement_cumule_pct IS NOT NULL) = (montant_deja_facture_ht IS NOT NULL)`.
- `total_ht <> '0.00'` sauf `type='solde'` (acompte, situation, avoir > 0 ; solde ≥ 0).
- `(cancelled_at IS NULL) = (motif_annulation IS NULL)`.
- `origine='v6'` ⇒ préfixe selon type (`acompte→ACP-`, `avoir→AVO-`, `situation|solde→FAC-`), format `xxx-nnnnn-yy`, année = `substr(date_emission,3,2)`.

Index uniques partiels : [INV-52]
- `uq_facture_acompte_actif ON factures(bc_id) WHERE type='acompte' AND cancelled_at IS NULL`
- `uq_facture_solde_actif ON factures(bc_id) WHERE type='solde' AND cancelled_at IS NULL`
- `uq_situation_actif ON factures(bc_id, situation_numero) WHERE type='situation' AND cancelled_at IS NULL`

`client_id` peut changer **uniquement** par rattachement d'un client `a_rattacher`. Le solde annulé peut être réémis (l'index partiel ne compte que les actifs).

**`facture_lignes`** : `id` PK · `facture_id` NN FK→factures (RESTRICT) · `ordre` NN ≥ 1 · `bc_ligne_id` NULL FK→bc_lignes · `reference_prestation` · `designation` NN · `description` · `quantite` DL NN · `unite` NN · `prix_unitaire_ht` DL NN · `remise_type` NN · `remise_valeur` · `type_ligne` NN · `montant_ht` D2S NN · `created_at`.
`UQ(facture_id, ordre)`. `type_ligne='deduction'` ⇔ `montant_ht` négatif ; pour une déduction : `quantite='1'`, `prix_unitaire_ht` = valeur absolue, `montant_ht = −arrondi(quantite × prix)`. [INV-62]
Composition :
- **acompte** : 1 ligne `synthese`, montant = `total_ht`.
- **situation** : 1 ligne `synthese`, montant = montant de la situation (le cumul % et le déjà-facturé restent sur la facture).
- **solde** : lignes `prestation` copiées des lignes BC, puis lignes `deduction` (facturation nette antérieure, et remise globale du BC) ; `Σ = total_ht`, y compris `0.00`.
- **avoir** : lignes positives (`prestation` ou `synthese`).

Contrôle `Σ facture_lignes.montant_ht = factures.total_ht` : par le service à l'émission **et** par requête de contrôle CK-05 (SQLite ne peut pas l'imposer en fin de transaction). Aucune exemption, y compris pour les données importées. [INV-54]

### 4.9 Règlements

**`reglements`** : `id` PK · `facture_id` NN FK→factures · `type` NN · `date_evenement` D NN · `montant` D2 NN (`<> '0.00'`) · `mode` NN · `reference` · `note` · `cancelled_at` TS · `motif_annulation` · `created_at` · +IMP.
CHECK `(cancelled_at IS NULL) = (motif_annulation IS NULL)`. Jamais supprimé ; seules `cancelled_at` et `motif_annulation` peuvent être renseignées, une seule fois. Un remboursement porte sur un **avoir** (`facture_id` = l'avoir) ; il n'y a pas de colonne `avoir_id`. [INV-70, INV-71]

### 4.10 Garanties

**`garanties`** : `id` PK · `bc_id` NN FK→bons_commande · `bc_ligne_id` NN FK→bc_lignes · `garantie_type` NN · `date_declenchement` D NN · `date_fin_suivi` D NN · `facture_declenchement_id` NN FK→factures · `created_at`.
`UQ(bc_ligne_id, garantie_type)` (aucune garantie n'est importée : elles naissent uniquement de la facturation V6, INV-134). CHECK `date_fin_suivi > date_declenchement`. Pas de colonne statut. Aucun UPDATE ni DELETE. [INV-85 à INV-90]

Création : à l'émission d'un solde actif, le service lit `bc_ligne_garanties` du BC et insère `INSERT OR IGNORE` (idempotent, la première date est conservée). `date_declenchement` = date d'émission de ce solde. `date_fin_suivi` = +1 an / +2 ans / +10 ans ; 29 février → 28 février si l'année cible n'est pas bissextile. L'annulation du solde, un avoir, un règlement ne suppriment ni ne modifient une garantie.

### 4.11 PV

**`pv`** : `id` PK · `numero` UQ NN · `bc_id` NN FK→bons_commande · `type` NN · `date_reception` D NN · BLOC-SNAP (chantier, client, entreprise) · `observations` · `reserves` · `origine_pv_id` NULL FK→pv · `suffixe` INTEGER · `created_at` · +IMP.
CHECK :
- `(type='levee_reserves') = (origine_pv_id IS NOT NULL) = (suffixe IS NOT NULL)` ; `suffixe BETWEEN 1 AND 99`.
- `(reserves IS NOT NULL) = (type='reception_avec_reserves')`.
`UQ(origine_pv_id, suffixe)`. TR-41 : l'origine est un PV `reception_avec_reserves` **du même BC** ; une levée ne référence jamais une levée ; `suffixe = max + 1` ; `numero` de la levée = `numero` de l'origine + `-` + suffixe sur 2 chiffres. Le PV est facultatif et ne conditionne ni le solde, ni Terminé, ni les garanties. Plusieurs PV initiaux par BC ne sont pas interdits. Immuable dès l'INSERT (aucun UPDATE, aucun DELETE). [INV-95 à INV-97]

### 4.12 Dépenses, planning, notes

**`depenses`** : `id` PK · `numero` UQ NN · `fournisseur_id` NULL FK · `bc_id` NULL FK · `date_depense` D NN · `montant` D2 NN (`<> '0.00'`, montant réellement payé, franchise de TVA) · `categorie_id` NN FK→categories_depenses · `description` NN · `piece_jointe_chemin` · `piece_jointe_racine_id` INTEGER (les deux ou aucun) · `notes` · TS.
Ni statut de paiement, ni échéance, ni règlement fournisseur. Une dépense ne réduit jamais le CA URSSAF. `date_depense` modifiable tant que l'année (yy) ne change pas. Un fournisseur `archive` ne peut pas être sélectionné lors de la création d'une nouvelle dépense ; une dépense historique conserve son fournisseur. Pour `bc_id`, si `date_du_jour > date_100_facture + 30 jours`, le service demande une confirmation avant rattachement ; une confirmation positive permet le rattachement sans limite de durée. [INV-100, INV-103]

**`planning_evenements`** : `id` PK · `type_evenement` NN · `bc_id` NULL FK · `titre` NN · `date_debut` DL_LOCAL NN · `date_fin` DL_LOCAL NN · `journee_entiere` INTEGER NN (0/1) · `lieu` · `description` · TS.
CHECK : `journee_entiere=1` ⇒ deux dates `YYYY-MM-DD` ; sinon `YYYY-MM-DDTHH:MM` ; `date_fin >= date_debut` ; `type IN ('intervention','travaux')` ⇒ `bc_id` NN ; `type IN ('conge','indisponibilite')` ⇒ `bc_id` NULL. Aucun mapping de types à prévoir : aucune donnée de planning n'est importée (P-01).
Aucun effet sur le statut du BC. Le **Gantt lit `bons_commande.date_debut/date_fin`**, pas cette table ; un BC sans dates n'a pas de barre Gantt. [INV-101]

**`bc_notes`** : `id` PK · `bc_id` NN FK · `contenu` NN · TS. Modifiables et supprimables ; ne touchent aucun montant.

### 4.13 Documents

**`documents`** : `id` PK · `type_entite` NN · `entite_id` INTEGER NN · `type_document` NN · `numero_version` INTEGER NN ≥ 1 · `racine_stockage_id` INTEGER NN (référence **logique** vers `machine.db.stockage_racines`, pas de FK possible) · `chemin_relatif` NN · `nom_fichier` NN · `hash` TEXT (SHA-256 hex du contenu réellement présent) · `created_at`.
`UQ(type_entite, entite_id, type_document, numero_version)`. Seul `chemin_relatif` est modifiable (déplacement de statut). Une régénération crée une **nouvelle version**. Aucun DELETE. Le BC n'a pas de document. [INV-105 à INV-108]

### 4.14 Historique

**`historique`** : `id` PK · `type_entite` NN · `entite_id` INTEGER NULL · `bc_id` NULL FK · `type_evenement` NN · `acteur` NN défaut `utilisateur` · `donnees` JSON · `created_at` TS NN.
Append-only : aucun UPDATE, aucun DELETE. Pas de `updated_at`. Événements obligatoires : gel, émission, règlement et annulation, remboursement, avoir, annulation (facture, BC), passage à `termine`, retour à `en_cours`, déclenchement de garantie, annulation automatique d'acompte (`acteur='systeme'`), rattachement client, déclaration/correction URSSAF, import, restauration. [INV-110, INV-111]

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

Cette sous-section ne crée **aucune règle ni décision nouvelle** : elle fixe la traduction SQL des §2 à §4.5, §8 et §9 pour la première tranche métier.

1. **Périmètre de la migration** : `import_anomalies`, `numerotation_sequences`, `categories_prestations`, `categories_depenses`, `clients`, `prestations`, `prestation_garanties` ; triggers TR-90 et TR-95 ; index `clients(statut)`, `prestations(categorie_id)`, `prestations(actif)`, `import_anomalies(categorie, statut)`. `fournisseurs` n'est pas dans cette tranche : il constitue la tranche suivante, avant `devis`, `bons_commande` puis `depenses`.
2. **Aucune ligne insérée** par la migration (listes de référence, catalogue par défaut, séquences) : jeu de données d'installation (§4.3) ; les séquences naissent à la première attribution (§4.2) ou à l'import (§10.6).
3. **Textes obligatoires non vides** : `code`, `nom`, `libelle`, `reference`, `designation`, `ref_source`, `motif`, `type_entite` (CHECK `<> ''`). Les textes facultatifs ne sont pas contrôlés.
4. **Familles et listes** : `prix_unitaire_ht` en famille DL (§2.3) ; `actif` ∈ (0, 1) ; `statut` client, `unite`, `type_prestation`, `garantie_type`, `categorie`/`statut` d'anomalie : listes fermées du §2.5 (`CHECK … IN (…)`).
5. **Code client** : `CHECK code GLOB 'CLI-[0-9][0-9][0-9][0-9]'`, **sans exception d'origine** (D-01, INV-20, INV-27). `statut = 'a_rattacher'` ⇒ `origine = 'import'` ; `legacy_numero` NULL ou différent de `code` (INV-136).
6. **BLOC-IMP** (`clients`, `prestations`) : `origine IN ('v6','import')` ; `origine = 'v6'` ⇒ `legacy_id`, `legacy_data` (et `legacy_numero` pour `clients`) NULL ; `legacy_data` JSON valide si présent. Aucune contrainte supplémentaire (en particulier, `legacy_id` n'est pas rendu obligatoire ni unique).
7. **`import_anomalies`** : `type_entite` est un texte non vide **sans CHECK `IN (…)`** : c'est l'exception explicite à la règle d'énumération fermée des liens polymorphes (§2.1). Motifs : la table est alimentée uniquement à l'import (INV-163) ; une anomalie `non_importe` décrit une donnée que V6 ne représente pas, donc hors des types d'entités V6 ; le modèle (§2.5, §4.1, §10.7) n'en définit pas la liste. Les valeurs admises sont définies par le contrat `import-v6.json` (point P-04) et vérifiées par le lecteur strict (INV-153) ; CK-09 contrôle l'existence de `entite_id` pour les anomalies `a_verifier`. TR-90 : DELETE interdit ; UPDATE autorisé uniquement pour la transition `a_traiter` → `traite` (colonnes `statut` et `traite_at`, une seule fois). Aucune FK (lien polymorphe, contrôlé par CK-09).
8. **`numerotation_sequences`** : `annee BETWEEN 0 AND 99` ; plafond `dernier_numero` 9 999 (CLI/FOU) ou 99 999 (documents) en CHECK ; TR-95 : `dernier_numero` ne diminue jamais. Création/attribution : `INSERT (type_objet, annee, dernier_numero) VALUES (?, ?, 1) ON CONFLICT(type_objet, annee) DO UPDATE SET dernier_numero = dernier_numero + 1, updated_at = … RETURNING dernier_numero` ; au plafond, le CHECK refuse l'écriture (le service la traduit en erreur métier explicite).
9. **`prestation_garanties`** : FK `prestation_id` en CASCADE (INV-05) ; l'index de `UQ(prestation_id, garantie_type)` couvre la FK (pas d'index séparé).
10. **Point ouvert (P-04)** : le contrat d'import accepte un bloc `categories_prestations` dont chaque objet porte un `ref` copié dans `legacy_id`, alors que BLOC-IMP n'existe pas sur `categories_prestations` (§2.4). Le DDL suit le §2.4 (pas de BLOC-IMP sur les listes). La suite (ajouter BLOC-IMP aux catégories, ou ne pas conserver le `ref`) est à trancher avec le schéma JSON.

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
- **`sequence_high_water`** : à chaque attribution de numéro, le service écrit `max(max_attribue, numéro)` **avant** le COMMIT de la base métier. L'atomicité entre les deux fichiers n'est pas garantie en WAL ; d'où la règle de réconciliation du §11.4. [INV-25]
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
| Devis | `DEV-00001-26` | DEV | `date_creation` |
| BC | `BCD-00001-26` | BCD | `date_creation` |
| Acompte | `ACP-00001-26` | ACP | `date_emission` |
| Situation | `FAC-00001-26` | FAC | `date_emission` |
| Solde | `FAC-00001-26` | FAC (partagée avec situation) | `date_emission` |
| Avoir | `AVO-00001-26` | AVO | `date_emission` |
| PV initial | `PVR-00001-26` | PVR | `date_reception` |
| Levée de réserves | `PVR-00001-26-01`, `-02`… | suffixe = max + 1 par PV d'origine | — |
| Dépense | `DEP-00001-26` | DEP | `date_depense` |

- Le compteur repart à 1 chaque année ; la séquence est déterminée par l'année de la date métier. Plafond 99 999 (documents) et 9 999 (CLI/FOU) : erreur explicite au-delà.
- Un numéro est attribué une fois, dans la transaction de création, et n'est **jamais réutilisé**, même après annulation.
- **L'année (yy) d'une date de numérotation ne change jamais.** `date_creation` (devis, BC) est immuable ; `date_validite` reste modifiable. `date_depense` est modifiable dans la même année.
- **Chronologie continue** : pour ACP, FAC, AVO uniquement, `date_emission >= numerotation_sequences.derniere_date` de la séquence (TR-02). Elle ne s'applique pas à DEV, BCD, PVR, DEP.
- **Numéros historiques importés** : les devis, factures et PV `origine='import'` gardent le `numero` déjà remis au client (seule exemption de format, §10.4, INV-131) ; les contrôles de format de ces trois tables ne s'appliquent qu'à `origine='v6'`. BC et codes clients importés reçoivent du convertisseur des numéros au format V6 (ancien code dans `legacy_numero`, D-01).
- **Séquences importées** : le fichier d'import fournit `dernier_numero` (et `derniere_date`) par clé ; V6 en initialise `numerotation_sequences` et `sequence_high_water` ; un numéro sauté est acceptable, un numéro attribué n'est jamais réutilisé (§10.6, INV-135).

---

## 7. Gel, cycle de vie et immutabilité [INV-31 à INV-36, INV-53]

### 7.1 Gel commercial

`frozen_at` est posé **par trigger (TR-15)**, sur le devis **et** le BC, dans la transaction de l'événement, au premier de :
1. premier encaissement actif, même partiel, sur un acompte ;
2. insertion d'une situation ;
3. insertion d'un solde.

Un acompte émis mais non encaissé **ne gèle pas**. Si le devis/BC est alors modifié, l'acompte non réglé est **annulé automatiquement** dans la même transaction (`acteur='systeme'`, motif automatique) et peut être réémis. `frozen_at` ne revient jamais à `NULL` ; l'annulation d'une facture ne dégèle pas.

### 7.2 Colonnes modifiables

| Table | Non gelé | Gelé |
|---|---|---|
| `devis` | tout sauf `id`, `numero`, `date_creation`, `created_at`, `frozen_at` | `statut`, `cancelled_at`, `motif_annulation`, `client_id` (rattachement), `updated_at` |
| `devis_lignes`, `devis_ligne_garanties` | insertion, modification, suppression | aucune |
| `bons_commande` | tout sauf `id`, `numero`, `devis_id`, `date_creation`, `created_at`, `frozen_at` | caches (`montant_deja_facture_ht`, `avancement`, `date_100_facture`, `statut`, `completed_at`), `date_debut`, `date_fin`, `cancelled_at`, `motif_annulation`, `client_id` (rattachement), `updated_at` |
| `bc_lignes`, `bc_ligne_garanties` | régénérées depuis le devis | aucune |
| `factures` | — (jamais brouillon) | `cancelled_at`, `motif_annulation` (une fois), `client_id` (rattachement) |
| `facture_lignes` | insertion dans la transaction d'émission uniquement | aucune |
| `reglements` | — | `cancelled_at`, `motif_annulation` (une fois) |
| `pv`, `garanties`, `historique` | — | aucune |
| `documents` | — | `chemin_relatif` |

---

## 8. Triggers et index uniques [INV-05, INV-52, INV-53]

Les triggers ne servent que là où un `CHECK` ne suffit pas. Ils lèvent `RAISE(ABORT, 'INV-xx: …')` avec l'identifiant de l'invariant. Ils ne sont **exemptés pour aucune origine** : les données importées les traversent comme toute écriture V6 (INV-131).

| ID | Table / événement | Règle | INV |
|---|---|---|---|
| TR-01 | devis, BC, factures, pv, dépenses / UPDATE | `numero` immuable ; année de la date de numérotation immuable | 23 |
| TR-01 bis | dépenses / INSERT | si `bc_id` est renseigné et que le BC est à plus de 30 jours de `date_100_facture`, le service doit obtenir une confirmation explicite avant le rattachement ; aucun blocage définitif | 103 |
| TR-02 | factures / INSERT | ACP/FAC/AVO : `date_emission >= derniere_date` ; mise à jour de `derniere_date` | 24 |
| TR-10 | devis / UPDATE | modifiable seulement si `en_attente`, ou `accepte` non gelé ; colonnes du §7.2 si gelé | 31, 36 |
| TR-11 | devis_lignes, devis_ligne_garanties / INSERT, UPDATE, DELETE | interdit si devis gelé ou non modifiable | 36 |
| TR-12 | bons_commande / UPDATE | colonnes du §7.2 | 36 |
| TR-13 | bc_lignes, bc_ligne_garanties / INSERT, UPDATE, DELETE | interdit si BC gelé | 36 |
| TR-14 | devis, BC / UPDATE | `frozen_at` : NULL → valeur, jamais l'inverse | 34 |
| TR-15 | factures (situation, solde) et reglements (encaissement sur acompte) / AFTER INSERT | pose `frozen_at` sur devis et BC si NULL ; écrit l'événement `gel` | 33 |
| TR-16 | factures / INSERT | BC `en_cours` uniquement ; `client_id` = celui du BC | 47, 48 |
| TR-17 | bons_commande / INSERT | `client_id` = celui du devis ; devis `accepte` | 40, 48 |
| TR-20 | factures / UPDATE | seulement `cancelled_at`/`motif_annulation` (une fois) et `client_id` de rattachement | 53 |
| TR-21 | factures, facture_lignes / DELETE, facture_lignes / UPDATE | interdits | 6, 53 |
| TR-22 | factures / INSERT | acompte ≤ contractuel ; situation : nette après ≤ contractuel et cumul cohérent ; solde = formule 3.2 ; aucun acompte/situation si solde actif | 55 à 58 |
| TR-23 | factures / INSERT (avoir) | origine non avoir, non annulée, même BC ; Σ avoirs actifs ≤ montant origine ; aucun nouveau solde par avoir | 58, 76 |
| TR-24 | factures / UPDATE `cancelled_at` | interdit si encaissement actif ou avoir actif ; acompte/situation : aucune situation/solde actif postérieur ; situation : la dernière active seulement ; pas d'annulation d'un avoir avec remboursement actif | 61, 77 |
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
| TR-95 | numerotation_sequences / UPDATE | `dernier_numero` ne diminue jamais | 22 |

Index uniques (hors UNIQUE de colonnes) : `bons_commande(devis_id)`, `uq_facture_acompte_actif`, `uq_facture_solde_actif`, `uq_situation_actif`, `pv(origine_pv_id, suffixe)`, `garanties(bc_ligne_id, garantie_type)`, `documents(type_entite, entite_id, type_document, numero_version)`, `urssaf_periodes(date_debut)`, `urssaf_periodes(date_fin)`, `urssaf_periode_encaissements` (deux index partiels), `urssaf_details(periode_id)`.

Rappel : les caches du BC et la création des garanties sont faits par le **service**, pas par des triggers.
Chaque trigger et chaque index est créé par la migration de la tranche qui crée sa table (§17.1) : TR-90 et TR-95 par `metier/001_initial.sql`.

---

## 9. Index

Un index **par clé étrangère** (l'index d'un `UNIQUE` qui commence par la FK en tient lieu : `prestation_garanties`), plus les index de recherche :

- clients(statut) · fournisseurs(statut) · prestations(categorie_id) · prestations(actif)
- devis(client_id) · devis(statut) · devis(date_creation) · devis_lignes(devis_id, ordre) · devis_lignes(prestation_id)
- bons_commande(client_id) · bons_commande(statut) · bc_lignes(bc_id, ordre) · bc_lignes(devis_ligne_id)
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
- **Les valeurs dérivées ne sont jamais lues du fichier** : caches du BC (`statut`, `avancement`, `montant_deja_facture_ht`, `date_100_facture`, `completed_at`), `frozen_at` (posé par TR-15), états dérivés du §3.4. V6 les recalcule (§3.7). [INV-169]
- **Sources jamais modifiées**, aucune donnée supprimée en silence : ce que le convertisseur ne peut pas représenter est déclaré dans `anomalies` et conservé (§10.7). [INV-130]
- **Catalogue** : l'import n'ajoute pas le catalogue par défaut V6 ; le catalogue est celui du fichier (D-14). Les référentiels livrés avec V6 (listes fermées, catégories de dépenses D-18, référentiel URSSAF) sont initialisés comme pour toute installation.

### 10.2 Répartition des responsabilités

| Sujet | Convertisseur externe (hors V6) | V6 (import standard) |
|---|---|---|
| Lecture de la sauvegarde V2 | enveloppe, anciennes structures, clés optionnelles, colonnes décalées, renommages | ne lit jamais le format V2 |
| Normalisation | unités (D-13), statuts, types de ligne, catégories, dates, textes | vérifie les énumérations fermées du §2.5 |
| Catalogue, clients | catalogue V2, clients déduits des devis, rapprochements, recodage des codes | vérifie unicité, FK, statut `a_rattacher` (INV-49) |
| Devis, BC, factures | reconstruction des BC et des lignes, totaux et arrondis, composition des factures, snapshots (dont entreprise), `date_acceptation` estimée | applique toutes les formules du §3 et tous les triggers ; gel par TR-15 ; recalcul des caches |
| Paiements | traduction des statuts de paiement en règlements, factures sans statut | règles TR-30/31 comme en fonctionnement normal |
| PV, URSSAF | rattachement des PV à un BC ; saisies URSSAF V2 laissées hors du fichier | PV : TR-40/41 ; aucune donnée URSSAF acceptée (INV-161) |
| Compteurs historiques | récupération, réconciliation avec les numéros présents, conversion en `sequences` | initialise séquences et `sequence_high_water` (§10.6) |
| Anomalies | déclaration dans `anomalies` (`a_verifier`, `non_importe`) ; avertissements informatifs et rapport détaillé dans son propre rapport | stocke `import_anomalies`, affiche le bandeau (§10.7) |

Les règles de transformation V2 → `import-v6.json` (mapping complet, décisions D-13, D-15, D-16, D-17, D-19 et anciens INV-132, 155 à 160, 162) vivent dans le futur document `docs/migration/convertisseur-v2-vers-import-v6.md`. Le journal de `invariants.md` conserve l'énoncé de chaque règle transférée.

### 10.3 Contrat d'entrée `import-v6.json` (principes ; le schéma JSON détaillé est le point P-04)
- **Enveloppe** : `format` = `"import-v6"` ; `contrat_version` (entier) ; `genere_par` (nom et version du convertisseur) ; `genere_le` (timestamp) ; `source` (type, version et date de la sauvegarde d'origine, informatifs) ; `controles` (totaux de contrôle, §10.8).
- **Blocs acceptés** : `parametres_entreprise`, `categories_prestations`, `clients`, `prestations`, `devis` (avec `lignes`), `bons_commande` (avec `lignes`), `factures` (avec `lignes`), `reglements`, `pv`, `sequences`, `anomalies`.
- **Blocs refusés** : `fournisseurs`, `depenses`, `garanties` (et garanties de ligne), planning, notes, documents, `historique`, `urssaf_*`. La V2 ne les fournit pas ; les garanties naissent uniquement de la facturation V6 (INV-134) ; le profil URSSAF est saisi au premier lancement et aucune période n'est calculée avant (INV-161). Ouvrir un bloc supplémentaire = nouvelle `contrat_version`.
- **Objets** : chaque objet porte un `ref` (identifiant local au fichier, unique par bloc) copié dans `legacy_id` ; les références croisées se font par `ref` ; V6 attribue les `id`. Optionnels : `legacy_data` (JSON, données sources non représentables en colonnes, jamais interprétées par V6) et `legacy_numero` (clients et BC seulement).
- **Faits saisis, pas valeurs dérivées** : statut d'un devis, dates, annulations, règlements, snapshots complets (BLOC-SNAP obligatoire), montants sous forme de chaînes décimales à la précision de leur famille (INV-15).
- **Numéros** : BC et codes clients au format V6 ; devis, factures et PV peuvent garder leur numéro historique (§10.4).

### 10.4 Exemption unique : numéros historiques [INV-131]
Les devis, factures (acompte, situation, solde, avoir) et PV `origine='import'` conservent le `numero` qu'ils portaient quand ils ont été remis au client : un numéro déjà émis ne change jamais. Pour eux seulement, le format, le préfixe et l'année du `numero` ne sont pas contrôlés (non vide, unique, immuable par TR-01). Les CHECK de format restent conditionnés par `origine='v6'` sur `devis`, `factures` et `pv` uniquement.
**Tout le reste est appliqué sans exception** : `date_echeance >= date_emission`, `Σ lignes = total_ht`, caps d'acompte / situation / encaissement / remboursement / avoir (TR-22, 23, 31), chronologie ACP/FAC/AVO (TR-02), `bc_lignes.devis_ligne_id` NN, `garanties` NN. Un fichier qui viole une de ces règles est rejeté ; le convertisseur corrige ou déclare la donnée en `non_importe` avant génération.
Les index uniques ne sont pas exemptés non plus (deux acomptes actifs, deux BC pour un devis).

### 10.5 Ordre d'import
paramètres entreprise → catégories → clients → prestations → devis (+ lignes) → BC (+ lignes) → factures (+ lignes), insérées par `date_emission` puis `ref` croissants (TR-02 actif) → règlements par `date_evenement` croissante → PV → `sequences` → `anomalies` → recalcul des caches (§3.7) → CK-01 à CK-12 et totaux de contrôle → événement `import` dans `historique`.
Le gel est posé par TR-15 lors de l'insertion des factures et règlements, comme en fonctionnement normal. Un BC est inséré `en_cours` puis recalculé (`termine` si les conditions du §3.5 sont remplies).

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
Le bloc `controles` du fichier déclare comptages par bloc, Σ `total_ht` des factures actives et Σ `reste_du` attendu. V6 les compare aux valeurs recalculées ; tout écart, ou tout échec de CK-01 à CK-12, annule l'import complet. Après import : profil URSSAF à renseigner (message, pas une erreur).

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
3. lire `user_version` : **refus** si supérieur au schéma supporté ;
4. copier dans un fichier temporaire et y appliquer les migrations de schéma nécessaires ;
5. `PRAGMA integrity_check` ;
6. `PRAGMA foreign_key_check` ;
7. **sauvegarde de sécurité** de la base courante ;
8. remplacement atomique de la base métier ;
9. contrôles post-restauration (CK-xx), puis réouverture.

`machine.db` reste inchangée : mot de passe local, licence, identifiant d'installation, racines et dossier de travail sont conservés. Événement `restauration` écrit dans `historique` après le remplacement.

### 11.3 Documents après restauration
Un `racine_stockage_id` inconnu de la machine courante rend les documents concernés « non localisables » : consultation des métadonnées possible, écran de **remappage** des racines proposé. Une restauration ne rend jamais BATORYA inutilisable parce qu'elle vient d'un autre ordinateur.

### 11.4 Numéros déjà émis et `sequence_high_water` [INV-25]
- **Principe** : un numéro déjà attribué n'est jamais réutilisé ; un trou de numérotation est acceptable. `max_attribue` **ne diminue jamais automatiquement**.
- **Restauration** : après le remplacement, pour chaque `(type_objet, annee)`, `dernier_numero := max(dernier_numero restauré, max_attribue)` et `max_attribue := max(max_attribue, dernier_numero restauré)`. Un avertissement liste les numéros « consommés » que la sauvegarde ne contient plus (des PDF portant ces numéros ont pu être remis à des clients).
- **Démarrage normal** : si `max_attribue > dernier_numero` sans restauration, le service constate un crash entre l'écriture du high-water et le COMMIT. Il **conserve** `max_attribue` : le prochain numéro est `max_attribue + 1` (`dernier_numero` est relevé à `max_attribue`, comme à la restauration). Le trou éventuel est accepté et journalisé. Aucun numéro déjà attribué ne peut être réutilisé.
- **Import de `import-v6.json`** : `sequence_high_water.max_attribue` est initialisé aux `dernier_numero` du fichier (§10.6) ; la règle « jamais de réutilisation » s'applique dès le premier numéro V6.

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
| C-01 | Contractuel 1000.00 ; acompte 200.00 émis, non encaissé | pas de gel ; BC modifiable ; si modifié → acompte annulé automatiquement, réémission possible |
| C-02 | Acompte encaissé 50.00 (partiel) | gel immédiat ; `reste_du` acompte = 150.00 ; `etat_paiement = partiellement_reglee` |
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
| C-19 | Situation annulée, puis BC : annulation directe demandée | refusée (INV-44) |
| C-20 | Solde annulé (impayé) puis réémis | nouveau solde accepté ; garanties inchangées ; `date_100_facture` = date du nouveau solde |
| C-21 | BC arrivé à 100 % il y a 20 jours ; nouvelle dépense rattachée | rattachement normal, sans confirmation |
| C-22 | BC arrivé à 100 % il y a 45 jours ; nouvelle dépense rattachée | message indiquant que le BC est clôturé depuis 15 jours ; confirmation positive → rattachement accepté |

### 13.2 Tests d'intégrité T-01 à T-20 (repris de la V3.4 §99) [INV-167]

À couvrir avant le passage au DDL. T-01 à T-03 sont des tests de concurrence (deux transactions simultanées).

| Test | Énoncé | INV |
|---|---|---|
| T-01 | deux BC simultanés pour un devis → un seul réussit | INV-40 |
| T-02 | deux acomptes actifs simultanés → un seul réussit | INV-52 |
| T-03 | deux soldes actifs simultanés → un seul réussit | INV-52 |
| T-04 | restauration → mot de passe local inchangé | INV-142 |
| T-05 | restauration → licence inchangée | INV-142 |
| T-06 | restauration → dossier de travail inchangé | INV-142 |
| T-07 | modification du catalogue → garantie contractuelle inchangée | INV-37 |
| T-08 | modification du BC après acompte non encaissé → acompte annulé | INV-35 |
| T-09 | premier encaissement → gel irréversible | INV-33, INV-34 |
| T-10 | situation → gel | INV-33 |
| T-11 | solde → gel | INV-33 |
| T-12 | avoir → pas de réouverture du cycle de facturation | INV-58 |
| T-13 | annulation d'un avoir → recalcul financier | INV-79 |
| T-14 | solde annulé → garantie conservée | INV-87 |
| T-15 | levée de réserves → uniquement depuis un PV avec réserves | INV-96 |
| T-16 | import d'un `import-v6.json` de référence → reste dû recalculé = totaux de contrôle du fichier (V3.4 : « migration V2 → comparaison du reste dû ») | INV-133 |
| T-17 | période URSSAF verrouillée → modification directe refusée | INV-125 |
| T-18 | correction URSSAF → historique conservé | INV-125, INV-126 |
| T-19 | facture → somme des lignes égale au total | INV-54 |
| T-20 | numéro → jamais réattribué | INV-22 |

### 13.3 Tests ajoutés : validation et import V6 (T-21 à T-23), numérotation (T-24) — 2026-09-30 ; premier démarrage `machine.db` (T-25), DDL de la première tranche métier (T-26) — 2026-10-01 [INV-170, INV-25, INV-171, INV-172, INV-04, INV-05, INV-14, INV-20, INV-21, INV-22, INV-130, INV-136]

Ces tests ne lisent jamais un fichier V2. Les tests du convertisseur (`TC-xx`) sont définis dans son propre document.

| Test | Énoncé | INV |
|---|---|---|
| T-21 | `import-v6.json` non conforme (clé inconnue, `ref` introuvable, montant hors précision, règle de trigger violée) → rejet total, base métier inchangée | INV-153, INV-154 |
| T-22 | séquences importées → `numerotation_sequences` et `sequence_high_water` initialisés ; premier numéro V6 = `dernier_numero + 1` ; aucun numéro attribué réutilisé ; un saut accepté | INV-135, INV-25 |
| T-23 | import sur base non vide refusé ; document `origine='import'` au numéro historique accepté, même numéro en `origine='v6'` refusé | INV-131, INV-154 |
| T-24 | crash simulé entre l'écriture du high-water et le COMMIT → `max_attribue` conservé, prochain numéro = `max_attribue + 1`, trou journalisé, aucun numéro réutilisé | INV-25, INV-22 |
| T-25 | premier démarrage sur `machine.db` vierge : `user_version=1`, aucune ligne après la migration ; initialisation → `licence`, `services_etat`, `gmail_etat` (`connecte=0`), `preferences_sauvegarde` (1, 30, 1, NULL, NULL) créées avec `id=1` ; création du compte (identifiant, hash argon2id, nom/prénom facultatifs) ; compte sans identifiant, identifiant vide ou hash non argon2id refusé ; second démarrage : `INSERT OR IGNORE` ne modifie ni le compte, ni `identifiant_installation`, ni les préférences changées ; aucun trigger dans la base | INV-171, INV-172, INV-151, INV-08 |
| T-26 | migration `metier/001_initial.sql` sur base vide : `user_version=1` posé par le runner, 7 tables `STRICT` sans aucune ligne, 3 triggers, `foreign_key_check` vide ; `id` jamais réutilisé ; `numerotation_sequences` : attribution par upsert, plafonds 99 999 / 9 999, TR-95 (aucune diminution), `annee=0` ⇔ CLI/FOU ; `import_anomalies` : CHECK de catégorie, TR-90 (DELETE refusé, seule transition `a_traiter` → `traite`) ; `clients` : code `CLI-NNNN` sans exception, `a_rattacher` ⇒ `import`, BLOC-IMP+ ; `prestations` : DL, listes fermées, BLOC-IMP ; suppression d'une prestation → `prestation_garanties` supprimées en CASCADE seulement | INV-04, INV-05, INV-14, INV-20, INV-21, INV-22, INV-130, INV-136 |

---

## 14. Ce que SQLite ne garantit pas (contrôlé par service + requêtes CK)

| Règle | Garde |
|---|---|
| `Σ facture_lignes = total_ht`, `Σ lignes = total` de devis/BC | service à l'émission + CK-05 |
| Montants exacts de situation et de solde | service (formules §3) + tests C-03/C-04 |
| Caches BC (`statut`, `avancement`, `date_100_facture`, …) | service financier unique + CK-06 |
| `date_echeance = date_emission + délai du snapshot` | service |
| Création idempotente des garanties | service + `UQ` |
| Existence des `entite_id` polymorphes, `racine_stockage_id` | CK-09, CK-10 |
| Recalcul des périodes URSSAF | service ; `ca_encaisse = Σ retenu` : CK-08 |
| Insertion de lignes de facture hors transaction d'émission | service ; détection CK-05 |

Requêtes de contrôle exécutées : en test, après import, après restauration, et sur demande :
CK-01 numéros uniques, et conformes au format V6 sauf devis/factures/PV `origine='import'` · CK-02 séquences ≥ max des numéros au format V6 · CK-03 FK (`foreign_key_check`) · CK-04 factures sans lignes · CK-05 `Σ lignes = total_ht` · CK-06 caches BC = recalcul · CK-07 garanties d'un BC ayant un solde actif · CK-08 `ca_encaisse` = Σ retenu · CK-09 `entite_id` existants · CK-10 racines de documents connues · CK-11 périodes URSSAF sans chevauchement · CK-12 (à l'import) totaux de contrôle du fichier = totaux recalculés.

---

## 15. Décisions ajoutées par cette rédaction (D-01 à D-20 validées le 2026-09-29 ; D-21 à D-27 du 2026-09-30 ; D-28 à D-30 du 2026-10-01 ; D-31 du 2026-10-01)

| ID | Décision par défaut | Alternative | Statut |
|---|---|---|---|
| D-01 | Codes clients importés au format `CLI-0001…` (sans exception dans V6), ancien code en `legacy_numero` ; recodage fait par le convertisseur (il n'y a pas de fournisseur à importer) | conserver `CLI-001` V2 (ambiguïté avec `CLI-0001`) | **Validée** 2026-09-29 ; exécution transférée au convertisseur (D-21) |
| D-02 | Timestamps en TEXT ISO UTC `…SSS Z` (retour à la V3.3) | entiers Unix ms | **Validée** 2026-09-29 |
| D-03 | Types de planning : `intervention` et `travaux` rétablis (CDC §26), `bc_id` obligatoire ; `conge`/`indisponibilite` sans BC | types V3.4 seuls | **Validée** 2026-09-29 |
| D-04 | Secrets (licence, jetons Gmail) dans le coffre système ; `machine.db` = états non secrets | tout dans `machine.db` | **Validée** 2026-09-29 |
| D-05 | Annulation directe du BC **interdite** dès qu'une facture autre qu'un acompte non réglé existe (V3.4 conservé), plus strict que CDC §17 (voir errata E-07) | autoriser avec solde impayé et sans situation | **Validée** 2026-09-29 |
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
| D-20 | Lignes de BC : pas de colonne `active`, régénération avant gel, lignes de facture en `RESTRICT` (écart 1 de §18) | rétablir `active`, `updated_at` et identifiants stables (V3.4) | **Validée** 2026-09-29 |
| D-21 | **Migration V2 externalisée** : V2 JSON → convertisseur externe → `import-v6.json` → import standard V6. V6 ne lit pas la V2, n'adapte pas son schéma à la V2 ; V5.16 n'est pas une source | moteur de migration V2 dans V6 (V3.5, §10 ancien) | **Validée** 2026-09-30 (brief Rémy) — erratum E-09 |
| D-22 | `migration_rapports` supprimée (trace = événement `import` de `historique`) ; `migration_quarantaine` remplacée par `import_anomalies` (`a_verifier`, `non_importe`), sans lot d'import | conserver les deux tables génériques | **Validée** 2026-09-30 (intégrée au modèle V3.6 et confirmée par Rémy) |
| D-23 | BLOC-MIG devient BLOC-IMP : `origine` (`v6`/`import`), `legacy_id` (= `ref` du fichier), `legacy_data` ; `migration_id` supprimé ; `legacy_numero` seulement sur `clients` et `bons_commande` ; bloc retiré de `fournisseurs`, `garanties`, `depenses` | garder `migration_id` et le bloc partout | **Validée** 2026-09-30 (intégrée au modèle V3.6 et confirmée par Rémy) |
| D-24 | Exemption unique : `numero` historique libre pour devis, factures et PV `origine='import'` (numéro déjà remis au client) ; toutes les autres exemptions sont supprimées (échéance, Σ lignes, caps, chronologie, NOT NULL) | tout renuméroter au format V6 (`legacy_numero`) | **Validée** 2026-09-30 (intégrée au modèle V3.6 et confirmée par Rémy) |
| D-25 | Lecteur strict : fichier non conforme rejeté en bloc, jamais réparé ni mis en quarantaine par V6 ; valeurs dérivées (caches BC, gel) jamais lues du fichier | lecteur tolérant (V3.5) | **Validée** 2026-09-30 (brief Rémy) |
| D-26 | Compteurs V2 compatibles récupérés par le convertisseur, transmis dans `sequences` ; V6 initialise séquences et high-water ; un saut est acceptable, aucune réutilisation | séquences V6 vides après migration (V3.5) | **Validée** 2026-09-30 (brief Rémy) |
| D-27 | `max_attribue` ne diminue jamais automatiquement ; s'il dépasse `dernier_numero` au démarrage, il est conservé, le trou est accepté et journalisé (corrige la contradiction du §11.4 de la V3.6) | abaisser `max_attribue` à `dernier_numero` (risque de réattribuer un numéro déjà attribué) | **Validée** 2026-09-30 (brief Rémy) |
| D-28 | Compte local **obligatoire** au premier démarrage : `utilisateur_local.identifiant` TEXT NOT NULL UNIQUE (non vide), `mot_de_passe_hash` NOT NULL (argon2id) ; `nom` et `prenom` facultatifs | profil local facultatif, mot de passe facultatif (V3.7) | **Validée** 2026-10-01 (réponse de Rémy) |
| D-29 | Préférences de sauvegarde par défaut : automatique activée, toutes les 30 minutes (`frequence_minutes` NOT NULL défaut 30, remplace `frequence_jours`), sauvegarde à la fermeture activée ; `derniere_sauvegarde_statut` NULL avant la première sauvegarde, puis `succes` / `echec` | fréquence en jours, sauvegarde automatique désactivée par défaut | **Validée** 2026-10-01 (réponse de Rémy) |
| D-30 | `machine.db` sans trigger : INV-25 et INV-106 restent des gardes de service (conforme au registre) ; pas de garde d'immutabilité sur `identifiant_installation` ; singletons jamais insérés par le DDL, créés par le service d'initialisation (`INSERT OR IGNORE`) | triggers de protection en base ; singletons insérés par la migration | **Validée** 2026-10-01 (réponse de Rémy) |
| D-31 | **Dépenses tardives sur BC** : à compter de `date_100_facture`, rattachement normal pendant 30 jours calendaires ; passé ce délai, le BC est considéré clôturé pour les nouvelles dépenses mais reste toujours rattachable après une confirmation simple indiquant le nombre de jours écoulés ; aucun déblocage, autorisation ou délai maximal supplémentaire | blocage définitif après 30 jours ; procédure de déblocage dédiée | **Validée** 2026-10-01 (réponse de Rémy) |

### Points à figer avant le DDL (P-xx)
- **P-01** *(clos)* : unités figées par D-13 ; catégories de prestations = 13 du catalogue par défaut V5.16 + `Revêtement` ; le mapping des types de planning est sans objet (aucune donnée de planning n'est importée) ; liste initiale des catégories de dépenses figée par D-18.
- **P-02** *(clos sur l'échantillon)* : quantités et prix unitaires V2 ≤ 2 décimales ; totaux V2 non arrondis jusqu'à 5 décimales et artefacts flottants ⇒ INV-15. Le convertisseur refait la mesure sur la sauvegarde réelle ; V6 rejette tout montant hors précision (INV-15).
- **P-04** *(ouvert)* : schéma JSON détaillé du contrat `import-v6.json` (champs, types, exemples) ; à écrire avec le document du convertisseur, avant l'implémentation de l'import. Bloque l'import, pas le DDL des tables (D-22 est validée : `import_anomalies` est figée). Deux points y sont ajoutés par la V3.9 (§4.17, points 7 et 10) : liste des valeurs admises de `import_anomalies.type_entite` (définie par le contrat, sans CHECK en base), et sort du `ref` des objets du bloc `categories_prestations` (BLOC-IMP absent des listes).
- **P-03** *(clos)* : une prestation V5.16 porte une seule garantie ; le modèle multi-garanties est conservé, le catalogue par défaut n'en utilise qu'une.

---

## 16. Matrice de non-régression (règles déjà perdues une fois)

| Règle perdue dans une version | Rétablie ici |
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

---

## 17. Critères de sortie de la V3.9 et suivi des migrations

Le modèle est prêt pour le DDL lorsque :
1. chaque INV de `invariants.md` a une garde désignée et un nom de test ; les tests T-01 à T-20 (§13.2) et T-21 à T-26 (§13.3) sont écrits ;
2. D-01 à D-12 sont validées (fait le 2026-09-29) ; D-13 à D-17 sont validées (fait le 2026-09-29) ; D-21 à D-27 validées (2026-09-30) ; D-28 à D-30 validées (2026-10-01) ;
3. D-18, D-19 et D-20 sont validées (P-01 soldé, fait) ; D-16 est tranchée (aucune garantie recréée, fait) ;
4. les errata E-01 à E-09 sont au fichier `cdc-errata-v6.md` ;
5. l'ordre du DDL est : `machine/001` (indépendant) puis métier : import_anomalies → séquences → listes → clients/fournisseurs → catalogue → devis → BC → factures → règlements → garanties → PV → dépenses → planning → documents → historique → paramètres → URSSAF. Chaque tranche est une migration distincte, accompagnée de ses triggers, de ses index et de ses tests ; le modèle passe à la version suivante **avant** chaque migration (§17.1).

### 17.1 Suivi des migrations

| Migration | Contenu | Modèle | Test |
|---|---|---|---|
| `src-tauri/migrations/machine/001_initial.sql` | `machine.db` : 7 tables (§5) | V3.8 | T-25 |
| `src-tauri/migrations/metier/001_initial.sql` | `import_anomalies`, `numerotation_sequences`, `categories_prestations`, `categories_depenses`, `clients`, `prestations`, `prestation_garanties` ; TR-90, TR-95 | V3.9 | T-26 |

Tranches suivantes (ordre du critère 5) : fournisseurs et dépenses, devis, BC, factures, règlements, garanties, PV, planning, documents, historique, paramètres, URSSAF.

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
| §18-20 Création du BC, BC, lignes de BC | §4.7 · INV-38, 40 · **voir écart 1** |
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
1. **Lignes de BC** : la V3.4 prévoyait `bc_lignes.active`, `updated_at` et des identifiants stables. La V3.5 supprime `active` et régénère les lignes avant gel (§4.7, INV-38). Ce changement vient du point « lignes de BC / lignes de facture » de l'audit V3.4 ; il reste sûr parce qu'aucune facture ne référence une ligne BC avant le gel et que `facture_lignes.bc_ligne_id` est en `RESTRICT`. **Validé** par Rémy (D-20, 2026-09-29) ; contrainte associée : INV-168.
2. **BC terminé** : la V3.4 disait « solde actif et reste dû du solde = 0 ». Arbitrage 1 du 2026-09-29 : Σ reste dû des factures actives hors avoir = 0.
3. **Types de planning** : `intervention` et `travaux` rétablis (CDC §26, D-03) ; ils manquaient à la V3.4.
4. **Migration** : la source est la V2 (la V5 n'a jamais été distribuée) ; `complete → solde` sans objet ; les règles V2 (D-13 à D-19) sont désormais portées par le convertisseur (écart 6).
5. **Timestamps** : TEXT ISO UTC (D-02).
6. **Migration V2 externalisée (2026-09-30, V3.6)** : la première rédaction de la V3.5 embarquait un mode migration dans SQLite (`origine='migration'`, exemptions, `migration_rapports`, `migration_quarantaine`, compteurs jamais importés). Elle est remplacée par le flux V2 JSON → convertisseur externe → `import-v6.json` → import V6 (§10, D-21 à D-26, E-09). Retirés : mode migration, exemptions sauf le format du `numero` historique, `migration_id`, les deux tables de migration, le lecteur V2 tolérant. Aucune autre règle métier validée n'est modifiée ; en revanche `garanties.bc_ligne_id`, `garanties.facture_declenchement_id` et `bc_lignes.devis_ligne_id` sont NOT NULL sans condition, et les CHECK d'échéance, de format BC/CLI et de Σ lignes n'ont plus de condition d'origine.
7. **Numérotation (2026-09-30, V3.7)** : la V3.6 abaissait `max_attribue` à `dernier_numero` au démarrage normal, ce qui pouvait réattribuer un numéro déjà attribué. Corrigé : `max_attribue` ne diminue jamais, le trou est accepté et journalisé (§11.4, D-27, INV-25, T-24). Aucun nouveau mécanisme de numérotation.
8. **`machine.db` (2026-10-01, V3.8)** : compte local obligatoire avec identifiant (D-28), préférences de sauvegarde en minutes avec valeurs par défaut (D-29), aucun trigger dans `machine.db` et singletons créés par le service d'initialisation (D-30). Le DDL `machine/001_initial.sql` est aligné sur ce §5.
9. **Première tranche métier (2026-10-01, V3.9)** : traduction SQL de `import_anomalies`, des séquences, des listes, des clients et du catalogue ; aucune règle nouvelle (§4.17). Le jeu de données d'installation (listes, catalogue par défaut) reste hors migration.
