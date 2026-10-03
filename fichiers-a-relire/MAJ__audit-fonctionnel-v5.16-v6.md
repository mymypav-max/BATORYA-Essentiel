# Audit fonctionnel V5.16 → BATORYA V6

Statut : Audit clôturé (historique) — mis à jour le 2026-10-01 (alignement sur le modèle SQLite V3.9, le registre des invariants v4 et les errata E-01 à E-09). **Renvois ajoutés le 2026-10-03 (en relecture)** : plusieurs règles ci-dessous sont dépassées par les arbitrages E-10 à E-20 (modèle SQLite V3.13, invariants v7) ; l'audit historique n'est pas réécrit, les passages concernés portent une mention « Dépassé ».
Version de référence : BATORYA V5.16 (**jamais distribuée**)
Cible : BATORYA V6 – Essentiel

⸻

## 1. Objet du document

Cet audit vérifie que la conception fonctionnelle de BATORYA V6 a bien pris en compte les règles métier, comportements et fonctionnalités utiles présents dans BATORYA V5.16.

L'objectif n'est pas de déterminer quelles parties du code V5.16 peuvent être réutilisées. BATORYA V6 fait l'objet d'une reconstruction complète, avec une architecture, un modèle de données et une séparation des responsabilités nouveaux.

### Statut de la V5.16

* La V5.16 **n'a jamais été distribuée**. Aucun utilisateur ne possède de données V5.16 : **il n'existe donc aucune migration V5.16 → V6**, et il n'y en aura pas.
* La V5.16 sert uniquement de **référence fonctionnelle et technique** (règles métier, comportements, catalogue de prestations).
* La seule migration réelle prévue concerne l'ancien **format de sauvegarde JSON V2** d'un utilisateur historique. Elle passe par un convertisseur externe (§ 18) ; BATORYA V6 ne lit jamais le format V2.

### Documents de référence actuels

* CDC V6 (gelé) et registre d'errata `cdc-errata-v6.md` (E-01 à E-09) ;
* modèle métier V6 ;
* modèle de données SQLite V6 (V3.9) et registre des invariants `invariants.md`.

En cas de divergence entre cet audit et ces documents, ce sont ces derniers qui font foi.

⸻

## 2. Méthode d'audit

L'analyse a été réalisée en confrontant :

* les fonctionnalités réellement présentes dans V5.16 ;
* les règles métier observées dans le fonctionnement des modules ;
* les décisions fonctionnelles prises lors de la conception de V6 ;
* le CDC V6 consolidé, puis le modèle de données SQLite et ses errata.

Pour chaque domaine, les fonctionnalités ont été classées selon quatre catégories :

* **Conservé** : comportement ou règle métier repris dans V6 ;
* **Évolué** : comportement V5 conservé mais modifié ou renforcé ;
* **Abandonné** : fonctionnalité volontairement supprimée du périmètre V6 ;
* **Remplacé** : fonctionnalité conservée dans son objectif mais entièrement reconstruite selon une nouvelle logique.

Pour le catalogue et les garanties, le constat est en outre détaillé selon cinq colonnes : ce qui existe déjà, ce qui est conservé, amélioré, supprimé, et ce qui est créé en V6.

⸻

## 3. Synthèse par domaine

### 3.1 Catalogue de prestations

**V5.16**

Le catalogue contient les prestations prédéfinies utilisées pour constituer les devis. L'audit du catalogue réel a permis d'identifier **205 prestations** prédéfinies.

Certaines incohérences existent dans le modèle V5 :

* coexistence de `categorie` et `corps` ;
* unités non uniformisées ;
* prix stockés sous forme numérique flottante ;
* suppression physique des prestations.

La prestation **ELE-008 – « F+P prise RJ45 Cat6 avec câblage »** est une **prestation spécifique**, et non une catégorie « Cat6 ».

Les garanties sont **déjà gérables depuis le Catalogue** de la V5.16 : elles sont rattachées aux prestations.

**Décision V6**

Remplacé (catalogue reconstruit), garanties conservées.

* Le catalogue V6 est reconstruit proprement à partir du catalogue réel V5.16. Les données utiles sont conservées, le modèle est normalisé.
* ELE-008 est **supprimée** du catalogue V6 : le catalogue par défaut compte donc **204 prestations**. Un document historique qui la contiendrait la conserve par snapshot.
* La catégorie / famille est **rationalisée** : une seule notion de catégorie, tenue dans une liste de référence (plus de coexistence `categorie` / `corps`).
* Unités en liste fermée : `u`, `ens`, `ml`, `m2`, `m3`.
* Les prix sont traités avec une représentation décimale exacte (aucun flottant).
* Une prestation n'est jamais supprimée si elle a été utilisée : elle est **désactivée**.
* Les prestations utilisées historiquement ne cassent jamais les documents existants : les lignes de devis sont des snapshots.
* Le catalogue par défaut est chargé **uniquement** lors d'une « nouvelle installation » ; lors d'un import de données historiques, le catalogue est celui du fichier importé.
* **Il n'y a pas lieu de créer un module séparé « Garanties »** : la gestion des garanties reste dans le Catalogue (voir § 13).

| Existe déjà (V5.16) | Conservé | Amélioré | Supprimé | Créé en V6 |
|---|---|---|---|---|
| 205 prestations prédéfinies | Données commerciales utiles du catalogue ; garanties gérées depuis le catalogue | Catégorie unique ; unités fermées ; prix décimaux exacts ; désactivation au lieu de suppression | ELE-008 ; `corps` ; suppression physique ; prix flottants | Liste de référence des catégories ; catalogue par défaut de 204 prestations chargé à la nouvelle installation |

⸻

### 3.2 Clients

**V5.16**

Le client possède notamment : code, nom, prénom, adresse, téléphone, email, notes. Les documents conservent une copie des informations client utilisées lors de leur création.

**Décision V6**

Conservé et renforcé.

* Les clients deviennent de véritables entités référencées par identifiant (`client_id`) ; le rattachement ne repose plus sur le nom.
* Les documents conservent leur propre snapshot des informations client.
* Le code client est indépendant de la numérotation des documents : **`CLI-0001`** (quatre chiffres, sans année).
* Un client ayant un historique n'est jamais supprimé : il est archivé. *[Dépassé le 2026-10-03 — E-12 : conservation permanente, aucun archivage.]*
* Un client n'est jamais créé implicitement à partir d'un nom saisi dans un document. Le statut `a_rattacher` n'existe que pour un client issu de l'import de données historiques, en attente de rattachement à un client existant (le rattachement est tracé). *[Dépassé le 2026-10-03 — E-12 : le statut `a_rattacher` et le rattachement de client sont supprimés.]*

⸻

## 4. Devis

**V5.16**

Le devis permet notamment : sélection d'un client, prestations du catalogue, lignes libres, quantités, unités, prix, remises, type de prestation, acompte, validité, objet, adresse de chantier, notes, rappel, statut, création d'un BC lors de l'acceptation. Les lignes conservent les informations de la prestation au moment de leur utilisation. Numérotation V5 : `DEV-00001`.

**Décision V6**

Évolué et reconstruit.

* Le principe fonctionnel est conservé, le modèle de données est entièrement reconstruit.
* Numérotation : **`DEV-00001-26`**.
* Le devis possède un `client_id` en plus de son snapshot client. Les statuts sont normalisés : en attente, accepté, refusé, annulé.
* Les lignes sont des **snapshots structurés**. Une ligne libre n'a pas de prestation associée (aucune pseudo-prestation) ; une ligne issue du catalogue conserve la référence de la prestation.
* La date de création est distincte de la date d'acceptation ; la date d'acceptation est conservée comme événement métier.
* L'acceptation crée un véritable BC de façon structurée et **idempotente** (un seul BC par devis).
* **Un devis accepté mais non gelé reste modifiable** (errata E-01) : la modification du devis régénère le BC. Un devis refusé ou annulé est immuable. *[Dépassé le 2026-10-03 — E-10, E-11 : brouillon / devis validé verrouillé ; refusé rouvrable.]*
* La suppression est soumise aux règles d'historique.

⸻

## 5. Bons de commande

**V5.16**

Le BC V5.16 est principalement un prolongement du devis accepté, sans véritable entité indépendante ni mécanisme structuré d'annulation. Numérotation historique : `BC-0001-26`. Le statut dépend largement de la facturation.

**Décision V6**

Évolution structurelle majeure.

* Le BC devient une **entité centrale** du dossier, avec son propre cycle de vie et son **propre numéro V6** : **`BCD-00001-26`**. Le vocabulaire fonctionnel reste « BC ».
* Le BC est créé **à l'acceptation du devis** ; le devis reste le seul point d'édition tant que rien n'est gelé : les lignes du BC sont alors régénérées depuis le devis.
* Cycle normal : **En cours → Terminé**, avec retour possible à En cours (annulation d'un règlement ou d'un avoir). Un BC peut être Annulé.
* Un BC est **Terminé** lorsqu'un **solde actif** existe **et** que la somme des restes dus des factures actives (hors avoirs) est nulle. Un solde à 0 € ne suffit pas tant qu'un acompte ou une situation reste dû.
* **Gel** : la structure commerciale (devis et BC) est gelée, de façon irréversible, au premier encaissement actif d'un acompte, à l'émission d'une situation ou à l'émission du solde. Un acompte émis mais non encaissé ne gèle pas ; si le devis/BC est alors modifié, l'acompte non réglé est annulé automatiquement (errata E-01). *[Dépassé le 2026-10-03 — E-10 : plus de gel progressif ni d'annulation automatique d'acompte.]*
* **Annulation** (errata E-07) : interdite directement dès qu'une facture autre qu'un acompte non réglé existe ; une situation émise (même annulée) l'interdit toujours ; un montant encaissé l'interdit également. La correction passe alors par avoir ou annulation de facture. Un BC annulé reste conservé dans l'historique et ne participe plus au CA engagé. *[Dépassé le 2026-10-03 — E-15 : annulation sans condition de facturation, sans cascade vers les devis.]*

⸻

## 6. Facturation

**V5.16**

Le système distingue acompte, situation, solde, avoir et un ancien type technique `complete`. Les factures sont liées aux devis. Les situations utilisent une logique de progression cumulée. Les factures possèdent un montant restant à payer et un statut.

**Décision V6**

Reconstruit entièrement : le principe métier est conservé, le modèle V5 n'est pas repris.

* Le type `complete` disparaît. La facturation repose sur **Acompte, Situation, Solde, Avoir**. Les factures sont rattachées au BC.
* **Le solde est toujours le document final**, y compris lorsqu'aucun acompte ni aucune situation n'a précédé.
* Un **solde à 0 €** est autorisé (100 % déjà couvert par les acomptes et situations). Il reste l'événement de clôture de facturation.
* La logique des situations par progression cumulée est conservée : `montant de la situation = contractuel × cumul % − facturation nette antérieure`, sans jamais dépasser le contractuel.
* « 100 % facturé » signifie **présence d'un solde actif**.
* Dès qu'un solde actif existe : plus d'acompte, plus de situation, et **aucun avoir ne rouvre la facturation**.
* Une facture n'est jamais brouillon : elle est émise, puis seulement annulable. Facturation et paiement sont deux notions distinctes. *[Précisé le 2026-10-03 — E-14 : aucune facture brouillon ; une facture validée n'est plus « annulable », elle se corrige par un avoir.]*
* Numérotation : `FAC-00001-26` (commun aux situations et aux soldes), `ACP-00001-26`, `AVO-00001-26`.

⸻

## 7. Règlements

**V5.16**

Le règlement repose sur une date de paiement, un mode, un statut et un reste à payer ; une facture est marquée réglée en une seule opération.

**Décision V6**

Évolution fonctionnelle majeure.

* Le règlement devient une **entité indépendante** ; une facture peut recevoir **plusieurs règlements**. Chaque règlement contient date, montant, mode, référence et note.
* Deux types : **encaissement** et **remboursement** (un remboursement porte sur un avoir).
* Modes : espèces, chèque, virement, carte, autre.
* Le reste à payer est **calculé** (jamais saisi) ; un encaissement ne peut pas dépasser le reste dû.
* Les états de la facture sont **dérivés** et jamais persistés : en attente, partiellement réglée, réglée, annulée, avec l'indicateur transversal « en retard » (une facture peut être partiellement réglée **et** en retard). *[Dépassé le 2026-10-03 — E-14 : l'état « annulée » disparaît (remplacé par un état dérivé « entièrement créditée », PT-9).]*
* Un règlement n'est jamais supprimé : il est annulé (date et motif). Aucune réconciliation bancaire automatique n'est prévue.

⸻

## 8. Avoirs

**V5.16**

L'avoir est conservé comme document historique et référence une facture d'origine. Le V5 permet des avoirs partiels.

**Décision V6**

Conservé et renforcé.

* L'avoir est un document autonome, avec son numéro `AVO-00001-26`, son motif obligatoire et sa facture d'origine. Le total des avoirs actifs d'une facture ne dépasse pas son montant.
* L'avoir ne détruit ni ne modifie la facture d'origine. Une facture déjà payée n'est jamais supprimée : l'avoir est le mécanisme de correction.
* L'avoir réduit la facturation nette et, par le calcul du reste dû, peut absorber une dette ; il n'est pas un encaissement. Il ne rouvre jamais la facturation après un solde actif.
* Un éventuel remboursement est un règlement de type remboursement, limité au crédit disponible.
* L'impact d'un avoir ou d'un remboursement sur le calcul URSSAF est déterminé par la version du référentiel réglementaire applicable à la période.

⸻

## 9. Dépenses

**V5.16**

Les dépenses peuvent être globales, associées à un BC, à un fournisseur, avec pièce ou note. Le V5 possède une logique de paiement des dépenses.

**Décision V6**

Conservé pour l'analyse, simplifié fonctionnellement.

* Les dépenses restent globales ou rattachées à un BC. Le fournisseur est référencé par identifiant.
* La catégorie provient d'une liste de référence modifiable par l'utilisateur.
* La gestion du paiement est volontairement supprimée : pas de statut payé/non payé, pas de règlement fournisseur, pas d'échéance, pas de workflow de paiement.
* La dépense est une donnée d'analyse et de marge ; elle ne réduit jamais le CA servant au calcul URSSAF.
* Numérotation : `DEP-00001-26`.

⸻

## 10. Fournisseurs

**V5.16**

Le fournisseur constitue un carnet indépendant utilisé notamment pour les dépenses.

**Décision V6**

Conservé et restructuré.

* Entité indépendante, relation avec les dépenses par identifiant stable.
* Un fournisseur ayant un historique n'est jamais supprimé : il est archivé. *[Dépassé le 2026-10-03 — E-12 : conservation permanente, aucun archivage.]*
* Code : **`FOU-0001`** (quatre chiffres, sans année).

⸻

## 11. Planning → Planification

**V5.16**

Le planning représente les interventions liées aux devis/BC, avec prise en compte des jours ouvrés et des jours fériés français.

**Décision V6**

Évolué. Le module s'appelle **Planification** (errata E-03) et comporte deux onglets :

* **Calendrier** : événements typés (intervention, travaux, rendez-vous client, réunion, appel, administratif, congé, indisponibilité, autre), avec rattachement à un BC obligatoire pour `intervention` et `travaux`, et interdit pour congé et indisponibilité ;
* **Gantt** : lié aux dates de début et de fin du BC ; un BC sans dates n'a pas de barre.

Le planning ne modifie jamais le statut du BC. Les règles de jours ouvrés et de jours fériés pertinentes sont conservées. Aucune synchronisation avec Outlook ou Google n'est prévue en V6.

⸻

## 12. PV de réception

**V5.16**

Le PV est un objet distinct du devis/BC.

**Décision V6**

Évolué et restructuré.

* Le PV est **facultatif** : il ne conditionne ni le solde, ni l'état Terminé, ni les garanties.
* Types : réception sans réserve, réception avec réserves, levée de réserves.
* Le PV devient **immuable** dès son émission. La levée de réserves est un second PV autonome qui référence le PV d'origine (avec réserves, du même BC) ; une levée ne porte jamais sur une levée.
* Numérotation : `PVR-00001-26` ; levées : `PVR-00001-26-01`, `PVR-00001-26-02`…
* La levée des réserves ne modifie pas la date de début du suivi interne des garanties.
* Stockage : `2026/PV/`.

⸻

## 13. Garanties

**V5.16**

Le V5 associe les garanties aux prestations (configurables depuis le Catalogue) et calcule le suivi à partir de la réception / du PV.

**Décision V6**

Règle métier volontairement modifiée, configuration conservée.

* **Configuration** : depuis les prestations du Catalogue. Une prestation peut porter plusieurs types de garantie (le catalogue par défaut n'en utilise qu'un par prestation). Ces valeurs sont des valeurs par défaut, jamais une source historique.
* **Snapshots** : les types de garantie sont copiés sur les lignes de devis puis de BC ; une modification du catalogue ne change jamais une garantie existante.
* **Déclenchement** : les garanties natives sont générées au franchissement de 100 % facturé, c'est-à-dire à l'émission d'un **solde actif**, indépendamment du PV, de la réception, des réserves, de leur levée et du **paiement**.
* Types et durées : parfait achèvement (1 an), biennale (2 ans), décennale (10 ans).
* Création idempotente ; la première date est conservée. L'annulation du solde, un avoir ou un règlement ne suppriment ni ne modifient une garantie.
* **Aucune garantie n'est recréée à partir d'anciennes données V2** : les BC déjà soldés avant l'import n'en reçoivent pas.
* Le suivi est un **suivi interne indicatif** et non une détermination juridique ; le libellé « Suivi interne BATORYA — date indicative » doit rester visible.
* Pas de module catalogue de garanties séparé.

| Existe déjà (V5.16) | Conservé | Amélioré | Supprimé | Créé en V6 |
|---|---|---|---|---|
| Garanties gérées depuis les prestations du Catalogue ; suivi basé sur le PV | Configuration depuis le Catalogue ; types parfait achèvement / biennale / décennale ; caractère indicatif | Snapshots sur lignes de devis et de BC ; plusieurs types par prestation possibles | Dépendance au PV et à la réception ; recréation automatique depuis V2 | Garanties natives générées au solde actif ; création idempotente ; état dérivé (à surveiller / échue) |

⸻

## 14. Notes

**V5.16**

Le système possède des notes rattachées au contexte du dossier.

**Décision V6**

Conservé et amélioré. Le BC peut comporter plusieurs notes internes (contenu, dates de création et de modification), modifiables ou supprimables. Elles ne constituent pas un système de tâches ni de workflow et n'ont aucun effet sur les montants.

⸻

## 15. URSSAF

**V5.16**

Le V5 contient déjà des éléments de calcul et de suivi URSSAF.

**Décision V6**

Entièrement restructuré, déjà validé dans le CDC. Périmètre strict : micro-entrepreneur, BTP, prestations de services, franchise en base de TVA.

* Les calculs reposent sur le **CA encaissé** et non sur les factures émises ; les paiements partiels comptent à hauteur du montant réellement encaissé.
* Le profil URSSAF (date de début d'activité, périodicité, ACRE) est saisi par l'utilisateur et conservé par versions.
* Les périodes déclaratives sont conservées historiquement et **verrouillées** à la déclaration ; un événement postérieur touchant une période verrouillée crée une **correction** tracée (mécanisme dédié), jamais une modification silencieuse.
* Les règles réglementaires sont **versionnées** (append-only) ; les anciennes versions restent disponibles pour reproduire les calculs historiques. Le référentiel peut être mis à jour via les Services BATORYA.
* Les événements négatifs (avoirs, remboursements) sont pris en compte selon la règle du référentiel applicable.
* Aucune déclaration officielle automatique n'est effectuée.

⸻

## 16. Comptabilité et analyse

**V5.16**

Le système fournit chiffre d'affaires, facturation, encaissements, dépenses, marge, devis acceptés restant à facturer.

**Décision V6**

Conservé comme couche d'analyse. BATORYA ne devient pas un logiciel comptable complet ; les analyses exploitent les données des modules métier.

Trois niveaux de prévision sont distingués :

1. CA encaissé réel ;
2. CA engagé (BC en cours uniquement, net des avoirs et des encaissements) ;
3. CA prévisionnel.

Un BC annulé ne fait plus partie du CA engagé. Ces valeurs sont calculées, jamais stockées.

⸻

## 17. Documents et PDF

**V5.16**

Les PDF sont classés selon année, type de document et statut.

**Décision V6**

Conservé fonctionnellement, reconstruit techniquement. SQLite est la source de vérité ; le PDF n'en est qu'une représentation générée. Une régénération crée une nouvelle version du document.

Structure V6 :

```
2026/
├── Devis/
│   ├── En_attente/
│   ├── Accepte/
│   ├── Refuse/
│   └── Annule/
│
├── Factures/
│   ├── Acomptes/
│   ├── Situations/
│   ├── Soldes/
│   └── Avoirs/
│
└── PV/
```

Les BC ne possèdent pas de dossier PDF propre : ils constituent un dossier métier et non un document PDF indépendant. Le dossier de travail est indépendant de la base SQLite.

⸻

## 18. Sauvegardes, restauration et reprise des données V2

**V5.16**

Le V5 sauvegarde notamment devis, factures, clients, fournisseurs, dépenses, PV, notes, planning, historique, paramètres, compteurs. Une ancienne structure de sauvegarde V2 a également été identifiée.

**Décision V6 — sauvegarde et restauration**

Conservé et fortement sécurisé (errata E-02).

* La sauvegarde officielle est une **copie cohérente de la base SQLite métier** ; le JSON n'est qu'un **export** (consultation, archivage), jamais un format de restauration.
* Sauvegarde manuelle, automatique et à la fermeture, avec un seul moteur.
* Restauration validée et atomique : validation du fichier, contrôle de version, migrations de schéma sur copie, contrôles d'intégrité, **sauvegarde de sécurité** avant remplacement, contrôles après restauration.
* Les données machine (mot de passe local, licence, identifiant d'installation, dossiers de stockage, état de la numérotation attribuée) sont dans une base séparée qui n'est ni sauvegardée ni restaurée.
* Après restauration, un numéro déjà attribué n'est jamais réutilisé (§ 24).

**Décision V6 — reprise des données historiques V2**

La V5.16 n'étant pas une source, **la seule reprise de données prévue est celle de la sauvegarde JSON V2** de l'utilisateur historique. Son architecture est la suivante :

```
JSON V2  →  convertisseur externe  →  import-v6.json  →  import V6
```

* **Le convertisseur externe** porte toute la complexité propre à la V2 : anciennes structures, renommages, normalisation, catalogue, clients, devis/BC/factures, paiements, PV, compteurs historiques, anomalies et données non représentables.
* **BATORYA V6 ne lit jamais le JSON V2** et n'adapte pas son modèle à la V2. Il ne possède qu'un **lecteur strict** de `import-v6.json`, son contrat d'entrée.
* L'import se fait en deux temps (validation sans écriture, puis transaction unique) et **uniquement sur une base métier vide**. Tout fichier non conforme est rejeté en bloc.
* Les valeurs dérivées (caches du BC, gel) sont recalculées par V6 et jamais lues du fichier.
* Les compteurs historiques compatibles sont transmis dans le fichier (`sequences`) et initialisent la numérotation V6.
* Les anomalies et données non représentables sont déclarées dans le fichier et conservées dans une table dédiée (`import_anomalies`) ; les éléments à contrôler (par exemple une facture importée sans statut de paiement) sont signalés à l'utilisateur par un bandeau jusqu'à traitement. Il n'y a ni rapport de migration ni quarantaine génériques dans V6.
* Les règles de transformation V2 → `import-v6.json` seront décrites dans un document distinct consacré au convertisseur.

⸻

## 19. Paramètres

**V5.16**

Les paramètres regroupent les informations de l'entreprise et plusieurs préférences.

**Décision V6**

Restructuré. Les paramètres distinguent :

* identité professionnelle, informations administratives, coordonnées ;
* informations bancaires facultatives ;
* paramètres commerciaux (délai de paiement, modes de règlement, mentions et conditions) ;
* sauvegardes, Gmail, Services BATORYA, profil utilisateur, dossier de travail.

Les paramètres URSSAF disposent de leur propre espace. Les valeurs courantes ne reconstruisent jamais un document historique (snapshots). Les numéros de documents ne sont pas configurables manuellement.

⸻

## 20. Email et rapports d'erreur

**V5.16**

Le système permet notamment l'envoi manuel de documents par email.

**Décision V6**

Conservé. Gmail reste le fournisseur prévu, **facultatif**. Les emails sont toujours déclenchés explicitement par l'utilisateur ; il n'existe aucun envoi automatique et jamais de faux envoi si Gmail n'est pas configuré ou si l'envoi échoue. Cela concerne les devis, factures et autres documents (PDF envoyés manuellement) ainsi que les rapports d'erreur, copiables ou enregistrables et envoyés manuellement.

⸻

## 21. Licence et mises à jour

**V5.16**

Le V5 possède son propre mécanisme de licence et d'association à la machine.

**Décision V6**

Remplacé par **Services BATORYA — Licence & mises à jour** : validation de licence, association de machine, mises à jour logicielles, distribution du référentiel réglementaire.

* Vérification trimestrielle ; période de grâce de 15 jours pour reconnecter la machine.
* Après expiration : consultation et exports autorisés ; création, modification, suppression et facturation bloquées.
* Les secrets (clé de licence, jetons Gmail) sont conservés dans le coffre du système d'exploitation, hors base métier.
* Les données métier ne sont jamais transmises au service distant ; aucune dépendance réseau pour le fonctionnement métier courant.

⸻

## 22. Google Drive

**V5.16**

Une intégration Google Drive est présente dans le V5.

**Décision V6**

Abandonné. Google Drive ne fait pas partie du périmètre initial de BATORYA V6.

⸻

## 23. Historique

**V5.16**

Le système conserve différents événements liés aux opérations effectuées.

**Décision V6**

Conservé et restructuré. L'historique est **append-only** (aucune modification ni suppression) et indépendant de la structure interne des anciens modules. Il trace notamment : gel, émission, règlement et annulation, remboursement, avoir, annulation, passage à Terminé et retour à En cours, déclenchement de garantie, rattachement client, déclaration et correction URSSAF, import, restauration. Les suppressions destructives sont remplacées par l'archivage, l'annulation ou la conservation historique.

⸻

## 24. Convention de numérotation V6

L'audit a constaté que les conventions V5 sont hétérogènes. La convention V6 est uniformisée : **`TRI-00001-yy`** (trigramme métier, compteur sur 5 chiffres, année sur 2 chiffres), avec un compteur qui repart à 1 chaque année.

| Objet | Numéro |
|---|---|
| Devis | DEV-00001-26 |
| Bon de commande | BCD-00001-26 |
| Facture (situation, solde) | FAC-00001-26 |
| Acompte | ACP-00001-26 |
| Avoir | AVO-00001-26 |
| PV de réception | PVR-00001-26 |
| Levée de réserves | PVR-00001-26-01, PVR-00001-26-02… |
| Dépense | DEP-00001-26 |

Les clients et fournisseurs conservent leurs propres codes, sans année : **`CLI-0001`** et **`FOU-0001`**.

Règles :

* **un numéro déjà attribué n'est jamais réutilisé ; un trou de numérotation est acceptable** (annulation, incident, import) ;
* le dernier numéro attribué est mémorisé hors de la base métier afin qu'une restauration ou un incident ne puisse pas ramener un compteur en arrière ;
* les factures, acomptes et avoirs suivent une chronologie continue (date d'émission jamais antérieure à la dernière de la séquence) ;
* **exception historique d'import** (décision D-24) : les anciens numéros V2 des devis, factures et PV importés sont conservés tels qu'ils ont été remis aux clients ; les BC et les codes clients importés reçoivent des numéros V6.

⸻

## 25. Fonctionnalités volontairement abandonnées

L'audit confirme que les éléments suivants ne doivent pas être reproduits dans V6 :

* architecture V5 basée sur localStorage ;
* logique métier directement dans les modules UI ;
* ancien modèle de facture `complete` ;
* paiement unique des factures ;
* gestion du paiement des dépenses ;
* Google Drive ;
* ancienne logique de garantie basée sur le PV ;
* suppression physique non contrôlée des données historiques ;
* numérotations hétérogènes V5 ;
* gestion métier basée sur des noms texte lorsque des identifiants sont nécessaires ;
* stockage monétaire reposant sur des flottants ;
* dépendance à un backend pour les données métier ;
* **toute migration V5.16 → V6** (la V5.16 n'a jamais été distribuée) ;
* **tout lecteur ou moteur de migration V2 à l'intérieur de V6** : la conversion est externe.

Ces abandons sont des décisions de conception V6, et non des omissions de l'audit.

⸻

## 26. Points particuliers confirmés par l'audit

Plusieurs règles importantes ont été confirmées ou découvertes au cours de l'analyse :

* les Situations utilisent une logique de progression cumulée ;
* le solde est toujours le document final, y compris à 0 € ; aucun avoir ne rouvre la facturation après un solde actif ;
* la facturation et le paiement sont deux notions distinctes ;
* le règlement est une entité indépendante ;
* le BC est une véritable entité métier, avec son propre numéro ;
* un devis accepté mais non gelé reste modifiable ; le gel intervient au premier encaissement actif d'un acompte, à l'émission d'une situation ou du solde ; *[Dépassé — E-10 ; E-16.]*
* un BC annulé ne doit plus alimenter le CA engagé ; *[Inchangé ; E-15 : devis non annulés automatiquement.]*
* un BC ayant une facturation au-delà d'un acompte non réglé ne peut pas être annulé directement ; *[Dépassé — E-15.]*
* une facture payée ne doit pas être supprimée pour corriger son montant : l'avoir est le mécanisme approprié ;
* le suivi interne des garanties démarre au franchissement de 100 % facturé, indépendamment du paiement et du PV ; le PV et la garantie sont deux mécanismes distincts ;
* les garanties sont configurables depuis le Catalogue ; aucun module « Garanties » séparé n'est nécessaire ;
* les documents doivent conserver les informations historiques nécessaires (snapshots) ;
* le fournisseur doit être référencé par identifiant ;
* les règles URSSAF dépendent d'un référentiel réglementaire versionné ;
* le dossier de travail est indépendant de la base SQLite ; son changement ne déplace pas automatiquement les anciennes données, et une sauvegarde est proposée avant changement ;
* un numéro attribué n'est jamais réutilisé ;
* **la V5.16 n'a jamais été distribuée : elle n'est pas une source de migration ;**
* **l'ancienne sauvegarde JSON V2 est la seule source de reprise ; elle est traitée par un convertisseur externe et n'est ni un format de restauration V6 ni une contrainte technique de V6.**

⸻

## 27. Conclusion de l'audit

L'audit fonctionnel de BATORYA V5.16 est considéré comme terminé.

Aucune fonctionnalité métier majeure de V5.16 n'a été identifiée comme absente du périmètre fonctionnel V6.

Les différences entre V5.16 et V6 correspondent principalement à :

* des reconstructions techniques ;
* des normalisations de données ;
* des renforcements de règles ;
* des corrections de comportements fragiles ;
* des évolutions fonctionnelles volontairement décidées ;
* des fonctionnalités explicitement sorties du périmètre.

Le code V5.16 ne constitue donc pas une base technique à refactoriser. Il constitue une **source de vérification fonctionnelle et technique** et la source du catalogue de prestations, et non une source de migration.

À compter de la clôture de cet audit, le CDC V6 constitue la référence fonctionnelle. Le modèle métier V6, le modèle de données SQLite (V3.9), les invariants et les errata en sont la déclinaison à jour. La conception technique V6 est engagée indépendamment de l'architecture V5.16, dans l'architecture Tauri 2 + React + TypeScript.
