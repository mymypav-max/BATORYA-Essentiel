# A — Rapport global d'audit de cohérence documentaire (BATORYA Essentiel V6)

> **Zone non officielle.** Audit en lecture seule du dépôt `mymypav-max/BATORYA-Essentiel`, branche `main`, commit `d1d8bb9dd517c1fd457e756d10a4411359e4ebbf` (2026-10-13 13:32). Rédigé le 2026-10-15.
> Aucun fichier officiel modifié, aucun fichier supprimé, aucun commit, aucun push, aucune migration intégrée, aucune version validée.
> Légende des niveaux : **[F]** fait vérifié dans le dépôt (chemin + ligne) · **[D]** déduction · **[NV]** non vérifiable avec les sources accessibles.
> Les propositions (`MAJ__*`, `CADRAGE__*`, diffs) ne sont **jamais** citées comme décisions validées.

## 1. Périmètre et méthode

### 1.1 Fichiers examinés
| Zone | Fichiers suivis par Git | Examen |
|---|---|---|
| `docs/` (référence officielle) | 36 (9 `.md`, 26 fichiers de `conception/references-ui/`, 1 `.gitkeep`) | les 9 `.md` lus en entier (4 867 lignes) |
| `fichiers-a-relire/` (non officiel) | 58 (48 hors `preuves_009_pv/`) | inventaire complet, liens entrants calculés, 11 `.diff` testés avec `git apply --check` (sens direct et inverse) ; contenus lus sur les fichiers pertinents à l'audit (`MAJ__*`, `PLAN_MAJ_DOC__009a_*`, `CADRAGE__00x` ciblés, `README.md`) |
| `src-tauri/migrations/` | 13 (dont `machine/001`) | en-têtes, versions de modèle citées, triggers, `INSERT`/`PRAGMA` ; 009a n'existe **pas** dans le dépôt |
| `src-tauri/tests/` | 13 modules (1 879 `def test_*`) | noms de tests rapprochés des INV ; 17 tests « BC annulé + facture » inventoriés un par un |
| Dossier non suivi `reprise-autonome-v3.14-tranche-010/` | 8 documents + `annexes/` | lu ; **ne fait pas partie du dépôt** (non suivi) |

### 1.2 Exclusions
- **BATORYA Entreprise** : hors périmètre (consigne).
- **Contenu fonctionnel de la charte graphique et des 26 références UI** : cycle de vie et liens examinés, contenu graphique non audité.
- **Non accessibles** : services applicatifs, importeur, runner de migrations (Rust), bases de développement et leur `PRAGMA user_version`, PR GitHub, historique des échanges, messages saisis du 13/10 06:10 → 08:08. Tout ce qui en dépend est marqué **[NV]**.
- **`preuves_009_pv/`** (18 fichiers) : inventorié et classé, non réaudité ligne à ligne (preuves de la campagne de mutation 009, déjà contrôlées par leurs manifestes SHA-256).

### 1.3 Méthode (pas de conclusion sur recherche textuelle seule)
1. Lecture intégrale des 9 documents de `docs/`, hiérarchie des conventions §2 (l.18-24) appliquée.
2. Registres D/E/INV/TR/C/CK/T extraits par script, rapprochés des citations dans les documents, migrations et tests (scripts d'audit conservés hors dépôt : `ids.py`, `ids2.py`, `mig.py`, `refs.py`).
3. Chaque passage sur l'annulation du BC et la cascade relu **dans son contexte** (lignes encadrantes), puis rapproché des migrations livrées 004 à 009 et des tests.
4. Liens entrants de chaque fichier de `fichiers-a-relire/` et de `references-ui/` calculés par recherche du nom de fichier dans tout le dépôt ; les faux positifs (nom générique `README.md`, sous-chaîne) sont signalés.
5. Les diffs candidats (dossier `D_propositions/`) sont vérifiés avec `git apply --check`, seuls puis appliqués à la suite dans une copie jetable.

## 2. État documentaire réel

**Hiérarchie [F]** (`docs/conception/conventions-techniques-v6.md` §2, l.18-24) : CDC > modèle SQLite V3.12 > invariants > modèle métier > errata (traçabilité historique). Un écart au CDC n'est valide que s'il figure « Validé » dans les errata (`cdc-errata-v6.md` l.47).

**Registres officiels [F]** : D-01 à D-39, E-01 à E-09, T-01 à T-29, C-01 à C-29, CK-01 à CK-13 sans trou ; INV jusqu'à INV-178 ; TR jusqu'à TR-96 ; tous les TR cités existent.

**Décisions de Rémy prises en compte [F, preuve dans `reprise-autonome…/annexes/messages_utilisateur/`]** : V3.12 = dernière version validée ; V3.13 non promue ; V3.14 reconstruite depuis V3.12 avec reprise sélective ; fichiers `MAJ__*` = propositions ; règle stricte d'annulation du BC ; pas de cascade BC → devis (`bfc171c3`) ; pas d'import de BC annulés ; INV-44 partagé entre service et trigger (`42303cb1`).

## 3. Cas prioritaire — annulation d'un BC facturé

### 3.1 Règle cible (décision de Rémy, 2026-10-13)
Un BC ne peut pas devenir `annule` dès qu'**au moins une facture** lui est rattachée, quel que soit son type (acompte, situation, solde, avoir) et son état. Un acompte **prévu** sans facture émise ne bloque pas. 009a ne modifie pas rétroactivement les BC déjà annulés.
Source primaire : `42303cb1` §1-2 (conservé) ; confirmations du 13/10 06:57, 07:29, 08:08 (**messages saisis, source primaire non conservée [NV]**).

### 3.2 Passages officiels à harmoniser (lignes vérifiées sur `d1d8bb9`)
| # | Fichier | Ligne | Texte actuel (extrait) | Nature |
|---|---|---|---|---|
| 1 | `docs/conception/modèle-données-sqlite-v6-v3.12.md` | 898 (D-05) | « interdite dès qu'une facture autre qu'un acompte non réglé existe » | contradiction avec la règle cible |
| 2 | `docs/conception/invariants.md` | 78 (INV-44) | « autorisée avec acompte non réglé, annulé dans la même transaction ; toute autre facture interdit » | contradiction |
| 3 | `docs/décisions/cdc-errata-v6.md` | 14 (E-07) | « interdit l'annulation directe dès qu'une facture autre qu'un acompte non réglé existe » | **historique à conserver** (registre de traçabilité) ; à annoter, pas à réécrire |
| 4 | `docs/specifications/cdc-fonctionnel-architectural-v6.md` | 512 | « Annulation directe interdite dès qu'une facture autre qu'un acompte non réglé existe… » | contradiction |
| 5 | idem | 543 | « la facture d'acompte annulée reste conservée lorsqu'elle existe » | devient sans objet (un BC annulable n'a aucune facture) |
| 6 | idem | 514, 516, 518, 522, 530, 1320 | acompte non réglé annulé avec le BC ; situation émise ; encaissement | **compatibles mais redondants** avec la règle cible (l.516/522/530/1320 sont des cas particuliers de « toute facture »). l.514 vise la modification du devis (flux E-01), voir M-06 |
| 7 | `docs/conception/modèle-métier-V6.md` | 248 | « interdite… dès qu'une facture autre qu'un acompte non réglé existe… Un acompte non réglé est annulé avec le BC » | contradiction |
| 8 | idem | 801 (règle 6) | « dont la facturation dépasse un acompte non réglé… » | contradiction |
| 9 | `docs/audit/audit-fonctionnel-v5.16-v6.md` | 144, 551 | ancienne règle (E-07) | document d'analyse historique, `l.27` : « ces derniers font foi » ; **ne pas corriger**, annoter |
| 10 | modèle V3.12 | 332, 356, 640 | l'annulation (INV-44) « reste dans le service » | contradiction avec la décision « service + trigger » (et avec l'en-tête de 004, l.39-40) |
| 11 | modèle V3.12 | 809 (C-19) | « Situation annulée, puis BC : annulation directe demandée → refusée » | à compléter par les cas chiffrés de la règle cible |
| 12 | modèle V3.12 / invariants | 366, 717 / 190 (INV-169), journal l.251 | « un BC historique annulé s'importe par les étapes normales » | contradiction avec « pas d'import de BC annulés » (voir M-04) |
| 13 | `docs/conception/conventions-techniques-v6.md` | 88 | une migration ne doit pas contredire « les responsabilités explicitement attribuées aux services » | **satisfaite** une fois modèle/INV-44 corrigés (service + trigger) |

### 3.3 Propositions `MAJ__*` : règle **inverse**, à ne pas reprendre
`MAJ__cdc-errata-v6.md` E-15 (l.22), `MAJ__modèle-données-sqlite-v6-v3.13.md` D-46 (l.1195), D-05 « remplacée » (l.1154), C-19 obsolète (l.1030), `MAJ__invariants.md` INV-44 (l.76), `MAJ__cdc-fonctionnel-architectural-v6.md` encadré E-15 (l.521), `CADRAGE__005_depenses.md` / `MAJ__CADRAGE__005_depenses.md` (R27, C-E « annulation avec solde actif possible, E-15 »), `MAJ__audit-fonctionnel-v5.16-v6.md` l.551 (« Dépassé — E-15 ») : tous énoncent « annulation **sans condition de facturation** ». C'est le contraire de la décision du 13/10.
**Conséquence [D]** : la reconstruction V3.14 ne doit reprendre ni E-15 (clause d'annulation) ni D-46 (clause « sans condition de facturation ») ni le cas chiffré C-36. Leur clause « devis non annulés automatiquement » relève de la cascade (§4) et doit être arbitrée séparément.

### 3.4 Migrations et tests [F]
- **Aucun trigger** livré (004 à 009) ne refuse la transition `annule` pour cause de facture ; 009a n'est pas dans le dépôt (proposition `PROPOSITION_DIFF__009a_V2…diff` : `git apply --check` **réussit**, donc non appliquée).
- Les **17 tests** « BC annulé + facture » (`06_INVENTAIRE_17_TESTS.md`) : 2 incompatibles dans leur scénario (`test_C_36_…`, `test_T50_H_un_BC_annule_apres_le_solde_conserve_ses_garanties`), 1 conforme, 14 « historique légitime ». Avec 009a ajoutée dans une copie hors dépôt, les 13 modules passent (1 916 tests, 0 échec) parce que chaque module limite la chaîne à son propre rang.
- Les factures sont **immuables** dès leur INSERT en 006 (`tr_20`, `tr_21`, pas de `cancelled_at`, pas de `statut` ; l.24-27, 274-300). Il n'existe donc pas de « facture annulée » ni d'« acompte annulé automatiquement » en SQL livré ; l'exception « acompte non réglé » de D-05/INV-44 n'est pas exécutable (voir M-06).
- 009a : en-tête « Rang 13 **décidé** le 2026-10-13 » ; position de Rémy = rang 13 « **privilégié**, sous réserve du contrôle des `user_version` des bases de développement » **[NV]** (voir M-17).

## 4. Cascade BC → devis — traitée à part, **non tranchée**
Dossier dédié : `F_DOSSIER_ARBITRAGE_CASCADE_BC_DEVIS.md`. Résumé :
- **Officiel (cascade)** : CDC l.540-541 ; INV-45 l.79 (« devis `annule`, BC d'abord puis devis… TR-18 ») ; INV-169 l.190 ; modèle V3.12 l.340, 351, 366, 717, 818 (C-28), 886 (CK-13 « BC annulé sans devis annulé »), D-36.
- **Livré et propositions (pas de cascade)** : 005b l.456-457 (« Aucune cascade BC → devis (INV-188) »), tests 005b/005c, `MAJ` E-15/D-46, décision `bfc171c3`.
- **Compatibles avec les deux lectures [F]** : TR-18 et INV-175 (ils ne conditionnent que « BC `annule` »). Le trigger 009a ne lit pas `devis`.
- **Conclusion** : contradiction réelle, préexistante, indépendante de 009a ; aucune ligne de la matrice B ne la tranche.

## 5. Autres constats (classés par famille)

### 5.1 Contradictions et règles décrites différemment
| ID | Constat | Preuve |
|---|---|---|
| R-1 | **Statut de la V3.12** : « validée après intégration de la migration 004 » (modèle l.5) ; « en relecture (non validée) » (`docs/README.md` l.23 et l.37) ; « en relecture, non validé » (`invariants.md` l.3). Décision de Rémy : V3.12 = dernière version validée. Sa **date de validation n'est pas établie [NV]**. | cf. M-07 |
| R-2 | **Date du BC** : métier l.224 « date de création (= date d'acceptation) » contredit métier l.226 (« distincte ») et INV-176 / D-37 (« les deux peuvent différer »). | M-09 |
| R-3 | **Un BC par devis** : modèle V3.12 (`UNIQUE devis_id`, INV-175, D-36), métier (« un devis accepté produit un seul BC ») contre 005b livrée (`bc_devis`, BC ← N devis, `bons_commande` sans `devis_id`). Cette structure vient de la V3.13 (Q17), **non validée**. | M-13 |
| R-4 | **Annulation d'une facture** : CDC l.441, E-01, INV-35, INV-61, TR-24 prévoient annulation de facture et acompte annulé automatiquement ; 006 livrée rend la facture immuable et sans `cancelled_at`. | M-06 |
| R-5 | **Modèle métier** : l.182 « relation **future** `bons_commande.devis_id` » alors que 004 la livre ; l.7 « aligné sur V3.11 » alors que l.35, 788, 823 disent V3.10 et l.824 « invariants version 3 » (registre en version 6). | M-08, M-09 |
| R-6 | **Modèle V3.12 internes** : T-29 « à écrire » (l.862) contre « intégré » (l.483, 973) ; l.992 « copies en relecture… tests du dépôt non exécutés » alors que les tests 001-003 sont committés (28/18/68) ; §13 sans titre 13.1 ; tableau §17.1 coupé par une ligne vide (l.987). | M-16 |

### 5.2 Décisions non propagées / références à des versions inexistantes ou non validées
- **Migrations 005, 005a, 005b, 005c, 006, 007, 008, 009 : toutes citent « modèle V3.13 »** (non validée, non officielle) et des sources non officielles (`CADRAGE__00x`, PT-x, D-44/48/50/54/55/56). `machine/001`, 001, 002, 003 et 004 citent respectivement V3.8, V3.9, V3.10, V3.10 et V3.12 ; **003 cite V3.10 alors que le modèle §17.1 attribue 003 à V3.11** **[F, `mig.py`]**.
- **D-55, D-56** (validées dans leur périmètre selon Rémy) et la **chaîne ordonnée / rang / correctives** n'existent dans **aucun** fichier de `docs/` (0 occurrence de « rang », « chaîne ordonnée », « corrective NNNx », « reconstruction de table »). Les migrations 005a/b/c, 009a s'y réfèrent.
- Le **modèle §17.1** (l.981-990) ne suit que `machine/001` et `metier/001` à `004`. Les **conventions §4** (l.47-64) et l.94-98, 139-145 ne listent que 001-003.
- **Noms** `005a_corrections_v313`, `005b_…`, `005c_…` : le suffixe lettre et la mention de version ne sont pas définis par les conventions officielles (l.103 : `NNN_<objet>.sql`) ; un nom ne se change jamais (l.83) → dette de nommage définitive à documenter, non à corriger.
- `docs/README.md` ne cite ni `charte-graphique-batorya-v6.md` (v0.5 « En construction ») ni `references-ui/`.
- `cdc-errata-v6.md` l.4 écrit `docs/decisions/` ; le dossier réel est `docs/décisions/`.
- CDC l.10 (historique V6.1) : « modèle SQLite V3.7 » ; `audit-fonctionnel` l.3 et l.25 : V3.9 / invariants v4 (historiques, voir hiérarchie).

### 5.3 Identifiants non répertoriés ou incohérents
- **Hors registres officiels, utilisés par des migrations ou tests** : D-40 à D-61 ; E-10 à E-20 ; INV-179 à INV-203 (tests nommés pour INV 179, 180-184, 186-190, 193, 196-201 alors que le registre officiel s'arrête à INV-178) ; TR-97 à TR-102 (005 : TR-101, TR-102 ; 005a : TR-97/98/100 ; 005b : TR-99), **TR-103** (proposé par 009a) ; **TR-51** défini seulement dans `CADRAGE__008_garanties.md` et migration 008.
- **TR-99** : la ligne `MAJ` (l.782) liste INSERT/UPDATE/DELETE de `bc_devis` ; 006 ajoute `tr_99_bc_devis_apres_solde` (l.483) sans ligne correspondante **[F]**.
- **Convention de test** (`invariants.md` l.9 : « un test du même nom `test_INV_xx` ») : 49 des 125 INV du registre ont un test nommé `test_*INV_xx*` ; les autres sont couverts par des noms de scénario **[F, script]**. Écart entre règle écrite et pratique (arbitrage, M-11).
- **Citations** : tout INV du registre est cité dans le modèle sauf INV-41, 47, 59 (après expansion des plages). INV-132, 155-160, 162 sont cités comme règles retirées (cohérent avec E-09).

### 5.4 Écarts docs / SQL / tests (hors annulation)
| ID | Constat | Preuve |
|---|---|---|
| S-1 | 005a et 005b contiennent des `INSERT` (reconstructions de table et tables de garde : 6 et 8 instructions) et citent `PRAGMA foreign_keys` OFF/ON (exécutés **hors fichier**) ; les conventions officielles disent « une migration n'insère aucune ligne » (l.105) et « aucun PRAGMA » (l.204). Les en-têtes expliquent l'exception, mais **la règle officielle n'a pas d'exception écrite**. | M-15 |
| S-2 | Chaque module de test construit la chaîne **jusqu'à son propre rang** (`sorted(MIGRATIONS.glob("*.sql"))[:9]` dans `test_006`) : aucun test ne couvre la chaîne finale 001 → 009 (+009a) en une seule base. | `06_INVENTAIRE_17_TESTS.md` §2 |
| S-3 | Campagne de mutation (conventions §7.1 : 0 survivant non qualifié par tranche) : rapports présents pour 007, 008, 009 ; pas pour 005, 005a/b/c, 006. | `fichiers-a-relire/RAPPORT_MUTATION__*` |
| S-4 | Tranche 010 : `planning_evenements` est spécifiée dans V3.12 (l.421-423) ; **ni SQL, ni test, ni cadrage** dans le dépôt (T-52 prévu, non créé). | `reprise-autonome…/01` §3 |

### 5.5 Redondances (point 7)
- La règle d'annulation est répétée dans le CDC (§17 : l.512, 516, 522, 530, 1320), INV-44, D-05, E-07, métier l.248 et l.801, audit l.144 et l.551, modèle l.332/356/640/809. Après harmonisation, **un seul énoncé normatif** (INV-44 + D-05) suffit ; les autres peuvent renvoyer à INV-44. Aucune suppression proposée sans validation.
- `docs/README.md` ↔ `fichiers-a-relire/README.md` ↔ `MAJ__README-docs.md` : voir C (le second est une copie du troisième, sous un nom trompeur).

## 6. Cycle de vie des documents — synthèse (détail et contrôle des liens : `C_PLAN_ASSAINISSEMENT.md`)
| Statut | Effectif |
|---|---|
| Référence officielle active | 9 `.md` de `docs/` |
| Historique à conserver | `CADRAGE__005b/006/007/008/009` (cités par les en-têtes de migrations et tests), `RAPPORT_MUTATION__007/008/009`, `RAPPORT__COMPATIBILITE_001_004_AVANT_005`, `RAPPORT__MISE_A_JOUR_V3.13`, `preuves_009_pv/` |
| Proposition non validée | 10 `MAJ__*`, `PROPOSITION_DIFF__009a_V2…diff`, `DIFF_DOC__010_historique_planification.diff` (applicable, non appliqué), `PLAN_MAJ_DOC__009a_…_V3`, `RAPPORT_FINAL__009a…` |
| Document temporaire de travail | famille « 009 contrôle NUL » (`BILAN_VALIDATION`, `COMPLEMENT_*`, `PLAN_REMEDIATION`, `SYNTHESE`, `PROPOSITION_*009_pv*`, `DIFF_FINAL__*`, `DIFF_DOC__maj_apres_rejeu…`, `DIFF_DOC__rapport_bilan…`, `outils_mutation_009.py`, `sorties_brutes_009_nul.py`) |
| Doublon | `fichiers-a-relire/README.md` (copie de `MAJ__README-docs.md`, 1 ligne d'écart), `AUDIT__REGLE_CONSERVATION…` (version antérieure de `MAJ__AUDIT…`, 11 lignes d'écart) |
| Version antérieure à archiver (après arbitrage) | `CADRAGE__005_depenses.md` (révisé par `MAJ__CADRAGE__005`), `PLAN_MAJ_DOC__009a_…` (V2, remplacé par V3 qui le déclare « conservé »), `Diff_doc_010_correctif_redactionnel.diff` (v1, ni applicable ni inversible), `Diff_doc_010_tracabilite_diff_lot1.diff` (v1) |
| Statut indéterminé (arbitrage) | `DIFF_DOC__010_corrections_documentaires.diff`, `DIFF_FINAL__009_pv.sql.diff` (patch corrompu à la ligne 48), `DIFF_DOC__maj_apres_rejeu_complet_009.diff`, 24 fichiers de `references-ui/` sans lien entrant |
| Suppression justifiée | **aucune** à ce stade (voir C : tout est conservé ou archivé avec pointeur) |

## 7. Points nécessitant une décision humaine
1. **Cascade BC → devis** : cascade officielle ou absence de cascade ? (dossier F)
2. **Support de la règle stricte** : numéro d'erratum (E-10 est déjà pris dans les `MAJ` par un autre contenu) et format d'annotation d'une décision révisée (D-05, E-07). Le CDC étant gelé, la modification de §17 exige un erratum « Validé ».
3. **Statut de la V3.12** : libellé à retenir dans `README` et `invariants.md` (D3), et date de validation si elle doit être inscrite.
4. **Reprise sélective pour V3.14** : parmi les apports de la V3.13 déjà exécutés par les migrations 005 à 009 (BC multi-devis, dépenses, facturation, règlements, garanties, PV), lesquels sont des décisions validées ? Sans réponse, V3.14 ne peut pas décrire le schéma réellement livré.
5. **Facture annulée** : maintenir le flux CDC/INV-35/INV-61/TR-24 (annulation de facture, acompte annulé automatiquement) ou entériner 006 (factures immuables, correction par avoir) ? Conséquence sur « quel que soit l'état de la facture ».
6. **Rang 13 de 009a** : après contrôle des `user_version` des bases de développement **[NV]**.
7. **IDs hors registre** : fusion dans le registre officiel lors de V3.14 (D-40+, INV-179+, TR-97+), et traitement de TR-51.
8. **Convention `test_INV_xx`** : l'appliquer rétroactivement ou l'assouplir dans les conventions.
9. **Anciens BC annulés facturés** (avant 009a) : conserver INV-188 / D-56 / 005c comme règles d'état historique, et ajouter ou non un contrôle diagnostique (type CK).
10. **Références UI** : conserver telles quelles avec un index, ou archiver les prototypes non retenus.

## 8. Résultat de l'audit
**Le corpus n'est pas cohérent à ce jour.** Les constats ci-dessus sont des contradictions vérifiées dans leur contexte, pas des détections textuelles. Les registres officiels sont cohérents entre eux, mais la chaîne SQL livrée s'appuie sur une V3.13 non validée dont une partie n'a aucun support dans `docs/`.
