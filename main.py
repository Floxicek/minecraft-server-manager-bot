import discord
from discord import app_commands
from discord.ext import tasks
from dotenv import load_dotenv
import config
import os, sleeper, crafty, platform
import msvcrt, threading
load_dotenv()


MY_GUILD = discord.Object(id=config.GUILD_ID)
should_sleep = platform.system() == "Windows" # Sleep only works on windows
sleep_enabled = should_sleep  # Initial state based on OS


class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

client = MyClient()


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('─' * 20)
    change_status.start()
    if should_sleep and sleep_enabled:
        sleeper.start_monitoring()
        
    running = crafty.get_running_servers()
    crafty.are_any_running = len(running) > 0


last_discord_activity = ""
@tasks.loop(seconds=10)
async def change_status():
    global sleep_enabled
    
    if crafty.are_any_running:
        if should_sleep and sleep_enabled:
            sleeper.stop_monitoring()
            activity = crafty.get_status()
            if activity != last_discord_activity:
                await client.change_presence(activity=discord.Game(activity))
        else:
            await client.change_presence(status=discord.Status.online)
    else:
        if should_sleep and sleep_enabled:
            sleeper.start_monitoring()
        await client.change_presence(status=discord.Status.online)

@client.tree.command(description="Control the minecraft server")
@app_commands.describe(server='Server to control', action='action')
@app_commands.choices(server=[
    app_commands.Choice(name=server["name"], value=server["server_id"]) for server in crafty.servers]
)
async def server(
    interaction: discord.Interaction,
    # This makes it so the first parameter can only be between 0 to 100.
    server: app_commands.Choice[str],
    action: crafty.ServerActions
):
    
    await interaction.response.send_message("Action send" if crafty.server_action(server.value, action.value) else "Failed to send action", ephemeral=True)

@client.tree.command(description="Setup notifications for the minecraft server")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(server="Which server to setup webhooks for", password="Password for the action")
@app_commands.choices(server=[
    app_commands.Choice(name=server["name"], value=server["server_id"]) for server in crafty.servers]
)
async def webhooks_setup(interaction: discord.Interaction, server: app_commands.Choice[str], password: str):
    if password != os.environ["SETUP_PASSWORD"]:
        await interaction.response.send_message("Wrong password", ephemeral=True)
        return
    await crafty.config_webhook(server.value)
    await interaction.response.send_message("Setup done", ephemeral=True)

@client.tree.command(description="Remove notifications for the minecraft server")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(server="Which server to remove webhooks from", password="Password for the action")
@app_commands.choices(server=[
    app_commands.Choice(name=server["name"], value=server["server_id"]) for server in crafty.servers]
)
async def webhooks_remove(interaction: discord.Interaction, server: app_commands.Choice[str], password: str):
    if password != os.environ["SETUP_PASSWORD"]:
        await interaction.response.send_message("Wrong password", ephemeral=True)
        return
    await crafty.remove_webhooks(server.value)
    await interaction.response.send_message("Setup done", ephemeral=True)

@app_commands.command(description="Update servers")
async def update_servers(interaction: discord.Interaction):
    crafty.update_servers()
    await interaction.response.send_message("Updating servers", ephemeral=True)

def toggle_sleep():
    global sleep_enabled
    sleep_enabled = not sleep_enabled
    print(f"Automatic sleep {'enabled' if sleep_enabled else 'disabled'}")

def listen_for_s():
    global sleep_enabled
    while True:
        key = msvcrt.getch()  # Waits for a key press (console only)
        if key.lower() == b's':  # Check if 's' key is pressed
            sleep_enabled = not sleep_enabled
            print(f"Automatic sleep {'enabled' if sleep_enabled else 'disabled'}")
        elif key.lower() == b'q':  # Check if 'q' key is pressed
            print(f"Stopping the bot")
            os._exit(0)

if should_sleep:
    threading.Thread(target=listen_for_s, daemon=True).start()


client.run(os.environ["DISCORD_TOKEN"])