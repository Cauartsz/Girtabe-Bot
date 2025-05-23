from discord import app_commands
from discord.ext import commands
import discord
from datetime import timedelta


class RegistrarGrupo(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="registrar", description="...")
        self.bot = bot


    @app_commands.command(name="cargo", description="Registre um cargo comprável com valor e duração.")
    @app_commands.describe(cargo="Cargo que poderá ser comprado",nome="Nome customizado para exibição",valor="Preço do cargo em estrelas",duracao="Duração do cargo em horas")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def cargo(self, interaction: discord.Interaction, cargo: discord.Role, nome: str,valor: int,duracao: int):
        guild_id = interaction.guild.id
        autor_id = interaction.user.id

        # Validações simples
        if valor <= 0:
            return await interaction.response.send_message("O valor deve ser maior que 0.", ephemeral=True)

        if duracao <= 0:
            return await interaction.response.send_message("A duração deve ser maior que 0 horas.", ephemeral=True)

        if len(nome) > 30:
            return await interaction.response.send_message("O nome pode ter no máximo 30 caracteres.", ephemeral=True)

        try:
            tempo = timedelta(hours=duracao)
            await self.bot.db.execute("""
                INSERT INTO cargos_compraveis (guild_id, role_id, autor_id, nome, valor, duracao)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (guild_id, role_id) DO UPDATE
                SET nome = EXCLUDED.nome,
                    valor = EXCLUDED.valor,
                    duracao = EXCLUDED.duracao,
                    autor_id = EXCLUDED.autor_id
            """, guild_id, cargo.id, autor_id, nome, valor, tempo)

            await interaction.response.send_message(
                f"✅ O cargo {cargo.mention} foi registrado como comprável por `{valor}` estrelas por `{duracao}` horas.",
                ephemeral=False
            )

        except Exception as e:
            print(f"[Erro Interno] Falha ao registrar cargo: {e}")
            await interaction.response.send_message("❌ Ocorreu um erro ao registrar o cargo.", ephemeral=True)



class Registrar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.registrar_grupo = RegistrarGrupo(bot)
        self.bot.tree.add_command(self.registrar_grupo)

async def setup(bot):
    await bot.add_cog(Registrar(bot))