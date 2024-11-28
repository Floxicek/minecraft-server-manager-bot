from time import time
import config

servers_idle_from = {}
last_run_time = time()


def update_idle_servers(running_servers):
    global last_run_time
    current_time = time()

    idle_servers = []
    for server, (idle_start_time, server_name) in list(servers_idle_from.items()):
        is_running = False
        for s in running_servers:
            if s["server_id"] == server:
                is_running = True
                break
        if not is_running:
            print(f"Server {server_name} is no longer running")
            del servers_idle_from[server]
            continue

        if server in config.SPECIAL_SERVERS:
            idle_time = config.SPECIAL_IDLE_STOP_TIME
        else:
            idle_time = config.SERVERS_IDLE_STOP_TIME
        
        if config.DEBUG_PRINT:
            print(f"Checking server {server_name} with idle time {idle_time}")
            print(f"{current_time - idle_start_time} / {idle_time}")
        if current_time - idle_start_time > idle_time:
            del servers_idle_from[server]
            print(f"Server {server_name} is idle for {idle_time} seconds, stopping")
            idle_servers.append(server)
    
    last_run_time = current_time
    return idle_servers

def update_server_idle_time(server, server_name):
    if server not in servers_idle_from:
        print(f"Server {server_name} is now idle")
        servers_idle_from[server] = (time(), server_name)

def remove_server_idle_time(server, server_name):
    if server in servers_idle_from:
        print(f"Server {server_name} is no longer idle")
        del servers_idle_from[server]