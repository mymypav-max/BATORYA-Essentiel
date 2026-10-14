# B — Matrice de cohérence

> **Zone non officielle.** Une fiche par problème, avec les 7 colonnes demandées. Lignes vérifiées sur `d1d8bb9`. « Autorité » = document faisant autorité **selon la hiérarchie** (conventions §2) ou décision de Rémy identifiée.
> Légende : **[F]** vérifié · **[D]** déduction · **[NV]** non vérifiable. Diffs candidats : `D_propositions/`.
> **Aucune fiche ne tranche la cascade BC → devis** (voir M-05 et le dossier F).

---

## M-01 — Règle d'annulation du BC (exception « acompte non réglé »)
- **Références** : modèle V3.12 l.898 (D-05) ; `invariants.md` l.78 (INV-44) ; CDC l.512, l.543 ; métier l.248, l.801 ; errata l.14 (E-07) ; audit l.144, l.551.
- **État actuel** : « interdite dès qu'une facture autre qu'un acompte non réglé existe ; acompte non réglé annulé avec le BC ; situation / encaissement l'interdisent ».
- **Autorité** : décision de Rémy du 2026-10-13 (`42303cb1` §1-2 ; confirmations 06:57 / 07:29 / 08:08, messages saisis [NV]). Règle : ≥ 1 facture rattachée (tout type, tout état) interdit l'annulation ; acompte prévu sans facture ne bloque pas ; avoir total ne rétablit pas le droit.
- **Correction proposée** : `D1_regle_annulation_stricte_BC.diff` (CDC l.512 réécrit, l.543 supprimée ; INV-44 réécrit + ligne de journal ; métier l.248 et l.801). D-05 : texte dans `D4_fiche_report_V3.14.md` (le modèle V3.12 ne se modifie pas en place). E-07 : **ne pas réécrire**, annoter « révisé par E-xx ». Audit l.144 / l.551 : ne pas toucher.
- **Traçabilité** : D-05 (révisée), INV-44, E-07, TR-103 (proposé), C-19 + nouveaux cas, ligne de journal 2026-10-13.
- **Dépendances** : numéro d'erratum à arbitrer (point de décision n°2 du rapport A), car le CDC est gelé et la règle d'usage de l'errata (l.47) l'exige ; M-02, M-04, M-06 ; migration 009a ; rang (M-17).
- **Validation requise** : **oui** pour l'application dans `docs/` (autorisation de modifier + numéro d'erratum). Le contenu de la règle est déjà décidé.

## M-02 — Annulation du BC : « service seul » contre « service + trigger SQL »
- **Références** : modèle V3.12 l.332, l.356 (« Annulation du BC (INV-44) \| — \| oui \| — »), l.640 ; `004_bons_commande.sql` l.39-40 ; `invariants.md` l.78 (garde « SVC, test ») ; conventions l.88.
- **État actuel** : la règle reste « dans le service ».
- **Autorité** : décision de Rémy `42303cb1` §2 n°3 (INV-44 partagé entre service et trigger SQL).
- **Correction proposée** : garde INV-44 → « TRG (TR-103), SVC, test » (inclus dans D1) ; l.332, l.356, l.640 du modèle → report dans V3.14 (`D4`). Le commentaire de 004 est **livré, non modifiable** : le noter comme obsolète dans la fiche, sans toucher au fichier.
- **Traçabilité** : INV-44, TR-103, conventions l.88 (désormais respectée : le trigger ne contredit plus une attribution exclusive au service).
- **Dépendances** : M-01, M-10 (TR-103 hors registre).
- **Validation requise** : **oui** (même autorisation que M-01).

## M-03 — Propositions `MAJ__*` portant la règle inverse
- **Références** : `MAJ__cdc-errata-v6.md` l.22 (E-15) ; `MAJ__modèle-données…v3.13.md` l.1154 (D-05 « remplacée »), l.1195 (D-46), l.1030 (C-19 obsolète), cas C-36 (l.1047) ; `MAJ__invariants.md` l.76 ; `MAJ__cdc-fonctionnel…` l.521 ; `CADRAGE__005_depenses.md` / `MAJ__CADRAGE__005_depenses.md` (R27, C-E) ; `MAJ__audit-fonctionnel` l.551.
- **État actuel** : « annulation sans condition de facturation ».
- **Autorité** : décision du 13/10 (M-01). V3.13 non promue.
- **Correction proposée** : **aucune dans les MAJ** (propositions en voie d'archivage). Pour V3.14 : ne pas reprendre E-15 (clause d'annulation), D-46 (clause « sans condition »), C-36. Marquer les `MAJ` comme « règle d'annulation dépassée par la décision du 13/10 » dans l'index d'archive.
- **Traçabilité** : conserver les MAJ comme historique de la proposition abandonnée.
- **Dépendances** : M-05 (la clause « devis non annulés automatiquement » de E-15/D-46 est une question de cascade, à ne pas jeter avec le reste).
- **Validation requise** : **non** pour le constat ; **oui** pour toute reprise ou rejet formel de E-15 dans V3.14.

## M-04 — Import d'un « BC historique annulé »
- **Références** : modèle V3.12 l.366, l.717 ; `invariants.md` l.190 (INV-169), journal l.251.
- **État actuel** : le parcours d'import reconstruit un BC annulé en y insérant ses factures puis en l'annulant.
- **Autorité** : décision `42303cb1` §2 n°6 : pas d'import de BC annulés ; règle documentée + importateur strict, sans trigger redondant.
- **Correction proposée** : supprimer les incises, ou remplacer par « Aucun BC annulé n'est importé » (texte exact à arrêter à la construction de V3.14). Pas de diff : dépend de la forme choisie (alternative « conserver pour un BC annulé **sans facture** » non écartée par les sources).
- **Traçabilité** : INV-169 (journal), C-29, CK-13.
- **Dépendances** : M-01 ; importateur **[NV]**.
- **Validation requise** : **oui** (suppression ou restriction).

## M-05 — Cascade d'annulation BC → devis (SÉPARÉ, NON TRANCHÉ)
- **Références** : CDC l.540-541 ; `invariants.md` l.79 (INV-45), l.190 (INV-169) ; modèle V3.12 l.340, 351, 366, 717, 818 (C-28), 886 (CK-13), D-36 ; `005b_bc_multi_devis.sql` l.456-457 ; `MAJ` E-15 / D-46 ; décision `bfc171c3`.
- **État actuel** : texte officiel = cascade ; SQL livré, tests et propositions = pas de cascade.
- **Autorité** : **indéterminée** — le texte officiel dit cascade, la décision de Rémy (`bfc171c3`) dit non, et aucune ligne de `docs/` ne reflète cette décision.
- **Correction proposée** : **aucune** dans ce lot. Dossier d'arbitrage : `F_DOSSIER_ARBITRAGE_CASCADE_BC_DEVIS.md`.
- **Traçabilité** : INV-45, INV-169, D-36, CK-13, C-28, TR-18, INV-175.
- **Dépendances** : tests 005b/005c (alignés sur « pas de cascade »), service **[NV]**.
- **Validation requise** : **oui** (arbitrage métier).

## M-06 — Annulation / immutabilité des factures (flux « acompte annulé automatiquement »)
- **Références** : CDC l.435, 441, 514, 518 ; E-01 (errata l.8) ; INV-35, INV-61 ; TR-24 ; modèle l.315, 574, 617, 791 (C-01), 834 (T-08) ; métier l.272, l.800 ; `006_facturation.sql` l.24-27, 274-300 (`tr_20`, `tr_21`).
- **État actuel** : docs : une facture peut être annulée (`cancelled_at`), un acompte non réglé est annulé automatiquement à la modification du devis/BC. SQL livré : facture immuable dès l'INSERT, sans `cancelled_at`, sans `statut`.
- **Autorité** : docs/ (CDC, INV) pour le flux ; le SQL 006 suit la V3.13 (non validée), où ce flux est supprimé (E-14 dans les MAJ).
- **Correction proposée** : aucune dans ce lot. Interaction avec la règle stricte : si ce flux existe, un acompte annulé automatiquement reste une facture rattachée et **bloque** l'annulation du BC (« quel que soit l'état ») ; s'il n'existe pas, la précision « quel que soit l'état » est sans effet SQL.
- **Traçabilité** : E-01, INV-35, INV-61, TR-24, C-01, T-08.
- **Dépendances** : M-01 (formulation « tout état »), M-13.
- **Validation requise** : **oui** (maintenir le flux ou entériner 006).

## M-07 — Statut de la V3.12
- **Références** : modèle V3.12 l.5 (« validée après intégration de la migration 004 ») ; `docs/README.md` l.23 et l.37 ; `invariants.md` l.3.
- **État actuel** : trois documents disent « en relecture / non validée » ; le modèle dit « validée ».
- **Autorité** : décision `a835c585` (V3.12 = dernière version validée). Date de validation **[NV]** (aucune source accessible).
- **Correction proposée** : `D3_statut_V3.12_libelle_a_confirmer.diff` (libellé sans date).
- **Traçabilité** : mention de la V3.13 comme proposition non source de vérité (README).
- **Dépendances** : `fichiers-a-relire/README.md` (M-20).
- **Validation requise** : **oui** (libellé et éventuelle date).

## M-08 — Références de version périmées
- **Références** : métier l.7 (V3.11), l.35 et l.788 et l.823 (V3.10), l.824 (invariants v3) ; errata l.4 (`docs/decisions/` et V3.7) ; CDC l.10 (V3.7) ; audit l.3, l.25 (V3.9, invariants v4).
- **État actuel** : versions figées d'anciens états ; le modèle courant est V3.12, les invariants en version 6.
- **Autorité** : `docs/README.md` (version courante) ; chemin réel `docs/décisions/`.
- **Correction proposée** : `D2_corrections_certaines_sans_effet_metier.diff` : métier → renvoi à `docs/README.md` (pas de nouveau numéro figé) ; errata l.4 → `docs/décisions/`. **Laissés intacts** : modèle V3.12 l.1047 (« chemin d'origine `docs/decisions/` », mention historique) ; CDC l.10 (entrée d'historique datée, exacte à son époque) ; audit (historique, hors hiérarchie).
- **Traçabilité** : aucune décision modifiée.
- **Dépendances** : aucune.
- **Validation requise** : **non** pour la forme (correction de référence) ; autorisation d'écrire dans `docs/` requise.

## M-09 — Date de création du BC et relation « future »
- **Références** : métier l.224 (« date de création (= date d'acceptation) ») contre métier l.226, `invariants.md` l.87 (INV-176), modèle D-37 l.930 ; métier l.182 (« relation future `bons_commande.devis_id` »).
- **État actuel** : contradiction interne du métier ; `devis_id` existe depuis 004.
- **Autorité** : INV-176 / D-37 (validée 2026-10-01).
- **Correction proposée** : D2 (l.224 → « distincte de la date d'acceptation : INV-176 » ; l.182 → « la relation `bons_commande.devis_id` »).
- **Traçabilité** : INV-176, D-37.
- **Dépendances** : M-13 (la relation `devis_id` disparaît avec 005b : ne pas figer la mention au-delà de V3.12).
- **Validation requise** : **non** (alignement sur règle validée).

## M-10 — Identifiants hors registres officiels
- **Références** : registres officiels (D-39, E-09, INV-178, TR-96) ; migrations 005 à 009 et tests (D-40 à D-61, E-10 à E-20, INV-179 à INV-203, TR-97 à TR-102, TR-103 proposé, TR-51) ; `MAJ…v3.13.md` l.782 (TR-99) / `006` l.483 (`tr_99_bc_devis_apres_solde`).
- **État actuel** : le SQL livré cite des numéros que le registre officiel ne définit pas ; TR-99 a deux triggers pour une seule ligne de registre ; TR-51 défini hors registre.
- **Autorité** : registres de `docs/` pour les numéros existants ; pour les autres, **aucune**.
- **Correction proposée** : aucun diff ; table de correspondance à intégrer dans V3.14 (fiche `D4`, §3) ; ne pas attribuer de nouveaux numéros avant arbitrage (E-10 est déjà pris par un autre contenu dans les MAJ).
- **Traçabilité** : chaque numéro à rattacher à sa source (message de Rémy, cadrage).
- **Dépendances** : M-12, M-17.
- **Validation requise** : **oui**.

## M-11 — Convention « un test `test_INV_xx` par invariant »
- **Références** : `invariants.md` l.9 ; conventions §7 ; tests (1 879 fonctions).
- **État actuel** : 49 INV sur 125 ont un test nommé `test_*INV_xx*`.
- **Autorité** : règle écrite (invariants l.9).
- **Correction proposée** : aucune ; choisir entre rattrapage des noms ou assouplissement de la règle.
- **Traçabilité** : registre des INV (colonne « Cas »).
- **Dépendances** : V3.14.
- **Validation requise** : **oui**.

## M-12 — En-têtes de migrations : modèle cité
- **Références** : 005, 005a, 005b, 005c, 006, 007, 008, 009 (« modèle de données SQLite V3.13 ») ; 003 (V3.10) contre modèle §17.1 (V3.11) ; conventions l.104 (l'en-tête cite la version du modèle).
- **État actuel** : 8 migrations citent un modèle non validé.
- **Autorité** : conventions l.104 ; les migrations livrées ne se modifient pas.
- **Correction proposée** : ne pas toucher aux migrations. Consigner dans V3.14 (§17.1) la correspondance migration → version(s) de modèle citée(s), avec la mention « V3.13 : proposition non validée » pour 005 à 009.
- **Traçabilité** : §17.1 du futur modèle.
- **Dépendances** : M-14.
- **Validation requise** : **oui**.

## M-13 — Structure « un BC par devis » contre BC multi-devis (005b)
- **Références** : modèle V3.12 (`UNIQUE devis_id` ; INV-175 l.86 ; D-36) ; métier (« un devis accepté produit un seul BC ») ; `005b_bc_multi_devis.sql` l.1-60 (`bc_devis`, `bons_commande` sans `devis_id`).
- **État actuel** : le schéma livré diffère du modèle validé.
- **Autorité** : V3.12 pour le texte officiel ; le SQL réalise les décisions Q17/Q-A à Q-D (cadrage 005b), dont le statut de validation n'est pas inscrit dans `docs/`.
- **Correction proposée** : aucune ; arbitrage de reprise sélective pour V3.14.
- **Traçabilité** : Q17, `CADRAGE__005b`, PT-6.
- **Dépendances** : M-05, M-09, M-12.
- **Validation requise** : **oui**.

## M-14 — Chaîne ordonnée, rang et noms de migrations absents de `docs/`
- **Références** : modèle §17.1 l.981-990 (001 à 004 seulement) ; conventions §4 l.47-64, l.94-98, l.139-145 (001-003) ; noms `005a/b/c` (conventions l.83, l.103).
- **État actuel** : la notion de rang / `user_version` / corrective n'existe que dans `MAJ__conventions-techniques-v6.md`.
- **Autorité** : D-55 et D-56 (validées dans leur périmètre, selon Rémy) — mais absentes de `docs/`.
- **Correction proposée** : reporter dans V3.14 et dans une version des conventions ; pas de diff avant arbitrage.
- **Traçabilité** : D-55, D-56, §5 de la MAJ conventions.
- **Dépendances** : M-10, M-12, M-17.
- **Validation requise** : **oui**.

## M-15 — `INSERT` et `PRAGMA` dans 005a / 005b
- **Références** : conventions l.105 et l.204 ; `005a_corrections_v313.sql`, `005b_bc_multi_devis.sql` (6 et 8 `INSERT`, `PRAGMA foreign_keys` hors fichier).
- **État actuel** : exception documentée dans les en-têtes, absente des conventions officielles.
- **Autorité** : conventions officielles (l.105, l.204) ; la MAJ conventions prévoit « Données dans une migration » et le protocole de reconstruction.
- **Correction proposée** : intégrer la règle d'exception à la prochaine version des conventions.
- **Traçabilité** : D-56 (chaîne, protocole).
- **Dépendances** : M-14.
- **Validation requise** : **oui**.

## M-16 — Incohérences internes du modèle V3.12
- **Références** : l.862 (T-29 « à écrire ») contre l.483 et l.973 (« intégré ») ; l.992 (« copies en relecture… non exécutés ») ; §13 sans 13.1 ; §17.1 (tableau coupé l.987).
- **Autorité** : état réel (tests committés : 28/18/68 pour 001-003 ; T-29 = `test_004_bons_commande.py`).
- **Correction proposée** : à faire **dans V3.14**, pas dans V3.12 (modèle validé, non modifiable en place). Liste dans `D4`.
- **Traçabilité** : journal du modèle.
- **Dépendances** : M-14.
- **Validation requise** : **non** pour les erreurs matérielles ; **oui** pour l.992 (formulation).

## M-17 — Rang 13 de 009a et références de 009a
- **Références** : proposition 009a (en-tête : « Rang 13 décidé le 2026-10-13 », « D-55 », « D-56 », TR-103) ; `591e4ede`, `130eb1a6`, `665451c0` §6 (rang « privilégié », conditionnel).
- **État actuel** : l'en-tête est plus affirmatif que la position de Rémy.
- **Autorité** : position de Rémy : privilégié, après contrôle des `user_version` **[NV]**.
- **Correction proposée** : adoucir l'en-tête (« rang 13 proposé, sous réserve… ») avant tout dépôt de 009a ; aucune édition ici.
- **Traçabilité** : D-55, D-56.
- **Dépendances** : M-14.
- **Validation requise** : **oui**.

## M-18 — 17 tests « BC annulé + facture »
- **Références** : `06_INVENTAIRE_17_TESTS.md` (2 INC, 1 CONF, 14 HL).
- **État actuel** : tests passent ; deux scénarios présentent comme acceptée la transition désormais interdite.
- **Autorité** : conventions §7 (un test ne doit pas devenir une seconde spécification contradictoire) ; règle stricte.
- **Correction proposée** : aucune modification de test dans cet audit ; adapter plus tard les fixtures (état fabriqué au rang 12 puis chaîne portée au rang 13).
- **Traçabilité** : INV-44, INV-188, D-56.
- **Dépendances** : M-01, M-17.
- **Validation requise** : **oui** (au moment de la tranche d'adaptation).

## M-19 — `docs/README.md` : documents non listés
- **Références** : `docs/README.md` (structure l.7-12, liste l.14-30) ; `charte-graphique-batorya-v6.md` (v0.5 « En construction ») ; `conception/references-ui/` (26 fichiers).
- **État actuel** : ni la charte ni les références UI ne sont mentionnées.
- **Autorité** : `docs/README.md`.
- **Correction proposée** : ajouter une ligne « charte graphique — en construction, hors périmètre de référence » et « references-ui — matériel de référence visuel, non normatif » (formulation à confirmer). Pas de diff (dépend de M-07).
- **Traçabilité** : aucune décision modifiée.
- **Dépendances** : M-07, M-20.
- **Validation requise** : **oui** (statut de la charte).

## M-20 — Doublons et anciennes versions dans `fichiers-a-relire/`
- **Références** : voir `C_PLAN_ASSAINISSEMENT.md`.
- **État actuel** : README en copie, paires v1/v2, trois familles de diffs partiellement appliqués.
- **Autorité** : liens entrants vérifiés (C).
- **Correction proposée** : archivage avec index et pointeurs, jamais de suppression (C).
- **Traçabilité** : index d'archive (modèle dans C).
- **Dépendances** : M-07.
- **Validation requise** : **oui** (arbitrage de Rémy, car le dossier est son espace de relecture).

## M-21 — Coquilles de mise en forme du CDC
- **Références** : CDC l.486 et l.843 (puces fusionnées « ;* »).
- **État actuel** : deux listes écrasées sur une ligne.
- **Autorité** : CDC (texte identique, seule la mise en forme change).
- **Correction proposée** : D2 (retour à la ligne).
- **Traçabilité** : aucune.
- **Dépendances** : aucune.
- **Validation requise** : **non** (aucun contenu changé) ; le CDC étant gelé, accord d'écriture tout de même requis.
