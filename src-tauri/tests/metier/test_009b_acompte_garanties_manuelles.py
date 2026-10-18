"""Migration corrective 009b_acompte_garanties_manuelles (rang 14, après 009a_bc_annulation_interdite_si_facture) ; révision G (2026-10-17), révisée le 2026-10-18 (V3.14) : ordre acompte / situation par COUVERTURE (INV-204, INV-205, D-62). Ce fichier porte les règles historiques de 009b ; les 13 tests d'acceptation T-53 de la couverture sont dans test_009b_couverture_situations.py.

009b aligne le SQL livré (006, 008 — IMMUABLES) sur les décisions métier validées :
  * acompte : plafonné par l'acompte PRÉVU du devis (aucun / pourcentage / montant), jusqu'à 100 % du marché ; aucun plafond « générique » ;
    facturation facultative ; aucune confirmation spéciale à 100 % (le plafond du devis est la règle) ;
  * situation : jamais à 100 % du contractuel (nette après < contractuel) ;
  * solde : strictement positif, aucun solde à 0.00 ; égal au contractuel FINAL (contractuel moins avoirs « prestation_non_realisee » sur solde) moins la
    facturation nette avant le solde ; aucun acompte préalable exigé ;
  * avoirs : motif en liste fermée (correction_erreur | prestation_non_realisee), un avoir sur acompte ne corrige qu'une erreur ;
  * ordre des factures : aucun acompte sur un devis COUVERT par une situation (situation_devis, V3.14 ; INV-205) ni après un solde ; l'acompte est facultatif ; un acompte prévu à 100 % et entièrement facturé
    ne clôture pas le cycle (aucun solde à 0.00) ; aucune règle de cumul supplémentaire sur l'acompte ;
  * garanties : déclenchement MANUEL, sans facture de solde (facture_declenchement_id nullable) ; périmètre contractuel réel : retrait ciblé d'une
    prestation (bc_ligne_retraits_garantie) par moins-value (écrite par le service) ou par avoir « prestations non réalisées » sur un SOLDE ;
    un avoir d'erreur ou un avoir sur situation ne retire rien ; aucun double retrait ; les garanties des autres prestations restent inchangées.

Les tests 006 et 008 décrivent ces migrations TELLES QUE LIVRÉES (rangs 9 et 11) : ils ne sont pas réécrits. Ce fichier vérifie le comportement du rang 14.

Responsabilités vérifiées ici : fichiers de la chaîne et rang ; protocole de reconstruction (foreign_keys, foreign_key_check, integrity_check, ROLLBACK intégral) ;
préservation des données (garanties existantes, soldes à 0.00 historiques, sqlite_sequence) ; schéma exact ; plafonds d'acompte ; situation < 100 % ;
solde > 0 ; indépendance des garanties vis-à-vis du solde et de l'état du BC ; retraits de prestation ; immuabilité.
Ne sont PAS dans le SQL (règles de service, hors de ces tests) : le déclenchement manuel lui-même, la date de déclenchement, la moins-value (aucune table : le
stockage des réductions est À CONCEVOIR, donc le contractuel COURANT n'est pas modélisé), l'avertissement avant moins-value, le périmètre résiduel d'une
moins-value ou d'un avoir partiel (À CONCEVOIR). Les sections K à N vérifient, sur la chaîne COMPLÈTE (001 à 009b), le contractuel final, les motifs d'avoir,
l'ordre des factures et le suivi actif des garanties.

Exécution : python3 src-tauri/tests/metier/test_009b_acompte_garanties_manuelles.py
"""
import pathlib
import sqlite3
import sys
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import test_009_pv as P  # noqa: E402  (chaîne 001 à 009, fabriques de devis, BC, factures, avoirs et garanties)

G = P.G
F = G.R.F
T, C = F.T, F.C
MIGRATIONS = F.MIGRATIONS
NOM_009B = "009b_acompte_garanties_manuelles.sql"
NOM_009A = "009a_bc_annulation_interdite_si_facture.sql"
SQL_009A = (MIGRATIONS / NOM_009A).read_text(encoding="utf-8")
NOMS = P.NOMS + (NOM_009A, NOM_009B)
SQL_009B = (MIGRATIONS / NOM_009B).read_text(encoding="utf-8")
RANG_009A = 13
RANG = 14
c, eur, dl = F.c, F.eur, F.dl
OMIT = F.OMIT
D_REF = "2026-10-05"

TRIGGERS_AJOUTES = {"tr_50_bc_ligne_retraits_garantie_update", "tr_50_bc_ligne_retraits_garantie_no_delete", "tr_51_bc_ligne_retraits_garantie_insert",
                    "tr_104_situation_devis_insert", "tr_105_situation_devis_update", "tr_105_situation_devis_delete"}
TRIGGERS_REMPLACES = {"tr_22_factures_acompte", "tr_22_factures_situation", "tr_22_factures_solde", "tr_23_factures_avoir", "tr_51_garanties_insert"}
VUES_AJOUTEES = {"v_garanties_suivi_actif"}
TRIGGERS_RECREES = {"tr_50_garanties_update", "tr_50_garanties_no_delete"}
INDEXES_RETRAITS = {"idx_bc_ligne_retraits_garantie_bc_id", "idx_bc_ligne_retraits_garantie_avoir_id", "idx_situation_devis_devis_id"}
COLONNES_RETRAITS = ["id", "bc_id", "bc_ligne_id", "motif_retrait", "avoir_id", "date_retrait", "created_at"]
COLONNES_GARANTIES = ["id", "bc_id", "bc_ligne_id", "garantie_type", "date_declenchement", "date_fin_suivi", "facture_declenchement_id", "created_at"]


# --------------------------------------------------------------------------------------------------------------------
# Chaîne
# --------------------------------------------------------------------------------------------------------------------
def migrer13(recursive=True):
    """Chaîne 001 à 009 (rang 12) puis 009a_bc_annulation_interdite_si_facture (rang 13) : le point de départ de 009b."""
    db = P.migrer12(recursive=recursive)
    T.appliquer(db, RANG_009A, SQL_009A)
    return db


def migrer14(recursive=True):
    """Chaîne 001 à 009 (rang 12), 009a_bc_annulation_interdite_si_facture (rang 13) puis 009b avec le protocole de reconstruction du runner
    (foreign_keys=OFF, contrôles, user_version = 14)."""
    db = migrer13(recursive=recursive)
    T.runner(db, RANG, SQL_009B)
    return db


def prevu(total_cents, type_, valeur):
    """Oracle : acompte prévu d'un devis, en centimes (HALF_UP, entiers purs)."""
    if type_ == "aucun":
        return 0
    v = int(valeur.replace(".", ""))
    if type_ == "montant":
        return v
    return (total_cents * v * 2 + 10000) // 20000                                                    # arrondi HALF_UP de total × pct / 100 sans flottant


class Base14(P.Base12):
    """Base au rang 14. Fabriques héritées de test_005b à 009 ; les fabriques propres à 009b sont définies ici."""

    DECALAGES = P.Base12.DECALAGES + (("bc_ligne_retraits_garantie", 115),)

    def setUp(self):
        self.db = migrer14()
        self._n = 0
        self._npv = {}
        self.desynchroniser_ids()

    @classmethod
    def _sur(cls, db):
        t = cls()
        t.db = db
        t._n = 0
        t._npv = {}
        t.desynchroniser_ids()
        return t

    # --- monde : un BC à un devis dont l'acompte prévu est choisi ----------------------------------------------------
    def monde_a(self, lignes=(("1000.00", ("decennale",)),), acompte_type="aucun", acompte_valeur=None, total=None):
        """BC en cours à un devis. `lignes` : (montant, types de garantie). Le total du devis est la somme des lignes (ou `total`)."""
        cli = self.client()
        brut = sum(c(m) for m, _ in lignes)
        d = self.brouillon(client_id=cli, total_ht=total or eur(brut), acompte_type=acompte_type, acompte_valeur=acompte_valeur, remise_type="aucune")
        for k, (m, ts) in enumerate(lignes, 1):
            lid = self.ligne(d, k, designation=f"Ligne {k}", quantite="1", prix_unitaire_ht=dl(m), total_ht=m)
            for ty in ts:
                self.garantie(lid, ty)
        self.finaliser(d)
        self.accepter(d)
        b = self.creer_bc(d)
        bls = [r_[0] for r_ in self.tous("SELECT bl.id FROM bc_lignes bl JOIN devis_lignes dl ON dl.id = bl.devis_ligne_id WHERE dl.devis_id = ? ORDER BY dl.ordre", d)]
        return types.SimpleNamespace(b=b, cli=cli, d=[d], bl=[bls], lignes=bls)

    def monde_pa(self):
        """BC de deux lignes (garanties decennale + biennale, puis parfait_achevement) dont le devis prévoit 20 % d'acompte : les factures d'acompte sont possibles."""
        return self.monde_a(lignes=(("4000.00", ("decennale", "biennale")), ("2000.00", ("parfait_achevement",))), acompte_type="pourcentage", acompte_valeur="20.00")

    def acompte_ok(self, bc, total, **kw):
        m = self.tente_f(bc, "acompte", total, devis_id=bc.d[0], **kw)
        self.assertIsNone(m, m)

    def acompte_ko(self, bc, total, inv="INV-57", **kw):
        m = self.tente_f(bc, "acompte", total, devis_id=bc.d[0], **kw)
        self.assertIsNotNone(m, f"acompte {total} accepté à tort")
        self.assertRegex(m, inv)

    # --- couverture des situations (V3.14, §4.8 ter) ------------------------------------------------------------------------
    def couvrir(self, facture, bc):
        """Service d'émission : UNE instruction INSERT … SELECT sur tous les devis alors rattachés au BC (aucune liste en paramètre)."""
        bc_id = bc.b if hasattr(bc, "b") else bc
        self.db.execute("INSERT INTO situation_devis (facture_id, devis_id) SELECT ?, devis_id FROM bc_devis WHERE bc_id = ?", (facture, bc_id))

    def situation(self, bc, total, numero, avant, **kw):
        """Situation émise AVEC sa couverture (insertion brute de la facture, puis couverture) ; retourne l'id de la facture."""
        f = self.facture(bc, "situation", total, situation_numero=numero, montant_deja_facture_ht=avant, **kw)
        self.couvrir(f, bc)
        return f

    def couverture(self, facture):
        return [d for (d,) in self.tous("SELECT devis_id FROM situation_devis WHERE facture_id=? ORDER BY devis_id", facture)]

    # --- garanties manuelles --------------------------------------------------------------------------------------------
    def declenche(self, ligne, type_, date=D_REF, **kw):
        """Garantie déclenchée manuellement : aucune facture de déclenchement."""
        return self.garantie_g(ligne, type_, None, date_declenchement=date, **kw)

    def tente_manuel(self, ligne, type_, date=D_REF, **kw):
        return self.tente_g(ligne, type_, None, date_declenchement=date, **kw)

    # --- retraits ---------------------------------------------------------------------------------------------------------
    def avoir_motif(self, origine, motif, total=None, ligne=None, **kw):
        """Avoir sur `origine` de motif donné ; si `ligne` est fourni, la ligne de l'avoir référence cette ligne de BC."""
        b, tot = self.un("SELECT bc_id, total_ht FROM factures WHERE id=?", origine)
        total = total or tot
        cols = self.cols_facture(b, "avoir", total, origine_facture_id=origine, motif_avoir=motif, **kw)
        f = self.inserer("factures", cols)
        self.ligne_f(f, 1, "prestation", total, ligne)
        return f

    def retrait(self, ligne, motif="moins_value", avoir=None, date=D_REF, **kw):
        cols = {"bc_ligne_id": ligne, "motif_retrait": motif, "avoir_id": avoir, "date_retrait": date}
        cols["bc_id"] = kw["bc_id"] if "bc_id" in kw else self.bc_de_ligne(ligne)
        cols.update(kw)
        return self.inserer("bc_ligne_retraits_garantie", {k: v for k, v in cols.items() if v is not OMIT})

    def tente_retrait(self, ligne, motif="moins_value", avoir=None, **kw):
        self.db.execute("SAVEPOINT tenterr")
        try:
            self.retrait(ligne, motif, avoir, **kw)
            return None
        except sqlite3.IntegrityError as e:
            return str(e)
        finally:
            self.db.execute("ROLLBACK TO tenterr")
            self.db.execute("RELEASE tenterr")

    def retrait_ko(self, ligne, motif, avoir, inv, **kw):
        m = self.tente_retrait(ligne, motif, avoir, **kw)
        self.assertIsNotNone(m, "retrait accepté à tort")
        if inv:
            self.assertRegex(m, inv)
        else:
            self.assertNotIn("INV-", m)

    def suivi_actif(self, b):
        """Suivi actif lu dans la vue v_garanties_suivi_actif (état dérivé : garanties dont la ligne de BC n'a pas de retrait)."""
        return self.tous("SELECT id FROM v_garanties_suivi_actif WHERE bc_id=? ORDER BY id", b)

    def cols_facture(self, bc, type_, total, **kw):
        """Un avoir est « correction_erreur » par défaut (motif en liste fermée, TR-23) ; `kw` le remplace."""
        if type_ == "avoir":
            kw.setdefault("motif_avoir", "correction_erreur")
        return super().cols_facture(bc, type_, total, **kw)

    def monde_devis(self, specs):
        """BC en cours à plusieurs devis : `specs` = (total, acompte_type, acompte_valeur) ; une ligne par devis."""
        cli = self.client()
        ds = []
        for tot, ty, val in specs:
            d = self.brouillon(client_id=cli, total_ht=tot, acompte_type=ty, acompte_valeur=val, remise_type="aucune")
            lid = self.ligne(d, 1, designation="L", quantite="1", prix_unitaire_ht=dl(tot), total_ht=tot)
            self.garantie(lid, "decennale")
            self.finaliser(d)
            self.accepter(d)
            ds.append(d)
        b = self.creer_bc(ds[0])
        for d in ds[1:]:
            self.rattacher(b, d)
        return types.SimpleNamespace(b=b, cli=cli, d=ds)

    # --- second devis rattaché APRÈS une situation (règle du 2026-10-17 : l'ordre s'apprécie par devis) ----------------------------
    LIEN_D2 = "2099-01-01T00:00:00.000Z"          # rattachement du second devis : postérieur aux factures de test (TS_EMISSION 2050)
    ACOMPTE_D2 = "2099-02-01T00:00:00.000Z"
    SITUATION_2 = "2099-03-01T00:00:00.000Z"

    def devis_accepte_a(self, bc, total, acompte_type, acompte_valeur):
        """Devis accepté (une ligne garantie) du client du BC, non rattaché."""
        d = self.brouillon(client_id=bc.cli, total_ht=total, acompte_type=acompte_type, acompte_valeur=acompte_valeur, remise_type="aucune")
        lid = self.ligne(d, 1, designation="L2", quantite="1", prix_unitaire_ht=dl(total), total_ht=total)
        self.garantie(lid, "decennale")
        self.finaliser(d)
        self.accepter(d)
        return d

    def rattacher_a(self, bc, d, ts=None):
        """Service de rattachement (lien, copie des lignes et garanties, contractuel augmenté) avec un lien daté explicitement (bc_devis n'est pas modifiable)."""
        ts = ts or self.LIEN_D2
        rang = self.un("SELECT COALESCE(MAX(rang), 0) + 1 FROM bc_devis WHERE bc_id=?", bc.b)[0]
        self.db.execute("INSERT INTO bc_devis (bc_id, devis_id, rang, created_at) VALUES (?, ?, ?, ?)", (bc.b, d, rang, ts))
        self.ts_lignes = ts
        try:
            self.copier_lignes(bc.b, d)
        finally:
            self.ts_lignes = F.TS
        total = self.un("SELECT total_ht FROM devis WHERE id=?", d)[0]
        self.db.execute("UPDATE bons_commande SET montant_contractuel_ht = ? WHERE id=?", (eur(self.contractuel(bc.b) + c(total)), bc.b))
        bc.d.append(d)
        return d

    def monde_apres_situation(self, total1="1000.00", type1="pourcentage", val1="100.00", total2="800.00", type2="pourcentage", val2="50.00"):
        """BC à un premier devis, déjà facturé par une situation (100.00), puis second devis accepté rattaché APRÈS cette situation. Retourne (bc, d1, d2)."""
        bc = self.monde_devis([(total1, type1, val1)])
        self.situation(bc, "100.00", 1, "0.00")
        d2 = self.devis_accepte_a(bc, total2, type2, val2)
        self.rattacher_a(bc, d2)
        return bc, bc.d[0], d2

    def acompte_d2(self, bc, d, total, **kw):
        kw.setdefault("created_at", self.ACOMPTE_D2)
        return self.acompte(bc, d, total, **kw)

    def tente_acompte(self, bc, d, total, **kw):
        kw.setdefault("created_at", self.ACOMPTE_D2)
        return self.tente_f(bc, "acompte", total, devis_id=d, **kw)

    def contractuel_final(self, b):
        """Oracle (service) : contractuel moins les avoirs prestation_non_realisee dont l'origine est un solde ; en centimes."""
        b = b.b if hasattr(b, "b") else b
        nr = sum(c(t) for (t,) in self.tous("SELECT a.total_ht FROM factures a JOIN factures o ON o.id = a.origine_facture_id "
                                            "WHERE a.bc_id=? AND a.type='avoir' AND a.motif_avoir='prestation_non_realisee' AND o.type='solde'", b))
        return self.contractuel(b) - nr

    def solde_final(self, bc, date=D_REF, **kw):
        """Solde émis au montant du contractuel final moins la facturation nette (insertion brute, sans lignes)."""
        total = self.contractuel_final(bc) - self.nette(bc)
        kw.setdefault("date_echeance", date)
        return self.facture(bc, "solde", eur(total), date_emission=date, **kw)


# --------------------------------------------------------------------------------------------------------------------
# A. Chaîne, rang, protocole, schéma
# --------------------------------------------------------------------------------------------------------------------
class Chaine(Base14):
    def test_009b_fichiers_de_la_chaine_dans_l_ordre(self):
        noms = [p.name for p in sorted(MIGRATIONS.glob("*.sql"))]
        self.assertEqual(noms[:14], list(NOMS))
        self.assertEqual(noms[12], NOM_009A)
        self.assertEqual(noms[13], NOM_009B)

    def test_009b_rang_14_et_user_version(self):
        self.assertEqual(self.un("PRAGMA user_version")[0], 14)

    def test_009b_aucune_transaction_ni_pragma_ni_donnee_metier_dans_le_fichier(self):
        for st in T.instructions(SQL_009B):
            tete = T.sans_commentaires(st).strip().upper()
            for interdit in ("BEGIN", "COMMIT", "ROLLBACK", "PRAGMA", "DELETE", "UPDATE FACTURES", "UPDATE GARANTIES"):
                self.assertFalse(tete.startswith(interdit), tete[:60])
            if tete.startswith("INSERT"):
                self.assertTrue(tete.startswith("INSERT INTO GARDE_009B") or tete.startswith("INSERT INTO GARANTIES_NEW") or tete.startswith("INSERT INTO SQLITE_SEQUENCE"), tete[:60])

    def test_009b_les_messages_des_triggers_sont_ASCII_et_portent_un_invariant(self):
        for nom, sql in self.tous("SELECT name, sql FROM sqlite_master WHERE type='trigger' AND name IN (%s)" %
                                  ",".join("?" * len(TRIGGERS_AJOUTES | TRIGGERS_REMPLACES | TRIGGERS_RECREES)), *sorted(TRIGGERS_AJOUTES | TRIGGERS_REMPLACES | TRIGGERS_RECREES)):
            import re
            for m in re.findall(r"RAISE\(ABORT, '((?:[^']|'')*)'\)", sql):
                self.assertTrue(m.isascii(), (nom, m))
                self.assertRegex(m, r"^INV-\d+:", (nom, m))

    def test_009b_les_migrations_006_et_008_sont_inchangees_dans_leur_comportement_de_rang(self):
        """Rang 11 : 008 accepte toujours son ancien comportement (garantie liée à un solde) — cf. test_008. Ici : la chaîne du rang 13 reste constructible."""
        db = migrer13()
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 13)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='bc_ligne_retraits_garantie'").fetchone()[0], 0)

    def test_009b_le_runner_est_necessaire_foreign_keys_ON_refuse_la_migration(self):
        db = migrer13()
        db.execute("PRAGMA foreign_keys=ON")
        with self.assertRaises(sqlite3.IntegrityError) as cm:
            db.executescript(f"BEGIN IMMEDIATE;\n{SQL_009B}\nPRAGMA user_version = 14;\nCOMMIT;")
        self.assertIn("foreign_keys = OFF", str(cm.exception))
        if db.in_transaction:
            db.execute("ROLLBACK")
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 13)

    def test_009b_refuse_une_base_qui_n_est_pas_au_rang_13(self):
        for rang in (11, 12, 14):
            db = migrer13()
            db.execute(f"PRAGMA user_version = {rang}")
            avant = [r for r in db.execute("SELECT type, name, sql FROM sqlite_master ORDER BY name")]
            with self.assertRaises((sqlite3.IntegrityError, T.ErreurRunner)):
                T.runner(db, RANG, SQL_009B)
            self.assertEqual(avant, [r for r in db.execute("SELECT type, name, sql FROM sqlite_master ORDER BY name")])
            self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_009b_atomicite_une_erreur_annule_tout(self):
        db = migrer13()
        avant = [r for r in db.execute("SELECT type, name, sql FROM sqlite_master ORDER BY name")]
        casse = SQL_009B + "\nCREATE TABLE bc_ligne_retraits_garantie (x INTEGER);\n"                  # collision de nom en fin de fichier
        with self.assertRaises(sqlite3.OperationalError):
            T.runner(db, RANG, casse)
        self.assertEqual(avant, [r for r in db.execute("SELECT type, name, sql FROM sqlite_master ORDER BY name")])
        self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 13)
        self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_009b_foreign_key_check_et_integrity_check_sont_propres(self):
        self.assertEqual(self.tous("PRAGMA foreign_key_check"), [])
        self.assertEqual(self.tous("PRAGMA integrity_check"), [("ok",)])

    def test_009b_objets_exacts_au_rang_14(self):
        avant = migrer13()
        tables_avant = {n for (n,) in avant.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        tables = {n for (n,) in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual(tables - tables_avant, {"bc_ligne_retraits_garantie", "situation_devis"})
        self.assertEqual(tables_avant - tables, set())
        trig_avant = {n for (n,) in avant.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
        trig = {n for (n,) in self.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
        self.assertEqual(trig - trig_avant, TRIGGERS_AJOUTES)
        self.assertEqual(trig_avant - trig, set())
        idx = {n for (n,) in self.db.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")}
        idx_avant = {n for (n,) in avant.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")}
        self.assertEqual(idx - idx_avant, INDEXES_RETRAITS)
        self.assertEqual(idx_avant - idx, set())
        vues = {n for (n,) in self.db.execute("SELECT name FROM sqlite_master WHERE type='view'")}
        self.assertEqual(vues, VUES_AJOUTEES)
        self.assertEqual({n for (n,) in avant.execute("SELECT name FROM sqlite_master WHERE type='view'")}, set())

    def test_009b_seuls_les_triggers_annonces_changent_les_autres_sont_identiques_au_caractere_pres(self):
        avant = migrer13()
        a = dict(avant.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'").fetchall())
        n = dict(self.db.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'").fetchall())
        changes = {k for k in a if a[k] != n.get(k)}
        self.assertEqual(changes, TRIGGERS_REMPLACES)
        for k in TRIGGERS_RECREES:
            self.assertEqual(a[k], n[k], k)

    def test_009b_garanties_seule_la_nullabilite_de_la_facture_de_declenchement_change(self):
        avant = migrer13()
        ia = {r[1]: r for r in avant.execute("PRAGMA table_info(garanties)")}
        ib = {r[1]: r for r in self.db.execute("PRAGMA table_info(garanties)")}
        self.assertEqual(list(ia), COLONNES_GARANTIES)
        self.assertEqual(list(ib), COLONNES_GARANTIES)
        self.assertEqual(ia["facture_declenchement_id"][3], 1)
        self.assertEqual(ib["facture_declenchement_id"][3], 0)
        for col in COLONNES_GARANTIES:
            if col != "facture_declenchement_id":
                self.assertEqual(ia[col], ib[col], col)
        self.assertEqual([tuple(r[2:5]) for r in avant.execute("PRAGMA foreign_key_list(garanties)")], [tuple(r[2:5]) for r in self.db.execute("PRAGMA foreign_key_list(garanties)")])
        self.assertEqual(self.db.execute("SELECT strict FROM pragma_table_list('garanties')").fetchone()[0], 1)

    def test_009b_table_des_retraits_stricte_colonnes_fk_restrict_et_unicite(self):
        self.assertEqual([r[1] for r in self.db.execute("PRAGMA table_info(bc_ligne_retraits_garantie)")], COLONNES_RETRAITS)
        self.assertEqual(self.db.execute("SELECT strict FROM pragma_table_list('bc_ligne_retraits_garantie')").fetchone()[0], 1)
        fks = {r[3]: (r[2], r[6]) for r in self.db.execute("PRAGMA foreign_key_list(bc_ligne_retraits_garantie)")}
        self.assertEqual(fks, {"bc_id": ("bons_commande", "RESTRICT"), "bc_ligne_id": ("bc_lignes", "RESTRICT"), "avoir_id": ("factures", "RESTRICT")})
        uniques = [[x[2] for x in self.db.execute(f"PRAGMA index_info({i[1]})")] for i in self.db.execute("PRAGMA index_list(bc_ligne_retraits_garantie)") if i[2] == 1]
        self.assertIn(["bc_ligne_id"], uniques)

    def test_009b_toute_cle_etrangere_des_retraits_est_couverte_par_un_index_de_tete(self):
        tetes = {self.db.execute(f"SELECT name FROM pragma_index_info('{i[1]}') WHERE seqno=0").fetchone()[0]
                 for i in self.db.execute("PRAGMA index_list(bc_ligne_retraits_garantie)")}
        self.assertTrue({"bc_id", "bc_ligne_id", "avoir_id"} <= tetes)


# --------------------------------------------------------------------------------------------------------------------
# B. Préservation des données
# --------------------------------------------------------------------------------------------------------------------
class Donnees(unittest.TestCase):
    def _base12_peuplee(self):
        t = P.Base12()
        t.db = migrer13()
        t._n = 0
        t._npv = {}
        t.desynchroniser_ids()
        bc = t.monde_g()
        t.acompte(bc, bc.d[0], "1000.00")
        s = t.solde_g(bc)
        ids = t.creer_toutes(bc, s)
        return t, bc, s, ids

    def test_009b_les_garanties_existantes_sont_copiees_a_l_identique_avec_leurs_ids(self):
        t, bc, s, ids = self._base12_peuplee()
        avant = t.db.execute("SELECT * FROM garanties ORDER BY id").fetchall()
        seq_avant = t.db.execute("SELECT seq FROM sqlite_sequence WHERE name='garanties'").fetchone()[0]
        T.runner(t.db, RANG, SQL_009B)
        self.assertEqual(avant, t.db.execute("SELECT * FROM garanties ORDER BY id").fetchall())
        self.assertTrue(all(r[6] == s for r in avant))                                              # la facture de déclenchement historique est conservée
        seq = t.db.execute("SELECT seq FROM sqlite_sequence WHERE name='garanties'").fetchone()[0]
        self.assertGreaterEqual(seq, seq_avant)
        self.assertEqual(t.db.execute("SELECT COUNT(*) FROM sqlite_sequence WHERE name='garanties_new'").fetchone()[0], 0)
        self.assertEqual(t.db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_009b_la_sequence_ne_regresse_pas_un_id_n_est_jamais_reutilise(self):
        t, bc, s, ids = self._base12_peuplee()
        t.db.execute("UPDATE sqlite_sequence SET seq = seq + 50 WHERE name='garanties'")            # séquence en avance sur max(id), comme après des insertions ignorées
        haut = t.db.execute("SELECT seq FROM sqlite_sequence WHERE name='garanties'").fetchone()[0]
        T.runner(t.db, RANG, SQL_009B)
        self.assertGreaterEqual(t.db.execute("SELECT seq FROM sqlite_sequence WHERE name='garanties'").fetchone()[0], haut)

    def test_009b_les_factures_les_lignes_et_les_autres_tables_ne_sont_pas_touchees(self):
        t, bc, s, ids = self._base12_peuplee()
        tables = ("factures", "facture_lignes", "bc_lignes", "bc_ligne_garanties", "bons_commande", "devis")
        avant = {n: t.db.execute(f"SELECT * FROM {n} ORDER BY id").fetchall() for n in tables}
        T.runner(t.db, RANG, SQL_009B)
        for n in tables:
            self.assertEqual(avant[n], t.db.execute(f"SELECT * FROM {n} ORDER BY id").fetchall(), n)

    def test_009b_un_solde_a_0_00_historique_est_conserve_et_reste_un_solde_actif(self):
        t = P.Base12()
        t.db = migrer13()
        t._n = 0
        t._npv = {}
        t.desynchroniser_ids()
        bc = t.monde_g()
        t.acompte(bc, bc.d[0], "6000.00")
        s0 = t.solde_g(bc)                                                                           # 006 admet ce solde à 0.00
        self.assertEqual(t.eur_solde(s0), "0.00")
        T.runner(t.db, RANG, SQL_009B)
        self.assertEqual(t.eur_solde(s0), "0.00")
        r = t.tente_f(bc, "solde", "1.00", date_emission="2026-10-06")
        self.assertRegex(r, "INV-52")                                                                # un seul solde actif : le solde à 0.00 historique n'est jamais neutralisé

    def test_009b_la_migration_est_equivalente_sur_base_fraiche_et_sur_base_peuplee(self):
        t, bc, s, ids = self._base12_peuplee()
        T.runner(t.db, RANG, SQL_009B)
        neuve = migrer14()
        schema = lambda d: sorted((a, b) for a, b in d.execute("SELECT name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall())
        self.assertEqual(schema(t.db), schema(neuve))


# --------------------------------------------------------------------------------------------------------------------
# C. Acompte : plafond = acompte prévu du devis
# --------------------------------------------------------------------------------------------------------------------
class Acompte(Base14):
    def test_009b_prevu_30_pour_cent_de_1000_plafond_300(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="30.00")
        self.acompte_ok(bc, "200.00")
        self.acompte_ok(bc, "300.00")
        self.acompte_ko(bc, "350.00")
        self.acompte_ko(bc, "300.01")

    def test_009b_prevu_100_pour_cent_plafond_1000_sans_confirmation_particuliere(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="100.00")
        self.acompte_ok(bc, "1000.00")
        self.acompte_ok(bc, "500.00")
        self.acompte_ko(bc, "1000.01")
        f = self.acompte(bc, bc.d[0], "1000.00")
        self.assertEqual(self.nette(bc), 100000)

    def test_009b_aucun_acompte_prevu_aucune_facture_d_acompte(self):
        bc = self.monde_a(acompte_type="aucun")
        self.acompte_ko(bc, "0.01")
        self.acompte_ko(bc, "100.00")

    def test_009b_prevu_en_montant(self):
        bc = self.monde_a(acompte_type="montant", acompte_valeur="150.00")
        self.acompte_ok(bc, "150.00")
        self.acompte_ok(bc, "1.00")
        self.acompte_ko(bc, "150.01")

    def test_009b_arrondi_HALF_UP_du_prevu_en_pourcentage(self):
        cas = [("333.33", "30.00"), ("100.05", "50.00"), ("0.01", "50.00"), ("99.99", "12.34"), ("1000.00", "0.00"), ("1234.56", "33.33"), ("7.77", "99.99")]
        for total, pct in cas:
            with self.subTest(total=total, pct=pct):
                bc = self.monde_a(lignes=((total, ("decennale",)),), acompte_type="pourcentage", acompte_valeur=pct)
                p = prevu(c(total), "pourcentage", pct)
                if p > 0:
                    self.acompte_ok(bc, eur(p))
                self.acompte_ko(bc, eur(p + 1))

    def test_009b_l_acompte_est_facultatif_situation_et_solde_sans_acompte(self):
        bc = self.monde_a(lignes=(("600.00", ("decennale",)), ("400.00", ("biennale",))), acompte_type="pourcentage", acompte_valeur="30.00")
        self.assertEqual(self.tous("SELECT id FROM factures WHERE bc_id=? AND type='acompte'", bc.b), [])
        s = self.emettre_situation(bc, {bc.lignes[0]: 5000, bc.lignes[1]: 5000})                      # 50 % sans aucun acompte
        self.assertEqual(self.eur_solde(s), "500.00")
        so = self.solde_g(bc)
        self.assertEqual(self.eur_solde(so), "500.00")

    def test_009b_solde_sans_acompte_ni_situation(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="30.00")
        so = self.solde_g(bc)
        self.assertEqual(self.eur_solde(so), "1000.00")

    def test_009b_acompte_inferieur_au_prevu_puis_situation_et_solde(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="30.00")
        self.acompte(bc, bc.d[0], "100.00")
        self.emettre_situation(bc, {bc.lignes[0]: 6000})                                              # cumul visé 60 %
        so = self.solde_g(bc)
        self.assertEqual(self.eur_solde(so), "400.00")

    def test_009b_plafond_par_devis_dans_un_bc_a_deux_devis(self):
        cli = self.client()
        ds = []
        for tot, ty, val in (("1000.00", "pourcentage", "20.00"), ("500.00", "montant", "50.00")):
            d = self.brouillon(client_id=cli, total_ht=tot, acompte_type=ty, acompte_valeur=val, remise_type="aucune")
            lid = self.ligne(d, 1, designation="L", quantite="1", prix_unitaire_ht=dl(tot), total_ht=tot)
            self.garantie(lid, "decennale")
            self.finaliser(d)
            self.accepter(d)
            ds.append(d)
        b = self.creer_bc(ds[0])
        self.rattacher(b, ds[1])
        bc = types.SimpleNamespace(b=b, d=ds)
        self.assertIsNone(self.tente_f(bc, "acompte", "200.00", devis_id=ds[0]))
        self.assertRegex(self.tente_f(bc, "acompte", "200.01", devis_id=ds[0]), "INV-57")
        self.assertIsNone(self.tente_f(bc, "acompte", "50.00", devis_id=ds[1]))
        self.assertRegex(self.tente_f(bc, "acompte", "50.01", devis_id=ds[1]), "INV-57")
        self.assertRegex(self.tente_f(bc, "acompte", "200.00", devis_id=ds[1]), "INV-57")             # le prévu de l'autre devis ne s'emprunte pas

    def test_009b_regles_anterieures_de_l_acompte_inchangees(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="50.00")
        a = self.acompte(bc, bc.d[0], "300.00")
        self.acompte_ko(bc, "100.00", inv="INV-52")                                                   # un seul acompte actif par devis
        self.avoir(a)                                                                                 # avoir total : l'acompte est neutralisé
        self.acompte_ok(bc, "500.00")                                                                 # nouvel acompte, dans le prévu
        self.acompte_ko(bc, "500.01")
        so = self.solde_g(bc)
        self.acompte_ko(bc, "10.00", inv="INV-58")                                                    # aucun acompte après un solde


# --------------------------------------------------------------------------------------------------------------------
# D. Situation < 100 % et solde > 0
# --------------------------------------------------------------------------------------------------------------------
class SituationEtSolde(Base14):
    def test_009b_une_situation_ne_porte_jamais_le_cumul_a_100_pour_cent(self):
        bc = self.monde_a(acompte_type="aucun")
        m = self.tente_f(bc, "situation", "1000.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.assertRegex(m, "INV-57")
        m = self.tente_f(bc, "situation", "1000.01", situation_numero=1, montant_deja_facture_ht="0.00")
        self.assertRegex(m, "INV-57")
        self.assertIsNone(self.tente_f(bc, "situation", "999.99", situation_numero=1, montant_deja_facture_ht="0.00"))

    def test_009b_le_cumul_avec_acompte_et_situations_precedentes_reste_sous_100(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="20.00")
        self.acompte(bc, bc.d[0], "200.00")
        self.assertRegex(self.tente_f(bc, "situation", "800.00", situation_numero=1, montant_deja_facture_ht="200.00"), "INV-57")
        self.assertIsNone(self.tente_f(bc, "situation", "799.99", situation_numero=1, montant_deja_facture_ht="200.00"))
        s1 = self.facture(bc, "situation", "500.00", situation_numero=1, montant_deja_facture_ht="200.00")
        self.assertRegex(self.tente_f(bc, "situation", "300.00", situation_numero=2, montant_deja_facture_ht="700.00"), "INV-57")
        self.assertIsNone(self.tente_f(bc, "situation", "299.99", situation_numero=2, montant_deja_facture_ht="700.00"))

    def test_009b_un_acompte_a_100_pour_cent_ferme_la_voie_aux_situations_et_au_solde_sans_creer_de_solde_a_0(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="100.00")
        self.acompte(bc, bc.d[0], "1000.00")
        self.assertEqual(self.nette(bc), self.contractuel(bc))
        self.assertRegex(self.tente_f(bc, "situation", "0.01", situation_numero=1, montant_deja_facture_ht="1000.00"), "INV-57")
        self.assertRegex(self.tente_f(bc, "solde", "0.00"), "INV-55")
        self.assertRegex(self.tente_f(bc, "solde", "1.00"), "INV-58")
        self.assertEqual(self.tous("SELECT id FROM factures WHERE bc_id=? AND type='solde'", bc.b), [])
        # le BC n'est ni clôturé ni modifié automatiquement (le cycle ultérieur est À CONCEVOIR)
        self.assertEqual(self.un("SELECT statut FROM bons_commande WHERE id=?", bc.b)[0], "en_cours")

    def test_009b_aucun_solde_a_0_00_quelle_que_soit_la_voie(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="100.00")
        self.acompte(bc, bc.d[0], "1000.00")
        self.assertRegex(self.tente_f(bc, "solde", "0.00"), "INV-55")
        bc2 = self.monde_a(acompte_type="aucun")
        self.assertRegex(self.tente_f(bc2, "solde", "0.00"), "INV-55")                               # même quand la formule ne l'exigerait pas

    def test_009b_solde_strictement_positif_apres_situation(self):
        bc = self.monde_a(acompte_type="aucun")
        self.emettre_situation(bc, {bc.lignes[0]: 9000})
        so = self.solde_g(bc)
        self.assertEqual(self.eur_solde(so), "100.00")

    def test_009b_solde_apres_avoir_d_erreur_sur_acompte_integral(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="100.00")
        a = self.acompte(bc, bc.d[0], "1000.00")
        self.avoir(a, "400.00")                                                                       # avoir partiel : la facturation nette redescend à 600
        so = self.solde_g(bc)
        self.assertEqual(self.eur_solde(so), "400.00")

    def test_009b_le_solde_reste_la_difference_exacte_et_un_seul_solde_actif(self):
        bc = self.monde_a(acompte_type="aucun")
        self.acompte_ko(bc, "1.00")
        self.assertRegex(self.tente_f(bc, "solde", "999.99"), "INV-58")
        so = self.solde_g(bc)
        self.assertRegex(self.tente_f(bc, "solde", "1.00"), "INV-52")
        self.avoir(so)                                                                                # avoir total sur le solde : nouveau solde possible
        self.assertIsNone(self.tente_f(bc, "solde", "1000.00"))

    def test_009b_aucune_exigence_d_acompte_prealable_pour_les_autres_types(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="30.00")
        self.assertIsNone(self.tente_f(bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00"))
        self.assertIsNone(self.tente_f(bc, "solde", "1000.00"))


# --------------------------------------------------------------------------------------------------------------------
# E. Garanties : déclenchement manuel, indépendant du solde et du cycle
# --------------------------------------------------------------------------------------------------------------------
class GarantiesManuelles(Base14):
    def test_009b_garantie_declenchee_sans_aucune_facture(self):
        bc = self.monde_g()
        self.assertEqual(self.tous("SELECT id FROM factures WHERE bc_id=?", bc.b), [])
        ids = [self.declenche(l_, t_) for (l_, t_) in self.attendues(bc.b)]
        self.assertEqual(len(ids), 3)
        self.assertTrue(all(r[0] is None for r in self.tous("SELECT facture_declenchement_id FROM garanties WHERE bc_id=?", bc.b)))

    def test_009b_garantie_declenchee_avant_le_solde_cycle_non_termine_factures_impayees(self):
        bc = self.monde_pa()
        self.facture(bc, "acompte", "100.00", devis_id=bc.d[0])
        self.emettre_situation(bc, {bc.lignes[0]: 3000, bc.lignes[1]: 3000})
        for (l_, t_) in self.attendues(bc.b):
            self.declenche(l_, t_)
        self.assertEqual(len(self.tous("SELECT id FROM garanties WHERE bc_id=?", bc.b)), 3)
        self.assertEqual(self.un("SELECT statut FROM bons_commande WHERE id=?", bc.b)[0], "en_cours")
        self.assertEqual(self.tous("SELECT id FROM factures WHERE bc_id=? AND type='solde'", bc.b), [])

    def test_009b_garantie_declenchee_a_une_date_libre_sans_lien_avec_une_facture(self):
        bc = self.monde_g()
        l_, t_ = self.attendues(bc.b)[0]
        self.declenche(l_, t_, date="2031-03-17")
        self.assertEqual(self.un("SELECT date_fin_suivi FROM garanties WHERE bc_ligne_id=?", l_)[0], G.fin_attendue("2031-03-17", t_))

    def test_009b_garantie_sur_bc_annule_ou_termine_n_est_pas_gardee_par_le_sql(self):
        for etat in ("annule", "termine"):
            with self.subTest(etat=etat):
                bc = self.monde_g()
                self.etat(bc, etat)
                l_, t_ = self.attendues(bc.b)[0]
                self.assertIsNone(self.tente_manuel(l_, t_))

    def test_009b_les_gardes_G1_G3_et_les_durees_sont_conservees(self):
        bc = self.monde_g()
        autre = self.monde_g()
        l_, t_ = self.attendues(bc.b)[0]
        self.assertRegex(self.tente_manuel(l_, t_, bc_id=autre.b), "INV-90")                          # G1 : ligne d'un autre BC
        absent = [t for t in G.TYPES_G if (l_, t) not in self.attendues(bc.b)][0]
        self.assertRegex(self.tente_manuel(l_, absent), "INV-86")                                    # G3 : type absent de la ligne
        self.assertNotIn("INV-", self.tente_manuel(l_, t_, date_fin_suivi="2999-01-01"))              # durée exacte (CHECK)
        self.assertIsNone(self.tente_manuel(l_, t_))

    def test_009b_une_ligne_sans_garantie_de_ligne_pour_ce_type_est_refusee(self):
        bc = self.monde_g()
        l_ = bc.lignes[0]
        sans = [t for t in G.TYPES_G if (l_, t) not in self.attendues(bc.b)]
        self.assertTrue(sans)
        self.assertRegex(self.tente_manuel(l_, sans[0]), "INV-86")

    def test_009b_unicite_et_immuabilite(self):
        bc = self.monde_g()
        l_, t_ = self.attendues(bc.b)[0]
        g = self.declenche(l_, t_)
        self.assertNotIn("INV-", self.tente_manuel(l_, t_))                                           # UNIQUE(bc_ligne_id, garantie_type)
        self.assertRegex(self.essai("UPDATE garanties SET date_declenchement=date_declenchement WHERE id=?", g), "INV-87")
        self.assertRegex(self.essai("DELETE FROM garanties WHERE id=?", g), "INV-87")
        self.assertRegex(self.essai("INSERT OR REPLACE INTO garanties (id, bc_id, bc_ligne_id, garantie_type, date_declenchement, date_fin_suivi) "
                                    "VALUES (?,?,?,?,?,?)", g, bc.b, l_, t_, D_REF, G.fin_attendue(D_REF, t_)), "INV-87")

    def test_009b_ancienne_voie_lien_vers_un_solde_reste_possible_et_gardee(self):
        bc = self.monde_g()
        s = self.solde_g(bc)
        l_, t_ = self.attendues(bc.b)[0]
        self.assertIsNone(self.tente_g(l_, t_, s))                                                    # facture = solde du BC, date = émission
        self.assertRegex(self.tente_g(l_, t_, s, date_declenchement="2026-10-06", date_fin_suivi=G.fin_attendue("2026-10-06", t_)), "INV-87")   # G4
        autre = self.monde_g()
        s2 = self.solde_g(autre)
        self.assertRegex(self.tente_g(l_, t_, s2), "INV-85")                                          # G2 : solde d'un autre BC

    def test_009b_un_avoir_total_sur_le_solde_ne_touche_pas_une_garantie(self):
        bc = self.monde_g()
        s = self.solde_g(bc)
        ids = self.creer_toutes(bc, s)
        avant = self.tous("SELECT * FROM garanties ORDER BY id")
        self.avoir(s)
        self.assertEqual(avant, self.tous("SELECT * FROM garanties ORDER BY id"))


# --------------------------------------------------------------------------------------------------------------------
# F. Périmètre contractuel : retrait ciblé d'une prestation
# --------------------------------------------------------------------------------------------------------------------
class Retraits(Base14):
    def monde_solde(self):
        bc = self.monde_g()
        s = self.solde_g(bc)
        return bc, s

    def test_009b_avoir_pour_prestation_non_realisee_sur_solde_retire_la_prestation(self):
        bc, s = self.monde_solde()
        l1, l2 = bc.lignes[0], bc.lignes[1]
        av = self.avoir_motif(s, "prestation_non_realisee", "100.00", l1)
        r = self.retrait(l1, "avoir_prestation_non_realisee", av)
        self.assertEqual(self.un("SELECT motif_retrait, avoir_id, bc_id FROM bc_ligne_retraits_garantie WHERE id=?", r), ("avoir_prestation_non_realisee", av, bc.b))

    def test_009b_l_avoir_seul_suffit_aucune_moins_value_distincte_n_est_requise(self):
        bc, s = self.monde_solde()
        av = self.avoir_motif(s, "prestation_non_realisee", "100.00", bc.lignes[0])
        self.assertIsNone(self.tente_retrait(bc.lignes[0], "avoir_prestation_non_realisee", av))
        self.assertEqual(self.tous("SELECT id FROM bc_ligne_retraits_garantie"), [])                  # (la tentative est annulée) : aucune moins-value en base

    def test_009b_un_avoir_d_erreur_ne_retire_aucune_prestation(self):
        bc, s = self.monde_solde()
        av = self.avoir_motif(s, "correction_erreur", "10.00", bc.lignes[0])
        self.retrait_ko(bc.lignes[0], "avoir_prestation_non_realisee", av, "INV-76")
        for motif in ("Erreur de facturation", "autre"):                                              # hors liste fermée : l'avoir lui-même est refusé (TR-23)
            with self.subTest(motif=motif):
                self.assertRegex(self.tente_f(bc, "avoir", "10.00", origine_facture_id=s, motif_avoir=motif), "INV-76")

    def test_009b_un_avoir_pour_prestation_non_realisee_sur_situation_ne_retire_pas_automatiquement(self):
        bc = self.monde_g()
        sit = self.emettre_situation(bc, {bc.lignes[0]: 5000, bc.lignes[1]: 5000})
        av = self.avoir_motif(sit, "prestation_non_realisee", "100.00", bc.lignes[0])
        self.retrait_ko(bc.lignes[0], "avoir_prestation_non_realisee", av, "INV-76")

    def test_009b_un_avoir_sur_acompte_ne_retire_aucune_prestation(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="50.00")
        a = self.acompte(bc, bc.d[0], "100.00")
        self.assertRegex(self.tente_f(bc, "avoir", "50.00", origine_facture_id=a, motif_avoir="prestation_non_realisee"), "INV-76")   # refusé dès l'avoir (TR-23)
        av = self.avoir_motif(a, "correction_erreur", "50.00", bc.lignes[0])                           # même avec une ligne de BC : le motif d'erreur ne retire rien
        self.retrait_ko(bc.lignes[0], "avoir_prestation_non_realisee", av, "INV-76")

    def test_009b_l_avoir_doit_designer_la_prestation_par_une_de_ses_lignes(self):
        bc, s = self.monde_solde()
        sans_ligne = self.avoir_motif(s, "prestation_non_realisee", "100.00", None)
        autre_ligne = self.avoir_motif(s, "prestation_non_realisee", "20.00", bc.lignes[1])
        self.retrait_ko(bc.lignes[0], "avoir_prestation_non_realisee", sans_ligne, "INV-76")
        self.retrait_ko(bc.lignes[0], "avoir_prestation_non_realisee", autre_ligne, "INV-76")
        self.assertIsNone(self.tente_retrait(bc.lignes[1], "avoir_prestation_non_realisee", autre_ligne))

    def test_009b_l_avoir_d_un_autre_bc_ou_une_facture_qui_n_est_pas_un_avoir_est_refuse(self):
        bc, s = self.monde_solde()
        autre, s2 = self.monde_solde()
        av2 = self.avoir_motif(s2, "prestation_non_realisee", "100.00", autre.lignes[0])
        self.retrait_ko(bc.lignes[0], "avoir_prestation_non_realisee", av2, "INV-76")
        self.retrait_ko(bc.lignes[0], "avoir_prestation_non_realisee", s, "INV-76")                    # la facture est un solde, pas un avoir

    def test_009b_moins_value_motif_sans_avoir_et_motif_avoir_sans_avoir(self):
        bc, s = self.monde_solde()
        av = self.avoir_motif(s, "prestation_non_realisee", "100.00", bc.lignes[0])
        self.assertIsNone(self.tente_retrait(bc.lignes[0], "moins_value", None))
        self.retrait_ko(bc.lignes[0], "moins_value", av, None)                                         # CHECK : une moins-value ne porte pas d'avoir
        self.retrait_ko(bc.lignes[0], "avoir_prestation_non_realisee", None, None)                     # CHECK : le motif avoir exige l'avoir
        self.retrait_ko(bc.lignes[0], "inconnu", None, None)

    def test_009b_aucun_double_retrait_d_une_meme_prestation(self):
        bc, s = self.monde_solde()
        av = self.avoir_motif(s, "prestation_non_realisee", "100.00", bc.lignes[0])
        self.retrait(bc.lignes[0], "moins_value", None)
        self.retrait_ko(bc.lignes[0], "avoir_prestation_non_realisee", av, None)                       # UNIQUE : déjà retirée par moins-value
        self.retrait_ko(bc.lignes[0], "moins_value", None, None)

    def test_009b_ligne_d_un_autre_bc_ou_inexistante_refusee(self):
        bc, s = self.monde_solde()
        autre = self.monde_g()
        self.retrait_ko(autre.lignes[0], "moins_value", None, "INV-90", bc_id=bc.b)
        self.retrait_ko(999999, "moins_value", None, "INV-90", bc_id=bc.b)

    def test_009b_une_prestation_retiree_ne_peut_plus_etre_declenchee_les_autres_oui(self):
        bc = self.monde_g()
        l1, l2 = bc.lignes[0], bc.lignes[1]
        self.retrait(l1, "moins_value", None)
        for t_ in ("decennale", "biennale"):
            self.assertRegex(self.tente_manuel(l1, t_), "INV-85")
        self.assertIsNone(self.tente_manuel(l2, "parfait_achevement"))
        self.assertNotIn("INV-", self.tente_manuel(l2, "parfait_achevement", date_fin_suivi="2999-01-01"))

    def test_009b_une_prestation_encore_contractuelle_reste_eligible_cycle_inacheve(self):
        bc = self.monde_pa()
        self.facture(bc, "acompte", "10.00", devis_id=bc.d[0])
        self.emettre_situation(bc, {bc.lignes[0]: 2000, bc.lignes[1]: 2000})
        for (l_, t_) in self.attendues(bc.b):
            self.assertIsNone(self.tente_manuel(l_, t_))                                              # aucun solde, aucun retrait : tout reste déclenchable

    def test_009b_retrait_d_une_prestation_dont_la_garantie_est_deja_declenchee_seule_cette_ligne_sort_du_suivi_actif(self):
        bc = self.monde_g()
        l1, l2 = bc.lignes[0], bc.lignes[1]
        gs = {(l_, t_): self.declenche(l_, t_) for (l_, t_) in self.attendues(bc.b)}
        avant = self.tous("SELECT * FROM garanties ORDER BY id")
        self.assertEqual(len(self.suivi_actif(bc.b)), 3)
        self.retrait(l1, "moins_value", None)
        actifs = {r[0] for r in self.suivi_actif(bc.b)}
        self.assertEqual(actifs, {gs[(l2, "parfait_achevement")]})                                     # les deux garanties de l1 sortent, celle de l2 reste
        self.assertEqual(avant, self.tous("SELECT * FROM garanties ORDER BY id"))                     # traçabilité : aucune garantie modifiée ni supprimée

    def test_009b_un_retrait_ne_modifie_aucune_garantie_des_autres_prestations_ni_des_autres_bc(self):
        bc, autre = self.monde_g(), self.monde_g()
        for b in (bc, autre):
            for (l_, t_) in self.attendues(b.b):
                self.declenche(l_, t_)
        avant = self.tous("SELECT * FROM garanties WHERE bc_id=? ORDER BY id", autre.b)
        self.retrait(bc.lignes[0], "moins_value", None)
        self.assertEqual(avant, self.tous("SELECT * FROM garanties WHERE bc_id=? ORDER BY id", autre.b))
        self.assertEqual(len(self.suivi_actif(autre.b)), 3)

    def test_009b_un_retrait_ne_se_modifie_ni_ne_se_supprime(self):
        bc = self.monde_g()
        r = self.retrait(bc.lignes[0], "moins_value", None)
        self.assertRegex(self.essai("UPDATE bc_ligne_retraits_garantie SET date_retrait=date_retrait WHERE id=?", r), "INV-87")
        self.assertRegex(self.essai("DELETE FROM bc_ligne_retraits_garantie WHERE id=?", r), "INV-87")
        self.assertRegex(self.essai("INSERT OR REPLACE INTO bc_ligne_retraits_garantie (id, bc_id, bc_ligne_id, motif_retrait, date_retrait) VALUES (?,?,?,?,?)",
                                    r, bc.b, bc.lignes[0], "moins_value", D_REF), "INV-87")

    def test_009b_la_date_de_retrait_est_une_date_reelle(self):
        bc = self.monde_g()
        for faux in ("2026-02-30", "2026-13-01", "26-01-01", "", "2026-1-1"):
            with self.subTest(date=faux):
                self.retrait_ko(bc.lignes[0], "moins_value", None, None, date_retrait=faux)


# --------------------------------------------------------------------------------------------------------------------
# G. Non-régression sur les règles inchangées
# --------------------------------------------------------------------------------------------------------------------
class NonRegression(Base14):
    def test_009b_avoir_et_immuabilite_des_factures_inchanges(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="30.00")
        a = self.acompte(bc, bc.d[0], "300.00")
        self.assertRegex(self.essai("UPDATE factures SET objet='x' WHERE id=?", a), "INV-53")
        self.assertRegex(self.essai("DELETE FROM factures WHERE id=?", a), "INV-06")
        self.assertRegex(self.tente_f(bc, "avoir", "300.01", origine_facture_id=a), "INV-76")
        self.assertIsNone(self.tente_f(bc, "avoir", "300.00", origine_facture_id=a))

    def test_009b_bc_annule_ne_recoit_ni_acompte_ni_situation_ni_solde(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="30.00")
        self.annuler_bc(bc.b)
        self.acompte_ko(bc, "100.00", inv="INV-188")
        self.assertRegex(self.tente_f(bc, "solde", "1000.00"), "INV-188")

    def test_009b_nettes_negatives_ou_acompte_sans_devis_toujours_refuses_par_les_contraintes(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="30.00")
        self.assertIsNotNone(self.tente_f(bc, "acompte", "100.00", devis_id=OMIT))
        self.assertNotIn("INV-", self.tente_f(bc, "acompte", "0.00", devis_id=bc.d[0]))


# --------------------------------------------------------------------------------------------------------------------
# K. Avoirs : motif en liste fermée (TR-23, INV-76) — comportement de la chaîne complète
# --------------------------------------------------------------------------------------------------------------------
class AvoirsMotifs(Base14):
    def test_009b_les_deux_motifs_de_la_liste_fermee_sont_acceptes_sur_situation_et_sur_solde(self):
        bc = self.monde_g()
        sit = self.emettre_situation(bc, {bc.lignes[0]: 5000, bc.lignes[1]: 5000})
        for origine in (sit,):
            for motif in ("correction_erreur", "prestation_non_realisee"):
                self.assertIsNone(self.tente_f(bc, "avoir", "10.00", origine_facture_id=origine, motif_avoir=motif), motif)
        s = self.solde_final(bc)
        for motif in ("correction_erreur", "prestation_non_realisee"):
            self.assertIsNone(self.tente_f(bc, "avoir", "10.00", origine_facture_id=s, motif_avoir=motif), motif)

    def test_009b_un_motif_hors_liste_est_refuse_par_la_base(self):
        bc = self.monde_g()
        s = self.solde_final(bc)
        for motif in ("Erreur de facturation", "autre", "x", "CORRECTION_ERREUR", " correction_erreur", "prestations_non_realisees", "prestation non realisee", ""):
            with self.subTest(motif=motif):
                m = self.tente_f(bc, "avoir", "10.00", origine_facture_id=s, motif_avoir=motif)
                self.assertIsNotNone(m)
                self.assertRegex(m, "INV-76")

    def test_009b_un_motif_absent_reste_refuse_par_le_CHECK(self):
        bc = self.monde_g()
        s = self.solde_final(bc)
        m = self.tente_f(bc, "avoir", "10.00", origine_facture_id=s, motif_avoir=None)
        self.assertIsNotNone(m)
        self.assertNotIn("INV-", m)

    def test_009b_un_avoir_sur_acompte_ne_corrige_qu_une_erreur(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="50.00")
        a = self.acompte(bc, bc.d[0], "400.00")
        self.assertRegex(self.tente_f(bc, "avoir", "100.00", origine_facture_id=a, motif_avoir="prestation_non_realisee"), "INV-76")
        self.assertIsNone(self.tente_f(bc, "avoir", "100.00", origine_facture_id=a, motif_avoir="correction_erreur"))
        self.avoir(a)                                                                                 # avoir total d'erreur : un nouvel acompte redevient possible
        self.acompte_ok(bc, "500.00")

    def test_009b_les_regles_anterieures_de_l_avoir_sont_conservees(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="30.00")
        a = self.acompte(bc, bc.d[0], "300.00")
        av = self.avoir(a, "100.00")
        self.assertRegex(self.tente_f(bc, "avoir", "100.00", origine_facture_id=av), "INV-76")        # l'origine n'est pas un avoir
        self.assertRegex(self.tente_f(bc, "avoir", "200.01", origine_facture_id=a), "INV-76")         # Σ avoirs <= origine
        autre = self.monde_a(acompte_type="pourcentage", acompte_valeur="30.00")
        self.assertRegex(self.tente_f(autre, "avoir", "10.00", origine_facture_id=a), "INV-76")       # même bon de commande

    def test_009b_un_avoir_historique_au_motif_libre_est_conserve_et_compte_comme_une_correction(self):
        t = P.Base12()
        t.db = migrer13()
        t._n = 0
        t._npv = {}
        t.desynchroniser_ids()
        bc = t.monde_g()
        s = t.solde_g(bc)
        av = t.avoir(s)                                                                               # 006 : motif libre « Erreur de facturation »
        self.assertEqual(t.un("SELECT motif_avoir FROM factures WHERE id=?", av)[0], "Erreur de facturation")
        T.runner(t.db, RANG, SQL_009B)
        self.assertEqual(t.un("SELECT motif_avoir, total_ht FROM factures WHERE id=?", av), ("Erreur de facturation", t.eur_solde(s)))
        u = Base14._sur(t.db)
        self.assertIsNone(u.tente_f(bc, "solde", t.eur_solde(s), date_emission="2026-10-06"))         # non compté comme prestation non réalisée : refacturable


# --------------------------------------------------------------------------------------------------------------------
# L. Contractuel final : les avoirs « prestation_non_realisee » sur solde ne sont pas refacturables (INV-58)
# --------------------------------------------------------------------------------------------------------------------
class ContractuelFinal(Base14):
    def test_009b_avoir_total_pour_prestations_non_realisees_sur_le_solde_aucun_nouveau_solde(self):
        bc = self.monde_a(acompte_type="aucun")
        s = self.solde_final(bc)
        self.avoir_motif(s, "prestation_non_realisee", "1000.00", bc.lignes[0])
        self.assertEqual(self.contractuel_final(bc), c("0.00"))
        self.assertRegex(self.tente_f(bc, "solde", "1000.00"), "INV-58")
        self.assertRegex(self.tente_f(bc, "solde", "0.01"), "INV-58")
        self.assertRegex(self.tente_f(bc, "solde", "0.00"), "INV-55")

    def test_009b_avoir_total_d_erreur_sur_le_solde_nouveau_solde_au_montant_complet(self):
        bc = self.monde_a(acompte_type="aucun")
        s = self.solde_final(bc)
        self.avoir_motif(s, "correction_erreur", "1000.00")
        self.assertIsNone(self.tente_f(bc, "solde", "1000.00"))
        self.assertRegex(self.tente_f(bc, "solde", "999.99"), "INV-58")

    def test_009b_avoir_mixte_seule_la_part_correction_est_refacturable(self):
        bc = self.monde_a(acompte_type="aucun")
        s = self.solde_final(bc)
        self.avoir_motif(s, "prestation_non_realisee", "600.00", bc.lignes[0])
        self.assertRegex(self.tente_f(bc, "solde", "400.00"), "INV-52")                                # le solde reste actif tant qu'il n'est pas totalement crédité
        self.avoir_motif(s, "correction_erreur", "400.00")
        self.assertIsNone(self.tente_f(bc, "solde", "400.00"))
        self.assertRegex(self.tente_f(bc, "solde", "1000.00"), "INV-58")
        self.assertRegex(self.tente_f(bc, "solde", "399.99"), "INV-58")

    def test_009b_un_avoir_partiel_sur_le_solde_ne_rouvre_pas_la_facturation(self):
        bc = self.monde_a(acompte_type="aucun")
        s = self.solde_final(bc)
        for motif in ("prestation_non_realisee", "correction_erreur"):
            self.avoir_motif(s, motif, "100.00", bc.lignes[0] if motif == "prestation_non_realisee" else None)
        self.assertRegex(self.tente_f(bc, "solde", "100.00"), "INV-52")
        self.assertRegex(self.tente_f(bc, "acompte", "1.00", devis_id=bc.d[0]), "INV-58")
        self.assertRegex(self.tente_f(bc, "situation", "1.00", situation_numero=1, montant_deja_facture_ht=eur(self.nette(bc))), "INV-58")

    def test_009b_un_avoir_pour_prestations_non_realisees_sur_situation_ne_reduit_pas_le_contractuel(self):
        bc = self.monde_a(acompte_type="aucun")
        sit = self.facture(bc, "situation", "500.00", situation_numero=1, montant_deja_facture_ht="0.00")
        self.avoir_motif(sit, "prestation_non_realisee", "200.00", bc.lignes[0])
        self.assertEqual(self.contractuel_final(bc), c("1000.00"))
        self.assertEqual(self.nette(bc), c("300.00"))
        self.assertRegex(self.tente_f(bc, "solde", "500.00"), "INV-58")
        self.assertIsNone(self.tente_f(bc, "solde", "700.00"))

    def test_009b_avec_acompte_et_situation_le_contractuel_final_n_entre_que_par_le_solde(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="30.00")
        self.acompte(bc, bc.d[0], "300.00")
        self.facture(bc, "situation", "200.00", situation_numero=1, montant_deja_facture_ht="300.00")
        s = self.solde_final(bc)
        self.assertEqual(self.eur_solde(s), "500.00")
        self.avoir_motif(s, "prestation_non_realisee", "500.00", bc.lignes[0])
        self.assertRegex(self.tente_f(bc, "solde", "500.00"), "INV-58")
        self.assertRegex(self.tente_f(bc, "solde", "0.00"), "INV-55")

    def test_009b_les_sommes_non_realisees_restent_deduites_d_un_solde_a_l_autre(self):
        bc = self.monde_a(acompte_type="aucun")
        s1 = self.solde_final(bc)
        self.avoir_motif(s1, "prestation_non_realisee", "300.00", bc.lignes[0])
        self.avoir_motif(s1, "correction_erreur", "700.00")
        s2 = self.solde_final(bc, date="2026-10-06")
        self.assertEqual(self.eur_solde(s2), "700.00")
        self.avoir_motif(s2, "correction_erreur", "700.00", date_emission="2026-10-07")
        self.assertEqual(self.contractuel_final(bc), c("700.00"))
        self.assertIsNone(self.tente_f(bc, "solde", "700.00", date_emission="2026-10-08"))
        self.assertRegex(self.tente_f(bc, "solde", "1000.00", date_emission="2026-10-08"), "INV-58")

    def test_009b_un_solde_conforme_au_contractuel_accepte_est_refuse_si_une_reduction_etait_acceptee_a_concevoir(self):
        """Documente la limite assumée : le contractuel COURANT (réductions acceptées) n'a pas de stockage (À CONCEVOIR) ; le SQL lit le montant ACCEPTÉ.
        Un solde calculé par le service avec une réduction (accepté − réduction − nette) est donc refusé tant que le stockage n'existe pas."""
        bc = self.monde_a(acompte_type="aucun")
        self.assertRegex(self.tente_f(bc, "solde", "900.00"), "INV-58")                                # 1000 accepté − réduction 100 : non représentable en base
        self.assertIsNone(self.tente_f(bc, "solde", "1000.00"))


# --------------------------------------------------------------------------------------------------------------------
# M. Ordre des factures et acompte (décisions du 2026-10-17) — chaîne complète
# --------------------------------------------------------------------------------------------------------------------
class OrdreDesFactures(Base14):
    """Règles (V3.14) : aucun acompte sur un devis couvert par une situation (INV-205), ni après un solde ; acompte ≤ acompte prévu du devis accepté ; acompte facultatif ; un acompte prévu à
    100 % et entièrement facturé ne clôture pas le cycle ; aucun solde à 0.00 ; AUCUNE règle de cumul supplémentaire sur l'acompte."""

    def test_009b_aucun_acompte_apres_une_situation(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="50.00")
        self.situation(bc, "100.00", 1, "0.00")
        m = self.tente_f(bc, "acompte", "100.00", devis_id=bc.d[0])
        self.assertRegex(m, "INV-205.*couvert")
        self.assertRegex(self.tente_f(bc, "acompte", "0.01", devis_id=bc.d[0]), "INV-205.*couvert")

    def test_009b_aucun_acompte_apres_un_solde_regle_de_006_conservee(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="50.00")
        self.solde_final(bc)
        self.assertRegex(self.tente_f(bc, "acompte", "100.00", devis_id=bc.d[0]), "INV-58.*solde")

    def test_009b_acompte_puis_situation_puis_solde_ordre_nominal_accepte(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="50.00")
        self.acompte(bc, bc.d[0], "500.00")
        self.facture(bc, "situation", "300.00", situation_numero=1, montant_deja_facture_ht="500.00")
        self.assertEqual(self.eur_solde(self.solde_final(bc)), "200.00")

    def test_009b_l_acompte_est_facultatif_les_situations_commencent_sans_acompte(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="30.00")                         # un acompte est prévu, jamais exigé
        self.assertIsNone(self.tente_f(bc, "situation", "100.00", situation_numero=1, montant_deja_facture_ht="0.00"))

    def test_009b_une_situation_deja_creditee_reste_une_situation_emise_pour_l_ordre(self):
        """INTERPRETATION : « émise » = existante ; un avoir ne fait pas disparaître la situation (les factures sont immuables)."""
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="50.00")
        s = self.situation(bc, "100.00", 1, "0.00")
        self.facture(bc, "avoir", "100.00", origine_facture_id=s)
        self.assertEqual(self.couverture(s), [bc.d[0]])                                                 # la couverture survit à l'avoir total
        self.assertRegex(self.tente_f(bc, "acompte", "100.00", devis_id=bc.d[0]), "INV-205.*couvert")

    def test_009b_le_plafond_de_l_acompte_prevu_est_conserve(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="30.00")
        self.acompte_ok(bc, "300.00")
        self.acompte_ko(bc, "300.01")
        sans = self.monde_a(acompte_type="aucun")
        self.acompte_ko(sans, "0.01")

    def test_009b_acompte_prevu_inferieur_a_100_les_acomptes_seuls_ne_peuvent_pas_atteindre_100(self):
        """Conséquence arithmétique du plafond, de l'acompte unique par devis (INV-52) et de l'ordre (aucun acompte après situation) : aucune règle de cumul
        n'est nécessaire, et aucune n'est ajoutée."""
        bc = self.monde_devis([("1000.00", "pourcentage", "50.00"), ("1000.00", "pourcentage", "50.00")])
        self.acompte(bc, bc.d[0], "500.00")
        self.acompte(bc, bc.d[1], "500.00")
        self.assertEqual(self.nette(bc), c("1000.00"))
        self.assertLess(self.nette(bc), self.contractuel(bc))

    def test_009b_acompte_prevu_100_toute_la_facturation_peut_passer_par_l_acompte_sans_confirmation_ni_cloture_automatique(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="100.00")
        a = self.acompte(bc, bc.d[0], "1000.00")
        self.assertEqual(self.nette(bc), self.contractuel(bc))
        self.assertEqual(self.tous("SELECT id FROM factures WHERE bc_id=? AND type='solde'", bc.b), [])
        self.assertEqual(self.un("SELECT statut, date_100_facture FROM bons_commande WHERE id=?", bc.b), ("en_cours", None))
        self.assertRegex(self.tente_f(bc, "solde", "0.00"), "INV-55")                                  # aucun solde à 0 €
        self.assertRegex(self.tente_f(bc, "solde", "0.01"), "INV-58")
        self.assertRegex(self.tente_f(bc, "situation", "0.01", situation_numero=1, montant_deja_facture_ht="1000.00"), "INV-57")
        self.assertIsNone(self.tente_f(bc, "avoir", "100.00", origine_facture_id=a))                   # une correction reste possible

    def test_009b_acompte_prevu_100_sur_deux_devis_l_acompte_cumule_a_100_est_admis_sans_cloture(self):
        bc = self.monde_devis([("1000.00", "pourcentage", "100.00"), ("1000.00", "pourcentage", "100.00")])
        self.acompte(bc, bc.d[0], "1000.00")
        self.acompte(bc, bc.d[1], "1000.00")
        self.assertEqual(self.nette(bc), self.contractuel(bc))
        self.assertRegex(self.tente_f(bc, "solde", "0.00"), "INV-55")

    # --- ordre apprécié PAR DEVIS (règle validée le 2026-10-17) ------------------------------------------------------------------
    def test_009b_cas1_acompte_refuse_sur_un_devis_ayant_deja_une_situation(self):
        # deux devis rattachés AVANT la situation : la situation (globale au BC) couvre les deux, l'acompte est refusé sur chacun
        bc = self.monde_devis([("1000.00", "pourcentage", "100.00"), ("1000.00", "pourcentage", "100.00")])
        s = self.situation(bc, "1000.00", 1, "0.00")
        self.assertEqual(self.couverture(s), sorted(bc.d))
        self.assertRegex(self.tente_f(bc, "acompte", "1000.00", devis_id=bc.d[0]), "INV-205.*couvert")
        self.assertRegex(self.tente_f(bc, "acompte", "1000.00", devis_id=bc.d[1]), "INV-205.*couvert")

    def test_009b_cas1_le_second_devis_redevient_refuse_des_qu_une_situation_est_emise_apres_son_rattachement(self):
        bc, d1, d2 = self.monde_apres_situation()
        self.assertIsNone(self.tente_acompte(bc, d2, "400.00"))                                       # avant la seconde situation : permis
        s2 = self.situation(bc, "100.00", 2, "100.00", created_at=self.SITUATION_2)
        self.assertEqual(self.couverture(s2), sorted([d1, d2]))
        self.assertRegex(self.tente_acompte(bc, d2, "400.00"), "INV-205.*couvert")                   # la situation 2 couvre d2 : plus d'acompte sur d2
        self.assertRegex(self.tente_acompte(bc, d1, "100.00"), "INV-205.*couvert")

    def test_009b_cas1_la_regle_ne_depend_d_aucun_horodatage_ni_ex_aequo_ni_ordre_inverse(self):
        """V3.14 : la couverture est enregistrée, jamais déduite de created_at. Même horodatage que le lien, ou situation « antérieure » au rattachement
        selon l'horloge : le résultat ne dépend que de situation_devis."""
        bc = self.monde_devis([("1000.00", "pourcentage", "100.00")])
        s = self.situation(bc, "100.00", 1, "0.00", created_at=self.LIEN_D2)
        d2 = self.devis_accepte_a(bc, "800.00", "pourcentage", "50.00")
        self.rattacher_a(bc, d2, ts=self.LIEN_D2)                                                      # lien et situation au même instant
        self.assertEqual(self.couverture(s), [bc.d[0]])
        self.assertIsNone(self.tente_acompte(bc, d2, "400.00"))                                       # d2 n'est pas couvert (plus d'ex æquo « réputé couvert »)
        self.assertRegex(self.tente_acompte(bc, bc.d[0], "100.00"), "INV-205")

    def test_009b_cas2_acompte_autorise_sur_un_second_devis_du_meme_bc_sans_situation_sur_ce_devis(self):
        bc, d1, d2 = self.monde_apres_situation()
        # le premier devis est bloqué par sa situation, pas le second
        self.assertRegex(self.tente_acompte(bc, d1, "100.00"), "INV-205.*couvert")
        self.assertIsNone(self.tente_acompte(bc, d2, "400.00"))
        f = self.acompte_d2(bc, d2, "400.00")
        self.assertEqual(self.un("SELECT type, bc_id, devis_id, total_ht FROM factures WHERE id=?", f), ("acompte", bc.b, d2, "400.00"))
        self.assertEqual(self.nette(bc), c("500.00"))                                                 # situation de d1 (100.00) + acompte de d2 (400.00)

    def test_009b_cas2_l_historique_de_facturation_du_premier_devis_ne_bloque_pas_le_second(self):
        # plusieurs situations, un avoir sur la situation du premier devis : le second devis, rattaché ensuite, n'est pas bloqué
        bc = self.monde_devis([("1000.00", "pourcentage", "100.00")])
        s1 = self.situation(bc, "100.00", 1, "0.00")
        self.situation(bc, "100.00", 2, "100.00")
        self.avoir_motif(s1, "correction_erreur")
        d2 = self.devis_accepte_a(bc, "800.00", "pourcentage", "50.00")
        self.rattacher_a(bc, d2)
        self.assertIsNone(self.tente_acompte(bc, d2, "400.00"))

    def test_009b_cas3_l_acompte_du_second_devis_reference_exclusivement_ce_devis(self):
        bc, d1, d2 = self.monde_apres_situation()
        avant_d1 = self.tous("SELECT * FROM factures WHERE bc_id=? AND type='situation'", bc.b)
        f = self.acompte_d2(bc, d2, "400.00")
        self.assertEqual(self.un("SELECT devis_id FROM factures WHERE id=?", f)[0], d2)
        self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE devis_id=?", d1)[0], 0)           # aucune facture d'acompte imputée au premier devis
        self.assertEqual(self.tous("SELECT * FROM factures WHERE bc_id=? AND type='situation'", bc.b), avant_d1)   # la situation du premier devis est intacte
        self.assertEqual(self.tous("SELECT bc_ligne_id FROM facture_lignes WHERE facture_id=? AND bc_ligne_id IS NOT NULL", f), [])   # aucune ligne de BC imputée
        self.assertEqual(self.un("SELECT COUNT(*) FROM factures WHERE devis_id IS NOT NULL AND bc_id=?", bc.b)[0], 1)
        # le premier devis reste sans acompte possible (situation) ; le second n'en admet qu'un (INV-52)
        self.assertRegex(self.tente_acompte(bc, d1, "10.00"), "INV-205.*couvert")
        self.assertRegex(self.tente_acompte(bc, d2, "1.00"), "INV-52")
        # un acompte ne se rattache qu'à un devis du BC de la facture (INV-189)
        autre = self.monde_devis([("500.00", "pourcentage", "100.00")])
        self.assertRegex(self.tente_acompte(bc, autre.d[0], "10.00"), "INV-189")

    def test_009b_cas4_le_plafond_est_controle_independamment_pour_chaque_devis_apres_une_situation(self):
        # d1 prévoit 100 % (1000.00), d2 prévoit 50 % de 800.00 = 400.00 : le plafond de d2 n'est ni celui de d1 ni celui du BC
        bc, d1, d2 = self.monde_apres_situation()
        self.assertRegex(self.tente_acompte(bc, d2, "400.01"), "INV-57")
        self.assertIsNone(self.tente_acompte(bc, d2, "400.00"))
        bc2, e1, e2 = self.monde_apres_situation(type2="montant", val2="200.00")                   # plafond en montant
        self.assertRegex(self.tente_acompte(bc2, e2, "200.01"), "INV-57")
        self.assertIsNone(self.tente_acompte(bc2, e2, "200.00"))
        bc3, f1, f2 = self.monde_apres_situation(type2="aucun", val2=None)                         # aucun acompte prévu sur d2 malgré 100 % sur d1
        self.assertRegex(self.tente_acompte(bc3, f2, "0.01"), "INV-57")

    def test_009b_cas4_plafonds_independants_de_deux_devis_sans_situation(self):
        bc = self.monde_devis([("1000.00", "pourcentage", "50.00"), ("1000.00", "montant", "300.00")])
        self.assertRegex(self.tente_f(bc, "acompte", "500.01", devis_id=bc.d[0]), "INV-57")
        self.assertRegex(self.tente_f(bc, "acompte", "300.01", devis_id=bc.d[1]), "INV-57")
        self.acompte(bc, bc.d[0], "500.00")                                                          # l'acompte de d1 n'entame pas le plafond de d2
        self.assertIsNone(self.tente_f(bc, "acompte", "300.00", devis_id=bc.d[1]))
        self.acompte(bc, bc.d[1], "300.00")
        self.assertEqual(self.nette(bc), c("800.00"))

    def test_009b_cas5_les_regles_existantes_d_unicite_et_de_plafond_sont_maintenues(self):
        bc, d1, d2 = self.monde_apres_situation()
        a = self.acompte_d2(bc, d2, "300.00")
        self.assertRegex(self.tente_acompte(bc, d2, "100.00"), "INV-52")                             # un seul acompte actif par devis
        self.avoir_motif(a, "correction_erreur", created_at=self.ACOMPTE_D2)
        self.assertIsNone(self.tente_acompte(bc, d2, "400.00"))                                      # acompte crédité : un nouvel acompte est possible
        self.assertRegex(self.tente_acompte(bc, d2, "400.01"), "INV-57")                             # plafond maintenu
        # la facturation nette reste bornée par le contractuel du BC (INV-57) : un acompte de 400.00 sur d2 dépasse le contractuel lorsque la nette le consomme
        self.acompte_d2(bc, d2, "400.00")
        self.assertEqual(self.nette(bc), c("500.00"))                                                 # situation 100.00 + acompte 400.00 (300.00 crédité)
        self.assertLess(self.nette(bc), self.contractuel(bc))
        self.assertRegex(self.tente_f(bc, "solde", "0.00"), "INV-55")

    def test_009b_seul_un_solde_valide_cloture_acompte_puis_situation_puis_solde_positif(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="50.00")
        self.acompte(bc, bc.d[0], "500.00")
        self.facture(bc, "situation", "499.00", situation_numero=1, montant_deja_facture_ht="500.00")
        self.assertRegex(self.tente_f(bc, "solde", "0.00"), "INV-55")
        s = self.solde_final(bc)
        self.assertEqual(self.eur_solde(s), "1.00")                                                   # solde valide, strictement positif
        self.assertEqual(self.nette(bc), c("1000.00"))
        d2 = self.monde_a(acompte_type="aucun").d[0]
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INV-187"):
            self.rattacher(bc.b, d2)                                                                  # le solde clôture le cycle : plus de devis

    def test_009b_l_acompte_facultatif_n_est_jamais_exige_pour_cloturer(self):
        bc = self.monde_a(acompte_type="pourcentage", acompte_valeur="100.00")
        self.assertIsNone(self.tente_f(bc, "solde", "1000.00"))                                       # clôture directe par le solde, sans acompte
        s = self.solde_final(bc)
        self.assertEqual(self.eur_solde(s), "1000.00")

    def test_009b_aucune_regle_de_cumul_supplementaire_sur_l_acompte_dans_le_trigger(self):
        """Le trigger de l'acompte ne porte que les contrôles validés : rattachement, ordre (solde ; devis couvert par une situation), acompte unique, plafond du devis prévu,
        total du devis, facturation nette ≤ contractuel. Aucune garde de « clôture du cycle » ni de cumul à 100 %."""
        sql = self.un("SELECT sql FROM sqlite_master WHERE type='trigger' AND name='tr_22_factures_acompte'")[0]
        import re
        messages = re.findall(r"RAISE\(ABORT, '((?:[^']|'')*)'\)", sql)
        self.assertEqual([m.split(":")[0] for m in messages], ["INV-189", "INV-58", "INV-205", "INV-52", "INV-57", "INV-57", "INV-57"])
        self.assertNotIn("cloture", sql.lower())
        self.assertNotIn("clôture", sql.lower())


# --------------------------------------------------------------------------------------------------------------------
# N. Suivi actif des garanties — vue v_garanties_suivi_actif (décisions 3.3 et 3.4)
# --------------------------------------------------------------------------------------------------------------------
class SuiviActif(Base14):
    def test_009b_la_vue_est_la_garantie_sans_retrait_de_sa_prestation(self):
        bc = self.monde_g()
        for (l_, t_) in self.attendues(bc.b):
            self.declenche(l_, t_)
        cols = [r[1] for r in self.tous("PRAGMA table_info(v_garanties_suivi_actif)")]
        self.assertEqual(cols, COLONNES_GARANTIES)
        self.assertEqual(self.tous("SELECT * FROM v_garanties_suivi_actif ORDER BY id"), self.tous("SELECT * FROM garanties ORDER BY id"))
        self.retrait(bc.lignes[0], "moins_value", None)
        attendu = self.tous("SELECT * FROM garanties WHERE bc_ligne_id <> ? ORDER BY id", bc.lignes[0])
        self.assertEqual(self.tous("SELECT * FROM v_garanties_suivi_actif ORDER BY id"), attendu)
        self.assertTrue(attendu)

    def test_009b_seule_la_prestation_retiree_sort_du_suivi_actif_ses_garanties_restent_dans_l_historique(self):
        bc = self.monde_g()
        for (l_, t_) in self.attendues(bc.b):
            self.declenche(l_, t_)
        avant = self.tous("SELECT * FROM garanties ORDER BY id")
        self.retrait(bc.lignes[1], "moins_value", None)
        self.assertEqual(avant, self.tous("SELECT * FROM garanties ORDER BY id"))                    # aucune garantie modifiée ni supprimée
        actifs = {r[0] for r in self.suivi_actif(bc.b)}
        self.assertEqual(actifs, {r[0] for r in avant if r[2] == bc.lignes[0]})
        self.assertTrue(all(r[0] not in actifs for r in avant if r[2] == bc.lignes[1]))

    def test_009b_un_retrait_ne_touche_pas_le_suivi_d_un_autre_bc(self):
        bc, autre = self.monde_g(), self.monde_g()
        for b in (bc, autre):
            for (l_, t_) in self.attendues(b.b):
                self.declenche(l_, t_)
        n_autre = len(self.suivi_actif(autre.b))
        for l_ in bc.lignes:
            self.retrait(l_, "moins_value", None)
        self.assertEqual(self.suivi_actif(bc.b), [])
        self.assertEqual(len(self.suivi_actif(autre.b)), n_autre)

    def test_009b_une_operation_non_validee_ne_modifie_pas_le_suivi(self):
        bc = self.monde_g()
        for (l_, t_) in self.attendues(bc.b):
            self.declenche(l_, t_)
        avant = self.suivi_actif(bc.b)
        s = self.solde_final(bc)
        self.db.execute("SAVEPOINT op")                                                                 # opération du service annulée avant validation
        av = self.avoir_motif(s, "prestation_non_realisee", "100.00", bc.lignes[0])
        self.retrait(bc.lignes[0], "avoir_prestation_non_realisee", av)
        self.db.execute("ROLLBACK TO op")
        self.db.execute("RELEASE op")
        self.assertEqual(self.suivi_actif(bc.b), avant)
        self.assertEqual(self.tous("SELECT id FROM bc_ligne_retraits_garantie"), [])

    def test_009b_un_retrait_par_avoir_ne_peut_exister_sans_avoir_valide(self):
        bc, s = self.monde_g(), None
        s = self.solde_final(bc)
        self.retrait_ko(bc.lignes[0], "avoir_prestation_non_realisee", None, "")                      # le CHECK exige l'avoir
        self.assertIsNotNone(self.tente_retrait(bc.lignes[0], "avoir_prestation_non_realisee", s))

    def test_009b_la_vue_est_en_lecture_seule(self):
        for sql in ("INSERT INTO v_garanties_suivi_actif (bc_id) VALUES (1)", "DELETE FROM v_garanties_suivi_actif", "UPDATE v_garanties_suivi_actif SET bc_id = 1"):
            with self.subTest(sql=sql):
                with self.assertRaisesRegex(sqlite3.OperationalError, "view"):
                    self.db.execute(sql)


if __name__ == "__main__":
    unittest.main()
