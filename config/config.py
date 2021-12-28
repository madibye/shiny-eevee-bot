from dotenv import load_dotenv
import os

load_dotenv()

_true = ["true", "True", "t", "T", "1", "yes", "Yes", "YES"]

mongo_url = os.environ.get("MONGO_URL", "mongodb://mongo/")

activity_text = "hi hi :)"
command_prefixes = ['!']

remindme_ignore_words = ["this"]
remindme_remove_words = ["in", "and", "on", "at", "@"]

discord_token = "OTI1MDg3MzMxOTE1MDIyMzc3.YcoAtw.65ePrP26S6niILlnGv6tbzzR5bM"
discord_cogs = [
    "cogs.reminders",
    "cogs.type",
    "cogs.music",
]
