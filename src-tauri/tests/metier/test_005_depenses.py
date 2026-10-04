"""T-44 — DDL de la tranche Dépenses (modèle V3.13, §4.12 et §8 ; migration metier/005_depenses.sql ; CADRAGE__005_depenses.md).
Table : depenses ; triggers TR-01, TR-101, TR-102 ; 4 index. Les migrations 001, 002, 003, 004 puis 005 sont appliquées comme le fait le
runner (D-55) : une transaction par fichier, PRAGMA user_version = rang posé dans la transaction, avant le COMMIT.

Exécution : python3 src-tauri/tests/metier/test_005_depenses.py
Les méthodes portent le nom de l'invariant vérifié (test_INV_xx_…) ; les autres commencent par test_T44_ ou test_D3x_.
Ces tests ne dépendent d'aucune interface graphique ni d'aucun service : ils ne vérifient que des faits SQL (ce que la base accepte et
refuse). Les règles de service (30 jours après date_100_facture, confirmation, BC annulé sans délai, catégorie active, fournisseur
existant, cohérence année DEP / date_depense à la correction, borne d'année 2001-2099, refus d'un montant REAL, attribution du numéro)
n'y sont PAS testées comme des contraintes SQL : lorsqu'un test les évoque, c'est pour établir que le SQL ne les impose pas.
Le numéro est attribué par le service (séquence DEP de numerotation_sequences, année de date_depense) : la migration ne le génère pas ;
la constante ATTRIBUER reproduit la requête documentée du service pour les tests de numérotation.
Connexion de test : PRAGMA foreign_keys=ON et PRAGMA recursive_triggers=ON (D-39) ; un test vérifie que le réglage est actif.
Fournisseurs : 002 impose fournisseurs.statut (NOT NULL) ; les fixtures le fournissent sans que Dépenses en dépende (INV-183).
"""
import pathlib
import re
import sqlite3
import types
import unittest

MIGRATIONS = pathlib.Path(__file__).resolve().parents[2] / "migrations"
SQL_001 = (MIGRATIONS / "metier" / "001_initial.sql").read_text(encoding="utf-8")
SQL_002 = (MIGRATIONS / "metier" / "002_fournisseurs.sql").read_text(encoding="utf-8")
SQL_003 = (MIGRATIONS / "metier" / "003_devis.sql").read_text(encoding="utf-8")
SQL_004 = (MIGRATIONS / "metier" / "004_bons_commande.sql").read_text(encoding="utf-8")
SQL_005 = (MIGRATIONS / "metier" / "005_depenses.sql").read_text(encoding="utf-8")
CHAINE = ((1, SQL_001), (2, SQL_002), (3, SQL_003), (4, SQL_004), (5, SQL_005))

TABLES_001 = {"import_anomalies", "numerotation_sequences", "categories_prestations", "categories_depenses",
              "clients", "prestations", "prestation_garanties"}
TABLES_002 = {"fournisseurs"}
TABLES_003 = {"devis", "devis_lignes", "devis_ligne_garanties"}
TABLES_004 = {"bons_commande", "bc_lignes", "bc_ligne_garanties"}
TABLES_005 = {"depenses"}
TRIGGERS_001 = {"tr_90_import_anomalies_no_delete", "tr_90_import_anomalies_update",
                "tr_95_numerotation_sequences_no_decrease"}
TRIGGERS_003 = {"tr_01_devis_numero_immuable", "tr_10_devis_modifiable", "tr_10_devis_refuse_annule",
                "tr_10_devis_gele", "tr_14_devis_frozen_at",
                "tr_11_devis_lignes_insert", "tr_11_devis_lignes_update", "tr_11_devis_lignes_delete",
                "tr_11_devis_ligne_garanties_insert", "tr_11_devis_ligne_garanties_update",
                "tr_11_devis_ligne_garanties_delete"}
TRIGGERS_004 = {"tr_01_bons_commande_numero_immuable", "tr_12_bons_commande_modifiable", "tr_12_bons_commande_gele",
                "tr_12_bons_commande_annule", "tr_14_bons_commande_frozen_at", "tr_17_bons_commande_insert",
                "tr_19_bons_commande_no_delete", "tr_18_devis_statut_avec_bc",
                "tr_13_bc_lignes_insert", "tr_13_bc_lignes_update", "tr_13_bc_lignes_delete",
                "tr_13_bc_ligne_garanties_insert", "tr_13_bc_ligne_garanties_update", "tr_13_bc_ligne_garanties_delete",
                "tr_96_numerotation_sequences_no_delete"}
TRIGGERS_005 = {"tr_01_depenses_numero_immuable", "tr_101_depenses_no_delete", "tr_102_depenses_annulee_immuable"}
INDEXES_001_002 = {"idx_clients_statut", "idx_prestations_categorie_id", "idx_prestations_actif",
                   "idx_import_anomalies_categorie_statut", "idx_fournisseurs_statut"}
INDEXES_003 = {"idx_devis_client_id", "idx_devis_statut", "idx_devis_date_creation", "idx_devis_lignes_prestation_id"}
INDEXES_004 = {"idx_bons_commande_client_id", "idx_bons_commande_statut", "idx_bc_lignes_prestation_id"}
INDEXES_005 = {"idx_depenses_bc_id", "idx_depenses_fournisseur_id", "idx_depenses_categorie_id", "idx_depenses_date_depense"}

COLONNES_DEPENSES = ["id", "numero", "fournisseur_id", "bc_id", "date_depense", "montant", "categorie_id", "description",
                     "piece_jointe_chemin", "piece_jointe_racine_id", "notes", "cancelled_at", "motif_annulation",
                     "created_at", "updated_at"]
# colonnes qui ne doivent jamais exister dans depenses (décisions DV-8 à DV-10, INV-183, D-23, PT-8)
COLONNES_INTERDITES = ["statut", "origine", "legacy_id", "legacy_data", "legacy_numero", "taux_tva", "montant_tva", "montant_ttc",
                       "tva", "ttc", "date_facture", "date_echeance", "date_paiement", "frozen_at", "completed_at", "created_by",
                       "modified_by", "modified_at", "historique", "journal", "fournisseur_nom", "client_id", "devis_id"]

TS = "2026-10-01T10:00:00.000Z"
TS2 = "2026-10-02T11:30:15.123Z"
SNAP = '{"nom": "Dupont"}'
ATTRIBUER = ("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES (?, ?, 1) "
             "ON CONFLICT (type_objet, annee) DO UPDATE SET dernier_numero = dernier_numero + 1, "
             "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') RETURNING dernier_numero")
TS_GLOB = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")


def appliquer(db, rang, sql):
    """Une migration comme le runner (D-55, conventions §5) : BEGIN IMMEDIATE, SQL du fichier, user_version = rang, COMMIT."""
    db.executescript(f"BEGIN IMMEDIATE;\n{sql}\nPRAGMA user_version = {rang};\nCOMMIT;")


def migrer(recursive=True, jusqu_a=5):
    """Applique 001 à 005 (ou jusqu'au rang `jusqu_a`) comme le runner. La connexion applique les réglages obligatoires (D-39) :
    foreign_keys=ON et recursive_triggers=ON."""
    db = sqlite3.connect(":memory:", isolation_level=None)
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA recursive_triggers=" + ("ON" if recursive else "OFF"))
    for rang, sql in CHAINE:
        if rang <= jusqu_a:
            appliquer(db, rang, sql)
    return db


def schema(db, hors_table=None):
    """Objets du schéma (type, nom, table, sql), sans les tables internes de SQLite ; `hors_table` exclut les objets d'une table."""
    return sorted(r for r in db.execute("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")
                  if r[2] != hors_table)


def sans_commentaires(sql):
    return re.sub(r"--[^\n]*", "", sql)


class Base(unittest.TestCase):
    def setUp(self):
        self.db = migrer()
        self._n = 0
        self._d = 0
        self.cat = self.categorie("MAT")
        self.f1 = self.fournisseur()
        self.f2 = self.fournisseur(statut="archive")

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

    def tous(self, sql, *args):
        return self.db.execute(sql, args).fetchall()

    def essai(self, sql, *args):
        """Retourne None si l'instruction réussit, sinon le message d'erreur."""
        try:
            self.db.execute(sql, args)
            return None
        except sqlite3.IntegrityError as e:
            return str(e)

    # --- fabrication de données : tranches 001 à 004 ---------------------------------
    def categorie(self, code="MAT", actif=1):
        self.db.execute("INSERT INTO categories_depenses (code, libelle, actif, ordre) VALUES (?, 'Libellé', ?, 1)", (code, actif))
        return self.un("SELECT id FROM categories_depenses WHERE code=?", code)[0]

    def fournisseur(self, statut="actif", **kw):
        self._n += 1
        cols = {"code": f"FOU-{self._n:04d}", "nom": "Fournisseur", "statut": statut}
        cols.update(kw)
        self.db.execute(f"INSERT INTO fournisseurs ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))
        return self.un("SELECT id FROM fournisseurs WHERE code=?", cols["code"])[0]

    def client(self):
        self._n += 1
        code = f"CLI-{self._n:04d}"
        self.db.execute("INSERT INTO clients (code, nom, statut) VALUES (?, 'Dupont', 'actif')", (code,))
        return self.un("SELECT id FROM clients WHERE code=?", code)[0]

    def devis_accepte(self):
        """Devis accepté sans ligne (suffisant pour porter un BC ; les lignes n'importent pas à Dépenses)."""
        self._n += 1
        numero = f"DEV-{self._n:05d}-26"
        cols = {"numero": numero, "client_id": self.client(), "client_snapshot": SNAP, "client_snapshot_version": 1,
                "entreprise_snapshot": SNAP, "entreprise_snapshot_version": 1, "chantier_snapshot": SNAP,
                "chantier_snapshot_version": 1, "date_creation": "2026-03-10", "statut": "accepte",
                "date_acceptation": "2026-03-12", "total_ht": "0.00"}
        self.db.execute(f"INSERT INTO devis ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))
        return self.un("SELECT id FROM devis WHERE numero=?", numero)[0]

    def creer_bc(self):
        """INSERT du BC par copie du devis accepté ; le numéro vient de la séquence BCD (année de date_creation)."""
        d = self.devis_accepte()
        s = self.un("SELECT client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, entreprise_snapshot_version, "
                    "chantier_snapshot, chantier_snapshot_version, date_acceptation, total_ht, remise_type, remise_valeur, "
                    "acompte_type, acompte_valeur FROM devis WHERE id=?", d)
        cols = dict(zip(["client_id", "client_snapshot", "client_snapshot_version", "entreprise_snapshot",
                         "entreprise_snapshot_version", "chantier_snapshot", "chantier_snapshot_version", "date_acceptation",
                         "montant_contractuel_ht", "remise_type", "remise_valeur", "acompte_type", "acompte_valeur"], s))
        cols["devis_id"] = d
        cols["date_creation"] = "2026-10-02"
        cols["numero"] = f"BCD-{self.un(ATTRIBUER, 'BCD', 26)[0]:05d}-26"
        self.db.execute(f"INSERT INTO bons_commande ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))
        return self.un("SELECT id FROM bons_commande WHERE numero=?", cols["numero"])[0]

    def geler_bc(self, b):
        self.db.execute("UPDATE bons_commande SET frozen_at=? WHERE id=?", (TS, b))
        self.db.execute("UPDATE devis SET frozen_at=? WHERE id=(SELECT devis_id FROM bons_commande WHERE id=?)", (TS, b))

    def terminer_bc(self, b, date_100="2026-10-02"):
        """Caches écrits en un seul UPDATE (INV-164) : BC entièrement facturé le `date_100`."""
        self.db.execute("UPDATE bons_commande SET statut='termine', completed_at=?, date_100_facture=?, avancement='100.00', "
                        "montant_deja_facture_ht=montant_contractuel_ht, updated_at=? WHERE id=?", (TS, date_100, TS, b))

    def annuler_bc(self, b):
        self.db.execute("UPDATE bons_commande SET statut='annule', cancelled_at=?, motif_annulation='Client renonce', "
                        "completed_at=NULL, date_100_facture=NULL, updated_at=? WHERE id=?", (TS, TS, b))

    def bc_en_etat(self, etat):
        """BC dans l'état voulu : en_cours, gele, termine, annule, annule_gele."""
        b = self.creer_bc()
        if etat in ("gele", "termine", "annule_gele"):
            self.geler_bc(b)
        if etat == "termine":
            self.terminer_bc(b)
        if etat in ("annule", "annule_gele"):
            self.annuler_bc(b)
        elif etat not in ("en_cours", "gele", "termine"):
            raise ValueError(etat)
        return b

    # --- fabrication de données : tranche 005 ------------------------------------------
    def dep(self, **kw):
        """INSERT d'une dépense active (le numéro vient d'un compteur de test ; il est unique et cohérent avec date_depense)."""
        cols = {"date_depense": "2026-10-02", "montant": "12.50", "categorie_id": self.cat, "description": "Achat"}
        cols.update(kw)
        if "numero" not in cols:
            self._d += 1
            cols["numero"] = f"DEP-{self._d:05d}-{cols['date_depense'][2:4]}"
        self.db.execute(f"INSERT INTO depenses ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))
        return self.un("SELECT id FROM depenses WHERE numero=?", cols["numero"])[0]

    def annuler(self, i, motif="Erreur de saisie", quand=TS2):
        self.db.execute("UPDATE depenses SET cancelled_at=?, motif_annulation=?, updated_at=? WHERE id=?", (quand, motif, quand, i))

    def ligne(self, i):
        return self.un("SELECT * FROM depenses WHERE id=?", i)


ETATS_BC = ("en_cours", "gele", "termine", "annule", "annule_gele")


class Migration(Base):
    def test_T44_migration_sur_base_issue_de_001_a_004(self):
        self.assertEqual(self.un("PRAGMA user_version")[0], 5)
        noms = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        self.assertEqual(noms, TABLES_001 | TABLES_002 | TABLES_003 | TABLES_004 | TABLES_005)
        strict = {r[1] for r in self.db.execute("PRAGMA table_list") if r[5] == 1}
        self.assertTrue(TABLES_005 <= strict)
        self.assertEqual({r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")},
                         TRIGGERS_001 | TRIGGERS_003 | TRIGGERS_004 | TRIGGERS_005)
        self.assertEqual({r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")},
                         INDEXES_001_002 | INDEXES_003 | INDEXES_004 | INDEXES_005)
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(self.db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])

    def test_T44_rang_et_user_version_pose_par_le_runner(self):
        db = migrer(jusqu_a=4)
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 4)
        appliquer(db, 5, SQL_005)
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 5)
        for rang in (1, 2, 3, 4, 5):                                                 # rang = position dans la chaîne (D-55)
            self.assertEqual(migrer(jusqu_a=rang).execute("PRAGMA user_version").fetchone()[0], rang)

    def test_T44_effectifs_de_la_tranche(self):
        sans = sans_commentaires(SQL_005)
        self.assertEqual(len(TABLES_005), 1)
        self.assertEqual(len(TRIGGERS_005), 3)
        self.assertEqual(len(INDEXES_005), 4)
        self.assertEqual(len(re.findall(r"(?im)^\s*CREATE\s+TABLE\b", sans)), 1)
        self.assertEqual(len(re.findall(r"(?im)^\s*CREATE\s+TRIGGER\b", sans)), 3)
        self.assertEqual(len(re.findall(r"(?im)^\s*CREATE\s+INDEX\b", sans)), 4)
        self.assertEqual(len(re.findall(r"(?im)^\s*CREATE\s+UNIQUE\s+INDEX\b", sans)), 0)
        self.assertEqual(len(re.findall(r"(?im)^\s*CREATE\s+(VIEW|VIRTUAL|TEMP)", sans)), 0)

    def test_T44_aucun_objet_non_prevu(self):
        nouveaux = {r[1] for r in schema(self.db, None)} - {r[1] for r in schema(migrer(jusqu_a=4), None)}
        self.assertEqual(nouveaux, TABLES_005 | TRIGGERS_005 | INDEXES_005)
        self.assertEqual(len(nouveaux), 8)
        # les seuls objets automatiques ajoutés sont ceux du UNIQUE de numero
        autos = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE tbl_name='depenses' AND name LIKE 'sqlite_autoindex%'")}
        self.assertEqual(len(autos), 1)

    def test_T44_table_strict_et_autoincrement(self):
        sql = self.un("SELECT sql FROM sqlite_master WHERE name='depenses'")[0]
        self.assertRegex(sql, r"\) STRICT$")
        self.assertIn("id                     INTEGER PRIMARY KEY AUTOINCREMENT", sql)

    def test_T44_colonnes_exactes(self):
        self.assertEqual([r[1] for r in self.db.execute("PRAGMA table_info(depenses)")], COLONNES_DEPENSES)
        types_ = {r[1]: r[2] for r in self.db.execute("PRAGMA table_info(depenses)")}
        self.assertEqual({c: t for c, t in types_.items() if t == "INTEGER"},
                         {"id": "INTEGER", "fournisseur_id": "INTEGER", "bc_id": "INTEGER", "categorie_id": "INTEGER",
                          "piece_jointe_racine_id": "INTEGER"})
        self.assertEqual({t for c, t in types_.items() if t != "INTEGER"}, {"TEXT"})

    def test_T44_colonnes_obligatoires_et_defauts(self):
        infos = {r[1]: r for r in self.db.execute("PRAGMA table_info(depenses)")}
        obligatoires = {"numero", "date_depense", "montant", "categorie_id", "description", "created_at", "updated_at"}
        for c in COLONNES_DEPENSES:
            if c != "id":
                self.assertEqual(infos[c][3], 1 if c in obligatoires else 0, c)
        defauts = {c: infos[c][4] for c in COLONNES_DEPENSES if infos[c][4] is not None}
        self.assertEqual(defauts, {"created_at": "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')",
                                   "updated_at": "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"})
        self.assertEqual([c for c in COLONNES_DEPENSES if infos[c][5]], ["id"])        # seule clé primaire : id

    def test_T44_cles_etrangeres(self):
        fk = {(r[2], r[3], r[4], r[6]) for r in self.db.execute("PRAGMA foreign_key_list(depenses)")}
        self.assertEqual(fk, {("fournisseurs", "fournisseur_id", "id", "RESTRICT"),
                              ("bons_commande", "bc_id", "id", "RESTRICT"),
                              ("categories_depenses", "categorie_id", "id", "RESTRICT")})
        tables = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for r in self.db.execute("PRAGMA foreign_key_list(depenses)"):
            self.assertEqual(r[5], "NO ACTION", r[3])                                  # aucune clause ON UPDATE
            self.assertIn(r[2], tables)
        self.assertNotRegex(sans_commentaires(SQL_005), r"(?i)\bON\s+UPDATE\b")
        self.assertNotRegex(sans_commentaires(SQL_005), r"(?i)\bON\s+DELETE\s+(CASCADE|SET)\b")
        # aucune FK ne désigne depenses (aucune table dépendante dans cette tranche)
        for t in TABLES_001 | TABLES_002 | TABLES_003 | TABLES_004:
            self.assertNotIn("depenses", {r[2] for r in self.db.execute(f"PRAGMA foreign_key_list({t})")}, t)

    def test_T44_index(self):
        def colonnes(nom):
            return [r[2] for r in self.db.execute(f"PRAGMA index_info({nom})")]
        self.assertEqual(colonnes("idx_depenses_bc_id"), ["bc_id"])
        self.assertEqual(colonnes("idx_depenses_fournisseur_id"), ["fournisseur_id"])
        self.assertEqual(colonnes("idx_depenses_categorie_id"), ["categorie_id"])
        self.assertEqual(colonnes("idx_depenses_date_depense"), ["date_depense"])
        for nom in INDEXES_005:
            self.assertEqual(self.un("SELECT tbl_name FROM sqlite_master WHERE name=?", nom)[0], "depenses")
        # le seul UNIQUE est celui de numero
        uniques = sorted([c[2] for c in self.db.execute(f"PRAGMA index_info({r[1]})")]
                         for r in self.db.execute("PRAGMA index_list(depenses)") if r[2] == 1)
        self.assertEqual(uniques, [["numero"]])
        # les index sont utilisés par les recherches de la tranche
        for colonne, valeur in (("bc_id", 1), ("fournisseur_id", 1), ("categorie_id", 1), ("date_depense", "2026-10-02")):
            plan = " ".join(str(r) for r in self.tous(f"EXPLAIN QUERY PLAN SELECT id FROM depenses WHERE {colonne}=?", valeur))
            self.assertIn(f"idx_depenses_{colonne}", plan, colonne)

    def test_T44_aucune_donnee_initiale(self):
        for t in TABLES_001 | TABLES_002 | TABLES_003 | TABLES_004 | TABLES_005:
            self.assertEqual(migrer().execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0], 0, t)       # y compris numerotation_sequences
        sans = sans_commentaires(SQL_005)
        sans = re.sub(r"(?i)\bON\s+(DELETE|UPDATE)\s+(RESTRICT|CASCADE)", "", sans)   # actions de FK
        triggers = re.findall(r"CREATE TRIGGER.*?\nEND;", sans, flags=re.S)
        self.assertEqual(len(triggers), len(TRIGGERS_005))
        hors_triggers = sans
        for t in triggers:
            hors_triggers = hors_triggers.replace(t, "")
        self.assertNotRegex(hors_triggers, r"(?i)\b(INSERT|UPDATE|DELETE|DROP|ALTER|PRAGMA|BEGIN|COMMIT|ROLLBACK)\b|\bREPLACE\s+INTO\b")
        self.assertEqual(sorted(re.findall(r"(?i)\bCREATE\s+(\w+)", hors_triggers)), ["INDEX"] * 4 + ["TABLE"])

    def test_T44_triggers_ne_font_que_garder(self):
        """Chaque trigger est BEFORE et ne contient que des « SELECT RAISE(ABORT, 'INV-nn: …') »."""
        sans = sans_commentaires(SQL_005)
        triggers = re.findall(r"CREATE TRIGGER.*?\nEND;", sans, flags=re.S)
        self.assertEqual(len(triggers), 3)
        for t in triggers:
            nom = re.match(r"CREATE TRIGGER (\w+)\nBEFORE (INSERT|UPDATE|DELETE)\b", t)
            self.assertIsNotNone(nom, t[:80])                                       # BEFORE : avant les CHECK
            corps = t[t.index("\nBEGIN") + 6:-len("END;")]
            corps = re.sub(r"'(?:[^']|'')*'", lambda m: m.group(0) if m.group(0).startswith("'INV-") else "''", corps)
            instructions = [i.strip() for i in corps.split(";") if i.strip()]
            self.assertEqual(len(instructions), 1, nom.group(1))
            self.assertRegex(instructions[0], r"^SELECT RAISE\(ABORT, 'INV-\d+: [^']*(?:''[^']*)*'\)$")
            self.assertNotRegex(re.sub(r"'(?:[^']|'')*'", "''", corps), r"(?i)\b(INSERT|UPDATE|DELETE|REPLACE|DROP|ALTER|SELECT\s+.*\bFROM)\b")

    def test_T44_triggers_table_et_evenement(self):
        attendu = {"tr_01_depenses_numero_immuable": "UPDATE OF numero, date_depense",
                   "tr_101_depenses_no_delete": "DELETE",
                   "tr_102_depenses_annulee_immuable": "UPDATE"}
        for nom, evenement in attendu.items():
            sql, tbl = self.un("SELECT sql, tbl_name FROM sqlite_master WHERE type='trigger' AND name=?", nom)
            with self.subTest(trigger=nom):
                self.assertEqual(tbl, "depenses")
                self.assertRegex(sql, rf"(?s)^CREATE TRIGGER {nom}\nBEFORE {evenement} ON depenses\b")
        # TR-102 : aucune liste de colonnes (couvre updated_at isolé et cancelled_at), condition sur l'état AVANT l'UPDATE
        sql102 = self.un("SELECT sql FROM sqlite_master WHERE name='tr_102_depenses_annulee_immuable'")[0]
        self.assertNotRegex(sql102.split("\nBEGIN")[0], r"UPDATE OF")
        self.assertRegex(sql102, r"WHEN OLD\.cancelled_at IS NOT NULL\nBEGIN")
        sql101 = self.un("SELECT sql FROM sqlite_master WHERE name='tr_101_depenses_no_delete'")[0]
        self.assertNotRegex(sql101, r"\bWHEN\b")                                    # aucune exception : actives et annulées

    def test_T44_aucune_dependance_aux_tranches_suivantes(self):
        code = re.sub(r"'[^']*'", "''", sans_commentaires(SQL_005))              # sans commentaires ni textes
        for absent in ("factures", "facture_lignes", "reglements", "historique", "documents", "garanties", "pv", "pv_reception",
                       "planning", "urssaf_periodes", "bc_devis", "devis_revisions"):
            with self.subTest(objet=absent):
                self.assertNotRegex(code, rf"\b{absent}\b")

    def test_T44_dependances_limitees_aux_cles_primaires_stables(self):
        """005 ne référence que `id` de fournisseurs, bons_commande et categories_depenses (compatibilité 001-004 / 005a / 005b)."""
        code = re.sub(r"'(?:[^']|'')*'", "''", sans_commentaires(SQL_005))
        self.assertEqual(set(re.findall(r"REFERENCES\s+(\w+)\s*\((\w+)\)", code)),
                         {("fournisseurs", "id"), ("bons_commande", "id"), ("categories_depenses", "id")})
        for lu in ("statut", "devis_id", "frozen_at", "date_100_facture", "clients", "devis", "a_rattacher", "actif",
                   "numerotation_sequences"):
            with self.subTest(lecture=lu):
                self.assertNotRegex(code, rf"\b{lu}\b")
        for nom in TRIGGERS_005:
            corps = self.un("SELECT sql FROM sqlite_master WHERE name=?", nom)[0]
            self.assertNotRegex(re.sub(r"'(?:[^']|'')*'", "''", corps), r"(?i)\b(FROM|JOIN)\b", nom)   # triggers locaux à une ligne

    def test_T44_conventions_du_fichier(self):
        sans = sans_commentaires(SQL_005)
        self.assertNotRegex(sans, r"(?i)INSERT\s+OR\s+REPLACE|\bREPLACE\s+INTO\b")
        self.assertNotRegex(sans, r"(?i)\bIF\s+NOT\s+EXISTS\b")                      # chaîne par rangs : chaque migration est jouée une fois
        self.assertNotRegex(sans, r"\{\d")                                           # GLOB sans quantificateur {n}
        self.assertNotRegex(sans, r"\bdate\([a-z_]+\)\s*=\s*[a-z_]+")                 # date(x) IS x, jamais date(x) = x
        self.assertRegex(sans, r"date\(date_depense\) IS date_depense")
        self.assertRegex(self.un("SELECT sql FROM sqlite_master WHERE name='depenses'")[0], r"\) STRICT$")
        self.assertNotRegex(sans, r"\b(REAL|FLOAT|DOUBLE|NUMERIC)\b")                 # aucun flottant financier
        self.assertNotRegex(sans, r"(?i)\b(PRAGMA|BEGIN\s+(IMMEDIATE|DEFERRED|EXCLUSIVE|TRANSACTION)|COMMIT)\b")   # transaction : runner

    def test_T44_non_regression_001_a_004_inchangees(self):
        avant = migrer(jusqu_a=4)
        anciens = schema(avant)
        self.assertEqual(schema(self.db, hors_table="depenses"), anciens)             # aucun objet ancien ajouté, retiré ou modifié
        self.assertEqual(len(anciens), len(TABLES_001 | TABLES_002 | TABLES_003 | TABLES_004)
                         + len(TRIGGERS_001 | TRIGGERS_003 | TRIGGERS_004) + len(INDEXES_001_002 | INDEXES_003 | INDEXES_004)
                         + len([r for r in anciens if r[1].startswith("sqlite_autoindex") or r[3] is None]))
        for t in TABLES_001 | TABLES_002 | TABLES_003 | TABLES_004:
            self.assertEqual(self.db.execute(f"PRAGMA table_info({t})").fetchall(), avant.execute(f"PRAGMA table_info({t})").fetchall(), t)
            self.assertEqual(self.db.execute(f"PRAGMA foreign_key_list({t})").fetchall(), avant.execute(f"PRAGMA foreign_key_list({t})").fetchall(), t)

    def test_T44_aucune_structure_d_import_ni_de_tva_ni_de_statut(self):
        colonnes = {r[1] for r in self.db.execute("PRAGMA table_info(depenses)")}
        for interdite in COLONNES_INTERDITES:
            with self.subTest(colonne=interdite):
                self.assertNotIn(interdite, colonnes)
        code = re.sub(r"'(?:[^']|'')*'", "''", sans_commentaires(SQL_005))
        self.assertNotRegex(code, r"(?i)legacy|origine|import_anomalies|\bBLOC-IMP\b|\btva\b|\bttc\b")
        # l'import V6 n'accepte pas de bloc depenses (modèle §10.3, D-23) : aucune anomalie ni table d'import n'est ajoutée
        self.assertEqual(self.un("SELECT COUNT(*) FROM import_anomalies")[0], 0)
        self.assertEqual(self.un("SELECT COUNT(*) FROM sqlite_master WHERE tbl_name='import_anomalies'")[0],
                         migrer(jusqu_a=4).execute("SELECT COUNT(*) FROM sqlite_master WHERE tbl_name='import_anomalies'").fetchone()[0])

    def test_T44_aucun_controle_ck_ni_regle_de_delai_dans_la_migration(self):
        """Aucun CK-xx n'est une table ou une vue ; aucune règle de service (30 jours, BC annulé, catégorie active) n'est codée."""
        code = re.sub(r"'(?:[^']|'')*'", "''", sans_commentaires(SQL_005))
        self.assertNotRegex(code, r"(?i)\bCK-\d+\b|\bjulianday\b|\bstrftime\('%s'|date\([^)]*,\s*'[-+]")
        self.assertNotRegex(code, r"(?i)\b30\b")
        self.assertEqual(self.un("SELECT COUNT(*) FROM sqlite_master WHERE type='view'")[0], 0)

    def test_D39_recursive_triggers_actif(self):
        self.assertEqual(self.un("PRAGMA recursive_triggers")[0], 1)
        self.assertEqual(self.un("PRAGMA foreign_keys")[0], 1)
        t = Base(); t.db = migrer(recursive=False)                          # témoin : le réglage n'est pas celui de SQLite par défaut
        self.assertEqual(t.un("PRAGMA recursive_triggers")[0], 0)
        self.assertEqual(sqlite3.connect(":memory:").execute("PRAGMA recursive_triggers").fetchone()[0], 0)

    def test_T44_atomicite_echec_pendant_la_migration_rollback_complet(self):
        db = migrer(jusqu_a=4)
        avant = schema(db)
        avant_fk = db.execute("PRAGMA foreign_keys").fetchone()[0]
        with self.assertRaises(sqlite3.OperationalError):
            db.executescript("BEGIN IMMEDIATE;\n" + SQL_005 + "\nINSERT INTO table_inexistante VALUES (1);\n"
                             "PRAGMA user_version = 5;\nCOMMIT;")
        self.assertTrue(db.in_transaction)                                      # la transaction du runner est toujours ouverte
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 4)
        db.execute("ROLLBACK")
        self.assertFalse(db.in_transaction)
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 4)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM sqlite_master WHERE tbl_name='depenses' OR name LIKE 'idx_depenses%'").fetchone()[0], 0)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM sqlite_master WHERE name LIKE 'tr_%depenses%' OR name LIKE 'sqlite_autoindex_depenses%'").fetchone()[0], 0)
        self.assertIsNone(db.execute("SELECT 1 FROM sqlite_sequence WHERE name='depenses'").fetchone())
        self.assertEqual(schema(db), avant)                                      # aucune table partiellement créée
        self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], avant_fk)

    def test_T44_atomicite_echec_au_milieu_de_005_aucun_objet_partiel(self):
        coupure = SQL_005.index("CREATE TRIGGER tr_102_depenses_annulee_immuable")
        db = migrer(jusqu_a=4)
        avant = schema(db)
        with self.assertRaises(sqlite3.OperationalError):
            db.executescript("BEGIN IMMEDIATE;\n" + SQL_005[:coupure] + "\nCREATE TRIGGER tr_102_depenses_annulee_immuable\n"
                             "BEFORE UPDATE ON depenses_inexistante BEGIN SELECT 1; END;\n" + SQL_005[coupure:] +
                             "\nPRAGMA user_version = 5;\nCOMMIT;")
        # à ce stade la table, les index et deux triggers existent dans la transaction ouverte
        self.assertEqual(db.execute("SELECT COUNT(*) FROM sqlite_master WHERE tbl_name='depenses'").fetchone()[0] > 0, True)
        db.execute("ROLLBACK")
        self.assertEqual(schema(db), avant)
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 4)

    def test_T44_user_version_non_modifie_avant_la_validation(self):
        db = migrer(jusqu_a=4)
        with self.assertRaises(sqlite3.OperationalError):
            db.executescript("BEGIN IMMEDIATE;\n" + SQL_005 + "\nPRAGMA user_version = 5;\nSELECT * FROM table_inexistante;\nCOMMIT;")
        db.execute("ROLLBACK")                                                   # user_version = 5 avait été posé avant l'échec
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 4)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM sqlite_master WHERE tbl_name='depenses'").fetchone()[0], 0)

    def test_T44_rejeu_apres_echec(self):
        db = migrer(jusqu_a=4)
        with self.assertRaises(sqlite3.OperationalError):
            db.executescript("BEGIN IMMEDIATE;\n" + SQL_005 + "\nINSERT INTO table_inexistante VALUES (1);\nCOMMIT;")
        db.execute("ROLLBACK")
        appliquer(db, 5, SQL_005)                                                # rejeu correct après échec
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 5)
        self.assertEqual(schema(db), schema(self.db))                            # même schéma qu'une base neuve
        self.assertEqual(db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
        self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_T44_la_migration_ne_se_rejoue_pas_sur_une_base_deja_a_son_rang(self):
        """Pas de IF NOT EXISTS : rejouer 005 sur une base au rang 5 échoue, et c'est le rang qui l'empêche (D-55)."""
        db = migrer()
        with self.assertRaises(sqlite3.OperationalError):
            db.executescript("BEGIN IMMEDIATE;\n" + SQL_005 + "\nCOMMIT;")
        db.execute("ROLLBACK")
        self.assertEqual(schema(db), schema(self.db))
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 5)


class Contraintes(Base):
    """Structure de la table : NOT NULL, PK, UNIQUE, CHECK, timestamps (INV-04, INV-10, INV-11, INV-14, INV-20)."""

    def test_INV_04_cle_primaire_autoincrement_jamais_reutilisee(self):
        a, b = self.dep(), self.dep()
        self.assertEqual(b, a + 1)
        self.assertEqual(self.un("SELECT seq FROM sqlite_sequence WHERE name='depenses'")[0], b)
        self.assertEqual(self.tous("SELECT pk FROM pragma_table_info('depenses') WHERE pk>0"), [(1,)])
        self.refuse("INSERT INTO depenses (id, numero, date_depense, montant, categorie_id, description) "
                    "VALUES (?, 'DEP-00099-26', '2026-10-02', '1.00', ?, 'x')", a, self.cat)                  # id déjà pris

    def test_T44_champs_obligatoires_refuses_a_l_insertion(self):
        base = {"numero": "DEP-00001-26", "date_depense": "2026-10-02", "montant": "5.00", "categorie_id": self.cat,
                "description": "x", "created_at": TS, "updated_at": TS}
        for col in base:
            with self.subTest(colonne=col):
                cols = dict(base, **{col: None})
                with self.assertRaises(sqlite3.IntegrityError) as cm:
                    self.db.execute(f"INSERT INTO depenses ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))
                self.assertIn("NOT NULL", str(cm.exception))
                self.assertEqual(self.un("SELECT COUNT(*) FROM depenses")[0], 0)

    def test_T44_champs_obligatoires_refuses_a_la_modification(self):
        i = self.dep()
        for col in ("numero", "date_depense", "montant", "categorie_id", "description", "created_at", "updated_at"):
            with self.subTest(colonne=col):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.db.execute(f"UPDATE depenses SET {col}=NULL WHERE id=?", (i,))

    def test_T44_champs_facultatifs_acceptes_a_NULL(self):
        i = self.dep()
        ligne = self.ligne(i)
        for col in ("fournisseur_id", "bc_id", "piece_jointe_chemin", "piece_jointe_racine_id", "notes", "cancelled_at", "motif_annulation"):
            self.assertIsNone(ligne[COLONNES_DEPENSES.index(col)], col)

    def test_T44_defauts_created_at_updated_at(self):
        i = self.dep()
        c, u = self.un("SELECT created_at, updated_at FROM depenses WHERE id=?", i)
        self.assertRegex(c, TS_GLOB)
        self.assertRegex(u, TS_GLOB)
        j = self.dep(created_at=TS, updated_at=TS2)
        self.assertEqual(self.un("SELECT created_at, updated_at FROM depenses WHERE id=?", j), (TS, TS2))     # valeurs explicites conservées

    def test_T44_timestamps_formats_invalides_refuses(self):
        i = self.dep()
        for col in ("created_at", "updated_at"):
            for valeur in ("2026-10-02", "2026-10-02T10:00:00Z", "2026-10-02 10:00:00.000", "2026-10-02T10:00:00.000",
                           "2026-10-02T10:00:00.00Z", "hier", "", "2026-10-02T10:00:00.0000Z"):
                with self.subTest(colonne=col, valeur=valeur):
                    self.refuse_check(f"UPDATE depenses SET {col}=? WHERE id=?", valeur, i)
        self.refuse_check("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description, created_at) "
                          "VALUES ('DEP-00099-26', '2026-10-02', '1.00', ?, 'x', 'x')", self.cat)

    # --- numero : UNIQUE ------------------------------------------------------------
    def test_INV_22_numero_unique(self):
        self.dep(numero="DEP-00001-26")
        self.refuse_check("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) "
                          "VALUES ('DEP-00001-26', '2026-10-02', '1.00', ?, 'x')", self.cat)
        i = self.dep(numero="DEP-00002-26")
        self.refuse_inv("INV-23", "UPDATE depenses SET numero='DEP-00001-26' WHERE id=?", i)               # TR-01 passe avant UNIQUE
        self.assertEqual(self.un("SELECT COUNT(DISTINCT numero), COUNT(*) FROM depenses"), (2, 2))

    def test_INV_22_unicite_est_portee_par_la_table_et_non_par_un_trigger(self):
        t = Base(); t.setUp(); t.db.execute("DROP TRIGGER tr_01_depenses_numero_immuable")
        t.dep(numero="DEP-00001-26")
        i = t.dep(numero="DEP-00002-26")
        t.refuse_check("UPDATE depenses SET numero='DEP-00001-26' WHERE id=?", i)                           # UNIQUE seul

    # --- description ---------------------------------------------------------------
    def test_T44_description_obligatoire_et_non_vide(self):
        self.refuse_check("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) "
                          "VALUES ('DEP-00001-26', '2026-10-02', '1.00', ?, '')", self.cat)
        self.refuse_check("INSERT INTO depenses (numero, date_depense, montant, categorie_id) "
                          "VALUES ('DEP-00001-26', '2026-10-02', '1.00', ?)", self.cat)
        i = self.dep(description="x")
        self.refuse_check("UPDATE depenses SET description='' WHERE id=?", i)
        self.dep(description="Achat de visserie « inox » – 12 pièces")                                      # texte libre

    def test_T44_notes_libres(self):
        i = self.dep(notes="")
        self.assertEqual(self.un("SELECT notes FROM depenses WHERE id=?", i)[0], "")
        self.db.execute("UPDATE depenses SET notes='n' WHERE id=?", (i,))
        self.db.execute("UPDATE depenses SET notes=NULL WHERE id=?", (i,))

    # --- pièce jointe ------------------------------------------------------------------
    def test_T44_piece_jointe_chemin_et_racine_ensemble_ou_aucun(self):
        a = self.dep(piece_jointe_chemin="2026/10/facture.pdf", piece_jointe_racine_id=7)
        self.assertEqual(self.un("SELECT piece_jointe_chemin, piece_jointe_racine_id FROM depenses WHERE id=?", a), ("2026/10/facture.pdf", 7))
        for cols in ({"piece_jointe_chemin": "a/b"}, {"piece_jointe_racine_id": 3}):
            with self.subTest(cols=cols):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.dep(**cols)
        i = self.dep()
        self.refuse_check("UPDATE depenses SET piece_jointe_chemin='a/b' WHERE id=?", i)
        self.refuse_check("UPDATE depenses SET piece_jointe_racine_id=3 WHERE id=?", i)
        self.db.execute("UPDATE depenses SET piece_jointe_chemin='a/b', piece_jointe_racine_id=3 WHERE id=?", (i,))
        self.refuse_check("UPDATE depenses SET piece_jointe_chemin=NULL WHERE id=?", i)
        self.refuse_check("UPDATE depenses SET piece_jointe_racine_id=NULL WHERE id=?", i)
        self.db.execute("UPDATE depenses SET piece_jointe_chemin=NULL, piece_jointe_racine_id=NULL WHERE id=?", (i,))

    def test_T44_piece_jointe_chemin_non_vide_et_racine_sans_cle_etrangere(self):
        self.refuse_check("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description, piece_jointe_chemin, "
                          "piece_jointe_racine_id) VALUES ('DEP-00001-26', '2026-10-02', '1.00', ?, 'x', '', 3)", self.cat)
        self.dep(piece_jointe_chemin="x", piece_jointe_racine_id=999999)               # racine de machine.db : référence logique, aucune FK
        self.assertNotIn("piece_jointe_racine_id", {r[3] for r in self.db.execute("PRAGMA foreign_key_list(depenses)")})

    # --- montant (HT, D2, strictement positif) ---------------------------------------------
    MONTANTS_VALIDES = ("0.01", "0.10", "0.99", "1.00", "10.00", "12.25", "100.05", "1250.50", "35.90", "99999999.99", "1234567890.12")
    MONTANTS_INVALIDES = ("0.00", "0.0", "0", "", "1", "1.5", "1.234", "1.", ".50", "01.00", "001.00", "00.50", "-1.00", "-0.01", "+1.00",
                          "1,50", "1.2.50", "1e2", "1e2.00", "1a.00", "12abc.50", "1 5.00", " 1.00", "1.00 ", "1.00\n", "1.0O", "abc",
                          "1-5.00", "1_0.00", "1/2.00", "１.００", "NaN", "Inf")

    def test_INV_11_montants_valides_conserves_octet_pour_octet(self):
        for m in self.MONTANTS_VALIDES:
            with self.subTest(montant=m):
                i = self.dep(montant=m)
                self.assertEqual(self.un("SELECT montant, typeof(montant) FROM depenses WHERE id=?", i), (m, "text"))

    def test_INV_14_montant_nul_negatif_ou_mal_forme_refuse(self):
        for m in self.MONTANTS_INVALIDES:
            with self.subTest(montant=m):
                with self.assertRaises(sqlite3.IntegrityError) as cm:
                    self.dep(montant=m)
                self.assertNotIn("INV-", str(cm.exception))                       # contrainte de table, pas un trigger
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses")[0], 0)

    def test_INV_14_montant_corrige_vers_une_valeur_invalide_refuse(self):
        i = self.dep()
        for m in ("0.00", "-3.00", "1.5", "1.234", "abc", ""):
            with self.subTest(montant=m):
                self.refuse_check("UPDATE depenses SET montant=? WHERE id=?", m, i)
        self.assertEqual(self.un("SELECT montant FROM depenses WHERE id=?", i)[0], "12.50")

    def test_INV_14_montant_zero_est_la_seule_forme_nulle_acceptee_par_le_motif_de_base(self):
        """Le motif D2 de 004 (GLOB '[0-9]*.[0-9][0-9]', sans zéro de tête) accepte '0.00' ; seul `<> '0.00'` le refuse ici."""
        base = "(SELECT 1 WHERE ? GLOB '[0-9]*.[0-9][0-9]' AND ? NOT GLOB '*[^0-9.]*' AND ? NOT GLOB '*.*.*' AND ? NOT GLOB '0[0-9]*')"
        self.assertEqual(self.tous(f"SELECT {base}", "0.00", "0.00", "0.00", "0.00"), [(1,)])
        nuls = [m for m in ("0.00", "00.00", "0.000", "0.0", "-0.00", "000.00") if self.tous(f"SELECT {base}", m, m, m, m) == [(1,)]]
        self.assertEqual(nuls, ["0.00"])
        self.refuse_check("UPDATE depenses SET montant='0.00' WHERE id=?", self.dep())

    def test_T44_somme_en_centimes_entiers_exacte(self):
        """La somme est une règle de service (centimes entiers, jamais en flottant) : le SQL conserve le texte exact."""
        for m in ("0.10", "0.20"):
            self.dep(montant=m)
        self.assertEqual(self.un("SELECT SUM(CAST(REPLACE(montant, '.', '') AS INTEGER)) FROM depenses")[0], 30)
        self.assertNotEqual(0.10 + 0.20, 0.30)                                       # le flottant, lui, dérive

    def test_T44_representation_sqlite_regle_sql_regle_de_service_montant(self):
        """Trois niveaux distincts, sans prétendre que le SQL interdit ce qu'il ne peut pas interdire :
        1. représentation SQLite : colonne STRICT TEXT, un nombre est converti en texte AVANT les CHECK ;
        2. règle SQL : le texte converti doit respecter le motif D2 (2 décimales exactes, > 0) ;
        3. règle de service : refuser un REAL / un entier en entrée, le formater à 2 décimales, saisir en centimes entiers."""
        for valeur in (12.5, 12.0, 0.1, 5, 12):                                      # converti en '12.5', '12.0', '0.1', '5', '12' : refusé
            with self.subTest(valeur=valeur):
                self.refuse_check("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) "
                                  "VALUES ('DEP-00001-26', '2026-10-02', ?, ?, 'x')", valeur, self.cat)
        # comportement documenté : un REAL qui s'écrit exactement avec 2 décimales est converti en texte canonique puis accepté
        self.db.execute("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) "
                        "VALUES ('DEP-00002-26', '2026-10-02', ?, ?, 'x')", (12.25, self.cat))
        self.assertEqual(self.un("SELECT montant, typeof(montant) FROM depenses WHERE numero='DEP-00002-26'"), ("12.25", "text"))
        with self.assertRaises(sqlite3.IntegrityError):                              # un BLOB n'est jamais converti
            self.db.execute("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) "
                            "VALUES ('DEP-00003-26', '2026-10-02', ?, ?, 'x')", (b"12.25", self.cat))

    # --- date_depense ----------------------------------------------------------------
    DATES_VALIDES = ("2026-10-02", "2024-02-29", "2000-02-29", "2026-02-28", "2026-04-30", "2026-12-31", "2026-01-01",
                     "1999-12-31", "2100-01-01", "2026-06-15")
    DATES_INVALIDES = ("2026-02-30", "2026-02-29", "2100-02-29", "2026-13-01", "2026-00-10", "2026-10-00", "2026-04-31", "2026-11-31",
                       "26-10-02", "2026/10/02", "2026-1-02", "2026-10-2", "20261002", "", "2026-10-02 ", " 2026-10-02",
                       "2026-10-02T00:00:00Z", "2026-10-02 10:00:00", "2026-10-02T10:00", "abcd-ef-gh", "now", "0000-00-00")

    def test_INV_10_dates_valides_historiques_ou_du_jour(self):
        for d in self.DATES_VALIDES:
            with self.subTest(date=d):
                self.dep(date_depense=d)
        aujourdhui = self.un("SELECT date('now')")[0]
        i = self.dep(date_depense=aujourdhui)                                        # date du jour : le service la propose par défaut
        self.assertEqual(self.un("SELECT date_depense FROM depenses WHERE id=?", i)[0], aujourdhui)

    def test_INV_10_dates_invalides_refusees(self):
        for d in self.DATES_INVALIDES:
            with self.subTest(date=d):
                with self.assertRaises(sqlite3.IntegrityError) as cm:
                    self.db.execute("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) "
                                    "VALUES ('DEP-00001-26', ?, '1.00', ?, 'x')", (d, self.cat))
                self.assertNotIn("INV-", str(cm.exception))
        self.refuse_check("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) "
                          "VALUES ('DEP-00001-26', NULL, '1.00', ?, 'x')", self.cat)
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses")[0], 0)

    def test_INV_10_date_corrigee_vers_une_date_invalide_refusee(self):
        i = self.dep()
        for d in ("2026-02-30", "2026-13-01", "2026/10/02", "2026-10-02T00:00:00Z", "2026-1-02"):
            with self.subTest(date=d):
                self.refuse_check("UPDATE depenses SET date_depense=? WHERE id=?", d, i)
        self.refuse_inv("INV-23", "UPDATE depenses SET date_depense='' WHERE id=?", i)     # année vide != '26' : TR-01 parle avant les CHECK
        self.refuse("UPDATE depenses SET date_depense=NULL WHERE id=?", i)

    def test_INV_10_date_est_une_date_calendaire_reelle_et_non_un_simple_motif(self):
        """GLOB seul accepte '2026-02-30' ; date(x) IS x refuse les dates impossibles (mois 00/13, jour 00, 31 avril…)."""
        glob = "'2026-02-30' GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'"
        self.assertEqual(self.un(f"SELECT {glob}")[0], 1)
        self.assertNotEqual(self.un("SELECT date('2026-02-30')")[0], "2026-02-30")           # SQLite normalise (2026-03-02) : jamais égal à l'entrée
        self.assertIsNone(self.un("SELECT date('2026-13-01')")[0])
        self.assertIsNone(self.un("SELECT date('2026-00-10')")[0])                            # NULL : un CHECK « = » l'accepterait, d'où IS
        self.refuse_check("UPDATE depenses SET date_depense='2026-02-30' WHERE id=?", self.dep())

    def test_INV_201_une_seule_date_metier(self):
        colonnes = {r[1] for r in self.db.execute("PRAGMA table_info(depenses)")}
        self.assertEqual({c for c in colonnes if c.startswith("date")}, {"date_depense"})
        for absente in ("date_facture", "date_echeance", "date_paiement", "date_creation", "date_saisie"):
            self.assertNotIn(absente, colonnes)
        i = self.dep(date_depense="2026-01-05")
        c = self.un("SELECT created_at FROM depenses WHERE id=?", i)[0]
        self.assertNotEqual(c[:10], "2026-01-05")                                   # created_at est une donnée technique distincte
        self.dep(date_depense="2026-12-31")                                          # date postérieure à la création : acceptée

    # --- cancelled_at / motif_annulation ---------------------------------------------------
    def test_T44_annulation_date_et_motif_ensemble_ou_aucun(self):
        i = self.dep()
        self.refuse_check("UPDATE depenses SET cancelled_at=? WHERE id=?", TS2, i)
        self.refuse_check("UPDATE depenses SET motif_annulation='x' WHERE id=?", i)
        self.assertEqual(self.un("SELECT cancelled_at, motif_annulation FROM depenses WHERE id=?", i), (None, None))
        self.db.execute("UPDATE depenses SET cancelled_at=?, motif_annulation='x' WHERE id=?", (TS2, i))

    def test_T44_annulation_motif_vide_refuse(self):
        i = self.dep()
        self.refuse_check("UPDATE depenses SET cancelled_at=?, motif_annulation='' WHERE id=?", TS2, i)
        self.refuse_check("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description, cancelled_at, motif_annulation) "
                          "VALUES ('DEP-00099-26', '2026-10-02', '1.00', ?, 'x', ?, '')", self.cat, TS2)

    def test_T44_annulation_format_de_cancelled_at(self):
        i = self.dep()
        for v in ("2026-10-03", "2026-10-03T08:00:00Z", "2026-10-03 08:00:00.000", "2026-10-03T08:00:00.000", "hier",
                  "2026-10-03T08:00:00.0000Z", ""):
            with self.subTest(valeur=v):
                self.refuse_check("UPDATE depenses SET cancelled_at=?, motif_annulation='x' WHERE id=?", v, i)
        self.assertEqual(self.un("SELECT cancelled_at FROM depenses WHERE id=?", i)[0], None)
        self.db.execute("UPDATE depenses SET cancelled_at=?, motif_annulation='x' WHERE id=?", (TS, i))

    def test_T44_depense_creee_deja_annulee_n_est_pas_interdite_par_le_sql(self):
        """Une dépense naît active : c'est une règle de service (cadrage §1.5.5), aucun trigger BEFORE INSERT n'existe."""
        i = self.dep(cancelled_at=TS2, motif_annulation="m")
        self.assertIsNotNone(self.un("SELECT cancelled_at FROM depenses WHERE id=?", i)[0])
        insert_triggers = [r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='depenses' "
                                                         "AND sql LIKE '%BEFORE INSERT%'")]
        self.assertEqual(insert_triggers, [])


class Numerotation(Base):
    """INV-06, INV-20, INV-22, INV-23, INV-25, INV-179, D-54 : format DEP-nnnnn-yy, année de date_depense, unicité, conservation.
    La migration ne génère aucun numéro : elle protège sa validité et son immutabilité."""

    NUMEROS_INVALIDES = ("DEP-1-26", "DEP-0001-26", "DEP-000001-26", "DEP-100000-26", "dep-00001-26", "Dep-00001-26", "DEV-00001-26",
                         "BCD-00001-26", "FAC-00001-26", "DEP00001-26", "DEP-00001_26", "DEP-00001-2026", "DEP-00001-6",
                         "DEP-0000A-26", "DEP-00001-2A", "DEP-00001-26 ", " DEP-00001-26", "DEP-00001-26\n", "DEP-00001-26-01", "DEP-", "",
                         "DEP-00001-27", "DEP-00001-25", "DEP-00001-00", "DEP-00001-99")

    def test_INV_20_format_valide_avec_date_de_la_meme_annee(self):
        i = self.dep(numero="DEP-00001-26", date_depense="2026-03-01")
        self.assertEqual(self.un("SELECT numero FROM depenses WHERE id=?", i)[0], "DEP-00001-26")
        self.dep(numero="DEP-00002-26", date_depense="2026-12-31")
        self.dep(numero="DEP-12345-26", date_depense="2026-01-01")

    def test_INV_20_changement_d_annee_nouveau_numero_dans_la_nouvelle_annee(self):
        a = self.dep(numero="DEP-00001-26", date_depense="2026-12-31")
        b = self.dep(numero="DEP-00001-27", date_depense="2027-01-01")                # même rang, autre année : séquence par année
        self.assertEqual(self.tous("SELECT numero FROM depenses ORDER BY id"), [("DEP-00001-26",), ("DEP-00001-27",)])
        self.assertNotEqual(a, b)

    def test_INV_20_plusieurs_numeros_distincts(self):
        for n in range(1, 8):
            self.dep(numero=f"DEP-{n:05d}-26")
        self.assertEqual(self.un("SELECT COUNT(DISTINCT numero), COUNT(*) FROM depenses"), (7, 7))

    def test_INV_20_numeros_invalides_refuses(self):
        for numero in self.NUMEROS_INVALIDES:
            with self.subTest(numero=numero):
                with self.assertRaises(sqlite3.IntegrityError) as cm:
                    self.db.execute("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) "
                                    "VALUES (?, '2026-10-02', '1.00', ?, 'x')", (numero, self.cat))
                self.assertNotIn("INV-", str(cm.exception))
        self.refuse_check("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) "
                          "VALUES (NULL, '2026-10-02', '1.00', ?, 'x')", self.cat)
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses")[0], 0)

    def test_INV_23_annee_du_numero_egale_celle_de_date_depense_pour_toutes_les_annees(self):
        """Pour chaque yy de 00 à 99 : numéro et date de la même année acceptés, année différente refusée (CHECK)."""
        for yy in range(0, 100):
            y = 1900 + yy if yy >= 50 else 2000 + yy
            autre = (yy + 1) % 100
            with self.subTest(yy=yy):
                self.dep(numero=f"DEP-{yy + 1:05d}-{yy:02d}", date_depense=f"{y}-06-15")
                self.refuse_check("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) "
                                  "VALUES (?, ?, '1.00', ?, 'x')", f"DEP-00500-{autre:02d}", f"{y}-06-15", self.cat)
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses")[0], 100)

    def test_INV_23_annee_du_numero_n_est_pas_l_annee_courante(self):
        self.dep(numero="DEP-00001-24", date_depense="2024-03-01")                    # saisie historique
        self.refuse_check("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) "
                          "VALUES ('DEP-00002-26', '2024-03-01', '1.00', ?, 'x')", self.cat)

    def test_INV_20_bornes_du_motif_00000_et_99999(self):
        self.dep(numero="DEP-00000-26")                                               # accepté par le motif, comme BCD-00000-yy
        self.dep(numero="DEP-99999-26")
        self.refuse_check("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) "
                          "VALUES ('DEP-100000-26', '2026-10-02', '1.00', ?, 'x')", self.cat)

    def test_INV_22_doublon_refuse_meme_apres_annulation(self):
        i = self.dep(numero="DEP-00001-26")
        self.annuler(i)
        self.refuse_check("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) "
                          "VALUES ('DEP-00001-26', '2026-10-02', '1.00', ?, 'Reprise')", self.cat)
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses")[0], 1)

    def test_INV_06_numero_conserve_apres_annulation(self):
        i = self.dep(numero="DEP-00042-26", bc_id=self.bc_en_etat("en_cours"), fournisseur_id=self.f1)
        avant = self.ligne(i)
        self.annuler(i)
        self.assertEqual(self.un("SELECT numero FROM depenses WHERE id=?", i)[0], "DEP-00042-26")
        apres = self.ligne(i)
        for c in ("id", "numero", "fournisseur_id", "bc_id", "date_depense", "montant", "categorie_id", "description", "created_at"):
            self.assertEqual(apres[COLONNES_DEPENSES.index(c)], avant[COLONNES_DEPENSES.index(c)], c)

    def test_INV_179_numero_jamais_reutilisable(self):
        """Le numéro d'une dépense annulée ou perdue reste pris : ni DELETE, ni REPLACE, ni nouvelle insertion ne le libèrent."""
        i = self.dep(numero="DEP-00001-26")
        self.annuler(i)
        self.refuse_inv("INV-06", "DELETE FROM depenses WHERE id=?", i)
        self.refuse_inv("INV-06", "INSERT OR REPLACE INTO depenses (numero, date_depense, montant, categorie_id, description) "
                                  "VALUES ('DEP-00001-26', '2026-10-02', '1.00', ?, 'x')", self.cat)
        self.refuse_check("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) "
                          "VALUES ('DEP-00001-26', '2026-10-02', '1.00', ?, 'x')", self.cat)
        self.assertEqual(self.tous("SELECT numero, cancelled_at IS NOT NULL FROM depenses"), [("DEP-00001-26", 1)])

    def test_INV_179_trou_de_numerotation_accepte(self):
        self.dep(numero="DEP-00001-26")
        self.dep(numero="DEP-00003-26")                                              # DEP-00002-26 perdu (crash, rollback, annulation)
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses WHERE numero='DEP-00002-26'")[0], 0)
        self.dep(numero="DEP-00002-26")                                              # le SQL ne l'interdit pas : le service ne le réattribue pas

    def test_INV_25_sequence_dep_par_annee_attribuee_par_le_service(self):
        """Reproduction du service (modèle §4.17, PT-1) : la séquence DEP de numerotation_sequences, une ligne par année."""
        self.assertEqual([self.un(ATTRIBUER, "DEP", 26)[0] for _ in range(3)], [1, 2, 3])
        self.assertEqual(self.un(ATTRIBUER, "DEP", 27)[0], 1)
        self.assertEqual(self.un(ATTRIBUER, "DEP", 26)[0], 4)
        numero = f"DEP-{self.un(ATTRIBUER, 'DEP', 26)[0]:05d}-26"
        self.assertEqual(numero, "DEP-00005-26")
        self.dep(numero=numero)
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='DEP' AND annee=26")[0], 5)

    def test_INV_25_la_sequence_dep_n_est_pas_ecrite_par_la_migration(self):
        db = migrer()
        self.assertEqual(db.execute("SELECT COUNT(*) FROM numerotation_sequences").fetchone()[0], 0)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM depenses").fetchone()[0], 0)
        code = sans_commentaires(SQL_005)
        self.assertNotRegex(code, r"(?i)numerotation_sequences|dernier_numero|\bMAX\s*\(|\bCOUNT\s*\(")
        # le numéro n'a aucun défaut : il ne peut pas être produit par la table
        self.assertIsNone(self.un("SELECT dflt_value FROM pragma_table_info('depenses') WHERE name='numero'")[0])
        self.refuse_check("INSERT INTO depenses (date_depense, montant, categorie_id, description) VALUES ('2026-10-02', '1.00', ?, 'x')", self.cat)

    def test_INV_25_type_dep_dans_numerotation_sequences_controle_par_001(self):
        self.un(ATTRIBUER, "DEP", 26)
        self.refuse_check("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('DEP', 0, 1)")    # annee 0 réservé CLI/FOU
        self.refuse_check("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('DEP', 100, 1)")
        self.refuse_inv("INV-22", "UPDATE numerotation_sequences SET dernier_numero = 0 WHERE type_objet='DEP'")           # TR-95 : ne diminue jamais
        self.refuse_inv("INV-22", "DELETE FROM numerotation_sequences WHERE type_objet='DEP'")                             # TR-96
        self.refuse_inv("INV-22", "INSERT OR REPLACE INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('DEP', 26, 1)")
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='DEP'")[0], 1)

    def test_INV_25_la_sequence_dep_est_independante_des_autres_types(self):
        self.un(ATTRIBUER, "BCD", 26)
        self.un(ATTRIBUER, "DEV", 26)
        self.assertEqual(self.un(ATTRIBUER, "DEP", 26)[0], 1)
        self.assertEqual(self.un(ATTRIBUER, "BCD", 26)[0], 2)


class ImmutabiliteNumero(Base):
    """TR-01 [INV-23] : numero immuable ; l'année (yy) de date_depense ne change jamais ; la date peut changer dans la même année."""

    def test_INV_23_numero_immuable(self):
        i = self.dep(numero="DEP-00001-26")
        self.refuse_inv("INV-23", "UPDATE depenses SET numero='DEP-00002-26' WHERE id=?", i)
        self.refuse_inv("INV-23", "UPDATE depenses SET numero='DEP-00001-27' WHERE id=?", i)
        self.refuse_inv("INV-23", "UPDATE depenses SET numero='dep-00001-26' WHERE id=?", i)
        self.refuse_inv("INV-23", "UPDATE depenses SET numero=NULL WHERE id=?", i)                 # TR-01 avant NOT NULL
        self.assertEqual(self.un("SELECT numero FROM depenses WHERE id=?", i)[0], "DEP-00001-26")

    def test_INV_23_numero_inchange_accepte(self):
        i = self.dep(numero="DEP-00001-26")
        self.db.execute("UPDATE depenses SET numero=numero, montant='9.99' WHERE id=?", (i,))
        self.db.execute("UPDATE depenses SET numero='DEP-00001-26' WHERE id=?", (i,))

    def test_INV_23_correction_de_date_dans_la_meme_annee_acceptee(self):
        i = self.dep(numero="DEP-00001-26", date_depense="2026-10-02")
        for d in ("2026-01-01", "2026-12-31", "2026-02-28", "2026-10-02"):
            with self.subTest(date=d):
                self.db.execute("UPDATE depenses SET date_depense=? WHERE id=?", (d, i))
                self.assertEqual(self.un("SELECT date_depense, numero FROM depenses WHERE id=?", i), (d, "DEP-00001-26"))

    def test_INV_23_correction_de_date_vers_une_autre_annee_refusee_sans_renumerotation(self):
        i = self.dep(numero="DEP-00001-26", date_depense="2026-10-02")
        for d in ("2025-10-02", "2027-01-01", "2025-12-31", "2036-10-02", "2016-10-02"):
            with self.subTest(date=d):
                self.refuse_inv("INV-23", "UPDATE depenses SET date_depense=? WHERE id=?", d, i)
        self.assertEqual(self.un("SELECT date_depense, numero FROM depenses WHERE id=?", i), ("2026-10-02", "DEP-00001-26"))

    def test_INV_23_le_numero_ne_porte_que_deux_chiffres_d_annee_siecle_hors_perimetre_sql(self):
        """Comportement documenté, non modifié : le numéro DEP-nnnnn-yy ne porte que yy ; TR-01 et le CHECK comparent donc yy.
        Un autre siècle de même yy (1926 / 2126) n'est pas distinguable en SQL ; la borne d'année 2001-2099 (D-38) est une règle de
        SERVICE. Dans cette borne, yy identifie l'année sans ambiguïté."""
        i = self.dep(numero="DEP-00001-26", date_depense="2026-10-02")
        self.db.execute("UPDATE depenses SET date_depense='1926-10-02' WHERE id=?", (i,))
        self.assertEqual(self.un("SELECT date_depense, numero FROM depenses WHERE id=?", i), ("1926-10-02", "DEP-00001-26"))
        self.refuse_inv("INV-23", "UPDATE depenses SET date_depense='1927-10-02' WHERE id=?", i)

    def test_INV_23_numero_et_date_modifies_ensemble_refuses(self):
        """Pas de renumérotation SQL : même un couple numéro / date cohérent pour une autre année est refusé."""
        i = self.dep(numero="DEP-00001-26", date_depense="2026-10-02")
        self.refuse_inv("INV-23", "UPDATE depenses SET numero='DEP-00001-25', date_depense='2025-10-02' WHERE id=?", i)
        self.refuse_inv("INV-23", "UPDATE depenses SET numero='DEP-00007-26', date_depense='2026-11-02' WHERE id=?", i)

    def test_INV_23_date_invalide_vers_autre_annee_refusee_par_le_trigger_avant_le_check(self):
        i = self.dep(numero="DEP-00001-26", date_depense="2026-10-02")
        self.refuse_inv("INV-23", "UPDATE depenses SET date_depense='2025-02-30' WHERE id=?", i)   # BEFORE : avant les CHECK

    def test_INV_23_autres_colonnes_modifiables_avec_le_trigger_actif(self):
        i = self.dep()
        self.db.execute("UPDATE depenses SET montant='1.00', description='d', notes='n', updated_at=? WHERE id=?", (TS2, i))
        self.assertEqual(self.un("SELECT montant, description, notes, updated_at FROM depenses WHERE id=?", i), ("1.00", "d", "n", TS2))

    def test_INV_23_message_et_invariant_de_tr01(self):
        sql = self.un("SELECT sql FROM sqlite_master WHERE name='tr_01_depenses_numero_immuable'")[0]
        self.assertIn("INV-23: depenses.numero et l''annee de depenses.date_depense sont immuables", sql)
        i = self.dep()
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.db.execute("UPDATE depenses SET numero='DEP-00009-26' WHERE id=?", (i,))
        self.assertEqual(str(cm.exception), "INV-23: depenses.numero et l'annee de depenses.date_depense sont immuables")

    def test_INV_23_upsert_ne_contourne_pas_tr01(self):
        i = self.dep(numero="DEP-00001-26")
        self.refuse_inv("INV-23", "INSERT INTO depenses (id, numero, date_depense, montant, categorie_id, description) "
                                  "VALUES (?, 'DEP-00002-26', '2026-02-02', '1.00', ?, 'z') ON CONFLICT(id) DO UPDATE SET numero=excluded.numero",
                        i, self.cat)
        self.assertEqual(self.un("SELECT numero FROM depenses WHERE id=?", i)[0], "DEP-00001-26")


class Fournisseur(Base):
    """INV-05, INV-100, INV-183 : fournisseur facultatif, par identifiant ; Dépenses ne dépend jamais de fournisseurs.statut."""

    def test_INV_100_depense_sans_fournisseur(self):
        i = self.dep()
        self.assertIsNone(self.un("SELECT fournisseur_id FROM depenses WHERE id=?", i)[0])
        j = self.dep(fournisseur_id=None)
        self.assertIsNone(self.un("SELECT fournisseur_id FROM depenses WHERE id=?", j)[0])

    def test_INV_100_depense_avec_fournisseur_valide(self):
        i = self.dep(fournisseur_id=self.f1)
        self.assertEqual(self.un("SELECT fournisseur_id FROM depenses WHERE id=?", i)[0], self.f1)

    def test_INV_05_fournisseur_inexistant_refuse(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):
            self.dep(fournisseur_id=999999)
        i = self.dep()
        self.refuse_check("UPDATE depenses SET fournisseur_id=999999 WHERE id=?", i)
        self.refuse_check("UPDATE depenses SET fournisseur_id=0 WHERE id=?", i)
        self.assertIsNone(self.un("SELECT fournisseur_id FROM depenses WHERE id=?", i)[0])

    def test_INV_198_dependance_active_changer_ajouter_retirer_le_fournisseur(self):
        i = self.dep()
        for cible in (self.f1, self.f2, None, self.f1):
            with self.subTest(cible=cible):
                self.db.execute("UPDATE depenses SET fournisseur_id=?, updated_at=? WHERE id=?", (cible, TS2, i))
                self.assertEqual(self.un("SELECT fournisseur_id FROM depenses WHERE id=?", i)[0], cible)

    def test_INV_198_retrait_du_fournisseur_d_une_depense_active(self):
        i = self.dep(fournisseur_id=self.f1)
        self.db.execute("UPDATE depenses SET fournisseur_id=NULL WHERE id=?", (i,))
        self.assertIsNone(self.un("SELECT fournisseur_id FROM depenses WHERE id=?", i)[0])
        self.assertEqual(self.un("SELECT COUNT(*) FROM fournisseurs WHERE id=?", self.f1)[0], 1)          # le fournisseur est intact

    def test_INV_183_lien_historique_conserve_et_fournisseur_non_supprimable(self):
        i = self.dep(fournisseur_id=self.f1)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):
            self.db.execute("DELETE FROM fournisseurs WHERE id=?", (self.f1,))
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):
            self.db.execute("UPDATE fournisseurs SET id=? WHERE id=?", (777, self.f1))
        self.assertEqual(self.un("SELECT fournisseur_id FROM depenses WHERE id=?", i)[0], self.f1)
        self.db.execute("UPDATE fournisseurs SET nom='Nouveau nom' WHERE id=?", (self.f1,))               # données modifiables, lien intact
        self.assertEqual(self.un("SELECT fournisseur_id FROM depenses WHERE id=?", i)[0], self.f1)
        libre = self.fournisseur()
        self.db.execute("DELETE FROM fournisseurs WHERE id=?", (libre,))                                  # aucun CASCADE : seul un fournisseur libre se supprime
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses")[0], 1)

    def test_INV_183_aucune_dependance_a_fournisseurs_statut(self):
        """Quel que soit le statut du fournisseur (valeur imposée par 002), le SQL de Dépenses l'accepte et ne le lit jamais."""
        for statut, f in (("actif", self.f1), ("archive", self.f2)):
            with self.subTest(statut=statut):
                i = self.dep(fournisseur_id=f)
                self.db.execute("UPDATE depenses SET montant='7.00' WHERE id=?", (i,))
        i = self.dep(fournisseur_id=self.f1)
        self.db.execute("UPDATE fournisseurs SET statut='archive' WHERE id=?", (self.f1,))                # archivé après coup
        self.db.execute("UPDATE depenses SET montant='8.00', description='corrigée' WHERE id=?", (i,))
        self.db.execute("UPDATE fournisseurs SET statut='actif' WHERE id=?", (self.f1,))
        self.db.execute("UPDATE depenses SET fournisseur_id=? WHERE id=?", (self.f2, i))                  # vers un fournisseur 'archive'
        sql = sans_commentaires(SQL_005)
        self.assertNotIn("statut", sql)
        for nom in TRIGGERS_005 | {"depenses"}:
            self.assertNotIn("statut", self.un("SELECT sql FROM sqlite_master WHERE name=?", nom)[0])

    def test_INV_183_preuve_d_independance_le_retrait_de_la_colonne_statut_ne_change_rien(self):
        """Dans la connexion de test uniquement (aucun fichier, aucune migration) : sans fournisseurs.statut, Dépenses fonctionne
        à l'identique. Le retrait suit l'ordre DROP INDEX puis DROP COLUMN ; fournisseurs n'est pas reconstruite."""
        i = self.dep(fournisseur_id=self.f1)
        self.db.execute("DROP INDEX idx_fournisseurs_statut")
        self.db.execute("ALTER TABLE fournisseurs DROP COLUMN statut")
        self.assertNotIn("statut", {r[1] for r in self.db.execute("PRAGMA table_info(fournisseurs)")})
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(self.un("SELECT fournisseur_id FROM depenses WHERE id=?", i)[0], self.f1)
        j = self.dep(fournisseur_id=self.f2)
        self.db.execute("UPDATE depenses SET fournisseur_id=NULL WHERE id=?", (j,))
        self.db.execute("UPDATE depenses SET fournisseur_id=? WHERE id=?", (self.f2, j))
        self.refuse_check("UPDATE depenses SET fournisseur_id=999999 WHERE id=?", j)
        self.refuse_check("DELETE FROM fournisseurs WHERE id=?", self.f1)
        self.annuler(j)
        self.refuse_inv("INV-197", "UPDATE depenses SET notes='x' WHERE id=?", j)

    def test_INV_197_fournisseur_d_une_depense_annulee_fige(self):
        i = self.dep(fournisseur_id=self.f1)
        self.annuler(i)
        for cible in (self.f2, None):
            self.refuse_inv("INV-197", "UPDATE depenses SET fournisseur_id=? WHERE id=?", cible, i)
        self.assertEqual(self.un("SELECT fournisseur_id FROM depenses WHERE id=?", i)[0], self.f1)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):                            # le lien historique protège encore le fournisseur
            self.db.execute("DELETE FROM fournisseurs WHERE id=?", (self.f1,))


class Categorie(Base):
    """INV-05 : catégorie obligatoire, FK RESTRICT. La catégorie inactive est une règle de SERVICE (DV-11) : aucun test SQL ne l'exige."""

    def test_T44_categorie_valide(self):
        i = self.dep()
        self.assertEqual(self.un("SELECT categorie_id FROM depenses WHERE id=?", i)[0], self.cat)

    def test_INV_05_categorie_inexistante_refusee(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):
            self.dep(categorie_id=999999)
        i = self.dep()
        self.refuse_check("UPDATE depenses SET categorie_id=999999 WHERE id=?", i)
        self.refuse_check("UPDATE depenses SET categorie_id=0 WHERE id=?", i)
        self.assertEqual(self.un("SELECT categorie_id FROM depenses WHERE id=?", i)[0], self.cat)

    def test_T44_categorie_obligatoire_NULL_refuse(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, "NOT NULL"):
            self.db.execute("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) "
                            "VALUES ('DEP-00001-26', '2026-10-02', '1.00', NULL, 'x')")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "NOT NULL"):
            self.db.execute("INSERT INTO depenses (numero, date_depense, montant, description) VALUES ('DEP-00001-26', '2026-10-02', '1.00', 'x')")
        i = self.dep()
        self.refuse_check("UPDATE depenses SET categorie_id=NULL WHERE id=?", i)

    def test_INV_198_modification_de_categorie_d_une_depense_active(self):
        autre = self.categorie("AUT")
        i = self.dep()
        self.db.execute("UPDATE depenses SET categorie_id=?, updated_at=? WHERE id=?", (autre, TS2, i))
        self.assertEqual(self.un("SELECT categorie_id FROM depenses WHERE id=?", i)[0], autre)

    def test_INV_05_categorie_utilisee_non_supprimable_lien_historique_conserve(self):
        autre = self.categorie("AUT")
        i = self.dep(categorie_id=autre)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):
            self.db.execute("DELETE FROM categories_depenses WHERE id=?", (autre,))
        libre = self.categorie("LIB")
        self.db.execute("DELETE FROM categories_depenses WHERE id=?", (libre,))                        # aucun CASCADE : seule une catégorie libre se supprime
        self.assertEqual(self.un("SELECT categorie_id FROM depenses WHERE id=?", i)[0], autre)

    def test_T44_categorie_inactive_regle_de_service_le_sql_n_impose_rien(self):
        """DV-11 : une catégorie inactive n'est pas sélectionnable pour une nouvelle dépense ni comme cible d'une correction — contrôle
        de SERVICE (conventions §9 : aucun CHECK ni trigger inter-tables). Le SQL n'interdit rien et conserve le lien historique."""
        inactive = self.categorie("OLD", actif=0)
        i = self.dep(categorie_id=self.cat)
        self.db.execute("UPDATE categories_depenses SET actif=0 WHERE id=?", (self.cat,))              # catégorie désactivée après coup
        self.assertEqual(self.un("SELECT categorie_id FROM depenses WHERE id=?", i)[0], self.cat)        # lien historique conservé
        self.db.execute("UPDATE depenses SET montant='3.00' WHERE id=?", (i,))                          # dépense toujours consultable et modifiable
        self.assertNotRegex(sans_commentaires(SQL_005), r"\bactif\b")
        self.dep(categorie_id=inactive)                                                                # n'est pas refusé par le SQL (service)


class Bc(Base):
    """INV-05, INV-100, INV-103, INV-188, INV-198, INV-199 : BC facultatif ; un BC annulé reste une cible valide (création et
    rattachement ultérieur). La règle des 30 jours est une règle de service : le SQL ne la contrôle pas."""

    def test_INV_100_depense_globale_sans_bc(self):
        i = self.dep()
        self.assertIsNone(self.un("SELECT bc_id FROM depenses WHERE id=?", i)[0])
        self.assertIsNone(self.un("SELECT bc_id FROM depenses WHERE id=?", self.dep(bc_id=None))[0])

    def test_INV_199_creation_sur_un_bc_dans_chaque_etat(self):
        for etat in ETATS_BC:
            with self.subTest(etat=etat):
                b = self.bc_en_etat(etat)
                i = self.dep(bc_id=b)
                self.assertEqual(self.un("SELECT bc_id FROM depenses WHERE id=?", i)[0], b)
        self.assertEqual(self.tous("SELECT statut FROM bons_commande ORDER BY id"),
                         [("en_cours",), ("en_cours",), ("termine",), ("annule",), ("annule",)])      # 'gele' n'est pas un statut (gel = frozen_at)

    def test_INV_188_creation_d_une_depense_sur_un_bc_annule_acceptee(self):
        b = self.bc_en_etat("annule")
        i = self.dep(bc_id=b)
        self.assertEqual(self.un("SELECT bc_id FROM depenses WHERE id=?", i)[0], b)
        self.assertEqual(self.un("SELECT statut FROM bons_commande WHERE id=?", b)[0], "annule")
        for etat in ("annule", "annule_gele"):
            self.dep(bc_id=self.bc_en_etat(etat), fournisseur_id=self.f1)

    def test_INV_188_rattachement_ulterieur_d_une_depense_existante_a_un_bc_annule_accepte(self):
        b = self.bc_en_etat("annule")
        i = self.dep()
        self.db.execute("UPDATE depenses SET bc_id=?, updated_at=? WHERE id=?", (b, TS2, i))
        self.assertEqual(self.un("SELECT bc_id FROM depenses WHERE id=?", i)[0], b)
        j = self.dep(bc_id=self.bc_en_etat("en_cours"))
        self.db.execute("UPDATE depenses SET bc_id=? WHERE id=?", (b, j))                               # changement vers un BC annulé
        self.assertEqual(self.un("SELECT bc_id FROM depenses WHERE id=?", j)[0], b)

    def test_INV_199_aucune_contrainte_ni_trigger_ne_depend_de_l_etat_du_bc(self):
        for nom in TRIGGERS_005 | {"depenses"}:
            sql = self.un("SELECT sql FROM sqlite_master WHERE name=?", nom)[0]
            self.assertNotRegex(re.sub(r"'(?:[^']|'')*'", "''", sql), r"(?i)bons_commande\b(?!\s*\()|\bstatut\b|\bannule\b|\btermine\b", nom)

    def test_INV_103_regle_des_30_jours_n_est_pas_une_contrainte_sql(self):
        """Le SQL ne compare jamais date_depense à date_100_facture : toute combinaison de dates est acceptée (règle de service)."""
        b = self.bc_en_etat("termine")                                                                  # date_100_facture = 2026-10-02
        self.assertEqual(self.un("SELECT date_100_facture FROM bons_commande WHERE id=?", b)[0], "2026-10-02")
        for d in ("2026-10-02", "2026-10-30", "2026-11-01", "2026-12-31", "2026-01-01"):                # <= 30 jours, > 30 jours, avant la clôture
            with self.subTest(date_depense=d):
                self.dep(bc_id=b, date_depense=d)
        ba = self.bc_en_etat("annule")
        self.assertIsNone(self.un("SELECT date_100_facture FROM bons_commande WHERE id=?", ba)[0])
        self.dep(bc_id=ba, date_depense="2026-12-31")                                                   # BC annulé : aucune contrainte temporelle
        self.dep(bc_id=ba, date_depense="2026-01-01")
        code = re.sub(r"'(?:[^']|'')*'", "''", sans_commentaires(SQL_005))
        self.assertNotIn("date_100_facture", code)
        self.assertEqual([r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='depenses'")
                          if "julianday" in (self.un("SELECT sql FROM sqlite_master WHERE name=?", r[0])[0] or "")], [])

    def test_INV_05_bc_inexistant_refuse(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):
            self.dep(bc_id=999999)
        i = self.dep()
        self.refuse_check("UPDATE depenses SET bc_id=999999 WHERE id=?", i)
        self.refuse_check("UPDATE depenses SET bc_id=0 WHERE id=?", i)
        self.assertIsNone(self.un("SELECT bc_id FROM depenses WHERE id=?", i)[0])

    def test_INV_198_changement_de_bc_detachement_et_passage_globale_bc(self):
        b1, b2 = self.bc_en_etat("en_cours"), self.bc_en_etat("termine")
        i = self.dep()
        for cible in (b1, b2, None, b1, None):                                                          # globale -> BC -> BC -> globale -> BC -> globale
            with self.subTest(cible=cible):
                self.db.execute("UPDATE depenses SET bc_id=?, updated_at=? WHERE id=?", (cible, TS2, i))
                self.assertEqual(self.un("SELECT bc_id FROM depenses WHERE id=?", i)[0], cible)

    def test_INV_198_modification_sans_changer_de_bc_n_est_pas_un_rattachement(self):
        b = self.bc_en_etat("termine")
        i = self.dep(bc_id=b, date_depense="2026-12-31")                                                 # plus de 30 jours après la clôture
        self.db.execute("UPDATE depenses SET montant='99.00', description='corrigée' WHERE id=?", (i,))  # aucune nouvelle vérification de délai
        self.db.execute("UPDATE depenses SET bc_id=bc_id WHERE id=?", (i,))
        self.assertEqual(self.un("SELECT bc_id, montant FROM depenses WHERE id=?", i), (b, "99.00"))

    def test_INV_188_annulation_du_bc_apres_rattachement_n_affecte_pas_la_depense(self):
        b = self.bc_en_etat("en_cours")
        i = self.dep(bc_id=b, fournisseur_id=self.f1)
        avant = self.ligne(i)
        self.annuler_bc(b)
        self.assertEqual(self.ligne(i), avant)                                                          # le lien reste, aucune cascade
        self.db.execute("UPDATE depenses SET montant='5.00' WHERE id=?", (i,))                          # la dépense reste active et corrigeable

    def test_INV_193_depense_active_ou_annulee_conserve_le_lien_vers_un_bc_annule(self):
        b = self.bc_en_etat("annule")
        i = self.dep(bc_id=b)
        self.annuler(i)
        self.assertEqual(self.un("SELECT bc_id FROM depenses WHERE id=?", i)[0], b)

    def test_INV_05_bc_reference_jamais_supprimable(self):
        for etat in ETATS_BC:
            with self.subTest(etat=etat):
                b = self.bc_en_etat(etat)
                self.dep(bc_id=b)
                self.refuse("DELETE FROM bons_commande WHERE id=?", b)                                   # tr_19 (INV-174) et FK RESTRICT
                self.assertEqual(self.un("SELECT COUNT(*) FROM bons_commande WHERE id=?", b)[0], 1)

    def test_INV_05_la_fk_vers_bons_commande_est_une_garde_independante_du_trigger_tr19(self):
        t = Base(); t.setUp()
        t.db.execute("DROP TRIGGER tr_19_bons_commande_no_delete")
        b = t.creer_bc()
        i = t.dep(bc_id=b)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):                              # depenses.bc_id en RESTRICT (et non CASCADE / SET NULL)
            t.db.execute("DELETE FROM bons_commande WHERE id=?", (b,))
        self.assertEqual(t.un("SELECT bc_id FROM depenses WHERE id=?", i)[0], b)

    def test_INV_188_perimetre_des_triggers_de_004_ne_voit_pas_les_depenses(self):
        """Une dépense n'écrit rien dans bons_commande : créer, rattacher, détacher ou annuler une dépense ne touche pas au BC."""
        b = self.bc_en_etat("annule")
        avant = self.un("SELECT * FROM bons_commande WHERE id=?", b)
        i = self.dep(bc_id=b)
        self.db.execute("UPDATE depenses SET bc_id=NULL WHERE id=?", (i,))
        self.db.execute("UPDATE depenses SET bc_id=? WHERE id=?", (b, i))
        self.annuler(i)
        self.assertEqual(self.un("SELECT * FROM bons_commande WHERE id=?", b), avant)


class Annulation(Base):
    """INV-06, INV-193, INV-197, INV-200 : annulation par cancelled_at + motif_annulation, sans statut ; conservation de l'objet."""

    def test_INV_193_annulation_d_une_depense_active(self):
        b = self.bc_en_etat("en_cours")
        i = self.dep(bc_id=b, fournisseur_id=self.f1, notes="n", piece_jointe_chemin="a/b", piece_jointe_racine_id=2)
        avant = self.ligne(i)
        self.db.execute("UPDATE depenses SET cancelled_at=?, motif_annulation=?, updated_at=? WHERE id=?", (TS2, "Doublon", TS2, i))
        apres = self.ligne(i)
        self.assertEqual(apres[COLONNES_DEPENSES.index("cancelled_at")], TS2)
        self.assertEqual(apres[COLONNES_DEPENSES.index("motif_annulation")], "Doublon")
        for c in COLONNES_DEPENSES:                                                                       # toutes les autres données sont conservées
            if c not in ("cancelled_at", "motif_annulation", "updated_at"):
                self.assertEqual(apres[COLONNES_DEPENSES.index(c)], avant[COLONNES_DEPENSES.index(c)], c)
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses WHERE id=?", i)[0], 1)                    # l'objet est toujours présent

    def test_INV_193_annulation_sans_modifier_updated_at_acceptee(self):
        i = self.dep()
        self.db.execute("UPDATE depenses SET cancelled_at=?, motif_annulation='x' WHERE id=?", (TS2, i))

    def test_INV_193_active_se_reconnait_a_l_absence_de_cancelled_at(self):
        a, b = self.dep(), self.dep()
        self.annuler(b)
        self.assertEqual(self.tous("SELECT id FROM depenses WHERE cancelled_at IS NULL"), [(a,)])
        self.assertEqual(self.tous("SELECT id FROM depenses WHERE cancelled_at IS NOT NULL"), [(b,)])
        self.assertNotIn("statut", {r[1] for r in self.db.execute("PRAGMA table_info(depenses)")})

    def test_INV_200_depense_annulee_exclue_des_calculs_actifs_par_un_filtre_de_requete(self):
        """Le filtre `cancelled_at IS NULL` suffit ; aucun total n'est stocké (aucune colonne de cache sur bons_commande)."""
        b = self.bc_en_etat("en_cours")
        self.dep(bc_id=b, montant="10.00")
        i = self.dep(bc_id=b, montant="5.50")
        self.annuler(i)
        total = self.un("SELECT SUM(CAST(REPLACE(montant, '.', '') AS INTEGER)) FROM depenses WHERE bc_id=? AND cancelled_at IS NULL", b)[0]
        self.assertEqual(total, 1000)
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses WHERE bc_id=?", b)[0], 2)                  # la dépense annulée reste consultable

    def test_T44_annulation_invalides(self):
        i = self.dep()
        self.refuse_check("UPDATE depenses SET cancelled_at=? WHERE id=?", TS2, i)                          # date seule
        self.refuse_check("UPDATE depenses SET motif_annulation='x' WHERE id=?", i)                         # motif seul
        self.refuse_check("UPDATE depenses SET cancelled_at=?, motif_annulation='' WHERE id=?", TS2, i)    # motif vide
        self.refuse_check("UPDATE depenses SET cancelled_at='n''importe quoi', motif_annulation='x' WHERE id=?", i)   # date invalide
        self.refuse_check("UPDATE depenses SET cancelled_at=?, motif_annulation=NULL WHERE id=?", TS2, i)
        self.assertEqual(self.un("SELECT cancelled_at, motif_annulation FROM depenses WHERE id=?", i), (None, None))

    def test_INV_193_annulation_irreversible_aucune_reactivation(self):
        i = self.dep()
        self.annuler(i)
        self.refuse_inv("INV-197", "UPDATE depenses SET cancelled_at=NULL, motif_annulation=NULL WHERE id=?", i)
        self.refuse_inv("INV-197", "UPDATE depenses SET cancelled_at=NULL, motif_annulation=NULL, updated_at=? WHERE id=?", "2031-01-01T00:00:00.000Z", i)
        self.refuse_inv("INV-197", "UPDATE depenses SET cancelled_at=NULL WHERE id=?", i)
        self.refuse_inv("INV-197", "UPDATE depenses SET motif_annulation=NULL WHERE id=?", i)
        self.assertEqual(self.un("SELECT cancelled_at, motif_annulation FROM depenses WHERE id=?", i), (TS2, "Erreur de saisie"))

    def test_INV_193_nouvelle_annulation_d_une_depense_annulee_refusee(self):
        i = self.dep()
        self.annuler(i)
        self.refuse_inv("INV-197", "UPDATE depenses SET cancelled_at=?, motif_annulation='bis' WHERE id=?", "2031-01-01T00:00:00.000Z", i)
        self.assertEqual(self.un("SELECT motif_annulation FROM depenses WHERE id=?", i)[0], "Erreur de saisie")

    def test_INV_193_ressaisie_apres_annulation_est_un_nouvel_objet_au_nouveau_numero(self):
        a = self.dep(numero="DEP-00001-26")
        self.annuler(a)
        b = self.dep(numero="DEP-00002-26", date_depense="2026-10-02", montant="12.50")                    # nouvelle saisie : nouvel id, nouveau numéro
        self.assertNotEqual(a, b)
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses WHERE cancelled_at IS NULL")[0], 1)
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses")[0], 2)

    def test_INV_193_erreur_d_annee_se_regle_par_annulation_puis_nouvelle_saisie(self):
        a = self.dep(numero="DEP-00001-26", date_depense="2026-12-31")
        self.refuse_inv("INV-23", "UPDATE depenses SET date_depense='2027-01-01' WHERE id=?", a)         # pas de renumérotation
        self.annuler(a, motif="Mauvaise année")
        b = self.dep(numero="DEP-00001-27", date_depense="2027-01-01")
        self.assertEqual(self.tous("SELECT numero, cancelled_at IS NOT NULL FROM depenses ORDER BY id"),
                         [("DEP-00001-26", 1), ("DEP-00001-27", 0)])
        self.assertGreater(b, a)


class Suppression(Base):
    """TR-101 [INV-06] : aucune dépense n'est jamais supprimée ; INSERT OR REPLACE ne contourne pas la garde (recursive_triggers=ON, INV-07)."""

    def test_INV_06_delete_direct_d_une_depense_active_refuse(self):
        i = self.dep()
        self.refuse_inv("INV-06", "DELETE FROM depenses WHERE id=?", i)
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses WHERE id=?", i)[0], 1)

    def test_INV_06_delete_d_une_depense_annulee_refuse(self):
        i = self.dep()
        self.annuler(i)
        self.refuse_inv("INV-06", "DELETE FROM depenses WHERE id=?", i)
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses WHERE id=?", i)[0], 1)

    def test_INV_06_delete_quelle_que_soit_la_depense(self):
        cas = {"globale": {}, "avec fournisseur": {"fournisseur_id": self.f1}, "sur BC en cours": {"bc_id": self.bc_en_etat("en_cours")},
               "sur BC annule": {"bc_id": self.bc_en_etat("annule")}, "avec piece jointe": {"piece_jointe_chemin": "a", "piece_jointe_racine_id": 1}}
        for nom, kw in cas.items():
            with self.subTest(cas=nom):
                i = self.dep(**kw)
                self.refuse_inv("INV-06", "DELETE FROM depenses WHERE id=?", i)
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses")[0], len(cas))

    def test_INV_06_delete_par_toute_clause_refuse(self):
        a, b = self.dep(numero="DEP-00001-26"), self.dep(numero="DEP-00002-26")
        for sql in ("DELETE FROM depenses", "DELETE FROM depenses WHERE 1=1", "DELETE FROM depenses WHERE numero='DEP-00001-26'",
                    "DELETE FROM depenses WHERE montant='12.50'", "DELETE FROM depenses WHERE id IN (SELECT id FROM depenses)",
                    "DELETE FROM depenses WHERE cancelled_at IS NULL", "DELETE FROM depenses WHERE rowid=1"):
            with self.subTest(sql=sql):
                self.refuse_inv("INV-06", sql)
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses")[0], 2)
        self.db.execute("DELETE FROM depenses WHERE id=99999")                                           # aucune ligne : sans effet
        self.assertEqual({a, b}, {r[0] for r in self.db.execute("SELECT id FROM depenses")})

    def test_INV_06_delete_ne_laisse_aucun_effet_partiel_dans_une_transaction(self):
        self.dep(numero="DEP-00001-26")
        self.db.execute("BEGIN")
        self.dep(numero="DEP-00002-26")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-06"):
            self.db.execute("DELETE FROM depenses")
        self.db.execute("ROLLBACK")
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses")[0], 1)

    def test_INV_06_message_de_tr101(self):
        sql = self.un("SELECT sql FROM sqlite_master WHERE name='tr_101_depenses_no_delete'")[0]
        self.assertIn("INV-06: une depense ne se supprime jamais", sql)
        i = self.dep()
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.db.execute("DELETE FROM depenses WHERE id=?", (i,))
        self.assertEqual(str(cm.exception), "INV-06: une depense ne se supprime jamais")

    def test_INV_07_REPLACE_par_id_refuse_avec_recursive_triggers(self):
        i = self.dep(numero="DEP-00001-26", montant="12.50")
        avant = self.ligne(i)
        for sql in ("INSERT OR REPLACE INTO depenses (id, numero, date_depense, montant, categorie_id, description) "
                    "VALUES (?, 'DEP-00001-26', '2026-10-02', '1.00', ?, 'écrasé')",
                    "REPLACE INTO depenses (id, numero, date_depense, montant, categorie_id, description) "
                    "VALUES (?, 'DEP-00001-26', '2026-10-02', '1.00', ?, 'écrasé')",
                    "INSERT OR REPLACE INTO depenses (id, numero, date_depense, montant, categorie_id, description) "
                    "VALUES (?, 'DEP-00009-26', '2026-10-02', '1.00', ?, 'écrasé')"):
            with self.subTest(sql=sql[:40]):
                self.refuse_inv("INV-06", sql, i, self.cat)
                self.assertEqual(self.ligne(i), avant)

    def test_INV_07_REPLACE_par_numero_refuse_avec_recursive_triggers(self):
        i = self.dep(numero="DEP-00001-26", montant="12.50")
        avant = self.ligne(i)
        self.refuse_inv("INV-06", "INSERT OR REPLACE INTO depenses (numero, date_depense, montant, categorie_id, description) "
                                  "VALUES ('DEP-00001-26', '2026-10-02', '1.00', ?, 'écrasé')", self.cat)
        self.assertEqual(self.ligne(i), avant)
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses")[0], 1)

    def test_INV_07_REPLACE_d_une_depense_annulee_refuse(self):
        i = self.dep(numero="DEP-00001-26")
        self.annuler(i)
        avant = self.ligne(i)
        self.refuse_inv("INV-06", "INSERT OR REPLACE INTO depenses (id, numero, date_depense, montant, categorie_id, description) "
                                  "VALUES (?, 'DEP-00001-26', '2026-10-02', '1.00', ?, 'écrasé')", i, self.cat)
        self.refuse_inv("INV-06", "INSERT OR REPLACE INTO depenses (numero, date_depense, montant, categorie_id, description) "
                                  "VALUES ('DEP-00001-26', '2026-10-02', '1.00', ?, 'écrasé')", self.cat)
        self.assertEqual(self.ligne(i), avant)

    def test_INV_07_REPLACE_sans_conflit_est_un_INSERT_ordinaire(self):
        self.dep(numero="DEP-00001-26")
        self.db.execute("INSERT OR REPLACE INTO depenses (numero, date_depense, montant, categorie_id, description) "
                        "VALUES ('DEP-00002-26', '2026-10-02', '1.00', ?, 'nouvelle')", (self.cat,))      # n'écrase rien
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses")[0], 2)

    def test_INV_06_REPLACE_ne_serait_pas_refuse_sans_tr101_la_garde_est_bien_le_trigger(self):
        t = Base(); t.setUp()
        t.db.execute("DROP TRIGGER tr_101_depenses_no_delete")
        i = t.dep(numero="DEP-00001-26")
        t.db.execute("INSERT OR REPLACE INTO depenses (id, numero, date_depense, montant, categorie_id, description) "
                     "VALUES (?, 'DEP-00001-26', '2026-10-02', '1.00', ?, 'écrasé')", (i, t.cat))
        self.assertEqual(t.un("SELECT montant FROM depenses WHERE id=?", i)[0], "1.00")                   # sans TR-101, la ligne est remplacée

    def test_INV_06_delete_puis_reinsertion_du_meme_numero_impossible(self):
        i = self.dep(numero="DEP-00001-26")
        self.refuse_inv("INV-06", "DELETE FROM depenses WHERE id=?", i)
        self.refuse_check("INSERT INTO depenses (id, numero, date_depense, montant, categorie_id, description) "
                          "VALUES (?, 'DEP-00001-26', '2026-10-02', '1.00', ?, 'z')", i, self.cat)


class ImmutabiliteApresAnnulation(Base):
    """TR-102 [INV-197] : une dépense annulée est totalement immuable (aucun UPDATE, sur aucune colonne, updated_at compris)."""

    def annulee(self, **kw):
        kw.setdefault("bc_id", self.bc_en_etat("annule"))
        kw.setdefault("fournisseur_id", self.f1)
        kw.setdefault("piece_jointe_chemin", "2026/10/a.pdf")
        kw.setdefault("piece_jointe_racine_id", 3)
        kw.setdefault("notes", "n")
        i = self.dep(**kw)
        self.annuler(i)
        return i

    def tentatives(self):
        """(libellé, SET ...) : une tentative par colonne, valeur toujours acceptable par les CHECK et par les FK."""
        autre_bc = self.bc_en_etat("en_cours")
        return [("numero", "numero='DEP-00099-26'"), ("date_depense", "date_depense='2026-01-01'"),
                ("montant", "montant='99.99'"), ("categorie_id", f"categorie_id={self.categorie('AUT')}"),
                ("fournisseur_id", f"fournisseur_id={self.f2}"), ("fournisseur_id_null", "fournisseur_id=NULL"),
                ("bc_id", f"bc_id={autre_bc}"), ("bc_id_null", "bc_id=NULL"),
                ("description", "description='Autre'"), ("piece_jointe_chemin", "piece_jointe_chemin='b/c.pdf'"),
                ("piece_jointe_racine_id", "piece_jointe_racine_id=9"), ("piece_jointe_nulle", "piece_jointe_chemin=NULL, piece_jointe_racine_id=NULL"),
                ("notes", "notes='autre'"), ("notes_null", "notes=NULL"),
                ("cancelled_at", "cancelled_at='2031-01-01T00:00:00.000Z'"), ("cancelled_at_null", "cancelled_at=NULL, motif_annulation=NULL"),
                ("motif_annulation", "motif_annulation='Autre motif'"),
                ("created_at", "created_at='2020-01-01T00:00:00.000Z'"), ("updated_at", "updated_at='2031-01-01T00:00:00.000Z'"),
                ("id", "id=9999")]

    def test_INV_197_chaque_colonne_est_immuable_apres_annulation(self):
        i = self.annulee()
        avant = self.ligne(i)
        for colonne, set_ in self.tentatives():
            with self.subTest(colonne=colonne):
                with self.assertRaises(sqlite3.IntegrityError) as cm:
                    self.db.execute(f"UPDATE depenses SET {set_} WHERE rowid=?", (i,))
                self.assertIn("INV-", str(cm.exception))
                self.assertEqual(self.ligne(i), avant)

    def test_INV_197_message_de_tr102_pour_toutes_les_colonnes_sauf_numero(self):
        """Pour numero, TR-01 (INV-23) et TR-102 (INV-197) refusent tous deux ; pour toute autre colonne seul TR-102 parle."""
        i = self.annulee()
        for colonne, set_ in self.tentatives():
            if colonne == "numero":
                continue
            with self.subTest(colonne=colonne):
                self.refuse_inv("INV-197", f"UPDATE depenses SET {set_} WHERE rowid=?", i)

    def test_INV_197_updated_at_isole_refuse(self):
        i = self.annulee()
        self.refuse_inv("INV-197", "UPDATE depenses SET updated_at=? WHERE id=?", "2031-01-01T00:00:00.000Z", i)
        self.refuse_inv("INV-197", "UPDATE depenses SET updated_at=updated_at WHERE id=?", i)
        self.assertEqual(self.un("SELECT updated_at FROM depenses WHERE id=?", i)[0], TS2)

    def test_INV_197_update_sans_effet_apparent_refuse(self):
        i = self.annulee()
        for set_ in ("notes=notes", "montant=montant", "id=id", "cancelled_at=cancelled_at", "motif_annulation=motif_annulation",
                     "numero=numero", "bc_id=bc_id", "fournisseur_id=fournisseur_id"):
            with self.subTest(set=set_):
                self.refuse_inv("INV-197", f"UPDATE depenses SET {set_} WHERE id=?", i)

    def test_INV_197_plusieurs_colonnes_simultanement_refuse(self):
        i = self.annulee()
        avant = self.ligne(i)
        self.refuse_inv("INV-197", "UPDATE depenses SET montant='1.00', notes='z', description='z', updated_at=? WHERE id=?",
                        "2031-01-01T00:00:00.000Z", i)
        self.refuse_inv("INV-197", "UPDATE depenses SET fournisseur_id=?, bc_id=NULL, categorie_id=? WHERE id=?", self.f2, self.categorie("AUT"), i)
        self.refuse_inv("INV-197", "UPDATE depenses SET date_depense='2026-01-01', montant='2.00', notes=NULL WHERE id=?", i)
        self.assertEqual(self.ligne(i), avant)

    def test_INV_197_reactivation_impossible(self):
        i = self.annulee()
        avant = self.ligne(i)
        for set_ in ("cancelled_at=NULL, motif_annulation=NULL", "cancelled_at=NULL, motif_annulation=NULL, updated_at='2031-01-01T00:00:00.000Z'",
                     "cancelled_at=NULL", "motif_annulation=NULL"):
            with self.subTest(set=set_):
                self.refuse_inv("INV-197", f"UPDATE depenses SET {set_} WHERE id=?", i)
        self.assertEqual(self.ligne(i), avant)

    def test_INV_197_remplacement_de_la_ligne_refuse(self):
        i = self.annulee(numero="DEP-00001-26")
        avant = self.ligne(i)
        self.refuse_inv("INV-06", "INSERT OR REPLACE INTO depenses (id, numero, date_depense, montant, categorie_id, description) "
                                  "VALUES (?, 'DEP-00001-26', '2026-10-02', '1.00', ?, 'z')", i, self.cat)
        self.refuse_inv("INV-06", "INSERT OR REPLACE INTO depenses (numero, date_depense, montant, categorie_id, description) "
                                  "VALUES ('DEP-00001-26', '2026-10-02', '1.00', ?, 'z')", self.cat)
        self.refuse_inv("INV-197", "INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) "
                                   "VALUES ('DEP-00001-26', '2026-10-02', '1.00', ?, 'z') ON CONFLICT(numero) DO UPDATE SET montant=excluded.montant",
                        self.cat)
        self.assertEqual(self.ligne(i), avant)

    def test_INV_197_suppression_d_une_depense_annulee_refusee(self):
        i = self.annulee()
        self.refuse_inv("INV-06", "DELETE FROM depenses WHERE id=?", i)

    def test_INV_197_donnees_conservees_apres_toutes_les_tentatives(self):
        i = self.annulee()
        avant = self.ligne(i)
        for _, set_ in self.tentatives():
            self.assertIsNotNone(self.essai(f"UPDATE depenses SET {set_} WHERE id=?", i))
        self.assertIsNotNone(self.essai("DELETE FROM depenses WHERE id=?", i))
        self.assertEqual(self.ligne(i), avant)

    def test_INV_197_ne_vise_que_la_ligne_annulee(self):
        a, b = self.dep(numero="DEP-00001-26"), self.dep(numero="DEP-00002-26")
        self.annuler(a)
        self.db.execute("UPDATE depenses SET montant='7.00', updated_at=? WHERE id=?", (TS2, b))          # une autre dépense reste corrigeable
        self.assertEqual(self.un("SELECT montant FROM depenses WHERE id=?", b)[0], "7.00")
        self.refuse_inv("INV-197", "UPDATE depenses SET montant='7.00' WHERE id=?", a)
        self.refuse_inv("INV-197", "UPDATE depenses SET notes='x'")                                       # un UPDATE global atteint la ligne annulée : refusé en bloc
        self.assertIsNone(self.un("SELECT notes FROM depenses WHERE id=?", b)[0])
        self.dep(numero="DEP-00003-26")                                                                    # l'insertion reste possible

    def test_INV_197_annulation_en_cours_de_transaction_puis_modification_refusee(self):
        i = self.dep()
        self.db.execute("BEGIN")
        self.annuler(i)
        self.refuse_inv("INV-197", "UPDATE depenses SET notes='x' WHERE id=?", i)
        self.db.execute("COMMIT")
        self.assertIsNone(self.un("SELECT notes FROM depenses WHERE id=?", i)[0])

    def test_INV_197_condition_portee_par_l_etat_avant_l_update(self):
        """L'annulation (OLD.cancelled_at IS NULL) n'est pas visée ; une modification simultanée à l'annulation reste du ressort du service."""
        i = self.dep()
        self.db.execute("UPDATE depenses SET cancelled_at=?, motif_annulation='m' WHERE id=?", (TS2, i))
        j = self.dep()
        self.db.execute("UPDATE depenses SET cancelled_at=?, motif_annulation='m', montant='1.00', notes='z' WHERE id=?", (TS2, j))   # info : accepté par le SQL
        self.assertEqual(self.un("SELECT montant FROM depenses WHERE id=?", j)[0], "1.00")

    def test_INV_197_tr01_et_tr102_coexistent(self):
        i = self.annulee(numero="DEP-00001-26")
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.db.execute("UPDATE depenses SET numero='DEP-00002-26' WHERE id=?", (i,))
        self.assertIn("INV-", str(cm.exception))
        self.assertEqual(self.un("SELECT numero FROM depenses WHERE id=?", i)[0], "DEP-00001-26")

    def test_INV_197_depense_annulee_toujours_lisible_et_jointable(self):
        b = self.bc_en_etat("annule")
        i = self.annulee(bc_id=b)
        self.assertEqual(self.un("SELECT d.numero, b.statut FROM depenses d JOIN bons_commande b ON b.id=d.bc_id WHERE d.id=?", i),
                         (self.un("SELECT numero FROM depenses WHERE id=?", i)[0], "annule"))


class CorrectionActive(Base):
    """INV-193, INV-198 : une dépense active est corrigeable ; updated_at évolue normalement avant l'annulation."""

    def test_INV_198_toutes_les_corrections_de_la_liste_du_cadrage(self):
        b1, b2 = self.bc_en_etat("en_cours"), self.bc_en_etat("termine")
        autre = self.categorie("AUT")
        i = self.dep(numero="DEP-00001-26", date_depense="2026-10-02")
        corrections = [("montant", "UPDATE depenses SET montant='99.99' WHERE id=?"),
                       ("date dans la même année", "UPDATE depenses SET date_depense='2026-03-04' WHERE id=?"),
                       ("catégorie", f"UPDATE depenses SET categorie_id={autre} WHERE id=?"),
                       ("fournisseur", f"UPDATE depenses SET fournisseur_id={self.f1} WHERE id=?"),
                       ("changement de fournisseur", f"UPDATE depenses SET fournisseur_id={self.f2} WHERE id=?"),
                       ("retrait du fournisseur", "UPDATE depenses SET fournisseur_id=NULL WHERE id=?"),
                       ("rattachement", f"UPDATE depenses SET bc_id={b1} WHERE id=?"),
                       ("changement de BC", f"UPDATE depenses SET bc_id={b2} WHERE id=?"),
                       ("détachement", "UPDATE depenses SET bc_id=NULL WHERE id=?"),
                       ("globale -> BC", f"UPDATE depenses SET bc_id={b1} WHERE id=?"),
                       ("BC -> globale", "UPDATE depenses SET bc_id=NULL WHERE id=?"),
                       ("description", "UPDATE depenses SET description='Autre libellé' WHERE id=?"),
                       ("notes", "UPDATE depenses SET notes='Précision' WHERE id=?"),
                       ("pièce jointe", "UPDATE depenses SET piece_jointe_chemin='x/y.pdf', piece_jointe_racine_id=4 WHERE id=?")]
        for nom, sql in corrections:
            with self.subTest(correction=nom):
                self.db.execute(sql, (i,))
        self.assertEqual(self.un("SELECT numero, montant, date_depense, categorie_id, fournisseur_id, bc_id FROM depenses WHERE id=?", i),
                         ("DEP-00001-26", "99.99", "2026-03-04", autre, None, None))

    def test_INV_198_updated_at_evolue_normalement_avant_annulation(self):
        i = self.dep(created_at=TS, updated_at=TS)
        for ts in ("2026-10-02T11:30:15.123Z", "2026-10-03T08:00:00.000Z", "2026-10-03T08:00:00.001Z"):
            self.db.execute("UPDATE depenses SET montant='5.00', updated_at=? WHERE id=?", (ts, i))
            self.assertEqual(self.un("SELECT updated_at FROM depenses WHERE id=?", i)[0], ts)
        self.db.execute("UPDATE depenses SET updated_at=? WHERE id=?", ("2026-10-04T00:00:00.000Z", i))     # updated_at isolé : permis tant qu'active
        self.assertEqual(self.un("SELECT created_at FROM depenses WHERE id=?", i)[0], TS)

    def test_INV_198_corrections_multiples_en_une_seule_instruction(self):
        i = self.dep(fournisseur_id=self.f1, bc_id=self.bc_en_etat("en_cours"))
        self.db.execute("UPDATE depenses SET montant='2.00', fournisseur_id=NULL, bc_id=NULL, description='z', notes='n', updated_at=? WHERE id=?", (TS2, i))
        self.assertEqual(self.un("SELECT montant, fournisseur_id, bc_id, description, notes, updated_at FROM depenses WHERE id=?", i),
                         ("2.00", None, None, "z", "n", TS2))

    def test_INV_198_correction_invalide_refusee_et_ligne_inchangee(self):
        i = self.dep()
        avant = self.ligne(i)
        for sql in ("UPDATE depenses SET montant='0.00' WHERE id=?", "UPDATE depenses SET date_depense='2026-02-30' WHERE id=?",
                    "UPDATE depenses SET categorie_id=999999 WHERE id=?", "UPDATE depenses SET bc_id=999999 WHERE id=?",
                    "UPDATE depenses SET fournisseur_id=999999 WHERE id=?", "UPDATE depenses SET description='' WHERE id=?",
                    "UPDATE depenses SET numero='DEP-00002-26' WHERE id=?", "UPDATE depenses SET date_depense='2027-10-02' WHERE id=?",
                    "UPDATE depenses SET montant='5.00', description='' WHERE id=?"):
            with self.subTest(sql=sql):
                self.assertIsNotNone(self.essai(sql, i))
        self.assertEqual(self.ligne(i), avant)                                       # aucune correction partielle


class GardesIndependantes(Base):
    """Chaque trigger de la tranche refuse seul la violation qui lui est propre ; sans lui, la violation passe (il est donc le garde)."""

    def scenarios(self):
        """nom du trigger -> (préparation(t) retournant l'action, motif du message)."""
        def tr01(t):
            i = t.dep(numero="DEP-00001-26")
            return lambda: t.db.execute("UPDATE depenses SET numero='DEP-00099-26' WHERE id=?", (i,))
        def tr101(t):
            i = t.dep()
            return lambda: t.db.execute("DELETE FROM depenses WHERE id=?", (i,))
        def tr102(t):
            i = t.dep()
            t.annuler(i)
            return lambda: t.db.execute("UPDATE depenses SET montant='99.99' WHERE id=?", (i,))
        return {"tr_01_depenses_numero_immuable": (tr01, "INV-23"),
                "tr_101_depenses_no_delete": (tr101, "INV-06"),
                "tr_102_depenses_annulee_immuable": (tr102, "INV-197")}

    def isole(self, gardes):
        """Base 001-005 dont tous les triggers de la tranche 005 sont supprimés sauf `gardes`."""
        t = Base(); t.setUp()
        for nom in TRIGGERS_005 - set(gardes):
            t.db.execute(f"DROP TRIGGER {nom}")
        return t

    def test_T44_tous_les_triggers_ont_un_scenario(self):
        self.assertEqual(set(self.scenarios()), TRIGGERS_005)

    def test_T44_chaque_trigger_refuse_seul_et_sans_lui_la_violation_passe(self):
        for nom, (preparer, motif) in self.scenarios().items():
            with self.subTest(trigger=nom):
                seul = self.isole({nom})
                agir = preparer(seul)
                with self.assertRaisesRegex(sqlite3.IntegrityError, motif):
                    agir()
                sans = self.isole(set())
                agir = preparer(sans)
                agir()                                                       # aucune autre garde : la violation passe

    def test_T44_tr102_refuse_seul_chaque_colonne_d_une_depense_annulee(self):
        seul = self.isole({"tr_102_depenses_annulee_immuable"})
        i = seul.dep(bc_id=seul.bc_en_etat("annule"), fournisseur_id=seul.f1, notes="n", piece_jointe_chemin="a", piece_jointe_racine_id=1)
        seul.annuler(i)
        avant = seul.ligne(i)
        for set_ in ("numero='DEP-00099-26'", "date_depense='2026-01-01'", "montant='9.99'", f"categorie_id={seul.categorie('AUT')}",
                     f"fournisseur_id={seul.f2}", "fournisseur_id=NULL", "bc_id=NULL", "description='z'", "notes='z'",
                     "piece_jointe_chemin='b'", "piece_jointe_racine_id=2", "cancelled_at='2031-01-01T00:00:00.000Z'",
                     "cancelled_at=NULL, motif_annulation=NULL", "motif_annulation='z'", "created_at='2020-01-01T00:00:00.000Z'",
                     "updated_at='2031-01-01T00:00:00.000Z'"):
            with self.subTest(set=set_):
                with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-197"):
                    seul.db.execute(f"UPDATE depenses SET {set_} WHERE id=?", (i,))
        self.assertEqual(seul.ligne(i), avant)

    def test_T44_sans_tr102_chaque_colonne_d_une_depense_annulee_est_modifiable(self):
        """Témoin : le verrou vient de TR-102 et de lui seul (aucune contrainte de table n'interdit ces modifications)."""
        sans = self.isole(set())
        i = sans.dep(bc_id=sans.bc_en_etat("annule"), fournisseur_id=sans.f1)
        sans.annuler(i)
        for set_ in ("montant='9.99'", "updated_at='2031-01-01T00:00:00.000Z'", "bc_id=NULL", f"fournisseur_id={sans.f2}",
                     "notes='z'", "date_depense='2026-01-01'", "cancelled_at=NULL, motif_annulation=NULL"):
            sans.db.execute(f"UPDATE depenses SET {set_} WHERE id=?", (i,))

    def test_T44_tr01_refuse_seul_l_annee_de_la_date_et_le_check_la_double(self):
        seul = self.isole({"tr_01_depenses_numero_immuable"})
        i = seul.dep(numero="DEP-00001-26", date_depense="2026-10-02")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-23"):
            seul.db.execute("UPDATE depenses SET date_depense='2027-10-02' WHERE id=?", (i,))
        sans = self.isole(set())
        j = sans.dep(numero="DEP-00001-26", date_depense="2026-10-02")
        with self.assertRaises(sqlite3.IntegrityError) as cm:                                               # sans TR-01 : le CHECK numero / date refuse aussi
            sans.db.execute("UPDATE depenses SET date_depense='2027-10-02' WHERE id=?", (j,))
        self.assertNotIn("INV-", str(cm.exception))

    def test_T44_tr101_refuse_seul_replace_et_delete(self):
        seul = self.isole({"tr_101_depenses_no_delete"})
        i = seul.dep(numero="DEP-00001-26")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-06"):
            seul.db.execute("INSERT OR REPLACE INTO depenses (id, numero, date_depense, montant, categorie_id, description) "
                            "VALUES (?, 'DEP-00001-26', '2026-10-02', '1.00', ?, 'z')", (i, seul.cat))
        self.assertEqual(seul.un("SELECT montant FROM depenses WHERE id=?", i)[0], "12.50")


class Contournements(Base):
    """Résistance du schéma, pas seulement son usage nominal : REPLACE, UPDATE direct, DELETE direct, plusieurs colonnes, après annulation,
    changement de numéro ou d'année, FK invalides, valeurs limites des CHECK."""

    def test_T44_valeurs_limites_des_check(self):
        self.subTests_vus = []
        limites_ok = [("montant", "0.01"), ("montant", "99999999999.99"), ("date_depense", "2024-02-29"), ("date_depense", "2026-12-31"),
                      ("date_depense", "2026-01-01"), ("numero", "DEP-99999-26"), ("numero", "DEP-00000-26"), ("description", "x")]
        limites_ko = [("montant", "0.00"), ("montant", "0.001"), ("montant", "00.01"), ("date_depense", "2026-02-29"),
                      ("date_depense", "2026-12-32"), ("date_depense", "2026-00-01"), ("numero", "DEP-100000-26"), ("numero", "DEP-0000-26"),
                      ("description", "")]
        for col, val in limites_ok:
            with self.subTest(ok=(col, val)):
                kw = {col: val}
                if col == "date_depense":
                    kw["numero"] = f"DEP-{50000 + len(self.subTests_vus):05d}-{val[2:4]}"
                    self.subTests_vus.append(val)
                if col == "numero":
                    kw["date_depense"] = "2026-10-02"
                self.dep(**kw)
        for col, val in limites_ko:
            with self.subTest(ko=(col, val)):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.dep(**{col: val})

    def test_T44_attaques_combinees_sur_une_depense_active(self):
        i = self.dep(numero="DEP-00001-26", date_depense="2026-10-02")
        avant = self.ligne(i)
        attaques = [("UPDATE depenses SET numero='DEP-00001-27', date_depense='2027-10-02' WHERE id=?", "INV-23"),
                    ("UPDATE depenses SET date_depense='2027-10-02', montant='1.00' WHERE id=?", "INV-23"),
                    ("DELETE FROM depenses WHERE id=?", "INV-06"),
                    ("INSERT OR REPLACE INTO depenses (id, numero, date_depense, montant, categorie_id, description) "
                     "VALUES (?, 'DEP-00001-26', '2026-10-02', '1.00', 1, 'x')", "INV-06")]
        for sql, inv in attaques:
            with self.subTest(sql=sql[:50]):
                self.refuse_inv(inv, sql, i)
        self.assertEqual(self.ligne(i), avant)

    def test_T44_fk_invalides_a_l_insertion_et_a_la_modification(self):
        for col in ("fournisseur_id", "bc_id", "categorie_id"):
            for valeur in (999999, 0, -1):
                with self.subTest(col=col, valeur=valeur):
                    with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):
                        self.dep(**{col: valeur})
        self.assertEqual(self.un("SELECT COUNT(*) FROM depenses")[0], 0)

    def test_T44_fk_de_type_incorrect_refusee(self):
        i = self.dep()
        for col in ("fournisseur_id", "bc_id", "categorie_id"):
            with self.subTest(col=col):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.db.execute(f"UPDATE depenses SET {col}='abc' WHERE id=?", (i,))

    def test_T44_foreign_keys_off_ne_serait_pas_une_garde_acceptable_le_reglage_est_verifie(self):
        t = Base(); t.setUp()
        t.db.execute("PRAGMA foreign_keys=OFF")
        self.assertEqual(t.un("PRAGMA foreign_keys")[0], 0)
        t.dep(bc_id=999999)                                                          # sans FK activées : accepté — d'où le contrôle de connexion (D-39)
        self.assertEqual(self.un("PRAGMA foreign_keys")[0], 1)

    def test_T44_aucune_ecriture_de_depenses_ne_modifie_les_tables_parentes(self):
        avant = {t: self.tous(f"SELECT * FROM {t} ORDER BY 1") for t in ("fournisseurs", "bons_commande", "categories_depenses")}
        b = self.bc_en_etat("en_cours")
        avant["bons_commande"] = self.tous("SELECT * FROM bons_commande ORDER BY 1")
        i = self.dep(bc_id=b, fournisseur_id=self.f1)
        self.db.execute("UPDATE depenses SET montant='2.00' WHERE id=?", (i,))
        self.annuler(i)
        for t, lignes in avant.items():
            self.assertEqual(self.tous(f"SELECT * FROM {t} ORDER BY 1"), lignes, t)

    def test_T44_types_et_affinite_stricts(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) VALUES (?, '2026-10-02', '1.00', ?, 'x')",
                            (b"DEP-00001-26", self.cat))                              # BLOB refusé dans une colonne TEXT STRICT
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO depenses (numero, date_depense, montant, categorie_id, description) VALUES ('DEP-00001-26', '2026-10-02', '1.00', 'abc', 'x')")

    def test_T44_aucun_champ_calcule_ou_cache_n_est_stocke(self):
        """Aucun total de dépenses n'est dénormalisé (cadrage §1.5.5) : ni sur depenses, ni sur bons_commande."""
        colonnes_bc = {r[1] for r in self.db.execute("PRAGMA table_info(bons_commande)")}
        self.assertFalse({c for c in colonnes_bc if "depense" in c})
        self.assertFalse({c for c in {r[1] for r in self.db.execute("PRAGMA table_info(depenses)")} if c.startswith(("total", "cumul", "somme"))})


if __name__ == "__main__":
    unittest.main(verbosity=2)
