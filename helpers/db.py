from bson import ObjectId
from pymongo import MongoClient

from config import *

mongo_client = MongoClient(mongo_url)
database = mongo_client.staff_bot  # Database
db_reminders = database.reminders  # Mongo Collection
db_threads = database.thread
db_roles = database.roles
db_role_pickers = database.role_pickers


def add_reminder(data):
    return db_reminders.insert_one(data).inserted_id

def get_reminder(reminder_id: str):
    return db_reminders.find_one({"_id": ObjectId(reminder_id)})

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
    roles_doc = db_roles.find_one({"_id": "custom_roles"})
    if not roles_doc:
        roles_doc = create_custom_role_list()
    return roles_doc["role_ids"]

async def create_role_picker_db():
    role_pickers = []
    if hasattr(config, "default_role_picker_info"):
        for key, role_picker_info in default_role_picker_info.items():  # Need to unpack the dataclass objects into dicts
            document = {
                '_id': key, 'channel_id': role_picker_info.channel_id, 'embed_name': role_picker_info.embed_name, 'embed_desc': role_picker_info.embed_desc,
                'role_ids': role_picker_info.role_ids, 'max_row_length': role_picker_info.max_row_length, 'message_data': role_picker_info.message_data
            }
            await db_role_pickers.insert_one(document)
            role_pickers.append(document)
    return role_pickers


async def get_role_picker_db():
    """
    :return: A dict of all documents in the db converted into RolePickerInfo objects.
    """
    role_picker_db = await db_role_pickers.find().to_list(1000)

    if not role_picker_db:
        role_picker_db = await create_role_picker_db()

    role_pickers = {}
    for role_picker_info in role_picker_db:  # Turn these back into RolePickerInfo objects!!!!
        role_pickers[role_picker_info['_id']] = RolePickerInfo(
            channel_id=role_picker_info['channel_id'], embed_name=role_picker_info['embed_name'], embed_desc=role_picker_info['embed_desc'],
            role_ids=role_picker_info['role_ids'], max_row_length=role_picker_info['max_row_length'], message_data=role_picker_info['message_data'])
    return role_pickers


async def set_role_picker_db(role_pickers: dict):
    """
    :param role_pickers: A dict containing RolePickerInfo objects you want to go in the db. It's important to make sure
                         you're putting in the FULL db dict, like what you'd get from get_role_picker_db, but with any
                         changes you want made.
    """
    role_picker_keys = await get_role_picker_ids()
    for key in role_picker_keys:  # First, we'll kill any role pickers that were removed
        if key not in role_pickers:
            await db_role_pickers.delete_one({"_id": key})
    for key, role_picker_info in role_pickers.items():  # Then we again need to unpack the dataclass objects into dicts
        document = {
            '_id': key, 'channel_id': role_picker_info.channel_id, 'embed_name': role_picker_info.embed_name, 'embed_desc': role_picker_info.embed_desc,
            'role_ids': role_picker_info.role_ids, 'max_row_length': role_picker_info.max_row_length, 'message_data': role_picker_info.message_data
        }
        if key in role_picker_keys:  # Then slot them back in the db, either updating them...
            await db_role_pickers.replace_one({"_id": key}, document)
        else:  # Or inserting new ones
            await db_role_pickers.insert_one(document)


async def get_role_picker_ids():
    role_picker_db = await db_role_pickers.find().to_list(1000)
    return [role_picker_info['_id'] for role_picker_info in role_picker_db]


async def add_role_picker_msg(key: str, channel: int, message: int):
    """
    :param key: The key or ID of the role picker object you're editing
    :param channel: The channel ID of the message being set
    :param message: The message ID of the message being set
    """
    document = await db_role_pickers.find_one({"_id": key})
    document["message_data"] = {'channel_id': channel, 'message_id': message}
    await db_role_pickers.replace_one({"_id": key}, document)


async def remove_role_picker_msg(key: str):
    """
    :param key: The key or ID of the role picker object you're editing
    """
    document = await db_role_pickers.find_one({"_id": key})
    document["message_data"] = {'channel_id': 0, 'message_id': 0}
    await db_role_pickers.replace_one({"_id": key}, document)
