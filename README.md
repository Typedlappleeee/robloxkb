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

Pour racheter tout le stock d'une boutique à chaque restock (ex. la boutique de
graines : Carotte, Fraise, Myrtille…), sans rester devant l'écran.

**Mise en place (une seule fois) :**

1. Ouvre la boutique dans Roblox pour qu'elle reste affichée.
2. Va dans l'onglet **Auto-Achat**.
3. Pour chaque article, place la souris sur son bouton d'achat et appuie sur
   **`F3`** (ou clique **Capturer (3s)** puis place la souris). Le point apparaît
   dans la liste. Recommence pour chaque graine.
4. Règle les paramètres puis clique **Démarrer auto-achat** (ou **`F8`**).

Le script reclique chaque bouton capturé, attend, puis recommence à chaque restock.

**Paramètres :**

| Réglage | Rôle | Défaut |
|---|---|---|
| Intervalle restock (s) | temps entre deux passes d'achat | `60` |
| Clics par article | nombre de clics sur chaque bouton (pour vider le stock) | `10` |
| Délai entre clics (ms) | pause entre chaque clic | `150` |

> Restock toutes les 5 min → laisse l'intervalle à **60 s** : ça repasse au moins
> une fois par minute, donc aucun restock n'est manqué.

Les boutons capturés sont mémorisés automatiquement dans `autobuy_points.json` et
rechargés au prochain lancement. Garde la boutique ouverte et la fenêtre Roblox à
la même position, sinon les coordonnées ne correspondent plus.
