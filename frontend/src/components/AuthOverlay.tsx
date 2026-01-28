import { useState } from 'react';
import { Sparkles } from 'lucide-react';

interface AuthOverlayProps {
  onAuthenticate: () => void;
}

export default function AuthOverlay({ onAuthenticate }: AuthOverlayProps) {
  const [operatorId, setOperatorId] = useState('');
  const [missionToken, setMissionToken] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (operatorId && missionToken) {
      onAuthenticate();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm">
      <div className="glassmorphism w-full max-w-md rounded-2xl p-8 shadow-2xl">
        <div className="mb-8 flex items-center justify-center">
          <div className="flex items-center gap-3">
            <Sparkles className="h-8 w-8 text-neon-green" />
            <h1 className="text-3xl font-bold text-white">VAJRA</h1>
          </div>
        </div>

        <div className="mb-6 text-center">
          <p className="text-sm uppercase tracking-wider text-gray-400">
            MISSION CONTROL ACCESS
          </p>
          <p className="mt-2 font-mono text-xs text-neon-green">
            [ SECURE AUTHENTICATION REQUIRED ]
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label
              htmlFor="operatorId"
              className="mb-2 block text-sm font-medium uppercase tracking-wide text-gray-300"
            >
              Operator ID
            </label>
            <input
              type="text"
              id="operatorId"
              value={operatorId}
              onChange={(e) => setOperatorId(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-black/50 px-4 py-3 font-mono text-white placeholder-gray-600 focus:border-neon-green focus:outline-none focus:ring-2 focus:ring-neon-green/50"
              placeholder="Enter your operator ID"
              required
            />
          </div>

          <div>
            <label
              htmlFor="missionToken"
              className="mb-2 block text-sm font-medium uppercase tracking-wide text-gray-300"
            >
              Mission Token (MFA)
            </label>
            <input
              type="password"
              id="missionToken"
              value={missionToken}
              onChange={(e) => setMissionToken(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-black/50 px-4 py-3 font-mono text-white placeholder-gray-600 focus:border-neon-green focus:outline-none focus:ring-2 focus:ring-neon-green/50"
              placeholder="Enter your mission token"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full rounded-lg bg-neon-green px-6 py-3 font-semibold uppercase tracking-wide text-black transition-all hover:bg-neon-green/90 hover:shadow-lg hover:shadow-neon-green/50"
          >
            Initialize Session
          </button>
        </form>

        <div className="mt-6 text-center font-mono text-xs text-gray-600">
          <p>SYSTEM STATUS: ONLINE</p>
          <p className="mt-1">ENCRYPTION: AES-256 ACTIVE</p>
        </div>
      </div>
    </div>
  );
}
