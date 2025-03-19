import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
discord_token = os.getenv("TOKEN")
gemini_api_key = os.getenv("APIKEY")

genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.tree.sync()
        print(f"Logged in as {self.user}")

client = MyClient()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.name == "ai-channel":
        try:
            response = model.generate_content(message.content)
            ai_response = response.text

            await message.channel.send(ai_response)
        except Exception as e:
            await message.channel.send(f"Sorry, there was an error processing your request: {e}")

@client.tree.command(name="ai", description="Get a response from the AI based on your input.")
@app_commands.describe(prompt="The text to which the AI should respond.")
async def ai(interaction: discord.Interaction, prompt: str):
    try:
        await interaction.response.defer()

        response = model.generate_content(prompt)
        response_text = response.text

        await interaction.followup.send(f"{response_text}")
    except Exception as e:
        await interaction.followup.send(f"Sorry, there was an error processing your request: {e}", ephemeral=True)

client.run(discord_token)
