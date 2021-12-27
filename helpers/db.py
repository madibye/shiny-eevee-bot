from pymongo import MongoClient
import config

mongo_client = MongoClient(config.mongo_url)
database = mongo_client.staff_bot  # Database
db_reminders = database.reminders  # Mongo Collection


async def add_reminder(data):
    return db_reminders.insert_one(data).inserted_id

async def get_reminder_from_url(url: str):
    return db_reminders.find_one({"url": url})

async def delete_reminder(document):
    return db_reminders.remove(document)

async def get_all_reminders():
    return db_reminders.find({})
