# 🤖 Bot de Monitoramento de Preços

Um sistema completo e automatizado para monitorar preços de produtos em sites de e-commerce, com alertas inteligentes via Telegram e interface web moderna.

## 📋 Índice

- [Características](#-características)
- [Arquitetura](#-arquitetura)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [API](#-api)
- [Desenvolvimento](#-desenvolvimento)
- [Troubleshooting](#-troubleshooting)
- [Contribuição](#-contribuição)

## ✨ Características

### 🕷️ Web Scraping Inteligente
- **Scraping Estático**: Para sites simples usando `requests` e `BeautifulSoup`
- **Scraping Dinâmico**: Para sites complexos com JavaScript usando `Playwright`
- **Sites Suportados**: Nike, Adidas e sites genéricos de e-commerce
- **Anti-Bot**: Rotação de User-Agents, delays aleatórios e headers realistas

### 🔔 Sistema de Alertas Avançado
- **Preço Fixo**: Alerta quando o preço fica abaixo de um valor específico
- **Queda Percentual**: Alerta quando há uma queda percentual no preço
- **Mínimo Histórico**: Alerta quando o produto atinge o menor preço já registrado
- **Throttling**: Evita spam de notificações

### 💬 Integração com Telegram
- **Bot Interativo**: Comandos completos para gerenciar produtos e alertas
- **Notificações**: Alertas automáticos com informações detalhadas
- **Interface Amigável**: Botões inline e mensagens formatadas

### 🌐 Interface Web Moderna
- **Dashboard**: Visão geral com estatísticas e produtos recentes
- **Gerenciamento**: Adicionar produtos, criar alertas e visualizar histórico
- **Gráficos**: Histórico de preços com Chart.js
- **Responsiva**: Funciona perfeitamente em desktop e mobile

### 🗄️ Banco de Dados Robusto
- **SQLite**: Banco leve e eficiente
- **Histórico Completo**: Todos os preços são registrados para análise
- **Relacionamentos**: Produtos, histórico de preços e alertas interconectados

## 🏗️ Arquitetura

```
price_monitor_bot/
├── main.py                 # Ponto de entrada principal
├── requirements.txt        # Dependências Python
├── .env.example           # Exemplo de configuração
├── test_system.py         # Script de testes
├── config/
│   └── settings.py        # Configurações do sistema
├── src/
│   ├── database.py        # Modelos e operações do banco
│   ├── scraper.py         # Sistema de web scraping
│   ├── telegram_bot.py    # Integração com Telegram
│   └── alert_manager.py   # Gerenciamento de alertas
├── web/
│   ├── app.py            # Aplicação Flask
│   └── templates/        # Templates HTML
├── data/                 # Banco de dados SQLite
└── logs/                # Arquivos de log
```

### Fluxo de Funcionamento

1. **Adição de Produtos**: Via interface web ou Telegram
2. **Scraping Automático**: Verificação periódica de preços (30 min)
3. **Detecção de Mudanças**: Comparação com preços anteriores
4. **Verificação de Alertas**: Análise de condições configuradas
5. **Notificações**: Envio via Telegram e/ou interface web
6. **Registro Histórico**: Armazenamento de todas as mudanças

## 🚀 Instalação

### Pré-requisitos

- Python 3.11+
- Git
- Navegador Chrome/Chromium (para Playwright)

### Passo a Passo

1. **Clone o repositório**:
```bash
git clone <url-do-repositorio>
cd price_monitor_bot
```

2. **Crie um ambiente virtual**:
```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. **Instale as dependências**:
```bash
pip install -r requirements.txt
playwright install
```

4. **Configure as variáveis de ambiente**:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

5. **Execute os testes**:
```bash
python test_system.py
```

6. **Inicie o sistema**:
```bash
python main.py
```

## ⚙️ Configuração

### Arquivo .env

Crie um arquivo `.env` na raiz do projeto com as seguintes configurações:

```env
# Token do Bot do Telegram (obrigatório para alertas)
TELEGRAM_BOT_TOKEN=seu_token_aqui

# Configurações do banco de dados (opcional)
DATABASE_URL=sqlite:///data/price_monitor.db

# Configurações da aplicação Flask
FLASK_PORT=5000
FLASK_DEBUG=False

# Configurações de logging
LOG_LEVEL=INFO
```

### Obter Token do Telegram

1. Abra o Telegram e procure por `@BotFather`
2. Envie `/newbot` e siga as instruções
3. Copie o token fornecido para o arquivo `.env`
4. Para obter seu chat ID:
   - Procure por `@userinfobot`
   - Envie qualquer mensagem
   - Use o ID retornado nos alertas

### Configurações Avançadas

Edite `config/settings.py` para personalizar:

- **User-Agents**: Lista de navegadores para rotação
- **Delays**: Tempo entre requisições (min/max)
- **Tipos de Alerta**: Configurações de alertas disponíveis
- **Logging**: Nível de detalhamento dos logs

## 📖 Uso

### Interface Web

Acesse `http://localhost:5000` para:

1. **Dashboard**: Visualizar estatísticas e produtos recentes
2. **Adicionar Produtos**: Cole a URL do produto desejado
3. **Gerenciar Alertas**: Configure alertas personalizados
4. **Histórico**: Visualize gráficos de preços
5. **Testar Scraper**: Teste URLs antes de adicionar

### Comandos do Telegram

#### Comandos Básicos
- `/start` - Iniciar o bot
- `/help` - Mostrar ajuda completa
- `/add <url>` - Adicionar produto
- `/list` - Listar produtos monitorados
- `/alerts` - Gerenciar alertas
- `/stats` - Ver estatísticas
- `/update <id>` - Atualizar produto específico

#### Exemplos de Uso

**Adicionar produto**:
```
/add https://www.nike.com.br/produto/tenis-nike-air-max
```

**Ou simplesmente cole a URL**:
```
https://www.adidas.com.br/tenis-ultraboost
```

### Tipos de Alertas

#### 1. Preço Fixo
Alerta quando o preço fica abaixo de um valor específico.
```
Exemplo: Alertar quando o produto custar menos de R$ 200,00
```

#### 2. Queda Percentual
Alerta quando há uma queda percentual no preço.
```
Exemplo: Alertar quando o preço cair 15% ou mais
```

#### 3. Mínimo Histórico
Alerta quando o produto atinge o menor preço já registrado.
```
Exemplo: Alertar quando for o menor preço de todos os tempos
```

## 🔌 API

### Endpoints Principais

#### GET /api/products
Lista todos os produtos monitorados.

**Resposta**:
```json
[
  {
    "id": 1,
    "name": "Tênis Nike Air Max",
    "url": "https://...",
    "current_price": 299.99,
    "original_price": 399.99,
    "last_updated": "2024-01-15T10:30:00",
    "active": true
  }
]
```

#### GET /api/product/{id}/history
Retorna o histórico de preços de um produto.

**Parâmetros**:
- `limit` (opcional): Número máximo de registros (padrão: 50)

**Resposta**:
```json
[
  {
    "id": 1,
    "product_id": 1,
    "price": 299.99,
    "timestamp": "2024-01-15T10:30:00"
  }
]
```

#### POST /api/product/{id}/update
Força a atualização do preço de um produto.

**Resposta**:
```json
{
  "success": true,
  "old_price": 299.99,
  "new_price": 279.99,
  "message": "Produto atualizado com sucesso"
}
```

#### POST /api/add_alert
Adiciona um novo alerta.

**Corpo da requisição**:
```json
{
  "product_id": 1,
  "alert_type": "static",
  "threshold_price": 250.00,
  "chat_id": "123456789"
}
```

#### GET /api/stats
Retorna estatísticas do sistema.

**Resposta**:
```json
{
  "total_products": 25,
  "active_products": 23,
  "total_alerts": 15,
  "active_alerts": 12,
  "total_price_records": 1250
}
```

## 🛠️ Desenvolvimento

### Estrutura do Código

#### src/database.py
- **Modelos**: Product, PriceHistory, Alert
- **DatabaseManager**: Operações CRUD e consultas
- **Funções**: Inicialização e estatísticas

#### src/scraper.py
- **BaseScraper**: Classe abstrata base
- **StaticScraper**: Para sites estáticos
- **DynamicScraper**: Para sites com JavaScript
- **ScraperManager**: Gerencia qual scraper usar

#### src/telegram_bot.py
- **TelegramBot**: Classe principal do bot
- **Comandos**: Handlers para todos os comandos
- **Callbacks**: Processamento de botões inline

#### src/alert_manager.py
- **AlertManager**: Gerencia verificações e alertas
- **Scheduling**: Agendamento automático
- **Notifications**: Envio de notificações

### Executar Testes

```bash
# Testa todo o sistema
python test_system.py

# Testa apenas o scraper
python -c "from src.scraper import ScraperManager; s = ScraperManager(); print(s.test_scraper('URL_AQUI'))"

# Testa banco de dados
python -c "from src.database import DatabaseManager; print(DatabaseManager.get_database_stats())"
```

### Adicionar Novo Site

1. **Identifique os seletores CSS** do site
2. **Edite src/scraper.py**:
   - Adicione o domínio em `dynamic_sites` se necessário
   - Crie método específico `_scrape_SITE_static/dynamic`
3. **Teste** com `test_scraper.py`

### Logs e Debug

Os logs são salvos em `logs/price_monitor.log` com as seguintes informações:
- Tentativas de scraping
- Alertas disparados
- Erros e exceções
- Estatísticas de performance

Para debug detalhado, altere `LOG_LEVEL=DEBUG` no `.env`.

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Erro "Token do Telegram inválido"
**Solução**: Verifique se o token no `.env` está correto e se o bot foi criado corretamente no BotFather.

#### 2. Scraping falha constantemente
**Possíveis causas**:
- Site mudou estrutura HTML
- Proteções anti-bot mais rigorosas
- Problemas de conectividade

**Soluções**:
- Teste com `python test_system.py`
- Verifique logs em `logs/price_monitor.log`
- Atualize seletores CSS no código

#### 3. Alertas não são enviados
**Verificações**:
- Bot do Telegram está ativo?
- Chat ID está correto?
- Condições do alerta estão sendo atendidas?

#### 4. Interface web não carrega
**Soluções**:
- Verifique se a porta 5000 está livre
- Confirme que todas as dependências foram instaladas
- Execute `python test_system.py` para diagnóstico

#### 5. Banco de dados corrompido
**Solução**:
```bash
# Backup do banco atual
cp data/price_monitor.db data/price_monitor.db.backup

# Reinicializar banco
rm data/price_monitor.db
python main.py
```

### Logs Úteis

```bash
# Ver logs em tempo real
tail -f logs/price_monitor.log

# Filtrar apenas erros
grep ERROR logs/price_monitor.log

# Ver alertas disparados
grep "ALERTA DISPARADO" logs/price_monitor.log
```

## 🤝 Contribuição

### Como Contribuir

1. **Fork** o repositório
2. **Crie** uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. **Commit** suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. **Push** para a branch (`git push origin feature/nova-funcionalidade`)
5. **Abra** um Pull Request

### Padrões de Código

- **PEP 8**: Siga as convenções Python
- **Docstrings**: Documente funções e classes
- **Type Hints**: Use anotações de tipo quando possível
- **Logging**: Use o sistema de logging para debug
- **Testes**: Adicione testes para novas funcionalidades

### Roadmap

#### Próximas Funcionalidades
- [ ] Suporte a mais sites de e-commerce
- [ ] Dashboard com métricas avançadas
- [ ] Exportação de dados (CSV, JSON)
- [ ] Integração com Discord
- [ ] API REST completa
- [ ] Sistema de usuários e autenticação
- [ ] Alertas por email
- [ ] Análise de tendências de preços

#### Melhorias Técnicas
- [ ] Containerização com Docker
- [ ] Deploy automatizado
- [ ] Testes unitários abrangentes
- [ ] Monitoramento e métricas
- [ ] Cache de resultados
- [ ] Rate limiting inteligente

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- **BeautifulSoup** e **Playwright** pelo web scraping
- **python-telegram-bot** pela integração com Telegram
- **Flask** pela interface web
- **SQLAlchemy** pelo ORM
- **Chart.js** pelos gráficos interativos

## 📞 Suporte

Para suporte e dúvidas:
- 📧 Email: suporte@pricebot.com
- 💬 Telegram: @PriceBotSupport
- 🐛 Issues: [GitHub Issues](https://github.com/seu-usuario/price-monitor-bot/issues)

---

**Desenvolvido com ❤️ para economizar seu dinheiro!**

