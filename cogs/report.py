import discord
from discord.ext import commands
from dislash import slash_command,ActionRow,Button,ButtonStyle,Option,OptionType,OptionChoice
import sqlite3

class report(commands.Cog):
    def __init__(self,bot,db,base,k):
        self.bot = bot
        self.db = db
        self.base = base
        self.k = k

    def expected(self,wr,lr):
        ew = 1/(1+10**((lr-wr)/400))
        return ew

    def calc(self,ew,res,wr,lr):
        nw = round(wr + self.k * ((1-res) - (1-ew)))
        nl = round(lr + self.k * (res - ew))
        return nw,nl

    def calc_elo(self,w,l,res,reg):
        con = sqlite3.connect(DB)
        cur = con.cursor()
        try:
            cur.execute("SELECT rating,wins FROM players where name = ?",(str(w),))
            wr = cur.fetchone()
            if wr is None:
                cur.execute("INSERT INTO players (name,rating,region,wins,losses) VALUES (?,?,?,0,0)",(str(w),int(BASE_RATING),str(reg)))
                con.commit()
                wr = (self.base,0)
            cur.execute("SELECT rating,wins FROM players where name=?",(str(l),))
            lr = cur.fetchone()
            if lr is None:
                cur.execute("INSERT INTO players (name,rating,region,wins,losses) VALUES (?,?,?,0,0)",(str(l),int(BASE_RATING),str(reg)))
                con.commit()
                lr = (self.base,0)
            ew = expected(wr[0],lr[0])
            nw,nl = calc(ew,res,wr[0],lr[0])
            cur.execute("UPDATE players SET rating=?,wins=? WHERE name=?",(nw,w,wr[1]+1))
            cur.execute("UPDATE players SET rating=?,losses=? WHERE name=?",(nl,l,lr[1]+1))
            con.commit()
            con.close()
            return 0
        except Exception as e:
            print(e)
            return 5

    def report_results(self,user,w,l):
        con = sqlite3.connect(self.db)
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
                        e = self.calc_elo(match[1],match[2],res,match[3])
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

    @slash_command(description="Report")
    async def report(self, inter):
        pass

    @report.sub_command(description="Report match results",options=[Option("result","Enter the number of your won and loss games w-l",OptionType.STRING,required=True)])
    async def results(self, inter,result=None):
        user = inter.author
        won=result[0]
        loss=result[2]
        match = self.report_results(user,int(won),int(loss))
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

def setup(bot,db,base,k):
    bot.add_cog(report(bot,db,base,k))
