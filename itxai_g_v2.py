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
        self.conversations = {}

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
            user_id = message.author.id

            if user_id not in client.conversations:
                client.conversations[user_id] = []

            client.conversations[user_id].append({"role": "user", "content": message.content})

            context = client.conversations[user_id]
            response = model.generate_content("\n".join([f"{msg['role']}: {msg['content']}" for msg in context]))
            ai_response = response.text

            client.conversations[user_id].append({"role": "assistant", "content": ai_response})

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

@client.tree.command(name="ai_custom", description="Get a response from the AI based on your input and creativity setting.")
@app_commands.describe(prompt="The text to which the AI should respond.", creativity="Creativity level for the AI (e.g., 0.1 for low creativity, 1.0 for high creativity).", style="Enter text style")
async def ai_custom(interaction: discord.Interaction, prompt: str, creativity: float, style: str):
    try:
        try:
            creativity = float(creativity)
        except ValueError:
            await interaction.response.send_message("Creativity must be a number between 0.0 and 10.0", ephemeral=True)
            return

        if not (0.0 <= creativity <= 10.0):
            await interaction.response.send_message("Creativity must be between 0.0 and 10.0", ephemeral=True)
            return

        await interaction.response.defer()

        response = model.generate_content(
            f"{prompt} in {style} style",
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=100,
                temperature=creativity/10,
            )
        )
        response_text = response.text

        await interaction.followup.send(f"{response_text}")
    except Exception as e:
        await interaction.followup.send(f"Sorry, there was an error processing your request: {e}", ephemeral=True)

@client.event
async def on_ready():
    try:
        await client.tree.sync() 
        print(f"Logged in as {client.user}. Command tree synced.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# Run the bot
client.run(discord_token)
