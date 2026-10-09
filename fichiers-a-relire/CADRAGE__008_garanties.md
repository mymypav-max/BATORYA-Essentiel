# CADRAGE 008 — Garanties

Tranche 008 (rang 11) : future `src-tauri/migrations/metier/008_garanties.sql` + `src-tauri/tests/metier/test_008_garanties.py` (T-50). **Ce document est un cadrage : aucun fichier SQL, test ou document officiel n'est créé ou modifié.**
Statut : **PROPOSÉ — en attente de validation par Rémy.** Dépôt lu : `main` @ `a9fd50f`.

Légende des étiquettes :
**[RD]** règle documentée · **[DV]** décision déjà validée (errata, cadrages 006/007, D-xx) · **[CT]** conséquence technique (déduite, aucune règle nouvelle) · **[PR]** proposition (à arbitrer) · **[QO]** question ouverte.

---

## 0. Sources lues et hiérarchie

Lues en entier sur les passages « garantie » : `docs/conception/invariants.md`, `modèle-métier-V6.md` (§24), `modèle-données-sqlite-v6-v3.12.md` (§4.10, §8, §9, §13, §14), `conventions-techniques-v6.md`, `docs/specifications/cdc-fonctionnel-architectural-v6.md` (§24-25), `docs/décisions/cdc-errata-v6.md` ; et leurs versions `fichiers-a-relire/MAJ__*` (dont **V3.13**, laissée dans `fichiers-a-relire/`, non déplacée, **non traitée comme publiée**) ; migrations `001` (`prestation_garanties`), `003` (`devis_ligne_garanties`), `004` et `005b` (`bc_ligne_garanties`, TR-13), `005a`, `006_facturation.sql`, `007_reglements.sql` ; tests 001→007 ; `CADRAGE__006_facturation.md` et `CADRAGE__007_reglements.md`.

Hiérarchie appliquée (celle des cadrages 006/007) : 1 décisions validées · 2 invariants · 3 modèle SQLite validé · 4 modèle métier · 5 errata · 6 CDC · 7 migrations existantes (référence technique réelle).
**Position sur la V3.13 :** le DDL de `garanties` (§4.10), TR-50 et les index sont **identiques en V3.12 (officielle) et V3.13 (`MAJ__`)** (cf. tableau ci-dessous) ; le cadrage ne dépend donc pas du statut de la V3.13 pour le DDL. Seul le libellé « avoir (même total) » remplace « annulation du solde » : c'est l'errata **E-14 validé** (niveau 1/5), pas la V3.13 en tant que telle.

### Comparaison V3.12 ↔ V3.13 sur le périmètre garanties

| Élément | V3.12 (`docs/`) | V3.13 (`MAJ__`) | Effet sur 008 |
|---|---|---|---|
| §4.10 colonnes, `UQ(bc_ligne_id, garantie_type)`, CHECK `date_fin_suivi > date_declenchement`, « pas de colonne statut », « aucun UPDATE ni DELETE » (l.401-405 / l.525-528) | oui | **identique** | aucun |
| §4.10 création (`INSERT OR IGNORE`, dates, +1/+2/+10 ans, 29/02) | oui | **identique** | aucun |
| §4.10 « ne suppriment ni ne modifient une garantie » | « L'annulation du solde, un avoir, un règlement » | « Un avoir (**même total**) sur le solde, un règlement » (E-14 : annulation de facture obsolète) | 008 suit E-14 |
| §4.10 paragraphe « Plusieurs devis sur un BC » | absent | ajouté (D-47, E-16, INV-187) | toutes les lignes du BC existent au 1er solde [CT-4] |
| TR-50 (§8) ; index §9 ; D-16, D-23, D-34 ; §10 (blocs refusés) | présents | identiques (D-47 ajouté) | aucun |
| T-14 | « solde annulé → garantie conservée » | « avoir total sur le solde → garantie conservée » | test T-14 écrit selon E-14 |
| INV-86, INV-87 | V3.12 | précisés (copie au rattachement ; avoir même total ; INV-187) | 008 suit les `MAJ__` (niveau 2 corrigé par errata) |
| CK-07 « garanties d'un BC ayant un solde actif » (§14) | oui | identique | voir Z-4 |

---

## 1. Règles déjà décidées (références exactes)

Fichiers cités : « Mod. » = `MAJ__modèle-données-sqlite-v6-v3.13.md` ; « Inv. » = `MAJ__invariants.md` ; « Mét. » = `MAJ__modèle-métier-V6.md`.

### 1.1 Entité et données
| Règle | Étiquette | Source |
|---|---|---|
| Table `garanties` : `id` PK · `bc_id` NN FK→`bons_commande` · `bc_ligne_id` NN FK→`bc_lignes` · `garantie_type` NN · `date_declenchement` D NN · `date_fin_suivi` D NN · `facture_declenchement_id` NN FK→`factures` · `created_at` | [RD] | Mod. §4.10 (l.527) ; V3.12 §4.10 (l.403) |
| `UQ(bc_ligne_id, garantie_type)` ; CHECK `date_fin_suivi > date_declenchement` ; **pas de colonne statut** ; aucun UPDATE ni DELETE | [RD] | Mod. §4.10 (l.528) ; INV-89 ; TR-50 (Mod. §8 l.786) |
| `garantie_type ∈ {parfait_achevement, biennale, decennale}` (liste fermée, identique à `bc_ligne_garanties`) | [RD] | Mod. §2.5 (l.132) ; 004 l.260 ; 005b l.279 |
| Une garantie appartient toujours à un BC ; ligne et facture de déclenchement NOT NULL **sans exception** | [RD] | INV-90 ; INV-134 (Inv. l.126, l.173) |
| Pas de BLOC-IMP sur `garanties` (ni `origine`, ni `legacy_*`) | [RD][DV] | D-23 (Mod. l.1163) ; Mod. §4.10 « aucune garantie n'est importée » |
| Aucun `updated_at`, aucune numérotation, aucun `historique` embarqué | [RD] | Mod. §4.10 ; D-34 (historique : tranche propre) |

### 1.2 Déclenchement et création
| Règle | Étiquette | Source |
|---|---|---|
| Les garanties naissent à l'**émission du premier solde actif** du BC. « 100 % facturé » = **présence d'un solde** (pas `avancement = 100.00`) | [RD][DV] | INV-85 ; CDC §24 (MAJ l.729) ; Mod. §3.2 (l.197) ; **DV-5** (cadrage 006 l.305 : « `avancement = 100 %` n'est pas l'émission d'un solde ») |
| Indépendantes du paiement, du PV, de la réception, des réserves et de leur levée | [RD] | Mét. §24 (l.638-643) ; INV-95 ; Mét. l.614 (la levée ne modifie pas le suivi) |
| Création **par le service** : lit `bc_ligne_garanties` du BC, `INSERT OR IGNORE` (idempotent, première date conservée) ; **jamais par trigger** | [RD] | Mod. §4.10 (l.530) ; Mod. §8 rappel (l.801) ; INV-86 ; conv. §9 (MAJ l.347 : `INSERT OR IGNORE` permis pour « la création des garanties ») |
| `date_declenchement` = date d'émission de ce solde ; **immuable** | [RD] | INV-87 ; Mét. §24 (l.645) |
| Un **solde à 0.00** reste un solde : il peut déclencher les conséquences métier du solde | [DV] | DV-9 (cadrage 006 l.309) ; C-08 ; cadrage 006 synthèse n°7 (l.1490 : « déclenche … les garanties (008) ») |
| Tout devis rattaché l'est **avant** la rédaction du solde (TR-99) : toutes les lignes du BC et leurs garanties de ligne existent au premier solde ; une ligne supprimée (brouillon) n'a plus de garantie ; **aucun nouveau mécanisme de garantie** | [RD][DV] | INV-87, INV-187 ; D-47 ; E-16 (errata MAJ l.23) ; PT-18 (Mod. l.1387) ; 006 `tr_99_bc_devis_apres_solde` (l.483) |

### 1.3 Durées et dates
| Règle | Étiquette | Source |
|---|---|---|
| `date_fin_suivi` = `date_declenchement` **+1 an** (parfait achèvement) / **+2 ans** (biennale) / **+10 ans** (décennale) | [RD] | INV-88 ; Mét. §24 (l.631) ; Mod. §4.10 |
| **29 février → 28 février** | [RD] | INV-88 ; Mod. §4.10 (« si l'année cible n'est pas bissextile ») — équivalence démontrée en [CT-3] |
| Suivi interne, libellé toujours « Suivi interne BATORYA — date indicative » ; état **dérivé** `a_surveiller` / `echue` | [RD] | INV-88, INV-89 ; Mod. §3.4 (l.226) ; CDC §24-25 |
| Dates au format `YYYY-MM-DD` réel (`GLOB` + `date(x) IS x`), aucune borne d'année (INV-177 : bornes réservées aux dates de numérotation) ; « jour courant » = date locale | [RD] | conv. techniques ; INV-177 (Inv. l.41) ; Mod. l.83 |

### 1.4 Effets des autres objets
| Règle | Étiquette | Source |
|---|---|---|
| Un **avoir (même total)** sur le solde, un **règlement** (encaissement, annulation, remboursement) ne suppriment ni ne modifient une garantie | [RD][DV] | INV-87 ; E-14 ; Mét. §24 (l.645) ; T-14 ; C-07 ; cadrage 006 M.5 (l.156) ; cadrage 007 §1.3 |
| `bons_commande.date_100_facture` (cache, premier solde **actif**, peut redevenir NULL / changer) ≠ `garanties.date_declenchement` (premier déclenchement historique, immuable) : divergence **voulue** | [RD][DV] | INV-43 ; Mod. §3.5 (l.238) ; VR-10 (cadrage 006 l.59, l.173-175) ; cadrage 006 M.5 (l.157 : un nouveau solde ne change pas la date des garanties) |
| Un avoir ne rouvre jamais commercialement le BC (aucun devis, acompte, situation) ; un nouveau **solde** reste possible après avoir total | [DV] | VR-09 ; DV-7, DV-8 ; INV-187 ; cadrage 007 §2bis |
| BC annulé : aucun nouveau solde (donc aucune naissance de garantie) ; avoirs sur documents existants autorisés | [DV] | INV-188 ; VR-04 ; 006 `tr_16_factures_bc` |
| Une garantie n'est **jamais recalculée** | [RD] | INV-134 (Inv. l.173) |

### 1.5 Import, suppression, FK
| Règle | Étiquette | Source |
|---|---|---|
| Le contrat d'import n'accepte **aucune garantie ni garantie de ligne** : `devis_ligne_garanties` et `bc_ligne_garanties` restent vides pour les objets importés ; un BC importé ne génère **aucune** garantie native | [RD][DV] | INV-134 ; D-16 (Mod. l.1156, l.1199) ; Mod. §10 (l.865-866) |
| Aucune règle exemptée pour les données importées | [RD] | INV-131 |
| Jamais de suppression physique d'une garantie ; FK en `RESTRICT` par défaut, `ON DELETE` examiné relation par relation : aucune cascade ici (pas de parent supprimable : BC, ligne de BC et facture sont insupprimables) ; aucune clause `ON UPDATE` | [RD][CT] | INV-05, INV-06, INV-174 ; D-44 ; 004 `tr_19`, 005b `tr_13_*_delete`, 006 `tr_21_factures_no_delete` |
| `INSERT OR REPLACE` / `REPLACE` interdits ; `recursive_triggers=ON` | [RD] | conv. §9 (official l.216) ; D-39 |

---

## 2. Périmètre SQL exact de la migration 008

**Contenu** : 1 table `garanties` (STRICT), 3 index nommés, 3 triggers. **Rien d'autre** : aucun `INSERT`, aucun `ALTER`, aucune reconstruction ni lecture/écriture de `numerotation_sequences`, aucun trigger sur `bons_commande`, `bc_lignes`, `bc_ligne_garanties`, `factures`, `reglements`. 001→007 inchangés (empreinte `sqlite_master` testée). Pas de `BEGIN/COMMIT/PRAGMA` dans le fichier ; `user_version = 11` posé par le runner (Mod. §17.1 l.1268, D-55, D-56, conv. MAJ l.136).

```sql
CREATE TABLE garanties (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    bc_id                    INTEGER NOT NULL REFERENCES bons_commande (id) ON DELETE RESTRICT,
    bc_ligne_id              INTEGER NOT NULL REFERENCES bc_lignes (id) ON DELETE RESTRICT,
    garantie_type            TEXT    NOT NULL CHECK (garantie_type IN ('parfait_achevement', 'biennale', 'decennale')),
    date_declenchement       TEXT    NOT NULL CHECK (date_declenchement GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_declenchement) IS date_declenchement),
    date_fin_suivi           TEXT    NOT NULL CHECK (date_fin_suivi GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(date_fin_suivi) IS date_fin_suivi),
    facture_declenchement_id INTEGER NOT NULL REFERENCES factures (id) ON DELETE RESTRICT,
    created_at               TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (bc_ligne_id, garantie_type),
    CHECK (date_fin_suivi > date_declenchement),
    -- [PR] QO-2 : durée exacte par type, 29/02 -> 28/02
    CHECK (date_fin_suivi = printf('%04d', CAST(substr(date_declenchement, 1, 4) AS INTEGER)
                                         + CASE garantie_type WHEN 'parfait_achevement' THEN 1 WHEN 'biennale' THEN 2 ELSE 10 END)
                            || CASE WHEN substr(date_declenchement, 6, 5) = '02-29' THEN '-02-28' ELSE substr(date_declenchement, 5) END),
    CHECK (created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;
```
*(Esquisse du cadrage, éprouvée sur une copie jetable de la chaîne 001→007 hors dépôt : STRICT, FK `RESTRICT` sans `ON UPDATE`, CHECK, UNIQUE, index et triggers se comportent comme décrit ci-dessous. Ce n'est pas le livrable `008_garanties.sql`.)*

**Absences voulues** : `statut`, `updated_at`, `origine`/`legacy_*`, `prestation_id`/`designation` (lisibles via `bc_lignes`), `active`, numéro, `facture_declenchement_id` NULL. Les types (`INTEGER`/`TEXT`) sont ceux de 004/006.

---

## 3. Triggers, index et contraintes nécessaires

### 3.1 Contraintes de table
| Contrainte | Étiquette | INV |
|---|---|---|
| 6 colonnes `NOT NULL` (`bc_id`, `bc_ligne_id`, `garantie_type`, 2 dates, `facture_declenchement_id`) | [RD] | 90, 134 |
| `UNIQUE(bc_ligne_id, garantie_type)` — rempart de l'idempotence ; son index couvre la FK `bc_ligne_id` | [RD] | 86 |
| CHECK `garantie_type IN (3 valeurs)`, dates réelles, TS | [RD][CT] | 88 |
| CHECK `date_fin_suivi > date_declenchement` | [RD] | 88 |
| CHECK durée exacte par type (29/02 → 28/02) — **G5** | **[PR] QO-2** | 88 |
| 3 FK `RESTRICT`, sans `ON UPDATE` | [RD][CT] | 05, 06, 174 |

### 3.2 Index
| Index | Étiquette | Justification |
|---|---|---|
| `idx_garanties_bc_id (bc_id)` | [RD] | Mod. §9 (l.817) ; lecture « garanties d'un BC » (CDC §25) |
| `idx_garanties_facture_declenchement_id (facture_declenchement_id)` | [RD] | Mod. §9 : un index par FK |
| `idx_garanties_date_fin_suivi (date_fin_suivi)` | [RD] | Mod. §9 : vues de suivi (échéances) |
| ~~`garanties(bc_ligne_id)`~~ | [CT] | **redondant** : l'index de `UNIQUE(bc_ligne_id, garantie_type)` commence par `bc_ligne_id` (règle de tête de Mod. §9, précédent 004) — vérifié par `EXPLAIN QUERY PLAN` (utilise `sqlite_autoindex_garanties_1`). Voir Z-5 |

### 3.3 Triggers (gardes pures `BEFORE`, `SELECT RAISE(ABORT,'INV-nn: …') WHERE …`, ASCII, aucune écriture, **aucune exemption d'origine**, INV-131)
| Trigger | Événement | Garde | INV | Étiquette |
|---|---|---|---|---|
| `tr_50_garanties_update` | BEFORE UPDATE | toujours refusé (même no-op ; couvre `UPDATE OR REPLACE/IGNORE` et `ON CONFLICT DO UPDATE`) | 87 | [RD] TR-50 |
| `tr_50_garanties_no_delete` | BEFORE DELETE | toujours refusé (couvre le DELETE implicite d'un `INSERT OR REPLACE`, `recursive_triggers=ON`) | 87, 06 | [RD] TR-50 |
| `tr_51_garanties_insert` — **G1** | BEFORE INSERT | `bc_ligne_id` existe et `bc_lignes.bc_id = NEW.bc_id` | 90 | [CT] |
| — **G2** | idem | `facture_declenchement_id` désigne une facture `type = 'solde'` du **même BC** (pas « actif » : notion dérivée, PT-9 ; le premier solde reste valide après avoir total) | 85, 90 | [CT] |
| — **G3** | idem | `(bc_ligne_id, garantie_type)` existe dans `bc_ligne_garanties` (« création lue dans `bc_ligne_garanties` ») ; rend impossible toute garantie sur un BC importé (INV-134) | 86, 134 | **[PR] QO-1** |
| — **G4** | idem | `date_declenchement = factures.date_emission` de la facture de déclenchement | 87 | **[PR] QO-1** |
| — **G6** | idem | la facture est le **premier** solde du BC | 87 | **[PR] déconseillé — QO-3** |

*Numérotation : `TR-50` est celui du modèle ; `TR-51` est **proposé** pour les gardes d'insertion (libre dans Mod. §8, qui passe de TR-50 à TR-60) — à reporter dans le modèle après validation (Z-9).*

### 3.4 Protections anti-contournement
`INSERT OR REPLACE` (DELETE implicite refusé) ; `UPDATE OR REPLACE/IGNORE` (RAISE(ABORT) non altéré par `OR`) ; **UPSERT `ON CONFLICT … DO UPDATE`** (déclenche `BEFORE UPDATE` → refusé, sondé) ; `INSERT OR IGNORE` rejoué : sans violation de garde, 0 ligne, aucune erreur, première date conservée (sondé) ; ré-INSERT d'un doublon avec une garde fausse → **ABORT** (un `BEFORE` s'exécute avant la détection du doublon, sondé : c'est pourquoi G6 est déconseillée, cf. QO-3). **Limite assumée (D-39)** : avec `recursive_triggers=OFF`, le DELETE implicite d'un `REPLACE` échapperait à `tr_50_garanties_no_delete` (sondé : la ligne est remplacée, id changé) — réglage de connexion, testé comme en 006/007. Octet NUL et saturation int64 : limites transverses 001–007, sans objet spécifique ici (aucun montant).

### 3.5 Conséquences techniques
- **CT-1** Les triggers de 008 ne lisent ni `reglements`, ni `bons_commande.statut`, ni les avoirs : une garantie est **indépendante du paiement et de l'état du BC** (INV-85, INV-87).
- **CT-2** Aucun trigger n'est posé sur `factures`/`reglements`/`bc_ligne_garanties` : l'immutabilité de 004/005b/006 suffit (avoir, règlement, annulation de règlement : aucune écriture dans `garanties`).
- **CT-3** *29/02* : pour une origine bissextile `Y`, les années cibles `Y+1`, `Y+2`, `Y+10` sont ≡ 1, 2, 2 (mod 4) : **jamais bissextiles**. « 29/02 → 28/02 » (INV-88) et « → 28/02 si l'année cible n'est pas bissextile » (Mod. §4.10) sont donc **équivalents** pour les trois durées ; la condition est du code mort. Piège : `date('2028-02-29','+1 year')` renvoie `2029-03-01` (sondé) — le service ne doit pas utiliser les modificateurs de date SQLite.
- **CT-4** Complétude : TR-99 (006) interdit tout rattachement après un solde ; au premier solde, `bc_ligne_garanties` est complet (lignes de **tous** les devis). Le SQL de 008 n'impose pas cette complétude (limite assumée) ; **CK-07a** la diagnostique.
- **CT-5** Aucun garde « BC non annulé » sur `garanties` : aucune source ne le prévoit (les garanties ne sont pas du contenu contractuel, INV-173) et la naissance exige un solde, déjà refusé sur BC annulé (`tr_16`, INV-188). Une garantie existante survit à l'annulation du BC.

---

## 4. Ce qui relève du service applicatif (ne passe pas en SQL)

| Règle | Pourquoi pas SQL |
|---|---|
| **Détecter** le déclenchement : émission du **premier solde du BC** (type `solde`, jamais `avancement = 100.00`, DV-5), solde à 0.00 inclus après confirmation (DV-9) | État du BC et ordre d'émission : service financier (INV-46, INV-164) |
| Créer les garanties **dans la même transaction que le solde** (échec ⇒ rollback du solde) : sinon fenêtre « solde sans garantie » (CK-07a) | Atomicité = transaction du service [CT] |
| Lire `bc_ligne_garanties` de **toutes** les lignes du BC (tous devis rattachés) ; ne tenter la création qu'au premier solde (au 2ᵉ solde après avoir total : rien à créer) | Règle de déclenchement (INV-85/86) ; G6 refusée (QO-3) |
| **Calculer** `date_fin_suivi` (+1/+2/+10 ans, 29/02 → 28/02) en arithmétique civile, **sans** `date(x,'+N year')` | INV-88 : garde « SVC, test » ; le CHECK QO-2 ne fait que **vérifier** |
| `INSERT OR IGNORE` uniquement ; jamais `REPLACE`, jamais UPSERT | conv. §9 |
| États dérivés `a_surveiller` / `echue`, libellé « Suivi interne BATORYA — date indicative », jour courant = date locale | INV-89 ; jamais persistés |
| Consultation par BC / client / prestation / type / dates (jointures sur `bc_lignes`, `bons_commande`, `clients`) | CDC §25 ; aucun module « Garanties » (Mét. l.145) |
| Événement `declenchement_garantie` dans `historique` (INV-110, INV-194) | `historique` n'est pas encore créée (D-34 : tranche propre) ; hors 008 ; granularité (par BC ou par garantie) non décidée — voir §7, P-2 |
| Copie des garanties de ligne devis → BC (création, rattachement), refus après solde | 004/005b/006 (déjà livrés) |
| Contrat d'import : aucune garantie ni garantie de ligne ; CK-07 après import et restauration | INV-134 ; Mod. §14 |
| Pas d'effet des PV et de leur levée sur les garanties | INV-95 ; Mét. l.614 |

**Requêtes de contrôle** (lecture seule, constantes de test ; **CK-07 n'ayant pas de formule dans les sources**, découpé en a/b/c sans nouveau numéro) :
- **CK-07a — garantie manquante** : pour tout BC ayant (ou ayant eu) un solde, toute paire `(ligne de BC, garantie_type)` de `bc_ligne_garanties` sans ligne dans `garanties` (esquisse éprouvée : renvoie 0 ligne sur un BC conforme).
- **CK-07b — garantie incohérente** : paire absente de `bc_ligne_garanties` ; `bc_id` ≠ BC de la ligne ; facture non-solde ou d'un autre BC ; `date_declenchement` ≠ `date_emission` ; `date_fin_suivi` ≠ formule INV-88 ; garantie sur un BC `origine = 'import'` (INV-134).
- **CK-07c — non premier solde** (informatif, utile si G6 est refusée) : `facture_declenchement_id` ≠ plus petit `id` des soldes du BC.

---

## 5. Tests (`test_008_garanties.py`, T-50) — positifs, négatifs, limites, non-régression

**Infra réutilisée** de 006/007 : `migrer10` + application de 008 au rang 11 (`BEGIN IMMEDIATE`, fichier, `user_version = 11`, `COMMIT`), `Base9`/`monde()`, `emettre_solde`, `neutraliser`, `terminer_bc`/`annuler_bc`, `desynchroniser_ids` ; ajout d'une fabrique de devis **avec garanties de ligne**, d'un **service émulé** `declencher_garanties()` (centimes/arithmétique civile indépendante du SQL) et d'un **oracle Python** de `date_fin_suivi` (balayage ≥ 800 dates × 3 types). Assertion sur la **règle** (code INV du message ; état résultant par empreintes), jamais sur l'exécution. Connexion : `foreign_keys=ON`, `recursive_triggers=ON`.

| Groupe | Contenu |
|---|---|
| **A chaîne et structure** | migration 008 sur base 007 vide et peuplée ; `user_version = 11` ; 1 table STRICT, colonnes/ordre/NOT NULL/défauts exacts, aucune colonne statut/`updated_at`/`origine`/`legacy_*` ; 3 index + autoindex UQ ; 3 triggers ; **aucune ligne** insérée ; 001–007 inchangés (empreinte `sqlite_master`) ; `foreign_key_list` = 3 `RESTRICT`, sans `ON UPDATE` ; `integrity_check` / `foreign_key_check` vides |
| **B CHECK de colonnes** | `garantie_type` (3 valides ; casse, espaces, vide, NULL, voisins refusés) ; dates (29/02 bissextile, 31/12, 01/01, `0001-01-01` ; 30/02, 29/02 non bissextile, 13ᵉ mois, `2026-1-1`, avec heure, vide, NULL refusés) ; `fin = début`, `fin < début`, `fin = début + 1 jour` ; `created_at` ; NOT NULL ×6. *(Les BEFORE masquent certains codes : un NULL sur la facture lève INV-85, pas « NOT NULL » — chaque test vérifie le code attendu.)* |
| **C Unicité et idempotence** | doublon `(ligne, type)` refusé ; même type sur 2 lignes accepté ; 2 types sur 1 ligne accepté ; `INSERT OR IGNORE` rejoué = 0 ligne, **première date conservée** (rejeu au 2ᵉ solde avec date différente) ; rejeu partiel complète seulement les manquantes ; UPSERT `DO UPDATE` refusé ; `INSERT OR REPLACE` refusé (témoin `recursive_triggers=OFF` documenté) |
| **D Durées et 29/02** (QO-2) | table de vérité 3 types × dates (fin d'année, 31 janvier, 28/02, **29/02 de 2000, 2028, 2096**, 01/01, `0001-01-01`) ; valeurs fausses (±1 jour, ±1 an, type permuté, 29/02 conservé, 01/03) refusées ; `9999-12-31` → année à 5 chiffres refusée ; **témoin** `date(x,'+1 year')` = 01/03 (ce que le service ne doit pas faire) ; balayage différentiel contre l'oracle |
| **E FK et suppression des parents** | DELETE de `bons_commande`, `bc_lignes`, `factures` référencés refusés (tr_19, tr_13, tr_21) ; FK `RESTRICT` éprouvée sur base **sans triggers** avec `foreign_keys=ON` ; ids volontairement distincts (`bc_id`/`bc_ligne_id`/`facture_declenchement_id`, leçon 006) |
| **F `tr_50`** | UPDATE de **chaque** colonne, UPDATE no-op, `UPDATE OR REPLACE/IGNORE`, UPSERT, DELETE (simple, multi-lignes), `INSERT OR REPLACE` ; code INV-87 ; aucune modification résiduelle |
| **G `tr_51`** (selon QO-1/QO-3) | G1 : `bc_id` incohérent, ligne d'un autre BC, ligne inexistante ; G2 : facture acompte / situation / avoir / solde d'un autre BC / inexistante / NULL ; G3 : type absent de `bc_ligne_garanties`, ligne sans garantie de ligne ; G4 : date ≠ `date_emission` (±1 jour) ; G6 (si retenue) : 2ᵉ solde refusé, y compris au rejeu |
| **H Scénarios métier** (service émulé) | C-04 : solde → garanties de toutes les lignes ; **BC sans garantie de ligne** → 0 ligne, pas d'erreur ; multi-devis (C-34) : lignes des deux devis ; **solde 0.00** (C-08, DV-9) déclenche ; **situation à 100 % sans solde** → aucune garantie (DV-5) ; C-07 : avoir partiel → inchangé ; **T-14 : avoir total sur le solde** → garanties, `facture_declenchement_id` et dates inchangés, BC `termine → en_cours`, **nouveau solde** → rejeu `IGNORE` = 0 ligne, première date conservée (distincte de `date_100_facture`, VR-10) ; solde **impayé** → garanties créées (indépendance du paiement) ; règlement / annulation / remboursement → empreinte de `garanties` inchangée ; BC annulé après solde → garanties conservées ; avoir sur BC annulé / `termine` ; rattachement de devis après solde refusé (tr_99) ⇒ complétude ; absence de PV |
| **I Import** | BC `origine='import'` + factures importées : `bc_ligne_garanties` vides ⇒ aucune garantie insérable (G3) ; mêmes gardes pour toute origine (INV-131) ; ligne de BC importée sans garantie de ligne ; CK-07 vide |
| **J Diagnostics** | CK-07a (manquante, y compris BC dont le **solde est totalement crédité**, Z-4) ; CK-07b (orpheline, date erronée, mauvais BC, base sans triggers) ; CK-07c ; BC sans solde → rien d'attendu ; lecture seule (empreinte avant/après) |
| **K Non-régression** | suites 001→007 inchangées (1344 tests) ; 008 n'écrit ni ne lit `bons_commande`, `bc_ligne_garanties`, `factures`, `reglements`, `numerotation_sequences` (empreintes) ; texte des triggers 001–007 identique ; chaîne rejouée sur base vide et peuplée |
| **L Données malformées / contournements** | BLOB, REAL, INTEGER dans colonnes TEXT (STRICT), NUL, espaces, casse, années extrêmes ; `recursive_triggers=OFF` (témoin) |
| **M Atomicité** | `INSERT … SELECT` multi-lignes partiellement invalide ⇒ rien ; `SAVEPOINT`/`ROLLBACK` ; `sqlite_sequence` cohérent |

**Volume visé** : 180 à 230 tests (1 table, 3 index, 3 triggers + CK). **Mutation** (phase suivante, après validation et livraison SQL + tests, comme en 007) : mutants du seul `008_garanties.sql` — listes `IN`, littéraux `1/2/10`, `'02-29'`, `substr`, `GLOB`, `>`/`>=`, `WHERE` des gardes, `CASE` — chaque survivant qualifié individuellement ; **non lancée ici**.

---

## 6. Contradictions et lacunes documentaires

| # | Source / section | Constat | Conséquence pour 008 | Correction minimale proposée |
|---|---|---|---|---|
| Z-1 | `docs/conception/` | Le modèle V3.13 n'existe que dans `fichiers-a-relire/` ; `docs/` contient la V3.12 (identique à V3.13 sur le DDL de `garanties`) | Aucune dépendance bloquante (tableau §0) | Reporter les `MAJ__*` dans `docs/` (hors 008, à votre main) |
| Z-2 | Officiels `docs/` : `invariants.md` INV-87 (l.128), INV-38 (l.67), INV-86 (l.127) ; `modèle-métier-V6.md` §24 (l.599) ; `cdc-fonctionnel…` §24 (l.717) ; V3.12 §4.10 / T-14 | « annulation du solde » (mécanisme **obsolète, E-14**) ; INV-38 : « régénère `bc_lignes`, garanties de lignes… » (obsolète, E-10 : plus de régénération) ; pas de copie des garanties au rattachement | 008 suit E-14 et les `MAJ__` | Reporter les `MAJ__invariants`, `MAJ__modèle-métier`, `MAJ__modèle SQLite` |
| Z-3 | `MAJ__cdc-fonctionnel…` §24 : amendement (l.717) vs corps (l.740) ; `MAJ__audit-fonctionnel` l.290 | L'amendement annonce « « L'annulation du solde » est remplacée par « un avoir (même total) sur le solde » », mais le corps (l.740) et l'audit (l.290) disent encore « l'annulation du solde » | Aucun (E-14 prime) | Remplacer dans l.740 et l.290 par « un avoir (même total) sur le solde » |
| Z-4 | Mod. §14 (l.1129) et V3.12 (l.884) : **CK-07** « garanties d'un BC ayant un solde **actif** » | Aucune formule ; et « solde actif » rendrait CK-07 **aveugle** pour un BC dont le solde est totalement crédité alors que ses garanties doivent persister (INV-87, T-14) | CK-07 défini en a/b/c (§4) sur « BC ayant **ou ayant eu** un solde » | Libellé : « garanties d'un BC ayant (ou ayant eu) un solde » + formules §4 |
| Z-5 | Mod. §9 (l.817) / V3.12 (l.655) | La liste impose `garanties(bc_ligne_id)`, alors que la règle de tête du même §9 dit que l'index d'un `UNIQUE` commençant par la FK en tient lieu | 3 index au lieu de 4 (le 4ᵉ serait un doublon exact) | Retirer `garanties(bc_ligne_id)` de la liste |
| Z-6 | Inv. INV-86 / INV-87, colonne « Cas » (l.122-123) | Renvoient à **C-20**, marqué **OBSOLÈTE (E-14)** (remplacé par C-33) | Cosmétique ; tests référencent C-04, C-07, C-08, C-33, C-34, T-14 | « C-20 » → « C-33 » |
| Z-7 | INV-88 « 29 février → 28 février » vs Mod. §4.10 « … si l'année cible n'est pas bissextile » | Équivalents pour +1/+2/+10 ans (CT-3) : **pas de vraie contradiction** | Service inconditionnel + tests | Aucune (note possible dans INV-88) |
| Z-8 | INV-90 « native : ligne et facture de déclenchement NOT NULL » | « native » est un reliquat du mode migration V3.5 (supprimé V3.6, D-23, INV-134 « NOT NULL sans exception ») | Aucune garantie non native : NOT NULL partout | Supprimer « native » |
| Z-9 | Mod. §8 | Seul TR-50 existe ; les gardes d'insertion (G1-G4) n'ont pas de numéro | `TR-51` proposé | Ajouter TR-51 au §8 après arbitrage QO-1 |
| Z-10 | Mod. §3.4 (l.226) et CDC §24-25 | `a_surveiller` « avant échéance » / `echue` « après `date_fin_suivi` » : le **jour même** de `date_fin_suivi` n'est classé nulle part | Aucun effet SQL (état dérivé) | [PR service/UI] `echue` ⇔ jour courant **>** `date_fin_suivi` (lecture littérale de « après ») ; à fixer à l'écriture du service |
| Z-11 | CDC §24 « franchissement de 100 % facturé » vs DV-5 (`avancement` peut valoir 100.00 par situations sans solde) | Lecture ambiguë du déclencheur | Résolu par Mod. §3.2 (l.197 : « 100 % facturé = présence d'un solde »), INV-85, DV-5 | Aucune ; test dédié (groupe H) |

Aucune de ces lacunes ne contredit le **DDL** ni le **comportement** décidés de `garanties`.

---

## 7. Points bloquants et arbitrages

**Points bloquants : aucun.** Le DDL, TR-50, l'idempotence, les durées et l'effet des avoirs/règlements sont entièrement décidés (§1) ; aucune règle n'est inventée.

**Arbitrages proposés** (non bloquants ; une valeur par défaut est recommandée, comme pour Q1-Q3 de 007) :

- **QO-1 — Gardes d'insertion croisées G3 + G4** (en plus de G1 + G2, [CT]). *G3* : la garantie doit exister dans `bc_ligne_garanties` de la ligne (INV-86 « création lue dans `bc_ligne_garanties` ») ; *G4* : `date_declenchement = date_emission` de la facture (INV-87). Raison : la table est **immuable** (TR-50) — une ligne erronée ne se corrige jamais ; G3 rend en outre INV-134 (« un BC importé ne génère aucune garantie ») vrai en SQL. Coût : deux `WHERE`. **Recommandé : oui.** *Si non* : tr_51 se limite à G1 + G2 ; CK-07b porte G3/G4.
- **QO-2 — CHECK de durée exacte** (INV-88 « SVC, test »). Le service calcule ; le CHECK ne fait que **vérifier** (+1/+2/+10, 29/02 → 28/02), sur une seule ligne, sans lecture d'autre table. Même raison d'irréparabilité. **Recommandé : oui.** *Si non* : seul `fin > début` reste ; CK-07b + oracle de test portent la règle.
- **QO-3 — Garde « premier solde » en SQL (G6).** **Recommandé : non.** Un `BEFORE INSERT` s'exécute avant la détection du doublon : au 2ᵉ solde, un rejeu `INSERT OR IGNORE` (légitime, idempotent) ferait **échouer** la transaction au lieu d'être ignoré (sondé). La règle « premier solde » reste au service (§4) et au diagnostic CK-07c.

**Points d'information (service/UI, non bloquants, à ne pas rouvrir ici)** :
- **P-1** Jour d'échéance : voir Z-10.
- **P-2** Événement `declenchement_garantie` : un par BC ou par garantie ? À fixer avec la tranche `historique`.
- **P-3** Limite assumée : 004/005b autorisent en SQL un `INSERT` tardif dans `bc_ligne_garanties` d'un BC non annulé (même après solde, hors TR-99 qui ne garde que le lien devis) ; 008 ne le corrige pas (001–007 intouchables) — CK-07a le détecte. Idem pour `bc_ligne_garanties` sur un BC importé (INV-134).

---

## Conclusion

**Cadrage prêt à valider.** Aucun point bloquant. Il reste **trois arbitrages simples** (QO-1 : G3+G4 ; QO-2 : CHECK de durée ; QO-3 : G6) avec recommandation : **oui / oui / non**. Après validation : implémentation `008_garanties.sql` → `test_008_garanties.py` → mutation → contrôles finaux → rapport (même ordre qu'en 007).

## Livraison
Ce seul fichier : `fichiers-a-relire/CADRAGE__008_garanties.md`. Aucun `008_garanties.sql`, aucun test modifié, aucun document officiel modifié, aucune mutation lancée, V3.13 non déplacée. Aucun push effectué (vous poussez vous-même).
