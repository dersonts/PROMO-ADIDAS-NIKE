# src/scrapers/netshoes.py
from bs4 import BeautifulSoup
from .utils import brl_to_float, find_jsonld_prices, choose_price, extract_all_brl
import re

PIX_TOKEN_RE   = re.compile(r'\bno\s*pix\b', re.IGNORECASE)
CARD_TOKEN_RE  = re.compile(r'\bou\s*R\$\s*\d', re.IGNORECASE)  # linha do "ou R$ ... em até ..."
PARCEL_RE      = re.compile(r'\bem\s+at[eé]\b', re.IGNORECASE)

def parse_netshoes(html: str, url: str, prefer_price: str = "lowest") -> dict:
    soup = BeautifulSoup(html, 'lxml')

    # 1) Nome
    name = None
    h1 = soup.select_one('h1.product-name')
    if h1:
        name = h1.get_text(strip=True)
    if not name:
        # fallback em meta tags
        mt = soup.find('meta', property='og:title')
        if mt and mt.get('content'):
            name = mt['content']

    # 2) JSON-LD primeiro (quando existe)
    candidates = []
    jsonld_prices, currency, availability = find_jsonld_prices(soup)
    for p in jsonld_prices:
        candidates.append( (float(p), "current") )

    # 3) Fallback por texto + heurística
    #    Pegamos o bloco "buy box" (quando existir), senão varremos a página inteira
    container = None
    # Muitas PDPs usam blocos como ".buy-box", ".price-info" etc — mantenho alguns fallbacks
    for sel in ['.buy-box', '.product-price', '.price', '.showcase__description', 'body']:
        container = soup.select_one(sel)
        if container:
            break

    if container:
        txt = container.get_text(" ", strip=True)
    else:
        txt = soup.get_text(" ", strip=True)

    # Exemplo do seu log:
    # "R$ 599,99R$ 512,99 no Pix ou R$ 539,99 em até 7x"
    # Vamos identificar marcadores por trechos:
    # - Perto de "no Pix" → pix
    # - Perto de "ou R$ ... em até" → card
    # Se não der, todos vão como "other"
    # Dica: mapeamos o offset do match pra decidir a que trecho pertence
    spans = [(m.start(), m.end(), brl_to_float(m.group(0))) for m in re.finditer(r'R\$\s*\d{1,3}(\.\d{3})*,\d{2}', txt)]
    for start, end, val in spans:
        tag = "other"
        # janela de contexto à direita/esquerda
        left = txt[max(0, start-25):start]
        right = txt[end:min(len(txt), end+40)]

        if PIX_TOKEN_RE.search(right) or PIX_TOKEN_RE.search(left):
            tag = "pix"
        elif CARD_TOKEN_RE.search(left) or PARCEL_RE.search(right):
            tag = "card"

        if val is not None:
            candidates.append( (val, tag) )

    # 4) Decisão de preço
    price_value, price_tag = choose_price(candidates, prefer=prefer_price)

    return {
        "url": url,
        "name": name,
        "price": price_value,       # float (ex.: 512.99)
        "price_type": price_tag,    # "pix" | "card" | "current" | "other"
        "currency": "BRL",
        "availability": availability,
        "raw_candidates": candidates,  # útil para depuração
    }
