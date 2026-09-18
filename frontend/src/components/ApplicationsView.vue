<script setup lang="ts">
import { onActivated, onMounted, reactive, ref } from "vue";

import { api } from "../api";
import type { Application, ApplicationStatus, VacancyListItem } from "../types";
import EmptyState from "./EmptyState.vue";

const applications = ref<Application[]>([]);
const vacancies = ref(new Map<number, VacancyListItem["vacancy"]>());
const loading = ref(false);
const errorMessage = ref("");
const loaded = ref(false);
const notes = reactive<Record<number, string>>({});
const savingNotes = ref<number | null>(null);

const statuses: { value: ApplicationStatus; label: string }[] = [
  { value: "new", label: "Новый" },
  { value: "shortlisted", label: "В шорт-листе" },
  { value: "applied", label: "Отклик отправлен" },
  { value: "hr", label: "Интервью с HR" },
  { value: "technical", label: "Техническое интервью" },
  { value: "final", label: "Финальный этап" },
  { value: "offer", label: "Оффер" },
  { value: "rejected", label: "Отказ" },
  { value: "withdrawn", label: "Снят" },
];

async function load(): Promise<void> {
  loading.value = true;
  errorMessage.value = "";
  try {
    const [applicationRows, vacancyRows] = await Promise.all([
      api<Application[]>("/applications?limit=100"),
      api<VacancyListItem[]>("/vacancies?limit=100"),
    ]);
    applications.value = applicationRows;
    vacancies.value = new Map(vacancyRows.map((row) => [row.vacancy.id, row.vacancy]));
    for (const application of applicationRows) {
      notes[application.id] = application.notes ?? "";
    }
    loaded.value = true;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Не удалось загрузить отклики";
  } finally {
    loading.value = false;
  }
}

async function updateStatus(application: Application, event: Event): Promise<void> {
  const select = event.target as HTMLSelectElement;
  const previousStatus = application.status;
  const status = select.value as ApplicationStatus;
  select.disabled = true;
  try {
    const updated = await api<Application>(`/applications/${application.id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
    application.status = updated.status;
  } catch (error) {
    select.value = previousStatus;
    errorMessage.value = error instanceof Error ? error.message : "Не удалось изменить статус";
  } finally {
    select.disabled = false;
  }
}

async function updateNotes(application: Application): Promise<void> {
  savingNotes.value = application.id;
  errorMessage.value = "";
  try {
    const updated = await api<Application>(`/applications/${application.id}`, {
      method: "PATCH",
      body: JSON.stringify({ notes: notes[application.id]?.trim() || null }),
    });
    application.notes = updated.notes;
    notes[application.id] = updated.notes ?? "";
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Не удалось сохранить заметку";
  } finally {
    savingNotes.value = null;
  }
}

onMounted(load);
onActivated(() => {
  if (loaded.value) void load();
});
</script>

<template>
  <section class="workspace standalone-view">
    <div class="section-heading">
      <div>
        <p class="eyebrow">PIPELINE</p>
        <h2>Мои отклики</h2>
      </div>
      <span class="count-badge">{{ applications.length }}</span>
    </div>

    <div v-if="errorMessage" class="error-panel">{{ errorMessage }}</div>
    <div v-else-if="loading && !loaded" class="loading-panel">Загружаем отклики…</div>
    <div v-else-if="applications.length" class="application-list">
      <article v-for="application in applications" :key="application.id" class="application-row">
        <div class="application-main">
          <h3>{{ vacancies.get(application.vacancy_id)?.title ?? `Вакансия #${application.vacancy_id}` }}</h3>
          <p>{{ vacancies.get(application.vacancy_id)?.company ?? "Вакансия больше не доступна в списке" }}</p>
          <a
            v-if="vacancies.get(application.vacancy_id)"
            :href="vacancies.get(application.vacancy_id)?.url"
            target="_blank"
            rel="noopener noreferrer"
          >Открыть вакансию ↗</a>
        </div>
        <div class="application-notes">
          <label :for="`application-notes-${application.id}`">Заметка</label>
          <textarea
            :id="`application-notes-${application.id}`"
            v-model="notes[application.id]"
            maxlength="10000"
            rows="2"
            placeholder="Контакт, следующий шаг, важные детали…"
          />
          <button
            class="card-button"
            type="button"
            :disabled="savingNotes === application.id || notes[application.id] === (application.notes ?? '')"
            @click="updateNotes(application)"
          >
            {{ savingNotes === application.id ? "Сохраняем…" : "Сохранить" }}
          </button>
        </div>
        <select
          :value="application.status"
          aria-label="Статус отклика"
          @change="updateStatus(application, $event)"
        >
          <option v-for="status in statuses" :key="status.value" :value="status.value">
            {{ status.label }}
          </option>
        </select>
      </article>
    </div>
    <EmptyState
      v-else
      title="Откликов пока нет"
      description="Добавьте интересную вакансию в шорт-лист."
    />
  </section>
</template>
