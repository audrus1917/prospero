<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref } from "vue";

import { api } from "../api";
import type { CollectionResult, VacancyListItem } from "../types";
import EmptyState from "./EmptyState.vue";
import StatusMessage from "./StatusMessage.vue";
import VacancyCard from "./VacancyCard.vue";
import VacancyDetails from "./VacancyDetails.vue";

const PAGE_SIZE = 20;

const rows = ref<VacancyListItem[]>([]);
const offset = ref(0);
const loading = ref(false);
const hasMore = ref(false);
const listError = ref("");
const collecting = ref(false);
const collectStatus = ref("");
const collectError = ref(false);
const collectQuery = ref("Senior Python Developer");
const analyzeNew = ref(true);
const filters = reactive({ query: "", vacancyState: "all", remote: false });
const selectedRow = ref<VacancyListItem | null>(null);

function restoreFilters(): void {
  const params = new URLSearchParams(window.location.search);
  filters.query = params.get("query") ?? "";
  filters.vacancyState = params.get("vacancy_state") ?? "all";
  filters.remote = params.get("remote") === "true";
}

function saveFilters(): void {
  const url = new URL(window.location.href);
  const query = filters.query.trim();
  if (query) url.searchParams.set("query", query);
  else url.searchParams.delete("query");
  if (filters.vacancyState !== "all") url.searchParams.set("vacancy_state", filters.vacancyState);
  else url.searchParams.delete("vacancy_state");
  if (filters.remote) url.searchParams.set("remote", "true");
  else url.searchParams.delete("remote");
  window.history.replaceState({}, "", url);
}

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

async function loadVacancies(reset = false): Promise<void> {
  if (loading.value) return;
  if (reset) {
    offset.value = 0;
    rows.value = [];
    selectedRow.value = null;
  }
  loading.value = true;
  listError.value = "";
  try {
    const page = await api<VacancyListItem[]>(`/vacancies?${filtersQuery()}`);
    rows.value.push(...page);
    offset.value += page.length;
    hasMore.value = page.length === PAGE_SIZE;
  } catch (error) {
    listError.value = error instanceof Error ? error.message : "Не удалось загрузить вакансии";
    hasMore.value = false;
  } finally {
    loading.value = false;
  }
}

function applyFilters(): void {
  saveFilters();
  void loadVacancies(true);
}

function restoreFromHistory(): void {
  restoreFilters();
  void loadVacancies(true);
}

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
    collectStatus.value = `Получено: ${result.fetched}, новых: ${result.created}, оценено: ${result.analyzed}`;
    await loadVacancies(true);
  } catch (error) {
    collectError.value = true;
    collectStatus.value = error instanceof Error ? error.message : "Не удалось собрать вакансии";
  } finally {
    collecting.value = false;
  }
}

restoreFilters();
onMounted(() => {
  window.addEventListener("popstate", restoreFromHistory);
  void loadVacancies(true);
});
onBeforeUnmount(() => window.removeEventListener("popstate", restoreFromHistory));
</script>

<template>
  <section class="hero">
    <div>
      <p class="eyebrow">JOB SEARCH WORKSPACE</p>
      <h1>Найти работу,<br><em>которая подходит.</em></h1>
      <p class="hero-copy">
        Собирайте вакансии, сравнивайте их с профилем и ведите отклики
        в одном спокойном рабочем пространстве.
      </p>
    </div>
    <form class="collect-card" @submit.prevent="collect">
      <label for="collect-query">Новый поиск</label>
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

  <section class="workspace">
    <div class="section-heading">
      <div>
        <p class="eyebrow">DISCOVERY</p>
        <h2>Вакансии</h2>
      </div>
      <span class="count-badge">{{ rows.length }}</span>
    </div>

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

    <div v-if="listError" class="error-panel">{{ listError }}</div>
    <div v-else-if="loading && !rows.length" class="loading-panel">Загружаем вакансии…</div>
    <div v-else-if="rows.length" class="card-grid">
      <VacancyCard
        v-for="row in rows"
        :key="row.vacancy.id"
        :row="row"
        @changed="loadVacancies(true)"
        @open="selectedRow = row"
      />
    </div>
    <EmptyState
      v-else
      title="Здесь пока пусто"
      description="Запустите сбор вакансий или измените фильтры."
    />
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

  <VacancyDetails v-if="selectedRow" :row="selectedRow" @close="selectedRow = null" />
</template>
