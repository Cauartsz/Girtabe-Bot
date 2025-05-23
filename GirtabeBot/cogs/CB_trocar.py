from discord import app_commands, Interaction
from discord.ext import commands
import discord
import os


#GRUPO
class TrocarGrupo(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="trocar")
        self.bot = bot


    #TROCAR CONSTELAÇÕES (OK)
    @app_commands.command(name="constelações", description="Troque suas constelações por estrelas!")
    @app_commands.describe(quantidade="Quantia de constelações que deseja trocar...")
    async def trocar_constelacoes(self, interaction: discord.Interaction, quantidade: int):

        await interaction.response.defer()

        if quantidade <= 0:
            return await interaction.followup.send("Você deve trocar pelo menos 1 constelação.", ephemeral=True)

        guild_id = interaction.guild.id
        user_id = interaction.user.id

        #Verifica se o usuário tem constelações suficientes
        resultado = await self.bot.db.fetchrow("SELECT constellations FROM users WHERE userid = $1", user_id)
        if not resultado or resultado["constellations"] < quantidade:
            return await interaction.followup.send("Você não tem constelações suficientes para fazer isso. Insira um valor que você possui.", ephemeral=True)

        if quantidade:
            await self.bot.db.execute("""
                INSERT INTO users (userid) VALUES ($1)
                ON CONFLICT (userid) DO NOTHING
            """, user_id)

        # Atualiza o banco de dados
        TAXA_CONVERSAO = 1000
        estrelas = quantidade * TAXA_CONVERSAO

        async with self.bot.db.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    UPDATE users SET constellations = constellations - $1 WHERE userid = $2
                """, quantidade, user_id)
                await conn.execute("""
                    INSERT INTO userperguild (guildid, userid, stars)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (guildid, userid)
                    DO UPDATE SET stars = userperguild.stars + $3
                """, guild_id, user_id, estrelas)

        qtd_fmt = f"{quantidade:,}".replace(",", ".")
        qtd_fmt2 = f"{estrelas:,}".replace(",", ".")
        await interaction.followup.send(f"Você trocou **{qtd_fmt}** constelações e recebeu **{qtd_fmt2}** estrelas com sucesso!")


class Trocar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trocar_grupo = TrocarGrupo(bot)
        self.bot.tree.add_command(self.trocar_grupo)

    def adicionar_cog_unload(self):
        self.bot.tree.remove_command(self.trocar_grupo.name)

async def setup(bot):
    await bot.add_cog(Trocar(bot))
