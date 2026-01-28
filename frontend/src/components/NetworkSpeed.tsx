import { Activity } from 'lucide-react';

export default function NetworkSpeed() {
  return (
    <div className="glassmorphism rounded-2xl p-6">
      <div className="mb-4 flex items-center gap-3">
        <Activity className="h-5 w-5 text-neon-green" />
        <h3 className="text-lg font-semibold text-white">Network Speed</h3>
      </div>

      <div className="mb-6">
        <div className="flex items-baseline gap-2">
          <span className="font-mono text-5xl font-bold text-white">72.5</span>
          <span className="text-2xl font-light text-gray-400">GB/s</span>
        </div>
      </div>

      <div className="relative h-32 overflow-hidden rounded-lg bg-black/50">
        <svg className="h-full w-full" viewBox="0 0 300 100" preserveAspectRatio="none">
          <defs>
            <linearGradient id="graphGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#45F882" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#45F882" stopOpacity="0" />
            </linearGradient>
          </defs>

          <polyline
            fill="url(#graphGradient)"
            stroke="#45F882"
            strokeWidth="2"
            points="0,80 30,75 60,65 90,70 120,50 150,55 180,45 210,40 240,35 270,30 300,25 300,100 0,100"
          />
        </svg>

        <div className="absolute bottom-4 left-4 right-4 flex items-end justify-between">
          <div className="text-center">
            <div className="font-mono text-sm font-bold text-white">21.10</div>
            <div className="font-mono text-xs text-gray-400">GB/s</div>
          </div>
          <div className="text-center">
            <div className="font-mono text-sm font-bold text-neon-green">49.32</div>
            <div className="font-mono text-xs text-gray-400">GB/s</div>
          </div>
        </div>
      </div>

      <div className="mt-4 flex items-center gap-2 text-xs text-gray-400">
        <div className="h-2 w-2 rounded-full bg-gray-600" />
        <span>Global</span>
      </div>

      <p className="mt-2 text-xs text-gray-500">
        Measure uplink/downlink efficiency across regions
      </p>
    </div>
  );
}
