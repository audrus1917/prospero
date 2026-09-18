<script setup lang="ts">
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
    <span>∴</span>
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
  </div>
</template>
