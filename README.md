# Macro Recorder

Trois outils d'automatisation Roblox dans une seule fenêtre :

- **Macro** — enregistre tes actions clavier/souris une fois et rejoue-les en boucle.
- **Autoclicker** — clique tout seul à la cadence (CPS) de ton choix.
- **Auto-Achat** — rachète automatiquement une boutique qui restock (graines, etc.).

## Installation

```bash
pip install -r requirements.txt
# Linux seulement — installer tkinter :
sudo apt install python3-tk
```

## Lancer

**Windows (le plus simple) :** double-clique sur **`Lancer_Macro.bat`**. Il vérifie Python, installe `pynput` tout seul et ouvre le menu.

**Manuel :**
```bash
python macro_recorder.py    # Windows
python3 macro_recorder.py   # Linux / Mac
```

## Utilisation

| Action | Bouton / Raccourci |
|---|---|
| Démarrer l'enregistrement | `F9` ou bouton vert |
| Arrêter l'enregistrement | `F10` ou bouton rouge |
| Lancer la lecture | `F5` ou bouton bleu |
| Stopper la lecture | `F6` ou bouton rouge |
| Toggle autoclicker | `F7` |
| Toggle auto-achat | `F8` |
| Capturer un bouton d'achat | `F3` |

Tous les raccourcis sont reconfigurables dans chaque onglet (bouton **Changer**).

## Options

- **Boucles** : nombre de répétitions (0 = infini)
- **Vitesse** : multiplicateur de vitesse (1.0 = vitesse réelle, 2.0 = 2× plus rapide)
- **Délai entre boucles** : pause en secondes entre chaque répétition

## Sauvegarder / Charger

Les macros sont sauvegardées en `.json` dans le dossier `macros/`. Tu peux les recharger plus tard.

## Auto-Achat (boutique qui restock)

Pour racheter une boutique à chaque restock (ex. la boutique de graines :
Carotte, Fraise, Myrtille…) sans rester devant l'écran. Tu **enregistres ta
routine d'achat une seule fois** — y compris les clics en deux étapes
(item → **Acheter**) et les **scrolls** pour atteindre les articles plus bas —
et le script la rejoue automatiquement à chaque restock.

**Mise en place (une seule fois) :**

1. Ouvre la boutique dans Roblox pour qu'elle reste affichée.
2. Va dans l'onglet **Auto-Achat** et clique **Enregistrer la routine**
   (ou appuie sur **`F3`**).
3. Dans Roblox, fais tes achats normalement : clique un article, clique
   **Acheter**, scrolle vers le bas, achète les suivants, etc.
4. Reviens et clique **Arrêter l'enreg.** (ou **`F3`** à nouveau).
5. Clique **Démarrer auto-achat** (ou **`F8`**). Le script rejoue ta routine,
   attend, puis recommence à chaque restock.

> Astuce : pendant un article en stock `x5`, clique 5 fois sur item → Acheter
> pour tout rafler. Les clics « en trop » quand le stock est vide ne font rien.

**Paramètres :**

| Réglage | Rôle | Défaut |
|---|---|---|
| Intervalle restock (s) | temps d'attente entre deux passes | `60` |
| Délai entre actions (ms) | pause entre chaque clic/scroll rejoué (laisse le temps au popup « Acheter » d'apparaître) | `400` |

> Restock toutes les 5 min → laisse l'intervalle à **60 s** : ça repasse au moins
> une fois par minute, donc aucun restock n'est manqué.

Les clics faits **sur la fenêtre de l'outil** pendant l'enregistrement sont
ignorés automatiquement (seuls comptent tes clics dans Roblox). La routine est
mémorisée dans `autobuy_routine.json` et rechargée au prochain lancement. Garde
la boutique ouverte et la fenêtre Roblox **à la même position**, sinon les
coordonnées enregistrées ne correspondent plus.
