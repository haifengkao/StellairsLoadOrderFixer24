# -*- coding: utf-8 -*-
import json
from shutil import copyfile
import os
import ctypes  # An included library with Python install.

def abort(message):
    Mbox('', message, 0)
    sys.exit(1)
    
class Mod():
	def __init__(self, hashKey, name, modId):
		self.hashKey = hashKey
		self.name = name
		self.modId = modId
		self.sortedKey = name.encode("ascii", errors="ignore")


def sortedKey(mod):
	return mod.sortedKey

def getModList(data):
	modList = []
	for key, data in data.items():
		name = data['displayName']
		modId = data['gameRegistryId']
		mod = Mod(key, name, modId)
		modList.append(mod)
	modList.sort(key=sortedKey)
	return modList


def writeLoadOrder(idList, dlc_load):
    data = {}
    with open(dlc_load, 'r+') as json_file:
        data = json.load(json_file)

    if len(data) < 1: 
        abort('dlc_load.json loading failed')
    data["enabled_mods"] = idList

    with open(dlc_load, 'w') as json_file:
        json.dump(data, json_file)

def writeDisplayOrder(hashList, game_data):
    data = {}
    with open(game_data, 'r+') as json_file:
        data = json.load(json_file)
    if len(data) < 1:
        abort('game_data.json loading failed')
    data["modsOrder"] = hashList
    with open(game_data, 'w') as json_file:
        json.dump(data, json_file)

def run(settingPath):
	registry = os.path.join(settingPath, "mods_registry.json")
	dlc_load = os.path.join(settingPath, "dlc_load.json")
	copyfile(dlc_load, dlc_load + ".bak")
	game_data = os.path.join(settingPath, "game_data.json")
	copyfile(game_data, game_data + ".bak")

	modList = []
	with open(registry) as json_file:
		data = json.load(json_file)
		modList = getModList(data)
	if len(modList) <= 0:
            abort('no mod found')
	idList = [mod.modId for mod in modList]
	hashList = [mod.hashKey for mod in modList]
	writeDisplayOrder(hashList, game_data)
	writeLoadOrder(idList, dlc_load)

def Mbox(title, text, style):
	return ctypes.windll.user32.MessageBoxA(0, text, title, style)

setting = os.path.expanduser('~/Paradox Interactive/Stellaris')
# setting = "./"
run(setting)
Mbox('', 'done', 0)
