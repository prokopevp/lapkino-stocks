import sqlite3
con = sqlite3.connect("data.db")

print(con.cursor().execute("select * from user").fetchall())
con.commit()
