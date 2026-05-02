# 🤖 Projet Kamisado – Bot IA

**Auteurs :**  
- Noah Bertholet (24371)  
- Rafaël Matthys (23032)  

---

## 🧠 Stratégie de l’IA

Notre bot utilise une approche avancée combinant heuristiques et recherche en profondeur.

### 1. Détection des coups gagnants immédiats
Le bot vérifie d’abord si un coup permet de gagner immédiatement.  
Si c’est le cas, il est joué sans réflexion supplémentaire.

---

### 2. Évitement des défaites immédiates
Le bot simule chaque coup possible et vérifie si l’adversaire peut gagner au tour suivant.  
Les coups dangereux sont éliminés si possible.

---

### 3. Tri heuristique des coups
Avant la recherche, les coups sont triés pour améliorer l’efficacité :

- progression vers la ligne d’arrivée  
- distance parcourue  
- position centrale sur le plateau  
- potentiel de victoire rapide  

Seuls les meilleurs coups sont conservés pour limiter le temps de calcul.

---

### 4. Recherche Negamax avec élagage alpha-bêta
Le bot utilise l’algorithme **Negamax** avec **alpha-bêta pruning** :

- exploration des coups futurs
- réduction drastique du nombre de positions évaluées
- inversion des scores pour gérer les deux joueurs

Cela permet d’aller plus profond dans l’arbre de recherche.

---

### 5. Iterative Deepening (approfondissement progressif)
La recherche se fait par profondeur croissante :

- profondeur 1 → 2 → 3 → ...
- à chaque étape, le meilleur coup est sauvegardé
- si le temps expire, le bot retourne le meilleur coup connu

---

### 6. Table de transposition (cache)
Le bot mémorise les positions déjà évaluées :

- évite de recalculer des états identiques
- améliore fortement les performances
- limitée à une taille maximale (`CACHE_MAX_SIZE`)

---

### 7. Fonction d’évaluation avancée

L’évaluation d’une position prend en compte :

- progression vers la victoire  
- distance restante  
- position centrale  
- liberté de mouvement (cases libres devant)  
- possibilités de déplacement diagonales  
- mobilité globale (nombre de coups possibles)  

---

## 🧰 Technologies et bibliothèques utilisées

- `socket` : communication avec le serveur  
- `json` : sérialisation des messages  
- `struct` : gestion du protocole réseau  
- `threading` : exécution du serveur du bot  
- `random` : variabilité des messages et fallback  
- `time` : gestion stricte du temps  

---

## ⏱️ Gestion du temps

Le bot dispose d’un temps limité pour jouer (`TIME_LIMIT = 2.8s`).

### Fonctionnement :

- un **deadline global** est défini au début du calcul  
- des vérifications (`check_timeout`) sont faites dans toute la recherche  
- si le temps est dépassé :
  - arrêt immédiat de la recherche
  - retour du meilleur coup trouvé

Une **marge de sécurité** (`SAFETY_MARGIN`) est appliquée pour éviter tout dépassement.

---

## ⚙️ Optimisations implémentées

- Limitation du nombre de coups explorés :
  - `MAX_ROOT_MOVES` (racine)
  - `MAX_NEGAMAX_MOVES` (recherche)
- Tri heuristique des coups
- Alpha-bêta pruning
- Table de transposition
- Iterative deepening

---

## 💡 Améliorations possibles

- Meilleur ordering des coups (killer moves, history heuristic)
- Amélioration de la fonction d’évaluation
- Gestion plus fine du temps (estimation dynamique de profondeur)
- Ajout d’une détection de zugzwang / blocage
- Optimisation de la table de transposition (LRU au lieu de clear)

---
