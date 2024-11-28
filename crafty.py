import requests
from dotenv import load_dotenv
import os
from enum import Enum
import json
import aiohttp


class ServerActions(Enum):
    start_server = "start_server"
    stop_server = "stop_server"
    restart_server = "restart_server"
    kill_server = "kill_server"
    backup_server = "backup_server"


load_dotenv()
url = "https://localhost:8443/api/v2"

token = os.environ.get("CRAFTY_TOKEN")

headers = {
    "Authorization": f"Bearer {token}"
}

def post_req(url, body=None):
    try:
        req = requests.post(url, headers=headers, json=body, verify=False)
        req.raise_for_status()  # Raise an HTTPError for bad responses
        return req
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_req(url):
    try:
        req = requests.get(url, headers=headers, verify=False)
        req.raise_for_status()  # Raise an HTTPError for bad responses
        return req
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None



def get_servers():
    response = get_req(f"{url}/servers")
    data = response.json()["data"]
    server_names = []
    for server in data:
        server_names.append({"name": server["server_name"], "server_id": server["server_id"], "port":server["server_port"]})
    return server_names
    
servers = get_servers()
are_any_running = False



def get_running_info():
    running_servers = []
    for server in servers:
        stats = get_server_stats(server["server_id"])
        # print(stats)
        if stats and stats["running"]:
            running_servers.append(stats)
    return running_servers

def server_action(server_id, action):
    global are_any_running
    if action == "start_server":
        print("Starting server")
        are_any_running = True
    elif action != "backup_server":
        are_any_running = False
    # available actions: clone_server, start_server, stop_server, restart_server, kill_server, backup_server, update_executable
    status = post_req(url=f"{url}/servers/{server_id}/action/{action}").json()
    return status["status"] == "ok"


def get_server_stats(server_id):
    response = get_req(f"{url}/servers/{server_id}/stats")
#     {
#     "status": "ok",
#     "data": {
#         "stats_id": 457,
#         "created": "2022-05-25T18:47:41.814015",
#         "server_id": {
#             "server_id": 1,
#             "created": "2022-05-25T01:24:22.427327",
#             "server_uuid": "6079f8b1-d690-4974-9c0d-792480307a86",
#             "server_name": "aaaaaaaaaaaaaaaa",
#             "path": "/home/luukas/dev/crafty-commander/servers/6079f8b1-d690-4974-9c0d-792480307a86",
#             "backup_path": "/home/luukas/dev/crafty-commander/backups/6079f8b1-d690-4974-9c0d-792480307a86",
#             "executable": "paper-1.18.2.jar",
#             "log_path": "/home/luukas/dev/crafty-commander/servers/6079f8b1-d690-4974-9c0d-792480307a86/logs/latest.log",
#             "execution_command": "java -Xms1000M -Xmx2000M -jar /home/luukas/dev/crafty-commander/servers/6079f8b1-d690-4974-9c0d-792480307a86/paper-1.18.2.jar nogui",
#             "auto_start": false,
#             "auto_start_delay": 10,
#             "crash_detection": false,
#             "stop_command": "stop",
#             "executable_update_url": "",
#             "server_ip": "127.0.0.1",
#             "server_port": 25565,
#             "logs_delete_after": 0,
#             "type": "minecraft-java"
#         },
#         "started": "2022-05-25 15:44:05",
#         "running": true,
#         "cpu": 0.33,
#         "mem": "1.6GB",
#         "mem_percent": 10.0,
#         "world_name": "aaaaaaaaaaaaaaaa",
#         "world_size": "185.4MB",
#         "server_port": 25565,
#         "int_ping_results": "True",
#         "online": 0,
#         "max": 20,
#         "players": "[]",
#         "desc": "A Minecraft Server",
#         "version": "Paper 1.18.2",
#         "updating": false,
#         "waiting_start": false,
#         "first_run": true,
#         "crashed": false,
#         "downloading": false
#     }
# }
    if response:
        data = response.json().get("data")
        # print(data)
        return {
            "name": data["server_id"]["server_name"],
            "running": data.get("running"),
            "online": data.get("online"),
            "max": data.get("max"),
            "version": data.get("version")
        }
    return None


async def config_webhook(server_id):
    async with aiohttp.ClientSession() as session:
        with open("webhooks.json", 'r') as file:
            webhooks = json.load(file)
        
        for webhook in webhooks:
            server_name = ""
            for server in servers:
                if server["server_id"] == server_id:
                    server_name = server["name"]
            
            webhook["name"] = server_name + webhook["name"]
            webhook["url"] = os.environ.get("WEBHOOK_URL")
            print(webhook)
            async with session.post(f"{url}/servers/{server_id}/webhook", headers=headers, json=webhook, ssl=False) as req:
                resp = await req.json()
                if resp["status"] == "ok":
                    print(f"Configured webhook for server {server_id}")
                else:
                    print(f"Failed to configure webhook for server {server_id}: {resp}")
        
# def get_webhooks(server_id):
#     response = get_req(f"{url}/servers/{server_id}/webhook")
#     return response.json()

async def remove_webhooks(server_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{url}/servers/{server_id}/webhook", headers=headers, ssl=False) as response:
            response_json = await response.json()
            if "data" in response_json:
                webhooks = response_json["data"]
                for webhook_id in webhooks:
                    async with session.delete(f"{url}/servers/{server_id}/webhook/{webhook_id}", headers=headers, ssl=False) as delete_response:
                        resp = await delete_response.json()
                        if resp["status"] == "ok":
                            print(f"Deleted webhook {webhook_id}")
                        else:
                            print(f"Failed to delete webhook {webhook_id}")




# print(get_webhooks(servers[1]["server_id"]))

# print(server_action(servers[1]["server_id"], "start_server"))
# print(get_req(f"{url}/servers/{servers[1]['server_id']}/stats"))
# print(get_server_stats(servers[1]["server_id"]))


# TODO https://localhost:8443/api/v2/servers/1/stdin


