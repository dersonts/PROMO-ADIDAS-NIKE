import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    # Configurações do Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    
    # Configurações do banco de dados
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/price_monitor.db')
    
    # Configurações de scraping
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
    
    # Configurações de delay entre requisições (em segundos)
    MIN_DELAY = 2
    MAX_DELAY = 5
    
    # Configurações de logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'logs/price_monitor.log'
    
    # Configurações da interface web
    FLASK_HOST = '0.0.0.0'
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Configurações de alertas
    ALERT_TYPES = {
        'static': 'Preço abaixo de um valor fixo',
        'percentage': 'Queda percentual',
        'lowest_ever': 'Novo mínimo histórico'
    }

