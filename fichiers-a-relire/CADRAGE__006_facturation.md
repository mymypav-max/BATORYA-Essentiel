# CADRAGE — Tranche 006 « Facturation » (BATORYA Essentiel V6)

| | |
|---|---|
| **Statut** | Cadrage et audit **uniquement**. Aucun SQL, aucun test, aucune source officielle modifiée. **Mis à jour le 2026-10-05** : décisions V6-01 et V6-03 verrouillées (partie M). **Mis à jour le 2026-10-06** : la corrective 005c est livrée (migration et test présents dans `main`) ; 006 reste au rang 9, non créée. |
| **Livrable** | `fichiers-a-relire/CADRAGE__006_facturation.md` (seul fichier créé) |
| **Date** | 2026-10-05 |
| **Rang prévu** | **9** dans la chaîne : une corrective **`005c`** (rang 8, décision verrouillée VR-06) précède 006 ; D-55 et le modèle §17.1 réservaient le rang 8 à 006 (alignés le 2026-10-05 : D-56, modèle §17.1, conventions §5) |
| **Test prévu** | `test_006_facturation.py` — numérotation de tests **T-48** (T-44 = 005, T-45 = 005a, T-46 = 005b, T-47 = 005c, livrée) |
| **Hiérarchie appliquée** | 1 décisions validées · 2 invariants · 3 modèle SQLite validé · 4 modèle métier · 5 errata / décisions correctives · 6 CDC · 7 migrations existantes (référence technique réelle) |

---

## M. Mise à jour du 2026-10-05 — décisions verrouillées (V6-01, V6-03)

> **Portée.** Cette partie intègre les décisions que Rémy a **verrouillées le 2026-10-05** sur V6-01 (`frozen_at`) et V6-03 (BC annulé, avoirs, BC `termine`, caches). Elle prime sur toute formulation antérieure du document ; les §0 à §19 et les annexes ont été alignés sur elle. Les identifiants `VR-nn` (décision verrouillée), `CD-nn` (contradiction documentaire) et `QO-n` (question ouverte) sont **propres à ce cadrage** : ce ne sont **pas** des entrées du registre officiel (D-xx, E-xx, INV-xx). Le report de ces décisions dans les sources (modèle, invariants, conventions) est une étape ultérieure (§M.8), **non effectuée ici**.
>
> **Hiérarchie des sources appliquée** (consigne du 2026-10-05) : 1 décisions validées · 2 invariants · 3 modèle SQLite validé · 4 modèle métier · 5 errata / décisions correctives · 6 CDC · 7 migrations existantes (référence technique **réelle** : elles disent ce qui est implémenté, pas ce qui est décidé).
>
> **Étiquettes** : **[RD]** règle documentée · **[DT]** déduction technique · **[PR]** proposition · **[VR]** décision verrouillée (Rémy, 2026-10-05) · **[QO]** question ouverte. L'ancienne étiquette **[DV]** (« décision à valider ») subsiste dans le texte pour les points non encore tranchés ; elle équivaut à **[QO]**.

### M.0 Correspondance avec les 19 contenus attendus

| # | Contenu attendu | Où |
|---|---|---|
| 1 | Cadrage métier | §1, §M.1 |
| 2 | Modèle de données | §2 |
| 3 | Relations | §3 |
| 4 | Cycle de vie | §4, §M.3 à §M.5 |
| 5 | Règles de facturation | §6, §9, §M.6 |
| 6 | Règles acompte / situation / solde | §4.2, §6.2 à §6.5, §9.2, §M.7 |
| 7 | Règles avoir / correction | §4.1, §M.5, §M.7, A6-10 |
| 8 | Comportement du BC `annule` | §M.4, §9.3 |
| 9 | Comportement du BC `termine` après avoir | §M.5, §9.3 |
| 10 | Définition des caches | §M.6, §6.6, §7 |
| 11 | Distinction état financier / réouverture commerciale | §M.3 |
| 12 | Répartition SQL / triggers / services / CK-13 | §11, §9.4, §M.8 |
| 13 | Impact de 005c | §M.8, §14, §16 |
| 14 | Stratégie de tests | §17, §18, §M.9 |
| 15 | Contradictions documentaires | §M.10, §15 |
| 16 | Décisions verrouillées | §M.1 |
| 17 | Questions restant réellement à valider | §M.11, §19 |
| 18 | Structure proposée de `006_facturation.sql` | §16 |
| 19 | Structure proposée de `test_006_facturation.py` | §17 |

### M.1 Décisions verrouillées

| ID | Décision verrouillée **[VR]** | Remplace |
|---|---|---|
| **VR-01** | Le **gel progressif est abandonné**. E-10 remplace E-01 ; INV-33, INV-34, INV-35 (retirés le 2026-10-03) ne sont pas rétablis. **Aucun gel** au premier acompte ni au premier encaissement. `frozen_at` n'est **jamais** un verrou métier. | V6-01 (options a, b1, b2) |
| **VR-02** | `bons_commande.frozen_at` (et `devis.frozen_at`) est **conservée**, pour compatibilité et pour éviter une reconstruction de table inutile. Statut **résiduel technique** : ce n'est ni une règle métier ni un état métier ; elle ne crée **aucun** blocage nouveau ; **aucune règle n'est déduite de son existence** ; **aucun événement n'est inventé** pour lui donner un sens. | V6-01 |
| **VR-03** | Les **obligations techniques** qui découlent des CHECK et triggers du SQL actuel sont documentées (§M.2) **sans être promues en règles métier**. | V6-01 |
| **VR-04** | BC `annule` = **état terminal commercial**. **Interdits** : nouveau devis accepté rattaché, nouvel acompte, nouvelle situation, nouveau solde, tout document commercial poursuivant l'exécution. **Autorisés** : règlements sur documents existants, corrections financières, avoirs sur documents existants, régularisation comptable ou historique. Un BC annulé **n'est pas figé financièrement**. | V6-03 (i) |
| **VR-05** | Les caches `montant_deja_facture_ht`, `avancement`, `date_100_facture` **peuvent continuer d'évoluer** après annulation lorsqu'une opération financière légitime sur un document existant modifie la situation économique. `statut` reste `annule`. L'évolution d'un cache **n'est pas** une réouverture commerciale. | V6-03 (i), option A |
| **VR-06** | **Corrective 005c** — « correction BC annulé / caches financiers » : remplacement ciblé de `tr_12_bons_commande_annule` (protections commerciales conservées, mises à jour financières nécessaires autorisées), **sans reconstruction de table**, sans modification d'une autre règle de 005b. Elle **précède** 006 (§M.8). Ni 005c ni son test ne sont écrits ici. | V6-03 (i) |
| **VR-07** | Un BC `termine` **peut recevoir un avoir** sur un document existant ; ce n'est **pas** une réouverture commerciale. **Avoir partiel** : ne ramène pas automatiquement le BC à `en_cours` (il reste `termine` si les conditions de `termine` restent vraies). **Avoir total absorbant le solde actif** : le solde n'est plus actif ; `date_100_facture` peut devenir NULL s'il n'existe pas d'autre solde actif ; l'état dérivé peut passer `termine → en_cours` — **état financier dérivé**, pas réouverture commerciale : aucun rattachement de devis, aucune reprise libre de l'exécution commerciale. | V6-03 (ii), (iii) ; A6-03, A6-12 |
| **VR-08** | **État financier dérivé ≠ réouverture commerciale** (§M.3). | V6-03 |
| **VR-09** | Dès qu'un **solde a été émis/validé**, le BC est **fermé à tout nouveau devis**, **même si ce solde est ensuite totalement crédité**. Un avoir ne contourne jamais cette fermeture. | INV-187 précisé par la décision |
| **VR-10** | `bons_commande.date_100_facture` = **cache financier** : date d'émission du **premier solde actif** (qui atteint 100 %). Un avoir partiel ne l'efface pas. Elle redevient NULL si le solde actif est totalement crédité et qu'aucun autre solde actif n'existe. Un nouveau solde actif donne une nouvelle valeur. | V6-11 ; A6-06 |
| **VR-11** | `bons_commande.completed_at` = **cache technique de `termine`** : renseigné si `statut = 'termine'`, NULL sinon (NULL à nouveau au retour à `en_cours`). L'historique réel relève de la **traçabilité V6** (événements), pas de `completed_at`. Aucun rôle d'historique métier sans source. | V6-03 |
| **VR-12** | « **Solde actif** » = solde **non totalement absorbé** par les avoirs/corrections qui lui sont rattachés selon les règles V6. Totalement crédité ⇒ plus actif ; il ne contribue plus aux caches comme solde économique restant dû. **Aucun mécanisme de statut supplémentaire** si les données suffisent. | V6-02 (définition) ; A6-04 |
| **VR-13** | La **règle des 30 jours des dépenses** (INV-103) est une règle de **service Dépenses** qui lit `bons_commande.date_100_facture` à l'instant du rattachement (INV-199). **006 ne l'implémente pas, ne la réinitialise pas, ne la prolonge pas.** | consigne de Rémy ; **[RD]** INV-103, INV-199, métier l.500 (§17) |

> **Réserve sur VR-13.** La consigne du 2026-10-05 mentionne une colonne `fournisseurs.date_100_facture`. Elle **n'existe pas** (002 : `fournisseurs` = code, nom, adresse, cpville, tel, email, notes, statut, created_at, updated_at ; cadrage 005 R28 : « Date de facture fournisseur : aucune colonne (à ne pas confondre avec `date_100_facture`, colonne du BC) »). Les sources fondent le délai de 30 jours sur **la colonne du BC**. C'est ce qui est écrit ici (CD-01, §M.10).

### M.2 `frozen_at` : statut résiduel et obligations techniques (VR-01 à VR-03)

**[RD]** E-10 supprime le gel progressif ; INV-33/34/35 sont retirés ; le modèle §7.1 classe la règle comme « règle métier validée » et PT-8 comme « choix non fait » ; `statut` du BC = `en_cours`, `termine`, `annule` (pas de `gele`). **[VR]** La colonne est conservée telle quelle (VR-02) : **aucune migration ne la supprime**.

**Objets du rang 7 qui la mentionnent (DDL réel rejoué)** — constat **[DT]**, pas règle métier :

| Objet | Ce qu'il impose | Effet pour 006 |
|---|---|---|
| `bons_commande.frozen_at` (TS nullable) + CHECK de format | forme canonique | aucun |
| CHECK `statut <> 'termine' OR frozen_at IS NOT NULL` | `termine` exige `frozen_at` posé | obligation O-1 |
| CHECK `date_100_facture IS NULL OR frozen_at IS NOT NULL` | `date_100_facture` exige `frozen_at` posé | obligation O-1 |
| CHECK `statut <> 'termine' OR date_100_facture IS NOT NULL` (005b l.219) | `termine` exige `date_100_facture` posée ; ne mentionne pas `frozen_at`, mais forme avec les deux CHECK précédents la chaîne `termine` ⇒ `date_100_facture` ⇒ `frozen_at` (et `date_100_facture` ⇒ `avancement = '100.00'`) | complète O-1 : `termine` ne se pose que dans un `UPDATE` qui pose aussi `date_100_facture` (`avancement = '100.00'`) et `frozen_at` |
| `tr_14_bons_commande_frozen_at` | passage NULL → valeur irréversible (le message cite encore INV-34, retiré) | obligation O-3 |
| `tr_17_bons_commande_insert` | `frozen_at` NULL à la naissance | aucun |
| `tr_12_bons_commande_annule` | `frozen_at` figé sur un BC annulé | **conservé** par 005c |
| `devis.frozen_at` + CHECK `frozen_at IS NULL OR statut IN ('accepte','annule')` + `tr_14_devis_frozen_at` | marqueur technique du devis | 006 n'y touche pas |
| `tr_12_bons_commande_contrat` | s'applique à tout BC non annulé, **que `frozen_at` soit posé ou non** (005b Q-B) | `frozen_at` ne ferme aucune édition |

**Obligations techniques [DT]** (VR-03). Sondage en mémoire (lecture seule) sur la chaîne 001 → 005b :

| # | Obligation | Preuve |
|---|---|---|
| **O-1** | Tant que les deux CHECK existent, le service financier qui pose **pour la première fois** `date_100_facture` (non NULL) ou `statut = 'termine'` sur un BC dont `frozen_at` est NULL doit poser `frozen_at` **dans le même `UPDATE`**. | `date_100_facture` + `avancement = '100.00'` sans `frozen_at` → refusé ; avec `frozen_at` dans le même `UPDATE` → accepté ; `termine` sans `frozen_at` → refusé |
| **O-2** | La valeur posée est un horodatage canonique **sans signification métier** : ni « date de gel », ni « premier encaissement », ni « première facture ». Aucun événement n'est créé pour elle ; aucune règle ne la lit. | VR-02 |
| **O-3** | `frozen_at` est irréversible : après `termine → en_cours` ou après avoir total (`date_100_facture` redevenue NULL), il **reste posé**. `frozen_at NOT NULL` ne dit donc **rien** de l'état courant du BC. | sondage : `termine → en_cours` avec `frozen_at` conservé accepté ; remise à NULL refusée |
| **O-4** | Les caches `montant_deja_facture_ht` et `avancement` (sans `date_100_facture`, sans `termine`) s'écrivent **sans** `frozen_at`. Un BC jamais `termine` et sans `date_100_facture` garde `frozen_at` NULL même s'il porte des factures. | sondage : `avancement = '50.00'`, `montant_deja_facture_ht = '5.00'` accepté ; `avancement = '100.00'` sans `date_100_facture` accepté |
| **O-5** | Personne n'écrit `frozen_at` aujourd'hui (TR-15 n'a jamais été créé). Le **contrat du service financier** (hors SQL) devra donc porter O-1. | 0 occurrence de TR-15 / `UPDATE … frozen_at` dans les migrations |

**Ce que 006 n'en déduit pas** : aucun comportement conditionné à `frozen_at` (rattachement de devis, édition, avoir, annulation) ; aucun nouveau CHECK ni trigger sur `frozen_at` ; aucune colonne `frozen_at` dans `factures`.

**Coût d'une suppression, pour mémoire** (non retenue) : `ALTER TABLE … DROP COLUMN` est refusé (dépendances CHECK/triggers) ; il faudrait reconstruire `bons_commande` et `devis` et recréer ≈ 30 triggers (10 autour du BC, 23 autour du devis, 3 communs) sous protocole `foreign_keys=OFF` — aucune règle validée ne l'exige.

### M.3 État financier dérivé ≠ réouverture commerciale (VR-08, VR-09)

Deux axes **indépendants**, que le vocabulaire « rouvrir » confondait (A6-03) :

| | Axe 1 — **état financier dérivé** | Axe 2 — **clôture commerciale** |
|---|---|---|
| Objet | `statut ∈ {en_cours, termine}`, `completed_at`, `montant_deja_facture_ht`, `avancement`, `date_100_facture` | possibilité de rattacher un devis, d'émettre un document commercial qui poursuit l'exécution |
| Nature | **recalculé** par le service financier unique, même transaction, un seul `UPDATE` (INV-46, INV-164) | **porté par aucune colonne** (ni `statut`, ni `date_100_facture`, ni `completed_at`, ni `frozen_at`) |
| Détermination | formules INV-42 / INV-43 / INV-56 / §3.7 du modèle | BC `annule` (terminal) **ou** un solde a existé, même totalement crédité (VR-09) |
| Peut revenir en arrière ? | **oui**, par recalcul (annulation d'un règlement, avoir total absorbant le solde) | **non** : un avoir ne rouvre jamais ; seule voie : un nouveau BC (E-16) |
| Garde | service + CK-06 + CHECK de 004 | service + CK-14 ; trigger `bc_devis` optionnel (V6-10) |

**Règles [VR]/[RD]** :

1. Un avoir, partiel ou total, **n'est jamais** un acte de réouverture commerciale (INV-187, INV-58, VR-07, VR-09).
2. Un avoir total qui neutralise le solde actif peut faire passer le BC de `termine` à `en_cours` **par pur recalcul** (INV-42 : `termine ⇔ solde actif ∧ Σ reste_du hors avoir = 0`). C'est un déplacement de l'axe 1 uniquement.
3. `en_cours` est **nécessaire mais non suffisant** pour émettre : un BC redevenu `en_cours` après avoir total sur son solde n'accepte qu'un **nouveau solde** et des avoirs (§M.7) ; jamais de devis (VR-09), jamais d'acompte ni de situation (INV-58).
4. Aucun libellé de 006 ne doit écrire qu'un avoir « rouvre » le BC : il peut **modifier l'état dérivé** ou **ne rien modifier**.

### M.4 Comportement du BC `annule` (VR-04, VR-05, VR-06)

| Opération sur un BC `annule` | Résultat | Qualif. / source | Couche |
|---|---|---|---|
| Nouvel **acompte**, nouvelle **situation**, nouveau **solde** | **refusé** | **[RD]** INV-188, E-15, INV-47 ; métier §7 l.273 | trigger TR-16 de 006 |
| **Rattachement d'un devis** (`bc_devis`) | **refusé** | **[RD]** INV-188 ; 005b `tr_99_bc_devis_insert` (déjà en place) | 005b |
| Tout autre document commercial poursuivant l'exécution | **refusé** | **[VR]** VR-04 ; aucun autre type n'existe (§1.2) | — |
| **Avoir** sur une facture existante | **autorisé** | **[RD]** INV-188, INV-173, C-36 | 006 |
| **Règlement** sur un document existant | **autorisé** | **[RD]** INV-188, E-15 ; métier §7 l.273 | 007 (non créé en 006) |
| Correction financière / régularisation comptable ou historique | **autorisée** | **[VR]** VR-04. Aucun mécanisme n'est documenté au-delà de l'avoir et du règlement : 006 n'en invente aucun | — |
| Recalcul des **caches** `montant_deja_facture_ht`, `avancement`, `date_100_facture` après une opération légitime | **autorisé** (un seul `UPDATE`, CHECK de 004 respectés) | **[VR]** VR-05 ; **[RD]** INV-46, INV-164, INV-173 ; modèle §7.2 | **005c** |
| `statut` | reste `annule` | **[RD]** INV-173 (terminal) | `tr_12` remplacé (protégé) |
| `completed_at`, `cancelled_at`, `motif_annulation`, `frozen_at` | inchangés | **[RD]** INV-173 ; **[DT]** `completed_at` est NULL (CHECK `(statut='termine') = (completed_at IS NOT NULL)`) | `tr_12` remplacé (protégé) |
| Contrat : `id`, `client_id`, snapshots + versions, `date_acceptation`, `date_debut`, `date_fin`, `montant_contractuel_ht`, `created_at`, `origine`, `legacy_*` | inchangés | **[RD]** INV-173, INV-186 | `tr_12` remplacé (protégé) |
| `updated_at` | libre | **[RD]** INV-173 (« seul `updated_at` … ») | inchangé |

**Précisions [DT]** :

- **Annulation d'un BC facturé.** L'annulation est un **acte** (INV-44), pas un recalcul : elle modifie `statut`, `cancelled_at`, `motif_annulation` (et force `completed_at = NULL` si le BC était `termine`) et **laisse les caches tels quels**, puisque leurs formules ne dépendent pas du `statut`. Sondage : un BC portant un acompte (`5.00` / `15.87`) ou un solde (`date_100_facture` posée, `avancement = 100.00`) conserve ses caches à l'annulation.
- **`statut` et `completed_at` d'un BC annulé ne sont jamais recalculés** ; **CK-06** pour un BC annulé compare donc **seulement** `montant_deja_facture_ht`, `avancement`, `date_100_facture` au recalcul.
- **Écriture conjointe.** Le CHECK de 004 `date_100_facture IS NULL OR avancement = '100.00'` impose que `avancement` et `date_100_facture` bougent **ensemble** dans le même `UPDATE` (un solde totalement crédité : `date_100_facture = NULL` **et** `avancement < 100.00` simultanément). Sondage : abaisser `avancement` en gardant `date_100_facture` → refusé.
- **Limite assumée.** Une fois `tr_12` remplacé, rien n'empêche en SQL un `UPDATE` de cache **sans** avoir derrière (comme sur un BC non annulé, où `tr_12_bons_commande_contrat` laisse déjà les caches libres). La légitimité de la valeur est garantie par le **service** et diagnostiquée par **CK-06** ; elle ne peut pas être un trigger de « miroir » (conv. §9).
- **Un BC annulé ne participe plus au CA engagé** (métier §7 l.273) : sans lien avec les caches de facturation ; 006 ne crée ni ne modifie rien à ce sujet.

### M.5 Comportement du BC `termine` après avoir (VR-07)

**Principe [VR]** : l'avoir est autorisé sur un BC `termine` (TR-16 n'est pas créé comme refus) ; il ne rouvre rien commercialement (§M.3).

**Scénario de référence** (hypothèses : contractuel 1000.00 ; acompte 200.00 ; situation 300.00 ; solde 500.00 ; tout encaissé ; BC `termine`, `date_100_facture` = date du solde). Les encaissements relèvent de 007 : **en 006, les états `termine` des tests sont posés par un helper**, comme le fait 005b (`terminer_bc`).

| Cas | Facturation nette | `statut` | `completed_at` | `avancement` | `date_100_facture` | Suite |
|---|---|---|---|---|---|---|
| **A** avoir **partiel** 50.00 sur l'acompte ou la situation | 950.00 | `termine` (conservé) | conservé | 100.00 (solde actif) | conservée | l'avoir sur facture entièrement payée crée un **crédit** (`absorbe = min(avoirs, max(0, M − encaissé)) = 0`, modèle §3.3) ; il ne « réduit » pas un reste dû nul |
| **B** avoir **total** 200.00 sur l'acompte | 800.00 | `termine` (conservé) | conservé | 100.00 | conservée | remplacement de l'acompte : **QO-1** |
| **C** avoir **partiel** 100.00 sur le solde | 900.00 | `termine` (conservé) | conservé | 100.00 (solde actif) | conservée (INV-43) | aucun nouveau solde (INV-52) |
| **D** avoir **total** 500.00 sur le solde | 500.00 | **`en_cours`** (INV-42 : plus de solde actif) | **NULL** | **50.00** (500/1000, plus de solde actif) | **NULL** (aucun autre solde actif) | BC fermé aux devis (VR-09) ; un **nouveau solde** est permis, pas d'acompte ni de situation |

- **[DT]** Cas D : les cinq caches s'écrivent **dans un seul `UPDATE`** (`montant_deja_facture_ht`, `avancement`, `date_100_facture = NULL`, `statut = 'en_cours'`, `completed_at = NULL`) ; `frozen_at` reste posé (O-3). Sondé : accepté par les CHECK de 004.
- **[RD]** `termine → en_cours` : `completed_at` repasse à NULL et l'événement d'historique `retour_en_cours` est la trace réelle (modèle §3.5 ; la table `historique` n'existe pas encore : 006 n'écrit aucun événement, A6-22).
- **[RD]** Garanties : un avoir ne modifie pas les garanties déjà déclenchées (métier l.645 ; `garanties.date_declenchement` peut diverger de `date_100_facture`, modèle §3.5). 008 n'est pas concerné par cette mise à jour.
- **[DT]** Si un nouveau solde est ensuite émis, `date_100_facture` prend la date d'émission du **nouveau** solde ; `garanties.date_declenchement` garde la première date.
- **Précision de formulation.** Il ne faut pas écrire qu'un avoir partiel « réduit le montant économique restant dû » d'une facture déjà payée : il réduit la **facturation nette** et peut créer un **crédit** ; seul un avoir sur une facture non entièrement payée réduit `reste_du` (via `absorbe`).

### M.6 Définition des caches du BC (VR-05, VR-10, VR-11)

| Colonne | Définition | Évolution | BC `annule` | Contrainte SQL existante | Qualif. / source |
|---|---|---|---|---|---|
| `montant_deja_facture_ht` | **facturation nette** du BC = Σ acomptes + Σ situations + Σ soldes − Σ avoirs (D2) | recalculée après **toute** opération y compris un avoir | évolue (VR-05) | famille D2 | **[RD]** INV-46, INV-56 ; modèle §3.2 |
| `avancement` | P2 = nette / contractuel ; **100.00 dès qu'un solde actif existe** ; mesure la facturation, jamais l'avancement physique | idem | évolue (VR-05) | P2 ; `date_100_facture` ⇒ `'100.00'` | **[RD]** modèle §4.7, INV-46 |
| `date_100_facture` | `date_emission` du **premier solde actif** ; conservée par avoir partiel, règlement, remboursement ; NULL si le solde actif est totalement crédité et qu'aucun autre n'est actif ; nouvelle valeur au nouveau solde actif | recalculée | évolue (VR-05) | `⇒ avancement = '100.00'` ; `⇒ frozen_at` (O-1) | **[RD]** INV-43 ; **[VR]** VR-10 |
| `statut` | `en_cours` / `termine` : **dérivé** (INV-42) ; `annule` : **acte**, jamais recalculé | recalculé tant que non annulé | **reste `annule`** | CHECK 3 valeurs ; `termine ⇒ frozen_at` | **[RD]** INV-42, INV-44, INV-173 |
| `completed_at` | cache technique de `termine` : TS si `termine`, NULL sinon | suit `statut` | NULL | `(statut='termine') = (completed_at IS NOT NULL)` | **[VR]** VR-11 ; **[RD]** modèle §3.5, INV-79 |
| `frozen_at` | **n'est pas un cache** : marqueur technique résiduel | posé par le service si O-1 l'exige ; irréversible | inchangé | voir §M.2 | **[VR]** VR-02 |

**`date_100_facture` — points de cohérence** :

- **Ce n'est pas `garanties.date_declenchement`** (première date, immuable, 008) ; les deux peuvent diverger volontairement (modèle §3.5).
- **Elle n'intervient pas dans le rattachement d'un devis** (INV-43, INV-187) : la fermeture commerciale (VR-09) ne dépend pas d'elle, donc ne disparaît pas quand elle redevient NULL.
- **Premier solde actif** : si le premier solde est totalement crédité et qu'un second solde est actif, la valeur est la date du **second**.
- **Lecture par Dépenses** (VR-13) : la règle des 30 jours évalue `bons_commande.date_100_facture` **à l'instant du rattachement** (INV-199) ; un BC annulé en est exempté (INV-103). Ce que le service Dépenses fait d'une valeur NULL ou changée n'est pas défini par 006 et **n'est pas décidé ici**. L'énoncé antérieur « la fenêtre de 30 jours repart de la nouvelle date » (A6-06 ancienne version, arbitrage du 2026-10-05) était **imprécis** et est retiré.

### M.7 Réémission après avoir total, et fermeture après solde

| Situation | Règle | Qualif. / source |
|---|---|---|
| Acompte totalement crédité, **aucun solde émis** | nouvel acompte du même devis, nouveau numéro | **[RD]** INV-185, E-14, C-33 |
| Situation totalement créditée, **aucun solde émis** | nouvelle situation, nouveau numéro de facture ; réutilisation du `situation_numero` : V6-06 | **[RD]** INV-185, C-33 ; **[QO]** V6-06 |
| Solde totalement crédité | **nouveau solde** uniquement (nouveau numéro) | **[RD]** E-14, C-33, métier §13 ; **[VR]** VR-12 |
| Solde actif existant | aucun second solde ; aucun acompte ni situation | **[RD]** INV-52, INV-58 |
| Solde émis puis totalement crédité : acompte ou situation | **refusés** (INV-58 : plus d'acompte ni de situation après solde) | **[RD]** INV-58 ; lecture « même neutralisé » : **[DT]** hiérarchie CD-07 |
| Acompte / situation totalement crédité(e) **alors qu'un solde existe** (actif ou crédité) : remplacement par une facture du même type ? | **non couvert explicitement** : INV-58 l'interdit, INV-185 l'autorise en termes généraux | **[QO]** QO-1 (CD-08) ; lecture prudente **[PR]** : non, le montant se refacture par remplacement du solde |
| Rattachement de devis après solde, **même totalement crédité** | **refusé** | **[VR]** VR-09 ; **[RD]** INV-187, E-16, C-35 |
| Avoir partiel | ne rouvre rien : ni devis, ni nouveau solde, ni acompte/situation | **[RD]** INV-58, INV-187 |

> Aucune règle n'est inventée ici pour combler QO-1 ; ce qui n'est pas explicitement couvert reste une question ouverte.

### M.8 Impact 005c — « 005c — correction BC annulé / caches financiers » (VR-06)

**Nature [VR]/[DT].** Corrective préalable à 006, selon les conventions (deux catégories : tranche `NNN_<objet>.sql` ; corrective `NNNx_<objet>.sql` rattachée à la dernière tranche exécutée avant elle). Elle est **cohérente avec le précédent 005b**, qui a lui-même remplacé `tr_12`, `tr_13`, `tr_17`, `tr_18` par `DROP TRIGGER` + `CREATE TRIGGER`.

| Point | Contenu |
|---|---|
| Nom | **Définitif (décision du 2026-10-05)** : migration `005c_bc_annule_caches_financiers.sql` ; test `test_005c_bc_annule_caches_financiers.py`. Aucun autre nom. Les deux fichiers sont **livrés dans `main`**. |
| Rang | **8** (`PRAGMA user_version`) ; **006 passe au rang 9**, 007 → 10, 008 → 11, 009 → 12, 010 → 13 (noms 006 → 010 = réservations d'ordre, conv. §5) |
| Objet remplacé | un seul : `tr_12_bons_commande_annule` (`BEFORE UPDATE ON bons_commande`, `WHEN OLD.statut = 'annule'`) |
| Nouvelle liste de colonnes gardées | l'ancienne liste **moins** `montant_deja_facture_ht`, `avancement`, `date_100_facture`. Restent protégées : `id`, `client_id`, snapshots et versions, `date_acceptation`, `date_debut`, `date_fin`, `montant_contractuel_ht`, `statut`, `completed_at`, `cancelled_at`, `motif_annulation`, `frozen_at`, `created_at`, `origine`, `legacy_*`. `updated_at` reste libre |
| Message | **Décidé (2026-10-05)** : `INV-173: bon de commande annule terminal, seules les evolutions autorisees sont modifiables` — message générique, sans énumérer les caches ; préfixe `INV-173` conservé, aucun nouveau code d'erreur (l'ancien texte « seul `updated_at` est modifiable » n'est plus exact) |
| Reconstruction de table | **aucune** : pas de protocole `foreign_keys=OFF` |
| Inchangé | tables, CHECK de 004/005b (dont les deux CHECK `frozen_at`), `tr_12_bons_commande_contrat`, `tr_13_*`, `tr_14_*`, `tr_17`, `tr_18`, `tr_19`, `tr_99_*`, CK-13/14 |
| Contrainte vérifiée | `avancement` et `date_100_facture` doivent changer ensemble (CHECK de 004) ; sondé par essai à blanc : avoir total sur solde (`date_100_facture = NULL` + `avancement = 50.00`) accepté ; abaisser `avancement` seul refusé |
| Limite | le trigger remplacé ne peut pas juger de la légitimité financière de la nouvelle valeur (§M.4) |

**Pourquoi avant 006.** Les tests de 006 doivent prouver que le recalcul des caches après un avoir sur un BC annulé est possible (G22). Le SQL de `factures` lui-même n'écrit aucun cache (le service le fait) : la dépendance est celle de la **chaîne de tests et du service**, pas du DDL de `factures`.

**Tests de 005c — écrits et livrés (`test_005c_bc_annule_caches_financiers.py`).** Numérotation par analogie 005a/005b : **T-47 = 005c**, donc **T-48 = 006** **[DT]**. Périmètre couvert :
- chaîne tronquée : rang 8 ; migration 005c sur une base de rang 7 ;
- matrice `annule` et `annule_gele` : chacun des trois caches **autorisé** individuellement et ensemble ; chacune des autres colonnes de la liste **refusée** ; `updated_at` seul accepté ; `statut → en_cours` refusé ; CHECK de 004 toujours effectifs (`date_100_facture` sans `avancement = '100.00'` refusé ; `termine ⇒ frozen_at`) ;
- non-régression : mêmes objets qu'au rang 7 sauf le trigger remplacé (DDL comparé octet pour octet) ; tests 001–005b inchangés (ils rejouent des chaînes tronquées à leur rang : `test_005a:604` `[:6]`, `test_005b:755` `[:7]`) ;
- campagne de mutation **ciblée** sur le trigger remplacé (conv. §7.1) : suppression de chaque colonne de la liste, inversion du `WHEN`, `BEFORE → AFTER`, suppression du `RAISE`, ajout d'un cache dans la liste.

**Réalisation de 005c (2026-10-06).** 62 tests dédiés (groupes A à L : chaîne et rang 8, scénario de base, caches autorisés, champs protégés un à un, `frozen_at`, statut, absence de table de facturation, CHECK existants et formats des caches, BC non annulés, atomicité, régressions 005b, anti-contournement) ; suites vertes : 756 tests métier et 13 tests machine ; `integrity_check` ok et `foreign_key_check` vide ; campagne de mutation : 185 mutants, 164 tués, 21 survivants justifiés (19 CHECK de 005b hors périmètre, couverts par `test_005b` ; 2 mutants du runner d'émulation, équivalents) — **aucun survivant réel dans le périmètre 005c**. Seul `tr_12_bons_commande_annule` change entre le rang 7 et le rang 8 (79 objets de part et d'autre).

**Alignement documentaire préalable à 005c — réalisé le 2026-10-05** : décision D-56 ; modèle §4.19, §7.2 (ligne « BC annulé »), §8 (ligne `tr_12`), §17.1 (rangs et tableau des correctives), PT-16, PT-20 ; conventions §5 (chaîne des rangs) ; invariants INV-46/47/188 relus, aucun changement, et INV-173 précisé le 2026-10-05 (« montants » = montants contractuels) ; le présent cadrage (§M.2 : CHECK `termine` ⇒ `date_100_facture`). V6-20 (nommage de la migration et du test) : décidée le 2026-10-05. **Mise à jour du 2026-10-06** : la corrective 005c est livrée ; le modèle (D-56, §17.1), les conventions (§5) et le présent cadrage décrivent cet état.

### M.9 Stratégie de tests — mises à jour (détail en §17 et §18)

**Ajouts au futur `test_006_facturation.py`** (groupes G22 à G24, G15 révisé) :

| Groupe | Contenu |
|---|---|
| **G22 BC annulé** | acompte / situation / solde sur BC annulé → refusés ; devis rattaché → refusé (`tr_99`) ; modification commerciale (colonnes du contrat) → refusée ; modification de `statut`, `completed_at`, `cancelled_at`, `motif_annulation`, `frozen_at` → refusée ; avoir sur document existant → accepté ; recalcul des trois caches après avoir (un `UPDATE`) → accepté ; `statut` reste `annule` ; aucune réouverture implicite ; règlement sur document existant : « si prévu », test porté par 007 (la table `reglements` n'existe pas en 006) |
| **G23 BC `termine` et avoirs** | cas A à D de §M.5 (avoir partiel sur acompte, situation, solde ; avoir total sur acompte ; avoir total sur solde) ; conservation ou évolution de `termine` ; `termine → en_cours` possible dans le cas D ; `completed_at` cohérent (CHECK) ; `date_100_facture` cohérent (conservée / NULL / nouvelle valeur) ; aucun devis rattaché après un solde, **y compris crédité** (CK-14, service, trigger si V6-10) ; nouveau solde après solde crédité accepté ; acompte / situation après solde crédité refusés |
| **G24 `frozen_at` résiduel** | obligations O-1 à O-4 (pose conjointe, irréversibilité, NULL à la naissance, absence de comportement) ; la matrice `en_cours` / `gele` donne les **mêmes** résultats de facturation (`gele` = état de test, pas un statut) ; aucune colonne `frozen_at` dans `factures` |
| **G15 révisé** | CK-06 : pour un BC annulé, seuls les trois caches sont comparés au recalcul ; écriture conjointe `avancement` / `date_100_facture` |

**Campagne de mutation approfondie** (comparable aux tranches précédentes, conv. §7.1) :
- **006** : mêmes familles qu'en §18, plus les familles ajoutées par la mise à jour : définition de « neutralisée » (`=` ↔ `<=`, `<` ; `total_ht > 0` supprimé), clause « un solde a existé » (neutralisé ou non), `EXISTS ↔ NOT EXISTS` sur les soldes, conditions d'état du BC dans TR-16 (`annule`, `termine` autorisé pour l'avoir), requêtes CK-06 / CK-14 ;
- **005c** : campagne ciblée (§M.8) ;
- règle de clôture inchangée : **0 survivant non qualifié**, rapport mutant / classe / preuve / décision.

### M.10 Contradictions documentaires et corrections internes

Format imposé : **source (document + section)** · **règle** · **interprétation retenue** · **conséquence technique**.

| ID | Sources en tension | Règle | Interprétation retenue | Conséquence technique |
|---|---|---|---|---|
| **CD-01** | Consigne du 2026-10-05 (« `fournisseurs.date_100_facture` pilote le délai de 30 jours ») **vs** `002_fournisseurs.sql` (colonnes), cadrage 005 R28, 005 (commentaire SQL, `test_005` l.8), INV-103, INV-199, métier l.500 (§17) | délai de 30 jours des dépenses | **[RD]** la seule colonne `date_100_facture` est celle de `bons_commande` ; la règle est une règle de service Dépenses (hiérarchie 1 à 4 > consigne non étayée par le SQL) | aucun objet de 006 ne touche `fournisseurs` ; VR-13 écrit sans la colonne fantôme ; **à signaler à Rémy** |
| **CD-02** | Brief 006 §4, §16, §24 et rappel 005b (« gelé après le premier **encaissement actif** ») **vs** E-10, journal des invariants (INV-33/34/35 retirés le 2026-10-03), métier §9, modèle §7.1, §2.5 | gel progressif | **[VR]** VR-01 : E-10 l'emporte (niveaux 1, 2, 5) ; le brief reprenait une règle retirée | aucun gel ; `frozen_at` résiduel (§M.2) |
| **CD-03** | `tr_12_bons_commande_annule` (004/005b) « seul `updated_at` modifiable » **vs** INV-173, INV-188, INV-46/164, modèle §7.2, TR-12 « à adapter (PT-16) » ; 005b l.26-27 et l.352 (report à la tranche Facturation) | caches d'un BC annulé après avoir | **[VR]** VR-05 : invariants (niveau 2) > implémentation (niveau 7) | corrective 005c (§M.8) |
| **CD-04** | INV-47 et modèle §8 TR-16 (« avoir sur BC `termine` : l'existant le refuse, à confirmer ») **vs** CDC §22, C-06, C-13, arbitrage B | avoir sur BC `termine` | **[VR]** VR-07 : autorisé ; INV-47 est un énoncé « à confirmer », non décision | TR-16 n'existe pas dans le SQL (0 occurrence) : 006 le crée **sans** ce refus |
| **CD-05** | Métier §7 l.272 et CDC §16 (texte d'origine) : « …ou si un avoir intervient » **vs** CDC §16 amendement E-14/E-16 et modèle §3.5 : « seule l'annulation d'un règlement » | `termine → en_cours` | **[VR]** VR-07 : la formule INV-42 est recalculée ; un avoir qui neutralise le solde actif peut faire passer à `en_cours` (niveaux 2 et 4 > 5 et 6 sur ce point) | A6-03 résolu ; état dérivé, pas réouverture (§M.3) |
| **CD-06** | INV-52 (« actif » = non entièrement neutralisé par un avoir total) **vs** modèle §3.2, §3.4, §3.5, §4.8 (« proposition PT-9 ») | définition d'« actif » | **[VR]** VR-12 ; invariant (niveau 2) > modèle (niveau 3) ; seul le **mécanisme** reste proposition | `neutralisee(F)` dérivé des données, aucune colonne d'état |
| **CD-07** | INV-58, modèle §3.2 (« solde rédigé/validé » ⇒ plus d'acompte ni de situation) **vs** modèle §8 TR-22 et métier §13 (« solde actif ») | portée de l'interdiction après solde | niveau 2 (INV-58) > niveau 3 (TR-22) : l'interdiction vaut **même si le solde est totalement crédité** **[DT]** | `tr_22_factures_acompte` / `_situation` : refus dès qu'un solde existe (neutralisé ou non) |
| **CD-08** | INV-185, E-14, C-33 (« nouvelle facture du **même type** » après avoir total) **vs** INV-58 (plus d'acompte/situation après solde) | remplacement d'un acompte/situation crédité(e) après solde | **non tranché** : **[QO]** QO-1 ; lecture prudente **[PR]** | aucune règle SQL écrite pour ce cas avant décision |
| **CD-09** | CHECK de 004 (`termine` et `date_100_facture` ⇒ `frozen_at`) ; INV-46 (« la condition “gelé” des CHECK actuels dépend de PT-8 ») **vs** E-10 (gel supprimé) | sens des CHECK `frozen_at` | **[VR]** VR-02/03 : conservés ; obligations techniques O-1 à O-5 | contrat de service ; aucune migration |
| **CD-10** | Brief 006 §6 et §17 (« un avoir ne doit pas rouvrir automatiquement un BC ») **vs** métier §7 l.272 | sens de « rouvrir » | **[VR]** VR-08 : « rouvrir » = axe 2 (commercial) ; le recalcul `termine → en_cours` est l'axe 1 | libellés de 006 corrigés (§M.3 règle 4) |

**Corrections internes du cadrage** (formulations de ma part, retirées) :
1. L'arbitrage du 2026-10-05 et l'ancienne version de A6-06 écrivaient que la fenêtre de 30 jours « repart de la nouvelle date » : **faux ou imprécis** (VR-13, §M.6).
2. Le cadrage listait V6-02 comme « actif non défini » : INV-52 le définit (**[RD]**), seul le mécanisme restait proposition.
3. La consigne qualifie l'avoir partiel de réducteur du « montant économique restant dû » : précisé en §M.5.

### M.11 Questions restant réellement ouvertes

Après contrôle contre E-10, les invariants, le métier, le CDC, les errata, D-*, les migrations 001 → 005b et les tranches précédentes. **Les décisions validées ne sont pas rouvertes.**

| ID | Question | Pourquoi elle reste ouverte | Lecture prudente **[PR]** (non décidée) |
|---|---|---|---|
| **QO-1** (ex-V6-09) | Après émission d'un solde (actif ou crédité), peut-on remplacer un **acompte** ou une **situation** totalement crédité(e) par une nouvelle facture du même type ? | INV-185 / E-14 / C-33 (même type) et INV-58 (plus d'acompte/situation après solde) ne sont pas conciliés (CD-08) | non ; le montant se refacture par remplacement du solde |
| **QO-2** (ex-V6-02, A6-24) | Un **solde à `0.00`** émis par erreur ne peut recevoir aucun avoir (INV-55 : avoir `> 0.00`) : comment le corrige-t-on ? | conséquence directe de règles validées ; aucune règle de correction | ne rien inventer ; le dire |
| **V6-02** (résiduel) | Mécanisme **technique** de l'unicité sans `cancelled_at` | PT-9 : proposition de triggers `EXISTS` | triggers `BEFORE INSERT` ensemblistes |
| **V6-04**, **V6-05** | `factures.devis_id` (PT-10) ; colonnes de situation et plafond `< 100 %` (PT-11) | DDL de `factures` ; non touchés par cette mise à jour | cf. §19 |
| **V6-06**, **V6-07**, **V6-08**, **V6-10**, **V6-12** à **V6-19** | inchangés | non touchés par V6-01/V6-03 (V6-10 : garde SQL « après solde », VR-09 en fixe la règle mais pas la couche) | cf. §19 |
| **V6-20** (réduit) | Nom exact de la corrective 005c, de son test et des gardes d'exécution | le rang (8 / 9) et l'ordre sont **décidés** (VR-06) ; nommage **décidé le 2026-10-05** (migration `005c_bc_annule_caches_financiers.sql`, test `test_005c_bc_annule_caches_financiers.py`) ; aucune garde d'exécution dans le fichier SQL (005c ne crée aucun objet ; le runner D-55 pose le rang) | §M.8 |

**Closes par cette mise à jour** : V6-01 (VR-01 à VR-03), V6-03 (VR-04 à VR-09), V6-11 (VR-10, VR-13), la définition d'« actif » de V6-02 (VR-12), A6-03, A6-06, A6-12, A6-23.

---

## 0. Préambule : méthode, vérifications, légende

### 0.1 Légende des qualifications (brief §28)

Chaque affirmation importante porte l'une de ces étiquettes (quatre d'origine, deux ajoutées le 2026-10-05) et une référence.

| Étiquette | Sens |
|---|---|
| **[RD]** RÈGLE DOCUMENTÉE | écrite explicitement dans une source V6 (référence donnée) |
| **[DT]** DÉDUCTION TECHNIQUE | conséquence nécessaire d'une règle existante (la règle de départ est citée) |
| **[PR]** PROPOSITION | solution technique proposée, **non décidée**. Jamais présentée comme règle métier |
| **[DV]** DÉCISION À VALIDER | point que les sources ne permettent pas de trancher ; numéroté `V6-nn` (§19) |
| **[VR]** DÉCISION VERROUILLÉE | décision prise par Rémy le 2026-10-05 (V6-01, V6-03) ; numérotée `VR-nn` (§M.1) ; propre à ce cadrage, non officielle |
| **[QO]** QUESTION OUVERTE | point que ni les sources ni les décisions ne permettent de trancher ; numéroté `QO-n` (§M.11) ; équivaut à **[DV]** |

Les contradictions et ambiguïtés sont numérotées `A6-nn` (§15) et `CD-nn` (§M.10). Les décisions à valider sont numérotées `V6-nn` (§19) et les décisions verrouillées `VR-nn` (§M.1). Ces numérotations sont propres à ce cadrage ; **elles ne sont pas des décisions officielles** (brief §30).

Abréviations de sources : **modèle** = `MAJ__modèle-données-sqlite-v6-v3.13.md` ; **invariants** = `MAJ__invariants.md` (INV-xx) ; **métier** = `MAJ__modèle-métier-V6.md` ; **CDC** = `MAJ__cdc-fonctionnel-architectural-v6.md` ; **errata** = `MAJ__cdc-errata-v6.md` (E-xx) ; **conv.** = `MAJ__conventions-techniques-v6.md` ; **audit conservation** = `MAJ__AUDIT__REGLE_CONSERVATION_OBJETS_NUMEROTES.md` (D1–D6) ; **audit fonctionnel** = `MAJ__audit-fonctionnel-v5.16-v6.md` ; PT-xx / D-xx / T-xx / C-xx / CK-xx / TR-xx = identifiants du modèle.

### 0.2 Vérification préalable du clone (brief « Méthode imposée »)

| Contrôle | Résultat |
|---|---|
| Clone frais de `origin/main` | HEAD `37530e5` |
| Migrations métier 001 → 005b | présentes : `001_initial`, `002_fournisseurs`, `003_devis`, `004_bons_commande`, `005_depenses`, `005a_corrections_v313`, `005b_bc_multi_devis` (`src-tauri/migrations/metier/`) |
| Tests 001 → 005b | présents : `test_001_initial` … `test_005b_bc_multi_devis` (`src-tauri/tests/metier/`) ; **694 tests métier verts** (153 pour 005b), 13 tests `machine` verts |
| SQL 005b d'origine = SQL 005b local | identiques (le SQL et le test de 005b poussés sont identiques aux copies locales) |
| Chaîne 001 → 005b rejouée en mémoire (runner émulé : `executescript`, `user_version = rang`) | `PRAGMA integrity_check` = `ok` ; `PRAGMA foreign_key_check` = vide ; **rang 7**, 79 objets nommés (17 tables, 15 index, 47 triggers, 0 vue) |
| Présence de tables de facturation | **aucune** : `factures`, `facture_lignes`, `reglements`, `garanties`, `historique`, `documents`, `parametres_entreprise` n'existent pas dans la chaîne (les tests 003/004/005 l'assertent : `test_003:273`, `test_004:480,1702`, `test_005:374`) |

> Les 17 tables du rang 7 : `bc_devis`, `bc_ligne_garanties`, `bc_lignes`, `bons_commande`, `categories_depenses`, `categories_prestations`, `clients`, `depenses`, `devis`, `devis_ligne_garanties`, `devis_lignes`, `devis_revisions`, `fournisseurs`, `import_anomalies`, `numerotation_sequences`, `prestation_garanties`, `prestations`.

### 0.3 Anomalies de dépôt constatées (hors périmètre de correction ici)

1. **Chemins du brief inexistants.** Le brief cite `docs/conception/modèle-données-sqlite-v6-v3.13.md`, `docs/conception/invariants.md`, etc. Dans le dépôt, `docs/` contient encore la **V3.12** (et un `docs/README.md` de cette époque) ; la **V3.13** n'existe que sous forme de copies de travail `fichiers-a-relire/MAJ__*` (en relecture, non intégrées à `docs/`). Le présent cadrage s'appuie sur ces copies `MAJ__*`, parce que ce sont elles qui portent les décisions D-40 → D-55 et les errata E-10 → E-20 sur lesquels reposent 005a et 005b. → **A6-00 / V6-18** : intégrer (ou confirmer) la V3.13 avant de figer le SQL.
2. **`fichiers-a-relire/CADRAGE__005b_bc_multi_devis.md` sur `origin/main`** est une copie de 104 lignes contenant du HTML GitHub collé ; la version locale (191 lignes, non suivie) est la version propre. Aucune action ici.
3. **`historique`, `documents`, `parametres_entreprise`** sont référencés par le modèle (événements `emission`, `avoir`, `documents.type_entite = 'facture'`, snapshot entreprise) mais **n'existent pas encore** dans la chaîne (D-34 : « traités dans leur contexte propre »). Conséquence pour 006 en §14.

### 0.4 Sources auditées

Modèle V3.13 (§2.3–2.5, §3.1–3.8, §4.6–4.10, §4.17–4.19, §6, §7, §8, §9, §10, §11, §13, §14, §15, §16, §17, §19) ; invariants (INV-01 → 08, 20 → 27, 31 → 36, 38 → 48, 52 → 62, 70 → 80, 85 → 90, 103, 130 → 136, 164 → 170, 173 → 201, journal) ; métier §1, §2, §7–§17 ; CDC §1–§3, §6, §14–§22, §24, §42 et amendements E-13/E-14/E-15/E-16/E-17/E-18 ; errata E-01, E-07, E-10 → E-20 ; conv. §5, §7, §7.1, §9 ; audit conservation (D1–D6, §4.4, §4.6, §8–§9) ; audit fonctionnel (facturation) ; migrations 001 → 005b (DDL réel rejoué) ; tests 001 → 005b (en-têtes, constantes de chaîne, groupes T-44/T-45/T-46, CK13/CK14).

---

## Synthèse (à lire d'abord)

1. **006 = deux tables** : `factures` (4 types dans une seule table) et `facture_lignes`. Rien d'autre n'est nécessaire (§2). **[RD]** modèle §4.8 ; **[PR]** pour les colonnes de PT-10/PT-11.
2. **Une facture validée est un fait historique** : créée, numérotée et validée dans une seule transaction, jamais modifiée, jamais supprimée, jamais annulée ; correction par avoir ; après avoir total, nouvelle facture du même type avec nouveau numéro. **[RD]** INV-185, INV-53, E-14, D-45.
3. **La facturation est globale au niveau du BC** ; seul l'acompte est rattaché à un devis (`devis_id`, PT-10). **[RD]** D-48, INV-189, INV-190 ; **[PR]** mécanisme `factures.devis_id`.
4. **Pas de TVA, pas de TTC** dans Essentiel V6. **[RD]** CDC §1–§2, métier §10, modèle §4.8, INV-55. La mention légale de franchise n'est spécifiée nulle part (**[DV]** V6-16, hors SQL).
5. **Mise à jour du 2026-10-05 : deux des trois blocages d'origine sont levés** (partie M) :
   - **V6-01 `frozen_at`** : gel progressif abandonné (E-10) ; colonne conservée à titre **résiduel technique** ; obligations techniques O-1 à O-5 documentées (VR-01 à VR-03).
   - **V6-03 BC annulé / BC `termine` / caches** : BC annulé = terminal commercial mais **non figé financièrement** ; caches évolutifs ; avoir autorisé sur BC `termine` ; **état financier dérivé ≠ réouverture commerciale** (VR-04 à VR-09) ; corrective **005c** préalable (VR-06) ; **006 au rang 9**.
   - **V6-02** : « actif » est défini (VR-12) ; restent le mécanisme technique et le solde `0.00` (QO-2).
   - **Restent bloquants pour le DDL de `factures`** : V6-04 (PT-10) et V6-05 (PT-11) (§19).
6. **Aucun nouveau CK, aucune nouvelle décision officielle, aucun nouveau type de document n'est créé.** Les CK utilisés sont les CK existants (CK-01, 02, 04, 05, 06, 13, 14) ; CK-04/05/06 deviennent exécutables avec 006, et le morceau de CK-14 « aucun devis rattaché après un solde » (que 005b n'a pas pu tester faute de factures) se complète en 006.
7. **Une seule question métier nouvelle reste ouverte après la mise à jour** : QO-1 (remplacement d'un acompte ou d'une situation crédité(e) alors qu'un solde existe, CD-08). La règle des 30 jours des dépenses n'est ni implémentée, ni réinitialisée, ni prolongée par 006 ; la colonne `fournisseurs.date_100_facture` citée dans la consigne du 2026-10-05 n'existe pas (CD-01).

---

## 1. Cadrage métier de la facturation

### 1.1 Qu'est-ce qu'une facture dans BATORYA Essentiel V6 ? (question 1)

**[RD]** « La Facture représente un document de facturation **validé** : il n'existe **pas de brouillon persistant**. La facture est créée, numérotée et validée en une seule opération ; l'abandon d'une préparation avant validation ne crée aucun objet ; le numéro n'est attribué qu'à la validation » (métier §10 ; INV-185 ; E-14 ; D-45 ; modèle §4.8 « Aucun brouillon persistant »).

**[RD]** Une facture est : rattachée à **un BC** (le ou les devis sont accessibles par le BC) (métier §10) ; porteuse de **snapshots** client/entreprise/chantier (modèle §4.8, §2.4 BLOC-SNAP) ; **sans statut stocké** (INV-60) ; **sans TVA ni TTC** (métier §10, modèle §4.8, INV-55) ; **immuable dès l'INSERT**, jamais supprimée, jamais annulée (INV-53, INV-185, TR-20, TR-21).

**[DT]** La « validation » n'a pas de date distincte : l'émission **est** la validation (une seule transaction, INV-185). Il n'existe donc ni `date_validation`, ni état intermédiaire, ni `updated_at` (modèle §4.8 : « Pas de `updated_at`, pas de `statut`, pas de `total_ttc` »).

### 1.2 Types exacts de documents facturés (question 2)

**[RD]** Quatre types fonctionnels : `acompte`, `situation`, `solde`, `avoir` (CDC §18 ; modèle §2.5 `factures.type` ; INV-55). Le type historique `complete` n'existe pas (CDC §18 ; métier §10 ; INV-55).

| Type | Préfixe / séquence | Montant `total_ht` | Rattachement | Lignes (`facture_lignes`) | Sources |
|---|---|---|---|---|---|
| `acompte` | `ACP-nnnnn-yy` / ACP | `> 0.00`, ≤ contractuel du devis concerné | BC **et** devis d'origine (PT-10) | 1 ligne `synthese` = `total_ht` | métier §10 ; modèle §4.8 ; INV-57, INV-62, INV-189 |
| `situation` | `FAC-nnnnn-yy` / FAC (partagée avec solde) | `> 0.00` ; cumul net après ≤ contractuel | BC (globale, tous devis) | 1 ligne `synthese` = montant de la situation | métier §12 ; modèle §3.2, §4.8 ; INV-57, INV-62, INV-190 |
| `solde` | `FAC-nnnnn-yy` / FAC | `≥ 0.00` (le `0.00` est autorisé) ; = contractuel − facturation nette avant | BC (global) | lignes `prestation` copiées des lignes du BC, puis lignes `deduction` ; Σ = `total_ht`, y compris `0.00` | métier §13 ; modèle §3.2, §4.8 ; INV-55, INV-58, INV-62 |
| `avoir` | `AVO-nnnnn-yy` / AVO | `> 0.00`, Σ avoirs d'une origine ≤ montant de l'origine | BC de la facture d'origine ; `origine_facture_id` obligatoire | lignes positives (`prestation` ou `synthese`) | métier §14 ; modèle §4.8 ; INV-76, INV-62 |

**[RD]** « La facture finale est toujours un solde », y compris sans acompte ni situation préalable et y compris à `0.00` (CDC §18 « Solde » ; métier §13 ; INV-55, INV-58).

**[DV] / A6-09** — « facture corrective » et « document correctif » : le brief et plusieurs sources (E-14, INV-185, métier §10 : « ou, selon le cas, un document correctif ») les citent, mais **aucune source ne définit un cinquième type** ; l'énumération `factures.type` est fermée à quatre valeurs (modèle §2.5). **[PR]** Considérer que l'avoir est le seul document correctif ; ne créer aucun type supplémentaire. À confirmer (V6-08).

### 1.3 Ce qui relève de 006, ce qui attend 007 (question 13)

| Sujet | 006 Facturation | 007 Règlements (et suivantes) | Source |
|---|---|---|---|
| Tables | `factures`, `facture_lignes` | `reglements` (+ TR-30 → TR-33) ; `garanties` (008) ; `historique`, `documents` (contexte propre) | D-34 ; modèle §4.8–§4.10, §17.1 |
| Facturation nette, solde, situation, acompte (montants, plafonds, unicité) | **oui** | — | modèle §3.2, TR-22, TR-23 |
| Immuabilité, non-suppression, numérotation | **oui** | — | INV-53, TR-20, TR-21, TR-02 |
| Caches du BC `montant_deja_facture_ht`, `avancement`, `date_100_facture` | service financier (calcul) ; **colonnes déjà en 004** ; évoluent aussi sur un BC annulé après une opération financière légitime (VR-05, corrective **005c**) | — | INV-46, modèle §3.7 ; §M.6 |
| `reste_du`, `absorbe`, `credit`, états de paiement, `en_retard` | — (calculs dérivés) | **007** | modèle §3.3, §3.4 ; INV-72 → 75 |
| `statut = 'termine'`, `completed_at` | conditions : « solde actif » (006) **et** Σ `reste_du` = 0 (007) | **007** pour la partie encaissements | modèle §3.5 ; INV-42 |
| Garanties | — | 008 | modèle §4.10 ; INV-85 → 90 |
| Exécution, remise globale au prorata | **rien n'est créé** (PT-12, PT-13 « À CONCEVOIR ») | — | modèle §3.8 ; INV-191, INV-192 |

**[DT]** Avant 007, tout encaissement est nul : `reste_du(F) = total_ht(F) − absorbe(F)`. La partie « encaissements » de `termine` ne peut donc être exercée qu'avec 007 ; 006 n'a **ni besoin ni droit** de créer `reglements` (D-34 ; brief §30 « ne pas créer de tranche 007 »).

### 1.4 Mécanique commune d'une émission (rappel des règles déjà tranchées)

1. **[RD]** Réservation du numéro (PT-1, tranché 2026-10-03, modèle §11.4) : `n = max(compteur, high-water) + 1` sous `BEGIN IMMEDIATE` ; high-water écrit durablement dans `machine.db` ; compteur posé à `n` et **committé** ; l'objet est créé dans une **transaction distincte** avec le numéro `n`. Un trou après crash ou rollback est accepté et **n'est jamais récupéré** (INV-179, D-54, E-13, C-42).
2. **[RD]** Dans la transaction de l'objet : INSERT `factures` + INSERT `facture_lignes` + écriture des caches du BC **en un seul `UPDATE`** (INV-46, modèle §3.7).
3. **[RD]** Le numéro n'est affiché ni remis (PDF, e-mail) avant le COMMIT de l'objet (modèle §11.4 point 7).
4. **[DT]** Tout cela relève du **service** : le SQL de 006 ne fait que garantir ce qui peut l'être structurellement (§11).

---

## 2. Modèle de données proposé

### 2.1 Architecture : deux tables, justification (brief §23)

| Table | Raison métier | Source |
|---|---|---|
| `factures` | une seule table typée pour acompte, situation, solde, avoir : même numérotation (table unique → `UNIQUE(numero)` couvre FAC partagée), même immuabilité, mêmes snapshots, mêmes FK | **[RD]** modèle §4.8, §6 ; métier §10 |
| `facture_lignes` | photographie des éléments facturés, indépendante du catalogue et du devis après émission ; négatifs uniquement pour `deduction` | **[RD]** modèle §4.8 ; métier §11 ; INV-62 |

**Tables explicitement non créées** (brief §23 « pas de structure générique au cas où ») :

| Candidat | Décision | Motif |
|---|---|---|
| `acomptes`, `situations`, `soldes`, `avoirs` séparées | **non** | le modèle prévoit une table unique ; les colonnes propres à un type sont gardées par CHECK (§2.2). **[RD]** modèle §4.8 |
| table de lien facture ↔ devis | **non** | un acompte référence **un** devis : colonne `devis_id` (PT-10) ; situation et solde sont globaux. **[PR]** |
| table de ventilation par devis | **non** | la facturation est globale au BC ; aucune ventilation n'est documentée. **[RD]** INV-190, D-48 |
| table d'« état » ou de « neutralisation » d'une facture | **non** | un état stocké contredirait INV-60 et l'immuabilité ; « entièrement créditée » est **dérivé** (PT-9). **[DT]** |
| `facture_taxes`, colonnes TVA/TTC | **non** | Essentiel V6 est hors TVA (§8). **[RD]** |
| brouillons de facture | **non** | INV-185. **[RD]** |
| `reglements` | **non** (007) | D-34 |
| événements d'historique | **non** | la table `historique` n'existe pas encore (§0.3) |

### 2.2 Table `factures` (PROPOSITION de DDL, issue du modèle §4.8)

STRICT, `id INTEGER PRIMARY KEY AUTOINCREMENT` (INV-04, conv. §9).

| Colonne | Type / famille | Null | Origine de la colonne | Remarques |
|---|---|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | NN | **[RD]** INV-04 | jamais réutilisé |
| `numero` | TEXT | NN, **UNIQUE** | **[RD]** modèle §4.8, INV-20 | immuable (TR-20 interdit tout UPDATE) |
| `type` | TEXT CHECK IN (`acompte`,`situation`,`solde`,`avoir`) | NN | **[RD]** §2.5 | |
| `bc_id` | INTEGER FK → `bons_commande(id)` **ON DELETE RESTRICT** | NN | **[RD]** §4.8 | |
| `client_id` | INTEGER FK → `clients(id)` **ON DELETE RESTRICT** | NN | **[RD]** §4.8, INV-48 | = `client_id` du BC (trigger) |
| `devis_id` | INTEGER FK → `devis(id)` **ON DELETE RESTRICT** | NULL | **[PR]** PT-10 | acompte seulement ; voir §9.2 |
| `client_snapshot`, `entreprise_snapshot`, `chantier_snapshot` | TEXT `json_valid` | NN | **[RD]** BLOC-SNAP | |
| `client_snapshot_version`, `entreprise_snapshot_version`, `chantier_snapshot_version` | INTEGER | NN | **[RD]** BLOC-SNAP | même forme que `bons_commande` |
| `objet` | TEXT | NULL | **[RD]** §4.8 | |
| `date_emission` | D (`GLOB` + `date(x) IS x`) | NN | **[RD]** §4.8, INV-10 | date de numérotation (§7) |
| `date_echeance` | D | NULL | **[RD]** §4.8, INV-59 | NN hors avoir, NULL pour un avoir |
| `total_ht` | D2 | NN | **[RD]** §4.8, INV-55 | |
| `situation_numero` | INTEGER ≥ 1 | NULL | **[RD]** §4.8 | situation seulement ; D6 ouverte |
| `situation_mode` | TEXT IN (`pourcentage`,`montant`) | NULL | **[PR]** PT-11 | situation seulement |
| `situation_valeur_saisie` | TEXT (P2 si pourcentage, D2 si montant) | NULL | **[PR]** PT-11 | situation seulement ; sens du « montant » : V6-05 |
| `avancement_cumule_pct` | P2 | NULL | **[RD]** §4.8 | situation seulement |
| `montant_deja_facture_ht` | D2 | NULL | **[RD]** §4.8, §3.2 | situation seulement : facturation nette **avant** la situation |
| `origine_facture_id` | INTEGER FK → `factures(id)` **ON DELETE RESTRICT** | NULL | **[RD]** §4.8 | avoir seulement |
| `motif_avoir` | TEXT | NULL | **[RD]** §4.8, INV-76 | avoir seulement, non vide |
| `created_at` | TEXT (horodatage canonique, défaut `strftime`) | NN | **[RD]** §2.2 | donnée technique |
| `origine`, `legacy_id`, `legacy_data` | BLOC-IMP | NN / NULL / NULL | **[RD]** §2.4, D-23 | pas de `legacy_numero` (réservé à `clients` et `bons_commande`) |

**Absences voulues** : `updated_at`, `statut`, `cancelled_at`, `motif_annulation`, `total_ttc`, `taux_tva`, `montant_tva`, `frozen_at`, `date_validation`, `date_paiement`, colonne `avoir_id`. **[RD]** modèle §4.8 ; E-14 ; INV-60, INV-185 ; CDC §2.

**CHECK de table proposés** (chacun avec sa source) :

| # | CHECK | Source |
|---|---|---|
| F1 | `type IN (…)` | **[RD]** §2.5 |
| F2 | `(type = 'avoir') = (origine_facture_id IS NOT NULL)` | **[RD]** §4.8 |
| F3 | `type = 'avoir'` ⇒ `motif_avoir` non NULL, non vide, et `date_echeance` NULL ; `type <> 'avoir'` ⇒ `date_echeance` non NULL et `motif_avoir` NULL | **[RD]** §4.8, INV-59, INV-76 |
| F4 | `date_echeance IS NULL OR date_echeance >= date_emission` | **[RD]** §4.8, INV-59 |
| F5 | `(type = 'situation') = (situation_numero IS NOT NULL) = (situation_mode IS NOT NULL) = (situation_valeur_saisie IS NOT NULL) = (avancement_cumule_pct IS NOT NULL) = (montant_deja_facture_ht IS NOT NULL)` | **[RD]** §4.8 pour 3 des 6 termes ; **[PR]** PT-11 pour mode/valeur |
| F6 | `total_ht` D2 ; `total_ht <> '0.00'` sauf `type = 'solde'` | **[RD]** INV-55, §4.8 |
| F7 | `origine = 'v6'` ⇒ préfixe (`acompte→ACP-`, `avoir→AVO-`, `situation|solde→FAC-`), format `xxx-nnnnn-yy`, `yy = substr(date_emission, 3, 2)` ; `origine = 'import'` ⇒ `numero` non vide (seule exemption) | **[RD]** §4.8, §10.4, INV-131, D-24 |
| F8 | `(type = 'acompte') = (devis_id IS NOT NULL)` | **[PR]** PT-10 |
| F9 | `origine = 'v6'` ⇒ `legacy_id`, `legacy_data` NULL | **[RD]** §2.4 |
| F10 | dates : `GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'` ET `date(x) IS x` — **aucune borne d'année** | **[RD]** §2.2, D-38, INV-10 |
| F11 | `situation_mode = 'pourcentage'` ⇒ `situation_valeur_saisie` P2 ; `= 'montant'` ⇒ D2 `> 0.00` ; `situation_numero >= 1` ; `avancement_cumule_pct` P2 ; `montant_deja_facture_ht` D2 | **[RD]** familles §2.3 ; **[PR]** pour la forme de la valeur |
| F12 | `created_at` au format canonique | **[RD]** §2.2 |

**[DV] / V6-05** : faut-il borner `avancement_cumule_pct` strictement sous `100.00` (« une situation atteignant 100 % n'existe pas », métier §12) ou le laisser jusqu'à `100.00` (« nette après ≤ contractuel », modèle §3.2) ? Voir A6-17.

**Index** (modèle §9, un par FK + recherche) : `factures(bc_id)`, `factures(client_id)`, `factures(origine_facture_id)`, `factures(type, date_echeance)`, `factures(date_emission)`, `factures(devis_id)` **[PR]** PT-10. `numero` est déjà indexé par son `UNIQUE`. **[PR]** Aucun index supplémentaire (ex. `(bc_id, type)`) n'est proposé : non documenté, à justifier par une mesure si besoin plus tard.

### 2.3 Table `facture_lignes` (PROPOSITION de DDL, modèle §4.8)

| Colonne | Type / famille | Null | Remarques |
|---|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | NN | |
| `facture_id` | INTEGER FK → `factures(id)` **ON DELETE RESTRICT** | NN | **[RD]** §4.8 « RESTRICT » ; D-20 |
| `ordre` | INTEGER `>= 1` | NN | `UNIQUE(facture_id, ordre)` |
| `bc_ligne_id` | INTEGER FK → `bc_lignes(id)` **ON DELETE RESTRICT** | NULL | référence éventuelle à la ligne de BC d'origine (métier §11) |
| `reference_prestation` | TEXT | NULL | |
| `designation` | TEXT non vide | NN | |
| `description` | TEXT | NULL | |
| `quantite` | DL | NN | |
| `unite` | TEXT IN (`u`,`ens`,`ml`,`m2`,`m3`) | NN | D-13, §2.5 |
| `prix_unitaire_ht` | DL | NN | |
| `remise_type` | TEXT IN (`aucune`,`pourcentage`,`montant`) | NN | |
| `remise_valeur` | TEXT | NULL | `(remise_type = 'aucune') = (remise_valeur IS NULL)` comme `bc_lignes` |
| `type_ligne` | TEXT IN (`prestation`,`synthese`,`deduction`) | NN | |
| `montant_ht` | **D2S** | NN | seule colonne métier où le négatif est autorisé (modèle §2.3) |
| `created_at` | TEXT | NN | |

**CHECK proposés** : `type_ligne = 'deduction'` ⇔ `montant_ht` négatif (préfixe `-`, `-0.00` interdit par D2S) **[RD]** INV-62 ; pour une déduction : `quantite = '1'` **[RD]** §4.8 ; `designation <> ''` ; cohérence `remise_*` identique à `bc_lignes`. **[DT]** « `prix_unitaire_ht` = valeur absolue du montant de la déduction » et « `montant_ht = −arrondi(quantite × prix)` » (modèle §4.8) sont des calculs : à garantir par le **service** et à détecter par CK-05 ; aucun CHECK de calcul n'existe pour `bc_lignes` non plus (précédent 004).

**Index** : `UNIQUE(facture_id, ordre)` (tient lieu d'index sur `facture_id`, modèle §9) ; `facture_lignes(bc_ligne_id)`.

**Absences voulues** : `updated_at`, `active`, `type_prestation` (le modèle §4.8 ne le prévoit pas ; les garanties se lisent via `bc_ligne_garanties`, 008), liaison générique, BLOC-IMP (modèle §2.4 : les lignes importées sont imbriquées dans leur facture sans `ref` propre). **[RD]**

### 2.4 Triggers proposés (noms au format des tranches 004/005b)

| Trigger (PR) | Table / événement | Règle gardée | Source |
|---|---|---|---|
| `tr_02_factures_chronologie` | `factures` BEFORE INSERT | ACP/FAC/AVO : `date_emission >= derniere_date` de la clé (garde pure **[PR]** ; qui écrit `derniere_date` : V6-07) | **[RD]** TR-02, INV-24 ; détail ouvert : V6-07 |
| `tr_16_factures_bc` | `factures` BEFORE INSERT | acompte/situation/solde : BC `en_cours` (ni `termine`, ni annulé) ; toute facture : `client_id = bons_commande.client_id` ; **avoir permis sur BC `termine` et sur BC annulé** (VR-04, VR-07) | **[RD]** TR-16, INV-47, INV-48, INV-188 ; **[VR]** VR-04, VR-07 |
| `tr_22_factures_acompte` | `factures` BEFORE INSERT (type acompte) | devis rattaché au BC (`bc_devis`) ; un acompte non neutralisé par devis ; `total_ht ≤ devis.total_ht` ; aucun solde existant sur le BC | **[RD]** TR-22, INV-52, INV-57, INV-189 ; **[PR]** forme (PT-10, PT-9) |
| `tr_22_factures_situation` | idem (type situation) | aucune situation si un solde existe ; une situation non neutralisée par numéro ; `montant_deja_facture_ht` = facturation nette avant ; facturation nette après ≤ contractuel (borne : V6-05) | **[RD]** TR-22, INV-57 ; **[PR]** forme |
| `tr_22_factures_solde` | idem (type solde) | un seul solde non neutralisé par BC ; `total_ht = contractuel − facturation nette avant` (≥ 0) | **[RD]** TR-22, INV-52, INV-58 ; tension avec modèle §14 : A6-13 |
| `tr_23_factures_avoir` | idem (type avoir) | origine existante, non avoir, même BC ; Σ avoirs de l'origine + `total_ht` ≤ `total_ht` de l'origine ; avoir sur avoir interdit | **[RD]** TR-23, INV-76 |
| `tr_20_factures_no_update` | `factures` BEFORE UPDATE | aucun UPDATE (couvre `numero` immuable, `client_id`, etc.) | **[RD]** TR-20, INV-53, INV-185 |
| `tr_21_factures_no_delete` | `factures` BEFORE DELETE | aucune suppression (directe ou par `REPLACE`, `recursive_triggers=ON`) | **[RD]** TR-21, INV-53, INV-06 |
| `tr_21_facture_lignes_no_update` / `_no_delete` | `facture_lignes` | aucune modification, aucune suppression | **[RD]** TR-21, INV-53 |
| `tr_24_facture_lignes_insert` | `facture_lignes` BEFORE INSERT | composition par type de facture (acompte/situation : 1 ligne `synthese` ; avoir : lignes positives `prestation`/`synthese` ; `deduction` seulement pour un solde) ; `bc_ligne_id` appartenant au BC de la facture | **[DT]** INV-62 (« SQL, SVC ») ; **[DV]** V6-14 |
| `tr_99_bc_devis_apres_solde` | `bc_devis` BEFORE INSERT | aucun rattachement de devis si un solde (même totalement crédité) existe sur le BC | **[RD]** « trigger possible avec la tranche Facturation » (modèle §4.7, §14) ; règle fixée par **[VR]** VR-09 ; couche (trigger ou service + CK-14) : **[DV]** V6-10 |

> Remarque de numérotation : `TR-24` du modèle est « obsolète, jamais créé » (annulation de facture). Je ne le réutilise pas pour une autre règle : le nom `tr_24_facture_lignes_insert` est **[PR]**, un autre identifiant sera choisi à la rédaction du SQL si l'on veut éviter toute confusion avec TR-24 du modèle.

**[RD]** Triggers sans exemption d'origine : les factures `origine = 'import'` les traversent (modèle §8 en-tête, INV-131).

---

## 3. Relations

### 3.1 Carte des relations

| Relation | Cardinalité | FK / mécanisme | `ON DELETE` | Source |
|---|---|---|---|---|
| BC → factures | 1 → N | `factures.bc_id` | RESTRICT | **[RD]** §4.8 |
| BC ↔ devis | 1 ↔ N (un devis dans un seul BC) | `bc_devis(bc_id, devis_id UNIQUE, rang)` — **existe depuis 005b** | RESTRICT | **[RD]** 005b, INV-187 |
| devis → facture d'acompte | 1 → 0..1 non neutralisé (« un acompte par devis ») | `factures.devis_id` | RESTRICT | **[RD]** D-48, INV-189 ; **[PR]** mécanisme PT-10 |
| facture → lignes | 1 → N | `facture_lignes.facture_id` | RESTRICT | **[RD]** §4.8 |
| ligne de facture → ligne de BC | N → 0..1 | `facture_lignes.bc_ligne_id` | RESTRICT | **[RD]** §4.8, métier §11 |
| facture → avoir | 1 → N (plusieurs avoirs partiels possibles) | `factures.origine_facture_id` | RESTRICT | **[RD]** INV-76 (« Σ avoirs ≤ montant de l'origine »), métier §14 |
| facture → client | N → 1 | `factures.client_id` | RESTRICT | **[RD]** §4.8 |
| facture ↔ acompte/situation/solde | même table, colonne `type` | CHECK F5/F8 | — | **[RD]** §4.8 |
| facture ← règlements | 1 → N | `reglements.facture_id` (**007**) | — | modèle §4.9 |
| facture ← garantie | `garanties.facture_declenchement_id` (**008**) | — | — | modèle §4.10 |

**[RD]** Aucune relation facture ↔ `devis_lignes` : la facture ne dépend « plus du catalogue ni du devis après émission » (métier §11). **[DT]** Les lignes de devis ne sont atteintes que par `bc_lignes.devis_ligne_id`, depuis le BC.

**[DT] Aucune FK entrante ne peut supprimer une facture** : les FK entrantes futures (`reglements`, `garanties`, `urssaf_*`) sont toutes en RESTRICT (conv. §9). Les seules FK sortantes de `facture_lignes` pointent vers des objets déjà non supprimables (`bc_lignes` : `tr_13_bc_lignes_delete` ; BC : `tr_19`).

### 3.2 Réponses précises aux questions du brief

**Facture directement liée au BC ou aux devis / lignes ?** (question 4) — **[RD]** au BC (`bc_id` NN). Le devis n'est référencé que pour un acompte (PT-10 **[PR]**). Les lignes de facture peuvent référencer une `bc_ligne` (jamais une ligne de devis). Le brief demande de « ne pas supposer qu'une facture est directement rattachée à un devis si les documents V6 établissent une relation BC → facturation » : c'est le cas (métier §10 : « BC (le ou les devis sont accessibles par le BC) »).

**Facture ↔ avoir** — lien **direct et obligatoire** (`origine_facture_id`, F2), même BC que l'origine, jamais d'avoir sur avoir (TR-23, INV-76). Plusieurs avoirs partiels sont possibles sur une même origine dans la limite de son montant (INV-76 ; modèle §3.3 « Σ avoirs actifs ≤ M »). **[RD]**

**BC ↔ plusieurs devis (côté facturation)** — voir §9.2.

---

## 4. Cycle de vie

### 4.1 Principe commun à tous les documents de facturation

| Étape | Règle | Qualif. | Source |
|---|---|---|---|
| Préparation | aucun objet persistant ; l'abandon ne crée rien et ne consomme aucun numéro | **[RD]** | INV-185, INV-180 (par analogie de principe), modèle §6, D-45 |
| Réservation du numéro | transaction propre, committée **avant** l'objet (PT-1) ; un trou est accepté, jamais récupéré | **[RD]** | modèle §11.4, INV-179, D-54, C-42 |
| Émission = validation | une seule transaction : facture + lignes + caches du BC (un seul `UPDATE`) | **[RD]** | INV-185, INV-46, modèle §3.7 |
| Après émission | **immuable** : ni contenu, ni lignes, ni numéro, ni montants, ni snapshots, ni `client_id` | **[RD]** | INV-53, TR-20, TR-21, modèle §7.2 (ligne `factures`, `facture_lignes`), E-12 |
| Correction | **avoir** ; après avoir total, nouvelle facture du **même type**, **nouveau numéro** ; l'initiale et son avoir restent | **[RD]** | INV-185, E-14, D-45, arbitrage B, C-33 |
| Annulation | **n'existe pas** (`cancelled_at`, `motif_annulation`, état « Annulée », TR-24 obsolètes) | **[RD]** | E-14, INV-185 |
| Suppression | **jamais**, pour aucun type, ni pour les lignes | **[RD]** | INV-53, TR-21, INV-06, conv. §9 |
| État | aucun statut stocké ; état de paiement dérivé (007) ; « entièrement créditée » dérivé (PT-9) | **[RD]** / **[DV]** | INV-60 ; PT-9 |

### 4.2 Par type de document (question 10 : quand devient-on immuable ? — toujours dès l'INSERT)

| | Acompte | Situation | Solde | Avoir |
|---|---|---|---|---|
| Préalable | BC `en_cours`, devis rattaché au BC, aucun solde sur le BC | BC `en_cours`, aucun solde sur le BC | BC `en_cours`, aucun solde **non neutralisé** | facture d'origine (non avoir) du même BC ; BC annulé accepté |
| Particularité | peut exister **sans être payé** : trois niveaux distincts (acompte prévu / facture / règlement) | globale au BC ; mode, valeur saisie, avancement, montant HT facturé **figés** | toujours le document final ; `0.00` autorisé ; clôture commerciale du BC (plus de devis) | Σ avoirs ≤ montant de l'origine ; pas d'avoir sur avoir ; pas annulable |
| Modifiable | non | non | non | non |
| Corrigé par | avoir (total → nouvel acompte du même devis) | avoir (partiel libère un montant refacturable, C-09 ; total → nouvelle situation) | avoir (partiel : ne rouvre pas ; total → nouveau solde) | **[DV]** A6-10 (correction d'un avoir erroné non conçue, PT-9) |
| Supprimable | non | non | non | non |
| Source | INV-189, INV-57, modèle §3.2 | INV-190, métier §12, E-17 | INV-58, métier §13, CDC §18 | métier §14, INV-76, E-14 |

**[RD]** Une situation « atteignant 100 % n'existe pas : la facture finale est un Solde » (métier §12). **[RD]** « Une situation ne peut plus être émise dès qu'un solde actif existe, ni sur un BC annulé » (métier §12).

**[RD]/[DT] / A6-20 (VR-09, VR-12, CD-07, QO-1)** — Après un avoir total sur le **solde**, seul un **nouveau solde** est émissible : INV-58 interdit tout acompte et toute situation après un solde (lecture « même neutralisé » : niveau 2 > TR-22 niveau 3) ; E-14 et C-33 autorisent le nouveau solde. Le cas d'un acompte ou d'une situation totalement crédité(e) **alors qu'un solde existe** n'est pas couvert explicitement : **[QO]** QO-1 (§M.7).

### 4.3 Cycle de vie du BC vu par la facturation (rappel, 004/005b)

`statut ∈ {en_cours, termine, annule}` ; naissance `en_cours` caches à zéro (tr_17) ; `annule` terminal **commercial** (`tr_12_bons_commande_annule`, remplacé par la corrective 005c (livrée) pour laisser évoluer les trois caches de facturation : VR-04 à VR-06) ; jamais supprimé (tr_19) ; `termine` ⇔ `completed_at` NN. **[RD]** 004/005b (DDL réel rejoué) ; modèle §4.7. Le cycle du BC vu de la facturation (état financier dérivé ≠ réouverture commerciale) est décrit en §M.3 à §M.5.

---

## 5. Règles de numérotation

### 5.1 Règles documentées (brief §1)

| Règle | Qualif. | Source |
|---|---|---|
| Familles `ACP-00001-26` (acompte), `FAC-00001-26` (situation **et** solde, séquence partagée), `AVO-00001-26` (avoir) ; compteur 5 chiffres, année 2 chiffres, plafond 99 999 | **[RD]** | modèle §6, CDC §18–§19 |
| Année du numéro = année de `date_emission` | **[RD]** | modèle §6 |
| Un numéro définitif n'est **jamais attribué deux fois** ; un trou est accepté et jamais récupéré ; **absence de doublon > absence de trou** ; le compteur ne revient jamais en arrière | **[RD]** | INV-179, E-13, D-54, modèle §6, §11.4 |
| Mécanisme : réservation committée avant l'objet, high-water `machine.db`, `UNIQUE(numero)` dernier rempart | **[RD]** (tranché) | PT-1, modèle §11.4 |
| `numerotation_sequences` : `UNIQUE(type_objet, annee)`, types `ACP`/`FAC`/`AVO` **déjà autorisés**, `tr_95` (jamais de diminution), `tr_96` (jamais de suppression) | **[RD]** | 001 (DDL réel), 004 (tr_96), INV-22 |
| Chronologie continue ACP/FAC/AVO : `date_emission >= derniere_date` (TR-02) ; ne s'applique pas à DEV/BCD/PVR/DEP | **[RD]** | modèle §6, TR-02, INV-24 |
| Numéro immuable une fois attribué | **[RD]** | TR-01, INV-23 |
| Numéros historiques importés conservés tels quels (seule exemption de format) ; n'alimentent pas les séquences | **[RD]** | modèle §10.4, §10.6, INV-131, INV-135, D-24 |
| Pas de mécanisme parallèle | **[RD]** | brief §1 |

### 5.2 Conséquences pour 006

- **[DT]** `numerotation_sequences` n'est **pas modifiée** par 006 : les trois clés existent dans le CHECK de 001. **006 n'insère aucune ligne de séquence** (« Données dans une migration » : séquences = interdit dans une migration d'installation, conv. §5).
- **[DT]** `UNIQUE(numero)` sur `factures` couvre à lui seul la séquence FAC partagée entre situation et solde (une seule table). C'est le dernier rempart de PT-1 (modèle §11.4 point 5).
- **[DT]** Le SQL ne peut pas « attribuer » un numéro : l'attribution (réservation, high-water, plafond 99 999) est un acte de **service** (INV-25, D-30 : `machine.db` sans trigger). 006 garantit seulement forme, unicité, immuabilité, non-suppression, chronologie.
- **[DT]** Non-réutilisation en base : `tr_21_factures_no_delete` + `recursive_triggers=ON` rendent impossible la libération d'un numéro par `DELETE`/`REPLACE` ; `AUTOINCREMENT` empêche la réutilisation d'un `id`.

### 5.3 Chronologie (TR-02) — points non tranchés

**[RD]** TR-02 s'applique à `factures` INSERT : `date_emission >= derniere_date`, puis mise à jour de `derniere_date` (modèle §8).

**[DV] / A6-07 (V6-07)** — Quatre trous :
1. **Quelle clé ?** `numerotation_sequences` est indexée par `(type_objet, annee)`. Pour une facture `origine = 'v6'`, la clé se lit indifféremment dans `numero` ou dans `(type, substr(date_emission,3,2))` (F7 les rend identiques). **[PR]** Dériver la clé de `(type, date_emission)` : fonctionne aussi pour les factures importées au numéro libre.
2. **Ligne de séquence absente.** Le service (PT-1) crée toujours la ligne avant la première facture d'une clé. Mais l'import insère les factures **avant** `sequences` (modèle §10.5), tout en affirmant « TR-02 actif », puis initialise les séquences (§10.6, `derniere_date ≥ toute date_emission de la même clé`). Si le trigger crée la ligne, l'initialisation ultérieure devient un conflit sur `UNIQUE(type_objet, annee)` ; s'il ne la crée pas, TR-02 est sans effet pendant l'import. **[PR]** Option A : TR-02 ne contraint que si la ligne existe, ne crée jamais de ligne ; `derniere_date` est alors fixée par `sequences`. Option B : le trigger fait un UPSERT. À trancher avec le contrat d'import (P-04).
3. **Cross-année.** Le trigger étant par clé `(type, année)`, une facture datée 2026-12-31 peut être émise après une datée 2027-01-02 (autre clé). **[DT]** Conséquence de la définition par clé ; rien dans les sources ne la déclare problématique. À mentionner, pas à corriger.
4. **Qui écrit `derniere_date` ?** Le texte de TR-02 dit « mise à jour de `derniere_date` » (un trigger qui *écrit*), alors que le modèle §8 pose que les triggers « ne servent que là où un `CHECK` ne suffit pas » et lèvent `RAISE(ABORT, …)`, et que les triggers de 004 et 005 sont testés comme **purement gardiens** (`test_004` T-29 « les triggers ne modifient aucune donnée » ; `test_005:341` `test_T44_triggers_ne_font_que_garder`). **[PR]** Trigger de 006 = garde pure (`date_emission >= derniere_date`) ; l'écriture de `derniere_date` se fait par le **service** dans la transaction de réservation/émission, comme `dernier_numero`. Alternative : trigger `AFTER INSERT` qui écrit (conforme à la lettre de TR-02, rompt le précédent « gardien seulement »).

**[RD]** Le service borne l'année à 2001–2099 (INV-177, D-38) : **jamais un CHECK** — 006 n'ajoute donc aucune borne d'année (un test doit le vérifier, voir §17).

---

## 6. Règles financières

### 6.1 Principes monétaires (brief §2)

| Règle | Qualif. | Source |
|---|---|---|
| Aucun `REAL` : TEXT canonique contrôlé par CHECK ; D2 / D2S / DL / P2 | **[RD]** | modèle §2.3, INV-11, INV-12, INV-14, CDC §6 |
| Arithmétique SQL **uniquement en centimes entiers** `CAST(REPLACE(x,'.','') AS INTEGER)` | **[RD]** | modèle §2.3 |
| `HALF_UP` en valeur absolue (`0.125 → 0.13`, `−0.125 → −0.13`) ; **un seul arrondi par ligne** ; total = Σ lignes arrondies − remise globale arrondie | **[RD]** | modèle §3.1, C-14 → C-17, CDC §6 |
| Pourcentages saisis à 2 décimales | **[RD]** | modèle §3.1, CDC §6 |
| Négatifs autorisés **uniquement** pour `facture_lignes.montant_ht` (`deduction`) | **[RD]** | modèle §2.3, INV-62 |
| Pas de `max(0)` artificiel sur les valeurs légitimement négatives | **[RD]** (brief) | **[DT]** la somme des lignes d'un solde passe par des termes négatifs ; seules `reste_du`, `credit`, CA engagé (007+) utilisent `max(0, …)` (modèle §3.3, §3.6) |

### 6.2 Formules de facturation (modèle §3.2 ; INV-56, INV-57, INV-58)

```
facturation_nette(BC) = Σ total_ht(acomptes) + Σ total_ht(situations) + Σ total_ht(soldes) − Σ total_ht(avoirs)

situation, mode pourcentage :
  montant      = arrondi_HALF_UP(contractuel × cumul% / 100) − nette_avant
  deja_facture = nette_avant                         (montant_deja_facture_ht de la situation)
  nette_apres  = nette_avant + montant ≤ contractuel  (borne stricte ou non : V6-05)

solde : total_ht = contractuel − nette_avant        (≥ 0.00 ; 0.00 autorisé)
acompte : total_ht ≤ contractuel du devis concerné   (INV-57)
avoir : Σ avoirs(origine) ≤ total_ht(origine)         (INV-76)
```

**[DT]** La facturation nette n'a **besoin d'aucune définition d'« actif »** : une facture neutralisée par un avoir total contribue `F − avoirs(F) = 0`. Seules les règles d'**unicité**, de **reste dû** et de **`termine`** dépendent de la notion d'« actif » (PT-9). Cette observation réduit l'ambiguïté PT-9 à trois endroits précis (§15, A6-04).

**[DT]** En centimes : `nette = Σ CAST(REPLACE(total_ht,'.','') AS INTEGER)` signé selon le type ; `arrondi_HALF_UP(c × p / 10000)` en entiers vaut `(c × p × 2 + 10000) / 20000` (division entière) pour `c` en centimes et `p` en centièmes de pourcent ; pas de dépassement de 64 bits tant que `c < 10^13` centimes. **[PR]** formule à réutiliser dans trigger/test, **si** V6-13 retient le recalcul SQL de la situation en pourcentage.

### 6.3 Vecteurs chiffrés de référence (à traduire en tests)

| Cas (modèle §13) | Entrées | Attendu | Couche |
|---|---|---|---|
| C-03 | contractuel 1000.00 ; acompte 200.00 ; cumul 60 % | situation = **400.00** ; nette = 600.00 | service + TR-22 |
| C-04 | nette avant solde = 600.00 | solde = **400.00** ; `date_100_facture` = date du solde | service |
| C-08 | acompte 200.00 + situation 800.00 | **solde 0.00** autorisé ; BC non `termine` tant qu'un acompte ou une situation reste dû (007) | SQL (D2 ≥ 0) + TR-22 |
| C-09 | contractuel 1000 ; acompte 200 ; situation 400 (60 %) ; avoir 100 sur la situation | nette = 500.00 ; nouvelle situation cumul 60 % = **100.00** | service + TR-22/23 |
| C-07 | solde 400.00 impayé ; avoir 100.00 | aucun nouveau solde ; `date_100_facture` inchangée | TR-22/23 |
| C-33 | avoir total sur acompte/situation/solde ; nouvelle facture du même type | accepté ; nouveau numéro ; annulation inexistante | TR-22/23/20/21 |
| C-34 | BC à deux devis, acompte A + situation A, puis devis B rattaché avant solde | contractuel = Σ `total_ht` ; acompte distinct pour B | TR-22 (PT-10) |
| C-35 | solde émis ; devis C ; avoir total sur le solde ; nouvelle tentative | rattachement refusé dans les deux cas | service + CK-14 / `tr_99…` |
| C-36 | annulation d'un BC portant acompte payé, situations, encaissements | factures conservées ; avoir possible ; aucun nouvel acompte/situation/solde | TR-16 |
| C-37 | situation globale à deux devis, % puis montant | calcul en montants cumulés ; mode, valeur, avancement, montant HT figés | service (PT-11) |
| C-15 / C-16 | `2.5 × 10.005` ; `±0.125` | `25.01` ; `±0.13` | service (arrondi) |
| *(à ajouter, **[PR]**)* | `100.05 × 50 %` | `50.025 → 50.03` (HALF_UP ; l'arrondi bancaire donnerait `50.02`) | discrimine HALF_UP |

### 6.4 Acompte : prévu, facturé, encaissé (brief §4)

**[RD]** Trois niveaux **distincts** : acompte **prévu** dans le devis (`devis.acompte_type/valeur`, `acompte_prevu = arrondi(contractuel × pct/100)` ou montant fixe, toujours ≤ contractuel, modèle §3.1) ; **facture** d'acompte, qui peut exister sans être payée ; **règlement encaissé** (INV-189, métier §10 CDC §18). « Une facture d'acompte n'est pas un règlement » (brief) : 006 ne crée aucune notion d'encaissement.

**[DV] / V6-04** : le montant facturé doit-il être **égal** à l'acompte prévu, ou seulement **≤ `devis.total_ht`** ? Les sources donnent le plafond (INV-57, TR-22) et le « prévu » comme valeur proposée, jamais comme égalité obligatoire. **[PR]** SQL garantit seulement le plafond ; le prévu reste une proposition du service.

### 6.5 Acomptes dans le solde (brief §13)

**[RD]** Le solde ne « déduit » pas les acomptes par une règle spéciale : son `total_ht = contractuel − facturation nette avant` (modèle §3.2). Les lignes du solde conservent la trace : lignes `prestation` copiées du BC, puis lignes `deduction` « facturation nette antérieure » et « remise globale de chaque devis rattaché » (modèle §4.8, INV-62). **[DT]** Plusieurs acomptes (un par devis) sont donc pris en compte par la nette, sans traitement particulier ; les avoirs sur acompte avant solde réduisent la nette et font remonter le solde. **[DT]** Sous la lecture « solde même neutralisé » (A6-20), un avoir sur acompte émis après le solde ne permet pas de recréer d'acompte : le montant ne se refacture que par remplacement du solde.

**[DV] / A6-19** : les lignes `deduction` « facturation antérieure » sont-elles une seule ligne ou une par facture ? Le modèle dit « lignes `deduction` (facturation nette antérieure, et remise globale de chaque devis rattaché) » : le texte exige une ligne par remise de devis, **pas** le nombre de lignes pour la facturation antérieure. À préciser dans le contrat service (hors SQL, `Σ lignes = total_ht` reste le seul invariant, CK-05).

### 6.6 Avancement (brief §14)

**[RD]** `avancement` = facturation nette / contractuel (P2), **100.00 dès qu'un solde actif existe** ; mesure la facturation, jamais l'avancement physique (modèle §4.7, métier §7, INV-46). Colonnes et CHECK **déjà en 004** (`avancement` P2 0–10000 centièmes ; `date_100_facture ⇒ avancement = '100.00'`). **[DT]** 006 **ne crée aucune règle d'avancement** : il fournit la source (les factures) ; l'écriture du cache est une règle de service (INV-46) contrôlée par CK-06. La limite « 100 % » n'est portée que par la distinction situation/solde (§4.2).

**[VR]** Après un avoir, `avancement` suit sa définition (100.00 tant qu'un solde actif subsiste ; sinon facturation nette / contractuel) et s'écrit **avec** `date_100_facture` dans le même `UPDATE` (CHECK de 004). Sur un BC annulé, il évolue de la même façon (VR-05) : voir §M.6.

### 6.7 Ce que 006 ne calcule pas (reste à 007+)

`reste_du`, `absorbe`, `credit`, `etat_paiement`, `en_retard`, CA engagé, CA encaissé, URSSAF : **[RD]** modèle §3.3, §3.4, §3.6 ; aucun n'est une colonne.

---

## 7. Règles de dates (brief §10)

| Date | Existe ? | Nature | Règle | Source |
|---|---|---|---|---|
| `date_emission` | **oui**, D NN | date métier de la facture ; **date de numérotation** (donne `yy`) ; sert à TR-02 | forme `GLOB` + `date(x) IS x`, **aucune borne d'année en SQL** (INV-177/D-38 : service 2001–2099) ; `yy = substr(date_emission,3,2)` pour `origine='v6'` | **[RD]** modèle §4.8, §6, §2.2, TR-02 |
| `date_echeance` | **oui**, D (NN hors avoir, NULL pour avoir) | échéance de paiement | `>= date_emission` (CHECK) ; **= `date_emission` + délai de paiement du snapshot entreprise : règle de service** | **[RD]** §4.8, INV-59 ; modèle §14 |
| `created_at` | **oui** | horodatage technique | défaut `strftime` ; jamais métier | **[RD]** §2.2, INV-201 (principe : date métier ≠ `created_at`) |
| date de validation | **non** | — | l'émission est la validation (une transaction) | **[DT]** INV-185 |
| date de situation / date de solde | **non** | — | portées par `date_emission` de la facture concernée | **[DT]** |
| période facturée (du … au …) | **non documentée** | — | **ne pas créer** | **[DV]** absence documentaire — aucune source ne la prévoit |
| date de paiement | **hors 006** | `reglements.date_evenement` | 007 | modèle §4.9 |
| `date_100_facture` (cache du BC) | existe en 004 | = `date_emission` du **premier solde actif** ; NULL si ce solde est totalement crédité et qu'aucun autre n'est actif | service ; ne réinitialise ni ne prolonge la règle des 30 jours des dépenses (VR-13) | **[RD]** modèle §3.5, INV-43 ; **[VR]** VR-10 |
| `garanties.date_declenchement` | 008 | = `date_emission` du premier solde, immuable | — | **[RD]** modèle §4.10 |

**[DV] / V6-17** — Aucune source ne dit si `date_emission` peut être **future** ou antérieure à la date du jour (seule la chronologie TR-02 et la borne de service existent). **[PR]** Ne rien ajouter en SQL (« ne pas transformer une absence documentaire en décision implicite »). Test : accepter le passé non chronologique est refusé uniquement par TR-02.

---

## 8. Règles TVA (brief §11)

**Résultat de l'audit : BATORYA Essentiel V6 est explicitement sans TVA.**

| Point demandé | Constat | Qualif. | Source |
|---|---|---|---|
| TVA ou absence de TVA | **absence** : « n'étant pas assujettis à la TVA dans le cadre couvert par BATORYA Essentiel » ; « absence de gestion de TVA » ; `TVA` figure dans la liste de ce qui **ne fait pas partie** d'Essentiel V6 ; « absence de TVA » parmi les principes structurants | **[RD]** | CDC §1, §2 (« Ne font pas partie… »), synthèse finale ; métier en-tête (« franchise en base de TVA »), métier §10 (« Aucune TVA (franchise en base) ») |
| Montant HT | seul montant ; `total_ht` D2 ; aucun TTC | **[RD]** | modèle §4.8 (« pas de `total_ttc` »), INV-55 |
| Taux, montant de TVA, plusieurs taux, TTC | **non documentés** (volontairement absents) | **[RD]** par absence explicite | idem ; dépenses : « sans TVA ni montant TTC » (métier §18, modèle §4.12) |
| Exonération éventuelle | seule la franchise en base est citée ; pas de colonne d'exonération | **[RD]** | métier §10 |
| Précision et arrondis | ceux des montants HT (D2, HALF_UP) | **[RD]** | modèle §2.3, §3.1 |
| **Mention légale** de franchise sur la facture | **aucune source** ne dit où elle vit (le snapshot entreprise contient « mention commerciale, conditions commerciales et particulières », modèle §2.4, mais n'y affecte pas la mention de TVA) | absente | **[DV]** V6-16 — hors SQL (génération du document) |

**Modélisation retenue** — **[PR]** : *absence de colonnes* (aucune colonne `tva`, `ttc`, `taux`, `exoneration` dans `factures` ni `facture_lignes`) et un **test de structure** vérifiant cette absence, sur le modèle de `test_T44_aucune_structure_d_import_ni_de_tva_ni_de_statut` (`test_005:414`). Le brief interdit de déduire quoi que ce soit des devis ou des dépenses : les devis n'ont pas non plus de TVA, et ce n'est pas la raison invoquée ici — la source est le CDC et le modèle, pas l'analogie.

**[DT]** Il n'existe **aucune configuration** Essentiel avec TVA dans les sources : la question « comment cette réalité est-elle modélisée dans certaines configurations » n'a pas d'objet ; le CDC §2 renvoie la TVA à BATORYA Entreprise (non anticipé, brief « IMPORTANT »).

---

## 9. Règles de rattachement au BC

### 9.1 Le BC est la référence de la facturation (brief §3)

| Règle | Qualif. | Source |
|---|---|---|
| Toute facture a un `bc_id` NN ; le BC est le « dossier métier central » | **[RD]** | modèle §4.8, métier §7, CDC §15 |
| `client_id` de la facture = `client_id` du BC (contrôle à l'INSERT) | **[RD]** | TR-16, INV-48 |
| Le contractuel de la facturation est `bons_commande.montant_contractuel_ht` (= Σ `total_ht` des devis rattachés, contrôlé par CK-13) | **[RD]** | modèle §3.1, §4.7, CK-13, INV-175 |
| Les lignes du solde sont celles de `bc_lignes` ; le BC reste stable, seul l'ajout d'un devis l'augmente | **[RD]** | modèle §4.8, INV-186, INV-187 |
| La facturation **ne réécrit jamais** le contrat du BC (tr_12_bons_commande_contrat : seuls montant contractuel, caches, dates de début/fin et annulation sont modifiables) | **[RD]** | INV-186 ; 005b `tr_12_bons_commande_contrat` |

### 9.2 BC multi-devis (005b) — conséquences sur la facturation (brief §15, question 5)

| Sujet | Règle | Qualif. | Source |
|---|---|---|---|
| Niveau de facturation | **globale au niveau BC** (situation, solde) ; l'acompte seul est rattaché à son devis | **[RD]** | D-48, INV-189, INV-190, E-16, E-17 |
| Lignes issues de plusieurs devis | le solde reprend toutes les `bc_lignes` ; chaque ligne garde `devis_ligne_id` (donc son devis) | **[DT]** | 005b `bc_lignes.devis_ligne_id UNIQUE` ; modèle §4.8 |
| Remise globale | portée par chaque devis, jamais recalculée ; elle apparaît dans le solde en **une ligne `deduction` par devis** | **[RD]** | modèle §3.1, §4.8, INV-62, INV-192 |
| Acompte | un acompte **par devis** (non neutralisé) ; plafond = contractuel du devis concerné | **[RD]** principe ; **[PR]** colonne `devis_id` | D-48, INV-189, INV-57 ; PT-10 |
| Situation | globale, saisie en % ou en montant, calcul en montants cumulés, aucune double facturation | **[RD]** | E-17, INV-190, C-37 |
| Solde | global ; `contractuel − nette avant` | **[RD]** | modèle §3.2 |
| Ventilation par devis des situations / soldes | **non prévue** | **[RD]** par absence + INV-190 « globale » | — |
| Rattachement tardif d'un devis | possible tant que **aucun solde n'est rédigé/validé**, même après acompte(s) et situation(s) ; un avoir sur le solde ne rouvre pas | **[RD]** | INV-187, E-16, C-34, C-35 |
| Conservation des références historiques | `bc_devis` est immuable (`tr_99_bc_devis_no_update/no_delete`) ; `factures.devis_id` et `bc_lignes` en RESTRICT | **[RD]** 005b ; **[DT]** | INV-184 |
| Devis ajouté après un acompte d'un autre devis | l'acompte existant reste valable ; le contractuel augmente ; la situation suivante se calcule sur le nouveau contractuel | **[DT]** | C-34, C-37 |

**[DV] / V6-04** — PT-10 reste une *proposition* : colonne `factures.devis_id` (acompte seulement), un acompte non neutralisé par devis. Points non tranchés : (a) base de l'« acompte prévu » (devis `total_ht` après remise ?) ; (b) tableau d'avancement des acomptes d'un BC à plusieurs devis ; (c) rôle de `devis_id` à l'import (V2 : un seul devis par BC, rang 1).

### 9.3 États du BC et facturation (brief §16, §17, §18 ; question 12)

**Clarification préalable : « BC gelé » (brief §4, §16, §24). Décisions verrouillées VR-01 à VR-03 :**

- **[RD]** `bons_commande.statut ∈ {en_cours, termine, annule}` : la valeur **`gele` n'existe pas** (modèle §2.5 « statut BC », CHECK de 004/005b).
- **[VR]** Le gel progressif est **abandonné** (E-10 remplace E-01 ; INV-33, INV-34, INV-35 retirés le 2026-10-03). `frozen_at` est **conservée** comme marqueur technique résiduel : aucun effet sur la facturation, l'édition, le rattachement de devis, l'avoir ou l'annulation ; ses obligations techniques sont en §M.2 (O-1 à O-5).
- **[RD]** Dans les tests 004/005b, « gelé » est un **état de test** (`frozen_at` posé) : `ETATS_BC = ("en_cours","gele","termine","annule","annule_gele")` (`test_005b:78-80`, `geler_bc` l.523-525). Les tests 006 réutilisent cette matrice sans créer de statut et doivent montrer que `en_cours` et `gele` donnent les mêmes résultats (G24).
- **[RD]** La règle du brief « le BC est gelé après le premier **encaissement actif** d'un acompte, d'une situation ou d'un solde ; une facture émise non payée ne gèle pas » reprend INV-33 et INV-35 (**retirés le 2026-10-03**) et le TR-15 de la V3.12 (obsolète, modèle §7.1) : **écartée** (CD-02). Elle ne relèverait de toute façon pas de 006 (l'encaissement est 007).

**Matrice (règles documentées et décisions verrouillées) :**

| Opération | `en_cours` | `termine` | `annule` | Effet de `frozen_at` | Source / qualif. |
|---|---|---|---|---|---|
| Nouvel **acompte** | ✓ si aucun solde n'a été émis | ✗ (solde actif existe) | ✗ | aucun | **[RD]** TR-16, INV-47, INV-58, INV-188 ; **[DT]** pour `termine` (TR-22) |
| Nouvelle **situation** | ✓ si aucun solde n'a été émis | ✗ | ✗ | aucun | idem |
| Nouveau **solde** | ✓ si aucun solde actif | ✗ (solde actif) | ✗ | aucun | **[RD]** INV-58, TR-22, INV-188 |
| **Avoir** sur facture existante | ✓ | ✓ **[VR]** VR-07 | ✓ **[RD]** INV-188 | aucun | **[RD]** INV-188 ; **[VR]** VR-04, VR-07 |
| Modification / suppression / annulation d'une facture | ✗ | ✗ | ✗ | aucun | **[RD]** INV-53, INV-185 |
| Rattachement d'un devis (005b) | ✓ si aucun solde n'a été émis (**même crédité** : VR-09) | ✗ (solde existe) | ✗ (`tr_99`) | aucun (005b : « un BC gelé peut recevoir un nouveau devis ») | **[RD]** INV-187 ; **[VR]** VR-09 ; garde SQL : V6-10 |
| Nouvelle facture du **même type** après avoir total | ✓ selon §M.7 | sans objet : un BC `termine` a un solde actif ; si l'avoir neutralise le solde, le BC est redevenu `en_cours` | ✗ (pas de nouveau cycle) | aucun | **[RD]** arbitrage B, INV-188 ; **[QO]** QO-1 |
| Recalcul des caches de facturation après avoir | ✓ | ✓ | ✓ (trois caches ; `statut` reste `annule`) | aucun | **[VR]** VR-05, VR-07 |
| Réouverture commerciale | — | **jamais créée** par 006 (brief §17) ; seul le service financier recalcule l'état dérivé (INV-42) | — | — | **[RD]** INV-41, modèle §3.5 ; **[VR]** VR-08 |

**[VR] BC annulé** : voir §M.4. Les factures existantes restent intactes (immuables) ; un avoir sur un document existant est permis (INV-188, C-36) ; les trois caches de facturation continuent d'évoluer (VR-05, corrective 005c) ; `statut` reste `annule`.

**[VR] BC terminé** : voir §M.5. Un avoir est permis ; il ne rouvre pas commercialement le BC ; un avoir total qui neutralise le solde actif peut faire repasser l'**état dérivé** à `en_cours` par recalcul (INV-42), sans rattachement de devis possible (VR-09).

### 9.4 Rôle de CK-13 et CK-14 (brief §22)

| CK | État | Rôle pour 006 | Source |
|---|---|---|---|
| **CK-13** (devis ↔ BC) | existe (005b) | inchangé ; reste exécuté après import et restauration ; garantit que `montant_contractuel_ht` = Σ `total_ht` des devis, donc la **base** des formules de solde/situation | **[RD]** modèle §14, conv. §9 |
| **CK-14** (rattachement multi-devis) | existe (005b) ; la clause **« aucun devis rattaché après un solde »** n'a pas pu être testée en 005b (pas de factures) | à **compléter en test 006** par une requête sur `bc_devis` / `factures` ; **aucun nouveau CK n'est créé** | **[RD]** modèle §14 ; 005b l.37-39 ; `test_005b:2464-2474` (CK14 sans la clause) |
| CK-01, CK-02 | existent | s'appliquent à `factures.numero` (numéros uniques et conformes sauf `origine='import'` ; séquences ≥ max des numéros) | **[RD]** modèle §14 |
| CK-04, CK-05, CK-06 | existent (libellés) | **exécutables pour la première fois** avec 006 (factures sans lignes ; Σ lignes = total ; caches du BC = recalcul) | **[RD]** modèle §14 |

**[DT]** Le modèle donne les libellés CK-04/05/06 mais **pas les requêtes SQL** : comme 005b l'a fait pour CK-13/14 (constantes `CK13_*`, `CK14_*` dans le test), 006 écrira les requêtes dans son fichier de test ; ce n'est pas un nouveau CK.

---

## 10. Invariants

### 10.1 Invariants applicables à 006 (registre `invariants.md`)

| INV | Contenu (abrégé) | Couche cible pour 006 | Qualif. |
|---|---|---|---|
| INV-04 | `id` AUTOINCREMENT, jamais réutilisé ; un numéro métier n'est jamais une clé étrangère | SQL | **[RD]** |
| INV-05 | FK `RESTRICT` par défaut, aucune clause `ON UPDATE` ; aucune cascade ne supprime un historique | SQL | **[RD]** |
| INV-06 | aucune suppression physique d'un objet numéroté (ACP, FAC, AVO) ; annulation/avoir/correction métier selon l'objet | trigger | **[RD]** |
| INV-07 | `recursive_triggers=ON`, `INSERT OR REPLACE`/`REPLACE` interdits par convention | connexion + triggers de suppression | **[RD]** |
| INV-10, INV-11, INV-12, INV-13, INV-14 | dates réelles ; TEXT décimal canonique ; centimes entiers ; HALF_UP un arrondi par ligne ; négatifs limités à `facture_lignes.montant_ht` | CHECK / service | **[RD]** |
| INV-20 → INV-24 | formats V6 ; `UNIQUE(type_objet, annee)`, FAC partagée, ACP/AVO séparés ; jamais attribué deux fois, `dernier_numero` jamais diminué ni ligne supprimée ; `numero` immuable ; chronologie ACP/FAC/AVO | CHECK + trigger + service | **[RD]** |
| INV-25 | `sequence_high_water` (machine.db) ; restauration `dernier_numero := max(restauré, max_attribue)` | service | **[RD]** |
| INV-27, INV-131, INV-135, INV-136 | numéros historiques importés, aucune exemption sauf format du `numero`, séquences importées, BLOC-IMP | CHECK conditionnés par `origine`, triggers sans exemption | **[RD]** |
| INV-30 | snapshots versionnés ; le catalogue, la fiche client et les paramètres n'altèrent jamais un document existant | CHECK `json_valid` + service | **[RD]** |
| INV-32 | factures figées dès l'INSERT ; aucun brouillon persistant | trigger (TR-20) | **[RD]** |
| INV-46, INV-164 | caches du BC par un service financier unique, en un seul `UPDATE` ; ordre de recalcul | service + CK-06 + CHECK de 004 | **[RD]** |
| INV-47 | nouvel acompte/situation/solde seulement sur BC `en_cours` ; avoirs possibles sur BC annulé ; avoir sur BC `termine` **autorisé** (l'« à confirmer » est levé par VR-07) | trigger TR-16 | **[RD]** / **[VR]** |
| INV-48 | `client_id` cohérent devis / BC / factures à l'INSERT | trigger | **[RD]** |
| INV-52 | un acompte actif par devis, un solde actif par BC, une situation active par numéro ; « actif » = non entièrement neutralisé par un avoir total (VR-12) | trigger | **[RD]** principe et définition / **[PR]** mécanisme PT-9 |
| INV-53 | facture immuable, jamais supprimée ni annulée ; correction par avoir | trigger | **[RD]** |
| INV-54 | `Σ facture_lignes.montant_ht = total_ht`, sans exemption | service + CK-05 | **[RD]** |
| INV-55 | `total_ht` : acompte, situation, avoir `> 0.00` ; solde `≥ 0.00` ; aucun TTC ; pas de type `complete` | CHECK | **[RD]** |
| INV-56 | facturation nette = Σ acomptes + situations + soldes − avoirs | service (+ triggers qui la lisent) | **[RD]** |
| INV-57, INV-190 | situation globale, % ou montant, montants cumulés ; acompte ≤ contractuel du devis | trigger (bornes) + service (calcul) | **[RD]** |
| INV-58 | solde = contractuel − nette avant ; plus d'acompte/situation après solde ; avoir partiel ne rouvre pas | trigger | **[RD]** |
| INV-59 | `date_echeance` NN hors avoir, NULL pour un avoir, ≥ `date_emission` | CHECK | **[RD]** |
| INV-60 | aucun statut de facture persisté | structure | **[RD]** |
| INV-62 | composition des lignes par type ; négatifs uniquement `deduction` | CHECK + trigger (PR) + service | **[RD]** / **[DV]** V6-14 |
| INV-76, INV-78 | avoir : origine obligatoire, non avoir, même BC, motif, Σ ≤ origine ; l'avoir ne modifie jamais l'origine | CHECK + trigger | **[RD]** |
| INV-177 | borne 2001–2099 : service uniquement, jamais un CHECK | service | **[RD]** |
| INV-179 | un numéro définitif n'est jamais attribué deux fois (trou accepté) | service + `UNIQUE` | **[RD]** |
| INV-184 | une relation historique ne change jamais de cible (facture ↔ BC, avoir ↔ origine) | FK + TR-20 | **[RD]** |
| INV-185 | facture validée : pas de brouillon, une seule transaction, immuable, correction par avoir, avoir total → nouvelle facture du même type | trigger + service | **[RD]** |
| INV-186 | le contrat du BC n'est jamais réécrit par la facturation | triggers de 005b (déjà en place) | **[RD]** |
| INV-187 | rattachement d'un devis tant qu'aucun solde n'est rédigé/validé ; un avoir sur le solde ne rouvre pas | service + CK-14 (+ trigger PR) | **[RD]** |
| INV-188 | BC annulé : factures, avoirs conservés ; pas de nouvel acompte/situation/solde/devis ; avoirs possibles | trigger TR-16 | **[RD]** |
| INV-189 | acompte : prévu / facture / règlement ; chaque devis peut avoir son acompte | CHECK + trigger (PT-10) | **[RD]** / **[PR]** |
| INV-42, INV-43 | `termine` ⇔ solde actif ∧ Σ reste dû hors avoir = 0 ; `date_100_facture` = date d'émission du premier solde actif, conservée par avoir partiel | service + CK-06 | **[RD]** ; sort après avoir total : **[VR]** VR-10 |
| INV-44, INV-173 | annulation possible quel que soit l'état de facturation ; BC annulé terminal : `updated_at` et corrections de documents existants (avoirs) seulement | trigger `tr_12_bons_commande_annule` (remplacé par 005c) | **[RD]** ; **[VR]** VR-04 à VR-06 |

### 10.2 Invariants hors 006 (portés par 007+) ou retirés

- **007** : INV-70 → INV-75, INV-79, INV-80 (règlements, reste dû, crédit) ; TR-30 → TR-33. **008** : INV-85 → INV-90 (garanties). **Dérivés** : INV-60 (états), INV-72–74.
- **Retirés le 2026-10-03** (journal des invariants) : INV-33, INV-34, INV-35 (gel progressif, E-10), INV-49 (rattachement de client, E-12), INV-61 (annulation de facture, E-14), INV-77 (annulation d'avoir, E-14). **006 ne doit en reprendre aucun.**
- **`frozen_at`** : conservée à titre résiduel technique (VR-02) ; son maintien ne rétablit aucun des invariants retirés ci-dessus (§M.2).
- **Exécution / remise au prorata** : INV-191, INV-192 — « À CONCEVOIR » (PT-12, PT-13) : **rien n'est créé** en 006.

---

## 11. Répartition SQL / triggers / services / CK (brief §22)

Principe appliqué (conv. §9, §8) : *structure → SQL ; protection d'immuabilité et plafonds locaux calculables par ensembles → trigger ; cohérence inter-tables de diagnostic → CK ; orchestration, calculs dérivés, attribution de numéro → service.* « Un contrôle qui compare des lignes de plusieurs tables n'est jamais un CHECK ni un trigger de miroir » (conv. §9).

| # | Règle | CHECK / FK / UNIQUE | Trigger | Service | CK |
|---|---|---|---|---|---|
| 1 | types fermés `acompte/situation/solde/avoir` | ✓ | | | |
| 2 | colonnes propres à un type (avoir ⇒ origine+motif ; situation ⇒ ses 6 colonnes ; acompte ⇒ `devis_id`) | ✓ | | | |
| 3 | format, préfixe et année du `numero` (v6) | ✓ | | | CK-01 |
| 4 | unicité du `numero` | ✓ UNIQUE | | | CK-01 |
| 5 | attribution du numéro (réservation, high-water, plafond 99 999) | | | ✓ (PT-1) | CK-02 |
| 6 | chronologie `date_emission >= derniere_date` | | ✓ TR-02 | | |
| 7 | immuabilité de `factures` (aucun UPDATE) | | ✓ | | |
| 8 | immuabilité de `facture_lignes` (aucun UPDATE) | | ✓ | | |
| 9 | non-suppression `factures` / `facture_lignes`, y compris `REPLACE` | ✓ FK RESTRICT entrantes | ✓ | (convention : pas de `REPLACE`) | |
| 10 | familles de montants D2 / D2S / DL / P2 | ✓ | | | |
| 11 | `total_ht > 0.00` sauf solde (`≥ 0`) | ✓ | | | |
| 12 | négatif uniquement pour `deduction` | ✓ | | | |
| 13 | `date_echeance >= date_emission` | ✓ | | | |
| 14 | `date_echeance = date_emission + délai` | | | ✓ | |
| 15 | dates valides (forme + calendrier), sans borne d'année | ✓ | | ✓ borne 2001–2099 | |
| 16 | `Σ facture_lignes = total_ht` | | | ✓ à l'émission | CK-05 |
| 17 | toute facture a des lignes | | | ✓ | CK-04 |
| 18 | composition des lignes par type de facture | ✓ (`type_ligne`/signe) | ✓ **[PR]** V6-14 | ✓ | CK-05 |
| 19 | calcul du montant de ligne (un arrondi HALF_UP) | | | ✓ | CK-05 (somme seulement) |
| 20 | `bc_ligne_id` appartient au BC de la facture | ✓ FK | ✓ **[PR]** | | |
| 21 | BC `en_cours`/non annulé pour acompte/situation/solde | | ✓ TR-16 | ✓ | |
| 22 | `client_id` = client du BC | | ✓ TR-16 | | CK-13 (côté devis) |
| 23 | avoir autorisé sur BC annulé **et** sur BC `termine` (acompte/situation/solde : BC `en_cours`) | | ✓ TR-16 (VR-04, VR-07) | | |
| 24 | acompte : devis rattaché au BC, plafond `devis.total_ht`, un acompte non neutralisé par devis | ✓ FK `devis_id` | ✓ TR-22 **[PR]** | ✓ | |
| 25 | un solde non neutralisé par BC ; pas d'acompte/situation si un solde existe | | ✓ TR-22 | ✓ | |
| 26 | une situation non neutralisée par `situation_numero` | | ✓ TR-22 | ✓ | |
| 27 | situation : `montant_deja = nette avant` ; nette après ≤ contractuel | | ✓ TR-22 | ✓ | |
| 28 | situation : montant = `arrondi(contractuel × % / 100) − nette avant` (calcul) | | ✓ ou service **[DV]** V6-13 | ✓ | |
| 29 | solde : `total_ht = contractuel − nette avant` | | ✓ TR-22 **[DV]** V6-13 | ✓ | |
| 30 | avoir : origine non avoir, même BC, Σ avoirs ≤ origine | ✓ F2 | ✓ TR-23 | | |
| 31 | avoir total → nouvelle facture du même type | | ✓ (via 24–26) | ✓ | |
| 32 | caches du BC (`montant_deja_facture_ht`, `avancement`, `date_100_facture`, `statut`, `completed_at`) ; **sur BC annulé : trois caches évolutifs, `statut` et `completed_at` figés** (VR-05) | ✓ CHECK 004 | ✓ `tr_12_bons_commande_annule` **remplacé par 005c** | ✓ un seul `UPDATE` | CK-06 |
| 33 | `date_100_facture` = date du premier solde actif (NULL si ce solde est totalement crédité et qu'aucun autre n'est actif : VR-10) | | | ✓ | CK-06 |
| 34 | création des garanties au solde | | | ✓ (008) | CK-07 (008) |
| 35 | aucun devis rattaché après un solde | | ✓ **[PR]** V6-10 | ✓ | CK-14 |
| 36 | cohérence devis ↔ BC | | triggers 005b | ✓ | CK-13 |
| 37 | snapshots JSON valides ; contenu | ✓ `json_valid` | | ✓ | |
| 38 | BLOC-IMP (`origine`, `legacy_*`) | ✓ | | | |
| 39 | numéro importé libre mais non vide, unique, immuable | ✓ (CHECK conditionné) | ✓ TR-20 | | CK-01 |
| 40 | absence de TVA / TTC / statut / annulation | structure (aucune colonne) | | | |
| 41 | reste dû, absorbe, crédit, états de paiement, `en_retard` | | | dérivé | (007) |
| 42 | événements d'historique | | | `historique` n'existe pas | |
| 43 | `frozen_at` : pose conjointe avec la première `date_100_facture` ou le premier `termine` (O-1), irréversible, sans effet métier | ✓ CHECK 004 | ✓ `tr_14` (existant) | ✓ contrat du service | |
| 44 | règle des 30 jours des dépenses (lit `bons_commande.date_100_facture`) | | | ✓ Dépenses (INV-103) ; **non** 006 | |

**Ce qui n'est volontairement pas un trigger** (brief : « ne pas transformer une règle complexe en trigger uniquement parce que SQLite le permet ») : reste dû et `termine` (dérivés, dépendent de 007) ; création des garanties ; recalcul des caches ; contrôle `Σ lignes = total` (impossible en fin de transaction) ; délai d'échéance ; borne d'année ; attribution du numéro.

**Limite structurelle documentée** : l'insertion de lignes dans une facture déjà émise, **hors transaction d'émission**, n'est pas empêchable par SQLite ; elle est détectée par CK-05 (et CK-04) (modèle §14, dernière ligne du tableau). **[RD]** Il serait possible d'ajouter une garde heuristique ; ce n'est pas proposé (V6-14).

---

## 12. Import V2 → V6 (brief §20)

**Chaîne officielle inchangée** : V2 → convertisseur externe → `import-v6.json` → importeur V6 strict → SQLite V6 (modèle §10.1, D-21). V6 ne lit jamais la V2 ; le schéma n'est pas adapté à la V2.

| Question du brief | Réponse | Qualif. | Source |
|---|---|---|---|
| Les factures peuvent-elles figurer dans `import-v6.json` ? | **Oui** : bloc `factures` **avec `lignes`**, et `reglements` ; sont citées « factures (acompte, situation, solde, avoir) » | **[RD]** | modèle §10.3, §10.4 |
| Colonnes d'import à ajouter | **uniquement BLOC-IMP** sur `factures` : `origine`, `legacy_id` (= `ref` du fichier), `legacy_data` ; **pas** de `legacy_numero` (réservé à `clients` et `bons_commande`) ; **aucun** BLOC-IMP sur `facture_lignes` | **[RD]** | modèle §2.4, D-23, INV-136 |
| `migration_rapports`, `migration_id` | n'existent plus ; trace = événement `import` de `historique` (table future) et `import_anomalies` | **[RD]** | D-22, D-23 |
| Champs importables | faits saisis : type, `numero` historique, références (BC, client, devis d'un acompte, facture d'origine d'un avoir) par `ref`, snapshots complets (obligatoires), objet, `date_emission`, `date_echeance`, `total_ht`, champs de situation, `motif_avoir`, lignes | **[RD]** (principe) ; détail = **P-04 non écrit** | modèle §10.3 |
| Champs obligatoires | toutes les colonnes `NOT NULL` ; BLOC-SNAP obligatoire | **[RD]** | modèle §10.3 |
| Champs **jamais lus** (recalculés) | caches du BC (`statut`, `avancement`, `montant_deja_facture_ht`, `date_100_facture`, `completed_at`), `frozen_at` (résiduel, VR-02), états dérivés, garanties | **[RD]** | modèle §10.1, INV-169 |
| Exemption de règle pour l'import | **une seule** : format/préfixe/année du `numero` historique ; tout le reste est appliqué (échéance, Σ lignes, plafonds, chronologie, unicités) | **[RD]** | modèle §10.4, D-24, INV-131 |
| Ordre d'insertion | BC (inséré `en_cours`) → factures par `date_emission` puis `ref` croissants (TR-02 actif) → règlements ; un BC annulé s'insère `en_cours`, reçoit ses factures, puis est annulé | **[RD]** | modèle §10.5 |
| Anomalies | facture V2 sans statut : importée **non réglée**, comptée dans la facturation, le reste dû, le CA engagé ; listée « À vérifier » (`import_anomalies` `a_verifier`) ; donnée non représentable : `non_importe` | **[RD]** | D-19, modèle §10.7 |
| Facture V2 « annulée » | représentée par la facture **et un avoir total** ; contrat à écrire | **[RD]** principe ; **[DV]** détail | PT-19 |

**Conséquences pour 006 :**

- **[DT]** 006 n'ajoute ni table ni colonne d'import au-delà de BLOC-IMP ; les triggers TR-02/16/22/23/20/21 s'appliquent aux lignes importées (aucun drapeau de session).
- **[DT]** Une facture importée au numéro libre : `UNIQUE(numero)` et non-vide seulement. Elle n'alimente **pas** les séquences (modèle §10.6).
- **[DV] / A6-15 / V6-15** (contrat P-04 à écrire — ce sont des questions **posées au contrat**, pas des colonnes proposées) :
  1. `devis_id` d'un acompte importé (V2 : un seul devis par BC, lien de rang 1) ;
  2. champs de situation importés (`situation_mode`, `situation_valeur_saisie`) dépendent de PT-11 ;
  3. `montant_deja_facture_ht` d'une situation importée : fait fourni, mais le trigger le vérifie (facture insérée dans l'ordre chronologique) ;
  4. clé TR-02 et ligne de séquence absente à l'insertion (A6-07) ;
  5. avoir total d'une facture V2 annulée : `date_emission`, `motif_avoir`, numéro (historique libre ?) ;
  6. valeur de `created_at` des lignes importées (non précisée par les sources).
- **[RD]** Contrôles de fin d'import : Σ `total_ht` des factures actives et Σ `reste_du` attendu comparés (CK-12) ; échec de CK-01 → CK-13 annule l'import (modèle §10.8). `reste_du` relève de 007 : CK-12 est complet seulement avec 007.

---

## 13. Sauvegarde / restauration (brief §21)

| Sujet | Règle | Qualif. | Source |
|---|---|---|---|
| Contenu d'une sauvegarde | copie cohérente de la **seule** base métier (API Backup / `VACUUM INTO`) ; `machine.db` n'y est jamais ; donc `factures` et `facture_lignes` sont sauvegardées avec le reste | **[RD]** | modèle §11.1, INV-02 |
| Ce qui est recalculé après restauration | caches du BC et états dérivés (service financier) ; contrôlés par CK-06 | **[RD]** | modèle §3.7, §14 |
| Ce qui n'est **jamais restauré depuis `machine.db`** | `machine.db` n'est ni sauvegardée ni écrasée ; `sequence_high_water` y vit et protège les numéros émis | **[RD]** | INV-02, INV-25, modèle §5, §11.4 |
| Séquences | `dernier_numero := max(restauré, max_attribue)` ; avertissement listant les numéros consommés absents de la sauvegarde ; C-18 : FAC-00007-26 émise, base restaurée à 00005 → compteur 7, prochain `00008` | **[RD]** | modèle §11.2, §11.4, C-18 |
| Restauration d'une sauvegarde plus ancienne | refus si `user_version > N` ; sinon migrations `k+1 … N` appliquées dans l'ordre : une base de rang ≤ 7 reçoit 006 comme une installation (tables vides) | **[RD]** | modèle §11.2, conv. §5 |
| Contrôles post-restauration | CK du §14 ; **échec de la restauration si un contrôle d'intégrité obligatoire ou CK-13 échoue** (sauvegarde de sécurité) | **[RD]** | modèle §11.2, conv. §9 |
| Limite irréductible | base métier restaurée plus ancienne **et** `machine.db` perdue : doublon possible sur les numéros postérieurs ; avertissement, `h := max(h, c, plus grand numéro présent)` | **[RD]** (acceptée) | modèle §11.4 point 5 |

- **[DT]** 006 n'exige **aucun mécanisme spécifique** de sauvegarde ou de restauration (brief : « ne pas créer de mécanisme spécifique si les conventions générales suffisent »). Il ajoute seulement des tables qui participent à la copie et des triggers qui se recréent avec la chaîne de migrations.
- **[DT]** `derniere_date` (TR-02) est restaurée avec la base : après restauration d'une base plus ancienne, la chronologie ne protège que jusqu'à la date restaurée — conséquence normale de la restauration (les factures postérieures n'existent plus).
- **[DV] / A6-26 (V6-12)** — Les sources ne disent **pas** si un échec de CK-04, CK-05 ou CK-06 (devenus exécutables avec 006) rend la restauration « échouée » (seuls l'intégrité et CK-13 le font, modèle §11.2, conv. §9). Ne pas l'étendre sans décision.
- **[RD]** PDF des factures = `documents` (table future) hors base : « non localisables » si la racine est inconnue (modèle §11.3) ; hors 006.

---

## 14. Compatibilité avec 001–005b (brief §25)

### 14.1 Méthode

Chaîne rejouée (§0.2) ; DDL réel des 79 objets de rang 7 lu ; tests T-44/T-45/T-46 lus ; assertions sensibles à l'ajout d'un rang recensées.

### 14.2 Compatibilité par migration

| Migration | Objets dont 006 dépend | Impact de 006 | Verdict |
|---|---|---|---|
| **001** | `numerotation_sequences` (types `ACP`/`FAC`/`AVO`, `tr_95`, `tr_96` [posé en 004]), `clients` (FK) | aucune modification ; aucune ligne de séquence insérée | ✓ compatible |
| **002** | — | aucun | ✓ |
| **003** | `devis` (FK `devis_id` d'un acompte ; `acompte_*`, `total_ht`) ; `tr_14_devis_frozen_at` | aucune modification | ✓ ; `frozen_at` : voir VR-02, §M.2 |
| **004 / 005b** | `bons_commande` (FK, caches, CHECK `frozen_at`), `bc_lignes` (FK `bc_ligne_id`), `bc_devis`, triggers `tr_12_*`, `tr_13_*`, `tr_14_*`, `tr_17`, `tr_18`, `tr_19`, `tr_99_*` | lecture des caches ; écriture des caches par le **service** | ⚠ **un remplacement de trigger (005c) et des constats** (ci-dessous) |
| **005** | `depenses.bc_id` | aucun lien avec les factures ; numérotation DEP indépendante | ✓ |
| **005a** | `devis_revisions` | aucun | ✓ |
| **005c** *(corrective livrée, rang 8)* | remplace `tr_12_bons_commande_annule` ; ne crée ni ne supprime aucun objet nommé | 006 passe au rang 9 | ✓ prérequis de 006 (§M.8) |

### 14.3 Incompatibilités ou blocages réels (format imposé : identifier / migration / règle / correction séparée)

**I-1 — CHECK `frozen_at` de `bons_commande` : obligation de service, pas de blocage SQL (VR-01 à VR-03)**
1. *Identification* : `CHECK (statut <> 'termine' OR frozen_at IS NOT NULL)` et `CHECK (date_100_facture IS NULL OR frozen_at IS NOT NULL)` (DDL de `bons_commande`, rang 7).
2. *Migration responsable* : `004_bons_commande.sql`, conservés « tels quels » par `005b` (en-tête l.30-31, PT-8 conservateur ; 005a l.205, l.419 : « PT-8 ouvert »).
3. *Règle concernée* : INV-46 (« la condition “gelé” des CHECK actuels dépend de PT-8 »), modèle §4.7 l.437, §7.1 ; E-10 ; **[VR]** VR-01 à VR-03.
4. *Effet* : le service financier doit poser `frozen_at` dans le **même** `UPDATE` que la première `date_100_facture` ou le premier `termine` (O-1) ; rien d'autre n'écrit `frozen_at` (TR-15 n'a jamais été créé). Aucun objet de 006 n'est bloqué.
5. *Correction* : **aucune migration** (VR-02). Les obligations O-1 à O-5 (§M.2) sont consignées au contrat du service ; ce ne sont pas des règles métier.

**I-2 — `tr_12_bons_commande_annule` verrouille les caches d'un BC annulé : corrigé par la corrective 005c (VR-05, VR-06)**
1. *Identification* : trigger `BEFORE UPDATE` à `WHEN OLD.statut = 'annule'` refusant toute modification de `montant_deja_facture_ht`, `avancement`, `date_100_facture`, `statut`, `completed_at`, etc. (`INV-173: bon de commande annule terminal, seul updated_at est modifiable`).
2. *Migration responsable* : `004`, réécrit par `005b`.
3. *Règle concernée* : INV-173, INV-188 (avoirs possibles sur un BC annulé) + PT-16 ; modèle §7.2 (« caches recalculables après avoir sur document existant ») ; **005b a explicitement reporté PT-16 à la tranche Facturation** (`005b_bc_multi_devis.sql` l.26-27, Q-C ; l.352).
4. *Effet* : sans correction, le recalcul de `montant_deja_facture_ht`/`avancement`/`date_100_facture` après un avoir sur un BC annulé est impossible ; CK-06 signalerait un écart permanent.
5. *Correction séparée* **[VR]** : corrective **005c**, remplacement ciblé du trigger (§M.8), sans reconstruction de table.

**I-3 — Avoir sur BC `termine` (TR-16 / PT-16) : levé (VR-07)** (décision, pas défaut de SQL)
Règle d'origine : INV-47 « l'existant le refuse (TR-16), à confirmer au regard du CDC §22 ». Résolution : avoir autorisé ; TR-16 n'existe pas dans le SQL et est créé sans ce refus (A6-12, CD-04).

**I-4 — Ajout d'un trigger sur `bc_devis` (CK-14 « après solde ») : règle fixée, couche ouverte** (optionnel)
`tr_99_bc_devis_insert` (005b) ne connaît pas les factures ; **[PR]** ajouter un **nouveau** trigger `BEFORE INSERT ON bc_devis` plutôt que réécrire celui de 005b (aucune modification des objets existants). La règle (aucun devis après un solde, même crédité) est **verrouillée** (VR-09) ; seule la couche reste ouverte : V6-10.

### 14.4 Assertions de tests existants sensibles à l'ajout des rangs 8 (005c) et 9 (006)

| Test | Assertion | Verdict avec 006 |
|---|---|---|
| `test_005a:604`, `test_005b:755` | `sorted(MIGRATIONS.glob("*.sql"))[:6]` / `[:7]` == `NOMS` | ✓ — tranche volontaire ; `005c_…` se trie **après** `005b_…` (`'5b' < '5c'`) et `006_facturation.sql` après `005c_…` (`'5' < '6'`), hors des 6/7 premiers |
| `test_003:273`, `test_004:480,1702`, `test_005:374` | `factures`, `facture_lignes`, `reglements`… absents | ✓ — ces tests rejouent des chaînes **tronquées à leur rang** (`SQL_001…SQL_004`, `NOMS` de 7 fichiers) |
| `test_005b` (`TABLES_RANG7`, `TRIGGERS_*`, comptes exacts d'objets) | égalité d'ensembles sur la chaîne de 7 fichiers | ✓ — chaîne tronquée à 7 |
| `test_005:372-377` (`SQL_005` sans référence aux tranches suivantes) | analyse du texte de `005_depenses.sql` | ✓ — le fichier 005 n'est pas modifié |

**[DT]** La suite cumulative (694 tests) reste verte par construction tant qu'**aucun fichier 001–005b n'est modifié** ; 005c (rang 8) et 006 (rang 9) ne réécrivent ni migration ni test existants (brief §25). Le passage de 006 au rang 9 ne change pas ces assertions (les tests 005a/005b tronquent la chaîne à leur rang) ; le tableau de rangs du modèle (§17.1), D-55 et les conventions devront être alignés (§M.8).

### 14.5 Ce que le futur test 006 doit prouver (non-régression)

Chaîne 001 → 006 (rang 9, 005c incluse) : `integrity_check = ok`, `foreign_key_check` vide ; ensembles de tables/triggers/index du **rang 8** (rang 7 + 005c, qui ne crée ni ne supprime aucun objet nommé) inchangés + objets de 006 ; DDL des tables existantes identique octet pour octet ; seul `tr_12_bons_commande_annule` diffère de son DDL de rang 7 (remplacé par 005c, testé en 005c) ; 004/005b (`tr_12_contrat`, `tr_13_*`, `tr_17`, `tr_18`, `tr_19`, `tr_99_*`) toujours effectifs ; CK-13 et CK-14 (clauses de 005b) toujours vides sur des données cohérentes, y compris avec factures.

---

## 15. Points ambigus ou contradictoires (brief §29)

Format de chaque point : **sources en tension** (document + section) → **nature** → **hiérarchie applicable** → **résolution proposée [PR]** → **statut**. La hiérarchie de référence est : décisions validées / invariants / modèle SQLite validé / modèle métier / conventions → CDC. Aucune source n'est modifiée.

### A6-00 — Documentation officielle (`docs/`, V3.12) vs V3.13 (`fichiers-a-relire/MAJ__*`)
- *Sources* : `docs/` (V3.12, README de cette époque) vs `MAJ__modèle-données…v3.13`, `MAJ__invariants`, `MAJ__cdc-errata`, etc. ; chemins `docs/conception/…` cités par le brief inexistants.
- *Nature* : écart de version documentaire, pas contradiction de règle.
- *Hiérarchie* : les décisions D-40 → D-55 et les errata E-10 → E-20 sont celles que 005a/005b ont implémentées ; le présent cadrage les suit.
- *Résolution [PR]* : intégrer ou confirmer la V3.13 comme référence avant de figer le SQL 006. *Statut* : **ouvert (V6-18)**.

### A6-01 — « BC gelé » : le brief, le modèle V3.13 et les CHECK de 004 ne disaient pas la même chose — **résolu (VR-01 à VR-03)**
- *Sources en tension* : brief §4 (« Le BC est gelé après le premier **encaissement actif** d'un acompte, d'une situation ou d'un solde ; une facture d'acompte émise mais non payée ne gèle pas »), brief §16, §24, rappel 005b (« Un BC gelé peut recevoir un nouveau devis ») **vs** journal des invariants (INV-33 et INV-35 **retirés le 2026-10-03**, E-10), métier §9 (« Aucun document n'évolue par un “gel” progressif »), modèle §7.1 (PT-8 : « choix non fait »), modèle §2.5 (`statut` BC = 3 valeurs, **pas de `gele`**), DDL de 004/005b (`frozen_at` conservé, CHECK `termine ⇒ frozen_at`, `date_100_facture ⇒ frozen_at`), 005b l.30-31 et Q-B (« frozen_at ne ferme pas le rattachement »).
- *Nature* : le brief reprenait une règle **retirée** (variante de l'ancien TR-15), sans décision postérieure qui la rétablisse ; elle était de plus **incompatible** avec les CHECK de `bons_commande` (un solde émis non encaissé, cas C-08, ne pourrait pas poser `date_100_facture`).
- *Hiérarchie* : décisions validées et invariants (E-10, journal) > énoncé de brief non repris dans le registre (niveaux 1, 2, 5).
- *Résolution [VR]* : **gel progressif abandonné ; `frozen_at` conservée à titre résiduel technique ; obligations O-1 à O-5 documentées** (§M.2). Écartées : (a) suppression de la colonne (reconstruction de `bons_commande` et `devis` non exigée par une règle validée) ; (b1) pose à l'émission de la première facture et (b2) pose au premier encaissement (elles donneraient à la colonne un sens métier que VR-02 interdit).
- *Statut* : **verrouillé**. Aucun objet de 006 ne dépend de `frozen_at`.

### A6-02 — Caches d'un BC annulé : le trigger SQL était plus strict que l'invariant — **résolu (VR-04 à VR-06)**
- *Sources* : `tr_12_bons_commande_annule` (004/005b : « seul updated_at est modifiable ») **vs** INV-173 (« seules évolutions : `updated_at` et les opérations de correction de documents existants (avoirs) »), INV-188, modèle §7.2 (ligne BC annulé : « caches recalculables après avoir sur document existant (PT-16) »), TR-12 « à adapter (PT-6, PT-16) ».
- *Nature* : contradiction **SQL vs invariant** (CD-03).
- *Hiérarchie* : invariant et décision (INV-173, INV-188) > implémentation SQL (niveau 7).
- *Résolution [VR]* : option A retenue, portée par la corrective **005c** : remplacement de `tr_12_bons_commande_annule` qui autorise `montant_deja_facture_ht`, `avancement`, `date_100_facture` et garde `statut`, `completed_at`, `cancelled_at`, `motif_annulation`, `frozen_at`, contrat et snapshots immuables (§M.8). Option B (caches figés à la date d'annulation) écartée : un BC annulé n'est pas figé financièrement.
- *Statut* : **verrouillé**.

### A6-03 — Un avoir peut-il ramener un BC de `termine` à `en_cours` ? — **résolu (VR-07, VR-08)**
- *Sources* : métier §7 l.272 (« Le BC repasse En cours si un règlement est annulé **ou si un avoir intervient** et que la condition n'est plus remplie ») ; CDC §16 texte d'origine (« Une annulation de règlement ou d'avoir peut faire revenir le BC à En cours ») **vs** CDC §16 amendement E-14/E-16 (« Un avoir n'étant pas annulable, **seule l'annulation d'un règlement** peut ramener le BC à En cours ») ; modèle §3.5 (« Passage `termine → en_cours` (annulation d'un règlement) ») ; 005b en-tête l.37-40 ; brief §6 et §17 (« Un avoir ne doit pas rouvrir automatiquement un BC »).
- *Nature* : vocabulaire ambigu : « rouvrir » vise tantôt le **rattachement de devis** (INV-187), tantôt le **statut** `termine → en_cours` (CD-05, CD-10).
- *Analyse [DT]* : `termine ⇔ solde actif ∧ Σ reste_du = 0` (INV-42). Un avoir ne peut ramener le BC à `en_cours` **que s'il neutralise le solde actif** ; un avoir partiel, ou sur un acompte ou une situation, ne change pas `termine`.
- *Hiérarchie* : INV-42 (niveau 2) et modèle §3.5 > texte du CDC ; métier §7 (niveau 4) > CDC §16 sur ce point.
- *Résolution [VR]* : aucune règle de **réouverture commerciale** ; le statut est le résultat de la formule INV-42 recalculée par le service ; un avoir total qui neutralise le solde actif peut faire passer l'**état dérivé** à `en_cours`, sans rattachement de devis possible (axes 1 et 2 : §M.3 ; cas A à D : §M.5).
- *Statut* : **verrouillé**.

### A6-04 — « Actif » / « entièrement créditée » (PT-9) — **définition verrouillée (VR-12)**
- *Sources* : INV-52 (« “actif” = non entièrement neutralisé par un avoir total (E-14) », énoncé comme règle) **vs** modèle §3.2, §3.4, §3.5, §4.8 (« la notion d'“actif” éventuellement conservée … est une **proposition** (PT-9) »), INV-42, INV-43, INV-56, INV-72, modèle §19 intro.
- *Nature* : un invariant énonce la définition que le modèle déclare encore proposition (CD-06).
- *Analyse [DT]* : la **facturation nette n'en dépend pas** (§6.2). « Actif » ne sert qu'à (i) l'**unicité** d'acompte/solde/situation, (ii) `date_100_facture`/`termine`, (iii) `reste_du` (007).
- *Résolution* : **[VR]** « actif » = non totalement absorbé par les avoirs rattachés (lecture **cumulative** : plusieurs avoirs partiels peuvent neutraliser une facture), sans mécanisme de statut supplémentaire ; **[PR]** formule dérivée des données `neutralisee(F)` ⇔ `F.type <> 'avoir'` ∧ `F.total_ht > 0.00` ∧ `Σ avoirs(F) = F.total_ht`.
- *Statut* : définition **verrouillée** ; mécanisme technique : V6-02 (résiduel) ; solde `0.00` : QO-2.

### A6-05 — Mécanisme d'unicité sans `cancelled_at`
- *Sources* : modèle §4.8 « Unicité » et §8 « index uniques » (obsolètes, remplacement : PT-9) ; INV-52 (couche « SVC, TRG (PT-9) »).
- *Résolution [PR]* : triggers `BEFORE INSERT` ensembliste (`EXISTS` sur les factures du même BC / même `devis_id` / même `situation_numero` non neutralisées) ; un index partiel ne peut pas exprimer un état dérivé. Aucune concurrence à craindre : une écriture SQLite est sérialisée et le numéro est réservé sous `BEGIN IMMEDIATE`. *Statut* : suit V6-02.

### A6-06 — Sort de `date_100_facture` après avoir total sur le solde puis nouveau solde — **résolu (VR-10, VR-13)**
- *Sources* : modèle §3.5 (« sort … À CONCEVOIR (PT-9) ») ; INV-43 (« sort en cas d'avoir total sur le solde : PT-9 ») ; DDL de 004 (`CHECK (date_100_facture IS NULL OR avancement = '100.00')`) ; modèle §3.5 (`date_100_facture` ≠ `garanties.date_declenchement`, divergence voulue).
- *Analyse [DT]* : tant que le solde est totalement crédité, il n'y a plus de « solde actif », donc `avancement` < 100.00 ; le CHECK de 004 **impose** alors `date_100_facture = NULL` (dans le même `UPDATE`). À l'émission du nouveau solde, la formule documentée (« date d'émission du premier solde **actif** ») donne la date du *nouveau* solde ; `garanties.date_declenchement` garde la première date.
- *Conséquence, rectifiée* : la règle des 30 jours des dépenses (D-31, INV-103, INV-199) est une règle de **service Dépenses** qui lit `bons_commande.date_100_facture` à l'instant du rattachement. 006 **ne l'implémente pas, ne la réinitialise pas, ne la prolonge pas.** La version antérieure de ce paragraphe écrivait qu'un nouveau solde « redémarre » la fenêtre : formulation retirée (CD-01, §M.10). Aucune colonne `fournisseurs.date_100_facture` n'existe.
- *Résolution [VR]* : appliquer la formule telle quelle (VR-10). *Statut* : **verrouillé**.

### A6-07 — TR-02 : clé, ligne de séquence absente, cross-année, qui écrit `derniere_date`
Voir §5.3 (quatre points). *Statut* : ouvert (V6-07).

### A6-08 — Mention légale de franchise de TVA
Aucune source ne dit où elle se trouve (hors snapshots/colonnes). Voir §8. *Statut* : ouvert (V6-16), hors SQL.

### A6-09 — « Facture corrective », « document correctif »
Voir §1.2. *Statut* : ouvert (V6-08). *[PR]* l'avoir est le seul document correctif.

### A6-10 — Correction d'un avoir erroné ; « avoir total » = un avoir ou un cumul ?
- *Sources* : métier §14 (« la correction d'un avoir erroné est à concevoir (PT-9) ») ; INV-76 et modèle §3.3 (« Σ avoirs actifs ≤ M ») ; arbitrage B et INV-185 (« un **avoir total** … ») ; TR-23 (« avoir sur avoir interdit »).
- *Analyse [DT]* : plusieurs avoirs partiels peuvent s'additionner jusqu'à `M` ; le texte parle d'« un avoir total » au singulier. Les deux lectures (avoir unique = montant de l'origine ; ou Σ avoirs = montant) ne diffèrent que si l'on cumule des partiels. *[PR]* retenir la lecture **cumulative** (`Σ avoirs = total_ht`) : la lecture « avoir unique » laisserait une facture entièrement créditée par trois avoirs *non remplaçable*, sans raison documentée. Pour l'avoir erroné : aucun mécanisme n'existe (pas d'annulation d'avoir, pas d'avoir sur avoir) ; si l'avoir était total, la nouvelle facture du même type en reproduit l'effet ; **s'il était partiel, aucune correction n'est documentée**. Ne pas inventer de chaîne de correction (brief §7). *Statut* : lecture cumulative **verrouillée** (VR-12, « avoirs … qui lui sont rattachés ») ; correction d'un avoir partiel erroné : **non conçue**, aucune règle inventée (V6-08).

### A6-11 — Frontière 006 / 007 pour `termine` et CK-06
CK-06 (« caches BC = recalcul ») n'est complet qu'avec 007 pour `statut`/`completed_at` (dépendent des encaissements). En 006, il ne peut contrôler que `montant_deja_facture_ht`, `avancement`, `date_100_facture` et le cas particulier `termine` par absorption d'avoirs (C-10). *[DT]* *Statut* : à confirmer (V6-12).

### A6-12 — Avoir sur BC `termine` (TR-16 / PT-16) — **résolu (VR-07)**
- *Sources* : INV-47 (« Avoir sur BC `termine` : l'existant le refuse (TR-16), ce qui est à confirmer au regard de CDC §22 ») ; modèle §8 TR-16 (« sur BC `termine` : à confirmer ») ; PT-16 ; **vs** CDC §22 (l'avoir est « le mécanisme de correction ou de restitution après facturation lorsque cela est nécessaire », sans condition d'état), C-06 et C-13 (facture payée, avoir, remboursement), arbitrage B.
- *Hiérarchie* : INV-47 = énoncé « à confirmer », non décision ; CDC §22 et C-xx indiquent que refuser l'avoir sur BC `termine` empêcherait les cas de remboursement après règlement complet (CD-04).
- *Résolution [VR]* : l'avoir est **autorisé** sur un BC `termine` ; ce n'est pas une réouverture commerciale. TR-16 n'existe pas dans le SQL (0 occurrence) : 006 le crée sans ce refus.
- *Statut* : **verrouillé**.

### A6-13 — TR-22 « solde = formule 3.2 » vs modèle §14 « montants exacts de situation et de solde : service »
- *Sources* : modèle §8 TR-22 et INV-57/INV-58 (couche TRG) **vs** modèle §14 (« Montants exacts de situation et de solde | service (formules §3) + tests C-03/C-04 »).
- *Nature* : deux colonnes du même document assignent la même règle à deux couches.
- *Résolution [PR]* : **trigger** pour ce qui est calcul d'ensembles sans arrondi (solde = contractuel − nette ; bornes ; `montant_deja_facture_ht` = nette avant) ; **service** pour l'arrondi du pourcentage (HALF_UP) et la sémantique de la saisie. Une exactitude du montant de situation en mode pourcentage en SQL est faisable (§6.2) mais *dépend de PT-11*. *Statut* : ouvert (V6-13).

### A6-14 — Composition des lignes : SQL ou service ? Insertion tardive
INV-62 attribue la composition à « SQL, SVC » sans préciser la part SQL ; l'insertion de lignes hors transaction d'émission n'est détectable que par CK-04/05 (modèle §14). *Résolution [PR]* : un trigger `BEFORE INSERT ON facture_lignes` limité à des invariants **locaux** vérifiables ligne par ligne (type de ligne autorisé selon le type de facture, positivité, appartenance de `bc_ligne_id` au BC) ; **pas** de contrôle de somme ni de nombre de lignes final. *Statut* : ouvert (V6-14).

### A6-15 — Contrat d'import `factures` (P-04 non écrit)
Voir §12. Le modèle accepte le bloc mais ne détaille ni champs ni anomalies. *Statut* : ouvert (V6-15).

### A6-16 — Restes de texte CDC antérieurs aux amendements
- *Sources* : CDC §17 (texte d'origine sous l'encadré E-15 : annulation du BC interdite dès qu'une facture autre qu'un acompte non réglé existe ; acompte annulé automatiquement ; devis passe à Annulé), CDC §21 (liste d'états incluant « Annulée ») et CDC §16 (« annulation de règlement ou d'avoir ») **vs** encadrés d'amendement E-14/E-15/E-16 dans les mêmes sections ; errata E-14, E-15.
- *Hiérarchie* : errata + amendements prévalent sur le texte d'origine qu'ils déclarent remplacé. *[PR]* nettoyage éditorial du CDC (non effectué ici). *Statut* : informatif.

### A6-17 — Situation : plafond « 100 % » strict ou large ?
- *Sources* : métier §12 (« Une situation atteignant 100 % n'existe pas : la facture finale est un Solde ») **vs** modèle §3.2 et INV-57 (« nette après situation ≤ contractuel »).
- *Hiérarchie* : métier > modèle ? Même niveau de hiérarchie (modèle SQLite validé vs modèle métier) : le métier énonce l'intention, le modèle une borne technique non strictement équivalente.
- *Résolution [PR]* : borne **stricte** (`nette après < contractuel`, donc cumul `< 100.00`), qui oblige à émettre un solde (même `0.00`) pour atteindre 100 %. *Statut* : ouvert (V6-05).

### A6-18 — PT-11 (sens de la valeur « montant ») et D6 (réutilisation de `situation_numero`)
- *PT-11* : modèle §3.2/§4.8 (« À CONCEVOIR ») **vs** INV-57 (« montant = valeur cumulée visée − facturation nette avant », dans les deux modes) et E-17 (« valeur réalisée exprimée en montant »). *[PR]* lire la valeur saisie en montant comme **valeur cumulée visée**, cohérent avec « montants cumulés » (INV-190, C-37).
- *D6* : audit conservation §4.6, D6 « Ouverte » ; INV-52 « une situation active par numéro » → après avoir total d'une situation, le numéro d'ordre peut être réutilisé (la facture `FAC-` reçoit un numéro neuf). *[PR]* ne pas réutiliser (ordinal = `1 + max` sur **toutes** les situations du BC, neutralisées comprises) — mais c'est une règle absente des sources. *Statut* : ouvert (V6-05, V6-06).

### A6-19 — Nombre de lignes `deduction` pour la facturation antérieure
Modèle §4.8 : « lignes `deduction` (facturation nette antérieure, et remise globale de chaque devis rattaché) ». Seule la remise est « par devis ». *[PR]* ne rien imposer en SQL ; le service documente une ligne par facture antérieure ou une ligne de cumul. *Statut* : ouvert (V6-14).

### A6-20 — Types émissibles après neutralisation du solde
Voir §4.2 et §M.7. *Statut* : réduit à **QO-1** (le reste est tranché : VR-09, VR-12, CD-07).

### A6-21 — `date_emission` : passée, future, période facturée
Aucune source n'encadre `date_emission` autrement que par TR-02 et la borne de service ; aucune date de période facturée n'est documentée. *[PR]* ne rien ajouter. *Statut* : ouvert (V6-17).

### A6-22 — Tables absentes : `historique`, `documents`, `parametres_entreprise`
- *Sources* : INV-194 (historique métier utile), modèle §2.5 (`historique.type_evenement` : `emission`, `avoir`), §4.13–§4.15, D-34 (traités « dans leur contexte propre ») **vs** chaîne réelle 001 → 005b (aucune de ces tables).
- *Résolution [PR]* : 006 n'écrit aucun événement et ne référence aucune de ces tables (précédent : 005 « pas d'historique propre aux dépenses » ; 005b ne crée pas d'événement `rattachement_devis`). Le service journalisera lorsque la table existera. *Statut* : ouvert (V6-19).

### A6-23 — Rang de 006 et corrective `005c` — **décidé (VR-06)**
D-55 : rang = position dans la chaîne ordonnée ; `006` était réservé au rang 8 (modèle §17.1). La corrective `005c` (rang 8) précède 006, qui passe au **rang 9** ; conv. §5 précise que les noms 006 → 010 sont des **réservations d'ordre**. Les sources (D-55 complétée par D-56, modèle §17.1, conventions §5) ont été alignées le 2026-10-05, avant l'écriture de 005c (§M.8). *Statut* : **verrouillé** ; nommage : V6-20.

### A6-24 — Un solde à `0.00` ne peut pas être corrigé par avoir
INV-55 impose `avoir.total_ht > 0.00` et INV-76 `Σ avoirs ≤ montant de l'origine` : un solde à `0.00` ne peut recevoir aucun avoir, donc n'est jamais « neutralisé » et ne peut être remplacé (arbitrage B). *[DT]* conséquence directe de règles validées ; aucune règle n'organise la correction d'un solde `0.00` émis par erreur. *Statut* : à confirmer (**QO-2**).

### A6-26 — Caractère bloquant de CK-04/05/06 à la restauration
Voir §13. *Statut* : ouvert (V6-12).

---

## 16. Proposition de structure de `006_facturation.sql` (brief §23, question 19)

> **PROPOSITION**, rédigée avant les décisions de §19 et **alignée le 2026-10-05 sur VR-01 à VR-13**. Aucun SQL n'est écrit ici. V6-01 et V6-03 sont verrouillées ; le contenu dépend encore de V6-04 et V6-05 (⛔). Le rang de 006 est **9** (corrective 005c au rang 8, §M.8).

### 16.1 En-tête de fichier (comme 005 et 005b)

Références (modèle §4.8, §6, §8, §9, §14, §17.1 ; conv. §5, §9 ; cadrage 006 et décisions V6-xx validées), invariants cités, décisions, propositions techniques mises en œuvre (PT-9, PT-10, PT-11, PT-16 selon décisions), **liste explicite de ce qui n'est pas créé** (`reglements`, `garanties`, `historique`, `documents`, TVA/TTC, statut, annulation, brouillon, structure d'import au-delà de BLOC-IMP, exécution/remise au prorata PT-12/13, aucune donnée initiale), description d'exécution par le runner (une transaction, `user_version = 9` posé par le runner avant COMMIT, aucun `BEGIN`/`COMMIT`/`PRAGMA` dans le fichier, `foreign_keys=ON`, `recursive_triggers=ON`).

### 16.2 Contenu minimal et suffisant (ordre d'écriture)

| # | Bloc | Contenu | Remarques |
|---|---|---|---|
| 1 | Gardes d'exécution (optionnelles) | `user_version = 8` (chaîne 005c → 006) ; au besoin, vérification que la base n'a ni `factures` ni `facture_lignes` | précédent 005b (tables temporaires `CHECK`) ; 005 n'en a pas — **[DV]** simple choix de style |
| 2 | `CREATE TABLE factures` (STRICT) | colonnes et CHECK §2.2 | aucune ligne insérée |
| 3 | `CREATE TABLE facture_lignes` (STRICT) | colonnes et CHECK §2.3 | |
| 4 | Index | §2.2, §2.3 | un par FK + recherche (modèle §9) |
| 5 | Triggers d'immuabilité | `tr_20_factures_no_update`, `tr_21_factures_no_delete`, `tr_21_facture_lignes_no_update`, `tr_21_facture_lignes_no_delete` | messages `INV-53: …`, `INV-06: …` |
| 6 | Triggers d'insertion de `factures` | `tr_02_…`, `tr_16_…`, `tr_22_…` (×3), `tr_23_…` | gardes pures, ASCII sans accents (style 005b : `SELECT RAISE(ABORT, 'INV-xx: …') WHERE …`) |
| 7 | Trigger d'insertion de `facture_lignes` | selon V6-14 | |
| 8 | (selon décisions) | trigger `bc_devis` « après solde » (V6-10 ; règle fixée par VR-09) | **aucun remplacement d'objet existant dans 006** : le remplacement de `tr_12_bons_commande_annule` est porté par la corrective **005c** (rang 8) ; `frozen_at` : aucune action (VR-02) |
| 9 | Pied de fichier | aucun `INSERT` de donnée métier ; `sqlite_sequence` non touchée | |

### 16.3 Ce que le fichier ne doit pas contenir (garde-fous)

`reglements`, `garanties`, colonnes TVA/TTC, `statut`, `cancelled_at`, `updated_at`, drapeau « brouillon », triggers qui **écrivent** dans une autre table (sauf décision V6-07), CHECK inter-tables, borne d'année, ligne de `numerotation_sequences`, objet référencé inexistant (`historique`, `documents`), `DROP`/`ALTER` de 001–005c (le remplacement de `tr_12_bons_commande_annule` appartient à 005c), toute colonne ou règle `frozen_at`.

### 16.4 Volumétrie attendue (indicative, hors décisions de remplacement)

2 tables ; ≈ 7 index ; ≈ 11 à 14 triggers (4 d'immuabilité, 1 chronologie, 1 BC/client, 3 TR-22, 1 TR-23, 1 lignes, 1 `bc_devis` optionnel) ; 0 vue ; 0 ligne de donnée. Soit un **rang 9** de ≈ 99 à 103 objets nommés (79 au rang 7, 005c n'ajoutant aucun objet net, + ≈ 20–24) — à recalculer à l'écriture.

---

## 17. Proposition de structure de `test_006_facturation.py` (brief §24, question 20)

### 17.1 Conventions (conv. §7, tests 004/005/005b)

- Fichier `src-tauri/tests/metier/test_006_facturation.py` ; en-tête décrivant l'objet, les sources et la numérotation **T-48** (T-47 = 005c) ; méthodes nommées `test_INV_xx_…` / `test_T48_…`.
- Chaîne **001 → 006** (rang 9, 005c incluse) rejouée avec un runner émulé (comme `test_005b` : `executescript`, `user_version = rang`) ; connexion de test avec `foreign_keys=ON` et `recursive_triggers=ON`, un test de contrôle de ces réglages ; helpers d'état BC `en_cours / gele / termine / annule / annule_gele` réutilisés de 005b (`gele` = état de test sans statut ni effet : VR-02) (`test_005b:78-80`, `geler_bc`).
- Contrôles CK écrits en constantes SQL (`CK01_…`, `CK04_…`, `CK05_…`, `CK06_…`, `CK13_…`, `CK14_…`) comme dans 005b — **aucun nouveau CK**.
- Messages de triggers asserts par identifiant d'invariant (`refuse_inv("INV-53", …)`), comme dans 005.
- Effectif indicatif : **220 à 290 tests** (180 à 230 avant les groupes G22 à G24) (004 : 150 ; 005 : 158 ; 005a : 119 ; 005b : 153).

### 17.2 Groupes de tests (brief §24 + cadrage)

| Groupe | Contenu (liste non exhaustive) | Source |
|---|---|---|
| **G1 Migration et chaîne** | migration sur base issue de 001–005c ; rang et `user_version` posé par le runner ; atomicité (échec au milieu → aucun objet partiel, `user_version` inchangé) ; non-rejeu ; objets exacts créés (tables, index, triggers) et rien d'autre ; tables/triggers/index du rang 8 (005c) inchangés ; `integrity_check`, `foreign_key_check` | conv. §5 ; `test_T44_*`, `test_T46_*` |
| **G2 Structure** | tables STRICT, AUTOINCREMENT, colonnes exactes et types, NOT NULL, défauts `created_at`, FK et `ON DELETE` (RESTRICT), index, UNIQUE, absence de `updated_at`/`statut`/`cancelled_at`/TVA/TTC/`frozen_at`/`date_validation`, absence de BLOC-IMP+ et de `legacy_numero`, aucun BLOC-IMP sur `facture_lignes` | modèle §4.8 ; `test_T44_colonnes_exactes` |
| **G3 CHECK de `factures`** | F1 → F12 une par une, avec valeurs limites : type inconnu ; avoir sans origine / origine sans avoir ; motif vide ; échéance présente/absente selon type ; échéance < émission ; situation incomplète (chacune des 6 colonnes) ; `total_ht` `0.00` pour acompte/situation/avoir refusé, pour solde accepté ; négatif refusé ; préfixe/format/année du numéro (v6) ; `origine='import'` numéro libre mais non vide ; `legacy_*` interdits pour `v6` ; dates mal formées et dates inexistantes (`2026-02-30`) ; **absence de borne d'année** (`2100-01-01` accepté en SQL) | INV-55, INV-59, INV-131, D-38 |
| **G4 CHECK de `facture_lignes`** | `ordre ≥ 1`, `UNIQUE(facture_id, ordre)`, désignation vide, unités, `remise_*` cohérents, familles DL/D2S, `deduction ⇔ négatif`, `-0.00` refusé, `deduction ⇒ quantite='1'` | modèle §4.8, §2.3 |
| **G5 Montants** | formes canoniques D2/D2S/DL/P2 (zéros de tête, séparateurs, exposants, espaces) ; Σ en centimes exacte ; aucune `REAL` ; vecteurs C-14 → C-17 *(arrondi service, vérifiés par oracle Python HALF_UP)* ; `100.05 × 50 %` | INV-11 → INV-14 |
| **G6 Numérotation** | `UNIQUE(numero)` partagé FAC (situation vs solde) ; ACP/AVO séparés ; non-réutilisation (suppression refusée, `REPLACE` refusé, 3 variantes) ; `numerotation_sequences` : `tr_95`, `tr_96`, `REPLACE` refusé pour ACP/FAC/AVO ; TR-02 (égal accepté, antérieur refusé, autre clé indépendante, ligne absente selon V6-07) ; numéro immuable ; année du numéro = année d'émission ; plafond **non** testable en SQL (service) | INV-20 → INV-24, INV-179 |
| **G7 Immutabilité** | pour **chaque colonne** de `factures` : `UPDATE` refusé (y compris `client_id`, `bc_id`, `type`, `total_ht`, snapshots, `numero`, dates, `origine`) ; `UPDATE` sans changement refusé ; `facture_lignes` : `UPDATE` de chaque colonne refusé ; insertion de lignes sur une facture existante *(limite documentée : acceptée en SQL, détectée par CK-04/05)* | INV-53, TR-20, TR-21 |
| **G8 Suppression et contournements** | `DELETE` facture / ligne refusés pour chaque type ; `INSERT OR REPLACE`, `REPLACE INTO` et conflit `ON CONFLICT REPLACE` sur `factures` (par `id`, par `numero`) et `facture_lignes` (par `id`, par `(facture_id, ordre)`) ; suppression du parent : `DELETE bons_commande` (tr_19), `devis`, `clients`, `bc_lignes`, `factures` (origine d'un avoir) refusés ; FK `foreign_keys=ON` vs `OFF` (le `PRAGMA foreign_key_check` détecte) ; `ON DELETE CASCADE` absent | INV-06, INV-07, conv. §9, audit conservation §8 |
| **G9 Types : acompte** | acompte prévu vs facture vs (absence de) règlement ; acompte sans paiement possible ; un acompte non neutralisé par devis ; devis hors BC refusé ; plafond ≤ `devis.total_ht` ; acompte après solde refusé ; deux devis → deux acomptes ; nouvel acompte après avoir total accepté, après avoir partiel refusé | INV-189, INV-57, C-34 |
| **G10 Types : situation** | pourcentage et montant ; cumul ; `montant_deja_facture_ht` = nette avant ; nette après ≤ (ou <) contractuel ; situation après solde refusée ; numéro unique par BC non neutralisé ; après avoir : C-09 ; 6 colonnes figées ; vecteurs C-03, C-37 | INV-57, INV-190, C-03, C-09, C-37 |
| **G11 Types : solde** | final obligatoire ; `0.00` accepté (C-08) ; formule `contractuel − nette` (vecteurs C-04) ; deuxième solde refusé ; solde après avoir partiel de l'ancien refusé ; solde après avoir total accepté (nouveau numéro) ; acompte/situation après solde refusés | INV-58, C-04, C-07, C-08, C-33 |
| **G12 Types : avoir** | origine obligatoire, non avoir, même BC ; Σ ≤ origine (dernier centime) ; avoir sur avoir refusé ; avoir sur BC annulé accepté ; sur BC `termine` **accepté** (VR-07) ; motif ; échéance NULL ; avoir partiel ne rouvre pas ; avoir total puis nouvelle facture ; avoir sur solde `0.00` refusé | INV-76, INV-78, INV-188, C-33, C-35, C-36 |
| **G13 BC multi-devis** | matrice des états `en_cours`, `gele` (marqueur), `termine`, `annule`, `annule_gele` × {acompte, situation, solde, avoir} ; BC à 1, 2, 3 devis ; contractuel = Σ ; solde reprend les lignes de tous les devis ; remise globale par devis (lignes `deduction`) ; rattachement refusé après solde (y compris neutralisé) | INV-187, INV-188, C-34, C-35 |
| **G14 Lignes et composition** | par type (synthèse/prestation/déduction) ; `bc_ligne_id` d'un autre BC refusé ; `bc_ligne_id` NULL accepté ; `Σ lignes = total_ht` : CK-05 vide sur données cohérentes, **non vide** sur incohérence fabriquée ; facture sans ligne : CK-04 | INV-54, INV-62 |
| **G15 Caches du BC** | CK-06 : égalité caches/recalcul sur scénarios (C-03 → C-10) ; écriture en un seul `UPDATE` (aucun état intermédiaire refusé par les CHECK de 004) ; BC annulé : trois caches évolutifs, `statut` et `completed_at` figés (VR-05 ; G22) ; `date_100_facture` selon VR-10 | INV-46, INV-164 |
| **G16 Dates** | `date_emission` / `date_echeance` / `created_at` ; échéance = émission acceptée ; chronologie TR-02 ; fin d'année / bissextile (`2028-02-29`) | INV-10, INV-24, INV-59 |
| **G17 Import** | `origine='import'` : numéro libre non vide ; unicité ; immutabilité ; mêmes triggers que `v6` (acompte en double refusé, Σ échéance, chronologie) ; ordre d'insertion `date_emission` puis `ref` ; BC historique annulé (factures insérées `en_cours` puis BC annulé) ; absence de `legacy_numero` | INV-131, modèle §10.4–10.5 |
| **G18 Sauvegarde/restauration** | migration d'une base de rang 5, 6, 7 et 8 vers 9 (tables vides, ids conservés, `sqlite_sequence`) ; restauration + CK-13/CK-14 ; séquences après restauration d'une base plus ancienne (C-18 côté base : `dernier_numero` jamais diminué) | modèle §11.2 |
| **G19 TVA et absences** | aucune colonne `tva`/`ttc`/`taux`/`exoneration`/`statut`/`cancelled_at`/`motif_annulation`/`updated_at`/`frozen_at` ; aucune table `reglements`/`garanties`/`historique`/`documents`/`parametres_entreprise` ; aucune référence aux tranches suivantes dans le texte du SQL | `test_T44_aucune_dependance_aux_tranches_suivantes`, `test_T44_aucune_structure_…ni_de_tva…` |
| **G20 Non-régression 001–005c** | pour **chaque** objet de rang 8 (sauf `tr_12_bons_commande_annule`, remplacé par 005c et testé en 005c) : même DDL ; les suites 001–005b rejouées ; invariants rappelés (tr_12 contrat, tr_13, tr_17, tr_18, tr_19, tr_99, tr_95/96, tr_97, tr_98, tr_101/102) ; CK-13 et CK-14 inchangés | brief §25 |
| **G21 Triggers = gardiens** | aucun trigger de 006 ne modifie une donnée (selon V6-07) ; aucun CHECK/trigger inter-tables de « miroir » | `test_T29_*`, `test_T44_triggers_ne_font_que_garder` |
| **G22 BC annulé** (VR-04, VR-05) | acompte / situation / solde sur BC annulé refusés ; rattachement de devis refusé (`tr_99`) ; modification commerciale (colonnes du contrat) refusée ; modification de `statut`, `completed_at`, `cancelled_at`, `motif_annulation`, `frozen_at` refusée ; avoir sur document existant accepté ; recalcul des trois caches après avoir (un seul `UPDATE`) accepté ; `statut` reste `annule` ; aucune réouverture implicite ; règlement sur document existant : test porté par 007 (`reglements` n'existe pas en 006) | INV-173, INV-188, C-36, §M.4 |
| **G23 BC `termine` et avoirs** (VR-07, VR-09, VR-10, VR-11) | cas A à D de §M.5 (avoir partiel sur acompte, situation, solde ; avoir total sur acompte ; avoir total sur solde) ; conservation ou évolution de `termine` ; `termine → en_cours` dans le cas D ; `completed_at` cohérent (CHECK) ; `date_100_facture` conservée / NULL / nouvelle valeur ; aucun devis après un solde **y compris crédité** (CK-14, service, trigger si V6-10) ; nouveau solde après solde crédité accepté ; acompte / situation après solde crédité refusés | INV-42, INV-43, INV-58, INV-187, C-07, C-33, C-35 |
| **G24 `frozen_at` résiduel** (VR-02, VR-03) | O-1 à O-4 (pose conjointe, irréversibilité, NULL à la naissance, absence de comportement) ; les états de test `en_cours` et `gele` donnent les **mêmes** résultats de facturation ; aucune colonne `frozen_at` dans `factures` | §M.2 |

### 17.3 Cas chiffrés à traduire (modèle §13) : C-02 (à l'avoir près), C-03, C-04, C-07, C-08, C-09, C-14 → C-17, C-33 → C-37 ; C-05, C-06, C-10 → C-13 sont des cas de 007 *(sauf C-10 pour la partie « absorbé par avoir », vérifiable avec 006 seul)*.

---

## 18. Stratégie de mutation testing (brief §26, conv. §7.1)

### 18.1 Cadre

**[RD]** Chaque tranche reçoit sa campagne de mutation sur la migration **et** son fichier de test ; objectif : **0 survivant non qualifié** ; un survivant n'est conservé que s'il est démontré et documenté comme équivalent ou inatteignable (conv. §7.1). Précédents : 001 — 267 mutants, 255 tués, 10 survivants (8 équivalents, 2 inatteignables), 2 non viables (modèle §17.1) ; 004 : 150 tests ; 005 : 158 ; 005a : 119.

**Méthode [PR]** (celle des tranches précédentes) : copie de travail **hors dépôt** ; un mutant = une modification d'un seul élément du SQL de 006 ; exécution de `test_006_facturation.py` en arrêt au premier échec (`unittest -f`) ; le mutant est « tué » si au moins un test échoue, « non viable » si le SQL ne se charge plus (erreur de syntaxe/DDL), « survivant » sinon. Les migrations 001–005b ne sont jamais mutées par cette campagne (leurs propres campagnes existent) ; elles servent de décor. Les mutants des **requêtes CK** et des **helpers de test** (constantes `CK04_…`, `CK05_…`, `CK14_…`) sont aussi produits pour prouver que les tests détectent une incohérence fabriquée et non un résultat toujours vide.

### 18.2 Cibles à muter (brief §26) et opérateurs

| Famille | Éléments | Opérateurs de mutation |
|---|---|---|
| **CHECK** (`factures`, `facture_lignes`) | F1 → F12, `deduction ⇔ négatif`, `remise_*`, familles D2/D2S/DL/P2, dates, `created_at`, `json_valid` | suppression de la clause ; négation ; `AND ↔ OR` ; constantes (`'ACP-'` ↔ `'AVO-'`, `'0.00'` → `'0.01'`, `'situation'` ↔ `'solde'`) ; bornes `>= ↔ >` ; `IS NULL ↔ IS NOT NULL` ; motifs `GLOB` élargis/rétrécis ; `substr(…,3,2)` → `substr(…,1,2)` |
| **FK** | `bc_id`, `client_id`, `devis_id`, `origine_facture_id`, `facture_id`, `bc_ligne_id` | suppression de `REFERENCES` ; `RESTRICT → CASCADE / SET NULL / NO ACTION` ; mauvaise table ou colonne cible |
| **UNIQUE / PK** | `numero`, `(facture_id, ordre)`, `AUTOINCREMENT` | suppression ; élargissement/rétrécissement de la clé ; retrait d'`AUTOINCREMENT` (INV-04) |
| **STRICT / NOT NULL / DEFAULT** | tables STRICT ; chaque `NOT NULL` ; `origine DEFAULT 'v6'` ; `created_at DEFAULT` | retrait ; défaut modifié |
| **Triggers d'immuabilité** | `tr_20_*`, `tr_21_*` | suppression du trigger ; `BEFORE → AFTER` ; restriction de `UPDATE OF col` ; `WHEN` ajouté ; message modifié |
| **Triggers d'insertion** | `tr_02`, `tr_16`, `tr_22_*`, `tr_23`, `tr_24`, `tr_99_bc_devis_*` | suppression de chaque `RAISE` d'un trigger multi-règles ; `WHERE` : `AND ↔ OR`, `= ↔ <>`, `< ↔ <=`, `IS NOT ↔ <>` (cas NULL), `EXISTS ↔ NOT EXISTS` ; `bc_id ↔ id` dans les jointures ; types ; conversion en centimes (`REPLACE(x,'.','')` retiré) ; signe d'un avoir dans la nette ; `+` ↔ `−` ; `SUM` sans `COALESCE` |
| **Règles de calcul** | nette, solde, plafond d'acompte, nette après situation, Σ avoirs ≤ origine, définition de « neutralisée » | altération de la formule d'un chiffre ; inversion d'une comparaison ; omission d'un terme (avoirs, soldes, situations) |
| **Règles de verrouillage** | états BC (`en_cours`, `termine`, `annule`) ; client du BC ; BC annulé **et BC `termine`** acceptent l'avoir ; interdictions après solde (y compris crédité) | inversion de la condition d'état ; retrait d'un état de la liste |
| **Index** | un par FK + recherche | suppression (détectée par la structure, §17.2 G2) |
| **Requêtes CK** | CK-04, CK-05, CK-06, CK-13, CK-14 (clause après solde) | jointure modifiée, filtre inversé, colonne comparée altérée |

### 18.3 Classification obligatoire des survivants (brief §26)

| Classe | Définition | Preuve exigée | Décision |
|---|---|---|---|
| **Équivalent** | le mutant ne change aucun comportement observable | raisonnement + énumération exhaustive d'un domaine borné (types × états BC × valeurs frontières) montrant des sorties identiques | conservé, consigné avec la preuve |
| **Redondant** | un second objet garde le même comportement : le mutant est masqué | identifier l'objet masquant ; test ciblé le neutralisant (il est possible de désactiver l'objet masquant sur une base de test) | conservé **ou** redondance supprimée/assumée (« défense en profondeur ») — décision écrite |
| **Non testable** | le comportement n'est pas observable en SQLite (service, `machine.db`) ou l'état est inatteignable | démonstration d'inatteignabilité ou renvoi à la couche responsable | consigné, avec le test de service attendu |
| **Véritable faiblesse** | un comportement réel n'est détecté par aucun test | — | **test ajouté**, mutant tué avant clôture |

**Règle de clôture** : aucun survivant non équivalent sans décision ; **0 survivant non qualifié** (conv. §7.1). Le rapport de campagne liste mutant, classe, preuve, décision.

### 18.4 Survivants prévisibles à préparer (hypothèses de travail **[PR]**, à vérifier, non des constats)

| Zone | Pourquoi un survivant est plausible | Classe probable |
|---|---|---|
| `BEFORE → AFTER` sur un trigger qui ne fait que `RAISE(ABORT)` sans lire la ligne insérée | l'effet (annulation de l'instruction) est identique | équivalent (à prouver) ; **ne l'est pas** pour les gardes qui testent l'existence d'une autre facture (l'`AFTER` verrait la ligne insérée) → doit être tué |
| `ON DELETE RESTRICT → NO ACTION` | comportement identique pour des FK non différées | équivalent (à prouver sur FK immédiates) |
| FK `facture_lignes.facture_id` / `factures.bc_id` mutées alors que `tr_21` / `tr_19` interdisent déjà la suppression du parent | double protection | redondant |
| `tr_20_factures_no_update` vs gardes par colonne (si elles existent) | `UPDATE` interdit globalement | redondant |
| CHECK `total_ht <> '0.00'` vs famille D2 > 0 | recoupement partiel selon le type | à qualifier |
| `numero` unique vs format | formats disjoints par préfixe | à qualifier |
| Plafond 99 999, borne d'année, attribution du numéro | règles de service | non testable (SQL) |
| `index` mutés | pas de comportement fonctionnel | tués par le test de structure (sinon non testable) |
| Message de `RAISE` modifié | n'affecte que le texte | tué si les tests assertent l'identifiant INV (`refuse_inv`) — sinon véritable faiblesse |

### 18.5 Ordre de la campagne (propositions)

1. Passe DDL (CHECK, FK, UNIQUE, NOT NULL, STRICT, défauts).
2. Passe triggers d'immuabilité et de suppression.
3. Passe triggers d'insertion (TR-02, 16, 22, 23, lignes, `bc_devis`).
4. Passe calculs/verrouillages (cas chiffrés C-xx).
5. Passe CK et helpers de test.
6. Rejeu complet de 001–005c sur la chaîne 001 → 006 (non-régression). Le trigger de 005b remplacé par 005c (VR-06) est couvert par la **campagne ciblée de 005c** (conv. §7.1 : « Lorsqu'une correction est apportée à une migration déjà existante… ») ; 006 ne mute ni 005b ni 005c.

Volumétrie indicative (**[PR]**, non documentée) : de l'ordre de **plusieurs centaines** de mutants (≈ 500 à 900), plus nombreux que pour 004 du fait des triggers multi-règles.

### 18.6 Compléments du 2026-10-05

Familles ajoutées à la campagne de 006 : définition de « neutralisée » (`=` ↔ `<=`/`<`, `total_ht > 0` supprimé), clause « un solde a existé » (neutralisé ou non), `EXISTS ↔ NOT EXISTS` sur les soldes, conditions d'état du BC dans TR-16 (`termine` accepté pour l'avoir), requêtes CK-06 (BC annulé : trois caches seulement) et CK-14. Campagne **ciblée** de 005c : ≈ 40 à 80 mutants **[PR]** (un trigger, ≈ 25 colonnes ; détail en §M.8, §M.9). Règle de clôture inchangée : **0 survivant non qualifié**.

---

## 19. Liste des décisions nécessitant notre validation (brief §27, question 18)

Légende : ⛔ = bloque l'écriture du SQL (DDL ou trigger dont la forme en dépend) ; ◐ = à trancher avant le SQL mais avec une proposition par défaut raisonnable ; ○ = indépendant du SQL ; ✔ = **verrouillée le 2026-10-05** (§M.1). « Recommandation » = **PROPOSITION**, jamais une décision. Les lignes marquées ✔ sont des décisions de Rémy ; les autres restent des propositions.

| ID | Question | Options (la 1ʳᵉ = proposition) | Réf. | Prio |
|---|---|---|---|---|
| **V6-01** ✔ | **Sort de `frozen_at` (PT-8) et règle du brief « gel au premier encaissement »** | **Verrouillée (VR-01 à VR-03)** : gel progressif abandonné (E-10) ; colonne conservée, statut résiduel technique ; obligations techniques O-1 à O-5 ; aucune corrective pour `frozen_at` | A6-01, §M.2, modèle §7.1, INV-46, journal INV-33/35 | ✔ |
| **V6-02** | **PT-9** : « actif » / « entièrement créditée » ; « avoir total » = un avoir ou un cumul ; mécanisme d'unicité ; solde `0.00` non corrigeable | **Définition verrouillée (VR-12)**, lecture cumulative incluse ; reste **[PR]** : unicité par triggers `EXISTS` ; solde `0.00` : QO-2 (aucune règle inventée) | A6-04, A6-05, A6-10, A6-24, INV-52 | ◐ |
| **V6-03** ✔ | **PT-16** : caches d'un BC annulé après avoir ; avoir sur BC `termine` ; avoir total sur le solde d'un BC `termine` | **Verrouillée (VR-04 à VR-09)** : caches évolutifs sur BC annulé (`statut` reste `annule`) via la corrective **005c** ; avoir autorisé sur BC `termine` ; `termine → en_cours` possible par recalcul (état dérivé ≠ réouverture commerciale) | A6-02, A6-03, A6-12, INV-47, INV-173, INV-188, 005b l.26-27, §M.4, §M.5 | ✔ |
| **V6-04** | **PT-10** : `factures.devis_id` (acompte seulement) ; un acompte non neutralisé par devis ; plafond = `devis.total_ht` ; acompte facturé = prévu ou seulement ≤ plafond ? | colonne `devis_id` + CHECK F8 ; plafond seulement | §6.4, §9.2, INV-189, D-48 | ⛔ |
| **V6-05** | **PT-11** : colonnes de situation (`situation_mode`, `situation_valeur_saisie`) ; sens du « montant » (valeur cumulée visée) ; plafond strict `< 100 %` | cumulée ; strict | A6-17, A6-18, INV-57, INV-190, E-17 | ⛔ |
| **V6-06** | **D6** : `situation_numero` réutilisable après avoir total d'une situation ? | non réutilisable (ordinal = max global + 1) | A6-18, audit conservation §4.6 | ◐ |
| **V6-07** | **TR-02** : clé `(type, année de date_emission)` ; ligne de séquence absente ; qui écrit `derniere_date` (service ou trigger) | clé par type+date ; pas de création de ligne par trigger ; écriture par le service ; trigger garde pure | A6-07, §5.3, modèle §8, §10.5–10.6 | ◐ |
| **V6-08** | **« Document correctif »** = avoir uniquement ? **Correction d'un avoir erroné** (partiel) : rien n'est documenté | aucun 5ᵉ type ; laisser la correction d'un avoir partiel erroné non conçue et le dire | A6-09, A6-10, E-14, INV-185 | ◐ |
| **V6-09** | Après avoir total sur le **solde**, quels types peuvent être émis ? | **Réduite à QO-1** : nouveau solde seulement (INV-58, E-14, C-33) ; reste le remplacement d'un acompte/d'une situation crédité(e) alors qu'un solde existe | A6-20, §M.7, CD-08 | ◐ |
| **V6-10** | Garde SQL « aucun devis rattaché après un solde » (même crédité) : la **règle est fixée** (VR-09) ; **couche** : nouveau trigger sur `bc_devis`, ou service + CK-14 seulement ? | nouveau trigger (aucune réécriture de 005b) ; CK-14 reste le diagnostic | modèle §4.7, §14 ; INV-187 | ◐ |
| **V6-11** ✔ | **`date_100_facture`** après avoir total du solde puis nouveau solde ; lien avec la règle des 30 jours | **Verrouillée (VR-10, VR-13)** : NULL si le solde actif est totalement crédité et qu'aucun autre n'est actif ; date du nouveau solde actif ; 006 n'agit pas sur la règle des 30 jours | A6-06, INV-43, INV-103, D-31 | ✔ |
| **V6-12** | **Frontière 006 / 007** : parts de `termine`, CK-06, CK-04/05/06 bloquants ou non à la restauration | 006 : formules de facturation et gardes ; 007 : `reste_du`, `termine` par encaissements ; échec de CK-04/05/06 non bloquant tant que rien n'est décidé | A6-11, A6-26, §1.3, §13 | ◐ |
| **V6-13** | **Triggers vs service** pour l'exactitude du solde et de la situation (TR-22 vs modèle §14) | trigger pour sommes/bornes ; service pour l'arrondi % | A6-13, §6.2 | ◐ |
| **V6-14** | **Lignes** : composition par type en trigger ; `bc_ligne_id` du même BC ; lignes `deduction` de facturation antérieure (nombre) ; aucune garde heuristique d'insertion tardive | trigger de gardes locales ; rien d'autre | A6-14, A6-19, INV-62 | ◐ |
| **V6-15** | **Contrat d'import `factures`** (P-04) : `devis_id` des acomptes, champs de situation, `montant_deja_facture_ht`, avoir de facture V2 annulée (PT-19), `created_at`, clé TR-02 | à écrire dans le contrat ; 006 n'ajoute que BLOC-IMP | A6-15, §12 | ○ |
| **V6-16** | **TVA** : confirmer l'absence de toute colonne ; où vit la mention légale de franchise ? | absence de colonnes + test ; mention hors SQL (document) | A6-08, §8 | ○ |
| **V6-17** | **`date_emission`** : dates futures/passées, période facturée | rien en SQL | A6-21, §7 | ○ |
| **V6-18** | **Documentation** : intégration de la V3.13 dans `docs/` avant le gel du SQL | intégrer / confirmer | A6-00, §0.3 | ○ |
| **V6-19** | **`historique` / `documents`** absents : 006 n'écrit aucun événement et ne référence pas ces tables | oui | A6-22 | ○ |
| **V6-20** ✔ | **Nom exact** de la corrective 005c et de son test ; gardes d'exécution (style 005b ou 005) | **Décidée (2026-10-05)** : `005c_bc_annule_caches_financiers.sql` et `test_005c_bc_annule_caches_financiers.py` ; aucune garde d'exécution dans le SQL ; rang **9** pour 006 et **T-48** (décidés par VR-06) | D-55, A6-23, §16, §M.8 | ○ |

**Ordre de décision recommandé** (V6-01, V6-03 et V6-11 étant verrouillées, V6-02 réduite) : V6-04 et V6-05 (DDL de `factures`), puis QO-1, V6-07, V6-10, V6-13, V6-14, puis les points ○.

---

## Annexe A — Réponses aux 20 questions du brief

1. **Qu'est-ce qu'une facture ?** Un document de facturation **validé**, numéroté, rattaché à un BC, immuable dès l'INSERT, sans statut, sans brouillon, sans TVA ni TTC, jamais annulé ni supprimé. *(§1.1 ; INV-185, INV-53, métier §10, E-14)*
2. **Types exacts ?** `acompte`, `situation`, `solde`, `avoir` — pas de `complete`, pas de cinquième type documenté ; « document correctif » non défini (A6-09). *(§1.2 ; CDC §18, modèle §2.5)*
3. **ACP, FAC, AVO ?** `ACP-nnnnn-yy` (acomptes), `FAC-nnnnn-yy` (situations **et** soldes, séquence partagée), `AVO-nnnnn-yy` (avoirs) ; année = `date_emission` ; réservation PT-1 ; trou accepté, doublon jamais ; chronologie TR-02 ; `numerotation_sequences` inchangée. *(§5 ; modèle §6, INV-20 → 24, INV-179)*
4. **Lien au BC ou aux devis/lignes ?** Au **BC** (`bc_id`) ; devis référencé seulement par un acompte (PT-10, proposition) ; lignes de facture ↔ `bc_lignes`, jamais `devis_lignes`. *(§3 ; métier §10–§11)*
5. **Plusieurs devis d'un BC ?** Facturation **globale au BC** (situations, solde) ; un acompte par devis ; remises globales en lignes `deduction` par devis ; pas de ventilation ; rattachement tardif possible jusqu'au solde. *(§9.2 ; D-48, INV-187, INV-189, INV-190)*
6. **Situation ?** Globale au BC, saisie en % ou en montant, calcul en montants cumulés, mode/valeur/avancement/montant figés, ne peut atteindre 100 % (le solde clôt), ni suivre un solde ; correction par avoir ; colonnes et sens du « montant » = PT-11 **à valider**. *(§4.2, §6.2 ; métier §12, E-17, INV-57)*
7. **Solde ?** Toujours la facture finale, `0.00` autorisé, `= contractuel − nette avant`, unique non neutralisé par BC, clôture commerciale (plus de devis), déclenche `date_100_facture` et les garanties (008). *(métier §13, INV-58)*
8. **Acomptes ?** Prévu ≠ facturé ≠ encaissé ; un par devis ; plafond = contractuel du devis ; pris en compte par la nette dans le solde (lignes `deduction`) ; la facture d'acompte n'est pas un règlement. *(§6.4–6.5 ; INV-189)*
9. **Avoirs ?** Seul mécanisme de correction : origine obligatoire, même BC, non avoir, motif, Σ ≤ origine, jamais annulable ; avant solde il libère un montant refacturable ; après solde il ne rouvre rien ; avoir total ⇒ nouvelle facture du même type, nouveau numéro. Correction d'un avoir erroné : non conçue. *(métier §14, INV-76, INV-185 ; A6-10)*
10. **Immuabilité ?** **Dès l'INSERT**, pour tout : numéro, BC, client, type, dates, montants, lignes, snapshots, relations. *(§4 ; INV-53, TR-20, TR-21, INV-184)*
11. **Documents supprimables ?** **Aucun** (facture, acompte, situation, solde, avoir, lignes, relations). Seule une *préparation non validée* disparaît parce qu'elle n'a jamais existé en base. *(INV-06, INV-53, INV-185)*
12. **Règles par état du BC ?** `en_cours` : tous types tant qu'aucun solde n'a été émis (après un solde, même crédité : nouveau solde et avoirs seulement) ; `termine` : aucun nouveau document hors avoir, **avoir autorisé** (VR-07) ; `annule` : terminal commercial, avoirs et règlements sur documents existants, caches financiers évolutifs, `statut` reste `annule` (VR-04, VR-05) ; `frozen_at` : marqueur technique résiduel sans effet ; `gele` n'est pas un statut. *(§9.3, §M.3 à §M.5 ; INV-47, INV-188)*
13. **006 vs 007 ?** 006 : tables `factures`/`facture_lignes`, formules de facturation, unicités, plafonds, immuabilité, numérotation (garde). 007 : règlements, `reste_du`, `absorbe`, crédit, états de paiement, `termine` par encaissements. *(§1.3)*
14. **Données historiques à conserver ?** Toute facture et toute ligne (contenu, snapshots, numéro, relations BC/avoir/devis), jamais modifiées ; les caches du BC, eux, sont recalculables. *(INV-184, INV-30)*
15. **Garanties SQLite ?** Formes et types, unicités, FK RESTRICT, immuabilité, non-suppression (y compris `REPLACE`), plafonds locaux, chronologie, conditions d'état du BC. *(§11)*
16. **Règles de service ?** Attribution du numéro (PT-1), calcul des montants et arrondis, Σ lignes, caches du BC, échéance, borne d'année, garanties, rattachement de devis (porte), événements d'historique. *(§11)*
17. **CK nécessaires ?** Aucun nouveau. Existants rendus exécutables ou complétés : CK-01, CK-02, CK-04, CK-05, CK-06, CK-13, CK-14 (clause « après solde »). *(§9.4, §11)*
18. **Décisions à valider ?** V6-01, V6-03 et V6-11 **verrouillées** (VR-01 à VR-13) ; **bloquantes restantes** : V6-04 (devis_id), V6-05 (situation) ; questions ouvertes : QO-1, QO-2 ; autres : V6-02 (mécanisme), V6-06 à V6-08, V6-10, V6-12 à V6-19 (V6-20 décidée le 2026-10-05). *(§M.11, §19)*
19. **Structure minimale de `006_facturation.sql` ?** 2 tables STRICT (`factures`, `facture_lignes`), ≈ 7 index, ≈ 11–14 triggers gardiens, 0 donnée, sans TVA/statut/annulation/historique ; **rang 9, après la corrective 005c** ; aucun remplacement d'objet existant dans 006. *(§16, §M.8)*
20. **Campagne de tests ?** 24 groupes (G1 → G24), 220–290 tests, matrice des états du BC (dont annulé, et `termine` avec avoirs), contournements `DELETE`/`REPLACE`/parent/FK, non-régression 001–005c, CK écrits en constantes, mutation à 0 survivant non qualifié (006, plus campagne ciblée 005c). *(§17, §18, §M.9)*

---

## Annexe B — Vérification d'intégrité du dépôt (fin de phase)

- Fichier modifié lors de la mise à jour du 2026-10-05 (V6-01, V6-03) : **uniquement** `fichiers-a-relire/CADRAGE__006_facturation.md`.
- Aucun autre fichier du dépôt modifié ; **aucune migration ni aucun test de 006 créé** ; aucun CK, aucune décision officielle créé par ce cadrage.
- Les trois fichiers 005b (`005b_bc_multi_devis.sql`, `test_005b_bc_multi_devis.py`, `CADRAGE__005b_bc_multi_devis.md`) sont présents dans `main` : non touchés.
- Mise à jour du 2026-10-06 : la corrective 005c (`005c_bc_annule_caches_financiers.sql` et `test_005c_bc_annule_caches_financiers.py`) est livrée dans `main` ; elle n'est pas modifiée par ce cadrage, qui n'en reprend que l'état (rang 8, 006 au rang 9).
- Ce cadrage ne commite ni ne pousse rien ; l'intégration dans le dépôt est manuelle.
