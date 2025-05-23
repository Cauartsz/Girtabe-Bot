from discord import app_commands, Interaction
from discord.ext import commands
import discord

#RANK ESTRELAS
class EstrelasRankingView(discord.ui.View):
    def __init__(self, bot, data, guild_id, pagina=0):
        super().__init__(timeout=60)
        self.bot = bot
        self.data = data
        self.pagina = pagina
        self.guild_id = guild_id
        self.total_paginas = (len(data) - 1) // 10 + 1
        self.atualizar_botoes()

    def atualizar_botoes(self):
        self.previous.disabled = self.pagina == 0
        self.next.disabled = self.pagina >= self.total_paginas - 1

    async def criar_embed(self, interaction: discord.Interaction) -> discord.Embed:
        inicio = self.pagina * 10
        fim = inicio + 10
        ranking_atual = self.data[inicio:fim]

        descricao = ""
        for i, row in enumerate(ranking_atual, start=inicio + 1):
            user = self.bot.get_user(row["userid"]) or await self.bot.fetch_user(row["userid"])
            descricao += f"**{i}.** {user.mention if user else f'`{row['userid']}`'} – <:star:1375219269373132800> {row['stars']:,}\n"

        posicao_usuario = next((i + 1 for i, r in enumerate(self.data) if r["userid"] == interaction.user.id), None)
        estrelas_usuario = next((r["stars"] for r in self.data if r["userid"] == interaction.user.id), 0)

        embed = discord.Embed(
            title=f"Ranking de Estrelas – Página {self.pagina + 1}/{self.total_paginas}",
            description=descricao,
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="Sua posição:",
            value=f"**{posicao_usuario if posicao_usuario else '❓'}º** – <:star:1375219269373132800> {estrelas_usuario:,}",
            inline=False
        )

        return embed

    @discord.ui.button(label="Anterior", style=discord.ButtonStyle.secondary, emoji="<:left:1375303938911240273>")
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina -= 1
        self.atualizar_botoes()
        embed = await self.criar_embed(interaction)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Próxima", style=discord.ButtonStyle.secondary, emoji="<:right:1375303893084409967>")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina += 1
        self.atualizar_botoes()
        embed = await self.criar_embed(interaction)
        await interaction.response.edit_message(embed=embed, view=self)

