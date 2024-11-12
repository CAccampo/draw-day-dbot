import os
import discord
from dotenv import load_dotenv
from datetime import datetime

import sqlite3

db = sqlite3.connect('drawday.db')
def create_tables(db):
    cur = db.cursor()
    cur.execute('''
CREATE TABLE IF NOT EXISTS streaks (
    streak_id integer PRIMARY KEY AUTOINCREMENT,
    length_days integer NOT NULL,
    start_day text NOT NULL,
    end_day text NOT NULL,
    user_id integer NOT NULL
    )''')
    db.commit()

def insert_new_streak(msg):
    cur = db.cursor()
    now = datetime.now()
    cur.execute('''
        INSERT INTO streaks (length_days, start_day, end_day, user_id)
        VALUES (?, ?, ?, ?)
        ''', [1, datetime.now(), datetime.now(), msg.author.id]
    )
    db.commit()


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')



intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

#@commands.Cog.listener()
async def on_ready():
    create_tables(db)
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(msg):
    channel = msg.channel
    if msg.author == client.user:
        return
    '''
    TO DO:  
            only check first image of day
            cancellation with react
    '''
    for att in msg.attachments:
        if att.content_type.startswith('image'):
            insert_new_streak(msg)
            await msg.add_reaction('✅')
            await reply_with_streak(msg)

async def reply_with_streak(msg):
    cur = db.cursor()
    cur.execute('''
                SELECT length_days
                FROM streaks
                WHERE user_id LIKE (?)
                ORDER BY end_day
                LIMIT 1''', [msg.author.id])
    for i in cur.fetchall():
        streak=i[0]
    await msg.reply(f'Your streak is {streak}. React here with ❌ to cancel')

client.run(TOKEN)