"""
Módulo de integração com Telegram para o Bot de Monitoramento de Preços
Gerencia comandos do bot e envio de notificações
"""

import logging
import asyncio
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode

from src.database import DatabaseManager
from src.scraper import ScraperManager
from config.settings import Config

logger = logging.getLogger(__name__)

class TelegramBot:
    """Classe principal do bot do Telegram"""
    
    def __init__(self):
        self.application = None
        self.scraper_manager = ScraperManager()
        self.user_states = {}  # Para controlar estados de conversação
    
    def setup_bot(self):
        """Configura o bot do Telegram"""
        if not Config.TELEGRAM_BOT_TOKEN:
            logger.warning("Token do Telegram não configurado")
            return False
        
        try:
            # Cria a aplicação
            self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
            
            # Adiciona handlers de comandos
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("add", self.add_command))
            self.application.add_handler(CommandHandler("list", self.list_command))
            self.application.add_handler(CommandHandler("alerts", self.alerts_command))
            self.application.add_handler(CommandHandler("stats", self.stats_command))
            self.application.add_handler(CommandHandler("update", self.update_command))
            
            # Handler para callback queries (botões inline)
            self.application.add_handler(CallbackQueryHandler(self.button_callback))
            
            # Handler para mensagens de texto (URLs)
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            
            logger.info("Bot do Telegram configurado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao configurar bot do Telegram: {e}")
            return False
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        chat_id = update.effective_chat.id
        user_name = update.effective_user.first_name or "usuário"
        
        welcome_message = f"""
🤖 *Olá, {user_name}!*

Bem-vindo ao *Bot de Monitoramento de Preços*! 

Eu posso ajudá-lo a:
• 📦 Monitorar preços de produtos
• 🔔 Criar alertas personalizados
• 📊 Acompanhar histórico de preços
• 🛒 Encontrar as melhores ofertas

*Comandos disponíveis:*
/help - Ver todos os comandos
/add - Adicionar produto para monitoramento
/list - Listar produtos monitorados
/alerts - Gerenciar alertas
/stats - Ver estatísticas

Para começar, envie uma URL de produto ou use /add!
        """
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Salva o chat_id para futuras notificações
        logger.info(f"Novo usuário iniciou o bot: {chat_id} ({user_name})")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        help_message = """
📚 *Ajuda - Bot de Monitoramento de Preços*

*Comandos Principais:*
/start - Iniciar o bot
/help - Mostrar esta ajuda
/add <url> - Adicionar produto para monitoramento
/list - Listar todos os produtos monitorados
/alerts - Gerenciar seus alertas
/stats - Ver estatísticas do sistema
/update <id> - Atualizar preço de um produto

*Como usar:*

1️⃣ *Adicionar produto:*
   • Envie: `/add https://site.com/produto`
   • Ou apenas cole a URL do produto

2️⃣ *Criar alerta:*
   • Use /alerts para gerenciar
   • Escolha tipo: preço fixo, porcentagem ou mínimo histórico

3️⃣ *Acompanhar:*
   • Use /list para ver todos os produtos
   • Receba notificações automáticas quando os preços baixarem

*Sites suportados:*
✅ Nike, Adidas e muitos outros!

*Dúvidas?* Entre em contato com o desenvolvedor.
        """
        
        await update.message.reply_text(
            help_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def add_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /add para adicionar produto"""
        chat_id = update.effective_chat.id
        
        # Verifica se foi fornecida uma URL
        if context.args:
            url = ' '.join(context.args)
            await self.process_product_url(update, url)
        else:
            # Solicita URL
            await update.message.reply_text(
                "📦 *Adicionar Produto*\n\n"
                "Envie a URL do produto que deseja monitorar:\n"
                "Exemplo: `https://nike.com/produto`",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Define estado do usuário
            self.user_states[chat_id] = 'waiting_url'
    
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /list para listar produtos"""
        try:
            products = DatabaseManager.get_all_products()
            
            if not products:
                await update.message.reply_text(
                    "📦 *Nenhum produto monitorado*\n\n"
                    "Use /add para adicionar seu primeiro produto!",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            message = "📦 *Produtos Monitorados:*\n\n"
            
            for i, product in enumerate(products[:10], 1):  # Limita a 10 produtos
                status = "🟢" if product.active else "🔴"
                message += f"{status} *{i}. {product.name[:40]}...*\n"
                message += f"💰 Preço atual: R$ {product.current_price:.2f}\n"
                message += f"🕒 Atualizado: {product.last_updated.strftime('%d/%m %H:%M')}\n"
                message += f"🆔 ID: `{product.id}`\n\n"
            
            if len(products) > 10:
                message += f"... e mais {len(products) - 10} produtos.\n"
                message += "Use a interface web para ver todos!"
            
            # Adiciona botões inline
            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar Lista", callback_data="refresh_list")],
                [InlineKeyboardButton("🌐 Interface Web", url="http://localhost:5000")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro no comando /list: {e}")
            await update.message.reply_text(
                "❌ Erro ao listar produtos. Tente novamente."
            )
    
    async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /alerts para gerenciar alertas"""
        chat_id = str(update.effective_chat.id)
        
        try:
            # Busca alertas do usuário
            all_alerts = DatabaseManager.get_active_alerts()
            user_alerts = [alert for alert in all_alerts if alert.chat_id == chat_id]
            
            if not user_alerts:
                await update.message.reply_text(
                    "🔔 *Nenhum alerta configurado*\n\n"
                    "Use /list para ver produtos e criar alertas!",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            message = "🔔 *Seus Alertas:*\n\n"
            
            for i, alert in enumerate(user_alerts, 1):
                product = alert.product
                message += f"*{i}. {product.name[:30]}...*\n"
                
                if alert.alert_type == 'static':
                    message += f"📉 Preço abaixo de R$ {alert.threshold_price:.2f}\n"
                elif alert.alert_type == 'percentage':
                    message += f"📊 Queda de {alert.percentage_threshold}%\n"
                elif alert.alert_type == 'lowest_ever':
                    message += f"🎯 Novo mínimo histórico\n"
                
                message += f"💰 Preço atual: R$ {product.current_price:.2f}\n"
                message += f"🆔 ID: `{alert.id}`\n\n"
            
            # Botões inline
            keyboard = [
                [InlineKeyboardButton("➕ Criar Alerta", callback_data="create_alert")],
                [InlineKeyboardButton("🗑️ Remover Alerta", callback_data="remove_alert")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro no comando /alerts: {e}")
            await update.message.reply_text(
                "❌ Erro ao listar alertas. Tente novamente."
            )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /stats para mostrar estatísticas"""
        try:
            stats = DatabaseManager.get_database_stats()
            
            message = f"""
📊 *Estatísticas do Sistema*

📦 *Produtos:*
• Total: {stats['total_products']}
• Ativos: {stats['active_products']}

🔔 *Alertas:*
• Total: {stats['total_alerts']}
• Ativos: {stats['active_alerts']}

📈 *Dados:*
• Registros de preço: {stats['total_price_records']}

🌐 *Interface Web:*
Acesse http://localhost:5000 para mais detalhes!
            """
            
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Erro no comando /stats: {e}")
            await update.message.reply_text(
                "❌ Erro ao obter estatísticas. Tente novamente."
            )
    
    async def update_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /update para atualizar preço de um produto"""
        if not context.args:
            await update.message.reply_text(
                "🔄 *Atualizar Produto*\n\n"
                "Use: `/update <id_do_produto>`\n"
                "Exemplo: `/update 1`\n\n"
                "Use /list para ver os IDs dos produtos.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        try:
            product_id = int(context.args[0])
            product = DatabaseManager.get_product_by_id(product_id)
            
            if not product:
                await update.message.reply_text(
                    "❌ Produto não encontrado. Use /list para ver os produtos disponíveis."
                )
                return
            
            # Mostra mensagem de carregamento
            loading_msg = await update.message.reply_text(
                f"🔄 Atualizando preço de *{product.name[:30]}...*",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Faz scraping
            product_data = self.scraper_manager.scrape_product(product.url)
            
            if not product_data:
                await loading_msg.edit_text(
                    "❌ Não foi possível atualizar o produto. "
                    "Verifique se a URL ainda está válida."
                )
                return
            
            # Atualiza no banco
            old_price = product.current_price
            success = DatabaseManager.update_product_price(product_id, product_data.price)
            
            if success:
                price_change = product_data.price - old_price
                change_emoji = "📈" if price_change > 0 else "📉" if price_change < 0 else "➡️"
                
                message = f"""
✅ *Produto Atualizado!*

📦 *{product.name[:40]}...*

💰 *Preço:*
• Anterior: R$ {old_price:.2f}
• Atual: R$ {product_data.price:.2f}
• Variação: {change_emoji} R$ {abs(price_change):.2f}

🕒 Atualizado agora
                """
                
                await loading_msg.edit_text(message, parse_mode=ParseMode.MARKDOWN)
            else:
                await loading_msg.edit_text(
                    "❌ Erro ao salvar os dados atualizados."
                )
                
        except ValueError:
            await update.message.reply_text(
                "❌ ID inválido. Use apenas números.\n"
                "Exemplo: `/update 1`",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Erro no comando /update: {e}")
            await update.message.reply_text(
                "❌ Erro ao atualizar produto. Tente novamente."
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa mensagens de texto (principalmente URLs)"""
        chat_id = update.effective_chat.id
        text = update.message.text.strip()
        
        # Verifica se é uma URL
        if self.is_valid_url(text):
            await self.process_product_url(update, text)
        else:
            # Verifica se o usuário está em algum estado específico
            user_state = self.user_states.get(chat_id)
            
            if user_state == 'waiting_url':
                await update.message.reply_text(
                    "❌ Por favor, envie uma URL válida.\n"
                    "Exemplo: `https://nike.com/produto`",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # Mensagem padrão para texto não reconhecido
                await update.message.reply_text(
                    "🤔 Não entendi. Envie uma URL de produto ou use /help para ver os comandos disponíveis."
                )
    
    async def process_product_url(self, update: Update, url: str):
        """Processa uma URL de produto"""
        chat_id = update.effective_chat.id
        
        # Remove estado do usuário
        self.user_states.pop(chat_id, None)
        
        if not self.is_valid_url(url):
            await update.message.reply_text(
                "❌ URL inválida. Por favor, envie uma URL completa.\n"
                "Exemplo: `https://nike.com/produto`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Verifica se o produto já existe
        existing = DatabaseManager.get_product_by_url(url)
        if existing:
            await update.message.reply_text(
                f"⚠️ Este produto já está sendo monitorado!\n\n"
                f"📦 *{existing.name[:40]}...*\n"
                f"💰 Preço atual: R$ {existing.current_price:.2f}\n"
                f"🆔 ID: `{existing.id}`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Mostra mensagem de carregamento
        loading_msg = await update.message.reply_text(
            "🔍 Analisando produto...\n"
            "Isso pode levar alguns segundos."
        )
        
        try:
            # Faz scraping do produto
            product_data = self.scraper_manager.scrape_product(url)
            
            if not product_data:
                await loading_msg.edit_text(
                    "❌ Não foi possível extrair dados do produto.\n\n"
                    "Possíveis causas:\n"
                    "• URL inválida ou produto não encontrado\n"
                    "• Site com proteção anti-bot\n"
                    "• Estrutura do site não suportada\n\n"
                    "Tente uma URL diferente ou use /help para mais informações."
                )
                return
            
            # Adiciona ao banco de dados
            product = DatabaseManager.add_product(
                name=product_data.name,
                url=url,
                price=product_data.price,
                image_url=product_data.image_url,
                original_price=product_data.original_price
            )
            
            if product:
                message = f"""
✅ *Produto Adicionado com Sucesso!*

📦 *{product_data.name[:40]}...*
💰 *Preço:* R$ {product_data.price:.2f}
🆔 *ID:* `{product.id}`

O produto está sendo monitorado!
Use /alerts para criar alertas de preço.
                """
                
                # Botões inline
                keyboard = [
                    [InlineKeyboardButton("🔔 Criar Alerta", callback_data=f"alert_{product.id}")],
                    [InlineKeyboardButton("🌐 Ver no Site", url=url)]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await loading_msg.edit_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            else:
                await loading_msg.edit_text(
                    "❌ Erro ao salvar produto no banco de dados."
                )
                
        except Exception as e:
            logger.error(f"Erro ao processar URL {url}: {e}")
            await loading_msg.edit_text(
                "❌ Erro interno. Tente novamente mais tarde."
            )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa callbacks de botões inline"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "refresh_list":
            # Atualiza lista de produtos
            await self.list_command(update, context)
        elif data == "create_alert":
            await query.edit_message_text(
                "🔔 *Criar Alerta*\n\n"
                "Para criar um alerta, use a interface web:\n"
                "http://localhost:5000\n\n"
                "Ou use /list para ver os produtos e seus IDs.",
                parse_mode=ParseMode.MARKDOWN
            )
        elif data.startswith("alert_"):
            product_id = int(data.split("_")[1])
            await query.edit_message_text(
                f"🔔 *Criar Alerta para Produto {product_id}*\n\n"
                "Use a interface web para criar alertas personalizados:\n"
                "http://localhost:5000\n\n"
                "Tipos de alerta disponíveis:\n"
                "• 💰 Preço abaixo de um valor\n"
                "• 📊 Queda percentual\n"
                "• 🎯 Novo mínimo histórico",
                parse_mode=ParseMode.MARKDOWN
            )
    
    def is_valid_url(self, url: str) -> bool:
        """Verifica se uma string é uma URL válida"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    async def send_price_alert(self, chat_id: str, product, old_price: float, new_price: float, alert_type: str):
        """Envia alerta de preço via Telegram"""
        if not self.application:
            return False
        
        try:
            price_change = new_price - old_price
            change_percent = (price_change / old_price) * 100
            
            # Emoji baseado no tipo de alerta
            alert_emojis = {
                'static': '💰',
                'percentage': '📊',
                'lowest_ever': '🎯'
            }
            
            emoji = alert_emojis.get(alert_type, '🔔')
            
            message = f"""
{emoji} *ALERTA DE PREÇO!*

📦 *{product.name[:40]}...*

💰 *Preço:*
• Anterior: R$ {old_price:.2f}
• Atual: R$ {new_price:.2f}
• Economia: R$ {abs(price_change):.2f} ({abs(change_percent):.1f}%)

🕒 {alert_type.replace('_', ' ').title()}

🛒 Aproveite a oferta!
            """
            
            # Botão para ver no site
            keyboard = [[InlineKeyboardButton("🛒 Ver Produto", url=product.url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar alerta para {chat_id}: {e}")
            return False
    
    def run_bot(self):
        """Executa o bot do Telegram"""
        if not self.application:
            logger.error("Bot não foi configurado")
            return
        
        try:
            logger.info("Iniciando bot do Telegram...")
            self.application.run_polling(drop_pending_updates=True)
        except Exception as e:
            logger.error(f"Erro ao executar bot: {e}")

# Instância global do bot
telegram_bot = TelegramBot()

def init_telegram_bot():
    """Inicializa o bot do Telegram"""
    return telegram_bot.setup_bot()

def get_telegram_bot():
    """Retorna a instância do bot do Telegram"""
    return telegram_bot

