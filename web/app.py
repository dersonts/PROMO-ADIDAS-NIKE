"""
Aplicação Flask para interface web do Bot de Monitoramento de Preços
"""

import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.database import DatabaseManager, init_database
from src.scraper import ScraperManager
from config.settings import Config

logger = logging.getLogger(__name__)

def create_app():
    """Cria e configura a aplicação Flask"""
    app = Flask(__name__)
    app.secret_key = 'price_monitor_secret_key_change_in_production'
    
    # Habilita CORS
    CORS(app)
    
    # Inicializa o banco de dados
    try:
        init_database()
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
    
    # Inicializa o scraper manager
    scraper_manager = ScraperManager()
    
    @app.route('/')
    def dashboard():
        """Página principal - Dashboard"""
        try:
            stats = DatabaseManager.get_database_stats()
            recent_products = DatabaseManager.get_all_products()[:10]  # Últimos 10 produtos
            
            return render_template('dashboard.html', 
                                 stats=stats, 
                                 recent_products=recent_products)
        except Exception as e:
            logger.error(f"Erro no dashboard: {e}")
            flash(f"Erro ao carregar dashboard: {e}", 'error')
            return render_template('dashboard.html', stats={}, recent_products=[])
    
    @app.route('/products')
    def products():
        """Página de produtos"""
        try:
            all_products = DatabaseManager.get_all_products()
            return render_template('products.html', products=all_products)
        except Exception as e:
            logger.error(f"Erro ao carregar produtos: {e}")
            flash(f"Erro ao carregar produtos: {e}", 'error')
            return render_template('products.html', products=[])
    
    @app.route('/product/<int:product_id>')
    def product_detail(product_id):
        """Página de detalhes do produto"""
        try:
            product = DatabaseManager.get_product_by_id(product_id)
            if not product:
                flash('Produto não encontrado', 'error')
                return redirect(url_for('products'))
            
            # Busca histórico de preços
            price_history = DatabaseManager.get_price_history(product_id, limit=50)
            
            # Busca alertas ativos
            alerts = DatabaseManager.get_active_alerts(product_id)
            
            return render_template('product_detail.html', 
                                 product=product, 
                                 price_history=price_history,
                                 alerts=alerts)
        except Exception as e:
            logger.error(f"Erro ao carregar detalhes do produto: {e}")
            flash(f"Erro ao carregar produto: {e}", 'error')
            return redirect(url_for('products'))
    
    @app.route('/add_product', methods=['GET', 'POST'])
    def add_product():
        """Página para adicionar novo produto"""
        if request.method == 'POST':
            try:
                url = request.form.get('url', '').strip()
                if not url:
                    flash('URL é obrigatória', 'error')
                    return render_template('add_product.html')
                
                # Verifica se o produto já existe
                existing = DatabaseManager.get_product_by_url(url)
                if existing:
                    flash('Produto já está sendo monitorado', 'warning')
                    return redirect(url_for('product_detail', product_id=existing.id))
                
                # Faz scraping do produto
                product_data = scraper_manager.scrape_product(url)
                
                if not product_data:
                    flash('Não foi possível extrair dados do produto. Verifique a URL.', 'error')
                    return render_template('add_product.html')
                
                # Adiciona ao banco de dados
                product = DatabaseManager.add_product(
                    name=product_data.name,
                    url=url,
                    price=product_data.price,
                    image_url=product_data.image_url,
                    original_price=product_data.original_price
                )
                
                if product:
                    flash(f'Produto "{product_data.name}" adicionado com sucesso!', 'success')
                    return redirect(url_for('product_detail', product_id=product.id))
                else:
                    flash('Erro ao salvar produto no banco de dados', 'error')
                    
            except Exception as e:
                logger.error(f"Erro ao adicionar produto: {e}")
                flash(f'Erro ao adicionar produto: {e}', 'error')
        
        return render_template('add_product.html')
    
    @app.route('/alerts')
    def alerts():
        """Página de alertas"""
        try:
            active_alerts = DatabaseManager.get_active_alerts()
            return render_template('alerts.html', alerts=active_alerts)
        except Exception as e:
            logger.error(f"Erro ao carregar alertas: {e}")
            flash(f"Erro ao carregar alertas: {e}", 'error')
            return render_template('alerts.html', alerts=[])
    
    @app.route('/test_scraper', methods=['GET', 'POST'])
    def test_scraper():
        """Página para testar o scraper"""
        if request.method == 'POST':
            try:
                url = request.form.get('url', '').strip()
                if not url:
                    flash('URL é obrigatória', 'error')
                    return render_template('test_scraper.html')
                
                # Testa o scraper
                result = scraper_manager.test_scraper(url)
                
                return render_template('test_scraper.html', test_result=result)
                
            except Exception as e:
                logger.error(f"Erro ao testar scraper: {e}")
                flash(f'Erro ao testar scraper: {e}', 'error')
        
        return render_template('test_scraper.html')
    
    # API Endpoints
    @app.route('/api/products')
    def api_products():
        """API endpoint para listar produtos"""
        try:
            products = DatabaseManager.get_all_products()
            return jsonify([product.to_dict() for product in products])
        except Exception as e:
            logger.error(f"Erro na API de produtos: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/product/<int:product_id>/history')
    def api_product_history(product_id):
        """API endpoint para histórico de preços"""
        try:
            limit = request.args.get('limit', 50, type=int)
            history = DatabaseManager.get_price_history(product_id, limit)
            return jsonify([h.to_dict() for h in history])
        except Exception as e:
            logger.error(f"Erro na API de histórico: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/product/<int:product_id>/update', methods=['POST'])
    def api_update_product(product_id):
        """API endpoint para atualizar preço de um produto"""
        try:
            product = DatabaseManager.get_product_by_id(product_id)
            if not product:
                return jsonify({'error': 'Produto não encontrado'}), 404
            
            # Faz scraping atualizado
            product_data = scraper_manager.scrape_product(product.url)
            
            if not product_data:
                return jsonify({'error': 'Não foi possível atualizar o produto'}), 400
            
            # Atualiza no banco
            success = DatabaseManager.update_product_price(product_id, product_data.price)
            
            if success:
                return jsonify({
                    'success': True,
                    'old_price': product.current_price,
                    'new_price': product_data.price,
                    'message': 'Produto atualizado com sucesso'
                })
            else:
                return jsonify({'error': 'Erro ao atualizar produto'}), 500
                
        except Exception as e:
            logger.error(f"Erro ao atualizar produto: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/add_alert', methods=['POST'])
    def api_add_alert():
        """API endpoint para adicionar alerta"""
        try:
            data = request.get_json()
            
            product_id = data.get('product_id')
            chat_id = data.get('chat_id', 'web_user')  # Default para usuário web
            alert_type = data.get('alert_type')
            threshold_price = data.get('threshold_price')
            percentage_threshold = data.get('percentage_threshold')
            
            if not all([product_id, alert_type]):
                return jsonify({'error': 'Dados obrigatórios faltando'}), 400
            
            alert = DatabaseManager.add_alert(
                product_id=product_id,
                chat_id=chat_id,
                alert_type=alert_type,
                threshold_price=threshold_price,
                percentage_threshold=percentage_threshold
            )
            
            if alert:
                return jsonify({
                    'success': True,
                    'alert_id': alert.id,
                    'message': 'Alerta adicionado com sucesso'
                })
            else:
                return jsonify({'error': 'Erro ao adicionar alerta'}), 500
                
        except Exception as e:
            logger.error(f"Erro ao adicionar alerta: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/stats')
    def api_stats():
        """API endpoint para estatísticas"""
        try:
            stats = DatabaseManager.get_database_stats()
            return jsonify(stats)
        except Exception as e:
            logger.error(f"Erro na API de estatísticas: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Filtros de template
    @app.template_filter('currency')
    def currency_filter(value):
        """Filtro para formatar valores monetários"""
        if value is None:
            return "R$ 0,00"
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @app.template_filter('datetime')
    def datetime_filter(value):
        """Filtro para formatar datas"""
        if value is None:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                return value
        return value.strftime('%d/%m/%Y %H:%M')
    
    @app.template_filter('timeago')
    def timeago_filter(value):
        """Filtro para mostrar tempo relativo"""
        if value is None:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                return value
        
        now = datetime.utcnow()
        diff = now - value
        
        if diff.days > 0:
            return f"há {diff.days} dia{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"há {hours} hora{'s' if hours > 1 else ''}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"há {minutes} minuto{'s' if minutes > 1 else ''}"
        else:
            return "agora mesmo"
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.FLASK_DEBUG)

