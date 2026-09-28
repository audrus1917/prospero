<script setup lang="ts">
import { computed, ref } from "vue";

import { api } from "../api";
import type { Application, VacancyAnalysis, VacancyListItem } from "../types";

// The parent owns the canonical row list. This card requests refreshes after
// mutations and asks the parent to open details instead of duplicating state.
const props = defineProps<{ row: VacancyListItem }>();
const emit = defineEmits<{ changed: []; open: [] }>();

// Keep analysis and tracking states independent because they invoke different endpoints.
const analyzing = ref(false);
const tracking = ref(false);
const actionError = ref("");

// Exhaustive status mapping makes every backend workflow state user-readable.
const applicationLabels: Record<Application["status"], string> = {
  new: "Новый",
  shortlisted: "В шорт-листе",
  applied: "Отклик отправлен",
  hr: "Интервью с HR",
  technical: "Техническое интервью",
  final: "Финальный этап",
  offer: "Оффер",
  rejected: "Отказ",
  withdrawn: "Снят",
};

/** Format the optional salary range for the Russian UI locale. */
const salary = computed(() => {
  const vacancy = props.row.vacancy;
  const currency = vacancy.salary_currency ?? "";
  // Salary values arrive as strings to preserve database decimal precision.
  const format = (value: string) => Number(value).toLocaleString("ru-RU");
  if (vacancy.salary_from && vacancy.salary_to) {
    return `${format(vacancy.salary_from)}–${format(vacancy.salary_to)} ${currency}`;
  }
  if (vacancy.salary_from) return `от ${format(vacancy.salary_from)} ${currency}`;
  if (vacancy.salary_to) return `до ${format(vacancy.salary_to)} ${currency}`;
  return null;
});

/** Select the best available short explanation for the card body. */
const summary = computed(() => {
  // Prefer semantic analysis, then deterministic filtering, then raw content.
  if (props.row.analysis) return props.row.analysis.explanation;
  if (props.row.vacancy.filtered_reason) return props.row.vacancy.filtered_reason;
  const description = props.row.vacancy.description.replace(/\s+/g, " ").trim();
  // Keep grid cards compact; complete content remains available in the drawer.
  return description.length > 190 ? `${description.slice(0, 187)}…` : description;
});

/** Trigger semantic analysis for a vacancy that passed deterministic filters. */
async function analyze(): Promise<void> {
  analyzing.value = true;
  actionError.value = "";
  try {
    await api<VacancyAnalysis>(`/vacancies/${props.row.vacancy.id}/analyze`, { method: "POST" });
    // Reload through the parent so the card receives the backend's canonical row.
    emit("changed");
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : "Не удалось выполнить анализ";
  } finally {
    analyzing.value = false;
  }
}

/** Create a shortlisted application record for this vacancy. */
async function track(): Promise<void> {
  tracking.value = true;
  actionError.value = "";
  try {
    await api<Application>("/applications", {
      method: "POST",
      body: JSON.stringify({ vacancy_id: props.row.vacancy.id, status: "shortlisted" }),
    });
    emit("changed");
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : "Не удалось добавить отклик";
  } finally {
    tracking.value = false;
  }
}
</script>

<template>
  <!-- Summary card used by the responsive vacancy result grid. -->
  <article class="vacancy-card">
    <div class="card-top">
      <div>
        <p class="company">{{ row.vacancy.company }}</p>
        <h3>{{ row.vacancy.title }}</h3>
      </div>
      <!-- A muted dash differentiates missing analysis from a zero score. -->
      <div
        class="score"
        :class="{ muted: !row.analysis }"
        :title="row.analysis ? 'Итоговый балл' : 'Ещё не оценено'"
      >
        {{ row.analysis?.final_score ?? "—" }}
      </div>
    </div>

    <!-- Render only metadata that is present or relevant for this row. -->
    <div class="meta">
      <span v-if="row.vacancy.remote" class="tag good">Remote</span>
      <span v-if="row.vacancy.location" class="tag">{{ row.vacancy.location }}</span>
      <span v-if="salary" class="tag">{{ salary }}</span>
      <span v-if="row.analysis?.recommended" class="tag good">Рекомендуется</span>
      <span v-if="row.vacancy.filtered_reason" class="tag warn">Отфильтрована</span>
      <span v-if="row.application" class="tag good">
        {{ applicationLabels[row.application.status] }}
      </span>
    </div>

    <p class="summary">{{ summary || "Описание отсутствует." }}</p>
    <p v-if="actionError" class="inline-error">{{ actionError }}</p>

    <!-- Context-sensitive actions disappear once their goal has been reached. -->
    <div class="card-actions">
      <a :href="row.vacancy.url" target="_blank" rel="noopener noreferrer">Открыть на HH</a>
      <button class="card-button" type="button" @click="emit('open')">Подробнее</button>
      <button
        v-if="!row.analysis && !row.vacancy.filtered_reason"
        class="card-button"
        type="button"
        :disabled="analyzing"
        @click="analyze"
      >
        {{ analyzing ? "Анализ…" : "Анализировать" }}
      </button>
      <button
        v-if="!row.application"
        class="card-button accent"
        type="button"
        :disabled="tracking"
        @click="track"
      >
        {{ tracking ? "Добавляем…" : "В шорт-лист" }}
      </button>
    </div>
  </article>
</template>
