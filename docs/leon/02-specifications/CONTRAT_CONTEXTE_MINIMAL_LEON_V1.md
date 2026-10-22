# Contrat de contexte minimal de Léon — BATORYA Essentiel V6

**Statut :** proposition de conception — non validée  
**Version :** V1 de travail  
**Périmètre :** BATORYA Essentiel V6 exclusivement  
**Dépendance :** `docs/leon/01-cadrage/CADRAGE_FONCTIONNEL_LEON_V1.md`

> Ce document traduit le cadrage fonctionnel en proposition de contrat entre BATORYA et Léon. Il ne définit pas encore une API technique, ne crée aucun service applicatif et ne modifie aucune règle métier. Les champs, exemples et mécanismes ci-dessous restent à valider.

## 1. Objectif

Définir le minimum d'informations fiables dont Léon a besoin pour interpréter une demande, ainsi que les règles d'actualisation du contexte et de récupération ciblée des données métier.

Le contrat doit permettre de :
- situer la demande dans l'interface BATORYA ;
- identifier sans ambiguïté un objet métier lorsqu'un objet est explicitement sélectionné ;
- enrichir le contexte uniquement si la demande le nécessite ;
- distinguer les informations connues, absentes, indisponibles ou non vérifiées ;
- maintenir la séparation entre contexte courant, données métier récupérées et mémoire conversationnelle ;
- garantir que Léon n'a aucun accès direct à SQLite, au système de fichiers ou à une capacité d'écriture métier.

## 2. Principes directeurs

1. **BATORYA est la source du contexte d'interface.** Léon ne doit pas déduire le module actif à partir du seul texte utilisateur lorsque l'application peut le fournir.
2. **Le contexte est construit à la demande.** Ouvrir un écran ou changer d'onglet actualise l'état de navigation, mais ne déclenche pas à lui seul un traitement IA.
3. **Minimal par défaut.** Ne transmettre que les informations nécessaires pour interpréter la demande. Ne pas injecter une fiche client, un devis complet ou un lot de données par simple précaution.
4. **Référence ne signifie pas contenu.** Une référence d'objet permet de demander une lecture autorisée ; elle ne signifie pas que ses champs métier ont déjà été chargés.
5. **Données et règles métier font autorité.** Les données factuelles et les règles vérifiées proviennent de BATORYA ou d'une source explicitement reconnue, pas d'une supposition du modèle.
6. **Lecture seule.** Les enrichissements passent par des services applicatifs autorisés et contrôlés. Aucun accès direct de Léon à SQLite ou au système de fichiers.
7. **Séparation des contextes.** La navigation courante, les données métier lues pour une demande et la mémoire conversationnelle sont trois éléments distincts.
8. **Pas de présomption.** Une information non présente dans le contexte n'est pas automatiquement inexistante dans BATORYA.
9. **Échec explicite.** Une lecture échouée, ambiguë ou impossible doit rester identifiable comme telle ; elle ne doit pas être remplacée par une valeur inventée.

## 3. Les trois composantes à ne pas confondre

### 3.1 Contexte courant de navigation

Il décrit la position actuelle de l'utilisateur dans BATORYA : chapitre/module, écran, onglet ou étape si ces éléments existent, et éventuel objet sélectionné. Il est actualisé par BATORYA indépendamment de toute inférence du modèle.

### 3.2 Données métier récupérées pour une demande

Ce sont les informations précises obtenues, si nécessaire, au moyen d'un service applicatif autorisé en lecture seule : par exemple le statut d'un devis ou les échéances d'une facture. Ces données sont associées à la demande qui les a justifiées et ne doivent pas être conservées indéfiniment dans le contexte courant.

### 3.3 Mémoire conversationnelle

Elle conserve les éléments nécessaires à la continuité du dialogue : objectif initial, précisions fournies, résultats vérifiés et progression. Son format, son stockage et son expiration relèvent du document distinct consacré à son cycle de vie. Le présent contrat ne redéfinit pas la règle d'expiration de 30 minutes déjà retenue dans le cadrage.

## 4. Contenu minimal proposé

Le contrat devrait être composé de deux parties logiques : un **contexte courant** fourni par BATORYA et un **contexte de requête** construit lorsque l'utilisateur sollicite Léon.

### 4.1 Contexte courant

| Élément proposé | Rôle | Règle |
|---|---|---|
| Identifiant/version du contrat | Identifier la structure transmise | Sert à détecter une version non prise en charge ; format technique à choisir |
| Chapitre ou module actif | Situer la demande dans BATORYA | Valeur contrôlée par l'application, si disponible |
| Identifiant logique de l'écran | Identifier la vue active | Utiliser un identifiant stable défini par l'application, pas le titre affiché seul |
| Onglet ou étape active | Préciser la position dans un parcours | Facultatif : seulement si la vue en possède un |
| Objet métier sélectionné | Identifier l'objet courant | Facultatif ; type et identifiant stable, jamais un objet deviné par Léon |
| Instant d'actualisation | Apprécier la fraîcheur du contexte | Horodatage produit par BATORYA ; format à définir |
| État de disponibilité | Signaler si le contexte est complet ou partiel | Distinguer « non applicable », « inconnu » et « indisponible » si cela change le comportement |

Le minimum opérationnel visé est donc : **module/écran connus, éventuelle référence d'objet, et fraîcheur de l'information**. Onglet et étape ne sont transmis que s'ils sont utiles et réellement disponibles.

Ne sont pas requis par défaut : le contenu complet de l'écran, tous les champs visibles, la liste complète des objets, l'historique de navigation, toutes les données métier ou une capture d'écran.

### 4.2 Contexte de requête

À chaque sollicitation de Léon, BATORYA devrait associer à la demande :
- le texte de la demande utilisateur ;
- un instantané du contexte courant au moment où la demande est prise en charge ;
- un identifiant de requête ou mécanisme équivalent permettant d'associer les lectures à cette demande, si nécessaire à l'implémentation ;
- les références conversationnelles déjà établies, fournies par le mécanisme distinct de mémoire lorsque cela est utile.

L'identifiant de requête et la représentation exacte sont des propositions techniques, pas des décisions validées.

**Important :** l'instantané associé à une demande en cours ne doit pas être modifié rétroactivement si l'utilisateur navigue pendant que Léon prépare sa réponse. La navigation actualise le contexte courant pour les interactions suivantes. Si Léon a besoin du nouvel écran pour poursuivre, cette nouvelle information doit être prise en compte explicitement, sans mélanger silencieusement les deux états.

## 5. Références aux objets métier

Lorsqu'un objet est sélectionné, le contexte peut transmettre une référence structurée contenant au minimum :
- un type d'objet reconnu par BATORYA ;
- un identifiant stable permettant à un service autorisé de le retrouver.

Un libellé lisible peut être ajouté uniquement s'il est déjà disponible et utile. Il ne remplace jamais l'identifiant stable.

Types possibles à titre d'exemples : client, prestation, devis, BC, facture, règlement, avoir, PV, garantie, fournisseur, dépense ou note. Cette liste illustre le périmètre V6 ; elle ne constitue pas le catalogue définitif des services ou des types de référence.

Règles :
- aucune référence n'est créée par Léon à partir d'une simple supposition ;
- une référence absente signifie « aucun objet explicitement sélectionné », pas « aucun objet pertinent pour la demande » ;
- si l'identifiant ne permet plus de retrouver l'objet, BATORYA doit signaler l'échec ou l'absence de résultat ;
- si plusieurs objets correspondent à une demande et qu'aucun n'est identifié de manière fiable, Léon demande une précision ciblée ;
- la référence ne confère aucun droit d'accès : chaque lecture reste soumise aux services et contrôles applicatifs.

Les identifiants internes ne doivent pas être exposés dans la réponse utilisateur sauf nécessité fonctionnelle.

## 6. Actualisation du contexte courant

L'application doit actualiser son contexte de navigation lorsqu'un changement pertinent survient, par exemple :
- changement de module ou d'écran ;
- changement d'onglet ou d'étape ;
- sélection ou désélection d'un objet ;
- remplacement de l'objet sélectionné.

Cette actualisation est une opération d'état de l'interface, pas un appel au modèle. Elle ne doit pas provoquer de recherche métier, d'inférence ni de traitement IA en arrière-plan.

Règles de cohérence proposées :
1. le contexte reflète la dernière situation connue de l'interface ;
2. le contexte est fourni à Léon lors d'une sollicitation, ou lors d'une reprise explicitement demandée ;
3. le contexte de navigation courant et l'instantané associé à une demande en cours restent distinguables ;
4. un changement d'écran ne supprime pas la mémoire conversationnelle ;
5. le contexte doit signaler qu'un élément est inconnu ou indisponible plutôt que conserver silencieusement une ancienne valeur devenue trompeuse ;
6. le contexte ne contient pas d'objet sélectionné si l'interface n'en a effectivement aucun.

La stratégie précise de mise à jour (événements UI, état centralisé ou autre mécanisme) sera choisie au moment de la conception de l'architecture applicative. Ce document ne prescrit pas de bibliothèque ni de structure de code.

## 7. Enrichissement par lectures autorisées

Le contexte minimal ne doit pas porter toutes les données nécessaires à toutes les intentions. Lorsqu'une demande l'exige, Léon peut identifier le besoin de données ; BATORYA exécute alors une lecture via un service applicatif explicitement autorisé.

### 7.1 Séquence conceptuelle

1. BATORYA transmet la demande et l'instantané de contexte.
2. Léon détermine si le contexte et les informations déjà vérifiées suffisent.
3. Si une donnée manque, Léon formule un besoin de lecture ciblé, selon les capacités autorisées qui lui sont exposées.
4. BATORYA vérifie le type de lecture demandé, les paramètres, les droits et les limites applicables.
5. Le service applicatif retourne uniquement les données nécessaires, ou un état d'échec explicite.
6. Léon répond en s'appuyant sur les résultats vérifiés et signale toute limite restante.

Cette séquence est une proposition fonctionnelle. La forme de la demande de lecture et l'éventuelle médiation déterministe entre le modèle et les services doivent être définies dans la conception technique ; elle ne donne pas à Léon un accès libre aux services internes.

### 7.2 Limites obligatoires

- Exposer une liste limitée de lectures nommées et autorisées ; ne pas exposer une requête SQL générique.
- Vérifier et valider les paramètres avant l'appel.
- Restreindre le résultat au besoin : champs, nombre d'éléments et portée appropriés.
- Appliquer les règles métier et contrôles d'accès de BATORYA.
- Ne fournir aucune fonction de création, modification, suppression, validation, changement de statut ou déclenchement d'opération métier.
- Ne pas parcourir le système de fichiers ni les bases de données directement depuis Léon.
- Ne pas considérer qu'une donnée est vraie simplement parce qu'elle a été demandée ; s'appuyer sur le résultat effectif du service.
- Ne pas répéter automatiquement une lecture coûteuse ou large sans justification.

### 7.3 Catalogue de services : étape distincte

Le présent document ne nomme ni ne définit les contrats définitifs des services de lecture. Ceux-ci doivent être recensés à partir des intentions réellement retenues, puis rapprochés des services applicatifs qui existeront effectivement dans BATORYA.

Pour chaque lecture candidate, un document ultérieur devra préciser :
- finalité fonctionnelle ;
- données d'entrée autorisées et validation ;
- données de sortie minimales ;
- cardinalité ou limite de résultats ;
- états « trouvé », « absent », « ambigu », « invalide », « indisponible » et erreur technique, selon le cas ;
- règles métier et contrôles appliqués ;
- données sensibles ou inutiles à exclure ;
- tests et critères d'acceptation.

Le catalogue initial des intentions est une source pour identifier les besoins potentiels, mais ne prouve pas qu'un service existe ni qu'il est déjà autorisé.

## 8. Informations manquantes, obsolètes ou en erreur

Le contrat doit préserver la distinction entre les situations suivantes :

| Situation | Interprétation attendue |
|---|---|
| Champ non applicable | L'écran ou le parcours ne possède pas ce champ |
| Information inconnue | BATORYA ne peut pas établir la valeur |
| Information non transmise | Le champ n'a pas été inclus dans ce contexte |
| Donnée non trouvée | Une lecture autorisée a été exécutée sans trouver l'objet |
| Donnée ambiguë | Plusieurs résultats plausibles empêchent une réponse fiable |
| Lecture indisponible | Le service ne peut pas répondre dans l'état actuel |
| Erreur technique | L'opération a échoué ; ne pas la présenter comme un résultat métier |
| Contexte périmé | La fraîcheur ne suffit plus à garantir que l'information décrit l'état actuel |

La représentation technique de ces états reste à concevoir. Ils ne doivent pas être tous ramenés à une valeur vide ou à `null` si cela empêcherait Léon de les distinguer.

Comportement attendu :
- ne jamais transformer une absence de résultat en affirmation que l'objet n'existe pas, sauf si le service permet réellement de conclure cela ;
- ne jamais masquer une erreur technique derrière une réponse métier supposée ;
- demander une précision si une ambiguïté affecte substantiellement la réponse ;
- répondre partiellement si cela reste utile et fiable, en précisant ce qui n'a pas pu être vérifié.

## 9. Confidentialité et minimisation

Le contrat doit respecter le principe du besoin d'en connaître :
- ne transmettre que les données pertinentes pour la demande ;
- privilégier les références aux objets avant de charger leurs détails ;
- éviter de transmettre des coordonnées, adresses, notes libres ou autres informations personnelles lorsqu'elles ne sont pas nécessaires ;
- ne pas placer les données métier complètes dans les journaux techniques ;
- limiter la durée de conservation des données récupérées à ce que nécessite la demande et le fonctionnement conversationnel validé ;
- définir dans le document de mémoire les modalités de stockage, de protection et d'expiration des éléments conversationnels ;
- ne pas utiliser la mémoire conversationnelle comme substitut à une nouvelle vérification d'une donnée métier susceptible d'avoir changé.

Ces principes ne fixent pas à eux seuls une politique technique de journalisation ou de stockage ; celle-ci devra être définie avant l'implémentation.

## 10. Responsabilités

### BATORYA

- Maintenir l'état de navigation fiable.
- Fournir les identifiants logiques d'écran/module connus de l'application.
- Capturer l'instantané du contexte au moment de la sollicitation.
- Contrôler et exécuter les lectures via des services applicatifs autorisés.
- Valider les paramètres, appliquer les règles d'accès et limiter les résultats.
- Retourner des états explicites en cas d'absence, d'ambiguïté ou d'échec.
- Ne pas exposer de capacité d'écriture métier à Léon.

### Léon

- Interpréter la demande à partir du texte et du contexte fourni.
- Déterminer si les données disponibles suffisent.
- Ne demander que les lectures nécessaires et autorisées.
- Ne pas prétendre qu'une donnée a été consultée si aucun résultat de service ne l'atteste.
- Distinguer les faits vérifiés, les inconnues et les hypothèses.
- Demander une clarification ciblée lorsqu'une ambiguïté réelle bloque une réponse fiable.
- Ne jamais exécuter lui-même une opération métier.

## 11. Exemple de fonctionnement

**Situation :** l'utilisateur se trouve dans le parcours de création d'un devis et demande : « Pourquoi je ne peux pas sélectionner ce client ? »

1. BATORYA transmet l'écran/parcours actif et, si un client est réellement sélectionné, sa référence.
2. Léon vérifie si les informations présentes suffisent à expliquer la situation.
3. Si une règle ou une donnée complémentaire est nécessaire, il demande une lecture précise autorisée ; il ne reçoit pas l'intégralité de la fiche client par défaut.
4. BATORYA exécute la lecture et retourne les données utiles ou un état explicite indiquant que la situation n'a pas pu être vérifiée.
5. Léon explique uniquement ce que les informations obtenues permettent d'établir et guide l'utilisateur pour la suite. Il ne modifie pas le client ni le devis.

Cet exemple illustre la méthode ; il ne définit pas à lui seul la règle métier réelle de sélection d'un client.

## 12. Points à arbitrer avant validation

Les questions suivantes restent ouvertes et ne doivent pas être considérées comme décidées :

1. Quels identifiants stables utiliser pour les chapitres, modules, écrans, onglets et étapes ?
2. Quel niveau de granularité d'écran est utile sans rendre le contrat fragile aux changements d'interface ?
3. Le contrat doit-il inclure un titre d'écran lisible en complément de son identifiant logique ?
4. Quelle représentation technique choisir pour les états inconnus, non applicables, non transmis, périmés et indisponibles ?
5. Comment détecter qu'une référence d'objet n'est plus valide entre sa sélection et une lecture ?
6. Quelles limites de résultats et de taille appliquer aux lectures ?
7. Les besoins de lecture doivent-ils être sélectionnés exclusivement par une couche déterministe, proposés par le modèle puis validés, ou combinés selon le type d'intention ?
8. Quelles données peuvent être conservées en mémoire conversationnelle après une lecture et pendant combien de temps ?
9. Comment distinguer un contexte de demande en cours d'un contexte actualisé après navigation, notamment lorsque l'utilisateur intervient pendant la génération d'une réponse ?
10. Quels contrôles et tests garantissent que Léon ne peut jamais invoquer une capacité d'écriture métier ?

## 13. Ordre de travail proposé

1. Relire et valider les principes du présent contrat.
2. Arrêter les champs strictement minimaux du contexte courant et de l'instantané de requête.
3. Définir séparément le cycle de vie de la mémoire conversationnelle, en traitant les points déjà laissés ouverts par le cadrage.
4. Reprendre le catalogue initial des intentions pour identifier les besoins de données réels et les clarifications.
5. Établir le catalogue des lectures autorisées en le confrontant aux services applicatifs réellement prévus ou disponibles.
6. Définir les états d'erreur, les limites de données et les tests de sécurité/fiabilité.
7. Seulement ensuite, traduire les décisions validées en contrats techniques et en architecture applicative.

## 14. Critères d'acceptation du contrat

Le contrat pourra être considéré comme suffisamment défini lorsque les revues permettront de vérifier que :

- un écran ou module connu est transmis sans que Léon ait à l'inventer ;
- l'absence d'objet sélectionné est représentée explicitement ;
- le contexte de requête peut être distingué de l'état de navigation ultérieur ;
- aucun changement de navigation ne déclenche à lui seul un traitement IA ;
- les lectures sont limitées à des capacités nommées, contrôlées et en lecture seule ;
- les informations non disponibles et les erreurs ne sont pas confondues avec des résultats métier ;
- les données transmises et retournées sont limitées au besoin ;
- aucune voie d'accès direct à SQLite, au système de fichiers ou à l'écriture métier n'est exposée à Léon ;
- la relation avec la mémoire conversationnelle est définie sans confondre les responsabilités.

**Statut final :** proposition de contrat à examiner. Les critères ci-dessus sont des critères proposés pour la revue, pas la preuve qu'une implémentation existe déjà.
