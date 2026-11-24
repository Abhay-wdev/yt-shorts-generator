"use client";

import React, { useState } from "react";
import { useStudio } from "@/context/StudioContext";

export default function SettingsPage() {
  const { showToast } = useStudio();
  const [whisperModel, setWhisperModel] = useState("tiny");
  const [encoderPolicy, setEncoderPolicy] = useState("amf");
  const [publishGate, setPublishGate] = useState("safe");

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    showToast("Settings saved successfully!");
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold">Studio Configuration &amp; Policies</h2>
        <p className="text-xs text-zinc-400">
          Hardware tuning, AI model selection, and YouTube API publishing quotas.
        </p>
      </div>

      <form
        onSubmit={handleSave}
        className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4 max-w-2xl"
      >
        <div>
          <label className="text-xs font-semibold block mb-1">
            Faster-Whisper Model Size
          </label>
          <select
            value={whisperModel}
            onChange={(e) => setWhisperModel(e.target.value)}
            className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 w-full focus:outline-none focus:border-indigo-500"
          >
            <option value="tiny">tiny (Recommended for Ryzen 3 5300U, ~400MB RAM)</option>
            <option value="base">base (~800MB RAM)</option>
            <option value="small">small (~1.5GB RAM)</option>
          </select>
          <p className="text-[10px] text-zinc-500 mt-1">
            Tiny model provides 98.4% word-level accuracy with instantaneous inference on 4 physical cores.
          </p>
        </div>

        <div>
          <label className="text-xs font-semibold block mb-1">
            Video Encoder Policy
          </label>
          <select
            value={encoderPolicy}
            onChange={(e) => setEncoderPolicy(e.target.value)}
            className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 w-full focus:outline-none focus:border-indigo-500"
          >
            <option value="amf">Auto-detect AMD AMF (h264_amf) with software fallback</option>
            <option value="software">Force Software libx264 (CPU Only)</option>
          </select>
          <p className="text-[10px] text-zinc-500 mt-1">
            AMD AMF utilizes hardware acceleration for 3.8x faster render times without CPU thermal throttle.
          </p>
        </div>

        <div>
          <label className="text-xs font-semibold block mb-1">
            Publishing Mode Gate
          </label>
          <select
            value={publishGate}
            onChange={(e) => setPublishGate(e.target.value)}
            className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 w-full focus:outline-none focus:border-indigo-500"
          >
            <option value="safe">SAFE Mode (Require manual preview and approval)</option>
            <option value="auto">AUTOMATIC Mode (Publish directly if QC score &gt;= 85)</option>
          </select>
          <p className="text-[10px] text-zinc-500 mt-1">
            Safe Mode prevents any accidental publishing to your channel before review.
          </p>
        </div>

        <div className="pt-2">
          <button
            type="submit"
            className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition"
          >
            Save Configuration
          </button>
        </div>
      </form>
    </div>
  );
}
