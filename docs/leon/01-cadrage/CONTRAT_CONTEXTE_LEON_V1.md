# CONTRAT_CONTEXTE_LEON_V1.md

**Projet :** BATORYA Essentiel V6  
**Statut :** document de travail — cadrage du contrat de contexte  
**Périmètre :** Léon V1 exclusivement

## 1. Objet du document

Ce document définit les principes selon lesquels BATORYA fournit à Léon les informations nécessaires à la compréhension et au traitement d'une demande utilisateur.

Il complète le document `CADRAGE_FONCTIONNEL_LEON_V1.md`.

Il vise à garantir :
- une compréhension rapide des demandes ;
- une utilisation pertinente du contexte de BATORYA ;
- la continuité conversationnelle malgré les changements d'écran ;
- la limitation des ressources consommées ;
- la minimisation des données transmises ;
- la fiabilité des réponses ;
- l'absence de capacité de modification des données métier par Léon.

Ce document ne définit ni une liste exhaustive d'intents, ni une architecture technique définitive.

Les familles d'intents et leurs détails seront construits progressivement, au rythme du développement de BATORYA V6 et de l'apparition de fonctionnalités réellement utilisables.

## 2. Principes déjà validés

### 2.1 Construction du contexte à la demande

Léon ne doit traiter aucune demande ni solliciter le modèle IA en arrière-plan lorsque l'utilisateur ne fait pas appel à lui.

Le contexte nécessaire est construit au moment de la sollicitation.

La navigation dans BATORYA ne doit pas déclencher à elle seule un traitement IA.

### 2.2 Contexte courant et mémoire conversationnelle distincts

Deux informations doivent être gérées séparément :

- **Le contexte courant**, qui décrit la situation présente de l'utilisateur dans BATORYA.
- **Le contexte conversationnel**, qui conserve les éléments nécessaires à la continuité de l'échange.

Le contexte courant évolue avec la navigation. Le contexte conversationnel peut persister indépendamment de cette navigation.

### 2.3 Continuité de la demande

Un changement d'écran ou de module ne doit pas annuler automatiquement une demande en cours ni interrompre la conversation.

Léon doit pouvoir poursuivre une demande initiale dans un nouvel écran lorsque le déplacement de l'utilisateur s'inscrit dans la résolution du problème.

### 2.4 Mémoire conversationnelle

Le principe retenu est une conservation du contexte conversationnel pendant une période d'inactivité de 30 minutes avant expiration.

Cette durée concerne la mémoire conversationnelle. Elle ne constitue ni une durée maximale de traitement d'une demande ni une durée de maintien du modèle en mémoire vive.

Les modalités exactes de démarrage et de renouvellement du délai restent à préciser.

### 2.5 Lecture seule et fiabilité

Léon ne peut pas modifier les données métier, créer de document, enregistrer une opération ou déclencher une action d'écriture.

Les données métier nécessaires sont obtenues par des mécanismes contrôlés en lecture seule.

Léon ne doit pas inventer une information absente. Il doit distinguer ce qui est vérifié de ce qui est inconnu et demander une précision lorsque cela est nécessaire.

## 3. Le contexte courant

### 3.1 Finalité

Le contexte courant permet à Léon de comprendre où se trouve l'utilisateur au moment de sa demande.

Il ne doit pas dépendre uniquement d'une déduction du modèle à partir de la formulation de l'utilisateur.

BATORYA doit fournir les informations de navigation qu'il connaît de manière fiable.

### 3.2 Informations candidates

Le contexte courant pourra comprendre, selon leur disponibilité et leur utilité :

- le chapitre métier actif ;
- le module actif ;
- l'écran courant ;
- l'onglet ou l'étape active ;
- l'objet sélectionné ou consulté ;
- les informations de navigation nécessaires à l'interprétation de la demande.

Ces éléments constituent une base de conception, pas une obligation de transmettre systématiquement tous les champs.

Le contrat minimal exact reste à définir.

### 3.3 Objet sélectionné

Lorsqu'un objet métier est pertinent, BATORYA peut transmettre une référence permettant de l'identifier sans ambiguïté.

Exemples : un client, un devis, une facture ou un règlement.

L'identifiant de l'objet ne signifie pas que Léon connaît toutes les données associées. Les informations supplémentaires doivent être récupérées uniquement si elles sont nécessaires à la demande et si leur accès est autorisé.

Si aucun objet n'est sélectionné, Léon ne doit pas en inventer un ni supposer que la demande concerne un objet particulier.

### 3.4 Actualisation

Le contexte courant doit correspondre à la situation réelle au moment où une nouvelle demande est traitée.

Si l'utilisateur change de module entre deux interactions, la nouvelle sollicitation doit prendre en compte le nouvel écran sans effacer automatiquement la demande précédente.

Le suivi de navigation doit être réalisé sans traitement permanent du modèle IA.

## 4. Récupération des données métier

### 4.1 Principe

Le contexte courant ne doit pas contenir systématiquement toutes les données métier.

Lorsqu'une demande nécessite des informations complémentaires, BATORYA peut les récupérer par l'intermédiaire de services applicatifs autorisés, en lecture seule.

Exemples :
- rechercher un client dans le carnet clients ;
- vérifier le statut d'un devis ;
- consulter les échéances d'une facture ;
- récupérer les informations nécessaires à l'explication d'un blocage métier.

### 4.2 Récupération ciblée

La récupération doit être limitée aux informations utiles à la demande.

Léon ne doit pas recevoir une fiche complète ou un ensemble de données métier simplement parce qu'il pourrait éventuellement en avoir besoin.

Le mécanisme de récupération doit respecter les règles métier et les autorisations de BATORYA.

### 4.3 Autorité des informations

Les données métier et les règles vérifiées de BATORYA constituent les références factuelles.

Le modèle IA ne doit pas remplacer une règle métier par une supposition ni présenter une interprétation comme un résultat officiellement établi par BATORYA.

Lorsqu'une information nécessaire n'est pas disponible ou ne peut pas être vérifiée, Léon doit le signaler.

## 5. Le contexte conversationnel

### 5.1 Finalité

Le contexte conversationnel permet à Léon de conserver le fil d'une demande et d'éviter que l'utilisateur ait à répéter des informations déjà établies.

Il pourra comprendre, lorsque ces éléments sont utiles :
- la demande initiale ;
- l'objectif poursuivi ;
- les précisions fournies par l'utilisateur ;
- les informations déjà vérifiées ;
- les questions et réponses pertinentes ;
- l'état d'avancement de la résolution ;
- les références aux objets métier concernés.

Le contenu exact et le format technique de cette mémoire restent à concevoir.

### 5.2 Continuité malgré la navigation

La navigation dans BATORYA ne doit pas être interprétée comme une fin de conversation.

**Exemple : recherche d'un client lors de la création d'un devis**

1. L'utilisateur commence la création d'un devis.
2. Il indique à Léon qu'il ne trouve pas un client pourtant enregistré.
3. Avant que Léon ait terminé, l'utilisateur ouvre le carnet clients.
4. Léon doit prendre en compte le nouvel écran tout en conservant l'objectif initial : retrouver le client pour poursuivre la création du devis.
5. Léon peut poursuivre l'accompagnement à partir du carnet clients si les informations disponibles le permettent.

Le changement de module actualise le contexte courant, mais ne supprime pas le contexte conversationnel.

### 5.3 Gestion des références

Lorsqu'une nouvelle demande fait référence à un élément précédent, Léon doit exploiter le contexte conversationnel si celui-ci permet d'identifier cet élément de façon suffisamment fiable.

Si plusieurs interprétations restent possibles et conduisent à des réponses différentes, Léon doit poser une question ciblée.

Il ne doit ni oublier systématiquement le contexte précédent, ni supposer qu'une référence est certaine lorsqu'elle ne l'est pas.

## 6. Expiration de la mémoire

Le principe d'une expiration après 30 minutes d'inactivité est validé.

Les modalités suivantes restent à préciser :

- le point de départ du délai ;
- les interactions qui renouvellent le délai ;
- le traitement d'une demande encore en cours ;
- le comportement lorsque la mémoire expire ;
- les données conservées après expiration ;
- la manière de reprendre une demande dont le contexte n'est plus disponible.

Après expiration, Léon ne doit pas prétendre disposer d'informations conversationnelles qui ne sont plus conservées.

Il pourra demander à l'utilisateur de rappeler les éléments nécessaires à la reprise de la demande.

L'expiration de la mémoire conversationnelle ne doit pas être confondue avec la suppression des données métier de BATORYA.

## 7. Sobriété des ressources

Le contrat de contexte doit respecter les contraintes de fonctionnement local de Léon.

Les principes retenus sont les suivants :

- aucun traitement IA lorsque l'utilisateur ne sollicite pas Léon ;
- aucune analyse IA permanente de l'écran ;
- aucune récupération systématique de l'ensemble des données métier ;
- aucun chargement de contexte inutile ;
- récupération ciblée des informations complémentaires ;
- séparation entre suivi de navigation, mémoire conversationnelle et traitement du modèle.

Le maintien d'une mémoire conversationnelle ne doit pas entraîner un traitement continu du modèle.

Les exigences de performance et la quantité de contexte supportable devront être évaluées lors des essais sur une configuration matérielle représentative.

## 8. Confidentialité et limites d'accès

Le contexte transmis à Léon doit être limité aux informations nécessaires à la demande.

Léon ne doit pas :
- disposer d'un accès libre à la base SQLite ;
- parcourir librement les fichiers de l'ordinateur ;
- recevoir systématiquement toutes les données d'un client ou d'un document ;
- utiliser des données qui ne sont pas disponibles dans le contexte ou accessibles par un mécanisme autorisé ;
- effectuer une opération d'écriture métier.

Les mécanismes techniques d'accès devront garantir ces limites indépendamment du comportement du modèle.

Les modalités précises de stockage, de protection et de suppression du contexte conversationnel restent à définir.

## 9. Cas de test à prévoir

Le contrat de contexte devra être vérifié notamment sur les situations suivantes :

1. Demande simple depuis un écran connu.
2. Demande nécessitant une récupération métier complémentaire.
3. Demande pour laquelle une information indispensable est absente.
4. Changement de module avant la réponse de Léon.
5. Changement de module entre deux messages d'une même conversation.
6. Référence à un document évoqué précédemment.
7. Référence ambiguë à plusieurs objets possibles.
8. Expiration de la mémoire après 30 minutes d'inactivité.
9. Tentative de réponse fondée sur une donnée non disponible.
10. Vérification de l'absence de traitement IA en arrière-plan lors de la navigation.

Ces cas devront évoluer avec les fonctionnalités réellement disponibles dans BATORYA V6.

## 10. Points restant à préciser

Les éléments suivants ne sont pas considérés comme définitivement décidés :

- le format technique du contexte courant ;
- les champs exacts du contexte minimal ;
- les services de lecture exposés à Léon ;
- le format de la mémoire conversationnelle ;
- le détail du cycle de vie de la mémoire de 30 minutes ;
- le traitement des demandes en cours lors d'une navigation ;
- les modalités de protection et de suppression de la mémoire ;
- les critères mesurables de performance.

Les familles d'intents et le catalogue des intents seront définis progressivement pendant le développement de V6. Le contrat de contexte devra pouvoir évoluer avec eux sans nécessiter une refonte générale.

## 11. Suite du travail

Après validation de ce document :

1. préciser les champs du contexte minimal et les responsabilités de BATORYA ;
2. détailler le cycle de vie de la mémoire conversationnelle ;
3. confronter progressivement le contrat aux écrans et fonctionnalités développés dans V6 ;
4. définir les familles et intents au fil des besoins constatés ;
5. construire les tests de fiabilité et de continuité ;
6. étudier les solutions techniques locales et mesurer leur coût réel.

**Statut :** document de travail à valider. Il formalise les décisions déjà prises et identifie les points encore ouverts, sans figer prématurément l'architecture ni le catalogue d'intents.
