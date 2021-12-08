import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()

DB=os.getenv("DB")

"""
Tables
hosting         ft,p1,region
matches         ft,p1,p2,region
players         name,rating,region
reported        w,l,region,result,reportee
discrepancies   p1,p2,res1,res2,region
"""

con = sqlite3.connect(DB)
cur = con.cursor()
try:
    cur.execute("CREATE TABLE hosting (ft int, p1 text, region text)")
except Exception as e:
    print(e)
try:
    cur.execute("CREATE TABLE matches (ft int, p1 text, p2 text, region text)")
except Exception as e:
    print(e)
try:
    cur.execute("CREATE TABLE players (name text, rating int, region text)")
except Exception as e:
    print(e)
try:
    cur.execute("CREATE TABLE reported (w text, l text, region text, reportee text, result real)")
except Exception as e:
    print(e)
try:
    cur.execute("CREATE TABLE discrepancies (p1 text, p2 text, res1 real, res2 real, region text)")
except Exception as e:
    print(e)
con.commit()
con.close()
