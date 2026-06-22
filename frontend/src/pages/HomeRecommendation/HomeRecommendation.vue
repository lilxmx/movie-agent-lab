<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "@/api";
import RecCard from "@/components/RecCard.vue";
import type { RecItem } from "@/types";

type Mode = "classic" | "agent";

const mode = ref<Mode>("classic");
const scene = ref("personalized");
const items = ref<RecItem[]>([]);
const traceId = ref("");
const loading = ref(false);

const scenes = [
  { key: "personalized", label: "个性化" },
  { key: "hot", label: "热门" },
];

async function load() {
  loading.value = true;
  try {
    const res =
      mode.value === "agent"
        ? await api.recommendAgent("personalized", 12)
        : await api.recommendClassic(scene.value, 12);
    items.value = res.items;
    traceId.value = res.trace_id;
  } catch {
    items.value = [];
  } finally {
    loading.value = false;
  }
}

function switchMode(m: Mode) {
  mode.value = m;
  load();
}

function switchScene(s: string) {
  scene.value = s;
  load();
}

onMounted(load);
</script>

<template>
  <div class="home">
    <header class="head">
      <h2>推荐首页</h2>
      <div class="switch">
        <button class="seg" :class="{ active: mode === 'classic' }" @click="switchMode('classic')">
          传统推荐
        </button>
        <button class="seg" :class="{ active: mode === 'agent' }" @click="switchMode('agent')">
          Agent 推荐
        </button>
      </div>
    </header>

    <div v-if="mode === 'classic'" class="scenes">
      <button
        v-for="s in scenes"
        :key="s.key"
        class="tag-btn"
        :class="{ active: scene === s.key }"
        @click="switchScene(s.key)"
      >
        {{ s.label }}
      </button>
    </div>

    <div class="trace muted" v-if="traceId">trace_id: {{ traceId }}</div>

    <div v-if="loading" class="muted">加载中…</div>
    <div v-else-if="items.length" class="grid">
      <RecCard v-for="item in items" :key="item.movie_id" :item="item" />
    </div>
    <div v-else class="muted">暂无推荐结果，请登录或先对电影评分。</div>
  </div>
</template>

<style scoped>
.home {
  padding: 24px;
}
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.head h2 {
  margin: 0;
}
.switch {
  display: flex;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 4px;
  gap: 4px;
}
.seg {
  border: none;
  background: transparent;
  color: var(--text-dim);
  padding: 8px 18px;
  border-radius: 8px;
}
.seg.active {
  background: var(--accent);
  color: #fff;
}
.scenes {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}
.tag-btn {
  border: 1px solid var(--border);
  background: var(--bg-card);
  color: var(--text-dim);
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 13px;
}
.tag-btn.active {
  border-color: var(--accent);
  color: var(--accent);
}
.trace {
  margin: 12px 0;
  font-size: 12px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
  margin-top: 16px;
}
</style>
