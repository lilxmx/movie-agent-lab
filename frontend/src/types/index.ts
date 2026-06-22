export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T | null;
}

export interface Paged<T> {
  items: T[];
  total: number;
}

export interface MovieBrief {
  movie_id: number;
  movie_name: string;
  movie_genres?: string | null;
  movie_released_year?: string | null;
  movie_avg_rating?: number | null;
}

export interface MovieDetail {
  movie_id: number;
  movie_name: string;
  movie_genres?: string | null;
  movie_released_year?: string | null;
  movie_summary?: string | null;
  movie_avg_rating?: number | null;
}

export interface ActorBrief {
  actor_id: number;
  actor_name: string;
}

export interface CommentBrief {
  comment_id: number;
  parent_id: number;
  user_name?: string | null;
  comment_title?: string | null;
  comment_info?: string | null;
  like_num: number;
}

export interface RecItem {
  movie_id: number;
  title: string;
  score: number;
  reason: string;
  source: string;
}

export interface RecResult {
  mode: string;
  trace_id: string;
  items: RecItem[];
}

export interface LoginResult {
  access_token: string;
  token_type: string;
  user_id: number;
  user_name: string;
  rating_num: number;
}

export interface ClientConfig {
  poster_cdn: string;
  poster_bg_cdn: string;
  cast_poster_cdn: string;
  rec_modes: string[];
}

export interface ChatReply {
  session_id: string;
  reply: string;
  recommendations: RecItem[];
}

export interface ChatMessage {
  role: string;
  content: string;
  extra_data?: string | null;
  created_at?: string | null;
}

export interface SessionInfo {
  session_id: string;
  title?: string | null;
  mode: string;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface QuizQuestion {
  question_id: number;
  question_info: string;
  option_a?: string | null;
  option_b?: string | null;
  option_c?: string | null;
  option_d?: string | null;
}

export interface UserProfile {
  user_id: number;
  like_genres: string[];
  rating_count: number;
  avg_rating?: number | null;
  avg_released_year?: number | null;
  recent_scans: number[];
  memories: { type: string; content: string }[];
}
