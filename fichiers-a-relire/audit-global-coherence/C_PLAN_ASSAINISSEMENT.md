# C — Plan d'assainissement du dépôt

> **Zone non officielle. Plan seulement : rien n'est déplacé, fusionné, archivé ni supprimé.**
> « Liens » = nombre de fichiers du dépôt qui citent le nom du fichier (recherche du nom complet, `refs.py`). Les faux positifs sont signalés : `README.md` (nom générique), sous-chaînes (`…V3.html` contenu dans `…V3.html.html`).
> Principe : **aucune suppression** à ce stade. Un fichier cité par une migration, un test ou une preuve de validation n'est ni déplacé ni supprimé sans plan de redirection.

## 1. À CONSERVER en l'état (référence ou traçabilité)
| Fichier | Statut | Liens | Justification |
|---|---|---|---|
| `docs/README.md`, `audit/…`, `conception/{conventions,invariants,modèle-données…v3.12,modèle-métier}`, `décisions/cdc-errata-v6.md`, `specifications/cdc…` | référence officielle active | — | hiérarchie documentaire ; corrections par D1 à D3 seulement après autorisation |
| `docs/conception/charte-graphique-batorya-v6.md` | document de conception « en construction » (v0.5) | 0 entrant ; cite `prototype_claude_ui-uxV3.html` | non listé dans le README (M-19) |
| `CADRAGE__005b_bc_multi_devis.md`, `CADRAGE__006_facturation.md`, `CADRAGE__007_reglements.md`, `CADRAGE__008_garanties.md`, `CADRAGE__009_pv.md` | historique à conserver | 2, 4, 5, 3, 5 | **cités par les en-têtes des migrations livrées et des tests** ; les migrations ne se modifient pas → ne pas déplacer sans redirection |
| `RAPPORT_MUTATION__007_reglements.md`, `…008_garanties.md`, `…009_pv.md` | preuve (conventions §7.1) | 0, 1, 10 | preuves de campagne de mutation |
| `RAPPORT__COMPATIBILITE_001_004_AVANT_005.md`, `RAPPORT__MISE_A_JOUR_V3.13.md` | historique (justifie la V3.13 non validée) | 0, 1 | un lien entrant nul ne prouve pas l'obsolescence : le rapport sert de preuve |
| `MAJ__*` (10 fichiers) | proposition non validée | 2 à 9 | matière première de V3.14 (reprise sélective) ; à archiver **après** construction de V3.14, jamais avant |
| `PLAN_MAJ_DOC__009a_regle_annulation_bc_V3.md`, `RAPPORT_FINAL__009a_proposition_finale_v2.md`, `PROPOSITION_DIFF__009a_V2_bc_annulation_interdite_si_facture.diff` | proposition active (009a) | 0, 0, 1 | `git apply --check` du diff : **réussit** (non appliqué) |
| `DIFF_DOC__010_historique_planification.diff` | proposition active (contenu documentaire de la tranche 011 validé, sans promotion) | 1 | `git apply --check` : **réussit** (non appliqué) |
| `preuves_009_pv/` (18 fichiers) | preuves de validation 009 | cités par `BILAN_VALIDATION`, `LISEZ-MOI`, manifestes | ne jamais supprimer une preuve de validation |
| `docs/conception/references-ui/` (26) | matériel de référence visuel | 24 sans lien entrant | voir §3 |
| `reprise-autonome-v3.14-tranche-010/` (non suivi) | document de reprise | — | garder ; à versionner ou non selon décision de Rémy |

## 2. À CORRIGER (propositions dans `D_propositions/`)
| Fichier officiel | Passage | Proposition | Validation |
|---|---|---|---|
| `cdc-fonctionnel…` | l.512, l.543 | `D1` | oui (erratum) |
| `invariants.md` | l.78 + journal | `D1` | oui |
| `modèle-métier-V6.md` | l.248, l.801 | `D1` | oui |
| `cdc-errata-v6.md` | l.4 | `D2` | non (forme) |
| `modèle-métier-V6.md` | l.7, 35, 182, 224, 788, 823, 824 | `D2` | non pour la forme ; l.224 aligne sur INV-176 validée |
| `cdc-fonctionnel…` | l.486, l.843 | `D2` | non (mise en forme) |
| `docs/README.md` l.23, l.37 ; `invariants.md` l.3 | statut V3.12 | `D3` | oui (libellé) |
| modèle V3.12 | D-05, l.332/356/640/809, 366/717, incohérences internes | **pas de diff sur V3.12** : fiche de report vers V3.14 (`D4`) | oui |
| `E-07` (errata l.14) | — | **ne pas réécrire** ; annoter à la création de l'erratum | oui |

## 3. À ARCHIVER (déplacement avec index et pointeur ; **après** arbitrage, jamais avant V3.14)
Destination proposée : `fichiers-a-relire/archive/` (n'existe pas). Chaque fichier archivé laisse une ligne dans `archive/INDEX.md` (nom, raison, remplaçant, commit d'origine). Le contrôle des liens entrants est à refaire au moment du déplacement.

| Fichier | Raison | Remplaçant / pointeur | Liens entrants à traiter | Traçabilité préservée par |
|---|---|---|---|---|
| `CADRAGE__005_depenses.md` | version antérieure, révisée par `MAJ__CADRAGE__005_depenses.md` (133 lignes diffèrent ; la révision corrige notamment une erreur sur l'annulation d'un BC avec solde actif, `MAJ__CADRAGE__005` l.129 et C-E l.458, fondée sur la règle D-46/E-15 que la décision du 13/10 écarte) | `MAJ__CADRAGE__005_depenses.md` | **9** (dont `005_depenses.sql`, `MAJ__invariants`, `MAJ__modèle…`, `RAPPORT__MISE_A_JOUR`) | l'en-tête de `005_depenses.sql` cite le nom : **conserver à l'emplacement** ou laisser un fichier-pointeur |
| `AUDIT__REGLE_CONSERVATION_OBJETS_NUMEROTES.md` | version antérieure de `MAJ__AUDIT…` (11 lignes diffèrent) | `MAJ__AUDIT__REGLE_CONSERVATION…` | 5 (cadrages 005, 006, 009, MAJ, rapport) | idem : citée par des cadrages |
| `PLAN_MAJ_DOC__009a_regle_annulation_bc.md` (V2) | remplacé par V3, qui déclare le conserver et liste ses erreurs | `…_V3.md` | 2 (V3, `RAPPORT_FINAL__009a`) | V3 §1 « Erreurs du plan V2 » |
| `Diff_doc_010_correctif_redactionnel.diff` (v1) | remplacé par v2 ; `git apply --check` échoue dans les deux sens | `…_v2.diff` | 0 | v2 |
| `Diff_doc_010_correctif_redactionnel_v2.diff` | **déjà reflété** dans l'arbre (`git apply --check -R` réussit) | — | 0 | contenu présent dans les fichiers cibles |
| `Diff_doc_010_tracabilite_diff_lot1.diff` (v1) et `…_v2.diff` | patchent un fichier nommé `Diff_010_corrections_documentaires.diff` qui n'existe plus (renommé `DIFF_DOC__010_…`) ; `git apply --check -R` réussit | `DIFF_DOC__010_corrections_documentaires.diff` | 0 | le renommage est la trace |
| `DIFF_FINAL__test_009_pv.py.diff` | déjà appliqué (`-R --check` réussit) | `test_009_pv.py` | 4 | preuve de la campagne 009 : **garder avec les preuves** |
| `DIFF_DOC__rapport_bilan__chemins_preuves.diff` | déjà appliqué (`-R --check` réussit) | — | 2 | idem |
| famille 009 « contrôle NUL » : `BILAN_VALIDATION__009…`, `COMPLEMENT_ANALYSE__009…`, `COMPLEMENT_CADRAGE__009…`, `PLAN_REMEDIATION__001_008…`, `PROPOSITION_DIFF__009…`, `PROPOSITION_DIFF_TESTS__009…`, `PROPOSITION_DOC__009…`, `SYNTHESE__009…`, `outils_mutation_009.py`, `sorties_brutes_009_nul.py` | documents de travail d'une campagne terminée (009), mais cités entre eux et par les manifestes de preuves | `preuves_009_pv/` + `RAPPORT_MUTATION__009_pv.md` | de 1 à 10 | archiver **en bloc** avec les preuves, pas fichier par fichier |

## 4. À FUSIONNER
| Fichiers | Fusion proposée | Condition |
|---|---|---|
| `fichiers-a-relire/README.md` ≡ `MAJ__README-docs.md` (1 ligne diffère : « révisée en place le 2026-10-12 ») | garder **`MAJ__README-docs.md`** (porte la date), remplacer `README.md` par un vrai README de la zone de relecture (modèle : `D_propositions/D5_candidat_README_zone_relecture.md`) | arbitrage de Rémy ; `README.md` a 9 « liens » mais c'est un faux positif (nom générique) |
| `MAJ__AUDIT__REGLE_CONSERVATION…` / `AUDIT__REGLE_CONSERVATION…` | voir §3 : l'ancien est archivé, pas fusionné | — |
| `DIFF_DOC__010_corrections_documentaires.diff` (indéterminé : ni applicable ni inversible) | à rapprocher de `Diff_doc_010_*` : déterminer si c'est un reliquat partiel ou une version à rejouer | audit complémentaire du contenu (non fait) |

## 5. À SUPPRIMER
**Aucune suppression justifiée à ce stade.**
Candidats examinés et **écartés** :
| Candidat | Pourquoi pas de suppression |
|---|---|
| `fichiers-a-relire/README.md` | copie, mais sa suppression sans README de remplacement laisserait la zone sans présentation ; lien nominal absent |
| `Diff_doc_010_*_v1.diff` | 0 lien entrant, mais ce sont les seules traces de la révision v1 → archiver |
| `DIFF_FINAL__009_pv.sql.diff` (patch corrompu à la ligne 48) | pièce liée à la validation 009 (4 liens, dont `BILAN_VALIDATION` et manifestes) : ne pas supprimer ; consigner qu'il est inutilisable tel quel et que `009_pv.sql` reste la référence |
| `docs/conception/references-ui/prototype_claude_ui-uxV3.html.html` | nom suspect (double extension), mais contenu **différent** de `…V3.html` (257 lignes de diff, 1 716 lignes contre 1 963) : pas un doublon prouvé |
| `batorya-essentiel-v6-atelier-interpretation-mistral-du-registre (3).html` | suffixe « (3) » de téléchargement, mais aucun original dans le dépôt : c'est la seule copie |
| tout fichier de `references-ui/` | 24 sans lien entrant ; absence de lien ≠ obsolescence |

## 6. `docs/conception/references-ui/` — décision de principe
- 26 fichiers, aucun hash en double. Seul `prototype_claude_ui-uxV3.html` est cité (par la charte).
- Proposition : conserver, créer un `INDEX.md` (statut de chaque prototype : retenu / exploration / abandonné) à renseigner par Rémy ; aucun déplacement.
- **Statut indéterminé nécessitant arbitrage** : tous les fichiers sauf `prototype_claude_ui-uxV3.html` (retenu par la charte).

## 7. Ordre d'exécution recommandé (hors de cette phase)
1. Arbitrer les points de décision A §7 (en particulier 1, 2, 4, 5).
2. Appliquer `D2` (sans effet métier) après autorisation.
3. Reconstruire V3.14 depuis V3.12 (avec les fiches `D4`) ; appliquer `D1`/`D3` en même temps que l'erratum.
4. Seulement ensuite : archivage (§3) avec `INDEX.md` et contrôle des liens.
5. Contrôle final identique à E avant et après chaque lot.
