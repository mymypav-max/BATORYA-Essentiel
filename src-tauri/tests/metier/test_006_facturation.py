"""T-48 — Tranche 006_facturation (rang 9) ; modèle V3.13 §4.8 (factures, facture_lignes), §6 (numérotation ACP, FAC, AVO), §8 (TR-02, TR-16, TR-20 à TR-23,
TR-99), §9 (index), §10 (import), §14 (CK-01 à CK-06, CK-13, CK-14) ; invariants INV-06, INV-24, INV-47, INV-48, INV-52 à INV-62, INV-76, INV-173, INV-185,
INV-187 à INV-190 ; CADRAGE__006_facturation.md (VR-01 à VR-13, DV-1 à DV-10, QO-3) et les décisions de l'étape d'implémentation (acomptes par devis,
situations ligne par ligne, référence d'avancement ρ, ordinal de situation par BC, formule de facturation figée).

006 crée deux tables (factures, facture_lignes), leurs index et leurs triggers, et UN trigger sur bc_devis (aucun devis après un solde, même crédité).
Responsabilités vérifiées ici :
  * CHECK / index : types, cohérence type <-> colonnes, familles de montants, bornes de pourcentage, précédent <= cumulé, unicité de l'ordinal de
    situation par BC, une ligne d'avancement par facture et par ligne de BC ;
  * triggers : immuabilité, aucun DELETE (REPLACE compris), un seul acompte actif par devis, appartenance devis <-> BC, aucune facture après un solde,
    plafond contractuel, BC annulé / terminé, cohérence avoir <-> origine, ligne de BC du bon BC, référence d'avancement ρ ;
  * services (reproduits ici par des fabriques et un oracle Python, JAMAIS par le schéma) : plafond de l'acompte prévu, g / r / X / N / M, M > 0,
    situation_numero = 1 + MAX, exhaustivité des lignes d'avancement, confirmation d'un solde à 0.00, date_100_facture, caches du BC ;
  * diagnostics CK (requêtes en constantes SQL, lecture seule) : CK-01, CK-02, CK-03, CK-04, CK-05, CK-06 (volet 006), CK-13, CK-14 (volet solde) et deux
    contrôles nouveaux justifiés par 006 : CK-16 (lignes d'avancement : exhaustivité, doublon, ligne étrangère) et CK-17 (cohérence montant / pourcentages).

Réutilisation : ces tests importent test_005c (qui importe test_005b) pour l'émulation du runner et la fabrication des devis, BC et lignes, sans les modifier.
Le rang 9 est obtenu en appliquant 006 sur la chaîne du rang 8 : 006 ne reconstruit aucune table (BEGIN IMMEDIATE, fichier, PRAGMA user_version = 9, COMMIT,
foreign_keys=ON conservé) ; le protocole de reconstruction du runner est aussi accepté et testé.

Exécution : python3 src-tauri/tests/metier/test_006_facturation.py
Les méthodes portent le nom de l'invariant vérifié (test_INV_xx_…) ; les autres commencent par test_T48_ suivi du groupe (A chaîne, B structure, C CHECK de
factures, D CHECK de facture_lignes, E argent et oracle, F numérotation, G immuabilité et contournements, H acomptes, I situations, J solde, K avoirs,
L devis et états du BC, M diagnostics CK, N import, O sauvegarde et restauration, P non-régression, Q triggers gardiens et transactions, R cas limites).
Les décisions d'interprétation portent « INTERPRETATION ». Connexion de test : PRAGMA foreign_keys=ON et PRAGMA recursive_triggers=ON (D-39).
Un refus levé par un trigger se reconnaît à son préfixe « INV-nn » ; un refus levé par une contrainte (CHECK, NOT NULL, UNIQUE, FK) n'en porte aucun.
"""
import pathlib
import random
import re
import sqlite3
import sys
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import test_005b_bc_multi_devis as T  # noqa: E402  (fabrication de données et émulation du runner)
import test_005c_bc_annule_caches_financiers as C  # noqa: E402

MIGRATIONS = T.MIGRATIONS
NOM_006 = "006_facturation.sql"
NOMS = C.NOMS + (NOM_006,)
SQL_006 = (MIGRATIONS / NOM_006).read_text(encoding="utf-8")
RANG = 9
TS, TS2 = T.TS, T.TS2
TS_EMISSION = "2050-01-01T12:00:00.000Z"                                                    # created_at des factures de test : après les lignes de BC (TS) et après l'horloge réelle des liens bc_devis (CK-14)
TS_APRES = "2099-01-01T00:00:00.000Z"                                                        # lignes de BC créées après toute facture (horloge réelle)
ATTRIBUER = T.ATTRIBUER
OMIT = object()                                                                             # valeur d'une colonne à ne pas fournir

TABLES_RANG9 = T.TABLES_RANG7 | {"factures", "facture_lignes"}
INDEXES_006 = {"idx_factures_bc_id", "idx_factures_client_id", "idx_factures_devis_id", "idx_factures_origine_facture_id",
               "idx_factures_type_date_echeance", "idx_factures_date_emission", "uq_factures_bc_situation_numero",
               "idx_facture_lignes_bc_ligne_id", "uq_facture_lignes_avancement"}
TRIGGERS_006 = {"tr_20_factures_no_update": "factures", "tr_21_factures_no_delete": "factures", "tr_21_facture_lignes_no_update": "facture_lignes",
                "tr_21_facture_lignes_no_delete": "facture_lignes", "tr_02_factures_chronologie": "factures", "tr_16_factures_bc": "factures",
                "tr_22_factures_acompte": "factures", "tr_22_factures_situation": "factures", "tr_22_factures_solde": "factures",
                "tr_23_factures_avoir": "factures", "tr_22_facture_lignes_insert": "facture_lignes", "tr_99_bc_devis_apres_solde": "bc_devis"}
COLONNES_FACTURES = ["id", "numero", "type", "bc_id", "client_id", "devis_id", "client_snapshot", "client_snapshot_version", "entreprise_snapshot",
                     "entreprise_snapshot_version", "chantier_snapshot", "chantier_snapshot_version", "objet", "date_emission", "date_echeance",
                     "total_ht", "situation_numero", "montant_deja_facture_ht", "origine_facture_id", "motif_avoir", "created_at", "origine",
                     "legacy_id", "legacy_data"]
COLONNES_LIGNES = ["id", "facture_id", "ordre", "bc_ligne_id", "reference_prestation", "designation", "description", "quantite", "unite",
                   "prix_unitaire_ht", "remise_type", "remise_valeur", "type_ligne", "montant_ht", "avancement_precedent_pct",
                   "avancement_cumule_pct", "created_at"]
TYPES = ("acompte", "situation", "solde", "avoir")
# Écritures MALFORMÉES, toutes refusées par la famille D2 (montant >= 0 à deux décimales, forme canonique) : chacune ne peut être arrêtée que par UN terme du CHECK.
MAL_D2 = ("1.23.45", "12.34.56", "1.2.34", "1a.23", "a1.23", "1.2a", "1.23 ", " 1.23", "1.23\n", "1..23", "1,23", ".50", ".00", ".99", "0x.00", "١.00",
          "00.00", "01.23", "-0.00", "-1.23", "--1.23", "+1.23", "1.23e", "1e2.00", "1.", ".", "..", "")
# idem pour la partie NÉGATIVE de la famille D2S (déduction)
MAL_D2S_NEG = ("-1.23.45", "-12.34.56", "-1.2.34", "-1a.23", "-a1.23", "-1.2a", "-1.23 ", "- 1.23", "-1.23\n", "-1..23", "-1,23", "-.50", "-.00", "-0x.00", "-١.00",
               "-00.50", "-01.23", "-0.00", "--1.23", "-+1.23", "-1.23e", "-1.", "-.", "-", "1.23-", "-1")
# idem pour la famille DL (décimal libre sans zéro final : quantité, prix, remise en montant)
MAL_DL = ("1.2.3", "1.5.5", "12.34.5", "1a", "a1", "1..5", "1,5", ".5", ".25", "5.", "0x1", "1 5", " 1", "1 ", "1\n", "١", "-1", "+1", "1e3", "00", "01", "00.5", "1.50", "1.0", "0.0", "")
PREFIXES = {"acompte": "ACP", "situation": "FAC", "solde": "FAC", "avoir": "AVO"}


# --------------------------------------------------------------------------------------------------------------------
# Chaîne
# --------------------------------------------------------------------------------------------------------------------
def migrer9(recursive=True):
    """Chaîne 001 à 005c (rang 8) puis 006 comme une migration ordinaire : BEGIN IMMEDIATE, fichier, user_version = 9, COMMIT."""
    db = C.migrer8(recursive=recursive)
    T.appliquer(db, RANG, SQL_006)
    return db


# --------------------------------------------------------------------------------------------------------------------
# Oracle monétaire (le « service » : jamais de flottant ; centimes entiers ; HALF_UP aux seuls endroits prévus)
# --------------------------------------------------------------------------------------------------------------------
def c(s):
    """'12.50' -> 1250 ; '-0.05' -> -5 (centimes entiers) ; un pourcentage P2 '62.50' donne 6250 (centièmes de pour cent)."""
    return int(s.replace(".", ""))


def eur(n):
    """1250 -> '12.50' ; -5 -> '-0.05'."""
    return ("-" if n < 0 else "") + f"{abs(n) // 100}.{abs(n) % 100:02d}"


def dl(montant):
    """Représentation DL minimale d'un montant D2 : '4000.00' -> '4000', '12.50' -> '12.5', '0.00' -> '0'."""
    s = montant.lstrip("-")
    return s.rstrip("0").rstrip(".") if "." in s else s


def g(b, p):
    """Valeur de la ligne : (b × P + 5000) div 10000 — HALF_UP, une seule fois par ligne (b en centimes, P en centièmes de pour cent)."""
    return (b * p + 5000) // 10000


def r(R, G, B):
    """Réduction globale du devis : (2·R·G + B) div (2·B) — HALF_UP, une seule fois par devis ; 0 si B = 0."""
    return 0 if B == 0 else (2 * R * G + B) // (2 * B)


def valeur_cumulee(devis):
    """devis : liste de (lignes [(b, P)], total_devis). Retourne (X, [(B, R, G, rr)]) — X = Σ_d (G_d − r_d)."""
    x, detail = 0, []
    for lignes, total in devis:
        B = sum(b for b, _ in lignes)
        R = B - total
        assert R >= 0, "remise négative"
        G = sum(g(b, p) for b, p in lignes)
        rr = r(R, G, B)
        x += G - rr
        detail.append((B, R, G, rr))
    return x, detail


# --------------------------------------------------------------------------------------------------------------------
# Diagnostics CK (requêtes de contrôle : lecture seule ; chaque requête retourne les lignes en violation)
# --------------------------------------------------------------------------------------------------------------------
SOMME_AVOIRS = "(SELECT COALESCE(SUM(CAST(REPLACE(av.total_ht, '.', '') AS INTEGER)), 0) FROM factures av WHERE av.origine_facture_id = {a}.id)"
NEUTRALISEE = "({a}.total_ht <> '0.00' AND " + SOMME_AVOIRS + " = CAST(REPLACE({a}.total_ht, '.', '') AS INTEGER))"
NETTE_BC = ("(SELECT COALESCE(SUM(CASE WHEN f.type = 'avoir' THEN -CAST(REPLACE(f.total_ht, '.', '') AS INTEGER) "
            "ELSE CAST(REPLACE(f.total_ht, '.', '') AS INTEGER) END), 0) FROM factures f WHERE f.bc_id = {b}.id)")
CK01_DOUBLONS = "SELECT numero FROM factures GROUP BY numero HAVING count(*) > 1"
CK01_FORMAT_V6 = ("SELECT id FROM factures WHERE origine = 'v6' AND NOT (numero GLOB (CASE type WHEN 'acompte' THEN 'ACP-' WHEN 'avoir' THEN 'AVO-' ELSE 'FAC-' END) "
                  "|| '[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]' AND substr(numero, 11, 2) = substr(date_emission, 3, 2))")
CK02_SEQUENCES = ("SELECT f.id FROM factures f WHERE f.origine = 'v6' AND NOT EXISTS (SELECT 1 FROM numerotation_sequences s "
                  "WHERE s.type_objet = substr(f.numero, 1, 3) AND s.annee = CAST(substr(f.numero, 11, 2) AS INTEGER) "
                  "AND s.dernier_numero >= CAST(substr(f.numero, 5, 5) AS INTEGER))")
CK04_SANS_LIGNES = "SELECT f.id FROM factures f WHERE NOT EXISTS (SELECT 1 FROM facture_lignes l WHERE l.facture_id = f.id)"
CK05_SOMME = ("SELECT f.id FROM factures f WHERE (SELECT COALESCE(SUM(CAST(REPLACE(l.montant_ht, '.', '') AS INTEGER)), 0) FROM facture_lignes l "
              "WHERE l.facture_id = f.id) <> CAST(REPLACE(f.total_ht, '.', '') AS INTEGER)")
CK06_NETTE = ("SELECT b.id FROM bons_commande b WHERE CAST(REPLACE(b.montant_deja_facture_ht, '.', '') AS INTEGER) <> " + NETTE_BC.format(b="b"))
CK06_DATE_100 = ("SELECT b.id FROM bons_commande b WHERE b.date_100_facture IS NOT (SELECT MIN(s.date_emission) FROM factures s "
                 "WHERE s.bc_id = b.id AND s.type = 'solde' AND NOT " + NEUTRALISEE.format(a="s") + ")")
CK06_AVANCEMENT_SOLDE = ("SELECT b.id FROM bons_commande b WHERE EXISTS (SELECT 1 FROM factures s WHERE s.bc_id = b.id AND s.type = 'solde' "
                         "AND NOT " + NEUTRALISEE.format(a="s") + ") AND b.avancement <> '100.00'")
CK14_DEVIS_APRES_SOLDE = ("SELECT l.devis_id FROM bc_devis l WHERE EXISTS (SELECT 1 FROM factures s WHERE s.bc_id = l.bc_id AND s.type = 'solde' "
                          "AND s.created_at < l.created_at)")
# CK-16 : lignes d'avancement d'une situation — (a) ligne de BC existant au moment de l'émission sans ligne d'avancement ; (b) ligne d'avancement
# en double ; (c) ligne d'avancement d'une ligne de BC étrangère au BC de la facture ; (d) ligne d'avancement dans une facture qui n'est pas une situation
CK16_MANQUANTE = ("SELECT f.id, bl.id FROM factures f JOIN bc_lignes bl ON bl.bc_id = f.bc_id WHERE f.type = 'situation' AND bl.created_at <= f.created_at "
                  "AND NOT EXISTS (SELECT 1 FROM facture_lignes l WHERE l.facture_id = f.id AND l.type_ligne = 'avancement' AND l.bc_ligne_id = bl.id)")
CK16_DOUBLON = ("SELECT facture_id, bc_ligne_id FROM facture_lignes WHERE type_ligne = 'avancement' GROUP BY facture_id, bc_ligne_id HAVING count(*) > 1")
CK16_ETRANGERE = ("SELECT l.id FROM facture_lignes l JOIN factures f ON f.id = l.facture_id JOIN bc_lignes bl ON bl.id = l.bc_ligne_id "
                  "WHERE bl.bc_id <> f.bc_id")
CK16_HORS_SITUATION = ("SELECT l.id FROM facture_lignes l JOIN factures f ON f.id = l.facture_id WHERE l.type_ligne = 'avancement' AND f.type <> 'situation'")
CK16 = {"manquante": CK16_MANQUANTE, "doublon": CK16_DOUBLON, "etrangere": CK16_ETRANGERE, "hors_situation": CK16_HORS_SITUATION}
# CK-17 : un montant de situation égal à X − N, X étant recalculé à partir des seuls pourcentages cumulés des lignes d'avancement (formule figée, centimes entiers)
CK17_FORMULE = (
    "WITH lignes AS ("
    "  SELECT f.id AS fid, dl.devis_id AS did, CAST(REPLACE(bl.total_ht, '.', '') AS INTEGER) AS b, "
    "         CAST(REPLACE(l.avancement_cumule_pct, '.', '') AS INTEGER) AS p "
    "    FROM factures f JOIN facture_lignes l ON l.facture_id = f.id AND l.type_ligne = 'avancement' "
    "    JOIN bc_lignes bl ON bl.id = l.bc_ligne_id JOIN devis_lignes dl ON dl.id = bl.devis_ligne_id WHERE f.type = 'situation'), "
    "par_devis AS ("
    "  SELECT fid, did, SUM(b) AS B, SUM((b * p + 5000) / 10000) AS G FROM lignes GROUP BY fid, did), "
    "valeur AS ("
    "  SELECT pd.fid, SUM(pd.G - CASE WHEN pd.B = 0 THEN 0 ELSE (2 * (pd.B - CAST(REPLACE(d.total_ht, '.', '') AS INTEGER)) * pd.G + pd.B) / (2 * pd.B) END) AS X "
    "    FROM par_devis pd JOIN devis d ON d.id = pd.did GROUP BY pd.fid) "
    "SELECT f.id FROM factures f LEFT JOIN valeur v ON v.fid = f.id WHERE f.type = 'situation' "
    "AND CAST(REPLACE(f.total_ht, '.', '') AS INTEGER) IS NOT COALESCE(v.X, 0) - CAST(REPLACE(f.montant_deja_facture_ht, '.', '') AS INTEGER)")


# --------------------------------------------------------------------------------------------------------------------
# Fabrique : BC, factures, lignes, services (reproduits côté test ; aucune règle de service n'est portée par le schéma)
# --------------------------------------------------------------------------------------------------------------------
class Base9(C.Base8):
    """Base au rang 9. Les fabriques de devis, BC et lignes viennent de test_005b ; les services de facturation sont reproduits ici."""

    ts_lignes = TS

    DECALAGES = (("clients", 10), ("devis", 20), ("devis_lignes", 30), ("bons_commande", 40), ("bc_lignes", 50), ("bc_devis", 60), ("factures", 70),
                 ("facture_lignes", 80))

    def setUp(self):
        self.db = migrer9()
        self._n = 0
        self.desynchroniser_ids()

    def desynchroniser_ids(self):
        """Les compteurs AUTOINCREMENT démarrent à des valeurs différentes : un identifiant de client, de BC, de devis, de facture ou de ligne ne
        vaut jamais celui d'une autre table. Sans cela, une jointure sur la mauvaise colonne (bc_id au lieu de client_id, id au lieu de devis_id)
        donnerait par hasard le bon résultat dans un jeu de test où tout vaut 1."""
        for nom, seq in self.DECALAGES:
            if self.db.execute("UPDATE sqlite_sequence SET seq=? WHERE name=?", (seq, nom)).rowcount == 0:                # ligne déjà créée par un jeu de données de migration
                self.db.execute("INSERT INTO sqlite_sequence (name, seq) VALUES (?, ?)", (nom, seq))

    def isole(self, gardes):
        """Base du rang 9 dont tous les triggers sont supprimés sauf `gardes`."""
        t = Base9()
        t.db = migrer9()
        t._n = 0
        for (nom,) in t.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
            if nom not in gardes:
                t.db.execute(f"DROP TRIGGER {nom}")
        return t

    def sans_triggers(self):
        return self.isole(())

    # --- monde : un BC avec ses devis acceptés et leurs lignes --------------------------------------------------------
    def monde(self, devis=None, client_id=None):
        """BC en cours portant un ou plusieurs devis acceptés. `devis` : liste de dictionnaires
        {"lignes": [montants D2 des lignes], "total": total_ht du devis (par défaut Σ lignes), "acompte": (type, valeur)}.
        Retourne b, cli, d (devis), bl (lignes de BC par devis), lignes (toutes les lignes de BC), spec."""
        devis = devis or [{"lignes": ["4000.00", "2000.00"]}]
        cli = client_id or self.client()
        ds, bls = [], []
        for i, spec in enumerate(devis, 1):
            brut = sum(c(m) for m in spec["lignes"])
            at, av = spec.get("acompte", ("aucun", None))
            d = self.brouillon(client_id=cli, total_ht=spec.get("total", eur(brut)), acompte_type=at, acompte_valeur=av,
                               remise_type="aucune")
            for k, m in enumerate(spec["lignes"], 1):
                self.ligne(d, k, designation=f"Ligne {i}.{k}", quantite="1", prix_unitaire_ht=dl(m), total_ht=m)
            self.finaliser(d)
            self.accepter(d)
            ds.append(d)
        b = self.creer_bc(ds[0])
        for d in ds[1:]:
            self.rattacher(b, d)
        for d in ds:
            bls.append([r_[0] for r_ in self.tous("SELECT bl.id FROM bc_lignes bl JOIN devis_lignes dl ON dl.id = bl.devis_ligne_id "
                                                   "WHERE dl.devis_id = ? ORDER BY dl.ordre", d)])
        return types.SimpleNamespace(b=b, cli=cli, d=ds, bl=bls, lignes=[x for sous in bls for x in sous], spec=devis)

    def ajouter_devis(self, bc, lignes, total=None, acompte=("aucun", None), apres=False):
        """Rattache un devis accepté supplémentaire (service de rattachement : lien, copie des lignes, contractuel) et retourne (devis, lignes de BC).
        `apres=True` date les lignes de BC copiées APRÈS toute situation émise (created_at 2099) : elles ne sont pas « applicables » aux situations déjà émises ;
        `apres="<horodatage>"` les date à cet instant précis (pour intercaler l'ajout entre deux émissions)."""
        brut = sum(c(m) for m in lignes)
        d = self.brouillon(client_id=bc.cli, total_ht=total or eur(brut), acompte_type=acompte[0], acompte_valeur=acompte[1], remise_type="aucune")
        for k, m in enumerate(lignes, 1):
            self.ligne(d, k, designation=f"Ligne +{k}", quantite="1", prix_unitaire_ht=dl(m), total_ht=m)
        self.finaliser(d)
        self.accepter(d)
        self.ts_lignes = apres if isinstance(apres, str) else (TS_APRES if apres else TS)
        try:
            self.rattacher(bc.b, d)
        finally:
            self.ts_lignes = TS
        nouvelles = [r_[0] for r_ in self.tous("SELECT bl.id FROM bc_lignes bl JOIN devis_lignes dl ON dl.id = bl.devis_ligne_id "
                                                "WHERE dl.devis_id = ? ORDER BY dl.ordre", d)]
        bc.d.append(d)
        bc.bl.append(nouvelles)
        bc.lignes.extend(nouvelles)
        return d, nouvelles

    def copier_lignes(self, b, d, max_ordre=99):
        """Copie 1:1 des lignes (et garanties) du devis `d` dans le BC, avec created_at = self.ts_lignes (TS par défaut) : l'exhaustivité d'une
        situation (CK-16) s'apprécie par rapport à la date de création des lignes de BC."""
        decalage = self.un("SELECT COALESCE(MAX(ordre), 0) FROM bc_lignes WHERE bc_id=?", b)[0]
        self.db.execute("INSERT INTO bc_lignes (bc_id, devis_ligne_id, ordre, prestation_id, reference_prestation, designation, "
                        "description, quantite, unite, prix_unitaire_ht, remise_type, remise_valeur, type_prestation, total_ht, created_at, updated_at) "
                        "SELECT ?, dl.id, dl.ordre + ?, dl.prestation_id, dl.reference_prestation, dl.designation, dl.description, "
                        "dl.quantite, dl.unite, dl.prix_unitaire_ht, dl.remise_type, dl.remise_valeur, dl.type_prestation, dl.total_ht, ?, ? "
                        "FROM devis_lignes dl WHERE dl.devis_id = ? AND dl.ordre <= ? ORDER BY dl.ordre", (b, decalage, self.ts_lignes, self.ts_lignes, d, max_ordre))
        self.db.execute("INSERT INTO bc_ligne_garanties (ligne_id, garantie_type) SELECT bl.id, dg.garantie_type "
                        "FROM bc_lignes bl JOIN devis_ligne_garanties dg ON dg.ligne_id = bl.devis_ligne_id "
                        "JOIN devis_lignes dl ON dl.id = bl.devis_ligne_id WHERE bl.bc_id = ? AND dl.devis_id = ?", (b, d))

    # --- états du BC ------------------------------------------------------------------------------------------------
    def etat(self, bc, etat):
        b = bc.b if hasattr(bc, "b") else bc
        if etat in ("gele", "termine", "annule_gele"):
            self.geler_bc(b)
        if etat == "termine":
            self.terminer_bc(b)
        if etat in ("annule", "annule_gele"):
            self.annuler_bc(b)

    def revenir_en_cours(self, bc):
        """Recalcul financier dérivé (INV-42) : un BC dont le solde est totalement crédité repasse 'en_cours' (un seul UPDATE)."""
        b = bc.b if hasattr(bc, "b") else bc
        self.db.execute("UPDATE bons_commande SET statut='en_cours', completed_at=NULL, date_100_facture=NULL, avancement='50.00', updated_at=? WHERE id=?",
                        (TS2, b))

    # --- factures brutes -------------------------------------------------------------------------------------------------
    def numero(self, type_, date):
        pre = PREFIXES[type_]
        yy = date[2:4] if isinstance(date, str) and len(date) >= 4 else "26"
        return f"{pre}-{self.un(ATTRIBUER, pre, int(yy))[0]:05d}-{yy}"

    def cols_facture(self, bc, type_, total, **kw):
        b = bc.b if hasattr(bc, "b") else bc
        s = self.un("SELECT client_id, client_snapshot, client_snapshot_version, entreprise_snapshot, entreprise_snapshot_version, "
                    "chantier_snapshot, chantier_snapshot_version FROM bons_commande WHERE id=?", b)
        date = kw.get("date_emission", "2026-10-05")
        cols = {"type": type_, "bc_id": b, "created_at": TS_EMISSION, "client_id": s[0], "client_snapshot": s[1], "client_snapshot_version": s[2], "entreprise_snapshot": s[3],
                "entreprise_snapshot_version": s[4], "chantier_snapshot": s[5], "chantier_snapshot_version": s[6], "date_emission": date,
                "total_ht": total}
        if type_ != "avoir":
            cols["date_echeance"] = kw.get("date_echeance", "2026-11-04")
        else:
            cols["motif_avoir"] = "Erreur de facturation"
        cols.update(kw)
        if "numero" not in cols:
            cols["numero"] = self.numero(type_, cols.get("date_emission"))
        return {k: v for k, v in cols.items() if v is not OMIT}

    def inserer(self, table, cols, verbe="INSERT"):
        return self.db.execute(f"{verbe} INTO {table} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values())).lastrowid

    def facture(self, bc, type_, total, **kw):
        """Insertion brute d'une facture (colonnes obligatoires pré-remplies ; `kw` remplace, OMIT retire)."""
        return self.inserer("factures", self.cols_facture(bc, type_, total, **kw))

    def ligne_f(self, f, ordre, type_ligne, montant, bc_ligne_id=None, **kw):
        cols = {"facture_id": f, "ordre": ordre, "designation": f"Ligne {ordre}", "quantite": "1", "unite": "ens",
                "prix_unitaire_ht": dl(montant) or "0", "remise_type": "aucune", "type_ligne": type_ligne, "montant_ht": montant}
        if bc_ligne_id is not None:
            cols["bc_ligne_id"] = bc_ligne_id
        cols.update(kw)
        return self.inserer("facture_lignes", {k: v for k, v in cols.items() if v is not OMIT})

    # --- état dérivé, calculé côté « service » (indépendant du SQL des triggers) ---------------------------------------
    def total(self, f):
        return c(self.un("SELECT total_ht FROM factures WHERE id=?", f)[0])

    def neutralisee(self, f):
        t = self.total(f)
        return t > 0 and sum(c(x) for (x,) in self.tous("SELECT total_ht FROM factures WHERE origine_facture_id=?", f)) == t

    def nette(self, b):
        b = b.b if hasattr(b, "b") else b
        return sum((-1 if ty == "avoir" else 1) * c(t) for ty, t in self.tous("SELECT type, total_ht FROM factures WHERE bc_id=?", b))

    def contractuel(self, b):
        b = b.b if hasattr(b, "b") else b
        return sum(c(t) for (t,) in self.tous("SELECT d.total_ht FROM bc_devis l JOIN devis d ON d.id = l.devis_id WHERE l.bc_id=?", b))

    def rho(self, b, avant=None):
        """Référence ρ : la situation non neutralisée d'ordinal le plus grand (parmi les ordinaux < avant si fourni). None s'il n'y en a pas."""
        b = b.b if hasattr(b, "b") else b
        candidats = [(num, fid) for fid, num in self.tous("SELECT id, situation_numero FROM factures WHERE bc_id=? AND type='situation'", b)
                     if (avant is None or num < avant) and not self.neutralisee(fid)]
        return max(candidats)[1] if candidats else None

    def precedents(self, b, avant=None):
        """{bc_ligne_id: avancement cumulé (centièmes) dans la situation de référence} ; vide si pas de référence."""
        f = self.rho(b, avant)
        if f is None:
            return {}
        return {bl: c(p) for bl, p in self.tous("SELECT bc_ligne_id, avancement_cumule_pct FROM facture_lignes WHERE facture_id=? AND type_ligne='avancement'", f)}

    def lignes_de_bc(self, b):
        b = b.b if hasattr(b, "b") else b
        return self.tous("SELECT bl.id, dl.devis_id, bl.total_ht FROM bc_lignes bl JOIN devis_lignes dl ON dl.id = bl.devis_ligne_id WHERE bl.bc_id=? ORDER BY bl.ordre", b)

    def calcul_situation(self, bc, pcts, avant=None):
        """Service : g, r, X, N, M d'une nouvelle situation. `pcts` : {bc_ligne_id: P cumulé en centièmes}. Une ligne absente de `pcts` garde son précédent."""
        b = bc.b if hasattr(bc, "b") else bc
        prec = self.precedents(b, avant)
        par_devis, lignes = {}, []
        for bl, did, tot in self.lignes_de_bc(b):
            p = pcts.get(bl, prec.get(bl, 0))
            par_devis.setdefault(did, []).append((c(tot), p))
            lignes.append((bl, did, c(tot), prec.get(bl, 0), p, g(c(tot), p)))
        devis = [(l_, c(self.un("SELECT total_ht FROM devis WHERE id=?", did)[0])) for did, l_ in par_devis.items()]
        X, detail = valeur_cumulee(devis)
        N = self.nette(b)
        return types.SimpleNamespace(lignes=lignes, X=X, N=N, M=X - N, detail=detail, devis=list(par_devis), reductions={did: d[3] for did, d in zip(par_devis, detail)})

    def emettre_situation(self, bc, pcts, numero=None, confirmer_non_positif=False, **kw):
        """Service d'émission d'une situation : calcule, vérifie M > 0, pose situation_numero = 1 + MAX, insère la facture puis TOUTES ses lignes
        (une ligne d'avancement par ligne de BC, puis les déductions : remise de chaque devis et facturation nette antérieure)."""
        b = bc.b if hasattr(bc, "b") else bc
        k = self.calcul_situation(bc, pcts)
        if k.M <= 0 and not confirmer_non_positif:
            raise ValueError(f"M = {k.M} : une situation doit être strictement positive")
        num = numero or self.un("SELECT COALESCE(MAX(situation_numero), 0) + 1 FROM factures WHERE bc_id=?", b)[0]
        f = self.facture(bc, "situation", eur(k.M), situation_numero=num, montant_deja_facture_ht=eur(k.N), **kw)
        o = 0
        for bl, did, tot, prec, p, valeur in k.lignes:
            o += 1
            self.ligne_f(f, o, "avancement", eur(valeur), bl, avancement_precedent_pct=eur(prec), avancement_cumule_pct=eur(p))
        for did, red in k.reductions.items():
            if red > 0:
                o += 1
                self.ligne_f(f, o, "deduction", eur(-red))
        if k.N > 0:
            o += 1
            self.ligne_f(f, o, "deduction", eur(-k.N))
        return f

    def acompte(self, bc, devis, total, **kw):
        f = self.facture(bc, "acompte", total, devis_id=devis, **kw)
        self.ligne_f(f, 1, "synthese", total)
        return f

    def solde(self, bc, **kw):
        """Service d'émission du solde : total = contractuel − N ; lignes = lignes de BC, remise globale de chaque devis, facturation antérieure."""
        b = bc.b if hasattr(bc, "b") else bc
        N, Ctr = self.nette(b), self.contractuel(b)
        total = Ctr - N
        f = self.facture(bc, "solde", eur(total), **kw)
        o, brut = 0, {}
        for bl, did, tot in self.lignes_de_bc(b):
            o += 1
            self.ligne_f(f, o, "prestation", tot, bl)
            brut[did] = brut.get(did, 0) + c(tot)
        for did, B in brut.items():
            remise = B - c(self.un("SELECT total_ht FROM devis WHERE id=?", did)[0])
            if remise > 0:
                o += 1
                self.ligne_f(f, o, "deduction", eur(-remise))
        if N > 0:
            o += 1
            self.ligne_f(f, o, "deduction", eur(-N))
        return f

    def avoir(self, origine, total=None, **kw):
        """Avoir sur `origine` (total par défaut : avoir total) ; ligne synthèse du montant."""
        b, tot = self.un("SELECT bc_id, total_ht FROM factures WHERE id=?", origine)
        total = total or tot
        cols = self.cols_facture(b, "avoir", total, origine_facture_id=origine, **kw)
        f = self.inserer("factures", cols)
        self.ligne_f(f, 1, "synthese", total)
        return f

    def devis_de(self, bc, i=0):
        return bc.d[i]

    def tente(self, sql, *args):
        """Exécute l'instruction puis l'annule (SAVEPOINT) : None si elle réussit, sinon le message de l'erreur d'intégrité."""
        self.db.execute("SAVEPOINT tente")
        try:
            self.db.execute(sql, self._a(args))
            return None
        except sqlite3.IntegrityError as e:
            return str(e)
        finally:
            self.db.execute("ROLLBACK TO tente")
            self.db.execute("RELEASE tente")

    def tente_f(self, bc, type_, total, **kw):
        """Insertion brute d'une facture annulée juste après : None si acceptée, sinon le message d'erreur."""
        self.db.execute("SAVEPOINT tentef")
        try:
            self.facture(bc, type_, total, **kw)
            return None
        except sqlite3.IntegrityError as e:
            return str(e)
        finally:
            self.db.execute("ROLLBACK TO tentef")
            self.db.execute("RELEASE tentef")

    def refuse_f(self, inv, bc, type_, total, **kw):
        """La facture est refusée par un trigger dont le message porte `inv`."""
        m = self.tente_f(bc, type_, total, **kw)
        self.assertIsNotNone(m, f"facture {type_} {total} acceptée à tort")
        self.assertRegex(m, inv)

    def refuse_check_f(self, bc, type_, total, **kw):
        """La facture est refusée par une contrainte (aucun préfixe INV-)."""
        m = self.tente_f(bc, type_, total, **kw)
        self.assertIsNotNone(m, f"facture {type_} {total} acceptée à tort")
        self.assertNotIn("INV-", m)

    def accepte_f(self, bc, type_, total, **kw):
        m = self.tente_f(bc, type_, total, **kw)
        self.assertIsNone(m, m)

    def ck(self, sql, *args):
        """Résultat d'une requête de diagnostic (liste de lignes en violation)."""
        return self.tous(sql, *args)


# --------------------------------------------------------------------------------------------------------------------
# Services de facturation reproduits côté test (le schéma n'en porte aucun : plafond de l'acompte prévu, confirmation du solde à 0.00,
# caches du BC, date_100_facture). Ils servent à fabriquer des états conformes et à éprouver la frontière SQL / service.
# --------------------------------------------------------------------------------------------------------------------
class ErreurService(Exception):
    """Refus d'une règle de SERVICE (jamais levé par SQLite)."""


def prevu_acompte(self, devis_id):
    """Acompte prévu d'un devis (centimes) : pourcentage -> devis.total_ht × pct (HALF_UP, une fois) ; montant -> acompte_valeur ; aucun -> 0."""
    typ, val, total = self.un("SELECT acompte_type, acompte_valeur, total_ht FROM devis WHERE id=?", devis_id)
    if typ == "aucun":
        return 0
    if typ == "montant":
        return c(val)
    return (c(total) * c(val) + 5000) // 10000


def prevu_bc(self, bc):
    """Acompte prévu du BC : donnée DÉRIVÉE = Σ des acomptes prévus des devis actuellement rattachés (aucun pourcentage recalculé sur le contractuel)."""
    b = bc.b if hasattr(bc, "b") else bc
    return sum(self.prevu_acompte(d) for (d,) in self.tous("SELECT devis_id FROM bc_devis WHERE bc_id=?", b))


def emettre_acompte(self, bc, devis, total, **kw):
    """Service d'émission d'un acompte : le total ne dépasse pas l'acompte PRÉVU du devis (aucun -> aucun acompte) ; puis insertion SQL."""
    prevu = self.prevu_acompte(devis)
    if prevu == 0:
        raise ErreurService("devis sans acompte prévu")
    if c(total) > prevu:
        raise ErreurService("acompte supérieur à l'acompte prévu")
    return self.acompte(bc, devis, total, **kw)


def emettre_solde(self, bc, confirmer_zero=False, **kw):
    """Service d'émission du solde : un solde à 0.00 exige une confirmation explicite."""
    b = bc.b if hasattr(bc, "b") else bc
    if self.contractuel(b) - self.nette(b) == 0 and not confirmer_zero:
        raise ErreurService("solde à 0.00 : confirmation requise")
    return self.solde(bc, **kw)


def neutraliser(self, origine, **kw):
    """Avoir du RESTE à créditer de la facture (neutralisation totale quel que soit l'historique des avoirs partiels)."""
    reste = self.total(origine) - sum(c(x) for (x,) in self.tous("SELECT total_ht FROM factures WHERE origine_facture_id=?", origine))
    return self.avoir(origine, eur(reste), **kw)


def soldes_actifs(self, b):
    b = b.b if hasattr(b, "b") else b
    return [(d, i) for i, d in self.tous("SELECT id, date_emission FROM factures WHERE bc_id=? AND type='solde'", b) if not self.neutralisee(i)]


def recalcul_bc(self, bc, regle=True):
    """Service financier (INV-46) : recalcule les caches du BC en UN SEUL UPDATE. `regle` : tout est encaissé (007 absent en 006 : état posé par le test).
    BC annulé : seuls les trois caches financiers évoluent ; statut, completed_at, frozen_at restent intacts (VR-05)."""
    b = bc.b if hasattr(bc, "b") else bc
    nette, ctr = self.nette(b), self.contractuel(b)
    actifs = self.soldes_actifs(b)
    avanc = 10000 if actifs else (min(10000, (2 * nette * 10000 + ctr) // (2 * ctr)) if ctr else 0)
    d100 = min(d for d, _ in actifs) if actifs else None
    statut = self.un("SELECT statut FROM bons_commande WHERE id=?", b)[0]
    if statut == "annule":
        self.db.execute("UPDATE bons_commande SET montant_deja_facture_ht=?, avancement=?, date_100_facture=?, updated_at=? WHERE id=?",
                        (eur(nette), eur(avanc), d100, TS2, b))
    elif actifs and regle:
        self.db.execute("UPDATE bons_commande SET montant_deja_facture_ht=?, avancement=?, date_100_facture=?, statut='termine', "
                        "completed_at=COALESCE(completed_at, ?), frozen_at=COALESCE(frozen_at, ?), updated_at=? WHERE id=?",
                        (eur(nette), eur(avanc), d100, TS, TS, TS2, b))
    else:
        self.db.execute("UPDATE bons_commande SET montant_deja_facture_ht=?, avancement=?, date_100_facture=?, statut='en_cours', completed_at=NULL, "
                        "updated_at=? WHERE id=?", (eur(nette), eur(avanc), d100, TS2, b))


def etat_bc(self, bc):
    b = bc.b if hasattr(bc, "b") else bc
    return self.un("SELECT statut, completed_at, date_100_facture, avancement, montant_deja_facture_ht FROM bons_commande WHERE id=?", b)


def clients_et_snapshots(self, bc):
    b = bc.b if hasattr(bc, "b") else bc
    return self.un("SELECT client_id, client_snapshot FROM bons_commande WHERE id=?", b)


def fixer_date(self, type_objet, annee, date):
    """Service : écrit derniere_date de la séquence (la ligne existe, créée par l'attribution du numéro)."""
    n = self.db.execute("UPDATE numerotation_sequences SET derniere_date=?, updated_at=? WHERE type_objet=? AND annee=?", (date, TS2, type_objet, annee)).rowcount
    self.assertEqual(n, 1)


for _f in (fixer_date, neutraliser, prevu_acompte, prevu_bc, emettre_acompte, emettre_solde, soldes_actifs, recalcul_bc, etat_bc, clients_et_snapshots):
    setattr(Base9, _f.__name__, _f)


# ====================================================================================================================
# A — chaîne de migration
# ====================================================================================================================
def code_sql():
    return T.sans_commentaires(SQL_006)


def monter_depuis_rang_6():
    """Base peuplée au rang 6 portée au rang 9 par la chaîne réelle (005b par le runner, 005c et 006 comme migrations ordinaires)."""
    t = T.base6_peuplee()
    T.runner(t.db, 7)
    T.appliquer(t.db, 8, C.SQL_005C)
    return t


class Chaine(Base9):
    """Groupe A : 001 → … → 005c → 006, rang 9, aucune régression de la chaîne."""

    def test_T48_A_fichiers_de_la_chaine_dans_l_ordre(self):
        self.assertEqual([p.name for p in sorted(MIGRATIONS.glob("*.sql"))[:9]], list(NOMS))
        self.assertEqual(NOMS[-1], "006_facturation.sql")
        self.assertEqual(len(NOMS), RANG)

    def test_T48_A_rang_et_user_version(self):
        db = C.migrer8()
        self.assertEqual(T.db_user_version(db), 8)
        T.appliquer(db, RANG, SQL_006)
        self.assertEqual(T.db_user_version(db), 9)
        self.assertEqual(T.db_user_version(self.db), 9)
        self.assertEqual(self.un("PRAGMA foreign_keys")[0], 1)
        self.assertEqual(self.un("PRAGMA recursive_triggers")[0], 1)
        self.assertEqual(self.tous("PRAGMA integrity_check"), [("ok",)])
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])

    def test_T48_A_le_protocole_de_reconstruction_du_runner_est_accepte(self):
        db = C.migrer8()
        T.runner(db, RANG, SQL_006)
        self.assertEqual(T.db_user_version(db), 9)
        self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        self.assertEqual(T.objets(db), T.objets(self.db))

    def test_T48_A_le_fichier_ne_contient_que_des_creations_sans_transaction_ni_pragma_ni_donnee(self):
        code = code_sql()
        for interdit in (r"\bPRAGMA\b", r"\bCOMMIT\b", r"\bROLLBACK\b", r"\bSAVEPOINT\b", r"BEGIN\s+(IMMEDIATE|DEFERRED|EXCLUSIVE|TRANSACTION)",
                         r"\bALTER\b", r"\bDROP\b", r"\bINSERT\s+INTO\b", r"\bUPDATE\s+\w+\s+SET\b", r"\bDELETE\s+FROM\b", r"\bREPLACE\s+INTO\b",
                         r"\bINSERT\s+OR\b", r"\bCREATE\s+(VIEW|TEMP|TEMPORARY|VIRTUAL)\b", r"\bRETURNING\b", r"\bON\s+UPDATE\b", r"\bCASCADE\b",
                         r"\bON\s+CONFLICT\b"):
            self.assertIsNone(re.search(interdit, code, re.I), interdit)
        sts = [T.sans_commentaires(s).strip() for s in T.instructions(SQL_006)]
        genres = [re.match(r"CREATE\s+(UNIQUE\s+)?(TABLE|INDEX|TRIGGER)", s).group(0).split()[-1] for s in sts]
        self.assertEqual({g_: genres.count(g_) for g_ in ("TABLE", "INDEX", "TRIGGER")}, {"TABLE": 2, "INDEX": 9, "TRIGGER": 12})
        self.assertEqual(len(sts), 23)
        self.assertTrue(all(s.endswith(";") for s in sts))

    def test_T48_A_objets_exacts_au_rang_9(self):
        self.assertEqual(T.noms(self.db, "table") - {"sqlite_sequence"}, TABLES_RANG9)
        self.assertEqual(T.noms(self.db, "view"), set())
        nommes = {n for n in T.noms(self.db, "index") if not n.startswith("sqlite_")}
        self.assertEqual(nommes, T.INDEXES_RANG7 | INDEXES_006)
        triggers9 = {n for n in T.noms(self.db, "trigger")}
        triggers8 = T.noms(C.migrer8(), "trigger")
        self.assertEqual(triggers9 - triggers8, set(TRIGGERS_006))
        self.assertEqual(triggers8 - triggers9, set())
        for nom, table in TRIGGERS_006.items():
            self.assertEqual(self.un("SELECT tbl_name FROM sqlite_master WHERE name=?", nom)[0], table, nom)

    def test_T48_A_les_objets_du_rang_8_sont_identiques_au_caractere_pres(self):
        o8 = {(t, n, tb): s for t, n, tb, s in T.objets(C.migrer8())}
        o9 = {(t, n, tb): s for t, n, tb, s in T.objets(self.db)}
        self.assertEqual(set(o9) - set(o8), {("table", "factures", "factures"), ("table", "facture_lignes", "facture_lignes")}
                         | {("index", n, "factures") for n in INDEXES_006 if "facture_lignes" not in n and n not in ("uq_facture_lignes_avancement",)}
                         | {("index", n, "facture_lignes") for n in ("idx_facture_lignes_bc_ligne_id", "uq_facture_lignes_avancement")}
                         | {("trigger", n, t) for n, t in TRIGGERS_006.items()})
        self.assertEqual(set(o8) - set(o9), set())
        for cle, sql in o8.items():
            self.assertEqual(o9[cle], sql, cle)

    def test_T48_A_aucune_donnee_n_est_modifiee_par_la_migration(self):
        t8 = C.Base8()
        t8.setUp()
        for etat in T.ETATS_BC:
            t8.bc_en_etat(etat)
        avant = T.tout(t8.db)
        self.assertTrue(avant["bons_commande"])
        T.appliquer(t8.db, RANG, SQL_006)
        apres = T.tout(t8.db)
        self.assertEqual(apres.pop("factures"), [])
        self.assertEqual(apres.pop("facture_lignes"), [])
        self.assertEqual(apres, avant)                                                       # y compris sqlite_sequence : rien pour les nouvelles tables
        self.assertEqual(T.db_user_version(t8.db), 9)

    def test_T48_A_migration_d_une_base_peuplee_du_rang_6_ids_et_sequences_conserves(self):
        t = monter_depuis_rang_6()
        avant = T.tout(t.db)
        T.appliquer(t.db, RANG, SQL_006)
        apres = T.tout(t.db)
        self.assertEqual(apres.pop("factures"), [])
        self.assertEqual(apres.pop("facture_lignes"), [])
        self.assertEqual(apres, avant)
        self.assertEqual(self.tous.__func__(types.SimpleNamespace(db=t.db, _a=staticmethod(C.Base8._a)), "PRAGMA foreign_key_check"), [])
        self.assertEqual(t.db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])

    def test_T48_A_schema_identique_base_fraiche_et_base_migree_peuplee(self):
        t = monter_depuis_rang_6()
        T.appliquer(t.db, RANG, SQL_006)
        self.assertEqual(T.objets(t.db), T.objets(self.db))

    def test_T48_A_atomicite_un_echec_n_importe_ou_annule_tout(self):
        points = ["CREATE TABLE factures (", "CREATE TABLE facture_lignes (", "CREATE INDEX idx_factures_bc_id", "CREATE UNIQUE INDEX uq_factures_bc_situation_numero",
                  "CREATE UNIQUE INDEX uq_facture_lignes_avancement", "CREATE TRIGGER tr_20_factures_no_update", "CREATE TRIGGER tr_02_factures_chronologie",
                  "CREATE TRIGGER tr_22_factures_acompte", "CREATE TRIGGER tr_22_facture_lignes_insert", "CREATE TRIGGER tr_99_bc_devis_apres_solde"]
        db0 = C.migrer8()
        avant = T.objets(db0)
        for point in points:
            with self.subTest(point=point):
                self.assertEqual(SQL_006.count(point), 1, point)
                coupe = SQL_006.replace(point, "SELECT * FROM table_qui_n_existe_pas;\n" + point, 1)
                db = C.migrer8()
                with self.assertRaises(sqlite3.Error):
                    T.runner(db, RANG, coupe)
                self.assertFalse(db.in_transaction)
                self.assertEqual(T.db_user_version(db), 8)
                self.assertEqual(T.objets(db), avant)
        with self.subTest(point="apres la derniere instruction"):
            db = C.migrer8()
            with self.assertRaises(sqlite3.Error):
                T.runner(db, RANG, SQL_006 + "\nSELECT * FROM table_qui_n_existe_pas;\n")
            self.assertEqual(T.db_user_version(db), 8)
            self.assertEqual(T.objets(db), avant)

    def test_T48_A_rejeu_sur_une_base_deja_au_rang_9_est_refuse_sans_effet(self):
        avant = T.objets(self.db)
        with self.assertRaises(sqlite3.Error):
            T.runner(self.db, RANG, SQL_006)
        self.assertEqual(T.objets(self.db), avant)
        self.assertEqual(T.db_user_version(self.db), 9)

    def test_T48_A_006_exige_le_rang_8_les_tables_du_bc_et_des_devis(self):
        db = T.migrer(7)                                                                      # sans 005c : 006 s'applique techniquement, mais le rang attendu est 8
        self.assertEqual(T.db_user_version(db), 7)
        db = T.migrer(5)                                                                      # sans bc_devis : les triggers sont créés mais ne peuvent pas être exécutés
        with self.assertRaises(sqlite3.Error):
            T.appliquer(db, RANG, SQL_006)
        self.assertEqual(T.db_user_version(db), 5)

    def test_T48_A_le_fichier_ne_touche_ni_aux_tables_ni_aux_triggers_existants(self):
        code = code_sql()
        creees = set(re.findall(r"CREATE\s+(?:UNIQUE\s+)?(?:TABLE|INDEX|TRIGGER)\s+(\w+)", code))
        self.assertEqual(creees, {"factures", "facture_lignes"} | INDEXES_006 | set(TRIGGERS_006))
        existants = {n for n in T.noms(C.migrer8(), "table") | T.noms(C.migrer8(), "index") | T.noms(C.migrer8(), "trigger")}
        self.assertEqual(creees & existants, set())

    def test_T48_A_aucune_dependance_aux_tranches_suivantes_ni_a_une_structure_hors_perimetre(self):
        code = code_sql().lower()
        for hors in ("reglements", "garanties", "urssaf", "historique", "documents", "parametres_entreprise", "tva", "ttc", "taux_", "exoneration",
                     "situation_mode", "situation_valeur_saisie", "montant_contractuel_ht", "legacy_numero", "frozen_at", "cancelled_at",
                     "motif_annulation", "updated_at", "date_100_facture", "completed_at", "sequence_high_water", "machine"):
            self.assertNotIn(hors, code, hors)
        for table in ("bc_ligne_garanties", "depenses", "devis_revisions"):
            self.assertNotRegex(code, r"\b" + table + r"\b", table)

    def test_T48_A_les_ids_et_sequences_ne_sont_pas_crees_avant_la_premiere_ecriture(self):
        t = Base9()                                                                                   # base du rang 9 sans décalage d'identifiants
        t.db, t._n = migrer9(), 0
        self.assertEqual(t.tous("SELECT name FROM sqlite_sequence WHERE name IN ('factures', 'facture_lignes')"), [])
        bc = t.monde()
        t.facture(bc, "acompte", "10.00", devis_id=bc.d[0])
        self.assertEqual(t.tous("SELECT name, seq FROM sqlite_sequence WHERE name IN ('factures', 'facture_lignes')"), [("factures", 1)])


# ====================================================================================================================
# B — structure
# ====================================================================================================================
INFO_FACTURES = [
    ("id", "INTEGER", 0, None, 1, 0), ("numero", "TEXT", 1, None, 0, 0), ("type", "TEXT", 1, None, 0, 0), ("bc_id", "INTEGER", 1, None, 0, 0),
    ("client_id", "INTEGER", 1, None, 0, 0), ("devis_id", "INTEGER", 0, None, 0, 0), ("client_snapshot", "TEXT", 1, None, 0, 0),
    ("client_snapshot_version", "INTEGER", 1, None, 0, 0), ("entreprise_snapshot", "TEXT", 1, None, 0, 0),
    ("entreprise_snapshot_version", "INTEGER", 1, None, 0, 0), ("chantier_snapshot", "TEXT", 1, None, 0, 0),
    ("chantier_snapshot_version", "INTEGER", 1, None, 0, 0), ("objet", "TEXT", 0, None, 0, 0), ("date_emission", "TEXT", 1, None, 0, 0),
    ("date_echeance", "TEXT", 0, None, 0, 0), ("total_ht", "TEXT", 1, None, 0, 0), ("situation_numero", "INTEGER", 0, None, 0, 0),
    ("montant_deja_facture_ht", "TEXT", 0, None, 0, 0), ("origine_facture_id", "INTEGER", 0, None, 0, 0), ("motif_avoir", "TEXT", 0, None, 0, 0),
    ("created_at", "TEXT", 1, "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')", 0, 0), ("origine", "TEXT", 1, "'v6'", 0, 0), ("legacy_id", "TEXT", 0, None, 0, 0),
    ("legacy_data", "TEXT", 0, None, 0, 0)]
INFO_LIGNES = [
    ("id", "INTEGER", 0, None, 1, 0), ("facture_id", "INTEGER", 1, None, 0, 0), ("ordre", "INTEGER", 1, None, 0, 0), ("bc_ligne_id", "INTEGER", 0, None, 0, 0),
    ("reference_prestation", "TEXT", 0, None, 0, 0), ("designation", "TEXT", 1, None, 0, 0), ("description", "TEXT", 0, None, 0, 0),
    ("quantite", "TEXT", 1, None, 0, 0), ("unite", "TEXT", 1, None, 0, 0), ("prix_unitaire_ht", "TEXT", 1, None, 0, 0), ("remise_type", "TEXT", 1, None, 0, 0),
    ("remise_valeur", "TEXT", 0, None, 0, 0), ("type_ligne", "TEXT", 1, None, 0, 0), ("montant_ht", "TEXT", 1, None, 0, 0),
    ("avancement_precedent_pct", "TEXT", 0, None, 0, 0), ("avancement_cumule_pct", "TEXT", 0, None, 0, 0),
    ("created_at", "TEXT", 1, "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')", 0, 0)]


class Structure(Base9):
    """Groupe B : tables STRICT, colonnes exactes et types, FK, index, absences voulues, triggers gardiens."""

    def test_T48_B_factures_colonnes_exactes_types_nullite_defauts(self):
        self.assertEqual(T.colonnes(self.db, "factures"), COLONNES_FACTURES)
        self.assertEqual(T.info_colonnes(self.db, "factures"), INFO_FACTURES)

    def test_T48_B_facture_lignes_colonnes_exactes_types_nullite_defauts(self):
        self.assertEqual(T.colonnes(self.db, "facture_lignes"), COLONNES_LIGNES)
        self.assertEqual(T.info_colonnes(self.db, "facture_lignes"), INFO_LIGNES)

    def test_T48_B_tables_strict_et_autoincrement(self):
        for table in ("factures", "facture_lignes"):
            with self.subTest(table=table):
                self.assertTrue(T.est_strict(self.db, table))
                self.assertRegex(T.sql_de(self.db, table), r"id\s+INTEGER PRIMARY KEY AUTOINCREMENT")

    def test_T48_B_cles_etrangeres_toutes_en_restrict_sans_on_update(self):
        self.assertEqual(T.cles_etrangeres(self.db, "factures"), sorted([
            ("bons_commande", "bc_id", "id", "NO ACTION", "RESTRICT"), ("clients", "client_id", "id", "NO ACTION", "RESTRICT"),
            ("devis", "devis_id", "id", "NO ACTION", "RESTRICT"), ("factures", "origine_facture_id", "id", "NO ACTION", "RESTRICT")]))
        self.assertEqual(T.cles_etrangeres(self.db, "facture_lignes"), sorted([
            ("factures", "facture_id", "id", "NO ACTION", "RESTRICT"), ("bc_lignes", "bc_ligne_id", "id", "NO ACTION", "RESTRICT")]))

    def test_T48_B_index_exacts_et_unicites(self):
        att = {"factures": {("idx_factures_bc_id", 0, "c", 0), ("idx_factures_client_id", 0, "c", 0), ("idx_factures_devis_id", 0, "c", 0),
                            ("idx_factures_origine_facture_id", 0, "c", 0), ("idx_factures_type_date_echeance", 0, "c", 0),
                            ("idx_factures_date_emission", 0, "c", 0), ("uq_factures_bc_situation_numero", 1, "c", 0)},
               "facture_lignes": {("idx_facture_lignes_bc_ligne_id", 0, "c", 0), ("uq_facture_lignes_avancement", 1, "c", 1)}}
        for table, attendus in att.items():
            reels = {i for i in T.indexes_de(self.db, table) if not i[0].startswith("sqlite_autoindex")}
            self.assertEqual(reels, attendus, table)
        autos = [i for i in T.indexes_de(self.db, "factures") if i[0].startswith("sqlite_autoindex")]
        self.assertEqual(len(autos), 1)                                                       # UNIQUE(numero)
        autos = [i for i in T.indexes_de(self.db, "facture_lignes") if i[0].startswith("sqlite_autoindex")]
        self.assertEqual(len(autos), 1)                                                       # UNIQUE(facture_id, ordre)
        cols = lambda n: [r[2] for r in self.tous(f"PRAGMA index_info({n})")]
        self.assertEqual(cols("uq_factures_bc_situation_numero"), ["bc_id", "situation_numero"])
        self.assertEqual(cols("uq_facture_lignes_avancement"), ["facture_id", "bc_ligne_id"])
        self.assertEqual(cols("idx_factures_type_date_echeance"), ["type", "date_echeance"])
        self.assertRegex(T.sql_de(self.db, "uq_facture_lignes_avancement"), r"WHERE type_ligne = 'avancement'")
        self.assertNotRegex(T.sql_de(self.db, "uq_factures_bc_situation_numero"), r"\bWHERE\b")

    def test_T48_B_chaque_cle_etrangere_est_couverte_par_un_index(self):
        for table, cles in (("factures", ("bc_id", "client_id", "devis_id", "origine_facture_id")),
                            ("facture_lignes", ("facture_id", "bc_ligne_id"))):
            premieres = set()
            for (nom, *_x) in T.indexes_de(self.db, table):
                premieres.add(self.tous(f"PRAGMA index_info({nom})")[0][2])
            for cle in cles:
                self.assertIn(cle, premieres, f"{table}.{cle}")

    def test_T48_B_colonnes_absentes_par_choix_de_conception(self):
        for col in ("updated_at", "statut", "cancelled_at", "motif_annulation", "frozen_at", "date_validation", "date_paiement", "total_ttc",
                    "taux_tva", "montant_tva", "tva", "avoir_id", "legacy_numero", "situation_mode", "situation_valeur_saisie",
                    "montant_contractuel_ht", "avancement_cumule_pct", "avancement", "date_100_facture", "completed_at"):
            self.assertNotIn(col, T.colonnes(self.db, "factures"), col)
        for col in ("updated_at", "active", "type_prestation", "origine", "legacy_id", "legacy_data", "legacy_numero", "quantite_executee", "metre"):
            self.assertNotIn(col, T.colonnes(self.db, "facture_lignes"), col)

    def test_T48_B_aucune_table_de_reglement_garantie_ou_etat_de_facture(self):
        for table in ("reglements", "garanties", "historique", "documents", "parametres_entreprise", "acomptes", "situations", "soldes", "avoirs",
                      "facture_etats", "factures_neutralisees", "facture_taxes"):
            self.assertNotIn(table, T.noms(self.db, "table"), table)

    def test_T48_B_bloc_imp_de_factures_sans_legacy_numero_et_sans_bloc_imp_sur_les_lignes(self):
        for col in ("origine", "legacy_id", "legacy_data"):
            self.assertIn(col, T.colonnes(self.db, "factures"))
        self.assertEqual([c_ for c_ in T.colonnes(self.db, "facture_lignes") if c_.startswith("legacy") or c_ == "origine"], [])

    def test_T48_B_tous_les_triggers_de_006_sont_before_et_ne_font_que_garder(self):
        for nom in TRIGGERS_006:
            sql = T.sql_de(self.db, nom)
            self.assertRegex(sql, r"^CREATE TRIGGER \w+\s+BEFORE (INSERT|UPDATE|DELETE) ON", nom)
            corps = sql[sql.index("BEGIN"):]
            self.assertNotRegex(corps, r"\b(INSERT|UPDATE|DELETE|REPLACE)\b\s+(INTO|OR|FROM|\w+\s+SET)", nom)
            instr = [s for s in corps.split(";") if s.strip() and s.strip() not in ("BEGIN", "END")]
            for s in instr:
                self.assertRegex(s, r"SELECT RAISE\(ABORT, 'INV-\d+: [^']*(?:''[^']*)*'\)", nom)

    def test_T48_B_messages_de_triggers_ascii_et_prefixes_inv(self):
        for nom in TRIGGERS_006:
            for m in re.findall(r"RAISE\(ABORT, '((?:[^']|'')*)'\)", T.sql_de(self.db, nom)):
                self.assertRegex(m, r"^INV-\d+: ", nom)
                self.assertTrue(m.isascii(), m)

    def test_T48_B_noms_des_triggers_au_format_des_tranches_precedentes(self):
        for nom in TRIGGERS_006:
            self.assertRegex(nom, r"^tr_\d\d_(factures|facture_lignes|bc_devis)_\w+$", nom)
        self.assertNotIn("tr_24_facture_lignes_insert", TRIGGERS_006)                          # TR-24 du modèle est obsolète, jamais créé

    def test_T48_B_triggers_dans_l_ordre_inverse_de_creation_non_contractuel(self):
        """INTERPRETATION : l'ordre d'exécution de plusieurs triggers d'un même événement n'est pas un contrat ; aucun test ne dépend du préfixe
        du message quand plusieurs gardes sont en défaut."""
        self.assertEqual(len([n for n in TRIGGERS_006 if TRIGGERS_006[n] == "factures"]), 8)

    def test_T48_B_les_check_de_factures_sont_ceux_du_sql(self):
        defs = T.definitions(T.sql_de(self.db, "factures"))
        self.assertEqual(sum(1 for d in defs if d.startswith("CHECK")), 12)
        defs = T.definitions(T.sql_de(self.db, "facture_lignes"))
        self.assertEqual(sum(1 for d in defs if d.startswith("CHECK")), 10)
        self.assertEqual(sum(1 for d in defs if d.startswith("UNIQUE")), 1)


# ====================================================================================================================
# C — CHECK, NOT NULL, UNIQUE et FK de `factures` (triggers de 006 retirés : on n'éprouve que les contraintes déclaratives)
# ====================================================================================================================
def sans_006(self):
    """Base du rang 9 dont les triggers de 006 sont supprimés : seules les contraintes déclaratives (CHECK, NOT NULL, UNIQUE, FK) restent actives."""
    t = Base9()
    t.db = migrer9()
    t._n = 0
    for nom in TRIGGERS_006:
        t.db.execute(f"DROP TRIGGER {nom}")
    return t


Base9.sans_006 = sans_006


class CheckFactures(Base9):
    """Groupe C : F1 → F12 une par une, avec valeurs limites. Méthode : une ligne de contrôle valide, puis une seule colonne modifiée."""

    def setUp(self):
        super().setUp()
        self.t = self.sans_006()
        self.bc = self.t.monde()
        self.orig = self.t.facture(self.bc, "acompte", "100.00", devis_id=self.bc.d[0], numero="ACP-09999-26")
        self.n_sit = 100

    def defauts(self, type_):
        if type_ == "acompte":
            return {"devis_id": self.bc.d[0]}
        if type_ == "situation":
            self.n_sit += 1
            return {"situation_numero": self.n_sit, "montant_deja_facture_ht": "0.00"}
        if type_ == "avoir":
            return {"origine_facture_id": self.orig}
        return {}

    def essai_f(self, type_, total="10.00", **kw):
        cols = self.defauts(type_)
        cols.update(kw)
        return self.t.tente_f(self.bc, type_, total, **cols)

    def ok(self, type_, total="10.00", **kw):
        m = self.essai_f(type_, total, **kw)
        self.assertIsNone(m, f"{type_} {total} {kw} refusée à tort : {m}")

    def ko(self, type_, total="10.00", **kw):
        m = self.essai_f(type_, total, **kw)
        self.assertIsNotNone(m, f"{type_} {total} {kw} acceptée à tort")
        self.assertRegex(m, r"constraint failed|NOT NULL|UNIQUE|FOREIGN KEY|datatype|cannot store")

    # --- F1 : type ---------------------------------------------------------------------------------------------------
    def test_T48_C_F1_les_quatre_types_sont_acceptes_et_aucun_autre(self):
        for ty in TYPES:
            with self.subTest(type=ty):
                self.ok(ty)
        for faux in ("Acompte", "facture", "", "avoir ", "complete", "NULL", "ACOMPTE", "zzz"):
            with self.subTest(faux=faux):
                m = self.t.tente_f(self.bc, faux, "10.00", numero="FAC-00099-26", date_echeance="2026-11-04")
                self.assertIsNotNone(m)

    def test_T48_C_F1_type_null_refuse(self):
        cols = self.t.cols_facture(self.bc, "solde", "10.00")
        cols["type"] = None
        with self.assertRaises(sqlite3.IntegrityError):
            self.t.inserer("factures", cols)

    # --- F2 / F3 : avoir, origine, motif, échéance -----------------------------------------------------------------------
    def test_T48_C_F2_avoir_exige_une_origine_et_aucun_autre_type_n_en_porte(self):
        self.ok("avoir")
        self.ko("avoir", origine_facture_id=None)
        for ty in ("acompte", "situation", "solde"):
            with self.subTest(type=ty):
                self.ok(ty)
                self.ko(ty, origine_facture_id=self.orig)

    def test_T48_C_F3_motif_de_l_avoir_non_vide_et_absent_des_autres_types(self):
        self.ok("avoir", motif_avoir="x")
        for faux in (None, ""):
            with self.subTest(motif=faux):
                self.ko("avoir", motif_avoir=faux)
        for ty in ("acompte", "situation", "solde"):
            with self.subTest(type=ty):
                self.ko(ty, motif_avoir="Erreur")
                self.ko(ty, motif_avoir="")

    def test_T48_C_F3_echeance_absente_pour_l_avoir_obligatoire_pour_les_autres(self):
        self.ok("avoir", date_echeance=None)
        self.ko("avoir", date_echeance="2026-11-04")
        for ty in ("acompte", "situation", "solde"):
            with self.subTest(type=ty):
                self.ok(ty, date_echeance="2026-11-04")
                self.ko(ty, date_echeance=None)
                self.ko(ty, date_echeance=OMIT)

    def test_T48_C_F4_echeance_pas_avant_emission(self):
        for ty in ("acompte", "situation", "solde"):
            with self.subTest(type=ty):
                self.ok(ty, date_emission="2026-10-05", date_echeance="2026-10-05")             # égalité acceptée
                self.ok(ty, date_emission="2026-10-05", date_echeance="2026-10-06")
                self.ok(ty, date_emission="2026-10-05", date_echeance="2027-01-01")
                self.ko(ty, date_emission="2026-10-05", date_echeance="2026-10-04")
                self.ko(ty, date_emission="2026-10-05", date_echeance="2025-10-06")
                self.ko(ty, date_emission="2026-12-31", date_echeance="2026-01-01")

    # --- F8 : devis_id ----------------------------------------------------------------------------------------------------
    def test_T48_C_F8_devis_obligatoire_pour_l_acompte_et_interdit_ailleurs(self):
        self.ok("acompte")
        self.ko("acompte", devis_id=None)
        self.ko("acompte", devis_id=OMIT)
        for ty in ("situation", "solde", "avoir"):
            with self.subTest(type=ty):
                self.ok(ty)
                self.ko(ty, devis_id=self.bc.d[0])

    # --- F5 / F11 : situation ----------------------------------------------------------------------------------------------
    def test_T48_C_F5_situation_exige_numero_et_deja_facture_les_autres_types_aucun(self):
        self.ok("situation")
        self.ko("situation", situation_numero=None)
        self.ko("situation", montant_deja_facture_ht=None)
        self.ko("situation", situation_numero=None, montant_deja_facture_ht=None)
        for ty in ("acompte", "solde", "avoir"):
            with self.subTest(type=ty):
                self.ko(ty, situation_numero=1)
                self.ko(ty, montant_deja_facture_ht="0.00")
                self.ko(ty, situation_numero=1, montant_deja_facture_ht="0.00")

    def test_T48_C_F11_situation_numero_entier_superieur_ou_egal_a_un(self):
        for ok in (1, 2, 99, 100000):
            with self.subTest(ok=ok):
                self.ok("situation", situation_numero=ok)
        for ko in (0, -1, -100):
            with self.subTest(ko=ko):
                self.ko("situation", situation_numero=ko)
        for faux in ("a", "1.5", ""):
            with self.subTest(faux=faux):
                self.ko("situation", situation_numero=faux)

    def test_T48_C_F11_montant_deja_facture_famille_D2_positive_ou_nulle(self):
        for ok in ("0.00", "0.01", "1234.50", "999999999.99"):
            with self.subTest(ok=ok):
                self.ok("situation", montant_deja_facture_ht=ok)
        for ko in ("-1.00", "1", "1.5", "01.00", "1.000", "1,00", " 1.00", "1.00 ", "+1.00", "1e2", "", "abc", ".50", "1.", "1.2.3") + MAL_D2:
            with self.subTest(ko=ko):
                self.ko("situation", montant_deja_facture_ht=ko)

    # --- F6 : total_ht ----------------------------------------------------------------------------------------------------
    def test_T48_C_F6_total_nul_refuse_sauf_pour_le_solde(self):
        self.ok("solde", "0.00")
        for ty in ("acompte", "situation", "avoir"):
            with self.subTest(type=ty):
                self.ko(ty, "0.00")
                self.ok(ty, "0.01")

    def test_T48_C_F6_total_famille_D2_valeurs_limites(self):
        for ty in TYPES:
            for ok in ("0.01", "1.00", "10.50", "123456789.99", "999999999.99", "10.10", "10.01"):
                with self.subTest(type=ty, ok=ok):
                    self.ok(ty, ok)
            for ko in ("-0.01", "-10.00", "1", "10", "1.5", "01.00", "00.50", "1.000", "1,00", " 1.00", "1.00 ", "+1.00", "1e2", "", "abc", ".50", "1.", "1.2.3",
                       "1 000.00", "１.00") + MAL_D2:
                with self.subTest(type=ty, ko=ko):
                    self.ko(ty, ko)

    def test_T48_C_F6_total_zero_ecrit_autrement_n_est_pas_un_zero_admis(self):
        for ty in ("acompte", "situation", "avoir"):
            for z in ("0", "0.0", "00.00", "0.000", "-0.00"):
                with self.subTest(type=ty, z=z):
                    self.ko(ty, z)
        for z in ("0", "0.0", "00.00", "0.000", "-0.00"):
            with self.subTest(type="solde", z=z):
                self.ko("solde", z)

    def test_T48_C_F6_total_entier_ou_reel_non_texte_refuse_par_la_table_stricte(self):
        for valeur in (5, 5.5, 0):
            with self.subTest(valeur=valeur):
                self.ko("solde", valeur)

    def test_T48_C_F6_total_null_refuse(self):
        self.ko("solde", None)

    # --- F7 : numéro -----------------------------------------------------------------------------------------------------
    def test_T48_C_F7_format_v6_par_type_et_annee_de_la_date_d_emission(self):
        bons = {"acompte": "ACP-00001-26", "situation": "FAC-00001-26", "solde": "FAC-00002-26", "avoir": "AVO-00001-26"}
        for ty, n in bons.items():
            with self.subTest(type=ty):
                self.ok(ty, numero=n, date_emission="2026-10-05")
        croise = {"acompte": ("FAC-00001-26", "AVO-00001-26", "BCD-00001-26"), "situation": ("ACP-00001-26", "AVO-00001-26"),
                  "solde": ("ACP-00001-26", "AVO-00001-26"), "avoir": ("ACP-00001-26", "FAC-00001-26")}
        for ty, faux in croise.items():
            for n in faux:
                with self.subTest(type=ty, numero=n):
                    self.ko(ty, numero=n)

    def test_T48_C_F7_format_v6_chiffres_separateurs_casse(self):
        for faux in ("FAC-0001-26", "FAC-000001-26", "FAC-00001-2", "FAC-00001-026", "FAC-00001/26", "FAC_00001-26", "fac-00001-26", "FAC-0000a-26",
                     "FAC-00001-2a", " FAC-00001-26", "FAC-00001-26 ", "FAC-00001-26-1", "FAC00001-26", "FAC-00001", "", "FAC-00001-2626"):
            with self.subTest(faux=faux):
                self.ko("solde", numero=faux)

    def test_T48_C_F7_annee_du_numero_egale_a_celle_de_date_emission(self):
        self.ok("solde", numero="FAC-00001-26", date_emission="2026-10-05")
        self.ko("solde", numero="FAC-00001-27", date_emission="2026-10-05")
        self.ko("solde", numero="FAC-00001-25", date_emission="2026-10-05")
        self.ok("solde", numero="FAC-00001-27", date_emission="2027-01-01", date_echeance="2027-02-01")
        self.ko("solde", numero="FAC-00001-26", date_emission="2027-01-01", date_echeance="2027-02-01")
        self.ok("solde", numero="FAC-00001-99", date_emission="2099-12-31", date_echeance="2100-01-30")

    def test_T48_C_F7_numero_vide_ou_null_refuse(self):
        self.ko("solde", numero="")
        self.ko("solde", numero=None)

    def test_T48_C_F7_origine_import_numero_libre_mais_non_vide(self):
        for libre in ("2024-017", "F2024/0007", "A", "FAC-1", "ACP-00001-26", "fac 12", "été 2024"):
            with self.subTest(libre=libre):
                self.ok("solde", numero=libre, origine="import")
        self.ko("solde", numero="", origine="import")
        self.ko("solde", numero=None, origine="import")

    def test_T48_C_F7_origine_inconnue_refusee(self):
        for faux in ("", "V6", "legacy", "migration", "zzz", None):
            with self.subTest(faux=faux):
                self.ko("solde", origine=faux)
        self.ok("solde", origine="v6")

    def test_T48_C_F7_numero_unique_et_fac_partage_entre_situation_et_solde(self):
        self.t.facture(self.bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", numero="FAC-00001-26")
        self.ko("solde", numero="FAC-00001-26")                                                 # même séquence FAC
        self.ko("situation", numero="FAC-00001-26", situation_numero=2)
        self.ok("solde", numero="FAC-00002-26")
        self.t.facture(self.bc, "acompte", "10.00", devis_id=self.bc.d[0], numero="ACP-00001-26")
        self.ko("acompte", numero="ACP-00001-26")
        self.ok("acompte", numero="ACP-00002-26")
        self.t.facture(self.bc, "avoir", "5.00", origine_facture_id=self.orig, numero="AVO-00001-26")
        self.ko("avoir", numero="AVO-00001-26")

    def test_T48_C_F7_numeros_import_en_double_refuses(self):
        self.t.facture(self.bc, "solde", "10.00", numero="2024-017", origine="import")
        self.ko("solde", numero="2024-017", origine="import")

    # --- F9 : BLOC-IMP ---------------------------------------------------------------------------------------------------
    def test_T48_C_F9_legacy_interdit_pour_v6_permis_pour_import(self):
        self.ko("solde", legacy_id="L-1")
        self.ko("solde", legacy_data='{"k": 1}')
        self.ko("solde", legacy_id="L-1", legacy_data='{"k": 1}')
        self.ok("solde", numero="X-1", origine="import", legacy_id="L-1", legacy_data='{"k": 1}')
        self.ok("solde", numero="X-2", origine="import", legacy_id=None, legacy_data=None)
        self.ko("solde", numero="X-3", origine="import", legacy_data="pas du json")
        self.ko("solde", numero="X-4", origine="import", legacy_data="{")

    # --- F10 : dates -----------------------------------------------------------------------------------------------------
    def test_T48_C_F10_dates_reelles_au_format_aaaa_mm_jj(self):
        for ko in ("2026-02-30", "2026-13-01", "2026-00-10", "2026-10-00", "2026-10-32", "26-10-05", "2026-10-5", "2026-1-05", "2026/10/05", "20261005",
                   "", "abc", "2026-10-05T10:00:00", "2026-10-05 ", " 2026-10-05", "2027-02-29", "2026-04-31", "2026-06-31",
                   "-0001-01-01", "-0001-12-31", "-4713-12-01", "-4713-12-31", "10000-01-01", "+2026-10-05"):               # date() accepte des années négatives : le GLOB les refuse
            with self.subTest(date_emission=ko):
                self.ko("solde", date_emission=ko, numero="X-D", origine="import", date_echeance="2030-01-01")
        for ok in ("2028-02-29", "2026-02-28", "2026-12-31", "2026-01-01", "2024-02-29"):
            with self.subTest(date_emission=ok):
                self.ok("solde", date_emission=ok, numero="X-D", origine="import", date_echeance="2030-01-01")

    def test_T48_C_F10_date_echeance_reelle(self):
        for ko in ("2026-02-30", "2026-13-01", "2027-02-29", "", "26-11-04", "2026-11-4", "-0001-01-01", "-4713-12-31", "2026-11-04 ", "+2026-11-04"):
            with self.subTest(date_echeance=ko):
                self.ko("solde", date_echeance=ko)
        self.ok("solde", date_emission="2028-02-29", date_echeance="2028-02-29", numero="X-F", origine="import")

    def test_T48_C_F10_aucune_borne_d_annee_dans_la_base(self):
        """INTERPRETATION (D-38) : la borne 2001-2099 est une règle de service ; le schéma accepte 1900 ou 2100."""
        for d in ("1900-01-01", "2000-12-31", "2100-01-01", "9999-12-31", "0001-01-01"):
            with self.subTest(date=d):
                self.ok("solde", date_emission=d, date_echeance="9999-12-31", numero="X-B", origine="import")

    def test_T48_C_F10_date_emission_absente_ou_null_refusee(self):
        self.ko("solde", date_emission=None)
        self.ko("solde", date_emission=OMIT)

    # --- F12 : created_at, snapshots, NOT NULL ----------------------------------------------------------------------------------
    def test_T48_C_F12_created_at_horodatage_canonique(self):
        self.ok("solde", created_at="2026-10-05T10:00:00.000Z")
        for ko in ("2026-10-05", "2026-10-05T10:00:00Z", "2026-10-05T10:00:00.00Z", "2026-10-05 10:00:00.000Z", "2026-10-05T10:00:00.000", "", "x"):
            with self.subTest(created_at=ko):
                self.ko("solde", created_at=ko)
        self.ko("solde", created_at=None)

    def test_T48_C_F12_created_at_prend_une_valeur_par_defaut_valide(self):
        cols = self.t.cols_facture(self.bc, "solde", "10.00", created_at=OMIT)
        f = self.t.inserer("factures", cols)
        v = self.t.un("SELECT created_at FROM factures WHERE id=?", f)[0]
        self.assertRegex(v, r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$")

    def test_T48_C_snapshots_json_valide_et_versions_obligatoires(self):
        for col in ("client_snapshot", "entreprise_snapshot", "chantier_snapshot"):
            with self.subTest(col=col):
                self.ok("solde", **{col: '{"a": 1}'})
                self.ok("solde", **{col: "[]"})
                self.ko("solde", **{col: "pas du json"})
                self.ko("solde", **{col: "{"})
                self.ko("solde", **{col: ""})
                self.ko("solde", **{col: None})
                self.ko("solde", **{col: OMIT})
        for col in ("client_snapshot_version", "entreprise_snapshot_version", "chantier_snapshot_version"):
            with self.subTest(col=col):
                self.ok("solde", **{col: 7})
                self.ko("solde", **{col: None})
                self.ko("solde", **{col: OMIT})
                self.ko("solde", **{col: "abc"})

    def test_T48_C_colonnes_obligatoires_not_null(self):
        for col in ("numero", "type", "bc_id", "client_id", "total_ht", "date_emission", "client_snapshot", "client_snapshot_version", "entreprise_snapshot",
                    "entreprise_snapshot_version", "chantier_snapshot", "chantier_snapshot_version", "origine"):
            with self.subTest(col=col):
                self.ko("solde", **{col: None})
        for col in ("objet", "legacy_id", "legacy_data"):
            with self.subTest(col=col):
                self.ok("solde", **{col: None})

    def test_T48_C_objet_libre(self):
        for v in (None, "", "Chantier A", "é" * 500, "ligne1\nligne2"):
            with self.subTest(objet=v):
                self.ok("solde", objet=v)

    # --- FK ------------------------------------------------------------------------------------------------------------
    def test_T48_C_les_cles_etrangeres_inexistantes_sont_refusees(self):
        self.ko("solde", bc_id=99999)
        self.ko("solde", client_id=99999)
        self.ko("acompte", devis_id=99999)
        self.ko("avoir", origine_facture_id=99999)
        self.ko("solde", bc_id=None)
        self.ko("solde", client_id=None)

    def test_T48_C_foreign_keys_off_laisse_passer_un_orphelin_que_foreign_key_check_detecte(self):
        self.t.db.execute("PRAGMA foreign_keys=OFF")
        self.ok("solde", bc_id=99999)
        self.t.db.execute("PRAGMA foreign_keys=OFF")
        self.t.facture(self.bc, "solde", "10.00", client_id=99999)
        self.t.db.execute("PRAGMA foreign_keys=ON")
        self.assertEqual(len(self.t.tous("PRAGMA foreign_key_check")), 1)


# ====================================================================================================================
# D — CHECK, UNIQUE et FK de `facture_lignes` (triggers de 006 retirés)
# ====================================================================================================================
class CheckLignes(Base9):
    """Groupe D : ordre, désignation, familles DL / D2S / P2, déduction <=> négatif, lignes d'avancement. Une ligne de contrôle valide, une seule colonne modifiée."""

    def setUp(self):
        super().setUp()
        self.t = self.sans_006()
        self.bc = self.t.monde()
        self.f = self.t.facture(self.bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.n = 10

    def cols(self, type_ligne="prestation", montant="10.00", **kw):
        self.n += 1
        cols = {"facture_id": self.f, "ordre": self.n, "designation": "Ligne", "quantite": "1", "unite": "ens", "prix_unitaire_ht": "10",
                "remise_type": "aucune", "type_ligne": type_ligne, "montant_ht": montant}
        if type_ligne == "avancement":
            cols.update({"bc_ligne_id": self.bc.lignes[0], "avancement_precedent_pct": "0.00", "avancement_cumule_pct": "50.00"})
        cols.update(kw)
        return {k: v for k, v in cols.items() if v is not OMIT}

    def essai(self, type_ligne="prestation", montant="10.00", **kw):
        cols = self.cols(type_ligne, montant, **kw)
        self.t.db.execute("SAVEPOINT l")
        try:
            self.t.inserer("facture_lignes", cols)
            return None
        except sqlite3.IntegrityError as e:
            return str(e)
        finally:
            self.t.db.execute("ROLLBACK TO l")
            self.t.db.execute("RELEASE l")

    def ok(self, *a, **kw):
        m = self.essai(*a, **kw)
        self.assertIsNone(m, f"{a} {kw} refusée à tort : {m}")

    def ko(self, *a, **kw):
        m = self.essai(*a, **kw)
        self.assertIsNotNone(m, f"{a} {kw} acceptée à tort")
        self.assertRegex(m, r"constraint failed|NOT NULL|UNIQUE|FOREIGN KEY|datatype|cannot store")

    # --- ordre, désignation ------------------------------------------------------------------------------------------------
    def test_T48_D_ordre_entier_superieur_ou_egal_a_un(self):
        for ok in (1, 2, 99, 100000):
            with self.subTest(ok=ok):
                self.ok(ordre=ok)
        for ko in (0, -1, None, "a", 1.5):
            with self.subTest(ko=ko):
                self.ko(ordre=ko)

    def test_T48_D_ordre_unique_par_facture(self):
        self.t.inserer("facture_lignes", self.cols(ordre=1))
        self.ko(ordre=1)
        self.ok(ordre=2)
        autre = self.t.facture(self.bc, "solde", "0.00")
        self.ok(facture_id=autre, ordre=1)                                                       # même ordre dans une autre facture
        self.ok(facture_id=autre, ordre=2)

    def test_T48_D_designation_non_vide_et_obligatoire(self):
        self.ok(designation="x")
        self.ok(designation="é" * 300)
        self.ko(designation="")
        self.ko(designation=None)
        self.ko(designation=OMIT)

    def test_T48_D_colonnes_obligatoires(self):
        for col in ("facture_id", "ordre", "designation", "quantite", "unite", "prix_unitaire_ht", "remise_type", "type_ligne", "montant_ht", "created_at"):
            with self.subTest(col=col):
                self.ko(**{col: None})
        for col in ("bc_ligne_id", "reference_prestation", "description"):
            with self.subTest(col=col):
                self.ok(**{col: None})

    # --- familles DL ----------------------------------------------------------------------------------------------------
    def test_T48_D_quantite_et_prix_famille_DL(self):
        for col in ("quantite", "prix_unitaire_ht"):
            for ok in ("1", "2.5", "0.5", "10", "1234.56", "0.001", "100"):
                with self.subTest(col=col, ok=ok):
                    self.ok(**{col: ok})
            for ko in MAL_DL + ("1.5.2",):
                with self.subTest(col=col, ko=ko):
                    self.ko(**{col: ko})

    def test_T48_D_quantite_zero_refusee_prix_zero_accepte(self):
        self.ko(quantite="0")
        self.ok(prix_unitaire_ht="0")
        self.ok(prix_unitaire_ht="0.5")

    def test_T48_D_unite_enumeration(self):
        for ok in ("u", "ens", "ml", "m2", "m3"):
            with self.subTest(ok=ok):
                self.ok(unite=ok)
        for ko in ("", "U", "m", "kg", "m²", "h", "zzz", None):
            with self.subTest(ko=ko):
                self.ko(unite=ko)

    # --- remise ----------------------------------------------------------------------------------------------------------
    def test_T48_D_remise_aucune_si_et_seulement_si_valeur_nulle(self):
        self.ok(remise_type="aucune", remise_valeur=None)
        self.ko(remise_type="aucune", remise_valeur="10.00")
        self.ko(remise_type="pourcentage", remise_valeur=None)
        self.ko(remise_type="montant", remise_valeur=None)
        self.ko(remise_type="autre", remise_valeur="1.00")
        self.ko(remise_type="zzz", remise_valeur="1.00")
        self.ko(remise_type="zzz", remise_valeur=None)
        self.ko(remise_type=None)

    def test_T48_D_remise_pourcentage_P2_bornes_0_a_100(self):
        for ok in ("0.00", "0.01", "10.00", "99.99", "100.00", "12.50"):
            with self.subTest(ok=ok):
                self.ok(remise_type="pourcentage", remise_valeur=ok)
        for ko in ("100.01", "-1.00", "1", "1.5", "01.00", "1.000", "abc", "", "200.00", ".5", "100.10", "101.00", "999.99") + MAL_D2:
            with self.subTest(ko=ko):
                self.ko(remise_type="pourcentage", remise_valeur=ko)

    def test_T48_D_remise_montant_famille_DL(self):
        for ok in ("1", "12.5", "100", "0.01"):
            with self.subTest(ok=ok):
                self.ok(remise_type="montant", remise_valeur=ok)
        for ko in MAL_DL:
            with self.subTest(ko=ko):
                self.ko(remise_type="montant", remise_valeur=ko)

    # --- type_ligne et montant_ht (D2S) -------------------------------------------------------------------------------------
    def test_T48_D_type_ligne_enumeration(self):
        for ok in ("prestation", "synthese", "deduction", "avancement"):
            with self.subTest(ok=ok):
                montant = "-10.00" if ok == "deduction" else "10.00"
                kw = {"quantite": "1"}
                self.ok(ok, montant, **kw)
        for ko in ("", "Prestation", "avance", "remise", "zzz", None):
            with self.subTest(ko=ko):
                self.ko(type_ligne=ko)

    def test_T48_D_montant_famille_D2S_formes_canoniques(self):
        for ok in ("0.00", "0.01", "12.50", "999999999.99", "10.10"):
            with self.subTest(ok=ok):
                self.ok("prestation", ok)
        for ok in ("-0.01", "-12.50", "-999999999.99", "-10.10"):
            with self.subTest(ok=ok):
                self.ok("deduction", ok)
        for ko in ("-0.00", "--1.00", "1.5", "-1.5", "-", "", "-01.00", "+1.00", "1.00-", "- 1.00", " 1.00", "1.00 ", "1", "-1", "01.00", "1.000", "1,00",
                   "1e2", "abc", ".50", "-.50", "1.", "-1.", "1.2.3", "-1.2.3", "1-.00", "--0.00") + tuple(x for x in MAL_D2 if x != "-1.23") + MAL_D2S_NEG:       # -1.23 : forme canonique d'une déduction
            with self.subTest(ko=ko):
                self.ko("prestation", ko)
                self.ko("deduction", ko)

    def test_T48_D_montant_negatif_zero_ecrit_avec_signe_refuse(self):
        self.ko("deduction", "-0.00")
        self.ko("prestation", "-0.00")
        self.ok("prestation", "0.00")                                                            # le zéro positif reste admis (ligne à 0.00)

    def test_T48_D_deduction_si_et_seulement_si_montant_negatif(self):
        self.ok("deduction", "-5.00")
        self.ko("deduction", "5.00")
        self.ko("deduction", "0.00")
        for ty in ("prestation", "synthese"):
            with self.subTest(type=ty):
                self.ok(ty, "5.00")
                self.ok(ty, "0.00")
                self.ko(ty, "-5.00")
        self.ko("avancement", "-5.00")

    def test_T48_D_une_deduction_porte_la_quantite_un(self):
        self.ok("deduction", "-5.00", quantite="1")
        for q in ("2", "0.5", "10", "1.5"):
            with self.subTest(q=q):
                self.ko("deduction", "-5.00", quantite=q)
        self.ok("prestation", "5.00", quantite="2")

    def test_T48_D_aucune_ligne_negative_hors_deduction(self):
        for ty in ("prestation", "synthese", "avancement"):
            for m in ("-0.01", "-100.00", "-999999999.99"):
                with self.subTest(type=ty, m=m):
                    self.ko(ty, m)

    # --- avancement ---------------------------------------------------------------------------------------------------------
    def test_T48_D_ligne_d_avancement_valide_et_a_zero(self):
        self.ok("avancement", "5.00")
        self.ok("avancement", "0.00", avancement_precedent_pct="0.00", avancement_cumule_pct="0.00")
        self.ok("avancement", "0.00")                                                            # une ligne peut valoir 0.00

    def test_T48_D_avancement_les_deux_pourcentages_et_la_ligne_de_bc_sont_obligatoires(self):
        self.ko("avancement", "5.00", avancement_precedent_pct=None)
        self.ko("avancement", "5.00", avancement_cumule_pct=None)
        self.ko("avancement", "5.00", avancement_precedent_pct=None, avancement_cumule_pct=None)
        self.ko("avancement", "5.00", bc_ligne_id=None)
        self.ko("avancement", "5.00", bc_ligne_id=OMIT)

    def test_T48_D_les_pourcentages_d_avancement_n_existent_que_pour_une_ligne_d_avancement(self):
        for ty in ("prestation", "synthese"):
            with self.subTest(type=ty):
                self.ko(ty, "5.00", avancement_precedent_pct="0.00")
                self.ko(ty, "5.00", avancement_cumule_pct="10.00")
                self.ko(ty, "5.00", avancement_precedent_pct="0.00", avancement_cumule_pct="10.00")
        self.ko("deduction", "-5.00", avancement_cumule_pct="10.00")
        self.ko("deduction", "-5.00", avancement_precedent_pct="0.00")

    def test_T48_D_precedent_inferieur_ou_egal_au_cumule_et_bornes_0_100(self):
        for p, cu in (("0.00", "0.00"), ("0.00", "0.01"), ("12.34", "12.34"), ("12.34", "12.35"), ("99.99", "100.00"), ("100.00", "100.00"), ("0.00", "100.00")):
            with self.subTest(p=p, cu=cu):
                self.ok("avancement", "5.00", avancement_precedent_pct=p, avancement_cumule_pct=cu)
        for p, cu in (("0.01", "0.00"), ("50.00", "49.99"), ("100.00", "99.99"), ("12.35", "12.34"), ("10.00", "9.99")):
            with self.subTest(p=p, cu=cu):
                self.ko("avancement", "5.00", avancement_precedent_pct=p, avancement_cumule_pct=cu)

    def test_T48_D_pourcentages_d_avancement_famille_P2(self):
        for col in ("avancement_precedent_pct", "avancement_cumule_pct"):
            autre = {"avancement_precedent_pct": "avancement_cumule_pct", "avancement_cumule_pct": "avancement_precedent_pct"}[col]
            base = "100.00" if col == "avancement_precedent_pct" else "0.00"                    # la colonne voisine ne doit jamais, à elle seule, motiver le refus
            for ko in ("100.01", "-1.00", "1", "1.5", "01.00", "00.00", "00.50", "1.000", "abc", "", "200.00", ".5", "+1.00", "1e1", " 1.00", "50.0", "5.",
                       "1.2.3", "1.23.45", "12.34.56", "1a.23", "1.2a", "a1.23", "1.23 ", "1.23\n", "-0.00", "0.0", "00.0", "1,23", "1.2.34", "1..23", "..", ".", "1x.00",
                       "0x.00", "10.0a", "١.00", ".50", ".00", ".99", " 1.23", "+1.23", "1.23e", "1.", "") + tuple(x for x in MAL_D2 if x not in ("1.23", "12.34")):
                with self.subTest(col=col, ko=ko):
                    self.ko("avancement", "5.00", **{col: ko, autre: base})
            for ok in ("0.00", "0.01", "99.99", "100.00", "9.99", "10.00", "50.00"):
                with self.subTest(col=col, ok=ok):
                    kw = {col: ok, autre: ok}
                    self.ok("avancement", "5.00", **kw)

    def test_T48_D_une_seule_ligne_d_avancement_par_facture_et_par_ligne_de_bc(self):
        self.t.inserer("facture_lignes", self.cols("avancement", "5.00"))
        self.ko("avancement", "5.00")                                                            # même facture, même ligne de BC
        self.ok("avancement", "5.00", bc_ligne_id=self.bc.lignes[1])                              # autre ligne de BC
        autre = self.t.facture(self.bc, "situation", "10.00", situation_numero=2, montant_deja_facture_ht="10.00")
        self.ok("avancement", "5.00", facture_id=autre)                                          # autre facture, même ligne de BC

    def test_T48_D_l_unicite_d_avancement_ne_vise_que_les_lignes_d_avancement(self):
        solde = self.t.facture(self.bc, "solde", "10.00")
        self.t.inserer("facture_lignes", self.cols("prestation", "5.00", facture_id=solde, bc_ligne_id=self.bc.lignes[0]))
        self.ok("prestation", "5.00", facture_id=solde, bc_ligne_id=self.bc.lignes[0])           # deux lignes de solde sur la même ligne de BC : permis par le schéma
        self.t.inserer("facture_lignes", self.cols("deduction", "-5.00", facture_id=solde, bc_ligne_id=None))
        self.ok("deduction", "-5.00", facture_id=solde, bc_ligne_id=None)

    def test_T48_D_ligne_de_bc_et_facture_inexistantes_refusees(self):
        self.ko("avancement", "5.00", bc_ligne_id=99999)
        self.ko("prestation", "5.00", bc_ligne_id=99999)
        self.ko("prestation", "5.00", facture_id=99999)
        self.ko("prestation", "5.00", facture_id=None)

    def test_T48_D_created_at_canonique_et_defaut_valide(self):
        self.ok(created_at="2026-10-05T10:00:00.000Z")
        for ko in ("2026-10-05", "2026-10-05T10:00:00Z", "x", ""):
            with self.subTest(created_at=ko):
                self.ko(created_at=ko)
        i = self.t.inserer("facture_lignes", self.cols(created_at=OMIT))
        self.assertRegex(self.t.un("SELECT created_at FROM facture_lignes WHERE id=?", i)[0], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$")

    def test_T48_D_pas_de_borne_haute_sur_les_montants_de_ligne_d_une_facture_plus_petite(self):
        """INTERPRETATION : Σ lignes = total_ht est un contrôle diagnostic (CK-05), jamais une contrainte (SQLite ne l'impose pas en fin de transaction)."""
        self.ok("prestation", "999999999.99")


# ====================================================================================================================
# Groupe E — argent : formule figée, oracle, recoupement SQL (CK-17) / Python, arrondis
# ====================================================================================================================
class Argent(Base9):
    """La formule est un service : l'oracle Python et la requête CK-17 (SQL indépendante) doivent donner le même X, au centime."""

    P = lambda self, x: int(round(x * 100))                                                 # noqa: E731  62.5 -> 6250

    def sit(self, bc, pcts_pct):
        """Émet une situation. pcts_pct : liste de pourcentages (flottants de saisie, ex. 62.5) dans l'ordre des lignes de BC du monde."""
        return self.emettre_situation(bc, {bl: self.P(p) for bl, p in zip(bc.lignes, pcts_pct)})

    # --- formule seule ------------------------------------------------------------------------------------------------
    def test_T48_E_formule_g_demi_superieur_une_seule_fois_par_ligne(self):
        self.assertEqual(g(400000, 6250), 250000)
        self.assertEqual(g(1, 5000), 1)             # 0.005 -> 0.01 (HALF_UP)
        self.assertEqual(g(1, 4999), 0)             # 0.004999 -> 0.00
        self.assertEqual(g(3, 5000), 2)             # 0.015 -> 0.02
        self.assertEqual(g(10, 3333), 3)            # 3.333 -> 3
        self.assertEqual(g(10, 3500), 4)            # 3.5 -> 4
        self.assertEqual(g(0, 10000), 0)
        self.assertEqual(g(123456, 10000), 123456)  # 100 % : exactement b
        self.assertEqual(g(123456, 0), 0)

    def test_T48_E_formule_r_demi_superieur_une_seule_fois_par_devis(self):
        self.assertEqual(r(0, 5000, 10000), 0)                       # pas de remise
        self.assertEqual(r(100, 0, 1000), 0)                         # rien de facturé
        self.assertEqual(r(100, 1000, 1000), 100)                    # 100 % : la remise entière
        self.assertEqual(r(1, 1, 3), 0)                              # 1/3 -> 0
        self.assertEqual(r(1, 2, 3), 1)                              # 2/3 -> 1
        self.assertEqual(r(1, 1, 2), 1)                              # 1/2 -> 1 (HALF_UP)
        self.assertEqual(r(5, 3, 4), 4)                              # 3.75 -> 4
        self.assertEqual(r(7, 5, 0), 0)                              # B = 0 -> 0 (jamais de division)

    def test_T48_E_a_100_pour_cent_X_vaut_la_somme_des_devis(self):
        rnd = random.Random(48)
        for _ in range(300):
            devis = []
            for _ in range(rnd.randint(1, 4)):
                lignes = [rnd.randint(0, 900000) for _ in range(rnd.randint(1, 6))]
                B = sum(lignes)
                total = B - rnd.randint(0, B // 3) if B else 0
                devis.append(([(b, 10000) for b in lignes], total))
            X, _ = valeur_cumulee(devis)
            self.assertEqual(X, sum(t for _, t in devis))

    def test_T48_E_X_est_croissant_avec_chaque_pourcentage(self):
        rnd = random.Random(49)
        for _ in range(300):
            lignes = [rnd.randint(1, 500000) for _ in range(rnd.randint(1, 5))]
            B = sum(lignes)
            total = B - rnd.randint(0, B // 2)
            ps = [rnd.randint(0, 9000) for _ in lignes]
            x0, _ = valeur_cumulee([(list(zip(lignes, ps)), total)])
            k = rnd.randrange(len(lignes))
            ps2 = list(ps)
            ps2[k] += rnd.randint(0, 1000)
            x1, _ = valeur_cumulee([(list(zip(lignes, ps2)), total)])
            self.assertGreaterEqual(x1, x0)
            x2, _ = valeur_cumulee([(list(zip(lignes, [10000] * len(lignes))), total)])
            self.assertLessEqual(x1, x2)

    def test_T48_E_remise_negative_refusee_par_l_oracle(self):
        with self.assertRaises(AssertionError):
            valeur_cumulee([([(100, 5000)], 200)])

    # --- oracle (scénario reconstitué : devis unique 4000 + 2000, contractuel 6000) -----------------------------------
    def test_T48_E_ORACLE_situation_1_3050_et_solde_2950(self):
        """62.50 % de 4000 = 2500 ; 27.50 % de 2000 = 550 ; X = M = 3050.00 ; le solde qui suivrait vaut 6000 − 3050 = 2950."""
        bc = self.monde()
        s1 = self.sit(bc, [62.5, 27.5])
        self.assertEqual(self.un("SELECT total_ht, montant_deja_facture_ht FROM factures WHERE id=?", s1), ("3050.00", "0.00"))
        self.assertEqual([x[0] for x in self.tous("SELECT montant_ht FROM facture_lignes WHERE facture_id=? ORDER BY ordre", s1)], ["2500.00", "550.00"])
        self.assertEqual(self.contractuel(bc) - self.nette(bc), 295000)
        self.assertEqual(self.ck(CK17_FORMULE), [])
        self.assertEqual(self.ck(CK05_SOMME), [])

    def test_T48_E_ORACLE_situation_2_X_3450_M_400(self):
        """Deuxième situation : 70.00 % et 32.50 % -> X = 2800 + 650 = 3450 ; N = 3050 ; M = 400.00 ; solde ensuite 2550."""
        bc = self.monde()
        self.sit(bc, [62.5, 27.5])
        k = self.calcul_situation(bc, {bc.lignes[0]: 7000, bc.lignes[1]: 3250})
        self.assertEqual((k.X, k.N, k.M), (345000, 305000, 40000))
        s2 = self.sit(bc, [70, 32.5])
        self.assertEqual(self.un("SELECT total_ht, montant_deja_facture_ht FROM factures WHERE id=?", s2), ("400.00", "3050.00"))
        self.assertEqual(self.tous("SELECT type_ligne, montant_ht, avancement_precedent_pct, avancement_cumule_pct FROM facture_lignes "
                                   "WHERE facture_id=? ORDER BY ordre", s2),
                         [("avancement", "2800.00", "62.50", "70.00"), ("avancement", "650.00", "27.50", "32.50"), ("deduction", "-3050.00", None, None)])
        self.assertEqual(self.contractuel(bc) - self.nette(bc), 255000)
        self.assertEqual(self.ck(CK17_FORMULE), [])

    def test_T48_E_ORACLE_acompte_1700_puis_situation_1(self):
        """Acompte 1700 + situation 1 (X = 3050) : M = 3050 − 1700 = 1350 ; N = 1700 ; solde = 6000 − 3050 = 2950."""
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1700.00")}])
        self.acompte(bc, bc.d[0], "1700.00")
        k = self.calcul_situation(bc, {bc.lignes[0]: 6250, bc.lignes[1]: 2750})
        self.assertEqual((k.X, k.N, k.M), (305000, 170000, 135000))
        s1 = self.sit(bc, [62.5, 27.5])
        self.assertEqual(self.un("SELECT total_ht, montant_deja_facture_ht FROM factures WHERE id=?", s1), ("1350.00", "1700.00"))
        self.assertEqual(self.contractuel(bc) - self.nette(bc), 295000)
        self.assertEqual(self.ck(CK17_FORMULE), [])
        self.assertEqual(self.ck(CK05_SOMME), [])

    def test_T48_E_ORACLE_a_100_pour_cent_X_vaut_6000(self):
        bc = self.monde()
        k = self.calcul_situation(bc, {bc.lignes[0]: 10000, bc.lignes[1]: 10000})
        self.assertEqual((k.X, k.M), (600000, 600000))
        s = self.sit(bc, [100, 100])
        self.assertEqual(self.total(s), 600000)
        self.assertEqual(self.contractuel(bc) - self.nette(bc), 0)           # 100 % n'est pas un solde : aucune facture de type solde
        self.assertEqual(self.un("SELECT count(*) FROM factures WHERE type='solde'")[0], 0)

    # --- cas particuliers -----------------------------------------------------------------------------------------------
    def test_T48_E_zero_pour_cent_partout_donne_M_nul_refuse_par_le_service(self):
        bc = self.monde()
        with self.assertRaises(ValueError):
            self.sit(bc, [0, 0])
        k = self.calcul_situation(bc, {})
        self.assertEqual((k.X, k.M), (0, 0))

    def test_T48_E_une_ligne_a_zero_les_autres_a_zero_sauf_une(self):
        bc = self.monde()
        s = self.sit(bc, [0, 10])
        self.assertEqual(self.total(s), 20000)
        self.assertEqual([x[0] for x in self.tous("SELECT montant_ht FROM facture_lignes WHERE facture_id=? ORDER BY ordre", s)], ["0.00", "200.00"])
        self.assertEqual(self.ck(CK17_FORMULE), [])

    def test_T48_E_petits_montants_et_centimes_fractionnaires(self):
        bc = self.monde(devis=[{"lignes": ["0.01", "0.03", "0.07"]}])
        s = self.sit(bc, [50, 50, 50])            # 0.005 -> 0.01 ; 0.015 -> 0.02 ; 0.035 -> 0.04
        self.assertEqual([x[0] for x in self.tous("SELECT montant_ht FROM facture_lignes WHERE facture_id=? ORDER BY ordre", s)], ["0.01", "0.02", "0.04"])
        self.assertEqual(self.total(s), 7)
        self.assertEqual(self.ck(CK17_FORMULE), [])

    def test_T48_E_remise_globale_du_devis_reduit_la_situation(self):
        """Devis 6000 de lignes brutes pour un total de 5400 (remise 600) : à 50 % partout, G = 3000, r = 300, X = 2700."""
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "total": "5400.00"}])
        k = self.calcul_situation(bc, {bc.lignes[0]: 5000, bc.lignes[1]: 5000})
        self.assertEqual((k.X, k.reductions[bc.d[0]]), (270000, 30000))
        s = self.sit(bc, [50, 50])
        self.assertEqual(self.total(s), 270000)
        self.assertEqual([x[0] for x in self.tous("SELECT montant_ht FROM facture_lignes WHERE facture_id=? ORDER BY ordre", s)],
                         ["2000.00", "1000.00", "-300.00"])
        self.assertEqual(self.ck(CK17_FORMULE), [])
        s2 = self.sit(bc, [100, 100])
        self.assertEqual(self.total(s2), 270000)                              # X = 5400 ; N = 2700
        self.assertEqual(self.nette(bc), 540000)

    def test_T48_E_plusieurs_devis_arrondis_divergents(self):
        """Deux devis avec remise : la réduction est arrondie PAR DEVIS (jamais sur le BC) ; X = Σ (G_d − r_d)."""
        bc = self.monde(devis=[{"lignes": ["33.33", "66.67"], "total": "99.00"}, {"lignes": ["10.01", "20.02", "5.05"], "total": "34.00"}])
        pcts = [33.33, 12.5, 7.77, 50, 99.99]
        k = self.calcul_situation(bc, {bl: self.P(p) for bl, p in zip(bc.lignes, pcts)})
        (X_attendu, _) = valeur_cumulee([([(c(t), self.P(p)) for (_, did2, t), p in zip(self.lignes_de_bc(bc), pcts) if did2 == did],
                                          c(self.un("SELECT total_ht FROM devis WHERE id=?", did)[0])) for did in k.devis])
        self.assertEqual(k.X, X_attendu)
        # le recalcul par BC (jamais fait) donnerait un autre résultat : preuve que l'arrondi par devis compte
        B = sum(c(t) for _, _, t in self.lignes_de_bc(bc))
        R = B - sum(c(self.un("SELECT total_ht FROM devis WHERE id=?", d)[0]) for d in bc.d)
        G = sum(x[5] for x in k.lignes)
        global_X = G - r(R, G, B)
        self.assertNotEqual(global_X, k.X, "le scénario doit distinguer l'arrondi par devis de l'arrondi par BC")
        s = self.sit(bc, pcts)
        self.assertEqual(self.total(s), k.M)
        self.assertEqual(self.ck(CK17_FORMULE), [])

    def test_T48_E_cumul_trois_situations_la_somme_des_situations_vaut_X(self):
        bc = self.monde(devis=[{"lignes": ["1000.00", "250.00", "750.00"], "total": "1900.00"}])
        s1 = self.sit(bc, [10, 20, 30])
        s2 = self.sit(bc, [40, 20, 60])
        s3 = self.sit(bc, [41, 25, 61])
        self.assertEqual(self.ck(CK17_FORMULE), [])
        self.assertEqual(self.ck(CK05_SOMME), [])
        self.assertEqual(self.total(s1) + self.total(s2) + self.total(s3), self.nette(bc))
        self.assertEqual(self.nette(bc), self.calcul_situation(bc, {}).X)       # N = X tant que rien n'avance : M = 0

    def test_T48_E_avoir_partiel_diminue_N_et_augmente_la_situation_suivante(self):
        bc = self.monde()
        s1 = self.sit(bc, [50, 50])                                    # 3000
        self.avoir(s1, "500.00")
        k = self.calcul_situation(bc, {})                              # X = 3000 (références inchangées), N = 2500
        self.assertEqual((k.X, k.N, k.M), (300000, 250000, 50000))
        s2 = self.sit(bc, [50, 50])                                    # M = 500 : la situation re-facture ce qui a été crédité
        self.assertEqual(self.un("SELECT total_ht, montant_deja_facture_ht FROM factures WHERE id=?", s2), ("500.00", "2500.00"))
        self.assertEqual(self.ck(CK17_FORMULE), [])

    def test_T48_E_recoupement_aleatoire_oracle_python_contre_CK17_SQL(self):
        """40 BC aléatoires (1 à 3 devis, remises, 1 à 4 situations croissantes, avoirs partiels) : CK-17 (SQL) et CK-05 restent vides."""
        rnd = random.Random(20261008)
        for tour in range(40):
            devis = []
            for _ in range(rnd.randint(1, 3)):
                lignes = [eur(rnd.randint(1, 300000)) for _ in range(rnd.randint(1, 4))]
                brut = sum(c(x) for x in lignes)
                devis.append({"lignes": lignes, "total": eur(brut - rnd.randint(0, brut // 4))})
            bc = self.monde(devis=devis)
            courant = {bl: 0 for bl in bc.lignes}
            for _ in range(rnd.randint(1, 4)):
                pcts = {bl: min(10000, courant[bl] + rnd.choice([0, 0, rnd.randint(1, 4000)])) for bl in bc.lignes}
                if self.calcul_situation(bc, pcts).M <= 0:
                    continue
                f = self.emettre_situation(bc, pcts)
                courant = pcts
                if rnd.random() < 0.3 and self.total(f) > 1:
                    self.avoir(f, eur(rnd.randint(1, self.total(f) - 1)))
            self.assertEqual(self.ck(CK17_FORMULE), [], f"tour {tour}")
            self.assertEqual(self.ck(CK05_SOMME), [], f"tour {tour}")
            self.assertEqual(self.ck(CK16["manquante"]) + self.ck(CK16["doublon"]) + self.ck(CK16["etrangere"]), [], f"tour {tour}")
            self.assertLessEqual(self.nette(bc), self.contractuel(bc), f"tour {tour}")

    def test_T48_E_CK17_detecte_un_montant_faux_d_un_centime(self):
        bc = self.monde()
        self.sit(bc, [50, 50])
        self.assertEqual(self.ck(CK17_FORMULE), [])
        f = self.facture(bc, "situation", "0.01", situation_numero=2, montant_deja_facture_ht="3000.00")
        self.assertEqual(self.ck(CK17_FORMULE), [(f,)])                      # aucune ligne : X = 0 ≠ 0.01 + 3000

    def test_T48_E_CK17_detecte_un_pourcentage_modifie(self):
        bc = self.monde()
        f = self.sit(bc, [50, 50])
        self.assertEqual(self.ck(CK17_FORMULE), [])
        self.db.execute("DROP TRIGGER tr_21_facture_lignes_no_update")
        self.db.execute("UPDATE facture_lignes SET avancement_cumule_pct='50.01' WHERE facture_id=? AND ordre=1", (f,))
        self.assertEqual(self.ck(CK17_FORMULE), [(f,)])

    def test_T48_E_pas_de_flottant_dans_le_schema_ni_dans_les_triggers(self):
        sql = T.sans_commentaires(SQL_006)
        for mot in ("REAL", "FLOAT", "DOUBLE", "ROUND(", "round(", "NUMERIC"):
            self.assertNotIn(mot, sql)
        self.assertNotRegex(sql, r"\*\s*1\.0|/\s*100\.0|CAST\([^)]*AS\s+REAL")


# ====================================================================================================================
# Groupe F — numérotation ACP / FAC / AVO (mécanisme V6 existant : numerotation_sequences, UNIQUE(numero), TR-02)
# ====================================================================================================================
class Numerotation(Base9):
    def sequences(self):
        return self.tous("SELECT type_objet, annee, dernier_numero, derniere_date FROM numerotation_sequences "
                         "WHERE type_objet IN ('ACP','FAC','AVO') ORDER BY type_objet, annee")

    def fixer_date(self, type_objet, annee, date):
        """Service : écrit derniere_date de la séquence (la ligne existe, créée par l'attribution du numéro)."""
        n = self.db.execute("UPDATE numerotation_sequences SET derniere_date=?, updated_at=? WHERE type_objet=? AND annee=?",
                            (date, TS2, type_objet, annee)).rowcount
        self.assertEqual(n, 1)

    def test_T48_F_prefixes_et_sequences_independantes(self):
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        a = self.acompte(bc, bc.d[0], "1000.00")
        s = self.emettre_situation(bc, {bc.lignes[0]: 5000, bc.lignes[1]: 5000})
        v = self.avoir(a, "100.00")
        numeros = {k: self.un("SELECT numero FROM factures WHERE id=?", i)[0] for k, i in (("a", a), ("s", s), ("v", v))}
        self.assertEqual(numeros, {"a": "ACP-00001-26", "s": "FAC-00001-26", "v": "AVO-00001-26"})
        self.assertEqual(self.sequences(), [("ACP", 26, 1, None), ("AVO", 26, 1, None), ("FAC", 26, 1, None)])

    def test_T48_F_FAC_est_partage_par_situation_et_solde(self):
        bc = self.monde()
        s1 = self.emettre_situation(bc, {bc.lignes[0]: 2500, bc.lignes[1]: 2500})
        s2 = self.emettre_situation(bc, {bc.lignes[0]: 5000, bc.lignes[1]: 5000})
        so = self.solde(bc)
        self.assertEqual([self.un("SELECT numero FROM factures WHERE id=?", i)[0] for i in (s1, s2, so)],
                         ["FAC-00001-26", "FAC-00002-26", "FAC-00003-26"])
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='FAC'")[0], 3)
        self.assertEqual(self.ck(CK01_DOUBLONS), [])
        self.assertEqual(self.ck(CK01_FORMAT_V6), [])
        self.assertEqual(self.ck(CK02_SEQUENCES), [])

    def test_T48_F_numero_unique_toutes_formes_de_doublon_refusees(self):
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        o = self.facture(bc, "situation", "50.00", situation_numero=1, montant_deja_facture_ht="0.00")
        n = self.un("SELECT numero FROM factures WHERE id=?", o)[0]
        avant = self.tous("SELECT * FROM factures")
        for verbe in ("INSERT", "INSERT OR REPLACE", "REPLACE"):
            with self.subTest(verbe=verbe):
                self.db.execute("SAVEPOINT x")
                try:
                    with self.assertRaises(sqlite3.IntegrityError):
                        self.inserer("factures", self.cols_facture(bc, "situation", "5.00", situation_numero=2, montant_deja_facture_ht="50.00", numero=n), verbe)
                finally:
                    self.db.execute("ROLLBACK TO x")
                    self.db.execute("RELEASE x")
        # INSERT OR IGNORE : le doublon est ignoré sans erreur, aucune ligne n'est ajoutée ni remplacée
        self.inserer("factures", self.cols_facture(bc, "situation", "5.00", situation_numero=2, montant_deja_facture_ht="50.00", numero=n), "INSERT OR IGNORE")
        self.assertEqual(self.tous("SELECT * FROM factures"), avant)

    def test_T48_F_prefixe_d_une_autre_famille_refuse(self):
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        self.refuse_check_f(bc, "acompte", "10.00", devis_id=bc.d[0], numero="FAC-00001-26")
        self.refuse_check_f(bc, "avoir", "10.00", origine_facture_id=self.facture(bc, "situation", "50.00", situation_numero=1, montant_deja_facture_ht="0.00"),
                            numero="ACP-00001-26")
        self.refuse_check_f(bc, "situation", "10.00", situation_numero=2, montant_deja_facture_ht="50.00", numero="AVO-00001-26")

    def test_T48_F_annee_du_numero_est_celle_de_date_emission(self):
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        self.refuse_check_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", numero="FAC-00001-27", date_emission="2026-12-31",
                            date_echeance="2027-01-30")
        self.accepte_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", numero="FAC-00001-27", date_emission="2027-01-02",
                       date_echeance="2027-02-01")

    def test_T48_F_une_sequence_par_annee(self):
        bc = self.monde(devis=[{"lignes": ["10000.00"]}])
        a = self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", date_emission="2026-12-30", date_echeance="2027-01-29")
        b = self.facture(bc, "situation", "10.00", situation_numero=2, montant_deja_facture_ht="10.00", date_emission="2027-01-02", date_echeance="2027-02-01")
        self.assertEqual([self.un("SELECT numero FROM factures WHERE id=?", i)[0] for i in (a, b)], ["FAC-00001-26", "FAC-00001-27"])
        self.assertEqual(self.sequences(), [("FAC", 26, 1, None), ("FAC", 27, 1, None)])

    def test_T48_F_une_emission_annulee_ne_consomme_aucun_numero(self):
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        self.db.execute("SAVEPOINT emission")
        self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='FAC'")[0], 1)
        self.db.execute("ROLLBACK TO emission")
        self.db.execute("RELEASE emission")
        self.assertEqual(self.sequences(), [])
        f = self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.assertEqual(self.un("SELECT numero FROM factures WHERE id=?", f)[0], "FAC-00001-26")

    def test_T48_F_un_refus_de_trigger_apres_attribution_annule_aussi_le_numero(self):
        """Dans la transaction d'émission, le refus d'un garde-fou (ici INV-57) annule l'attribution du numéro : pas de trou."""
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        self.db.execute("SAVEPOINT emission")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-57"):
            self.facture(bc, "situation", "100.01", situation_numero=1, montant_deja_facture_ht="0.00")
        self.db.execute("ROLLBACK TO emission")
        self.db.execute("RELEASE emission")
        self.assertEqual(self.sequences(), [])

    def test_T48_F_plafond_de_la_sequence_refuse_l_attribution(self):
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        self.un(ATTRIBUER, "FAC", 26)
        self.db.execute("UPDATE numerotation_sequences SET dernier_numero=99999 WHERE type_objet='FAC'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.un(ATTRIBUER, "FAC", 26)
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='FAC'")[0], 99999)
        f = self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", numero="FAC-99999-26")
        self.assertEqual(self.ck(CK02_SEQUENCES), [])
        self.assertIsNotNone(f)

    def test_T48_F_les_sequences_ne_se_modifient_pas_par_006(self):
        """006 n'ajoute ni table, ni colonne, ni trigger de numérotation : le mécanisme V6 de 001 est réutilisé tel quel."""
        sql = T.sans_commentaires(SQL_006)
        self.assertNotRegex(sql, r"(?i)numerotation_sequences\s*(SET|\()|INSERT\s+INTO\s+numerotation|UPDATE\s+numerotation|ALTER\s+TABLE")
        self.assertNotRegex(sql, r"(?i)high.?water|sequence_high_water")
        self.assertEqual(self.tous("SELECT name FROM sqlite_master WHERE name LIKE '%high%'"), [])

    # --- TR-02 : chronologie ------------------------------------------------------------------------------------------
    def monde_chrono(self):
        bc = self.monde(devis=[{"lignes": ["10000.00"], "acompte": ("montant", "1000.00")}])
        return bc

    def test_INV_24_TR02_date_anterieure_a_la_derniere_date_refusee(self):
        bc = self.monde_chrono()
        self.un(ATTRIBUER, "FAC", 26)
        self.fixer_date("FAC", 26, "2026-10-10")
        for type_, kw in (("situation", dict(situation_numero=1, montant_deja_facture_ht="0.00")),
                          ("solde", dict())):
            with self.subTest(type=type_):
                self.refuse_f("INV-24", bc, type_, "10000.00" if type_ == "solde" else "10.00", date_emission="2026-10-09", date_echeance="2026-11-08", **kw)

    def test_INV_24_TR02_date_egale_ou_posterieure_acceptee_et_garde_pure(self):
        bc = self.monde_chrono()
        self.un(ATTRIBUER, "FAC", 26)
        self.fixer_date("FAC", 26, "2026-10-10")
        for date in ("2026-10-10", "2026-10-11", "2026-12-31"):
            with self.subTest(date=date):
                self.accepte_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", date_emission=date, date_echeance="2027-01-30")
        f = self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", date_emission="2026-10-11", date_echeance="2026-11-30")
        # garde pure : le trigger n'écrit jamais derniere_date (c'est le service)
        self.assertEqual(self.un("SELECT derniere_date FROM numerotation_sequences WHERE type_objet='FAC'")[0], "2026-10-10")
        self.assertIsNotNone(f)

    def test_INV_24_TR02_trois_chronologies_independantes(self):
        bc = self.monde_chrono()
        for pre in ("ACP", "FAC", "AVO"):
            self.un(ATTRIBUER, pre, 26)
        self.fixer_date("FAC", 26, "2026-10-20")
        self.accepte_f(bc, "acompte", "100.00", devis_id=bc.d[0], date_emission="2026-10-01", date_echeance="2026-10-31")      # ACP : sa propre séquence
        s = self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", date_emission="2026-10-21", date_echeance="2026-11-30")
        self.accepte_f(bc, "avoir", "5.00", origine_facture_id=s, date_emission="2026-10-01")                                  # AVO : sa propre séquence
        self.fixer_date("AVO", 26, "2026-10-25")
        self.refuse_f("INV-24", bc, "avoir", "5.00", origine_facture_id=s, date_emission="2026-10-24")
        self.fixer_date("ACP", 26, "2026-10-25")
        self.refuse_f("INV-24", bc, "acompte", "100.00", devis_id=bc.d[0], date_emission="2026-10-24", date_echeance="2026-11-30")

    def test_INV_24_TR02_sans_ligne_de_sequence_ou_sans_date_aucune_contrainte(self):
        bc = self.monde_chrono()
        self.accepte_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", numero="FAC-00001-26", date_emission="2026-01-01",
                       date_echeance="2026-01-31")
        self.assertEqual(self.sequences(), [])                                                         # le trigger n'a rien créé
        self.un(ATTRIBUER, "FAC", 26)                                                                   # ligne sans derniere_date
        self.accepte_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", date_emission="2026-01-01", date_echeance="2026-01-31")

    def test_INV_24_TR02_autre_annee_non_concernee(self):
        bc = self.monde_chrono()
        self.un(ATTRIBUER, "FAC", 26)
        self.fixer_date("FAC", 26, "2026-12-31")
        self.accepte_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", date_emission="2027-01-01", date_echeance="2027-01-31")

    def test_INV_24_TR02_facture_importee_sans_sequence_acceptee(self):
        """Une facture importée (numéro libre, date ancienne) ne passe par aucune séquence : la chronologie ne la concerne pas."""
        bc = self.monde_chrono()
        self.accepte_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", origine="import", numero="LEGACY-9", date_emission="2020-01-01",
                       date_echeance="2020-01-31", legacy_id="L9", legacy_data="{}")

    # --- diagnostics -----------------------------------------------------------------------------------------------------
    def test_T48_F_CK02_numero_au_dela_de_la_sequence_est_signale(self):
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        f = self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", numero="FAC-00007-26")
        self.assertEqual(self.ck(CK02_SEQUENCES), [(f,)])
        self.un(ATTRIBUER, "FAC", 26)
        self.assertEqual(self.ck(CK02_SEQUENCES), [(f,)])
        self.db.execute("UPDATE numerotation_sequences SET dernier_numero=7 WHERE type_objet='FAC' AND annee=26")
        self.assertEqual(self.ck(CK02_SEQUENCES), [])

    def test_T48_F_CK02_ignore_les_factures_importees(self):
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", origine="import", numero="X-1", legacy_id="1", legacy_data="{}")
        self.assertEqual(self.ck(CK02_SEQUENCES), [])
        self.assertEqual(self.ck(CK01_FORMAT_V6), [])

    # --- concurrence ------------------------------------------------------------------------------------------------------
    def test_T48_F_BEGIN_IMMEDIATE_serialise_deux_emissions(self):
        """Deux connexions : la seconde ne peut pas ouvrir sa transaction d'écriture tant que la première n'a pas terminé ;
        elle reçoit alors le numéro suivant (aucun doublon, aucun trou)."""
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "metier.db")
            copie = sqlite3.connect(chemin, isolation_level=None)
            self.db.backup(copie)
            copie.close()
            a = sqlite3.connect(chemin, isolation_level=None, timeout=0)
            b = sqlite3.connect(chemin, isolation_level=None, timeout=0)
            for k in (a, b):
                k.execute("PRAGMA foreign_keys=ON")
                k.execute("PRAGMA recursive_triggers=ON")
            a.execute("BEGIN IMMEDIATE")
            n1 = a.execute(ATTRIBUER, ("FAC", 26)).fetchone()[0]
            with self.assertRaisesRegex(sqlite3.OperationalError, "locked"):
                b.execute("BEGIN IMMEDIATE")
            a.execute("COMMIT")
            b.execute("BEGIN IMMEDIATE")
            n2 = b.execute(ATTRIBUER, ("FAC", 26)).fetchone()[0]
            b.execute("COMMIT")
            self.assertEqual((n1, n2), (1, 2))
            a.close()
            b.close()

    def test_T48_F_restauration_limite_acceptee_pas_de_high_water_en_base_metier(self):
        """Limite explicitement acceptée : une base restaurée plus ancienne retrouve un compteur plus bas ; la protection (high-water) vit dans machine.db
        et 006 n'en ajoute aucune pour la numérotation des factures ni pour situation_numero."""
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        sauvegarde = sqlite3.connect(":memory:")
        self.db.backup(sauvegarde)
        f = self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.assertEqual(self.un("SELECT numero FROM factures WHERE id=?", f)[0], "FAC-00001-26")
        sauvegarde.row_factory = None
        self.assertEqual(sauvegarde.execute("SELECT count(*) FROM factures").fetchone()[0], 0)
        self.assertEqual(sauvegarde.execute("SELECT count(*) FROM numerotation_sequences WHERE type_objet='FAC'").fetchone()[0], 0)
        self.assertEqual(sauvegarde.execute("SELECT name FROM sqlite_master WHERE name LIKE '%high%'").fetchall(), [])
        sauvegarde.close()


# ====================================================================================================================
# Groupe G — immuabilité et contournements au niveau SQLite (UPDATE, DELETE, REPLACE, IGNORE, UPSERT, parents)
# ====================================================================================================================
class Immuabilite(Base9):
    def jeu(self):
        """BC avec un acompte, une situation à 50 % et un avoir partiel sur la situation."""
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        a = self.acompte(bc, bc.d[0], "1000.00")
        s = self.emettre_situation(bc, {bc.lignes[0]: 5000, bc.lignes[1]: 5000})
        v = self.avoir(s, "100.00")
        return types.SimpleNamespace(bc=bc, a=a, s=s, v=v)

    def photo(self):
        return (self.tous("SELECT * FROM factures ORDER BY id"), self.tous("SELECT * FROM facture_lignes ORDER BY id"),
                self.tous("SELECT * FROM numerotation_sequences ORDER BY id"))

    def refuse_sql(self, motif, sql, *args):
        """Le SQL est refusé par un trigger (message `motif`) et l'état des tables de facturation est inchangé."""
        avant = self.photo()
        m = self.tente(sql, *args)
        self.assertIsNotNone(m, f"accepté à tort : {sql}")
        self.assertRegex(m, motif)
        self.assertEqual(self.photo(), avant)

    def inchange(self, sql, *args):
        """Le SQL n'altère aucune ligne de facturation (refusé ou ignoré)."""
        avant = self.photo()
        self.tente(sql, *args)
        self.assertEqual(self.photo(), avant)

    # --- UPDATE ------------------------------------------------------------------------------------------------------
    def test_INV_53_chaque_colonne_de_factures_est_immuable_meme_sans_changement(self):
        j = self.jeu()
        for col in COLONNES_FACTURES:
            with self.subTest(colonne=col):
                self.refuse_sql("INV-53", f"UPDATE factures SET {col} = {col} WHERE id = ?", j.s)

    def test_INV_53_modification_effective_de_chaque_type_de_colonne(self):
        j = self.jeu()
        for col, val in (("total_ht", "1.00"), ("numero", "FAC-99999-26"), ("date_emission", "2026-10-06"), ("bc_id", 999), ("client_id", 999),
                         ("type", "solde"), ("situation_numero", 7), ("montant_deja_facture_ht", "0.00"), ("origine_facture_id", j.s),
                         ("devis_id", None), ("motif_avoir", "autre"), ("origine", "import"), ("client_snapshot", "{}"), ("created_at", TS)):
            with self.subTest(colonne=col):
                self.refuse_sql("INV-53", f"UPDATE factures SET {col} = ? WHERE id = ?", val, j.s)

    def test_INV_53_chaque_colonne_de_facture_lignes_est_immuable(self):
        j = self.jeu()
        ligne = self.un("SELECT id FROM facture_lignes WHERE facture_id=? ORDER BY ordre LIMIT 1", j.s)[0]
        for col in COLONNES_LIGNES:
            with self.subTest(colonne=col):
                self.refuse_sql("INV-53", f"UPDATE facture_lignes SET {col} = {col} WHERE id = ?", ligne)
        for col, val in (("montant_ht", "1.00"), ("avancement_cumule_pct", "99.00"), ("avancement_precedent_pct", "1.00"), ("ordre", 99),
                         ("bc_ligne_id", None), ("type_ligne", "prestation"), ("facture_id", j.a)):
            with self.subTest(modification=col):
                self.refuse_sql("INV-53", f"UPDATE facture_lignes SET {col} = ? WHERE id = ?", val, ligne)

    def test_INV_53_update_sans_where_et_toutes_clauses_de_conflit(self):
        j = self.jeu()
        for verbe in ("UPDATE", "UPDATE OR IGNORE", "UPDATE OR REPLACE", "UPDATE OR FAIL", "UPDATE OR ABORT", "UPDATE OR ROLLBACK"):
            for table, col, val in (("factures", "total_ht", "1.00"), ("facture_lignes", "montant_ht", "1.00")):
                with self.subTest(verbe=verbe, table=table):
                    self.refuse_sql("INV-53", f"{verbe} {table} SET {col} = '{val}'")
        self.assertIsNotNone(j)

    def test_INV_53_la_cle_primaire_non_plus_ne_se_deplace_pas(self):
        j = self.jeu()
        self.refuse_sql("INV-53", "UPDATE factures SET id = id + 1000 WHERE id = ?", j.v)
        self.refuse_sql("INV-53", "UPDATE facture_lignes SET id = id + 1000")

    # --- DELETE ------------------------------------------------------------------------------------------------------
    def test_INV_06_aucune_facture_ne_se_supprime(self):
        j = self.jeu()
        self.refuse_sql("INV-06", "DELETE FROM factures WHERE id = ?", j.v)
        self.refuse_sql("INV-06", "DELETE FROM factures WHERE id = ?", j.a)
        self.refuse_sql("INV-06", "DELETE FROM factures")
        self.refuse_sql("INV-06", "DELETE FROM factures WHERE 1=0 OR id IN (SELECT id FROM factures)")

    def test_INV_53_aucune_ligne_ne_se_supprime(self):
        j = self.jeu()
        self.refuse_sql("INV-53", "DELETE FROM facture_lignes WHERE facture_id = ?", j.s)
        self.refuse_sql("INV-53", "DELETE FROM facture_lignes")
        self.refuse_sql("INV-53", "DELETE FROM facture_lignes WHERE type_ligne = 'avancement'")

    def test_INV_53_suppression_puis_reinsertion_impossible(self):
        """Supprimer une ligne d'avancement pour la remplacer (même emplacement, autre montant) est refusé dès la suppression."""
        j = self.jeu()
        ligne = self.un("SELECT id, bc_ligne_id FROM facture_lignes WHERE facture_id=? AND type_ligne='avancement' ORDER BY ordre LIMIT 1", j.s)
        self.refuse_sql("INV-53", "DELETE FROM facture_lignes WHERE id = ?", ligne[0])
        # sans le DELETE, la réinsertion au même emplacement viole l'unicité
        m = self.tente("INSERT INTO facture_lignes (facture_id, ordre, bc_ligne_id, designation, quantite, unite, prix_unitaire_ht, remise_type, type_ligne, "
                       "montant_ht, avancement_precedent_pct, avancement_cumule_pct) VALUES (?, 1, ?, 'x', '1', 'ens', '1', 'aucune', 'avancement', '1.00', '0.00', '0.01')",
                       j.s, ligne[1])
        self.assertIsNotNone(m)

    # --- REPLACE / IGNORE / UPSERT ----------------------------------------------------------------------------------------
    def cols_doublon_facture(self, j, **kw):
        """Colonnes d'un avoir VALIDE (les triggers d'insertion l'acceptent) qui entre en conflit avec l'avoir du jeu, par id ou par numero."""
        ligne = self.un("SELECT * FROM factures WHERE id=?", j.v)
        cols = dict(zip(COLONNES_FACTURES, ligne))
        cols.update(kw)
        return cols

    def test_INV_06_REPLACE_sur_factures_refuse_par_id_et_par_numero(self):
        j = self.jeu()
        numero = self.un("SELECT numero FROM factures WHERE id=?", j.v)[0]
        for verbe in ("INSERT OR REPLACE", "REPLACE"):
            for nom, conflit in (("id", {"total_ht": "50.00"}), ("numero", {"id": 4242, "total_ht": "50.00", "numero": numero})):
                with self.subTest(verbe=verbe, conflit=nom):
                    cols = self.cols_doublon_facture(j, **conflit)
                    self.refuse_sql("INV-06", f"{verbe} INTO factures ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", *cols.values())

    def test_INV_53_REPLACE_sur_facture_lignes_refuse_par_id_ordre_et_unicite_avancement(self):
        j = self.jeu()
        syn = dict(zip(COLONNES_LIGNES, self.un("SELECT * FROM facture_lignes WHERE facture_id=? ORDER BY ordre LIMIT 1", j.v)))
        av = dict(zip(COLONNES_LIGNES, self.un("SELECT * FROM facture_lignes WHERE facture_id=? AND type_ligne='avancement' ORDER BY ordre LIMIT 1", j.s)))
        cas = (("id", {**syn, "montant_ht": "50.00"}), ("facture_id+ordre", {**syn, "id": 99999, "montant_ht": "50.00"}),
               ("facture_id+bc_ligne (avancement)", {**av, "id": 99998, "ordre": 77}))
        for verbe in ("INSERT OR REPLACE", "REPLACE"):
            for nom, cols in cas:
                with self.subTest(verbe=verbe, conflit=nom):
                    self.refuse_sql("INV-53", f"{verbe} INTO facture_lignes ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", *cols.values())

    def test_T48_G_INSERT_OR_IGNORE_n_ecrase_rien_et_ne_cree_rien_d_invalide(self):
        j = self.jeu()
        cols = self.cols_doublon_facture(j, total_ht="1.00")
        self.inchange(f"INSERT OR IGNORE INTO factures ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", *cols.values())
        base = dict(zip(COLONNES_LIGNES, self.un("SELECT * FROM facture_lignes WHERE facture_id=? AND ordre=1", j.s)))
        base["montant_ht"] = "1.00"
        self.inchange(f"INSERT OR IGNORE INTO facture_lignes ({','.join(base)}) VALUES ({','.join('?' * len(base))})", *base.values())

    def test_INV_53_UPSERT_DO_UPDATE_refuse_DO_NOTHING_neutre(self):
        """Les triggers BEFORE INSERT jugent d'abord la ligne proposée ; une ligne VALIDE qui entre en conflit déclenche DO UPDATE -> TR-20/TR-21 refusent."""
        j = self.jeu()
        numero_avoir = self.un("SELECT numero FROM factures WHERE id=?", j.v)[0]
        cols = self.cols_facture(j.bc, "avoir", "5.00", origine_facture_id=j.s, numero=numero_avoir)           # valide (somme des avoirs <= total), numéro déjà pris
        marques, noms = ",".join("?" * len(cols)), ",".join(cols)
        self.assertIsNone(self.tente(f"INSERT INTO factures ({noms}) VALUES ({marques}) ON CONFLICT (numero) DO NOTHING", *cols.values()))
        self.inchange(f"INSERT INTO factures ({noms}) VALUES ({marques}) ON CONFLICT (numero) DO NOTHING", *cols.values())
        self.refuse_sql("INV-53", f"INSERT INTO factures ({noms}) VALUES ({marques}) ON CONFLICT (numero) DO UPDATE SET total_ht = '1.00'", *cols.values())
        self.refuse_sql("INV-53", f"INSERT INTO factures ({noms}) VALUES ({marques}) ON CONFLICT (numero) DO UPDATE SET total_ht = excluded.total_ht", *cols.values())
        ligne = {"facture_id": j.a, "ordre": 1, "designation": "x", "quantite": "1", "unite": "ens", "prix_unitaire_ht": "1", "remise_type": "aucune",
                 "type_ligne": "synthese", "montant_ht": "1.00"}
        marques, noms = ",".join("?" * len(ligne)), ",".join(ligne)
        self.inchange(f"INSERT INTO facture_lignes ({noms}) VALUES ({marques}) ON CONFLICT (facture_id, ordre) DO NOTHING", *ligne.values())
        self.refuse_sql("INV-53", f"INSERT INTO facture_lignes ({noms}) VALUES ({marques}) ON CONFLICT (facture_id, ordre) DO UPDATE SET montant_ht = '1.00'",
                        *ligne.values())

    def test_T48_G_temoin_sans_recursive_triggers_le_replace_efface_la_facture(self):
        """Démontre pourquoi D-39 est obligatoire : sans recursive_triggers, INSERT OR REPLACE supprime une facture sans passer par TR-21."""
        t = Base9()
        t.db = migrer9(recursive=False)
        t._n = 0
        j = Immuabilite.jeu(t)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-06"):
            t.db.execute("DELETE FROM factures WHERE id=?", (j.v,))
        x = t.facture(j.bc, "avoir", "5.00", origine_facture_id=j.a)                                          # sans ligne : aucun enfant ne retient la FK
        cols = dict(zip(COLONNES_FACTURES, t.un("SELECT * FROM factures WHERE id=?", x)))
        cols["total_ht"] = "0.01"
        t.db.execute(f"INSERT OR REPLACE INTO factures ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", tuple(cols.values()))
        self.assertEqual(t.un("SELECT total_ht FROM factures WHERE id=?", x)[0], "0.01")                  # facture altérée : la protection exige D-39

    # --- verbes de conflit sur des factures invalides ----------------------------------------------------------------------
    def test_T48_G_aucun_verbe_de_conflit_ne_contourne_un_garde_fou(self):
        """Une facture invalide (ici : au-delà du contractuel, ou BC annulé, ou solde faux) n'entre jamais, quel que soit le verbe INSERT."""
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        avant = self.tous("SELECT count(*) FROM factures")
        for verbe in ("INSERT", "INSERT OR ABORT", "INSERT OR FAIL", "INSERT OR IGNORE", "INSERT OR REPLACE", "INSERT OR ROLLBACK", "REPLACE"):
            for type_, total, kw in (("situation", "100.01", dict(situation_numero=1, montant_deja_facture_ht="0.00")),
                                      ("solde", "99.99", {}), ("situation", "10.00", dict(situation_numero=1, montant_deja_facture_ht="1.00"))):
                with self.subTest(verbe=verbe, type=type_, total=total):
                    self.db.execute("SAVEPOINT v")
                    try:
                        self.inserer("factures", self.cols_facture(bc, type_, total, **kw), verbe)
                    except sqlite3.IntegrityError:
                        pass
                    finally:
                        n = self.un("SELECT count(*) FROM factures")[0]
                        self.db.execute("ROLLBACK TO v")
                        self.db.execute("RELEASE v")
                    self.assertEqual(n, 0)
        self.assertEqual(avant, [(0,)])

    def test_T48_G_aucun_verbe_de_conflit_ne_contourne_les_gardes_des_lignes(self):
        bc = self.monde(devis=[{"lignes": ["100.00"]}, {"lignes": ["50.00"]}])
        f = self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        for verbe in ("INSERT", "INSERT OR IGNORE", "INSERT OR REPLACE", "INSERT OR FAIL", "REPLACE"):
            with self.subTest(verbe=verbe):
                self.db.execute("SAVEPOINT v")
                try:
                    self.ligne_f.__func__(self, f, 1, "prestation", "10.00")                           # type de ligne interdit dans une situation
                except sqlite3.IntegrityError:
                    pass
                try:
                    self.inserer("facture_lignes", {"facture_id": f, "ordre": 1, "designation": "x", "quantite": "1", "unite": "ens", "prix_unitaire_ht": "10",
                                                    "remise_type": "aucune", "type_ligne": "prestation", "montant_ht": "10.00"}, verbe)
                except sqlite3.IntegrityError:
                    pass
                n = self.un("SELECT count(*) FROM facture_lignes")[0]
                self.db.execute("ROLLBACK TO v")
                self.db.execute("RELEASE v")
                self.assertEqual(n, 0)

    # --- parents : FK RESTRICT et immuabilités existantes ------------------------------------------------------------------
    def test_T48_G_les_parents_d_une_facture_ne_se_suppriment_pas(self):
        j = self.jeu()
        b, cli, d = j.bc.b, j.bc.cli, j.bc.d[0]
        ligne_bc = j.bc.lignes[0]
        for sql, args in (("DELETE FROM bons_commande WHERE id=?", (b,)), ("DELETE FROM clients WHERE id=?", (cli,)), ("DELETE FROM devis WHERE id=?", (d,)),
                          ("DELETE FROM bc_lignes WHERE id=?", (ligne_bc,)), ("DELETE FROM bc_devis WHERE bc_id=?", (b,)),
                          ("DELETE FROM bc_lignes", ()), ("DELETE FROM bons_commande", ()), ("DELETE FROM clients", ())):
            with self.subTest(sql=sql):
                self.refuse_sql("INV-|FOREIGN KEY", sql, *args)

    def test_T48_G_foreign_keys_actives_dans_la_connexion_de_test(self):
        self.assertEqual(self.un("PRAGMA foreign_keys")[0], 1)
        self.assertEqual(self.un("PRAGMA recursive_triggers")[0], 1)
        for sql in ("INSERT INTO factures (numero) VALUES ('X')",):
            self.assertIsNotNone(self.tente(sql))

    def test_T48_G_devis_et_BC_rattaches_sont_figes_apres_emission(self):
        """Le contractuel (Σ devis.total_ht) sur lequel reposent plafond et solde ne peut pas bouger sous une facture émise."""
        j = self.jeu()
        for sql in ("UPDATE devis SET total_ht='1.00'", "UPDATE devis_lignes SET total_ht='1.00'", "UPDATE bc_lignes SET total_ht='1.00'",
                    "UPDATE bc_lignes SET devis_ligne_id=devis_ligne_id", "UPDATE bc_devis SET devis_id=devis_id", "DELETE FROM bc_devis"):
            with self.subTest(sql=sql):
                self.refuse_sql("INV-", sql)
        self.assertEqual(self.contractuel(j.bc), 600000)

    def test_T48_G_le_cache_montant_contractuel_n_est_pas_une_source_pour_les_triggers(self):
        """montant_contractuel_ht (cache modifiable du BC) est ignoré par 006 : seuls bc_devis et devis.total_ht comptent."""
        j = self.jeu()
        self.db.execute("UPDATE bons_commande SET montant_contractuel_ht='1.00' WHERE id=?", (j.bc.b,))
        self.assertIsNotNone(self.tente_f(j.bc, "situation", "5000.00", situation_numero=2, montant_deja_facture_ht="2900.00"))   # 2900 + 5000 > 6000
        self.accepte_f(j.bc, "situation", "3100.00", situation_numero=2, montant_deja_facture_ht="2900.00")

    # --- valeurs limites et NULL -----------------------------------------------------------------------------------------------
    def test_T48_G_valeurs_nulles_et_limites_des_colonnes_de_factures(self):
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        sit = dict(situation_numero=1, montant_deja_facture_ht="0.00")
        for col in ("type", "bc_id", "client_id", "numero", "client_snapshot", "client_snapshot_version", "entreprise_snapshot", "entreprise_snapshot_version",
                    "chantier_snapshot", "chantier_snapshot_version", "date_emission", "total_ht", "created_at", "origine"):
            with self.subTest(null=col):
                self.assertIsNotNone(self.tente_f(bc, "situation", "10.00", **{**sit, col: None}))
        for numero_situation in (0, -1, None, 1.5, "a"):
            with self.subTest(situation_numero=numero_situation):
                self.assertIsNotNone(self.tente_f(bc, "situation", "10.00", situation_numero=numero_situation, montant_deja_facture_ht="0.00"))
        self.accepte_f(bc, "situation", "10.00", situation_numero=9223372036854775807, montant_deja_facture_ht="0.00")
        for total in ("", "0", "1", "1.0", "1.000", "-1.00", "+1.00", "1,00", "1e2", " 1.00", "01.00", "1.00.00", "NaN", "Infinity", "٣.٠٠"):
            with self.subTest(total_ht=total):
                self.assertIsNotNone(self.tente_f(bc, "situation", total, **sit))
        for total in (1, 1.0, b"1.00"):
            with self.subTest(total_ht_type=type(total).__name__):
                self.assertIsNotNone(self.tente_f(bc, "situation", total, **sit))
        self.refuse_f("INV-57", bc, "situation", "99999999999999.99", **sit)                             # grand montant : plafond contractuel

    def test_T48_G_valeurs_limites_des_lignes(self):
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        f = self.facture(bc, "solde", "100.00")
        base = {"facture_id": f, "ordre": 1, "designation": "x", "quantite": "1", "unite": "ens", "prix_unitaire_ht": "1", "remise_type": "aucune",
                "type_ligne": "prestation", "montant_ht": "1.00"}
        def essaie(**kw):
            cols = {k: v for k, v in {**base, **kw}.items() if v is not OMIT}
            self.db.execute("SAVEPOINT l")
            try:
                self.inserer("facture_lignes", cols)
                return None
            except sqlite3.IntegrityError as e:
                return str(e)
            finally:
                self.db.execute("ROLLBACK TO l")
                self.db.execute("RELEASE l")
        self.assertIsNone(essaie())
        self.assertIsNone(essaie(ordre=9223372036854775807))
        for ordre in (0, -1, None, 1.5, "x"):
            self.assertIsNotNone(essaie(ordre=ordre), ordre)
        for col in ("facture_id", "ordre", "designation", "quantite", "unite", "prix_unitaire_ht", "remise_type", "type_ligne", "montant_ht", "created_at"):
            self.assertIsNotNone(essaie(**{col: None}), col)
        self.assertIsNotNone(essaie(facture_id=999999))                                                    # parent inexistant : FK
        self.assertIsNotNone(essaie(bc_ligne_id=999999))


# ====================================================================================================================
# Groupe H — acomptes (par devis ; un seul acompte actif par devis ; plafond prévu = service)
# ====================================================================================================================
class Acomptes(Base9):
    def deux_devis(self, a1=("montant", "1000.00"), a2=("pourcentage", "20.00")):
        return self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": a1}, {"lignes": ["3000.00"], "acompte": a2}])

    # --- rattachement du devis (INV-189) -------------------------------------------------------------------------------
    def test_INV_189_le_devis_de_l_acompte_doit_etre_rattache_au_BC_de_la_facture(self):
        bc = self.deux_devis()
        autre = self.monde(devis=[{"lignes": ["500.00"], "acompte": ("montant", "50.00")}])
        self.accepte_f(bc, "acompte", "100.00", devis_id=bc.d[0])
        self.accepte_f(bc, "acompte", "100.00", devis_id=bc.d[1])
        self.refuse_f("INV-189", bc, "acompte", "100.00", devis_id=autre.d[0])                              # devis d'un autre BC
        self.refuse_f("INV-189", bc, "acompte", "100.00", devis_id=self.brouillon(client_id=bc.cli))        # devis non rattaché (brouillon)

    def test_INV_189_devis_inexistant_refuse_par_la_cle_etrangere_apres_le_trigger(self):
        bc = self.deux_devis()
        self.refuse_f("INV-189", bc, "acompte", "100.00", devis_id=999999)

    def test_INV_189_devis_rattache_apres_un_premier_acompte_peut_porter_le_sien(self):
        bc = self.monde(devis=[{"lignes": ["4000.00"], "acompte": ("montant", "1000.00")}])
        self.acompte(bc, bc.d[0], "1000.00")
        d2, _ = self.ajouter_devis(bc, ["2000.00"], acompte=("montant", "500.00"))
        self.accepte_f(bc, "acompte", "500.00", devis_id=d2)

    def test_T48_H_devis_obligatoire_pour_un_acompte_et_interdit_ailleurs(self):
        bc = self.deux_devis()
        # BEFORE INSERT précède les CHECK : sans devis, INV-189 refuse d'abord (le CHECK (type='acompte') = (devis_id IS NOT NULL) est testé en groupe C)
        self.refuse_f("INV-189", bc, "acompte", "100.00", devis_id=None)
        self.refuse_f("INV-189", bc, "acompte", "100.00", devis_id=OMIT)
        self.refuse_check_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", devis_id=bc.d[0])
        self.refuse_check_f(bc, "solde", "9000.00", devis_id=bc.d[0])

    # --- un seul acompte actif par devis (INV-52) -------------------------------------------------------------------------
    def test_INV_52_un_second_acompte_sur_le_meme_devis_est_refuse(self):
        bc = self.deux_devis()
        self.acompte(bc, bc.d[0], "1000.00")
        self.refuse_f("INV-52", bc, "acompte", "1.00", devis_id=bc.d[0])
        self.refuse_f("INV-52", bc, "acompte", "1000.00", devis_id=bc.d[0])                                 # pas de « complément d'acompte »
        self.accepte_f(bc, "acompte", "100.00", devis_id=bc.d[1])                                           # un autre devis : son propre acompte

    def test_INV_52_un_acompte_partiellement_credite_reste_actif(self):
        bc = self.deux_devis()
        a = self.acompte(bc, bc.d[0], "1000.00")
        self.avoir(a, "999.99")
        self.assertFalse(self.neutralisee(a))
        self.refuse_f("INV-52", bc, "acompte", "1.00", devis_id=bc.d[0])

    def test_INV_52_un_acompte_totalement_neutralise_libere_le_devis_avant_tout_solde(self):
        bc = self.deux_devis()
        a = self.acompte(bc, bc.d[0], "1000.00")
        self.avoir(a, "400.00")
        self.avoir(a, "600.00")                                                                             # deux avoirs : somme = total
        self.assertTrue(self.neutralisee(a))
        a2 = self.acompte(bc, bc.d[0], "700.00", date_emission="2026-10-06")
        self.assertIsNotNone(a2)
        self.refuse_f("INV-52", bc, "acompte", "1.00", devis_id=bc.d[0])                                    # le nouveau est actif à son tour
        self.assertEqual(self.nette(bc), 70000)

    def test_INV_52_le_remplacement_d_un_acompte_neutralise_suit_la_meme_regle_pour_chaque_devis(self):
        bc = self.deux_devis()
        a1 = self.acompte(bc, bc.d[0], "1000.00")
        a2 = self.acompte(bc, bc.d[1], "600.00")
        self.avoir(a2, "600.00")
        self.accepte_f(bc, "acompte", "100.00", devis_id=bc.d[1])                                           # devis 2 libéré
        self.refuse_f("INV-52", bc, "acompte", "100.00", devis_id=bc.d[0])                                  # devis 1 toujours actif
        self.assertIsNotNone(a1)

    def test_INV_52_apres_un_solde_meme_neutralise_aucun_nouvel_acompte(self):
        bc = self.deux_devis()
        a = self.acompte(bc, bc.d[0], "1000.00")
        self.avoir(a, "1000.00")
        so = self.solde(bc)
        self.avoir(so, self.un("SELECT total_ht FROM factures WHERE id=?", so)[0])
        self.assertTrue(self.neutralisee(so))
        self.refuse_f("INV-58", bc, "acompte", "100.00", devis_id=bc.d[0])
        self.refuse_f("INV-58", bc, "acompte", "100.00", devis_id=bc.d[1])

    # --- plafonds ---------------------------------------------------------------------------------------------------------
    def test_INV_57_un_acompte_ne_depasse_pas_le_total_de_son_devis(self):
        bc = self.deux_devis()
        self.accepte_f(bc, "acompte", "3000.00", devis_id=bc.d[1])
        self.refuse_f("INV-57", bc, "acompte", "3000.01", devis_id=bc.d[1])
        self.accepte_f(bc, "acompte", "6000.00", devis_id=bc.d[0])
        self.refuse_f("INV-57", bc, "acompte", "6000.01", devis_id=bc.d[0])

    def test_INV_57_la_facturation_nette_apres_acompte_ne_depasse_pas_le_contractuel(self):
        bc = self.deux_devis()                                                                              # contractuel 9000
        self.facture(bc, "situation", "7000.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.accepte_f(bc, "acompte", "2000.00", devis_id=bc.d[1])
        self.refuse_f("INV-57", bc, "acompte", "2000.01", devis_id=bc.d[1])

    def test_INV_57_apres_un_avoir_la_place_se_libere(self):
        bc = self.deux_devis()
        s = self.facture(bc, "situation", "9000.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.refuse_f("INV-57", bc, "acompte", "0.01", devis_id=bc.d[1])
        self.facture(bc, "avoir", "100.00", origine_facture_id=s)
        self.accepte_f(bc, "acompte", "100.00", devis_id=bc.d[1])
        self.refuse_f("INV-57", bc, "acompte", "100.01", devis_id=bc.d[1])

    def test_T48_H_une_situation_a_100_pour_cent_n_est_pas_un_solde_et_ferme_la_place_de_l_acompte(self):
        bc = self.deux_devis()
        s = self.emettre_situation(bc, {bl: 10000 for bl in bc.lignes})
        self.assertEqual(self.nette(bc), self.contractuel(bc))
        self.refuse_f("INV-57", bc, "acompte", "0.01", devis_id=bc.d[0])                                    # plafond contractuel, pas la règle du solde
        self.avoir(s, eur(self.total(s)))
        self.accepte_f(bc, "acompte", "100.00", devis_id=bc.d[0])                                           # aucun solde : l'acompte redevient possible

    # --- plafond prévu = règle de service ---------------------------------------------------------------------------------
    def test_T48_H_acompte_prevu_pourcentage_montant_aucun(self):
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("pourcentage", "30.00")}, {"lignes": ["1000.00"], "acompte": ("montant", "250.00")},
                               {"lignes": ["500.00"], "acompte": ("aucun", None)}])
        self.assertEqual([self.prevu_acompte(d) for d in bc.d], [180000, 25000, 0])
        self.assertEqual(self.prevu_bc(bc), 205000)

    def test_T48_H_acompte_prevu_pourcentage_sur_le_total_du_devis_remise_comprise_et_demi_superieur(self):
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "total": "5400.00", "acompte": ("pourcentage", "30.00")},
                               {"lignes": ["0.05"], "acompte": ("pourcentage", "50.00")}])
        self.assertEqual(self.prevu_acompte(bc.d[0]), 162000)                                               # 30 % de 5400 (jamais des lignes brutes)
        self.assertEqual(self.prevu_acompte(bc.d[1]), 3)                                                    # 0.025 -> 0.03

    def test_T48_H_le_prevu_du_BC_suit_les_devis_rattaches(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "100.00")}])
        self.assertEqual(self.prevu_bc(bc), 10000)
        self.ajouter_devis(bc, ["2000.00"], acompte=("pourcentage", "10.00"))
        self.assertEqual(self.prevu_bc(bc), 30000)                                                          # 100 + 10 % de 2000, aucun pourcentage sur le contractuel

    def test_T48_H_le_service_refuse_un_acompte_au_dela_du_prevu_ou_sans_acompte_prevu(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "100.00")}, {"lignes": ["500.00"], "acompte": ("aucun", None)}])
        with self.assertRaises(ErreurService):
            self.emettre_acompte(bc, bc.d[0], "100.01")
        with self.assertRaises(ErreurService):
            self.emettre_acompte(bc, bc.d[1], "1.00")
        self.assertEqual(self.un("SELECT count(*) FROM factures")[0], 0)
        a = self.emettre_acompte(bc, bc.d[0], "100.00")
        self.assertEqual(self.total(a), 10000)

    def test_T48_H_frontiere_SQL_service_le_schema_ne_porte_pas_le_plafond_prevu(self):
        """Le SQL accepte un acompte supérieur à l'acompte prévu (tant qu'il respecte le total du devis et le contractuel) : le plafond prévu est un service."""
        bc = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "100.00")}])
        self.accepte_f(bc, "acompte", "900.00", devis_id=bc.d[0])
        bc2 = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("aucun", None)}])
        self.accepte_f(bc2, "acompte", "1.00", devis_id=bc2.d[0])

    def test_T48_H_acompte_inferieur_au_prevu_accepte_mais_un_seul_actif(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "300.00")}])
        a = self.emettre_acompte(bc, bc.d[0], "120.00")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-52"):
            self.emettre_acompte(bc, bc.d[0], "180.00")
        self.assertIsNotNone(a)

    # --- lignes, états, client -----------------------------------------------------------------------------------------------
    def test_INV_62_un_acompte_ne_porte_qu_une_ligne_de_synthese(self):
        bc = self.deux_devis()
        a = self.facture(bc, "acompte", "100.00", devis_id=bc.d[0])
        for t_ in ("prestation", "deduction", "avancement", "zzz"):
            with self.subTest(type_ligne=t_):
                montant = "-1.00" if t_ == "deduction" else "1.00"
                extra = dict(avancement_precedent_pct="0.00", avancement_cumule_pct="1.00", bc_ligne_id=bc.lignes[0]) if t_ == "avancement" else {}
                m = self.tente("INSERT INTO facture_lignes (facture_id, ordre, designation, quantite, unite, prix_unitaire_ht, remise_type, type_ligne, montant_ht"
                               + "".join("," + k for k in extra) + ") VALUES (?, 1, 'x', '1', 'ens', '1', 'aucune', ?, ?" + ",?" * len(extra) + ")",
                               a, t_, montant, *extra.values())
                self.assertRegex(m or "", "INV-62")
        self.ligne_f(a, 1, "synthese", "100.00")

    def test_INV_48_le_client_de_l_acompte_est_celui_du_BC(self):
        bc = self.deux_devis()
        autre_client = self.client()
        self.refuse_f("INV-48", bc, "acompte", "100.00", devis_id=bc.d[0], client_id=autre_client)

    def test_T48_H_acompte_selon_l_etat_du_BC(self):
        """'gele' n'est pas un statut : frozen_at est posé, le statut reste 'en_cours' -> l'acompte reste possible. Terminé : INV-47 ; annulé (gelé ou non) : INV-188."""
        for etat, inv in (("en_cours", None), ("gele", None), ("termine", "INV-47"), ("annule", "INV-188"), ("annule_gele", "INV-188")):
            with self.subTest(etat=etat):
                bc = self.deux_devis()
                self.etat(bc, etat)
                if inv:
                    self.refuse_f(inv, bc, "acompte", "100.00", devis_id=bc.d[0])
                else:
                    self.accepte_f(bc, "acompte", "100.00", devis_id=bc.d[0])

    # --- diagnostics ----------------------------------------------------------------------------------------------------------------
    def test_T48_H_CK04_CK05_pour_un_acompte(self):
        bc = self.deux_devis()
        a = self.facture(bc, "acompte", "100.00", devis_id=bc.d[0])
        self.assertEqual(self.ck(CK04_SANS_LIGNES), [(a,)])                                                 # émission incomplète : aucune ligne
        self.assertEqual(self.ck(CK05_SOMME), [(a,)])
        self.ligne_f(a, 1, "synthese", "100.00")
        self.assertEqual(self.ck(CK04_SANS_LIGNES), [])
        self.assertEqual(self.ck(CK05_SOMME), [])
        b = self.facture(bc, "acompte", "50.00", devis_id=bc.d[1])
        self.ligne_f(b, 1, "synthese", "49.99")
        self.assertEqual(self.ck(CK05_SOMME), [(b,)])


# ====================================================================================================================
# Groupe I — situations : ordinal par BC, montant_deja, plafond, lignes d'avancement et référence ρ (INV-190)
# ====================================================================================================================
class Situations(Base9):
    P = lambda self, x: int(round(x * 100))                                                 # noqa: E731

    def sit(self, bc, pcts_pct, **kw):
        return self.emettre_situation(bc, {bl: self.P(p) for bl, p in zip(bc.lignes, pcts_pct)}, **kw)

    def lignes_av(self, f):
        """[(bc_ligne_id, précédent, cumulé, montant)] d'une situation, dans l'ordre des lignes."""
        return self.tous("SELECT bc_ligne_id, avancement_precedent_pct, avancement_cumule_pct, montant_ht FROM facture_lignes "
                         "WHERE facture_id=? AND type_ligne='avancement' ORDER BY ordre", f)

    def tente_ligne(self, f, ordre, bl, prec, cum, montant="0.00", type_ligne="avancement"):
        """Insertion brute (puis annulation) d'une ligne d'avancement : None si acceptée, sinon le message."""
        self.db.execute("SAVEPOINT tl")
        try:
            self.ligne_f(f, ordre, type_ligne, montant, bl, avancement_precedent_pct=prec, avancement_cumule_pct=cum)
            return None
        except sqlite3.IntegrityError as e:
            return str(e)
        finally:
            self.db.execute("ROLLBACK TO tl")
            self.db.execute("RELEASE tl")

    def essai_ligne(self, bc, numero, bl, prec, cum, montant="0.00"):
        """Crée (dans un SAVEPOINT annulé) une situation d'ordinal `numero` puis y insère une ligne d'avancement : None si acceptée, sinon le message.
        Rien ne subsiste : la situation d'essai ne devient jamais une référence."""
        self.db.execute("SAVEPOINT essai")
        try:
            f = self.situation_vide(bc, numero)
            self.ligne_f(f, 1, "avancement", montant, bl, avancement_precedent_pct=prec, avancement_cumule_pct=cum)
            return None
        except sqlite3.IntegrityError as e:
            return str(e)
        finally:
            self.db.execute("ROLLBACK TO essai")
            self.db.execute("RELEASE essai")

    def situation_vide(self, bc, numero, deja=None, **kw):
        """Facture de situation sans ligne (insertion brute) : montant_deja = facturation nette courante par défaut."""
        deja = eur(self.nette(bc)) if deja is None else deja
        return self.facture(bc, "situation", kw.pop("total", "10.00"), situation_numero=numero, montant_deja_facture_ht=deja, **kw)

    # --- ordinal ------------------------------------------------------------------------------------------------------
    def test_T48_I_situation_numero_unique_par_BC(self):
        bc = self.monde()
        self.situation_vide(bc, 1)
        self.refuse_check_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="10.00")
        autre = self.monde()
        self.accepte_f(autre, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")         # autre BC : même ordinal permis
        for verbe in ("INSERT OR REPLACE", "REPLACE"):
            with self.subTest(verbe=verbe):
                self.db.execute("SAVEPOINT x")
                with self.assertRaises(sqlite3.IntegrityError):
                    self.inserer("factures", self.cols_facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="10.00"), verbe)
                self.db.execute("ROLLBACK TO x")
                self.db.execute("RELEASE x")
        self.assertEqual(self.un("SELECT count(*) FROM factures WHERE bc_id=?", bc.b)[0], 1)

    def test_T48_I_l_ordinal_est_un_plus_max_du_service_et_n_est_pas_consomme_par_un_rollback(self):
        bc = self.monde()
        self.db.execute("SAVEPOINT emission")
        self.sit(bc, [10, 10])
        self.db.execute("ROLLBACK TO emission")
        self.db.execute("RELEASE emission")
        s1 = self.sit(bc, [10, 10])
        s2 = self.sit(bc, [20, 20])
        self.assertEqual([self.un("SELECT situation_numero FROM factures WHERE id=?", i)[0] for i in (s1, s2)], [1, 2])

    def test_T48_I_une_situation_neutralisee_garde_son_ordinal_qui_n_est_pas_reutilise(self):
        bc = self.monde()
        s1 = self.sit(bc, [10, 10])
        self.avoir(s1)
        s2 = self.sit(bc, [10, 10])
        self.assertEqual(self.un("SELECT situation_numero FROM factures WHERE id=?", s2)[0], 2)
        self.refuse_check_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht=eur(self.nette(bc)))        # l'ordinal 1 reste pris

    def test_T48_I_le_SQL_n_impose_ni_contiguite_ni_ordre_d_insertion_des_ordinaux(self):
        bc = self.monde(devis=[{"lignes": ["10000.00"]}])
        a = self.situation_vide(bc, 5)
        b = self.situation_vide(bc, 2)
        c_ = self.situation_vide(bc, 9)
        self.assertEqual(self.tous("SELECT situation_numero FROM factures WHERE bc_id=? ORDER BY situation_numero", bc.b), [(2,), (5,), (9,)])
        self.assertEqual(self.rho(bc), c_)
        self.assertEqual(self.rho(bc, avant=9), a)
        self.assertEqual(self.rho(bc, avant=5), b)

    def test_T48_I_ordinal_importe_conserve(self):
        bc = self.monde()
        self.accepte_f(bc, "situation", "10.00", situation_numero=7, montant_deja_facture_ht="0.00", origine="import", numero="OLD-7", legacy_id="7", legacy_data="{}")
        f = self.facture(bc, "situation", "10.00", situation_numero=7, montant_deja_facture_ht="0.00", origine="import", numero="OLD-7", legacy_id="7",
                         legacy_data="{}")
        self.assertEqual(self.un("SELECT situation_numero, origine FROM factures WHERE id=?", f), (7, "import"))
        self.assertEqual(self.un("SELECT COALESCE(MAX(situation_numero),0)+1 FROM factures WHERE bc_id=?", bc.b)[0], 8)

    # --- montant déjà facturé, plafond, solde ---------------------------------------------------------------------------------
    def test_INV_57_montant_deja_facture_est_la_facturation_nette_exacte(self):
        bc = self.monde(devis=[{"lignes": ["10000.00"], "acompte": ("montant", "1000.00")}])
        a = self.acompte(bc, bc.d[0], "1000.00")
        self.refuse_f("INV-57", bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.refuse_f("INV-57", bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="999.99")
        self.refuse_f("INV-57", bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="1000.01")
        self.accepte_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="1000.00")
        self.avoir(a, "300.00")
        self.refuse_f("INV-57", bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="1000.00")
        self.accepte_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="700.00")           # nette = acompte − avoir

    def test_INV_57_montant_deja_facture_compte_acomptes_situations_et_soldes_moins_avoirs(self):
        bc = self.monde(devis=[{"lignes": ["10000.00"], "acompte": ("montant", "1000.00")}])
        self.acompte(bc, bc.d[0], "1000.00")
        s1 = self.situation_vide(bc, 1, total="2000.00")
        self.situation_vide(bc, 2, total="500.00")
        self.avoir(s1, "250.00")
        self.assertEqual(self.nette(bc), 325000)
        self.accepte_f(bc, "situation", "10.00", situation_numero=3, montant_deja_facture_ht="3250.00")
        self.refuse_f("INV-57", bc, "situation", "10.00", situation_numero=3, montant_deja_facture_ht="3500.00")

    def test_INV_57_plafond_contractuel_exact_a_100_pour_cent(self):
        bc = self.monde()
        self.accepte_f(bc, "situation", "6000.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.refuse_f("INV-57", bc, "situation", "6000.01", situation_numero=1, montant_deja_facture_ht="0.00")
        self.situation_vide(bc, 1, total="3000.00")
        self.accepte_f(bc, "situation", "3000.00", situation_numero=2, montant_deja_facture_ht="3000.00")
        self.refuse_f("INV-57", bc, "situation", "3000.01", situation_numero=2, montant_deja_facture_ht="3000.00")

    def test_INV_57_le_plafond_suit_les_devis_rattaches(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        self.refuse_f("INV-57", bc, "situation", "1000.01", situation_numero=1, montant_deja_facture_ht="0.00")
        self.ajouter_devis(bc, ["500.00"])
        self.accepte_f(bc, "situation", "1500.00", situation_numero=1, montant_deja_facture_ht="0.00")

    def test_INV_58_aucune_situation_apres_un_solde_meme_neutralise(self):
        bc = self.monde()
        so = self.solde(bc)
        self.refuse_f("INV-58", bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="6000.00")
        self.avoir(so)
        self.assertTrue(self.neutralisee(so))
        self.refuse_f("INV-58", bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")

    def test_T48_I_une_situation_a_100_pour_cent_n_est_pas_un_solde(self):
        bc = self.monde()
        s = self.sit(bc, [100, 100])
        self.assertEqual(self.etat_bc(bc)[0], "en_cours")
        self.assertEqual(self.un("SELECT count(*) FROM factures WHERE type='solde'")[0], 0)
        self.assertEqual(self.ck(CK06_DATE_100), [])                                                             # aucun solde actif : date_100_facture reste NULL
        self.avoir(s, "100.00")
        s2 = self.sit(bc, [100, 100])                                                                           # re-facture ce qui a été crédité
        self.assertEqual(self.total(s2), 10000)
        self.assertEqual(self.ck(CK17_FORMULE), [])

    def test_T48_I_le_service_refuse_une_situation_non_strictement_positive(self):
        bc = self.monde()
        self.sit(bc, [50, 50])
        with self.assertRaises(ValueError):
            self.sit(bc, [50, 50])                                                                              # M = 0
        s = self.facture(bc, "situation", "0.01", situation_numero=2, montant_deja_facture_ht="3000.00")        # le SQL, lui, accepte un montant positif quelconque
        self.assertIsNotNone(s)
        self.refuse_check_f(bc, "situation", "0.00", situation_numero=3, montant_deja_facture_ht="3000.01")      # 0.00 interdit hors solde (CHECK)

    # --- lignes d'avancement : validité unitaire -----------------------------------------------------------------------------------
    def test_INV_190_premiere_situation_precedent_zero_pour_toute_ligne(self):
        bc = self.monde()
        f = self.situation_vide(bc, 1)
        self.assertIsNone(self.tente_ligne(f, 1, bc.lignes[0], "0.00", "40.00", "1600.00"))
        for prec in ("0.01", "10.00", "100.00"):
            with self.subTest(precedent=prec):
                self.assertRegex(self.tente_ligne(f, 1, bc.lignes[0], prec, "100.00", "4000.00"), "INV-190")

    def test_INV_190_precedent_egal_au_cumule_de_la_situation_de_reference(self):
        bc = self.monde()
        self.sit(bc, [40, 25])
        f = self.situation_vide(bc, 2)
        self.assertIsNone(self.tente_ligne(f, 1, bc.lignes[0], "40.00", "50.00", "400.00"))
        self.assertIsNone(self.tente_ligne(f, 1, bc.lignes[1], "25.00", "25.00", "0.00"))
        for prec in ("0.00", "39.99", "40.01", "25.00"):
            with self.subTest(precedent=prec):
                self.assertRegex(self.tente_ligne(f, 1, bc.lignes[0], prec, "100.00", "1.00"), "INV-190")

    def test_INV_190_precedent_et_cumule_bornes_et_ordonnes_par_les_CHECK(self):
        bc = self.monde()
        f = self.situation_vide(bc, 1)
        for prec, cum in (("0.00", "100.01"), ("0.00", "-0.01"), ("0.00", "1.5"), ("0.00", None), (None, "10.00"), ("5.00", "4.99")):
            with self.subTest(prec=prec, cum=cum):
                m = self.tente_ligne(f, 1, bc.lignes[0], prec, cum)
                self.assertIsNotNone(m)
        self.assertIsNone(self.tente_ligne(f, 1, bc.lignes[0], "0.00", "100.00", "4000.00"))
        self.assertIsNone(self.tente_ligne(f, 1, bc.lignes[0], "0.00", "0.00", "0.00"))

    def test_INV_190_une_ligne_peut_valoir_zero_euro(self):
        bc = self.monde()
        f = self.situation_vide(bc, 1)
        self.assertIsNone(self.tente_ligne(f, 1, bc.lignes[0], "0.00", "0.00", "0.00"))
        self.assertIsNone(self.tente_ligne(f, 1, bc.lignes[0], "0.00", "0.01", "0.00"))                        # 0.0001 x 4000 -> 0.40 -> 0 centime arrondi

    # --- INV-62 : types et BC ----------------------------------------------------------------------------------------------------------
    def test_INV_62_une_situation_ne_porte_que_des_lignes_d_avancement_et_de_deduction(self):
        bc = self.monde()
        f = self.situation_vide(bc, 1)
        for t_, montant in (("prestation", "1.00"), ("synthese", "1.00"), ("zzz", "1.00")):          # `zzz` : valeur hors énumération, refusée par le trigger avant le CHECK
            with self.subTest(type_ligne=t_):
                self.db.execute("SAVEPOINT t")
                try:
                    self.ligne_f(f, 1, t_, montant)
                    self.fail("accepté à tort")
                except sqlite3.IntegrityError as e:
                    self.assertRegex(str(e), "INV-62")
                finally:
                    self.db.execute("ROLLBACK TO t")
                    self.db.execute("RELEASE t")
        self.ligne_f(f, 1, "deduction", "-1.00")

    def test_INV_62_ligne_d_une_ligne_de_BC_etrangere_refusee(self):
        bc = self.monde()
        autre = self.monde()
        f = self.situation_vide(bc, 1)
        self.assertRegex(self.tente_ligne(f, 1, autre.lignes[0], "0.00", "10.00"), "INV-62")
        self.assertIsNone(self.tente_ligne(f, 1, bc.lignes[1], "0.00", "10.00"))

    def test_INV_62_ligne_de_BC_inexistante_refusee_par_la_cle_etrangere(self):
        bc = self.monde()
        f = self.situation_vide(bc, 1)
        m = self.tente_ligne(f, 1, 999999, "0.00", "10.00")
        self.assertIsNotNone(m)
        self.assertNotIn("INV-62", m)

    # --- les 13 tests agressifs de lignes ------------------------------------------------------------------------------------------------------
    def test_T48_I_L01_ligne_manquante_acceptee_par_le_SQL_signalee_par_CK16_et_CK17(self):
        """Service : une ligne d'avancement par ligne de BC applicable. Le SQL n'impose pas l'exhaustivité ; CK-16 puis CK-17 la contrôlent."""
        bc = self.monde()
        k = self.calcul_situation(bc, {bc.lignes[0]: 5000, bc.lignes[1]: 5000})
        f = self.facture(bc, "situation", eur(k.M), situation_numero=1, montant_deja_facture_ht="0.00")
        self.ligne_f(f, 1, "avancement", "2000.00", bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="50.00")        # la 2e ligne manque
        self.assertEqual(self.ck(CK16["manquante"]), [(f, bc.lignes[1])])
        self.assertEqual(self.ck(CK05_SOMME), [(f,)])
        self.assertEqual(self.ck(CK17_FORMULE), [(f,)])

    def test_T48_I_L02_ligne_en_trop_doublon_de_ligne_de_BC_refuse_et_type_interdit_refuse(self):
        bc = self.monde()
        s = self.sit(bc, [50, 50])
        m = self.tente_ligne(s, 50, bc.lignes[0], "0.00", "50.00", "2000.00")                                   # même ligne de BC une seconde fois
        self.assertIsNotNone(m)
        self.assertNotIn("INV-", m)                                                                             # unicité (index partiel), pas un trigger
        self.assertEqual(self.ck(CK16["doublon"]), [])

    def test_T48_I_L03_ligne_d_un_autre_BC_refusee(self):
        bc = self.monde()
        autre = self.monde()
        s = self.situation_vide(bc, 1)
        self.assertRegex(self.tente_ligne(s, 1, autre.lignes[1], "0.00", "50.00", "100.00"), "INV-62")
        self.assertEqual(self.ck(CK16["etrangere"]), [])

    def test_T48_I_L04_doublon_par_ordre_different_ou_replace_refuse(self):
        bc = self.monde()
        s = self.sit(bc, [50, 50])
        cols = {"facture_id": s, "ordre": 60, "bc_ligne_id": bc.lignes[0], "designation": "dup", "quantite": "1", "unite": "ens", "prix_unitaire_ht": "1",
                "remise_type": "aucune", "type_ligne": "avancement", "montant_ht": "2000.00", "avancement_precedent_pct": "0.00", "avancement_cumule_pct": "50.00"}
        avant = self.photo_lignes()
        for verbe in ("INSERT", "INSERT OR ABORT", "INSERT OR FAIL"):
            with self.subTest(verbe=verbe):
                self.db.execute("SAVEPOINT d")
                with self.assertRaises(sqlite3.IntegrityError):
                    self.inserer("facture_lignes", cols, verbe)
                self.db.execute("ROLLBACK TO d")
                self.db.execute("RELEASE d")
        for verbe in ("INSERT OR REPLACE", "REPLACE"):
            with self.subTest(verbe=verbe):
                self.db.execute("SAVEPOINT d")
                with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-53"):
                    self.inserer("facture_lignes", cols, verbe)
                self.db.execute("ROLLBACK TO d")
                self.db.execute("RELEASE d")
        self.inserer("facture_lignes", cols, "INSERT OR IGNORE")
        self.assertEqual(self.photo_lignes(), avant)

    def photo_lignes(self):
        return self.tous("SELECT * FROM facture_lignes ORDER BY id")

    def test_T48_I_L05_ordre_d_insertion_different_des_lignes_meme_resultat(self):
        """Lignes insérées dans l'ordre inverse, déductions avant avancements : le SQL accepte, CK-05/16/17 sont satisfaits."""
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "total": "5400.00"}])
        k = self.calcul_situation(bc, {bc.lignes[0]: 5000, bc.lignes[1]: 5000})
        f = self.facture(bc, "situation", eur(k.M), situation_numero=1, montant_deja_facture_ht="0.00")
        self.ligne_f(f, 3, "deduction", eur(-k.reductions[bc.d[0]]))
        self.ligne_f(f, 2, "avancement", eur(k.lignes[1][5]), bc.lignes[1], avancement_precedent_pct="0.00", avancement_cumule_pct="50.00")
        self.ligne_f(f, 1, "avancement", eur(k.lignes[0][5]), bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="50.00")
        self.assertEqual(self.ck(CK05_SOMME) + self.ck(CK17_FORMULE) + self.ck(CK16["manquante"]) + self.ck(CK04_SANS_LIGNES), [])

    def test_T48_I_L06_INSERT_OR_REPLACE_d_une_ligne_d_avancement_refuse(self):
        bc = self.monde()
        s = self.sit(bc, [50, 50])
        ligne = dict(zip(COLONNES_LIGNES, self.un("SELECT * FROM facture_lignes WHERE facture_id=? AND type_ligne='avancement' ORDER BY ordre LIMIT 1", s)))
        ligne["avancement_cumule_pct"] = "99.00"
        ligne["montant_ht"] = "3960.00"
        for verbe in ("INSERT OR REPLACE", "REPLACE"):
            with self.subTest(verbe=verbe):
                self.db.execute("SAVEPOINT r")
                with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-53"):
                    self.inserer("facture_lignes", ligne, verbe)
                self.db.execute("ROLLBACK TO r")
                self.db.execute("RELEASE r")
        self.assertEqual(self.lignes_av(s)[0][2], "50.00")

    def test_T48_I_L07_modification_apres_emission_refusee(self):
        bc = self.monde()
        s = self.sit(bc, [50, 50])
        for col, val in (("avancement_cumule_pct", "60.00"), ("avancement_precedent_pct", "10.00"), ("montant_ht", "1.00"), ("bc_ligne_id", bc.lignes[1])):
            with self.subTest(colonne=col):
                self.assertRegex(self.tente(f"UPDATE facture_lignes SET {col}=? WHERE facture_id=? AND ordre=1", val, s) or "", "INV-53")
        self.assertEqual(self.lignes_av(s)[0], (bc.lignes[0], "0.00", "50.00", "2000.00"))

    def test_T48_I_L08_suppression_puis_reinsertion_refusee(self):
        bc = self.monde()
        s = self.sit(bc, [50, 50])
        self.assertRegex(self.tente("DELETE FROM facture_lignes WHERE facture_id=? AND ordre=1", s) or "", "INV-53")
        self.assertRegex(self.tente("DELETE FROM facture_lignes WHERE facture_id=?", s) or "", "INV-53")
        self.assertEqual(len(self.lignes_av(s)), 2)

    def test_T48_I_L09_ligne_ajoutee_entre_deux_situations_repart_de_zero(self):
        """Une ligne de BC (nouveau devis) créée entre S1 et S2 n'est pas applicable à S1 (CK-16 vide), est obligatoire dans S2 et y part de 0.00 bien que
        ρ = S1 existe ; la situation suivante la reprend depuis S2."""
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"]}])
        s1 = self.sit(bc, [50, 50], created_at="2026-10-05T12:00:00.000Z")
        d2, nouvelles = self.ajouter_devis(bc, ["1000.00"], apres="2026-10-06T00:00:00.000Z")
        self.assertEqual(self.ck(CK16["manquante"]), [])
        k = self.calcul_situation(bc, {bc.lignes[0]: 5000, bc.lignes[1]: 5000, nouvelles[0]: 3000})
        self.assertEqual([x[3] for x in k.lignes], [5000, 5000, 0])                                              # précédents : 50, 50 puis 0
        s2 = self.emettre_situation(bc, {bc.lignes[0]: 5000, bc.lignes[1]: 5000, nouvelles[0]: 3000}, created_at="2026-10-07T12:00:00.000Z")
        self.assertEqual(self.lignes_av(s2)[2], (nouvelles[0], "0.00", "30.00", "300.00"))
        self.assertEqual(self.ck(CK16["manquante"]), [])
        self.assertEqual(self.ck(CK17_FORMULE), [])
        self.assertIsNone(self.essai_ligne(bc, 3, nouvelles[0], "30.00", "40.00", "100.00"))
        self.assertRegex(self.essai_ligne(bc, 3, nouvelles[0], "0.00", "40.00", "100.00"), "INV-190")               # S2 est désormais la référence
        self.assertIsNotNone(s1)

    def test_T48_I_L09b_ligne_ajoutee_avant_la_situation_est_obligatoire_et_son_absence_signalee(self):
        bc = self.monde(devis=[{"lignes": ["4000.00"]}])
        self.sit(bc, [50], created_at="2026-10-05T12:00:00.000Z")
        d2, nouvelles = self.ajouter_devis(bc, ["1000.00"], apres="2026-10-06T00:00:00.000Z")
        k = self.calcul_situation(bc, {bc.lignes[0]: 6000})
        f = self.facture(bc, "situation", eur(k.M), situation_numero=2, montant_deja_facture_ht=eur(k.N), created_at="2026-10-07T12:00:00.000Z")
        self.ligne_f(f, 1, "avancement", eur(k.lignes[0][5]), bc.lignes[0], avancement_precedent_pct="50.00", avancement_cumule_pct="60.00")
        self.assertEqual(self.ck(CK16["manquante"]), [(f, nouvelles[0])])

    def test_T48_I_L10_toutes_les_lignes_a_zero_sauf_une(self):
        bc = self.monde(devis=[{"lignes": ["1000.00", "2000.00", "3000.00"]}])
        s1 = self.sit(bc, [0, 0, 25])
        self.assertEqual([x[1:3] for x in self.lignes_av(s1)], [("0.00", "0.00"), ("0.00", "0.00"), ("0.00", "25.00")])
        self.assertEqual([x[3] for x in self.lignes_av(s1)], ["0.00", "0.00", "750.00"])
        s2 = self.sit(bc, [10, 0, 25])                                                                            # seule la ligne 1 avance
        self.assertEqual(self.total(s2), 10000)
        self.assertEqual([x[1:3] for x in self.lignes_av(s2)], [("0.00", "10.00"), ("0.00", "0.00"), ("25.00", "25.00")])
        self.assertEqual(self.ck(CK17_FORMULE) + self.ck(CK05_SOMME) + self.ck(CK16["manquante"]), [])

    def test_T48_I_L11_progression_a_100_pour_cent_reste_une_situation(self):
        bc = self.monde(devis=[{"lignes": ["1000.00", "2000.00"], "total": "2700.00"}])
        s1 = self.sit(bc, [100, 100])
        self.assertEqual(self.total(s1), 270000)
        self.assertEqual(self.contractuel(bc) - self.nette(bc), 0)
        self.assertEqual(self.un("SELECT count(*) FROM factures WHERE type='solde'")[0], 0)
        with self.assertRaises(ValueError):
            self.sit(bc, [100, 100])                                                                              # plus rien à facturer
        self.refuse_f("INV-57", bc, "situation", "0.01", situation_numero=2, montant_deja_facture_ht="2700.00")
        self.assertEqual(self.ck(CK17_FORMULE), [])

    def test_T48_I_L12_neutralisation_de_la_derniere_situation_la_precedente_redevient_reference(self):
        bc = self.monde()
        s1 = self.sit(bc, [30, 30])
        s2 = self.sit(bc, [60, 60])
        self.assertEqual(self.rho(bc), s2)
        self.avoir(s2)
        self.assertTrue(self.neutralisee(s2))
        self.assertEqual(self.rho(bc), s1)
        s3 = self.sit(bc, [70, 70])
        self.assertEqual([x[1] for x in self.lignes_av(s3)], ["30.00", "30.00"])                                   # précédent = cumulé de S1
        f = self.situation_vide(bc, 4)
        self.assertRegex(self.tente_ligne(f, 1, bc.lignes[0], "60.00", "70.00") or "", "INV-190")                  # S2 n'est plus la référence... (S3 l'est)
        self.assertRegex(self.tente_ligne(f, 1, bc.lignes[0], "30.00", "70.00") or "", "INV-190")                  # ... ni S1 : ρ = S3
        self.assertIsNone(self.tente_ligne(f, 1, bc.lignes[0], "70.00", "75.00"))

    def test_T48_I_L13_reprise_correcte_de_la_reference_dans_tous_les_cas(self):
        bc = self.monde()
        l0 = bc.lignes[0]
        s1 = self.sit(bc, [10, 10])
        s2 = self.sit(bc, [20, 20])
        s3 = self.sit(bc, [30, 30])
        # (a) avoir partiel : ρ inchangée
        self.avoir(s3, "1.00")
        self.assertEqual(self.rho(bc), s3)
        self.assertIsNone(self.essai_ligne(bc, 4, l0, "30.00", "31.00"))
        # (b) neutralisation d'une situation intermédiaire : ρ reste S3 tant que S3 est active
        self.neutraliser(s2)
        self.assertEqual(self.rho(bc), s3)
        self.assertIsNone(self.essai_ligne(bc, 4, l0, "30.00", "31.00"))
        self.assertRegex(self.essai_ligne(bc, 4, l0, "20.00", "31.00") or "", "INV-190")
        # (c) neutralisation de la dernière : repli sur S1 (S2, neutralisée, est sautée)
        self.neutraliser(s3)
        self.assertEqual(self.rho(bc), s1)
        self.assertIsNone(self.essai_ligne(bc, 4, l0, "10.00", "11.00"))
        self.assertRegex(self.essai_ligne(bc, 4, l0, "30.00", "31.00") or "", "INV-190")
        self.assertRegex(self.essai_ligne(bc, 4, l0, "20.00", "31.00") or "", "INV-190")
        # (d) tout neutralisé : 0 %
        self.neutraliser(s1)
        self.assertIsNone(self.rho(bc))
        self.assertIsNone(self.essai_ligne(bc, 4, l0, "0.00", "5.00"))
        self.assertRegex(self.essai_ligne(bc, 4, l0, "10.00", "11.00") or "", "INV-190")
        # (e) la situation suivante émise par le service repart de 0 %
        s4 = self.sit(bc, [5, 5])
        self.assertEqual([x[1] for x in self.lignes_av(s4)], ["0.00", "0.00"])
        self.assertEqual(self.rho(bc), s4)

    def test_T48_I_L13b_la_reference_suit_l_ordinal_et_non_l_ordre_d_insertion(self):
        bc = self.monde(devis=[{"lignes": ["10000.00"]}])
        b = self.situation_vide(bc, 2, total="10.00")
        self.ligne_f(b, 1, "avancement", "100.00", bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="1.00")
        a = self.situation_vide(bc, 1, total="10.00", deja="10.00")
        self.assertIsNone(self.tente_ligne(a, 1, bc.lignes[0], "0.00", "0.50"))                                    # ordinal 1 : aucune référence antérieure
        self.assertRegex(self.tente_ligne(a, 1, bc.lignes[0], "1.00", "2.00") or "", "INV-190")
        c_ = self.situation_vide(bc, 3, deja="20.00")
        self.assertIsNone(self.tente_ligne(c_, 1, bc.lignes[0], "1.00", "2.00"))                                    # ρ = ordinal 2 (insérée avant l'ordinal 1)

    def test_T48_I_L13c_une_ligne_absente_de_la_reference_repart_a_zero_meme_si_la_reference_existe(self):
        bc = self.monde()
        r_ = self.situation_vide(bc, 1)
        self.ligne_f(r_, 1, "avancement", "100.00", bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="2.50")      # S1 ne porte que la ligne 1
        f = self.situation_vide(bc, 2, deja="10.00")
        self.assertIsNone(self.tente_ligne(f, 1, bc.lignes[0], "2.50", "3.00"))
        self.assertIsNone(self.tente_ligne(f, 1, bc.lignes[1], "0.00", "3.00"))
        self.assertRegex(self.tente_ligne(f, 1, bc.lignes[1], "2.50", "3.00") or "", "INV-190")

    def test_T48_I_L13d_la_reference_ne_depasse_pas_la_situation_courante(self):
        """Une situation d'ordinal supérieur n'est jamais la référence d'une situation d'ordinal inférieur (même insérée avant)."""
        bc = self.monde(devis=[{"lignes": ["10000.00"]}])
        hauts = self.situation_vide(bc, 9)
        self.ligne_f(hauts, 1, "avancement", "100.00", bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="77.00")
        bas = self.situation_vide(bc, 3, deja="10.00")
        self.assertIsNone(self.tente_ligne(bas, 1, bc.lignes[0], "0.00", "5.00"))
        self.assertRegex(self.tente_ligne(bas, 1, bc.lignes[0], "77.00", "78.00") or "", "INV-190")

    def test_T48_I_L13e_la_reference_est_propre_au_BC(self):
        bc = self.monde()
        autre = self.monde()
        self.sit(autre, [80, 80])
        f = self.situation_vide(bc, 1)
        self.assertIsNone(self.tente_ligne(f, 1, bc.lignes[0], "0.00", "10.00"))

    def test_T48_I_ROT_la_reference_du_trigger_egale_l_oracle_Python_sur_tirages_aleatoires(self):
        """Tirages : situations, avoirs partiels/totaux dans un ordre quelconque. Le précédent de l'oracle est accepté ; le précédent ±0.01 est refusé."""
        rnd = random.Random(190)
        for tour in range(30):
            bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00", "1000.00"]}])
            courant = {bl: 0 for bl in bc.lignes}
            sits = []
            for _ in range(rnd.randint(2, 5)):
                pcts = {bl: min(10000, courant[bl] + rnd.choice([0, rnd.randint(1, 3000)])) for bl in bc.lignes}
                if self.calcul_situation(bc, pcts).M <= 0:
                    continue
                f = self.emettre_situation(bc, pcts)
                sits.append(f)
                courant = pcts
                if rnd.random() < 0.4:
                    cible = rnd.choice(sits)
                    reste = self.total(cible) - sum(c(x) for (x,) in self.tous("SELECT total_ht FROM factures WHERE origine_facture_id=?", cible))
                    if reste > 0:
                        self.avoir(cible, eur(reste if rnd.random() < 0.5 else max(1, reste // 2)))
                        courant = {bl: v for bl, v in (self.precedents(bc.b) or {}).items()}
                        courant = {bl: courant.get(bl, 0) for bl in bc.lignes}
            f = self.situation_vide(bc, 99, deja=eur(self.nette(bc)))
            ref = self.precedents(bc.b, avant=99)
            for bl in bc.lignes:
                attendu = ref.get(bl, 0)
                self.assertIsNone(self.tente_ligne(f, 1, bl, eur(attendu), eur(min(10000, attendu + 5))), f"tour {tour}")
                if attendu < 10000 - 5:
                    self.assertRegex(self.tente_ligne(f, 1, bl, eur(attendu + 1), eur(attendu + 5)) or "", "INV-190", f"tour {tour}")
                if attendu > 0:
                    self.assertRegex(self.tente_ligne(f, 1, bl, eur(attendu - 1), eur(attendu + 5)) or "", "INV-190", f"tour {tour}")


# ====================================================================================================================
# Groupe J — solde : contractuel − facturation nette, exactement ; un seul solde actif ; fermeture commerciale du BC
# ====================================================================================================================
class Solde(Base9):
    def sit(self, bc, pcts_pct, **kw):
        return self.emettre_situation(bc, {bl: int(round(p * 100)) for bl, p in zip(bc.lignes, pcts_pct)}, **kw)

    def test_INV_58_le_solde_est_le_contractuel_moins_la_facturation_nette_exactement(self):
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        self.accepte_f(bc, "solde", "6000.00")
        for faux in ("5999.99", "6000.01", "0.00", "1.00", "12000.00"):
            self.refuse_f("INV-58", bc, "solde", faux)
        a = self.acompte(bc, bc.d[0], "1000.00")
        self.refuse_f("INV-58", bc, "solde", "6000.00")
        self.accepte_f(bc, "solde", "5000.00")
        self.sit(bc, [50, 50])                                                                                   # N = 1000 + (3000 - 1000)
        self.assertEqual(self.nette(bc), 300000)
        self.accepte_f(bc, "solde", "3000.00")
        self.avoir(a, "250.00")                                                                                  # N = 2750
        self.accepte_f(bc, "solde", "3250.00")
        self.refuse_f("INV-58", bc, "solde", "3000.00")

    def test_INV_58_le_solde_suit_le_contractuel_des_devis_rattaches(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        self.accepte_f(bc, "solde", "1000.00")
        self.ajouter_devis(bc, ["250.50"])
        self.refuse_f("INV-58", bc, "solde", "1000.00")
        self.accepte_f(bc, "solde", "1250.50")

    def test_INV_58_le_cache_montant_contractuel_n_est_pas_la_source(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        self.db.execute("UPDATE bons_commande SET montant_contractuel_ht='1.00' WHERE id=?", (bc.b,))
        self.accepte_f(bc, "solde", "1000.00")
        self.refuse_f("INV-58", bc, "solde", "1.00")

    def test_INV_58_solde_a_zero_autorise_par_le_SQL_confirmation_par_le_service(self):
        bc = self.monde()
        self.sit(bc, [100, 100])
        self.assertEqual(self.contractuel(bc) - self.nette(bc), 0)
        self.accepte_f(bc, "solde", "0.00")
        self.refuse_f("INV-58", bc, "solde", "0.01")
        with self.assertRaises(ErreurService):
            self.emettre_solde(bc)
        self.assertEqual(self.un("SELECT count(*) FROM factures WHERE type='solde'")[0], 0)
        so = self.emettre_solde(bc, confirmer_zero=True)
        self.assertEqual(self.un("SELECT total_ht FROM factures WHERE id=?", so)[0], "0.00")
        self.assertEqual(self.tous("SELECT type_ligne, montant_ht FROM facture_lignes WHERE facture_id=? ORDER BY ordre", so),
                         [("prestation", "4000.00"), ("prestation", "2000.00"), ("deduction", "-6000.00")])
        self.assertEqual(self.ck(CK05_SOMME), [])

    def test_INV_52_un_seul_solde_actif_par_BC(self):
        bc = self.monde()
        so = self.solde(bc)
        self.refuse_f("INV-52", bc, "solde", "0.00")
        self.refuse_f("INV-52", bc, "solde", "6000.00")
        self.refuse_f("INV-52", bc, "solde", "-1.00")
        self.assertIsNotNone(so)

    def test_INV_52_un_solde_partiellement_credite_reste_actif(self):
        bc = self.monde()
        so = self.solde(bc)
        self.avoir(so, "5999.99")
        self.assertFalse(self.neutralisee(so))
        self.refuse_f("INV-52", bc, "solde", "5999.99")

    def test_INV_52_un_solde_a_zero_n_est_jamais_neutralise_donc_aucun_second_solde(self):
        bc = self.monde()
        self.sit(bc, [100, 100])
        so = self.emettre_solde(bc, confirmer_zero=True)
        self.assertFalse(self.neutralisee(so))
        self.assertIsNotNone(self.tente_f(bc, "avoir", "0.01", origine_facture_id=so))                           # aucun avoir sur 0.00 (INV-76)
        self.refuse_f("INV-52", bc, "solde", "0.00")

    def test_INV_52_apres_neutralisation_totale_un_nouveau_solde_est_possible(self):
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        a = self.acompte(bc, bc.d[0], "1000.00")
        so = self.solde(bc)
        self.assertEqual(self.total(so), 500000)
        self.neutraliser(so)
        self.assertTrue(self.neutralisee(so))
        self.assertEqual(self.nette(bc), 100000)                                                                 # N = acompte seul
        so2 = self.solde(bc, date_emission="2026-10-06")
        self.assertEqual(self.total(so2), 500000)
        self.refuse_f("INV-52", bc, "solde", "5000.00")
        self.assertEqual(self.ck(CK01_DOUBLONS), [])
        self.assertIsNotNone(a)

    def test_INV_58_apres_un_solde_credite_ni_acompte_ni_situation_ni_devis(self):
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        so = self.solde(bc)
        self.neutraliser(so)
        self.refuse_f("INV-58", bc, "acompte", "100.00", devis_id=bc.d[0])
        self.refuse_f("INV-58", bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        autre = self.brouillon(client_id=bc.cli)
        self.finaliser(autre)
        self.accepter(autre)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-187"):
            self.rattacher(bc.b, autre)

    # --- lignes du solde -------------------------------------------------------------------------------------------------------
    def test_INV_62_un_solde_ne_porte_que_des_lignes_de_prestation_et_de_deduction(self):
        bc = self.monde()
        f = self.facture(bc, "solde", "6000.00")
        for t_ in ("synthese", "avancement", "zzz"):
            with self.subTest(type_ligne=t_):
                extra = dict(bc_ligne_id=bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="1.00") if t_ == "avancement" else {}
                m = self.tente("INSERT INTO facture_lignes (facture_id, ordre, designation, quantite, unite, prix_unitaire_ht, remise_type, type_ligne, montant_ht"
                               + "".join("," + k for k in extra) + ") VALUES (?, 1, 'x', '1', 'ens', '1', 'aucune', ?, '1.00'" + ",?" * len(extra) + ")",
                               f, t_, *extra.values())
                self.assertRegex(m or "", "INV-62")
        self.ligne_f(f, 1, "prestation", "6000.00")
        self.ligne_f(f, 2, "deduction", "-1.00")

    def test_T48_J_composition_du_solde_somme_des_lignes_egale_total(self):
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "total": "5400.00", "acompte": ("montant", "1000.00")}])
        self.acompte(bc, bc.d[0], "1000.00")
        self.sit(bc, [50, 50])
        so = self.solde(bc)
        self.assertEqual(self.un("SELECT total_ht FROM factures WHERE id=?", so)[0], "2700.00")                   # 5400 - (3000 - 600... ) = contractuel - N
        self.assertEqual(self.ck(CK05_SOMME), [])
        self.assertEqual(self.ck(CK04_SANS_LIGNES), [])

    def test_T48_J_le_solde_ne_cree_aucun_avancement_ligne_par_ligne(self):
        bc = self.monde()
        so = self.solde(bc)
        self.assertEqual(self.tous("SELECT count(*) FROM facture_lignes WHERE facture_id=? AND type_ligne='avancement'", so), [(0,)])
        self.assertEqual(self.ck(CK16["manquante"]), [])                                                          # CK-16 ne vise que les situations

    # --- états du BC et caches ------------------------------------------------------------------------------------------------------------
    def test_INV_47_un_solde_exige_un_BC_en_cours(self):
        for etat, inv in (("en_cours", None), ("gele", None), ("termine", "INV-47"), ("annule", "INV-188"), ("annule_gele", "INV-188")):
            with self.subTest(etat=etat):
                bc = self.monde()
                self.etat(bc, etat)
                if inv:
                    self.refuse_f(inv, bc, "solde", "6000.00")
                else:
                    self.accepte_f(bc, "solde", "6000.00")

    def test_T48_J_le_solde_ferme_commercialement_le_BC_et_fixe_date_100_facture(self):
        bc = self.monde()
        s = self.sit(bc, [100, 100])
        self.assertEqual(self.un("SELECT date_100_facture FROM bons_commande WHERE id=?", bc.b)[0], None)
        so = self.emettre_solde(bc, confirmer_zero=True, date_emission="2026-10-08")
        self.recalcul_bc(bc)
        self.assertEqual(self.etat_bc(bc), ("termine", TS, "2026-10-08", "100.00", "6000.00"))
        self.assertEqual(self.ck(CK06_DATE_100) + self.ck(CK06_NETTE) + self.ck(CK06_AVANCEMENT_SOLDE), [])
        self.assertIsNotNone(s)

    def test_T48_J_VR10_date_100_facture_est_la_plus_ancienne_date_de_solde_actif(self):
        bc = self.monde()
        so1 = self.solde(bc, date_emission="2026-10-06")
        self.neutraliser(so1, date_emission="2026-10-07")
        self.recalcul_bc(bc)
        self.assertEqual(self.etat_bc(bc)[:3], ("en_cours", None, None))                                         # solde neutralisé : plus de 100 % facturé
        so2 = self.solde(bc, date_emission="2026-10-09")
        self.recalcul_bc(bc)
        self.assertEqual(self.etat_bc(bc)[:3], ("termine", TS, "2026-10-09"))
        self.assertEqual(self.ck(CK06_DATE_100), [])
        self.assertIsNotNone(so2)

    def test_T48_J_CK06_signale_un_cache_perime(self):
        bc = self.monde()
        self.solde(bc)
        self.assertEqual(self.ck(CK06_NETTE), [(bc.b,)])                                                          # le service n'a pas encore recalculé
        self.assertEqual(self.ck(CK06_DATE_100), [(bc.b,)])
        self.assertEqual(self.ck(CK06_AVANCEMENT_SOLDE), [(bc.b,)])
        self.recalcul_bc(bc)
        self.assertEqual(self.ck(CK06_NETTE) + self.ck(CK06_DATE_100) + self.ck(CK06_AVANCEMENT_SOLDE), [])

    def test_T48_J_apres_neutralisation_totale_du_solde_le_BC_revient_en_cours(self):
        bc = self.monde()
        so = self.solde(bc)
        self.recalcul_bc(bc)
        self.assertEqual(self.etat_bc(bc)[0], "termine")
        self.avoir(so)
        self.recalcul_bc(bc)
        self.assertEqual(self.etat_bc(bc)[:3], ("en_cours", None, None))
        self.assertEqual(self.etat_bc(bc)[4], "0.00")
        self.assertEqual(self.ck(CK06_NETTE) + self.ck(CK06_DATE_100), [])
        self.accepte_f(bc, "solde", "6000.00")                                                                     # un nouveau solde est possible, pas une situation
        self.refuse_f("INV-58", bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")

    def test_T48_J_un_BC_termine_garde_son_solde_et_refuse_tout_sauf_les_avoirs(self):
        bc = self.monde()
        so = self.solde(bc)
        self.recalcul_bc(bc)
        # plusieurs garde-fous s'additionnent (BC terminé, solde existant) : tous refusent, l'ordre de déclenchement n'est pas spécifié
        self.assertIsNotNone(self.tente_f(bc, "solde", "6000.00"))
        self.assertIsNotNone(self.tente_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="6000.00"))
        self.accepte_f(bc, "avoir", "10.00", origine_facture_id=so)


# ====================================================================================================================
# Groupe K — avoirs : origine, plafond, neutralisation dérivée, aucun effet sur le statut du BC
# ====================================================================================================================
class Avoirs(Base9):
    def jeu(self):
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        a = self.acompte(bc, bc.d[0], "1000.00")
        s = self.emettre_situation(bc, {bc.lignes[0]: 5000, bc.lignes[1]: 5000})
        return bc, a, s

    # --- origine ---------------------------------------------------------------------------------------------------
    def test_INV_76_l_origine_n_est_pas_un_avoir(self):
        bc, a, s = self.jeu()
        v = self.avoir(a, "100.00")
        self.refuse_f("INV-76", bc, "avoir", "10.00", origine_facture_id=v)

    def test_INV_76_l_origine_appartient_au_meme_BC(self):
        bc, a, s = self.jeu()
        autre = self.monde(devis=[{"lignes": ["500.00"]}])
        etrangere = self.facture(autre, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.refuse_f("INV-76", bc, "avoir", "10.00", origine_facture_id=etrangere)

    def test_T48_K_origine_inexistante_refusee_par_la_cle_etrangere(self):
        bc, a, s = self.jeu()
        m = self.tente_f(bc, "avoir", "10.00", origine_facture_id=999999)
        self.assertIsNotNone(m)
        self.assertNotIn("INV-76", m)

    def test_T48_K_un_avoir_porte_origine_et_motif_et_aucun_attribut_d_un_autre_type(self):
        bc, a, s = self.jeu()
        self.refuse_check_f(bc, "avoir", "10.00", origine_facture_id=s, devis_id=bc.d[0])
        self.refuse_check_f(bc, "avoir", "10.00", origine_facture_id=s, situation_numero=9, montant_deja_facture_ht="0.00")
        self.refuse_check_f(bc, "avoir", "10.00", origine_facture_id=s, motif_avoir=None)
        self.refuse_check_f(bc, "avoir", "10.00", origine_facture_id=s, motif_avoir="")
        self.refuse_check_f(bc, "avoir", "10.00", origine_facture_id=s, date_echeance="2026-11-04")
        self.refuse_check_f(bc, "situation", "10.00", situation_numero=2, montant_deja_facture_ht=eur(self.nette(bc)), origine_facture_id=s, motif_avoir="x")

    # --- plafond et neutralisation --------------------------------------------------------------------------------------------
    def test_INV_76_la_somme_des_avoirs_ne_depasse_pas_le_total_de_l_origine(self):
        bc, a, s = self.jeu()
        self.accepte_f(bc, "avoir", "1000.00", origine_facture_id=a)
        self.refuse_f("INV-76", bc, "avoir", "1000.01", origine_facture_id=a)
        self.avoir(a, "400.00")
        self.accepte_f(bc, "avoir", "600.00", origine_facture_id=a)
        self.refuse_f("INV-76", bc, "avoir", "600.01", origine_facture_id=a)
        self.avoir(a, "600.00")
        self.refuse_f("INV-76", bc, "avoir", "0.01", origine_facture_id=a)                                      # origine neutralisée : plus rien à créditer

    def test_INV_76_un_avoir_sur_une_origine_a_zero_est_impossible(self):
        bc = self.monde()
        self.facture(bc, "situation", "6000.00", situation_numero=1, montant_deja_facture_ht="0.00")
        so = self.facture(bc, "solde", "0.00")
        self.refuse_f("INV-76", bc, "avoir", "0.01", origine_facture_id=so)

    def test_T48_K_neutralisation_derivee_aux_bornes(self):
        bc, a, s = self.jeu()
        self.assertFalse(self.neutralisee(a))
        self.avoir(a, "999.99")
        self.assertFalse(self.neutralisee(a))
        self.avoir(a, "0.01")
        self.assertTrue(self.neutralisee(a))
        self.assertEqual(self.tous("SELECT count(*) FROM factures WHERE origine_facture_id=?", a), [(2,)])

    def test_T48_K_aucun_avoir_dans_une_facture_d_un_autre_type_de_ligne(self):
        bc, a, s = self.jeu()
        v = self.facture(bc, "avoir", "10.00", origine_facture_id=a)
        for t_, montant in (("deduction", "-1.00"), ("avancement", "1.00"), ("zzz", "1.00")):
            with self.subTest(type_ligne=t_):
                extra = dict(bc_ligne_id=bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="1.00") if t_ == "avancement" else {}
                m = self.tente("INSERT INTO facture_lignes (facture_id, ordre, designation, quantite, unite, prix_unitaire_ht, remise_type, type_ligne, montant_ht"
                               + "".join("," + k for k in extra) + ") VALUES (?, 1, 'x', '1', 'ens', '1', 'aucune', ?, ?" + ",?" * len(extra) + ")",
                               v, t_, montant, *extra.values())
                self.assertRegex(m or "", "INV-62")
        self.ligne_f(v, 1, "synthese", "10.00")

    # --- états du BC -------------------------------------------------------------------------------------------------------------------
    def test_T48_K_un_avoir_accepte_les_lignes_de_prestation_et_de_synthese(self):
        bc, a, s = self.jeu()
        v = self.facture(bc, "avoir", "10.00", origine_facture_id=a)
        self.ligne_f(v, 1, "prestation", "6.00")
        self.ligne_f(v, 2, "synthese", "4.00")
        self.ligne_f(v, 3, "prestation", "0.00")

    def test_T48_K_avoir_possible_sur_BC_termine_et_annule_pas_sur_les_autres_types(self):
        for etat in ("en_cours", "gele", "termine", "annule", "annule_gele"):
            with self.subTest(etat=etat):
                bc = self.monde(devis=[{"lignes": ["100.00"]}])
                s = self.facture(bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00")
                self.etat(bc, etat)
                self.accepte_f(bc, "avoir", "10.00", origine_facture_id=s)

    def test_T48_K_un_avoir_ne_rouvre_jamais_un_BC_termine_ou_annule(self):
        # BC terminé par un solde
        bc = self.monde()
        so = self.solde(bc)
        self.recalcul_bc(bc)
        self.avoir(so, "10.00")
        self.recalcul_bc(bc)
        self.assertEqual(self.etat_bc(bc)[0], "termine")                                                          # partiellement crédité : toujours terminé
        # BC annulé : le recalcul financier ne touche ni statut, ni dates
        bc2 = self.monde(devis=[{"lignes": ["100.00"]}])
        s = self.facture(bc2, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.etat(bc2, "annule")
        avant = self.un("SELECT statut, cancelled_at, completed_at, frozen_at, motif_annulation FROM bons_commande WHERE id=?", bc2.b)
        self.neutraliser(s)
        self.recalcul_bc(bc2)
        self.assertEqual(self.un("SELECT statut, cancelled_at, completed_at, frozen_at, motif_annulation FROM bons_commande WHERE id=?", bc2.b), avant)
        self.assertEqual(self.etat_bc(bc2)[4], "0.00")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE bons_commande SET statut='en_cours', cancelled_at=NULL, motif_annulation=NULL WHERE id=?", (bc2.b,))

    def test_T48_K_un_avoir_n_ecrit_rien_en_dehors_des_tables_de_facturation(self):
        bc, a, s = self.jeu()
        tables = [n for (n,) in self.tous("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
                  if n not in ("factures", "facture_lignes", "numerotation_sequences")]
        avant = {t_: self.tous(f"SELECT * FROM {t_}") for t_ in tables}
        self.avoir(a, "100.00")
        self.assertEqual({t_: self.tous(f"SELECT * FROM {t_}") for t_ in tables}, avant)

    def test_INV_48_un_avoir_porte_le_client_du_BC(self):
        bc, a, s = self.jeu()
        self.refuse_f("INV-48", bc, "avoir", "10.00", origine_facture_id=a, client_id=self.client())

    def test_T48_K_avoir_d_un_solde_ne_rouvre_ni_situation_ni_acompte_ni_devis(self):
        bc, a, s = self.jeu()
        self.neutraliser(a)
        self.neutraliser(s)
        so = self.solde(bc)
        self.neutraliser(so)
        self.assertEqual(self.nette(bc), 0)
        self.refuse_f("INV-58", bc, "acompte", "10.00", devis_id=bc.d[0])
        self.refuse_f("INV-58", bc, "situation", "10.00", situation_numero=9, montant_deja_facture_ht="0.00")

    def test_T48_K_un_avoir_reduit_la_facturation_nette_et_donc_agrandit_le_solde(self):
        bc, a, s = self.jeu()
        n0 = self.nette(bc)
        self.avoir(s, "500.00")
        self.assertEqual(self.nette(bc), n0 - 50000)
        self.accepte_f(bc, "solde", eur(self.contractuel(bc) - n0 + 50000))
        self.refuse_f("INV-58", bc, "solde", eur(self.contractuel(bc) - n0))


# ====================================================================================================================
# Groupe L — devis rattachés et matrice des états du BC
# ====================================================================================================================
class DevisEtats(Base9):
    ETATS = ("en_cours", "gele", "termine", "annule", "annule_gele")
    # état -> (message du refus par type, None = accepté) ; l'avoir reste possible partout
    MATRICE = {"en_cours": {"acompte": None, "situation": None, "solde": None, "avoir": None},
               "gele": {"acompte": None, "situation": None, "solde": None, "avoir": None},
               "termine": {"acompte": "INV-47", "situation": "INV-47", "solde": "INV-47", "avoir": None},
               "annule": {"acompte": "INV-188", "situation": "INV-188", "solde": "INV-188", "avoir": None},
               "annule_gele": {"acompte": "INV-188", "situation": "INV-188", "solde": "INV-188", "avoir": None}}

    def monde_matrice(self):
        """BC dont la seule irrégularité éventuelle est son état : une situation de 100.00 existe (origine des avoirs) ; chaque tentative est conforme par ailleurs."""
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        s = self.facture(bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00")
        return bc, s

    def tentative(self, bc, s, type_):
        n = self.nette(bc)
        if type_ == "acompte":
            return self.tente_f(bc, "acompte", "100.00", devis_id=bc.d[0])
        if type_ == "situation":
            return self.tente_f(bc, "situation", "100.00", situation_numero=2, montant_deja_facture_ht=eur(n))
        if type_ == "solde":
            return self.tente_f(bc, "solde", eur(self.contractuel(bc) - n))
        return self.tente_f(bc, "avoir", "10.00", origine_facture_id=s)

    def test_T48_L_matrice_etat_du_BC_par_type_de_facture(self):
        for etat in self.ETATS:
            for type_ in TYPES:
                with self.subTest(etat=etat, type=type_):
                    bc, s = self.monde_matrice()
                    self.etat(bc, etat)
                    m = self.tentative(bc, s, type_)
                    attendu = self.MATRICE[etat][type_]
                    if attendu is None:
                        self.assertIsNone(m)
                    else:
                        self.assertIsNotNone(m)
                        self.assertRegex(m, attendu)

    def test_T48_L_BC_annule_est_terminal_pour_les_factures_et_un_avoir_ne_le_rouvre_pas(self):
        bc, s = self.monde_matrice()
        self.etat(bc, "annule")
        v = self.avoir(s, "100.00")
        self.assertEqual(self.un("SELECT statut FROM bons_commande WHERE id=?", bc.b)[0], "annule")
        self.assertIsNotNone(v)
        for type_ in ("acompte", "situation", "solde"):
            self.assertRegex(self.tentative(bc, s, type_), "INV-188")

    # --- devis après acomptes / situations / solde -------------------------------------------------------------------------
    def test_T48_L_un_devis_peut_etre_rattache_apres_acomptes_et_situations_jusqu_au_solde(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "100.00")}])
        a = self.acompte(bc, bc.d[0], "100.00")
        s = self.emettre_situation(bc, {bc.lignes[0]: 5000})
        d2, _ = self.ajouter_devis(bc, ["500.00"])
        self.assertEqual(self.contractuel(bc), 150000)
        d3, _ = self.ajouter_devis(bc, ["250.00"])
        self.assertEqual(self.contractuel(bc), 175000)
        self.assertEqual(self.tous("SELECT count(*) FROM bc_devis WHERE bc_id=?", bc.b), [(3,)])
        self.assertEqual(self.ck(CK14_DEVIS_APRES_SOLDE), [])
        self.assertIsNotNone((a, s, d2, d3))

    def test_INV_187_aucun_devis_apres_un_solde_meme_neutralise(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        so = self.solde(bc)
        for neutralise in (False, True):
            with self.subTest(neutralise=neutralise):
                if neutralise:
                    self.neutraliser(so)
                d = self.brouillon(client_id=bc.cli)
                self.finaliser(d)
                self.accepter(d)
                self.db.execute("SAVEPOINT x")
                with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-187"):
                    self.rattacher(bc.b, d)
                self.db.execute("ROLLBACK TO x")
                self.db.execute("RELEASE x")
        self.assertEqual(self.tous("SELECT count(*) FROM bc_devis WHERE bc_id=?", bc.b), [(1,)])

    def test_INV_187_la_regle_ne_vise_que_le_BC_du_solde(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        autre = self.monde(devis=[{"lignes": ["500.00"]}])
        self.solde(bc)
        d2, _ = self.ajouter_devis(autre, ["100.00"])
        self.assertEqual(self.tous("SELECT count(*) FROM bc_devis WHERE bc_id=?", autre.b), [(2,)])
        self.assertIsNotNone(d2)

    def test_INV_187_creation_d_un_BC_n_est_pas_concernee(self):
        """Le trigger agit sur bc_devis seulement quand un solde existe déjà sur le BC visé : un nouveau BC n'en a jamais."""
        bc = self.monde(devis=[{"lignes": ["10.00"]}])
        self.solde(bc)
        autre = self.monde(devis=[{"lignes": ["20.00"]}])
        self.assertEqual(self.contractuel(autre), 2000)

    def test_T48_L_CK14_signale_un_devis_rattache_apres_un_solde_si_le_trigger_est_contourne(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        self.solde(bc, created_at="2030-01-01T00:00:00.000Z")
        d = self.brouillon(client_id=bc.cli)
        self.finaliser(d)
        self.accepter(d)
        self.assertEqual(self.ck(CK14_DEVIS_APRES_SOLDE), [])
        self.db.execute("DROP TRIGGER tr_99_bc_devis_apres_solde")
        self.db.execute("INSERT INTO bc_devis (bc_id, devis_id, rang, created_at) VALUES (?, ?, 2, '2099-01-01T00:00:00.000Z')", (bc.b, d))
        self.assertEqual(self.ck(CK14_DEVIS_APRES_SOLDE), [(d,)])

    def test_T48_L_CK13_et_CK14_de_005b_restent_vides_en_presence_de_factures(self):
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}, {"lignes": ["500.00"]}])
        self.acompte(bc, bc.d[0], "1000.00")
        self.emettre_situation(bc, {bl: 5000 for bl in bc.lignes})
        self.solde(bc)
        for nom, q in list(T.CK13.items()) + list(T.CK14.items()):
            with self.subTest(controle=nom):
                self.assertEqual(self.ck(q), [])


# ====================================================================================================================
# Groupe M — diagnostics CK (lecture seule) : CK-01 à CK-06 (volet 006), CK-13, CK-14, CK-16, CK-17 ; CK-10 non concerné
# ====================================================================================================================
TOUS_CK_006 = {"CK01_DOUBLONS": CK01_DOUBLONS, "CK01_FORMAT_V6": CK01_FORMAT_V6, "CK02_SEQUENCES": CK02_SEQUENCES, "CK04_SANS_LIGNES": CK04_SANS_LIGNES,
               "CK05_SOMME": CK05_SOMME, "CK06_NETTE": CK06_NETTE, "CK06_DATE_100": CK06_DATE_100, "CK06_AVANCEMENT_SOLDE": CK06_AVANCEMENT_SOLDE,
               "CK14_DEVIS_APRES_SOLDE": CK14_DEVIS_APRES_SOLDE, "CK16_MANQUANTE": CK16_MANQUANTE, "CK16_DOUBLON": CK16_DOUBLON,
               "CK16_ETRANGERE": CK16_ETRANGERE, "CK16_HORS_SITUATION": CK16_HORS_SITUATION, "CK17_FORMULE": CK17_FORMULE}


class Diagnostics(Base9):
    def monde_riche(self):
        """Deux devis (remise sur le premier), acompte, trois situations dont une partiellement créditée et une neutralisée, puis un solde et le recalcul du BC."""
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "total": "5400.00", "acompte": ("pourcentage", "10.00")},
                               {"lignes": ["1500.00", "500.00"], "acompte": ("montant", "300.00")}])
        self.emettre_acompte(bc, bc.d[0], "540.00")
        self.emettre_acompte(bc, bc.d[1], "300.00")
        s1 = self.emettre_situation(bc, {bl: p for bl, p in zip(bc.lignes, [3000, 2000, 5000, 0])})
        s2 = self.emettre_situation(bc, {bl: p for bl, p in zip(bc.lignes, [6000, 4000, 7000, 1000])})
        self.avoir(s1, "50.00")
        self.neutraliser(s2)
        self.emettre_situation(bc, {bl: p for bl, p in zip(bc.lignes, [5000, 3000, 6000, 500])})
        self.solde(bc)
        self.recalcul_bc(bc)
        return bc

    def tous_vides(self):
        return {nom: self.ck(q) for nom, q in TOUS_CK_006.items() if self.ck(q)}

    def test_T48_M_un_monde_riche_et_coherent_ne_declenche_aucun_diagnostic(self):
        bc = self.monde_riche()
        self.assertEqual(self.tous_vides(), {})
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])                                       # CK-03
        self.assertEqual(self.tous("PRAGMA integrity_check"), [("ok",)])
        for nom, q in list(T.CK13.items()) + list(T.CK14.items()):
            self.assertEqual(self.ck(q), [], nom)
        self.assertEqual(self.etat_bc(bc)[0], "termine")

    def test_T48_M_les_diagnostics_sont_en_lecture_seule(self):
        self.monde_riche()
        avant = [(n, self.tous(f"SELECT * FROM {n}")) for (n,) in self.tous("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        changes = self.db.total_changes
        for nom, q in TOUS_CK_006.items():
            self.assertRegex(q.lstrip().upper(), r"^(SELECT|WITH)\b", nom)
            self.assertNotRegex(q.upper(), r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|PRAGMA)\b|REPLACE\s+INTO", nom)
            self.ck(q)
        self.assertEqual(self.db.total_changes, changes)
        self.assertEqual([(n, self.tous(f"SELECT * FROM {n}")) for (n,) in self.tous("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")], avant)

    # --- CK-01 -------------------------------------------------------------------------------------------------------------------
    def donnees_corrompues(self, bc, **cols):
        """Insère une facture qui viole un CHECK (ignore_check_constraints=ON le temps de l'insertion) : seul un import défectueux ou une corruption la produit."""
        self.db.execute("PRAGMA ignore_check_constraints=ON")
        try:
            return self.facture(bc, cols.pop("type_", "situation"), cols.pop("total", "10.00"), **cols)
        finally:
            self.db.execute("PRAGMA ignore_check_constraints=OFF")

    def test_T48_M_CK01_format_V6_signale_prefixe_et_annee_incorrects_mais_pas_l_import(self):
        bc = self.monde()
        base = dict(situation_numero=None, montant_deja_facture_ht="0.00")
        ok = self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        mauvais_prefixe = self.donnees_corrompues(bc, situation_numero=2, montant_deja_facture_ht="10.00", numero="ACP-00009-26")
        mauvaise_annee = self.donnees_corrompues(bc, situation_numero=3, montant_deja_facture_ht="20.00", numero="FAC-00010-27")
        mal_forme = self.donnees_corrompues(bc, situation_numero=4, montant_deja_facture_ht="30.00", numero="FAC-1-26")
        importee = self.facture(bc, "situation", "10.00", situation_numero=5, montant_deja_facture_ht="40.00", origine="import", numero="Facture 12/2019",
                                legacy_id="12", legacy_data="{}")
        self.assertEqual(sorted(self.ck(CK01_FORMAT_V6)), sorted([(mauvais_prefixe,), (mauvaise_annee,), (mal_forme,)]))
        self.assertNotIn((ok,), self.ck(CK01_FORMAT_V6))
        self.assertNotIn((importee,), self.ck(CK01_FORMAT_V6))
        self.assertIsNotNone(base)

    def test_T48_M_CK01_doublons_requete_sur_table_sans_unicite(self):
        """UNIQUE(numero) interdit tout doublon dans factures ; la requête de CK-01 est vérifiée sur une table témoin sans contrainte."""
        self.db.execute("CREATE TEMP TABLE temoin (numero TEXT)")
        self.db.executemany("INSERT INTO temoin VALUES (?)", [("FAC-00001-26",), ("FAC-00001-26",), ("ACP-00001-26",)])
        self.assertEqual(self.tous(CK01_DOUBLONS.replace("FROM factures", "FROM temoin")), [("FAC-00001-26",)])

    def test_T48_M_CK01_ne_confond_pas_les_familles_de_numeros(self):
        bc = self.monde(devis=[{"lignes": ["100.00"], "acompte": ("montant", "10.00")}])
        a = self.acompte(bc, bc.d[0], "10.00")
        self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="10.00")
        self.avoir(a, "5.00")
        self.assertEqual(self.ck(CK01_DOUBLONS), [])                                                            # ACP-00001, FAC-00001, AVO-00001 : trois familles
        self.assertEqual(self.tous("SELECT numero FROM factures ORDER BY id"), [("ACP-00001-26",), ("FAC-00001-26",), ("AVO-00001-26",)])

    # --- CK-03 -----------------------------------------------------------------------------------------------------------------------
    def test_T48_M_CK03_foreign_key_check_detecte_une_facture_orpheline(self):
        t = self.sans_triggers()                                                                              # sans garde-fou ni clés étrangères : simulation d'une base corrompue
        bc = t.monde()
        t.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.assertEqual(t.tous("PRAGMA foreign_key_check"), [])
        t.db.execute("PRAGMA foreign_keys=OFF")
        t.facture(bc, "situation", "10.00", situation_numero=2, montant_deja_facture_ht="10.00", bc_id=424242)
        t.db.execute("PRAGMA foreign_keys=ON")
        controle = t.tous("PRAGMA foreign_key_check")
        self.assertEqual([x[0] for x in controle], ["factures"])
        self.assertEqual(controle[0][2], "bons_commande")

    # --- CK-04 / CK-05 ---------------------------------------------------------------------------------------------------------------
    def test_T48_M_CK04_CK05_pour_chaque_type_de_facture(self):
        bc = self.monde_riche()
        self.assertEqual(self.ck(CK04_SANS_LIGNES) + self.ck(CK05_SOMME), [])
        fantome = self.facture(bc, "avoir", "5.00", origine_facture_id=self.un("SELECT id FROM factures WHERE type='acompte' LIMIT 1")[0])
        self.assertEqual(self.ck(CK04_SANS_LIGNES), [(fantome,)])
        self.assertEqual(self.ck(CK05_SOMME), [(fantome,)])
        self.ligne_f(fantome, 1, "synthese", "5.01")
        self.assertEqual(self.ck(CK04_SANS_LIGNES), [])
        self.assertEqual(self.ck(CK05_SOMME), [(fantome,)])

    def test_T48_M_CK05_somme_des_lignes_negatives_comprises(self):
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "total": "5400.00"}])
        so = self.facture(bc, "solde", "5400.00")
        self.ligne_f(so, 1, "prestation", "4000.00", bc.lignes[0])
        self.ligne_f(so, 2, "prestation", "2000.00", bc.lignes[1])
        self.assertEqual(self.ck(CK05_SOMME), [(so,)])
        self.ligne_f(so, 3, "deduction", "-600.00")
        self.assertEqual(self.ck(CK05_SOMME), [])
        self.ligne_f(so, 4, "deduction", "-0.01")
        self.assertEqual(self.ck(CK05_SOMME), [(so,)])

    # --- CK-06 (volet 006) -------------------------------------------------------------------------------------------------------------
    def test_T48_M_CK06_cache_nette_compte_acomptes_situations_soldes_moins_avoirs(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "100.00")}])
        a = self.acompte(bc, bc.d[0], "100.00")
        self.recalcul_bc(bc)
        self.assertEqual(self.ck(CK06_NETTE), [])
        self.avoir(a, "40.00")
        self.assertEqual(self.ck(CK06_NETTE), [(bc.b,)])
        self.recalcul_bc(bc)
        self.assertEqual(self.ck(CK06_NETTE), [])
        self.assertEqual(self.etat_bc(bc)[4], "60.00")

    def test_T48_M_CK06_BC_annule_ses_caches_suivent_aussi_les_avoirs(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        s = self.facture(bc, "situation", "1000.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.recalcul_bc(bc)
        self.etat(bc, "annule")
        self.assertEqual(self.ck(CK06_NETTE), [])
        self.avoir(s, "250.00")
        self.assertEqual(self.ck(CK06_NETTE), [(bc.b,)])
        self.recalcul_bc(bc)
        self.assertEqual(self.ck(CK06_NETTE), [])
        self.assertEqual(self.etat_bc(bc)[0], "annule")

    def test_T48_M_CK06_date_100_ignore_un_solde_neutralise_et_prend_le_plus_ancien_actif(self):
        bc = self.monde()
        so = self.solde(bc, date_emission="2026-10-06")
        self.neutraliser(so, date_emission="2026-10-06")
        self.assertEqual(self.ck(CK06_DATE_100), [])                                                            # aucun solde actif et cache NULL
        so2 = self.solde(bc, date_emission="2026-10-07")
        self.assertEqual(self.ck(CK06_DATE_100), [(bc.b,)])
        self.recalcul_bc(bc)
        self.assertEqual(self.ck(CK06_DATE_100), [])
        self.assertEqual(self.etat_bc(bc)[2], "2026-10-07")
        self.assertIsNotNone(so2)

    # --- CK-16 / CK-17 --------------------------------------------------------------------------------------------------------------------
    def test_T48_M_CK16_ligne_etrangere_et_avancement_hors_situation_si_les_triggers_sont_contournes(self):
        t = self.sans_triggers()
        bc = t.monde()
        autre = t.monde()
        s = t.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        etrangere = t.ligne_f(s, 1, "avancement", "1.00", autre.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="1.00")
        a = t.facture(bc, "acompte", "10.00", devis_id=bc.d[0])
        hors = t.ligne_f(a, 1, "avancement", "1.00", bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="1.00")
        self.assertEqual(t.ck(CK16_ETRANGERE), [(etrangere,)])
        self.assertEqual(t.ck(CK16_HORS_SITUATION), [(hors,)])
        self.assertEqual(t.ck(CK16_DOUBLON), [])

    def test_T48_M_CK16_doublon_si_l_index_unique_est_retire(self):
        bc = self.monde()
        s = self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.ligne_f(s, 1, "avancement", "1.00", bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="1.00")
        self.db.execute("DROP INDEX uq_facture_lignes_avancement")
        self.ligne_f(s, 2, "avancement", "1.00", bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="1.00")
        self.assertEqual(self.ck(CK16_DOUBLON), [(s, bc.lignes[0])])

    def test_T48_M_CK16_exhaustivite_se_mesure_a_la_creation_des_lignes_de_BC(self):
        bc = self.monde()
        s = self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.assertEqual(sorted(self.ck(CK16_MANQUANTE)), sorted([(s, bc.lignes[0]), (s, bc.lignes[1])]))
        self.ligne_f(s, 1, "avancement", "1.00", bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="1.00")
        self.assertEqual(self.ck(CK16_MANQUANTE), [(s, bc.lignes[1])])
        self.ajouter_devis(bc, ["100.00"], apres=True)                                                           # ligne créée après l'émission : non applicable
        self.assertEqual(self.ck(CK16_MANQUANTE), [(s, bc.lignes[1])])

    def test_T48_M_CK17_limite_connue_au_dela_de_21_millions_d_euros_par_devis(self):
        """CK-17 calcule en entiers : 2·R·G + B dépasse int64 quand B dépasse 2,147·10^9 centimes (≈ 21,4 M€) avec une remise égale à la totalité de B ;
        SQLite bascule alors en nombre réel, sans erreur (limite documentée, hors usage Essentiel : devis de travaux)."""
        self.assertEqual(self.un("SELECT typeof(2 * 2000000000 * 2000000000)")[0], "integer")
        self.assertEqual(self.un("SELECT typeof(2 * 2200000000 * 2200000000)")[0], "real")
        self.assertLess(2 * 2000000000 ** 2, 2 ** 63)
        self.assertGreater(2 * 2200000000 ** 2, 2 ** 63 - 1)


# ====================================================================================================================
# Groupe N — import (le SQL ignore V2 ; les données importées respectent les invariants V6, sinon a_verifier / non_importe, D-22)
# ====================================================================================================================
class Import(Base9):
    def imp(self, bc, type_, total, numero, **kw):
        return self.facture(bc, type_, total, origine="import", numero=numero, legacy_id=kw.pop("legacy_id", numero), legacy_data=kw.pop("legacy_data", '{"v2":true}'), **kw)

    def test_T48_N_numero_importe_libre_non_vide_unique_et_immuable(self):
        bc = self.monde()
        for numero in ("2019-0042", "F/2019/12", "Facture n°7 (copie)", "FAC-00001-26", "x"):
            with self.subTest(numero=numero):
                self.accepte_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", origine="import", numero=numero, legacy_id="1", legacy_data="{}")
        self.refuse_check_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", origine="import", numero="", legacy_id="1", legacy_data="{}")
        self.refuse_check_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", origine="import", numero=None, legacy_id="1", legacy_data="{}")
        f = self.imp(bc, "situation", "10.00", "OLD-1", situation_numero=1, montant_deja_facture_ht="0.00")
        self.refuse_check_f(bc, "situation", "10.00", situation_numero=2, montant_deja_facture_ht="10.00", origine="import", numero="OLD-1", legacy_id="2", legacy_data="{}")
        self.assertRegex(self.tente("UPDATE factures SET numero='OLD-2' WHERE id=?", f) or "", "INV-53")

    def test_T48_N_donnees_d_origine_json_valide_et_interdites_pour_v6(self):
        bc = self.monde()
        self.refuse_check_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", origine="import", numero="OLD-1", legacy_id="1", legacy_data="{pas json")
        self.accepte_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", origine="import", numero="OLD-1", legacy_id=None, legacy_data=None)
        self.refuse_check_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", legacy_id="1")
        self.refuse_check_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", legacy_data="{}")

    def test_T48_N_pas_de_legacy_numero_ni_de_colonne_V2_dans_les_tables_de_facturation(self):
        for table, colonnes in (("factures", COLONNES_FACTURES), ("facture_lignes", COLONNES_LIGNES)):
            self.assertEqual([x[1] for x in self.tous(f"PRAGMA table_info({table})")], colonnes)
        self.assertNotIn("legacy_numero", COLONNES_FACTURES)

    def test_T48_N_une_facture_importee_respecte_les_invariants_V6_sinon_a_verifier(self):
        """Chaque invariant transactionnel s'applique aux lignes importées : une facture qui les viole est refusée (le convertisseur la classe a_verifier / non_importe)."""
        bc = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "100.00")}])
        autre = self.monde(devis=[{"lignes": ["10.00"]}])
        kw = dict(origine="import", legacy_id="1", legacy_data="{}")
        self.refuse_f("INV-57", bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="5.00", numero="O1", **kw)            # montant_deja faux
        self.refuse_f("INV-57", bc, "situation", "1000.01", situation_numero=1, montant_deja_facture_ht="0.00", numero="O2", **kw)          # au-delà du contractuel
        self.refuse_f("INV-189", bc, "acompte", "10.00", devis_id=autre.d[0], numero="O3", **kw)                                           # devis d'un autre BC
        self.refuse_f("INV-58", bc, "solde", "999.00", numero="O4", **kw)                                                                    # solde ≠ contractuel − nette
        self.refuse_f("INV-48", bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", numero="O5", client_id=self.client(), **kw)
        a = self.imp(bc, "acompte", "100.00", "O6", devis_id=bc.d[0])
        self.refuse_f("INV-52", bc, "acompte", "10.00", devis_id=bc.d[0], numero="O7", **kw)                                                # second acompte actif
        self.refuse_f("INV-76", bc, "avoir", "100.01", origine_facture_id=a, numero="O8", **kw)                                             # avoir > origine

    def test_T48_N_apres_un_solde_importe_plus_rien_ne_s_ajoute(self):
        bc = self.monde(devis=[{"lignes": ["500.00"]}])
        self.imp(bc, "solde", "500.00", "S-1")
        kw = dict(origine="import", legacy_id="1", legacy_data="{}")
        self.refuse_f("INV-58", bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="500.00", numero="O1", **kw)
        self.refuse_f("INV-58", bc, "acompte", "10.00", devis_id=bc.d[0], numero="O2", **kw)

    def test_T48_N_ordre_d_import_par_date_emission_TR02_actif_si_la_sequence_existe(self):
        bc = self.monde(devis=[{"lignes": ["5000.00"]}])
        self.un(ATTRIBUER, "FAC", 19)
        self.db.execute("UPDATE numerotation_sequences SET derniere_date='2019-06-30' WHERE type_objet='FAC' AND annee=19")
        kw = dict(origine="import", legacy_id="1", legacy_data="{}")
        self.refuse_f("INV-24", bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", numero="OLD-1", date_emission="2019-05-01",
                      date_echeance="2019-06-01", **kw)
        self.accepte_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", numero="OLD-1", date_emission="2019-07-01", date_echeance="2019-08-01", **kw)

    def test_T48_N_historique_importe_complet_acompte_situation_avoir_solde(self):
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        a = self.imp(bc, "acompte", "1000.00", "A-2019-1", devis_id=bc.d[0], date_emission="2019-03-01", date_echeance="2019-03-31")
        self.ligne_f(a, 1, "synthese", "1000.00")
        s = self.imp(bc, "situation", "2000.00", "S-2019-2", situation_numero=1, montant_deja_facture_ht="1000.00", date_emission="2019-04-01", date_echeance="2019-05-01")
        self.ligne_f(s, 1, "avancement", "2500.00", bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="62.50")
        self.ligne_f(s, 2, "avancement", "500.00", bc.lignes[1], avancement_precedent_pct="0.00", avancement_cumule_pct="25.00")
        self.ligne_f(s, 3, "deduction", "-1000.00")
        v = self.imp(bc, "avoir", "50.00", "AV-2019-1", origine_facture_id=s, date_emission="2019-04-10", motif_avoir="Remise commerciale")
        self.ligne_f(v, 1, "synthese", "50.00")
        so = self.imp(bc, "solde", "3050.00", "S-2019-9", date_emission="2019-06-01", date_echeance="2019-07-01")
        self.ligne_f(so, 1, "prestation", "4000.00", bc.lignes[0])
        self.ligne_f(so, 2, "prestation", "2000.00", bc.lignes[1])
        self.ligne_f(so, 3, "deduction", "-2950.00")
        self.assertEqual(self.ck(CK01_DOUBLONS) + self.ck(CK01_FORMAT_V6) + self.ck(CK02_SEQUENCES) + self.ck(CK04_SANS_LIGNES) + self.ck(CK05_SOMME)
                         + self.ck(CK17_FORMULE), [])

    def test_T48_N_CK17_et_CK16_classent_une_situation_importee_qui_ne_suit_pas_la_formule_V6(self):
        """Montants V2 différents de la formule V6 : le SQL les accepte tant qu'ils respectent les invariants transactionnels ; CK-16/CK-17 les signalent (a_verifier)."""
        bc = self.monde()
        s = self.imp(bc, "situation", "3333.33", "V2-1", situation_numero=1, montant_deja_facture_ht="0.00")
        self.ligne_f(s, 1, "avancement", "2500.00", bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="62.50")
        self.ligne_f(s, 2, "avancement", "833.33", bc.lignes[1], avancement_precedent_pct="0.00", avancement_cumule_pct="41.67")
        self.assertEqual(self.ck(CK05_SOMME), [])
        self.assertEqual(self.ck(CK17_FORMULE), [(s,)])

    def test_T48_N_ordinal_importe_d_une_situation_preserve_et_non_reutilise(self):
        bc = self.monde(devis=[{"lignes": ["5000.00"]}])
        self.imp(bc, "situation", "10.00", "O-3", situation_numero=3, montant_deja_facture_ht="0.00")
        self.imp(bc, "situation", "10.00", "O-1", situation_numero=1, montant_deja_facture_ht="10.00")
        self.assertEqual(self.tous("SELECT situation_numero FROM factures ORDER BY situation_numero"), [(1,), (3,)])
        self.refuse_check_f(bc, "situation", "10.00", situation_numero=3, montant_deja_facture_ht="20.00", origine="import", numero="O-3b", legacy_id="1", legacy_data="{}")
        self.assertEqual(self.un("SELECT COALESCE(MAX(situation_numero),0)+1 FROM factures WHERE bc_id=?", bc.b)[0], 4)


# ====================================================================================================================
# Groupe O — sauvegarde, restauration, VACUUM INTO ; Groupe P — non-régression des objets du rang 8
# ====================================================================================================================
class Sauvegarde(Base9):
    def monde_sauve(self):
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        self.acompte(bc, bc.d[0], "1000.00")
        self.emettre_situation(bc, {bc.lignes[0]: 5000, bc.lignes[1]: 5000})
        self.recalcul_bc(bc)
        return bc

    def objets(self, db):
        return sorted(db.execute("SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall())

    def copie(self, via):
        cible = sqlite3.connect(":memory:")
        if via == "backup":
            self.db.backup(cible)
        else:
            import os
            import tempfile
            with tempfile.TemporaryDirectory() as dossier:
                chemin = os.path.join(dossier, "copie.db")
                self.db.execute("VACUUM INTO ?", (chemin,))
                src = sqlite3.connect(chemin)
                src.backup(cible)
                src.close()
        cible.execute("PRAGMA foreign_keys=ON")
        cible.execute("PRAGMA recursive_triggers=ON")
        return cible

    def test_T48_O_restauration_schema_donnees_et_garde_fous_identiques(self):
        self.monde_sauve()
        for via in ("backup", "vacuum_into"):
            with self.subTest(via=via):
                r_ = self.copie(via)
                self.assertEqual(self.objets(r_), self.objets(self.db))
                self.assertEqual(r_.execute("PRAGMA user_version").fetchone()[0], RANG)
                self.assertEqual(r_.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
                self.assertEqual(r_.execute("PRAGMA foreign_key_check").fetchall(), [])
                for t_ in ("factures", "facture_lignes", "numerotation_sequences"):
                    self.assertEqual(r_.execute(f"SELECT * FROM {t_} ORDER BY id").fetchall(), self.db.execute(f"SELECT * FROM {t_} ORDER BY id").fetchall())
                for nom, q in TOUS_CK_006.items():
                    self.assertEqual(r_.execute(q).fetchall(), [], nom)
                with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-53"):
                    r_.execute("UPDATE factures SET total_ht='1.00'")
                with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-06"):
                    r_.execute("DELETE FROM factures")
                r_.close()

    def test_T48_O_apres_restauration_la_numerotation_et_l_ordinal_continuent(self):
        bc = self.monde_sauve()
        r_ = self.copie("backup")
        t = Base9()
        t.db, t._n = r_, 0
        n = t.un(ATTRIBUER, "FAC", 26)[0]
        self.assertEqual(n, 2)
        self.assertEqual(t.un("SELECT COALESCE(MAX(situation_numero),0)+1 FROM factures WHERE bc_id=?", bc.b)[0], 2)
        s2 = t.emettre_situation(bc, {bc.lignes[0]: 6000, bc.lignes[1]: 6000})
        self.assertEqual(t.un("SELECT numero, situation_numero FROM factures WHERE id=?", s2), ("FAC-00003-26", 2))
        r_.close()

    def test_T48_O_CK02_signale_une_sequence_perdue_a_la_restauration(self):
        self.monde_sauve()
        r_ = self.copie("backup")
        t = Base9()
        t.db, t._n = r_, 0
        r_.execute("PRAGMA recursive_triggers=OFF")
        for (nom,) in r_.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='numerotation_sequences'").fetchall():
            r_.execute(f"DROP TRIGGER {nom}")
        r_.execute("DELETE FROM numerotation_sequences WHERE type_objet IN ('ACP','FAC')")
        self.assertEqual(len(t.ck(CK02_SEQUENCES)), 2)
        r_.close()

    def test_T48_O_la_restauration_d_une_base_plus_ancienne_est_la_limite_acceptee(self):
        """Une sauvegarde antérieure à une émission restaure un compteur plus bas : la détection (high-water) relève de machine.db, pas de la base métier."""
        bc = self.monde_sauve()
        ancienne = self.copie("backup")
        self.emettre_situation(bc, {bc.lignes[0]: 6000, bc.lignes[1]: 6000})
        self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='FAC'")[0], 2)
        self.assertEqual(ancienne.execute("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet='FAC'").fetchone()[0], 1)
        self.assertEqual(ancienne.execute("SELECT count(*) FROM factures WHERE type='situation'").fetchone()[0], 1)
        ancienne.close()


class NonRegression(Base9):
    """Les comportements des tranches 001 à 005c, sur la base du rang 9."""

    def test_T48_P_numerotation_TR95_TR96_s_applique_aux_prefixes_de_facturation(self):
        for pre in ("ACP", "FAC", "AVO"):
            self.un(ATTRIBUER, pre, 26)
            self.un(ATTRIBUER, pre, 26)
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute("UPDATE numerotation_sequences SET dernier_numero=1 WHERE type_objet=? AND annee=26", (pre,))
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute("DELETE FROM numerotation_sequences WHERE type_objet=?", (pre,))
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute("INSERT OR REPLACE INTO numerotation_sequences (type_objet, annee, dernier_numero) VALUES (?, 26, 1)", (pre,))
            self.assertEqual(self.un("SELECT dernier_numero FROM numerotation_sequences WHERE type_objet=? AND annee=26", pre)[0], 2)

    def test_T48_P_les_caches_financiers_du_BC_restent_modifiables_par_le_service_apres_facturation(self):
        bc = self.monde()
        self.facture(bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.db.execute("UPDATE bons_commande SET montant_deja_facture_ht='100.00', avancement='2.00', updated_at=? WHERE id=?", (TS2, bc.b))
        self.assertEqual(self.etat_bc(bc)[3:], ("2.00", "100.00"))

    def test_T48_P_un_BC_ne_se_supprime_pas_et_un_devis_accepte_reste_fige(self):
        bc = self.monde()
        self.facture(bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.assertRegex(self.tente("DELETE FROM bons_commande WHERE id=?", bc.b) or "", "INV-174")
        self.assertRegex(self.tente("UPDATE devis SET total_ht='1.00' WHERE id=?", bc.d[0]) or "", "INV-181")

    def test_T48_P_les_objets_de_006_sont_les_seuls_ajouts(self):
        r8 = C.migrer8()
        avant = {(t_, n) for t_, n in r8.execute("SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
        apres = {(t_, n) for t_, n in self.db.execute("SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
        self.assertEqual(avant - apres, set())
        self.assertEqual({n for _, n in apres - avant} - set(INDEXES_006) - set(TRIGGERS_006), {"factures", "facture_lignes"})
        r8.close()


# ====================================================================================================================
# Groupe Q — triggers gardiens (aucune écriture), atomicité des émissions, insertions multi-lignes
# ====================================================================================================================
class Gardiens(Base9):
    def test_T48_Q_une_insertion_acceptee_n_ecrit_qu_une_ligne(self):
        """total_changes inclut les écritures faites par les triggers : une facture acceptée = exactement 1 changement (aucun trigger n'écrit)."""
        bc = self.monde(devis=[{"lignes": ["4000.00", "2000.00"], "acompte": ("montant", "1000.00")}])
        a = None
        for type_ in TYPES:
            if type_ == "acompte":
                cols = self.cols_facture(bc, "acompte", "100.00", devis_id=bc.d[0], numero="ACP-00001-26")
            elif type_ == "situation":
                cols = self.cols_facture(bc, "situation", "50.00", situation_numero=1, montant_deja_facture_ht="100.00", numero="FAC-00001-26")
            elif type_ == "avoir":
                cols = self.cols_facture(bc, "avoir", "10.00", origine_facture_id=a, numero="AVO-00001-26")
            else:
                cols = self.cols_facture(bc, "solde", eur(self.contractuel(bc) - self.nette(bc)), numero="FAC-00002-26")
            avant = self.db.total_changes
            i = self.inserer("factures", cols)
            self.assertEqual(self.db.total_changes - avant, 1, type_)
            a = i if type_ == "acompte" else a
        self.assertEqual(self.un("SELECT count(*) FROM factures")[0], 4)

    def test_T48_Q_une_ligne_acceptee_n_ecrit_qu_une_ligne(self):
        bc = self.monde()
        s = self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        avant = self.db.total_changes
        self.ligne_f(s, 1, "avancement", "1.00", bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="1.00")
        self.assertEqual(self.db.total_changes - avant, 1)

    def test_T48_Q_un_refus_laisse_le_total_de_changements_inchange(self):
        bc = self.monde(devis=[{"lignes": ["100.00"]}])
        avant = self.db.total_changes
        self.assertIsNotNone(self.tente_f(bc, "situation", "100.01", situation_numero=1, montant_deja_facture_ht="0.00", numero="FAC-00001-26"))
        self.assertEqual(self.db.total_changes, avant)

    # --- atomicité de l'émission ----------------------------------------------------------------------------------------------
    def emission_defectueuse(self, bc):
        """Émission d'une situation dont la 2e ligne viole INV-190 (précédent faux)."""
        f = self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.ligne_f(f, 1, "avancement", "1.00", bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="1.00")
        self.ligne_f(f, 2, "avancement", "1.00", bc.lignes[1], avancement_precedent_pct="5.00", avancement_cumule_pct="6.00")

    def test_T48_Q_une_emission_defectueuse_annulee_ne_laisse_ni_facture_ni_ligne_ni_numero(self):
        bc = self.monde()
        photo = [self.tous(f"SELECT * FROM {t_}") for t_ in ("factures", "facture_lignes", "numerotation_sequences")]
        self.db.execute("SAVEPOINT emission")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-190"):
            self.emission_defectueuse(bc)
        self.db.execute("ROLLBACK TO emission")
        self.db.execute("RELEASE emission")
        self.assertEqual([self.tous(f"SELECT * FROM {t_}") for t_ in ("factures", "facture_lignes", "numerotation_sequences")], photo)

    def test_T48_Q_sans_transaction_l_emission_defectueuse_laisse_une_facture_sans_lignes_signalee_par_CK04(self):
        """Pourquoi le service enveloppe l'émission dans UNE transaction : le schéma ne peut pas imposer l'exhaustivité (CK-04, CK-05, CK-16 la détectent)."""
        bc = self.monde()
        with self.assertRaises(sqlite3.IntegrityError):
            self.emission_defectueuse(bc)
        self.assertEqual(self.un("SELECT count(*) FROM factures")[0], 1)
        self.assertEqual(self.ck(CK05_SOMME), self.tous("SELECT id FROM factures"))
        self.assertEqual(len(self.ck(CK16_MANQUANTE)), 1)

    def test_T48_Q_dans_une_meme_transaction_les_gardes_voient_les_ecritures_precedentes(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "100.00")}])
        self.db.execute("SAVEPOINT t")
        self.acompte(bc, bc.d[0], "100.00")
        self.refuse_f("INV-57", bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.accepte_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="100.00")
        self.db.execute("RELEASE t")

    # --- insertions de plusieurs lignes en une instruction -----------------------------------------------------------------------
    def test_T48_Q_insertion_multiple_les_gardes_s_appliquent_ligne_a_ligne(self):
        bc = self.monde()
        cols = ",".join(self.cols_facture(bc, "situation", "4000.00", situation_numero=1, montant_deja_facture_ht="0.00"))
        c1 = self.cols_facture(bc, "situation", "4000.00", situation_numero=1, montant_deja_facture_ht="0.00", numero="FAC-00001-26")
        c2 = self.cols_facture(bc, "situation", "4000.00", situation_numero=2, montant_deja_facture_ht="0.00", numero="FAC-00002-26")
        sql = f"INSERT INTO factures ({','.join(c1)}) VALUES ({','.join('?' * len(c1))}), ({','.join('?' * len(c2))})"
        avant = self.photo_f()
        m = self.tente(sql, *c1.values(), *c2.values())
        self.assertRegex(m or "", "INV-57")                                                                    # la 2e voit la 1re : montant_deja devrait valoir 4000.00
        self.assertEqual(self.photo_f(), avant)                                                                # l'instruction est atomique : rien n'est resté
        self.assertIsNotNone(cols)

    def photo_f(self):
        return self.tous("SELECT * FROM factures")

    def test_T48_Q_deux_acomptes_du_meme_devis_en_une_instruction_refuses(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "100.00")}])
        c1 = self.cols_facture(bc, "acompte", "10.00", devis_id=bc.d[0], numero="ACP-00001-26")
        c2 = self.cols_facture(bc, "acompte", "10.00", devis_id=bc.d[0], numero="ACP-00002-26")
        sql = f"INSERT INTO factures ({','.join(c1)}) VALUES ({','.join('?' * len(c1))}), ({','.join('?' * len(c2))})"
        avant = self.photo_f()
        self.assertRegex(self.tente(sql, *c1.values(), *c2.values()) or "", "INV-52")
        self.assertEqual(self.photo_f(), avant)

    def test_T48_Q_deux_lignes_d_avancement_de_la_meme_ligne_de_BC_en_une_instruction_refusees(self):
        bc = self.monde()
        s = self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        base = dict(facture_id=s, bc_ligne_id=bc.lignes[0], designation="x", quantite="1", unite="ens", prix_unitaire_ht="1", remise_type="aucune",
                    type_ligne="avancement", montant_ht="1.00", avancement_precedent_pct="0.00", avancement_cumule_pct="1.00")
        noms = ",".join(["ordre"] + list(base))
        marque = "(" + ",".join("?" * (len(base) + 1)) + ")"
        avant = self.tous("SELECT * FROM facture_lignes")
        m = self.tente(f"INSERT INTO facture_lignes ({noms}) VALUES {marque}, {marque}", 1, *base.values(), 2, *base.values())
        self.assertIsNotNone(m)
        self.assertEqual(self.tous("SELECT * FROM facture_lignes"), avant)

    def test_T48_Q_INSERT_SELECT_de_lignes_dont_une_viole_INV_190_n_en_laisse_aucune(self):
        bc = self.monde()
        s = self.facture(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        avant = self.tous("SELECT * FROM facture_lignes")
        m = self.tente("INSERT INTO facture_lignes (facture_id, ordre, bc_ligne_id, designation, quantite, unite, prix_unitaire_ht, remise_type, type_ligne, montant_ht, "
                       "avancement_precedent_pct, avancement_cumule_pct) "
                       "SELECT ?, bl.ordre, bl.id, 'x', '1', 'ens', '1', 'aucune', 'avancement', '1.00', CASE WHEN bl.ordre = 2 THEN '9.00' ELSE '0.00' END, '10.00' "
                       "FROM bc_lignes bl WHERE bl.bc_id = ? ORDER BY bl.ordre", s, bc.b)
        self.assertRegex(m or "", "INV-190")
        self.assertEqual(self.tous("SELECT * FROM facture_lignes"), avant)


# ====================================================================================================================
# Groupe R — cas limites : 1 centime, BC vide, BC sans devis, chronologie par préfixe et par année, référence ρ et lignes de déduction
# ====================================================================================================================
class CasLimites(Base9):
    def sit(self, bc, numero, total="10.00", **kw):
        return self.facture(bc, "situation", total, situation_numero=numero, montant_deja_facture_ht=kw.pop("deja", eur(self.nette(bc))), **kw)

    def tente_av(self, f, ordre, bl, prec, cum):
        self.db.execute("SAVEPOINT r")
        try:
            self.ligne_f(f, ordre, "avancement", "0.00", bl, avancement_precedent_pct=prec, avancement_cumule_pct=cum)
            return None
        except sqlite3.IntegrityError as e:
            return str(e)
        finally:
            self.db.execute("ROLLBACK TO r")
            self.db.execute("RELEASE r")

    # --- acompte : plafonds exacts sur un BC vide ---------------------------------------------------------------------------
    def test_T48_R_acompte_egal_au_contractuel_entier_d_un_BC_vide_accepte(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "1000.00")}])
        self.accepte_f(bc, "acompte", "1000.00", devis_id=bc.d[0])
        self.refuse_f("INV-57", bc, "acompte", "1000.01", devis_id=bc.d[0])

    def test_T48_R_acompte_d_un_centime_et_neutralisation_au_centime_pres(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "1.00")}])
        self.accepte_f(bc, "acompte", "0.01", devis_id=bc.d[0])
        a = self.acompte(bc, bc.d[0], "0.02")
        self.avoir(a, "0.01")
        self.assertFalse(self.neutralisee(a))
        self.refuse_f("INV-52", bc, "acompte", "0.01", devis_id=bc.d[0])                                   # il manque un centime pour neutraliser
        self.avoir(a, "0.01")
        self.assertTrue(self.neutralisee(a))
        self.accepte_f(bc, "acompte", "0.01", devis_id=bc.d[0])

    def test_T48_R_acompte_d_un_centime_neutralise_par_un_avoir_d_un_centime(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "1.00")}])
        a = self.acompte(bc, bc.d[0], "0.01")
        self.refuse_f("INV-52", bc, "acompte", "0.01", devis_id=bc.d[0])
        self.avoir(a, "0.01")
        self.assertTrue(self.neutralisee(a))
        self.accepte_f(bc, "acompte", "0.01", devis_id=bc.d[0])

    # --- situation : un centime, neutralisation et référence ρ ------------------------------------------------------------------
    def test_T48_R_une_situation_d_un_centime_neutralisee_cesse_d_etre_la_reference(self):
        bc = self.monde()
        s1 = self.sit(bc, 1, "0.02")
        self.ligne_f(s1, 1, "avancement", "0.02", bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="50.00")
        self.avoir(s1, "0.01")                                                                              # partiel : S1 reste la référence
        s2 = self.sit(bc, 2)
        self.assertRegex(self.tente_av(s2, 1, bc.lignes[0], "0.00", "60.00"), "INV-190")
        self.assertIsNone(self.tente_av(s2, 1, bc.lignes[0], "50.00", "60.00"))
        self.avoir(s1, "0.01")                                                                              # total : S1 neutralisée
        s3 = self.sit(bc, 3)
        self.assertIsNone(self.tente_av(s3, 1, bc.lignes[0], "0.00", "60.00"))
        self.assertRegex(self.tente_av(s3, 1, bc.lignes[0], "50.00", "60.00"), "INV-190")

    def test_T48_R_la_reference_est_la_situation_non_neutralisee_d_ordinal_le_plus_grand_meme_sans_lignes(self):
        bc = self.monde()
        s1 = self.sit(bc, 1, "100.00")
        self.ligne_f(s1, 1, "avancement", "1.00", bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="20.00")
        s2 = self.sit(bc, 2, "100.00")
        self.ligne_f(s2, 1, "avancement", "1.00", bc.lignes[0], avancement_precedent_pct="20.00", avancement_cumule_pct="30.00")
        s3 = self.sit(bc, 3)
        self.assertIsNone(self.tente_av(s3, 1, bc.lignes[0], "30.00", "40.00"))
        self.assertRegex(self.tente_av(s3, 1, bc.lignes[0], "20.00", "40.00"), "INV-190")
        self.avoir(s2, "100.00")
        self.assertIsNone(self.tente_av(s3, 1, bc.lignes[0], "20.00", "40.00"))                              # S2 neutralisée : retour à S1
        self.assertRegex(self.tente_av(s3, 1, bc.lignes[0], "30.00", "40.00"), "INV-190")

    def test_T48_R_une_ligne_de_deduction_rattachee_a_une_ligne_de_BC_n_est_pas_un_avancement_de_reference(self):
        """Dans la situation de référence, une déduction (sans pourcentage) portant le bc_ligne_id de la ligne, insérée AVANT la ligne d'avancement, ne masque pas
        le cumulé de la ligne d'avancement."""
        bc = self.monde()
        s1 = self.sit(bc, 1, "100.00")
        self.ligne_f(s1, 1, "deduction", "-1.00", bc.lignes[0])
        self.ligne_f(s1, 2, "avancement", "1.00", bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="50.00")
        s2 = self.sit(bc, 2)
        self.assertIsNone(self.tente_av(s2, 1, bc.lignes[0], "50.00", "60.00"))
        self.assertRegex(self.tente_av(s2, 1, bc.lignes[0], "0.00", "60.00"), "INV-190")

    # --- solde : un centime, BC vide, BC sans devis ----------------------------------------------------------------------------
    def test_T48_R_solde_d_un_centime_sur_un_BC_vide_et_apres_une_situation(self):
        bc = self.monde(devis=[{"lignes": ["0.01"]}])
        self.refuse_f("INV-58", bc, "solde", "0.00")
        self.refuse_f("INV-58", bc, "solde", "0.02")
        self.accepte_f(bc, "solde", "0.01")
        self.facture(bc, "solde", "0.01")                                                                   # un solde de 0.01 sans avoir est actif : aucun second solde
        self.refuse_f("INV-52", bc, "solde", "0.00")
        bc2 = self.monde(devis=[{"lignes": ["1000.00"]}])
        self.sit(bc2, 1, "999.99")
        self.refuse_f("INV-58", bc2, "solde", "0.00")
        self.refuse_f("INV-58", bc2, "solde", "0.02")
        self.accepte_f(bc2, "solde", "0.01")

    def test_T48_R_solde_a_zero_apres_une_situation_a_100_pour_cent(self):
        bc = self.monde(devis=[{"lignes": ["1000.00"]}])
        self.sit(bc, 1, "1000.00")
        self.accepte_f(bc, "solde", "0.00")
        self.refuse_f("INV-58", bc, "solde", "0.01")

    def test_T48_R_un_BC_sans_devis_rattache_a_un_contractuel_nul(self):
        d = self.devis_accepte()
        b = self.creer_bc(d, lier=False)
        self.refuse_f("INV-57", b, "situation", "0.01", situation_numero=1, montant_deja_facture_ht="0.00")
        self.refuse_f("INV-189", b, "acompte", "0.01", devis_id=d)
        self.accepte_f(b, "solde", "0.00")
        self.refuse_f("INV-58", b, "solde", "0.01")

    # --- TR-02 : séquence de l'année, séquence du préfixe ---------------------------------------------------------------------
    def test_T48_R_TR02_la_sequence_d_une_autre_annee_ne_contraint_pas_la_date_d_une_annee_anterieure(self):
        bc = self.monde(devis=[{"lignes": ["10000.00"]}])
        self.un(ATTRIBUER, "FAC", 27)
        self.db.execute("UPDATE numerotation_sequences SET derniere_date='2027-03-01' WHERE type_objet='FAC' AND annee=27")
        self.accepte_f(bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", date_emission="2026-12-31", date_echeance="2027-01-30",
                       numero="FAC-00001-26")
        self.refuse_f("INV-24", bc, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00", date_emission="2027-02-28", date_echeance="2027-03-30",
                      numero="FAC-00002-27")

    def test_T48_R_TR02_chaque_prefixe_n_est_contraint_que_par_sa_propre_sequence(self):
        types = (("acompte", "ACP"), ("avoir", "AVO"), ("situation", "FAC"), ("solde", "FAC"))
        for cible in ("ACP", "AVO", "FAC"):
            with self.subTest(cible=cible):
                bc = self.monde(devis=[{"lignes": ["10000.00"], "acompte": ("montant", "100.00")}])
                s0 = self.sit(bc, 1, "10.00", date_emission="2026-01-02", date_echeance="2026-02-01")
                for pre in ("ACP", "AVO", "FAC"):
                    self.un(ATTRIBUER, pre, 26)
                    self.fixer_date(pre, 26, "2026-10-10" if pre == cible else "2026-01-01")
                for type_, pre in types:
                    kw = {"acompte": dict(devis_id=bc.d[0]), "avoir": dict(origine_facture_id=s0),
                          "situation": dict(situation_numero=2, montant_deja_facture_ht="10.00"), "solde": {}}[type_]
                    total = {"acompte": "100.00", "avoir": "5.00", "situation": "10.00", "solde": "9990.00"}[type_]
                    if type_ != "avoir":
                        kw["date_echeance"] = "2026-11-30"
                    kw["date_emission"] = "2026-10-09"
                    with self.subTest(cible=cible, type=type_):
                        if pre == cible:
                            self.refuse_f("INV-24", bc, type_, total, **kw)
                        else:
                            self.accepte_f(bc, type_, total, **kw)

    # --- un solde, un acompte ou une situation d'un AUTRE BC ne contraint pas ce BC ---------------------------------------------------
    def test_T48_R_le_solde_d_un_autre_BC_ne_bloque_ni_acompte_ni_situation_ni_solde(self):
        bc1 = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "100.00")}])
        bc2 = self.monde(devis=[{"lignes": ["2000.00"], "acompte": ("montant", "100.00")}])
        self.facture(bc1, "solde", "1000.00")
        self.accepte_f(bc2, "acompte", "100.00", devis_id=bc2.d[0])
        self.accepte_f(bc2, "situation", "10.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.accepte_f(bc2, "solde", "2000.00")
        self.facture(bc2, "solde", "2000.00")                                                               # deux soldes actifs sur deux BC distincts
        self.assertEqual(self.un("SELECT count(*) FROM factures WHERE type='solde'")[0], 2)

    def test_T48_R_l_acompte_d_un_autre_devis_d_un_autre_BC_ne_bloque_pas_ce_devis(self):
        bc1 = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "100.00")}])
        bc2 = self.monde(devis=[{"lignes": ["1000.00"], "acompte": ("montant", "100.00")}])
        self.acompte(bc1, bc1.d[0], "100.00")
        self.accepte_f(bc2, "acompte", "100.00", devis_id=bc2.d[0])

    def test_T48_R_une_situation_d_un_centime_sans_avoir_reste_la_reference(self):
        bc = self.monde()
        s1 = self.sit(bc, 1, "0.01")
        self.ligne_f(s1, 1, "avancement", "0.01", bc.lignes[0], avancement_precedent_pct="0.00", avancement_cumule_pct="50.00")
        s2 = self.sit(bc, 2)
        self.assertIsNone(self.tente_av(s2, 1, bc.lignes[0], "50.00", "60.00"))
        self.assertRegex(self.tente_av(s2, 1, bc.lignes[0], "0.00", "60.00"), "INV-190")


if __name__ == "__main__":
    unittest.main()
