import discord
import aiohttp
import aiofiles

import os
from dotenv import load_dotenv

load_dotenv()
from pprint import pprint as pp

from pixiv import Pixiv


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
    
    await pixiv._get_token_cached()
    try:
        resp_from_login = await pixiv._login()
    except Exception as e:
        # probably the token is not valid anymore
        print('probably token is not a valid anymore\n', e)
        pixiv.update_token()
        # try again
        print('second try to login')
        resp_from_login = await pixiv._login()
    print('success login with resp', resp_from_login)

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

    if message.content.startswith('!pix '):
        keyword = message.content[5:]
        pic_filename = await pixiv.get_picture(keyword)
        print('pic filename: ', pic_filename)
        await message.channel.send(file=discord.File(pic_filename))
        # async with aiofiles.open(pic_filename, 'rb') as f:
        #     data = await f.read()
        #     picture = discord.File(data)
        #     await message.channel.send(file=picture)
        
pixiv = Pixiv()
client.run(config['token'])