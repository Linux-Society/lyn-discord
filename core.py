import logging

import discord

from client import LynBotClient

logging.basicConfig(level=logging.DEBUG)

import platform

client = LynBotClient()
client.add_lyn_status(f"Running {platform.platform()}")
client.add_lyn_status("lyn@linuxsociety")
client.add_lyn_ext("lynext.verify")
client.add_lyn_ext("lynext.export")

# Modify these "variables" to modify the functionality of the verify extension without having to modify the actual
# code Removing the setting of a variable will result it in returning to its default value as set in the setup
# function for an extension.

# The expiry time of the one time password from its creation in seconds (float/int)
client.set_lyn_ext_var("lynext.verify", "otp_expire_time", 1800)

# The length of the one time password generated in characters (int)
client.set_lyn_ext_var("lynext.verify", "otp_length", 42)

# The pool of characters to pull from to create the one time password (str)
client.set_lyn_ext_var(
    "lynext.verify", "otp_char_pool", "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
)

# This variable accepts a key of guild id's of which the value is list of user id's, when the verify setup command is
# run in a guild, the list of user id's will be used to determine if to continue with the verify setup or whether to
# return silently (Dict[guild id, List[user id]])
client.set_lyn_ext_var(
    "lynext.verify", "allowed_setup_users",
        # stellaurora
        [237465974545055744]
)

# this variable accepts a list of user id's which have whitelist permission
client.set_lyn_ext_var(
    "lynext.export", "export_whitelist",
    [227018516497170433, 237465974545055744, 389354203883241494, 1072881649580265482, 286027626936664066]
)

# Accepts a list of discord.Objects, or just a singular discord.Object representing the roles to grant to a user upon verification 
client.set_lyn_ext_var(
    "lynext.verify", "verify_grant_role",
        # "Verified"
        [discord.Object(1147938807035990016), discord.Object(1163334586789527683)]
)

# The colour for all embeds associated with the lynext.verify extension (discord.Colour)
client.set_lyn_ext_var(
    "lynext.verify", "verify_colour", discord.Colour.from_rgb(245, 190, 4)
)

# The title of all verifysetup error embeds in the lynext.verify extension (string)
client.set_lyn_ext_var(
    "lynext.verify", "verify_setup_err_title",
    "<:tux:1132503295315955752> Error in Verification Setup <:tux:1132503295315955752>"
)

# The title of the invalid verification code error embed (string)
client.set_lyn_ext_var(
    "lynext.verify", "verify_invalid_err_title",
    "<:tux:1132503295315955752> Your verification code is invalid <:tux:1132503295315955752>"
)

# The content of the error embed in the non_guild error. (string)
client.set_lyn_ext_var(
    "lynext.verify", "verify_err_non_guild_content",
    "\u200b\n➔ **Here's the reason why:**\n"
    ">>> You cannot run the verification setup outside of a guild, Please run the command in a guild for it to function"
)

# The title of the actual verification embed (string)
client.set_lyn_ext_var(
    "lynext.verify", "verify_setup_title",
    "<:tux:1132503295315955752> Verification <:tux:1132503295315955752>"
)

# The content of the verification embed (string)
client.set_lyn_ext_var(
    "lynext.verify", "verify_setup_content",
    "❁ ➔ **Please verify yourself**\n"
    ">>> In order to gain access to the server please verify yourself by verifying your zID through email.\n\n"
    " 1. Press get code and enter zid\n"
    " 2. Check your email for a code, check spam folder too\n"
    " 3. Press Enter code button and put in the code from the email\n"
    " 4. Congratulations you’re verified!\n\n"
    "If you have any feedback or issues regarding the verification process\n"
    "[Visit this form here](https://docs.google.com/forms/d/e/1FAIpQLScvqcvp1ymFoq1VRAS2yIVUr_MNRB9WP9wzIwDQz63S8pEmwQ/viewform?usp=sf_link)"
)

# Set details about the initial verification button, the button which recieves the zid from the user & sends an email.
#
# The format for this variable is the first element of the tuple is the label of the button, the second is the style and
# the third is the associated emoji string. (string, discord.ButtonStyle, string)
client.set_lyn_ext_var(
    "lynext.verify", "verify_button_initial", ("Get code", discord.ButtonStyle.grey, "🔒")
)

client.set_lyn_ext_var(
    "lynext.verify", "verify_button_finish", ("Enter code", discord.ButtonStyle.grey, "🔐")
)

# The title for the modal which requests for the user's zID (string)
client.set_lyn_ext_var(
    "lynext.verify", "enter_zid_modal_title", "Verify yourself"
)

# The label above the enter zID text prompt on the zID request modal (string)
client.set_lyn_ext_var(
    "lynext.verify", "enter_zid_modal_label", "Enter your zID (including the z)"
)

# Min & maximum length of allowed input to zID request modal (should be length of ziD) (int)
client.set_lyn_ext_var(
    "lynext.verify", "zid_length_min", 8
)

client.set_lyn_ext_var(
    "lynext.verify", "zid_length_max", 8
)

# The title of the embed a user recieves when lyn sends an verification code
# email to them (string)
client.set_lyn_ext_var(
    "lynext.verify", "sent_mail_title",
    "<:tux:1132503295315955752> Check your Mailbox <:tux:1132503295315955752>"
)

# The content of the verification code email embed thats sent to notify the user (string)
# {email} - The email of which the code was sent to
# {timestamp} - The time left for the email sending task occurs
client.set_lyn_ext_var(
    "lynext.verify", "sent_mail_content",
    "\u200b\n❁ ➔ **We've sent you some mail**\n"
    "> Please check your email and enter the code you've received back into the prompt given by the "
    "second button in order to verify yourself as ``{email}``\n\u200b\n"
    "⚜ ➔ **Notes**\n"
    ">>> Your mail with the code will be sent <t:{timestamp}:R>, so please be patient and dont repeatedly spam the "
    "verification service.\n\n The mail will most likely appear in the spam/junk section. (if you are forwarding to a "
    "gmail account, it will probably appear in the main inbox on the forwarded account)\n\nRequesting a new code "
    "invalidates the previously requested code"
)

# The title for the modal which requests for the user's verification code & some info (string)
client.set_lyn_ext_var(
    "lynext.verify", "enter_code_modal_title", "Verify yourself"
)

# The label above the enter verification text prompt on the code request modal (string)
client.set_lyn_ext_var(
    "lynext.verify", "enter_code_modal_label", "Enter your verification code"
)

# The email of which verification code mails to zid users will be sent to (string)
# {zid} - The zid of which was entered
client.set_lyn_ext_var(
    "lynext.verify", "verify_mail_zid_base", "{zid}@ad.unsw.edu.au"
)

# The label above the enter verification text prompt on the code request modal (string)
client.set_lyn_ext_var(
    "lynext.verify", "verify_err_invalid_verif_code",
    "\u200b\nⓧ ➔ **Your verification code was invalid!**\n"
    "> You've either entered your code incorrectly, or it has expired! Please try entering it again, "
    "if you encounter any difficulties or have a grievance about the verification "
    "process please [submit a grievance]("
    "https://docs.google.com/forms/d/e/1FAIpQLSdbROH4_C8ccMnqNLqN_LOAChte5OLXkI_vGFw688gavgZWfg/viewform) or contact "
    "an executive\n\u200b\n"
    "❃ ➔ **Please be patient**\n"
    ">>> Please wait a while before you request for a new verification code, note that receiving a new code will take a"
    " few minutes before it appears, along with the fact that it'll probably appear in the spam section."
)

# The title of the successful verification embed sent to the user (string)
client.set_lyn_ext_var(
    "lynext.verify", "verify_success_title", "<:tux:1132503295315955752> Verification Successful "
                                             "<:tux:1132503295315955752>"
)

# The content of the successful verification embed sent to the user (string)
client.set_lyn_ext_var(
    "lynext.verify", "verify_success_content", "> Welcome to the server!, Please follow the rules"
)

# The audit log reason as to why the roles which were added to the user were added (string)
# {zid} - zID which the member verified as
client.set_lyn_ext_var(
    "lynext.verify", "verify_grant_audit_reason", "Granted to this member through verification as {zid}"
)

# The subject of the verification mail that will be sent to the user (string)
# {zid} - zID of mail recipient
# {username} - username of the person who requested verification for this zid
# {user_id} - the user id of the person who requested verification for this zid
# {sever_name} - The name of the server of which this verification was requested from (basically just linux society ngl)
# {code} - verification code
client.set_lyn_ext_var(
    "lynext.verify", "verify_mail_subject", 'Linux Society Verification code for {username}'
)

# The name of which the verification mail that will be sent to the user will have come from (string)
client.set_lyn_ext_var(
    "lynext.verify", "verify_mail_from", "UNSW Linux Society"
)

# The text content of the verification mail (string)
# {zid} - zID of mail recipient
# {username} - username of the person who requested verification for this zid
# {user_id} - the user id of the person who requested verification for this zid
# {sever_name} - The name of the server of which this verification was requested from (basically just linux society ngl)
# {code} - verification code
client.set_lyn_ext_var(
    "lynext.verify", "verify_mail_text_content",

    'Hey there, {username}\n\nTo verify yourself as {zid} in {server_name} please use this code:\n'
    '\n{code}\n\nThis message was sent to you by the Linux Society at the University of New South Wales.'
)

# The html content of the verification mail (string)
# {zid} - zID of mail recipient
# {username} - username of the person who requested verification for this zid
# {user_id} - the user id of the person who requested verification for this zid
# {sever_name} - The name of the server of which this verification was requested from (basically just linux society ngl)
# {code} - verification code
client.set_lyn_ext_var(
    "lynext.verify", "verify_mail_html_content",
    """
    <!DOCTYPE html>
    <html>
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse; padding:0; margin:0px;">
        <tr valign="top">
            <td align="center">
                <h3>Hey there, {username}</h3>
                <p>To verify yourself as {zid} in {server_name} please use this code:</p>
                <h4>{code}</h4><br/><br/>
                <p>This message was sent to you by the Linux Society at the University of New South Wales.</p>
            </td>
        </tr>
    </table>
    </html>
    """

)

client.set_lyn_ext_var(
    "lynext.verify", "verify_helpful_eph_msg",
    "**<:tux:1132503295315955752> Please check your DM's for information! <:tux:1132503295315955752>**"
)

client.set_lyn_ext_var(
    "lynext.verify", "enter_info_modal_prompts", 
    [
        discord.ui.InputText(label="What's your full name?", custom_id="person_name", placeholder="Linus Torvalds", required=True, style=discord.InputTextStyle.short),
        discord.ui.InputText(label="What's your fave linux distro? (optional)", custom_id="fave_distro", placeholder="Arch, ArcoLinux, ChimeraOS, EndeavourOS, Manjaro, Garuda Linux", required=False, style=discord.InputTextStyle.long),
        discord.ui.InputText(label="What's your year & degree? (optional)", custom_id="year_degree", placeholder="First year, Bachelor of Advanced Computer Science (Honours)", required=False, style=discord.InputTextStyle.long),
    ]
)

client.set_lyn_ext_var(
    "lynext.export", "export_keys", 
    ["verif_timestamp", "person_name", "zid", "discord_name", "snowflake", "fave_distro", "year_degree", False]
)

client.set_lyn_ext_var(
    "lynext.export", "export_column_names",
    "Verification Timestamp,Full Name,zID,Discord Username,Discord Snowflake,Favourite distribution,Year & Degree,Reviewed"
)
  

client.run_lyn()

    