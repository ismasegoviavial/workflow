import React from 'react';
import { Menu, Share2, HelpCircle } from 'lucide-react';

interface HeaderProps {
  onBackToApp?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onBackToApp }) => {
  return (
    <header className="h-12 bg-[#1a73e8] text-white flex items-center justify-between px-3 select-none z-30 shadow-md">
      {/* Left section: Logo & App Title */}
      <div className="flex items-center space-x-3">
        <button 
          className="p-1 hover:bg-blue-700 rounded transition-colors text-white"
          title="Menú Principal"
        >
          <Menu className="w-5 h-5" />
        </button>
        
        {/* Google Cloud Data Fusion Studio Brand */}
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded bg-white/20 flex items-center justify-center font-bold text-xs tracking-wider text-white">
            CDF
          </div>
          <span className="font-medium text-base tracking-wide flex items-center space-x-1.5">
            <span>Cloud Data Fusion</span>
            <span className="text-blue-200 font-light">|</span>
            <span className="font-normal text-blue-100">Studio</span>
          </span>
        </div>
      </div>

      {/* Right section: Links & Edition Badge */}
      <div className="flex items-center space-x-5 text-xs font-medium tracking-wider">
        <button className="text-blue-100 hover:text-white transition-colors uppercase">
          DASHBOARD
        </button>
        <button className="text-blue-100 hover:text-white transition-colors uppercase">
          HUB
        </button>
        <button className="text-blue-100 hover:text-white transition-colors uppercase">
          SYSTEM ADMIN
        </button>

        <div className="h-4 w-px bg-blue-400/50" />

        <button className="p-1 text-blue-100 hover:text-white hover:bg-blue-700 rounded transition-colors" title="Compartir">
          <Share2 className="w-4 h-4" />
        </button>

        <button className="p-1 text-blue-100 hover:text-white hover:bg-blue-700 rounded transition-colors" title="Ayuda">
          <HelpCircle className="w-4 h-4" />
        </button>

        {/* Edition Badge */}
        <div className="bg-blue-800/80 border border-blue-400/40 text-blue-100 px-2.5 py-1 rounded text-[11px] font-semibold flex items-center space-x-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Basic Edition</span>
        </div>
      </div>
    </header>
  );
};
