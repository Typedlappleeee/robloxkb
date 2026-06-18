-- DataService : charge, garde en mémoire et sauvegarde la progression de chaque joueur.
-- La sauvegarde utilise les DataStores de Roblox.
--   ⚠️ Dans Studio, il faut activer "Enable Studio Access to API Services"
--      (Game Settings -> Security) sinon ça ne sauvegarde pas — mais le jeu
--      reste 100% jouable, ça ne plante pas.

local Players = game:GetService("Players")
local DataStoreService = game:GetService("DataStoreService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Remotes = require(Shared:WaitForChild("Remotes"))
local Config = require(Shared:WaitForChild("Config"))

-- on protège l'accès au DataStore : s'il n'est pas dispo, "store" reste nil
-- et on jouera en mémoire (sans sauvegarde entre les sessions)
local store
pcall(function()
	store = DataStoreService:GetDataStore("LuckySlimes_v1")
end)

local function DEFAUT()
	return {
		pieces = Config.PIECES_DEPART,
		niveauChance = 0,
		niveauVitesse = 0,
		inventaire = {}, -- slimes à vendre : { Commun = 5, Rare = 2 }
		decouverts = {}, -- collection : { Commun = true } (reste à vie)
	}
end

local DataService = {}
local cache = {} -- [player] = données

function DataService.charger(player)
	local data
	if store then
		local ok, res = pcall(function()
			return store:GetAsync("joueur_" .. player.UserId)
		end)
		if ok and res then
			data = res
		end
	end
	data = data or DEFAUT()

	-- on s'assure que toutes les clés existent (utile si on ajoute des trucs plus tard)
	for k, v in pairs(DEFAUT()) do
		if data[k] == nil then
			data[k] = v
		end
	end
	data.inventaire = data.inventaire or {}
	data.decouverts = data.decouverts or {}

	cache[player] = data
	return data
end

function DataService.obtenir(player)
	return cache[player]
end

function DataService.sauvegarder(player)
	local data = cache[player]
	if not data or not store then
		return
	end
	pcall(function()
		store:SetAsync("joueur_" .. player.UserId, data)
	end)
end

-- envoie au client une copie propre de ses données (pour mettre à jour l'écran)
function DataService.envoyer(player)
	local data = cache[player]
	if not data then
		return
	end
	Remotes.MajDonnees:FireClient(player, {
		pieces = data.pieces,
		niveauChance = data.niveauChance,
		niveauVitesse = data.niveauVitesse,
		inventaire = data.inventaire,
		decouverts = data.decouverts,
	})
end

function DataService.Init()
	Players.PlayerRemoving:Connect(function(player)
		DataService.sauvegarder(player)
		cache[player] = nil
	end)

	game:BindToClose(function()
		for _, player in ipairs(Players:GetPlayers()) do
			DataService.sauvegarder(player)
		end
		task.wait(1)
	end)

	-- sauvegarde automatique toutes les 60 secondes
	task.spawn(function()
		while true do
			task.wait(60)
			for player in pairs(cache) do
				DataService.sauvegarder(player)
			end
		end
	end)
end

return DataService
