"use client";

import React, { useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { CheckCircle, RefreshCw, Sparkles } from "lucide-react";
import { useStudio } from "@/context/StudioContext";
import { api } from "@/lib/api";

function OpportunitiesContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const {
    videos,
    selectedVideo,
    setSelectedVideo,
    candidates,
    setCandidates,
    selectedLayout,
    setSelectedLayout,
    selectedStyle,
    setSelectedStyle,
    handleGenerateShort,
    handleStartAnalysis,
    showToast,
    loading,
  } = useStudio();

  // Sync video from URL query param ?video=
  useEffect(() => {
    const videoParam = searchParams.get("video");
    if (videoParam && videos.length > 0) {
      const found = videos.find((v) => v.id === videoParam);
      if (found && found.id !== selectedVideo?.id) {
        setSelectedVideo(found);
      }
    }
  }, [searchParams, videos, selectedVideo?.id, setSelectedVideo]);

  const onGenerateClick = async (cand: any) => {
    const res = await handleGenerateShort(cand);
    if (res) {
      router.push(`/shorts?id=${res.id}&video=${res.source_video_id}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h2 className="text-lg font-bold">Engagement Opportunity Moments (0–100)</h2>
          <p className="text-xs text-zinc-400">
            Candidate clip segments conforming to 15–60s brackets with natural sentence boundaries.
          </p>
        </div>

        {/* Source Video Selector & Recalculate */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-[11px] text-zinc-400 font-medium">Source Video:</label>
            <select
              value={selectedVideo?.id || ""}
              onChange={(e) => {
                const target = videos.find((v) => v.id === e.target.value);
                if (target) {
                  setSelectedVideo(target);
                  router.push(`/opportunities?video=${target.id}`);
                }
              }}
              className="bg-zinc-900 border border-zinc-700 text-zinc-200 text-xs rounded-lg px-3 py-1.5 focus:border-indigo-500 focus:outline-none max-w-[260px] truncate"
            >
              {videos.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.title} ({v.analysis_status})
                </option>
              ))}
            </select>
          </div>

          {selectedVideo && (
            <button
              onClick={() => {
                showToast("Recalculating candidates...");
                api
                  .getCandidates(selectedVideo.id)
                  .then((res) => {
                    setCandidates(Array.isArray(res) ? res : []);
                    showToast(`Loaded ${res.length} candidates!`);
                  })
                  .catch(() => showToast("Failed to fetch candidates", "err"));
              }}
              className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-white text-xs px-3 py-1.5 rounded-lg transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Recalculate
            </button>
          )}
        </div>
      </div>

      {/* AI Editing Studio Controls Bar */}
      <div className="bg-gradient-to-r from-zinc-900 via-indigo-950/40 to-zinc-900 border border-indigo-500/30 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 shadow-lg">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              AI Automated Short Editor Studio
            </span>
            <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full font-mono">
              OpusClip &amp; CapCut AI Style
            </span>
          </div>
          <p className="text-[11px] text-zinc-400">
            Human-grade editorial finishing: scene-aware framing, broadcast audio EQ &amp; crossfades, clean lower-third subtitles, and fade-out hook cards.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Layout Preset */}
          <div className="flex items-center gap-2">
            <label className="text-[11px] text-zinc-400 font-medium">Layout:</label>
            <select
              value={selectedLayout}
              onChange={(e) => setSelectedLayout(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg px-3 py-1.5 focus:border-indigo-500 focus:outline-none"
            >
              <option value="auto">✨ Scene-Aware Auto (AI Detects Screen vs Face)</option>
              <option value="screen_focus">🖥️ Screen / Trading Focus (High-Contrast Backdrop)</option>
              <option value="portrait_focus">👤 Portrait Rule-of-Thirds (Talking Head / Vlog)</option>
              <option value="split_screen">📱 Split Screen Dual Stack (Top/Bottom)</option>
            </select>
          </div>

          {/* Subtitle Preset */}
          <div className="flex items-center gap-2">
            <label className="text-[11px] text-zinc-400 font-medium">Captions:</label>
            <select
              value={selectedStyle}
              onChange={(e) => setSelectedStyle(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg px-3 py-1.5 focus:border-indigo-500 focus:outline-none"
            >
              <option value="editorial_gold">✨ Premiere Clean Gold (Human-Grade Editorial)</option>
              <option value="modern_minimal">💎 Modern Cyan Minimal (Clean Lower Third)</option>
              <option value="cinematic_white">🎬 Cinematic Studio White (Understated)</option>
              <option value="bold_yellow">⚡ Bold Electric Yellow (High Energy)</option>
            </select>
          </div>
        </div>
      </div>

      {candidates.length === 0 ? (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 text-center text-xs text-zinc-400 space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto text-xl">
            ⚡
          </div>
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-zinc-200">
              {selectedVideo?.title ? `"${selectedVideo.title.slice(0, 50)}..."` : "No Video Selected"}
            </h3>
            <p className="text-xs text-zinc-400 max-w-md mx-auto">
              {selectedVideo?.analysis_status === "analyzing"
                ? "Analysis is currently processing speech and visual cues. Candidates will appear automatically once transcription finishes."
                : selectedVideo?.analysis_status === "completed"
                ? "Analysis is complete, but no candidate segments matched the 15-60s threshold for this video. You can switch to another video above or re-run analysis."
                : "This video has not been analyzed yet. Run multi-modal analysis to detect high-engagement hooks and generate shorts."}
            </p>
          </div>

          <div className="flex items-center justify-center gap-3 pt-2">
            {selectedVideo && selectedVideo.analysis_status !== "analyzing" && (
              <button
                onClick={() => handleStartAnalysis(selectedVideo.id)}
                disabled={loading}
                className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-4 py-2.5 rounded-lg transition flex items-center gap-2 shadow-md shadow-indigo-600/30"
              >
                <Sparkles className="w-4 h-4" />
                Analyze This Video Now
              </button>
            )}
            {videos.some((v) => v.id !== selectedVideo?.id && v.analysis_status === "completed") && (
              <button
                onClick={() => {
                  const readyVid = videos.find(
                    (v) => v.id !== selectedVideo?.id && v.analysis_status === "completed"
                  );
                  if (readyVid) setSelectedVideo(readyVid);
                }}
                className="bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold px-4 py-2.5 rounded-lg transition border border-zinc-700 flex items-center gap-2"
              >
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                Switch to Analyzed Video
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {candidates.map((cand, idx) => (
            <div
              key={cand.id}
              className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4 hover:border-zinc-700 transition"
            >
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <span className="text-[10px] text-zinc-500 font-mono uppercase tracking-wider">
                    Rank #{idx + 1} • {cand.scoring_mode} Mode
                  </span>
                  <h4 className="text-sm font-bold text-zinc-200">
                    Candidate Segment ({cand.start_time.toFixed(1)}s – {cand.end_time.toFixed(1)}s)
                  </h4>
                </div>
                <div className="text-right">
                  <div className="text-xl font-black bg-gradient-to-r from-amber-400 to-pink-500 bg-clip-text text-transparent">
                    {cand.overall_score}
                  </div>
                  <span className="text-[10px] text-zinc-500 font-mono">
                    Conf: {(cand.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* Component breakdown */}
              <div className="grid grid-cols-5 gap-2 text-center text-[10px] bg-zinc-950 p-2.5 rounded-lg border border-zinc-800">
                <div>
                  <div className="text-zinc-500">Hook</div>
                  <div className="font-bold text-zinc-200">{cand.hook_score}</div>
                </div>
                <div>
                  <div className="text-zinc-500">Payoff</div>
                  <div className="font-bold text-zinc-200">{cand.payoff_score}</div>
                </div>
                <div>
                  <div className="text-zinc-500">Emotion</div>
                  <div className="font-bold text-zinc-200">{cand.emotional_score}</div>
                </div>
                <div>
                  <div className="text-zinc-500">Topic</div>
                  <div className="font-bold text-zinc-200">{cand.topic_score}</div>
                </div>
                <div>
                  <div className="text-zinc-500">Visual</div>
                  <div className="font-bold text-zinc-200">{cand.visual_score}</div>
                </div>
              </div>

              {/* Justifications */}
              <div className="space-y-1">
                <span className="text-[11px] text-zinc-500 block font-medium">Why Selected:</span>
                <ul className="text-xs text-zinc-300 space-y-1 pl-4 list-disc">
                  {cand.reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>

              <div className="pt-2 border-t border-zinc-800 flex justify-between items-center">
                <span className="text-xs text-zinc-400 font-mono">
                  Duration: {cand.duration.toFixed(1)}s (Shorts compliant)
                </span>
                <button
                  onClick={() => onGenerateClick(cand)}
                  disabled={loading}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition flex items-center gap-1.5 shadow-md shadow-indigo-600/20"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  Generate AI Short
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function OpportunitiesPage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center text-xs text-zinc-500">
          Loading Opportunities &amp; Candidates...
        </div>
      }
    >
      <OpportunitiesContent />
    </Suspense>
  );
}
