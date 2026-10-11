# Preuves de la migration 009 (PV) — dossier minimal, mode de rejeu et statut des vérifications

Objet : rendre **auditables et rejouables depuis un clone** les preuves de `RAPPORT_MUTATION__009_pv.md` et `BILAN_VALIDATION__009_pv__controle_nul.md`.
Ce dossier ne contient ni migration, ni test, ni document officiel ; il n'est pas destiné à `src-tauri/`. Il ne contient **que** ce qui sert à comprendre, rejouer ou comparer (§2, §6).

**Statut d'ensemble (daté).** Au commit `main` = `5ebf202` (2026-10-10 21:06), `009_pv.sql` et `test_009_pv.py` corrigés sont sur `main` (empreintes en §1) mais le dossier de preuves n'y est que partiel (13 fichiers, dont 2 mal rangés ; `mut009b.py`, `genmut009b.py`, `preuves_equivalence_009.py` — publié sous le nom `fichiers-a-relire/outils_mutation_009.py` — et les sorties de campagne manquent) : **ce clone brut de `main` ne permet pas de rejouer la campagne**. L'arborescence décrite ci-dessous est celle qui a été rejouée **en entier le 2026-10-10 (22:49–23:05, heure de Paris) depuis une copie contenant uniquement `main` 5ebf202 et les fichiers de ce dossier** (§4) : elle est donc reproductible depuis un clone propre *une fois publiée*. Ses empreintes sont dans `MANIFEST_SHA256.txt`.

## 1. Prérequis

- Python 3 (rejeu fait avec 3.11.15), bibliothèque standard seulement ; bash pour les scripts d'ensemble ; **gcc** seulement pour l'expérience à date décalée (§5). SQLite : celui de Python (rejeu fait avec **3.45.1**) ; 2 cœurs.
- `RACINE` = un clone du dépôt (dossier contenant `src-tauri/` et `fichiers-a-relire/`). Références exigées par les outils (sha256 complets) :
  - `src-tauri/migrations/metier/009_pv.sql` : `764a2d302969f471bad2e6770f57454eff7659ebd886e5c6aa6be14509d84cb3`
  - `src-tauri/tests/metier/test_009_pv.py` : `4d56721107285773f12920224c2f83ded43f7aeb74b96a8909ef57beaeb59f04`
  Sur une version plus ancienne de ces deux fichiers, les outils s'arrêtent ou échouent.
- Les scripts s'appellent **par leur chemin** et se retrouvent entre eux **par leur position relative** : ne pas renommer ni séparer `outils/preuves_equivalence/` (le rapprochement lit `preuves_equivalence_009.py` dans le même dossier) ni `outils/campagne_mutation/` (`genmut009b.py`, `classify009b.py`, `verifier_campagne_009.py` lisent `mut009b.py`).
- Aucun script n'écrit dans le dépôt : `mut009b.py` travaille dans des copies de `src-tauri/` sous le dossier de travail donné.

## 2. Contenu conservé (48 fichiers) et rôle de chacun

```
preuves_009_pv/
├── LISEZ-MOI__preuves_009_pv.md            ce fichier
├── MANIFEST_SHA256.txt                     empreintes de TOUS les fichiers de ce dossier sauf lui-même (vérification : outils/controles/verifier_manifestes_009.py)
├── MANIFEST_SHA256__fichiers_valides.txt   empreintes du SQL, des tests, des diffs, du rapport, du bilan (chemins depuis RACINE)
├── outils/
│   ├── rejouer_toutes_les_verifications_009.sh   COMMANDE UNIQUE : rejoue tout et classe chaque étape (§3)
│   ├── campagne_mutation/
│   │   ├── mut009b.py                      campagne complète (966 mutants générés → 797 distincts, exécutés) ; passes de diagnostic via MUT_EXCLUDE
│   │   ├── genmut009b.py                   régénère les mutants de mut009b.py (bibliothèque)
│   │   ├── classify009b.py                 classement par famille depuis des sorties enregistrées
│   │   ├── verifier_campagne_009.py        partition 797 = 770 + 3 + 24 ; rejeu ciblé facultatif
│   │   └── comparer_campagne_009.py        compare une campagne rejouée aux sorties de référence, sans rien masquer
│   ├── preuves_equivalence/
│   │   ├── preuves_equivalence_009.py      52 contrôles sur le SQL réel (S01–S24, K01–K14, témoins) ; porte le registre S/K
│   │   ├── rapprochement_survivants_registre.py   bijection survivants de la campagne ↔ registre S/K
│   │   └── epreuves_negatives_rapprochement.py    le rapprochement doit échouer dans 4 cas
│   └── controles/
│       ├── compte_sous_tests.py            268 tests / 940 sous-tests
│       ├── controle_integrite_009.py       integrity_check / foreign_key_check sur base construite 001→009
│       ├── verifier_manifestes_009.py      vérifie réellement les deux manifestes (empreintes + périmètre exact)
│       ├── passes_a_date_decalee_009.sh    expérience : rejoue les deux passes de diagnostic à une date UTC simulée (§5)
│       └── faketime_shim.c                 bibliothèque LD_PRELOAD (décalage d'horloge d'un processus) utilisée par le script précédent
└── sorties_brutes/
    ├── campagne_complete/                  RÉFÉRENCE HISTORIQUE (5 fichiers) : tueurs (770), survivants (24), invalides (3), journal, classification_familles.txt
    ├── passes_diagnostic/                  RÉFÉRENCE HISTORIQUE (4 fichiers) : passes « sans A » (36 survivants) et « sans A ni témoin K » (50)
    ├── rejeu_copie_propre_2026-10-10/      SORTIES DU DERNIER REJEU (14 fichiers dont 2 listes de survivants rejoués des passes) : STATUT.tsv, environnement.txt, étapes 04–07, 10, 11, 13–16
    └── experience_date_decalee_2026-10-10/ SORTIES DE L'EXPÉRIENCE du §5 (2 dates × 4 fichiers)
```

Les deux références historiques sont lues par les scripts (comparaison, rapprochement, classement) : elles ne sont donc pas facultatives. Elles proviennent de la copie de travail et ont été produites le 2026-10-09 (≈ 23:00 UTC) ; les scripts de ce dossier sont **octet pour octet** ceux qui les ont produites, hors `classify009b.py`, `rapprochement_survivants_registre.py` et `verifier_campagne_009.py` (voir §7).

## 3. Commandes de rejeu

`PREUVES` = `RACINE/fichiers-a-relire/preuves_009_pv`.

**Commande unique** (≈ 16 min sur 2 cœurs ; le dossier de sortie doit être vide ou absent) :
```
bash $PREUVES/outils/rejouer_toutes_les_verifications_009.sh $RACINE /chemin/sortie [/chemin/travail]
```
Elle écrit `STATUT.tsv` (une ligne par étape : `reussie` / `echouee` / `non_executee`, code, durée, commande) et une sortie brute par étape ; code de sortie 1 si une étape échoue. `SANS_CAMPAGNE=1` saute les trois campagnes de mutation (étapes 01–07 alors `non_executee`). **Attendu les jours UTC où mois = jour (1/1 … 12/12) : l'étape 05 échoue (§5) et le script rend donc 1** ; ce n'est pas une régression, c'est la dépendance à la date décrite au §5.

Vérification des manifestes (après rejeu ou seule ; non incluse dans le script d'ensemble car les manifestes se recalculent à chaque édition) :
```
python3 -B $PREUVES/outils/controles/verifier_manifestes_009.py $RACINE        # attendu : CONFORME
```
Expérience à date décalée (facultative, ≈ 7 min par date) :
```
bash $PREUVES/outils/controles/passes_a_date_decalee_009.sh $RACINE /chemin/sortie 2026-09-08   # mois ≠ jour : attendu 36 et 50, listes identiques à l'historique
```

Commandes unitaires :

| But | Commande | Durée observée (dernier rejeu) | Résultat attendu |
|---|---|---|---|
| **Campagne complète (797 mutants)** | `python3 -B $PREUVES/outils/campagne_mutation/mut009b.py $RACINE /tmp/mut009_travail` | 197 s | `{'tué': 770, 'survivant': 24, 'invalide': 3}` ; fichiers `survivors009.txt`, `invalides009.txt`, `killers009.json` |
| Passe sans groupe A | `MUT_EXCLUDE=Chaine python3 -B …/mut009b.py $RACINE /tmp/m_sansA` | 199 s | 36 survivants **ou 37 selon la date UTC (§5)** |
| Passe sans A ni témoin K | `MUT_EXCLUDE=Chaine,Malformees.test_T51_K_TEMOIN_sans_les_controles_de_longueur_et_d_octet_nul_les_valeurs_a_queue_passent python3 -B …/mut009b.py $RACINE /tmp/m_sansAK` | 206 s | 50 survivants **ou 51 selon la date UTC (§5)** |
| Comparaison campagne rejouée ↔ référence | `python3 -B $PREUVES/outils/campagne_mutation/comparer_campagne_009.py DOSSIER_REJEU` | < 1 s | `IDENTIQUE A LA RÉFÉRENCE` |
| Cohérence 797 = 770 + 3 + 24 (statique) | `python3 -B $PREUVES/outils/campagne_mutation/verifier_campagne_009.py $RACINE [--sorties DOSSIER]` | < 1 s | `COHÉRENT` |
| + rejeu ciblé (3 invalides, 24 survivants, N tués) | `… verifier_campagne_009.py $RACINE --rejeu 60 --travail /tmp/rejeu009` | ≈ 90 s (rejeu partiel de la nuit du 10/10, non conservé) | `COHÉRENT` |
| Rapprochement survivants ↔ registre | `python3 -B $PREUVES/outils/preuves_equivalence/rapprochement_survivants_registre.py $RACINE [mut009b.py survivors009.txt survivors_sans_A.txt survivors_sans_A_ni_temoin_K.txt]` | < 1 s | `BIJECTION OK` |
| Épreuves négatives du rapprochement | `python3 -B $PREUVES/outils/preuves_equivalence/epreuves_negatives_rapprochement.py $RACINE` | 1 s | `TOUTES LES ÉPREUVES ÉCHOUENT COMME ATTENDU` |
| Preuves d'équivalence liées au SQL | `python3 -B $PREUVES/outils/preuves_equivalence/preuves_equivalence_009.py $RACINE` | 216 s | 52 contrôles OK, `TOUT EST OK` |
| Classement par famille | `python3 -B $PREUVES/outils/campagne_mutation/classify009b.py $RACINE [DOSSIER_SORTIES]` | < 1 s | identique à `classification_familles.txt` |
| Suite machine / suite métier 001→009 | `cd $RACINE/src-tauri/tests/{machine,metier} && python3 -B -m unittest discover -s . -p 'test_*.py'` | < 1 s / 103 s | 13 / 1 866 tests OK |
| Comptage tests et sous-tests | `python3 -B $PREUVES/outils/controles/compte_sous_tests.py $RACINE/src-tauri/tests/metier` | 14 s | `tests 268 sous-tests 940 ok` |
| Intégrité SQLite / FK | `python3 -B $PREUVES/outils/controles/controle_integrite_009.py $RACINE` | < 1 s | `OK` |

## 4. Statut de chaque vérification (distinction stricte)

**Dernier rejeu** : 2026-10-10, 22:49:39 → ≈ 23:05 (Paris), soit le **10/10 UTC** ; SQLite 3.45.1, Python 3.11.15, 2 cœurs ; copie de `main` 5ebf202 **plus uniquement les fichiers de ce dossier** (ni git, ni fichier extérieur) ; commande unique du §3. Sorties : `sorties_brutes/rejeu_copie_propre_2026-10-10/`. Les outils sont restés inchangés pendant le rejeu (empreintes comparées avant/après). Les sorties 08, 09 et 12 de `STATUT.tsv` ne sont pas conservées : elles sont octet pour octet identiques aux sorties 07, 06 et à `campagne_complete/classification_familles.txt` (comparées par `cmp`).

| Vérification | Statut | Sortie | Observation |
|---|---|---|---|
| Campagne complète : 966 générés, 797 distincts ; 770 tués / 3 invalides / 24 survivants ; 0 délai dépassé | **exécutée, réussie** | 01, 04 | **Identique à la référence historique** : mêmes 24 survivants et mêmes 3 invalides (octet pour octet), même test tueur pour chacun des 770 tués |
| Partition 797 et cohérence (45 tests tueurs distincts existants) | **exécutée, réussie** | 06 (campagne rejouée ; la 09, sur la référence, lui est identique) | pas de doublon, d'oubli ni d'intrus |
| Rapprochement survivants ↔ registre S01–S24 / K01–K14 | **exécutée, réussie** | 07 (survivants rejoués ; la 08, sur la référence, lui est identique) | BIJECTION OK 24↔24 et 14↔14 |
| Épreuves négatives du rapprochement | **exécutée, réussie** | 10 | 4 échecs attendus sur 4 |
| Preuves d'équivalence (24 survivants, 14 K, 11 témoins non équivalents) | **exécutée, réussie** | 11 | 52 contrôles OK, 0 échec ; journal identique à l'ancien hors chemin et durée |
| Classement par famille | **exécutée, réussie** | 12 (non conservée : identique à `campagne_complete/classification_familles.txt`) | identique à la référence |
| Suite machine (13) et suite métier 001→009 (1 866) | **exécutées, réussies** | 13, 14 | |
| Comptage 268 tests / 940 sous-tests | **exécutée, réussie** | 15 | |
| Intégrité SQLite et clés étrangères | **exécutée, réussie** | 16 | identique à la référence |
| Passe « sans groupe A » | **exécutée, résultat DIFFÉRENT de la référence** (étape 05 « échouée ») | 02, 05, `rejeu_copie_propre…/passes_diagnostic/` | 37 survivants au lieu de 36 : explication et expérience au §5 |
| Passe « sans A ni témoin K » | **exécutée, résultat DIFFÉRENT de la référence** | 03, 05 | 51 survivants au lieu de 50 : §5 |
| Expérience à date simulée (8 et 9 sept.) | **exécutée, réussie** (hypothèse confirmée *pour l'horloge vue par les processus*) | `experience_date_decalee_2026-10-10/` | §5 |
| Vérification des deux manifestes | **exécutée, réussie** lors de la préparation de cet arbre final (script `verifier_manifestes_009.py`) | non conservée (dépend des empreintes de ce dossier) | à relancer par le lecteur : commande au §3 |
| Compatibilité sur d'autres versions de SQLite (D1–D3 sur 3.39.4→3.53.4, suite sur 3.51.1, rusqlite 3.53.2) | **résultat historique conservé, NON reproduit** | non publié (scripts hors dépôt) | cité dans le rapport comme historique |
| Rejeu partiel de la nuit du 10/10 (87 mutants), 1er essai de campagne (outil v1, 27 invalides), campagne initiale (v0), suites 13/1 866 historiques | **résultats historiques, NON conservés ici** | — | remplacés par le dernier rejeu (§6) |
| Moteur SQLite réellement embarqué dans l'application ; services Rust/TypeScript | **non exécutée — impossible** | — | §8 |

## 5. Passes de diagnostic : un survivant dépend de la date UTC

`default_fmt#1` (`'%Y-%m-%d…'` → `'%Y-%d-%d…'` : le mois est remplacé par le jour dans le `DEFAULT` de `created_at`) **survit** aux deux passes de diagnostic lorsque le jour UTC a mois = jour. Les références historiques (36 et 50) ont été produites le 2026-10-09 UTC (mois ≠ jour) ; le dernier rejeu a eu lieu le **10/10 UTC** (mois = jour) et donne 37 et 51. Le diff exact est une seule entrée en plus, `default_fmt#1` (`rejeu_copie_propre_2026-10-10/05_comparaison_passes_vs_historique.txt`).
- **Cause** : hors groupe A, seul `CheckPV.test_T51_B_created_at_par_defaut_est_l_instant_courant_utc` peut tuer ce mutant (il compare le `created_at` par défaut à l'heure UTC courante à 60 s près). Quand `%d` = `%m`, le mutant produit exactement la même chaîne que l'original : aucun test comportemental ne peut le distinguer. Cela concerne 12 jours UTC par an (1/1, 2/2 … 12/12).
- **Expérience (exécutée le 10/10 au soir)** : `passes_a_date_decalee_009.sh` rejoue les deux passes en décalant l'horloge **des seuls processus de la campagne** (bibliothèque LD_PRELOAD ; l'horloge du système n'est pas touchée ; SQL, tests et `mut009b.py` inchangés). Les processus voient bien la date simulée (`environnement.txt` de chaque dossier : SQLite `now` et Python concordent).

  | Date UTC simulée | Mois = jour ? | Passe « sans A » | Passe « sans A ni témoin K » | Listes vs référence historique |
  |---|---|---|---|---|
  | 2026-09-08 | non | **36** | **50** | **identiques** (diff vide) |
  | 2026-09-09 | oui | **37** | **51** | diffèrent d'une seule entrée : `default_fmt#1` |

  L'hypothèse est donc confirmée dans les deux sens, **sur l'horloge vue par les processus**. Ce n'est pas un rejeu un autre jour réel : la machine n'a pas été exécutée un autre jour UTC. SQLite 3.45.1 uniquement.
- **Ce qui reste vrai** : la campagne complète (24 survivants) n'en dépend pas, car le mutant y est tué par le test textuel `Chaine.test_T51_A_table_stricte_et_colonnes_exactes` ; le rapprochement du registre reste en BIJECTION OK. Aucun test, SQL ni nombre attendu n'a été modifié pour faire disparaître l'écart.
- **Conséquence** : 36 et 50 ne sont **pas** des résultats universellement reproductibles ; ils valent les jours UTC où mois ≠ jour (37 et 51 les 12 autres). Ce ne sont pas des résultats de la campagne complète.

## 6. Ce qui n'est volontairement pas dans le dossier

Écarté pour garder un dossier minimal (conservé dans la copie de travail, non publié) : la sortie complète du rejeu (listes de tués rejouées, 101 Ko, déjà comparées octet pour octet à la référence par l'étape 04), les sorties 08, 09 et 12 (doublons prouvés, §4), les journaux historiques de preuves et de suites (remplacés par les sorties 11, 13–16), le journal du 1er essai de campagne (outil v1, 27 invalides dus à un défaut d'outil), l'outil de la campagne initiale `mut009_v0_campagne_initiale.py` (`d8dcd863…`, non nécessaire à un rejeu), le rejeu partiel de la nuit du 10/10 (87 mutants), dont 3 fichiers étaient sur `main` et sont proposés à la suppression (remplacés par le rejeu complet). Le rapport cite le journal du 1er essai et l'outil initial comme **historiques non publiés**.

## 7. Qui a changé quoi dans les outils, et doublons retirés

- `rapprochement_survivants_registre.py` : arguments facultatifs à valeurs par défaut déduites de l'arborescence ; contrôle explicite des fichiers requis (code 2 et message clair) ; logique **inchangée**.
- `classify009b.py` : chemins relatifs codés en dur remplacés par des arguments (même sortie, vérifiée). `verifier_campagne_009.py` : option `--sorties` ajoutée.
- Nouveaux : `comparer_campagne_009.py`, `rejouer_toutes_les_verifications_009.sh`, `epreuves_negatives_rapprochement.py`, `verifier_manifestes_009.py`, `passes_a_date_decalee_009.sh`, `faketime_shim.c`.
- `mut009b.py`, `genmut009b.py`, `preuves_equivalence_009.py`, `compte_sous_tests.py`, `controle_integrite_009.py` : octet pour octet ceux qui ont produit les sorties historiques.
- **Doublons** : `fichiers-a-relire/outils_mutation_009.py` (sha256 `72d2e99a…`) est une copie exacte de `outils/preuves_equivalence/preuves_equivalence_009.py` ; `fichiers-a-relire/sorties_brutes_009_nul.py` (`1d56db56…`) est l'ancienne version du rapprochement, remplacée et en échec tel que publié. Aucun document utile n'y renvoie plus (seul un nom de scénario de test négatif les cite). **Leur suppression n'est sûre que si `preuves_equivalence_009.py` est publié au même moment** : c'est la seule copie du script de preuve sur `main`. Deux scripts de `main` mal rangés (`outils/preuves_equivalence/campagne_mutation/`) sont déplacés vers `outils/campagne_mutation/`.

## 8. Limites restantes (aucune n'est levée par ce dossier)

- Le moteur SQLite réellement embarqué dans l'application n'est pas identifié à partir des sources du dépôt (point V-7 des documents de conception).
- La compatibilité avec les futurs services Rust/TypeScript n'est pas démontrée : leurs sources ne sont pas dans le dépôt.
- La campagne complète et tous les rejeux ont été exécutés sur **SQLite 3.45.1** ; les résultats sur d'autres versions sont historiques et non rejoués ici. L'équivalence E10 (`instr(TEXT, x'00')` ≡ `instr(CAST(TEXT AS BLOB), x'00')`) dépend du moteur.
- Une campagne de mutation réussie ne remplace pas la validation sur le moteur réellement utilisé par l'application.
- Les chiffres 36 et 50 dépendent de la date UTC (§5) et la confirmation porte sur une horloge simulée, pas sur un autre jour réel.
