# CADRAGE 009 — PV (procès-verbaux de réception)

Tranche 009 (rang 12) : future `src-tauri/migrations/metier/009_pv.sql` + `src-tauri/tests/metier/test_009_pv.py` (T-51). **Ce document est un cadrage : aucun fichier SQL, test, rapport de mutation ou document officiel n'est créé ou modifié.**
Statut : **cadrage initial (2026-10-09), en attente de relecture et de validation par Rémy avant toute écriture du SQL et des tests.** Dépôt lu : `main` @ `a9fd50f` ; les fichiers 008 (`008_garanties.sql`, `test_008_garanties.py`, `CADRAGE__008_garanties.md`, `RAPPORT_MUTATION__008_garanties.md`) sont lus dans la copie de travail (non encore poussés par Rémy, donc non présents dans `main`).

Légende des étiquettes :
**[RD]** règle documentée · **[DV]** décision déjà validée (errata, cadrages 006/007/008, D-xx) · **[CT]** conséquence technique (déduite, aucune règle nouvelle) · **[PR]** proposition à arbitrer · **[QO]** question ouverte.
*Toute règle non documentée est signalée comme telle et n'est pas transformée en règle : la valeur par défaut d'une [QO] est toujours « aucune règle ajoutée ».*

---

## 0. Sources lues et hiérarchie

Lues sur les passages « PV / levée / réception / PVR » : `docs/conception/invariants.md`, `modèle-métier-V6.md` (§22-23), `modèle-données-sqlite-v6-v3.12.md` (§4.11, §6, §7.2, §8, §9, §10), `conventions-techniques-v6.md`, `docs/specifications/cdc-fonctionnel-architectural-v6.md` (§23), `docs/décisions/cdc-errata-v6.md`, `docs/audit/audit-fonctionnel-v5.16-v6.md` (§12) ; leurs versions de travail `fichiers-a-relire/MAJ__*` (dont **V3.13**, laissée dans `fichiers-a-relire/`, non déplacée, **non traitée comme publiée**) ; `MAJ__AUDIT__REGLE_CONSERVATION_OBJETS_NUMEROTES.md` (§3.7, C-7), `RAPPORT__MISE_A_JOUR_V3.13.md` ; cadrages 005 à 008 ; migrations `001` (`numerotation_sequences`), `004`/`005b` (`bons_commande`, `bc_lignes`), `006_facturation.sql` (patron `factures` : snapshots, numéro, immuabilité), `007_reglements.sql`, `008_garanties.sql` ; tests 006 à 008 (infrastructure à réutiliser).
Le fichier `docs/conception/modèle-données-sqlite-v6-v3.13.md` **n'existe pas** : la V3.13 n'est que dans `fichiers-a-relire/MAJ__modèle-données-sqlite-v6-v3.13.md`.

Hiérarchie appliquée (celle des cadrages 006 à 008) : 1 décisions validées · 2 invariants · 3 modèle SQLite validé · 4 modèle métier · 5 errata · 6 CDC · 7 migrations existantes (référence technique réelle).

**Position sur la V3.13.** Comparaison mécanique (texte à texte) V3.12 officielle ↔ `MAJ__` sur le périmètre PV :

| Élément | V3.12 (`docs/`) | V3.13 (`MAJ__`) | Effet sur 009 |
|---|---|---|---|
| §4.11 `pv` (colonnes, CHECK, `UQ`, TR-41, immuabilité) | l.408-414 | l.534-540 | **identique** |
| TR-40, TR-41 (§8) ; index `pv(bc_id)`, `pv(origine_pv_id)` (§9) ; ligne « PV » du §10.2 | l.622-623, 656, 694 | l.784-785, 818, 856 | **identiques** |
| INV-26, 27, 30, 95, 96, 97, 131, 177 ; INV-20, 24, 07 | identiques | identiques | aucun |
| INV-32 | « figés dès l'INSERT (aucun brouillon) » | + « l'abandon d'une préparation ne crée aucun objet ; le numéro n'est attribué qu'à la validation (INV-185, INV-179) » | 009 suit la V3.13 (E-13/E-14 validés) |
| TR-01 (§8) | `numero` immuable | + « une fois attribué » (devis brouillon, PT-2) | sans effet sur `pv` (TR-40 couvre tout UPDATE) |
| Métier §22-23 ; CDC §23 ; audit fonctionnel §12 | identiques | identiques | aucun |
| INV-188 (BC annulé) | **absent** de `docs/` | présent | cité pour QO-1 |

→ Le DDL, les gardes et le comportement de `pv` **ne dépendent pas du statut de la V3.13**.

---

## 1. Règles déjà décidées (références exactes)

Fichiers cités : « Mod. » = `MAJ__modèle-données-sqlite-v6-v3.13.md` ; « Inv. » = `MAJ__invariants.md` ; « Mét. » = `MAJ__modèle-métier-V6.md` ; « CDC » = `MAJ__cdc-fonctionnel-architectural-v6.md`.

### 1.1 Entité et données
| Règle | Étiquette | Source |
|---|---|---|
| `pv` : `id` PK · `numero` UQ NN · `bc_id` NN FK→`bons_commande` · `type` NN · `date_reception` D NN · BLOC-SNAP (chantier, client, entreprise) · `observations` · `reserves` · `origine_pv_id` NULL FK→`pv` · `suffixe` INTEGER · `created_at` · +IMP | [RD] | Mod. §4.11 (l.536) ; Mét. §22 (l.584-598) |
| `pv.type ∈ {reception_sans_reserves, reception_avec_reserves, levee_reserves}` (liste fermée) | [RD] | Mod. §2.5 (l.139) ; Inv. — |
| CHECK `(type='levee_reserves') = (origine_pv_id IS NOT NULL) = (suffixe IS NOT NULL)` ; `suffixe BETWEEN 1 AND 99` | [RD] | Mod. §4.11 (l.538) ; INV-97 |
| CHECK `(reserves IS NOT NULL) = (type='reception_avec_reserves')` | [RD] | Mod. §4.11 (l.539) ; INV-97 ; Mét. §22 (« renseignées si et seulement si ») |
| `UQ(origine_pv_id, suffixe)` | [RD] | Mod. §4.11 (l.540) ; Mod. §8 (index uniques, l.799) ; INV-96 |
| BLOC-SNAP : trois snapshots `json_valid` NN + trois versions NN ; BLOC-IMP : `origine`, `legacy_id`, `legacy_data` (pas de `legacy_numero`, réservé aux clients et BC) | [RD] | Mod. §2.4 (l.114-115) ; INV-30, INV-136 |
| Pas de `statut`, pas de `cancelled_at`/`motif_annulation`, pas de `updated_at` | [RD] | Mod. §4.11 (liste de colonnes) ; Mod. §7.2 (l.745 : « aucune » modification) ; audit conservation §3.7 (l.240) |
| Aucune table fille (réserves = champ texte, sans numéro propre) | [RD] | audit conservation §3.7 (l.132 du fichier : « Non applicable ») |

### 1.2 Création, rattachement et nature de l'objet
| Règle | Étiquette | Source |
|---|---|---|
| Le PV est **facultatif** : il ne conditionne ni le solde, ni l'état Terminé, ni les garanties | [RD] | INV-95 ; Mét. §22 (l.602) ; CDC §23 ; audit fonctionnel §12 |
| **Plusieurs PV initiaux par BC ne sont pas interdits** | [RD] | Mod. §4.11 ; Mét. §22 (l.602) |
| Un PV appartient à un BC (`bc_id` NN) | [RD] | Mod. §4.11 |
| Aucun brouillon persistant : l'abandon avant validation ne crée aucun objet ; le numéro n'est attribué qu'à la validation | [RD] | INV-32 (V3.13) ; INV-185, INV-179 |
| Le PV est un objet **documentaire** (génération du PDF, arborescence `PV/`) : relève de la tranche Documents, pas de 009 | [RD][CT] | INV-108 ; Mod. §2.5 (`documents.type_entite` contient `pv`) ; D-34 |

### 1.3 Levée de réserves
| Règle | Étiquette | Source |
|---|---|---|
| La levée **n'est pas une modification** du PV initial : elle crée un **nouveau PV** | [RD] | Mét. §23 (l.610) ; CDC §23 |
| L'origine est un PV `reception_avec_reserves` **du même BC** ; **jamais de levée sur levée** | [RD] | INV-96 ; Mod. §4.11 (TR-41) ; Mét. §23 (l.612) |
| `suffixe = max + 1` par PV d'origine, dans la transaction | [RD] | INV-26 ; Mod. §4.11, §6 (l.710) |
| `numero` de la levée = `numero` de l'origine + `-` + suffixe sur 2 chiffres (`PVR-00001-26-01`, `-02`…) | [RD] | Mod. §4.11 ; Mét. §23 (l.613) ; CDC §23 ; E-04 |
| Le PV d'origine reste inchangé ; **la levée ne modifie pas le suivi interne des garanties** | [RD] | Mét. §23 (l.614) ; CDC §23 (l.711) ; audit §12 |
| Limite haute : 99 levées par origine (`suffixe ≤ 99`, numéro à 2 chiffres) | [RD] | Mod. §4.11 (CHECK) |

### 1.4 Immuabilité, suppression, FK
| Règle | Étiquette | Source |
|---|---|---|
| PV **immuable dès l'INSERT** : aucun UPDATE, aucun DELETE (TR-40) | [RD] | INV-96, INV-32 ; Mod. §4.11, §8 (l.784) ; Mét. §22 (l.604) ; CDC §23 |
| Aucune suppression physique d'un objet portant un numéro définitif (PVR inclus) ; annulation et refus ne libèrent jamais un numéro | [RD] | INV-06 ; INV-179 |
| FK en `RESTRICT`, sans `ON UPDATE` ; chaque `ON DELETE` examiné | [RD] | INV-05 ; D-44 |
| **Le seul rempart contre la réutilisation d'un suffixe est la non-suppression d'une levée** (aucune séquence) | [CT] | audit conservation §3.7 (l.241) |
| Garde de non-suppression **et** protection contre `INSERT OR REPLACE` dès la création de la table (`recursive_triggers=ON`) | [DV] | audit conservation C-7 (l.346) ; D-39 ; INV-07 ; précédents TR-21 (006), TR-50 (008) |
| `INSERT OR REPLACE` interdit par convention ; `INSERT OR IGNORE` permis seulement pour l'idempotence voulue (non pertinente pour `pv`) | [RD] | conv. §9 (l.347) ; INV-07 |

### 1.5 Numérotation
| Règle | Étiquette | Source |
|---|---|---|
| Format `PVR-nnnnn-yy`, séquence `PVR` par année, `yy` = année de `date_reception` | [RD] | Mod. §6 (l.709) ; INV-20 ; E-04 ; `type_objet` `PVR` déjà dans 001 (CHECK) |
| La levée **n'a ni séquence propre ni année propre** (« — ») | [RD] | Mod. §6 (l.710) ; audit conservation §3.7 (l.124 du fichier) |
| Chronologie TR-02 **non applicable** à PVR | [RD] | Mod. §6 (« Chronologie continue ») ; INV-24 ; cadrage 006 (l.697) |
| Plafond 99 999 : erreur explicite au-delà ; année supportée 2001-2099 pour les dates de numérotation, **au niveau du service, jamais un CHECK** (« réception du PV » est citée) | [RD][DV] | Mod. §6, §2.2 (l.85) ; INV-177 ; D-38 |
| Réservation du numéro : transaction propre, committée **avant** l'objet (`n = max(compteur, high-water) + 1`, `BEGIN IMMEDIATE`) ; trou accepté, jamais récupéré ni réutilisé | [DV] | PT-1 ; D-54 ; INV-22, 25, 179 ; Mod. §11.4 |

### 1.6 Import
| Règle | Étiquette | Source |
|---|---|---|
| Le bloc `pv` est accepté par le contrat d'import (rattachement des PV à un BC) ; **TR-40/TR-41 s'appliquent** ; aucune exemption de règle métier | [RD] | Mod. §10.2 (l.856), §10.3 (l.864), §10.1 ; INV-131 ; cadrage 008 §1.5 |
| Les PV `origine='import'` gardent le `numero` historique remis au client, **jamais transformé** ; seuls format, préfixe et année du numéro sont exemptés ; numéro non vide, unique, immuable | [RD][DV] | INV-27, INV-131 ; D-24 ; Mod. §6 (l.718), §10.4 |
| Les CHECK de format de `numero` sont conditionnés par `origine='v6'` | [RD] | Mod. §10.4 ; patron `factures` (006 l.129-134) |
| Les numéros historiques hors format V6 n'alimentent pas les séquences | [RD] | Mod. §10.6 |
| Ordre d'import : … règlements → **PV** → `sequences` → `anomalies` → recalcul des caches | [RD] | Mod. §10.5 (l.878) |

### 1.7 Position dans la chaîne
| Règle | Étiquette | Source |
|---|---|---|
| 009 = rang 12, après 008 (rang 11) ; `PRAGMA user_version = 12` posé par le runner dans la transaction de la migration | [DV] | D-34, D-55 ; Mod. §17.1 (l.1269) ; conv. §5 |
| 009 ne dépend d'aucune table de la tranche 010 ; `planning_evenements` n'est pas lu | [CT] | D-34 (ordre) ; INV-95 |

---

## 2. Périmètre exact de la tranche 009

**Dans 009** : 1 table `pv` (STRICT), 1 index explicite, 3 triggers (`BEFORE`). **Hors 009** (exclusions) :
- tranche **010 Planification** (non anticipée) ; `documents` (PDF des PV, `2026/PV/`), `historique` (événement de création), `urssaf_*`, paramètres : « traités dans leur contexte propre » (D-34) ;
- toute **règle de service** (§4) : numérotation, calcul du suffixe, contrôles préalables, borne d'année ;
- toute modification de 001 à 008 (immuables), de `bons_commande`, `factures`, `garanties`, `numerotation_sequences` ; aucun trigger posé sur ces tables ;
- le contrat d'import détaillé (P-04) et le convertisseur ;
- BATORYA Entreprise (non concerné).

**Contenu SQL** — esquisse du cadrage, **éprouvée sur une copie jetable en mémoire de la chaîne 001→008, hors dépôt** (SQLite 3.45.1) ; ce n'est **pas** le livrable `009_pv.sql` :

```sql
CREATE TABLE pv (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    numero                      TEXT    NOT NULL UNIQUE,
    bc_id                       INTEGER NOT NULL REFERENCES bons_commande (id) ON DELETE RESTRICT,
    type                        TEXT    NOT NULL CHECK (type IN ('reception_sans_reserves', 'reception_avec_reserves', 'levee_reserves')),
    date_reception              TEXT    NOT NULL CHECK (date_reception GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_reception) IS date_reception),
    -- BLOC-SNAP
    client_snapshot             TEXT    NOT NULL CHECK (json_valid(client_snapshot)),
    client_snapshot_version     INTEGER NOT NULL,
    entreprise_snapshot         TEXT    NOT NULL CHECK (json_valid(entreprise_snapshot)),
    entreprise_snapshot_version INTEGER NOT NULL,
    chantier_snapshot           TEXT    NOT NULL CHECK (json_valid(chantier_snapshot)),
    chantier_snapshot_version   INTEGER NOT NULL,
    observations                TEXT,
    reserves                    TEXT,
    origine_pv_id               INTEGER REFERENCES pv (id) ON DELETE RESTRICT,
    suffixe                     INTEGER,
    created_at                  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    -- BLOC-IMP
    origine                     TEXT    NOT NULL DEFAULT 'v6' CHECK (origine IN ('v6', 'import')),
    legacy_id                   TEXT,
    legacy_data                 TEXT    CHECK (legacy_data IS NULL OR json_valid(legacy_data)),

    UNIQUE (origine_pv_id, suffixe),
    CHECK (numero <> ''),
    CHECK ((type = 'levee_reserves') = (origine_pv_id IS NOT NULL)),
    CHECK ((origine_pv_id IS NOT NULL) = (suffixe IS NOT NULL)),
    CHECK (suffixe IS NULL OR suffixe BETWEEN 1 AND 99),
    CHECK ((reserves IS NOT NULL) = (type = 'reception_avec_reserves')),
    CHECK (origine <> 'v6' OR (legacy_id IS NULL AND legacy_data IS NULL)),
    -- [PR-3] PV initial V6 : PVR + 5 chiffres + année de date_reception ; la levée n'a pas de format propre (TR-41)
    CHECK (origine <> 'v6' OR type = 'levee_reserves'
           OR (numero GLOB 'PVR-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9]'
               AND substr(numero, 11, 2) = substr(date_reception, 3, 2))),
    CHECK (created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;

CREATE INDEX idx_pv_bc_id ON pv (bc_id);

CREATE TRIGGER tr_40_pv_no_update BEFORE UPDATE ON pv BEGIN SELECT RAISE(ABORT, 'INV-96: ...'); END;
CREATE TRIGGER tr_40_pv_no_delete BEFORE DELETE ON pv BEGIN SELECT RAISE(ABORT, 'INV-06: ...'); END;
CREATE TRIGGER tr_41_pv_insert BEFORE INSERT ON pv WHEN NEW.type = 'levee_reserves'
BEGIN
    -- G1 : origine = PV reception_avec_reserves (couvre « jamais de levée sur levée »)
    SELECT RAISE(ABORT, 'INV-96: ...') WHERE NOT EXISTS (SELECT 1 FROM pv o WHERE o.id = NEW.origine_pv_id AND o.type = 'reception_avec_reserves');
    -- G2 : même BC
    SELECT RAISE(ABORT, 'INV-96: ...') WHERE NOT EXISTS (SELECT 1 FROM pv o WHERE o.id = NEW.origine_pv_id AND o.bc_id IS NEW.bc_id);
    -- G3 : suffixe = max + 1 pour cette origine
    SELECT RAISE(ABORT, 'INV-26: ...') WHERE NEW.suffixe IS NOT (SELECT COALESCE(MAX(p.suffixe), 0) + 1 FROM pv p WHERE p.origine_pv_id = NEW.origine_pv_id);
    -- G4 : numero = numero de l'origine || '-' || suffixe sur 2 chiffres
    SELECT RAISE(ABORT, 'INV-26: ...') WHERE NOT EXISTS (SELECT 1 FROM pv o WHERE o.id = NEW.origine_pv_id AND NEW.numero = o.numero || '-' || printf('%02d', NEW.suffixe));
END;
```
*(Libellés exacts des messages : fixés à l'écriture du SQL, ASCII, préfixe `INV-nn` comme 006-008.)*

**Absences voulues** : `statut`, `cancelled_at`, `motif_annulation`, `updated_at`, `legacy_numero`, `client_id`, `devis_id`, `facture_id`, `garantie_id`, toute colonne de date de fin ou de levée, toute table fille. Les types (`INTEGER`/`TEXT`) sont ceux de 004/006. **Aucun** `INSERT`, `ALTER`, reconstruction, `BEGIN/COMMIT/PRAGMA`, aucune lecture/écriture de `numerotation_sequences`. 001→008 inchangés (empreinte `sqlite_master` testée).

---

## 3. Contraintes, index et triggers

### 3.1 Contraintes de table
| Contrainte | Étiquette | Justification / INV |
|---|---|---|
| NOT NULL : `numero`, `bc_id`, `type`, `date_reception`, 3 snapshots + 3 versions, `created_at`, `origine` | [RD] | Mod. §4.11 ; INV-30 |
| `UNIQUE(numero)` | [RD] | UQ NN ; INV-179 (rempart d'unicité des numéros) |
| `UNIQUE(origine_pv_id, suffixe)` — son index couvre la FK `origine_pv_id` | [RD] | INV-96 ; règle de tête du §9 |
| CHECK `type IN (3 valeurs)` ; `date_reception` : `GLOB` + `date(x) IS x`, **aucune borne d'année** | [RD] | Mod. §2.5, §2.2 ; INV-10, INV-177 |
| CHECK de cohérence levée ⇔ `origine_pv_id` ⇔ `suffixe` ; `suffixe` 1-99 | [RD] | INV-97 |
| CHECK `reserves` ⇔ `reception_avec_reserves` | [RD] | INV-97 |
| CHECK `numero <> ''` (tous les types, toutes origines) | [CT] | INV-131 « non vide » ; précédent 006 |
| CHECK format `numero` du **PV initial V6** + `yy` = année de `date_reception` ; **la levée n'a pas de CHECK de format** | [RD][PR-3] | INV-20 ; Mod. §6 ; INV-131 ; voir §4.4 et QO-2 |
| CHECK `origine='v6' ⇒ legacy_id, legacy_data NULL` ; `legacy_data` `json_valid` | [RD] | INV-136 |
| `created_at` : `GLOB` TS ; défaut `strftime(...,'now')` | [RD] | INV-10 |
| Snapshots : `json_valid` (comme 004/006) ; aucun CHECK sur les versions au-delà de NOT NULL | [CT] | cohérence avec 004/006 ; aucune règle documentée sur la valeur |
| FK : `bc_id` → `bons_commande`, `origine_pv_id` → `pv`, toutes `RESTRICT`, sans `ON UPDATE` | [RD] | INV-05, INV-06, INV-174 |
| `STRICT` | [CT] | conv. §5 / précédents |

### 3.2 Index
| Index | Étiquette | Justification |
|---|---|---|
| `idx_pv_bc_id (bc_id)` | [RD] | Mod. §9 (l.818) : un index par FK ; lecture « PV d'un BC » |
| ~~`pv(origine_pv_id)`~~ | [CT] | **redondant** : l'index de `UNIQUE(origine_pv_id, suffixe)` commence par `origine_pv_id` (règle de tête du §9, précédents 004 et 008-Z-5) — vérifié par `EXPLAIN QUERY PLAN` (utilise `sqlite_autoindex_pv_2`). Voir Z-5 |
| `UNIQUE(numero)` | [RD] | autoindex, pas d'index nommé |
| `pv(date_reception)` | non retenu | aucune source ne la prévoit |

### 3.3 Triggers (gardes pures `BEFORE`, `SELECT RAISE(ABORT,'INV-nn: …') WHERE …`, aucune écriture, **aucune exemption d'origine**, INV-131)
| Trigger | Événement | Garde | INV | Étiquette |
|---|---|---|---|---|
| `tr_40_pv_no_update` | BEFORE UPDATE | toujours refusé (même no-op ; couvre `UPDATE OR REPLACE/IGNORE` et `ON CONFLICT DO UPDATE`) | 96, 32 | [RD] TR-40 |
| `tr_40_pv_no_delete` | BEFORE DELETE | toujours refusé (couvre le DELETE implicite d'un `INSERT OR REPLACE` avec `recursive_triggers=ON`) | 96, 06 | [RD] TR-40 + [DV] C-7 |
| `tr_41_pv_insert` — **G1** | BEFORE INSERT, `WHEN type='levee_reserves'` | l'origine existe et est `reception_avec_reserves` (⇒ jamais de levée sur levée, ni sur un sans-réserves) | 96 | [RD] TR-41 |
| — **G2** | idem | l'origine appartient au **même BC** | 96 | [RD] TR-41 |
| — **G3** | idem | `suffixe = max(suffixe de l'origine) + 1` (1 si aucune levée) | 26 | [RD] TR-41 |
| — **G4** | idem | `numero = numero(origine) \|\| '-' \|\| printf('%02d', suffixe)` | 26 | [RD] TR-41, sous réserve de QO-2 pour `origine='import'` |

*Numérotation : `TR-40` et `TR-41` sont ceux du modèle ; aucun autre numéro n'est créé. Le nom `tr_40_pv_*` / `tr_41_pv_insert` n'est utilisé nulle part dans la chaîne 001→008 (vérifié). Le `TR-01` de `pv` est **subsumé** par TR-40 (aucun UPDATE du tout), comme pour `factures` (006).*

### 3.4 Protections anti-contournement (sondées sur la copie jetable)
Refusés : `UPDATE` (no-op compris), `DELETE`, `INSERT OR REPLACE` **par `id`, par `numero` et par `(origine_pv_id, suffixe)`** (recursive_triggers=ON), `DELETE` d'un BC référencé (FK `RESTRICT`), insertion multi-lignes dont une ligne est invalide (instruction annulée entièrement). Acceptés : plusieurs PV initiaux pour un même BC ; 99 levées successives ; `INSERT … VALUES` de 3 levées 1,2,3 en une seule instruction (les gardes voient les lignes déjà insérées de l'instruction). **Témoin documenté** : avec `recursive_triggers=OFF`, un `INSERT OR REPLACE` par `id` **remplace** un PV (`recursive_triggers=ON` est donc nécessaire, D-39 ; testé comme témoin, groupe E).

### 3.5 Conséquences techniques
- **CT-1** Aucune lecture de `bons_commande.statut`, de `factures`, `reglements`, `garanties` par les triggers : un PV est **indépendant** de l'état et de la facturation du BC (INV-95) ; voir QO-1.
- **CT-2** Aucun trigger n'est posé sur `bons_commande`, `factures`, `garanties` : leur immuabilité (004-008) suffit ; un PV, y compris une levée, n'écrit **jamais** dans `garanties` ni dans les caches du BC.
- **CT-3** G1 couvre à la fois « origine = avec réserves » et « pas de levée sur levée » : la seconde règle est un sous-cas de la première (message distinct impossible sans garde dédiée) ; la redondance est assumée, un seul garde, un seul libellé INV-96.
- **CT-4** Un BEFORE s'exécutant avant les CHECK, une levée dont `origine_pv_id` est NULL est refusée par G1 (INV-96) avant le CHECK de cohérence ; une origine inexistante est refusée par G1 (message trigger) et non par la FK. Aucun effet métier ; les tests acceptent l'un ou l'autre code selon le cas, avec la base témoin sans triggers pour éprouver chaque CHECK / FK isolément (leçon 007/008).
- **CT-5** G3 est correct sous `BEGIN IMMEDIATE` (un seul écrivain) ; le `UNIQUE` reste le rempart en cas de concurrence non maîtrisée.
- **CT-6** Plafond : la 100ᵉ levée d'une origine est refusée par le CHECK `suffixe ≤ 99` (message SQL brut) ; le **service** la traduit en erreur explicite **avant** toute écriture (§4.2).
- **CT-7** Un PV initial V6 daté de l'année 2100 ou 2000 (`yy = 00`) est accepté par le SQL (aucune borne d'année, D-38) ; il est refusé par le **service** et, de toute façon, impossible à numéroter (`annee = 0` réservé à CLI/FOU dans `numerotation_sequences`). Sondé.
- **CT-8** Une levée **V6** sur une origine **importée** (numéro libre) est possible avec le dispositif retenu : son numéro est `numero(origine) \|\| '-' \|\| suffixe`, sans format imposé (PR-3). Sondé.

---

## 4. Règles de service (ne passent pas en SQL) et interactions

### 4.1 Création d'un PV initial (service)
1. **Pré-contrôles avant toute réservation** : BC existant ; `type ∈ {sans_reserves, avec_reserves}` ; `reserves` fourni ⇔ avec réserves ; snapshots construits (INV-30) ; **année de `date_reception` ∈ 2001-2099** (INV-177, D-38) ; plafond 99 999 non atteint (erreur explicite).
2. **Réservation** du numéro `PVR-nnnnn-yy` (`yy` = année de `date_reception`) dans sa transaction propre committée (PT-1, D-54) ; le compteur ne décroît jamais.
3. `BEGIN IMMEDIATE` ; `INSERT` du PV (**`INSERT` simple, jamais `OR REPLACE` ni `OR IGNORE`**) ; `COMMIT`.
4. Échec avant réservation : aucun numéro consommé. Échec après réservation : le PV disparaît, le compteur garde un **trou**, jamais réutilisé (INV-179). Numérotation inchangée.
5. Aucune écriture sur `bons_commande`, `factures`, `garanties` (CT-2) ; aucun recalcul de cache.

### 4.2 Création d'une levée de réserves (service)
1. Pré-contrôles : origine existante, `reception_avec_reserves`, même BC ; `suffixe = max + 1` calculé dans la transaction ; **si `max = 99` : erreur métier explicite avant toute écriture** ; `numero = numero(origine) \|\| '-' \|\| suffixe(2)`.
2. **Aucune réservation de séquence** (la levée n'a pas de séquence) ; aucun high-water.
3. `INSERT` dans `BEGIN IMMEDIATE`. Un échec ne consomme donc **rien** : ni numéro, ni suffixe (le suffixe est recalculé à chaque tentative).
4. Le PV d'origine reste inchangé ; `garanties` inchangées.

### 4.3 Règles « non-effet » (testées)
Un PV (initial, avec ou sans réserves, levée) ne crée, ne modifie ni ne supprime : une facture, un règlement, une garantie, une ligne de BC, un cache de BC (`statut`, `avancement`, `montant_deja_facture_ht`, `date_100_facture`, `completed_at`, `updated_at`), une ligne de `numerotation_sequences` (par le SQL ; la réservation est un acte de service). La date de début du suivi des garanties n'est jamais déplacée par un PV ni par sa levée (Mét. §23 ; INV-87).

### 4.4 Import (INV-131)
Les PV importés traversent TR-40 (aucune mise à jour postérieure) et TR-41 comme toute écriture V6. Insertion **après** les BC (FK) et par `id` croissant des origines **avant** leurs levées (sinon G1 refuse), les levées d'une même origine par suffixe croissant 1, 2, 3… **sans trou** (G3). Le format du `numero` d'un PV initial `origine='import'` n'est pas contrôlé (non vide, unique). Pour une **levée**, la relation G4 est appliquée à toute origine — **c'est le point QO-2** (INV-27/D-24 « jamais transformé » vs TR-41).

### 4.5 Contrôles de cohérence (hors SQL, service / requêtes CK)
- **CK-01** (numéros uniques et au format V6 sauf devis/factures/PV importés) : pour `pv`, le format d'une **levée** est celui de la relation avec son origine, pas un format propre (Z-7).
- **CK-02** (séquences ≥ max des numéros au format V6) : seuls les PV **initiaux** `PVR-nnnnn-yy` alimentent le max ; les numéros de levée ne sont **pas** des numéros de séquence (Z-7).
- **CK-03** `foreign_key_check` couvre `pv`. Aucune nouvelle requête CK n'est créée par 009 ; la tranche **teste** les requêtes ci-dessus (lecture seule).

---

## 5. Cas limites et scénarios d'anomalie à couvrir
1. PV initial sans réserves / avec réserves ; `observations` NULL ; `reserves` vide `''` (QO-4) ; `reserves` sur un sans-réserves ou absentes sur un avec-réserves ⇒ refus.
2. Plusieurs PV initiaux sur un BC ; **deux PV de même `date_reception`** ; PV avant le solde, après le solde, sur BC `en_cours`, `termine`, `annule` (QO-1), BC sans facture.
3. Levée : sur sans-réserves ; sur levée ; sur origine d'un autre BC ; sur origine inexistante ; origine `NULL` avec suffixe ; suffixe 0, 2 avant 1, doublon, trou, 100 ; plusieurs origines sur un même BC (suffixes indépendants) ; levée multi-lignes ; levée dont le `numero` ne dérive pas de l'origine ; levées 1 à 99 puis 100ᵉ refusée.
4. Numérotation : yy ≠ année de `date_reception` ; format incorrect (préfixe, nombre de chiffres, séparateur) ; doublon ; levée de numéro identique à un PV initial ; PV initial `PVR-00001-26-01` (forme de levée) ⇒ refusé (type ≠ levée) ; année bissextile ; 29/02 ; `0000`, `2000`, `2100`, `9999` (SQL accepte, service refuse 2000/2100/9999 pour un PV V6).
5. Immuabilité : UPDATE de chaque colonne, no-op, `OR REPLACE/IGNORE`, UPSERT, DELETE (simple, multi-lignes), REPLACE par id / numero / (origine, suffixe), `recursive_triggers=OFF` (témoin).
6. FK : `bc_id` inexistant ; suppression d'un BC avec PV (TR-19 puis FK `RESTRICT` sur base **sans triggers**) ; suppression d'un PV origine ayant des levées ; identifiants volontairement distincts (`id` PV ≠ `bc_id` ≠ `origine_pv_id`).
7. Import : PV `origine='import'` avec numéro libre ; numéro vide refusé ; numéro identique à un PV V6 refusé ; levée importée avant son origine ; levée importée avec suffixe 2 sans 1 ; `legacy_*` sur `origine='v6'` refusé ; aucun `legacy_numero`.
8. Données malformées : snapshots non JSON / NULL / BLOB ; versions NULL ; dates `2026-1-1`, `2026-02-30`, `2026-13-01`, avec heure, `now`, NULL ; REAL/BLOB/NUL dans colonnes TEXT (STRICT) ; casse du `type`.
9. Atomicité de l'émission du PV (service émulé) : échec avant / après réservation, compteur PVR, aucun PV partiel.
10. Indépendance : empreintes avant/après de `bons_commande`, `bc_lignes`, `bc_ligne_garanties`, `factures`, `reglements`, **`garanties`** ; rejeu du scénario T-14 (avoir total, nouveau solde) avec un PV et une levée intercalés ⇒ garanties identiques champ par champ.

---

## 6. Tests (`test_009_pv.py`, T-51) — positifs, négatifs, limites, non-régression

**Infrastructure réutilisée** de 006/007/008 : `migrer11` + application de 009 au rang 12 (`BEGIN IMMEDIATE`, fichier, `user_version = 12`, `COMMIT`), `Base11`/`monde_g()`, `empreinte_base`, `emettre_solde`, `annuler_bc`/`terminer_bc`, `desynchroniser_ids`, base témoin sans triggers. Ajouts : fabrique de PV (initial, avec réserves, levée), **service émulé** `creer_pv()` / `creer_levee()` (pré-contrôles, réservation PT-1 dans une transaction committée, `BEGIN IMMEDIATE`, `INSERT` simple), oracle indépendant du numéro attendu (arithmétique sur chaînes, sans lire la ligne persistée). Aucune dépendance à `machine.db` (le high-water est émulé comme en 006).

| Groupe | Contenu |
|---|---|
| **A chaîne et structure** | 009 sur base 008 vide et peuplée ; `user_version = 12` ; 1 table STRICT, colonnes/ordre/NOT NULL/défauts exacts, **aucune** colonne statut/`cancelled_*`/`updated_at`/`legacy_numero` ; 1 index + 2 autoindex (`numero`, `(origine_pv_id, suffixe)`) ; 3 triggers ; aucune ligne insérée ; `foreign_key_list` = 2 `RESTRICT` sans `ON UPDATE` ; 001–008 inchangés (empreinte `sqlite_master`) ; `EXPLAIN QUERY PLAN` ; fichier sans `BEGIN/COMMIT/PRAGMA/INSERT` |
| **B CHECK de colonnes** | `type` (3 valeurs ; casse, espaces, vide, NULL, voisins refusés) ; `date_reception` (limites, 29/02, jours/mois invalides, `now`) ; levée ⇔ origine ⇔ suffixe (8 combinaisons) ; `suffixe` 0, 1, 99, 100, −1 ; `reserves` ⇔ avec réserves ; snapshots ; `numero` vide ; format V6 du PV initial (préfixe, chiffres, séparateur, `yy`) ; `created_at` ; `origine`/`legacy_*` ; NOT NULL ×12 |
| **C Numérotation** (service émulé) | PVR réservé par année (`yy` de `date_reception`) ; plusieurs PV même année ; changement d'année ; **levée : séquence PVR et `derniere_date` inchangées** ; aucune chronologie TR-02 (PV daté avant un PV déjà numéroté accepté) ; plafond 99 999 ⇒ erreur explicite, aucune réservation ; années 2000/2100 refusées par le service ; indépendance vis-à-vis de FAC/AVO |
| **D Levée (TR-41)** | G1 (sans réserves, levée, origine inexistante) ; G2 (autre BC) ; G3 (1, 2…99 ; trou ; doublon ; 100 ; deux origines indépendantes ; insertion multi-lignes) ; G4 (numéro incohérent, bon numéro) ; plusieurs PV initiaux ; max calculé sur une base alimentée sans trigger (témoin) |
| **E Immuabilité (TR-40)** | UPDATE de **chaque** colonne, no-op, `OR REPLACE/IGNORE`, UPSERT ; DELETE ; REPLACE ×3 ; `recursive_triggers=OFF` (témoin documenté) ; code `INV-96`/`INV-06` ; aucune modification résiduelle ; `sqlite_sequence` |
| **F FK et suppression des parents** | `bc_id` inexistant ; DELETE de `bons_commande` et de PV origine refusés (avec et sans triggers) ; ids distincts ; `origine_pv_id` RESTRICT |
| **G Indépendance** (CT-1, CT-2, §4.3) | empreintes avant/après de toutes les tables hors `pv` ; PV sur BC `en_cours`/`termine`/`annule` selon QO-1 ; PV avant/après solde ; **garanties intactes** après PV et levée (dont T-14) ; caches du BC intacts ; le PV ne conditionne ni solde, ni Terminé |
| **H Import** | PV importés (numéro libre, `legacy_id`) ; mêmes gardes pour toute origine (INV-131) ; levée importée (ordre, suffixes consécutifs, numéro selon QO-2) ; unicité ; `origine='v6' ⇒ legacy_* NULL` |
| **I Diagnostics** | requêtes CK-01/CK-02 exprimées pour `pv` (levée exclue du max de séquence) ; lecture seule (empreinte avant/après) ; base alimentée en SQL direct (triggers retirés) ⇒ détection |
| **J Non-régression** | suites 001→008 inchangées (**1598 tests**) ; texte des triggers 001–008 identique ; chaîne rejouée sur base vide et peuplée ; 009 n'écrit ni ne lit les autres tables (empreintes) |
| **K Données malformées / contournements** | BLOB, REAL, INTEGER dans colonnes TEXT (STRICT), NUL, espaces, casse ; années extrêmes ; `recursive_triggers=OFF` (témoin) |
| **L Atomicité** | `INSERT` multi-lignes partiellement invalide ⇒ rien ; `SAVEPOINT`/`ROLLBACK` ; **émission du PV** : échec avant réservation (compteur inchangé) / après réservation (compteur +1, trou jamais réutilisé, aucun PV) ; échec d'une levée ⇒ aucun suffixe consommé ; avant/après (empreinte complète) à chaque scénario d'échec |

Chaque test d'échec vérifie **les données persistées et l'état de la base avant/après** (pas seulement l'exception). Nommage des méthodes : `test_T51_<groupe>_<comportement>` (pratique 006-008 ; Z-9). **Volume visé : 170 à 230 tests** (1 table, 1 index, 3 triggers : moins de surface que 008, pas de post-condition C1-C8).
**Mutation** (phase suivante, après validation et livraison SQL + tests, comme en 007/008) : mutants du seul `009_pv.sql` — listes `IN`, bornes `1`/`99`/`+ 1`, `COALESCE(...,0)`, `WHEN`, `GLOB`, `substr(numero, 11, 2)`/`substr(date_reception, 3, 2)`, `IS`/`=`, `WHERE` de G1 à G4, `printf('%02d')`, ordre des gardes, `DROP INDEX`, `STRICT`, FK ; chaque survivant qualifié individuellement (équivalent démontré ou test manquant) ; **non lancée ici**. Équivalents prévisibles à qualifier : `FOR EACH ROW`, conjoncts redondants entre CHECK de cohérence (levée ⇔ origine ⇔ suffixe), redondance G1/CHECK, `IS` vs `=` sur colonnes NOT NULL.

---

## 7. Contradictions et lacunes documentaires

| # | Source / section | Constat | Conséquence pour 009 | Correction minimale proposée |
|---|---|---|---|---|
| Z-1 | `docs/conception/` | La V3.13 n'existe que dans `fichiers-a-relire/` ; `docs/` contient la V3.12 ; `invariants.md` officiel est antérieur (INV-188 absent ; INV-32, INV-06, INV-23, INV-05 différents) | Aucune dépendance bloquante : règles PV identiques (§0) | Reporter les `MAJ__*` dans `docs/` (hors 009, à votre main) |
| Z-2 | Mod. §17.1 (« Prochaine tranche métier : 006 … en cadrage », rangs 9-11 « prévue / non créée ») ; conv. §5 (rangs 5-7 « prévue, non créée », 9-11 « prévue ») | Le suivi des migrations n'est pas à jour : 005, 005a, 005b, 006, 007 (et 008, en copie de travail) existent | Aucun effet technique ; la chaîne réelle est 001→008 (user_version 11) | Mettre à jour §17.1 et conv. §5 à la validation de 009 (hors cadrage) |
| Z-3 | Mét. §2.4 (l.81) : le PV est rangé parmi les objets « jamais supprimés … annulés (date et motif) lorsque l'objet est annulable (devis, BC, dépense, règlement), ou corrigé par un document opposé » | Le modèle **ne prévoit aucune annulation de PV** et aucun « document opposé » pour un PV : **aucun mécanisme n'est documenté pour corriger un PV erroné** (audit conservation X-9, déjà signalé « mineur ») | Aucun effet SQL (immuable, pas de statut) ; voir QO-5 | Clarifier le métier §2.4 : un PV erroné n'est ni annulé ni modifié (QO-5) |
| Z-4 | Mét. §23 / Mod. §4.11 | Aucune règle de **levée partielle** : une levée n'a pas de `reserves` (CHECK INV-97 : `reserves` NULL hors « avec réserves »), plusieurs levées par origine sont possibles (`suffixe` 1-99) mais le modèle ne dit ni quelles réserves chacune lève, ni quand la levée est « complète » | Aucun effet SQL ; rien n'est inventé | Information : la nature des réserves levées se lit dans `observations` (texte libre) ; à préciser côté métier si nécessaire |
| Z-5 | Mod. §9 (l.818) : `pv(origine_pv_id)` | La liste impose un index que la règle de tête du même §9 rend redondant (`UNIQUE(origine_pv_id, suffixe)` commence par la FK) — même cas que `garanties(bc_ligne_id)` (008 Z-5) | 1 index explicite au lieu de 2 | Retirer `pv(origine_pv_id)` de la liste |
| Z-6 | Mod. §8, TR-01 (liste `pv`) | TR-01 (« numéro immuable ») est subsumé par TR-40 (aucun UPDATE) | Pas de trigger TR-01 spécifique sur `pv` | Annoter TR-01 : « pv couvert par TR-40 » |
| Z-7 | Mod. §14 (CK-01, CK-02) ; INV-20 | Non dit comment CK-01/CK-02 traitent une **levée** (`PVR-00001-26-01`) : ce n'est pas un numéro de séquence ; CK-02 doit l'exclure du « max des numéros au format V6 » | §4.5 : seuls les PV initiaux alimentent le max ; levée contrôlée par la relation avec l'origine | Préciser CK-01/CK-02 dans le modèle |
| Z-8 | INV-27 / D-24 / Mod. §10.4 (« numéro historique **jamais transformé** ; exemption : format, préfixe, année ») **vs** TR-41 / Mod. §4.11 (« numéro de la levée = numéro de l'origine + `-` + suffixe ») | Pour un PV importé : si le numéro historique d'une levée n'est pas `numero(origine) + '-' + suffixe`, ou si une levée **V6** est créée sur une origine **importée** (dont le numéro ne suit pas le format V6), les deux règles ne sont pas conciliables telles quelles | Point **QO-2** : défaut retenu (PR-3) = relation G4 appliquée à toute origine, **pas de format propre** pour la levée | Trancher QO-2 puis préciser §4.11/§10.4 |
| Z-9 | Conv. §7 (méthodes de test nommées `test_INV_xx_…`) vs pratique 006-008 (`test_T<nn>_<groupe>_…`) | Deux conventions de nommage | Aucune ; 009 suit 006-008 | Aligner conv. §7 sur la pratique |
| Z-10 | Mod. §2.2 / INV-177 : « réception du PV » dans la liste des dates de numérotation | Ne distingue pas le PV initial (numéroté) de la levée (pas de `yy` propre) : la borne 2001-2099 vise-t-elle aussi `date_reception` d'une levée ? | Aucun effet SQL (service) ; par défaut la borne ne porte que sur la date du PV **initial** (seule date qui détermine un `yy`) | Préciser INV-177 |
| Z-11 | Mod. §4.10 / §23 Mét. vs 008 | « Un PV ou sa levée ne modifient pas une garantie » : 008 le garantit en n'ayant aucun lien avec `pv` | 009 n'introduit aucune lecture/écriture croisée ; testé (groupe G) | Aucune |

Aucune de ces lacunes ne contredit le **DDL** ni le **comportement** documentés de `pv`, sauf Z-8 (point d'arbitrage QO-2).

---

## 8. Questions ouvertes et propositions

### Propositions [PR] (valeur par défaut retenue ; à confirmer ou infirmer)
- **PR-1** *1 seul index explicite* (`idx_pv_bc_id`) ; `pv(origine_pv_id)` assuré par l'index de l'`UNIQUE` (Z-5).
- **PR-2** *3 triggers* : `tr_40_pv_no_update`, `tr_40_pv_no_delete`, `tr_41_pv_insert` (G1-G4). Aucun trigger sur d'autres tables.
- **PR-3** *Format de `numero`* : CHECK de format `origine='v6'` **réservé au PV initial** (préfixe, 5 chiffres, `yy` = année de `date_reception`) ; **la levée n'a pas de CHECK de format** : son numéro est imposé par G4 (relation avec l'origine), ce qui rend possible une levée V6 sur une origine importée (CT-8).
- **PR-4** *Pas de lecture du statut du BC* dans les triggers (CT-1) ; voir QO-1.

### Questions ouvertes [QO]
- **QO-1 — PV et état du BC.** Un PV peut-il être créé sur un BC `annule` ? sur un BC `termine` ? sur un BC sans aucune facture ? **Non documenté** : INV-95 dit seulement que le PV ne conditionne rien ; INV-188 interdit sur BC annulé « un nouvel acompte, une nouvelle situation, un nouveau solde, un nouveau devis » et autorise avoirs et dépenses, sans citer le PV. *Par défaut : aucune garde en SQL (ni en service tant que rien n'est décidé).*
- **QO-2 — Numéro d'une levée importée / levée V6 sur origine importée (Z-8).** (a) *Défaut PR-3 / lecture littérale de TR-41* : G4 s'applique à **toute** origine ; l'import d'une levée dont le numéro ne dérive pas de son origine est **rejeté** (le convertisseur la normalise ou la déclare `non_importe`) ; (b) *variante* : G4 limité à `origine='v6'`, numéro libre (non vide, unique) pour une levée importée, mais alors une levée V6 sur origine importée garderait G4. Les deux gardent G1-G3 pour toute origine. **À trancher avant l'écriture du SQL** (modifie G4 et le test H).
- **QO-3 — Cohérence de dates.** Aucune règle documentée entre `date_reception` d'une levée et celle de son origine (levée ≥ origine ?), entre `date_reception` et la date de création/solde du BC, ni contre une date future. *Par défaut : aucune garde (SQL ni service), conformément à « aucune borne autre que la validité calendaire » (INV-177).*
- **QO-4 — `reserves` non vide.** « Renseignées » (Mét. §22) implique-t-il `reserves <> ''` (et sans espaces seuls) ? Le CHECK documenté exige seulement `reserves IS NOT NULL`. *Par défaut : pas de CHECK supplémentaire (un `''` est accepté par le SQL, testé comme limite) ; le service/l'UI peut exiger un texte non vide si vous le décidez.*
- **QO-5 — Correction d'un PV erroné (Z-3).** Aucun mécanisme documenté (ni annulation, ni document opposé). La seule voie possible aujourd'hui est la création d'un **nouveau PV initial** (« plusieurs PV initiaux par BC ne sont pas interdits »), l'erroné restant en base. À confirmer ; **aucun effet SQL**, hors 009.

### Points bloquants
**Aucun point bloquant.** **QO-2 doit être tranchée avant l'écriture du SQL** (elle modifie G4 et les tests d'import) ; QO-1, QO-3 et QO-4 sont sans effet SQL si le défaut est confirmé ; QO-5 est hors SQL.

---

## 9. Critères d'acceptation de la tranche 009
1. `009_pv.sql` contient exactement : 1 table `pv` STRICT, `idx_pv_bc_id`, `tr_40_pv_no_update`, `tr_40_pv_no_delete`, `tr_41_pv_insert` ; **rien d'autre** (§2) ; aucune modification de 001-008.
2. `PRAGMA user_version = 12` sur la chaîne 001→009 ; `foreign_key_check` vide ; `integrity_check` ok ; empreinte `sqlite_master` de 001-008 inchangée.
3. `test_009_pv.py` (T-51) : tous les groupes A à L du §6 verts ; chaque scénario d'échec vérifie l'état persisté avant/après ; **suites 001→008 inchangées et vertes (1598 tests)**.
4. G1 à G4, CHECK de cohérence, immuabilité et les trois variantes de `REPLACE` éprouvés ; plafond 99 levées ; plusieurs PV initiaux ; PV sans effet sur BC, factures, règlements, **garanties** (empreintes).
5. Les points QO-1 à QO-5 sont arbitrés (ou leur défaut confirmé) avant écriture ; aucune règle non documentée n'est introduite.
6. Campagne de mutation sur le seul `009_pv.sql` : **0 survivant non qualifié** (conv. §7.1) ; rapport `RAPPORT_MUTATION__009_pv.md` ; toute lacune de test corrigée par des tests, jamais en modifiant le SQL sans repasser par le cadrage.
7. Rapport final détaillé pour revue indépendante ; **validation finale conditionnée à la revue** ; aucun push par l'agent (vous poussez vous-même).

---

## Conclusion
**Cadrage prêt à relire.** Le périmètre SQL est petit et entièrement documenté : une table, un index, trois triggers (TR-40 ×2, TR-41). Les règles PV sont **identiques en V3.12 et V3.13**. Un seul arbitrage conditionne l'écriture du SQL (**QO-2**, numéro d'une levée sur/dans un contexte importé) ; quatre autres questions n'ont d'effet SQL que si vous décidez d'ajouter une garde. Un PV, levée comprise, n'agit sur aucune autre table, en particulier les garanties. Aucune implémentation n'est commencée.

## Livraison
Ce seul fichier : `fichiers-a-relire/CADRAGE__009_pv.md`. Aucun `009_pv.sql`, aucun test, aucun rapport de mutation, aucun document officiel ou migration modifié ; V3.13 non déplacée. Les sondes SQL citées (§2, §3.4, CT-4, CT-7, CT-8) ont été exécutées sur une copie jetable **en mémoire**, hors dépôt (scratchpad) ; aucun test du dépôt n'a été exécuté pour ce cadrage. Aucun push effectué (vous poussez vous-même).
