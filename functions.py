import os
from database import BotDataBase
import os
import shutil
import zipfile


def remove_directory(dir_path):
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        shutil.rmtree(dir_path)



def create_directory_if_not_exists(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)



def add_message(message_data):
    db = BotDataBase()

    db.insert_user(
        message_data['user_id'],
        message_data['username'],
        message_data['last_name'],
        message_data['first_name']
    )
    db.insert_message(
        message_data['message']['from_user'],
        message_data['message']['chat_id'],
        message_data['message']['message_id'],
        message_data['message']['message_text'],
        message_data['message']['include_media']
    )
    db.close_connection()



def get_deleted_messages_data(message_ids):
    try:
        messages = {
            'owner': None,
            'message': []
        }
        db = BotDataBase()
        for id in message_ids:
            messages['message'].append(db.get_deleted_messages_data(id))

        messages['owner'] = db.get_messages_owner(messages['message'][0]['from_user'])
        db.close_connection()

        return messages
    except TypeError as error:
        print(f'No logged message was deleted id`s: {message_ids}')



def delete_message_data(message):
    db = BotDataBase()
    db.delete_message_from_db(message['id'])
    db.close_connection()

    if message["include_media"] != None:
        remove_directory(f'files\{message["chat_id"]}_{message["message_id"]}')



def move_media_to_archive(file_path, server_path):
    create_directory_if_not_exists(server_path)
    filename = os.path.basename(file_path)
    destination = os.path.join(server_path, filename)

    shutil.move(file_path, destination)
    shutil.make_archive(destination, 'zip', server_path, filename)

    os.remove(destination)
    return f'{server_path}\{filename}.zip'



def unzip_media(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
        return zip_path[0:-4]



