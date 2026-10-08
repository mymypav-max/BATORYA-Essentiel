# CADRAGE 007 — Règlements

Tranche 007 (rang 10) : `src-tauri/migrations/metier/007_reglements.sql` + `src-tauri/tests/metier/test_007_reglements.py`.
Statut : **cadrage à valider — aucun SQL ni test n'est écrit.** Aucun fichier 001–006 n'est touché.

Légende des étiquettes :
**[RD]** règle documentée · **[DV]** décision déjà validée (errata, cadrage 006, D-xx) · **[CT]** conséquence technique (déduite, aucune règle nouvelle) · **[PR]** proposition · **[QO]** question ouverte.

---

## 0. Sources et écart documentaire préalable

Sources lues : `invariants.md`, modèle SQLite V3.13, `modèle-métier-V6.md`, `cdc-errata-v6.md`, `cdc-fonctionnel-architectural-v6.md`, `audit-fonctionnel-v5.16-v6.md`, `conventions-techniques-v6.md`, `CADRAGE__006_facturation.md`, `005c`, `006_facturation.sql` et son test (validés).

| # | Document | Section | Écart | Conséquence pour 007 | Correction minimale proposée |
|---|---|---|---|---|---|
| Z-1 | `docs/conception/` | modèle | Le brief cite `docs/conception/modèle-données-sqlite-v6-v3.13.md` : **ce fichier n'existe pas** dans `main` (5b7697a). `docs/` contient la **V3.12** ; la V3.13 n'existe que dans `fichiers-a-relire/MAJ__modèle-données-sqlite-v6-v3.13.md`. | Même situation que pour 006, qui s'est appuyée sur les `MAJ__*`. | **Je retiens les `MAJ__*` (V3.13, post-E-14/E-15) comme référence**, comme en 006. Si ce n'est pas le cas, dites-le avant validation. |
| Z-2 | `docs/conception/invariants.md` | INV-72, INV-76 | Version `docs/` antérieure à E-14 (« aucun encaissement sur facture annulée », « Σ avoirs actifs », « non annulée »). Les `MAJ__invariants.md` sont à jour. | Idem Z-1. | Reporter les `MAJ__*` dans `docs/` (hors 007, à votre main). |
| Z-3 | Modèle V3.13 | §10.5 (ordre d'import) | La phrase « Le gel est posé par TR-15 lors de l'insertion des factures et règlements » est un **reliquat**, TR-15 étant marqué obsolète (PT-8, VR-01, E-10). | Aucun : 007 ne pose ni gel ni `frozen_at`. | Supprimer la phrase (documentaire). |

Aucune contradiction **bloquante** n'a été trouvée sur le fond des règlements.

---

## 1. Règles déjà décidées

### 1.1 Entité et données
| Règle | Étiquette | Source |
|---|---|---|
| `reglements` : `id`, `facture_id` NN FK, `type` NN, `date_evenement` D NN, `montant` D2 NN (`<> '0.00'`), `mode` NN, `reference`, `note`, `cancelled_at`, `motif_annulation`, `created_at`, +IMP | [RD] | modèle §4.9 ; métier §15 |
| `type ∈ {encaissement, remboursement}` ; `mode ∈ {especes, cheque, virement, carte, autre}` (énumérations fermées) | [RD] | modèle §2.5 ; métier §15 ; CDC §20 |
| `mode` obligatoire ; `reference` et `note` « éventuelles » | [RD] | modèle §4.9 (NN) ; métier §15 |
| CHECK `(cancelled_at IS NULL) = (motif_annulation IS NULL)` | [RD] | modèle §4.9 |
| Un règlement = **une seule facture** ; une facture = **plusieurs** règlements ; virement multi-factures réparti explicitement | [RD][DV] | INV-71 ; D-48 (Q20, Q27) ; errata « Hors errata » |
| Un remboursement porte sur un **avoir** (`facture_id` = l'avoir) ; **pas de colonne `avoir_id`** | [RD] | modèle §4.9 ; INV-71 |
| Aucune **numérotation** propre : pas de préfixe REG, pas de ligne dans `numerotation_sequences` (`type_objet` de 001 : CLI FOU DEV BCD ACP FAC AVO PVR DEP) | [RD] | métier §15 (pas de numéro) ; modèle §6 |
| Montant exact : TEXT canonique 2 décimales, centimes entiers, jamais REAL ; montant > 0 | [RD] | modèle §2.3 ; INV-15 ; métier §15 |
| Index : `reglements(facture_id)`, `(date_evenement)`, `(type)` | [RD] | modèle §9 |

### 1.2 Garde-fous (INV-70 à INV-75, TR-30 à TR-33)
| Règle | Étiquette | Source |
|---|---|---|
| Un règlement n'est **jamais supprimé ni modifié** ; seule l'annulation (`cancelled_at` + motif, **une fois**) | [RD] | INV-70 ; TR-32 |
| Encaissement → facture **hors avoir** « active » ; remboursement → **avoir** « actif » | [RD] | INV-71 ; TR-30 |
| Encaissement ≤ `reste_du` ; remboursement ≤ `credit` (à l'INSERT) | [RD] | INV-72, INV-74 ; TR-31 ; C-11 |
| Annulation d'un encaissement **refusée** si elle rend `credit` < Σ remboursements actifs | [RD] | INV-75 ; TR-33 ; C-12 |
| Formules : `encaisse`, `absorbe = min(Σ avoirs, max(0, M − encaisse))`, `reste_du = max(0, M − encaisse − absorbe)`, `credit = Σ avoirs − absorbe − Σ remboursements actifs` (par facture d'origine, jamais < 0) | [RD] | modèle §3.3 ; INV-73 ; métier §15 ; C-06 |
| Un remboursement peut viser **n'importe quel avoir** de la même origine ; le crédit se calcule **par facture d'origine** | [RD] | modèle §3.3 |
| `reste_du` est calculé, jamais saisi ; états de paiement dérivés, jamais persistés | [RD] | INV-60 ; modèle §3.4 ; audit §7 |
| Le caps s'applique à l'import « sans exception » (TR-31 compris) ; pas d'exemption d'origine | [RD][DV] | modèle §10.4 ; INV-131 |
| Un règlement importé suit le même chemin que les autres ; un règlement V2 « paiement unique » devient un `encaissement` (mode `autre`) | [RD] | modèle §10.2 (ligne Paiements) ; journal INV-132 |

### 1.3 Avec le BC
| Règle | Étiquette | Source |
|---|---|---|
| `termine ⇔ solde actif ∧ Σ reste_du (factures hors avoir) = 0` ; l'avoir n'est pas un encaissement, il agit par `absorbe` | [RD] | modèle §3.5 ; INV-42 ; C-05, C-10 ; D-06 |
| Annulation d'un règlement : recalcul en chaîne (`termine → en_cours`, `completed_at = NULL`, événement `retour_en_cours`) | [RD] | INV-79 ; modèle §3.5 ; C-05 |
| Caches du BC recalculés par **un service financier unique**, un seul `UPDATE` ; source de vérité = factures + règlements | [RD] | INV-46, INV-164 ; modèle §3.7 |
| **BC annulé** : règlements sur documents existants **autorisés** ; caches financiers évolutifs ; `statut` reste `annule` | [DV] | VR-04, VR-05 (cadrage 006) ; INV-188 ; PT-16(b) ; 005c ; C-36 |
| **État financier dérivé ≠ réouverture commerciale** (`termine → en_cours` par recalcul est un état dérivé) | [DV] | VR-07, VR-08 (cadrage 006) |
| Après un solde (même totalement crédité) : aucun devis rattachable, ni acompte, ni situation | [DV] | VR-09 ; DV-7, DV-8 ; INV-187 ; C-35 |
| Un règlement ne modifie ni ne supprime une garantie ; `date_100_facture` est conservée par un règlement | [RD] | INV-43, INV-87 |
| Facture importée non réglée = facture ordinaire (ni CA encaissé ni URSSAF tant qu'aucun règlement) | [RD][DV] | INV-163 ; D-19 |
| Facture d'acompte ≠ règlement ; l'acompte a trois niveaux (prévu / facturé / encaissé) | [RD][DV] | INV-189 ; cadrage 006, synthèse n°8 (« Acomptes ? ») |
| Un BC `termine` peut recevoir un avoir (non réouverture) | [DV] | VR-07 |

### 1.4 Frontière 006 / 007
**[DV]** cadrage 006 §1.3 : `reste_du`, `absorbe`, `credit`, états de paiement, partie « encaissements » de `termine`, TR-30→33 sont à **007**. 006 ne les calcule pas (§6.7). Les caches du BC restent écrits par le **service**.

---

## 2. Règles déduites techniquement

| # | Déduction | Pourquoi ce n'est pas une règle nouvelle |
|---|---|---|
| CT-1 | **« Active » dans TR-30/INV-71 n'exige aucune définition SQL.** Aucune facture ne s'annule (E-14) ni ne s'annule un avoir. Une facture totalement créditée a `reste_du = 0` (INV-72) ⇒ tout encaissement (> 0) y est déjà refusé par TR-31. | INV-72 le dit en toutes lettres ; PT-9 (définition de « actif ») reste ouvert **sans effet** sur 007. |
| CT-2 | **Tout avoir est « actif »** (aucune annulation d'avoir, E-14, INV-77 retiré). TR-30 côté remboursement se réduit à `facture cible.type = 'avoir'`. | E-14. |
| CT-3 | **Forme fermée** : `reste_du = max(0, M − encaisse − Σ avoirs)` ; `Σ avoirs − absorbe = max(0, Σ avoirs + encaisse − M)`. | Identités algébriques de la formule §3.3 : la première vaut toujours, la seconde sous l'invariant `encaisse ≤ M` (CT-4) ; équivalences vérifiées par énumération exhaustive. Le SQL pourra les écrire sous l'une ou l'autre forme ; le test oracle reste la formule du modèle. |
| CT-4 | **Invariant dérivé** : à tout instant `Σ encaissements actifs ≤ M` de la facture ; `credit` calculé **sans écrêtage** est toujours ≥ 0. Seul l'**annulation d'un encaissement** peut faire baisser le crédit (un encaissement qui s'ajoute le fait monter, un avoir ne le fait pas baisser, un remboursement est borné par TR-31). TR-33 couvre donc le seul événement dangereux. | Démontrable depuis §3.3 ; vérifié par fuzz différentiel prévu (§9). |
| CT-5 | **Annuler un remboursement n'est jamais refusé par SQL** (il fait monter le crédit). INV-75 ne vise que l'encaissement. | Absence de règle contraire. |
| CT-6 | **Aucun trigger de 007 ne lit ni n'écrit `bons_commande`.** `termine`, `completed_at`, caches : service. Donc un règlement ne peut pas, par construction SQL, réouvrir le BC commercialement ; ce sont les gardes de 006 (`tr_22`, `tr_99`, `tr_16`) qui ferment toujours acompte/situation/second solde/devis après un solde. | INV-46, INV-164 ; VR-07/08/09 ; INV-131 (triggers = gardes pures). |
| CT-7 | **`facture_id` et `type` sont immuables** (UPDATE interdit hors `cancelled_*`) ⇒ TR-30 n'a besoin d'être posé qu'à l'INSERT. | INV-70, INV-184. |
| CT-8 | **Solde à 0.00 / facture à 0.00** : `M = 0` ⇒ `reste_du = 0` ⇒ aucun encaissement (montant > 0). Un avoir ne s'y applique pas non plus (006). Aucune règle spéciale. | INV-72 + `montant <> '0.00'`. |
| CT-9 | **Dépendances aval** : `urssaf_periode_encaissements.reglement_id` (TR-84 « non annulé ») et `historique` relèvent de leurs tranches ; 007 n'en crée rien. Les événements d'historique (règlement, annulation, remboursement, `retour_en_cours`) sont écrits par le service quand `historique` existera. | modèle §4.14 (historique), §4.16 (URSSAF), D-34 ; INV-110. |
| CT-10 | **Gardes séparées par objet de règle et mutuellement exclusives** (TR-31 ne se déclenche pas si la cible est du mauvais type, que TR-30 refuse déjà) : l'ordre entre triggers distincts étant non spécifié, cela garantit des messages déterministes. | Convention 006 (« ordre des triggers non spécifié »). |

---

## 3. Dépendances avec 006 (et avant)

| Dépendance | Détail | Verdict |
|---|---|---|
| `factures` (006) | FK `reglements.facture_id → factures.id` RESTRICT ; lecture de `type`, `total_ht` (M), `origine_facture_id` (avoirs de F). `idx_factures_origine_facture_id` existe déjà. | Rien à modifier en 006. |
| Immutabilité des factures (`tr_20/21`) | La cible d'un règlement ne change jamais ni ne disparaît ⇒ `M` stable ; CT-7. | OK |
| Avoirs (`tr_23`) | Σ avoirs ≤ M(origine) ; avoir sur avoir interdit. Fournit les bornes de `credit` (CT-4). | OK |
| « Neutralisée » (006) = `total_ht > 0 ∧ Σ avoirs = total_ht` | Dérivé ; 007 la rejoint sans la redéfinir : `reste_du = 0`. | OK |
| Unicité du solde actif (`tr_22` solde) | Un solde à 0.00 n'est jamais neutralisé (DV-9) ; son `reste_du` est 0 ⇒ `termine` peut être vrai sans encaissement (D-06). | Pas d'impact SQL. |
| `tr_16` (BC `en_cours` pour acompte/situation/solde) | Après `termine → en_cours` dû à l'annulation d'un encaissement, le BC redevient `en_cours` : **seule** la clause « après solde » (`tr_22`) empêche alors tout nouvel acompte/situation/solde actif. À **prouver par test** (§9, groupe I). | Test d'intégration, pas de modification. |
| `tr_99_bc_devis_apres_solde` | Ferme le rattachement après solde, indépendamment du statut. | Test d'intégration. |
| 004/005b/005c (`bons_commande`) | `statut` peut passer `termine → en_cours` si `OLD.statut <> 'annule'` (`tr_12_contrat`) ; sur BC annulé, seuls `updated_at` et les 3 caches financiers évoluent (`tr_12_annule`, 005c). CHECK `termine ⇔ completed_at`, `termine ⇒ date_100_facture`, `termine ⇒ frozen_at` : le **service** doit écrire ces champs ensemble (résiduel `frozen_at`, VR-02 : non réouvert). | Test d'intégration avec oracle de recalcul (réutilise `recalcul_bc`). |
| Numérotation | Aucune pour les règlements ; ACP/AVO/FAC restent 006. `type_objet` de 001 n'est pas modifié. | OK |
| Import | `origine IN ('v6','import')`, `legacy_id`, `legacy_data json_valid` ; `origine='v6'` ⇒ legacy NULL ; **aucune exemption** (INV-131). | OK ; voir QO-1 et QO-2. |
| Runner | `PRAGMA user_version = 10` (rang 10, D-55) ; `foreign_keys=ON`, `recursive_triggers=ON` (D-39). | OK |

---

## 4. Invariants à porter dans SQLite

### 4.1 Table `reglements` (STRICT) — CHECK / FK / index
- `id INTEGER PRIMARY KEY AUTOINCREMENT` ; `facture_id INTEGER NOT NULL REFERENCES factures(id) ON DELETE RESTRICT`.
- `type IN ('encaissement','remboursement')` ; `mode IN ('especes','cheque','virement','carte','autre')`.
- `date_evenement` : GLOB `'[0-9]{4}-[0-9]{2}-[0-9]{2}'` (forme explicite) **et** `date(x) IS x` — aucune borne d'année (INV-177).
- `montant` : famille D2 (GLOB 2 décimales, chiffres seuls, un seul point, pas de zéro de tête) **et** `<> '0.00'` ⇒ strictement positif.
- `cancelled_at` : TS `YYYY-MM-DDTHH:MM:SS.SSSZ` (GLOB) ou NULL ; `motif_annulation` NULL ou `<> ''` ; `(cancelled_at IS NULL) = (motif_annulation IS NULL)`.
- `created_at` : TS NN, défaut `strftime('%Y-%m-%dT%H:%M:%fZ','now')`.
- BLOC-IMP : `origine IN ('v6','import')` défaut `'v6'` ; `legacy_data` NULL ou `json_valid` ; `origine='v6' ⇒ legacy_id IS NULL AND legacy_data IS NULL`.
- Index : `idx_reglements_facture_id`, `idx_reglements_date_evenement`, `idx_reglements_type`. **Aucun index unique** (deux paiements identiques sont légitimes).
- FK en RESTRICT, sans `ON UPDATE` (INV-05).

### 4.2 Triggers (gardes pures, ASCII, `RAISE(ABORT,'INV-nn: …')`, aucun n'écrit)
| Trigger | Événement | Garde | INV |
|---|---|---|---|
| `tr_30_reglements_cible` | BEFORE INSERT | encaissement ⇒ cible `type <> 'avoir'` ; remboursement ⇒ cible `type = 'avoir'` | 71 |
| `tr_31_reglements_encaissement` | BEFORE INSERT, `type='encaissement'` (cible non-avoir) | `montant ≤ reste_du(cible)` en centimes | 72 |
| `tr_31_reglements_remboursement` | BEFORE INSERT, `type='remboursement'` (cible avoir) | `montant ≤ credit(origine de l'avoir)` en centimes | 74 |
| `tr_32_reglements_update` | BEFORE UPDATE | (a) toute colonne autre que `cancelled_at`/`motif_annulation` inchangée (id, facture_id, type, date_evenement, montant, mode, reference, note, created_at, origine, legacy_*) ; (b) `OLD.cancelled_at IS NOT NULL` ⇒ refus (annulation **une seule fois**, irréversible, motif non modifiable) | 70 |
| `tr_32_reglements_no_delete` | BEFORE DELETE | refus (couvre le DELETE implicite d'un `INSERT OR REPLACE`, `recursive_triggers=ON`) | 70 |
| `tr_33_reglements_annulation` | BEFORE UPDATE, `OLD.cancelled_at IS NULL AND NEW.cancelled_at IS NOT NULL AND OLD.type='encaissement'` | `Σ avoirs − absorbe(encaisse − montant) < Σ remboursements actifs de l'origine` ⇒ refus | 75 |

### 4.3 Protections anti-contournement
`INSERT OR REPLACE` (DELETE implicite refusé) ; `UPDATE OR REPLACE/IGNORE` (RAISE(ABORT) n'est pas altéré par `OR`) ; `UPDATE` de `montant`/`type`/`facture_id`/`date_evenement` ; ré-activation (`cancelled_at = NULL`) ; double annulation ; changement de motif ; `DELETE` ; `INSERT` sans `type`/`mode` ; valeurs hors énumération ; `montant` mal formé (`'1'`, `'1.0'`, `'01.00'`, `'-1.00'`, `'1,00'`, `' 1.00'`, `'1.00 '`). **Limite assumée (D-39)** : avec `recursive_triggers=OFF` le DELETE implicite de REPLACE échapperait au trigger — réglage de connexion, testé comme en 006.

---

## 5. Règles laissées aux services

| Règle | Pourquoi pas SQL |
|---|---|
| Calcul/affichage de `reste_du`, `absorbe`, `credit`, `etat_paiement`, `credit_disponible`, `en_retard`, « entièrement créditée » (PT-9) | Dérivés, jamais persistés (INV-60). |
| Transitions `en_cours ↔ termine`, `completed_at`, `date_100_facture`, `avancement`, `montant_deja_facture_ht` : un seul `UPDATE`, même transaction que le règlement | INV-46/164 ; CK-06 diagnostique. |
| Événements d'historique : règlement, annulation, remboursement, `retour_en_cours`, passage à Terminé | `historique` = tranche propre ; INV-110. |
| Défauts de saisie (date du jour, mode par défaut), confirmations de remboursement | UI/service. |
| Répartition d'un virement sur plusieurs factures (plusieurs règlements) | Q20/Q27 ; service/UI. |
| CA encaissé, CA engagé, CA URSSAF, événements négatifs selon référentiel | Hors 007 (URSSAF, analyses). |
| Choix de l'avoir ciblé par un remboursement ; saisie du motif | Service/UI (SQL impose seulement non vide). |
| Correspondance « client/BC » : implicite via la facture | Aucune redondance à stocker. |

---

## 6. Cas limites à tester

**Structure / formats** : table STRICT, colonnes, défauts, index, 6 triggers, `user_version = 10`, aucune ligne insérée, objets 001–006 inchangés (empreinte `sqlite_master`), migration sur base 006 peuplée (données conservées).
**Montants** : `0.00` refusé ; `0.01` accepté ; `0.1`, `1`, `1.000`, `.50`, `-1.00`, `+1.00`, `1e2`, `01.00`, `1,00`, espaces, vide, NULL, REAL, INTEGER refusés ; très grands montants (comportement identique à 006 : conversion en centimes entiers) ; cumul 0.01 × n.
**Dates** : valides (29/02 bissextile, 31/12, 01/01) ; invalides (30/02, 29/02 non bissextile, 13e mois, `-0001-01-01`, `2026-1-1`, `2026-01-01T00:00`, vide, NULL) ; année 0001/9999 acceptées (aucune borne) ; `cancelled_at` TS valide/invalide.
**Encaissement** : partiel ; plusieurs ; complet (reste 0 ensuite) ; `reste_du + 0.01` refusé ; exactement `reste_du` accepté ; sur facture à 0.00 ; sur facture neutralisée ; après avoir partiel (cap = M − enc − Σav) ; après avoir total ; enc + avoir > M (C-06) ; encaissement qui libère de la capacité après annulation ; sur acompte, situation, solde, et solde à 0.00 ; sur un avoir (refusé).
**Remboursement** : sur facture hors avoir (refusé) ; ≤ crédit ; crédit + 0.01 refusé ; crédit nul ; plusieurs avoirs d'une même origine (crédit commun, remboursement sur l'un ou l'autre) ; avoirs d'origines différentes (crédits séparés) ; C-13 ; remboursement sans avoir.
**Annulation** : encaissement sans remboursement ; encaissement avec remboursement (refus si crédit < Σ remb., accepté si suffisant) ; limites exactes (crédit = Σ remb.) ; deux encaissements dont un annulé ; annulation d'un remboursement ; double annulation ; motif vide ; `cancelled_at` sans motif ; ré-activation ; modification du motif après annulation ; `UPDATE` sans effet sur un actif (no-op).
**Immuabilité / bypass** : UPDATE de chaque colonne ; DELETE actif et annulé ; `INSERT OR REPLACE` sur `id` existant ; `UPDATE OR REPLACE` ; cascade (aucune) : DELETE facture/BC/client refusés (006/004) ; `recursive_triggers` documentée.
**BC** : encaissement/remboursement/annulation sur BC `en_cours`, `termine`, `annule` ; aucune écriture de 007 sur `bons_commande` (empreinte avant/après) ; recalcul oracle : `en_cours → termine` à Σ reste = 0 avec solde actif, `termine → en_cours` à l'annulation d'un encaissement, `annule` reste `annule` avec caches évolutifs ; **après `termine → en_cours` : devis, acompte, situation, second solde actif toujours refusés** ; C-05, C-10, C-36 ; solde à 0.00 + acompte dû ⇒ pas `termine`.
**Import** : `origine='import'` + `legacy_id`/`legacy_data` ; `origine='v6'` + legacy refusé ; `legacy_data` invalide ; mêmes triggers (encaissement import dépassant le reste dû refusé, INV-131) ; QO-1/QO-2 selon décision.
**Atomicité** : une garde échouée dans une transaction multi-règlements annule tout (`ROLLBACK`/`SAVEPOINT`) ; `sqlite_sequence` cohérent ; échec d'un `INSERT` ne laisse aucune ligne ; `INSERT … SELECT` multi-lignes partiellement invalide ⇒ rien.
**Désynchronisation d'ids** (leçon 006) : ids de `reglements`, `factures`, `bons_commande`… volontairement distincts pour tuer les mutants `facture_id ↔ bc_id/id`.

---

## 7. Questions ouvertes (3, chacune avec défaut proposé)

**QO-1 — INSERT d'un règlement déjà annulé (`cancelled_at` renseigné dès l'INSERT).**
Le contrat d'import traite les **annulations** comme des faits saisis (modèle §10.3) et TR-31 s'y applique « comme en fonctionnement normal » (§10.2) ; rien ne dit si un règlement peut naître annulé, ni si le plafond s'applique alors. Un règlement annulé n'étant pas « actif », il ne consomme aucune capacité.
**[PR] Défaut proposé** : INSERT annulé **autorisé pour toutes les origines** (INV-131) ; `tr_30` (cible/type) s'applique toujours ; `tr_31` et `tr_33` ne s'appliquent qu'aux règlements **actifs**.
*Alternative* : tout règlement naît actif, l'annulation se fait par UPDATE (le convertisseur doit alors rejouer l'ordre chronologique réel, sans qu'aucun document ne le fournisse).

**QO-2 — Ordre d'import (§10.5) vs plafond TR-31.**
L'import insère **toutes les factures, avoirs compris, puis les règlements** (par `date_evenement`). Un encaissement historique **antérieur** à un avoir qui l'absorbe (cas C-06 : 1000 payé 600, puis avoir 500 ; ou facture V2 « annulée » = facture + avoir total, PT-19, déjà partiellement payée) serait **refusé** à l'import, alors que l'état final est valide en fonctionnement natif. §10.4 prévoit déjà que le convertisseur « corrige ou déclare non_importe » une donnée violant un plafond.
**[PR] Défaut proposé** : aucune modification SQL ni de l'ordre d'import ; contrainte à consigner dans le contrat du convertisseur (P-04). À confirmer.

**QO-3 — Précisions de DDL mineures sans source (à ne pas décider seul).**
(a) `date_evenement` : aucune chronologie imposée (ni ≥ `date_emission` de la facture, ni ≤ aujourd'hui, ni remboursement ≥ date de l'avoir) ; (b) `reference`/`note` : texte libre sans CHECK (`''` toléré) ; (c) `cancelled_at` : seul le format TS est contrôlé (pas de relation avec `created_at`/`date_evenement`).
**[PR] Défaut proposé** : **rien en SQL** pour (a)(b)(c) (même principe que V6-17 en 006 : ne pas transformer une absence documentaire en décision implicite). Les tests documentent l'acceptation.

Hors questions (déjà tranché ou sans effet SQL) : « active » (CT-1), neutralisation (CT-1/CT-8), BC annulé/terminé (VR-04/07), numérotation (aucune), PT-9 « entièrement créditée » (affichage), `frozen_at` (résiduel, VR-02).

---

## 8. Proposition de structure SQL (`007_reglements.sql`, ≈ 200 lignes)

1. En-tête : références (modèle §2, §2.3, §2.4, §4.9, §8, §9, §10 ; INV-70 à 75, 131 ; D-34, D-39, D-48, D-55), précisions de DDL, mention « aucun BEGIN/COMMIT/PRAGMA, user_version = 10 posé par le runner ».
2. `CREATE TABLE reglements (...) STRICT` — CHECK de colonne d'abord (type, mode, date, montant, motif, TS), CHECK de table ensuite (paire annulation, BLOC-IMP).
3. 3 index (`facture_id`, `date_evenement`, `type`).
4. 6 triggers dans l'ordre §4.2, commentés (INV, forme fermée CT-3, rôle de chaque garde, limites).
5. Aucun `INSERT`, aucun `ALTER` d'une table existante, aucune modification de `numerotation_sequences`.
Contrôle d'atomicité : une seule transaction du runner ; échec ⇒ ROLLBACK intégral.

---

## 9. Stratégie de tests (`test_007_reglements.py`)

- **Infra réutilisée de 006** (`Base9`, `monde()`, `facture()`, `avoir()`, `tente/accepte/refuse`, `recalcul_bc`, `emettre_*`, `desynchroniser_ids`, oracle g/r/valeur_cumulee) ; ajout `Base10` (+`migrer10`, rang 10), constructeurs `encaisse()`, `rembourse()`, `annule_reglement()`, et un **oracle Decimal** indépendant : `encaisse`, `absorbe`, `reste_du`, `credit`, `etat_paiement`, `termine?`.
- **Groupes** : A structure/migration · B CHECK de colonnes · C énumérations · D dates · E montants/centimes · F FK/index · G `tr_30` · H `tr_31` encaissement · I intégration BC (annulé / terminé / en cours, recalcul oracle, pas de réouverture commerciale) · J `tr_31` remboursement · K `tr_32` (UPDATE/DELETE/REPLACE) · L `tr_33` · M avoirs (partiel, total, multiples, origines différentes) · N acompte/situation/solde/solde 0.00/facture neutralisée · O import/BLOC-IMP · P anti-contournement SQL · Q atomicité/rollback · R cas chiffrés du modèle (C-02, C-05, C-06, C-10, C-11, C-12, C-13, C-36) · S fuzz déterministe (graine fixe) contre l'oracle.
- **Volume attendu** : ≈ 180–230 tests (006 : 309 pour 2 tables et 12 triggers).
- **Assertion sur la règle, pas sur l'exécution** : chaque refus vérifie le code INV du message ; chaque acceptation vérifie l'état résultant (lignes, sommes, empreintes des autres tables).
- **Mutation** : `mut007.py` (dérivé de `mut006.py`, périmètre : seul `007_reglements.sql`), mutants de CHECK, littéraux, opérateurs, listes IN, GLOB, `substr`, triggers (WHEN, SELECT, sous-requêtes, `COALESCE`, `CASE`), cache de migration rang 9 sérialisé, 2 workers, fail-fast. Statistiques séparées **table/CHECK/index** et **triggers**. **Chaque survivant qualifié individuellement** : tué / invalide / équivalent démontré (fuzz différentiel `diff007.py` : original vs mutant en parallèle, avec mutants-témoins non équivalents) / vraie lacune de test / vraie lacune métier.
- **Contrôles finaux** : pytest 001→007 ; pytest 007 seul ; `integrity_check` ; `foreign_key_check` ; `user_version = 10` ; statistiques exactes ; tableau des survivants.

---

## Livraison prévue après validation
`007_reglements.sql`, `test_007_reglements.py` (envoyés ici ; vous poussez vous-même) et le rapport de mutation. Aucune modification de 001–006 ni des documents officiels.
