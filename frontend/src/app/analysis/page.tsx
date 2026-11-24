"use client";

import React from "react";
import { Activity } from "lucide-react";
import { useStudio } from "@/context/StudioContext";

export default function AnalysisPage() {
  const { selectedVideo, handleStartAnalysis } = useStudio();

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-lg font-bold">Multi-Modal Video Intelligence Engine</h2>
          <p className="text-xs text-zinc-400">
            Active Video: {selectedVideo?.title || "Select a video from header or library"}
          </p>
        </div>
        {selectedVideo && (
          <button
            onClick={() => handleStartAnalysis(selectedVideo.id)}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition"
          >
            <Activity className="w-4 h-4" />
            Start Full Analysis
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <h4 className="text-xs font-bold text-zinc-400 mb-1">1. Audio Dynamics</h4>
          <p className="text-xs text-zinc-300">RMS Energy, Peaks &amp; Silence detection</p>
          <span className="text-[10px] text-emerald-400 mt-2 block font-mono">
            SoundFile + NumPy
          </span>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <h4 className="text-xs font-bold text-zinc-400 mb-1">2. Transcription</h4>
          <p className="text-xs text-zinc-300">Word-level timestamps &amp; VAD</p>
          <span className="text-[10px] text-emerald-400 mt-2 block font-mono">
            Faster-Whisper (CPU int8)
          </span>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <h4 className="text-xs font-bold text-zinc-400 mb-1">3. Scene Cuts</h4>
          <p className="text-xs text-zinc-300">Shot boundary transitions</p>
          <span className="text-[10px] text-emerald-400 mt-2 block font-mono">
            PySceneDetect ContentDetector
          </span>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <h4 className="text-xs font-bold text-zinc-400 mb-1">4. Visual Saliency</h4>
          <p className="text-xs text-zinc-300">Motion centroid &amp; activity indexing</p>
          <span className="text-[10px] text-emerald-400 mt-2 block font-mono">
            OpenCV 5.1
          </span>
        </div>
      </div>

      {selectedVideo ? (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 space-y-3">
          <h3 className="text-xs font-bold">Standardized Video Analysis Schema</h3>
          <div className="bg-zinc-950 p-4 rounded-lg font-mono text-[11px] text-zinc-400 overflow-x-auto max-h-96">
            <pre>
              {JSON.stringify(
                {
                  video_id: selectedVideo.id,
                  title: selectedVideo.title,
                  duration: selectedVideo.duration_seconds,
                  analysis_status: selectedVideo.analysis_status,
                  proxy_path: selectedVideo.proxy_path,
                  audio_path: selectedVideo.audio_path,
                  pipelines: [
                    "audio_rms",
                    "faster_whisper",
                    "scenedetect",
                    "opencv_motion",
                  ],
                },
                null,
                2
              )}
            </pre>
          </div>
        </div>
      ) : (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 text-center text-xs text-zinc-500">
          No video selected. Ingest or pick a video from Video Library.
        </div>
      )}
    </div>
  );
}
