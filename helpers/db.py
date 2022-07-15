from pymongo import MongoClient
import config

mongo_client = MongoClient(config.mongo_url)
database = mongo_client.staff_bot  # Database
db_reminders = database.reminders  # Mongo Collection
db_threads = database.threads
db_roles = database.roles


def add_reminder(data):
    return db_reminders.insert_one(data).inserted_id

def get_reminder_from_url(url: str):
    return db_reminders.find_one({"url": url})

def delete_reminder(document):
    return db_reminders.remove(document)

def get_all_reminders():
    return db_reminders.find({})

def create_thread_keep_alive_list():
    thread_list_doc = {
        "_id": "keep_alive_threads",
        "threads": []  # List[int]
    }
    db_threads.insert_one(thread_list_doc)
    return thread_list_doc

def add_keep_alive_thread(thread_id):
    thread_list_doc = db_threads.find_one({"_id": "keep_alive_threads"})
    if thread_id not in thread_list_doc["threads"]:
        thread_list_doc["threads"].append(thread_id)
        return db_threads.replace_one({"_id": "keep_alive_threads"}, thread_list_doc)

def remove_keep_alive_thread(thread_id):
    thread_list_doc = db_threads.find_one({"_id": "keep_alive_threads"})
    if thread_id in thread_list_doc["threads"]:
        thread_list_doc["threads"].remove(thread_id)
        return db_threads.replace_one({"_id": "keep_alive_threads"}, thread_list_doc)

def get_keep_alive_threads():
    thread_list_doc = db_threads.find_one({"_id": "keep_alive_threads"})
    if not thread_list_doc:
        thread_list_doc = create_thread_keep_alive_list()
    return thread_list_doc["threads"]

def create_custom_role_list():
    roles_doc = {
        "_id": "custom_roles",
        "role_ids": {}  # {user_id: role_id, etc.}
    }
    db_roles.insert_one(roles_doc)
    return roles_doc

def edit_custom_role(user_id: str, role_id: int):
    roles_doc = db_roles.find_one({"_id": "custom_roles"})
    if not roles_doc:
        roles_doc = create_custom_role_list()
    roles_doc["role_ids"][user_id] = role_id
    return db_roles.replace_one({"_id": "custom_roles"}, roles_doc)

def get_custom_roles():
    roles_doc = db_threads.find_one({"_id": "keep_alive_threads"})
    if not roles_doc:
        roles_doc = create_custom_role_list()
    return roles_doc["role_ids"]
