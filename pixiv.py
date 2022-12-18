import aiofiles
import asyncio

from gppt import GetPixivToken
from pixivpy_async import AppPixivAPI

import os
from dotenv import load_dotenv
from datetime import datetime

from functools import partial

import pprint


class Pixiv:
    '''
    Async class for using in `DisXiv` discord pixiv bot.

    Incapsulates pixiv related logic.
    '''
    def __init__(self):
        self._token_filename = '.refresh'
        self._refresh_token = None
        self._token_getter = GetPixivToken()
        self._login_user_id = None
        self._aapi = AppPixivAPI()

    async def _get_token_cached(self):
        '''
        Try to get refresh token for pixiv.net cached, using Pixiv API if fails
        '''
        # looking for token in object field
        if self._refresh_token:
            return self._refresh_token
        # looking for token in .env file
        # as the operation to get one is long and heavy
        token = None
        async with aiofiles.open(self._token_filename, 'r') as f:
            content = await f.read()
            lines = content.split('\n')
            for line in lines:
                name_val = line.split('=')
                if len(name_val) != 2:
                    continue
                name, val = name_val
                if name == 'PIXIV_REFRESH_TOKEN':
                    token = val
        if token:
            print(f'Token {token} found in {self._token_filename} file')
            self._refresh_token = token
            return token
        print(f'Token not found in {self._token_filename} file')
        # saved token not found - let's try to get it with api (long procedure)
        return await self._get_token_api()

    async def _get_token_api(self):
        '''
        Gets refresh token for pixiv.net using Pixiv API

        Updates cached values: `self._refresh_token` and value in file
        '''
        loop = asyncio.get_event_loop()
        try:
            res = await loop.run_in_executor(None, partial(
                    self._token_getter.login,
                    headless=True,
                    user=os.getenv('PIXIV_USERNAME'),
                    pass_=os.getenv('PIXIV_PASSWORD')
                )
            )
        except Exception as e:
            print('ERROR: Get refresh token fail. Reason:\n', e)
            return None

        access_token = res['access_token']
        refresh_token = res['refresh_token']
        user_id = res['response']['user']['id']
        # debug
        print('Got the following info from pixiv API:')
        print('access token:', access_token)
        print('refresh token:', refresh_token)
        print('user id:', user_id)

        # updating cache
        await self.set_refresh_token(refresh_token)

        return refresh_token

    async def set_refresh_token(self, token):
        self._refresh_token = token
        async with aiofiles.open(self._token_filename, 'w') as f:
            await f.write(f'PIXIV_REFRESH_TOKEN={self._refresh_token}\n')
    
    async def get_url(self, text) -> str:
        response = await self._aapi.search_illust(word=text)
        illustrations = response['illusts']
        print(f'found {len(illustrations)} illustrations')
        # let's get first not R-18 illustration
        picked_pic = None
        for illustration in illustrations:
            if illustration['x_restrict'] == 0:
                picked_pic = illustration
                break
        if not picked_pic:
            print(f"Can't find picture with '{text} keyword'")
            return None
        
        # pic_id = picked_pic['id']
        pic_url_medium = picked_pic['image_urls']['square_medium']

        return pic_url_medium

    async def download_by_url(self, url):
        name = str(datetime.now()) + '.jpg'
        await self._aapi.download(url, path='pictures', name=name)

    async def _login(self):
        return await self._aapi.login(refresh_token=self._refresh_token)

    async def update_token(self):
        loop = asyncio.get_event_loop()
        print('start refreshing refresh token')
        try:
            res = await loop.run_in_executor(None, partial(
                    self._token_getter.refresh,
                    self._refresh_token
                )
            )
        except Exception as e:
            print('ERROR: Get refresh token fail. Reason:\n', e)
            return None
        print(res)
        new_refresh_token = res['refresh_token']
        await self.set_refresh_token(new_refresh_token)
        

async def _main(pixiv: Pixiv):
    token = await pixiv._get_token_cached()
    try:
        resp_from_login = await pixiv._login()
    except Exception as e:
        # probably the token is not valid anymore
        print('probably token is not a valid anymore\n', e)
        pixiv.update_token()
        # try again
        print('second try to login')
        resp_from_login = await pixiv._login()

    pprint.pprint('response from login:', resp_from_login)
    url = await pixiv.get_url('arknights')
    await pixiv.download_by_url(url)


if __name__ == '__main__':
    load_dotenv()
    p = Pixiv()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_main(p))
