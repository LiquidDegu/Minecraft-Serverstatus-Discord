import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
import re
import os
import webserver

DISCORD_TOKEN = os.environ['discordkey']


# Define bot and its command prefix
intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent
bot = commands.Bot(command_prefix="!", intents=intents)

# Global variables to store the Minecraft server IP, update interval, and custom "0 players" message
minecraft_server_ip = "play.examplemcserver.com"  # Default server IP
update_interval = 120  # Default update interval in seconds
no_players_message = "Keiner da"  # Default message when 0 players are online

# Mapping Minecraft formatting codes to Discord-compatible formats (for bold, italic, etc.)
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
    'k': '',  # Obfuscated (not supported)
    'l': '**',  # Bold in Discord
    'm': '~~',  # Strikethrough in Discord
    'n': '__',  # Underline in Discord
    'o': '*',   # Italic in Discord
    'r': '',    # Reset (remove formatting)
}

# Function to format the MOTD by removing or converting Minecraft formatting codes
def format_minecraft_motd(motd):
    # Replace Minecraft formatting codes with Discord-friendly equivalents
    formatted_motd = re.sub(r'§.', lambda match: MINECRAFT_FORMATTING_CODES.get(match.group()[1], ''), motd)
    return formatted_motd

# Function to check Minecraft server status and return the number of online players and MOTD
def get_online_players_and_motd(host, port=25565):
    """
    Checks the status of a Minecraft server to get the number of online players and the MOTD.
    
    Parameters:
    - host: The IP address or domain of the Minecraft server.
    - port: The port of the Minecraft server (default is 25565).
    
    Returns:
    - A dictionary containing the number of players online and the formatted MOTD, or an error message if the server is not reachable.
    """
    try:
        # Create a Minecraft server object using JavaServer
        server = JavaServer.lookup(f"{host}:{port}")
        
        # Get the server status and number of online players
        status = server.status()
        formatted_motd = format_minecraft_motd(status.description)  # Format the MOTD
        return {
            "players_online": status.players.online,
            "motd": formatted_motd
        }
    except Exception as e:
        return {"error": str(e)}

# Task to update the bot's status with the number of online players every few seconds (dynamically set)
@tasks.loop(seconds=update_interval)
async def update_status():
    global minecraft_server_ip  # Use the dynamically set IP address
    server_info = get_online_players_and_motd(minecraft_server_ip)
    
    if "error" in server_info:
        # If there's an error (e.g., the server is unreachable), display the error in the status
        await bot.change_presence(activity=discord.Game(f"Server error: {server_info['error']}"))
    else:
        online_players = server_info["players_online"]
        if online_players == 0:
            # If no players are online, use the custom message
            await bot.change_presence(activity=discord.Game(no_players_message))
        else:
            # If players are online, update the bot's status in German and include the MOTD
            await bot.change_presence(activity=discord.Game(f"{online_players} Spieler sind online - {server_info['motd']}"))

# Start the status update loop when the bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    update_status.start()  # Start the loop

# Command to dynamically set the Minecraft server IP
@bot.command(name="mcstatusip")
async def mcstatusip(ctx, server_ip: str):
    """
    Command to set the Minecraft server IP dynamically.
    
    Usage: !mcstatusip <server_ip>
    Example: !mcstatusip play.examplemcserver.com
    """
    global minecraft_server_ip
    minecraft_server_ip = server_ip
    await ctx.send(f"Updated Minecraft server IP to: {minecraft_server_ip}")

# Command to dynamically set the update interval in seconds
@bot.command(name="setinterval")
async def setinterval(ctx, seconds: int):
    """
    Command to set the update interval for checking the Minecraft server status in seconds.
    
    Usage: !setinterval <seconds>
    Example: !setinterval 60
    """
    global update_interval
    update_interval = seconds

    # Restart the loop with the new interval
    update_status.change_interval(seconds=update_interval)
    
    await ctx.send(f"Updated status check interval to: {update_interval} seconds.")

# Command to set the custom message for when 0 players are online
@bot.command(name="setnoplayersmsg")
async def setnoplayersmsg(ctx, message: str):
    """
    Command to set the custom message for when 0 players are online.
    
    Usage: !setnoplayersmsg <message>
    Example: !setnoplayersmsg Niemand spielt gerade
    """
    global no_players_message
    no_players_message = message
    await ctx.send(f"Updated 'no players' message to: {no_players_message}")

# Command to manually check the Minecraft server status and MOTD
@bot.command(name="mcstatus")
async def mcstatus(ctx, server_ip: str = None):
    """
    Command to check the status of a Minecraft server manually, including the MOTD.
    
    Usage: !mcstatus <server_ip>
    Example: !mcstatus play.examplemcserver.com
    """
    ip_to_check = server_ip or minecraft_server_ip  # If no IP is given, use the current IP
    server_info = get_online_players_and_motd(ip_to_check)
    
    if "error" in server_info:
        await ctx.send(f"Konnte den Serverstatus nicht abrufen: {server_info['error']}")
    else:
        await ctx.send(f"Es sind aktuell {server_info['players_online']} Spieler online auf {ip_to_check}.")
        await ctx.send(f"MOTD: {server_info['motd']}")

webserver.keep_alive()
bot.run(DISCORD_TOKEN)
