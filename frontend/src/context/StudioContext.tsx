"use client";

import React, { createContext, useContext, useState, useEffect, useRef, ReactNode } from "react";
import {
  api,
  SystemHealth,
  YouTubeChannel,
  SourceVideo,
  EngagementCandidate,
  ClipProject,
  QCReport,
  ActiveAnalysisStatus,
  getOAuthConnectUrl,
} from "@/lib/api";

interface StudioContextType {
  health: SystemHealth | null;
  channels: YouTubeChannel[];
  videos: SourceVideo[];
  selectedVideo: SourceVideo | null;
  setSelectedVideo: (v: SourceVideo | null) => void;
  selectedVideoRef: React.MutableRefObject<SourceVideo | null>;
  candidates: EngagementCandidate[];
  setCandidates: React.Dispatch<React.SetStateAction<EngagementCandidate[]>>;
  shorts: ClipProject[];
  setShorts: React.Dispatch<React.SetStateAction<ClipProject[]>>;
  selectedShort: ClipProject | null;
  setSelectedShort: (s: ClipProject | null) => void;
  selectedShortRef: React.MutableRefObject<ClipProject | null>;
  activeQC: QCReport | null;
  setActiveQC: (qc: QCReport | null) => void;
  insights: any;
  analyticsSummary: any;
  loading: boolean;
  setLoading: (l: boolean) => void;
  toast: { msg: string; type: "ok" | "err" } | null;
  showToast: (msg: string, type?: "ok" | "err") => void;
  activeTask: ActiveAnalysisStatus | null;
  selectedLayout: string;
  setSelectedLayout: (l: string) => void;
  selectedStyle: string;
  setSelectedStyle: (s: string) => void;
  shortFilterVideoId: string;
  setShortFilterVideoId: (id: string) => void;
  refreshAll: () => Promise<void>;
  checkActiveTask: () => Promise<void>;
  handleStartAnalysis: (videoId: string) => Promise<void>;
  handleGenerateShort: (cand: EngagementCandidate) => Promise<ClipProject | null>;
  handlePublish: (shortId: string, mode?: "SAFE" | "AUTOMATIC") => Promise<void>;
  handleConnectOAuth: () => void;
  handleImportYtVideo: (videoUrl: string) => Promise<SourceVideo | null>;
  handleUploadVideo: (file: File, title?: string, status?: string) => Promise<SourceVideo | null>;
}

const StudioContext = createContext<StudioContextType | undefined>(undefined);

export function StudioProvider({ children }: { children: ReactNode }) {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [channels, setChannels] = useState<YouTubeChannel[]>([]);
  const [videos, setVideos] = useState<SourceVideo[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<SourceVideo | null>(null);
  const [candidates, setCandidates] = useState<EngagementCandidate[]>([]);
  const [shorts, setShorts] = useState<ClipProject[]>([]);
  const [selectedShort, setSelectedShort] = useState<ClipProject | null>(null);
  const [activeQC, setActiveQC] = useState<QCReport | null>(null);
  const [insights, setInsights] = useState<any>(null);
  const [analyticsSummary, setAnalyticsSummary] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [toast, setToast] = useState<{ msg: string; type: "ok" | "err" } | null>(null);
  const [activeTask, setActiveTask] = useState<ActiveAnalysisStatus | null>(null);

  // Stable references for closures inside timers
  const selectedShortRef = useRef<ClipProject | null>(null);
  const selectedVideoRef = useRef<SourceVideo | null>(null);

  useEffect(() => {
    selectedShortRef.current = selectedShort;
  }, [selectedShort]);

  useEffect(() => {
    selectedVideoRef.current = selectedVideo;
  }, [selectedVideo]);

  // AI Editor Studio Settings
  const [selectedLayout, setSelectedLayout] = useState<string>("auto");
  const [selectedStyle, setSelectedStyle] = useState<string>("editorial_gold");
  const [shortFilterVideoId, setShortFilterVideoId] = useState<string>("all");

  const showToast = (msg: string, type: "ok" | "err" = "ok") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  const refreshAll = async () => {
    try {
      const [h, ch, v, s] = await Promise.all([
        api.getSystemHealth().catch(() => null),
        api.listChannels().catch(() => []),
        api.listVideos().catch(() => []),
        api.listShorts().catch(() => []),
      ]);
      if (h) setHealth(h);
      if (ch) setChannels(ch);
      if (v) {
        setVideos(v);
        if (!selectedVideoRef.current && v.length > 0) {
          const completedVid = v.find((item) => item.analysis_status === "completed") || v[0];
          selectedVideoRef.current = completedVid;
          setSelectedVideo(completedVid);
        } else if (selectedVideoRef.current) {
          const freshVid = v.find((item) => item.id === selectedVideoRef.current?.id);
          if (freshVid) {
            if (
              freshVid.analysis_status !== selectedVideoRef.current.analysis_status ||
              freshVid.source_status !== selectedVideoRef.current.source_status ||
              freshVid.download_progress?.percent !== selectedVideoRef.current.download_progress?.percent
            ) {
              selectedVideoRef.current = freshVid;
              setSelectedVideo(freshVid);
            }
          }
        }
      }
      if (s) {
        setShorts(s);
        if (!selectedShortRef.current && s.length > 0) {
          selectedShortRef.current = s[0];
          setSelectedShort(s[0]);
        } else if (selectedShortRef.current) {
          const freshShort = s.find((item) => item.id === selectedShortRef.current?.id);
          if (freshShort) {
            if (
              freshShort.status !== selectedShortRef.current.status ||
              freshShort.rendered_video_path !== selectedShortRef.current.rendered_video_path ||
              freshShort.title !== selectedShortRef.current.title
            ) {
              selectedShortRef.current = freshShort;
              setSelectedShort(freshShort);
            }
          }
        }
      }
    } catch (e: any) {
      console.error(e);
    }
  };

  const checkActiveTask = async () => {
    try {
      const task = await api.getActiveAnalysis();
      setActiveTask(task);
      if (task.is_recently_completed) {
        await refreshAll();
        const targetId = task.video_id || selectedVideoRef.current?.id;
        if (targetId) {
          api
            .getCandidates(targetId)
            .then((res) => {
              setCandidates(Array.isArray(res) ? res : []);
            })
            .catch(() => null);
        }
      }
    } catch {
      // ignore
    }
  };

  // Background heartbeat polling every 2 seconds
  useEffect(() => {
    refreshAll();
    checkActiveTask();
    const interval = setInterval(() => {
      refreshAll();
      checkActiveTask();
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  // Fetch candidates whenever active video changes
  useEffect(() => {
    if (selectedVideo) {
      api
        .getCandidates(selectedVideo.id)
        .then((res) => setCandidates(Array.isArray(res) ? res : []))
        .catch(() => setCandidates([]));
    }
  }, [selectedVideo?.id, selectedVideo?.analysis_status]);

  // Periodic poll for candidates if currently looking at an analyzing video or empty candidates
  useEffect(() => {
    if (!selectedVideo) return;
    if (selectedVideo.analysis_status === "analyzing" || candidates.length === 0) {
      const cInterval = setInterval(() => {
        api
          .getCandidates(selectedVideo.id)
          .then((res) => {
            if (Array.isArray(res) && res.length > 0) {
              setCandidates(res);
            }
          })
          .catch(() => null);
      }, 3000);
      return () => clearInterval(cInterval);
    }
  }, [selectedVideo?.id, selectedVideo?.analysis_status, candidates.length]);

  // Fetch QC report for selected short
  useEffect(() => {
    if (selectedShort && selectedShort.status !== "queued" && selectedShort.status !== "rendering") {
      api
        .getQCReport(selectedShort.id)
        .then((qc) => setActiveQC(qc))
        .catch(() => setActiveQC(null));
    } else {
      setActiveQC(null);
    }
  }, [selectedShort?.id, selectedShort?.status]);

  // Fetch channel analytics when available
  useEffect(() => {
    if (channels.length > 0) {
      const chId = channels[0].id;
      api.getChannelAnalytics(chId).then(setAnalyticsSummary).catch(() => null);
      api.getChannelInsights(chId).then(setInsights).catch(() => null);
    }
  }, [channels]);

  const handleStartAnalysis = async (videoId: string) => {
    setLoading(true);
    try {
      await api.startAnalysis(videoId);
      showToast("Started multi-modal video analysis in background!");
      await refreshAll();
    } catch (err: any) {
      showToast(err.message || "Failed to start analysis", "err");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateShort = async (cand: EngagementCandidate): Promise<ClipProject | null> => {
    if (!selectedVideoRef.current) return null;
    setLoading(true);
    try {
      const newShort = await api.generateShort({
        source_video_id: selectedVideoRef.current.id,
        candidate_id: cand.id,
        title: `Short - ${cand.duration.toFixed(0)}s (${cand.scoring_mode})`,
        start_time: cand.start_time,
        end_time: cand.end_time,
        caption_style: selectedStyle,
        framing_mode: selectedLayout,
      });
      showToast("AI Short rendering job queued!");
      selectedShortRef.current = newShort;
      setSelectedShort(newShort);
      await refreshAll();
      return newShort;
    } catch (err: any) {
      showToast(err.message || "Failed to generate short", "err");
      return null;
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = async (shortId: string, mode: "SAFE" | "AUTOMATIC" = "SAFE") => {
    if (channels.length === 0) {
      showToast("No connected YouTube channel. Connect account in Channels tab.", "err");
      return;
    }
    setLoading(true);
    try {
      const res = await api.publishShort({
        clip_project_id: shortId,
        channel_id: channels[0].id,
        mode: mode,
        privacy_status: "private",
      });
      showToast(res.message || "Published to YouTube safely!");
      await refreshAll();
    } catch (err: any) {
      showToast(err.message || "Failed to publish", "err");
    } finally {
      setLoading(false);
    }
  };

  const handleConnectOAuth = () => {
    window.location.href = getOAuthConnectUrl();
  };

  const handleImportYtVideo = async (videoUrl: string): Promise<SourceVideo | null> => {
    try {
      showToast("Starting YouTube download with live progress tracking...");
      const newVid = await api.importYouTubeVideo(videoUrl, true);
      showToast(`Downloading "${newVid.title}"! Tracking real-time % in Video Library.`);
      await refreshAll();
      setSelectedVideo(newVid);
      return newVid;
    } catch (err: any) {
      showToast(err.message || "Failed to import YouTube video", "err");
      return null;
    }
  };

  const handleUploadVideo = async (
    file: File,
    title?: string,
    status: string = "owned"
  ): Promise<SourceVideo | null> => {
    setLoading(true);
    try {
      const res = await api.uploadVideo(file, title || file.name, status);
      showToast(`Uploaded "${res.title}" successfully!`);
      await refreshAll();
      setSelectedVideo(res);
      return res;
    } catch (err: any) {
      showToast(err.message || "Upload failed", "err");
      return null;
    } finally {
      setLoading(false);
    }
  };

  return (
    <StudioContext.Provider
      value={{
        health,
        channels,
        videos,
        selectedVideo,
        setSelectedVideo,
        selectedVideoRef,
        candidates,
        setCandidates,
        shorts,
        setShorts,
        selectedShort,
        setSelectedShort,
        selectedShortRef,
        activeQC,
        setActiveQC,
        insights,
        analyticsSummary,
        loading,
        setLoading,
        toast,
        showToast,
        activeTask,
        selectedLayout,
        setSelectedLayout,
        selectedStyle,
        setSelectedStyle,
        shortFilterVideoId,
        setShortFilterVideoId,
        refreshAll,
        checkActiveTask,
        handleStartAnalysis,
        handleGenerateShort,
        handlePublish,
        handleConnectOAuth,
        handleImportYtVideo,
        handleUploadVideo,
      }}
    >
      {children}
    </StudioContext.Provider>
  );
}

export function useStudio() {
  const context = useContext(StudioContext);
  if (!context) {
    throw new Error("useStudio must be used within a StudioProvider");
  }
  return context;
}
