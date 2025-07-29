#!/usr/bin/env python3
"""
Bot de Monitoramento de Preços
Ponto de entrada principal da aplicação
"""

import logging
import sys
import os
import signal
import threading
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import Config
from src.database import init_database
from src.telegram_bot import init_telegram_bot, get_telegram_bot
from src.alert_manager import init_alert_manager, get_alert_manager
from web.app import create_app

def setup_logging():
    """Configura o sistema de logging"""
    # Cria o diretório de logs se não existir
    Path('logs').mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )

def signal_handler(signum, frame):
    """Handler para sinais de sistema (Ctrl+C)"""
    logger = logging.getLogger(__name__)
    logger.info("Sinal de interrupção recebido, finalizando aplicação...")
    
    # Para o gerenciador de alertas
    try:
        alert_manager = get_alert_manager()
        alert_manager.stop_monitoring()
    except:
        pass
    
    print("\n👋 Bot finalizado!")
    sys.exit(0)

def run_telegram_bot():
    """Executa o bot do Telegram em thread separada"""
    try:
        telegram_bot = get_telegram_bot()
        if telegram_bot.application:
            telegram_bot.run_bot()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao executar bot do Telegram: {e}")

def main():
    """Função principal"""
    print("🤖 Iniciando Bot de Monitoramento de Preços...")
    
    # Configura logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Configura handler para sinais
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Inicializa o banco de dados
        logger.info("Inicializando banco de dados...")
        init_database()
        print("✅ Banco de dados inicializado")
        
        # Inicializa o bot do Telegram
        logger.info("Configurando bot do Telegram...")
        telegram_success = init_telegram_bot()
        
        if telegram_success:
            print("✅ Bot do Telegram configurado")
            
            # Inicia bot do Telegram em thread separada
            telegram_thread = threading.Thread(target=run_telegram_bot, daemon=True)
            telegram_thread.start()
            print("🚀 Bot do Telegram iniciado")
        else:
            print("⚠️  Bot do Telegram não configurado (token não fornecido)")
            print("   Para habilitar, configure TELEGRAM_BOT_TOKEN no arquivo .env")
        
        # Inicializa o gerenciador de alertas
        logger.info("Iniciando gerenciador de alertas...")
        alert_success = init_alert_manager()
        
        if alert_success:
            print("✅ Gerenciador de alertas iniciado")
        else:
            print("⚠️  Erro ao iniciar gerenciador de alertas")
        
        print("\n" + "="*60)
        print("🎉 SISTEMA INICIADO COM SUCESSO!")
        print("="*60)
        print(f"📊 Interface web: http://localhost:{Config.FLASK_PORT}")
        print(f"📝 Logs: {Config.LOG_FILE}")
        
        if telegram_success:
            print("💬 Bot do Telegram: Ativo")
        else:
            print("💬 Bot do Telegram: Inativo (configure o token)")
        
        if alert_success:
            print("🔔 Alertas automáticos: Ativos")
        else:
            print("🔔 Alertas automáticos: Inativos")
        
        print("\n📖 Funcionalidades disponíveis:")
        print("   • Adicionar produtos via interface web ou Telegram")
        print("   • Criar alertas personalizados")
        print("   • Monitoramento automático de preços")
        print("   • Notificações via Telegram")
        print("   • Histórico detalhado de preços")
        print("\n🛑 Para parar: Ctrl+C")
        print("="*60)
        
        # Inicia a aplicação Flask
        app = create_app()
        app.run(
            host=Config.FLASK_HOST,
            port=Config.FLASK_PORT,
            debug=Config.FLASK_DEBUG,
            use_reloader=False  # Evita problemas com threads
        )
        
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        print(f"❌ Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

