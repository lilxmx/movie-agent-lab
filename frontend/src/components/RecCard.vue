<script setup lang="ts">
import { useRouter } from "vue-router";
import MoviePoster from "./MoviePoster.vue";
import type { RecItem } from "@/types";

const props = defineProps<{ item: RecItem }>();
const router = useRouter();
</script>

<template>
  <div class="rec-card card" @click="router.push(`/movie/${props.item.movie_id}`)">
    <MoviePoster :movie-id="props.item.movie_id" :title="props.item.title" />
    <div class="info">
      <div class="name">{{ props.item.title }}</div>
      <div class="score" v-if="props.item.score">匹配度 {{ props.item.score.toFixed(2) }}</div>
      <div class="reason muted" v-if="props.item.reason">{{ props.item.reason }}</div>
      <span class="badge">{{ props.item.source }}</span>
    </div>
  </div>
</template>

<style scoped>
.rec-card {
  padding: 8px;
  cursor: pointer;
  transition: transform 0.15s ease;
}
.rec-card:hover {
  transform: translateY(-3px);
  border-color: var(--accent);
}
.info {
  padding: 8px 4px 4px;
}
.name {
  font-weight: 600;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.score {
  font-size: 12px;
  color: var(--accent-2);
  margin-top: 2px;
}
.reason {
  font-size: 12px;
  margin-top: 4px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.badge {
  display: inline-block;
  margin-top: 6px;
  font-size: 10px;
  padding: 1px 8px;
  border-radius: 999px;
  background: rgba(56, 211, 159, 0.15);
  color: var(--accent-2);
}
</style>
