-- GameService : toute la logique du jeu côté serveur.
--   - tirer un slime (la chance !)
--   - vendre les slimes
--   - acheter les améliorations (chance / vitesse)
--   - afficher le dernier slime sur un piédestal 3D
-- C'est le serveur qui décide de tout (un joueur ne peut pas tricher).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Remotes = require(Shared:WaitForChild("Remotes"))
local SlimeData = require(Shared:WaitForChild("SlimeData"))
local Config = require(Shared:WaitForChild("Config"))
local DataService = require(script.Parent.DataService)

local GameService = {}

local piedestaux = {} -- [player] = { model, boule, label }
local dernierRoll = {} -- [player] = os.clock()  (pour le temps d'attente)
local prochainOffset = 0 -- pour ne pas empiler les piédestaux

-- ============ PIÉDESTAL 3D (montre ton dernier slime) ============
local function creerPiedestal(player)
	local offsetX = prochainOffset
	prochainOffset += 16

	local model = Instance.new("Model")
	model.Name = "Piedestal_" .. player.Name

	local socle = Instance.new("Part")
	socle.Anchored = true
	socle.Shape = Enum.PartType.Cylinder
	socle.Size = Vector3.new(2, 8, 8)
	socle.CFrame = CFrame.new(offsetX, 1, 14) * CFrame.Angles(0, 0, math.rad(90))
	socle.Color = Color3.fromRGB(80, 80, 95)
	socle.Material = Enum.Material.SmoothPlastic
	socle.Parent = model

	local boule = Instance.new("Part")
	boule.Anchored = true
	boule.CanCollide = false
	boule.Shape = Enum.PartType.Ball
	boule.Size = Vector3.new(3, 3, 3)
	boule.Position = Vector3.new(offsetX, 3.5, 14)
	boule.Color = Color3.fromRGB(120, 205, 120)
	boule.Material = Enum.Material.SmoothPlastic
	boule.Parent = model

	local bb = Instance.new("BillboardGui")
	bb.Size = UDim2.new(0, 220, 0, 50)
	bb.StudsOffset = Vector3.new(0, 4, 0)
	bb.AlwaysOnTop = true
	bb.Parent = boule
	local lbl = Instance.new("TextLabel")
	lbl.Size = UDim2.new(1, 0, 1, 0)
	lbl.BackgroundTransparency = 1
	lbl.TextColor3 = Color3.new(1, 1, 1)
	lbl.TextStrokeTransparency = 0
	lbl.Font = Enum.Font.FredokaOne
	lbl.TextScaled = true
	lbl.Text = "🎰 " .. player.Name
	lbl.Parent = bb

	model.Parent = workspace
	piedestaux[player] = { model = model, boule = boule, label = lbl }
end

local function majPiedestal(player, slime)
	local p = piedestaux[player]
	if not p then
		return
	end
	local taille = 2 + slime.rang * 0.7
	p.boule.Size = Vector3.new(taille, taille, taille)
	p.boule.Position = Vector3.new(p.boule.Position.X, 2 + taille / 2, p.boule.Position.Z)
	p.boule.Color = slime.couleur
	p.boule.Material = (slime.rang >= 3) and Enum.Material.Neon or Enum.Material.SmoothPlastic
	p.label.Text = slime.emoji .. " " .. slime.nom
end

-- ============ ACTIONS ============
function GameService.rouler(player)
	local data = DataService.obtenir(player)
	if not data then
		return
	end

	-- temps d'attente entre deux tirages
	local cd = Config.cooldown(data.niveauVitesse)
	local now = os.clock()
	if dernierRoll[player] and (now - dernierRoll[player]) < cd then
		return
	end
	dernierRoll[player] = now

	-- LE TIRAGE 🎰
	local slime = SlimeData.tirer(Config.multiChance(data.niveauChance))
	data.inventaire[slime.id] = (data.inventaire[slime.id] or 0) + 1

	-- nouveau dans la collection ?
	local nouveau = not data.decouverts[slime.id]
	if nouveau then
		data.decouverts[slime.id] = true
	end

	majPiedestal(player, slime)
	Remotes.Resultat:FireClient(player, slime.id, nouveau)
	DataService.envoyer(player)
end

function GameService.vendre(player)
	local data = DataService.obtenir(player)
	if not data then
		return
	end
	local total = 0
	for id, n in pairs(data.inventaire) do
		local s = SlimeData.parId[id]
		if s then
			total += s.valeur * n
		end
	end
	if total > 0 then
		data.pieces += total
		data.inventaire = {}
		Remotes.Notif:FireClient(player, "💰 +" .. total .. " pièces !")
	else
		Remotes.Notif:FireClient(player, "🤷 Rien à vendre. Roule d'abord !")
	end
	DataService.envoyer(player)
end

function GameService.ameliorer(player, type_)
	local data = DataService.obtenir(player)
	if not data then
		return
	end
	if type_ == "chance" then
		local cout = Config.coutChance(data.niveauChance)
		if data.pieces >= cout then
			data.pieces -= cout
			data.niveauChance += 1
			Remotes.Notif:FireClient(player, "🍀 Chance améliorée ! Niveau " .. data.niveauChance)
		else
			Remotes.Notif:FireClient(player, "❌ Pas assez de pièces !")
		end
	elseif type_ == "vitesse" then
		local cout = Config.coutVitesse(data.niveauVitesse)
		if data.pieces >= cout then
			data.pieces -= cout
			data.niveauVitesse += 1
			Remotes.Notif:FireClient(player, "⚡ Vitesse améliorée ! Niveau " .. data.niveauVitesse)
		else
			Remotes.Notif:FireClient(player, "❌ Pas assez de pièces !")
		end
	end
	DataService.envoyer(player)
end

-- ============ DÉMARRAGE ============
function GameService.Init()
	local function onJoin(player)
		DataService.charger(player)
		creerPiedestal(player)
		DataService.envoyer(player)
	end
	Players.PlayerAdded:Connect(onJoin)
	for _, p in ipairs(Players:GetPlayers()) do
		task.spawn(onJoin, p)
	end

	Players.PlayerRemoving:Connect(function(player)
		local p = piedestaux[player]
		if p then
			p.model:Destroy()
		end
		piedestaux[player] = nil
		dernierRoll[player] = nil
	end)

	Remotes.Rouler.OnServerEvent:Connect(function(player)
		GameService.rouler(player)
	end)
	Remotes.Vendre.OnServerEvent:Connect(function(player)
		GameService.vendre(player)
	end)
	Remotes.AcheterAmelioration.OnServerEvent:Connect(function(player, type_)
		GameService.ameliorer(player, type_)
	end)
	Remotes.Pret.OnServerEvent:Connect(function(player)
		DataService.envoyer(player)
	end)
end

return GameService
