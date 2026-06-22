<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "@/api";
import { useAuthStore } from "@/stores/auth";
import RecCard from "@/components/RecCard.vue";
import type { ChatMessage, RecItem, SessionInfo, UserProfile } from "@/types";

const auth = useAuthStore();
const sessionId = ref("");
const messages = ref<ChatMessage[]>([]);
const recommendations = ref<RecItem[]>([]);
const profile = ref<UserProfile | null>(null);
const input = ref("");
const loading = ref(false);
const chatBody = ref<HTMLElement | null>(null);

// 会话历史列表
const sessions = ref<SessionInfo[]>([]);

// Agent 推理步骤（流式）
const agentSteps = ref<string[]>([]);
const showSteps = ref(false);

// SSE 需要直接拼完整 URL，从 baseURL 里去掉 /api/v1 后缀得到纯 host
const _rawBase: string = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const API_HOST = _rawBase.replace(/\/api\/v1\/?$/, "");

async function loadSessions() {
  if (!auth.userId) return;
  try {
    sessions.value = await api.listSessions();
  } catch {
    sessions.value = [];
  }
}

async function newSession() {
  const s = await api.createSession("新对话");
  sessionId.value = s.session_id;
  messages.value = [
    { role: "assistant", content: "你好，告诉我你想看什么样的电影吧，例如「轻松治愈的科幻片」。" },
  ];
  recommendations.value = [];
  await loadSessions();
}

async function switchSession(sid: string) {
  if (sid === sessionId.value || loading.value) return;
  sessionId.value = sid;
  try {
    const msgs = await api.sessionMessages(sid);
    messages.value = msgs.length
      ? msgs
      : [{ role: "assistant", content: "你好，告诉我你想看什么样的电影吧，例如「轻松治愈的科幻片」。" }];
  } catch {
    messages.value = [];
  }
  recommendations.value = restoreRecommendations(messages.value);
  scrollToBottom();
}

function restoreRecommendations(msgs: ChatMessage[]): RecItem[] {
  for (let i = msgs.length - 1; i >= 0; i--) {
    const m = msgs[i];
    if (m.role === "assistant" && m.extra_data) {
      try {
        return JSON.parse(m.extra_data) as RecItem[];
      } catch {
        // ignore
      }
    }
  }
  return [];
}

async function removeSession(sid: string) {
  if (!confirm("确定删除该会话吗？")) return;
  try {
    await api.deleteSession(sid);
    if (sid === sessionId.value) {
      const remaining = sessions.value.filter((s) => s.session_id !== sid);
      if (remaining.length) {
        await switchSession(remaining[0].session_id);
      } else {
        await newSession();
      }
    }
    await loadSessions();
  } catch {
    // ignore
  }
}

async function loadProfile() {
  if (!auth.userId) return;
  try {
    profile.value = await api.profile(auth.userId);
  } catch {
    profile.value = null;
  }
}

async function send() {
  const text = input.value.trim();
  if (!text || loading.value || !sessionId.value) return;

  messages.value.push({ role: "user", content: text });
  input.value = "";
  loading.value = true;
  agentSteps.value = [];
  showSteps.value = true;
  scrollToBottom();

  try {
    await sendWithStream(text);
    await loadSessions();
  } catch {
    messages.value.push({ role: "assistant", content: "抱歉，服务暂时不可用，请稍后再试。" });
  } finally {
    loading.value = false;
    showSteps.value = false;
    scrollToBottom();
  }
}

async function sendWithStream(text: string) {
  const token = auth.token ? `Bearer ${auth.token}` : "";
  const res = await fetch(
    `${API_HOST}/api/v1/chat/sessions/${sessionId.value}/messages/stream`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: token } : {}),
      },
      body: JSON.stringify({ content: text }),
    }
  );

  if (!res.ok || !res.body) {
    throw new Error(`HTTP ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data:")) continue;
      const payload = line.slice(5).trim();
      if (payload === "[DONE]") continue;

      try {
        const event = JSON.parse(payload);
        handleEvent(event);
      } catch {
        // 忽略解析失败的行
      }
    }
  }
}

function handleEvent(event: { type: string; message: string; data?: any }) {
  if (event.type === "step" || event.type === "tool") {
    agentSteps.value.push(event.message);
    scrollToBottom();
  } else if (event.type === "result") {
    const d = event.data;
    if (d?.reply) {
      messages.value.push({ role: "assistant", content: d.reply });
    }
    if (d?.recommendations) {
      recommendations.value = d.recommendations;
    }
  }
}

function scrollToBottom() {
  requestAnimationFrame(() => {
    if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight;
  });
}

function formatTime(iso?: string | null) {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000);
  if (diffDays === 0) return d.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  if (diffDays === 1) return "昨天";
  if (diffDays < 7) return `${diffDays}天前`;
  return d.toLocaleDateString("zh-CN", { month: "numeric", day: "numeric" });
}

onMounted(async () => {
  await loadSessions();
  if (sessions.value.length) {
    await switchSession(sessions.value[0].session_id);
  } else {
    await newSession();
  }
  await loadProfile();
});
</script>

<template>
  <div class="chat-layout">
    <!-- 左栏：会话历史 + 用户画像 -->
    <section class="col left card">
      <!-- 会话历史 -->
      <div class="section-header">
        <span class="section-title">历史会话</span>
        <button class="btn-new" :disabled="loading" @click="newSession">+ 新对话</button>
      </div>
      <div v-if="auth.userId" class="session-list">
        <div
          v-for="s in sessions"
          :key="s.session_id"
          class="session-item"
          :class="{ active: s.session_id === sessionId }"
          @click="switchSession(s.session_id)"
        >
          <div class="session-title">{{ s.title || "新对话" }}</div>
          <div class="session-meta">
            <span class="session-time">{{ formatTime(s.updated_at) }}</span>
            <button
              class="btn-del"
              title="删除"
              @click.stop="removeSession(s.session_id)"
            >×</button>
          </div>
        </div>
        <div v-if="!sessions.length" class="muted small">暂无历史会话</div>
      </div>
      <div v-else class="muted small">登录后可查看历史会话。</div>

      <!-- 用户画像 -->
      <div class="block-title" style="margin-top:18px">我的画像</div>
      <template v-if="profile">
        <div class="muted small">评分数 {{ profile.rating_count }} · 平均分 {{ profile.avg_rating ?? "-" }}</div>
        <div class="block-title">偏好标签</div>
        <div>
          <span v-for="g in profile.like_genres" :key="g" class="tag">{{ g }}</span>
          <span v-if="!profile.like_genres.length" class="muted small">暂无</span>
        </div>
        <div class="block-title">长期记忆</div>
        <div v-if="profile.memories.length">
          <div v-for="(m, i) in profile.memories" :key="i" class="memo small">{{ m.content }}</div>
        </div>
        <div v-else class="muted small">暂无记忆</div>
      </template>
      <div v-else-if="!auth.userId" class="muted small">登录后可查看个性化画像与记忆。</div>
    </section>

    <!-- 中栏：主对话窗口 -->
    <section class="col center card">
      <div class="chat-header">对话推荐</div>
      <div ref="chatBody" class="chat-body">
        <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
          <div class="bubble">{{ m.content }}</div>
        </div>

        <!-- Agent 推理过程（流式） -->
        <div v-if="showSteps" class="msg assistant">
          <div class="bubble thinking">
            <div class="thinking-title">🤖 Agent 推理中</div>
            <div v-for="(step, i) in agentSteps" :key="i" class="step-line">{{ step }}</div>
            <div class="blink-cursor" />
          </div>
        </div>
      </div>

      <div class="chat-input">
        <input
          v-model="input"
          placeholder="描述你的观影需求，回车发送"
          :disabled="loading"
          @keydown.enter="send"
        />
        <button class="btn btn-primary" :disabled="loading" @click="send">
          {{ loading ? "思考中…" : "发送" }}
        </button>
      </div>
    </section>

    <!-- 右栏：推荐卡片 -->
    <section class="col right card">
      <h3>为你推荐</h3>
      <div v-if="recommendations.length" class="rec-list">
        <RecCard v-for="item in recommendations" :key="item.movie_id" :item="item" />
      </div>
      <div v-else class="muted small">对话后将在此展示推荐电影与理由。</div>
    </section>
  </div>
</template>

<style scoped>
.chat-layout {
  display: grid;
  grid-template-columns: 260px 1fr 320px;
  gap: 14px;
  padding: 16px;
  height: 100%;
}
.col {
  padding: 16px;
  overflow-y: auto;
}
.col h3 {
  margin: 0 0 10px;
}
.center {
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}
.chat-header {
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
  font-weight: 600;
}
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.msg {
  display: flex;
}
.msg.user {
  justify-content: flex-end;
}
.bubble {
  max-width: 78%;
  padding: 10px 14px;
  border-radius: 12px;
  line-height: 1.5;
  background: var(--bg-soft);
}
.msg.user .bubble {
  background: var(--accent);
  color: #fff;
}

/* Agent 推理气泡 */
.bubble.thinking {
  background: #f0f4ff;
  border: 1px solid #d0daff;
  font-size: 13px;
  max-width: 92%;
  padding: 12px 16px;
}
.thinking-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: #4a6cf7;
}
.step-line {
  color: #444;
  padding: 2px 0;
  line-height: 1.6;
}
.step-line:nth-child(odd) {
  color: #666;
}
.blink-cursor {
  display: inline-block;
  width: 8px;
  height: 14px;
  background: #4a6cf7;
  margin-top: 6px;
  border-radius: 2px;
  animation: blink 1s infinite;
  vertical-align: middle;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.chat-input {
  display: flex;
  gap: 8px;
  padding: 14px;
  border-top: 1px solid var(--border);
}
.chat-input input {
  flex: 1;
}
.rec-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.block-title {
  margin: 14px 0 6px;
  font-size: 13px;
  font-weight: 600;
}
.small {
  font-size: 12px;
}
.memo {
  background: var(--bg-soft);
  padding: 8px 10px;
  border-radius: 8px;
  margin-bottom: 6px;
  line-height: 1.4;
}

/* 会话列表 */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.section-title {
  font-size: 13px;
  font-weight: 600;
}
.btn-new {
  font-size: 12px;
  padding: 3px 8px;
  border: 1px solid var(--accent);
  border-radius: 6px;
  background: transparent;
  color: var(--accent);
  cursor: pointer;
  transition: background 0.15s;
}
.btn-new:hover:not(:disabled) {
  background: var(--accent);
  color: #fff;
}
.btn-new:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.session-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 220px;
  overflow-y: auto;
}
.session-item {
  padding: 7px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.12s;
  border: 1px solid transparent;
}
.session-item:hover {
  background: var(--bg-soft);
}
.session-item.active {
  background: #eef2ff;
  border-color: #c7d2fe;
}
.session-title {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.session-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 2px;
}
.session-time {
  font-size: 11px;
  color: #999;
}
.btn-del {
  font-size: 14px;
  line-height: 1;
  padding: 0 4px;
  background: transparent;
  border: none;
  color: #bbb;
  cursor: pointer;
  border-radius: 4px;
  transition: color 0.12s;
}
.btn-del:hover {
  color: #e44;
}
</style>
