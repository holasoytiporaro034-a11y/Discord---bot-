import discord
from discord import app_commands
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("Falta la variable de entorno DISCORD_TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    logger.info(f"Bot conectado como {client.user}")

@tree.command(name="ping", description="Muestra la latencia del bot")
async def ping(interaction: discord.Interaction):
    latencia = round(client.latency * 1000)
    await interaction.response.send_message(f"Pong! Latencia: {latencia}ms")

@tree.command(name="hola", description="El bot te saluda")
async def hola(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hola, {interaction.user.display_name}!")

@tree.command(name="ayuda", description="Muestra todos los comandos disponibles")
async def ayuda(interaction: discord.Interaction):
    embed = discord.Embed(title="Comandos disponibles", color=discord.Color.blurple())
    embed.add_field(name="/ping", value="Latencia del bot", inline=False)
    embed.add_field(name="/hola", value="El bot te saluda", inline=False)
    embed.add_field(name="/ayuda", value="Este mensaje", inline=False)
    await interaction.response.send_message(embed=embed)

client.run(TOKEN, reconnect=True)
