-- Remotes : crée (côté serveur) et récupère (côté client) les "RemoteEvents",
-- c'est-à-dire les canaux qui permettent au client et au serveur de se parler.
-- Tu n'as normalement jamais besoin de toucher ce fichier.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local NOMS = {
	"Rouler", -- client -> serveur : "je tente ma chance"
	"Vendre", -- client -> serveur : "je vends tous mes slimes"
	"AcheterAmelioration", -- client -> serveur : "j'achète chance/vitesse"
	"Pret", -- client -> serveur : "je suis chargé, envoie-moi mes données"
	"Resultat", -- serveur -> client : "voici le slime que tu as obtenu"
	"MajDonnees", -- serveur -> client : "voici tes données à jour (pièces, etc.)"
	"Notif", -- serveur -> client : "petit message à afficher"
}

local dossier
if RunService:IsServer() then
	dossier = ReplicatedStorage:FindFirstChild("Remotes")
	if not dossier then
		dossier = Instance.new("Folder")
		dossier.Name = "Remotes"
		dossier.Parent = ReplicatedStorage
	end
	for _, nom in ipairs(NOMS) do
		if not dossier:FindFirstChild(nom) then
			local re = Instance.new("RemoteEvent")
			re.Name = nom
			re.Parent = dossier
		end
	end
else
	dossier = ReplicatedStorage:WaitForChild("Remotes")
end

local Remotes = {}
for _, nom in ipairs(NOMS) do
	Remotes[nom] = dossier:WaitForChild(nom)
end

return Remotes
