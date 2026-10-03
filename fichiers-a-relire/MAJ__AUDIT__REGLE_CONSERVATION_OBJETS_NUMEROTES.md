# BATORYA Essentiel V6 — Audit de la règle de conservation des objets numérotés

**Version 2** — mise à jour après validation des décisions D1 à D5 (D6 reste ouverte), le 2026-10-02.

> **Mise à jour documentaire du 2026-10-03 (en relecture, annotation de la version 2 — rien n'est réécrit).** Les arbitrages Q1–Q27 ont tranché ou modifié plusieurs points de cet audit ; le texte d'origine est conservé et chaque passage concerné doit être lu avec les renvois suivants (errata E-10 à E-20, invariants INV-179 à INV-196, modèle SQLite V3.13) :
> - **D2 (archivage des clients/fournisseurs, § 3.1, § 3.2, § 4.5)** : **remplacé** — conservation permanente, aucun archivage, aucun statut, `a_rattacher` supprimé (E-12, INV-183) ; Q-4 (immutabilité du code) et Q-5 (cycle de vie `a_rattacher`) sont traitées par cette décision (mécanismes : PT-3, PT-4).
> - **D3 (« aucune suppression, même d'un brouillon », § 3.3)** : **précisé** — un devis brouillon, sans numéro, est supprimable ; tout objet numéroté est conservé (E-10, INV-180, Q5/Q11) ; Q-6 est traitée (annulation d'un devis : statut, motif, historique).
> - **§ 3.6 (factures `cancelled_at`)** : **remplacé** — une facture validée n'est plus annulée ; correction par avoir (E-14, INV-185) ; mécanisme : PT-9.
> - **Q-1 (numéro attribué dans une transaction rollbackée)** : **tranchée (second envoi du 2026-10-03)** — un numéro définitif n'est jamais attribué deux fois ; un trou après crash ou rollback est acceptable et n'est jamais récupéré (E-13, INV-179, D-54). Le mécanisme actuel est conforme sauf sur deux points (réattribution après rollback propre, high-water perdu) : **correction proposée, non validée** (modèle §11.4, PT-1).
> - **Q-3 (numéros importés)** : inchangée. **Q-7 (annulation des dépenses)** : tranchée sur le principe (E-19, INV-193 ; mécanisme PT-14). **Q-8 (numéro de situation)** : voir INV-190, PT-11.
> - **§ 3.4 (BC)** : conformité maintenue pour la suppression ; l'annulation du BC n'annule plus les devis (E-15) et un BC peut regrouper plusieurs devis (E-16).
> Les anomalies techniques du § 4 (suppressions possibles, codes modifiables, `INSERT OR REPLACE`) restent exactes sur 001–004 ; leurs corrections passent par des migrations ultérieures (modèle §4.19, PT-20), jamais en réécrivant 001–004.
**Statut** : rapport d'audit. Aucun fichier officiel, aucune migration, aucun test ni aucun code n'a été modifié. Ce rapport ne contient **aucun SQL** et ne propose **aucune décision métier nouvelle**.
**Base** : dépôt `mymypav-max/BATORYA-Essentiel`, branche `main`, commit `c03c71b` (migrations 001–004 intégrées et inchangées depuis la version 1 de l'audit). Les numéros de ligne cités se rapportent à ce commit.
**Consulté** (lecture intégrale ou recherche ciblée) : `docs/README.md`, audit fonctionnel, `invariants.md`, modèle SQLite V3.12, modèle métier, errata, CDC, conventions, migrations `metier/001–004` et `machine/001`, tests `test_001` à `test_004`, cadrage 005.
**Revérifié pour cette version** : tous les constats de la version 1 ont été rejoués sur une base construite avec 001→004 (`foreign_keys=ON`, `recursive_triggers=ON`) : **ils restent exacts**. Les quatre suites de tests existantes passent (28 + 18 + 68 + 150 tests). Une variante supplémentaire de la faille `INSERT OR REPLACE` a été trouvée (E-4, variante 3).

**Étiquettes de source**

| Étiquette | Sens |
|---|---|
| **[VALIDÉ]** | décision validée par Rémy (D1 à D5) |
| **[DOC]** | règle déjà écrite dans un document (fichier, section ou ligne) |
| **[SQL]** | comportement réellement présent dans une migration (fichier, trigger) |
| **[CONSTATÉ]** | comportement vérifié par exécution sur 001→004 (annexe A) |
| **[TEST]** | comportement affirmé par un test existant |
| **[DÉD]** | déduction technique |
| **[ÉCART]** | écart à corriger |

---

## 0. Résumé

### 0.1 Ce qui est désormais acquis

La règle transversale de conservation est **validée** (D1). Elle s'applique aux clients et fournisseurs sans condition d'archivage (D2), au devis y compris brouillon (D3), à la dépense (D5). Les failles techniques identifiées sont **à corriger indépendamment de la règle** (D4). Le sort du numéro de situation est **explicitement ouvert** (D6).

### 0.2 Anomalies techniques constatées (inchangées, revérifiées)

| # | Constat | Nature |
|---|---|---|
| **E-1** | `clients` : suppression directe possible dès qu'aucun devis/BC ne le référence, **même archivé** | Écart à la règle |
| **E-2** | `fournisseurs` : idem | Écart à la règle |
| **E-3** | `devis` : suppression directe possible **dans les quatre statuts** tant qu'aucun BC n'existe (lignes supprimées en cascade) | Écart à la règle (règle contraire documentée : D-33) |
| **E-4** | `INSERT OR REPLACE` contourne l'immutabilité et les protections de cycle de vie sur `clients`, `fournisseurs`, `devis`, en **trois variantes** (4.4) | **Faille indépendante de la règle** (D4) |
| **E-5** | `clients.code` et `fournisseurs.code` **modifiables** : un numéro peut être libéré puis réattribué | Écart à la règle |
| **E-6** | Après suppression ou libération, le SQL accepte la réinsertion d'un numéro déjà consommé | Limite à connaître |
| **E-7** | Cycle de vie du client `a_rattacher` : aucun document ne dit ce qu'il devient après rattachement | Sujet à traiter séparément (D2) |
| **E-8** | `situation_numero` réutilisable après annulation d'une situation | **Ouvert** (D6) |
| **E-9** | La restauration d'une sauvegarde supprime physiquement des objets postérieurs | Cas technique distinct (D1) |

### 0.3 Conformité par objet (détail en section 3)

Conformes : **BC**, **séquences** (`numerotation_sequences`), `import_anomalies`. Conformes par conception documentée, à vérifier à l'écriture : **facture/acompte/avoir**, **PV**. Non conformes : **client, fournisseur, devis**. À concevoir conformes : **dépense**.

### 0.4 Ce qui a changé par rapport à la version 1

| Élément | Version 1 | Version 2 |
|---|---|---|
| Règle | formulation proposée, périmètre à valider | **texte validé (D1)** + précisions rollback et restauration |
| Recommandations | propositions `[PROP]` et recommandations sur D1–D6 | **retirées** : les décisions sont celles de Rémy ; aucune proposition nouvelle |
| Client a_rattacher | proposition d'archivage | **renvoyé à un traitement séparé** (D2) |
| Annulation du devis | présentée comme sortie | **constat uniquement** ; détail du mécanisme renvoyé au cadrage (D3) |
| Véhicule des corrections SQL | option recommandée | **volontairement non tranché** (D4) ; impacts décrits sans choix |
| Dépense | Q2 ouverte, Q3 rouverte | D5 **valide** : jamais supprimée ; annulation métier ; **dépense créable et rattachable à un BC annulé** |
| `INSERT OR REPLACE` | deux variantes | **trois variantes** (nouvelle : conflit sur le numéro) ; `recursive_triggers=ON` déclaré insuffisant |
| Conséquences transversales | dispersées | **section 8 dédiée** |
| Annexe de vérification | énoncés d'essais | **décrite en langage courant, sans SQL** |

---

## 1. Règle générale validée

### 1.1 Texte validé (D1) **[VALIDÉ]**

> Tout objet métier auquel BATORYA attribue un numéro définitif ne peut jamais être physiquement supprimé après attribution et validation de l'opération. Il peut être modifié lorsque son cycle de vie l'autorise, ou annulé lorsque le métier le prévoit, mais son enregistrement et son numéro sont conservés. Tout numéro attribué est définitivement consommé et ne peut jamais être réutilisé, y compris après annulation. Les trous de numérotation sont normaux.

**Précisions validées**

1. **Rollback** : une opération annulée par rollback **avant** sa validation (COMMIT) n'est pas considérée comme la suppression d'un objet métier ayant reçu un numéro définitivement consommé.
2. **Restauration** : la restauration d'une sauvegarde est un **cas technique distinct** ; elle n'est pas assimilée à une suppression métier.

### 1.2 Décisions associées **[VALIDÉ]**

| # | Décision | État |
|---|---|---|
| **D1** | Règle transversale ci-dessus | Validée |
| **D2** | **Clients et fournisseurs** : la règle ne se limite pas aux objets archivés ; tout client ou fournisseur ayant reçu un code définitif est conservé ; pas de suppression physique ; code non réutilisable ; **code immuable après attribution** « selon les règles qui seront définies techniquement » ; l'archivage reste un mécanisme métier **distinct** de la suppression. Le cycle de vie du client `a_rattacher` est **hors de cette décision** | Validée |
| **D3** | **Devis** : plus aucune suppression physique, **y compris brouillon / `en_attente` jamais envoyé, accepté ou associé à un BC**. Le devis conserve son numéro et son historique ; l'annulation passe par le cycle de vie métier approprié. Le détail du mécanisme d'annulation des devis est renvoyé à un cadrage ultérieur | Validée |
| **D4** | **Corrections techniques** : les failles (DELETE possible, `INSERT OR REPLACE`, codes modifiables ou réutilisables) sont à corriger **même indépendamment** de la règle ; `PRAGMA recursive_triggers=ON` **n'est pas considéré comme suffisant** ; la **migration d'intégration n'est pas décidée** (005, migration dédiée, ou autre organisation) | Validée, intégration ouverte |
| **D5** | **Dépenses** : jamais supprimée après attribution de son numéro ; mécanisme métier d'**annulation** ; une dépense annulée reste conservée avec son numéro, son historique, ses rattachements et ses données de traçabilité ; **une nouvelle dépense peut être créée et rattachée à un BC déjà annulé** (règle métier volontaire) ; le BC annulé reste un conteneur historique et économique conservé | Validée |
| **D6** | **Numéro de situation** : à examiner au cadrage de la Facturation | **Ouverte** |

### 1.3 Ce que les documents disaient déjà

| Énoncé existant | Source | Rapport avec D1 |
|---|---|---|
| « Un numéro déjà attribué n'est jamais réutilisé ; un trou de numérotation est acceptable » | **[DOC]** Métier l.69 ; CDC §19 l.590 ; Audit fonctionnel l.510, l.559 ; Modèle §6 l.557 (« même après annulation ») ; INV-22, INV-25, INV-135 ; Métier l.812 (« même après annulation, restauration ou incident ») | Clauses « numéro consommé » et « trous » **déjà documentées** |
| « Aucune suppression physique des entités historiques (clients/fournisseurs/prestations **utilisés**, devis **avec BC**, tout BC, factures, règlements, PV, garanties, historique) » | **[DOC]** INV-06 (invariants l.25) | Formulation **conditionnelle**, plus étroite que D1 |
| « Un client ayant un historique n'est jamais supprimé ; il est archivé » | **[DOC]** Modèle §4.4 l.273 ; Métier l.103 ; Audit fonctionnel l.103 | Conditionnelle, plus étroite que D2 |
| « Un fournisseur ayant un historique est archivé, jamais supprimé » | **[DOC]** Modèle §4.4 l.275 ; Métier l.501 ; Audit fonctionnel l.235 | idem |
| « Un devis sans BC peut être supprimé physiquement ; ses lignes et garanties sont supprimées en CASCADE » | **[DOC]** Modèle §4.6 l.299 ; Métier l.182 ; D-33 ; en-tête de `003_devis.sql` l.17-19 | **Contraire à D3** |
| « Aucun BC n'est jamais supprimé physiquement » | **[DOC]** INV-174 ; Modèle §4.7 l.331 ; D-35 | Conforme à D1 |
| « Un document émis, un règlement, une garantie, un PV ou un événement d'historique n'est jamais supprimé pour corriger une erreur : il est annulé (date et motif) ou corrigé par un document opposé (avoir) » | **[DOC]** Métier §2.4 l.79 | Conforme à D1 pour les objets cités ; **ne cite ni client, ni fournisseur, ni devis, ni dépense** |
| Aucune règle de suppression ni d'annulation de la **dépense** | **[DOC]** (silence) | Défini par D5 |

---

## 2. Inventaire des objets numérotés

### 2.1 Objets numérotés

| Objet | Format | Table / colonne | Séquence | Tranche | État |
|---|---|---|---|---|---|
| Client | `CLI-0001` | `clients.code` | `CLI`, année 0, plafond 9 999 | **001** | implémenté |
| Fournisseur | `FOU-0001` | `fournisseurs.code` | `FOU`, année 0, plafond 9 999 | **002** | implémenté |
| Devis | `DEV-00001-26` (numéro historique libre si `origine='import'`, INV-131) | `devis.numero` | `DEV` par année | **003** | implémenté |
| Bon de commande | `BCD-00001-26` | `bons_commande.numero` | `BCD` par année | **004** | implémenté |
| Dépense | `DEP-00001-26` | `depenses.numero` | `DEP` par année | 005 | à concevoir |
| Facture (situation, solde) | `FAC-00001-26` | `factures.numero` | `FAC` partagée | 006 | documenté |
| Acompte | `ACP-00001-26` | `factures.numero` (`type='acompte'`) | `ACP` | 006 | documenté |
| Avoir | `AVO-00001-26` | `factures.numero` (`type='avoir'`) | `AVO` | 006 | documenté |
| PV initial | `PVR-00001-26` | `pv.numero` | `PVR` par année | 009 | documenté |
| Levée de réserves | `PVR-00001-26-01` | `pv.numero` + `pv.suffixe` | **aucune** (suffixe = max + 1 par PV d'origine) | 009 | documenté |

Sources : Modèle §6 (l.539-553) **[DOC]** ; liste fermée `type_objet` de `numerotation_sequences` : `CLI`, `FOU`, `DEV`, `BCD`, `ACP`, `FAC`, `AVO`, `PVR`, `DEP` **[SQL]** (001 l.80).

### 2.2 Éléments à numéro **sans** numérotation définitive propre (aucune règle créée)

| Élément | Pourquoi il n'est pas concerné |
|---|---|
| **Réserves** | `pv.reserves` est un **champ texte** (Modèle §4.11 l.413). Elles n'ont pas de numéro propre. Seule leur **levée** est un PV numéroté. **Non applicable** |
| Règlement, garantie, historique, document | pas de numéro métier (`id` seulement) ; déjà « jamais supprimés » (TR-32, TR-50, TR-60, TR-70) |
| Prestation (`reference`) | référence de catalogue ; une prestation est même **supprimée du catalogue V6** (CDC l.365) ; « jamais supprimée si utilisée » (INV-06) |
| Catégories (`code`) | listes modifiables de l'utilisateur |
| `documents.numero_version` | compteur de versions ; aucun DELETE (TR-70) |
| `devis_lignes.ordre`, `bc_lignes.ordre`, `facture_lignes.ordre` | ordinaux de présentation |
| **`factures.situation_numero`** | ordinal par BC ; **D6 ouverte** |
| `id` (toutes tables) | `AUTOINCREMENT`, jamais réutilisé (INV-04) ; **[TEST]** `test_INV_04_*` dans 001–004 |

---

## 3. Résultat par objet (au regard de la règle validée)

### 3.0 Vue d'ensemble

| Objet | Verdict | Motif en une ligne |
|---|---|---|
| Client | **Non conforme** | suppression possible ; `code` modifiable ; REPLACE possible (E-1, E-4, E-5) |
| Fournisseur | **Non conforme** | idem (E-2, E-4, E-5) |
| Devis | **Non conforme** | suppression possible dans tous les statuts sans BC ; REPLACE contourne l'immutabilité (E-3, E-4) |
| Bon de commande | **Conforme** | TR-19 + FK `RESTRICT` ; annulation sans suppression |
| Dépense | **Non applicable (à concevoir)** | table inexistante ; conformité exigée par D5 (section 7) |
| Facture / Acompte / Avoir | **Conforme sur le papier** | TR-21 (DELETE interdit), `cancelled_at` ; à vérifier à l'écriture de 006 |
| PV / Levée | **Conforme sur le papier** | TR-40 ; la non-suppression est la seule garde contre la réutilisation d'un suffixe |
| Réserves | **Non applicable** | pas de numérotation propre |
| `numerotation_sequences` | **Conforme** | TR-95 (UPDATE) + TR-96 (DELETE, y compris REPLACE) |
| `sequence_high_water` | **Conforme, garde de service** | aucun trigger dans `machine.db` (D-30) |

### 3.1 Client — **NON CONFORME**

| # | Critère | Constat |
|---|---|---|
| 1-3 | Objet / format / migration | Client ; `CLI-0001` ; **001** (`clients`, séquence `CLI` année 0). `code` : `UNIQUE`, contrôle de format **[SQL]** 001 l.146 |
| 4 | Suppression actuelle | **[DOC]** « jamais supprimé s'il a un historique » (Modèle l.273, Métier l.103). **[SQL]** **aucun trigger de suppression** sur `clients` ; seules gardes : FK `RESTRICT` de `devis.client_id` (003 l.61) et `bons_commande.client_id` (004 l.78). **[CONSTATÉ]** A1, A4 : la suppression directe est acceptée pour un client sans devis ni BC, **y compris archivé** |
| 5 | Annulation | aucune ; l'équivalent métier est `statut='archive'`, réversible (T3, T4). `a_rattacher` réservé à l'import (001 l.163) |
| 6 | Modification | **[CONSTATÉ]** U1 : le `code` est **modifiable** ; **[SQL]** aucun trigger sur `clients` ; TR-01 ne couvre que devis, BC, factures, PV, dépenses (Modèle §8 l.601) |
| 7 | Protection contre la réutilisation | compteur `CLI` (TR-95, TR-96) + high-water. **Pas** de protection structurelle une fois la ligne supprimée ou le `code` modifié |
| 8 | Suppression physique | suppression directe ; **REPLACE** (C1, R1) |
| 9 | ON DELETE | `devis.client_id`, `bons_commande.client_id` : `RESTRICT` — non problématique |
| 10 | Conformité | non conforme à D1 et D2 (suppression, code mutable) |
| 11 | Contradiction | avec INV-06, non (INV-06 est conditionnel) ; avec D2, oui. Test qui consacre le comportement actuel : **[TEST]** `test_003` l.705-706 |
| 12 | Correction | **[ÉCART]** garde de non-suppression ; immutabilité du code ; clarification documentaire. Voir section 6 |

### 3.2 Fournisseur — **NON CONFORME**

| # | Critère | Constat |
|---|---|---|
| 1-3 | Objet / format / migration | Fournisseur ; `FOU-0001` ; **002** (`fournisseurs.code`, séquence `FOU` année 0) |
| 4 | Suppression actuelle | **[DOC]** « ayant un historique : archivé, jamais supprimé » (Modèle l.275, Métier l.501). **[SQL]** 002 l.28-31 : le contrôle de suppression est « la FK RESTRICT de `depenses.fournisseur_id`, créée par la tranche des dépenses ». **Aucune FK entrante n'existe encore** : à ce jour rien n'empêche la suppression. **[CONSTATÉ]** A2, A2b : suppression acceptée, **même archivé** |
| 5 | Annulation | aucune ; `statut` ∈ `actif`, `archive` |
| 6 | Modification | **[CONSTATÉ]** U2 : `code` modifiable |
| 7 | Protection contre la réutilisation | compteur `FOU` ; **[TEST]** `test_002` l.183-189 `test_INV_22_numero_jamais_reutilise` **supprime** des fournisseurs puis vérifie que le compteur continue : il décrit le comportement que D2 n'autorise plus |
| 8 | Suppression physique | suppression directe ; **REPLACE** (C3, R2) |
| 9 | ON DELETE | aucun aujourd'hui ; futur `depenses.fournisseur_id` : `RESTRICT` — non problématique |
| 10 | Conformité | non conforme à D1 et D2 |
| 11 | Contradiction | **[TEST]** `test_002` l.160-165 `test_INV_05_aucune_fk_et_suppression_sans_historique` affirme la suppression sans historique |
| 12 | Correction | **[ÉCART]** idem client |

### 3.3 Devis — **NON CONFORME** (règle contraire documentée)

| # | Critère | Constat |
|---|---|---|
| 1-3 | Objet / format / migration | Devis ; `DEV-00001-26` (numéro historique libre si `origine='import'`) ; **003** |
| 4 | Suppression actuelle | **[DOC]** « Un devis sans BC peut être supprimé physiquement ; ses lignes et garanties sont supprimées en CASCADE » (Modèle §4.6 l.299 ; Métier l.182 ; D-33). **[SQL]** 003 l.17-19 : « aucun trigger sur DELETE devis » ; la garde « devis avec BC » est la FK `RESTRICT` `bons_commande.devis_id` (004 l.77). **[CONSTATÉ]** A3 : suppression acceptée pour **les quatre statuts**, lignes supprimées en cascade, y compris `refuse` et `annule` |
| 5 | Annulation | **[SQL]** `statut='annule'` + `cancelled_at` + `motif_annulation` existent ; **[CONSTATÉ]** T1 : le passage `en_attente → annule` est possible. Le devis annulé est immuable (TR-10). Le détail du mécanisme d'annulation relève du cadrage ultérieur prévu par D3 |
| 6 | Modification | `numero` et `date_creation` immuables (TR-01) **[CONSTATÉ]** U4, U5 ; devis `refuse`/`annule` immuable (TR-10) |
| 7 | Protection contre la réutilisation | compteur `DEV` ; `UNIQUE(numero)` tant que la ligne existe (B3), **mais** non effectif face à REPLACE (R3) ; **[CONSTATÉ]** B1 : après suppression, réinsertion du numéro acceptée |
| 8 | Suppression physique | suppression directe ; **REPLACE** : C4 (par identifiant), R3 (par conflit sur le numéro) |
| 9 | ON DELETE | `devis_lignes.devis_id` en **CASCADE** : le seul CASCADE qui atteint les données d'un objet numérotable. Il contourne `tr_11_devis_lignes_delete` (la ligne parente est déjà supprimée quand le trigger s'exécute, cf. 004 l.462-463) : un devis `refuse`/`annule` perd ses lignes |
| 10 | Conformité | non conforme à D1 et D3 ; l'immutabilité TR-10 est contournable (E-4) |
| 11 | Contradiction | **règle documentée contraire** (D-33, Modèle l.299, Métier l.182). **[TEST]** `test_003` l.721-731 `test_INV_06_suppression_d_un_devis_sans_garde_dans_cette_tranche` porte la mention *« À reconsidérer avec la tranche BC »* ; `test_004` l.1789-1798 reconduit « sans BC : supprimé en CASCADE ». Le point n'avait jamais été rouvert avant D3 |
| 12 | Correction | **[ÉCART]** D-33 à remplacer ; garde de non-suppression ; documentation. Le CASCADE `devis_lignes` reste utilisé par la régénération des lignes avant gel (INV-38), qui supprime des lignes **sans** supprimer le devis : son devenir est un point de conception de la correction |

### 3.4 Bon de commande — **CONFORME**

| # | Critère | Constat |
|---|---|---|
| 1-3 | Objet / format / migration | BC ; `BCD-00001-26` ; **004** |
| 4 | Suppression actuelle | **[DOC]** INV-174, D-35, Modèle §4.7 l.331. **[SQL]** `tr_19_bons_commande_no_delete` (004 l.411), toujours refusé ; FK `RESTRICT` sur `bc_lignes.bc_id`. **[TEST]** `test_004` l.2256-2275 |
| 5 | Annulation | `statut='annule'`, terminal (INV-173, TR-12) |
| 6 | Modification | `numero`, `date_creation` immuables (TR-01, 004 l.287) ; BC annulé : `client_id` de rattachement et `updated_at` seulement |
| 7 | Protection contre la réutilisation | ligne conservée ; compteur `BCD` ; **[TEST]** `test_004` l.790-801 |
| 8 | Suppression physique | aucune ; REPLACE refusé car `tr_19` existe et `recursive_triggers=ON` (**[TEST]** `test_004` l.2177) |
| 9 | ON DELETE | tous `RESTRICT` (sauf `bc_ligne_garanties` → ligne, CASCADE) |
| 10-12 | Conformité | **conforme, aucune correction** : modèle de référence de la règle |

### 3.5 Dépense — **NON APPLICABLE (à concevoir)**

Table inexistante. **[DOC]** numéro `DEP-00001-26`, TR-01 (Modèle §4.12 l.418-419, §8 l.601). Règles validées par D5 : section 7.

### 3.6 Facture, acompte, avoir — **CONFORME SUR LE PAPIER** (non implémenté)

| # | Critère | Constat |
|---|---|---|
| 1-3 | Objet / format / migration | `FAC-`, `ACP-`, `AVO-00001-26` ; table `factures` ; tranche **006** |
| 4 | Suppression | **[DOC]** « jamais supprimée » (INV-53 ; INV-78 ; CDC l.532, l.645 ; TR-21, Modèle §8 l.614) |
| 5 | Annulation | `cancelled_at` + `motif_annulation`, irréversible (INV-61, TR-24 ; Modèle §4.8) |
| 6 | Modification | immuable dès l'INSERT, hors `cancelled_*` et rattachement client (INV-53, TR-20) |
| 7 | Protection contre la réutilisation | ligne conservée + compteur ; chronologie TR-02 |
| 8-9 | Suppression physique / ON DELETE | `facture_lignes.facture_id` en `RESTRICT` (Modèle l.386) |
| 10-12 | Conformité | conforme **par conception**. À contrôler à l'écriture de 006 : voir section 8 ; `situation_numero` : D6 ouverte |

### 3.7 PV et levée de réserves — **CONFORME SUR LE PAPIER**, avec un point de vigilance

| # | Critère | Constat |
|---|---|---|
| 1-3 | Objet / format / migration | `PVR-00001-26` ; levée `PVR-00001-26-01` ; `pv` ; tranche **009** |
| 4 | Suppression | **[DOC]** « Immuable dès l'INSERT (aucun UPDATE, aucun DELETE) » (Modèle §4.11 l.414 ; INV-95 à 97 ; TR-40 ; CDC §23) |
| 5 | Annulation | **aucune** : `pv` n'a ni `cancelled_at` ni statut (Modèle §4.11). Conforme à « annulé lorsque le métier le prévoit » |
| 7 | Protection contre la réutilisation | PV initial : compteur `PVR`. **Levée : aucune séquence**, `suffixe = max + 1` calculé sur les lignes existantes (TR-41). **[DÉD]** la seule protection contre la réutilisation d'un suffixe est l'**interdiction de supprimer** une levée |
| 11 | Contradiction | **[DOC]** Métier §2.4 l.79 range le PV parmi ce qui est « annulé (date et motif) » alors que le modèle ne prévoit aucune annulation de PV : incohérence documentaire mineure |
| 12 | Correction | clarification documentaire (Métier §2.4) ; à l'écriture de 009 : voir section 8 |

### 3.8 Séquences et high-water — **CONFORME**

| Élément | Constat |
|---|---|
| `numerotation_sequences` | **[SQL]** `tr_95` (le compteur ne diminue jamais, 001 l.271) + `tr_96` (suppression refusée, y compris par REPLACE, 004 l.494). **[CONSTATÉ]** C8 : REPLACE sur une séquence existante refusé. C7 : sur une séquence **inexistante** il réussit, sans conséquence (il crée) |
| `sequence_high_water` | **[SQL]** `machine/001` l.186-197. **Aucun trigger** (D-30 : garde de service). Une modification ou une suppression directe est possible en SQL ; INV-25 repose sur le service |

---

## 4. Anomalies techniques constatées

Toutes sont **[CONSTATÉ]** sur 001→004 (annexe A) et corroborées par la lecture des migrations. Aucune n'est corrigée dans cet audit.

### 4.1 E-1, E-2, E-3 — Suppression physique possible

| Objet | Constat | Garde existante | Source |
|---|---|---|---|
| Client | suppression acceptée sans devis ni BC, même archivé | FK `RESTRICT` des documents seulement | A1, A4 ; 001 ; `test_003` l.705-706 |
| Fournisseur | suppression acceptée, même archivé ; aucune FK entrante aujourd'hui | aucune | A2, A2b ; 002 l.28-31 ; `test_002` l.160-165, l.183-189 |
| Devis | suppression acceptée dans `en_attente`, `accepte`, `refuse`, `annule` ; lignes et garanties supprimées en cascade | FK `RESTRICT` de `bons_commande.devis_id` seulement | A3 ; 003 l.17-19 ; `test_003` l.721-731 ; `test_004` l.1798 |

**[DÉD]** la FK `RESTRICT` protège contre la suppression d'un parent **référencé**, pas contre la suppression d'un objet numéroté qui n'a pas (encore) d'enfant : elle ne peut pas porter la règle D1 seule.

### 4.2 E-5 — Codes `CLI` / `FOU` modifiables

**[CONSTATÉ]** U1, U2 : la modification du `code` d'un client ou d'un fournisseur est acceptée. **[DOC]** aucune règle d'immutabilité du code client/fournisseur (INV-23 vise `numero` ; TR-01 liste devis, BC, factures, PV, dépenses). **[CONSTATÉ]** U3 : le code libéré peut être réattribué. Contraire à D2 (code immuable après attribution). Les modalités techniques de l'immutabilité restent à définir (D2).

### 4.3 E-6 — Réutilisation d'un numéro non empêchée par le SQL

**[CONSTATÉ]** B1, B2 : après suppression, la réinsertion d'un numéro ou code déjà consommé réussit ; B3 : tant que la ligne existe, l'unicité refuse une insertion simple. **[DÉD]** :
1. La conservation apporte une protection que le compteur ne donne pas : l'**unicité du numéro persiste** avec la ligne.
2. Cette protection est **contournée par REPLACE** (E-4, variante 3) tant qu'aucune garde de suppression n'existe.
3. Un numéro « trou » (consommé, jamais associé à une ligne, par exemple après un crash) reste insérable à la main ; le SQL ne peut pas l'interdire et **CK-02 ne le détecte pas** (CK-02 compare séquences et numéros présents, Modèle §14). Cette limite relève du service, qui n'attribue que par la séquence.

### 4.4 E-4 — `INSERT OR REPLACE` : `recursive_triggers=ON` ne suffit pas (D4)

**Principe** : lorsque l'insertion entre en conflit avec une ligne existante (sur la clé primaire **ou sur une colonne unique**), `REPLACE` **supprime** d'abord cette ligne, sans passer par un `UPDATE`. [DOC] Modèle §1 l.47-50.

**Ce que `recursive_triggers=ON` apporte, et ses limites [DÉD]**

| Aspect | Constat |
|---|---|
| Apport | le suppression implicite déclenche les triggers de suppression **qui existent** ; c'est ce qui rend effectifs TR-19 (BC), TR-96 (séquences), TR-90, TR-11 (lignes de devis), TR-13 (lignes de BC) |
| Limite 1 | **là où aucun trigger de suppression n'existe, le réglage ne protège rien** : `clients`, `fournisseurs`, `devis` |
| Limite 2 | un REPLACE **ne déclenche pas les triggers `UPDATE`** (Modèle §1 l.50, vérifié) : les gardes d'immutabilité écrites en `UPDATE` (TR-01, TR-10, TR-12…) ne sont jamais atteintes |
| Limite 3 | l'interdiction de REPLACE est une **convention**, non imposée mécaniquement (INV-07, conventions §9) |
| Limite 4 | une FK `RESTRICT` bloque le remplacement d'un parent **référencé** (C2), jamais celui d'une ligne sans enfant ; les enfants en `CASCADE` sont supprimés sans bruit (R3) |

**Trois variantes constatées**

| Variante | Essai | Résultat |
|---|---|---|
| 1. Par identifiant, sur un devis `refuse` puis `annule`, sans BC | remplacement d'un devis existant par un autre ayant un numéro différent | **accepté** : le devis redevient `en_attente`, son numéro change (C4) ; les modifications équivalentes par `UPDATE` sont **refusées** (C5, C6) |
| 2. Par identifiant, sur un client / fournisseur sans enfant | remplacement avec un code différent | **accepté** (C1, C3) ; refusé si un devis référence le client (C2) |
| 3. **Par conflit sur le numéro (nouveau)**, sans fournir d'identifiant | insertion avec un numéro déjà présent | **accepté** : l'ancienne ligne est supprimée, une ligne neuve (nouvel identifiant) la remplace ; pour un devis annulé, **ses lignes disparaissent** et le nouvel objet est `en_attente` (R1, R2, R3) |

**Écart avec la documentation** : D-39 et INV-07 présentent `recursive_triggers=ON` comme neutralisant le contournement ; c'est exact **uniquement là où un trigger de suppression existe**. Les tests de renforcement de 003 couvrent les seules lignes et garanties de devis (**[TEST]** `test_003` l.1030-1067).
**Indépendance de la règle** : le contournement réécrit un objet que le modèle déclare immuable (INV-23, INV-31). D4 le classe à corriger **dans tous les cas**.

### 4.5 E-7 — Client `a_rattacher` (sujet séparé)

**[DOC]** le rattachement « réaffecte `client_id` » des devis, BC et factures vers le client cible (Modèle §4.4 l.272 ; Métier l.104). **Aucun document ne dit ce que devient le client `a_rattacher` d'origine.** Il porte un code `CLI-xxxx` attribué (les codes des clients importés suivent le format V6, CDC §18 l.573). D2 renvoie ce sujet à un **traitement séparé** ; cet audit ne le définit pas.

### 4.6 E-8 — `situation_numero` (D6 ouverte)

**[DOC]** ordinal par BC (D-07), unique parmi les situations **actives** (Modèle l.382). **[DÉD]** après annulation de la dernière situation, la suivante peut reprendre le même ordinal, alors que le numéro de **facture** `FAC-` est neuf. Si ce numéro est visible sur un document client, il pourrait relever de la règle générale ; si c'est un ordinal interne, non (D6). **Non tranché ici.**

### 4.7 E-9 — Restauration (cas technique distinct, D1)

**[DOC]** Modèle §11.2, §11.4 : la restauration remplace la base ; le compteur est relevé par le high-water ; « un avertissement liste les numéros consommés que la sauvegarde ne contient plus ». **[DÉD]** des objets numérotés disparaissent physiquement et leurs numéros deviennent des trous. D1 classe la restauration comme **cas technique distinct** : elle n'est pas une suppression métier. Les documents ne le disent pas encore (section 6, correction documentaire).

---

## 5. Impacts sur les tranches 001–004

Aucune migration n'est modifiée. Éléments touchés :

| Élément | Nature | Détail |
|---|---|---|
| INV-06 | formulation conditionnelle | plus étroite que D1/D2/D3 |
| Modèle §4.4 l.273-275, §4.6 l.299, D-33 ; Métier l.79, l.103, l.182, l.501 ; Audit fonctionnel l.103, l.235 | formulations conditionnelles ou contraires | à clarifier |
| Modèle §1 l.47-50, D-39, INV-07, conventions §9 | présentent `recursive_triggers=ON` comme suffisant | à nuancer (4.4) |
| `002_fournisseurs.sql` l.28-34, `003_devis.sql` l.17-19 | commentaires d'en-tête décrivant l'état à la date de la tranche | migrations historiques : **ne pas modifier** |
| `test_002` l.160-165, l.183-189 ; `test_003` l.297, l.385, l.705-706, l.721-731 ; `test_004` l.1798 | tests qui affirment la suppression possible | **restent valides** pour leur tranche : chacun n'applique que sa propre chaîne (`test_002` l.32-40 : 001-002 ; `test_003` l.56-64 : 001-003 ; `test_004` l.122-130 : 001-004) ; **non modifiés** |

**[DÉD]** une garde ajoutée par une migration **postérieure** ne change le résultat d'aucun de ces tests. Elle les rend en revanche descriptifs d'un état intermédiaire, ce que leurs en-têtes devraient pouvoir exprimer (décision de forme, non traitée ici).

---

## 6. Corrections nécessaires (listées, non réalisées)

La **migration d'intégration n'est pas décidée** (D4). Chaque correction est décrite par sa nature et son impact.

| # | Nature | Cible | Correction | Impacts |
|---|---|---|---|---|
| C-1 | Documentaire | INV-06, Modèle §4.4 / §4.6 / D-33, Métier l.79 / l.103 / l.182 / l.501, Audit fonctionnel l.103 / l.235 | aligner sur D1/D2/D3 : conservation inconditionnelle, archivage distinct de la suppression, fin de la suppression du devis | numéros d'invariant et de décision à attribuer à l'intégration |
| C-2 | Documentaire | Modèle §1, D-39, INV-07, conventions §9 | déclarer `recursive_triggers=ON` **nécessaire mais non suffisant** ; décrire les trois variantes (4.4) ; indiquer qu'une table d'objet numéroté exige une garde de suppression pour être protégée | cohérence avec C-5 |
| C-3 | Documentaire | Modèle §11.4, §6 | consigner : rollback avant COMMIT ≠ suppression ; restauration = cas technique distinct (D1) | voir Q-1 et Q-3 (section 10.2) |
| C-4 | Documentaire | Modèle §4.12 l.419, INV-100, Métier (dépenses) | remplacer « sera déterminé lors de la conception de la tranche Dépenses » par la règle D5 ; vérifier que « ni statut de paiement » ne s'entend pas comme interdisant l'annulation | cadrage 005 |
| C-5 | **SQL** (à concevoir) | `clients`, `fournisseurs`, `devis` | garde de non-suppression pour chaque table (même famille que TR-19) | neutralise aussi E-4 sur ces tables ; vérification contre REPLACE des trois variantes |
| C-6 | **SQL** (à concevoir) | `clients.code`, `fournisseurs.code` | immutabilité du code après attribution (modalités techniques à définir, D2) | à vérifier aussi contre REPLACE (la garde d'immutabilité en UPDATE ne suffit pas, 4.4) |
| C-7 | **SQL** (à la conception) | `depenses` (005), `factures` (006), `pv` (009) | garde de non-suppression et protection contre REPLACE dès la création de la table | voir section 8 |
| C-8 | Applicative (service) | UI et services | aucune suppression émise sur un objet numérotable | remplacement des actions de suppression existantes ou prévues par l'archivage ou l'annulation selon l'objet |
| C-9 | Tests | tests de la future migration | suppression directe refusée ; trois variantes de REPLACE refusées ; code immuable ; campagne de mutation dédiée (conventions §7.1) ; **tests 001–004 inchangés** | dépend du véhicule retenu |
| C-10 | Documentaire | Modèle §15, registre INV, §17.1 | décisions, invariants, journal, ligne de migration ; modèle à la version suivante **avant** la migration (conventions §5) | procédure habituelle |

**Impacts selon le véhicule (D4 non tranché), sans préférence**

| Véhicule | Impacts constatés |
|---|---|
| Dans 005 | précédent : 004 ajoute `tr_96` sur une table de 001 « pour compléter tr_95 » ; la tranche 005 contient alors des gardes sur des tables de 001–003 ; sa campagne de mutation les couvre ; l'ordre officiel 001–010 est conservé |
| Migration corrective dédiée | un numéro de migration supplémentaire ; l'**ordre officiel 005–010 est à renuméroter** ou à compléter (conventions §4, §5, Modèle §17.1) |
| Autre organisation | non décrite par D4 |

---

## 7. Impacts sur Dépenses (D5)

### 7.1 Règles validées **[VALIDÉ]**

1. Une dépense n'est **jamais supprimée** après attribution de son numéro.
2. Elle dispose d'un **mécanisme métier d'annulation** pour les cas où elle ne doit plus être considérée comme active.
3. Une dépense annulée **reste conservée** avec son numéro, son historique, ses rattachements et ses données de traçabilité.
4. **Une nouvelle dépense peut être créée et rattachée à un BC déjà annulé** : règle métier volontaire. Exemple : devis accepté, BC créé, acompte facturé, matériel acheté, client rétracté avant encaissement, BC annulé ; l'achat reste une dépense réelle, qui reste rattachée au BC annulé, et d'autres dépenses peuvent y être ajoutées ensuite.
5. Le BC annulé reste un **conteneur historique et économique conservé**.

### 7.2 Garanties déjà présentes pour le BC annulé **[SQL]**

| # | Constat | Source |
|---|---|---|
| 1 | aucun BC n'est supprimable (garde de suppression, TR-19) | 004 l.411 ; INV-174 |
| 2 | les tables qui référencent un BC le font en `RESTRICT` (aucun CASCADE entrant) ; la future FK `depenses.bc_id` suivrait la règle INV-05 | INV-05 ; 004 l.15-18 |
| 3 | l'annulation d'un BC est une modification du seul BC ; **aucun trigger de 001–004 ne touche une dépense** | 004 (triggers TR-12, TR-13, TR-14, TR-17, TR-18) |
| 4 | une modification commerciale d'un BC annulé est refusée (TR-12), sans effet sur les dépenses (qui ne sont pas des données commerciales du BC) | INV-173 |

**[DÉD]** les dépenses d'un BC annulé restent donc rattachées sans règle SQL supplémentaire ; la règle 4 de D5 (création sur BC annulé) est **compatible** avec le SQL des tranches validées, qui n'interdit rien de tel.

### 7.3 Conséquences pour la tranche 005

| # | Conséquence | Statut |
|---|---|---|
| 1 | `depenses` doit refuser toute suppression, **y compris** par REPLACE (C-7) | découle de D1, D4, D5 |
| 2 | la proposition « suppression physique permise » (cadrage 005, Q3, A-3) est **abandonnée** ; A-4 (REPLACE contourne TR-01) est traité par la garde de suppression | découle de D5 |
| 3 | la question « dépense sur BC annulé » (cadrage 005, Q2) est **tranchée dans son principe** : création et rattachement autorisés | D5 |
| 4 | le **modèle exact** de l'annulation (colonnes, effets sur les analyses de marge, modifiabilité d'une dépense annulée, réversibilité éventuelle) est **à décider au cadrage 005** | ouvert |
| 5 | la règle des 30 jours (INV-103) s'applique-t-elle, et avec quelle confirmation, à un BC **annulé** ? D5 autorise la création mais ne précise ni confirmation ni délai pour ce cas ; un BC annulé a en principe `date_100_facture` nulle | à préciser au cadrage 005 |
| 6 | `date_depense` : l'année (yy) du numéro est immuable (INV-23) ; corriger une année erronée passe par l'annulation puis une nouvelle saisie | découle de D5 + INV-23 |
| 7 | la FK `depenses.fournisseur_id` en `RESTRICT` annoncée par 002 reste obligatoire (INV-05) mais n'est plus la seule garde du fournisseur | découle de D2 |

### 7.4 Éléments du cadrage 005 déjà remis, désormais caducs (**non modifiés**, à reprendre)

Le fichier `CADRAGE__005_depenses.md` n'est **pas** modifié par cet audit. Passages concernés :
- §0 « 1 trigger », « aucun statut » : à réviser (garde de suppression, mécanisme d'annulation) ;
- §2 esquisse de la table : suppose la suppression permise ;
- §3.2 matrice BC : la ligne « annulé » ;
- §4.3 INV-180 (contenu), **INV-181** (« une dépense peut être supprimée ») ;
- §6 A-2, A-3, A-4 ;
- §8 groupes de tests « Suppression » et « REPLACE » ;
- §9 Q2 (option B proposée), Q3 (option a recommandée).

---

## 8. Conséquences transversales pour les futures entités numérotées

Cette section déduit de D1 ce qui s'impose à toute entité numérotée, **sans définir son cycle de vie** (à définir dans sa tranche).

### 8.1 Obligations qui découlent de D1 **[DÉD]**

Pour toute table portant un numéro définitif attribué par BATORYA :

| # | Obligation | Origine |
|---|---|---|
| 1 | aucune suppression physique possible après validation de l'opération, **y compris** par suppression directe et par `INSERT OR REPLACE` sous ses trois variantes (4.4) | D1, D4 |
| 2 | `recursive_triggers=ON` est **nécessaire** mais ne remplace pas une garde de suppression sur la table | D4 |
| 3 | une FK `RESTRICT` entrante ne suffit pas à la place d'une garde sur la table elle-même | 4.1 |
| 4 | le numéro est immuable après attribution (comme TR-01 pour devis et BC) ; l'immutabilité en `UPDATE` ne protège pas contre REPLACE | D2, 4.4 |
| 5 | l'attribution passe par la séquence (compteur croissant, ligne non supprimable) et le high-water | INV-22, INV-25 |
| 6 | l'objet « annulé » conserve sa ligne et son numéro ; le mécanisme d'annulation est propre à l'objet | D1 |
| 7 | les enfants d'un objet numéroté ne sont pas supprimables par CASCADE depuis un objet numéroté ; seuls les CASCADE existants (lignes, garanties de lignes) avant gel restent à qualifier | 3.3 ligne 9 |
| 8 | le numéro historique importé (devis, factures, PV `origine='import'`) : traitement à préciser (question Q-3) | D1, INV-131 |
| 9 | la restauration reste un cas technique distinct ; le high-water protège les numéros | D1, §11.4 |
| 10 | tests de la tranche : suppression directe refusée, REPLACE refusé (trois variantes), numéro non réutilisable, campagne de mutation (conventions §7.1) | D4 |

### 8.2 Par entité

| Entité | Tranche | Ce qui est **déjà documenté** | Ce que D1 ajoute / exige | Cycle de vie |
|---|---|---|---|---|
| **Dépense** | 005 | numéro `DEP`, TR-01, pas de suppression de BC | garde de suppression ; annulation (D5) ; dépense sur BC annulé autorisée | **à définir au cadrage 005** |
| **Facture (situation, solde)** | 006 | jamais supprimée (INV-53), annulation `cancelled_at`, TR-21, TR-24 | vérifier garde de suppression et REPLACE ; D6 pour `situation_numero` | défini par ses documents ; non repris ici |
| **Acompte** | 006 | idem ; un seul acompte actif (index partiel) | idem ; un acompte annulé conserve son numéro `ACP` | idem |
| **Avoir** | 006 | idem ; origine obligatoire (INV-76) | idem ; numéro `AVO` jamais réutilisé | idem |
| **PV initial** | 009 | immuable, aucun UPDATE ni DELETE (TR-40) | vérifier garde de suppression et REPLACE | pas d'annulation de PV dans le modèle |
| **Levée de réserves** | 009 | PV autonome, `suffixe = max + 1` | la non-suppression est la **seule** garde contre la réutilisation du suffixe (aucune séquence) | idem |
| **Réserves** | 009 | champ texte du PV | **non applicable** (pas de numérotation propre) | — |
| **Règlement** | 007 | jamais supprimé, annulation unique (TR-32) | aucune règle de numérotation (pas de numéro) | défini par ses documents |
| **Garantie** | 008 | aucun UPDATE ni DELETE (TR-50) | aucune règle de numérotation (pas de numéro) | défini par ses documents |
| **Planification** | 010 | événements sans numéro ; `bc_notes` supprimables (INV-102) | **hors règle** (aucun numéro définitif) | défini par ses documents |
| **Import** | — | `import-v6.json` : séquences initialisées, numéros historiques conservés | lignes importées conservées ; clients `a_rattacher` : E-7 | — |
| **Toute entité future** | — | — | 8.1 s'applique dès qu'un numéro définitif est attribué | à définir |

---

## 9. Cohérence de la numérotation

| Point | Constat |
|---|---|
| **`numerotation_sequences`** | une ligne par `(type_objet, annee)`, compteur croissant (TR-95), ligne non supprimable (TR-96), mise à jour par insertion avec résolution de conflit (seule forme autorisée). **Conforme à D1** [SQL] [TEST] `test_004` l.2075-2148 |
| **`sequence_high_water`** (`machine.db`) | écrit **avant** le COMMIT (Modèle §5 l.528) ; ne diminue jamais ; garde **de service uniquement** (D-30). D1 (« numéro définitivement consommé ») repose sur cette garde pour la restauration et les crashs. Non testable en SQL |
| **Numéros attribués** | ligne persistante (BC) ; ligne supprimable pour client, fournisseur, devis (E-1 à E-3) ; code modifiable pour client et fournisseur (E-5) |
| **Annulation** | l'objet annulé conserve sa ligne et son numéro ; la séquence n'est jamais rendue ; **[TEST]** `test_004` l.790-801 (BC) ; [DOC] Modèle §6 l.557. Création après annulation : numéro suivant du compteur |
| **Sauvegarde** | copie de la base métier ; `machine.db` (donc le high-water) n'est **jamais** sauvegardée ni restaurée (Modèle §5, CDC l.1173) : c'est ce qui protège les numéros à la restauration |
| **Restauration** | `dernier_numero := max(restauré, max_attribue)` ; avertissement listant les numéros consommés absents (§11.4). Cas technique distinct (D1, E-9) |
| **Démarrage après crash** | `max_attribue > dernier_numero` → `max_attribue` conservé, trou journalisé (§11.4 l.771) |
| **Rollback** | D1 : l'opération annulée avant COMMIT n'est pas une suppression d'objet numéroté. Ce que devient le numéro attribué dans une transaction annulée (réattribution ou trou) n'est pas écrit dans les documents (question Q-1) |
| **Import** | `dernier_numero` fourni par fichier, validé ≥ plus grand numéro V6 du fichier ; `max_attribue := dernier_numero` ; numéros historiques hors format V6 n'alimentent pas les séquences (§10.6, INV-135) |
| **`INSERT OR REPLACE`** | **Protégé** sur : `numerotation_sequences` (TR-96), `bons_commande` (TR-19), `import_anomalies` (TR-90), lignes et garanties de devis (TR-11) et de BC (TR-13). **Non protégé** sur : `clients`, `fournisseurs`, `devis` (E-4) |
| **Suppression implicite** | `ON DELETE CASCADE` : `prestation_garanties` → prestation, `devis_lignes` → devis, `devis_ligne_garanties` → ligne, `bc_ligne_garanties` → ligne. Aucun `SET NULL` dans 001–004 ni `machine/001`. Seul CASCADE atteignant les données d'un objet numérotable : `devis_lignes.devis_id` |

---

## 10. Décisions, contradictions et points ouverts

### 10.1 Décisions validées intégrées

D1, D2, D3, D4 (principe), D5 : section 1.2.

### 10.2 Questions ouvertes (aucune recommandation ici)

| # | Sujet | Origine | À traiter |
|---|---|---|---|
| Q-1 | **Numéro attribué dans une transaction annulée avant COMMIT** : D1 précise que ce n'est pas une suppression ; reste à écrire si le numéro est réattribuable ou devient un trou, au regard de l'écriture du high-water avant COMMIT | D1, Modèle §5 l.528, §11.4 | documentation technique |
| Q-2 | **Véhicule des corrections SQL** (005, migration dédiée, autre) | D4 | décision ultérieure |
| Q-3 | **Numéros historiques importés** (devis, factures, PV `origine='import'`) : D1 les couvre-t-il explicitement ? | D1, INV-131 | à préciser |
| Q-4 | **Modalités techniques de l'immutabilité des codes** client et fournisseur | D2 | définition technique |
| Q-5 | **Cycle de vie du client `a_rattacher`** après rattachement | D2, E-7 | sujet séparé |
| Q-6 | **Mécanisme d'annulation des devis** (détail) | D3 | cadrage ultérieur |
| Q-7 | **Mécanisme d'annulation des dépenses** (modèle exact, effets, règle des 30 jours sur BC annulé) | D5, 7.3 | cadrage 005 |
| Q-8 | **Numéro de situation** | D6 | cadrage Facturation |

### 10.3 Contradictions restantes entre les documents / le code et les décisions validées

| # | Contradiction | Sources | Nature |
|---|---|---|---|
| X-1 | INV-06 conditionnel (« utilisés », « avec BC ») vs D1/D2 inconditionnels | invariants l.25 | documentaire |
| X-2 | « Un client / fournisseur ayant un historique » vs D2 | Modèle l.273, l.275 ; Métier l.103, l.501 ; Audit l.103, l.235 | documentaire |
| X-3 | « Un devis sans BC peut être supprimé » (D-33) vs D3 | Modèle l.299 ; Métier l.182 | documentaire |
| X-4 | Le SQL de 001–003 autorise suppression et modification de code vs D1/D2/D3 | 001, 002, 003 | SQL |
| X-5 | `recursive_triggers=ON` présenté comme suffisant vs D4 | Modèle §1 ; D-39 ; INV-07 ; conventions §9 | documentaire |
| X-6 | Tests qui affirment la suppression (valides pour leur tranche) | `test_002`, `test_003`, `test_004` (5.) | tests historiques |
| X-7 | Modèle §4.12 : « le rattachement d'une dépense à un BC annulé sera déterminé lors de la conception de la tranche Dépenses » vs D5 (déjà déterminé) | Modèle l.419 | documentaire |
| X-8 | Cadrage 005 remis : propositions Q2 (B), Q3 (a), « aucun statut », « 1 trigger » vs D5 | `CADRAGE__005_depenses.md` (7.4) | document de travail |
| X-9 | Métier §2.4 range le PV parmi les objets « annulés » alors que le modèle n'a pas d'annulation de PV | Métier l.79 ; Modèle §4.11 | documentaire mineure |
| X-10 | « Ni statut de paiement » (dépenses) vs mécanisme d'annulation de D5 : à ne pas lire comme interdisant l'annulation | INV-100 ; Modèle §4.12 ; CDC §28 ; cadrage 005 | formulation à vérifier |

---

## Annexe A — Protocole de vérification (rejouable, décrit sans SQL)

Base : mémoire, migrations `metier/001` à `004` appliquées dans l'ordre, clés étrangères activées, `recursive_triggers` activé. Script de travail conservé hors dépôt. Rejoué en intégralité pour la version 2.

1. **A — Suppressions directes** : suppression d'un client sans devis (A1) et archivé (A4) ; d'un fournisseur actif (A2) et archivé (A2b) ; d'un devis portant une ligne, dans chacun des quatre statuts (A3). Tous acceptés ; les lignes du devis disparaissent.
2. **B — Réutilisation** : séquence `DEV` de l'année 26 à 1, suppression du devis, insertion d'un nouveau devis portant le même numéro (B1) et d'un client portant le même code (B2) : acceptées. Insertion simple d'un numéro encore présent (B3) : refusée par l'unicité.
3. **C — Remplacement par identifiant** : remplacement d'un client (C1), d'un fournisseur (C3), d'un devis `en_attente`, `refuse`, `annule` (C4) avec un autre numéro : acceptés ; client référencé par un devis (C2) : refusé par la clé étrangère. Les modifications équivalentes par mise à jour d'un devis `refuse`/`annule` (C5, C6) : refusées. Remplacement sur une séquence inexistante (C7) : accepté ; existante (C8) : refusé par TR-96.
4. **R — Remplacement par conflit sur le numéro (nouveau)** : insertion avec remplacement d'un client (R1), d'un fournisseur (R2) et d'un devis annulé (R3) portant un numéro déjà présent, sans identifiant : acceptés ; la ligne d'origine est remplacée par une ligne neuve (identifiant différent) ; les lignes du devis annulé sont supprimées.
5. **D, E, T, U** : triggers de suppression présents (`bons_commande` et `numerotation_sequences` seulement) ; actions de clés étrangères ; passage `en_attente → annule` d'un devis (T1) et `actif ↔ archive` d'un client (T3, T4) acceptés ; modification du code d'un client (U1) et d'un fournisseur (U2) acceptée, réinsertion du code libéré (U3) acceptée ; modification du numéro d'un devis (U4) et de son année de création (U5) refusées.
6. **Suites de tests existantes** : `test_001` (28), `test_002` (18), `test_003` (68), `test_004` (150) : toutes passent, sans modification.
7. **Indépendance des tests** : chaque fichier de test n'applique que sa propre chaîne de migrations (références en section 5).

## Annexe B — Index des sources principales

| Sujet | Sources |
|---|---|
| Numérotation, jamais réutilisé | Modèle §6 l.539-561, §10.6, §11.4 l.768-772 ; INV-20 à INV-25, INV-135 ; Métier l.60-70, l.812 ; CDC §19 l.590, §42 l.1156-1175 ; Audit fonctionnel l.510, l.559 |
| Non-suppression | INV-06, INV-53, INV-70, INV-78, INV-95, INV-105, INV-110, INV-174 ; Modèle §4.4, §4.6 l.299, §4.7 l.331, §8 l.601-635 ; Métier §2.4 l.79 ; CDC l.532, l.645 |
| REPLACE et `recursive_triggers` | INV-07 ; D-39 ; Modèle §1 l.47-50 ; conventions §7, §9 ; `004` l.32-35 ; tests `test_004` l.2075-2260 ; `test_003` l.1030-1067 |
| Séquences et high-water | `001_initial.sql` l.77-96, l.271 ; `004_bons_commande.sql` l.494 ; `machine/001_initial.sql` l.186-197 ; INV-22, INV-25, D-27, D-30 |
| Suppression dans le SQL | `001` l.246 (TR-90) ; `002` l.28-34 ; `003` l.17-19, l.376-409 ; `004` l.15, l.411, l.453-498 |
| Dépenses | Modèle §4.12 l.418-419, §6, §8 ; INV-100, INV-103 ; CDC §28, §29 ; cadrage 005 |
