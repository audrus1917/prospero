<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";

import type { VacancyListItem } from "../types";

const props = defineProps<{ row: VacancyListItem }>();
const emit = defineEmits<{ close: [] }>();

const panel = ref<HTMLElement | null>(null);
let previousOverflow = "";

const scores = computed(() => {
  const analysis = props.row.analysis;
  if (!analysis) return [];
  return [
    { label: "Технологии", value: analysis.technical_score },
    { label: "Уровень", value: analysis.seniority_score },
    { label: "Домен", value: analysis.domain_score },
    { label: "Локация", value: analysis.location_score },
    { label: "Зарплата", value: analysis.salary_score },
  ];
});

const description = computed(() => props.row.vacancy.description
  .replace(/<[^>]+>/g, " ")
  .replace(/\s+/g, " ")
  .trim());

function closeOnEscape(event: KeyboardEvent): void {
  if (event.key === "Escape") emit("close");
}

onMounted(async () => {
  previousOverflow = document.body.style.overflow;
  document.body.style.overflow = "hidden";
  document.addEventListener("keydown", closeOnEscape);
  await nextTick();
  panel.value?.focus();
});

onBeforeUnmount(() => {
  document.body.style.overflow = previousOverflow;
  document.removeEventListener("keydown", closeOnEscape);
});
</script>

<template>
  <Teleport to="body">
    <div class="drawer-backdrop" @click.self="emit('close')">
      <aside
        ref="panel"
        class="vacancy-drawer"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="`vacancy-title-${row.vacancy.id}`"
        tabindex="-1"
      >
        <header class="drawer-header">
          <div>
            <p class="company">{{ row.vacancy.company }}</p>
            <h2 :id="`vacancy-title-${row.vacancy.id}`">{{ row.vacancy.title }}</h2>
          </div>
          <button class="icon-button" type="button" aria-label="Закрыть" @click="emit('close')">×</button>
        </header>

        <div class="meta">
          <span v-if="row.vacancy.remote" class="tag good">Remote</span>
          <span v-if="row.vacancy.location" class="tag">{{ row.vacancy.location }}</span>
          <span v-if="row.analysis?.recommended" class="tag good">Рекомендуется</span>
          <span v-if="row.vacancy.filtered_reason" class="tag warn">Отфильтрована</span>
        </div>

        <section v-if="row.analysis" class="analysis-section">
          <div class="analysis-total">
            <div class="score">{{ row.analysis.final_score }}</div>
            <div>
              <p class="eyebrow">ИТОГОВАЯ ОЦЕНКА</p>
              <p>{{ row.analysis.explanation }}</p>
            </div>
          </div>
          <div class="score-breakdown">
            <div v-for="score in scores" :key="score.label" class="score-row">
              <span>{{ score.label }}</span>
              <progress :value="score.value" max="100">{{ score.value }}</progress>
              <strong>{{ score.value }}</strong>
            </div>
          </div>

          <div class="analysis-lists">
            <div v-if="row.analysis.strengths.length">
              <h3>Сильные стороны</h3>
              <ul><li v-for="item in row.analysis.strengths" :key="item">{{ item }}</li></ul>
            </div>
            <div v-if="row.analysis.gaps.length">
              <h3>Пробелы</h3>
              <ul><li v-for="item in row.analysis.gaps" :key="item">{{ item }}</li></ul>
            </div>
            <div v-if="row.analysis.missing_keywords.length">
              <h3>Недостающие ключевые слова</h3>
              <div class="meta">
                <span v-for="item in row.analysis.missing_keywords" :key="item" class="tag warn">{{ item }}</span>
              </div>
            </div>
          </div>
        </section>

        <section v-else-if="row.vacancy.filtered_reason" class="analysis-section">
          <h3>Причина фильтрации</h3>
          <p>{{ row.vacancy.filtered_reason }}</p>
        </section>

        <section class="description-section">
          <h3>Описание вакансии</h3>
          <p>{{ description || "Описание отсутствует." }}</p>
        </section>

        <footer class="drawer-footer">
          <span v-if="row.application" class="tag good">Вакансия добавлена в отклики</span>
          <a :href="row.vacancy.url" target="_blank" rel="noopener noreferrer">Открыть на HH ↗</a>
        </footer>
      </aside>
    </div>
  </Teleport>
</template>
