#!/usr/bin/env python3
"""
Script de teste para o Bot de Monitoramento de Preços
Testa todos os componentes principais do sistema
"""

import sys
import os
import logging
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import Config
from src.database import init_database, DatabaseManager
from src.scraper import ScraperManager
from src.alert_manager import get_alert_manager

def setup_test_logging():
    """Configura logging para testes"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_database():
    """Testa funcionalidades do banco de dados"""
    print("🗄️  Testando banco de dados...")
    
    try:
        # Inicializa banco
        init_database()
        print("   ✅ Inicialização do banco: OK")
        
        # Testa estatísticas
        stats = DatabaseManager.get_database_stats()
        print(f"   📊 Estatísticas: {stats}")
        
        # Testa busca de produtos
        products = DatabaseManager.get_all_products()
        print(f"   📦 Produtos encontrados: {len(products)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro no banco de dados: {e}")
        return False

def test_scraper():
    """Testa o sistema de scraping"""
    print("🕷️  Testando scraper...")
    
    try:
        scraper = ScraperManager()
        
        # URLs de teste
        test_urls = [
            "https://www.nike.com.br/produto/tenis-nike-air-max-90-masculino",
            "https://www.adidas.com.br/tenis-ultraboost-22"
        ]
        
        for url in test_urls:
            print(f"   🔍 Testando: {url[:50]}...")
            
            try:
                result = scraper.test_scraper(url)
                
                if result['success']:
                    print(f"   ✅ Scraper {result['scraper_type']}: OK")
                    print(f"      Nome: {result['data']['name'][:40]}...")
                    print(f"      Preço: R$ {result['data']['price']:.2f}")
                else:
                    print(f"   ⚠️  Scraper falhou: {result['error']}")
                    
            except Exception as e:
                print(f"   ❌ Erro no teste: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro no scraper: {e}")
        return False

def test_alert_system():
    """Testa o sistema de alertas"""
    print("🔔 Testando sistema de alertas...")
    
    try:
        alert_manager = get_alert_manager()
        
        # Testa estatísticas
        stats = alert_manager.get_alert_statistics()
        print(f"   📊 Estatísticas de alertas: {stats}")
        
        # Testa sistema de alertas
        test_result = alert_manager.test_alert_system()
        
        if test_result['success']:
            print("   ✅ Sistema de alertas: OK")
            print(f"      Produtos verificados: {test_result['products_checked']}")
            print(f"      Produtos atualizados: {test_result['products_updated']}")
            print(f"      Alertas disparados: {test_result['alerts_triggered']}")
        else:
            print("   ⚠️  Sistema de alertas com problemas")
            for error in test_result['errors']:
                print(f"      ❌ {error}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro no sistema de alertas: {e}")
        return False

def test_web_interface():
    """Testa a interface web"""
    print("🌐 Testando interface web...")
    
    try:
        from web.app import create_app
        
        app = create_app()
        
        with app.test_client() as client:
            # Testa página principal
            response = client.get('/')
            if response.status_code == 200:
                print("   ✅ Dashboard: OK")
            else:
                print(f"   ❌ Dashboard falhou: {response.status_code}")
            
            # Testa API de estatísticas
            response = client.get('/api/stats')
            if response.status_code == 200:
                print("   ✅ API de estatísticas: OK")
            else:
                print(f"   ❌ API falhou: {response.status_code}")
            
            # Testa página de produtos
            response = client.get('/products')
            if response.status_code == 200:
                print("   ✅ Página de produtos: OK")
            else:
                print(f"   ❌ Página de produtos falhou: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro na interface web: {e}")
        return False

def test_configuration():
    """Testa configurações do sistema"""
    print("⚙️  Testando configurações...")
    
    try:
        # Verifica configurações básicas
        print(f"   📁 Banco de dados: {Config.DATABASE_URL}")
        print(f"   🌐 Flask host: {Config.FLASK_HOST}:{Config.FLASK_PORT}")
        print(f"   📝 Log level: {Config.LOG_LEVEL}")
        
        # Verifica token do Telegram
        if Config.TELEGRAM_BOT_TOKEN:
            print("   ✅ Token do Telegram: Configurado")
        else:
            print("   ⚠️  Token do Telegram: Não configurado")
        
        # Verifica diretórios
        directories = ['data', 'logs', 'web/templates', 'web/static']
        for directory in directories:
            if Path(directory).exists():
                print(f"   ✅ Diretório {directory}: OK")
            else:
                print(f"   ❌ Diretório {directory}: Não encontrado")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro nas configurações: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🧪 INICIANDO TESTES DO SISTEMA")
    print("=" * 50)
    
    setup_test_logging()
    
    tests = [
        ("Configurações", test_configuration),
        ("Banco de Dados", test_database),
        ("Scraper", test_scraper),
        ("Sistema de Alertas", test_alert_system),
        ("Interface Web", test_web_interface)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name.upper()}")
        print("-" * 30)
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"   ❌ Erro crítico: {e}")
            results[test_name] = False
    
    # Resumo dos resultados
    print("\n" + "=" * 50)
    print("📋 RESUMO DOS TESTES")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{test_name:20} {status}")
        if success:
            passed += 1
    
    print(f"\n📊 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("   O sistema está funcionando corretamente.")
        return 0
    else:
        print("⚠️  ALGUNS TESTES FALHARAM")
        print("   Verifique os erros acima e corrija os problemas.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

