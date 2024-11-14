import os
import discord
from dotenv import load_dotenv
from datetime import datetime

import sqlite3
db = sqlite3.connect('drawday.db')

def create_tables(db):
    cur = db.cursor()
#     cur.execute('''
#   CREATE TABLE IF NOT EXISTS artists (
#       user_id integer PRIMARY KEY,
#       current_streak_id integer,
#       is_active_streak boolean NOT NULL,
#   )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS streaks (
        streak_id integer PRIMARY KEY AUTOINCREMENT,
        length_days integer NOT NULL,
        start_day text NOT NULL,
        end_day text NOT NULL,
        user_id integer NOT NULL
    )''')
    
    db.commit()

def should_start_new(msg, cur):
    #1. user has no streaks
    #2. user's last streak is broken
    return False

def should_increment(msg, cur, date_now):
    #user has submitted on a new day from previous
    cur.execute('''
                SELECT end_day
                FROM streaks
                WHERE user_id LIKE (?)
                ORDER BY end_day
                LIMIT 1''', [msg.author.id])
    for i in cur.fetchall():
        end_day = i[0]
    
    print(end_day, date_now)
    if end_day < date_now:
        return True
    return False

def insert_new_streak(msg, cur, date_now):
    cur.execute('''
        INSERT INTO streaks (length_days, start_day, end_day, user_id)
        VALUES (?, ?, ?, ?)
        ''', [1, date_now, date_now, msg.author.id]
    )
    db.commit()

def increment_streak(msg, cur, date_now):
    cur.execute('''
        UPDATE streaks
        SET length_days = length_days + 1
        WHERE user_id = (?)
        ''', [msg.author.id])
    cur.execute('''
        UPDATE streaks
        SET end_day = (?)
        WHERE user_id = (?)
        ''', [date_now, msg.author.id])
    db.commit()

async def reply_with_streak(msg, cur):
    cur.execute('''
                SELECT length_days
                FROM streaks
                WHERE user_id LIKE (?)
                ORDER BY end_day
                LIMIT 1''', [msg.author.id])
    for i in cur.fetchall():
        streak = i[0]
    await msg.reply(f'Your streak is {streak}. React here with ❌ to cancel BROKEN')



load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
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
            cur = db.cursor()
            date_now = datetime.now().strftime('%Y-%m-%d')
            insert_new_streak(msg, cur, date_now)
            await reply_with_streak(msg, cur)
            
            if should_increment(msg, cur, date_now):
                increment_streak(msg, cur, date_now)
                await msg.add_reaction('✅')
                await reply_with_streak(msg, cur)

client.run(TOKEN)