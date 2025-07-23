import requests
from bs4 import BeautifulSoup


def buscar_promocoes_adidas():
    url = 'https://www.adidas.com.br/outlet'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    promocoes = []
    for produto in soup.select('.product-card'):
        nome = produto.select_one('.product-card__title')
        preco = produto.select_one('.product-card__price--sale')
        if nome and preco:
            promocoes.append({
                'nome': nome.text.strip(),
                'preco': preco.text.strip(),
            })
    return promocoes 