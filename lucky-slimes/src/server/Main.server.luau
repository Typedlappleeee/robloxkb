-- Main : démarre le jeu côté serveur. C'est le premier script qui tourne.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Lighting = game:GetService("Lighting")

-- petite ambiance lumineuse et joyeuse
Lighting.ClockTime = 14
Lighting.Brightness = 2.5

-- on crée les "Remotes" AVANT de lancer les services qui s'en servent
require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Remotes"))

local DataService = require(script.Parent.DataService)
local GameService = require(script.Parent.GameService)

DataService.Init()
GameService.Init()

print("[Lucky Slimes] Serveur prêt 🍀")
