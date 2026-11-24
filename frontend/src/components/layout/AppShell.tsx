"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  AlertCircle,
  BarChart2,
  Check,
  CheckCircle,
  Clock,
  Cpu,
  FileVideo,
  Film,
  Loader2,
  RefreshCw,
  Send,
  Settings as SettingsIcon,
  Sparkles,
  TrendingUp,
  Upload,
  Youtube,
} from "lucide-react";
import { useStudio } from "@/context/StudioContext";

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { href: "/", label: "Dashboard", icon: BarChart2 },
  { href: "/channels", label: "YouTube Channels", icon: Youtube },
  { href: "/library", label: "Video Library", icon: FileVideo },
  { href: "/analysis", label: "Video Analysis", icon: Activity },
  { href: "/opportunities", label: "Opportunities", icon: Sparkles },
  { href: "/shorts", label: "Generated Shorts", icon: Film },
  { href: "/publishing", label: "Publishing Queue", icon: Send },
  { href: "/analytics", label: "Performance", icon: TrendingUp },
  { href: "/settings", label: "Settings", icon: SettingsIcon },
  { href: "/health", label: "System Health", icon: Cpu },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const {
    health,
    videos,
    selectedVideo,
    setSelectedVideo,
    toast,
    activeTask,
    refreshAll,
  } = useStudio();

  // Determine current page label
  const currentNav =
    navItems.find((item) => {
      if (item.href === "/") {
        return pathname === "/" || pathname === "/dashboard";
      }
      return pathname.startsWith(item.href);
    }) || navItems[0];

  return (
    <div className="flex min-h-screen bg-zinc-950 text-zinc-100 font-sans">
      {/* Toast Notification */}
      {toast && (
        <div
          className={`fixed top-5 right-5 z-50 flex items-center gap-2 px-4 py-3 rounded-lg shadow-xl text-sm border font-medium transition-all ${
            toast.type === "ok"
              ? "bg-emerald-950 border-emerald-600 text-emerald-200"
              : "bg-rose-950 border-rose-600 text-rose-200"
          }`}
        >
          {toast.type === "ok" ? (
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-400" />
          )}
          {toast.msg}
        </div>
      )}

      {/* Sidebar */}
      <aside className="w-64 border-r border-zinc-800 bg-zinc-900/60 p-4 flex flex-col justify-between shrink-0 sticky top-0 h-screen">
        <div>
          {/* Logo / Brand */}
          <Link href="/" className="flex items-center gap-3 px-2 py-3 mb-6 block group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-pink-500 flex items-center justify-center font-bold text-lg shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
              ⚡
            </div>
            <div>
              <h1 className="font-bold text-sm tracking-wide bg-gradient-to-r from-indigo-200 to-pink-200 bg-clip-text text-transparent">
                Shorts Studio AI
              </h1>
              <p className="text-[10px] text-zinc-500 font-mono">Ryzen 3 5300U • $0 Local</p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/"
                  ? pathname === "/" || pathname === "/dashboard"
                  : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`w-full flex items-center gap-3 px-3 py-2 text-xs font-medium rounded-lg transition-all ${
                    isActive
                      ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-semibold"
                      : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Live System Mini-Badge */}
        <div className="border border-zinc-800 bg-zinc-950/80 rounded-xl p-3 text-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-zinc-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              {health?.hardware.ram.pressure_state || "NORMAL"}
            </span>
            <span className="text-[10px] font-mono text-zinc-500">
              {health?.hardware.video_acceleration.name || "h264_amf"}
            </span>
          </div>
          <div className="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                (health?.hardware.ram.used_percent || 0) > 85
                  ? "bg-rose-500"
                  : (health?.hardware.ram.used_percent || 0) > 70
                  ? "bg-amber-500"
                  : "bg-indigo-500"
              }`}
              style={{ width: `${health?.hardware.ram.used_percent || 65}%` }}
            ></div>
          </div>
          <div className="flex justify-between text-[10px] text-zinc-500">
            <span>RAM: {health?.hardware.ram.available_mb || 3700} MB Free</span>
            <span>CPU: {health?.hardware.cpu.physical_cores || 4}C/8T</span>
          </div>
        </div>
      </aside>

      {/* Main Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Sticky Header */}
        <header className="h-16 border-b border-zinc-800 px-6 flex items-center justify-between bg-zinc-900/30 sticky top-0 z-20 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <span className="text-zinc-400 text-xs uppercase tracking-wider font-semibold">
              {currentNav.label}
            </span>
            {videos.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-zinc-600 text-xs">•</span>
                <select
                  value={selectedVideo?.id || ""}
                  onChange={(e) => {
                    const found = videos.find((v) => v.id === e.target.value);
                    if (found) setSelectedVideo(found);
                  }}
                  className="text-xs bg-zinc-900 text-zinc-300 px-2.5 py-1 rounded-md border border-zinc-700 font-mono max-w-[240px] truncate focus:outline-none focus:border-indigo-500"
                >
                  {videos.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.title}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={refreshAll}
              className="p-2 text-zinc-400 hover:text-white rounded-lg hover:bg-zinc-800 transition"
              title="Refresh All"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <Link
              href="/library"
              className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-pink-600 text-white text-xs font-medium px-3.5 py-2 rounded-lg hover:opacity-90 shadow-md shadow-indigo-600/20 transition"
            >
              <Upload className="w-3.5 h-3.5" />
              Upload / Import Video
            </Link>
          </div>
        </header>

        {/* Real-Time Processing Monitor Banner */}
        {activeTask && (activeTask.has_active || activeTask.is_recently_completed) && (
          <div className="mx-6 mt-6 p-4 rounded-xl border transition-all duration-300 shadow-xl bg-gradient-to-r from-indigo-950/80 via-zinc-900 to-zinc-900 border-indigo-700/60 shadow-indigo-950/40">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-3">
              <div className="flex items-center gap-3">
                {activeTask.has_active ? (
                  <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center shrink-0">
                    <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                  </div>
                ) : (
                  <div className="w-8 h-8 rounded-lg bg-emerald-600/20 border border-emerald-500/40 flex items-center justify-center shrink-0">
                    <Check className="w-4 h-4 text-emerald-400" />
                  </div>
                )}
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase font-mono ${
                        activeTask.is_downloading
                          ? "bg-sky-950 text-sky-300 border border-sky-800 animate-pulse"
                          : activeTask.has_active
                          ? "bg-indigo-950 text-indigo-300 border border-indigo-800"
                          : "bg-emerald-950 text-emerald-300 border border-emerald-800"
                      }`}
                    >
                      {activeTask.is_downloading
                        ? "YouTube Download in Progress"
                        : activeTask.has_active
                        ? "AI Video Processing Active"
                        : "Analysis Completed"}
                    </span>
                    <span className="text-xs font-bold text-zinc-200 line-clamp-1">
                      {activeTask.video_title}
                    </span>
                  </div>
                  <p className="text-xs text-indigo-300/90 mt-0.5 flex items-center gap-1.5 font-medium">
                    <span>{activeTask.current_step || "Processing pipeline..."}</span>
                  </p>
                </div>
              </div>

              {/* Progress & ETA info */}
              <div className="flex items-center gap-4 text-xs font-mono text-zinc-400">
                {activeTask.has_active && (
                  <>
                    <div className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-zinc-500" />
                      <span>
                        {activeTask.is_downloading ? (
                          <>
                            Downloaded:{" "}
                            <strong className="text-sky-300">
                              {activeTask.progress_percent?.toFixed(1)}%
                            </strong>{" "}
                            | Remaining:{" "}
                            <strong className="text-zinc-300">
                              {activeTask.remaining_percent?.toFixed(1)}%
                            </strong>
                          </>
                        ) : (
                          <>
                            Elapsed: {Math.floor((activeTask.elapsed_seconds || 0) / 60)}:
                            {String((activeTask.elapsed_seconds || 0) % 60).padStart(2, "0")}
                          </>
                        )}
                      </span>
                    </div>
                    {(activeTask.estimated_remaining_seconds || 0) > 0 && (
                      <span
                        className={
                          activeTask.is_downloading ? "text-sky-400" : "text-indigo-400"
                        }
                      >
                        ETA: ~{activeTask.estimated_remaining_seconds}s
                      </span>
                    )}
                  </>
                )}
                {activeTask.is_recently_completed && (
                  <button
                    onClick={() => {
                      const v = videos.find((item) => item.id === activeTask.video_id);
                      if (v) setSelectedVideo(v);
                      router.push("/opportunities");
                    }}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs px-3.5 py-1.5 rounded-lg transition shadow-md shadow-emerald-900/30 flex items-center gap-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    View Engagement Moments &amp; Shorts
                  </button>
                )}
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-zinc-950 border border-zinc-800 rounded-full h-2.5 overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${
                  activeTask.is_downloading
                    ? "bg-gradient-to-r from-sky-400 via-indigo-500 to-emerald-400 animate-pulse"
                    : activeTask.has_active
                    ? "bg-gradient-to-r from-indigo-500 via-pink-500 to-emerald-400 animate-pulse"
                    : "bg-emerald-500"
                }`}
                style={{ width: `${Math.max(5, activeTask.progress_percent || 0)}%` }}
              ></div>
            </div>
            <div className="flex justify-between items-center text-[10px] text-zinc-500 font-mono mt-1">
              <span>
                {activeTask.is_downloading
                  ? "Download Stage: 1 Extract Info ➔ 2 1080p Stream Download ➔ 3 Audio Merge ➔ 4 Proxy Gen ➔ 5 AI Analysis"
                  : "Pipeline: 1 Ingest ➔ 2 Audio RMS ➔ 3 Whisper AI ➔ 4 Scene Cuts ➔ 5 Tracking ➔ 6 Viral Shorts"}
              </span>
              <span className="font-bold text-zinc-300">
                {activeTask.is_downloading
                  ? `${activeTask.progress_percent?.toFixed(1)}% (${activeTask.remaining_percent?.toFixed(1)}% left)`
                  : `${activeTask.progress_percent?.toFixed(0)}%`}
              </span>
            </div>
          </div>
        )}

        {/* Dynamic Page Views */}
        <div className="p-6 max-w-7xl w-full mx-auto space-y-6">{children}</div>
      </main>
    </div>
  );
}
