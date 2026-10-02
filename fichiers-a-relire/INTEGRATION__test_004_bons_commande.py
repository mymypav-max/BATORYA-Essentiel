"""T-29 — DDL de la tranche Bons de commande (modèle V3.12, §4.7 et §4.18 ; migration metier/004_bons_commande.sql).
Tables : bons_commande, bc_lignes, bc_ligne_garanties ; triggers TR-01, TR-12 (x3), TR-13 (x6), TR-14, TR-17, TR-18, TR-19
et TR-96 (posé sur numerotation_sequences). Les migrations 001, 002, 003 puis 004 sont appliquées comme le fait le runner
(une transaction par fichier, user_version posé après succès).

Exécution : python3 src-tauri/tests/metier/test_004_bons_commande.py
Les méthodes portent le nom de l'invariant vérifié (test_INV_xx_…) ; les autres commencent par test_T29_ ou test_D3x_.
Ces tests ne dépendent d'aucune interface graphique ni d'aucun service : le service de création du BC (numéro de la séquence
BCD, copie du devis, des lignes et des garanties) est reproduit avec les requêtes documentées (modèle §4.7, §4.17 point 8).
La facturation, le gel par TR-15 (factures, règlements) et l'historique n'existent pas encore : le gel est posé ici par un
UPDATE de frozen_at, les caches par un UPDATE unique (comme le fera le service financier). CK-13 (diagnostic devis <-> BC,
modèle §14) est une requête de contrôle ; une version de référence est exécutée ici (constante CK13).
Connexion de test : PRAGMA foreign_keys=ON et PRAGMA recursive_triggers=ON (D-39) ; un test vérifie que le réglage est actif.
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

TABLES_001 = {"import_anomalies", "numerotation_sequences", "categories_prestations", "categories_depenses",
              "clients", "prestations", "prestation_garanties"}
TABLES_002 = {"fournisseurs"}
TABLES_003 = {"devis", "devis_lignes", "devis_ligne_garanties"}
TABLES_004 = {"bons_commande", "bc_lignes", "bc_ligne_garanties"}
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
INDEXES_001_002 = {"idx_clients_statut", "idx_prestations_categorie_id", "idx_prestations_actif",
                   "idx_import_anomalies_categorie_statut", "idx_fournisseurs_statut"}
INDEXES_003 = {"idx_devis_client_id", "idx_devis_statut", "idx_devis_date_creation", "idx_devis_lignes_prestation_id"}
INDEXES_004 = {"idx_bons_commande_client_id", "idx_bons_commande_statut", "idx_bc_lignes_prestation_id"}

COLONNES_BC = ["id", "numero", "devis_id", "client_id", "client_snapshot", "client_snapshot_version",
               "entreprise_snapshot", "entreprise_snapshot_version", "chantier_snapshot", "chantier_snapshot_version",
               "date_creation", "date_acceptation", "date_debut", "date_fin", "montant_contractuel_ht", "remise_type",
               "remise_valeur", "acompte_type", "acompte_valeur", "montant_deja_facture_ht", "avancement",
               "date_100_facture", "statut", "completed_at", "cancelled_at", "motif_annulation", "frozen_at",
               "created_at", "updated_at", "origine", "legacy_id", "legacy_data", "legacy_numero"]
COLONNES_BC_LIGNES = ["id", "bc_id", "devis_ligne_id", "ordre", "prestation_id", "reference_prestation", "designation",
                      "description", "quantite", "unite", "prix_unitaire_ht", "remise_type", "remise_valeur",
                      "type_prestation", "total_ht", "created_at", "updated_at"]
COLONNES_BC_GARANTIES = ["id", "ligne_id", "garantie_type", "created_at"]

TS = "2026-10-01T10:00:00.000Z"
TS2 = "2026-10-02T11:30:15.123Z"
SNAP = '{"nom": "Dupont"}'
ATTRIBUER = ("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES (?, ?, 1) "
             "ON CONFLICT (type_objet, annee) DO UPDATE SET dernier_numero = dernier_numero + 1, "
             "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') RETURNING dernier_numero")
TS_GLOB = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")

# CK-13 (modèle §14) : requête de contrôle, version de référence. Une ligne = une divergence (bc_id, devis_id, anomalie).
# La règle du miroir (liste S) ne porte que sur les BC non annulés ; les contrôles de statut portent sur tous.
CK13 = """
SELECT b.id AS bc_id, b.devis_id AS devis_id, 'client_id' AS anomalie
  FROM bons_commande b JOIN devis d ON d.id = b.devis_id WHERE b.statut <> 'annule' AND b.client_id IS NOT d.client_id
UNION ALL SELECT b.id, b.devis_id, 'contractuel' FROM bons_commande b JOIN devis d ON d.id = b.devis_id
  WHERE b.statut <> 'annule' AND b.montant_contractuel_ht IS NOT d.total_ht
UNION ALL SELECT b.id, b.devis_id, 'remise' FROM bons_commande b JOIN devis d ON d.id = b.devis_id
  WHERE b.statut <> 'annule' AND (b.remise_type IS NOT d.remise_type OR b.remise_valeur IS NOT d.remise_valeur)
UNION ALL SELECT b.id, b.devis_id, 'acompte' FROM bons_commande b JOIN devis d ON d.id = b.devis_id
  WHERE b.statut <> 'annule' AND (b.acompte_type IS NOT d.acompte_type OR b.acompte_valeur IS NOT d.acompte_valeur)
UNION ALL SELECT b.id, b.devis_id, 'snapshots' FROM bons_commande b JOIN devis d ON d.id = b.devis_id
  WHERE b.statut <> 'annule' AND (b.client_snapshot IS NOT d.client_snapshot
     OR b.client_snapshot_version IS NOT d.client_snapshot_version
     OR b.entreprise_snapshot IS NOT d.entreprise_snapshot
     OR b.entreprise_snapshot_version IS NOT d.entreprise_snapshot_version
     OR b.chantier_snapshot IS NOT d.chantier_snapshot
     OR b.chantier_snapshot_version IS NOT d.chantier_snapshot_version)
UNION ALL SELECT b.id, b.devis_id, 'date_acceptation' FROM bons_commande b JOIN devis d ON d.id = b.devis_id
  WHERE b.statut <> 'annule' AND b.date_acceptation IS NOT d.date_acceptation
UNION ALL SELECT b.id, b.devis_id, 'ligne_manquante' FROM bons_commande b JOIN devis_lignes dl ON dl.devis_id = b.devis_id
  WHERE b.statut <> 'annule'
    AND NOT EXISTS (SELECT 1 FROM bc_lignes bl WHERE bl.bc_id = b.id AND bl.devis_ligne_id = dl.id)
UNION ALL SELECT b.id, b.devis_id, 'ligne_en_trop' FROM bons_commande b JOIN bc_lignes bl ON bl.bc_id = b.id
  WHERE b.statut <> 'annule'
    AND NOT EXISTS (SELECT 1 FROM devis_lignes dl WHERE dl.id = bl.devis_ligne_id AND dl.devis_id = b.devis_id)
UNION ALL SELECT b.id, b.devis_id, 'ligne_differente' FROM bons_commande b
  JOIN bc_lignes bl ON bl.bc_id = b.id JOIN devis_lignes dl ON dl.id = bl.devis_ligne_id AND dl.devis_id = b.devis_id
  WHERE b.statut <> 'annule'
    AND (bl.ordre IS NOT dl.ordre OR bl.prestation_id IS NOT dl.prestation_id
         OR bl.reference_prestation IS NOT dl.reference_prestation OR bl.designation IS NOT dl.designation
         OR bl.description IS NOT dl.description OR bl.quantite IS NOT dl.quantite OR bl.unite IS NOT dl.unite
         OR bl.prix_unitaire_ht IS NOT dl.prix_unitaire_ht OR bl.remise_type IS NOT dl.remise_type
         OR bl.remise_valeur IS NOT dl.remise_valeur OR bl.type_prestation IS NOT dl.type_prestation
         OR bl.total_ht IS NOT dl.total_ht)
UNION ALL SELECT b.id, b.devis_id, 'garantie_manquante' FROM bons_commande b
  JOIN bc_lignes bl ON bl.bc_id = b.id JOIN devis_ligne_garanties dg ON dg.ligne_id = bl.devis_ligne_id
  WHERE b.statut <> 'annule'
    AND NOT EXISTS (SELECT 1 FROM bc_ligne_garanties bg WHERE bg.ligne_id = bl.id AND bg.garantie_type = dg.garantie_type)
UNION ALL SELECT b.id, b.devis_id, 'garantie_en_trop' FROM bons_commande b
  JOIN bc_lignes bl ON bl.bc_id = b.id JOIN bc_ligne_garanties bg ON bg.ligne_id = bl.id
  WHERE b.statut <> 'annule'
    AND NOT EXISTS (SELECT 1 FROM devis_ligne_garanties dg WHERE dg.ligne_id = bl.devis_ligne_id AND dg.garantie_type = bg.garantie_type)
UNION ALL SELECT b.id, b.devis_id, 'bc_annule_devis_non_annule' FROM bons_commande b JOIN devis d ON d.id = b.devis_id
  WHERE b.statut = 'annule' AND d.statut <> 'annule'
UNION ALL SELECT b.id, b.devis_id, 'devis_annule_bc_non_annule' FROM bons_commande b JOIN devis d ON d.id = b.devis_id
  WHERE d.statut = 'annule' AND b.statut <> 'annule'
UNION ALL SELECT NULL, d.id, 'devis_accepte_sans_bc' FROM devis d
  WHERE d.statut = 'accepte' AND NOT EXISTS (SELECT 1 FROM bons_commande b WHERE b.devis_id = d.id)
UNION ALL SELECT b.id, b.devis_id, 'contractuel_nul' FROM bons_commande b WHERE b.montant_contractuel_ht = '0.00'
"""


def migrer(recursive=True):
    """Applique 001, 002, 003 puis 004 comme le runner : une transaction par fichier, user_version après succès.
    La connexion applique les réglages obligatoires (D-39) : foreign_keys=ON et recursive_triggers=ON."""
    db = sqlite3.connect(":memory:", isolation_level=None)
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA recursive_triggers=" + ("ON" if recursive else "OFF"))
    for numero, sql in ((1, SQL_001), (2, SQL_002), (3, SQL_003), (4, SQL_004)):
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

    def tous(self, sql, *args):
        return self.db.execute(sql, args).fetchall()

    def essai(self, sql, *args):
        """Retourne None si l'instruction réussit, sinon le message d'erreur."""
        try:
            self.db.execute(sql, args)
            return None
        except sqlite3.IntegrityError as e:
            return str(e)

    def ck13(self, db=None):
        return sorted((db or self.db).execute(CK13).fetchall(), key=lambda r: (r[0] or 0, r[1], r[2]))

    def essai_creer(self, d, **kw):
        """Message d'erreur de la création du BC sans lignes (None si elle réussit)."""
        try:
            self.creer_bc(d, lignes=False, **kw)
            return None
        except sqlite3.IntegrityError as e:
            return str(e)

    # --- fabrication de données : tranches 001 à 003 -------------------------------
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

    def accepter(self, d):
        self.db.execute("UPDATE devis SET statut='accepte', date_acceptation='2026-03-12' WHERE id=?", (d,))

    def geler_devis(self, d):
        self.db.execute("UPDATE devis SET frozen_at=? WHERE id=?", (TS, d))

    def annuler_devis(self, d):
        self.db.execute("UPDATE devis SET statut='annule', cancelled_at=?, motif_annulation='Annulation du BC' WHERE id=?", (TS, d))

    def devis_accepte(self, client_id=None, lignes=2, **kw):
        """Devis accepté non gelé : ligne 1 (prestation du catalogue, deux garanties), ligne 2 libre sans garantie."""
        kw.setdefault("total_ht", "31.50")
        kw.setdefault("remise_type", "pourcentage")
        kw.setdefault("remise_valeur", "10.00")
        kw.setdefault("acompte_type", "montant")
        kw.setdefault("acompte_valeur", "5.00")
        d = self.devis(client_id=client_id, **kw)
        if lignes >= 1:
            self._n += 1
            l1 = self.ligne(d, 1, prestation_id=self.prestation(f"PLO-{self._n:03d}"), reference_prestation="PLO-X")
            self.garantie(l1, "decennale")
            self.garantie(l1, "biennale")
        if lignes >= 2:
            self.ligne(d, 2, designation="Ligne libre", total_ht="10.50", quantite="1")
        self.accepter(d)
        return d

    # --- fabrication de données : tranche 004 (ce que fait le service de création) ----
    def creer_bc(self, d=None, numero=None, lignes=True, **kw):
        """INSERT du BC par copie du devis accepté (liste S) ; le numéro vient de la séquence BCD (année de date_creation)."""
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
        self.db.execute(f"INSERT INTO bons_commande ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))
        b = self.un("SELECT id FROM bons_commande WHERE numero=?", numero)[0]
        if lignes:
            self.copier_lignes(b)
        return b

    def copier_lignes(self, b):
        """Copie lignes et garanties de ligne du devis du BC (le devis reste le seul point d'édition, INV-38)."""
        self.db.execute("INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, prestation_id, reference_prestation, designation, "
                        "description, quantite, unite, prix_unitaire_ht, remise_type, remise_valeur, type_prestation, total_ht) "
                        "SELECT ?, dl.id, dl.ordre, dl.prestation_id, dl.reference_prestation, dl.designation, dl.description, "
                        "dl.quantite, dl.unite, dl.prix_unitaire_ht, dl.remise_type, dl.remise_valeur, dl.type_prestation, dl.total_ht "
                        "FROM devis_lignes dl JOIN bons_commande b ON b.devis_id = dl.devis_id WHERE b.id = ? ORDER BY dl.ordre",
                        (b, b))
        self.db.execute("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) SELECT bl.id, dg.garantie_type "
                        "FROM bc_lignes bl JOIN devis_ligne_garanties dg ON dg.ligne_id = bl.devis_ligne_id WHERE bl.bc_id = ?", (b,))

    def ligne_bc(self, b, dl, ordre, **kw):
        """Ligne de BC copiée de la ligne de devis dl."""
        r = self.db.execute("SELECT prestation_id, reference_prestation, designation, description, quantite, unite, "
                            "prix_unitaire_ht, remise_type, remise_valeur, type_prestation, total_ht FROM devis_lignes WHERE id=?",
                            (dl,)).fetchone()
        cols = dict(zip(["prestation_id", "reference_prestation", "designation", "description", "quantite", "unite",
                         "prix_unitaire_ht", "remise_type", "remise_valeur", "type_prestation", "total_ht"], r))
        cols.update({"bc_id": b, "devis_ligne_id": dl, "ordre": ordre})
        cols.update(kw)
        self.db.execute(f"INSERT INTO bc_lignes ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))
        return self.un("SELECT id FROM bc_lignes WHERE bc_id=? AND ordre=?", cols["bc_id"], cols["ordre"])[0]

    def bc_ligne(self, b, ordre=1):
        return self.un("SELECT id FROM bc_lignes WHERE bc_id=? AND ordre=?", b, ordre)[0]

    # --- transitions d'état du BC (le service financier / TR-15 les feront plus tard) ---
    def geler_bc(self, b):
        """Pose du gel sur le BC et son devis (ce que fera TR-15, dans la transaction de l'événement)."""
        self.db.execute("UPDATE bons_commande SET frozen_at=? WHERE id=?", (TS, b))
        self.db.execute("UPDATE devis SET frozen_at=? WHERE id=(SELECT devis_id FROM bons_commande WHERE id=?)", (TS, b))

    def terminer_bc(self, b):
        """Caches écrits en un seul UPDATE (INV-164) : BC entièrement facturé."""
        self.db.execute("UPDATE bons_commande SET statut='termine', completed_at=?, date_100_facture='2026-10-02', "
                        "avancement='100.00', montant_deja_facture_ht=montant_contractuel_ht, updated_at=? WHERE id=?", (TS, TS, b))

    def annuler_bc(self, b):
        self.db.execute("UPDATE bons_commande SET statut='annule', cancelled_at=?, motif_annulation='Client renonce', "
                        "completed_at=NULL, date_100_facture=NULL, updated_at=? WHERE id=?", (TS, TS, b))

    def bc_en_etat(self, etat, client_id=None, dl3=False, **kw):
        """BC (avec lignes et garanties) dans l'état voulu : en_cours, gele, termine, annule, annule_gele.
        dl3=True ajoute au devis (avant le gel) une 3e ligne non copiée dans le BC, utilisable pour tester l'INSERT d'une ligne de BC."""
        d = self.devis_accepte(client_id=client_id)
        b = self.creer_bc(d, **kw)
        extra = self.ligne(d, 3, designation="Ligne à venir", total_ht="5.00", quantite="1") if dl3 else None
        if etat in ("gele", "termine", "annule_gele"):
            self.geler_bc(b)
        if etat == "termine":
            self.terminer_bc(b)
        if etat in ("annule", "annule_gele"):
            self.annuler_bc(b)
        elif etat not in ("en_cours", "gele", "termine"):
            raise ValueError(etat)
        return types.SimpleNamespace(
            d=d, b=b, dl3=extra, bl1=self.bc_ligne(b, 1), bl2=self.bc_ligne(b, 2),
            dl1=self.un("SELECT id FROM devis_lignes WHERE devis_id=? AND ordre=1", d)[0],
            dl2=self.un("SELECT id FROM devis_lignes WHERE devis_id=? AND ordre=2", d)[0],
            bg1=self.un("SELECT id FROM bc_ligne_garanties WHERE ligne_id=? AND garantie_type='decennale'", self.bc_ligne(b, 1))[0],
            bg2=self.un("SELECT id FROM bc_ligne_garanties WHERE ligne_id=? AND garantie_type='biennale'", self.bc_ligne(b, 1))[0])


ETATS_MODIFIABLES = ("en_cours",)
ETATS_FIGES = ("gele", "termine", "annule", "annule_gele")        # lignes et garanties non modifiables
ETATS_TOUS = ETATS_MODIFIABLES + ETATS_FIGES


class Migration(Base):
    def test_T29_migration_sur_base_issue_de_001_a_003(self):
        self.assertEqual(self.un("PRAGMA user_version")[0], 4)
        noms = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        self.assertEqual(noms, TABLES_001 | TABLES_002 | TABLES_003 | TABLES_004)
        strict = {r[1] for r in self.db.execute("PRAGMA table_list") if r[5] == 1}
        self.assertTrue(TABLES_004 <= strict)
        self.assertEqual({r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")},
                         TRIGGERS_001 | TRIGGERS_003 | TRIGGERS_004)
        self.assertEqual({r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")},
                         INDEXES_001_002 | INDEXES_003 | INDEXES_004)
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(self.db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])

    def test_T29_effectifs_de_la_tranche(self):
        sans = re.sub(r"--[^\n]*", "", SQL_004)
        self.assertEqual(len(TABLES_004), 3)
        self.assertEqual(len(TRIGGERS_004), 15)
        self.assertEqual(len(INDEXES_004), 3)
        self.assertEqual(len(re.findall(r"(?im)^\s*CREATE\s+TABLE\b", sans)), 3)
        self.assertEqual(len(re.findall(r"(?im)^\s*CREATE\s+TRIGGER\b", sans)), 15)
        self.assertEqual(len(re.findall(r"(?im)^\s*CREATE\s+INDEX\b", sans)), 3)
        self.assertEqual(len(re.findall(r"(?im)^\s*CREATE\s+UNIQUE\s+INDEX\b", sans)), 0)

    def test_T29_colonnes_exactes(self):
        for table, attendu in (("bons_commande", COLONNES_BC), ("bc_lignes", COLONNES_BC_LIGNES),
                               ("bc_ligne_garanties", COLONNES_BC_GARANTIES)):
            self.assertEqual([r[1] for r in self.db.execute(f"PRAGMA table_info({table})")], attendu, table)

    def test_T29_colonnes_obligatoires_et_defauts(self):
        infos = {r[1]: r for r in self.db.execute("PRAGMA table_info(bons_commande)")}
        obligatoires = {"numero", "devis_id", "client_id", "client_snapshot", "client_snapshot_version", "entreprise_snapshot",
                        "entreprise_snapshot_version", "chantier_snapshot", "chantier_snapshot_version", "date_creation",
                        "date_acceptation", "montant_contractuel_ht", "remise_type", "acompte_type", "montant_deja_facture_ht",
                        "avancement", "statut", "created_at", "updated_at", "origine"}
        for c in COLONNES_BC:
            if c != "id":
                self.assertEqual(infos[c][3], 1 if c in obligatoires else 0, c)
        defauts = {c: infos[c][4] for c in COLONNES_BC if infos[c][4] is not None}
        self.assertEqual(defauts, {"montant_deja_facture_ht": "'0.00'", "avancement": "'0.00'", "statut": "'en_cours'",
                                   "origine": "'v6'", "created_at": "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')",
                                   "updated_at": "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"})
        for t, cols in (("bc_lignes", {"bc_id", "devis_ligne_id", "ordre", "designation", "quantite", "unite", "prix_unitaire_ht",
                                       "remise_type", "type_prestation", "total_ht", "created_at", "updated_at"}),
                        ("bc_ligne_garanties", {"ligne_id", "garantie_type", "created_at"})):
            obl = {r[1] for r in self.db.execute(f"PRAGMA table_info({t})") if r[3] and not r[5]}
            self.assertEqual(obl, cols, t)
        facultatives = {r[1] for r in self.db.execute("PRAGMA table_info(bc_lignes)") if not r[3]}
        self.assertEqual(facultatives, {"id", "prestation_id", "reference_prestation", "description", "remise_valeur"})

    def test_T29_cles_etrangeres(self):
        def fk(table):
            return {(r[2], r[3], r[4], r[6]) for r in self.db.execute(f"PRAGMA foreign_key_list({table})")}
        self.assertEqual(fk("bons_commande"), {("devis", "devis_id", "id", "RESTRICT"), ("clients", "client_id", "id", "RESTRICT")})
        self.assertEqual(fk("bc_lignes"), {("bons_commande", "bc_id", "id", "RESTRICT"),
                                           ("devis_lignes", "devis_ligne_id", "id", "RESTRICT"),
                                           ("prestations", "prestation_id", "id", "RESTRICT")})
        self.assertEqual(fk("bc_ligne_garanties"), {("bc_lignes", "ligne_id", "id", "CASCADE")})
        # aucune clause ON UPDATE (valeur par défaut de SQLite) et aucune FK vers une table absente
        tables = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for t in TABLES_004:
            for r in self.db.execute(f"PRAGMA foreign_key_list({t})"):
                self.assertEqual(r[5], "NO ACTION", (t, r[3]))
                self.assertIn(r[2], tables)
        self.assertNotRegex(re.sub(r"--[^\n]*", "", SQL_004), r"(?i)\bON\s+UPDATE\b")

    def test_T29_index(self):
        def colonnes(nom):
            return [r[2] for r in self.db.execute(f"PRAGMA index_info({nom})")]
        self.assertEqual(colonnes("idx_bons_commande_client_id"), ["client_id"])
        self.assertEqual(colonnes("idx_bons_commande_statut"), ["statut"])
        self.assertEqual(colonnes("idx_bc_lignes_prestation_id"), ["prestation_id"])
        for nom, table in (("idx_bons_commande_client_id", "bons_commande"), ("idx_bons_commande_statut", "bons_commande"),
                           ("idx_bc_lignes_prestation_id", "bc_lignes")):
            self.assertEqual(self.un("SELECT tbl_name FROM sqlite_master WHERE name=?", nom)[0], table)
        # les UNIQUE couvrent numero, devis_id, devis_ligne_id, (bc_id, ordre) et (ligne_id, garantie_type)
        uniques = {}
        for t in TABLES_004:
            uniques[t] = sorted([c[2] for c in self.db.execute(f"PRAGMA index_info({r[1]})")]
                                for r in self.db.execute(f"PRAGMA index_list({t})") if r[2] == 1)
        self.assertEqual(uniques, {"bons_commande": [["devis_id"], ["numero"]],
                                   "bc_lignes": [["bc_id", "ordre"], ["devis_ligne_id"]],
                                   "bc_ligne_garanties": [["ligne_id", "garantie_type"]]})

    def test_T29_aucune_donnee_initiale(self):
        for t in TABLES_001 | TABLES_002 | TABLES_003 | TABLES_004:
            self.assertEqual(self.un(f"SELECT COUNT(*) FROM {t}")[0], 0, t)          # y compris numerotation_sequences
        sans = re.sub(r"--[^\n]*", "", SQL_004)
        sans = re.sub(r"(?i)\bON\s+(DELETE|UPDATE)\s+(RESTRICT|CASCADE)", "", sans)   # actions de FK
        triggers = re.findall(r"CREATE TRIGGER.*?\nEND;", sans, flags=re.S)
        self.assertEqual(len(triggers), len(TRIGGERS_004))
        hors_triggers = sans
        for t in triggers:
            hors_triggers = hors_triggers.replace(t, "")
        self.assertNotRegex(hors_triggers, r"(?i)\b(INSERT|UPDATE|DELETE|DROP|ALTER|PRAGMA|BEGIN|COMMIT)\b|\bREPLACE\s+INTO\b")
        self.assertEqual(sorted(re.findall(r"(?i)\bCREATE\s+(\w+)", hors_triggers)), ["INDEX"] * 3 + ["TABLE"] * 3)

    def test_T29_triggers_ne_font_que_garder(self):
        """Chaque trigger est BEFORE et ne contient que des « SELECT RAISE(ABORT, 'INV-nn: …') [WHERE …] »."""
        sans = re.sub(r"--[^\n]*", "", SQL_004)
        triggers = re.findall(r"CREATE TRIGGER.*?\nEND;", sans, flags=re.S)
        self.assertEqual(len(triggers), 15)
        for t in triggers:
            nom = re.match(r"CREATE TRIGGER (\w+)\nBEFORE (INSERT|UPDATE|DELETE)\b", t)
            self.assertIsNotNone(nom, t[:80])                                       # BEFORE : avant les CHECK
            corps = t[t.index("\nBEGIN") + 6:-len("END;")]
            corps = re.sub(r"'(?:[^']|'')*'", lambda m: m.group(0) if m.group(0).startswith("'INV-") else "''", corps)
            instructions = [i.strip() for i in corps.split(";") if i.strip()]
            self.assertGreaterEqual(len(instructions), 1, nom.group(1))
            for i in instructions:
                self.assertRegex(i, r"^SELECT RAISE\(ABORT, 'INV-\d+: [^']*(?:''[^']*)*'\)")
            self.assertNotRegex(re.sub(r"'(?:[^']|'')*'", "''", corps), r"(?i)\b(INSERT|UPDATE|DELETE|REPLACE|DROP|ALTER)\b")

    def test_T29_triggers_table_et_evenement(self):
        attendu = {"tr_01_bons_commande_numero_immuable": ("bons_commande", "UPDATE OF numero, date_creation"),
                   "tr_12_bons_commande_modifiable": ("bons_commande", "UPDATE"),
                   "tr_12_bons_commande_gele": ("bons_commande", "UPDATE"),
                   "tr_12_bons_commande_annule": ("bons_commande", "UPDATE"),
                   "tr_14_bons_commande_frozen_at": ("bons_commande", "UPDATE OF frozen_at"),
                   "tr_17_bons_commande_insert": ("bons_commande", "INSERT"),
                   "tr_19_bons_commande_no_delete": ("bons_commande", "DELETE"),
                   "tr_18_devis_statut_avec_bc": ("devis", "UPDATE OF statut"),
                   "tr_13_bc_lignes_insert": ("bc_lignes", "INSERT"), "tr_13_bc_lignes_update": ("bc_lignes", "UPDATE"),
                   "tr_13_bc_lignes_delete": ("bc_lignes", "DELETE"),
                   "tr_13_bc_ligne_garanties_insert": ("bc_ligne_garanties", "INSERT"),
                   "tr_13_bc_ligne_garanties_update": ("bc_ligne_garanties", "UPDATE"),
                   "tr_13_bc_ligne_garanties_delete": ("bc_ligne_garanties", "DELETE"),
                   "tr_96_numerotation_sequences_no_delete": ("numerotation_sequences", "DELETE")}
        for nom, (table, evenement) in attendu.items():
            sql, tbl = self.un("SELECT sql, tbl_name FROM sqlite_master WHERE type='trigger' AND name=?", nom)
            with self.subTest(trigger=nom):
                self.assertEqual(tbl, table)
                self.assertRegex(sql, rf"(?s)^CREATE TRIGGER {nom}\nBEFORE {evenement} ON {table}\b")
                if evenement.startswith("UPDATE") and "OF" not in evenement:
                    self.assertNotRegex(sql.split("\nBEGIN")[0], r"UPDATE OF")

    def test_T29_aucune_dependance_aux_tranches_suivantes(self):
        code = re.sub(r"'[^']*'", "''", re.sub(r"--[^\n]*", "", SQL_004))        # sans commentaires ni textes
        for absent in ("factures", "facture_lignes", "reglements", "historique", "documents", "depenses", "garanties",
                       "bc_notes", "pv", "pv_reception", "fournisseurs", "planning", "urssaf_periodes"):
            with self.subTest(objet=absent):
                self.assertNotRegex(code, rf"\b{absent}\b")

    def test_T29_conventions_du_fichier(self):
        sans = re.sub(r"--[^\n]*", "", SQL_004)
        self.assertNotRegex(sans, r"(?i)INSERT\s+OR\s+REPLACE|\bREPLACE\s+INTO\b")
        self.assertNotRegex(sans, r"\{\d")                                           # GLOB sans quantificateur {n}
        self.assertNotRegex(sans, r"\bdate\([a-z_]+\)\s*=\s*[a-z_]+")                 # date(x) IS x, jamais date(x) = x
        for t in TABLES_004:
            self.assertRegex(self.un("SELECT sql FROM sqlite_master WHERE name=?", t)[0], r"\) STRICT$")
            self.assertIn("AUTOINCREMENT", self.un("SELECT sql FROM sqlite_master WHERE name=?", t)[0], t)
        self.assertNotRegex(sans, r"\b(REAL|FLOAT|DOUBLE|NUMERIC)\b")                 # aucun flottant financier

    def test_T29_non_regression_001_a_003_inchangees(self):
        avant = sqlite3.connect(":memory:", isolation_level=None)
        for sql in (SQL_001, SQL_002, SQL_003):
            avant.executescript("BEGIN;" + sql + "\nCOMMIT;")
        def schema(db, noms):
            marques = ",".join("?" * len(noms))
            return db.execute(f"SELECT type, name, sql FROM sqlite_master WHERE name IN ({marques}) ORDER BY name", tuple(noms)).fetchall()
        anciens = [r[0] for r in avant.execute("SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")]
        self.assertEqual(schema(avant, anciens), schema(self.db, anciens))
        self.assertEqual(len(anciens), len(TABLES_001 | TABLES_002 | TABLES_003) + len(TRIGGERS_001 | TRIGGERS_003)
                         + len(INDEXES_001_002 | INDEXES_003))
        # 004 n'ajoute que ses objets : 3 tables, 3 index, 15 triggers (dont 2 posés sur devis et numerotation_sequences)
        apres = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
        nouveaux = apres - set(anciens)
        self.assertEqual(nouveaux, TABLES_004 | INDEXES_004 | TRIGGERS_004)
        self.assertEqual(len(nouveaux), 21)


class Creation(Base):
    """INV-40, INV-48, INV-175, INV-176 : création du BC à partir d'un devis accepté (opération de service)."""

    def test_INV_40_creation_valide_et_etat_de_naissance(self):
        d = self.devis_accepte()
        b = self.creer_bc(d)
        r = self.db.execute("SELECT * FROM bons_commande WHERE id=?", (b,)).fetchone()
        ligne = dict(zip(COLONNES_BC, r))
        self.assertEqual(ligne["numero"], "BCD-00001-26")
        self.assertEqual((ligne["statut"], ligne["montant_deja_facture_ht"], ligne["avancement"]), ("en_cours", "0.00", "0.00"))
        for c in ("frozen_at", "cancelled_at", "completed_at", "motif_annulation", "date_100_facture", "date_debut", "date_fin"):
            self.assertIsNone(ligne[c], c)
        self.assertEqual((ligne["origine"], ligne["legacy_id"], ligne["legacy_data"], ligne["legacy_numero"]), ("v6", None, None, None))
        self.assertEqual((ligne["date_creation"], ligne["date_acceptation"]), ("2026-10-02", "2026-03-12"))
        self.assertEqual((ligne["montant_contractuel_ht"], ligne["remise_type"], ligne["remise_valeur"],
                          ligne["acompte_type"], ligne["acompte_valeur"]), ("31.50", "pourcentage", "10.00", "montant", "5.00"))
        self.assertRegex(ligne["created_at"], TS_GLOB)
        self.assertRegex(ligne["updated_at"], TS_GLOB)
        self.assertEqual(self.un("SELECT COUNT(*) FROM bc_lignes WHERE bc_id=?", b)[0], 2)
        self.assertEqual(self.un("SELECT COUNT(*) FROM bc_ligne_garanties")[0], 2)
        self.assertEqual(self.ck13(), [])
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_INV_40_defauts_de_colonnes_donnent_l_etat_de_naissance(self):
        d = self.devis_accepte()
        self.db.execute("INSERT INTO bons_commande (numero, devis_id, client_id, client_snapshot, client_snapshot_version, "
                        "entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, "
                        "date_creation, date_acceptation, montant_contractuel_ht, remise_type, acompte_type) "
                        "SELECT 'BCD-00001-26', id, client_id, client_snapshot, 1, entreprise_snapshot, 1, chantier_snapshot, 1, "
                        "'2026-10-02', '2026-03-12', total_ht, 'aucune', 'aucun' FROM devis WHERE id=?", (d,))
        self.assertEqual(self.un("SELECT statut, montant_deja_facture_ht, avancement, origine, frozen_at, completed_at, "
                                 "cancelled_at, motif_annulation, date_100_facture FROM bons_commande"),
                         ("en_cours", "0.00", "0.00", "v6", None, None, None, None, None))

    def test_INV_40_chaque_ecart_de_l_etat_de_naissance_est_refuse(self):
        ecarts = {"statut": ["termine", "annule", "bidon"], "frozen_at": [TS], "date_100_facture": ["2026-10-02"],
                  "motif_annulation": ["Motif", ""], "montant_deja_facture_ht": ["10.00", "0.0", "0"],
                  "avancement": ["50.00", "100.00", "0.0", "0"]}
        for col, valeurs in ecarts.items():
            for v in valeurs:
                with self.subTest(colonne=col, valeur=v):
                    d = self.devis_accepte()
                    self.assertIn("INV-40", self.essai_creer(d, **{col: v}) or "")
                    self.assertEqual(self.un("SELECT COUNT(*) FROM bons_commande WHERE devis_id=?", d)[0], 0)
        for col in ("statut", "montant_deja_facture_ht", "avancement"):                    # NULL : refusé aussi (NOT NULL ou trigger)
            with self.subTest(colonne=col, valeur=None):
                self.assertIsNotNone(self.essai_creer(self.devis_accepte(), **{col: None}))
        d = self.devis_accepte()                                                              # BC « annulé » complet à la naissance
        self.assertIn("INV-40", self.essai_creer(d, statut="annule", cancelled_at=TS, motif_annulation="m") or "")
        self.assertIn("INV-40", self.essai_creer(d, statut="termine", completed_at=TS, date_100_facture="2026-10-02",
                                                    frozen_at=TS, avancement="100.00", montant_deja_facture_ht="31.50") or "")

    def test_T29_completed_at_et_cancelled_at_a_la_naissance_refuses_par_les_CHECK(self):
        for kw in ({"completed_at": TS}, {"cancelled_at": TS}, {"cancelled_at": TS, "motif_annulation": "m"}):
            with self.subTest(kw=kw):
                msg = self.essai_creer(self.devis_accepte(), **kw)
                self.assertIsNotNone(msg)
                self.assertNotIn("INV-", msg.replace("INV-40", "") if "motif_annulation" in kw else msg)

    def test_INV_40_devis_non_accepte_refuse(self):
        cas = {"en_attente": {}, "refuse": {"statut": "refuse", "date_refus": "2026-03-12"},
               "annule": {"statut": "annule", "cancelled_at": TS, "motif_annulation": "m"}}
        for statut, kw in cas.items():
            with self.subTest(devis=statut):
                d = self.devis(**kw)
                self.assertIn("INV-40", self.essai_creer(d) or "")
        d = self.devis_accepte()
        self.assertIsNone(self.essai_creer(d))                                              # témoin : devis accepté
        d2 = self.devis_accepte()
        self.geler_devis(d2)
        self.assertIsNone(self.essai_creer(d2))                                             # accepté et gelé : permis

    def test_INV_48_client_du_bc_egal_client_du_devis(self):
        d = self.devis_accepte()
        autre = self.client()
        self.assertIn("INV-48", self.essai_creer(d, client_id=autre) or "")
        self.assertIsNotNone(self.essai_creer(d, client_id=None))
        self.assertIsNone(self.essai_creer(d))

    def test_INV_40_garde_du_devis_avant_celle_du_client(self):
        d = self.devis(client_id=self.client())
        self.assertIn("INV-40", self.essai_creer(d, client_id=self.client()) or "")      # devis non accepté ET client différent

    def test_INV_174_un_seul_bc_par_devis(self):
        d = self.devis_accepte()
        self.creer_bc(d)
        self.refuse_check("INSERT INTO bons_commande (numero, devis_id, client_id, client_snapshot, client_snapshot_version, "
                          "entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, "
                          "date_creation, date_acceptation, montant_contractuel_ht, remise_type, acompte_type) "
                          "SELECT 'BCD-00099-26', id, client_id, client_snapshot, 1, entreprise_snapshot, 1, chantier_snapshot, 1, "
                          "'2026-10-02', '2026-03-12', total_ht, 'aucune', 'aucun' FROM devis WHERE id=?", d)
        d2 = self.devis_accepte()
        self.assertIsNone(self.essai_creer(d2))

    def test_INV_40_creation_atomique_et_idempotente(self):
        """Le service lit le BC existant avant d'allouer un numéro ; en cas d'échec, tout est annulé (séquence comprise)."""
        d = self.devis_accepte()
        self.db.execute("BEGIN")
        b = self.creer_bc(d)
        self.db.execute("COMMIT")
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='BCD'")[0], 1)
        # seconde tentative sur le même devis : UNIQUE(devis_id), la transaction est annulée, le compteur ne bouge pas
        self.db.execute("BEGIN")
        with self.assertRaises(sqlite3.IntegrityError):
            self.creer_bc(d)
        self.db.execute("ROLLBACK")
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='BCD'")[0], 1)
        self.assertEqual(self.un("SELECT COUNT(*) FROM bons_commande")[0], 1)
        # échec au milieu de la copie des lignes : ni BC, ni lignes, ni numéro consommé
        d2 = self.devis_accepte()
        self.db.execute("BEGIN")
        try:
            b2 = self.creer_bc(d2)
            self.db.execute("INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, designation, quantite, unite, prix_unitaire_ht, "
                            "remise_type, type_prestation, total_ht) VALUES (?, 1, 9, 'x', '0', 'u', '1', 'aucune', 'pose', '1.00')", (b2,))
            self.fail("la quantité 0 aurait dû être refusée")
        except sqlite3.IntegrityError:
            self.db.execute("ROLLBACK")
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='BCD'")[0], 1)
        self.assertEqual(self.un("SELECT COUNT(*) FROM bons_commande")[0], 1)
        self.assertEqual(self.un("SELECT COUNT(*) FROM bc_lignes")[0], 2)
        self.assertEqual(self.creer_bc(d2) and self.un("SELECT numero FROM bons_commande WHERE devis_id=?", d2)[0], "BCD-00002-26")
        self.assertEqual(b, self.un("SELECT id FROM bons_commande WHERE devis_id=?", d)[0])

    def test_INV_40_devis_inexistant_refuse_par_la_cle_etrangere(self):
        d = self.devis_accepte()
        self.refuse_check("INSERT INTO bons_commande (numero, devis_id, client_id, client_snapshot, client_snapshot_version, "
                          "entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, "
                          "date_creation, date_acceptation, montant_contractuel_ht, remise_type, acompte_type) "
                          "SELECT 'BCD-00001-26', 99999, client_id, client_snapshot, 1, entreprise_snapshot, 1, chantier_snapshot, 1, "
                          "'2026-10-02', '2026-03-12', total_ht, 'aucune', 'aucun' FROM devis WHERE id=?", d)
        self.refuse_check("INSERT INTO bons_commande (numero, devis_id, client_id, client_snapshot, client_snapshot_version, "
                          "entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, "
                          "date_creation, date_acceptation, montant_contractuel_ht, remise_type, acompte_type) "
                          "SELECT 'BCD-00001-26', NULL, client_id, client_snapshot, 1, entreprise_snapshot, 1, chantier_snapshot, 1, "
                          "'2026-10-02', '2026-03-12', total_ht, 'aucune', 'aucun' FROM devis WHERE id=?", d)

    def test_INV_40_client_inexistant_refuse(self):
        d = self.devis_accepte()
        self.assertIsNotNone(self.essai_creer(d, client_id=99999))

    def test_INV_176_date_creation_et_date_acceptation_independantes(self):
        for creation, acceptation in (("2026-10-02", "2026-03-12"),      # acceptation contractuelle antérieure
                                      ("2026-03-01", "2026-03-12"),      # acceptation postérieure à l'enregistrement
                                      ("2026-03-12", "2026-03-12"),      # même jour
                                      ("2026-12-31", "2025-01-01"),      # année différente (le yy du numéro suit date_creation)
                                      ("2026-01-01", "2030-06-15")):
            with self.subTest(creation=creation, acceptation=acceptation):
                d = self.devis_accepte()
                self.db.execute("UPDATE devis SET date_acceptation=? WHERE id=?", (acceptation, d))
                b = self.creer_bc(d, date_creation=creation)
                self.assertEqual(self.un("SELECT date_creation, date_acceptation FROM bons_commande WHERE id=?", b),
                                 (creation, acceptation))
                self.assertEqual(self.un("SELECT numero FROM bons_commande WHERE id=?", b)[0][-2:], creation[2:4])
        self.assertEqual(self.ck13(), [])

    def test_INV_176_date_acceptation_obligatoire_et_reelle(self):
        d = self.devis_accepte()
        self.assertIn("NOT NULL", self.essai_creer(d, date_acceptation=None))
        for v in ("2026-02-30", "2026-13-01", "26-03-10", "2026-3-10", "", "hier", "2026-03-10T10:00:00Z"):
            with self.subTest(valeur=v):
                self.assertIsNotNone(self.essai_creer(d, date_acceptation=v))
        self.assertIsNone(self.essai_creer(d, date_acceptation="2024-02-29"))

    def test_INV_40_montant_contractuel_nul_non_refuse_par_la_base(self):
        """INV-178 : le devis à 0.00 € n'est pas acceptable (service) ; la base ne le refuse pas, CK-13 le signale."""
        d = self.devis_accepte(total_ht="0.00", lignes=0)
        b = self.creer_bc(d)
        self.assertEqual(self.ck13(), [(b, d, "contractuel_nul")])

    def test_INV_175_tr17_ne_compare_pas_le_bc_au_devis_au_dela_des_invariants_locaux(self):
        """Contractuel, remise, acompte, snapshots, date_acceptation différents du devis : acceptés par TR-17, détectés par CK-13."""
        d = self.devis_accepte()
        b = self.creer_bc(d, lignes=False, montant_contractuel_ht="99.00", remise_type="aucune", remise_valeur=None,
                          acompte_type="aucun", acompte_valeur=None, client_snapshot='{"autre": 1}', client_snapshot_version=2,
                          date_acceptation="2026-04-01")
        anomalies = {r[2] for r in self.ck13() if r[0] == b}
        self.assertEqual(anomalies, {"contractuel", "remise", "acompte", "snapshots", "date_acceptation", "ligne_manquante"})


class Numerotation(Base):
    """INV-04, INV-20 à INV-23, D-37, D-38 : numéro BCD-nnnnn-yy."""

    def test_INV_04_id_autoincrement_jamais_reutilise(self):
        bc = self.bc_en_etat("en_cours")
        l = self.ligne_bc_libre(bc)
        self.db.execute("DELETE FROM bc_lignes WHERE id=?", (l,))
        self.assertGreater(self.ligne_bc_libre(bc), l)
        g = self.un("SELECT MAX(id) FROM bc_ligne_garanties")[0]
        self.db.execute("DELETE FROM bc_ligne_garanties WHERE id=?", (g,))
        self.db.execute("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'parfait_achevement')", (bc.bl2,))
        self.assertGreater(self.un("SELECT MAX(id) FROM bc_ligne_garanties")[0], g)

    def ligne_bc_libre(self, bc):
        """Nouvelle ligne de devis (le devis accepté non gelé reste modifiable) et sa ligne de BC, ordre libre."""
        dl = self.ligne(bc.d, self.un("SELECT MAX(ordre) FROM devis_lignes WHERE devis_id=?", bc.d)[0] + 1)
        return self.ligne_bc(bc.b, dl, self.un("SELECT MAX(ordre) FROM bc_lignes WHERE bc_id=?", bc.b)[0] + 1)

    def test_INV_20_format_numero(self):
        for i, (num, date) in enumerate([("BCD-00001-26", "2026-01-01"), ("BCD-99999-26", "2026-12-31"),
                                         ("BCD-00042-27", "2027-06-15"), ("BCD-00007-99", "2099-02-28"),
                                         ("BCD-00008-01", "2001-02-28")]):
            self.assertIsNone(self.essai_creer(self.devis_accepte(), numero=num, date_creation=date), num)
        invalides = ["", "BCD-1-26", "BCD-0001-26", "BCD-000001-26", "BCD-00001-2026", "BCD-00001-6", "bcd-00001-26",
                     "BCD00001-26", "BCD-00001-26-01", "DEV-00001-26", "FAC-00001-26", "DEP-00001-26", "BCD-0000A-26",
                     "BCD-00001-26 ", " BCD-00001-26", "BCD-+0001-26", "BCD-00001-2A", "CLI-0001", "BCD-00001-26\n",
                     "BCD-00001_26", "BCD_00001-26", "BC-00001-26", "BCDD-00001-26"]
        for v in invalides:
            with self.subTest(numero=v):
                self.assertIsNotNone(self.essai_creer(self.devis_accepte(), numero=v, date_creation="2026-03-10"))

    def test_INV_20_le_format_ne_depend_pas_de_l_origine(self):
        """Le numéro BCD est exigé aussi pour un BC importé (le convertisseur génère les numéros de BC)."""
        for origine, extra in (("v6", {}), ("import", {"legacy_id": "r1", "legacy_numero": "BC-2024-17"})):
            with self.subTest(origine=origine):
                self.assertIsNone(self.essai_creer(self.devis_accepte(), origine=origine, **extra))
                self.assertIsNotNone(self.essai_creer(self.devis_accepte(), origine=origine, numero="BC-2024-17", **extra))
                self.assertIsNotNone(self.essai_creer(self.devis_accepte(), origine=origine, numero="HIST-1", **extra))

    def test_INV_20_annee_du_numero_egale_annee_de_date_creation(self):
        self.assertIsNone(self.essai_creer(self.devis_accepte(), numero="BCD-00001-26", date_creation="2026-03-10"))
        for num, date in (("BCD-00002-27", "2026-03-10"), ("BCD-00003-26", "2027-03-10"), ("BCD-00004-25", "2026-12-31"),
                          ("BCD-00005-26", "2025-12-31")):
            with self.subTest(numero=num, date_creation=date):
                self.assertIsNotNone(self.essai_creer(self.devis_accepte(), numero=num, date_creation=date))

    def test_INV_176_l_annee_du_numero_vient_de_date_creation_et_non_de_date_acceptation(self):
        d = self.devis_accepte()
        self.db.execute("UPDATE devis SET date_acceptation='2025-12-31' WHERE id=?", (d,))
        self.assertIsNotNone(self.essai_creer(d, numero="BCD-00001-25", date_creation="2026-01-02"))
        self.assertIsNone(self.essai_creer(d, numero="BCD-00001-26", date_creation="2026-01-02"))

    def test_INV_20_numero_unique(self):
        self.creer_bc(numero="BCD-00001-26", date_creation="2026-03-10")
        self.assertIn("UNIQUE", self.essai_creer(self.devis_accepte(), numero="BCD-00001-26", date_creation="2026-04-10"))
        self.assertIsNone(self.essai_creer(self.devis_accepte(), numero="BCD-00002-26", date_creation="2026-04-10"))
        self.assertIsNone(self.essai_creer(self.devis_accepte(), numero="BCD-00001-27", date_creation="2027-04-10"))   # autre année
        self.assertIn("UNIQUE", self.essai_creer(self.devis_accepte(), numero="BCD-00001-26", date_creation="2026-05-01"))

    def test_INV_23_numero_et_date_creation_immuables(self):
        for etat in ETATS_TOUS:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                self.refuse_inv("INV-23", "UPDATE bons_commande SET numero='BCD-00099-26' WHERE id=?", bc.b)
                self.refuse_inv("INV-23", "UPDATE bons_commande SET date_creation='2026-10-03' WHERE id=?", bc.b)    # même année : refusé aussi
                self.refuse_inv("INV-23", "UPDATE bons_commande SET date_creation='2027-10-02' WHERE id=?", bc.b)
                self.refuse_inv("INV-23", "UPDATE bons_commande SET numero=numero||'x', date_creation='2026-10-03' WHERE id=?", bc.b)
                self.refuse_inv("INV-23", "UPDATE bons_commande SET numero=NULL WHERE id=?", bc.b)
                self.db.execute("UPDATE bons_commande SET numero=numero, date_creation=date_creation, updated_at=? WHERE id=?",
                                (TS2, bc.b))                                                                              # valeurs identiques : permis
                self.assertEqual(self.un("SELECT updated_at FROM bons_commande WHERE id=?", bc.b)[0], TS2)

    def test_INV_21_sequence_BCD_par_annee(self):
        def creer(date):
            self.db.execute("BEGIN")
            try:
                n = self.un(ATTRIBUER, "BCD", int(date[2:4]))[0]
                self.creer_bc(self.devis_accepte(), numero=f"BCD-{n:05d}-{date[2:4]}", date_creation=date)
                self.db.execute("COMMIT")
            except Exception:
                self.db.execute("ROLLBACK")
                raise
            return f"BCD-{n:05d}-{date[2:4]}"
        self.assertEqual([creer("2026-01-05"), creer("2026-07-01"), creer("2027-01-02"), creer("2026-12-31")],
                         ["BCD-00001-26", "BCD-00002-26", "BCD-00001-27", "BCD-00003-26"])
        self.assertEqual(self.un("SELECT COUNT(*) FROM numerotation_sequences WHERE type_objet='BCD'")[0], 2)
        self.refuse(ATTRIBUER, "BCD", 0)                                # annee = 0 réservé à CLI / FOU
        self.assertEqual(self.un(ATTRIBUER, "DEV", 26)[0], 1)           # séquences indépendantes de DEV
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='BCD' AND annee=26")[0], 3)

    def test_INV_21_creation_via_le_service_attribue_le_numero_de_l_annee_de_date_creation(self):
        a = self.creer_bc(date_creation="2026-12-31")
        b = self.creer_bc(date_creation="2027-01-01")
        c = self.creer_bc(date_creation="2026-06-30")
        self.assertEqual([self.un("SELECT numero FROM bons_commande WHERE id=?", x)[0] for x in (a, b, c)],
                         ["BCD-00001-26", "BCD-00001-27", "BCD-00002-26"])

    def test_INV_22_plafond_99999_trous_autorises_et_numero_jamais_reutilise(self):
        self.db.execute("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('BCD', 26, 99997)")
        n = self.un(ATTRIBUER, "BCD", 26)[0]                           # 99998 attribué puis perdu : trou autorisé
        self.assertEqual(n, 99998)
        n = self.un(ATTRIBUER, "BCD", 26)[0]
        self.assertEqual(n, 99999)
        b = self.creer_bc(numero=f"BCD-{n:05d}-26")
        self.assertEqual(self.un("SELECT numero FROM bons_commande WHERE id=?", b)[0], "BCD-99999-26")
        with self.assertRaises(sqlite3.IntegrityError):                # dépassement : refusé (erreur métier côté service)
            self.un(ATTRIBUER, "BCD", 26)
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='BCD'")[0], 99999)
        self.refuse_inv("INV-174", "DELETE FROM bons_commande WHERE id=?", b)         # supprimer le BC est impossible : numéro jamais libéré
        self.refuse_inv("INV-22.*diminue", "UPDATE numerotation_sequences SET dernier_numero = 5 WHERE type_objet='BCD'")   # TR-95

    def test_INV_22_un_trou_de_numero_reste_apres_un_echec_de_creation(self):
        n1 = self.un(ATTRIBUER, "BCD", 26)[0]                           # attribution validée, création échouée
        self.assertIsNotNone(self.essai_creer(self.devis_accepte(), numero="BCD-00001-26", date_creation="2026-13-01"))
        b = self.creer_bc()
        self.assertEqual((n1, self.un("SELECT numero FROM bons_commande WHERE id=?", b)[0]), (1, "BCD-00002-26"))

    def test_D38_la_borne_2001_2099_n_est_pas_un_CHECK_de_la_base(self):
        """Règle de service (D-38) : la base ne limite pas les années ; seule la séquence refuse l'année 00."""
        for num, date in (("BCD-00001-01", "2001-01-01"), ("BCD-00002-99", "2099-12-31"),
                          ("BCD-00003-00", "2000-12-31"), ("BCD-00004-00", "2100-01-01"), ("BCD-00005-99", "1999-12-31"),
                          ("BCD-00006-26", "2126-03-10")):
            with self.subTest(numero=num, date_creation=date):
                self.assertIsNone(self.essai_creer(self.devis_accepte(), numero=num, date_creation=date))
        self.refuse(ATTRIBUER, "BCD", 0)                                # la séquence BCD n'existe pas pour l'année 00
        self.refuse(ATTRIBUER, "BCD", 100)
        self.assertEqual(self.un(ATTRIBUER, "BCD", 1)[0], 1)
        self.assertEqual(self.un(ATTRIBUER, "BCD", 99)[0], 1)

    def test_D38_dates_hors_numerotation_sans_borne(self):
        """date_acceptation, date_debut, date_fin, date_100_facture ne sont pas des dates de numérotation : aucune borne d'année."""
        d = self.devis_accepte()
        self.db.execute("UPDATE devis SET date_acceptation='1990-05-05' WHERE id=?", (d,))
        b = self.creer_bc(d)
        self.db.execute("UPDATE bons_commande SET date_debut='1970-01-01', date_fin='2150-12-31' WHERE id=?", (b,))
        self.assertEqual(self.un("SELECT date_acceptation, date_debut, date_fin FROM bons_commande WHERE id=?", b),
                         ("1990-05-05", "1970-01-01", "2150-12-31"))


class ContraintesBC(Base):
    def test_INV_30_snapshots_obligatoires_json_valides_et_versionnes(self):
        for col in ("client_snapshot", "entreprise_snapshot", "chantier_snapshot"):
            for v in (None, "pas du json", "", "{"):
                with self.subTest(colonne=col, valeur=v):
                    self.assertIsNotNone(self.essai_creer(self.devis_accepte(), **{col: v}))
            self.assertIsNone(self.essai_creer(self.devis_accepte(), **{col: "[]"}))
            self.assertIsNotNone(self.essai_creer(self.devis_accepte(), **{col + "_version": None}))

    def test_T29_statut_liste_fermee_avec_defaut(self):
        infos = {r[1]: r for r in self.db.execute("PRAGMA table_info(bons_commande)")}
        self.assertEqual(infos["statut"][4], "'en_cours'")
        b = self.bc_en_etat("gele").b
        for v in ("EN_COURS", "en cours", "", "refuse", "accepte", "en_attente", None):
            with self.subTest(statut=v):
                self.refuse("UPDATE bons_commande SET statut=? WHERE id=?", v, b)
        self.assertEqual(self.un("SELECT statut FROM bons_commande WHERE id=?", b)[0], "en_cours")

    def test_T29_coherence_statut_et_horodatages(self):
        """CHECK : (statut='termine') = (completed_at NN) ; termine => date_100_facture NN ; (statut='annule') = (cancelled_at NN) ;
        cancelled_at => motif non vide ; avec toutes les variantes NULL."""
        bc = self.bc_en_etat("gele")
        # termine
        self.refuse_check("UPDATE bons_commande SET statut='termine' WHERE id=?", bc.b)                         # sans completed_at
        self.refuse_check("UPDATE bons_commande SET completed_at=? WHERE id=?", TS, bc.b)                      # completed_at sans termine
        self.refuse_check("UPDATE bons_commande SET statut='termine', completed_at=? WHERE id=?", TS, bc.b)     # sans date_100_facture
        self.refuse_check("UPDATE bons_commande SET statut='termine', date_100_facture='2026-10-02', avancement='100.00' WHERE id=?", bc.b)
        self.refuse_check("UPDATE bons_commande SET statut='termine', completed_at=NULL, date_100_facture='2026-10-02', "
                          "avancement='100.00' WHERE id=?", bc.b)
        self.refuse_check("UPDATE bons_commande SET statut='en_cours', completed_at=? WHERE id=?", TS, bc.b)
        self.terminer_bc(bc.b)
        self.assertEqual(self.un("SELECT statut, avancement, montant_deja_facture_ht FROM bons_commande WHERE id=?", bc.b),
                         ("termine", "100.00", "31.50"))
        self.refuse_check("UPDATE bons_commande SET completed_at=NULL WHERE id=?", bc.b)                       # termine sans completed_at
        self.refuse_check("UPDATE bons_commande SET statut='en_cours' WHERE id=?", bc.b)                       # completed_at sans termine
        self.refuse_check("UPDATE bons_commande SET date_100_facture=NULL WHERE id=?", bc.b)                   # termine sans date_100_facture
        self.db.execute("UPDATE bons_commande SET statut='en_cours', completed_at=NULL, date_100_facture=NULL, avancement='60.00', "
                        "montant_deja_facture_ht='18.90' WHERE id=?", (bc.b,))                                  # retour_en_cours : permis (§3.5)
        # annule
        bc2 = self.bc_en_etat("en_cours")
        self.refuse_check("UPDATE bons_commande SET statut='annule' WHERE id=?", bc2.b)                         # sans cancelled_at
        self.refuse_check("UPDATE bons_commande SET cancelled_at=? WHERE id=?", TS, bc2.b)                     # cancelled_at sans annule
        self.refuse_check("UPDATE bons_commande SET statut='annule', cancelled_at=? WHERE id=?", TS, bc2.b)    # sans motif
        for motif in ("", None):
            self.refuse_check("UPDATE bons_commande SET statut='annule', cancelled_at=?, motif_annulation=? WHERE id=?", TS, motif, bc2.b)
        self.refuse_check("UPDATE bons_commande SET statut='annule', cancelled_at=NULL, motif_annulation='m' WHERE id=?", bc2.b)
        self.refuse_check("UPDATE bons_commande SET statut='en_cours', cancelled_at=?, motif_annulation='m' WHERE id=?", TS, bc2.b)
        self.db.execute("UPDATE bons_commande SET motif_annulation='note' WHERE id=?", (bc2.b,))               # motif seul : permis hors annulation
        self.annuler_bc(bc2.b)
        self.assertEqual(self.un("SELECT statut, cancelled_at IS NOT NULL FROM bons_commande WHERE id=?", bc2.b), ("annule", 1))

    def test_T29_caches_coherents_sous_garde_du_gel(self):
        """CHECK sûrs : termine => frozen_at ; date_100_facture => frozen_at ; date_100_facture => avancement = '100.00'."""
        bc = self.bc_en_etat("en_cours")                                                      # non gelé
        self.refuse_check("UPDATE bons_commande SET date_100_facture='2026-10-02', avancement='100.00' WHERE id=?", bc.b)
        self.refuse_check("UPDATE bons_commande SET statut='termine', completed_at=?, date_100_facture='2026-10-02', "
                          "avancement='100.00' WHERE id=?", TS, bc.b)
        self.geler_bc(bc.b)
        self.refuse_check("UPDATE bons_commande SET date_100_facture='2026-10-02' WHERE id=?", bc.b)           # avancement < 100
        self.refuse_check("UPDATE bons_commande SET date_100_facture='2026-10-02', avancement='99.99' WHERE id=?", bc.b)
        self.refuse_check("UPDATE bons_commande SET date_100_facture='2026-10-02', avancement='100.0' WHERE id=?", bc.b)
        self.db.execute("UPDATE bons_commande SET date_100_facture='2026-10-02', avancement='100.00' WHERE id=?", (bc.b,))  # solde actif, non terminé
        self.assertEqual(self.un("SELECT statut, date_100_facture FROM bons_commande WHERE id=?", bc.b), ("en_cours", "2026-10-02"))
        self.refuse_check("UPDATE bons_commande SET avancement='50.00' WHERE id=?", bc.b)                       # date_100_facture => 100.00
        self.db.execute("UPDATE bons_commande SET avancement='50.00', date_100_facture=NULL WHERE id=?", (bc.b,))
        # gel non réversible : frozen_at ne peut donc pas être retiré pour contourner ces CHECK
        self.refuse_inv("INV-34", "UPDATE bons_commande SET frozen_at=NULL WHERE id=?", bc.b)

    def test_T29_caches_ecrits_en_un_seul_update(self):
        """Deux UPDATE successifs peuvent passer par un état intermédiaire interdit ; un seul UPDATE est cohérent (INV-164)."""
        bc = self.bc_en_etat("gele")
        self.refuse_check("UPDATE bons_commande SET statut='termine' WHERE id=?", bc.b)                         # état intermédiaire refusé
        self.terminer_bc(bc.b)                                                                                  # même résultat en un seul UPDATE
        self.assertEqual(self.un("SELECT statut FROM bons_commande WHERE id=?", bc.b)[0], "termine")

    def test_T29_dates_debut_fin(self):
        b = self.bc_en_etat("en_cours").b
        for deb, fin, ok in (("2026-11-01", "2026-11-01", True), ("2026-11-01", "2026-11-02", True), ("2026-11-02", "2026-11-01", False),
                             ("2026-11-01", None, True), (None, "2026-11-01", True), (None, None, True),
                             ("2026-12-31", "2027-01-01", True), ("2027-01-01", "2026-12-31", False)):
            with self.subTest(debut=deb, fin=fin):
                sql = "UPDATE bons_commande SET date_debut=?, date_fin=? WHERE id=?"
                if ok:
                    self.db.execute(sql, (deb, fin, b))
                else:
                    self.refuse_check(sql, deb, fin, b)
        self.db.execute("UPDATE bons_commande SET date_debut='2026-11-01', date_fin='2026-11-10' WHERE id=?", (b,))
        self.refuse_check("UPDATE bons_commande SET date_fin='2026-10-31' WHERE id=?", b)                       # une seule colonne modifiée
        self.refuse_check("UPDATE bons_commande SET date_debut='2026-11-11' WHERE id=?", b)

    def test_INV_10_dates_reelles(self):
        d = self.devis_accepte()
        b = self.creer_bc(d)
        bg = self.bc_en_etat("gele").b                       # date_100_facture exige frozen_at et avancement = '100.00'
        for col in ("date_creation", "date_acceptation", "date_debut", "date_fin", "date_100_facture"):
            for v in ("2026-02-30", "2026-13-01", "2026-00-10", "2026-01-00", "26-03-10", "2026/03/10", "2026-3-10",
                      "2026-03-10T10:00:00Z", "", "hier", "2026-03-10 "):
                with self.subTest(colonne=col, valeur=v):
                    if col == "date_creation":
                        self.assertIsNotNone(self.essai_creer(self.devis_accepte(), numero="BCD-00001-26", date_creation=v))
                    elif col == "date_acceptation":
                        self.assertIsNotNone(self.essai_creer(self.devis_accepte(), date_acceptation=v))
                    elif col == "date_100_facture":
                        self.refuse_check("UPDATE bons_commande SET date_100_facture=?, avancement='100.00' WHERE id=?", v, bg)
                    else:
                        self.refuse("UPDATE bons_commande SET %s=? WHERE id=?" % col, v, b)
        for v in ("2024-02-29", "2026-10-02"):               # témoin : seule la date change la décision
            self.db.execute("UPDATE bons_commande SET date_100_facture=?, avancement='100.00' WHERE id=?", (v, bg))
        self.assertIsNone(self.essai_creer(self.devis_accepte(), numero="BCD-00001-24", date_creation="2024-02-29", date_acceptation="2024-02-29"))
        self.assertIsNotNone(self.essai_creer(self.devis_accepte(), numero="BCD-00002-26", date_creation="2026-02-29"))
        self.assertIsNone(self.essai_creer(self.devis_accepte(), numero="BCD-00001-28", date_creation="2028-02-29"))
        self.assertIsNotNone(self.essai_creer(self.devis_accepte(), numero="BCD-00001-00", date_creation="2100-02-29"))   # 2100 non bissextile
        self.assertIsNone(self.essai_creer(self.devis_accepte(), numero="BCD-00002-00", date_creation="2000-02-29"))      # 2000 bissextile
        for jour in ("2026-04-30", "2026-04-31"):
            self.assertEqual(self.essai_creer(self.devis_accepte(), numero=f"BCD-{jour[-2:]}001-26", date_creation=jour) is None,
                             jour == "2026-04-30")
        self.db.execute("UPDATE bons_commande SET date_debut=NULL, date_fin=NULL WHERE id=?", (b,))

    def test_INV_10_calendrier_exhaustif(self):
        """Pour chaque (année, mois 00-13, jour 00-32) la base accepte exactement les dates du calendrier grégorien."""
        import datetime
        b = self.bc_en_etat("en_cours").b
        refusees = acceptees = 0
        for annee in (1999, 2000, 2023, 2024, 2026, 2099, 2100):
            for mois in range(0, 14):
                for jour in range(0, 33):
                    v = "%04d-%02d-%02d" % (annee, mois, jour)
                    try:
                        datetime.date(annee, mois, jour)
                        attendu = True
                    except ValueError:
                        attendu = False
                    erreur = self.essai("UPDATE bons_commande SET date_debut=? WHERE id=?", v, b)
                    self.assertEqual(erreur is None, attendu, v)
                    acceptees += attendu
                    refusees += not attendu
        self.assertGreater(acceptees, 2500)
        self.assertGreater(refusees, 600)
        self.assertEqual(self.essai("UPDATE bons_commande SET date_debut='2024-02-29' WHERE id=?", b), None)
        self.assertIsNotNone(self.essai("UPDATE bons_commande SET date_debut='2023-02-29' WHERE id=?", b))

    def test_INV_14_montant_contractuel_famille_D2(self):
        valides = ["0.00", "1.00", "31.50", "999999.99", "10.10", "100.00"]
        invalides = ["", "0", "1", "1.0", "1.000", ".50", "1.", "-1.00", "+1.00", "1,00", "01.00", "00.00", "1.00.00", "1e2",
                     "abc", "1.00 ", " 1.00", "1.0a", "NaN", "Infinity", "1a.00", "1.2.50", "1.00.50"]
        for v in valides:
            with self.subTest(valide=v):
                self.assertIsNone(self.essai_creer(self.devis_accepte(), montant_contractuel_ht=v))
        for v in invalides + [None, 31.5]:
            with self.subTest(invalide=v):
                self.assertIsNotNone(self.essai_creer(self.devis_accepte(), montant_contractuel_ht=v))
        self.assertIn("STRICT", self.un("SELECT sql FROM sqlite_master WHERE name='bons_commande'")[0][-12:])

    def test_INV_14_caches_financiers_D2_et_P2(self):
        bc = self.bc_en_etat("gele")
        for v in ("0.00", "10.00", "31.50", "100000.00"):
            self.db.execute("UPDATE bons_commande SET montant_deja_facture_ht=? WHERE id=?", (v, bc.b))
        for v in ("", "0", "1.0", "-1.00", "01.00", "1.00.00", "abc", None, "1,00", "1a.00", "1.2.50", "1.00.50"):
            with self.subTest(montant_deja_facture_ht=v):
                self.refuse_check("UPDATE bons_commande SET montant_deja_facture_ht=? WHERE id=?", v, bc.b)
        for v in ("0.00", "0.01", "50.00", "99.99", "100.00"):
            self.db.execute("UPDATE bons_commande SET avancement=? WHERE id=?", (v, bc.b))
        for v in ("", "0", "100", "100.01", "101.00", "1000.00", "-0.01", "00.00", "05.00", "1.0", "99.999", "abc", None, "1e1", "1a.00", "1.2.50", "9a.00", "1.00.50"):
            with self.subTest(avancement=v):
                self.refuse_check("UPDATE bons_commande SET avancement=? WHERE id=?", v, bc.b)
        # pas de CHECK montant_deja_facture_ht <= montant_contractuel_ht (transitoirement faux, INV-46)
        self.db.execute("UPDATE bons_commande SET montant_deja_facture_ht='1000000.00' WHERE id=?", (bc.b,))
        self.assertEqual(self.un("SELECT montant_deja_facture_ht FROM bons_commande WHERE id=?", bc.b)[0], "1000000.00")

    def test_INV_14_remise_globale(self):
        for kw in ({"remise_type": "aucune", "remise_valeur": None}, {"remise_type": "pourcentage", "remise_valeur": "0.00"},
                   {"remise_type": "pourcentage", "remise_valeur": "100.00"}, {"remise_type": "pourcentage", "remise_valeur": "12.50"},
                   {"remise_type": "montant", "remise_valeur": "0.00"}, {"remise_type": "montant", "remise_valeur": "2500.00"},
                   {"remise_type": "montant", "remise_valeur": "100.01"}):
            with self.subTest(kw=kw):
                self.assertIsNone(self.essai_creer(self.devis_accepte(), **kw))
        mauvais = [{"remise_type": "aucune", "remise_valeur": "0.00"}, {"remise_type": "pourcentage", "remise_valeur": None},
                   {"remise_type": "montant", "remise_valeur": None}, {"remise_type": "pourcentage", "remise_valeur": "100.01"},
                   {"remise_type": "pourcentage", "remise_valeur": "101.00"}, {"remise_type": "pourcentage", "remise_valeur": "10"},
                   {"remise_type": "pourcentage", "remise_valeur": "10.0"}, {"remise_type": "pourcentage", "remise_valeur": "-1.00"},
                   {"remise_type": "pourcentage", "remise_valeur": "010.00"}, {"remise_type": "pourcentage", "remise_valeur": "1.00.00"},
                   {"remise_type": "pourcentage", "remise_valeur": "abc"}, {"remise_type": "montant", "remise_valeur": "5"},
                   {"remise_type": "montant", "remise_valeur": "5.5"}, {"remise_type": "montant", "remise_valeur": "-5.00"},
                   {"remise_type": "montant", "remise_valeur": "05.00"}, {"remise_type": "montant", "remise_valeur": "5.00.00"},
                   {"remise_type": "montant", "remise_valeur": "x5.00"}, {"remise_type": "bidon", "remise_valeur": "5.00"},
                   {"remise_type": "bidon", "remise_valeur": None}, {"remise_type": None, "remise_valeur": None},
                   {"remise_type": "montant", "remise_valeur": ""}]
        for kw in mauvais:
            with self.subTest(kw=kw):
                self.assertIsNotNone(self.essai_creer(self.devis_accepte(), **kw))
        # sans valeur par défaut : le service copie celle du devis
        infos = {r[1]: r for r in self.db.execute("PRAGMA table_info(bons_commande)")}
        self.assertIsNone(infos["remise_type"][4])
        self.assertIsNone(infos["acompte_type"][4])

    def test_INV_14_acompte_prevu(self):
        for kw in ({"acompte_type": "aucun", "acompte_valeur": None}, {"acompte_type": "pourcentage", "acompte_valeur": "30.00"},
                   {"acompte_type": "pourcentage", "acompte_valeur": "100.00"}, {"acompte_type": "pourcentage", "acompte_valeur": "0.00"},
                   {"acompte_type": "montant", "acompte_valeur": "500.00"}, {"acompte_type": "montant", "acompte_valeur": "100.01"}):
            with self.subTest(kw=kw):
                self.assertIsNone(self.essai_creer(self.devis_accepte(), **kw))
        mauvais = [{"acompte_type": "aucun", "acompte_valeur": "0.00"}, {"acompte_type": "pourcentage", "acompte_valeur": None},
                   {"acompte_type": "montant", "acompte_valeur": None}, {"acompte_type": "pourcentage", "acompte_valeur": "100.01"},
                   {"acompte_type": "pourcentage", "acompte_valeur": "30"}, {"acompte_type": "pourcentage", "acompte_valeur": "-1.00"},
                   {"acompte_type": "pourcentage", "acompte_valeur": "030.00"}, {"acompte_type": "pourcentage", "acompte_valeur": "1.00.00"},
                   {"acompte_type": "montant", "acompte_valeur": "500"}, {"acompte_type": "montant", "acompte_valeur": "-5.00"},
                   {"acompte_type": "montant", "acompte_valeur": "05.00"}, {"acompte_type": "montant", "acompte_valeur": "5.00.00"},
                   {"acompte_type": "montant", "acompte_valeur": "x5.00"}, {"acompte_type": "bidon", "acompte_valeur": "5.00"},
                   {"acompte_type": None, "acompte_valeur": None}, {"acompte_type": "montant", "acompte_valeur": ""}]
        for kw in mauvais:
            with self.subTest(kw=kw):
                self.assertIsNotNone(self.essai_creer(self.devis_accepte(), **kw))

    def test_INV_136_bloc_imp_plus(self):
        b = self.creer_bc()
        self.assertEqual(self.un("SELECT origine, legacy_id, legacy_data, legacy_numero FROM bons_commande WHERE id=?", b),
                         ("v6", None, None, None))
        for kw in ({"legacy_id": "x"}, {"legacy_data": "{}"}, {"legacy_numero": "BC-1"},
                   {"legacy_id": "x", "legacy_data": "{}", "legacy_numero": "BC-1"}):
            with self.subTest(origine="v6", kw=kw):
                self.assertIsNotNone(self.essai_creer(self.devis_accepte(), origine="v6", **kw))
        self.assertIsNotNone(self.essai_creer(self.devis_accepte(), origine="migration"))
        self.assertIsNotNone(self.essai_creer(self.devis_accepte(), origine=None))
        self.assertIsNotNone(self.essai_creer(self.devis_accepte(), origine="import", legacy_data="pas du json"))
        self.assertIsNone(self.essai_creer(self.devis_accepte(), origine="import"))                              # tout facultatif
        self.assertIsNone(self.essai_creer(self.devis_accepte(), origine="import", legacy_id="ref-4",
                                           legacy_data='{"statut_v2": "Envoyé"}', legacy_numero="BC-2024-17"))
        # legacy_numero NULL ou différent de numero (INV-136)
        d = self.devis_accepte()
        self.assertIsNotNone(self.essai_creer(d, origine="import", numero="BCD-00077-26", legacy_numero="BCD-00077-26"))
        self.assertIsNone(self.essai_creer(d, origine="import", numero="BCD-00077-26", legacy_numero="BCD-00078-26"))
        for t in ("bc_lignes", "bc_ligne_garanties"):                                                          # pas de traçabilité sur les lignes
            self.assertFalse({r[1] for r in self.db.execute(f"PRAGMA table_info({t})")} & {"origine", "legacy_id", "legacy_data"})
        self.assertFalse({r[1] for r in self.db.execute("PRAGMA table_info(bons_commande)")} & {"migration_id", "active"})

    def test_INV_136_import_ne_contourne_aucun_trigger(self):
        """Les triggers ne sont exemptés pour aucune origine (INV-131)."""
        d = self.devis_accepte()
        self.assertIn("INV-40", self.essai_creer(d, origine="import", legacy_id="r", statut="annule", cancelled_at=TS, motif_annulation="m") or "")
        b = self.creer_bc(self.devis_accepte(), origine="import", legacy_id="r1", legacy_numero="BC-17")
        self.refuse_inv("INV-23", "UPDATE bons_commande SET numero='BCD-00099-26' WHERE id=?", b)
        self.refuse_inv("INV-174", "DELETE FROM bons_commande WHERE id=?", b)

    def test_INV_10_horodatages(self):
        b = self.creer_bc()
        c, u = self.un("SELECT created_at, updated_at FROM bons_commande WHERE id=?", b)
        self.assertRegex(c, TS_GLOB)
        self.assertRegex(u, TS_GLOB)
        for col in ("created_at", "updated_at"):
            for v in ("2026-10-01", "2026-10-01 10:00:00", "2026-10-01T10:00:00Z", "2026-10-01T10:00:00.00Z", "now", "", None):
                with self.subTest(colonne=col, valeur=v):
                    self.assertIsNotNone(self.essai_creer(self.devis_accepte(), **{col: v}))
        self.assertIsNone(self.essai_creer(self.devis_accepte(), created_at=TS, updated_at=TS2))
        bc = self.bc_en_etat("gele")
        for col in ("cancelled_at", "completed_at", "frozen_at"):
            for v in ("2026-10-01", "2026-10-01 10:00:00", "2026-10-01T10:00:00Z", "2026-10-01T10:00:00.00Z", "now", ""):
                with self.subTest(colonne=col, valeur=v):
                    extra = {"cancelled_at": ", statut='annule', motif_annulation='m'",
                             "completed_at": ", statut='termine', date_100_facture='2026-10-02', avancement='100.00'",
                             "frozen_at": ""}[col]
                    sql = f"UPDATE bons_commande SET {col}=?{extra} WHERE id=?"
                    if col == "frozen_at":
                        bc2 = self.bc_en_etat("en_cours")
                        self.refuse(sql, v, bc2.b)
                    else:
                        self.refuse(sql, v, bc.b)
        self.refuse_check("UPDATE bons_commande SET updated_at='2026-10-01' WHERE id=?", b)
        self.db.execute("UPDATE bons_commande SET updated_at=? WHERE id=?", (TS2, b))

    def test_T29_horodatages_par_defaut_sont_l_instant_courant(self):
        for t, extra in (("bons_commande", None), ("bc_lignes", None), ("bc_ligne_garanties", None)):
            for col in ("created_at", "updated_at"):
                if t == "bc_ligne_garanties" and col == "updated_at":
                    continue
                defaut = {r[1]: r[4] for r in self.db.execute(f"PRAGMA table_info({t})")}[col]
                self.assertEqual(defaut, "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')", (t, col))
        bc = self.bc_en_etat("en_cours")
        for t, id_ in (("bons_commande", bc.b), ("bc_lignes", bc.bl1), ("bc_ligne_garanties", bc.bg1)):
            ecart = self.un(f"SELECT ABS(strftime('%s', 'now') - strftime('%s', created_at)) FROM {t} WHERE id=?", id_)[0]
            self.assertLess(ecart, 5, t)

    def test_T29_listes_fermees_exactes(self):
        sql = self.un("SELECT sql FROM sqlite_master WHERE name='bons_commande'")[0]
        self.assertEqual(sorted(re.search(r"statut IN \(([^)]*)\)", sql).group(1).replace("'", "").replace(" ", "").split(",")),
                         ["annule", "en_cours", "termine"])
        self.assertEqual(sorted(re.search(r"origine IN \(([^)]*)\)", sql).group(1).replace("'", "").replace(" ", "").split(",")),
                         ["import", "v6"])
        self.assertEqual(sorted(re.search(r"remise_type IN \(([^)]*)\)", sql).group(1).replace("'", "").replace(" ", "").split(",")),
                         ["aucune", "montant", "pourcentage"])
        self.assertEqual(sorted(re.search(r"acompte_type IN \(([^)]*)\)", sql).group(1).replace("'", "").replace(" ", "").split(",")),
                         ["aucun", "montant", "pourcentage"])
        sl = self.un("SELECT sql FROM sqlite_master WHERE name='bc_lignes'")[0]
        self.assertEqual(sorted(re.search(r"unite IN \(([^)]*)\)", sl).group(1).replace("'", "").replace(" ", "").split(",")),
                         ["ens", "m2", "m3", "ml", "u"])
        self.assertEqual(sorted(re.search(r"type_prestation IN \(([^)]*)\)", sl).group(1).replace("'", "").replace(" ", "").split(",")),
                         ["fourniture", "fourniture_pose", "pose"])
        sg = self.un("SELECT sql FROM sqlite_master WHERE name='bc_ligne_garanties'")[0]
        self.assertEqual(sorted(re.search(r"garantie_type IN \(([^)]*)\)", sg).group(1).replace("'", "").replace(" ", "").split(",")),
                         ["biennale", "decennale", "parfait_achevement"])


class LignesBC(Base):
    """INV-38, INV-168, INV-175 : lignes de BC (copie 1:1 des lignes du devis), UNIQUE(devis_ligne_id), TR-13."""

    def essai_ligne(self, b, dl, ordre, **kw):
        try:
            self.ligne_bc(b, dl, ordre, **kw)
            return None
        except sqlite3.IntegrityError as e:
            return str(e)

    def bc_vide(self, nb=3):
        """BC sans lignes, devis accepté non gelé portant nb lignes de devis disponibles : retourne (d, b, [dl…])."""
        d = self.devis_accepte(lignes=0)
        dls = [self.ligne(d, i) for i in range(1, nb + 1)]
        return d, self.creer_bc(d, lignes=False), dls

    def test_T29_ligne_nominale_catalogue_et_ligne_libre(self):
        d, b, dls = self.bc_vide()
        p = self.prestation("ELE-001")
        self.db.execute("UPDATE devis_lignes SET prestation_id=?, reference_prestation='ELE-001', description='Détail' WHERE id=?", (p, dls[0]))
        l1 = self.ligne_bc(b, dls[0], 1)
        l2 = self.ligne_bc(b, dls[1], 2)
        self.assertEqual(self.un("SELECT prestation_id, reference_prestation, description, designation FROM bc_lignes WHERE id=?", l1),
                         (p, "ELE-001", "Détail", "Pose prise"))
        self.assertEqual(self.un("SELECT prestation_id, reference_prestation FROM bc_lignes WHERE id=?", l2), (None, None))   # ligne libre
        self.assertRegex(self.un("SELECT created_at FROM bc_lignes WHERE id=?", l1)[0], TS_GLOB)
        self.assertEqual(self.ck13()[0][2:], ("ligne_manquante",))                                  # la 3e ligne du devis n'est pas encore copiée
        self.ligne_bc(b, dls[2], 3)
        self.assertEqual(self.ck13(), [])

    def test_T29_ordre_et_unicite(self):
        d, b, dls = self.bc_vide(4)
        for ordre in (0, -1, None, "a", 1.5):
            with self.subTest(ordre=ordre):
                self.assertIsNotNone(self.essai_ligne(b, dls[0], ordre))
        self.ligne_bc(b, dls[0], 1)
        msg = self.essai_ligne(b, dls[1], 1)                                      # même (bc_id, ordre)
        self.assertIn("UNIQUE", msg)
        self.assertNotIn("INV-", msg)
        self.assertIsNone(self.essai_ligne(b, dls[1], 2))
        d2, b2, dls2 = self.bc_vide(1)
        self.assertIsNone(self.essai_ligne(b2, dls2[0], 1))                       # même ordre dans un autre BC : permis
        self.assertIsNone(self.essai_ligne(b, dls[2], 10 ** 6))

    def test_INV_168_UNIQUE_devis_ligne_id(self):
        d, b, dls = self.bc_vide(2)
        self.ligne_bc(b, dls[0], 1)
        msg = self.essai_ligne(b, dls[0], 2)                                      # même ligne de devis, autre ordre, même BC
        self.assertIn("UNIQUE", msg)
        self.assertIn("devis_ligne_id", msg)
        self.assertNotIn("INV-", msg)
        self.assertEqual(self.un("SELECT COUNT(*) FROM bc_lignes")[0], 1)
        # UPDATE : une ligne de BC ne peut pas pointer vers une ligne de devis déjà utilisée
        l2 = self.ligne_bc(b, dls[1], 2)
        self.refuse_check("UPDATE bc_lignes SET devis_ligne_id=? WHERE id=?", dls[0], l2)
        # le même devis_ligne_id ne peut appartenir à deux BC : le second BC est refusé par TR-13 (ligne d'un autre devis)
        d2 = self.devis_accepte(lignes=0)
        b2 = self.creer_bc(d2, lignes=False)
        self.refuse_inv("INV-175", "INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, designation, quantite, unite, prix_unitaire_ht, "
                        "remise_type, type_prestation, total_ht) VALUES (?, ?, 1, 'x', '1', 'u', '1', 'aucune', 'pose', '1.00')", b2, dls[0])

    def test_INV_175_la_ligne_de_devis_appartient_au_devis_du_bc(self):
        d, b, dls = self.bc_vide(1)
        autre = self.devis_accepte(lignes=0)
        dl_autre = self.ligne(autre, 1)                                            # devis sans BC
        self.refuse_inv("INV-175", "INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, designation, quantite, unite, prix_unitaire_ht, "
                        "remise_type, type_prestation, total_ht) VALUES (?, ?, 1, 'x', '1', 'u', '1', 'aucune', 'pose', '1.00')", b, dl_autre)
        autre_bc = self.creer_bc(autre, lignes=False)                              # devis avec son propre BC
        self.refuse_inv("INV-175", "INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, designation, quantite, unite, prix_unitaire_ht, "
                        "remise_type, type_prestation, total_ht) VALUES (?, ?, 1, 'x', '1', 'u', '1', 'aucune', 'pose', '1.00')", b, dl_autre)
        l = self.ligne_bc(b, dls[0], 1)
        l_autre = self.ligne_bc(autre_bc, dl_autre, 1)
        self.refuse_inv("INV-175", "UPDATE bc_lignes SET devis_ligne_id=? WHERE id=?", dl_autre, l)           # UPDATE : même garde
        self.refuse_inv("INV-175", "UPDATE bc_lignes SET bc_id=? WHERE id=?", autre_bc, l)                    # déplacer vers un BC d'un autre devis
        self.refuse_inv("INV-175", "UPDATE bc_lignes SET bc_id=?, ordre=2 WHERE id=?", b, l_autre)
        self.assertEqual(self.un("SELECT bc_id, devis_ligne_id FROM bc_lignes WHERE id=?", l), (b, dls[0]))
        # remplacer par une autre ligne du même devis : permis (régénération)
        nouvelle = self.ligne(d, 2)
        self.db.execute("UPDATE bc_lignes SET devis_ligne_id=? WHERE id=?", (nouvelle, l))
        self.assertEqual(self.un("SELECT devis_ligne_id FROM bc_lignes WHERE id=?", l)[0], nouvelle)

    def test_INV_175_bc_ou_ligne_de_devis_inexistants_refuses_par_la_cle_etrangere(self):
        d, b, dls = self.bc_vide(1)
        base = ("INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, designation, quantite, unite, prix_unitaire_ht, "
                "remise_type, type_prestation, total_ht) VALUES (?, ?, 1, 'x', '1', 'u', '1', 'aucune', 'pose', '1.00')")
        self.refuse_check(base, 99999, dls[0])
        self.refuse_check(base, b, 99999)
        self.refuse_check(base, b, None)
        self.refuse_check(base, None, dls[0])
        l = self.ligne_bc(b, dls[0], 1)
        self.refuse_check("UPDATE bc_lignes SET devis_ligne_id=99999 WHERE id=?", l)
        self.refuse_check("UPDATE bc_lignes SET bc_id=99999 WHERE id=?", l)
        self.refuse_check("UPDATE bc_lignes SET prestation_id=99999 WHERE id=?", l)
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_T29_designation_obligatoire_non_vide(self):
        d, b, dls = self.bc_vide(1)
        for v in ("", None):
            self.assertIsNotNone(self.essai_ligne(b, dls[0], 1, designation=v))
        self.assertIsNone(self.essai_ligne(b, dls[0], 1, designation=" "))

    def test_INV_14_quantite_DL_strictement_positive(self):
        d, b, dls = self.bc_vide(1)
        for v in ("1", "2", "0.5", "10.25", "1.001", "100", "3.14159", "10", "0.1", "1000000"):
            with self.subTest(valide=v):
                self.db.execute("SAVEPOINT s")
                self.assertIsNone(self.essai_ligne(b, dls[0], 1, quantite=v))
                self.db.execute("ROLLBACK TO s")
                self.db.execute("RELEASE s")
        for v in ("0", "0.0", "0.00", "-1", "", "1.", ".5", "1.50", "01", "00.5", "1.2.3", "1e2", "abc", "1,5", " 1", "1 ", None):
            with self.subTest(invalide=v):
                self.assertIsNotNone(self.essai_ligne(b, dls[0], 1, quantite=v))

    def test_INV_14_prix_unitaire_DL(self):
        d, b, dls = self.bc_vide(1)
        for v in ("0", "10", "10.5", "10.25", "0.001", "1234.5678", "100"):
            with self.subTest(valide=v):
                self.db.execute("SAVEPOINT s")
                self.assertIsNone(self.essai_ligne(b, dls[0], 1, prix_unitaire_ht=v))
                self.db.execute("ROLLBACK TO s")
                self.db.execute("RELEASE s")
        for v in ("", "-1", "1.", ".5", "10.50", "010", "00.5", "1.2.3", "1e2", "abc", "1,5", " 1", None):
            with self.subTest(invalide=v):
                self.assertIsNotNone(self.essai_ligne(b, dls[0], 1, prix_unitaire_ht=v))

    def test_INV_14_total_ht_ligne_D2(self):
        d, b, dls = self.bc_vide(1)
        for v in ("0.00", "21.00", "0.01", "999999.99", "10.10"):
            with self.subTest(valide=v):
                self.db.execute("SAVEPOINT s")
                self.assertIsNone(self.essai_ligne(b, dls[0], 1, total_ht=v))
                self.db.execute("ROLLBACK TO s")
                self.db.execute("RELEASE s")
        for v in ("", "0", "21", "21.0", "21.000", ".50", "1.", "-1.00", "01.00", "00.00", "1.00.00", "abc", "1,00", None, 21.0, "1a.00", "1.2.50", "1.00.50"):
            with self.subTest(invalide=v):
                self.assertIsNotNone(self.essai_ligne(b, dls[0], 1, total_ht=v))

    def test_INV_14_remise_de_ligne(self):
        d, b, dls = self.bc_vide(1)
        valides = [("aucune", None), ("pourcentage", "0.00"), ("pourcentage", "100.00"), ("pourcentage", "12.50"),
                   ("montant", "5"), ("montant", "5.5"), ("montant", "12.75"), ("montant", "0"), ("montant", "1234.5678")]
        invalides = [("aucune", "0.00"), ("pourcentage", None), ("montant", None), ("pourcentage", "100.01"),
                     ("pourcentage", "10"), ("pourcentage", "10.0"), ("pourcentage", "-1.00"), ("pourcentage", "010.00"),
                     ("pourcentage", "abc"), ("montant", ""), ("montant", "-5"), ("montant", "5."), ("montant", ".5"),
                     ("montant", "5.50"), ("montant", "05"), ("montant", "5.5.5"), ("montant", "x"), ("bidon", "5.00"),
                     ("bidon", None), (None, None), ("montant", "1e2"), ("zzz", "5.00"), ("zzz", None), ("", None), ("", "5.00")]
        for t, v in valides:
            with self.subTest(valide=(t, v)):
                self.db.execute("SAVEPOINT s")
                self.assertIsNone(self.essai_ligne(b, dls[0], 1, remise_type=t, remise_valeur=v))
                self.db.execute("ROLLBACK TO s")
                self.db.execute("RELEASE s")
        for t, v in invalides:
            with self.subTest(invalide=(t, v)):
                self.assertIsNotNone(self.essai_ligne(b, dls[0], 1, remise_type=t, remise_valeur=v))

    def test_T29_listes_fermees_ligne(self):
        d, b, dls = self.bc_vide(1)
        for col, bons, mauvais in (("unite", ("u", "ens", "ml", "m2", "m3"), ("", "kg", "U", "m²", None)),
                                   ("type_prestation", ("fourniture", "pose", "fourniture_pose"), ("", "service", "Pose", None))):
            for v in bons:
                with self.subTest(colonne=col, valide=v):
                    self.db.execute("SAVEPOINT s")
                    self.assertIsNone(self.essai_ligne(b, dls[0], 1, **{col: v}))
                    self.db.execute("ROLLBACK TO s")
                    self.db.execute("RELEASE s")
            for v in mauvais:
                with self.subTest(colonne=col, invalide=v):
                    self.assertIsNotNone(self.essai_ligne(b, dls[0], 1, **{col: v}))

    def test_INV_10_horodatages_ligne(self):
        d, b, dls = self.bc_vide(1)
        for col in ("created_at", "updated_at"):
            for v in ("2026-10-01", "2026-10-01 10:00:00", "2026-10-01T10:00:00Z", "2026-10-01T10:00:00.00Z", "now", "", None):
                with self.subTest(colonne=col, valeur=v):
                    self.assertIsNotNone(self.essai_ligne(b, dls[0], 1, **{col: v}))
        self.assertIsNone(self.essai_ligne(b, dls[0], 1, created_at=TS, updated_at=TS2))

    def test_INV_36_lignes_modifiables_tant_que_le_bc_ne_l_est_pas_fige(self):
        bc = self.bc_en_etat("en_cours", dl3=True)
        l3 = self.ligne_bc(bc.b, bc.dl3, 3)                                       # INSERT
        self.db.execute("UPDATE bc_lignes SET designation='Nouvelle', quantite='4', total_ht='42.00', updated_at=? WHERE id=?", (TS2, l3))
        self.db.execute("UPDATE bc_lignes SET ordre=7 WHERE id=?", (l3,))
        self.db.execute("DELETE FROM bc_lignes WHERE id=?", (l3,))
        self.assertEqual(self.un("SELECT COUNT(*) FROM bc_lignes WHERE bc_id=?", bc.b)[0], 2)

    def test_INV_36_lignes_interdites_si_le_bc_est_gele_ou_annule(self):
        for etat in ETATS_FIGES:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat, dl3=True)
                avant = self.tous("SELECT * FROM bc_lignes ORDER BY id")
                self.refuse_inv("INV-36", "INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, designation, quantite, unite, "
                                "prix_unitaire_ht, remise_type, type_prestation, total_ht) "
                                "VALUES (?, ?, 3, 'x', '1', 'u', '1', 'aucune', 'pose', '1.00')", bc.b, bc.dl3)
                self.refuse_inv("INV-36", "UPDATE bc_lignes SET designation='x' WHERE id=?", bc.bl1)
                self.refuse_inv("INV-36", "UPDATE bc_lignes SET updated_at=? WHERE id=?", TS2, bc.bl1)
                self.refuse_inv("INV-36", "UPDATE bc_lignes SET quantite='9' WHERE id=?", bc.bl2)
                self.refuse_inv("INV-36", "DELETE FROM bc_lignes WHERE id=?", bc.bl1)
                self.refuse_inv("INV-36", "DELETE FROM bc_lignes WHERE bc_id=?", bc.b)
                self.assertEqual(self.tous("SELECT * FROM bc_lignes ORDER BY id"), avant)

    def test_INV_36_deplacer_une_ligne_entre_bc(self):
        """UPDATE bc_id : le côté ancien ET le côté nouveau sont gardés."""
        a = self.bc_en_etat("gele")
        b = self.bc_en_etat("en_cours")
        self.refuse_inv("INV-36", "UPDATE bc_lignes SET bc_id=?, ordre=9 WHERE id=?", b.b, a.bl1)             # depuis un BC gelé
        self.refuse_inv("INV-36", "UPDATE bc_lignes SET bc_id=?, ordre=9 WHERE id=?", a.b, b.bl1)             # vers un BC gelé
        for etat in ("annule", "termine", "annule_gele"):
            with self.subTest(etat=etat):
                f = self.bc_en_etat(etat)
                self.refuse_inv("INV-36", "UPDATE bc_lignes SET bc_id=?, ordre=9 WHERE id=?", b.b, f.bl1)
                self.refuse_inv("INV-36", "UPDATE bc_lignes SET bc_id=?, ordre=9 WHERE id=?", f.b, b.bl1)
        self.assertEqual(self.un("SELECT bc_id FROM bc_lignes WHERE id=?", b.bl1)[0], b.b)

    def test_T29_regeneration_des_lignes_avant_gel(self):
        """Ordre du modèle (§4.7) : supprimer bc_lignes -> modifier devis et devis_lignes -> recopier -> mettre à jour le BC."""
        bc = self.bc_en_etat("en_cours")
        self.refuse_check("DELETE FROM devis_lignes WHERE id=?", bc.dl1)                                       # RESTRICT : BC non régénéré
        self.db.execute("DELETE FROM bc_lignes WHERE bc_id=?", (bc.b,))                                         # garanties en CASCADE
        self.assertEqual(self.un("SELECT COUNT(*) FROM bc_ligne_garanties")[0], 0)
        self.db.execute("DELETE FROM devis_lignes WHERE id=?", (bc.dl2,))
        self.db.execute("UPDATE devis_lignes SET designation='Modifiée', total_ht='30.00' WHERE id=?", (bc.dl1,))
        self.ligne(bc.d, 2, designation="Nouvelle ligne", total_ht="1.50")
        self.db.execute("UPDATE devis SET total_ht='31.50' WHERE id=?", (bc.d,))
        self.copier_lignes(bc.b)
        self.assertEqual(self.tous("SELECT ordre, designation FROM bc_lignes WHERE bc_id=? ORDER BY ordre", bc.b),
                         [(1, "Modifiée"), (2, "Nouvelle ligne")])
        self.assertEqual(self.un("SELECT COUNT(*) FROM bc_ligne_garanties")[0], 2)
        self.assertEqual(self.ck13(), [])

    def test_INV_168_ligne_de_devis_non_supprimable_tant_qu_une_ligne_de_bc_la_reference(self):
        bc = self.bc_en_etat("en_cours")
        self.refuse_check("DELETE FROM devis_lignes WHERE id=?", bc.dl1)
        self.refuse_check("DELETE FROM devis_lignes WHERE devis_id=?", bc.d)
        self.refuse_check("UPDATE devis_lignes SET id=99999 WHERE id=?", bc.dl1)
        self.assertEqual(self.un("SELECT COUNT(*) FROM devis_lignes WHERE devis_id=?", bc.d)[0], 2)

    def test_T29_index_prestation_id_utilise(self):
        bc = self.bc_en_etat("en_cours")
        plan = " ".join(str(r) for r in self.db.execute("EXPLAIN QUERY PLAN SELECT id FROM bc_lignes WHERE prestation_id = ?", (1,)))
        self.assertIn("idx_bc_lignes_prestation_id", plan)
        plan = " ".join(str(r) for r in self.db.execute("EXPLAIN QUERY PLAN SELECT id FROM bons_commande WHERE client_id = ?", (1,)))
        self.assertIn("idx_bons_commande_client_id", plan)
        plan = " ".join(str(r) for r in self.db.execute("EXPLAIN QUERY PLAN SELECT id FROM bons_commande WHERE statut = ?", ("en_cours",)))
        self.assertIn("idx_bons_commande_statut", plan)
        plan = " ".join(str(r) for r in self.db.execute("EXPLAIN QUERY PLAN SELECT id FROM bc_lignes WHERE devis_ligne_id = ?", (1,)))
        self.assertIn("sqlite_autoindex_bc_lignes", plan)                                                       # index de UNIQUE(devis_ligne_id)

    def test_INV_06_prestation_utilisee_par_une_ligne_de_bc_ne_se_supprime_pas(self):
        bc = self.bc_en_etat("en_cours")
        p = self.un("SELECT prestation_id FROM bc_lignes WHERE id=?", bc.bl1)[0]
        self.refuse_check("DELETE FROM prestations WHERE id=?", p)
        self.db.execute("DELETE FROM bc_lignes WHERE id=?", (bc.bl1,))
        self.refuse_check("DELETE FROM prestations WHERE id=?", p)                                             # la ligne de devis la référence encore
        self.db.execute("DELETE FROM devis_lignes WHERE id=?", (bc.dl1,))
        self.db.execute("DELETE FROM prestations WHERE id=?", (p,))

    def test_INV_37_le_catalogue_ne_modifie_jamais_une_ligne_de_bc(self):
        bc = self.bc_en_etat("en_cours")
        p = self.un("SELECT prestation_id FROM bc_lignes WHERE id=?", bc.bl1)[0]
        avant = self.tous("SELECT * FROM bc_lignes ORDER BY id")
        self.db.execute("UPDATE prestations SET designation='Autre', prix_unitaire_ht='99', unite='m2', actif=0 WHERE id=?", (p,))
        self.db.execute("INSERT INTO prestation_garanties (prestation_id, garantie_type) VALUES (?, 'parfait_achevement')", (p,))
        self.assertEqual(self.tous("SELECT * FROM bc_lignes ORDER BY id"), avant)
        self.assertEqual(self.ck13(), [])


class GarantiesBC(Base):
    """INV-36, INV-37, INV-134, TR-13 : garanties de ligne snapshotées au niveau du BC."""

    def test_T29_garanties_de_ligne(self):
        bc = self.bc_en_etat("en_cours")
        self.assertEqual(self.tous("SELECT garantie_type FROM bc_ligne_garanties WHERE ligne_id=? ORDER BY garantie_type", bc.bl1),
                         [("biennale",), ("decennale",)])
        self.assertEqual(self.un("SELECT COUNT(*) FROM bc_ligne_garanties WHERE ligne_id=?", bc.bl2)[0], 0)
        self.assertRegex(self.un("SELECT created_at FROM bc_ligne_garanties WHERE id=?", bc.bg1)[0], TS_GLOB)
        msg = self.essai("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'decennale')", bc.bl1)   # UNIQUE(ligne_id, type)
        self.assertIn("UNIQUE", msg)
        self.assertNotIn("INV-", msg)
        self.db.execute("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'decennale')", (bc.bl2,))   # même type, autre ligne
        for v in ("", "decennal", "DECENNALE", "garantie", "10 ans", None):
            with self.subTest(garantie_type=v):
                self.refuse_check("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, ?)", bc.bl2, v)
        for v in ("parfait_achevement", "biennale"):
            self.db.execute("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, ?)", (bc.bl2, v))
        self.refuse_check("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (NULL, 'decennale')")
        self.refuse_check("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (99999, 'decennale')")     # FK
        for v in ("2026-10-01", "2026-10-01T10:00:00Z", "now", "", None, "2026-10-01T10:00:00.000", "2026-10-01 10:00:00.000Z"):
            with self.subTest(created_at=v):                  # type libre sur bl1 : seul created_at peut motiver le refus
                self.refuse_check("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type, created_at) VALUES (?, 'parfait_achevement', ?)", bc.bl1, v)
        self.db.execute("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type, created_at) VALUES (?, 'parfait_achevement', ?)", (bc.bl1, TS))
        self.assertEqual(self.ck13()[0][2:], ("garantie_en_trop",))                           # garanties de plus que le devis (INSERT directs)

    def test_INV_36_garanties_modifiables_si_le_bc_est_modifiable(self):
        bc = self.bc_en_etat("en_cours")
        self.db.execute("UPDATE bc_ligne_garanties SET garantie_type='parfait_achevement' WHERE id=?", (bc.bg1,))
        self.db.execute("UPDATE bc_ligne_garanties SET ligne_id=? WHERE id=?", (bc.bl2, bc.bg1))                     # d'une ligne à l'autre
        self.db.execute("DELETE FROM bc_ligne_garanties WHERE id=?", (bc.bg1,))
        self.db.execute("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'decennale')", (bc.bl2,))

    def test_INV_36_garanties_interdites_si_le_bc_est_gele_ou_annule(self):
        for etat in ETATS_FIGES:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                avant = self.tous("SELECT * FROM bc_ligne_garanties ORDER BY id")
                self.refuse_inv("INV-36", "INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'parfait_achevement')", bc.bl1)
                self.refuse_inv("INV-36", "INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'decennale')", bc.bl2)
                self.refuse_inv("INV-36", "UPDATE bc_ligne_garanties SET garantie_type='parfait_achevement' WHERE id=?", bc.bg1)
                self.refuse_inv("INV-36", "UPDATE bc_ligne_garanties SET ligne_id=? WHERE id=?", bc.bl2, bc.bg1)
                self.refuse_inv("INV-36", "DELETE FROM bc_ligne_garanties WHERE id=?", bc.bg1)
                self.refuse_inv("INV-36", "DELETE FROM bc_ligne_garanties WHERE ligne_id=?", bc.bl1)
                self.assertEqual(self.tous("SELECT * FROM bc_ligne_garanties ORDER BY id"), avant)

    def test_INV_36_deplacer_une_garantie_entre_bc(self):
        """UPDATE ligne_id : l'ancienne ligne ET la nouvelle sont gardées."""
        gele = self.bc_en_etat("gele")
        libre = self.bc_en_etat("en_cours")
        self.refuse_inv("INV-36", "UPDATE bc_ligne_garanties SET ligne_id=? WHERE id=?", libre.bl2, gele.bg1)      # depuis un BC gelé
        self.refuse_inv("INV-36", "UPDATE bc_ligne_garanties SET ligne_id=? WHERE id=?", gele.bl2, libre.bg1)      # vers un BC gelé
        for etat in ("annule", "termine", "annule_gele"):
            with self.subTest(etat=etat):
                f = self.bc_en_etat(etat)
                self.refuse_inv("INV-36", "UPDATE bc_ligne_garanties SET ligne_id=? WHERE id=?", libre.bl2, f.bg1)
                self.refuse_inv("INV-36", "UPDATE bc_ligne_garanties SET ligne_id=? WHERE id=?", f.bl2, libre.bg1)
        self.db.execute("UPDATE bc_ligne_garanties SET ligne_id=? WHERE id=?", (libre.bl2, libre.bg1))            # entre lignes d'un BC modifiable

    def test_INV_05_cascade_ligne_vers_garanties_seulement(self):
        bc = self.bc_en_etat("en_cours")
        self.db.execute("DELETE FROM bc_lignes WHERE id=?", (bc.bl1,))
        self.assertEqual(self.un("SELECT COUNT(*) FROM bc_ligne_garanties")[0], 0)                                 # CASCADE
        self.assertEqual(self.un("SELECT COUNT(*) FROM bons_commande WHERE id=?", bc.b)[0], 1)
        self.assertEqual(self.un("SELECT COUNT(*) FROM devis_ligne_garanties")[0], 2)                              # le devis n'est pas touché
        actions = {(r[2], r[6]) for t in TABLES_004 for r in self.db.execute(f"PRAGMA foreign_key_list({t})")}
        self.assertEqual({a for a in actions if a[1] == "CASCADE"}, {("bc_lignes", "CASCADE")})

    def test_INV_36_la_cascade_ne_contourne_pas_la_garde_des_lignes(self):
        """Lors d'un CASCADE la ligne parente est déjà supprimée : la garde est tr_13_bc_lignes_delete (ligne gelée/annulée)."""
        for etat in ETATS_FIGES:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                self.refuse_inv("INV-36", "DELETE FROM bc_lignes WHERE id=?", bc.bl1)
                self.assertEqual(self.un("SELECT COUNT(*) FROM bc_ligne_garanties WHERE ligne_id=?", bc.bl1)[0], 2)

    def test_INV_37_le_catalogue_ne_modifie_jamais_les_garanties_du_bc(self):
        bc = self.bc_en_etat("en_cours")
        p = self.un("SELECT prestation_id FROM bc_lignes WHERE id=?", bc.bl1)[0]
        self.db.execute("INSERT INTO prestation_garanties (prestation_id, garantie_type) VALUES (?, 'parfait_achevement')", (p,))
        self.db.execute("DELETE FROM prestation_garanties WHERE prestation_id=?", (p,))
        self.db.execute("UPDATE prestations SET actif=0 WHERE id=?", (p,))
        self.assertEqual(self.tous("SELECT garantie_type FROM bc_ligne_garanties WHERE ligne_id=? ORDER BY 1", bc.bl1),
                         [("biennale",), ("decennale",)])
        self.assertEqual(self.ck13(), [])

    def test_INV_134_un_bc_importe_n_a_aucune_garantie_de_ligne(self):
        d = self.devis_accepte(lignes=1)
        self.db.execute("DELETE FROM devis_ligne_garanties")                                                     # le contrat n'importe aucune garantie
        b = self.creer_bc(d, origine="import", legacy_id="r1")
        self.assertEqual(self.un("SELECT COUNT(*) FROM bc_ligne_garanties")[0], 0)
        self.assertEqual(self.ck13(), [])


# Autre valeur pour chaque colonne de bons_commande, utilisée pour vérifier que TR-12 couvre TOUTES les colonnes.
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


COLONNES_GELE_MODIFIABLES = {"montant_deja_facture_ht", "avancement", "date_100_facture", "statut", "completed_at", "date_debut",
                             "date_fin", "cancelled_at", "motif_annulation", "client_id", "updated_at"}
COLONNES_ANNULE_MODIFIABLES = {"client_id", "updated_at"}


class CycleDeVie(Base):
    """INV-31, INV-34, INV-36, INV-49, INV-173 : états du BC, gel, annulation terminale, liste blanche du modèle §7.2."""

    def _bc(self, etat, rattachable=False):
        """(bc, client_cible) ; l'ancien client est 'a_rattacher' si demandé."""
        ancien = self.client(statut="a_rattacher") if rattachable else self.client()
        cible = self.client()
        return self.bc_en_etat(etat, client_id=ancien), cible

    def test_T29_TR12_toutes_les_colonnes_sont_couvertes(self):
        self.assertEqual([r[1] for r in self.db.execute("PRAGMA table_info(bons_commande)")], COLONNES_BC)
        bc, cible = self._bc("gele")
        ligne = self.un("SELECT * FROM bons_commande WHERE id=?", bc.b)
        for col, ancienne in zip(COLONNES_BC, ligne):
            autre_valeur_bc(col, ancienne, cible)        # lève KeyError si une colonne n'a pas de valeur de test

    def test_INV_36_bc_modifiable_tout_sauf_les_colonnes_immuables(self):
        modifs = ["client_snapshot='{\"a\": 1}'", "client_snapshot_version=7", "entreprise_snapshot='{\"a\": 1}'",
                  "entreprise_snapshot_version=7", "chantier_snapshot='{\"a\": 1}'", "chantier_snapshot_version=7",
                  "date_acceptation='2026-04-01'", "date_debut='2026-11-01'", "date_fin='2026-11-30'",
                  "montant_contractuel_ht='99.00'", "remise_type='montant', remise_valeur='3.00'", "remise_valeur='20.00'",
                  "acompte_type='pourcentage', acompte_valeur='30.00'", "acompte_valeur='7.00'", "montant_deja_facture_ht='10.00'",
                  "avancement='10.00'", "updated_at='%s'" % TS2, "origine='import'", "origine='import', legacy_id='x'",
                  "origine='import', legacy_data='{}'", "origine='import', legacy_numero='BC-1'", "frozen_at='%s'" % TS,
                  "client_id=%d"]
        bc, cible = self._bc("en_cours")
        for m in modifs:
            with self.subTest(modif=m):
                self.db.execute("SAVEPOINT s")
                self.db.execute(f"UPDATE bons_commande SET {m % cible if '%d' in m else m} WHERE id=?", (bc.b,))
                self.db.execute("ROLLBACK TO s")
                self.db.execute("RELEASE s")
        ligne = self.un("SELECT * FROM bons_commande WHERE id=?", bc.b)
        for col, ancienne in zip(COLONNES_BC, ligne):
            if col in ("id", "devis_id", "created_at"):
                with self.subTest(colonne=col):
                    self.refuse_inv("INV-36", f"UPDATE bons_commande SET {col}=? WHERE id=?", autre_valeur_bc(col, ancienne, cible), bc.b)
            elif col in ("numero", "date_creation"):
                with self.subTest(colonne=col):
                    self.refuse_inv("INV-23", f"UPDATE bons_commande SET {col}=? WHERE id=?", autre_valeur_bc(col, ancienne, cible), bc.b)
        self.assertEqual(self.un("SELECT * FROM bons_commande WHERE id=?", bc.b), ligne)

    def test_INV_36_id_devis_id_created_at_gardes_pendant_une_transition_d_etat(self):
        bc, _ = self._bc("en_cours")
        self.refuse_inv("INV-36", "UPDATE bons_commande SET statut='annule', cancelled_at=?, motif_annulation='m', "
                        "created_at='2020-01-01T00:00:00.000Z' WHERE id=?", TS, bc.b)
        self.refuse_inv("INV-36", "UPDATE bons_commande SET frozen_at=?, devis_id=? WHERE id=?", TS, self.devis_accepte(), bc.b)
        self.refuse_inv("INV-36", "UPDATE bons_commande SET frozen_at=?, id=? WHERE id=?", TS, 5555, bc.b)
        self.annuler_bc(bc.b)                                                                                  # transition seule : permise

    def test_INV_36_bc_gele_ou_termine_liste_blanche_colonne_par_colonne(self):
        for etat in ("gele", "termine"):
            bc, cible = self._bc(etat, rattachable=False)
            ligne = self.un("SELECT * FROM bons_commande WHERE id=?", bc.b)
            for col, ancienne in zip(COLONNES_BC, ligne):
                if col in COLONNES_GELE_MODIFIABLES:
                    continue
                with self.subTest(etat=etat, colonne=col):
                    self.refuse_inv("INV-23|INV-34|INV-36", f"UPDATE bons_commande SET {col}=? WHERE id=?",
                                    autre_valeur_bc(col, ancienne, cible), bc.b)
            self.refuse_inv("INV-36", "UPDATE bons_commande SET client_id=? WHERE id=?", cible, bc.b)          # ancien client non 'a_rattacher'
            self.assertEqual(self.un("SELECT * FROM bons_commande WHERE id=?", bc.b), ligne)                   # rien n'a bougé
            for m in ("montant_contractuel_ht='1.00', avancement='20.00'", "avancement='20.00', remise_valeur='1.00'",
                      "date_debut='2026-11-01', numero='BCD-00099-26'", "date_fin='2026-11-02', origine='import'",
                      "statut=statut, devis_id=%d" % self.devis_accepte()):
                with self.subTest(etat=etat, melange=m):
                    self.refuse(f"UPDATE bons_commande SET {m} WHERE id=?", bc.b)                              # autorisée + interdite : refusé

    def test_INV_36_bc_gele_colonnes_autorisees(self):
        bc, cible = self._bc("gele")
        autorisees = ["montant_deja_facture_ht='10.00'", "avancement='50.00'", "date_100_facture='2026-10-02', avancement='100.00'",
                      "date_debut='2026-11-01'", "date_fin='2026-11-30'", "date_debut='2026-11-01', date_fin='2026-11-30'",
                      "updated_at='%s'" % TS2,
                      "statut='termine', completed_at='%s', date_100_facture='2026-10-02', avancement='100.00'" % TS,
                      "statut='annule', cancelled_at='%s', motif_annulation='Client renonce'" % TS]
        for m in autorisees:
            with self.subTest(modif=m):
                self.db.execute("SAVEPOINT s")
                self.db.execute(f"UPDATE bons_commande SET {m} WHERE id=?", (bc.b,))
                self.db.execute("ROLLBACK TO s")
                self.db.execute("RELEASE s")
        self.terminer_bc(bc.b)
        self.db.execute("UPDATE bons_commande SET statut='en_cours', completed_at=NULL, date_100_facture=NULL, avancement='60.00', "
                        "montant_deja_facture_ht='18.90' WHERE id=?", (bc.b,))                                  # retour_en_cours
        self.assertEqual(self.un("SELECT statut, frozen_at IS NOT NULL FROM bons_commande WHERE id=?", bc.b), ("en_cours", 1))
        self.annuler_bc(bc.b)                                                                                   # annulation d'un BC gelé
        self.assertEqual(self.un("SELECT statut, frozen_at IS NOT NULL, cancelled_at IS NOT NULL FROM bons_commande WHERE id=?", bc.b),
                         ("annule", 1, 1))

    def test_INV_173_bc_annule_terminal_colonne_par_colonne(self):
        for etat in ("annule", "annule_gele"):
            bc, cible = self._bc(etat)
            ligne = self.un("SELECT * FROM bons_commande WHERE id=?", bc.b)
            for col, ancienne in zip(COLONNES_BC, ligne):
                if col in COLONNES_ANNULE_MODIFIABLES:
                    continue
                with self.subTest(etat=etat, colonne=col):
                    self.refuse_inv("INV-23|INV-34|INV-173", f"UPDATE bons_commande SET {col}=? WHERE id=?",
                                    autre_valeur_bc(col, ancienne, cible), bc.b)
            self.refuse_inv("INV-173", "UPDATE bons_commande SET client_id=? WHERE id=?", cible, bc.b)         # client non 'a_rattacher'
            self.assertEqual(self.un("SELECT * FROM bons_commande WHERE id=?", bc.b), ligne)
            self.db.execute("UPDATE bons_commande SET updated_at=? WHERE id=?", (TS2, bc.b))                   # seule colonne libre

    def test_INV_173_un_bc_annule_ne_redevient_jamais_actif(self):
        for etat in ("annule", "annule_gele"):
            bc, _ = self._bc(etat)
            with self.subTest(etat=etat):
                self.refuse_inv("INV-173", "UPDATE bons_commande SET statut='en_cours', cancelled_at=NULL, motif_annulation=NULL WHERE id=?", bc.b)
                self.refuse_inv("INV-173", "UPDATE bons_commande SET statut='termine', cancelled_at=NULL, motif_annulation=NULL, completed_at=?, "
                                "date_100_facture='2026-10-02', avancement='100.00', frozen_at=? WHERE id=?", TS, TS, bc.b)
                self.refuse_inv("INV-173", "UPDATE bons_commande SET cancelled_at=NULL WHERE id=?", bc.b)
                self.refuse_inv("INV-173", "UPDATE bons_commande SET motif_annulation='Autre' WHERE id=?", bc.b)
                self.refuse_inv("INV-173", "UPDATE bons_commande SET statut='annule' , cancelled_at=? WHERE id=?", TS2, bc.b)    # même statut, autre date
                self.refuse_inv("INV-173", "UPDATE bons_commande SET date_debut='2026-11-01' WHERE id=?", bc.b)
                self.refuse_inv("INV-173", "UPDATE bons_commande SET montant_deja_facture_ht='1.00' WHERE id=?", bc.b)

    def test_INV_173_un_bc_annule_ne_se_gele_pas(self):
        bc, _ = self._bc("annule")
        self.refuse_inv("INV-173", "UPDATE bons_commande SET frozen_at=? WHERE id=?", TS, bc.b)

    def test_INV_49_rattachement_du_client(self):
        for etat in ETATS_TOUS:
            for statut_ancien in ("a_rattacher", "actif", "archive"):
                with self.subTest(etat=etat, ancien_client=statut_ancien):
                    ancien = self.client(statut=statut_ancien)
                    cible = self.client()
                    bc = self.bc_en_etat(etat, client_id=ancien)
                    avant = self.un("SELECT * FROM bons_commande WHERE id=?", bc.b)
                    sql = "UPDATE bons_commande SET client_id=?, updated_at=? WHERE id=?"
                    if etat == "en_cours" or statut_ancien == "a_rattacher":
                        self.db.execute(sql, (cible, TS2, bc.b))
                        apres = self.un("SELECT * FROM bons_commande WHERE id=?", bc.b)
                        changees = [c for c, a, b in zip(COLONNES_BC, avant, apres) if a != b]
                        self.assertEqual(sorted(changees), ["client_id", "updated_at"])
                    else:
                        self.refuse_inv("INV-36|INV-173", sql, cible, TS2, bc.b)
                        self.assertEqual(self.un("SELECT * FROM bons_commande WHERE id=?", bc.b), avant)
        for etat in ("gele", "annule", "annule_gele", "termine"):                                                # rattachement + autre modification
            with self.subTest(etat=etat, melange=True):
                bc = self.bc_en_etat(etat, client_id=self.client(statut="a_rattacher"))
                self.refuse_inv("INV-36|INV-173", "UPDATE bons_commande SET client_id=?, montant_contractuel_ht='1.00' WHERE id=?",
                                self.client(), bc.b)
                self.refuse_inv("INV-36|INV-173", "UPDATE bons_commande SET client_id=?, client_snapshot='{}' WHERE id=?", self.client(), bc.b)
        bc = self.bc_en_etat("gele", client_id=self.client(statut="a_rattacher"))
        self.refuse_check("UPDATE bons_commande SET client_id=NULL WHERE id=?", bc.b)
        self.refuse_check("UPDATE bons_commande SET client_id=99999 WHERE id=?", bc.b)

    def test_INV_34_frozen_at_ne_revient_jamais_a_null(self):
        bc, _ = self._bc("en_cours")
        self.db.execute("UPDATE bons_commande SET frozen_at=? WHERE id=?", (TS, bc.b))                         # NULL -> valeur (pose du gel)
        self.refuse_inv("INV-34", "UPDATE bons_commande SET frozen_at=NULL WHERE id=?", bc.b)
        self.refuse_inv("INV-34", "UPDATE bons_commande SET frozen_at=? WHERE id=?", TS2, bc.b)                # pas de modification de la valeur
        self.db.execute("UPDATE bons_commande SET frozen_at=frozen_at, updated_at=? WHERE id=?", (TS2, bc.b))  # valeur identique : permis
        self.assertEqual(self.un("SELECT frozen_at FROM bons_commande WHERE id=?", bc.b)[0], TS)
        for v in ("2026-10-01", "2026-10-01T10:00:00Z", "now", ""):
            bc2, _ = self._bc("en_cours")
            self.refuse("UPDATE bons_commande SET frozen_at=? WHERE id=?", v, bc2.b)                           # format TS
        bc3, _ = self._bc("termine")
        self.refuse_inv("INV-34", "UPDATE bons_commande SET frozen_at=NULL WHERE id=?", bc3.b)

    def test_INV_34_le_gel_permet_les_caches_et_l_annulation_ne_degele_pas(self):
        bc, _ = self._bc("gele")
        self.annuler_bc(bc.b)
        self.assertEqual(self.un("SELECT frozen_at FROM bons_commande WHERE id=?", bc.b)[0], TS)
        bc2, _ = self._bc("annule_gele")
        self.refuse_inv("INV-34|INV-173", "UPDATE bons_commande SET frozen_at=NULL WHERE id=?", bc2.b)

    def test_INV_31_bc_non_gele_peut_etre_gele_et_annule_dans_le_meme_update(self):
        bc, _ = self._bc("en_cours")
        self.db.execute("UPDATE bons_commande SET frozen_at=?, statut='annule', cancelled_at=?, motif_annulation='m', updated_at=? WHERE id=?",
                        (TS, TS, TS, bc.b))
        self.assertEqual(self.un("SELECT statut, frozen_at FROM bons_commande WHERE id=?", bc.b), ("annule", TS))

    def test_T29_termine_demande_le_gel(self):
        bc, _ = self._bc("en_cours")
        self.refuse_check("UPDATE bons_commande SET statut='termine', completed_at=?, date_100_facture='2026-10-02', avancement='100.00' "
                          "WHERE id=?", TS, bc.b)
        self.geler_bc(bc.b)
        self.terminer_bc(bc.b)

    def test_T29_termine_sans_solde_nul_non_controle_ici(self):
        """BC terminé = solde actif + sommes dues = 0 (hors avoirs) : mécanique de la Facturation, aucune table ici."""
        bc, _ = self._bc("gele")
        self.db.execute("UPDATE bons_commande SET statut='termine', completed_at=?, date_100_facture='2026-10-02', avancement='100.00', "
                        "montant_deja_facture_ht='0.00' WHERE id=?", (TS, bc.b))
        self.assertEqual(self.un("SELECT statut FROM bons_commande WHERE id=?", bc.b)[0], "termine")
        tables = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertFalse(tables & {"factures", "facture_lignes", "reglements"})

    def test_T29_les_triggers_ne_modifient_aucune_donnee(self):
        bc = self.bc_en_etat("en_cours")
        avant = {t: self.db.execute(f"SELECT * FROM {t} ORDER BY id").fetchall()
                 for t in TABLES_001 | TABLES_002 | TABLES_003 | TABLES_004}
        self.db.execute("UPDATE bons_commande SET date_debut='2026-11-01' WHERE id=?", (bc.b,))
        self.db.execute("UPDATE bc_lignes SET designation='y' WHERE id=?", (bc.bl1,))
        self.db.execute("UPDATE bc_ligne_garanties SET garantie_type='parfait_achevement' WHERE id=?", (bc.bg1,))
        apres = {t: self.db.execute(f"SELECT * FROM {t} ORDER BY id").fetchall() for t in avant}
        self.assertEqual(sorted(t for t in avant if avant[t] != apres[t]), ["bc_ligne_garanties", "bc_lignes", "bons_commande"])

    def test_INV_36_pose_du_gel_avec_autres_modifications_dans_le_meme_UPDATE(self):
        """La règle de TR-12 se lit sur l'ÉTAT D'ORIGINE : tant que OLD.frozen_at est NULL, la pose du gel (NULL -> valeur,
        TR-14/TR-15) peut accompagner n'importe quelle modification ; une fois gelé, la liste blanche s'applique."""
        bc = self.bc_en_etat("en_cours")
        self.db.execute("UPDATE bons_commande SET frozen_at=?, montant_contractuel_ht='40.00', remise_type='aucune', "
                        "remise_valeur=NULL WHERE id=?", (TS, bc.b))
        self.assertEqual(self.un("SELECT montant_contractuel_ht, frozen_at FROM bons_commande WHERE id=?", bc.b), ("40.00", TS))
        self.refuse_inv("INV-36", "UPDATE bons_commande SET montant_contractuel_ht='41.00' WHERE id=?", bc.b)

    def test_INV_36_annulation_d_un_BC_gele_ne_modifie_que_les_colonnes_de_la_liste_blanche(self):
        """L'annulation d'un BC gelé est jugée sur l'état d'origine (gelé, non annulé) : elle n'ouvre pas la porte
        à une modification d'une colonne hors liste blanche dans le même UPDATE."""
        for colonne in ("montant_contractuel_ht='1.00'", "date_acceptation='2020-01-01'", "acompte_valeur='7.00'"):
            with self.subTest(colonne=colonne):
                bc = self.bc_en_etat("gele")
                self.refuse_inv("INV-36", "UPDATE bons_commande SET statut='annule', cancelled_at=?, motif_annulation='Motif', "
                                          + colonne + " WHERE id=?", TS, bc.b)
                self.annuler_bc(bc.b)
                self.assertEqual(self.un("SELECT statut FROM bons_commande WHERE id=?", bc.b)[0], "annule")


class DevisEtBC(Base):
    """INV-175 : TR-18 (le devis ne quitte accepte que si son BC est annulé) et CK-13 (diagnostic devis <-> BC)."""

    SORTIES = {"annule": "UPDATE devis SET statut='annule', cancelled_at='%s', motif_annulation='m' WHERE id=?" % TS,
               "refuse": "UPDATE devis SET statut='refuse', date_refus='2026-04-01' WHERE id=?",
               "en_attente": "UPDATE devis SET statut='en_attente' WHERE id=?"}

    def test_INV_175_un_devis_ayant_un_bc_non_annule_ne_quitte_pas_accepte(self):
        for etat in ("en_cours", "gele", "termine"):
            bc = self.bc_en_etat(etat)
            for cible, sql in self.SORTIES.items():
                with self.subTest(bc=etat, sortie=cible):
                    self.refuse_inv("INV-175", sql, bc.d)
                    self.assertEqual(self.un("SELECT statut FROM devis WHERE id=?", bc.d)[0], "accepte")

    def test_INV_175_un_devis_dont_le_bc_est_annule_peut_quitter_accepte(self):
        for etat in ("annule", "annule_gele"):
            for cible, sql in self.SORTIES.items():
                if cible == "en_attente" or (cible == "refuse" and etat == "annule_gele"):
                    continue                    # 003 : un devis accepté gelé ne revient pas en attente et ne se refuse pas
                with self.subTest(bc=etat, sortie=cible):
                    bc = self.bc_en_etat(etat)
                    self.db.execute(sql, (bc.d,))
                    self.assertEqual(self.un("SELECT statut FROM devis WHERE id=?", bc.d)[0], cible)
        bc = self.bc_en_etat("annule")
        self.db.execute(self.SORTIES["en_attente"], (bc.d,))                       # BC annulé, devis non gelé : retour en attente permis
        self.assertEqual(self.un("SELECT statut FROM devis WHERE id=?", bc.d)[0], "en_attente")

    def test_INV_175_ordre_de_l_annulation_bc_puis_devis_dans_une_transaction(self):
        bc = self.bc_en_etat("gele")
        self.db.execute("BEGIN")
        self.refuse_inv("INV-175", self.SORTIES["annule"], bc.d)                    # devis d'abord : refusé
        self.annuler_bc(bc.b)
        self.db.execute(self.SORTIES["annule"], (bc.d,))                            # BC puis devis : permis
        self.db.execute("COMMIT")
        self.assertEqual(self.ck13(), [])
        self.assertEqual(self.un("SELECT statut FROM bons_commande WHERE id=?", bc.b)[0], "annule")

    def test_INV_175_TR18_ne_gene_ni_les_autres_colonnes_ni_les_devis_sans_bc(self):
        bc = self.bc_en_etat("gele")
        self.db.execute("UPDATE devis SET statut='accepte', updated_at=? WHERE id=?", (TS2, bc.d))            # même statut
        d = self.devis_accepte()
        for cible, sql in self.SORTIES.items():
            with self.subTest(devis_sans_bc=cible):
                d = self.devis_accepte()
                self.db.execute(sql, (d,))
                self.assertEqual(self.un("SELECT statut FROM devis WHERE id=?", d)[0], cible)
        d2 = self.devis()                                                                                    # en_attente -> accepte -> en_attente
        self.accepter(d2)
        self.db.execute("UPDATE devis SET statut='en_attente' WHERE id=?", (d2,))
        d3 = self.devis_accepte()
        b3 = self.creer_bc(d3)
        self.db.execute("UPDATE devis SET objet='Nouvel objet', notes='n' WHERE id=?", (d3,))                  # devis modifiable avec BC

    def test_INV_174_le_devis_d_un_bc_ne_se_supprime_jamais(self):
        for etat in ETATS_TOUS:
            with self.subTest(bc=etat):
                bc = self.bc_en_etat(etat)
                if etat.startswith("annule"):
                    self.annuler_devis(bc.d)
                self.refuse_check("DELETE FROM devis WHERE id=?", bc.d)
                self.assertEqual(self.un("SELECT COUNT(*) FROM devis WHERE id=?", bc.d)[0], 1)
        d, l, g = self.devis_complet_sans_bc()
        self.db.execute("DELETE FROM devis WHERE id=?", (d,))                                                 # sans BC : supprimé en CASCADE
        self.assertEqual(self.un("SELECT COUNT(*) FROM devis_lignes WHERE devis_id=?", d)[0], 0)

    def devis_complet_sans_bc(self):
        d = self.devis()
        l = self.ligne(d)
        g = self.garantie(l)
        self.accepter(d)
        return d, l, g

    # --- CK-13 ----------------------------------------------------------------
    def test_INV_175_CK13_vide_sur_donnees_coherentes(self):
        self.assertEqual(self.ck13(), [])
        for etat in ETATS_TOUS:
            self.bc_en_etat(etat)
        for b, d in self.tous("SELECT id, devis_id FROM bons_commande WHERE statut='annule'"):
            self.annuler_devis(d)                                                                             # annulation BC puis devis
        self.assertEqual(self.ck13(), [])

    def divergence(self, modif, attendu, etat="en_cours"):
        """Applique modif (sql, args) sur un BC cohérent ; CK-13 doit signaler exactement `attendu` pour ce BC."""
        bc = self.bc_en_etat(etat)
        self.assertEqual([r for r in self.ck13() if r[0] == bc.b], [])
        sql, args = modif(bc)
        self.db.execute(sql, args)
        return bc, sorted({r[2] for r in self.ck13() if r[0] == bc.b})

    def test_INV_175_CK13_detecte_chaque_divergence_de_la_liste_S_cote_bc(self):
        cas = {
            "client_id": ("UPDATE bons_commande SET client_id=? WHERE id=?", lambda bc: (self.client(), bc.b)),
            "contractuel": ("UPDATE bons_commande SET montant_contractuel_ht='99.00' WHERE id=?", lambda bc: (bc.b,)),
            "remise": ("UPDATE bons_commande SET remise_valeur='11.00' WHERE id=?", lambda bc: (bc.b,)),
            "remise ": ("UPDATE bons_commande SET remise_type='montant' WHERE id=?", lambda bc: (bc.b,)),
            "acompte": ("UPDATE bons_commande SET acompte_valeur='6.00' WHERE id=?", lambda bc: (bc.b,)),
            "acompte ": ("UPDATE bons_commande SET acompte_type='pourcentage', acompte_valeur='5.00' WHERE id=?", lambda bc: (bc.b,)),
            "snapshots": ("UPDATE bons_commande SET client_snapshot='{\"autre\": 1}' WHERE id=?", lambda bc: (bc.b,)),
            "snapshots ": ("UPDATE bons_commande SET client_snapshot_version=2 WHERE id=?", lambda bc: (bc.b,)),
            "snapshots  ": ("UPDATE bons_commande SET entreprise_snapshot='{\"autre\": 1}' WHERE id=?", lambda bc: (bc.b,)),
            "snapshots   ": ("UPDATE bons_commande SET entreprise_snapshot_version=2 WHERE id=?", lambda bc: (bc.b,)),
            "snapshots    ": ("UPDATE bons_commande SET chantier_snapshot='{\"autre\": 1}' WHERE id=?", lambda bc: (bc.b,)),
            "snapshots     ": ("UPDATE bons_commande SET chantier_snapshot_version=2 WHERE id=?", lambda bc: (bc.b,)),
            "date_acceptation": ("UPDATE bons_commande SET date_acceptation='2026-04-01' WHERE id=?", lambda bc: (bc.b,)),
            "ligne_manquante": ("DELETE FROM bc_lignes WHERE id=?", lambda bc: (bc.bl2,)),
            "garantie_manquante": ("DELETE FROM bc_ligne_garanties WHERE id=?", lambda bc: (bc.bg1,)),
            "garantie_en_trop": ("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'parfait_achevement')", lambda bc: (bc.bl1,)),
        }
        for nom, (sql, args) in cas.items():
            with self.subTest(divergence=nom.strip()):
                bc, trouve = self.divergence(lambda b: (sql, args(b)), None)
                self.assertEqual(trouve, [nom.strip()])

    def test_INV_175_CK13_detecte_une_ligne_de_bc_differente_champ_par_champ(self):
        champs = {"ordre": "9", "prestation_id": "NULL", "reference_prestation": "'AUTRE'", "designation": "'Autre'",
                  "description": "'Autre'", "quantite": "'7'", "unite": "'m2'", "prix_unitaire_ht": "'7'", "remise_type": "'montant'",
                  "remise_valeur": "'1'", "type_prestation": "'fourniture'", "total_ht": "'7.00'"}
        for champ, valeur in champs.items():
            with self.subTest(champ=champ):
                bc = self.bc_en_etat("en_cours")
                cible = bc.bl1
                if champ in ("remise_type", "remise_valeur"):             # remise identique des deux côtés, puis un seul champ diffère
                    self.db.execute("UPDATE devis_lignes SET remise_type='montant', remise_valeur='12.34' WHERE id=?", (bc.dl1,))
                    self.db.execute("UPDATE bc_lignes SET remise_type='montant', remise_valeur='12.34' WHERE id=?", (cible,))
                    self.assertEqual([r for r in self.ck13() if r[0] == bc.b], [])
                    if champ == "remise_type":
                        self.db.execute("UPDATE bc_lignes SET remise_type='pourcentage' WHERE id=?", (cible,))
                    else:
                        self.db.execute("UPDATE bc_lignes SET remise_valeur='12.35' WHERE id=?", (cible,))
                else:
                    self.db.execute(f"UPDATE bc_lignes SET {champ}={valeur} WHERE id=?", (cible,))
                self.assertEqual({r[2] for r in self.ck13() if r[0] == bc.b}, {"ligne_differente"})

    def test_INV_175_CK13_detecte_une_modification_du_devis_non_repercutee(self):
        """Le devis reste le seul point d'édition : une modification de son côté sans régénération du BC est détectée."""
        modifs = {"contractuel": "UPDATE devis SET total_ht='40.00' WHERE id=?",
                  "remise": "UPDATE devis SET remise_valeur='15.00' WHERE id=?",
                  "acompte": "UPDATE devis SET acompte_valeur='9.00' WHERE id=?",
                  "snapshots": "UPDATE devis SET chantier_snapshot_version=3 WHERE id=?",
                  "date_acceptation": "UPDATE devis SET date_acceptation='2026-03-30' WHERE id=?",
                  "client_id": "UPDATE devis SET client_id=(SELECT MAX(id) FROM clients) WHERE id=?"}
        for nom, sql in modifs.items():
            with self.subTest(divergence=nom):
                bc = self.bc_en_etat("en_cours")
                self.client()
                self.db.execute(sql, (bc.d,))
                self.assertEqual({r[2] for r in self.ck13() if r[0] == bc.b}, {nom})
        bc = self.bc_en_etat("en_cours")
        self.db.execute("UPDATE devis_lignes SET designation='Modifiée' WHERE id=?", (bc.dl1,))
        self.assertEqual({r[2] for r in self.ck13() if r[0] == bc.b}, {"ligne_differente"})
        bc = self.bc_en_etat("en_cours")
        self.ligne(bc.d, 3, designation="Ajoutée")
        self.assertEqual({r[2] for r in self.ck13() if r[0] == bc.b}, {"ligne_manquante"})
        bc = self.bc_en_etat("en_cours")
        self.garantie(bc.dl2, "decennale")
        self.assertEqual({r[2] for r in self.ck13() if r[0] == bc.b}, {"garantie_manquante"})

    def test_INV_175_CK13_statuts_et_contractuel_nul(self):
        d = self.devis_accepte()                                                                              # devis accepté sans BC
        self.assertEqual(self.ck13(), [(None, d, "devis_accepte_sans_bc")])
        b = self.creer_bc(d)
        self.assertEqual(self.ck13(), [])
        self.annuler_bc(b)                                                                                    # BC annulé, devis encore accepté
        self.assertEqual(self.ck13(), [(b, d, "bc_annule_devis_non_annule")])
        self.annuler_devis(d)
        self.assertEqual(self.ck13(), [])
        d2 = self.devis_accepte(total_ht="0.00", lignes=0)
        b2 = self.creer_bc(d2)
        self.assertEqual(self.ck13(), [(b2, d2, "contractuel_nul")])

    def test_INV_175_CK13_un_bc_annule_est_exclu_de_la_comparaison_du_miroir(self):
        bc = self.bc_en_etat("annule")
        self.db.execute("UPDATE devis SET total_ht='1.00', remise_valeur='1.00', date_acceptation='2026-01-01', "
                        "client_snapshot_version=9 WHERE id=?", (bc.d,))
        self.db.execute("UPDATE devis_lignes SET designation='Autre' WHERE id=?", (bc.dl1,))
        self.assertEqual(self.ck13(), [(bc.b, bc.d, "bc_annule_devis_non_annule")])

    def test_INV_175_CK13_devis_annule_dont_le_bc_n_est_pas_annule(self):
        """État interdit par TR-18 en fonctionnement normal ; il ne subsiste que dans une base altérée (restauration)."""
        bc = self.bc_en_etat("gele")
        autre = migrer()
        autre.execute("DROP TRIGGER tr_18_devis_statut_avec_bc")
        t = Base(); t.db = autre; t._n = 0
        bc = t.bc_en_etat("gele")
        autre.execute(self.SORTIES["annule"], (bc.d,))
        self.assertEqual(t.ck13(), [(bc.b, bc.d, "devis_annule_bc_non_annule")])

    def test_INV_175_CK13_ligne_de_bc_d_un_autre_devis(self):
        """TR-13 interdit cet état ; il ne subsiste que dans une base altérée (restauration)."""
        autre = migrer()
        autre.execute("DROP TRIGGER tr_13_bc_lignes_insert")
        t = Base(); t.db = autre; t._n = 0
        bc = t.bc_en_etat("en_cours")
        d2 = t.devis_accepte(lignes=0)
        dl = t.ligne(d2, 1)
        t.ligne_bc(bc.b, dl, 9)
        self.assertEqual(sorted(t.ck13(), key=str), sorted([(bc.b, bc.d, "ligne_en_trop"), (None, d2, "devis_accepte_sans_bc")], key=str))

    def test_INV_175_CK13_est_en_lecture_seule(self):
        for etat in ETATS_TOUS:
            self.bc_en_etat(etat)
        self.db.execute("UPDATE bons_commande SET montant_contractuel_ht='1.00' WHERE statut='en_cours' AND frozen_at IS NULL")
        avant = {t: self.tous(f"SELECT * FROM {t} ORDER BY 1") for t in TABLES_003 | TABLES_004 | {"clients", "numerotation_sequences"}}
        self.assertNotEqual(self.ck13(), [])
        self.assertEqual({t: self.tous(f"SELECT * FROM {t} ORDER BY 1") for t in avant}, avant)
        self.assertNotRegex(CK13, r"(?i)\b(INSERT|UPDATE|DELETE|REPLACE|DROP|ALTER)\b")

    def test_INV_48_rattachement_cote_devis_et_cote_bc_dans_la_meme_transaction(self):
        ancien = self.client(statut="a_rattacher")
        cible = self.client()
        bc = self.bc_en_etat("gele", client_id=ancien)
        self.db.execute("BEGIN")
        self.db.execute("UPDATE devis SET client_id=?, updated_at=? WHERE id=?", (cible, TS2, bc.d))
        self.assertEqual([r[2] for r in self.ck13()], ["client_id"])                                           # état intermédiaire
        self.db.execute("UPDATE bons_commande SET client_id=?, updated_at=? WHERE id=?", (cible, TS2, bc.b))
        self.db.execute("COMMIT")
        self.assertEqual(self.ck13(), [])

    def test_T29_import_d_un_bc_historique_annule_par_les_etapes_normales(self):
        """Modèle §10.5 : devis en_attente + lignes -> accepte -> BC en_cours + lignes -> BC annulé -> devis annulé."""
        d = self.devis(numero="HIST-12", origine="import", legacy_id="r12", total_ht="31.50")
        l1 = self.ligne(d, 1, total_ht="31.50")
        self.db.execute("UPDATE devis SET statut='accepte', date_acceptation='2024-05-02' WHERE id=?", (d,))
        b = self.creer_bc(d, origine="import", legacy_id="r12", legacy_numero="BC-2024-05", date_creation="2024-05-03")
        self.assertEqual(self.un("SELECT numero, statut FROM bons_commande WHERE id=?", b), ("BCD-00001-24", "en_cours"))
        self.annuler_bc(b)
        self.annuler_devis(d)
        self.assertEqual(self.ck13(), [])
        self.assertEqual(self.un("SELECT COUNT(*) FROM bc_ligne_garanties")[0], 0)                            # aucune garantie importée


class IdentifiantsDecales(Base):
    """Les identifiants des tables liées sont tous différents (client 7, devis 2, lignes de devis 4+, BC 1) : une garde qui
    confondrait deux identifiants de tables différentes ne peut plus réussir par coïncidence (id = 1 partout)."""

    def setUp(self):
        super().setUp()
        for _ in range(6):
            self.client()
        factice = self.devis(client_id=1)                    # devis n° 1 et ses lignes 1 à 3 : décalent les identifiants suivants
        for i in (1, 2, 3):
            self.ligne(factice, i)

    def test_creation_et_copie(self):
        bc = self.bc_en_etat("en_cours")
        client = self.un("SELECT client_id FROM bons_commande WHERE id=?", bc.b)[0]
        self.assertEqual(len({client, bc.d, bc.dl1, bc.b}), 4)
        self.assertEqual(self.un("SELECT COUNT(*) FROM bc_lignes WHERE bc_id=?", bc.b)[0], 2)
        self.assertEqual(self.un("SELECT COUNT(*) FROM bc_ligne_garanties")[0], 2)
        self.assertEqual(self.ck13(), [])

    def test_INV_40_INV_48_creation(self):
        d = self.devis()                                     # en_attente : devis 2, client 7
        self.assertIn("INV-40", self.essai_creer(d) or "")
        autre = self.client()
        d2 = self.devis_accepte()
        self.assertIn("INV-48", self.essai_creer(d2, client_id=autre) or "")
        self.assertIsNone(self.essai_creer(d2))

    def test_INV_175_ligne_de_devis_etrangere(self):
        b = self.creer_bc(self.devis_accepte(), lignes=False)
        dl_propre = self.un("SELECT id FROM devis_lignes WHERE devis_id=(SELECT devis_id FROM bons_commande WHERE id=?) AND ordre=1", b)[0]
        dl_etranger = self.un("SELECT id FROM devis_lignes WHERE devis_id=?", self.devis_accepte())[0]
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-175"):
            self.ligne_bc(b, dl_etranger, 1)
        bl = self.ligne_bc(b, dl_propre, 1)
        self.refuse_inv("INV-175", "UPDATE bc_lignes SET devis_ligne_id=? WHERE id=?", dl_etranger, bl)
        self.db.execute("UPDATE bc_lignes SET designation='Modifiée' WHERE id=?", (bl,))

    def test_INV_36_lignes_d_un_BC_fige_et_BC_libre_inchange(self):
        gele = self.bc_en_etat("gele", dl3=True)
        d2 = self.devis_accepte()
        extra = self.ligne(d2, 3, designation="À venir", total_ht="5.00", quantite="1")
        b2 = self.creer_bc(d2, lignes=False)
        for dl in self.tous("SELECT id FROM devis_lignes WHERE devis_id=? AND ordre<3 ORDER BY ordre", d2):
            self.ligne_bc(b2, dl[0], self.un("SELECT ordre FROM devis_lignes WHERE id=?", dl[0])[0])
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-36"):
            self.ligne_bc(gele.b, gele.dl3, 3)
        self.refuse_inv("INV-36", "UPDATE bc_lignes SET designation='x' WHERE id=?", gele.bl1)
        # un BC libre reste modifiable alors qu'un autre BC est gelé
        self.db.execute("UPDATE bc_lignes SET designation='x' WHERE bc_id=?", (b2,))
        self.ligne_bc(b2, extra, 3)
        self.db.execute("UPDATE bc_lignes SET designation='y' WHERE bc_id=? AND ordre=3", (b2,))

    def test_INV_36_deplacer_une_ligne_depuis_ou_vers_un_BC_fige(self):
        """TR-13 juge l'ancien BC (OLD.bc_id) ET le nouveau (NEW.bc_id) : le refus INV-36 passe avant le contrôle INV-175."""
        gele = self.bc_en_etat("gele")
        d2 = self.devis_accepte()
        b2 = self.creer_bc(d2)
        bl_libre = self.bc_ligne(b2, 1)
        self.refuse_inv("INV-36", "UPDATE bc_lignes SET bc_id=? WHERE id=?", b2, gele.bl1)          # depuis un BC gelé
        self.refuse_inv("INV-36", "UPDATE bc_lignes SET bc_id=? WHERE id=?", gele.b, bl_libre)      # vers un BC gelé

    def test_INV_175_statut_du_devis_selon_son_BC(self):
        bc = self.bc_en_etat("en_cours")
        libre = self.devis_accepte()
        self.annuler_devis(libre)                            # pas de BC : permis
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-175"):
            self.annuler_devis(bc.d)


class SequencesEtReplace(Base):
    """INV-07, INV-22, D-39 : recursive_triggers=ON, TR-95 (UPDATE), TR-96 (DELETE), REPLACE, upsert maîtrisé."""

    MSG_DIMINUE = "INV-22: numerotation_sequences.dernier_numero ne diminue jamais"
    MSG_SUPPRIME = "INV-22: numerotation_sequences ne se supprime jamais"

    def sequences(self):
        return self.tous("SELECT id, type_objet, annee, dernier_numero, derniere_date, created_at FROM numerotation_sequences ORDER BY id")

    def preparer(self):
        for t, a in (("BCD", 26), ("BCD", 27), ("DEV", 26), ("CLI", 0)):
            self.un(ATTRIBUER, t, a)
        self.un(ATTRIBUER, "BCD", 26)
        self.un(ATTRIBUER, "BCD", 26)                                    # BCD 26 = 3
        return self.sequences()

    def refuse_message(self, message, sql, *args):
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            self.db.execute(sql, args)
        self.assertEqual(str(cm.exception), message)

    def test_D39_recursive_triggers_actif(self):
        self.assertEqual(self.un("PRAGMA recursive_triggers")[0], 1)
        self.assertEqual(self.un("PRAGMA foreign_keys")[0], 1)
        t = Base(); t.db = migrer(recursive=False)                          # témoin : le réglage n'est pas celui de SQLite par défaut
        self.assertEqual(t.un("PRAGMA recursive_triggers")[0], 0)
        self.assertEqual(sqlite3.connect(":memory:").execute("PRAGMA recursive_triggers").fetchone()[0], 0)

    def test_INV_22_les_messages_de_tr95_et_tr96_sont_distincts(self):
        self.assertEqual(self.MSG_DIMINUE.split(": ")[0], self.MSG_SUPPRIME.split(": ")[0])         # même invariant INV-22
        self.assertNotEqual(self.MSG_DIMINUE, self.MSG_SUPPRIME)
        sql95 = self.un("SELECT sql FROM sqlite_master WHERE name='tr_95_numerotation_sequences_no_decrease'")[0]
        sql96 = self.un("SELECT sql FROM sqlite_master WHERE name='tr_96_numerotation_sequences_no_delete'")[0]
        self.assertIn(self.MSG_DIMINUE, sql95)
        self.assertIn(self.MSG_SUPPRIME, sql96)
        self.assertNotIn("supprime", sql95)
        self.assertNotIn("diminue", sql96)

    def test_INV_22_TR96_delete_direct_refuse(self):
        avant = self.preparer()
        for sql, args in (("DELETE FROM numerotation_sequences WHERE type_objet='BCD' AND annee=26", ()),
                          ("DELETE FROM numerotation_sequences WHERE id=?", (avant[0][0],)),
                          ("DELETE FROM numerotation_sequences WHERE type_objet='CLI'", ()),
                          ("DELETE FROM numerotation_sequences WHERE type_objet='DEV'", ()),
                          ("DELETE FROM numerotation_sequences WHERE dernier_numero > 0", ()),
                          ("DELETE FROM numerotation_sequences", ())):
            with self.subTest(sql=sql):
                self.refuse_message(self.MSG_SUPPRIME, sql, *args)
                self.assertEqual(self.sequences(), avant)                        # aucune ligne supprimée, valeurs intactes
        self.db.execute("DELETE FROM numerotation_sequences WHERE type_objet='FAC'")          # aucune ligne concernée : sans effet
        self.db.execute("DELETE FROM numerotation_sequences WHERE 0")
        self.assertEqual(self.sequences(), avant)
        for type_objet in ("CLI", "FOU", "DEV", "BCD", "ACP", "FAC", "AVO", "PVR", "DEP"):
            annee = 0 if type_objet in ("CLI", "FOU") else 26
            self.db.execute("INSERT OR IGNORE INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES (?, ?, 5)", (type_objet, annee))
            self.refuse_message(self.MSG_SUPPRIME, "DELETE FROM numerotation_sequences WHERE type_objet=?", type_objet)

    def test_INV_22_TR96_delete_refuse_meme_si_la_sequence_est_vide_ou_au_plafond(self):
        self.db.execute("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('BCD', 28, 0)")
        self.refuse_message(self.MSG_SUPPRIME, "DELETE FROM numerotation_sequences WHERE annee=28")
        self.db.execute("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('BCD', 29, 99999)")
        self.refuse_message(self.MSG_SUPPRIME, "DELETE FROM numerotation_sequences WHERE annee=29")
        self.assertEqual(self.un("SELECT COUNT(*) FROM numerotation_sequences")[0], 2)

    def test_INV_22_TR95_update_diminuant_toujours_refuse(self):
        avant = self.preparer()
        for sql in ("UPDATE numerotation_sequences SET dernier_numero = 2 WHERE type_objet='BCD' AND annee=26",
                    "UPDATE numerotation_sequences SET dernier_numero = 0 WHERE type_objet='BCD' AND annee=26",
                    "UPDATE numerotation_sequences SET dernier_numero = dernier_numero - 1 WHERE type_objet='BCD' AND annee=26",
                    "UPDATE numerotation_sequences SET dernier_numero = dernier_numero - 1"):
            with self.subTest(sql=sql):
                self.refuse_message(self.MSG_DIMINUE, sql)
                self.assertEqual(self.sequences(), avant)
        # le DELETE n'est pas le message du UPDATE
        self.refuse_message(self.MSG_SUPPRIME, "DELETE FROM numerotation_sequences WHERE type_objet='BCD'")

    def test_INV_22_TR95_update_non_diminuant_permis(self):
        self.preparer()
        self.db.execute("UPDATE numerotation_sequences SET dernier_numero = dernier_numero WHERE type_objet='BCD' AND annee=26")
        self.db.execute("UPDATE numerotation_sequences SET dernier_numero = 3 WHERE type_objet='BCD' AND annee=26")
        self.db.execute("UPDATE numerotation_sequences SET dernier_numero = 50 WHERE type_objet='BCD' AND annee=26")
        self.db.execute("UPDATE numerotation_sequences SET derniere_date = '2026-10-02', updated_at = ? WHERE type_objet='BCD' AND annee=26", (TS2,))
        self.assertEqual(self.un("SELECT dernier_numero, derniere_date FROM numerotation_sequences WHERE type_objet='BCD' AND annee=26"),
                         (50, "2026-10-02"))

    def test_INV_22_REPLACE_refuse_par_tr96_avec_recursive_triggers(self):
        avant = self.preparer()
        premiere = avant[0]
        for sql, args in (
                ("INSERT OR REPLACE INTO numerotation_sequences (id, type_objet, annee, dernier_numero) VALUES (?, 'BCD', 26, 1)", (premiere[0],)),
                ("INSERT OR REPLACE INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('BCD', 26, 1)", ()),
                ("REPLACE INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('BCD', 26, 1)", ()),
                ("INSERT OR REPLACE INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('BCD', 26, 5000)", ()),   # même un compteur supérieur
                ("INSERT OR REPLACE INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('CLI', 0, 1)", ())):
            with self.subTest(sql=sql):
                self.refuse_message(self.MSG_SUPPRIME, sql, *args)
                self.assertEqual(self.sequences(), avant)                                  # ligne existante intacte, valeur non diminuée
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='BCD' AND annee=26")[0], 3)
        # un REPLACE sans conflit n'écrase rien : c'est un INSERT ordinaire
        self.db.execute("INSERT OR REPLACE INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('BCD', 30, 1)")
        self.assertEqual(len(self.sequences()), len(avant) + 1)

    def test_D39_temoin_sans_recursive_triggers_le_replace_efface_la_sequence(self):
        """Démontre pourquoi le réglage est obligatoire : sans lui, TR-96 refuse le DELETE direct mais pas le REPLACE."""
        t = Base(); t.db = migrer(recursive=False); t._n = 0
        t.preparer = lambda: None
        for type_objet, annee in (("BCD", 26),):
            for _ in range(3):
                t.un(ATTRIBUER, type_objet, annee)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "ne se supprime jamais"):
            t.db.execute("DELETE FROM numerotation_sequences WHERE type_objet='BCD'")
        t.db.execute("INSERT OR REPLACE INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('BCD', 26, 1)")
        self.assertEqual(t.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='BCD'")[0], 1)    # compteur diminué !

    def test_INV_22_upsert_maitrise_autorise(self):
        avant = self.preparer()
        n = self.un(ATTRIBUER, "BCD", 26)[0]
        self.assertEqual(n, 4)
        après = self.sequences()
        self.assertEqual([l[:3] + l[5:] for l in après], [l[:3] + l[5:] for l in avant])                 # id, type, annee, created_at identiques
        self.assertEqual(sorted(l[3] for l in après), sorted([4 if l[1:3] == ("BCD", 26) else l[3] for l in avant]))
        # la ligne n'a pas été supprimée puis recréée (id et created_at conservés)
        self.assertEqual(self.un("SELECT id FROM numerotation_sequences WHERE type_objet='BCD' AND annee=26")[0], avant[0][0])
        # upsert qui fixe explicitement une valeur supérieure : permis ; inférieure : refusé par TR-95
        self.db.execute("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('BCD', 26, 10) "
                        "ON CONFLICT (type_objet, annee) DO UPDATE SET dernier_numero = excluded.dernier_numero")
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='BCD' AND annee=26")[0], 10)
        self.refuse_message(self.MSG_DIMINUE, "INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('BCD', 26, 5) "
                            "ON CONFLICT (type_objet, annee) DO UPDATE SET dernier_numero = excluded.dernier_numero")
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='BCD' AND annee=26")[0], 10)
        # INSERT d'une nouvelle séquence et INSERT OR IGNORE : permis, sans effet sur l'existant
        self.db.execute("INSERT INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('BCD', 31, 1)")
        self.db.execute("INSERT OR IGNORE INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES ('BCD', 26, 1)")
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='BCD' AND annee=26")[0], 10)

    def test_INV_22_upsert_repete_ne_produit_jamais_de_doublon_ni_de_retour_en_arriere(self):
        numeros = [self.un(ATTRIBUER, "BCD", 26)[0] for _ in range(25)]
        self.assertEqual(numeros, list(range(1, 26)))
        self.assertEqual(self.un("SELECT COUNT(*) FROM numerotation_sequences")[0], 1)

    def test_INV_174_REPLACE_ne_contourne_pas_tr19(self):
        champs = ("numero, devis_id, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                  "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, date_acceptation, "
                  "montant_contractuel_ht, remise_type, acompte_type")
        for etat in ETATS_TOUS:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                avant = self.un("SELECT * FROM bons_commande WHERE id=?", bc.b)
                with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-174"):             # conflit sur id
                    self.db.execute(f"INSERT OR REPLACE INTO bons_commande (id, {champs}) "
                                    f"SELECT id, {champs.replace('remise_type, acompte_type', chr(39) + 'aucune' + chr(39) + ', ' + chr(39) + 'aucun' + chr(39))} "
                                    "FROM bons_commande WHERE id=?", (bc.b,))
                with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-174"):             # conflit sur numero et devis_id (autre id)
                    self.db.execute(f"INSERT OR REPLACE INTO bons_commande (id, {champs}) "
                                    f"SELECT 99999, {champs.replace('remise_type, acompte_type', chr(39) + 'aucune' + chr(39) + ', ' + chr(39) + 'aucun' + chr(39))} "
                                    "FROM bons_commande WHERE id=?", (bc.b,))
                self.assertEqual(self.un("SELECT * FROM bons_commande WHERE id=?", bc.b), avant)
                self.assertEqual(self.un("SELECT COUNT(*) FROM bc_lignes WHERE bc_id=?", bc.b)[0], 2)

    def test_D39_temoin_sans_recursive_triggers_le_replace_efface_un_bc(self):
        t = Base(); t.db = migrer(recursive=False); t._n = 0
        d = t.devis_accepte(lignes=0)
        b = t.creer_bc(d, lignes=False)
        t.db.execute("INSERT OR REPLACE INTO bons_commande (id, numero, devis_id, client_id, client_snapshot, client_snapshot_version, "
                     "entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, "
                     "date_acceptation, montant_contractuel_ht, remise_type, acompte_type, statut) "
                     "SELECT id, numero, devis_id, client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, "
                     "entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, date_acceptation, "
                     "'1.00', 'aucune', 'aucun', 'en_cours' FROM bons_commande WHERE id=?", (b,))
        self.assertEqual(t.un("SELECT montant_contractuel_ht FROM bons_commande WHERE id=?", b)[0], "1.00")      # remplacé sans trigger
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-174"):
            t.db.execute("DELETE FROM bons_commande WHERE id=?", (b,))                                          # le DELETE direct reste refusé

    REPLACE_LIGNE = ("INSERT OR REPLACE INTO bc_lignes (id, bc_id, devis_ligne_id, ordre, designation, quantite, unite, "
                     "prix_unitaire_ht, remise_type, type_prestation, total_ht) "
                     "VALUES (?, ?, ?, 3, 'x', '1', 'u', '1', 'aucune', 'pose', '1.00')")

    def test_INV_36_REPLACE_ne_contourne_pas_tr13_lignes(self):
        """Le REPLACE « déplace » la ligne d'un BC figé vers un BC modifiable : l'INSERT est permis, c'est le DELETE implicite de
        l'ancienne ligne qui doit être refusé (BEFORE DELETE, effectif avec recursive_triggers=ON)."""
        t = Base(); t.db = migrer(recursive=False); t._n = 0                  # témoin : l'ancienne ligne disparaît sans contrôle
        figé, libre = t.bc_en_etat("gele"), t.bc_en_etat("en_cours", dl3=True)
        t.db.execute(self.REPLACE_LIGNE, (figé.bl1, libre.b, libre.dl3))
        self.assertEqual(t.un("SELECT bc_id FROM bc_lignes WHERE id=?", figé.bl1)[0], libre.b)
        for etat in ETATS_FIGES:
            with self.subTest(etat=etat):
                figé, libre = self.bc_en_etat(etat), self.bc_en_etat("en_cours", dl3=True)
                avant = self.un("SELECT * FROM bc_lignes WHERE id=?", figé.bl1)
                with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-36"):
                    self.db.execute(self.REPLACE_LIGNE, (figé.bl1, libre.b, libre.dl3))
                self.assertEqual(self.un("SELECT * FROM bc_lignes WHERE id=?", figé.bl1), avant)
                self.assertEqual(self.un("SELECT COUNT(*) FROM bc_lignes WHERE bc_id=?", libre.b)[0], 2)
                self.assertEqual(self.un("SELECT COUNT(*) FROM bc_ligne_garanties WHERE ligne_id=?", figé.bl1)[0], 2)

    def test_INV_36_REPLACE_ne_contourne_pas_tr13_garanties(self):
        remplace = "INSERT OR REPLACE INTO bc_ligne_garanties (id, ligne_id, garantie_type) VALUES (?, ?, 'decennale')"
        t = Base(); t.db = migrer(recursive=False); t._n = 0                  # témoin
        figé, libre = t.bc_en_etat("gele"), t.bc_en_etat("en_cours")
        t.db.execute(remplace, (figé.bg1, libre.bl2))
        self.assertEqual(t.un("SELECT ligne_id FROM bc_ligne_garanties WHERE id=?", figé.bg1)[0], libre.bl2)
        for etat in ETATS_FIGES:
            with self.subTest(etat=etat):
                figé, libre = self.bc_en_etat(etat), self.bc_en_etat("en_cours")
                with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-36"):
                    self.db.execute(remplace, (figé.bg1, libre.bl2))
                self.assertEqual(self.un("SELECT ligne_id FROM bc_ligne_garanties WHERE id=?", figé.bg1)[0], figé.bl1)

    def test_INV_36_REPLACE_autorise_sur_un_bc_modifiable_pour_les_lignes(self):
        """Le REPLACE n'est pas interdit par la base sur un BC modifiable (la convention d'équipe l'interdit au service)."""
        bc = self.bc_en_etat("en_cours")
        self.db.execute("INSERT OR REPLACE INTO bc_lignes (id, bc_id, devis_ligne_id, ordre, designation, quantite, unite, prix_unitaire_ht, "
                        "remise_type, type_prestation, total_ht) VALUES (?, ?, ?, 1, 'x', '1', 'u', '1', 'aucune', 'pose', '1.00')",
                        (bc.bl1, bc.b, bc.dl1))
        self.assertEqual(self.un("SELECT designation FROM bc_lignes WHERE id=?", bc.bl1)[0], "x")


class SuppressionEtCles(Base):
    """INV-05, INV-06, INV-174 : aucune suppression physique d'un BC ; FK RESTRICT ; aucune clause ON UPDATE."""

    def test_INV_174_delete_d_un_bc_toujours_refuse(self):
        for etat in ETATS_TOUS:
            with self.subTest(etat=etat):
                bc = self.bc_en_etat(etat)
                self.refuse_inv("INV-174", "DELETE FROM bons_commande WHERE id=?", bc.b)
                self.refuse_inv("INV-174", "DELETE FROM bons_commande WHERE numero=(SELECT numero FROM bons_commande WHERE id=?)", bc.b)
                self.assertEqual(self.un("SELECT COUNT(*) FROM bons_commande WHERE id=?", bc.b)[0], 1)
                self.assertEqual(self.un("SELECT COUNT(*) FROM bc_lignes WHERE bc_id=?", bc.b)[0], 2)
        sans_lignes = self.creer_bc(self.devis_accepte(), lignes=False)                                          # BC sans aucune ligne
        self.refuse_inv("INV-174", "DELETE FROM bons_commande WHERE id=?", sans_lignes)
        self.refuse_inv("INV-174", "DELETE FROM bons_commande", )
        self.db.execute("DELETE FROM bons_commande WHERE id=99999")                                              # aucune ligne : sans effet
        self.assertEqual(self.un("SELECT COUNT(*) FROM bons_commande")[0], len(ETATS_TOUS) + 1)

    def test_INV_174_bc_importe_ou_annule_avec_son_devis_jamais_supprimable(self):
        bc = self.bc_en_etat("annule")
        self.annuler_devis(bc.d)
        self.refuse_inv("INV-174", "DELETE FROM bons_commande WHERE id=?", bc.b)
        self.refuse_check("DELETE FROM devis WHERE id=?", bc.d)
        self.refuse_check("DELETE FROM clients WHERE id=(SELECT client_id FROM bons_commande WHERE id=?)", bc.b)

    def test_INV_174_FK_RESTRICT_est_une_garde_independante_du_trigger(self):
        t = Base(); t.db = migrer(); t._n = 0
        t.db.execute("DROP TRIGGER tr_19_bons_commande_no_delete")
        bc = t.bc_en_etat("en_cours")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):                 # bc_lignes.bc_id en RESTRICT (et non CASCADE)
            t.db.execute("DELETE FROM bons_commande WHERE id=?", (bc.b,))
        self.assertEqual(t.un("SELECT COUNT(*) FROM bc_lignes WHERE bc_id=?", bc.b)[0], 2)
        sans = t.creer_bc(t.devis_accepte(), lignes=False)                                    # sans lignes : seul TR-19 protège
        t.db.execute("DELETE FROM bons_commande WHERE id=?", (sans,))
        self.assertEqual(t.un("SELECT COUNT(*) FROM bons_commande WHERE id=?", sans)[0], 0)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY"):                 # bons_commande.devis_id en RESTRICT
            t.db.execute("DELETE FROM devis WHERE id=?", (bc.d,))

    def test_INV_05_aucune_cascade_vers_ou_depuis_bons_commande(self):
        actions = {(t, r[2], r[3], r[6]) for t in TABLES_004 for r in self.db.execute(f"PRAGMA foreign_key_list({t})")}
        self.assertEqual({a for a in actions if a[3] == "CASCADE"}, {("bc_ligne_garanties", "bc_lignes", "ligne_id", "CASCADE")})
        for t in TABLES_004 - {"bc_ligne_garanties"}:
            self.assertEqual({a[3] for a in actions if a[0] == t}, {"RESTRICT"}, t)

    def test_INV_06_client_et_prestation_utilises_ne_se_suppriment_pas(self):
        bc = self.bc_en_etat("en_cours")
        c = self.un("SELECT client_id FROM bons_commande WHERE id=?", bc.b)[0]
        self.refuse_check("DELETE FROM clients WHERE id=?", c)
        self.refuse_check("UPDATE clients SET id=99999 WHERE id=?", c)                         # aucune clause ON UPDATE
        self.refuse("UPDATE devis SET id=99999 WHERE id=?", bc.d)                              # TR-10 (003) ou FK
        self.refuse_check("UPDATE bc_lignes SET id=99999 WHERE id=?", bc.bl1)                  # garanties : ligne_id sans ON UPDATE
        self.refuse_check("UPDATE devis_lignes SET id=99999 WHERE id=?", bc.dl1)
        self.refuse_inv("INV-48", "INSERT INTO bons_commande (numero, devis_id, client_id, client_snapshot, client_snapshot_version, "
                          "entreprise_snapshot, entreprise_snapshot_version, chantier_snapshot, chantier_snapshot_version, date_creation, "
                          "date_acceptation, montant_contractuel_ht, remise_type, acompte_type) "
                          "SELECT 'BCD-00088-26', id, 99999, client_snapshot, 1, entreprise_snapshot, 1, chantier_snapshot, 1, "
                          "'2026-10-02', '2026-03-12', total_ht, 'aucune', 'aucun' FROM devis WHERE id=?", self.devis_accepte())
        self.refuse_check("UPDATE bons_commande SET client_id=99999 WHERE id=?", bc.b)
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_T29_cle_etrangere_vers_une_table_absente_echoue_meme_avec_NULL(self):
        """Raison pour laquelle 004 n'anticipe aucune table future : une FK vers une table inexistante échoue même avec NULL."""
        db = sqlite3.connect(":memory:", isolation_level=None)
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("CREATE TABLE a (id INTEGER PRIMARY KEY, f_id INTEGER REFERENCES absente (id)) STRICT")
        with self.assertRaises(sqlite3.Error):
            db.execute("INSERT INTO a (id, f_id) VALUES (1, NULL)")
        tables = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for t in TABLES_004:
            for r in self.db.execute(f"PRAGMA foreign_key_list({t})"):
                self.assertIn(r[2], tables)

    def test_T29_scenario_complet_laisse_une_base_saine(self):
        for etat in ETATS_TOUS:
            bc = self.bc_en_etat(etat)
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(self.db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
        self.assertEqual(self.un("SELECT COUNT(*) FROM bons_commande")[0], len(ETATS_TOUS))
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='BCD' AND annee=26")[0], len(ETATS_TOUS))


class ChaqueTriggerGardeSeul(Base):
    """Chaque trigger de la tranche refuse seul la violation qui lui est propre ; sans lui, la violation passe (il est donc le garde)."""

    def scenarios(self):
        """nom du trigger -> (préparation(t) retournant l'action, motif du message)."""
        def tr01(t):
            bc = t.bc_en_etat("en_cours")
            return lambda: t.db.execute("UPDATE bons_commande SET numero='BCD-00099-26' WHERE id=?", (bc.b,))
        def tr12_mod(t):
            bc = t.bc_en_etat("en_cours")
            return lambda: t.db.execute("UPDATE bons_commande SET created_at='2020-01-01T00:00:00.000Z' WHERE id=?", (bc.b,))
        def tr12_gele(t):
            bc = t.bc_en_etat("gele")
            return lambda: t.db.execute("UPDATE bons_commande SET montant_contractuel_ht='1.00' WHERE id=?", (bc.b,))
        def tr12_annule(t):
            bc = t.bc_en_etat("annule")
            return lambda: t.db.execute("UPDATE bons_commande SET date_debut='2026-11-01' WHERE id=?", (bc.b,))
        def tr14(t):
            bc = t.bc_en_etat("gele")
            return lambda: t.db.execute("UPDATE bons_commande SET frozen_at=NULL WHERE id=?", (bc.b,))
        def tr17(t):
            d = t.devis_accepte()
            return lambda: t.creer_bc(d, lignes=False, montant_deja_facture_ht="5.00")
        def tr19(t):
            b = t.creer_bc(t.devis_accepte(), lignes=False)
            return lambda: t.db.execute("DELETE FROM bons_commande WHERE id=?", (b,))
        def tr18(t):
            bc = t.bc_en_etat("en_cours")
            return lambda: t.db.execute("UPDATE devis SET statut='annule', cancelled_at=?, motif_annulation='m' WHERE id=?", (TS, bc.d))
        def lig_ins(t):
            bc = t.bc_en_etat("gele", dl3=True)
            return lambda: t.ligne_bc(bc.b, bc.dl3, 3)
        def lig_ins_annule(t):
            bc = t.bc_en_etat("annule", dl3=True)
            return lambda: t.ligne_bc(bc.b, bc.dl3, 3)
        def lig_upd(t):
            bc = t.bc_en_etat("gele")
            return lambda: t.db.execute("UPDATE bc_lignes SET designation='x' WHERE id=?", (bc.bl1,))
        def lig_upd_vers(t):
            gele, libre = t.bc_en_etat("gele"), t.bc_en_etat("en_cours")
            return lambda: t.db.execute("UPDATE bc_lignes SET designation='x' WHERE id=?", (gele.bl1,))
        def lig_del(t):
            bc = t.bc_en_etat("gele")
            return lambda: t.db.execute("DELETE FROM bc_lignes WHERE id=?", (bc.bl2,))
        def gar_ins(t):
            bc = t.bc_en_etat("gele")
            return lambda: t.db.execute("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) VALUES (?, 'parfait_achevement')", (bc.bl1,))
        def gar_upd(t):
            bc = t.bc_en_etat("gele")
            return lambda: t.db.execute("UPDATE bc_ligne_garanties SET garantie_type='parfait_achevement' WHERE id=?", (bc.bg1,))
        def gar_del(t):
            bc = t.bc_en_etat("gele")
            return lambda: t.db.execute("DELETE FROM bc_ligne_garanties WHERE id=?", (bc.bg1,))
        def tr96(t):
            t.un(ATTRIBUER, "BCD", 26)
            return lambda: t.db.execute("DELETE FROM numerotation_sequences WHERE type_objet='BCD'")
        return {"tr_01_bons_commande_numero_immuable": (tr01, "INV-23"),
                "tr_12_bons_commande_modifiable": (tr12_mod, "INV-36"),
                "tr_12_bons_commande_gele": (tr12_gele, "INV-36"),
                "tr_12_bons_commande_annule": (tr12_annule, "INV-173"),
                "tr_14_bons_commande_frozen_at": (tr14, "INV-34"),
                "tr_17_bons_commande_insert": (tr17, "INV-40"),
                "tr_19_bons_commande_no_delete": (tr19, "INV-174"),
                "tr_18_devis_statut_avec_bc": (tr18, "INV-175"),
                "tr_13_bc_lignes_insert": (lig_ins, "INV-36"),
                "tr_13_bc_lignes_update": (lig_upd, "INV-36"),
                "tr_13_bc_lignes_delete": (lig_del, "INV-36"),
                "tr_13_bc_ligne_garanties_insert": (gar_ins, "INV-36"),
                "tr_13_bc_ligne_garanties_update": (gar_upd, "INV-36"),
                "tr_13_bc_ligne_garanties_delete": (gar_del, "INV-36"),
                "tr_96_numerotation_sequences_no_delete": (tr96, "ne se supprime jamais")}

    def isole(self, gardes):
        """Base 001-004 dont tous les triggers de la tranche 004 sont supprimés sauf `gardes`."""
        t = Base(); t.db = migrer(); t._n = 0
        for nom in TRIGGERS_004 - set(gardes):
            t.db.execute(f"DROP TRIGGER {nom}")
        return t

    def test_T29_tous_les_triggers_ont_un_scenario(self):
        self.assertEqual(set(self.scenarios()), TRIGGERS_004)

    def test_T29_chaque_trigger_refuse_seul_et_sans_lui_la_violation_passe(self):
        for nom, (preparer, motif) in self.scenarios().items():
            with self.subTest(trigger=nom):
                seul = self.isole({nom})
                agir = preparer(seul)
                with self.assertRaisesRegex(sqlite3.IntegrityError, motif):
                    agir()
                sans = self.isole(set())
                agir = preparer(sans)
                agir()                                                       # aucune autre garde : la violation passe

    def test_T29_le_trigger_annule_et_le_trigger_gele_n_ont_pas_le_meme_perimetre(self):
        # tr_12_gele ne garde pas un BC annulé non gelé ; tr_12_annule ne garde pas un BC gelé non annulé
        seul = self.isole({"tr_12_bons_commande_gele"})
        bc = seul.bc_en_etat("annule")
        seul.db.execute("UPDATE bons_commande SET date_debut='2026-11-01' WHERE id=?", (bc.b,))
        seul = self.isole({"tr_12_bons_commande_annule"})
        bc = seul.bc_en_etat("gele")
        seul.db.execute("UPDATE bons_commande SET montant_contractuel_ht='1.00' WHERE id=?", (bc.b,))
        seul = self.isole({"tr_12_bons_commande_modifiable"})
        for etat in ("gele", "annule"):
            bc = seul.bc_en_etat(etat)
            seul.db.execute("UPDATE bons_commande SET created_at='2020-01-01T00:00:00.000Z' WHERE id=?", (bc.b,))   # hors périmètre

    def test_T29_TR01_et_TR14_ne_dependent_pas_des_triggers_de_liste_blanche(self):
        seul = self.isole({"tr_01_bons_commande_numero_immuable"})
        for etat in ETATS_TOUS:
            bc = seul.bc_en_etat(etat)
            with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-23"):
                seul.db.execute("UPDATE bons_commande SET date_creation='2026-10-03' WHERE id=?", (bc.b,))
        seul = self.isole({"tr_14_bons_commande_frozen_at"})
        for etat in ("gele", "termine", "annule_gele"):
            bc = seul.bc_en_etat(etat)
            with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-34"):
                seul.db.execute("UPDATE bons_commande SET frozen_at=? WHERE id=?", (TS2, bc.b))
        bc = seul.bc_en_etat("annule")
        seul.db.execute("UPDATE bons_commande SET frozen_at=? WHERE id=?", (TS2, bc.b))                          # NULL -> valeur : permis par TR-14


if __name__ == "__main__":
    unittest.main(verbosity=2)
