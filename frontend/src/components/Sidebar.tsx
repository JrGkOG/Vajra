import { Sparkles, BarChart3, Globe2, AlertTriangle, Cpu, Settings } from 'lucide-react';

export default function Sidebar() {
  return (
    <div className="fixed left-0 top-0 h-screen w-24 border-r border-gray-800 bg-[#0B0C10] flex flex-col items-center py-8">
      <div className="mb-12">
        <Sparkles className="h-8 w-8 text-golden-yellow" />
      </div>

      <nav className="flex flex-col gap-8">
        <button className="group flex h-12 w-12 items-center justify-center rounded-lg bg-white/5 transition-all hover:bg-white/10">
          <BarChart3 className="h-5 w-5 text-gray-400 group-hover:text-white" />
        </button>

        <button className="group flex h-12 w-12 items-center justify-center rounded-lg transition-all hover:bg-white/10">
          <Globe2 className="h-5 w-5 text-gray-400 group-hover:text-white" />
        </button>

        <button className="group flex h-12 w-12 items-center justify-center rounded-lg transition-all hover:bg-white/10">
          <AlertTriangle className="h-5 w-5 text-gray-400 group-hover:text-white" />
        </button>

        <button className="group flex h-12 w-12 items-center justify-center rounded-lg transition-all hover:bg-white/10">
          <Cpu className="h-5 w-5 text-gray-400 group-hover:text-white" />
        </button>

        <button className="group flex h-12 w-12 items-center justify-center rounded-lg transition-all hover:bg-white/10">
          <Settings className="h-5 w-5 text-gray-400 group-hover:text-white" />
        </button>
      </nav>
    </div>
  );
}
