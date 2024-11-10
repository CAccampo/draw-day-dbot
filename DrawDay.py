import os

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('GUILD_ID')


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
guild = client.get_guild(GUILD)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    channel = message.channel
    if message.author == client.user:
        return

    # nickname = message.author.nick
    # print(nickname)
    # await message.author.edit(nick='1')
    for att in message.attachments:
        if att.content_type.startswith('image'):
            await message.add_reaction('✅')

client.run(TOKEN)