# BATORYA Essentiel V6 — Errata du CDC gelé

Le CDC V6 est gelé. Tout écart décidé ensuite est tracé ici : date, section, ancienne formulation, nouvelle décision, motif, impact, statut.
Ce fichier est un **registre de décisions**, pas une spécification : le détail des règles est dans le modèle, les invariants et les documents de conception. Il est une pièce obligatoire du modèle de données (V3.6). Chemin dans le dépôt : `docs/decisions/cdc-errata-v6.md`.

| ID | Date | Section CDC | Ancienne formulation | Nouvelle décision | Motif | Impact | Statut |
|---|---|---|---|---|---|---|---|
| E-01 | 2026-09-29 | §14 Modification d'un devis accepté | Le devis et le BC sont figés « dès qu'une facturation a commencé ». | Un acompte émis mais non encaissé **ne gèle pas**. Le gel intervient au premier encaissement actif (même partiel) d'un acompte, à l'émission d'une situation ou d'un solde. Modifier le devis/BC annule automatiquement l'acompte non encaissé (même transaction). Le gel est irréversible. | Permettre de corriger un devis tant qu'aucun engagement financier ou opérationnel réel n'existe. | INV-33 à INV-36 ; TR-10 à TR-15 ; `frozen_at` sur devis et BC | Validé (V3.4, arbitrage Rémy) |
| E-02 | 2026-09-29 | §42 Sauvegardes | Sauvegardes JSON, moteur commun. | La sauvegarde et la restauration officielles sont une copie cohérente de la **base SQLite métier** (API Backup ou `VACUUM INTO`). Le JSON est un **export** ; l'import des sauvegardes V2 JSON reste obligatoire pour la migration. `machine.db` est exclue des sauvegardes. | Cohérence transactionnelle, restauration atomique, séparation des données machine. | INV-140 à INV-144 | Validé (V3.4) — **clause « l'import des sauvegardes V2 JSON reste obligatoire pour la migration » obsolète depuis E-09** (le JSON V2 est une entrée du convertisseur externe, pas un format d'import de V6 ; INV-144 réécrit) |
| E-03 | 2026-09-29 | §26 Planning | Planning mixte (événements BC + événements généraux). | Le module s'appelle **Planification** : onglet **Calendrier** (événements typés, rattachement facultatif à un BC) et onglet **Gantt** (lié aux dates `date_debut/date_fin` du BC). Le Gantt ne constitue pas une gestion de chantier indépendante du BC (CDC §2 respecté). Types `intervention` et `travaux` conservés (BC obligatoire). | Usage type agenda + suivi de chantier borné au BC. | INV-101 ; table `planning_evenements` | Validé (D-03 validée 2026-09-29) |
| E-04 | 2026-09-29 | §23 Numérotation des PV | `PV-0001-26`, `PV-0001-26-01`. | `PVR-00001-26` et `PVR-00001-26-01` (convention TRI-00001-26 de l'audit V5.16 → V6 §24). Le PV initial n'a pas de suffixe. | Uniformisation des numéros de documents. | INV-20, INV-26 | Validé (audit V5.16 → V6) |
| E-05 | 2026-09-29 | §18-19 Préfixes | Préfixes « définis à partir du fonctionnement V5.16 ». | Format uniforme `TRI-00001-yy` : `DEV`, `BCD`, `FAC`, `ACP`, `AVO`, `PVR`, `DEP`. Numéros historiques V2 conservés tels quels à la migration (la V5 n'a jamais été distribuée). | Hétérogénéité des conventions V5. | INV-20, INV-27 | Validé (audit V5.16 → V6) — **clause « numéros historiques V2 conservés tels quels à la migration » précisée par E-09** : conservés seulement pour les devis, factures et PV importés ; BC et codes clients importés au format V6 |
| E-06 | 2026-09-29 | §12 Clients / audit §24 | Codes `CLI-001`, `FOU-001` (audit). | Codes `CLI-0001`, `FOU-0001` (4 chiffres, sans année). Migration : codes V2 recodés, ancien code en `legacy_numero`. | Cohérence des formats ; évite l'ambiguïté `CLI-001` / `CLI-0001`. | INV-20, INV-27 | Validé (D-01, 2026-09-29) — **« Migration : codes V2 recodés » désormais exécuté par le convertisseur externe (E-09)** ; le format `CLI-0001` reste la règle V6 |
| E-07 | 2026-09-29 | §17 Annulation du BC | Annulation possible si aucune situation émise et aucun paiement encaissé ; acompte impayé annulé avec le BC. | Le modèle V3.4/V3.5 **interdit** l'annulation directe dès qu'une facture autre qu'un acompte non réglé existe (par exemple un solde impayé sans situation), la correction passant par avoir/annulation de facture. Une situation émise (même annulée) interdit toujours l'annulation directe. | Le CDC est silencieux sur le solde impayé sans situation ; le modèle a retenu la règle la plus prudente. | INV-44 ; TR-24 | Validé (D-05, 2026-09-29) |
| E-08 | 2026-09-29 | §39-40 / modèle | Le référentiel réglementaire « remplace les paramètres précédents ». | Versions **append-only** ; `date_debut_effet` strictement croissante ; version applicable à une période = celle en vigueur à sa date de début. | Reproductibilité des calculs historiques (CDC §36). | INV-121 | Validé (D-10, 2026-09-29) |
| E-09 | 2026-09-30 | §42 Sauvegardes / migration (modèle V3.5 initiale §10, D-01, D-13 à D-19, INV-131 à INV-136, INV-153 à INV-163, `migration_rapports`, `migration_quarantaine`) | La migration V2 est exécutée par V6 : lecteur V2 tolérant, mode migration (`origine='migration'`) avec exemptions SQL, rapports et quarantaine de migration, compteurs V2 jamais importés. | **Migration V2 externalisée** : V2 JSON → convertisseur externe → `import-v6.json` → import standard V6 (texte complet ci-dessous). Remplace les décisions antérieures de traitement direct de la structure V2 dans SQLite V6. | V6 ne doit pas adapter son modèle métier à la structure et aux incohérences V2 ; contrat d'entrée propre ; une seule source historique (V5 jamais distribuée). | INV-130 à INV-136, INV-144, INV-153, INV-154, INV-161, INV-163, INV-165, INV-169, INV-170 ; INV-132 et INV-155 à INV-160, INV-162 retirés (règles au convertisseur) ; modèle §10, D-21 à D-26 ; T-16, T-21 à T-23 | Validé (brief Rémy, 2026-09-30) — sous-décisions D-22, D-23, D-24 du modèle **à valider** |

## Décisions d'architecture

### 2026-09-30 — Migration V2 externalisée (E-09)

La migration de l'ancienne sauvegarde V2 n'est plus réalisée directement par le modèle ou les services métier V6.

Le flux retenu est :
V2 JSON → convertisseur externe → import-v6.json → import V6.

Le convertisseur porte les adaptations nécessaires aux structures et incohérences historiques V2. V6 ne doit pas adapter son modèle métier à la structure V2.

import-v6.json constitue le contrat d'entrée propre de V6.

V5.16 n'a jamais été distribué et ne constitue donc pas une source de migration. Il reste uniquement une référence fonctionnelle et technique.

Les compteurs historiques V2 compatibles sont récupérés lors de la conversion et transmis au format d'import V6.

La traçabilité historique, les anomalies et les données non représentables doivent être conservées ou signalées selon le contrat d'import V6, sans introduire d'exceptions structurelles V2 dans le modèle métier.

Cette décision remplace les décisions antérieures qui prévoyaient un traitement direct de la structure V2 dans SQLite V6.

**Décisions antérieures devenues obsolètes (référencées, non effacées)** : E-02 (clause d'import des sauvegardes V2 JSON) ; E-05 et E-06 (volet « à la migration ») ; dans le modèle V3.5 initiale : §10 « Migration V2 → V6 » et son mode migration, `migration_rapports`, `migration_quarantaine`, `migration_id`, exemptions par `origine='migration'` ; dans `invariants.md` : INV-131 (principe général d'exemptions), INV-132, INV-135 (compteurs jamais importés), INV-153 (lecteur tolérant), INV-155 à INV-160 et INV-162 (règles V2) ; D-13, D-15, D-16, D-17, D-19 (statuts « transférée au convertisseur »).

**Suite prévue** (hors de ce registre) : `docs/migration/convertisseur-v2-vers-import-v6.md` (mapping complet V2 → import-v6.json), après validation du modèle V6 nettoyé.

## Règle d'usage

- Un écart au CDC n'est valide que s'il figure dans ce tableau avec le statut **Validé**.
- Une ligne « À confirmer » n'autorise pas encore le DDL à s'écarter du CDC ; elle bloque le passage au DDL pour les tables concernées.
