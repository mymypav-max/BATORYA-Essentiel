# Journal de continuité — BATORYA Essentiel V6
Ce fichier n'est pas un document de référence et ne contient aucune décision (conventions §3).

## Règles
1. Cycle d'un bloc : **ouverture** (début de session : bloc « NON CLÔTURÉE » + relevé initial) → **au fil de la session** (actions significatives, commandes) → **clôture** (relevé final, réconciliation, passage à « CLÔTURÉE »). Une session interrompue laisse le bloc « NON CLÔTURÉE » : ne jamais le compléter après coup ; la session suivante le signale dans son propre bloc.
2. Aucun bloc clôturé n'est modifié. Toute correction ultérieure est ajoutée dans un nouveau bloc daté, qui référence le bloc concerné et indique le motif de la correction.
3. Statuts de **preuve**, appliqués à chaque action ou affirmation : [FAIT-VÉRIFIÉ] (réalisé, preuve disponible, citée) · [PRÉVU] (envisagé, non réalisé) · [NON VÉRIFIÉ] (insuffisamment contrôlé). Une action [PRÉVU] n'est jamais présentée comme faite.
4. Statuts **documentaires**, distincts des précédents, réservés aux documents et décisions : [OFF] officiel · [LOCAL] modification locale non commitée · [REL] en relecture.
5. Un seul outil actif à la fois.
6. Toute écriture, création ou suppression est consignée au registre B (intention avant, résultat après), y compris fichiers temporaires, fichiers ignorés et fichiers créés par les outils.
7. Chaque relevé et chaque verdict indiquent leur **portée** : fichiers suivis / non suivis / ignorés ; contenu contrôlé par empreinte ou non. Un contrôle limité aux fichiers suivis ne permet pas d'affirmer que le dépôt est inchangé.
8. Un état final identique à l'état initial ne prouve pas l'absence de modification temporaire.
9. Si un relevé est impossible : « RELEVÉ IMPOSSIBLE : <motif> ». Ne rien déduire.

## Relevé d'état (lecture seule ; références locales ; aucun fetch)
- `git branch --show-current` · `git rev-parse --short HEAD` · `git rev-list --left-right --count HEAD...origin/main`
- `git status --short --ignored` (dossiers volumineux résumés) · `git diff --stat` · `git diff --cached --stat` · `git stash list`
- Empreintes SHA-256 **uniquement** pour : les fichiers que la session compte modifier ; les fichiers critiques concernés (migrations 006, 009a, 009b ; fichiers de `.claude/` si la session s'y intéresse) ; toute comparaison jugée utile. Pas de calcul global systématique.
- Limites connues : sans empreinte, le contenu des fichiers non suivis et des fichiers suivis déjà modifiés n'est pas contrôlé (`git diff --stat` n'en donne qu'une trace grossière) ; les fichiers ignorés ne sont contrôlés que par présence et date.

## Modèle de bloc (à copier pour chaque session)

```markdown
## Session <AAAA-MM-JJ hh:mm> — outil : Claude Code | Claude Desktop
Clôture : NON CLÔTURÉE

### A. Ouverture — relevé initial
- Branche / HEAD / avance-retard :
- Suivis modifiés (`diff --stat`) · non suivis (nombre/liste) · indexé · stash :
- Ignorés notables (présence, date) :
- Empreintes (fichiers désignés par la règle ci-dessus) :
- Portée du relevé : suivis ☐ non suivis ☐ ignorés ☐ contenu par empreinte ☐
- Écart avec l'état final de la session précédente : aucun | liste | état précédent absent | bloc précédent NON CLÔTURÉ

### B. Registre des actions (au fil de la session)
| # | Action | Cible (dépôt / ignoré / hors dépôt) | Avant (intention) | Après (résultat) | Preuve | Statut | Annulée ? |

### C. Commandes et tests réellement exécutés
| Commande exacte | Répertoire | Résultat réel (code de sortie, comptes, extrait) | Portée / limites | Statut |
(Rien ici sans exécution. Une commande ou un test non lancé est [PRÉVU] en D.)

### D. Décisions rapportées, points non résolus, prochaine étape
- Décisions (réf., contenu, source ; statut documentaire [OFF]/[LOCAL]/[REL] ; statut de preuve) :
- Points non résolus :
- Prochaine étape [PRÉVU] et préalables :

### E. Clôture — relevé final (mêmes éléments et mêmes portées que A)

### F. Réconciliation
- Écarts initial → final : expliqués par B | non expliqués (liste) | non évaluables (portée insuffisante)
- Registre B tenu sur toute la session : oui | non | incertain
- Portée du verdict :
- Verdict :
  - CONCORDANT-PROUVÉ : écarts = registre B, sur la portée indiquée, avec empreintes cohérentes pour les fichiers concernés.
  - CONCORDANT-NON-PROUVÉ : état final = initial sur la portée indiquée, mais registre incomplet, portée partielle ou contenu non contrôlé ; modification non détectée non exclue.
  - DISCORDANT : écarts non expliqués (liste).
  - RÉCONCILIATION IMPOSSIBLE : motif.
- Fiabilité : COMPLET | PARTIEL | NON FIABLE (motif)
Clôture : CLÔTURÉE <date heure>   (seulement une fois F rempli)
```

---

## Session 2026-10-22 13:33 — Claude Code — tranche 010 `historique` : intégration de deux tests de comportement dans `test_010_historique.py` et mutation ciblée de contrôle
Clôture : CLÔTURÉE le 2026-10-22 à 13:58 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-22 13:33, avant toute écriture de ce bloc)
- `CLAUDE.md` (fourni au démarrage) ; dernier bloc du journal = 2026-10-22 11:07, CLÔTURÉE, lu avant toute autre action [FAIT-VÉRIFIÉ]
- Git `main`, HEAD `a99d4c2`, 28 entrées `git status`, rien d'indexé, aucun stash (identique à l'état final du bloc 11:07) [FAIT-VÉRIFIÉ]
- Empreintes (16 premiers caractères) : migration 010 `763f81cd771ca295`, test 010 `a5d275ad5e36984e`, modèle V3.14 `064d40f2257b6cad`, `invariants.md` `381b8682a018a198`, `CLAUDE.md` `9a4c1f5d2a06a7aa`, `.claude/settings.local.json` `c49433832d9be741` ; 31 fichiers antérieurs : 0 écart [FAIT-VÉRIFIÉ]
- Journal avant ouverture : `9d68d0bcf2288988`.
- Fichiers que cette session compte modifier (autorisation de Rémy, message du 2026-10-22) : `src-tauri/tests/metier/test_010_historique.py` (deux tests) ; le modèle V3.14 (ligne T-55) seulement si la couverture annoncée l'exige ; ce journal. Aucune migration modifiée. Travaux hors dépôt : copies isolées du scratchpad.
- Portée du relevé : suivis ☑ · non suivis (par nom) ☑ · empreintes ☑. **Non contrôlé :** identique au bloc 02:17.

### B. Registre des actions
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (journal) | insérer ce bloc au-dessus du bloc 11:07 | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Relecture, correction et intégration des deux tests candidats | dépôt (`test_010_historique.py`) | D19 (`created_at` position par position), F16 (ABORT contre ROLLBACK) | effectuée : relus et renforcés (séparateurs testés avec une lettre et un chiffre ; F16 : message par opération, contenu des lignes avant et après, écriture validée par COMMIT, ROLLBACK de secours) ; `a5d275ad5e36984e` → `a42a843378c140b2` ; 94 tests ; CRLF conservé | [FAIT-VÉRIFIÉ] |
| 3 | Exécution des tests (dépôt, copies CRLF et LF) et mutation ciblée sur la référence actualisée | dépôt (lecture), scratchpad | résultats | effectuée : voir C ; ligne T-55, bandeau du §4.14, D-64 et §17.1 du modèle V3.14 actualisés (couverture et état de la campagne) ; `064d40f2257b6cad` → `0986ab87e092d0d4` | [FAIT-VÉRIFIÉ] |
| 4 | Complément de ce bloc et clôture | dépôt (journal) | résultats et réconciliation | effectuée | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
- `python -B -m unittest test_010_historique -v` (dépôt) : **94 tests, OK** [FAIT-VÉRIFIÉ]
- Copies isolées reconstruites (`mutcamp.setup()`, `ref` identique au dépôt) ; baseline `python -B -m unittest discover -s src-tauri/tests/metier -p "test_*.py" -v` : copie CRLF **2197 tests, OK** (140,9 s) ; copie LF **2197 tests, OK** (141,1 s) [FAIT-VÉRIFIÉ]
- Suite métier depuis la racine du dépôt (variante `-B` de `CLAUDE.md` §5) : **2197 tests, OK** (236,6 s avant l'actualisation du modèle, 115,4 s après) [FAIT-VÉRIFIÉ]
- `python -B mut010_run.py run --env crlf --workers 7 --out results2_crlf` et `--env lf --workers 7 --out results2_lf` : les **418 mutants** rejoués dans chaque environnement : **416 tués, 2 survivants (M013, M166), 0 invalide, 0 délai dépassé** ; statuts identiques CRLF/LF ; mêmes tueurs pour 414 des 416 tués (M037 et M373, `UNIQUE (created_at)`, dépendants de l'horloge) ; intégrité de la copie vérifiée avant et après chaque mutant (418 ok par environnement) ; dépôt inchangé pendant la campagne [FAIT-VÉRIFIÉ]
- Les 22 survivants de `created_at` sont tous tués par D19 (et par aucun autre test) ; M387 et M402 (`RAISE(ROLLBACK)`) sont tués par F16 ; aucun mutant tué par D19 ou F16 sans divergence du harnais (pas de faux positif) [FAIT-VÉRIFIÉ]
- `python -B mut010_equiv.py surv results2_crlf.jsonl` : M013 et M166 sans divergence sur le domaine énuméré ; trois témoins divergents ; M013 identique sous le protocole du runner pour `user_version` 0, 1, 13, 14, 15, 16, 17, 20 [FAIT-VÉRIFIÉ]
- Aucune campagne de mutation du code des tests ; `src-tauri/tests/machine/` et tests front non lancés.

### D. Autorisation
**Instruction de Rémy (message du 2026-10-22)** : intégration des deux tests candidats (`test_010_complement.py` du scratchpad) dans `test_010_historique.py` après relecture ; ni modification de la migration SQL, ni mutation du code des tests ; exécution CRLF et LF et suite métier ; mutation ciblée sur copies isolées ; documentation seulement si la couverture annoncée de T-55 l'exige ; journal clôturé non réécrit ; ni commit ni push.

### E. Clôture — relevé final (2026-10-22 13:58)
- Git : `main`, HEAD `a99d4c2`, 28 entrées `git status`, rien d'indexé, aucun stash, aucun commit ni push [FAIT-VÉRIFIÉ]
- Fichiers du dépôt modifiés depuis l'ouverture (`find -newermt`) : `test_010_historique.py` et le modèle V3.14, plus ce journal — aucun autre ; migration 010 `763f81cd771ca295`, `invariants.md` `381b8682a018a198`, `CLAUDE.md`, `.claude/settings.local.json` inchangés ; les 31 fichiers antérieurs : 0 écart [FAIT-VÉRIFIÉ]
- Nouveaux : test 010 `a42a843378c140b2`, modèle V3.14 `0986ab87e092d0d4`.
- Portée du relevé final : identique à A. **Non contrôlé :** identique au bloc 02:17.

### F. Réconciliation
- Écarts initial → final : test 010, modèle V3.14, ce journal. Registre B tenu : oui. **Verdict : CONCORDANT-NON-PROUVÉ**. Fiabilité : COMPLET sur la portée indiquée.
- Statut : **aucun changement consigné comme acquis** : la tranche 010 n'est pas validée par le propriétaire ; V3.14 reste en relecture ; la campagne ciblée est un rejeu des 418 mutants sur copies isolées, non une validation.
Clôture : CLÔTURÉE 2026-10-22 13:58

---

## Session 2026-10-22 11:07 — Claude Code — campagne de mutation T-55 de la tranche 010 `historique` (copie isolée, hors dépôt)
Clôture : CLÔTURÉE le 2026-10-22 à 11:56 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-22 11:07, avant toute écriture de ce bloc)
- `CLAUDE.md` (fourni au démarrage) ; dernier bloc du journal = 2026-10-22 10:13, CLÔTURÉE, lu avant toute autre action [FAIT-VÉRIFIÉ]
- Git `main`, HEAD `a99d4c2`, 28 entrées `git status`, rien d'indexé, aucun stash [FAIT-VÉRIFIÉ] (identique à l'état final du bloc 10:13)
- Empreintes (SHA-256, 16 premiers caractères) : migration 010 `763f81cd771ca295`, test 010 `a5d275ad5e36984e`, modèle V3.14 `064d40f2257b6cad`, `invariants.md` `381b8682a018a198`, `CLAUDE.md` `9a4c1f5d2a06a7aa`, `.claude/settings.local.json` `c49433832d9be741` ; les 31 fichiers antérieurs conformes à `empreintes_avant_010.txt` (0 écart) ; 16 migrations et 17 modules de test présents [FAIT-VÉRIFIÉ]
- Journal avant ouverture : `f1490d53749480dc` (octets du bloc 10:13 compris).
- Fichiers que cette session compte écrire : ce journal ; **hors dépôt** (scratchpad) : pilote ad hoc, copies isolées, résultats. Aucun fichier du dépôt autre que le journal.
- Portée du relevé : suivis ☑ · non suivis (par nom) ☑ · empreintes ☑. **Non contrôlé :** identique au bloc 02:17.

### B. Registre des actions
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (journal) | insérer ce bloc au-dessus du bloc 10:13 | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Reconstruction de la copie isolée (`ref`, `work`, `work_lf`) à partir du dépôt actuel, baselines, génération et exécution des mutants, preuves d'équivalence, rejeux | scratchpad (hors dépôt) | résultats | effectuée : voir C et le rapport ; fichiers de travail dans le scratchpad (`mutwork/`, `mut010/`, `mut010_gen.py`, `mut010_run.py`, `mut010_equiv.py`, `test_010_complement.py`) | [FAIT-VÉRIFIÉ] |
| 3 | Complément de ce bloc (C, E, F) et clôture | dépôt (journal) | résultats et réconciliation | effectuée | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
- Reconstruction de la copie isolée (`mutcamp.setup()` du pilote existant, scratchpad) depuis le dépôt actuel : `ref` = 36 fichiers identiques au dépôt octet pour octet (16 migrations, 17 modules de test, modèle V3.14) [FAIT-VÉRIFIÉ]
- Baseline avant toute mutation : `python -B -m unittest discover -s src-tauri/tests/metier -p "test_*.py" -v` dans la copie CRLF : **2195 tests, OK** (141,2 s) ; dans la copie LF : **2195 tests, OK** (140,8 s) [FAIT-VÉRIFIÉ]
- `python -B mut010_gen.py` : **418 mutants générés, 418 distincts** (0 doublon), dérivés du texte réel de `010_historique.sql` de `ref` [FAIT-VÉRIFIÉ]
- `python -B mut010_run.py run --env crlf --workers 8` : 418 mutants, chacun avec les 92 tests de `test_010_historique` (sans arrêt au premier échec) : **394 tués, 24 survivants, 0 invalide, 0 délai dépassé** ; intégrité de la copie comparée à la référence avant et après chacun des 418 mutants (418 ok), puis en fin de campagne ; dépôt (`src-tauri` et modèle) inchangé [FAIT-VÉRIFIÉ]
- `python -B mut010_run.py run --env lf --workers 6` (campagne complète en LF) : mêmes statuts pour les 418 mutants ; mêmes tests tueurs pour 392 des 394 tués (M037 et M373 : `UNIQUE (created_at)`, ensemble de tueurs dépendant de la résolution de l'horloge) ; rejeu `--ids` des 24 survivants et de 60 tués tirés (graine 2026) en LF : 84 sur 84 identiques [FAIT-VÉRIFIÉ]
- `python -B mut010_equiv.py sig 0..11 12` (harnais d'équivalence différentielle, 12 processus) puis `mut010_equiv.py surv` : signatures de comportement des 418 mutants ; survivants et témoins divergents [FAIT-VÉRIFIÉ]
- `python -B mut010_run.py baseline` et `run --extra test_010_complement.py --module test_010_complement` : complément **candidat**, hors dépôt (2 tests) ; baseline OK en CRLF et en LF ; il tue les 22 survivants de `created_at` et les deux variantes `RAISE(ROLLBACK)` [FAIT-VÉRIFIÉ]
- Aucun test du dépôt n'a été lancé hors de la copie isolée ; `test_010_historique.py` du dépôt n'a pas été modifié. `src-tauri/tests/machine/` et tests front non lancés.

### D. Autorisation
**Instruction de Rémy (message du 2026-10-22)** : campagne de mutation T-55 autorisée (exécution et analyse), sur la version actuelle de `010_historique.sql`, `test_010_historique.py` (92 tests) et du modèle V3.14 ; baseline CRLF et LF avant toute mutation ; copies isolées hors dépôt ; pilote ad hoc dans l'environnement temporaire existant, aucun outil ajouté au dépôt ; ni commit, ni push, ni modification des migrations ou tests existants, ni modification documentaire sans nécessité ; arrêt et attente de la revue de Rémy à la fin.

### E. Clôture — relevé final (2026-10-22 11:56)
- Git : `main`, HEAD `a99d4c2`, 28 entrées `git status`, rien d'indexé, aucun stash, aucun commit [FAIT-VÉRIFIÉ]
- Empreintes : migration 010 `763f81cd771ca295`, test 010 `a5d275ad5e36984e`, modèle V3.14 `064d40f2257b6cad`, `invariants.md` `381b8682a018a198`, `CLAUDE.md` `9a4c1f5d2a06a7aa`, `.claude/settings.local.json` `c49433832d9be741` : identiques à A ; les 31 fichiers antérieurs : 0 écart ; aucun fichier du dépôt modifié depuis l'ouverture hors ce journal (`find -newermt`) [FAIT-VÉRIFIÉ]
- Copies : `ref` inchangée ; copies de travail conformes à la référence en fin de campagne (assertions du pilote) [FAIT-VÉRIFIÉ]
- Portée du relevé final : identique à A. **Non contrôlé :** identique au bloc 02:17.

### F. Réconciliation
- Écarts initial → final : ce journal seul. Registre B tenu : oui. **Verdict : CONCORDANT-NON-PROUVÉ** (portée : voir E). Fiabilité : COMPLET sur la portée indiquée.
- Résultat de la campagne (détail dans le rapport) : **non concluante en l'état** : 22 survivants non équivalents (format de `created_at`, position par position) ; 2 survivants équivalents (M013, M166) avec preuve et témoins divergents ; 72 mutants tués par des seuls tests de texte, dont 59 équivalents au sens du harnais ; M387 et M402 (`RAISE(ROLLBACK)`) tués par le seul texte, non équivalents. Aucune correction du dépôt : décision de Rémy.
- Statut : **aucun changement consigné comme acquis** ; la tranche 010 n'est pas validée ; V3.14 reste en relecture.
Clôture : CLÔTURÉE 2026-10-22 11:56

---

## Session 2026-10-22 10:13 — Claude Code — tranche 010 `historique` : contrôle des octets NUL, corrections documentaires du modèle V3.14 (relecture ciblée puis corrections)
Clôture : CLÔTURÉE le 2026-10-22 à 10:13 (ouverture tardive : bloc rédigé en fin de session, voir F)

### A. Relevé initial (état constaté au début des corrections, après la relecture en lecture seule)
- Dernier bloc du journal lu : 2026-10-22 09:36, CLÔTURÉE ; `CLAUDE.md` fourni au démarrage [FAIT-VÉRIFIÉ]
- Git `main`, HEAD `a99d4c2`, 28 entrées `git status`, rien d'indexé, aucun stash ; empreintes : migration 010 `6174ca0d55c7e878`, test 010 `0c0a7fe67c11ba78`, modèle V3.14 `311e254b36634038`, `invariants.md` `381b8682a018a198`, journal `b21894b16dd052e2` ; les 31 fichiers antérieurs conformes à `empreintes_avant_010.txt` [FAIT-VÉRIFIÉ]
- Portée : suivis ☑ · non suivis (par nom) ☑ · empreintes ☑. **Non contrôlé :** identique au bloc 02:17.

### B. Registre des actions
| # | Action | Cible | Résultat | Statut |
|---|---|---|---|---|
| 1 | Contrôle NUL dans `010_historique.sql` : `donnees` (`json_valid(...) AND instr(CAST(donnees AS BLOB), x'00') = 0`), `created_at` (`AND length(CAST(created_at AS BLOB)) = 24`), commentaire d'en-tête ; mécanisme repris de `009_pv.sql` ; `6174ca0d55c7e878` → `763f81cd771ca295` | dépôt | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | `test_010_historique.py` : 8 tests ajoutés (B contrôle présent dans le DDL ; D14 à D18 ; E25, E26), constantes `NUL`, `ECH_NUL`, `GLOB_CREATED_AT`, docstrings ; `0c0a7fe67c11ba78` → `a5d275ad5e36984e` ; fins de ligne CRLF conservées | dépôt | effectuée | [FAIT-VÉRIFIÉ] |
| 3 | Modèle V3.14 : §2.1 (`historique.entite_id` : orphelin admis, pas de requête de contrôle), CK-09 (§14, deux passages : hors `historique`), §4.14 (état, contrôle NUL, `created_at`), en-tête, T-55, §13.3, D-64, §17.1 ; `311e254b36634038` → `064d40f2257b6cad` | dépôt | effectuée | [FAIT-VÉRIFIÉ] |
| 4 | `invariants.md` | dépôt | non modifié : aucune contradiction réelle avec les décisions | [FAIT-VÉRIFIÉ] |
| 5 | Sondes en mémoire (copie du DDL, hors dépôt) et contrôle négatif : les nouveaux tests exécutés contre la migration d'avant la correction échouent tous (13 échecs sur 13 sélectionnés) | scratchpad | effectuées | [FAIT-VÉRIFIÉ] |
| 6 | Ouverture et clôture de ce bloc | dépôt (journal) | effectuée | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
- `python -B -m unittest test_010_historique -v` depuis `src-tauri/tests/metier` : **92 tests, OK** (4,37 s) [FAIT-VÉRIFIÉ]
- `python -B -m unittest discover -s src-tauri/tests/metier -p "test_*.py" -v` depuis la racine (variante `-B` de `CLAUDE.md` §5) : **2195 tests, OK**, code de sortie 0 (94,05 s) ; avertissements « ResourceWarning : unclosed database » préexistants, non corrigés [FAIT-VÉRIFIÉ]
- Aucune campagne de mutation ; `src-tauri/tests/machine/` et tests front non lancés.

### D. Autorisation
Message de Rémy du 2026-10-22 (« corrections avant campagne de mutation ») : contrôle NUL dans 010 (mécanisme de 009), mise à jour directe des documents officiels en cas de contradiction, conservation de la décision A ; ni campagne de mutation, ni nouvel outil, ni commit ; journal clôturé non modifié artificiellement.

### E. Clôture — relevé final (2026-10-22 10:13)
- Git : `main`, HEAD `a99d4c2`, 28 entrées `git status` (identiques), rien d'indexé, aucun stash, `git diff --stat` 9 fichiers +274 / −127 (modèle V3.14 compris) [FAIT-VÉRIFIÉ]. Aucun commit.
- Les 31 fichiers antérieurs (15 migrations, 16 tests) : 0 écart ; `cdc-errata-v6.md`, `modèle-métier-V6.md`, `conventions-techniques-v6.md`, CDC, `docs/README.md`, `CLAUDE.md`, `.claude/settings.local.json`, `invariants.md` inchangés ; aucun bloc antérieur du journal modifié [FAIT-VÉRIFIÉ]
- Nouveaux : migration `763f81cd771ca295`, test `a5d275ad5e36984e`, modèle V3.14 `064d40f2257b6cad`.
- Portée : identique à A. **Non contrôlé :** identique au bloc 02:17.

### F. Réconciliation
- Écarts initial → final : B1 à B3 et ce journal. Registre B tenu : oui. **Verdict : CONCORDANT-NON-PROUVÉ**. Ouverture tardive signalée (bloc rédigé après les actions, à partir de leur trace) : fiabilité COMPLET sur la portée, sauf l'horodatage des actions B1 à B3.
- Correction d'une inexactitude du bloc 09:36 (non réécrit) : les outils de `fichiers-a-relire/` y sont dits « non suivis » ; ils sont suivis par Git.
- Statut : **aucun changement consigné comme acquis** : la tranche 010 reste locale, non commitée, campagne de mutation non réalisée, revue du rapport en attente ; V3.14 reste en relecture.
- Points relevés non traités : la V3.12 contient la même phrase sur l'existence des `entite_id` (version historique, non modifiée) ; le §17.1 de la V3.14 donnait 010a et 011 au même rang 17 (reformulé sans attribuer de rang à 011).
Clôture : CLÔTURÉE 2026-10-22 10:13

---

## Session 2026-10-22 09:36 — Claude Code — tranche 010 `historique` : ajustements documentaires minimaux, migration `010_historique.sql` et test `test_010_historique.py`
Clôture : CLÔTURÉE le 2026-10-22 à 09:49 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-22 09:36, avant toute écriture de ce bloc)
- `CLAUDE.md` (fourni au démarrage) ; dernier bloc du journal = 2026-10-22 09:00, CLÔTURÉE le 09:03, verdict CONCORDANT-NON-PROUVÉ, lu avant toute autre action [FAIT-VÉRIFIÉ]
- Comparaison à l'état final du bloc 09:00 : Git `main`, HEAD `a99d4c2`, 26 entrées `git status`, `git diff --stat` 9 fichiers +271 / −125 ; empreintes `invariants.md` `a983a013397aff51`, modèle V3.14 `02bf4a1ac3f36946`, `cdc-errata-v6.md` `c9c2cfc492c4d98d`, `modèle-métier-V6.md` `9aa5ff44a45cfe17`, `conventions-techniques-v6.md` `ed9c9c8d357307c4`, CDC `5937b7bcda5fcf91`, `docs/README.md` `54d5e5968218cef8`, `CLAUDE.md` `9a4c1f5d2a06a7aa`, `.claude/settings.local.json` `c49433832d9be741`, agrégat des 15 migrations et 16 fichiers de test `1aec50f21bd38398` : aucun écart [FAIT-VÉRIFIÉ]
- Journal avant ouverture : SHA-256 `c1d37c47a6fbcefc…`. Empreintes individuelles des 31 fichiers (15 migrations et 16 tests) relevées avant toute écriture (copie dans le scratchpad, `empreintes_avant_010.txt`).
- Fichiers que cette session compte créer ou modifier (autorisation de Rémy, message du 2026-10-22, validation du cadrage) : création de `src-tauri/migrations/metier/010_historique.sql` et de `src-tauri/tests/metier/test_010_historique.py` ; modification minimale de `docs/conception/modèle-données-sqlite-v6-v3.14.md` et de `docs/conception/invariants.md` pour retranscrire les décisions du cadrage (retrait de l'extension de CK-09 à `historique`, concordance de `bc_id` garantie par le service, sens de `entite_id` et de `donnees`) ; ce journal. Aucune migration ni aucun test existant ne sera modifié.
- Portée du relevé : suivis ☑ · empreintes ☑ (documents, 31 fichiers individuellement, agrégat). **Non contrôlé :** identique au bloc 02:17.

### B. Registre des actions
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (`docs/suivi/journal-continuite.md`) | insérer ce bloc au-dessus du bloc 09:00 | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Ajustements documentaires minimaux (modèle V3.14, `invariants.md`) | dépôt | retirer l'extension de CK-09 et les « requêtes de contrôle » de `historique`, consigner les décisions A, B et C du cadrage | effectuée : modèle V3.14 (en-tête, §4.14 `entite_id` et bloc « Écriture et responsabilités », liste des CK du §14 rétablie sans extension de CK-09, D-64, T-55) et `invariants.md` (INV-110 : concordance garantie par le service ; ligne de journal du registre ; version 11) ; modèle `02bf4a1ac3f36946` → `311e254b36634038`, invariants `a983a013397aff51` → `381b8682a018a198` ; bloc CK-21 / CK-22 inchangé ; sauvegardes `docs_avant7\` | [FAIT-VÉRIFIÉ] |
| 3 | Création de `010_historique.sql` | dépôt | rang 16, garde `user_version = 15`, §4.14 du modèle | effectuée : fichier créé (145 lignes, CRLF), rang 16, garde `user_version = 15`, table `historique` STRICT, CHECK `acceptation` (bc_id non NULL pour les deux natures), trois index, deux triggers TR-60 ; aucun PRAGMA, aucune transaction, aucune donnée, aucune requête de contrôle ; appliquée par le runner de test sur une base de rang 15 → `user_version` 16, `integrity_check` ok | [FAIT-VÉRIFIÉ] |
| 4 | Création de `test_010_historique.py` | dépôt | groupes A à H sur le modèle de `test_009c` | effectuée : fichier créé (785 lignes, CRLF, 84 tests) ; groupes A (chaîne, rang, garde), B (structure), C (énumérations), D (`donnees`, `created_at`, références), E (`acceptation`), F (append-only, `recursive_triggers=ON` activé et relu, témoins REPLACE, témoin OFF), G (immuabilité des 15 migrations antérieures par empreinte), H (non-régression), M (conformité au modèle) | [FAIT-VÉRIFIÉ] |
| 5 | Exécution de `test_010_historique.py`, puis de la suite métier (commande de `CLAUDE.md` §5), correction des défauts des deux fichiers créés | dépôt | résultats réels | effectuée : voir C ; défaut du test D13 (une valeur entière est convertie sans perte en TEXT par une table STRICT, donc non refusée) corrigé dans `test_010_historique.py` ; autres corrections de tests écrits pendant la session avant la première exécution complète | [FAIT-VÉRIFIÉ] |
| 6 | Vérification des empreintes antérieures, outillage de mutation, relevé Git, complément de ce bloc (E, F) et clôture | dépôt, scratchpad | aucune migration ni aucun test antérieur modifié | effectuée : voir C, E et F ; aucune campagne de mutation lancée (hors autorisation) | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
- `python -B -m unittest test_010_historique -v` depuis `src-tauri/tests/metier` : première exécution 84 tests, **83 OK, 1 échec** (D13) ; après correction de D13 : **84 tests, OK** (3,96 s) [FAIT-VÉRIFIÉ]
- `python -m unittest discover -s src-tauri/tests/metier -p "test_*.py" -v` depuis la racine du dépôt (commande de `CLAUDE.md` §5, sans `-B`) : **Ran 2187 tests in 92,816 s — OK**, code de sortie 0, sortie complète dans le scratchpad (`suite_metier.txt`) [FAIT-VÉRIFIÉ]
- Cette commande a pu écrire des fichiers ignorés (`src-tauri/tests/metier/__pycache__/`) ; les exécutions de `test_010` ont utilisé `-B` [FAIT-VÉRIFIÉ]
- Avertissements « ResourceWarning : unclosed database » issus des assistants de `test_005b` (connexions du runner) : antérieurs à cette tranche, non corrigés [FAIT-VÉRIFIÉ]
- Hors suite : `src-tauri/tests/machine/test_premier_demarrage.py`, tests front et campagnes de mutation non lancés (non demandés)
- Outillage de mutation : aucun outil complet, exécutable et autonome, n'est versionné ; le dépôt ne contient (non suivis, dans `fichiers-a-relire/`) que `outils_mutation_009.py`, `classify009b.py`, `verifier_campagne_009.py` et des rapports, dont certains dépendent de modules absents (voir bloc 2026-10-18 23:31). **Aucune campagne de mutation n'a été lancée** pour `test_010_historique.py` : il en faut une (conventions §7.1) avant intégration, avec autorisation distincte de Rémy [FAIT-VÉRIFIÉ pour la recherche dans le dépôt]

### D. Autorisation
**Instruction de Rémy (message du 2026-10-22)** : cadrage de la tranche 010 validé (références polymorphes et orphelins, `donnees`, contrôles inter-tables, décisions conservées) ; ajustements documentaires minimaux autorisés si indispensables ; création de `010_historique.sql` et de `test_010_historique.py` ; exécution de `test_010_historique.py` puis de la suite métier avec la commande habituelle ; correction des seuls fichiers autorisés ; vérification des empreintes antérieures ; signalement de l'outillage de mutation ; aucun commit ; aucune migration ni aucun test existant modifié.

### E. Clôture — relevé final (2026-10-22 09:49)
- Git : `main`, HEAD `a99d4c2`, 28 entrées `git status` (26 en A + `010_historique.sql` et `test_010_historique.py`, non suivis, créés par cette session ; aucune autre différence de liste), `git diff --stat` 9 fichiers +271 / −124 (−125 en A, du fait de l'alignement des deux documents) [FAIT-VÉRIFIÉ]. Aucun commit, aucune opération Git d'écriture.
- Fichiers modifiés ou créés depuis l'ouverture (`find -newermt "2026-10-22 09:30:00"`, hors fichiers ignorés) : `invariants.md`, modèle V3.14, `010_historique.sql`, `test_010_historique.py` et ce journal — **aucun autre** [FAIT-VÉRIFIÉ]
- Empreintes (SHA-256 des octets, 16 premiers caractères) : les **31 fichiers** (15 migrations et 16 tests) relevés avant toute écriture sont **tous identiques** à `empreintes_avant_010.txt` (0 écart) ; cdc-errata `c9c2cfc492c4d98d`, modèle métier `9aa5ff44a45cfe17`, conventions `ed9c9c8d357307c4`, CDC `5937b7bcda5fcf91`, `docs/README.md` `54d5e5968218cef8`, `CLAUDE.md` `9a4c1f5d2a06a7aa`, `.claude/settings.local.json` `c49433832d9be741` inchangés ; modifiés volontairement : invariants `381b8682a018a198`, modèle V3.14 `311e254b36634038` ; créés : `010_historique.sql` `6174ca0d55c7e878`, `test_010_historique.py` `0c0a7fe67c11ba78` [FAIT-VÉRIFIÉ]
- L'agrégat de l'ouverture (`1aec50f21bd38398`) n'a pas été recalculé : sa méthode n'est pas consignée ; la comparaison individuelle des 31 fichiers la remplace.
- Portée du relevé final : suivis ☑ · non suivis (par nom, `find`) ☑ · empreintes ☑ · ignorés : `__pycache__` présent (non comparé). **Non contrôlé :** identique au bloc 02:17.

### F. Réconciliation
- Écarts initial → final : modèle V3.14 et invariants (B2) ; création des deux fichiers de la tranche (B3, B4) ; ce journal (B1) ; fichiers ignorés (`__pycache__`) susceptibles d'avoir changé ; aucun autre écart sur la portée contrôlée.
- Registre B tenu : oui. **Verdict : CONCORDANT-NON-PROUVÉ** (portée : voir E). Fiabilité : COMPLET sur la portée indiquée.
- Statut documentaire : **aucun changement consigné comme acquis**. La migration 010 et son test sont [LOCAL] (non commités) ; D-64 et T-55 restent en rédaction en relecture ; la campagne de mutation de `test_010_historique.py` n'est pas faite ; le rang 16 n'a pas de preuve par runner du dépôt (aucun runner dans le dépôt) hors l'émulation du test ; `CLAUDE.md` n'est pas modifié (la mention de la chaîne de migrations y reste à tenir à jour sur décision de Rémy).
- Limite assumée : la protection append-only dépend de `PRAGMA recursive_triggers=ON` à chaque ouverture de connexion (témoin OFF dans F15).
Clôture : CLÔTURÉE 2026-10-22 09:49

---

## Session 2026-10-22 09:00 — Claude Code — arbitrages devis ↔ BC et `bc_id` des événements `acceptation` : mise en cohérence documentaire avant la tranche 010
Clôture : CLÔTURÉE le 2026-10-22 à 09:03 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-22 09:00, avant toute écriture de ce bloc)
- `CLAUDE.md` (fourni au démarrage) ; dernier bloc du journal = 2026-10-22 08:38, CLÔTURÉE (ouverture tardive signalée, fiabilité PARTIEL), lu avant toute autre action [FAIT-VÉRIFIÉ]
- Comparaison à l'état final du bloc 08:38 : Git `main`, HEAD `a99d4c2`, 26 entrées `git status`, `git diff --stat` 9 fichiers +253 / −116 ; empreintes `invariants.md` `990b0ea811688d04`, modèle V3.14 `b389dbec78789215`, `cdc-errata-v6.md` `0459fef9a6683f37`, `modèle-métier-V6.md` `3db0e15a95e052f0`, `conventions-techniques-v6.md` `2be827c5aa6e3b5f`, CDC `5937b7bcda5fcf91`, `docs/README.md` `54d5e5968218cef8`, `CLAUDE.md` `9a4c1f5d2a06a7aa`, `.claude/settings.local.json` `c49433832d9be741`, agrégat migrations + tests métier `1aec50f21bd38398` : aucun écart [FAIT-VÉRIFIÉ]
- Journal avant ouverture : SHA-256 `ac9532b7b1594377…`
- Fichiers que cette session compte modifier (décisions du propriétaire, message du 2026-10-22) : `docs/conception/invariants.md` (INV-40, INV-110, registre), `docs/conception/modèle-métier-V6.md`, `docs/conception/modèle-données-sqlite-v6-v3.14.md` (§4.7 bis, §4.14, ligne de garanties du §4.7, CK-09, D-64, T-55, en-tête), `docs/décisions/cdc-errata-v6.md` (E-22 : complément), `docs/conception/conventions-techniques-v6.md` (§2) ; ce journal. Le CDC, `CLAUDE.md`, `docs/README.md`, les migrations, les tests et `fichiers-a-relire/` ne sont pas modifiés.
- Portée du relevé : suivis ☑ · empreintes ☑ · non suivis ☑ (par nom). **Non contrôlé :** identique au bloc 02:17.

### B. Registre des actions
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (`docs/suivi/journal-continuite.md`) | insérer ce bloc au-dessus du bloc 08:38 | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Recensement des formulations « un devis accepté produit un BC / nouveau BC indépendant » dans les documents de référence ; lecture des chemins réels | dépôt (lecture seule) | CDC §14 (ligne 453) et §16 (lignes 486-488), INV-40, modèle métier (lignes 181, 222, 745, 801), modèle V3.14 (ligne 366 du §4.7) | effectué | [FAIT-VÉRIFIÉ] |
| 3 | Sonde SQLite jetable en mémoire (aucun fichier écrit) : expression du CHECK des événements `acceptation` avec `bc_id` non NULL pour toute acceptation | scratchpad / mémoire (hors dépôt) | vérifier l'expression candidate avant de la consigner | effectuée : l'expression actuelle acceptait une acceptation initiale sans `bc_id` ; la candidate la refuse et ne change aucun autre des 17 cas essayés | [FAIT-VÉRIFIÉ] |
| 4 | Mise à jour des invariants (INV-40, INV-110, registre) | dépôt | refléter les décisions 1 et 2 | effectuée : INV-40 réécrit (rattachement à un BC créé ou existant, rattachement unique et immuable), INV-110 précisé (`bc_id` non NULL pour tout événement `acceptation`, même transaction, concordance par requête de contrôle), deux lignes du journal du registre avec les énoncés d'origine, version du registre 10 ; `990b0ea811688d04` → `a983a013397aff51` | [FAIT-VÉRIFIÉ] |
| 5 | Mise à jour du modèle de données V3.14 | dépôt | refléter les décisions 1, 2 et 3 ; T-55 | effectuée : en-tête (puce `historique`), ligne de garanties « un devis n'appartient qu'à un seul BC » du §4.7, §4.7 bis (rattachement à l'acceptation), §4.14 (`bc_id` non NULL pour toute acceptation, nouvelle clause d'écriture et de contrôles inter-tables, points ouverts, expression de référence du CHECK), liste des CK du §14 (CK-09 étendu), D-64, ligne T-55 ; `b389dbec78789215` → `02bf4a1ac3f36946` ; bloc CK-21 / CK-22 identique | [FAIT-VÉRIFIÉ] |
| 6 | Mise à jour du modèle métier | dépôt | corriger les formulations « un seul BC par devis » | effectuée : quatre lignes (181, 222, 745, 801) ; `3db0e15a95e052f0` → `9aa5ff44a45cfe17` | [FAIT-VÉRIFIÉ] |
| 7 | Complément d'E-22 dans les errata ; précédence dans les conventions §2 | dépôt | enregistrer la contradiction avec le CDC sans identifiant nouveau | effectuée : complément d'E-22 (cinq cellules et paragraphe de la section datée ; statut inchangé), `0459fef9a6683f37` → `c9c2cfc492c4d98d` ; conventions §2 : règle de précédence ajoutée (une puce et un paragraphe), `2be827c5aa6e3b5f` → `ed9c9c8d357307c4` (une correction d'espace après coup) ; aucun identifiant D, E, INV, CK, TR ou T créé | [FAIT-VÉRIFIÉ] |
| 8 | Vérification des diffs, complément de ce bloc (E, F) et clôture | dépôt, scratchpad | aucune modification hors périmètre | effectuée : contrôle au caractère près de chaque ligne modifiée (insertions, plus les remplacements voulus), CRLF uniforme, CDC, README, `CLAUDE.md`, migrations, tests et `fichiers-a-relire/` inchangés ; sauvegardes `journal.avant35` et `journal.avant36`, `docs_avant6\` | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
Relevé initial, recherches de texte, lectures Python, sonde SQLite en mémoire (voir B3). Aucun test du dépôt, aucune campagne de mutation, aucune commande Git modifiant l'état.

### D. Autorisation
**Instruction de Rémy (message du 2026-10-22)** : hiérarchie applicable (les invariants et le modèle V3.14 prévalent sur les documents contradictoires, qui doivent être corrigés) ; décision 1 (un BC peut regrouper plusieurs devis acceptés ; l'acceptation rattache le devis à un BC créé ou existant) ; décision 2 (`bc_id` identifie le BC de rattachement pour tout événement `acceptation`, CHECK `bc_id IS NOT NULL` quelle que soit la nature, même transaction, concordance contrôlée par le service et une requête de contrôle) ; décision 3 (contrôles de cohérence à placer sans les ajouter automatiquement à la migration 010) ; phase documentaire uniquement, sans SQL, test ni migration, puis arrêt avant `010_historique.sql`.

### E. Clôture — relevé final (2026-10-22 09:03)
- Git : `main`, HEAD `a99d4c2`, 26 entrées `git status` (identique à A), `git diff --stat` 9 fichiers +271 / −125 (+253 / −116 en A) [FAIT-VÉRIFIÉ]
- Fichiers modifiés depuis l'ouverture (`find -newermt "2026-10-22 08:59:00"`) : `invariants.md`, modèle V3.14, `cdc-errata-v6.md`, `modèle-métier-V6.md`, `conventions-techniques-v6.md` et ce journal — **aucun autre** [FAIT-VÉRIFIÉ]
- Empreintes inchangées : CDC `5937b7bcda5fcf91`, `docs/README.md` `54d5e5968218cef8`, `CLAUDE.md` `9a4c1f5d2a06a7aa`, `.claude/settings.local.json` `c49433832d9be741` ; agrégat des 15 migrations et des tests métier `1aec50f21bd38398` ; copies de travail de `fichiers-a-relire/` propres [FAIT-VÉRIFIÉ]
- Portée du relevé final : identique à A. **Non contrôlé :** identique au bloc 02:17.

### F. Réconciliation
- Écarts initial → final : les cinq documents officiels (B4 à B7) et ce journal (B1, B8) ; aucun autre écart sur la portée contrôlée.
- Registre B tenu : oui. **Verdict : CONCORDANT-NON-PROUVÉ** (portée : voir E). Fiabilité : COMPLET sur la portée indiquée.
- Statut documentaire : **aucun changement consigné comme acquis**. Les arbitrages du 2026-10-22 sont inscrits comme décisions du propriétaire dont la rédaction reste en relecture ; E-22 garde son statut ; le CDC n'est pas modifié ; `CLAUDE.md` §1 (conflit de hiérarchie « non résolu ») n'est pas modifié. Résiduels : INV-175 et CK-13 restent formulés pour un devis par BC ; modèle métier ligne 224 (« date de création (= date d'acceptation) ») contredit INV-176 / D-37 ; table cible de chaque `type_entite` et sens de `entite_id` pour `import` / `restauration` non précisés.
Clôture : CLÔTURÉE 2026-10-22 09:03

---

## Session 2026-10-22 08:38 — Claude Code — vérification de la règle `bc_id` des événements `acceptation` (analyse seule)
Clôture : CLÔTURÉE le 2026-10-22 à 08:38 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-22 08:38)
- `CLAUDE.md` (fourni au démarrage) ; dernier bloc du journal = 2026-10-22 04:14, CLÔTURÉE le 04:15, verdict CONCORDANT-NON-PROUVÉ, lu avant l'écriture de ce bloc [FAIT-VÉRIFIÉ]
- **Ouverture tardive** : ce bloc est écrit après les lectures de la session (la demande ne concernait que de la lecture) ; aucune écriture de dépôt n'a précédé ce bloc [FAIT-VÉRIFIÉ]
- État observé : `main`, HEAD `a99d4c2`, 26 entrées `git status`, `git diff --stat` 9 fichiers +253 / −116 ; empreintes `invariants.md` `990b0ea811688d04`, modèle V3.14 `b389dbec78789215`, `cdc-errata-v6.md` `0459fef9a6683f37`, `modèle-métier-V6.md` `3db0e15a95e052f0`, `conventions-techniques-v6.md` `2be827c5aa6e3b5f`, `CLAUDE.md` `9a4c1f5d2a06a7aa`, agrégat migrations + tests métier `1aec50f21bd38398` : identiques à la clôture du bloc 04:14 [FAIT-VÉRIFIÉ]
- Fichiers que cette session modifie : ce journal uniquement.

### B. Registre des actions
| # | Action | Cible | Après (résultat) | Statut |
|---|---|---|---|---|
| 1 | Lecture : CDC §14 (lignes 448-453) et §16 (lignes 482-490) ; INV-40, INV-175, INV-178, INV-207 ; modèle métier (lignes 181, 273, 801) ; modèle V3.14 (§4.7 « Partage des rôles à la création », §4.7 bis, §4.14) ; `005b` (`tr_99_bc_devis_*`) ; errata officiel (aucun erratum sur « nouveau BC indépendant ») ; erratum de travail E-16 (`fichiers-a-relire/MAJ__cdc-errata-v6.md`, ligne 23) | dépôt (lecture seule) | contradiction documentaire identifiée entre « un devis accepté produit un BC / nouveau BC indépendant » (CDC, INV-40, modèle métier) et le rattachement à un BC existant (modèle §4.7 bis, INV-207, migration 005b) ; arbitrage demandé à Rémy | [FAIT-VÉRIFIÉ] |
| 2 | Ce bloc | dépôt (`docs/suivi/journal-continuite.md`) | écrit | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
Lectures et recherches de texte, `git status`, `sha256sum`. Aucun test, aucune campagne de mutation, aucune commande Git modifiant l'état.

### D. Autorisation
Question de Rémy (message du 2026-10-22) : le `bc_id` d'un événement `acceptation` doit-il référencer le BC créé à l'acceptation initiale et le BC existant lors d'une réacceptation ? Vérifier au regard du cycle de vie devis → BC et des décisions C3, ne déduire aucune contrainte SQL non justifiée, signaler toute contradiction et attendre un arbitrage.

### E. Clôture — relevé final (2026-10-22 08:38)
- Aucune écriture hors ce journal ; empreintes des documents, des migrations et des tests identiques à A [FAIT-VÉRIFIÉ]
- Portée : suivis ☑ · empreintes ☑. **Non contrôlé :** identique au bloc 02:17.

### F. Réconciliation
- Écarts initial → final : ce journal seul. Registre B tenu : oui, avec ouverture tardive signalée en A. **Verdict : CONCORDANT-NON-PROUVÉ** (portée : voir E). Fiabilité : PARTIEL (ouverture tardive).
- Statut documentaire : aucun changement ; la contradiction signalée est en attente d'arbitrage de Rémy et n'est tranchée dans aucun document.

---

## Session 2026-10-22 04:14 — Claude Code — remplacement des formulations obsolètes « T-53 libre » dans trois documents de travail
Clôture : CLÔTURÉE le 2026-10-22 à 04:15 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-22 04:14, avant toute écriture de ce bloc)
- `CLAUDE.md` (fourni au démarrage) ; dernier bloc du journal = 2026-10-22 03:50, CLÔTURÉE le 03:53, verdict CONCORDANT-NON-PROUVÉ, lu avant toute autre action [FAIT-VÉRIFIÉ]
- État Git observé : `main`, HEAD `a99d4c2`, 26 entrées `git status` (identique à E du bloc 03:50) ; journal avant ouverture : SHA-256 `7ca1ce9774078e5d…` [FAIT-VÉRIFIÉ]
- Fichiers que cette session compte modifier (instruction de Rémy, message du 2026-10-22) : `reprise-autonome-v3.14-tranche-010/02_TRANCHE_010_CADRAGE.md` (ligne 91), `reprise-autonome-v3.14-tranche-010/03_TRANCHE_010_SQL_ET_TESTS.md` (ligne 99), `fichiers-a-relire/PLAN_MAJ_DOC__009a_regle_annulation_bc_V3.md` (ligne 191) ; ce journal. Rien d'autre.
- Portée du relevé : suivis ☑ (statut) · empreintes ☑ au relevé final. **Non contrôlé :** identique au bloc 02:17.

### B. Registre des actions
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (`docs/suivi/journal-continuite.md`) | insérer ce bloc au-dessus du bloc 03:50 | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Lecture des trois passages : l'affirmation obsolète (« T-53 libre ») figurait encore à côté du marqueur de correction ajouté à 03:50 | dépôt (lecture seule) | confirmer ou infirmer la présence de la formulation obsolète | confirmée pour les trois | [FAIT-VÉRIFIÉ] |
| 3 | Remplacement de chacune des trois lignes par une formulation directement correcte (historique conservé, marqué périmé, prochain numéro non utilisé explicite) | dépôt | aucune ambiguïté sur T-52, T-53, T-54, T-55 et le prochain numéro | effectué : `02_TRANCHE_010_CADRAGE.md` ligne 91 (`b6e7cbaf4b64a52e`), `03_TRANCHE_010_SQL_ET_TESTS.md` ligne 99 (`e25981b37e5c4dca`), `PLAN_MAJ_DOC__009a_regle_annulation_bc_V3.md` ligne 191 (`3611827ffd67ef8f`) ; la formulation « T-53 libre » est conservée entre guillemets et marquée périmée, le marqueur ajouté à 03:50 est absorbé dans la nouvelle formulation ; prochain numéro non utilisé : T-56 (recherche : aucune occurrence) ; dans la ligne 99 de `03`, « 011 » désignant la tranche `historique` devient « 010 depuis la décision du 2026-10-22 ; « 011 » dans la rédaction d'origine » | [FAIT-VÉRIFIÉ] |
| 4 | Vérification des diffs, complément de ce bloc (E, F) et clôture | dépôt, scratchpad | autres corrections inchangées | effectuée : empreintes identiques à celles de la clôture du bloc 03:50 pour le modèle V3.14, les conventions, `CLAUDE.md`, les deux fichiers restaurés de `fichiers-a-relire/`, `invariants.md`, `cdc-errata-v6.md` ; agrégat migrations et tests `1aec50f21bd38398` ; sauvegardes `journal.avant32` et `journal.avant33`, `docs_avant5\` (scratchpad) | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
Relevé initial (`git status`, `sha256sum`), lectures Python des trois lignes, recherche de « T-56 » (aucune occurrence dans `docs/`, `fichiers-a-relire/`, `reprise-autonome-v3.14-tranche-010/`, `src-tauri/`, `README.md`, `CLAUDE.md`). Aucun test, aucune commande Git modifiant l'état.

### D. Autorisation
**Instruction de Rémy (message du 2026-10-22)** : identifier les trois passages exacts, remplacer toute formulation obsolète présentant T-53 comme libre par une formulation correcte, sans ambiguïté sur le prochain numéro disponible, sans modifier d'autre fichier, migration, test ou identifiant, fournir le diff exact, confirmer que les autres corrections sont inchangées, puis s'arrêter avant `010_historique.sql`.

### E. Clôture — relevé final (2026-10-22 04:15)
- Git : `main`, HEAD `a99d4c2`, 26 entrées `git status` (identique à A) [FAIT-VÉRIFIÉ]
- Fichiers modifiés depuis l'ouverture : les trois documents de travail listés en A et ce journal ; les autres corrections n'ont pas bougé (empreintes en B4) [FAIT-VÉRIFIÉ]
- Portée du relevé final : identique à A. **Non contrôlé :** contenu des autres entrées non suivies autrement que par date, `node_modules/`, `.git/index`, `__pycache__/`.

### F. Réconciliation
- Écarts initial → final : trois lignes de documents de travail (B3) et ce journal (B1, B4) ; aucun autre écart sur la portée contrôlée.
- Registre B tenu : oui. **Verdict : CONCORDANT-NON-PROUVÉ** (portée : voir E). Fiabilité : COMPLET sur la portée indiquée.
- Statut documentaire : aucun changement ; aucun identifiant créé ou renuméroté (T-56 est cité comme prochain numéro non utilisé, sans attribution). Les occurrences de « prochain numéro libre » restent dans les enregistrements exclus (diff 011, annexes, transcriptions), non modifiés.
Clôture : CLÔTURÉE 2026-10-22 04:15

---

## Session 2026-10-22 03:50 — Claude Code — corrections documentaires décidées après la revue de la phase 1 (sans SQL)
Clôture : CLÔTURÉE le 2026-10-22 à 03:53 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-22 03:50, avant toute écriture de ce bloc)
- `CLAUDE.md` (fourni au démarrage) ; dernier bloc du journal = 2026-10-22 03:41, CLÔTURÉE le 03:42, verdict CONCORDANT-NON-PROUVÉ, lu avant toute autre action [FAIT-VÉRIFIÉ]
- Comparaison à l'état final du bloc 03:41 : Git `main`, HEAD `a99d4c2`, 27 entrées `git status`, `git diff --stat` 10 fichiers +255 / −114 ; empreintes `invariants.md` `990b0ea811688d04`, modèle V3.14 `d7d19285730a9fe3`, `cdc-errata-v6.md` `0459fef9a6683f37`, `modèle-métier-V6.md` `3db0e15a95e052f0`, `conventions-techniques-v6.md` `2e3fc5e2db9d4003`, `docs/README.md` `54d5e5968218cef8`, `CLAUDE.md` `1fc64bc79bd10606`, `.claude/settings.local.json` `c49433832d9be741`, `MAJ__conventions-techniques-v6.md` `2752bc9114493d3f`, `MAJ__modèle-données-sqlite-v6-v3.13.md` `47871582f30c912a`, `02_TRANCHE_010_CADRAGE.md` `cf7f43d844796378`, `03_TRANCHE_010_SQL_ET_TESTS.md` `29a86e1a33e095c1`, `PLAN_MAJ_DOC__009a_regle_annulation_bc_V3.md` `51e9d5178a89450b`, agrégat migrations + tests métier `1aec50f21bd38398` : aucun écart [FAIT-VÉRIFIÉ]
- Journal avant ouverture : SHA-256 `2a8894e92f445992…`
- Fichiers que cette session compte modifier (décisions du propriétaire, message du 2026-10-22) : `fichiers-a-relire/MAJ__conventions-techniques-v6.md` et `fichiers-a-relire/MAJ__modèle-données-sqlite-v6-v3.13.md` (restauration de l'état antérieur) ; `docs/conception/conventions-techniques-v6.md` (§5) ; `docs/conception/modèle-données-sqlite-v6-v3.14.md` (§4.14, T-55, note de numérotation des tests, D-64) ; `CLAUDE.md` (référence à la cellule T-53) ; `reprise-autonome-v3.14-tranche-010/02_TRANCHE_010_CADRAGE.md` et `03_TRANCHE_010_SQL_ET_TESTS.md`, `fichiers-a-relire/PLAN_MAJ_DOC__009a_regle_annulation_bc_V3.md` (affirmations « T-53 libre ») ; ce journal. Rien d'autre.
- Portée du relevé : suivis ☑ · empreintes ☑ · non suivis ☑ (par nom). **Non contrôlé :** identique au bloc 02:17.

### B. Registre des actions
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (`docs/suivi/journal-continuite.md`) | insérer ce bloc au-dessus du bloc 03:41 | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Retrait des deux notes de `fichiers-a-relire/` | dépôt | restaurer l'état antérieur exact (copie des sauvegardes, pas de commande Git) | effectuée : sauvegardes vérifiées identiques à HEAD (fins de ligne normalisées), `git diff` vide pour les deux fichiers ; empreintes `921fe251378a401c` (conventions MAJ) et `bc7e5a169a9de36f` (modèle V3.13 MAJ) | [FAIT-VÉRIFIÉ] |
| 3 | Précisions du modèle V3.14 (contournement observé avec `OFF`, T-55, T-52, D-64) | dépôt | documenter sans ajouter de trigger | effectuée : 4 lignes du modèle modifiées (paragraphe des triggers du §4.14 : dépendance `recursive_triggers=ON` et cas `OFF` ; ligne T-55 : liste des tests d'immutabilité et témoin `OFF` ; note de numérotation des tests : T-52 ; cellule d'alternatives de D-64), `d7d19285730a9fe3` → `b389dbec78789215`, CRLF uniforme, bloc CK-21 / CK-22 identique | [FAIT-VÉRIFIÉ] |
| 4 | Clarification du §5 de `conventions-techniques-v6.md` | dépôt | l'en-tête d'une migration cite la version courante du modèle | effectuée : une proposition modifiée dans la puce du §5 (`l’en-tête de la migration cite la version du modèle` devient `l’en-tête d’une migration cite la version courante du modèle, qu’elle soit validée ou en relecture`), `2e3fc5e2db9d4003` → `2be827c5aa6e3b5f` | [FAIT-VÉRIFIÉ] |
| 5 | Corrections ciblées des affirmations « T-53 libre » dans trois documents de travail | dépôt | marqueurs de correction, constats historiques conservés | effectuée : un marqueur ajouté en fin de ligne dans `02_TRANCHE_010_CADRAGE.md` (ligne 91, `35c4b63a58e6e71e`), `03_TRANCHE_010_SQL_ET_TESTS.md` (ligne 99, `9db8d4e92270c71e`) et `PLAN_MAJ_DOC__009a_regle_annulation_bc_V3.md` (ligne 191, `4ab0352cae06f2f5`) ; aucun texte retiré | [FAIT-VÉRIFIÉ] |
| 6 | Référence fragile de `CLAUDE.md` | dépôt | remplacer « ligne 938 » par l'identifiant T-53 et la section | effectuée : « cellule T-53 (ligne 938) » devient « cellule T-53 (§13.3, table des tests ajoutés) », `1fc64bc79bd10606` → `9a4c1f5d2a06a7aa` ; la ligne 6 (statut du fichier) n'est pas modifiée | [FAIT-VÉRIFIÉ] |
| 7 | Vérification des diffs avant / après, complément de ce bloc (E, F) et clôture | dépôt, scratchpad | aucune modification hors périmètre | effectuée : contrôle au caractère près de chaque ligne modifiée (insertions seulement, hormis le remplacement voulu de la liste « append-only » de T-55, du membre de phrase du §5 et de « ligne 938 ») ; sauvegardes `journal.avant30` (avant ouverture) et `journal.avant31` (avant clôture) | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
| Commande | Répertoire | Résultat | Portée / limites | Statut |
|---|---|---|---|---|
| Relevé initial (`git`, `sha256sum`, scripts Python de lecture) | racine | voir A | lecture seule | [FAIT-VÉRIFIÉ] |
Aucun test, aucune campagne de mutation, aucune commande Git modifiant l'état n'est lancé dans cette session.

### D. Autorisation
**Instruction de Rémy (message du 2026-10-22)** : appliquer uniquement les corrections décidées après la revue de la phase 1 — modèle V3.14 conservé (pas de V3.15, E-22 inchangé) ; retrait des deux notes de `fichiers-a-relire/` ; TR-60 et ses deux triggers conservés, pas de troisième trigger, dépendance à `recursive_triggers=ON` à vérifier par T-55 et cas `OFF` documenté ; aucun identifiant T renuméroté ; §5 des conventions, note de numérotation des tests, affirmations « T-53 libre », référence de `CLAUDE.md` corrigés ; mention historique de T-52 dans `test_009a` inchangée ; aucune migration ni aucun test modifié ; puis arrêt avant toute écriture de `010_historique.sql`. La modification de `CLAUDE.md` est explicitement demandée dans ce message.

### E. Clôture — relevé final (2026-10-22 03:53)
- Git : `main`, HEAD `a99d4c2`, indexé rien, stash 0 ; entrées `git status` : 26 (27 en A : les deux fichiers de `fichiers-a-relire/` restaurés redeviennent propres, `PLAN_MAJ_DOC__009a_regle_annulation_bc_V3.md` apparaît comme modifié) [FAIT-VÉRIFIÉ]
- Fichiers modifiés depuis l'ouverture (`find -newermt "2026-10-22 03:48:00"`) : `CLAUDE.md`, `conventions-techniques-v6.md`, modèle V3.14, `02_TRANCHE_010_CADRAGE.md`, `03_TRANCHE_010_SQL_ET_TESTS.md`, `PLAN_MAJ_DOC__009a_regle_annulation_bc_V3.md`, les deux fichiers restaurés (date de réécriture, contenu antérieur) et ce journal — **aucun autre** [FAIT-VÉRIFIÉ]
- Empreintes inchangées par rapport à A : `invariants.md` `990b0ea811688d04`, `cdc-errata-v6.md` `0459fef9a6683f37`, `modèle-métier-V6.md` `3db0e15a95e052f0`, `docs/README.md` `54d5e5968218cef8`, CDC `5937b7bcda5fcf91`, `.claude/settings.local.json` `c49433832d9be741` ; agrégat des 15 migrations et des tests métier `1aec50f21bd38398` (aucune migration, aucun test modifié ni créé) [FAIT-VÉRIFIÉ]
- Portée du relevé final : identique à A. **Non contrôlé :** contenu des autres entrées non suivies autrement que par date, `node_modules/`, `.git/index`, `__pycache__/`.

### F. Réconciliation
- Écarts initial → final : les sept documents listés en E (B2 à B6) et ce journal (B1, B7) ; aucun autre écart sur la portée contrôlée.
- Registre B tenu : oui. **Verdict : CONCORDANT-NON-PROUVÉ** (portée : voir E). Fiabilité : COMPLET sur la portée indiquée.
- Statut documentaire : **aucun changement de statut consigné comme acquis** ; E-22 inchangé ; la V3.14 reste le modèle courant en relecture ; aucune V3.15. `CLAUDE.md` a été modifié sur instruction explicite de Rémy : sa ligne 6 (statut et historique des clarifications) n'a pas été mise à jour, à décider par Rémy. Résiduel : la puce du §5 des conventions conserve « passe à la version suivante », que la pratique des versions en relecture nuance ; seule la clause de l'en-tête a été précisée.
Clôture : CLÔTURÉE 2026-10-22 03:53

---

## Session 2026-10-22 03:41 — Claude Code — revue ciblée de la phase 1 `historique` avant SQL (analyse seule)
Clôture : CLÔTURÉE le 2026-10-22 à 03:42 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-22 03:41)
- `CLAUDE.md` (fourni au démarrage) ; dernier bloc du journal = 2026-10-22 03:17, CLÔTURÉE le 03:20, verdict CONCORDANT-NON-PROUVÉ, lu avant toute autre action [FAIT-VÉRIFIÉ]
- Comparaison à l'état final du bloc 03:17 : Git `main`, HEAD `a99d4c2`, 27 entrées `git status`, `git diff --stat` 10 fichiers +255 / −114 ; empreintes `invariants.md` `990b0ea811688d04`, modèle V3.14 `d7d19285730a9fe3`, `cdc-errata-v6.md` `0459fef9a6683f37`, `modèle-métier-V6.md` `3db0e15a95e052f0`, `conventions-techniques-v6.md` `2e3fc5e2db9d4003`, `docs/README.md` `54d5e5968218cef8`, `CLAUDE.md` `1fc64bc79bd10606`, `.claude/settings.local.json` `c49433832d9be741`, `MAJ__conventions-techniques-v6.md` `2752bc9114493d3f`, `MAJ__modèle-données-sqlite-v6-v3.13.md` `47871582f30c912a`, agrégat migrations + tests métier `1aec50f21bd38398` : aucun écart [FAIT-VÉRIFIÉ]
- Journal avant ouverture : SHA-256 `fc07b7ed2d5056c6…`
- Fichiers que cette session compte modifier : ce journal uniquement (revue sans modification des documents).
- Portée du relevé : suivis ☑ · empreintes ☑ · non suivis ☑ (par nom). **Non contrôlé :** identique au bloc 02:17.

### B. Registre des actions
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (`docs/suivi/journal-continuite.md`) | insérer ce bloc au-dessus du bloc 03:17 | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Lectures : conventions §5 / §12 ; rangs et versions de modèle cités par les en-têtes des 15 migrations ; README ; références à `V3.14` dans le dépôt ; historique Git des fichiers de modèle ; diffs des deux fichiers de `fichiers-a-relire/` (lecture `git diff`) ; recensement des occurrences de T-52 et T-53 | dépôt (lecture seule) | répondre aux quatre points de la revue | effectuées | [FAIT-VÉRIFIÉ] |
| 3 | Sondes SQLite jetables `probe_historique.py` et deux sondes en ligne (DDL du §4.14 lu dans le modèle, listes d'énumération extraites du modèle) | scratchpad (hors dépôt) | observer `UPDATE`, `DELETE`, `REPLACE`, `UPSERT`, `INSERT OR IGNORE` avec `recursive_triggers` actif et inactif ; essayer un trigger de renfort | exécutées ; résultats dans la réponse | [FAIT-VÉRIFIÉ] |
| 4 | Complément de ce bloc (E, F) et clôture | ce journal | relevé final et réconciliation | effectué ; sauvegardes `journal.avant28` (avant ouverture) et `journal.avant29` (avant clôture), scratchpad | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
| Commande | Répertoire | Résultat | Portée / limites | Statut |
|---|---|---|---|---|
| `python -I -B probe_historique.py` et sondes Python en ligne (bases en mémoire) ; `git diff --no-color` limité aux deux fichiers de `fichiers-a-relire/` ; `git log` ; recherches de texte | racine, scratchpad | voir réponse | sondes jetables hors dépôt ; aucune commande Git modifiant l'état ; SQLite 3.50.4 seulement | [FAIT-VÉRIFIÉ] |
Aucun test du dépôt, aucune campagne de mutation.

### D. Autorisation
**Instruction de Rémy (message du 2026-10-22)** : revue ciblée de la phase 1 avant SQL — version du modèle, diffs et pertinence des deux fichiers de `fichiers-a-relire/`, immutabilité de `historique` sur base temporaire, cohérence de T-52 / T-53 — sans créer ni modifier migration, test ou document, sans travail sur C3, puis arrêt pour validation de Rémy.

### E. Clôture — relevé final (2026-10-22 03:42)
- Git : `main`, HEAD `a99d4c2`, 27 entrées `git status`, `git diff --stat` 10 fichiers +255 / −114 : identiques au relevé initial de ce bloc [FAIT-VÉRIFIÉ]
- Empreintes, agrégat migrations / tests et fichiers modifiés depuis l'ouverture : relevé final comparé à A avant clôture, résultat en F [FAIT-VÉRIFIÉ]
- Portée du relevé final : identique à A. **Non contrôlé :** identique au bloc 02:17.

### F. Réconciliation
- Écarts initial → final : ce journal seul (B1, B4) ; aucun document, aucune migration, aucun test modifié.
- Registre B tenu : oui. **Verdict : CONCORDANT-NON-PROUVÉ** (portée : voir E). Fiabilité : COMPLET sur la portée indiquée.
- Statut documentaire : aucun changement ; les propositions présentées à Rémy (version du modèle, retrait des deux notes de `fichiers-a-relire/`, renforcement éventuel du DDL d'`historique`, précision de T-55) ne sont pas appliquées. Constat à retenir : avec `recursive_triggers=OFF`, un `INSERT OR REPLACE` sur un identifiant existant écrase une ligne d'`historique` (sonde) ; avec `ON`, il est refusé.
Clôture : CLÔTURÉE 2026-10-22 03:42

---

## Session 2026-10-22 03:17 — Claude Code — phase 1 : cadrage documentaire de la tranche `historique` (`010_historique.sql`, rang 16)
Clôture : CLÔTURÉE le 2026-10-22 à 03:20 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-22 03:17, avant toute écriture de ce bloc)
- `CLAUDE.md` (fourni au démarrage) ; dernier bloc du journal = 2026-10-22 02:55, CLÔTURÉE le 02:56, verdict CONCORDANT-NON-PROUVÉ, lu avant toute autre action [FAIT-VÉRIFIÉ]
- Comparaison à l'état final du bloc 02:55 : Git `main`, HEAD `a99d4c2`, indexé rien, 25 entrées `git status`, `git diff --stat` 8 fichiers +186 / −108 ; empreintes `invariants.md` `9c61d36d2909c958`, `cdc-errata-v6.md` `0459fef9a6683f37`, `modèle-métier-V6.md` `3db0e15a95e052f0`, modèle V3.14 `958a3c0dfc627840`, `conventions-techniques-v6.md` `2e3fc5e2db9d4003`, `docs/README.md` `54d5e5968218cef8`, `CLAUDE.md` `1fc64bc79bd10606`, `.claude/settings.local.json` `c49433832d9be741`, agrégat migrations + tests métier `1aec50f21bd38398` ; 15 fichiers de migration métier : aucun écart [FAIT-VÉRIFIÉ]
- Journal avant ouverture : SHA-256 `915af2d8486334c0…`
- Fichiers que cette session compte modifier (autorisation de Rémy, message du 2026-10-22) : `docs/conception/modèle-données-sqlite-v6-v3.14.md`, `docs/conception/invariants.md` ; documents de travail concernés par la réservation de 010 à la planification (`reprise-autonome-v3.14-tranche-010/` : `00_LIRE_EN_PREMIER.md`, `02_TRANCHE_010_CADRAGE.md`, `03_TRANCHE_010_SQL_ET_TESTS.md`, `05_MATRICE_TRACABILITE.md`, `07_REPRISE_NOUVELLE_SESSION.md` ; `fichiers-a-relire/` : `MAJ__modèle-données-sqlite-v6-v3.13.md`, `MAJ__conventions-techniques-v6.md`) ; ce journal. Les diffs, patchs, messages d'utilisateur et annexes de ces dossiers restent des enregistrements historiques non modifiés.
- Portée du relevé : suivis ☑ · empreintes ☑ (documents ci-dessus, agrégat migrations/tests) · non suivis ☑ (par nom). **Non contrôlé :** identique au bloc 02:17.

### B. Registre des actions
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (`docs/suivi/journal-continuite.md`) | insérer ce bloc au-dessus du bloc 02:55 | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Vérifications préalables : plus hauts identifiants D / T / CK / TR employés dans `docs/`, `fichiers-a-relire/`, `reprise-autonome-*`, `src-tauri/`, `README.md`, `CLAUDE.md` ; confrontation des 18 événements au modèle métier §26, INV-110, CDC ; recensement des documents de travail qui réservent 010 à la planification | dépôt (lecture seule) | attribuer D-64 et T-55 sans collision ; fonder l'énumération | effectuées (voir réponse) | [FAIT-VÉRIFIÉ] |
| 3 | Mise à jour de `invariants.md` (INV-110, ligne de journal du registre, version du registre) | dépôt | rendre obligatoire la traçabilité des acceptations et définir la structure des événements | effectuée : 52379 puis 53838 octets (après le lot précédent, 53838 est l'état courant), `990b0ea811688d04…`, CRLF uniforme ; INV-110 réécrit (acceptation obligatoire, structure de `donnees`, CHECK local, T-55) ; ligne du journal des modifications du registre avec l'ancien énoncé ; version du registre 9 ; aucun autre INV modifié | [FAIT-VÉRIFIÉ] |
| 4 | Mise à jour du modèle V3.14 (§4.14, TR-60, index, §13.3, §15, §17.1, en-tête) | dépôt | spécifier `historique` et positionner la tranche | effectuée : 177319 → 187771 octets, `d7d19285730a9fe3…`, CRLF uniforme ; §4.14 réécrit (colonnes, contraintes, énumérations définitives, CHECK conditionnel avec expression de référence, index, TR-60, tranche) ; ligne TR-60 ; noms des index ; D-64 (§15) ; T-55 (§13.3) ; ligne `010_historique.sql` au §17.1 et positionnement ; bullet d'en-tête et ligne de la table des versions ; bloc CK-21 / CK-22 strictement identique (extraction du test 12 comparée avant / après) | [FAIT-VÉRIFIÉ] |
| 5 | Notes de correction de numérotation dans les documents de travail concernés | dépôt (`reprise-autonome-*`, `fichiers-a-relire/`) | 010 = historique, 011 = planification ; contenus historiques conservés | effectuée dans 7 documents de travail : note de tête dans `00_LIRE_EN_PREMIER`, `02_TRANCHE_010_CADRAGE`, `03_TRANCHE_010_SQL_ET_TESTS`, `05_MATRICE_TRACABILITE`, `07_REPRISE_NOUVELLE_SESSION` (dossier `reprise-autonome-v3.14-tranche-010/`) et dans `MAJ__modèle-données-sqlite-v6-v3.13.md`, `MAJ__conventions-techniques-v6.md` (`fichiers-a-relire/`) ; cinq marqueurs « corrigé » sur des lignes qui attribuaient un rang (05 : lignes des tranches 010 et 011 ; 07 : étape 3 ; 02 : ligne 011 ; 03 : tranche suivante) ; sauvegardes dans `scratchpad\travail_avant\` ; diffs, patchs, messages d'utilisateur, annexes et rapports non modifiés | [FAIT-VÉRIFIÉ] |
| 6 | Contrôles de cohérence croisée, complément de ce bloc (E, F) et clôture | dépôt, scratchpad | vérifier références, fins de ligne, empreintes | effectuée (voir E) ; sauvegardes du journal `journal.avant26` (avant ouverture) et `journal.avant27` (avant clôture) | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
| Commande | Répertoire | Résultat | Portée / limites | Statut |
|---|---|---|---|---|
| Relevé initial (`git`, `sha256sum`, scripts Python de lecture), recherches d'identifiants et de références | racine | voir A et B2 | lecture seule | [FAIT-VÉRIFIÉ] |
Scripts d'application dans le scratchpad (hors dépôt) : `apply_hist_inv.py`, `apply_hist_model.py`, `apply_hist_travail.py`, avec contrôle des ancrages avant écriture. Une sonde SQLite jetable supplémentaire a validé l'expression du CHECK conditionnel avec `json_valid` (21 cas). Aucun test du dépôt, aucune campagne de mutation, aucune commande Git modifiant l'état n'est lancé dans cette session.

### D. Autorisation
**Instruction de Rémy (message du 2026-10-22, phase 1)** : décisions validées — `010_historique.sql` rang 16 ; `010a_reacceptation_devis.sql` rang 17 mais hors périmètre ; planification décalée à 011 dans les documents de travail ; `historique` livrée avant l'activation de la réacceptation ; aucune dérogation à l'interdiction des triggers de miroir ; aucune migration ni aucun test créé. Travail : spécifier `historique` dans le modèle SQLite de référence (colonnes, énumérations, JSON, dates, index, TR-60, structure conditionnelle des événements `acceptation`), modifier INV-110, mettre à jour le positionnement et le suivi, corriger uniquement les documents de travail concernés, vérifier la cohérence, sans présenter la décision comme officiellement validée, puis s'arrêter pour la revue de Rémy.

### E. Clôture — relevé final (2026-10-22 03:20)
- Git : `main`, HEAD `a99d4c2`, indexé rien, stash 0 ; entrées `git status` : 27 (25 en A : `fichiers-a-relire/MAJ__conventions-techniques-v6.md` et `fichiers-a-relire/MAJ__modèle-données-sqlite-v6-v3.13.md` apparaissent comme modifiés ; `reprise-autonome-v3.14-tranche-010/` était déjà non suivi) ; `git diff --stat` : 10 fichiers, +255 / −114 (8 fichiers, +186 / −108 en A) [FAIT-VÉRIFIÉ]
- Fichiers modifiés depuis l'ouverture (`find -newermt "2026-10-22 03:15:00"`, hors `node_modules`, `.git`) : les 2 documents officiels, les 7 documents de travail annoncés en A et ce journal — **aucun autre** [FAIT-VÉRIFIÉ]
- Empreintes modifiées, attendues : `invariants.md` `9c61d36d2909c958` → `990b0ea811688d04` ; modèle V3.14 `958a3c0dfc627840` → `d7d19285730a9fe3` [FAIT-VÉRIFIÉ]
- Empreintes inchangées par rapport à A : `cdc-errata-v6.md` `0459fef9a6683f37`, `modèle-métier-V6.md` `3db0e15a95e052f0`, CDC `5937b7bcda5fcf91`, `docs/README.md` `54d5e5968218cef8`, `conventions-techniques-v6.md` `2e3fc5e2db9d4003`, `CLAUDE.md` `1fc64bc79bd10606`, `.claude/settings.local.json` `c49433832d9be741` ; agrégat des 15 migrations et des tests métier `1aec50f21bd38398` (aucune migration créée ou modifiée, aucun test créé ou modifié) [FAIT-VÉRIFIÉ]
- Contrôles de cohérence (lecture seule) : CRLF uniforme dans les deux documents officiels ; références INV du §4.14 (INV-102, INV-110, INV-111, INV-175, INV-206) toutes présentes au registre ; D-64 et T-55 présents une seule fois comme lignes de tableau dans le modèle, absents ailleurs avant ce lot ; énumération de 18 événements confrontée au modèle métier §26 (correspondance une à une) ; seul test lisant un document (`test_009b_couverture_situations`, test 12) : extraction « -- CK-21 : » inchangée [FAIT-VÉRIFIÉ]
- Portée du relevé final : identique à A. **Non contrôlé :** contenu des autres entrées non suivies autrement que par date, `node_modules/`, `.git/index`, `__pycache__/`.

### F. Réconciliation
- Écarts initial → final : les deux documents officiels (B3, B4), les sept documents de travail (B5) et ce journal (B1, B6) ; aucun autre écart sur la portée contrôlée.
- Registre B tenu : oui. **Verdict : CONCORDANT-NON-PROUVÉ** (portée : voir E). Fiabilité : COMPLET sur la portée indiquée.
- Statut documentaire : **aucun changement consigné comme acquis**. D-64 est une décision du propriétaire dont la rédaction reste en relecture ; la version du modèle n'est pas renumérotée ; aucun document de référence n'est promu. Contradictions résiduelles à signaler : texte de D-34 (« historique … non positionnés ») complété par D-64 sans être modifié ; ligne « Tranches suivantes » du §17.1 antérieure à la livraison des tranches 005 à 009 ; numéros T-52 / T-53 employés différemment dans les documents de travail.
Clôture : CLÔTURÉE 2026-10-22 03:20

---

## Session 2026-10-22 02:55 — Claude Code — cadrage de la tranche `historique` et de la migration corrective C3 (analyse seule)
Clôture : CLÔTURÉE le 2026-10-22 à 02:56 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-22 02:55)
- `CLAUDE.md` (fourni au démarrage) ; dernier bloc du journal = 2026-10-22 02:48, CLÔTURÉE, verdict CONCORDANT-NON-PROUVÉ, lu avant toute autre action [FAIT-VÉRIFIÉ]
- Comparaison à l'état final du bloc 02:48 : Git `main`, HEAD `a99d4c2`, 25 entrées `git status`, `git diff --stat` 8 fichiers +186 / −108 ; empreintes `invariants.md` `9c61d36d2909c958`, `cdc-errata-v6.md` `0459fef9a6683f37`, `modèle-métier-V6.md` `3db0e15a95e052f0`, modèle V3.14 `958a3c0dfc627840`, `CLAUDE.md` `1fc64bc79bd10606`, `.claude/settings.local.json` `c49433832d9be741`, agrégat migrations + tests métier `1aec50f21bd38398` ; 15 fichiers de migration métier : aucun écart [FAIT-VÉRIFIÉ]
- Journal avant ouverture : SHA-256 `e7874ae4c5035017…`
- Fichiers que cette session compte modifier dans le dépôt : ce journal uniquement.
- Portée du relevé : suivis ☑ · empreintes ☑ (documents ci-dessus, agrégat migrations/tests). **Non contrôlé :** identique au bloc 02:17.

### B. Registre des actions
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (`docs/suivi/journal-continuite.md`) | insérer ce bloc au-dessus du bloc 02:48 | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Lectures : rangs `PRAGMA user_version` des 15 migrations livrées ; tests qui énumèrent les migrations (`test_005a` à `test_009c`, dont `test_009c` H et `test_009a`) ; helpers de population de `test_009c` ; INV-110 / INV-111, modèle V3.14 (§2.5, §4.14, §17.1, D-34), conventions §5 / §7.1 / §9 ; dossier `reprise-autonome-v3.14-tranche-010` et `fichiers-a-relire/` (non référence, lecture seule : collisions de numéros) | dépôt (lecture seule) | fonder le cadrage sur la chaîne réellement livrée | effectuées | [FAIT-VÉRIFIÉ] |
| 3 | Sondes SQLite jetables : CHECK conditionnel des événements `acceptation` (deux versions) | scratchpad (hors dépôt) | valider le comportement des CHECK avec NULL avant de le proposer | exécutées ; la première version laissait passer des cas invalides (CHECK évalué à NULL) ; seconde version conforme | [FAIT-VÉRIFIÉ] |
| 4 | Complément de ce bloc (E, F) et clôture | ce journal | relevé final et réconciliation | effectué ; sauvegardes `journal.avant24` (avant ouverture) et `journal.avant25` (avant clôture), scratchpad | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
| Commande | Répertoire | Résultat | Portée / limites | Statut |
|---|---|---|---|---|
| `python -I -B probe_ck_accept.py` et `probe_ck_accept2.py` (base en mémoire) | scratchpad | voir réponse | sondes jetables, aucune base du dépôt, aucun test du dépôt | [FAIT-VÉRIFIÉ] |
Aucun test du dépôt, aucune campagne de mutation, aucune commande Git modifiant l'état.

### D. Autorisation
**Instruction de Rémy (message du 2026-10-22)** : orientations de cadrage (O1 avec W = 1 000 000 ; tranche `historique` dédiée avec CHECK conditionnel local ; porte de fermeture du jeton sans dérogation acquise ; règles métier de P2 conservées) et livrable attendu : cadrage complet de la tranche `historique` puis de la migration corrective C3, sans modifier document officiel, migration, test ni état Git avant validation explicite.

### E. Clôture — relevé final (2026-10-22 02:56)
- Git : `main`, HEAD `a99d4c2`, 25 entrées `git status`, `git diff --stat` 8 fichiers +186 / −108 : identiques au relevé initial de ce bloc [FAIT-VÉRIFIÉ]
- Empreintes des documents, de `CLAUDE.md`, de `.claude/settings.local.json` et agrégat migrations / tests métier : relevé final comparé à A avant clôture ; résultat consigné en F [FAIT-VÉRIFIÉ]
- Portée du relevé final : identique à A. **Non contrôlé :** identique au bloc 02:17.

### F. Réconciliation
- Écarts initial → final : ce journal seul (B1, B4) ; aucun document officiel, aucune migration, aucun test modifié.
- Registre B tenu : oui. **Verdict : CONCORDANT-NON-PROUVÉ** (portée : voir E). Fiabilité : COMPLET sur la portée indiquée.
- Statut documentaire : aucun changement ; le cadrage présenté à Rémy est une proposition non intégrée. Précisions à retenir : la première version du CHECK conditionnel des événements d'acceptation laissait passer des cas invalides (évaluation à NULL), corrigée par des tests `IS` / `COALESCE` ; tous les CHECK de la future migration devront être écrits ainsi et couverts par la campagne de mutation.
Clôture : CLÔTURÉE 2026-10-22 02:56

---

## Session 2026-10-22 02:48 — Claude Code — ordre des lignes du BC, périmètre de la migration `historique`, vérification du jeton (analyse seule)
Clôture : CLÔTURÉE le 2026-10-22 à 02:48 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-22 02:48)
- `CLAUDE.md` (fourni au démarrage) ; dernier bloc du journal = 2026-10-22 02:36, CLÔTURÉE, verdict CONCORDANT-NON-PROUVÉ, lu avant toute autre action [FAIT-VÉRIFIÉ]
- Comparaison à l'état final du bloc 02:36 : Git `main`, HEAD `a99d4c2`, 25 entrées `git status`, `git diff --stat` 8 fichiers +186 / −108 ; empreintes `invariants.md` `9c61d36d2909c958`, `cdc-errata-v6.md` `0459fef9a6683f37`, `modèle-métier-V6.md` `3db0e15a95e052f0`, modèle V3.14 `958a3c0dfc627840`, `CLAUDE.md` `1fc64bc79bd10606`, `.claude/settings.local.json` `c49433832d9be741`, agrégat migrations + tests métier `1aec50f21bd38398` : aucun écart [FAIT-VÉRIFIÉ]
- Journal avant ouverture : SHA-256 `61bab399e7a629e6…`
- Fichiers que cette session compte modifier dans le dépôt : ce journal uniquement.
- Portée du relevé : suivis ☑ · empreintes ☑ (documents ci-dessus, agrégat migrations/tests). **Non contrôlé :** identique au bloc 02:17.

### B. Registre des actions
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (`docs/suivi/journal-continuite.md`) | insérer ce bloc au-dessus du bloc 02:36 | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Lectures : modèle V3.14 (§4.14, §2.5, index, TR-60, §17.1), INV-110 / INV-111, conventions §5 / §7.1 / §9, `test_004`, `test_005b`, `test_006` (helpers de copie des lignes de BC), migrations 005b / 006 / 008 / 009b, dossier `reprise-autonome-v3.14-tranche-010` (non référence, lecture seule) | dépôt (lecture seule) | répondre aux deux points demandés | effectuées | [FAIT-VÉRIFIÉ] |
| 3 | Sondes SQLite jetables (`probe_jeton2.py` et trois sondes en ligne : stratégies d'`ordre`, matrice opérations × étapes) | scratchpad (hors dépôt) | vérifier jeton, rollback, commit avec jeton, réglages, diagnostic ; chiffrer les collisions d'`ordre` | exécutées ; résultats dans la réponse | [FAIT-VÉRIFIÉ] |
| 4 | Complément de ce bloc (E, F) et clôture | ce journal | relevé final et réconciliation | effectué ; sauvegardes `journal.avant22` (avant ouverture) et `journal.avant23` (avant clôture), scratchpad | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
| Commande | Répertoire | Résultat | Portée / limites | Statut |
|---|---|---|---|---|
| `python -I -B probe_jeton2.py` et sondes Python en ligne (bases temporaires ou en mémoire) | scratchpad | voir réponse ; une première exécution a échoué sur l'amorçage des données (garde de facture active), corrigée avant exploitation ; une première matrice comptait à tort des instructions sans effet (0 ligne), refaite avec contrôle du nombre de lignes affectées | sondes jetables, aucune base du dépôt, aucun test du dépôt | [FAIT-VÉRIFIÉ] |
Aucun test du dépôt, aucune campagne de mutation, aucune commande Git modifiant l'état.

### D. Autorisation
**Instruction de Rémy (message du 2026-10-22)** : P2 retenue comme orientation ; traiter uniquement (1) la comparaison des stratégies d'ordre des lignes du BC et (2) le périmètre minimal de la migration `historique` avec une vérification ciblée du jeton, sans modifier document officiel, migration, test ni état Git, puis s'arrêter pour validation de Rémy.

### E. Clôture — relevé final (2026-10-22 02:48)
- Git : `main`, HEAD `a99d4c2`, 25 entrées `git status`, `git diff --stat` 8 fichiers +186 / −108 : identiques au relevé initial de ce bloc [FAIT-VÉRIFIÉ]
- Empreintes des documents, de `CLAUDE.md`, de `.claude/settings.local.json` et agrégat migrations / tests métier : relevé final comparé à A avant clôture ; résultat consigné en F [FAIT-VÉRIFIÉ]
- Portée du relevé final : identique à A. **Non contrôlé :** identique au bloc 02:17.

### F. Réconciliation
- Écarts initial → final : ce journal seul (B1, B4) ; aucun document officiel, aucune migration, aucun test modifié.
- Registre B tenu : oui. **Verdict : CONCORDANT-NON-PROUVÉ** (portée : voir E). Fiabilité : COMPLET sur la portée indiquée.
- Statut documentaire : aucun changement ; les conclusions présentées à Rémy sont des propositions non intégrées. Corrections à signaler par rapport aux comptes rendus précédents : (1) la porte de fermeture G, proposée comme trigger comparant devis et BC, est en tension avec conventions §9 et INV-175 (« jamais un trigger de miroir ») ; (2) l'insertion liée au contenu JSON est un renforcement optionnel, non une base ; (3) la première matrice de la sonde ne couvrait que l'étape 0 et comptait des instructions sans effet, refaite.
Clôture : CLÔTURÉE 2026-10-22 02:48

---

## Session 2026-10-22 02:36 — Claude Code — résolution des quatre points techniques avant cadrage de la migration corrective C2/C3 (analyse seule)
Clôture : CLÔTURÉE le 2026-10-22 à 02:36 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-22 02:36)
- `CLAUDE.md` (fourni au démarrage) ; dernier bloc du journal = 2026-10-22 02:29, CLÔTURÉE, verdict CONCORDANT-NON-PROUVÉ, lu avant toute autre action [FAIT-VÉRIFIÉ]
- Comparaison à l'état final du bloc 02:29 : Git `main`, HEAD `a99d4c2`, indexé rien, stash 0, 25 entrées `git status`, `git diff --stat` 8 fichiers +186 / −108 ; empreintes `invariants.md` `9c61d36d2909c958`, `cdc-errata-v6.md` `0459fef9a6683f37`, `modèle-métier-V6.md` `3db0e15a95e052f0`, modèle V3.14 `958a3c0dfc627840`, `CLAUDE.md` `1fc64bc79bd10606`, `.claude/settings.local.json` `c49433832d9be741`, agrégat migrations + tests métier `1aec50f21bd38398` : aucun écart [FAIT-VÉRIFIÉ]
- Fichiers que cette session compte modifier dans le dépôt : ce journal uniquement.
- Portée du relevé : suivis ☑ · empreintes ☑ (documents ci-dessus, agrégat migrations/tests). **Non contrôlé :** identique au bloc 02:17.

### B. Registre des actions
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (`docs/suivi/journal-continuite.md`) | insérer ce bloc au-dessus du bloc 02:29 | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Lectures : migrations 003, 004, 005a, 005b, 006, 008, 009b (clés étrangères vers `bc_lignes` / `devis_lignes`, triggers d'insertion des garanties et retraits), `test_004` et `test_005b` (requête CK-13, copie des lignes multi-devis), modèle V3.14 (§4.7, §4.14, CK-13), INV-175 / INV-176, conventions (réglages de connexion) | dépôt (lecture seule) | répondre aux quatre points techniques | effectuées | [FAIT-VÉRIFIÉ] |
| 3 | Sonde SQLite jetable `probe_jeton.py` (base temporaire hors dépôt) : jeton transactionnel, FK différée, `RESTRICT`, `json_each` dans un trigger | scratchpad (hors dépôt) | vérifier le comportement réel de SQLite 3.50.4 avant de le proposer | exécutée ; résultats dans la réponse | [FAIT-VÉRIFIÉ] |
| 4 | Complément de ce bloc (E, F) et clôture | ce journal | relevé final et réconciliation | effectué ; sauvegardes `journal.avant20` (avant ouverture) et `journal.avant21` (avant clôture), scratchpad | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
| Commande | Répertoire | Résultat | Portée / limites | Statut |
|---|---|---|---|---|
| `python -I -B probe_jeton.py` et deux sondes en mémoire (comportement de `RESTRICT` avec et sans `PRAGMA defer_foreign_keys`) | scratchpad | voir réponse ; première exécution du jeton invalide (colonne de contrainte différée nullable, donc sans effet) corrigée avant exploitation | sonde jetable, aucune base du dépôt, aucun test du dépôt | [FAIT-VÉRIFIÉ] |
Aucun test du dépôt, aucune campagne de mutation, aucune commande Git modifiant l'état.

### D. Autorisation
**Instruction de Rémy (message du 2026-10-22)** : intégrer les arbitrages Q1 à Q3 et résoudre quatre points techniques (fenêtre d'autorisation F/G, ordre des lignes du BC, historique des acceptations, périmètre des garanties), sans modifier document officiel, migration, test ni état Git, puis s'arrêter pour validation de Rémy.

### E. Clôture — relevé final (2026-10-22 02:36)
- Git : `main`, HEAD `a99d4c2`, 25 entrées `git status`, `git diff --stat` 8 fichiers +186 / −108 : identiques au relevé initial de ce bloc [FAIT-VÉRIFIÉ]
- Empreintes (documents, `CLAUDE.md`, `.claude/settings.local.json`, agrégat migrations et tests métier) : à comparer à A ; relevé final effectué avant clôture, voir F [FAIT-VÉRIFIÉ]
- Portée du relevé final : identique à A. **Non contrôlé :** identique au bloc 02:17.

### F. Réconciliation
- Écarts initial → final : ce journal seul (B1, B4) ; aucun document officiel, aucune migration, aucun test modifié.
- Registre B tenu : oui. **Verdict : CONCORDANT-NON-PROUVÉ** (portée : voir E). Fiabilité : COMPLET sur la portée indiquée.
- Statut documentaire : aucun changement ; les réponses présentées à Rémy sont des propositions non intégrées. Correction à signaler : une affirmation du compte rendu de 02:29 (« la clé `RESTRICT` est immédiate même si les clés étrangères sont différées ») est exacte pour une contrainte déclarée différée mais inexacte avec `PRAGMA defer_foreign_keys=ON` (sonde de cette session).
Clôture : CLÔTURÉE 2026-10-22 02:36

---

## Session 2026-10-22 02:29 — Claude Code — mise au point ciblée sur quatre réserves de la proposition C2/C3 (analyse seule)
Clôture : CLÔTURÉE le 2026-10-22 à 02:28 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-22 02:29)
- `CLAUDE.md` (fourni au démarrage) ; dernier bloc du journal = 2026-10-22 02:17, CLÔTURÉE le 02:22, verdict CONCORDANT-NON-PROUVÉ, lu avant toute autre action [FAIT-VÉRIFIÉ]
- État Git observé au démarrage de ce bloc : `main`, HEAD `a99d4c2`, 25 entrées `git status` (identique à E du bloc 02:17) [FAIT-VÉRIFIÉ] ; les empreintes seront rapprochées de celles du bloc 02:17 au relevé final.
- Fichiers que cette session compte modifier : ce journal uniquement.
- Portée : suivis ☑ (statut) · empreintes ☑ au relevé final. **Non contrôlé :** identique au bloc 02:17.

### B. Registre des actions
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (`docs/suivi/journal-continuite.md`) | insérer ce bloc au-dessus du bloc 02:17 | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Lectures complémentaires des migrations (003, 004, 005b, 006, 008, 009b : clés étrangères vers `bc_lignes` et `devis_lignes`, triggers d'insertion des garanties) et du CDC §14 | dépôt (lecture seule) | quatre compléments : stockage des révisions en attente, formulation de précédence, ordre de réacceptation, dates et snapshots | effectuées ; constats utilisés : `bc_ligne_garanties`, `garanties` et `bc_ligne_retraits_garantie` référencent `bc_lignes` en `RESTRICT` ; les triggers d'insertion des garanties n'exigent aucune facture ; CDC §14 lignes 428-449 ; V3.12 §7 ligne 565 et TR-15 ligne 608 | [FAIT-VÉRIFIÉ] |
| 3 | Complément de ce bloc (E, F) et clôture | ce journal | relevé final et réconciliation | effectué ; sauvegardes `journal.avant18` et `journal.avant19` (scratchpad) | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
Lectures et `git status` seulement. Aucun test, aucune campagne de mutation, aucune commande Git modifiant l'état.

### D. Autorisation
**Instruction de Rémy (message du 2026-10-22)** : mise au point ciblée sur quatre réserves (historique des révisions refusées ; formulation de précédence limitée à C2/C3 ; ordre SQL de la réacceptation ; dates et snapshots), sans modifier aucun document officiel, migration, test ni état Git, puis arrêt pour validation de Rémy.

### E. Clôture — relevé final (2026-10-22 02:28)
- Git : `main`, HEAD `a99d4c2`, 25 entrées `git status`, `git diff --stat` 8 fichiers +186 / −108 : identiques au relevé final du bloc 02:17 [FAIT-VÉRIFIÉ]
- Empreintes identiques à celles du bloc 02:17 : `invariants.md` `9c61d36d2909c958`, `cdc-errata-v6.md` `0459fef9a6683f37`, `modèle-métier-V6.md` `3db0e15a95e052f0`, modèle V3.14 `958a3c0dfc627840`, CDC `5937b7bcda5fcf91`, `CLAUDE.md` `1fc64bc79bd10606`, `.claude/settings.local.json` `c49433832d9be741` ; empreinte agrégée des migrations et des tests métier `1aec50f21bd38398` [FAIT-VÉRIFIÉ]
- Fichiers modifiés depuis l'ouverture (`find -newermt "2026-10-22 02:25:00"`) : uniquement ce journal [FAIT-VÉRIFIÉ]
- Portée du relevé final : identique à A. **Non contrôlé :** identique au bloc 02:17.

### F. Réconciliation
- Écarts initial → final : ce journal seul (B1, B3) ; aucun autre écart sur la portée contrôlée.
- Registre B tenu : oui. **Verdict : CONCORDANT-NON-PROUVÉ** (portée : voir E). Fiabilité : COMPLET sur la portée indiquée.
- Statut documentaire : aucun changement ; les compléments présentés à Rémy sont des propositions non intégrées aux documents officiels. Aucun test, aucune campagne de mutation, aucune commande Git modifiant l'état.
Clôture : CLÔTURÉE 2026-10-22 02:28

---

## Session 2026-10-22 02:17 — Claude Code — corrections documentaires ciblées E-22 / modèle V3.14 et proposition technique consolidée C2/C3
Clôture : CLÔTURÉE le 2026-10-22 à 02:22 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-22 02:17, avant toute écriture de ce bloc)
- `CLAUDE.md` (fourni au démarrage, relu) ; dernier bloc du journal = 2026-10-22 01:11, CLÔTURÉE le 01:20, verdict CONCORDANT-NON-PROUVÉ, lu avant toute autre action [FAIT-VÉRIFIÉ]
- Comparaison à l'état final noté dans ce bloc : empreintes SHA-256 identiques pour `invariants.md` `9c61d36d2909c958`, `cdc-errata-v6.md` `50459e0979c18a02`, `modèle-métier-V6.md` `3db0e15a95e052f0`, modèle V3.14 `95e1445c97a7d314`, `CLAUDE.md` `1fc64bc79bd10606`, `.claude/settings.local.json` `c49433832d9be741` (4451 octets, 2026-10-19 01:32:36) ; Git : `main`, HEAD `a99d4c2`, indexé rien, stash 0, 25 entrées `git status`, `git diff --stat` 8 fichiers, +182 / −107 ; aucun écart avec E du bloc 01:11 [FAIT-VÉRIFIÉ]
- Journal : 8758131212c70dc0 avant ouverture de ce bloc ; 803 CRLF, 1 CR isolé (anomalie n° 2, inchangée) [FAIT-VÉRIFIÉ]
- Empreinte agrégée des 15 migrations et des tests `test_*.py` de `src-tauri/tests/metier/` (tri des empreintes individuelles puis SHA-256) : `1aec50f21bd38398` — référence pour le relevé final [FAIT-VÉRIFIÉ]
- Fichiers que cette session compte modifier : `docs/décisions/cdc-errata-v6.md` (statut et motif d'E-22), `docs/conception/modèle-données-sqlite-v6-v3.14.md` (description de `tr_12_bons_commande_modifiable` et `tr_12_bons_commande_gele`) ; ce journal. Aucun autre.
- Portée du relevé : suivis ☑ (statut, `diff --stat`) · non suivis ☑ (par nom) · ignorés ☑ (empreinte de `.claude/settings.local.json`) · contenu par empreinte ☑ (documents ci-dessus, migrations et tests métier en agrégat). **Non contrôlé :** contenu des autres entrées non suivies (`src/`, `public/`, `reprise-autonome-*/`, fichiers de configuration) autrement que par date, `node_modules/`, `.git/index`, `__pycache__/`.

### B. Registre des actions
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (`docs/suivi/journal-continuite.md`) | insérer ce bloc au-dessus du bloc 01:11 sans modifier celui-ci | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Correction 1 (statut d'E-22) et correction 2 (motif d'E-22, constat technique séparé) | dépôt (`cdc-errata-v6.md`) | ne plus présenter E-22 comme « Validé » ; séparer décision du propriétaire et constat technique | effectuées : `cdc-errata-v6.md` 13830 → 14504 octets, `0459fef9a6683f37…` ; statut d'E-22 = décision du propriétaire (arbitrages des 21 et 22 octobre 2026), rédaction en relecture, non validée officiellement ([LOCAL]) ; colonne Motif réduite à la décision ; constat technique (migration 006) déplacé dans la section datée, formulé comme à vérifier ; phrase sur l'acompte non encaissé reformulée en conséquence directe du verrou. Arbitrages C2/C3 inchangés | [FAIT-VÉRIFIÉ] |
| 3 | Correction 3 (triggers `tr_12_*` historiques) | dépôt (modèle V3.14, §6 et ligne TR-12) | distinguer historique, remplacement 005b, cible E-22 non implémentée | effectuée : modèle V3.14 176137 → 177319 octets, `958a3c0dfc627840…` ; lignes `tr_12_bons_commande_modifiable` et `_gele` réécrites en trois volets (comportement historique, remplacement effectif en 005b, cible E-22 non implémentée) ; ligne `tr_12_bons_commande_contrat` ajoutée (trigger livré) ; renvoi ajouté dans la ligne TR-12 du tableau §8 ; sections CK-21 / CK-22 non touchées | [FAIT-VÉRIFIÉ] |
| 4 | Lectures des migrations 005a, 005b, 006 et des documents nécessaires à la proposition technique | dépôt (lecture seule) | analyse A à F, sans modifier d'autre document | effectuée en lecture seule : 003, 004, 005a, 005b, 006 (extraits), conventions §2, CDC V6.1 ligne 12, README ligne 40, modèle V3.14 §4.7 bis ; aucun autre document modifié | [FAIT-VÉRIFIÉ] |
| 5 | Complément de ce bloc (E, F) et clôture | ce journal | relevé final et réconciliation | effectué ; octets du préambule et des autres blocs vérifiés identiques ; sauvegardes `journal.avant16` (avant ouverture) et `journal.avant17` (avant clôture), `docs_avant2\` (deux documents avant correction) | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
| Commande | Répertoire | Résultat | Portée / limites | Statut |
|---|---|---|---|---|
| Relevé initial (`git status`, `git rev-parse`, `git diff --stat`, `sha256sum`, `stat`, lecture Python du journal) | racine | voir A | lecture seule | [FAIT-VÉRIFIÉ] |
Aucun test, aucune campagne de mutation, aucune commande Git modifiant l'état n'est lancé dans cette session.

### D. Autorisation
**Instruction de Rémy (message du 2026-10-22)** : corriger trois défauts documentaires précis (statut d'E-22 ; motif d'E-22 ; description des triggers historiques `tr_12_*` du modèle V3.14) puis présenter une proposition technique unique et consolidée (A à F) pour les points à arbitrer, sans modifier davantage les documents officiels, sans migration corrective, sans modifier SQL ni tests, sans commande Git modifiant l'état, sans revenir sur les arbitrages C2/C3. S'arrêter après la proposition.

### E. Clôture — relevé final (2026-10-22 02:22)
- Git : branche `main`, HEAD `a99d4c2`, `main...origin/main [behind 7]` (inchangé) ; indexé : rien ; stash : 0 ; entrées `git status` : 25 (identique à A) ; `git diff --stat` : 8 fichiers, +186 / −108 (+182 / −107 en A : écart attribuable aux deux documents corrigés) [FAIT-VÉRIFIÉ]
- Fichiers modifiés depuis l'ouverture (`find -newermt "2026-10-22 02:15:00"`, hors `node_modules`, `.git`) : `cdc-errata-v6.md`, modèle V3.14 et ce journal — **aucun autre** [FAIT-VÉRIFIÉ]
- Empreintes inchangées par rapport à A : `invariants.md` `9c61d36d2909c958`, `modèle-métier-V6.md` `3db0e15a95e052f0`, CDC `5937b7bcda5fcf91`, `docs/README.md` `54d5e5968218cef8`, `conventions-techniques-v6.md` `2e3fc5e2db9d4003`, `CLAUDE.md` `1fc64bc79bd10606`, `.claude/settings.local.json` `c49433832d9be741` (4451 octets, 2026-10-19 01:32:36) ; empreinte agrégée des 15 migrations et des tests métier `1aec50f21bd38398` = A (aucune migration ni aucun test modifié) [FAIT-VÉRIFIÉ]
- Empreintes modifiées, attendues : `cdc-errata-v6.md` `50459e0979c18a02` → `0459fef9a6683f37` ; modèle V3.14 `95e1445c97a7d314` → `958a3c0dfc627840` ; CRLF uniforme dans les deux (0 LF isolé, 0 CR isolé) [FAIT-VÉRIFIÉ]
- Journal avant ce complément : 834 CRLF, 1 CR isolé (anomalie n° 2, inchangée) [FAIT-VÉRIFIÉ]
- Portée du relevé final : identique à A. **Non contrôlé :** contenu des autres entrées non suivies (`src/`, `public/`, `reprise-autonome-*/`, fichiers de configuration) autrement que par date, `node_modules/`, `.git/index`, `__pycache__/`.

### F. Réconciliation
- Écarts initial → final : `cdc-errata-v6.md`, modèle V3.14 (B2, B3) et ce journal (B1, B5) ; aucun autre écart sur la portée contrôlée.
- Registre B tenu pendant la session : oui.
- Portée du verdict : voir E.
- **Verdict : CONCORDANT-NON-PROUVÉ** (écarts = registre B sur la portée indiquée ; contenu hors portée non contrôlé par empreinte).
- Fiabilité : COMPLET sur la portée indiquée.
- Statut documentaire : **aucun changement de statut consigné comme acquis**. E-22 est présenté comme décision du propriétaire dont la rédaction reste en relecture ; la proposition technique A à F n'est pas intégrée aux documents officiels et attend la validation de Rémy. Aucun test, aucune campagne de mutation, aucune commande Git modifiant l'état.
Clôture : CLÔTURÉE 2026-10-22 02:22

---

## Session 2026-10-22 01:11 — Claude Code — mise à jour documentaire C2/C3 (gel abandonné, révision des devis jusqu'à la première facture)
Clôture : CLÔTURÉE le 2026-10-22 à 01:20 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-22 01:08:14, avant toute écriture de cette session)
- `CLAUDE.md` (fourni au démarrage) et dernier bloc du journal (2026-10-19 20:52, CLÔTURÉ le 20:54, verdict CONCORDANT-NON-PROUVÉ) lus avant toute autre action [FAIT-VÉRIFIÉ]
- Branche `main`, HEAD `a99d4c2` ; indexé : rien ; stash : 0 ; suivis modifiés : 7 ; `git diff --stat` : 7 fichiers, +61 / −22 ; entrées `git status` : 24 ; mêmes valeurs qu'au dernier relevé Git du journal (bloc 01:54 du 2026-10-19) [FAIT-VÉRIFIÉ]
- **Écart signalé (non lié aux fichiers de cette session)** : `git status -sb` indique « retard 7 » sur `origin/main`, contre « retard 1 » aux relevés précédents. `.git/FETCH_HEAD` a été modifié le 2026-10-22 à 01:06:33, soit **avant** ce relevé : une opération de récupération externe à cette session a eu lieu (non lancée par Claude). Les 7 nouveaux commits amont (`31b2a31` à `99b4f20`) ne touchent que `docs/leon/**` ; aucun fichier de l'arbre de travail n'a changé (statut et `diff --stat` identiques) [FAIT-VÉRIFIÉ par `git log HEAD..origin/main`, `git diff --stat HEAD origin/main`]
- Ignorés : `.claude/settings.local.json` : 4451 octets, 2026-10-19 01:32:36, inchangé ; `CLAUDE.md` SHA-256 `1fc64bc7…` inchangé ; journal : 124163 octets, 2026-10-19 20:54:14 [FAIT-VÉRIFIÉ]
- Fichiers que cette session compte modifier (tous suivis par Git, tous en CRLF uniforme, 0 LF isolé, 0 CR isolé) :
  - `docs/conception/invariants.md` : 46629 octets, SHA-256 `59594e05190d3cc4…`, blob Git `acb7bd0` ; modifié localement par rapport à HEAD (+3 lignes, [LOCAL]) ;
  - `docs/décisions/cdc-errata-v6.md` : 9067 octets, `3aef866522f57fb8…`, blob `3065de1` ; modifié localement (2 lignes) ;
  - `docs/conception/modèle-métier-V6.md` : 40327 octets, `48acba654f9cb515…`, blob `4a7038e` ;
  - `docs/conception/modèle-données-sqlite-v6-v3.14.md` : 169037 octets, `f87be3885baf1f53…`, blob `9024c82` ; modifié localement (26 lignes) ;
  - `docs/specifications/cdc-fonctionnel-architectural-v6.md` : 39692 octets, `5937b7bcda5fcf91…`, blob `9e8df51` (lecture ; modification non prévue, voir D).
  Fichiers de référence non modifiés par cette session : `docs/README.md` `54d5e596…`, `conventions-techniques-v6.md` `2e3fc5e2…`, 15 migrations, 4 tests métier.
- Portée du relevé : suivis ☑ (statut, `diff --stat`, blobs) · non suivis ☑ (par nom) · ignorés ☑ (présence, dates, empreinte de `.claude/settings.local.json`) · contenu par empreinte ☑ (documents ci-dessus, `CLAUDE.md`). **Non contrôlé :** contenu des autres entrées non suivies (`src/`, `public/`, `reprise-autonome-*/`, fichiers de configuration) autrement que par date, `node_modules/`, `.git/index`, contenu de `__pycache__/`.

### B. Registre des actions
Légende de la colonne Cible : **dépôt** = répertoire de travail du projet ; **scratchpad** = dossier temporaire de l'outil, hors dépôt.
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (`docs/suivi/journal-continuite.md`) | insérer ce bloc au-dessus du bloc 2026-10-19 20:52 sans modifier celui-ci ni le CR isolé du bloc 22:14 | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Sauvegardes des cinq documents de référence avant modification, scripts d'application, journaux | scratchpad (hors dépôt) | pouvoir comparer et restaurer | effectuées : sauvegardes des 5 documents dans `scratchpad\docs_avant\`, scripts `apply_inv.py`, `apply_err.py`, `apply_metier.py`, `apply_modele.py`, sauvegardes du journal `journal.avant14` et `journal.avant15` | [FAIT-VÉRIFIÉ] |
| 3 | Mise à jour de `docs/conception/invariants.md` (INV-31, 34, 36, 38, 49, 110, 168, 169, 174 ; INV-33 et INV-35 retirés ; INV-206 et INV-207 ajoutés ; journal des retraits et modifications) | dépôt | appliquer C2 et C3 au registre, en priorité | effectuée : 46629 → 52379 octets, SHA-256 `9c61d36d2909c958…`, CRLF uniforme ; version du registre 8 ; INV-31, 34, 36, 38, 49, 110, 168, 169, 174 modifiés ; INV-33 et 35 retirés (énoncés d'origine cités au journal du registre) ; INV-206 et 207 ajoutés ; 6 lignes de journal du registre | [FAIT-VÉRIFIÉ] |
| 4 | Ajout de l'erratum E-22 à `docs/décisions/cdc-errata-v6.md` | dépôt | tracer l'écart au CDC §14 et à E-01 | effectuée : 9067 → 13830 octets, `50459e0979c18a02…` ; ligne E-22 (statut « Validé » pour les décisions de Rémy, « à arbitrer » pour les points du §7.4), annotation du statut d'E-01, section narrative datée | [FAIT-VÉRIFIÉ] |
| 5 | Alignement de `docs/conception/modèle-métier-V6.md` | dépôt | réécrire §9 et les renvois au gel | effectuée : 40327 → 42003 octets, `3db0e15a95e052f0…` ; §9 « Verrou du contenu contractuel (première facture) » ; renvois au gel réécrits | [FAIT-VÉRIFIÉ] |
| 6 | Alignement de `docs/conception/modèle-données-sqlite-v6-v3.14.md` | dépôt | réécrire §7 et les renvois au gel, documenter les points à arbitrer | effectuée : 169037 → 176137 octets, `95e1445c97a7d314…`, CRLF uniforme ; §7.1 à 7.4, tableau des triggers, TR-10 à TR-15, C-01, C-02, T-08 à T-11, règle de lecture du mot « gel » ; bloc CK-21 / CK-22 (§14) strictement identique avant/après (770 caractères comparés) | [FAIT-VÉRIFIÉ] |
| 7 | Contrôles de cohérence croisée (lecture seule), complément de ce bloc (E, F) et clôture | dépôt, scratchpad | vérifier références INV/E/TR et fins de ligne | effectuée (voir E) ; complément de ce bloc et clôture | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
| Commande | Répertoire | Résultat | Portée / limites | Statut |
|---|---|---|---|---|
| Relevé initial (`git`, `sha256sum`, `git hash-object`, `git log HEAD..origin/main`, `git diff --stat HEAD origin/main`, `stat`, scripts Python de lecture) ; lectures des documents et des migrations 003, 004, 005a, 005b, 006, 008, 009b | racine | voir A et D | lecture seule | [FAIT-VÉRIFIÉ] |
Aucun test, aucune campagne de mutation n'est lancé dans cette session (tâche documentaire).

### D. Autorisation, analyse préalable et choix d'identifiants
**Autorisation de Rémy (message du 2026-10-22)** : mettre à jour la documentation officielle à la suite du diagnostic C2/C3, sans modifier le SQL ni les tests existants. Décisions du propriétaire à intégrer : **C2** gel progressif du BC définitivement abandonné, `frozen_at` conservé comme champ technique sans sens métier ; **C3** tous les champs métier du devis modifiables ou révisables jusqu'à l'émission de la première facture du BC ; une version modifiée d'un devis déjà accepté doit être acceptée de nouveau par le client avant de devenir la version contractuelle de référence et d'être synchronisée dans le BC ; verrou au niveau du BC dès la première facture (tous les devis rattachés) ; un avoir intégral ne réactive pas la révision ; conformément à Q23, un nouveau devis peut encore être rattaché jusqu'à la création du solde final, sans rouvrir les contenus existants ; mécanisme de révision existant à préserver. Ordre : `CLAUDE.md` et hiérarchie, identifiant d'erratum sans collision, `invariants.md` en priorité, puis uniquement les documents officiels concernés, puis cohérence croisée. Limites : aucune migration ni aucun test SQL modifié ; pas de nettoyage de `fichiers-a-relire/` ; pas de promotion globale des documents intermédiaires ; rien poussé sur Git ; aucune décision technique inventée, les ambiguïtés (synchronisation des snapshots, états du devis et du BC) sont documentées comme points à arbitrer.

**Identifiants (aucun numéro attribué de mémoire)**
- **Erratum : E-22.** Recherche textuelle de `E-nn` dans tous les fichiers du dépôt hors `node_modules`, `.git`, `src/`, `public/` : le plus élevé employé est **E-21** (propositions dans `fichiers-a-relire/` et `reprise-autonome-*/`) ; E-10 à E-20 sont des identifiants de travail ; le registre officiel s'arrête à E-09. E-22 n'apparaît nulle part : plancher de non-collision, comme INV-204, D-62 (modèle V3.14, ligne 12). E-10 à E-21 restent réservés.
- **Invariants : INV-206 et INV-207.** Le registre indique « le suivant libre est INV-206 » ; seul `invariants.md` mentionne ce numéro.
- **Décision D-nn : aucune attribuée** (non demandée) ; E-22 est le registre de décision de C2/C3.
- **TR-nn, CK-nn, C-nn, T-nn : aucun numéro nouveau attribué.** Les gardes SQL à livrer (migration corrective) sont décrites sans numéro. Les cas C-01 et C-02 et les tests T-08 à T-11 existants sont réécrits ou marqués retirés, sans renumérotation.

**CDC** : `docs/specifications/cdc-fonctionnel-architectural-v6.md` est un document gelé ; ses écarts sont tracés aux errata, et E-01 (qui modifiait déjà le §14) n'y est pas intégré. **Aucune modification du CDC prévue** ; l'erratum E-22 porte l'écart (section CDC citée : §14).

**Contrôle préalable** : le seul test qui lit un document est `test_009b_couverture_situations.py` (modèle V3.14, texte de CK-21 / CK-22, test 12). Les sections correspondantes du modèle ne seront pas modifiées.

### D bis. Réalisé — identifiants, points à arbitrer
- Identifiants retenus : **E-22** ; **INV-206**, **INV-207** (le suivant libre du registre devient INV-208). Aucun D, TR, CK, C ni T nouveau attribué ; TR-15, T-08, T-10, T-11 marqués retirés (numéros réservés), C-01, C-02 et T-09 réécrits.
- CDC `cdc-fonctionnel-architectural-v6.md` : **non modifié** (document gelé ; l'écart est tracé par E-22). Aucune migration, aucun test, `README.md` et `conventions-techniques-v6.md` non modifiés par cette session.
- Points techniques **non tranchés**, documentés au modèle §7.4 et dans la section narrative d'E-22 : états du devis pendant la ré-acceptation (TR-18, refus d'acceptation pendant une révision) ; identification de la version contractuelle de référence ; synchronisation des snapshots et de `date_acceptation` avec des snapshots de BC immuables ; états du BC et émission d'une facture pendant une révision ouverte ; forme de la garde SQL du verrou (migration corrective à livrer, avec tests).
- Statut : les décisions C2/C3 sont portées par E-22 comme décisions du propriétaire ; les documents modifiés restent [LOCAL]/[REL] tant que Rémy ne les a pas validés.

### E. Clôture — relevé final (2026-10-22 01:20)
- Git : branche `main`, HEAD `a99d4c2`, `main...origin/main [behind 7]` (inchangé depuis A) ; indexé : rien ; stash : 0 ; entrées `git status` : 25 (24 en A : `modèle-métier-V6.md` est désormais modifié) ; `git diff --stat` : 8 fichiers, +182 / −107 (7 fichiers, +61 / −22 en A) [FAIT-VÉRIFIÉ]
- Fichiers modifiés depuis l'ouverture (`find -newermt "2026-10-22 01:08:00"`, hors `node_modules`, `.git`) : `invariants.md`, `cdc-errata-v6.md`, `modèle-métier-V6.md`, `modèle-données-sqlite-v6-v3.14.md` et ce journal — **aucun autre** [FAIT-VÉRIFIÉ]
- Empreintes inchangées par rapport à A : CDC `5937b7bcda5fcf91`, `docs/README.md` `54d5e5968218cef8`, `conventions-techniques-v6.md` `2e3fc5e2db9d4003`, `CLAUDE.md` `1fc64bc79bd10606`, `.claude/settings.local.json` (4451 octets, 2026-10-19 01:32:36, `c49433832d9be741`) ; `git diff --stat` des migrations et du CDC : vide ; tests 009a/009b : mêmes modifications locales qu'en A (aucune réécriture dans cette session) [FAIT-VÉRIFIÉ]
- Contrôles de cohérence (lecture seule) : CRLF uniforme (0 LF isolé, 0 CR isolé) dans les 4 documents modifiés ; INV-206 et INV-207 présents au registre ; INV-33 et INV-35 absents du registre et cités uniquement dans des contextes documentés (journal du registre, ligne et section d'E-22, concordance du modèle §18) ; références INV nouvellement introduites dans le modèle et les errata toutes présentes au registre (sauf INV-33/35, retirés, cités comme tels) ; E-22 référencé dans les 4 documents ; occurrences restantes du mot « gel » : décisions historiques (D-20, D-25, D-32, V3.4, V3.11, §18) couvertes par la règle de lecture du modèle, et contraintes techniques sur `frozen_at` [FAIT-VÉRIFIÉ]
- Journal avant ce complément : 132410 octets, 1 CR isolé (anomalie n° 2, inchangée) [FAIT-VÉRIFIÉ]
- Portée du relevé final : suivis ☑ (statut, `diff --stat`) · non suivis ☑ (par nom et par date de modification) · ignorés ☑ (présence, dates, empreinte de `.claude/settings.local.json`) · contenu par empreinte ☑ (documents ci-dessus, `CLAUDE.md`, 4 documents modifiés). **Non contrôlé :** contenu des autres entrées non suivies (`src/`, `public/`, `reprise-autonome-*/`, fichiers de configuration) autrement que par date, empreinte des migrations et des tests autrement que par `git diff` et date, `node_modules/`, `.git/index`, `__pycache__/`.

### F. Réconciliation
- Écarts initial → final : les 4 documents officiels listés en A, modifiés comme annoncé en B3 à B6, et ce journal (B1, B7) ; aucun autre écart sur la portée contrôlée.
- Écart externe signalé en A : `git fetch` externe (`origin/main` en retard de 7, `docs/leon/**` seul concerné), sans effet sur l'arbre de travail ; inchangé pendant la session.
- Registre B tenu pendant la session : oui.
- Portée du verdict : voir E.
- **Verdict : CONCORDANT-NON-PROUVÉ** (écarts = registre B sur la portée indiquée ; contenu hors portée non contrôlé par empreinte).
- Fiabilité : COMPLET sur la portée indiquée.
- Statut documentaire : **aucun changement de statut consigné comme acquis**. Aucun test, aucune campagne de mutation, aucune commande Git modifiant l'état (lectures seules) n'ont été exécutés.
Clôture : CLÔTURÉE 2026-10-22 01:20

---

## Session 2026-10-19 20:52 — Claude Code — clôture de la révision documentaire de CLAUDE.md (deux passes)
Clôture : CLÔTURÉE le 2026-10-19 à 20:54 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-19 20:52:21, avant toute écriture de cette session)
- `CLAUDE.md` (fourni au démarrage de la session) et dernier bloc du journal (01:54, CLÔTURÉ le 01:57, verdict CONCORDANT-NON-PROUVÉ) lus avant toute autre action [FAIT-VÉRIFIÉ]
- Git (branche, HEAD, avance/retard, `git status`, `git diff --stat`, index, stash) : **RELEVÉ IMPOSSIBLE : l'instruction de Rémy interdit toute commande Git dans cette intervention** ; rien n'est déduit des valeurs du bloc 01:54.
- `CLAUDE.md` : **11870 octets, 76 lignes, LF uniquement (0 CRLF, 0 CR), SHA-256 `8a6dcab476f82f6c3ffd63eb50cdb72488b530909d4c0aff890844f231cfb5f1`**, dernière modification 2026-10-19 11:52:09 [FAIT-VÉRIFIÉ]
- Journal : 110645 octets, 655 CRLF, 0 LF isolé, 1 CR isolé (anomalie n° 2, inchangée), dernière modification 01:57:27 [FAIT-VÉRIFIÉ]
- Ignorés : `dist/` (10:27:08) et `src-tauri/tests/metier/__pycache__/` (13:38:02, 16 fichiers) inchangés ; `.claude/settings.local.json` : **4451 octets, 01:32:36, SHA-256 `c4943383…ee79`**, identique à l'ouverture du bloc 01:54 (anomalie n° 1 : aucune variation depuis, origine [NON VÉRIFIÉ], non modifié) [FAIT-VÉRIFIÉ]
- Empreintes SHA-256 de 23 fichiers (`CLAUDE.md`, `docs/README.md`, `conventions-techniques-v6.md`, 15 migrations, 4 tests métier, `.claude/settings.local.json`) comparées à celles relevées à l'ouverture du bloc 01:54 : **22 identiques** ; **1 différente, attendue** : `CLAUDE.md` (deux passes de révision, voir B2 et B3) [FAIT-VÉRIFIÉ]
- Fichiers du dépôt modifiés depuis la clôture du bloc 01:54 (`find -newermt "2026-10-19 01:58:00"`, hors `.git`, `node_modules`) : **uniquement `CLAUDE.md`** [FAIT-VÉRIFIÉ]
- Écart avec l'état final de la session précédente (bloc 01:54, E) : **un seul**, `CLAUDE.md` (11131 octets, `8e443318…6952` → 11870 octets, `8a6dcab4…b5f1`), expliqué par B2 et B3 ; aucun autre sur la portée contrôlée.
- Portée du relevé : suivis ☐ (Git interdit) · non suivis ☐ par Git (seuls les fichiers modifiés depuis 01:58 sont détectés par date) · ignorés ☑ (présence, dates, empreinte de `.claude/settings.local.json`) · contenu par empreinte ☑ (23 fichiers). **Non contrôlé :** état Git (statut, index, stash, `diff --stat`), contenu des autres entrées non suivies (`src/`, `public/`, `reprise-autonome-*/`, fichiers de configuration) autrement que par date, `node_modules/`, `.git/index`, contenu de `__pycache__/`.

### B. Registre des actions
Légende de la colonne Cible : **dépôt** = répertoire de travail du projet ; **scratchpad** = dossier temporaire de l'outil, hors dépôt.
Les lignes 2 à 4 concernent des interventions antérieures à ce bloc, **consignées après coup** : le journal n'était pas autorisé en écriture pendant elles (les instructions de ces interventions limitaient les modifications à `CLAUDE.md`). Leurs résultats viennent des sorties de commandes de ces interventions.
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (`docs/suivi/journal-continuite.md`) | insérer ce bloc au-dessus du bloc 01:54 sans modifier celui-ci ni le CR isolé du bloc 22:14 | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | **Première passe de correction de `CLAUDE.md`** (à partir de 10:50:50) : copie de sauvegarde `CLAUDE.md.avant_relecture` (SHA-256 `8e443318…6952`) et fichier de diff `diff_claude_relecture.txt` dans le scratchpad ; **cinq passages de `CLAUDE.md` modifiés** sur instruction de Rémy (ligne 6 statut ; ligne 34 rang 15 de 009c ; ligne 52 interprétation C ; ligne 53 outils de mutation ; ligne 61 tests) | dépôt (`CLAUDE.md`) + scratchpad | corriger les cinq passages relus, avant validation de Rémy | `CLAUDE.md` : 11131 → 11406 octets, SHA-256 `3f124194…d09db`, 76 lignes, LF ; `find -newermt "2026-10-19 10:50:00"` : seul `CLAUDE.md` modifié | [FAIT-VÉRIFIÉ] |
| 3 | **Seconde passe de correction de `CLAUDE.md`** (à partir de 11:51:55) : copie `CLAUDE.md.avant_passe2` (SHA-256 `3f124194…d09db`) et diff `diff_claude_passe2.txt` dans le scratchpad ; **trois passages modifiés** sur instruction de Rémy (ligne 34 ; ligne 50 ; ligne 61) | dépôt (`CLAUDE.md`) + scratchpad | rendre cohérentes les lignes 34 et 50 et rétablir le répertoire d'exécution des tests | `CLAUDE.md` : 11406 → **11870 octets**, SHA-256 `8a6dcab4…b5f1`, 76 lignes, LF, modifié à 11:52:09 ; `find -newermt "2026-10-19 11:51:00"` : seul `CLAUDE.md` modifié ; statut `[REL]` de la ligne 6 conservé | [FAIT-VÉRIFIÉ] |
| 4 | Lecture seule de `CLAUDE.md` et du journal (relecture des cinq passages, avant la première passe) | dépôt | contrôler texte, numéros de ligne et sources | aucune écriture | [FAIT-VÉRIFIÉ] |
| 5 | Complément de ce bloc (E, F) et clôture ; sauvegardes du journal `journal.avant12` (avant ouverture) et `journal.avant13` (avant clôture), scratchpad | ce journal ; scratchpad | consigner relevé final et réconciliation | effectuée ; octets du préambule et des autres blocs vérifiés identiques | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
| Commande | Répertoire | Résultat | Portée / limites | Statut |
|---|---|---|---|---|
| Lecture de `CLAUDE.md` et du journal (outil de lecture), relevé initial de ce bloc (`sha256sum`, `ls -l`, `find -newermt`, script Python de lecture et de hachage) | racine | voir A | lecture seule | [FAIT-VÉRIFIÉ] |
| Pour les passes de B2 et B3, d'après l'historique de ces interventions : `sha256sum`, `cp` vers le scratchpad, `diff -u`, `find -newermt`, `ls -l`, scripts Python de lecture et de hachage | racine | voir B2 et B3 | aucune écriture dans le dépôt autre que `CLAUDE.md` | [FAIT-VÉRIFIÉ] |
**Aucun test, aucune campagne de mutation et aucune commande Git n'ont été exécutés** pendant les deux passes de révision, ni dans cette session (d'après l'historique des commandes de ces interventions). **Cette absence d'exécution n'est pas une preuve de bon fonctionnement** : la documentation révisée n'a été vérifiée par aucun test et aucun résultat de test n'est présenté ici.

### D. Décisions rapportées, points non résolus, prochaine étape
**1. Validation rapportée (source : message de Rémy du 2026-10-19, hors dépôt ; heure de la validation : non disponible)**
- Rémy a validé le contenu de la seconde passe de `CLAUDE.md`. [décision du propriétaire, rapportée ; statut de preuve : rapportée par ce message, non revérifiable dans le dépôt]
- **Statut documentaire : aucun changement n'est consigné.** La ligne 6 de `CLAUDE.md` porte toujours `[REL]` (« en cours de relecture par Rémy ; ne pas les présenter comme approuvées ») et n'a pas été modifiée dans cette intervention (instruction de ne pas modifier `CLAUDE.md`). La mise en cohérence de cette ligne avec la validation rapportée n'est ni faite ni décidée ici : **à décider par Rémy**.
- Réserve rédactionnelle **facultative** signalée par Rémy sur la formulation de la vérification technique des rangs : elle ne bloque pas la validation, n'est pas rouverte et n'a donné lieu à aucune modification. Son détail n'est pas disponible dans cette session au-delà de cet intitulé.

**2. Les trois corrections de la seconde passe, validées (numéros de ligne de `CLAUDE.md` après modification)**
- Ligne 34 (§2, migration 009c) : la confirmation de Rémy du rang 15 (2026-10-18) est conservée sans le mot « acquise » ; la phrase distingue la confirmation de Rémy, le statut documentaire des fichiers qui portent le rang (inchangé, `[LOCAL]/[REL]`) et l'absence de preuve technique du rang par exécution dans l'état actuel du dépôt (pas de runner).
- Ligne 50 (§4) : la règle « les rangs lus dans les en-têtes sont `[NON VÉRIFIÉ]` » est remplacée par : un rang lu dans un en-tête de migration n'est pas, à lui seul, une preuve technique par exécution ; sa vérification technique reste `[NON VÉRIFIÉ]` ; cela ne remet pas en cause une confirmation explicite de Rémy (exemple : rang 15 de 009c).
- Ligne 61 (§5) : consigne ajoutée selon laquelle, les chemins de la commande étant relatifs, elle se lance depuis la racine du dépôt (ainsi exécutée dans les sessions consignées, blocs 23:01 et 00:56, colonne « Répertoire » : « racine »). La commande standard est inchangée ; `python -B` reste présenté comme variante.
Première passe, pour mémoire (cinq passages, B2) : ligne 6 (statut `[REL]`, clarifications du 2026-10-19 en cours de relecture) ; ligne 34 (rang 15) ; ligne 52 (interprétation C : campagne de mutation associée au trigger de 009a, couvre 009c et les contrôles affectés) ; ligne 53 (outils de mutation : aucun outil complet exécutable et autonome dans le dépôt ; pilotes ad hoc hors dépôt) ; ligne 61 (suppression des versions de Python et de SQLite, variante `-B`). Les versions de Python 3.14.8 et de SQLite 3.50.4 ne figurent plus dans `CLAUDE.md` ; elles restent consignées au bloc 23:01.

**3. Blocs antérieurs** : le bloc 01:54 (clôturé, D bis et E) décrit la rédaction des cinq passages **avant** les deux passes ; il n'est pas modifié (règle 2) et ne reflète plus la rédaction courante. La rédaction courante fait foi dans `CLAUDE.md` et dans les diffs des deux passes (scratchpad, temporaires).

**4. Points non résolus (aucun n'est tranché dans ce bloc)**
- Décisions ouvertes du bloc 01:54, D.3 : e6 ; m4 et m5 ; B10 à B13 de `test_009b_couverture` ; compteur T-54 (59 contre 61 tests) ; intégration de 009c. Inchangées.
- Signalés lors de la première passe et non traités : la définition de l'interprétation C n'est donnée que par la parenthèse du bloc 23:01 (les autres lectures ne sont énumérées nulle part dans le journal) ; l'affirmation « aucun outil complet… dans le dépôt » repose sur l'inspection du bloc 23:31, pas sur un audit exhaustif ; la ligne 6 ne date pas la révision.
- Anomalie n° 1 (`.claude/settings.local.json`, origine [NON VÉRIFIÉ]) et anomalie n° 2 (CR isolé du bloc 22:14) : inchangées, suivies séparément.

**5. Prochaine étape [PRÉVU]** : instruction de Rémy ; aucun travail n'est engagé par ce bloc. Préalable : reprise obligatoire (`CLAUDE.md` §0).

### E. Clôture — relevé final (2026-10-19 20:53)
- Git : **RELEVÉ IMPOSSIBLE : commandes Git interdites par l'instruction de Rémy** (même motif qu'en A).
- `CLAUDE.md` : 11870 octets, 76 lignes, LF uniquement, SHA-256 `8a6dcab4…b5f1` — **identique à A** : non modifié pendant ce bloc [FAIT-VÉRIFIÉ]
- Ignorés : `dist/` (10:27:08) et `src-tauri/tests/metier/__pycache__/` (13:38:02, 16 fichiers) inchangés ; `.claude/settings.local.json` : 4451 octets, 01:32:36, SHA-256 `c4943383…ee79` — **identique à A** [FAIT-VÉRIFIÉ]
- Empreintes de 23 fichiers comparées à celles de l'ouverture du bloc 01:54 : **22 identiques** ; **1 différente, attendue** : `CLAUDE.md` (B2 et B3) [FAIT-VÉRIFIÉ]
- Fichiers du dépôt modifiés depuis l'ouverture de ce bloc (`find -newermt "2026-10-19 20:52:00"`) : **uniquement le journal** ; depuis la clôture du bloc 01:54 (`-newermt "2026-10-19 01:58:00"`) : `CLAUDE.md` et le journal, aucun autre [FAIT-VÉRIFIÉ]
- Journal avant ce complément : 121060 octets, 710 CRLF, 0 LF isolé, 1 CR isolé (anomalie n° 2, inchangée) [FAIT-VÉRIFIÉ]
- Portée du relevé final : identique à A (Git non relevé ; ignorés par présence, dates et empreinte de `.claude/settings.local.json` ; contenu par empreinte pour 23 fichiers). **Non contrôlé :** état Git, contenu des autres entrées non suivies (`src/`, `public/`, `reprise-autonome-*/`, fichiers de configuration) autrement que par date, `node_modules/`, `.git/index`, contenu de `__pycache__/`.

### F. Réconciliation
- Écarts initial → final de ce bloc : ce journal (B1, B5) ; aucun autre écart sur la portée contrôlée.
- Écarts depuis l'état final du bloc 01:54 : `CLAUDE.md` (deux passes de révision, B2 et B3, consignées après coup) ; aucun autre fichier du dépôt modifié sur la portée contrôlée (empreintes de 23 fichiers et recherche par date).
- Registre B tenu sur toute la session : **non pour l'intervalle entre la clôture du bloc 01:54 et l'ouverture de ce bloc** (B2 à B4 consignées après coup, d'après l'historique des interventions) ; oui pour ce bloc.
- Portée du verdict : voir E.
- **Verdict : CONCORDANT-NON-PROUVÉ** (écarts = registre B sur la portée indiquée, empreintes cohérentes ; registre tenu après coup pour les deux passes, état Git non relevé et contenu hors portée non contrôlé par empreinte : une modification non détectée n'est pas exclue). L'anomalie n° 1 (`.claude/settings.local.json`) reste suivie séparément : aucune variation constatée depuis le bloc 01:54.
- Fiabilité : PARTIEL (état Git non relevé ; deux passes consignées après coup)
- Statut documentaire : **aucun changement consigné** ; `CLAUDE.md` conserve `[REL]` (ligne 6). Aucun arbitrage métier ou technique n'a été réalisé dans ce bloc ; aucun test, aucune campagne de mutation et aucune commande Git n'ont été exécutés.
Clôture : CLÔTURÉE 2026-10-19 20:54

---

## Session 2026-10-19 01:54 — Claude Code — clôture de continuité : journal et clarifications de CLAUDE.md
Clôture : CLÔTURÉE le 2026-10-19 à 01:57 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-19 01:54:53, avant toute écriture de cette session)
- `CLAUDE.md` (intégral) et `docs/suivi/journal-continuite.md` (règles, modèle, dernier bloc : 00:56, CLÔTURÉ le 01:32, verdict DISCORDANT limité à `.claude/settings.local.json`) lus avant toute autre action [FAIT-VÉRIFIÉ]
- Branche `main`, HEAD `a99d4c2`, retard 1 sur `origin/main` (référence locale, aucun fetch) ; indexé : rien ; stash : 0 [FAIT-VÉRIFIÉ]
- Suivis modifiés : 7 ; `git diff --stat` : 7 fichiers, +61 / −22 ; entrées `git status` : 24 ; mêmes valeurs qu'à la clôture du bloc 00:56 [FAIT-VÉRIFIÉ]
- Ignorés : `dist/` (10:27:08) et `src-tauri/tests/metier/__pycache__/` (13:38:02, 16 fichiers) inchangés ; `.claude/settings.local.json` : **4451 octets, 01:32:36, SHA-256 `c4943383…ee79`**, contre 4108 octets, 01:07:36, `e4daa88c…` notés à la clôture du bloc 00:56 (anomalie n° 1 : variation constatée, origine [NON VÉRIFIÉ], non modifié) [FAIT-VÉRIFIÉ]
- Empreintes SHA-256 de 23 fichiers (`CLAUDE.md`, `docs/README.md`, `conventions-techniques-v6.md`, 15 migrations, 4 tests métier, `.claude/settings.local.json`) comparées à celles relevées à l'ouverture du bloc 00:56 : **20 identiques** (dont `CLAUDE.md` `93f8fec6…`, les 15 migrations et `test_009b_couverture`, `test_009b_acompte`) ; 3 différentes, **toutes déjà notées au bloc 00:56 (E)** : `test_009a_…py` (`f4d835f5…`), `test_009c_…py` (`746bccab…`), `.claude/settings.local.json`. Blobs Git de `invariants.md` `acb7bd0`, `cdc-errata-v6.md` `3065de1`, `modèle-données-sqlite-v6-v3.14.md` `9024c82` identiques [FAIT-VÉRIFIÉ]
- Fichiers de travail modifiés depuis la clôture du bloc 00:56 (`find -newermt`, hors `.git`, `node_modules`, `.claude/`) : uniquement `docs/suivi/journal-continuite.md` (écrit par cette clôture du bloc 00:56) [FAIT-VÉRIFIÉ]
- Journal : 561 CRLF, 0 LF isolé, 1 CR isolé (anomalie n° 2, inchangée), 95247 octets ; `CLAUDE.md` : 75 lignes LF, 10202 octets [FAIT-VÉRIFIÉ]
- Écart avec l'état final de la session précédente : **un seul**, sur `.claude/settings.local.json` (4108 → 4451 octets), consigné ci-dessus ; aucun autre.
- Portée du relevé : suivis ☑ (statut, `diff --stat`) · non suivis ☑ (par nom et dates récentes) · ignorés ☑ (présence, dates, empreinte de `.claude/settings.local.json`) · contenu par empreinte ☑ (23 fichiers). **Non contrôlé :** contenu des autres entrées non suivies (`src/`, `public/`, `reprise-autonome-*/`, fichiers de configuration) autrement que par date, `node_modules/`, `.git/index`, contenu de `__pycache__/`.

### B. Registre des actions
Légende de la colonne Cible : **dépôt** = répertoire de travail du projet ; **scratchpad** = dossier temporaire de l'outil, hors dépôt.
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (`docs/suivi/journal-continuite.md`) | insérer ce bloc au-dessus du bloc 00:56 sans modifier celui-ci ni le CR isolé du bloc 22:14 | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Empreintes d'ouverture (`h_ouverture_4.txt`) | scratchpad | pouvoir comparer en fin de session | créé | [FAIT-VÉRIFIÉ] |
| 3 | Clarifications de `CLAUDE.md` (cinq passages, détaillés en D) **sur instruction explicite de Rémy** (message de clôture de continuité du 2026-10-19 : « mettre à jour `CLAUDE.md` uniquement si une consigne durable doit être ajoutée ou clarifiée ») ; exception à `CLAUDE.md` §7, qui n'autorise pas Claude à le modifier de sa propre initiative | dépôt (`CLAUDE.md`) | éviter que la prochaine session lise des énoncés périmés (rang 15 « non confirmé », §7.1 « en attente ») contredisant les arbitrages de Rémy déjà consignés | effectuée : cinq passages modifiés (détail en D bis) ; `CLAUDE.md` 75 → 76 lignes, 10202 → 11131 octets, SHA-256 `93f8fec6…` → `8e443318…6952`, fins de ligne LF conservées | [FAIT-VÉRIFIÉ] |
| 4 | Complément de ce bloc (D bis, E, F) et clôture ; sauvegarde du journal avant écriture | ce journal ; scratchpad | consigner relevé final et réconciliation | effectuée ; sauvegarde `journal.avant11` ; octets des autres blocs vérifiés identiques | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
| Commande | Répertoire | Résultat | Portée / limites | Statut |
|---|---|---|---|---|
| Lecture de `CLAUDE.md` et du journal (règles, modèle, bloc 00:56, passages sur les arbitrages et l'environnement), relevé initial (`git`, `sha256sum`, `ls -l`, `find`, scripts Python de lecture) | racine | voir A | lecture seule | [FAIT-VÉRIFIÉ] |
**Aucun test, aucun outil de mutation, aucune commande de validation n'est lancé dans cette session** (instruction de Rémy). Les résultats de tests rapportés en D ne sont pas revérifiés ici.

### D. État des travaux, rectifications, décisions ouvertes, réserves
**1. Travaux de la session précédente (bloc 00:56, CLÔTURÉ) — résultats rapportés, non revérifiés dans ce bloc** [NON VÉRIFIÉ dans ce bloc ; preuves : bloc 00:56, sections B, C, D bis, E, F]
- Correction ciblée des tests de non-régression après 009c : seuls deux fichiers de test modifiés, `src-tauri/tests/metier/test_009c_bc_annulation_acompte_encaissement.py` et `src-tauri/tests/metier/test_009a_bc_annulation_interdite_si_facture.py`. Corrections annoncées : C10, C13, C17 (garde de chaîne de `test_009c`), A3, A4, A5, A7 (non-vacuité de `test_009a`), cas w4 de R1 (test `BEFORE`). Aucune migration ni aucun document de référence modifié par cette intervention : confirmé ici pour les fichiers contrôlés par empreinte (voir A : 20 empreintes sur 23 identiques, les 3 autres expliquées) [FAIT-VÉRIFIÉ pour ce point précis].
- Résultats rapportés : tests directs des quatre modules OK (57, 106, 13, 61 tests) ; suite métier complète OK (2103 tests, 0 échec, 0 erreur, 0 ignoré) ; mutants visés tués après correction ; scénarios S0 à S11 et 12 combinaisons « défaut + mutant » rejoués ; C1 : 44 tués, 7 survivants, 1 non exécutable.
- Verdict **proposé** pour la garde SQL de 009c (périmètre limité) : « validable sous réserves précisément énoncées ». **Ce n'est pas une décision d'intégration** ; elle reste à prendre par Rémy. 009c n'est pas déclarée validée.

**2. Rectifications du bloc 00:56 (clôturé, non réécrit — règle 2)**
- R-1. Le titre de la section E du bloc 00:56 annonce un « relevé final (2026-10-19 01:30 à 01:35) » alors que la clôture de ce bloc est horodatée 01:32 : la plage annoncée dépasse l'heure réelle de clôture. Les relevés eux-mêmes (empreintes à 01:30:29, vérifications après écriture avant 01:32) ne sont pas remis en cause ; la plage correcte est 01:30 à 01:32.
- R-2. Anomalie n° 1 : le bloc 00:56 note `.claude/settings.local.json` à 4108 octets (01:07:36) ; le fichier mesurait 4451 octets à 01:32:36 (changement postérieur à ces relevés). Origine [NON VÉRIFIÉ] (hypothèse du bloc 23:31 : consignation des autorisations d'outils approuvées) ; fichier non modifié.

**3. Décisions encore ouvertes — aucune n'est tranchée dans ce bloc** (statut : en attente de Rémy)
1. R1 / e6 : priorité du message `INV-44` ou `INV-186` lorsqu'un même `UPDATE` modifie l'identifiant et viole les deux conditions (non documentée ; code et tests inchangés).
2. R1 / m4 et m5 : le modèle impose le préfixe `INV-xx`, mais pas les libellés complets des messages (code et tests inchangés).
3. `test_009b_couverture` : décider si les améliorations souhaitables B10 à B13 doivent être appliquées (fichier non modifié).
4. Compteur T-54 : le modèle indique encore « 59 tests en 8 groupes » alors que `test_009c` en compte 61 (rapporté) ; mise à jour du modèle non effectuée.
5. Intégration de 009c : non décidée.

**4. Réserves techniques à conserver**
- L'outil de mutation est ad hoc, hors dépôt et non versionné ; les mutants sont écrits à la main ; mutants et scénarios évalués en CRLF uniquement.
- Aucune campagne SQL spécifique à 009b n'a été menée.
- L'atomicité « avoir + annulation » reste hors périmètre.
- La source primaire de D-63 et du rang 15 est toujours absente du dépôt (confirmation de Rémy du 2026-10-18 consignée au bloc 23:01).
- T-54 « campagne de mutation (20 mutants) » : toujours non démontré [NON VÉRIFIÉ] ; T-53 et le modèle inchangés.
- `ResourceWarning: unclosed database` : 1727 contre 1608 (rapporté) ; point de qualité non corrigé.
- Anomalie n° 1 (`.claude/settings.local.json`) : origine non vérifiée ; suivie séparément. Anomalie n° 2 (CR isolé du bloc 22:14) : inchangée.

**5. Clarifications de `CLAUDE.md` (action B3, appliquées : voir D bis) — consignes durables uniquement, détail de session laissé au journal**
- Ligne « Statut de ce fichier » : mention des clarifications du 2026-10-19, [REL], non relues par Rémy.
- §2, migration 009c : rang 15 confirmé par Rémy le 2026-10-18 (source primaire hors dépôt, absente du dépôt) au lieu de « [NON VÉRIFIÉ] — non confirmé ».
- §4, conventions §7.1 : interprétation C retenue par Rémy le 2026-10-18, au lieu de « décision de Rémy en attente ».
- §4 : nouvelle ligne « outils de mutation » (aucun outil exécutable dans le dépôt ; pilote ad hoc hors dépôt ; rien à ajouter au dépôt sans autorisation séparée).
- §5 : environnement d'exécution observé (racine du dépôt, Python 3.14.8, SQLite 3.50.4, variante `python -B`), au lieu de « [NON VÉRIFIÉ] ».

**6. Prochaine étape [PRÉVU] et préalables** : reprise obligatoire (`CLAUDE.md` §0) ; décision de Rémy sur les cinq points ouverts ; relecture par Rémy des clarifications de `CLAUDE.md` ; aucun travail technique n'est engagé par cette session.

### D bis. Résultat des clarifications de `CLAUDE.md` (action B3)
Passages modifiés (numéros de ligne du fichier après modification) ; aucun autre passage n'a changé (§0, §1, §3, §6, §7 inchangés, y compris la règle de §7 selon laquelle Claude ne modifie pas `CLAUDE.md` de sa propre initiative) :
- ligne 6 (statut du fichier) : ajout de « Clarifications des §2, §4 et §5 ajoutées le 2026-10-19 sur instruction de Rémy (clôture de continuité) : [REL], non encore relues par Rémy » ; la mention de validation du 2026-10-18 est conservée telle quelle ;
- ligne 34 (§2, migration 009c) : « rang (15) [NON VÉRIFIÉ] — non confirmé… » remplacé par « rang 15 confirmé par Rémy le 2026-10-18 (message de reprise ; source primaire hors dépôt, absente du dépôt ; journal, bloc 2026-10-18 23:01). Aucun runner dans le dépôt : un rang lu dans un en-tête reste [NON VÉRIFIÉ] par la seule lecture » ; le reste de la ligne (lieux où le rang est inscrit, état sur `origin/main`) est conservé ;
- ligne 52 (§4, conventions §7.1) : « n'est pas tranchée… décision de Rémy en attente » remplacé par « interprétation C retenue par Rémy le 2026-10-18 (… ce n'est pas une affirmation que le texte exclut toute autre lecture ; journal, bloc 2026-10-18 23:01) » ; « Ne lancer aucun test ni aucune campagne sans demande » est conservé ;
- ligne 53 (§4, ajoutée) : outils de mutation — aucun outil exécutable dans le dépôt ; pilote ad hoc hors dépôt et non versionné sur copie isolée ; rien de tel à ajouter au dépôt sans autorisation séparée de Rémy ;
- ligne 61 (§5) : « Répertoire d'exécution et version de Python : [NON VÉRIFIÉ] » remplacé par l'environnement observé (racine du dépôt, Python 3.14.8, SQLite 3.50.4, variante `python -B` ; à revérifier à chaque session) ; « Ne lancer aucun test sans demande » est conservé.
Ces passages reprennent des arbitrages de Rémy **déjà consignés** au journal (bloc 23:01) et des constats déjà vérifiés (blocs 23:01 et 00:56) ; ils ne tranchent aucune question ouverte (voir D.3) et ne changent aucun statut documentaire. Ils restent [REL] jusqu'à relecture par Rémy. Rien du détail de cette session n'a été ajouté à `CLAUDE.md`.

### E. Clôture — relevé final (2026-10-19 01:56 à 01:57)
- Branche `main`, HEAD `a99d4c2`, retard 1 sur `origin/main` (référence locale, aucun fetch) ; indexé : rien ; stash : 0 [FAIT-VÉRIFIÉ]
- Suivis modifiés : 7 ; `git diff --stat` : 7 fichiers, +61 / −22 (inchangé : `CLAUDE.md` et `docs/suivi/` sont non suivis) ; entrées `git status` : 24, mêmes noms [FAIT-VÉRIFIÉ]
- Ignorés : `dist/` (10:27:08) et `src-tauri/tests/metier/__pycache__/` (13:38:02, 16 fichiers) inchangés ; `.claude/settings.local.json` : 4451 octets, 01:32:36, SHA-256 `c4943383…ee79` — **identique à l'ouverture de ce bloc** [FAIT-VÉRIFIÉ]
- Empreintes de 23 fichiers comparées à A : **22 identiques** (15 migrations, 4 tests métier, `docs/README.md`, `conventions-techniques-v6.md`, `.claude/settings.local.json`) ; **1 différente, attendue** : `CLAUDE.md` (action B3) ; blobs Git de `invariants.md`, `cdc-errata-v6.md`, `modèle-données-sqlite-v6-v3.14.md` identiques (`acb7bd0`, `3065de1`, `9024c82`) [FAIT-VÉRIFIÉ]
- Recherche `find -newermt "2026-10-19 01:54:00"` dans le dépôt (hors `.git`, `node_modules`, `.claude/`) : exactement `CLAUDE.md` et `docs/suivi/journal-continuite.md`, aucun autre [FAIT-VÉRIFIÉ]
- Aucun fichier de test, aucune migration, aucun document de référence ni `.gitignore` modifié par cette session ; aucun test, aucun outil de mutation, aucune commande de validation lancé [FAIT-VÉRIFIÉ]
- Journal avant ce complément : 627 CRLF, 0 LF isolé, 1 CR isolé (anomalie n° 2, inchangée) [FAIT-VÉRIFIÉ]
- Portée du relevé final : identique à A (suivis ☑ · non suivis ☑ par nom et dates · ignorés ☑ présence, dates, empreinte de `.claude/settings.local.json` · contenu par empreinte ☑ 23 fichiers). **Non contrôlé :** contenu des autres entrées non suivies (`src/`, `public/`, `reprise-autonome-*/`, fichiers de configuration) autrement que par date, `node_modules/`, `.git/index`, contenu de `__pycache__/`.

### F. Réconciliation
- Écarts initial → final : (a) ce journal (B1, B4) ; (b) `CLAUDE.md` (B3, sur instruction de Rémy). Aucun autre écart sur la portée contrôlée. Aucun écart sur `.claude/settings.local.json` pendant ce bloc (l'écart antérieur est consigné en A, R-2).
- Registre B tenu sur toute la session : oui. Aucun effet de bord attendu (aucun test lancé ; aucun fichier ignoré créé par cette session).
- Portée du verdict : voir E.
- **Verdict : CONCORDANT-NON-PROUVÉ** (écarts = registre B sur la portée indiquée, empreintes cohérentes ; contenu hors portée non contrôlé par empreinte, une modification non détectée n'est pas exclue). L'anomalie n° 1 (`.claude/settings.local.json`, origine [NON VÉRIFIÉ]) reste suivie séparément.
- Fiabilité : PARTIEL (portée partielle)
- Aucun arbitrage métier ou technique n'a été réalisé dans cette session ; les cinq décisions de D.3 restent ouvertes.
Clôture : CLÔTURÉE 2026-10-19 01:57

---

## Session 2026-10-19 00:56 — Claude Code — correction ciblée des tests de non-régression après 009c (C10, C13, C17, A3/A4/A5/A7, R1)
Clôture : CLÔTURÉE le 2026-10-19 à 01:32 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-19 00:56:20, avant toute action d'écriture de cette session)
- `CLAUDE.md` (fourni au démarrage de la session) et dernier bloc du journal (23:31 : CLÔTURÉE le 2026-10-19 à 00:42, verdict DISCORDANT limité à `.claude/settings.local.json`) lus avant toute autre action [FAIT-VÉRIFIÉ]
- Branche `main`, HEAD `a99d4c2`, retard 1 sur `origin/main` (référence locale, aucun fetch) ; indexé : rien ; stash : 0 [FAIT-VÉRIFIÉ]
- Suivis modifiés : 7 ; `git diff --stat` : 7 fichiers, +51 / −20 ; entrées `git status` : 24 ; mêmes noms qu'à la clôture du bloc 23:31 [FAIT-VÉRIFIÉ]
- Ignorés : `dist/` (10:27:08) et `src-tauri/tests/metier/__pycache__/` (13:38:02, 16 fichiers) inchangés ; `.claude/settings.local.json` : **3599 octets, 00:42:31, SHA-256 `f6150c5e318eb432697ac1c97d27625143254e8afa98ea49ab5dda63864b1b36`**, contre 3414 octets, 00:20:47, `9863aa4b…` à la clôture du bloc 23:31 (anomalie n° 1 : variation constatée, origine [NON VÉRIFIÉ], non modifié) [FAIT-VÉRIFIÉ]
- Empreintes SHA-256 de 23 fichiers (`CLAUDE.md`, `docs/README.md`, `conventions-techniques-v6.md`, 15 migrations, 4 tests métier, `.claude/settings.local.json`) : **22 identiques** aux valeurs du relevé initial du bloc 23:31, 1 différente (`.claude/settings.local.json`) ; blobs Git de `invariants.md` `acb7bd0`, `cdc-errata-v6.md` `3065de1`, `modèle-données-sqlite-v6-v3.14.md` `9024c82` identiques [FAIT-VÉRIFIÉ]
- Empreintes SHA-256 de départ des trois fichiers de test qui pourront être modifiés : `test_009a_bc_annulation_interdite_si_facture.py` `5e10e723…176d`, `test_009b_couverture_situations.py` `90152ade…c994`, `test_009c_bc_annulation_acompte_encaissement.py` `78ffec0f…414f` (identiques à celles du bloc 23:31) [FAIT-VÉRIFIÉ]
- Journal : 441 CRLF, 0 LF isolé, 1 CR isolé (anomalie n° 2, inchangée), 71125 octets [FAIT-VÉRIFIÉ]
- Portée du relevé : suivis ☑ (statut, `diff --stat`) · non suivis ☑ (par nom) · ignorés ☑ (présence, dates, empreinte de `.claude/settings.local.json`) · contenu par empreinte ☑ (23 fichiers). **Non contrôlé :** contenu des autres entrées non suivies (`src/`, `public/`, `reprise-autonome-*/`, fichiers de configuration), `node_modules/`, `.git/index`, contenu de `__pycache__/`, dossier temporaire du système.

### B. Registre des actions
Légende de la colonne Cible : **dépôt** = répertoire de travail du projet ; **copie** = copie temporaire hors dépôt ; **scratchpad** = dossier temporaire de l'outil, hors dépôt.
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (`docs/suivi/journal-continuite.md`) | insérer ce bloc au-dessus du bloc 23:31 sans modifier celui-ci ni le CR isolé du bloc 22:14 | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Empreintes d'ouverture (`h_ouverture_3.txt`) et sauvegarde des trois fichiers de test dans `tests_avant/` | scratchpad | pouvoir comparer et restaurer | créés | [FAIT-VÉRIFIÉ] |
| 3 | Essai préalable des corrections sur une copie (`trial/`) puis tests de cette copie | scratchpad (hors dépôt) | ne pas toucher au dépôt avant d'avoir vu les tests passer | `test_009a` 57, `test_009b_couverture` 13, `test_009c` 61 : OK | [FAIT-VÉRIFIÉ] |
| 4 | **Modification de `src-tauri/tests/metier/test_009c_bc_annulation_acompte_encaissement.py`** (script `apply_tests.py`) : 797 → 858 lignes, + 66 / − 5 ; SHA-256 `78ffec0f…` → `746bccab…` ; CRLF uniformes (0 LF isolé, 0 CR isolé) | **dépôt** | corriger C10, C13, C17 et R1/w4 | effectuée ; empreinte identique à celle de la copie d'essai | [FAIT-VÉRIFIÉ] |
| 5 | **Modification de `src-tauri/tests/metier/test_009a_bc_annulation_interdite_si_facture.py`** (`apply_tests.py`, puis `patch2.py` qui sépare l'appel de l'assertion de preuve) : 790 → 798 lignes, + 10 / − 2 ; SHA-256 `5e10e723…` → `f4d835f5…` ; CRLF uniformes | **dépôt** | corriger A3, A4, A5, A7 | effectuée | [FAIT-VÉRIFIÉ] |
| 6 | Aucune modification de `test_009b_couverture_situations.py` (`90152ade…` inchangée), de `test_009b_acompte_garanties_manuelles.py`, d'aucune migration, d'aucun document, de `CLAUDE.md` | dépôt | — | vérifié par empreintes (E) | [FAIT-VÉRIFIÉ] |
| 7 | Reconstruction de la copie isolée à partir du dépôt corrigé (`mutcamp_v2.py setup`), pilote complémentaire `mutcamp_v2.py`, scripts `run_v2.sh`, résultats `mut_results_v2/`, journaux | copie et scratchpad (hors dépôt) | réévaluer les mutants sur le code corrigé ; les résultats d'avant correction (`mut_results/`) sont conservés | effectuée ; `work` et `work_lf` conformes à `ref` au relevé final | [FAIT-VÉRIFIÉ] |
| 8 | Complément de ce bloc (B, C, D bis, E, F) et clôture ; sauvegarde `journal.avant9` | ce journal | consigner résultats et réconciliation | effectuée | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
| Commande | Répertoire | Résultat | Portée / limites | Statut |
|---|---|---|---|---|
| Relevé initial (`git`, `sha256sum`, `ls -l`, scripts Python en lecture seule) | racine | voir A | lecture seule | [FAIT-VÉRIFIÉ] |
| Lecture des trois fichiers de test (zones concernées), recherches (`Grep`) dans `docs/` et dans les tests | racine | voir D | lecture seule | [FAIT-VÉRIFIÉ] |
| Sonde `BEFORE`/`AFTER` contre les `CHECK` de la ligne (base `:memory:` construite depuis la copie `ref` du scratchpad) | scratchpad | `UPDATE bons_commande SET statut='annule'` sur un BC portant un acompte non neutralisé : message `INV-44` avec le trigger livré, `CHECK constraint failed` avec la variante `AFTER UPDATE` | lecture seule, 3 `UPDATE` incomplets ou complets | [FAIT-VÉRIFIÉ] |
| `python -B apply_tests.py --dest trial/…` puis `python -B -m unittest` sur les trois modules de la copie d'essai | scratchpad | 57 / 13 / 61 tests, OK | copie hors dépôt | [FAIT-VÉRIFIÉ] |
| `python -B apply_tests.py` ; `python -B patch2.py` | racine (écrit dans le dépôt, deux fichiers de test) | empreintes en B4 et B5 ; fins de ligne CRLF conservées | seules écritures de test de cette session | [FAIT-VÉRIFIÉ] |
| `python -B src-tauri/tests/metier/test_009a_….py`, `…test_009b_acompte_garanties_manuelles.py`, `…test_009b_couverture_situations.py`, `…test_009c_….py` (un fichier à la fois, depuis la racine) | racine | code de sortie 0 pour les quatre ; `Ran 57`, `Ran 106`, `Ran 13`, `Ran 61` ; `OK` | ces fichiers seuls | [FAIT-VÉRIFIÉ] |
| `python -B -m unittest discover -s src-tauri/tests/metier -p "test_*.py" -v` (commande documentée, **avec `-B` ajouté**) | racine | code 0 ; `Ran 2103 tests in 91.044s` ; `OK` ; 0 FAIL, 0 ERROR, 0 ignoré ; 16 modules ; 1727 lignes `ResourceWarning: unclosed database` (1608 à l'étape 1) | **uniquement** `src-tauri/tests/metier/` ; hors portée : `src-tauri/tests/machine/test_premier_demarrage.py`, front | [FAIT-VÉRIFIÉ] |
| `mutcamp_v2.py setup`, `baseline --env crlf`, `baseline --env lf` | scratchpad | 57 / 106 / 13 / 61 tests OK dans les deux environnements | copie | [FAIT-VÉRIFIÉ] |
| `run_v2.sh` : C2 (16 mutants), C4 (16 mutants), C1 (52 mutants SQL), scénarios S0 à S11, 12 combinaisons « défaut + mutant » (01:08:58 à 01:22:20) ; puis `scen S0` et `scen S4` avec C24 + C13 | scratchpad | aucun traceback ; résultats en D bis ; chaque campagne se termine par « copie restauree conforme, depot src-tauri inchange » | exécution sans arrêt au premier échec (`NOFF=1`) ; CRLF seulement pour les mutants et scénarios | [FAIT-VÉRIFIÉ] |
| Relevé final (`git`, `sha256sum`, `find -newermt`, comparaison des arbres, comptage du journal) | racine | voir E | lecture seule | [FAIT-VÉRIFIÉ] |
Aucun fetch, pull, commit, push, changement de branche, add, stash, restore, reset, clean [FAIT-VÉRIFIÉ par relevé final]. Les sorties complètes sont dans le scratchpad (hors dépôt).

### D. Autorisation, analyse préalable et plan
**Autorisation de Rémy (message du 2026-10-19)** : traiter les lacunes de tests identifiées à l'étape 2 avant toute décision d'intégration de 009c : C10, C13, C17 (contrôles de chaîne de `test_009c`) ; assertions de non-vacuité pertinentes dans `test_009a` et `test_009b_couverture` ; vérifications ciblées de R1 uniquement si l'attendu est établi sans ambiguïté. Phase 1 obligatoire : examiner et proposer avant toute modification. Limites : aucune migration (006, 009a, 009b, 009c) ; aucun document de référence ; ni `CLAUDE.md` ni modèle (T-53, T-54 inchangés) ; ni `.claude/settings.local.json` ni `.gitignore` ; pilote de mutation hors dépôt ; aucune opération Git d'état ou de synchronisation ; périmètre fonctionnel de 009c inchangé ; atomicité « avoir + annulation » hors périmètre ; arrêt et demande de décision si une migration, une règle non documentée ou un élargissement de périmètre devient nécessaire ; en cas d'échec d'un test : analyser la cause, ne pas supprimer d'assertion pour masquer un échec.

**Analyse préalable (lecture seule)**
| Lacune | Code responsable | Cause | Correction minimale | Nature |
|---|---|---|---|---|
| C10 | `test_009c`, `migrations_suivantes()` (collection positionnelle `sorted(glob)[RANG:]`, lit la constante `MIGRATIONS`) | tant que 010 n'existe pas, la collection est vide et un décalage de tranche est invisible ; aucun test n'établit qu'une 010 posée est collectée avec les rangs 16, 17… (S2 + C10 : 4 modules OK) | paramètre facultatif `dossier` pour `migrations_suivantes()` ; témoin sur un dossier temporaire (15 migrations livrées copiées + 010, 011 posées) qui vérifie noms et rangs, puis rejoue la suite | **nécessaire** |
| C13 | `test_009c`, `suite_conserve_le_trigger`, ligne `t.refuse(bc.b, M_ACOMPTE)` | seul détecteur d'une 010 qui laisse la définition identique mais rend la garde inopérante (S4) ; le témoin de 009c ne contient pas ce cas (celui de `test_009a`, lignes 779–782, le contient) | ajouter le cas « 010 inopérante » (même SQL que le témoin de `test_009a`) aux témoins de 009c, en exigeant `AssertionError` | **nécessaire** |
| C17 | `test_009c`, test `…_apres_chaque_migration_suivante` (appel sur la chaîne réelle) | l'appel n'a aucune trace vérifiable : tant que 010 n'existe pas, sa suppression ne change aucun résultat | `suite_conserve_le_trigger` retourne la liste des migrations rejouées et contrôlées ; le test la compare à la liste construite par comparaison de noms (`> NOM_009C`), indépendante de la tranche positionnelle | **nécessaire** |
| A3, A4, A5, A7 | `test_009a`, `migrations_suivantes()` (filtre `NOM_SUCCESSEUR`, tranche) et test `…_apres_chaque_migration_suivante` | la liste examinée peut devenir vide sans échec : aucune assertion de non-vacuité | assertion que la première migration examinée est `(14, 009b_acompte_garanties_manuelles.sql)` ; `suite_conserve_le_trigger` retourne les noms rejoués, comparés à la liste collectée | **nécessaire** |
| B10 à B13 | `test_009b_couverture`, test 13 | aucune itération vide (12 empreintes littérales, `noms[:12]` et `noms[12:14]` explicites) ; les mutants sont des suppressions d'assertion, atténuées par la redondance (S8, S10, S11 détectés par d'autres modules) | piste : fonction de contrôle levant `AssertionError` + témoin sur dossier temporaire altéré | **souhaitable, non appliqué** (pas de vacuité à corriger ; décision de Rémy) |
| R1 / w4 (`AFTER UPDATE`) | `test_009c`, groupe E | attendu **établi** : modèle V3.14 ligne 540 (« un trigger `BEFORE` s'exécute avant les CHECK, donc … remonte avec le message `INV-xx` du trigger ») et en-tête de 009c | nouveau test : `UPDATE … SET statut='annule'` incomplet (viole aussi un `CHECK`) sur un BC refusé par la garde → message `INV-44` ; témoin sur un BC sans facture → `CHECK constraint failed` | **appliqué** (R1, attendu établi) |
| R1 / e6 (`NEW.id`) | — | priorité de message entre `INV-44` et `INV-186` quand l'`id` change dans le même `UPDATE` : **non documentée** | aucune | **question à arbitrer**, code inchangé |
| R1 / m4, m5 (libellés) | — | le modèle impose le préfixe `INV-xx` ; les libellés complets ne sont pas contractualisés | aucune | **question à arbitrer**, code inchangé |

**Compatibilité** : aucune migration n'est modifiée ; les ajouts n'emploient que `shutil`, `tempfile` (bibliothèque standard) et les aides existantes ; `test_006` utilise déjà un dossier temporaire du système. **Effet documentaire à signaler sans le corriger** : `test_009c` passerait de 59 à 61 tests (deux ajouts : témoin de collection, test `BEFORE`), alors que T-54 indique « 59 tests en 8 groupes » ; le modèle n'est pas modifié (décision de Rémy).

**Plan de vérification** : tests directs des trois fichiers ; suite métier complète ; sur la copie isolée (hors dépôt), recopie des fichiers corrigés puis réévaluation : mutants C10, C11, C13, C17, C18 et mutants A3 à A7 réécrits contre le code corrigé, mutant SQL w4, scénarios S2, S3, S4, S5, S6, S10, S11 ; réconciliation finale.

### D bis. Résultats (copie isolée reconstruite depuis le dépôt corrigé)
Constats à ne pas confondre : (1) « les tests corrigés passent » ; (2) « tel mutant est maintenant tué » ; (3) « tel survivant est équivalent, sans effet ou reste une lacune » ; (4) « la migration est validée » — **(4) n'est pas établi** ; verdict limité en F.

**Corrections apportées**
- `test_009c` : `migrations_suivantes(dossier=None)` accepte un dossier alternatif ; `suite_conserve_le_trigger` retourne la liste des migrations rejouées et contrôlées ; le test sur la chaîne réelle compare cette liste à celle construite par comparaison de noms (`> NOM_009C`) ; **nouveau témoin** `test_009c_H_temoin_une_010_posee_dans_le_dossier_est_collectee_rejouee_et_controlee` : un dossier temporaire reçoit les 15 migrations livrées puis des 010 et 011 réelles ; il vérifie noms et rangs collectés (16, 17), le rejeu dans l'ordre, puis que trois défauts (010 qui supprime le trigger, qui le recrée altéré, qui le laisse intact mais inopérant) sont collectés et refusés par la garde ; **nouveau test** `test_009c_E_le_trigger_est_BEFORE_le_refus_INV_44_remonte_avant_les_CHECK_de_la_ligne` (R1, attendu établi : modèle V3.14 ligne 540 et en-tête de 009c) ; imports `shutil`, `tempfile`.
- `test_009a` : constante `NOM_009B` ; `suite_conserve_le_trigger` retourne les noms rejoués ; le test de chaîne exige que la première migration examinée soit `(14, 009b_acompte_garanties_manuelles.sql)` (non-vacuité) et que toutes les migrations collectées aient été rejouées et contrôlées.
- `test_009b_couverture` : **non modifié** (voir réserves).

**Mutants visés : avant → après correction**
| Mutant | Avant | Après | Détecteur après correction |
|---|---|---|---|
| C10 (tranche décalée, groupe H) | survivant (S2 non détecté par les 4 modules) | **tué** | témoin « 010 posée dans le dossier » |
| C11 (rang `RANG + i`) | survivant sans 010 | **tué** | même témoin |
| C13 (contrôle d'effectivité supprimé) | survivant (S4 non détecté) | **tué** | même témoin, cas `010_inoperante` ; avec C24 (ce cas supprimé) + C13, S0 et S4 passent sur les 4 modules : ce cas est l'unique détecteur, non redondant |
| C17 (appel supprimé) | survivant (S4 non détecté) | **tué** | test sur la chaîne réelle (`NameError` sur `controlees`) |
| A3, A4, A5, A6, A7 (`test_009a`) | survivants (A6 sans effet) | **tués** | assertion de non-vacuité du test `…_apres_chaque_migration_suivante` |
| A13 (appel supprimé), A16 (appel remplacé par une liste vide) | nouveaux | **tués** | même test |
| w4 (SQL : `AFTER UPDATE`) | survivant | **tué** | nouveau test `BEFORE` du groupe E |
C1 complet : 52 mutants, 44 tués, 7 survivants, 1 non exécutable (g7) ; seul w4 a changé de statut. Les autres statuts de C1 sont identiques à ceux d'avant correction.

**Survivants restants après correction (aucun non classé)**
| Mutant | Observation | Classement |
|---|---|---|
| g6, w5, o5, a6 (SQL) | équivalents ou sans effet dans la chaîne, prouvés à l'étape 2 (bloc 23:31, D bis) | équivalent / sans effet |
| e6 (SQL, `NEW.id`) | priorité de message `INV-44` / `INV-186` quand l'`id` change dans le même `UPDATE` : **non documentée** | **question à arbitrer** (R1), code inchangé |
| m4, m5 (SQL, libellés) | le modèle impose le préfixe `INV-xx`, pas le libellé complet | **question à arbitrer** (R1), code inchangé |
| A14, A15 (`test_009a`) | suppression de l'assertion de non-vacuité ou de l'assertion sur les migrations contrôlées : l'appel reste, le test redevient aussi faible qu'avant ; détectable seulement par un méta-test | limite de la méthode (suppression d'une assertion), pas un défaut de chaîne non détecté |
| C17b (`test_009c`, appel remplacé par `controlees = []`) | **inhérent tant qu'aucune 010 n'existe** : la liste attendue est vide ; sera tué dès qu'une 010 existera | limite temporaire, documentée |
| C18, C22, C23 (`test_009c`) | assertions redondantes avec d'autres contrôles (S2 et S3 restent détectés ; boucle des défauts du témoin) | sans effet observable |
| C24 (cas `010_inoperante` supprimé du témoin) | fait survivre C13 (voir ci-dessus) | confirme que ce cas est nécessaire |
Non traités (souhaitables, hors correction minimale) : B1, B2, B10 à B13 de `test_009b_couverture` (pas d'itération vide : 12 empreintes littérales ; ces mutants sont des suppressions d'assertion, atténuées par la redondance entre modules) ; C1 à C6 et C8 de `test_009c` (assertions redondantes) ; B1 et C7 dépendent des fins de ligne (tués en CRLF, survivants en LF).

**Scénarios de défauts de chaîne rejoués sur le code corrigé** (copie CRLF) : S0 et S1 (010 neutre) : 4 modules OK (aucun faux positif) ; S2, S3, S4, S5, S9 : seul `test_009c` échoue ; S6 : `test_009a`, `test_009b_acompte`, `test_009c` ; S7 : `test_009a`, `test_009c` ; S8 : `test_009b_couverture`, `test_009c` ; S10 et S11 : les 4 modules. Combinaisons (S2+C10, S2+C17, S3+C13, S4+C13, S4+C17, S4+C10, S6+A3/A4/A5/A7/A13, S10+A14) : le défaut reste détecté par au moins `test_009c` (et `test_009a` pour S6) avec le mutant en place.

**Effets documentaires et qualité (non corrigés ici)** : `test_009c` passe de 59 à **61 tests** (T-54 indique « 59 tests en 8 groupes » ; 8 groupes inchangés) et la suite de 2101 à **2103** ; le modèle n'est pas modifié (décision de Rémy). `ResourceWarning: unclosed database` : 1727 contre 1608 (les nouveaux tests ouvrent des bases comme les aides existantes) ; point de qualité, non corrigé. T-54 « campagne de mutation (20 mutants) » : toujours **non démontré** [NON VÉRIFIÉ] ; une nouvelle campagne ne le prouve pas rétroactivement.

**Réserves encore ouvertes** : R1 (e6, m4, m5 : à arbitrer) ; R4 (outil ad hoc hors dépôt et non versionné, mutants écrits à la main, pas de campagne SQL sur 009b, atomicité « avoir + annulation » hors périmètre, rang 15 et D-63 sans source primaire dans le dépôt, mutants et scénarios évalués en CRLF seulement). R2 (C10, C13, C17) et R3 (A3, A4, A5, A7) : traités.

**Anomalie de traçabilité n° 1 (mise à jour)** : `.claude/settings.local.json` est passé de 3599 octets (00:42:31) à **4108 octets (01:07:36)**, SHA-256 `e4daa88cd4448eb1cc478a0506d75f36744288f35072db7b404b7c580cb686ed` ; modifié pendant cette session sans écriture volontaire de ma part ; cause la plus probable (observée au bloc 23:31) : consignation des autorisations d'outils approuvées ; mécanisme [NON VÉRIFIÉ] ; non modifié, non supprimé.

### E. Clôture — relevé final (2026-10-19 01:30 à 01:35)
- Branche `main`, HEAD `a99d4c2`, retard 1 sur `origin/main` (référence locale, aucun fetch) ; indexé : rien ; stash : 0 [FAIT-VÉRIFIÉ]
- Suivis modifiés : 7 ; `git diff --stat` : 7 fichiers, **+61 / −22** (contre +51 / −20 à l'ouverture : la différence est exactement celle de `test_009a`, + 10 / − 2) ; entrées `git status` : 24, mêmes noms qu'en A ; `test_009c` est non suivi, donc absent du `diff --stat` [FAIT-VÉRIFIÉ]
- Ignorés : `dist/` (10:27:08) et `src-tauri/tests/metier/__pycache__/` (13:38:02, 16 fichiers) inchangés ; `.claude/settings.local.json` : 4108 octets, 01:07:36, SHA-256 `e4daa88c…86ed` (voir D bis) [FAIT-VÉRIFIÉ]
- Empreintes de 23 fichiers comparées à A : **20 identiques** (`CLAUDE.md`, `docs/README.md`, `conventions-techniques-v6.md`, 15 migrations, `test_009b_couverture_situations.py`, `test_009b_acompte_garanties_manuelles.py`) ; **3 différentes, toutes attendues ou déjà suivies** : `test_009a_…py` (`5e10e723…` → `f4d835f5…`), `test_009c_…py` (`78ffec0f…` → `746bccab…`), `.claude/settings.local.json` ; blobs Git de `invariants.md` `acb7bd0`, `cdc-errata-v6.md` `3065de1`, `modèle-données-sqlite-v6-v3.14.md` `9024c82` identiques [FAIT-VÉRIFIÉ]
- Recherche `find -newermt "2026-10-19 00:56:00"` dans le dépôt (hors `.git`, `node_modules`, journal, `.claude/`) : exactement les deux fichiers de test modifiés, aucun autre [FAIT-VÉRIFIÉ]
- Arbres `src-tauri/migrations` et `src-tauri/tests` du dépôt (hors `__pycache__`) **identiques à `ref`** (copie faite à 01:07, après les corrections) ; `work` et `work_lf` conformes à `ref` ; aucun mutant résiduel [FAIT-VÉRIFIÉ]
- Journal avant ce complément : 489 CRLF, 0 LF isolé, 1 CR isolé (anomalie n° 2, inchangée) [FAIT-VÉRIFIÉ]
- Portée du relevé final : suivis ☑ (statut, `diff --stat`) · non suivis ☑ (par nom et dates récentes) · ignorés ☑ (présence, dates, empreinte de `.claude/settings.local.json`) · contenu par empreinte ☑ (23 fichiers, arbres `src-tauri/migrations` et `tests`). **Non contrôlé :** contenu des autres entrées non suivies (`src/`, `public/`, `reprise-autonome-*/`, fichiers de configuration) autrement que par date de modification, `node_modules/`, `.git/index`, contenu de `__pycache__/`, dossier temporaire du système (les tests de cette session utilisent `tempfile.TemporaryDirectory`, nettoyés à la fin de chaque test).

### F. Réconciliation
- Écarts initial → final : (a) ce journal ; (b) les deux fichiers de test modifiés **sur autorisation de Rémy** (`test_009a`, `test_009c`) ; (c) `.claude/settings.local.json` (anomalie n° 1). Aucun autre écart sur la portée contrôlée. Aucune mutation n'a été appliquée au dépôt ; aucune migration ni document de référence modifié ; aucun mutant ne subsiste [FAIT-VÉRIFIÉ].
- Registre B tenu sur toute la session : oui. Effets de bord : `__pycache__` du dépôt non modifié grâce à `-B`.
- **Verdict : DISCORDANT, limité à `.claude/settings.local.json`** (anomalie n° 1, suivie séparément) ; les deux modifications de test sont attendues et vérifiées par empreinte. Pour le reste de la portée : CONCORDANT-NON-PROUVÉ (contenu hors portée non contrôlé par empreinte).
- Fiabilité : PARTIEL (portée partielle)
- **Verdict proposé sur la garde SQL de 009c (périmètre limité ; la décision d'intégration est prise séparément par Rémy)** : **validable sous réserves précisément énoncées** — les lacunes C10, C13, C17 (garde de chaîne) et A3, A4, A5, A7 (non-vacuité de `test_009a`) sont corrigées et vérifiées par mutation ; reste R1 (e6, m4, m5 à arbitrer ; w4 traité) et R4 (limites de la campagne, atomicité hors périmètre, source primaire de D-63 et du rang 15 absente du dépôt, T-54 non démontré) ; compteur de tests de T-54 (59) devenu inexact (61). 009c n'est pas déclarée validée.
Clôture : CLÔTURÉE 2026-10-19 01:32

---

## Session 2026-10-18 23:31 — Claude Code — étape 2 : campagnes de mutation ciblées sur copie isolée (009a, 009b, 009c)
Clôture : CLÔTURÉE le 2026-10-19 à 00:42 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-18 23:31:26, avant toute action d'écriture de cette session)
- `CLAUDE.md` (début) et dernier bloc du journal (23:01 : CLÔTURÉE le 23:17, verdict DISCORDANT limité à `.claude/settings.local.json`) lus avant toute autre action [FAIT-VÉRIFIÉ]
- Branche `main`, HEAD `a99d4c2`, avance 0 / retard 1 sur `origin/main` (référence locale, aucun fetch) ; indexé : rien ; stash : 0 [FAIT-VÉRIFIÉ]
- Suivis modifiés : 7 ; `git diff --stat` : 7 fichiers, +51 / −20 ; non suivis : 17 entrées ; mêmes noms qu'à la clôture du bloc 23:01 [FAIT-VÉRIFIÉ]
- Ignorés : `dist/` (10:27:08) et `src-tauri/tests/metier/__pycache__/` (13:38:02, 16 fichiers) inchangés ; `.claude/settings.local.json` : **1838 octets, 23:17:10, SHA-256 `293fc5400c50b086264f7caf80062e46a00a7f3641b24e8e8bd43ce6b0245156`**, contre 1638 octets, 23:06:49, `4285913e…` à la clôture du bloc 23:01 (anomalie n° 1 : variation constatée, origine [NON VÉRIFIÉ], non modifié) [FAIT-VÉRIFIÉ]
- Empreintes SHA-256 de 23 fichiers (`CLAUDE.md`, `docs/README.md`, `conventions-techniques-v6.md`, 15 migrations, 4 tests métier, `.claude/settings.local.json`) : **22 identiques** aux valeurs du relevé A du bloc 23:01 (liste complète dans ce bloc), 1 différente (`.claude/settings.local.json`, voir ci-dessus) ; comparaison automatique ; blobs Git de `invariants.md` `acb7bd0`, `cdc-errata-v6.md` `3065de1`, `modèle-données-sqlite-v6-v3.14.md` `9024c82` identiques [FAIT-VÉRIFIÉ]
- Journal : 298 CRLF, 0 LF isolé, 1 CR isolé (anomalie n° 2 du bloc 23:01, inchangée) [FAIT-VÉRIFIÉ]
- Fins de ligne : les 15 migrations et les 16 fichiers de test du dépôt sont **entièrement en CRLF** (comptage d'octets) [FAIT-VÉRIFIÉ]
- Portée du relevé : suivis ☑ (statut, `diff --stat`) · non suivis ☑ (par nom) · ignorés ☑ (présence, dates, empreinte de `.claude/settings.local.json`) · contenu par empreinte ☑ (23 fichiers). **Non contrôlé :** contenu des autres entrées non suivies (`src/`, `public/`, `reprise-autonome-*/`, fichiers de configuration), `node_modules/`, `.git/index`, contenu de `__pycache__/`, dossier temporaire du système.

### B. Registre des actions
Légende de la colonne Cible : **dépôt** = répertoire de travail du projet ; **copie** = copie temporaire hors dépôt ; **scratchpad** = dossier temporaire de l'outil, hors dépôt.
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | dépôt (`docs/suivi/journal-continuite.md`) | insérer ce bloc au-dessus du bloc 23:01 sans modifier celui-ci ni le CR isolé du bloc 22:14 | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Fichier d'empreintes `h_ouverture.txt` créé par erreur dans `/tmp` (dossier temporaire du système), puis déplacé vers le scratchpad (`h_ouverture_2.txt`) | hors dépôt | conserver les empreintes d'ouverture | déplacé ; absence de `/tmp/h_ouverture.txt` vérifiée | [FAIT-VÉRIFIÉ] |
| 3 | Création de la copie isolée (commande `setup` du pilote) : `mutwork/ref` (lecture seule), `mutwork/work` (fins de ligne du dépôt, CRLF), `mutwork/work_lf` (mêmes fichiers en LF) ; contenu : `src-tauri/migrations`, `src-tauri/tests` et une copie en lecture seule de `docs/conception/modèle-données-sqlite-v6-v3.14.md` | copie (scratchpad, hors dépôt) | disposer d'un arbre où muter sans toucher au dépôt | créée ; au relevé final, `ref` est identique au dépôt (migrations : 16 fichiers, tests : 17 fichiers, hors `__pycache__`) ; la copie du document du modèle a été ajoutée après un premier échec de baseline (voir D, rectification) | [FAIT-VÉRIFIÉ] |
| 4 | Écriture du pilote `mutcamp.py` (bibliothèque standard seule), de scripts d'exécution (`run_*.sh`), de sondes (`probe_w4.py`, `probe_equiv.py`), de journaux et de résultats (`mut_results/`, `mut_results_all/`, `synthese_campagnes.txt`) | scratchpad (hors dépôt) | outil ad hoc ; non ajouté au dépôt | créés | [FAIT-VÉRIFIÉ] |
| 5 | Mutations des campagnes C1 à C4, scénarios S0 à S11, combinaisons « mutant de test + défaut de chaîne » | copie `work` (et `work_lf` pour C3 et C4 en LF) | une modification à la fois ; restauration par empreinte après chacune | `assert_pristine` (copie comparée à `ref`) exécuté avant et après chaque mutant et chaque scénario, sans échec ; au relevé final `work` = `ref` et `work_lf` = `ref` normalisée LF ; aucun fichier intercalaire résiduel ; aucun `__pycache__` dans les copies | [FAIT-VÉRIFIÉ] pour les copies |
| 6 | Sondes de comportement (bases `:memory:` construites depuis `ref`) pour qualifier les survivants SQL | processus Python lisant `ref` | ne rien écrire | exécutées | [FAIT-VÉRIFIÉ] |
| 7 | Compléments au pilote : scénarios S10 et S11, option `NOFF` (exécution sans arrêt au premier échec, résultats dans `mut_results_all/`) ; sauvegardes `mutcamp.py.avant_s10`, `mutcamp.py.avant_noff` | scratchpad | corriger une limite de l'outil (voir D bis) | effectués | [FAIT-VÉRIFIÉ] |
| 8 | Complément de ce bloc (B, C, D bis, E, F) et clôture ; sauvegarde `journal.avant7` | ce journal | consigner résultats et réconciliation | effectuée ; octets des autres blocs préservés (vérifié par le script) | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
| Commande | Répertoire | Résultat | Portée / limites | Statut |
|---|---|---|---|---|
| Lecture de `CLAUDE.md` (début), du journal (bloc 23:01), des outils de `fichiers-a-relire/` (`outils_mutation_009.py` lignes 1 à 140, `classify009b.py`, `verifier_campagne_009.py`), recherches (`find`, `grep`) | racine | voir D | lecture seule | [FAIT-VÉRIFIÉ] |
| Relevé initial (`git`, `sha256sum`, `ls -l`, script Python en lecture seule) | racine | voir A | lecture seule | [FAIT-VÉRIFIÉ] |
| `python -B mutcamp.py setup`, puis `baseline --env crlf` et `baseline --env lf` | scratchpad | copies créées ; baselines (`unittest` dans la copie) : 009a 57 tests, 009b_acompte 106, 009b_couverture 13, 009c 59, tous OK dans les deux environnements. Un premier baseline avait échoué sur `test_009b_couverture` (FileNotFoundError, document du modèle absent de la copie) : corrigé, refait | tests de la copie seulement | [FAIT-VÉRIFIÉ] |
| `python -B mutcamp.py c1 --only e1 w1` (mutants témoins) | scratchpad | e1 et w1 tués ; copie restaurée ; `src-tauri` du dépôt inchangé | | [FAIT-VÉRIFIÉ] |
| `c1`, `c2`, `c3 --env crlf`, `c3 --env lf`, `c4 --env crlf`, `c4 --env lf` (23:45:23 à 23:56:48) | scratchpad | résultats en D bis ; aucun traceback ; chaque campagne se termine par la ligne « copie restauree conforme, depot src-tauri inchange » | `unittest -f` (arrêt au premier échec) | [FAIT-VÉRIFIÉ] |
| `scen all --env crlf` (S0 à S9, 23:57:05 à 00:01:13) | scratchpad | résultats en D bis | | [FAIT-VÉRIFIÉ] |
| `probe_w4.py`, `probe_equiv.py` | scratchpad, lecture de `ref` | w4 : message différent dans 8 cas sur 16 ; e6 : 1 cas ; w5, o5, a6 : identiques sur 16 cas (voir D bis). Une première version de `probe_equiv.py` était invalide (méthode `monde` écrasant celle de la classe de base, aucun cas construit) : détectée, corrigée, refaite | 16 cas, non exhaustif | [FAIT-VÉRIFIÉ] |
| `run_combos.sh` : S10, S11 et 30 combinaisons (00:06:48 à environ 00:20) | scratchpad | 32 exécutions, aucun traceback ; résultats en D bis | | [FAIT-VÉRIFIÉ] |
| `run_noff.sh` : C1 à C4 en CRLF, sans arrêt au premier échec (00:20:47 à 00:27:36) | scratchpad | statuts identiques à ceux du premier passage sur les 96 mutants | établit les tests détecteurs complets (C1) | [FAIT-VÉRIFIÉ] |
| Relevé final : `git status --porcelain`, `git diff --stat`, `git diff --cached`, `git stash list`, `git hash-object` (3 fichiers), `sha256sum` (23 fichiers), `find -newermt`, comparaison des arbres `src-tauri/migrations` et `src-tauri/tests` à `ref`, comptage du journal | racine | voir E | lecture seule | [FAIT-VÉRIFIÉ] |
Aucun fetch, pull, commit, push, changement de branche, add, stash, restore, reset, clean [FAIT-VÉRIFIÉ par relevé final]. Les sorties complètes sont dans le scratchpad (hors dépôt).

### D. Autorisation, inspection des outils, plan et garanties d'isolation
**Autorisation de Rémy (message du 2026-10-18, étape 2)** : campagnes de mutation ciblées et isolées pour évaluer l'efficacité des tests de 009a, 009b (deux fichiers) et 009c ; périmètre métier inchangé : **garde SQL de 009c uniquement** ; interprétation C de conventions §7.1 ; aucune modification des migrations, tests, documents de référence, `CLAUDE.md`, `.gitignore`, `.claude/settings.local.json` du dépôt ; aucune opération Git d'état ou de synchronisation ; aucune installation de dépendance, aucun nouvel outil **dans le dépôt** ; copie temporaire isolée de `src-tauri/` autorisée hors du dépôt si aucun outil existant ne convient ; si l'isolation ou la restauration ne peut pas être garantie : arrêt sans mutation. T-53 et T-54 : ni modèle ni `CLAUDE.md` modifiés (T-54 reste [NON VÉRIFIÉ] ; une nouvelle campagne ne prouve pas rétroactivement l'ancienne). 1608 `ResourceWarning: unclosed database` de l'étape 1 : consignés comme point de qualité des tests, non corrigés.

**Inspection des outils existants (lecture seule) — conclusion : aucun outil existant n'est utilisable ici.**
- `fichiers-a-relire/outils_mutation_009.py` : preuves d'équivalence des 24 survivants de la campagne de `009_pv.sql` ; lié au texte de `009_pv.sql` et à `test_009_pv.py` ; ne génère ni n'exécute de campagne ; non adapté à 009a/009b/009c.
- `fichiers-a-relire/preuves_009_pv/outils/preuves_equivalence/campagne_mutation/classify009b.py` et `verifier_campagne_009.py` : classent ou vérifient les sorties d'une campagne déjà exécutée sur 009 ; **ils importent `genmut009b` et appellent `mut009b.py`, qui sont absents du dépôt** (recherche `find` : aucun fichier de ces noms) ; ils ne peuvent donc pas s'exécuter ; spécifiques à `009_pv.sql`.
- Les rapports `RAPPORT_MUTATION__007/008` citent des outils (`mut007.py`, `genmut007.py`…) décrits comme « hors dépôt » : absents.
- L'outil de campagne le plus proche (`mut009b.py`) est décrit comme travaillant « dans des copies de `src-tauri/` sous le dossier de travail donné » et n'écrivant pas dans le dépôt ; l'approche retenue ci-dessous est la même.

**Outil retenu : un pilote Python minimal (bibliothèque standard seule, aucune installation), écrit dans le scratchpad, hors du dépôt**, exécuté sur une **copie temporaire de `src-tauri/{migrations/metier,tests/metier}`** (hors dépôt). C'est un outil ad hoc créé pour cette étape ; il n'est pas ajouté au dépôt.

**Garanties d'isolation (à vérifier avant toute mutation, résultats consignés plus bas)** :
1. Les tests localisent les migrations par `pathlib.Path(__file__).resolve().parents[2] / "migrations"` : exécutés depuis la copie, ils lisent les migrations **de la copie** (lecture du code des tests + preuve par mutant témoin).
2. Aucun test ne référence `docs/`, `fichiers-a-relire/` ni un chemin hors de `src-tauri/` (recherche) ; les tests ouvrent des bases `:memory:` ; `test_006` utilise un dossier temporaire du système.
3. Empreintes du dépôt (23 fichiers) relevées avant et après chaque campagne ; la copie est comparée à sa référence après chaque mutant (restauration vérifiée par empreinte).
4. Exécution avec `python -B` (pas de bytecode) et répertoire courant dans la copie.
5. Si une de ces garanties échoue : arrêt sans mutation.

**Campagnes prévues** (détail et résultats dans les sections suivantes) :
- **C1** — mutants du SQL de `009c` évalués par `test_009c` (garde SQL, conditions, ordre, messages, WHEN, garde `user_version`, nom/DROP) ;
- **C2** — mutants du code de `test_009a` (filtre `NOM_SUCCESSEUR`, tranche, rang) et **épreuves de défauts de chaîne** pour établir si le test peut réussir à vide sans examiner 009b ;
- **C3** — mutants du code de `test_009b_couverture` (normalisation CRLF/LF, tranches `noms[12:14]`, assertions d'ordre, empreintes), avec un second environnement à fins de ligne LF pour qualifier les mutants dépendants de l'environnement ;
- **C4** — mutants des gardes de `test_009c` (groupes A, G, H) et épreuves de défauts de chaîne (migration suivante qui supprime ou altère le trigger, fichier intercalaire, altération de 006/009a/009b dans la copie) ;
- `test_009b_acompte_garanties_manuelles.py` : évalué par les épreuves de défauts de chaîne qui le concernent (altération de 009b dans la copie) ; **pas de campagne de mutation complète sur 009b** (hors du périmètre « garde SQL de 009c » ; limite à documenter).

**Rectification de la garantie d'isolation n° 2 (constatée au premier baseline)** : l'affirmation « aucun test ne référence `docs/` » était inexacte. `test_009b_couverture_situations.py` lit `docs/conception/modèle-données-sqlite-v6-v3.14.md` (chemin construit par segments `pathlib`, non repéré par ma recherche de la chaîne `docs/`). Le premier baseline dans la copie a échoué (FileNotFoundError). Correction : copie de ce document en lecture seule dans `ref`, `work` et `work_lf` (empreinte identique à celle du dépôt, vérifiée), baselines refaits. Ce test ne fait que lire ; le dépôt n'a pas été exposé en écriture. Garantie corrigée : les tests lisent le document du modèle (lecture seule), n'écrivent que dans des bases `:memory:` et, pour `test_006`, dans un dossier temporaire du système.

### D bis. Résultats des campagnes (copie isolée ; mutants écrits à la main)
Quatre constats à ne pas confondre : (1) « les tests existants passent » (étape 1, bloc 23:01) ; (2) « tel mutant est tué » ; (3) « tel survivant est équivalent, sans effet observable ou révèle une lacune » ; (4) « la migration est validée » — **(4) n'est pas établi par ce bloc au-delà du verdict limité donné en F**.

**Résultats par campagne** (premier passage, arrêt au premier échec ; un second passage sans arrêt a donné les mêmes statuts sur les 96 mutants distincts)
| Campagne | Cible mutée → module évalué | Générés | Exécutés | Tués | Survivants | Non exécutables | Non classés |
|---|---|---|---|---|---|---|---|
| C1 | SQL de 009c → `test_009c` | 52 | 51 | 43 | 8 | 1 (g7) | 0 |
| C2 | code de `test_009a` → `test_009a` | 12 | 12 | 7 | 5 | 0 | 0 |
| C3 (CRLF) | code de `test_009b_couverture` → lui-même | 14 | 14 | 9 | 5 | 0 | 0 |
| C3 (LF) | idem, copie à fins de ligne LF | 14 | 14 | 8 | 6 | 0 | 0 |
| C4 (CRLF) | code de `test_009c` (groupes A, G, H) → lui-même | 18 | 18 | 6 | 12 | 0 | 0 |
| C4 (LF) | idem, copie LF | 18 | 18 | 5 | 13 | 0 | 0 |
Taux : C1 donne 43 tués sur 51 exécutables (84 %), 43 sur 47 si l'on écarte les 4 survivants équivalents ou sans effet dans la chaîne (w5, o5, a6, g6). **Ces taux sont indicatifs, pas une preuve** : mutants choisis à la main (aucun générateur disponible), ensembles hétérogènes, certains posés comme « équivalence probable ». Pour C2 à C4 (mutations du code de test), un taux n'a pas de sens ; seuls comptent les survivants qualifiés.

**Tests détecteurs (C1, second passage complet)** : 59 tests de `test_009c` en échec pour g1, g2, g7 ; 37 à 38 pour w2 et w3 ; 9 à 35 pour e2, e3, e5, e7, o1 à o3, a1 à a4, a7, a9 à a11, r2, k4, m1 à m3 ; 3 à 8 pour e1, s1 à s3, o4, o6, a5, g8, k1, k3 ; **un seul test** pour g3, g4, g5 (`Chaine`, garde `user_version`), w1 et w6 (`GardeChaine`, témoins), e4 (`Encaissements`), a8 (`Factures`), r1 et k2 (`Messages`). Les mutants tués par un seul test reposent sur ce test unique. w6 (`=`/`<>` remplacés par `IS`/`IS NOT`, équivalent en comportement) est tué par un test de définition textuelle : les tests exigent le texte exact du trigger.

**Survivants SQL de 009c (C1) et qualification** (sondes sur 16 cas : annulation simple, avec changement d'`id`, avec modification contractuelle simultanée, pour 4 types de BC)
| Mutant | Modification | Condition métier / observation | Classement |
|---|---|---|---|
| w5 | `UPDATE OF statut` | identique sur 16 cas ; `WHEN` exige déjà un changement de `statut` | équivalent |
| o5 | `'situation'` ajouté à `NOT IN` | identique sur 16 cas ; la condition 2 précède la 3 dans le même trigger et vise `type = 'situation'` | équivalent |
| a6 | `<>` au lieu de `IS NOT` (motif d'avoir) | identique sur 16 cas ; `CHECK` de `006_facturation.sql:137` : `motif_avoir IS NOT NULL` pour un avoir, toujours présent au rang 15 | équivalent |
| g6 | `DROP TRIGGER IF EXISTS` | n'agit que si le trigger est absent d'une base au rang 14 ; la garde `user_version = 14` et 009a garantissent sa présence | sans effet observable dans la chaîne normale |
| w4 | `AFTER UPDATE` au lieu de `BEFORE UPDATE` | **non équivalent** : 8 cas sur 16 changent de message (`INV-186` au lieu de `INV-44`) quand l'`UPDATE` viole aussi le contenu contractuel ; refus identique ; 009c documente « BEFORE… avant les CHECK de la ligne » | lacune de couverture, impact limité au message et à l'ordre des règles |
| e6 | `NEW.id` au lieu de `OLD.id` (condition 1) | 1 cas sur 16 diffère (`id` modifié dans le même `UPDATE`) : autre message, refus identique | lacune de couverture, impact limité au message |
| m4 | mention `(D-05)` retirée du message 3 | les tests vérifient préfixe `INV-44`, messages distincts, ASCII, pas le libellé complet | lacune de couverture, impact limité au libellé |
| m5 | `neutralise` → `neutralisee` (message 4) | idem | lacune de couverture, impact limité au libellé |
Aucun survivant SQL ne change la décision d'accepter ou de refuser l'annulation sur les cas éprouvés. Mutant non exécutable : g7 (suppression du `DROP TRIGGER` : « trigger already exists »).

**Survivants des mutations de code de test** (le défaut de chaîne correspondant est éprouvé avec le mutant en place ; module = résultat du module muté, autres = résultat des trois autres modules)
| Mutant | Modification | Épreuve | Observation | Classement |
|---|---|---|---|---|
| A3, A4, A5, A7 (`test_009a`) | filtre inversé, `NOM_SUCCESSEUR` vide, tranche `[RANG + 1:]`, 009b exclue : la liste examinée devient vide | S6 (009b altérée : `DROP TRIGGER tr_103` en fin de fichier) | `test_009a` passe à vide ; `test_009b_acompte` et `test_009c` (groupe A) détectent S6 | lacune du module (aucune assertion de non-vacuité), atténuée par redondance entre modules |
| A6 (`test_009a`) | `RANG + 1 + i` → `RANG + i` | S6 | `test_009a` détecte S6 | sans effet observable |
| B1 (`test_009b_couverture`) | normalisation CRLF → LF supprimée | CRLF puis LF | tué en CRLF, survit en LF (normalisation sans objet) | dépend de l'environnement (limite de la campagne) |
| B2 | `replace(b'\r\n', b'\n')` → `replace(b'\r', b'')` | — | équivalent tant qu'aucun CR isolé n'existe (migrations 100 % CRLF, vérifié) | équivalent sur les données actuelles |
| B10, B11, B12 | assertions d'ordre ou de préfixe supprimées | S10, S11 | `test_009a`, `test_009b_acompte`, `test_009c` détectent ; `test_009b_couverture` lui-même détecte S11 mais pas S10 avec B10 | lacune du module, atténuée par redondance |
| B13 | assertion d'empreinte supprimée | S8 (006 altérée) | `test_009c` (groupe G) détecte | lacune du module, atténuée par redondance |
| C1 à C6 (`test_009c`, groupe A) | assertions de chaîne supprimées ou modifiées une à une | S5 (intercalaire 009b_zzz) | S5 reste détecté par `test_009c` groupe A | redondance observée sur S5 seulement ; équivalence non démontrée pour d'autres défauts |
| C7 | normalisation CRLF → LF supprimée (G) | CRLF puis LF | tué en CRLF, survit en LF | dépend de l'environnement |
| C8 | assertion d'empreinte supprimée (G) | S6, S7, S8 | détecté respectivement par `test_009a`, `test_009a`, `test_009b_couverture` | redondance entre modules |
| **C10** | tranche `[RANG:]` → `[RANG + 1:]` (groupe H) | S2 (010 supprime le trigger) | **aucun des 4 modules ne détecte S2** | **lacune significative de la garde de chaîne de `test_009c`** (non-vacuité de la liste examinée) |
| C11, C18 | rang passé à la migration suivante modifié, assertion `problemes_de_recreation == []` supprimée | S2, S3 | détectés par d'autres tests du groupe H | sans effet observable |
| **C13** | contrôle d'effectivité du refus supprimé (groupe H) | S2, S3, S4 | S2 et S3 détectés autrement ; **S4 (010 inopérante) non détecté** | **lacune significative** (aucun témoin pour ce contrôle) |
| **C17** | appel `suite_conserve_le_trigger(migrations_suivantes())` supprimé | S2, S3, S4 | S2 et S3 détectés par un autre test du groupe H ; **S4 non détecté** | **lacune significative** |

**Scénarios de défauts de chaîne** (copie CRLF, 42 lignes de résultats dans `scen_crlf.jsonl`) : S0 aucune modification : 4 modules OK. S1 migration 010 neutre : 4 modules OK (aucun faux positif). S2 (010 supprime le trigger), S3 (010 le recrée altéré), S4 (010 inopérante) : seul `test_009c` (groupe H) échoue ; `test_009a` n'examine volontairement que les migrations antérieures à 009c. S5 (fichier 009b_zzz intercalaire) : seul `test_009c` (groupe A). S6 (009b altérée) : `test_009a`, `test_009b_acompte`, `test_009c` ; pas `test_009b_couverture`. S7 (009a altérée) : `test_009a` et `test_009c` (groupe G). S8 (006 altérée) : `test_009b_couverture` et `test_009c` (groupe G). S9 (009c altérée dans la copie) : `test_009c`. S10 (intercalaire 009a_zzz) et S11 (intercalaire 008z) : les 4 modules.

**Lacunes de l'outil et de la campagne** : (a) pilote ad hoc créé hors dépôt, non versionné ; les outils existants de `fichiers-a-relire/` ne sont pas exécutables ici (dépendances absentes) ; (b) mutants écrits à la main, non exhaustifs, aucun générateur ; (c) le premier passage utilisait `unittest -f` : le champ « tueur » ne donnait que le premier échec, d'où le second passage (C1 à C4 en CRLF) ; les scénarios et les combinaisons n'ont été exécutés qu'en CRLF ; (d) pas de campagne de mutation sur le SQL de 009b (hors périmètre) ; (e) sondes limitées à 16 cas ; (f) atomicité « avoir + annulation » hors périmètre (non éprouvée par ces campagnes) ; (g) les scénarios ne contrôlent pas le dépôt à chaque exécution : le dépôt est contrôlé au relevé final et à chaque campagne `c1`-`c4` (arbre `src-tauri` comparé avant/après).

**Autres constats** : T-54 « campagne de mutation (20 mutants) » reste **non démontrée** [NON VÉRIFIÉ] ; une nouvelle campagne ne la prouve pas rétroactivement ; le modèle et `CLAUDE.md` ne sont pas modifiés. 1608 `ResourceWarning: unclosed database` (étape 1) : point de qualité des tests, non corrigé. Rang 15 et D-63 : confirmés par Rémy le 2026-10-18, source primaire toujours absente du dépôt. Aucun test ni migration modifié pour tuer un survivant.

**Anomalie de traçabilité n° 1 (mise à jour)** : `.claude/settings.local.json` est passé de 1838 octets (23:17:10) à **3414 octets (00:20:47)**, SHA-256 `9863aa4b2dbacfebc9e4d3d556bc113c9d8873ffe89516dde420c7fbf0d907f6`. Lecture seule du contenu : une seule clé `permissions` avec 35 règles `allow`, dont des commandes lancées pendant cette session (par exemple `nohup bash run_noff.sh`). Cause la plus probable : le harnais consigne les autorisations d'outils approuvées ; le mécanisme d'écriture n'est pas vérifié [NON VÉRIFIÉ] ; aucune écriture volontaire de ma part ; fichier non modifié, non supprimé ; suivi séparément selon l'arbitrage de Rémy.

### E. Clôture — relevé final (empreintes 2026-10-19 00:29:23 ; Git, parasites, `__pycache__` et journal entre 00:36 et 00:39)
- Branche `main`, HEAD `a99d4c2`, retard 1 sur `origin/main` (référence locale, aucun fetch) ; indexé : rien ; stash : 0 [FAIT-VÉRIFIÉ]
- Suivis modifiés : 7 ; `git diff --stat` : 7 fichiers, +51 / −20 ; entrées `git status` : 24 (7 suivies, 17 non suivies), mêmes noms qu'en A [FAIT-VÉRIFIÉ]
- Ignorés : `dist/` (10:27:08) et `src-tauri/tests/metier/__pycache__/` (13:38:02, 16 fichiers) inchangés ; `.claude/settings.local.json` : 3414 octets, 00:20:47, SHA-256 `9863aa4b…07f6` (voir D bis) [FAIT-VÉRIFIÉ]
- Empreintes (22 fichiers : `CLAUDE.md`, `docs/README.md`, `conventions-techniques-v6.md`, 15 migrations, 4 tests) : **identiques au relevé A** ; blobs Git de `invariants.md` `acb7bd0`, `cdc-errata-v6.md` `3065de1`, `modèle-données-sqlite-v6-v3.14.md` `9024c82` identiques [FAIT-VÉRIFIÉ]
- Arbres `src-tauri/migrations` (16 fichiers) et `src-tauri/tests` (17 fichiers, hors `__pycache__`) du dépôt **identiques à `ref`** (copie faite au `setup`) ; `src-tauri` ne contient pas d'autre fichier hors `__pycache__` [FAIT-VÉRIFIÉ]
- Recherche `find -newermt "2026-10-18 23:31:00"` dans le dépôt (hors `.git`, `node_modules`, journal et `.claude/`) : aucun fichier [FAIT-VÉRIFIÉ]
- Copies : `work` et `work_lf` conformes à `ref` (empreintes) ; `ref` en lecture seule ; aucun mutant résiduel [FAIT-VÉRIFIÉ]
- Journal avant ce complément : 351 CRLF, 0 LF isolé, 1 CR isolé (anomalie n° 2, inchangée) [FAIT-VÉRIFIÉ]
- Portée du relevé final : suivis ☑ (statut, `diff --stat`) · non suivis ☑ (par nom et dates récentes) · ignorés ☑ (présence, dates, empreinte de `.claude/settings.local.json`) · contenu par empreinte ☑ (23 fichiers, arbres `src-tauri/migrations` et `tests`). **Non contrôlé :** contenu des autres entrées non suivies (`src/`, `public/`, `reprise-autonome-*/`, fichiers de configuration) autrement que par date de modification, `node_modules/`, `.git/index`, contenu des fichiers de `__pycache__`, dossier temporaire du système.

### F. Réconciliation
- Écarts initial → final : (a) ce journal (B1, B8), exclu des comparaisons ; (b) `.claude/settings.local.json` (anomalie n° 1, voir D bis). Aucun autre écart sur la portée contrôlée. **Aucune mutation n'a été appliquée au dépôt** : toutes l'ont été à la copie ; aucun mutant ne subsiste dans le dépôt (empreintes et arbres identiques) ni dans la copie [FAIT-VÉRIFIÉ].
- Registre B tenu sur toute la session : oui. Effets de bord attendus : `__pycache__` du dépôt non modifié grâce à `-B` ; dossiers temporaires du système éventuellement créés puis supprimés par `test_006` : non contrôlés.
- **Verdict : DISCORDANT, limité à `.claude/settings.local.json`** (anomalie n° 1, suivie séparément). Pour le reste de la portée : CONCORDANT-NON-PROUVÉ (contenu hors portée non contrôlé par empreinte ; une modification non détectée n'est pas exclue).
- Fiabilité : PARTIEL (portée partielle)
- **Verdict sur la garde SQL de 009c (périmètre de l'étape 2, et lui seul)** : **validable sous réserves précisément énoncées** — (R1) timing `BEFORE`, priorité entre messages et libellés non couverts (w4, e6, m4, m5), sans effet sur l'acceptation ou le refus pour les cas éprouvés ; (R2) garde de chaîne de `test_009c` : trois lacunes sur la non-vacuité et l'effectivité (C10, C13, C17) ; (R3) `test_009a` et `test_009b_couverture` : assertions de non-vacuité absentes (A3, A4, A5, A7, B10 à B13), atténuées par la redondance entre modules ; (R4) campagne non exhaustive avec outil ad hoc hors dépôt, aucune campagne SQL sur 009b, atomicité hors périmètre, T-54 non démontré, rang 15 et D-63 sans source primaire dans le dépôt, résultats dépendants des fins de ligne pour B1 et C7. 009c n'est pas déclarée validée globalement.
Clôture : CLÔTURÉE 2026-10-19 00:42

---

## Session 2026-10-18 23:01 — Claude Code — reprise contrôlée, arbitrages de Rémy, exécution des tests métier existants (étape 1)
Clôture : CLÔTURÉE le 2026-10-18 à 23:17 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-18 23:01:01, avant toute action de cette session autre que des lectures)
- `CLAUDE.md` et ce journal lus avant toute autre action ; dernier bloc (22:14) : CLÔTURÉE le 22:36, verdict DISCORDANT limité à `.claude/settings.local.json` [FAIT-VÉRIFIÉ]
- Branche `main`, HEAD `a99d4c2`, avance 0 / retard 1 sur `origin/main` (référence locale, aucun fetch) ; indexé : rien ; stash : 0 [FAIT-VÉRIFIÉ]
- Suivis modifiés : 7 ; `git diff --stat` : 7 fichiers, +51 / −20 ; non suivis : 17 entrées [FAIT-VÉRIFIÉ]
- Ignorés : `dist/` (10:27:08) ; `src-tauri/tests/metier/__pycache__/` (13:38:02, 16 fichiers, le plus récent 13:38:02) ; `.claude/settings.local.json` : 915 octets, 22:19:06, SHA-256 `ac8d3ea6c18a5eea6c18d2324ff346890e779bc00dc3fa6161f955d94652ab83` [FAIT-VÉRIFIÉ]
- Écart avec l'état final du bloc 22:14 : **aucun** sur tous les éléments à empreinte, sur les noms, les compteurs et les ignorés contrôlés (à l'exception de ce journal, exclu des comparaisons) [FAIT-VÉRIFIÉ]
- Empreintes SHA-256 (octets bruts du fichier de travail) :
  - `CLAUDE.md` `93f8fec6a60be961a0fad856c672fd82653efef1363ca2a870bdba889ef3b682` ; `docs/README.md` `54d5e5968218cef8597c916f6c89c0cc7ae29d77f4ac3cfc3b29c7b4d83f57d4` ; `conventions-techniques-v6.md` `2e3fc5e2db9d4003da66ace5b78fedc059b591bbca25374672a35083e73b7595`
  - blobs Git de `invariants.md` `acb7bd0`, `cdc-errata-v6.md` `3065de1`, `modèle-données-sqlite-v6-v3.14.md` `9024c82`
  - migrations (`src-tauri/migrations/metier/`) :
    - `001_initial` `000505089027b6896cd0fff79ffcd7658f10c9db02620fed636defb58b204408`
    - `002_fournisseurs` `c8d5ba9e3b5cbd95cbc8c231f5667f91406c115eba171692e43cee0c592d37ad`
    - `003_devis` `7872f1e90c1c035727b15865f88d11dd5d4a765f7d0e743c063d4185930aa31f`
    - `004_bons_commande` `8e4de7f7d908552ec7d98eaa1bef050a8568535b02b8648ae3ec38a95453a11a`
    - `005_depenses` `ed8c3fd370d82ab04b1cff3e8ab6964a6657f23c7cdf94e1642800d642465c3b`
    - `005a_corrections_v313` `deae9e6514943756d1643490b260989d3b970ad51126018140639afbd90d6fbd`
    - `005b_bc_multi_devis` `98dc2fc4bc643fc3522bb8c15a8849ca94a84f67f39b525afeeb92680d2215c2`
    - `005c_bc_annule_caches_financiers` `2493a3bcbfe12f6eacdb2308c6c1dc6b69a9ba73614c9f5485bf88a717537681`
    - `006_facturation` `b4dad89414ca056281d44b16f8a7866efebe90f5be482a486a85a15bf0a56baa`
    - `007_reglements` `39e7170e4f91721727392b04f602da10e6bd8f367e64fda8f31223c15cfe752b`
    - `008_garanties` `c01bfe8d549ca05a90f9fdab01b11abbcf89bb8afb7fdd9e3bbe5db6381fa233`
    - `009_pv` `f436baadaec4f3cc2ac05f4afa7527275f01ea10886557179d7e4f8c4e72c49c`
    - `009a_bc_annulation_interdite_si_facture` `b53cd6df2880b5eb3d4e345b75c26a7471e28cac80e0e98b82135392d308c571`
    - `009b_acompte_garanties_manuelles` `8bfdbde0156e03c92908e7c1e86f500b6580de6046ea58fe64c1fe6d803c9255`
    - `009c_bc_annulation_acompte_encaissement` `662cc2ef7f53add4ffe4de22be0503b017dfbc28d704a9128f6796fc7f53585b`
  - tests (`src-tauri/tests/metier/`) :
    - `test_009a_bc_annulation_interdite_si_facture.py` `5e10e723e2f54955a7c6968a4606d86848896a72a88e1d07f27256ad424a176d`
    - `test_009b_couverture_situations.py` `90152ade4f613ba43d9eb20b1a353ca525594f07f16cc14177e6174c9fb0c994`
    - `test_009b_acompte_garanties_manuelles.py` `eb2169ce1b8f3cac3adc42ef27db300c5ac30b366369b2285f57214664bba4df`
    - `test_009c_bc_annulation_acompte_encaissement.py` `78ffec0fb51ba11856e5826b62b6cfcfd9b68457c91ab60cbf7dbf9ea7ac414f`
- Prérequis des tests : Python 3.14.8 (`C:\Users\Remy\AppData\Local\Programs\Python\Python314\python.exe`), SQLite 3.50.4 (le modèle exige ≥ 3.37) ; les tests ouvrent des bases `:memory:` ; `test_006_facturation.py` utilise `tempfile.TemporaryDirectory()` (dossier temporaire du système, supprimé par le test) [FAIT-VÉRIFIÉ par lecture et par `python -I`]
- Portée du relevé : suivis ☑ (statut, `diff --stat`) · non suivis ☑ (par nom) · ignorés ☑ (présence, dates, empreinte de `.claude/settings.local.json`, nombre de fichiers de `__pycache__`) · contenu par empreinte ☑ (fichiers listés). **Non contrôlé :** contenu des autres entrées non suivies (`src/`, `public/`, `reprise-autonome-*/`, fichiers de configuration), `node_modules/`, `.git/index`, contenu des fichiers de `__pycache__`.

### B. Registre des actions
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc | `docs/suivi/journal-continuite.md` | insérer ce bloc au-dessus du bloc 22:14 sans modifier celui-ci ni le caractère CR isolé décrit en D | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Sauvegarde du journal avant cette ouverture (`journal.avant4`), fichier de bloc `bloc_2301.md` et script d'insertion | hors dépôt (scratchpad de l'outil) | pouvoir comparer les blocs antérieurs | créés | [FAIT-VÉRIFIÉ] |
| 3 | Exécution des tests existants (voir C) | processus Python ; bases `:memory:` ; dossiers temporaires de `test_006_facturation.py` (supprimés par le test) | ne modifier aucun fichier ; éviter toute écriture de bytecode (option `-B`) | `__pycache__/` inchangé (16 fichiers, dates inchangées) ; aucun fichier suivi ou non suivi modifié (22 empreintes identiques à A, noms et compteurs Git identiques) ; état du dossier temporaire du système non contrôlé | [FAIT-VÉRIFIÉ] pour le dépôt |
| 4 | Journaux d'exécution `run_*.log`, `sha_apres_tests.txt`, `h_final.txt`, scripts `close_bloc_2301.py` et sauvegarde `journal.avant5` | hors dépôt (scratchpad de l'outil) | conserver les sorties complètes des tests | créés | [FAIT-VÉRIFIÉ] |
| 5 | Complément de ce bloc (B, C, D bis, E, F) et clôture | ce journal | consigner résultats et réconciliation | effectuée ; octets des autres blocs préservés | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
| Commande | Répertoire | Résultat | Portée / limites | Statut |
|---|---|---|---|---|
| Lecture de `CLAUDE.md` (lignes 1 à 12) et du journal (lignes 60 à 131) | racine | lus | `CLAUDE.md` avait été lu en entier plus tôt dans la même conversation | [FAIT-VÉRIFIÉ] |
| Relevé initial (`git branch`, `rev-parse`, `rev-list`, `status`, `diff --stat`, `stash list`, `sha256sum`, `ls -l`, `git hash-object`, `python -I --version`, `sqlite3.sqlite_version`) | racine | voir A | lecture seule | [FAIT-VÉRIFIÉ] |
| Contrôle des octets du journal (script Python en lecture seule) | racine | 193 CRLF, 0 LF isolé, **1 CR isolé** (voir D) | lecture seule | [FAIT-VÉRIFIÉ] |
| Première tentative d'écriture de ce bloc par un script en ligne | racine | erreur de syntaxe du shell avant exécution ; **rien écrit** (vérifié : bloc absent, 24 entrées Git) | — | [FAIT-VÉRIFIÉ] |
| `python -B src-tauri/tests/metier/test_009a_bc_annulation_interdite_si_facture.py` | racine | code de sortie 0 ; `Ran 57 tests in 2.615s` ; `OK` | ce fichier seul | [FAIT-VÉRIFIÉ] |
| `python -B src-tauri/tests/metier/test_009b_acompte_garanties_manuelles.py` | racine | code 0 ; `Ran 106 tests in 5.072s` ; `OK` | ce fichier seul | [FAIT-VÉRIFIÉ] |
| `python -B src-tauri/tests/metier/test_009b_couverture_situations.py` | racine | code 0 ; `Ran 13 tests in 0.914s` ; `OK` | ce fichier seul | [FAIT-VÉRIFIÉ] |
| `python -B src-tauri/tests/metier/test_009c_bc_annulation_acompte_encaissement.py` | racine | code 0 ; `Ran 59 tests in 3.296s` ; `OK` | ce fichier seul | [FAIT-VÉRIFIÉ] |
| `python -B -m unittest discover -s src-tauri/tests/metier -p "test_*.py" -v` (commande documentée, **avec l'option `-B` ajoutée** pour ne pas écrire de bytecode) | racine | code 0 ; `Ran 2101 tests in 87.323s` ; `OK` ; 0 FAIL, 0 ERROR, 0 test ignoré ; 16 modules chargés (de `test_001_initial` à `test_009c_…`) ; 1608 lignes `ResourceWarning: unclosed database` (avertissements, pas des échecs) | **uniquement** `src-tauri/tests/metier/` ; hors portée : `src-tauri/tests/machine/test_premier_demarrage.py` (non exécuté), campagnes de mutation, front | [FAIT-VÉRIFIÉ] |
Les sorties complètes sont dans le scratchpad de l'outil (hors dépôt). Aucune campagne de mutation lancée. Aucun fetch, pull, commit, push, changement de branche, add, stash, restore, reset, clean [FAIT-VÉRIFIÉ par relevé final].

### D. Arbitrages de Rémy, références, anomalies, points non résolus
**Arbitrages confirmés par Rémy le 2026-10-18** (message de reprise de cette session ; source primaire : ce message, hors dépôt) :
- Conventions §7.1 : **interprétation C** retenue comme arbitrage explicite (la campagne de mutation concernée par le trigger de 009a est réévaluée ; cela couvre 009c et les contrôles affectés). Ce n'est pas une affirmation que le texte exclut toute autre lecture. [décision du propriétaire]
- **D-63 et rang 15 de 009c : confirmés par Rémy.** Aucune source primaire n'a été retrouvée dans le dépôt ; la confirmation est celle du message de reprise cité ci-dessus. Statut documentaire des documents qui les portent : inchangé ([LOCAL]/[REL]).
- Vérifications autorisées **par étapes** : étape 1 = exécution des tests existants, sans modifier le SQL ni les tests ; examen des résultats ; étape 2 = campagnes de mutation ciblées, **après décision de Rémy**. Cette session ne traite que l'étape 1.
- Périmètre de validation : **garde SQL de 009c uniquement** ; l'atomicité applicative complète est hors périmètre (service absent).
- `.claude/settings.local.json` : **anomalie de traçabilité distincte**, à suivre séparément ; ne pas l'ignorer, la supprimer ni la corriger sans autorisation.
- T-54 « campagne de mutation (20 mutants) » : le modèle reste **sans modification** ; l'affirmation reste [NON VÉRIFIÉ] dans le suivi.
- Référence : rapport d'analyse en lecture seule de 009c remis à Rémy après la clôture du bloc 22:14 (résumé en D de ce bloc 22:14).

**Anomalie de traçabilité n° 1 — `.claude/settings.local.json`** : 250 octets (21:39:05) → 706 (22:04:13) → 915 (22:19:06) ; inchangé entre 22:19:06 et le relevé de 23:01:01. Origine exacte [NON VÉRIFIÉ] ; non modifié, non supprimé.

**Anomalie de traçabilité n° 2 — caractère CR isolé dans un bloc clôturé** : le bloc 22:14 contient un octet CR (0x0D) isolé au milieu de la 3e puce de sa section D (décalage 12570 du fichier à l'ouverture de ce bloc), à l'endroit où devait figurer l'écriture littérale du motif de la commande `grep -c` (dollar, apostrophe, antislash, r, apostrophe). Cause : échappement mal géré dans le script qui a écrit ce texte. Effet : la mention s'affiche « $'' » ; la lecture correcte est `grep -c $'\r'`. Conformément à la règle 2 du préambule, le bloc 22:14 n'est pas modifié ; cette rectification est portée ici. Le contrôle « 0 LF isolé » consigné alors ne comptait pas les CR isolés [FAIT-VÉRIFIÉ].

**Points non résolus** : hiérarchie documentaire (conflit ouvert) ; statut historique du registre des invariants ; cellule T-53 du modèle V3.14 [NON VÉRIFIÉ] ; T-54 [NON VÉRIFIÉ] ; INV-188 cité par 009c mais absent de `invariants.md`.
**Prochaine étape [PRÉVU]** : exécuter les tests métier existants de 009a, 009b et 009c, puis la suite métier, sans rien modifier ; présenter les résultats et attendre la décision de Rémy avant toute campagne de mutation.

### D bis. Résultats de l'étape 1 (tests existants)
Trois constats distincts, à ne pas confondre : (1) « les tests exécutés passent » ; (2) « les mutants ciblés sont tués » ; (3) « la migration est validée ». **Seul le constat (1) est établi ici ; (2) et (3) ne le sont pas.**
- **Constat (1)** : tous les tests exécutés ont réussi (code de sortie 0 pour les 4 fichiers pris isolément et pour la suite métier : 2101 tests, 0 échec, 0 erreur, 0 ignoré) [FAIT-VÉRIFIÉ]. Aucun diagnostic de correction n'est donc nécessaire.
- **Couverture de ces tests** : les 16 fichiers `test_*.py` de `src-tauri/tests/metier/`. Ne sont **pas** couverts : la base machine (`test_premier_demarrage.py` non exécuté), les campagnes de mutation, le front, l'atomicité applicative (aucun service), les migrations suivantes (inexistantes).
- **Écarts entre résultat observé et affirmations documentaires** :
  - T-54 « 59 tests en 8 groupes » : 59 tests exécutés, tous OK (concordant). T-54 « campagne de mutation (20 mutants) » : **non démontrée**, reste [NON VÉRIFIÉ] ; le modèle n'est pas modifié (arbitrage de Rémy).
  - T-53 « 13 tests … écrits et exécutés avec succès dans `test_009b_couverture_situations.py` » : 13 tests exécutés, tous OK le 2026-10-18 à 23:08:41, sur l'arbre actuel. La partie « exécution » de cette cellule est donc étayée pour ce fichier ; la cellule reste inchangée et `CLAUDE.md` §2 (qui la dit [NON VÉRIFIÉ]) n'est pas modifié sans l'accord de Rémy.
  - Reprise du 13/10 : « 1 916 tests, 13 modules » (copie hors dépôt, 50 tests pour 009a) contre 2101 tests et 16 modules aujourd'hui (57 tests pour 009a) : non comparables, l'état du dépôt a changé.
  - 1608 `ResourceWarning: unclosed database` : connexions non fermées dans les aides de test ; sans effet sur les verdicts, à noter comme défaut de qualité des tests.
- **Anomalie de traçabilité n° 1 (mise à jour)** : `.claude/settings.local.json` est passé de 915 octets (22:19:06) à **1638 octets (23:06:49)**, SHA-256 `4285913edeaef50717e28aa4539c2478b1213cbb3a94d0ac07532abaf18ac2f6` ; modifié pendant cette session sans écriture volontaire sur ce fichier ; origine exacte [NON VÉRIFIÉ] ; non modifié, non supprimé.
- **État** : étape 1 terminée ; l'étape 2 (campagnes de mutation) n'est pas commencée ; **elle attend la décision de Rémy**. 009c n'est pas déclarée validée.

### E. Clôture — relevé final (2026-10-18 23:13:18 ; empreintes revérifiées à 23:15:30)
- Branche `main`, HEAD `a99d4c2`, avance 0 / retard 1 sur `origin/main` (référence locale) ; indexé : rien ; stash : 0 [FAIT-VÉRIFIÉ]
- Suivis modifiés : 7 ; `git diff --stat` : 7 fichiers, +51 / −20 ; non suivis : 17 entrées ; mêmes noms qu'en A [FAIT-VÉRIFIÉ]
- Ignorés : `dist/` et `src-tauri/tests/metier/__pycache__/` (16 fichiers, dates inchangées) ; `.claude/settings.local.json` : 1638 octets, 23:06:49, SHA-256 `4285913e…ac2f6` (voir D bis) [FAIT-VÉRIFIÉ]
- Empreintes (22 fichiers : `CLAUDE.md`, `docs/README.md`, `conventions-techniques-v6.md`, 15 migrations, 4 tests) : **identiques au relevé A** ; blobs Git de `invariants.md`, `cdc-errata-v6.md`, `modèle-données-sqlite-v6-v3.14.md` : identiques à A [FAIT-VÉRIFIÉ]
- Portée du relevé final : identique à A.

### F. Réconciliation
- Écarts initial → final : (a) ce journal (B1, B5), exclu des comparaisons ; (b) `.claude/settings.local.json` (anomalie n° 1, voir D bis). Aucun autre écart sur la portée contrôlée. Aucun mutant ni changement temporaire n'a été introduit (aucune mutation lancée ; aucun fichier de migration ou de test modifié, vérifié par empreintes) [FAIT-VÉRIFIÉ].
- Registre B tenu sur toute la session : oui. Effet de bord attendu des tests : `__pycache__` non modifié grâce à `-B` [FAIT-VÉRIFIÉ] ; dossiers temporaires du système éventuellement créés puis supprimés par `test_006` : non contrôlés.
- Portée du verdict : noms de fichiers suivis et non suivis, compteurs de `diff --stat`, 22 empreintes de fichiers, blobs Git de 3 fichiers, empreinte de `.claude/settings.local.json`, présence et dates de `dist/` et `__pycache__/`. **Non contrôlé :** contenu des autres entrées non suivies (`src/`, `public/`, `reprise-autonome-*/`, fichiers de configuration), `node_modules/`, `.git/index`, contenu des fichiers de `__pycache__`, dossier temporaire du système.
- **Verdict : DISCORDANT, limité à `.claude/settings.local.json`** (anomalie n° 1, suivie séparément selon l'arbitrage de Rémy). Pour le reste de la portée : CONCORDANT-NON-PROUVÉ (contenu hors portée non contrôlé par empreinte ; une modification non détectée n'est pas exclue).
- Fiabilité : PARTIEL (portée partielle)
Clôture : CLÔTURÉE 2026-10-18 23:17

---

## Session 2026-10-18 22:14 — Claude Code — reprise, rectifications du bloc 21:46, analyse en lecture seule de la migration corrective 009c
Clôture : CLÔTURÉE le 2026-10-18 à 22:36 (réconciliation en F)

### A. Ouverture — relevé initial (2026-10-18 22:14:23, avant toute modification de cette session)
- `CLAUDE.md` et ce journal lus avant toute autre action ; dernier bloc (21:46) : CLÔTURÉE [FAIT-VÉRIFIÉ]
- Branche `main`, HEAD `a99d4c2`, avance 0 / retard 1 sur `origin/main` (référence locale, aucun fetch) ; indexé : rien ; stash : 0 [FAIT-VÉRIFIÉ]
- Suivis modifiés : 7 (`docs/README.md`, `conventions-techniques-v6.md`, `invariants.md`, `modèle-données-sqlite-v6-v3.14.md`, `cdc-errata-v6.md`, `test_009a_…py`, `test_009b_couverture_situations.py`) ; `git diff --stat` : 7 fichiers, +51 / −20 [FAIT-VÉRIFIÉ]
- Non suivis : 17 entrées (les 15 du bloc 21:46 + `CLAUDE.md` + `docs/suivi/`) [FAIT-VÉRIFIÉ]
- Ignorés : `dist/` (10:27:08) et `src-tauri/tests/metier/__pycache__/` (13:38:02) inchangés ; `.claude/settings.local.json` : **706 octets, modifié le 22:04:13, SHA-256 `5c281172afc1733bef44bda884cb2fd7dcf3b43e0f96a51ea616aa7f4e833840`**, contre 250 octets, 21:39:05, `095cb50d…` à la clôture du bloc 21:46 ; modifié depuis le dernier relevé sans action volontaire de cette session ; origine exacte [NON VÉRIFIÉ]
- Écart avec l'état final du bloc 21:46 : mêmes noms et mêmes compteurs Git. Contenus modifiés depuis sa clôture, sur instruction de Rémy : `CLAUDE.md` (ligne 44, retrait du récit sur `.claude/settings.local.json`) et ce journal (règle 2, verdict de F) ; `CLAUDE.md` n'a pas d'empreinte en F du bloc 21:46 (créé avant ; première empreinte ci-dessous).
- Empreintes SHA-256 (octets bruts) :
  - `CLAUDE.md` : `e9529bd05baeec6930625e70731d60a18bfc7b6002780f0ec0d0e383ffddfff8`
  - ce journal (information, exclu des comparaisons) : `b3fd4db8b013835070f896b10e1f41a8ef5109b5fd6bb65cb6c42b82a2f52ef9`
  - `docs/README.md` : `54d5e5968218cef8597c916f6c89c0cc7ae29d77f4ac3cfc3b29c7b4d83f57d4` (= clôture du bloc 21:46)
  - `docs/conception/conventions-techniques-v6.md` : `2e3fc5e2db9d4003da66ace5b78fedc059b591bbca25374672a35083e73b7595` (= clôture du bloc 21:46)
  - migrations `006` `b4dad894…56baa`, `009a` `b53cd6df…c571`, `009b` `8bfdbde0…9255` : identiques à A du bloc 21:46
  - `009c_bc_annulation_acompte_encaissement.sql` : `662cc2ef7f53add4ffe4de22be0503b017dfbc28d704a9128f6796fc7f53585b`
  - `test_009a_bc_annulation_interdite_si_facture.py` : `5e10e723e2f54955a7c6968a4606d86848896a72a88e1d07f27256ad424a176d`
  - `test_009b_couverture_situations.py` : `90152ade4f613ba43d9eb20b1a353ca525594f07f16cc14177e6174c9fb0c994`
  - `test_009c_bc_annulation_acompte_encaissement.py` : `78ffec0fb51ba11856e5826b62b6cfcfd9b68457c91ab60cbf7dbf9ea7ac414f`
  - empreintes Git (blobs) de `invariants.md` `acb7bd0`, `cdc-errata-v6.md` `3065de1`, `modèle-données-sqlite-v6-v3.14.md` `9024c82` : identiques à celles notées en F du bloc 21:46
- Portée du relevé : suivis ☑ (statut, `diff --stat`) · non suivis ☑ (par nom) · ignorés ☑ (présence, date, empreinte de `.claude/settings.local.json`) · contenu par empreinte ☑ (fichiers listés ci-dessus : ceux qui seront modifiés, les migrations critiques, et les fichiers lus pour l'analyse de 009c). **Non contrôlé :** contenu des autres entrées non suivies (`src/`, `public/`, `reprise-autonome-*/`, fichiers de configuration), `node_modules/`, `.git/index`.

### B. Registre des actions
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Ouverture de ce bloc dans le journal | `docs/suivi/journal-continuite.md` | insérer ce bloc au-dessus du bloc 21:46 sans modifier celui-ci | effectuée | [FAIT-VÉRIFIÉ] |
| 2 | Mise à jour de la seule ligne « Statut de ce fichier » de `CLAUDE.md` (validation du contenu par Rémy) | `CLAUDE.md` | remplacer uniquement cette ligne | ligne 6 remplacée (diff contre la sauvegarde : 1 ligne) ; fins de ligne LF préservées (0 CRLF) ; SHA-256 après : `93f8fec6a60be961a0fad856c672fd82653efef1363ca2a870bdba889ef3b682` | [FAIT-VÉRIFIÉ] |
| 3 | Sauvegarde `CLAUDE.md.avant3` et script d'édition en ligne (Python, sans fichier) | hors dépôt (scratchpad de l'outil) | conserver l'état avant l'étape 2 | créée ; identique à `CLAUDE.md` avant modification | [FAIT-VÉRIFIÉ] |
| 4 | Mise à jour de ce bloc (B, C, D, puis E, F et clôture en fin de session) | ce journal | consigner au fil de la session | effectuée ; le bloc du 21:46 n'a pas été modifié (comparaison de texte : identique) | [FAIT-VÉRIFIÉ] |
Aucune autre écriture : l'analyse de la migration corrective 009c est restée en lecture seule (aucune migration, aucun test, aucun document de référence modifié) [FAIT-VÉRIFIÉ par relevé final].

### C. Commandes et tests réellement exécutés
| Commande | Répertoire | Résultat | Portée / limites | Statut |
|---|---|---|---|---|
| Lecture de `CLAUDE.md` et du journal | racine | lus en entier (journal à partir de la ligne 60) | lecture seule | [FAIT-VÉRIFIÉ] |
| Relevé initial (`git branch`, `rev-parse`, `rev-list`, `status`, `diff --stat`, `stash list`, `sha256sum`, `ls -l`, `git hash-object`) | racine | voir A | lecture seule | [FAIT-VÉRIFIÉ] |
| Lectures (outil de lecture, `grep`, `sed`) : `CLAUDE.md`, ce journal, conventions §5 et §7.1, migrations 009a, 009b (tr_23), 009c, tests 009a, 009b_couverture, 009b_acompte, 009c, modèle V3.14 (§15, §17.1, T-54), `invariants.md`, `fichiers-a-relire/` (recherches) | racine | lus ; voir réponse à Rémy | lecture seule | [FAIT-VÉRIFIÉ] |
| Script Python en lecture seule : comparaison des SHA-256 codés en dur dans `test_009c` (006, 009a, 009b) et `test_009b_couverture` (001 à 009, 12 fichiers) avec les blobs `git show HEAD:…` | racine | 15 comparaisons sur 14 fichiers distincts, toutes concordantes | vérification statique ; n'exécute aucun test | [FAIT-VÉRIFIÉ] |
| Reprise après coupure de connexion de l'utilisateur : `git status --short \| wc -l`, `git diff --stat`, début du SHA-256 de `CLAUDE.md` (2026-10-18 22:33:56) | racine | 24 entrées, 7 fichiers +51/−20, `CLAUDE.md` inchangé depuis B2 | contrôle limité (noms, compteurs, un fichier) | [FAIT-VÉRIFIÉ] |
Aucun test lancé, aucune campagne de mutation. Aucun fetch, pull, commit, push, changement de branche, add, stash, restore, reset, clean [FAIT-VÉRIFIÉ par relevé final].

### D. Rectifications concernant le bloc clôturé du 2026-10-18 21:46, décisions, points non résolus
Le bloc 21:46 n'est pas modifié davantage (aucune autre modification de ce bloc n'est prévue).
- **Verdict de F corrigé** sur instruction de Rémy : `CONCORDANT-PROUVÉ sur la portée indiquée` remplacé par `CONCORDANT-NON-PROUVÉ` (limites de portée et fiabilité PARTIEL conservées). Modification d'un bloc clôturé effectuée avant la clarification de la règle 2 du préambule.
- **Règle 2 du préambule** clarifiée sur instruction de Rémy : aucun bloc clôturé n'est modifié ; toute correction ultérieure est ajoutée dans un nouveau bloc daté, avec référence au bloc concerné et motif.
- **B4 et B5 du bloc 21:46 sont erronées** quant aux fins de ligne. Réalité constatée par comptage d'octets : `CLAUDE.md` est en **LF** (75 lignes, 0 CRLF) ; le journal est en **CRLF** (125 lignes) **après conversion** par l'outil (il avait été écrit en LF puis converti). Motif de l'erreur : la commande de contrôle utilisée (`grep -c $''`) comptait toutes les lignes quel que soit le fichier ; elle était invalide. Les mentions « CRLF constatées après écriture » de B4 et B5 doivent être lues comme erronées. Précision : l'affirmation de A du bloc 21:46 sur `conventions-techniques-v6.md` et `docs/README.md` (CRLF) est restée exacte ; elle a été reconfirmée par comptage d'octets (282/282 et 50/50, aucun mélange).
- **Analyse de la migration corrective 009c (lecture seule)** : effectuée ; constats, incertitudes et décisions sont dans la réponse faite à Rémy le 2026-10-18. **009c n'est pas déclarée validée.** Constats vérifiés par lecture ou comparaison statique : (a) les empreintes codées en dur dans `test_009c` et `test_009b_couverture` sont égales aux blobs de HEAD `a99d4c2` ; (b) l'arbitrage « option A » et le rang 15 n'apparaissent que dans des fichiers locaux ou non suivis (009c, ses tests, modèle V3.14) : aucune source primaire dans le dépôt ; (c) la ligne T-54 du modèle affirme « campagne de mutation (20 mutants) » : aucun rapport ni outil correspondant trouvé dans le dépôt [NON VÉRIFIÉ] ; (d) le texte de conventions §7.1 est ambigu pour une corrective ; (e) le filtre ajouté à `test_009a` est relayé par les groupes A et H de `test_009c` pour les migrations suivantes, avec une portée de contrôle dynamique limitée au cas de l'acompte non neutralisé.
- Session interrompue puis reprise après une coupure de connexion de l'utilisateur ; aucun changement détecté pendant la coupure sur les indicateurs contrôlés (voir C).

### E. Clôture — relevé final (2026-10-18 22:34:59)
- Branche `main`, HEAD `a99d4c2`, avance 0 / retard 1 sur `origin/main` (référence locale) ; indexé : rien ; stash : 0 [FAIT-VÉRIFIÉ]
- Suivis modifiés : 7 ; `git diff --stat` : 7 fichiers, +51 / −20 (identique à A) ; non suivis : 17 entrées (identique à A) [FAIT-VÉRIFIÉ]
- Ignorés : `dist/` et `__pycache__/` inchangés (dates identiques à A) ; `.claude/settings.local.json` : **915 octets, modifié le 22:19:06, SHA-256 `ac8d3ea6c18a5eea6c18d2324ff346890e779bc00dc3fa6161f955d94652ab83`**, contre 706 octets, 22:04:13, `5c281172…` en A [FAIT-VÉRIFIÉ]
- Empreintes finales : `CLAUDE.md` `93f8fec6a60be961a0fad856c672fd82653efef1363ca2a870bdba889ef3b682` (modifié par B2) ; `docs/README.md`, `conventions-techniques-v6.md`, migrations 006, 009a, 009b, 009c, tests 009a, 009b_couverture, 009c : **identiques à A** ; blobs Git de `invariants.md`, `cdc-errata-v6.md`, `modèle-données-sqlite-v6-v3.14.md` : identiques à A [FAIT-VÉRIFIÉ]
- Portée du relevé final : identique à A.

### F. Réconciliation
- Écarts initial → final expliqués par B : `CLAUDE.md` (ligne 6, B2) ; ce journal (B4, exclu des comparaisons). Aucun autre fichier à empreinte n'a changé ; aucune migration, aucun test métier, aucun document de référence n'a été modifié [FAIT-VÉRIFIÉ sur la portée].
- **Écart non expliqué par B : `.claude/settings.local.json`** (fichier ignoré ; 706 → 915 octets pendant la session). Aucune écriture volontaire de cette session sur ce fichier ; le fichier a déjà évolué pendant les sessions précédentes ; origine exacte [NON VÉRIFIÉ] (stockage des permissions de l'outil, hypothèse non démontrée).
- Registre B tenu sur toute la session : oui. Coupure de connexion de l'utilisateur : aucune action pendant la coupure ; contrôle à la reprise en C.
- Portée du verdict : noms de fichiers suivis et non suivis, compteurs de `diff --stat`, empreintes des fichiers listés en A, empreinte de `.claude/settings.local.json`. **Non contrôlé :** contenu des autres entrées non suivies (`src/`, `public/`, `reprise-autonome-*/`, fichiers de configuration), `node_modules/`, `.git/index`, contenu des ignorés autres que `.claude/settings.local.json`.
- **Verdict : DISCORDANT, limité à `.claude/settings.local.json`** (écart unique non expliqué par B). Pour le reste de la portée : CONCORDANT-NON-PROUVÉ (contenu hors portée non contrôlé par empreinte ; modification non détectée non exclue).
- Fiabilité : PARTIEL (portée partielle)
Clôture : CLÔTURÉE 2026-10-18 22:36

---

## Session 2026-10-18 21:46 — Claude Code — création de CLAUDE.md, de ce journal et des amendements documentaires
Clôture : CLÔTURÉE le 2026-10-18 à 21:58 (réconciliation en F)

### A. Ouverture — relevé initial (effectué le 2026-10-18 à 21:46:31, avant toute modification de cette tâche)
- Branche `main`, HEAD `a99d4c2`, avance 0 / retard 1 sur `origin/main` (référence locale, non rafraîchie : aucun fetch) [FAIT-VÉRIFIÉ]
- Suivis modifiés : 6 (`conventions-techniques-v6.md`, `invariants.md`, `modèle-données-sqlite-v6-v3.14.md`, `cdc-errata-v6.md`, `test_009a_bc_annulation_interdite_si_facture.py`, `test_009b_couverture_situations.py`) ; `git diff --stat` : 6 fichiers, +39 / −19 [FAIT-VÉRIFIÉ]
- Non suivis : 15 entrées (`.gitignore`, `README.md`, `eslint.config.js`, `index.html`, `package-lock.json`, `package.json`, `public/`, `reprise-autonome-v3.14-tranche-010/`, migration `009c_…sql`, test `test_009c_…py`, `src/`, `tsconfig.app.json`, `tsconfig.json`, `tsconfig.node.json`, `vite.config.ts`) [FAIT-VÉRIFIÉ]
- Indexé : rien ; stash : 0 [FAIT-VÉRIFIÉ]
- Ignorés notables : `.claude/settings.local.json` (250 octets, modifié le 2026-10-18 21:39:05) ; `dist/` (10:27:08) ; `src-tauri/tests/metier/__pycache__/` (13:38:02) ; `node_modules/` non examiné [FAIT-VÉRIFIÉ pour présence et date]
- Absents : `CLAUDE.md`, `docs/suivi/` [FAIT-VÉRIFIÉ]
- Fins de ligne : `conventions-techniques-v6.md` et `docs/README.md` entièrement en CRLF (`core.autocrlf=true`) [FAIT-VÉRIFIÉ]
- Empreintes SHA-256 du fichier de travail (octets bruts) :
  - `docs/conception/conventions-techniques-v6.md` : `578404a448a380a5e6f13f3e813d16e415e988f165a5b09d97bf592e812ba47e`
  - `docs/README.md` : `fdb2a5343eebea86649c8b577758c31bc8f6457c82e04e62b5d1649f6ad7815e`
  - `src-tauri/migrations/metier/006_facturation.sql` : `b4dad89414ca056281d44b16f8a7866efebe90f5be482a486a85a15bf0a56baa`
  - `src-tauri/migrations/metier/009a_bc_annulation_interdite_si_facture.sql` : `b53cd6df2880b5eb3d4e345b75c26a7471e28cac80e0e98b82135392d308c571`
  - `src-tauri/migrations/metier/009b_acompte_garanties_manuelles.sql` : `8bfdbde0156e03c92908e7c1e86f500b6580de6046ea58fe64c1fe6d803c9255`
  - `.claude/settings.local.json` : `095cb50deb428ec1dcd9f0ab199c41ac2b9e57f7f4690f32a7f92aaeaf587fec`
- Portée du relevé : suivis ☑ (statut, `diff --stat`) · non suivis ☑ (par nom seulement) · ignorés ☑ (présence et date) · contenu par empreinte ☑ (6 fichiers ci-dessus uniquement). **Non contrôlé :** contenu des 15 entrées non suivies, contenu des 4 autres fichiers suivis modifiés, contenu des fichiers ignorés, `node_modules/`, état de `.git/index` [NON VÉRIFIÉ].
- Écart avec l'état final de la session précédente : état précédent absent. Ce bloc est le premier du journal ; la phase de cadrage qui l'a précédé dans la même conversation n'a pas donné lieu à un relevé initial complet et n'est pas reprise ici comme tel (voir D).

### B. Registre des actions
| # | Action | Cible | Avant (intention) | Après (résultat) | Statut |
|---|---|---|---|---|---|
| 1 | Script d'édition `amend_docs.py` et sauvegardes `conventions-techniques-v6.md.avant`, `README.md.avant` | hors dépôt (scratchpad de l'outil) | créer script et copies de sauvegarde | créés ; copies identiques aux fichiers avant édition | [FAIT-VÉRIFIÉ] |
| 2 | Ajout du passage « Dossier de suivi de session » à la fin de la section 3 de `docs/conception/conventions-techniques-v6.md` | dépôt (suivi, déjà modifié localement) | insérer 7 lignes avant « ## 4. » sans toucher au reste | +7 lignes (diff contre la sauvegarde) ; modification locale V-2 préservée ; CRLF préservé (282/282) ; SHA-256 après : `2e3fc5e2db9d4003da66ace5b78fedc059b591bbca25374672a35083e73b7595` | [FAIT-VÉRIFIÉ] |
| 3 | Trois ajouts à `docs/README.md` (liste Organisation, section « Suivi (hors référence) », phrase de périmètre) | dépôt (suivi, propre au départ) | insérer 4 lignes et reformuler 1 phrase | +4 lignes, 1 ligne modifiée (diff contre la sauvegarde) ; CRLF préservé (50/50) ; SHA-256 après : `54d5e5968218cef8597c916f6c89c0cc7ae29d77f4ac3cfc3b29c7b4d83f57d4` | [FAIT-VÉRIFIÉ] |
| 4 | Création de `CLAUDE.md` (racine) | dépôt (non suivi) | créer à partir de la proposition validée et des corrections convenues | créé (75 lignes, fins de ligne CRLF constatées après écriture) ; relecture finale de Rémy en attente | [FAIT-VÉRIFIÉ] pour la création ; contenu [NON VÉRIFIÉ] tant que non relu |
| 5 | Création de `docs/suivi/` et de ce fichier | dépôt (non suivi) | créer avec le modèle validé et ce premier bloc | créés (fins de ligne CRLF constatées après écriture) | [FAIT-VÉRIFIÉ] |
| 6 | Mise à jour de ce fichier : correction de la mention des fins de ligne (B4, B5), relevé final (E), réconciliation (F), clôture | dépôt (non suivi) | compléter le bloc en fin de tâche | effectuée | [FAIT-VÉRIFIÉ] |

### C. Commandes et tests réellement exécutés
| Commande | Répertoire | Résultat | Portée / limites | Statut |
|---|---|---|---|---|
| Relevé initial (`git branch`, `rev-parse`, `rev-list`, `status`, `diff --stat`, `stash list`, `sha256sum`, `ls -l`) | racine du dépôt | voir A | lecture seule | [FAIT-VÉRIFIÉ] |
| `python -I …/amend_docs.py` | racine du dépôt | sortie « OK » avec les deux SHA-256 de B2 et B3 ; script protégé par une garde (arrêt si l'empreinte d'un fichier a changé depuis le relevé) | script d'édition, ce n'est pas un test | [FAIT-VÉRIFIÉ] |
| `diff --strip-trailing-cr` (sauvegarde ↔ fichier) et comptage des fins de ligne | racine du dépôt | différences conformes à B2 et B3 | lecture seule | [FAIT-VÉRIFIÉ] |
Aucun test lancé, aucune campagne de mutation. Aucun fetch, pull, commit, push, changement de branche, add, stash, restore, reset, clean [FAIT-VÉRIFIÉ].

### D. Décisions rapportées, points non résolus, prochaine étape
- Décision rapportée : accord du propriétaire (message du 2026-10-18) pour procéder aux créations et modifications documentaires validées ci-dessus ; source primaire hors dépôt. Statut documentaire : amendements conventions §3 et README = [LOCAL].
- Contexte antérieur à ce relevé (**pas un relevé**, [NON VÉRIFIÉ] en tant qu'état du dépôt) : `.claude/settings.local.json` est apparu puis a été modifié en cours de conversation (17:17, puis 21:39) sans action volontaire de l'outil ; origine exacte non établie.
- Points non résolus : hiérarchie documentaire (conflit ouvert, CLAUDE.md §1) · statut historique du registre des invariants · rang et source de 009c · cellule T-53 du modèle V3.14 · application de conventions §7.1 à la corrective 009c · vérifications de mutation des tests 009a / 009b modifiés (logique) avant intégration.
- Prochaine étape [PRÉVU] : relecture finale de Rémy de `CLAUDE.md`, du journal et des passages ajoutés ; aucun commit tant que Rémy ne le demande.
- À relire en priorité : verdict de F (choix de la formulation) ; texte de conventions §3 (apostrophes droites, alors que la section voisine utilise des apostrophes typographiques) ; `CLAUDE.md` §3 (ajout « changement de branche » et « modification inattendue : s'arrêter ») et ligne « Statut de ce fichier ».

### E. Clôture — relevé final (2026-10-18 21:54:26)
- Branche `main`, HEAD `a99d4c2`, avance 0 / retard 1 sur `origin/main` (référence locale) ; indexé : rien ; stash : 0 [FAIT-VÉRIFIÉ]
- Suivis modifiés : 7 (les 6 du relevé A + `docs/README.md`) ; `git diff --stat` : 7 fichiers, +51 / −20 [FAIT-VÉRIFIÉ]
- Non suivis : 17 entrées (les 15 du relevé A + `CLAUDE.md` + `docs/suivi/`) [FAIT-VÉRIFIÉ]
- Ignorés : `.claude/settings.local.json` inchangé depuis A (250 octets, 21:39:05, même SHA-256) ; `dist/` et `__pycache__/` présents (dates non revérifiées) [FAIT-VÉRIFIÉ pour `.claude/`]
- Empreintes finales : `conventions-techniques-v6.md` `2e3fc5e2db9d4003da66ace5b78fedc059b591bbca25374672a35083e73b7595` ; `docs/README.md` `54d5e5968218cef8597c916f6c89c0cc7ae29d77f4ac3cfc3b29c7b4d83f57d4` ; migrations 006, 009a, 009b : identiques à A [FAIT-VÉRIFIÉ]
- Portée du relevé final : identique à A.

### F. Réconciliation
- Écarts initial → final : expliqués par B. Modifications de contenu : conventions (+7 lignes, B2) et README (+4 lignes, 1 phrase modifiée, B3) ; nouveaux non suivis : `CLAUDE.md` (B4), `docs/suivi/` (B5). Compteurs `diff --stat` : 6 fichiers +39/−19 → 7 fichiers +51/−20, soit +12/−1 = +7 (conventions) +5/−1 (README) [FAIT-VÉRIFIÉ].
- Indice indirect, hors relevé A : les empreintes Git des 5 autres fichiers suivis modifiés sont identiques à celles observées plus tôt dans la conversation (non consignées en A) [FAIT-VÉRIFIÉ comme comparaison, non comme preuve d'état initial].
- Registre B tenu sur toute la tâche : oui.
- Portée du verdict : noms de fichiers suivis et non suivis, compteurs de `diff --stat`, empreintes des fichiers désignés en A (conventions, README, 006, 009a, 009b, `.claude/settings.local.json`). **Non contrôlé :** contenu des 15 entrées non suivies initiales, contenu par empreinte des 5 autres fichiers suivis modifiés (en A), fichiers ignorés hors `.claude/`, `node_modules/`, `.git/index`. Le journal lui-même est exclu des comparaisons.
- **Verdict : CONCORDANT-NON-PROUVÉ.** Les écarts constatés sont tous expliqués par B, mais le contenu des fichiers hors de la portée indiquée n'est pas contrôlé par empreinte : une modification non détectée n'est pas exclue.
- Fiabilité : PARTIEL (portée partielle)
Clôture : CLÔTURÉE 2026-10-18 21:58
