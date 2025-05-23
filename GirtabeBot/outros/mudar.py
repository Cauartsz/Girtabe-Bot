from discord import app_commands
from discord.ext import commands
import discord

class MudarGrupo(app_commands.Group):
    def __init__(self):
        super().__init__(name="mudar", description="Comandos administrativos para modificar configurações.")

    @app_commands.command(name="prefixo", description="Altere o prefixo do bot neste servidor.")
    @app_commands.describe(prefixo="Novo prefixo a ser definido")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def mudar_prefixo(self, interaction: discord.Interaction, prefixo: str):
        await interaction.response.defer(ephemeral=True)

        if len(prefixo) > 2:
            return await interaction.followup.send("❌ O prefixo pode ter no máximo **2 caracteres**.", ephemeral=True)

        await interaction.client.db.execute(
            """
            INSERT INTO servidores (guild_id, prefixo)
            VALUES ($1, $2)
            ON CONFLICT (guild_id) DO UPDATE SET prefixo = EXCLUDED.prefixo
            """,
            interaction.guild.id,
            prefixo
        )

        await interaction.followup.send(f"✅ Prefixo atualizado para `{prefixo}`.", ephemeral=True)

class Mudar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.tree.add_command(MudarGrupo())

async def setup(bot):
    await bot.add_cog(Mudar(bot))
