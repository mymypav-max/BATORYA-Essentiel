# BATORYA Essentiel V6 — Rapport de mise à jour documentaire V3.13

**Date** : 2026-10-03 · **Statut** : copies complètes **en relecture** dans `fichiers-a-relire/` (préfixe `MAJ__`). Rien n'est commité ni poussé. Les fichiers officiels (`docs/**`), les migrations 001–004, les tests et le code sont **inchangés**.
**Méthode** : le dépôt existant a été traité comme **matière d'audit**, non comme vérité normative. Quand une décision validée contredit un document ou une contrainte SQL, la décision prévaut et l'écart est signalé (modèle V3.13 §4.19). Chaque point est étiqueté **[VALIDÉ]** (règle métier), **[DÉDUIT]** (contrainte technique déduite) ou **[PT]** (proposition technique non validée / à concevoir).

---

## 1. Fichiers modifiés (copies complètes, noms inchangés pour les originaux)

| Copie livrée | Source (non modifiée) |
|---|---|
| `MAJ__cdc-errata-v6.md` | `docs/décisions/cdc-errata-v6.md` |
| `MAJ__invariants.md` | `docs/conception/invariants.md` |
| `MAJ__modèle-données-sqlite-v6-v3.13.md` | `docs/conception/modèle-données-sqlite-v6-v3.12.md` |
| `MAJ__modèle-métier-V6.md` | `docs/conception/modèle-métier-V6.md` |
| `MAJ__cdc-fonctionnel-architectural-v6.md` | `docs/specifications/cdc-fonctionnel-architectural-v6.md` |
| `MAJ__conventions-techniques-v6.md` | `docs/conception/conventions-techniques-v6.md` |
| `MAJ__audit-fonctionnel-v5.16-v6.md` | `docs/audit/audit-fonctionnel-v5.16-v6.md` (renvois seulement) |
| `MAJ__README-docs.md` | `fichiers-a-relire/README.md` (version relue) |
| `MAJ__CADRAGE__005_depenses.md` | `fichiers-a-relire/CADRAGE__005_depenses.md` (bloc d'obsolescence) |
| `MAJ__AUDIT__REGLE_CONSERVATION_OBJETS_NUMEROTES.md` | `fichiers-a-relire/AUDIT__…` v2 (bloc d'obsolescence) |
| `RAPPORT__MISE_A_JOUR_V3.13.md` | ce rapport (nouveau) |

**Second envoi du 2026-10-03** (cycle de vie du devis, révisions, numérotation) : addendum en tête de la section 2 ; les 10 copies `MAJ__*` sont mises à jour (le README, les conventions et l'audit fonctionnel ne changent que par les plages de renvois). Aucune migration, aucun test, aucun code. Aucun fichier existant de `fichiers-a-relire/` n'a été renommé. Le document « migration V2 » inexistant n'a pas été créé.

## 2. Résumé des modifications

**Addendum — second envoi (2026-10-03)** :
- **Cycle de vie du devis [validé]** : brouillon (sans numéro, supprimable tant que jamais finalisé) → finalisation (numéro définitif consommé) → `en_attente` **numéroté et modifiable** → `accepte` (verrouillé, dernière version) / `refuse` (verrouillé, rouvrable, même numéro). E-10 corrigé ; E-20 ajouté ; INV-31, 36, 38, 175, 180, 181, 182 réécrits ; INV-196 ajouté.
- **Révisions [règle validée]** : devis initial sans suffixe, puis « Révision 1 », « Révision 2 » ; numéro identique ; une révision = une version complète ; confirmation avant d'ouvrir une révision ; dernière révision validée = version contractuelle. **Stockage [proposition PT-21, non validée]** : version courante dans les tables vivantes + table append-only `devis_revisions` (copie JSON complète de chaque version validée), colonnes `devis.revision` / `revision_en_cours`, `bc_devis.revision_acceptee`, TR-100, CK-15.
- **Numérotation [règle validée]** : un numéro n'est jamais attribué deux fois ; un trou est acceptable, jamais récupéré ; le compteur ne revient pas en arrière. Lecture du premier envoi (« rollback ne consomme rien », alternatives α/ρ) **abandonnée**. INV-22, 25, 179 réécrits ; D-40 remplacée par D-54. **Analyse** : failles F1 (réattribution après rollback propre), F2 (`machine.db` perdue), F3 (écriture du high-water non bloquante). **Mécanisme [proposition PT-1 révisée, non validée]** : `max(compteur, high-water)+1`, réservation durable avant création, fail-closed.


- **Errata** : E-10 à E-20 ajoutés (E-01 et E-07 annotés « remplacé »). Statut explicite de chaque point (validé / déduit / à concevoir).
- **Invariants (v7)** : INV-179 à INV-196 ajoutés (section N) ; INV-05, 06, 22, 23, 25, 31, 32, 36, 38–40, 42–48, 52, 53, 56–58, 60, 62, 76, 86, 87, 100, 110, 169, 173, 175, 176 modifiés ; INV-33, 34, 35, 49, 61, 77, 79 retirés ou réduits, énoncé d'origine conservé au journal.
- **Modèle SQLite V3.13** : règles ci-dessus traduites ; **nouveaux** §3.8 (exécution et remise), §4.19 (écarts 001–004 → migrations), §11.4 restructuré (PT-1 sans choix), §19 (catalogue PT-1 à PT-21) ; D-40 à D-54 ; cas C-30 à C-40 ; tests T-30 à T-41 ; triggers proposés TR-97 à TR-99 ; migrations correctives proposées M-A et M-B.
- **Modèle métier** : Client sans statut ; Devis brouillon/verrouillé/rouvrable ; BC multi-devis, annulation sans cascade ; fin du « gel » ; facture validée immuable, avoir ; situation globale ; exécution et remise (principes) ; dépense annulable ; fournisseur conservé ; historique.
- **CDC V6.2** : encadrés « Amendement E-10 à E-20 » (texte V6.1 contredit conservé, l'amendement prévaut) aux §12, 13, 14, 16, 17, 18, 19, 21, 22, 24, 28, 33, 42 et en fin de document.
- **Conventions (0.5)** : modèle V3.13 en référence, 004 ajoutée à l'arborescence, correction structurelle par migration ultérieure, `ON DELETE` examiné par relation, conservation.
- **Audit / README / CADRAGE / AUDIT** : renvois et blocs d'obsolescence, sans réécrire l'historique.

## 3. Matrice Q1–Q27

Statut : **V** = règle métier validée · **PT** = mécanisme en proposition technique (non validé) · **AC** = à concevoir · **NT** = non tranché.

| Q | Décision | Statut | Documents impactés | Tables | Migrations | Tests |
|---|---|---|---|---|---|---|
| Q1 | ~~Numéro consommé au COMMIT~~ → **corrigé (second envoi)** : un numéro n'est jamais attribué deux fois ; trou après crash/rollback acceptable, jamais récupéré | **V** ; mécanisme **NT** (PT-1 révisée) | INV-22/25/179, E-13, D-54, modèle §11.4 | `numerotation_sequences`, `machine.db` | aucun DDL | T-24, T-30, C-42 |
| Q2 | Clients/fournisseurs conservés, `a_rattacher` supprimé | **V** ; PT-3, PT-4 | INV-183, E-12, modèle §4.4, métier §3/§19, CDC §12 | `clients`, `fournisseurs` | M-A | T-27, T-33, C-32 |
| Q3 | Devis accepté verrouillé ; `en_attente` numéroté **modifiable** (second envoi) ; aucun avenant | **V** ; PT-2, PT-21 | INV-181, INV-196, E-10, E-20, métier §5, CDC §14 | `devis`, lignes | M-A | T-32, C-30 |
| Q4 | Contenu contractuel du BC stable | **V** ; PT-6, PT-8 | INV-186, E-16, modèle §4.7/§7 | `bons_commande`, `bc_lignes` | M-B | T-29 (adapter), T-34 |
| Q5 | Devis brouillon (sans numéro, supprimable tant que jamais finalisé) ; finalisation = numéro définitif + `en_attente` | **V** ; PT-2 | INV-180, E-10, modèle §4.6 | `devis` (`statut`, `numero` nullable) | M-A | T-32, C-30 |
| Q6 | Numéro de facture attribué à la validation | **V** | INV-179, INV-185, E-13/E-14 | `factures` (tranche à venir) | Facturation | T-30, T-36 |
| Q7 | Dépense corrigeable puis annulable | **V** ; PT-14 | INV-193, E-19, modèle §4.12 | `depenses` | Dépenses | T-40, C-40 |
| Q8 | Pas de facture brouillon ; correction par avoir ; nouvelle facture après avoir total | **V** ; PT-9 | INV-185, E-14, modèle §4.8, CDC §18/21/22 | `factures` sans `cancelled_at` | Facturation | T-36, C-33 |
| Q9 | Tout objet numéroté est conservé | **V** ; PT-4 | INV-06, E-12, conventions §9 | toutes tables numérotées | M-A | T-37 |
| Q10 | `numero` immuable | **V** | INV-23, TR-01 | `devis` | M-A (numéro nullable → attribué) | T-28 (adapter), T-32 |
| Q11 | Objet sans numéro supprimable (brouillon) | **V** ; PT-5 | INV-06, INV-180 | `devis`, lignes | M-A (TR-98) | T-32, T-37 |
| Q12 | `ON DELETE` examiné relation par relation | **V** ; PT-5 | INV-05, D-44, modèle §4.19 | FK devis/BC/garanties | M-A, M-B | T-37 |
| Q13 | Archive ≠ suppression ; non appliqué aux clients/fournisseurs | **V** | INV-183, E-12 | `clients`, `fournisseurs` | M-A | T-33 |
| Q14 | Devis refusé verrouillé et rouvrable (même numéro) | **V** ; PT-17 | INV-182, E-11, modèle §4.6/§8 | `devis` | M-A (TR-10) | T-31, C-31 |
| Q15 | Historique métier utile | **V** ; PT-15 | INV-194, modèle §2.5/§4.14 | `historique` (tranche à venir) | Historique | T-41 |
| Q16 | Références historiques stables | **V** | INV-184 | FK / relations | — | T-37 |
| Q17 | Travail supplémentaire = nouveau devis, rattachable au BC | **V** ; PT-6, PT-7 | INV-187, E-16 | `bc_devis`, `devis.devis_origine_id` | M-B | T-34, C-34 |
| Q18 / Q21 | BC annulable sans condition, conservé avec ses données, avoirs possibles, sans cascade devis | **V** ; PT-16 | INV-188, E-15, modèle §4.7, CDC §17 | `bons_commande`, TR-12/16/18 | M-B | T-35, C-26/C-28/C-36 |
| Q19 | Acompte par devis | **V** ; PT-10 | INV-189, modèle §4.8 | `factures.devis_id` | Facturation | C-34 |
| Q20 / Q27 | Un règlement = une facture | **V** | INV-70/71, modèle §4.9 | `reglements` (déjà `facture_id` obligatoire) | aucune | T-36 (couverture) |
| Q22 / Q25 / Q26 | Couche d'exécution distincte du contractuel ; nouveau devis pour un périmètre accru | **V** (principes) ; schéma **AC** (PT-12) | INV-191, E-18, modèle §3.8 | aucune table créée | — | C-38, T-39 (après conception) |
| Arbitrage D | Remise globale au prorata (10 000/1 000/2 000 → 8 000/800/7 200) | **V** (principe) ; formule **AC** (PT-13) | INV-192, modèle §3.8 | aucune | — | C-39, T-39 |
| Q23 (corrigé) | Rattachement tant que le solde n'est pas rédigé/validé ; avoir sur solde ne rouvre pas ; BC annulé refuse | **V** ; PT-6 | INV-187, E-16, D-47, modèle §4.7 | `bc_devis` | M-B | T-34, C-34, C-35 |
| Q24 | Situation globale en % ou en montant | **V** ; PT-11 | INV-190, E-17, métier §12 | `factures` (colonnes situation) | Facturation | T-38, C-37 |
| Garanties | Principe CDC §24 inchangé ; ligne supprimée = plus de garantie | **V** ; PT-18 (aucun mécanisme) | INV-86/87, modèle §4.10 | `bc_ligne_garanties` | M-B (RESTRICT, PT-5) | T-14 (adapter) |
| Pointages | Hors périmètre Essentiel V6 | **V** | INV-195, D-52 | aucune | — | — |

## 4. Contradictions supprimées ou annotées

1. Devis accepté modifiable tant que non gelé, régénération du BC (E-01, D-33, INV-31/32/36/38) → devis validé verrouillé.
2. « Gel » progressif (INV-33/34/35, TR-14/15, C-01/C-02, T-08 à T-11, §7 du modèle) → supprimé ; sort de `frozen_at` : PT-8.
3. Annulation automatique d'un acompte non réglé (E-01, D-32/INV-35) → supprimée.
4. Annulation du BC conditionnée par la facturation, cascade BC → devis (E-07, D-05, INV-44/45, CDC §17) → annulation sans condition, **sans cascade**.
5. Statuts client/fournisseur `archive`/`a_rattacher`, rattachement de client (INV-49, D-32, métier §3, audit §3.2) → supprimés.
6. Annulation de facture et d'avoir (INV-61/77/79, TR-20/24, état « Annulée », index partiels) → correction par avoir ; « actif » à redéfinir (PT-9).
7. « Un devis = un BC » (INV-40, `bons_commande.devis_id UNIQUE`, D-36) → un BC regroupe plusieurs devis ; un devis n'appartient qu'à un BC.
8. Suppression d'un devis sans BC (D-33) → seul le brouillon est supprimable.
9. CASCADE de `devis_lignes`/`devis_ligne_garanties` (003) et de `bc_ligne_garanties` (004) → examinés par relation (PT-5).
10. CDC §14 « nouveau devis → nouveau BC indépendant » → rattachement possible (E-16).
11. CDC §43 « Une Situation émise interdit l'annulation du BC » → obsolète.
12. D-27 / INV-25 (high-water avant COMMIT, excédent conservé) face à Q1 → **signalé, non corrigé** (PT-1).
13. Proposition « BC facturé à 100 % = solde non neutralisé » (Q23) → retirée ; seul critère : solde rédigé/validé.
14. Garanties : « annulation du solde » → avoir (même total) ; aucun nouveau mécanisme.
15. Événements d'historique `gel`, `rattachement_client`, annulation automatique d'acompte → retirés du catalogue.
16. Audit de conservation (D2 archivage, D3 « pas même un brouillon », Q-1) et CADRAGE 005 (fournisseur archivé, dépense non annulable) → blocs d'obsolescence.

## 5. Impacts SQLite (migrations 001–004 telles qu'appliquées)

- `clients`/`fournisseurs` : colonnes `statut`, CHECK `a_rattacher`, index `statut` à retirer ; garde DELETE et code immuable à ajouter.
- `devis` : `numero` obligatoire → nullable pour le brouillon ; statut `brouillon` ; `frozen_at` (PT-8) ; `date_refus` vs réouverture (PT-17) ; TR-10/TR-11 à réécrire ; DELETE non gardé et CASCADE qui contourne TR-11.
- `bons_commande` : `devis_id UNIQUE NOT NULL` à remplacer par `bc_devis` ; `remise_*`/`acompte_*` à déplacer vers chaque devis ; TR-12/13/17/18 à adapter ; `frozen_at` et CHECK `termine ⇒ frozen_at` (PT-8).
- `bc_ligne_garanties` : CASCADE → RESTRICT (PT-5).
- `numerotation_sequences`, TR-95, TR-96 : inchangés ; le défaut est dans le mécanisme de service (PT-1).
- Tables futures : `factures` sans annulation, `devis_id` d'acompte, colonnes de situation, `depenses.cancelled_at`, événements d'historique.

## 6. Migrations nécessaires (PROPOSITIONS, non créées)

- **M-A** `metier/005_corrections_v313.sql` : clients/fournisseurs sans statut (PT-3), gardes (PT-4), `devis` brouillon et numéro nullable (PT-2, PT-7, PT-8), TR-10/TR-11, garde DELETE et cascade limitée au brouillon (PT-5).
- **M-B** `metier/006_bc_multi_devis.sql` : `bc_devis`, retrait de `devis_id` et des remises/acomptes du BC, adaptation TR-12/13/17/18, RESTRICT sur `bc_ligne_garanties` (PT-5, PT-6, PT-7, PT-16).
- Ensuite (ordre proposé) : Dépenses (annulation) → Facturation (PT-9/10/11) → Règlements → Garanties → PV → Planification → exécution (PT-12/13).
- Numérotation et découpage des fichiers : propositions ; le modèle passe à la version suivante avant chaque migration (conventions §5).

## 7. Tests à ajouter ou modifier

- **Ajouter** (propositions, modèle §13.3) : T-30 à T-42 ; cas C-30 à C-42. T-39 (exécution, remise) seulement après conception de PT-12 et PT-13.
- **Modifier** : T-24 (selon PT-1), T-27 (statut fournisseur), T-28 (`a_rattacher`, suppression en CASCADE, TR-10/TR-11, `frozen_at`), T-29 (second BC pour un devis, `devis_id`, régénération, liste blanche et gel, exception du rattachement, CASCADE des garanties), T-01/T-02/T-03, T-14 ; obsolètes : T-08, T-09, T-10, T-11, T-13, C-01, C-19, C-20.
- Les tests 001–004 décrivent chaque migration isolément ; les comportements V3.13 se testent sur la chaîne avec M-A/M-B ; nouvelle campagne de mutation sur les triggers réécrits (conventions §7.1).

## 8. Propositions techniques NON validées (liste séparée)

PT-1 numérotation / high-water (`max(compteur, high-water)+1`, proposition révisée, **non validée**) · PT-21 stockage des révisions de devis (**non validé**) · PT-2 brouillon de devis · PT-3 retrait des statuts client/fournisseur et client importé ambigu · PT-4 gardes de conservation · PT-5 `ON DELETE` par relation · PT-6 table `bc_devis` (sans cascade d'annulation) · PT-7 devis d'origine, remise/acompte par devis · PT-8 sort de `frozen_at` · PT-9 factures sans annulation, « actif », correction d'un avoir erroné (**à concevoir**) · PT-10 acompte lié à son devis · PT-11 colonnes de situation (signification de « montant » : **à concevoir**) · PT-12 modèles d'exécution A/B/C (**à concevoir**) · PT-13 formule de remise (**à concevoir**) · PT-14 annulation de dépense · PT-15 catalogue d'événements · PT-16 TR-16/INV-47 (avoir sur BC `termine` : à confirmer) · PT-17 réouverture `refuse → en_attente` · PT-18 garanties (aucun mécanisme, conséquence de la suppression de ligne) · PT-19 import d'une facture V2 « annulée » · PT-20 migrations correctives sans réécrire 001–004.

## 9. Points réellement indécidés

**Aucun arbitrage métier bloquant.** Restent des décisions **techniques** de Rémy :
1. **PT-1** : validation du mécanisme d'attribution (`max(compteur, high-water)+1`, réservation durable avant création, fail-closed) ; protection si `machine.db` est perdue (F2) ; instance unique ; journalisation du trou. La règle métier est fixée.
2. **PT-21** : stockage des révisions (table `devis_revisions` JSON append-only) ; modification sans révision, abandon d'une révision, refus/annulation pendant une révision, lien avec `documents.numero_version`, devis importés.
3. **PT-8** : supprimer ou conserver `frozen_at` comme marqueur informatif.
4. **PT-9, PT-11, PT-12, PT-13** : à concevoir avant la tranche Facturation / exécution (aucune table créée en attendant).
5. Une confirmation d'usage : correction sur place d'un devis `en_attente` sans révision (PT-21 propose que non) ; l'annulation d'un BC n'a aucune précondition de facturation (confirmation d'interface relevant du service) ; PT-16 : avoir sur un BC `termine`. Le point « devis `en_attente` verrouillé » est **clos** : il est modifiable.


---

**Risque** : les copies `MAJ__*` supposent la validation de la V3.13 ; tant qu'elle n'est pas faite, `docs/` (V3.12) reste la dernière version validée et les migrations 001–004 divergent des règles (§4.19). Le fichier `AUDIT__REGLE_CONSERVATION…` de `fichiers-a-relire/` est modifié localement (v2) et le dépôt distant a un commit d'avance sur ce fichier : non aligné.

**Micro-amélioration** : trancher PT-1 puis PT-21 puis PT-8 en premier — ils débloquent M-A/M-B et T-24.
