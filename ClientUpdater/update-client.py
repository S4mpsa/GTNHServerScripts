#Change this to the instance you want to modify (Keep the r in front)
clientDirectory = r"C:\Minecraft\Prism\instances\GregTech- New Horizons 2.3.4\.minecraft"

#Place the modpack .zips in the same folder as this script









import os
from zipfile import ZipFile
import shutil
import re
from difflib import SequenceMatcher

configChanges = 'permanentConfigs.txt'
extraModFolder = 'additionalMods'

#Files that should be ignored when updating
blacklist = ['banned-ips.json', 'banned-players.json', 'eula.txt', 'ops.json', 'server.properties', 'userache.json', 'whitelist.json', 'usercache.json']
#Keywords that are not useful for figuring out mod names and versions
fluff = [".jar", ".dirty", "1.7.10", "alpha", "beta", "universal", " ", "_MC", "GTNH"]

def numberRatio(name):
    if len(name) > 0:
        return sum(c.isdigit() for c in name) / len(name)
    else:
        return 0

def getModName(mod):
    pruned = mod
    for word in fluff:
        pruned = pruned.replace(word, '')
    pruned = pruned.replace('[', '-').replace(']', '-')
    tokens = pruned.split('-')
    name = []
    i = 0
    while i < len(tokens) and numberRatio(tokens[i]) < 0.5:
        name.append(tokens[i])
        i = i + 1
    if i < len(tokens):
        version = tokens[i]
    else:
        #Attempt to get version from name
        versionStart = re.search(r"\d", ''.join(name))
        candidate = ''
        if versionStart:
            candidate = ''.join(name)[versionStart.start():]
        if numberRatio(candidate) >= 0.5:
            version = candidate
            name = [''.join(name)[:versionStart.start()]]
        else:
            version = "Unknown"
    return mod, ''.join(name), version

def numbers(version):
    strVersion = ''.join([s for s in re.findall(r'\b\d+\b', version)])
    if len(strVersion) > 0:
        return int(strVersion)
    else:
        return 0

def compareVersions(newVersion, oldVersion):
    newTokens = newVersion.split('.')
    oldTokens = oldVersion.split('.')
    i = 0
    while i < len(newTokens):
        #New version has more versioning places, must be higher
        if i >= len(oldTokens):
            return True
        if numbers(newTokens[i]) > numbers(oldTokens[i]):
            return True
        i += 1
    return False

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

doOp = True
def updateMod(old, new, sourceFolder, destinationFolder):
    if doOp:
        os.remove(os.path.join(destinationFolder, old))
        shutil.copy(os.path.join(sourceFolder, new), os.path.join(destinationFolder, os.path.split(old)[0], new))

def addMod(new, sourceFolder, destinationFolder):
    if doOp:
        shutil.copy(os.path.join(sourceFolder, new), os.path.join(destinationFolder, new))

def removeMod(old, destinationFolder):
    if doOp:
        os.remove(os.path.join(destinationFolder, old))
def replaceFolder(old, new):
    existingFiles = os.listdir(old)
    newFiles = os.listdir(new)
    for file in newFiles:
        if file in existingFiles:
            if not os.path.isfile(os.path.join(new, file)):
                shutil.rmtree(os.path.join(old, file))
                shutil.copytree(os.path.join(new, file), os.path.join(old, file))  
            else:
                os.remove(os.path.join(old, file))
                shutil.copy(os.path.join(new, file), os.path.join(old, file))
        else:
            if not os.path.isfile(os.path.join(new, file)):
                shutil.copytree(os.path.join(new, file), os.path.join(old, file))  
            else:
                shutil.copy(os.path.join(new, file), os.path.join(old, file))

#Select archive to update with
packArchives = []

for file in os.listdir(os.getcwd()):
    if file.endswith('.zip'):
        packArchives.append(file)

if len(packArchives) == 0:
    print("No ZIP files found! Place the archives in the same folder with this script.")
else:
    print("----------------------------Found the following server mod versions".ljust(100, "-"))
    for i in range(packArchives.__len__()):
        print(str(i + 1) + ": " + packArchives[i])
    selection = input("Select which update to apply: ")
    validSelection = False
    try:
        selection = int(selection) - 1
        if selection < 0 or selection > packArchives.__len__() - 1:
            print("Invalid selection.")
        else:
            validSelection = True
    except:
        print("Invalid selection.")

    if validSelection:
        updateDirectory = path=os.path.join(os.getcwd(), "temp")
        if os.path.isdir(updateDirectory):
            shutil.rmtree(updateDirectory)
            pass
        with ZipFile(os.path.join(os.getcwd(), packArchives[selection])) as archive:
            print("Extracting " + packArchives[selection])
            archive.extractall(updateDirectory)
            updateMods = {}
            for mod in os.listdir(os.path.join(updateDirectory, "mods")):
                if not os.path.isfile(os.path.join(updateDirectory, "mods", mod)):
                    folder = os.listdir(os.path.join(updateDirectory, "mods", mod))
                    for modInFolder in folder:
                        if os.path.isfile(os.path.join(updateDirectory, "mods", mod, modInFolder)):
                            path, name, version =  getModName(modInFolder)
                            updateMods[name] = (os.path.join(mod, path), name, version)
                else:
                    path, name, version = getModName(mod)
                    updateMods[name] = (path, name, version)

            print("Extra mods:")
            for file in os.listdir(extraModFolder):
                print("     " + file)
                path, name, version = getModName(file)
                #Custom mod versions take priority
                if name in updateMods.keys():
                    os.remove(os.path.join(updateDirectory, "mods", updateMods[name][0]))
                    shutil.copy(os.path.join(extraModFolder, file), os.path.join(updateDirectory, "mods", file))
                else:
                    shutil.copy(os.path.join(extraModFolder, file), os.path.join(updateDirectory, "mods", file))

    print("Updating instance: " + clientDirectory)
    processed = 0
    serverModFolder =   os.listdir(os.path.join(clientDirectory, "mods"))
    existingMods = {}
    updateMods = []
    possibleNewMods = []
    missed = []
    for mod in serverModFolder:
        if not os.path.isfile(os.path.join(clientDirectory, "mods", mod)):
            folder = os.listdir(os.path.join(clientDirectory, "mods", mod))
            for modInFolder in folder:
                if os.path.isfile(os.path.join(clientDirectory, "mods", mod, modInFolder)):
                    path, name, version =  getModName(modInFolder)
                    existingMods[name] = (os.path.join(mod, path), name, version)
        else:
            path, name, version = getModName(mod)
            existingMods[name] = (path, name, version)

    for mod in os.listdir(os.path.join(updateDirectory, "mods")):
        path, name, version = getModName(mod)
        #Cache the mods
        updateMods.append(name.lower())
        #Skip identical mods
        if mod in serverModFolder:
            processed += 1
            continue
        try:
            if compareVersions(version, existingMods[name][2]):
                print(name.ljust(30) + existingMods[name][2].rjust(12) + " -> " + version)
                processed += 1
                updateMod(existingMods[name][0], path, os.path.join(updateDirectory, "mods"), os.path.join(clientDirectory, "mods"))
            else:
                #Downgrading mods?
                if existingMods[name][2] != version:
                    print(name.ljust(30) + existingMods[name][2].rjust(12) + " -> " + version.ljust(15) + " (Downgrade)")
                processed += 1
                updateMod(existingMods[name][0], path, os.path.join(updateDirectory, "mods"), os.path.join(clientDirectory, "mods"))
        except:
            possibleNewMods.append(mod.lower())
    print("----------------------------Added new mods".ljust(100, "-"))
    #Some weirdly named jars might have appeared here, final check for them
    newMods = []
    for mod in possibleNewMods:
        path, name, version =  getModName(mod)
        maxSimilarity = 0
        bestMatch = ""
        for existing in existingMods.keys():
            try:
                ratio = similarity(name.lower(), existing.lower())
                if ratio > maxSimilarity:
                    maxSimilarity = ratio
                    bestMatch = existing
            except:
                pass
        #Very high confidence that the mod is the same, update it
        if maxSimilarity > 0.95:
            processed += 1
            updateMod(existingMods[bestMatch][0], path, os.path.join(updateDirectory, "mods"), os.path.join(clientDirectory, "mods"))
        else:
            newMods.append(mod)
            

    for mod in newMods:
        path, name, version = getModName(mod)
        if mod in serverModFolder:
            processed += 1
            continue
        try:
            if compareVersions(version, existingMods[name][2]):
                print(name.ljust(30) + existingMods[name][2].rjust(12) + " -> " + version)
                processed += 1
                updateMod(existingMods[name][0], path, os.path.join(updateDirectory, "mods"), os.path.join(clientDirectory, "mods"))
            else:
                #Downgrading mods?
                print(name.ljust(30) + existingMods[name][2].rjust(12) + " -> " + version.ljust(15) + " (Downgrade)")
                processed += 1
                updateMod(existingMods[name][0], path, os.path.join(updateDirectory, "mods"), os.path.join(clientDirectory, "mods"))
        except:
            print(mod.ljust(30))
            processed += 1
            addMod(mod, os.path.join(updateDirectory, "mods"), os.path.join(clientDirectory, "mods"))

    print("----------------------------Removed mods".ljust(100, "-"))
    for mod in existingMods.keys():
        if mod.lower() not in updateMods:
            print(mod)
            try:
                removeMod(existingMods[mod][0], os.path.join(clientDirectory, "mods"))
            except:
                print("Failed to remove mod: " + existingMods[mod][0])

    print("Processed " + str(processed) + " out of " + str(len(os.listdir(os.path.join(updateDirectory, "mods")))))
    #Update scripts
    try:
        replaceFolder(os.path.join(clientDirectory, "scripts"), os.path.join(updateDirectory, "scripts"))
    except:
        print("No scripts folder found.")
    #Update configs
    try:
        replaceFolder(os.path.join(clientDirectory, "config"), os.path.join(updateDirectory, "config"))
    except:
        print("No config folder found.")
    #Apply config changes
    print("----------------------------Applying config changes".ljust(100, "-"))
    with open("permanentConfigs.txt") as f:
        lines = [line.strip() for line in f]
        currentConfig = ""
        configFile = False
        configLines = []
        for line in lines:
            if ".cfg" in  line:
                currentConfig = line
                try:
                    configFile = open(os.path.join(updateDirectory, "config/" + str(currentConfig)))
                    print("Editing " + currentConfig)
                except:
                    print("Failed opening " + currentConfig)
                continue
            elif len(line) == 0:
                if configFile:
                    configFile.close()
                    with open(os.path.join(updateDirectory, "config/" + str(currentConfig)), 'w') as editedConfig:
                        editedConfig.writelines(configLines)
                    configFile = False
                    configLines = []
                    currentConfig = ""
                continue
            #Edit the value
            if configFile:
                settingTokens = line.split("=")
                configLines = [l for l in configFile]
                for lineNumber in range(len(configLines)):
                    if settingTokens[0] in configLines[lineNumber]:
                        oldSettingTokens = configLines[lineNumber].split("=")
                        print("   |  " + oldSettingTokens[0].strip() + ": " + oldSettingTokens[1].strip().rjust(20) + " -> " + settingTokens[1].strip())
                        configLines[lineNumber] = oldSettingTokens[0] + "=" + settingTokens[1] + "\n"
            if configFile:
                configFile.close()

    #Delete the temporary directory
    shutil.rmtree(updateDirectory)