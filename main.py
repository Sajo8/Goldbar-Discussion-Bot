from asyncio.exceptions import CancelledError
from asyncio.tasks import Task
from typing import Coroutine
from datetime import datetime

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
print(f"Test Mode: {globals.TEST_MODE}")

bot = commands.Bot(command_prefix=".", intents=discord.Intents.default())
manager: DiscussionQuestionManager = DiscussionQuestionManager()

cancelled: bool = False
sleep_task: Task = None

# if we're in production, load existing manager
# otherwise, we overwrite it every time
if not globals.TEST_MODE:
    with open("manager.txt", "rb") as f: 
        try:
            manager = pickle.load(f)
        except EOFError:
            pass

def is_sleeping():
    """
    Returns bot_sleep Task if it exists, else returns None
    """
    print("sleeping:", sleep_task)

    return None

async def cancel_question():
    """
    Cancel bot_sleep task if it exists
    """
    is_sleeping()

    t = is_sleeping()
    try:
        if t:
            print("before wait")
            asyncio.wait_for(t.cancel())
            print("after wait")
            cancelled = True
            return True
        else:
            print("didnt exist")
            return False
    except asyncio.TimeoutError:
        print("couldnt cancel ")
        cancelled = False
        return False

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

@bot.command(
    help = "Usage: .cancel",
    brief = "Cancel posting of the next question"
)
async def cancel(ctx: Context):
    res = await cancel_question()
    if res:
        await ctx.send("Cancelled posting of next question!")
    else:
        await ctx.send("Failed to cancel, please try again.")
    

@bot.command()
async def p(ctx):
    print(asyncio.all_tasks())


@bot.command(
    help = "Usage: \n.reschedule 02/04/21 18:07\nDate format: MM/DD/YY HH:MM",
    brief = "Reschedule next question"
)
async def reschedule(ctx: Context, new_date, time):
    print(ctx.args)
    print(new_date)
    print(time)

    date: datetime = datetime.strptime(new_date, "%m/%d/%y %H:%M")
    now: datetime = datetime.now()

    delay = (date - now).total_seconds()
    await cancel_question()
    # cancelled = false
    # print(delay)
    # await bot_sleep(delay)


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


## bot event loop

async def bot_sleep(delay = None):
    global sleep_task

    print("bs:", cancelled)
    try:
        print("being slept")
        if not delay:
            delay = globals.TEST_MESSAGE_DELAY_S if globals.TEST_MODE else globals.ACTUAL_MESSAGE_DELAY_S

        print(sleep_task)
        
        sleep_task = asyncio.create_task(asyncio.sleep(delay))
        await sleep_task

        print(sleep_task)
        exit()
    except CancelledError:
        print("cancelled")

async def send_message():
    # print("m:", cancelled)

    msg = str(manager)
    channel = await bot.fetch_channel(globals.TEST_CHANNEL) if globals.TEST_MODE else await bot.fetch_channel(globals.ACTUAL_CHANNEL)
    await channel.send(msg)

    with open("manager.txt", "wb") as f:
        pickle.dump(manager, f)


async def start_message_loop():
    while True:
        # print("l:", cancelled)
        if cancelled: 
            break

        # only sleep if we're not already sleeping
        if not is_sleeping():
            print("we r  not sleeping")
            await bot_sleep()
        await send_message()
        

# start bot
bot.run(token)

########################################

# in progress
# <Task pending name='Task-12' coro=<sleep() running at c:\users\sajo\appdata\local\programs\python\python38\lib\asyncio\tasks.py:648> wait_for=<Future pending cb=[<TaskWakeupMethWrapper object at 0x0000016002FEBB80>()]> cb=[<TaskWakeupMethWrapper object at 0x0000016002ECCB20>()]>

#over
# <Task finished name='Task-12' coro=<sleep() done, defined at c:\users\sajo\appdata\local\programs\python\python38\lib\asyncio\tasks.py:630> result=None>

# see Task documentation to see if it's pending or finished and use that check if we're sleeping or done slepenig?

# ensure .cancel works
# ensure .reschedule works
#### for reschedule, check if the newly added time works (it should)
