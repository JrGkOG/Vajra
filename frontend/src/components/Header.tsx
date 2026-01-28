import { Sparkles, TrendingDown, Bell, ChevronDown } from 'lucide-react';

export default function Header() {
  return (
    <header className="mb-8 flex items-center justify-between">
      <div>
        <div className="mb-2 flex items-center gap-3">
          <Sparkles className="h-6 w-6 text-golden-yellow" />
          <h1 className="text-3xl font-bold text-white">Welcome back, Operator</h1>
        </div>
        <div className="flex items-center gap-3 font-mono text-sm text-gray-400">
          <span className="uppercase">VAJRA IS STABLE</span>
          <TrendingDown className="h-4 w-4 text-neon-green" />
          <span className="text-neon-green">1.2MS</span>
          <span className="uppercase">TODAY</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="rounded-lg p-2 transition-colors hover:bg-white/10">
          <Bell className="h-5 w-5 text-gray-400" />
        </button>

        <div className="flex items-center gap-3 rounded-lg bg-white/5 px-4 py-2">
          <div className="h-10 w-10 overflow-hidden rounded-full bg-gradient-to-br from-neon-green to-blue-500">
            <img
              src="https://images.pexels.com/photos/614810/pexels-photo-614810.jpeg?auto=compress&cs=tinysrgb&w=100"
              alt="Operator"
              className="h-full w-full object-cover"
            />
          </div>
          <div className="text-left">
            <div className="text-sm font-semibold text-white">Mission Operator</div>
            <div className="text-xs text-gray-400">Senior Analyst</div>
          </div>
          <ChevronDown className="h-4 w-4 text-gray-400" />
        </div>
      </div>
    </header>
  );
}
