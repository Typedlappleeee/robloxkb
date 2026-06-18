# 🍀 Lucky Slimes 🌈

Un petit jeu Roblox de **chance** : tu **roules** pour tomber sur des slimes plus ou
moins rares (Commun → Secret), tu les **vends** pour des pièces, et tu achètes des
**bonus de chance** pour décrocher les slimes les plus rares. Le but : **tous les
attraper** ! 📒

> Tu n'as **aucune compétence Roblox** à avoir : suis juste les étapes ci-dessous,
> c'est expliqué clic par clic. ⏱️ Compte ~15 min la première fois.

---

## 🎮 Comment on joue

- **🎰 ROULER** (ou la touche **R**) : tente ta chance, tu obtiens un slime au hasard.
- Plus c'est rare, plus la révélation est stylée (flash, arc-en-ciel ✨).
- **💰 VENDRE** : transforme tous tes slimes en pièces.
- **🍀 Chance** : améliore tes probas de tomber sur du rare.
- **⚡ Vitesse** : roule de plus en plus vite.
- **📒 Collection** : la liste des slimes que tu as déjà trouvés.

---

## 🛠️ Installation sur Windows (pas à pas)

On utilise un outil qui s'appelle **Rojo** : il envoie le code de ce dossier
directement dans Roblox Studio. C'est le pont entre les fichiers et le jeu.

### Étape 1 — Roblox Studio
Si ce n'est pas déjà fait, installe **Roblox Studio** :
https://create.roblox.com/ → bouton **Start Creating** (connecte-toi avec ton compte Roblox).

### Étape 2 — Visual Studio Code (gratuit)
Télécharge et installe **VS Code** : https://code.visualstudio.com/

### Étape 3 — L'extension Rojo
1. Ouvre VS Code.
2. À gauche, clique sur l'icône **Extensions** (les 4 carrés).
3. Cherche **`Rojo`** (l'éditeur est *evaera*) et clique **Install**.

### Étape 4 — Installer le plugin Rojo dans Studio
1. Dans VS Code, appuie sur **Ctrl+Shift+P** → tape **`Rojo: Open Menu`** → Entrée.
2. Dans le menu Rojo, clique **`Install Roblox Studio Plugin`**.
   (Ça ajoute un bouton "Rojo" dans Roblox Studio.)

### Étape 5 — Ouvrir le dossier du jeu
Dans VS Code : menu **File → Open Folder…** et choisis le dossier **`lucky-slimes`**.

### Étape 6 — Démarrer le serveur Rojo
1. **Ctrl+Shift+P** → **`Rojo: Open Menu`**.
2. Clique sur la petite flèche ▶️ à côté de **`default.project.json`** pour lancer le serveur.
   (Tu verras "Rojo server listening on port 34872" : c'est bon, laisse VS Code ouvert.)

### Étape 7 — Connecter Studio
1. Ouvre **Roblox Studio** → **New** → modèle **Baseplate** (le sol plat).
2. En haut, onglet **Plugins** → clique le bouton **Rojo** → **Connect**.
   → Tout le code du jeu apparaît tout seul dans Studio. 🎉

### Étape 8 — Jouer !
Appuie sur le bouton **Play** ▶️ (ou **F5**) en haut de Studio. Roule tes premiers slimes ! 🍀

---

## 💾 Activer la sauvegarde (optionnel mais conseillé)

Sans ça, le jeu marche mais ta progression repart à zéro à chaque test.

1. Dans Studio : onglet **Home** → **Game Settings**.
2. Section **Security** → active **Enable Studio Access to API Services** → **Save**.

*(La vraie sauvegarde entre deux parties marche surtout une fois le jeu publié, voir plus bas.)*

---

## 🚀 Publier le jeu (pour que tes potes y jouent)

Dans Studio : **File → Publish to Roblox As…** → **Create new game** → donne un nom →
**Create**. Ensuite, sur https://create.roblox.com/, ouvre le jeu et mets-le en
**Public** pour que tout le monde puisse y jouer.

---

## 🎨 Modifier le jeu toi-même (facile !)

- **Ajouter / changer les slimes et les raretés** :
  `src/shared/SlimeData.luau` → copie une ligne, change le nom, la couleur, la `chance`
  et la `valeur`. (Garde la liste triée : le plus rare en haut.)
- **Changer les prix, la chance, la vitesse** :
  `src/shared/Config.luau`.
- **Changer l'apparence des boutons / de l'écran** :
  `src/client/Main.client.luau`.

Après chaque modif, si le serveur Rojo tourne et que Studio est connecté, les
changements arrivent **automatiquement** dans Studio. ✨

---

## 🧩 Comment c'est organisé (pour info)

```
lucky-slimes/
├── default.project.json     ← dit à Rojo où mettre chaque fichier
└── src/
    ├── shared/   (code partagé client + serveur)
    │   ├── SlimeData.luau    ← les slimes et leurs raretés
    │   ├── Config.luau       ← les réglages (prix, chance, vitesse)
    │   └── Remotes.luau      ← la communication client/serveur
    ├── server/   (cerveau du jeu, sécurisé)
    │   ├── Main.server.luau  ← démarre tout
    │   ├── DataService.luau  ← sauvegarde la progression
    │   └── GameService.luau  ← tirage, vente, améliorations
    └── client/   (ce que le joueur voit)
        └── Main.client.luau  ← l'interface et les animations
```
