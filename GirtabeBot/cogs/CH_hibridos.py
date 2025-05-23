from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import discord
import random
import time


class Hibridos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



    #CARTEIRA - BAL (ok)
    @commands.hybrid_command(name="carteira", description="Veja quantas estrelas e constelações alguém possui", aliases=["bal"])
    @app_commands.describe(membro="Veja a carteira deste membro!")
    async def carteira_command(self, ctx: commands.Context, membro: discord.Member = None):

        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)
        else:
            await ctx.defer()

        member = membro or ctx.author

        if member.bot:
            return await ctx.reply("Bots não possuem carteira...", ephemeral=True)

        user_id = member.id
        guild_id = ctx.guild.id

        try:
            # Buscar estrelas (por servidor)
            estrelas_result = await self.bot.db.fetchrow("""
                SELECT stars FROM public.userperguild WHERE userid = $1 AND guildid = $2
            """, user_id, guild_id)
            estrelas = estrelas_result["stars"] if estrelas_result else 0

            # Buscar constelações (global)
            constelacoes_result = await self.bot.db.fetchrow("""
                SELECT constellations FROM public.users WHERE userid = $1
            """, user_id)
            constelacoes = constelacoes_result["constellations"] if constelacoes_result else 0

            embed = discord.Embed(
                title=f"Carteira de {member.display_name}",
                color=discord.Color.blurple()
            )
            embed.set_thumbnail(url=member.display_avatar.url)

            estrelas_fmt = f"{estrelas:,}".replace(",", ".")
            constelacoes_fmt = f"{constelacoes:,}".replace(",", ".")

            embed.add_field(name="<:constelacao:1375218065297510471> Constelações (Global)", value=f"{constelacoes_fmt}", inline=False)
            embed.add_field(name="<:star:1375219269373132800> Estrelas (Local)", value=f"{estrelas_fmt}", inline=False)

            await ctx.reply(embed=embed, mention_author=False, ephemeral=True)

        except Exception as e:
            print(f"[Erro Interno] Falha ao buscar saldo: {e}")
            await ctx.reply("Ocorreu um erro ao consultar seu saldo. Tente novamente mais tarde.", mention_author=False, ephemeral=True)


    #DAILY ()
    @commands.hybrid_command(name="daily", description="Lance um dado diário, avance no tabuleiro e ganhe recompensas!")
    async def daily_command(self, ctx: commands.Context):
        
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)
        else:
            await ctx.defer()

        user_id = ctx.author.id
        guild_id = ctx.guild.id
        now = datetime.now(timezone.utc)

        # Buscar progresso atual do usuário
        row = await self.bot.db.fetchrow("""
            SELECT lastdaily, dailyspot FROM users WHERE userid = $1
        """, user_id)

        last_daily = row["lastdaily"] if row and row["lastdaily"] else None
        dailyspot = row["dailyspot"] if row and row["dailyspot"] is not None else 0

        # Verifica se o usuário já usou o daily hoje
        if last_daily:
            if last_daily.tzinfo is None:
                last_daily = last_daily.replace(tzinfo=timezone.utc)
            else:
                last_daily = last_daily.astimezone(timezone.utc)

            delta = now - last_daily
            if delta < timedelta(hours=24):
                restante = timedelta(hours=24) - delta
                horas, resto = divmod(int(restante.total_seconds()), 3600)
                minutos, _ = divmod(resto, 60)
                return await ctx.reply(
                    f"Você já lançou o dado hoje! Tente novamente em **{horas}h {minutos}min**.",
                    ephemeral=True
                )

        # Gerar número do dado (1 a 6)
        dado = random.randint(1, 6)
        ganho = dado * 1000
        nova_casa = dailyspot + dado

        recompensa_constelacao = False

        async with self.bot.db.acquire() as conn:
            async with conn.transaction():

                # Adiciona estrelas ao servidor
                await conn.execute("""
                    INSERT INTO userperguild (guildid, userid, stars)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (guildid, userid)
                    DO UPDATE SET stars = userperguild.stars + EXCLUDED.stars
                """, guild_id, user_id, ganho)

                # Verifica se chegou na última casa
                if nova_casa >= 20:
                    recompensa_constelacao = True

                    # Dá constelação
                    await conn.execute("""
                        INSERT INTO users (userid, lastdaily, dailyspot, constelacoes)
                        VALUES ($1, $2, 0, 1)
                        ON CONFLICT (userid) DO UPDATE
                        SET lastdaily = EXCLUDED.lastdaily,
                            dailyspot = 0,
                            constelacoes = users.constelacoes + 1
                    """, user_id, now)

                    # Reseta todos os dailyspot para 0
                    await conn.execute("""
                        UPDATE users SET dailyspot = 0
                    """)

                else:
                    # Apenas atualiza posição e lastdaily
                    await conn.execute("""
                        INSERT INTO users (userid, lastdaily, dailyspot)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (userid) DO UPDATE
                        SET lastdaily = EXCLUDED.lastdaily,
                            dailyspot = EXCLUDED.dailyspot
                    """, user_id, now, nova_casa)

                # Novo saldo
                novo_saldo = await conn.fetchval("""
                    SELECT stars FROM userperguild WHERE guildid = $1 AND userid = $2
                """, guild_id, user_id)

        # Montar embed de resposta
        embed = discord.Embed(
            title="🎲 Daily Roll!",
            description=(
                f"Você lançou um dado e tirou **{dado}**!\n"
                f"➡ Avançou **{dado} casas** no tabuleiro (posição: **{nova_casa if not recompensa_constelacao else 20} de 20**).\n"
                f"⭐ Recebeu **{ganho} estrelas**.\n"
                f"💰 Novo saldo: **{novo_saldo} estrelas**\n"
            ),
            color=discord.Color.gold()
        )

        if recompensa_constelacao:
            embed.add_field(name="🌟 Parabéns!", value="Você chegou na última casa e ganhou **1 constelação**!\nO tabuleiro foi reiniciado para todos!")

        await ctx.reply(embed=embed, ephemeral=True)


    #PING ()
    @commands.hybrid_command(name="ping", description="Exibe a latência do bot.")
    async def ping(self, ctx: commands.Context):
        ws_latency = round(self.bot.latency * 1000)
        start = time.perf_counter()
        msg = await ctx.send(f" 🏓 Pong!\n⌚ ┃ **WebSocket:** `{ws_latency}ms`\n⚡ ┃ **API:** `...ms`")
        end = time.perf_counter()
        api_latency = round((end - start) * 1000)
        await msg.edit(content=f" 🏓 Pong!\n⌚ ┃ **WebSocket:** `{ws_latency}ms`\n⚡ ┃ **API:** `{api_latency}ms`")


async def setup(bot):
    await bot.add_cog(Hibridos(bot))
