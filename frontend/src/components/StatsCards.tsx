export default function StatsCards() {
  return (
    <div className="grid grid-cols-3 gap-6">
      <div className="glassmorphism rounded-xl p-4">
        <div className="mb-1 text-sm text-gray-400">Packet Loss</div>
        <div className="flex items-baseline gap-2">
          <span className="font-mono text-xl font-bold text-neon-green">{'< 0.01%'}</span>
          <span className="font-mono text-xs text-neon-green">( -0.08% )</span>
        </div>
      </div>

      <div className="glassmorphism rounded-xl p-4">
        <div className="mb-1 text-sm text-gray-400">Min Latency</div>
        <div className="font-mono text-xl font-bold text-white">12ms</div>
      </div>

      <div className="glassmorphism rounded-xl p-4">
        <div className="mb-1 text-sm text-gray-400">Peak Throughput</div>
        <div className="font-mono text-xl font-bold text-white">126GB/s</div>
      </div>
    </div>
  );
}
