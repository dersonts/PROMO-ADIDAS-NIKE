"""
Módulo de Web Scraping para monitoramento de preços
Suporta tanto scraping estático (requests/BeautifulSoup) quanto dinâmico (Playwright)
"""

import logging
import random
import time
import re
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, Browser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from config.settings import Config

logger = logging.getLogger(__name__)

class ProductData:
    """Classe para representar dados de um produto"""
    def __init__(self, name: str, price: float, original_price: float = None, 
                 url: str = "", image_url: str = "", availability: str = ""):
        self.name = name
        self.price = price
        self.original_price = original_price or price
        self.url = url
        self.image_url = image_url
        self.availability = availability
    
    def __repr__(self):
        return f"ProductData(name='{self.name}', price={self.price}, url='{self.url}')"

class BaseScraper(ABC):
    """Classe base abstrata para todos os scrapers"""
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
    
    def setup_session(self):
        """Configura a sessão HTTP com headers padrão"""
        self.session.headers.update({
            'User-Agent': random.choice(Config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def random_delay(self):
        """Adiciona delay aleatório entre requisições"""
        delay = random.uniform(Config.MIN_DELAY, Config.MAX_DELAY)
        time.sleep(delay)
    
    def extract_price(self, price_text: str) -> float:
        """Extrai valor numérico do texto de preço"""
        if not price_text:
            return 0.0
        
        # Remove caracteres não numéricos exceto vírgula e ponto
        price_clean = re.sub(r'[^\d,.]', '', price_text.replace(',', '.'))
        
        try:
            return float(price_clean)
        except ValueError:
            logger.warning(f"Não foi possível extrair preço de: {price_text}")
            return 0.0
    
    @abstractmethod
    def scrape_product(self, url: str) -> Optional[ProductData]:
        """Método abstrato para scraping de produto"""
        pass

class StaticScraper(BaseScraper):
    """Scraper para conteúdo estático usando requests e BeautifulSoup"""
    
    def scrape_product(self, url: str) -> Optional[ProductData]:
        """Faz scraping de um produto usando requests/BeautifulSoup"""
        try:
            logger.info(f"Fazendo scraping estático de: {url}")
            
            # Adiciona delay aleatório
            self.random_delay()
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Detecta o site e usa a lógica específica
            domain = urlparse(url).netloc.lower()
            
            if 'nike' in domain:
                return self._scrape_nike_static(soup, url)
            elif 'adidas' in domain:
                return self._scrape_adidas_static(soup, url)
            else:
                return self._scrape_generic(soup, url)
                
        except Exception as e:
            logger.error(f"Erro no scraping estático de {url}: {e}")
            return None
    
    def _scrape_nike_static(self, soup: BeautifulSoup, url: str) -> Optional[ProductData]:
        """Scraping específico para Nike (método estático)"""
        try:
            # Seletores comuns da Nike
            name_selectors = [
                'h1[data-automation-id="product-title"]',
                'h1.headline-5',
                'h1.pdp_product_title'
            ]
            
            price_selectors = [
                '[data-automation-id="product-price"]',
                '.product-price',
                '.price-current'
            ]
            
            name = self._find_text_by_selectors(soup, name_selectors)
            price_text = self._find_text_by_selectors(soup, price_selectors)
            
            if not name or not price_text:
                logger.warning(f"Dados incompletos para Nike: {url}")
                return None
            
            price = self.extract_price(price_text)
            
            # Busca imagem
            image_url = ""
            img_tag = soup.find('img', {'alt': re.compile(name[:20], re.I)})
            if img_tag and img_tag.get('src'):
                image_url = urljoin(url, img_tag['src'])
            
            return ProductData(
                name=name.strip(),
                price=price,
                url=url,
                image_url=image_url
            )
            
        except Exception as e:
            logger.error(f"Erro no scraping Nike estático: {e}")
            return None
    
    def _scrape_adidas_static(self, soup: BeautifulSoup, url: str) -> Optional[ProductData]:
        """Scraping específico para Adidas (método estático)"""
        try:
            # Seletores comuns da Adidas
            name_selectors = [
                'h1[data-auto-id="product-title"]',
                'h1.name___JQmUl',
                'h1.product_title'
            ]
            
            price_selectors = [
                '[data-auto-id="price"]',
                '.price___1JvDJ',
                '.product-price'
            ]
            
            name = self._find_text_by_selectors(soup, name_selectors)
            price_text = self._find_text_by_selectors(soup, price_selectors)
            
            if not name or not price_text:
                logger.warning(f"Dados incompletos para Adidas: {url}")
                return None
            
            price = self.extract_price(price_text)
            
            # Busca imagem
            image_url = ""
            img_tag = soup.find('img', {'alt': re.compile(name[:20], re.I)})
            if img_tag and img_tag.get('src'):
                image_url = urljoin(url, img_tag['src'])
            
            return ProductData(
                name=name.strip(),
                price=price,
                url=url,
                image_url=image_url
            )
            
        except Exception as e:
            logger.error(f"Erro no scraping Adidas estático: {e}")
            return None
    
    def _scrape_generic(self, soup: BeautifulSoup, url: str) -> Optional[ProductData]:
        """Scraping genérico para outros sites"""
        try:
            # Seletores genéricos comuns
            name_selectors = [
                'h1', 'h2', 
                '[class*="title"]', '[class*="name"]', '[class*="product"]',
                '[id*="title"]', '[id*="name"]', '[id*="product"]'
            ]
            
            price_selectors = [
                '[class*="price"]', '[class*="cost"]', '[class*="value"]',
                '[id*="price"]', '[id*="cost"]', '[id*="value"]'
            ]
            
            name = self._find_text_by_selectors(soup, name_selectors)
            price_text = self._find_text_by_selectors(soup, price_selectors)
            
            if not name or not price_text:
                logger.warning(f"Dados incompletos para site genérico: {url}")
                return None
            
            price = self.extract_price(price_text)
            
            return ProductData(
                name=name.strip(),
                price=price,
                url=url
            )
            
        except Exception as e:
            logger.error(f"Erro no scraping genérico: {e}")
            return None
    
    def _find_text_by_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """Busca texto usando uma lista de seletores CSS"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        return ""

class DynamicScraper(BaseScraper):
    """Scraper para conteúdo dinâmico usando Playwright"""
    
    def __init__(self):
        super().__init__()
        self.playwright = None
        self.browser = None
    
    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def scrape_product(self, url: str) -> Optional[ProductData]:
        """Faz scraping de um produto usando Playwright"""
        try:
            logger.info(f"Fazendo scraping dinâmico de: {url}")
            
            page = self.browser.new_page()
            
            # Configura User-Agent
            page.set_extra_http_headers({
                'User-Agent': random.choice(Config.USER_AGENTS)
            })
            
            # Navega para a página
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Adiciona delay para carregamento completo
            page.wait_for_timeout(3000)
            
            # Detecta o site e usa a lógica específica
            domain = urlparse(url).netloc.lower()
            
            if 'nike' in domain:
                result = self._scrape_nike_dynamic(page, url)
            elif 'adidas' in domain:
                result = self._scrape_adidas_dynamic(page, url)
            else:
                result = self._scrape_generic_dynamic(page, url)
            
            page.close()
            return result
                
        except Exception as e:
            logger.error(f"Erro no scraping dinâmico de {url}: {e}")
            return None
    
    def _scrape_nike_dynamic(self, page: Page, url: str) -> Optional[ProductData]:
        """Scraping específico para Nike (método dinâmico)"""
        try:
            # Aguarda elementos carregarem
            page.wait_for_selector('h1', timeout=10000)
            
            # Seletores para Nike
            name_selectors = [
                'h1[data-automation-id="product-title"]',
                'h1.headline-5',
                'h1.pdp_product_title'
            ]
            
            price_selectors = [
                '[data-automation-id="product-price"]',
                '.product-price',
                '.price-current'
            ]
            
            name = self._find_text_by_selectors_dynamic(page, name_selectors)
            price_text = self._find_text_by_selectors_dynamic(page, price_selectors)
            
            if not name or not price_text:
                logger.warning(f"Dados incompletos para Nike dinâmico: {url}")
                return None
            
            price = self.extract_price(price_text)
            
            # Busca imagem
            image_url = ""
            try:
                img_element = page.query_selector('img[alt*="' + name[:20] + '"]')
                if img_element:
                    image_url = img_element.get_attribute('src') or ""
            except:
                pass
            
            return ProductData(
                name=name.strip(),
                price=price,
                url=url,
                image_url=image_url
            )
            
        except Exception as e:
            logger.error(f"Erro no scraping Nike dinâmico: {e}")
            return None
    
    def _scrape_adidas_dynamic(self, page: Page, url: str) -> Optional[ProductData]:
        """Scraping específico para Adidas (método dinâmico)"""
        try:
            # Aguarda elementos carregarem
            page.wait_for_selector('h1', timeout=10000)
            
            # Seletores para Adidas
            name_selectors = [
                'h1[data-auto-id="product-title"]',
                'h1.name___JQmUl',
                'h1.product_title'
            ]
            
            price_selectors = [
                '[data-auto-id="price"]',
                '.price___1JvDJ',
                '.product-price'
            ]
            
            name = self._find_text_by_selectors_dynamic(page, name_selectors)
            price_text = self._find_text_by_selectors_dynamic(page, price_selectors)
            
            if not name or not price_text:
                logger.warning(f"Dados incompletos para Adidas dinâmico: {url}")
                return None
            
            price = self.extract_price(price_text)
            
            # Busca imagem
            image_url = ""
            try:
                img_element = page.query_selector('img[alt*="' + name[:20] + '"]')
                if img_element:
                    image_url = img_element.get_attribute('src') or ""
            except:
                pass
            
            return ProductData(
                name=name.strip(),
                price=price,
                url=url,
                image_url=image_url
            )
            
        except Exception as e:
            logger.error(f"Erro no scraping Adidas dinâmico: {e}")
            return None
    
    def _scrape_generic_dynamic(self, page: Page, url: str) -> Optional[ProductData]:
        """Scraping genérico para outros sites (método dinâmico)"""
        try:
            # Aguarda elementos carregarem
            page.wait_for_selector('h1', timeout=10000)
            
            # Seletores genéricos
            name_selectors = [
                'h1', 'h2',
                '[class*="title"]', '[class*="name"]', '[class*="product"]'
            ]
            
            price_selectors = [
                '[class*="price"]', '[class*="cost"]', '[class*="value"]'
            ]
            
            name = self._find_text_by_selectors_dynamic(page, name_selectors)
            price_text = self._find_text_by_selectors_dynamic(page, price_selectors)
            
            if not name or not price_text:
                logger.warning(f"Dados incompletos para site genérico dinâmico: {url}")
                return None
            
            price = self.extract_price(price_text)
            
            return ProductData(
                name=name.strip(),
                price=price,
                url=url
            )
            
        except Exception as e:
            logger.error(f"Erro no scraping genérico dinâmico: {e}")
            return None
    
    def _find_text_by_selectors_dynamic(self, page: Page, selectors: List[str]) -> str:
        """Busca texto usando uma lista de seletores CSS no Playwright"""
        for selector in selectors:
            try:
                element = page.query_selector(selector)
                if element:
                    text = element.inner_text().strip()
                    if text:
                        return text
            except:
                continue
        return ""

class ScraperManager:
    """Gerenciador de scrapers que decide qual usar baseado no site"""
    
    def __init__(self):
        self.static_scraper = StaticScraper()
        # Sites que requerem scraping dinâmico
        self.dynamic_sites = ['nike.com', 'adidas.com', 'adidas.com.br']
    
    def scrape_product(self, url: str) -> Optional[ProductData]:
        """Faz scraping de um produto usando o scraper apropriado"""
        domain = urlparse(url).netloc.lower()
        
        # Verifica se precisa de scraping dinâmico
        needs_dynamic = any(site in domain for site in self.dynamic_sites)
        
        if needs_dynamic:
            logger.info(f"Usando scraper dinâmico para: {domain}")
            with DynamicScraper() as dynamic_scraper:
                return dynamic_scraper.scrape_product(url)
        else:
            logger.info(f"Usando scraper estático para: {domain}")
            return self.static_scraper.scrape_product(url)
    
    def test_scraper(self, url: str) -> Dict:
        """Testa o scraper em uma URL e retorna informações de debug"""
        result = {
            'url': url,
            'success': False,
            'data': None,
            'error': None,
            'scraper_type': None
        }
        
        try:
            domain = urlparse(url).netloc.lower()
            needs_dynamic = any(site in domain for site in self.dynamic_sites)
            result['scraper_type'] = 'dynamic' if needs_dynamic else 'static'
            
            product_data = self.scrape_product(url)
            
            if product_data:
                result['success'] = True
                result['data'] = {
                    'name': product_data.name,
                    'price': product_data.price,
                    'original_price': product_data.original_price,
                    'image_url': product_data.image_url,
                    'availability': product_data.availability
                }
            else:
                result['error'] = 'Não foi possível extrair dados do produto'
                
        except Exception as e:
            result['error'] = str(e)
        
        return result

