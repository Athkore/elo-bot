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


load_dotenv()

TOKEN=os.getenv("DISCORD_TOKEN")

DB=os.getenv("DB")

BASE_RATING=int(os.getenv("BASE_RATING"))

K_FACTOR=int(os.getenv("K_FACTOR"))

bot = commands.Bot(command_prefix="$")

inter_client = InteractionClient(bot, test_guilds=[711158475262001153])


async def host(user,ft,region):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    try:
        cur.execute("SELECT * FROM hosting WHERE p1=?;",(str(user),))
        match = cur.fetchone()
        if match is None:
            cur.execute("INSERT INTO hosting (ft,p1,region) VALUES (?,?,?);",(int(ft),str(user),str(region)))
            con.commit()
            con.close()
            return 0
        else:
            return None
    except Exception as e:
        print(e)
        con.close()
        return None

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

def expected(wr,lr):
    ew = 1/(1+10**((lr-wr)/400))
    #el = 1/(1+10**((wr-lr)/400))
    return ew

def calc(ew,res,wr,lr):
    nw = round(wr + K_FACTOR * ((1-res) - (1-ew)))
    nl = round(lr + K_FACTOR * (res - ew))
    return nw,nl

async def calc_elo(w,l,res,reg):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    try:
        cur.execute("SELECT rating FROM players where name = ?",(str(w),))
        wr = cur.fetchone()
        if wr is None:
            cur.execute("INSERT INTO players (name,rating,region) VALUES (?,?,?)",(str(w),int(BASE_RATING),str(reg)))
            con.commit()
            wr = (BASE_RATING,)
        cur.execute("SELECT rating FROM players where name=?",(str(l),))
        lr = cur.fetchone()
        if lr is None:
            cur.execute("INSERT INTO players (name,rating,region) VALUES (?,?,?)",(str(l),int(BASE_RATING),str(reg)))
            con.commit()
            lr = (BASE_RATING,)
        ew = expected(wr[0],lr[0])
        nw,nl = calc(ew,res,wr[0],lr[0])
        cur.execute("UPDATE players SET rating=? WHERE name=?",(nw,w))
        cur.execute("UPDATE players SET rating=? WHERE name=?",(nl,l))
        con.commit()
        con.close()
        return 0
    except Exception as e:
        print(e)
        return 5

async def report_results(user,w,l):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    try:
        if w > l:
            cur.execute("SELECT w,l,result,reportee FROM reported WHERE w=?",(str(user),))
        else:
            cur.execute("SELECT w,l,result,reportee FROM reported WHERE l=?",(str(user),))
        report = cur.fetchone()
        cur.execute("SELECT ft,p1,p2,region FROM matches WHERE p1=? OR p2=?",(str(user),str(user)))
        match = cur.fetchone()
        if match is None:
            return (4,)
        opponent = ""
        if match[1] == str(user):
            opponent = match[2]
        else:
            opponent = match[1]
        enough = False
        ft=int(match[0])
        if ft == w:
            enough = True
        if ft == l:
            enough = True
        if enough:
            if report is None:
                if w > l:
                    res = w/(w+l)
                    cur.execute("INSERT INTO reported (w,l,region,result,reportee) VALUES (?,?,?,?,?)",(str(user),str(opponent),str(match[3]),float(res),str(user)))
                else:
                    res = l/(w+l)
                    cur.execute("INSERT INTO reported (w,l,region,result,reportee) VALUES (?,?,?,?,?)",(str(opponent),str(user),str(match[3]),float(res),str(user)))
                con.commit()
                return 0,
            else:
                if report[3] == str(user):
                    return (3,str(opponent))
                if w > l:
                    res = w/(w+l)
                else:
                    res = l/(w+l)
                if float(res) == float(report[2]):
                    e = await calc_elo(match[1],match[2],res,match[3])
                    cur.execute("DELETE FROM reported WHERE w=? OR l=?",(str(report[0]),str(report[0])))
                    cur.execute("DELETE FROM matches WHERE p1=? OR p2=?",(str(report[0]),str(report[0])))
                    con.commit()
                    con.close()
                    return e,
                else:
                    cur.execute("INSERT INTO discrepancies (p1,p2,res1,res2,region) VALUES (?,?,?,?,?)",(str(match[1]),str(match[2]),str(report[2]),str(res),str(match[3])))
                    con.commit()
                    con.close()
                    return 2,
        else:
            return 1,
    except Exception as e:
        print(e)
        con.close()
        return -1,

def get_rankings():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    try:
        #if player is not None:
        #    cur.execute(f"SELECT ROW_NUMBER () OVER ( ORDER BY rating DESC ) RowNum,rating,name,region FROM players WHERE name=?",(str(player),))
        #else:   
        cur.execute("SELECT ROW_NUMBER () OVER ( ORDER BY rating DESC ) RowNum,rating,name,region FROM players LIMIT 20")
        rank = cur.fetchall()
        return rank
    except Exception as e:
        print(e)
        return None

@inter_client.slash_command(description="Look for a ranked match",options=[Option("region","Select which region",OptionType.STRING,required=True),Option("ft","Enter how many games to win",OptionType.STRING)])
async def ranked(inter,region=None,ft=5):
    user = inter.author
    match = await host(user,ft,region)
    emb = discord.Embed(title=f"{user} looking for a first to {ft} wins ranked match in {region}.\nType /join match: {user} to join this match",)
    await inter.reply(embed=emb)

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

@inter_client.slash_command(description="View rankings",options=[Option("player","Enter which player's ranking to see",OptionType.USER)])
async def view_rankings(inter, player=None):
    rank=get_rankings()
    emb = None
    desc = ""
    if rank is not None:
        if player is None:
            for pos in rank:
                desc += f"{pos[0]}     |   {pos[1]}        |   {pos[2]}        |   {pos[3]}\n"
        else:
            for pos in rank:
                if pos[2] == str(player):
                    desc += f"{pos[0]}     |   {pos[1]}        |   {pos[2]}        |   {pos[3]}\n"
        emb = discord.Embed(title=f"Rankings",description=desc,color=discord.Color.default())
        await inter.reply(embed=emb)


@inter_client.slash_command(description="Report match results",options=[Option("result","Enter the number of your won and loss games w-l",OptionType.STRING,required=True)])
async def report(inter,result=None):
    user = inter.author
    won=result[0]
    loss=result[2]
    match = await report_results(user,int(won),int(loss))
    emb = None
    if match[0] == 0:
        emb = discord.Embed(title=f"{user} reported result {won} - {loss}",)
    elif match[0] == 1:
        emb = discord.Embed(title=f"No player won enough games",)
    elif match[0] == 2:
        emb = discord.Embed(title=f"There was a discrepancy in the reported results",)
    elif match[0] == 3:
        emb = discord.Embed(title=f"You have already reported your latest match against {match[1]}",)
    elif match[0] == 4:
        emb = discord.Embed(title=f"There is no match to report",)
    elif match[0] == 5:
        emb = discord.Embed(title=f"Error in calculating elo",)
    elif match[0] < 0:
        emb = discord.Embed(title=f"Database error",)
    await inter.reply(embed=emb)

bot.run(TOKEN)
