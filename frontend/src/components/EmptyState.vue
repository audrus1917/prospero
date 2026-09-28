<script setup lang="ts">
// Optional copy makes this presentation component reusable across all lists.
// Defaults provide a sensible generic empty-state message.
withDefaults(defineProps<{
  title?: string;
  description?: string;
}>(), {
  title: "Здесь пока пусто",
  description: "Измените параметры или добавьте новые данные.",
});
</script>

<template>
  <div class="empty-state">
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
  </div>
</template>
