from discord import app_commands, Interaction
from discord.ext import commands
import discord
import random
from datetime import datetime, timedelta, timezone
from cogs.EC_Views import EstrelasRankingView


class RankGrupo(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="rank")
        self.bot = bot


    #RANK LOCAL DE ESTRELAS (OK)
    @app_commands.command(name="estrelas", description="Veja quantas estrelas você possui e o ranking local.")
    async def rank_estrelas(self, interaction: Interaction):

        await interaction.response.defer()

        user_id = interaction.user.id
        guild_id = interaction.guild.id

        #Buscar estrelas do usuário no servidor atual
        resultado = await self.bot.db.fetchrow(
            "SELECT stars FROM userperguild WHERE guildid = $1 AND userid = $2",
            guild_id, user_id
        )
        estrelas = resultado["stars"] if resultado else 0

        #Buscar ranking local
        ranking = await self.bot.db.fetch("""
            SELECT userid, stars
            FROM userperguild
            WHERE guildid = $1
            ORDER BY stars DESC
        """, guild_id)

        view = EstrelasRankingView(bot=self.bot, data=ranking, guild_id=guild_id)
        embed = await view.criar_embed(interaction)  # NOVO: gera o embed fora
        await interaction.followup.send(embed=embed, view=view)  # Envia com followup


    # 
    @app_commands.command(name="constelações", description="Veja quantas constelações globais você possui.")
    async def rank_constelacoes(self, interaction: Interaction):
        user_id = interaction.user.id

        resultado = await self.bot.db.fetchrow(
            "SELECT constellations FROM users WHERE userid = $1",
            user_id
        )

        consts = resultado["constellations"] if resultado else 0

        await interaction.response.send_message(
            f"🌌 Você possui **{consts:,} constelações**.", ephemeral=True
        )


    # 
    @app_commands.command(name="daily", description="Receba estrelas diárias com base no dado do tabuleiro.")
    async def rank_daily(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id
        guild_id = interaction.guild.id
        now = datetime.now(timezone.utc)

        row = await self.bot.db.fetchrow("SELECT lastdaily, dailyspot FROM users WHERE userid = $1", user_id)
        last_daily = row["lastdaily"] if row else None
        dailyspot = row["dailyspot"] if row and "dailyspot" in row else 0

        # Verifica cooldown
        if last_daily:
            if last_daily.tzinfo is None:
                last_daily = last_daily.replace(tzinfo=timezone.utc)
            else:
                last_daily = last_daily.astimezone(timezone.utc)

            remaining = timedelta(hours=24) - (now - last_daily)
            if remaining.total_seconds() > 0:
                horas, resto = divmod(int(remaining.total_seconds()), 3600)
                minutos, _ = divmod(resto, 60)
                return await interaction.followup.send(
                    f"⏳ Você já coletou sua recompensa diária. Tente novamente em **{horas}h {minutos}m**.",
                    ephemeral=True
                )

        dado = random.randint(1, 6)
        ganho = dado * 1000
        nova_casa = dailyspot + dado

        # Se chegou ou passou da casa 20
        ganhou_constelacao = nova_casa >= 20
        nova_casa = 0 if ganhou_constelacao else nova_casa

        async with self.bot.db.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    INSERT INTO users (userid, lastdaily, dailyspot, vitorias)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (userid) DO UPDATE
                    SET lastdaily = EXCLUDED.lastdaily,
                        dailyspot = EXCLUDED.dailyspot,
                        vitorias = users.vitorias + $4
                """, user_id, now, nova_casa, 1 if ganhou_constelacao else 0)

                await conn.execute("""
                    INSERT INTO userperguild (guildid, userid, stars)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (guildid, userid)
                    DO UPDATE SET stars = userperguild.stars + EXCLUDED.stars
                """, guild_id, user_id, ganho)

                if ganhou_constelacao:
                    await conn.execute("""
                        UPDATE users SET constellations = constellations + 1 WHERE userid = $1
                    """, user_id)

        embed = discord.Embed(
            title="🎲 Daily do Tabuleiro!",
            description=(
                f"Você rolou um **{dado}** e ganhou **{ganho:,} estrelas**!\n"
                f"🔢 Progresso no tabuleiro: {'✅ Finalizado! +1 constelação' if ganhou_constelacao else f'casa {nova_casa}/20'}"
            ),
            color=discord.Color.blue()
        )

        await interaction.followup.send(embed=embed, ephemeral=True)



class Rank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rank_grupo = RankGrupo(bot)
        self.bot.tree.add_command(self.rank_grupo)

    def cog_unload(self):
        self.bot.tree.remove_command(self.rank_grupo.name)


async def setup(bot):
    await bot.add_cog(Rank(bot))
