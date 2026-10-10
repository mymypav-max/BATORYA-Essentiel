# Preuves de la migration 009 (PV) — inventaire et mode de rejeu

Date : 2026-10-10. Objet : rendre **auditables et rejouables** les preuves de `RAPPORT_MUTATION__009_pv.md` et `BILAN_VALIDATION__009_pv__controle_nul.md`.
**Ce dossier ne contient ni migration, ni test, ni document officiel.** Il n'est pas destiné à `src-tauri/`. Rien n'est commité.

## 1. Prérequis

- Python 3 (rejeu fait avec 3.11.15), bibliothèque standard seulement. SQLite : celui de Python (rejeu fait avec **3.45.1**).
- `RACINE` = un dossier contenant `src-tauri/` avec les migrations 001→009 **et le `009_pv.sql` / `test_009_pv.py` révisés** (sha256 dans `MANIFEST_SHA256.txt`). Sur `origin/main`, ces deux fichiers sont encore les anciens : les outils s'arrêtent ou échouent dessus.
- Les scripts s'appellent **par leur chemin** et se retrouvent entre eux **par leur position relative** : ne pas renommer ni séparer `outils/preuves_equivalence/` (le rapprochement lit `preuves_equivalence_009.py` dans le même dossier) ni `outils/campagne_mutation/` (`genmut009b.py` et `classify009b.py` lisent `mut009b.py`).
- Aucun script n'écrit dans le dépôt : `mut009b.py` travaille dans des copies de `src-tauri/` sous le dossier de travail donné.

## 2. Arborescence

```
preuves_009_pv/
├── LISEZ-MOI__preuves_009_pv.md            (ce fichier)
├── MANIFEST_SHA256.txt                     empreintes de tous les fichiers de ce dossier (vérifiable : cd preuves_009_pv && sha256sum -c MANIFEST_SHA256.txt)
├── MANIFEST_SHA256__fichiers_valides.txt   empreintes du SQL, des tests, des diffs, du rapport et du bilan (chemins relatifs à RACINE ; sha256sum -c depuis RACINE)
├── outils/
│   ├── campagne_mutation/
│   │   ├── mut009b.py                      campagne complète (génère 966 mutants → 797 distincts, les exécute)
│   │   ├── genmut009b.py                   régénère les mutants de mut009b.py (bibliothèque)
│   │   ├── classify009b.py                 classement par famille depuis les sorties enregistrées
│   │   └── verifier_campagne_009.py        NOUVEAU : partition 797 = 770 + 3 + 24 ; rejeu ciblé facultatif
│   ├── preuves_equivalence/
│   │   ├── preuves_equivalence_009.py      52 contrôles sur le SQL réel (S01–S24, K01–K14, témoins)
│   │   ├── rapprochement_survivants_registre.py   bijection survivants de la campagne ↔ registre S/K
│   │   └── epreuves_negatives_rapprochement.py    NOUVEAU : le rapprochement doit échouer dans 4 cas
│   ├── controles/
│   │   ├── compte_sous_tests.py            268 tests / 940 sous-tests
│   │   └── controle_integrite_009.py       integrity_check / foreign_key_check sur base construite 001→009
│   └── historique/mut009_v0_campagne_initiale.py   outil de la 1re campagne (pour mémoire)
└── sorties_brutes/
    ├── campagne_complete/                  mut009_complete.log, tueurs_…json (770), survivants_… (24), invalides_… (3), classification_familles.txt
    ├── passes_diagnostic/                  passes « sans groupe A » et « sans A ni témoin K » (journaux + survivants)
    ├── preuves_equivalence/                preuves_sql_depot.log (52 OK), rapprochement.log (BIJECTION OK)
    ├── suites_et_integrite/                suite_metier.log (1 866), suite_machine.log (13), compte_sous_tests.log, integrite.log
    ├── historique/                         journal du 1er essai (outil v1, 27 invalides, défaut CAST)
    └── rejeu_depuis_structure_livree/      sorties du rejeu fait DEPUIS cette arborescence (voir §5)
```

## 3. Commandes de rejeu (depuis n'importe quel dossier ; `RACINE` et `PREUVES` à adapter)

`PREUVES` = ce dossier (`…/fichiers-a-relire/preuves_009_pv`).

| But | Commande | Durée observée | Résultat attendu |
|---|---|---|---|
| Cohérence 797 = 770 + 3 + 24 (statique) | `python3 -B $PREUVES/outils/campagne_mutation/verifier_campagne_009.py $RACINE` | ≈ 1 s | `COHÉRENT` |
| + rejeu ciblé de 3 invalides, 24 survivants, N tués | `… verifier_campagne_009.py $RACINE --rejeu 60 --travail /tmp/rejeu009` | 90 s | `COHÉRENT` |
| Preuves d'équivalence liées au SQL | `python3 -B $PREUVES/outils/preuves_equivalence/preuves_equivalence_009.py $RACINE` | 203–296 s | 52 contrôles OK, `TOUT EST OK` |
| Rapprochement survivants ↔ registre | `python3 -B $PREUVES/outils/preuves_equivalence/rapprochement_survivants_registre.py $RACINE` | < 1 s | `BIJECTION OK` |
| Épreuves négatives du rapprochement | `python3 -B $PREUVES/outils/preuves_equivalence/epreuves_negatives_rapprochement.py $RACINE` | quelques s | `TOUTES LES ÉPREUVES ÉCHOUENT COMME ATTENDU` |
| Classement par famille | `python3 -B $PREUVES/outils/campagne_mutation/classify009b.py $RACINE` | quelques s | identique à `classification_familles.txt` |
| Intégrité SQLite / FK | `python3 -B $PREUVES/outils/controles/controle_integrite_009.py $RACINE` | quelques s | `OK` |
| Comptage tests / sous-tests | `python3 -B $PREUVES/outils/controles/compte_sous_tests.py $RACINE/src-tauri/tests/metier` | ≈ 13 s | `tests 268 sous-tests 940 ok` |
| **Campagne complète (797 mutants)** | `python3 -B $PREUVES/outils/campagne_mutation/mut009b.py $RACINE /tmp/mut009_travail` | non rejouée en entier le 10/10 | `{'tué': 770, 'survivant': 24, 'invalide': 3}` + fichiers `survivors009.txt`, `invalides009.txt`, `killers009.json` |
| Passe sans groupe A | `MUT_EXCLUDE=Chaine python3 -B …/mut009b.py $RACINE /tmp/m_sansA` | idem | 36 survivants |
| Passe sans A ni témoin K | `MUT_EXCLUDE=Chaine,Malformees.test_T51_K_TEMOIN_sans_les_controles_de_longueur_et_d_octet_nul_les_valeurs_a_queue_passent python3 -B …/mut009b.py $RACINE /tmp/m_sansAK` | idem | 50 survivants |

Le rapprochement accepte aussi les arguments explicites de l'ancienne forme : `… RACINE mut009b.py survivors009.txt [survivors_sans_A.txt survivors_sans_A_ni_temoin_K.txt]` (utile pour comparer une campagne fraîchement rejouée).

## 4. Quelle sortie brute prouve quoi

| Affirmation | Sortie brute | Outil qui la recoupe | Limite |
|---|---|---|---|
| 797 mutants distincts (966 générés) | `campagne_complete/mut009_complete.log` l.1 | `verifier_campagne_009.py` (régénère) | — |
| 770 tués, avec le test tueur de chacun | `campagne_complete/tueurs_campagne_complete.json` | `verifier_campagne_009.py` : partition + existence des 45 tests tueurs | Que chacun des 770 soit bien tué n'est **rejoué que pour l'échantillon** (60 tirés, graine 2026) ; le reste exige la campagne complète |
| 3 invalides (SQL qui ne se charge pas) | `campagne_complete/invalides_campagne_complete.txt` + message d'erreur dans `mut009_complete.log` | rejeu ciblé : les 3 retrouvés | — |
| 24 survivants | `campagne_complete/survivants_campagne_complete.txt` | rejeu ciblé : les 24 survivent encore | — |
| Les 24 survivants sont équivalents, et eux seuls | `preuves_equivalence/preuves_sql_depot.log` (52 OK) + `rapprochement.log` (BIJECTION OK) | rejeu des deux scripts, épreuves négatives | Preuves **sur SQLite 3.45.1** ; les domaines bornés sont dans le script (rapport §4) |
| 14 mutants K tués seulement par le texte du témoin | `passes_diagnostic/*` + `rapprochement.log` (partie K) | rejeu du rapprochement | E10 (`instr(TEXT,x'00')` ≡ `instr(CAST…)`) dépend du moteur : vérifiée sur 3.45.1 seulement ici |
| Suites 1 866 / 13 / 268 / 940, intégrité | `suites_et_integrite/*` | `compte_sous_tests.py`, `controle_integrite_009.py` rejoués | La suite 001→009 complète (≈ 102 s) n'a pas été rejouée dans ce lot (sortie du 10/10 conservée) |

## 5. Rejeu fait le 2026-10-10 depuis cette arborescence

Dossier `sorties_brutes/rejeu_depuis_structure_livree/` (SQLite 3.45.1, Python 3.11.15, SQL et tests aux empreintes du manifeste) :
`verifier_campagne_009` partie 1 = 12 contrôles OK ; partie 2 (87 mutants) = 24 survivants, 3 invalides et 60 tués retrouvés avec le **même test tueur** ; `preuves_equivalence_009.py` = 52 OK, journal identique à l'original (hors durée) ; `rapprochement` = BIJECTION OK, journal identique à l'original ; épreuves négatives = 4 échecs attendus ; classement et intégrité identiques à l'original ; 268 tests / 940 sous-tests.
**Non rejoué** : la campagne complète de 797 mutants (710 tués non tirés au sort), et les passes « sans A » / « sans A ni témoin K ».

## 6. Ce qui a changé par rapport aux outils précédents

- `rapprochement_survivants_registre.py` : arguments facultatifs à valeurs par défaut déduites de l'arborescence ; contrôle explicite des fichiers requis (code de sortie 2 et message clair, au lieu d'un `FileNotFoundError`) ; logique de rapprochement **inchangée** (mêmes résultats, journal identique).
- `classify009b.py` : chemins relatifs codés en dur remplacés par des arguments (même sortie).
- `mut009b.py`, `genmut009b.py`, `preuves_equivalence_009.py`, `compte_sous_tests.py`, `controle_integrite_009.py`, `mut009_v0…` : **octet pour octet identiques** (empreintes du manifeste = celles du rapport).
- Nouveaux : `verifier_campagne_009.py`, `epreuves_negatives_rapprochement.py`, ce fichier, `MANIFEST_SHA256.txt`, dossier `rejeu_depuis_structure_livree/`.

## 7. Fichiers déjà poussés sur GitHub sous d'autres noms (à décider par le propriétaire du dépôt)

`fichiers-a-relire/outils_mutation_009.py` = `outils/preuves_equivalence/preuves_equivalence_009.py` (identique) ; `fichiers-a-relire/sorties_brutes_009_nul.py` = ancienne version du rapprochement (sha256 `1d56db56…`, **remplacée** par celle de ce dossier ; elle échoue telle que poussée). Ces deux fichiers sont des doublons mal nommés ; je n'y touche pas (aucun commit, aucun push).
