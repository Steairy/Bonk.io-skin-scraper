import requests
import json, math, time
from websockets.sync.client import connect
import ssl
import hashlib
import urllib3
import datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

username = 'skinbot'

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://bonk.io/",
    "X-Requested-With": "XMLHttpRequest",
    "Cookie": "SESSIONID=abcd1234; othercookie=value",
}


alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
def yeast():
    num = math.floor(time.time()*1000)
    encoded = ""
    while num > 0 or encoded == "":
        encoded = alphabet[num % len(alphabet)] + encoded
        num = math.floor(num / len(alphabet))
    return encoded

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def getData(room): # enter a room and get the output
    global currentProxy
    try:
        sid = requests.get(f"https://{room['server']}.bonk.io/socket.io/?EIO=3&transport=polling&t={yeast}", verify=False, headers=headers).text.split('"')[3]
        with connect(f"wss://{room['server']}.bonk.io/socket.io/?EIO=3&transport=websocket&sid={sid}", ssl=ssl_context) as websocket:
            websocket.send("2probe")
            websocket.recv()
            websocket.send("5")
            websocket.recv()
            websocket.send('42[13,{"joinID":"{address}","roomPassword":"","guest":true,"dbid":2,"version":` + version + `,"peerID":"` + self.peerid + `","bypass":"","guestName":"` + self.username + `","avatar":{"layers":[],"bc":14737632}}]'.replace("{address}", room["address"]).replace("` + version + `", "49").replace("` + self.peerid + `", "peer123").replace("` + self.username + `", username))
            return websocket.recv()
    except Exception as e:
        print(f"New Exception at getData: {e}")
        return "42[16]"


def saveToDatalake(data): # give data as single line
    with open("datalake.jsonl", "a") as f:
        f.write(json.dumps(data) + "\n")


seen = set()
with open("datalake.jsonl", "a+") as f: #get all the previous info from datalake
    for line in f.readlines():
        l = json.loads(line)
        seen.add(hashlib.blake2b(json.dumps(l["avatar"], sort_keys=True).encode(), digest_size=16).hexdigest())

entered = 0
while True:
    try:
        p = requests.post("https://bonk2.io/scripts/getrooms.php", data={"version":"49", "gl":"n","token":""}, headers=headers)
        rooms = json.loads(p.text)["rooms"]

        for roomRaw in rooms:
            if(roomRaw["password"] == 1 or roomRaw["minlevel"] > 0):
                continue

            address = requests.post("https://bonk2.io/scripts/getroomaddress.php", data={"id":roomRaw["id"]}, headers=headers)
            room = json.loads(address.text)
            entered += 1
            print(f"Entered room count: {entered}")

            if(room == {'r': 'fail', 'e': 'ratelimited'}):
                wait_seconds = math.ceil(((datetime.datetime.now().replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)) - datetime.datetime.now()).total_seconds())
                print(f'Ratelimited for {wait_seconds} seconds')
                time.sleep(wait_seconds+20)
                continue
            
            data = json.loads(getData(room).removeprefix("42"))
            if(data[0] == 16):
                continue

            playerList = data[3]
            for player in playerList:
                if type(player) == dict:
                    if not player["guest"]:
                        hash = hashlib.blake2b(json.dumps(player["avatar"], sort_keys=True).encode(), digest_size=16).hexdigest()
                        if(hash not in seen):
                            seen.add(hash)
                            finalData = {"name":player["userName"], "avatar":player["avatar"]}
                            saveToDatalake(finalData)
        time.sleep(900)
    except Exception as e:
        print("New Exception at main loop:", e)
        time.sleep(30)
