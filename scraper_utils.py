# src/scrapers/utils.py
import json
import re
from bs4 import BeautifulSoup

BRL_RE = re.compile(r'R\$\s*\d{1,3}(\.\d{3})*,\d{2}', re.IGNORECASE)

def brl_to_float(txt: str) -> float:
    """Converte 'R$ 1.234,56' -> 1234.56"""
    t = txt.strip()
    t = re.sub(r'[^\d,\.]', '', t)        # remove R$, espaços etc
    t = t.replace('.', '').replace(',', '.')  # remove milhar, troca vírgula por ponto
    try:
        return float(t)
    except ValueError:
        return None

def find_jsonld_prices(soup: BeautifulSoup):
    """Procura Product/Offer em JSON-LD."""
    prices = []
    currency = None
    availability = None
    for tag in soup.select('script[type="application/ld+json"]'):
        txt = (tag.string or tag.text or '').strip()
        if not txt:
            continue
        # Algumas páginas têm múltiplos JSONs concatenados
        # Tente carregar item a item
        try:
            data = json.loads(txt)
        except json.JSONDecodeError:
            # Tente "corrigir" listas de JSONs simples
            try:
                data = json.loads(f'[{txt}]')
            except Exception:
                continue

        def visit(node):
            nonlocal currency, availability
            if isinstance(node, dict):
                if node.get('@type', '').lower() == 'product' or node.get('@type') == ['Product']:
                    offers = node.get('offers')
                    if isinstance(offers, dict):
                        price = offers.get('price') or offers.get('lowPrice') or offers.get('highPrice')
                        if price:
                            prices.append(float(str(price).replace(',', '.')))
                        currency = currency or offers.get('priceCurrency')
                        availability = availability or (offers.get('availability') or offers.get('Availability'))
                    elif isinstance(offers, list):
                        for o in offers:
                            p = o.get('price') or o.get('lowPrice') or o.get('highPrice')
                            if p:
                                prices.append(float(str(p).replace(',', '.')))
                            currency = currency or o.get('priceCurrency')
                            availability = availability or (o.get('availability') or o.get('Availability'))
                for v in node.values():
                    visit(v)
            elif isinstance(node, list):
                for v in node:
                    visit(v)
        visit(data)
    return prices, currency, availability

def choose_price(candidates: list[tuple[float,str]], prefer: str = "lowest") -> tuple[float,str] | tuple[None,None]:
    """
    candidates: lista de (valor, tag) onde tag ∈ {"pix","card","current","other"}
    prefer: "pix" | "card" | "lowest" | "current"
    """
    if not candidates:
        return (None, None)
    prefer = (prefer or "lowest").lower()
    if prefer in {"pix","card","current"}:
        filtered = [c for c in candidates if c[1] == prefer]
        if filtered:
            # se houver múltiplos, pega o menor por segurança
            return sorted(filtered, key=lambda x: x[0])[0]
    # fallback para menor preço geral
    return sorted(candidates, key=lambda x: x[0])[0]

def extract_all_brl(text: str):
    """Extrai todos os valores R$ ... do texto."""
    vals = []
    for m in BRL_RE.finditer(text):
        v = brl_to_float(m.group(0))
        if v is not None:
            vals.append( (v, m.group(0)) )
    return vals
