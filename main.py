import globals

from discussion_question import DiscussionQuestion
from discord.ext.commands.context import Context
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

token = os.environ["GOLDBAR_BOT_TOKEN"]

bot = commands.Bot(command_prefix=".", intents=discord.Intents.default())
manager: DiscussionQuestionManager = DiscussionQuestionManager()

# if we're in production, load existing manager
# otherwise, we overwrite it every time
if not globals.TEST_MODE:
    with open("manager.txt", "rb") as f: 
        try:
            manager = pickle.load(f)
        except EOFError:
            pass

@bot.event
async def on_ready():
    print("--------\nREADY!!\n--------")
    await start_message_loop()

@bot.command(
    help = "Usage: \n.submit your question goes here!",
    brief = "Submit your question"
)
async def submit(ctx: Context, your_question = ""):
    question = DiscussionQuestion(ctx.message)
    manager.add_question(question)
    await ctx.send("Submission received!")

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

@bot.command(
    help = "Usage: \n.anon \n.anon off \n.anon on \n\nJust .anon will show the current status. \nOnly Kinjo can use this",
    brief = "Show/hide author's name"
) 
async def anon(ctx: Context, new_mode = ""):
    if globals.TEST_MODE:
        if ctx.author.id not in globals.ALLOWED_IDS:
            return
    else: 
        if ctx.author.id != globals.KINJO_ID:
            return
    
    if new_mode == "":
        await ctx.send(f"Anonymous status: {manager.anonymous}")
    elif new_mode == "on":
        manager.anonymous = True
        await ctx.send(f"New anonymous status: {manager.anonymous}")
    elif new_mode == "off":
        manager.anonymous = False
        await ctx.send(f"New anonymous status: {manager.anonymous}")

# people react to message to add/remove themself from the list of people to be notified
# flag to see if they're being added / removed
async def change_notifiee(reaction: RawReaction, add: bool):
    if globals.TEST_MODE:
        if reaction.message_id != globals.TEST_REACTION_MSG_ID:
            return
    else: 
        if reaction.message_id != globals.ACTUAL_REACTION_MSG_ID:
            return

    if reaction.user_id != globals.KINJO_ID: # don't care if kinjo's reacting, he will always be notified
        if add:
            manager.add_notifiee(reaction.user_id)
        else:
            manager.remove_notifiee(reaction.user_id)
    
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
        await change_notifiee(reaction, True)
    
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
        await change_notifiee(reaction, False)

    # save updated manager to file
    with open("manager.txt", "wb") as f:
        pickle.dump(manager, f)


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
