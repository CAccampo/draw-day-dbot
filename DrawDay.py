import os

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message):
    channel = message.channel
    if message.author == client.user:
        return
    '''
    TO DO:  
            keep up with each user's streak
            only check first image of day
            cancellation with react
    '''
    for att in message.attachments:
        if att.content_type.startswith('image'):
            await message.add_reaction('✅')
            await message.reply(f'Your streak is {0}. React here with ❌ to cancel')

client.run(TOKEN)