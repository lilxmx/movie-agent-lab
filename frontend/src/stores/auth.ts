import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "@/api";

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string>(localStorage.getItem("token") || "");
  const userId = ref<number>(Number(localStorage.getItem("userId")) || 0);
  const userName = ref<string>(localStorage.getItem("userName") || "");

  function persist(t: string, id: number, name: string) {
    token.value = t;
    userId.value = id;
    userName.value = name;
    localStorage.setItem("token", t);
    localStorage.setItem("userId", String(id));
    localStorage.setItem("userName", name);
  }

  async function login(name: string, password: string) {
    const res = await api.login(name, password);
    persist(res.access_token, res.user_id, res.user_name);
  }

  async function register(name: string, password: string) {
    const res = await api.register(name, password);
    persist(res.access_token, res.user_id, res.user_name);
  }

  function logout() {
    persist("", 0, "");
    localStorage.clear();
  }

  return { token, userId, userName, login, register, logout };
});
