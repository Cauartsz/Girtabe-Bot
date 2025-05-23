import random
import discord
from discord.ext import commands
from discord import ui

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
            user = self.bot.get_user(entry["usuario_id"])
            nome = user.name if user else f"<@{entry['usuario_id']}>"
            desc += f"`#{idx}` **{nome}** — {entry['quantidade']} estrelas\n"

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

    @commands.hybrid_command(name="claim", description="Receba uma quantia aleatória de estrelas!")
    async def estrelas(self, ctx):
        user_id = ctx.author.id
        ganho = random.randint(100, 1000)

        try:
            await self.bot.db.execute("""
            INSERT INTO public.estrelas (usuario_id, quantidade)
            VALUES ($1, $2)
            ON CONFLICT (usuario_id)
            DO UPDATE SET quantidade = public.estrelas.quantidade + EXCLUDED.quantidade
        """, user_id, ganho)


            await ctx.reply(f"✨ Você recebeu **{ganho}** estrelas!", mention_author=False)
        except Exception as e:
            print(f"[Erro Interno] Falha no /claim: {e}")
            await ctx.reply("❌ Ocorreu um erro ao receber suas estrelas. Tente novamente mais tarde.", mention_author=False)


    @commands.hybrid_command(name="bal", description="Veja quantas estrelas você possui.")
    async def minhas_estrelas(self, ctx):
        user_id = ctx.author.id
        try:
            result = await self.bot.db.fetch("""
                SELECT quantidade FROM public.estrelas WHERE usuario_id = $1
            """, user_id)
            quantidade = result[0]["quantidade"] if result else 0
            await ctx.reply(f"🌟 Você possui **{quantidade}** estrelas!", mention_author=False)
        except Exception as e:
            print(f"[Erro Interno] Falha ao buscar estrelas: {e}")
            await ctx.reply("❌ Ocorreu um erro ao consultar suas estrelas. Tente novamente mais tarde.", mention_author=False)

    @commands.hybrid_command(name="top", description="Veja quem tem mais estrelas globalmente!")
    async def topestrelas(self, ctx):
        try:
            data = await self.bot.db.fetch("""
                SELECT usuario_id, quantidade
                FROM public.estrelas
                WHERE quantidade > 0
                ORDER BY quantidade DESC
            """)

            view = TopEstrelasView(data, self.bot)
            await ctx.reply(embed=view.get_embed(), view=view, mention_author=False)
        except Exception as e:
            print(f"[Erro Interno] Falha ao buscar ranking: {e}")
            await ctx.reply("❌ Não foi possível buscar o ranking.", mention_author=False)

    @commands.hybrid_command(name="tops", description="Veja quem tem mais estrelas no servidor!")
    async def topestrelasservidor(self, ctx):
        try:
            # Obtém IDs dos membros do servidor atual
            membros_ids = {member.id for member in ctx.guild.members if not member.bot}

            # Busca todas as estrelas
            todos = await self.bot.db.fetch("""
                SELECT usuario_id, quantidade
                FROM public.estrelas
                WHERE quantidade > 0
            """)

            # Filtra apenas os usuários que estão no servidor
            dados_guild = [r for r in todos if r["usuario_id"] in membros_ids]

            # Ordena por quantidade
            dados_ordenados = sorted(dados_guild, key=lambda x: x["quantidade"], reverse=True)

            # Verifica se há dados
            if not dados_ordenados:
                return await ctx.reply("🤷‍♂️ Ninguém neste servidor tem estrelas ainda!", mention_author=False)

            # Paginação com a mesma classe anterior
            view = TopEstrelasView(dados_ordenados, self.bot)
            await ctx.reply(embed=view.get_embed(), view=view, mention_author=False)

        except Exception as e:
            print(f"[Erro Interno] Falha ao buscar ranking do servidor: {e}")
            await ctx.reply("❌ Não foi possível buscar o ranking do servidor.", mention_author=False)


async def setup(bot):
    await bot.add_cog(Estrelas(bot))
