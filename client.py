import logging
import os
from abc import ABC
from email.mime.multipart import MIMEMultipart
from typing import Iterable, Dict, Any, List, Type
import time

import discord
import discord.ext.commands as ext
from discord.ext import tasks
from motor.motor_asyncio import AsyncIOMotorClient
from aiosmtplib import SMTP

from cryptography.fernet import Fernet

key = b"REDACTED"
fernet = Fernet(key)


def mentioned_prefix(
    discord_bot: discord.AutoShardedBot, _message: discord.Message
) -> Iterable[str]:
    """
    Returns the prefix used by the discord bot

    :param discord_bot: The bot instance from discord
    :param _message: The message (irrelevant to the prefix)
    :return: The prefix of the bot which is from mentions
    """

    discord_bot_id: int = discord_bot.user.id
    return [f"<@{discord_bot_id}>", f"<@!{discord_bot_id}"]


def start_motor_client(database_uri: str) -> AsyncIOMotorClient:
    """
    Starts the database client (mongodb) for Lyn to be used later

    :param database_uri: The uri pointing to the database
    :return: The client connected to the database
    """

    return AsyncIOMotorClient(database_uri)


def start_smtp_client(hostname: str, username: str, password: str) -> SMTP:
    """
    Starts the smtp client for lyn to send verification emails

    :param hostname: The hostname to connect the smtp client to
    :param username: The username of the lyn email
    :param password: The app password/password to the lyn email
    :return: The smtp client, not connected though
    """

    smtp_client = SMTP(hostname=hostname, username=username, password=password, timeout=10, port=587)

    return smtp_client


class LynBotClient(ext.AutoShardedBot, ABC):
    """
    Main class representing the client behind Lyn.
    """

    def __init__(self) -> None:
        super().__init__(
            command_prefix=mentioned_prefix,
            case_insensitive=True,
            intents=discord.Intents.default(),
            strip_after_prefix=True,
        )

        # Persistent view stuff
        self.persistent_views_base = []
        self.persistent_views_added = False

        # Motor mongodb database initialisation
        self.motor_client = start_motor_client(
            fernet.decrypt(os.environ.get("MONGODB_URI").encode()).decode()
        )
        self.verification_database = self.motor_client["lyn"]["verify"]

        # Smtp stuff
        self.smtp_client = start_smtp_client(
            "smtp.gmail.com",
            fernet.decrypt(os.environ.get("GMAIL_USER").encode()).decode(),
            fernet.decrypt(os.environ.get("GMAIL_APP_PASS").encode()).decode(),
        )
        self.mail = []
        self.send_lyn_mail.start()

        # Verification cache for OTPs
        self.verify_cache = {}

        # Things for the current status of Lyn
        self.current_status = 0
        self.lyn_statuses = []
        self.set_lyn_status.start()

        # Lyn extensions
        self.lyn_extensions = []
        self.lyn_ext_vars: Dict[str, Dict[str, Any]] = {}
        self.lyn_ext_var_accepted: Dict[str, List[str]] = {}

    def add_persistent_view_to_ext(self, view: Type[discord.ui.View], ext) -> None:
        """
        Adds a persistent view to be registered for an extension

        :param view: The persistent view
        :param ext: The extension that this view belongs to
        """

        self.persistent_views_base.append((view, ext))

    async def on_ready(self) -> None:
        """
        On ready call from when lyn is ready
        """

        if not self.persistent_views_added:
            for view_to_add in self.persistent_views_base:
                self.add_view(view_to_add[0](view_to_add[1]))

            self.persistent_views_added = True

    async def add_to_mail(self, mail: MIMEMultipart) -> None:
        """
        Adds a multipart mail to the queue of mails to send

        :param mail: The mail to add
        """

        self.mail.append(mail)

    @tasks.loop(seconds=30)
    async def send_lyn_mail(self) -> None:
        """
        Sends mail through lyns SMTP client from the current mail queue
        """

        if len(self.mail) > 0:
            async with self.smtp_client:
                for i in range(0, len(self.mail)):
                    logging.debug(f"Sending mail to: {self.mail[i]['To']}")

                    await self.smtp_client.send_message(self.mail[i])

                    logging.debug(f"Sent mail to: {self.mail[i]['To']}")

        self.mail.clear()

    def add_lyn_ext(self, ext: str) -> None:
        """
        Adds a new extension to be loaded by lyn when ran

        :param ext: The extension to add
        """

        self.lyn_extensions.append(ext)
        self.lyn_ext_vars[ext] = {}

    def set_lyn_ext_var(self, ext: str, var: str, value: Any) -> None:
        """
        Sets a variable to the lyn extension variables

        :param ext: The extension to set the variable for
        :param var: The variable name
        :param value: The value of the variable
        """

        self.lyn_ext_vars[ext][var] = value

    def set_lyn_ext_var_def(self, ext: str, var: str, value: Any) -> None:
        """
        Sets a variable to the lyn extension variables if it does not already exist

        :param ext: The extension to set the variable for
        :param var: The variable name
        :param value: The value of the variable
        """

        if var not in self.lyn_ext_vars[ext]:
            self.set_lyn_ext_var(ext, var, value)

        if ext not in self.lyn_ext_var_accepted:
            self.lyn_ext_var_accepted[ext] = []

        self.lyn_ext_var_accepted[ext].append(var)

    def add_lyn_status(self, status: str) -> None:
        """
        Adds a new status to lyn for displaying (rotates every 60 seconcds)

        :param status: The status to add.
        """

        self.lyn_statuses.append(status)

    async def insert_zid_data(
        self, zid: str, interaction: discord.Interaction, extra_data: Dict[any, any]
    ) -> None:
        """
        Inserts the zid & interaction data about the associated user into the database

        :param zid: The zid of the user
        :param interaction: The interaction which caused this insertion
        """

        # The data to be inserted for this user as part of their entry in the database
        data = {
            "zid": zid,
            "discord_name": interaction.user.name,
            "verif_timestamp": str(time.time()),
            "extra_data": extra_data,
        }

        await self.insert_data(interaction.user.id, data)

    async def insert_data(self, snowflake: int, data: Dict[Any, Any]) -> None:
        """
        Inserts information related to a member into the verification database

        :param data: The data associated to the member
        :param snowflake: The snowflake of the member
        """

        verify_data = {"snowflake": str(snowflake), "data": data}

        await self.verification_database.insert_one(verify_data)

    @tasks.loop(seconds=60)
    async def set_lyn_status(self) -> None:
        """
        Sets the status for lyn every 60 seconds.
        """

        await self.wait_until_ready()

        # Get the next status and update the status of lyn
        next_status = self.get_next_status()
        activity = discord.CustomActivity(next_status)

        await self.change_presence(activity=activity, status=discord.Status.idle)

    def get_next_status(self) -> str:
        """
        Retrieves the next status in the list of lyn statuses, pushing it back to the end of the "queue"

        :return: The status, if there are no statuses then this function will return an empty string
        """

        # Safeguard
        if len(self.lyn_statuses) == 0:
            return ""

        # Reset rewind
        if self.current_status == len(self.lyn_statuses) - 1:
            self.current_status = 0

        else:
            self.current_status += 1

        # Get the current status
        return self.lyn_statuses[self.current_status]

    def load_lyn_ext(self) -> None:
        """
        Loads all the provided extensions to lyn

        :return:
        """

        for extension in self.lyn_extensions:
            print(f"Loaded Extension: {self.load_extension(f'{extension}')[0]}\n")

    def run_lyn(self) -> None:
        """
        Bringeth thy lyn to life !!
        """

        self.load_lyn_ext()

        token = fernet.decrypt(os.environ.get("LYN_TOKEN").encode()).decode()
        self.run(token)


class LynCogStuff(ext.Cog):
    def __init__(self, client: LynBotClient = None, ext_name: str = "") -> None:
        self.client: LynBotClient = client
        self.ext_name: str = ext_name

    def set_lyn_ext_var_def(self, var: str, value: Any) -> None:
        """
        Sets a default variable for this extension

        :param var: The variable "name"
        :param value: Its associated default value
        """

        self.client.set_lyn_ext_var_def(self.ext_name, var, value)

    def get_lyn_ext_var(self, var: str) -> Any:
        """
        Gets the associated variable's value for this extension

        :param var: The variable to get the value for
        :return: The value
        """

        return self.client.lyn_ext_vars[self.ext_name][var]

    def print_ext_var_debug(self) -> None:
        """
        Prints a debug statement about the variables for this extension
        """

        logging.debug(f"Extension {self.ext_name} variables:")

        for var in self.client.lyn_ext_vars[self.ext_name]:
            logging.debug(f"{var}: {self.get_lyn_ext_var(var)}")

        logging.debug(f"Accepted variables: {self.client.lyn_ext_var_accepted[self.ext_name]}\n")
