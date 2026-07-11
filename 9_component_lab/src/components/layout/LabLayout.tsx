import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function LabLayout() {
  return (
    <div className="flex h-screen bg-[#0E0E10] text-zinc-100 overflow-hidden font-sans selection:bg-indigo-500/30">
      <Sidebar />
      <main className="flex-1 overflow-auto relative">
        {/* Figma Grid Pattern */}
        <div className="absolute inset-0 bg-[#0E0E10] bg-[radial-gradient(#222_1px,transparent_1px)] [background-size:24px_24px] pointer-events-none" />
        
        <div className="relative z-10 h-full flex flex-col">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
