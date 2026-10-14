# Synthèse décisionnelle — audit global de cohérence (2026-10-15)

> Zone non officielle. Commit audité : `d1d8bb9`. Aucune modification officielle, suppression, commit, intégration SQL ni validation de version n'a été effectuée.

## Contenu du dossier
`A_RAPPORT_AUDIT.md` · `B_MATRICE_COHERENCE.md` (21 fiches M-01 à M-21) · `C_PLAN_ASSAINISSEMENT.md` · `D_propositions/` (3 diffs + 2 fiches) · `E_CONTROLE_FINAL.md` · `F_DOSSIER_ARBITRAGE_CASCADE_BC_DEVIS.md`

## 1. Corrections certaines (sans effet métier)
- Chemin `docs/decisions/` → `docs/décisions/` (errata l.4).
- Métier : références de version figées (V3.10/V3.11, invariants « version 3 »), date de création du BC alignée sur INV-176 / D-37 (l.224), « relation future » `devis_id` (l.182).
- CDC : deux listes écrasées (l.486, l.843).
→ `D2` (s'applique proprement, aucun identifiant ajouté ni retiré).

## 2. Corrections dont le contenu est décidé, application à autoriser
- Règle stricte d'annulation du BC : CDC l.512 et l.543, INV-44, métier l.248 et l.801 (`D1`) ; modèle D-05, l.332/356/640, C-19, TR-103 (`D4`, pour V3.14).
- Statut de la V3.12 : README l.23 et l.37, `invariants.md` l.3 (`D3`, libellé à confirmer).
- **Une condition** : le CDC étant gelé, la règle stricte exige un erratum « Validé » (errata l.47) ; son numéro n'est pas fixé.

## 3. Suppressions et archivages justifiés
- **Suppressions : aucune.**
- **Archivage après V3.14 et après contrôle des liens** : `CADRAGE__005_depenses.md`, `AUDIT__REGLE_CONSERVATION…` (versions antérieures), `PLAN_MAJ_DOC__009a_…` V2, `Diff_doc_010_*` v1/v2 (v2 déjà reflété dans l'arbre), diffs 009 déjà appliqués, famille « contrôle NUL » 009 en bloc avec ses preuves.
- **Fusion** : `fichiers-a-relire/README.md` est une copie de `MAJ__README-docs.md` (1 ligne d'écart) → le remplacer par un vrai README de zone (`D5`).
- **Conservation impérative** : `CADRAGE__005b…009` (cités par les migrations livrées), `preuves_009_pv/`, `RAPPORT_MUTATION__*`, `MAJ__*` jusqu'à V3.14.

## 4. Arbitrages métier encore nécessaires
1. **Cascade BC → devis** : décision de Rémy existante (`bfc171c3`, `42303cb1` §9) mais **absente de `docs/`**, qui prescrit l'inverse. À reporter dans un lot distinct, avec le sort de CK-13 (dossier F).
2. **Facture annulée / acompte annulé automatiquement** : le flux de `docs/` (E-01, INV-35, INV-61, TR-24) n'existe pas en SQL (006 : factures immuables). Il détermine la portée de « quel que soit l'état ».
3. **Reprise sélective de la V3.13** pour V3.14 : le SQL livré (005 à 009) suit une V3.13 non validée, dont BC multi-devis (005b), contraire au modèle validé (un BC par devis).
4. **Numérotation** : erratum de la règle stricte, TR-103, D-40+/E-10+/INV-179+/TR-97+ hors registre, TR-51.
5. **Rang 13 de 009a** : après contrôle des `user_version` des bases de développement.
6. **Import** : suppression des passages « BC annulé importé » (M-04) ; **anciens BC annulés facturés** : conservation de INV-188 / D-56 et contrôle diagnostique éventuel.
7. Convention `test_INV_xx` (49 INV sur 125 la respectent), statut de la charte graphique et des références UI.

## 5. Ordre d'opérations recommandé
1. Rendre les arbitrages 1 à 4 (une réponse courte chacun).
2. Appliquer `D2` (forme).
3. Construire V3.14 depuis V3.12 avec `D4` (règle stricte, registre, §17.1, corrections internes).
4. Appliquer `D1` + erratum + `D3` avec V3.14.
5. Contrôler les `user_version` puis fixer le rang de 009a ; ensuite seulement déposer 009a et adapter les 2 tests incompatibles.
6. Archiver (plan C) avec index, après nouveau contrôle des liens.

## 6. Risques résiduels
- Appliquer `D1` seul crée une référence à TR-103 non définie dans le modèle (E §2).
- Les migrations 005 à 009 citent une V3.13 non validée et ne se modifient pas : la dette de traçabilité est permanente ; seule la V3.14 peut la documenter.
- Comportement du service, de l'importateur et de CK-13 à la restauration : non accessible.
- Date de validation de V3.12 inconnue ; messages saisis du 13/10 06:57-08:08 non conservés.

**Aucune modification officielle, suppression définitive, intégration SQL ou validation d'une nouvelle version documentaire n'a été effectuée à ce stade.**
