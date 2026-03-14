# this is the xera backend, but with no obfuscations/ hardcode
# use in python anywhere
from flask import Flask, request, jsonify, send_file
import requests, json, ipaddress, secrets, base64, time, sqlite3, random, os, string, hashlib

app = Flask(__name__)

dbthing = '/home/XeraCompany/mysite/userdata.db'
webhookurl = 'https://discord.com/api/webhooksxxxxx'
tokensthing = True

_mk_parts = [
    "RGVvYmZ1c2Nh",
    "dGVkIGJ5IHJo",
    "dG1hbjQwODA="
]
_mk_expect = "238c8302b953e4d10055544ac331f7fecab6bc7bcff7b1c35533edecc2263898"

def _mk():
    s = base64.b64decode("".join(_mk_parts)).decode()
    h = hashlib.sha256((s + "|XERA|" + str(len(s))).encode()).hexdigest()
    if h != _mk_expect:
        raise RuntimeError("x")
    return s

def initdb():
    conn = sqlite3.connect(dbthing)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        ip TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        custom_id TEXT NOT NULL,
        create_time REAL NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS banned_ips (
        ip TEXT PRIMARY KEY
    )''')
    conn.commit()
    conn.close()

initdb()

def buildjwt(uid):
    mk = _mk()
    hdr = {'alg': 'HS256', 'typ': 'JWT'}
    now = int(time.time())
    pl = {
        'tid': secrets.token_hex(16),
        'uid': uid,
        'usn': secrets.token_hex(5),
        'vrs': {
            'authID': secrets.token_hex(20),
            'clientUserAgent': 'MetaQuest 1.16.3.1138_5edcbd98',
            'deviceID': secrets.token_hex(20),
            'loginType': 'meta_quest',
            'mk': hashlib.sha256((mk + ":" + uid).encode()).hexdigest()[:18]
        },
        'exp': now + 72000,
        'iat': now
    }
    def enc(obj):
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip('=')
    sig = secrets.token_urlsafe(32) + "." + hashlib.sha256((mk + "|" + uid + "|" + str(now)).encode()).hexdigest()[:22]
    return f"{enc(hdr)}.{enc(pl)}.{sig}"

def freshtokens():
    uid = secrets.token_hex(16)
    return {'token': buildjwt(uid), 'refresh_token': buildjwt(uid)}

oldtokens = {
    'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0aWQiOiI3OGU0NDBiOS00NWZjLTRhODYtOTllMy02ZGM5Y2RjN2M1N2UiLCJ1aWQiOiJmM2E1NjE4YS1hMzNmLTQyMDAtYThiYS1lYjM3YzdiZmJmOWMiLCJ1c24iOiJ4ZW5pdHl5dCIsInZycyI6eyJhdXRoSUQiOiJkYTEzZjU4YzJiMjU0ZTgwYTM5YzA3YzRlNzkyNjlmOSIsImNsaWVudFVzZXJBZ2VudCI6Ik1ldGFRdWVzdCAxLjE2LjMuMTEzOF81ZWRjYmQ5OCIsImRldmljZUlEIjoiMTcyZjZjMmU3MWE5NGMwMTBjMWY2Mjk5OWJjM2QzMjEiLCJsb2dpblR5cGUiOiJtZXRhX3F1ZXN0In0sImV4cCI6MTc0NDA2MzQwNiwiaWF0IjoxNzQzOTk0MzE4fQ.nRJLbep6nCGeBTwruOunyNjDUiLxfcvpAJHl7E6n3m8',
    'refresh_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0aWQiOiI3OGU0NDBiOS00NWZjLTRhODYtOTllMy02ZGM5Y2RjN2M1N2UiLCJ1aWQiOiJmM2E1NjE4YS1hMzNmLTQyMDAtYThiYS1lYjM3YzdiZmJmOWMiLCJ1c24iOiJ4ZW5pdHl5dCIsInZycyI6eyJhdXRoSUQiOiJkYTEzZjU4YzJiMjU0ZTgwYTM5YzA3YzRlNzkyNjlmOSIsImNsaWVudFVzZXJBZ2VudCI6Ik1ldGFRdWVzdCAxLjE2LjMuMTEzOF81ZWRjYmQ5OCIsImRldmljZUlEIjoiMTcyZjZjMmU3MWE5NGMwMTBjMWY2Mjk5OWJjM2QzMjEiLCJsb2dpblR5cGUiOiJtZXRhX3F1ZXN0In0sImV4cCI6MTc0NDE0NjIwNiwiaWF0IjoxNzQzOTk0MzE4fQ.f7nTHNnPrJW6oYYo54RDks1iDvntTP2yiBfpHdH-ygQ'
}

def getip():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if not ip:
        return ''
    if ',' in ip:
        ip = ip.split(',')[0]
    return ip.strip()

def istrusted(ipstr):
    try:
        owners = {'OWNER IP WAS HERE', 'OWNER IP'}
        if ipstr in owners:
            return True
        ip = ipaddress.ip_address(ipstr)
        if ip.version == 4:
            return ip in ipaddress.IPv4Network('1XXXXX1.0/24') or ip in ipaddress.IPv4Network('1XXXXX8/29')
        return ip in ipaddress.IPv6Network('2600:4040:303c:5b00::/64')
    except ValueError:
        return False

def randuname():
    return 'Xera+' + ''.join(random.choices(string.ascii_uppercase, k=6))

def randcid():
    return ''.join(random.choices(string.digits, k=17))

def getuser(ip):
    conn = sqlite3.connect(dbthing)
    c = conn.cursor()
    c.execute('SELECT 1 FROM banned_ips WHERE ip = ?', (ip,))
    if c.fetchone():
        conn.close()
        return None, True
    c.execute('SELECT username, custom_id FROM users WHERE ip = ?', (ip,))
    row = c.fetchone()
    if row:
        conn.close()
        return {'username': row[0], 'custom_id': row[1]}, False
    uname = '<color=red>0x11' if ip == '127.0.0.1' else randuname()
    cid = randcid()
    c.execute('INSERT INTO users (ip, username, custom_id, create_time) VALUES (?, ?, ?, ?)',
              (ip, uname, cid, time.time()))
    conn.commit()
    conn.close()
    return {'username': uname, 'custom_id': cid}, False

def genloadout():
    try:
        with open('/home/XeraCompany/mysite/econ_gameplay_items.json', 'r') as f:
            data = json.load(f)
        ids = [item['id'] for item in data if 'id' in item]
    except Exception as e:
        print(f"Failed to load econ_gameplay_items.json: {e}")
        ids = [
            'item_jetpack', 'item_flaregun', 'item_dynamite', 'item_tablet',
            'item_flashlight_mega', 'item_plunger', 'item_crossbow',
            'item_revolver', 'item_shotgun', 'item_pickaxe'
        ]
    kids = []
    for _ in range(20):
        if random.random() < 0.7 and 'item_arena_pistol' in ids:
            pick = 'item_arena_pistol'
        else:
            pick = random.choice(ids)
        kids.append({
            'itemID': pick,
            'scaleModifier': 100,
            'colorHue': random.randint(10, 111),
            'colorSaturation': random.randint(10, 111)
        })
    val = {
        'version': 1,
        'back': {
            'itemID': 'item_backpack_large_base',
            'scaleModifier': 120,
            'colorHue': 50,
            'colorSaturation': 50,
            'children': kids
        }
    }
    return {'objects': [{'collection': 'user_inventory', 'key': 'gameplay_loadout',
                         'permission_read': 1, 'permission_write': 1, 'value': json.dumps(val)}]}

bootresp = {'payload': '{"updateType":"Optional","attestResult":"Valid","attestTokenExpiresAt":1820877961,"photonAppID":"xxxxxx","photonVoiceAppID":"xxxxxx","termsAcceptanceNeeded":[],"dailyMissionDateKey":"","dailyMissions":null,"dailyMissionResetTime":0,"serverTimeUnix":1720877961,"gameDataURL":"https://xeracompany.pythonanywhere.com/game-data-prod.zip}'}

econitems = {'payload': '[{"id":"item_apple","netID":71,"name":"Apple","description":"An apple a day keeps the doctor away!","category":"Consumables","price":200,"value":7,"isLoot":true,"isPurchasable":false,"isUnique":false,"isDevOnly":false},{"id":"item_arrow","netID":103,"name":"Arrow","description":"Can be attached to the crossbow.","category":"Ammo","price":199,"value":8,"isLoot":false,"isPurchasable":true,"isUnique":false,"isDevOnly":false},{"id":"item_arrow_heart","netID":116,"name":"Heart Arrow","description":"A love-themed arrow that will have your targets seeing hearts! ","category":"Ammo","price":199,"value":8,"isLoot":false,"isPurchasable":true,"isUnique":false,"isDevOnly":false} ... ]'}

sumaccountig = {
    'user': {
        'id': '2e8aace0-282d-4c3d-b9d4-6a3b3ba2c2a6',
        'username': 'ERROR',
        'lang_tag': 'en',
        'metadata': '{}',
        'edge_count': 4,
        'create_time': '2024-08-24T07:30:12Z',
        'update_time': '2025-04-05T21:00:27Z'
    },
    'wallet': '{"stashCols": 4, "stashRows": 2, "hardCurrency": 30000000, "softCurrency": 20000000, "researchPoints": 500000}',
    'custom_id': '26344644298513663'
}

storedobj = {'objects': [
    {'collection': 'user_avatar', 'key': '0', 'user_id': '2e8aace0-282d-4c3d-b9d4-6a3b3ba2c2a6', 'value': '{"butt": "bp_butt_gorilla", "head": "bp_head_gorilla", "tail": "", "torso": "bp_torso_gorilla", "armLeft": "bp_arm_l_gorilla", "eyeLeft": "bp_eye_gorilla", "armRight": "bp_arm_r_gorilla", "eyeRight": "bp_eye_gorilla", "accessories": ["acc_fit_varsityjacket"], "primaryColor": "604170"}', 'version': '7a326a2a4d0639a5f08e3116bb99a3bf', 'permission_read': 2, 'create_time': '2024-10-29T00:22:08Z', 'update_time': '2025-04-04T03:55:19Z'},
    {'collection': 'user_inventory', 'key': 'avatar', 'user_id': '2e8aace0-282d-4c3d-b9d4-6a3b3ba2c2a6', 'value': '{"items": ["animal_gorilla", "bp_head_gorilla", "bp_eye_gorilla", "bp_torso_gorilla", "bp_arm_l_gorilla", "bp_arm_r_gorilla", "bp_butt_gorilla", "acc_fit_varsityjacket_black", "acc_fit_varsityjacket", "outfit_cube", "acc_fit_cubes", "acc_fit_head_cube", "animal_skeletongorilla"]}', 'version': 'b6a38347a29ec461a06d5e30ed8b3cd8', 'permission_read': 1, 'create_time': '2024-10-29T00:22:08Z', 'update_time': '2025-04-05T06:21:14Z'},
    {'collection': 'user_inventory', 'key': 'research', 'user_id': '2e8aace0-282d-4c3d-b9d4-6a3b3ba2c2a6', 'value': '{"nodes": ["node_arrow", "node_arrow_heart", "node_arrow_lightbulb", "node_backpack", "node_backpack_large", "node_backpack_large_basketball", "node_backpack_large_clover", "node_balloon", "node_balloon_heart", "node_baseball_bat", "node_boxfan", "node_clapper", "node_cluster_grenade", "node_company_ration", "node_crossbow", "node_crossbow_heart", "node_crowbar", "node_disposable_camera", "node_dynamite", "node_dynamite_cube", "node_flaregun", "node_flashbang", "node_flashlight_mega", "node_football", "node_frying_pan", "node_glowsticks", "node_heart_gun", "node_hookshot", "node_hoverpad", "node_impact_grenade", "node_impulse_grenade", "node_item_nut_shredder", "node_jetpack", "node_lance", "node_mega_broccoli", "node_mini_broccoli", "node_ogre_hands", "node_pickaxe", "node_pickaxe_cny", "node_pickaxe_cube", "node_plunger", "node_pogostick", "node_police_baton", "node_quiver", "node_quiver_heart", "node_revolver", "node_revolver_ammo", "node_rpg", "node_rpg_ammo", "node_rpg_cny", "node_saddle", "node_shield", "node_shield_bones", "node_shield_police", "node_shotgun", "node_shotgun_ammo", "node_skill_backpack_cap_1", "node_skill_backpack_cap_2", "node_skill_backpack_cap_3", "node_skill_explosive_1", "node_skill_gundamage_1", "node_skill_health_1", "node_skill_health_2", "node_skill_left_hip_attachment", "node_skill_melee_1", "node_skill_melee_2", "node_skill_melee_3", "node_skill_right_hip_attachment", "node_skill_selling_1", "node_skill_selling_2", "node_skill_selling_3", "node_stick_armbones", "node_stick_bone", "node_sticker_dispenser", "node_sticky_dynamite", "node_tablet", "node_teleport_grenade", "node_theramin", "node_tripwire_explosive", "node_umbrella", "node_umbrella_clover", "node_whoopie", "node_zipline_gun", "node_zipline_rope"]}', 'version': 'bb49186ef5806541f461f4c9f3f4f871', 'permission_read': 1, 'create_time': '2025-02-20T00:51:38Z', 'update_time': '2025-02-20T01:15:06Z'},
    {'collection': 'user_inventory', 'key': 'stash', 'user_id': '2e8aace0-282d-4c3d-b9d4-6a3b3ba2c2a6', 'value': '{"items": [{"itemID": "item_backpack_large_base", "colorHue": 202, "colorSaturation": 93, "scaleModifier": -91, "children": [{"itemID": "item_heart_gun", "colorHue": 142, "colorSaturation": -94, "scaleModifier": 108, "children": [{"itemID": "item_backpack_large_base", "colorHue": 122, "colorSaturation": 48, "scaleModifier": 111, "children": [{"itemID": "item_heart_gun", "colorHue": 236, "colorSaturation": -110, "scaleModifier": -110, "children": [{"itemID": "item_arena_pistol", "colorHue": 157, "colorSaturation": 10, "scaleModifier": -100}]}, {"itemID": "item_heart_gun", "colorHue": 179, "colorSaturation": 68, "scaleModifier": 66, "children": [{"itemID": "item_arena_pistol", "colorHue": 71, "colorSaturation": -69, "scaleModifier": -71}]}, {"itemID": "item_heart_gun", "colorHue": 111, "colorSaturation": -105, "scaleModifier": 21, "children": [{"itemID": "item_arena_pistol", "colorHue": 99, "colorSaturation": -46, "scaleModifier": -89}]}, {"itemID": "item_heart_gun", "colorHue": 213, "colorSaturation": 2, "scaleModifier": -120, "children": [{"itemID": "item_arena_pistol", "colorHue": 87, "colorSaturation": -23, "scaleModifier": -65}]}, {"itemID": "item_heart_gun", "colorHue": 86, "colorSaturation": -59, "scaleModifier": -27, "children": [{"itemID": "item_arena_pistol", "colorHue": 41, "colorSaturation": -99, "scaleModifier": -88}]}, {"itemID": "item_heart_gun", "colorHue": 224, "colorSaturation": 107, "scaleModifier": 4, "children": [{"itemID": "item_arena_pistol", "colorHue": 78, "colorSaturation": -39, "scaleModifier": 103}]}, {"itemID": "item_heart_gun", "colorHue": 129, "colorSaturation": -16, "scaleModifier": 103, "children": [{"itemID": "item_arena_pistol", "colorHue": 76, "colorSaturation": 77, "scaleModifier": 59}]}, {"itemID": "item_heart_gun", "colorHue": 168, "colorSaturation": 7, "scaleModifier": -74, "children": [{"itemID": "item_arena_pistol", "colorHue": 109, "colorSaturation": 42, "scaleModifier": 93}]}, {"itemID": "item_heart_gun", "colorHue": 21, "colorSaturation": 50, "scaleModifier": 17, "children": [{"itemID": "item_arena_pistol", "colorHue": 126, "colorSaturation": -23, "scaleModifier": -35}]}, {"itemID": "item_heart_gun", "colorHue": 81, "colorSaturation": -37, "scaleModifier": -88, "children": [{"itemID": "item_arena_pistol", "colorHue": 150, "colorSaturation": 117, "scaleModifier": 44}]}, {"itemID": "item_heart_gun", "colorHue": 143, "colorSaturation": 4, "scaleModifier": -106, "children": [{"itemID": "item_arena_pistol", "colorHue": 195, "colorSaturation": 26, "scaleModifier": -75}]}, {"itemID": "item_heart_gun", "colorHue": 152, "colorSaturation": 9, "scaleModifier": -41, "children": [{"itemID": "item_arena_pistol", "colorHue": 193, "colorSaturation": -46, "scaleModifier": 66}]}, {"itemID": "item_heart_gun", "colorHue": 236, "colorSaturation": -55, "scaleModifier": -19, "children": [{"itemID": "item_arena_pistol", "colorHue": 57, "colorSaturation": 85, "scaleModifier": -108}]}, {"itemID": "item_heart_gun", "colorHue": 102, "colorSaturation": -68, "scaleModifier": 113, "children": [{"itemID": "item_arena_pistol", "colorHue": 53, "colorSaturation": 4, "scaleModifier": -109}]}, {"itemID": "item_heart_gun", "colorHue": 61, "colorSaturation": 3, "scaleModifier": 115, "children": [{"itemID": "item_arena_pistol", "colorHue": 193, "colorSaturation": 118, "scaleModifier": 31}]}, {"itemID": "item_heart_gun", "colorHue": 185, "colorSaturation": 88, "scaleModifier": -25, "children": [{"itemID": "item_arena_pistol", "colorHue": 101, "colorSaturation": 2, "scaleModifier": -50}]}, {"itemID": "item_heart_gun", "colorHue": 23, "colorSaturation": 53, "scaleModifier": 84, "children": [{"itemID": "item_arena_pistol", "colorHue": 47, "colorSaturation": -55, "scaleModifier": -98}]}, {"itemID": "item_heart_gun", "colorHue": 35, "colorSaturation": 86, "scaleModifier": -28, "children": [{"itemID": "item_arena_pistol", "colorHue": 173, "colorSaturation": 1, "scaleModifier": 83}]}, {"itemID": "item_heart_gun", "colorHue": 20, "colorSaturation": 96, "scaleModifier": -49, "children": [{"itemID": "item_arena_pistol", "colorHue": 42, "colorSaturation": -93, "scaleModifier": -113}]}, {"itemID": "item_heart_gun", "colorHue": 56, "colorSaturation": 35, "scaleModifier": -14, "children": [{"itemID": "item_arena_pistol", "colorHue": 137, "colorSaturation": 102, "scaleModifier": -56}]}, {"itemID": "item_heart_gun", "colorHue": 203, "colorSaturation": -38, "scaleModifier": -7, "children": [{"itemID": "item_arena_pistol", "colorHue": 65, "colorSaturation": 49, "scaleModifier": 105}]}, {"itemID": "item_heart_gun", "colorHue": 130, "colorSaturation": 11, "scaleModifier": 35, "children": [{"itemID": "item_arena_pistol", "colorHue": 71, "colorSaturation": 97, "scaleModifier": 53}]}, {"itemID": "item_heart_gun", "colorHue": 2, "colorSaturation": 68, "scaleModifier": 119, "children": [{"itemID": "item_arena_pistol", "colorHue": 41, "colorSaturation": 50, "scaleModifier": -13}]}]}]}], "stashPos": 0}], "version": 1}', 'version': '8e192e752405b279447f0523a9049fdd', 'permission_read': 1, 'permission_write': 1, 'create_time': '2025-02-20T00:51:38Z', 'update_time': '2025-04-05T10:03:13Z'},
    {'collection': 'user_inventory', 'key': 'gameplay_loadout', 'user_id': '2e8aace0-282d-4c3d-b9d4-6a3b3ba2c2a6', 'value': '{"version": 1}', 'version': '77efb8e3fa276d4674932392a66555e4', 'permission_read': 1, 'permission_write': 1, 'create_time': '2025-02-20T00:51:50Z', 'update_time': '2025-04-05T21:06:17Z'},
    {'collection': 'user_preferences', 'key': 'gameplay_items', 'user_id': '2e8aace0-282d-4c3d-b9d4-6a3b3ba2c2a6', 'value': '{"recents": ["item_backpack_small_base", "item_flaregun", "item_tele_grenade", "item_glowstick", "item_jetpack", "item_stick_bone", "item_dynamite_cube", "item_tablet", "item_plunger", "item_flashlight_mega"], "favorites": ["item_flaregun"]}', 'version': '80aae98f75aab68ca6540247a17cc4a1', 'permission_read': 1, 'permission_write': 1, 'create_time': '2025-02-20T00:52:27Z', 'update_time': '2025-04-05T21:04:05Z'}
]}

allmethods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']

@app.after_request
def logreq(response):
    mk = _mk()
    body = request.get_data(as_text=True)
    qp = dict(request.args)
    msg = {
        'content': f"📡 **Request to: {request.path} - {mk}**",
        'embeds': [{
            'title': f"Request Details - {mk}",
            'fields': [
                {'name': 'Method', 'value': request.method, 'inline': True},
                {'name': 'Path', 'value': request.path, 'inline': True},
                {'name': 'Status Code', 'value': str(response.status_code), 'inline': True},
                {'name': 'Full URL', 'value': request.url, 'inline': False},
                {'name': 'Query Params', 'value': f"```json\n{json.dumps(qp, indent=2)}```" if qp else '*(none)*', 'inline': False},
                {'name': 'Headers', 'value': f"```json\n{json.dumps(dict(request.headers), indent=2)}```", 'inline': False},
                {'name': 'Body', 'value': f"```json\n{body}```" if body else '*(empty)*', 'inline': False},
            ],
            'color': 65280 if response.status_code < 400 else 16711680,
            'footer': {'text': mk}
        }]
    }
    try:
        requests.post(webhookurl, json=msg)
    except Exception:
        pass
    return response

@app.route('/v2/account/authenticate/custom', methods=allmethods)
def doauth():
    genloadout()
    return jsonify(freshtokens() if tokensthing else oldtokens)

@app.route('/v2/account1', methods=allmethods)
def acct1():
    return jsonify(sumaccountig)

@app.route('/v2/rpc/purchase.avatarItems', methods=['POST'])
def buyavatar():
    mk = _mk()
    return jsonify({'payload': '', 'debug': mk})

@app.route('/v2/rpc/avatar.update', methods=['POST'])
def updateavatar():
    mk = _mk()
    return jsonify({'payload': '', 'debug': mk})

@app.route('/v2/rpc/purchase.gameplayItems', methods=['POST'])
def buygameplay():
    mk = _mk()
    return jsonify({'payload': '', 'debug': mk})

@app.route('/game-data-prod.zip')
def servegamedata():
    mk = _mk()
    ip = request.remote_addr
    print(f"Request from IP: {ip} - {mk}")
    fpath = os.path.join('/home/XeraCompany/mysite', 'Zombie.zip')
    if not os.path.exists(fpath):
        print(f"File not found: {fpath}")
        return 'File not found', 404
    print(f"Serving Zombie.zip, size: {os.path.getsize(fpath)} bytes - {mk}")
    try:
        return send_file(fpath, mimetype='application/zip', as_attachment=False, download_name='Zombie.zip', max_age=3600)
    except Exception as e:
        print(f"Error serving file: {e}")
        return f"Error: {str(e)}", 500

@app.route('/v2/account', methods=['GET', 'PUT'])
def acct():
    mk = _mk()
    if request.method == 'PUT':
        res = jsonify({})
        res.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        res.headers['Content-Type'] = 'application/json'
        res.headers['Grpc-Metadata-Content-Type'] = 'application/grpc'
        res.headers['X-Deobfuscated-By'] = 'ratman4080'
        res.headers['X-Marker'] = hashlib.sha256((mk + "|hdr").encode()).hexdigest()[:24]
        return res
    ip = getip()
    user, banned = getuser(ip)
    if banned or user is None:
        print(f"[ERROR] banned or db fail - IP: {ip} - {mk}")
        return jsonify(sumaccountig)
    uname = 'ALEX [HELPER]' if istrusted(ip) else 'XERA COMPANY'
    return jsonify({
        'user': {
            'id': '2e8aace0-282d-4c3d-b9d4-6a3b3ba2c2a6',
            'username': uname,
            'lang_tag': 'en',
            'metadata': json.dumps({'isDeveloper': str(istrusted(ip)), 'deobfuscatedBy': 'ratman4080', 'mk': hashlib.sha256((mk + "|meta").encode()).hexdigest()[:18]}),
            'edge_count': 4,
            'create_time': '2024-08-24T07:30:12Z',
            'update_time': '2025-04-05T21:00:27Z'
        },
        'wallet': '{"stashCols": 16, "stashRows": 8, "hardCurrency": 0, "softCurrency": 20000000, "researchPoints": 69420}',
        'custom_id': user['custom_id']
    })

@app.route('/v2/account/alt2', methods=allmethods)
def acctalt():
    return jsonify(storedobj)

@app.route('/v2/account/link/device', methods=['POST'])
def linkdev():
    mk = _mk()
    return jsonify({
        'id': secrets.token_hex(16),
        'user_id': '13b8dce4-2c8e-4945-90b6-19af0c2b0ad7',
        'linked': True,
        'create_time': '2025-01-15T18:08:45Z',
        'note': mk
    })

@app.route('/v2/account/session/refresh', methods=allmethods)
def refreshsesh():
    return jsonify(freshtokens() if tokensthing else oldtokens)

@app.route('/v2/rpc/attest.start', methods=['POST'])
def atteststart():
    mk = _mk()
    return jsonify({'payload': json.dumps({'status': 'success', 'attestResult': 'Valid', 'message': f"Attestation validated - {mk}"})})

@app.route('/v2/storage', methods=allmethods)
def dostorage():
    if request.method == 'POST':
        try:
            data = request.get_json(force=True)
            if data and 'object_ids' in data:
                uid = data['object_ids'][0].get('user_id') if data['object_ids'] else None
                if not uid:
                    return jsonify({'objects': []})
                loadout = genloadout()
                objs = []
                for obj in storedobj['objects']:
                    o = obj.copy()
                    o['user_id'] = uid
                    if obj.get('key') == 'gameplay_loadout':
                        o['value'] = loadout['objects'][0]['value']
                    objs.append(o)
                return jsonify({'objects': objs})
            return jsonify({'objects': []})
        except Exception as e:
            mk = _mk()
            print(f"Storage error: {e} - {mk}")
            return jsonify({'objects': []})
    return jsonify(storedobj)

@app.route('/v2/storage/econ_gameplay_items', methods=allmethods)
def geteconomy():
    return jsonify(econitems)

@app.route('/v2/rpc/mining.balance', methods=['GET'])
def miningbal():
    mk = _mk()
    return jsonify({'payload': json.dumps({'hardCurrency': 20000000, 'researchPoints': 999999, 'deobfuscatedBy': 'ratman4080', 'mk': hashlib.sha256((mk + "|bal").encode()).hexdigest()[:18]})}), 200

@app.route('/v2/rpc/purchase.list', methods=['GET'])
def purchaselist():
    mk = _mk()
    data = {'purchases': [
        {
            'user_id': '13b8dce4-2c8e-4945-90b6-19af0c2b0ad7',
            'product_id': 'RESEARCH_PACK',
            'transaction_id': '540282689176766',
            'store': 3,
            'purchase_time': {'seconds': 1741450711},
            'create_time': {'seconds': 1741450837, 'nanos': 694669000},
            'update_time': {'seconds': 1741450837, 'nanos': 694669000},
            'refund_time': {},
            'provider_response': json.dumps({'success': True}),
            'environment': 2
        },
        {
            'user_id': '13b8dce4-2c8e-4945-90b6-19af0c2b0ad7',
            'product_id': 'G.O.A.T_BUNDLE',
            'transaction_id': '540281232510245',
            'store': 3,
            'purchase_time': {'seconds': 1741450591},
            'create_time': {'seconds': 1741450722, 'nanos': 851245000},
            'update_time': {'seconds': 1741450722, 'nanos': 851245000},
            'refund_time': {},
            'provider_response': json.dumps({'success': True}),
            'environment': 2
        }
    ], 'deobfuscatedBy': 'ratman4080', 'mk': hashlib.sha256((mk + "|p").encode()).hexdigest()[:18]}
    return jsonify({'payload': json.dumps(data)}), 200

@app.route('/v2/rpc/clientBootstrap', methods=allmethods)
def bootstrap():
    return jsonify(bootresp)

@app.route('/auth', methods=['GET', 'POST'])
def photonauth():
    mk = _mk()
    tok = request.args.get('auth_token')
    print(f"🔐 Photon Auth Request Received - {mk}")
    if tok:
        print(f"auth_token: {tok}")
        msg = 'Authentication successful'
    else:
        print('⚠️ No auth_token provided')
        msg = 'Authenticated without token'
    return jsonify({
        'ResultCode': 1,
        'Message': msg,
        'UserId': secrets.token_hex(16),
        'SessionID': secrets.token_hex(12),
        'Authenticated': True,
        'note': mk
    }), 200

@app.route('/debug', methods=allmethods)
def debugroute():
    mk = _mk()
    body = request.get_data(as_text=True)
    msg = {
        'content': '📡 **/debug request received**',
        'embeds': [{
            'title': f"Request Info - {mk}",
            'fields': [
                {'name': 'Method', 'value': request.method, 'inline': True},
                {'name': 'URL', 'value': request.url, 'inline': False},
                {'name': 'Headers', 'value': f"```json\n{json.dumps(dict(request.headers), indent=2)}```", 'inline': False},
                {'name': 'Body', 'value': f"```json\n{body}```" if body else '*(empty)*', 'inline': False},
            ],
            'color': 65484,
            'footer': {'text': mk}
        }]
    }
    try:
        requests.post(webhookurl, json=msg)
    except Exception as e:
        return f"Failed to send to Discord: {e}", 500
    return f"Sent debug to discord - {mk}", 200

if __name__ == '__main__':
    _mk()
    app.run(debug=False)
