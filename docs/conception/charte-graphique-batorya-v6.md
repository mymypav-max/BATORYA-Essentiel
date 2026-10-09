# Charte graphique BATORYA V6

**Version : 0.3**  
**Statut : En construction — référence de conception**  
**Périmètre : BATORYA Essentiel V6**

> Document de référence unique pour l'identité visuelle et le système graphique de BATORYA Essentiel V6. Il regroupe les règles communes ainsi que les déclinaisons **Mode clair** et **Mode sombre**.

---

## 1. Objet du document

Cette charte définit le langage visuel de BATORYA Essentiel V6 et constitue la référence à utiliser lors de la conception puis de l'implémentation de l'interface utilisateur.

Elle a deux objectifs :

1. préserver une identité graphique BATORYA cohérente dans toute l'application ;
2. permettre une déclinaison fidèle en **mode clair**, **mode sombre** et, à terme, **mode automatique** sans créer deux identités visuelles distinctes.

Le présent document est volontairement indépendant de l'organisation fonctionnelle définitive de l'application. Il ne définit ni la navigation, ni le Shell, ni les écrans métier.

### 1.1. Versionnement de la charte

La charte a été créée en version 0.1. La version courante est indiquée dans l'en-tête, l'historique et le pied de document.

Toute modification du contenu de cette charte devra entraîner une augmentation de l'indice de version. Les évolutions successives doivent permettre de retrouver précisément la référence graphique utilisée lors d'une phase de conception ou d'implémentation.

- 0.x : phase de construction et de validation de la charte ;
- 1.0 : première version considérée comme référence graphique stable pour l'implémentation V6 ;
- après 1.0 : toute modification substantielle devra faire évoluer l'indice selon son importance.

Une modification ne doit pas être introduite silencieusement : la section **Historique des versions** doit être complétée.

---

## 2. Principes d'identité BATORYA

### 2.1. Positionnement visuel

BATORYA doit donner une impression :

- professionnelle ;
- moderne ;
- claire ;
- technique sans être froide ;
- maîtrisée ;
- légère et contemporaine ;
- adaptée à un usage quotidien professionnel.

L'interface ne doit pas rechercher une esthétique de logiciel de gestion traditionnel.

Elle doit privilégier une approche proche des interfaces modernes de bureau et des produits professionnels contemporains, avec une hiérarchie visuelle nette et une utilisation mesurée des effets.

### 2.2. Rôle des couleurs

La hiérarchie chromatique repose sur trois rôles :

| Rôle | Couleur de référence | Fonction |
|---|---|---|
| Identité / structure | Bleu BATORYA | identité, structure, navigation, éléments techniques |
| Accent / énergie | Orange BATORYA | action, mise en évidence, accent visuel |
| Structure de surface | Gris / blanc | fonds, surfaces, séparation et lisibilité |

**Principe directeur :**

> **Bleu = identité et structure. Orange = énergie et accent. Gris/blanc = structure et lisibilité.**

L'orange ne doit pas devenir la couleur dominante de l'interface.

### 2.3. Hiérarchie des surfaces

Le principe validé pour le mode clair est :

> **Le fond gris structure l'espace. Le blanc porte l'information.**

Les surfaces importantes — cartes, panneaux, formulaires, tableaux et zones de travail — utilisent principalement le blanc ou des blancs légèrement teintés.

Le fond général peut utiliser des nuances de gris bleuté et des dégradés très légers afin de créer une profondeur discrète.

---

## 3. Typographie

### 3.1. Famille typographique

Le prototype de référence utilise une pile système :

    -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif

Cette approche est retenue comme principe de référence pour les prototypes actuels.

Elle permet de respecter les conventions visuelles natives de macOS, Windows et des environnements compatibles.

Aucune police externe ne doit être introduite sans décision graphique explicite.

### 3.2. Principes typographiques

La typographie doit rester :

- sans empattement ;
- lisible ;
- sobre ;
- suffisamment espacée ;
- hiérarchisée par taille, graisse et contraste plutôt que par multiplication des familles.

Le prototype utilise notamment des graisses allant de 500 à 700 selon le niveau hiérarchique.

Les titres utilisent un espacement légèrement resserré, notamment sur les grands titres.

---

## 4. Palette — Mode clair

Cette palette constitue la **palette réellement utilisée dans le prototype Login + Splash actuellement validé**. Elle constitue la base de travail de la charte et non encore une liste exhaustive de tous les composants V6.

### 4.1. Couleurs fondamentales

| Token prototype | Valeur | Rôle |
|---|---:|---|
| --orange | #DC6E29 | accent principal, actions, titres d'accueil |
| --orange-soft2 | #C9823A | orange secondaire / transitions |
| --blue-soft | #5B86AE | bleu secondaire, profondeur, ombres |
| --blue-deep | #2E5D8C | bleu profond, éléments structurants |
| BATORYA blue | #35699E | bleu d'identité actuellement présent dans le prototype |
| --text | #1B1C1E | texte principal |
| --text-sec | #595C61 | texte secondaire |
| --bg | #E9EEF4 | fond principal bleuté |
| --bg-deep | #DCE5EF | fond secondaire / profondeur |
| --orange-soft | rgba(201,130,58,0.14) | accent orange très léger |

### 4.2. Couleurs fonctionnelles déjà présentes

Le prototype utilise également un vert de confirmation pour l'état final du Splash :

| Usage | Valeur |
|---|---|
| Succès / espace prêt | #4FA56A |

Cette couleur est fonctionnelle et ne doit pas être confondue avec la couleur d'identité BATORYA.

Les couleurs d'erreur, d'avertissement et d'information complémentaires restent à définir dans une prochaine version de la charte lorsque les composants fonctionnels correspondants seront étudiés.

### 4.3. Transparences

Le prototype utilise largement des couleurs semi-transparentes, notamment pour :

- les halos ;
- les surfaces vitrées ;
- les bordures ;
- les ombres ;
- les accents techniques.

Les transparences doivent rester discrètes. Elles servent à créer une profondeur ou une hiérarchie, pas à produire un effet décoratif permanent.

---

## 5. Mode clair — surfaces et profondeur

### 5.1. Fond général

Le prototype utilise une combinaison de :

- gris bleuté ;
- blanc cassé ;
- gris bleu plus profond ;
- halos bleu et orange très diffus.

Le fond ne doit pas être parfaitement plat lorsque l'environnement le justifie, mais les effets doivent rester suffisamment faibles pour ne jamais concurrencer le contenu.

### 5.2. Surface principale

Les panneaux principaux utilisent des blancs légèrement translucides ou légèrement teintés.

Exemple de référence du prototype :

    background: linear-gradient(145deg, rgba(255,255,255,.82), rgba(248,250,252,.68));

### 5.3. Bordures

Les bordures sont fines et discrètes.

Le prototype utilise notamment des bordures blanches semi-transparentes et des bordures bleu/gris très faibles.

Elles servent principalement à délimiter une surface lorsqu'un contraste d'arrière-plan ne suffit pas.

### 5.4. Ombres

Les ombres doivent créer une profondeur douce.

Elles doivent éviter :

- les ombres noires fortes ;
- les contours lourds ;
- l'effet « carte flottante » systématique.

Le bleu BATORYA peut être utilisé très légèrement dans les ombres afin de conserver la cohérence chromatique.

---

## 6. Formes et rayons

Le prototype établit une famille de rayons arrondis :

| Élément | Référence prototype |
|---|---:|
| Grand panneau | 20px |
| Sélecteur segmenté / bouton principal | 50px (forme pilule) |
| Contrôle de saisie / champ | 12px |
| Bouton principal | 13px |
| Champ | 12px |
| Petit élément / état actif | 9px |

Ces valeurs constituent des **références de conception**, pas encore un système de tokens définitif.

La règle générale est :

> Plus le composant est structurel, plus son rayon peut être important ; les petits contrôles utilisent des rayons plus modérés.

---

## 7. Composants graphiques

### 7.1. Boutons

Le bouton principal du prototype utilise :

- orange BATORYA ;
- texte blanc ;
- rayon de 13px ;
- hauteur de 50px dans le formulaire de connexion ;
- ombre légère ;
- mouvement très léger au survol ;
- retour à la position initiale à l'activation.

L'orange doit identifier l'action principale sans transformer tous les contrôles de l'interface en éléments orange.

### 7.2. Champs

Les champs du prototype utilisent :

- fond blanc ou blanc translucide ;
- bordure gris neutre très légère ;
- rayon de 12px ;
- hauteur de 48px ;
- texte principal sombre ;
- placeholder gris ;
- focus matérialisé par une bordure bleue et un halo bleu léger.

Le focus doit rester visible sans devenir agressif.

### 7.3. Sélecteurs segmentés

Le sélecteur « Se connecter / Créer mon espace » établit un principe réutilisable :

- conteneur légèrement teinté ;
- deux zones de même importance ;
- état actif porté par une surface blanche ;
- accent orange pour l'état actif ;
- curseur actif qui glisse d'une cellule à l'autre (environ 900 ms) ;
- couleur du libellé actif synchronisée avec le déplacement ;
- géométrie du sélecteur stable pendant le mouvement.

---

## 8. Iconographie et logo

### 8.1. Logo

Le logo BATORYA constitue l'élément d'identité principal.

Il doit conserver ses proportions et ne doit pas être déformé.

Les effets de profondeur peuvent être utilisés avec parcimonie, notamment sous forme de drop-shadow léger.

Le logo utilisé dans le prototype est la référence visuelle actuelle en attendant la finalisation de la nouvelle version du logo.

### 8.2. Iconographie

Les icônes devront privilégier une approche :

- simple ;
- lisible ;
- cohérente ;
- contemporaine ;
- adaptée à une interface professionnelle.

Les styles d'icônes ne doivent pas mélanger de manière anarchique des familles visuelles différentes.

Le choix définitif de la bibliothèque ou du système d'icônes sera documenté lorsque le Shell et les composants UI seront conçus.

---

## 9. Animation et mouvement

L'animation fait partie du langage graphique BATORYA mais doit rester fonctionnelle.

### 9.1. Principes

Les animations doivent :

- accompagner une transition ;
- matérialiser une transformation ;
- confirmer une action ;
- créer une continuité entre deux états.

Elles ne doivent pas ralentir artificiellement l'utilisation du logiciel.

### 9.2. Courbe de mouvement

Le prototype utilise principalement :

    cubic-bezier(0.22, 1, 0.36, 1)

pour les mouvements d'entrée et de transformation.

Cette courbe constitue une référence pour les animations de type « entrée / sortie / transformation ».

Les transitions simples utilisent également des ease courts.

### 9.3. Durées

Le prototype utilise plusieurs familles :

- environ 180–260ms : changements d'état simples ;
- environ 380–500ms : petites transformations visuelles ;
- environ 850–1200ms : transitions majeures ;
- environ 900 ms pour le glissement du curseur du sélecteur et le retournement du panneau Login → Splash ;
- environ 950 ms pour les changements de largeur, de hauteur, de padding et d'ombre du panneau lors du passage vers « Créer mon espace ».

Ces durées ne doivent pas être appliquées mécaniquement à tous les composants. Elles définissent des ordres de grandeur selon l'importance de la transition.

### 9.4. Réduction des animations

BATORYA doit respecter prefers-reduced-motion: reduce.

Les animations non essentielles doivent être supprimées ou fortement réduites.

La fonctionnalité et la compréhension de l'interface doivent rester identiques.

---

## 10. Login + Splash — référence visuelle V6

Les deux prototypes ci-dessous constituent les **références graphiques figées** des écrans Login + Splash :

- Mode clair : `docs/conception/references-ui/Login page-Splash.html` ;
- Mode sombre : `docs/conception/references-ui/Login page-Splash-Dark.html`.

Ils définissent, chacun pour leur thème, les références visuelles pour :

- la palette ;
- les surfaces ;
- les formes ;
- les champs ;
- les boutons ;
- la hiérarchie typographique ;
- les animations ;
- les effets de profondeur ;
- la relation bleu/orange ;
- le traitement du Splash.

Les deux prototypes sont considérés comme **figés**. Ils ne doivent être modifiés que sur demande explicite ou à la suite d'une décision de conception clairement validée. Toute évolution ultérieure de la charte ne modifie pas automatiquement ces fichiers.

Le Shell et le dashboard visibles dans ce prototype sont uniquement des éléments de démonstration de transition et **ne constituent pas la référence fonctionnelle ou structurelle de l'application**.

---


### 10.1. Comportements graphiques figés

Les deux prototypes fixent également les comportements visuels suivants :

- Le panneau Login et le panneau « Créer mon espace » partagent le même composant visuel ; le passage à l'enregistrement élargit le panneau et répartit les champs en deux colonnes sur écran suffisamment large.
- Le curseur du sélecteur « Se connecter / Créer mon espace » glisse physiquement entre les deux cellules. Le plan technique en arrière-plan reste fixe pendant ce changement ; seul son halo peut réagir subtilement.
- Après une connexion de démonstration, le même panneau effectue un retournement sur son axe vertical pour révéler le Splash. Le Splash présente le logo, le message d'accueil, l'anneau de progression, les étapes de préparation et la version.
- À la fin de la préparation, l'anneau devient vert (#4FA56A) et le statut « Espace prêt » est affiché ; aucune coche n'est ajoutée.
- Le passage du Splash vers l'écran de démonstration BATORYA se fait par une transition progressive. Cet écran reste une démonstration visuelle, pas une spécification du Shell ou du dashboard métier.
- Les deux prototypes prévoient une adaptation de prefers-reduced-motion ; l'implémentation devra préserver la compréhension des états lorsque les animations sont réduites.

Ces comportements sont des références de conception des prototypes, pas une preuve que l'authentification ou le démarrage métier sont déjà implémentés.

## 11. Mode sombre

### 11.1. Principe

Le mode sombre doit être une **déclinaison de la même identité BATORYA**, et non une seconde charte graphique.

Il doit conserver :

- la même hiérarchie ;
- les mêmes rôles chromatiques ;
- les mêmes formes ;
- les mêmes principes typographiques ;
- les mêmes principes d'animation.

Les valeurs de couleurs pourront cependant être adaptées afin de garantir le contraste et le confort visuel.

### 11.2. Palette et surfaces — référence du prototype sombre

| Token prototype | Valeur | Rôle |
|---|---:|---|
| --orange | #E37A38 | Accent principal, titres et actions |
| --orange-soft2 | #C98954 | Orange secondaire et nuances de transition |
| --blue-soft | #6D96BD | Bleu secondaire, profondeur et focus |
| --blue-deep | #3F6F9E | Bleu profond |
| --text | #F1F3F5 | Texte principal |
| --text-sec | #B7BDC5 | Texte secondaire |
| --bg | #10161D | Fond principal |
| --bg-deep | #17212C | Fond profond |
| Succès / espace prêt | #4FA56A | Confirmation de fin du Splash, sans coche |

Le prototype sombre utilise des surfaces vitrées foncées, des bordures claires discrètes et des ombres mêlant profondeur sombre et nuances orange. Les halos bleu et orange restent diffus : ils donnent de la profondeur sans devenir un contour lumineux permanent. Le panneau, les champs et les effets de profondeur sont conçus spécifiquement pour le sombre ; ils ne sont pas une inversion mécanique des styles clairs.

### 11.3. Ce qui ne doit pas être fait

Le mode sombre ne doit pas être obtenu par une simple inversion des couleurs du mode clair.

En particulier :

- le blanc ne devient pas automatiquement noir ;
- le bleu ne doit pas être simplement remplacé par un bleu plus foncé ;
- l'orange ne doit pas devenir excessivement lumineux ;
- les ombres du mode clair ne doivent pas être conservées telles quelles ;
- les surfaces doivent conserver plusieurs niveaux de profondeur.

### 11.4. Structure attendue

Le mode sombre devra définir au minimum :

- fond général ;
- surface principale ;
- surface secondaire ;
- surface élevée ;
- texte principal ;
- texte secondaire ;
- texte tertiaire ;
- bordure ;
- focus ;
- bleu BATORYA ;
- orange BATORYA ;
- succès ;
- erreur ;
- avertissement ;
- information.

Les valeurs de la palette sombre ci-dessous sont celles du prototype sombre validé. Elles constituent une référence pour ce prototype, sans prétendre définir à elles seules tous les tokens du futur système de thème.

---

## 12. Gestion du thème

Le système graphique V6 doit prévoir trois modes d'utilisation :

### Automatique

BATORYA suit la préférence de thème du système d'exploitation.

La détection côté interface pourra s'appuyer sur la préférence système prefers-color-scheme: dark.

BATORYA n'a pas besoin de connaître la programmation horaire définie dans le système : si l'utilisateur configure son système pour passer automatiquement du clair au sombre, BATORYA suit cette préférence.

### Clair

L'utilisateur force le thème clair indépendamment du système.

### Sombre

L'utilisateur force le thème sombre indépendamment du système.

**Valeur par défaut recommandée : Automatique.**

Le choix utilisateur doit être mémorisé localement dans les préférences de BATORYA.

---

## 13. Tokens graphiques — principe d'implémentation

La future implémentation UI ne doit pas disperser les couleurs et valeurs graphiques directement dans les composants.

Les éléments graphiques communs devront être centralisés sous forme de tokens ou variables de thème.

Exemple conceptuel :

    --bg-app
    --bg-surface
    --bg-surface-secondary
    --bg-surface-elevated
    --text-primary
    --text-secondary
    --text-tertiary
    --border
    --focus
    --accent-blue
    --accent-orange
    --success
    --warning
    --danger
    --info
    --shadow

Les noms définitifs pourront évoluer avec l'architecture UI, mais le principe est ferme :

> **Un choix graphique global doit être modifiable à un endroit central et être répercuté de manière cohérente dans l'interface.**

Les composants ne doivent pas recréer chacun leur propre interprétation du bleu, de l'orange, du texte secondaire ou des surfaces.

---

## 14. Éléments restant à définir

La présente version 0.3 ne prétend pas figer tous les composants de l'application.

Restent notamment à définir :

- palette fonctionnelle complète ;
- tokens définitifs ;
- grille et système d'espacement ;
- tailles typographiques complètes ;
- iconographie définitive ;
- composants de navigation ;
- tableaux ;
- badges ;
- alertes ;
- modales ;
- menus ;
- tooltips ;
- pagination ;
- états vides ;
- états de chargement ;
- composants métier ;
- déclinaison complète des composants métier en mode sombre ;
- règles responsive complètes.

Ces éléments seront ajoutés lorsque leur conception sera effectivement réalisée.

Ils ne doivent pas être inventés dans cette charte simplement pour compléter une liste.

---

## 15. Règle de cohérence

Toute nouvelle interface BATORYA Essentiel V6 devra être conçue en respectant cette charte.

Lorsqu'un besoin fonctionnel nécessite un élément visuel qui n'est pas couvert par la charte :

1. le composant est conçu ;
2. sa règle graphique est définie ;
3. la présente charte est mise à jour ;
4. l'indice de version est augmenté ;
5. le composant devient une référence réutilisable.

La charte est donc un **document vivant**, mais elle ne doit pas devenir un catalogue de décisions fonctionnelles.

---

## 16. Historique des versions

| Version | Date | Nature de l'évolution |
|---|---|---|
| 0.1 | 2026-10-05 | Création de la charte. Formalisation de l'identité commune, du mode clair issu du prototype Login + Splash, principes du mode sombre et gestion du thème. |
| 0.2 | 2026-10-05 | Version intermédiaire antérieure ; le détail de ses changements n'était pas consigné dans l'historique source. |
| 0.3 | 2026-10-09 | Alignement sur les versions actuelles et figées des prototypes Login + Splash clair et sombre ; documentation de la palette sombre, du sélecteur segmenté animé, du panneau de création d'espace, du plan technique fixe et de la transition Login → Splash → BATORYA. |

---

## 17. Références

### Prototype de référence

docs/conception/references-ui/Login page-Splash.html

### Références visuelles

Les références visuelles présentes dans docs/conception/references-ui/ peuvent servir à l'inspiration et à la comparaison, mais ne remplacent pas les règles de cette charte.

---

**Statut actuel :** charte en construction.  
**Version courante : 0.3**
