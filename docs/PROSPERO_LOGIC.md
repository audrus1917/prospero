# Prospero: логика работы

## Основной поток

```text
HH search API -> HHCollector -> нормализация -> PostgreSQL vacancy
                                      |
                         rule-based filtering
                                      |
                              LLM analysis
                                      |
                         deterministic final score
```

`POST /vacancies/collect` получает страницу HH, удаляет дубликаты по `(source, external_id)`,
отбрасывает явно неподходящие вакансии и при необходимости запускает анализ.

## PDF-поток

PDF кладутся в `data/resumes` и `data/vacancies`. `POST /documents/process`:

1. вычисляет SHA-256 и синхронизирует каталог;
2. извлекает текст через `pypdf`;
3. классифицирует документ по `config/categories.json`;
4. сохраняет текст, категории, версию parser/classifier и статус.

Ошибки изолируются на уровне файла. Для сканированных документов выставляется `needs_ocr`.
Повторный запуск не обрабатывает неизменившиеся документы.

## Запуск

```bash
cp .env.example .env
docker compose up -d --build
```
