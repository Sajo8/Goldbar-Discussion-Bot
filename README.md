Goldbar-Discussion-Bot

# Setup

1. Clone
2. Setup discord bot (see [here](https://discordpy.readthedocs.io/en/latest/discord.html))
   1. When deciding what perms, give it an int value of `85056`
   2. view channels, send msgs, embed links, read msg history, add reactions
3. Set environment variable `GOLDBAR_BOT_TOKEN` to the client secret obtained from the "Bot" page
   1. [(For me)](https://discord.com/developers/applications/791466142760960001/bot)
4. Set environment variable `GOLDBAR_BOT_TEST_MODE` to a value of `True` or `False`.
5. Run `main.py`