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
import io

from client import LynBotClient, LynCogStuff

class Export(LynCogStuff):

    @ext.command(name='exportverify')
    async def setup_verification(self, context: Context) -> None:
        """
        Exports all the verification information in a parsable CSV format for google sheets

        :param context: The context of the place of which this command was executed
        """

        # Check if the user has the permission to actually run this command
        if context.author.id not in self.get_lyn_ext_var("export_whitelist"):
            logging.debug(f"User: {context.author.name} failed to run verify export due to "
                          f"lacking permissions.")
            return
        
        # This will be our compiled data string for export
        compiled_data = self.get_lyn_ext_var("export_column_names")
        keys = self.get_lyn_ext_var("export_keys")
        cursor = self.client.verification_database.find(batch_size=25)

        async for person in cursor:
            compiled_data += '\n'

            data_entry = {}
            self.add_to_data_entry(data_entry, person)

            for key in keys:

                string_value = ''

                try:
                    if isinstance(key, str):
                        string_value = data_entry[key]
                    elif isinstance(key, bool):
                        string_value = str(key).upper()
                except:
                    pass
                
                compiled_data += string_value + ','

            compiled_data = compiled_data[:-1]

        export_file = io.StringIO()
        export_file.write(compiled_data)
        export_file.seek(0)

        export_file = discord.File(export_file, filename=f"LynExport-{datetime.datetime.now().strftime('%D-%M-%Y_%H-%M-%S')}.csv")
        await context.send(file=export_file)
        
        
    def add_to_data_entry(self, data_entry: Dict[any, any], rest: Dict[any, any]):
        for key, value in rest.items():
            
            # Recursively go through if the value is a dict
            if isinstance(value, dict):
                self.add_to_data_entry(data_entry, value)
            
            else:
                data_entry[key] = value





def setup(client: LynBotClient) -> None:
    """
    Adds the extension in this file to Lyn

    :param client: The instance of lyn to add the extension to
    :return:
    """

    this_ext = Export(client, "lynext.export")

    this_ext.set_lyn_ext_var_def("export_whitelist", [])
    this_ext.set_lyn_ext_var_def("export_keys", ["zid"])
    this_ext.set_lyn_ext_var_def("export_column_names","zid")
    this_ext.print_ext_var_debug()

    client.add_cog(this_ext)
