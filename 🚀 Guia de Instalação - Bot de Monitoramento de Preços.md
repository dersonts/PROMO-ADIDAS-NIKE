# 🚀 Guia de Instalação - Bot de Monitoramento de Preços

Este guia fornece instruções detalhadas para instalar e configurar o Bot de Monitoramento de Preços em diferentes sistemas operacionais.

## 📋 Pré-requisitos

### Sistema Operacional
- **Linux**: Ubuntu 20.04+ (recomendado), Debian 10+, CentOS 8+
- **macOS**: 10.15+ (Catalina ou superior)
- **Windows**: 10/11 com WSL2 (recomendado) ou instalação nativa

### Software Necessário
- **Python**: 3.11 ou superior
- **Git**: Para clonar o repositório
- **Chrome/Chromium**: Para o Playwright (instalado automaticamente)

## 🐧 Instalação no Linux (Ubuntu/Debian)

### 1. Atualizar o Sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar Dependências do Sistema
```bash
# Python e ferramentas de desenvolvimento
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Git
sudo apt install -y git

# Dependências para Playwright
sudo apt install -y libnss3-dev libatk-bridge2.0-dev libdrm2 libxkbcommon0 libgtk-3-0 libgbm-dev libasound2-dev
```

### 3. Clonar o Repositório
```bash
git clone <url-do-repositorio>
cd price_monitor_bot
```

### 4. Criar Ambiente Virtual
```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 5. Instalar Dependências Python
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Instalar Navegadores do Playwright
```bash
playwright install
playwright install-deps
```

### 7. Configurar Variáveis de Ambiente
```bash
cp .env.example .env
nano .env  # ou use seu editor preferido
```

### 8. Testar a Instalação
```bash
python test_system.py
```

### 9. Executar o Sistema
```bash
python main.py
```

## 🍎 Instalação no macOS

### 1. Instalar Homebrew (se não tiver)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Instalar Dependências
```bash
# Python 3.11
brew install python@3.11

# Git (se não tiver)
brew install git
```

### 3. Clonar e Configurar
```bash
git clone <url-do-repositorio>
cd price_monitor_bot

# Criar ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Instalar Playwright
playwright install
```

### 4. Configurar e Executar
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações

python test_system.py
python main.py
```

## 🪟 Instalação no Windows

### Opção 1: WSL2 (Recomendado)

1. **Instalar WSL2**:
   - Abra PowerShell como administrador
   - Execute: `wsl --install`
   - Reinicie o computador
   - Configure Ubuntu no WSL2

2. **Seguir instruções do Linux** dentro do WSL2

### Opção 2: Instalação Nativa

1. **Instalar Python 3.11**:
   - Baixe de [python.org](https://www.python.org/downloads/)
   - Marque "Add Python to PATH" durante a instalação

2. **Instalar Git**:
   - Baixe de [git-scm.com](https://git-scm.com/download/win)

3. **Clonar e Configurar**:
```cmd
git clone <url-do-repositorio>
cd price_monitor_bot

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Instalar Playwright
playwright install
```

4. **Configurar e Executar**:
```cmd
copy .env.example .env
# Edite o arquivo .env

python test_system.py
python main.py
```

## 🐳 Instalação com Docker

### 1. Criar Dockerfile
```dockerfile
FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    git \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /app

# Copiar arquivos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Playwright
RUN playwright install --with-deps

# Copiar código
COPY . .

# Criar diretórios necessários
RUN mkdir -p data logs

# Expor porta
EXPOSE 5000

# Comando padrão
CMD ["python", "main.py"]
```

### 2. Criar docker-compose.yml
```yaml
version: '3.8'

services:
  price-monitor:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./.env:/app/.env
    restart: unless-stopped
    environment:
      - FLASK_HOST=0.0.0.0
```

### 3. Executar
```bash
docker-compose up -d
```

## ⚙️ Configuração Detalhada

### Arquivo .env

```env
# ===== TELEGRAM =====
# Token do bot (obrigatório para alertas via Telegram)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# ===== BANCO DE DADOS =====
# Caminho do banco SQLite
DATABASE_URL=sqlite:///data/price_monitor.db

# ===== FLASK =====
# Host da aplicação web (0.0.0.0 para acesso externo)
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False

# ===== LOGGING =====
# Nível de log: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
LOG_FILE=logs/price_monitor.log

# ===== SCRAPING =====
# Delay entre requisições (segundos)
MIN_DELAY=2
MAX_DELAY=5

# Timeout para requisições (segundos)
REQUEST_TIMEOUT=30
```

### Obter Token do Telegram

1. **Criar Bot**:
   - Abra o Telegram
   - Procure por `@BotFather`
   - Envie `/newbot`
   - Escolha um nome e username para o bot
   - Copie o token fornecido

2. **Configurar Bot**:
   - Cole o token no arquivo `.env`
   - Opcional: Configure foto e descrição do bot

3. **Obter Chat ID**:
   - Procure por `@userinfobot` no Telegram
   - Envie qualquer mensagem
   - Use o ID retornado para configurar alertas

## 🔧 Configuração do Sistema

### Permissões de Arquivo
```bash
# Tornar scripts executáveis
chmod +x main.py test_system.py

# Definir permissões dos diretórios
chmod 755 data logs
chmod 644 .env
```

### Configuração de Firewall

#### Ubuntu/Debian
```bash
# Permitir porta 5000
sudo ufw allow 5000/tcp
sudo ufw reload
```

#### CentOS/RHEL
```bash
# Permitir porta 5000
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

### Configuração como Serviço (Linux)

1. **Criar arquivo de serviço**:
```bash
sudo nano /etc/systemd/system/price-monitor.service
```

2. **Conteúdo do arquivo**:
```ini
[Unit]
Description=Bot de Monitoramento de Preços
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/price_monitor_bot
Environment=PATH=/home/ubuntu/price_monitor_bot/venv/bin
ExecStart=/home/ubuntu/price_monitor_bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. **Ativar serviço**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable price-monitor
sudo systemctl start price-monitor
```

4. **Verificar status**:
```bash
sudo systemctl status price-monitor
```

## 🧪 Verificação da Instalação

### Testes Básicos
```bash
# Teste completo do sistema
python test_system.py

# Teste específico do scraper
python -c "from src.scraper import ScraperManager; s = ScraperManager(); print('Scraper OK')"

# Teste do banco de dados
python -c "from src.database import init_database; init_database(); print('Banco OK')"

# Teste da interface web
curl http://localhost:5000/api/stats
```

### Verificação de Logs
```bash
# Ver logs em tempo real
tail -f logs/price_monitor.log

# Verificar erros
grep ERROR logs/price_monitor.log

# Verificar inicialização
grep "SISTEMA INICIADO" logs/price_monitor.log
```

## 🔍 Troubleshooting de Instalação

### Erro: "Python 3.11 not found"
```bash
# Ubuntu/Debian
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11

# macOS
brew install python@3.11

# Windows
# Baixar e instalar do site oficial do Python
```

### Erro: "playwright install failed"
```bash
# Instalar dependências manualmente
sudo apt install -y libnss3-dev libatk-bridge2.0-dev libdrm2 libxkbcommon0

# Reinstalar Playwright
pip uninstall playwright
pip install playwright
playwright install --with-deps
```

### Erro: "Permission denied"
```bash
# Corrigir permissões
chmod +x main.py
chmod 755 data logs
sudo chown -R $USER:$USER .
```

### Erro: "Port 5000 already in use"
```bash
# Encontrar processo usando a porta
sudo lsof -i :5000

# Matar processo (substitua PID)
sudo kill -9 PID

# Ou alterar porta no .env
echo "FLASK_PORT=5001" >> .env
```

## 📊 Monitoramento

### Logs Importantes
- **Inicialização**: Confirma que todos os módulos foram carregados
- **Scraping**: Registra tentativas e sucessos de extração de dados
- **Alertas**: Mostra quando alertas são disparados
- **Erros**: Indica problemas que precisam de atenção

### Métricas de Performance
```bash
# Uso de CPU e memória
top -p $(pgrep -f "python main.py")

# Espaço em disco
du -sh data/ logs/

# Conexões de rede
netstat -tulpn | grep :5000
```

## 🔄 Atualizações

### Atualizar o Sistema
```bash
# Parar o serviço
sudo systemctl stop price-monitor

# Fazer backup
cp -r data data_backup_$(date +%Y%m%d)

# Atualizar código
git pull origin main

# Atualizar dependências
source venv/bin/activate
pip install -r requirements.txt

# Testar
python test_system.py

# Reiniciar serviço
sudo systemctl start price-monitor
```

## 🆘 Suporte

Se encontrar problemas durante a instalação:

1. **Verifique os logs**: `tail -f logs/price_monitor.log`
2. **Execute os testes**: `python test_system.py`
3. **Consulte o README**: Documentação completa
4. **Abra uma issue**: No repositório do GitHub

---

**Instalação concluída com sucesso? Acesse http://localhost:5000 e comece a monitorar preços!** 🎉

