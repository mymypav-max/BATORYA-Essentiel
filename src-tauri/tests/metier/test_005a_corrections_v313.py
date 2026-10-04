"""T-45 — Migration corrective 005a_corrections_v313 (M-A, rang 6) ; modèle V3.13 §4.4, §4.6, §4.19, §8, §17.1 ; conventions techniques §5
(chaîne ordonnée, transaction et user_version, protocole de reconstruction de table) ; rapport de compatibilité 001–004 avant 005 (G-1, G-2, G-3).
Ce n'est pas une tranche métier : 005a corrige le schéma de 001–003 (clients, fournisseurs, devis) et recrée les objets de 003 et 004 que la
reconstruction impose de retirer. Les migrations 001 à 005 sont appliquées comme le fait le runner (D-55) ; 005a l'est par `runner()` qui
reproduit le protocole de reconstruction : foreign_keys=OFF hors transaction, BEGIN IMMEDIATE, fichier, PRAGMA foreign_key_check (vide),
PRAGMA integrity_check (ok), PRAGMA user_version = 6 dans la transaction, COMMIT, puis foreign_keys=ON.

Exécution : python3 src-tauri/tests/metier/test_005a_corrections_v313.py
Les méthodes portent le nom de l'invariant vérifié (test_INV_xx_…) ; les autres commencent par test_T45_.
Ces tests ne dépendent d'aucune interface graphique ni d'aucun service : ils ne vérifient que des faits SQL. Les règles de service (attribution du
numéro à la finalisation, création du snapshot, calcul des totaux, journalisation) n'y sont PAS testées comme des contraintes : les fixtures les
reproduisent avec des requêtes simples.
Connexion de test : PRAGMA foreign_keys=ON et PRAGMA recursive_triggers=ON (D-39) ; un test vérifie que le réglage est actif.
Interprétations de la migration (rapport de 005a, à confirmer avant 005b) : chacune est verrouillée par un test dont le nom contient « INTERPRETATION ».
Les tests de 001–005 décrivent l'état de chaque migration prise isolément ; ceux-ci décrivent le schéma de la chaîne complète jusqu'au rang 6.
"""
import pathlib
import re
import sqlite3
import types
import unittest

MIGRATIONS = pathlib.Path(__file__).resolve().parents[2] / "migrations" / "metier"
NOMS = ("001_initial.sql", "002_fournisseurs.sql", "003_devis.sql", "004_bons_commande.sql", "005_depenses.sql",
        "005a_corrections_v313.sql")
SQLS = [(MIGRATIONS / n).read_text(encoding="utf-8") for n in NOMS]
CHAINE = tuple(enumerate(SQLS, start=1))
SQL_005A = SQLS[5]

TABLES_RANG5 = {"import_anomalies", "numerotation_sequences", "categories_prestations", "categories_depenses", "clients",
                "prestations", "prestation_garanties", "fournisseurs", "devis", "devis_lignes", "devis_ligne_garanties",
                "bons_commande", "bc_lignes", "bc_ligne_garanties", "depenses"}
TABLES_RANG6 = TABLES_RANG5 | {"devis_revisions"}
INDEXES_RANG5 = {"idx_clients_statut", "idx_prestations_categorie_id", "idx_prestations_actif", "idx_import_anomalies_categorie_statut",
                 "idx_fournisseurs_statut", "idx_devis_client_id", "idx_devis_statut", "idx_devis_date_creation",
                 "idx_devis_lignes_prestation_id", "idx_bons_commande_client_id", "idx_bons_commande_statut",
                 "idx_bc_lignes_prestation_id", "idx_depenses_bc_id", "idx_depenses_fournisseur_id", "idx_depenses_categorie_id",
                 "idx_depenses_date_depense"}
INDEXES_RETIRES = {"idx_clients_statut", "idx_fournisseurs_statut"}
INDEXES_AJOUTES = {"uq_devis_revisions_initiale"}
INDEXES_RANG6 = (INDEXES_RANG5 - INDEXES_RETIRES) | INDEXES_AJOUTES
TRIGGERS_001 = {"tr_90_import_anomalies_no_delete", "tr_90_import_anomalies_update", "tr_95_numerotation_sequences_no_decrease"}
TRIGGERS_003 = {"tr_01_devis_numero_immuable", "tr_10_devis_modifiable", "tr_10_devis_refuse_annule", "tr_10_devis_gele",
                "tr_14_devis_frozen_at", "tr_11_devis_lignes_insert", "tr_11_devis_lignes_update", "tr_11_devis_lignes_delete",
                "tr_11_devis_ligne_garanties_insert", "tr_11_devis_ligne_garanties_update", "tr_11_devis_ligne_garanties_delete"}
TRIGGERS_004 = {"tr_01_bons_commande_numero_immuable", "tr_12_bons_commande_modifiable", "tr_12_bons_commande_gele",
                "tr_12_bons_commande_annule", "tr_14_bons_commande_frozen_at", "tr_17_bons_commande_insert",
                "tr_19_bons_commande_no_delete", "tr_18_devis_statut_avec_bc",
                "tr_13_bc_lignes_insert", "tr_13_bc_lignes_update", "tr_13_bc_lignes_delete",
                "tr_13_bc_ligne_garanties_insert", "tr_13_bc_ligne_garanties_update", "tr_13_bc_ligne_garanties_delete",
                "tr_96_numerotation_sequences_no_delete"}
TRIGGERS_005 = {"tr_01_depenses_numero_immuable", "tr_101_depenses_no_delete", "tr_102_depenses_annulee_immuable"}
TRIGGERS_RANG5 = TRIGGERS_001 | TRIGGERS_003 | TRIGGERS_004 | TRIGGERS_005
# 003 : retirés puis remplacés (réécriture TR-01 / TR-10 / TR-11) ; supprimés (remplacés par d'autres noms)
TRIGGERS_SUPPRIMES = {"tr_10_devis_refuse_annule", "tr_10_devis_gele"}
TRIGGERS_REECRITS = {"tr_01_devis_numero_immuable", "tr_10_devis_modifiable", "tr_11_devis_lignes_insert", "tr_11_devis_lignes_update",
                     "tr_11_devis_lignes_delete", "tr_11_devis_ligne_garanties_insert", "tr_11_devis_ligne_garanties_update",
                     "tr_11_devis_ligne_garanties_delete", "tr_12_bons_commande_gele", "tr_12_bons_commande_annule"}
# recréés à l'identique (la reconstruction de devis impose de les retirer, G-2) ; 004 : jamais touchés (G-3 vérifié)
TRIGGERS_RECREES_IDENTIQUES = {"tr_14_devis_frozen_at", "tr_17_bons_commande_insert", "tr_18_devis_statut_avec_bc"}
TRIGGERS_NOUVEAUX = {"tr_97_clients_no_delete", "tr_97_clients_code_immuable", "tr_97_fournisseurs_no_delete",
                     "tr_97_fournisseurs_code_immuable", "tr_98_devis_no_delete", "tr_10_devis_client_immuable",
                     "tr_10_devis_en_attente", "tr_10_devis_verrouille", "tr_10_devis_annule", "tr_10_devis_revision",
                     "tr_10_devis_acceptation", "tr_10_devis_finalisation", "tr_100_devis_revisions_insert",
                     "tr_100_devis_revisions_no_update", "tr_100_devis_revisions_no_delete"}
TRIGGERS_RANG6 = (TRIGGERS_RANG5 - TRIGGERS_SUPPRIMES) | TRIGGERS_NOUVEAUX
TRIGGERS_INCHANGES = TRIGGERS_RANG5 - TRIGGERS_SUPPRIMES - TRIGGERS_REECRITS - TRIGGERS_RECREES_IDENTIQUES
TRIGGERS_004_G3 = {"tr_01_bons_commande_numero_immuable", "tr_14_bons_commande_frozen_at", "tr_19_bons_commande_no_delete"}

COLONNES_CLIENTS = ["id", "code", "nom", "prenom", "adresse", "cpville", "tel", "email", "notes", "created_at", "updated_at",
                    "origine", "legacy_id", "legacy_data", "legacy_numero"]
COLONNES_FOURNISSEURS = ["id", "code", "nom", "adresse", "cpville", "tel", "email", "notes", "created_at", "updated_at"]
COLONNES_DEVIS_5 = ["id", "numero", "client_id", "client_snapshot", "client_snapshot_version", "entreprise_snapshot",
                    "entreprise_snapshot_version", "chantier_snapshot", "chantier_snapshot_version", "date_creation", "date_validite",
                    "date_acceptation", "date_refus", "objet", "notes", "statut", "remise_type", "remise_valeur", "acompte_type",
                    "acompte_valeur", "total_ht", "frozen_at", "cancelled_at", "motif_refus", "motif_annulation", "created_at",
                    "updated_at", "origine", "legacy_id", "legacy_data"]
COLONNES_DEVIS = ["id", "numero", "client_id", "client_snapshot", "client_snapshot_version", "entreprise_snapshot",
                  "entreprise_snapshot_version", "chantier_snapshot", "chantier_snapshot_version", "date_creation", "date_validite",
                  "date_acceptation", "date_refus", "objet", "notes", "statut", "revision", "revision_en_cours", "remise_type",
                  "remise_valeur", "acompte_type", "acompte_valeur", "total_ht", "frozen_at", "cancelled_at", "motif_refus",
                  "motif_annulation", "created_at", "updated_at", "origine", "legacy_id", "legacy_data"]
COLONNES_REVISIONS = ["id", "devis_id", "revision", "schema_contenu", "contenu", "total_ht", "valide_at", "created_at"]
COLONNES_BC = ["id", "numero", "devis_id", "client_id", "client_snapshot", "client_snapshot_version",
               "entreprise_snapshot", "entreprise_snapshot_version", "chantier_snapshot", "chantier_snapshot_version",
               "date_creation", "date_acceptation", "date_debut", "date_fin", "montant_contractuel_ht", "remise_type",
               "remise_valeur", "acompte_type", "acompte_valeur", "montant_deja_facture_ht", "avancement",
               "date_100_facture", "statut", "completed_at", "cancelled_at", "motif_annulation", "frozen_at",
               "created_at", "updated_at", "origine", "legacy_id", "legacy_data", "legacy_numero"]
# colonnes de devis dont la valeur est du « contenu » (verrouillé hors brouillon et hors phase de révision)
CONTENU_DEVIS = ["client_snapshot", "client_snapshot_version", "entreprise_snapshot", "entreprise_snapshot_version", "chantier_snapshot",
                 "chantier_snapshot_version", "date_validite", "objet", "notes", "remise_type", "remise_valeur", "acompte_type",
                 "acompte_valeur", "total_ht"]

TS = "2026-10-01T10:00:00.000Z"
TS2 = "2026-10-02T11:30:15.123Z"
SNAP = '{"nom": "Dupont"}'
ATTRIBUER = ("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES (?, ?, 1) "
             "ON CONFLICT (type_objet, annee) DO UPDATE SET dernier_numero = dernier_numero + 1, "
             "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') RETURNING dernier_numero")


# --------------------------------------------------------------------------------------------------------------------
# Exécution des migrations
# --------------------------------------------------------------------------------------------------------------------
def sans_commentaires(sql):
    return re.sub(r"--[^\n]*", "", sql)


def instructions(sql):
    """Découpe un fichier de migration en instructions complètes (les triggers contiennent des « ; »)."""
    tampon = ""
    for ligne in sql.splitlines(keepends=True):
        tampon += ligne
        if sqlite3.complete_statement(tampon):
            if sans_commentaires(tampon).strip():
                yield tampon
            tampon = ""
    if sans_commentaires(tampon).strip():
        raise AssertionError("instruction incomplète en fin de fichier : " + tampon)


class ErreurRunner(Exception):
    pass


def appliquer(db, rang, sql):
    """Une migration 001–005 comme le runner (D-55) : BEGIN IMMEDIATE, SQL du fichier, user_version = rang, COMMIT."""
    db.executescript(f"BEGIN IMMEDIATE;\n{sql}\nPRAGMA user_version = {rang};\nCOMMIT;")


def runner(db, rang=6, sql=None, verifier=True):
    """Protocole de reconstruction (conventions §5) : foreign_keys=OFF hors transaction (relu), BEGIN IMMEDIATE, instructions du fichier,
    foreign_key_check (vide), integrity_check (ok), user_version = rang dans la transaction, COMMIT ; ROLLBACK intégral sur toute erreur ;
    puis foreign_keys=ON (relu)."""
    sql = SQLS[rang - 1] if sql is None else sql
    db.execute("PRAGMA foreign_keys=OFF")
    if db.execute("PRAGMA foreign_keys").fetchone()[0] != 0:
        raise ErreurRunner("foreign_keys n'a pas pu être désactivé")
    try:
        db.execute("BEGIN IMMEDIATE")
        try:
            for st in instructions(sql):
                db.execute(st)
            if verifier:
                if db.execute("PRAGMA foreign_key_check").fetchall():
                    raise ErreurRunner("foreign_key_check non vide")
                if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                    raise ErreurRunner("integrity_check")
            db.execute(f"PRAGMA user_version = {rang}")
            db.execute("COMMIT")
        except BaseException:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise
    finally:
        db.execute("PRAGMA foreign_keys=ON")
        if db.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise ErreurRunner("foreign_keys n'a pas pu être réactivé")


def migrer(jusqu_a=6, recursive=True):
    """Applique 001 à 005 puis 005a (ou jusqu'au rang `jusqu_a`). La connexion applique les réglages obligatoires (D-39) :
    foreign_keys=ON et recursive_triggers=ON."""
    db = sqlite3.connect(":memory:", isolation_level=None)
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA recursive_triggers=" + ("ON" if recursive else "OFF"))
    for rang, sql in CHAINE:
        if rang <= jusqu_a:
            if rang == 6:
                runner(db)
            else:
                appliquer(db, rang, sql)
    return db


def objets(db, hors_tables=()):
    """Objets du schéma (type, nom, table, sql), sans les tables internes de SQLite."""
    return sorted(r for r in db.execute("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")
                  if r[2] not in hors_tables)


def sql_de(db, nom):
    return db.execute("SELECT sql FROM sqlite_master WHERE name=?", (nom,)).fetchone()[0]


def noms(db, type_):
    return {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type=? AND name NOT LIKE 'sqlite_%'", (type_,))}


def tout(db):
    """Contenu de toutes les tables, y compris sqlite_sequence."""
    r = {t: db.execute(f"SELECT * FROM {t} ORDER BY 1").fetchall() for t in sorted(noms(db, "table"))}
    r["sqlite_sequence"] = sorted(db.execute("SELECT name, seq FROM sqlite_sequence").fetchall())
    return r


def colonnes(db, table):
    return [r[1] for r in db.execute(f"PRAGMA table_info({table})")]


def peupler_rang5(db):
    """Base au rang 5 : toutes les tables ont des lignes, des trous d'identifiants (séquences AUTOINCREMENT en avance sur le max),
    tous les statuts de devis, un BC gelé avec lignes et garanties, des dépenses."""
    x = db.execute
    x("INSERT INTO clients (code, nom, prenom, adresse, cpville, tel, email, notes, statut) "
      "VALUES ('CLI-0001', 'Dupont', 'Jean', '1 rue A', '75001 Paris', '0102030405', 'a@b.fr', 'note', 'actif')")
    x("INSERT INTO clients (code, nom, statut) VALUES ('CLI-0002', 'Martin', 'archive')")
    x("INSERT INTO clients (code, nom, statut, origine, legacy_id, legacy_data, legacy_numero) "
      "VALUES ('CLI-0003', 'Durand', 'a_rattacher', 'import', 'L-3', '{\"k\": 3}', 'C-3')")
    x("INSERT INTO clients (code, nom, statut) VALUES ('CLI-0004', 'Temp', 'actif')")
    x("DELETE FROM clients WHERE code='CLI-0004'")                                             # séquence clients = 4, max(id) = 3
    x("INSERT INTO fournisseurs (code, nom, adresse, cpville, tel, email, notes, statut) "
      "VALUES ('FOU-0001', 'Quincaillerie', '2 rue B', '69001 Lyon', '0405060708', 'f@g.fr', 'nf', 'actif')")
    x("INSERT INTO fournisseurs (code, nom, statut) VALUES ('FOU-0002', 'Ancien', 'archive')")
    x("INSERT INTO fournisseurs (code, nom, statut) VALUES ('FOU-0003', 'Temp', 'actif')")
    x("DELETE FROM fournisseurs WHERE code='FOU-0003'")                                        # séquence fournisseurs = 3, max(id) = 2
    x("INSERT INTO categories_prestations (code, libelle, actif, ordre) VALUES ('PLO', 'Plomberie', 1, 1)")
    x("INSERT INTO prestations (reference, designation, categorie_id, unite, type_prestation, prix_unitaire_ht, actif) "
      "VALUES ('PLO-001', 'Pose', 1, 'u', 'pose', '10', 1)")
    x("INSERT INTO prestation_garanties (prestation_id, garantie_type) VALUES (1, 'decennale')")
    x("INSERT INTO categories_depenses (code, libelle, actif, ordre) VALUES ('MAT', 'Matériaux', 1, 1)")
    x("INSERT INTO import_anomalies (type_entite, entite_id, ref_source, categorie, motif) VALUES ('client', 3, 'L-3', 'a_verifier', 'à rattacher')")

    def devis(num, client, statut, **kw):
        cols = {"numero": f"DEV-{num:05d}-26", "client_id": client, "client_snapshot": SNAP, "client_snapshot_version": 1,
                "entreprise_snapshot": SNAP, "entreprise_snapshot_version": 1, "chantier_snapshot": SNAP,
                "chantier_snapshot_version": 1, "date_creation": "2026-03-10", "statut": statut, "total_ht": "31.50",
                "objet": f"Objet {num}", "notes": f"Notes {num}"}
        cols.update(kw)
        x(f"INSERT INTO devis ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))
    devis(1, 1, "en_attente", date_validite="2026-04-10", remise_type="pourcentage", remise_valeur="10.00",
          acompte_type="montant", acompte_valeur="5.00")
    x("INSERT INTO devis_lignes (devis_id, ordre, prestation_id, reference_prestation, designation, quantite, unite, "
      "prix_unitaire_ht, remise_type, type_prestation, total_ht) VALUES (1, 1, 1, 'PLO-001', 'Pose prise', '2', 'u', '10.5', 'aucune', 'pose', '21.00')")
    x("INSERT INTO devis_lignes (devis_id, ordre, designation, quantite, unite, prix_unitaire_ht, remise_type, type_prestation, total_ht) "
      "VALUES (1, 2, 'Ligne libre', '1', 'u', '10.5', 'aucune', 'pose', '10.50')")
    x("INSERT INTO devis_ligne_garanties (ligne_id, garantie_type) VALUES (1, 'decennale'), (1, 'biennale')")
    x("UPDATE devis SET statut='accepte', date_acceptation='2026-03-12' WHERE id=1")
    devis(2, 2, "en_attente", total_ht="0.00")
    devis(3, 1, "refuse", date_refus="2026-03-20", motif_refus="Trop cher")
    devis(4, 3, "annule", cancelled_at=TS, motif_annulation="Annulé", origine="import", legacy_id="LD-4", legacy_data='{"k": 4}')
    devis(5, 1, "en_attente")
    x("DELETE FROM devis WHERE numero='DEV-00005-26'")                                         # séquence devis = 5, max(id) = 4
    bcn = x(ATTRIBUER, ("BCD", 26)).fetchone()[0]
    x("INSERT INTO bons_commande (numero, devis_id, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
      "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, date_acceptation, "
      "montant_contractuel_ht, remise_type, remise_valeur, acompte_type, acompte_valeur) "
      "SELECT ?, id, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, entreprise_snapshot_version, "
      "chantier_snapshot, chantier_snapshot_version, '2026-10-02', date_acceptation, total_ht, remise_type, remise_valeur, "
      "acompte_type, acompte_valeur FROM devis WHERE id=1", (f"BCD-{bcn:05d}-26",))
    x("INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, prestation_id, reference_prestation, designation, description, quantite, "
      "unite, prix_unitaire_ht, remise_type, remise_valeur, type_prestation, total_ht) SELECT 1, id, ordre, prestation_id, "
      "reference_prestation, designation, description, quantite, unite, prix_unitaire_ht, remise_type, remise_valeur, "
      "type_prestation, total_ht FROM devis_lignes WHERE devis_id=1 ORDER BY ordre")
    x("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) SELECT bl.id, dg.garantie_type FROM bc_lignes bl "
      "JOIN devis_ligne_garanties dg ON dg.ligne_id = bl.devis_ligne_id")
    x("UPDATE bons_commande SET frozen_at=? WHERE id=1", (TS,))
    x("UPDATE devis SET frozen_at=? WHERE id=1", (TS,))
    x("INSERT INTO depenses (numero, fournisseur_id, bc_id, date_depense, montant, categorie_id, description) "
      "VALUES ('DEP-00001-26', 1, 1, '2026-10-02', '12.50', 1, 'Achat')")
    x("INSERT INTO depenses (numero, fournisseur_id, date_depense, montant, categorie_id, description, cancelled_at, motif_annulation) "
      "VALUES ('DEP-00002-26', 2, '2026-10-03', '8.00', 1, 'Achat 2', ?, 'Erreur')", (TS2,))


def base5_peuplee():
    db = migrer(5)
    peupler_rang5(db)
    return db


class Base(unittest.TestCase):
    """Base au rang 6 (001 à 005 puis 005a) et fabrication de données conformes au schéma V3.13."""

    def setUp(self):
        self.db = migrer()
        self._n = 0

    # --- utilitaires d'assertion -------------------------------------------------
    @staticmethod
    def _a(args):
        """Paramètres liés : accepte aussi un tuple unique (couple (sql, paramètres) construit par une fabrique)."""
        return args[0] if len(args) == 1 and isinstance(args[0], tuple) else args

    def refuse(self, sql, *args):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(sql, self._a(args))

    def refuse_inv(self, inv, sql, *args):
        """Refus levé par un trigger : le message porte l'identifiant de l'invariant."""
        with self.assertRaisesRegex(sqlite3.IntegrityError, inv):
            self.db.execute(sql, self._a(args))

    def refuse_check(self, sql, *args):
        """Refus levé par une contrainte (CHECK, NOT NULL, UNIQUE, FK) et non par un trigger."""
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.db.execute(sql, self._a(args))
        self.assertNotIn("INV-", str(cm.exception))

    def un(self, sql, *args):
        return self.db.execute(sql, self._a(args)).fetchone()

    def tous(self, sql, *args):
        return self.db.execute(sql, self._a(args)).fetchall()

    def essai(self, sql, *args):
        """Retourne None si l'instruction réussit, sinon le message d'erreur."""
        try:
            self.db.execute(sql, self._a(args))
            return None
        except sqlite3.IntegrityError as e:
            return str(e)

    def permis(self, sql, *args):
        """L'instruction réussit puis est annulée (la base reste inchangée)."""
        self.db.execute("SAVEPOINT s")
        try:
            self.db.execute(sql, self._a(args))
        finally:
            self.db.execute("ROLLBACK TO s")
            self.db.execute("RELEASE s")

    # --- fabrication de données : tranches 001 à 003 -------------------------------
    def client(self, **kw):
        self._n += 1
        cols = {"code": f"CLI-{self._n:04d}", "nom": "Dupont"}
        cols.update(kw)
        return self.db.execute(f"INSERT INTO clients ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                               tuple(cols.values())).lastrowid

    def fournisseur(self, **kw):
        self._n += 1
        cols = {"code": f"FOU-{self._n:04d}", "nom": "Fournisseur"}
        cols.update(kw)
        return self.db.execute(f"INSERT INTO fournisseurs ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                               tuple(cols.values())).lastrowid

    def prestation(self, ref="PLO-001"):
        self.db.execute("INSERT INTO categories_prestations (code, libelle, actif, ordre) VALUES (?, 'Libellé', 1, 1)", (f"C-{ref}",))
        cat = self.un("SELECT id FROM categories_prestations WHERE code=?", f"C-{ref}")[0]
        return self.db.execute("INSERT INTO prestations (reference, designation, categorie_id, unite, type_prestation, "
                               "prix_unitaire_ht, actif) VALUES (?, 'Désignation', ?, 'u', 'pose', '10', 1)", (ref, cat)).lastrowid

    def brouillon(self, client_id=None, **kw):
        """Devis brouillon : pas de numéro (PT-2)."""
        cols = {"numero": None, "client_id": client_id or self.client(), "client_snapshot": SNAP, "client_snapshot_version": 1,
                "entreprise_snapshot": SNAP, "entreprise_snapshot_version": 1, "chantier_snapshot": SNAP,
                "chantier_snapshot_version": 1, "date_creation": "2026-03-10", "statut": "brouillon", "total_ht": "0.00"}
        cols.update(kw)
        return self.db.execute(f"INSERT INTO devis ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                               tuple(cols.values())).lastrowid

    def snapshot_initial(self, d):
        total = self.un("SELECT total_ht FROM devis WHERE id=?", d)[0]
        self.db.execute("INSERT INTO devis_revisions (devis_id, revision, schema_contenu, contenu, total_ht, valide_at) "
                        "VALUES (?, NULL, 1, '{}', ?, ?)", (d, total, TS))

    def finaliser(self, d, numero=None):
        """Finalisation (INV-180) : snapshot de la version initiale, puis numéro attribué et statut en_attente dans un seul UPDATE."""
        self._n += 1
        numero = numero or f"DEV-{self._n:05d}-26"
        self.snapshot_initial(d)
        self.db.execute("UPDATE devis SET numero=?, statut='en_attente' WHERE id=?", (numero, d))
        return numero

    def devis(self, numero=None, client_id=None, **kw):
        """Devis en_attente (brouillon finalisé)."""
        d = self.brouillon(client_id=client_id, **kw)
        self.finaliser(d, numero)
        return d

    def devis_direct(self, statut="en_attente", **kw):
        """Devis inséré directement dans l'état voulu (conforme aux CHECK), sans snapshot ni ligne : pour les scénarios d'isolation."""
        self._n += 1
        cols = {"numero": None if statut == "brouillon" else f"DEV-{self._n:05d}-26", "client_id": self.client(),
                "client_snapshot": SNAP, "client_snapshot_version": 1, "entreprise_snapshot": SNAP, "entreprise_snapshot_version": 1,
                "chantier_snapshot": SNAP, "chantier_snapshot_version": 1, "date_creation": "2026-03-10", "statut": statut,
                "total_ht": "10.00"}
        if statut == "accepte":
            cols["date_acceptation"] = "2026-03-12"
        elif statut == "refuse":
            cols["date_refus"] = "2026-03-15"
            cols["motif_refus"] = "Trop cher"
        elif statut == "annule":
            cols["cancelled_at"] = TS
            cols["motif_annulation"] = "Annulation"
        cols.update(kw)
        return self.db.execute(f"INSERT INTO devis ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                               tuple(cols.values())).lastrowid

    def revision_directe(self):
        d = self.devis_direct("brouillon")
        return self.db.execute("INSERT INTO devis_revisions (devis_id, revision, schema_contenu, contenu, total_ht, valide_at) "
                               "VALUES (?, NULL, 1, '{}', '10.00', ?)", (d, TS)).lastrowid

    def ligne(self, devis_id, ordre=1, **kw):
        cols = {"devis_id": devis_id, "ordre": ordre, "designation": "Pose prise", "quantite": "2", "unite": "u",
                "prix_unitaire_ht": "10.5", "remise_type": "aucune", "type_prestation": "pose", "total_ht": "21.00"}
        cols.update(kw)
        return self.db.execute(f"INSERT INTO devis_lignes ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                               tuple(cols.values())).lastrowid

    def garantie(self, ligne_id, type_="decennale"):
        return self.db.execute("INSERT INTO devis_ligne_garanties (ligne_id, garantie_type) VALUES (?, ?)", (ligne_id, type_)).lastrowid

    def accepter(self, d):
        self.db.execute("UPDATE devis SET statut='accepte', date_acceptation='2026-03-12' WHERE id=?", (d,))

    def geler_devis(self, d):
        self.db.execute("UPDATE devis SET frozen_at=? WHERE id=?", (TS, d))

    def refuser(self, d):
        self.db.execute("UPDATE devis SET statut='refuse', date_refus='2026-03-15', motif_refus='Trop cher' WHERE id=?", (d,))

    def annuler_devis(self, d):
        self.db.execute("UPDATE devis SET statut='annule', cancelled_at=?, motif_annulation='Annulation' WHERE id=?", (TS, d))

    def contenu_brouillon(self, d, lignes=2):
        """Ligne 1 (prestation du catalogue, deux garanties) et ligne 2 libre, posées pendant le brouillon (TR-11)."""
        self._n += 1
        l1 = self.ligne(d, 1, prestation_id=self.prestation(f"PLO-{self._n:03d}"), reference_prestation="PLO-X")
        g1, g2 = self.garantie(l1, "decennale"), self.garantie(l1, "biennale")
        l2 = self.ligne(d, 2, designation="Ligne libre", total_ht="10.50", quantite="1") if lignes >= 2 else None
        return l1, l2, g1, g2

    def devis_en_etat(self, etat, client_id=None):
        """Devis dans l'état voulu, avec ses lignes (posées en brouillon) : brouillon, en_attente, revision (en_attente avec
        revision_en_cours = 1), accepte, accepte_gele, refuse, annule."""
        d = self.brouillon(client_id=client_id, total_ht="31.50", remise_type="pourcentage", remise_valeur="10.00",
                           acompte_type="montant", acompte_valeur="5.00", objet="Objet", notes="Notes", date_validite="2026-04-10")
        l1, l2, g1, g2 = self.contenu_brouillon(d)
        if etat != "brouillon":
            self.finaliser(d)
        if etat == "revision":
            self.db.execute("UPDATE devis SET revision_en_cours=1 WHERE id=?", (d,))
        elif etat in ("accepte", "accepte_gele"):
            self.accepter(d)
            if etat == "accepte_gele":
                self.geler_devis(d)
        elif etat == "refuse":
            self.refuser(d)
        elif etat == "annule":
            self.annuler_devis(d)
        elif etat not in ("brouillon", "en_attente"):
            raise ValueError(etat)
        return types.SimpleNamespace(d=d, l1=l1, l2=l2, g1=g1, g2=g2)

    def devis_accepte(self, client_id=None, lignes=2, **kw):
        """Devis accepté non gelé : ligne 1 (prestation du catalogue, deux garanties), ligne 2 libre sans garantie."""
        kw.setdefault("total_ht", "31.50")
        kw.setdefault("remise_type", "pourcentage")
        kw.setdefault("remise_valeur", "10.00")
        kw.setdefault("acompte_type", "montant")
        kw.setdefault("acompte_valeur", "5.00")
        d = self.brouillon(client_id=client_id, **kw)
        if lignes >= 1:
            self.contenu_brouillon(d, lignes)
        self.finaliser(d)
        self.accepter(d)
        return d

    # --- fabrication de données : tranche 004 (ce que fait le service de création) ----
    def creer_bc(self, d=None, numero=None, lignes=True, **kw):
        d = d or self.devis_accepte()
        s = self.db.execute("SELECT client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                            "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, "
                            "COALESCE(date_acceptation, '2026-03-12'), total_ht, remise_type, remise_valeur, "
                            "acompte_type, acompte_valeur FROM devis WHERE id=?", (d,)).fetchone()
        cols = dict(zip(["client_id", "client_snapshot", "client_snapshot_version", "entreprise_snapshot",
                         "entreprise_snapshot_version", "chantier_snapshot", "chantier_snapshot_version",
                         "date_acceptation", "montant_contractuel_ht", "remise_type", "remise_valeur", "acompte_type",
                         "acompte_valeur"], s))
        cols["devis_id"] = d
        cols["date_creation"] = kw.pop("date_creation", "2026-10-02")
        cols.update(kw)
        if numero is None:
            yy = cols["date_creation"][2:4]
            numero = f"BCD-{self.un(ATTRIBUER, 'BCD', int(yy))[0]:05d}-{yy}"
        cols["numero"] = numero
        b = self.db.execute(f"INSERT INTO bons_commande ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                            tuple(cols.values())).lastrowid
        if lignes:
            self.copier_lignes(b)
        return b

    def copier_lignes(self, b, max_ordre=99):
        self.db.execute("INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, prestation_id, reference_prestation, designation, "
                        "description, quantite, unite, prix_unitaire_ht, remise_type, remise_valeur, type_prestation, total_ht) "
                        "SELECT ?, dl.id, dl.ordre, dl.prestation_id, dl.reference_prestation, dl.designation, dl.description, "
                        "dl.quantite, dl.unite, dl.prix_unitaire_ht, dl.remise_type, dl.remise_valeur, dl.type_prestation, dl.total_ht "
                        "FROM devis_lignes dl JOIN bons_commande b ON b.devis_id = dl.devis_id WHERE b.id = ? AND dl.ordre <= ? ORDER BY dl.ordre",
                        (b, b, max_ordre))
        self.db.execute("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) SELECT bl.id, dg.garantie_type "
                        "FROM bc_lignes bl JOIN devis_ligne_garanties dg ON dg.ligne_id = bl.devis_ligne_id WHERE bl.bc_id = ?", (b,))

    def ligne_bc(self, b, dl, ordre, **kw):
        r = self.db.execute("SELECT prestation_id, reference_prestation, designation, description, quantite, unite, "
                            "prix_unitaire_ht, remise_type, remise_valeur, type_prestation, total_ht FROM devis_lignes WHERE id=?",
                            (dl,)).fetchone()
        cols = dict(zip(["prestation_id", "reference_prestation", "designation", "description", "quantite", "unite",
                         "prix_unitaire_ht", "remise_type", "remise_valeur", "type_prestation", "total_ht"], r))
        cols.update({"bc_id": b, "devis_ligne_id": dl, "ordre": ordre})
        cols.update(kw)
        return self.db.execute(f"INSERT INTO bc_lignes ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                               tuple(cols.values())).lastrowid

    def bc_ligne(self, b, ordre=1):
        return self.un("SELECT id FROM bc_lignes WHERE bc_id=? AND ordre=?", b, ordre)[0]

    def geler_bc(self, b):
        self.db.execute("UPDATE bons_commande SET frozen_at=? WHERE id=?", (TS, b))
        self.db.execute("UPDATE devis SET frozen_at=? WHERE id=(SELECT devis_id FROM bons_commande WHERE id=?)", (TS, b))

    def terminer_bc(self, b):
        self.db.execute("UPDATE bons_commande SET statut='termine', completed_at=?, date_100_facture='2026-10-02', "
                        "avancement='100.00', montant_deja_facture_ht=montant_contractuel_ht, updated_at=? WHERE id=?", (TS, TS, b))

    def annuler_bc(self, b):
        self.db.execute("UPDATE bons_commande SET statut='annule', cancelled_at=?, motif_annulation='Client renonce', "
                        "completed_at=NULL, date_100_facture=NULL, updated_at=? WHERE id=?", (TS, TS, b))

    def bc_en_etat(self, etat, client_id=None, dl3=False, **kw):
        """BC (avec lignes et garanties) dans l'état voulu : en_cours, gele, termine, annule, annule_gele.
        dl3=True ajoute au devis (avant la création du BC) une 3e ligne non copiée dans le BC."""
        d = self.brouillon(client_id=client_id, total_ht="31.50", remise_type="pourcentage", remise_valeur="10.00",
                           acompte_type="montant", acompte_valeur="5.00")
        dl1, dl2, _, _ = self.contenu_brouillon(d)
        extra = self.ligne(d, 3, designation="Ligne à venir", total_ht="5.00", quantite="1") if dl3 else None
        self.finaliser(d)
        self.accepter(d)
        b = self.creer_bc(d, lignes=False, **kw)
        self.copier_lignes(b, max_ordre=2)                                                         # la ligne 3 n'est pas copiée dans le BC
        if etat in ("gele", "termine", "annule_gele"):
            self.geler_bc(b)
        if etat == "termine":
            self.terminer_bc(b)
        if etat in ("annule", "annule_gele"):
            self.annuler_bc(b)
        elif etat not in ("en_cours", "gele", "termine"):
            raise ValueError(etat)
        return types.SimpleNamespace(
            d=d, b=b, dl1=dl1, dl2=dl2, dl3=extra, bl1=self.bc_ligne(b, 1), bl2=self.bc_ligne(b, 2),
            bg1=self.un("SELECT id FROM bc_ligne_garanties WHERE ligne_id=? AND garantie_type='decennale'", self.bc_ligne(b, 1))[0],
            bg2=self.un("SELECT id FROM bc_ligne_garanties WHERE ligne_id=? AND garantie_type='biennale'", self.bc_ligne(b, 1))[0])


def info_colonnes(db, table):
    """(nom, type, notnull, défaut, pk, caché) de PRAGMA table_xinfo."""
    return [tuple(r[1:]) for r in db.execute(f"PRAGMA table_xinfo({table})")]


def cles_etrangeres(db, table):
    """(table parente, colonne, colonne parente, on_update, on_delete)."""
    return sorted((r[2], r[3], r[4], r[5], r[6]) for r in db.execute(f"PRAGMA foreign_key_list({table})"))


def indexes_de(db, table):
    return sorted((r[1], r[2], r[3], r[4]) for r in db.execute(f"PRAGMA index_list({table})"))


TS_DEFAUT = "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"
INFO_CLIENTS = [("id", "INTEGER", 0, None, 1, 0), ("code", "TEXT", 1, None, 0, 0), ("nom", "TEXT", 1, None, 0, 0),
                ("prenom", "TEXT", 0, None, 0, 0), ("adresse", "TEXT", 0, None, 0, 0), ("cpville", "TEXT", 0, None, 0, 0),
                ("tel", "TEXT", 0, None, 0, 0), ("email", "TEXT", 0, None, 0, 0), ("notes", "TEXT", 0, None, 0, 0),
                ("created_at", "TEXT", 1, TS_DEFAUT, 0, 0), ("updated_at", "TEXT", 1, TS_DEFAUT, 0, 0),
                ("origine", "TEXT", 1, "'v6'", 0, 0), ("legacy_id", "TEXT", 0, None, 0, 0), ("legacy_data", "TEXT", 0, None, 0, 0),
                ("legacy_numero", "TEXT", 0, None, 0, 0)]
INFO_FOURNISSEURS = [("id", "INTEGER", 0, None, 1, 0), ("code", "TEXT", 1, None, 0, 0), ("nom", "TEXT", 1, None, 0, 0),
                     ("adresse", "TEXT", 0, None, 0, 0), ("cpville", "TEXT", 0, None, 0, 0), ("tel", "TEXT", 0, None, 0, 0),
                     ("email", "TEXT", 0, None, 0, 0), ("notes", "TEXT", 0, None, 0, 0),
                     ("created_at", "TEXT", 1, TS_DEFAUT, 0, 0), ("updated_at", "TEXT", 1, TS_DEFAUT, 0, 0)]
INFO_DEVIS = [("id", "INTEGER", 0, None, 1, 0), ("numero", "TEXT", 0, None, 0, 0), ("client_id", "INTEGER", 1, None, 0, 0),
              ("client_snapshot", "TEXT", 1, None, 0, 0), ("client_snapshot_version", "INTEGER", 1, None, 0, 0),
              ("entreprise_snapshot", "TEXT", 1, None, 0, 0), ("entreprise_snapshot_version", "INTEGER", 1, None, 0, 0),
              ("chantier_snapshot", "TEXT", 1, None, 0, 0), ("chantier_snapshot_version", "INTEGER", 1, None, 0, 0),
              ("date_creation", "TEXT", 1, None, 0, 0), ("date_validite", "TEXT", 0, None, 0, 0),
              ("date_acceptation", "TEXT", 0, None, 0, 0), ("date_refus", "TEXT", 0, None, 0, 0), ("objet", "TEXT", 0, None, 0, 0),
              ("notes", "TEXT", 0, None, 0, 0), ("statut", "TEXT", 1, None, 0, 0), ("revision", "INTEGER", 0, None, 0, 0),
              ("revision_en_cours", "INTEGER", 1, "0", 0, 0), ("remise_type", "TEXT", 1, "'aucune'", 0, 0),
              ("remise_valeur", "TEXT", 0, None, 0, 0), ("acompte_type", "TEXT", 1, "'aucun'", 0, 0),
              ("acompte_valeur", "TEXT", 0, None, 0, 0), ("total_ht", "TEXT", 1, None, 0, 0), ("frozen_at", "TEXT", 0, None, 0, 0),
              ("cancelled_at", "TEXT", 0, None, 0, 0), ("motif_refus", "TEXT", 0, None, 0, 0),
              ("motif_annulation", "TEXT", 0, None, 0, 0), ("created_at", "TEXT", 1, TS_DEFAUT, 0, 0),
              ("updated_at", "TEXT", 1, TS_DEFAUT, 0, 0), ("origine", "TEXT", 1, "'v6'", 0, 0), ("legacy_id", "TEXT", 0, None, 0, 0),
              ("legacy_data", "TEXT", 0, None, 0, 0)]
INFO_REVISIONS = [("id", "INTEGER", 0, None, 1, 0), ("devis_id", "INTEGER", 1, None, 0, 0), ("revision", "INTEGER", 0, None, 0, 0),
                  ("schema_contenu", "INTEGER", 1, None, 0, 0), ("contenu", "TEXT", 1, None, 0, 0),
                  ("total_ht", "TEXT", 1, None, 0, 0), ("valide_at", "TEXT", 1, None, 0, 0),
                  ("created_at", "TEXT", 1, TS_DEFAUT, 0, 0)]

# points d'échec injectés : le fichier est coupé juste avant le marqueur, puis une instruction qui échoue est ajoutée
POINTS_D_ECHEC = ["DROP TRIGGER tr_01_devis_numero_immuable;", "CREATE TABLE clients_new (", "DROP TABLE clients;",
                  "DROP INDEX idx_fournisseurs_statut;", "CREATE TABLE devis_new (", "DROP TABLE devis;",
                  "ALTER TABLE devis_new RENAME TO devis;", "CREATE TABLE devis_revisions (",
                  "CREATE TRIGGER tr_97_clients_no_delete", "CREATE TRIGGER tr_100_devis_revisions_insert",
                  "CREATE TRIGGER tr_12_bons_commande_annule"]


class Migration(unittest.TestCase):
    def test_T45_chaine_ordonnee_005_puis_005a(self):
        self.assertEqual(NOMS, ("001_initial.sql", "002_fournisseurs.sql", "003_devis.sql", "004_bons_commande.sql",
                                "005_depenses.sql", "005a_corrections_v313.sql"))
        self.assertEqual(sorted(p.name for p in MIGRATIONS.glob("*.sql"))[:6], sorted(NOMS))

    def test_T45_rang_6_et_reglages_de_connexion(self):
        db = migrer()
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 6)
        self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertEqual(db.execute("PRAGMA recursive_triggers").fetchone()[0], 1)
        self.assertEqual(migrer(5).execute("PRAGMA user_version").fetchone()[0], 5)

    def test_T45_le_fichier_ne_contient_ni_transaction_ni_pragma_ni_donnee_creee(self):
        sql = re.sub(r"\"[^\"]*\"|'[^']*'", "''", sans_commentaires(SQL_005A))                  # hors libellés de contraintes et messages
        for interdit in (r"\bBEGIN\s*;", r"\bBEGIN\s+(IMMEDIATE|EXCLUSIVE|DEFERRED|TRANSACTION)", r"\bCOMMIT\b", r"\bROLLBACK\b",
                         r"\bSAVEPOINT\b", r"\bPRAGMA\b", r"\bVACUUM\b", r"\bINSERT\s+OR\s+REPLACE\b", r"\bREPLACE\s+INTO\b"):
            with self.subTest(interdit=interdit):
                self.assertIsNone(re.search(interdit, sql, re.I))
        # les seules écritures de données sont la copie technique des lignes existantes et la conservation des séquences
        inserts = re.findall(r"\bINSERT\s+INTO\s+(\w+)", sql, re.I)
        self.assertEqual(sorted(inserts), ["clients_new", "devis_new", "garde_005a_foreign_keys_off", "garde_005a_user_version",
                                           "sqlite_sequence", "sqlite_sequence"])

    def test_T45_le_fichier_ne_touche_ni_001_ni_005_ni_les_objets_hors_perimetre(self):
        sql = sans_commentaires(SQL_005A)
        self.assertNotRegex(sql, r"\b(depenses|categories_depenses|categories_prestations|prestations|prestation_garanties|"
                                 r"import_anomalies)\b")
        # aucune table de la tranche 004 n'est reconstruite ; seuls deux triggers de bons_commande sont réécrits, un recréé
        self.assertEqual(sorted(re.findall(r"\bDROP\s+TABLE\s+(\w+)", sql, re.I)),
                         ["clients", "devis", "garde_005a_foreign_keys_off", "garde_005a_user_version"])
        self.assertEqual(sorted(re.findall(r"\bCREATE\s+(?:TEMP\s+)?TABLE\s+(\w+)", sql, re.I)),
                         ["clients_new", "devis_new", "devis_revisions", "garde_005a_foreign_keys_off", "garde_005a_user_version"])

    def test_T45_objets_exacts_au_rang_6(self):
        db = migrer()
        self.assertEqual(noms(db, "table"), TABLES_RANG6)
        self.assertEqual(noms(db, "index"), INDEXES_RANG6)
        self.assertEqual(noms(db, "trigger"), TRIGGERS_RANG6)
        self.assertEqual(noms(db, "view"), set())
        self.assertEqual(db.execute("SELECT count(*) FROM sqlite_temp_master").fetchone()[0], 0)       # gardes supprimées

    def test_T45_integrite_fk_et_user_version_apres_005a(self):
        for nom, db in (("fraiche", migrer()), ("peuplee", None)):
            with self.subTest(base=nom):
                if db is None:
                    db = base5_peuplee()
                    runner(db)
                self.assertEqual(db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
                self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 6)
                self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_T45_base_au_rang_5_puis_005a_donne_le_meme_schema_que_la_base_fraiche(self):
        fraiche = migrer()
        peuplee = base5_peuplee()
        runner(peuplee)
        vide5 = migrer(5)
        runner(vide5)
        self.assertEqual(objets(fraiche), objets(peuplee))
        self.assertEqual(objets(fraiche), objets(vide5))
        self.assertEqual(db_user_version(peuplee), 6)

    def test_T45_les_donnees_existantes_sont_conservees_table_par_table(self):
        db = base5_peuplee()
        avant = tout(db)
        anciens = {t: db.execute(f"SELECT {','.join(c)} FROM {t} ORDER BY id").fetchall()
                   for t, c in (("clients", [c for c in colonnes(db, "clients") if c != "statut"]),
                                ("fournisseurs", [c for c in colonnes(db, "fournisseurs") if c != "statut"]),
                                ("devis", COLONNES_DEVIS_5))}
        runner(db)
        apres = tout(db)
        for table in sorted(TABLES_RANG5 - {"clients", "fournisseurs", "devis"}):
            with self.subTest(table=table):
                self.assertEqual(avant[table], apres[table])
                self.assertGreater(len(apres[table]), 0)
        # clients et fournisseurs : mêmes lignes, sans la colonne statut
        self.assertEqual(anciens["clients"], apres["clients"])
        self.assertEqual(anciens["fournisseurs"], apres["fournisseurs"])
        self.assertEqual((len(apres["clients"]), len(apres["fournisseurs"])), (3, 2))
        # devis : mêmes valeurs ; revision NULL et revision_en_cours 0 ; aucun snapshot créé
        nouveau = db.execute(f"SELECT {','.join(COLONNES_DEVIS_5)} FROM devis ORDER BY id").fetchall()
        self.assertEqual(anciens["devis"], nouveau)
        self.assertEqual(len(nouveau), 4)
        self.assertEqual(db.execute("SELECT revision, revision_en_cours FROM devis").fetchall(), [(None, 0)] * 4)
        self.assertEqual(apres["devis_revisions"], [])
        self.assertEqual([r[0] for r in db.execute("SELECT id FROM devis ORDER BY id")], [1, 2, 3, 4])
        self.assertEqual([r[0] for r in db.execute("SELECT id FROM clients ORDER BY id")], [1, 2, 3])
        self.assertEqual([r[0] for r in db.execute("SELECT id FROM fournisseurs ORDER BY id")], [1, 2])
        # quelques valeurs relues explicitement (aucune conversion de type ni de format)
        self.assertEqual(db.execute("SELECT code, nom, prenom, email, origine, legacy_id, legacy_data, legacy_numero FROM clients WHERE id=3").fetchone(),
                         ("CLI-0003", "Durand", None, None, "import", "L-3", '{"k": 3}', "C-3"))
        self.assertEqual(db.execute("SELECT statut, date_refus, motif_refus FROM devis WHERE id=3").fetchone(), ("refuse", "2026-03-20", "Trop cher"))
        self.assertEqual(db.execute("SELECT statut, frozen_at, remise_type, remise_valeur, acompte_valeur FROM devis WHERE id=1").fetchone(),
                         ("accepte", TS, "pourcentage", "10.00", "5.00"))

    def test_T45_les_sequences_autoincrement_sont_conservees(self):
        db = base5_peuplee()
        avant = dict(db.execute("SELECT name, seq FROM sqlite_sequence").fetchall())
        self.assertEqual((avant["clients"], avant["fournisseurs"], avant["devis"]), (4, 3, 5))      # trous : séquence > max(id)
        runner(db)
        apres = dict(db.execute("SELECT name, seq FROM sqlite_sequence").fetchall())
        self.assertEqual(apres, avant)                                                              # aucune ligne en trop (pas de *_new)
        self.assertEqual(db.execute("INSERT INTO clients (code, nom) VALUES ('CLI-0005', 'N')").lastrowid, 5)
        self.assertEqual(db.execute("INSERT INTO fournisseurs (code, nom) VALUES ('FOU-0004', 'N')").lastrowid, 4)
        d = db.execute("INSERT INTO devis (client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                       "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, statut, total_ht) "
                       "VALUES (1, '{}', 1, '{}', 1, '{}', 1, '2026-03-10', 'brouillon', '0.00')").lastrowid
        self.assertEqual(d, 6)
        self.assertEqual(dict(db.execute("SELECT name, seq FROM sqlite_sequence").fetchall())["devis"], 6)

    def test_T45_sequence_conservee_meme_quand_la_table_est_vide(self):
        db = migrer(5)
        db.execute("INSERT INTO clients (code, nom) VALUES ('CLI-0001', 'A'), ('CLI-0002', 'B'), ('CLI-0003', 'C')")
        db.execute("DELETE FROM clients")
        db.execute("INSERT INTO fournisseurs (code, nom, statut) VALUES ('FOU-0001', 'A', 'actif')")
        db.execute("DELETE FROM fournisseurs")
        self.assertEqual(db.execute("SELECT seq FROM sqlite_sequence WHERE name='clients'").fetchone(), (3,))
        runner(db)
        self.assertEqual(db.execute("SELECT count(*) FROM clients").fetchone(), (0,))
        self.assertEqual(db.execute("SELECT seq FROM sqlite_sequence WHERE name='clients'").fetchone(), (3,))
        self.assertEqual(db.execute("SELECT seq FROM sqlite_sequence WHERE name='fournisseurs'").fetchone(), (1,))
        self.assertEqual(db.execute("INSERT INTO clients (code, nom) VALUES ('CLI-0004', 'D')").lastrowid, 4)
        self.assertEqual(db.execute("SELECT count(*) FROM sqlite_sequence WHERE name IN ('clients_new', 'devis_new')").fetchone(), (0,))

    def test_T45_sequence_jamais_regressive_quand_le_dernier_enregistrement_est_supprime(self):
        """Une reconstruction naïve (copie puis RENAME) ferait retomber la séquence au max(id) : 3 -> 2 pour clients, 2 -> 1 pour devis."""
        db = migrer(5)
        db.execute("INSERT INTO clients (code, nom) VALUES ('CLI-0001', 'A'), ('CLI-0002', 'B')")
        db.execute("DELETE FROM clients WHERE code='CLI-0002'")
        c3 = db.execute("INSERT INTO clients (code, nom) VALUES ('CLI-0003', 'C')").lastrowid
        db.execute("DELETE FROM clients WHERE id=?", (c3,))
        runner(db)
        self.assertEqual(db.execute("SELECT seq FROM sqlite_sequence WHERE name='clients'").fetchone(), (3,))
        self.assertEqual(db.execute("INSERT INTO clients (code, nom) VALUES ('CLI-0004', 'D')").lastrowid, 4)

    def test_T45_5a_est_atomique_un_echec_n_importe_ou_annule_tout(self):
        for point in POINTS_D_ECHEC:
            with self.subTest(echec_avant=point):
                db = base5_peuplee()
                avant, schema_avant = tout(db), objets(db)
                self.assertIn(point, SQL_005A)
                coupe = SQL_005A[:SQL_005A.index(point)] + "\nINSERT INTO table_inexistante_005a VALUES (1);\n"
                with self.assertRaises(sqlite3.Error):
                    runner(db, sql=coupe)
                self.assertFalse(db.in_transaction)
                self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 5)
                self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
                self.assertEqual(objets(db), schema_avant)
                self.assertEqual(tout(db), avant)
                self.assertEqual(db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
                runner(db)                                                                          # le rejeu complet réussit ensuite
                self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 6)

    def test_T45_echec_apres_la_derniere_instruction_annule_aussi(self):
        db = base5_peuplee()
        avant, schema_avant = tout(db), objets(db)
        with self.assertRaises(sqlite3.Error):
            runner(db, sql=SQL_005A + "\nINSERT INTO table_inexistante_005a VALUES (1);\n")
        self.assertEqual((db.execute("PRAGMA user_version").fetchone()[0], objets(db), tout(db)), (5, schema_avant, avant))

    def test_T45_le_commit_n_a_lieu_qu_apres_les_verifications(self):
        """Le runner pose user_version dans la transaction et ne valide qu'ensuite : une violation de clé étrangère découverte par
        foreign_key_check annule tout, user_version reste 5."""
        db = base5_peuplee()
        db.execute("PRAGMA foreign_keys=OFF")
        db.execute("INSERT INTO devis_lignes (devis_id, ordre, designation, quantite, unite, prix_unitaire_ht, remise_type, "
                   "type_prestation, total_ht) VALUES (999, 1, 'Orpheline', '1', 'u', '1', 'aucune', 'pose', '1.00')")
        db.execute("PRAGMA foreign_keys=ON")
        avant, schema_avant = tout(db), objets(db)
        with self.assertRaises(ErreurRunner):
            runner(db)
        self.assertEqual((db.execute("PRAGMA user_version").fetchone()[0], objets(db), tout(db)), (5, schema_avant, avant))

    def test_T45_rejeu_sur_une_base_deja_au_rang_6_est_refuse_sans_effet(self):
        db = migrer()
        avant, schema_avant = tout(db), objets(db)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "user_version = 5"):
            runner(db)
        self.assertEqual((db.execute("PRAGMA user_version").fetchone()[0], objets(db), tout(db)), (6, schema_avant, avant))

    def test_T45_version_incompatible_une_base_au_rang_4_ne_recoit_pas_005a(self):
        for rang in (1, 2, 3, 4):
            with self.subTest(rang=rang):
                db = migrer(rang)
                schema_avant = objets(db)
                with self.assertRaisesRegex(sqlite3.IntegrityError, "user_version = 5"):
                    runner(db)
                self.assertEqual((db.execute("PRAGMA user_version").fetchone()[0], objets(db)), (rang, schema_avant))
        db = sqlite3.connect(":memory:", isolation_level=None)                                       # base vide (user_version 0)
        with self.assertRaises(sqlite3.Error):
            runner(db)
        db = migrer(5)
        db.execute("PRAGMA user_version = 7")                                                         # base d'une version plus récente
        with self.assertRaisesRegex(sqlite3.IntegrityError, "user_version = 5"):
            runner(db)
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 7)

    def test_T45_la_chaine_normale_005_puis_005a_depuis_une_base_au_rang_4(self):
        db = migrer(4)
        appliquer(db, 5, SQLS[4])
        runner(db)
        self.assertEqual(objets(db), objets(migrer()))

    def test_T45_foreign_keys_actif_le_fichier_se_refuse_sans_rien_perdre(self):
        """Avec foreign_keys=ON, DROP TABLE devis supprimerait en silence les lignes liées en CASCADE : la garde l'interdit."""
        db = base5_peuplee()
        avant, schema_avant = tout(db), objets(db)
        self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "foreign_keys = OFF"):
            db.executescript(f"BEGIN IMMEDIATE;\n{SQL_005A}\nPRAGMA user_version = 6;\nCOMMIT;")
        if db.in_transaction:
            db.execute("ROLLBACK")
        self.assertEqual((db.execute("PRAGMA user_version").fetchone()[0], objets(db), tout(db)), (5, schema_avant, avant))

    def test_T45_les_gardes_ne_laissent_aucune_trace(self):
        db = migrer()
        self.assertEqual(db.execute("SELECT count(*) FROM sqlite_temp_master").fetchone()[0], 0)
        self.assertFalse([n for n in noms(db, "table") if "garde" in n])

    def test_T45_non_regression_des_objets_hors_perimetre_sql_identique(self):
        db5, db6 = migrer(5), migrer()
        tables_touchees = {"clients", "fournisseurs", "devis", "devis_lignes", "devis_ligne_garanties"}
        s5 = {o[1]: o for o in objets(db5)}
        s6 = {o[1]: o for o in objets(db6)}
        for nom in sorted(TRIGGERS_INCHANGES):
            with self.subTest(trigger_inchange=nom):
                self.assertEqual(s5[nom], s6[nom])
        for nom in sorted(TRIGGERS_RECREES_IDENTIQUES):
            with self.subTest(trigger_recree_identique=nom):
                self.assertEqual(s5[nom], s6[nom])                                                  # même table, même SQL, au caractère près
        for nom in sorted((INDEXES_RANG5 & INDEXES_RANG6)):
            with self.subTest(index=nom):
                self.assertEqual(s5[nom], s6[nom])
        for nom in sorted(TABLES_RANG5 - {"clients", "fournisseurs", "devis"}):
            with self.subTest(table=nom):
                self.assertEqual(s5[nom], s6[nom])
        self.assertTrue(tables_touchees)

    def test_T45_G3_les_triggers_bc_non_references_a_clients_ni_devis_restent_ceux_de_004(self):
        db5, db6 = migrer(5), migrer()
        for nom in sorted(TRIGGERS_004_G3 | {"tr_12_bons_commande_modifiable"}):
            with self.subTest(trigger=nom):
                self.assertEqual(sql_de(db5, nom), sql_de(db6, nom))
                self.assertNotRegex(sql_de(db6, nom).lower(), r"\b(from|join)\s+(clients|devis)\b")

    def test_T45_G1_les_triggers_tr12_gele_et_annule_ne_lisent_plus_clients(self):
        db5, db6 = migrer(5), migrer()
        for nom in ("tr_12_bons_commande_gele", "tr_12_bons_commande_annule"):
            with self.subTest(trigger=nom):
                self.assertRegex(sql_de(db5, nom), r"FROM clients")
                self.assertNotRegex(sql_de(db6, nom).lower(), r"clients|a_rattacher|statut\s+from")
                col5 = set(re.findall(r"NEW\.(\w+) IS NOT OLD\.\1", sql_de(db5, nom)))
                col6 = set(re.findall(r"NEW\.(\w+) IS NOT OLD\.\1", sql_de(db6, nom)))
                # mêmes colonnes verrouillées ; client_id devient inconditionnellement verrouillé (le client 'a_rattacher' n'existe plus)
                self.assertEqual(col6, col5)
                self.assertIn("client_id", col6)
                self.assertEqual(sql_de(db5, nom).split("WHEN")[1].split("(NEW.id")[0],
                                 sql_de(db6, nom).split("WHEN")[1].split("(NEW.id")[0])             # même condition d'application

    def test_T45_G2_tr17_tr18_tr14_devis_recrees_sur_la_nouvelle_table_devis(self):
        db = migrer()
        for nom, table in (("tr_17_bons_commande_insert", "bons_commande"), ("tr_18_devis_statut_avec_bc", "devis"),
                           ("tr_14_devis_frozen_at", "devis")):
            with self.subTest(trigger=nom):
                self.assertEqual(db.execute("SELECT tbl_name FROM sqlite_master WHERE name=?", (nom,)).fetchone()[0], table)


def db_user_version(db):
    return db.execute("PRAGMA user_version").fetchone()[0]


class Reconstruction(Base):
    """Structure exacte, contraintes, index et clés étrangères des tables reconstruites ou modifiées : clients, fournisseurs, devis, et
    de la table créée devis_revisions."""

    # --- clients -------------------------------------------------------------------------
    def test_T45_clients_structure_exacte(self):
        self.assertEqual(info_colonnes(self.db, "clients"), INFO_CLIENTS)
        self.assertEqual(colonnes(self.db, "clients"), COLONNES_CLIENTS_ATTENDUES)
        strict = self.un("SELECT strict FROM pragma_table_list WHERE name='clients'")[0]
        self.assertEqual(strict, 1)
        sql = sql_de(self.db, "clients")
        self.assertIn("AUTOINCREMENT", sql)
        self.assertNotRegex(sql, r"statut|a_rattacher")
        self.assertEqual(indexes_de(self.db, "clients"), [("sqlite_autoindex_clients_1", 1, "u", 0)])
        self.assertEqual(cles_etrangeres(self.db, "clients"), [])
        self.assertEqual(self.un("SELECT count(*) FROM sqlite_master WHERE tbl_name='clients' AND type='index' AND name NOT LIKE 'sqlite_%'")[0], 0)

    def test_INV_183_clients_sans_statut_ni_archivage(self):
        self.refuse_op("INSERT INTO clients (code, nom, statut) VALUES ('CLI-0100', 'X', 'actif')")
        self.refuse_op("UPDATE clients SET statut='actif' WHERE id=1")
        self.refuse_op("SELECT statut FROM clients")
        self.assertNotIn("statut", colonnes(self.db, "fournisseurs"))
        self.refuse_op("INSERT INTO fournisseurs (code, nom, statut) VALUES ('FOU-0100', 'X', 'actif')")
        self.refuse_op("SELECT statut FROM fournisseurs")

    def test_T45_clients_contraintes(self):
        invalides = [("code trop court", {"code": "CLI-12"}), ("code minuscule", {"code": "cli-0012"}),
                     ("code trop long", {"code": "CLI-00123"}), ("code lettres", {"code": "CLI-00A2"}), ("code NULL", {"code": None}),
                     ("nom vide", {"nom": ""}), ("nom NULL", {"nom": None}), ("origine inconnue", {"origine": "autre"}),
                     ("v6 avec legacy_id", {"legacy_id": "x"}), ("v6 avec legacy_data", {"legacy_data": "{}"}),
                     ("v6 avec legacy_numero", {"legacy_numero": "X-1"}),
                     ("import legacy_numero = code", {"origine": "import", "legacy_numero": "CLI-0200"}),
                     ("legacy_data non JSON", {"origine": "import", "legacy_data": "{pas du json"}),
                     ("created_at sans millisecondes", {"created_at": "2026-10-01T10:00:00Z"}),
                     ("created_at date seule", {"created_at": "2026-10-01"}), ("updated_at libre", {"updated_at": "hier"}),
                     ("created_at NULL", {"created_at": None}), ("origine NULL", {"origine": None})]
        for libelle, mod in invalides:
            with self.subTest(cas=libelle):
                cols = {"code": "CLI-0200", "nom": "Dupont"}
                cols.update(mod)
                self.refuse_check(f"INSERT INTO clients ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", *cols.values())
        self.client(code="CLI-0300")
        self.refuse_check("INSERT INTO clients (code, nom) VALUES ('CLI-0300', 'Doublon')")             # UNIQUE(code)
        c = self.client(origine="import", legacy_id="L-1", legacy_data='{"a": 1}', legacy_numero="OLD-9", prenom="P", adresse="A",
                        cpville="V", tel="T", email="E", notes="N")
        self.assertEqual(self.un("SELECT origine, legacy_id, legacy_numero FROM clients WHERE id=?", c), ("import", "L-1", "OLD-9"))

    def test_T45_clients_valeurs_par_defaut(self):
        c = self.client()
        origine, cree, maj = self.un("SELECT origine, created_at, updated_at FROM clients WHERE id=?", c)
        self.assertEqual(origine, "v6")
        self.assertRegex(cree, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
        self.assertRegex(maj, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")

    def test_T45_clients_cles_etrangeres_entrantes_en_restrict(self):
        for enfant in ("devis", "bons_commande"):
            with self.subTest(table=enfant):
                self.assertIn(("clients", "client_id", "id", "NO ACTION", "RESTRICT"), cles_etrangeres(self.db, enfant))
        bc = self.bc_en_etat("en_cours")
        c = self.un("SELECT client_id FROM devis WHERE id=?", bc.d)[0]
        self.db.execute("DROP TRIGGER tr_97_clients_no_delete")                                        # la FK refuse seule
        self.refuse_check("DELETE FROM clients WHERE id=?", c)
        self.db.execute("PRAGMA defer_foreign_keys=OFF")
        c2 = self.client()
        self.db.execute("DELETE FROM clients WHERE id=?", (c2,))                                         # client sans devis : la FK laisse faire

    # --- fournisseurs ---------------------------------------------------------------------
    def test_T45_fournisseurs_structure_exacte(self):
        self.assertEqual(info_colonnes(self.db, "fournisseurs"), INFO_FOURNISSEURS)
        self.assertEqual(self.un("SELECT strict FROM pragma_table_list WHERE name='fournisseurs'")[0], 1)
        self.assertNotRegex(sql_de(self.db, "fournisseurs"), r"statut")
        self.assertEqual(indexes_de(self.db, "fournisseurs"), [("sqlite_autoindex_fournisseurs_1", 1, "u", 0)])
        self.assertEqual(self.un("SELECT count(*) FROM sqlite_master WHERE name='idx_fournisseurs_statut'")[0], 0)
        self.assertEqual(cles_etrangeres(self.db, "fournisseurs"), [])

    def test_T45_fournisseurs_contraintes_conservees(self):
        for libelle, mod in (("code libre", {"code": "F-1"}), ("code minuscule", {"code": "fou-0001"}), ("nom vide", {"nom": ""}),
                             ("created_at libre", {"created_at": "hier"}), ("updated_at libre", {"updated_at": "hier"})):
            with self.subTest(cas=libelle):
                cols = {"code": "FOU-0200", "nom": "F"}
                cols.update(mod)
                self.refuse_check(f"INSERT INTO fournisseurs ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", *cols.values())
        f = self.fournisseur(code="FOU-0300", adresse="A", cpville="V", tel="T", email="E", notes="N")
        self.refuse_check("INSERT INTO fournisseurs (code, nom) VALUES ('FOU-0300', 'Doublon')")

    def test_T45_fournisseurs_la_cle_etrangere_de_depenses_reste_en_restrict(self):
        self.assertIn(("fournisseurs", "fournisseur_id", "id", "NO ACTION", "RESTRICT"), cles_etrangeres(self.db, "depenses"))
        f = self.fournisseur()
        cat = self.db.execute("INSERT INTO categories_depenses (code, libelle, actif, ordre) VALUES ('MAT', 'M', 1, 1)").lastrowid
        self.db.execute("INSERT INTO depenses (numero, fournisseur_id, date_depense, montant, categorie_id, description) "
                        "VALUES ('DEP-00001-26', ?, '2026-10-02', '1.00', ?, 'x')", (f, cat))
        self.db.execute("DROP TRIGGER tr_97_fournisseurs_no_delete")
        self.refuse_check("DELETE FROM fournisseurs WHERE id=?", f)

    # --- devis ----------------------------------------------------------------------------
    def test_T45_devis_structure_exacte(self):
        self.assertEqual(info_colonnes(self.db, "devis"), INFO_DEVIS)
        self.assertEqual(colonnes(self.db, "devis"), COLONNES_DEVIS)
        self.assertEqual(self.un("SELECT strict FROM pragma_table_list WHERE name='devis'")[0], 1)
        self.assertIn("AUTOINCREMENT", sql_de(self.db, "devis"))
        self.assertEqual(indexes_de(self.db, "devis"), [("idx_devis_client_id", 0, "c", 0), ("idx_devis_date_creation", 0, "c", 0),
                                                       ("idx_devis_statut", 0, "c", 0), ("sqlite_autoindex_devis_1", 1, "u", 0)])
        for index, colonne in (("idx_devis_client_id", "client_id"), ("idx_devis_statut", "statut"),
                               ("idx_devis_date_creation", "date_creation"), ("sqlite_autoindex_devis_1", "numero")):
            with self.subTest(index=index):
                self.assertEqual([r[2] for r in self.db.execute(f"PRAGMA index_info({index})")], [colonne])
        self.assertEqual(cles_etrangeres(self.db, "devis"), [("clients", "client_id", "id", "NO ACTION", "RESTRICT")])
        self.assertNotIn("devis_origine_id", colonnes(self.db, "devis"))                                  # PT-7 ouvert : non créé

    def test_T45_devis_cles_etrangeres_entrantes_inchangees(self):
        self.assertEqual(cles_etrangeres(self.db, "devis_lignes"),
                         [("devis", "devis_id", "id", "NO ACTION", "CASCADE"), ("prestations", "prestation_id", "id", "NO ACTION", "RESTRICT")])
        self.assertEqual(cles_etrangeres(self.db, "devis_ligne_garanties"), [("devis_lignes", "ligne_id", "id", "NO ACTION", "CASCADE")])
        self.assertIn(("devis", "devis_id", "id", "NO ACTION", "RESTRICT"), cles_etrangeres(self.db, "bons_commande"))
        self.assertEqual(cles_etrangeres(self.db, "devis_revisions"), [("devis", "devis_id", "id", "NO ACTION", "RESTRICT")])
        # les SQL des enfants citent toujours « devis » (aucun nom provisoire devis_new / clients_new après RENAME)
        for table in ("devis_lignes", "bons_commande", "devis_revisions"):
            with self.subTest(table=table):
                self.assertNotIn("_new", sql_de(self.db, table))
        self.assertNotIn("_new", sql_de(self.db, "devis"))
        self.assertNotIn("_new", sql_de(self.db, "clients"))

    def test_T45_devis_statuts_et_numero_brouillon(self):
        n = [0]

        def ins(**mod):
            n[0] += 1
            cols = {"numero": f"DEV-{n[0]:05d}-26", "client_id": 1, "client_snapshot": SNAP, "client_snapshot_version": 1,
                    "entreprise_snapshot": SNAP, "entreprise_snapshot_version": 1, "chantier_snapshot": SNAP,
                    "chantier_snapshot_version": 1, "date_creation": "2026-03-10", "statut": "en_attente", "total_ht": "10.00"}
            cols.update(mod)
            return f"INSERT INTO devis ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values())
        self.client()
        valides = [("brouillon sans numero", {"numero": None, "statut": "brouillon"}), ("en_attente", {}),
                   ("accepte", {"statut": "accepte", "date_acceptation": "2026-03-12"}),
                   ("accepte gele", {"statut": "accepte", "date_acceptation": "2026-03-12", "frozen_at": TS}),
                   ("refuse", {"statut": "refuse", "date_refus": "2026-03-15"}),
                   ("annule", {"statut": "annule", "cancelled_at": TS, "motif_annulation": "m"}),
                   ("annule gele", {"statut": "annule", "cancelled_at": TS, "motif_annulation": "m", "frozen_at": TS}),
                   ("en_attente en revision", {"revision": 2, "revision_en_cours": 1}),
                   ("en_attente revision 1", {"revision": 1}),
                   ("numero historique importe", {"numero": "ANCIEN/2019-7", "origine": "import", "legacy_id": "L7"}),
                   ("brouillon importe", {"numero": None, "statut": "brouillon", "origine": "import"})]
        for libelle, mod in valides:
            with self.subTest(valide=libelle):
                sql, args = ins(**mod)
                self.db.execute(sql, args)
        invalides = [("statut inconnu", {"statut": "termine"}), ("statut NULL", {"statut": None}),
                     ("brouillon avec numero", {"statut": "brouillon"}),
                     ("en_attente sans numero", {"numero": None}), ("accepte sans numero", {"numero": None, "statut": "accepte", "date_acceptation": "2026-03-12"}),
                     ("refuse sans numero", {"numero": None, "statut": "refuse", "date_refus": "2026-03-15"}),
                     ("annule sans numero", {"numero": None, "statut": "annule", "cancelled_at": TS, "motif_annulation": "m"}),
                     ("brouillon avec revision", {"numero": None, "statut": "brouillon", "revision": 1}),
                     ("brouillon en revision", {"numero": None, "statut": "brouillon", "revision_en_cours": 1}),
                     ("accepte en revision", {"statut": "accepte", "date_acceptation": "2026-03-12", "revision_en_cours": 1}),
                     ("refuse en revision", {"statut": "refuse", "date_refus": "2026-03-15", "revision_en_cours": 1}),
                     ("annule en revision", {"statut": "annule", "cancelled_at": TS, "motif_annulation": "m", "revision_en_cours": 1}),
                     ("revision 0", {"revision": 0}), ("revision negative", {"revision": -1}),
                     ("revision_en_cours 2", {"revision_en_cours": 2}), ("revision_en_cours NULL", {"revision_en_cours": None}),
                     ("numero vide", {"numero": ""}), ("numero sans format", {"numero": "DEV-1"}),
                     ("numero lettres", {"numero": "DEV-0000A-26"}), ("numero annee differente de date_creation", {"numero": "DEV-00099-27"}),
                     ("numero minuscule", {"numero": "dev-00099-26"}), ("numero vide importe", {"numero": "", "origine": "import"}),
                     ("accepte sans date_acceptation", {"statut": "accepte"}), ("refuse sans date_refus", {"statut": "refuse"}),
                     ("annule sans cancelled_at", {"statut": "annule", "motif_annulation": "m"}),
                     ("annule sans motif", {"statut": "annule", "cancelled_at": TS}),
                     ("annule motif vide", {"statut": "annule", "cancelled_at": TS, "motif_annulation": ""}),
                     ("cancelled_at sans annule", {"cancelled_at": TS, "motif_annulation": "m"}),
                     ("frozen_at en_attente", {"frozen_at": TS}), ("frozen_at refuse", {"statut": "refuse", "date_refus": "2026-03-15", "frozen_at": TS}),
                     ("frozen_at libre", {"statut": "accepte", "date_acceptation": "2026-03-12", "frozen_at": "hier"}),
                     ("cancelled_at libre", {"statut": "annule", "cancelled_at": "hier", "motif_annulation": "m"}),
                     ("created_at libre", {"created_at": "hier"}), ("updated_at libre", {"updated_at": "hier"}),
                     ("origine inconnue", {"origine": "x"}), ("v6 avec legacy_id", {"legacy_id": "x"}),
                     ("v6 avec legacy_data", {"legacy_data": "{}"}), ("legacy_data non JSON", {"origine": "import", "legacy_data": "{x"}),
                     ("client_id NULL", {"client_id": None}), ("client_id inconnu", {"client_id": 9999}),
                     ("snapshot non JSON", {"client_snapshot": "x"}), ("snapshot entreprise non JSON", {"entreprise_snapshot": "x"}),
                     ("snapshot chantier non JSON", {"chantier_snapshot": "x"}), ("snapshot NULL", {"client_snapshot": None})]
        for libelle, mod in invalides:
            with self.subTest(invalide=libelle):
                sql, args = ins(**mod)
                self.refuse_check(sql, *args)
        sql, args = ins(numero="DEV-00002-26")
        self.refuse_check(sql, *args)                                                                  # UNIQUE(numero)
        sql, args = ins(numero=None, statut="brouillon")
        self.db.execute(sql, args)
        sql, args = ins(numero=None, statut="brouillon")
        self.db.execute(sql, args)                                                                     # plusieurs brouillons : NULL distincts

    def test_T45_devis_dates_remises_acomptes_et_totaux(self):
        c = self.client()

        def ins(**mod):
            self._n += 1
            cols = {"numero": f"DEV-{self._n:05d}-26", "client_id": c, "client_snapshot": SNAP, "client_snapshot_version": 1,
                    "entreprise_snapshot": SNAP, "entreprise_snapshot_version": 1, "chantier_snapshot": SNAP,
                    "chantier_snapshot_version": 1, "date_creation": "2026-03-10", "statut": "en_attente", "total_ht": "10.00"}
            cols.update(mod)
            return f"INSERT INTO devis ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values())
        invalides = [("date_creation impossible", {"date_creation": "2026-02-30"}), ("date_creation format", {"date_creation": "2026-3-1"}),
                     ("date_creation NULL", {"date_creation": None}), ("date_creation vide", {"date_creation": ""}),
                     ("date_validite avant creation", {"date_validite": "2026-03-09"}), ("date_validite format", {"date_validite": "10/04/2026"}),
                     ("date_acceptation impossible", {"statut": "accepte", "date_acceptation": "2026-13-01"}),
                     ("date_refus impossible", {"statut": "refuse", "date_refus": "2026-04-31"}),
                     ("total vide", {"total_ht": ""}), ("total sans decimales", {"total_ht": "10"}), ("total une decimale", {"total_ht": "10.0"}),
                     ("total trois decimales", {"total_ht": "10.000"}), ("total negatif", {"total_ht": "-10.00"}),
                     ("total zero initial", {"total_ht": "010.00"}), ("total deux points", {"total_ht": "1.0.00"}),
                     ("total lettres", {"total_ht": "1a.00"}), ("total NULL", {"total_ht": None}),
                     ("remise aucune avec valeur", {"remise_type": "aucune", "remise_valeur": "1.00"}),
                     ("remise pourcentage sans valeur", {"remise_type": "pourcentage"}),
                     ("remise montant sans valeur", {"remise_type": "montant"}),
                     ("remise pourcentage > 100", {"remise_type": "pourcentage", "remise_valeur": "100.01"}),
                     ("remise type inconnu", {"remise_type": "x", "remise_valeur": "1.00"}),
                     ("remise valeur format", {"remise_type": "montant", "remise_valeur": "1"}),
                     ("acompte aucun avec valeur", {"acompte_type": "aucun", "acompte_valeur": "1.00"}),
                     ("acompte pourcentage sans valeur", {"acompte_type": "pourcentage"}),
                     ("acompte pourcentage > 100", {"acompte_type": "pourcentage", "acompte_valeur": "100.01"}),
                     ("acompte type inconnu", {"acompte_type": "x", "acompte_valeur": "1.00"}),
                     ("acompte valeur format", {"acompte_type": "montant", "acompte_valeur": "1.5"})]
        for libelle, mod in invalides:
            with self.subTest(invalide=libelle):
                sql, args = ins(**mod)
                self.refuse_check(sql, *args)
        for libelle, mod in (("remise 100.00 %", {"remise_type": "pourcentage", "remise_valeur": "100.00"}),
                             ("remise montant", {"remise_type": "montant", "remise_valeur": "0.50"}),
                             ("acompte 100.00 %", {"acompte_type": "pourcentage", "acompte_valeur": "100.00"}),
                             ("acompte montant", {"acompte_type": "montant", "acompte_valeur": "2.00"}),
                             ("date_validite = date_creation", {"date_validite": "2026-03-10"}), ("total 0.00", {"total_ht": "0.00"})):
            with self.subTest(valide=libelle):
                sql, args = ins(**mod)
                self.db.execute(sql, args)

    def test_T45_devis_valeurs_par_defaut(self):
        d = self.db.execute("INSERT INTO devis (client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                            "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, statut, total_ht) "
                            "VALUES (?, '{}', 1, '{}', 1, '{}', 1, '2026-03-10', 'brouillon', '0.00')", (self.client(),)).lastrowid
        self.assertEqual(self.un("SELECT numero, revision, revision_en_cours, remise_type, acompte_type, origine, frozen_at FROM devis WHERE id=?", d),
                         (None, None, 0, "aucune", "aucun", "v6", None))
        self.assertRegex(self.un("SELECT created_at FROM devis WHERE id=?", d)[0], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")

    def test_T45_devis_les_lignes_et_garanties_existantes_restent_rattachees(self):
        db = base5_peuplee()
        avant_lignes = db.execute("SELECT * FROM devis_lignes ORDER BY id").fetchall()
        avant_gar = db.execute("SELECT * FROM devis_ligne_garanties ORDER BY id").fetchall()
        avant_bc = db.execute("SELECT * FROM bons_commande ORDER BY id").fetchall()
        runner(db)
        self.assertEqual(db.execute("SELECT * FROM devis_lignes ORDER BY id").fetchall(), avant_lignes)
        self.assertEqual(db.execute("SELECT * FROM devis_ligne_garanties ORDER BY id").fetchall(), avant_gar)
        self.assertEqual(db.execute("SELECT * FROM bons_commande ORDER BY id").fetchall(), avant_bc)
        self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(db.execute("SELECT count(*) FROM devis_lignes l JOIN devis d ON d.id=l.devis_id").fetchone()[0], 2)
        self.assertEqual(db.execute("SELECT count(*) FROM bons_commande b JOIN devis d ON d.id=b.devis_id JOIN clients c ON c.id=b.client_id").fetchone()[0], 1)

    # --- devis_revisions ---------------------------------------------------------------------
    def test_T45_devis_revisions_structure_exacte(self):
        self.assertEqual(info_colonnes(self.db, "devis_revisions"), INFO_REVISIONS)
        self.assertEqual(self.un("SELECT strict FROM pragma_table_list WHERE name='devis_revisions'")[0], 1)
        self.assertIn("AUTOINCREMENT", sql_de(self.db, "devis_revisions"))
        self.assertEqual(indexes_de(self.db, "devis_revisions"),
                         [("sqlite_autoindex_devis_revisions_1", 1, "u", 0), ("uq_devis_revisions_initiale", 1, "c", 1)])
        self.assertEqual([r[2] for r in self.db.execute("PRAGMA index_info(sqlite_autoindex_devis_revisions_1)")], ["devis_id", "revision"])
        self.assertEqual(sql_de(self.db, "uq_devis_revisions_initiale"),
                         "CREATE UNIQUE INDEX uq_devis_revisions_initiale ON devis_revisions (devis_id) WHERE revision IS NULL")
        self.assertEqual(self.un("SELECT count(*) FROM devis_revisions")[0], 0)

    def test_T45_devis_revisions_contraintes(self):
        """Contraintes seules : les trois triggers TR-100 sont retirés pour que ni leur garde ni leurs messages n'interviennent."""
        for t in ("tr_100_devis_revisions_insert", "tr_100_devis_revisions_no_update", "tr_100_devis_revisions_no_delete"):
            self.db.execute(f"DROP TRIGGER {t}")
        d = self.brouillon()
        d2 = self.brouillon()

        def ins(**mod):
            cols = {"devis_id": d, "revision": 1, "schema_contenu": 1, "contenu": "{}", "total_ht": "10.00", "valide_at": TS}
            cols.update(mod)
            return f"INSERT INTO devis_revisions ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values())
        invalides = [("revision 0", {"revision": 0}), ("revision negative", {"revision": -1}), ("schema_contenu 0", {"schema_contenu": 0}),
                     ("schema_contenu NULL", {"schema_contenu": None}), ("contenu non JSON", {"contenu": "x"}),
                     ("contenu tableau", {"contenu": "[1]"}), ("contenu scalaire", {"contenu": "1"}), ("contenu NULL", {"contenu": None}),
                     ("total sans decimales", {"total_ht": "10"}), ("total negatif", {"total_ht": "-1.00"}), ("total NULL", {"total_ht": None}),
                     ("valide_at date", {"valide_at": "2026-10-01"}), ("valide_at NULL", {"valide_at": None}),
                     ("created_at libre", {"created_at": "hier"}), ("devis_id NULL", {"devis_id": None}),
                     ("devis inconnu", {"devis_id": 9999})]
        for libelle, mod in invalides:
            with self.subTest(invalide=libelle):
                sql, args = ins(**mod)
                self.refuse_check(sql, *args)
        self.db.execute(*ins(revision=None))                                                            # version initiale
        self.refuse_check(*ins(revision=None, valide_at=TS2))                                           # une seule version initiale (index partiel)
        self.db.execute(*ins(revision=None, devis_id=d2))                                               # une par devis
        self.db.execute(*ins(revision=1))
        self.refuse_check(*ins(revision=1, contenu='{"autre": 1}'))                                     # UNIQUE(devis_id, revision)
        self.db.execute(*ins(revision=2))
        self.db.execute(*ins(revision=1, devis_id=d2))
        self.assertEqual(self.un("SELECT count(*) FROM devis_revisions WHERE devis_id=? AND revision IS NULL", d)[0], 1)
        self.assertEqual(self.un("SELECT count(*) FROM devis_revisions WHERE devis_id=? AND revision IS ?", d, None)[0], 1)
        self.assertEqual(self.un("SELECT count(*) FROM devis_revisions WHERE devis_id=? AND revision = NULL", d)[0], 0)   # témoin : « = NULL » ne trouve rien

    def test_T45_devis_revisions_cle_etrangere_en_restrict(self):
        d = self.brouillon()
        self.db.execute("INSERT INTO devis_revisions (devis_id, revision, schema_contenu, contenu, total_ht, valide_at) "
                        "VALUES (?, NULL, 1, '{}', '0.00', ?)", (d, TS))
        self.db.execute("DROP TRIGGER tr_98_devis_no_delete")
        self.refuse_check("DELETE FROM devis WHERE id=?", d)

    def refuse_op(self, sql, *args):
        with self.assertRaises(sqlite3.OperationalError):
            self.db.execute(sql, args)


COLONNES_CLIENTS_ATTENDUES = COLONNES_CLIENTS


def autre_valeur_devis(col, ancienne, autre_client):
    valeurs = {"id": 99999, "numero": "DEV-00099-26", "client_id": autre_client, "client_snapshot": '{"autre": 1}',
               "client_snapshot_version": 7, "entreprise_snapshot": '{"autre": 1}', "entreprise_snapshot_version": 7,
               "chantier_snapshot": '{"autre": 1}', "chantier_snapshot_version": 7, "date_creation": "2026-03-11",
               "date_validite": "2026-06-01", "date_acceptation": "2026-03-20", "date_refus": "2026-03-21", "objet": "Autre objet",
               "notes": "Autres notes", "statut": "en_attente", "revision": 5, "revision_en_cours": 1, "remise_type": "montant",
               "remise_valeur": "7.00", "acompte_type": "pourcentage", "acompte_valeur": "8.00", "total_ht": "999.99",
               "frozen_at": TS2, "cancelled_at": TS2, "motif_refus": "Autre motif", "motif_annulation": "Autre motif",
               "created_at": "2020-01-01T00:00:00.000Z", "updated_at": TS2, "origine": "import", "legacy_id": "autre",
               "legacy_data": '{"autre": 1}'}
    v = valeurs[col]
    return v if v != ancienne else (None if ancienne is not None else "x")


ETATS_DEVIS = ("brouillon", "en_attente", "revision", "accepte", "accepte_gele", "refuse", "annule")
ETATS_DEVIS_MODIFIABLES = ("brouillon", "revision")


class ClientsFournisseurs(Base):
    """TR-97 [INV-183, INV-06] : aucun client ni fournisseur ne se supprime ; code immuable."""

    def test_INV_183_un_client_ne_se_supprime_jamais(self):
        c = self.client()
        self.refuse_inv("INV-183", "DELETE FROM clients WHERE id=?", c)
        for etat in ("en_attente", "accepte"):
            d = self.devis_en_etat(etat)
            cd = self.un("SELECT client_id FROM devis WHERE id=?", d.d)[0]
            self.refuse_inv("INV-183", "DELETE FROM clients WHERE id=?", cd)
        self.refuse_inv("INV-183", "DELETE FROM clients")
        self.assertGreaterEqual(self.un("SELECT count(*) FROM clients")[0], 3)

    def test_INV_183_un_fournisseur_ne_se_supprime_jamais(self):
        f = self.fournisseur()
        self.refuse_inv("INV-183", "DELETE FROM fournisseurs WHERE id=?", f)
        self.refuse_inv("INV-183", "DELETE FROM fournisseurs")
        self.assertEqual(self.un("SELECT count(*) FROM fournisseurs")[0], 1)

    def test_INV_183_le_code_est_immuable(self):
        c, f = self.client(), self.fournisseur()
        self.refuse_inv("INV-183", "UPDATE clients SET code='CLI-0999' WHERE id=?", c)
        self.refuse_inv("INV-183", "UPDATE fournisseurs SET code='FOU-0999' WHERE id=?", f)
        self.refuse_inv("INV-183", "UPDATE clients SET code=NULL WHERE id=?", c)
        self.refuse_inv("INV-183", "UPDATE clients SET code='CLI-0999', nom='Autre' WHERE id=?", c)
        self.refuse_inv("INV-183", "UPDATE fournisseurs SET code='FOU-0999', nom='Autre' WHERE id=?", f)
        # code identique ou autres colonnes : permis
        self.db.execute("UPDATE clients SET code=code, nom='Autre', prenom='P', adresse='A', cpville='V', tel='T', email='E', notes='N', "
                        "updated_at=? WHERE id=?", (TS2, c))
        self.db.execute("UPDATE fournisseurs SET code=code, nom='Autre', adresse='A', cpville='V', tel='T', email='E', notes='N', "
                        "updated_at=? WHERE id=?", (TS2, f))
        self.db.execute("UPDATE clients SET origine='import', legacy_id='L1' WHERE id=?", (c,))
        self.assertEqual(self.un("SELECT nom, origine FROM clients WHERE id=?", c), ("Autre", "import"))

    def test_INV_183_insert_or_replace_ne_contourne_pas_la_garde(self):
        self.client(code="CLI-0500")
        self.fournisseur(code="FOU-0500")
        self.refuse_inv("INV-183", "INSERT OR REPLACE INTO clients (code, nom) VALUES ('CLI-0500', 'Remplaçant')")
        self.refuse_inv("INV-183", "INSERT OR REPLACE INTO fournisseurs (code, nom) VALUES ('FOU-0500', 'Remplaçant')")
        self.assertEqual(self.un("SELECT nom FROM clients WHERE code='CLI-0500'")[0], "Dupont")
        self.assertEqual(self.un("SELECT nom FROM fournisseurs WHERE code='FOU-0500'")[0], "Fournisseur")

    def test_T45_temoin_recursive_triggers_off_le_replace_passerait(self):
        db = migrer(recursive=False)
        db.execute("INSERT INTO clients (code, nom) VALUES ('CLI-0500', 'A')")
        db.execute("INSERT OR REPLACE INTO clients (code, nom) VALUES ('CLI-0500', 'B')")              # D-39 : réglage obligatoire de la connexion
        self.assertEqual(db.execute("SELECT nom FROM clients WHERE code='CLI-0500'").fetchone()[0], "B")
        self.assertEqual(self.un("PRAGMA recursive_triggers")[0], 1)


class DevisNumeroEtGel(Base):
    """TR-01 [INV-23, INV-180] et TR-14 [INV-34] de devis, sur la table reconstruite."""

    def test_INV_180_numero_attribue_a_la_finalisation_puis_immuable(self):
        d = self.brouillon()
        self.assertIsNone(self.un("SELECT numero FROM devis WHERE id=?", d)[0])
        self.snapshot_initial(d)
        self.db.execute("UPDATE devis SET numero='DEV-00001-26', statut='en_attente' WHERE id=?", (d,))   # NULL -> valeur : permis
        self.refuse_inv("INV-23", "UPDATE devis SET numero='DEV-00002-26' WHERE id=?", d)
        self.refuse_inv("INV-23", "UPDATE devis SET numero=NULL WHERE id=?", d)
        self.refuse_inv("INV-23", "UPDATE devis SET numero=NULL, statut='brouillon' WHERE id=?", d)
        self.db.execute("UPDATE devis SET numero=numero, updated_at=? WHERE id=?", (TS2, d))              # valeur identique : permis

    def test_INV_23_numero_immuable_dans_chaque_etat(self):
        for etat in ETATS_DEVIS:
            if etat == "brouillon":
                continue
            with self.subTest(etat=etat):
                dv = self.devis_en_etat(etat)
                self.refuse_inv("INV-23", "UPDATE devis SET numero='DEV-00099-26' WHERE id=?", dv.d)
                self.refuse_inv("INV-23", "UPDATE devis SET numero=NULL WHERE id=?", dv.d)

    def test_INV_23_date_creation_immuable_dans_chaque_etat(self):
        for etat in ETATS_DEVIS:
            with self.subTest(etat=etat):
                dv = self.devis_en_etat(etat)
                self.refuse_inv("INV-23", "UPDATE devis SET date_creation='2026-03-11' WHERE id=?", dv.d)
                self.refuse_inv("INV-23", "UPDATE devis SET date_creation='2027-03-11' WHERE id=?", dv.d)
                self.db.execute("UPDATE devis SET date_creation=date_creation WHERE id=?", (dv.d,))

    def test_INV_20_le_numero_attribue_doit_porter_l_annee_de_date_creation(self):
        """INTERPRETATION arbitrée : l'année du numéro est celle de date_creation (CHECK conservé, conditionné à numero NOT NULL)."""
        d = self.brouillon(date_creation="2026-12-30")
        self.snapshot_initial(d)
        self.refuse_check("UPDATE devis SET numero='DEV-00001-27', statut='en_attente' WHERE id=?", d)
        self.refuse_check("UPDATE devis SET numero='DEV-00001', statut='en_attente' WHERE id=?", d)
        self.refuse_check("UPDATE devis SET numero='', statut='en_attente' WHERE id=?", d)
        self.refuse_check("UPDATE devis SET numero='DEV-00001-26' WHERE id=?", d)                       # numero sans quitter brouillon
        self.refuse_check("UPDATE devis SET statut='en_attente' WHERE id=?", d)                         # statut sans numero
        self.db.execute("UPDATE devis SET numero='DEV-00001-26', statut='en_attente' WHERE id=?", (d,))

    def test_INV_34_frozen_at_ne_revient_jamais_a_null(self):
        dv = self.devis_en_etat("accepte")
        self.db.execute("UPDATE devis SET frozen_at=? WHERE id=?", (TS, dv.d))                           # NULL -> valeur (TR-15)
        self.refuse_inv("INV-34", "UPDATE devis SET frozen_at=NULL WHERE id=?", dv.d)
        self.refuse_inv("INV-34", "UPDATE devis SET frozen_at=? WHERE id=?", TS2, dv.d)
        self.db.execute("UPDATE devis SET frozen_at=frozen_at, updated_at=? WHERE id=?", (TS2, dv.d))
        self.assertEqual(self.un("SELECT frozen_at FROM devis WHERE id=?", dv.d)[0], TS)
        for v in ("2026-10-01", "2026-10-01T10:00:00Z", "now", ""):
            d2 = self.devis_en_etat("accepte")
            self.refuse_check("UPDATE devis SET frozen_at=? WHERE id=?", v, d2.d)

    def test_INV_34_gel_seulement_pour_accepte_ou_annule_check_conserve(self):
        for etat in ("brouillon", "en_attente", "revision", "refuse"):
            with self.subTest(etat=etat):
                dv = self.devis_en_etat(etat)
                self.refuse(f"UPDATE devis SET frozen_at=? WHERE id=?", TS, dv.d)
        dv = self.devis_en_etat("accepte_gele")
        self.refuse("UPDATE devis SET statut='en_attente' WHERE id=?", dv.d)                            # PT-8 conservateur : CHECK frozen_at inchangé
        self.refuse("UPDATE devis SET statut='refuse', date_refus='2026-03-20' WHERE id=?", dv.d)
        self.annuler_devis(dv.d)                                                                        # un devis gelé ne peut qu'être annulé
        self.assertEqual(self.un("SELECT statut, frozen_at FROM devis WHERE id=?", dv.d), ("annule", TS))

    def test_INV_34_tr14_agit_seul_sur_un_devis_annule_gele(self):
        dv = self.devis_en_etat("accepte_gele")
        self.annuler_devis(dv.d)
        self.refuse_inv("INV-34|INV-31", "UPDATE devis SET frozen_at=NULL WHERE id=?", dv.d)


class DevisModifiable(Base):
    """TR-10 réécrit [INV-31, INV-36, INV-180, INV-181, INV-182, INV-196] : liste blanche par état."""

    def test_T45_toutes_les_colonnes_de_devis_ont_une_valeur_de_test(self):
        dv = self.devis_en_etat("accepte")
        ligne = self.un("SELECT * FROM devis WHERE id=?", dv.d)
        for col, ancienne in zip(COLONNES_DEVIS, ligne):
            autre_valeur_devis(col, ancienne, 1)                                                         # KeyError si une colonne est oubliée
        self.assertEqual(sorted(set(CONTENU_DEVIS) - set(COLONNES_DEVIS)), [])

    def test_INV_31_id_et_created_at_immuables_dans_chaque_etat(self):
        for etat in ETATS_DEVIS:
            with self.subTest(etat=etat):
                dv = self.devis_en_etat(etat)
                self.refuse_inv("INV-31", "UPDATE devis SET created_at='2020-01-01T00:00:00.000Z' WHERE id=?", dv.d)
                self.refuse_inv("INV-31", "UPDATE devis SET id=88888 WHERE id=?", dv.d)
                self.refuse_inv("INV-31", "UPDATE devis SET updated_at=?, created_at='2020-01-01T00:00:00.000Z' WHERE id=?", TS2, dv.d)

    def test_INV_180_brouillon_libre_sauf_numero_date_creation_id_created_at(self):
        dv = self.devis_en_etat("brouillon")
        autre = self.client()
        ligne = self.un("SELECT * FROM devis WHERE id=?", dv.d)
        for col, ancienne in zip(COLONNES_DEVIS, ligne):
            if col in ("id", "numero", "date_creation", "created_at", "statut", "revision", "revision_en_cours", "frozen_at",
                       "cancelled_at", "date_refus", "date_acceptation", "motif_refus", "motif_annulation", "origine", "legacy_id", "legacy_data"):
                continue
            with self.subTest(colonne=col):
                self.permis(f"UPDATE devis SET {col}=? WHERE id=?", autre_valeur_devis(col, ancienne, autre), dv.d)
        for m in ("remise_type='montant', remise_valeur='3.00'", "acompte_type='pourcentage', acompte_valeur='30.00'",
                  "date_validite='2026-05-01', objet='x', notes='y', total_ht='40.00', updated_at='%s'" % TS2):
            with self.subTest(modif=m):
                self.permis(f"UPDATE devis SET {m} WHERE id=?", dv.d)

    def test_INV_180_client_id_immuable_apres_la_finalisation(self):
        autre = self.client()
        dv = self.devis_en_etat("brouillon")
        self.permis("UPDATE devis SET client_id=? WHERE id=?", autre, dv.d)                              # brouillon : permis
        self.finaliser(dv.d)
        self.refuse_inv("INV-180", "UPDATE devis SET client_id=? WHERE id=?", autre, dv.d)
        for etat, motif in (("revision", "INV-180"), ("accepte", "INV-180|INV-181"), ("accepte_gele", "INV-180|INV-181"),
                            ("refuse", "INV-180|INV-181"), ("annule", "INV-180|INV-31")):
            with self.subTest(etat=etat):
                d2 = self.devis_en_etat(etat)
                self.refuse_inv(motif, "UPDATE devis SET client_id=? WHERE id=?", autre, d2.d)
        self.refuse_inv("INV-180", "UPDATE devis SET client_id=?, statut='annule', cancelled_at=?, motif_annulation='m' WHERE id=?",
                        autre, TS, self.devis_en_etat("en_attente").d)

    def test_INV_196_en_attente_le_contenu_n_est_modifiable_que_pendant_une_revision(self):
        autre = self.client()
        dv = self.devis_en_etat("en_attente")
        ligne = self.un("SELECT * FROM devis WHERE id=?", dv.d)
        for col, ancienne in zip(COLONNES_DEVIS, ligne):
            if col in CONTENU_DEVIS:
                with self.subTest(colonne=col):
                    self.refuse_inv("INV-196", f"UPDATE devis SET {col}=? WHERE id=?", autre_valeur_devis(col, ancienne, autre), dv.d)
        for m in ("total_ht='40.00', objet='x'", "statut='accepte', date_acceptation='2026-03-12', total_ht='40.00'",
                  "statut='annule', cancelled_at='%s', motif_annulation='m', notes='autre'" % TS):
            with self.subTest(melange=m):
                self.refuse_inv("INV-196", f"UPDATE devis SET {m} WHERE id=?", dv.d)
        self.assertEqual(self.un("SELECT * FROM devis WHERE id=?", dv.d), ligne)                        # rien n'a bougé

    def test_INV_196_en_attente_colonnes_hors_contenu_restent_libres(self):
        dv = self.devis_en_etat("en_attente")
        for m in ("updated_at='%s'" % TS2, "statut='accepte', date_acceptation='2026-03-12'",
                  "statut='refuse', date_refus='2026-03-15', motif_refus='Trop cher'",
                  "statut='annule', cancelled_at='%s', motif_annulation='m'" % TS, "date_acceptation='2026-03-12'",
                  "date_refus='2026-03-15', motif_refus='x'", "revision_en_cours=1"):
            with self.subTest(modif=m):
                self.permis(f"UPDATE devis SET {m} WHERE id=?", dv.d)

    def test_INV_196_pendant_une_revision_le_contenu_est_modifiable(self):
        autre = self.client()
        dv = self.devis_en_etat("revision")
        ligne = self.un("SELECT * FROM devis WHERE id=?", dv.d)
        for col, ancienne in zip(COLONNES_DEVIS, ligne):
            if col in CONTENU_DEVIS:
                with self.subTest(colonne=col):
                    self.permis(f"UPDATE devis SET {col}=? WHERE id=?", autre_valeur_devis(col, ancienne, autre), dv.d)
        self.permis("UPDATE devis SET remise_type='montant', remise_valeur='3.00', total_ht='1.00' WHERE id=?", dv.d)
        self.refuse_inv("INV-180", "UPDATE devis SET client_id=? WHERE id=?", autre, dv.d)             # le client reste immuable
        self.refuse_inv("INV-23", "UPDATE devis SET numero='DEV-00099-26' WHERE id=?", dv.d)

    def test_INV_181_accepte_et_refuse_verrouilles_colonne_par_colonne(self):
        autre = self.client()
        for etat in ("accepte", "accepte_gele", "refuse"):
            dv = self.devis_en_etat(etat)
            ligne = self.un("SELECT * FROM devis WHERE id=?", dv.d)
            for col, ancienne in zip(COLONNES_DEVIS, ligne):
                if col in ("id", "numero", "date_creation", "created_at", "statut", "date_acceptation", "date_refus", "motif_refus",
                           "cancelled_at", "motif_annulation", "frozen_at", "updated_at"):
                    continue
                with self.subTest(etat=etat, colonne=col):
                    self.refuse_inv("INV-18[01]|INV-196", f"UPDATE devis SET {col}=? WHERE id=?", autre_valeur_devis(col, ancienne, autre), dv.d)
            self.assertEqual(self.un("SELECT * FROM devis WHERE id=?", dv.d), ligne)
            for m in ("total_ht='1.00', updated_at='%s'" % TS2, "objet='x', statut=statut", "remise_type='montant', remise_valeur='1.00', total_ht='1.00'"):
                with self.subTest(etat=etat, melange=m):
                    self.refuse_inv("INV-181", f"UPDATE devis SET {m} WHERE id=?", dv.d)

    def test_INV_181_accepte_colonnes_autorisees(self):
        dv = self.devis_en_etat("accepte")
        for m in ("updated_at='%s'" % TS2, "date_acceptation='2026-03-13'", "frozen_at='%s'" % TS,
                  "statut='annule', cancelled_at='%s', motif_annulation='m'" % TS,
                  "statut='refuse', date_refus='2026-03-20', motif_refus='x'", "statut='en_attente'", "motif_refus='x'", "date_refus='2026-03-20'"):
            with self.subTest(modif=m):
                self.permis(f"UPDATE devis SET {m} WHERE id=?", dv.d)
        dv = self.devis_en_etat("accepte_gele")
        for m in ("updated_at='%s'" % TS2, "date_acceptation='2026-03-13'", "statut='annule', cancelled_at='%s', motif_annulation='m'" % TS):
            with self.subTest(gele=m):
                self.permis(f"UPDATE devis SET {m} WHERE id=?", dv.d)

    def test_INV_182_refuse_verrouille_mais_rouvrable_en_attente(self):
        dv = self.devis_en_etat("refuse")
        self.refuse_inv("INV-182", "UPDATE devis SET statut='accepte', date_acceptation='2026-03-12' WHERE id=?", dv.d)
        self.refuse_inv("INV-182", "UPDATE devis SET statut='annule', cancelled_at=?, motif_annulation='m' WHERE id=?", TS, dv.d)
        self.refuse_inv("INV-182", "UPDATE devis SET statut='brouillon' WHERE id=?", dv.d)
        self.permis("UPDATE devis SET updated_at=? WHERE id=?", TS2, dv.d)
        self.permis("UPDATE devis SET date_refus='2026-03-18', motif_refus='Autre' WHERE id=?", dv.d)
        self.db.execute("UPDATE devis SET statut='en_attente' WHERE id=?", (dv.d,))                       # réouverture
        self.assertEqual(self.un("SELECT numero IS NOT NULL, revision, revision_en_cours, total_ht FROM devis WHERE id=?", dv.d),
                         (1, None, 0, "31.50"))                                                         # numéro et contenu inchangés
        self.assertEqual(self.un("SELECT count(*) FROM devis_lignes WHERE devis_id=?", dv.d)[0], 2)

    def test_INV_182_INTERPRETATION_date_refus_et_motif_refus_conserves_a_la_reouverture(self):
        """PT-17 laissé ouvert : la migration ne touche ni date_refus ni motif_refus à la réouverture (CHECK refuse => date_refus inchangé)."""
        dv = self.devis_en_etat("refuse")
        self.db.execute("UPDATE devis SET statut='en_attente' WHERE id=?", (dv.d,))
        self.assertEqual(self.un("SELECT date_refus, motif_refus FROM devis WHERE id=?", dv.d), ("2026-03-15", "Trop cher"))
        self.db.execute("UPDATE devis SET statut='refuse' WHERE id=?", (dv.d,))                           # nouveau refus : le CHECK est satisfait
        self.assertEqual(self.un("SELECT statut FROM devis WHERE id=?", dv.d)[0], "refuse")

    def test_INV_182_refuse_n_est_jamais_un_devis_sans_date_refus(self):
        dv = self.devis_en_etat("en_attente")
        self.refuse_check("UPDATE devis SET statut='refuse' WHERE id=?", dv.d)

    def test_INV_31_annule_terminal_colonne_par_colonne(self):
        autre = self.client()
        dv = self.devis_en_etat("annule")
        ligne = self.un("SELECT * FROM devis WHERE id=?", dv.d)
        for col, ancienne in zip(COLONNES_DEVIS, ligne):
            if col in ("updated_at",):
                continue
            with self.subTest(colonne=col):
                regex = "INV-23" if col in ("numero", "date_creation") else "INV-31|INV-180|INV-196"
                self.refuse_inv(regex, f"UPDATE devis SET {col}=? WHERE id=?", autre_valeur_devis(col, ancienne, autre), dv.d)
        self.assertEqual(self.un("SELECT * FROM devis WHERE id=?", dv.d), ligne)
        self.db.execute("UPDATE devis SET updated_at=? WHERE id=?", (TS2, dv.d))                          # seule colonne libre
        for m in ("statut='en_attente', cancelled_at=NULL, motif_annulation=NULL", "statut='accepte', date_acceptation='2026-03-12', "
                  "cancelled_at=NULL, motif_annulation=NULL", "cancelled_at=NULL"):
            with self.subTest(reouverture=m):
                self.refuse_inv("INV-31", f"UPDATE devis SET {m} WHERE id=?", dv.d)

    def test_INV_31_annule_gele_reste_terminal(self):
        dv = self.devis_en_etat("accepte_gele")
        self.annuler_devis(dv.d)
        self.refuse_inv("INV-31", "UPDATE devis SET total_ht='1.00' WHERE id=?", dv.d)
        self.refuse_inv("INV-31|INV-34", "UPDATE devis SET frozen_at=NULL WHERE id=?", dv.d)
        self.refuse_inv("INV-31", "UPDATE devis SET motif_annulation='autre' WHERE id=?", dv.d)

    def test_T45_le_rattachement_d_un_client_a_rattacher_n_existe_plus(self):
        """003 autorisait de changer client_id d'un devis refusé/annulé/gelé dont le client était 'a_rattacher' (INV-49) : supprimé (INV-183)."""
        autre = self.client()
        for etat in ("accepte", "accepte_gele", "refuse", "annule", "en_attente", "revision"):
            with self.subTest(etat=etat):
                dv = self.devis_en_etat(etat)
                self.refuse_inv("INV-18[01]|INV-31", "UPDATE devis SET client_id=?, updated_at=? WHERE id=?", autre, TS2, dv.d)
        for tr in ("tr_10_devis_gele", "tr_10_devis_refuse_annule"):
            self.assertEqual(self.un("SELECT count(*) FROM sqlite_master WHERE name=?", tr)[0], 0)

    def test_INV_196_acceptation_refusee_pendant_une_revision(self):
        dv = self.devis_en_etat("revision")
        self.refuse_inv("INV-196", "UPDATE devis SET statut='accepte', date_acceptation='2026-03-12' WHERE id=?", dv.d)
        self.refuse_inv("INV-196", "UPDATE devis SET revision_en_cours=0, statut='accepte', date_acceptation='2026-03-12', revision=1 WHERE id=?", dv.d)
        self.db.execute("UPDATE devis SET revision_en_cours=0 WHERE id=?", (dv.d,))                       # abandon
        self.accepter(dv.d)

    def test_INV_196_finalisation_exige_le_snapshot_de_la_version_initiale(self):
        d = self.brouillon()
        for cible in ("en_attente", "accepte"):
            with self.subTest(cible=cible):
                extra = ", date_acceptation='2026-03-12'" if cible == "accepte" else ""
                self.refuse_inv("INV-196", f"UPDATE devis SET numero='DEV-00001-26', statut='{cible}'{extra} WHERE id=?", d)
        self.refuse_inv("INV-196", "UPDATE devis SET numero='DEV-00001-26', statut='refuse', date_refus='2026-03-15' WHERE id=?", d)
        self.permis("UPDATE devis SET total_ht='5.00' WHERE id=?", d)                                      # rester brouillon est libre
        self.snapshot_initial(d)
        self.db.execute("UPDATE devis SET numero='DEV-00001-26', statut='en_attente' WHERE id=?", (d,))

    def test_INV_196_le_snapshot_d_un_autre_devis_ne_suffit_pas(self):
        d1, d2 = self.brouillon(), self.brouillon()
        self.snapshot_initial(d2)
        self.refuse_inv("INV-196", "UPDATE devis SET numero='DEV-00001-26', statut='en_attente' WHERE id=?", d1)

    def test_INV_196_une_revision_numerotee_ne_vaut_pas_version_initiale(self):
        self.db.execute("DROP TRIGGER tr_100_devis_revisions_insert")
        d2 = self.brouillon()
        self.db.execute("INSERT INTO devis_revisions (devis_id, revision, schema_contenu, contenu, total_ht, valide_at) "
                        "VALUES (?, 1, 1, '{}', '0.00', ?)", (d2, TS))
        self.refuse_inv("INV-196", "UPDATE devis SET numero='DEV-00001-26', statut='en_attente' WHERE id=?", d2)


class RevisionsDevis(Base):
    """TR-10 (transitions de revision / revision_en_cours) et TR-100 [INV-196] : append-only, numérotation consécutive."""

    def valider_revision(self, d):
        n = self.un("SELECT COALESCE(MAX(revision), 0) + 1 FROM devis_revisions WHERE devis_id=?", d)[0]
        self.db.execute("INSERT INTO devis_revisions (devis_id, revision, schema_contenu, contenu, total_ht, valide_at) "
                        "VALUES (?, ?, 1, '{}', (SELECT total_ht FROM devis WHERE id=?), ?)", (d, n, d, TS))
        self.db.execute("UPDATE devis SET revision=?, revision_en_cours=0 WHERE id=?", (n, d))
        return n

    def insere(self, d, revision, **kw):
        cols = {"devis_id": d, "revision": revision, "schema_contenu": 1, "contenu": "{}", "total_ht": "1.00", "valide_at": TS}
        cols.update(kw)
        return f"INSERT INTO devis_revisions ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values())

    def test_INV_196_cycle_complet_de_revision(self):
        dv = self.devis_en_etat("en_attente")
        self.assertEqual(self.un("SELECT revision, revision_en_cours FROM devis WHERE id=?", dv.d), (None, 0))
        self.refuse_inv("INV-196", "UPDATE devis SET total_ht='40.00' WHERE id=?", dv.d)
        for attendu in (1, 2):
            self.db.execute("UPDATE devis SET revision_en_cours=1 WHERE id=?", (dv.d,))                  # démarrage
            self.db.execute("UPDATE devis SET total_ht=?, objet='révisé' WHERE id=?", (f"{40 + attendu}.00", dv.d))
            self.db.execute("UPDATE devis_lignes SET designation='révisée' WHERE id=?", (dv.l2,))
            self.assertEqual(self.valider_revision(dv.d), attendu)
            self.assertEqual(self.un("SELECT revision, revision_en_cours FROM devis WHERE id=?", dv.d), (attendu, 0))
            self.refuse_inv("INV-196", "UPDATE devis SET total_ht='99.00' WHERE id=?", dv.d)             # contenu de nouveau verrouillé
            self.refuse_inv("INV-36", "UPDATE devis_lignes SET designation='x' WHERE id=?", dv.l2)
        self.assertEqual(self.tous("SELECT revision FROM devis_revisions WHERE devis_id=? ORDER BY id", dv.d), [(None,), (1,), (2,)])
        # abandon : revision inchangé
        self.db.execute("UPDATE devis SET revision_en_cours=1 WHERE id=?", (dv.d,))
        self.db.execute("UPDATE devis SET revision_en_cours=0 WHERE id=?", (dv.d,))
        self.assertEqual(self.un("SELECT revision, revision_en_cours FROM devis WHERE id=?", dv.d), (2, 0))
        self.accepter(dv.d)

    def test_INV_196_transitions_de_revision_refusees(self):
        dv = self.devis_en_etat("en_attente")
        self.refuse_inv("INV-196", "UPDATE devis SET revision=1 WHERE id=?", dv.d)                       # revision sans phase de révision
        self.refuse_inv("INV-196", "UPDATE devis SET revision=1, revision_en_cours=1 WHERE id=?", dv.d)  # démarrage + numéro
        self.db.execute("UPDATE devis SET revision_en_cours=1 WHERE id=?", (dv.d,))
        self.refuse_inv("INV-196", "UPDATE devis SET revision=1 WHERE id=?", dv.d)                       # numéro sans fin de phase
        self.refuse_inv("INV-196", "UPDATE devis SET revision=1, revision_en_cours=0 WHERE id=?", dv.d)  # sans snapshot de ce numéro
        self.db.execute(*self.insere(dv.d, 1))
        self.refuse_inv("INV-196", "UPDATE devis SET revision=2, revision_en_cours=0 WHERE id=?", dv.d)  # saute un numéro
        self.refuse_inv("INV-196", "UPDATE devis SET revision=1, revision_en_cours=1, total_ht='2.00' WHERE id=?", dv.d)
        self.db.execute("UPDATE devis SET revision=1, revision_en_cours=0 WHERE id=?", (dv.d,))          # la bonne transition passe
        self.db.execute("UPDATE devis SET revision_en_cours=1 WHERE id=?", (dv.d,))
        self.refuse_inv("INV-196", "UPDATE devis SET revision=NULL, revision_en_cours=0 WHERE id=?", dv.d)
        self.db.execute(*self.insere(dv.d, 2))
        self.refuse_inv("INV-196", "UPDATE devis SET revision=0, revision_en_cours=0 WHERE id=?", dv.d)  # recule
        self.refuse_inv("INV-196", "UPDATE devis SET revision=3, revision_en_cours=0 WHERE id=?", dv.d)
        self.db.execute("UPDATE devis SET revision=2, revision_en_cours=0 WHERE id=?", (dv.d,))
        self.assertEqual(self.un("SELECT revision FROM devis WHERE id=?", dv.d)[0], 2)

    def test_INV_196_le_snapshot_d_une_autre_revision_ou_d_un_autre_devis_ne_valide_pas(self):
        dv, autre = self.devis_en_etat("revision"), self.devis_en_etat("revision")
        self.db.execute(*self.insere(autre.d, 1))
        self.refuse_inv("INV-196", "UPDATE devis SET revision=1, revision_en_cours=0 WHERE id=?", dv.d)

    def test_INV_196_la_revision_ne_demarre_que_pour_un_devis_en_attente(self):
        self.refuse_check("UPDATE devis SET revision_en_cours=1 WHERE id=?", self.devis_en_etat("brouillon").d)     # CHECK conservé
        for etat in ("accepte", "accepte_gele", "refuse", "annule"):
            with self.subTest(etat=etat):
                self.refuse_inv("INV-181|INV-31|INV-196", "UPDATE devis SET revision_en_cours=1 WHERE id=?", self.devis_en_etat(etat).d)

    def test_INV_196_tr100_append_only(self):
        dv = self.devis_en_etat("revision")
        self.valider_revision(dv.d)
        for i in self.tous("SELECT id FROM devis_revisions WHERE devis_id=?", dv.d):
            self.refuse_inv("INV-196", "UPDATE devis_revisions SET contenu='{}' WHERE id=?", i[0])
            self.refuse_inv("INV-196", "UPDATE devis_revisions SET created_at=created_at WHERE id=?", i[0])
            self.refuse_inv("INV-196", "DELETE FROM devis_revisions WHERE id=?", i[0])
        self.refuse_inv("INV-196", "DELETE FROM devis_revisions")
        self.assertEqual(self.un("SELECT count(*) FROM devis_revisions WHERE devis_id=?", dv.d)[0], 2)
        self.refuse_inv("INV-196", "INSERT OR REPLACE INTO devis_revisions (id, devis_id, revision, schema_contenu, contenu, total_ht, valide_at) "
                        "VALUES (1, ?, 5, 1, '{}', '1.00', ?)", dv.d, TS)

    def test_INV_196_tr100_version_initiale_une_seule_fois(self):
        d = self.brouillon()
        self.db.execute(*self.insere(d, None))
        self.refuse_check(*self.insere(d, None))                                                         # index unique partiel
        self.db.execute(*self.insere(self.brouillon(), None))                                            # une par devis
        self.assertEqual(self.un("SELECT count(*) FROM devis_revisions WHERE revision IS NULL")[0], 2)

    def test_INV_196_INTERPRETATION_la_version_initiale_n_est_pas_soumise_a_l_etat_du_devis(self):
        """TR-100 : seule une révision numérotée exige un devis en_attente en phase de révision ; le snapshot initial s'écrit avant la
        sortie de brouillon (TR-10 finalisation), donc quand le devis est encore brouillon ; l'index unique partiel garde l'unicité."""
        for etat in ("brouillon", "en_attente", "accepte", "refuse", "annule"):
            with self.subTest(etat=etat):
                self.permis(*self.insere(self.devis_direct(etat), None))

    def test_INV_196_tr100_revision_numerotee_exige_une_phase_de_revision(self):
        for etat in ("brouillon", "en_attente", "accepte", "accepte_gele", "refuse", "annule"):
            with self.subTest(etat=etat):
                dv = self.devis_en_etat(etat)
                self.refuse_inv("INV-196", *self.insere(dv.d, 1))
        dv = self.devis_en_etat("revision")
        self.permis(*self.insere(dv.d, 1))

    def test_INV_196_tr100_numerotation_consecutive_sans_trou_ni_doublon(self):
        dv = self.devis_en_etat("revision")
        self.refuse_inv("INV-196", *self.insere(dv.d, 2))                                                # premier numéro = 1
        self.refuse_inv("INV-196", *self.insere(dv.d, 3))
        self.db.execute(*self.insere(dv.d, 1))
        self.refuse_inv("INV-196", *self.insere(dv.d, 1))                                                # doublon
        self.refuse_inv("INV-196", *self.insere(dv.d, 3))                                                # trou
        self.refuse_inv("INV-196", *self.insere(dv.d, 0))                                                # jamais 0
        self.db.execute(*self.insere(dv.d, 2))
        self.db.execute(*self.insere(dv.d, 3))
        self.refuse_inv("INV-196", *self.insere(dv.d, 5))
        # chaque devis a sa propre numérotation
        d2 = self.devis_en_etat("revision")
        self.db.execute(*self.insere(d2.d, 1))
        # la version initiale (NULL) ne compte pas dans le maximum
        self.assertEqual(self.un("SELECT COALESCE(MAX(revision), 0) FROM devis_revisions WHERE devis_id=?", d2.d)[0], 1)

    def test_INV_196_tr100_devis_inexistant_refuse_par_la_cle_etrangere(self):
        self.refuse_check(*self.insere(9999, None))
        self.refuse_check(*self.insere(9999, 1))


class SuppressionDevis(Base):
    """TR-98 [INV-180, INV-06] (PT-5) : seul un devis brouillon se supprime ; la cascade des lignes ne joue que pour un brouillon."""

    def test_INV_180_un_devis_non_brouillon_ne_se_supprime_pas(self):
        for etat in ("en_attente", "revision", "accepte", "accepte_gele", "refuse", "annule"):
            with self.subTest(etat=etat):
                dv = self.devis_en_etat(etat)
                self.refuse_inv("INV-180", "DELETE FROM devis WHERE id=?", dv.d)
                self.assertEqual(self.un("SELECT count(*) FROM devis_lignes WHERE devis_id=?", dv.d)[0], 2)
                self.assertEqual(self.un("SELECT count(*) FROM devis_ligne_garanties WHERE ligne_id=?", dv.l1)[0], 2)

    def test_INV_180_un_brouillon_se_supprime_avec_ses_lignes_et_garanties(self):
        dv = self.devis_en_etat("brouillon")
        autre = self.devis_en_etat("brouillon")
        self.db.execute("DELETE FROM devis WHERE id=?", (dv.d,))
        self.assertEqual(self.un("SELECT count(*) FROM devis WHERE id=?", dv.d)[0], 0)
        self.assertEqual(self.un("SELECT count(*) FROM devis_lignes WHERE devis_id=?", dv.d)[0], 0)
        self.assertEqual(self.un("SELECT count(*) FROM devis_ligne_garanties WHERE ligne_id IN (?, ?)", dv.l1, dv.l2)[0], 0)
        self.assertEqual(self.un("SELECT count(*) FROM devis_lignes WHERE devis_id=?", autre.d)[0], 2)  # les autres sont intacts
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_INV_180_une_suppression_en_lot_est_refusee_en_entier(self):
        b, a = self.devis_en_etat("brouillon"), self.devis_en_etat("accepte")
        n = self.un("SELECT count(*) FROM devis")[0]
        self.refuse_inv("INV-180", "DELETE FROM devis")
        self.assertEqual(self.un("SELECT count(*) FROM devis")[0], n)
        self.assertEqual(self.un("SELECT count(*) FROM devis WHERE id=?", b.d)[0], 1)

    def test_INV_180_insert_or_replace_ne_contourne_pas_la_garde(self):
        dv = self.devis_en_etat("accepte")
        numero = self.un("SELECT numero FROM devis WHERE id=?", dv.d)[0]
        self.refuse_inv("INV-180", "INSERT OR REPLACE INTO devis (numero, client_id, client_snapshot, client_snapshot_version, "
                        "entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, "
                        "statut, total_ht) VALUES (?, 1, '{}', 1, '{}', 1, '{}', 1, '2026-03-10', 'en_attente', '0.00')", numero)
        self.assertEqual(self.un("SELECT statut FROM devis WHERE numero=?", numero)[0], "accepte")
        self.assertEqual(self.un("SELECT count(*) FROM devis_lignes WHERE devis_id=?", dv.d)[0], 2)

    def test_INV_175_un_devis_avec_bon_de_commande_ne_se_supprime_jamais(self):
        bc = self.bc_en_etat("annule")
        self.refuse_inv("INV-180", "DELETE FROM devis WHERE id=?", bc.d)
        self.db.execute("DROP TRIGGER tr_98_devis_no_delete")
        self.refuse_check("DELETE FROM devis WHERE id=?", bc.d)                                         # la FK RESTRICT de 004 reste la dernière garde


class LignesDevis(Base):
    """TR-11 réécrit [INV-36, INV-180, INV-181, INV-196] : lignes et garanties modifiables seulement en brouillon ou pendant une révision."""

    def operations(self, dv, numero=3):
        return {"insert ligne": ("INSERT INTO devis_lignes (devis_id, ordre, designation, quantite, unite, prix_unitaire_ht, remise_type, "
                                 "type_prestation, total_ht) VALUES (?, ?, 'N', '1', 'u', '1.5', 'aucune', 'pose', '1.50')", (dv.d, numero)),
                "update ligne": ("UPDATE devis_lignes SET designation='x' WHERE id=?", (dv.l2,)),
                "delete ligne": ("DELETE FROM devis_lignes WHERE id=?", (dv.l2,)),
                "insert garantie": ("INSERT INTO devis_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'parfait_achevement')", (dv.l1,)),
                "update garantie": ("UPDATE devis_ligne_garanties SET garantie_type='parfait_achevement' WHERE id=?", (dv.g1,)),
                "delete garantie": ("DELETE FROM devis_ligne_garanties WHERE id=?", (dv.g1,))}

    def test_INV_36_matrice_etat_du_devis_x_operation(self):
        for etat in ETATS_DEVIS:
            dv = self.devis_en_etat(etat)
            for nom, (sql, args) in self.operations(dv).items():
                with self.subTest(etat=etat, operation=nom):
                    if etat in ETATS_DEVIS_MODIFIABLES:
                        self.permis(sql, *args)
                    else:
                        self.refuse_inv("INV-36", sql, *args)

    def test_INV_181_un_devis_accepte_non_gele_n_a_plus_de_lignes_modifiables(self):
        """003 : lignes modifiables en 'en_attente' et en 'accepte' non gelé. V3.13 : brouillon et révision seulement."""
        dv = self.devis_en_etat("accepte")
        self.assertIsNone(self.un("SELECT frozen_at FROM devis WHERE id=?", dv.d)[0])
        for nom, (sql, args) in self.operations(dv).items():
            with self.subTest(operation=nom):
                self.refuse_inv("INV-36", sql, *args)
        dv = self.devis_en_etat("en_attente")
        for nom, (sql, args) in self.operations(dv).items():
            with self.subTest(en_attente=nom):
                self.refuse_inv("INV-36", sql, *args)

    def test_INV_36_deplacer_une_ligne_ou_une_garantie_vers_ou_depuis_un_devis_non_modifiable(self):
        libre, fige = self.devis_en_etat("brouillon"), self.devis_en_etat("accepte")
        self.refuse_inv("INV-36", "UPDATE devis_lignes SET devis_id=?, ordre=9 WHERE id=?", fige.d, libre.l2)
        self.refuse_inv("INV-36", "UPDATE devis_lignes SET devis_id=?, ordre=9 WHERE id=?", libre.d, fige.l2)
        self.refuse_inv("INV-36", "UPDATE devis_ligne_garanties SET ligne_id=? WHERE id=?", fige.l2, libre.g1)
        self.refuse_inv("INV-36", "UPDATE devis_ligne_garanties SET ligne_id=? WHERE id=?", libre.l2, fige.g1)
        self.permis("UPDATE devis_lignes SET devis_id=?, ordre=9 WHERE id=?", self.devis_en_etat("revision").d, libre.l2)
        self.permis("UPDATE devis_ligne_garanties SET ligne_id=? WHERE id=?", libre.l2, libre.g1)

    def test_INV_36_parent_inexistant_refuse_par_la_cle_etrangere_et_non_par_le_trigger(self):
        self.refuse_check("INSERT INTO devis_lignes (devis_id, ordre, designation, quantite, unite, prix_unitaire_ht, remise_type, "
                          "type_prestation, total_ht) VALUES (9999, 1, 'N', '1', 'u', '1.5', 'aucune', 'pose', '1.50')")
        self.refuse_check("INSERT INTO devis_ligne_garanties (ligne_id, garantie_type) VALUES (9999, 'decennale')")

    def test_INV_36_la_revision_ouvre_puis_referme_les_lignes(self):
        dv = self.devis_en_etat("en_attente")
        self.refuse_inv("INV-36", *self.operations(dv)["update ligne"])
        self.db.execute("UPDATE devis SET revision_en_cours=1 WHERE id=?", (dv.d,))
        for nom, (sql, args) in self.operations(dv).items():
            with self.subTest(pendant=nom):
                self.permis(sql, *args)
        self.db.execute("UPDATE devis SET revision_en_cours=0 WHERE id=?", (dv.d,))
        self.refuse_inv("INV-36", *self.operations(dv)["update ligne"])


def autre_valeur_bc(col, ancienne, autre_client):
    valeurs = {"id": 99999, "numero": "BCD-00099-26", "devis_id": 99998, "client_id": autre_client,
               "client_snapshot": '{"autre": 1}', "client_snapshot_version": 7, "entreprise_snapshot": '{"autre": 1}',
               "entreprise_snapshot_version": 7, "chantier_snapshot": '{"autre": 1}', "chantier_snapshot_version": 7,
               "date_creation": "2026-10-03", "date_acceptation": "2026-03-20", "date_debut": "2026-11-01",
               "date_fin": "2026-11-30", "montant_contractuel_ht": "999.99", "remise_type": "montant",
               "remise_valeur": "7.00", "acompte_type": "montant", "acompte_valeur": "8.00",
               "montant_deja_facture_ht": "12.00", "avancement": "12.00", "date_100_facture": "2026-10-03",
               "statut": "termine", "completed_at": TS2, "cancelled_at": TS2, "motif_annulation": "Autre motif",
               "frozen_at": TS2, "created_at": "2026-01-01T00:00:00.000Z", "updated_at": TS2, "origine": "import",
               "legacy_id": "autre", "legacy_data": '{"autre": 1}', "legacy_numero": "AUTRE-1"}
    v = valeurs[col]
    return v if v != ancienne else (None if ancienne is not None else "x")


# 004 (liste blanche du modèle §7.2) moins le rattachement d'un client 'a_rattacher' (INV-183) : client_id n'est plus modifiable
COLONNES_GELE_MODIFIABLES = {"montant_deja_facture_ht", "avancement", "date_100_facture", "statut", "completed_at", "date_debut",
                             "date_fin", "cancelled_at", "motif_annulation", "updated_at"}
COLONNES_ANNULE_MODIFIABLES = {"updated_at"}
ETATS_BC = ("en_cours", "gele", "termine", "annule", "annule_gele")
ETATS_BC_FIGES = ("gele", "termine", "annule", "annule_gele")


class TriggersBC(Base):
    """Comportement réel des triggers 004 sur la chaîne 001 → 005 → 005a (G-1, G-2, G-3) : tr_01, tr_12 x3, tr_13 x6, tr_14, tr_17,
    tr_18, tr_19 et tr_96."""

    def test_T45_toutes_les_colonnes_de_bons_commande_ont_une_valeur_de_test(self):
        self.assertEqual(colonnes(self.db, "bons_commande"), COLONNES_BC)
        bc = self.bc_en_etat("gele")
        for col, ancienne in zip(COLONNES_BC, self.un("SELECT * FROM bons_commande WHERE id=?", bc.b)):
            autre_valeur_bc(col, ancienne, 1)

    def test_INV_23_numero_et_date_creation_du_bc_immuables_dans_chaque_etat(self):
        for etat in ETATS_BC:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                self.refuse_inv("INV-23", "UPDATE bons_commande SET numero='BCD-00099-26' WHERE id=?", bc.b)
                self.refuse_inv("INV-23", "UPDATE bons_commande SET date_creation='2026-10-03' WHERE id=?", bc.b)
                self.refuse_inv("INV-23", "UPDATE bons_commande SET numero=NULL WHERE id=?", bc.b)

    def test_INV_36_bc_en_cours_modifiable_sauf_id_devis_id_created_at(self):
        autre = self.client()
        bc = self.bc_en_etat("en_cours")
        ligne = self.un("SELECT * FROM bons_commande WHERE id=?", bc.b)
        for col, ancienne in zip(COLONNES_BC, ligne):
            if col in ("id", "devis_id", "created_at"):
                with self.subTest(colonne=col):
                    self.refuse_inv("INV-36", f"UPDATE bons_commande SET {col}=? WHERE id=?", autre_valeur_bc(col, ancienne, autre), bc.b)
        for m in ("client_snapshot='{\"a\": 1}'", "client_snapshot_version=7", "chantier_snapshot='{\"a\": 1}'", "date_acceptation='2026-04-01'",
                  "date_debut='2026-11-01'", "date_fin='2026-11-30'", "montant_contractuel_ht='99.00'", "remise_type='montant', remise_valeur='3.00'",
                  "montant_deja_facture_ht='10.00'", "avancement='10.00'", "updated_at='%s'" % TS2, "origine='import'", "frozen_at='%s'" % TS,
                  "client_id=%d" % autre):
            with self.subTest(modif=m):
                self.permis(f"UPDATE bons_commande SET {m} WHERE id=?", bc.b)

    def test_INV_36_bc_gele_ou_termine_liste_blanche_colonne_par_colonne(self):
        autre = self.client()
        for etat in ("gele", "termine"):
            bc = self.bc_en_etat(etat)
            ligne = self.un("SELECT * FROM bons_commande WHERE id=?", bc.b)
            for col, ancienne in zip(COLONNES_BC, ligne):
                if col in COLONNES_GELE_MODIFIABLES:
                    continue
                with self.subTest(etat=etat, colonne=col):
                    self.refuse_inv("INV-23|INV-34|INV-36", f"UPDATE bons_commande SET {col}=? WHERE id=?",
                                    autre_valeur_bc(col, ancienne, autre), bc.b)
            self.assertEqual(self.un("SELECT * FROM bons_commande WHERE id=?", bc.b), ligne)
            for m in ("montant_contractuel_ht='1.00', avancement='20.00'", "avancement='20.00', remise_valeur='1.00'",
                      "date_debut='2026-11-01', numero='BCD-00099-26'", "date_fin='2026-11-02', origine='import'",
                      "avancement='20.00', client_id=%d" % autre):
                with self.subTest(etat=etat, melange=m):
                    self.refuse(f"UPDATE bons_commande SET {m} WHERE id=?", bc.b)

    def test_INV_36_bc_gele_colonnes_autorisees(self):
        bc = self.bc_en_etat("gele")
        for m in ("montant_deja_facture_ht='10.00'", "avancement='50.00'", "date_100_facture='2026-10-02', avancement='100.00'",
                  "date_debut='2026-11-01'", "date_fin='2026-11-30'", "updated_at='%s'" % TS2,
                  "statut='termine', completed_at='%s', date_100_facture='2026-10-02', avancement='100.00'" % TS,
                  "statut='annule', cancelled_at='%s', motif_annulation='Client renonce'" % TS):
            with self.subTest(modif=m):
                self.permis(f"UPDATE bons_commande SET {m} WHERE id=?", bc.b)
        self.terminer_bc(bc.b)
        self.db.execute("UPDATE bons_commande SET statut='en_cours', completed_at=NULL, date_100_facture=NULL, avancement='60.00', "
                        "montant_deja_facture_ht='18.90' WHERE id=?", (bc.b,))
        self.annuler_bc(bc.b)
        self.assertEqual(self.un("SELECT statut, frozen_at IS NOT NULL, cancelled_at IS NOT NULL FROM bons_commande WHERE id=?", bc.b), ("annule", 1, 1))

    def test_INV_173_bc_annule_terminal_colonne_par_colonne(self):
        autre = self.client()
        for etat in ("annule", "annule_gele"):
            bc = self.bc_en_etat(etat)
            ligne = self.un("SELECT * FROM bons_commande WHERE id=?", bc.b)
            for col, ancienne in zip(COLONNES_BC, ligne):
                if col in COLONNES_ANNULE_MODIFIABLES:
                    continue
                with self.subTest(etat=etat, colonne=col):
                    self.refuse_inv("INV-23|INV-34|INV-173", f"UPDATE bons_commande SET {col}=? WHERE id=?",
                                    autre_valeur_bc(col, ancienne, autre), bc.b)
            self.assertEqual(self.un("SELECT * FROM bons_commande WHERE id=?", bc.b), ligne)
            self.db.execute("UPDATE bons_commande SET updated_at=? WHERE id=?", (TS2, bc.b))
            for m in ("statut='en_cours', cancelled_at=NULL, motif_annulation=NULL", "cancelled_at=NULL", "motif_annulation='Autre'",
                      "date_debut='2026-11-01'", "montant_deja_facture_ht='1.00'"):
                with self.subTest(etat=etat, reouverture=m):
                    self.refuse_inv("INV-173", f"UPDATE bons_commande SET {m} WHERE id=?", bc.b)

    def test_INV_173_le_rattachement_d_un_client_a_rattacher_n_existe_plus(self):
        autre = self.client()
        for etat in ETATS_BC_FIGES:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                self.refuse_inv("INV-36|INV-173", "UPDATE bons_commande SET client_id=?, updated_at=? WHERE id=?", autre, TS2, bc.b)

    def test_INV_34_frozen_at_du_bc_ne_revient_jamais_a_null(self):
        bc = self.bc_en_etat("en_cours")
        self.db.execute("UPDATE bons_commande SET frozen_at=? WHERE id=?", (TS, bc.b))
        self.refuse_inv("INV-34", "UPDATE bons_commande SET frozen_at=NULL WHERE id=?", bc.b)
        self.refuse_inv("INV-34", "UPDATE bons_commande SET frozen_at=? WHERE id=?", TS2, bc.b)
        self.db.execute("UPDATE bons_commande SET frozen_at=frozen_at, updated_at=? WHERE id=?", (TS2, bc.b))
        bc2 = self.bc_en_etat("annule")
        self.refuse_inv("INV-173", "UPDATE bons_commande SET frozen_at=? WHERE id=?", TS2, bc2.b)         # un BC annulé ne se gèle pas

    def test_INV_40_un_bc_nait_d_un_devis_accepte(self):
        d = self.devis_en_etat("en_attente")
        self.refuse_inv("INV-40", "INSERT INTO bons_commande (numero, devis_id, client_id, client_snapshot, client_snapshot_version, "
                        "entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, "
                        "date_acceptation, montant_contractuel_ht) SELECT 'BCD-00001-26', id, client_id, client_snapshot, 1, entreprise_snapshot, 1, "
                        "chantier_snapshot, 1, '2026-10-02', '2026-03-12', total_ht FROM devis WHERE id=?", d.d)
        for etat in ("brouillon", "revision", "refuse", "annule"):
            with self.subTest(etat=etat):
                dv = self.devis_en_etat(etat)
                self.refuse_inv("INV-40", "INSERT INTO bons_commande (numero, devis_id, client_id, client_snapshot, client_snapshot_version, "
                                "entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, "
                                "date_acceptation, montant_contractuel_ht) SELECT 'BCD-00002-26', id, client_id, client_snapshot, 1, entreprise_snapshot, 1, "
                                "chantier_snapshot, 1, '2026-10-02', '2026-03-12', total_ht FROM devis WHERE id=?", dv.d)
        self.creer_bc(self.devis_accepte(), lignes=True)

    def test_INV_48_le_client_du_bc_est_celui_du_devis(self):
        d = self.devis_accepte()
        self.refuse_inv("INV-48", "INSERT INTO bons_commande (numero, devis_id, client_id, client_snapshot, client_snapshot_version, "
                        "entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, "
                        "date_acceptation, montant_contractuel_ht) SELECT 'BCD-00001-26', id, ?, client_snapshot, 1, entreprise_snapshot, 1, "
                        "chantier_snapshot, 1, '2026-10-02', '2026-03-12', total_ht FROM devis WHERE id=?", self.client(), d)

    def test_INV_40_etat_de_naissance_du_bc(self):
        for mod in ({"montant_deja_facture_ht": "5.00"}, {"avancement": "5.00"}, {"frozen_at": TS},
                    {"date_100_facture": "2026-10-02"}, {"motif_annulation": "m"}):
            with self.subTest(mod=mod):
                d = self.devis_accepte()
                with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-40"):
                    self.creer_bc(d, lignes=False, **mod)

    def test_INV_175_un_devis_avec_bc_ne_quitte_accepte_que_si_le_bc_est_annule(self):
        for etat, autorise in (("en_cours", False), ("gele", False), ("termine", False), ("annule", True), ("annule_gele", True)):
            with self.subTest(bc=etat):
                bc = self.bc_en_etat(etat)
                for m in ("statut='annule', cancelled_at='%s', motif_annulation='m'" % TS, "statut='en_attente'",
                          "statut='refuse', date_refus='2026-03-20'"):
                    sql = f"UPDATE devis SET {m} WHERE id=?"
                    if autorise:
                        # le BC annulé libère le devis (les CHECK de gel limitent ensuite les cibles d'un devis gelé)
                        if etat == "annule" or "annule" in m:
                            self.permis(sql, bc.d)
                    else:
                        self.refuse_inv("INV-175", sql, bc.d)
        d = self.devis_accepte()
        self.permis("UPDATE devis SET statut='en_attente' WHERE id=?", d)                                # accepté sans BC : libre
        bc = self.bc_en_etat("en_cours")
        self.permis("UPDATE devis SET updated_at=? WHERE id=?", TS2, bc.d)                               # sans changement de statut

    def test_INV_174_un_bc_ne_se_supprime_jamais(self):
        for etat in ETATS_BC:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                self.refuse_inv("INV-174", "DELETE FROM bons_commande WHERE id=?", bc.b)
        self.refuse_inv("INV-174", "DELETE FROM bons_commande")
        bc = self.bc_en_etat("en_cours")
        numero = self.un("SELECT numero FROM bons_commande WHERE id=?", bc.b)[0]
        self.refuse_inv("INV-174", "INSERT OR REPLACE INTO bons_commande (numero, devis_id, client_id, client_snapshot, client_snapshot_version, "
                        "entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, "
                        "date_acceptation, montant_contractuel_ht, remise_type, remise_valeur, acompte_type, acompte_valeur) "
                        "SELECT ?, id, client_id, client_snapshot, 1, entreprise_snapshot, 1, chantier_snapshot, 1, '2026-10-02', "
                        "'2026-03-12', total_ht, remise_type, remise_valeur, acompte_type, acompte_valeur FROM devis WHERE id=?", numero, bc.d)

    def test_INV_36_lignes_et_garanties_de_bc_selon_l_etat(self):
        for etat in ETATS_BC:
            bc = self.bc_en_etat(etat, dl3=True)
            ops = {"insert ligne": ("lig_ins", None), "update ligne": ("UPDATE bc_lignes SET designation='x' WHERE id=?", (bc.bl1,)),
                   "delete ligne": ("DELETE FROM bc_lignes WHERE id=?", (bc.bl2,)),
                   "insert garantie": ("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'parfait_achevement')", (bc.bl1,)),
                   "update garantie": ("UPDATE bc_ligne_garanties SET garantie_type='parfait_achevement' WHERE id=?", (bc.bg1,)),
                   "delete garantie": ("DELETE FROM bc_ligne_garanties WHERE id=?", (bc.bg1,))}
            for nom, (sql, args) in ops.items():
                with self.subTest(etat=etat, operation=nom):
                    if nom == "insert ligne":
                        self.db.execute("SAVEPOINT s")
                        try:
                            if etat == "en_cours":
                                self.ligne_bc(bc.b, bc.dl3, 3)
                            else:
                                with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-36"):
                                    self.ligne_bc(bc.b, bc.dl3, 3)
                        finally:
                            self.db.execute("ROLLBACK TO s")
                            self.db.execute("RELEASE s")
                    elif etat == "en_cours":
                        self.permis(sql, *args)
                    else:
                        self.refuse_inv("INV-36", sql, *args)

    def test_INV_95_96_protection_de_numerotation_sequences(self):
        self.un(ATTRIBUER, "BCD", 26)
        self.un(ATTRIBUER, "BCD", 26)
        self.refuse_inv("ne se supprime jamais", "DELETE FROM numerotation_sequences WHERE type_objet='BCD'")
        self.refuse_inv("ne se supprime jamais", "DELETE FROM numerotation_sequences")
        self.refuse_inv("ne se supprime jamais", "INSERT OR REPLACE INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('BCD', 26, 9)")
        self.refuse_inv("INV-", "UPDATE numerotation_sequences SET dernier_numero=1 WHERE type_objet='BCD'")
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='BCD'")[0], 2)

    def test_T45_triggers_001_et_005_toujours_actifs(self):
        f = self.fournisseur()
        cat = self.db.execute("INSERT INTO categories_depenses (code, libelle, actif, ordre) VALUES ('MAT', 'M', 1, 1)").lastrowid
        self.db.execute("INSERT INTO depenses (numero, fournisseur_id, date_depense, montant, categorie_id, description) "
                        "VALUES ('DEP-00001-26', ?, '2026-10-02', '1.00', ?, 'x')", (f, cat))
        i = self.un("SELECT id FROM depenses")[0]
        self.refuse_inv("INV-", "UPDATE depenses SET numero='DEP-00002-26' WHERE id=?", i)
        self.refuse_inv("INV-", "DELETE FROM depenses WHERE id=?", i)
        self.db.execute("UPDATE depenses SET cancelled_at=?, motif_annulation='Erreur' WHERE id=?", (TS2, i))
        self.refuse_inv("INV-", "UPDATE depenses SET montant='2.00' WHERE id=?", i)
        self.refuse_inv("INV-", "DELETE FROM depenses WHERE id=?", i)
        self.fournisseur(code="FOU-0900")
        self.refuse_inv("INV-183", "DELETE FROM fournisseurs WHERE id=?", f)


class Isolation(Base):
    """Chaque trigger touché par 005a refuse seul la violation qui lui est propre ; retiré, la violation passe (il est donc le garde) ;
    recréé à partir de son SQL, il la refuse de nouveau."""

    def prep_scenarios(self):
        """nom -> liste de (préparation(t) retournant l'action, motif du message)."""
        def devis_ligne(t, etat="accepte", type_="decennale"):
            d = t.devis_direct(etat)
            l = t.ligne(d, 1)
            g = t.garantie(l, type_)
            return d, l, g

        def s(*items):
            return list(items)
        sc = {}
        sc["tr_97_clients_no_delete"] = s((lambda t: (lambda c=t.client(): t.db.execute("DELETE FROM clients WHERE id=?", (c,))), "INV-183"))
        sc["tr_97_clients_code_immuable"] = s((lambda t: (lambda c=t.client(): t.db.execute("UPDATE clients SET code='CLI-0999' WHERE id=?", (c,))), "INV-183"))
        sc["tr_97_fournisseurs_no_delete"] = s((lambda t: (lambda f=t.fournisseur(): t.db.execute("DELETE FROM fournisseurs WHERE id=?", (f,))), "INV-183"))
        sc["tr_97_fournisseurs_code_immuable"] = s((lambda t: (lambda f=t.fournisseur(): t.db.execute("UPDATE fournisseurs SET code='FOU-0999' WHERE id=?", (f,))), "INV-183"))
        sc["tr_98_devis_no_delete"] = s((lambda t: (lambda d=t.devis_direct("annule"): t.db.execute("DELETE FROM devis WHERE id=?", (d,))), "INV-180"))
        sc["tr_01_devis_numero_immuable"] = s(
            (lambda t: (lambda d=t.devis_direct("en_attente"): t.db.execute("UPDATE devis SET numero='DEV-09999-26' WHERE id=?", (d,))), "INV-23"),
            (lambda t: (lambda d=t.devis_direct("en_attente"): t.db.execute("UPDATE devis SET date_creation='2026-03-11' WHERE id=?", (d,))), "INV-23"))
        sc["tr_10_devis_modifiable"] = s((lambda t: (lambda d=t.devis_direct("en_attente"): t.db.execute(
            "UPDATE devis SET created_at='2020-01-01T00:00:00.000Z' WHERE id=?", (d,))), "INV-31"))
        sc["tr_10_devis_client_immuable"] = s((lambda t: (lambda d=t.devis_direct("en_attente"), c=t.client(): t.db.execute(
            "UPDATE devis SET client_id=? WHERE id=?", (c, d))), "INV-180"))
        sc["tr_10_devis_en_attente"] = s((lambda t: (lambda d=t.devis_direct("en_attente"): t.db.execute(
            "UPDATE devis SET total_ht='40.00' WHERE id=?", (d,))), "INV-196"))
        sc["tr_10_devis_verrouille"] = s(
            (lambda t: (lambda d=t.devis_direct("accepte"): t.db.execute("UPDATE devis SET total_ht='40.00' WHERE id=?", (d,))), "INV-181"),
            (lambda t: (lambda d=t.devis_direct("refuse"): t.db.execute("UPDATE devis SET objet='x' WHERE id=?", (d,))), "INV-181"),
            (lambda t: (lambda d=t.devis_direct("refuse"): t.db.execute(
                "UPDATE devis SET statut='annule', cancelled_at=?, motif_annulation='m' WHERE id=?", (TS, d))), "INV-182"))
        sc["tr_10_devis_annule"] = s((lambda t: (lambda d=t.devis_direct("annule"): t.db.execute("UPDATE devis SET total_ht='40.00' WHERE id=?", (d,))), "INV-31"))
        sc["tr_10_devis_revision"] = s((lambda t: (lambda d=t.devis_direct("en_attente"): t.db.execute("UPDATE devis SET revision=3 WHERE id=?", (d,))), "INV-196"))
        sc["tr_10_devis_acceptation"] = s((lambda t: (lambda d=t.devis_direct("en_attente", revision_en_cours=1): t.db.execute(
            "UPDATE devis SET statut='accepte', date_acceptation='2026-03-12', revision_en_cours=0 WHERE id=?", (d,))), "INV-196"))
        sc["tr_10_devis_finalisation"] = s((lambda t: (lambda d=t.brouillon(): t.db.execute(
            "UPDATE devis SET numero='DEV-00001-26', statut='en_attente' WHERE id=?", (d,))), "INV-196"))
        sc["tr_14_devis_frozen_at"] = s((lambda t: (lambda d=t.devis_direct("accepte", frozen_at=TS): t.db.execute(
            "UPDATE devis SET frozen_at=NULL WHERE id=?", (d,))), "INV-34"))
        ins_l = ("INSERT INTO devis_lignes (devis_id, ordre, designation, quantite, unite, prix_unitaire_ht, remise_type, type_prestation, total_ht) "
                 "VALUES (?, 3, 'N', '1', 'u', '1.5', 'aucune', 'pose', '1.50')")
        sc["tr_11_devis_lignes_insert"] = s((lambda t: (lambda d=t.devis_direct("accepte"): t.db.execute(ins_l, (d,))), "INV-36"))
        sc["tr_11_devis_lignes_update"] = s(
            (lambda t: (lambda x=devis_ligne(t): t.db.execute("UPDATE devis_lignes SET designation='x' WHERE id=?", (x[1],))), "INV-36"),
            (lambda t: (lambda x=devis_ligne(t), y=devis_ligne(t, "brouillon"): t.db.execute(
                "UPDATE devis_lignes SET devis_id=?, ordre=9 WHERE id=?", (x[0], y[1]))), "INV-36"))
        sc["tr_11_devis_lignes_delete"] = s((lambda t: (lambda x=t.devis_direct("refuse"): (t.ligne(x, 1), t.db.execute(
            "DELETE FROM devis_lignes WHERE devis_id=?", (x,)))[1]), "INV-36"))
        sc["tr_11_devis_ligne_garanties_insert"] = s((lambda t: (lambda x=devis_ligne(t): t.db.execute(
            "INSERT INTO devis_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'parfait_achevement')", (x[1],))), "INV-36"))
        sc["tr_11_devis_ligne_garanties_update"] = s(
            (lambda t: (lambda x=devis_ligne(t): t.db.execute("UPDATE devis_ligne_garanties SET garantie_type='parfait_achevement' WHERE id=?", (x[2],))), "INV-36"),
            (lambda t: (lambda x=devis_ligne(t), y=devis_ligne(t, "brouillon", "biennale"): t.db.execute(
                "UPDATE devis_ligne_garanties SET ligne_id=? WHERE id=?", (x[1], y[2]))), "INV-36"))
        sc["tr_11_devis_ligne_garanties_delete"] = s((lambda t: (lambda x=devis_ligne(t): t.db.execute("DELETE FROM devis_ligne_garanties WHERE id=?", (x[2],))), "INV-36"))
        sc["tr_100_devis_revisions_no_update"] = s((lambda t: (lambda r=t.revision_directe(): t.db.execute(
            "UPDATE devis_revisions SET contenu='{}' WHERE id=?", (r,))), "INV-196"))
        sc["tr_100_devis_revisions_no_delete"] = s((lambda t: (lambda r=t.revision_directe(): t.db.execute(
            "DELETE FROM devis_revisions WHERE id=?", (r,))), "INV-196"))
        sc["tr_100_devis_revisions_insert"] = s(
            (lambda t: (lambda d=t.devis_direct("accepte"): t.db.execute(
                "INSERT INTO devis_revisions (devis_id, revision, schema_contenu, contenu, total_ht, valide_at) VALUES (?, 1, 1, '{}', '1.00', ?)", (d, TS))), "INV-196"),
            (lambda t: (lambda d=t.devis_direct("en_attente", revision_en_cours=1): t.db.execute(
                "INSERT INTO devis_revisions (devis_id, revision, schema_contenu, contenu, total_ht, valide_at) VALUES (?, 3, 1, '{}', '1.00', ?)", (d, TS))), "INV-196"))
        # --- 004 -----------------------------------------------------------------------------------------------
        def bc_(etat, **kw):
            return lambda t: t.bc_en_etat(etat, **kw)
        sc["tr_01_bons_commande_numero_immuable"] = s((lambda t: (lambda bc=t.bc_en_etat("en_cours"): t.db.execute(
            "UPDATE bons_commande SET numero='BCD-00099-26' WHERE id=?", (bc.b,))), "INV-23"))
        sc["tr_12_bons_commande_modifiable"] = s((lambda t: (lambda bc=t.bc_en_etat("en_cours"): t.db.execute(
            "UPDATE bons_commande SET created_at='2020-01-01T00:00:00.000Z' WHERE id=?", (bc.b,))), "INV-36"))
        sc["tr_12_bons_commande_gele"] = s(
            (lambda t: (lambda bc=t.bc_en_etat("gele"): t.db.execute("UPDATE bons_commande SET montant_contractuel_ht='1.00' WHERE id=?", (bc.b,))), "INV-36"),
            (lambda t: (lambda bc=t.bc_en_etat("gele"), c=t.client(): t.db.execute("UPDATE bons_commande SET client_id=? WHERE id=?", (c, bc.b))), "INV-36"))
        sc["tr_12_bons_commande_annule"] = s(
            (lambda t: (lambda bc=t.bc_en_etat("annule"): t.db.execute("UPDATE bons_commande SET date_debut='2026-11-01' WHERE id=?", (bc.b,))), "INV-173"),
            (lambda t: (lambda bc=t.bc_en_etat("annule"), c=t.client(): t.db.execute("UPDATE bons_commande SET client_id=? WHERE id=?", (c, bc.b))), "INV-173"))
        sc["tr_14_bons_commande_frozen_at"] = s((lambda t: (lambda bc=t.bc_en_etat("gele"): t.db.execute("UPDATE bons_commande SET frozen_at=NULL WHERE id=?", (bc.b,))), "INV-34"))
        sc["tr_17_bons_commande_insert"] = s(
            (lambda t: (lambda d=t.devis_accepte(): t.creer_bc(d, lignes=False, montant_deja_facture_ht="5.00")), "INV-40"),
            (lambda t: (lambda d=t.devis_direct("en_attente"): t.creer_bc(d, lignes=False)), "INV-40"),
            (lambda t: (lambda d=t.devis_accepte(): t.creer_bc(d, lignes=False, client_id=t.client())), "INV-48"))
        sc["tr_19_bons_commande_no_delete"] = s((lambda t: (lambda b=t.creer_bc(t.devis_accepte(), lignes=False): t.db.execute("DELETE FROM bons_commande WHERE id=?", (b,))), "INV-174"))
        sc["tr_18_devis_statut_avec_bc"] = s((lambda t: (lambda bc=t.bc_en_etat("en_cours"): t.db.execute(
            "UPDATE devis SET statut='annule', cancelled_at=?, motif_annulation='m' WHERE id=?", (TS, bc.d))), "INV-175"))
        sc["tr_13_bc_lignes_insert"] = s((lambda t: (lambda bc=t.bc_en_etat("gele", dl3=True): t.ligne_bc(bc.b, bc.dl3, 3)), "INV-36"))
        sc["tr_13_bc_lignes_update"] = s((lambda t: (lambda bc=t.bc_en_etat("gele"): t.db.execute("UPDATE bc_lignes SET designation='x' WHERE id=?", (bc.bl1,))), "INV-36"))
        sc["tr_13_bc_lignes_delete"] = s((lambda t: (lambda bc=t.bc_en_etat("gele"): t.db.execute("DELETE FROM bc_lignes WHERE id=?", (bc.bl2,))), "INV-36"))
        sc["tr_13_bc_ligne_garanties_insert"] = s((lambda t: (lambda bc=t.bc_en_etat("gele"): t.db.execute(
            "INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'parfait_achevement')", (bc.bl1,))), "INV-36"))
        sc["tr_13_bc_ligne_garanties_update"] = s((lambda t: (lambda bc=t.bc_en_etat("gele"): t.db.execute(
            "UPDATE bc_ligne_garanties SET garantie_type='parfait_achevement' WHERE id=?", (bc.bg1,))), "INV-36"))
        sc["tr_13_bc_ligne_garanties_delete"] = s((lambda t: (lambda bc=t.bc_en_etat("gele"): t.db.execute("DELETE FROM bc_ligne_garanties WHERE id=?", (bc.bg1,))), "INV-36"))
        sc["tr_96_numerotation_sequences_no_delete"] = s((lambda t: (lambda: (t.un(ATTRIBUER, "BCD", 26), t.db.execute(
            "DELETE FROM numerotation_sequences WHERE type_objet='BCD'"))[1]), "ne se supprime jamais"))
        return sc

    def isole(self, gardes):
        """Base 001-005a dont tous les triggers sont supprimés sauf `gardes`."""
        t = Base()
        t.db = migrer()
        t._n = 0
        for (nom,) in t.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
            if nom not in gardes:
                t.db.execute(f"DROP TRIGGER {nom}")
        return t

    def test_T45_tous_les_triggers_touches_ont_un_scenario(self):
        attendus = TRIGGERS_NOUVEAUX | TRIGGERS_REECRITS | TRIGGERS_RECREES_IDENTIQUES | TRIGGERS_004
        self.assertEqual(set(self.prep_scenarios()), attendus)

    def test_T45_chaque_trigger_refuse_seul_retire_la_violation_passe_recree_il_refuse_de_nouveau(self):
        for nom, scenarios in sorted(self.prep_scenarios().items()):
            for i, (preparer, motif) in enumerate(scenarios):
                with self.subTest(trigger=nom, scenario=i):
                    seul = self.isole({nom})
                    sql = sql_de(seul.db, nom)
                    with self.assertRaisesRegex(sqlite3.IntegrityError, motif):
                        preparer(seul)()
                    seul.db.execute(f"DROP TRIGGER {nom}")                                                  # temporairement supprimé…
                    preparer(seul)()                                                                       # …plus aucune garde : la violation passe
                    seul.db.execute(sql)                                                                   # …puis recréé à partir de son SQL
                    with self.assertRaisesRegex(sqlite3.IntegrityError, motif):
                        preparer(seul)()
                    self.assertEqual(sql_de(seul.db, nom), sql)

    def test_T45_aucun_scenario_n_est_arrete_par_une_contrainte_sans_le_trigger(self):
        """Garde-fou des scénarios ci-dessus : sans trigger, la violation passe ; elle n'est donc pas masquée par un CHECK ou une FK."""
        sans = self.isole(set())
        for nom, scenarios in sorted(self.prep_scenarios().items()):
            for i, (preparer, _) in enumerate(scenarios):
                with self.subTest(trigger=nom, scenario=i):
                    preparer(sans)()


if __name__ == "__main__":
    unittest.main(verbosity=2)
