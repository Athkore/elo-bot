import os
import discord
#from discord import Client, Intents, Embed
#from discord_slash import SlashCommand, SlashContext
from discord.ext import commands
from dislash import InteractionClient,Option,OptionType
from dotenv import load_dotenv
#from elo import rate_1vs1
import sqlite3
import time

from cogs import host,report,view

load_dotenv()

TOKEN=os.getenv("DISCORD_TOKEN")

DB=os.getenv("DB")

BASE_RATING=int(os.getenv("BASE_RATING"))

K_FACTOR=int(os.getenv("K_FACTOR"))

bot = commands.Bot(command_prefix="$")

inter_client = InteractionClient(bot, test_guilds=[711158475262001153])



async def join_match(user,author):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    try:
        cur.execute("SELECT ft,region FROM hosting WHERE p1 = ?",(str(user),))
        match = cur.fetchone()
        if match is None:
            return None
        cur.execute("DELETE FROM hosting WHERE p1=?;",(str(user),))
        cur.execute("INSERT INTO matches (ft,p1,p2,region) VALUES (?,?,?,?);",(int(match[0]),str(user),str(author),str(match[1])))
        con.commit()
        con.close()
        return match[0]
    except Exception as e:
        print(e)
        print("Error joining match")
        con.close()
        return None


@inter_client.slash_command(description="Join a player for a match",options=[Option("match","Enter which player to join",OptionType.USER,required=True)])
async def join(inter,match=None):
    challenger=inter.author
    if str(challenger) == str(match):
        await inter.reply("You can't fight yourself")
    else:
        ft = await join_match(match,challenger)
        if ft is None:
            await inter.reply(f"{match} not hosting a game")
        else:
            await inter.reply(f"{challenger} joined {match} for a first to {ft} match")

#@inter_client.slash_command(description="Challenge a player to a match",options=[Option("user","Enter which player to challenge",OptionType.USER,required=True),Option("ft","Enter how many games to win",OptionType.STRING)])
#async def challenge(inter,user=None,ft=5):
#    challenger = inter.author
#    host(challenger,ft)

#@inter_client.slash_command(description="Accept an issued challenge")
#async def accept(inter):
#    accept_challenge(inter.author)



host.setup(bot,DB)
report.setup(bot,DB,BASE_RATING,K_FACTOR)
view.setup(bot,DB)

bot.run(TOKEN)
