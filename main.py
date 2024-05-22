import discord
from discord.ext import commands
from datetime import datetime, timedelta
import aiosqlite
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize the database
async def init_db():
    async with aiosqlite.connect('database.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                level INTEGER NOT NULL,
                last_check_in TIMESTAMP
            )
        ''')
        await db.commit()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await init_db()

@bot.command(name='출첵')
async def check_in(ctx):
    user_id = ctx.author.id
    current_time = datetime.now()

    async with aiosqlite.connect('database.db') as db:
        cursor = await db.execute('SELECT level, last_check_in FROM users WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()

        if result:
            level, last_check_in = result
            if last_check_in:
                last_check_in_time = datetime.fromisoformat(last_check_in)
                if current_time - last_check_in_time < timedelta(days=1):
                    embed = discord.Embed(
                        title="출첵 실패",
                        description="출첵은 하루에 한 번만 가능합니다.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                    return

            # Update level and last check-in time
            new_level = level + 1
            await db.execute('UPDATE users SET level = ?, last_check_in = ? WHERE user_id = ?', (new_level, current_time.isoformat(), user_id))
        else:
            # Insert new user with initial level and check-in time
            new_level = 1
            await db.execute('INSERT INTO users (user_id, level, last_check_in) VALUES (?, ?, ?)', (user_id, new_level, current_time.isoformat()))

        await db.commit()

    embed = discord.Embed(
        title="출석 체크 완료",
        description=f"{ctx.author.mention}, 출석 체크 완료! 현재 레벨: {new_level}",
        color=discord.Color.green()
    )
    embed.set_footer(text="내일 다시 출석 체크 해주세요!")
    await ctx.send(embed=embed)

@bot.command(name='출석체크레벨')
async def check_level(ctx, member: discord.Member):
    user_id = member.id

    async with aiosqlite.connect('database.db') as db:
        cursor = await db.execute('SELECT level FROM users WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()

        if result:
            level = result[0]
            embed = discord.Embed(
                title="출석 체크 레벨",
                description=f"{member.mention}님의 현재 출석 체크 레벨은 {level}입니다.",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="출석 체크 레벨",
                description=f"{member.mention}님은 아직 출석 체크를 하지 않았습니다.",
                color=discord.Color.red()
            )

        await ctx.send()
access_token = os.environ["BOT_TOKEN"]
bot.run("access_token")
