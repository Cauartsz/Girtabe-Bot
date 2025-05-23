import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import (AppCommandError, CommandOnCooldown, MissingPermissions, BotMissingPermissions,
                                   MissingRole, CheckFailure, CommandInvokeError, NoPrivateMessage, CommandNotFound)
import logging


PERMISSION_TRANSLATIONS = {
    "manage_guild": "gerenciar servidor",
    "manage_channels": "gerenciar canais",
    "manage_roles": "gerenciar cargos",
    "manage_messages": "gerenciar mensagens",
    "administrator": "administrador",
    "kick_members": "expulsar membros",
    "ban_members": "banir membros",
}


def traduzir_permissoes(perms):
    return ', '.join([PERMISSION_TRANSLATIONS.get(p.lower(), p.replace('_', ' ').title()) for p in perms])


logger = logging.getLogger(__name__)


async def safe_send(interaction: discord.Interaction, message: str, ephemeral: bool = True):
    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(message, ephemeral=ephemeral)
    except Exception as e:
        logger.info(f"[Erro ao enviar resposta de erro] {e}")

class ErrosAppCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: AppCommandError):
        if isinstance(error, app_commands.CommandNotFound):
            return await safe_send(interaction, "Esse comando de barra não existe.")

        elif isinstance(error, CommandInvokeError):
            logger.info(f"[Erro Interno Slash] {error.original}")
            return await safe_send(interaction, "Ocorreu um erro interno ao executar o comando.")

        elif isinstance(error, app_commands.MissingRequiredArgument):
            return await safe_send(interaction, f"Você deixou de preencher o argumento obrigatório: **{error.param.name}**.")

        elif isinstance(error, app_commands.CommandOnCooldown):
            return await safe_send(interaction, f"Este comando está em cooldown. Tente novamente em **{round(error.retry_after, 1)}s**.")

        elif isinstance(error, MissingPermissions):
            perms = traduzir_permissoes(error.missing_permissions)
            return await safe_send(interaction, f"Você não tem permissão para **{perms}**.")

        elif isinstance(error, BotMissingPermissions):
            perms = traduzir_permissoes(error.missing_permissions)
            return await safe_send(interaction, f"Não tenho permissão para **{perms}**. Peça ajuda a um administrador!")

        elif isinstance(error, MissingRole):
            roles = ', '.join([f"`{r}`" for r in error.missing_roles])
            return await safe_send(interaction, f"Você precisa do(s) cargo(s): {roles}")

        elif isinstance(error, CheckFailure):
            return await safe_send(interaction, "Você não atende aos requisitos para usar este comando.")

        elif isinstance(error, NoPrivateMessage):
            return await safe_send(interaction, "Este comando não pode ser usado em mensagens privadas.")

        else:
            logger.info(f"[Erro não tratado Slash] {error.__class__.__name__}: {error}")
            return await safe_send(interaction, "Erro desconhecido ao executar o comando de barra.")

async def setup(bot):
    await bot.add_cog(ErrosAppCommands(bot))
