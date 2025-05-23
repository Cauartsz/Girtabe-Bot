from discord.ext import commands
from discord.ext.commands import (CommandNotFound, MissingPermissions, BotMissingPermissions, NotOwner, MissingRequiredArgument, BadArgument, MissingRole, BotMissingRole)
import logging
logger = logging.getLogger("Erro Prefix")

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
    return ', '.join([f"{PERMISSION_TRANSLATIONS.get(p.lower(), p.replace('_', ' ').title())}" for p in perms])


class Erros(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if hasattr(ctx.command, 'on_error'):
            return 


        if isinstance(error, CommandNotFound):
            if not ctx.author.bot:
                return await ctx.send(f"Olá {ctx.author.mention}, eu não possuo esse comando. Use ,help para que eu possa te ajudar!")


        elif isinstance(error, commands.CommandInvokeError):
            logger.info(f"[Erro Interno] {error.original}")
            return await ctx.send(f"{ctx.author.mention} ocorreu um erro interno no comando.")


        elif isinstance(error, MissingRequiredArgument):
            return await ctx.send(f"{ctx.author.mention} faltou você me passar os argumentos obrigatórios: **{error.param.name}**.")


        elif isinstance(error, BadArgument):
            return await ctx.send(f"{ctx.author.mention} você me passou um ou mais argumentos inválidos ou inexistentes.")


        elif isinstance(error, commands.TooManyArguments):
            return await ctx.send(f"{ctx.author.mention} você forneceu argumentos demais ou desnecessários no comando.")


        elif isinstance(error, commands.UserInputError):
            return await ctx.send(f"{ctx.author.mention} há algo de errado com os argumentos que você me passou, confira se está tudo certinho.")


        elif isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(f"{ctx.author.mention} este comando está em cooldown. Você pode usá-lo novamente em **{round(error.retry_after, 1)}s**.")


        elif isinstance(error, MissingPermissions):
            perms = traduzir_permissoes(error.missing_permissions)
            return await ctx.send(f"{ctx.author.mention} você não possui permissão para **{perms}**.")


        elif isinstance(error, BotMissingPermissions):
            perms = traduzir_permissoes(error.missing_permissions)
            return await ctx.send(f"{ctx.author.mention} Quero poder te ajudar, mas não tenho permissão para **{perms}**. Peça para alguém da administração me dar esta permissão. Valeu!")


        elif isinstance(error, MissingRole):
            roles = ', '.join([f"`{r.name}`" for r in error.missing_roles])
            return await ctx.send(f"{ctx.author.mention} você não possui um ou mais cargos necessários. Lhe falta: {roles}")


        elif isinstance(error, BotMissingRole):
            roles = ', '.join([f"`{r.name}`" for r in error.missing_roles])
            return await ctx.send(f"{ctx.author.mention} eu não possuo um ou mais cargos necessários. Me falta: {roles}")


        elif isinstance(error, NotOwner):
            return await ctx.send(f"{ctx.author.mention} esse comando é restrito ao dono.")


        elif isinstance(error, commands.NoPrivateMessage):
            return await ctx.author.send(f"{ctx.author.mention} este comando não pode ser usado em mensagens privadas.")


        elif isinstance(error, commands.PrivateMessageOnly):
            return await ctx.send(f"{ctx.author.mention} este comando só pode ser usado em mensagens privadas.")


        elif isinstance(error, commands.CheckFailure):
            return await ctx.send(f"{ctx.author.mention} você não atende aos requisitos para usar este comando (permissões ou cargos).")


        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send(f"{ctx.author.mention} este comando está desativado no momento.")


        elif isinstance(error, commands.CommandError):
            logger.info(f"[Erro genérico]: {error}")
            return await ctx.send("Um erro genérico ocorreu. Estou de olho nisso!")


        else:
            logger.info(f"[Erro Desconhecido] {error.__class__.__name__}: {error}")
            return await ctx.send("Erro desconhecido.")


async def setup(bot):
    await bot.add_cog(Erros(bot))
