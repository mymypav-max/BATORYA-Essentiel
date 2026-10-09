#!/usr/bin/env python3
"""Rapproche MÉCANIQUEMENT les survivants d'une campagne de mutation 009 du registre S01-Snn de preuves_equivalence_009.py.

Usage : python3 -B rapprochement_survivants_registre.py RACINE_DEPOT mut009b.py survivors009.txt [survivors_sans_A.txt survivors_sans_A_ni_temoin_K.txt]
  - regénère les mutants avec l'outil de campagne (mêmes opérateurs, SQL du dépôt) ;
  - lit les noms des survivants dans le fichier produit par la campagne (lignes « ### nom ») ;
  - reconstruit le SQL de chaque entrée du registre (substitution textuelle sur le SQL du dépôt) ;
  - exige une BIJECTION : chaque survivant de la campagne a exactement une entrée de registre dont le SQL muté est IDENTIQUE octet pour octet, et inversement.
Ce que cela ferme : « les preuves portent bien sur les survivants de la campagne, et sur eux seuls ». Ce que cela ne ferme pas : que la campagne elle-même soit complète."""
import pathlib, re, sys
sys.dont_write_bytecode = True
racine, outil, surv = (pathlib.Path(x).resolve() for x in sys.argv[1:4])
extra = [pathlib.Path(x).resolve() for x in sys.argv[4:6]]
preuves = pathlib.Path(__file__).with_name("preuves_equivalence_009.py").read_text(encoding="utf-8")
# 1. le registre, tel que défini dans le script de preuve (partie qui précède les outils de calcul)
g = {"__file__": str(pathlib.Path(__file__).with_name("preuves_equivalence_009.py")), "__name__": "registre"}
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
