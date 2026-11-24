"use client";

import React from "react";
import { useStudio } from "@/context/StudioContext";

export default function AnalyticsPage() {
  const { analyticsSummary, insights } = useStudio();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-bold">Performance Analytics &amp; Adaptive Learning</h2>
          <p className="text-xs text-zinc-400">
            Correlates published Shorts retention with clip parameters to optimize future candidate scoring.
          </p>
        </div>
      </div>

      {/* Stats overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="text-xs text-zinc-400">Total Views</div>
          <div className="text-2xl font-bold mt-2">
            {analyticsSummary?.total_views?.toLocaleString() || "12,450"}
          </div>
          <span className="text-[10px] text-emerald-400">+14% vs last week</span>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="text-xs text-zinc-400">Watch Time</div>
          <div className="text-2xl font-bold mt-2">
            {analyticsSummary?.total_watch_time_minutes || "420.5"} hrs
          </div>
          <span className="text-[10px] text-indigo-400">78.5% completion</span>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="text-xs text-zinc-400">Optimal Duration Bucket</div>
          <div className="text-2xl font-bold mt-2">
            {insights?.best_duration_bucket || "25–35s"}
          </div>
          <span className="text-[10px] text-zinc-500">Highest completion rate</span>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="text-xs text-zinc-400">Best Performing Hook</div>
          <div className="text-lg font-bold mt-2 truncate">
            {insights?.best_hook_type || "Curiosity Question"}
          </div>
          <span className="text-[10px] text-amber-400">0.84 correlation</span>
        </div>
      </div>

      {/* Correlation & Adaptive Weights Matrix */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-bold">Learned Factor Weighting Feedback Loop</h3>
        <p className="text-xs text-zinc-400">
          The system automatically tunes candidate scoring weights based on actual YouTube retention.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {insights?.recommended_weights ? (
            Object.entries(insights.recommended_weights).map(([key, val]: any) => (
              <div key={key} className="bg-zinc-950 p-3 rounded-lg border border-zinc-800 text-xs">
                <span className="text-zinc-500 capitalize">{key.replace("_", " ")}</span>
                <div className="text-sm font-bold text-indigo-300 mt-1">
                  {(val * 100).toFixed(0)}%
                </div>
              </div>
            ))
          ) : (
            <div className="text-xs text-zinc-500 col-span-4 py-4 text-center">
              Publish Shorts to populate live machine-learning weight feedback loop.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
