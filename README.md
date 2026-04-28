24371 Bertholet Noah 
23032 Matthys Rafaël

notre IA favorise le coup gagnant directement. Si ce n'est pas possible il favorise les coups qui amène le pion le plus vers le centre. 
Ensuite il calcule les coups possible de l'adversaire. Si le coup de notre bot permet de faire gagner l'adversaire il ne sera pas pris en compte. 
On utilise la bibliothèque socket pour communiquer avec le serveur, json pour formater les messages, struct pour gérer la taille des données envoyées, threading pour gérer les interactions en parallèle, et random pour choisir des coups aléatoires