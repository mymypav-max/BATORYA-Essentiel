Skip to content
mymypav-max
BATORYA-Essentiel
Repository navigation
Code
Issues
Pull requests
Agents
Actions
Projects
Wiki
BATORYA-Essentiel/fichiers-a-relire
/
CADRAGE__005b_bc_multi_devis.md
in
main

Edit

Preview
Indent mode

Spaces
Indent size

2
Line wrap mode

Soft wrap
Editing CADRAGE__005b_bc_multi_devis.md file contents
  1
  2
  3
  4
  5
  6
  7
  8
  9
 10
 11
 12
 13
 14
 15
 16
 17
 18
 19
 20
 21
 22
 23
 24
 25
 26
 27
 28
 29
 30
 31
 32
 33
 34
 35
# CADRAGE — 005b_bc_multi_devis (M-B, rang 7)

Statut : **décisions Q-A à Q-D arbitrées par Rémy (2026-10-05)** — voir section 9. Le SQL est écrit conformément à ces arbitrages.
Dépôt audité : `main` = `origin/main` = `b0a3a8d` (001 → 005a identiques à GitHub, 541 tests verts).
Documents de référence : ceux de `fichiers-a-relire/` (versions `MAJ__*`, V3.13). `docs/` contient encore les anciennes versions V3.12 : **non utilisé comme référence**.

Légende des natures : **[DOC]** règle documentée (source citée) · **[VAL]** décision déjà validée · **[DED]** déduction technique · **[PROP]** proposition (non validée dans les documents) · **[À VALIDER]** décision demandée.

---

## 0. Contradictions et écarts à signaler avant de figer le SQL

| # | Constat | Sources | Traitement proposé |
|---|---|---|---|
| C1 | **INV-175** dit que le service copie dans le BC la liste S du devis, *remise et acompte compris*. Le modèle §4.7 / §4.19 l.11 / PT-7 **retire** `remise_*` et `acompte_*` de `bons_commande` (portés par chaque devis). Un BC à N devis n'a pas une remise unique. | INV-175 ; modèle §4.7, §4.19 l.11 ; INV-189, INV-192 | Suivre §4.7 (retrait). **[À VALIDER] Q-A.** |
| C2 | Le tableau §17.1 place `devis_origine_id` dans M-A et dit que M-B en dépend. **005a (poussée) ne l'a pas créé** (arbitrage « Conservateur »). La colonne n'existe pas au rang 6. | modèle §17.1 ; en-tête de 005a ; tests 005a (`assertNotIn("devis_origine_id")`) | Ne pas la créer en 005b (voir §6). **[À VALIDER]** |
| C3 | Le brief demande de tester « ajout refusé après solde » et « avoir ultérieur ne rouvre pas ». **Aucune table de facture n'existe avant 006** : ces deux règles ne peuvent pas être garanties ni testées dans le schéma 005b. | INV-187 (« ne dépend d'aucune définition technique de facturé à 100 % »), INV-43 (`date_100_facture` n'intervient pas dans le rattachement), modèle §4.7 (tableau SQL/service/CK : « — (tranche Facturation) ») | Règle de **service** + **CK-14**. Les tests 005b vérifient que le SQL **ne** porte **pas** cette règle (aucun cache ne ferme le BC). Voir §3. |
| C4 | Vocabulaire : le brief dit « validée/finalisée », INV-187 dit « **rédigée/validée** » (plus tôt, donc plus strict). | INV-187, E-16 | Employer « rédigée/validée » (texte validé). |
| C5 | TR-17 « lecture du devis via le lien (PT-6) » est **impossible à l'INSERT du BC** : le lien `bc_devis` n'existe pas encore (il référence le BC). La vérification « le BC naît d'un devis accepté, du même client » ne peut donc plus se faire sur `bons_commande`. | modèle §8 (TR-17, TR-99) | Elle passe sur **TR-99** (INSERT du lien, y compris rang 1). Conséquence : un BC peut exister sans lien dans la transaction de création. CK-14 (tel que spécifié) ne couvre pas « BC sans devis de rang 1 » : **à ajouter à CK-14** (écart documentaire). |
| C6 | **Q4 / INV-186 / INV-36** (contenu contractuel du BC immuable *dès sa création*) contredit 004 : tant que le BC n'est pas gelé, `tr_12_bons_commande_modifiable` ne protège que `id`, `devis_id`, `created_at` ; lignes et garanties de lignes sont modifiables/supprimables avant gel (régénération, INV-38 ancien). Vérifié par essai au rang 6. | 004 `tr_12_*`, `tr_13_*` ; INV-36, INV-38, INV-186 ; modèle TR-12, TR-13 | 005b aligne sur Q4 (voir §4). |
| C7 | 005a (en-tête) renvoie **PT-16** (caches d'un BC annulé après avoir) à M-B ; PT-16 est « À CONCEVOIR / à confirmer ». | en-tête 005a ; PT-16 | **[À VALIDER] Q-C.** |
| C8 | Le modèle donne `date_acceptation` du BC = devis d'origine (PT-7) ; la migration ne peut pas le vérifier ni le corriger. | INV-176, modèle §4.7 | Aucune action SQL ; CK-13. |

---

## 1. Audit du modèle actuel devis → BC (rang 6)

Relation : **1 devis → 1 BC**, portée par `bons_commande.devis_id INTEGER NOT NULL UNIQUE REFERENCES devis(id) ON DELETE RESTRICT` (004, `CREATE TABLE bons_commande`). Le `UNIQUE` n'est **pas** le seul obstacle. Obstacles, vérifiés dans le SQL et par essais :

| # | Obstacle | Où | Preuve |
|---|---|---|---|
| O1 | `devis_id` `NOT NULL UNIQUE` : un deuxième BC pour le même devis est refusé ; surtout, il n'existe **aucune place** pour un 2ᵉ devis dans un BC (un BC porte une seule colonne `devis_id`). | 004 | `UNIQUE constraint failed: bons_commande.devis_id` |
| O2 | `tr_13_bc_lignes_insert/update` : `dl.devis_id <> b.devis_id` ⇒ une ligne de BC ne peut venir que **du** devis du BC. | 004 | essai : ligne d'un autre devis refusée (INV-175) |
| O3 | `tr_13_bc_lignes_insert` (et garanties) : INSERT refusé si `frozen_at IS NOT NULL OR statut='annule'` ⇒ aucun rattachement après gel. | 004 | essai : BC gelé refuse la ligne |
| O4 | `tr_12_bons_commande_gele` : `montant_contractuel_ht` immuable après gel ⇒ le contractuel ne peut pas augmenter au rattachement. | 004/005a | essai : refus |
Use Control + Shift + m to toggle the tab key moving focus. Alternatively, use esc then tab to move to the next interactive element on the page.
Aucun fichier choisi
Attach files by dragging & dropping, selecting or pasting them.
 
