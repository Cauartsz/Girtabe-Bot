from discord import app_commands
from discord.ext import commands, tasks
import discord
from datetime import datetime, timedelta, timezone

class DarGrupo(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="dar")
        self.bot = bot


    #DAR/TRANSFERIR ESTRELAS (OK)
    @app_commands.command(name="estrelas", description="Transfira suas estrelas para outro membro!")
    @app_commands.describe(membro="Membro que irá receber suas estrelas...", quantidade="Quantidade de estrelas que serão transferidas...")
    async def dar_estrelas(self, interaction: discord.Interaction, membro: discord.Member, quantidade: int):

        await interaction.response.defer()

        if quantidade <= 0:
            return await interaction.followup.send("A quantidade de estrelas que deseja transferir deve ser maior que zero!", ephemeral=True)

        if membro.id == interaction.user.id:
            return await interaction.followup.send("Você não pode transferir estrelas para si mesmo!", ephemeral=True)

        guild_id = interaction.guild.id
        remetente_id = interaction.user.id
        destinatario_id = membro.id

        #Verifica saldo
        row = await self.bot.db.fetchrow("""
            SELECT stars FROM userperguild WHERE guildid = $1 AND userid = $2
        """, guild_id, remetente_id)
        saldo = row["stars"] if row else 0

        if saldo < quantidade:
            return await interaction.followup.send("Você não tem estrelas suficientes para essa transferência...", ephemeral=True)

        if quantidade:
            #Caso o membro ainda não possua registro no banco
            await self.bot.db.execute("""
                INSERT INTO users (userid) VALUES ($1)
                ON CONFLICT (userid) DO NOTHING
            """, membro.id)

        #Executa a transação (Retirada e depois transferência)
        async with self.bot.db.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    UPDATE userperguild SET stars = stars - $1
                    WHERE guildid = $2 AND userid = $3
                """, quantidade, guild_id, remetente_id)

                await conn.execute("""
                    INSERT INTO userperguild (guildid, userid, stars)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (guildid, userid)
                    DO UPDATE SET stars = userperguild.stars + $3
                """, guild_id, destinatario_id, quantidade)

        # Mensagem de confirmação
        await interaction.followup.send(f"{interaction.user.mention} transferiu `{quantidade}` estrelas para {membro.mention}! <:star:1375219269373132800>")


    #DAR/TRANSFERIR CONSTELAÇÕES (OK)
    @app_commands.command(name="constelações", description="Transfira suas constelações para outro membro!")
    @app_commands.describe(membro="Membro que irá receber suas constelações...", quantidade="Quantidade de constelações que serão transferidas...")
    async def dar_constelacoes(self, interaction: discord.Interaction, membro: discord.Member, quantidade: int):

        await interaction.response.defer()

        if quantidade <= 0:
            return await interaction.followup.send("A quantidade de constelações que deseja transferir deve ser maior que zero!", ephemeral=True)

        if membro.id == interaction.user.id:
            return await interaction.followup.send("Você não pode transferir constelações para si mesmo!", ephemeral=True)

        remetente_id = interaction.user.id
        destinatario_id = membro.id

        # Verifica saldo
        row = await self.bot.db.fetchrow("""
            SELECT constellations FROM users WHERE userid = $1
        """, remetente_id)
        saldo = row["constellations"] if row else 0

        if saldo < quantidade:
            return await interaction.followup.send("Você não tem constelações suficientes para essa transferência...", ephemeral=True)

        await self.bot.db.execute("""
            INSERT INTO users (userid) VALUES ($1)
            ON CONFLICT (userid) DO NOTHING
        """, membro.id)

        # Executa a transação
        async with self.bot.db.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    UPDATE users SET constellations = constellations - $1
                    WHERE userid = $2
                """, quantidade, remetente_id)

                await conn.execute("""
                    INSERT INTO users (userid, constellations)
                    VALUES ($1, $2)
                    ON CONFLICT (userid)
                    DO UPDATE SET constellations = users.constellations + EXCLUDED.constellations
                """, destinatario_id, quantidade)

        # Mensagem de confirmação
        await interaction.followup.send(f"{interaction.user.mention} transferiu **{quantidade}** constelações para {membro.mention}! <:constelacao:1375218065297510471>")


    #
    @app_commands.command(name="cargo", description="Dá um cargo a um membro")
    @app_commands.describe(membro="Membro que receberá o cargo",cargo="Cargo a ser atribuído",duracao="Duração em minutos (opcional)")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    async def dar_cargo(self, interaction: discord.Interaction, membro: discord.Member, cargo: discord.Role, duracao: int = None):

        await interaction.response.defer(ephemeral=True)
        

        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.followup.send("Você não possui permissão para usar este comando...", ephemeral=True)


        if cargo >= interaction.guild.me.top_role:
            return await interaction.followup.send("Não posso atribuir esse cargo pois ele está acima do meu...", ephemeral=True)


        await membro.add_roles(cargo, reason=f"Cargo dado por {interaction.user}.")


        if duracao:
            expiracao = datetime.now(timezone.utc) + timedelta(minutes=duracao)
            await interaction.client.db.execute("""
                INSERT INTO cargos_temporarios (guild_id, user_id, role_id, duracao)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (guild_id, user_id, role_id)
                DO UPDATE SET duracao = EXCLUDED.duracao;
            """, interaction.guild.id, membro.id, cargo.id, expiracao)

            embed = discord.Embed(color=discord.Color.blue())
            embed.set_author(name="✅ Cargo atribuído com sucesso!")

            embed.description = (
                f"{membro.mention} recebeu o cargo {cargo.mention}\nDuração: **{f'{duracao} minuto(s)' or 'permanente'}**."
            )
        await interaction.followup.send(embed=embed)



class Dar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dar_grupo = DarGrupo(bot)
        self.bot.tree.add_command(self.dar_grupo)
        self.verificar_cargos.start()

    def dar_cog_unload(self):
        self.bot.tree.remove_command(self.dar_grupo.name)
        self.verificar_cargos.cancel()


    @tasks.loop(minutes=1)
    async def verificar_cargos(self):
        agora = datetime.now(timezone.utc)
        registros = await self.bot.db.fetch("""
            SELECT guild_id, user_id, role_id FROM cargos_temporarios
            WHERE duracao <= $1
        """, agora)

        for registro in registros:
            guild = self.bot.get_guild(registro["guild_id"])
            if not guild:
                continue
            membro = guild.get_member(registro["user_id"])
            cargo = guild.get_role(registro["role_id"])
            if membro and cargo:
                await membro.remove_roles(cargo, reason="Cargo temporário expirado")
                await self.bot.db.execute("""
                    DELETE FROM cargos_temporarios
                    WHERE guild_id = $1 AND user_id = $2 AND role_id = $3
                """, registro["guild_id"], registro["user_id"], registro["role_id"])

async def setup(bot):
    await bot.add_cog(Dar(bot))