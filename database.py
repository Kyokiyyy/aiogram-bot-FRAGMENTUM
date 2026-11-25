import sqlite3

def init_db():

    conn = sqlite3.connect("wishlist.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS wishlist (user_id INTEGER,item_code TEXT, PRIMARY KEY (user_id, item_code))")

def add_favorite(user_id, item_code):
    conn = sqlite3.connect("wishlist.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO wishlist (user_id, item_code) VALUES (?, ?)",(user_id, item_code))
    conn.commit()
    conn.close()

def remove_favorite(user_id, item_code):
    conn = sqlite3.connect("wishlist.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM wishlist WHERE user_id = ? AND item_code = ?",(user_id, item_code),)
    conn.commit()
    conn.close()

def get_favorites(user_id):
    conn = sqlite3.connect("wishlist.db")
    cursor = conn.cursor()
    cursor.execute("SELECT item_code FROM wishlist WHERE user_id = ? ORDER BY rowid",(user_id,),)
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def is_favorite(user_id, item_code):
    conn = sqlite3.connect("wishlist.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM wishlist WHERE user_id = ? AND item_code = ?",
        (user_id, item_code),
    )
    row = cursor.fetchone()
    conn.close()
    return row is not None


