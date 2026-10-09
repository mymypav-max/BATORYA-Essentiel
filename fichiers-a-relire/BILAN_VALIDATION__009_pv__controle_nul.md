# BILAN DE VALIDATION — 009 PV, contrôle de l'octet NUL (D1–D3)

Date : 2026-10-10. Dépôt de travail `g007/` (HEAD `a9fd50f`, branche `main` non en avance sur `origin/main`). SQLite 3.45.1, Python 3.11.15.
**Rien n'est commité ni poussé. Aucune migration 001–008 n'est modifiée. Z-8 et INV-131 sont inchangés. La tranche 010 n'est pas commencée.**

## 1. Ce qui a été modifié (autorisations 1 à 3)

| Fichier | sha256 avant | sha256 après |
|---|---|---|
| `src-tauri/migrations/metier/009_pv.sql` | `d32b20a4dc6130246cef1ec3fdef438bc568015d66ed9fef1d0ba8d56b804381` | `764a2d302969f471bad2e6770f57454eff7659ebd886e5c6aa6be14509d84cb3` (175 lignes) |
| `src-tauri/tests/metier/test_009_pv.py` | `d236c013cf60487c34875eb2e34d5dd7e3ef2a48dcfdf17d426f48222d2d6781` | `4d56721107285773f12920224c2f83ded43f7aeb74b96a8909ef57beaeb59f04` (268 tests) |
| `fichiers-a-relire/RAPPORT_MUTATION__009_pv.md` | `1cea167d69499734ad5ab704d404f5e46147b603c3cd485e3e6bf104b4f81913` | voir le fichier (193 lignes, réécrit après la campagne complète) |

Les deux premiers fichiers ont été obtenus en **appliquant `patch` aux diffs validés** (`sql_revise.diff`, `tests_revises.diff`) ; leurs empreintes sont **identiques** à celles des copies jetables. Contrôle : `diff -rq` entre la copie intacte de `src-tauri/` et le dépôt ne signale que ces deux fichiers ; `git status` ne montre aucun fichier suivi modifié (uniquement des fichiers non suivis : 008, 009 et `fichiers-a-relire/`) ; aucun `__pycache__`.
Diffs finaux exacts : `DIFF_FINAL__009_pv.sql.diff` (sha256 `37a4e7f73c197e82d6b98f517da135f556c232084c9854d9095d6c1b6c43dc78`) et `DIFF_FINAL__test_009_pv.py.diff` (sha256 `4edc51e9c296acb9d2a7863bc77c64cecaf19deec4272b607348826b59e9c7cb`), identiques (hors en-têtes) aux diffs que tu as validés. Diff SQL complet :

```diff
--- a/src-tauri/migrations/metier/009_pv.sql	2026-10-10 01:27:41.492051571 +0200
+++ b/src-tauri/migrations/metier/009_pv.sql	2026-10-10 01:27:41.496073694 +0200
@@ -80,12 +80,13 @@
     type                        TEXT    NOT NULL CHECK (type IN ('reception_sans_reserves', 'reception_avec_reserves', 'levee_reserves')),
     date_reception              TEXT    NOT NULL
                                 CHECK (date_reception GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_reception) IS date_reception),
-    -- BLOC-SNAP
-    client_snapshot             TEXT    NOT NULL CHECK (json_valid(client_snapshot)),
+    -- BLOC-SNAP : json_valid lit le TEXT comme une chaîne C (arrêt au premier octet NUL, queue ignorée) ; un octet NUL brut est donc refusé par
+    -- instr(CAST(x AS BLOB), x'00') ; l'échappement JSON \u0000 (six caractères, sans octet NUL) reste valide
+    client_snapshot             TEXT    NOT NULL CHECK (json_valid(client_snapshot) AND instr(CAST(client_snapshot AS BLOB), x'00') = 0),
     client_snapshot_version     INTEGER NOT NULL,
-    entreprise_snapshot         TEXT    NOT NULL CHECK (json_valid(entreprise_snapshot)),
+    entreprise_snapshot         TEXT    NOT NULL CHECK (json_valid(entreprise_snapshot) AND instr(CAST(entreprise_snapshot AS BLOB), x'00') = 0),
     entreprise_snapshot_version INTEGER NOT NULL,
-    chantier_snapshot           TEXT    NOT NULL CHECK (json_valid(chantier_snapshot)),
+    chantier_snapshot           TEXT    NOT NULL CHECK (json_valid(chantier_snapshot) AND instr(CAST(chantier_snapshot AS BLOB), x'00') = 0),
     chantier_snapshot_version   INTEGER NOT NULL,
     observations                TEXT,
     reserves                    TEXT,
@@ -95,7 +96,7 @@
     -- BLOC-IMP
     origine                     TEXT    NOT NULL DEFAULT 'v6' CHECK (origine IN ('v6', 'import')),
     legacy_id                   TEXT,
-    legacy_data                 TEXT    CHECK (legacy_data IS NULL OR json_valid(legacy_data)),
+    legacy_data                 TEXT    CHECK (legacy_data IS NULL OR (json_valid(legacy_data) AND instr(CAST(legacy_data AS BLOB), x'00') = 0)),
 
     UNIQUE (origine_pv_id, suffixe),
     CHECK (numero <> ''),
@@ -107,12 +108,16 @@
     CHECK ((reserves IS NOT NULL) = (type = 'reception_avec_reserves')),
     CHECK (origine <> 'v6' OR (legacy_id IS NULL AND legacy_data IS NULL)),
     -- numéro d'un PV INITIAL V6 : PVR + 5 chiffres + année de date_reception (INV-20) ;
-    -- import : numéro libre non vide ; levée : aucun contrôle de format ajouté (PR-3), son numéro est imposé par G4
+    -- import : numéro libre non vide ; levée : aucun contrôle de format ajouté (PR-3), son numéro est imposé par G4.
+    -- GLOB, substr et length() de TEXT s'arrêtent au premier octet NUL : la longueur est donc contrôlée en octets
+    -- (CAST ... AS BLOB) pour qu'aucune queue ne suive le format (numéro V6 : 12 octets ; created_at : 24 octets).
     CHECK (origine <> 'v6' OR type = 'levee_reserves'
            OR (numero GLOB 'PVR-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'
-               AND substr(numero, 11, 2) = substr(date_reception, 3, 2))),
+               AND substr(numero, 11, 2) = substr(date_reception, 3, 2)
+               AND length(CAST(numero AS BLOB)) = 12)),
     CHECK (created_at GLOB
-        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
+        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'
+        AND length(CAST(created_at AS BLOB)) = 24)
 ) STRICT;
 
 
```

## 2. Résultats (sorties brutes dans `sorties_brutes_009_nul/`)

| Contrôle | Résultat | Attendu (annoncé sur copies jetables) |
|---|---|---|
| Suite métier 001→009 (`unittest discover`, ≈ 102 s) | **1 866 tests, OK** | 1 866 ✔ |
| Suite machine | **13 tests, OK** | 13 ✔ |
| `test_009_pv` seul | 268 tests, **940 sous-tests**, OK | 268 ✔ (sous-tests : nouveau chiffre ; l'ancien, 669, est retrouvé sur l'ancien fichier) |
| Intégrité sur base construite par la chaîne 001→009 et alimentée (6 PV V6 dont 3 levées + 1 PV importé à `legacy_data` contenant `\u0000`) | `integrity_check` = ok, `quick_check` = ok, `foreign_key_check` = vide, en mémoire **et** sur fichier ; `user_version` = 12 ; table `pv` STRICT ; 3 triggers 009 | — |
| Campagne complète de mutation (`mut009b.py`) | **797 mutants : 770 tués, 3 invalides, 0 délai dépassé, 24 survivants** | 19 survivants annoncés → **divergence, voir §3** |
| Passe sans groupe A | 758 / 3 / 36 survivants (= 24 + les mêmes 12 mutants structurels qu'avant) | — |
| Passe sans groupe A ni test témoin de texte | 744 / 3 / 50 survivants (= 36 + 14 tués seulement par le texte du témoin) | « 6 équivalents probables » annoncés → **14, voir §3** |
| Preuves d'équivalence liées au SQL du dépôt (`preuves_equivalence_009.py`, 203 s) | **52 contrôles OK, 0 échec, TOUT EST OK** : 24 survivants S01–S24, 14 mutants K01–K14, 11 témoins non équivalents qui divergent | 29 contrôles annoncés (19 + 7 témoins…) → étendu |
| Rapprochement campagne ↔ registre (`rapprochement_survivants_registre.py`) | **BIJECTION OK** : 24 survivants ↔ S01–S24 (SQL muté identique octet pour octet) ; 14 ↔ K01–K14. Épreuve négative (survivant retiré, intrus ajouté) : ECHEC | nouveau |

### Justification de chaque équivalence (détail et chiffres : rapport §4 et §4 quater)
- **E1** S02–S10 (`GLOB` de date affaibli) : `date(x) IS x` impose que `x` soit une image de `date()` ; 5 373 485 jours juliens évalués, 0 divergence. Relative au conjoncte `date(x) IS x`.
- **E2** S01 (`substr(numero,11,3)`) : `length(CAST(numero AS BLOB)) = 12` ⇒ pas de 13ᵉ octet ; 240 000 couples, 0 divergence.
- **E3** S11–S12 (chiffres de `yy` → `?`) : l'égalité avec l'année de `date_reception` impose des chiffres ; 6 760 000 couples par variante.
- **E4** S13 (`%02i`) : synonyme de `%02d` ; 101 001 entiers + 300 levées successives.
- **E5** S14–S16 (jointure `pv o, pv x`) : conserve l'existence de `o` ; 156 états × 8 316 tentatives par les triggers réels.
- **E6** S17 (`IS`→`=`, G2) : `o.bc_id` NOT NULL, même message ; mêmes 156 états.
- **E7** S18–S19 (`FOR EACH ROW`) : comportement par défaut ; 1 047 tentatives d'UPDATE/DELETE/REPLACE.
- **E8 (nouveau)** S20–S21 (`legacy_data IS NULL` → `0`) : `NULL` satisfait un CHECK (original = 1, mutant = NULL) ; 20 valeurs, 0 divergence.
- **E9 (nouveau)** S22–S24 (`*` en queue/en tête des `GLOB` du numéro et de `created_at`) : redondants avec D1/D2 (le `GLOB` exige déjà ≥ N octets, le CHECK impose = N) ; 43 824 et 18 594 évaluations, NUL et multi-octets compris.
- **E10 / E9** K01–K14 (tués seulement par le texte du témoin) : `<= N` ≡ `= N` ; `instr(TEXT, x'00')` ≡ `instr(CAST(TEXT AS BLOB), x'00')` **sur SQLite 3.45.1 seulement** (le `CAST` est conservé pour ne pas dépendre de ce comportement).

## 3. Divergences avec ce que j'avais annoncé sur les copies jetables

1. **Survivants : 24 et non 19.** J'avais écrit que « les 19 survivants restent équivalents » ; c'était incomplet. La correction en crée 5 nouveaux (tous qualifiés équivalents) : S22–S24 (redondance des `GLOB` avec D1/D2, attendue) et **S20–S21, qui viennent de la modification validée du test** : `C_LEGACY_JSON` passe de `legacy_data IS NULL OR json_valid(legacy_data)` à `json_valid(legacy_data)` et ne tue plus par le texte du message de contrainte le mutant `legacy_data IS NULL`→`0` (équivalent). *Option d'une ligne, non appliquée* : `C_LEGACY_JSON = "legacy_data IS NULL OR (json_valid(legacy_data)"` — essayée sur copie jetable : 268 tests OK, S20 et S21 tués (par le texte du message, pas par le comportement).
2. **Mutants tués seulement par le témoin de texte : 14 et non 6.** Les 6 annoncés (`<= 12`, `<= 24`, 4 × `instr` sans `CAST`) + 8 que l'aperçu ne générait pas (`CAST … AS TEXT` et `CAST` supprimé sur les 4 champs JSON).
3. **Défaut de l'outil de campagne, corrigé.** Premier essai : 803 mutants, 27 invalides au lieu de 3. Les opérateurs `cast_*` hérités de 006/007 supposaient `CAST(… AS INTEGER)` et fabriquaient du SQL invalide sur `CAST(x AS BLOB)`. Opérateur corrigé, campagne relancée en entier (résultat §2) ; la sortie du premier essai est conservée.
4. **Formulation imprécise dans la synthèse précédente** : « 14 nouveaux tests » ; en réalité 14 définitions ajoutées dont 1 remplace le test-constat (net +13, 255 → 268). Le chiffre « 7 tests échouent sur le SQL actuel » est celui mesuré alors ; non rejoué ici.
5. **Script de preuve étendu** (52 contrôles au lieu de 29 ; 11 témoins au lieu de 7 ; 24 + 14 entrées au registre) et **un défaut de chemin par défaut corrigé** (`parents[3]` → `parents[4]` pour l'emplacement proposé ; vérifié sur une copie jetable). Le rapprochement par texte exact est nouveau.
6. Les documents `PROPOSITION_DIFF__…`, `SYNTHESE__…` et `COMPLEMENT_*` rédigés avant ton autorisation portent encore « non appliqué » : **ce bilan et le rapport de mutation mis à jour les remplacent** ; je ne les ai pas réécrits.
7. Aucune autre divergence constatée : les suites (1 866 / 13 / 268), les empreintes et les diffs sont ceux annoncés.

## 4. Script de preuve des survivants : emplacement et exécution proposés (autorisation : « propose son emplacement et son mode d'exécution »)

**Livré** : `fichiers-a-relire/outils_mutation_009/preuves_equivalence_009.py` (sha256 `72d2e99af9ad8e818585442488d420649a3be83629e69c8cbcac8f17b90ec6a7`), avec `rapprochement_survivants_registre.py`. Il lit `009_pv.sql` dans le dépôt (substitutions textuelles à ancres uniques, CHECK extraits du DDL créé, triggers exécutés tels que créés) ; il **s'arrête** si le SQL ne correspond plus au registre. **Il ne remplace pas la campagne de mutation** : seule la campagne énumère les survivants ; le rapprochement relie les deux.
- **Emplacement proposé** : `src-tauri/tests/metier/outils/preuves_equivalence_009.py` et `…/rapprochement_survivants_registre.py` (hors du motif `test_*.py` et sans `__init__.py` : `unittest discover` ne les collecte pas — **vérifié sur copie jetable : 1 866 tests avant et après**). Le chemin par défaut du dépôt est dérivé de cet emplacement.
- **Exécution proposée** : manuelle ou en CI hors suite rapide (≈ 3,5 min), obligatoire dès que `009_pv.sql` change : `python3 -B src-tauri/tests/metier/outils/preuves_equivalence_009.py` (code de sortie 0 = TOUT EST OK). Après toute modification du SQL : relancer la campagne (`mut009b.py`), puis le rapprochement ; un survivant sans entrée de registre fait échouer le rapprochement.
- **Variantes** (à ton choix) : (B) test opt-in appelant le script via une variable d'environnement ; (D) versionner aussi l'outil de campagne `mut009b.py` + `genmut009b.py` + `classify009b.py` (seule option qui rend la complétude rejouable depuis le dépôt) ; (C) ne rien versionner et annexer sha256 + sorties au rapport (déjà fait dans le rapport §6).
**Rien de tout cela n'est dans `src-tauri/`** : les outils sont dans `fichiers-a-relire/outils_mutation_009/`.

## 5. Points qui restent à arbitrer

1. Valider le **diff final** (SQL + tests + rapport de mutation) avant tout commit ; je n'ai rien commité.
2. Option `C_LEGACY_JSON` plus stricte (une ligne) : l'appliquer (S20–S21 tués par le texte du message) ou garder le test validé tel quel (S20–S21 restent des équivalents qualifiés).
3. Les 14 kills « textuels » (§4 quater) : les accepter comme tels, ou ajouter un test comportemental pour ceux qui ne dépendent pas du moteur (`<= N` ne peut pas être distingué comportementalement ; les 12 mutants `instr`/`CAST` sont équivalents sur 3.45.1 par construction).
4. Placer ou non le script de preuve (et l'outil de campagne) dans le dépôt, et sous quelle forme (§4).
5. Mentions documentaires optionnelles D-1 à D-3 (`PROPOSITION_DOC__009_pv__formulations_controle_nul.md`) : aucune n'est nécessaire à la conformité.
6. **Version de SQLite embarquée par Tauri : non vérifiée.** D1–D3 n'emploient que `length`, `instr`, `CAST AS BLOB` ; E10 est relative à la version.
7. Les services Rust/TS filtrent-ils déjà les NUL ? écrivent-ils `created_at` explicitement ? (hors dépôt ; un `created_at` non conforme sera désormais refusé).
8. Plan de remédiation 001–008 (livrable d'analyse distinct, inchangé) : vagues, mode par trigger ou par reconstruction de table, bases existantes — à arbitrer avant toute migration corrective.
9. Rapport de mutation : il décrit désormais la campagne complète sur le SQL final ; l'ancienne version (692 mutants) n'est plus valable pour ce SQL.

## 6. Pièces livrées dans `fichiers-a-relire/`

`RAPPORT_MUTATION__009_pv.md` (mis à jour) · `BILAN_VALIDATION__009_pv__controle_nul.md` (ce fichier) · `DIFF_FINAL__009_pv.sql.diff` · `DIFF_FINAL__test_009_pv.py.diff` · `PROPOSITION_DOC__009_pv__formulations_controle_nul.md` · `outils_mutation_009/` (outils, non versionnés dans `src-tauri/`) · `sorties_brutes_009_nul/` (suites, campagnes, preuves, intégrité, rapprochement, survivants, tueurs, essai 1).
