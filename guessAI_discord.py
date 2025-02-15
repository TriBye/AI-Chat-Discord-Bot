import os
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from google import genai
from dotenv import load_dotenv

load_dotenv()
discord_token = os.getenv("TOKEN")
gemini_api_key = os.getenv("APIKEY")

# Initialize the Gemini client and chat session
client_ai = genai.Client(api_key=gemini_api_key)
chat = client_ai.chats.create(model="gemini-2.0-flash")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.tree.sync()
        print(f"Logged in as {self.user}")

client = MyClient()

@client.tree.command(name="guess_ai_quiz", description="Play the GuessAI game by ITX Mini")
@app_commands.describe(
    difficulty="Enter Difficulty",
    questions="Enter Number of Questions (We recommend 20)",
    extra="Extra Wishes or Game Adjustments, keep empty if not"
)
async def guess_ai(interaction: discord.Interaction, difficulty: str, questions: int, extra: str):
    await interaction.response.defer()
    
    if interaction.channel and interaction.channel.name == "ai-channel": 
        # Start the conversation with the initial prompt.
        conversation_history = (
            f"You are thinking of a famous person with the {difficulty} difficulty. "
            f"Let's play a guessing game with {questions} yes/no questions. "
            f"Start by introducing the game and remind the player when the question limit is reached. "
            f"Extra instructions: {extra}"
        )
        
        # Send initial prompt to the AI and relay its introduction.
        ai_response = chat.send_message(conversation_history)
        await interaction.followup.send(ai_response.text)
        
        # Allow multiple turns: each iteration represents one question/answer turn.
        for i in range(questions):
            def check(message: discord.Message):
                return (message.author.id == interaction.user.id and 
                        message.channel.id == interaction.channel.id)
            
            try:
                # Wait for the user's answer with a timeout (60 seconds in this example)
                user_message = await client.wait_for("message", timeout=200.0, check=check)
            except asyncio.TimeoutError:
                await interaction.followup.send("Timeout waiting for your answer. Game over.")
                return
            
            # Append the user's response to the conversation history
            conversation_history += f"\nUser: {user_message.content}"
            
            # Get the AI's next response based on the updated conversation history
            ai_response = chat.send_message(conversation_history)
            await interaction.followup.send(ai_response.text)
            
            # Optionally, check if the AI indicates the game has ended (e.g., it guessed correctly)
            if "guessed" in ai_response.text.lower():
                break
        
        await interaction.followup.send("Game over!")
    else:
        await interaction.followup.send("Please use the AI-Channel for Games!")

client.run(discord_token)