# PLAN DE MISE À JOUR DOCUMENTAIRE — Règle d'annulation du BC (corrective 009a)

**Date** : 2026-10-13 · **Base** : `main` 74adb2f · **Nature** : liste de modifications **à autoriser**. Aucun document n'est modifié par ce plan. Les numéros de ligne sont ceux de `docs/` et de `fichiers-a-relire/` à 74adb2f.
**Cible** : le modèle de données V3.14 (décision du 2026-10-13 : V3.12 inchangé, V3.13 non promu). Les lignes `MAJ__*` désignent des propositions en relecture, non adoptées.

## 0. Formulation unique à reporter partout

> Un bon de commande ne peut plus être annulé dès qu'au moins une facture a été émise pour ce BC (acompte, situation, solde ou avoir), qu'elle soit réglée ou non, quel que soit le montant restant dû ou le net facturé après avoir. Un avoir, même total, ne rétablit pas le droit d'annuler. Un acompte prévu au devis, sans facture émise, n'interdit pas l'annulation.

## 1. Statut de chaque élément

| Catégorie | Éléments |
|---|---|
| **Décisions métier confirmées** (Rémy, 2026-10-13) | La règle ci-dessus ; aucun import de BC annulé ; corrective au rang 13 et décalage de 010 et 011 ; modèle suivant = V3.14 |
| **Règles techniques déjà implémentées** (`main`) | Factures non modifiables et non supprimables (`tr_20`, `tr_21`) ; pas de `cancelled_at` en 006 ; BC sans colonne d'acompte (005a) ; un BC annulé ne reçoit ni acompte, ni situation, ni solde (`tr_16`, INV-188) mais accepte un avoir ; 005c / D-56. **Rien en SQL n'interdit encore l'annulation d'un BC facturé** |
| **Proposées, non intégrées** | Migration `009a` (diff V2) ; TR-103 ; rangs 010 = 14 et 011 = 15 |
| **Décisions documentaires à prendre** | Les cinq points du §6 |

## 2. Ordre d'application (hiérarchie officielle : conventions techniques §2)

1. CDC (`docs/specifications/cdc-fonctionnel-architectural-v6.md`) — le CDC est gelé ; son précédent : la ligne 512 reprend déjà D-05 / E-07, donc le CDC est mis à jour directement, l'erratum assurant la trace.
2. Modèle de données SQLite (V3.14).
3. Invariants.
4. Modèle métier.
5. Errata (registre de traçabilité, jamais réécrit en silence).
6. Conventions techniques §5, D-61 et diff 011 (rangs seulement).

Toutes ces modifications forment **un seul lot** : tant que l'une manque, la migration cite un texte qui la contredit.

## 3. Modifications requises par la règle confirmée

### 3.1 CDC §17 (`cdc-fonctionnel-architectural-v6.md`)

| Ligne | Texte actuel | Modification |
|---|---|---|
| 512 | « Annulation directe interdite dès qu'une facture autre qu'un acompte non réglé existe, notamment lorsqu'un solde impayé existe sans situation. » | Remplacer par la formulation du §0. |
| après 512 | — | Ajouter : « Un acompte prévu au devis n'est pas une facture : seule une facture d'acompte émise interdit l'annulation. » |
| 514, 516, 518, 1320 | acompte non réglé annulé automatiquement ; situation « même annulée » ; « annulation de facture » | **Non modifiées par ce lot** : elles relèvent du flux INV-35 (§5). |

### 3.2 Modèle de données SQLite (V3.12 → V3.14)

| Élément | Ligne | Modification |
|---|---|---|
| **D-05** | V3.12 l.898 ; MAJ l.1154 | Remplacer par : « Annulation directe du BC **interdite** dès qu'au moins une facture (acompte, situation, solde ou avoir) a été émise pour ce BC, réglée ou non, avoir total compris ; un acompte prévu au devis, sans facture, ne bloque pas ». Colonne « Alternatives écartées » : « conserver l'exception acompte non réglé ; rétablir le droit d'annuler par un avoir total ; se fonder sur les caches du BC ». Statut : « **Validée** 2026-09-29, **révisée** 2026-10-13 ». La mention « [REMPLACÉE … par D-46 / E-15] » de la proposition MAJ (l.1154) est **retirée**. |
| **D-46** | MAJ l.1195 | Supprimer « annulation sans condition de facturation » et l'alternative écartée « annulation conditionnée à la facturation (D-05) ». Conserver : BC annulé conservé avec ses devis (non annulés automatiquement), factures, avoirs, dépenses et historique. Statut : à préciser (§6, point 3). |
| **D-35** | MAJ l.1184 | Dans l'annotation : « annulation sans condition ni cascade, D-46 » → « annulation sans cascade, D-46 ; condition de facturation : D-05 révisée ». |
| **Tableau des triggers** | V3.12 l.605–617 (TR-12 … TR-24) | Ajouter la ligne **TR-103** : `bons_commande / UPDATE (statut → annule)` · « refusé dès qu'une ligne de `factures` référence le BC ; message `INV-44` » · invariant 44. |
| **Comptage de la rubrique « Triggers (15) »** | V3.12 l.488 | À recompter avec TR-103. |
| **Scénarios** | V3.12 l.809 (C-19) | Compléter C-19 (« Situation annulée, puis BC… ») et ajouter : acompte prévu sans facture → annulation acceptée ; facture d'acompte non réglée → refusée ; facture réglée → refusée ; avoir total → refusée ; émission échouée ou défaite par rollback → annulation acceptée. Libellés `C-xx` à attribuer. |
| **Tests** | tableau des T-xx | Ajouter une ligne pour `test_009a_bc_annulation_interdite_si_facture.py` (T-xx à attribuer ; T-52 reste réservé à 010). |
| **Chaîne ordonnée (§17.1)** | MAJ l.1272 et suivantes | Voir §4. |
| **Import d'un BC annulé** | V3.12 l.366 et l.717 ; MAJ l.493 et l.889 | Supprimer le paragraphe « BC historique annulé (import) » ou le remplacer par : « Aucun BC annulé n'est importé : cette fonctionnalité n'existait pas dans les versions précédentes (décision du 2026-10-13). Un BC importé et facturé suit la règle d'annulation commune. » |

### 3.3 Invariants (`docs/conception/invariants.md`)

| Élément | Ligne | Modification |
|---|---|---|
| **INV-44** | l.78 ; MAJ l.76 | Remplacer par : « Annulation directe du BC interdite dès qu'au moins une facture (acompte, situation, solde ou avoir) a été émise pour ce BC, réglée ou non, quel que soit le reste dû ou le net après avoir ; un avoir, même total, ne rétablit pas le droit d'annuler ; un acompte prévu au devis, sans facture, n'interdit pas l'annulation (D-05 révisée) ». Colonne de vérification : « **TRG (TR-103)**, SVC, test ». Colonne des scénarios : retirer C-01 (flux INV-35), ajouter C-19 et les nouveaux C-xx. |
| **INV-45** | MAJ l.77 | Aucune modification. |
| **INV-169** | l.190 et journal l.251 ; MAJ l.185 et journal l.312 | Retirer toute mention d'un parcours « BC historique annulé ». |
| **INV-188 et INV-173** | MAJ l.219 et docs l.84 | **Conséquence à noter, sans changement de texte** : pour un BC annulé après 009a, il n'existe plus de facture, donc plus d'avoir possible ; les clauses sur les avoirs et les caches d'un BC annulé (D-56 / 005c) ne s'appliquent plus qu'aux BC annulés **avant** 009a. Décision documentaire : conserver (recommandé, le schéma reste rejouable) ou signaler. |
| **INV-189** | MAJ l.220 | Compatible (acompte prévu / facture d'acompte / règlement). Ajouter un renvoi à INV-44. |
| **Journal des modifications** | fin du fichier | Ajouter une ligne datée du 2026-10-13. |

### 3.4 Modèle métier (`modèle-métier-V6.md`)

| Ligne | Texte actuel | Modification |
|---|---|---|
| 248 | « … interdite directement dès qu'une facture autre qu'un acompte non réglé existe ; une situation émise (même annulée) l'interdit toujours ; un encaissement l'interdit. Un acompte non réglé est annulé avec le BC. La correction passe sinon par avoir ou annulation de facture. » | Remplacer par la formulation du §0 ; supprimer « Un acompte non réglé est annulé avec le BC » ; « La correction passe par avoir » (la mention « annulation de facture » relève du §5). |
| 801 | « un BC dont la facturation dépasse un acompte non réglé ne peut pas être annulé directement ; une situation émise (même annulée) l'interdit toujours » | « un BC portant au moins une facture ne peut pas être annulé directement, quel que soit son type ou son règlement ». |
| 272, 800 | acompte non réglé annulé automatiquement | **Non modifiées par ce lot** (§5). |

### 3.5 Errata (`docs/décisions/cdc-errata-v6.md`)

| Élément | Modification |
|---|---|
| **E-07** (l.14) | Ne pas réécrire la ligne. Colonne « Statut » : « Validé (D-05, 2026-09-29) ; **révisé le 2026-10-13 par E-21** : l'exception « acompte non réglé » est supprimée ». |
| **E-21** (nouveau ; numéro suivant celui de la proposition E-20, à ajuster si E-10 à E-20 ne sont pas intégrés) | Date 2026-10-13 ; section CDC §17 ; ancienne formulation : celle de E-07 ; nouvelle décision : formulation du §0 ; motif : cohérence avec les factures immuables (006) et l'historique de facturation ; impact : INV-44, TR-103, CDC §17, D-05, `009a` ; statut : **Validé** (Rémy, 2026-10-13). |
| **E-15** (MAJ l.22) | Remplacer « Remplace E-07 (et D-05) » par « Remplace E-07 pour les effets de l'annulation ; la condition de facturation de l'annulation est fixée par E-21 » ; dans « Nouvelle décision », « Un BC peut être annulé » → « Un BC sans facture peut être annulé ». |

## 4. Rangs de la chaîne (décalage de 010 et 011)

| Document | Ligne | Modification |
|---|---|---|
| **Conventions techniques §5** (MAJ) | l.127 et suivantes (tableau de la chaîne) | Insérer la ligne rang 13 `009a_bc_annulation_interdite_si_facture` (corrective) ; « rangs 1 à 12 » → « 1 à 13 » ; 010 → rang 14 ; 011 → rang 15 ; une `010a` éventuelle → rang 15 ; une corrective après 011 → `011a`, rang 16. |
| **Conventions §5** | l.166 | « une `010a_*` aurait le rang 14 » → « rang 15 ». |
| **Conventions §5** | l.178 | « Les lignes des rangs 5 à 12 … » → « 5 à 13 » (ligne 13 figée à la livraison de 009a). |
| **Modèle §17.1** (MAJ) | l.1272 et suivantes | Même mise à jour du tableau ; ajouter 009a. |
| **D-61** | V3.13 MAJ l.1210 ; l.557 | « `010_planification.sql` au rang 13 » → « rang 14 ». |
| **D-55 (amendée)** | modèle MAJ | « 011_historique, rang 14 » → « rang 15 ». |
| **D-56** | — | Aucune modification. |
| **Diff 011 validé** (`DIFF_DOC__010_historique_planification.diff`, blob `8124bf58…`) | l.7, 8, 28, 59, 63, 64, 74, 91, 92, 97, 101, 105, 106, 113, 121, 123 | « 010 (rang 13) » → « 14 » ; « 011 (rang 14) » → « 15 » ; « `010a_*` (rang 14) » → « 15 » ; « `011a_*` rang 15 » → « 16 » ; ajouter 009a (rang 13, corrective) dans les tableaux de la chaîne. **Le périmètre validé du diff (contenu de 011, INV-203, D-60) ne change pas** ; seuls des numéros de rang sont reportés, ce qui exige un diff 011 de remplacement, à produire après autorisation. |
| **Plan de remédiation NUL** | P-4 | « avant ou après 010 » devient « avant ou après le rang 14 ». |
| **Clause de D-61** « révisé en place (pas de V3.14) » | MAJ l.1210 | Contraire à la décision V3.14 : à reformuler (point déjà signalé). |

## 5. Flux distinct : INV-35 et annulation d'une facture (non intégré à la corrective)

Ces textes décrivent l'annulation automatique d'un acompte non réglé ou l'annulation d'une facture ; la 006 livrée l'a rendue impossible (aucun `cancelled_at`, `tr_20`). Ils **ne sont pas** modifiés par le lot ci-dessus et appellent leur propre décision (fin de l'annulation de facture, PT-9 ; correction par avoir) :

| Référence | Objet |
|---|---|
| CDC l.435, 441, 514, 518 ; audit l.143–144 | acompte non encaissé annulé automatiquement ; « annulation de facture » |
| INV-35, INV-61 ; modèle métier l.272, 800 | idem |
| Modèle V3.12 l.315, 574, 617 (TR-24), C-01 (l.791), T-08 (l.834) | CHECK transitoire, annulation automatique, `cancelled_at` |
| INV-44 (partie « annulé dans la même transaction ») | **retirée par le lot §3.3** : seul l'effet sur l'annulation du BC est traité ici |

Conséquence de la règle confirmée sur ce flux : un acompte non réglé ne peut jamais être « annulé avec le BC » ; l'annulation automatique lors d'une modification du devis ou du BC reste à décider séparément.

## 6. Décisions documentaires restant à prendre

1. **Support de la règle** : erratum **E-21** (recommandé : traçabilité sans réécrire E-07 ni E-15) ou modification de E-15 seule.
2. **Statut de D-46 et de E-15** : conserver leurs autres éléments (BC annulé conservé, aucune cascade vers les devis) tout en retirant la condition de facturation.
3. **INV-188 / INV-173 / D-56** : conserver les clauses sur les avoirs d'un BC annulé (BC annulés avant 009a) ou les neutraliser.
4. **Numéros** : T-xx et C-xx à attribuer ; E-21 à ajuster selon l'intégration de E-10 à E-20.
5. **Calendrier** : les rangs de 010 et 011 changent dans les documents au même moment que la migration 009a est intégrée, jamais avant (sinon la documentation annonce un rang 13 pour deux migrations).
