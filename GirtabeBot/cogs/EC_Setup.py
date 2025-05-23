import discord
from dotenv import load_dotenv
import os
load_dotenv()

INTENTS = discord.Intents.all()
PREFIX = ","
OWNER_ID = int(os.getenv("OWNER_ID"))
TOKEN = os.getenv("BOT_TOKEN")
