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
const menuOpen = ref(false);
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
  menuOpen.value = false;
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
  menuOpen.value = false;
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape") menuOpen.value = false;
}

// Register global listeners only for the lifetime of the root component.
onMounted(() => {
  window.addEventListener("popstate", restoreView);
  window.addEventListener("keydown", onKeydown);
});
onBeforeUnmount(() => {
  window.removeEventListener("popstate", restoreView);
  window.removeEventListener("keydown", onKeydown);
});
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <button
        class="menu-button"
        type="button"
        aria-label="Открыть меню"
        aria-controls="workspace-menu"
        :aria-expanded="menuOpen"
        @click="menuOpen = true"
      ><span></span><span></span><span></span></button>
      <strong class="topbar-title">{{ views.find(({ name }) => name === activeView)?.label }}</strong>
      <a class="api-link" href="/docs">API</a>
    </header>

    <button v-if="menuOpen" class="menu-backdrop" type="button" aria-label="Закрыть меню" @click="menuOpen = false"></button>
    <nav id="workspace-menu" class="side-menu" :class="{ open: menuOpen }" aria-label="Основная навигация">
      <div class="menu-header"><a class="sidebar-brand" href="/">PROSPERO</a><button class="menu-close" type="button" aria-label="Закрыть меню" @click="menuOpen = false">×</button></div>
      <span class="menu-section-label">Рабочее пространство</span>
      <button
        v-for="view in views"
        :key="view.name"
        class="menu-link"
        :class="{ active: activeView === view.name }"
        type="button"
        :aria-current="activeView === view.name ? 'page' : undefined"
        @click="selectView(view.name)"
      >{{ view.label }}</button>
      <div class="menu-footer"><span>Поиск работы и управление откликами</span></div>
    </nav>

    <!-- Keep inactive views mounted so filters and unsaved form input survive. -->
    <main class="main-content">
      <KeepAlive><component :is="activeComponent" /></KeepAlive>
    </main>
  </div>
</template>
