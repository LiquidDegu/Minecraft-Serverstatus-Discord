import discord
from discord.ext import commands
from mcstatus import JavaServer
import re
import os

# Mapping Minecraft color/format codes to Discord (or plain text)
MINECRAFT_FORMATTING_CODES = {
    '0': '',  # Black
    '1': '',  # Dark Blue
    '2': '',  # Dark Green
    '3': '',  # Dark Aqua
    '4': '',  # Dark Red
    '5': '',  # Dark Purple
    '6': '',  # Gold
    '7': '',  # Gray
    '8': '',  # Dark Gray
    '9': '',  # Blue
    'a': '',  # Green
    'b': '',  # Aqua
    'c': '',  # Red
    'd': '',  # Light Purple
    'e': '',  # Yellow
    'f': '',  # White
    'k': '',  # Obfuscated (not supported, so we ignore it)
    'l': '**',  # Bold in Discord
    'm': '~~',  # Strikethrough in Discord
    'n': '__',  # Underline in Discord
    'o': '*',   # Italic in Discord
    'r': '',    # Reset (back to plain text)
}

# Function to format the MOTD by removing Minecraft formatting codes
def format_minecraft_motd(motd):
    # Regex to find all Minecraft formatting codes
    motd_cleaned = re.sub(r'§.', lambda match: MINECRAFT_FORMATTING_CODES.get(match.group()[1], ''), motd)
    return motd_cleaned

# Minecraft server check function
def check_minecraft_server_status(host, port=25565):
    """
    Checks the status of a Minecraft server, including the number of players online and the MOTD.

    Parameters:
    - host: The IP address or domain of the Minecraft server.
    - port: The port of the Minecraft server (default is 25565).

    Returns:
    - A dictionary containing the MOTD, number of players online, maximum player slots, and latency.
    """
    try:
        # Create a Minecraft server object using JavaServer
        server = JavaServer.lookup(f"{host}:{port}")
        
        # Ping the server for status info
        status = server.status()

        # Format the MOTD to remove Minecraft formatting codes
        motd_formatted = format_minecraft_motd(status.description)

        # Create a result dictionary
        result = {
            "MOTD": motd_formatted,
            "Players Online": status.players.online,
            "Max Players": status.players.max,
            "Latency": status.latency
        }

        # Try querying the server for more information if the server has query enabled
        try:
            query = server.query()
            result["Player List"] = query.players.names
        except:
            result["Player List"] = "Query not enabled"

        return result

    except Exception as e:
        return {"Error": str(e)}

# Define bot and its command prefix
intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent
bot = commands.Bot(command_prefix="!", intents=intents)

# The command that checks the Minecraft server status
@bot.command(name="mcstatus")
async def mcstatus(ctx, server_ip: str):
    """
    Command to check the status of a Minecraft server.
    
    Usage: !mcstatus <server_ip>
    Example: !mcstatus play.examplemcserver.com
    """
    result = check_minecraft_server_status(server_ip)

    if "Error" in result:
        await ctx.send(f"Could not retrieve server status: {result['Error']}")
    else:
        motd = result["MOTD"]
        players_online = result["Players Online"]
        max_players = result["Max Players"]
        latency = result["Latency"]
        player_list = result["Player List"]

        # Send the server status information as a message
        response = (
            f"**Server Status**:\n"
            f"MOTD: {motd}\n"
            f"Players Online: {players_online} / {max_players}\n"
            f"Latency: {latency} ms\n"
            f"Player List: {player_list}"
        )
        await ctx.send(response)
DISCORD_TOKEN = os.environ['discordkey']
bot.run(DISCORD_TOKEN)
