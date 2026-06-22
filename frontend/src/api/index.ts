import http, { unwrap } from "./http";
import type {
  ActorBrief,
  ChatMessage,
  ChatReply,
  ClientConfig,
  CommentBrief,
  LoginResult,
  MovieBrief,
  MovieDetail,
  Paged,
  QuizQuestion,
  RecResult,
  SessionInfo,
  UserProfile,
} from "@/types";

export const api = {
  // ---- 配置 ----
  clientConfig: () => unwrap<ClientConfig>(http.get("/config/client")),

  // ---- 鉴权 ----
  login: (user_name: string, user_password: string) =>
    unwrap<LoginResult>(http.post("/auth/login", { user_name, user_password })),
  register: (user_name: string, user_password: string) =>
    unwrap<LoginResult>(http.post("/auth/register", { user_name, user_password })),

  // ---- 电影 ----
  listMovies: (page: number, pageSize: number, q = "", type = 0) =>
    unwrap<Paged<MovieBrief>>(
      http.get("/movies", { params: { page, page_size: pageSize, q, type } }),
    ),
  movieDetail: (id: number) => unwrap<MovieDetail>(http.get(`/movies/${id}`)),
  movieCast: (id: number) => unwrap<ActorBrief[]>(http.get(`/movies/${id}/cast`)),
  rateMovie: (id: number, rating: number) =>
    unwrap(http.post(`/movies/${id}/rating`, { movie_rating: rating })),
  myRating: (id: number) => unwrap<number>(http.get(`/movies/${id}/my-rating`)),
  toggleCollect: (id: number) => unwrap<string>(http.post(`/movies/${id}/collect`)),
  isCollected: (id: number) => unwrap<boolean>(http.get(`/movies/${id}/is-collected`)),
  comments: (id: number, parentId = 0) =>
    unwrap<CommentBrief[]>(http.get(`/movies/${id}/comments`, { params: { parent_id: parentId } })),
  addComment: (id: number, info: string, title = "") =>
    unwrap(http.post(`/movies/${id}/comments`, { comment_info: info, comment_title: title })),

  // ---- 答题资格 ----
  ratingQualified: (movieId: number) =>
    unwrap<boolean>(http.get(`/movies/${movieId}/rating-qualified`)),
  quizQuestions: (movieId: number, num = 1) =>
    unwrap<QuizQuestion[]>(http.get(`/movies/${movieId}/quiz`, { params: { num } })),
  submitAnswer: (movieId: number, questionId: number, answer: number) =>
    unwrap<{ correct: boolean }>(
      http.post(`/movies/${movieId}/quiz/submit`, { question_id: questionId, answer }),
    ),

  // ---- 推荐 ----
  recommendClassic: (scene: string, size = 10, movieId?: number) =>
    unwrap<RecResult>(
      http.post("/recommendations/classic", { scene, size, movie_id: movieId ?? null }),
    ),
  recommendAgent: (scene = "personalized", size = 10) =>
    unwrap<RecResult>(http.post("/recommendations/agent", { scene, size })),

  // ---- 对话推荐 ----
  listSessions: () =>
    unwrap<SessionInfo[]>(http.get("/chat/sessions")),
  createSession: (title?: string, mode = "chatbot") =>
    unwrap<SessionInfo>(http.post("/chat/sessions", { title, mode })),
  deleteSession: (sessionId: string) =>
    unwrap(http.delete(`/chat/sessions/${sessionId}`)),
  sessionMessages: (sessionId: string) =>
    unwrap<ChatMessage[]>(http.get(`/chat/sessions/${sessionId}/messages`)),
  sendMessage: (sessionId: string, content: string) =>
    unwrap<ChatReply>(http.post(`/chat/sessions/${sessionId}/messages`, { content })),

  // ---- Memory / 知识库 / 评测 ----
  profile: (userId: number) => unwrap<UserProfile>(http.get(`/memory/profile/${userId}`)),
  knowledgeSearch: (query: string, topK = 5) =>
    unwrap(http.post("/knowledge/search", { query, top_k: topK })),
  coverage: (mode: string) =>
    unwrap(http.get("/eval/metrics/coverage", { params: { mode } })),
};
