from discord import app_commands
from discord.ext import commands
import discord
from datetime import datetime, timezone
from pytz import timezone

class VerGrupo(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="ver", description="...")
        self.bot = bot

    @app_commands.command(name="cargos", description="Lista os cargos temporários ativos de um membro.")
    @app_commands.describe(membro="Membro para listar os cargos temporários")
    async def ver_cargos(self, interaction: discord.Interaction, membro: discord.Member = None):

        await interaction.response.defer(ephemeral=True)

        if membro is None:
            membro = interaction.user
        
        registros = await interaction.client.db.fetch("""
            SELECT role_id, duracao FROM cargos_temporarios
            WHERE guild_id = $1 AND user_id = $2
        """, interaction.guild.id, membro.id)

        if not registros:
            return await interaction.followup.send(
                f"{membro.mention} não possui cargos temporários ativos.")

        linhas = []
        fuso_brasil = timezone("America/Sao_Paulo")
        agora = datetime.now(fuso_brasil)

        for registro in registros:
            cargo = interaction.guild.get_role(registro["role_id"])
            if not cargo:
                continue
            expiracao = registro["duracao"].astimezone(fuso_brasil)
            restante = expiracao - agora


            dias = restante.days
            horas, resto = divmod(restante.seconds, 3600)
            minutos = resto // 60

            tempo_formatado = []
            if dias > 0:
                tempo_formatado.append(f"{dias} dias")
            if horas > 0:
                tempo_formatado.append(f"{horas} horas")
            if minutos > 0:
                tempo_formatado.append(f"{minutos} minutos")
            if not tempo_formatado:
                tempo_formatado.append("menos de 1 minuto")

            linhas.append(f"{cargo.mention} – expira em {' '.join(tempo_formatado)}.")

        descricao = "\n".join(linhas)

        embed = discord.Embed(
            title=f"Cargos temporários de {membro.display_name}",
            description=descricao,
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)


    @app_commands.command(name="prefixo", description="Mostra o prefixo atual do servidor")
    async def ver_prefixo(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        registro = await self.bot.db.fetchrow(
            "SELECT sinal FROM prefixo WHERE guild_id = $1", interaction.guild.id
        )

        prefixo = registro["sinal"] if registro else ","
        await interaction.followup.send(f"O prefixo atual é `{prefixo}`", ephemeral=True)


class Ver(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ver_grupo = VerGrupo(bot)
        self.bot.tree.add_command(self.ver_grupo)

async def setup(bot):
    await bot.add_cog(Ver(bot))