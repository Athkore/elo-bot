import discord
from discord.ext import commands
from dislash import slash_command,ActionRow,Button,ButtonStyle,Option,OptionType,OptionChoice
import sqlite3

class host(commands.Cog):
    def __init__(self,bot,db):
        self.bot = bot
        self.db = db

    async def host_stop(self,user):
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        try:
            cur.execute("DELETE FROM hosting WHERE p1=?",(str(user),))
            con.commit()
        except Exception as e:
            print(e)

    async def host_ranked(self,user,ft,region):
        con = sqlite3.connect(self.db)
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

    @slash_command(description="Host a game")
    async def host(self,inter):
        pass

    @host.sub_command(description="Look for a ranked match",
            options=[Option("region","Select which region",OptionType.STRING,required=True,choices=[
            OptionChoice("Europe","EU"),
            OptionChoice("North America","NA")]
            ),
            Option("ft","Enter how many games to win",OptionType.STRING)])
    
    async def ranked(self,inter,region=None,ft=5):
        user = inter.author
        match = await self.host_ranked(user,ft,region)
        emb = discord.Embed(title=f"{user} looking for a first to {ft} wins ranked match in {region}.\nType /join match: {user} to join this match",)
        await inter.reply(embed=emb)

    @host.sub_command(description="Stop looking for a match")
    async def stop(self,inter):
        user = inter.author
        await self.host_stop(user)
        await inter.reply()


def setup(bot,db):
    bot.add_cog(host(bot,db))
