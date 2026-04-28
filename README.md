# 🤖 Projet Kamisado – Bot IA

**Auteurs :**  
- Noah Bertholet (24371)  
- Rafaël Matthys (23032)  

---

## 🧠 Stratégie de l’IA

Notre bot repose sur une logique de prise de décision en plusieurs étapes, visant à maximiser ses chances de victoire tout en limitant les risques :

1. **Priorité au coup gagnant**  
   Si un coup permet de gagner immédiatement la partie, il est joué sans hésitation.

2. **Avancement stratégique vers le centre**  
   En l’absence de victoire directe, l’IA privilégie les coups qui rapprochent ses pions du centre du plateau, offrant généralement plus d’options de déplacement et de contrôle.

3. **Analyse des coups adverses**  
   Pour chaque coup envisageable, le bot simule les réponses possibles de l’adversaire.

4. **Évitement des coups dangereux**  
   Si un coup permet à l’adversaire de gagner au tour suivant, il est automatiquement rejeté.

5. **Choix final**  
   Parmi les coups restants, un choix est effectué (parfois aléatoire) afin de conserver une certaine variabilité dans le jeu.

---

## 🧰 Technologies et bibliothèques utilisées

Notre projet utilise plusieurs bibliothèques Python essentielles :

- `socket` : communication avec le serveur du jeu  
- `json` : formatage des messages échangés  
- `struct` : gestion de la taille des données envoyées  
- `threading` : gestion des tâches en parallèle  
- `random` : sélection aléatoire de coups  

---

## ⏱️ Gestion du temps (`time`)

Le module `time` est utilisé pour contrôler le temps de réflexion de notre IA.

Dans un environnement compétitif, le bot dispose d’un temps limité pour jouer. Nous utilisons donc :

- `time.time()` : retourne le temps actuel en secondes  

### Fonctionnement :

- Au début du calcul d’un coup, on enregistre le temps de départ  
- Pendant les calculs, on vérifie régulièrement le temps écoulé  
- Si la limite de temps est atteinte :
  - le bot retourne le meilleur coup trouvé jusqu’à présent  
  - ou un coup déjà analysé  
  - ou en dernier recours, un coup aléatoire  

Cela garantit que le bot respecte toujours le temps imposé.

---

## ⚙️ Améliorations possibles

- Amélioration de l’évaluation des coups  
- Meilleure gestion des positions (blocages, mobilité, etc.)  
- Optimisation des performances  

---