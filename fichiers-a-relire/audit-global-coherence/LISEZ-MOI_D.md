# D — Propositions de modifications

> **Zone non officielle. Rien n'est appliqué.** Les diffs sont rédigés contre `docs/` à `d1d8bb9` ; `git apply --check` réussit pour chacun, seul puis appliqués à la suite (D1, D2, D3) dans une copie jetable.
> Aucun diff ne touche le modèle V3.12 (version validée : on ne la modifie pas en place) ; ses corrections vont dans la V3.14 reconstruite, via la fiche `D4`.

| Fichier | Contenu | Touche | Validation requise |
|---|---|---|---|
| `D1_regle_annulation_stricte_BC.diff` | règle stricte : CDC l.512 (réécrite) et l.543 (puce supprimée) ; INV-44 réécrit (garde `TRG (TR-103), SVC, test`) + ligne de journal 2026-10-13 ; métier l.248 et l.801 | CDC, `invariants.md`, `modèle-métier-V6.md` | **oui** : autorisation de modifier `docs/` ; le CDC étant gelé, **un erratum « Validé » est requis** (errata l.47) — son numéro n'est pas fixé ici (E-10 est déjà pris par un autre contenu dans les `MAJ`). **Ne tranche pas la cascade.** |
| `D2_corrections_certaines_sans_effet_metier.diff` | errata l.4 (chemin `docs/décisions/`) ; métier l.7, 35, 182, 224, 788, 823, 824 (références de version périmées, date de création du BC alignée sur INV-176, « relation future » devenue réelle) ; CDC l.486 et l.843 (puces fusionnées) | errata, métier, CDC | non pour le contenu ; accord d'écriture dans `docs/` requis |
| `D3_statut_V3.12_libelle_a_confirmer.diff` | `docs/README.md` l.23 et l.37 et `invariants.md` l.3 : V3.12 « dernière version validée » ; mention que toute version ultérieure en relecture n'est pas une source de vérité | README, invariants | **oui** : libellé, et date de validation si elle doit être inscrite (non établie par les sources accessibles) |
| `D4_fiche_report_V3.14.md` | textes de remplacement pour le modèle (D-05, l.332/356/640/809, TR-103), listes d'erreurs internes de V3.12, table de correspondance des identifiants hors registre, table des rangs de migrations | modèle V3.14 (à construire) | oui |
| `D5_candidat_README_zone_relecture.md` | README candidat de `fichiers-a-relire/`, à la place de la copie du README de `docs/` | zone de relecture | oui (arbitrage de Rémy) |

Ordre d'application conseillé : arbitrages (rapport A §7) → D2 → V3.14 avec D4 → D1 + erratum + D3.
Non fourni volontairement : aucun diff sur la cascade (dossier F), aucun sur E-07 (historique), aucun sur `audit-fonctionnel` (document d'analyse historique), aucun sur les migrations ou tests.
