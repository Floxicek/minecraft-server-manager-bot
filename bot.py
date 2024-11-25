from typing import Literal, Union, NamedTuple
from enum import Enum

import discord
from discord import app_commands
from discord.ext import tasks
import os
from dotenv import load_dotenv

load_dotenv()

import crafty

MY_GUILD = discord.Object(id=1301510250209345576)

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

@tasks.loop(seconds=10)
async def change_status():
    if crafty.are_any_running:
        running = crafty.get_running_info()
        if len(running) > 0:
            if len(running) > 1:
                servers = ", ".join(server["name"] for server in running)
                await client.change_presence(activity=discord.Game(f"Running {servers}"))
            else:
                running_server = running[0]
                print(running_server)
                await client.change_presence(activity=discord.Game(f"Running {running_server["name"]} {running_server['online']}/{running_server['max']}"))
        else:
            await client.change_presence(status=discord.Status.online)
    else:
        await client.change_presence(status=discord.Status.online)

@client.tree.command()
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


client.run(os.environ["DISCORD_TOKEN"])