from telethon import TelegramClient, events
from config import *
from functions import *
import os
import shutil

queue = []
default_chat_id = None
client = TelegramClient('session_name', API_ID, API_HASH)


@client.on(events.NewMessage(pattern='/set_default_chat'))
async def set_default_chat(event):
    global default_chat_id
    default_chat_id = event.chat_id
    await event.respond('Чат установлен как место для отчетов об удаленных сообщениях.')

    if(len(queue) != 0):
        await show_queue()




@client.on(events.NewMessage())
async def new_message_handler(event):
    if event.is_private:
        user = await event.get_sender()
        message_data = {
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

        if event.message.media:
            file_path = await client.download_media(event.message)
            server_path = get_encrypted_path(message_data["message"]["chat_id"], message_data["message"]["message_id"])
            message_data['message']['include_media'] = move_media_to_archive(file_path, server_path)

        else:
            message_data['message']['include_media'] = None

        add_message(message_data)



@client.on(events.MessageDeleted())
async def delete_message_handler(event):
    global default_chat_id
    global queue
    deleted_messages = event.deleted_ids
    messages_data = get_deleted_messages_data(deleted_messages)
    try:
        for message in messages_data['message']:
            del_msg = f'Удалено сообщение от пользователя {decrypt_data(messages_data["owner"]["first_name"])} {decrypt_data(messages_data["owner"]["last_name"])} | @{decrypt_data(messages_data["owner"]["username"])} \n '
            del_msg += f'Содержание сообщения: \n'

            if message['message_text'] != '':
                del_msg += f'<b>Текст:</b>\n'
                del_msg += f'<code>\n{decrypt_data(message["message_text"])}\n</code>'

            if message["include_media"] != None:
                folder_path = get_encrypted_path(message["chat_id"], message["message_id"])
                extract_to = folder_path
                media_path = folder_path+"\\"+unzip_media(folder_path +"\\"+ message['include_media'] +'.zip', extract_to)
                await client.send_file(default_chat_id, media_path, caption=del_msg, parse_mode='html')
            else:
                await client.send_message(default_chat_id, del_msg, parse_mode='html')

            delete_message_data(message)
    except TypeError as error:
        try:
            await client.send_message(default_chat_id, 'Сообщение было удалено пользователем')
        except:
            print('Напиши команду /set_default_chat в том чате, куда необходимо отправлять отчеты об удаленных сообщениях.')
            queue.append(messages_data)



async def show_queue():
    global queue
    global default_chat_id

    for message in queue:
        for message_data in message['message']:
            del_msg = f'Удалено сообщение от пользователя {decrypt_data(message["owner"]["first_name"])} {decrypt_data(message["owner"]["last_name"])} | @{decrypt_data(message["owner"]["username"])} \n '
            del_msg += f'Содержание сообщения: \n'

            if message_data['message_text'] != '':
                del_msg += f'<b>Текст:</b>\n'
                del_msg += f'<code>\n{decrypt_data(message_data["message_text"])}\n</code>'

            if message_data["include_media"] != None:
                folder_path = get_encrypted_path(message_data["chat_id"], message_data["message_id"])
                extract_to = folder_path
                media_path = folder_path+"\\"+unzip_media(folder_path +"\\"+ message_data['include_media'] +'.zip', extract_to)
                await client.send_file(default_chat_id, media_path, caption=del_msg, parse_mode='html')
            else:
                await client.send_message(default_chat_id, del_msg, parse_mode='html')

            delete_message_data(message_data)
    queue = []




if __name__ == '__main__':
    init()
    with client:
        client.run_until_disconnected()
