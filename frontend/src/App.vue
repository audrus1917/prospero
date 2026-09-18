<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import ApplicationsView from "./components/ApplicationsView.vue";
import DocumentsView from "./components/DocumentsView.vue";
import VacanciesView from "./components/VacanciesView.vue";

type ViewName = "vacancies" | "applications" | "documents";

const views: { name: ViewName; label: string }[] = [
  { name: "vacancies", label: "Вакансии" },
  { name: "applications", label: "Отклики" },
  { name: "documents", label: "PDF-анализ" },
];

const requestedView = new URLSearchParams(window.location.search).get("view");
const initialView = views.some(({ name }) => name === requestedView)
  ? (requestedView as ViewName)
  : "vacancies";
const activeView = ref<ViewName>(initialView);
const activeComponent = computed(() => ({
  vacancies: VacanciesView,
  applications: ApplicationsView,
  documents: DocumentsView,
})[activeView.value]);

function viewFromUrl(): ViewName {
  const requested = new URLSearchParams(window.location.search).get("view");
  return views.some(({ name }) => name === requested) ? (requested as ViewName) : "vacancies";
}

function selectView(view: ViewName): void {
  activeView.value = view;
  const url = new URL(window.location.href);
  if (view === "vacancies") {
    url.searchParams.delete("view");
  } else {
    url.searchParams.set("view", view);
  }
  window.history.pushState({}, "", url);
}

function restoreView(): void {
  activeView.value = viewFromUrl();
}

onMounted(() => window.addEventListener("popstate", restoreView));
onBeforeUnmount(() => window.removeEventListener("popstate", restoreView));
</script>

<template>
  <header class="topbar">
    <a class="brand" href="/" aria-label="Prospero">
      <span class="brand-mark">P</span>
      <span>PROSPERO</span>
    </a>
    <nav aria-label="Основная навигация">
      <button
        v-for="view in views"
        :key="view.name"
        class="nav-link"
        :class="{ active: activeView === view.name }"
        type="button"
        @click="selectView(view.name)"
      >
        {{ view.label }}
      </button>
    </nav>
    <a class="api-link" href="/docs">API ↗</a>
  </header>

  <main>
    <KeepAlive>
      <component :is="activeComponent" />
    </KeepAlive>
  </main>
</template>
