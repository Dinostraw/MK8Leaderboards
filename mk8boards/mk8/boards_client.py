from nintendo import nnas
from nintendo.games import MK8
from nintendo.nex import settings


class MK8Client:
    async def login(self) -> None:
        self.access_token = await self.nnas.login(self.username, self.password)
        self.nex_token = await self.nnas.get_nex_token(self.access_token.token, MK8.GAME_SERVER_ID)

    # Perhaps use this as a wrapper function instead of repeating code?
    # async def connect_and_run(self, func: Callable, *args, **kwargs) -> Any:
    #     async with backend.connect(self.settings, self.nex_token.host, self.nex_token.port) as be:
    #         async with be.login(str(self.nex_token.pid), self.nex_token.password) as client:
    #             ranking_client = RankingClient(client)
    #             return await func(ranking_client, *args, **kwargs)

    def __init__(self, device_id: int, serial_num: str, system_ver: int, country_id: int,
                 country_name: str, region_id: int, region_name: str, lang: str,
                 username: str, password: str):
        self.device_id = device_id
        self.serial_num = serial_num
        self.system_ver = system_ver
        self.country_id = country_id
        self.country_name = country_name
        self.region_id = region_id
        self.region_name = region_name
        self.lang = lang
        self.username = username
        self.password = password

        self.nnas = nnas.NNASClient()
        self.nnas.set_device(self.device_id, self.serial_num, self.system_ver)
        self.nnas.set_title(MK8.TITLE_ID_EUR, MK8.LATEST_VERSION)
        self.nnas.set_locale(self.region_id, self.country_name, self.lang)
        self.settings = settings.default()
        self.settings.configure(MK8.ACCESS_KEY, MK8.NEX_VERSION)
        self.access_token = None
        self.nex_token = None
