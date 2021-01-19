import os

try:
    # convert "1" to 1 to True
    # convert "0" to 0 to False
    TEST_MODE: bool = bool(int(os.environ["GOLDBAR_BOT_TEST_MODE"]))
    os.environ["GOLDBAR_BOT_TOKEN"] # not used, but tested here so that we don't need to in main.py
except KeyError as e:
    print(f"Token {e} not found. Please set your environment variable properly. See README. Exiting.")
    exit()

TEST_CHANNEL: int = 791471427277553735
ACTUAL_CHANNEL: int = 445478735970304001
ALLOWED_CHANNELS: list = [TEST_CHANNEL, ACTUAL_CHANNEL]

KINJO_ID: int = 182417232524083201
SAJO_ID: int = 235707623985512451
ALLOWED_IDS: list = [KINJO_ID, SAJO_ID]

TEST_REACTION_MSG_ID: int = 791826753462075412
ACTUAL_REACTION_MSG_ID: int = 791829415810039828

TEST_MESSAGE_DELAY_S = 5 #20
ACTUAL_MESSAGE_DELAY_S = 604800