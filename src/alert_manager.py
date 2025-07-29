"""
Módulo de gerenciamento de alertas para o Bot de Monitoramento de Preços
Detecta quedas de preço e envia notificações
"""

import logging
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from threading import Thread

from src.database import DatabaseManager
from src.scraper import ScraperManager
from src.telegram_bot import get_telegram_bot
from config.settings import Config

logger = logging.getLogger(__name__)

class AlertManager:
    """Gerenciador de alertas de preço"""
    
    def __init__(self):
        self.scraper_manager = ScraperManager()
        self.telegram_bot = get_telegram_bot()
        self.is_running = False
        self.scheduler_thread = None
        
        # Configurações de throttling
        self.last_alert_times = {}  # Para evitar spam de alertas
        self.min_alert_interval = 3600  # 1 hora entre alertas do mesmo tipo
    
    def start_monitoring(self):
        """Inicia o monitoramento automático"""
        if self.is_running:
            logger.warning("Monitoramento já está em execução")
            return
        
        logger.info("Iniciando monitoramento de alertas...")
        
        # Agenda verificações periódicas
        schedule.every(30).minutes.do(self.check_all_products)
        schedule.every(1).hours.do(self.cleanup_old_alerts)
        
        self.is_running = True
        
        # Inicia thread do scheduler
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Monitoramento de alertas iniciado")
    
    def stop_monitoring(self):
        """Para o monitoramento automático"""
        logger.info("Parando monitoramento de alertas...")
        self.is_running = False
        schedule.clear()
        logger.info("Monitoramento de alertas parado")
    
    def _run_scheduler(self):
        """Executa o scheduler em thread separada"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Verifica a cada minuto
    
    def check_all_products(self):
        """Verifica todos os produtos ativos para atualizações de preço"""
        logger.info("Iniciando verificação de todos os produtos...")
        
        try:
            products = DatabaseManager.get_all_products(active_only=True)
            
            if not products:
                logger.info("Nenhum produto ativo para verificar")
                return
            
            updated_count = 0
            alert_count = 0
            
            for product in products:
                try:
                    # Atualiza o preço do produto
                    old_price = product.current_price
                    updated = self.update_product_price(product.id)
                    
                    if updated:
                        updated_count += 1
                        
                        # Verifica alertas para este produto
                        alerts_triggered = self.check_product_alerts(product.id, old_price)
                        alert_count += alerts_triggered
                        
                        # Pequeno delay entre produtos
                        time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Erro ao verificar produto {product.id}: {e}")
                    continue
            
            logger.info(f"Verificação concluída: {updated_count} produtos atualizados, {alert_count} alertas disparados")
            
        except Exception as e:
            logger.error(f"Erro na verificação geral de produtos: {e}")
    
    def update_product_price(self, product_id: int) -> bool:
        """Atualiza o preço de um produto específico"""
        try:
            product = DatabaseManager.get_product_by_id(product_id)
            if not product:
                logger.warning(f"Produto {product_id} não encontrado")
                return False
            
            # Faz scraping do produto
            product_data = self.scraper_manager.scrape_product(product.url)
            
            if not product_data:
                logger.warning(f"Não foi possível atualizar produto {product_id}")
                return False
            
            # Atualiza no banco se o preço mudou
            if product_data.price != product.current_price:
                success = DatabaseManager.update_product_price(product_id, product_data.price)
                if success:
                    logger.info(f"Preço atualizado para produto {product_id}: {product.current_price} -> {product_data.price}")
                return success
            else:
                logger.debug(f"Preço inalterado para produto {product_id}")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao atualizar preço do produto {product_id}: {e}")
            return False
    
    def check_product_alerts(self, product_id: int, old_price: float) -> int:
        """Verifica alertas para um produto específico"""
        try:
            product = DatabaseManager.get_product_by_id(product_id)
            if not product:
                return 0
            
            current_price = product.current_price
            alerts = DatabaseManager.get_active_alerts(product_id)
            
            if not alerts:
                return 0
            
            alerts_triggered = 0
            
            for alert in alerts:
                try:
                    should_trigger = self.should_trigger_alert(alert, old_price, current_price, product_id)
                    
                    if should_trigger:
                        success = self.send_alert_notification(alert, product, old_price, current_price)
                        
                        if success:
                            # Marca o alerta como disparado
                            DatabaseManager.update_alert_triggered(alert.id)
                            alerts_triggered += 1
                            
                            # Registra para throttling
                            alert_key = f"{alert.id}_{alert.alert_type}"
                            self.last_alert_times[alert_key] = datetime.utcnow()
                            
                            logger.info(f"Alerta {alert.id} disparado para produto {product_id}")
                        
                except Exception as e:
                    logger.error(f"Erro ao processar alerta {alert.id}: {e}")
                    continue
            
            return alerts_triggered
            
        except Exception as e:
            logger.error(f"Erro ao verificar alertas do produto {product_id}: {e}")
            return 0
    
    def should_trigger_alert(self, alert, old_price: float, current_price: float, product_id: int) -> bool:
        """Determina se um alerta deve ser disparado"""
        
        # Verifica throttling
        alert_key = f"{alert.id}_{alert.alert_type}"
        last_alert_time = self.last_alert_times.get(alert_key)
        
        if last_alert_time:
            time_since_last = (datetime.utcnow() - last_alert_time).total_seconds()
            if time_since_last < self.min_alert_interval:
                logger.debug(f"Alerta {alert.id} em throttling (faltam {self.min_alert_interval - time_since_last:.0f}s)")
                return False
        
        # Verifica condições específicas do tipo de alerta
        if alert.alert_type == 'static':
            return self._check_static_alert(alert, current_price)
        elif alert.alert_type == 'percentage':
            return self._check_percentage_alert(alert, old_price, current_price)
        elif alert.alert_type == 'lowest_ever':
            return self._check_lowest_ever_alert(alert, current_price, product_id)
        
        return False
    
    def _check_static_alert(self, alert, current_price: float) -> bool:
        """Verifica alerta de preço fixo"""
        if not alert.threshold_price:
            return False
        
        return current_price <= alert.threshold_price
    
    def _check_percentage_alert(self, alert, old_price: float, current_price: float) -> bool:
        """Verifica alerta de queda percentual"""
        if not alert.percentage_threshold or old_price <= 0:
            return False
        
        price_drop_percent = ((old_price - current_price) / old_price) * 100
        
        return price_drop_percent >= alert.percentage_threshold
    
    def _check_lowest_ever_alert(self, alert, current_price: float, product_id: int) -> bool:
        """Verifica alerta de novo mínimo histórico"""
        try:
            lowest_price = DatabaseManager.get_lowest_price(product_id)
            
            if lowest_price is None:
                return False
            
            # Considera uma margem pequena para evitar alertas por diferenças mínimas
            margin = 0.01  # R$ 0,01
            return current_price < (lowest_price - margin)
            
        except Exception as e:
            logger.error(f"Erro ao verificar mínimo histórico: {e}")
            return False
    
    def send_alert_notification(self, alert, product, old_price: float, current_price: float) -> bool:
        """Envia notificação de alerta"""
        try:
            success = False
            
            # Envia via Telegram se configurado
            if alert.chat_id and alert.chat_id != 'web_user' and self.telegram_bot.application:
                telegram_success = asyncio.run(
                    self.telegram_bot.send_price_alert(
                        alert.chat_id, product, old_price, current_price, alert.alert_type
                    )
                )
                success = success or telegram_success
            
            # Log da notificação
            self._log_alert_notification(alert, product, old_price, current_price)
            
            return True  # Sempre retorna True para não bloquear outros alertas
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificação do alerta {alert.id}: {e}")
            return False
    
    def _log_alert_notification(self, alert, product, old_price: float, current_price: float):
        """Registra log detalhado da notificação"""
        price_change = current_price - old_price
        change_percent = (price_change / old_price) * 100 if old_price > 0 else 0
        
        log_message = (
            f"ALERTA DISPARADO - "
            f"Produto: {product.name[:30]}... | "
            f"Tipo: {alert.alert_type} | "
            f"Preço: {old_price:.2f} -> {current_price:.2f} | "
            f"Variação: {change_percent:.1f}% | "
            f"Chat: {alert.chat_id}"
        )
        
        logger.info(log_message)
    
    def cleanup_old_alerts(self):
        """Remove registros antigos de throttling"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            keys_to_remove = []
            for key, timestamp in self.last_alert_times.items():
                if timestamp < cutoff_time:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.last_alert_times[key]
            
            if keys_to_remove:
                logger.info(f"Limpeza: removidos {len(keys_to_remove)} registros antigos de throttling")
                
        except Exception as e:
            logger.error(f"Erro na limpeza de alertas antigos: {e}")
    
    def test_alert_system(self) -> Dict:
        """Testa o sistema de alertas"""
        logger.info("Iniciando teste do sistema de alertas...")
        
        results = {
            'products_checked': 0,
            'products_updated': 0,
            'alerts_triggered': 0,
            'errors': [],
            'success': False
        }
        
        try:
            # Pega alguns produtos para teste
            products = DatabaseManager.get_all_products(active_only=True)[:5]  # Limita a 5 para teste
            
            for product in products:
                results['products_checked'] += 1
                
                try:
                    old_price = product.current_price
                    updated = self.update_product_price(product.id)
                    
                    if updated:
                        results['products_updated'] += 1
                        
                        # Verifica alertas
                        alerts_triggered = self.check_product_alerts(product.id, old_price)
                        results['alerts_triggered'] += alerts_triggered
                        
                except Exception as e:
                    error_msg = f"Erro no produto {product.id}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            results['success'] = True
            logger.info(f"Teste concluído: {results}")
            
        except Exception as e:
            error_msg = f"Erro geral no teste: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
        
        return results
    
    def get_alert_statistics(self) -> Dict:
        """Retorna estatísticas dos alertas"""
        try:
            stats = DatabaseManager.get_database_stats()
            
            # Adiciona informações específicas de alertas
            all_alerts = DatabaseManager.get_active_alerts()
            
            alert_types = {}
            for alert in all_alerts:
                alert_type = alert.alert_type
                alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
            
            return {
                'total_alerts': stats['total_alerts'],
                'active_alerts': stats['active_alerts'],
                'alert_types': alert_types,
                'monitoring_active': self.is_running,
                'throttling_records': len(self.last_alert_times)
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de alertas: {e}")
            return {}

# Instância global do gerenciador de alertas
alert_manager = AlertManager()

def init_alert_manager():
    """Inicializa o gerenciador de alertas"""
    try:
        alert_manager.start_monitoring()
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar gerenciador de alertas: {e}")
        return False

def get_alert_manager():
    """Retorna a instância do gerenciador de alertas"""
    return alert_manager

