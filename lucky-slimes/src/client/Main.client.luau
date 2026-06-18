-- Main (client) : construit tout l'écran du joueur par code, et gère les clics.
-- Tout ce que le joueur voit (boutons, carte de slime, collection) est créé ici.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Remotes = require(Shared:WaitForChild("Remotes"))
local SlimeData = require(Shared:WaitForChild("SlimeData"))
local Config = require(Shared:WaitForChild("Config"))

-- copie locale des données du joueur (mise à jour par le serveur)
local donnees = {
	pieces = 0,
	niveauChance = 0,
	niveauVitesse = 0,
	inventaire = {},
	decouverts = {},
}
local enAttente = false -- pour respecter le temps d'attente entre 2 tirages

-- ============ PETITS OUTILS POUR CRÉER L'INTERFACE ============
local function coin(inst, rayon)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, rayon)
	c.Parent = inst
end

local function cercle(inst)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(1, 0)
	c.Parent = inst
end

local function texte(parent, props)
	local t = Instance.new(props.bouton and "TextButton" or "TextLabel")
	t.Size = props.size
	t.Position = props.pos
	t.AnchorPoint = props.ancre or Vector2.new(0, 0)
	t.BackgroundColor3 = props.bg or Color3.fromRGB(40, 40, 60)
	t.BackgroundTransparency = props.bgt or 0
	t.TextColor3 = props.tc or Color3.new(1, 1, 1)
	t.Font = props.font or Enum.Font.FredokaOne
	t.TextScaled = true
	t.Text = props.txt or ""
	if t:IsA("TextButton") then
		t.AutoButtonColor = true
	end
	if props.stroke then
		t.TextStrokeTransparency = props.stroke
	end
	coin(t, props.rayon or 12)
	t.Parent = parent
	return t
end

-- ============ L'ÉCRAN ============
local gui = Instance.new("ScreenGui")
gui.Name = "LuckySlimesUI"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.Parent = playerGui

-- voile de couleur pour les "flashs" lors d'une rareté
local flash = Instance.new("Frame")
flash.Size = UDim2.new(1, 0, 1, 0)
flash.BackgroundColor3 = Color3.new(1, 1, 1)
flash.BackgroundTransparency = 1
flash.ZIndex = 0
flash.Parent = gui

-- compteur de pièces (en haut)
local lblPieces = texte(gui, {
	size = UDim2.new(0, 240, 0, 56),
	pos = UDim2.new(0.5, 0, 0, 12),
	ancre = Vector2.new(0.5, 0),
	bg = Color3.fromRGB(35, 35, 55),
	bgt = 0.1,
	tc = Color3.fromRGB(255, 230, 120),
	txt = "🪙 0",
})

-- titre
texte(gui, {
	size = UDim2.new(0, 360, 0, 44),
	pos = UDim2.new(0.5, 0, 0, 74),
	ancre = Vector2.new(0.5, 0),
	bg = Color3.new(0, 0, 0),
	bgt = 1,
	txt = "🍀 LUCKY SLIMES 🌈",
	stroke = 0,
})

-- message de notification (apparaît puis disparaît)
local lblNotif = texte(gui, {
	size = UDim2.new(0, 460, 0, 50),
	pos = UDim2.new(0.5, 0, 0, 124),
	ancre = Vector2.new(0.5, 0),
	bg = Color3.fromRGB(25, 120, 70),
	txt = "",
})
lblNotif.Visible = false

-- ---- la carte de révélation au centre ----
local carte = Instance.new("Frame")
carte.Size = UDim2.new(0, 260, 0, 300)
carte.Position = UDim2.new(0.5, 0, 0.43, 0)
carte.AnchorPoint = Vector2.new(0.5, 0.5)
carte.BackgroundColor3 = Color3.fromRGB(30, 30, 48)
carte.BackgroundTransparency = 0.1
coin(carte, 20)
carte.Parent = gui
local carteScale = Instance.new("UIScale")
carteScale.Parent = carte

-- le corps du slime (un gros rond) + ses yeux
local corps = Instance.new("Frame")
corps.Size = UDim2.new(0, 130, 0, 130)
corps.Position = UDim2.new(0.5, 0, 0, 28)
corps.AnchorPoint = Vector2.new(0.5, 0)
corps.BackgroundColor3 = Color3.fromRGB(120, 205, 120)
cercle(corps)
corps.Parent = carte

local function oeil(px)
	local e = Instance.new("Frame")
	e.Size = UDim2.new(0, 30, 0, 30)
	e.Position = UDim2.new(px, 0, 0.34, 0)
	e.AnchorPoint = Vector2.new(0.5, 0.5)
	e.BackgroundColor3 = Color3.new(1, 1, 1)
	cercle(e)
	e.Parent = corps
	local p = Instance.new("Frame")
	p.Size = UDim2.new(0, 13, 0, 13)
	p.Position = UDim2.new(0.5, 0, 0.6, 0)
	p.AnchorPoint = Vector2.new(0.5, 0.5)
	p.BackgroundColor3 = Color3.new(0, 0, 0)
	cercle(p)
	p.Parent = e
end
oeil(0.33)
oeil(0.67)

local lblNom = texte(carte, {
	size = UDim2.new(1, -20, 0, 44),
	pos = UDim2.new(0.5, 0, 0, 168),
	ancre = Vector2.new(0.5, 0),
	bg = Color3.new(0, 0, 0),
	bgt = 1,
	txt = "Clique sur ROULER !",
	stroke = 0,
})
local lblSurN = texte(carte, {
	size = UDim2.new(1, -20, 0, 26),
	pos = UDim2.new(0.5, 0, 0, 212),
	ancre = Vector2.new(0.5, 0),
	bg = Color3.new(0, 0, 0),
	bgt = 1,
	txt = "",
	tc = Color3.fromRGB(205, 205, 215),
	stroke = 0.6,
})
local lblValeur = texte(carte, {
	size = UDim2.new(1, -20, 0, 30),
	pos = UDim2.new(0.5, 0, 0, 242),
	ancre = Vector2.new(0.5, 0),
	bg = Color3.new(0, 0, 0),
	bgt = 1,
	txt = "",
	tc = Color3.fromRGB(255, 230, 120),
	stroke = 0.6,
})
local badge = texte(carte, {
	size = UDim2.new(0, 140, 0, 30),
	pos = UDim2.new(0.5, 0, 0, 0),
	ancre = Vector2.new(0.5, 0.5),
	bg = Color3.fromRGB(230, 50, 110),
	txt = "✨ NOUVEAU ✨",
})
badge.Visible = false

-- ---- boutons du bas ----
texte(gui, {
	size = UDim2.new(0, 460, 0, 26),
	pos = UDim2.new(0.5, 0, 1, -156),
	ancre = Vector2.new(0.5, 1),
	bg = Color3.new(0, 0, 0),
	bgt = 1,
	txt = "Appuie sur 🎰 ROULER (ou la touche R) pour tenter ta chance !",
	stroke = 0.5,
})

local btnRoll = texte(gui, {
	bouton = true,
	size = UDim2.new(0, 280, 0, 70),
	pos = UDim2.new(0.5, 0, 1, -78),
	ancre = Vector2.new(0.5, 1),
	bg = Color3.fromRGB(80, 175, 90),
	txt = "🎰 ROULER",
})
local btnChance = texte(gui, {
	bouton = true,
	size = UDim2.new(0, 160, 0, 56),
	pos = UDim2.new(0.5, -250, 1, -12),
	ancre = Vector2.new(0.5, 1),
	bg = Color3.fromRGB(70, 160, 80),
	txt = "🍀 Chance",
})
local btnVendre = texte(gui, {
	bouton = true,
	size = UDim2.new(0, 200, 0, 56),
	pos = UDim2.new(0.5, 0, 1, -12),
	ancre = Vector2.new(0.5, 1),
	bg = Color3.fromRGB(210, 160, 40),
	txt = "💰 VENDRE",
})
local btnVitesse = texte(gui, {
	bouton = true,
	size = UDim2.new(0, 160, 0, 56),
	pos = UDim2.new(0.5, 250, 1, -12),
	ancre = Vector2.new(0.5, 1),
	bg = Color3.fromRGB(70, 110, 200),
	txt = "⚡ Vitesse",
})

-- ---- panneau collection (à droite) ----
local btnIndex = texte(gui, {
	bouton = true,
	size = UDim2.new(0, 140, 0, 48),
	pos = UDim2.new(1, -12, 0, 12),
	ancre = Vector2.new(1, 0),
	bg = Color3.fromRGB(95, 70, 145),
	txt = "📒 Collection",
})

local panneau = Instance.new("Frame")
panneau.Size = UDim2.new(0, 250, 0, 320)
panneau.Position = UDim2.new(1, -12, 0, 68)
panneau.AnchorPoint = Vector2.new(1, 0)
panneau.BackgroundColor3 = Color3.fromRGB(28, 28, 44)
panneau.BackgroundTransparency = 0.1
panneau.Visible = false
coin(panneau, 16)
panneau.Parent = gui
texte(panneau, {
	size = UDim2.new(1, -16, 0, 32),
	pos = UDim2.new(0.5, 0, 0, 8),
	ancre = Vector2.new(0.5, 0),
	bg = Color3.new(0, 0, 0),
	bgt = 1,
	txt = "📒 Ma collection",
})

local lignesIndex = {}
do
	local tries = {}
	for _, s in ipairs(SlimeData.liste) do
		table.insert(tries, s)
	end
	table.sort(tries, function(a, b)
		return a.rang < b.rang
	end)
	for i, s in ipairs(tries) do
		local y = 48 + (i - 1) * 42
		local swatch = Instance.new("Frame")
		swatch.Size = UDim2.new(0, 28, 0, 28)
		swatch.Position = UDim2.new(0, 12, 0, y)
		swatch.BackgroundColor3 = Color3.fromRGB(60, 60, 75)
		cercle(swatch)
		swatch.Parent = panneau
		local l = texte(panneau, {
			size = UDim2.new(1, -56, 0, 30),
			pos = UDim2.new(0, 48, 0, y - 1),
			bg = Color3.new(0, 0, 0),
			bgt = 1,
			txt = "??? — 🔒",
			tc = Color3.fromRGB(150, 150, 160),
			stroke = 0.6,
		})
		l.TextXAlignment = Enum.TextXAlignment.Left
		lignesIndex[s.id] = { swatch = swatch, label = l, slime = s }
	end
end
btnIndex.MouseButton1Click:Connect(function()
	panneau.Visible = not panneau.Visible
end)

-- ============ EFFETS & RÉVÉLATION ============
local function flashCouleur(couleur, force)
	flash.BackgroundColor3 = couleur
	flash.BackgroundTransparency = 1 - (force or 0.5)
	TweenService:Create(flash, TweenInfo.new(0.5), { BackgroundTransparency = 1 }):Play()
end

local rainbowToken = 0
local function flashArcEnCiel()
	rainbowToken += 1
	local mine = rainbowToken
	local couleurs = {
		Color3.fromRGB(255, 0, 0),
		Color3.fromRGB(255, 150, 0),
		Color3.fromRGB(255, 255, 0),
		Color3.fromRGB(0, 220, 60),
		Color3.fromRGB(0, 150, 255),
		Color3.fromRGB(150, 0, 255),
	}
	task.spawn(function()
		for _, c in ipairs(couleurs) do
			if mine ~= rainbowToken then
				return
			end
			flash.BackgroundColor3 = c
			flash.BackgroundTransparency = 0.35
			task.wait(0.12)
		end
		if mine == rainbowToken then
			TweenService:Create(flash, TweenInfo.new(0.5), { BackgroundTransparency = 1 }):Play()
		end
	end)
end

local function revele(id, nouveau)
	local s = SlimeData.parId[id]
	if not s then
		return
	end
	corps.BackgroundColor3 = s.couleur
	lblNom.Text = s.emoji .. " " .. string.upper(s.nom) .. " !"
	lblNom.TextColor3 = s.couleur
	lblSurN.Text = "1 chance sur " .. s.surN
	lblValeur.Text = "Vaut " .. s.valeur .. " 🪙"
	badge.Visible = nouveau

	-- petite animation "pop"
	carteScale.Scale = 0.6
	TweenService:Create(carteScale, TweenInfo.new(0.28, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 })
		:Play()

	-- effets spéciaux selon la rareté
	if s.arcEnCiel then
		flashArcEnCiel()
	elseif s.rang >= 4 then
		flashCouleur(s.couleur, 0.6)
	elseif s.rang >= 3 then
		flashCouleur(s.couleur, 0.35)
	end
end
Remotes.Resultat.OnClientEvent:Connect(revele)

-- ============ NOTIFICATIONS ============
local notToken = 0
local function notif(t)
	notToken += 1
	local mine = notToken
	lblNotif.Text = t
	lblNotif.Visible = true
	task.delay(2.4, function()
		if mine == notToken then
			lblNotif.Visible = false
		end
	end)
end
Remotes.Notif.OnClientEvent:Connect(notif)

-- ============ MISE À JOUR DE L'ÉCRAN ============
local function totalVente()
	local total = 0
	for id, n in pairs(donnees.inventaire) do
		local s = SlimeData.parId[id]
		if s then
			total += s.valeur * n
		end
	end
	return total
end

Remotes.MajDonnees.OnClientEvent:Connect(function(data)
	donnees = data
	donnees.inventaire = donnees.inventaire or {}
	donnees.decouverts = donnees.decouverts or {}

	lblPieces.Text = "🪙 " .. donnees.pieces

	local t = totalVente()
	btnVendre.Text = (t > 0) and ("💰 VENDRE +" .. t) or "💰 VENDRE"

	btnChance.Text = "🍀 Chance Niv." .. donnees.niveauChance .. "\n" .. Config.coutChance(donnees.niveauChance) .. " 🪙"
	btnVitesse.Text = "⚡ Vitesse Niv." .. donnees.niveauVitesse .. "\n" .. Config.coutVitesse(donnees.niveauVitesse) .. " 🪙"

	for id, ligne in pairs(lignesIndex) do
		if donnees.decouverts[id] then
			ligne.label.Text = ligne.slime.nom .. " — ✅"
			ligne.label.TextColor3 = Color3.new(1, 1, 1)
			ligne.swatch.BackgroundColor3 = ligne.slime.couleur
		else
			ligne.label.Text = "??? — 🔒"
			ligne.label.TextColor3 = Color3.fromRGB(150, 150, 160)
			ligne.swatch.BackgroundColor3 = Color3.fromRGB(60, 60, 75)
		end
	end
end)

-- ============ ACTIONS DES BOUTONS ============
btnVendre.MouseButton1Click:Connect(function()
	Remotes.Vendre:FireServer()
end)
btnChance.MouseButton1Click:Connect(function()
	Remotes.AcheterAmelioration:FireServer("chance")
end)
btnVitesse.MouseButton1Click:Connect(function()
	Remotes.AcheterAmelioration:FireServer("vitesse")
end)

local function faireRoll()
	if enAttente then
		return
	end
	enAttente = true
	Remotes.Rouler:FireServer()

	-- petit verrou visuel le temps du cooldown
	local cd = Config.cooldown(donnees.niveauVitesse)
	btnRoll.AutoButtonColor = false
	btnRoll.BackgroundColor3 = Color3.fromRGB(60, 120, 65)
	task.delay(cd, function()
		enAttente = false
		btnRoll.AutoButtonColor = true
		btnRoll.BackgroundColor3 = Color3.fromRGB(80, 175, 90)
	end)
end
btnRoll.MouseButton1Click:Connect(faireRoll)

-- touche R pour rouler vite
UserInputService.InputBegan:Connect(function(input, gpe)
	if gpe then
		return
	end
	if input.KeyCode == Enum.KeyCode.R then
		faireRoll()
	end
end)

-- on signale au serveur qu'on est prêt -> il nous renvoie nos données
Remotes.Pret:FireServer()
