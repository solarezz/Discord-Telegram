import aiosqlite


class Database:
    def __init__(self, db_name='database.db'):
        self.db_name = db_name

    async def start(self, server_id, channel_id, user_id_discord, server_name):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(f"""
            CREATE TABLE IF NOT EXISTS {server_id} (
    server_name       TEXT  DEFAULT {server_name},
    channel_id        INTEGER DEFAULT {channel_id},
    user_id_telegram  INTEGER DEFAULT (NULL),
    user_id_discord   INTEGER UNIQUE,
    firstname         TEXT    DEFAULT (NULL),
    username          TEXT    DEFAULT (NULL),
    cooldown_telegram INTEGER DEFAULT (0),
    cooldown_discord  INTEGER DEFAULT (0),
    notifications     TEXT    DEFAULT Выключены
)
""")
            await db.execute(f'INSERT INTO {server_id} (user_id_discord) VALUES (?)',
                             (user_id_discord,))
            await db.commit()
            #await self.add_user(user_id_discord=user_id_discord, server_id=server_id)

    async def add_user(self, user_id_discord, server_id):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(f'INSERT OR IGNORE INTO [{server_id}] (user_id_discord) VALUES (?)',
                             (user_id_discord,))
            await db.commit()

    async def checker(self, server_id):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(f'SELECT * FROM [{server_id}]') as cursor:
                checker = cursor.fetchall
                return checker

    async def update_info(self, server_id, user_id_discord, user_id_telegram, firstname, username):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                f'UPDATE [{server_id}] SET user_id_telegram = ?, firstname = ?, username = ? WHERE user_id_discord = ?',
                (user_id_telegram,
                 firstname,
                 username,
                 user_id_discord))
            await db.commit()

    async def input_ids_telegram_table(self, user_id):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(f'INSERT OR IGNORE INTO users_telegram (user_id) VALUES (?)',
                             (user_id,))
            await db.commit()

    async def output_ids_telegram_table(self):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT user_id FROM users_telegram') as cursor:
                result = await cursor.fetchall()
                return [row[0] for row in result]

    async def info(self, server_id):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(f'SELECT * FROM [{server_id}]') as cursor:
                users = await cursor.fetchall()
                return users

    async def update_last_msg(self, user_telegram_id, last_msg):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(f'UPDATE users_telegram SET last_msg_id=? WHERE user_id=?',
                             (last_msg,
                              user_telegram_id))
            await db.commit()

    async def check_channel_id(self, user_telegram_id):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT last_msg_id FROM users_telegram WHERE user_id=?',
                                  (user_telegram_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0]

    async def get_user_ids(self, user_id_telegram):
        async with aiosqlite.connect(self.db_name) as db:
            # Получаем список всех таблиц в базе данных
            async with db.execute("SELECT name FROM sqlite_master WHERE type='table';") as cursor:
                tables = await cursor.fetchall()

            user_ids = []

            # Проходим по всем таблицам и пытаемся получить user_id_telegram
            for (table_name,) in tables:
                try:
                    async with db.execute(f"SELECT server_name FROM [{table_name}] WHERE user_id_telegram=?;",
                                          (user_id_telegram,)) as cursor:
                        rows = await cursor.fetchall()
                        user_ids.extend([row[0] for row in rows if row[0] is not None])
                except aiosqlite.Error as e:
                    print(f"Ошибка при обработке таблицы {table_name}: {e}")

            return user_ids

    async def get_channel_id(self, server_name):
        async with aiosqlite.connect(self.db_name) as db:
            # Получаем список всех таблиц в базе данных
            async with db.execute("SELECT name FROM sqlite_master WHERE type='table';") as cursor:
                tables = await cursor.fetchall()

            channel_id = []

            # Проходим по всем таблицам и пытаемся получить user_id_telegram
            for (table_name,) in tables:
                try:
                    async with db.execute(f"SELECT channel_id FROM [{table_name}] WHERE server_name = ?;",
                                          (server_name,)) as cursor:
                        rows = await cursor.fetchall()
                        channel_id.extend([row[0] for row in rows if row[0] is not None])
                except aiosqlite.Error as e:
                    print(f"Ошибка при обработке таблицы {table_name}: {e}")

            return channel_id

    async def get_server_name(self):
        async with aiosqlite.connect(self.db_name) as db:
            # Получаем список всех таблиц в базе данных
            async with db.execute("SELECT name FROM sqlite_master WHERE type='table';") as cursor:
                tables = await cursor.fetchall()

            server_name = []

            # Проходим по всем таблицам и пытаемся получить user_id_telegram
            for (table_name,) in tables:
                try:
                    async with db.execute(f"SELECT server_name FROM [{table_name}]") as cursor:
                        rows = await cursor.fetchall()
                        server_name.extend([row[0] for row in rows if row[0] is not None])
                except aiosqlite.Error as e:
                    print(f"Ошибка при обработке таблицы {table_name}: {e}")

            return server_name

    async def check_notifications(self, server_id, user_id_telegram):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(f'SELECT notifications FROM [{server_id}] WHERE user_id_telegram=?',
                                  (user_id_telegram,)) as cursor:
                result = await cursor.fetchone()
                return result

    async def update_notif(self, notifications, user_id_tg, server_id):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(f'UPDATE [{server_id}] SET notifications=? WHERE user_id_telegram=?',
                             (notifications,
                              user_id_tg))
            await db.commit()

    async def get_id_notifications(self):
        async with aiosqlite.connect(self.db_name) as db:
            # Получаем список всех таблиц в базе данных
            async with db.execute("SELECT name FROM sqlite_master WHERE type='table';") as cursor:
                tables = await cursor.fetchall()

            user_ids = []

            # Проходим по всем таблицам и пытаемся получить user_id_telegram
            for (table_name,) in tables:
                try:
                    async with db.execute(
                            f"SELECT user_id_telegram FROM [{table_name}] WHERE notifications = 'Включены';") as cursor:
                        rows = await cursor.fetchall()
                        user_ids.extend([row[0] for row in rows if row[0] is not None])
                except aiosqlite.Error as e:
                    print(f"Ошибка при обработке таблицы {table_name}: {e}")

            return user_ids

    async def get_server_id(self, server_name):
        async with aiosqlite.connect(self.db_name) as db:
            # Получаем список всех таблиц в базе данных
            async with db.execute("SELECT name FROM sqlite_master WHERE type='table';") as cursor:
                tables = await cursor.fetchall()

            # Перебираем все таблицы и ищем сервер
            for (table_name,) in tables:
                try:
                    async with db.execute(f"SELECT * FROM [{table_name}] WHERE server_name = ?", (server_name,)) as cursor:
                        row = await cursor.fetchone()
                        if row:
                            return table_name
                except:
                    pass

        return "Сервер не найден."
