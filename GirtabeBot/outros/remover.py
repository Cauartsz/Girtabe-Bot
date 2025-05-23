from discord import app_commands, Interaction
from discord.ext import commands
import discord

class Remover(commands.GroupCog, name="remover"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="estrelas", description="Remove estrelas de um membro.")
    @app_commands.describe(membro="Membro que perderá estrelas", quantidade="Quantidade de estrelas a remover")
    async def estrelas(self, interaction: Interaction, membro: discord.Member, quantidade: int):
        if quantidade <= 0:
            return await interaction.response.send_message("❌ A quantidade deve ser maior que zero.", ephemeral=True)

        # Verifica saldo atual
        row = await self.bot.db.fetchrow("""
            SELECT qtd FROM estrelas WHERE guild_id = $1 AND user_id = $2
        """, interaction.guild.id, membro.id)

        saldo = row["qtd"] if row else 0

        if saldo < quantidade:
            return await interaction.response.send_message("⚠️ Esse membro não possui estrelas suficientes.", ephemeral=True)

        await self.bot.db.execute("""
            UPDATE estrelas SET qtd = qtd - $1
            WHERE guild_id = $2 AND user_id = $3
        """, quantidade, interaction.guild.id, membro.id)

        embed = discord.Embed(
            title="⭐ Estrelas removidas",
            description=f"Foram removidas `{quantidade}` estrelas de {membro.mention}.",
            color=discord.Color.yellow()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="constelacoes", description="Remove constelações de um membro.")
    @app_commands.describe(membro="Membro que perderá constelações", quantidade="Quantidade de constelações a remover")
    async def constelacoes(self, interaction: Interaction, membro: discord.Member, quantidade: int):
        if quantidade <= 0:
            return await interaction.response.send_message("❌ A quantidade deve ser maior que zero.", ephemeral=True)

        # Verifica saldo atual
        row = await self.bot.db.fetchrow("""
            SELECT qtd FROM constelacoes WHERE user_id = $1
        """, membro.id)

        saldo = row["qtd"] if row else 0

        if saldo < quantidade:
            return await interaction.response.send_message("⚠️ Esse membro não possui constelações suficientes.", ephemeral=True)

        await self.bot.db.execute("""
            UPDATE constelacoes SET qtd = qtd - $1
            WHERE user_id = $2
        """, quantidade, membro.id)

        embed = discord.Embed(
            title="🌌 Constelações removidas",
            description=f"Foram removidas `{quantidade}` constelações de {membro.mention}.",
            color=discord.Color.dark_purple()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Remover(bot))
