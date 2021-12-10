import discord
from discord.ext import commands
from dislash import slash_command,ActionRow,Button,ButtonStyle,Option,OptionType,OptionChoice
import sqlite3

class view(commands.Cog):
    def __init__(self,bot,db):
        self.bot = bot
        self.db = db

    def get_rankings(self,region=None, limit=20):
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        try:
            if region is not None:
                if limit>0:
                    cur.execute(f"SELECT ROW_NUMBER () OVER ( ORDER BY rating DESC ) RowNum,rating,name,region,wins,losses FROM players WHERE region=? LIMIT ?",(str(region),limit))
                else:
                    cur.execute(f"SELECT ROW_NUMBER () OVER ( ORDER BY rating DESC ) RowNum,rating,name,region,wins,losses FROM players WHERE region=?",(str(region),))
            else:
                if limit>0:   
                    cur.execute("SELECT ROW_NUMBER () OVER ( ORDER BY rating DESC ) RowNum,rating,name,region,wins,losses FROM players LIMIT ?",(limit,))
                else:
                    cur.execute("SELECT ROW_NUMBER () OVER ( ORDER BY rating DESC ) RowNum,rating,name,region,wins,losses FROM players")
            rank = cur.fetchall()
            return rank
        except Exception as e:
            print(e)
            return None

    @slash_command(description="View")
    async def view(self,inter):
        pass

    @view.sub_command(description="View rankings",options=[
        Option("region","Enter which region's ranking to see",OptionType.STRING),
        Option("limit","Enter how many player's ranking to see",OptionType.INTEGER,
        choices=[
            OptionChoice("Europe","EU"),
            OptionChoice("North America","NA")]
        )])
    async def rankings(self,inter,region=None,limit=20):
        rank=self.get_rankings(region=region,limit=limit)
        emb = None
        if rank is not None:
            desc = "Rank|Rating|ID|Region|Winrate\n"
            for pos in rank:
                winrate=100*pos[4]/(pos[4]+pos[5])
                desc += f"{pos[0]}     |   {pos[1]}        |   {pos[2]}        |   {pos[3]}     |   {winrate}\n"
            emb = discord.Embed(title=f"Rankings",description=desc,color=discord.Color.default())
            await inter.reply(embed=emb)
        else:
            await inter.reply("No ranked players found")

    @view.sub_command(description="View player stats",options=[Option("user","Enter which player's ranking to see",OptionType.USER,required=True)])
    async def player(self,inter,user):
        rank=self.get_rankings(limit=-1)
        if rank is not None:
            desc = ""
            for pos in rank:
                if pos[2] == str(user):
                    winrate=100*pos[4]/(pos[4]+pos[5])
                    desc = "Rank|Rating|ID|Region|Winrate|Wins-Losses\n"
                    desc += f"{pos[0]}     |   {pos[1]}        |   {pos[2]}        |   {pos[3]}     |   {winrate}   |   {pos[4]}-{pos[5]}\n"
            if desc == "":
                await inter.reply("No player with that name found")
            else:
                emb = discord.Embed(title=f"Player statistics for {user}",description=desc,color=discord.Color.default())
                await inter.reply(embed=emb)
        else:
            await inter.reply("No ranked players found")

def setup(bot,db):
    bot.add_cog(view(bot,db))