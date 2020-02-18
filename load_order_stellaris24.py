# -*- coding: utf-8 -*-
import json
from shutil import copyfile
import os
import ctypes  # An included library with Python install.
import sys
import traceback
import platform


def abort(message):
    Mbox('abort', message, 0)
    sys.exit(1)


class Mod():
    def __init__(self, hashKey, name, modId):
        self.hashKey = hashKey
        self.name = name
        self.modId = modId
        self.sortedKey = name.encode('ascii', errors='ignore')


def sortedKey(mod):
    return mod.sortedKey


def getModList(data):
    modList = []
    for key, data in data.items():
        try:
            name = data['displayName']
            modId = data['gameRegistryId']
            mod = Mod(key, name, modId)
            modList.append(mod)
        except KeyError:
            try:
                name = data['displayName']
                modId = data['steamId']
                mod = Mod(key, name, modId)
                modList.append(mod)
            except KeyError:
                print('key not found in ', key, data)
    modList.sort(key=sortedKey, reverse=True)
    return modList


def tweakModOrder(list):
    for i in range(len(list) - 1, 0, -1):
        j = i - 1
        if list[j].sortedKey.startswith(list[i].sortedKey):
            tmp = list[j]
            list[j] = list[i]
            list[i] = tmp
    return list


def specialOrder(mods):
    specialNames = ["UI Overhaul Dynamic", "Dark UI", "Dark U1"]
    specialList = []
    for specialName in specialNames:
        toBeRemoved = []
        for mod in mods:
            if specialName in mod.name:
                specialList.append(mod)
                toBeRemoved.append(mod)

        for mod in toBeRemoved:
            mods.remove(mod)
    return mods + specialList


def writeLoadOrder(idList, dlc_load, enabled_mods):
    data = {}
    with open(dlc_load, 'r+') as json_file:
        data = json.load(json_file)

    if len(data) < 1:
        abort('dlc_load.json loading failed')

    if enabled_mods is not None:
        idList = [m for m in idList if m in enabled_mods]

    data['enabled_mods'] = idList

    with open(dlc_load, 'w') as json_file:
        json.dump(data, json_file)


def writeDisplayOrder(hashList, game_data):
    data = {}
    with open(game_data, 'r+') as json_file:
        data = json.load(json_file)
    if len(data) < 1:
        abort('game_data.json loading failed')

    data['modsOrder'] = hashList
    with open(game_data, 'w') as json_file:
        json.dump(data, json_file)


def run(settingPath):
    registry = os.path.join(settingPath, 'mods_registry.json')

    dlc_load = os.path.join(settingPath, 'dlc_load.json')
    if os.path.isfile(dlc_load):
        copyfile(dlc_load, dlc_load + '.bak')
    else:
        abort('please enable at least one mod')

    enabled_mods = None
    if os.path.exists(dlc_load):
        with open(dlc_load) as dlc_load_file:
            dlc_load_data = json.load(dlc_load_file)

            # Do some legwork ahead of time to put into a set to avoidic quadratic loop later for filtering.
            enabled_mods = frozenset(dlc_load_data.get("enabled_mods", []))

    game_data = os.path.join(settingPath, 'game_data.json')
    copyfile(game_data, game_data + '.bak')

    modList = []
    with open(registry, encoding='UTF-8') as json_file:
        data = json.load(json_file)
        modList = getModList(data)

        # move Dark UI and UIOverhual to the bottom
        modList = specialOrder(modList)
        # make sure UIOverhual+SpeedDial will load after UIOverhual
        modList = tweakModOrder(modList)
    if len(modList) <= 0:
        abort('no mod found')
    idList = [mod.modId for mod in modList]
    hashList = [mod.hashKey for mod in modList]
    writeDisplayOrder(hashList, game_data)
    writeLoadOrder(idList, dlc_load, enabled_mods)


def Mbox(title, text, style):
    if platform.system() == 'Windows':
        return ctypes.windll.user32.MessageBoxW(0, text, title, style)
    else:
        print(title + ": " + text)


def errorMesssage(error):
    error_class = e.__class__.__name__  # 取得錯誤類型
    detail = e.args[0]  # 取得詳細內容
    _, _, tb = sys.exc_info()  # 取得Call Stack
    lastCallStack = traceback.extract_tb(tb)[-1]  # 取得Call Stack的最後一筆資料
    fileName = lastCallStack[0]  # 取得發生的檔案名稱
    lineNum = lastCallStack[1]  # 取得發生的行號
    funcName = lastCallStack[2]  # 取得發生的函數名稱
    return "File \"{}\", line {}, in {}: [{}] {}".format(
        fileName, lineNum, funcName, error_class, detail)


def test():
    mod1 = Mod("", "!(", "")
    mod2 = Mod("", "!（更多中文", "")
    mod3 = Mod("", "UI + PD", "")
    mod4 = Mod("", "UI", "")
    mod5 = Mod("", "UI + Speed Dial", "")
    modList = [mod1, mod2, mod3, mod4, mod5]
    modList.sort(key=sortedKey, reverse=True)
    print([x.sortedKey for x in modList])
    tweaked = tweakModOrder(modList)
    print([x.sortedKey for x in tweaked])


try:
    # sys.setdefaultencoding() does not exist, here!
    reload(sys)  # Reload does the trick!
    sys.setdefaultencoding('UTF8')
except:
    print('set encoding failed')

# check Stellaris settings location
locations = [
    ".", "..",
    os.path.join(os.path.expanduser('~'), 'Documents', 'Paradox Interactive',
                 'Stellaris'),
    os.path.join(os.path.expanduser('~'), '.local', 'share',
                 'Paradox Interactive', 'Stellaris')
]
settingPaths = [
    settingPath for settingPath in locations
    if os.path.isfile(os.path.join(settingPath, "mods_registry.json"))
]
if (len(settingPaths) > 0):
    print('find Stellaris setting at ', settingPaths[0])
    try:
        run(settingPaths[0])
        Mbox('', 'done', 0)
    except Exception as e:
        print(errorMesssage(e))
        Mbox('error', errorMesssage(e), 0)
else:
    Mbox('error', 'unable to location "mods_registry.json', 0)
