<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "@/api";

interface Hit {
  movie_id: number;
  title: string;
  score: number;
}

const router = useRouter();
const query = ref("");
const hits = ref<Hit[]>([]);
const loading = ref(false);
const searched = ref(false);

async function search() {
  const q = query.value.trim();
  if (!q) return;
  loading.value = true;
  searched.value = true;
  try {
    hits.value = (await api.knowledgeSearch(q, 8)) as Hit[];
  } catch {
    hits.value = [];
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="page">
    <h2>知识库检索</h2>
    <p class="muted">基于电影简介的关键词检索，直接查询数据库中 9000+ 部电影简介。</p>
    <p class="muted small">支持中英文关键词，输入剧情描述或主题词，如「末日生存」「space adventure」。</p>

    <div class="search">
      <input v-model="query" placeholder="描述剧情或关键词，如 space adventure" @keydown.enter="search" />
      <button class="btn btn-primary" @click="search">检索</button>
    </div>

    <div v-if="loading" class="muted">检索中…</div>
    <div v-else-if="hits.length" class="list">
      <div
        v-for="h in hits"
        :key="h.movie_id"
        class="card hit"
        @click="router.push(`/movie/${h.movie_id}`)"
      >
        <span>{{ h.title }}</span>
        <span class="muted">相关度 {{ h.score }}</span>
      </div>
    </div>
    <div v-else-if="searched" class="muted">无匹配结果。</div>
  </div>
</template>

<style scoped>
.page {
  padding: 24px;
}
.small {
  font-size: 12px;
}
.search {
  display: flex;
  gap: 8px;
  margin: 16px 0;
  max-width: 560px;
}
.search input {
  flex: 1;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 560px;
}
.hit {
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  cursor: pointer;
}
.hit:hover {
  border-color: var(--accent);
}
</style>
