-- SlimeData : la liste de tous les slimes du jeu, classés par rareté.
--
-- Pour AJOUTER un slime : copie une ligne, change les valeurs, garde la liste
-- triée du PLUS RARE (en haut) au PLUS COMMUN (en bas).
--
-- Champs :
--   id      : nom interne unique (sans accent ni espace)
--   nom     : nom affiché au joueur
--   emoji   : petit emoji affiché à côté
--   rang    : 1 = commun ... 6 = secret (sert à la taille / au tri)
--   chance  : probabilité de tomber dessus à chaque tirage (entre 0 et 1)
--   surN    : version "1 chance sur N" (juste pour l'affichage)
--   valeur  : pièces gagnées en le vendant
--   couleur : couleur du slime
--   arcEnCiel (optionnel) : effet arc-en-ciel spécial à la révélation

local SlimeData = {}

SlimeData.liste = {
	{ id = "Secret",     nom = "Secret",     emoji = "🌈", rang = 6, chance = 0.0001, surN = 10000, valeur = 100000, couleur = Color3.fromRGB(25, 25, 30),   arcEnCiel = true },
	{ id = "Mythique",   nom = "Mythique",   emoji = "🌸", rang = 5, chance = 0.001,  surN = 1000,  valeur = 5000,   couleur = Color3.fromRGB(255, 70, 165) },
	{ id = "Legendaire", nom = "Légendaire", emoji = "🌟", rang = 4, chance = 0.004,  surN = 250,   valeur = 750,    couleur = Color3.fromRGB(255, 170, 0) },
	{ id = "Epique",     nom = "Épique",     emoji = "🟣", rang = 3, chance = 0.02,   surN = 50,    valeur = 100,    couleur = Color3.fromRGB(175, 80, 255) },
	{ id = "Rare",       nom = "Rare",       emoji = "🔵", rang = 2, chance = 0.1,    surN = 10,    valeur = 25,     couleur = Color3.fromRGB(60, 145, 255) },
	{ id = "Commun",     nom = "Commun",     emoji = "🟢", rang = 1, chance = 1,      surN = 1,     valeur = 5,      couleur = Color3.fromRGB(120, 205, 120) },
}

-- accès rapide par id : SlimeData.parId["Rare"]
SlimeData.parId = {}
for _, s in ipairs(SlimeData.liste) do
	SlimeData.parId[s.id] = s
end

-- Tire un slime au hasard.
-- luck = multiplicateur de chance (1 = normal, 2 = deux fois plus de chance, etc.)
-- On teste du plus rare au plus commun : le premier qui "passe" est gagné.
function SlimeData.tirer(luck)
	luck = luck or 1
	for _, s in ipairs(SlimeData.liste) do
		if s.id == "Commun" then
			return s -- filet de sécurité : on retombe toujours au moins sur commun
		end
		if math.random() < s.chance * luck then
			return s
		end
	end
	return SlimeData.parId.Commun
end

return SlimeData
