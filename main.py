import globals
from discussion_question_manager import DiscussionQuestionManager

import pickle
import discord
from discord.channel import TextChannel
from discord.message import Message
from discord.ext import tasks
import logging
import os


class Client(discord.Client):

    manager: DiscussionQuestionManager = DiscussionQuestionManager()

    async def on_ready(self):
        print("READY!!")
        self.send_message.start()


    async def on_raw_reaction_add(self, reaction: discord.RawReactionActionEvent):
        if reaction.event_type != "REACTION_ADD":
            return
        
        if reaction.emoji.name != "✅":
            return
        
        # if we're testing, allow me and kinjo
        if globals.TEST_MODE:
            if reaction.member.id not in globals.ALLOWED_IDS:
                return
        # if we're live, only allow kinjo
        else:
            if reaction.member.id != globals.KINJO_ID:
                return
        
        channel: TextChannel = await self.fetch_channel(reaction.channel_id)
        msg: Message = await channel.fetch_message(reaction.message_id)

        # add new question to manager, and add save manager to file
        self.manager.add_question_from_msg(msg)
        with open("questions.txt", "wb") as f:
            pickle.dump(self.manager, f)
    
    # @tasks.loop(hours=168)
    @tasks.loop(seconds=10)
    async def send_message(self):
        msg = str(self.manager)
        channel = await self.fetch_channel(globals.TEST_CHANNEL)
        await channel.send(msg)

        with open("questions.txt", "wb") as f:
            pickle.dump(self.manager, f)
        
def main():
    # set up logging
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

    # set up environment token
    try:
        token = os.environ["GOLDBAR_BOT_TOKEN"]
    except KeyError:
        print("Token not found. Please set your environment variable properly. See README. Exiting.")
        exit()
    
    # choose intents
    intents = discord.Intents.default()

    # make bot object
    client = Client(intents=intents)

    # load existing question manager, if any
    with open("questions.txt", "rb") as f:
        try:
            client.manager = pickle.load(f)
        except EOFError:
            pass

    # start bot
    client.run(token)

if __name__ == "__main__":
    main()