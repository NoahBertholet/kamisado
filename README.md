# Projet Kamisado – Bot IA

Auteurs :  
- Noah Bertholet (24371)  
- Rafaël Matthys (23032)

---

# Présentation

Dans ce projet, nous avons développé un bot capable de jouer au jeu Kamisado de manière autonome.

L’objectif principal était de créer une intelligence artificielle capable de prendre de bonnes décisions dans un temps limité. Pour cela, nous avons combiné plusieurs techniques simples mais efficaces afin d’obtenir un bot réactif et compétitif.

---

# Fonctionnement du bot

## Recherche des meilleurs coups

À chaque tour, le bot analyse les différents coups possibles avant de choisir celui qui semble le plus avantageux.

Il commence par vérifier :
- si un coup permet de gagner immédiatement ;
- si un coup risque de donner une victoire facile à l’adversaire.

Cela permet déjà d’éviter beaucoup d’erreurs simples.

---

## Évaluation des positions

Lorsque plusieurs coups sont possibles, le bot évalue les positions obtenues selon différents critères :

- la progression vers la ligne d’arrivée ;
- la position des pièces sur le plateau ;
- la mobilité des pièces ;
- les possibilités de déplacement.

Le bot privilégie donc les positions qui lui donnent plus d’options et qui le rapprochent de la victoire.

---

## Recherche en profondeur

Le bot utilise ensuite une recherche en profondeur pour anticiper plusieurs tours à l’avance.

Il explore les coups possibles de chaque joueur afin d’estimer quelles décisions sont les plus intéressantes sur le long terme.

Pour accélérer cette recherche, certains coups moins intéressants sont ignorés afin de gagner du temps.

---

## Gestion du temps

Le temps de réflexion du bot est limité à environ 2,8 secondes par tour.

Pour éviter de dépasser cette limite :
- le temps est vérifié régulièrement pendant les calculs ;
- le meilleur coup trouvé est sauvegardé au fur et à mesure ;
- si le temps arrive à la limite, le bot joue immédiatement le meilleur coup disponible.

---

# Optimisations utilisées

Plusieurs optimisations ont été ajoutées afin d’améliorer les performances du bot :

- tri des coups les plus intéressants ;
- limitation du nombre de coups analysés ;
- système de cache pour éviter des calculs inutiles ;
- recherche progressive en profondeur.

Ces optimisations permettent au bot d’analyser plus de situations dans le temps imparti.

---

# Technologies utilisées

Le projet a été réalisé en Python avec les bibliothèques suivantes :

- `socket` : communication avec le serveur ;
- `json` : échange des données ;
- `struct` : gestion du protocole réseau ;
- `threading` : exécution du bot ;
- `time` : gestion du temps ;
- `random` : choix de secours dans certains cas.

---

# Améliorations possibles

Plusieurs pistes d’amélioration pourraient encore être ajoutées :

- améliorer l’évaluation des positions ;
- optimiser davantage la gestion du temps ;
- analyser plus profondément certaines situations ;
- améliorer le système de cache.

---

# Conclusion

Ce projet nous a permis de mettre en pratique plusieurs notions importantes liées à l’intelligence artificielle et aux jeux de stratégie.

Le bot obtenu est capable de jouer rapidement tout en prenant des décisions cohérentes et efficaces.
