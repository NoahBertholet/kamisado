# 🤖 Projet Kamisado – Bot IA

**Auteurs :**  
- Noah Bertholet (24371)  
- Rafaël Matthys (23032)  

---

## 🧠 Stratégie de l’IA

Notre bot utilise une stratégie basée sur des règles simples du jeu Kamisado.  
Il ne repose pas sur un algorithme complexe, mais sur une analyse des coups possibles à chaque tour.

1. **Recherche d’un coup gagnant**  
   Le bot commence par vérifier si un coup permet de gagner immédiatement la partie.  
   Si c’est le cas, ce coup est joué en priorité.

2. **Évitement des victoires adverses**  
   Pour chaque coup possible, le bot simule l’état du plateau après ce coup.  
   Il regarde ensuite si l’adversaire pourrait gagner directement au tour suivant.  
   Si un coup donne une victoire immédiate à l’adversaire, il est évité.

3. **Évaluation du déplacement**  
   Les coups restants reçoivent un score.  
   Le bot favorise les coups qui font avancer le pion vers la ligne de victoire, sans donner trop d’importance aux déplacements trop agressifs.

4. **Positionnement sur le plateau**  
   Le bot donne aussi un bonus aux coups qui rapprochent le pion du centre du plateau.  
   Une position centrale offre généralement plus de possibilités de déplacement.

5. **Analyse de la couleur imposée**  
   Dans Kamisado, la case d’arrivée détermine la couleur du pion que l’adversaire devra jouer.  
   Le bot prend donc en compte le nombre de coups que cette couleur donnera à l’adversaire.  
   Si l’adversaire n’a aucun coup possible, le coup reçoit un gros bonus.  
   Si l’adversaire a beaucoup de possibilités, le coup est pénalisé.

6. **Choix final**  
   Le bot choisit le coup avec le meilleur score.  
   Si plusieurs coups ont le même score, il en choisit un aléatoirement afin de garder une certaine variabilité.

---

## 🧰 Technologies et bibliothèques utilisées

Notre projet utilise plusieurs bibliothèques Python essentielles :

- `socket` : communication avec le serveur du jeu  
- `json` : formatage des messages échangés  
- `struct` : gestion de la taille des données envoyées  
- `threading` : gestion des tâches en parallèle  
- `random` : sélection aléatoire parmi plusieurs coups équivalents  
- `copy` : création d’une copie du plateau pour simuler les coups  
- `time` : gestion du temps afin de ne pas dépasser les 3 secondes  

---

## ⏱️ Gestion du temps

Le module `time` est utilisé pour contrôler le temps de réflexion du bot.

### Fonctionnement :

- Au début du calcul d’un coup, on enregistre le temps de départ  
- Pendant l’analyse, on vérifie régulièrement le temps écoulé  
- Si la limite de temps est atteinte :
  - le bot retourne le meilleur coup trouvé jusqu’à présent  
  - ou un coup déjà analysé  
  - ou en dernier recours, un coup aléatoire  

Cela garantit que le bot respecte toujours le temps imposé par le serveur.

---

## ⚙️ Améliorations possibles

- Amélioration de l’évaluation des positions  
- Meilleure anticipation des blocages futurs  
- Optimisation des performances  

---