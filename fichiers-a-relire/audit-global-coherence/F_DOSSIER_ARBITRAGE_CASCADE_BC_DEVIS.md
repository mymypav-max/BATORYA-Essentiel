# F — Dossier séparé : cascade d'annulation BC → devis

> **Zone non officielle.** Traité à part de la règle d'annulation stricte (lot 009a), comme demandé. **Aucune ligne de ce dossier, aucun diff D1 à D3 ne tranche la cascade.** 009a ne lit pas la table `devis` et reste indépendante de ce sujet (vérifié : le trigger `tr_103…` ne référence que `factures`).

## 1. La contradiction
| Source | Position | Statut de la source |
|---|---|---|
| CDC `cdc-fonctionnel-architectural-v6.md` l.538-541 | « Lorsqu'un BC peut légalement être annulé : le devis passe à Annulé ; son PDF est placé dans Devis/Annule » | officiel |
| `invariants.md` l.79 (INV-45) | « BC annulé : devis `annule` (BC d'abord, puis devis, dans la même transaction : TR-18), PDF du devis dans `Devis/Annule` » | officiel |
| `invariants.md` l.190 (INV-169) et journal l.251 | import d'un BC annulé : annulation du BC puis du devis | officiel |
| modèle V3.12 l.340, l.351 (D-36), l.366, l.717 | le service annule le BC puis le devis, dans cet ordre | officiel |
| modèle V3.12 l.818 (C-28) | « annulation du BC et du devis dans la même transaction (BC d'abord) → accepté » | officiel |
| modèle V3.12 l.886 (CK-13) | signale « BC `annule` sans devis `annule` » | officiel |
| `005b_bc_multi_devis.sql` l.456-457 | « Aucune cascade BC → devis (INV-188) » | SQL livré (suit la V3.13, non validée) |
| `test_005b…` (l.1564-1568), `test_005c…` (l.804-811) | aucune cascade | tests livrés |
| `MAJ` E-15 / D-46 | « devis non annulés automatiquement » | proposition non validée |
| Rémy, `bfc171c3` (§2, « Corrige PT-6 ») | « L'annulation d'un BC n'annule pas automatiquement les devis qui lui sont rattachés… Ne crée donc aucune cascade métier » | **décision de Rémy** (message conservé) |
| Rémy, `42303cb1` §9 | « la règle d'absence de cascade métier BC → devis, qui doit être cohérente dans les documents officiels » | **demande de Rémy** de mise en cohérence |

**Constat [F]** : une décision de Rémy (pas de cascade) existe et le SQL livré la respecte, mais **aucun passage de `docs/` ne la reflète** ; le texte officiel prescrit la cascade. Le désaccord est entre la décision et le texte officiel, pas entre deux décisions.

## 2. Ce qui ne change pas quelle que soit l'issue
- **TR-18 / INV-175** : « un devis ne quitte `accepte` que si son BC est `annule` » reste vrai avec ou sans cascade (vérifié : TR-18 conditionne l'état du BC, pas l'inverse).
- **Trigger 009a** : indépendant.
- **Exclusion du CA engagé** d'un BC annulé (INV-45, 2ᵉ partie) : le CA engagé se calcule par BC.

## 3. Passages à modifier **si** l'absence de cascade est inscrite dans `docs/` (lot distinct, autorisation séparée)
| Fichier | Ligne | Passage | Remarque |
|---|---|---|---|
| CDC | 538-541 | « le devis passe à Annulé ; son PDF est placé dans Devis/Annule » | retirer ou reformuler ; le PDF reste en `Devis/` tant que le devis n'est pas annulé |
| `invariants.md` | 79 (INV-45) | « devis `annule` (BC d'abord, puis devis…) » | INV-45 garde l'exclusion du CA engagé et l'interdiction de nouvelle facturation |
| `invariants.md` | 190 (INV-169), 251 (journal) | import d'un BC annulé | à traiter avec M-04 (pas d'import de BC annulé) |
| modèle (V3.14) | 340, 351, 366, 717 | « annule le BC puis le devis » | + D-36 |
| modèle (V3.14) | 818 (C-28) | second cas « annulation du BC et du devis » | à scinder : BC annulé ; devis annulé séparément par action de l'utilisateur |
| modèle (V3.14) | 886 (CK-13) | « BC `annule` sans devis `annule` » | **ce contrôle signalerait une anomalie là où il n'y en a plus** : à retirer ou reformuler ; point sensible pour l'import et la restauration (échec de restauration si CK-13 retourne une ligne) |
| `modèle-métier-V6.md` | — | silencieux sur la cascade | aucune modification requise ; ajouter la règle explicite si souhaité |

**Test de non-régression à prévoir** : CK-13 sur une base contenant un BC annulé dont le devis est `accepte` (cas normal sans cascade) ne doit pas faire échouer une restauration. À vérifier dans le service **[NV]**.

## 4. Questions d'arbitrage (une réponse suffit à fermer le dossier)
1. Confirmer que la décision `bfc171c3` (aucune cascade) doit être reportée dans les documents officiels (la demande `42303cb1` §9 va dans ce sens).
2. Un devis dont le BC est annulé peut-il être annulé ensuite **séparément** par l'utilisateur ? (le modèle V3.12 l'autorise via TR-18 une fois le BC annulé ; le texte de `bfc171c3` ne l'interdit pas.)
3. Le PDF d'un devis resté `accepte` après annulation du BC reste-t-il dans `Devis/` ?
4. CK-13 : le motif « BC annulé sans devis annulé » est-il supprimé, ou remplacé par un autre contrôle ?

## 5. Lien avec les autres lots
- Ne conditionne ni 009a ni D1 (règle stricte).
- Doit être traité **avant** la reconstruction de V3.14 pour éviter qu'elle ne reprenne la cascade de V3.12 ou l'absence de cascade de V3.13 sans décision.
- Les propositions `MAJ` (E-15, D-46) contiennent la bonne clause de cascade **et** la mauvaise clause d'annulation : lors de la reprise sélective, séparer les deux (voir M-03).
