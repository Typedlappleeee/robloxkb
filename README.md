# Macro Recorder

Enregistre tes actions clavier/souris une fois et rejoue-les en boucle.

## Installation

```bash
pip install -r requirements.txt
# Linux seulement — installer tkinter :
sudo apt install python3-tk
```

## Lancer

```bash
python3 macro_recorder.py
```

## Utilisation

| Action | Bouton / Raccourci |
|---|---|
| Démarrer l'enregistrement | `F9` ou bouton vert |
| Arrêter l'enregistrement | `F10` ou bouton rouge |
| Lancer la lecture | `F5` ou bouton bleu |
| Stopper la lecture | `F6` ou bouton rouge |

## Options

- **Boucles** : nombre de répétitions (0 = infini)
- **Vitesse** : multiplicateur de vitesse (1.0 = vitesse réelle, 2.0 = 2× plus rapide)
- **Délai entre boucles** : pause en secondes entre chaque répétition

## Sauvegarder / Charger

Les macros sont sauvegardées en `.json` dans le dossier `macros/`. Tu peux les recharger plus tard.
