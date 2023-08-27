import base64
from typing import Any, Self

import aiohttp


class FinalityTypes:
    FINAL = 'final'
    OPTIMISTIC = 'optimistic'


class JsonProviderError(Exception):
    def __init__(self, error: Any):
        self.error = error
        super().__init__(f'Provider error: {error!r}')


class JsonProvider:
    _session: aiohttp.ClientSession | None

    def __init__(self, rpc_addr: str) -> None:
        self._rpc_addr = rpc_addr
        self._session = None

    def start(self) -> None:
        if self._session is None:
            self._session = aiohttp.ClientSession()

    async def close(self) -> None:
        if self._session:
            await self._session.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    def rpc_addr(self) -> str:
        return self._rpc_addr

    async def json_rpc(self, method: str, params: dict | list | str, timeout: aiohttp.ClientTimeout | None = None) -> dict:
        j = {
            'method': method,
            'params': params,
            'id': 'dontcare',
            'jsonrpc': '2.0',
        }

        assert self._session
        async with self._session.post(self.rpc_addr(), json=j, timeout=timeout) as resp:
            resp.raise_for_status()
            content = await resp.json()
            if 'error' in content:
                raise JsonProviderError(content['error'])
            return content['result']

    async def send_tx(self, signed_tx: bytes, timeout: aiohttp.ClientTimeout | None = None) -> dict:
        return await self.json_rpc('broadcast_tx_async', [base64.b64encode(signed_tx).decode('utf8')], timeout)

    async def send_tx_and_wait(self, signed_tx: bytes, timeout: aiohttp.ClientTimeout | None = None) -> dict:
        return await self.json_rpc('broadcast_tx_commit', [base64.b64encode(signed_tx).decode('utf8')], timeout)

    async def get_status(self, timeout: aiohttp.ClientTimeout | None = None) -> dict:
        assert self._session
        async with self._session.get(f'{self.rpc_addr()}/status', timeout=timeout) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_validators(self, timeout: aiohttp.ClientTimeout | None = None) -> dict:
        return await self.json_rpc('validators', [None], timeout)

    async def query(self, query_object: dict | list | str, timeout: aiohttp.ClientTimeout | None = None) -> dict:
        return await self.json_rpc('query', query_object, timeout)

    async def get_account(
            self,
            account_id: str,
            finality: str = FinalityTypes.OPTIMISTIC,
            timeout: aiohttp.ClientTimeout | None = None,
    ) -> dict:
        return await self.query({
            'request_type': 'view_account',
            'account_id': account_id,
            'finality': finality,
        }, timeout)

    async def get_access_key_list(
            self,
            account_id: str,
            finality: str = FinalityTypes.OPTIMISTIC,
            timeout: aiohttp.ClientTimeout | None = None,
    ) -> dict:
        return await self.query({
            'request_type': 'view_access_key_list',
            'account_id': account_id,
            'finality': finality,
        }, timeout)

    async def get_access_key(
            self,
            account_id: str,
            public_key: str,
            finality: str = FinalityTypes.OPTIMISTIC,
            timeout: aiohttp.ClientTimeout | None = None,
    ) -> dict:
        return await self.query({
            'request_type': 'view_access_key',
            'account_id': account_id,
            'public_key': public_key,
            'finality': finality,
        }, timeout)

    async def view_call(
            self,
            account_id: str,
            method_name: str,
            args: bytes,
            finality: str = FinalityTypes.OPTIMISTIC,
            timeout: aiohttp.ClientTimeout | None = None,
    ) -> dict:
        return await self.query({
            'request_type': 'call_function',
            'account_id': account_id,
            'method_name': method_name,
            'args_base64': base64.b64encode(args).decode('utf8'),
            'finality': finality,
        }, timeout)

    async def get_block(
            self,
            block_id: str | int | None = None,
            finality: str | None = None,
            timeout: aiohttp.ClientTimeout | None = None,
    ) -> dict:
        params = {}
        if block_id:
            params['block_id'] = block_id
        if finality:
            params['finality'] = finality

        return await self.json_rpc('block', params, timeout)

    async def get_chunk(self, chunk_id: str, timeout: aiohttp.ClientTimeout | None = None) -> dict:
        return await self.json_rpc('chunk', {'chunk_id': chunk_id}, timeout)

    async def get_tx(self, tx_hash: str, tx_recipient_id: str, timeout: aiohttp.ClientTimeout | None = None) -> dict:
        return await self.json_rpc('tx', [tx_hash, tx_recipient_id], timeout)

    async def get_changes_in_block(
            self,
            block_id: str | None = None,
            finality: str | None = None,
            timeout: aiohttp.ClientTimeout | None = None,
    ) -> dict:
        """Use either block_id or finality. Choose finality from 'finality_types' class."""
        params = {}
        if block_id:
            params['block_id'] = block_id
        if finality:
            params['finality'] = finality

        return await self.json_rpc('EXPERIMENTAL_changes_in_block', params, timeout)

    async def get_validators_ordered(self, block_hash: bytes, timeout: aiohttp.ClientTimeout | None = None) -> dict:
        return await self.json_rpc('EXPERIMENTAL_validators_ordered', [block_hash], timeout)

    async def get_light_client_proof(
            self,
            outcome_type: str,
            tx_or_receipt_id: str,
            sender_or_receiver_id: str,
            light_client_head: str,
            timeout: aiohttp.ClientTimeout | None = None,
    ) -> dict:
        if outcome_type == 'receipt':
            params = {
                'type': 'receipt',
                'receipt_id': tx_or_receipt_id,
                'receiver_id': sender_or_receiver_id,
                'light_client_head': light_client_head,
            }
        else:
            params = {
                'type': 'transaction',
                'transaction_hash': tx_or_receipt_id,
                'sender_id': sender_or_receiver_id,
                'light_client_head': light_client_head,
            }

        return await self.json_rpc('light_client_proof', params, timeout)

    async def get_next_light_client_block(self, last_block_hash: str, timeout: aiohttp.ClientTimeout | None = None) -> dict:
        return await self.json_rpc('next_light_client_block', [last_block_hash], timeout)

    async def get_receipt(self, receipt_hash: str, timeout: aiohttp.ClientTimeout | None = None) -> dict:
        return await self.json_rpc('EXPERIMENTAL_receipt', [receipt_hash], timeout)

    async def get_tx_receipts(self, tx_hash: str, sender_id: str, timeout: aiohttp.ClientTimeout | None = None) -> dict:
        return await self.json_rpc('EXPERIMENTAL_tx_status', [tx_hash, sender_id], timeout)
