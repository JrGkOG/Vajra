export default function OrbitVisual() {
  return (
    <div className="relative flex h-full items-center justify-center">
      <div className="absolute inset-0 flex items-center justify-center opacity-10">
        <div className="grid grid-cols-8 gap-4">
          {Array.from({ length: 64 }).map((_, i) => (
            <div key={i} className="h-1 w-1 rounded-full bg-gray-700" />
          ))}
        </div>
      </div>

      <div className="relative">
        <div className="relative h-64 w-64">
          <div className="absolute inset-0 animate-spin-slow">
            <svg
              viewBox="0 0 200 200"
              className="h-full w-full"
              style={{ animationDuration: '20s' }}
            >
              <defs>
                <pattern
                  id="grid"
                  width="10"
                  height="10"
                  patternUnits="userSpaceOnUse"
                >
                  <path
                    d="M 10 0 L 0 0 0 10"
                    fill="none"
                    stroke="rgba(255,255,255,0.1)"
                    strokeWidth="0.5"
                  />
                </pattern>
              </defs>

              <circle
                cx="100"
                cy="100"
                r="60"
                fill="url(#grid)"
                stroke="rgba(255,255,255,0.3)"
                strokeWidth="1"
              />

              <ellipse
                cx="100"
                cy="100"
                rx="60"
                ry="15"
                fill="none"
                stroke="rgba(255,255,255,0.2)"
                strokeWidth="1"
              />
              <ellipse
                cx="100"
                cy="100"
                rx="60"
                ry="30"
                fill="none"
                stroke="rgba(255,255,255,0.15)"
                strokeWidth="1"
              />

              {Array.from({ length: 12 }).map((_, i) => {
                const angle = (i * 30 * Math.PI) / 180;
                const x1 = 100;
                const y1 = 100;
                const x2 = 100 + 60 * Math.cos(angle);
                const y2 = 100 + 60 * Math.sin(angle);
                return (
                  <line
                    key={i}
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    stroke="rgba(255,255,255,0.1)"
                    strokeWidth="0.5"
                  />
                );
              })}

              {Array.from({ length: 30 }).map((_, i) => {
                const lat = -75 + i * 5;
                const points = Array.from({ length: 36 })
                  .map((_, j) => {
                    const lon = j * 10;
                    const latRad = (lat * Math.PI) / 180;
                    const lonRad = (lon * Math.PI) / 180;
                    const r = 60 * Math.cos(latRad);
                    const x = 100 + r * Math.cos(lonRad);
                    const y = 100 + r * Math.sin(lonRad);
                    return `${x},${y}`;
                  })
                  .join(' ');
                return (
                  <polyline
                    key={`lat-${i}`}
                    points={points}
                    fill="none"
                    stroke="rgba(69, 248, 130, 0.2)"
                    strokeWidth="0.5"
                  />
                );
              })}
            </svg>
          </div>

          <div className="absolute left-[-20%] top-[20%] animate-orbit">
            <div className="relative h-8 w-16">
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="h-2 w-12 rounded-full bg-white shadow-lg shadow-white/50" />
              </div>
              <div className="absolute left-0 top-1/2 h-4 w-4 -translate-y-1/2 rounded-full bg-white shadow-lg shadow-white/50" />
              <div className="absolute right-0 top-1/2 h-3 w-6 -translate-y-1/2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div
                    key={i}
                    className="absolute h-0.5 bg-white/70"
                    style={{
                      width: '100%',
                      top: `${i * 50}%`,
                      left: '0',
                    }}
                  />
                ))}
              </div>
            </div>
          </div>

          <div className="absolute inset-0 animate-spin-slow opacity-30">
            <svg viewBox="0 0 200 200" className="h-full w-full">
              <ellipse
                cx="100"
                cy="100"
                rx="95"
                ry="35"
                fill="none"
                stroke="rgba(255,255,255,0.3)"
                strokeWidth="1"
                strokeDasharray="5,5"
              />
            </svg>
          </div>
        </div>

        <div className="absolute bottom-[-3rem] left-1/2 -translate-x-1/2 whitespace-nowrap">
          <div className="flex items-center gap-2 rounded-full border border-neon-green/30 bg-black/50 px-4 py-2 backdrop-blur-sm">
            <div className="h-2 w-2 animate-pulse rounded-full bg-neon-green" />
            <span className="font-mono text-sm text-neon-green">UPLINK ACTIVE</span>
          </div>
        </div>
      </div>

      <div className="absolute left-10 top-10 text-xs text-gray-600">+</div>
      <div className="absolute right-10 top-10 text-xs text-gray-600">+</div>
      <div className="absolute bottom-10 left-10 text-xs text-gray-600">+</div>
      <div className="absolute bottom-10 right-10 text-xs text-gray-600">+</div>
    </div>
  );
}
