from time import time
from pymongo import ASCENDING, MongoClient
import configparser

config = configparser.ConfigParser()
config.read('bot.conf')
MONGO_CON = config['DB']['MONGO_CON']

client = MongoClient(MONGO_CON)
db = client.sportnews

# NEWS


def search_id(id):
    return db.news.find_one({'id': id})


def check_history(link):
    return db.news.find_one({'link': link})


def search_title(title):
    return db.news.find_one({'title': title})


def search_tag(tag):
    return db.news.find_one({'tag': tag})


def get_all_news():
    return db.news.find({})


def remove_all_news():
    db.news.delete_many({})


# user


def search_user(user_id):
    return db.users.find_one({'user_id': user_id})


def get_all_users():
    return db.users.find({})


def set_user_sudo(user_id):
    return db.users.update_one(
        {'user_id': user_id}, {'$set': {'sudo': 'true'}}
    )


def un_set_user_sudo(user_id):
    return db.users.update_one(
        {'user_id': user_id}, {'$set': {'sudo': 'false'}}
    )


# chat


def search_chat(chat_id):
    return db.chats.find_one({'chat_id': chat_id})


def get_all_chats():
    return db.chats.find({})


def remove_chat_db(chat_id):
    db.chats.delete_one({'chat_id': chat_id})


# NOVO


def add_news(title, date):
    last_id = db.news.find().sort('id', -1).limit(1)
    last_id = list(last_id)

    if len(last_id) == 0:
        news_id = 1
    else:
        last_id = last_id[0]['id']
        news_id = int(last_id) + 1
    result = db.news.insert_one(
        {
            'id': news_id,
            'title': title,
            'date': date,
        }
    )
    return result


def add_chat_db(chat_id, chat_name):
    return db.chats.insert_one(
        {
            'chat_id': chat_id,
            'chat_name': chat_name,
            'banned': 'false',
            'tag': '',
        }
    )


def add_user_db(message):
    first_name = message.from_user.first_name
    last_name = str(message.from_user.last_name).replace('None', '')
    username = str(message.from_user.username).replace('None', '')
    return db.users.insert_one(
        {
            'user_id': message.from_user.id,
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'sudo': 'false',
        }
    )
