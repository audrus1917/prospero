<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api } from "../api";
import type {
  PDFDocument,
  PDFDocumentRecord,
  PDFMatch,
  PDFProcessingResult,
} from "../types";
import EmptyState from "./EmptyState.vue";
import StatusMessage from "./StatusMessage.vue";

const resumes = ref<PDFDocument[]>([]);
const vacancyDocuments = ref<PDFDocument[]>([]);
const resumeCatalog = ref(new Map<string, PDFDocumentRecord>());
const vacancyCatalog = ref(new Map<string, PDFDocumentRecord>());
const selectedResume = ref("");
const selectedVacancies = ref<string[]>([]);
const results = ref<PDFMatch[]>([]);
const loading = ref(false);
const processing = ref(false);
const analyzing = ref(false);
const statusMessage = ref("");
const statusError = ref(false);

const canAnalyze = computed(() => Boolean(selectedResume.value && selectedVacancies.value.length));

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} Б`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} КБ`;
  return `${(bytes / 1024 / 1024).toFixed(1)} МБ`;
}

function processingStatusLabel(status: string): string {
  return {
    pending: "ожидает обработки",
    processed: "обработан",
    needs_ocr: "нужен OCR",
    failed: "ошибка",
  }[status] ?? status;
}

function fileLabel(document: PDFDocument, catalog: Map<string, PDFDocumentRecord>): string {
  const record = catalog.get(document.name);
  const state = record ? ` · ${processingStatusLabel(record.processing_status)}` : "";
  return `${document.name} · ${formatFileSize(document.size)}${state}`;
}

async function loadDocuments(): Promise<void> {
  loading.value = true;
  statusError.value = false;
  try {
    const [resumeFiles, vacancyFiles, resumeRecords, vacancyRecords] = await Promise.all([
      api<PDFDocument[]>("/documents/resumes"),
      api<PDFDocument[]>("/documents/vacancies"),
      api<PDFDocumentRecord[]>("/documents/catalog/resume"),
      api<PDFDocumentRecord[]>("/documents/catalog/vacancy"),
    ]);
    resumes.value = resumeFiles;
    vacancyDocuments.value = vacancyFiles;
    resumeCatalog.value = new Map(resumeRecords.map((record) => [record.filename, record]));
    vacancyCatalog.value = new Map(vacancyRecords.map((record) => [record.filename, record]));
    if (!resumeFiles.some((file) => file.name === selectedResume.value)) {
      selectedResume.value = resumeFiles[0]?.name ?? "";
    }
    const availableVacancies = new Set(vacancyFiles.map((file) => file.name));
    selectedVacancies.value = selectedVacancies.value.filter((name) => availableVacancies.has(name));
    if (!selectedVacancies.value.length) {
      selectedVacancies.value = vacancyFiles.map((file) => file.name);
    }
  } catch (error) {
    statusError.value = true;
    statusMessage.value = error instanceof Error ? error.message : "Не удалось загрузить документы";
  } finally {
    loading.value = false;
  }
}

async function processDocuments(): Promise<void> {
  processing.value = true;
  statusError.value = false;
  statusMessage.value = "Извлекаем текст и определяем категории…";
  try {
    const result = await api<PDFProcessingResult>("/documents/process", { method: "POST" });
    statusMessage.value = `Обработано: ${result.processed}, OCR: ${result.needs_ocr}, ошибок: ${result.failed}`;
    await loadDocuments();
  } catch (error) {
    statusError.value = true;
    statusMessage.value = error instanceof Error ? error.message : "Не удалось обработать документы";
  } finally {
    processing.value = false;
  }
}

async function analyzeDocuments(): Promise<void> {
  if (!canAnalyze.value) {
    statusError.value = true;
    statusMessage.value = "Выберите резюме и хотя бы одну вакансию.";
    return;
  }
  analyzing.value = true;
  statusError.value = false;
  statusMessage.value = "Извлекаем текст и сравниваем документы…";
  results.value = [];
  try {
    results.value = await api<PDFMatch[]>("/documents/analyze", {
      method: "POST",
      body: JSON.stringify({
        resume_file: selectedResume.value,
        vacancy_files: selectedVacancies.value,
      }),
    });
    statusMessage.value = `Готово: проанализировано ${results.value.length}`;
  } catch (error) {
    statusError.value = true;
    statusMessage.value = error instanceof Error ? error.message : "Не удалось сравнить документы";
  } finally {
    analyzing.value = false;
  }
}

onMounted(loadDocuments);
</script>

<template>
  <section class="workspace standalone-view">
    <div class="section-heading">
      <div>
        <p class="eyebrow">DOCUMENT MATCHING</p>
        <h2>Резюме × вакансии</h2>
      </div>
    </div>

    <div class="document-layout">
      <form class="document-controls" @submit.prevent="analyzeDocuments">
        <div>
          <label for="resume-file">Выбранное резюме</label>
          <select id="resume-file" v-model="selectedResume" required :disabled="loading">
            <option v-if="!resumes.length" value="">PDF-резюме не найдены</option>
            <option v-for="resume in resumes" :key="resume.name" :value="resume.name">
              {{ fileLabel(resume, resumeCatalog) }}
            </option>
          </select>
        </div>
        <fieldset>
          <legend>PDF-вакансии</legend>
          <div class="file-list">
            <label v-for="document in vacancyDocuments" :key="document.name" class="file-option">
              <input v-model="selectedVacancies" type="checkbox" :value="document.name">
              <span>{{ fileLabel(document, vacancyCatalog) }}</span>
            </label>
            <p v-if="!vacancyDocuments.length" class="privacy-note">PDF-вакансии не найдены.</p>
          </div>
        </fieldset>
        <p class="privacy-note">
          Текст выбранных документов передаётся настроенному LLM-провайдеру.
          В режиме heuristic анализ полностью локальный.
        </p>
        <button class="secondary-button" type="button" :disabled="processing" @click="processDocuments">
          {{ processing ? "Обрабатываем…" : "Обработать новые PDF" }}
        </button>
        <button class="primary-button" type="submit" :disabled="analyzing || !canAnalyze">
          {{ analyzing ? "Сравниваем…" : "Сравнить документы" }}
        </button>
        <StatusMessage :message="statusMessage" :error="statusError" />
      </form>

      <div class="document-results">
        <article v-for="match in results" :key="match.vacancy_file" class="document-match">
          <header>
            <h3>{{ match.vacancy_file }}</h3>
            <div class="score">{{ match.final_score }}</div>
          </header>
          <p class="summary">{{ match.explanation }}</p>
          <template v-if="match.strengths.length">
            <h4>Сильные стороны</h4>
            <ul><li v-for="item in match.strengths" :key="item">{{ item }}</li></ul>
          </template>
          <template v-if="match.gaps.length">
            <h4>Пробелы</h4>
            <ul><li v-for="item in match.gaps" :key="item">{{ item }}</li></ul>
          </template>
          <template v-if="match.recommendations.length">
            <h4>Рекомендации для резюме</h4>
            <ul><li v-for="item in match.recommendations" :key="item">{{ item }}</li></ul>
          </template>
        </article>
        <div v-if="analyzing" class="loading-panel">Анализ может занять несколько минут…</div>
        <EmptyState
          v-else-if="!results.length"
          title="Добавьте PDF-файлы"
          description="Резюме — в data/resumes, вакансии — в data/vacancies."
        />
      </div>
    </div>
  </section>
</template>
