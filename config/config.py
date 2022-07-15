from dotenv import load_dotenv
import os

load_dotenv()

_true = ["true", "True", "t", "T", "1", "yes", "Yes", "YES"]

guild_id = 991518170542260336

mongo_url = os.environ.get("MONGO_URL", "mongodb://mongo/")

activity_text = "hi hi :)"
command_prefixes = ['!']

remindme_ignore_words = ["this"]
remindme_remove_words = ["in", "and", "on", "at", "@"]

discord_token = os.environ.get("PRINCESS_TRIXIE_TOKEN")
bot_application_id = 925087331915022377
discord_cogs = [
    "cogs.reminders",
    "cogs.type",
]
