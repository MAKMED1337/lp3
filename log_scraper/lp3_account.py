import json
from typing import Any

from pydantic import BaseModel, TypeAdapter

from .logs import Logs, LogsParams
from .nearcrowd_account import V2, NearCrowdAccount


class Permission(BaseModel):
    user_id: str
    mask: int
    accepted: bool


class FarmInvite(BaseModel):
    accepted: bool
    can_logs: bool
    farm_id: int
    is_admin: bool
    is_mod: bool
    name: str
    owner_id: str
    task_id: int


class LP3Account(NearCrowdAccount):
    farm_id: int

    def __init__(self, account_id: str, private_key: str, farm_id: int):
        super().__init__(account_id, private_key)
        self.farm_id = farm_id

    async def query(self, q: V2, prefix: str = 'v2/lp3/') -> str | None:
        q.path = prefix + q.path
        q.args['farm_id'] = self.farm_id
        return await super().query(q)

    async def update_permissions(self, user_id: str, permission: int, action: str) -> None:
        await self.query(V2(path='update_permissions', args={'user_id': user_id, 'permission': permission, 'action': action}))

    async def delete_user(self, user_id: str) -> None:
        await self.query(V2(path='delete_user', args={'user_id': user_id}))

    async def add_user(self, user_id: str) -> None:
        await self.query(V2(path='add_user', args={'user_id': user_id}))

    async def get_permissions(self) -> list[Permission]:
        adapter = TypeAdapter(list[Permission])
        return adapter.validate_json(await self.query(V2(path='get_permissions')), strict=False)  #type: ignore[arg-type]

    async def get_books(self) -> list[FarmInvite]:
        adapter = TypeAdapter(list[FarmInvite])
        return adapter.validate_json(await self.query(V2(path='get_tasks')), strict=False)  #type: ignore[arg-type]

    async def accept_invitation(self) -> None:
        await self.query(V2(path='accept_invitation'))

    async def get_logs(self, options: LogsParams = LogsParams()) -> list[Logs]:  # noqa: B008
        logs = json.loads(await self.query(V2(path='v2/logs', args=options.model_dump(exclude_none=True)), ''))  #type: ignore[arg-type]
        for i in logs:
            i['data'] = json.loads(i['data'])
        return [Logs(**i) for i in logs]
