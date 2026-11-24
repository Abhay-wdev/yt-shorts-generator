"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  FileVideo,
  Loader2,
  PlaySquare,
  RefreshCw,
  Search,
  Sparkles,
  Upload,
} from "lucide-react";
import { useStudio } from "@/context/StudioContext";
import { api, ExploreChannelResponse } from "@/lib/api";

export default function VideoLibraryPage() {
  const router = useRouter();
  const {
    videos,
    selectedVideo,
    setSelectedVideo,
    handleStartAnalysis,
    handleImportYtVideo,
    handleUploadVideo,
    showToast,
    loading,
    activeTask,
  } = useStudio();

  // Upload modal state
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState("owned");

  // YouTube Channel Import state
  const [ytChannelInput, setYtChannelInput] = useState("");
  const [exploredChannel, setExploredChannel] = useState<ExploreChannelResponse | null>(null);
  const [exploringYt, setExploringYt] = useState(false);
  const [importingVideoId, setImportingVideoId] = useState<string | null>(null);

  const handleExploreChannel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ytChannelInput.trim()) return;
    setExploringYt(true);
    try {
      showToast("Searching YouTube channel videos...");
      const res = await api.exploreChannel(ytChannelInput.trim(), 12);
      setExploredChannel(res);
      showToast(`Loaded ${res.videos.length} videos from ${res.channel_name}!`);
    } catch (err: any) {
      showToast(err.message || "Failed to find channel", "err");
    } finally {
      setExploringYt(false);
    }
  };

  const onImportClick = async (url: string, id: string) => {
    setImportingVideoId(id);
    try {
      await handleImportYtVideo(url);
    } finally {
      setImportingVideoId(null);
    }
  };

  const onUploadClick = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    const res = await handleUploadVideo(uploadFile, uploadTitle, uploadStatus);
    if (res) {
      setUploadFile(null);
      setUploadTitle("");
    }
  };

  return (
    <div className="space-y-6">
      {/* YouTube Channel Auto-Ingest Card */}
      <div className="bg-gradient-to-r from-rose-950/30 via-zinc-900 to-zinc-900 border border-rose-900/40 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-rose-600/20 border border-rose-500/30 flex items-center justify-center">
              <PlaySquare className="w-4 h-4 text-rose-500" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-zinc-100">
                Auto-Import from YouTube Channel / URL
              </h3>
              <p className="text-[11px] text-zinc-400">
                Paste any YouTube channel link (e.g. @MrBeast, https://youtube.com/@Channel) or specific video URL to auto-extract &amp; generate Shorts
              </p>
            </div>
          </div>
        </div>

        <form onSubmit={handleExploreChannel} className="flex gap-2">
          <input
            type="text"
            placeholder="Enter channel handle or link: @ChannelName or https://www.youtube.com/@Name"
            value={ytChannelInput}
            onChange={(e) => setYtChannelInput(e.target.value)}
            className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:border-rose-500"
          />
          <button
            type="submit"
            disabled={exploringYt || !ytChannelInput.trim()}
            className="bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold px-4 py-2 rounded-lg disabled:opacity-50 transition flex items-center gap-1.5 shadow-md shadow-rose-900/20"
          >
            {exploringYt ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Fetching...
              </>
            ) : (
              <>
                <Search className="w-3.5 h-3.5" />
                Fetch Channel
              </>
            )}
          </button>
        </form>

        {/* Explored Channel Results */}
        {exploredChannel && (
          <div className="mt-4 pt-4 border-t border-zinc-800/80 space-y-3">
            <div className="flex justify-between items-center">
              <h4 className="text-xs font-bold text-zinc-200 flex items-center gap-2">
                <span>Channel:</span>
                <span className="text-rose-400">{exploredChannel.channel_name}</span>
                <span className="text-[10px] text-zinc-500">
                  ({exploredChannel.videos.length} videos found)
                </span>
              </h4>
              <button
                onClick={() => setExploredChannel(null)}
                className="text-[10px] text-zinc-500 hover:text-zinc-300"
              >
                Clear
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {exploredChannel.videos.map((vid) => (
                <div
                  key={vid.id}
                  className="bg-zinc-950 border border-zinc-800/80 rounded-lg p-3 space-y-2.5 flex flex-col justify-between hover:border-zinc-700 transition"
                >
                  <div className="space-y-2">
                    <div className="relative aspect-video rounded overflow-hidden bg-zinc-900">
                      <img
                        src={vid.thumbnail_url}
                        alt={vid.title}
                        className="w-full h-full object-cover"
                      />
                      <span className="absolute bottom-1 right-1 bg-black/80 text-[10px] text-zinc-300 font-mono px-1.5 py-0.5 rounded">
                        {vid.duration_formatted}
                      </span>
                    </div>
                    <h5 className="text-xs font-semibold line-clamp-2 text-zinc-200">
                      {vid.title}
                    </h5>
                  </div>

                  <button
                    onClick={() => onImportClick(vid.url, vid.id)}
                    disabled={
                      loading ||
                      importingVideoId === vid.id ||
                      Boolean(
                        activeTask?.has_active &&
                          activeTask.video_title?.includes(vid.title.substring(0, 15))
                      )
                    }
                    className={`w-full text-white text-xs font-semibold py-1.5 rounded transition flex items-center justify-center gap-1.5 disabled:opacity-80 ${
                      activeTask?.has_active &&
                      activeTask.video_title?.includes(vid.title.substring(0, 15))
                        ? "bg-indigo-600 animate-pulse border border-indigo-400"
                        : "bg-rose-600/90 hover:bg-rose-600"
                    }`}
                  >
                    {activeTask?.has_active &&
                    activeTask.video_title?.includes(vid.title.substring(0, 15)) ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        Analyzing ({activeTask.progress_percent?.toFixed(0)}%)
                      </>
                    ) : importingVideoId === vid.id ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        Downloading Video...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5" />
                        Auto-Import &amp; Generate Shorts
                      </>
                    )}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Upload Card */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-bold flex items-center gap-2">
          <Upload className="w-4 h-4 text-indigo-400" />
          Or Ingest Local Video File
        </h3>
        <form onSubmit={onUploadClick} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-[11px] text-zinc-400 block mb-1">
              Video File (MP4, MKV, MOV)
            </label>
            <input
              type="file"
              accept="video/*"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              className="text-xs text-zinc-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-zinc-800 file:text-zinc-200 hover:file:bg-zinc-700 w-full"
            />
          </div>
          <div>
            <label className="text-[11px] text-zinc-400 block mb-1">
              Custom Title (Optional)
            </label>
            <input
              type="text"
              placeholder="My Documentary / Podcast Episode"
              value={uploadTitle}
              onChange={(e) => setUploadTitle(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-200 w-full focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="text-[11px] text-zinc-400 block mb-1">
              Source Permission Status
            </label>
            <div className="flex gap-2">
              <select
                value={uploadStatus}
                onChange={(e) => setUploadStatus(e.target.value)}
                className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-200 flex-1 focus:outline-none focus:border-indigo-500"
              >
                <option value="owned">Owned by me</option>
                <option value="licensed">Licensed content</option>
                <option value="authorized">Authorized permission</option>
                <option value="unknown">Unknown</option>
              </select>
              <button
                type="submit"
                disabled={loading || !uploadFile}
                className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-4 py-1.5 rounded-lg disabled:opacity-50 transition"
              >
                Ingest
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Videos List */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold flex items-center justify-between">
          <span>Ingested Video Library ({videos.length})</span>
          <span className="text-xs text-zinc-500 font-normal">
            Click any video card to set it as active
          </span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {videos.map((vid) => (
            <div
              key={vid.id}
              className={`bg-zinc-900 border rounded-xl p-4 space-y-3 transition cursor-pointer ${
                selectedVideo?.id === vid.id
                  ? "border-indigo-500 shadow-md shadow-indigo-500/10 ring-1 ring-indigo-500/50"
                  : "border-zinc-800 hover:border-zinc-700"
              }`}
              onClick={() => setSelectedVideo(vid)}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-xs font-bold line-clamp-1">{vid.title}</h4>
                  <span className="text-[10px] text-zinc-500 font-mono">
                    {vid.width}x{vid.height} • {vid.fps}fps • {vid.codec_video || "h264"}
                  </span>
                </div>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                    vid.analysis_status === "completed"
                      ? "bg-emerald-950 text-emerald-400 border-emerald-800"
                      : vid.analysis_status === "analyzing"
                      ? "bg-indigo-950 text-indigo-400 border-indigo-800 animate-pulse"
                      : vid.analysis_status === "downloading" || vid.download_progress
                      ? "bg-sky-950 text-sky-400 border-sky-800 animate-pulse"
                      : "bg-zinc-800 text-zinc-400 border-zinc-700"
                  }`}
                >
                  {vid.download_progress
                    ? vid.download_progress.status === "processing"
                      ? "Downloaded ✓"
                      : `Downloading ${vid.download_progress.percent.toFixed(0)}%`
                    : vid.analysis_status}
                </span>
              </div>

              {/* Live Download Status & Progress Bar */}
              {(vid.download_progress || vid.analysis_status === "downloading") && (
                <div className="bg-zinc-950 p-2.5 rounded-lg border border-sky-500/30 space-y-2">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-sky-300 flex items-center gap-1.5 text-[11px]">
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-400" />
                      {vid.download_progress?.status === "processing"
                        ? "✓ Download Complete! Processing..."
                        : `Downloaded: ${vid.download_progress?.percent || 0}%`}
                    </span>
                    <span className="font-mono text-zinc-400 text-[10px]">
                      {vid.download_progress?.status !== "processing" ? (
                        <>
                          Remaining:{" "}
                          <strong className="text-zinc-200">
                            {vid.download_progress?.remaining_percent ?? 100}%
                          </strong>
                        </>
                      ) : (
                        <span className="text-emerald-400">Ready to Analyze</span>
                      )}
                    </span>
                  </div>

                  <div className="w-full bg-zinc-800 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-sky-400 via-indigo-500 to-emerald-400 h-full transition-all duration-300"
                      style={{
                        width: `${Math.max(4, vid.download_progress?.percent || 0)}%`,
                      }}
                    ></div>
                  </div>

                  <div className="flex justify-between text-[10px] text-zinc-500 font-mono">
                    <span>Speed: {vid.download_progress?.speed || "Connecting..."}</span>
                    {(vid.download_progress?.eta || 0) > 0 && (
                      <span className="text-sky-400">
                        ETA: ~{vid.download_progress?.eta}s
                      </span>
                    )}
                    {(vid.download_progress?.total_mb || 0) > 0 && (
                      <span>
                        {vid.download_progress?.downloaded_mb}/
                        {vid.download_progress?.total_mb} MB
                      </span>
                    )}
                  </div>
                </div>
              )}

              <div className="flex justify-between items-center text-[11px] text-zinc-400">
                <span>
                  Duration:{" "}
                  {vid.duration_seconds > 0
                    ? `${vid.duration_seconds.toFixed(1)}s`
                    : "Fetching..."}
                </span>
                <span className="capitalize text-zinc-500">
                  Status: {vid.source_status}
                </span>
              </div>

              <div className="flex gap-2 pt-2 border-t border-zinc-800">
                {vid.analysis_status === "downloading" ? (
                  <div className="w-full text-center py-2 text-[11px] font-medium text-sky-400 bg-sky-950/40 border border-sky-800/40 rounded-lg flex items-center justify-center gap-2">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-400" />
                    Downloading Video Stream ({vid.download_progress?.percent || 0}%)
                  </div>
                ) : (
                  <>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleStartAnalysis(vid.id);
                      }}
                      className="flex-1 bg-zinc-800 hover:bg-zinc-700 text-white text-xs py-1.5 rounded-lg transition text-center"
                    >
                      Analyze
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedVideo(vid);
                        router.push(`/opportunities?video=${vid.id}`);
                      }}
                      className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white text-xs py-1.5 rounded-lg transition text-center"
                    >
                      Opportunities
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
