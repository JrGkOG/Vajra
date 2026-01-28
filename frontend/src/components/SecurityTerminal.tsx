import { useEffect, useState, useRef } from 'react';
import { Terminal } from 'lucide-react';

interface LogEntry {
  id: number;
  type: 'SYS' | 'AES-256' | 'KYBER' | 'NET';
  message: string;
  timestamp: string;
}

export default function SecurityTerminal() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const terminalRef = useRef<HTMLDivElement>(null);

  const logMessages = [
    { type: 'SYS' as const, message: 'Sharding Data Stream...' },
    { type: 'AES-256' as const, message: 'Encrypting Packet #4092...' },
    { type: 'KYBER' as const, message: 'Key Exchange Verified.' },
    { type: 'NET' as const, message: 'Uplink Bandwidth: 72.5 GB/s' },
    { type: 'SYS' as const, message: 'Satellite SAT-402 Online' },
    { type: 'AES-256' as const, message: 'Encrypting Packet #4093...' },
    { type: 'KYBER' as const, message: 'Quantum-Safe Protocol Active' },
    { type: 'NET' as const, message: 'Packet Loss: < 0.01%' },
    { type: 'SYS' as const, message: 'Memory Buffer: 89% Utilized' },
    { type: 'AES-256' as const, message: 'Encrypting Packet #4094...' },
    { type: 'KYBER' as const, message: 'Key Rotation Complete' },
    { type: 'NET' as const, message: 'Latency: 12ms' },
  ];

  useEffect(() => {
    let index = 0;
    const interval = setInterval(() => {
      const now = new Date();
      const timestamp = now.toTimeString().split(' ')[0];
      const logEntry: LogEntry = {
        id: Date.now(),
        ...logMessages[index % logMessages.length],
        timestamp,
      };
      setLogs((prev) => [...prev.slice(-15), logEntry]);
      index++;
    }, 1500);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'SYS':
        return 'text-blue-400';
      case 'AES-256':
        return 'text-neon-green';
      case 'KYBER':
        return 'text-purple-400';
      case 'NET':
        return 'text-yellow-400';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className="glassmorphism h-full rounded-2xl p-6">
      <div className="mb-4 flex items-center gap-3">
        <Terminal className="h-5 w-5 text-neon-green" />
        <h3 className="text-lg font-semibold text-white">Security Terminal</h3>
        <div className="ml-auto flex items-center gap-2">
          <div className="h-2 w-2 animate-pulse rounded-full bg-neon-green" />
          <span className="font-mono text-xs text-neon-green">LIVE</span>
        </div>
      </div>

      <div
        ref={terminalRef}
        className="h-64 overflow-y-auto rounded-lg bg-black/50 p-4 font-mono text-xs"
        style={{ scrollbarWidth: 'thin', scrollbarColor: '#45F882 #000' }}
      >
        {logs.map((log) => (
          <div key={log.id} className="mb-1 flex gap-3">
            <span className="text-gray-600">{log.timestamp}</span>
            <span className={`font-bold ${getTypeColor(log.type)}`}>[{log.type}]</span>
            <span className="text-gray-300">{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
