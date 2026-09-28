<script setup lang="ts">
import { onActivated, onMounted, reactive, ref } from "vue";

import { api } from "../api";
import type { Application, ApplicationStatus, VacancyListItem } from "../types";
import EmptyState from "./EmptyState.vue";

// Application records and vacancy metadata are fetched separately by the API.
const applications = ref<Application[]>([]);
// Index vacancies by id to make repeated template lookups inexpensive and clear.
const vacancies = ref(new Map<number, VacancyListItem["vacancy"]>());
const loading = ref(false);
const errorMessage = ref("");
// Distinguish the first blocking load from background refreshes after KeepAlive activation.
const loaded = ref(false);
// Draft notes are separate from saved application.notes values until submitted.
const notes = reactive<Record<number, string>>({});
// Store the id rather than a boolean so only the submitted row is disabled.
const savingNotes = ref<number | null>(null);

// Ordered workflow options shared by every application status selector.
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

/** Load tracking records and their associated vacancy display metadata. */
async function load(): Promise<void> {
  loading.value = true;
  errorMessage.value = "";
  try {
    // These independent reads can run concurrently to minimize view startup time.
    const [applicationRows, vacancyRows] = await Promise.all([
      api<Application[]>("/applications?limit=100"),
      api<VacancyListItem[]>("/vacancies?limit=100"),
    ]);
    applications.value = applicationRows;
    vacancies.value = new Map(vacancyRows.map((row) => [row.vacancy.id, row.vacancy]));
    // Initialize editable drafts from the latest persisted notes.
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

/** Persist a status selected directly in an application row. */
async function updateStatus(application: Application, event: Event): Promise<void> {
  // The handler is attached only to a select, so this narrow assertion is safe.
  const select = event.target as HTMLSelectElement;
  // Retain the prior value to roll back the native control on request failure.
  const previousStatus = application.status;
  const status = select.value as ApplicationStatus;
  // Prevent another change while the current transition is unresolved.
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

/** Trim and persist the draft note for a single application. */
async function updateNotes(application: Application): Promise<void> {
  savingNotes.value = application.id;
  errorMessage.value = "";
  try {
    const updated = await api<Application>(`/applications/${application.id}`, {
      method: "PATCH",
      // Convert a blank note to null to match the optional backend field.
      body: JSON.stringify({ notes: notes[application.id]?.trim() || null }),
    });
    application.notes = updated.notes;
    // Synchronize the draft so the save button becomes disabled again.
    notes[application.id] = updated.notes ?? "";
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Не удалось сохранить заметку";
  } finally {
    savingNotes.value = null;
  }
}

// Load on first mount. KeepAlive calls onActivated when the user returns to the
// cached view, at which point a refresh picks up changes made elsewhere.
onMounted(load);
onActivated(() => {
  if (loaded.value) void load();
});
</script>

<template>
  <!-- Application pipeline: vacancy context, editable notes, and current stage. -->
  <section class="workspace standalone-view">
    <div class="section-heading">
      <div>
        <p class="eyebrow">PIPELINE</p>
        <h2>Мои отклики</h2>
      </div>
      <span class="count-badge">{{ applications.length }}</span>
    </div>

    <!-- Preserve already loaded rows during refresh; block only the first load. -->
    <div v-if="errorMessage" class="error-panel">{{ errorMessage }}</div>
    <div v-else-if="loading && !loaded" class="loading-panel">Загружаем отклики…</div>
    <div v-else-if="applications.length" class="application-list">
      <!-- Each row is independently editable and persisted. -->
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
        <!-- Local draft avoids a network request for every typed character. -->
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
        <!-- Status changes are saved immediately and rolled back on failure. -->
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
