from discussion_question import DiscussionQuestion
from discord.ext.commands.context import Context
import globals
from discussion_question_manager import DiscussionQuestionManager

from textwrap import dedent
import pickle
import discord
from discord.channel import TextChannel
from discord.message import Message
from discord.ext import commands
from discord import RawReactionActionEvent as RawReaction
import os
import asyncio

# set up environment tokens
try:
    token = os.environ["GOLDBAR_BOT_TOKEN"]
except KeyError as e:
    print(f"Token {e} not found. Please set your environment variable properly. See README. Exiting.")
    exit()

bot = commands.Bot(command_prefix=".", description='".submit your-question-here', intents=discord.Intents.default())
manager: DiscussionQuestionManager = DiscussionQuestionManager()
with open("manager.txt", "rb") as f: # load existing question manager, if any
    try:
        manager = pickle.load(f)
    except EOFError:
        pass

# TODO
# which i guess I should have a way to toggle off "who asked the question" if they want to be anonymous
# time should mention the timezone

@bot.event
async def on_ready():
    print("--------\nREADY!!\n--------")
    await start_message_loop()

@bot.command()
async def submit(ctx: Context):
    question = DiscussionQuestion(ctx.message)
    manager.add_question(question)

    if globals.TEST_MODE:
        kinjo = await bot.fetch_user(globals.SAJO_ID)
    else:
        kinjo = await bot.fetch_user(globals.KINJO_ID)
    
    message = f"""
    Hey Kinjo!
    <@{question.author}> just submitted this question:

    {question.content}

    React with :white_check_mark: if you like it.
    """
    sent_msg: Message = await kinjo.send(dedent(message))
    question.add_verify_id(sent_msg.id)

# people react to message to add/remove themself from the list of people to be notified
# if they are already added, they are removed. else they are added.
async def change_notifiee(reaction: RawReaction):

    # if we're in test mode 
    if globals.TEST_MODE:
        # check if the msg is the same as the designated test one
        if reaction.message_id != globals.TEST_REACTION_MSG_ID:
            return
    # otherwise
    else: 
        # check if it's the same as the designated real one
        if reaction.message_id != globals.ACTUAL_REACTION_MSG_ID:
            return

    if reaction.user_id != globals.KINJO_ID: # don't care if kinjo's reacting, he will always be notified
        self.manager.change_notifiee(reaction.user_id)
    
async def add_question(reaction: RawReaction):
    # if we're testing, allow me and kinjo
    if globals.TEST_MODE:
        if reaction.user_id not in globals.ALLOWED_IDS:
            return
    # if we're live, only allow kinjo
    else:
        if reaction.user_id != globals.KINJO_ID:
            return
    
    channel: TextChannel = await bot.fetch_channel(reaction.channel_id)
    msg: Message = await channel.fetch_message(reaction.message_id)

    question = manager.get_from_verify_id(msg.id)
    if question:
        question.verify()
    
@bot.event
async def on_raw_reaction_add(reaction: RawReaction):
    if reaction.event_type != "REACTION_ADD":
        return
    
    if reaction.emoji.name == "kaneko_ok":
        await change_notifiee(reaction)
    
    if reaction.emoji.name == "✅":
        await add_question(reaction)
    
    # save updated manager to file
    with open("manager.txt", "wb") as f:
        pickle.dump(manager, f)

@bot.event
async def on_raw_reaction_remove(reaction: RawReaction):
    if reaction.event_type != "REACTION_REMOVE":
        return
    
    if reaction.emoji.name == "kaneko_ok":
        await self.change_notifiee(reaction)

    # save updated manager to file
    with open("manager.txt", "wb") as f:
        pickle.dump(self.manager, f)


async def start_message_loop():
    while True:
        if globals.TEST_MODE:
            await asyncio.sleep(globals.TEST_MESSAGE_DELAY_S)
        else:
            await asyncio.sleep(globals.ACTUAL_MESSAGE_DELAY_S)

        msg = str(manager)
        if globals.TEST_MODE:
            channel = await bot.fetch_channel(globals.TEST_CHANNEL)
        else:
            channel = await bot.fetch_channel(globals.ACTUAL_CHANNEL)
        await channel.send(msg)

        with open("manager.txt", "wb") as f:
            pickle.dump(manager, f)

# start bot
bot.run(token)
