# Charte graphique BATORYA V6

**Version : 0.4**  
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

La palette validée pour les deux prototypes Login + Splash repose sur trois couleurs principales et une répartition visuelle indicative **60 / 30 / 10** :

| Part indicative | Couleur | Fonction |
|---|---|---|
| 60 % | Gris très clair #F4F7F8 en mode clair ; fonds anthracite/bleu-noir en mode sombre | surface de fond et respiration |
| 30 % | Bleu glacier #C8F3FF | halos, tracés techniques, détails et états actifs |
| 10 % | Orange BATORYA #FF5C23 | action principale, accent et mise en évidence |

Ces proportions sont un repère de composition, pas une mesure pixel par pixel. En mode sombre, le bleu glacier doit être dosé selon le contraste ; l'orange reste ponctuel pour éviter un rendu agressif.

**Principe directeur :**

> **Fond neutre = lisibilité. Bleu glacier = profondeur technique et états. Orange = action et accent.**

Les deux thèmes partagent les mêmes couleurs d'identité, mais adaptent les fonds, les surfaces, les textes et les transparences à leur environnement.

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

Cette palette correspond au prototype clair actuellement validé : docs/conception/references-ui/Login page-Splash.html. Les valeurs ci-dessous décrivent les couleurs de référence et les principaux tokens du prototype ; elles ne constituent pas encore le système exhaustif de composants V6.

### 4.1. Palette de référence

| Rôle | Valeur | Utilisation |
|---|---:|---|
| Fond clair principal | #F4F7F8 | fond général gris très clair, légèrement froid |
| Bleu glacier | #C8F3FF | halos, tracés techniques, détails, états actifs |
| Orange BATORYA | #FF5C23 | action principale et accents |
| Bleu pétrole profond | #24434A | contraste structurel et nuance sombre de la palette |
| Fond clair secondaire | #EAF0F2 | profondeur et variations du fond |
| Texte secondaire | #595C61 | libellés et informations secondaires |
| Succès / espace prêt | #4FA56A | confirmation de fin du Splash, sans coche |

La répartition 60 / 30 / 10 est indicative : elle guide l'équilibre visuel global, sans imposer ces proportions à chaque composant.

### 4.2. Tokens du prototype clair

Le prototype utilise actuellement les variables CSS suivantes :

| Token | Valeur actuelle |
|---|---|
| --orange | rgb(255, 94, 35) |
| --orange-soft2 | #FF5C23 |
| --blue-soft | #C8F3FF |
| --blue-deep | #24434A |
| --text | #ff5c23 |
| --text-sec | #595C61 |
| --bg | #F4F7F8 |
| --bg-deep | #EAF0F2 |
| --orange-soft | rgba(255, 92, 35, 0.12) |

Ces valeurs documentent fidèlement le prototype validé. Les tokens de couleur du texte devront être rationalisés au moment de la conception du système UI complet, sans modifier rétroactivement le prototype validé.

### 4.3. Couleurs fonctionnelles

Le vert de succès est réservé aux états de confirmation, notamment à la fin du Splash. Il ne fait pas partie de l'identité chromatique principale.

Les couleurs d'erreur, d'avertissement et d'information complémentaires restent à définir lorsque les composants fonctionnels correspondants seront étudiés.

### 4.4. Transparences

Les transparences servent notamment pour les halos, les surfaces vitrées, les bordures, les ombres et les accents techniques. Elles doivent rester discrètes et ne pas concurrencer le contenu.

## 5. Mode clair — surfaces et profondeur

### 5.1. Fond général

Le fond général de référence est #F4F7F8, avec des variations très légères vers #EAF0F2. Les halos bleu glacier et orange peuvent ajouter une profondeur diffuse, à condition de rester subtils.

### 5.2. Surface principale

Les panneaux principaux privilégient le blanc ou des blancs légèrement translucides. La surface doit rester distincte du fond sans recourir à une bordure lourde.

### 5.3. Bordures et ombres

Les bordures sont fines et discrètes. Les ombres créent une profondeur douce et peuvent intégrer une nuance de bleu ou d'orange à faible opacité. Éviter les ombres noires fortes, les contours lourds et l'effet « carte flottante » systématique.

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

Le mode sombre est une déclinaison nocturne de la même identité BATORYA, et non une seconde identité ni une inversion mécanique du mode clair. Les deux prototypes partagent le bleu glacier #C8F3FF et l'orange #FF5C23, tout en adaptant les surfaces, le contraste, les ombres et les transparences.

### 11.2. Palette de référence — prototype sombre

| Rôle / token | Valeur | Utilisation |
|---|---|---|
| Orange BATORYA --orange | #FF5C23 | action principale, accents |
| Orange clair secondaire --orange-soft2 | #FF9A72 | transitions et nuance secondaire |
| Bleu glacier --blue-soft | #C8F3FF | tracés techniques, focus, halos et détails actifs |
| Bleu pétrole profond --blue-deep | #24434A | nuance structurelle |
| Texte principal --text | #F1F3F5 | texte sur fond sombre |
| Texte secondaire --text-sec | #B7BDC5 | libellés et informations secondaires |
| Fond principal --bg | #10161D | fond anthracite |
| Fond profond --bg-deep | #17212C | profondeur bleu-noir |
| Succès / espace prêt | #4FA56A | confirmation de fin du Splash, sans coche |

Le prototype utilise des surfaces vitrées foncées, des bordures discrètes et des ombres profondes. Les halos bleu glacier et orange restent diffus. L'orange est réservé aux éléments d'accent et ne doit pas devenir une lueur omniprésente.

### 11.3. Règles de contraste et de profondeur

- Conserver plusieurs niveaux de surface pour distinguer le panneau, les champs et le fond.
- Employer le bleu glacier avec mesure : sa forte luminosité doit servir à souligner un état ou un tracé, pas à colorer toutes les bordures.
- Réserver l'orange aux actions et accents importants.
- Garder un contraste suffisant entre texte et fond ; le bleu glacier ne remplace pas automatiquement le texte courant.
- Ne pas reprendre telles quelles les ombres du mode clair : le sombre nécessite une profondeur et des transparences adaptées.

### 11.4. Tokens du prototype sombre

| Token | Valeur actuelle |
|---|---|
| --orange | #FF5C23 |
| --orange-soft2 | #FF9A72 |
| --blue-soft | #C8F3FF |
| --blue-deep | #24434A |
| --text | #F1F3F5 |
| --text-sec | #B7BDC5 |
| --bg | #10161D |
| --bg-deep | #17212C |
| --orange-soft | rgba(255, 92, 35, 0.16) |

Ces valeurs décrivent le prototype sombre validé. Elles ne prétendent pas définir à elles seules tous les tokens du futur système de thème.

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
| 0.3 | 2026-10-09 | Alignement sur les versions alors figées des prototypes Login + Splash clair et sombre ; documentation du sélecteur segmenté animé, du panneau de création d'espace, du plan technique fixe et de la transition Login → Splash → BATORYA. |
| 0.4 | 2026-10-09 | Mise à jour des palettes de référence après validation de la palette gris clair / bleu glacier / orange et harmonisation des tokens documentés pour les prototypes clair et sombre. |

---

## 17. Références

### Prototype de référence

docs/conception/references-ui/Login page-Splash.html

### Références visuelles

Les références visuelles présentes dans docs/conception/references-ui/ peuvent servir à l'inspiration et à la comparaison, mais ne remplacent pas les règles de cette charte.

---

**Statut actuel :** charte en construction.  
**Version courante : 0.4**
