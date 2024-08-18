import re
import disnake
import asyncio
import logging
from disnake.ext import commands
from database import Database
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext

ds_token = input('DS_token: ')

tg_token = input('tg_token: ')

intents = disnake.Intents.default().all()

db = Database()

logging.basicConfig(level=logging.INFO)

tg = Bot(token=tg_token)
dp = Dispatcher(tg, storage=MemoryStorage())

ds = commands.Bot(command_prefix='/', intents=intents)


class Form(StatesGroup):
    switch_notifications = State()


@dp.message_handler(commands=["start"])
async def start_tg(message: types.Message):
    if message.get_args():
        parameter = message.get_args()
        match = re.search(r'(\d+)-(\w+)', parameter)
        user_id = match.group(1)
        server_id = match.group(2)
        await db.update_info(server_id=server_id,
                             user_id_discord=user_id,
                             user_id_telegram=message.chat.id,
                             firstname=message.from_user.first_name,
                             username=message.from_user.username)
        await db.input_ids_telegram_table(message.chat.id)
        await tg.send_message(message.chat.id, "[✅] Вы успешно привязали свой аккаунт!")
    else:
        await db.input_ids_telegram_table(message.chat.id)
        await message.reply('[👋] Привет! Перейдите по ссылке с привязкой из Discord. (Подробнее /info - В DISCORD!)')


@dp.message_handler(commands=['notifications'])
async def notifications(message: types.Message):
    telegram_ids = await db.get_user_ids(user_id_telegram=message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [types.KeyboardButton(str(tg_id)) for tg_id in telegram_ids]
    markup.add(*buttons)
    await Form.switch_notifications.set()
    await message.answer("[⚖️] Выберите сервер где хотите включить/выключить уведомления!", reply_markup=markup)


@dp.message_handler(state=Form.switch_notifications)
async def process_switch_notifications(message: types.Message, state: FSMContext):
    server_name = message.text
    server_id = await db.get_server_id(server_name=server_name)
    check_not = await db.check_notifications(server_id=server_id, user_id_telegram=message.chat.id)
    print(check_not[0])
    if check_not[0] == "Выключены":
        await db.update_notif(notifications="Включены", user_id_tg=message.chat.id, server_id=server_id)
        kb = [
            [
                types.KeyboardButton(text="/notifications"),
            ]
        ]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=kb)
        await tg.send_message(message.chat.id, "[🟢] Вы включили уведомления с дискорда!", reply_markup=markup)
        await state.finish()
    elif check_not[0] == 'Включены':
        await db.update_notif(notifications="Выключены", user_id_tg=message.chat.id, server_id=server_id)
        kb = [
            [
                types.KeyboardButton(text="/notifications"),
            ]
        ]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=kb)
        await tg.send_message(message.chat.id, "[🔴] Вы выключили уведомления с дискорда!", reply_markup=markup)
        await state.finish()
    else:
        await tg.send_message(message.chat.id, "[⛔] Вы не зарегистрированы. Напишите /start для регистрации!")
        await state.finish()


@dp.message_handler(commands=['sendall'])
async def sendall(message: types.Message):
    if message.chat.id == 2023527964:
        text_send = message.get_args()
        ids = await db.output_ids_telegram_table()
        kb = [
            [
                types.KeyboardButton(text="/notifications"),
            ]
        ]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=kb)
        for user in ids:
            await tg.send_message(user, f'```{text_send}```', reply_markup=markup, parse_mode='Markdown')

        await tg.send_message(message.chat.id, f'отправили всем [{ids}]')
    else:
        pass


@dp.message_handler()
async def message_in_discord(message: types.Message):
    server_id = await db.check_channel_id(user_telegram_id=message.chat.id)
    text_server = message.text
    server_name = await db.get_server_name()
    if text_server in server_name:
        await message.answer(f'[✍🏻] Введите текст который хотите отправить на {text_server}:')
        server_channel_id = await db.get_channel_id(server_name=text_server)
        await db.update_last_msg(user_telegram_id=message.chat.id, last_msg=server_channel_id[0])
    elif server_id != 0:
        user_text = message.text
        await on_ready(name=message.from_user.username, message=user_text, channel_id=server_id)
        await db.update_last_msg(user_telegram_id=message.chat.id, last_msg=0)
        types.ReplyKeyboardRemove()
        kb = [
            [
                types.KeyboardButton(text="/notifications"),
            ]
        ]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=kb)
        await message.answer('[✅] Успешно отправлено!', reply_markup=markup)
    else:
        telegram_ids = await db.get_user_ids(user_id_telegram=message.chat.id)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [types.KeyboardButton(str(tg_id)) for tg_id in telegram_ids]
        markup.add(*buttons)
        await message.answer("[⚖️] Выберите сервер куда хотите написать!", reply_markup=markup)


@ds.event
async def on_ready(name, message, channel_id):
    URL = f'[{name}](https://t.me/{name})'
    embed = disnake.Embed(title=f"[📩] Сообщение из телеграмм от: ", description=URL, color=disnake.Colour.blue())
    embed.add_field(name='[📝] Содержание сообщение:', value=message)
    embed.set_thumbnail(url="https://cdn2.iconfinder.com/data/icons/round-set-vol-2/120/sending-1024.png")
    channel = ds.get_channel(channel_id)
    await channel.send(embed=embed)


@ds.event
async def on_message(message):
    if message.author == ds.user:
        return

    user_list = await db.get_id_notifications()
    server_id = message.guild.id

    for userid in user_list:
        print(userid)
        checker = await db.check_notifications(server_id=server_id, user_id_telegram=userid)
        print(checker)
        if checker[0] == 'Выключены':
            user_list.remove(userid)
            print(user_list)
        else:
            await tg.send_message(userid, f'{message.author}:\n{message.content}')


@ds.event
async def on_guild_join(guild):
    channel = guild.system_channel
    if channel is not None:
        await channel.send(f'[🚀] Привет! Для начала работы со мной пропишите команду /start!')


@ds.slash_command(name='start', description="Регистрация Discord сервера")
@commands.has_permissions(administrator=True)
async def start(interaction: disnake.ApplicationCommandInteraction):
    examination = await db.get_server_name()
    server_id = [interaction.guild.id]
    user_id = interaction.user.id
    channel_id = interaction.channel.id
    server_name = [interaction.guild.name]
    if server_name[0] in [name.strip("'") for name in examination]:
        await interaction.send("[✅] Ваш сервер уже зарегистрирован!")
    else:
        await interaction.send("[⚙️] Регистрация вашего Discord сервера...")
        await db.start(server_id=server_id, channel_id=channel_id, user_id_discord=user_id, server_name=server_name)
        await interaction.send("[✅] Ваш сервер успешно зарегистрирован!")


@start.error
async def admin_command_error(interaction: disnake.ApplicationCommandInteraction, error):
    if isinstance(error, commands.MissingPermissions):
        await interaction.send("[⛔] У вас нет прав для использования этой команды.", ephemeral=True)


@ds.slash_command(name='info', description="Информация зарегистрированных пользователей в телеграмм")
async def info(interaction: disnake.ApplicationCommandInteraction):
    server_id = interaction.guild.id
    users = await db.info(server_id=server_id)
    user_list = '\n'.join([f'{user[4]} - @{user[5]}' for user in users])
    embed = disnake.Embed(title=f'[🌐] Пользователи которым вы можете отправить сообщение:\n',
                          color=disnake.Colour.blurple())
    embed.add_field(name='', value=user_list)
    embed.add_field(name="[❓] Как отправить сообщение?",
                    value="[💡] Ввести команду /stg -> выбрать кому отправить -> написать сообщение.",
                    inline=False)
    embed.add_field(name='[❓] Как привязать аккаунт Telegram?',
                    value='[💡] Ввести команду /link -> перейти по ссылке -> нажать кнопку в Telegram боте.',
                    inline=False)
    embed.set_thumbnail(url="https://cdn2.iconfinder.com/data/icons/round-set-vol-2/120/sending-1024.png")
    await interaction.send(embed=embed, ephemeral=True)


@ds.slash_command(name='stg', description="Отправить сообщение в телеграмм")
async def stg(interaction: disnake.ApplicationCommandInteraction, name: str, message: str):
    channel_id = interaction.channel_id
    server_id = interaction.guild.id
    users = await db.info(server_id=server_id)
    user_list = [f'{user[4]}' for user in users]
    print(user_list)
    if name in user_list:
        user = interaction.user
        user_id = [f'{user[2]}' for user in users]
        await interaction.send(f"[📨] Вы отправили сообщение пользователю - {name}!")
        await tg.send_message(user_id[0], f'[{message}] - от {user.name}')
        await db.update_last_msg(user_telegram_id=user_id[0], last_msg=channel_id)
    else:
        await interaction.send(f"[❌] Вы не привязали свой аккаунт Telegram! Введите команду /info!", ephemeral=True)


@stg.autocomplete('name')
async def name_autocomplete(interaction: disnake.ApplicationCommandInteraction, current: str):
    server_id = interaction.guild.id
    users = await db.info(server_id=server_id)
    user_list = [f'{user[4]}' for user in users]
    choices = [name for name in user_list if current.lower() in name.lower()]
    return choices


@ds.slash_command(name="dev", description="Разработчик бота")
async def dev(interaction: disnake.ApplicationCommandInteraction):
    embed = disnake.Embed(title="[👨🏻‍💻] О боте:", color=0x185200)
    embed.add_field(name="[🛠] Разработчик", value="@solarezzwhynot")
    embed.add_field(name="[⚙️] Версия", value="1.1")
    embed.add_field(name="[💳] Поддержка копеечкой для хостинга", value="2200 7007 1699 4750")
    embed.set_thumbnail(url="https://i.pinimg.com/originals/f8/d0/bc/f8d0bc025046ab637a78a09598b905a7.png")
    await interaction.send(embed=embed)


@ds.slash_command(name='link', description='Привязать аккаунт к Telegram')
async def link(interaction: disnake.ApplicationCommandInteraction):
    try:
        user_id = interaction.author.id
        server_id = interaction.guild.id
        await db.add_user(server_id=server_id, user_id_discord=user_id)
        referral_link = f'https://t.me/solarezzTesting_BOT?start={user_id}-{server_id}'
        await interaction.send(f"[🔗] Вот ваша ссылка для привязки аккаунта Telegram: {referral_link}", ephemeral=True)
    except:
        await interaction.send("[⚠️] Ваш Discord еще не зарегистрирован в базе. Обратитесь к администратору сервера!")


async def main():
    # Start the Telegram bot
    await dp.start_polling(tg)


# Run both bots
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_until_complete(ds.start(ds_token))
