import sqlite3
conn = sqlite3.connect("data/pmo_rpa.db")
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT * FROM Permissions").fetchall()
print("=== Permissions ===")
for r in rows:
    print(dict(r))
rp_rows = conn.execute("SELECT * FROM Role_Permissions").fetchall()
print("\n=== Role_Permissions ===")
for r in rp_rows:
    print(dict(r))
conn.close()
