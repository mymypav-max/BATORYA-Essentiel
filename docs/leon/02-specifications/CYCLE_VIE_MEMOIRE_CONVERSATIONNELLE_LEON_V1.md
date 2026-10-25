# Cycle de vie de la mémoire conversationnelle de Léon — BATORYA Essentiel V6

**Statut :** proposition de conception — décisions fonctionnelles partielles confirmées en revue, document complet non validé  
**Version :** V1 de travail  
**Périmètre :** BATORYA Essentiel V6 exclusivement  
**Dépendances :** `CADRAGE_FONCTIONNEL_LEON_V1.md` et proposition de contrat de contexte minimal

> Ce document précise le comportement fonctionnel attendu de la mémoire conversationnelle. Les décisions explicitement marquées comme confirmées ont été validées lors de la revue, mais le document complet et son architecture restent à valider.

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
8. **Minimisation des données :** la mémoire ne conserve que les informations nécessaires à la continuité de la conversation. Elle évite de recopier inutilement des données personnelles ou confidentielles et le contenu intégral des documents métier.
9. **Gestion des informations manquantes :** Léon ne comble jamais une lacune de mémoire par une supposition présentée comme certaine. Si l'information manquante empêche une réponse fiable ou l'identification certaine d'un objet métier, il pose une question de clarification ciblée.

## 3. Ce que la mémoire doit conserver

Pendant une conversation active, Léon peut conserver les éléments pertinents suivants :

- l'objectif principal de l'utilisateur et les différents sujets secondaires ouverts dans la même conversation, chacun avec sa progression et ses éventuelles questions en attente ;
- l'objectif initial de l'utilisateur et la question à résoudre ;
- les précisions et réponses apportées par l'utilisateur ;
- les interprétations confirmées ou les ambiguïtés qui restent ouvertes ;
- la nature des informations conservées, en distinguant explicitement les faits métier vérifiés (avec leur moment de vérification si utile), les déclarations de l'utilisateur et les hypothèses non confirmées ;
- les faits métier effectivement vérifiés, avec assez d'information pour savoir ce qui a été vérifié et ce qui doit l'être à nouveau ;
- les éléments déjà établis qui peuvent être réutilisés sans répétition systématique, en les rappelant seulement lorsqu'ils aident à comprendre, justifier la réponse ou confirmer l'objet concerné ;
- les étapes déjà expliquées et la progression de l'accompagnement ;
- les références aux objets métier déjà identifiés de façon fiable ;
- les engagements de dialogue utiles, notamment les questions en attente et les précisions attendues de l'utilisateur, afin qu'une réponse ultérieure puisse être interprétée correctement même après un changement d'écran.

La mémoire n'a pas vocation à conserver systématiquement chaque détail de l'interface, toutes les données renvoyées par les services, ni une copie complète des objets métier. Elle applique un principe de minimisation : conserver uniquement les éléments utiles à la continuité (par exemple une référence d'objet, son objet et quelques faits pertinents), sans recopier inutilement les coordonnées personnelles, coordonnées bancaires, autres informations confidentielles ou le contenu intégral d'un document.\n\n**Décision confirmée en revue :** la continuité repose sur deux éléments complémentaires :\n- un résumé structuré de la conversation, contenant l'objectif, les précisions utiles, les faits vérifiés et la progression ;\n- les derniers échanges utiles, pour préserver le contexte immédiat et interpréter correctement les références courtes.\n\nLe résumé est actualisé à l'occasion des interactions avec Léon, sans traitement IA en arrière-plan. La taille du résumé et le nombre d'échanges récents conservés restent à définir techniquement. La mémoire doit respecter un budget technique global à définir, plutôt qu'un nombre fixe de sujets. En cas de contrainte de capacité, la priorité va à la demande active, aux questions en attente, aux faits vérifiés pertinents et aux échanges récents utiles. Si une information est écartée, Léon ne doit plus s'y fier et doit demander une précision si elle redevient nécessaire. Si plusieurs messages utilisateur arrivent avant la fin d'une réponse, Léon les traite comme une même demande lorsque leur lien est clair, plutôt que de lancer des réponses concurrentes. En cas de contradiction ou d'ambiguïté importante, il demande une clarification. Si un nouveau message correspond clairement à une demande indépendante, Léon termine la réponse déjà en cours, puis traite la nouvelle demande ; il ne l'interrompt pas automatiquement. Il n'est pas exigé de conserver indéfiniment l'intégralité des messages mot pour mot.

## 4. Ce que la mémoire ne doit pas faire

La mémoire conversationnelle :

- ne remplace pas le contexte d'écran transmis à l'activation de Léon ;
- ne remplace pas une nouvelle lecture métier lorsque le statut, le montant, l'échéance ou toute autre donnée peut avoir changé ;
- ne transforme pas une hypothèse en fait vérifié ;
- ne confond pas une déclaration de l'utilisateur avec une donnée métier vérifiée indépendamment ;
- ne donne aucun droit d'accès supplémentaire aux données métier ;
- ne conserve pas inutilement les données personnelles ou confidentielles, les coordonnées bancaires ni le contenu intégral des documents métier ;
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

Si le message suivant ne permet pas de déterminer s'il se rattache à la demande précédente ou s'il s'agit d'un nouveau sujet, Léon interprète le contexte lorsqu'il est suffisamment clair et ne pose une question que si l'ambiguïté change substantiellement la réponse. Il réutilise les faits déjà établis sans les répéter systématiquement ; il les rappelle uniquement lorsque cela facilite la compréhension, justifie la réponse ou aide à confirmer l'objet concerné.

## 6. Règle des 30 minutes d'inactivité — confirmée en revue

Pour la V1, les règles suivantes sont confirmées :

- le délai de 30 minutes est calculé depuis la dernière interaction de l'utilisateur avec Léon ;
- envoyer un nouveau message à Léon renouvelle le délai ; plusieurs messages successifs avant la fin d'une réponse sont regroupés dans une même demande lorsqu'ils sont clairement liés, sans lancer de réponses concurrentes ;
- une réponse en cours de génération ne doit pas être interrompue automatiquement, que ce soit parce que le délai arrive à échéance ou parce qu'une nouvelle demande indépendante est reçue ; le contexte reste disponible pour terminer ce tour. Le délai glissant de 30 minutes repart à la fin de la réponse, une fois celle-ci délivrée à l'utilisateur ;
- la navigation dans BATORYA, l'ouverture ou la fermeture d'un module et le maintien de l'application ouverte ne renouvellent pas le délai ;
- un traitement interne ou une lecture métier en cours ne constitue pas, à lui seul, une interaction utilisateur renouvelant le délai ;
- après 30 minutes sans interaction avec Léon, la conversation est considérée comme expirée.

Le choix fonctionnel est confirmé. La manière technique de mesurer et d'appliquer le délai reste à définir.

## 7. Comportement à l'expiration

À l'expiration :

1. Léon ne doit plus utiliser le contexte conversationnel expiré pour interpréter une nouvelle demande.
2. La prochaine sollicitation démarre une nouvelle conversation sans présumer que l'objectif précédent, ses précisions ou ses références sont encore disponibles.
3. Si l'utilisateur fait référence à la conversation précédente — par exemple « on reprend où on en était ? » — Léon indique brièvement qu'il ne dispose plus du contexte nécessaire, puis demande uniquement les informations indispensables pour reprendre. Il ne tente pas de reconstruire l'échange à partir de suppositions.
4. Les données métier de BATORYA ne sont ni supprimées ni modifiées par l'expiration de la mémoire.
5. Aucun message ne doit laisser croire que Léon a conservé des informations qui ont été supprimées ou ne sont plus accessibles.

Il est préférable de ne pas imposer à l'utilisateur un récapitulatif complet : Léon demande uniquement les éléments indispensables pour comprendre à nouveau la demande. Les questions en attente et les précisions attendues sont abandonnées avec le contexte expiré.

## 8. Nouvelle conversation et changement de sujet

L'expiration au bout de 30 minutes est distincte d'un changement de sujet avant expiration.

Lorsqu'un utilisateur pose clairement une nouvelle question sans lien avec la précédente, Léon doit répondre à cette nouvelle demande sans forcer artificiellement l'ancien objectif dans l'interprétation. Les éléments antérieurs peuvent rester disponibles tant qu'ils sont utiles à une référence ultérieure et que la conversation n'a pas expiré. Si plusieurs sujets sont traités dans la même conversation, Léon conserve un objectif principal et distingue les sujets secondaires, leur progression et leurs questions en attente afin de pouvoir y revenir sans mélanger leurs informations. Il suit naturellement un nouveau sujet sans annoncer systématiquement le changement ; il ne le signale que si cela permet d'éviter une confusion importante.

**Décision confirmée en revue :** l'utilisateur pourra démarrer explicitement une nouvelle conversation au moyen d'une action dédiée dans l'interface de Léon, distincte du simple changement de sujet. Cette action abandonne immédiatement le contexte conversationnel précédent, y compris les questions en attente et les précisions attendues, sans attendre l'expiration des 30 minutes. Les détails d'emplacement et de présentation du contrôle restent à concevoir. Un simple changement de sujet ne déclenche pas à lui seul la suppression de toute la mémoire.

## 9. Données métier et fraîcheur des informations

La mémoire peut retenir qu'une lecture a été effectuée et ce qu'elle a établi à cet instant. Elle ne doit pas considérer automatiquement que le résultat demeure actuel.

Exemples :
- le statut d'un devis peut avoir changé ;
- un règlement peut avoir été enregistré depuis la dernière vérification ;
- une échéance ou un montant peut ne plus correspondre à l'état présent.

Si la réponse de suivi dépend de l'état métier actuel, BATORYA doit fournir une nouvelle lecture autorisée. Si cette lecture est indisponible, Léon doit le signaler plutôt que de présenter l'ancien résultat comme actuel. Dans la mémoire, les résultats de lecture métier restent identifiés comme des faits vérifiés à un instant donné ; les propos de l'utilisateur sont conservés comme ses déclarations, et les hypothèses non confirmées restent clairement marquées comme telles.

## 10. Stockage, confidentialité et suppression — choix fonctionnel confirmé

**Décision confirmée en revue :** pour la V1, la mémoire conversationnelle est conservée uniquement en mémoire vive (RAM). Elle n'est pas enregistrée dans SQLite ni dans un fichier et n'est pas restaurée après fermeture de BATORYA.

Conséquences attendues :
- à l'expiration des 30 minutes, le contexte conversationnel est supprimé ;
- lorsqu'une nouvelle conversation est demandée explicitement, le contexte précédent est supprimé immédiatement ;
- à la fermeture normale ou à l'arrêt inattendu de BATORYA, la mémoire disparaît et n'est pas restaurée à la prochaine ouverture ;
- si BATORYA se ferme pendant la génération d'une réponse de Léon, la génération est interrompue avec l'application ; à la prochaine ouverture, Léon ne reprend pas automatiquement cette génération et ne restaure pas la conversation interrompue ;
- les données métier dans SQLite ne sont pas modifiées par ces suppressions ;
- aucun traitement IA périodique ou en arrière-plan n'est lancé pour entretenir la mémoire.

Restent à définir dans la conception technique :
- le budget global de mémoire et les règles de priorité/éviction des éléments, sans fixer un nombre maximal arbitraire de sujets ;
- comment isoler le contexte de la conversation active et éviter qu'il soit partagé entre utilisateurs éventuels du même poste ;
- comment supprimer effectivement les références et buffers de contexte à l'expiration ou à la réinitialisation, dans les limites garanties par l'environnement d'exécution ;
- quelles données, le cas échéant, peuvent apparaître dans les journaux techniques et comment éviter d'y copier le contenu conversationnel ;
- comment tester que la fermeture ou un arrêt inattendu ne restaure pas de mémoire expirée.

La mémoire en RAM est un choix fonctionnel pour la V1 ; ses modalités d'implémentation et de vérification restent à spécifier.

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
- les messages de suivi peuvent réutiliser les précisions pertinentes déjà fournies sans les répéter systématiquement ;
- plusieurs messages successifs clairement liés avant la fin d'une réponse sont traités comme une même demande ; en cas de contradiction ou d'ambiguïté importante, Léon demande une clarification plutôt que de produire des réponses concurrentes ;
- si un message reçu pendant la génération constitue clairement une demande indépendante, Léon termine la réponse en cours puis traite cette nouvelle demande ; l'interruption volontaire éventuelle reste à définir séparément ;
- les faits déjà établis ne sont rappelés que lorsqu'ils sont utiles à la compréhension, à la justification de la réponse ou à la confirmation de l'objet concerné ;
- une réponse à une question en attente peut être comprise après un changement d'écran, tant que la conversation n'a pas expiré ou été réinitialisée ;
- les questions en attente sont abandonnées lors de l'expiration ou du démarrage explicite d'une nouvelle conversation ;
- les données métier susceptibles d'avoir changé sont revérifiées avant de servir de faits actuels ;
- la navigation seule ne renouvelle pas le délai d'inactivité ;
- le délai de 30 minutes est appliqué sans interrompre arbitrairement une réponse en cours ; si la génération dépasse ce délai, le contexte reste disponible jusqu'à la fin de la réponse et le délai repart lorsque la réponse est délivrée ;
- après expiration, Léon ne prétend pas connaître l'ancien contexte ;
- l'expiration est silencieuse et ne déclenche ni notification automatique ni traitement IA en arrière-plan ;
- la reprise après expiration indique brièvement que le contexte précédent n'est plus disponible, puis demande seulement les informations indispensables, sans reconstruire la conversation par supposition ;
- une information manquante qui empêche une réponse fiable entraîne une question de clarification ciblée, jamais une supposition présentée comme un fait ;
- les faits métier vérifiés, les déclarations de l'utilisateur et les hypothèses non confirmées restent explicitement distingués dans la mémoire ;
- la mémoire ne conserve que les données nécessaires à la continuité et évite les copies inutiles de données personnelles ou confidentielles et de documents complets ;
- l'expiration de la mémoire ne modifie aucune donnée métier ;
- aucun traitement IA en arrière-plan n'est déclenché pour entretenir la mémoire ;
- le mécanisme de stockage et de suppression est défini avant implémentation ;
- le budget technique global de mémoire et les règles de priorité/éviction sont définis, sans nombre fixe de sujets ; si un élément évincé devient nécessaire, Léon demande une précision plutôt que de l'inventer ;
- une fermeture pendant la génération interrompt la réponse et ne provoque aucune reprise ou restauration automatique au redémarrage.

## 13. Décisions confirmées et points restant à arbitrer

### Décisions confirmées en revue

1. Le délai de 30 minutes est calculé depuis la dernière interaction de l'utilisateur avec Léon ; la navigation seule ne le renouvelle pas.
2. Une réponse en cours peut se terminer même si le délai est atteint pendant sa génération ; le contexte ne doit pas être coupé au milieu du tour. Le délai glissant de 30 minutes repart à la fin de la réponse, une fois celle-ci délivrée à l'utilisateur.
3. Une action dédiée dans l'interface permet à l'utilisateur de démarrer explicitement une nouvelle conversation et supprime immédiatement le contexte précédent ; un simple changement de sujet ne déclenche pas cette suppression.
4. La mémoire est conservée uniquement en RAM, sans persistance ni restauration après fermeture normale ou inattendue de BATORYA.
5. La mémoire combine un résumé structuré de fond et les derniers échanges utiles, plutôt que de conserver indéfiniment l'historique intégral.
6. Le résumé est actualisé lors des interactions avec Léon, sans traitement IA en arrière-plan.
7. Les données métier sont distinctes de la mémoire conversationnelle et ne sont pas supprimées par son expiration.
8. Une même conversation peut contenir plusieurs sujets : la mémoire conserve un objectif principal et distingue les sujets secondaires, leur progression et leurs questions en attente. Le délai d'inactivité reste global à la conversation.
9. Léon suit naturellement un changement de sujet sans l'annoncer systématiquement ; il ne le signale que si cela aide à éviter une confusion importante.
8. Si une information manquante empêche une réponse fiable ou l'identification certaine d'un objet métier, Léon pose une question ciblée au lieu de deviner.
9. Le démarrage explicite d'une nouvelle conversation passe par une action dédiée dans l'interface de Léon, distincte d'un changement de sujet ; son emplacement et sa présentation restent à concevoir.
10. Après expiration, si l'utilisateur demande de reprendre l'ancienne conversation, Léon explique brièvement qu'il n'en a plus le contexte et demande les seules précisions nécessaires, sans inventer ni reconstruire l'échange.
11. Si BATORYA se ferme pendant la génération d'une réponse, celle-ci est interrompue ; la génération et le contexte conversationnel ne sont pas restaurés ni repris automatiquement à la prochaine ouverture.
12. L'expiration au bout de 30 minutes est silencieuse lorsqu'elle survient sans sollicitation de Léon : aucune notification ni aucun traitement en arrière-plan n'est déclenché. Si l'utilisateur fait ensuite référence à la conversation expirée, Léon explique brièvement que le contexte n'est plus disponible.
13. Si une réponse de Léon dépasse 30 minutes de génération, le délai n'expire pas au milieu de ce tour : le contexte reste disponible jusqu'à la fin de la réponse, puis le délai glissant repart à partir de la délivrance de celle-ci.
14. La mémoire conserve les questions en attente et les précisions attendues de l'utilisateur pour interpréter ses réponses ultérieures, y compris après un changement d'écran. Ces éléments sont abandonnés à l'expiration ou au démarrage explicite d'une nouvelle conversation.
15. Léon réutilise les faits et précisions déjà établis sans les répéter systématiquement ; il les rappelle uniquement si cela aide à comprendre ou justifier sa réponse, ou à confirmer l'objet concerné.
16. La mémoire distingue explicitement les faits métier vérifiés (et le moment de leur vérification lorsque pertinent), les déclarations de l'utilisateur et les hypothèses non confirmées. Une hypothèse ne devient jamais un fait vérifié sans vérification appropriée.
17. La mémoire applique un principe de minimisation : elle conserve uniquement les éléments nécessaires à la continuité et évite de recopier inutilement des données personnelles ou confidentielles, des coordonnées bancaires et le contenu intégral de documents métier.
18. Une conversation peut regrouper plusieurs sujets : Léon conserve un objectif principal et distingue les sujets secondaires, chacun avec sa progression et ses questions en attente. Le délai de 30 minutes s'applique globalement à la conversation ; l'expiration ou le démarrage explicite d'une nouvelle conversation abandonne tous les sujets mémorisés.
19. Léon suit naturellement un nouveau sujet sans annoncer systématiquement le changement ; il ne le signale que si cela aide à éviter une confusion importante.
20. Plusieurs messages utilisateur successifs reçus avant la fin d'une réponse sont traités comme une même demande lorsqu'ils sont clairement liés. Léon évite les réponses concurrentes et demande une clarification ciblée en cas de contradiction ou d'ambiguïté importante.
21. Si l'utilisateur envoie une demande clairement indépendante pendant la génération d'une réponse, Léon termine la réponse en cours avant de traiter la nouvelle demande. L'éventuelle possibilité d'interrompre volontairement une génération reste à définir séparément.
22. La mémoire respecte un budget technique global à définir plutôt qu'un nombre fixe de sujets. La demande active, les questions en attente, les faits vérifiés pertinents et les derniers échanges utiles sont prioritaires. Si une information est écartée et devient ensuite nécessaire, Léon demande une précision au lieu de s'y fier ou de l'inventer.

### Points restant à arbitrer

1. Définir les limites de taille du résumé structuré et le nombre ou la taille des derniers échanges utiles conservés, afin de préserver la fluidité.
2. Déterminer les exigences techniques d'isolation, de suppression effective et de journalisation sans contenu conversationnel inutile.
3. Concevoir l'emplacement et la présentation de l'action dédiée « Nouvelle conversation » dans l'interface.
4. Préparer ultérieurement des tests fonctionnels couvrant navigation, suivi, changement de sujet, données métier périmées, réinitialisation explicite et expiration.

**Statut final :** proposition de cycle de vie partiellement confirmée en revue. Les décisions listées en section 13 sont retenues fonctionnellement ; les points restant à arbitrer, les détails techniques et les critères d'acceptation doivent encore être finalisés avant validation complète du document.
