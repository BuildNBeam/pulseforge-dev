import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger(__name__)

class Gaming(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trivia_questions = [
            {
                "question": "What is the capital of France?",
                "options": ["London", "Berlin", "Paris", "Madrid"],
                "correct": 2,
                "difficulty": "easy"
            },
            {
                "question": "Which planet is known as the Red Planet?",
                "options": ["Venus", "Mars", "Jupiter", "Saturn"],
                "correct": 1,
                "difficulty": "easy"
            },
            {
                "question": "What is the largest mammal in the world?",
                "options": ["African Elephant", "Blue Whale", "Giraffe", "Polar Bear"],
                "correct": 1,
                "difficulty": "medium"
            },
            {
                "question": "In which year did World War II end?",
                "options": ["1944", "1945", "1946", "1947"],
                "correct": 1,
                "difficulty": "medium"
            },
            {
                "question": "What is the chemical symbol for gold?",
                "options": ["Go", "Gd", "Au", "Ag"],
                "correct": 2,
                "difficulty": "hard"
            },
            {
                "question": "Who painted the Mona Lisa?",
                "options": ["Vincent van Gogh", "Pablo Picasso", "Leonardo da Vinci", "Michelangelo"],
                "correct": 2,
                "difficulty": "medium"
            },
            {
                "question": "What is the speed of light in vacuum?",
                "options": ["299,792,458 m/s", "300,000,000 m/s", "299,000,000 m/s", "301,000,000 m/s"],
                "correct": 0,
                "difficulty": "hard"
            },
            {
                "question": "Which programming language is known as the 'language of the web'?",
                "options": ["Python", "Java", "JavaScript", "C++"],
                "correct": 2,
                "difficulty": "easy"
            }
        ]
    
    @commands.hybrid_command(name="roll")
    @app_commands.describe(sides="Number of sides on the die (default: 6)")
    async def roll_die(self, ctx, sides: int = 6):
        """Roll a die with specified number of sides"""
        if sides < 2 or sides > 100:
            await ctx.send("❌ Number of sides must be between 2 and 100!")
            return
        
        result = random.randint(1, sides)
        
        embed = discord.Embed(
            title="🎲 Dice Roll",
            color=discord.Color.random()
        )
        embed.add_field(name="Die", value=f"d{sides}", inline=True)
        embed.add_field(name="Result", value=f"**{result}**", inline=True)
        embed.set_footer(text=f"Rolled by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="multiroll")
    @app_commands.describe(
        count="Number of dice to roll",
        sides="Number of sides on each die"
    )
    async def multi_roll(self, ctx, count: int = 2, sides: int = 6):
        """Roll multiple dice"""
        if count < 1 or count > 20:
            await ctx.send("❌ Number of dice must be between 1 and 20!")
            return
        
        if sides < 2 or sides > 100:
            await ctx.send("❌ Number of sides must be between 2 and 100!")
            return
        
        results = [random.randint(1, sides) for _ in range(count)]
        total = sum(results)
        
        embed = discord.Embed(
            title="🎲 Multiple Dice Roll",
            color=discord.Color.random()
        )
        embed.add_field(name="Dice", value=f"{count}d{sides}", inline=True)
        embed.add_field(name="Results", value=" + ".join(map(str, results)), inline=True)
        embed.add_field(name="Total", value=f"**{total}**", inline=True)
        embed.set_footer(text=f"Rolled by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="coinflip")
    async def coin_flip(self, ctx):
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙" if result == "Heads" else "🔴"
        
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"{emoji} **{result}**",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Flipped by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="8ball")
    @app_commands.describe(question="Question to ask the magic 8-ball")
    async def magic_8ball(self, ctx, *, question: str):
        """Ask the magic 8-ball a question"""
        responses = [
            # Positive
            "It is certain.", "Without a doubt.", "Yes definitely.", "You may rely on it.",
            "As I see it, yes.", "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
            
            # Neutral
            "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
            "Cannot predict now.", "Concentrate and ask again.",
            
            # Negative
            "Don't count on it.", "My reply is no.", "My sources say no.",
            "Outlook not so good.", "Very doubtful."
        ]
        
        response = random.choice(responses)
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=discord.Color.purple()
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=f"*{response}*", inline=False)
        embed.set_footer(text=f"Asked by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="rps")
    @app_commands.describe(choice="Your choice: rock, paper, or scissors")
    async def rock_paper_scissors(self, ctx, choice: str):
        """Play Rock, Paper, Scissors against the bot"""
        choice = choice.lower()
        if choice not in ["rock", "paper", "scissors"]:
            await ctx.send("❌ Please choose rock, paper, or scissors!")
            return
        
        bot_choice = random.choice(["rock", "paper", "scissors"])
        
        # Determine winner
        if choice == bot_choice:
            result = "It's a tie!"
            color = discord.Color.yellow()
        elif (choice == "rock" and bot_choice == "scissors") or \
             (choice == "paper" and bot_choice == "rock") or \
             (choice == "scissors" and bot_choice == "paper"):
            result = "You win! 🎉"
            color = discord.Color.green()
        else:
            result = "I win! 😎"
            color = discord.Color.red()
        
        # Emojis
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        
        embed = discord.Embed(
            title="✂️ Rock Paper Scissors",
            description=result,
            color=color
        )
        embed.add_field(name="Your Choice", value=f"{emojis[choice]} {choice.title()}", inline=True)
        embed.add_field(name="My Choice", value=f"{emojis[bot_choice]} {bot_choice.title()}", inline=True)
        embed.set_footer(text=f"Played by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="trivia")
    @app_commands.describe(difficulty="Difficulty level: easy, medium, or hard")
    async def trivia_game(self, ctx, difficulty: str = "random"):
        """Start a trivia game"""
        difficulty = difficulty.lower()
        
        # Filter questions by difficulty
        if difficulty in ["easy", "medium", "hard"]:
            questions = [q for q in self.trivia_questions if q["difficulty"] == difficulty]
        else:
            questions = self.trivia_questions
        
        if not questions:
            await ctx.send("❌ No questions available for that difficulty!")
            return
        
        question_data = random.choice(questions)
        
        embed = discord.Embed(
            title="🧠 Trivia Time!",
            description=question_data["question"],
            color=discord.Color.blue()
        )
        
        # Add options
        options_text = ""
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        for i, option in enumerate(question_data["options"]):
            options_text += f"{emojis[i]} {option}\n"
        
        embed.add_field(name="Options", value=options_text, inline=False)
        embed.add_field(name="Difficulty", value=question_data["difficulty"].title(), inline=True)
        embed.set_footer(text="You have 30 seconds to answer! React with the correct number.")
        
        msg = await ctx.send(embed=embed)
        
        # Add reaction options
        for i in range(len(question_data["options"])):
            await msg.add_reaction(emojis[i])
        
        def check(reaction, user):
            return (user == ctx.author and 
                   str(reaction.emoji) in emojis[:len(question_data["options"])] and 
                   reaction.message.id == msg.id)
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            # Check answer
            user_answer = emojis.index(str(reaction.emoji))
            correct_answer = question_data["correct"]
            
            if user_answer == correct_answer:
                result_embed = discord.Embed(
                    title="✅ Correct!",
                    description=f"Great job, {ctx.author.mention}!",
                    color=discord.Color.green()
                )
            else:
                result_embed = discord.Embed(
                    title="❌ Incorrect!",
                    description=f"The correct answer was: **{question_data['options'][correct_answer]}**",
                    color=discord.Color.red()
                )
            
            result_embed.add_field(
                name="Question",
                value=question_data["question"],
                inline=False
            )
            
            await ctx.send(embed=result_embed)
            
        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="⏰ Time's Up!",
                description=f"The correct answer was: **{question_data['options'][question_data['correct']]}**",
                color=discord.Color.orange()
            )
            await ctx.send(embed=timeout_embed)
    
    @commands.hybrid_command(name="random")
    @app_commands.describe(
        minimum="Minimum number",
        maximum="Maximum number"
    )
    async def random_number(self, ctx, minimum: int = 1, maximum: int = 100):
        """Generate a random number between min and max"""
        if minimum >= maximum:
            await ctx.send("❌ Minimum must be less than maximum!")
            return
        
        if maximum - minimum > 1000000:
            await ctx.send("❌ Range too large! Maximum range is 1,000,000.")
            return
        
        result = random.randint(minimum, maximum)
        
        embed = discord.Embed(
            title="🎲 Random Number",
            color=discord.Color.random()
        )
        embed.add_field(name="Range", value=f"{minimum} - {maximum}", inline=True)
        embed.add_field(name="Result", value=f"**{result}**", inline=True)
        embed.set_footer(text=f"Generated for {ctx.author.display_name}")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="choose")
    @app_commands.describe(choices="Comma-separated list of choices")
    async def choose_option(self, ctx, *, choices: str):
        """Choose randomly from a list of options"""
        options = [choice.strip() for choice in choices.split(",")]
        
        if len(options) < 2:
            await ctx.send("❌ Please provide at least 2 options separated by commas!")
            return
        
        if len(options) > 20:
            await ctx.send("❌ Too many options! Maximum is 20.")
            return
        
        choice = random.choice(options)
        
        embed = discord.Embed(
            title="🤔 Random Choice",
            color=discord.Color.random()
        )
        embed.add_field(
            name="Options",
            value=", ".join(options),
            inline=False
        )
        embed.add_field(
            name="I choose...",
            value=f"**{choice}**",
            inline=False
        )
        embed.set_footer(text=f"Chosen for {ctx.author.display_name}")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Gaming(bot))
