<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import ApplicationsView from "./components/ApplicationsView.vue";
import DocumentsView from "./components/DocumentsView.vue";
import VacanciesView from "./components/VacanciesView.vue";

// The application intentionally uses lightweight local navigation instead of
// a router because the MVP has only three top-level views.
type ViewName = "vacancies" | "applications" | "documents";

// This array is the single source for navigation order, labels, and validation
// of the `view` query parameter.
const views: { name: ViewName; label: string }[] = [
  { name: "vacancies", label: "Вакансии" },
  { name: "applications", label: "Отклики" },
  { name: "documents", label: "Анализ документов" },
];

// Deep-link to a view through `?view=...`; unknown values safely fall back to
// the primary vacancies screen.
const requestedView = new URLSearchParams(window.location.search).get("view");
const initialView = views.some(({ name }) => name === requestedView)
  ? (requestedView as ViewName)
  : "vacancies";
const activeView = ref<ViewName>(initialView);
// Resolve the selected name to a component. KeepAlive below preserves each
// view's local state while the user switches between navigation tabs.
const activeComponent = computed(() => ({
  vacancies: VacanciesView,
  applications: ApplicationsView,
  documents: DocumentsView,
})[activeView.value]);

/** Read and validate the active view from the current browser URL. */
function viewFromUrl(): ViewName {
  const requested = new URLSearchParams(window.location.search).get("view");
  return views.some(({ name }) => name === requested) ? (requested as ViewName) : "vacancies";
}

/** Activate a view and create a browser-history entry for back/forward use. */
function selectView(view: ViewName): void {
  activeView.value = view;
  const url = new URL(window.location.href);
  // Keep the default URL clean, while non-default views remain linkable.
  if (view === "vacancies") {
    url.searchParams.delete("view");
  } else {
    url.searchParams.set("view", view);
  }
  window.history.pushState({}, "", url);
}

/** Synchronize component state after browser back or forward navigation. */
function restoreView(): void {
  activeView.value = viewFromUrl();
}

// Register global listeners only for the lifetime of the root component.
onMounted(() => window.addEventListener("popstate", restoreView));
onBeforeUnmount(() => window.removeEventListener("popstate", restoreView));
</script>

<template>
  <!-- Persistent application identity and top-level view navigation. -->
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

  <!-- Keep inactive views mounted so filters and unsaved form input survive. -->
  <main>
    <KeepAlive>
      <component :is="activeComponent" />
    </KeepAlive>
  </main>
</template>
