"""
Módulo de banco de dados para o Bot de Monitoramento de Preços
Gerencia modelos SQLAlchemy e operações de banco de dados
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.exc import SQLAlchemyError

from config.settings import Config

logger = logging.getLogger(__name__)

# Base para os modelos
Base = declarative_base()

# Engine e Session globais
engine = None
SessionLocal = None

class Product(Base):
    """Modelo para produtos monitorados"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    url = Column(Text, nullable=False, unique=True)
    image_url = Column(Text)
    original_price = Column(Float)
    current_price = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
    
    # Relacionamentos
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name[:50]}...', price={self.current_price})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o produto para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'image_url': self.image_url,
            'original_price': self.original_price,
            'current_price': self.current_price,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'active': self.active
        }

class PriceHistory(Base):
    """Modelo para histórico de preços"""
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relacionamento
    product = relationship("Product", back_populates="price_history")
    
    def __repr__(self):
        return f"<PriceHistory(product_id={self.product_id}, price={self.price}, timestamp={self.timestamp})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o histórico para dicionário"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'price': self.price,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class Alert(Base):
    """Modelo para alertas de preço"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    chat_id = Column(String(100), nullable=False)  # ID do chat do Telegram
    threshold_price = Column(Float)  # Preço limite para alerta
    alert_type = Column(String(50), nullable=False)  # 'static', 'percentage', 'lowest_ever'
    percentage_threshold = Column(Float)  # Para alertas de porcentagem
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime)
    
    # Relacionamento
    product = relationship("Product", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, product_id={self.product_id}, type={self.alert_type}, active={self.active})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o alerta para dicionário"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'chat_id': self.chat_id,
            'threshold_price': self.threshold_price,
            'alert_type': self.alert_type,
            'percentage_threshold': self.percentage_threshold,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None
        }

def init_database():
    """Inicializa o banco de dados"""
    global engine, SessionLocal
    
    try:
        # Cria o diretório de dados se não existir
        db_path = Config.DATABASE_URL.replace('sqlite:///', '')
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Cria engine
        engine = create_engine(
            Config.DATABASE_URL,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True
        )
        
        # Cria SessionLocal
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Cria todas as tabelas
        Base.metadata.create_all(bind=engine)
        
        logger.info("Banco de dados inicializado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        raise

def get_db() -> Session:
    """Retorna uma sessão do banco de dados"""
    if SessionLocal is None:
        raise RuntimeError("Banco de dados não foi inicializado. Chame init_database() primeiro.")
    
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise

class DatabaseManager:
    """Gerenciador de operações do banco de dados"""
    
    @staticmethod
    def add_product(name: str, url: str, price: float, image_url: str = "", original_price: float = None) -> Optional[Product]:
        """Adiciona um novo produto ao banco de dados"""
        db = get_db()
        try:
            # Verifica se o produto já existe
            existing = db.query(Product).filter(Product.url == url).first()
            if existing:
                logger.warning(f"Produto já existe: {url}")
                return existing
            
            product = Product(
                name=name,
                url=url,
                image_url=image_url,
                original_price=original_price or price,
                current_price=price,
                last_updated=datetime.utcnow()
            )
            
            db.add(product)
            db.commit()
            db.refresh(product)
            
            # Adiciona primeiro registro no histórico
            DatabaseManager.add_price_history(product.id, price)
            
            logger.info(f"Produto adicionado: {name} - R$ {price}")
            return product
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Erro ao adicionar produto: {e}")
            return None
        finally:
            db.close()
    
    @staticmethod
    def update_product_price(product_id: int, new_price: float) -> bool:
        """Atualiza o preço de um produto"""
        db = get_db()
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                logger.warning(f"Produto não encontrado: {product_id}")
                return False
            
            old_price = product.current_price
            product.current_price = new_price
            product.last_updated = datetime.utcnow()
            
            db.commit()
            
            # Adiciona ao histórico se o preço mudou
            if old_price != new_price:
                DatabaseManager.add_price_history(product_id, new_price)
                logger.info(f"Preço atualizado para produto {product_id}: R$ {old_price} -> R$ {new_price}")
            
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Erro ao atualizar preço: {e}")
            return False
        finally:
            db.close()
    
    @staticmethod
    def add_price_history(product_id: int, price: float) -> bool:
        """Adiciona um registro ao histórico de preços"""
        db = get_db()
        try:
            history = PriceHistory(
                product_id=product_id,
                price=price,
                timestamp=datetime.utcnow()
            )
            
            db.add(history)
            db.commit()
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Erro ao adicionar histórico de preço: {e}")
            return False
        finally:
            db.close()
    
    @staticmethod
    def get_product_by_url(url: str) -> Optional[Product]:
        """Busca produto por URL"""
        db = get_db()
        try:
            return db.query(Product).filter(Product.url == url).first()
        finally:
            db.close()
    
    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Product]:
        """Busca produto por ID"""
        db = get_db()
        try:
            return db.query(Product).filter(Product.id == product_id).first()
        finally:
            db.close()
    
    @staticmethod
    def get_all_products(active_only: bool = True) -> List[Product]:
        """Retorna todos os produtos"""
        db = get_db()
        try:
            query = db.query(Product)
            if active_only:
                query = query.filter(Product.active == True)
            return query.all()
        finally:
            db.close()
    
    @staticmethod
    def get_price_history(product_id: int, limit: int = 100) -> List[PriceHistory]:
        """Retorna histórico de preços de um produto"""
        db = get_db()
        try:
            return db.query(PriceHistory)\
                    .filter(PriceHistory.product_id == product_id)\
                    .order_by(desc(PriceHistory.timestamp))\
                    .limit(limit)\
                    .all()
        finally:
            db.close()
    
    @staticmethod
    def get_lowest_price(product_id: int) -> Optional[float]:
        """Retorna o menor preço já registrado para um produto"""
        db = get_db()
        try:
            result = db.query(PriceHistory.price)\
                      .filter(PriceHistory.product_id == product_id)\
                      .order_by(PriceHistory.price)\
                      .first()
            return result[0] if result else None
        finally:
            db.close()
    
    @staticmethod
    def add_alert(product_id: int, chat_id: str, alert_type: str, 
                  threshold_price: float = None, percentage_threshold: float = None) -> Optional[Alert]:
        """Adiciona um novo alerta"""
        db = get_db()
        try:
            # Verifica se já existe um alerta similar
            existing = db.query(Alert).filter(
                Alert.product_id == product_id,
                Alert.chat_id == chat_id,
                Alert.alert_type == alert_type,
                Alert.active == True
            ).first()
            
            if existing:
                logger.warning(f"Alerta similar já existe para produto {product_id}")
                return existing
            
            alert = Alert(
                product_id=product_id,
                chat_id=chat_id,
                alert_type=alert_type,
                threshold_price=threshold_price,
                percentage_threshold=percentage_threshold
            )
            
            db.add(alert)
            db.commit()
            db.refresh(alert)
            
            logger.info(f"Alerta adicionado: produto {product_id}, tipo {alert_type}")
            return alert
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Erro ao adicionar alerta: {e}")
            return None
        finally:
            db.close()
    
    @staticmethod
    def get_active_alerts(product_id: int = None) -> List[Alert]:
        """Retorna alertas ativos"""
        db = get_db()
        try:
            query = db.query(Alert).filter(Alert.active == True)
            if product_id:
                query = query.filter(Alert.product_id == product_id)
            return query.all()
        finally:
            db.close()
    
    @staticmethod
    def update_alert_triggered(alert_id: int) -> bool:
        """Marca um alerta como disparado"""
        db = get_db()
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if alert:
                alert.last_triggered = datetime.utcnow()
                db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Erro ao atualizar alerta: {e}")
            return False
        finally:
            db.close()
    
    @staticmethod
    def deactivate_product(product_id: int) -> bool:
        """Desativa um produto (não o remove, apenas marca como inativo)"""
        db = get_db()
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if product:
                product.active = False
                db.commit()
                logger.info(f"Produto {product_id} desativado")
                return True
            return False
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Erro ao desativar produto: {e}")
            return False
        finally:
            db.close()
    
    @staticmethod
    def get_database_stats() -> Dict[str, Any]:
        """Retorna estatísticas do banco de dados"""
        db = get_db()
        try:
            stats = {
                'total_products': db.query(Product).count(),
                'active_products': db.query(Product).filter(Product.active == True).count(),
                'total_price_records': db.query(PriceHistory).count(),
                'total_alerts': db.query(Alert).count(),
                'active_alerts': db.query(Alert).filter(Alert.active == True).count()
            }
            return stats
        finally:
            db.close()

