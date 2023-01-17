import contextlib
from typing import AsyncIterator

from nintendo.nex import backend, settings
from nintendo.nex.backend import BackEndClient
from nintendo.nnas import NNASClient

from mk8boards.common import MK8GameInfo


class MK8Client:
    async def configure(self, access_key: str, nex_version: int, client_version: int = None) -> None:
        self.settings.configure(access_key, nex_version, client_version)

    async def login(self, username: str, password: str, password_type: str = None) -> None:
        self.access_token = await self.nnas.login(username, password, password_type)
        self.nex_token = await self.nnas.get_nex_token(self.access_token.token, MK8GameInfo.GAME_SERVER_ID)

    @contextlib.asynccontextmanager
    async def backend_login(self) -> AsyncIterator[BackEndClient]:
        async with backend.connect(self.settings, self.nex_token.host, self.nex_token.port) as be:
            async with be.login(str(self.nex_token.pid), self.nex_token.password) as be_client:
                yield be_client

    def set_device(self, device_id: int, serial_number: str, system_version: int, cert: str = None) -> None:
        self.nnas.set_device(device_id, serial_number, system_version, cert)

    def set_locale(self, region_id: int, region_name: str, country_id: int,
                   country_name: str, lang: str) -> None:
        self.nnas.set_locale(region_id, country_name, lang)
        self.region_id = region_id
        self.region_name = region_name
        self.country_id = country_id
        self.country_name = country_name
        self.language = lang

    def set_title(self, title_id: int, title_version: int) -> None:
        self.nnas.set_title(title_id, title_version)

    def __init__(self):
        self.country_name = None
        self.country_id = None
        self.language = None
        self.region_name = None
        self.region_id = None

        self.access_token = None
        self.nex_token = None

        self.nnas = NNASClient()
        self.nnas.set_title(MK8GameInfo.TITLE_ID_USA, MK8GameInfo.LATEST_VERSION)

        self.settings = settings.default()
        self.settings.configure(MK8GameInfo.ACCESS_KEY, MK8GameInfo.NEX_VERSION)
