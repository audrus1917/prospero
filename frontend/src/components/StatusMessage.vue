<script setup lang="ts">
// `error` changes only presentation; the message text remains controlled by
// the parent workflow that owns the async operation.
defineProps<{
  message: string;
  error?: boolean;
}>();
</script>

<template>
  <!-- aria-live announces collection and processing updates to screen readers. -->
  <p class="form-status" :class="{ error }" aria-live="polite">{{ message }}</p>
</template>
