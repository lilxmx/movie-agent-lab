<script setup lang="ts">
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();

const nav = [
  { name: "ChatRecommend", path: "/chat", label: "对话推荐", icon: "💬" },
  { name: "HomeRecommendation", path: "/home", label: "推荐首页", icon: "🏠" },
  { name: "AgentMemory", path: "/memory", label: "Agent Memory", icon: "🧠" },
  { name: "KnowledgeBase", path: "/knowledge", label: "知识库", icon: "📚" },
  { name: "EvalSandbox", path: "/eval", label: "评测沙箱", icon: "📊" },
];

function go(path: string) {
  router.push(path);
}

function handleAuth() {
  if (auth.token) {
    auth.logout();
  }
  router.push("/login");
}
</script>

<template>
  <aside class="sidebar">
    <div class="brand">
      <span class="logo">🎬</span>
      <div>
        <div class="title">Movie Agent Lab</div>
        <div class="subtitle muted">AI-native 推荐实验平台</div>
      </div>
    </div>

    <nav>
      <button
        v-for="item in nav"
        :key="item.path"
        class="nav-item"
        :class="{ active: $route.path === item.path }"
        @click="go(item.path)"
      >
        <span class="icon">{{ item.icon }}</span>{{ item.label }}
      </button>
    </nav>

    <div class="account">
      <div v-if="auth.token" class="muted">已登录：{{ auth.userName }}</div>
      <div v-else class="muted">未登录</div>
      <button class="btn" style="width: 100%; margin-top: 8px" @click="handleAuth">
        {{ auth.token ? "退出登录" : "登录 / 注册" }}
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 240px;
  flex-shrink: 0;
  background: var(--bg-soft);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 18px 14px;
  height: 100%;
}
.brand {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 24px;
}
.logo {
  font-size: 28px;
}
.title {
  font-weight: 700;
}
.subtitle {
  font-size: 11px;
}
nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  border: none;
  background: transparent;
  color: var(--text-dim);
  padding: 11px 14px;
  border-radius: 8px;
  text-align: left;
  font-size: 14px;
}
.nav-item:hover {
  background: var(--bg-card);
  color: var(--text);
}
.nav-item.active {
  background: var(--accent);
  color: #fff;
}
.icon {
  font-size: 16px;
}
.account {
  border-top: 1px solid var(--border);
  padding-top: 14px;
}
</style>
