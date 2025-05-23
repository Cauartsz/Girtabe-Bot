from discord.ext import tasks, commands
from datetime import datetime, timezone

class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.limpar_parcerias_expiradas.start()

    def cog_unload(self):
        self.limpar_parcerias_expiradas.cancel()

    @tasks.loop(minutes=30)  # roda a cada 30 minutos
    async def limpar_parcerias_expiradas(self):
        try:
            registros = await self.bot.db.fetch("""
                SELECT guild_id, server_id, role_id
                FROM parcerias
                WHERE renovacao + duracao < NOW()
            """)

            for row in registros:
                server = self.bot.get_guild(row["server_id"])
                if server:
                    role = server.get_role(row["role_id"])
                    if role:
                        try:
                            await role.delete(reason="Parceria expirada")
                        except Exception as e:
                            print(f"[Erro] Falha ao deletar cargo de parceria: {e}")

            # Deleta os registros do banco
            await self.bot.db.execute("""
                DELETE FROM parcerias
                WHERE renovacao + duracao < NOW()
            """)
            print(f"[Tarefa] Parcerias expiradas removidas com sucesso.")

        except Exception as e:
            print(f"[Erro] Falha ao limpar parcerias expiradas: {e}")

    @limpar_parcerias_expiradas.before_loop
    async def before_task(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Tasks(bot))
