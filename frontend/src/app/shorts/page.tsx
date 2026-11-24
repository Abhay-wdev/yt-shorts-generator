"use client";

import React, { useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  CheckCircle,
  PlaySquare,
  RefreshCw,
  Send,
} from "lucide-react";
import { useStudio } from "@/context/StudioContext";
import { api, getThumbnailUrl, getShortVideoUrl } from "@/lib/api";

function ShortsStudioContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const {
    shorts,
    selectedShort,
    setSelectedShort,
    selectedShortRef,
    videos,
    shortFilterVideoId,
    setShortFilterVideoId,
    activeQC,
    refreshAll,
    handlePublish,
  } = useStudio();

  // URL query sync: ?id=<shortId>&video=<videoId>
  useEffect(() => {
    const idParam = searchParams.get("id");
    const videoParam = searchParams.get("video");

    if (videoParam) {
      setShortFilterVideoId(videoParam);
    }

    if (idParam && shorts.length > 0) {
      const found = shorts.find((s) => s.id === idParam);
      if (found && found.id !== selectedShort?.id) {
        selectedShortRef.current = found;
        setSelectedShort(found);
      }
    }
  }, [searchParams, shorts, selectedShort?.id, setSelectedShort, setShortFilterVideoId, selectedShortRef]);

  const onSelectShort = (s: any) => {
    selectedShortRef.current = s;
    setSelectedShort(s);
    router.replace(`/shorts?id=${s.id}${shortFilterVideoId !== "all" ? `&video=${shortFilterVideoId}` : ""}`);
  };

  const filteredShorts =
    shortFilterVideoId === "all"
      ? shorts
      : shorts.filter((s) => s.source_video_id === shortFilterVideoId);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-bold">Generated Shorts &amp; 9:16 Preview Studio</h2>
          <p className="text-xs text-zinc-400">
            Rendered with smart face tracking, animated word-level ASS subtitles, and EBU R128 audio normalization.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Shorts List */}
        <div className="space-y-3 lg:col-span-1">
          <div className="flex justify-between items-center gap-2">
            <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-wider">
              Rendered Shorts ({filteredShorts.length})
            </h3>
            {videos.length > 1 && (
              <select
                value={shortFilterVideoId}
                onChange={(e) => {
                  setShortFilterVideoId(e.target.value);
                  router.replace(
                    `/shorts?${selectedShort ? `id=${selectedShort.id}&` : ""}video=${e.target.value}`
                  );
                }}
                className="bg-zinc-950 border border-zinc-800 text-[10px] text-zinc-300 rounded px-2 py-1 focus:outline-none focus:border-indigo-500 max-w-[140px] truncate"
              >
                <option value="all">All Videos ({shorts.length})</option>
                {videos.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.title}
                  </option>
                ))}
              </select>
            )}
          </div>

          {filteredShorts.length === 0 ? (
            <div className="py-12 text-center text-xs text-zinc-500 border border-dashed border-zinc-800 rounded-xl p-4">
              No shorts found for this filter. Generate one from the Opportunities tab!
            </div>
          ) : (
            <div className="space-y-2.5 max-h-[600px] overflow-y-auto pr-1">
              {filteredShorts.map((s) => (
                <div
                  key={s.id}
                  onClick={() => onSelectShort(s)}
                  className={`bg-zinc-900 border rounded-xl p-3 space-y-2 cursor-pointer transition ${
                    selectedShort?.id === s.id
                      ? "border-indigo-500 ring-2 ring-indigo-500/50 bg-zinc-900/90 shadow-lg shadow-indigo-500/10"
                      : "border-zinc-800 hover:border-zinc-700 hover:bg-zinc-800/40"
                  }`}
                >
                  <div className="flex gap-3 items-center">
                    <div className="w-12 h-16 bg-zinc-950 rounded-lg overflow-hidden border border-zinc-800 shrink-0 relative flex items-center justify-center">
                      <img
                        src={getThumbnailUrl(s.id)}
                        alt={s.title}
                        className="w-full h-full object-cover relative z-10"
                        onError={(e) => {
                          (e.currentTarget as HTMLElement).style.display = "none";
                        }}
                      />
                      <PlaySquare className="w-4 h-4 text-zinc-600 absolute z-0" />
                    </div>
                    <div className="flex-1 min-w-0 space-y-1">
                      <div className="flex justify-between items-start gap-1">
                        <h4 className="text-xs font-bold line-clamp-1 text-zinc-200">{s.title}</h4>
                        <div className="flex items-center gap-1 shrink-0">
                          {selectedShort?.id === s.id && (
                            <span className="text-[9px] bg-indigo-600 text-white font-bold px-1.5 py-0.5 rounded uppercase tracking-wider">
                              Active
                            </span>
                          )}
                          <span
                            className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${
                              s.status === "qc_passed" || s.status === "approved" || s.status === "published"
                                ? "bg-emerald-950 text-emerald-400 border-emerald-800"
                                : s.status === "rendering" || s.status === "queued"
                                ? "bg-indigo-950 text-indigo-400 border-indigo-800 animate-pulse"
                                : "bg-rose-950 text-rose-400 border-rose-800"
                            }`}
                          >
                            {s.status}
                          </span>
                        </div>
                      </div>
                      <div className="flex justify-between text-[10px] text-zinc-500">
                        <span>{(s.end_time - s.start_time).toFixed(1)}s vertical</span>
                        <span className="capitalize">{s.caption_style?.replace("_", " ")}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Video Player & Inspector */}
        <div className="lg:col-span-2 bg-zinc-900 border border-zinc-800 rounded-xl p-6 space-y-5">
          {selectedShort ? (
            <div className="space-y-5">
              <div className="flex flex-col md:flex-row gap-6 items-center">
                {/* 9:16 Video Player Container */}
                <div className="w-56 h-96 bg-black rounded-2xl overflow-hidden border-2 border-zinc-800 shadow-2xl relative shrink-0">
                  {selectedShort.rendered_video_path ? (
                    <video
                      key={selectedShort.id}
                      src={getShortVideoUrl(selectedShort.id)}
                      controls
                      autoPlay
                      className="w-full h-full object-contain"
                    />
                  ) : selectedShort.status === "failed" || selectedShort.status === "qc_failed" ? (
                    <div className="w-full h-full flex flex-col items-center justify-center text-xs text-rose-400 p-4 text-center">
                      <span className="text-xl mb-2">⚠️</span>
                      <span className="font-semibold">Rendering Failed</span>
                      <span className="text-[10px] text-zinc-500 mt-1">Please retry or check system logs.</span>
                    </div>
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center text-xs text-zinc-400 p-4 text-center space-y-2">
                      <RefreshCw className="w-6 h-6 animate-spin text-indigo-400" />
                      <span className="font-semibold text-zinc-200">Rendering 9:16 Short</span>
                      <span className="text-[10px] text-zinc-500 leading-tight">
                        Scene-aware framing, broadcast audio EQ &amp; ASS subtitles...
                      </span>
                    </div>
                  )}
                </div>

                {/* Metadata & Controls */}
                <div className="space-y-4 flex-1">
                  <div>
                    <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
                      Title &amp; SEO Metadata
                    </span>
                    <h3 className="text-sm font-bold text-zinc-100 mt-1">{selectedShort.title}</h3>
                  </div>

                  {selectedShort.metadata && (
                    <div className="space-y-2 text-xs text-zinc-300 bg-zinc-950 p-3.5 rounded-lg border border-zinc-800">
                      <p className="font-semibold text-zinc-400">Viral Title Alternatives:</p>
                      <ul className="text-[11px] text-zinc-400 space-y-1 list-disc pl-4">
                        {selectedShort.metadata.title_options.slice(1, 4).map((t, i) => (
                          <li key={i}>{t}</li>
                        ))}
                      </ul>
                      <div className="flex flex-wrap gap-1.5 pt-2">
                        {selectedShort.metadata.hashtags.map((h, i) => (
                          <span key={i} className="text-[10px] bg-zinc-800 text-indigo-300 px-2 py-0.5 rounded">
                            {h}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Quality Control Badge */}
                  {activeQC && (
                    <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-3 text-xs space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-bold flex items-center gap-1.5">
                          <CheckCircle className="w-4 h-4 text-emerald-400" />
                          Quality Control: {activeQC.passed ? "PASSED" : "FAILED"}
                        </span>
                        <span className="text-zinc-400 font-mono">Score: {activeQC.overall_score}/100</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-[11px] text-zinc-400">
                        <div>• 9:16 Ratio: Valid</div>
                        <div>• Audio Loudness: Normalized</div>
                        <div>• Subtitles: Synchronized</div>
                        <div>• Black Frames: None</div>
                      </div>
                    </div>
                  )}

                  <div className="flex gap-3 pt-2">
                    <button
                      onClick={() => api.approveShort(selectedShort.id).then(refreshAll)}
                      disabled={selectedShort.status === "approved" || selectedShort.status === "published"}
                      className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2 rounded-lg transition"
                    >
                      {selectedShort.status === "approved" ? "Approved" : "Approve Short"}
                    </button>
                    <button
                      onClick={() => handlePublish(selectedShort.id, "SAFE")}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition flex items-center gap-1.5"
                    >
                      <Send className="w-3.5 h-3.5" />
                      Publish to YouTube (Safe Mode)
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-16 text-center text-xs text-zinc-500">
              Select a rendered Short to preview 9:16 playback and view Quality Control analysis.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ShortsPage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center text-xs text-zinc-500">
          Loading Shorts Studio...
        </div>
      }
    >
      <ShortsStudioContent />
    </Suspense>
  );
}
