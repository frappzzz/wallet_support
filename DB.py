import sqlite3

statuses = ['awaiting response', 'response received']

class DB():
    def __init__(self):
        self.con = sqlite3.connect('DataBases/DB.db', check_same_thread=False)
        self.cur = self.con.cursor()

    def __del__(self):
        self.con.close()

    def createUserMessagesTable(self):
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS UserMessages (id_user_message INTEGER PRIMARY KEY autoincrement, id_user_web INTEGER, id_user_tg INTEGER, user_message TEXT, user_message_number INTEGER, status TEXT);")
        self.con.commit()

    def addMessage(self, id_user_web, id_user_tg, user_message, user_message_number):
        self.cur.execute(
            "INSERT INTO UserMessages (id_user_web, id_user_tg, user_message, user_message_number, status) VALUES (?, ?, ?, ?, ?);",
            (id_user_web, id_user_tg, user_message, user_message_number, 'awaiting response'))
        self.con.commit()

    def get_all_messages(self):
        self.cur.execute("SELECT * FROM UserMessages ORDER BY id_user_message")
        return self.cur.fetchall()

    def get_new_messages(self, last_id):
        self.cur.execute("""
            SELECT * FROM UserMessages 
            WHERE id_user_message > ? 
            ORDER BY id_user_message
        """, (last_id,))
        return self.cur.fetchall()

    def createBotMessagesTable(self):
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS BotMessages (id_bot_message INTEGER PRIMARY KEY autoincrement, id_user_tg INTEGER, bot_message TEXT, bot_message_number INTEGER, status TEXT);")
        self.con.commit()

    def addBotMessage(self, id_user_tg, bot_message, bot_message_number):
        self.cur.execute(
            "INSERT INTO BotMessages (id_user_tg, bot_message, bot_message_number, status) VALUES (?, ?, ?, ?);",
            (id_user_tg, bot_message, bot_message_number, 'response'))
        self.con.commit()

    def get_messages_by_user(self, id_user_tg):
        self.cur.execute("""
            SELECT id_user_message, id_user_web, id_user_tg, user_message, user_message_number, status 
            FROM UserMessages 
            WHERE id_user_tg = ?
            ORDER BY user_message_number
        """, (id_user_tg,))
        user_messages = self.cur.fetchall()
        return user_messages

    # В методе get_messages_by_bot исправляем сортировку
    def get_messages_by_bot(self, id_user_tg):
        self.cur.execute("""
            SELECT id_bot_message, id_user_tg, bot_message, bot_message_number, status 
            FROM BotMessages 
            WHERE id_user_tg = ?
            ORDER BY bot_message_number
        """, (id_user_tg,))
        bot_messages = self.cur.fetchall()
        return bot_messages
    def get_last_user_message_number(self, id_user_tg):
        self.cur.execute("""
            SELECT user_message_number FROM UserMessages 
            WHERE id_user_tg = ?
            ORDER BY user_message_number DESC
            LIMIT 1
        """, (id_user_tg,))
        result = self.cur.fetchone()
        return result[0] if result else 0