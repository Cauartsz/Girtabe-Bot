# Girtabe-Bot
Um bot do Discord feito com `discord.py` que utiliza PostgreSQL para persistência de dados.

## ✔ Requisitos

- Python 3.10+ (Em uso: 3.12.7)
- Discord.py: 2.5.2
- PostgreSQL
- Pip (gerenciador de pacotes)

## 📦 Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/seu-repositorio.git
   cd seu-repositorio

2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows

4. Instale as dependências:
   ```bash
   pip install -r requirements.txt

5. Crie o arquivo .env com:
   ```bash
   DB_PASSWORD=sua_senha_do_postgres
   TOKEN=seu_token_discord

6. Execute o bot:
   ```bash
   python bot.py
