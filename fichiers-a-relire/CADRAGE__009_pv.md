# CADRAGE 009 — PV (procès-verbaux de réception)

Tranche 009 (rang 12) : future `src-tauri/migrations/metier/009_pv.sql` + `src-tauri/tests/metier/test_009_pv.py` (T-51). **Ce document est un cadrage : aucun fichier SQL, test, rapport de mutation ou document officiel n'est créé ou modifié.**
Statut : **cadrage corrigé après audit contradictoire (révision du 2026-10-09), en attente de relecture et de validation par Rémy avant toute écriture du SQL et des tests.** Dépôt lu : `main` @ `a9fd50f` ; les fichiers 008 (`008_garanties.sql`, `test_008_garanties.py`, `CADRAGE__008_garanties.md`, `RAPPORT_MUTATION__008_garanties.md`) sont lus dans la copie de travail (non encore poussés par Rémy, donc non présents dans `main`).

Légende des étiquettes :
**[RD]** règle documentée · **[DV]** décision déjà validée (errata, cadrages 006/007/008, D-xx) · **[CT]** conséquence technique (déduite, aucune règle nouvelle) · **[PR]** proposition à arbitrer · **[QO]** question ouverte.
*Toute règle non documentée est signalée comme telle et n'est pas transformée en règle : la valeur par défaut d'une [QO] est toujours « aucune règle ajoutée ».*
*Les informations communiquées par Rémy après l'audit sont marquées **(info Rémy)** : ce sont des données de contexte, ni des règles documentées ni des décisions validées ; elles ne portent aucune étiquette de règle.*

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

**Révision après audit contradictoire (2026-10-09).** Ce cadrage a été corrigé à la suite de l'audit (étiquettes, classification des lacunes, requalification de QO-1 à QO-5 et de Z-8). Les règles normatives et les documents officiels ne sont pas modifiés.
**(info Rémy) La V2 ne contient aucun PV ; aucun PV historique n'est importé depuis la V2.** Vérification documentaire : aucune source lue n'affirme explicitement l'absence de PV en V2 ; plusieurs la contredisent implicitement en décrivant des PV V2 importés — INV-160 (retiré ; `MAJ__invariants.md` l.275, `docs/conception/invariants.md` l.240 : « PV V2 sans BC (`refDevis` absent ou devis non accepté) → quarantaine ; numéro V2 conservé »), `MAJ__audit-fonctionnel-v5.16-v6.md` l.409 (le convertisseur porte « … paiements, PV, compteurs historiques … »), Mod. V3.13 l.856 (ligne « PV » du contrat d'import), l.1226 (« Numéro de PV initial sans suffixe (V2) »), D-17 (« conformité PV »), et INV-27 / D-24 / INV-131 (PV `origine='import'`). Cette divergence est **signalée, non corrigée** (documents hors périmètre). Le cadrage retient l'information de Rémy pour qualifier Z-8 ; il conserve `origine`/`legacy_*` et les règles INV-131 du modèle, sans rien supprimer du contrat d'import.

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
| `recursive_triggers=ON` à la connexion, nécessaire pour que le DELETE implicite d'un `INSERT OR REPLACE` déclenche la garde de non-suppression | [DV] | D-39 ; INV-07 ; INV-174 |
| Garde de non-suppression **et** protection contre `INSERT OR REPLACE` posées dès la création de la table : **recommandation** de l'audit de conservation (C-7), pas une décision validée ; de fait couverte par TR-40 (DELETE interdit, [RD]) ; précédents TR-21 (006), TR-50 (008) | [PR] | audit conservation C-7 (l.346) ; TR-40 |
| `INSERT OR REPLACE` interdit par convention ; `INSERT OR IGNORE` permis seulement pour l'idempotence voulue (non pertinente pour `pv`) | [RD] | conv. §9 (l.347) ; INV-07 |

### 1.5 Numérotation
| Règle | Étiquette | Source |
|---|---|---|
| Format `PVR-nnnnn-yy`, séquence `PVR` par année, `yy` = année de `date_reception` | [RD] | Mod. §6 (l.709) ; INV-20 ; E-04 ; `type_objet` `PVR` déjà dans 001 (CHECK) |
| La levée **n'a ni séquence propre ni année propre** (« — ») | [RD] | Mod. §6 (l.710) ; audit conservation §3.7 (l.124 du fichier) |
| Chronologie TR-02 **non applicable** à PVR | [RD] | Mod. §6 (« Chronologie continue ») ; INV-24 ; cadrage 006 (l.697) |
| Plafond 99 999 : erreur explicite au-delà ; année supportée 2001-2099 pour les dates de numérotation, **au niveau du service, jamais un CHECK** (« réception du PV » est citée ; la levée, qui n'a pas d'année propre, n'est pas mentionnée : Z-10) | [RD][DV] | Mod. §6, §2.2 (l.85) ; INV-177 ; D-38 |
| Réservation du numéro : transaction propre, committée **avant** l'objet (`n = max(compteur, high-water) + 1`, `BEGIN IMMEDIATE`) ; trou accepté, jamais récupéré ni réutilisé | [DV] | PT-1 ; D-54 ; INV-22, 25, 179 ; Mod. §11.4 |

### 1.6 Import
| Règle | Étiquette | Source |
|---|---|---|
| Le bloc `pv` est accepté par le contrat d'import (rattachement des PV à un BC) ; **TR-40/TR-41 s'appliquent** ; aucune exemption de règle métier | [RD] | Mod. §10.2 (l.856), §10.3 (l.864), §10.1 ; INV-131 ; cadrage 008 §1.5 |
| Les PV `origine='import'` gardent le `numero` historique remis au client, **jamais transformé** ; seuls format, préfixe et année du numéro sont exemptés ; numéro non vide, unique, immuable | [RD][DV] | INV-27, INV-131 ; D-24 ; Mod. §6 (l.718), §10.4 |
| Les CHECK de format de `numero` sont conditionnés par `origine='v6'` ; **leur application à la levée n'est pas spécifiée** (Mod. §4.11 ne liste aucun CHECK de format pour `pv` ; Z-8) | [RD] pour le principe | Mod. §10.4 (l.873) ; INV-131 ; patron `factures` (006 l.129-134) |
| Les numéros historiques hors format V6 n'alimentent pas les séquences | [RD] | Mod. §10.6 |
| Ordre d'import : … règlements → **PV** → `sequences` → `anomalies` → recalcul des caches | [RD] | Mod. §10.5 (l.878) |
| (info Rémy) La V2 ne contient aucun PV : aucun PV historique n'est importé depuis la V2 ; le contrat d'import conserve néanmoins un bloc `pv` et `origine='import'` | — | communication de Rémy (2026-10-09), hors sources ; divergence avec INV-160 (retiré), audit fonctionnel l.409, Mod. l.1226 : voir §0 et Z-8 |

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

**Contenu SQL** — esquisse du cadrage, **éprouvée sur une copie jetable en mémoire de la chaîne 001→008, hors dépôt** (SQLite 3.45.1) ; ce n'est **pas** le livrable `009_pv.sql`, et cette épreuve **ne vaut pas preuve de conformité documentaire** (§3.6) :

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
    -- [RD] format du PV initial V6 (INV-20, Mod. §10.4) ; [PR-3] aucun CHECK de format ajouté pour la levée (traitement non spécifié ; son numéro est dérivé par G4)
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
| `UNIQUE(origine_pv_id, suffixe)` | [RD] | INV-96 ; Mod. §4.11 (l.540). Que son index couvre aussi la FK `origine_pv_id` est une proposition technique (PR-1, Z-5) |
| CHECK `type IN (3 valeurs)` ; `date_reception` : `GLOB` + `date(x) IS x`, **aucune borne d'année** | [RD] | Mod. §2.5, §2.2 ; INV-10, INV-177 |
| CHECK de cohérence levée ⇔ `origine_pv_id` ⇔ `suffixe` ; `suffixe` 1-99 | [RD] | INV-97 |
| CHECK `reserves` ⇔ `reception_avec_reserves` | [RD] | INV-97 |
| CHECK `numero <> ''` (tous les types, toutes origines) | [CT] | INV-131 « non vide » ; précédent 006 |
| CHECK de format `numero` d'un **PV initial V6** (`PVR-nnnnn-yy`) + `yy` = année de `date_reception` | [RD] | INV-20 ; Mod. §6 (l.709) ; Mod. §10.4 (« CHECK de format … conditionnés par `origine='v6'` … `pv` ») ; INV-131 ; Mod. §4.11 ne le liste pas |
| **Levée** : aucun CHECK de format ajouté (son numéro est dérivé par G4). INV-20 cite le format de levée `PVR-00001-yy-01`, mais ni Mod. §4.11 ni §10.4 ne dit comment le CHECK de format s'applique à la levée : traitement **non spécifié** | [PR-3] | INV-20 ; Mod. §4.11 ; Z-8 |
| CHECK `origine='v6' ⇒ legacy_id, legacy_data NULL` ; `legacy_data` `json_valid` | [RD] | INV-136 |
| `created_at` : `GLOB` TS ; défaut `strftime(...,'now')` | [RD] | INV-10 |
| Snapshots : `json_valid` (comme 004/006) ; aucun CHECK sur les versions au-delà de NOT NULL | [CT] | cohérence avec 004/006 ; aucune règle documentée sur la valeur |
| FK : `bc_id` → `bons_commande`, `origine_pv_id` → `pv`, toutes `RESTRICT`, sans `ON UPDATE` | [RD] | INV-05, INV-06, INV-174 |
| `STRICT` | [CT] | conv. §5 / précédents |

### 3.2 Index
| Index | Étiquette | Justification |
|---|---|---|
| `idx_pv_bc_id (bc_id)` | [RD] | Mod. §9 (l.818) : un index par FK ; lecture « PV d'un BC » |
| ~~`pv(origine_pv_id)`~~ | [CT][PR-1] | **redondant** : l'index de `UNIQUE(origine_pv_id, suffixe)` commence par `origine_pv_id` (règle de tête du §9, précédents 004 et 008-Z-5) — vérifié par `EXPLAIN QUERY PLAN` (utilise `sqlite_autoindex_pv_2`). Voir Z-5 |
| `UNIQUE(numero)` | [RD] | autoindex, pas d'index nommé |
| `pv(date_reception)` | non retenu | aucune source ne la prévoit |

### 3.3 Triggers (gardes pures `BEFORE`, `SELECT RAISE(ABORT,'INV-nn: …') WHERE …`, aucune écriture, **aucune exemption d'origine**, INV-131)
| Trigger | Événement | Garde | INV | Étiquette |
|---|---|---|---|---|
| `tr_40_pv_no_update` | BEFORE UPDATE | toujours refusé (même no-op ; couvre `UPDATE OR REPLACE/IGNORE` et `ON CONFLICT DO UPDATE`) | 96, 32 | [RD] TR-40 |
| `tr_40_pv_no_delete` | BEFORE DELETE | toujours refusé (couvre le DELETE implicite d'un `INSERT OR REPLACE` avec `recursive_triggers=ON`) | 96, 06 | [RD] TR-40 (C-7 : recommandation [PR], §1.4) |
| `tr_41_pv_insert` — **G1** | BEFORE INSERT, `WHEN type='levee_reserves'` | l'origine existe et est `reception_avec_reserves` (⇒ jamais de levée sur levée, ni sur un sans-réserves) | 96 | [RD] TR-41 |
| — **G2** | idem | l'origine appartient au **même BC** | 96 | [RD] TR-41 |
| — **G3** | idem | `suffixe = max(suffixe de l'origine) + 1` (1 si aucune levée) | 26 | [RD] TR-41 |
| — **G4** | idem | `numero = numero(origine) \|\| '-' \|\| printf('%02d', suffixe)` | 26 | [RD] TR-41 (Mod. §4.11 : aucune condition sur `origine`) ; aucune exemption d'origine (INV-131) [CT] ; cas `origine='import'` : Z-8 (non spécifié, hors périmètre de migration) |

*Numérotation : `TR-40` et `TR-41` sont ceux du modèle ; aucun autre numéro n'est créé. Le nom `tr_40_pv_*` / `tr_41_pv_insert` n'est utilisé nulle part dans la chaîne 001→008 (vérifié). Le `TR-01` de `pv` est **subsumé** par TR-40 (aucun UPDATE du tout), comme pour `factures` (006) : [CT], proposition technique (PR-6, Z-6).*

### 3.4 Protections anti-contournement (sondées sur la copie jetable ; limites au §3.6)
Refusés : `UPDATE` (no-op compris), `DELETE`, `INSERT OR REPLACE` **par `id`, par `numero` et par `(origine_pv_id, suffixe)`** (recursive_triggers=ON), `DELETE` d'un BC référencé (FK `RESTRICT`, sur base **sans** les triggers de `bons_commande`), insertion multi-lignes `VALUES` dont une ligne est invalide (instruction annulée entièrement). Acceptés : plusieurs PV initiaux pour un même BC ; 99 levées successives ; `INSERT … VALUES` de 3 levées 1,2,3 en une seule instruction (les gardes voient les lignes déjà insérées de l'instruction). **Témoin documenté** : avec `recursive_triggers=OFF`, un `INSERT OR REPLACE` par `id` **remplace** un PV (`recursive_triggers=ON` est donc nécessaire, D-39 ; testé comme témoin, groupe E).

### 3.5 Conséquences techniques
- **CT-1** Aucune lecture de `bons_commande.statut`, de `factures`, `reglements`, `garanties` par les triggers : un PV est **indépendant** de l'état et de la facturation du BC (INV-95) ; voir QO-1.
- **CT-2** Aucun trigger n'est posé sur `bons_commande`, `factures`, `garanties` : leur immuabilité (004-008) suffit ; un PV, y compris une levée, n'écrit **jamais** dans `garanties` ni dans les caches du BC.
- **CT-3** G1 couvre à la fois « origine = avec réserves » et « pas de levée sur levée » : la seconde règle est un sous-cas de la première (message distinct impossible sans garde dédiée) ; la redondance est assumée, un seul garde, un seul libellé INV-96.
- **CT-4** Un BEFORE s'exécutant avant les CHECK, une levée dont `origine_pv_id` est NULL est refusée par G1 (INV-96) avant le CHECK de cohérence ; une origine inexistante est refusée par G1 (message trigger) et non par la FK. Aucun effet métier ; les tests acceptent l'un ou l'autre code selon le cas, avec la base témoin sans triggers pour éprouver chaque CHECK / FK isolément (leçon 007/008).
- **CT-5** G3 est correct sous `BEGIN IMMEDIATE` (un seul écrivain) ; le `UNIQUE` reste le rempart en cas de concurrence non maîtrisée.
- **CT-6** [RD] Plafond : la 100ᵉ levée d'une origine est refusée par le CHECK `suffixe ≤ 99` (message SQL brut ; Mod. §4.11). Une traduction par le service en erreur explicite avant écriture serait une **proposition non validée** (PR-5) : aucune source ne l'impose.
- **CT-7** Un PV initial V6 daté de l'année 2100 ou 2000 (`yy = 00`) est accepté par le SQL (aucune borne d'année, D-38) ; il est refusé par le **service** et, de toute façon, impossible à numéroter (`annee = 0` réservé à CLI/FOU dans `numerotation_sequences`). Sondé.
- **CT-8** Levée **V6** sur une origine `origine='import'` à numéro libre : cas **non spécifié** (Z-8), hors périmètre de migration (info Rémy : aucun PV en V2). Le dispositif ne l'interdit pas et n'ajoute aucune exemption : G4 en dérive le numéro (`numero(origine) \|\| '-' \|\| suffixe`), sans CHECK de format sur la levée (PR-3). Comportement constaté par sonde (sans valeur documentaire), pas une règle.

### 3.6 Limites des sondes et vérifications techniques
Les sondes (§2, §3.4, CT-4, CT-7, CT-8) ont été exécutées sur une copie jetable en mémoire, hors dépôt. Elles éclairent le comportement de SQLite pour l'esquisse ; elles **ne prouvent ni la conformité documentaire ni la validité de la future migration**, qui reposent sur les sources citées, sur la relecture de Rémy, puis sur les tests et la mutation de la phase suivante. Limites connues :
- `INSERT … SELECT` et UPSERT (`ON CONFLICT DO UPDATE / DO NOTHING`) sur `pv` : **non sondés** (seul `INSERT … VALUES`, mono et multi-lignes, l'a été) ; à examiner en phase de tests.
- Les conclusions sur `INSERT OR REPLACE` **dépendent de `recursive_triggers=ON`** (D-39, posé à la connexion) : avec `OFF`, un `INSERT OR REPLACE` par `id` remplace un PV (témoin, groupe E).
- Le comportement de **TR-19** n'a pas été vérifié dans les conditions réelles de la chaîne complète : la sonde a retiré les triggers de `bons_commande` pour observer la FK `RESTRICT` seule ; le groupe F devra l'examiner chaîne complète.
- Répartition SQL / service : sont documentés côté service la réservation du numéro (PT-1, D-54), le plafond 99 999 et la borne d'année du PV initial (INV-177). Le statut du BC, la cohérence de dates, la non-vacuité de `reserves` et un message explicite au-delà de 99 levées ne sont **ni documentés ni obligatoires** (QO-1, QO-3, QO-4, PR-5).

---

## 4. Règles de service (ne passent pas en SQL) et interactions

### 4.1 Création d'un PV initial (service)
1. **Pré-contrôles avant toute réservation** : BC existant ; `type ∈ {sans_reserves, avec_reserves}` ; `reserves` fourni ⇔ avec réserves ; snapshots construits (INV-30) ; **année de `date_reception` ∈ 2001-2099** (INV-177, D-38) ; plafond 99 999 non atteint (erreur explicite).
2. **Réservation** du numéro `PVR-nnnnn-yy` (`yy` = année de `date_reception`) dans sa transaction propre committée (PT-1, D-54) ; le compteur ne décroît jamais.
3. `BEGIN IMMEDIATE` ; `INSERT` du PV (**`INSERT` simple, jamais `OR REPLACE` ni `OR IGNORE`**) ; `COMMIT`.
4. Échec avant réservation : aucun numéro consommé. Échec après réservation : le PV disparaît, le compteur garde un **trou**, jamais réutilisé (INV-179). Numérotation inchangée.
5. Aucune écriture sur `bons_commande`, `factures`, `garanties` (CT-2) ; aucun recalcul de cache.

### 4.2 Création d'une levée de réserves (service)
1. Pré-contrôles : origine existante, `reception_avec_reserves`, même BC ; `suffixe = max + 1` calculé dans la transaction ; au-delà de 99, le CHECK refuse (CT-6) ; une erreur de service explicite serait une proposition non validée (PR-5) ; `numero = numero(origine) \|\| '-' \|\| suffixe(2)`.
2. **Aucune réservation de séquence** (la levée n'a pas de séquence) ; aucun high-water.
3. `INSERT` dans `BEGIN IMMEDIATE`. Un échec ne consomme donc **rien** : ni numéro, ni suffixe (le suffixe est recalculé à chaque tentative).
4. Le PV d'origine reste inchangé ; `garanties` inchangées.
5. **Borne d'année** : INV-177 (« réception du PV ») ne mentionne pas la levée, qui n'a pas d'année propre (Mod. §6) ; aucune règle propre aux levées n'est posée (Z-10).

### 4.3 Règles « non-effet » (testées)
Un PV (initial, avec ou sans réserves, levée) ne crée, ne modifie ni ne supprime : une facture, un règlement, une garantie, une ligne de BC, un cache de BC (`statut`, `avancement`, `montant_deja_facture_ht`, `date_100_facture`, `completed_at`, `updated_at`), une ligne de `numerotation_sequences` (par le SQL ; la réservation est un acte de service). La date de début du suivi des garanties n'est jamais déplacée par un PV ni par sa levée (Mét. §23 ; INV-87).

### 4.4 Import (INV-131)
Les PV importés traversent TR-40 (aucune mise à jour postérieure) et TR-41 comme toute écriture V6 (INV-131 : aucune exemption de règle métier). **(info Rémy) La V2 ne contient aucun PV** : aucun PV historique n'est importé depuis la V2 ; le contrat d'import conserve néanmoins un bloc `pv` (Mod. §10.2) et `origine='import'`. Si un bloc `pv` était fourni : insertion **après** les BC (FK) et par `id` croissant des origines **avant** leurs levées (sinon G1 refuse), les levées d'une même origine par suffixe croissant 1, 2, 3… **sans trou** (G3). Le format du `numero` d'un PV initial `origine='import'` n'est pas contrôlé (non vide, unique : INV-131). Pour une **levée** liée à un PV `origine='import'` (ou une levée importée), le traitement du numéro n'est **pas spécifié** (Z-8, QO-2) : G1-G4 s'appliquent sans exemption d'origine ([CT], lecture littérale d'INV-131 et de TR-41), aucune exemption n'est ajoutée ; scénario hors périmètre de migration.

### 4.5 Contrôles de cohérence (hors SQL, service / requêtes CK)
- **CK-01** (numéros uniques et au format V6 sauf devis/factures/PV importés) : le traitement des **levées** n'est pas spécifié (Z-7) ; 009 ne le définit pas.
- **CK-02** (séquences ≥ max des numéros au format V6) : idem (Z-7) ; 009 ne prétend pas que les numéros de levée sont ou non exclus du maximum.
- **CK-03** `foreign_key_check` couvre `pv`. Aucune requête CK n'est créée ni redéfinie par 009.

---

## 5. Cas limites et scénarios d'anomalie à couvrir
1. PV initial sans réserves / avec réserves ; `observations` NULL ; `reserves` vide `''` (QO-4) ; `reserves` sur un sans-réserves ou absentes sur un avec-réserves ⇒ refus.
2. Plusieurs PV initiaux sur un BC ; **deux PV de même `date_reception`** ; PV avant le solde, après le solde, sur BC `en_cours`, `termine`, BC sans facture (aucune restriction documentée, INV-95), `annule` (non spécifié, QO-1 : comportement constaté, pas une règle).
3. Levée : sur sans-réserves ; sur levée ; sur origine d'un autre BC ; sur origine inexistante ; origine `NULL` avec suffixe ; suffixe 0, 2 avant 1, doublon, trou, 100 ; plusieurs origines sur un même BC (suffixes indépendants) ; levée multi-lignes ; levée dont le `numero` ne dérive pas de l'origine ; levées 1 à 99 puis 100ᵉ refusée.
4. Numérotation : yy ≠ année de `date_reception` ; format incorrect (préfixe, nombre de chiffres, séparateur) ; doublon ; levée de numéro identique à un PV initial ; PV initial `PVR-00001-26-01` (forme de levée) ⇒ refusé (type ≠ levée) ; année bissextile ; 29/02 ; `0000`, `2000`, `2100`, `9999` (SQL accepte, service refuse 2000/2100/9999 pour un PV V6).
5. Immuabilité : UPDATE de chaque colonne, no-op, `OR REPLACE/IGNORE`, UPSERT, DELETE (simple, multi-lignes), REPLACE par id / numero / (origine, suffixe), `recursive_triggers=OFF` (témoin).
6. FK : `bc_id` inexistant ; suppression d'un BC avec PV (TR-19 puis FK `RESTRICT` sur base **sans triggers**) ; suppression d'un PV origine ayant des levées ; identifiants volontairement distincts (`id` PV ≠ `bc_id` ≠ `origine_pv_id`).
7. Import : PV `origine='import'` avec numéro libre ; numéro vide refusé ; numéro identique à un PV V6 refusé ; levée importée avant son origine ; levée importée avec suffixe 2 sans 1 ; `legacy_*` sur `origine='v6'` refusé ; aucun `legacy_numero`. Cas hors migration V2 (info Rémy) : ils constatent seulement que TR-40/TR-41 s'appliquent sans exemption (INV-131).
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
| **C Numérotation** (service émulé) | PVR réservé par année (`yy` de `date_reception`) ; plusieurs PV même année ; changement d'année ; **levée : séquence PVR et `derniere_date` inchangées** ; aucune chronologie TR-02 (PV daté avant un PV déjà numéroté accepté) ; plafond 99 999 ⇒ erreur explicite, aucune réservation ; années 2000/2100 refusées par le service pour le PV initial (INV-177 ; levée : non spécifié, Z-10) ; indépendance vis-à-vis de FAC/AVO |
| **D Levée (TR-41)** | G1 (sans réserves, levée, origine inexistante) ; G2 (autre BC) ; G3 (1, 2…99 ; trou ; doublon ; 100 ; deux origines indépendantes ; insertion multi-lignes) ; G4 (numéro incohérent, bon numéro) ; plusieurs PV initiaux ; max calculé sur une base alimentée sans trigger (témoin) |
| **E Immuabilité (TR-40)** | UPDATE de **chaque** colonne, no-op, `OR REPLACE/IGNORE`, UPSERT ; DELETE ; REPLACE ×3 ; `recursive_triggers=OFF` (témoin documenté) ; code `INV-96`/`INV-06` ; aucune modification résiduelle ; `sqlite_sequence` |
| **F FK et suppression des parents** | `bc_id` inexistant ; DELETE de `bons_commande` et de PV origine refusés (avec et sans triggers) ; ids distincts ; `origine_pv_id` RESTRICT |
| **G Indépendance** (CT-1, CT-2, §4.3) | empreintes avant/après de toutes les tables hors `pv` ; PV sur BC `en_cours`/`termine`/`annule` (constat ; QO-1 non spécifiée) ; PV avant/après solde ; **garanties intactes** après PV et levée (dont T-14) ; caches du BC intacts ; le PV ne conditionne ni solde, ni Terminé |
| **H Import** | PV `origine='import'` (numéro libre, `legacy_id`) ; mêmes gardes pour toute origine (INV-131) ; levée sur/dans un contexte importé (ordre, suffixes consécutifs, numéro dérivé par G4) : **constat du comportement, sans le poser en règle métier** (Z-8 non spécifié, hors périmètre de migration) ; unicité ; `origine='v6' ⇒ legacy_* NULL` |
| **I Diagnostics** | `foreign_key_check` (CK-03) sur `pv` ; lecture seule (empreinte avant/après) ; base alimentée en SQL direct (triggers retirés) ⇒ détection par requêtes **de test** (pas des CK du modèle : le traitement des levées par CK-01/CK-02 n'est pas spécifié, Z-7) |
| **J Non-régression** | suites 001→008 inchangées (**1598 tests**) ; texte des triggers 001–008 identique ; chaîne rejouée sur base vide et peuplée ; 009 n'écrit ni ne lit les autres tables (empreintes) |
| **K Données malformées / contournements** | BLOB, REAL, INTEGER dans colonnes TEXT (STRICT), NUL, espaces, casse ; années extrêmes ; `recursive_triggers=OFF` (témoin) |
| **L Atomicité** | `INSERT` multi-lignes partiellement invalide ⇒ rien ; `SAVEPOINT`/`ROLLBACK` ; **émission du PV** : échec avant réservation (compteur inchangé) / après réservation (compteur +1, trou jamais réutilisé, aucun PV) ; échec d'une levée ⇒ aucun suffixe consommé ; avant/après (empreinte complète) à chaque scénario d'échec |

Chaque test d'échec vérifie **les données persistées et l'état de la base avant/après** (pas seulement l'exception). Nommage des méthodes : `test_T51_<groupe>_<comportement>` (pratique 006-008 ; Z-9). **Volume visé : 170 à 230 tests** (1 table, 1 index, 3 triggers : moins de surface que 008, pas de post-condition C1-C8).
**Mutation** (phase suivante, après validation et livraison SQL + tests, comme en 007/008) : mutants du seul `009_pv.sql` — listes `IN`, bornes `1`/`99`/`+ 1`, `COALESCE(...,0)`, `WHEN`, `GLOB`, `substr(numero, 11, 2)`/`substr(date_reception, 3, 2)`, `IS`/`=`, `WHERE` de G1 à G4, `printf('%02d')`, ordre des gardes, `DROP INDEX`, `STRICT`, FK ; chaque survivant qualifié individuellement (équivalent démontré ou test manquant) ; **non lancée ici**. Équivalents prévisibles à qualifier : `FOR EACH ROW`, conjoncts redondants entre CHECK de cohérence (levée ⇔ origine ⇔ suffixe), redondance G1/CHECK, `IS` vs `=` sur colonnes NOT NULL.

---

## 7. Contradictions et lacunes documentaires

| # | Statut (audit) | Source / section | Constat | Conséquence pour 009 | Correction minimale proposée |
|---|---|---|---|---|---|
| Z-1 | FAUX POSITIF (sans effet sur 009) | `docs/conception/` | La V3.13 n'existe que dans `fichiers-a-relire/` ; `docs/` contient la V3.12 ; `invariants.md` officiel est antérieur (INV-188 absent ; INV-32, INV-06, INV-23, INV-05 différents) | Aucune dépendance : règles PV identiques (§0) | Reporter les `MAJ__*` dans `docs/` (hors 009, à votre main) |
| Z-2 | PROPOSITION (documentaire ; pas un blocage SQL) | Mod. §17.1 (« Prochaine tranche métier : 006 … en cadrage », rangs 9-11 « prévue / non créée ») ; conv. §5 (rangs 5-7 « prévue, non créée », 9-11 « prévue ») | Le suivi des migrations n'est pas à jour : 005, 005a, 005b, 006, 007 (et 008, en copie de travail) existent | Aucun effet technique ; la chaîne réelle est 001→008 (user_version 11) | Mettre à jour §17.1 et conv. §5 à la validation de 009 (hors cadrage, à votre main) |
| Z-3 | NON SPÉCIFIÉ | Métier §2.4 — **officiel** `docs/conception/modèle-métier-V6.md` l.79 : « … un PV … n'est jamais supprimé pour corriger une erreur : il est annulé (date et motif) ou corrigé par un document opposé (avoir) » ; **travail** `MAJ__modèle-métier-V6.md` l.81 : « annulé (date et motif) lorsque l'objet est annulable (devis, BC, dépense, règlement), ou corrigé par un document opposé » | Les deux versions divergent sur l'annulation applicable au PV. Le modèle de données (V3.12 et V3.13, §4.11) ne prévoit ni statut ni colonne d'annulation pour `pv`, ni « document opposé » pour un PV : aucun mécanisme de correction d'un PV erroné n'est documenté (audit conservation X-9). **Divergence signalée, non tranchée ; aucune source modifiée.** | Aucun effet SQL (PV immuable, sans statut) ; voir QO-5 | Aucune pour 009 ; clarification du métier §2.4 hors périmètre |
| Z-4 | NON SPÉCIFIÉ | Mét. §23 / Mod. §4.11 | Aucune règle de **levée partielle** : une levée n'a pas de `reserves` (CHECK INV-97), plusieurs levées par origine sont possibles (`suffixe` 1-99), mais les sources ne disent ni quelles réserves chacune lève, ni quand la levée est « complète » | Aucun effet SQL ; rien n'est ajouté | Aucune (précision métier éventuelle, hors 009) |
| Z-5 | PROPOSITION (technique) | Mod. §9 (l.818) : `pv(origine_pv_id)` | La liste impose un index que la règle de tête du même §9 rend redondant (`UNIQUE(origine_pv_id, suffixe)` commence par la FK) — même cas que `garanties(bc_ligne_id)` (008 Z-5) | 1 index explicite au lieu de 2 (PR-1) | Retirer `pv(origine_pv_id)` de la liste du modèle : proposition technique, à confirmer par Rémy, pas une décision métier |
| Z-6 | PROPOSITION (technique) | Mod. §8, TR-01 (liste `pv`) | TR-01 (« numéro immuable ») est subsumé par TR-40 (aucun UPDATE) — lecture du cadrage | Pas de trigger TR-01 spécifique sur `pv` (PR-6) | Annoter TR-01 : « pv couvert par TR-40 » (proposition, à confirmer) |
| Z-7 | NON SPÉCIFIÉ | Mod. §14 (CK-01, CK-02, l.1129) ; INV-20 | CK-01 et CK-02 ne disent pas comment une **levée** (`PVR-00001-26-01`) est traitée (contrôle de format V6 ? contribution au « max des numéros au format V6 » ?). Le cadrage ne prétend pas le contraire | Aucun effet SQL ; 009 ne crée ni ne redéfinit aucune requête CK (§4.5) | Aucune pour 009 ; précision éventuelle de CK-01/CK-02 dans le modèle, hors périmètre |
| Z-8 | NON SPÉCIFIÉ — hors périmètre de migration (info Rémy) | INV-27 / D-24 / INV-131 / Mod. §10.4 (numéro historique conservé ; exemption : format, préfixe, année) ; TR-41 / Mod. §4.11 / CDC §23 (numéro de la levée = numéro de l'origine + `-` + suffixe) ; INV-20 (format V6, levée `PVR-00001-yy-01`) | (info Rémy) La V2 ne contient aucun PV : aucun PV historique n'est importé depuis la V2. Le scénario « levée créée en V6 sur un PV importé de la V2 » est donc hors du parcours de migration prévu. Pour les PV créés en V6, TR-41 et INV-20 restent applicables sans modification. INV-27 n'est pas en cause : dériver le numéro d'une levée ne transforme pas le numéro de l'origine. Le contrat d'import conserve toutefois un bloc `pv` et `origine='import'` (INV-131, D-24), et plusieurs sources décrivent encore des PV V2 importés (§0) : divergence signalée, non corrigée | Aucune exemption inventée ; G1-G4 sans exemption d'origine (INV-131) ; aucune décision demandée ; non bloquant | Aucune pour 009. Si des PV `origine='import'` entraient un jour dans le périmètre, la règle devrait alors être précisée (décision de Rémy) |
| Z-9 | PROPOSITION (conventionnelle) | Conv. §7 (méthodes de test nommées `test_INV_xx_…`) vs pratique 006-008 (`test_T<nn>_<groupe>_…`) | Deux conventions de nommage | Aucune ; 009 suit 006-008 | Aligner conv. §7 sur la pratique (documentaire) |
| Z-10 | NON SPÉCIFIÉ | Mod. §2.2 (l.85) / INV-177 ; Mod. §6 (l.710) | INV-177 cite « réception du PV » parmi les dates de numérotation annuelle ; la levée n'a pas d'année propre (Mod. §6) et n'est pas mentionnée. Les sources ne disent pas si la borne 2001-2099 (service) vise aussi `date_reception` d'une levée. **Aucune règle propre aux levées n'est posée** | Aucun effet SQL (aucune borne d'année en SQL, D-38) | Aucune pour 009 ; précision éventuelle d'INV-177, hors périmètre |
| Z-11 | FAUX POSITIF | Mod. §4.10 / §23 Mét. vs 008 | « Un PV ou sa levée ne modifient pas une garantie » : 008 le garantit en n'ayant aucun lien avec `pv` | 009 n'introduit aucune lecture/écriture croisée ; testé (groupe G) | Aucune |

Aucune de ces lacunes ne contredit le **DDL** ni le **comportement** documentés de `pv`, et aucune n'est bloquante pour le SQL 009. Z-8 est non spécifié et hors périmètre de migration (info Rémy).

---

## 8. Questions ouvertes et propositions

### Propositions [PR] (techniques ou documentaires ; non décidées, non nécessaires à la conformité)
- **PR-1** *1 seul index explicite* (`idx_pv_bc_id`) ; `pv(origine_pv_id)` assuré par l'index de l'`UNIQUE` (Z-5).
- **PR-2** *3 triggers* : `tr_40_pv_no_update`, `tr_40_pv_no_delete`, `tr_41_pv_insert` (G1-G4). Aucun trigger sur d'autres tables.
- **PR-3** *Format de `numero`* : le CHECK de format `origine='v6'` porte sur le **PV initial** (documenté : INV-20, Mod. §10.4). **Aucun CHECK de format n'est ajouté pour la levée** : son traitement n'est pas spécifié (Z-8) ; son numéro est dérivé par G4 (TR-41). Aucune règle nouvelle ; cette position n'a d'effet différentiel que pour une origine à numéro libre, hors périmètre de migration.
- **PR-4** *Pas de lecture du statut du BC* dans les triggers (CT-1) ; voir QO-1.
- **PR-5** *Erreur de service explicite au-delà de 99 levées* : proposition non validée ; seul le CHECK `suffixe ≤ 99` est documenté (CT-6).
- **PR-6** *TR-01 de `pv` non posé séparément* (couvert par TR-40) : proposition technique (Z-6).

### Questions ouvertes [QO] — toutes non spécifiées ; aucune n'est bloquante pour le SQL 009, aucune n'a d'effet de schéma
- **QO-1 — PV sur un BC `annule`.** **Non spécifié** : INV-95 dit seulement que le PV ne conditionne rien ; INV-188 (V3.13, `MAJ__invariants.md`) interdit sur BC annulé « un nouvel acompte, une nouvelle situation, un nouveau solde, un nouveau devis » et autorise avoirs et dépenses, sans citer le PV. Le cas du BC `termine` est couvert par les règles documentées (INV-95 : le PV ne conditionne ni le solde ni Terminé ; aucune restriction n'est documentée) et n'est plus une question. *009 n'ajoute aucune garde.*
- **QO-2 — Numéro d'une levée liée à un PV `origine='import'` (Z-8).** **Non spécifié ; hors périmètre de migration** (info Rémy : la V2 ne contient aucun PV). Aucune décision n'est demandée à Rémy ; aucune exemption de format n'est inventée ; TR-41 et INV-20 restent applicables aux PV créés en V6. Aucun effet de schéma.
- **QO-3 — Cohérence de dates.** **Non spécifié** : aucune règle documentée entre `date_reception` d'une levée et celle de son origine, entre `date_reception` et les dates du BC, ni contre une date future ; INV-177 ne porte que sur les bornes d'année. *009 n'ajoute aucune garde.*
- **QO-4 — `reserves` non vide.** **Non spécifié** : « renseignées » (Mét. §22) ; le CHECK documenté exige seulement `reserves IS NOT NULL` et ne traite pas `''`. *009 n'ajoute aucune garde (un `''` est accepté par le SQL ; comportement constaté en test, pas une règle).*
- **QO-5 — Correction d'un PV erroné (Z-3).** **Non spécifié** : aucun mécanisme documenté (ni annulation, ni document opposé) et les deux versions du métier §2.4 divergent (Z-3). Toute voie de correction serait une règle nouvelle. Aucun effet SQL, hors 009.

### Points bloquants
**Aucun.** Aucune question ouverte ni aucune lacune Z n'est bloquante pour l'écriture du SQL 009 ; la validation de ce cadrage par Rémy reste requise avant toute implémentation.

---

## 9. Critères d'acceptation de la tranche 009
1. `009_pv.sql` contient exactement : 1 table `pv` STRICT, `idx_pv_bc_id`, `tr_40_pv_no_update`, `tr_40_pv_no_delete`, `tr_41_pv_insert` ; **rien d'autre** (§2) ; aucune modification de 001-008.
2. `PRAGMA user_version = 12` sur la chaîne 001→009 ; `foreign_key_check` vide ; `integrity_check` ok ; empreinte `sqlite_master` de 001-008 inchangée.
3. `test_009_pv.py` (T-51) : tous les groupes A à L du §6 verts ; chaque scénario d'échec vérifie l'état persisté avant/après ; **suites 001→008 inchangées et vertes (1598 tests)**.
4. G1 à G4, CHECK de cohérence, immuabilité et les trois variantes de `REPLACE` éprouvés ; plafond 99 levées ; plusieurs PV initiaux ; PV sans effet sur BC, factures, règlements, **garanties** (empreintes).
5. Aucune règle non documentée n'est introduite ; QO-1 à QO-5 restent non spécifiées, sans effet de schéma (aucune garde ajoutée) ; ce cadrage est validé par Rémy avant écriture.
6. Campagne de mutation sur le seul `009_pv.sql` : **0 survivant non qualifié** (conv. §7.1) ; rapport `RAPPORT_MUTATION__009_pv.md` ; toute lacune de test corrigée par des tests, jamais en modifiant le SQL sans repasser par le cadrage.
7. Rapport final détaillé pour revue indépendante ; **validation finale conditionnée à la revue** ; aucun push par l'agent (vous poussez vous-même).

---

## Conclusion
**Cadrage corrigé après audit, prêt à relire.** Le périmètre SQL est petit et documenté : une table, un index, trois triggers (TR-40 ×2, TR-41). Les règles PV sont **identiques en V3.12 et V3.13**. Aucune question ouverte ni lacune ne bloque l'écriture du SQL ; Z-8 / QO-2 est non spécifié et hors périmètre de migration (info Rémy). Étiquettes corrigées (C-7 [PR], PR-3, CT-6, Z-3, Z-7, Z-10). Un PV, levée comprise, n'agit sur aucune autre table, en particulier les garanties. Aucune implémentation n'est commencée.

## Livraison
Ce seul fichier : `fichiers-a-relire/CADRAGE__009_pv.md`. Aucun `009_pv.sql`, aucun test, aucun rapport de mutation, aucun document officiel ou migration modifié ; V3.13 non déplacée. Les sondes SQL citées (§2, §3.4, CT-4, CT-7, CT-8) ont été exécutées sur une copie jetable **en mémoire**, hors dépôt (scratchpad) ; elles ne constituent pas une preuve de conformité documentaire (§3.6) ; aucun test du dépôt n'a été exécuté pour ce cadrage. Aucun push effectué (vous poussez vous-même).
