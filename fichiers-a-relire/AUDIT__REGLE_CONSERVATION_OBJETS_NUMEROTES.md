# BATORYA Essentiel V6 — Audit transversal de la règle de conservation des objets numérotés

**Statut** : rapport d'audit, **sans aucune modification** du dépôt hors ce fichier. La règle auditée n'est **pas** une règle officielle : elle le deviendra seulement après votre validation (section 9).
**Base** : dépôt `mymypav-max/BATORYA-Essentiel`, branche `main`, commit `86d7806` (migrations 001–004 intégrées). Les numéros de ligne cités se rapportent à ce commit.
**Consulté** (lecture intégrale ou recherche ciblée) : `docs/README.md`, audit fonctionnel, `invariants.md`, modèle SQLite V3.12, modèle métier, errata, CDC, conventions, migrations `metier/001–004` et `machine/001`, tests `test_001` à `test_004` (recherche ciblée des suppressions, REPLACE et séquences), cadrage 005.
**Vérifié par exécution** : les comportements SQL annoncés « constatés » ont été **rejoués sur une base construite avec 001→004** (`foreign_keys=ON`, `recursive_triggers=ON`, comme les connexions applicatives, D-39). Protocole en annexe A. Aucune migration, aucun test ni aucun fichier officiel n'a été touché.

**Étiquettes de source**

| Étiquette | Sens |
|---|---|
| **[DOC]** | règle déjà écrite dans un document (fichier, section ou ligne) |
| **[SQL]** | comportement réellement présent dans une migration (fichier, trigger) |
| **[CONSTATÉ]** | comportement vérifié par exécution sur 001→004 (annexe A) |
| **[TEST]** | comportement affirmé par un test existant |
| **[DÉD]** | déduction technique de ma part |
| **[PROP]** | proposition, non officielle |
| **[ÉCART]** | écart à corriger (documentaire, SQL ou applicatif) |

---

## 0. Résumé

La règle proposée est **déjà largement présente** dans la conception pour le BC, les factures, les règlements, les PV, les garanties et l'historique. Elle est **violée par trois objets déjà implémentés et validés** (client, fournisseur, devis), et un défaut technique **indépendant de la règle** est apparu pendant la vérification.

| # | Constat | Gravité |
|---|---|---|
| **E-1** | `clients` : supprimable dès qu'aucun devis/BC ne le référence, **même archivé** (aucun trigger DELETE) | Écart à la règle |
| **E-2** | `fournisseurs` : idem ; un test valide explicitement la suppression d'un fournisseur (le compteur continue, la ligne disparaît) | Écart à la règle |
| **E-3** | `devis` : supprimable **dans les quatre statuts** (en_attente, accepté, refusé, annulé) tant qu'aucun BC n'existe ; règle documentée (D-33) et testée | Écart à la règle (règle documentée contraire) |
| **E-4** | **`INSERT OR REPLACE` contourne l'immutabilité** de `devis` (un devis refusé ou annulé a été remplacé avec un autre numéro et un autre statut) et réécrit `clients.code` / `fournisseurs.code` | **Défaut réel**, existe avec ou sans la nouvelle règle |
| **E-5** | `clients.code` et `fournisseurs.code` sont **modifiables par UPDATE** (aucun TR-01) : un numéro peut être libéré puis ré-attribué | Écart à la règle |
| **E-6** | Un numéro supprimé ou libéré n'est protégé que par le compteur (service) : le SQL accepte la réinsertion d'un numéro déjà consommé | Limite à connaître |
| **E-7** | Sort du client `a_rattacher` après rattachement : **aucun document** | Silence à trancher |
| **E-8** | `situation_numero` (ordinal par BC) peut être réutilisé après annulation d'une situation (index partiel) | Ambigu (tranche 006) |
| **E-9** | Une restauration supprime physiquement les objets postérieurs à la sauvegarde | Limite de portée à écrire |

Objets déjà conformes : **BC** (TR-19, FK `RESTRICT`), **séquences** (TR-95 + TR-96), `import_anomalies`. Objets conformes **par conception documentée mais pas encore implémentés** : facture/acompte/avoir (TR-21), PV (TR-40). **Dépense** : non encore écrite, donc à concevoir conforme ; la règle **remet en cause la proposition Q3 du cadrage 005** (suppression physique), comme vous l'avez anticipé.

Aucune correction ne demande de **réécrire** 001–004. Elles prennent la forme d'une **clarification documentaire** (immédiate) et de **triggers de non-suppression ajoutés par une migration ultérieure** (précédent : TR-96 ajouté par 004 pour compléter TR-95 de 001). Les tests 001–004 restent valides tels quels : chacun n'applique que sa propre chaîne de migrations (annexe A, point 5).

---

## 1. Règle auditée

### 1.1 Formulation (telle que proposée)

> **R-A (conservation)** — Tout objet métier auquel BATORYA attribue un numéro définitif ne peut jamais être physiquement supprimé. Il peut être modifié quand son cycle de vie l'autorise, ou annulé quand le métier le prévoit ; son enregistrement et son numéro sont conservés.
> **R-B (consommation)** — Tout numéro attribué est définitivement consommé et ne peut jamais être réutilisé, y compris lorsque l'objet est annulé.
> **R-C (trous)** — Les trous dans les séquences sont normaux et ne sont jamais comblés.

### 1.2 Ce qui existe déjà dans les documents

| Énoncé existant | Source | Rapport avec la règle |
|---|---|---|
| « Un numéro déjà attribué n'est jamais réutilisé ; un trou de numérotation est acceptable » | **[DOC]** Métier l.69 ; CDC §19 l.590 ; Audit l.510, l.559 ; Modèle §6 l.557 (« même après annulation ») ; INV-22, INV-25, INV-135 ; Métier l.812 (principe 17 : « même après annulation, restauration ou incident ») | **R-B et R-C déjà validées** |
| « Aucune suppression physique des entités historiques (clients/fournisseurs/prestations **utilisés**, devis **avec BC**, tout BC, factures, règlements, PV, garanties, historique) : archivage, annulation, avoir » | **[DOC]** INV-06 (invariants l.25) | R-A **conditionnée** (« utilisés », « avec BC ») |
| « Un client ayant un historique n'est jamais supprimé ; il est archivé » | **[DOC]** Métier l.103 ; Modèle §4.4 l.273 ; Audit l.103 | R-A conditionnée à « un historique » |
| « Un fournisseur ayant un historique est archivé, jamais supprimé » | **[DOC]** Modèle §4.4 l.275 ; Métier l.501 ; Audit l.235 | idem |
| « Un devis sans BC peut être supprimé physiquement ; ses lignes et garanties sont supprimées en CASCADE » | **[DOC]** Modèle §4.6 l.299 ; Métier l.182 ; D-33 ; en-tête de 003 l.17-19 | **Contraire** à R-A |
| « Aucun BC n'est jamais supprimé physiquement » (INV-174) | **[DOC]** INV-174 ; Modèle §4.7 l.331 ; D-35 | R-A appliquée sans condition |
| « Un document émis, un règlement, une garantie, un PV ou un événement d'historique n'est jamais supprimé pour corriger une erreur : il est annulé (date et motif) ou corrigé par un document opposé (avoir) » | **[DOC]** Métier §2.4 l.79 | R-A pour les objets émis ; **ne cite ni client, ni fournisseur, ni devis, ni dépense** |
| Aucune règle de suppression ou de conservation pour la **dépense** | **[DOC]** (silence) | à définir |

### 1.3 Périmètre proposé **[PROP]**

« Numéro définitif » = identifiant métier **attribué par BATORYA** à partir de `numerotation_sequences` (types `CLI`, `FOU`, `DEV`, `BCD`, `ACP`, `FAC`, `AVO`, `PVR`, `DEP`) ou, pour la levée de réserves, un suffixe calculé (`PVR-nnnnn-yy-nn`). Ne sont **pas** concernés : références de catalogue saisies, codes de listes, ordinaux de lignes, compteurs de versions de documents (détail en 2.2).

### 1.4 Points de formulation à trancher avant de l'inscrire (voir section 9)

1. **Annulé ou archivé ?** Client et fournisseur n'ont pas de statut « annulé » mais `archive` : la règle doit dire « annulé **ou archivé** selon l'objet ».
2. **Numéros historiques importés** (devis, factures, PV `origine='import'`, numéro déjà remis au client, INV-131) : ils ne viennent pas des séquences. Dans le périmètre ? **[PROP]** oui pour R-A (la ligne persiste), non pour R-C (sans objet).
3. **Définition de « attribué »** : le service écrit le high-water **avant** le COMMIT (Modèle §5 l.528). Si la transaction est annulée (rollback) sans crash, `dernier_numero` revient en arrière alors que `max_attribue` a monté. Les documents traitent le **crash** (§11.4 l.771), pas le rollback en session. **[PROP]** : un numéro est « attribué » à partir de la création validée (COMMIT) ; un rollback ne consomme pas le numéro, un crash en laisse un trou (déjà documenté).
4. **Restauration** : elle supprime physiquement les objets postérieurs à la sauvegarde. La règle porte sur les **opérations applicatives**, pas sur la restauration (E-9).

---

## 2. Inventaire des objets numérotés

### 2.1 Objets numérotés

| Objet | Format | Table / colonne | Séquence | Tranche | État |
|---|---|---|---|---|---|
| Client | `CLI-0001` | `clients.code` | `CLI`, année 0, plafond 9 999 | **001** | implémenté |
| Fournisseur | `FOU-0001` | `fournisseurs.code` | `FOU`, année 0, plafond 9 999 | **002** | implémenté |
| Devis | `DEV-00001-26` (historique libre si `origine='import'`) | `devis.numero` | `DEV` par année | **003** | implémenté |
| Bon de commande | `BCD-00001-26` | `bons_commande.numero` | `BCD` par année | **004** | implémenté |
| Dépense | `DEP-00001-26` | `depenses.numero` | `DEP` par année | 005 | à concevoir |
| Facture (situation, solde) | `FAC-00001-26` | `factures.numero` | `FAC` partagée | 006 | documenté |
| Acompte | `ACP-00001-26` | `factures.numero` (`type='acompte'`) | `ACP` | 006 | documenté |
| Avoir | `AVO-00001-26` | `factures.numero` (`type='avoir'`) | `AVO` | 006 | documenté |
| PV initial | `PVR-00001-26` | `pv.numero` | `PVR` par année | 009 | documenté |
| Levée de réserves | `PVR-00001-26-01` | `pv.numero` + `pv.suffixe` | **aucune** (suffixe = max + 1 par PV d'origine) | 009 | documenté |

Sources : Modèle §6 (l.539-553) **[DOC]** ; `numerotation_sequences` : `CHECK type_objet IN ('CLI','FOU','DEV','BCD','ACP','FAC','AVO','PVR','DEP')` **[SQL]** 001 l.80 ; ordre des tranches D-34 / votre brief.

### 2.2 Éléments à numéro **sans** numérotation définitive propre (aucune règle à créer)

| Élément | Pourquoi il n'est pas concerné |
|---|---|
| **Réserves** | `pv.reserves` est un **champ texte** (Modèle §4.11 l.413). Elles n'ont pas de numéro. Seule leur **levée** est un PV numéroté (ligne ci-dessus). **Non applicable** |
| Règlement, garantie, historique, document | pas de numéro métier (`id` seulement) ; déjà « jamais supprimés » (TR-32, TR-50, TR-60, TR-70) |
| Prestation (`reference`, ex. `ELE-008`) | référence de catalogue saisie ; une prestation est même **supprimée du catalogue V6** (CDC l.365) ; « jamais supprimée si utilisée » (INV-06) |
| Catégories (`code`) | listes modifiables de l'utilisateur |
| `documents.numero_version` | compteur de versions ; aucun DELETE (TR-70) |
| `devis_lignes.ordre`, `bc_lignes.ordre`, `facture_lignes.ordre` | ordinaux de présentation |
| **`factures.situation_numero`** | ordinal de situation par BC ; **cas limite**, voir E-8 |
| `id` (toutes tables) | `AUTOINCREMENT`, jamais réutilisé (INV-04) ; **[TEST]** `test_INV_04_*` dans 001–004 |

---

## 3. Résultat par objet

### 3.0 Vue d'ensemble

| Objet | Verdict | Motif en une ligne |
|---|---|---|
| Client | **Non conforme** | supprimable sans historique ; `code` modifiable ; REPLACE possible (E-1, E-4, E-5) |
| Fournisseur | **Non conforme** | idem, même archivé (E-2, E-4, E-5) |
| Devis | **Non conforme** | supprimable dans tous les statuts sans BC ; REPLACE contourne l'immutabilité (E-3, E-4) |
| Bon de commande | **Conforme** | TR-19 + FK `RESTRICT` + `recursive_triggers=ON` ; annulation sans suppression |
| Dépense | **Non applicable (à concevoir)** | table inexistante ; la règle impose la conception (section 5) |
| Facture / Acompte / Avoir | **Conforme (documenté)** | TR-21 (DELETE interdit), `cancelled_at` ; à vérifier à l'écriture de 006 ; E-8 |
| PV / Levée | **Conforme (documenté)** + point à vérifier | TR-40 ; le suffixe n'est protégé **que** par la non-suppression |
| Réserves | **Non applicable** | pas de numérotation propre |
| `numerotation_sequences` | **Conforme** | TR-95 (UPDATE) + TR-96 (DELETE, y compris REPLACE) |
| `sequence_high_water` | **Conforme, garde de service** | aucun trigger dans `machine.db` (D-30) |

### 3.1 Client — **NON CONFORME**

| # | Critère | Constat |
|---|---|---|
| 1-3 | Objet / format / migration | Client ; `CLI-0001` ; **001** (`clients`, séquence `CLI` année 0). `code` : `UNIQUE`, `CHECK GLOB 'CLI-[0-9][0-9][0-9][0-9]'` **[SQL]** 001 l.146 |
| 4 | Suppression actuelle | **[DOC]** « jamais supprimé s'il a un historique » (Modèle l.273, Métier l.103). **[SQL]** **aucun trigger DELETE** sur `clients` ; seules gardes : FK `RESTRICT` de `devis.client_id` (003 l.61) et `bons_commande.client_id` (004 l.78). **[CONSTATÉ]** A1, A4 : `DELETE` accepté pour un client sans devis ni BC, **y compris archivé** |
| 5 | Annulation | aucune ; l'équivalent est `statut='archive'`, réversible (T3, T4). `a_rattacher` réservé à l'import (001 l.163) |
| 6 | Modification | **[CONSTATÉ]** U1 : `UPDATE clients SET code=…` **accepté** ; **[SQL]** aucun trigger sur `clients` ; TR-01 ne couvre que devis, BC, factures, PV, dépenses (Modèle §8 l.601) |
| 7 | Protection contre la réutilisation | compteur `CLI` (TR-95, TR-96), high-water. **Pas** de protection structurelle une fois la ligne supprimée ou le `code` modifié |
| 8 | Suppression physique | oui, DELETE direct sans historique ; **REPLACE** (C1) |
| 9 | ON DELETE | `devis.client_id` et `bons_commande.client_id` en `RESTRICT` : **non problématique** |
| 10 | Conformité | non conforme à R-A (suppression) et à R-B (U1 puis U3 : `CLI-0001` ré-attribué) |
| 11 | Contradiction | avec INV-06 ? **non**, INV-06 est conditionnel (« utilisés ») ; contradiction avec la règle **cible** uniquement. Test qui consacre le comportement : **[TEST]** `test_003` l.705-706 |
| 12 | Correction | **[ÉCART]** trigger `BEFORE DELETE` sur `clients` ; immutabilité de `code` (comme TR-01) ; clarification INV-06 / Métier. Voir section 8 |

### 3.2 Fournisseur — **NON CONFORME**

| # | Critère | Constat |
|---|---|---|
| 1-3 | Objet / format / migration | Fournisseur ; `FOU-0001` ; **002** (`fournisseurs.code`, séquence `FOU` année 0) |
| 4 | Suppression actuelle | **[DOC]** « ayant un historique : archivé, jamais supprimé » (Modèle l.275, Métier l.501). **[SQL]** 002 l.28-31 : « Le contrôle de suppression d'un fournisseur ayant un historique est la FK RESTRICT de `depenses.fournisseur_id`, créée par la tranche des dépenses ». **Aucune FK entrante n'existe encore** : à ce jour **rien** n'empêche la suppression. **[CONSTATÉ]** A2, A2b : DELETE accepté, **même archivé** |
| 5 | Annulation | aucune ; `statut` ∈ `actif`, `archive` |
| 6 | Modification | **[CONSTATÉ]** U2 : `code` modifiable |
| 7 | Protection contre la réutilisation | compteur `FOU` ; **[TEST]** `test_002` l.183-189 `test_INV_22_numero_jamais_reutilise` **supprime** `FOU-0003` puis tout, et vérifie que le compteur continue (c'est exactement le comportement que la règle ne veut plus voir **possible**) |
| 8 | Suppression physique | oui, DELETE direct ; REPLACE (C3) |
| 9 | ON DELETE | aucun aujourd'hui ; futur `depenses.fournisseur_id` : `RESTRICT` (non problématique) |
| 10 | Conformité | non conforme à R-A |
| 11 | Contradiction | **[TEST]** `test_002` l.160-165 `test_INV_05_aucune_fk_et_suppression_sans_historique` affirme la suppression sans historique |
| 12 | Correction | **[ÉCART]** idem client : trigger `BEFORE DELETE`, immutabilité de `code`, documentation |

### 3.3 Devis — **NON CONFORME** (règle contraire documentée)

| # | Critère | Constat |
|---|---|---|
| 1-3 | Objet / format / migration | Devis ; `DEV-00001-26` (historique libre si `origine='import'`, INV-131) ; **003** |
| 4 | Suppression actuelle | **[DOC]** « Un devis sans BC peut être supprimé physiquement ; ses lignes et garanties sont supprimées en CASCADE » (Modèle §4.6 l.299 ; Métier l.182 ; D-33). **[SQL]** 003 l.17-19 : « aucun trigger sur DELETE devis » ; garde « devis avec BC » = FK `RESTRICT` `bons_commande.devis_id` (004 l.77). **[CONSTATÉ]** A3 : DELETE accepté pour **les quatre statuts**, lignes supprimées en cascade, y compris `refuse` et `annule` |
| 5 | Annulation | **[SQL]** `statut='annule'` + `cancelled_at` + `motif_annulation` ; **[CONSTATÉ]** T1 : `en_attente → annule` possible. Le devis annulé est immuable (TR-10) |
| 6 | Modification | `numero` et `date_creation` immuables (TR-01) **[CONSTATÉ]** U4, U5. Devis `refuse`/`annule` immuable (TR-10) ; `accepte` gelé (TR-10) |
| 7 | Protection contre la réutilisation | compteur `DEV` ; `UNIQUE(numero)` tant que la ligne existe (B3) ; **[CONSTATÉ]** B1 : après suppression, le SQL accepte la réinsertion de `DEV-00001-26` |
| 8 | Suppression physique | DELETE direct ; **REPLACE (C4)** : un devis `refuse` (puis `annule`) est remplacé en un seul ordre par un devis `en_attente` portant un autre numéro |
| 9 | ON DELETE | `devis_lignes.devis_id` en **CASCADE** : seul CASCADE qui atteint les données d'un objet numérotable. Il contourne en outre `tr_11_devis_lignes_delete` (la ligne parente est déjà supprimée quand le trigger s'exécute, cf. 004 l.462-463) : un devis `refuse`/`annule` perd ses lignes en cascade |
| 10 | Conformité | non conforme à R-A ; l'immutabilité TR-10 est **contournable** (E-4) |
| 11 | Contradiction | **règle documentée contraire** (D-33, Modèle l.299, Métier l.182). **[TEST]** `test_003` l.721-731 `test_INV_06_suppression_d_un_devis_sans_garde_dans_cette_tranche` : *« À reconsidérer avec la tranche BC »* ; `test_004` l.1789-1798 reconduit « sans BC : supprimé en CASCADE ». Le point **n'a jamais été rouvert** |
| 12 | Correction | **[ÉCART]** décision D-33 à remplacer ; trigger `BEFORE DELETE` sur `devis` ; documentation (Modèle l.299, Métier l.182, INV-06). Le CASCADE `devis_lignes` devient inutilisable pour un devis (reste utile pour la régénération des lignes, INV-38, qui supprime des lignes **sans** supprimer le devis) |

### 3.4 Bon de commande — **CONFORME**

| # | Critère | Constat |
|---|---|---|
| 1-3 | Objet / format / migration | BC ; `BCD-00001-26` ; **004** |
| 4 | Suppression actuelle | **[DOC]** INV-174, D-35, Modèle §4.7 l.331. **[SQL]** `tr_19_bons_commande_no_delete` (004 l.411), toujours refusé ; FK `RESTRICT` sur `bc_lignes.bc_id`. **[TEST]** `test_004` l.2256-2275, `test_INV_174_*` |
| 5 | Annulation | `statut='annule'`, terminal (INV-173, TR-12) |
| 6 | Modification | `numero`, `date_creation` immuables (TR-01, 004 l.287) ; BC annulé : `client_id` de rattachement et `updated_at` seulement |
| 7 | Protection contre la réutilisation | ligne conservée donc `UNIQUE(numero)` ; compteur `BCD` ; **[TEST]** `test_004` l.790-801 |
| 8 | Suppression physique | aucune ; REPLACE refusé avec `recursive_triggers=ON` (**[TEST]** `test_004` l.2177 `test_INV_174_REPLACE_ne_contourne_pas_tr19`) |
| 9 | ON DELETE | tous `RESTRICT` (sauf `bc_ligne_garanties` → ligne, CASCADE) |
| 10-12 | Conformité / contradiction / correction | **conforme, aucune correction**. C'est le **modèle de référence** de la règle |

### 3.5 Dépense — **NON APPLICABLE (à concevoir)**

Table inexistante. **[DOC]** `depenses` : `numero` `DEP-00001-26`, TR-01 (Modèle §4.12 l.418-419, §8 l.601). **[DOC]** aucune règle de suppression, de statut ni d'annulation. Conséquences détaillées en **section 5**.

### 3.6 Facture, acompte, avoir — **CONFORME (documenté, non implémenté)**

| # | Critère | Constat |
|---|---|---|
| 1-3 | Objet / format / migration | `FAC-`, `ACP-`, `AVO-00001-26` ; table `factures` ; tranche **006** (non écrite) |
| 4 | Suppression | **[DOC]** « jamais supprimée » (INV-53 ; INV-78 ; CDC l.532, l.645 ; TR-21 : DELETE interdit, Modèle §8 l.614) |
| 5 | Annulation | `cancelled_at` + `motif_annulation`, irréversible, une seule fois (INV-61, TR-24 ; Modèle §4.8) |
| 6 | Modification | immuable dès l'INSERT, hors `cancelled_*` et rattachement client (INV-53, TR-20) |
| 7 | Protection contre la réutilisation | ligne conservée + compteur ; chronologie TR-02 |
| 8-9 | Suppression physique / ON DELETE | `facture_lignes.facture_id` en `RESTRICT` (Modèle l.386) ; `origine_facture_id` FK |
| 10-12 | Conformité | conforme **par conception**. **À contrôler à l'écriture de 006** : trigger `BEFORE DELETE` effectivement présent, REPLACE refusé (D-39), `situation_numero` (E-8) |

### 3.7 PV et levée de réserves — **CONFORME (documenté)**, avec un point de vigilance

| # | Critère | Constat |
|---|---|---|
| 1-3 | Objet / format / migration | `PVR-00001-26` ; levée `PVR-00001-26-01` ; `pv` ; tranche **009** |
| 4 | Suppression | **[DOC]** « Immuable dès l'INSERT (aucun UPDATE, aucun DELETE) » (Modèle §4.11 l.414 ; INV-95 à 97 ; TR-40 ; CDC §23 l.665-690) |
| 5 | Annulation | **aucune** : `pv` n'a ni `cancelled_at` ni statut (Modèle §4.11). Conforme à « annulé *lorsque le métier le prévoit* » |
| 7 | Protection contre la réutilisation | PV initial : compteur `PVR`. **Levée : aucune séquence**, `suffixe = max + 1` calculé sur les lignes existantes (TR-41). **[DÉD]** la seule protection contre la réutilisation d'un suffixe est donc l'**interdiction de supprimer** une levée : si une levée pouvait être supprimée, le suffixe `-02` serait ré-attribué |
| 11 | Contradiction | **[DOC]** Métier §2.4 l.79 range le PV parmi ce qui est « annulé (date et motif) » alors que le modèle ne prévoit aucune annulation de PV : incohérence documentaire mineure |
| 12 | Correction | clarification documentaire (Métier §2.4) ; vérifier TR-40 et l'absence de contournement REPLACE à l'écriture de 009 |

### 3.8 Séquences et high-water — **CONFORME**

| Élément | Constat |
|---|---|
| `numerotation_sequences` | **[SQL]** `tr_95` (`dernier_numero` ne diminue jamais, 001 l.271) + `tr_96` (DELETE refusé, y compris REPLACE, 004 l.494). **[CONSTATÉ]** C8 : REPLACE sur une séquence existante refusé. C7 : sur une séquence **inexistante** le REPLACE réussit, ce qui est sans conséquence (il crée) |
| `sequence_high_water` | **[SQL]** `machine/001` l.186-197 : PK `(type_objet, annee)`, `max_attribue >= 0`. **Aucun trigger** (D-30 : garde de service). Un `UPDATE` ou un `DELETE` direct est possible en SQL ; INV-25 repose sur le service |

---

## 4. Impacts sur les tranches 001–004

Aucune migration n'est modifiée dans cet audit. Écarts constatés, par ordre d'importance :

### E-4 — REPLACE contourne l'immutabilité (défaut indépendant de la règle)

**Comportement actuel [CONSTATÉ]** (`recursive_triggers=ON`) :

| Essai | Résultat |
|---|---|
| C4 : `INSERT OR REPLACE INTO devis (id, numero, statut, …)` sur un devis `refuse`, puis `annule`, sans BC | **accepté** : le devis redevient `en_attente` et son numéro passe de `DEV-00001-26` à `DEV-00777-26` |
| C5, C6 (témoins) : `UPDATE devis SET numero=…` ou `statut='en_attente'` sur ces mêmes devis | **refusés** (TR-10, TR-01) |
| C1 : `INSERT OR REPLACE INTO clients (id, code, …)` sans devis | accepté : `CLI-0001` devient `CLI-0009` |
| C3 : idem `fournisseurs` | accepté |
| C2 : idem `clients` référencé par un devis | refusé (FK `RESTRICT`) |

**Pourquoi** : `devis`, `clients` et `fournisseurs` n'ont **aucun trigger `BEFORE DELETE`**. Or la protection contre REPLACE repose entièrement sur ces triggers (Modèle §1 l.47-49 ; conventions §9 l.212-218 ; INV-07).
**Écart avec la documentation** : D-39 et INV-07 présentent `recursive_triggers=ON` comme neutralisant le contournement ; c'est vrai **là où un `BEFORE DELETE` existe**. Les tests de renforcement de 003 ne couvrent que `devis_lignes` et `devis_ligne_garanties` (**[TEST]** `test_003` l.1030-1067, TR-11).
**Pourquoi c'est indépendant de la règle** : le contournement réécrit un objet que le modèle déclare immuable (INV-31, INV-23). Il faut le corriger **même si la règle R-A n'est pas adoptée**.
**Correction** : les triggers `BEFORE DELETE` de non-suppression de E-1 à E-3 le résolvent automatiquement (même mécanisme que TR-19). **Migration corrective ultérieure** (section 8).

### E-1, E-2, E-3 — Suppression physique possible

Détail en 3.1 à 3.3. **Règle cible** : aucun DELETE sur `clients`, `fournisseurs`, `devis`. **Correction** : trigger `BEFORE DELETE` par table (**migration ultérieure**, pas une réécriture) + clarification documentaire.
Effet de bord à connaître : sans suppression possible, l'unique sortie d'un client ou fournisseur créé par erreur est l'**archivage**, et celle d'un devis créé par erreur est l'**annulation** (possible dès `en_attente`, T1).

### E-5 — Codes `CLI` / `FOU` modifiables

**[CONSTATÉ]** U1-U3 : `UPDATE clients.code` libère un numéro, que le SQL laisse ré-attribuer. **[DOC]** aucune règle d'immutabilité du code client/fournisseur (INV-23 vise `numero` ; TR-01 liste devis, BC, factures, PV, dépenses). **[PROP]** étendre l'immutabilité aux deux codes (même schéma que TR-01).

### E-6 — Réutilisation non empêchée par le SQL

**[CONSTATÉ]** B1, B2 : après suppression, `INSERT` d'un `numero` ou `code` déjà consommé réussit ; **[CONSTATÉ]** B3 : tant que la ligne existe, `UNIQUE` l'empêche. **[DÉD]** deux conséquences :
1. **La non-suppression apporte une protection que le compteur ne donne pas** : `UNIQUE(numero)` persiste. C'est l'argument technique principal en faveur de R-A (au-delà du métier).
2. **Même avec R-A, un numéro « trou »** (consommé par un crash, jamais associé à une ligne) reste insérable à la main : le SQL ne peut pas l'interdire et **CK-02 ne le détecte pas** (CK-02 compare séquences et numéros présents, §14). Cette limite relève du service (le service n'attribue que par la séquence) ; elle ne justifie aucune nouvelle contrainte.

### E-7 — Client `a_rattacher` après rattachement (silence)

**[DOC]** le rattachement « réaffecte `client_id` » des devis, BC et factures vers le client cible (Modèle §4.4 l.272 ; Métier l.104). **Aucun document ne dit ce que devient le client `a_rattacher` d'origine** (supprimé, archivé, conservé tel quel). Il porte un `CLI-xxxx` attribué (les codes des clients importés suivent le format V6, CDC §18 l.573). Avec R-A, il ne peut plus être supprimé : il devra être **archivé** ou rester `a_rattacher`. **Décision requise** (section 9).

### E-8 — `situation_numero` (tranche 006, cas limite)

**[DOC]** `situation_numero` est un ordinal par BC (D-07), unique **parmi les situations actives** (`uq_situation_actif … WHERE cancelled_at IS NULL`, Modèle l.382). **[DÉD]** après annulation de la dernière situation (n° 2), la situation suivante peut reprendre le n° 2 : le **numéro de situation** est réutilisé, alors que le **numéro de facture** `FAC-` est neuf. Si « situation n° 2 » apparaît sur le PDF, R-B pourrait s'y appliquer. **Pas de règle à créer ici sans décision** (section 9) ; à trancher avant 006.

### E-9 — Restauration

**[DOC]** Modèle §11.2, §11.4 : la restauration remplace la base ; le high-water relève le compteur ; « un avertissement liste les numéros consommés que la sauvegarde ne contient plus ». **[DÉD]** des objets numérotés **disparaissent physiquement** et leurs numéros deviennent des trous. C'est cohérent avec R-B et R-C, mais **contredit R-A au sens littéral**. **[PROP]** écrire que R-A porte sur les opérations applicatives ; la restauration est un retour à un état antérieur, tracé (`restauration` dans `historique`) et protégé pour les numéros par le high-water.

### Documentation et tests de 001–004 touchés

| Élément | Nature |
|---|---|
| INV-06, Modèle §4.4, §4.6 l.299, Métier l.103, l.182, l.501, §2.4 l.79 | formulations conditionnelles ou contraires à clarifier |
| D-33 (Modèle) | à remplacer par la nouvelle décision |
| `002_fournisseurs.sql` l.28-34, `003_devis.sql` l.17-19 | commentaires d'en-tête décrivant l'état à la date de la tranche : **ne pas modifier** (migrations historiques) ; la clarification se fait dans le modèle |
| `test_002` l.160-165, l.183-189 ; `test_003` l.297, l.385, l.705-706, l.721-731 ; `test_004` l.1798 | tests qui consacrent la suppression : **restent verts**, chacun n'appliquant que sa propre chaîne 001→N (annexe A, point 5). À **ne pas modifier** ; ils décrivent l'état de leur tranche |

---

## 5. Impacts sur Dépenses (tranche 005)

### 5.1 Conséquences directes de la chaîne « numérotée → pas de suppression → annulation/conservation → numéro consommé »

| # | Conséquence | Origine |
|---|---|---|
| D5-1 | **Q3 du cadrage 005 est rouverte** : l'option (a) « suppression physique permise » est **incompatible** avec la règle ; l'option (b) « interdite, ce qui exige un mécanisme d'annulation » devient la seule cohérente. Les raisons qui motivaient (a) tombent : le numéro est de toute façon consommé, et l'erreur de saisie se corrige par **annulation + nouvelle saisie** | R-A + cadrage 005 §9 Q3 |
| D5-2 | **A-4 (REPLACE contourne TR-01) disparaît** : un `BEFORE DELETE` sur `depenses` refuse aussi le DELETE implicite du REPLACE (`recursive_triggers=ON`, comme TR-19). TR-01 redevient effectif | E-4 |
| D5-3 | `depenses` aurait **2 triggers** au lieu de 1 (TR-01 immutabilité + non-suppression) ; le nombre exact dépend du modèle d'annulation choisi | [DÉD] |
| D5-4 | **Il faut un mécanisme d'annulation** : le cadrage 005 avait retenu « aucun statut » (R4 : ni statut de paiement, ni échéance). **Annulation ≠ paiement** : le refus d'un statut de paiement ne s'oppose pas à une annulation (date et motif, comme `cancelled_at` / `motif_annulation` des devis, BC, factures, règlements). **Le modèle exact reste à décider dans le cadrage 005**, comme demandé | [DOC] CDC §28, INV-100 ; [PROP] |
| D5-5 | **Conséquences à instruire pour ce modèle** (sans le fixer) : effet d'une dépense annulée sur l'analyse de marge (CDC §29 : « distinguer recettes et charges ») ; modifiable ou immuable une fois annulée ; une annulation de dépense peut-elle être levée ; `date_depense` dont l'année (yy) est immuable : corriger une année erronée = annuler + ressaisir ; fichier de pièce jointe d'une dépense annulée | à traiter au cadrage |
| D5-6 | **BC annulé et dépenses** (votre cas : matériel acheté avant l'acompte, client rétracté) : **les garanties nécessaires existent déjà** : (i) aucun DELETE de BC (TR-19, **[SQL]** 004 l.411) ; (ii) `depenses.bc_id` serait en `RESTRICT` (jamais CASCADE) ; (iii) l'annulation du BC est un `UPDATE bons_commande` : **aucun trigger de 001–004 ne touche une dépense** ; (iv) CDC/Modèle §14 : « Suppression d'un BC … le service n'émet aucun DELETE ». **Les dépenses déjà rattachées restent donc rattachées au BC annulé : conforme à votre énoncé, sans règle SQL supplémentaire** | [SQL] ; [DOC] INV-173, INV-174 |
| D5-7 | **Reste ouvert** (Q2 du cadrage) : **créer ou rattacher une *nouvelle* dépense à un BC déjà annulé** (facture matériel reçue après l'annulation). Votre cas décrit une dépense **antérieure** à l'annulation ; il oriente vers l'autorisation, **sans l'établir** pour une saisie postérieure. Reste une règle de service (confirmation ou non) | [DOC] silence ; cadrage Q2 |
| D5-8 | **Fournisseur** : avec R-A les fournisseurs ne se suppriment plus du tout ; la FK `depenses.fournisseur_id … RESTRICT` annoncée par 002 devient une garde **redondante mais obligatoire** (INV-05, un index par FK) | E-2 |
| D5-9 | **Import** (inchangé) : `depenses` reste bloc refusé de `import-v6.json` (Modèle §10.3, D-23) : aucune dépense importée n'est concernée par R-A | cadrage A-1 |

### 5.2 Effet sur le cadrage 005 déjà transmis

| Élément du cadrage | Effet |
|---|---|
| §0 synthèse (« 1 trigger », « aucun statut ») | à réviser : au moins 2 triggers, mécanisme d'annulation à décider |
| §2 modèle de données | colonnes d'annulation à décider (non fixées ici) ; l'esquisse DDL actuelle suppose la suppression permise |
| §3.2 (BC annulé), §4.3 INV-180/181 | INV-181 (« une dépense peut être supprimée ») **à réécrire** ; INV-180 inchangé |
| §6 A-3, A-4 | A-3 (« suppression physique ? ») et A-4 (« TR-01 face à un REPLACE ») **résolus** par R-A |
| §8 tests | groupes « Suppression » et « REPLACE » inversés (refus), nouveaux tests d'annulation ; cibles de mutation sur le trigger de non-suppression |
| §9 Q3 | à remplacer par la question du **modèle d'annulation** (après validation de R-A) |

**Ce rapport ne modifie pas le cadrage 005** (consigne).

---

## 6. Impacts sur les futures tranches (uniquement lorsque pertinent)

| Tranche | Pertinent ? | Impact |
|---|---|---|
| **006 Facturation** | Oui | `factures` (FAC/ACP/AVO) : déjà conforme sur le papier (TR-21, `cancelled_at`). À l'écriture : trigger `BEFORE DELETE` présent et **testé contre REPLACE** (E-4) ; `facture_lignes` en `RESTRICT` ; décision sur `situation_numero` (E-8) ; TR-02 chronologie inchangée |
| **007 Règlements** | Non (pas de numéro) | `reglements` : « jamais supprimé », TR-32 ; déjà conforme à la logique ; aucune règle de numérotation à ajouter |
| **008 Garanties** | Non (pas de numéro) | `garanties` : aucun UPDATE ni DELETE (TR-50) ; création `INSERT OR IGNORE` (autorisé par D-39) ; rien à changer |
| **009 PV** | Oui | `pv` : TR-40 ; la non-suppression est la **seule** garde contre la réutilisation d'un suffixe de levée (3.7) ; clarifier que le PV n'a pas d'annulation (Métier §2.4) ; réserves : non applicable |
| **010 Planification** | Non | `planning_evenements` n'est pas un objet numéroté ; `bc_notes` modifiables et supprimables (INV-102) : **hors règle**, à confirmer dans la formulation du périmètre |
| Import | Oui | devis/factures/PV importés à numéro historique : la ligne importée est conservée par R-A ; clients `a_rattacher` : E-7 |

---

## 7. Numérotation : cohérence d'ensemble

| Point | Constat |
|---|---|
| **`numerotation_sequences`** | une ligne par `(type_objet, annee)`, `dernier_numero` croissant (TR-95), ligne non supprimable (TR-96), upsert `ON CONFLICT DO UPDATE … RETURNING` seul autorisé. **Conforme à R-B et R-C** [SQL] [TEST] `test_004` l.2075-2148 |
| **`sequence_high_water`** (`machine.db`) | écrit **avant** le COMMIT (Modèle §5 l.528) ; `max_attribue` ne diminue jamais ; garde **de service uniquement** (D-30, aucun trigger dans `machine.db`). R-B repose donc sur cette garde pour la restauration et les crashs. Non testable en SQL |
| **Numéros attribués** | ligne persistante (BC conforme) ; ligne supprimable pour client/fournisseur/devis (E-1 à E-3) ; code modifiable pour client/fournisseur (E-5) |
| **Suppression** | voir E-1 à E-4. Après adoption de R-A : aucune suppression applicative d'un objet numéroté |
| **Annulation** | l'objet annulé **conserve sa ligne et son numéro** ; la séquence n'est jamais rendue. **[TEST]** `test_004` l.790-801 (BC), `test_003` (devis annulé). Création d'un nouvel objet après annulation : numéro suivant du compteur, jamais celui de l'annulé [DOC] Modèle §6 l.557 |
| **Sauvegarde** | la sauvegarde copie la base métier ; `machine.db` (donc le high-water) n'est **jamais** sauvegardée ni restaurée (Modèle §5, CDC l.1173) : c'est ce qui rend R-B robuste à la restauration |
| **Restauration** | formule §11.4 : `dernier_numero := max(restauré, max_attribue)` ; avertissement listant les numéros consommés absents. Cohérent avec R-B et R-C ; les objets postérieurs à la sauvegarde disparaissent (E-9) |
| **Démarrage après crash** | `max_attribue > dernier_numero` → `max_attribue` conservé, trou journalisé (§11.4 l.771) |
| **Rollback en session** | non traité par les documents (1.4 point 3) |
| **Import** | `dernier_numero` fourni par fichier, validé ≥ plus grand numéro V6 du fichier ; `max_attribue := dernier_numero` ; numéros historiques hors format V6 n'alimentent pas les séquences (§10.6). Conforme à R-B ; INV-135 |
| **`INSERT OR REPLACE`** | interdit par convention (D-39, conventions §9). **Protégé** sur : `numerotation_sequences` (TR-96), `bons_commande` (TR-19), `import_anomalies` (TR-90), lignes et garanties de devis (TR-11) et de BC (TR-13). **Non protégé** sur : `clients`, `fournisseurs`, `devis` (E-4). La future `depenses` doit être protégée dès sa création |
| **Mécanismes de suppression implicite** | `ON DELETE CASCADE` : `prestation_garanties` → prestation, `devis_lignes` → devis, `devis_ligne_garanties` → ligne, `bc_ligne_garanties` → ligne. Aucun `SET NULL` dans 001–004 et `machine/001`. Le seul qui atteint les données d'un objet numérotable est `devis_lignes.devis_id` (3.3). `INSERT OR REPLACE` : voir ci-dessus |

---

## 8. Corrections nécessaires (listées, **non réalisées**)

| # | Nature | Cible | Correction | Forme | Dépend de |
|---|---|---|---|---|---|
| C-1 | Documentaire | Modèle §4.4 l.273-275, Métier l.103, l.501 | remplacer « ayant un historique » par la règle inconditionnelle (archiver, jamais supprimer) | clarification | D1, D2 |
| C-2 | Documentaire | Modèle §4.6 l.299, D-33, Métier l.182 | retirer « un devis sans BC peut être supprimé » ; l'annulation du devis (dès `en_attente`) est la sortie | clarification + décision remplaçant D-33 | D3 |
| C-3 | Documentaire | INV-06 | reformuler : objets numérotés jamais supprimés, sans condition d'historique ; ajouter un INV (numéro à fixer) pour R-B / R-C si non déjà couvert par INV-22 | invariant | D1 |
| C-4 | Documentaire | Métier §2.4 l.79 | ajouter client, fournisseur, devis, dépense ; harmoniser « annulé ou archivé » ; lever l'ambiguïté PV (3.7) | clarification | D1 |
| C-5 | Documentaire | Modèle §6, §8, §14 ; conventions §9 | généraliser « suppression d'un BC » en « suppression d'un objet numéroté » ; exiger un `BEFORE DELETE` pour toute table d'objet numéroté (condition d'efficacité de `recursive_triggers=ON`) ; limite de la restauration (E-9) | clarification | D1 |
| C-6 | Documentaire | Modèle §11.4 | définir « attribué » (COMMIT) et traiter le rollback en session | clarification | D1 |
| C-7 | **SQL** | `clients`, `fournisseurs`, `devis` | 3 triggers `BEFORE DELETE` de non-suppression (message `INV-xx`, même schéma que TR-19) | **migration ultérieure** | D2, D3, D4 |
| C-8 | **SQL** | `clients.code`, `fournisseurs.code` | trigger d'immutabilité (même schéma que TR-01) | **migration ultérieure** | D2, D4 |
| C-9 | **SQL** | `depenses` (005) | `BEFORE DELETE` conforme dès la création + modèle d'annulation | tranche 005 | D5 |
| C-10 | **SQL** | `factures` (006), `pv` (009) | vérifier trigger `BEFORE DELETE`, absence de contournement REPLACE | à la création | — |
| C-11 | Applicative (service) | UI et services | aucun `DELETE` émis sur un objet numérotable ; « supprimer » devient « archiver » (client, fournisseur) ou « annuler » (devis, dépense) | spécification de service | D1 à D3 |
| C-12 | Tests | nouveaux tests de la migration C-7/C-8 | DELETE direct et REPLACE refusés pour clients, fournisseurs, devis ; `code` immuable ; campagne de mutation dédiée (conventions §7.1) ; **tests 001–004 inchangés** | tests de la migration ultérieure | C-7 |
| C-13 | Documentaire | Modèle §15 et registre INV | ajouter la décision, les INV, l'entrée de journal, la ligne §17.1 de la migration ultérieure ; passer le modèle à la version suivante **avant** d'écrire la migration (conventions §5) | procédure | toutes |

**Où placer C-7 et C-8 [PROP]** : ni réécriture de 001–004, ni nouvelle tranche qui décalerait l'ordre officiel 005–010. Deux options (décision D4) : **(a)** dans `005_depenses.sql`, section « gardes complémentaires des tranches antérieures » ; précédent direct : 004 ajoute `tr_96` sur une table de 001 « pour compléter tr_95 » ; **(b)** différer chacun à la tranche qui crée l'objet (non applicable ici, ces tables existent déjà). **(a)** est la seule compatible avec l'ordre officiel sans nouveau numéro de migration, au prix d'une tranche 005 plus large (et d'une campagne de mutation couvrant aussi ces triggers).

---

## 9. Décisions à valider

Seules les décisions qui changent réellement le contenu des documents ou du SQL sont listées.

| # | Décision | Options | Recommandation **[PROP]** |
|---|---|---|---|
| **D1** | **Adopter la règle R-A / R-B / R-C et son périmètre** : objets issus des séquences + suffixe de levée ; « annulé ou archivé » ; numéros historiques importés inclus pour R-A ; « attribué » = création validée (COMMIT) ; restauration hors portée | (a) adopter tel que formulé en 1.1 avec les précisions 1.4 ; (b) adopter sans les précisions (les points restent flous) | **(a)** : sans la définition de « attribué » et la limite de la restauration, deux cas d'application resteraient indécidables |
| **D2** | **Client et fournisseur** : archivage seul ; **sort du client `a_rattacher`** après rattachement (E-7) ; immutabilité de `code` (E-5) | (a) archivage seul, `a_rattacher` archivé après rattachement, `code` immuable ; (b) archivage seul, `a_rattacher` conservé tel quel ; (c) suppression conservée pour les clients/fournisseurs sans historique (règle actuelle) | **(a)**, sauf si vous souhaitez conserver la suppression d'un client saisi par erreur (c), auquel cas R-A devient « sauf client et fournisseur sans historique » |
| **D3** | **Devis** : supprimer la possibilité de supprimer un devis sans BC (remplace D-33), y compris un brouillon `en_attente` jamais envoyé ; l'annulation est la sortie | (a) aucune suppression ; (b) maintenir D-33 pour `en_attente` seulement | **(a)** : le numéro `DEV` est consommé dès la création ; `en_attente → annule` est possible (T1). (b) crée une exception que seul le statut distingue |
| **D4** | **Véhicule de la correction SQL** (C-7, C-8) et **traitement du défaut E-4** | (a) triggers ajoutés dans `005_depenses.sql` (précédent TR-96) ; (b) migration dédiée hors ordre officiel ; (c) ne rien ajouter au SQL, corriger les documents seulement (E-4 resterait ouvert) | **(a)** ; et corriger E-4 **quelle que soit** la décision D1 (défaut d'immutabilité indépendant de la règle) |
| **D5** | **Dépense** : confirmer qu'une dépense n'est jamais supprimée (Q3 de 005 rouverte) et qu'un mécanisme d'annulation est nécessaire ; le **modèle exact** est décidé ensuite dans le cadrage 005 | (a) oui ; (b) non (la dépense reste supprimable : exception explicite à R-A) | **(a)** : cohérent avec D1 et avec votre cas du BC annulé |
| **D6** | **`situation_numero`** (E-8) : à traiter comme numéro définitif (jamais réutilisé après annulation) ou comme simple ordinal | (a) ordinal (réutilisable) ; (b) numéro définitif | **À trancher avant 006**, selon que ce numéro est visible sur le document remis au client ; je ne propose pas de choix sans cette information |

**Ce que cet audit ne conclut pas** : le modèle d'annulation des dépenses, la règle pour une *nouvelle* dépense sur un BC annulé (Q2), et le contenu exact des invariants et décisions (numéros à fixer à l'intégration). Je m'arrête ici ; je reprends le cadrage 005 après votre validation.

---

## Annexe A — Protocole de vérification (rejouable)

Base : `:memory:`, migrations `metier/001` à `004` appliquées dans l'ordre, `PRAGMA foreign_keys=ON`, `PRAGMA recursive_triggers=ON`. Script de travail conservé hors dépôt.

1. **A — DELETE** : `DELETE FROM clients WHERE id=?` (A1, A4 archivé), `DELETE FROM fournisseurs …` (A2, A2b archivé), `DELETE FROM devis …` avec une ligne, pour `en_attente`, `accepte`, `refuse`, `annule` (A3) → tous acceptés, lignes en cascade.
2. **B — Réutilisation** : séquence `DEV/26` à 1, suppression du devis, réinsertion de `DEV-00001-26` (B1) et de `CLI-0001` (B2) → acceptées ; réinsertion d'un numéro existant (B3) → `UNIQUE` refuse.
3. **C — REPLACE** : `INSERT OR REPLACE INTO clients/fournisseurs/devis (id, …)` sur ligne existante : acceptés (C1, C3, C4 pour `en_attente`, `refuse`, `annule`) ; client référencé par un devis refusé (C2, FK) ; `numerotation_sequences` existante refusée (C8, TR-96).
4. **D, E, T, U** : triggers `DELETE` présents (`bons_commande`, `numerotation_sequences` seulement) ; liste des FK et de leurs actions ; transitions `en_attente → annule` (T1), `actif ↔ archive` (T3, T4) ; `UPDATE clients.code` / `fournisseurs.code` acceptés (U1, U2), `UPDATE devis.numero` refusé (U4).
5. **Indépendance des tests 001–004** : chaque `migrer()` n'applique que sa chaîne (`test_002` l.32-40 : 001-002 ; `test_003` l.56-64 : 001-003 ; `test_004` l.122-130 : 001-004). Un trigger ajouté par une migration ultérieure ne modifie aucun de leurs résultats.

## Annexe B — Index des sources principales

| Sujet | Sources |
|---|---|
| Numérotation, jamais réutilisé | Modèle §6 l.539-561, §10.6, §11.4 l.768-772 ; INV-20 à INV-25, INV-135 ; Métier l.60-70, l.812 ; CDC §19 l.590, §42 l.1156-1175 ; Audit l.510, l.559 |
| Non-suppression | INV-06, INV-53, INV-70, INV-78, INV-95, INV-105, INV-110, INV-174 ; Modèle §4.4, §4.6 l.299, §4.7 l.331, §8 l.601-635 ; Métier §2.4 l.79 ; CDC l.532, l.645 |
| REPLACE et `recursive_triggers` | INV-07 ; D-39 ; Modèle §1 l.47-50 ; conventions §7, §9 ; `004` l.32-35 ; tests `test_004` l.2075-2260 |
| Séquences et high-water | `001_initial.sql` l.77-96, l.271 ; `004_bons_commande.sql` l.494 ; `machine/001_initial.sql` l.186-197 ; INV-22, INV-25, D-27, D-30 |
| Suppression dans le SQL | `001` l.246 (TR-90) ; `002` l.28-34 ; `003` l.17-19, l.376-409 ; `004` l.15, l.411, l.453-498 |
