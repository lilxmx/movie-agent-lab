<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useConfigStore } from "@/stores/config";

const props = defineProps<{ movieId: number; title?: string }>();
const configStore = useConfigStore();
const failed = ref(false);

const posterSrc = computed(() => configStore.posterUrl(props.movieId));

// CDN 地址变更后重置失败状态，触发重新加载
watch(posterSrc, () => { failed.value = false; });
</script>

<template>
  <div class="poster">
    <img
      v-if="!failed"
      :src="posterSrc"
      :alt="props.title"
      @error="failed = true"
    />
    <div v-else class="placeholder">
      <span>🎞️</span>
      <small>{{ props.title }}</small>
    </div>
  </div>
</template>

<style scoped>
.poster {
  width: 100%;
  aspect-ratio: 2 / 3;
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-soft);
}
.poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--text-dim);
  font-size: 28px;
  padding: 8px;
  text-align: center;
}
.placeholder small {
  font-size: 11px;
}
</style>
