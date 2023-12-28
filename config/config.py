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

koala_city_id = 991518170542260336


mongo_url = os.environ.get("MONGO_URL", "mongodb://mongo/")

activity_text = "version numbering is for foolish fools who foolishly accept the foolishness of a fool's fool"
command_prefixes = ['!']

# Roles
ccgse_notif_role = 996963548959871069
minecraft_notif_role = 1007714356189991083
club_notif_role = 1007714385642393655
top_non_custom_role = 993590393146978419
admin_roles = [991519286642352138, 1189762451483398144]

# Channels
ccgse_channel = 993962449717960836
minecraft_channel = 1009699321651925022
club_channel = 991544912556339241
roles_channel = 1066176296280924190
starboard_channel = 991550133869223937
starboard_allowed_channels = [991523087348662373, 991544337747951617, 991518171729231924]

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
    "cogs.roles",
    "cogs.notifications",
    "cogs.role_picker",
    "cogs.starboard",
]

magicball_answers = [
    "It is certain.", "It is decidedly so.", "Without a doubt.", "Yes, definitely.", "You may rely on it.",
    "As I see it, yes.", "Most likely.", "Outlook: Good.", "Yes.", "Signs point to yes.", "Reply hazy, try again.",
    "Ask again later.", "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.",
    "Don't count on it.", "My reply is no.", "My sources say no.", "Outlook: Not so good.", "Very doubtful.",
    "You are unworthy of an answer. Consult <@1164760702301519944> for further instruction.",
]

default_role_picker_info = {}
