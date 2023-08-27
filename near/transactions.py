import hashlib
from typing import Annotated

from . import signer
from .serializer import BinarySerializer


class FunctionCallPermission:
    allowance: int | None
    receiver_id: str
    method_names: list[str]


class FullAccessPermission:
    pass


class AccessKeyPermission:
    enum: FunctionCallPermission | FullAccessPermission


class AccessKey:
    nonce: int
    permission: AccessKeyPermission


class PublicKey:
    key_type: int
    data: Annotated[bytes, 32]


class Signature:
    key_type: int
    data: Annotated[bytes, 64]


class CreateAccount:
    pass


class DeployContract:
    code: bytes


class FunctionCall:
    method_name: str
    args: bytes
    gas: int
    deposit: int


class Transfer:
    deposit: int


class Stake:
    stake: int
    public_key: PublicKey


class AddKey:
    access_key: AccessKey
    public_key: PublicKey


class DeleteKey:
    public_key: PublicKey


class DeleteAccount:
    beneficiary_id: str


class Action:
    enum: CreateAccount | DeployContract | FunctionCall | Transfer | Stake | AddKey | DeleteKey | DeleteAccount


class Transaction:
    signer_id: str
    public_key: PublicKey
    nonce: int
    receiver_id: str
    block_hash: Annotated[bytes, 32]
    actions: list[Action]


class SignedTransaction:
    transaction: Transaction
    signature: Signature


tx_schema = {
    Signature: {
        'kind': 'struct',
        'fields': [
            ['key_type', 'u8'],
            ['data', [64]],
        ],
    },
    SignedTransaction: {
        'kind': 'struct',
        'fields': [
            ['transaction', Transaction],
            ['signature', Signature],
        ],
    },
    Transaction: {
        'kind': 'struct',
        'fields': [
            ['signer_id', 'string'],
            ['public_key', PublicKey],
            ['nonce', 'u64'],
            ['receiver_id', 'string'],
            ['block_hash', [32]],
            ['actions', [Action]],
        ],
    },
    PublicKey: {
        'kind': 'struct',
        'fields': [
            ['key_type', 'u8'],
            ['data', [32]],
        ],
    },
    AccessKey: {
        'kind': 'struct',
        'fields': [
            ['nonce', 'u64'],
            ['permission', AccessKeyPermission],
        ],
    },
    AccessKeyPermission: {
        'kind': 'enum',
        'field': 'enum',
        'values': [
            FunctionCallPermission,
            FullAccessPermission,
        ],
    },
    FunctionCallPermission: {
        'kind': 'struct',
        'fields': [
            ['allowance', {'kind': 'option', type: 'u128'}],
            ['receiver_id', 'string'],
            ['method_names', ['string']],
        ],
    },
    FullAccessPermission: {
        'kind': 'struct',
        'fields': [],
    },
    Action: {
        'kind': 'enum',
        'field': 'enum',
        'values': [
            CreateAccount,
            DeployContract,
            FunctionCall,
            Transfer,
            Stake,
            AddKey,
            DeleteKey,
            DeleteAccount,
        ],
    },
    CreateAccount: {
        'kind': 'struct',
        'fields': [],
    },
    DeployContract: {
        'kind': 'struct',
        'fields': [
            ['code', ['u8']],
        ],
    },
    FunctionCall: {
        'kind': 'struct',
        'fields': [
            ['method_name', 'string'],
            ['args', ['u8']],
            ['gas', 'u64'],
            ['deposit', 'u128'],
        ],
    },
    Transfer: {
        'kind': 'struct',
        'fields': [
            ['deposit', 'u128'],
        ],
    },
    Stake: {
        'kind': 'struct',
        'fields': [
            ['stake', 'u128'],
            ['public_key', PublicKey],
        ],
    },
    AddKey: {
        'kind': 'struct',
        'fields': [
            ['public_key', PublicKey],
            ['access_key', AccessKey],
        ],
    },
    DeleteKey: {
        'kind': 'struct',
        'fields': [
            ['public_key', PublicKey],
        ],
    },
    DeleteAccount:
    {
        'kind': 'struct',
        'fields': [
            ['beneficiary_id', 'string'],
        ],
    },
}


def sign_and_serialize_transaction(
        receiver_id: str,
        nonce: int,
        actions: list[Action],
        block_hash: bytes,
        signer: signer.Signer,
) -> bytes:
    assert signer.public_key is not None    # TODO: Need to replace to Exception
    assert block_hash is not None    # TODO: Need to replace to Exception
    tx = Transaction()
    tx.signer_id = signer.account_id
    tx.public_key = PublicKey()
    tx.public_key.key_type = 0
    tx.public_key.data = signer.public_key
    tx.nonce = nonce
    tx.receiver_id = receiver_id
    tx.actions = actions
    tx.block_hash = block_hash

    msg: bytes = BinarySerializer(tx_schema).serialize(tx)
    hash_: bytes = hashlib.sha256(msg).digest()

    signature = Signature()
    signature.key_type = 0
    signature.data = signer.sign(hash_)

    signed_tx = SignedTransaction()
    signed_tx.transaction = tx
    signed_tx.signature = signature

    return BinarySerializer(tx_schema).serialize(signed_tx)


def create_create_account_action() -> Action:
    create_account = CreateAccount()
    action = Action()
    action.enum = create_account
    return action


def create_delete_account_action(beneficiary_id: str) -> Action:
    delete_account = DeleteAccount()
    delete_account.beneficiary_id = beneficiary_id
    action = Action()
    action.enum = delete_account
    return action


def create_full_access_key_action(pk: bytes) -> Action:
    permission = AccessKeyPermission()
    permission.enum = FullAccessPermission()
    access_key = AccessKey()
    access_key.nonce = 0
    access_key.permission = permission
    public_key = PublicKey()
    public_key.key_type = 0
    public_key.data = pk
    add_key = AddKey()
    add_key.access_key = access_key
    add_key.public_key = public_key
    action = Action()
    action.enum = add_key
    return action


def create_delete_access_key_action(pk: bytes) -> Action:
    public_key = PublicKey()
    public_key.key_type = 0
    public_key.data = pk
    delete_key = DeleteKey()
    delete_key.public_key = public_key
    action = Action()
    action.enum = delete_key
    return action


def create_transfer_action(amount: int) -> Action:
    transfer = Transfer()
    transfer.deposit = amount
    action = Action()
    action.enum = transfer
    return action


# TODO: deprecate usage of create_payment_action.
create_payment_action = create_transfer_action


def create_staking_action(amount: int, pk: bytes) -> Action:
    stake = Stake()
    stake.stake = amount
    stake.public_key = PublicKey()
    stake.public_key.key_type = 0
    stake.public_key.data = pk
    action = Action()
    action.enum = stake
    return action


def create_deploy_contract_action(code: bytes) -> Action:
    deploy_contract = DeployContract()
    deploy_contract.code = code
    action = Action()
    action.enum = deploy_contract
    return action


def create_function_call_action(method_name: str, args: bytes, gas: int, deposit: int) -> Action:
    function_call = FunctionCall()
    function_call.method_name = method_name
    function_call.args = args
    function_call.gas = gas
    function_call.deposit = deposit
    action = Action()
    action.enum = function_call
    return action


def sign_create_account_tx(
        creator_signer: signer.Signer,
        new_account_id: str,
        nonce: int,
        block_hash: bytes,
) -> bytes:
    action = create_create_account_action()
    return sign_and_serialize_transaction(new_account_id, nonce, [action], block_hash, creator_signer)


def sign_create_account_with_full_access_key_and_balance_tx(
        signer: signer.Signer,
        new_account_id: str,
        public_key: bytes,
        balance: int,
        nonce: int,
        block_hash: bytes,
) -> bytes:
    create_account_action = create_create_account_action()
    full_access_key_action = create_full_access_key_action(public_key)
    payment_action = create_transfer_action(balance)
    actions = [create_account_action, full_access_key_action, payment_action]
    return sign_and_serialize_transaction(new_account_id, nonce, actions, block_hash, signer)


def sign_delete_access_key_tx(
        signer: signer.Signer,
        target_account_id: str,
        key_for_deletion: bytes,
        nonce: int,
        block_hash: bytes,
) -> bytes:
    action = create_delete_access_key_action(key_for_deletion)
    return sign_and_serialize_transaction(target_account_id, nonce, [action], block_hash, signer)


def sign_payment_tx(
        signer: signer.Signer,
        receiver_id: str,
        amount: int,
        nonce: int,
        block_hash: bytes,
) -> bytes:
    action = create_transfer_action(amount)
    return sign_and_serialize_transaction(receiver_id, nonce, [action], block_hash, signer)


def sign_staking_tx(
        signer: signer.Signer,
        validator_key: bytes,
        amount: int,
        nonce: int,
        block_hash: bytes,
) -> bytes:
    action = create_staking_action(amount, validator_key)
    return sign_and_serialize_transaction(signer.account_id, nonce, [action], block_hash, signer)


def sign_deploy_contract_tx(
        signer: signer.Signer,
        code: bytes,
        nonce: int,
        block_hash: bytes,
) -> bytes:
    action = create_deploy_contract_action(code)
    return sign_and_serialize_transaction(signer.account_id, nonce, [action], block_hash, signer)


def sign_function_call_tx(
        signer: signer.Signer,
        contract_id: str,
        method_name: str,
        args: bytes,
        gas: int,
        deposit: int,
        nonce: int,
        block_hash: bytes,
) -> bytes:
    action = create_function_call_action(method_name, args, gas, deposit)
    return sign_and_serialize_transaction(contract_id, nonce, [action], block_hash, signer)
