# CADRAGE 008 — Garanties

Tranche 008 (rang 11) : future `src-tauri/migrations/metier/008_garanties.sql` + `src-tauri/tests/metier/test_008_garanties.py` (T-50). **Ce document est un cadrage : aucun fichier SQL, test ou document officiel n'est créé ou modifié.**
Statut : **RÉVISÉ le 2026-10-09 après les arbitrages de Rémy (QO-1 oui, QO-2 oui, QO-3 non — §1.6) le traitement des dates extrêmes (§3.6) et le renforcement de la post-condition du service (§4.1, groupe O) ; en attente de validation avant écriture du SQL et des tests.** Dépôt lu : `main` @ `a9fd50f`.

Légende des étiquettes :
**[RD]** règle documentée · **[DV]** décision déjà validée (errata, cadrages 006/007, D-xx) · **[CT]** conséquence technique (déduite, aucune règle nouvelle) · **[PR]** proposition (à arbitrer) · **[QO]** question ouverte. *Révision 2026-10-09 : les trois [PR] de la première version sont devenues **[DV]** (arbitrages du 2026-10-09).*

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
| La règle « premier solde » (une seule tentative de création, au premier solde du BC) est portée par le **service**, pas par le SQL, pour préserver l'idempotence du rejeu `INSERT OR IGNORE` | [DV] | **QO-3 : NON** (Rémy, 2026-10-09) ; §1.6 |
| Tout devis rattaché l'est **avant** la rédaction du solde (TR-99) : toutes les lignes du BC et leurs garanties de ligne existent au premier solde ; une ligne supprimée (brouillon) n'a plus de garantie ; **aucun nouveau mécanisme de garantie** | [RD][DV] | INV-87, INV-187 ; D-47 ; E-16 (errata MAJ l.23) ; PT-18 (Mod. l.1387) ; 006 `tr_99_bc_devis_apres_solde` (l.483) |

### 1.3 Durées et dates
| Règle | Étiquette | Source |
|---|---|---|
| `date_fin_suivi` = `date_declenchement` **+1 an** (parfait achèvement) / **+2 ans** (biennale) / **+10 ans** (décennale) | [RD] | INV-88 ; Mét. §24 (l.631) ; Mod. §4.10 |
| **29 février → 28 février** | [RD] | INV-88 ; Mod. §4.10 (« si l'année cible n'est pas bissextile ») — équivalence démontrée en [CT-3] |
| Suivi interne, libellé toujours « Suivi interne BATORYA — date indicative » ; état **dérivé** `a_surveiller` / `echue` | [RD] | INV-88, INV-89 ; Mod. §3.4 (l.226) ; CDC §24-25 |
| Dates au format `YYYY-MM-DD` réel (famille D : `GLOB` + `date(x) IS x`, année sur **4 chiffres**), aucune borne d'année **métier** (INV-177 : 2001-2099 réservé aux dates de numérotation annuelle, contrôle de service) ; « jour courant » = date locale | [RD] | INV-10 (Inv. l.35) ; Mod. §2 famille D (l.78) ; INV-177 (Inv. l.41) ; Mod. l.83 |
| Une date de fin **non représentable** en famille D (année > 9999) n'est ni tronquée ni bornée : voir §3.6 | [CT] | INV-10, INV-88 ; §3.6 |

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

### 1.6 Arbitrages validés par Rémy (2026-10-09)
| Arbitrage | Décision | Effet sur le cadrage |
|---|---|---|
| **QO-1** | **OUI** — deux gardes d'insertion supplémentaires : G3 (la garantie existe dans `bc_ligne_garanties` de la ligne) et G4 (`date_declenchement = date_emission` de la facture) | `tr_51_garanties_insert` = **G1 + G2 + G3 + G4** (§3.3) |
| **QO-2** | **OUI** — `CHECK` de durée exacte selon le type, **y compris 29 février → 28 février** | CHECK **G5** dans la table (§2, §3.1) |
| **QO-3** | **NON** — pas de garde « premier solde » en SQL ; la règle reste au service, pour préserver l'idempotence (rejeu `INSERT OR IGNORE` sans erreur) | G6 **abandonnée** ; CK-07c reste un diagnostic ; test de rejeu au 2ᵉ solde (§5, groupe C) |
| Dates extrêmes | Traitement technique de §3.6 (aucune borne métier nouvelle) ; soumis à validation avec ce cadrage révisé | §3.6, §4, §5 groupe N, Z-12 |
| Post-condition du service renforcée | Correction ciblée du 2026-10-09 09:54 : complétude, facture = premier solde, dates exactes, rattachement ; erreur et **rollback intégral** de l'émission. **Aucune garde SQL ajoutée ; QO-1/2/3 inchangées ; aucune règle métier nouvelle** | §4.1, §5 groupe O, Z-14, P-5 à P-7 |

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
    -- [DV] QO-2 (G5) : durée exacte par type (+1 / +2 / +10 ans), 29/02 -> 28/02
    CHECK (date_fin_suivi = printf('%04d', CAST(substr(date_declenchement, 1, 4) AS INTEGER)
                                         + CASE garantie_type WHEN 'parfait_achevement' THEN 1 WHEN 'biennale' THEN 2 ELSE 10 END)
                            || CASE WHEN substr(date_declenchement, 6, 5) = '02-29' THEN '-02-28' ELSE substr(date_declenchement, 5) END),
    CHECK (created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]Z')
) STRICT;
```
*(Esquisse du cadrage, éprouvée sur une copie jetable de la chaîne 001→007 hors dépôt : STRICT, FK `RESTRICT` sans `ON UPDATE`, CHECK, UNIQUE, index et triggers se comportent comme décrit ci-dessous. Ce n'est pas le livrable `008_garanties.sql`.)*

**Contenu retenu après arbitrages : 1 table, 3 index, 3 triggers** (`tr_50_garanties_update`, `tr_50_garanties_no_delete`, `tr_51_garanties_insert` portant G1 à G4). Aucun trigger supplémentaire n'est nécessaire pour les dates extrêmes (§3.6).

**Absences voulues** : `statut`, `updated_at`, `origine`/`legacy_*`, `prestation_id`/`designation` (lisibles via `bc_lignes`), `active`, numéro, `facture_declenchement_id` NULL. Les types (`INTEGER`/`TEXT`) sont ceux de 004/006.

---

## 3. Triggers, index et contraintes nécessaires

### 3.1 Contraintes de table
| Contrainte | Étiquette | INV |
|---|---|---|
| 6 colonnes `NOT NULL` (`bc_id`, `bc_ligne_id`, `garantie_type`, 2 dates, `facture_declenchement_id`) | [RD] | 90, 134 |
| `UNIQUE(bc_ligne_id, garantie_type)` — rempart de l'idempotence ; son index couvre la FK `bc_ligne_id` | [RD] | 86 |
| CHECK `garantie_type IN (3 valeurs)`, dates réelles (famille D, année sur 4 chiffres), TS | [RD][CT] | 88 |
| CHECK `date_fin_suivi > date_declenchement` | [RD] | 88 |
| CHECK durée exacte par type (29/02 → 28/02) — **G5** | **[DV] QO-2** | 88 |
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
| — **G3** | idem | `(bc_ligne_id, garantie_type)` existe dans `bc_ligne_garanties` (« création lue dans `bc_ligne_garanties` ») ; rend impossible toute garantie sur un BC importé (INV-134) | 86, 134 | **[DV] QO-1** |
| — **G4** | idem | `date_declenchement = factures.date_emission` de la facture de déclenchement | 87 | **[DV] QO-1** |
| ~~G6~~ | — | ~~la facture est le premier solde du BC~~ — **abandonnée** : reste au service (rejeu idempotent préservé) | 87 | **[DV] QO-3 : NON** |

*Numérotation : `TR-50` est celui du modèle ; `TR-51` est **retenu** pour les gardes d'insertion (libre dans Mod. §8, qui passe de TR-50 à TR-60) — à reporter dans le modèle après validation (Z-9).*

### 3.4 Protections anti-contournement
`INSERT OR REPLACE` (DELETE implicite refusé) ; `UPDATE OR REPLACE/IGNORE` (RAISE(ABORT) non altéré par `OR`) ; **UPSERT `ON CONFLICT … DO UPDATE`** (déclenche `BEFORE UPDATE` → refusé, sondé) ; `INSERT OR IGNORE` rejoué : sans violation de garde, 0 ligne, aucune erreur, première date conservée (sondé) ; ré-INSERT d'un doublon avec une garde fausse → **ABORT** (un `BEFORE` s'exécute avant la détection du doublon, sondé : c'est pourquoi G6 est abandonnée (QO-3 : NON)). **Limite assumée (D-39)** : avec `recursive_triggers=OFF`, le DELETE implicite d'un `REPLACE` échapperait à `tr_50_garanties_no_delete` (sondé : la ligne est remplacée, id changé) — réglage de connexion, testé comme en 006/007. Octet NUL et saturation int64 : limites transverses 001–007, sans objet spécifique ici (aucun montant).

### 3.5 Conséquences techniques
- **CT-1** Les triggers de 008 ne lisent ni `reglements`, ni `bons_commande.statut`, ni les avoirs : une garantie est **indépendante du paiement et de l'état du BC** (INV-85, INV-87).
- **CT-2** Aucun trigger n'est posé sur `factures`/`reglements`/`bc_ligne_garanties` : l'immutabilité de 004/005b/006 suffit (avoir, règlement, annulation de règlement : aucune écriture dans `garanties`).
- **CT-3** *29/02* : pour une origine bissextile `Y`, les années cibles `Y+1`, `Y+2`, `Y+10` sont ≡ 1, 2, 2 (mod 4) : **jamais bissextiles**. « 29/02 → 28/02 » (INV-88) et « → 28/02 si l'année cible n'est pas bissextile » (Mod. §4.10) sont donc **équivalents** pour les trois durées ; la condition est du code mort. Piège : `date('2028-02-29','+1 year')` renvoie `2029-03-01` (sondé) — le service ne doit pas utiliser les modificateurs de date SQLite.
- **CT-4** Complétude : TR-99 (006) interdit tout rattachement après un solde ; au premier solde, `bc_ligne_garanties` est complet (lignes de **tous** les devis). Le SQL de 008 n'impose pas cette complétude (limite assumée) ; **CK-07a** la diagnostique.
- **CT-5** Aucun garde « BC non annulé » sur `garanties` : aucune source ne le prévoit (les garanties ne sont pas du contenu contractuel, INV-173) et la naissance exige un solde, déjà refusé sur BC annulé (`tr_16`, INV-188). Une garantie existante survit à l'annulation du BC.

### 3.6 Dates extrêmes : date de fin non représentable (analyse et traitement retenus)

**Constat.** `date_fin_suivi` = année + N (N = 1, 2 ou 10). Pour une année de départ `Y`, la fin n'est représentable en famille D (année sur 4 chiffres, INV-10, Mod. §2 l.78) que si `Y + N ≤ 9999` : parfait achèvement jusqu'à `Y = 9998`, biennale jusqu'à `9997`, décennale jusqu'à `9989`. Au-delà, `printf('%04d')` produit 5 chiffres (`10000-…`) : refusé par le `GLOB` de `date_fin_suivi` et par le CHECK de durée. Côté bas, `0000-01-01` est une date valide (famille D) et n'a aucun effet (+N reste positif).

**Au regard des invariants et conventions.**
- INV-177 borne **uniquement** les dates de numérotation (2001-2099, contrôle de service, « jamais un CHECK ») ; la date d'émission d'une facture V6 est donc ≤ 2099 en flux nominal, et `date_fin_suivi` ≤ 2109 : **le cas est inatteignable par le service**. Il reste atteignable en SQL direct (le SQL ne borne pas l'année) : les années `9990`-`9999` ont un `yy` de numérotation valide (`90`-`99`), contrairement à `9900`/`0000`/`2000` (`yy = 00` impossible).
- INV-88 impose les durées exactes, INV-134 « une garantie n'est jamais recalculée », INV-85/86 qu'un solde V6 porte les garanties de ses lignes. Aucune source ne prévoit de **tronquer** (ex. `9999-12-31`), de **décaler** ou d'**omettre** une garantie : le faire serait **inventer une règle** (et violerait INV-88).

**Comportement technique attendu (aucune borne métier nouvelle).**
1. **SQL** : une ligne dont la fin n'est pas représentable est **refusée par contrainte** (CHECK, sans préfixe `INV-nn`) ; aucun trigger, aucune borne d'année ajoutée. La limite est celle du **format de date** (convention existante), pas une règle métier.
2. **Piège établi (sondé, chaîne 001→007 + esquisse 008)** : `INSERT OR IGNORE` ignore **aussi** les violations de `CHECK` et de `NOT NULL` (seuls les `RAISE(ABORT)` des triggers et les FK y échappent). Avec un solde daté `9990-06-01` (BC à garanties décennale, biennale, parfait achèvement), le `INSERT OR IGNORE … SELECT` naïf du service renvoie **sans erreur** `rowcount = 2` sur 3 attendues : le solde existerait avec des garanties **partielles**, en silence. Résultats sondés : `9989-06-01` → 3 ; `9990-06-01` → 2 ; `9997-06-01` → 2 ; `9998-06-01` → 1 ; `9999-06-01` et `9999-12-31` → 0. **Le CHECK seul ne suffit donc pas à faire échouer la transaction.**
3. **Service (obligatoire, [CT])** — détaillé en **§4.1** (procédure, mode PREMIER / REJEU, post-condition C1 à C8) :
   a. **calcul préalable pur** de toutes les dates de fin (arithmétique civile entière, sans SQLite) *avant la réservation du numéro* et avant toute écriture : si une seule année de fin dépasse 9999 → erreur typée `DateFinSuiviHorsFormat` (BC, ligne, type, date de déclenchement) ; **rien n'a été écrit et le compteur de numérotation est inchangé** ;
   b. `INSERT OR IGNORE` (inchangé, [RD]) ;
   c. **post-condition C1 à C8 dans la même transaction**, en dernier, juste avant le `COMMIT` (§4.1) : elle ferme aussi tout autre `IGNORE` silencieux (valeur de CHECK, NOT NULL).
4. **Transaction (décision technique)** : l'impossibilité de calculer **ou** d'enregistrer une date de fin **fait échouer toute la transaction d'émission du solde** (facture, lignes, garanties, caches du BC et toute autre écriture de la transaction) : **ROLLBACK intégral**. Raison : « un solde sans garantie attendue » est l'état que CK-07a doit détecter (INV-85/86), non un état à produire ; une garantie ne peut pas être « rattrapée plus tard » (sa date est celle du solde, immuable, INV-87, jamais recalculée, INV-134). Conséquence : un solde ne peut être émis à une date dont la fin de suivi dépasse 9999 **pour un BC portant une garantie du type concerné** ; un BC sans garantie de ligne, ou dont les types présents restent représentables, n'est pas affecté. Numérotation : voir §4.1 (trou admis après une réservation, jamais réutilisé ; Z-14).
5. **Diagnostic** : CK-07a (manquante) et CK-07b (date de fin ≠ formule) détectent a posteriori tout écart (import, restauration, SQL direct).

*Non retenu (et pourquoi)* : borne d'année sur `date_declenchement` (nouvelle borne métier) ; troncature à `9999-12-31` (invente une date, viole INV-88) ; garantie omise avec avertissement (viole INV-85/86) ; remplacement de `OR IGNORE` par `WHERE NOT EXISTS` (rouvrirait une décision : Mod. §4.10, INV-86, conv. §9) ; doublon du CHECK de durée en `RAISE(ABORT)` dans `tr_51` : renforcement possible, **non retenu** (voir P-4).

---

## 4. Ce qui relève du service applicatif (ne passe pas en SQL)

| Règle | Pourquoi pas SQL |
|---|---|
| **Détecter** le déclenchement : émission du **premier solde du BC** (type `solde`, jamais `avancement = 100.00`, DV-5), solde à 0.00 inclus après confirmation (DV-9) | État du BC et ordre d'émission : service financier (INV-46, INV-164) |
| Créer les garanties **dans la même transaction que le solde** ; tout échec de calcul, d'insertion ou de **post-condition (§4.1)** ⇒ **rollback intégral de l'émission** (facture, lignes, garanties, caches du BC, toute autre écriture) : sinon fenêtre « solde sans garantie » (CK-07a). Numérotation : §4.1 | Atomicité = transaction du service [CT] |
| Lire `bc_ligne_garanties` de **toutes** les lignes du BC (tous devis rattachés) ; déterminer le mode **PREMIER / REJEU** (§4.1) ; ne créer qu'en PREMIER (au 2ᵉ solde, par exemple après avoir total : 0 ligne créée, garanties historiques intactes **et vérifiées** par la post-condition) | Règle de déclenchement (INV-85/86) ; garde « premier solde » en SQL **refusée** (QO-3 : NON, [DV]) |
| **Calculer** `date_fin_suivi` (+1/+2/+10 ans, 29/02 → 28/02) en arithmétique civile, **sans** `date(x,'+N year')` | INV-88 : garde « SVC, test » ; le CHECK QO-2 ne fait que **vérifier** |
| `INSERT OR IGNORE` uniquement ; jamais `REPLACE`, jamais UPSERT. **Calcul préalable pur de toutes les dates de fin + post-condition C1 à C8 (§4.1) dans la transaction** ; toute date de fin non représentable, garantie manquante, incohérente ou mal rattachée ⇒ **erreur et rollback de l'émission** (§3.6, §4.1) | conv. §9 ; `OR IGNORE` masque les violations de CHECK/NOT NULL (sondé) |
| Vérifier que toute garantie référence le **premier solde** du BC et porte sa date d'émission (règle de service, **sans garde SQL**) | QO-3 : NON ; post-condition C4/C5 (§4.1) |
| États dérivés `a_surveiller` / `echue`, libellé « Suivi interne BATORYA — date indicative », jour courant = date locale | INV-89 ; jamais persistés |
| Consultation par BC / client / prestation / type / dates (jointures sur `bc_lignes`, `bons_commande`, `clients`) | CDC §25 ; aucun module « Garanties » (Mét. l.145) |
| Événement `declenchement_garantie` dans `historique` (INV-110, INV-194) | `historique` n'est pas encore créée (D-34 : tranche propre) ; hors 008 ; granularité (par BC ou par garantie) non décidée — voir §7, P-2 |
| Copie des garanties de ligne devis → BC (création, rattachement), refus après solde | 004/005b/006 (déjà livrés) |
| Contrat d'import : aucune garantie ni garantie de ligne ; CK-07 après import et restauration | INV-134 ; Mod. §14 |
| Pas d'effet des PV et de leur levée sur les garanties | INV-95 ; Mét. l.614 |

### 4.1 Procédure d'émission du solde et post-condition renforcée *(correction ciblée du 2026-10-09)*

Règle de **service** [CT] : aucune règle métier nouvelle, aucune garde SQL ajoutée (QO-1/2/3 inchangées, G6 toujours abandonnée). Les valeurs attendues sont **recalculées par le service** à partir du premier solde du BC et de `bc_ligne_garanties` ; elles ne sont tirées ni des lignes de `garanties` déjà persistées ni de l'expression du CHECK (sinon une ligne fausse validerait sa propre vérification). **Une garantie n'est pas valide du seul fait que sa ligne existe.**

**Définitions.** `b` = BC ; `E` = paires `(bc_ligne_id, garantie_type)` de `bc_ligne_garanties` des lignes de `b` (`#E` = leur nombre) ; **R** = premier solde de `b` = le solde de plus petit `id` parmi les soldes de `b`, neutralisé ou non (convention technique, P-7) ; `D` = `R.date_emission` ; `fin(D, type)` = arithmétique civile entière du §3.6 (+1 / +2 / +10 ans, 29/02 → 28/02) ; **périmètre `P`** = garanties dont `bc_id = b` **ou** dont `bc_ligne_id` appartient à une ligne de `b` (voit aussi une garantie mal rattachée).
**Mode** — **PREMIER** : aucun autre solde de `b` n'existe avant le nouveau (R = le nouveau solde). **REJEU** : un solde antérieur existe (R = ce premier solde, **jamais** le nouveau).

**Séquence.**
1. **Pré-contrôles** (lecture seule, *avant* toute réservation de numéro) : toute `fin(D, type)` est représentable (avec la date d'émission prévue en PREMIER, `R.date_emission` en REJEU) ; en REJEU, C1 à C6 sur les garanties historiques. Échec ⇒ erreur typée, **rien n'est écrit, compteur de numérotation inchangé**.
2. **Réservation du numéro** de facture dans sa propre transaction (PT-1, inchangé).
3. `BEGIN IMMEDIATE` ; facture solde et lignes ; **mode et R relus dans la transaction** ; relevé de `P` (« avant »).
4. **PREMIER** : C8, puis `INSERT OR IGNORE` d'une garantie par paire de `E` (facture = R, `date_declenchement = D`, fin calculée). **REJEU** : aucune création attendue ; si le service tente l'`INSERT OR IGNORE` (valeurs de R), il doit renvoyer 0.
5. Recalcul des caches du BC et toute autre écriture de l'émission.
6. **Post-condition C1 à C8**, en dernier, juste avant le `COMMIT` (le pré-contrôle est une optimisation ; la post-condition fait foi).
7. `COMMIT`. Toute violation ⇒ erreur typée `PostConditionGaranties` (pour chaque violation : code Cn, BC, ligne, type, valeur attendue, valeur constatée) ⇒ `ROLLBACK`.

| Contrôle | Exigence (comparée aux valeurs attendues de R, jamais à une autre ligne persistée) | Reprend |
|---|---|---|
| **C1 Complétude** | chaque paire de `E` existe dans `garanties`, une seule fois | CK-07a |
| **C2 Pas de surplus** | aucune garantie de `P` dont la paire n'est pas dans `E` | CK-07b |
| **C3 Rattachement** | pour chaque garantie de `P` : `bc_id = b` **et** `bc_ligne_id` est une ligne de `b` | CK-07b |
| **C4 Facture déclenchante** | `facture_declenchement_id = R.id` (R : type `solde`, BC `b`) — **règle de service, pas de garde SQL** | CK-07c ; QO-3 |
| **C5 Date de déclenchement** | `date_declenchement = D` (date d'émission de R) | G4 ; INV-87 |
| **C6 Date de fin** | `date_fin_suivi = fin(D, garantie_type)` exactement (29/02 → 28/02) | G5 ; INV-88 |
| **C7 Effet de l'émission** | PREMIER : nombre de lignes créées `= #E` ; REJEU : **0** créée et `P` identique avant/après (id, valeurs, `created_at`) — aucune réparation silencieuse | INV-86, INV-134 |
| **C8 Pas de garantie préexistante (PREMIER)** | `P` vide avant les `INSERT` | INV-85 |

**Distinction des trois situations.**
| Situation | Reconnue par | Résultat |
|---|---|---|
| Création correcte au premier solde | mode PREMIER, `P` vide avant, C7 = `#E`, C1 à C6 satisfaits | `COMMIT` |
| Rejeu au solde suivant (après avoir total, ou nouveau solde) | mode REJEU, valeurs attendues prises sur R, 0 ligne créée, `P` inchangé, C1 à C6 satisfaits | `COMMIT` ; garanties historiques intactes (la date du nouveau solde n'entre jamais dans les valeurs attendues) |
| Garantie préexistante incohérente (mauvaise facture, date, fin, BC, ligne, surplus, manquante) | C2 à C6 ou C8 contre R | erreur + `ROLLBACK` ; **ni corrigée, ni supprimée, ni acceptée** (fail-closed, P-6) |

**Atomicité.** Toute violation, ou toute erreur aux étapes 3 à 6, annule la transaction d'émission : facture, lignes, garanties, caches du BC et toute autre écriture. L'état persisté revient à l'état d'avant l'émission, **à l'exception du seul compteur de numérotation après réservation** (ci-dessous).

**Numérotation** (PT-1 ; Mod. §11.4 ; INV-22, 25, 32, 179 ; E-13 ; E-14/INV-185). La demande « aucun numéro de facture ne doit être consommé si l'émission échoue, conformément aux règles de numérotation existantes » s'applique ainsi, **sans modifier la numérotation** : (i) échec détecté au pré-contrôle (étape 1) : **aucun numéro n'est réservé**, compteur inchangé ; (ii) échec après réservation (étapes 3 à 6) : **aucune facture ne porte ce numéro** (rollback), mais le compteur a avancé — **trou admis** par les règles existantes, jamais récupéré ni réutilisé ; le compteur ne décroît jamais. Le numéro n'est attribué à un objet persisté qu'à la validation. Voir Z-14, P-5.

*Esquisse éprouvée (service émulé sur copie jetable de la chaîne 001→007 + esquisse 008, hors dépôt)* : absence après `IGNORE` → C1 + C7 ; date de déclenchement fausse → C5 ; fin fausse → C6 ; mauvais BC → C3 ; mauvaise ligne → C1 + C2 + C3 ; garanties préexistantes rattachées au 2ᵉ solde → C4 + C5 + C6 ; rejeu légitime → 0 ligne, garanties identiques champ par champ, nouveau solde persisté ; garantie historique manquante au rejeu → C1 ; solde daté `9990-06-01` → refus au pré-contrôle. Après chaque échec, l'empreinte de **toutes** les tables est identique à l'état d'avant, `numerotation_sequences` (et son `sqlite_sequence`) mis à part pour les seuls échecs post-réservation. Avec 008 complet, une valeur de déclenchement fausse est déjà arrêtée par G4 (`INV-87`) : la post-condition est testée aussi sur une **base témoin** privée de `tr_51` et du CHECK G5, pour prouver qu'elle tient seule.

### 4.2 Requêtes de contrôle
(lecture seule, constantes de test ; **CK-07 n'ayant pas de formule dans les sources**, découpé en a/b/c sans nouveau numéro) :
- **CK-07a — garantie manquante** : pour tout BC ayant (ou ayant eu) un solde, toute paire `(ligne de BC, garantie_type)` de `bc_ligne_garanties` sans ligne dans `garanties` (esquisse éprouvée : renvoie 0 ligne sur un BC conforme). **C1** du service reprend cette requête dans la transaction du solde (§4.1).
- **CK-07b — garantie incohérente** : paire absente de `bc_ligne_garanties` ; `bc_id` ≠ BC de la ligne ; facture non-solde ou d'un autre BC ; `date_declenchement` ≠ `date_emission` ; `date_fin_suivi` ≠ formule INV-88 ; garantie sur un BC `origine = 'import'` (INV-134). **C2 à C6** du service reprennent ces contrôles, avec les valeurs attendues calculées depuis le premier solde (§4.1).
- **CK-07c — non premier solde** (diagnostic seul, G6 étant abandonnée) : `facture_declenchement_id` ≠ plus petit `id` des soldes du BC. En SQL : diagnostic seul. Le **service** applique la même règle en **C4** (§4.1), sans garde SQL : QO-3 inchangée.

---

## 5. Tests (`test_008_garanties.py`, T-50) — positifs, négatifs, limites, non-régression

**Infra réutilisée** de 006/007 : `migrer10` + application de 008 au rang 11 (`BEGIN IMMEDIATE`, fichier, `user_version = 11`, `COMMIT`), `Base9`/`monde()`, `emettre_solde`, `neutraliser`, `terminer_bc`/`annuler_bc`, `desynchroniser_ids` ; ajout d'une fabrique de devis **avec garanties de ligne**, d'un **service émulé** `declencher_garanties()` (arithmétique civile indépendante du SQL, **avec pré-contrôles, réservation du numéro, `INSERT OR IGNORE` et post-condition C1 à C8, §4.1**), d'un **oracle Python** de `date_fin_suivi` (voir groupe N), d'une **empreinte complète** de la base (toutes tables, `sqlite_sequence` compris, avec ou sans `numerotation_sequences`) et d'une **base témoin** (texte de 008 privé de `tr_51` et du CHECK G5, fixture de test, hors livrable). Assertion sur la **règle** (code INV du message ; état résultant par empreintes), jamais sur l'exécution. Connexion : `foreign_keys=ON`, `recursive_triggers=ON`.

| Groupe | Contenu |
|---|---|
| **A chaîne et structure** | migration 008 sur base 007 vide et peuplée ; `user_version = 11` ; 1 table STRICT, colonnes/ordre/NOT NULL/défauts exacts, aucune colonne statut/`updated_at`/`origine`/`legacy_*` ; 3 index + autoindex UQ ; 3 triggers ; **aucune ligne** insérée ; 001–007 inchangés (empreinte `sqlite_master`) ; `foreign_key_list` = 3 `RESTRICT`, sans `ON UPDATE` ; `integrity_check` / `foreign_key_check` vides |
| **B CHECK de colonnes** | `garantie_type` (3 valides ; casse, espaces, vide, NULL, voisins refusés) ; dates (29/02 bissextile, 31/12, 01/01, `0001-01-01` ; 30/02, 29/02 non bissextile, 13ᵉ mois, `2026-1-1`, avec heure, vide, NULL refusés) ; `fin = début`, `fin < début`, `fin = début + 1 jour` ; `created_at` ; NOT NULL ×6. *(Les BEFORE masquent certains codes : un NULL sur la facture lève INV-85, pas « NOT NULL » — chaque test vérifie le code attendu.)* |
| **C Unicité et idempotence** | doublon `(ligne, type)` refusé ; même type sur 2 lignes accepté ; 2 types sur 1 ligne accepté ; `INSERT OR IGNORE` rejoué = 0 ligne, **première date conservée** ; **QO-3 : rejeu au 2ᵉ solde (date et facture différentes) = 0 ligne et aucune erreur** (idempotence préservée, aucune garde « premier solde ») ; rejeu partiel complète seulement les manquantes ; UPSERT `DO UPDATE` refusé ; `INSERT OR REPLACE` refusé (témoin `recursive_triggers=OFF` documenté) |
| **D Durées et 29/02** (QO-2, G5) | table de vérité 3 types × dates (fin d'année, 31 janvier, 28/02, **29/02 de 2000, 2028, 2096, 9996**, 01/01, `0001-01-01`, `0000-01-01`) ; valeurs fausses (±1 jour, ±1 an, type permuté, 29/02 conservé, 01/03) refusées ; **témoin** `date(x,'+1 year')` = 01/03 (ce que le service ne doit pas faire) ; balayage différentiel contre l'oracle |
| **E FK et suppression des parents** | DELETE de `bons_commande`, `bc_lignes`, `factures` référencés refusés (tr_19, tr_13, tr_21) ; FK `RESTRICT` éprouvée sur base **sans triggers** avec `foreign_keys=ON` ; ids volontairement distincts (`bc_id`/`bc_ligne_id`/`facture_declenchement_id`, leçon 006) |
| **F `tr_50`** | UPDATE de **chaque** colonne, UPDATE no-op, `UPDATE OR REPLACE/IGNORE`, UPSERT, DELETE (simple, multi-lignes), `INSERT OR REPLACE` ; code INV-87 ; aucune modification résiduelle |
| **G `tr_51`** (G1 à G4, validés) | G1 : `bc_id` incohérent, ligne d'un autre BC, ligne inexistante ; G2 : facture acompte / situation / avoir / solde d'un autre BC / inexistante / NULL ; G3 : type absent de `bc_ligne_garanties`, ligne sans garantie de ligne, BC importé ; G4 : date ≠ `date_emission` (±1 jour) ; **absence de G6** : une garantie référençant un 2ᵉ solde est acceptée si G1-G4 passent (INTERPRETATION documentée, la règle « premier solde » étant au service) |
| **H Scénarios métier** (service émulé) | C-04 : solde → garanties de toutes les lignes ; **BC sans garantie de ligne** → 0 ligne, pas d'erreur ; multi-devis (C-34) : lignes des deux devis ; **solde 0.00** (C-08, DV-9) déclenche ; **situation à 100 % sans solde** → aucune garantie (DV-5) ; C-07 : avoir partiel → inchangé ; **T-14 : avoir total sur le solde** → garanties, `facture_declenchement_id` et dates inchangés, BC `termine → en_cours`, **nouveau solde** → rejeu `IGNORE` = 0 ligne, première date conservée (distincte de `date_100_facture`, VR-10 ; contrôles détaillés en O6) ; solde **impayé** → garanties créées (indépendance du paiement) ; règlement / annulation / remboursement → empreinte de `garanties` inchangée ; BC annulé après solde → garanties conservées ; avoir sur BC annulé / `termine` ; rattachement de devis après solde refusé (tr_99) ⇒ complétude ; absence de PV |
| **I Import** | BC `origine='import'` + factures importées : `bc_ligne_garanties` vides ⇒ aucune garantie insérable (G3) ; mêmes gardes pour toute origine (INV-131) ; ligne de BC importée sans garantie de ligne ; CK-07 vide |
| **J Diagnostics** | CK-07a (manquante, y compris BC dont le **solde est totalement crédité**, Z-4) ; CK-07b (orpheline, date erronée, mauvais BC, base sans triggers) ; CK-07c ; BC sans solde → rien d'attendu ; lecture seule (empreinte avant/après) |
| **K Non-régression** | suites 001→007 inchangées (1344 tests) ; 008 n'écrit ni ne lit `bons_commande`, `bc_ligne_garanties`, `factures`, `reglements`, `numerotation_sequences` (empreintes) ; texte des triggers 001–007 identique ; chaîne rejouée sur base vide et peuplée |
| **L Données malformées / contournements** | BLOB, REAL, INTEGER dans colonnes TEXT (STRICT), NUL, espaces, casse, années extrêmes ; `recursive_triggers=OFF` (témoin) |
| **M Atomicité** | `INSERT … SELECT` multi-lignes partiellement invalide ⇒ rien (avec `INSERT` simple) ; `SAVEPOINT`/`ROLLBACK` ; `sqlite_sequence` cohérent ; atomicité de l'**émission complète** du solde : groupe O |
| **N Dates extrêmes** (§3.6) | voir ci-dessous |
| **O Post-condition du service et atomicité de l'émission** (§4.1) | voir ci-dessous |

**Groupe N — dates extrêmes, avec oracle indépendant.**
- **Oracle 1 (entiers purs, sans SQLite ni `datetime`)** : `fin_attendue(debut, type) → 'YYYY-MM-DD' | None` : `y, m, d` extraits par découpe de chaîne ; `y' = y + N` ; si `(m, d) = (02, 29)` alors `d = 28` ; si `y' > 9999` → `None` (non représentable) ; sinon formatage `%04d-%02d-%02d`. Fonction `bissextile(y)` propre au test (règle grégorienne 4/100/400), utilisée pour valider les dates d'entrée.
- **Oracle 2 (indépendant du premier)** : `datetime.date` de Python (années 1-9999) : `date(y + N, m, d)` avec repli `d = 28` si `ValueError` sur un 29/02 ; `OverflowError`/`ValueError` d'année ⇒ `None`. Les deux oracles doivent **concorder** sur tout le balayage ; l'année `0000` (hors `datetime`) n'est vérifiée que par l'oracle 1.
- **Balayage** : toutes les années 0000-9999 × {01-01, 02-28, 02-29 (si bissextile), 12-31} × 3 types (97 275 cas dont 41 non représentables, chiffres éprouvés : les deux oracles concordent sur tous les cas et l'expression du CHECK donne le même verdict ; exécution par `executemany` dans une transaction annulée) ; pour chaque cas, SQL (CHECK G5 sur INSERT avec la valeur de l'oracle) **accepte exactement quand l'oracle ≠ None** et que la valeur de l'oracle est insérée ; toute autre valeur de fin est refusée.
- **Seuils exacts** (cas nommés) : parfait achèvement `9998-xx` accepté / `9999-xx` refusé ; biennale `9997` accepté / `9998` refusé ; décennale `9989` accepté / `9990` refusé ; `9999-12-31` refusé pour les 3 types ; `9996-02-29` (bissextile) : fins `9997-02-28`, `9998-02-28` ; décennale refusée.
- **Refus par contrainte** : une fin à 5 chiffres (`10000-06-01`) est refusée avec un message **sans préfixe `INV-nn`** ; aucune ligne créée ; `sqlite_sequence` inchangé.
- **Piège `OR IGNORE`** (témoin, base chaîne 001→008) : solde daté `9990-06-01` (BC à 3 garanties : décennale, biennale, parfait achèvement) ; un `INSERT OR IGNORE … SELECT` brut renvoie `rowcount = 2` **sans erreur** (documente le piège) ; le **service émulé** doit, lui, lever `DateFinSuiviHorsFormat` **avant toute écriture** : aucune ligne dans `garanties`, aucun solde, **compteur FAC inchangé** (pré-contrôle avant réservation, §4.1 ; empreintes avant/après, numérotation comprise) ; mêmes essais à `9997`, `9998`, `9999`.
- **Post-condition** : couverte par le groupe O (O1, O7).
- **Cas qui doivent réussir** : BC sans garantie de ligne avec solde daté `9999-12-31` (rien à créer) ; BC à `parfait_achevement` seul avec solde `9998-12-31` ; solde nominal 2099 (fin ≤ 2109).
- **Voie nominale** : date d'émission V6 hors 2001-2099 refusée par le **service** (INV-177), jamais par le SQL (témoin : le SQL accepte la facture, `9990-xx` incluse) ; `yy = 00` (ex. `9900-01-01`) refusé par la séquence (`annee = 0` réservé CLI/FOU), distinct de §3.6.
- **Diagnostics** : CK-07a/b sur base alimentée en SQL direct (triggers supprimés) avec une fin incorrecte ou absente ⇒ détection.

**Groupe O — post-condition du service et atomicité de l'émission (§4.1).**
Méthode commune : pour chaque test, relevé **avant** et **après** de (a) l'empreinte complète de la base (toutes tables, hors `numerotation_sequences` et son `sqlite_sequence`), (b) `factures`, lignes de facture, `garanties` (valeurs champ par champ) et caches du BC (`statut`, `avancement`, `montant_deja_facture_ht`, `date_100_facture`, `completed_at`, `frozen_at`, `updated_at`), (c) `numerotation_sequences`. Les assertions portent sur les **données persistées** et sur l'erreur typée (type, codes Cn, valeurs attendue / constatée), jamais sur la seule levée d'une exception. Bases : **réelle** (008 complet) ; **témoin** (sans `tr_51` ni CHECK G5, pour laisser exister une valeur fausse) ; **SQL direct** (triggers retirés) pour installer une garantie préexistante incohérente.
- **O1 — garantie absente après `INSERT OR IGNORE`** *(demande 1)* : défaut injecté retirant une paire du lot ⇒ C1 (+ C7) ; variante réelle : une fin fausse refusée par le CHECK G5 puis **ignorée** par `OR IGNORE` ⇒ paire absente ⇒ C1 ; erreur levée, rollback intégral.
- **O2 — garantie existante rattachée à la mauvaise facture** *(demande 2)* : (a) PREMIER avec garanties préexistantes ⇒ C8 ; (b) REJEU dont les garanties historiques référencent un 2ᵉ solde (SQL direct, G1-G4 satisfaites car la date est celle de ce solde) ⇒ C4 (+ C5, C6) ; détecté au **pré-contrôle** (compteur inchangé) ; variante pré-contrôle neutralisé ⇒ détecté par la post-condition en transaction.
- **O3 — `date_declenchement` fausse** *(demande 3)* : base témoin, ±1 jour, date du nouveau solde au lieu de celle de R ⇒ C5 ; base réelle : l'insertion du service lève `INV-87` (G4) ⇒ rollback intégral aussi.
- **O4 — `date_fin_suivi` fausse** *(demande 4)* : base témoin, ±1 jour, ±1 an, type permuté, 29/02 conservé, `01/03` (`date(x,'+1 year')`) ⇒ C6 ; base réelle : CHECK G5 refuse, `OR IGNORE` ignore, C1 détecte.
- **O5 — mauvais BC ou mauvaise ligne** *(demande 5)* : `bc_id` d'un autre BC ; ligne d'un autre BC ; `bc_id` correct + ligne autre ; ligne correcte + `bc_id` autre ⇒ C3 (+ C1, C2) ; base réelle : G1 refuse.
- **O6 — rejeu légitime au 2ᵉ solde** *(demande 6)* : T-14 (avoir total puis nouveau solde, date différente) ⇒ mode REJEU, **0 ligne créée**, chaque garantie identique champ par champ (`id`, `bc_id`, ligne, type, dates, `facture_declenchement_id` = R, `created_at`) ; le nouveau solde, ses lignes, son numéro et les caches sont persistés (`date_100_facture` = date du 2ᵉ solde, distincte de `date_declenchement`) ; ni C5 ni C6 malgré la date différente ; 3ᵉ solde idem ; solde à 0.00 en rejeu ; BC sans garantie de ligne (`E` vide) : aucune garantie, aucune erreur, en PREMIER comme en REJEU.
- **O7 — restauration complète de l'état** *(demande 7)* : pour **chaque** scénario d'échec (O1 à O5, O8, O9, O10), empreinte avant = après ; nombre et ids de `factures`, lignes de facture, `garanties`, caches du BC, `reglements` et `sqlite_sequence` des tables objets inchangés ; aucune facture ne porte le numéro réservé.
- **O8 — numérotation** : (a) échec au pré-contrôle (fin > 9999 ; rejeu incohérent) : compteur FAC **inchangé** ; (b) échec après réservation : compteur +1 (trou), aucune facture ne porte ce numéro, le solde suivant (corrigé) obtient N+1 et **jamais N** (non-réutilisation) ; le compteur ne décroît jamais.
- **O9 — garantie historique incohérente en REJEU** : mauvaise facture, date, fin, BC, ligne, surplus, paire manquante ⇒ erreur, rien n'est corrigé ni supprimé (fail-closed, P-6) ; pré-contrôle puis post-condition (pré-contrôle neutralisé par le test).
- **O10 — surplus (C2)** : garantie hors `bc_ligne_garanties` (SQL direct sans G3) ; garantie portée par un BC importé.
- **O11 — 29 février** : premier solde au `2028-02-29` ⇒ fins `2029-02-28`, `2030-02-28`, `2038-02-28`, post-condition satisfaite ; une fin `2029-03-01` injectée ⇒ C6.
- **O12 — indépendance des valeurs attendues** : le service calcule R, D et `fin` par sa propre arithmétique entière ; le test les compare aux oracles 1 et 2 (groupe N) ; témoin documenté : des valeurs attendues tirées de la ligne persistée ou du nouveau solde donneraient un faux accord (ligne fausse validée) ou un faux rejet (rejeu).
- **O13 — ordre** : la post-condition s'exécute après les `INSERT` et le recalcul des caches ; défaut injecté sur l'écriture des caches, ou après les `INSERT` ⇒ rollback intégral.

**Volume visé** : 250 à 310 tests (dont 35 à 45 pour le groupe O) (1 table, 3 index, 3 triggers + CK ; le balayage du groupe N compte comme un petit nombre de tests à nombreux sous-tests). **Mutation** (phase suivante, après validation et livraison SQL + tests, comme en 007) : mutants du seul `008_garanties.sql` — listes `IN`, littéraux `1/2/10`, `'02-29'`, `substr`, `GLOB`, `>`/`>=`, `WHERE` des gardes, `CASE` — chaque survivant qualifié individuellement ; **non lancée ici**.

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
| Z-9 | Mod. §8 | Seul TR-50 existe ; les gardes d'insertion (G1-G4) n'ont pas de numéro | `TR-51` retenu (QO-1 validé) | Ajouter TR-51 au §8 |
| Z-10 | Mod. §3.4 (l.226) et CDC §24-25 | `a_surveiller` « avant échéance » / `echue` « après `date_fin_suivi` » : le **jour même** de `date_fin_suivi` n'est classé nulle part | Aucun effet SQL (état dérivé) | [PR service/UI] `echue` ⇔ jour courant **>** `date_fin_suivi` (lecture littérale de « après ») ; à fixer à l'écriture du service |
| Z-11 | CDC §24 « franchissement de 100 % facturé » vs DV-5 (`avancement` peut valoir 100.00 par situations sans solde) | Lecture ambiguë du déclencheur | Résolu par Mod. §3.2 (l.197 : « 100 % facturé = présence d'un solde »), INV-85, DV-5 | Aucune ; test dédié (groupe H) |
| Z-12 | INV-88, INV-10, INV-177, Mod. §4.10 (« aucune borne d'année » sur les dates hors numérotation) | Les sources ne disent pas ce qui se passe quand `date_declenchement + N ans` dépasse l'année 9999 (famille D à 4 chiffres) ; « aucune borne d'année » (INV-177) vise les bornes **métier**, pas la représentabilité | Traitement §3.6 : refus par contrainte + échec du solde, aucune borne métier | Ajouter à INV-88 : « si l'année de fin dépasse 9999, la création est refusée et le solde n'est pas émis » |
| Z-13 | Mod. §4.10 / INV-86 / conv. §9 (« `INSERT OR IGNORE` … idempotent ») | Non dit : `OR IGNORE` ignore aussi `CHECK` et `NOT NULL` (sondé) ; l'idempotence ne doit pas masquer un défaut de valeur | Post-condition obligatoire dans le service (§3.6, §4.1) | Ajouter une phrase à conv. §9 / Mod. §4.10 : « `INSERT OR IGNORE` ne dispense pas du contrôle du nombre de lignes créées » |
| Z-14 | PT-1 ; Mod. §11.4 ; INV-22, 25, 32, 179 ; E-13 ; E-14/INV-185 vs la formulation « aucun numéro de facture consommé en cas d'échec » | Le numéro est réservé et committé dans une transaction propre **avant** la transaction de l'objet ; un trou après échec est accepté, jamais récupéré ni réutilisé ; le compteur ne décroît jamais. « Aucun numéro consommé » n'est donc vrai que pour les échecs détectés **avant** la réservation | §4.1 : pré-contrôles avant réservation ; après réservation, trou admis et jamais réutilisé ; numérotation inchangée (001–007 intouchables) | Aucune ; reformuler « aucun numéro n'est attribué à un objet persisté ; un trou est admis » (P-5) |

Aucune de ces lacunes ne contredit le **DDL** ni le **comportement** décidés de `garanties`.

---

## 7. Points bloquants et arbitrages

**Points bloquants : aucun.**

**Arbitrages — tous tranchés (§1.6)** : QO-1 **OUI** (G3 + G4) · QO-2 **OUI** (CHECK de durée, 29/02 → 28/02) · QO-3 **NON** (pas de garde « premier solde » en SQL).
**À valider avec ce cadrage révisé** : le traitement des dates extrêmes (§3.6) — refus par contrainte, calcul préalable, **rollback intégral du solde**, aucune borne métier nouvelle — et la **post-condition renforcée du service (§4.1, C1 à C8, groupe O)**, avec les trois points ci-dessous (P-5 à P-7, valeur par défaut retenue, non bloquants).

**Points d'information (service/UI, non bloquants, à ne pas rouvrir ici)** :
- **P-1** Jour d'échéance : voir Z-10.
- **P-2** Événement `declenchement_garantie` : un par BC ou par garantie ? À fixer avec la tranche `historique`.
- **P-3** Limite assumée : 004/005b autorisent en SQL un `INSERT` tardif dans `bc_ligne_garanties` d'un BC non annulé (même après solde, hors TR-99 qui ne garde que le lien devis) ; 008 ne le corrige pas (001–007 intouchables) — CK-07a le détecte. Idem pour `bc_ligne_garanties` sur un BC importé (INV-134).
- **P-4** Option non retenue par défaut : dupliquer la vérification de durée exacte en `RAISE(ABORT)` dans `tr_51` (un `ABORT` n'est pas masqué par `OR IGNORE`, contrairement au CHECK). Elle ferait échouer le SQL lui-même, sans dépendre du service ; coût : une règle écrite deux fois (mutants équivalents à qualifier). Le cadrage retient le CHECK validé (QO-2) + garde du service ; à ne rouvrir que si vous souhaitez ce double rempart.

**Points soulevés par la post-condition (non bloquants ; défaut retenu, à confirmer ou infirmer)** :
- **P-5** *Numérotation.* La règle « aucun numéro consommé si l'émission échoue » est appliquée **au sens des règles existantes** (PT-1, Z-14) : aucun numéro réservé pour tout échec **prévisible** (pré-contrôles, avant réservation) ; après réservation, la facture et son numéro disparaissent avec le rollback mais le compteur garde un **trou**, jamais réutilisé. Une lecture littérale (compteur intact même après réservation) exigerait de modifier la numérotation 001–007 : **non proposé**.
- **P-6** *Fail-closed au rejeu.* Une garantie historique incohérente ou manquante (cas possible seulement par SQL direct, import, restauration, ou P-3) **bloque l'émission d'un nouveau solde** du BC tant qu'elle n'est pas traitée : le service ne la corrige pas (INV-134, jamais recalculée), ne la supprime pas (INV-87) et ne la tolère pas. Alternative non retenue : diagnostic CK-07 seul en REJEU, au prix de soldes émis sur des garanties fausses.
- **P-7** *Premier solde.* « Premier solde » = solde de **plus petit `id`** du BC, neutralisé ou non (cohérent avec CK-07c, Z-4, T-14) ; convention technique, sans date ni statut, ne modifiant aucune règle.

---

## Conclusion

**Cadrage révisé prêt à valider.** Aucun point bloquant. Les trois arbitrages (QO-1 oui, QO-2 oui, QO-3 non) sont intégrés comme décisions validées. Dates extrêmes : **refus par contrainte, échec de toute la transaction du solde, aucune borne métier nouvelle** (§3.6) — avec une exigence de service explicite, car `INSERT OR IGNORE` masque les violations de CHECK. **Post-condition du service renforcée (§4.1)** : complétude, facture = premier solde, dates exactes, rattachement ; erreur et rollback intégral ; rejeu idempotent préservé ; aucune garde SQL ajoutée. Après validation : implémentation `008_garanties.sql` → `test_008_garanties.py` → mutation → contrôles finaux → rapport (même ordre qu'en 007).

## Livraison
Ce seul fichier : `fichiers-a-relire/CADRAGE__008_garanties.md` (version révisée du 2026-10-09, post-condition renforcée). Aucun `008_garanties.sql`, aucun test ni document officiel modifié, aucune migration modifiée, aucune mutation lancée, V3.13 non déplacée. Aucun push effectué (vous poussez vous-même).
