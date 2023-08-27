import itertools
import json
from typing import Any

import base58
from aiohttp import ClientTimeout

from . import providers, signer, transactions

# Amount of gas attached by default 1e14.
DEFAULT_ATTACHED_GAS = 100_000_000_000_000


class TransactionError(Exception):
    pass


class ViewFunctionError(Exception):
    pass


class Account:

    def __init__(
            self,
            provider: providers.JsonProvider,
            signer: signer.Signer,
    ) -> None:
        self._provider = provider
        self._signer = signer
        self._account_id = self._signer.account_id

    async def start(self) -> None:
        self._account: dict = await self._provider.get_account(self._account_id)
        self._access_key: dict = await self._provider.get_access_key(self._account_id, self._signer.key_pair.encoded_public_key)
        if 'error' in self._access_key:
            raise ViewFunctionError(self._access_key['error'])

    async def _sign_and_submit_tx(self, receiver_id: str, actions: list[transactions.Action]) -> dict:
        serialized_tx = await self.get_tx(receiver_id, actions)
        result: dict = await self._provider.send_tx_and_wait(serialized_tx, ClientTimeout(10))
        for outcome in itertools.chain([result['transaction_outcome']], result['receipts_outcome']):
            for log in outcome['outcome']['logs']:
                print('Log:', log)
        if 'Failure' in result['status']:
            raise TransactionError(result['status']['Failure'])
        return result

    async def get_tx(self, receiver_id: str, actions: list[transactions.Action]) -> bytes:
        self._access_key['nonce'] += 1
        block_hash = (await self._provider.get_status())['sync_info']['latest_block_hash']
        block_hash = base58.b58decode(block_hash.encode('utf8'))
        return transactions.sign_and_serialize_transaction(
            receiver_id, self._access_key['nonce'], actions, block_hash, self._signer)

    @property
    def account_id(self) -> str:
        return self._account_id

    @property
    def signer(self) -> signer.Signer:
        return self._signer

    @property
    def provider(self) -> providers.JsonProvider:
        return self._provider

    @property
    def access_key(self) -> dict:
        return self._access_key

    @property
    def state(self) -> dict:
        return self._account

    async def fetch_state(self) -> None:
        """Fetch state for given account."""
        self._account = await self.provider.get_account(self.account_id)

    async def send_money(self, account_id: str, amount: int) -> dict:
        """Sends funds to given account_id given amount."""
        return await self._sign_and_submit_tx(account_id, [transactions.create_transfer_action(amount)])

    async def function_call(
            self,
            contract_id: str,
            method_name: str,
            args: dict,
            gas: int = DEFAULT_ATTACHED_GAS,
            amount: int = 0,
    ) -> dict:
        args = json.dumps(args).encode('utf8')
        return await self._sign_and_submit_tx(
            contract_id,
            [transactions.create_function_call_action(method_name, args, gas, amount)],
        )

    async def create_account(self, account_id: str, public_key: bytes, initial_balance: int) -> dict:
        actions = [
            transactions.create_create_account_action(),
            transactions.create_full_access_key_action(public_key),
            transactions.create_transfer_action(initial_balance),
        ]
        return await self._sign_and_submit_tx(account_id, actions)

    async def delete_account(self, beneficiary_id: str) -> dict:
        return await self._sign_and_submit_tx(self._account_id, [transactions.create_delete_account_action(beneficiary_id)])

    async def deploy_contract(self, contract_code: bytes) -> dict:
        return await self._sign_and_submit_tx(self._account_id, [transactions.create_deploy_contract_action(contract_code)])

    async def stake(self, public_key: bytes, amount: int) -> dict:
        return await self._sign_and_submit_tx(self._account_id, [transactions.create_staking_action(amount, public_key)])

    async def create_and_deploy_contract(
            self,
            contract_id: str,
            public_key: bytes,
            contract_code: bytes,
            initial_balance: int,
    ) -> dict:
        actions = [
            transactions.create_create_account_action(),
            transactions.create_transfer_action(initial_balance),
            transactions.create_deploy_contract_action(contract_code),
        ] + ([transactions.create_full_access_key_action(public_key)] if public_key is not None else [])
        return await self._sign_and_submit_tx(contract_id, actions)

    async def create_deploy_and_init_contract(
            self,
            contract_id: str,
            public_key: bytes,
            contract_code: bytes,
            initial_balance: int,
            args: bytes,
            gas: int = DEFAULT_ATTACHED_GAS,
            init_method_name: str = 'new',
    ) -> dict:
        args = json.dumps(args).encode('utf8')
        actions = [
            transactions.create_create_account_action(),
            transactions.create_transfer_action(initial_balance),
            transactions.create_deploy_contract_action(contract_code),
            transactions.create_function_call_action(init_method_name, args, gas, 0),
        ] + ([transactions.create_full_access_key_action(public_key)] if public_key is not None else [])
        return await self._sign_and_submit_tx(contract_id, actions)

    async def view_function(self, contract_id: str, method_name: str, args: dict | None = None) -> Any:
        result = await self._provider.view_call(contract_id, method_name, json.dumps(args).encode('utf8'))
        if 'error' in result:
            raise ViewFunctionError(result['error'])
        result['result'] = json.loads(''.join([chr(x) for x in result['result']]))
        return result
