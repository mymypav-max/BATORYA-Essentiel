"""T-28 — DDL de la tranche Devis (modèle V3.10, §4.6 ; migration metier/003_devis.sql).
Tables : devis, devis_lignes, devis_ligne_garanties. Les migrations 001, 002 puis 003 sont appliquées
comme le fait le runner (une transaction par fichier, user_version posé après succès).

Exécution : python3 src-tauri/tests/metier/test_003_devis.py
Les méthodes portent le nom de l'invariant vérifié (test_INV_xx_…) ; les autres commencent par test_T28_.
Ces tests ne dépendent d'aucune interface graphique ni d'aucun service : l'attribution du numéro par le
service est reproduite avec la requête documentée (modèle §4.17 point 8). Le BC, le gel par TR-15 (factures,
règlements) et l'historique n'existent pas encore : le gel est posé ici par un UPDATE de frozen_at.
Renforcé (seconde passe V3.12, D-39) : la connexion de test active explicitement PRAGMA recursive_triggers=ON, un test vérifie que le réglage est actif, un test ciblé vérifie que INSERT OR REPLACE ne contourne pas les triggers de protection applicables.
"""
import pathlib
import re
import sqlite3
import unittest

MIGRATIONS = pathlib.Path(__file__).resolve().parents[2] / "migrations"
SQL_001 = (MIGRATIONS / "metier" / "001_initial.sql").read_text(encoding="utf-8")
SQL_002 = (MIGRATIONS / "metier" / "002_fournisseurs.sql").read_text(encoding="utf-8")
SQL_003 = (MIGRATIONS / "metier" / "003_devis.sql").read_text(encoding="utf-8")

TABLES_001 = {"import_anomalies", "numerotation_sequences", "categories_prestations", "categories_depenses",
              "clients", "prestations", "prestation_garanties"}
TABLES_002 = {"fournisseurs"}
TABLES_003 = {"devis", "devis_lignes", "devis_ligne_garanties"}
TRIGGERS_001 = {"tr_90_import_anomalies_no_delete", "tr_90_import_anomalies_update",
                "tr_95_numerotation_sequences_no_decrease"}
TRIGGERS_003 = {"tr_01_devis_numero_immuable", "tr_10_devis_modifiable", "tr_10_devis_refuse_annule",
                "tr_10_devis_gele", "tr_14_devis_frozen_at",
                "tr_11_devis_lignes_insert", "tr_11_devis_lignes_update", "tr_11_devis_lignes_delete",
                "tr_11_devis_ligne_garanties_insert", "tr_11_devis_ligne_garanties_update",
                "tr_11_devis_ligne_garanties_delete"}
INDEXES_001_002 = {"idx_clients_statut", "idx_prestations_categorie_id", "idx_prestations_actif",
                   "idx_import_anomalies_categorie_statut", "idx_fournisseurs_statut"}
INDEXES_003 = {"idx_devis_client_id", "idx_devis_statut", "idx_devis_date_creation", "idx_devis_lignes_prestation_id"}

COLONNES_DEVIS = ["id", "numero", "client_id", "client_snapshot", "client_snapshot_version", "entreprise_snapshot",
                  "entreprise_snapshot_version", "chantier_snapshot", "chantier_snapshot_version", "date_creation",
                  "date_validite", "date_acceptation", "date_refus", "objet", "notes", "statut", "remise_type",
                  "remise_valeur", "acompte_type", "acompte_valeur", "total_ht", "frozen_at", "cancelled_at",
                  "motif_refus", "motif_annulation", "created_at", "updated_at", "origine", "legacy_id", "legacy_data"]
COLONNES_LIGNES = ["id", "devis_id", "ordre", "prestation_id", "reference_prestation", "designation", "description",
                   "quantite", "unite", "prix_unitaire_ht", "remise_type", "remise_valeur", "type_prestation",
                   "total_ht", "created_at", "updated_at"]
COLONNES_GARANTIES = ["id", "ligne_id", "garantie_type", "created_at"]

TS = "2026-10-01T10:00:00.000Z"
TS2 = "2026-10-02T11:30:15.123Z"
SNAP = '{"nom": "Dupont"}'
ATTRIBUER = ("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES (?, ?, 1) "
             "ON CONFLICT (type_objet, annee) DO UPDATE SET dernier_numero = dernier_numero + 1, "
             "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') RETURNING dernier_numero")
TS_GLOB = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")


def migrer(recursive=True):
    """Applique 001, 002 puis 003 comme le runner : une transaction par fichier, user_version après succès.
    La connexion applique les réglages obligatoires (D-39) : foreign_keys=ON et recursive_triggers=ON."""
    db = sqlite3.connect(":memory:", isolation_level=None)
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA recursive_triggers=" + ("ON" if recursive else "OFF"))
    for numero, sql in ((1, SQL_001), (2, SQL_002), (3, SQL_003)):
        db.executescript("BEGIN;" + sql + "\nCOMMIT;")
        db.execute(f"PRAGMA user_version = {numero}")
    return db


class Base(unittest.TestCase):
    def setUp(self):
        self.db = migrer()
        self._n = 0

    # --- utilitaires d'assertion -------------------------------------------------
    def refuse(self, sql, *args):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(sql, args)

    def refuse_inv(self, inv, sql, *args):
        """Refus levé par un trigger : le message porte l'identifiant de l'invariant."""
        with self.assertRaisesRegex(sqlite3.IntegrityError, inv):
            self.db.execute(sql, args)

    def refuse_check(self, sql, *args):
        """Refus levé par une contrainte (CHECK, NOT NULL, UNIQUE, FK) et non par un trigger."""
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.db.execute(sql, args)
        self.assertNotIn("INV-", str(cm.exception))

    def un(self, sql, *args):
        return self.db.execute(sql, args).fetchone()

    def essai(self, sql, *args):
        """Retourne None si l'instruction réussit, sinon le message d'erreur."""
        try:
            self.db.execute(sql, args)
            return None
        except sqlite3.IntegrityError as e:
            return str(e)

    # --- fabrication de données --------------------------------------------------
    def client(self, code=None, statut="actif", **kw):
        self._n += 1
        code = code or f"CLI-{self._n:04d}"
        cols = {"code": code, "nom": "Dupont", "statut": statut}
        if statut == "a_rattacher":
            cols["origine"] = "import"
        cols.update(kw)
        self.db.execute(f"INSERT INTO clients ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))
        return self.un("SELECT id FROM clients WHERE code=?", code)[0]

    def prestation(self, ref="PLO-001", **kw):
        self.db.execute("INSERT INTO categories_prestations (code, libelle, actif, ordre) VALUES (?, 'Libellé', 1, 1)", (f"C-{ref}",))
        cat = self.un("SELECT id FROM categories_prestations WHERE code=?", f"C-{ref}")[0]
        cols = {"reference": ref, "designation": "Désignation", "categorie_id": cat, "unite": "u",
                "type_prestation": "pose", "prix_unitaire_ht": "10", "actif": 1}
        cols.update(kw)
        self.db.execute(f"INSERT INTO prestations ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))
        return self.un("SELECT id FROM prestations WHERE reference=?", ref)[0]

    def devis(self, numero=None, client_id=None, **kw):
        self._n += 1
        numero = numero or f"DEV-{self._n:05d}-26"
        cols = {"numero": numero, "client_id": client_id or self.client(), "client_snapshot": SNAP,
                "client_snapshot_version": 1, "entreprise_snapshot": SNAP, "entreprise_snapshot_version": 1,
                "chantier_snapshot": SNAP, "chantier_snapshot_version": 1, "date_creation": "2026-03-10",
                "statut": "en_attente", "total_ht": "0.00"}
        cols.update(kw)
        self.db.execute(f"INSERT INTO devis ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))
        return self.un("SELECT id FROM devis WHERE numero=?", numero)[0]

    def ligne(self, devis_id, ordre=1, **kw):
        cols = {"devis_id": devis_id, "ordre": ordre, "designation": "Pose prise", "quantite": "2", "unite": "u",
                "prix_unitaire_ht": "10.5", "remise_type": "aucune", "type_prestation": "pose", "total_ht": "21.00"}
        cols.update(kw)
        self.db.execute(f"INSERT INTO devis_lignes ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))
        return self.un("SELECT id FROM devis_lignes WHERE devis_id=? AND ordre=?", devis_id, ordre)[0]

    def garantie(self, ligne_id, type_="decennale"):
        self.db.execute("INSERT INTO devis_ligne_garanties (ligne_id, garantie_type) VALUES (?, ?)", (ligne_id, type_))
        return self.un("SELECT id FROM devis_ligne_garanties WHERE ligne_id=? AND garantie_type=?", ligne_id, type_)[0]

    # --- transitions d'état (UPDATE autorisés tant que le devis est modifiable) ----
    def accepter(self, d):
        self.db.execute("UPDATE devis SET statut='accepte', date_acceptation='2026-03-12' WHERE id=?", (d,))

    def geler(self, d):
        self.db.execute("UPDATE devis SET frozen_at=? WHERE id=?", (TS, d))

    def refuser(self, d):
        self.db.execute("UPDATE devis SET statut='refuse', date_refus='2026-03-12' WHERE id=?", (d,))

    def annuler(self, d):
        self.db.execute("UPDATE devis SET statut='annule', cancelled_at=?, motif_annulation='Client renonce' WHERE id=?", (TS, d))

    def mettre_en_etat(self, d, etat):
        if etat == "accepte":
            self.accepter(d)
        elif etat == "gele":
            self.accepter(d); self.geler(d)
        elif etat == "refuse":
            self.refuser(d)
        elif etat == "annule":
            self.annuler(d)
        elif etat == "annule_gele":
            self.accepter(d); self.geler(d); self.annuler(d)
        elif etat != "en_attente":
            raise ValueError(etat)

    def devis_complet(self, etat, **kw):
        """Devis avec une ligne et une garantie (créées tant qu'il est en attente), puis mis dans l'état voulu."""
        d = self.devis(**kw)
        l = self.ligne(d)
        g = self.garantie(l)
        self.mettre_en_etat(d, etat)
        return d, l, g


ETATS_MODIFIABLES = ("en_attente", "accepte")
ETATS_NON_MODIFIABLES = ("gele", "refuse", "annule", "annule_gele")


class Migration(Base):
    def test_T28_migration_sur_base_issue_de_001_et_002(self):
        self.assertEqual(self.un("PRAGMA user_version")[0], 3)
        noms = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        self.assertEqual(noms, TABLES_001 | TABLES_002 | TABLES_003)
        strict = {r[1] for r in self.db.execute("PRAGMA table_list") if r[5] == 1}
        self.assertTrue(TABLES_003 <= strict)
        self.assertEqual({r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")},
                         TRIGGERS_001 | TRIGGERS_003)
        self.assertEqual({r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")},
                         INDEXES_001_002 | INDEXES_003)
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(self.db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])

    def test_T28_colonnes_exactes(self):
        for table, attendu in (("devis", COLONNES_DEVIS), ("devis_lignes", COLONNES_LIGNES),
                               ("devis_ligne_garanties", COLONNES_GARANTIES)):
            self.assertEqual([r[1] for r in self.db.execute(f"PRAGMA table_info({table})")], attendu, table)
        infos = {r[1]: r for r in self.db.execute("PRAGMA table_info(devis)")}
        for c in ("numero", "client_id", "client_snapshot", "client_snapshot_version", "entreprise_snapshot",
                  "entreprise_snapshot_version", "chantier_snapshot", "chantier_snapshot_version", "date_creation",
                  "statut", "remise_type", "acompte_type", "total_ht", "created_at", "updated_at", "origine"):
            self.assertEqual(infos[c][3], 1, c)                              # NOT NULL
        for c in ("date_validite", "date_acceptation", "date_refus", "objet", "notes", "remise_valeur", "acompte_valeur",
                  "frozen_at", "cancelled_at", "motif_refus", "motif_annulation", "legacy_id", "legacy_data"):
            self.assertEqual(infos[c][3], 0, c)                              # nullable
        self.assertIsNone(infos["statut"][4])                               # statut : aucune valeur par défaut
        self.assertEqual(infos["remise_type"][4], "'aucune'")
        self.assertEqual(infos["acompte_type"][4], "'aucun'")
        self.assertEqual(infos["origine"][4], "'v6'")

    def test_T28_colonnes_obligatoires_lignes_et_garanties(self):
        attendu = {"devis_lignes": {"devis_id", "ordre", "designation", "quantite", "unite", "prix_unitaire_ht", "remise_type",
                                    "type_prestation", "total_ht", "created_at", "updated_at"},
                   "devis_ligne_garanties": {"ligne_id", "garantie_type", "created_at"}}
        for t, cols in attendu.items():
            obligatoires = {r[1] for r in self.db.execute(f"PRAGMA table_info({t})") if r[3] and not r[5]}
            self.assertEqual(obligatoires, cols, t)
        facultatives = {r[1] for r in self.db.execute("PRAGMA table_info(devis_lignes)") if not r[3]}
        self.assertEqual(facultatives, {"id", "prestation_id", "reference_prestation", "description", "remise_valeur"})

    def test_T28_cles_etrangeres(self):
        def fk(table):
            return {(r[2], r[3], r[4], r[6]) for r in self.db.execute(f"PRAGMA foreign_key_list({table})")}
        self.assertEqual(fk("devis"), {("clients", "client_id", "id", "RESTRICT")})
        self.assertEqual(fk("devis_lignes"), {("devis", "devis_id", "id", "CASCADE"),
                                              ("prestations", "prestation_id", "id", "RESTRICT")})
        self.assertEqual(fk("devis_ligne_garanties"), {("devis_lignes", "ligne_id", "id", "CASCADE")})
        # aucune FK vers une table absente (BC, factures…) : toutes les cibles existent déjà
        tables = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for t in TABLES_003:
            for r in self.db.execute(f"PRAGMA foreign_key_list({t})"):
                self.assertIn(r[2], tables)

    def test_T28_index(self):
        def colonnes(nom):
            return [r[2] for r in self.db.execute(f"PRAGMA index_info({nom})")]
        self.assertEqual(colonnes("idx_devis_client_id"), ["client_id"])
        self.assertEqual(colonnes("idx_devis_statut"), ["statut"])
        self.assertEqual(colonnes("idx_devis_date_creation"), ["date_creation"])
        self.assertEqual(colonnes("idx_devis_lignes_prestation_id"), ["prestation_id"])
        # les index UNIQUE couvrent devis_id/ordre et ligne_id/garantie_type (pas d'index séparé)
        uniques = {}
        for t in ("devis_lignes", "devis_ligne_garanties"):
            for r in self.db.execute(f"PRAGMA index_list({t})"):
                if r[2] == 1:
                    uniques[t] = [c[2] for c in self.db.execute(f"PRAGMA index_info({r[1]})")]
        self.assertEqual(uniques, {"devis_lignes": ["devis_id", "ordre"], "devis_ligne_garanties": ["ligne_id", "garantie_type"]})

    def test_T28_aucune_donnee_initiale(self):
        for t in TABLES_001 | TABLES_002 | TABLES_003:
            self.assertEqual(self.un(f"SELECT COUNT(*) FROM {t}")[0], 0, t)          # y compris numerotation_sequences
        sans_commentaires = re.sub(r"--[^\n]*", "", SQL_003)
        sans_commentaires = re.sub(r"(?i)\bON\s+(DELETE|UPDATE)\s+(RESTRICT|CASCADE)", "", sans_commentaires)   # actions de FK
        triggers = re.findall(r"CREATE TRIGGER.*?\nEND;", sans_commentaires, flags=re.S)
        self.assertEqual(len(triggers), len(TRIGGERS_003))
        hors_triggers = sans_commentaires
        for t in triggers:
            hors_triggers = hors_triggers.replace(t, "")
        self.assertNotRegex(hors_triggers, r"(?i)\b(INSERT|UPDATE|DELETE|DROP|ALTER|PRAGMA|BEGIN|COMMIT)\b|\bREPLACE\s+INTO\b")
        self.assertEqual(sorted(re.findall(r"(?i)\bCREATE\s+(\w+)", hors_triggers)), ["INDEX"] * 4 + ["TABLE"] * 3)

    def test_T28_triggers_ne_font_que_garder(self):
        sans_commentaires = re.sub(r"--[^\n]*", "", SQL_003)
        for t in re.findall(r"CREATE TRIGGER.*?\nEND;", sans_commentaires, flags=re.S):
            corps = t[t.index("BEGIN"):]
            self.assertRegex(corps, r"^BEGIN\s+SELECT RAISE\(ABORT, '[^']*(?:''[^']*)*'\);\s+END;$")
            self.assertRegex(corps, r"RAISE\(ABORT, 'INV-\d+: ")

    def test_T28_aucune_dependance_aux_tranches_suivantes(self):
        code = re.sub(r"'[^']*'", "''", re.sub(r"--[^\n]*", "", SQL_003))        # sans commentaires ni textes
        for absent in ("bons_commande", "bc_lignes", "bc_id", "factures", "facture_lignes", "reglements", "historique",
                       "documents", "depenses", "fournisseurs", "pv_reception"):
            with self.subTest(objet=absent):
                self.assertNotRegex(code, rf"\b{absent}\b")

    def test_T28_non_regression_001_002_inchangees(self):
        avant = sqlite3.connect(":memory:", isolation_level=None)
        for sql in (SQL_001, SQL_002):
            avant.executescript("BEGIN;" + sql + "\nCOMMIT;")
        def schema(db, noms):
            marques = ",".join("?" * len(noms))
            return db.execute(f"SELECT type, name, sql FROM sqlite_master WHERE name IN ({marques}) ORDER BY name", tuple(noms)).fetchall()
        anciens = [r[0] for r in avant.execute("SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")]
        self.assertEqual(schema(avant, anciens), schema(self.db, anciens))
        self.assertEqual(len(anciens), len(TABLES_001 | TABLES_002) + len(TRIGGERS_001) + len(INDEXES_001_002))


class Numerotation(Base):
    """INV-04, INV-20 à INV-23 : numéro DEV-00001-yy."""

    def test_INV_04_id_autoincrement_jamais_reutilise(self):
        for t in TABLES_003:
            self.assertIn("AUTOINCREMENT", self.un("SELECT sql FROM sqlite_master WHERE name=?", t)[0], t)
        d1 = self.devis()
        self.db.execute("DELETE FROM devis WHERE id=?", (d1,))
        self.assertGreater(self.devis(), d1)
        l1 = self.ligne(d1 + 1)
        self.db.execute("DELETE FROM devis_lignes WHERE id=?", (l1,))
        self.assertGreater(self.ligne(d1 + 1), l1)

    def test_INV_20_format_numero_v6(self):
        for i, (num, date) in enumerate([("DEV-00001-26", "2026-01-01"), ("DEV-99999-26", "2026-12-31"),
                                         ("DEV-00042-27", "2027-06-15"), ("DEV-00007-99", "2099-02-28")]):
            self.devis(num, date_creation=date)
        invalides = ["", "DEV-1-26", "DEV-0001-26", "DEV-000001-26", "DEV-00001-2026", "DEV-00001-6", "dev-00001-26",
                     "DEV00001-26", "DEV-00001-26-01", "FAC-00001-26", "BCD-00001-26", "DEP-00001-26", "DEV-0000A-26",
                     "DEV-00001-26 ", " DEV-00001-26", "DEV-+0001-26", "DEV-00001-2A", "CLI-0001"]
        for i, v in enumerate(invalides):
            with self.subTest(numero=v):
                self.refuse("INSERT INTO devis (numero, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                            "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, statut, total_ht) "
                            "VALUES (?, ?, ?, 1, ?, 1, ?, 1, '2026-03-10', 'en_attente', '0.00')",
                            v, self.client(), SNAP, SNAP, SNAP)
        self.refuse("INSERT INTO devis (client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                    "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, statut, total_ht) "
                    "VALUES (?, ?, 1, ?, 1, ?, 1, '2026-03-10', 'en_attente', '0.00')", self.client(), SNAP, SNAP, SNAP)  # numéro NN

    def test_INV_20_annee_du_numero_egale_annee_de_date_creation(self):
        self.devis("DEV-00001-26", date_creation="2026-03-10")
        for num, date in (("DEV-00002-27", "2026-03-10"), ("DEV-00003-26", "2027-03-10"), ("DEV-00004-25", "2026-12-31"),
                          ("DEV-00005-26", "2025-12-31")):
            with self.subTest(numero=num, date_creation=date):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.devis(num, date_creation=date)

    def test_INV_20_numero_unique(self):
        self.devis("DEV-00001-26")
        self.refuse_check("INSERT INTO devis (numero, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                          "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, statut, total_ht) "
                          "VALUES ('DEV-00001-26', ?, ?, 1, ?, 1, ?, 1, '2026-03-10', 'en_attente', '0.00')", self.client(), SNAP, SNAP, SNAP)
        self.devis("DEV-00001-27", date_creation="2027-01-05")        # même compteur, autre année : permis

    def test_INV_131_numero_historique_import_libre_mais_non_vide(self):
        for i, v in enumerate(["D-2023-045", "2023/12", "DEV-1", "00045", "DEV-00001-2023"]):
            self.devis(v, origine="import", legacy_id=f"ref-{i}")
        self.refuse_check("INSERT INTO devis (numero, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                          "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, statut, total_ht, origine) "
                          "VALUES ('', ?, ?, 1, ?, 1, ?, 1, '2026-03-10', 'en_attente', '0.00', 'import')", self.client(), SNAP, SNAP, SNAP)
        self.refuse_check("INSERT INTO devis (numero, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                          "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, statut, total_ht, origine) "
                          "VALUES ('D-2023-045', ?, ?, 1, ?, 1, ?, 1, '2026-03-10', 'en_attente', '0.00', 'import')", self.client(), SNAP, SNAP, SNAP)  # unique
        with self.assertRaises(sqlite3.IntegrityError):                # le même numéro en origine v6 est refusé
            self.devis("D-2023-046", origine="v6")

    def test_INV_23_numero_et_date_creation_immuables(self):
        for etat in ETATS_MODIFIABLES:
            with self.subTest(etat=etat):
                d = self.devis(date_creation="2026-03-10")
                self.mettre_en_etat(d, etat)
                self.refuse_inv("INV-23", "UPDATE devis SET numero='DEV-00099-26' WHERE id=?", d)
                self.refuse_inv("INV-23", "UPDATE devis SET date_creation='2026-03-11' WHERE id=?", d)   # même année : refusé aussi
                self.refuse_inv("INV-23", "UPDATE devis SET date_creation='2027-03-10' WHERE id=?", d)
                self.refuse_inv("INV-23", "UPDATE devis SET numero=numero||'x', date_creation='2026-03-11' WHERE id=?", d)
                self.db.execute("UPDATE devis SET numero=numero, date_creation=date_creation, objet='ok' WHERE id=?", (d,))  # valeurs identiques : permis
        d = self.devis("HIST-1", origine="import", legacy_id="r1")
        self.refuse_inv("INV-23", "UPDATE devis SET numero='HIST-2' WHERE id=?", d)                      # numéro historique immuable aussi

    def test_INV_21_sequence_DEV_par_annee(self):
        def creer(date):
            self.db.execute("BEGIN")
            try:
                n = self.un(ATTRIBUER, "DEV", int(date[2:4]))[0]
                self.devis(f"DEV-{n:05d}-{date[2:4]}", date_creation=date)
                self.db.execute("COMMIT")
            except Exception:
                self.db.execute("ROLLBACK")
                raise
            return f"DEV-{n:05d}-{date[2:4]}"
        self.assertEqual([creer("2026-01-05"), creer("2026-07-01"), creer("2027-01-02"), creer("2026-12-31")],
                         ["DEV-00001-26", "DEV-00002-26", "DEV-00001-27", "DEV-00003-26"])
        self.assertEqual(self.un("SELECT COUNT(*) FROM numerotation_sequences WHERE type_objet='DEV'")[0], 2)
        self.refuse(ATTRIBUER, "DEV", 0)                                # annee = 0 réservé à CLI / FOU
        self.assertEqual(self.un(ATTRIBUER, "FOU", 0)[0], 1)            # séquences indépendantes
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='DEV' AND annee=26")[0], 3)

    def test_INV_22_plafond_99999_et_numero_jamais_reutilise(self):
        self.db.execute("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('DEV', 26, 99998)")
        n = self.un(ATTRIBUER, "DEV", 26)[0]
        self.assertEqual(n, 99999)
        d = self.devis(f"DEV-{n:05d}-26")
        with self.assertRaises(sqlite3.IntegrityError):                 # dépassement : refusé (erreur métier côté service)
            self.un(ATTRIBUER, "DEV", 26)
        self.db.execute("DELETE FROM devis WHERE id=?", (d,))          # supprimer le devis ne libère pas le numéro
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='DEV'")[0], 99999)
        self.refuse("UPDATE numerotation_sequences SET dernier_numero = 5 WHERE type_objet='DEV'")       # TR-95 (001)


class ContraintesDevis(Base):
    def test_INV_30_snapshots_obligatoires_json_valides_et_versionnes(self):
        d = self.devis()
        for col in ("client", "entreprise", "chantier"):
            snap, ver = f"{col}_snapshot", f"{col}_snapshot_version"
            for invalide in ("", "pas du json", "{", None):
                with self.subTest(colonne=snap, valeur=invalide):
                    self.refuse(f"UPDATE devis SET {snap}=? WHERE id=?", invalide, d)
            self.refuse(f"UPDATE devis SET {ver}=NULL WHERE id=?", d)
            self.db.execute(f"UPDATE devis SET {snap}='{{}}', {ver}=2 WHERE id=?", (d,))
            self.db.execute(f"UPDATE devis SET {snap}='[1, 2]' WHERE id=?", (d,))                   # seule la validité JSON est contrôlée
        self.assertEqual(self.un("SELECT client_snapshot_version, entreprise_snapshot_version, chantier_snapshot_version "
                                 "FROM devis WHERE id=?", d), (2, 2, 2))

    def test_T28_statut_liste_fermee_et_sans_defaut(self):
        for i, s in enumerate(("en_attente",)):
            self.devis(statut=s)
        for s in ("", "ACCEPTE", "accepté", "archive", "a_rattacher", "termine", "expire", "en attente"):
            with self.subTest(statut=s):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.devis(statut=s, date_acceptation="2026-03-12", date_refus="2026-03-12")
        with self.assertRaises(sqlite3.IntegrityError):
            self.devis(statut=None)
        self.refuse_check("INSERT INTO devis (numero, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                          "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, total_ht) "
                          "VALUES ('DEV-00077-26', ?, ?, 1, ?, 1, ?, 1, '2026-03-10', '0.00')", self.client(), SNAP, SNAP, SNAP)

    def test_T28_coherence_statut_et_dates(self):
        a = self.devis(statut="accepte", date_acceptation="2026-03-12")
        self.devis(statut="refuse", date_refus="2026-03-12", motif_refus="Trop cher")
        self.devis(statut="annule", cancelled_at=TS, motif_annulation="Doublon")
        with self.assertRaises(sqlite3.IntegrityError):
            self.devis(statut="accepte")                                                # date_acceptation requise
        with self.assertRaises(sqlite3.IntegrityError):
            self.devis(statut="refuse")                                                 # date_refus requise
        with self.assertRaises(sqlite3.IntegrityError):
            self.devis(statut="annule", motif_annulation="x")                           # cancelled_at requis
        with self.assertRaises(sqlite3.IntegrityError):
            self.devis(statut="annule", cancelled_at=TS)                                # motif requis
        with self.assertRaises(sqlite3.IntegrityError):
            self.devis(statut="annule", cancelled_at=TS, motif_annulation="")           # motif non vide
        with self.assertRaises(sqlite3.IntegrityError):
            self.devis(statut="en_attente", cancelled_at=TS, motif_annulation="x")      # cancelled_at <=> annule
        with self.assertRaises(sqlite3.IntegrityError):
            self.devis(statut="accepte", date_acceptation="2026-03-12", cancelled_at=TS, motif_annulation="x")
        self.assertIsNotNone(a)

    def test_INV_10_dates_reelles(self):
        for col in ("date_creation", "date_validite", "date_acceptation", "date_refus"):
            for v in ("2026-02-30", "2026-13-01", "26-03-10", "2026/03/10", "2026-3-10", "2026-03-10T10:00:00Z", "", "hier"):
                with self.subTest(colonne=col, valeur=v):
                    with self.assertRaises(sqlite3.IntegrityError):
                        self.devis(**{col: v})
        self.devis("DEV-00001-24", date_creation="2024-02-29", date_validite="2024-03-29", date_acceptation="2024-03-01", date_refus="2024-03-02")
        with self.assertRaises(sqlite3.IntegrityError):
            self.devis(date_creation=None)

    def test_T28_date_validite_posterieure_ou_egale_a_creation(self):
        self.devis(date_creation="2026-03-10", date_validite="2026-03-10")
        self.devis(date_creation="2026-03-10", date_validite="2026-04-09")
        self.devis(date_creation="2026-03-10", date_validite=None)
        with self.assertRaises(sqlite3.IntegrityError):
            self.devis(date_creation="2026-03-10", date_validite="2026-03-09")

    def test_INV_14_total_ht_famille_D2(self):
        for v in ("0.00", "0.01", "1250.50", "99999999.99", "10.00"):
            self.devis(total_ht=v)
        for v in ("", "0", "10", "10.0", "10.5", "10.505", "-10.00", "-0.00", "01.00", "1,50", "abc", ".50", "10.", "1.2.30", " 1.00", "1e3", "1a.00", "1e1.00"):
            with self.subTest(total_ht=v):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.devis(total_ht=v)
        with self.assertRaises(sqlite3.IntegrityError):
            self.devis(total_ht=None)

    def test_INV_14_remise_globale(self):
        for t, v in (("aucune", None), ("pourcentage", "0.00"), ("pourcentage", "12.50"), ("pourcentage", "100.00"),
                     ("montant", "0.00"), ("montant", "250.75")):
            self.devis(remise_type=t, remise_valeur=v)
        invalides = [("aucune", "10.00"), ("pourcentage", None), ("montant", None), ("pourcentage", "100.01"),
                     ("pourcentage", "12.5"), ("pourcentage", "12"), ("pourcentage", "-1.00"), ("pourcentage", "abc"),
                     ("montant", "12.5"), ("montant", "12"), ("montant", "-5.00"), ("montant", "1.005"), ("montant", ""),
                     ("remise", "10.00"), ("autre", "10.00"), ("Montant", "10.00"), ("", None),
                     ("pourcentage", "1.2.30"), ("pourcentage", "01.00"), ("pourcentage", "1a.00"), ("pourcentage", "1e1.00"),
                     ("montant", "1.2.30"), ("montant", "01.00"), ("montant", "1a.00"), ("montant", "1e1.00")]
        for t, v in invalides:
            with self.subTest(remise_type=t, remise_valeur=v):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.devis(remise_type=t, remise_valeur=v)
        d = self.devis()
        self.assertEqual(self.un("SELECT remise_type, remise_valeur, acompte_type, acompte_valeur FROM devis WHERE id=?", d),
                         ("aucune", None, "aucun", None))

    def test_INV_14_acompte_prevu(self):
        for t, v in (("aucun", None), ("pourcentage", "30.00"), ("pourcentage", "100.00"), ("pourcentage", "0.00"),
                     ("montant", "200.00"), ("montant", "0.00")):
            self.devis(acompte_type=t, acompte_valeur=v)
        invalides = [("aucun", "10.00"), ("pourcentage", None), ("montant", None), ("pourcentage", "100.01"),
                     ("pourcentage", "30"), ("pourcentage", "30.5"), ("montant", "200"), ("montant", "200.5"),
                     ("montant", "-1.00"), ("aucune", None), ("remise", "10.00"), ("autre", "10.00"), ("Montant", "10.00"),
                     ("pourcentage", "1.2.30"), ("pourcentage", "01.00"), ("pourcentage", "1a.00"), ("pourcentage", "1e1.00"),
                     ("montant", "1.2.30"), ("montant", "01.00"), ("montant", "1a.00"), ("montant", "1e1.00")]
        for t, v in invalides:
            with self.subTest(acompte_type=t, acompte_valeur=v):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.devis(acompte_type=t, acompte_valeur=v)

    def test_INV_136_bloc_imp(self):
        d = self.devis()
        self.assertEqual(self.un("SELECT origine, legacy_id, legacy_data FROM devis WHERE id=?", d), ("v6", None, None))
        with self.assertRaises(sqlite3.IntegrityError):
            self.devis(origine="v6", legacy_id="x")
        with self.assertRaises(sqlite3.IntegrityError):
            self.devis(origine="v6", legacy_data="{}")
        with self.assertRaises(sqlite3.IntegrityError):
            self.devis(origine="migration", numero="H-1")
        with self.assertRaises(sqlite3.IntegrityError):
            self.devis(origine="import", numero="H-2", legacy_data="pas du json")
        self.devis(origine="import", numero="H-3")                                             # legacy_id facultatif
        self.devis(origine="import", numero="H-4", legacy_id="ref-4", legacy_data='{"statut_v2": "Envoyé"}')
        colonnes = {r[1] for r in self.db.execute("PRAGMA table_info(devis)")}
        self.assertFalse(colonnes & {"legacy_numero", "migration_id"})                         # legacy_numero : clients et BC seulement
        for t in ("devis_lignes", "devis_ligne_garanties"):                                    # pas de traçabilité sur les lignes
            self.assertFalse({r[1] for r in self.db.execute(f"PRAGMA table_info({t})")} & {"origine", "legacy_id", "legacy_data"})

    def test_INV_10_horodatages(self):
        d = self.devis()
        c, u = self.un("SELECT created_at, updated_at FROM devis WHERE id=?", d)
        self.assertRegex(c, TS_GLOB)
        self.assertRegex(u, TS_GLOB)
        for col in ("created_at", "updated_at", "frozen_at", "cancelled_at"):
            for v in ("2026-10-01", "2026-10-01 10:00:00", "2026-10-01T10:00:00Z", "2026-10-01T10:00:00.00Z", "now", ""):
                with self.subTest(colonne=col, valeur=v):
                    with self.assertRaises(sqlite3.IntegrityError):
                        self.devis(**{col: v, "statut": "annule" if col == "cancelled_at" else "accepte",
                                      "date_acceptation": "2026-03-12", "motif_annulation": "m"})
        self.devis(created_at=TS, updated_at=TS2)

    def test_T28_champs_facultatifs_texte_libre(self):
        d = self.devis(objet="Rénovation salle de bain", notes="Accès par le garage", motif_refus=None)
        self.assertEqual(self.un("SELECT objet, notes FROM devis WHERE id=?", d), ("Rénovation salle de bain", "Accès par le garage"))
        self.devis(objet=None, notes=None)
        self.devis(objet="", notes="")


class ContraintesLignes(Base):
    def test_T28_ligne_nominale_catalogue_et_ligne_libre(self):
        d = self.devis()
        p = self.prestation("PLO-001")
        l1 = self.ligne(d, 1, prestation_id=p, reference_prestation="PLO-001")
        l2 = self.ligne(d, 2, prestation_id=None, reference_prestation=None, designation="Saisie libre")      # ligne libre
        l3 = self.ligne(d, 3, prestation_id=None, reference_prestation="ELE-008", designation="Prise RJ45 Cat6")  # INV-166 : snapshot
        self.assertEqual(self.un("SELECT prestation_id FROM devis_lignes WHERE id=?", l2)[0], None)
        self.assertEqual(self.un("SELECT reference_prestation, prestation_id FROM devis_lignes WHERE id=?", l3), ("ELE-008", None))
        self.assertEqual(self.un("SELECT COUNT(*) FROM devis_lignes WHERE devis_id=?", d)[0], 3)
        self.assertEqual(self.un("SELECT created_at FROM devis_lignes WHERE id=?", l1)[0][-1], "Z")

    def test_T28_ordre_et_unicite(self):
        d = self.devis()
        self.ligne(d, 1)
        self.ligne(d, 2)
        for v in (0, -1, None):
            with self.subTest(ordre=v):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.ligne(d, v)
        with self.assertRaises(sqlite3.IntegrityError):
            self.ligne(d, 1)                                                            # UNIQUE(devis_id, ordre)
        d2 = self.devis()
        self.ligne(d2, 1)                                                              # même ordre dans un autre devis : permis

    def test_T28_designation_obligatoire_non_vide(self):
        d = self.devis()
        for v in ("", None):
            with self.subTest(designation=v):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.ligne(d, 1, designation=v)

    def test_INV_14_quantite_DL_strictement_positive(self):
        d = self.devis()
        for i, v in enumerate(("1", "2", "0.5", "3.333", "12.75", "1000", "0.001")):
            self.ligne(d, i + 1, quantite=v)
        for i, v in enumerate(("0", "", "0.0", "1.0", "01", ".5", "5.", "1.2.3", "-1", "1e3", "1,5", "abc", " 1", None)):
            with self.subTest(quantite=v):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.ligne(d, 100 + i, quantite=v)

    def test_INV_14_prix_unitaire_DL(self):
        d = self.devis()
        for i, v in enumerate(("0", "10", "3.333", "0.5", "12.75", "1000.05")):
            self.ligne(d, i + 1, prix_unitaire_ht=v)
        for i, v in enumerate(("", "1.0", "10.50", "00", "01", ".5", "5.", "1.2.3", "-1", "1e3", "1,5", "abc", None)):
            with self.subTest(prix=v):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.ligne(d, 100 + i, prix_unitaire_ht=v)

    def test_INV_14_total_ht_ligne_D2(self):
        d = self.devis()
        for i, v in enumerate(("0.00", "21.00", "33.33", "25.01")):
            self.ligne(d, i + 1, total_ht=v)
        for i, v in enumerate(("", "0", "21", "21.5", "21.505", "-21.00", "01.00", "abc", "1a.00", "1e1.00", "1.2.30", None)):
            with self.subTest(total_ht=v):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.ligne(d, 100 + i, total_ht=v)

    def test_INV_14_remise_de_ligne(self):
        d = self.devis()
        valides = [("aucune", None), ("pourcentage", "10.00"), ("pourcentage", "100.00"), ("pourcentage", "0.00"),
                   ("montant", "5"), ("montant", "12.5"), ("montant", "12.75"), ("montant", "0"), ("montant", "3.333")]
        for i, (t, v) in enumerate(valides):
            self.ligne(d, i + 1, remise_type=t, remise_valeur=v)
        invalides = [("aucune", "5"), ("pourcentage", None), ("montant", None), ("pourcentage", "100.01"), ("pourcentage", "10"),
                     ("pourcentage", "10.5"), ("pourcentage", "-5.00"), ("montant", "12.50"), ("montant", "-5"), ("montant", ""),
                     ("montant", "01"), ("montant", "abc"), ("pourcent", "10.00"), ("autre", "10.00"), ("autre", "5"), (None, None),
                     ("pourcentage", "1.2.30"), ("pourcentage", "01.00"), ("pourcentage", "1a.00"), ("pourcentage", "1e1.00"),
                     ("montant", "1.2.3"), ("montant", ".5"), ("montant", "5."), ("montant", "1e1"), ("montant", "1a"), ("montant", "1,5")]
        for i, (t, v) in enumerate(invalides):
            with self.subTest(remise_type=t, remise_valeur=v):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.ligne(d, 100 + i, remise_type=t, remise_valeur=v)
        self.refuse_check("INSERT INTO devis_lignes (devis_id, ordre, designation, quantite, unite, prix_unitaire_ht, type_prestation, total_ht) "
                          "VALUES (?, 200, 'D', '1', 'u', '1', 'pose', '1.00')", d)                 # remise_type : pas de défaut

    def test_T28_listes_fermees_ligne(self):
        d = self.devis()
        for i, u in enumerate(("u", "ens", "ml", "m2", "m3")):
            self.ligne(d, i + 1, unite=u)
        for i, t in enumerate(("fourniture", "pose", "fourniture_pose")):
            self.ligne(d, 10 + i, type_prestation=t)
        for i, u in enumerate(("m", "kg", "U", "", "m²", None)):
            with self.subTest(unite=u):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.ligne(d, 100 + i, unite=u)
        for i, t in enumerate(("libre", "service", "Pose", "", None)):
            with self.subTest(type_prestation=t):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.ligne(d, 200 + i, type_prestation=t)

    def test_INV_10_horodatages_ligne(self):
        d = self.devis()
        l = self.ligne(d)
        c, u = self.un("SELECT created_at, updated_at FROM devis_lignes WHERE id=?", l)
        self.assertRegex(c, TS_GLOB)
        self.assertRegex(u, TS_GLOB)
        for col in ("created_at", "updated_at"):
            for i, v in enumerate(("2026-10-01", "2026-10-01T10:00:00Z", "now", "")):
                with self.subTest(colonne=col, valeur=v):
                    with self.assertRaises(sqlite3.IntegrityError):
                        self.ligne(d, 100 + i, **{col: v})

    def test_T28_garanties_de_ligne(self):
        d = self.devis()
        l = self.ligne(d)
        for t in ("parfait_achevement", "biennale", "decennale"):
            self.garantie(l, t)
        self.refuse_check("INSERT INTO devis_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'decennale')", l)       # UNIQUE
        for t in ("triennale", "", "Decennale", None):
            with self.subTest(garantie_type=t):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.garantie(l, t)
        self.refuse_check("INSERT INTO devis_ligne_garanties (ligne_id, garantie_type) VALUES (999, 'decennale')")         # FK
        self.assertRegex(self.un("SELECT created_at FROM devis_ligne_garanties LIMIT 1")[0], TS_GLOB)
        self.refuse_check("INSERT INTO devis_ligne_garanties (ligne_id, garantie_type, created_at) VALUES (?, 'biennale', 'x')", self.ligne(d, 2))
        l2 = self.ligne(d, 3)
        self.garantie(l2, "decennale")                                                 # même type sur une autre ligne : permis


class Schema(Base):
    def test_T28_horodatages_par_defaut_sont_l_instant_courant(self):
        d = self.devis()
        l = self.ligne(d)
        g = self.garantie(l)
        for table, id_, cols in (("devis", d, ("created_at", "updated_at")), ("devis_lignes", l, ("created_at", "updated_at")),
                                 ("devis_ligne_garanties", g, ("created_at",))):
            for col in cols:
                with self.subTest(table=table, colonne=col):
                    ecart = self.un(f"SELECT abs(julianday({col}) - julianday('now')) FROM {table} WHERE id=?", id_)[0]
                    self.assertLess(ecart, 1.0 / 1440)                                           # moins d'une minute

    def test_T28_listes_fermees_exactes(self):
        attendu = {("devis", "statut"): {"en_attente", "accepte", "refuse", "annule"},
                   ("devis", "remise_type"): {"aucune", "pourcentage", "montant"},
                   ("devis", "acompte_type"): {"aucun", "pourcentage", "montant"},
                   ("devis", "origine"): {"v6", "import"},
                   ("devis_lignes", "remise_type"): {"aucune", "pourcentage", "montant"},
                   ("devis_lignes", "unite"): {"u", "ens", "ml", "m2", "m3"},
                   ("devis_lignes", "type_prestation"): {"fourniture", "pose", "fourniture_pose"},
                   ("devis_ligne_garanties", "garantie_type"): {"parfait_achevement", "biennale", "decennale"}}
        for (table, col), valeurs in attendu.items():
            sql = self.un("SELECT sql FROM sqlite_master WHERE name=?", table)[0]
            m = re.search(rf"\b{col} IN \(([^)]*)\)", sql)
            self.assertIsNotNone(m, (table, col))
            self.assertEqual(set(re.findall(r"'([^']*)'", m.group(1))), valeurs, (table, col))


class CleEtrangeres(Base):
    def test_INV_06_client_et_prestation_utilises_ne_se_suppriment_pas(self):
        c = self.client()
        p = self.prestation("PLO-001")
        d = self.devis(client_id=c)
        l = self.ligne(d, 1, prestation_id=p)
        self.refuse_check("DELETE FROM clients WHERE id=?", c)
        self.refuse_check("DELETE FROM prestations WHERE id=?", p)
        self.refuse_check("UPDATE devis SET client_id=999 WHERE id=?", d)
        self.refuse_check("INSERT INTO devis (numero, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                          "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, statut, total_ht) "
                          "VALUES ('DEV-00088-26', 999, ?, 1, ?, 1, ?, 1, '2026-03-10', 'en_attente', '0.00')", SNAP, SNAP, SNAP)
        self.refuse_check("INSERT INTO devis (numero, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                          "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, statut, total_ht) "
                          "VALUES ('DEV-00089-26', NULL, ?, 1, ?, 1, ?, 1, '2026-03-10', 'en_attente', '0.00')", SNAP, SNAP, SNAP)   # client obligatoire
        self.refuse_check("INSERT INTO devis_lignes (devis_id, ordre, prestation_id, designation, quantite, unite, prix_unitaire_ht, "
                          "remise_type, type_prestation, total_ht) VALUES (?, 2, 999, 'D', '1', 'u', '1', 'aucune', 'pose', '1.00')", d)
        self.refuse_check("INSERT INTO devis_lignes (devis_id, ordre, designation, quantite, unite, prix_unitaire_ht, "
                          "remise_type, type_prestation, total_ht) VALUES (999, 1, 'D', '1', 'u', '1', 'aucune', 'pose', '1.00')")
        self.db.execute("DELETE FROM devis_lignes WHERE id=?", (l,))
        self.refuse_check("DELETE FROM clients WHERE id=?", c)                              # le devis référence toujours le client
        self.db.execute("DELETE FROM prestations WHERE id=?", (p,))                         # plus aucune ligne : permis
        self.db.execute("DELETE FROM devis WHERE id=?", (d,))
        self.db.execute("DELETE FROM clients WHERE id=?", (c,))                             # plus aucun devis : permis

    def test_INV_05_cascade_devis_lignes_garanties_seulement(self):
        d, l, g = self.devis_complet("en_attente")
        self.ligne(d, 2)
        self.db.execute("DELETE FROM devis WHERE id=?", (d,))
        for t in ("devis_lignes", "devis_ligne_garanties"):
            self.assertEqual(self.un(f"SELECT COUNT(*) FROM {t}")[0], 0, t)
        d2, l2, g2 = self.devis_complet("en_attente")
        self.db.execute("DELETE FROM devis_lignes WHERE id=?", (l2,))
        self.assertEqual(self.un("SELECT COUNT(*) FROM devis_ligne_garanties")[0], 0)
        self.assertEqual(self.un("SELECT COUNT(*) FROM devis WHERE id=?", d2)[0], 1)
        actions = {(r[2], r[6]) for t in TABLES_003 for r in self.db.execute(f"PRAGMA foreign_key_list({t})")}
        self.assertEqual(actions, {("clients", "RESTRICT"), ("devis", "CASCADE"), ("prestations", "RESTRICT"), ("devis_lignes", "CASCADE")})

    def test_INV_06_suppression_d_un_devis_sans_garde_dans_cette_tranche(self):
        """Décision consignée dans l'en-tête de 003 : aucun trigger DELETE sur devis ; la garde « devis avec BC »
        est la FK RESTRICT de bons_commande.devis_id (tranche BC). À reconsidérer avec la tranche BC."""
        triggers_devis = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='devis'")}
        self.assertFalse(any("delete" in n for n in triggers_devis))
        for etat in ("en_attente", "accepte", "refuse", "annule"):
            with self.subTest(etat=etat):
                d, l, g = self.devis_complet(etat)
                self.db.execute("DELETE FROM devis WHERE id=?", (d,))
                self.assertEqual(self.un("SELECT COUNT(*) FROM devis_lignes WHERE devis_id=?", d)[0], 0)

    def test_INV_37_le_catalogue_ne_modifie_jamais_une_ligne(self):
        p = self.prestation("PLO-001", designation="Pose prise", prix_unitaire_ht="10.5", unite="u", type_prestation="pose")
        self.db.execute("INSERT INTO prestation_garanties (prestation_id, garantie_type) VALUES (?, 'decennale')", (p,))
        d = self.devis()
        l = self.ligne(d, 1, prestation_id=p, reference_prestation="PLO-001", designation="Pose prise", prix_unitaire_ht="10.5",
                       unite="u", type_prestation="pose")
        self.garantie(l, "decennale")
        avant = self.un("SELECT * FROM devis_lignes WHERE id=?", l)
        garanties_avant = self.db.execute("SELECT * FROM devis_ligne_garanties").fetchall()
        self.db.execute("UPDATE prestations SET reference='PLO-999', designation='Autre', prix_unitaire_ht='99.99', unite='ml', "
                        "type_prestation='fourniture', actif=0, description='x', updated_at=? WHERE id=?", (TS2, p))
        self.db.execute("DELETE FROM prestation_garanties WHERE prestation_id=?", (p,))
        self.db.execute("INSERT INTO prestation_garanties (prestation_id, garantie_type) VALUES (?, 'biennale')", (p,))
        self.assertEqual(self.un("SELECT * FROM devis_lignes WHERE id=?", l), avant)
        self.assertEqual(self.db.execute("SELECT * FROM devis_ligne_garanties").fetchall(), garanties_avant)
        self.refuse_check("DELETE FROM prestations WHERE id=?", p)                           # prestation utilisée : jamais supprimée


# Autre valeur pour chaque colonne de devis, utilisée pour vérifier que TR-10 couvre TOUTES les colonnes.
def autre_valeur(col, ancienne, autre_client):
    valeurs = {"id": 99999, "numero": "DEV-00099-26", "client_id": autre_client, "client_snapshot": '{"autre": 1}',
               "client_snapshot_version": 7, "entreprise_snapshot": '{"autre": 1}', "entreprise_snapshot_version": 7,
               "chantier_snapshot": '{"autre": 1}', "chantier_snapshot_version": 7, "date_creation": "2026-03-11",
               "date_validite": "2026-12-31", "date_acceptation": "2026-03-20", "date_refus": "2026-03-21", "objet": "Autre objet",
               "notes": "Autres notes", "statut": "en_attente", "remise_type": "pourcentage", "remise_valeur": "10.00",
               "acompte_type": "pourcentage", "acompte_valeur": "30.00", "total_ht": "999.99", "frozen_at": TS2,
               "cancelled_at": TS2, "motif_refus": "Autre", "motif_annulation": "Autre motif", "created_at": "2026-01-01T00:00:00.000Z",
               "updated_at": TS2, "origine": "import", "legacy_id": "autre", "legacy_data": '{"autre": 1}'}
    v = valeurs[col]
    return v if v != ancienne else (None if ancienne is not None else "x")


class Triggers(Base):
    def _preparer(self, etat, client_rattachable=False):
        """Retourne (devis_id, client_cible_id) ; le devis est dans l'état voulu."""
        ancien = self.client(statut="a_rattacher") if client_rattachable else self.client()
        cible = self.client()
        d = self.devis(client_id=ancien, objet="o", notes="n", date_validite="2026-12-31", motif_refus=None)
        self.mettre_en_etat(d, etat)
        return d, cible

    def test_T28_TR10_toutes_les_colonnes_sont_couvertes(self):
        self.assertEqual([r[1] for r in self.db.execute("PRAGMA table_info(devis)")], COLONNES_DEVIS)
        d, cible = self._preparer("refuse")
        ligne = self.un("SELECT * FROM devis WHERE id=?", d)
        for col, ancienne in zip(COLONNES_DEVIS, ligne):
            autre_valeur(col, ancienne, cible)        # lève KeyError si une colonne n'a pas de valeur de test

    def test_INV_31_devis_modifiable_en_attente_et_accepte_non_gele(self):
        for etat in ETATS_MODIFIABLES:
            with self.subTest(etat=etat):
                d, cible = self._preparer(etat)
                self.db.execute("UPDATE devis SET objet='Nouvel objet', notes='Nouvelles notes', date_validite='2027-01-31', "
                                "client_snapshot='{\"x\": 1}', client_snapshot_version=2, entreprise_snapshot='{\"x\": 2}', "
                                "chantier_snapshot='{\"x\": 3}', remise_type='pourcentage', remise_valeur='10.00', "
                                "acompte_type='montant', acompte_valeur='100.00', total_ht='450.00', motif_refus='Prix', "
                                "origine='import', legacy_id='r', legacy_data='{}', updated_at=? WHERE id=?", (TS2, d))
                self.db.execute("UPDATE devis SET client_id=? WHERE id=?", (cible, d))                  # client librement modifiable
                self.refuse_inv("INV-31", "UPDATE devis SET id=id+1000 WHERE id=?", d)
                self.refuse_inv("INV-31", "UPDATE devis SET created_at=? WHERE id=?", TS2, d)

    def test_INV_31_transitions_depuis_en_attente(self):
        d, _ = self._preparer("en_attente")
        self.accepter(d)
        self.assertEqual(self.un("SELECT statut FROM devis WHERE id=?", d)[0], "accepte")
        d2, _ = self._preparer("en_attente")
        self.refuser(d2)
        self.assertEqual(self.un("SELECT statut FROM devis WHERE id=?", d2)[0], "refuse")
        d3, _ = self._preparer("en_attente")
        self.annuler(d3)
        self.assertEqual(self.un("SELECT statut FROM devis WHERE id=?", d3)[0], "annule")
        d4, _ = self._preparer("accepte")
        self.annuler(d4)                                                                              # accepte non gelé -> annule
        self.assertEqual(self.un("SELECT statut, frozen_at FROM devis WHERE id=?", d4), ("annule", None))

    def test_INV_31_devis_refuse_ou_annule_immuable_colonne_par_colonne(self):
        autorisees = {"client_id", "updated_at"}
        for etat in ("refuse", "annule"):
            d, cible = self._preparer(etat)
            ligne = self.un("SELECT * FROM devis WHERE id=?", d)
            for col, ancienne in zip(COLONNES_DEVIS, ligne):
                if col in autorisees:
                    continue
                with self.subTest(etat=etat, colonne=col):
                    self.refuse_inv("INV-23|INV-31|INV-34", f"UPDATE devis SET {col}=? WHERE id=?", autre_valeur(col, ancienne, cible), d)
            self.assertEqual(self.un("SELECT * FROM devis WHERE id=?", d), ligne)                    # rien n'a bougé
            self.refuse_inv("INV-31", "UPDATE devis SET objet='x', total_ht='1.00' WHERE id=?", d)
            self.refuse_inv("INV-31", "UPDATE devis SET statut=statut, objet='y' WHERE id=?", d)

    def test_INV_36_devis_gele_colonne_par_colonne(self):
        autorisees = {"statut", "cancelled_at", "motif_annulation", "client_id", "updated_at"}
        d, cible = self._preparer("gele")
        ligne = self.un("SELECT * FROM devis WHERE id=?", d)
        for col, ancienne in zip(COLONNES_DEVIS, ligne):
            if col in autorisees:
                continue
            with self.subTest(colonne=col):
                self.refuse_inv("INV-23|INV-34|INV-36", f"UPDATE devis SET {col}=? WHERE id=?", autre_valeur(col, ancienne, cible), d)
        self.assertEqual(self.un("SELECT * FROM devis WHERE id=?", d), ligne)
        self.db.execute("UPDATE devis SET updated_at=? WHERE id=?", (TS2, d))                           # colonnes autorisées
        self.db.execute("UPDATE devis SET statut='annule', cancelled_at=?, motif_annulation='Annulation du BC' WHERE id=?", (TS2, d))
        self.assertEqual(self.un("SELECT statut, frozen_at IS NOT NULL FROM devis WHERE id=?", d), ("annule", 1))

    def test_INV_36_devis_gele_ne_peut_etre_ni_refuse_ni_remis_en_attente(self):
        d, _ = self._preparer("gele")
        self.refuse_inv("INV-36", "UPDATE devis SET statut='refuse', date_refus='2026-04-01' WHERE id=?", d)   # date_refus non modifiable
        self.refuse_check("UPDATE devis SET statut='refuse' WHERE id=?", d)                                  # CHECK : date_refus requise
        self.refuse_check("UPDATE devis SET statut='en_attente' WHERE id=?", d)                              # CHECK : frozen_at => accepte|annule

    def test_INV_49_rattachement_client_sur_devis_non_modifiable(self):
        for etat in ETATS_NON_MODIFIABLES:
            with self.subTest(etat=etat):
                d, cible = self._preparer(etat, client_rattachable=True)
                avant = self.un("SELECT * FROM devis WHERE id=?", d)
                self.db.execute("UPDATE devis SET client_id=?, updated_at=? WHERE id=?", (cible, TS2, d))   # rattachement permis
                apres = self.un("SELECT * FROM devis WHERE id=?", d)
                changees = [c for c, a, b in zip(COLONNES_DEVIS, avant, apres) if a != b]
                self.assertEqual(sorted(changees), ["client_id", "updated_at"])                              # et rien d'autre (snapshots intacts)
                self.refuse_inv("INV-3[16]", "UPDATE devis SET client_id=?, objet='autre' WHERE id=?", self.client(), d)  # pas de modification mêlée
        for etat in ETATS_NON_MODIFIABLES:
            with self.subTest(etat=etat, client="actif"):
                d, cible = self._preparer(etat, client_rattachable=False)
                self.refuse_inv("INV-3[16]", "UPDATE devis SET client_id=? WHERE id=?", cible, d)            # client non 'a_rattacher' : refusé
        d, _ = self._preparer("accepte", client_rattachable=False)
        self.db.execute("UPDATE devis SET client_id=? WHERE id=?", (self.client(), d))                  # devis modifiable : libre

    def test_INV_34_frozen_at_ne_revient_jamais_a_null(self):
        d, _ = self._preparer("accepte")
        self.db.execute("UPDATE devis SET frozen_at=? WHERE id=?", (TS, d))                              # NULL -> valeur (pose du gel)
        self.refuse_inv("INV-3[46]", "UPDATE devis SET frozen_at=NULL WHERE id=?", d)
        self.refuse_inv("INV-3[46]", "UPDATE devis SET frozen_at=? WHERE id=?", TS2, d)
        self.assertEqual(self.un("SELECT frozen_at FROM devis WHERE id=?", d)[0], TS)
        d2, _ = self._preparer("annule_gele")
        self.refuse_inv("INV-3[146]", "UPDATE devis SET frozen_at=NULL WHERE id=?", d2)                 # annulation : le gel n'est pas levé
        self.assertIsNotNone(self.un("SELECT frozen_at FROM devis WHERE id=?", d2)[0])
        d3, _ = self._preparer("en_attente")
        self.refuse_check("UPDATE devis SET frozen_at=? WHERE id=?", TS, d3)                             # gel seulement accepte|annule
        d4, _ = self._preparer("refuse")
        self.refuse("UPDATE devis SET frozen_at=? WHERE id=?", TS, d4)

    def test_INV_36_lignes_et_garanties_modifiables_si_devis_modifiable(self):
        for etat in ETATS_MODIFIABLES:
            with self.subTest(etat=etat):
                d, l, g = self.devis_complet(etat)
                l2 = self.ligne(d, 2)
                self.garantie(l2, "biennale")
                self.db.execute("UPDATE devis_lignes SET designation='Modifiée', quantite='3', total_ht='31.50', updated_at=? WHERE id=?", (TS2, l))
                self.db.execute("UPDATE devis_lignes SET ordre=3 WHERE id=?", (l2,))
                self.db.execute("UPDATE devis_ligne_garanties SET garantie_type='parfait_achevement' WHERE id=?", (g,))
                self.db.execute("DELETE FROM devis_ligne_garanties WHERE id=?", (g,))
                self.db.execute("DELETE FROM devis_lignes WHERE id=?", (l2,))
                self.assertEqual(self.un("SELECT COUNT(*) FROM devis_lignes WHERE devis_id=?", d)[0], 1)

    def test_INV_36_lignes_et_garanties_interdites_si_devis_non_modifiable(self):
        for etat in ETATS_NON_MODIFIABLES:
            with self.subTest(etat=etat):
                d, l, g = self.devis_complet(etat)
                self.refuse_inv("INV-36", "INSERT INTO devis_lignes (devis_id, ordre, designation, quantite, unite, prix_unitaire_ht, "
                                          "remise_type, type_prestation, total_ht) VALUES (?, 2, 'D', '1', 'u', '1', 'aucune', 'pose', '1.00')", d)
                self.refuse_inv("INV-36", "UPDATE devis_lignes SET designation='Modifiée' WHERE id=?", l)
                self.refuse_inv("INV-36", "UPDATE devis_lignes SET updated_at=? WHERE id=?", TS2, l)
                self.refuse_inv("INV-36", "DELETE FROM devis_lignes WHERE id=?", l)
                self.refuse_inv("INV-36", "INSERT INTO devis_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'biennale')", l)
                self.refuse_inv("INV-36", "UPDATE devis_ligne_garanties SET garantie_type='biennale' WHERE id=?", g)
                self.refuse_inv("INV-36", "DELETE FROM devis_ligne_garanties WHERE id=?", g)
                self.assertEqual(self.un("SELECT COUNT(*) FROM devis_lignes WHERE id=?", l)[0], 1)
                self.assertEqual(self.un("SELECT COUNT(*) FROM devis_ligne_garanties WHERE id=?", g)[0], 1)

    def test_INV_36_deplacer_une_ligne_entre_devis(self):
        ouvert, l_ouvert, g_ouvert = self.devis_complet("en_attente")
        ferme, l_ferme, g_ferme = self.devis_complet("refuse")
        self.refuse_inv("INV-36", "UPDATE devis_lignes SET devis_id=?, ordre=9 WHERE id=?", ferme, l_ouvert)   # vers un devis non modifiable
        self.refuse_inv("INV-36", "UPDATE devis_lignes SET devis_id=?, ordre=9 WHERE id=?", ouvert, l_ferme)   # depuis un devis non modifiable
        autre = self.devis()
        self.db.execute("UPDATE devis_lignes SET devis_id=?, ordre=1 WHERE id=?", (autre, l_ouvert))           # entre devis modifiables : permis
        self.refuse_inv("INV-36", "UPDATE devis_ligne_garanties SET ligne_id=? WHERE id=?", l_ferme, g_ouvert)
        self.refuse_inv("INV-36", "UPDATE devis_ligne_garanties SET ligne_id=? WHERE id=?", l_ouvert, g_ferme)

    def test_INV_36_deplacer_une_ligne_depuis_ou_vers_chaque_etat_non_modifiable(self):
        for etat in ETATS_NON_MODIFIABLES:
            with self.subTest(etat=etat):
                ouvert, l_ouvert, g_ouvert = self.devis_complet("en_attente")
                ferme, l_ferme, g_ferme = self.devis_complet(etat)
                self.refuse_inv("INV-36", "UPDATE devis_lignes SET devis_id=?, ordre=9 WHERE id=?", ferme, l_ouvert)   # vers le devis fermé
                self.refuse_inv("INV-36", "UPDATE devis_lignes SET devis_id=?, ordre=9 WHERE id=?", ouvert, l_ferme)   # depuis le devis fermé
                self.refuse_inv("INV-36", "UPDATE devis_ligne_garanties SET ligne_id=? WHERE id=?", l_ferme, g_ouvert)
                self.refuse_inv("INV-36", "UPDATE devis_ligne_garanties SET ligne_id=? WHERE id=?", l_ouvert, g_ferme)
                self.assertEqual(self.un("SELECT devis_id FROM devis_lignes WHERE id=?", l_ouvert)[0], ouvert)
                self.assertEqual(self.un("SELECT devis_id FROM devis_lignes WHERE id=?", l_ferme)[0], ferme)

    def test_INV_31_id_et_created_at_gardes_pendant_une_transition_d_etat(self):
        """tr_10_devis_modifiable se décide sur l'état d'AVANT (OLD) : une transition ne lève pas la garde."""
        d, _ = self._preparer("en_attente")
        self.refuse_inv("INV-31", "UPDATE devis SET statut='accepte', date_acceptation='2026-03-12', created_at=? WHERE id=?", TS2, d)
        d, _ = self._preparer("en_attente")
        self.refuse_inv("INV-31", "UPDATE devis SET statut='accepte', date_acceptation='2026-03-12', id=id+700 WHERE id=?", d)
        d, _ = self._preparer("accepte")
        self.refuse_inv("INV-31", "UPDATE devis SET statut='annule', cancelled_at=?, motif_annulation='m', created_at=? WHERE id=?", TS, TS2, d)
        d, _ = self._preparer("accepte")
        self.refuse_inv("INV-31", "UPDATE devis SET frozen_at=?, created_at=? WHERE id=?", TS, TS2, d)
        d, _ = self._preparer("accepte")
        self.db.execute("UPDATE devis SET frozen_at=? WHERE id=?", (TS, d))                              # témoin : la pose du gel seule passe

    def test_INV_36_devis_ou_ligne_inexistants_refuses_par_la_cle_etrangere(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):
            self.db.execute("INSERT INTO devis_lignes (devis_id, ordre, designation, quantite, unite, prix_unitaire_ht, remise_type, "
                            "type_prestation, total_ht) VALUES (999, 1, 'D', '1', 'u', '1', 'aucune', 'pose', '1.00')")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):
            self.db.execute("INSERT INTO devis_ligne_garanties (ligne_id, garantie_type) VALUES (999, 'decennale')")

    def test_T28_import_pose_les_statuts_finaux_apres_les_lignes(self):
        """Conséquence de TR-10/TR-11, sans exemption pour l'import (INV-131) : on ne peut pas insérer de lignes
        sur un devis déjà refusé/annulé ; l'import insère le devis en attente, ses lignes, puis le statut final."""
        d = self.devis(statut="refuse", date_refus="2026-03-12", origine="import", numero="H-10")
        self.refuse_inv("INV-36", "INSERT INTO devis_lignes (devis_id, ordre, designation, quantite, unite, prix_unitaire_ht, "
                                  "remise_type, type_prestation, total_ht) VALUES (?, 1, 'D', '1', 'u', '1', 'aucune', 'pose', '1.00')", d)
        e = self.devis(origine="import", numero="H-11")
        self.ligne(e, 1)
        self.refuser(e)
        self.assertEqual(self.un("SELECT statut FROM devis WHERE id=?", e)[0], "refuse")
        self.assertEqual(self.un("SELECT COUNT(*) FROM devis_lignes WHERE devis_id=?", e)[0], 1)

    def _sans(self, *triggers):
        for t in triggers:
            self.db.execute(f"DROP TRIGGER {t}")

    def test_T28_chaque_trigger_garde_seul_TR01_et_TR14_sont_recouverts_par_TR10(self):
        """Isolation : TR-01 et TR-14 recoupent TR-10 ; chaque garde doit tenir même si l'autre est absente."""
        # TR-10 refuse_annule / gele protègent numero, date_creation, frozen_at sans l'aide de TR-01 / TR-14
        self._sans("tr_01_devis_numero_immuable", "tr_14_devis_frozen_at")
        for etat in ("refuse", "annule", "gele", "annule_gele"):
            with self.subTest(etat=etat):
                d, _ = self._preparer(etat)
                self.refuse_inv("INV-3[16]", "UPDATE devis SET numero='DEV-00099-26' WHERE id=?", d)
                self.refuse_inv("INV-3[16]", "UPDATE devis SET date_creation='2026-03-11' WHERE id=?", d)
        d, _ = self._preparer("gele")
        self.refuse_inv("INV-36", "UPDATE devis SET frozen_at=NULL WHERE id=?", d)
        self.refuse_inv("INV-36", "UPDATE devis SET frozen_at=? WHERE id=?", TS2, d)
        d, _ = self._preparer("annule_gele")
        self.refuse_inv("INV-31", "UPDATE devis SET frozen_at=NULL WHERE id=?", d)
        self.refuse_inv("INV-31", "UPDATE devis SET frozen_at=? WHERE id=?", TS2, d)

    def test_T28_TR01_seul(self):
        self._sans("tr_10_devis_modifiable", "tr_10_devis_refuse_annule", "tr_10_devis_gele", "tr_14_devis_frozen_at")
        for etat in ("en_attente", "accepte", "refuse", "annule", "gele"):
            with self.subTest(etat=etat):
                d, _ = self._preparer(etat)
                self.refuse_inv("INV-23", "UPDATE devis SET numero='DEV-00099-26' WHERE id=?", d)
                self.refuse_inv("INV-23", "UPDATE devis SET date_creation='2026-03-11' WHERE id=?", d)
                self.db.execute("UPDATE devis SET objet = 'libre' WHERE id=?", (d,))                 # rien d'autre n'est gardé

    def test_T28_TR14_seul(self):
        self._sans("tr_10_devis_modifiable", "tr_10_devis_refuse_annule", "tr_10_devis_gele")
        for etat in ("gele", "annule_gele"):
            with self.subTest(etat=etat):
                d, _ = self._preparer(etat)
                self.refuse_inv("INV-34", "UPDATE devis SET frozen_at=NULL WHERE id=?", d)
                self.refuse_inv("INV-34", "UPDATE devis SET frozen_at=? WHERE id=?", TS2, d)
        d, _ = self._preparer("accepte")
        self.db.execute("UPDATE devis SET frozen_at=? WHERE id=?", (TS, d))                              # NULL -> valeur : permis
        self.db.execute("UPDATE devis SET frozen_at=frozen_at, objet='x' WHERE id=?", (d,))             # inchangé : permis

    def test_T28_TR10_modifiable_ne_garde_pas_un_devis_gele(self):
        """Un devis accepte GELÉ relève de tr_10_devis_gele, pas de tr_10_devis_modifiable."""
        self._sans("tr_10_devis_gele", "tr_10_devis_refuse_annule", "tr_14_devis_frozen_at", "tr_01_devis_numero_immuable")
        d, _ = self._preparer("gele")
        self.db.execute("UPDATE devis SET created_at=? WHERE id=?", (TS2, d))
        d, _ = self._preparer("accepte")
        self.refuse_inv("INV-31", "UPDATE devis SET created_at=? WHERE id=?", TS2, d)
        d, _ = self._preparer("en_attente")
        self.refuse_inv("INV-31", "UPDATE devis SET id=id+500 WHERE id=?", d)

    def test_T28_TR10_refuse_annule_et_gele_seuls_n_ont_pas_le_meme_perimetre(self):
        """Isolation de tr_10_devis_gele : un devis refusé/annulé ne dépend pas de lui, et inversement."""
        self._sans("tr_10_devis_refuse_annule")
        for etat in ("refuse", "annule"):
            d, _ = self._preparer(etat)
            self.db.execute("UPDATE devis SET objet='libre' WHERE id=?", (d,))
        d, _ = self._preparer("gele")
        self.refuse_inv("INV-36", "UPDATE devis SET objet='x' WHERE id=?", d)
        self.setUp()
        self._sans("tr_10_devis_gele")
        d, _ = self._preparer("gele")
        self.db.execute("UPDATE devis SET objet='libre' WHERE id=?", (d,))
        d, _ = self._preparer("annule_gele")
        self.refuse_inv("INV-31", "UPDATE devis SET objet='x' WHERE id=?", d)

    def test_T28_les_triggers_ne_modifient_aucune_donnee(self):
        d, l, g = self.devis_complet("accepte")
        avant = {t: self.db.execute(f"SELECT * FROM {t} ORDER BY id").fetchall() for t in TABLES_001 | TABLES_002 | TABLES_003}
        self.db.execute("UPDATE devis SET objet='x' WHERE id=?", (d,))
        self.db.execute("UPDATE devis_lignes SET designation='y' WHERE id=?", (l,))
        apres = {t: self.db.execute(f"SELECT * FROM {t} ORDER BY id").fetchall() for t in TABLES_001 | TABLES_002 | TABLES_003}
        diffs = [t for t in avant if avant[t] != apres[t]]
        self.assertEqual(sorted(diffs), ["devis", "devis_lignes"])


class ConnexionEtReplace(Base):
    """D-39 : recursive_triggers=ON et non-contournement des protections TR-11 par INSERT OR REPLACE."""

    def gele_avec_ligne(self, db_base):
        """Devis accepté et gelé portant une ligne et une garantie ; second devis modifiable (cible du REPLACE)."""
        d1 = db_base.devis()
        l1 = db_base.ligne(d1)
        db_base.garantie(l1)
        d2 = db_base.devis()
        db_base.accepter(d1)
        db_base.geler(d1)
        return d1, l1, d2

    REPLACE_LIGNE = ("INSERT OR REPLACE INTO devis_lignes (id, devis_id, ordre, designation, quantite, unite, "
                     "prix_unitaire_ht, remise_type, type_prestation, total_ht) "
                     "VALUES (?, ?, 1, 'x', '1', 'u', '1', 'aucune', 'pose', '1.00')")

    def test_D39_recursive_triggers_actif(self):
        self.assertEqual(self.un("PRAGMA recursive_triggers")[0], 1)

    def test_INV_36_replace_ne_contourne_pas_tr_11_lignes(self):
        # Témoin : sans recursive_triggers, REPLACE « déplace » la ligne d'un devis gelé (BEFORE DELETE non déclenché).
        t = Base(); t.db = migrer(recursive=False); t._n = 0
        d1, l1, d2 = self.gele_avec_ligne(t)
        t.db.execute(self.REPLACE_LIGNE, (l1, d2))
        self.assertEqual(t.un("SELECT devis_id FROM devis_lignes WHERE id=?", l1)[0], d2)
        # Connexion conforme : refus INV-36, ligne et garantie intactes.
        d1, l1, d2 = self.gele_avec_ligne(self)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-36"):
            self.db.execute(self.REPLACE_LIGNE, (l1, d2))
        self.assertEqual(self.un("SELECT devis_id FROM devis_lignes WHERE id=?", l1)[0], d1)
        self.assertEqual(self.un("SELECT count(*) FROM devis_ligne_garanties WHERE ligne_id=?", l1)[0], 1)

    def test_INV_36_replace_ne_contourne_pas_tr_11_garanties(self):
        d1, l1, d2 = self.gele_avec_ligne(self)
        l2 = self.ligne(d2)
        gid = self.un("SELECT id FROM devis_ligne_garanties WHERE ligne_id=?", l1)[0]
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-36"):
            self.db.execute("INSERT OR REPLACE INTO devis_ligne_garanties (id, ligne_id, garantie_type) VALUES (?, ?, 'decennale')",
                            (gid, l2))
        self.assertEqual(self.un("SELECT ligne_id FROM devis_ligne_garanties WHERE id=?", gid)[0], l1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
