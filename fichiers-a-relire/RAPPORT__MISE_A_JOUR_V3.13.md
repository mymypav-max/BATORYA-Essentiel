# BATORYA Essentiel V6 — Rapport de mise à jour documentaire V3.13

**Date** : 2026-10-03 (mise à jour du 2026-10-04 : versionnement des migrations, §10) · **Statut** : copies complètes **en relecture** dans `fichiers-a-relire/` (préfixe `MAJ__`). Rien n'est commité ni poussé. Les fichiers officiels (`docs/**`), les migrations 001–004, les tests et le code sont **inchangés**.
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
- **Révisions [règle validée]** : devis initial = **version initiale** (jamais une « révision 0 ») ; Révision 1, 2, 3… ; numéro `DEV-xxxxx-YY` identique ; une révision = une version complète ; confirmation avant d'ouvrir une phase de révision ; dernière version validée = version contractuelle. Stockage **PT-21** : voir l'addendum du troisième envoi ci-dessous.
- **Numérotation [règle validée]** : un numéro n'est jamais attribué deux fois ; un trou est acceptable, jamais récupéré ; le compteur ne revient pas en arrière. Lecture du premier envoi (« rollback ne consomme rien », alternatives α/ρ) **abandonnée**. INV-22, 25, 179 réécrits ; D-40 remplacée par D-54. Mécanisme **PT-1 : tranché au troisième envoi** (voir ci-dessous).


**Addendum — troisième envoi (2026-10-03)** :
- **PT-1 tranché** (numérotation) : réservation du numéro **committée avant la création de l'objet** — `n = max(compteur, high-water) + 1` sous `BEGIN IMMEDIATE`, high-water écrit durablement dans `machine.db` (blocage si échec), compteur posé à `n` et committé, objet créé dans une transaction distincte. Les documents (§5, §6, §11.4, D-27, D-54, T-24, T-30, C-42, INV-25, INV-179, E-13, encadrés CDC, métier) sont alignés. Limite acceptée : base métier restaurée plus ancienne **et** `machine.db` perdue en même temps (avertissement et relèvement prudent).
- **PT-21 validé sur le principe** (« A raffiné ») : tables vivantes + `devis_revisions` append-only (snapshot complet de chaque version validée, version initiale incluse), `devis.revision`, `devis.revision_en_cours`, `documents.revision`, TR-100, CK-15. **Le devis initial n'est jamais une « révision 0 »** : la version initiale est représentée en interne par `revision IS NULL` (convention technique documentée, distincte du numéro de révision métier ; le numéro de la révision en cours se calcule `COALESCE(revision,0)+1`).
- **Dix décisions intégrées** : (1) version initiale ≠ révision 0 ; (2) toute modification du contenu présenté ou à impact quantitatif/financier crée une phase de révision ; (3) `notes` présentées = contenu de la révision ; (4) `client_id` immuable après finalisation (INV-180) ; (5) révision abandonnée = jamais historique, aucun numéro consommé ; (6) validation sans modification significative refusée ou abandonnée ; (7) refus ou annulation pendant une révision = abandon ; (8) `documents.revision` identifie la version, `numero_version` ne la remplace pas ; (9) `bc_devis.revision_acceptee` supprimée, sans équivalent ; (10) pas de reprise d'une ancienne révision à ce stade.
- **Aucune migration, aucun test, aucun code** ; migrations 001–004 inchangées ; `005_depenses.sql` et `test_005_depenses.py` non créés. Il n'existe pas de document de cadrage de la tranche 003 : les règles sont portées par le modèle V3.13 (§4.6, §4.19, §7.2, §8, §11.4, §13 à §19), les invariants, les errata, le modèle métier et le CDC.


**Addendum — quatrième envoi (2026-10-03)** :
- **Représentation de la version initiale figée : `revision IS NULL`** (option A). Version initiale : NULL ; Révision 1 : `revision = 1` ; etc. Jamais de Révision 0 ; `ordre_version` non retenu ; le 0 de `COALESCE(revision,0)+1` est un terme de calcul, jamais stocké.
- **Protections prévues (futur DDL, non créé)** : `CHECK (revision IS NULL OR revision >= 1)` ; `UNIQUE(devis_id, revision)` ; index unique partiel `UNIQUE(devis_id) WHERE revision IS NULL` ; contrôle du snapshot initial pour tout devis sorti de brouillon (TR-10, CK-15) ; règles d'écriture (`IS NULL` / `IS ?`, jamais `= NULL` ; `COALESCE` explicite).
- **Tests futurs** : T-43 (11 points demandés + 2 compléments), non écrits.
- **Requête canonique** documentée dans le modèle (§4.6) pour le repository/service ; **aucune vue** `v_devis_version_validee` pour l'instant.
- Documents modifiés : modèle V3.13, invariants, errata, rapport. **Aucune migration, aucun test, aucun code, aucun trigger réel ; 001–004 inchangées.**


- **Errata** : E-10 à E-20 ajoutés (E-01 et E-07 annotés « remplacé »). Statut explicite de chaque point (validé / déduit / à concevoir).
- **Invariants (v7)** : INV-179 à INV-196 ajoutés (section N) ; INV-05, 06, 22, 23, 25, 31, 32, 36, 38–40, 42–48, 52, 53, 56–58, 60, 62, 76, 86, 87, 100, 110, 169, 173, 175, 176 modifiés ; INV-33, 34, 35, 49, 61, 77, 79 retirés ou réduits, énoncé d'origine conservé au journal.
- **Modèle SQLite V3.13** : règles ci-dessus traduites ; **nouveaux** §3.8 (exécution et remise), §4.19 (écarts 001–004 → migrations), §11.4 restructuré (PT-1 sans choix), §19 (catalogue PT-1 à PT-21) ; D-40 à D-54 ; cas C-30 à C-40 ; tests T-30 à T-43 ; triggers proposés TR-97 à TR-99 ; migrations correctives proposées M-A et M-B.
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

*(Noms et ordre corrigés le 2026-10-04 : voir §10 — les noms `005_corrections_v313` / `006_bc_multi_devis` et l'ordre « M-A → M-B → Dépenses » de l'envoi initial sont **remplacés**.)*

- **M-A** `metier/005a_corrections_v313.sql` (corrective, rang 6) : `clients` reconstruit sans statut ; `fournisseurs.statut` retiré par `DROP INDEX` puis `DROP COLUMN` (PT-3), gardes (PT-4), `devis` brouillon et numéro nullable (PT-2, PT-7, PT-8), TR-10/TR-11, garde DELETE et cascade limitée au brouillon (PT-5). **Contenu en proposition.**
- **M-B** `metier/005b_bc_multi_devis.sql` (corrective, rang 7) : `bc_devis`, reprise des liens existants, reconstruction de `bons_commande` (retrait de `devis_id` et des remises/acomptes), adaptation TR-12/13/17/18, adaptation de `bc_ligne_garanties` en RESTRICT (PT-5, PT-6, PT-7, PT-16). **Contenu en proposition.**
- Ordre validé (V-1, 2026-10-04) : 005 Dépenses (annulation) → [005a, 005b] → 006 Facturation (PT-9/10/11) → 007 Règlements → 008 Garanties → 009 PV → 010 Planification → exécution (PT-12/13).
- Le modèle passe à la version suivante avant chaque migration (conventions §5).

## 7. Tests à ajouter ou modifier

- **Ajouter** (propositions, modèle §13.3) : T-30 à T-43 ; cas C-30 à C-42. T-39 (exécution, remise) seulement après conception de PT-12 et PT-13.
- **Modifier** : T-24 (selon PT-1), T-27 (statut fournisseur), T-28 (`a_rattacher`, suppression en CASCADE, TR-10/TR-11, `frozen_at`), T-29 (second BC pour un devis, `devis_id`, régénération, liste blanche et gel, exception du rattachement, CASCADE des garanties), T-01/T-02/T-03, T-14 ; obsolètes : T-08, T-09, T-10, T-11, T-13, C-01, C-19, C-20.
- Les tests 001–004 décrivent chaque migration isolément ; les comportements V3.13 se testent sur la chaîne avec M-A/M-B ; nouvelle campagne de mutation sur les triggers réécrits (conventions §7.1).

## 8. Propositions techniques (PT-1 tranché, PT-21 validé sur le principe, les autres non validées)

PT-1 numérotation / high-water (**tranché le 2026-10-03**) · PT-21 stockage des révisions de devis (**validé sur le principe le 2026-10-03** ; représentation de la version initiale figée : `revision IS NULL` ; autres détails = propositions) · PT-2 brouillon de devis · PT-3 retrait des statuts client/fournisseur et client importé ambigu · PT-4 gardes de conservation · PT-5 `ON DELETE` par relation · PT-6 table `bc_devis` (sans cascade d'annulation) · PT-7 devis d'origine, remise/acompte par devis · PT-8 sort de `frozen_at` · PT-9 factures sans annulation, « actif », correction d'un avoir erroné (**à concevoir**) · PT-10 acompte lié à son devis · PT-11 colonnes de situation (signification de « montant » : **à concevoir**) · PT-12 modèles d'exécution A/B/C (**à concevoir**) · PT-13 formule de remise (**à concevoir**) · PT-14 annulation de dépense · PT-15 catalogue d'événements · PT-16 TR-16/INV-47 (avoir sur BC `termine` : à confirmer) · PT-17 réouverture `refuse → en_attente` · PT-18 garanties (aucun mécanisme, conséquence de la suppression de ligne) · PT-19 import d'une facture V2 « annulée » · PT-20 migrations correctives sans réécrire 001–004.

## 9. Points réellement indécidés

**Aucun arbitrage métier bloquant.** Restent des décisions **techniques** de Rémy :
1. **PT-1 (tranché)** : détails d'implémentation seulement — nommage des PDF si un balayage du dossier de documents sert de plancher complémentaire, instance unique, journalisation du trou, garde-fou « hors transaction », `synchronous=FULL` sur `machine.db`. Limite acceptée : base métier restaurée plus ancienne et `machine.db` perdue en même temps.
2. **PT-21 (validé sur le principe ; représentation de la version initiale figée à `revision IS NULL`)** : détails techniques restants — les `notes` sont-elles imprimées sur le devis (fait à confirmer, par défaut incluses dans le snapshot) ; comparaison « modification significative » (normalisation, refus ou abandon automatique : interface) ; PDF généré après le COMMIT de la validation depuis le snapshot ; triggers TR-10/TR-11 en liste blanche et TR-100 ; ordre des lignes dans `json_group_array` selon la version de SQLite embarquée ; libellés des événements d'historique (PT-15).

3. **PT-8** : supprimer ou conserver `frozen_at` comme marqueur informatif.
4. **PT-9, PT-11, PT-12, PT-13** : à concevoir avant la tranche Facturation / exécution (aucune table créée en attendant).
5. Une confirmation d'usage : l'annulation d'un BC n'a aucune précondition de facturation (confirmation d'interface relevant du service) ; PT-16 : avoir sur un BC `termine`. Sont **clos** : « devis `en_attente` verrouillé » (il est modifiable, via les révisions) et « correction sur place sans révision » (toute modification du contenu présenté ou à impact quantitatif/financier passe par une phase de révision).


---

## 10. Mise à jour du 2026-10-04 — versionnement des migrations (phase documentaire uniquement)

*Décisions prises en compte : V-1 (ordre métier réservé 001 → 010), V-2 (tranches `NNN_<objet>` et correctives `NNNx_<objet>`), V-3 (`PRAGMA user_version` = rang dans une chaîne ordonnée figée), V-4 (M-A et M-B après 005, avant 006), V-5 (protocole de reconstruction et runner = chantier technique distinct) ; DV-2 et DV-3 (annulation des dépenses). Enregistrées au modèle sous **D-55**. Aucune migration, aucun test, aucun code, aucun runner n'a été créé ni modifié ; `005_depenses.sql`, `005a`, `005b` et `test_005_depenses.py` n'existent pas. Aucun commit, aucun push.*

### A. Documents examinés

| Catégorie | Documents |
|---|---|
| Documents officiels (lecture seule, `docs/**`) | `conception/conventions-techniques-v6.md` ; `conception/invariants.md` ; `conception/modèle-données-sqlite-v6-v3.12.md` ; `conception/modèle-métier-V6.md` ; `décisions/cdc-errata-v6.md` ; `specifications/cdc-fonctionnel-architectural-v6.md` ; `audit/audit-fonctionnel-v5.16-v6.md` — recherche de `user_version`, restauration, « migration », numéros de fichiers, `M-A`/`M-B` ; lecture des passages concernés |
| Documents de travail déjà présents (`fichiers-a-relire/`) | `CADRAGE__005_depenses.md` (original) et `MAJ__CADRAGE__005_depenses.md` ; `AUDIT__REGLE_CONSERVATION_OBJETS_NUMEROTES.md` et sa copie `MAJ__` ; `MAJ__conventions-techniques-v6.md` ; `MAJ__invariants.md` ; `MAJ__modèle-données-sqlite-v6-v3.13.md` ; `MAJ__modèle-métier-V6.md` ; `MAJ__cdc-errata-v6.md` ; `MAJ__cdc-fonctionnel-architectural-v6.md` ; `MAJ__audit-fonctionnel-v5.16-v6.md` ; `MAJ__README-docs.md` ; ce rapport |
| Migrations (lecture seule) | `src-tauri/migrations/metier/001_initial.sql`, `002_fournisseurs.sql`, `003_devis.sql`, `004_bons_commande.sql` ; `src-tauri/migrations/machine/001_initial.sql` |
| Tests (lecture seule) | `src-tauri/tests/metier/test_001_initial.py` à `test_004_bons_commande.py` ; `src-tauri/tests/machine/test_premier_demarrage.py` |
| Expériences SQLite (hors dépôt) | scripts jetables sur SQLite 3.45.1 avec le DDL réel de 001–004 (données synthétiques, mécanique uniquement) : retrait de colonne, `RENAME` avec triggers dépendants, `DROP TABLE` sous `foreign_keys=ON`, `sqlite_sequence`, `user_version` transactionnel, protocole complet avec succès et échec injecté |

### B. Modifications préparées (copies `MAJ__*`, rien dans `docs/**`)

| # | Fichier | Section | Ancienne règle | Nouvelle règle | Raison / référence |
|---|---|---|---|---|---|
| B1 | `MAJ__conventions-techniques-v6.md` | en-tête | version 0.5 | version 0.6 (2026-10-04) | suivi |
| B2 | idem | §5, règles générales | « le numéro de migration est séquentiel » | l'ordre est celui d'une chaîne ordonnée figée ; le **rang** (pas le préfixe de fichier) est la version du schéma | V-3 |
| B3 | idem | §5, règles générales | le runner met à jour `user_version` « selon le modèle SQLite » | `user_version` écrit **dans la même transaction que la migration, avant son `COMMIT`** ; le runner n'existe pas encore (chantier distinct) | V-3, V-5 ; expérience T1 (`user_version` transactionnel) |
| B4 | idem | §5, base métier | nommage : « `NNN_<objet>.sql` (numéro séquentiel) » | deux catégories seulement : tranche `NNN_<objet>.sql`, corrective `NNNx_<objet>.sql` (`005a`/`005b` ne sont pas des tranches) | V-2 |
| B5 | idem | §5, base métier | « une migration n'insère aucune ligne » | aucune **donnée métier initiale** ; copie technique permise ; migration de données volontaire seulement si décidée et testée (tableau « Données dans une migration ») | demande 6 |
| B6 | idem | §5, nouvelles sous-sections | (absentes) | « Chaîne ordonnée, rang et `user_version` » : liste de rangs 1 → 12, `user_version` = rang (exemple 7), invariants append-only, algorithme (`k > N` refus, sinon rangs `k+1` à `N`) | V-1, V-3, V-4 |
| B7 | idem | §5, nouvelle sous-section | (absente) | « Transaction et `user_version` » : `BEGIN → SQL → contrôles → PRAGMA user_version → COMMIT` | V-3 ; T1 |
| B8 | idem | §5, nouvelle sous-section | (absente) | **Protocole de reconstruction de table en 17 étapes** (`foreign_keys=OFF` hors transaction et vérifié, `BEGIN IMMEDIATE`, triggers dépendants supprimés y compris sur d'autres tables, ids conservés, `sqlite_sequence` monotone, `foreign_key_check`, `ROLLBACK` intégral, `user_version` dans la transaction, `foreign_keys=ON` vérifié) | V-5 ; expériences P5–P9, T2 |
| B9 | idem | §5 et §9 | restauration : « migrations nécessaires » non définies | restauration = même chaîne qu'une installation, par **rang** ; refus si `user_version` > rang maximal | V-3 |
| B10 | `MAJ__modèle-données-sqlite-v6-v3.13.md` | §1 (migrations), historique V3.13, §15 (D-55) | « `user_version` mis à jour après succès » | rang, même transaction, correctives `NNNx`, append-only ; décision **D-55** enregistrée | V-1 à V-5 |
| B11 | idem | §4.19 intro et lignes 2, 4, 10, 17, 21 | ligne 2 : « reconstruire `fournisseurs` » ; ligne 21 : `documents.revision` dans M-A | ligne 2 : `DROP INDEX` puis `DROP COLUMN`, **sans reconstruction** ; ligne 21 : `documents.revision` relève de la future tranche Documents ; lignes 4, 10, 17 : reconstructions selon le protocole, reprise des liens de `bc_devis` explicitée | expériences P1–P4 ; `documents` absent de 001–004 |
| B12 | idem | §11.2 étapes 3–4 | « refus si supérieur au schéma supporté » ; « migrations nécessaires » | `k > N` refus ; migrations de rang `k+1` à `N` dans l'ordre | V-3 |
| B13 | idem | §17.1 | tableau sans rang, ligne vide avant 004 ; M-A `005_corrections_v313`, M-B `006_bc_multi_devis` ; ordre M-A → M-B → Dépenses | tableau avec colonne **Rang** (ligne vide corrigée) ; chaîne 1 → 12 ; M-A = `005a` (rang 6), M-B = `005b` (rang 7), après 005 et avant 006 ; contenu M-A/M-B toujours en proposition | V-1, V-2, V-4 |
| B14 | idem | critère 5 du §17, PT-3, PT-20, PT-21 | PT-3 : « reconstruction de tables » ; PT-20 : numérotation à valider ; PT-21/M-A : `documents.revision` | PT-3 : `clients` reconstruit, `fournisseurs` `DROP COLUMN` ; PT-20 : numérotation et ordre **validés** (D-55), contenu à valider ; PT-21 : `documents.revision` hors M-A | idem |
| B15 | `MAJ__invariants.md` | INV-08, INV-141, en-tête, journal | « numérotées, `user_version` après succès » ; « ≤ supporté » | chaîne figée, `user_version` = rang écrit dans la transaction ; rang maximal supporté ; version du registre 8 ; ligne de journal | D-55 |
| B16 | `MAJ__AUDIT__REGLE_CONSERVATION_OBJETS_NUMEROTES.md` | option « migration corrective dédiée » | « l'ordre officiel 005–010 est à renuméroter » | une corrective n'occupe aucun numéro de tranche ; aucune renumérotation | V-2 |
| B17 | `MAJ__cdc-fonctionnel-architectural-v6.md` | rapport de diagnostic (informations contenues) | « version du schéma SQLite » | précisé : rang de la dernière migration appliquée (`PRAGMA user_version`) | V-3 |
| B18 | `MAJ__CADRAGE__005_depenses.md` | en-tête, §0, §2–§3, §4, §5, §6 (C-M à C-O), §7 (DV-1 à DV-3 retirées du tableau), nouvelle §7 bis, §8, annexe B, risque | DV-1 recommandait « M-A/M-B d'abord » et un numéro de fichier de 005 « à trancher » ; DV-2 « Proposition » ; DV-3 « Décision à valider » | DV-1 : 005 = Dépenses rang 5, `005a`/`005b` après ; DV-2 validée (`cancelled_at` + `motif_annulation`, sans `statut`, UTC ms, motif non vide, cohérence) ; DV-3 option A (irréversible, TR-102 certain) ; DV-4 à DV-10 inchangées | V-1 à V-5 ; DV-2, DV-3 |
| B19 | `RAPPORT__MISE_A_JOUR_V3.13.md` | en-tête, §6, présent §10 | noms `005_corrections_v313` / `006_bc_multi_devis` | noms et ordre corrigés ; section A–D ajoutée | cohérence |

### C. Points volontairement inchangés

- **Migrations 001–004** (y compris leurs en-têtes « `user_version` posé par le runner APRÈS succès », immuables) et `machine/001_initial.sql`.
- **Tests 001–004** et `test_premier_demarrage.py` (leurs fonctions d'application posent `user_version` après le `COMMIT`, avec le numéro de fichier ; valable pour les rangs 1 à 4).
- Tout **code** applicatif, le **runner** (inexistant) et tout manifeste.
- **`005_depenses.sql`, `005a_corrections_v313.sql`, `005b_bc_multi_devis.sql`, `test_005_depenses.py`** : non créés.
- Décisions métier **non validées** : PT-8 (`frozen_at`) et les autres PT ouverts (contenu exact de M-A et M-B, PT-2, PT-5, PT-6, PT-7, PT-16, PT-17…) ; DV-4 à DV-10 du cadrage 005.
- `MAJ__modèle-métier-V6.md` (restauration l.695 compatible), `MAJ__cdc-errata-v6.md`, `MAJ__audit-fonctionnel-v5.16-v6.md`, `MAJ__README-docs.md` : relus, non modifiés.
- Fichiers officiels `docs/**` et originaux de `fichiers-a-relire/` (sauf l'audit v2 déjà modifié localement, sans lien avec cette phase).

### D. Contrôles de cohérence

| Contrôle | Résultat |
|---|---|
| `user_version` vs chaîne | cohérent : rang 1 → 12 ; 005_depenses = 5, 005a = 6, 005b = 7, 006 = 8 ; `010a` éventuelle = 13 ; rang = numéro de fichier pour 001–005 uniquement |
| Aucune tranche renumérotée | 001 → 010 conservés ; 006 reste Facturation (D-34 et V-1) |
| 005 reste Dépenses | oui : cadrage, §17.1, conventions |
| M-A/M-B explicitement correctives | oui : `005a`/`005b`, catégorie « corrective », « ne consomment aucun numéro de tranche » |
| Restauration cohérente | §11.2, INV-141, conventions §5/§9 : refus si `k > N`, sinon rangs `k+1` à `N` ; même algorithme qu'une installation |
| Protocole vs expériences | les 17 étapes reprennent les résultats P5–P9 et T1–T2 (SQLite 3.45.1) ; limites déclarées (données synthétiques ; version minimale du SQLite embarqué non fixée) |
| `sqlite_sequence` | exigence explicite (étape 7) : une reconstruction naïve la fait régresser (2 → 1), ce qui violerait INV-04 |
| Pas de `documents.revision` dans M-A | corrigé (modèle §4.19 ligne 21, §17.1, PT-21) |
| Pas de reconstruction inutile de `fournisseurs` | corrigé (§4.19 ligne 2, §17.1, PT-3, cadrage C-N) |
| Contrainte « une seule source de vérité » | aucun `schema_version` par fichier introduit ; la liste ordonnée fait foi |
| Tests de non-régression des invariants | INV-08 et INV-141 modifiés avec ligne de journal ; aucun INV retiré |

### Nouvelles contradictions relevées

1. **Fonctions d'application des tests 001–004** : elles posent `user_version` **après** le `COMMIT` — contraire à la nouvelle règle (dans la transaction). Émulation seulement ; non modifiée (tests intouchables).
2. **En-têtes des migrations 001–004** : « posé par le runner APRÈS succès » — idem, immuables ; la convention précise qu'elles se lisent selon la règle V3.13.
3. `RAPPORT…` §6 et Modèle §17.1 nommaient M-A/M-B `005_corrections_v313` et `006_bc_multi_devis` avec l'ordre M-A → M-B → Dépenses : **corrigés**.
4. Cadrage 005 (DV-1 et « Risque ») : recommandation « (b) » et risque sur la reconstruction de `fournisseurs` : **corrigés** (C-M, C-N) ; le vrai point sensible est la reconstruction de `bons_commande` par M-B, référencée par `depenses.bc_id`.
5. Conventions §7 : liste des tests métier restée à 001–003 (`test_004_bons_commande.py` existe) : **signalé, non corrigé** (hors périmètre de cette phase).

### Points à valider avant d'écrire `005_depenses.sql`

1. **DV-5 à DV-7** (champs corrigeables, rattachement d'une dépense existante à un BC annulé, 30 jours sur BC annulé) : conditionnent INV-197 et suivants et les tests de service.
2. **DV-4, DV-8, DV-9, DV-10** : sans effet sur le SQL, mais à consigner avant la validation du modèle.
3. **TR-102** : sort d'un `updated_at` isolé sur une dépense annulée (liste blanche ou refus total).
4. **Validation du modèle V3.13** (prérequis de conventions §5) et de **D-55**.
5. Hors 005 mais à ne pas oublier : version minimale du **SQLite embarqué** (V-7, non tranchée ; ≥ 3.37 requis par `STRICT`) ; existence éventuelle de bases V6 contenant des données (V-6) ; conception et tests du **runner** (V-5) ; adaptation des tests 001–004 (modèle §4.19 ligne 20).

---

**Risque** : les copies `MAJ__*` supposent la validation de la V3.13 ; tant qu'elle n'est pas faite, `docs/` (V3.12) reste la dernière version validée et les migrations 001–004 divergent des règles (§4.19). Le fichier `AUDIT__REGLE_CONSERVATION…` de `fichiers-a-relire/` est modifié localement (v2) et le dépôt distant a un commit d'avance sur ce fichier : non aligné.

**Micro-amélioration** : trancher PT-1 puis PT-21 puis PT-8 en premier — ils débloquent M-A/M-B et T-24. *(PT-1 et PT-21 sont tranchés ; reste PT-8, puis DV-5 à DV-7 pour 005.)*
