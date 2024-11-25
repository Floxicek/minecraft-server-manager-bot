import discord
from discord import app_commands
from discord.ext import tasks
from dotenv import load_dotenv
import os, sleeper, crafty, platform
load_dotenv()


MY_GUILD = discord.Object(id=615248760766988311)
idle_time_to_sleep = 10 # minutes
should_sleep = False


if platform.system() == "Windows":
    should_sleep = True # Sleep only works on windows

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
    if should_sleep:
        sleeper.start_monitoring(idle_time_to_sleep)



@tasks.loop(seconds=10)
async def change_status():
    if crafty.are_any_running:
        if should_sleep:
            sleeper.stop_monitoring()
        running = crafty.get_running_info()
        if len(running) > 0:
            if len(running) > 1:
                servers = ", ".join(server["name"] for server in running)
                await client.change_presence(activity=discord.Game(f"Running {servers}"))
            else:
                running_server = running[0]
                print(running_server)
                await client.change_presence(activity=discord.Game(f"Running {running_server['name']} {running_server['online']}/{running_server['max']}"))
        else:
            await client.change_presence(status=discord.Status.online)
    else:
        if should_sleep:
            sleeper.start_monitoring(idle_time_to_sleep)
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

client.run(os.environ["DISCORD_TOKEN"])