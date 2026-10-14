# E — Contrôle final

> **Zone non officielle.** Contrôles exécutés le 2026-10-15 sur `d1d8bb9` (copie de travail jetable pour l'application des diffs). Aucun fichier officiel de la copie de travail n'a été modifié : `git status` ne montre que des fichiers **nouveaux** non suivis (`audit-global-coherence/`, `reprise-autonome-v3.14-tranche-010/`).

## 1. Les diffs s'appliquent-ils ?
| Diff | `git apply --check` seul | Appliqué à la suite (D1 → D2 → D3) |
|---|---|---|
| `D1_regle_annulation_stricte_BC.diff` | OK | OK |
| `D2_corrections_certaines_sans_effet_metier.diff` | OK | OK |
| `D3_statut_V3.12_libelle_a_confirmer.diff` | OK | OK |

## 2. Création de nouvelle contradiction ?
Méthode : comparaison des identifiants D/E/INV/TR/C/CK/T cités dans les 8 documents de `docs/` avant et après application des trois diffs.

| Contrôle | Résultat |
|---|---|
| INV, D, E, C, CK, T ajoutés ou retirés | **aucun** (134 / 39 / 9 / 29 / 13 / 29 identiques) |
| Cascade BC → devis | **intacte** : « le devis passe à Annulé » (CDC) et INV-45 (cascade) toujours présents ; aucun diff ne les touche |
| Ancienne règle d'annulation restante après D1 | audit-fonctionnel l.144 et l.551 (analyse historique, hors hiérarchie), E-07 (registre historique) et **modèle V3.12 D-05 l.898, l.332, l.356, l.640** (couverts par la fiche `D4`, pas par un diff) |
| **Référence pendante créée par D1** | **TR-103** est cité par INV-44 mais **n'est pas défini dans le modèle V3.12** (et TR-97 à TR-102 n'y sont pas non plus). **D1 ne doit donc pas être appliqué seul** : à appliquer avec la V3.14 qui définit TR-103 (ordre indiqué dans `LISEZ-MOI_D.md`). Point à lever par une décision sur la numérotation. |
| Erratum | D1 modifie le CDC gelé sans ajouter de ligne d'erratum : **non conforme à errata l.47** tant que l'erratum n'est pas créé. Volontairement non inclus (numéro à arbitrer) |

## 3. Changement de décision métier sans validation ?
| Diff | Évaluation |
|---|---|
| D1 | traduit **une décision de Rémy identifiée** (`42303cb1` §1-2) ; ne fait rien d'autre (pas de cascade, pas d'import, pas de rang). Application soumise à autorisation |
| D2 | aucune règle changée : références de version, chemin, mise en forme ; la ligne métier l.224 s'aligne sur INV-176 / D-37 (validées) |
| D3 | reflète la décision `a835c585` (V3.12 dernière validée) ; **libellé et date à confirmer** (date non établie) |
| D4, D5 | fiches et README candidats ; aucun effet tant que non intégrés |

## 4. Rupture de référence documentaire ?
| Contrôle | Résultat |
|---|---|
| Fichiers cités par D2 / D3 (`docs/README.md`, `fichiers-a-relire/`) | existent |
| Fichiers de `fichiers-a-relire/` à archiver (plan C) | **rien n'est déplacé** ; chaque archivage futur impose de refaire le contrôle des liens entrants (migrations et tests citent `CADRAGE__00x`) |
| Migrations et tests | **non modifiés** ; leurs commentaires obsolètes (004 l.39-40, en-têtes « V3.13 ») sont consignés, pas corrigés |
| Chemin `docs/décisions/` | corrigé dans D2 (errata l.4). Autres occurrences de `docs/decisions/` : modèle V3.12 l.1047 (formulée « chemin d'origine » : laissée telle quelle, historique) et `MAJ__cdc-errata-v6.md` l.4 (même coquille, proposition non validée : à corriger dans V3.14) |

## 5. Limites de ce contrôle
- Le comportement du **service** (annulation, importateur, CK-13 à la restauration) n'est pas accessible : toute conclusion à ce sujet est **[NV]**.
- Le rang de 009a, les `user_version` des bases de développement et la date de validation de V3.12 ne sont pas établis.
- Les 17 tests ont été classés par lecture et par instrumentation dans une copie hors dépôt ; aucun test n'est modifié.
- Le contenu graphique des 26 références UI et de la charte n'a pas été audité.
- La famille de diffs `DIFF_DOC__010_corrections_documentaires.diff` (ni applicable ni inversible) n'est pas résolue : statut « indéterminé » (C §4).

## 6. Verdict
Les propositions D1 à D3 **ne créent aucune contradiction nouvelle sur les identifiants et ne touchent pas la cascade**, sous deux conditions explicites : (1) D1 est appliqué avec la définition de TR-103 (V3.14) et son erratum ; (2) le libellé de D3 est confirmé. Le corpus **reste incohérent** tant que les arbitrages A §7 ne sont pas rendus.
