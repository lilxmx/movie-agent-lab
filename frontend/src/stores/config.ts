import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "@/api";
import type { ClientConfig } from "@/types";

const FALLBACK: ClientConfig = {
  poster_cdn: "http://127.0.0.1/posters/",
  poster_bg_cdn: "http://127.0.0.1/poster_background/",
  cast_poster_cdn: "http://127.0.0.1/cast_poster/",
  rec_modes: ["hot", "similar", "personalized", "agent"],
};

export const useConfigStore = defineStore("config", () => {
  const config = ref<ClientConfig>(FALLBACK);
  const loaded = ref(false);

  async function load() {
    if (loaded.value) return;
    try {
      config.value = await api.clientConfig();
    } catch {
      config.value = FALLBACK;
    }
    loaded.value = true;
  }

  const posterUrl = (movieId: number) => `${config.value.poster_cdn}${movieId}.jpg`;
  const posterBgUrl = (movieId: number) => `${config.value.poster_bg_cdn}${movieId}.jpg`;
  const castUrl = (actorId: number) => `${config.value.cast_poster_cdn}${actorId}.jpg`;

  return { config, load, posterUrl, posterBgUrl, castUrl };
});
