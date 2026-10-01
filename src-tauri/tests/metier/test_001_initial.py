"""
T-26 — DDL de la première tranche métier (modèle V3.9, §4.17 ; migration metier/001_initial.sql).
Tables : import_anomalies, numerotation_sequences, categories_prestations, categories_depenses,
clients, prestations, prestation_garanties.

Exécution : python3 src-tauri/tests/metier/test_001_initial.py
Les méthodes portent le nom de l'invariant vérifié (test_INV_xx_…).
"""
import pathlib
import sqlite3
import unittest

SQL = (pathlib.Path(__file__).resolve().parents[2] / "migrations" / "metier" / "001_initial.sql").read_text(encoding="utf-8")
TS = "2026-10-01T10:00:00.000Z"
TABLES = ("import_anomalies", "numerotation_sequences", "categories_prestations", "categories_depenses",
          "clients", "prestations", "prestation_garanties")
TRIGGERS = {"tr_90_import_anomalies_no_delete", "tr_90_import_anomalies_update",
            "tr_95_numerotation_sequences_no_decrease"}
INDEXES = {"idx_clients_statut", "idx_prestations_categorie_id", "idx_prestations_actif",
           "idx_import_anomalies_categorie_statut"}

ATTRIBUER = ("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES (?, ?, 1) "
             "ON CONFLICT (type_objet, annee) DO UPDATE SET dernier_numero = dernier_numero + 1, "
             "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') RETURNING dernier_numero")


def migrer():
    """Applique la migration comme le runner : une transaction, user_version après succès."""
    db = sqlite3.connect(":memory:", isolation_level=None)
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("BEGIN;" + SQL + "\nCOMMIT;")
    db.execute("PRAGMA user_version = 1")
    return db


class Base(unittest.TestCase):
    def setUp(self):
        self.db = migrer()

    def refuse(self, sql, *args):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(sql, args)

    def un(self, sql, *args):
        return self.db.execute(sql, args).fetchone()

    def categorie(self, code="CAT-1"):
        self.db.execute("INSERT INTO categories_prestations (code, libelle, actif, ordre) VALUES (?, 'Libellé', 1, 1)", (code,))
        return self.un("SELECT id FROM categories_prestations WHERE code=?", code)[0]

    def prestation(self, ref="PLO-001", prix="10", cat=None, **kw):
        cat = cat or self.categorie(f"C-{ref}")
        cols = {"reference": ref, "designation": "Désignation", "categorie_id": cat, "unite": "u",
                "type_prestation": "pose", "prix_unitaire_ht": prix, "actif": 1}
        cols.update(kw)
        self.db.execute(f"INSERT INTO prestations ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))
        return self.un("SELECT id FROM prestations WHERE reference=?", ref)[0]

    def client(self, code="CLI-0001", **kw):
        cols = {"code": code, "nom": "Dupont"}
        cols.update(kw)
        self.db.execute(f"INSERT INTO clients ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))


class Migration(Base):
    def test_T26_migration_sur_base_vide(self):
        self.assertEqual(self.un("PRAGMA user_version")[0], 1)
        noms = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        self.assertEqual(noms, set(TABLES))
        for t in TABLES:                                   # aucune ligne insérée par la migration
            self.assertEqual(self.un(f"SELECT COUNT(*) FROM {t}")[0], 0, t)
        self.assertEqual({r[1] for r in self.db.execute("PRAGMA table_list") if not r[1].startswith("sqlite_") and r[5] == 1}, set(TABLES))
        self.assertEqual({r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}, TRIGGERS)
        self.assertEqual({r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")}, INDEXES)
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(self.db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])


class Invariants(Base):
    # INV-04 : id AUTOINCREMENT, jamais réutilisé
    def test_INV_04_id_jamais_reutilise(self):
        a = self.prestation("PLO-001")
        self.db.execute("DELETE FROM prestations WHERE id=?", (a,))
        b = self.prestation("PLO-002")
        self.assertGreater(b, a)
        for t in TABLES:
            sql = self.un("SELECT sql FROM sqlite_master WHERE name=?", t)[0]
            self.assertIn("AUTOINCREMENT", sql, t)

    # INV-05 : CASCADE uniquement prestation_garanties ; les autres FK en RESTRICT
    def test_INV_05_cascade_prestation_garanties_seulement(self):
        p = self.prestation("PLO-001")
        self.db.execute("INSERT INTO prestation_garanties (prestation_id, garantie_type) VALUES (?, 'decennale')", (p,))
        self.db.execute("INSERT INTO prestation_garanties (prestation_id, garantie_type) VALUES (?, 'biennale')", (p,))
        self.db.execute("DELETE FROM prestations WHERE id=?", (p,))
        self.assertEqual(self.un("SELECT COUNT(*) FROM prestation_garanties")[0], 0)
        q = self.prestation("PLO-002")                     # catégorie utilisée : suppression refusée
        cat = self.un("SELECT categorie_id FROM prestations WHERE id=?", q)[0]
        self.refuse("DELETE FROM categories_prestations WHERE id=?", cat)
        actions = {(r[2], r[6]) for t in TABLES for r in self.db.execute(f"PRAGMA foreign_key_list({t})")}
        self.assertEqual(actions, {("categories_prestations", "RESTRICT"), ("prestations", "CASCADE")})

    def test_INV_05_garantie_type_et_unicite(self):
        p = self.prestation("PLO-001")
        self.db.execute("INSERT INTO prestation_garanties (prestation_id, garantie_type) VALUES (?, 'parfait_achevement')", (p,))
        self.db.execute("INSERT INTO prestation_garanties (prestation_id, garantie_type) VALUES (?, 'decennale')", (p,))  # plusieurs types
        self.refuse("INSERT INTO prestation_garanties (prestation_id, garantie_type) VALUES (?, 'decennale')", p)        # doublon
        self.refuse("INSERT INTO prestation_garanties (prestation_id, garantie_type) VALUES (?, 'triennale')", p)        # hors liste
        self.refuse("INSERT INTO prestation_garanties (prestation_id, garantie_type) VALUES (999, 'decennale')")         # FK

    # INV-14 / INV-11 : prix en famille DL (TEXT canonique, précision libre, sans zéro de fin)
    def test_INV_14_prix_unitaire_famille_DL(self):
        valides = ["0", "10", "100", "3.333", "0.5", "12.75", "1000.05"]
        for i, v in enumerate(valides):
            self.prestation(f"OK-{i}", prix=v)
        invalides = ["", "1.0", "10.50", "0.50", "00", "01", ".5", "5.", "1.2.3", "-1", "1e3", "1,5", "abc", " 1"]
        for i, v in enumerate(invalides):
            with self.subTest(prix=v):
                self.refuse("INSERT INTO prestations (reference, designation, categorie_id, unite, type_prestation, prix_unitaire_ht, actif) "
                            "VALUES (?, 'D', ?, 'u', 'pose', ?, 1)", f"KO-{i}", self.categorie(f"K-{i}"), v)
        self.assertEqual(self.un("SELECT typeof(prix_unitaire_ht) FROM prestations WHERE reference='OK-3'")[0], "text")

    def test_INV_14_listes_fermees_prestation(self):
        for u in ("u", "ens", "ml", "m2", "m3"):
            self.prestation(f"U-{u}", unite=u)
        self.refuse("UPDATE prestations SET unite='h' WHERE reference='U-u'")
        self.refuse("UPDATE prestations SET unite='m²' WHERE reference='U-u'")
        for t in ("fourniture", "pose", "fourniture_pose"):
            self.prestation(f"T-{t}", type_prestation=t)
        self.refuse("UPDATE prestations SET type_prestation='service' WHERE reference='T-pose'")
        self.refuse("UPDATE prestations SET actif=2 WHERE reference='T-pose'")
        self.refuse("INSERT INTO prestations (reference, designation, categorie_id, unite, type_prestation, prix_unitaire_ht, actif) "
                    "VALUES ('', 'D', 1, 'u', 'pose', '1', 1)")

    # INV-20 / INV-27 : code client CLI-0001, sans exception d'origine
    def test_INV_20_code_client_sans_exception(self):
        self.client("CLI-0001")
        self.client("CLI-9999")
        self.client("CLI-0002", origine="import", legacy_id="c2", legacy_numero="CLI-002")
        for code in ("CLI-001", "CLI-00001", "cli-0003", "FOU-0001", "CLI-00A1", "CLI-0003-26", "", "0001"):
            with self.subTest(code=code):
                self.refuse("INSERT INTO clients (code, nom) VALUES (?, 'X')", code)
        self.refuse("INSERT INTO clients (code, nom, origine, legacy_id) VALUES ('CLI-001', 'X', 'import', 'x')")  # même import
        self.refuse("INSERT INTO clients (code, nom) VALUES ('CLI-0001', 'Autre')")                                # unicité

    def test_INV_20_client_statut_et_a_rattacher(self):
        self.client("CLI-0001", statut="archive")
        self.client("CLI-0002", statut="a_rattacher", origine="import", legacy_id="c")
        self.refuse("INSERT INTO clients (code, nom, statut) VALUES ('CLI-0003', 'X', 'a_rattacher')")   # v6 => interdit
        self.refuse("INSERT INTO clients (code, nom, statut) VALUES ('CLI-0003', 'X', 'supprime')")
        self.refuse("INSERT INTO clients (code, nom) VALUES ('CLI-0003', '')")
        self.assertEqual(self.un("SELECT statut FROM clients WHERE code='CLI-0003'"), None)
        self.client("CLI-0004")
        self.assertEqual(self.un("SELECT statut, origine FROM clients WHERE code='CLI-0004'"), ("actif", "v6"))

    # INV-136 : BLOC-IMP / BLOC-IMP+
    def test_INV_136_bloc_imp_clients(self):
        self.refuse("INSERT INTO clients (code, nom, legacy_id) VALUES ('CLI-0001', 'X', 'a')")
        self.refuse("INSERT INTO clients (code, nom, legacy_data) VALUES ('CLI-0001', 'X', '{}')")
        self.refuse("INSERT INTO clients (code, nom, legacy_numero) VALUES ('CLI-0001', 'X', 'CLI-001')")
        self.refuse("INSERT INTO clients (code, nom, origine) VALUES ('CLI-0001', 'X', 'migration')")
        self.refuse("INSERT INTO clients (code, nom, origine, legacy_data) VALUES ('CLI-0001', 'X', 'import', '{pas du json')")
        self.refuse("INSERT INTO clients (code, nom, origine, legacy_numero) VALUES ('CLI-0001', 'X', 'import', 'CLI-0001')")  # = code
        self.client("CLI-0001", origine="import", legacy_id="ref-1", legacy_data='{"ancien": true}', legacy_numero="CLI-001")
        self.client("CLI-0002", origine="import")      # legacy_* facultatifs en import

    def test_INV_136_bloc_imp_prestations(self):
        self.refuse("INSERT INTO prestations (reference, designation, categorie_id, unite, type_prestation, prix_unitaire_ht, actif, legacy_id) "
                    "VALUES ('A', 'D', 1, 'u', 'pose', '1', 1, 'x')")
        self.prestation("PLO-001", origine="import", legacy_id="p1", legacy_data='{"a": 1}')
        self.assertNotIn('legacy_numero', {r[1] for r in self.db.execute('PRAGMA table_info(prestations)')})   # BLOC-IMP sans legacy_numero
        for t in ("categories_prestations", "categories_depenses", "numerotation_sequences", "import_anomalies", "prestation_garanties"):
            cols = {r[1] for r in self.db.execute(f"PRAGMA table_info({t})")}
            self.assertFalse(cols & {"origine", "legacy_id", "legacy_data", "legacy_numero", "migration_id"}, t)

    # INV-21 / INV-22 : séquences
    def test_INV_21_une_sequence_par_type_et_annee(self):
        self.assertEqual(self.un(ATTRIBUER, "CLI", 0)[0], 1)
        self.assertEqual(self.un(ATTRIBUER, "CLI", 0)[0], 2)
        self.assertEqual(self.un(ATTRIBUER, "FAC", 26)[0], 1)   # situation et solde partagent FAC
        self.assertEqual(self.un(ATTRIBUER, "FAC", 26)[0], 2)
        self.assertEqual(self.un(ATTRIBUER, "ACP", 26)[0], 1)   # ACP et AVO séparés
        self.assertEqual(self.un(ATTRIBUER, "AVO", 26)[0], 1)
        self.assertEqual(self.un(ATTRIBUER, "FAC", 27)[0], 1)   # le compteur repart chaque année
        self.assertEqual(self.un("SELECT COUNT(*) FROM numerotation_sequences")[0], 5)
        self.refuse("INSERT INTO numerotation_sequences (type_objet, annee) VALUES ('FAC', 26)")   # UNIQUE
        for t in ("CLI", "FOU"):
            self.refuse("INSERT INTO numerotation_sequences (type_objet, annee) VALUES (?, 26)", t)   # annee=0 imposé
        for t in ("DEV", "BCD", "ACP", "FAC", "AVO", "PVR", "DEP"):
            self.refuse("INSERT INTO numerotation_sequences (type_objet, annee) VALUES (?, 0)", t)    # annee != 0 imposé
        self.refuse("INSERT INTO numerotation_sequences (type_objet, annee) VALUES ('XXX', 26)")
        self.refuse("INSERT INTO numerotation_sequences (type_objet, annee) VALUES ('DEV', 100)")
        self.refuse("INSERT INTO numerotation_sequences (type_objet, annee) VALUES ('DEV', -1)")
        self.db.execute("INSERT INTO numerotation_sequences (type_objet, annee) VALUES ('FOU', 0)")
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='FOU'")[0], 0)

    def test_INV_22_plafonds(self):
        self.db.execute("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('CLI', 0, 9998)")
        self.assertEqual(self.un(ATTRIBUER, "CLI", 0)[0], 9999)
        self.refuse(ATTRIBUER, "CLI", 0)                       # 10 000 refusé
        self.db.execute("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('DEV', 26, 99998)")
        self.assertEqual(self.un(ATTRIBUER, "DEV", 26)[0], 99999)
        self.refuse(ATTRIBUER, "DEV", 26)                      # 100 000 refusé
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='DEV'")[0], 99999)
        self.refuse("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('FAC', 26, -1)")

    def test_INV_22_dernier_numero_ne_diminue_jamais_TR95(self):
        self.un(ATTRIBUER, "FAC", 26)
        self.un(ATTRIBUER, "FAC", 26)
        self.refuse("UPDATE numerotation_sequences SET dernier_numero = 1 WHERE type_objet='FAC'")
        self.refuse("UPDATE numerotation_sequences SET dernier_numero = dernier_numero - 1")
        self.refuse("UPDATE numerotation_sequences SET dernier_numero = 0")
        self.db.execute("UPDATE numerotation_sequences SET dernier_numero = 2 WHERE type_objet='FAC'")    # égal : accepté
        self.db.execute("UPDATE numerotation_sequences SET dernier_numero = 40 WHERE type_objet='FAC'")   # relèvement (import, restauration)
        self.assertEqual(self.un(ATTRIBUER, "FAC", 26)[0], 41)                                            # trou accepté

    def test_INV_22_derniere_date(self):
        self.db.execute("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero, derniere_date) VALUES ('FAC', 26, 3, '2026-02-28')")
        self.refuse("UPDATE numerotation_sequences SET derniere_date='2026-02-30'")   # jour invalide
        self.refuse("UPDATE numerotation_sequences SET derniere_date='2026-00-15'")   # mois 00
        self.refuse("UPDATE numerotation_sequences SET derniere_date='2026-13-15'")   # mois 13
        self.refuse("UPDATE numerotation_sequences SET derniere_date='2026-01-00'")   # jour 00
        self.refuse("UPDATE numerotation_sequences SET derniere_date='28/02/2026'")
        self.db.execute("UPDATE numerotation_sequences SET derniere_date=NULL")

    # INV-130 / INV-165 / TR-90 : import_anomalies
    def anomalie(self, categorie="a_verifier", **kw):
        cols = {"type_entite": "facture", "ref_source": "f1", "categorie": categorie, "motif": "À contrôler"}
        if categorie == "a_verifier":
            cols["entite_id"] = 12
        else:
            cols["donnees"] = '{"champ": "valeur"}'
        cols.update(kw)
        self.db.execute(f"INSERT INTO import_anomalies ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))
        return self.un("SELECT MAX(id) FROM import_anomalies")[0]

    def test_INV_165_deux_categories_et_regles(self):
        self.anomalie("a_verifier")
        self.anomalie("non_importe")
        self.assertEqual(self.un("SELECT statut, traite_at FROM import_anomalies WHERE id=1"), ("a_traiter", None))
        self.refuse("INSERT INTO import_anomalies (type_entite, ref_source, categorie, motif) VALUES ('x', 'r', 'avertissement', 'm')")
        self.refuse("INSERT INTO import_anomalies (type_entite, ref_source, categorie, motif) VALUES ('facture', 'r', 'a_verifier', 'm')")  # entite_id requis
        self.refuse("INSERT INTO import_anomalies (type_entite, entite_id, ref_source, categorie, motif, donnees) VALUES ('facture', 1, 'r', 'non_importe', 'm', '{}')")
        self.refuse("INSERT INTO import_anomalies (type_entite, ref_source, categorie, motif) VALUES ('fournisseur', 'r', 'non_importe', 'm')")   # donnees requis
        self.refuse("INSERT INTO import_anomalies (type_entite, ref_source, categorie, motif, donnees) VALUES ('fournisseur', 'r', 'non_importe', 'm', 'pas du json')")
        for vide in ("type_entite", "ref_source", "motif"):                 # textes obligatoires non vides
            vals = {"type_entite": "t", "ref_source": "r", "motif": "m"}
            vals[vide] = ""
            self.refuse("INSERT INTO import_anomalies (type_entite, entite_id, ref_source, categorie, motif) VALUES (?, 1, ?, 'a_verifier', ?)",
                        vals["type_entite"], vals["ref_source"], vals["motif"])
        self.refuse("INSERT INTO import_anomalies (type_entite, entite_id, ref_source, categorie, motif, statut) VALUES ('t', 1, 'r', 'a_verifier', 'm', 'traite')")  # traite sans date
        self.refuse("INSERT INTO import_anomalies (type_entite, entite_id, ref_source, categorie, motif, traite_at) VALUES ('t', 1, 'r', 'a_verifier', 'm', ?)", TS)    # date sans statut

    def test_INV_130_TR90_import_anomalies_jamais_supprimee(self):
        a = self.anomalie("a_verifier")
        b = self.anomalie("non_importe")
        self.refuse("DELETE FROM import_anomalies WHERE id=?", a)
        self.refuse("DELETE FROM import_anomalies")
        self.assertEqual(self.un("SELECT COUNT(*) FROM import_anomalies")[0], 2)
        # seule la transition a_traiter -> traite (statut + traite_at) est permise, une seule fois
        self.refuse("UPDATE import_anomalies SET motif='autre' WHERE id=?", a)
        self.refuse("UPDATE import_anomalies SET donnees='{}' WHERE id=?", b)
        self.refuse("UPDATE import_anomalies SET entite_id=99 WHERE id=?", a)
        self.refuse("UPDATE import_anomalies SET statut='traite', traite_at=?, motif='autre' WHERE id=?", TS, a)
        self.refuse("UPDATE import_anomalies SET statut='a_traiter' WHERE id=?", a)                      # no-op refusé
        self.db.execute("UPDATE import_anomalies SET statut='traite', traite_at=? WHERE id=?", (TS, a))
        self.assertEqual(self.un("SELECT statut, traite_at FROM import_anomalies WHERE id=?", a), ("traite", TS))
        self.refuse("UPDATE import_anomalies SET traite_at='2026-10-02T00:00:00.000Z' WHERE id=?", a)    # une seule fois
        self.refuse("UPDATE import_anomalies SET statut='a_traiter', traite_at=NULL WHERE id=?", a)      # pas de retour
        self.refuse("DELETE FROM import_anomalies WHERE id=?", a)

    # Listes de référence
    def test_listes_de_reference(self):
        for t in ("categories_prestations", "categories_depenses"):
            self.db.execute(f"INSERT INTO {t} (code, libelle, actif) VALUES ('MAT', 'Matériaux', 1)")   # ordre facultatif
            self.refuse(f"INSERT INTO {t} (code, libelle, actif) VALUES ('MAT', 'Autre', 1)")           # code unique
            self.refuse(f"INSERT INTO {t} (code, libelle, actif) VALUES ('', 'X', 1)")
            self.refuse(f"INSERT INTO {t} (code, libelle, actif) VALUES ('Z', '', 1)")
            self.refuse(f"INSERT INTO {t} (code, libelle, actif) VALUES ('Z', 'X', 2)")
            self.refuse(f"INSERT INTO {t} (code, libelle) VALUES ('Z', 'X')")                           # actif explicite
            self.db.execute(f"UPDATE {t} SET actif=0, ordre=5 WHERE code='MAT'")                        # modifiable par l'utilisateur

    def test_horodatages_et_integrite(self):
        self.refuse("INSERT INTO clients (code, nom, created_at) VALUES ('CLI-0001', 'X', '2026-10-01')")
        self.refuse("INSERT INTO clients (code, nom, updated_at) VALUES ('CLI-0001', 'X', '2026-10-01T10:00:00Z')")
        self.client("CLI-0001", created_at=TS, updated_at=TS)
        self.prestation("PLO-001")
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(self.db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
