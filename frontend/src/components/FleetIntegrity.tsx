import { Target } from 'lucide-react';

export default function FleetIntegrity() {
  return (
    <div className="h-full rounded-2xl bg-white p-6 shadow-lg">
      <div className="mb-6 flex items-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
          <Target className="h-6 w-6 text-gray-800" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900">Fleet Integrity</h2>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-gray-200 pb-3">
          <span className="text-sm font-medium text-gray-600">Active Satellites</span>
          <span className="font-mono text-lg font-bold text-gray-900">142/142</span>
        </div>

        <div className="flex items-center justify-between border-b border-gray-200 pb-3">
          <span className="text-sm font-medium text-gray-600">Power Systems</span>
          <span className="inline-block rounded-full bg-neon-green px-3 py-1 text-xs font-bold uppercase text-black">
            NOMINAL
          </span>
        </div>

        <button className="w-full rounded-lg border-2 border-gray-900 bg-white px-6 py-3 font-semibold text-gray-900 transition-all hover:bg-gray-50">
          System Diagnostics
        </button>
      </div>
    </div>
  );
}
