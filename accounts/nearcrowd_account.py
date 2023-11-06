import asyncio
import base64
import json
from typing import Any, Literal
from urllib.parse import quote

import aiohttp
from pydantic import BaseModel

from helper.provider_config import provider
from near import Account, FinalityTypes, KeyPair, Signer, transactions

contract_id = 'app.nearcrowd.near'
api = 'https://nearcrowd.com/'


class PostData(BaseModel):
    type: Literal['body', 'json']
    data: Any


class V2(BaseModel):
    path: str
    Q: str = ''
    args: dict = {}
    name: str = 'v2'
    post: PostData | None = None

    retry_count: int = 10


class InvalidKeyError(Exception):
    pass


class NearCrowdAccount:
    def __init__(self, account_id: str, private_key: str) -> None:
        self._signer = Signer(account_id, KeyPair(private_key))

    @property
    def account_id(self) -> str:
        return self._signer.account_id

    def get_nearcrowd_tx(self, actions: list[transactions.Action]) -> bytes:
        nonce = 0
        block_hash = b'\0' * 32
        return transactions.sign_and_serialize_transaction(contract_id, nonce, actions, block_hash, self._signer)

    def get_tx_args(self, args: dict = {}, name: str='v2') -> str:  # noqa: B006
        args = str.encode(json.dumps(args))
        encoded_tx = self.get_nearcrowd_tx([transactions.create_function_call_action(name, args, 0, 0)])
        return base64.b64encode(encoded_tx).decode('ascii')

    def get_tx(self, name: str='v2') -> str:
        return self.get_tx_args(name=name)

    async def check_account(self) -> bool:
        account = Account(provider, self._signer)
        await account.start()
        return await account.view_function(contract_id, 'is_account_whitelisted', {'account_id': self._signer.account_id})

    #return public keys
    @staticmethod
    async def get_access_keys(account_id: str) -> list[str]:
        result = []
        for key in (await provider.get_access_key_list(account_id, FinalityTypes.FINAL))['keys']:
            access_key = key['access_key']
            permission = access_key['permission']
            if permission == 'FullAccess' or permission['FunctionCall']['receiver_id'] == contract_id:
                result.append(key['public_key'])
        return result


    # MAYBE add status ?
    async def _query_one_try(self, q: V2) -> str:
        encoded_tx = self.get_tx_args(q.args, q.name)
        url = f'{api}{q.path}/{encoded_tx}{q.Q}'
        post = q.post

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            if post is None:
                request = session.get(url)
            else:
                post_kwargs: dict[str, Any] = {post.type: post.data}
                request = session.post(url, **post_kwargs, headers={'Content-Type': 'application/json'})

            async with request as response:
                text = await response.text()
                if not response.ok and text.endswith('AssertionError: Access key not found\n'):
                    raise InvalidKeyError
                response.raise_for_status()

                return text

    async def query(self, q: V2) -> str | None:
        for _ in range(q.retry_count):
            try:
                return await self._query_one_try(q)
            except Exception:  # noqa: BLE001
                await asyncio.sleep(1)
        return None

    async def report_review(self, task_id: int, report_order: int, reason: str) -> None:
        path = f'v2/report_review/{task_id}/{report_order}/{quote(reason, "")}'
        await self.query(V2(path=path))


    @staticmethod
    async def fetch_accountless(path: str, retries: int=10) -> str | None:
        for _ in range(retries):
            try:
                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session, session.get(f'{api}{path}') as response:
                    response.raise_for_status()
                    return await response.text()
            except Exception:  # noqa: BLE001
                await asyncio.sleep(1)
        return None

    @staticmethod
    async def get_coef(retries: int=10) -> float | None:
        coef = await NearCrowdAccount.fetch_accountless('get_coef', retries)
        return float(coef) if coef is not None else None
