export const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  (process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL.replace(/\/api\/v1\/?$/, "")
    : "http://127.0.0.1:8000");

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || `${BACKEND_URL}/api/v1`;

export const getThumbnailUrl = (shortId: string) => `${BACKEND_URL}/static/thumbnails/${shortId}.jpg`;
export const getShortVideoUrl = (shortId: string) => `${BACKEND_URL}/static/shorts/${shortId}.mp4`;
export const getOAuthConnectUrl = () => `${API_BASE}/channels/oauth/connect`;

export interface SystemHealth {
  status: string;
  hardware: {
    os: { system: string; release: string; machine: string };
    cpu: { model: string; physical_cores: number; logical_threads: number; utilization_percent: number };
    ram: { total_mb: number; available_mb: number; used_percent: number; pressure_state: string };
    gpu: { name: string; is_integrated: boolean; dedicated_vram_mb: number; shared_pool_mb: number };
    video_acceleration: { name: string; type: string; preset?: string };
  };
  queue: {
    active_count: number;
    cancelled_count: number;
    jobs: Array<{ id: string; status: string; progress: number; is_heavy: boolean; error?: string }>;
  };
}

export interface YouTubeChannel {
  id: string;
  channel_id: string;
  title: string;
  custom_url?: string;
  thumbnail_url?: string;
  subscriber_count: number;
  video_count: number;
  is_authorized: boolean;
  created_at: string;
}

export interface DownloadProgress {
  status: string;
  percent: number;
  remaining_percent: number;
  speed: string;
  eta: number;
  downloaded_mb: number;
  total_mb: number;
}

export interface SourceVideo {
  id: string;
  channel_id?: string;
  youtube_video_id?: string;
  title: string;
  description?: string;
  duration_seconds: number;
  width: number;
  height: number;
  fps: number;
  codec_video?: string;
  codec_audio?: string;
  proxy_path?: string;
  audio_path?: string;
  source_status: string;
  analysis_status: string;
  created_at: string;
  download_progress?: DownloadProgress;
}

export interface ChannelVideoEntry {
  id: string;
  title: string;
  url: string;
  duration_seconds: number;
  duration_formatted: string;
  thumbnail_url: string;
  view_count?: number;
}

export interface ExploreChannelResponse {
  channel_name: string;
  channel_url: string;
  total_found: number;
  videos: ChannelVideoEntry[];
}

export interface ActiveAnalysisStatus {
  has_active: boolean;
  is_downloading?: boolean;
  is_recently_completed?: boolean;
  job_id?: string;
  video_id?: string;
  video_title?: string;
  status?: string;
  current_step?: string;
  progress_percent?: number;
  remaining_percent?: number;
  speed?: string;
  eta?: number;
  downloaded_mb?: number;
  total_mb?: number;
  elapsed_seconds?: number;
  estimated_remaining_seconds?: number;
}

export interface EngagementCandidate {
  id: string;
  source_video_id: string;
  start_time: number;
  end_time: number;
  duration: number;
  overall_score: number;
  scoring_mode: string;
  confidence: number;
  hook_score: number;
  payoff_score: number;
  emotional_score: number;
  topic_score: number;
  visual_score: number;
  retention_signal_score?: number;
  reasons: string[];
}

export interface ClipProject {
  id: string;
  candidate_id?: string;
  source_video_id: string;
  title: string;
  start_time: number;
  end_time: number;
  caption_style: string;
  framing_mode: string;
  rendered_video_path?: string;
  thumbnail_path?: string;
  status: string;
  metadata?: {
    title_options: string[];
    recommended_title: string;
    description: string;
    hashtags: string[];
    keywords: string[];
    suggested_category: string;
    suggested_publishing_time: string;
  };
  created_at: string;
}

export interface QCReport {
  id: string;
  clip_project_id: string;
  passed: boolean;
  overall_score: number;
  video_checks: Record<string, any>;
  audio_checks: Record<string, any>;
  caption_checks: Record<string, any>;
  framing_checks: Record<string, any>;
  repaired: boolean;
  created_at: string;
}

export const api = {
  // System Health
  async getSystemHealth(): Promise<SystemHealth> {
    const res = await fetch(`${API_BASE}/system/health`);
    return res.json();
  },

  // Channels
  async listChannels(): Promise<YouTubeChannel[]> {
    const res = await fetch(`${API_BASE}/channels`);
    return res.json();
  },
  async getAuthUrl(): Promise<{ authorization_url: string; state: string }> {
    const res = await fetch(`${API_BASE}/channels/oauth/authorize`);
    return res.json();
  },
  async revokeChannel(channelId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/channels/${channelId}/revoke`, { method: "POST" });
    return res.json();
  },

  // Source Videos
  async listVideos(): Promise<SourceVideo[]> {
    const res = await fetch(`${API_BASE}/videos`);
    return res.json();
  },
  async uploadVideo(file: File, title: string, sourceStatus: string = "owned"): Promise<SourceVideo> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", title);
    formData.append("source_status", sourceStatus);
    const res = await fetch(`${API_BASE}/videos/upload`, {
      method: "POST",
      body: formData,
    });
    return res.json();
  },
  async exploreChannel(channelUrl: string, maxResults: number = 10): Promise<ExploreChannelResponse> {
    const res = await fetch(`${API_BASE}/videos/explore-channel`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ channel_url: channelUrl, max_results: maxResults }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to connect to backend" }));
      throw new Error(err.detail || "Failed to explore channel");
    }
    return res.json();
  },
  async importYouTubeVideo(url: string, autoAnalyze: boolean = true): Promise<SourceVideo> {
    const res = await fetch(`${API_BASE}/videos/import-youtube`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, auto_analyze: autoAnalyze }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to connect to backend" }));
      throw new Error(err.detail || "Failed to import video");
    }
    return res.json();
  },

  // Analysis
  async getActiveAnalysis(): Promise<ActiveAnalysisStatus> {
    const res = await fetch(`${API_BASE}/analysis/active`);
    return res.json();
  },
  async startAnalysis(videoId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/analysis/${videoId}/start`, { method: "POST" });
    return res.json();
  },
  async getAnalysisStatus(videoId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/analysis/${videoId}/status`);
    return res.json();
  },
  async getAnalysisResults(videoId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/analysis/${videoId}/results`);
    return res.json();
  },

  // Candidates & Engagement
  async getCandidates(videoId: string): Promise<EngagementCandidate[]> {
    const res = await fetch(`${API_BASE}/engagement/${videoId}/candidates`);
    return res.json();
  },

  // Shorts Projects
  async listShorts(): Promise<ClipProject[]> {
    const res = await fetch(`${API_BASE}/shorts`);
    return res.json();
  },
  async generateShort(data: {
    source_video_id: string;
    candidate_id?: string;
    title: string;
    start_time: number;
    end_time: number;
    caption_style?: string;
    framing_mode?: string;
  }): Promise<ClipProject> {
    const res = await fetch(`${API_BASE}/shorts/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return res.json();
  },
  async getShortDetail(shortId: string): Promise<ClipProject> {
    const res = await fetch(`${API_BASE}/shorts/${shortId}`);
    return res.json();
  },
  async getQCReport(shortId: string): Promise<QCReport> {
    const res = await fetch(`${API_BASE}/shorts/${shortId}/qc`);
    return res.json();
  },
  async approveShort(shortId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/shorts/${shortId}/approve`, { method: "POST" });
    return res.json();
  },

  // Publishing
  async publishShort(data: {
    clip_project_id: string;
    channel_id: string;
    mode: "SAFE" | "AUTOMATIC";
    privacy_status: "private" | "unlisted" | "public";
  }): Promise<any> {
    const res = await fetch(`${API_BASE}/publishing/publish`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return res.json();
  },
  async getPublishQueue(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/publishing/queue`);
    return res.json();
  },

  // Analytics & Learning
  async getChannelAnalytics(channelId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/analytics/channel/${channelId}/summary`);
    return res.json();
  },
  async getChannelInsights(channelId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/analytics/channel/${channelId}/insights`);
    return res.json();
  },
};
