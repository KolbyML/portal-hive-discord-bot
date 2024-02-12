from discord.ext import tasks
import discord
from discord import app_commands
from discord.ext import commands
import traceback
import datetime
import util
import os

portal_hive_time = datetime.time(hour=2, minute=30, tzinfo=datetime.timezone.utc)
glados_update_time = datetime.time(hour=14, minute=00, tzinfo=datetime.timezone.utc)

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # an attribute we can access from our task
        self.state = {}
        self.prefix = "!"

    async def setup_hook(self) -> None:
        # start the task to run in the background
        self.portal_hive.start()
        self.glados_degradation_check.start()
        self.glados_daily_update.start()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        self.state = util.load_state()

    @tasks.loop(time=portal_hive_time)  # task runs at 2:30 UTC
    async def portal_hive(self):
        message = "[**Portal Hive Daily Results**](<https://portal-hive.ethdevops.io/>)\n"

        try:
            test_data = util.get_today_vs_yesterday_portal_hive_test_data()
            for k in test_data:
                message += "- ``" + k["name"] + "``: " + str(k["yesterday_percent"]) + " -> " + str(k["today_percent"]) + " " + k["emoji"] + "\n"
        except Exception as e:
            traceback_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            print("failed to today vs yesterday" + "::", traceback_str)

        await self.send_message(message, "hive_channels")

    @tasks.loop(minutes=5.0)
    async def glados_degradation_check(self):
        
        message = ""
        try: 
            glados_success_rate = util.get_glados_hourly_success_rate()
            if "glados_success_rate" in self.state:
                previous_success_rate = self.state["glados_success_rate"]
                if previous_success_rate > 50 and glados_success_rate < 50:
                    message += "Glados trin success rate has degraded to " + str(glados_success_rate) + "%\n"  
                    await self.send_message(message, "glados_channels")         

            self.state["glados_success_rate"] = glados_success_rate
            util.save_state(self.state)
        except Exception as e:
            traceback_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            print("failed to get glados success rate" + "::", traceback_str)

    @tasks.loop(time=glados_update_time)
    async def glados_daily_update(self):
        try:
            glados_data = util.get_glados_hourly_success_rate()
            message = "[**Glados Daily Results**](<https://glados.ethdevops.io/>)\n"
            message += "Glados success rate is " + str(glados_data) + "\n"
            await self.send_message(message, "glados_channels")
        except Exception as e:
            traceback_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            print("failed to get glados success rate" + "::", traceback_str)

    async def send_message(self, message, channel):
        for i in self.state.get(channel, []):
            try:
                channel = self.get_channel(i)
                await channel.send(message)
            except Exception as e:
                print("failed to send message in channel " + str(i) + "::", e, "message:", message)

    @portal_hive.before_loop
    @glados_degradation_check.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in

    async def on_message(self, message):

        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content == self.prefix + 'help':
            embed = discord.Embed(title="Portal Intergrations Bot Commands List",
                                  url="",
                                  color=0X33fffc)
            embed.add_field(name=self.prefix + 'sub-hive',
                            value="Subscribes channel this command is ran in to get a daily message of stats")
            embed.add_field(name=self.prefix + 'unsub-hive',
                            value="Un-subscribes channel this command is ran in to get a daily message of stats")

            await message.channel.send(embed=embed)
            return

        if message.author.id in self.state["admins"]:
            if message.content == self.prefix + 'sub-hive':
                channel = message.channel.id
                self.state["hive_channels"].append(channel)
                util.save_state(self.state)
                await message.channel.send('Added channel to Portal Hive Status Updates')
                return
            if message.content == self.prefix + 'unsub-hive':
                channel = message.channel.id
                try:
                    self.state["hive_channels"].remove(channel)
                    await message.channel.send('Removed channel to Portal Hive Status Updates')
                except:
                    await message.channel.send('Failed to remove channel to Portal Hive Status Updates')
                util.save_state(self.state)
                return
            
            if message.content == self.prefix + 'sub-glados':
                channel = message.channel.id
                self.state["glados_channels"].append(channel)
                util.save_state(self.state)
                await message.channel.send('Added channel to Glados Status Updates')
                return
            if message.content == self.prefix + 'unsub-glados':
                channel = message.channel.id
                try:
                    self.state["glados_channels"].remove(channel)
                    await message.channel.send('Removed channel to Glados Status Updates')
                except:
                    await message.channel.send('Failed to remove channel to Glados Status Updates')
                util.save_state(self.state)
                return

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(os.environ["PORTALINTEGRATIONBOTTOKEN"])

