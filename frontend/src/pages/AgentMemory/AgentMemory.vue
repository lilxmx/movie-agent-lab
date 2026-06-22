<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "@/api";
import { useAuthStore } from "@/stores/auth";
import type { UserProfile } from "@/types";

const auth = useAuthStore();
const profile = ref<UserProfile | null>(null);
const error = ref("");

async function load() {
  if (!auth.userId) {
    error.value = "请先登录以查看 Agent Memory。";
    return;
  }
  try {
    profile.value = await api.profile(auth.userId);
  } catch (e) {
    error.value = "加载画像失败。";
  }
}

onMounted(load);
</script>

<template>
  <div class="page">
    <h2>Agent Memory</h2>
    <p class="muted">用户画像、偏好标签与长期记忆，是 Agent 推荐与对话推荐的记忆基础。</p>

    <div v-if="profile" class="cards">
      <div class="card stat">
        <div class="num">{{ profile.rating_count }}</div>
        <div class="muted">评分数</div>
      </div>
      <div class="card stat">
        <div class="num">{{ profile.avg_rating ?? "-" }}</div>
        <div class="muted">平均评分</div>
      </div>
      <div class="card stat">
        <div class="num">{{ profile.avg_released_year ?? "-" }}</div>
        <div class="muted">平均观影年份</div>
      </div>
    </div>

    <div v-if="profile" class="card section">
      <h3>偏好标签</h3>
      <span v-for="g in profile.like_genres" :key="g" class="tag">{{ g }}</span>
      <span v-if="!profile.like_genres.length" class="muted">暂无</span>
    </div>

    <div v-if="profile" class="card section">
      <h3>长期记忆</h3>
      <div v-for="(m, i) in profile.memories" :key="i" class="memo">
        <span class="tag">{{ m.type }}</span>{{ m.content }}
      </div>
      <div v-if="!profile.memories.length" class="muted">尚无沉淀的长期记忆。</div>
    </div>

    <div v-if="error" class="muted">{{ error }}</div>
  </div>
</template>

<style scoped>
.page {
  padding: 24px;
}
.cards {
  display: flex;
  gap: 16px;
  margin: 16px 0;
}
.stat {
  padding: 18px 28px;
  text-align: center;
}
.num {
  font-size: 28px;
  font-weight: 700;
  color: var(--accent-2);
}
.section {
  padding: 18px;
  margin-bottom: 16px;
}
.memo {
  padding: 8px 0;
  display: flex;
  gap: 8px;
  align-items: center;
}
</style>
