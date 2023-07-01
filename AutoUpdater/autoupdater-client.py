#EDIT THIS TO MATCH YOUR INSTALLATION ex. "C:\Minecraft\Client"
directory = r"C:\Minecraft\Client Dev"













import socket
import os
import json
import time
import shutil
import re

CHUNKSIZE = 1_000_000
SERVER_PORT = 16384

soc = socket.socket()
host = "65.109.33.53"

os.chdir(directory)
try:
    shutil.rmtree("downloadedMods")
except:
    pass
os.makedirs("downloadedMods", exist_ok=True)


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

def download(connection):
        received = connection.recv(1024).decode()
        while len(received) == 0:
            received = connection.recv(1024).decode()
        filename, filesize = received.split(',')
        length = int(filesize)

        #Hacky way of closing down the connection :)
        if filename == "complete":
            return False

        path = os.path.join(directory, "downloadedMods", filename)
        with open(path,'wb') as f:
            while length:
                data = connection.recv(4096)
                if not data: break # socket closed
                f.write(data)
                length -= len(data)
        print(f'Downloading {filename}'.ljust(70), end = " ")
        if length != 0:
            print('Invalid download.')
        else:
            print('Done.')
            connection.send("ACK".encode('utf-8'))
            f.close()
            return True

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

def updateMod(old, new, sourceFolder, destinationFolder):
    os.remove(os.path.join(destinationFolder, old))
    shutil.copy(os.path.join(sourceFolder, new), os.path.join(destinationFolder, new))

mods = []

#Get the current modlist
for mod in os.listdir(os.path.join(directory, "mods")):
    mods.append(mod)
modlist = json.dumps(mods)
dataLength = len(modlist.encode('utf-8'))
try:
    soc.connect((host, SERVER_PORT))
    #Send the modlist
    with soc:
        soc.send(f"{dataLength}".encode('utf-8'))
        time.sleep(0.1)
        soc.sendall(modlist.encode('utf-8'))
        #Receive updated files until socket is closed
        receiving = True
        while receiving:
            receiving = download(soc)

        modFolder = os.listdir(os.path.join(directory, "mods"))
        receivedModFolder = os.listdir(os.path.join(directory, "downloadedMods"))
        print("Received {0} new mods!".format(len(receivedModFolder)))
        existingMods = {}
        updateMods = []
        processed = 0
        for mod in modFolder:
            path, name, version =  getModName(mod)
            existingMods[name] = (path, name, version)

        for mod in receivedModFolder:
            path, name, version = getModName(mod)
            #Cache the mods
            updateMods.append(name.lower())
            #Skip identical mods
            if mod in modFolder:
                continue
            try:
                if compareVersions(version, existingMods[name][2]):
                    print(name.ljust(30) + existingMods[name][2].rjust(12) + " -> " + version)
                    processed += 1
                    updateMod(existingMods[name][0], path, os.path.join(directory, "downloadedMods"), os.path.join(directory, "mods"))
                else:
                    #Downgrading mods?
                    print(name.ljust(30) + existingMods[name][2].rjust(12) + " -> " + version.ljust(15) + " (Downgrade)")
                    processed += 1
                    updateMod(existingMods[name][0], path, os.path.join(directory, "downloadedMods"), os.path.join(directory, "mods"))
            except:
                pass

        print("Updated {0} mods".format(processed))
        shutil.rmtree("downloadedMods")
except Exception as e:
    print("Connection to server failed, please notify Sampsa.")
    print(e)
    time.sleep(10)
    print("Starting client without updating.")