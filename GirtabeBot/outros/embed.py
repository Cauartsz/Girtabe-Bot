import discord
from discord import Interaction, TextStyle, app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput, Select

#BANCO TEMPORÁRIO
embeds_predefinidas = {}
campos_temp = {}

#MODAL AUTOR
class AuthorModal(Modal, title="Editar Autor"):
    def __init__(self,author: discord.User,message: discord.Message,current_name: str = "",current_icon: str = "",current_url: str = ""):
        super().__init__()
        self.author = author
        self.message = message

        self.nome = TextInput(
            label="Nome do Autor",
            max_length=256,
            default=current_name
        )
        self.icon_url = TextInput(
            label="URL de Ícone do Autor",
            max_length=512,
            required=False,
            placeholder="URL da imagem do ícone (ex: avatar personalizado)",
            default=current_icon or author.display_avatar.url
        )
        self.site_url = TextInput(
            label="URL de Site do Autor",
            max_length=512,
            required=False,
            placeholder="URL que o nome do Autor vai apontar",
            default=current_url
        )

        self.add_item(self.nome)
        self.add_item(self.icon_url)
        self.add_item(self.site_url)

    async def on_submit(self, interaction: Interaction):
        embed = embeds_predefinidas.get(self.author.id)
        if not embed:
            return await interaction.response.send_message("Nenhuma embed criada.", ephemeral=True)

        icon_url = self.icon_url.value or None
        site_url = self.site_url.value or None

        embed.set_author(name=self.nome.value, icon_url=icon_url, url=site_url)

        await interaction.response.edit_message(embed=embed, view=EmbedButtonView(self.author))

#MODAL CAMPOS
class CampoModal(Modal, title="Adicionar Campo à Embed"):
    def __init__(self, author: discord.User, message: discord.Message, index: int = None):
        super().__init__()
        self.author = author
        self.message = message
        self.index = index 

        self.nome = TextInput(label="Nome do Campo", max_length=256)
        self.valor = TextInput(label="Valor do Campo", style=TextStyle.paragraph, max_length=1024)

        self.add_item(self.nome)
        self.add_item(self.valor)

    async def on_submit(self, interaction: Interaction):
        if self.author.id not in campos_temp:
            campos_temp[self.author.id] = []

        if self.index is None:
            campos_temp[self.author.id].append({
                "name": self.nome.value,
                "value": self.valor.value,
                "inline": False
            })
        else:
            campos_temp[self.author.id][self.index] = {
                "name": self.nome.value,
                "value": self.valor.value,
                "inline": False
            }

        embed = embeds_predefinidas.get(self.author.id)
        if embed:
            embed.clear_fields()
            for campo in campos_temp.get(self.author.id, []):
                embed.add_field(name=campo["name"], value=campo["value"], inline=campo["inline"])

            await interaction.response.edit_message(embed=embed, view=EmbedButtonView(self.author))

#FOOTER MODAL
class FooterModal(Modal, title="Editar Rodapé"):
    def __init__(self, author: discord.User, message: discord.Message):
        super().__init__()
        self.author = author
        self.message = message

        self.footer = TextInput(label="Texto do Rodapé", max_length=2048)
        self.add_item(self.footer)

    async def on_submit(self, interaction: Interaction):
        embed = embeds_predefinidas.get(self.author.id)
        if not embed:
            return await interaction.response.send_message("Nenhuma embed criada.", ephemeral=True)

        embed.set_footer(text=self.footer.value, icon_url=self.author.avatar.url)
        await interaction.response.edit_message(embed=embed, view=EmbedButtonView(self.author))

#TEXTO MODAL (SUBMIT)
class TextoModal(Modal):
    def __init__(self, title: str, label: str, field_name: str, author: discord.User, current_value: str = ""):
        super().__init__(title=title)
        self.author = author
        self.field_name = field_name
        self.input = TextInput(
            label=label,
            style=TextStyle.paragraph,
            max_length=1024,
            default=current_value
        )
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        embed = embeds_predefinidas.get(self.author.id)
        if not embed:
            embed = discord.Embed(color=discord.Color.blue())
            embeds_predefinidas[self.author.id] = embed
        
        if self.field_name == "title":
            embed.title = self.input.value
        elif self.field_name == "description":
            embed.description = self.input.value
        elif self.field_name == "footer":
            embed.set_footer(text=self.input.value)
        elif self.field_name == "author":
            embed.set_author(name=self.input.value)
        elif self.field_name == "thumbnail":
            embed.set_thumbnail(url=self.input.value)
        elif self.field_name == "image":
            embed.set_image(url=self.input.value)

        await interaction.response.edit_message(embed=embed, view=EmbedButtonView(self.author))

#COLOR DROPDOWN
class ColorDropdown(Select):
    def __init__(self, author: discord.User):
        options = [
            discord.SelectOption(label="Azul", value="blue"),
            discord.SelectOption(label="Vermelho", value="red"),
            discord.SelectOption(label="Verde", value="green"),
            discord.SelectOption(label="Amarelo", value="yellow"),
            discord.SelectOption(label="Roxo", value="purple"),
            discord.SelectOption(label="Laranja", value="orange"),
            discord.SelectOption(label="Blurple", value="blurple"),
            discord.SelectOption(label="Aleatório", value="random"),
        ]
        super().__init__(placeholder="Escolha uma cor...", options=options)
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        cores = {
            "blue": discord.Color.blue(),
            "red": discord.Color.red(),
            "green": discord.Color.green(),
            "yellow": discord.Color.yellow(),
            "purple": discord.Color.purple(),
            "orange": discord.Color.orange(),
            "blurple": discord.Color.blurple(),
            "random": discord.Color.random()
        }

        cor_escolhida = cores.get(self.values[0], discord.Color.blue())

        embed = embeds_predefinidas.get(self.author.id)
        if not embed:
            embed = discord.Embed(color=cor_escolhida)
            embeds_predefinidas[self.author.id] = embed
        else:
            embed.color = cor_escolhida

        await interaction.response.edit_message(embed=embed, view=EmbedButtonView(self.author))

#CODIGO DE COR MODAL
class ColorCodeModal(Modal, title="Inserir Código de Cor"):
    def __init__(self, author: discord.User, default_color: str = ""):
        super().__init__()
        self.author = author
        self.codigo = TextInput(
            label="Código da Cor (ex: #3498db ou 0x3498db)", 
            placeholder="#RRGGBB ou 0xRRGGBB", 
            max_length=10,
            default=default_color
        )
        self.add_item(self.codigo)

    async def on_submit(self, interaction: discord.Interaction):
        embed = embeds_predefinidas.get(self.author.id)
        if not embed:
            embed = discord.Embed(color=discord.Color.blue())
            embeds_predefinidas[self.author.id] = embed

        codigo = self.codigo.value.strip()

        try:
            if codigo.startswith("#"):
                cor = int(codigo[1:], 16)
            elif codigo.startswith("0x"):
                cor = int(codigo, 16)
            else:
                cor = int(codigo, 16)

            embed.color = discord.Color(cor)

            await interaction.response.edit_message(embed=embed, view=EmbedButtonView(self.author))
        except ValueError:
            await interaction.response.send_message("❌ Código de cor inválido! Use #RRGGBB ou 0xRRGGBB.", ephemeral=True)

#EDITAR CAMPOS MODAL
class EditarCamposModal(Modal):
    def __init__(self, author: discord.User, campos: list, pagina: int = 0):
        super().__init__(title=f"Editar Campos (Página {pagina + 1}/{(len(campos) + 1) // 2})")
        self.author = author
        self.campos = campos
        self.pagina = pagina

        self.titulos = []
        self.descricoes = []

        inicio = pagina * 2
        fim = min(inicio + 2, len(campos))
        campos_na_pagina = campos[inicio:fim]

        for i, campo in enumerate(campos_na_pagina):
            # Primeiro: input para título
            titulo = TextInput(
                label=f"Título do Campo {inicio + i + 1}",
                default=campo["name"],
                max_length=256,
                required=False
            )
            self.add_item(titulo)
            self.titulos.append(titulo)

            if len(self.children) >= 5:
                break  # Garante que não passa de 5 inputs

            # Segundo: input para descrição
            descricao = TextInput(
                label=f"Descrição do Campo {inicio + i + 1}",
                default=campo["value"],
                style=TextStyle.paragraph,
                max_length=1024,
                required=False
            )
            self.add_item(descricao)
            self.descricoes.append(descricao)

    async def on_submit(self, interaction: Interaction):
        inicio = self.pagina * 2

        for i, (titulo, descricao) in enumerate(zip(self.titulos, self.descricoes)):
            idx = inicio + i
            if idx < len(campos_temp[self.author.id]):
                campos_temp[self.author.id][idx]["name"] = titulo.value
                campos_temp[self.author.id][idx]["value"] = descricao.value

        embed = embeds_predefinidas.get(self.author.id)
        if embed:
            embed.clear_fields()
            for campo in campos_temp.get(self.author.id, []):
                embed.add_field(name=campo["name"], value=campo["value"], inline=campo["inline"])

            await interaction.response.edit_message(embed=embed, view=EmbedButtonView(self.author))

#USAR CÓDIGO JSON MODAL
class JsonInputModal(Modal, title="Inserir Código JSON da Embed"):
    def __init__(self, author: discord.User):
        super().__init__()
        self.author = author
        self.json_input = TextInput(
            label="Cole o código JSON aqui",
            style=TextStyle.paragraph,
            placeholder='{"title": "Exemplo", "description": "Minha embed"}',
            max_length=4000
        )
        self.add_item(self.json_input)

    async def on_submit(self, interaction: discord.Interaction):
        import json

        try:
            data = json.loads(self.json_input.value)
            embed = discord.Embed.from_dict(data)
            embeds_predefinidas[self.author.id] = embed
            campos_temp[self.author.id] = []

            if "fields" in data:
                for field in data["fields"]:
                    campos_temp[self.author.id].append({
                        "name": field["name"],
                        "value": field["value"],
                        "inline": field.get("inline", False)
                    })

            await interaction.response.edit_message(
                content="Embed carregada com sucesso!",
                embed=embed,
                view=EmbedButtonView(self.author)
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao carregar JSON: `{str(e)}`", ephemeral=True)

#DROPDOWN SELECIONAR CAMPOS PARA EDITAR
class CampoSelectDropdown(Select):
    def __init__(self, author: discord.User):
        campos = campos_temp.get(author.id, [])
        options = []

        paginas = (len(campos) + 1) // 2
        for i in range(paginas):
            inicio = i * 2 + 1
            fim = min((i + 1) * 2, len(campos))
            label = f"Campos {inicio} - {fim}"
            options.append(discord.SelectOption(label=label, value=str(i)))

        super().__init__(
            placeholder="Selecione quais campos editar...",
            options=options,
            min_values=1,
            max_values=1
        )
        self.author = author

    async def callback(self, interaction: Interaction):
        pagina = int(self.values[0])
        await interaction.response.send_modal(EditarCamposModal(self.author, campos_temp.get(self.author.id, []), pagina))

class CampoSelectView(View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=60)
        self.author = author
        self.add_item(CampoSelectDropdown(author))

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Você não pode interagir aqui.", ephemeral=True)
            return False
        return True

#EMBED VIEW E BOTÕES
class EmbedButtonView(View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=300)
        self.author = author
        self.add_item(ColorDropdown(author))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Você não pode interagir aqui.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Título", style=discord.ButtonStyle.blurple)
    async def edit_title(self, interaction: discord.Interaction, button: Button):
        embed = embeds_predefinidas.get(self.author.id)
        current_value = embed.title if embed and embed.title else ""
        await interaction.response.send_modal(TextoModal("Editar Título", "Novo título", "title", self.author, current_value))

    @discord.ui.button(label="Descrição", style=discord.ButtonStyle.blurple)
    async def edit_description(self, interaction: discord.Interaction, button: Button):
        embed = embeds_predefinidas.get(self.author.id)
        current_value = embed.description if embed and embed.description else ""
        await interaction.response.send_modal(TextoModal("Editar Descrição", "Nova descrição", "description", self.author, current_value))
        
    @discord.ui.button(label="Cor", style=discord.ButtonStyle.blurple)
    async def codigo_cor(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.author:
            return await interaction.response.send_message("Você não pode usar este botão.", ephemeral=True)

        embed = embeds_predefinidas.get(self.author.id)
        current_color = ""
        if embed and embed.color:
            current_color = f"#{embed.color.value:06x}"

        await interaction.response.send_modal(ColorCodeModal(self.author, default_color=current_color))

    @discord.ui.button(label="Adicionar Campo", style=discord.ButtonStyle.blurple)
    async def add_field(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(CampoModal(self.author, interaction.message))

    @discord.ui.button(label="Rodapé", style=discord.ButtonStyle.blurple)
    async def edit_footer(self, interaction: discord.Interaction, button: Button):
        embed = embeds_predefinidas.get(self.author.id)
        current_value = embed.footer.text if embed and embed.footer and embed.footer.text else ""
        await interaction.response.send_modal(TextoModal("Editar Rodapé", "Novo Rodapé", "footer", self.author, current_value))

    @discord.ui.button(label="Autor", style=discord.ButtonStyle.blurple)
    async def add_author(self, interaction: discord.Interaction, button: Button):
        embed = embeds_predefinidas.get(self.author.id)
        current_name = ""
        current_icon = ""
        current_url = ""
        if embed and embed.author:
            current_name = embed.author.name or ""
            current_icon = embed.author.icon_url if embed.author.icon_url else ""
            current_url = embed.author.url or ""
        await interaction.response.send_modal(
            AuthorModal(
                author=self.author,
                message=interaction.message,
                current_name=current_name,
                current_icon=current_icon,
                current_url=current_url
            )
        )

    @discord.ui.button(label="Thumbnail", style=discord.ButtonStyle.blurple)
    async def add_thumbnail(self, interaction: discord.Interaction, button: Button):
        embed = embeds_predefinidas.get(self.author.id)
        current_value = embed.thumbnail.url if embed and embed.thumbnail and embed.thumbnail.url else ""
        await interaction.response.send_modal(TextoModal("Editar Thumbnail", "URL da thumbnail", "thumbnail", self.author, current_value))

    @discord.ui.button(label="Imagem", style=discord.ButtonStyle.blurple)
    async def add_image(self, interaction: discord.Interaction, button: Button):
        embed = embeds_predefinidas.get(self.author.id)
        current_value = embed.image.url if embed and embed.image and embed.image.url else ""
        await interaction.response.send_modal(TextoModal("Editar Imagem", "URL da imagem", "image", self.author, current_value))

    @discord.ui.button(label="Editar Campos", style=discord.ButtonStyle.blurple)
    async def editar_campos(self, interaction: discord.Interaction, button: Button):
        campos = campos_temp.get(self.author.id, [])
        if not campos:
            return await interaction.response.send_message("Encontrei nenhum campo para editar!", ephemeral=True)
        await interaction.response.send_message("Selecione quais campos você deseja editar:",view=CampoSelectView(self.author),ephemeral=True)

    @discord.ui.button(label="Exportar JSON", style=discord.ButtonStyle.secondary, row=2)
    async def gerar_json(self, interaction: discord.Interaction, button: Button):
        embed = embeds_predefinidas.get(self.author.id)
        if not embed:
            return await interaction.response.send_message("Nenhuma embed carregada.", ephemeral=True)
        import json
        embed_dict = embed.to_dict()
        json_text = json.dumps(embed_dict, indent=2, ensure_ascii=False)
        if len(json_text) > 6000:
            return await interaction.response.send_message("❌ O JSON gerado é muito grande para ser exibido aqui.", ephemeral=True)
        await interaction.response.send_message(
            f"```json\n{json_text}\n```",
            ephemeral=True
        )

    @discord.ui.button(label="Importar JSON", style=discord.ButtonStyle.secondary, row=2)
    async def usar_json(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(JsonInputModal(self.author))

    @discord.ui.button(label="Salvar Embed", style=discord.ButtonStyle.success)
    async def save_embed(self, interaction: discord.Interaction, button: Button):
        embed = embeds_predefinidas.get(self.author.id)
        if not embed:
            embed = discord.Embed(description="", color=discord.Color.blue())
            embeds_predefinidas[self.author.id] = embed
        await interaction.response.send_message("Embed salva! Use `/enviar-embed` para enviá-la!", ephemeral=True)

#COG EMBED
class Embed(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="criar-embed", description="Cria uma embed personalizada.")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True)
    async def embed(self, interaction: discord.Interaction):
        embeds_predefinidas[interaction.user.id] = discord.Embed(description="(Clique nos botões para editar)", color=discord.Color.blue())
        view = EmbedButtonView(interaction.user)
        await interaction.response.send_message("Edite sua embed usando os botões abaixo:", view=view, embed=embeds_predefinidas[interaction.user.id], ephemeral=True)

    @app_commands.command(name="enviar-embed", description="Envia sua última embed salva.")
    @app_commands.describe(canal="Canal para enviar a embed (opcional)")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True)
    async def embed_enviar(self, interaction: discord.Interaction, canal: discord.TextChannel = None):
        embed = embeds_predefinidas.get(interaction.user.id)
        if not embed:
            return await interaction.response.send_message("Você possui nenhuma embed salva.\nUse `/criar-embed` e salve uma.", ephemeral=True)
        destino = canal or interaction.channel
        await destino.send(embed=embed)
        await interaction.response.send_message(f"Embed enviada para {destino.mention} com sucesso por {interaction.user.mention}!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Embed(bot))



