-- Config : tous les réglages chiffrés du jeu, au même endroit.
-- (partagé client + serveur pour que les prix affichés = les prix réels)
-- N'hésite pas à changer ces nombres pour équilibrer le jeu à ton goût !

local Config = {}

-- Pièces de départ d'un nouveau joueur
Config.PIECES_DEPART = 0

-- ⏱️ Temps d'attente entre deux tirages (en secondes)
Config.COOLDOWN_BASE = 0.6 -- au niveau 0 de vitesse
Config.COOLDOWN_MIN = 0.05 -- on ne descend jamais en dessous
function Config.cooldown(niveauVitesse)
	return math.max(Config.COOLDOWN_MIN, Config.COOLDOWN_BASE - niveauVitesse * 0.06)
end

-- 🍀 Bonus de chance : multiplicateur appliqué aux probabilités de rareté
function Config.multiChance(niveauChance)
	return 1 + niveauChance * 0.5 -- +50% de chance par niveau
end

-- 💰 Coûts des améliorations (montent à chaque niveau acheté)
function Config.coutChance(niveau)
	return math.floor(100 * (1.8 ^ niveau))
end
function Config.coutVitesse(niveau)
	return math.floor(120 * (1.9 ^ niveau))
end

return Config
