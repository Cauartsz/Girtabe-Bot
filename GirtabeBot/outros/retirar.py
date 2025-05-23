from discord import app_commands
from discord.ext import commands, tasks
import discord
from datetime import datetime, timedelta

class RetirarGrupo(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="retirar", description="...")
        self.bot = bot

    @app_commands.command(name="cargo", description="Remove um cargo de um membro")
    @app_commands.describe(membro="Membro que terá o cargo removido",cargo="Cargo a ser removido")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    async def retirar_cargo(self, interaction: discord.Interaction, membro: discord.Member, cargo: discord.Role):

        await interaction.response.defer(ephemeral=True)

        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.followup.send("Você não tem permissão para usar este comando.", ephemeral=True)

        if cargo not in membro.roles:
            return await interaction.followup.send(f"{membro.mention} não possui o cargo {cargo.mention}.", ephemeral=True)

        await membro.remove_roles(cargo, reason=f"Cargo removido por {interaction.user}")
        await interaction.client.db.execute("""
            DELETE FROM cargos_temporarios
            WHERE guild_id = $1 AND user_id = $2 AND role_id = $3
        """, interaction.guild.id, membro.id, cargo.id)

        await interaction.followup.send(f"{cargo.mention} foi removido de {membro.mention}.")
   
class Retirar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.retirar_grupo = RetirarGrupo(bot)
        self.bot.tree.add_command(self.retirar_grupo)
        self.verificar_cargos.start()

    def retirar_cog_unload(self):
        self.bot.tree.remove_command(self.retirar_grupo.name)
        self.verificar_cargos.cancel()

    @tasks.loop(minutes=1)
    async def verificar_cargos(self):
        agora = datetime.utcnow()
        registros = await self.bot.db.fetch("""
            SELECT guild_id, user_id, role_id FROM cargos_temporarios
            WHERE duracao <= $1
        """, agora)

        for registro in registros:
            guild = self.bot.get_guild(registro["guild_id"])
            if not guild:
                continue
            membro = guild.get_member(registro["user_id"])
            cargo = guild.get_role(registro["role_id"])
            if membro and cargo:
                await membro.remove_roles(cargo, reason="Cargo temporário expirado")
                await self.bot.db.execute("""
                    DELETE FROM cargos_temporarios
                    WHERE guild_id = $1 AND user_id = $2 AND role_id = $3
                """, registro["guild_id"], registro["user_id"], registro["role_id"])

async def setup(bot):
    await bot.add_cog(Retirar(bot))
