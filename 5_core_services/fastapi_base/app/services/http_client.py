import httpx

class HttpClient:
    client: httpx.AsyncClient = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls.client is None:
            cls.client = httpx.AsyncClient(timeout=10.0)
        return cls.client

    @classmethod
    async def close_client(cls):
        if cls.client is not None:
            await cls.client.aclose()
            cls.client = None

http_client = HttpClient()
