import { useState } from 'react';
import { CheckCircle2, ArrowRight } from 'lucide-react';

export default function TelemetryWidget() {
  const [imageRevealed, setImageRevealed] = useState(false);

  return (
    <div className="glassmorphism rounded-2xl p-8">
      <div className="mb-6">
        <p className="mb-2 text-sm uppercase tracking-wider text-gray-400">
          Total Downlink Volume (24h)
        </p>
        <div className="flex items-baseline gap-4">
          <h1 className="font-mono text-6xl font-bold text-white">243.575</h1>
          <span className="text-4xl font-light text-gray-400">TB</span>
        </div>
      </div>

      <div className="mb-6 flex items-center gap-2">
        <CheckCircle2 className="h-4 w-4 text-neon-green" />
        <span className="inline-block rounded-full border border-neon-green/30 bg-neon-green/10 px-3 py-1 text-sm font-medium text-neon-green">
          Normal
        </span>
      </div>

      {!imageRevealed ? (
        <button
          onClick={() => setImageRevealed(true)}
          className="group flex items-center gap-2 rounded-lg bg-white/10 px-6 py-3 font-semibold uppercase tracking-wide text-white transition-all hover:bg-white/20"
        >
          Decode Feed
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
        </button>
      ) : (
        <div className="rounded-lg border border-neon-green/30 bg-black/50 p-4">
          <div className="mb-2 flex items-center gap-2">
            <div className="h-2 w-2 animate-pulse rounded-full bg-neon-green" />
            <span className="font-mono text-xs text-neon-green">DECODED IMAGE</span>
          </div>
          <img
            src="https://images.pexels.com/photos/2159/flight-sky-earth-space.jpg?auto=compress&cs=tinysrgb&w=600"
            alt="Decoded satellite feed"
            className="w-full rounded-lg"
          />
        </div>
      )}
    </div>
  );
}
