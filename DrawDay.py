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

def should_start_new(msg):
    with closing(db.cursor()) as cur:
        cur.execute('''
                    SELECT end_day
                    FROM streaks
                    WHERE user_id LIKE (?)
                    ORDER BY streak_id DESC
                    LIMIT 1''', [msg.author.id])
        fetch = cur.fetchall()
        if not fetch:
            return True #1. user has no streaks
        else:
            end_day = fetch[0][0]
            yday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
            if end_day < yday:
                return True #2. user's last streak is broken
    return False

def should_increment(msg, date_now):
    #user has submitted on a new day from previous
    with closing(db.cursor()) as cur:
        cur.execute('''
                    SELECT end_day
                    FROM streaks
                    WHERE user_id LIKE (?)
                    ORDER BY streak_id DESC
                    LIMIT 1''', [msg.author.id])
        fetch = cur.fetchall()
        if fetch:
            end_day = fetch[0][0]
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
    with closing(db.cursor()) as cur:
        cur.execute('''
                    SELECT length_days
                    FROM streaks
                    WHERE user_id LIKE (?)
                    ORDER BY streak_id DESC
                    LIMIT 1''', [msg.author.id])
        for i in cur.fetchall():
            streak = int(i[0])
    reply = ''
    if streak == 1:
        reply += 'New streak created.\n'
    await msg.reply(f'{reply}Streak: {streak}\n')
def get_end_days(msg):
    with closing(db.cursor()) as cur:
        cur.execute('''
            SELECT end_day
            FROM streaks
            WHERE user_id LIKE (?)
            ORDER BY streak_id DESC''', [msg.author.id])
        return cur.fetchall()


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.command()
async def streak(ctx):
    await reply_with_streak(ctx)
@bot.command()
async def find_break(ctx):
    fetch = get_end_days(ctx)
    today = datetime.now().strftime('%Y-%m-%d')
    end_day = ''
    if len(fetch) >= 2: #ADD check for currently broken streak
        end_day = fetch[1][0]
        await ctx.reply(f'Your Last streak was broken on {end_day}.')
    else:
        await ctx.reply(f'Break not found')

@bot.event
async def on_ready():
    create_tables(db)
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_message(msg):
    channel = msg.channel
    if msg.author == bot.user:
        return

    for att in msg.attachments:
        if att.content_type.startswith('image'):
            with freeze_time("2024-12-14"):
                date_now = datetime.now().strftime('%Y-%m-%d')
                if should_start_new(msg):
                    insert_new_streak(msg, date_now)
                    await reply_with_streak(msg)
                    await msg.add_reaction('✅')
                elif should_increment(msg, date_now):
                    increment_streak(msg, date_now)
                    await reply_with_streak(msg)
                    await msg.add_reaction('✅') 
    await bot.process_commands(msg)

bot.run(TOKEN)