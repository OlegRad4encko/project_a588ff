from telethon import TelegramClient, events
from config import *
from functions import *
import os
import sys
from typing import NoReturn




# оглашение глобальных переменных
queue = [] # очередь - необходима в случае, когда команда /set_default_chat не была выполнено. Все удаленные сообщения соберутся в очередь.
default_chat_id = None # тут хранится чат для отчетах о удаленных сообщениях
client = None # клиент телеграм, через который скрипт взаимодействует с телеграмом




# проверка, вписаны ли настройки в файл config.py
try:
    client = TelegramClient('session_name', API_ID, API_HASH)
except ValueError as error:
    print("Настройте API_ID и API_HASH. ", error)
    sys.exit()




# обработчик события установки дефолтного чата для отчетов об удаленных сообщениях
@client.on(events.NewMessage(pattern='/set_default_chat'))
async def set_default_chat(event) -> NoReturn:
    global default_chat_id
    default_chat_id = event.chat_id
    await event.respond('Чат установлен как место для отчетов об удаленных сообщениях.')

    # если после установки чата очередь не пуста - вызов метода отображении истории
    if(len(queue) != 0):
        await show_queue()




# хендлер обработки нового сообщения
@client.on(events.NewMessage())
async def new_message_handler(event) -> NoReturn:
    # проверка, является ли чат приватным
    if event.is_private:
        user = await event.get_sender() # данные о пользователе
        message_data = { # создание словаря с данными нового сообщения
            'user_id': user.id,
            'first_name': encrypt_data(user.first_name),
            'last_name': encrypt_data(user.last_name),
            'username': encrypt_data(user.username),
            'message': {
                'from_user': user.id,
                'chat_id': event.chat_id,
                'message_id': event.message.id,
                'message_text': encrypt_data(event.text)
            }
        }

        # проверка на медиа в сообщении, если да то ...
        if event.message.media:
            file_path = await client.download_media(event.message)
            server_path = get_encrypted_path(message_data["message"]["chat_id"], message_data["message"]["message_id"])
            message_data['message']['include_media'] = move_media_to_archive(file_path, server_path)

        # если нет в сообщении медиа, то ...
        else:
            message_data['message']['include_media'] = None

        # запись нового сообщения в БД
        add_message(message_data)




# Обработчик события удаления сообщения
@client.on(events.MessageDeleted())
async def delete_message_handler(event) -> NoReturn:
    global default_chat_id # айди чата куда слать сообщение
    global queue # очередь
    deleted_messages = event.deleted_ids # айди удаленных сообщений
    messages_data = get_deleted_messages_data(deleted_messages) # данные удаленных сообщений

    try:
        for message in messages_data['message']:

            # формирование сообщения на вывод
            del_msg = f'Удалено сообщение от пользователя {decrypt_data(messages_data["owner"]["first_name"])} {decrypt_data(messages_data["owner"]["last_name"])} | @{decrypt_data(messages_data["owner"]["username"])} \n '
            del_msg += f'Содержание сообщения: \n'

            # если текст содержится в сообщении, то ...
            if message['message_text'] != '':
                del_msg += f'<b>Текст:</b>\n'
                del_msg += f'<code>\n{decrypt_data(message["message_text"])}\n</code>'

            # Если медиа содержится в сообщении, то ...
            if message["include_media"] != None:
                folder_path = get_encrypted_path(message["chat_id"], message["message_id"])
                extract_to = folder_path
                media_path = folder_path+"\\"+unzip_media(folder_path +"\\"+ message['include_media'] +'.zip', extract_to)
                await client.send_file(default_chat_id, media_path, caption=del_msg, parse_mode='html')
            else:
                await client.send_message(default_chat_id, del_msg, parse_mode='html')

            # удаление данных о сообщении после восстановления удаленного сообщения и отправки в чат
            delete_message_data(message)

    # обработчик исключения, когда не сохраненное сообщение было удалено
    except TypeError as error:
        # если default_chat_id установлен, пользователю будет выведено ...
        try:
            await client.send_message(default_chat_id, 'Сообщение было удалено пользователем')

        # если не установлено, формируем информационное сообщение в консоль
        except:
            print('Напиши команду /set_default_chat в том чате, куда необходимо отправлять отчеты об удаленных сообщениях.')
            queue.append(messages_data)




# метод отображения очереди из удаленных сообщений
async def show_queue() -> NoReturn:
    global queue # очередь
    global default_chat_id # айди чата куда слать сообщение

    # проходимся по списку из очереди (состоит из элементов в каждом из которых есть владелец и удаленные им сообщения)
    for message in queue:

        # проходимся по сообщениям каждого владельца
        for message_data in message['message']:

            # формируем сообщение в чат для отчетов
            del_msg = f'Удалено сообщение от пользователя {decrypt_data(message["owner"]["first_name"])} {decrypt_data(message["owner"]["last_name"])} | @{decrypt_data(message["owner"]["username"])} \n '
            del_msg += f'Содержание сообщения: \n'

            # если текст содержится в сообщении, то ...
            if message_data['message_text'] != '':
                del_msg += f'<b>Текст:</b>\n'
                del_msg += f'<code>\n{decrypt_data(message_data["message_text"])}\n</code>'

            # Если медиа содержится в сообщении, то ...
            if message_data["include_media"] != None:
                folder_path = get_encrypted_path(message_data["chat_id"], message_data["message_id"])
                extract_to = folder_path
                media_path = folder_path+"\\"+unzip_media(folder_path +"\\"+ message_data['include_media'] +'.zip', extract_to)
                await client.send_file(default_chat_id, media_path, caption=del_msg, parse_mode='html')
            else:
                await client.send_message(default_chat_id, del_msg, parse_mode='html')

            # удаляем данные в бд и файловой системе о тех сообщениях, которые были восстановлены и пересланы в default_chat_id
            delete_message_data(message_data)

    # Очищаем историю
    queue = []




# если выполняемым файлом считается текущий - запускаем проверку и коннект к телеграму
if __name__ == '__main__':
    # инициализирующая проверка настроек, ключей шифрования, базы данных
    init()

    # запуск
    with client:
        print("Бот запущен.")
        client.run_until_disconnected()
