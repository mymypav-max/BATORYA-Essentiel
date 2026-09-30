BATORYA Essentiel V6

Cahier des charges fonctionnel et architectural définitif

Version : V6.1 — CDC consolidé le 01/10/2026

Historique des versions

* V6 — CDC initial gelé.
* V6.1 — consolidation des décisions validées E-01 à E-09 et des décisions déjà actées dans les invariants, le modèle métier et le modèle de données SQLite V3.7.

Le présent CDC V6.1 intègre les corrections E-01 à E-09. Le fichier `cdc-errata-v6.md` est conservé comme registre historique de traçabilité ; ses corrections ne constituent pas une couche corrective à appliquer séparément au CDC V6.1.

⸻

1. Objet du projet

BATORYA V6 est une application desktop locale destinée aux micro-entrepreneurs du BTP exerçant une activité de prestation de services, relevant du régime micro-entrepreneur et n’étant pas assujettis à la TVA dans le cadre couvert par BATORYA Essentiel.

BATORYA centralise notamment :

* clients ;
* catalogue de prestations ;
* devis ;
* BC ;
* facturation ;
* règlements ;
* planification ;
* PV ;
* garanties ;
* notes ;
* dépenses ;
* suivi URSSAF ;
* analyses de gestion ;
* documents PDF ;
* sauvegardes ;
* paramètres ;
* licence et mises à jour.

BATORYA est un outil de gestion et d’assistance, et non un logiciel comptable ou un service administratif officiel.

⸻

2. Périmètre BATORYA Essentiel

Inclus

Le périmètre V6 couvre exclusivement :

* micro-entrepreneur ;
* activité de prestation de services ;
* secteur BTP ;
* absence de gestion de TVA ;
* gestion locale des données ;
* devis ;
* BC ;
* factures ;
* règlements ;
* avoirs ;
* clients ;
* catalogue ;
* planification ;
* PV ;
* garanties ;
* notes ;
* dépenses ;
* suivi URSSAF ;
* analyses de gestion ;
* documents ;
* sauvegardes ;
* licence ;
* mises à jour logicielles ;
* mises à jour des références réglementaires.

Exclus

Ne font pas partie de BATORYA Essentiel V6 :

* BATORYA Entreprise ;
* gestion de salariés ;
* pointage salarié ;
* gestion de paie ;
* TVA ;
* gestion générale des régimes fiscaux ;
* BNC ;
* comptabilité complète ;
* rapprochement bancaire ;
* télétransmission URSSAF ;
* déclaration URSSAF automatique ;
* gestion automatique des emails ;
* gestion des échéances fournisseurs ;
* gestion du paiement des dépenses ;
* avenants ;
* gestion de chantier indépendante du BC ;
* compte utilisateur en ligne ;
* stockage cloud des données métier ;
* Google Drive ;
* banque connectée.

⸻

3. Principes fonctionnels

BATORYA V6 doit rester :

* simple ;
* local ;
* utilisable hors connexion ;
* cohérent ;
* traçable ;
* prévisible ;
* non intrusif.

BATORYA reste utilisable hors connexion, sauf restriction temporaire liée à la validation de licence, conformément au chapitre 41.

Les opérations importantes doivent être atomiques et ne jamais laisser une donnée dans un état incohérent.

BATORYA doit distinguer clairement :

* donnée ;
* calcul ;
* information ;
* estimation ;
* alerte ;
* règle réglementaire.

Aucune donnée ne doit être inventée automatiquement lorsqu’elle n’est pas disponible.

⸻

4. Architecture technique

La V6 est une nouvelle implémentation basée sur :

* Tauri 2 ;
* React ;
* TypeScript ;
* Vite ;
* SQLite.

Architecture logique :

Interface → services applicatifs → règles métier → repositories → SQLite

Les composants ne doivent pas accéder directement aux données d’un autre module.

Les commandes natives Tauri doivent rester limitées et contrôlées.

Le renderer ne doit pas disposer d’un accès arbitraire au système de fichiers.

⸻

5. Stockage des données

SQLite constitue la source de vérité des données métier.

Les données métier ne sont pas stockées dans le dossier de travail.

Le changement du dossier de travail ne doit donc :

* ni déplacer SQLite ;
* ni modifier les données métier ;
* ni nécessiter une migration des données.

Le dossier de travail concerne principalement le stockage des documents générés et des sauvegardes.

⸻

6. Gestion monétaire

Les montants monétaires sont manipulés avec une représentation décimale exacte. SQLite ne doit pas utiliser REAL comme représentation exacte d’un montant.

BATORYA utilise une représentation décimale fiable, avec stockage canonique en texte décimal et calcul via une bibliothèque décimale adaptée.

Les calculs intermédiaires conservent leur précision et aucun arrondi prématuré n’est effectué.

Les montants commerciaux finaux (totaux, acomptes, factures, règlements, dépenses) sont à 2 décimales. L’arrondi est HALF_UP et intervient une seule fois par ligne ; le total est obtenu par somme des lignes arrondies, moins la remise globale arrondie.

Les quantités, prix unitaires et remises en valeur peuvent conserver une précision libre lorsqu’elle est prévue par le modèle. Les pourcentages saisis utilisent 2 décimales.

Aucune perte silencieuse de précision n’est autorisée. Pour l’import historique, **V6 ne réarrondit pas les données** : le convertisseur externe porte les règles de transformation V2, notamment l’arrondi nécessaire des totaux historiques non arrondis, puis produit un `import-v6.json` conforme. V6 rejette tout fichier dont les montants ne respectent pas la précision de leur famille décimale.

⸻

7. Entreprise et profil utilisateur

Identité de l’entreprise

Les paramètres d’entreprise comprennent notamment :

* nom et prénom de l’entrepreneur ;
* entrepreneur individuel / EI lorsque nécessaire ;
* nom commercial éventuel ;
* adresse ;
* téléphone ;
* adresse email ;
* SIREN ;
* SIRET ;
* autres informations d’identification utiles ;
* coordonnées bancaires éventuellement affichées sur les documents.

Les coordonnées bancaires sont facultatives.

Profil local

BATORYA peut disposer d’un profil local permettant notamment :

* affichage du nom de l’utilisateur ;
* mot de passe local ;
* identification visuelle de l’utilisateur.

Il n’existe pas de compte utilisateur en ligne ni de système complexe de rôles.

Le mot de passe n’est jamais stocké en clair.

Mot de passe oublié

En cas de blocage lié à un mot de passe oublié :

* BATORYA ne récupère pas le mot de passe ;
* l’utilisateur contacte le support BATORYA ;
* le support peut générer une procédure de déblocage ;
* le mécanisme repose sur un code/token temporaire lié à l’installation ;
* aucune donnée métier n’est transmise au support ;
* après validation, l’utilisateur peut définir un nouveau mot de passe.

⸻

8. Paramètres généraux

Le module Paramètres regroupe uniquement les réglages réellement généraux.

Paramètres commerciaux

* délai de paiement par défaut ;
* modes de paiement proposés ;
* mention commerciale standard ;
* conditions particulières standard.

Ces valeurs servent de préremplissage mais peuvent être adaptées lorsque cela est autorisé.

Les mentions légalement obligatoires ne peuvent pas être supprimées simplement par préférence utilisateur.

Sauvegardes

Le module permet :

* activation/désactivation des sauvegardes automatiques ;
* fréquence lorsque nécessaire ;
* sauvegarde manuelle ;
* affichage/ouverture du dossier de sauvegarde ;
* affichage du dernier état de sauvegarde.

Le moteur de sauvegarde est centralisé.

Gmail

Le module permet :

* connexion du compte Gmail ;
* déconnexion ;
* affichage de l’état de connexion ;
* affichage du compte utilisé ;
* test de connexion.

Les emails sont toujours envoyés manuellement.

Services BATORYA

Le module affiche notamment :

* état de licence ;
* dernière vérification ;
* version installée ;
* disponibilité éventuelle d’une mise à jour ;
* version du référentiel réglementaire ;
* dernière communication réussie.

Les paramètres URSSAF ne sont pas dupliqués dans ce module.

⸻

9. Dossier de travail et documents

L’utilisateur choisit un dossier de travail local.

Ce dossier sert principalement de racine de stockage documentaire.

Modifier le dossier de travail :

* ne déplace pas SQLite ;
* ne modifie pas les données métier ;
* ne copie pas automatiquement les anciens documents ;
* fait simplement utiliser le nouveau chemin pour les futurs documents.

Les anciens fichiers restent dans leur ancien emplacement.

Sauvegarde lors du changement de dossier

Lors d’un changement de dossier de travail, BATORYA propose une sauvegarde immédiate avant le changement.

Cette sauvegarde reste dans l’ancien dossier avec les sauvegardes existantes.

Aucune copie automatique des anciennes sauvegardes vers le nouveau dossier n’est effectuée.

⸻

10. Structure documentaire

Les documents sont classés par année.

Structure générale :

Dossier de travail/
├── 2026/
│   ├── Devis/
│   │   ├── En_attente/
│   │   ├── Accepte/
│   │   ├── Refuse/
│   │   └── Annule/
│   ├── Factures/
│   │   ├── Acomptes/
│   │   ├── Situations/
│   │   ├── Soldes/
│   │   └── Avoirs/
│   └── PV/
└── Sauvegardes/

Le BC n’est pas un document généré et ne possède donc pas de dossier documentaire.

Le PV est un document généré et possède son propre dossier annuel.

⸻

11. Catalogue des prestations

Le catalogue constitue la base des prestations proposées dans les devis.

Le catalogue V6 doit reprendre le catalogue réel validé de V5.16.

Le catalogue réel de référence contient 205 prestations prédéfinies. Après suppression de ELE-008, le catalogue par défaut V6 comporte donc 204 prestations.

La liste doit être récupérée depuis le catalogue réel audité, et non reconstruite manuellement.

Garanties

Les garanties peuvent être gérées depuis le catalogue de prestations.

Une prestation peut disposer d’un ou plusieurs types de garantie par défaut.

Les garanties sont notamment :

* parfait achèvement : 1 an ;
* biennale : 2 ans ;
* décennale : 10 ans.

Les règles de garantie sont conservées dans les snapshots des documents historiques.

Suppression de Cat6

Cat6 n’est pas une catégorie.

Il s’agit d’une prestation spécifique :

ELE-008 — F+P prise RJ45 Cat6 avec câblage

Cette prestation doit être supprimée du catalogue V6.

⸻

12. Clients

Les clients constituent un référentiel indépendant.

Ils peuvent être utilisés par :

* devis ;
* BC ;
* factures ;
* planification ;
* PV ;
* garanties ;
* notes ;
* analyses.

Les documents historiques conservent les informations nécessaires à leur propre cohérence même si la fiche client évolue ensuite.

⸻

13. Devis

Le devis est le document commercial préalable à l’acceptation d’une prestation.

Chaque devis possède notamment :

* numéro ;
* client ;
* date ;
* lignes de prestations ;
* quantités ;
* prix ;
* conditions ;
* mentions nécessaires ;
* statut ;
* historique.

Numérotation : préfixe DEV.

États

Le devis peut notamment être :

* en attente ;
* accepté ;
* refusé ;
* annulé.

Classement PDF

Les PDF sont déplacés selon leur état :

* Devis/En_attente
* Devis/Accepte
* Devis/Refuse
* Devis/Annule

⸻

14. Modification d’un devis accepté

Un devis accepté reste modifiable tant qu’il n’est pas gelé.

Le gel est irréversible et intervient au premier événement suivant :
* encaissement actif, même partiel, d’un acompte ;
* émission d’une situation ;
* émission d’un solde.

Un acompte émis mais non encaissé ne gèle pas le devis ni le BC.

Lorsqu’un devis accepté non gelé est modifié :
* l’historique est conservé ;
* le BC associé est régénéré dans la même transaction ;
* les snapshots, lignes, garanties de lignes et montant contractuel du BC restent cohérents ;
* tout acompte émis mais non encaissé est annulé automatiquement dans la même transaction.

Un devis refusé ou annulé est immuable.

Après le gel :
* le devis et le BC sont figés sur leurs éléments commerciaux structurants ;
* les lignes, garanties de lignes, remises, acompte prévu, client, chantier, snapshots et montant contractuel ne sont plus modifiables.

Les travaux supplémentaires ne donnent pas lieu à un avenant dans Essentiel.

Ils nécessitent :

nouveau devis → acceptation → nouveau BC indépendant.

⸻

15. BC — Dossier central

Le BC est le point central du workflow BATORYA.

Il remplace toute notion fonctionnelle d’« Affaire ».

Le BC peut correspondre, dans le langage courant, à un chantier ou une affaire, mais BATORYA ne crée pas une entité fonctionnelle distincte.

Le BC relie notamment :

* client ;
* devis accepté ;
* facturation ;
* règlements ;
* planification ;
* notes ;
* PV ;
* garanties.

Les dépenses peuvent être globales ou rattachées à un BC.

⸻

16. Création et cycle de vie du BC

Lorsqu’un devis est accepté :

* le BC est créé automatiquement ;
* la création est atomique ;
* l’opération est idempotente ;
* aucun double BC ne doit être créé pour le même devis accepté.

Le BC démarre à l’état :

En cours

Le statut métier n’est pas librement modifiable par l’utilisateur.

Passage à Terminé

Le BC devient **Terminé** si et seulement si :
* un solde actif existe ;
* la somme des restes dus des factures actives hors avoir est nulle.

Un solde à 0 € ne suffit pas s’il reste un acompte ou une situation dû.

Le passage à Terminé est dérivé du service métier et n’est pas librement saisi par l’utilisateur. Une annulation de règlement ou d’avoir peut faire revenir le BC à En cours lorsque les conditions de Terminé ne sont plus réunies.

⸻

17. Annulation du BC

L’annulation du BC est possible uniquement dans les conditions prévues.

Annulation directe interdite dès qu’une facture autre qu’un acompte non réglé existe, notamment lorsqu’un solde impayé existe sans situation.

Un acompte non réglé peut être annulé automatiquement avec le BC lorsqu’une modification autorisée du devis/BC l’exige.

Une Situation émise, même annulée, interdit toujours l’annulation directe du BC.

Un encaissement interdit également l’annulation directe. La correction passe alors par l’annulation de facture ou l’avoir selon le cas.

Situation émise

Si une Situation a été émise, le BC ne peut plus être annulé directement, même si cette Situation est encore impayée.

Une Situation matérialise un avancement de travaux déjà commencé.

Paiement encaissé

Une fois qu’un paiement a été encaissé :

l’annulation directe du BC est interdite.

Une facture déjà payée n’est pas supprimée.

Elle est traitée par le mécanisme de facturation approprié, notamment par avoir.

Conséquences de l’annulation

Lorsqu’un BC peut légalement être annulé :

* le devis passe à Annulé ;
* son PDF est placé dans Devis/Annule ;
* le BC reste conservé ;
* la facture d’acompte annulée reste conservée lorsqu’elle existe ;
* aucune nouvelle opération de facturation ne peut être effectuée sur ce BC.

⸻

18. Facturation

BATORYA V6 gère quatre types fonctionnels :

* Acompte
* Situation
* Solde
* Avoir

Le type technique historique `complete` n’est pas conservé comme type métier V6.

Solde

La facture finale est toujours une facture de solde.

Même lorsqu’aucune facture préalable n’existe, la facture finale est de type Solde.

Acompte

Préfixe :

ACP

Les numéros V6 suivent la convention uniforme définie par le modèle : DEV, BCD, FAC, ACP, AVO, PVR, DEP suivis du compteur sur 5 chiffres et de l’année sur 2 chiffres.

Les devis, factures, acomptes, situations, soldes, avoirs et PV importés peuvent conserver leur numéro historique lorsqu’il a déjà été remis au client. Les BC et codes clients importés utilisent les formats V6 ; les fournisseurs ne sont pas importés.

⸻

19. Séquence de facturation

La séquence fonctionnelle permet notamment :

* acompte ;
* situations ;
* solde ;
* avoir.

Plusieurs situations peuvent être émises.

Le solde clôture la facturation commerciale du BC.

Les situations et les soldes partagent la même séquence FAC. Les numéros ne sont pas configurables manuellement et un numéro déjà attribué n’est jamais réutilisé ; les trous de numérotation sont acceptables.

Les factures historiques restent conservées.

⸻

20. Règlements

Une facture peut recevoir plusieurs règlements.

Chaque règlement comporte :

* date ;
* montant ;
* mode de paiement.

Modes notamment :

* espèces ;
* chèque ;
* virement ;
* carte ;
* autre.

Une facture n’est considérée comme totalement réglée que lorsque la totalité du montant dû a effectivement été enregistrée.

Un paiement partiel laisse apparaître le solde restant.

BATORYA ne réalise pas de rapprochement bancaire.

⸻

21. États des factures

Les états fonctionnels sont :

* En attente : aucun paiement ;
* Partiellement réglée : paiement(s) enregistré(s), solde restant ;
* Réglée : solde à zéro ;
* En retard : échéance dépassée avec un solde restant ;
* Annulée.

En retard est un indicateur transversal.

Une facture peut donc être :

Partiellement réglée — En retard

L’état de paiement et l’information d’échéance ne sont pas artificiellement exclusifs.

⸻

22. Avoirs

Un avoir constitue le mécanisme de correction ou de restitution après facturation lorsque cela est nécessaire.

Une facture payée n’est pas supprimée.

Elle reste dans l’historique et l’avoir constitue un document distinct.

L’avoir doit conserver :

* son origine ;
* son montant ;
* sa date ;
* son lien avec le document concerné ;
* son historique.

Le traitement d’un avoir ou remboursement dans le calcul du CA pris en compte pour l’URSSAF est défini par le référentiel réglementaire versionné.

BATORYA ne code pas cette règle en dur.

Le moteur applique la règle correspondant à la version réglementaire applicable à la période concernée.

⸻

23. PV et réception

Le PV est facultatif.

Il n’est jamais obligatoire pour terminer le workflow d’un BC.

Une réception peut être :

* sans réserve ;
* avec réserves.

Le PV original est immuable.

Une levée de réserves constitue un second PV autonome.

Le second PV référence le PV initial et ne modifie jamais le document original.

Numérotation

Le numéro du PV initial est réutilisé avec suffixe :

* PVR-00001-26
* PVR-00001-26-01
* PVR-00001-26-02

La levée de réserves ne modifie pas le suivi interne des garanties.

⸻

24. Garanties

BATORYA suit trois catégories :

* parfait achèvement ;
* biennale ;
* décennale.

Le suivi des garanties est un suivi interne BATORYA.

Déclenchement

Les garanties sont générées à l’émission du **premier solde actif**, c’est-à-dire au franchissement de 100 % facturé.

La création est idempotente : la première date de déclenchement est conservée et aucune garantie n’est recréée lors d’une réémission ou à partir de données historiques importées.

Le déclenchement ne dépend pas :
* du paiement du solde ;
* de la réception ;
* de l’existence d’un PV ;
* de la présence de réserves ;
* de la levée des réserves.

Une garantie générée n’est ni modifiée ni supprimée par l’annulation du solde, un avoir ou un règlement.

Cela est distinct du passage du BC à Terminé : les garanties sont déclenchées par le premier solde actif, alors que Terminé dépend du solde actif et de l’absence de reste dû sur les factures actives hors avoir.

Date de garantie

La date affichée dans BATORYA est une date de suivi interne.
