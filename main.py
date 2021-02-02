from asyncio.exceptions import CancelledError, InvalidStateError
from asyncio.tasks import Task
from datetime import datetime, timedelta

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
    Returns if we are sleeping or not
    """
    if sleep_task:
        try:
            res = sleep_task.result()  # if we get a result, it's finished sleeping
            return False
        except CancelledError:  # if it's cancelled, it's not sleeping
            return False
        except InvalidStateError:  # if it's still processing, it's sleeping
            return True

    # sleep task not defined yet
    # not sleeping
    else:
        return False


def cancel_posting():
    """
    Cancel bot_sleep task if it exists
    """
    global cancelled

    if sleep_task:
        sleep_task.cancel()
        cancelled = True


async def resume_posting():
    global cancelled
    cancelled = False
    await start_message_loop()


@bot.event
async def on_ready():
    print("--------\nREADY!!\n--------")
    await start_message_loop()


@bot.command(help="Usage: \n.submit your question goes here!", brief="Submit your question")
async def submit(ctx: Context, your_question=""):
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
    help="Usage: \n.anon \n.anon off \n.anon on \n\nJust .anon will show the current status. \nOnly Kinjo can use this",
    brief="Show/hide author's name",
)
async def anon(ctx: Context, new_mode=""):
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
    help="Usage: .cancel \nMUST BE FOLLOWED BY .resume OR .reschedule OR NO QUESTIONS WILL BE POSTED.",
    brief="Stops posting of questions. READ DETAILED INFO!!",
)
async def cancel(ctx: Context):
    cancel_posting()
    await ctx.send("Cancelled!")


@bot.command(help="Usage: .resume", brief="If cancelled, resumes posting of questions")
async def resume(ctx: Context):
    await ctx.send("Resumed!")
    await resume_posting()


@bot.command(
    help="Usage: \n.reschedule 02/04/2021 18:07\nDate format: MM/DD/YYYY HH:MM\n\nWill also resume posting of questions if previous cancelled\n\nOnly Kinjo can use this",
    brief="Reschedule next question",
)
async def reschedule(ctx: Context, new_date, new_time):
    if globals.TEST_MODE:
        if ctx.author.id not in globals.ALLOWED_IDS:
            return
    else:
        if ctx.author.id != globals.KINJO_ID:
            return
    
    try:
        date = datetime.strptime(new_date, "%m/%d/%Y").date()
        time = datetime.strptime(new_time, "%H:%M").time()
    except Exception as e: # they messe dup formatting somehow
        await ctx.send(f"Error! You did something wrong: {e}")
        return

    date: datetime = datetime.combine(date, time)
    now: datetime = datetime.now()
    
    if not (date > now): # scheduled date is before today
        await ctx.send("Error! You can't schedule a message for the past!")
        return
    
    planned_date: timedelta = date - now
    delay = planned_date.total_seconds()

    formatted_date = (now + planned_date).strftime("%m/%d/%Y, %H:%M:%S")
    await ctx.send(f"Successfully rescheduled! Will post next question on the specified date and time.\nPlanned time: {formatted_date}")
    
    cancel_posting()

    await bot_sleep(delay)
    await send_message()

    await resume_posting()


# people react to message to add/remove themself from the list of people to be notified
# flag to see if they're being added / removed
async def change_notifiee(reaction: RawReaction, add: bool):
    if globals.TEST_MODE:
        if reaction.message_id != globals.TEST_REACTION_MSG_ID:
            return
    else:
        if reaction.message_id != globals.ACTUAL_REACTION_MSG_ID:
            return

    if reaction.user_id != globals.KINJO_ID:  # don't care if kinjo's reacting, he will always be notified
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


async def send_message():
    msg = str(manager)
    channel = (
        await bot.fetch_channel(globals.TEST_CHANNEL)
        if globals.TEST_MODE
        else await bot.fetch_channel(globals.ACTUAL_CHANNEL)
    )
    await channel.send(msg)

    with open("manager.txt", "wb") as f:
        pickle.dump(manager, f)


async def bot_sleep(delay=None):
    global sleep_task

    print("being slept")
    if not delay:
        delay = globals.TEST_MESSAGE_DELAY_S if globals.TEST_MODE else globals.ACTUAL_MESSAGE_DELAY_S

    sleep_task = asyncio.create_task(asyncio.sleep(delay))
    try:
        await sleep_task
    except CancelledError:
        pass


async def start_message_loop():
    while True:
        # if cancelled, don't sleep
        if cancelled:
            break

        # only sleep if we're not already sleeping
        if not is_sleeping():
            await bot_sleep()
        # if cancelled, the bot will try to send a message
        # we need to stop that
        # two "if cancelled" checks are needed for that purpose
        if not cancelled:
            await send_message()


# start bot
bot.run(token)

########################################

# in progress
# <Task pending name='Task-12' coro=<sleep() running at c:\users\sajo\appdata\local\programs\python\python38\lib\asyncio\tasks.py:648> wait_for=<Future pending cb=[<TaskWakeupMethWrapper object at 0x0000016002FEBB80>()]> cb=[<TaskWakeupMethWrapper object at 0x0000016002ECCB20>()]>

# over
# <Task finished name='Task-12' coro=<sleep() done, defined at c:\users\sajo\appdata\local\programs\python\python38\lib\asyncio\tasks.py:630> result=None>

# see Task documentation to see if it's pending or finished and use that check if we're sleeping or done slepenig?

# ensure .cancel works
# ensure .reschedule works
#### for reschedule, check if the newly added time works (it should)
