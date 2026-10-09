# PROPOSITION DE DIFF DES TESTS — `test_009_pv.py` : octet NUL (numero, created_at, quatre champs JSON)

**NON APPLIQUÉ.** `test_009_pv.py` n'a pas été modifié. Ce diff accompagne `PROPOSITION_DIFF__009_pv__controle_nul.md` (révision 2) : les deux s'appliquent ensemble (`patch -p1`, racine du dépôt) ; l'un sans l'autre ne laisse pas la suite verte.

| | sha256 | tests |
|---|---|---:|
| `test_009_pv.py` actuel (inchangé) | `d236c013cf60487c34875eb2e34d5dd7e3ef2a48dcfdf17d426f48222d2d6781` | 255 |
| après application du diff (copie jetable) | `4d56721107285773f12920224c2f83ded43f7aeb74b96a8909ef57beaeb59f04` | **268** |

## 1. Résultat : suite entièrement verte (aucun échec « attendu »)

Mesuré sur une copie jetable portant le SQL révisé **et** ce diff, avec `python3 -B -m unittest` :

| Périmètre | Résultat |
|---|---|
| `test_009_pv` seul | **268 tests, OK** (255 − 1 remplacé + 14 ajoutés) |
| Suite complète `src-tauri/tests/metier` (001 → 009) | **1 866 tests, OK** (1 598 + 268) |
| `src-tauri/tests/machine` | 13 tests, OK |

Les diffs SQL et tests appliqués à une copie du dépôt donnent des fichiers identiques octet pour octet à la copie testée. Aucun `__pycache__` créé (`-B`).

## 2. Ce que le diff change

**Remplacé (1)** — le test qui constatait l'acceptation :

| Avant | Après |
|---|---|
| `test_T51_K_LIMITE_le_GLOB_de_sqlite_s_arrete_au_premier_octet_nul_CONSTAT` : `assertIsNone` sur `PVR-50001-26␀`, `…␀junk`, `created_at …Z␀` (docstring : « NON corrigée par 009 (cadrage validé) ») | `test_T51_K_octet_nul_apres_le_numero_ou_le_created_at_refuse` : **rejet** (CHECK, sans préfixe `INV-`), docstring corrigée (plus aucune attribution au cadrage) |

**Adapté (1 ligne)** — `C_LEGACY_JSON` : `"legacy_data IS NULL OR json_valid(legacy_data)"` → `"json_valid(legacy_data)"`. Le fragment était le texte exact du CHECK : 4 sous-tests de `test_T51_B_origine_import_legacy_optionnels_et_json_controle` auraient échoué sans changement de comportement.

**Ajoutés (14)** :

| Test | Groupe | Cas couverts |
|---|:--:|---|
| `…_numero_initial_v6_octet_nul_refuse_a_toute_position` | B | NUL final, NUL + queue (courte, ≥ 60 octets), NUL au début, NUL seul, NUL double, NUL remplaçant **chacun** des 12 caractères, NUL inséré à **chacune** des 13 positions (29 variantes distinctes) ; type sans et avec réserves |
| `…_numero_initial_v6_conforme_reste_accepte_et_fait_12_octets` | B | bornes `PVR-00001-01`, `PVR-99999-99`, `PVR-00000-00`, années 00/26/27/99 : acceptées (aucun faux rejet) |
| `…_numero_avec_octet_nul_n_est_pas_un_doublon_accepte_par_UNIQUE` | B | `numero + ␀` d'un numéro existant refusé **par le CHECK**, pas toléré par `UNIQUE` |
| `…_created_at_octet_nul_refuse_a_toute_position` | B | 53 variantes (mêmes familles) sur `created_at`, pour un PV **et** pour une levée |
| `…_created_at_conforme_reste_accepte_et_fait_24_octets_y_compris_le_defaut` | B | `.000Z`, `.999Z`, `0000-…`, `9999-…`, et valeur par défaut (`strftime`) : 24 octets, aucun NUL |
| `…_json_octet_nul_brut_refuse_sur_les_quatre_champs` | B | `client_snapshot`, `entreprise_snapshot`, `chantier_snapshot`, `legacy_data` : NUL final, NUL + queue, NUL au début, NUL au milieu, NUL **dans** une chaîne JSON, NUL seul, `[]␀`, `1␀`, `null␀` |
| `…_json_echappement_u0000_est_un_json_valide_distinct_de_l_octet_nul` | B | **échappement valide préservé** : `{"a":"\u0000"}`, `"\u0000"`, clé `\u0000`, tableau, `\\u0000` (barre oblique échappée) acceptés sur les quatre champs ; la valeur stockée est identique, de longueur en octets égale à celle du texte et **sans octet NUL** (`instr(…, x'00') = 0`) |
| `…_json_valeurs_conformes_et_malformees_inchangees_sur_les_quatre_champs` | B | 9 JSON conformes (dont Unicode, imbriqué) acceptés ; 8 malformés (`''`, `x`, `{`, `{"a":1`, `undefined`, `{'a':1}`, `[1,`, `nul`) refusés, sur les quatre champs |
| `…_legacy_data_null_reste_accepte_pour_un_pv_importe` | B | `legacy_data` NULL accepté pour `origine='import'` |
| `…_octet_nul_apres_le_numero_ou_le_created_at_refuse` | K | (remplaçant) cas qui étaient acceptés avant la correction |
| `…_une_origine_v6_a_numero_nul_n_existe_pas_donc_aucune_levee_n_en_derive` | K | l'origine est refusée ; aucune ligne à NUL en base |
| `…_numero_de_levee_avec_octet_nul_refuse_par_G4_a_toute_position` | K | NUL final, + queue, au milieu du numéro d'origine, du suffixe, au début : refus G4 ; levée conforme acceptée |
| `…_CONSTAT_origine_import_numero_libre_avec_octet_nul_accepte_Z8` | K | **témoin de périmètre, pas une règle** : numéros importés à NUL acceptés, numéro vide refusé, levée dérivée de `ANCIEN␀` acceptée avec le NUL recopié ; docstring : toute évolution est une évolution d'INV-131, à décider |
| `…_TEMOIN_sans_les_controles_de_longueur_et_d_octet_nul_les_valeurs_a_queue_passent` | K | la migration 009 privée de ses 6 conjoncts (2 longueurs + 4 `instr`) accepte les valeurs à queue : les conjoncts sont la **seule** garde ; échoue si la structure de SQL change |

## 3. Les tests détectent-ils bien le défaut ? (matrice, mêmes tests, SQL dégradé)

| SQL joué avec les 268 tests | Tests en échec |
|---|---|
| SQL **actuel** (sans D1, D2, D3) | 7 tests (42 sous-tests) : numéro, `created_at`, JSON brut, UNIQUE, K-constat, K-origine, témoin |
| SQL révisé **sans D1** | 5 tests (14 sous-tests) |
| SQL révisé **sans D2** | 3 tests (6 sous-tests) |
| SQL révisé **sans D3** | 2 tests (25 sous-tests) |
| SQL révisé complet | **0** |

Chaque conjoncte est donc la seule garde de ses cas et chaque groupe est surveillé par des tests propres. Les 8 JSON malformés et les 9 conformes des quatre champs valent aussi pour le SQL actuel (non-régression sans changement de comportement).

## 4. Cas demandés — correspondance

| Demande | Test(s) |
|---|---|
| Remplacer le test qui constate l'acceptation | `…_octet_nul_apres_le_numero_ou_le_created_at_refuse` (et suppression de `…_LIMITE_…_CONSTAT`) |
| Quatre champs JSON | `…_json_*` (quatre tests, boucle sur `CHAMPS_JSON`) |
| NUL brut ≠ échappement JSON valide | `…_json_octet_nul_brut_…` (refus) / `…_json_echappement_u0000_…` (accepté, sans octet NUL stocké) |
| Valeurs conformes | `…_numero_…_conforme_…`, `…_created_at_conforme_…`, `…_json_valeurs_conformes_…` |
| Variantes malformées déjà identifiées | `…_json_valeurs_…malformees…` (8 variantes), numéros hors format (tests B existants), NUL aux 29 (numéro) et 53 (`created_at`) variantes |
| Exception `origine='import'` / Z-8 | `…_CONSTAT_origine_import_…_Z8` (aucune règle nouvelle) |

## 5. Limites

- Les tests de la propagation à la levée dépendent des triggers G1–G4 (groupe K, base complète) ; les CHECK sont éprouvés triggers supprimés (groupe B) ; les deux niveaux sont couverts.
- La campagne de mutation n'est **pas** relancée ici (aperçu limité aux conjoncts ajoutés : voir la synthèse) ; la relance complète suit l'autorisation.
- Les services Rust/TS qui écrivent ces colonnes ne sont pas dans le dépôt analysé.

## 6. Diff

```diff
--- a/src-tauri/tests/metier/test_009_pv.py
+++ b/src-tauri/tests/metier/test_009_pv.py
@@ -628,7 +628,7 @@
 C_NUMERO_V6 = "numero GLOB 'PVR-"
 C_CREATED = "created_at GLOB"
 C_ORIGINE = "origine IN ('v6', 'import')"
-C_LEGACY_JSON = "legacy_data IS NULL OR json_valid(legacy_data)"
+C_LEGACY_JSON = "json_valid(legacy_data)"
 C_UNIQUE_NUMERO = "UNIQUE constraint failed: pv.numero"
 C_UNIQUE_SUFFIXE = "UNIQUE constraint failed: pv.origine_pv_id, pv.suffixe"
 
@@ -903,6 +903,101 @@
             with self.subTest(numero=n):
                 self.ok_l(numero=n)
 
+    # --- octet NUL : GLOB, substr, length() de TEXT et json_valid s'arrêtent au premier octet NUL ; la longueur est contrôlée en octets -----------
+    @staticmethod
+    def variantes_nul(base):
+        """Toutes les façons de placer un octet NUL dans `base` : final, suivi d'une queue (courte, longue), au début, seul, à la place de chaque caractère, inséré à chaque position."""
+        v = [base + "\x00", base + "\x00junk", base + "\x00" + "x" * 60, "\x00" + base, "\x00", base + "\x00\x00"]
+        v += [base[:i] + "\x00" + base[i + 1:] for i in range(len(base))]
+        v += [base[:i] + "\x00" + base[i:] for i in range(len(base) + 1)]
+        return list(dict.fromkeys(v))
+
+    def test_T51_B_numero_initial_v6_octet_nul_refuse_a_toute_position(self):
+        variantes = self.variantes_nul("PVR-50001-26")
+        self.assertGreater(len(variantes), 25)
+        for n in variantes:
+            for t in (SR, AR):
+                with self.subTest(numero=repr(n), type=t):
+                    self.ko_f(C_NUMERO_V6, t, numero=n)
+
+    def test_T51_B_numero_initial_v6_conforme_reste_accepte_et_fait_12_octets(self):
+        for n, d in (("PVR-00001-01", "2001-03-04"), ("PVR-99999-99", "2099-12-31"), ("PVR-00000-00", "2000-01-01"), ("PVR-50001-26", "2026-10-20"), ("PVR-12345-27", "2027-01-01")):
+            with self.subTest(numero=n):
+                self.assertEqual(len(n.encode("utf-8")), 12)
+                self.ok(SR, numero=n, date_reception=d)
+                self.ok(AR, numero=n, date_reception=d)
+
+    def test_T51_B_numero_avec_octet_nul_n_est_pas_un_doublon_accepte_par_UNIQUE(self):
+        """Sans le contrôle de longueur, `PVR-x\\0` et `PVR-x` coexisteraient (UNIQUE compare les octets) : deux numéros affichés à l'identique."""
+        existant = self.un("SELECT numero FROM pv WHERE id=?", self.SR)[0]
+        for suite in ("\x00", "\x00junk"):
+            with self.subTest(suite=repr(suite)):
+                m = self.essai_pv(SR, numero=existant + suite)
+                self.ko_f(C_NUMERO_V6, SR, numero=existant + suite)
+                self.assertNotIn("UNIQUE", m)
+
+    def test_T51_B_created_at_octet_nul_refuse_a_toute_position(self):
+        variantes = self.variantes_nul("2026-10-20T10:11:12.345Z")
+        self.assertGreater(len(variantes), 50)
+        for ts in variantes:
+            with self.subTest(created_at=repr(ts)):
+                self.ko_f(C_CREATED, SR, created_at=ts)
+                self.ko_lf(C_CREATED, created_at=ts)                                       # la levée porte le même CHECK
+
+    def test_T51_B_created_at_conforme_reste_accepte_et_fait_24_octets_y_compris_le_defaut(self):
+        for ts in ("2026-10-20T10:00:00.000Z", "2026-10-20T23:59:59.999Z", "0000-01-01T00:00:00.000Z", "9999-12-31T23:59:59.999Z"):
+            with self.subTest(ts=ts):
+                self.assertEqual(len(ts.encode("utf-8")), 24)
+                self.ok(SR, created_at=ts)
+                self.ok_l(created_at=ts)
+        pid = self.pv(self.B, SR, created_at=OMIT)
+        self.assertEqual(self.un("SELECT length(CAST(created_at AS BLOB)), instr(CAST(created_at AS BLOB), x'00') FROM pv WHERE id=?", pid), (24, 0))
+
+    CHAMPS_JSON = ("client_snapshot", "entreprise_snapshot", "chantier_snapshot", "legacy_data")
+
+    def essai_json(self, champ, valeur):
+        """Un PV portant `valeur` dans l'un des quatre champs JSON de 009 (`legacy_data` n'existe que pour origine='import')."""
+        if champ == "legacy_data":
+            return self.essai_pv(SR, origine="import", legacy_data=valeur)
+        return self.essai_pv(SR, **{champ: valeur})
+
+    def test_T51_B_json_octet_nul_brut_refuse_sur_les_quatre_champs(self):
+        for c in self.CHAMPS_JSON:
+            for bad in ("{}\x00", "{}\x00junk", "{}\x00" + "x" * 60, "\x00{}", "{\x00}", '{"a":"x\x00y"}', '{"a":"\x00"}', "\x00", "[]\x00", "1\x00", "null\x00"):
+                with self.subTest(colonne=c, valeur=repr(bad)):
+                    m = self.essai_json(c, bad)
+                    self.ko_check(m)
+                    self.assertIn(f"json_valid({c})", m)
+
+    def test_T51_B_json_echappement_u0000_est_un_json_valide_distinct_de_l_octet_nul(self):
+        """`\\u0000` (six caractères) est la forme JSON d'un NUL dans une chaîne : valide, stockée telle quelle, sans octet NUL."""
+        for c in self.CHAMPS_JSON:
+            for ok_ in ('{"a":"\\u0000"}', '"\\u0000"', '{"\\u0000":1}', '["\\u0000","x\\u0000y"]', '{"a":"\\\\u0000"}'):
+                with self.subTest(colonne=c, valeur=ok_):
+                    self.assertNotIn("\x00", ok_)
+                    self.ok_(self.essai_json(c, ok_))
+        for c, j in (("client_snapshot", '{"a":"\\u0000"}'), ("entreprise_snapshot", '"\\u0000"'), ("chantier_snapshot", '["\\u0000"]')):
+            with self.subTest(stocke=c):
+                pid = self.pv(self.B, SR, **{c: j})
+                self.assertEqual(self.un(f"SELECT {c}, length(CAST({c} AS BLOB)), instr(CAST({c} AS BLOB), x'00') FROM pv WHERE id=?", pid), (j, len(j.encode("utf-8")), 0))
+        pid = self.pv(self.B, SR, origine="import", legacy_data='{"k":"\\u0000"}')
+        self.assertEqual(self.un("SELECT legacy_data, instr(CAST(legacy_data AS BLOB), x'00') FROM pv WHERE id=?", pid), ('{"k":"\\u0000"}', 0))
+
+    def test_T51_B_json_valeurs_conformes_et_malformees_inchangees_sur_les_quatre_champs(self):
+        for c in self.CHAMPS_JSON:
+            for good in ("{}", "[]", '{"nom":"Dupont"}', "null", "1", '"x"', "true", '{"é":"日本"}', '{"a":[1,2,{"b":null}]}'):
+                with self.subTest(colonne=c, valeur=good):
+                    self.ok_(self.essai_json(c, good))
+            for bad in ("", "x", "{", '{"a":1', "undefined", "{'a':1}", "[1,", "nul"):
+                with self.subTest(colonne=c, valeur=bad):
+                    m = self.essai_json(c, bad)
+                    self.ko_check(m)
+                    self.assertIn(f"json_valid({c})", m)
+
+    def test_T51_B_legacy_data_null_reste_accepte_pour_un_pv_importe(self):
+        self.ok(SR, origine="import", legacy_data=None)
+        self.ok(SR, origine="import", legacy_data=None, legacy_id="L-1")
+
     # --- BLOC-IMP : comportement générique du schéma (aucun PV n'est importé de la V2) ----------------------------------------------
     def test_T51_B_origine_hors_liste_ou_null_refusee(self):
         for o in ("v7", "", "V6", "IMPORT", "Import", "import ", "v6 ", "manuel", 0):
@@ -2443,12 +2538,61 @@
         # G4 compare par égalité binaire : un octet NUL dans le numéro de la levée est refusé
         self.assertIn(M_G4, self.essai_levee(numero="PVR-00001-26-01\x00"))
 
-    def test_T51_K_LIMITE_le_GLOB_de_sqlite_s_arrete_au_premier_octet_nul_CONSTAT(self):
-        """LIMITE constatée, NON corrigée par 009 (cadrage validé) : GLOB ne lit pas au-delà d'un octet NUL ; un numéro PV initial V6 ou un created_at suivi d'un octet NUL
-        franchit donc leurs CHECK de format. C'est le comportement de TOUS les CHECK GLOB de la chaîne (created_at depuis 001). Ce test documente la limite : il ne la valide pas."""
-        self.assertIsNone(self.essai_pv(SR, numero="PVR-50001-26\x00"))
-        self.assertIsNone(self.essai_pv(SR, created_at="2026-10-20T10:00:00.000Z\x00"))
-        self.assertIsNone(self.essai_pv(SR, numero="PVR-50001-26\x00junk"))
+    def test_T51_K_octet_nul_apres_le_numero_ou_le_created_at_refuse(self):
+        """Un octet NUL ne peut suivre ni un numéro de PV initial V6 ni un created_at : GLOB, substr et length() de TEXT s'arrêtent au premier octet NUL, la longueur
+        est donc contrôlée en octets (length(CAST(x AS BLOB))). Ces valeurs étaient acceptées avant la correction ; tous les autres cas sont au groupe B."""
+        for t in (SR, AR):
+            self.ko_check(self.essai_pv(t, numero="PVR-50001-26\x00"))
+            self.ko_check(self.essai_pv(t, numero="PVR-50001-26\x00junk"))
+        self.ko_check(self.essai_pv(SR, created_at="2026-10-20T10:00:00.000Z\x00"))
+        self.ko_check(self.essai_pv(SR, created_at="2026-10-20T10:00:00.000Z\x00junk"))
+
+    def test_T51_K_une_origine_v6_a_numero_nul_n_existe_pas_donc_aucune_levee_n_en_derive(self):
+        avant = self.un("SELECT COUNT(*) FROM pv")[0]
+        for n in ("PVR-50001-26\x00", "PVR-50001-26\x00junk"):
+            with self.subTest(numero=repr(n)):
+                self.ko_check(self.essai_pv(AR, numero=n))
+        self.assertEqual(self.un("SELECT COUNT(*) FROM pv")[0], avant)
+        self.assertEqual(self.un("SELECT COUNT(*) FROM pv WHERE instr(CAST(numero AS BLOB), x'00') > 0")[0], 0)
+
+    def test_T51_K_numero_de_levee_avec_octet_nul_refuse_par_G4_a_toute_position(self):
+        origine = self.un("SELECT numero FROM pv WHERE id=?", self.AR)[0]
+        attendu = origine + "-01"
+        variantes = [attendu + "\x00", attendu + "\x00junk", origine + "\x00-01", "\x00" + attendu, origine + "-0\x001", origine + "-\x0001", origine[:5] + "\x00" + attendu[5:]]
+        for n in variantes:
+            with self.subTest(numero=repr(n)):
+                self.assertIn(M_G4, self.essai_levee(numero=n))
+        self.ok_l(numero=attendu)
+
+    def test_T51_K_CONSTAT_origine_import_numero_libre_avec_octet_nul_accepte_Z8(self):
+        """CONSTAT, non une règle : INV-131 exempte le numéro historique d'un PV importé (numéro libre, non vide, unique) ; 009 ne change pas cette exemption et ne
+        contrôle pas l'octet NUL d'un numéro importé. Le NUL d'une telle origine se retrouve dans la levée dérivée par G4 (Z-8 / QO-2 : aucun PV V2 n'est importé).
+        Si Rémy décidait d'interdire le NUL dans les numéros importés, ce test devrait être inversé : c'est une évolution de la règle INV-131, à décider explicitement."""
+        for n in ("ANCIEN\x00", "ANCIEN\x00junk", "\x00ANCIEN", "AN\x00CIEN", "\x00"):
+            with self.subTest(numero=repr(n)):
+                self.ok(SR, origine="import", numero=n)
+        self.ko_check(self.essai_pv(SR, origine="import", numero=""))                      # non vide : inchangé
+        oid = self.pv(self.B, AR, origine="import", numero="ANCIEN\x00")
+        lid = self.levee(oid)                                                              # levée dérivée : acceptée par G4 (égalité binaire), le NUL est recopié
+        self.assertEqual(self.un("SELECT numero FROM pv WHERE id=?", lid)[0], "ANCIEN\x00-01")
+
+    def test_T51_K_TEMOIN_sans_les_controles_de_longueur_et_d_octet_nul_les_valeurs_a_queue_passent(self):
+        """Témoin : la même migration 009 privée de ses conjonctes NUL accepte les valeurs à queue ; les conjonctes sont donc la seule garde."""
+        sql = SQL_009
+        sql = re.sub(r"\n\s+AND length\(CAST\((numero|created_at) AS BLOB\)\) = (12|24)", "", sql)
+        sql, n_json = re.subn(r" AND instr\(CAST\((\w+) AS BLOB\), x'00'\) = 0", "", sql)
+        self.assertEqual(n_json, 4)
+        self.assertEqual(sql.count("AS BLOB"), SQL_009.count("AS BLOB") - 6)
+        db = G.migrer11()
+        T.appliquer(db, RANG, sql)
+        t = self._sur(db)
+        t.m = t.bc()
+        t.B = t.m.b
+        self.assertIsNone(t.tente(t.B, SR, numero="PVR-50001-26\x00junk"))
+        self.assertIsNone(t.tente(t.B, SR, created_at="2026-10-20T10:00:00.000Z\x00junk"))
+        for c in ("client_snapshot", "entreprise_snapshot", "chantier_snapshot"):
+            self.assertIsNone(t.tente(t.B, SR, **{c: "{}\x00junk"}))
+        self.assertIsNone(t.tente(t.B, SR, origine="import", legacy_data="{}\x00junk"))
 
     def test_T51_K_chaines_hostiles_et_tres_longues_traitees_comme_des_donnees(self):
         for v in ("x'; DROP TABLE pv;--", "' OR '1'='1", "%", "x" * 100000):
```
