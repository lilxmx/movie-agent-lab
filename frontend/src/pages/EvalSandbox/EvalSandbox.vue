<script setup lang="ts">
import { ref } from "vue";
import { api } from "@/api";

interface Coverage {
  mode: string;
  total_movies: number;
  covered_movies: number;
  sampled_users: number;
  coverage: number;
}

const mode = ref("classic");
const result = ref<Coverage | null>(null);
const loading = ref(false);

async function run() {
  loading.value = true;
  try {
    result.value = (await api.coverage(mode.value)) as Coverage;
  } catch {
    result.value = null;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="page">
    <h2>评测沙箱</h2>
    <p class="muted">对传统推荐与 Agent 推荐做离线指标评测，当前支持覆盖率（多样性）。</p>

    <div class="controls">
      <select v-model="mode">
        <option value="classic">传统推荐</option>
        <option value="agent">Agent 推荐</option>
      </select>
      <button class="btn btn-primary" :disabled="loading" @click="run">运行评测</button>
    </div>

    <div v-if="loading" class="muted">评测中…</div>
    <div v-else-if="result" class="card report">
      <div class="row"><span class="muted">模式</span><span>{{ result.mode }}</span></div>
      <div class="row"><span class="muted">电影总数</span><span>{{ result.total_movies }}</span></div>
      <div class="row"><span class="muted">采样用户数</span><span>{{ result.sampled_users }}</span></div>
      <div class="row"><span class="muted">被覆盖电影</span><span>{{ result.covered_movies }}</span></div>
      <div class="row big"><span>覆盖率</span><span>{{ (result.coverage * 100).toFixed(2) }}%</span></div>
    </div>
  </div>
</template>

<style scoped>
.page {
  padding: 24px;
}
.controls {
  display: flex;
  gap: 8px;
  margin: 16px 0;
}
select {
  background: var(--bg-soft);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 12px;
}
.report {
  max-width: 420px;
  padding: 18px;
}
.row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
}
.row.big {
  font-size: 18px;
  font-weight: 700;
  color: var(--accent-2);
  border-bottom: none;
}
</style>
