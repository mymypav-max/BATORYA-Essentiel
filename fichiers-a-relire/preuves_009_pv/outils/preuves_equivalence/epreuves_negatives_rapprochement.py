#!/usr/bin/env python3
"""Épreuves négatives du script de rapprochement : il doit ÉCHOUER (code ≠ 0) dans quatre cas qui doivent être détectés.
Usage : python3 -B epreuves_negatives_rapprochement.py RACINE_DEPOT      (n'écrit que dans un dossier temporaire)
  N1 script copié seul (voisin preuves_equivalence_009.py absent)        -> code 2
  N2 voisin présent mais sous un autre nom (cas des noms poussés sur GitHub) -> code 2
  N3 un survivant retiré du fichier des survivants                      -> code 1 (entrée de registre sans survivant)
  N4 un mutant tué présenté comme survivant (intrus)                    -> code 1
Code de sortie : 0 si les quatre épreuves ont bien échoué comme attendu."""
import pathlib, shutil, subprocess, sys, tempfile
sys.dont_write_bytecode = True
ICI = pathlib.Path(__file__).resolve().parent
RAPP, PREU = ICI / "rapprochement_survivants_registre.py", ICI / "preuves_equivalence_009.py"
MUT = ICI.parent / "campagne_mutation" / "mut009b.py"
SURV = ICI.parent.parent / "sorties_brutes" / "campagne_complete" / "survivants_campagne_complete.txt"
R = pathlib.Path(sys.argv[1]).resolve()
def lancer(script, *args):
    r = subprocess.run([sys.executable, "-B", str(script), *map(str, args)], capture_output=True, text=True)
    dernier = (r.stdout + r.stderr).strip().splitlines()[-1:] 
    return r.returncode, (dernier[0] if dernier else "")
ok = True
def epreuve(nom, attendu, res):
    global ok
    bon = res[0] == attendu
    ok &= bon
    print(("OK   " if bon else "ECHEC"), f"{nom} : code {res[0]} (attendu {attendu}) | {res[1][:150]}")
with tempfile.TemporaryDirectory() as d:
    d = pathlib.Path(d)
    (d / "n1").mkdir(); shutil.copy(RAPP, d / "n1" / RAPP.name)
    epreuve("N1 voisin absent", 2, lancer(d / "n1" / RAPP.name, R))
    (d / "n2").mkdir(); shutil.copy(RAPP, d / "n2" / "sorties_brutes_009_nul.py"); shutil.copy(PREU, d / "n2" / "outils_mutation_009.py")
    epreuve("N2 voisin renommé", 2, lancer(d / "n2" / "sorties_brutes_009_nul.py", R))
    blocs = SURV.read_text(encoding="utf-8").split("### ")
    moins = "### ".join([blocs[0]] + [b for b in blocs[1:] if not b.startswith("glob_tail#1 L114")])
    (d / "moins1.txt").write_text(moins, encoding="utf-8")
    epreuve("N3 survivant retiré", 1, lancer(RAPP, R, MUT, d / "moins1.txt"))
    (d / "plus1.txt").write_text(SURV.read_text(encoding="utf-8") + "### check_off L80\n", encoding="utf-8")
    epreuve("N4 intrus ajouté", 1, lancer(RAPP, R, MUT, d / "plus1.txt"))
print("TOUTES LES ÉPREUVES ÉCHOUENT COMME ATTENDU" if ok else "ÉCHEC DES ÉPREUVES")
raise SystemExit(0 if ok else 1)
