import discord
import aiohttp

import os
from dotenv import load_dotenv

load_dotenv()
from pprint import pprint as pp


config = {
    'token': os.getenv('BOT_TOKEN'),
    'prefix': 'prefix'
}

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

# good
async def get_cat(channel):
    async with aiohttp.ClientSession() as session:
        async with session.get('http://aws.random.cat/meow') as r:
            if r.status == 200:
                js = await r.json()
                await channel.send(js['file'])

@client.event
async def on_message(message):
    # Ignore messages from the bot
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
    
    if message.content.startswith('!cat'):
        await get_cat(message.channel)
        

client.run(config['token'])