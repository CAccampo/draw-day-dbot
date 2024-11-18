import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timedelta
from contextlib import closing

from freezegun import freeze_time

import sqlite3
db = sqlite3.connect('drawday.db')

def create_tables(db):
    with closing(db.cursor()) as cur:
        cur.execute('''
        CREATE TABLE IF NOT EXISTS streaks (
            streak_id integer PRIMARY KEY AUTOINCREMENT,
            length_days integer NOT NULL,
            start_day text NOT NULL,
            end_day text NOT NULL,
            user_id integer NOT NULL
        )''')
    db.commit()

def table_grab(msg, grab):
    with closing(db.cursor()) as cur:
        cur.execute('''
            SELECT *
            FROM streaks
            WHERE user_id LIKE (?)
            ORDER BY streak_id DESC''', [msg.author.id])
        fetch = cur.fetchall()
        select_col = []
        for streak_row in fetch:
            select_col.append(streak_row[grab])
        return select_col

def last_grab(msg, grab):
    fetch = table_grab(msg, grab)
    if fetch:
        return fetch[0]
    return None


def is_current_streak(msg):
    end_day = last_grab(msg, 3)
    yday = (datetime.now() + timedelta(1)).strftime('%Y-%m-%d')
    if end_day and end_day < yday:
        return False
    return True


def should_start_new(msg):
    fetch = table_grab(msg, 3)
    if not fetch:
        print(1)
        return True #1. user has no streaks
    else:
        print(2)
        end_day = fetch[0]
        yday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
        if end_day < yday:
            print(3)
            return True #2. user's last streak is broken
        return False

def should_increment(msg, date_now):
    #user has submitted on a new day from previous
    with closing(db.cursor()) as cur:
        fetch = table_grab(msg, 3)
        if fetch:
            end_day = fetch[0]
            if end_day:
                if end_day < date_now:
                    return True
    return False

def insert_new_streak(msg, date_now):
    with closing(db.cursor()) as cur:
        cur.execute('''
            INSERT INTO streaks (length_days, start_day, end_day, user_id)
            VALUES (?, ?, ?, ?)
            ''', [1, date_now, date_now, msg.author.id]
        )
        db.commit()

def increment_streak(msg, date_now):
    with closing(db.cursor()) as cur:
        cur.execute('''
            UPDATE streaks
            SET length_days = length_days + 1
            WHERE streak_id = (
                SELECT streak_id
                FROM streaks
                WHERE user_id = (?)
                ORDER BY streak_id DESC
	            LIMIT 1);
            ''', [msg.author.id])
        cur.execute('''
            UPDATE streaks
            SET end_day = (?)
            WHERE streak_id = (
                SELECT streak_id
                FROM streaks
                WHERE user_id = (?)
                ORDER BY streak_id DESC
	            LIMIT 1);
            ''', [date_now, msg.author.id])
        db.commit()

async def reply_with_streak(msg):
    if is_current_streak(msg):
        streak_status = f'Broken'
    else:
        streak_status = 'Ongoing'
    start_day = last_grab(msg, 2)
    end_day = last_grab(msg, 3)
    streak = last_grab(msg, 1)
    await msg.reply(f'Streak: {streak}\t {start_day} : {end_day}\nStatus: {streak_status}')


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.command()
async def streak(msg):
    #TO DO: STATE FIRST AND LAST DAY OF STREAK
    await reply_with_streak(msg)
@bot.command()
async def find_break(msg):
    fetch = table_grab(msg, 3)
    today = datetime.now().strftime('%Y-%m-%d')
    end_day = ''
    if len(fetch) >= 2: #ADD check for currently broken streak
        end_day = fetch[1]
        #TO DO: GET START DAY AND REPLY WITH LENGTH OF BREAK
        await msg.reply(f'Your last streak was broken on {end_day}.')
    else:
        await msg.reply(f'Break not found')

@bot.event
async def on_ready():
    create_tables(db)
    print(f'{bot.user} has connected to Discord!')
    print(datetime.now())

@bot.event
async def on_message(msg):
    channel = msg.channel
    if msg.author == bot.user:
        return

    for att in msg.attachments:
        if att.content_type.startswith('image'):
            date_now = datetime.now().strftime('%Y-%m-%d')
            if should_start_new(msg):
                print('new streak')
                insert_new_streak(msg, date_now)
                await reply_with_streak(msg)
                await msg.add_reaction('✅')
            elif should_increment(msg, date_now):
                print('cont streak')
                increment_streak(msg, date_now)
                await reply_with_streak(msg)
                await msg.add_reaction('✅') 
    await bot.process_commands(msg)

bot.run(TOKEN)