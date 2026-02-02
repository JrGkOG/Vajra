import React from 'react';
import { Github, Globe } from 'lucide-react';

export const Footer = () => {
    return (
        <footer className="bg-black text-white py-8 border-t-8 border-black mt-12">
            <div className="max-w-6xl mx-auto">
                <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                    {/* Left: Project Info */}
                    <div className="text-center md:text-left">
                        <p className="font-mono font-bold text-lg mb-1">VAJRA</p>
                        <p className="text-sm font-mono opacity-80">Satellite Telemetry Exchange • 2026</p>
                    </div>

                    {/* Center: Social Links */}
                    <div className="flex gap-4">
                        <a
                            href="https://github.com/jrgkog"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-3 bg-brutal-pink border-5 border-white text-white hover:bg-white hover:text-brutal-pink shadow-hard-sm hover:shadow-hard hover:-translate-y-1 transition-all"
                            aria-label="GitHub"
                        >
                            <Github size={24} />
                        </a>
                        <a
                            href="https://jrgk.me"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-3 bg-brutal-blue border-5 border-white text-white hover:bg-white hover:text-brutal-blue shadow-hard-sm hover:shadow-hard hover:-translate-y-1 transition-all"
                            aria-label="Portfolio"
                        >
                            <Globe size={24} />
                        </a>
                    </div>
                </div>
            </div>
        </footer>
    );
};
