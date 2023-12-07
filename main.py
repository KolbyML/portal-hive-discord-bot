from discord.ext import tasks
import discord
from discord import app_commands
from discord.ext import commands
import datetime
import util
import os

announcement_time = datetime.time(hour=2, minute=30, tzinfo=datetime.timezone.utc)


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # an attribute we can access from our task
        self.state = {}
        self.prefix = "!"

    async def setup_hook(self) -> None:
        # start the task to run in the background
        self.my_background_task.start()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        self.state = util.load_state()

    @tasks.loop(time=announcement_time)  # task runs every 60 seconds
    async def my_background_task(self):
        message = "[**Portal Hive Daily Results**](<https://portal-hive.ethdevops.io/>)\n"

        try:
            test_data = util.get_today_vs_yesterday_portal_hive_test_data()
            for k in test_data:
                message += "- ``" + k["name"] + "``: " + str(k["yesterday_percent"]) + " -> " + str(k["today_percent"]) + " " + k["emoji"] + "\n"
        except Exception as e:
            message += "failed to today vs yesterday ::" + str(e.__traceback__) if e.__traceback__ is not None else "no trace avaliable"
            print("failed to today vs yesterday" + "::", e.__traceback__, "message:", message)


        for i in self.state["channels"]:
            try:
                channel = self.get_channel(i)
                await channel.send(message)
            except Exception as e:
                print("failed to send message in channel " + str(i) + "::", e, "message:", message)

    @my_background_task.before_loop
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
                self.state["channels"].append(channel)
                util.save_state(self.state)
                await message.channel.send('Added channel to Portal Hive Status Updates')
                return
            if message.content == self.prefix + 'unsub-hive':
                channel = message.channel.id
                try:
                    self.state["channels"].remove(channel)
                    await message.channel.send('Removed channel to Portal Hive Status Updates')
                except:
                    await message.channel.send('Failed to remove channel to Portal Hive Status Updates')
                util.save_state(self.state)
                return

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(os.environ["PORTALINTEGRATIONBOTTOKEN"])

