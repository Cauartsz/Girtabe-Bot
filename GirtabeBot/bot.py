#BIBLIOTECAS
import discord
from discord.ext import commands
from discord import app_commands
from cogs.EC_Setup import INTENTS, PREFIX, TOKEN
from cogs.EC_Banco import Database
from pathlib import Path
import logging

#LOGS
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)
logger = logging.getLogger("Main")

#CLASSE BOT
class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=PREFIX, intents=INTENTS)
        self.db = Database() #BANCO
        self.remove_command("help")  #REMOVER HELP PADRÃO


    async def setup_hook(self):
        await self.db.connect() #CONEXÃO COM O BANCO

        ignorar_cogs = {"EC_Banco", "EC_Setup", "EC_Views", "__init__"}
        for file in Path("cogs").glob("*.py"):  # CARREGAR COGS
            stem = file.stem
            if stem in ignorar_cogs:
                continue
            try:
                await self.load_extension(f"cogs.{stem}")
                logger.info(f"✅ Extensão carregada: {stem}")
            except Exception as e:
                logger.error(f"❌ Erro na Extensão {stem}: {e}")

        await self.tree.sync() #SINCRONIZAR COMANDOS


    async def on_ready(self):

        comandos = self.tree.get_commands()
        grupos = [c for c in comandos if isinstance(c, app_commands.Group)]
        subcomandos = sum(len(g.commands) for g in grupos)
        diretos = len(comandos) - len(grupos)
        logger.info(f"✅ {len(self.extensions)} Extensões carregadas.")
        logger.info(f"✅ {diretos} comandos diretos e {subcomandos} subcomandos.")
        logger.info(f"✅ Conectado como {self.user} em {len(self.guilds)} servidores.")


    async def close(self):
        await self.db.close()
        await super().close()


bot = Bot()
bot.run(TOKEN)
