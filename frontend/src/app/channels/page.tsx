"use client";

import React from "react";
import { Youtube } from "lucide-react";
import { useStudio } from "@/context/StudioContext";
import { api } from "@/lib/api";

export default function ChannelsPage() {
  const { channels, refreshAll, handleConnectOAuth } = useStudio();

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-lg font-bold">YouTube Account Integration</h2>
          <p className="text-xs text-zinc-400">
            Official Google OAuth 2.0 with AES-128 token encryption and safe publishing control.
          </p>
        </div>
        <button
          onClick={handleConnectOAuth}
          className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-lg shadow-red-600/20 transition"
        >
          <Youtube className="w-4 h-4" />
          Connect YouTube Channel
        </button>
      </div>

      {channels.length === 0 ? (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 text-center space-y-3">
          <Youtube className="w-12 h-12 text-zinc-600 mx-auto" />
          <h3 className="text-sm font-semibold">No YouTube Channels Connected</h3>
          <p className="text-xs text-zinc-400 max-w-md mx-auto">
            Connect your YouTube channel using Google OAuth 2.0 to enable official metadata sync, video discovery, and direct Shorts publishing.
          </p>
          <button
            onClick={handleConnectOAuth}
            className="inline-flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-white text-xs px-4 py-2 rounded-lg transition"
          >
            Connect Test / Production Channel
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {channels.map((ch) => (
            <div
              key={ch.id}
              className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-zinc-800 border border-zinc-700 overflow-hidden flex items-center justify-center font-bold text-lg">
                  {ch.thumbnail_url ? (
                    <img src={ch.thumbnail_url} alt={ch.title} className="w-full h-full object-cover" />
                  ) : (
                    ch.title.charAt(0)
                  )}
                </div>
                <div>
                  <h3 className="text-sm font-bold">{ch.title}</h3>
                  <p className="text-xs text-zinc-400 font-mono">{ch.custom_url || ch.channel_id}</p>
                  <div className="flex gap-3 text-[11px] text-zinc-500 mt-1">
                    <span>Subscribers: {ch.subscriber_count.toLocaleString()}</span>
                    <span>Videos: {ch.video_count}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-[11px] bg-emerald-950 text-emerald-400 border border-emerald-800 px-2.5 py-1 rounded-full font-medium">
                  Authorized
                </span>
                <button
                  onClick={() => api.revokeChannel(ch.id).then(refreshAll)}
                  className="text-xs text-zinc-500 hover:text-rose-400 p-2 rounded"
                  title="Revoke connection"
                >
                  Revoke
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
