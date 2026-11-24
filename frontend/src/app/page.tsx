"use client";

import React from "react";
import Link from "next/link";
import {
  BarChart2,
  CheckCircle,
  FileVideo,
  Film,
  RefreshCw,
  Send,
  Sparkles,
  Youtube,
  Zap,
} from "lucide-react";
import { useStudio } from "@/context/StudioContext";

export default function DashboardPage() {
  const {
    channels,
    videos,
    candidates,
    shorts,
    health,
    selectedVideo,
    handleGenerateShort,
    loading,
  } = useStudio();

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-indigo-950/60 via-zinc-900 to-zinc-900 border border-indigo-900/40 rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>Welcome to Shorts Studio AI</span>
            <span className="text-xs bg-indigo-500/20 text-indigo-300 font-mono px-2 py-0.5 rounded-full border border-indigo-500/30">
              v2.4 Editorial
            </span>
          </h2>
          <p className="text-xs text-zinc-400 mt-1 max-w-xl">
            Human-grade autonomous vertical video pipeline. Automated Whisper AI transcription, PySceneDetect boundary cuts, dynamic face tracking, and 100/100 QC verification.
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Link
            href="/opportunities"
            className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2.5 rounded-xl transition shadow-lg shadow-indigo-600/20 flex items-center gap-1.5"
          >
            <Sparkles className="w-4 h-4" />
            Explore Moments
          </Link>
          <Link
            href="/shorts"
            className="bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold px-4 py-2.5 rounded-xl transition border border-zinc-700 flex items-center gap-1.5"
          >
            <Film className="w-4 h-4" />
            View Shorts ({shorts.length})
          </Link>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="text-zinc-400 text-xs font-medium flex items-center justify-between">
            <span>Connected Channels</span>
            <Youtube className="w-4 h-4 text-red-500" />
          </div>
          <div className="text-2xl font-bold mt-2">{channels.length}</div>
          <p className="text-[11px] text-zinc-500 mt-1">Official OAuth 2.0</p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="text-zinc-400 text-xs font-medium flex items-center justify-between">
            <span>Videos Ingested</span>
            <FileVideo className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold mt-2">{videos.length}</div>
          <p className="text-[11px] text-zinc-500 mt-1">Probed via FFprobe</p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="text-zinc-400 text-xs font-medium flex items-center justify-between">
            <span>Total Opportunities</span>
            <Sparkles className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold mt-2">{candidates.length}</div>
          <p className="text-[11px] text-zinc-500 mt-1">Scored (0-100)</p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="text-zinc-400 text-xs font-medium flex items-center justify-between">
            <span>Generated Shorts</span>
            <Film className="w-4 h-4 text-pink-400" />
          </div>
          <div className="text-2xl font-bold mt-2">{shorts.length}</div>
          <p className="text-[11px] text-zinc-500 mt-1">9:16 Vertical Rendered</p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="text-zinc-400 text-xs font-medium flex items-center justify-between">
            <span>Approved Shorts</span>
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold mt-2">
            {shorts.filter((s) => s.status === "approved" || s.status === "published").length}
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">Ready to Publish</p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="text-zinc-400 text-xs font-medium flex items-center justify-between">
            <span>Published Shorts</span>
            <Send className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold mt-2">
            {shorts.filter((s) => s.status === "published").length}
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">Live on YouTube</p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="text-zinc-400 text-xs font-medium flex items-center justify-between">
            <span>Background Jobs</span>
            <RefreshCw className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold mt-2">{health?.queue.active_count || 0}</div>
          <p className="text-[11px] text-zinc-500 mt-1">RAM-Protected Queue</p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="text-zinc-400 text-xs font-medium flex items-center justify-between">
            <span>Hardware Encoder</span>
            <Zap className="w-4 h-4 text-orange-400" />
          </div>
          <div className="text-lg font-bold mt-2 font-mono truncate">
            {health?.hardware.video_acceleration.name || "h264_amf"}
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">AMD Radeon Engine</p>
        </div>
      </div>

      {/* Quick Action: Top Engagement Opportunities */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-400" />
              Top Engagement Moments ({selectedVideo?.title || "No video selected"})
            </h2>
            <p className="text-xs text-zinc-400 mt-0.5">
              Multi-modal engagement intelligence with dynamic weight normalization.
            </p>
          </div>
          <Link
            href="/opportunities"
            className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
          >
            View All →
          </Link>
        </div>

        {candidates.length === 0 ? (
          <div className="py-8 text-center text-xs text-zinc-500 border border-dashed border-zinc-800 rounded-lg">
            No engagement candidates calculated yet. Ingest a video and run analysis!
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {candidates.slice(0, 3).map((cand) => (
              <div
                key={cand.id}
                className="bg-zinc-950 border border-zinc-800 rounded-xl p-4 space-y-3 flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold bg-indigo-950 text-indigo-300 px-2 py-0.5 rounded border border-indigo-800">
                      Score: {cand.overall_score}/100
                    </span>
                    <span className="text-[11px] text-zinc-500 font-mono">
                      {cand.start_time.toFixed(1)}s - {cand.end_time.toFixed(1)}s ({cand.duration.toFixed(0)}s)
                    </span>
                  </div>
                  <div className="text-[11px] text-zinc-400 space-y-1">
                    <p className="line-clamp-2 italic text-zinc-300">
                      "{cand.reasons[0] || "High interest segment"}"
                    </p>
                    <div className="flex gap-2 text-[10px] text-zinc-500">
                      <span>Hook: {cand.hook_score}</span>
                      <span>Payoff: {cand.payoff_score}</span>
                      <span>Mode: {cand.scoring_mode}</span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => handleGenerateShort(cand)}
                  disabled={loading}
                  className="w-full bg-zinc-800 hover:bg-indigo-600 text-white text-xs font-medium py-2 rounded-lg transition"
                >
                  Generate 9:16 Short
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
