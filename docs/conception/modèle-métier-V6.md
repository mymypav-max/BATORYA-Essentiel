BATORYA Essentiel

Modèle métier V6 — Phase 1

Produit : BATORYA Essentiel
Version : V6
Statut : Conception technique — modèle métier
Périmètre : Micro-entrepreneur BTP — prestations de services — franchise en base de TVA

⸻

1. Principe général

BATORYA Essentiel est organisé autour du dossier commercial et opérationnel, dont le Bon de commande constitue l’élément central après acceptation d’un devis.

Le modèle métier suit globalement cette chaîne :

Client → Devis → Bon de commande → Facturation → Règlements

À cette chaîne principale s’ajoutent :

* prestations du catalogue ;
* dépenses ;
* planning ;
* notes ;
* PV ;
* garanties ;
* analyses ;
* URSSAF ;
* documents ;
* historique.

Les objets métier sont indépendants des écrans qui les manipulent.

Aucune interface ne doit devenir propriétaire des données ou des règles métier.

⸻

2. Entités principales

2.1 Client

Le Client représente le donneur d’ordre.

Données principales

* identifiant interne ;
* code client ;
* nom ;
* prénom ;
* coordonnées ;
* adresse ;
* téléphone ;
* email ;
* notes ;
* statut actif/archivé ;
* dates de création et modification.

Identifiant métier

CLI-001

Le code client est indépendant de la numérotation des documents.

Relations

Un client peut posséder :

* plusieurs devis ;
* plusieurs BC ;
* plusieurs factures ;
* plusieurs dépenses indirectement via les dossiers concernés.

⸻

3. Catalogue

3.1 Prestation

Une Prestation représente un élément commercial réutilisable dans les devis.

Données principales

* identifiant ;
* code prestation ;
* désignation ;
* description ;
* catégorie ;
* unité ;
* prix ;
* type de prestation ;
* paramètres de garantie éventuels ;
* actif/inactif.

Règle importante

Une prestation du catalogue n’est jamais la source historique d’un document existant.

Lorsqu’elle est utilisée dans un devis, ses informations commerciales nécessaires sont copiées dans la ligne du devis.

Une modification ultérieure du catalogue ne modifie donc jamais un devis existant.

⸻

4. Devis

4.1 Devis

Le Devis représente une proposition commerciale adressée à un client.

Données principales

* identifiant ;
* numéro ;
* date ;
* date de validité ;
* client ;
* snapshot client ;
* objet ;
* adresse d’intervention ;
* lignes ;
* remise ;
* acompte prévu ;
* notes ;
* statut ;
* date d’acceptation ;
* référence du BC associé ;
* dates de création/modification.

Numéro

DEV-00001-26

Statuts

* En attente ;
* Accepté ;
* Refusé ;
* Annulé.

Relations

Un devis :

* appartient à un client ;
* possède plusieurs lignes ;
* peut produire un BC ;
* peut être associé à plusieurs documents de facturation par l’intermédiaire du BC.

⸻

5. Ligne de devis

La LigneDevis est une photographie commerciale de la prestation au moment de son utilisation.

Données

* désignation ;
* description ;
* quantité ;
* unité ;
* prix unitaire ;
* remise ;
* type de prestation ;
* référence éventuelle au catalogue ;
* informations de garantie utiles ;
* montant calculé.

Règle

La ligne reste autonome après création du devis.

Une suppression ou modification du catalogue ne doit jamais modifier son contenu historique.

⸻

6. Bon de commande

6.1 BC

Le BC est le dossier métier central après acceptation du devis.

Il ne s’agit pas d’un simple état du devis.

Données principales

* identifiant ;
* numéro ;
* devis d’origine ;
* client ;
* état ;
* date de création ;
* date d’acceptation ;
* montant contractuel ;
* informations du chantier ;
* dates de début/fin éventuelles ;
* données nécessaires au suivi ;
* dates de création/modification.

Numéro

BCD-00001-26

Le vocabulaire fonctionnel reste BC.

États

* En cours ;
* Terminé ;
* Annulé.

Règles

À sa création :

BC = En cours

Un BC devient Terminé uniquement lorsque le solde est entièrement réglé.

Un BC annulé reste historiquement conservé.

Un BC annulé ne participe plus au CA engagé.

⸻

7. Relations du BC

Le BC peut être associé à :

* plusieurs factures ;
* plusieurs règlements indirectement via les factures ;
* plusieurs dépenses ;
* plusieurs interventions de planning ;
* plusieurs notes ;
* plusieurs PV ;
* plusieurs événements historiques ;
* plusieurs prestations garanties.

Le BC constitue donc le point de regroupement du dossier.

⸻

8. Facture

8.1 Facture

La Facture représente un document de facturation.

Types

* Acompte ;
* Situation ;
* Solde ;
* Avoir.

Il n’existe pas de type métier complete dans V6.

Données principales

* identifiant ;
* numéro ;
* type ;
* BC ;
* devis ;
* client ;
* snapshot client ;
* date d’émission ;
* date d’échéance ;
* lignes ;
* montant HT ;
* références éventuelles ;
* statut ;
* historique d’annulation ;
* dates de création/modification.

Numéro

FAC-00001-26

Le numéro est commun à tous les documents de facturation ordinaires.

Pour les acomptes :

ACP-00001-26

Pour les avoirs :

AVO-00001-26

⸻

9. Ligne de facture

La LigneFacture est une photographie des éléments facturés.

Elle ne dépend plus du catalogue ou du devis après émission.

Données

* désignation ;
* quantité ;
* unité ;
* prix ;
* remise ;
* montant ;
* référence éventuelle à la ligne d’origine.

⸻

10. Situation

Une Situation n’est pas une entité financière indépendante de la facture.

C’est une facture de type Situation avec des informations supplémentaires permettant de représenter la progression facturée.

Données spécifiques éventuelles

* progression cumulée ;
* montant déjà facturé ;
* montant supplémentaire facturé ;
* numéro d’ordre de situation ;
* période ou référence de situation.

Règle

La progression cumulée ne doit jamais permettre de dépasser le montant contractuel restant à facturer.

Si la progression atteint 100 %, le système doit produire une facture de Solde, et non une Situation finale.

⸻

11. Avoir

L’Avoir est une facture de type spécifique permettant de corriger financièrement une facturation existante.

Données spécifiques

* facture d’origine ;
* motif ;
* montant ;
* lignes ;
* éventuel remboursement.

Règle

L’avoir ne détruit jamais la facture d’origine.

La facture originale reste dans l’historique.

Son impact sur le calcul URSSAF est déterminé par le référentiel réglementaire applicable.

⸻

12. Règlement

Le Règlement devient une véritable entité indépendante.

Données

* identifiant ;
* facture ;
* date ;
* montant ;
* mode ;
* note éventuelle ;
* date de création.

Modes

* Espèces ;
* Chèque ;
* Virement ;
* Carte ;
* Autre.

Règle fondamentale

Une facture peut posséder plusieurs règlements.

Le reste à payer est calculé :

Montant dû − total des règlements applicables

Le statut de paiement de la facture est donc une information dérivée.

⸻

13. Statut de facture

Le statut n’est pas librement choisi par l’utilisateur.

Il est déterminé à partir de la situation financière de la facture et de son éventuelle annulation.

États :

* En attente ;
* Partiellement réglée ;
* Réglée ;
* En retard ;
* Annulée.

Une facture peut donc être :

Partiellement réglée + En retard

La notion d’en retard est transversale.

⸻

14. Dépense

La Dépense représente une charge enregistrée par l’entreprise.

Données

* identifiant ;
* numéro ;
* date ;
* montant ;
* catégorie ;
* fournisseur éventuel ;
* BC éventuel ;
* pièce jointe éventuelle ;
* note ;
* dates de création/modification.

Numéro

DEP-00001-26

Relation

Une dépense peut être :

* globale ;
* rattachée à un BC.

Aucune gestion du paiement fournisseur n’est prévue.

⸻

15. Fournisseur

Le Fournisseur est une entité indépendante.

Données

* identifiant ;
* code ;
* raison sociale / nom ;
* coordonnées ;
* notes ;
* statut ;
* dates de création/modification.

Code

FOU-001

Une dépense référence le fournisseur par identifiant.

⸻

16. Planning

Le Planning n’est pas limité aux BC.

Deux catégories d’événements sont nécessaires.

Événement BC

Exemples :

* intervention ;
* travaux ;
* rendez-vous lié au BC.

Événement général

Exemples :

* congé ;
* indisponibilité ;
* rendez-vous ;
* événement interne.

Règle

Le planning n’a pas d’autorité sur le cycle de vie du BC.

Une intervention planifiée ne rend pas automatiquement un BC actif ou terminé.

⸻

17. Note

La Note représente une information interne libre.

Données

* identifiant ;
* BC concerné ;
* contenu ;
* date de création ;
* date de modification.

Les notes ne constituent pas un système de tâches.

⸻

18. PV de réception

18.1 PV

Le PV représente un événement documentaire de réception.

Données

* identifiant ;
* numéro ;
* BC ;
* date ;
* type de réception ;
* réserves ;
* contenu ;
* référence éventuelle au PV d’origine ;
* date de création.

Numéro

PVR-00001-26

Types

* réception sans réserve ;
* réception avec réserves ;
* levée de réserves.

Le PV initial devient immuable après émission.

⸻

19. Levée de réserves

La levée de réserves n’est pas une modification du PV initial.

Elle crée un nouveau PV.

Exemple :

PVR-00001-26

puis :

PVR-00001-26-01

Le second PV référence le premier.

Le premier reste inchangé.

⸻

20. Garantie

La Garantie représente le suivi interne d’une obligation de garantie associée à une prestation.

Données

* BC ;
* prestation concernée ;
* type de garantie ;
* date de début du suivi interne ;
* date d’échéance ;
* état.

Types

* parfait achèvement ;
* biennale ;
* décennale.

Règle de déclenchement V6

Le suivi interne est créé lorsque le BC atteint 100 % facturé.

Il ne dépend pas :

* du PV ;
* de la réception ;
* des réserves ;
* de leur levée ;
* du paiement du solde.

Cette date est explicitement présentée comme :

Suivi interne BATORYA — date indicative.

⸻

21. Document

Le Document représente la matérialisation PDF d’un objet métier lorsqu’un document doit être produit.

Il ne doit pas devenir la source de vérité.

Principe

SQLite = source de vérité

Le PDF est une représentation générée à partir des données métier.

Les documents peuvent notamment correspondre à :

* devis ;
* factures ;
* avoirs ;
* PV.

Le BC reste un objet métier et non un document autonome obligatoire.

⸻

22. Historique

L’Historique représente les événements métier significatifs.

Exemples

* création d’un devis ;
* acceptation ;
* création d’un BC ;
* émission d’une facture ;
* règlement ;
* annulation ;
* création d’un avoir ;
* émission d’un PV ;
* modification importante.

L’historique doit rester indépendant de l’interface.

⸻

23. URSSAF

L’URSSAF ne constitue pas simplement une propriété du BC ou de la facture.

Il s’agit d’un domaine métier transversal exploitant les encaissements.

Il doit notamment gérer :

* périodes déclaratives ;
* CA encaissé ;
* contributions estimées ;
* CFP ;
* déclarations ;
* corrections ;
* historique ;
* version réglementaire applicable.

Principe

Une facture émise n’est pas automatiquement du CA encaissé.

Un règlement constitue l’événement financier permettant de déterminer l’encaissement.

⸻

24. Référentiel réglementaire

Le référentiel réglementaire est une composante distincte.

Il contient les paramètres nécessaires aux calculs réglementaires pour une période donnée.

Chaque version doit être identifiable.

Une nouvelle version remplace la version précédente pour les nouvelles périodes concernées, mais les anciennes versions restent conservées afin de reproduire les calculs historiques.

⸻

25. Paramètres entreprise

Les paramètres de l’entreprise ne sont pas une entité commerciale comme un Client ou un Fournisseur.

Ils représentent la configuration professionnelle utilisée par les différents services.

Ils comprennent notamment :

* identité ;
* coordonnées ;
* informations administratives ;
* informations bancaires facultatives ;
* paramètres commerciaux ;
* paramètres de sauvegarde ;
* configuration Gmail ;
* paramètres des Services BATORYA ;
* profil utilisateur.

Les paramètres URSSAF restent dans leur domaine dédié.

⸻

26. Utilisateur local

BATORYA Essentiel est une application locale.

Le profil utilisateur sert notamment à :

* identifier l’utilisateur local ;
* protéger l’accès ;
* gérer le mot de passe local.

Il n’existe pas de système de comptes utilisateurs distants ou de rôles dans le périmètre actuel.

⸻

27. Sauvegarde

La Sauvegarde n’est pas une donnée métier commerciale.

Elle représente un état exporté et versionné des données de l’application.

Le système doit permettre :

* création ;
* restauration ;
* validation ;
* rapport ;
* sauvegarde de sécurité avant restauration ;
* migration d’anciennes versions.

⸻

28. Licence

La licence est également séparée du domaine métier.

Elle représente l’autorisation d’utilisation de BATORYA Essentiel sur une machine donnée.

Elle est contrôlée par les Services BATORYA.

La licence ne doit jamais contenir ni transmettre les données commerciales de l’entreprise.

⸻

29. Vue d’ensemble des relations

Le cœur du modèle peut être représenté ainsi :

CLIENT
   │
   ├── DEVIS
   │      │
   │      └── LIGNES DEVIS
   │
   └── BC
          │
          ├── FACTURES
          │      │
          │      ├── LIGNES FACTURE
          │      ├── RÈGLEMENTS
          │      └── AVOIRS
          │
          ├── DÉPENSES
          │
          ├── PLANNING
          │
          ├── NOTES
          │
          ├── PV
          │      │
          │      └── LEVÉES DE RÉSERVES
          │
          └── GARANTIES

En parallèle :

CATALOGUE
   │
   └── PRESTATIONS
          │
          └── utilisées comme snapshots
              dans les LIGNES DEVIS
FOURNISSEUR
   │
   └── DÉPENSES
RÈGLEMENTS
   │
   └── URSSAF
          │
          └── PÉRIODES DÉCLARATIVES
RÉFÉRENTIEL RÉGLEMENTAIRE
   │
   └── URSSAF
PARAMÈTRES ENTREPRISE
   │
   ├── DOCUMENTS
   ├── PDF
   ├── EMAIL
   └── SERVICES BATORYA

⸻

30. Règle d’architecture fondamentale

Aucune entité métier ne doit connaître l’implémentation technique de la persistance.

Le domaine métier ne doit pas dépendre :

* de SQLite ;
* de React ;
* de Tauri ;
* du système de fichiers ;
* de l’interface graphique.

Les relations définies ici seront ensuite traduites en repositories et en tables SQLite.

⸻

31. Règles d’intégrité majeures

Le modèle V6 devra garantir notamment que :

1. un document conserve son historique après modification du référentiel ;
2. un devis accepté produit un BC de manière idempotente ;
3. un BC ne peut pas être terminé avant règlement complet du solde ;
4. un BC avec Situation émise ne peut pas être annulé directement ;
5. un BC ayant reçu un paiement ne peut pas être annulé directement ;
6. une facture peut recevoir plusieurs règlements ;
7. le reste à payer est calculé et non saisi manuellement ;
8. une facture payée ne disparaît jamais pour corriger une erreur ;
9. un avoir conserve la référence de la facture concernée ;
10. un BC annulé n’est plus comptabilisé dans le CA engagé ;
11. le suivi interne des garanties commence à 100 % facturé ;
12. un PV émis ne peut plus être modifié ;
13. une levée de réserves crée un nouveau PV ;
14. les calculs URSSAF utilisent les encaissements réels ;
15. les versions réglementaires historiques restent reproductibles ;
16. les montants sont manipulés avec une précision décimale exacte ;
17. les données métier restent locales ;
18. aucune fonctionnalité distante ne doit être nécessaire au fonctionnement normal des données métier.

⸻

32. Statut de cette phase

Cette phase définit le modèle conceptuel métier de BATORYA Essentiel V6.

Elle ne définit pas encore :

* les tables SQLite ;
* les types SQL ;
* les index ;
* les repositories ;
* les services TypeScript ;
* les composants React ;
* les commandes Tauri.

Ces éléments seront définis dans les phases suivantes.

Prochaine phase : modèle de données SQLite V6.
