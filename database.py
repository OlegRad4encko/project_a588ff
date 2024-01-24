import pymysql
import sys
import config

class BotDataBase:

    def __init__(self,
        host = config.DB_HOST,
        port = config.DB_PORT,
        user = config.DB_USER,
        password = config.DB_PASSWORD,
        database = config.DB_NAME):
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
            print(db_ex)
            # logging here
            sys.exit()


    def insert_user(self, user_id, username, last_name, first_name):
        with self.connection.cursor() as cursor:
            try:
                insert_data_query = f'INSERT INTO `users` (`user_id`, `username`, `last_name`, `first_name`) VALUES (%s, %s, %s, %s)'
                cursor.execute(insert_data_query, (user_id, username, last_name, first_name))
                self.connection.commit()
            except Exception as error:
                if 'Duplicate entry' not in str(error):
                    print("Error:", error, sep=' ')
                    # logging here

            finally:
                pass


    def insert_message(self, from_user, chat_id, message_id, message_text, include_media):
        with self.connection.cursor() as cursor:
            try:
                insert_data_query = f'INSERT INTO `messages` (`from_user`, `chat_id`, `message_id`, `message_text`, `include_media`) VALUES (%s, %s, %s, %s, %s)'
                cursor.execute(insert_data_query, (from_user, chat_id, message_id, message_text, include_media))
                self.connection.commit()
            except Exception as error:
                if 'Duplicate entry' not in str(error):
                    print("Error:", error, sep=' ')
                    # logging here

            finally:
                pass


    def get_deleted_messages_data(self, message_id):
        with self.connection.cursor() as cursor:
            try:
                select_data_query = f'select `id` , `from_user`, `chat_id`, `message_id`, `message_text`, `include_media` from `messages` where `message_id` = %s'
                cursor.execute(select_data_query, (message_id))
                return cursor.fetchall()[0]
            except Exception as error:
                # logging here
                print(error)

            finally:
                pass


    def get_messages_owner(self, from_user):
        with self.connection.cursor() as cursor:
            try:
                select_data_query = f'select `first_name`, `last_name`, `username` from `users` where `user_id` = %s'
                cursor.execute(select_data_query, (from_user))
                return cursor.fetchall()[0]
            except Exception as error:
                # logging here
                print(error)

            finally:
                pass


    def delete_message_from_db(self, message_id):
        with self.connection.cursor() as cursor:
            try:
                select_data_query = f'delete from `messages` where `id` = %s'
                cursor.execute(select_data_query, (message_id))
                self.connection.commit()
            except Exception as error:
                # logging here
                print(error)

            finally:
                pass


    def close_connection(self):
        self.connection.close()