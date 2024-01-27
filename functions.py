import os
from database import BotDataBase
import os
import shutil
import zipfile
import json

# импорт библиотек для шифрования
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64
import hashlib



def generate_new_key_and_iv():
    data = {
        'key': base64.b64encode(get_random_bytes(32)).decode('utf-8'),
        'iv': base64.b64encode(get_random_bytes(AES.block_size)).decode('utf-8')
    }

    with open('setting.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)



def check_key_file():
    if not os.path.exists('setting.json'):
        with open('setting.json', 'w', encoding='utf-8') as file:
            json.dump({}, file)
    else:
        with open('setting.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        if 'key' not in data:
            return False
        if 'iv' not in data:
            return False
        return True


def encrypt_data(plain_text):
    if not plain_text:
        plain_text = ''

    with open('setting.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    key = base64.b64decode(data['key'])
    iv = base64.b64decode(data['iv'])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_text = pad(plain_text.encode(), AES.block_size)
    cipher_text = cipher.encrypt(padded_text)
    cipher_text_b64 = base64.b64encode(iv + cipher_text)
    return cipher_text_b64



def decrypt_data(cipher_text_b64):
    with open('setting.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    key = base64.b64decode(data['key'])
    cipher_text_plus_iv = base64.b64decode(cipher_text_b64)
    iv_dec = cipher_text_plus_iv[:AES.block_size]
    cipher_text_dec = cipher_text_plus_iv[AES.block_size:]
    cipher_dec = AES.new(key, AES.MODE_CBC, iv_dec)

    decrypted_padded_text = cipher_dec.decrypt(cipher_text_dec)
    decrypted_text = unpad(decrypted_padded_text, AES.block_size)
    return decrypted_text.decode()



def md5_encrypt(data):
    data_bytes = data.encode('utf-8')
    hash_object = hashlib.md5(data_bytes)
    md5_hash = hash_object.hexdigest()
    return md5_hash


def get_encrypted_path(a, b):
    return f'files\{md5_encrypt(str(a)+"_"+str(b))}'


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
        remove_directory(f'{get_encrypted_path(message["chat_id"], message["message_id"])}')



def move_media_to_archive(file_path, server_path):
    create_directory_if_not_exists(server_path)
    filename = os.path.basename(file_path)
    destination = os.path.join(server_path, filename)
    destination_archive = os.path.join(server_path, md5_encrypt(filename))
    shutil.move(file_path, destination)
    shutil.make_archive(destination_archive, 'zip', server_path, filename)
    os.remove(destination)
    return md5_encrypt(filename)



def unzip_media(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        file_names = zip_ref.namelist()
        zip_ref.extractall(extract_to)
        return file_names[0]



def init():
    if not check_key_file():
        print("Empty cipher KEY and IV field")
        option = int(input("Введите 0 для выхода, 1 для генерации нового ключа шифрования: "))
        if option == 1:
            generate_new_key_and_iv()
            init()
        else:
            sys.exit(1)