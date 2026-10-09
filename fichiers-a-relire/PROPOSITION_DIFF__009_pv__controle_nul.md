# PROPOSITION DE DIFF SQL — 009 : contrôle des octets NUL (`numero`, `created_at`)

**NON APPLIQUÉ.** Proposition à valider par Rémy (décisions D1, D2, D3, D5 du fichier `COMPLEMENT_ANALYSE__009_pv__controle_nul.md`). `009_pv.sql` n'a pas été modifié (sha256 inchangé : `d32b20a4dc6130246cef1ec3fdef438bc568015d66ed9fef1d0ba8d56b804381`).
Les diffs ont été générés contre ce fichier et vérifiés avec `patch --dry-run` sur une copie jetable ; ils sont indépendants du reste du dépôt. Aucune règle métier ne change : la longueur exacte en **octets** est ajoutée à côté du `GLOB` prescrit (INV-20 / type TS).

Comportement vérifié sur la variante correspondante (SQLite 3.45.1) : voir §2.3-2.4 du complément d'analyse (0 divergence sur 23 825 cas, 0 faux rejet). Suite existante : 254/255 (seul le test-constat `…_LIMITE_…_CONSTAT` échoue, attendu). **Une relance complète des tests et de la campagne de mutation est requise avant toute livraison** (D5).

## Diff 1 — correction minimale (D1 + D2) : à retenir si les deux sont acceptées

```diff
--- a/src-tauri/migrations/metier/009_pv.sql
+++ b/src-tauri/migrations/metier/009_pv.sql
@@ -107,12 +107,16 @@
     CHECK ((reserves IS NOT NULL) = (type = 'reception_avec_reserves')),
     CHECK (origine <> 'v6' OR (legacy_id IS NULL AND legacy_data IS NULL)),
     -- numéro d'un PV INITIAL V6 : PVR + 5 chiffres + année de date_reception (INV-20) ;
-    -- import : numéro libre non vide ; levée : aucun contrôle de format ajouté (PR-3), son numéro est imposé par G4
+    -- import : numéro libre non vide ; levée : aucun contrôle de format ajouté (PR-3), son numéro est imposé par G4.
+    -- GLOB, substr et length() de TEXT s'arrêtent au premier octet NUL : la longueur est donc contrôlée en octets
+    -- (CAST ... AS BLOB) pour qu'aucune queue ne suive le format.
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

## Diff 2 — D1 seule (`numero` du PV initial V6)

```diff
--- a/src-tauri/migrations/metier/009_pv.sql
+++ b/src-tauri/migrations/metier/009_pv.sql
@@ -107,10 +107,13 @@
     CHECK ((reserves IS NOT NULL) = (type = 'reception_avec_reserves')),
     CHECK (origine <> 'v6' OR (legacy_id IS NULL AND legacy_data IS NULL)),
     -- numéro d'un PV INITIAL V6 : PVR + 5 chiffres + année de date_reception (INV-20) ;
-    -- import : numéro libre non vide ; levée : aucun contrôle de format ajouté (PR-3), son numéro est imposé par G4
+    -- import : numéro libre non vide ; levée : aucun contrôle de format ajouté (PR-3), son numéro est imposé par G4.
+    -- GLOB, substr et length() de TEXT s'arrêtent au premier octet NUL : la longueur est donc contrôlée en octets
+    -- (CAST ... AS BLOB) pour qu'aucune queue ne suive le format.
     CHECK (origine <> 'v6' OR type = 'levee_reserves'
            OR (numero GLOB 'PVR-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'
-               AND substr(numero, 11, 2) = substr(date_reception, 3, 2))),
+               AND substr(numero, 11, 2) = substr(date_reception, 3, 2)
+               AND length(CAST(numero AS BLOB)) = 12)),
     CHECK (created_at GLOB
         '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
 ) STRICT;
```

## Diff 3 — D2 seule (`created_at`)

```diff
--- a/src-tauri/migrations/metier/009_pv.sql
+++ b/src-tauri/migrations/metier/009_pv.sql
@@ -112,7 +112,8 @@
            OR (numero GLOB 'PVR-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'
                AND substr(numero, 11, 2) = substr(date_reception, 3, 2))),
     CHECK (created_at GLOB
-        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
+        '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z'
+        AND length(CAST(created_at AS BLOB)) = 24)
 ) STRICT;
 
 
```

(Les diffs 2 et 3 s'appliquent chacun sur le fichier actuel ; ils ne s'appliquent pas l'un après l'autre.)

## Diff 4 — OPTIONNEL, élargit le périmètre (option JSON, D3) : à appliquer **après** le diff 1

Cinq colonnes : `client_snapshot`, `entreprise_snapshot`, `chantier_snapshot`, `legacy_data` (4 CHECK). Non inclus dans la correction minimale. Impose d'adapter la constante `C_LEGACY_JSON` du test (4 sous-tests échouent sinon, sans changement de comportement) — voir §3.2 A2.

```diff
--- a/src-tauri/migrations/metier/009_pv.sql
+++ b/src-tauri/migrations/metier/009_pv.sql
@@ -81,11 +81,11 @@
     date_reception              TEXT    NOT NULL
                                 CHECK (date_reception GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_reception) IS date_reception),
     -- BLOC-SNAP
-    client_snapshot             TEXT    NOT NULL CHECK (json_valid(client_snapshot)),
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
@@ -95,7 +95,7 @@
     -- BLOC-IMP
     origine                     TEXT    NOT NULL DEFAULT 'v6' CHECK (origine IN ('v6', 'import')),
     legacy_id                   TEXT,
-    legacy_data                 TEXT    CHECK (legacy_data IS NULL OR json_valid(legacy_data)),
+    legacy_data                 TEXT    CHECK (legacy_data IS NULL OR (json_valid(legacy_data) AND instr(CAST(legacy_data AS BLOB), x'00') = 0)),
 
     UNIQUE (origine_pv_id, suffixe),
     CHECK (numero <> ''),
```

## Hors de ce diff (volontairement)

- `date_reception` : déjà protégée (`date(x) IS x`).
- Levée (PR-3) et `origine='import'` : aucun CHECK de format ajouté ; la propagation d'un NUL d'une origine `import` reste possible (Z-8).
- Migrations 001–008 : non modifiées ; 90 colonnes concernées par le même mécanisme (D4, complément §1).
- Tests, rapport de mutation, `equiv009.py` : leur mise à jour fait partie de D5, non préparée ici.
