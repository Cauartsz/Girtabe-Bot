import random
import discord
from discord.ext import commands
from discord import ui
from discord import app_commands

class TopEstrelasView(ui.View):
    def __init__(self, data, bot, page=0):
        super().__init__(timeout=60)
        self.data = data
        self.bot = bot
        self.page = page
        self.per_page = 5
        self.total_pages = max(1, (len(data) + self.per_page - 1) // self.per_page)

        # Desabilita botões no início
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        self.add_item(ui.Button(label="⬅️", style=discord.ButtonStyle.primary, disabled=self.page == 0, custom_id="prev"))
        self.add_item(ui.Button(label="➡️", style=discord.ButtonStyle.primary, disabled=self.page >= self.total_pages - 1, custom_id="next"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True  # Qualquer um pode interagir

    @ui.button(label="⬅️", style=discord.ButtonStyle.primary, custom_id="prev", row=0)
    async def previous(self, interaction: discord.Interaction, button: ui.Button):
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
            self.update_buttons()

    @ui.button(label="➡️", style=discord.ButtonStyle.primary, custom_id="next", row=0)
    async def next(self, interaction: discord.Interaction, button: ui.Button):
        if self.page < self.total_pages - 1:
            self.page += 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
            self.update_buttons()

    def get_embed(self):
        start = self.page * self.per_page
        end = start + self.per_page
        ranking = self.data[start:end]

        desc = ""
        for idx, entry in enumerate(ranking, start=start + 1):
            user = self.bot.get_user(entry["user_id"])
            nome = user.name if user else f"<@{entry['user_id']}>"
            desc += f"`#{idx}` **{nome}** — {entry['qtd']} estrelas\n"

        embed = discord.Embed(
            title="🌟 Top Estrelas Global/Local",
            description=desc or "Nenhum usuário com estrelas ainda.",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Página {self.page + 1} de {self.total_pages}")
        return embed

class Estrelas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.hybrid_command(name="converter", description="Converte constelações em estrelas.")
    @app_commands.describe(constelacoes="Quantidade de constelações a converter")
    async def converter(self, ctx: commands.Context, constelacoes: int):
        if constelacoes <= 0:
            return await ctx.reply("Você deve converter pelo menos 1 constelação.", ephemeral=True)

        user_id = ctx.author.id
        guild_id = ctx.guild.id

        # Verifica se o usuário tem constelações suficientes
        resultado = await self.bot.db.fetchrow("SELECT qtd FROM constelacoes WHERE user_id = $1", user_id)
        if not resultado or resultado["qtd"] < constelacoes:
            return await ctx.reply("Você não tem constelações suficientes.", ephemeral=True)

        # Atualiza o banco de dados
        TAXA_CONVERSAO = 1000
        estrelas = constelacoes * TAXA_CONVERSAO

        async with self.bot.db.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    UPDATE constelacoes SET qtd = qtd - $1 WHERE user_id = $2
                """, constelacoes, user_id)
                await conn.execute("""
                    INSERT INTO estrelas (guild_id, user_id, qtd)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (guild_id, user_id)
                    DO UPDATE SET qtd = estrelas.qtd + $3
                """, guild_id, user_id, estrelas)

        await ctx.reply(f"Você converteu {constelacoes} constelações em {estrelas} estrelas com sucesso!")


    @commands.hybrid_command(name="cc", description="Receba uma quantia aleatória de estrelas!")
    async def constelacoes(self, ctx):
        user_id = ctx.author.id
        ganho = random.randint(100, 1000)

        try:
            await self.bot.db.execute("""
            INSERT INTO public.constelacoes (user_id, qtd)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET qtd = public.constelacoes.qtd + EXCLUDED.qtd
        """, user_id, ganho)


            await ctx.reply(f"✨ Você recebeu **{ganho}** contelacoes!", mention_author=False)
        except Exception as e:
            print(f"[Erro Interno] Falha no /claim: {e}")
            await ctx.reply("❌ Ocorreu um erro ao receber suas estrelas. Tente novamente mais tarde.", mention_author=False)


async def setup(bot):
    await bot.add_cog(Estrelas(bot))
