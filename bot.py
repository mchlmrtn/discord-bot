import os
import discord
import nest_asyncio
from openai import OpenAI
import time

# Fix event loop issues
nest_asyncio.apply()

# API keys
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Discord client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

total_tokens_today = 0
today_date = time.strftime("%Y-%m-%d")
price_per_1k_tokens = 0.0001
daily_spend_limit_usd = 1.00
warning_threshold = 0.8

@client.event
async def on_ready():
    print(f'✅ Bot is online as {client.user}')

@client.event
async def on_message(message):
    global total_tokens_today, today_date, daily_spend_limit_usd

    if message.author == client.user:
        return

    if time.strftime("%Y-%m-%d") != today_date:
        total_tokens_today = 0
        today_date = time.strftime("%Y-%m-%d")
        daily_spend_limit_usd = 1.00

    if message.content.startswith('!boost'):
        daily_spend_limit_usd += 1.00
        await message.channel.send(f"🚀 Daily limit increased! New limit: ${daily_spend_limit_usd:.2f}")
        return

    if message.content.startswith('!ask'):
        prompt = message.content[5:].strip()

        if not prompt:
            await message.channel.send("⚠️ You must ask a question after `!ask`!")
            return

        estimated_spent = (total_tokens_today / 1000) * price_per_1k_tokens
        if estimated_spent >= daily_spend_limit_usd:
            await message.channel.send("🚫 Daily limit reached. Use `!boost` to add more!")
            return

        thinking_message = await message.channel.send("🤔 Thinking...")

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": prompt}]
            )
            reply = response.choices[0].message.content
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = prompt_tokens + completion_tokens
            total_tokens_today += total_tokens

            await thinking_message.edit(content=reply)

            estimated_spent = (total_tokens_today / 1000) * price_per_1k_tokens
            if estimated_spent >= daily_spend_limit_usd * warning_threshold and estimated_spent < daily_spend_limit_usd:
                await message.channel.send(f"⚠️ Warning: {int(estimated_spent / daily_spend_limit_usd * 100)}% of daily limit used!")

        except Exception as e:
            await thinking_message.edit(content=f"Error: {e}")

client.run(DISCORD_TOKEN)
