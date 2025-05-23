import discord
from discord.ext import commands
import asyncio
import signal
import threading
import os

class Status(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channel_id = int(os.getenv("STATUS_CHANNEL"))
        self.owner_id = int(os.getenv("BOT_OWNER"))
        # Captura Ctrl+C (SIGINT)
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)


    def handle_shutdown(self, sig, frame):
        threading.Thread(target=self._shutdown_thread).start()

    def _shutdown_thread(self):
        future = asyncio.run_coroutine_threadsafe(
            self.send_status_embed(
                "Bot desligado",
                "O bot foi encerrado manualmente (Ctrl+C).",
                discord.Color.red()
            ),
            self.bot.loop
        )

        try:
            future.result(timeout=5)
        except Exception as e:
            print(f"Erro ao esperar o envio do embed de desligamento: {e}")

        print("Desligando bot...")
        os._exit(0)

    async def send_status_embed(self, title, description, color):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(self.channel_id)
        if channel:
            embed = discord.Embed(
                title=title,
                description=description,
                color=color,
            )
            embed.set_footer(text="Status do bot")
            try:
                await channel.send(embed=embed)
            except Exception as e:
                print(f"Erro ao enviar embed de status: {e}")

    @commands.hybrid_command(name="off", description="Desliga o bot")
    @commands.is_owner()
    async def off(self, ctx:commands.Context):

        await ctx.reply("🔒 Desligando o bot...", ephemeral=True)
        await self.send_status_embed("Bot desligado", f"O bot foi desligado por {ctx.author.mention}.", discord.Color.red())
        await self.bot.close()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.send_status_embed("<a:check:1361429470652665956>  O Bot foi iniciado", "Estou online e pronto para ajudar!", discord.Color.brand_green())

    #REPETIR
    @commands.hybrid_command(name="repetir",description="Repete a mensagem")
    @commands.is_owner()
    async def repetir(self, ctx: commands.Context, *, texto: str):
        embed = discord.Embed(
            title = f"",
            description = f"{texto}",
            color = discord.Color.random()
            )
        await ctx.channel.purge(limit=1)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Status(bot))