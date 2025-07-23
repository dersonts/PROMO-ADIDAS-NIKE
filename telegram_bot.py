from telegram import Bot

TELEGRAM_TOKEN = 'COLE_SEU_TOKEN_AQUI'
CHAT_ID = 'COLE_SEU_CHAT_ID_AQUI'

bot = Bot(token=TELEGRAM_TOKEN)

def enviar_alerta(mensagem):
    bot.send_message(chat_id=CHAT_ID, text=mensagem) 