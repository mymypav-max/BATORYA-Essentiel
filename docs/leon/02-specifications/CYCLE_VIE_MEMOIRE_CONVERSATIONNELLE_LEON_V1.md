# Cycle de vie de la mémoire conversationnelle de Léon — BATORYA Essentiel V6

**Statut :** proposition de conception — non validée  
**Version :** V1 de travail  
**Périmètre :** BATORYA Essentiel V6 exclusivement  
**Dépendances :** `CADRAGE_FONCTIONNEL_LEON_V1.md` et proposition de contrat de contexte minimal

> Ce document précise le comportement fonctionnel attendu de la mémoire conversationnelle. Il ne choisit pas encore son mécanisme technique de stockage et ne vaut pas validation d'une architecture.

## 1. Objectif

Définir comment Léon conserve le fil d'une conversation, le reprend après un changement d'écran et cesse de s'appuyer sur son contexte après une période d'inactivité.

Le principe déjà retenu dans le cadrage est une expiration après **30 minutes d'inactivité**. Pour éviter les interprétations divergentes, la proposition ci-dessous définit l'inactivité comme l'absence d'interaction de l'utilisateur avec Léon, et non l'absence de navigation dans BATORYA.

## 2. Principes directeurs

1. **Continuité :** un changement d'écran ou de module ne démarre pas, à lui seul, une nouvelle conversation.
2. **Demande prioritaire :** l'objectif formulé par l'utilisateur reste le fil directeur. L'écran courant est un contexte complémentaire, pas une nouvelle intention supposée.
3. **Mémoire utile :** Léon conserve uniquement les éléments nécessaires pour comprendre les références, éviter les répétitions et poursuivre la résolution.
4. **Pas de traitement en arrière-plan :** la conservation du contexte ne déclenche pas de traitement IA lorsque l'utilisateur ne sollicite pas Léon.
5. **Expiration claire :** après 30 minutes sans interaction avec Léon, le contexte conversationnel expire et ne doit plus être présenté comme disponible.
6. **Séparation des données :** la mémoire conversationnelle n'est ni la base métier BATORYA, ni une copie durable des dossiers clients ou documents.
7. **Fiabilité :** une information conservée en mémoire n'est pas automatiquement une donnée métier encore à jour. Une donnée susceptible d'avoir changé doit être vérifiée à nouveau par une lecture autorisée.

## 3. Ce que la mémoire doit conserver

Pendant une conversation active, Léon peut conserver les éléments pertinents suivants :

- l'objectif initial de l'utilisateur et la question à résoudre ;
- les précisions et réponses apportées par l'utilisateur ;
- les interprétations confirmées ou les ambiguïtés qui restent ouvertes ;
- les faits métier effectivement vérifiés, avec assez d'information pour savoir ce qui a été vérifié et ce qui doit l'être à nouveau ;
- les étapes déjà expliquées et la progression de l'accompagnement ;
- les références aux objets métier déjà identifiés de façon fiable ;
- les engagements de dialogue utiles, par exemple une question posée à laquelle l'utilisateur doit encore répondre.

La mémoire n'a pas vocation à conserver systématiquement chaque détail de l'interface, toutes les données renvoyées par les services, ni une copie complète des objets métier. Le niveau exact de détail et le format de représentation seront définis lors de la conception technique.

## 4. Ce que la mémoire ne doit pas faire

La mémoire conversationnelle :

- ne remplace pas le contexte d'écran transmis à l'activation de Léon ;
- ne remplace pas une nouvelle lecture métier lorsque le statut, le montant, l'échéance ou toute autre donnée peut avoir changé ;
- ne transforme pas une hypothèse en fait vérifié ;
- ne donne aucun droit d'accès supplémentaire aux données métier ;
- ne permet aucune écriture ou action métier ;
- ne doit pas persister indéfiniment simplement parce que BATORYA reste ouvert ;
- ne doit pas être entretenue par un traitement IA périodique ou en arrière-plan.

## 5. Changement d'écran pendant une conversation

Un changement d'écran ne doit ni effacer l'objectif en cours, ni être interprété automatiquement comme une nouvelle demande.

Lors d'une nouvelle interaction avec Léon, BATORYA peut lui transmettre l'écran alors affiché, conformément au contrat de contexte. Léon peut alors utiliser ce nouvel écran comme contexte complémentaire du message de suivi.

En revanche, le nouvel écran ne doit pas réécrire rétroactivement le contexte associé à une demande précédente. Si une réponse est déjà en cours de préparation, un changement d'écran seul ne doit pas en modifier silencieusement le sens.

**Exemple :**
1. L'utilisateur demande de l'aide pour retrouver un client pendant la préparation d'un devis.
2. Il ouvre le carnet clients.
3. Il revient vers Léon et précise qu'il ne trouve toujours pas le client.
4. Léon conserve l'objectif de départ, tient compte du nouvel écran transmis à cette interaction et demande une lecture autorisée si des données sont nécessaires.
5. Il ne recommence pas toute la conversation et ne suppose pas que le changement d'écran a résolu le problème.

Si le message suivant ne permet pas de déterminer s'il se rattache à la demande précédente ou s'il s'agit d'un nouveau sujet, Léon interprète le contexte lorsqu'il est suffisamment clair et ne pose une question que si l'ambiguïté change substantiellement la réponse.

## 6. Définition proposée des 30 minutes d'inactivité

Pour la V1, la règle proposée est la suivante :

- le délai de 30 minutes est calculé depuis la dernière interaction de l'utilisateur avec Léon ;
- envoyer un nouveau message à Léon renouvelle le délai ;
- une réponse en cours de génération ne doit pas être interrompue uniquement parce que le délai arrive à échéance ; le contexte reste disponible pour terminer ce tour, puis le délai repart après la réponse ;
- la navigation dans BATORYA, l'ouverture ou la fermeture d'un module et le maintien de l'application ouverte ne renouvellent pas le délai ;
- un traitement interne ou une lecture métier en cours ne constitue pas, à lui seul, une interaction utilisateur renouvelant le délai ;
- après 30 minutes sans interaction avec Léon, la conversation est considérée comme expirée.

Cette définition est une proposition fonctionnelle à valider. Elle ne fixe pas encore la manière technique de mesurer le délai.

## 7. Comportement à l'expiration

À l'expiration :

1. Léon ne doit plus utiliser le contexte conversationnel expiré pour interpréter une nouvelle demande.
2. La prochaine sollicitation démarre une nouvelle conversation sans présumer que l'objectif précédent, ses précisions ou ses références sont encore disponibles.
3. Si l'utilisateur fait référence à la conversation précédente — par exemple « on reprend où on en était ? » — Léon indique simplement qu'il ne dispose plus du contexte nécessaire et demande les éléments minimums pour reprendre.
4. Les données métier de BATORYA ne sont ni supprimées ni modifiées par l'expiration de la mémoire.
5. Aucun message ne doit laisser croire que Léon a conservé des informations qui ont été supprimées ou ne sont plus accessibles.

Il est préférable de ne pas imposer à l'utilisateur un récapitulatif complet : Léon demande uniquement les éléments indispensables pour comprendre à nouveau la demande.

## 8. Nouvelle conversation et changement de sujet

L'expiration au bout de 30 minutes est distincte d'un changement de sujet avant expiration.

Lorsqu'un utilisateur pose clairement une nouvelle question sans lien avec la précédente, Léon doit répondre à cette nouvelle demande sans forcer artificiellement l'ancien objectif dans l'interprétation. Les éléments antérieurs peuvent rester disponibles tant qu'ils sont utiles à une référence ultérieure et que la conversation n'a pas expiré.

Le mécanisme permettant à l'utilisateur de demander explicitement une nouvelle conversation ou d'abandonner l'objectif en cours reste à préciser. Aucun bouton ou comportement d'interface n'est imposé par le présent document.

## 9. Données métier et fraîcheur des informations

La mémoire peut retenir qu'une lecture a été effectuée et ce qu'elle a établi à cet instant. Elle ne doit pas considérer automatiquement que le résultat demeure actuel.

Exemples :
- le statut d'un devis peut avoir changé ;
- un règlement peut avoir été enregistré depuis la dernière vérification ;
- une échéance ou un montant peut ne plus correspondre à l'état présent.

Si la réponse de suivi dépend de l'état métier actuel, BATORYA doit fournir une nouvelle lecture autorisée. Si cette lecture est indisponible, Léon doit le signaler plutôt que de présenter l'ancien résultat comme actuel.

## 10. Stockage, confidentialité et suppression

Le cadrage exige une mémoire limitée et un fonctionnement local, mais ne fixe pas encore le mécanisme de stockage. La proposition fonctionnelle est de limiter la durée de conservation au besoin de continuité de la conversation et de supprimer le contexte expiré.

Restent à définir dans la conception technique :
- si la mémoire est uniquement conservée en mémoire vive ou si une persistance locale temporaire est nécessaire ;
- comment le contexte est isolé entre les conversations et les utilisateurs éventuels du même poste ;
- comment garantir sa suppression à l'expiration et à la fermeture de l'application ;
- quelles données, le cas échéant, peuvent apparaître dans les journaux techniques ;
- comment éviter qu'une fermeture inattendue de BATORYA ne restaure une conversation expirée.

Aucune persistance durable de la mémoire conversationnelle n'est décidée par ce document. La base métier SQLite reste distincte et ne doit pas être utilisée comme stockage implicite de la mémoire de Léon.

## 11. Séquence fonctionnelle de référence

1. L'utilisateur active Léon et formule une demande.
2. BATORYA transmet le message, l'écran affiché à l'activation et, si utile et déjà disponible, les éléments pertinents de la conversation en cours.
3. Léon interprète la demande à la lumière de son objectif conversationnel et du contexte d'écran complémentaire.
4. Si nécessaire, une lecture métier ciblée est exécutée par un service autorisé en lecture seule.
5. Léon répond et conserve les éléments utiles à la continuité.
6. Une nouvelle interaction utilisateur avec Léon renouvelle le délai d'inactivité ; la navigation seule ne le fait pas.
7. Après 30 minutes sans interaction avec Léon, le contexte conversationnel expire.
8. À la sollicitation suivante, Léon démarre sans s'appuyer sur le contexte expiré.

Cette séquence est une référence fonctionnelle proposée, pas la description d'une implémentation existante.

## 12. Critères d'acceptation proposés

Le cycle de vie sera suffisamment défini pour être traduit en conception technique lorsque la revue permettra de vérifier que :

- un changement d'écran ne fait pas perdre le fil d'une demande en cours ;
- l'écran transmis à une interaction est un contexte complémentaire et ne remplace pas la demande explicite ;
- les messages de suivi peuvent réutiliser les précisions pertinentes déjà fournies ;
- les données métier susceptibles d'avoir changé sont revérifiées avant de servir de faits actuels ;
- la navigation seule ne renouvelle pas le délai d'inactivité ;
- le délai de 30 minutes est appliqué sans interrompre arbitrairement une réponse en cours ;
- après expiration, Léon ne prétend pas connaître l'ancien contexte ;
- la reprise après expiration demande seulement les informations indispensables ;
- l'expiration de la mémoire ne modifie aucune donnée métier ;
- aucun traitement IA en arrière-plan n'est déclenché pour entretenir la mémoire ;
- le mécanisme de stockage et de suppression est défini avant implémentation.

## 13. Points à arbitrer avant validation

1. Confirmer que les 30 minutes sont mesurées depuis la dernière interaction de l'utilisateur avec Léon, et non depuis la dernière activité dans BATORYA.
2. Confirmer le comportement proposé pendant une réponse en cours lorsque le délai arrive à échéance.
3. Déterminer si l'utilisateur doit pouvoir démarrer explicitement une nouvelle conversation ou abandonner l'objectif en cours.
4. Choisir le mécanisme de stockage et de suppression, en privilégiant la solution locale la plus simple qui respecte la confidentialité et la continuité attendue.
5. Définir les limites de taille et de détail de la mémoire pour préserver la fluidité sur les configurations ciblées.
6. Déterminer le comportement à la fermeture normale ou inattendue de l'application.
7. Préparer ultérieurement des tests fonctionnels couvrant navigation, suivi, changement de sujet, données métier périmées et expiration.

**Statut final :** proposition de cycle de vie à examiner. Les règles et critères ci-dessus ne sont pas considérés comme validés tant que les arbitrages n'ont pas été confirmés.
