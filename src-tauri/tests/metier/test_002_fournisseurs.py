"""T-27 — DDL de la tranche Fournisseurs (modèle V3.10, §4.4 ; migration metier/002_fournisseurs.sql).
Table : fournisseurs. Les migrations 001 puis 002 sont appliquées comme le fait le runner.

Exécution : python3 src-tauri/tests/metier/test_002_fournisseurs.py
Les méthodes portent le nom de l'invariant vérifié (test_INV_xx_…).
Ces tests ne dépendent d'aucune interface graphique ni d'aucun service : l'attribution du code par
le service est reproduite avec la requête documentée (modèle §4.17 point 8).
"""
import pathlib
import re
import sqlite3
import unittest

MIGRATIONS = pathlib.Path(__file__).resolve().parents[2] / "migrations"
SQL_001 = (MIGRATIONS / "metier" / "001_initial.sql").read_text(encoding="utf-8")
SQL_002 = (MIGRATIONS / "metier" / "002_fournisseurs.sql").read_text(encoding="utf-8")
SQL_MACHINE = (MIGRATIONS / "machine" / "001_initial.sql").read_text(encoding="utf-8")

TABLES_001 = {"import_anomalies", "numerotation_sequences", "categories_prestations", "categories_depenses",
              "clients", "prestations", "prestation_garanties"}
TRIGGERS_001 = {"tr_90_import_anomalies_no_delete", "tr_90_import_anomalies_update",
                "tr_95_numerotation_sequences_no_decrease"}
INDEXES_001 = {"idx_clients_statut", "idx_prestations_categorie_id", "idx_prestations_actif",
               "idx_import_anomalies_categorie_statut"}
COLONNES = ["id", "code", "nom", "adresse", "cpville", "tel", "email", "notes", "statut", "created_at", "updated_at"]
TS_GLOB = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")

ATTRIBUER = ("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES (?, ?, 1) "
             "ON CONFLICT (type_objet, annee) DO UPDATE SET dernier_numero = dernier_numero + 1, "
             "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') RETURNING dernier_numero")

def migrer():
    db = sqlite3.connect(":memory:", isolation_level=None)
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("BEGIN;" + SQL_001 + "\nCOMMIT;")
    db.execute("PRAGMA user_version = 1")
    db.executescript("BEGIN;" + SQL_002 + "\nCOMMIT;")
    db.execute("PRAGMA user_version = 2")
    return db

class Base(unittest.TestCase):
    def setUp(self):
        self.db = migrer()
    def refuse(self, sql, *args):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(sql, args)
    def un(self, sql, *args):
        return self.db.execute(sql, args).fetchone()
    def fournisseur(self, code="FOU-0001", **kw):
        cols = {"code": code, "nom": "Point P", "statut": "actif"}
        cols.update(kw)
        self.db.execute(f"INSERT INTO fournisseurs ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))
        return self.un("SELECT id FROM fournisseurs WHERE code=?", code)[0]
    def creer_avec_sequence(self, nom="Point P"):
        self.db.execute("BEGIN")
        try:
            n = self.un(ATTRIBUER, "FOU", 0)[0]
            code = f"FOU-{n:04d}"
            self.db.execute("INSERT INTO fournisseurs (code, nom, statut) VALUES (?, ?, 'actif')", (code, nom))
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise
        return code

class Migration(Base):
    def test_T27_migration_sur_base_issue_de_001(self):
        self.assertEqual(self.un("PRAGMA user_version")[0], 2)
        noms = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        self.assertEqual(noms, TABLES_001 | {"fournisseurs"})
        strict = {r[1] for r in self.db.execute("PRAGMA table_list") if r[5] == 1}
        self.assertIn("fournisseurs", strict)
        self.assertEqual({r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}, TRIGGERS_001)
        self.assertEqual({r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")}, INDEXES_001 | {"idx_fournisseurs_statut"})
        self.assertEqual([r[2] for r in self.db.execute("PRAGMA index_info(idx_fournisseurs_statut)")], ["statut"])
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(self.db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
    def test_T27_aucune_donnee_initiale(self):
        for t in TABLES_001 | {"fournisseurs"}:
            self.assertEqual(self.un(f"SELECT COUNT(*) FROM {t}")[0], 0, t)
        code = re.sub(r"--[^\n]*", "", SQL_002)
        self.assertNotRegex(code, r"(?i)\b(INSERT|REPLACE|UPDATE|DELETE|DROP|ALTER|PRAGMA|BEGIN|COMMIT)\b")
        self.assertEqual(re.findall(r"(?i)\bCREATE\s+(\w+)", code), ["TABLE", "INDEX"])

class Invariants(Base):
    def test_INV_04_id_autoincrement_jamais_reutilise(self):
        self.assertIn("AUTOINCREMENT", self.un("SELECT sql FROM sqlite_master WHERE name='fournisseurs'")[0])
        a = self.fournisseur("FOU-0001"); self.assertEqual(a, 1)
        self.assertEqual(self.fournisseur("FOU-0002"), a + 1)
        self.db.execute("DELETE FROM fournisseurs WHERE id=?", (a + 1,))
        self.assertGreater(self.fournisseur("FOU-0003"), a + 1)
    def test_T27_colonnes_du_modele_sans_champ_d_import(self):
        infos = {r[1]: r for r in self.db.execute("PRAGMA table_info(fournisseurs)")}
        self.assertEqual([r[1] for r in self.db.execute("PRAGMA table_info(fournisseurs)")], COLONNES)
        for interdit in ("origine","legacy_id","legacy_numero","legacy_data","migration_id","siret","tva","iban"):
            self.assertNotIn(interdit, infos)
        self.assertEqual(infos["id"][5], 1)
        for c in ("code","nom","statut","created_at","updated_at"): self.assertEqual(infos[c][3], 1, c)
        for c in ("adresse","cpville","tel","email","notes"): self.assertEqual(infos[c][3], 0, c)
        self.assertIsNone(infos["statut"][4])
    def test_INV_20_format_code_fournisseur(self):
        for i,v in enumerate(["FOU-0001","FOU-0042","FOU-0999","FOU-9999"]): self.fournisseur(v,nom=f"N{i}")
        invalides=["","FOU-1","FOU-001","FOU-00001","FOU-10000","fou-0001","Fou-0001","FOU-000A","FOU0001","FOU-0001 "," FOU-0001","CLI-0001","DEP-00001-26","FOU-0001-26","FOU--001","FOU-+001","FOU-1.00"]
        for v in invalides:
            with self.subTest(code=v): self.refuse("INSERT INTO fournisseurs (code, nom, statut) VALUES (?, 'X', 'actif')", v)
        self.refuse("INSERT INTO fournisseurs (code, nom, statut) VALUES (NULL, 'X', 'actif')")
        self.refuse("INSERT INTO fournisseurs (nom, statut) VALUES ('X', 'actif')")
    def test_INV_20_code_unique(self):
        self.fournisseur("FOU-0001"); self.refuse("INSERT INTO fournisseurs (code, nom, statut) VALUES ('FOU-0001', 'Autre', 'actif')")
        self.fournisseur("FOU-0002"); self.refuse("UPDATE fournisseurs SET code='FOU-0001' WHERE code='FOU-0002'")
        self.fournisseur("FOU-0003",nom="Point P")
    def test_T27_nom_obligatoire_non_vide(self):
        self.refuse("INSERT INTO fournisseurs (code, nom, statut) VALUES ('FOU-0001', '', 'actif')")
        self.refuse("INSERT INTO fournisseurs (code, nom, statut) VALUES ('FOU-0001', NULL, 'actif')")
        self.refuse("INSERT INTO fournisseurs (code, statut) VALUES ('FOU-0001', 'actif')")
        self.fournisseur("FOU-0001")
        self.refuse("UPDATE fournisseurs SET nom='' WHERE code='FOU-0001'")
        self.refuse("UPDATE fournisseurs SET nom=NULL WHERE code='FOU-0001'")
    def test_T27_champs_facultatifs_nullables(self):
        self.fournisseur("FOU-0001")
        self.assertEqual(self.un("SELECT adresse, cpville, tel, email, notes FROM fournisseurs WHERE code='FOU-0001'"),(None,None,None,None,None))
        self.fournisseur("FOU-0002",adresse="1 rue des Lilas",cpville="62300 Lens",tel="03 21 00 00 00",email="contact@exemple.fr",notes="Livraison le jeudi")
        self.assertEqual(self.un("SELECT cpville FROM fournisseurs WHERE code='FOU-0002'")[0],"62300 Lens")
        self.db.execute("UPDATE fournisseurs SET adresse=NULL, tel=NULL WHERE code='FOU-0002'")
    def test_INV_06_statut_actif_ou_archive(self):
        self.fournisseur("FOU-0001",statut="actif"); self.fournisseur("FOU-0002",statut="archive")
        for i,v in enumerate(["a_rattacher","inactif","archivé","ACTIF","Archive",""," actif"]):
            with self.subTest(statut=v): self.refuse("INSERT INTO fournisseurs (code, nom, statut) VALUES (?, 'X', ?)",f"FOU-{i+10:04d}",v)
        self.refuse("INSERT INTO fournisseurs (code, nom, statut) VALUES ('FOU-0099', 'X', NULL)")
        self.refuse("INSERT INTO fournisseurs (code, nom) VALUES ('FOU-0099', 'X')")
        self.db.execute("UPDATE fournisseurs SET statut='archive' WHERE code='FOU-0001'")
        self.refuse("UPDATE fournisseurs SET statut='supprime' WHERE code='FOU-0001'")
        self.refuse("UPDATE fournisseurs SET statut=NULL WHERE code='FOU-0001'")
    def test_T27_liste_statut_exacte(self):
        sql = self.un("SELECT sql FROM sqlite_master WHERE name='fournisseurs'")[0]
        m = re.search(r"\bstatut\s+IN\s+\(([^)]*)\)", sql)
        self.assertIsNotNone(m)
        self.assertEqual(set(re.findall(r"'([^']*)'", m.group(1))), {"actif", "archive"})

    def test_INV_10_horodatages(self):
        self.fournisseur("FOU-0001")
        c,u=self.un("SELECT created_at, updated_at FROM fournisseurs WHERE code='FOU-0001'"); self.assertRegex(c,TS_GLOB); self.assertRegex(u,TS_GLOB)
        self.fournisseur("FOU-0002",created_at="2026-10-01T10:00:00.000Z",updated_at="2026-10-02T11:30:15.123Z")
        invalides=["2026-10-01","2026-10-01 10:00:00","2026-10-01T10:00:00Z","2026-10-01T10:00:00.000","now","","2026-10-01T10:00:00.00Z"]
        for i,v in enumerate(invalides):
            with self.subTest(horodatage=v):
                self.refuse("INSERT INTO fournisseurs (code, nom, statut, created_at) VALUES (?, 'X', 'actif', ?)",f"FOU-{i+100:04d}",v)
                self.refuse("INSERT INTO fournisseurs (code, nom, statut, updated_at) VALUES (?, 'X', 'actif', ?)",f"FOU-{i+200:04d}",v)
        self.refuse("INSERT INTO fournisseurs (code, nom, statut, created_at) VALUES ('FOU-0003', 'X', 'actif', NULL)")
        self.refuse("UPDATE fournisseurs SET updated_at='2026-10-01' WHERE code='FOU-0001'")
        self.refuse("UPDATE fournisseurs SET updated_at=NULL WHERE code='FOU-0001'")
    def test_INV_05_aucune_fk_et_suppression_sans_historique(self):
        self.assertEqual(self.db.execute("PRAGMA foreign_key_list(fournisseurs)").fetchall(), [])
        cibles={r[2] for t in TABLES_001 for r in self.db.execute(f"PRAGMA foreign_key_list({t})")}
        self.assertNotIn("fournisseurs",cibles)
        self.fournisseur("FOU-0001"); self.db.execute("DELETE FROM fournisseurs WHERE code='FOU-0001'")
        self.assertEqual(self.un("SELECT COUNT(*) FROM fournisseurs")[0],0)
    def test_INV_21_sequence_FOU_annee_zero(self):
        self.assertEqual([self.creer_avec_sequence() for _ in range(3)],["FOU-0001","FOU-0002","FOU-0003"])
        self.assertEqual(self.un("SELECT annee, dernier_numero FROM numerotation_sequences WHERE type_objet='FOU'"),(0,3))
        self.assertEqual(self.un("SELECT COUNT(*) FROM numerotation_sequences")[0],1)
        self.refuse(ATTRIBUER,"FOU",26)
        self.refuse("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('FOU',1,1)")
        self.refuse("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('FOU',0,1)")
        self.db.execute("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('CLI',0,7)")
        self.assertEqual(self.un(ATTRIBUER,"FOU",0)[0],4)
    def test_INV_22_plafond_FOU_9999(self):
        self.db.execute("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('FOU',0,9998)")
        self.assertEqual(self.creer_avec_sequence(),"FOU-9999")
        with self.assertRaises(sqlite3.IntegrityError): self.creer_avec_sequence()
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='FOU'")[0],9999)
        self.assertEqual(self.un("SELECT COUNT(*) FROM fournisseurs")[0],1)
        self.refuse("INSERT INTO fournisseurs (code, nom, statut) VALUES ('FOU-10000','X','actif')")
        self.refuse("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('CLI',0,10000)")
    def test_INV_22_numero_jamais_reutilise(self):
        for _ in range(3): self.creer_avec_sequence()
        self.db.execute("DELETE FROM fournisseurs WHERE code='FOU-0003'")
        self.assertEqual(self.creer_avec_sequence(),"FOU-0004")
        self.db.execute("DELETE FROM fournisseurs")
        self.assertEqual(self.creer_avec_sequence(),"FOU-0005")
        self.refuse("UPDATE numerotation_sequences SET dernier_numero=2 WHERE type_objet='FOU'")
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='FOU'")[0],5)
    def test_INV_25_high_water_hors_base_metier(self):
        noms={r[0] for r in self.db.execute("SELECT name FROM sqlite_master")}
        self.assertNotIn("sequence_high_water",noms)
        self.assertRegex(SQL_MACHINE,r"CREATE TABLE sequence_high_water\b")
        self.assertRegex(SQL_MACHINE,r"type_objet\s+TEXT\s+NOT NULL CHECK \(type_objet IN \('CLI','FOU'")
        self.assertNotIn("sequence_high_water",SQL_002)

if __name__=="__main__":
    unittest.main(verbosity=2)
