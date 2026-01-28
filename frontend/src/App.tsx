import { useState } from 'react';
import AuthOverlay from './components/AuthOverlay';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import OrbitVisual from './components/OrbitVisual';
import CommandModule from './components/CommandModule';
import FleetIntegrity from './components/FleetIntegrity';
import TelemetryWidget from './components/TelemetryWidget';
import SecurityTerminal from './components/SecurityTerminal';
import NetworkSpeed from './components/NetworkSpeed';
import StatsCards from './components/StatsCards';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  return (
    <>
      {!isAuthenticated && <AuthOverlay onAuthenticate={() => setIsAuthenticated(true)} />}

      <div className="min-h-screen bg-[#0B0C10]">
        <Sidebar />

        <main className="ml-24 min-h-screen p-8">
          <Header />

          <div className="grid grid-cols-12 gap-6">
            <div className="col-span-7 row-span-2 glassmorphism rounded-2xl p-8">
              <OrbitVisual />
              <div className="mt-8">
                <StatsCards />
              </div>
            </div>

            <div className="col-span-5">
              <div className="grid grid-cols-2 gap-6">
                <div className="h-[280px]">
                  <CommandModule />
                </div>
                <div className="h-[280px]">
                  <FleetIntegrity />
                </div>
              </div>
            </div>

            <div className="col-span-5">
              <NetworkSpeed />
            </div>

            <div className="col-span-7">
              <TelemetryWidget />
            </div>

            <div className="col-span-5">
              <SecurityTerminal />
            </div>
          </div>
        </main>
      </div>
    </>
  );
}

export default App;
