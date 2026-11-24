"use client";

import React from "react";
import { Cpu, HardDrive } from "lucide-react";
import { useStudio } from "@/context/StudioContext";

export default function HealthPage() {
  const { health } = useStudio();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold">System Health &amp; Hardware Profiler</h2>
        <p className="text-xs text-zinc-400">
          Continuous thermal and memory monitoring for AMD Ryzen 3 5300U + Radeon Graphics.
        </p>
      </div>

      {health ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-bold flex items-center gap-2">
              <Cpu className="w-4 h-4 text-indigo-400" />
              Processor &amp; Memory
            </h3>
            <div className="space-y-2 text-xs text-zinc-300">
              <div className="flex justify-between py-1 border-b border-zinc-800">
                <span className="text-zinc-500">Model</span>
                <span className="font-mono">{health.hardware.cpu.model}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-zinc-800">
                <span className="text-zinc-500">Cores / Threads</span>
                <span className="font-mono">
                  {health.hardware.cpu.physical_cores} Cores /{" "}
                  {health.hardware.cpu.logical_threads} Threads
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-zinc-800">
                <span className="text-zinc-500">Total System RAM</span>
                <span className="font-mono">{health.hardware.ram.total_mb} MB</span>
              </div>
              <div className="flex justify-between py-1 border-b border-zinc-800">
                <span className="text-zinc-500">Available RAM</span>
                <span className="font-mono text-emerald-400">
                  {health.hardware.ram.available_mb} MB
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-zinc-500">Memory Pressure</span>
                <span className="font-mono font-bold text-indigo-400">
                  {health.hardware.ram.pressure_state}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-bold flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-pink-400" />
              Graphics &amp; Acceleration
            </h3>
            <div className="space-y-2 text-xs text-zinc-300">
              <div className="flex justify-between py-1 border-b border-zinc-800">
                <span className="text-zinc-500">Graphics Device</span>
                <span className="font-mono">{health.hardware.gpu.name}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-zinc-800">
                <span className="text-zinc-500">Dedicated VRAM</span>
                <span className="font-mono">
                  {health.hardware.gpu.dedicated_vram_mb} MB
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-zinc-800">
                <span className="text-zinc-500">Shared Memory Pool</span>
                <span className="font-mono">{health.hardware.gpu.shared_pool_mb} MB</span>
              </div>
              <div className="flex justify-between py-1 border-b border-zinc-800">
                <span className="text-zinc-500">Recommended Encoder</span>
                <span className="font-mono text-emerald-400">
                  {health.hardware.video_acceleration.name} (
                  {health.hardware.video_acceleration.type})
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-zinc-500">Active Queue Tasks</span>
                <span className="font-mono font-bold text-amber-400">
                  {health.queue.active_count} jobs
                </span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="py-12 text-center text-xs text-zinc-500">
          Loading hardware metrics...
        </div>
      )}
    </div>
  );
}
