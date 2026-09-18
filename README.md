# Prospero

Минимальный агент для поиска и оценки вакансий. Он собирает вакансии из HeadHunter,
нормализует и дедуплицирует их, отбрасывает очевидно неподходящие варианты до
семантического анализа и показывает рекомендации с детерминированным итоговым баллом.

## Быстрый запуск

```bash
cp .env.example .env
cp config/candidate_profile.example.yaml config/candidate_profile.yaml
mkdir -p data/resumes data/vacancies
docker compose up --build
```

API будет доступен на `http://localhost:9080`, Swagger UI — на
`http://localhost:9080/docs`. Рабочий web-интерфейс открывается на
`http://localhost:9080/`.

Локальный профиль кандидата хранится в `config/candidate_profile.yaml` и не отслеживается
Git. Перед первым сбором скопируйте публичный пример и заполните его своими ролями,
навыками и ограничениями.
Также укажите реальный контакт разработчика в `HH_USER_AGENT`: API HeadHunter требует
формат наподобие `ProsperoJobAgent/0.1 (you@example.com)` и отклоняет шаблонные адреса.
Для стабильного сбора создайте приложение в кабинете разработчика HH, получите токен
приложения через OAuth `client_credentials` и сохраните его в `HH_ACCESS_TOKEN`.

## Основной сценарий

```bash
curl -X POST http://localhost:8000/vacancies/collect \
  -H 'Content-Type: application/json' \
  -d '{"query":"Senior Python Developer","per_page":20,"analyze":true}'

curl -X POST http://localhost:8000/vacancies/1/analyze

curl 'http://localhost:8000/vacancies/recommended?limit=20&offset=0'

curl -X POST http://localhost:8000/applications \
  -H 'Content-Type: application/json' \
  -d '{"vacancy_id":1,"status":"shortlisted","notes":"Review CV keywords"}'

curl -X PATCH http://localhost:8000/applications/1 \
  -H 'Content-Type: application/json' \
  -d '{"status":"applied"}'
```

Встроенный `heuristic`-провайдер делает MVP работоспособным без ключа внешнего LLM.
Контракт `LLMProvider` изолирует анализ от конкретного SDK; следующий провайдер должен
возвращать тот же валидируемый `MatchResult`. Текст вакансии всегда считается
недоверенными данными, а профиль кандидата — единственным источником фактов о кандидате.

Для анализа через OpenAI-compatible Responses API задайте в `.env`:

```dotenv
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=<модель с поддержкой structured output>
OPENAI_API_KEY=<ключ>
```

Для медленных моделей можно увеличить `LLM_TIMEOUT` (по умолчанию 60 секунд); он
настраивается отдельно от таймаута запросов к HH.

Модель выбирается явно: приложение не подставляет её молча и не выполняет платные
вызовы, пока `LLM_PROVIDER` остаётся равным `heuristic`.

## Анализ PDF

Для сравнения конкретного резюме с сохранёнными вакансиями положите текстовые
PDF-файлы в каталоги:

```text
data/
├── resumes/     # варианты резюме
└── vacancies/   # вакансии для сравнения
```

Каталог `data/` содержит только локальные пользовательские данные и целиком исключён
из Git. Создайте его перед первым запуском, как показано в разделе быстрого запуска.

Откройте вкладку «PDF-анализ», выберите одно резюме и нужные вакансии. За один запрос
обрабатывается не более 20 вакансий. Итоговый балл рассчитывается приложением, а
провайдер возвращает сильные стороны, пробелы, отсутствующие ключевые слова и
рекомендации по формулировкам. Рекомендации не должны добавлять несуществующий опыт.

PDF должен содержать текстовый слой. Для сканов без текста сначала требуется OCR.
При `LLM_PROVIDER=openai` извлечённый текст выбранных документов отправляется указанному
LLM-провайдеру; режим `heuristic` выполняется локально.

## Локальная разработка

Нужны Python 3.12+, Node.js 22+, `uv` и npm:

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn job_agent.main:app --reload
```

Frontend реализован на Vue 3 и TypeScript. Для разработки с hot reload запустите
его отдельно; Vite проксирует API-запросы на FastAPI по адресу `127.0.0.1:8000`:

```bash
cd frontend
npm install
npm run dev
```

Production-сборка автоматически попадает в `src/job_agent/static` и раздаётся FastAPI:

```bash
cd frontend
npm run build
```

Для тестов можно использовать SQLite; рабочая конфигурация в Compose использует
PostgreSQL и применяет Alembic-миграции до запуска API.

```bash
uv run pytest
uv run ruff check src tests
uv run mypy src
cd frontend && npm run typecheck && npm test
```

## API

- `GET /health` — состояние процесса;
- `GET /vacancies` — вакансии с фильтрами и связанными анализом/откликом;
- `POST /vacancies/collect` — сбор и сохранение страницы HH;
- `GET /vacancies/{id}` — нормализованная вакансия;
- `POST /vacancies/{id}/analyze` — фильтрация, анализ и scoring;
- `GET /vacancies/recommended` — рекомендации с `limit/offset`;
- `GET /applications` — список отслеживаемых откликов;
- `POST /applications` — добавить вакансию в воронку;
- `PATCH /applications/{id}` — изменить статус или заметки;
- `GET /documents/resumes` — доступные PDF-резюме;
- `GET /documents/vacancies` — доступные PDF-вакансии;
- `POST /documents/analyze` — сравнить выбранное резюме с PDF-вакансиями.
- `POST /documents/process` — индексировать, извлечь текст и классифицировать PDF;
- `GET /documents/catalog/{kind}` — статусы, checksum и категории документов.

## Описание логики

Подробная схема потоков данных и PDF-обработки находится
в [docs/PROSPERO_LOGIC.md](docs/PROSPERO_LOGIC.md).
