<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { api } from "@/api";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import MoviePoster from "@/components/MoviePoster.vue";
import RecCard from "@/components/RecCard.vue";
import QuizModal from "@/components/QuizModal.vue";
import type { ActorBrief, CommentBrief, MovieDetail, QuizQuestion, RecItem } from "@/types";

const route = useRoute();
const auth = useAuthStore();
const configStore = useConfigStore();

const movie = ref<MovieDetail | null>(null);
const cast = ref<ActorBrief[]>([]);
const similar = ref<RecItem[]>([]);
const comments = ref<CommentBrief[]>([]);
const myRating = ref(0);
const collected = ref(false);
const newComment = ref("");

// 答题弹窗状态
const quizVisible = ref(false);
const quizQuestion = ref<QuizQuestion | null>(null);
const quizLoading = ref(false);
const pendingRating = ref(0);

function genres(): string[] {
  return (movie.value?.movie_genres || "").split("|").filter(Boolean);
}

async function loadAll(id: number) {
  movie.value = await api.movieDetail(id);
  cast.value = await api.movieCast(id).catch(() => []);
  comments.value = await api.comments(id).catch(() => []);
  similar.value = (await api.recommendClassic("similar", 8, id).catch(() => null))?.items ?? [];
  if (auth.token) {
    myRating.value = await api.myRating(id).catch(() => 0);
    collected.value = await api.isCollected(id).catch(() => false);
  }
}

async function rate(value: number) {
  if (!movie.value || !auth.token) return;
  const movieId = movie.value.movie_id;

  // 检查是否有评分资格
  const qualified = await api.ratingQualified(movieId).catch(() => false);
  if (qualified) {
    await doRate(movieId, value);
    return;
  }

  // 先弹窗显示"出题中"，再异步拉题
  pendingRating.value = value;
  quizQuestion.value = null;
  quizLoading.value = true;
  quizVisible.value = true;

  try {
    const questions = await api.quizQuestions(movieId, 1).catch(() => [] as QuizQuestion[]);
    if (!questions.length) {
      // 该电影没有题目，直接允许评分
      quizVisible.value = false;
      await doRate(movieId, value);
      return;
    }
    quizQuestion.value = questions[0];
  } finally {
    quizLoading.value = false;
  }
}

async function doRate(movieId: number, value: number) {
  await api.rateMovie(movieId, value);
  myRating.value = value;
}

// 答题通过：关闭弹窗，执行评分
async function onQuizPass() {
  quizVisible.value = false;
  if (movie.value) {
    await doRate(movie.value.movie_id, pendingRating.value);
  }
  quizQuestion.value = null;
}

function onQuizClose() {
  quizVisible.value = false;
  quizQuestion.value = null;
  quizLoading.value = false;
  pendingRating.value = 0;
}

async function toggleCollect() {
  if (!movie.value || !auth.token) return;
  await api.toggleCollect(movie.value.movie_id);
  collected.value = !collected.value;
}

async function submitComment() {
  const text = newComment.value.trim();
  if (!text || !movie.value || !auth.token) return;
  await api.addComment(movie.value.movie_id, text);
  newComment.value = "";
  comments.value = await api.comments(movie.value.movie_id);
}

onMounted(() => loadAll(Number(route.params.id)));
watch(
  () => route.params.id,
  (id) => id && loadAll(Number(id)),
);
</script>

<template>
  <div v-if="movie" class="detail">
    <div
      class="hero"
      :style="{ backgroundImage: `url(${configStore.posterBgUrl(movie.movie_id)})` }"
    >
      <div class="hero-mask">
        <div class="hero-inner">
          <div class="poster-wrap">
            <MoviePoster :movie-id="movie.movie_id" :title="movie.movie_name" />
          </div>
          <div class="meta">
            <h1>{{ movie.movie_name }} <span class="muted">({{ movie.movie_released_year }})</span></h1>
            <div class="rating-line">
              <span class="big-score">{{ movie.movie_avg_rating ?? "-" }}</span>
              <button class="btn" @click="toggleCollect">
                {{ collected ? "已收藏 ★" : "收藏 ☆" }}
              </button>
            </div>
            <div class="genres">
              <span v-for="g in genres()" :key="g" class="tag">{{ g }}</span>
            </div>
            <div class="my-rating">
              <span class="muted">我的评分：</span>
              <button
                v-for="n in 5"
                :key="n"
                class="star"
                :class="{ on: n <= myRating }"
                @click="rate(n)"
              >
                ★
              </button>
            </div>
            <p class="summary">{{ movie.movie_summary || "暂无简介" }}</p>
          </div>
        </div>
      </div>
    </div>

    <section class="block">
      <h3>演员</h3>
      <div class="cast">
        <div v-for="a in cast.slice(0, 8)" :key="a.actor_id" class="actor">
          <img
            :src="configStore.castUrl(a.actor_id)"
            :alt="a.actor_name"
            @error="(e) => ((e.target as HTMLImageElement).style.visibility = 'hidden')"
          />
          <div class="small">{{ a.actor_name }}</div>
        </div>
        <div v-if="!cast.length" class="muted">暂无演员信息</div>
      </div>
    </section>

    <section class="block">
      <h3>评论</h3>
      <div v-if="auth.token" class="comment-input">
        <input v-model="newComment" placeholder="说点什么…" @keydown.enter="submitComment" />
        <button class="btn btn-primary" @click="submitComment">发表</button>
      </div>
      <div v-for="c in comments" :key="c.comment_id" class="comment card">
        <div class="comment-head">
          <strong>{{ c.user_name || "匿名" }}</strong>
          <span class="muted small">👍 {{ c.like_num }}</span>
        </div>
        <div>{{ c.comment_info }}</div>
      </div>
      <div v-if="!comments.length" class="muted">暂无评论</div>
    </section>

    <section class="block">
      <h3>相似电影</h3>
      <div class="grid">
        <RecCard v-for="item in similar" :key="item.movie_id" :item="item" />
      </div>
      <div v-if="!similar.length" class="muted">暂无相似推荐</div>
    </section>
  </div>
  <div v-else class="muted" style="padding: 24px">加载中…</div>

  <!-- 答题资格弹窗 -->
  <QuizModal
    v-if="quizVisible && movie"
    :movie-id="movie.movie_id"
    :question="quizQuestion"
    :loading="quizLoading"
    @pass="onQuizPass"
    @close="onQuizClose"
  />
</template>

<style scoped>
.hero {
  background-size: cover;
  background-position: center;
}
.hero-mask {
  background: linear-gradient(to right, rgba(15, 19, 32, 0.96), rgba(15, 19, 32, 0.78));
  padding: 32px 24px;
}
.hero-inner {
  display: flex;
  gap: 24px;
}
.poster-wrap {
  width: 200px;
  flex-shrink: 0;
}
.meta h1 {
  margin: 0 0 12px;
}
.rating-line {
  display: flex;
  align-items: center;
  gap: 16px;
}
.big-score {
  font-size: 32px;
  font-weight: 700;
  color: var(--accent-2);
}
.genres {
  margin: 12px 0;
}
.my-rating {
  margin-bottom: 12px;
}
.star {
  border: none;
  background: transparent;
  color: var(--border);
  font-size: 22px;
  padding: 0 2px;
}
.star.on {
  color: #ffc83d;
}
.summary {
  max-width: 640px;
  line-height: 1.6;
  color: var(--text-dim);
}
.block {
  padding: 24px;
}
.cast {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.actor {
  width: 90px;
  text-align: center;
}
.actor img {
  width: 90px;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
  background: var(--bg-soft);
}
.comment-input {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.comment-input input {
  flex: 1;
}
.comment {
  padding: 12px 16px;
  margin-bottom: 10px;
}
.comment-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 14px;
}
.small {
  font-size: 12px;
}
</style>
