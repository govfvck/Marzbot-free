from aiogram import Dispatcher

from app.models.server import Server
from marzban_client import AuthenticatedClient


class Marzban:
    servers: dict[str, AuthenticatedClient] = dict()

    @classmethod
    def init_servers(cls, servers: list[Server]) -> None:
        for server in servers:
            cls.servers.update(
                {
                    server.id: AuthenticatedClient(
                        base_url=server.url,
                        token=server.token,
                    )
                }
            )

    @classmethod
    async def refresh_servers(cls) -> None:
        """refresh servers from database"""
        servers = await Server.all()
        cls.servers.clear()
        cls.init_servers(servers)

    @classmethod
    async def get_servers(cls) -> list["Marzban"]:
        """get Marzban server instances"""
        return cls.servers

    @classmethod
    def get_server(cls, id: int = None) -> "Marzban":
        if (server := cls.servers.get(id, None)) is None:
            raise KeyError(f"Server with id of '{id}' not found!")
        return server


def setup_api(dp: Dispatcher) -> None:
    dp.startup.register(Marzban.refresh_servers)
