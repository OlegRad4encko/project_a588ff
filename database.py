import pymysql
import sys
import config
from typing import NoReturn, Union, List, Dict
from loging_module import log_event

class BotDataBase:

    # конструктор
    def __init__(self,
        host: str = config.DB_HOST,
        port: int = config.DB_PORT,
        user: str = config.DB_USER,
        password: str = config.DB_PASSWORD,
        database: str = config.DB_NAME) -> NoReturn:
        try:
            self.connection = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                cursorclass=pymysql.cursors.DictCursor
            )
        except Exception as db_ex:
            print('No connection to database. Check your settings')
            log_event('critical', db_ex)
            sys.exit()




    # метод вставки в БД пользователей
    def insert_user(self, user_id: int, username: bytes, last_name: bytes, first_name: bytes) -> NoReturn:
        with self.connection.cursor() as cursor:
            try:
                insert_data_query = f'INSERT INTO `users` (`user_id`, `username`, `last_name`, `first_name`) VALUES (%s, %s, %s, %s)'
                cursor.execute(insert_data_query, (user_id, username, last_name, first_name))
                self.connection.commit()
            except Exception as error:
                if 'Duplicate entry' not in str(error):
                    log_event('error', error)

            finally:
                pass




    # метод вставки в БД сообщений
    def insert_message(self, from_user: int, chat_id: int, message_id: int, message_text: bytes, include_media: Union[str, None]) -> NoReturn:
        with self.connection.cursor() as cursor:
            try:
                insert_data_query = f'INSERT INTO `messages` (`from_user`, `chat_id`, `message_id`, `message_text`, `include_media`) VALUES (%s, %s, %s, %s, %s)'
                cursor.execute(insert_data_query, (from_user, chat_id, message_id, message_text, include_media))
                self.connection.commit()
            except Exception as error:
                if 'Duplicate entry' not in str(error):
                    log_event('error', error)

            finally:
                pass




    # метод извлечения из БД сообщений, которые были удалены
    def get_deleted_messages_data(self, message_id: int) -> Union[Dict, NoReturn]:
        with self.connection.cursor() as cursor:
            try:
                select_data_query = f'select `id`, `from_user`, `chat_id`, `message_id`, `message_text`, `include_media` from `messages` where `message_id` = %s'
                cursor.execute(select_data_query, (message_id))
                return cursor.fetchall()[0]
            except Exception as error:
                log_event('error', error)

            finally:
                pass




    # метод извлечения из БД отправителя сообщения
    def get_messages_owner(self, from_user: int) -> Union[Dict, NoReturn]:
        with self.connection.cursor() as cursor:
            try:
                select_data_query = f'select `first_name`, `last_name`, `username` from `users` where `user_id` = %s'
                cursor.execute(select_data_query, (from_user))
                return cursor.fetchall()[0]
            except Exception as error:
                log_event('error', error)

            finally:
                pass




    # метод удаления из БД сообщений, которые были удалены
    def delete_message_from_db(self, message_id: int) -> NoReturn:
        with self.connection.cursor() as cursor:
            try:
                select_data_query = f'delete from `messages` where `id` = %s'
                cursor.execute(select_data_query, (message_id))
                self.connection.commit()
            except Exception as error:
                log_event('error', error)

            finally:
                pass




    # метод закрытия соединения с БД
    def close_connection(self) -> NoReturn:
        self.connection.close()