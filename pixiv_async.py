import aiofiles
import asyncio
from gppt import GetPixivToken

import os
from dotenv import load_dotenv

from functools import partial


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
            contents = await f.read()
            for line in contents:
                name, val = line.split('=')
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
        self._refresh_token = refresh_token
        self._login_user_id = user_id
        async with aiofiles.open(self._token_filename, 'w') as f:
            await f.write(f'PIXIV_REFRESH_TOKEN={self._refresh_token}\n')
            await f.write(f'PIXIV_USER_ID={self._login_user_id}\n')

        return refresh_token


async def _main(pixiv: Pixiv):
    token = await pixiv._get_token_cached()
    print(token)

if __name__ == '__main__':
    load_dotenv()
    p = Pixiv()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_main(p))
