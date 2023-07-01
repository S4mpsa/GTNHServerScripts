serverDirectory = "/home/minecraft/gtnh/ballers"




import socket
import os
import re
import json

CHUNKSIZE = 1_000_000
SERVER_PORT = 16384
fluff = [".jar", ".dirty", "1.7.10", "alpha", "beta", "universal", " ", "_MC", "GTNH"]
os.chdir(serverDirectory)

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

def sameVersion(newVersion, oldVersion):
    if newVersion == oldVersion:
        return True
    else:
        return False

def startServer():
    soc = socket.socket()
    host = socket.gethostname()
    port = SERVER_PORT
    soc.bind((host, port))
    soc.listen()
    return soc

def upload(client: socket, file):
    path = os.path.join(serverDirectory, "mods", file)
    with open(path,'rb') as f:
        client.send(f"{file}{','}{os.path.getsize(path)}".encode('utf-8'))
        # Send the file in chunks so large files can be handled.
        while True:
            data = f.read(CHUNKSIZE)
            if not data: break
            client.sendall(data)
        f.close()
        return

def finishUpload(client: socket):
    client.send(f"complete{','}{1}".encode('utf-8'))
    
def receiveModlist(client):
    length = int(client.recv(1024).decode())
    modlist = b''
    while length:
        data = client.recv(4096)
        if not data: break # socket closed
        modlist += data
        length -= len(data)
    if length != 0:
        print('Modlist sending failed.')
    else:
        return json.loads(modlist)


#---------------------Server loop---------------------
server = startServer()

existingMods = {}
for mod in os.listdir(os.path.join(serverDirectory, "mods")):
    path, name, version =  getModName(mod)
    existingMods[name] = (path, name, version)

with server:
    while True:
        try:
            print("Waiting for connection")
            client, addr = server.accept()
            print("Connected to " + str(addr))
            mods = receiveModlist(client)
            mismatchedMods = []
            testModName = ""
            for mod in mods:
                path, name, version =  getModName(mod)
                testModName = name
                try:
                    if not sameVersion(path.strip(), existingMods[name][0].strip()):
                        print(name.ljust(30) + version.rjust(12) + " -> " + existingMods[name][2].ljust(12), end = " ")
                        upload(client, existingMods[name][0])
                        ack = client.recv(1024).decode()
                        while len(ack) == 0:
                            ack = client.recv(1024).decode()
                        print("Complete")
                    else:
                        pass
                except:
                    mismatchedMods.append(mod.lower())
            
            finishUpload(client)
            client.close()
        except Exception as e:
            print("A connection was accepted but had the wrong payload: ")
            print(e)
