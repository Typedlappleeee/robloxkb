# Macro Recorder

Enregistre tes actions clavier/souris une fois et rejoue-les en boucle.

## Telecharger

Clique sur le bouton vert **Code > Download ZIP**, extrais le dossier, puis double-clique sur **`Lancer_Macro.bat`**.

## Pré-requis

Installe **Python** : https://www.python.org/downloads/  
> Coche **"Add python.exe to PATH"** pendant l'installation !

Le `.bat` installe `pynput` automatiquement au premier lancement.

## Utilisation

| Action | Raccourci |
|---|---|
| Demarrer l'enregistrement | `F9` ou bouton vert |
| Arreter l'enregistrement | `F10` ou bouton rouge |
| Lancer la lecture | `F5` ou bouton bleu |
| Stopper la lecture | `F6` ou bouton rouge |

## Options

- **Boucles** : nombre de repetitions (0 = infini)
- **Vitesse** : multiplicateur (1.0 = vitesse reelle, 2.0 = 2x plus rapide)
- **Delai entre boucles** : pause en secondes entre chaque repetition

## Sauvegarder / Charger

Les macros sont sauvegardees en `.json` dans le dossier `macros/`.
