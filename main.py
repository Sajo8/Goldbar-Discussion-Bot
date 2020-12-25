import globals
from discussion_question_manager import DiscussionQuestionManager

import pickle
import discord
from discord.channel import TextChannel
from discord.message import Message
from discord.ext import tasks
from discord import RawReactionActionEvent as RawReaction
import logging
import os
import asyncio

logger: logging.Logger

class Client(discord.Client):

    manager: DiscussionQuestionManager = DiscussionQuestionManager()

    async def on_ready(self):
        print("READY!!")
        await self.start_message_loop()


    # people react to message to add/remove themself from the list of people to be notified
    # if they are already added, they are removed. else they are added.
    async def change_notifiee(self, reaction: RawReaction):

        # if we're in test mode 
        if globals.TEST_MODE:
            # check if the msg is the same as the designated test one
            if reaction.message_id != globals.TEST_REACTION_MSG_ID:
                return
        # otherwise
        else: 
            # heck if it's the same as the designated real one
            if reaction.message_id != globals.ACTUAL_REACTION_MSG_ID:
                return

        if reaction.user_id != globals.KINJO_ID: # don't care if kinjo's reacting, he will always be notified
            self.manager.change_notifiee(reaction.user_id)
        
            
    async def add_question(self, reaction: RawReaction):
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

        # add new question to manager
        self.manager.add_question_from_msg(msg)        


    async def on_raw_reaction_add(self, reaction: RawReaction):
        if reaction.event_type != "REACTION_ADD":
            return
        
        if reaction.emoji.name == "kaneko_ok":
            await self.change_notifiee(reaction)
        
        if reaction.emoji.name == "✅":
            await self.add_question(reaction)
        
        # save updated manager to file
        with open("manager.txt", "wb") as f:
            pickle.dump(self.manager, f)

    
    async def on_raw_reaction_remove(self, reaction: RawReaction):
        if reaction.event_type != "REACTION_REMOVE":
            return
        
        if reaction.emoji.name == "kaneko_ok":
            await self.change_notifiee(reaction)

        # save updated manager to file
        with open("manager.txt", "wb") as f:
            pickle.dump(self.manager, f)


    async def start_message_loop(self):
        while True:
            if globals.TEST_MODE:
                await asyncio.sleep(globals.TEST_MESSAGE_DELAY_S)
            else:
                await asyncio.sleep(globals.ACTUAL_MESSAGE_DELAY_S)

            msg = str(self.manager)
            channel = await self.fetch_channel(globals.TEST_CHANNEL)
            await channel.send(msg)

            with open("manager.txt", "wb") as f:
                pickle.dump(self.manager, f)
    
def main():
    global logger
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
    
    intents = discord.Intents.default() # choose intents
    client = Client(intents=intents) # make bot object

    with open("manager.txt", "rb") as f: # load existing question manager, if any
        try:
            client.manager = pickle.load(f)
        except EOFError:
            pass
    
    # start bot
    client.run(token)

if __name__ == "__main__":
    main()