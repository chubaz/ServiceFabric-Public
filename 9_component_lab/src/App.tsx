import { BrowserRouter, Routes, Route, useParams, useNavigate } from 'react-router-dom';
import { Box, Layers, Sparkles } from 'lucide-react';
import LabLayout from './components/layout/LabLayout';
import { getComponentById } from './registry';
import CreatorGuide from './lab/CreatorGuide';
import Studio from './lab/Studio';
import DynamicLab from './lab/DynamicLab';

function Overview() {
  const navigate = useNavigate();
  
  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] text-center p-8 space-y-12 animate-in fade-in duration-700 slide-in-from-bottom-4">
      <div className="flex flex-col items-center space-y-4">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-700 flex items-center justify-center shadow-2xl shadow-indigo-500/20 rotate-3">
            <span className="text-white text-3xl font-black italic">FL</span>
        </div>
        <h1 className="text-6xl font-black tracking-tighter text-white">Fabric Studio</h1>
        <p className="text-lg text-zinc-500 max-w-md leading-relaxed">
          The ultimate playground for building and testing React components in real-time.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-2xl">
        <button 
          onClick={() => navigate('/studio?category=Basic Inputs')}
          className="group relative flex flex-col items-start p-8 rounded-3xl bg-[#0A0A0B] border border-white/5 hover:border-indigo-500/50 hover:bg-indigo-500/5 transition-all duration-300 text-left"
        >
          <div className="p-3 rounded-xl bg-indigo-500/10 mb-6 group-hover:scale-110 transition-transform">
            <Box className="w-6 h-6 text-indigo-400" />
          </div>
          <h3 className="text-xl font-bold text-white mb-2">Basic Component</h3>
          <p className="text-sm text-zinc-500 leading-relaxed">
            Create simple inputs, buttons, or primitive UI elements with focused logic.
          </p>
          <div className="mt-6 flex items-center gap-2 text-xs font-bold text-indigo-400 uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity">
            Start Building <Sparkles className="w-3 h-3" />
          </div>
        </button>

        <button 
          onClick={() => navigate('/studio?category=Complex Components')}
          className="group relative flex flex-col items-start p-8 rounded-3xl bg-[#0A0A0B] border border-white/5 hover:border-purple-500/50 hover:bg-purple-500/5 transition-all duration-300 text-left"
        >
          <div className="p-3 rounded-xl bg-purple-500/10 mb-6 group-hover:scale-110 transition-transform">
            <Layers className="w-6 h-6 text-purple-400" />
          </div>
          <h3 className="text-xl font-bold text-white mb-2">Complex Lab</h3>
          <p className="text-sm text-zinc-500 leading-relaxed">
            Architect interactive layouts, data-driven widgets, or multi-state systems.
          </p>
          <div className="mt-6 flex items-center gap-2 text-xs font-bold text-purple-400 uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity">
            Start Lab <Sparkles className="w-3 h-3" />
          </div>
        </button>
      </div>
    </div>
  );
}

function ComponentStage() {
  const { id } = useParams();
  const labDef = getComponentById(id || '');

  if (!labDef) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh] text-zinc-500 border border-dashed border-white/10 rounded-3xl">
        <p className="text-xl font-medium tracking-tight">Component <code className="text-indigo-400">"{id}"</code> not found in registry.</p>
      </div>
    );
  }

  const LabView = labDef.component;
  return (
    <div className="animate-in fade-in duration-500">
        <LabView />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LabLayout />}>
          <Route index element={<Overview />} />
          <Route path="docs" element={<CreatorGuide />} />
          <Route path="component/:id" element={<ComponentStage />} />
          <Route path="studio" element={<Studio />} />
          <Route path="studio/:id" element={<Studio />} />
          <Route path="lab/:id" element={<DynamicLab />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
