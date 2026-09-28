<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref } from "vue";

import { api } from "../api";
import type { CollectionResult, VacancyListItem } from "../types";
import EmptyState from "./EmptyState.vue";
import StatusMessage from "./StatusMessage.vue";
import VacancyCard from "./VacancyCard.vue";
import VacancyDetails from "./VacancyDetails.vue";

// API page size also controls when the UI decides that another page may exist.
const PAGE_SIZE = 20;

// Paginated composite rows currently rendered in the vacancy grid.
const rows = ref<VacancyListItem[]>([]);
// Offset points to the first row of the next page.
const offset = ref(0);
// List loading is separate from collection so both workflows expose accurate UI state.
const loading = ref(false);
const hasMore = ref(false);
const listError = ref("");
// Collection state belongs to the hero search form.
const collecting = ref(false);
const collectStatus = ref("");
const collectError = ref(false);
const collectQuery = ref("Senior Python Developer");
const analyzeNew = ref(true);
// A reactive object keeps related filters grouped and template bindings concise.
const filters = reactive({ query: "", vacancyState: "all", remote: false });
// A non-null row opens the details drawer for that specific list snapshot.
const selectedRow = ref<VacancyListItem | null>(null);

/** Restore shareable vacancy filters from the current URL. */
function restoreFilters(): void {
  const params = new URLSearchParams(window.location.search);
  filters.query = params.get("query") ?? "";
  filters.vacancyState = params.get("vacancy_state") ?? "all";
  filters.remote = params.get("remote") === "true";
}

/** Persist non-default filters without adding a history entry on every search. */
function saveFilters(): void {
  const url = new URL(window.location.href);
  const query = filters.query.trim();
  // Omit defaults so generated links remain short and readable.
  if (query) url.searchParams.set("query", query);
  else url.searchParams.delete("query");
  if (filters.vacancyState !== "all") url.searchParams.set("vacancy_state", filters.vacancyState);
  else url.searchParams.delete("vacancy_state");
  if (filters.remote) url.searchParams.set("remote", "true");
  else url.searchParams.delete("remote");
  window.history.replaceState({}, "", url);
}

/** Convert local filter and pagination state into backend query parameters. */
function filtersQuery(): URLSearchParams {
  const params = new URLSearchParams({
    vacancy_state: filters.vacancyState,
    limit: String(PAGE_SIZE),
    offset: String(offset.value),
  });
  if (filters.query.trim()) params.set("query", filters.query.trim());
  if (filters.remote) params.set("remote", "true");
  return params;
}

/** Load the next vacancy page, or replace the list when `reset` is true. */
async function loadVacancies(reset = false): Promise<void> {
  // Prevent overlapping calls from appending the same offset twice.
  if (loading.value) return;
  if (reset) {
    // A changed query invalidates pagination and any currently open row.
    offset.value = 0;
    rows.value = [];
    selectedRow.value = null;
  }
  loading.value = true;
  listError.value = "";
  try {
    const page = await api<VacancyListItem[]>(`/vacancies?${filtersQuery()}`);
    // The same operation handles both an empty reset list and later pages.
    rows.value.push(...page);
    offset.value += page.length;
    // A full page may have a successor; a short page is necessarily terminal.
    hasMore.value = page.length === PAGE_SIZE;
  } catch (error) {
    listError.value = error instanceof Error ? error.message : "Не удалось загрузить вакансии";
    hasMore.value = false;
  } finally {
    loading.value = false;
  }
}

/** Apply the form state to both the URL and the visible result set. */
function applyFilters(): void {
  saveFilters();
  void loadVacancies(true);
}

/** Rebuild the list when browser history changes the query string. */
function restoreFromHistory(): void {
  restoreFilters();
  void loadVacancies(true);
}

/** Ask the backend collector for a new HH page and optionally analyze it. */
async function collect(): Promise<void> {
  collecting.value = true;
  collectError.value = false;
  collectStatus.value = "Получаем вакансии с HeadHunter…";
  try {
    const result = await api<CollectionResult>("/vacancies/collect", {
      method: "POST",
      body: JSON.stringify({
        query: collectQuery.value.trim(),
        per_page: PAGE_SIZE,
        analyze: analyzeNew.value,
      }),
    });
    // Report the most useful counters while leaving detailed failures to the API.
    collectStatus.value = `Получено: ${result.fetched}, новых: ${result.created}, оценено: ${result.analyzed}`;
    // Newly persisted vacancies must be reflected from the first list page.
    await loadVacancies(true);
  } catch (error) {
    collectError.value = true;
    collectStatus.value = error instanceof Error ? error.message : "Не удалось собрать вакансии";
  } finally {
    collecting.value = false;
  }
}

// Read query parameters before the first render to avoid initially displaying
// controls that disagree with the URL.
restoreFilters();
onMounted(() => {
  window.addEventListener("popstate", restoreFromHistory);
  void loadVacancies(true);
});
onBeforeUnmount(() => window.removeEventListener("popstate", restoreFromHistory));
</script>

<template>
  <section class="collect-card" aria-label="Сбор вакансий">
    <div>
      <h1>Сбор вакансий</h1>
      <p>Найдите новые вакансии на HeadHunter и оцените их соответствие профилю.</p>
    </div>
    <form @submit.prevent="collect">
      <label for="collect-query">Поисковый запрос</label>
      <div class="collect-row">
        <input id="collect-query" v-model="collectQuery" maxlength="200" required>
        <button class="primary-button" type="submit" :disabled="collecting">
          {{ collecting ? "Собираем…" : "Собрать" }}
        </button>
      </div>
      <label class="check-row">
        <input v-model="analyzeNew" type="checkbox">
        <span>Сразу анализировать новые вакансии</span>
      </label>
      <StatusMessage :message="collectStatus" :error="collectError" />
    </form>
  </section>

  <!-- Search filters and the paginated vacancy result grid. -->
  <section class="workspace">
    <div class="section-heading">
      <div>
        <h2>Вакансии</h2>
      </div>
      <span class="count-badge">{{ rows.length }}</span>
    </div>

    <!-- Submission makes applying several filter edits one explicit action. -->
    <form class="filters" @submit.prevent="applyFilters">
      <label class="search-field">
        <span class="visually-hidden">Поиск</span>
        <input v-model="filters.query" type="search" placeholder="Название или компания">
      </label>
      <select v-model="filters.vacancyState" aria-label="Состояние вакансии">
        <option value="all">Все состояния</option>
        <option value="recommended">Рекомендованные</option>
        <option value="other">Остальные оценки</option>
        <option value="unanalyzed">Без анализа</option>
        <option value="filtered">Отфильтрованные</option>
      </select>
      <label class="check-row compact">
        <input v-model="filters.remote" type="checkbox">
        <span>Только remote</span>
      </label>
      <button class="secondary-button" type="submit">Применить</button>
    </form>

    <!-- Render mutually exclusive request, loading, result, and empty states. -->
    <div v-if="listError" class="error-panel">{{ listError }}</div>
    <div v-else-if="loading && !rows.length" class="loading-panel">Загружаем вакансии…</div>
    <template v-else-if="rows.length">
      <div class="vacancy-list-header" aria-hidden="true">
        <span>Вакансия</span><span>Оценка</span><span>Подробности</span><span>Действия</span>
      </div>
      <div class="card-grid">
        <VacancyCard
          v-for="row in rows"
          :key="row.vacancy.id"
          :row="row"
          @changed="loadVacancies(true)"
          @open="selectedRow = row"
        />
      </div>
    </template>
    <EmptyState
      v-else
      title="Здесь пока пусто"
      description="Запустите сбор вакансий или измените фильтры."
    />
    <!-- Pagination appends data without replacing rows already inspected. -->
    <button
      v-if="hasMore"
      class="load-more"
      type="button"
      :disabled="loading"
      @click="loadVacancies()"
    >
      {{ loading ? "Загружаем…" : "Показать ещё" }}
    </button>
  </section>

  <!-- Mount the accessible drawer only while a row is selected. -->
  <VacancyDetails v-if="selectedRow" :row="selectedRow" @close="selectedRow = null" />
</template>
