from scraper_nike import buscar_promocoes_nike
from scraper_adidas import buscar_promocoes_adidas
from telegram_bot import enviar_alerta
import schedule
import time


def checar_promocoes():
    nike = buscar_promocoes_nike()
    adidas = buscar_promocoes_adidas()
    mensagem = ''
    if nike:
        print('Promoções Nike:')
        for p in nike:
            print(f"{p['nome']} - {p['preco']}")
        mensagem += 'Promoções Nike:\n'
        for p in nike:
            mensagem += f"{p['nome']} - {p['preco']}\n"
    if adidas:
        print('\nPromoções Adidas:')
        for p in adidas:
            print(f"{p['nome']} - {p['preco']}")
        mensagem += '\nPromoções Adidas:\n'
        for p in adidas:
            mensagem += f"{p['nome']} - {p['preco']}\n"
    if mensagem:
        enviar_alerta(mensagem)


schedule.every(60).minutes.do(checar_promocoes)

if __name__ == '__main__':
    checar_promocoes()
    while True:
        schedule.run_pending()
        time.sleep(1) 