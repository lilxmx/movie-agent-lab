import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

// 页面优先级（见 recode.md）：ChatRecommend > HomeRecommendation > MovieDetail > ...
const routes: RouteRecordRaw[] = [
  { path: "/", redirect: "/chat" },
  {
    path: "/chat",
    name: "ChatRecommend",
    component: () => import("@/pages/ChatRecommend/ChatRecommend.vue"),
    meta: { title: "对话推荐" },
  },
  {
    path: "/home",
    name: "HomeRecommendation",
    component: () => import("@/pages/HomeRecommendation/HomeRecommendation.vue"),
    meta: { title: "推荐首页" },
  },
  {
    path: "/movie/:id",
    name: "MovieDetail",
    component: () => import("@/pages/MovieDetail/MovieDetail.vue"),
    meta: { title: "电影详情" },
  },
  {
    path: "/memory",
    name: "AgentMemory",
    component: () => import("@/pages/AgentMemory/AgentMemory.vue"),
    meta: { title: "Agent Memory" },
  },
  {
    path: "/knowledge",
    name: "KnowledgeBase",
    component: () => import("@/pages/KnowledgeBase/KnowledgeBase.vue"),
    meta: { title: "知识库" },
  },
  {
    path: "/eval",
    name: "EvalSandbox",
    component: () => import("@/pages/EvalSandbox/EvalSandbox.vue"),
    meta: { title: "评测沙箱" },
  },
  {
    path: "/login",
    name: "Login",
    component: () => import("@/pages/Auth/Login.vue"),
    meta: { title: "登录", hideLayout: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.afterEach((to) => {
  document.title = `${(to.meta.title as string) || "Movie Agent Lab"} - Movie Agent Lab`;
});

export default router;
