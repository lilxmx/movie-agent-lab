<script setup lang="ts">
import { onMounted } from "vue";
import { useRoute } from "vue-router";
import AppSidebar from "@/components/AppSidebar.vue";
import { useConfigStore } from "@/stores/config";

const route = useRoute();
const configStore = useConfigStore();

onMounted(() => configStore.load());
</script>

<template>
  <div v-if="route.meta.hideLayout">
    <router-view />
  </div>
  <div v-else class="layout">
    <AppSidebar />
    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  height: 100%;
}
.content {
  flex: 1;
  overflow-y: auto;
  height: 100%;
}
</style>
