# PLAN DE MISE À JOUR DOCUMENTAIRE — Règle d'annulation du BC (corrective 009a) — V3

## 1. Objet et statut de la proposition

**Nature** : proposition non officielle, en lecture seule. Elle remplace le plan V2 (`PLAN_MAJ_DOC__009a_regle_annulation_bc.md`, conservé). Aucun document de `docs/`, aucune migration, aucun test et aucun diff n'est modifié ; aucun commit, aucun push.
**Référence relue** : `main` = `ca00c50` (le 2026-10-13). Depuis 74adb2f, `main` n'a reçu que les trois fichiers du lot V2 ; `docs/` et `src-tauri/` sont inchangés. Les numéros de ligne ci-dessous sont ceux de `ca00c50`.
**Statut des éléments cités** : `docs/` = sources officielles ; `fichiers-a-relire/` = propositions, **aucune n'est une décision validée** (arbitrage de Rémy du 2026-10-13 : rien de ce qui est en relecture n'est réputé validé).

**Erreurs du plan V2 corrigées par cette V3**
1. **Deux bases mélangées.** V2 modifiait des lignes de `docs/` (INV-44 l.78) mais s'appuyait sur des lignes qui n'existent **que** dans les propositions (INV-45 MAJ, INV-188, D-46, D-55, D-56, D-61, E-15). Aucun de D-55, D-56, D-61 ni de la chaîne des rangs n'existe dans `docs/` (recherche faite : 0 occurrence de « D-55 », « D-56 », « D-61 », « 005c » dans `docs/`).
2. **Contradiction cascade.** V2 conservait la clause de D-46 « devis non annulés automatiquement » tout en laissant INV-45 « inchangé » ; INV-45 officiel dit l'inverse (§4, C1).
3. **Oublis.** V2 omettait la puce du CDC l.543 (« facture d'acompte annulée reste conservée ») et les passages du modèle qui attribuent l'annulation au **service seul** (l.332, l.356, l.640), contraires à un trigger.
4. **Erreur de comptage.** V2 demandait de « recompter les triggers (15) » (modèle l.488) : ce chiffre est celui de la migration 004, non un total.
5. **Numéros et rangs pris pour acquis** (E-21, E-15, V3.14, rangs 14 et 15) : ils sont ici présentés comme **proposés** et soumis à arbitrage (§5, §8).
6. **Rangs et chaîne** présentés comme modifications de `docs/` : ils n'existent que dans les propositions (conventions MAJ §5, modèle MAJ §17.1, diff 011).

## 2. Sources officielles relues et hiérarchie appliquée

**Hiérarchie** (`docs/conception/conventions-techniques-v6.md` §2, l.20–24) : 1. CDC · 2. modèle de données SQLite · 3. invariants · 4. modèle métier · 5. errata (« traçabilité historique uniquement »). *« Une convention de code ne peut pas contredire ces documents. »* Règle de cohérence (`docs/README.md` l.33–35) : lorsqu'une décision validée est intégrée au CDC, celui-ci « présente directement la règle courante » ; les errata gardent la trace. Le fichier des errata (l.3) : « Le CDC V6 est gelé. Tout écart décidé ensuite est tracé ici ».
Chemin réel des errata : `docs/décisions/cdc-errata-v6.md` (avec accent ; le texte du fichier écrit `docs/decisions/`).

**Fichiers relus** : le CDC ; le modèle V3.12 (`docs/README.md` l.23 et l.37 : « en relecture (non validée) ») ; `invariants.md` (registre version 6, 2026-10-02) ; le modèle métier ; les errata ; `conventions-techniques-v6.md` ; les migrations `004`, `005b`, `005c`, `006`, `009a` (proposée) ; les tests `test_004`, `test_005b`, `test_005c`, `test_006`, `test_009a`.

| Règle | Formulation exacte (extrait) | Emplacement | Statut |
|---|---|---|---|
| D-05 | « Annulation directe du BC **interdite** dès qu'une facture autre qu'un acompte non réglé existe (V3.4 conservé), plus strict que CDC §17 (voir errata E-07) » | modèle V3.12 l.898 | décision **Validée 2026-09-29** (dans un modèle « en relecture ») |
| INV-44 | « interdite si encaissement actif, ou si une situation a été émise (même annulée) ; autorisée avec acompte non réglé, annulé dans la même transaction ; toute autre facture interdit l'annulation (décision D-05) » · garde **SVC, test** | `invariants.md` l.78 | règle validée |
| E-07 | « interdit l'annulation directe dès qu'une facture autre qu'un acompte non réglé existe » | errata l.14 | Validé (D-05, 2026-09-29) |
| CDC §17 | l.512 idem D-05 ; l.514 « Un acompte non réglé peut être annulé automatiquement avec le BC… » ; l.536–543 « le devis passe à Annulé… la facture d'acompte annulée reste conservée lorsqu'elle existe » | CDC | CDC gelé |
| Annulation = **service** | « La règle complète d'annulation (INV-44…) reste dans le service : elle dépend des tables de facturation… que la migration BC n'anticipe pas » (l.332) ; tableau « Annulation du BC (INV-44) \| — \| oui \| — » (l.356) ; « Autres règles de service sans trigger : … annulation du BC (INV-44) » (l.640) | modèle V3.12 | règle validée |
| INV-45 | « BC annulé : devis `annule` (BC d'abord, puis devis, dans la même transaction : TR-18)… » | `invariants.md` l.79 | règle validée |
| INV-175 / TR-18 | « un devis ayant un BC ne quitte `accepte` que si ce BC est `annule` » | invariants l.86 ; modèle l.611 | règle validée |
| CK-13 | requête diagnostique ; signale notamment « devis `annule` sans BC `annule`, et BC `annule` sans devis `annule` » | modèle V3.12 §14 l.886 | règle validée |
| D-36 | le service « annule le BC puis le devis » (l.351) ; TR-18 | modèle V3.12 | Validée |
| INV-173 / TR-12 | « Un BC `annule` est terminal… » | invariants l.84 ; modèle l.605 | règle validée |
| D-46, D-56, INV-188, INV-189, E-15, D-55, D-61 | absents de `docs/` | propositions `MAJ__*` et diff 011 | **propositions** (le diff 011 est « validé » dans la conversation, non appliqué à `docs/`) |
| Chaîne des rangs | absente de `docs/conventions` (qui ne liste que 001–003) | conventions MAJ §5 | proposition |

## 3. Règle métier cible

> Un bon de commande ne peut plus être annulé dès qu'au moins une facture existe pour ce BC : acompte, situation, solde ou avoir. Le paiement, le montant restant dû et la compensation par des avoirs ne changent pas cette interdiction. Un avoir, même total, ne rétablit pas le droit d'annuler le BC. Un acompte prévu au devis, sans facture émise, n'interdit pas l'annulation.

Cette formulation est celle de la demande du 2026-10-13 ; Rémy l'a confirmée dans ses messages des 07:29 et 08:08 du même jour. **Elle n'est consignée dans aucun fichier du dépôt** : c'est un arbitrage oral, à inscrire (§5, E).
**Traduction technique** (proposée) : `TR-103`, migration corrective `009a`, rang **proposé** 13 ; une ligne de `factures` référençant `bc_id` suffit ; aucune lecture des caches ; aucune réparation de données.

## 4. Contradictions documentaires constatées

| # | Contradiction | Passages | Verdict |
|---|---|---|---|
| **C1** | **Cascade BC → devis** : le plan V2 gardait « devis non annulés automatiquement » (D-46) et INV-45 « inchangé ». | **Officiel** : INV-45 l.79 « devis `annule` (BC d'abord, puis devis) » ; CDC l.536–541 « Lorsqu'un BC peut légalement être annulé : le devis passe à Annulé » ; modèle l.351 (le service « annule le BC puis le devis ») ; C-28 l.818 ; CK-13 l.886 (« BC `annule` sans devis `annule` » = anomalie) ; modèle l.366 et l.717. **Proposé seulement** : D-46 (MAJ l.1195), INV-45 MAJ l.77, TR-18 MAJ l.778 « aucune cascade », C-28 MAJ l.1039, CK-13 MAJ l.1140 (clause supprimée). | **Confirmée.** Les sources officielles imposent la cascade ; les propositions imposent son absence ; V2 mélangeait les deux. |
| **C1 bis** | Même sujet pour **INV-175 et TR-18**. | Ces deux règles ne conditionnent que « BC `annule` » : elles sont satisfaites avec ou sans cascade (vérifié, §9-B). | **Infirmée** pour INV-175 et TR-18. |
| **C2** | La règle 009a **exige** de modifier la cascade. | Le trigger lit uniquement `factures` et refuse la transition ; il ne cite ni `devis` ni `bc_devis` ; une annulation refusée laisse le devis `accepte`, ce qu'impose TR-18 (vérifié, §9-B). | **Infirmée.** 009a est indépendante du sujet de la cascade. |
| **C3** | Texte officiel (cascade) contre migrations **livrées** et leurs tests (« aucune cascade » : 005b l.457, tests `test_005b` l.1564–1568 et `test_005c` l.804–811). | cf. C1 | **Confirmée, préexistante, hors périmètre 009a.** |
| **C4** | Exception « acompte non réglé » contre la règle cible. | D-05 l.898 ; INV-44 l.78 ; E-07 l.14 ; CDC l.512 ; modèle métier l.248 et l.801 | **Confirmée.** |
| **C5** | **Responsabilité** : le modèle attribue l'annulation au **service seul** ; `TR-103` en fait aussi une garde SQL. Les conventions (§5, `docs/` l.88) interdisent « un trigger… qui contredit… les responsabilités explicitement attribuées aux services ». La migration 004 (l.39) le dit aussi. | modèle l.332, l.356, l.640 ; INV-44 « SVC, test » | **Confirmée** (point absent de V2). Le motif écrit en l.332 (« que la migration BC n'anticipe pas » la facturation) n'est plus vrai depuis 006. |
| **C6** | Puce CDC l.543 « la facture d'acompte annulée reste conservée lorsqu'elle existe ». | CDC §17 | **Confirmée** : sous la règle cible, un BC annulable n'a aucune facture. |
| **C7** | Parcours d'import « BC historique annulé » (factures puis annulation) contre la règle et l'arbitrage « aucun import de BC annulé ». | modèle l.366 et l.717 ; INV-169 l.190 (journal l.251) | **Confirmée.** |
| **C8** | Flux distinct : acompte non réglé annulé automatiquement ; annulation de facture ; `cancelled_at`. | CDC l.435, 441, 514, 518 ; INV-35 ; modèle l.315, 574, 617 (TR-24), 791 (C-01), 834 (T-08) ; modèle métier l.272, 800 | **Confirmée, à traiter à part** (la 006 livrée n'a ni `cancelled_at` ni UPDATE de facture : `tr_20`). |
| **C9** | « Annulation sans condition de facturation » contre la règle cible. | D-46 MAJ l.1195 ; E-15 MAJ l.22 ; INV-44 MAJ l.76 ; MAJ modèle l.458, 483 | **Confirmée** — mais ce sont des propositions. |
| **C10** | D-55, D-56, D-61, INV-188 absents de `docs/` alors que `005c` et `006` les citent. | cf. §2 | **Confirmée, préexistante, hors périmètre.** |
| **C11** | `D-56` / `INV-173` / `TR-12` / `005c` incompatibles avec 009a. | 009a ne touche aucun BC déjà annulé (§7) | **Infirmée.** |
| **C12** | `INSERT OR REPLACE` / UPSERT contournent le contrôle. | tests C du fichier 009a (exécutés) | **Infirmée.** |

## 5. Arbitrages métier indispensables (aucune décision inventée)

| | Question exacte | Options | Sans arbitrage |
|---|---|---|---|
| **A** | **Quelle est la base du prochain modèle ?** Rémy a décidé « V3.14 » (2026-10-13, 06:26) ; le diff 011 écrit « Aucune V3.14 n'est ouverte » ; `docs/` est en V3.12. V3.14 = V3.12 seul, ou V3.12 + quelles parties de la V3.13 ? | (1) V3.12 + uniquement les lots validés ; (2) V3.13 promue avec modifications | les numéros E/C/T/D et les lignes « MAJ » ne peuvent pas être fixés (§8) |
| **B** | **L'annulation du BC reste-t-elle une règle de service seule, ou devient-elle aussi une garde SQL (TR-103) ?** Rémy a demandé un contrôle SQL (demande du 2026-10-13, 06:57) ; le modèle l.332, 356, 640 et INV-44 disent « service ». | (1) service **et** TR-103 (modifier l.332, 356, 640 et INV-44) ; (2) service seul (009a abandonnée) | la migration contredit `docs/` et la règle des conventions |
| **C** | **Cascade BC → devis** (C1, C3) : conserver la cascade officielle ou entériner l'absence de cascade livrée en 005b/005c ? | (1) cascade (CDC, INV-45, CK-13, C-28) → les tests 005b/005c et le service sont à revoir ; (2) pas de cascade → CDC l.536–541, INV-45, CK-13, C-28, D-36, modèle l.351/366/717 à modifier | **non bloquant pour 009a** ; bloque toute retouche de ces lignes |
| **D** | **Import** : Rémy a arbitré « aucun import de BC annulé ». Confirmer la **suppression** des passages l.366, l.717 et d'INV-169 (au lieu d'une restriction). | (1) suppression ; (2) conserver pour un BC annulé **sans facture** | C7 reste ouverte |
| **E** | **Support documentaire** : un nouvel erratum (CDC gelé) ou une autre voie ? Format d'annotation d'une décision révisée : `docs/` n'en connaît aucun (0 occurrence de « MODIFIÉE/remplacée/révisée ») ; seules les propositions emploient « [MODIFIÉE le …] ». | (1) nouvel erratum + annotation de D-05 et E-07 ; (2) modification directe sans annotation | numérotation impossible |
| **F** | **Rang 13 de 009a** : confirmer, après contrôle des `user_version` des bases de développement (Rémy, 08:08). | rang 13 (décaler 010 et 011) ou rang ≥ 14 | rang « proposé » seulement |
| **G** | **Anciens BC annulés** : conserver les clauses d'avoirs et de caches (INV-188, D-56, 005c) pour les BC annulés avant 009a. | conserver (recommandé) / signaler | sans objet pour la technique, ouvert pour le texte |
| **H** | **Anomalie historique** (BC annulé et facturé avant 009a) : ajouter un contrôle diagnostique (type CK) ou rien. | CK nouveau / aucune action | l'anomalie reste invisible |

## 6. Matrice des documents à modifier

*Statut : **N** = nécessaire (la règle cible l'impose) · **C** = conditionnel (dépend d'un arbitrage indiqué) · **NR** = non requis. La formulation F0 est celle du §3.*

### 6.1 CDC — `docs/specifications/cdc-fonctionnel-architectural-v6.md`

| Ligne | Règle actuelle | Correction proposée | Justification | Dépend de | Statut |
|---|---|---|---|---|---|
| 512 | « Annulation directe interdite dès qu'une facture autre qu'un acompte non réglé existe, notamment lorsqu'un solde impayé existe sans situation. » | « Annulation directe interdite dès qu'au moins une facture existe pour le BC (acompte, situation, solde ou avoir), réglée ou non ; un avoir, même total, ne rétablit pas le droit d'annuler. » | C4 ; README l.35 | E | **N** |
| après 512 | — | « Un acompte prévu au devis, sans facture émise, n'interdit pas l'annulation. » | clarification de la distinction | E | C |
| 543 | « la facture d'acompte annulée reste conservée lorsqu'elle existe » | supprimer la puce | C6 | — | **N** |
| 514, 516, 518 | acompte non réglé annulé automatiquement ; situation « même annulée » ; « annulation de facture ou avoir » | aucune dans ce lot | C8 | flux séparé | NR |
| 536–541 | « le devis passe à Annulé » | **aucune** | C1/C2 : hors périmètre 009a | C | NR |

### 6.2 Modèle de données — `docs/conception/modèle-données-sqlite-v6-v3.12.md` (cible : version suivante)

| Ligne | Règle actuelle | Correction proposée | Justification | Dépend de | Statut |
|---|---|---|---|---|---|
| 898 (D-05) | cf. §2 | « Annulation directe du BC **interdite** dès qu'au moins une facture (acompte, situation, solde ou avoir) existe pour ce BC, réglée ou non, avoir total compris ; un acompte prévu au devis, sans facture, ne bloque pas » ; alternatives écartées : « autoriser avec acompte non réglé ; rétablir le droit par un avoir total ; se fonder sur les caches du BC » | C4 | A, E | **N** |
| 332 | « reste dans le service… que la migration BC n'anticipe pas » | « …le service porte la règle complète (motif, trace) ; la migration 009a (TR-103) en refuse la transition dès qu'une facture existe » | C5 | B | **N** si B(1) |
| 356 | `Annulation du BC (INV-44) \| — \| oui \| —` | colonne trigger : `TR-103` | C5 | B | **N** si B(1) |
| 640 | « Autres règles de service sans trigger : … annulation du BC (INV-44) … » | retirer cette mention | C5 | B | **N** si B(1) |
| tableau des triggers (l.605–617) | — | ajouter `TR-103 \| bons_commande / UPDATE (statut → annule) \| refusé dès qu'une ligne de factures référence le BC ; message INV-44 \| 44` | convention de nommage (`tr_<NN>`, conventions l.106) | A, B | **N** si B(1) |
| scénarios (l.809, C-19) | « Situation annulée, puis BC : annulation directe demandée → refusée (INV-44) » | compléter C-19 et ajouter des cas : acompte prévu sans facture (permise) ; facture d'acompte non réglée (refusée) ; facture réglée (refusée) ; avoir total (refusée) ; émission échouée ou défaite par rollback (permise) | INV : « Cas » obligatoire | A | **N** |
| tests (tableau T) | — | une ligne pour le test 009a | numérotation | A | C |
| l.366, l.717 | « BC historique annulé (import) » | supprimer, ou remplacer par « Aucun BC annulé n'est importé » | C7 | D | C |
| 488 | « Triggers (15) » | **aucune** (migration 004) | correction de V2 | — | NR |
| 315, 574, 617, 791, 834 | flux acompte automatique / TR-24 | aucune | C8 | flux séparé | NR |
| 351, D-35, D-36, TR-12, TR-18, TR-19, CK-13 | cascade, cycle de vie | **aucune** | C1/C2 | C | NR |

### 6.3 Invariants — `docs/conception/invariants.md`

| Ligne | Règle actuelle | Correction proposée | Justification | Dépend de | Statut |
|---|---|---|---|---|---|
| 78 (INV-44) | cf. §2 | « Annulation directe du BC interdite dès qu'au moins une facture (acompte, situation, solde ou avoir) existe pour ce BC, réglée ou non, quel que soit le reste dû ou le net après avoir ; un avoir, même total, ne rétablit pas le droit d'annuler ; un acompte prévu au devis, sans facture, n'interdit pas l'annulation (D-05) » · garde « **TRG (TR-103)**, SVC, test » · cas : C-19 et les nouveaux cas (retirer C-01 qui illustre le flux acompte) | C4, C5 ; test nommé `test_INV_44_*` déjà présent dans 009a | B, E | **N** |
| journal (l.210 et suivantes) | « Aucun INV ne… change de sens sans ligne dans le journal » (mode d'emploi) | une ligne datée : INV-44 modifié, motif, vérification (tests 009a), décision | règle du registre | E | **N** |
| en-tête | « Version du registre : 6 — 2026-10-02 » | incrémenter | règle du registre | A | C |
| 79 (INV-45), 84 (INV-173), 86 (INV-175) | cascade ; BC annulé terminal ; miroir | **aucune** | C1, C11 | C | NR |
| 190 (INV-169), journal 251 | « un BC historique annulé s'importe par les étapes normales… » | retirer cette incise | C7 | D | C |
| INV-35, INV-36, INV-61 | flux acompte | aucune | C8 | flux séparé | NR |

### 6.4 Modèle métier — `docs/conception/modèle-métier-V6.md`

| Ligne | Règle actuelle | Correction proposée | Justification | Dépend de | Statut |
|---|---|---|---|---|---|
| 248 | « Annulation : interdite directement dès qu'une facture autre qu'un acompte non réglé existe… Un acompte non réglé est annulé avec le BC. La correction passe sinon par avoir ou annulation de facture. » | F0 ; supprimer « Un acompte non réglé est annulé avec le BC » ; ne pas toucher « annulation de facture » (flux séparé) | C4 | E | **N** |
| 801 | « un BC dont la facturation dépasse un acompte non réglé ne peut pas être annulé directement ; une situation émise (même annulée) l'interdit toujours » | « un BC portant au moins une facture ne peut pas être annulé directement » | C4 | E | **N** |
| 249, 272, 800 | BC annulé conservé ; flux acompte | aucune | C8 | — | NR |

### 6.5 Errata — `docs/décisions/cdc-errata-v6.md`

| Ligne | Règle actuelle | Correction proposée | Justification | Dépend de | Statut |
|---|---|---|---|---|---|
| nouvelle ligne | — | un erratum « §17 Annulation du BC » : ancienne formulation = celle de E-07 ; décision = F0 ; motif : factures immuables (006) ; impact : INV-44, TR-103, CDC §17, D-05, 009a ; statut « Validé » seulement après décision de Rémy | « Un écart au CDC n'est valide que s'il figure dans ce tableau » (errata l.47) | A, E | **N** |
| 14 (E-07) | cf. §2 | ne pas réécrire la ligne ; annoter le statut : « révisé par E-xx » | l'errata est un registre de traçabilité | E | C |

### 6.6 Conventions techniques, README, audit et migrations livrées

| Fichier | Constat | Statut |
|---|---|---|
| `docs/conception/conventions-techniques-v6.md` §5 | ne décrit pas la chaîne des rangs ; sa règle « un trigger ne contredit pas les responsabilités des services » est satisfaite si B(1) | NR |
| `docs/README.md` | liste le modèle V3.12 ; à mettre à jour à la publication de la version suivante | C (A) |
| `docs/audit/…` l.143–144, 551 | analyse de l'existant, hors hiérarchie | NR |
| `004_bons_commande.sql` l.39 | commentaire « elle reste dans le service » : **livrée, non modifiable** ; devient obsolète | NR |

### 6.7 Propositions de `fichiers-a-relire/` (non officielles ; à aligner seulement si elles sont retenues)

| Fichier | Lignes | Alignement | Dépend de | Statut |
|---|---|---|---|---|
| MAJ modèle | D-05 l.1154 (« REMPLACÉE par D-46 / E-15 ») ; D-46 l.1195 ; D-35 l.1184 ; l.458, 483, 811 (« sans condition de facturation ») | retirer « annulation sans condition de facturation » et la mention « REMPLACÉE » ; **ne pas toucher** « sans cascade » (sujet C) | A, C | C |
| MAJ invariants | INV-44 l.76 ; INV-169 l.185 ; INV-188 l.219 ; INV-189 l.220 | INV-44 : texte du §6.3 ; INV-169 : retirer l'incise d'import ; INV-188 et INV-189 : aucun changement de texte | A, D | C |
| MAJ errata | E-15 l.22 | retirer « Remplace E-07 (et D-05) » et « Un BC peut être annulé » inconditionnel | A | C |
| MAJ conventions §5, MAJ modèle §17.1, diff 011 validé (blob `8124bf58…`), D-61, plan de remédiation P-4 | rangs 13/14 | 010 → 14, 011 → 15 **si F est confirmée** ; ajouter 009a (rang 13, corrective) ; le périmètre validé du diff 011 ne change pas | F | C |

## 6 bis. Matrice de cohérence

| Élément | Où | Rapport à 009a | Justification |
|---|---|---|---|
| **D-05** | modèle l.898 (officiel) | **directement concerné** | porte la règle ; son exception est supprimée |
| **D-46** | MAJ seulement | **indirectement concerné** | sa clause « sans condition de facturation » contredit la règle ; sa clause « sans cascade » est hors périmètre |
| **TR-18** | modèle l.611 ; livré 005b | **hors périmètre** | agit sur `devis`, satisfait avec ou sans cascade ; 009a ne lit pas `devis` |
| **INV-44** | invariants l.78 | **directement concerné** | texte, garde et cas à modifier |
| **INV-45** | invariants l.79 | **hors périmètre** | traite la cascade (sujet C), non la condition d'annulation |
| **INV-173** | invariants l.84 | **indirectement concerné** | un BC annulé est terminal ; 009a n'affecte pas les BC déjà annulés |
| **INV-175** | invariants l.86 | **hors périmètre** | miroir devis ↔ BC ; conditionné à « BC annulé » seulement |
| **INV-188** | MAJ seulement | **indirectement concerné** | « avoir encore possible » ne vaut plus que pour les BC annulés avant 009a |
| **CK-13** | modèle §14 | **hors périmètre** (technique) / **indirectement** (données) | signale « BC annulé sans devis annulé » : question de cascade (C), non de facturation |
| **D-56** | MAJ seulement ; livré 005c | **indirectement concerné** | trois caches libres sur BC annulé ; ne concerne que les BC annulés avant 009a |

## 7. Traitement des données historiques

La migration 009a ne contient qu'un `CREATE TRIGGER` ; elle ne lit, ne crée, ne modifie ni ne supprime aucune ligne (§9).

| Situation | Comportement après 009a |
|---|---|
| **Nouveau passage à `annule`** | refusé (`INV-44`) si au moins une facture existe ; accepté sinon (acompte prévu sans facture compris) |
| **BC déjà `annule` sans facture** | inchangé ; aucun avoir possible (aucune facture d'origine) |
| **BC déjà `annule` et facturé** (avant 009a) | **laissé tel quel** : terminal (TR-12), ni nouvel acompte/situation/solde (`tr_16`, INV-188), avoir encore possible, trois caches recalculables (005c / D-56), jamais supprimé (TR-19) |
| **UPDATE d'un BC déjà annulé sans changer le statut** | non visé par le trigger (`OLD.statut <> 'annule'`) |
| **Anomalie signalée, jamais réparée** | un BC annulé et facturé est détectable par la requête de test `DETECT_BC_ANNULE_FACTURE` (hors schéma, lecture seule) ; l'ajout d'un contrôle documenté relève de l'arbitrage H ; aucune réparation automatique |
| **Import / restauration** | aucune exception ; un BC importé suit les mêmes triggers (INV-131) ; le parcours « BC historique annulé » est incompatible avec la règle si le BC porte une facture (C7) ; **CK-13 officiel** signale tout BC annulé dont le devis est resté `accepte` — situation produite par les migrations livrées (C3) et indépendante de 009a |

## 8. Numérotation et versions proposées

*Aucun numéro n'est acquis. Registres complets relevés dans `docs/`, dans les propositions, dans les cadrages et dans le SQL ; un numéro « libre » l'est dans cette union.*

| Élément | Registre relevé | Proposition | Statut |
|---|---|---|---|
| Version de départ du modèle | `docs/` : **V3.12** (« en relecture ») ; proposition V3.13 non promue ; diff 011 : « Aucune V3.14 n'est ouverte » | version suivante : **V3.14**, décision de Rémy du 2026-10-13 06:26 **non consignée** | arbitrage A |
| TR | `docs/` jusqu'à TR-96 ; MAJ jusqu'à TR-100 ; SQL livré jusqu'à `tr_102` (`tr_101`, `tr_102` dans 005 ; aucun modèle ne les inscrit) | **TR-103** (introuvable ailleurs) ; l'inscription au modèle reste à faire | proposé |
| INV | `docs/` jusqu'à 178 ; MAJ jusqu'à 202 ; diff 011 ajoute 203 | **aucun nouvel INV** ; INV-44 modifié sur place avec ligne de journal ; si un INV est voulu : 204 libre | proposé |
| D | `docs/` jusqu'à D-39 ; MAJ jusqu'à D-61 | **aucune nouvelle décision** requise (D-05 modifiée sur place) ; D-62 libre | proposé |
| E | `docs/` E-01 à E-09 ; MAJ E-10 à E-20 | **E-21** libre dans l'union ; **E-10** seulement si les errata MAJ ne sont pas retenus | arbitrage A et E |
| C | `docs/` C-01 à C-29 ; MAJ jusqu'à C-42 | **C-43 et suivants** (nombre exact selon les cas retenus) | proposé |
| T | tests livrés : T-44 à T-51 ; T-52 réservé à 010 ; diff 011 : « le prochain numéro libre est T-53 » | **T-53** s'il est pris par 009a (la phrase du diff 011 deviendrait T-54), sinon T-54 | arbitrage F |
| Rang de 009a | livrées : 1 à 12 ; aucune 010 dans `main` | **13, proposé** ; 010 → 14 et 011 → 15 **seulement si F est confirmée** ; une `010a` éventuelle → 15, une `011a` → 16 | proposé |
| Documents | à modifier : CDC, modèle de données, invariants, modèle métier, errata ; à laisser intacts : conventions `docs/`, audit, migrations livrées, tests livrés | — | — |

**Dépendances empêchant encore l'intégration** : arbitrages A, B, D, E, F ; vérification des `user_version` des bases de développement (non faite : l'ordinateur de Rémy est lié à la session mais aucun dossier n'est connecté).

## 9. Contrôles techniques et tests à exécuter

**A. Démontrés par la lecture du SQL** (`009a_bc_annulation_interdite_si_facture.sql`)
- condition de transition : `WHEN NEW.statut = 'annule' AND OLD.statut <> 'annule'` ;
- recherche par `bc_id` : `EXISTS (SELECT 1 FROM factures f WHERE f.bc_id = OLD.id)`, sans filtre de type (`factures.type` ∈ acompte, situation, solde, avoir : 006) ;
- aucune lecture de `montant_deja_facture_ht`, `avancement`, `date_100_facture` ;
- le fichier ne contient qu'un `CREATE TRIGGER` : aucune écriture, donc aucune modification rétroactive ; ni `BEGIN`/`COMMIT` ni `PRAGMA` (le runner pose `user_version`) ;
- `tr_103` ne cite ni `devis` ni `bc_devis` ; il ne partage aucun événement avec TR-18 (sur `devis`) ; il s'ajoute aux trois `tr_12_bons_commande_*` (BEFORE UPDATE) et à `tr_19` (DELETE) sans les modifier.

**B. Exécutés au cours de cette tâche**
- `git apply --check` du diff V2 du dépôt sur un clone neuf de `main` `ca00c50` : **OK** ; `docs/` inchangé.
- Tous les fichiers de tests, un par un, sur ce clone avec le diff appliqué : 001 (28) · 002 (18) · 003 (68) · 004 (150) · 005 (158) · 005a (119) · 005b (153) · 005c (62) · 006 (309) · 007 (279) · 008 (254) · 009 (268) · **009a (50)** · premier démarrage (13) = **1 929 tests, 0 échec**. Les 50 tests de 009a couvrent : transition, types y compris avoir, indépendance des caches, acompte prévu, facture réglée ou non, émission échouée ou défaite par `ROLLBACK`, `INSERT OR REPLACE`, `UPDATE OR REPLACE`, UPSERT, atomicité, BC déjà annulé (aucune donnée touchée), non-régression de `tr_12`, `tr_19`, `tr_20`, `tr_21`, rang et `user_version`.
- Contrôle ad hoc hors dépôt (8 vérifications OK) : annulation refusée ⇒ le devis reste `accepte` et TR-18 refuse sa sortie ; BC sans facture annulé ⇒ aucune cascade en SQL et TR-18 libère le devis ; le trigger ne cite pas `devis`.
- Les 12 mutants sur 12 (11 tués, 1 équivalent) ont été exécutés lors de la tâche précédente, **non rejoués ici**.

**C. Non vérifiés**
- aucun test 009a ne cible TR-18 : l'absence de conflit repose sur la lecture et sur le contrôle ad hoc ci-dessus (un test dédié peut être ajouté plus tard, hors de cette tâche) ;
- `user_version` des bases de développement ; comportement du futur runner (inexistant) ; contenu de la version suivante du modèle.

## 10. Critères objectifs de validation

1. Arbitrages A, B, D, E, F consignés par écrit (leur réponse exacte).
2. Les modifications « N » du §6 appliquées en un seul lot ; aucune ligne « NR » touchée.
3. `docs/` : plus aucun passage « acompte non réglé » rattaché à l'annulation du **BC** (recherche textuelle), hors flux séparé (§4 C8).
4. `TR-103` inscrit au modèle ; INV-44 porte « TRG (TR-103) » ; ligne de journal INV-44 présente.
5. Le diff V2 s'applique sur le `main` du moment ; la suite complète reste verte.
6. Les bases de développement sont à `user_version` ≤ 12, ou la procédure de rattrapage du rapport final est appliquée.
7. Les rangs de 010 et 011 changent dans les documents au moment où 009a est intégrée, jamais avant.

## 11. Points encore bloquants

1. **A** : base et numéro de la version suivante du modèle.
2. **B** : trigger SQL contre « service seul » ; sans réponse, `TR-103` contredit `docs/` (C5).
3. **D** : sort des passages d'import (C7).
4. **E** : support de la décision (erratum) et format d'annotation.
5. **F** : rang 13 et vérification des bases de développement.
6. **C** (cascade) : **non bloquant pour 009a**, mais bloque toute retouche d'INV-45, TR-18, CK-13, C-28, D-36, CDC l.536–541.
7. **Flux INV-35** (acompte annulé automatiquement, annulation de facture) : à traiter séparément.

## 12. Conclusion

**Encore bloqué : pas de feu vert définitif à 009a.** Sur le plan technique, la migration et ses 50 tests sont cohérents avec la règle cible (1 929 tests verts). Sur le plan documentaire, la règle contredit D-05, INV-44, E-07, le CDC §17 (l.512 et l.543) et le modèle métier ; le trigger contredit en outre l'attribution de l'annulation au service (modèle l.332, 356, 640) tant que l'arbitrage B n'est pas rendu ; les passages d'import (modèle l.366, 717 ; INV-169) restent à trancher. La contradiction de cascade relevée en revue est **réelle**, mais **indépendante de 009a** : elle impose seulement de ne pas toucher INV-45, TR-18, CK-13, C-28 et D-36 dans ce lot.
