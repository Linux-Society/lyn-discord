import discord.ext.commands as ext
from discord.ext.commands import Context
import discord

from client import LynBotClient, LynCogStuff
import datetime

class TermDate(LynCogStuff):
    def __init__(self, client: LynBotClient, ext_name: str = "") -> None:
        super().__init__(client, ext_name)
        self.dates = self.set_term_dates(datetime.datetime.now().year)

    @discord.slash_command(name='tw')
    async def printTermWeek(self, ctx: discord.ApplicationContext) -> None:
        """
        Prints the current term week
        No args
        """
        try:
            current_date = datetime.datetime.now()

            # Determine which term the current date falls in
            current_term = self.determine_current_term()

            if current_term is None:
                await ctx.respond("It's the holiday's right now (probably).")
                return

            # Get the start date of the current term
            term_start = datetime.datetime.strptime(self.dates[current_term]["firstDay"], '%a %b %d %Y')
            term_end = datetime.datetime.strptime(self.dates[current_term]["examFinish"], '%a %b %d %Y')

            # Ensure current date is within the term's date range
            if not (term_start <= current_date <= term_end):
                await ctx.respond(f"Bot Error: The current date somehow falls outside of the calculated term {current_term}.")
                return

            # Calculate the current week of the term
            delta = current_date - term_start
            current_week = (delta.days // 7) + 1  # Week number starts from 1, not 0

            await ctx.respond(f"We are currently in week {current_week} of {current_term}.")            

        except Exception as e:
            await ctx.respond(f"An error occurred: {str(e)}")



    @ext.command(name='td')
    async def printTermDate(self, ctx: Context, *args) -> None:
        """
        This is truly the printing of the term date of all time
        Takes a numerical week, string day, and optional term in the form of "T1" "T2" or "T3"
        Capitalisation and order of the args don't matter since we're cool like that
        """ 
        try:
            # Determine which argument is the week and which is the day, and if there's a specified term
            week, day, term = self.parse_args(args)

            if term:
                term = term.upper()
                if term not in ['T1', 'T2', 'T3']:
                    await ctx.send("Invalid term. Please specify T1, T2, or T3.")
                    return
            else:
                term = self.determine_current_term()

            if not term:
                await ctx.send("Could not determine the current term. Please check the term dates.")
                return

            # Get the corresponding term start date
            term_start = datetime.datetime.strptime(self.dates[term]["firstDay"], '%a %b %d %Y')
            term_end = datetime.datetime.strptime(self.dates[term]["examFinish"], '%a %b %d %Y')

            # Calculate the date
            result_date = term_start + datetime.timedelta(weeks=week - 1, days=day)

            # Guard against invalid term dates
            if result_date > term_end or result_date < term_start:
                await ctx.send(f"The calculated date {result_date.strftime('%A, %d %B %Y')} falls outside the range of {term}.")
                return

            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

            msg = f"The date for week {week}, {days[day]} is {result_date.strftime('%d %B %Y')} ({term})"
            await ctx.send(msg)
        
        except ValueError as e:
            await ctx.send(str(e))

    def set_term_dates(self, year):
        """
        Cooks up the term dates for the year.
        Assumes a term is 11 weeks with another 1 week and 3 days of exam
        """
        T1start = datetime.datetime(year, 2, 11)
        T1start += datetime.timedelta(days=(7 - T1start.weekday()) % 7)  # Get the Monday after Feb 11
        
        # Term 2/3 starts the Monday after 15 weeks from prev term start 
        # (10 weeks + 1 week stuvac + 2 weeks exams + 2 weeks holidays)       
        T2start = T1start + datetime.timedelta(weeks=15)
        T3start = T2start + datetime.timedelta(weeks=15)

        return {
            "T1": {
                "firstDay": T1start.strftime('%a %b %d %Y'),
                "examFinish": (T1start + datetime.timedelta(weeks=12, days=0)).strftime('%a %b %d %Y')
            },
            "T2": {
                "firstDay": T2start.strftime('%a %b %d %Y'),
                "examFinish": (T2start + datetime.timedelta(weeks=12, days=0)).strftime('%a %b %d %Y')
            },
            "T3": {
                "firstDay": T3start.strftime('%a %b %d %Y'),
                "examFinish": (T3start + datetime.timedelta(weeks=12, days=0)).strftime('%a %b %d %Y')
            }
        }

    def determine_current_term(self):
        """
        Determines which term (T1, T2, T3) the current date falls in.
        """
        current_date = datetime.datetime.now()

        for term in ['T1', 'T2', 'T3']:
            term_start = datetime.datetime.strptime(self.dates[term]["firstDay"], '%a %b %d %Y')
            term_end = datetime.datetime.strptime(self.dates[term]["examFinish"], '%a %b %d %Y')
            if term_start <= current_date <= term_end:
                return term
        
        return None
    
    def parse_args(self, args):
        """
        Parse the arguments, which can be in any order, to extract:
        - The week number
        - The day of the week
        - The optional term (T1, T2, T3)
        """
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        term = None
        week = None
        day = None

        for arg in args:
            arg = arg.lower()

            # Check if the argument is a valid week number
            if arg.isdigit():
                if week is None:
                    week = int(arg)
                else:
                    raise ValueError("Multiple week numbers found. Please provide only one week number.")
            
            # Check if the argument is a valid day
            elif any(day.startswith(arg) for day in days):
                possible_days = [d for d in days if d.startswith(arg)]
                if len(possible_days) == 1:
                    if day is None:
                        day = days.index(possible_days[0])
                    else:
                        raise ValueError("Multiple days found. Please provide only one day.")
                else:
                    raise ValueError(f"Day '{arg}' is ambiguous or does not match any valid day.")

            # Check if the argument is a valid term (T1, T2, or T3)
            elif arg in ['t1', 't2', 't3']:
                if term is None:
                    term = arg.upper()
                else:
                    raise ValueError("Multiple terms found. Please provide only one term.")

        if week is None or day is None:
            raise ValueError("Week and day must be specified.")

        return week, day, term
        

def setup(client: LynBotClient) -> None:
    """
    Adds the extension in this file to Lyn

    :param client: The instance of lyn to add the extension to
    :return:
    """

    this_ext = TermDate(client, "lynext.termdate")

    client.add_cog(this_ext)
