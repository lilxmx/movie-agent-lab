<script setup lang="ts">
import type { QuizQuestion } from "@/types";

const props = defineProps<{
  movieId: number;
  question: QuizQuestion | null;
  loading?: boolean;
}>();

const emit = defineEmits<{
  (e: "pass"): void;
  (e: "fail"): void;
  (e: "close"): void;
}>();

import { ref } from "vue";
import { api } from "@/api";

const OPTIONS = [
  { key: 1, label: "A", textKey: "option_a" as const },
  { key: 2, label: "B", textKey: "option_b" as const },
  { key: 3, label: "C", textKey: "option_c" as const },
  { key: 4, label: "D", textKey: "option_d" as const },
];

const selected = ref<number | null>(null);
const result = ref<"correct" | "wrong" | null>(null);
const loading = ref(false);

async function choose(answer: number) {
  if (!props.question || result.value !== null || loading.value) return;
  selected.value = answer;
  loading.value = true;
  try {
    const res = await api.submitAnswer(props.movieId, props.question.question_id, answer);
    result.value = res.correct ? "correct" : "wrong";
    if (res.correct) {
      setTimeout(() => emit("pass"), 800);
    }
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="overlay" @click.self="emit('close')">
    <div class="modal card">
      <div class="modal-head">
        <span>评分资格认证</span>
        <button class="close-btn" @click="emit('close')">✕</button>
      </div>

      <div v-if="loading || !question" class="loading-box">
        <div class="spinner"></div>
        <div class="loading-text">AI 正在为这部电影生成题目…</div>
        <div class="loading-hint">题目考察你是否真的看过此片，通常需要几秒</div>
      </div>

      <template v-else>
        <p class="question">{{ question.question_info }}</p>

        <div class="options">
          <button
            v-for="opt in OPTIONS"
            :key="opt.key"
            class="opt-btn"
            :class="{
              selected: selected === opt.key && result === null,
              correct: selected === opt.key && result === 'correct',
              wrong: selected === opt.key && result === 'wrong',
              disabled: result !== null && selected !== opt.key,
            }"
            :disabled="result !== null"
            @click="choose(opt.key)"
          >
            <span class="opt-label">{{ opt.label }}</span>
            <span class="opt-text">{{ question[opt.textKey] }}</span>
          </button>
        </div>

        <div v-if="result === 'correct'" class="feedback correct-msg">
          ✓ 回答正确，获得评分资格！
        </div>
        <div v-else-if="result === 'wrong'" class="feedback wrong-msg">
          ✗ 回答有误，本次未获得评分资格。
          <button class="btn" style="margin-top: 10px" @click="emit('close')">关闭</button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  width: 480px;
  max-width: 92vw;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 15px;
}
.close-btn {
  border: none;
  background: transparent;
  color: var(--text-dim);
  font-size: 16px;
  cursor: pointer;
  padding: 4px 8px;
}
.question {
  font-size: 15px;
  line-height: 1.6;
  margin: 0;
}
.options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.opt-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-card);
  color: var(--text);
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, background 0.15s;
  font-size: 14px;
}
.opt-btn:hover:not(:disabled) {
  border-color: var(--accent);
}
.opt-btn.selected {
  border-color: var(--accent);
  background: rgba(56, 189, 248, 0.08);
}
.opt-btn.correct {
  border-color: var(--accent-2);
  background: rgba(56, 211, 159, 0.12);
  color: var(--accent-2);
}
.opt-btn.wrong {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}
.opt-btn.disabled {
  opacity: 0.4;
  cursor: default;
}
.opt-label {
  font-weight: 700;
  font-size: 14px;
  color: var(--accent);
  min-width: 18px;
}
.opt-btn.correct .opt-label,
.opt-btn.correct .opt-text {
  color: var(--accent-2);
}
.opt-btn.wrong .opt-label,
.opt-btn.wrong .opt-text {
  color: #ef4444;
}
.feedback {
  font-size: 14px;
  padding: 10px 14px;
  border-radius: 8px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.correct-msg {
  background: rgba(56, 211, 159, 0.12);
  color: var(--accent-2);
}
.wrong-msg {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
}
.loading-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px 0;
}
.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}
.loading-text {
  font-size: 14px;
  color: var(--text);
}
.loading-hint {
  font-size: 12px;
  color: var(--text-dim);
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
