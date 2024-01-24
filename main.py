from telethon import TelegramClient, events
from config import *
from functions import *
import os
import shutil

default_chat_id = None
client = TelegramClient('session_name', API_ID, API_HASH)


@client.on(events.NewMessage(pattern='/set_default_chat'))
async def set_default_chat(event):
    global default_chat_id
    default_chat_id = event.chat_id
    await event.respond('Чат установлен как место для отчетов об удаленных сообщениях.')


@client.on(events.NewMessage())
async def new_message_handler(event):
    if event.is_private:
        user = await event.get_sender()
        message_data = {
            'user_id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'message': {
                'from_user': user.id,
                'chat_id': event.chat_id,
                'message_id': event.message.id,
                'message_text': event.text
            }
        }

        if event.message.media:
            file_path = await client.download_media(event.message)
            server_path = f'files\{message_data["message"]["chat_id"]}_{message_data["message"]["message_id"]}'
            message_data['message']['include_media'] = move_media_to_archive(file_path, server_path)

        else:
            message_data['message']['include_media'] = None

        add_message(message_data)




@client.on(events.MessageDeleted())
async def handler(event):
    global default_chat_id
    deleted_messages = event.deleted_ids
    try:
        messages_data = get_deleted_messages_data(deleted_messages)

        for message in messages_data['message']:
            del_msg = f'Удалено сообщение от пользователя {messages_data["owner"]["first_name"]} {messages_data["owner"]["last_name"]} | @{messages_data["owner"]["username"]} \n '
            del_msg += f'Содержание сообщения: \n'

            if message['message_text'] != '':
                del_msg += f'<b>Текст:</b>\n'
                del_msg += f'<i>{message["message_text"]}</i>'

            if message["include_media"] != None:
                extract_to = f'files\{message["chat_id"]}_{message["message_id"]}'
                media_path = unzip_media(message['include_media'], extract_to)
                await client.send_file(default_chat_id, media_path, caption=del_msg, parse_mode='html')
            else:
                await client.send_message(default_chat_id, del_msg, parse_mode='html')

            delete_message_data(message)
    except TypeError as error:
        client.send_message(default_chat_id, 'Незалогированное сообщение было удалено')



with client:
    client.run_until_disconnected()
