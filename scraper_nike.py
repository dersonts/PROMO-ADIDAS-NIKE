import requests
from bs4 import BeautifulSoup


def buscar_promocoes_nike():
    url = 'https://www.nike.com.br/Ofertas?ps=60'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    promocoes = []
    for produto in soup.select('.produto__info'):
        nome = produto.select_one('.produto__nome-produto')
        preco = produto.select_one('.produto__preco')
        if nome and preco:
            promocoes.append({
                'nome': nome.text.strip(),
                'preco': preco.text.strip(),
            })
    return promocoes 