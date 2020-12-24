import globals

import discord
from discord.channel import TextChannel
from discord.message import Message
import logging
import os
import json

class Client(discord.Client):

    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_raw_reaction_add(self, reaction: discord.RawReactionActionEvent):
        if reaction.event_type != "REACTION_ADD":
            return
        
        if reaction.emoji.name != "✅":
            return
        
        if reaction.member.id not in globals.ALLOWED_IDS:
            return
        
        # if we're in the live server
        if reaction.channel_id != globals.TEST_CHANNEL:
            # only allow Kinjo to approve messages
            if reaction.member.id != globals.KINJO_ID:
                return
        
        channel: TextChannel = self.get_channel(reaction.channel_id)
        msg: Message = await channel.fetch_message(reaction.message_id)

        await self.add_message(msg)

    async def add_message(self, msg: Message):
        msg_info_dict = {
            "author": f"<@{msg.author.id}>",
            "content": msg.content,
            "date": msg.created_at.strftime("%d %b %Y")
        }

        await msg.channel.send(str(msg_info_dict))

        with open("messages.json", "a") as f:
            json.dump(msg_info_dict, f, indent=4)
    
    # TODO
    # look into better persistent storage
        # maybe make an object and pickle that instead of doing dict
        # save to some list? idk
    # look into discord.py cogs or something to schedule sending messages 


def main():
    # set up logging
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

    # set up environment token
    try:
        token = os.environ["DISCORD_TOKEN"]
    except KeyError:
        print("Token not found. Please set your environment variable properly. Exiting.")
        exit()
    
    # choose intents
    intents = discord.Intents.default()

    # start bot
    client = Client(intents=intents)
    client.run(token)

if __name__ == "__main__":
    main()