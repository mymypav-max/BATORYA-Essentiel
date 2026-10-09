# PROPOSITION DE DIFF SQL — 009 : contrôle des octets NUL (révision 2)

**NON APPLIQUÉ.** Cette révision remplace la première version de ce fichier (variantes « D1 seule », « D2 seule » et option JSON séparée supprimées : les orientations de Rémy retiennent D1, D2 et D3 ensemble). `009_pv.sql` n'a pas été modifié.
Ne vaut pas autorisation de modifier les fichiers protégés : le diff final sera validé avant toute modification réelle.

| | sha256 | lignes |
|---|---|---:|
| `009_pv.sql` actuel (inchangé) | `d32b20a4dc6130246cef1ec3fdef438bc568015d66ed9fef1d0ba8d56b804381` | 170 |
| `009_pv.sql` après application du diff (copie jetable) | `764a2d302969f471bad2e6770f57454eff7659ebd886e5c6aa6be14509d84cb3` | 175 |

Le diff s'applique à la racine du dépôt : `patch -p1 < diff` (vérifié avec `--dry-run` puis application sur une copie ; le résultat est identique octet pour octet à la copie testée).

## 1. Contenu

| Réf. | Changement | Colonnes |
|---|---|---|
| **D1** | `AND length(CAST(numero AS BLOB)) = 12` dans le CHECK du numéro du **PV initial V6** | `pv.numero` |
| **D2** | `AND length(CAST(created_at AS BLOB)) = 24` à côté du `GLOB` prescrit (type TS) | `pv.created_at` |
| **D3** | `AND instr(CAST(x AS BLOB), x'00') = 0` dans les quatre CHECK JSON : un octet NUL **brut** est refusé ; l'échappement JSON `\u0000` (six caractères, aucun octet NUL) reste valide | `client_snapshot`, `entreprise_snapshot`, `chantier_snapshot`, `legacy_data` |

Trois commentaires SQL expliquent le *pourquoi* (arrêt au premier NUL de `GLOB`, `substr`, `length()` de TEXT et `json_valid`). Aucune autre ligne ne change : `date_reception`, la levée (PR-3), `origine='import'`, les triggers, les index.

## 2. Diff

```diff
--- a/src-tauri/migrations/metier/009_pv.sql
+++ b/src-tauri/migrations/metier/009_pv.sql
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

## 3. Vérifications (SQLite 3.45.1, SQL actuel comparé au SQL révisé, `INSERT` réels sur la chaîne 001→009)

### 3.1 Matrice de 155 cas : 22 divergences, toutes des octets NUL en fin de valeur

| Champ | Valeurs | Origine | Avant | Après |
|---|---|---|:--:|:--:|
| `numero` (PV initial V6, sans/avec réserves) | `PVR-50001-26␀`, `PVR-50001-26␀junk` | v6 | accepté | **refusé** (4 cas) |
| `created_at` | `…Z␀`, `…Z␀junk` | v6 et import | accepté | **refusé** (4 cas) |
| `client_snapshot`, `entreprise_snapshot`, `chantier_snapshot` | `{}␀`, `{}␀junk` | v6 et import | accepté | **refusé** (12 cas) |
| `legacy_data` | `{}␀`, `{}␀junk` | import | accepté | **refusé** (2 cas) |

Aucune autre divergence sur les 133 autres cas. En particulier **inchangés** : JSON valides (`{}`, `[]`, `null`, `{"é":"日本"}`), JSON invalides (`{`, ``, `x`), NUL à l'intérieur ou au début d'un JSON (déjà refusés), et la chaîne JSON `{"a":"\u0000"}` (**acceptée avant et après**, stockée telle quelle, sans octet NUL).

### 3.2 Exception `origine='import'` et Z-8 : conditions vérifiées

| Point | Résultat | Évolution de règle ? |
|---|---|:--:|
| Numéro d'un PV importé : libre, non vide (`ANCIEN-1`, `pv 12/2019`, `PVR-1`, `x`, `PVR-50001-26`, `PVR-50001-26-01`, `PVR-50001-27`) | accepté avant **et** après | **non** |
| Numéro importé **vide** | refusé avant et après (`numero <> ''`) | non |
| Numéro importé **avec octet NUL** (`ANCIEN␀`, `PVR-50001-26␀`, `PVR-50001-26␀junk`, `␀ANCIEN`, `AN␀CIEN`, `␀`) | accepté avant **et** après (le CHECK de format reste conditionné par `origine='v6'`) | **non** — comportement identique |
| Levée dérivée d'une origine `import` à numéro `ANCIEN␀` | acceptée avant **et** après (G4 compare en binaire : le NUL est recopié) | non — c'est la propagation Z-8, **subsistante** |
| Format, préfixe, année du numéro (seule exemption d'INV-131) | toujours non contrôlés pour `origine='import'` | non |
| `created_at` et JSON d'un PV importé | les nouveaux conjoncts **s'appliquent** aussi à l'import | non : INV-131 n'exempte que le format/préfixe/année du `numero` ; un `created_at` ou un JSON avec NUL n'est pas une donnée « historique remise au client » |

**Conséquence à signaler** : le diff ne modifie **pas** la règle des numéros historiques importés (INV-131 / Z-8). Le NUL dans un numéro importé et sa propagation à la levée subsistent par conception ; ils sont consignés par un test témoin (`test_T51_K_CONSTAT_origine_import_numero_libre_avec_octet_nul_accepte_Z8`).

**Option NON incluse — évolution de règle à décider explicitement (Z-8-NUL).** Interdire l'octet NUL dans un numéro importé serait une restriction de l'exemption d'INV-131 (« numéro historique libre »). Le texte, vérifié valide (le numéro `ANCIEN␀` est alors refusé, et plus aucune levée n'en dérive), serait :

```sql
    CHECK (numero <> ''),
    CHECK (origine <> 'import' OR instr(CAST(numero AS BLOB), x'00') = 0),   -- NON INCLUS : évolution de la règle des numéros historiques
```

Elle exigerait aussi d'inverser le test témoin et de qualifier l'effet sur un futur import (aucun PV V2 aujourd'hui, Z-8). **Pas de décision implicite ici.**

### 3.3 Autres vérifications
- Suite 009 révisée sur ce SQL : **268 tests verts** ; suite complète 001–009 : **1 866 tests verts** ; test machine : 13 verts (détail dans la synthèse).
- Chacun des trois groupes de conjoncts (D1, D2, D3), retiré séparément du SQL révisé, fait échouer des tests propres (matrice dans le diff des tests).

## 4. Ce que ce diff ne fait pas

- aucune modification de 001–008 (voir le plan de remédiation) ;
- aucune modification de `date_reception`, de la levée (PR-3) ni de `origine='import'` ;
- aucun test, rapport de mutation ni script d'équivalence (fichiers séparés, non appliqués) ;
- aucune relance de la campagne de mutation (elle suit l'autorisation, voir la synthèse).

## 5. À arbitrer (SQL)

1. Valider le diff tel quel (D1 + D2 + D3).
2. Z-8-NUL : conserver l'exemption d'import telle quelle (recommandé : aucune évolution implicite) ou interdire le NUL dans les numéros importés (évolution de règle).
3. Version de SQLite embarquée par Tauri : non vérifiée ; le diff n'emploie que `length`, `instr`, `CAST AS BLOB` (disponibles dans toutes les versions de SQLite).
