import { useState } from 'react';
import { Radio } from 'lucide-react';

export default function CommandModule() {
  const [selectedCommand, setSelectedCommand] = useState('FIRE_THRUSTERS');

  const commands = [
    'FIRE_THRUSTERS',
    'PURGE_LOGS',
    'REALIGN_SOLAR_ARRAY',
    'ACTIVATE_BEACON',
    'EMERGENCY_SHUTDOWN',
    'DEPLOY_PAYLOAD',
  ];

  const handleTransmit = () => {
    alert(`Command ${selectedCommand} transmitted successfully!`);
  };

  return (
    <div className="h-full rounded-2xl bg-golden-yellow p-6 text-black shadow-lg shadow-golden-yellow/20">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-black/10">
          <Radio className="h-6 w-6" />
        </div>
        <h2 className="text-2xl font-bold">Orbital Maneuvers</h2>
      </div>

      <div className="mb-4">
        <div className="inline-block rounded-full bg-black/20 px-3 py-1 text-xs font-semibold uppercase tracking-wider">
          NEXT IN 45 MINS
        </div>
      </div>

      <div className="mb-4">
        <p className="text-sm font-medium">Propulsion Check: SAT-402</p>
      </div>

      <div className="mb-4">
        <label
          htmlFor="command"
          className="mb-2 block text-sm font-semibold uppercase tracking-wide"
        >
          Select Command
        </label>
        <select
          id="command"
          value={selectedCommand}
          onChange={(e) => setSelectedCommand(e.target.value)}
          className="w-full rounded-lg border-2 border-black/20 bg-black/10 px-4 py-3 font-mono font-semibold focus:border-black/40 focus:outline-none"
        >
          {commands.map((cmd) => (
            <option key={cmd} value={cmd}>
              {cmd}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={handleTransmit}
        className="w-full rounded-lg border-2 border-black bg-black px-6 py-3 font-bold uppercase tracking-wide text-golden-yellow transition-all hover:bg-black/90 hover:shadow-lg"
      >
        Authorize Burn
      </button>
    </div>
  );
}
