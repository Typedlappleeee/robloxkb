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

## Auto-Achat (boutique qui restock) — 100% automatique

Rachète une boutique à chaque restock (ex. la boutique de graines : Carotte,
Fraise, Myrtille…) **sans rien enregistrer**. L'outil **repère à l'écran** les
articles (cases sombres) et le **bouton d'achat doré**, puis clique dessus et
scrolle, automatiquement, à chaque restock.

**Utilisation :**

1. Ouvre la boutique dans Roblox pour qu'elle reste affichée.
2. Onglet **Auto-Achat** → clique **Tester la détection** (ou **`F3`**). Une
   image s'ouvre : **cadres verts** = articles repérés, **cercle orange** =
   bouton d'achat. Appuie sur une touche pour fermer.
3. Si la détection est bonne, clique **Démarrer auto-achat** (ou **`F8`**).
   Sinon, ajuste les deux curseurs (voir ci-dessous) et re-teste.

**Paramètres :**

| Réglage | Rôle | Défaut |
|---|---|---|
| Intervalle restock (s) | attente entre deux passes | `60` |
| Délai entre clics (ms) | pause entre chaque clic (laisse le temps au jeu de réagir) | `250` |
| Scrolls par passe | nombre de scrolls pour descendre la liste | `4` |
| Sensibilité articles | si des articles ne sont pas détectés, monte/baisse ce curseur | — |
| Tolérance bouton doré | élargit la couleur reconnue comme « bouton d'achat » | — |

> Restock toutes les 5 min → laisse l'intervalle à **60 s** : ça repasse au moins
> une fois par minute, donc aucun restock n'est manqué.

**À savoir :**

- Garde la boutique Roblox **ouverte et à la même place** (l'outil clique sur des
  positions à l'écran).
- Mets la **fenêtre de l'outil à l'écart de la boutique** : sinon les clics
  automatiques risquent de tomber sur l'outil au lieu du jeu.
- Idéalement **zoom d'affichage Windows à 100%** (sinon léger décalage possible).
- C'est de la détection visuelle : selon le jeu / la résolution, un petit
  réglage des deux curseurs via **Tester la détection** peut être nécessaire.
