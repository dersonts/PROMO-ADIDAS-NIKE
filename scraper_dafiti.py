from bs4 import BeautifulSoup
import re
from .utils import brl_to_float, find_jsonld_prices, choose_price

def _safe_float_dot(s: str) -> float | None:
    try:
        return float(str(s).strip().replace(',', '.'))
    except Exception:
        return None

def parse_dafiti(html: str, url: str, prefer_price: str = "lowest") -> dict:
    soup = BeautifulSoup(html, 'lxml')

    # ===== Nome / Marca / Seller =====
    name = None
    for sel in ['h1.product-name[itemprop="name"]', 'h1[itemprop="name"]', 'h1.product-name', 'h1']:
        h1 = soup.select_one(sel)
        if h1 and h1.get_text(strip=True):
            name = h1.get_text(strip=True)
            break
    if not name:
        mt = soup.find('meta', property='og:title')
        if mt and mt.get('content'):
            name = mt['content']

    brand = None
    a_brand = soup.select_one('.product-brand a[title], a[itemprop="brand"]')
    if a_brand:
        brand = a_brand.get_text(strip=True)

    seller = None
    # Ex.: <p class="product-seller-name"> Vendido e entregue por <a>...</a>
    seller_wrap = soup.select_one('.product-seller-name')
    if seller_wrap:
        a = seller_wrap.find('a')
        if a:
            seller = a.get_text(strip=True)

    # ===== Preços (layout atual que você trouxe) =====
    candidates = []
    currency = "BRL"
    availability = None

    # Preço atual (finalPrice)
    el_final = soup.select_one('.catalog-detail-price .catalog-detail-price-value[data-field="finalPrice"]')
    price_current = None
    if el_final:
        # 1) atributo content=329.99 (mais confiável)
        if el_final.has_attr('content'):
            price_current = _safe_float_dot(el_final['content'])
        # 2) texto "R$ 329,99" como fallback
        if price_current is None:
            price_current = brl_to_float(el_final.get_text(" ", strip=True))
        if price_current is not None:
            candidates.append((price_current, "current"))

    # Preço cheio (specialPrice) – útil para mostrar economia
    el_special = soup.select_one('.catalog-detail-price .catalog-detail-price-special[data-field="specialPrice"]')
    price_original = None
    if el_special:
        price_original = brl_to_float(el_special.get_text(" ", strip=True))

    # % de desconto (quando existe)
    el_disc = soup.select_one('.catalog-detail-price .catalog-detail-price-discount')
    discount_percent = None
    if el_disc:
        # Ex.: "-49%"
        m = re.search(r'-?\s*(\d+)\s*%', el_disc.get_text())
        if m:
            try:
                discount_percent = int(m.group(1))
            except Exception:
                pass

    # Moeda / disponibilidade via microdados
    mt_cur = soup.select_one('meta[itemprop="priceCurrency"]')
    if mt_cur and mt_cur.get('content'):
        currency = mt_cur['content']

    mt_av = soup.select_one('meta[itemprop="availability"]')
    if mt_av and mt_av.get('content'):
        availability = mt_av['content']  # ex.: https://schema.org/InStock

    # Mensagem de esgotado como override (quando aparece no SSR)
    stock_msg = soup.select_one('#stock-available .stock-available-message')
    if stock_msg and 'esgotad' in stock_msg.get_text(strip=True).lower():
        availability = 'https://schema.org/OutOfStock'

    # ===== Parcelamento (opcional) =====
    installments_count = None
    installments_value = None
    inst_count_el = soup.select_one('.catalog-detail-price-installment [data-field="installments-count"]')
    inst_val_el = soup.select_one('.catalog-detail-price-installment [data-field="installments-value"]')
    if inst_count_el:
        # "5x" -> 5
        m = re.search(r'(\d+)', inst_count_el.get_text())
        if m:
            try:
                installments_count = int(m.group(1))
            except Exception:
                pass
    if inst_val_el:
        installments_value = brl_to_float(inst_val_el.get_text(" ", strip=True))

    # ===== JSON-LD como segunda fonte =====
    if not candidates:
        jsonld_prices, currency_ld, availability_ld = find_jsonld_prices(soup)
        if currency_ld:
            currency = currency_ld
        if availability_ld:
            availability = availability_ld
        for p in jsonld_prices:
            try:
                candidates.append((float(str(p).replace(',', '.')), "current"))
            except Exception:
                pass

    # ===== Fallback por regex no texto todo =====
    if not candidates:
        txt = soup.get_text(" ", strip=True)
        for m in re.finditer(r'R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}', txt):
            v = brl_to_float(m.group(0))
            if v is not None:
                candidates.append((v, "other"))

    # ===== Decisão do preço =====
    price_value, price_tag = choose_price(candidates, prefer=prefer_price)

    return {
        "url": url,
        "name": name,
        "brand": brand,
        "seller": seller,
        "price": price_value,                # float, ex.: 329.99
        "price_type": price_tag or "current",
        "original_price": price_original,    # float ou None
        "discount_percent": discount_percent,
        "installments_count": installments_count,
        "installments_value": installments_value,
        "currency": currency or "BRL",
        "availability": availability,        # ex.: https://schema.org/InStock
        "raw_candidates": candidates,        # para auditoria
    }
