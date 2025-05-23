import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import pytz


class Setlog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #DEFINIR CANAL DE LOGS DE BAN
    @app_commands.command(name="set-ban-log", description="Define o canal de log para banimentos.")
    @app_commands.describe(canal="Canal onde os logs de banimentos serão enviados.")
    async def setbanlog(self, interaction: discord.Interaction, canal: discord.TextChannel):

        guild = interaction.guild
        # Verifica se o canal pertence ao servidor
        if canal.guild.id != guild.id:
            return await interaction.response.send_message("O canal definido não pertence a este servidor ou é inválido.", ephemeral=True)
        # Verifica permissão
        if not canal.permissions_for(guild.me).send_messages:
            return await interaction.response.send_message("Não tenho permissão para enviar mensagens nesse canal.", ephemeral=True)

        if self.bot.db.fetchrow("""
            SELECT canal_id
            FROM banlog
            WHERE guild_id = $1 AND status = TRUE
        """, guild.id):
            return await interaction.response.send_message("Os logs já estão definidos no servidor.", ephemeral=True)
        
        # Insere ou atualiza o log de banimentos
        await self.bot.db.execute("""
            INSERT INTO banlog (guild_id, canal_id, status)
            VALUES ($1, $2, TRUE)
            ON CONFLICT (guild_id, canal_id) DO UPDATE SET status = TRUE;
        """, guild.id, canal.id)

        await interaction.response.send_message(f"Log de banimentos ativado no canal {canal.mention}.", ephemeral=True)


    @app_commands.command(name="ban-unlog", description="Desativa o log de banimentos para este servidor.")
    async def desativarlog(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        result = await self.bot.db.execute("""
            UPDATE banlog
            SET status = FALSE
            WHERE guild_id = $1
        """, guild_id)

        await interaction.response.send_message("Log de banimentos desativado.", ephemeral=True)



    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        # Verifica no banco se o log está ativo
        result = await self.bot.db.fetchrow("""
            SELECT canal_id
            FROM banlog
            WHERE guild_id = $1 AND status = TRUE
        """, guild.id)

        if not result:
            return  # log desativado ou não configurado

        canal_id = result["canal_id"]
        canal = guild.get_channel(canal_id)
        if not canal or not canal.permissions_for(guild.me).send_messages:
            return

        # Busca o motivo e autor via audit log
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                moderador = entry.user
                motivo = entry.reason or "Não especificado"
                break
        else:
            moderador = None
            motivo = "Desconhecido"

        # Data formatada
        fuso_brasil = pytz.timezone("America/Sao_Paulo")
        agora = datetime.now(fuso_brasil)
        data_formatada = agora.strftime("%d/%m/%Y %H:%M")

        # Criar embed
        embed = discord.Embed(
            title="🚫 Banimento・Girtabe",
            color=discord.Color.blue()
        )
        embed.add_field(name="<:user:1366748682115878932> Usuário", value=f"**Nome:** {user.name}\n**ID:** `{user.id}`", inline=False)
        embed.add_field(
            name="<:moderator:1366747380103381093> Moderador",
            value=f"**Nome:** {moderador.name if moderador else 'Desconhecido'}\n**ID:** `{moderador.id if moderador else '???'}`",
            inline=False
        )
        embed.add_field(name="<:info:1366749282434285679> Informações", value=f"**Tempo:** `Permanente`\n**Motivo:** {motivo}\n**Data e horário:** {data_formatada}", inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)

        await canal.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Setlog(bot))
