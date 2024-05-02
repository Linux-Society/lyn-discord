import datetime
import logging
import random
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict

import discord
import discord.ext.commands as ext
from discord.ext.commands import Context

from client import LynBotClient, LynCogStuff


class OneTimePassword:
    def __init__(self, password: str, expiry: float) -> None:
        self.password = password
        self.expiry = expiry


class VerifyCacheEntry:
    def __init__(self, otp: OneTimePassword, zid: str, extra_data: Dict[any, any]):
        self.otp = otp
        self.zid = zid
        self.extra_data = extra_data


def generate_one_time_password(char_pool: str, length: int, expire_time: float) -> OneTimePassword:
    """
    Generates a one time password for a user of a certain length

    :param char_pool: The pool of characters to pull the one time password from
    :param length: Length of the one time password
    :param expire_time: The amount of time (in seconds) after the current timestamp of which this password should expire
    :return: The one time password
    """

    password = ""

    for i in range(1, length + 1):
        password += str(char_pool[random.randrange(0, len(char_pool) - 1)])

    expiry = time.time() + expire_time

    return OneTimePassword(password, expiry)
        

class VerifyInputZidModal(discord.ui.Modal):
    def __init__(self, ext: LynCogStuff) -> None:
        self.ext = ext
        self.client = ext.client

        title = self.ext.get_lyn_ext_var("enter_info_modal_title")
        super().__init__(title=title)

        label = self.ext.get_lyn_ext_var("enter_zid_modal_label")
        min_length = self.ext.get_lyn_ext_var("zid_length_min")
        max_length = self.ext.get_lyn_ext_var("zid_length_max")
        self.add_item(discord.ui.InputText(label=label, min_length=min_length, max_length=max_length, placeholder="zXXXXXXX"))

        for input in self.ext.get_lyn_ext_var("enter_info_modal_prompts"):
            self.add_item(input)

    async def callback(self, interaction: discord.Interaction) -> None:
        """
        The callback from when a user has inputted data into the zid modal.

        :param interaction: The interaction recieved from the modal
        :return:
        """
        children = self.children
        inputted_data = {}

        # Get all the data inputted into every text box
        for child in self.children:
            inputted_data[child.custom_id] = child.value

        # Get specifically the zid that the user inputted
        entered_value = self.children[0].value

        # Queue the one time password email to their zid
        await self.ext.send_otp_mail_zid(interaction, entered_value, inputted_data)

        # Get the timestamp/zid etc. for formatting the message to send to the user
        zid = entered_value
        next_timestamp = self.client.send_lyn_mail.next_iteration.replace(tzinfo=datetime.timezone.utc).timestamp()

        # Send the followup message
        user_email = self.ext.get_lyn_ext_var("verify_mail_zid_base").format(zid=zid)
        embed = self.ext.mail_sent_embed(email=user_email, timestamp=int(next_timestamp))
        await interaction.response.send_message(self.ext.get_lyn_ext_var("verify_helpful_eph_msg"), ephemeral=True)
        await interaction.user.send(embed=embed)


class VerifyInputCodeModal(discord.ui.Modal):
    def __init__(self, ext: LynCogStuff) -> None:
        self.ext = ext
        self.client = ext.client

        title = self.ext.get_lyn_ext_var("enter_code_modal_title")
        super().__init__(title=title)

        label = self.ext.get_lyn_ext_var("enter_code_modal_label")
        self.add_item(discord.ui.InputText(label=label, style=discord.InputTextStyle.long))

    async def verify_user_unsw(self, interaction: discord.Interaction, verify_cache_entry: VerifyCacheEntry) -> None:
        await interaction.response.defer()
        embed = discord.Embed(
            colour=self.ext.get_lyn_ext_var("verify_colour"),
            title=self.ext.get_lyn_ext_var("verify_success_title"),
            description=self.ext.get_lyn_ext_var("verify_success_content")
        )

        zid = verify_cache_entry.zid
        await self.client.insert_zid_data(zid, interaction, verify_cache_entry.extra_data)

        # Grant the user the roles
        verify_grant_roles = self.ext.get_lyn_ext_var("verify_grant_role")

        verify_grant_reason = self.ext.get_lyn_ext_var("verify_grant_audit_reason") \
            .format(zid=zid)

        await interaction.user.add_roles(*verify_grant_roles, reason=verify_grant_reason, atomic=True)
        # Clear the user's code as they've already used it
        del self.client.verify_cache[interaction.user.id]

        await interaction.user.send(embed=embed)
        return

    async def callback(self, interaction: discord.Interaction) -> None:
        """
        The callback from when a user has inputted data into the verification code modal

        :param interaction: The interaction recieved from the modal
        :return:
        """
        
        if interaction.user.id in self.client.verify_cache:

            verify_cache_entry: VerifyCacheEntry = self.client.verify_cache[interaction.user.id]
            verify_otp = verify_cache_entry.otp

            # Check that the code is not expired
            if (time.time() - verify_otp.expiry) <= 0:
                # Check that the passwords match
                if str(self.children[0].value) == str(verify_otp.password):
                    await self.verify_user_unsw(interaction, verify_cache_entry)
                    return
                else:
                    print(f"Failed to verify user with password {self.children[0].value} which should be {verify_otp.password}")

        embed = self.ext.err_invalid_code()
        await interaction.response.defer()
        await interaction.user.send(embed=embed)


class VerifyView(discord.ui.View):
    def __init__(self, ext: LynCogStuff) -> None:
        super().__init__(timeout=None)

        self.ext = ext
        self.client = ext.client
        button_one_settings = self.ext.get_lyn_ext_var("verify_button_initial")
        button_two_settings = self.ext.get_lyn_ext_var("verify_button_finish")

        # Set the button's from the variables
        self.children[0].style = button_one_settings[1]
        self.children[0].label = button_one_settings[0]
        self.children[0].emoji = button_one_settings[2]

        self.children[1].style = button_two_settings[1]
        self.children[1].label = button_two_settings[0]
        self.children[1].emoji = button_two_settings[2]

    @discord.ui.button(custom_id="verify_view:initial")
    async def initial_verify_button(self, button: discord.ui.button, interaction: discord.Interaction) -> None:
        """
        The verification button of which sends an email to a users zid

        :param button: This button
        :param interaction: The users interaction with the button
        """

        input_zid_modal = VerifyInputZidModal(self.ext)
        await interaction.response.send_modal(input_zid_modal)

    @discord.ui.button(custom_id="verify_view:finish")
    async def finish_verify_button(self, button: discord.ui.button, interaction: discord.Interaction) -> None:
        """
        The verification button of which receives a code from a user to verify them

        :param button: This button
        :param interaction: The users interaction with the button
        """

        input_code_modal = VerifyInputCodeModal(self.ext)
        await interaction.response.send_modal(input_code_modal)


class Verify(LynCogStuff):

    def verification_embed(self) -> discord.Embed:
        """
        Returns the main verification embed for the verification system

        :return: The verification embed
        """

        verification_embed = discord.Embed(
            colour=self.get_lyn_ext_var("verify_colour"),
            title=self.get_lyn_ext_var("verify_setup_title"),
            description=self.get_lyn_ext_var("verify_setup_content")
        )

        return verification_embed

    def mail_sent_embed(self, email: str, timestamp: int) -> discord.Embed:
        """
        Returns the mail sent notification embed

        :param email: The email of which the mail was sent to
        :param timestamp: The timestamp of which the task for sending mails will be sent at (next one)
        :return: The mail sent notification embed
        """

        mail_sent_description = self.get_lyn_ext_var("sent_mail_content") \
            .format(email=email, timestamp=timestamp)

        mail_sent_embed = discord.Embed(
            colour=self.get_lyn_ext_var("verify_colour"),
            title=self.get_lyn_ext_var("sent_mail_title"),
            description=mail_sent_description
        )

        return mail_sent_embed

    def err_non_guild(self) -> discord.Embed:
        """
        Returns the error embed for if the verification command was not invoked from a guild

        :return: The error embed
        """

        error_embed = discord.Embed(
            colour=self.get_lyn_ext_var("verify_colour"),
            title=self.get_lyn_ext_var("verify_setup_err_title"),
            description=self.get_lyn_ext_var("verify_err_non_guild_content")
        )

        return error_embed

    def err_invalid_code(self) -> discord.Embed:
        """
        Returns the error embed which is sent to a suer when they have inputted the incorrect verification code

        :return: The error embed
        """

        error_embed = discord.Embed(
            colour=self.get_lyn_ext_var("verify_colour"),
            title=self.get_lyn_ext_var("verify_invalid_err_title"),
            description=self.get_lyn_ext_var("verify_err_invalid_verif_code")
        )

        return error_embed

    @ext.command(name='verifysetup')
    async def setup_verification(self, context: Context) -> None:
        """
        The setup verification command for lyn which sends the view for a server of which members can use to "verify"
        themselves.

        :param context: The context of the place where the command was invoked
        """

        # Check the command was invoked in a guild
        if context.guild is None:
            # Send an error message as the command was not invoked in a guild
            embed = self.err_non_guild()
            await context.send(embed=embed)
            return

        # Check if the user has the permission to actually run this command now
        if context.author.id not in self.get_lyn_ext_var("allowed_setup_users"):
            logging.debug(f"User: {context.author.name} failed to run verify setup due to "
                          f"lacking permissions.")
            return

        # Send the verification embed
        verification_embed = self.verification_embed()
        verification_view = VerifyView(self)

        await context.send(embed=verification_embed, view=verification_view)

    async def send_otp_mail_zid(self, interaction: discord.Interaction, zid: str, extra_data: Dict[any, any]) -> None:
        """
        Sends a one time password as a response to an interaction from their zid
        * this doesn't actually count as a response on discords end

        :param interaction: The interaction
        :param zid: The zid to send the email to
        :return:
        """

        otp = generate_one_time_password(
            self.get_lyn_ext_var("otp_char_pool"),
            self.get_lyn_ext_var("otp_length"),
            self.get_lyn_ext_var("otp_expire_time")
        )

        # Set otp for this user
        verify_cache_entry = VerifyCacheEntry(otp, zid, extra_data)
        self.client.verify_cache[interaction.user.id] = verify_cache_entry

        msg = MIMEMultipart('alternative')
        msg['Subject'] = self.get_lyn_ext_var("verify_mail_subject") \
            .format(zid=zid, code=otp.password, username=interaction.user.name, user_id=interaction.user.id,
                    server_name=interaction.guild.name
                    )
        msg['From'] = self.get_lyn_ext_var("verify_mail_from")
        msg['To'] = self.get_lyn_ext_var("verify_mail_zid_base").format(zid=zid)

        text = self.get_lyn_ext_var("verify_mail_text_content") \
            .format(zid=zid, code=otp.password, username=interaction.user.name, user_id=interaction.user.id,
                    server_name=interaction.guild.name
                    )

        html = self.get_lyn_ext_var("verify_mail_html_content") \
            .format(zid=zid, code=otp.password, username=interaction.user.name, user_id=interaction.user.id,
                    server_name=interaction.guild.name
                    )

        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')

        msg.attach(part1)
        msg.attach(part2)

        await self.client.add_to_mail(msg)


def setup(client: LynBotClient) -> None:
    """
    Adds the extension in this file to Lyn

    :param client: The instance of lyn to add the extension to
    :return:
    """

    this_ext = Verify(client, "lynext.verify")

    # Default extension variables
    this_ext.set_lyn_ext_var_def("otp_expire_time", 1800)
    this_ext.set_lyn_ext_var_def("otp_length", 12)
    this_ext.set_lyn_ext_var_def("otp_char_pool", "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    this_ext.set_lyn_ext_var_def("allowed_setup_users", [])
    this_ext.set_lyn_ext_var_def("verify_grant_role", None)
    this_ext.set_lyn_ext_var_def("verify_colour", discord.Colour.from_rgb(245, 190, 4))
    this_ext.set_lyn_ext_var_def("verify_setup_err_title", "Error")
    this_ext.set_lyn_ext_var_def("verify_invalid_err_title", "Invalid Code")
    this_ext.set_lyn_ext_var_def("verify_err_non_guild_content",
                                 "Please only run the setup verification command in guilds")
    this_ext.set_lyn_ext_var_def("verify_setup_title", "Verification")
    this_ext.set_lyn_ext_var_def("verify_success_title", "Verification Successful")
    this_ext.set_lyn_ext_var_def("verify_success_content", "You have successfully verified yourself for this server")
    this_ext.set_lyn_ext_var_def("verify_grant_audit_reason", "Granted to this member through verification")
    this_ext.set_lyn_ext_var_def("verify_setup_content", "Verify yourself to enter this server")
    this_ext.set_lyn_ext_var_def("verify_button_initial", ("Get code", discord.ButtonStyle.grey, "🔒"))
    this_ext.set_lyn_ext_var_def("verify_button_finish", ("Enter code", discord.ButtonStyle.grey, "🎫"))
    this_ext.set_lyn_ext_var_def("enter_zid_modal_label", "Enter your zID (including the z)")
    this_ext.set_lyn_ext_var_def("zid_length_min", 8)
    this_ext.set_lyn_ext_var_def("zid_length_max", 8)
    this_ext.set_lyn_ext_var_def("sent_mail_title", "Check your mailbox")
    this_ext.set_lyn_ext_var_def("sent_mail_content", "This will take a while so please be patient")
    this_ext.set_lyn_ext_var_def("enter_code_modal_title", "Verify yourself")
    this_ext.set_lyn_ext_var_def("enter_code_modal_label", "Enter your verification code")
    this_ext.set_lyn_ext_var_def("verify_err_invalid_verif_code",
                                 "Your verification code is invalid! please try again.")
    this_ext.set_lyn_ext_var_def("verify_mail_subject",
                                 "Verify yourself")
    this_ext.set_lyn_ext_var_def("verify_mail_from",
                                 "Verification bot")
    this_ext.set_lyn_ext_var_def("verify_mail_text_content",
                                 "Verify yourself please")
    this_ext.set_lyn_ext_var_def("verify_mail_html_content",
                                 "Verify yourself")
    this_ext.set_lyn_ext_var_def("verify_mail_zid_base",
                                 "{zid}@ad.unsw.edu.au")
    this_ext.set_lyn_ext_var_def("verify_helpful_eph_msg",
                                 "Please check your DM's")
    this_ext.set_lyn_ext_var_def("enter_info_modal_title", "Enter some information about yourself")
    this_ext.set_lyn_ext_var_def("enter_info_modal_prompts", [discord.ui.InputText(label="Whats your favourite linux distro/s?", custom_id="fave_distro", placeholder="Arch", required=True, style=discord.InputTextStyle.long)])
    this_ext.print_ext_var_debug()

    client.add_persistent_view_to_ext(VerifyView, this_ext)

    client.add_cog(this_ext)

