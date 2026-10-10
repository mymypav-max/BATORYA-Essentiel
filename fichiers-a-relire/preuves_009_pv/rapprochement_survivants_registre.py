#!/usr/bin/env python3
"""Rapproche MÉCANIQUEMENT les survivants d'une campagne de mutation 009 du registre S01-Snn de preuves_equivalence_009.py.

Usage : python3 -B rapprochement_survivants_registre.py RACINE_DEPOT [mut009b.py [survivors009.txt [survivors_sans_A.txt survivors_sans_A_ni_temoin_K.txt]]]
  RACINE_DEPOT : dossier contenant src-tauri/ (obligatoire).
  Valeurs par défaut, déduites de l'arborescence livrée sous fichiers-a-relire/preuves_009_pv/ (les quatre autres arguments sont facultatifs) :
    mut009b.py                          = ../campagne_mutation/mut009b.py
    survivors009.txt                    = ../../sorties_brutes/campagne_complete/survivants_campagne_complete.txt
    survivors_sans_A.txt                = ../../sorties_brutes/passes_diagnostic/survivants_passe_sans_A.txt
    survivors_sans_A_ni_temoin_K.txt    = ../../sorties_brutes/passes_diagnostic/survivants_passe_sans_A_ni_temoin_K.txt
  Dépendance : preuves_equivalence_009.py, dans le MÊME dossier que ce script (sous ce nom exact).
  - regénère les mutants avec l'outil de campagne (mêmes opérateurs, SQL du dépôt) ;
  - lit les noms des survivants dans le fichier produit par la campagne (lignes « ### nom ») ;
  - reconstruit le SQL de chaque entrée du registre (substitution textuelle sur le SQL du dépôt) ;
  - exige une BIJECTION : chaque survivant de la campagne a exactement une entrée de registre dont le SQL muté est IDENTIQUE octet pour octet, et inversement.
Ce que cela ferme : « les preuves portent bien sur les survivants de la campagne, et sur eux seuls ». Ce que cela ne ferme pas : que la campagne elle-même soit complète.
Code de sortie : 0 = BIJECTION OK ; 1 = ECHEC ; 2 = fichier ou argument manquant (message explicite)."""
import pathlib, re, sys
sys.dont_write_bytecode = True
ICI = pathlib.Path(__file__).resolve().parent
SORTIES = ICI.parent.parent / "sorties_brutes"
def _manque(msg):
    print("ERREUR D'ENVIRONNEMENT :", msg, file=sys.stderr)
    raise SystemExit(2)
args = sys.argv[1:]
if not args or len(args) > 5 or len(args) == 4:
    _manque("usage : rapprochement_survivants_registre.py RACINE_DEPOT [mut009b.py [survivors009.txt [survivors_sans_A.txt survivors_sans_A_ni_temoin_K.txt]]]")
racine = pathlib.Path(args[0]).resolve()
outil = pathlib.Path(args[1]).resolve() if len(args) > 1 else (ICI.parent / "campagne_mutation" / "mut009b.py")
surv = pathlib.Path(args[2]).resolve() if len(args) > 2 else (SORTIES / "campagne_complete" / "survivants_campagne_complete.txt")
if len(args) == 5:
    extra = [pathlib.Path(args[3]).resolve(), pathlib.Path(args[4]).resolve()]
elif len(args) == 1:
    extra = [SORTIES / "passes_diagnostic" / "survivants_passe_sans_A.txt", SORTIES / "passes_diagnostic" / "survivants_passe_sans_A_ni_temoin_K.txt"]
else:
    extra = []
PREUVES = ICI / "preuves_equivalence_009.py"
for f, nom in [(PREUVES, "script de preuve (doit être à côté de ce script)"), (outil, "outil de campagne mut009b.py"), (surv, "fichier des survivants"), (racine / "src-tauri/migrations/metier/009_pv.sql", "009_pv.sql du dépôt")] + [(e, "fichier de survivants d'une passe de contrôle") for e in extra]:
    if not f.is_file():
        _manque(f"{nom} introuvable : {f}")
preuves = PREUVES.read_text(encoding="utf-8")
# 1. le registre, tel que défini dans le script de preuve (partie qui précède les outils de calcul)
g = {"__file__": str(PREUVES), "__name__": "registre"}
old = sys.argv
sys.argv = ["preuves", str(racine)]
exec(compile(preuves[:preuves.index("# ------------------------------------------------------------------------------------------------------------------ OUTILS")], "registre", "exec"), g)
sys.argv = old
SQL, REGISTRE, REGISTRE_KT, muter = g["SQL"], g["REGISTRE"], g["REGISTRE_KT"], g["muter"]
reg = {sid: muter(SQL, a, n) for sid, _f, a, n in REGISTRE}
# 2. les mutants de la campagne
src = outil.read_text(encoding="utf-8")
src = src[:src.index("NW = 2")]
sys.argv = ["mut", str(racine), "/nonexistent"]
h = {"__name__": "gen"}
exec(compile(src, "campagne", "exec"), h)
sys.argv = old
camp = dict(h["uniq"])
assert h["orig"] == SQL, "le SQL lu par la campagne n'est pas celui du registre"
noms = [l[4:].rstrip() for l in surv.read_text(encoding="utf-8").splitlines() if l.startswith("### ")]
ok = True
par_texte = {}
for sid, t in reg.items():
    par_texte.setdefault(t, []).append(sid)
for n in noms:
    sids = par_texte.get(camp[n], [])
    print(("OK   " if len(sids) == 1 else "ECHEC"), f"{n:48s} -> {sids}")
    ok &= len(sids) == 1
vus = [par_texte[camp[n]][0] for n in noms if len(par_texte.get(camp[n], [])) == 1]
manque = sorted(set(reg) - set(vus))
doublons = sorted({x for x in vus if vus.count(x) > 1})
print(f"survivants de la campagne : {len(noms)} ; entrées du registre : {len(reg)} ; entrées sans survivant : {manque} ; entrées en doublon : {doublons}")
ok &= not manque and not doublons and len(noms) == len(reg)
if len(extra) == 2:
    lire = lambda f: [l[4:].rstrip() for l in f.read_text(encoding="utf-8").splitlines() if l.startswith("### ")]
    kt = sorted(set(lire(extra[1])) - set(lire(extra[0])))
    regk = {sid: muter(SQL, a, n) for sid, _f, a, n in REGISTRE_KT}
    par_k = {}
    for sid, t in regk.items():
        par_k.setdefault(t, []).append(sid)
    print("\nMutants tués seulement par le test témoin de texte (survivants de la passe « sans A ni témoin K » absents de la passe « sans A ») :")
    for n in kt:
        sids = par_k.get(camp[n], [])
        print(("OK   " if len(sids) == 1 else "ECHEC"), f"{n:62s} -> {sids}")
        ok &= len(sids) == 1
    vk = [par_k[camp[n]][0] for n in kt if len(par_k.get(camp[n], [])) == 1]
    mk = sorted(set(regk) - set(vk))
    print(f"mutants K de la campagne : {len(kt)} ; entrées K du registre : {len(regk)} ; entrées sans mutant : {mk}")
    ok &= not mk and len(kt) == len(regk) and len(set(vk)) == len(vk)
print("BIJECTION OK" if ok else "ECHEC")
raise SystemExit(0 if ok else 1)
