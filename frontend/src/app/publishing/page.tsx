"use client";

import React from "react";
import { useStudio } from "@/context/StudioContext";

export default function PublishingPage() {
  const { shorts, channels, handlePublish } = useStudio();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-bold">YouTube Publishing Engine</h2>
          <p className="text-xs text-zinc-400">
            Safe Mode (Human Review) vs Automatic Mode (QC Gate Pass).
          </p>
        </div>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        {shorts.length === 0 ? (
          <div className="py-12 text-center text-xs text-zinc-500">
            No generated shorts in the queue yet.
          </div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-950/80 border-b border-zinc-800 text-zinc-400 font-mono text-[11px]">
              <tr>
                <th className="p-4">Short Title</th>
                <th className="p-4">Status</th>
                <th className="p-4">Channel</th>
                <th className="p-4">Target / Published ID</th>
                <th className="p-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {shorts.map((s) => (
                <tr key={s.id} className="hover:bg-zinc-800/30 transition">
                  <td className="p-4 font-semibold text-zinc-200 max-w-xs truncate">
                    {s.title}
                  </td>
                  <td className="p-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
                        s.status === "published"
                          ? "bg-emerald-950 text-emerald-400 border-emerald-800"
                          : s.status === "approved"
                          ? "bg-indigo-950 text-indigo-400 border-indigo-800"
                          : "bg-zinc-800 text-zinc-400 border-zinc-700"
                      }`}
                    >
                      {s.status}
                    </span>
                  </td>
                  <td className="p-4 text-zinc-400">
                    {channels[0]?.title || "Default Channel"}
                  </td>
                  <td className="p-4 font-mono text-zinc-500">
                    {s.status === "published"
                      ? `yt_short_${s.id.substring(0, 8)}`
                      : "Pending Upload"}
                  </td>
                  <td className="p-4">
                    {s.status !== "published" && (
                      <button
                        onClick={() => handlePublish(s.id, "SAFE")}
                        className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                      >
                        Publish Now
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
