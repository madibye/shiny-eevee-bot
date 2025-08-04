from bson import ObjectId
from pymongo import MongoClient
from pymongo.database import Database, Collection
from termcolor import cprint

from config import *

mongo_client = MongoClient(mongo_url, directConnection=True)
database: Database = mongo_client.staff_bot  # Database
db_reminders: Collection = database.reminders  # Mongo Collection
db_threads: Collection = database.thread
db_roles: Collection = database.roles
db_role_pickers: Collection = database.role_pickers
db_starboard: Collection = database.starboard
db_config: Collection = database.config


def add_reminder(data):
    return db_reminders.insert_one(data).inserted_id

def get_reminder(reminder_id: str):
    return db_reminders.find_one({"_id": ObjectId(reminder_id)})

def get_reminder_from_url(url: str):
    return db_reminders.find_one({"url": url})

def delete_reminder(document):
    return db_reminders.delete_one(document)

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
        "_id": "sa_custom_roles",
        "role_ids": {}  # {guild_id: {user_id: role_id}, etc.}
    }
    db_roles.insert_one(roles_doc)
    return roles_doc

def edit_custom_role(guild_id: str, user_id: str, role_id: int):
    roles_doc = db_roles.find_one({"_id": "sa_custom_roles"})
    if not roles_doc:
        roles_doc = create_custom_role_list()
    if not roles_doc["role_ids"].get(guild_id):
        roles_doc["role_ids"][guild_id] = {}
    roles_doc["role_ids"][guild_id][user_id] = role_id
    return db_roles.replace_one({"_id": "sa_custom_roles"}, roles_doc)

def get_custom_roles():
    roles_doc = db_roles.find_one({"_id": "sa_custom_roles"})
    if not roles_doc:
        roles_doc = create_custom_role_list()
    return roles_doc["role_ids"]

def create_role_picker_db():
    role_pickers = []
    if hasattr(config, "default_role_picker_info"):
        for key, role_picker_info in default_role_picker_info.items():  # Need to unpack the dataclass objects into dicts
            document = {
                '_id': key, 'channel_id': role_picker_info.channel_id, 'embed_name': role_picker_info.embed_name, 'embed_desc': role_picker_info.embed_desc,
                'role_ids': role_picker_info.role_ids, 'max_row_length': role_picker_info.max_row_length, 'message_data': role_picker_info.message_data
            }
            db_role_pickers.insert_one(document)
            role_pickers.append(document)
    return role_pickers

def get_role_picker_db():
    """
    :return: A dict of all documents in the db converted into RolePickerInfo objects.
    """
    role_picker_db = list(db_role_pickers.find({}))

    if not role_picker_db:
        role_picker_db = create_role_picker_db()

    role_pickers = {}
    for role_picker_info in role_picker_db:  # Turn these back into RolePickerInfo objects!!!!
        role_pickers[role_picker_info['_id']] = RolePickerInfo(
            channel_id=role_picker_info['channel_id'], embed_name=role_picker_info['embed_name'], embed_desc=role_picker_info['embed_desc'],
            role_ids=role_picker_info['role_ids'], max_row_length=role_picker_info['max_row_length'], message_data=role_picker_info['message_data'])
    return role_pickers

def set_role_picker_db(role_pickers: dict):
    """
    :param role_pickers: A dict containing RolePickerInfo objects you want to go in the db. It's important to make sure
                         you're putting in the FULL db dict, like what you'd get from get_role_picker_db, but with any
                         changes you want made.
    """
    role_picker_keys = get_role_picker_ids()
    for key in role_picker_keys:  # First, we'll kill any role pickers that were removed
        if key not in role_pickers:
            db_role_pickers.delete_one({"_id": key})
    for key, role_picker_info in role_pickers.items():  # Then we again need to unpack the dataclass objects into dicts
        document = {
            '_id': key, 'channel_id': role_picker_info.channel_id, 'embed_name': role_picker_info.embed_name, 'embed_desc': role_picker_info.embed_desc,
            'role_ids': role_picker_info.role_ids, 'max_row_length': role_picker_info.max_row_length, 'message_data': role_picker_info.message_data
        }
        if key in role_picker_keys:  # Then slot them back in the db, either updating them...
            db_role_pickers.replace_one({"_id": key}, document)
        else:  # Or inserting new ones
            db_role_pickers.insert_one(document)

def get_role_picker_ids():
    role_picker_db = list(db_role_pickers.find({}))
    return [role_picker_info['_id'] for role_picker_info in role_picker_db]

def add_role_picker_msg(key: str, channel: int, message: int):
    """
    :param key: The key or ID of the role picker object you're editing
    :param channel: The channel ID of the message being set
    :param message: The message ID of the message being set
    """
    document = db_role_pickers.find_one({"_id": key})
    document["message_data"] = {'channel_id': channel, 'message_id': message}
    db_role_pickers.replace_one({"_id": key}, document)

def remove_role_picker_msg(key: str):
    """
    :param key: The key or ID of the role picker object you're editing
    """
    document = db_role_pickers.find_one({"_id": key})
    document["message_data"] = {'channel_id': 0, 'message_id': 0}
    db_role_pickers.replace_one({"_id": key}, document)

def create_starboard_db():
    document = {"_id": "starboard_messages", "message_ids": [], "starboard_msg_ids": []}
    db_starboard.insert_one(document)

def get_starboard_db():
    return db_starboard.find_one({"_id": "starboard_messages"})

def update_starboard_db(list_to_edit, new_ids):
    return db_starboard.update_one({"_id": "starboard_messages"}, {"$set": {list_to_edit: new_ids}})

def create_config_value(config_id, default_value):
    document = {"_id": config_id, "value": default_value}
    cprint(f"Creating new db_config entry under \"{document['_id']}\" with value {document['value']}", "yellow")
    db_config.insert_one(document)
    return document

def get_config_value(config_id, default_value):
    document = db_config.find_one({"_id": str(config_id)})
    if document is None:
        document = create_config_value(config_id, default_value)
    if not document:
        cprint(f"Something went wrong when getting config value `{config_id}`!", "red")
    return document["value"]

def get_config_description(config_id):
    document = db_config.find_one({"_id": str(config_id)})
    if document:
        return document.get("description")
    return None

def set_config_value(config_id, new_value):
    """Do not call this method outside of live_config.set(). Desyncing with db would be sad."""
    document: dict = db_config.find_one({"_id": str(config_id)})
    if document is None:
        return db_config.insert_one({"_id": config_id, "value": new_value})
    document["value"] = new_value
    return db_config.replace_one({"_id": config_id}, document)

def set_config_description(config_id, new_description: str):
    document: dict = db_config.find_one({"_id": str(config_id)})
    if not document:
        return
    document["description"] = new_description
    return db_config.replace_one({"_id": config_id}, document)

def set_user_timezone(user_id: int, timezone_str: str):
    document = db_config.find_one({"_id": "user_timezones"})
    if document is None:
        db_config.insert_one(document := {"_id": "user_timezones", "values": {}})
    document["values"][str(user_id)] = timezone_str
    db_config.replace_one({"_id": "user_timezones"}, document)

def get_user_timezone(user_id: int):
    document = db_config.find_one({"_id": "user_timezones"})
    if document is None:
        db_config.insert_one(document := {"_id": "user_timezones", "values": {}})
    return document["values"].get(str(user_id), "America/New_York")
