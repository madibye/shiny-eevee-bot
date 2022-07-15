from pymongo import MongoClient
import config

mongo_client = MongoClient(config.mongo_url)
database = mongo_client.staff_bot  # Database
db_reminders = database.reminders  # Mongo Collection


def add_reminder(data):
    return db_reminders.insert_one(data).inserted_id

def get_reminder_from_url(url: str):
    return db_reminders.find_one({"url": url})

def delete_reminder(document):
    return db_reminders.remove(document)

def get_all_reminders():
    return db_reminders.find({})
