<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();

const isRegister = ref(false);
const userName = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

async function submit() {
  error.value = "";
  if (!userName.value || !password.value) {
    error.value = "请输入用户名和密码";
    return;
  }
  loading.value = true;
  try {
    if (isRegister.value) {
      await auth.register(userName.value, password.value);
    } else {
      await auth.login(userName.value, password.value);
    }
    router.push("/chat");
  } catch (e) {
    error.value = (e as Error).message || "操作失败";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-wrap">
    <div class="card login-box">
      <div class="brand">🎬 Movie Agent Lab</div>
      <h2>{{ isRegister ? "注册" : "登录" }}</h2>
      <input v-model="userName" placeholder="用户名" />
      <input v-model="password" type="password" placeholder="密码" @keydown.enter="submit" />
      <div v-if="error" class="error">{{ error }}</div>
      <button class="btn btn-primary submit" :disabled="loading" @click="submit">
        {{ loading ? "处理中…" : isRegister ? "注册" : "登录" }}
      </button>
      <div class="switch muted">
        {{ isRegister ? "已有账号？" : "还没有账号？" }}
        <a @click="isRegister = !isRegister">{{ isRegister ? "去登录" : "去注册" }}</a>
      </div>
      <div class="skip muted"><a @click="router.push('/chat')">游客进入</a></div>
    </div>
  </div>
</template>

<style scoped>
.login-wrap {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-box {
  width: 340px;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.brand {
  font-size: 18px;
  font-weight: 700;
}
.login-box h2 {
  margin: 4px 0 8px;
}
.submit {
  margin-top: 8px;
}
.error {
  color: var(--danger);
  font-size: 13px;
}
.switch,
.skip {
  font-size: 13px;
  text-align: center;
}
.switch a,
.skip a {
  color: var(--accent);
  cursor: pointer;
}
</style>
