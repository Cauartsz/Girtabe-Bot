from discord import app_commands, Interaction
from discord.ext import commands
import discord
import os


#GRUPO
class AdicionarGrupo(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="adicionar")
        self.bot = bot


    #ADICIONAR ESTRELAS (OK)
    @app_commands.command(name="estrelas", description="Adicione estrelas a um membro!")
    @app_commands.describe(membro="Membro que receberá a quantia de estrelas...", quantidade="Quantia de estrelas que serão adicionadas ao membro...")
    async def adicionar_estrelas(self, interaction: Interaction, membro: discord.Member, quantidade: int):
       
        await interaction.response.defer()

        if interaction.user.id != int(os.getenv("OWNER_ID")):
            return await interaction.followup.send("Apenas o dono do bot pode usar este comando!", ephemeral=True)
        
        if quantidade <= 0:
            return await interaction.followup.send("A quantidade que deseja dar deve ser maior que zero!", ephemeral=True)

        if quantidade: #Caso o membro ainda não possua registro no banco
            await self.bot.db.execute("""
                INSERT INTO users (userid) VALUES ($1)
                ON CONFLICT (userid) DO NOTHING
            """, membro.id)

            await self.bot.db.execute("""
                INSERT INTO guild (guildid) VALUES ($1)
                ON CONFLICT (guildid) DO NOTHING
            """, interaction.guild.id)

        #Transação
        await self.bot.db.execute("""
            INSERT INTO userperguild (guildid, userid, stars)
            VALUES ($1, $2, $3)
            ON CONFLICT (guildid, userid)
            DO UPDATE SET stars = userperguild.stars + $3
        """, interaction.guild.id, membro.id, quantidade)

        qtd_fmt = f"{quantidade:,}".replace(",", ".")
        await interaction.followup.send(f"Parabéns {membro.mention}, você recebeu **{qtd_fmt}** {'estrela' if quantidade == 1 else 'estrelas'} para usar neste servidor! <:star:1375219269373132800>")


    #ADICIONAR CONSTELAÇÕES (OK)
    @app_commands.command(name="constelações", description="Adicione constelações a um membro!")
    @app_commands.describe(membro="Membro que receberá as constelações...", quantidade="Quantidade de constelações que o membro receberá...")
    async def adicionar_constelacoes(self, interaction: Interaction, membro: discord.Member, quantidade: int):
     
        await interaction.response.defer()

        if interaction.user.id != int(os.getenv("OWNER_ID")):
            return await interaction.followup.send("Apenas o dono do bot pode usar este comando.", ephemeral=True)
        
        if quantidade <= 0:
            return await interaction.followup.send("A quantidade de estrelas que deseja adicionar deve ser maior que zero.", ephemeral=True)

        if quantidade:
            await self.bot.db.execute("""
                INSERT INTO users (userid) VALUES ($1)
                ON CONFLICT (userid) DO NOTHING
            """, membro.id)

        await self.bot.db.execute("""
            INSERT INTO users (userid, constellations)
            VALUES ($1, $2)
            ON CONFLICT (userid)
            DO UPDATE SET constellations = users.constellations + $2
        """, membro.id, quantidade)

        qtd_fmt = f"{quantidade:,}".replace(",", ".")
        await interaction.followup.send(f"Parabéns {membro.mention}, você recebeu **{qtd_fmt}** {'constelação' if quantidade == 1 else 'constelações'}! <:constelacao:1375218065297510471>")


class Adicionar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.adicionar_grupo = AdicionarGrupo(bot)
        self.bot.tree.add_command(self.adicionar_grupo)

    def adicionar_cog_unload(self):
        self.bot.tree.remove_command(self.adicionar_grupo.name)

async def setup(bot):
    await bot.add_cog(Adicionar(bot))
