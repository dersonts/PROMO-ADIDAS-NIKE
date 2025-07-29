## Fase 1: Análise dos requisitos e estruturação do projeto

- [x] Ler e compreender os requisitos do projeto (feito)
- [x] Definir a estrutura de pastas do projeto
- [x] Listar as bibliotecas Python necessárias
- [x] Esboçar o modelo de dados para o SQLite
- [x] Planejar a arquitetura geral do bot (módulos, interações)




### Bibliotecas Python Necessárias:
- `requests`
- `BeautifulSoup`
- `selenium`
- `playwright`
- `python-telegram-bot`
- `SQLAlchemy`
- `Flask`
- `Flask-SQLAlchemy`

### Esboço do Modelo de Dados SQLite:
- **Produtos (Products)**:
  - `id` (PK, INTEGER)
  - `name` (TEXT)
  - `url` (TEXT, UNIQUE)
  - `image_url` (TEXT)
  - `original_price` (REAL)
  - `current_price` (REAL)
  - `last_updated` (DATETIME)

- **Histórico de Preços (PriceHistory)**:
  - `id` (PK, INTEGER)
  - `product_id` (FK, INTEGER)
  - `price` (REAL)
  - `timestamp` (DATETIME)

- **Alertas (Alerts)**:
  - `id` (PK, INTEGER)
  - `product_id` (FK, INTEGER)
  - `chat_id` (TEXT) - ID do chat do Telegram para o alerta
  - `threshold_price` (REAL) - Preço limite para o alerta
  - `alert_type` (TEXT) - Tipo de alerta (e.g., 'static', 'percentage', 'lowest_ever')
  - `active` (BOOLEAN)




### Arquitetura Geral do Bot:

- **`main.py`**: Ponto de entrada principal do aplicativo. Orquestra a execução dos módulos.
- **`src/scraper.py`**: Contém a lógica de web scraping para extrair dados de produtos dos sites. Utilizará `requests`, `BeautifulSoup`, `selenium` ou `playwright` conforme necessário.
- **`src/database.py`**: Gerencia a conexão com o banco de dados SQLite e define os modelos de dados usando `SQLAlchemy`.
- **`src/telegram_bot.py`**: Lida com a integração do Telegram, incluindo o envio de mensagens e o processamento de comandos.
- **`src/alert_manager.py`**: Contém a lógica para detectar quedas de preço e gerenciar os alertas, interagindo com o banco de dados e o módulo do Telegram.
- **`web/app.py`**: Aplicação Flask para a interface web, permitindo a visualização de produtos e preços históricos.
- **`config/settings.py`**: Armazena configurações como tokens de API do Telegram, caminhos do banco de dados, etc.
- **`logs/`**: Diretório para arquivos de log.
- **`data/`**: Diretório para o arquivo do banco de dados SQLite.



## Fase 2: Configuração do ambiente e estrutura base do projeto

- [x] Criar ambiente virtual Python
- [x] Criar arquivo requirements.txt
- [x] Instalar dependências
- [x] Criar arquivos base do projeto (main.py, config/settings.py, etc.)
- [x] Configurar estrutura inicial dos módulos


## Fase 3: Implementação do sistema de web scraping e monitoramento

- [x] Implementar classe base para scrapers
- [x] Criar scraper com requests/BeautifulSoup
- [x] Criar scraper com Playwright para conteúdo dinâmico
- [x] Implementar lógica específica para Nike e Adidas
- [x] Adicionar sistema de rotação de User-Agents
- [x] Implementar delays e throttling
- [x] Criar sistema de detecção e tratamento de erros


## Fase 4: Desenvolvimento do banco de dados e modelos de dados

- [x] Implementar modelos SQLAlchemy (Products, PriceHistory, Alerts)
- [x] Criar funções de inicialização do banco de dados
- [x] Implementar operações CRUD básicas
- [x] Adicionar funções para consultas específicas (histórico, alertas)
- [x] Criar sistema de migração/atualização do schema


## Fase 5: Criação da interface web com Flask

- [x] Implementar aplicação Flask principal
- [x] Criar templates HTML responsivos
- [x] Implementar páginas: dashboard, produtos, histórico, alertas
- [x] Adicionar formulários para adicionar produtos e alertas
- [x] Implementar gráficos de histórico de preços
- [x] Criar API endpoints para AJAX
- [x] Adicionar CSS e JavaScript para interatividade


## Fase 6: Implementação da integração com Telegram

- [x] Implementar classe TelegramBot com comandos básicos
- [x] Criar comandos: /start, /help, /add, /list, /alerts
- [x] Implementar envio de mensagens e imagens
- [x] Adicionar sistema de captura de chat_id
- [x] Implementar notificações de alertas via Telegram
- [x] Criar sistema de confirmação de comandos
- [x] Adicionar tratamento de erros e logging


## Fase 7: Sistema de alertas e notificações

- [x] Implementar AlertManager com lógica de detecção de quedas
- [x] Criar sistema de verificação de alertas (static, percentage, lowest_ever)
- [x] Implementar agendamento automático de verificações
- [x] Adicionar sistema de notificações (Telegram + web)
- [x] Criar sistema de throttling para evitar spam
- [x] Implementar logs detalhados de alertas
- [x] Adicionar sistema de retry para falhas


## Fase 8: Testes, documentação e finalização

- [x] Atualizar main.py para integrar todos os módulos
- [x] Criar scripts de teste para cada componente
- [x] Testar o sistema completo
- [x] Criar documentação completa (README.md)
- [x] Adicionar exemplos de uso
- [x] Criar guia de instalação e configuração
- [x] Documentar APIs e endpoints

