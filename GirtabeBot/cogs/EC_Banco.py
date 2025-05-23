import asyncpg
import os
import logging
from typing import Any, Optional, List, Tuple
from dotenv import load_dotenv
from asyncpg.connection import Connection
from asyncpg.transaction import Transaction
load_dotenv()
logger = logging.getLogger("Banco")


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.dsn = f"postgresql://postgres:{os.getenv('DB_PASSWORD')}@localhost:5432/Girtabe"


    async def connect(self):
        min_size = int(os.getenv("DB_POOL_MIN", 1))
        max_size = int(os.getenv("DB_POOL_MAX", 5))
        self.pool = await asyncpg.create_pool(dsn=self.dsn, min_size=min_size, max_size=max_size)
        logger.info("✅ Conectado ao banco de dados com sucesso.")


    async def initialize(self):
        await self.connect()
        # Exemplo opcional de inicialização:
        # await self.execute("""CREATE TABLE IF NOT EXISTS ...""")


    async def close(self):
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("✅ Conexão com o banco de dados encerrada.")


    async def fetch(self, query: str, *args: Any) -> List[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)


    async def fetchrow(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)


    async def fetchval(self, query: str, *args: Any) -> Any:
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)


    async def fetchcolumn(self, query: str, *args: Any) -> List[Any]:
        async with self.pool.acquire() as conn:
            results = await conn.fetch(query, *args)
            return [record[0] for record in results]


    async def execute(self, query: str, *args: Any) -> str:
        async with self.pool.acquire() as conn:
            try:
                return await conn.execute(query, *args)
            except Exception as e:
                logger.exception(f"Erro ao executar query: {query}")
                raise


    async def executemany(self, query: str, args_list: List[Tuple[Any, ...]]) -> None:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                try:
                    await conn.executemany(query, args_list)
                except Exception as e:
                    logger.exception(f"Erro ao executar múltiplas queries: {query}")
                    raise


    async def record_exists(self, query: str, *args: Any) -> bool:
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(query, *args)
            return result is not None


    def acquire(self):
        return self.pool.acquire()


    async def transaction(self) -> Tuple[Connection, Transaction]:
        conn = await self.pool.acquire()
        try:
            tr = conn.transaction()
            await tr.start()
            return conn, tr
        except Exception:
            await self.pool.release(conn)
            raise
