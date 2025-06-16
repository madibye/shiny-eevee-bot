import os
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv


@dataclass
class RolePickerInfo:
    channel_id: Optional[int] = 0
    embed_name: Optional[str] = "👋 Hey there! What are your pronouns?"
    embed_desc: Optional[str] = "Use the buttons below to select what pronouns you'd like us to display for you."
    role_ids: Optional[List[int]] = None
    max_row_length: Optional[int] = 5
    message_data: Optional[dict] = None

    def __post_init__(self):
        # We should instantiate a default list & dict for these two
        if not self.role_ids:
            self.role_ids = []
        if not self.message_data:
            self.message_data = {'channel_id': 0, 'message_id': 0}


load_dotenv()

_true = ["true", "True", "t", "T", "1", "yes", "Yes", "YES"]


mongo_url = os.environ.get("MONGO_URL", "mongodb://mongo/")

activity_text = "version numbering is for foolish fools who foolishly accept the foolishness of a fool's fool"
command_prefixes = ['!']

# Roles
madi_id = 188875600373481472
custom_role_allowed_servers = [1253961620711800873]

remindme_ignore_words = ["this"]
remindme_remove_words = ["in", "and", "on", "at", "@"]

# Live Config
scv_blocked = {}  # Stub in case we ever want to use this

discord_token = os.environ.get("PRINCESS_TRIXIE_TOKEN")
bot_application_id = 925087331915022377
discord_cogs = [
    "cogs.admin",
    "cogs.reminders",
    "cogs.fun",
    "cogs.threads",
    "cogs.role_picker",
    "cogs.roles",
]

magicball_answers = [
    "It is certain.", "It is decidedly so.", "Without a doubt.", "Yes, definitely.", "You may rely on it.",
    "As I see it, yes.", "Most likely.", "Outlook: Good.", "Yes.", "Signs point to yes.", "Reply hazy, try again.",
    "Ask again later.", "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.",
    "Don't count on it.", "My reply is no.", "My sources say no.", "Outlook: Not so good.", "Very doubtful.",
    "You are unworthy of an answer. Consult <@1164760702301519944> for further instruction.",
]

default_role_picker_info = {}
