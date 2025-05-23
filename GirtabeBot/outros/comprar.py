from discord import app_commands
from discord.ext import commands
import discord
from datetime import timedelta, datetime, timezone
import asyncio
import asyncpg
from discord.ext import tasks

class ComprarGrupo(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="comprar", description="...")
        self.bot = bot


    @app_commands.command(name="cargo", description="Compre um cargo registrado com estrelas.")
    @app_commands.describe(nome="Nome do cargo")
    async def cargo(self, interaction: discord.Interaction, nome: str):

        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id
        guild = interaction.guild

        # Busca o cargo no banco
        resultado = await self.bot.db.fetchrow("""
            SELECT * FROM cargos_compraveis
            WHERE guild_id = $1 AND nome = $2
        """, guild.id, nome)

        if not resultado:
            return await interaction.followup.send("❌ Cargo não encontrado com esse nome.", ephemeral=True)

        role_id = resultado["role_id"]
        valor = resultado["valor"]
        duracao = resultado["duracao"]


        role = guild.get_role(role_id)
        if not role:
            # Você pode tentar buscar pelo ID direto como fallback:
            try:
                role = await guild.fetch_role(role_id)
            except discord.NotFound:
                return await interaction.followup.send("❌ Cargo não encontrado no servidor.", ephemeral=True)

        # Verifica saldo
        row = await self.bot.db.fetchrow("""
            SELECT qtd FROM estrelas WHERE guild_id = $1 AND user_id = $2
        """, guild.id, user_id)
        saldo = row["qtd"] if row else 0



        if saldo < valor:
            return await interaction.followup.send("💸 Você não tem estrelas suficientes para essa compra.", ephemeral=True)

        if role in interaction.user.roles:
            return await interaction.followup.send("⚠️ Você já possui esse cargo.", ephemeral=True)
        
        # Tenta dar o cargo
        role = guild.get_role(role_id)
        if not role:
            return await interaction.followup.send("❌ Cargo não encontrado no servidor.", ephemeral=True)

        # Recupera o ID do autor
        autor_id = resultado["autor_id"]

        autor = guild.get_member(autor_id)
        if not autor:
            try:
                autor = await guild.fetch_member(autor_id)
            except discord.NotFound:
                autor = None


        # Inicia transação
        async with self.bot.db.acquire() as conn:
            async with conn.transaction():
        # Desconta do comprador
                await conn.execute("""
                    UPDATE estrelas SET qtd = qtd - $1
                    WHERE guild_id = $2 AND user_id = $3
                """, valor, guild.id, user_id)

                # Dá ao autor (apenas se for diferente do comprador)
                if autor_id != user_id:
                    await conn.execute("""
                        INSERT INTO estrelas (guild_id, user_id, qtd)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (guild_id, user_id)
                        DO UPDATE SET qtd = estrelas.qtd + $3
                    """, guild.id, autor_id, valor)


                # Registra se for temporário
                if duracao.total_seconds() > 0:
                    expiracao = datetime.now(timezone.utc) + duracao
                    await self.bot.db.execute("""
                        INSERT INTO cargos_temporarios (guild_id, user_id, role_id, duracao)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (guild_id, user_id, role_id)
                        DO UPDATE SET duracao = EXCLUDED.duracao
                    """, guild.id, user_id, role.id, expiracao)

        try:
            await interaction.user.add_roles(role, reason="Cargo comprado com estrelas")
        except discord.Forbidden:
               return await interaction.followup.send("❌ Não tenho permissão para conceder esse cargo.", ephemeral=True)

        embed = discord.Embed(
            title="💼 Compra de Cargo",
            description=f"Você comprou o cargo {role.mention} com sucesso!",
            color=discord.Color.green()
        )
        if autor and autor.id != user_id:
            embed.add_field(name="Pagamento ao vendedor", value=f"{autor.mention} recebeu {valor} ⭐")

        await interaction.followup.send(embed=embed)

class Comprar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.comprar_grupo = ComprarGrupo(bot)
        self.bot.tree.add_command(self.comprar_grupo)
        self.verificar_cargos_expirados.start()

    def cog_unload(self):
        self.verificar_cargos_expirados.cancel()

    @tasks.loop(minutes=1)
    async def verificar_cargos_expirados(self):
        try:
            registros = await self.bot.db.fetch("""
                SELECT guild_id, user_id, role_id FROM cargos_temporarios
                WHERE duracao <= NOW()
            """)

            for registro in registros:
                guild = self.bot.get_guild(registro["guild_id"])
                if not guild:
                    continue

                member = guild.get_member(registro["user_id"])
                if not member:
                    continue

                role = guild.get_role(registro["role_id"])
                if not role:
                    continue

                try:
                    await member.remove_roles(role, reason="Cargo expirado (automático)")
                except discord.Forbidden:
                    pass  # Sem permissão
                except discord.HTTPException:
                    pass  # Falha geral

                await self.bot.db.execute("""
                    DELETE FROM cargos_temporarios
                    WHERE guild_id = $1 AND user_id = $2 AND role_id = $3
                """, registro["guild_id"], registro["user_id"], registro["role_id"])

        except asyncpg.PostgresError as e:
            print(f"Erro ao verificar cargos expirados: {e}")


async def setup(bot):
    await bot.add_cog(Comprar(bot))
