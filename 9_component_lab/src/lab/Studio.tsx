import React, { useState, useEffect } from 'react';
import { LiveProvider, LiveError, LivePreview } from 'react-live';
import Editor from '@monaco-editor/react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { Save, Layout, Code2, Sparkles, Plus, Download, Upload, X, Globe, Box } from 'lucide-react';
import { cn } from '../lib/utils';
import { saveComponent, getStoredComponents, deleteComponent, getStoredPackages, savePackage, deletePackage } from '../lib/StudioRegistry';
import type { ExternalPackage } from '../lib/StudioRegistry';
import { Button } from '../components/ui/Button';
import { useLiveScope } from '../lib/dynamicRunner';

// Default code for new components
const INITIAL_CODE = `
import { motion } from 'framer-motion';
import confetti from 'canvas-confetti';

const CustomComponent = () => {
  const [count, setCount] = React.useState(0);
  
  const handleSuccess = () => {
    setCount(prev => prev + 1);
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 }
    });
  };

  if (!motion || !motion.button) {
    return <div className="p-4 text-red-500 font-bold bg-red-500/10 rounded-xl">Framer Motion is still loading...</div>;
  }

  return (
    <div className="p-8 rounded-3xl bg-indigo-500/10 border border-indigo-500/20 text-center space-y-4">
      <h2 className="text-2xl font-bold text-white tracking-tight">Interactive Prototype</h2>
      <p className="text-zinc-400">Build your logic with real-time feedback and dynamic npm imports.</p>
      <div className="flex justify-center gap-4">
        <motion.button 
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleSuccess}
          className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold transition-all"
        >
          Increment & Celebrate: {count}
        </motion.button>
      </div>
    </div>
  );
};

render(<CustomComponent />);
`.trim();

export default function Studio() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [code, setCode] = useState(INITIAL_CODE);
  const [name, setName] = useState('New Component');
  const [category, setCategory] = useState<'Basic Inputs' | 'Complex Components'>('Basic Inputs');
  const [isSaving, setIsSaving] = useState(false);
  const [packages, setPackages] = useState<ExternalPackage[]>([]);
  const [showPackageManager, setShowPackageManager] = useState(false);
  
  // New Package form
  const [newPkgName, setNewPkgName] = useState('');
  const [newPkgUrl, setNewPkgUrl] = useState('');

  useEffect(() => {
    setPackages(getStoredPackages());
    
    const queryParams = new URLSearchParams(location.search);
    const catParam = queryParams.get('category');

    if (id) {
      const stored = getStoredComponents();
      const comp = stored.find(c => c.id === id);
      if (comp) {
        setCode(comp.code);
        setName(comp.name);
        setCategory(comp.category);
      }
    } else {
      // Reset for new component
      setCode(INITIAL_CODE);
      setName('New Component');
      setCategory(catParam === 'Complex Components' ? 'Complex Components' : 'Basic Inputs');
    }
  }, [id, location.search]);

  const handleSave = () => {
    let finalName = name.trim();
    if (!id && (name === 'New Component' || !finalName)) {
        const timestamp = new Date().getTime().toString().slice(-4);
        finalName = `Component ${timestamp}`;
        setName(finalName);
    }

    setIsSaving(true);
    const newId = finalName.toLowerCase().replace(/\s+/g, '-');
    
    if (id && id !== newId) {
        deleteComponent(id);
    }

    saveComponent({
      id: newId,
      name: finalName,
      category,
      code
    });

    setTimeout(() => {
        setIsSaving(false);
        navigate(`/studio/${newId}`, { replace: true });
    }, 800);
  };

  const handleAddPackage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPkgName || !newPkgUrl) return;

    const pkg: ExternalPackage = {
      id: newPkgName.toLowerCase().replace(/\s+/g, '-'),
      name: newPkgName,
      url: newPkgUrl
    };

    savePackage(pkg);
    setPackages(getStoredPackages());
    setNewPkgName('');
    setNewPkgUrl('');
  };

  const handleDeletePackage = (pkgId: string) => {
    deletePackage(pkgId);
    setPackages(getStoredPackages());
  };

  const handleExportPackages = () => {
    const data = JSON.stringify(packages, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'studio-packages.json';
    a.click();
  };

  const handleImportPackages = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const imported = JSON.parse(event.target?.result as string);
        if (Array.isArray(imported)) {
          imported.forEach(pkg => savePackage(pkg));
          setPackages(getStoredPackages());
        }
      } catch (err) {
        alert('Invalid JSON file');
      }
    };
    reader.readAsText(file);
  };

  const baseScope = React.useMemo(() => {
    const R = (window as any).React;
    return { 
      React: R, 
      useState: R.useState,
      useEffect: R.useEffect,
      useMemo: R.useMemo,
      useCallback: R.useCallback,
      useRef: R.useRef,
      Button, 
      cn
    };
  }, []);
  const { scope, cleanCode, loading } = useLiveScope(code, baseScope, packages);

  return (
    <div className="flex-1 h-full flex flex-col animate-in fade-in duration-500 overflow-hidden">
      {/* Header Controls */}
      <div className="flex items-center justify-between px-6 py-4 shrink-0 border-b border-white/5 bg-black/20 backdrop-blur-md">
        <div className="flex items-center gap-4">
           <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
              <Sparkles className="w-5 h-5 text-indigo-400" />
           </div>
           <div>
              <input 
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="bg-transparent border-none text-2xl font-black text-white focus:outline-none focus:ring-0 p-0 placeholder:text-zinc-700 w-[400px]"
                placeholder="Component Name..."
                onFocus={(e) => { if(e.target.value === 'New Component') setName('') }}
              />
              <div className="flex bg-white/5 p-1 rounded-xl border border-white/5 mt-2 w-fit">
                 <button 
                   onClick={() => setCategory('Basic Inputs')}
                   className={cn(
                     "px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all duration-300",
                     category === 'Basic Inputs' 
                       ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20" 
                       : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                   )}
                 >
                   Basic Input
                 </button>
                 <button 
                   onClick={() => setCategory('Complex Components')}
                   className={cn(
                     "px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all duration-300",
                     category === 'Complex Components' 
                       ? "bg-purple-600 text-white shadow-lg shadow-purple-600/20" 
                       : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                   )}
                 >
                   Complex Component
                 </button>
              </div>
           </div>
        </div>

        <div className="flex items-center gap-6 shrink-0">
          {/* Library Manager Button */}
          <button 
            onClick={() => setShowPackageManager(true)}
            className="flex items-center gap-3 bg-zinc-900/50 hover:bg-zinc-800 p-2 pr-4 rounded-2xl border border-white/5 transition-all group"
          >
            <div className="p-1.5 rounded-xl bg-indigo-500/10 text-indigo-400 group-hover:scale-110 transition-transform">
               <Box className="w-4 h-4" />
            </div>
            <div className="text-left">
               <div className="text-[10px] font-black text-zinc-500 uppercase tracking-widest leading-none mb-1">Packages</div>
               <div className="text-[11px] font-bold text-white leading-none">{packages.length} External Imports</div>
            </div>
          </button>

          <div className="h-8 w-px bg-white/5" />

          <div className="flex items-center gap-3">
            {id && (
              <Button variant="outline" size="sm" onClick={() => navigate('/studio')} className="gap-2 border-white/5 bg-white/5">
                  <Plus className="w-4 h-4" /> Create New
              </Button>
            )}
            <Button size="sm" onClick={handleSave} disabled={isSaving} className="gap-2 bg-indigo-600 hover:bg-indigo-500 min-w-[140px]">
              <Save className={cn("w-4 h-4", isSaving && "animate-spin")} /> {isSaving ? 'Saving...' : 'Save Component'}
            </Button>
          </div>
        </div>
      </div>

      {/* Main Studio Area */}
      <div className="flex-1 flex min-h-0 relative h-full">
        <LiveProvider code={cleanCode} scope={scope} noInline={true}>
          {/* Left: Preview */}
          <div className="flex-1 flex flex-col border-r border-white/5 overflow-hidden">
            <div className="h-12 border-b border-white/5 px-6 flex items-center justify-between bg-zinc-900/50 shrink-0">
                <div className="flex items-center gap-2">
                    <Layout className="w-4 h-4 text-zinc-500" />
                    <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Live Canvas</span>
                </div>
                {loading && (
                  <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 text-[10px] font-bold animate-pulse">
                    Loading Packages...
                  </div>
                )}
            </div>
            <div className="flex-1 p-12 overflow-auto bg-dot-pattern">
              <LivePreview />
              <LiveError className="mt-4 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-mono" />
            </div>
          </div>

          {/* Right: Monaco Editor */}
          <div className="flex-1 flex flex-col bg-[#16161A] overflow-hidden shadow-2xl">
            <div className="h-12 border-b border-white/5 px-6 flex items-center gap-2 bg-zinc-900/50 shrink-0">
                <Code2 className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Source Logic</span>
            </div>
            <div className="flex-1">
                <Editor
                  height="100%"
                  defaultLanguage="javascript"
                  theme="vs-dark"
                  value={code}
                  onChange={(val: string | undefined) => setCode(val || '')}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 15,
                    fontFamily: 'JetBrains Mono, Menlo, monospace',
                    padding: { top: 20 },
                    scrollbar: { vertical: 'hidden' },
                    overviewRulerLanes: 0,
                    lineNumbers: 'on',
                    renderLineHighlight: 'none',
                    scrollBeyondLastLine: false,
                    wordWrap: 'on'
                  }}
                />
            </div>
          </div>
        </LiveProvider>
      </div>

      {/* Package Manager Modal */}
      {showPackageManager && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/80 backdrop-blur-sm animate-in fade-in duration-300">
           <div className="w-full max-w-2xl bg-[#16161A] border border-white/10 rounded-[32px] shadow-2xl overflow-hidden flex flex-col max-h-[80vh]">
              <div className="p-6 border-b border-white/5 flex items-center justify-between bg-zinc-900/50">
                 <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
                       <Box className="w-5 h-5" />
                    </div>
                    <div>
                       <h3 className="text-xl font-black text-white">Package Manager</h3>
                       <p className="text-xs font-bold text-zinc-500 uppercase tracking-widest">Manage external dependencies</p>
                    </div>
                 </div>
                 <div className="flex items-center gap-2">
                    <button 
                      onClick={handleExportPackages}
                      title="Export to JSON"
                      className="p-2 rounded-xl hover:bg-white/5 text-zinc-400 transition-colors"
                    >
                       <Download className="w-5 h-5" />
                    </button>
                    <label className="p-2 rounded-xl hover:bg-white/5 text-zinc-400 transition-colors cursor-pointer">
                       <Upload className="w-5 h-5" />
                       <input type="file" className="hidden" accept=".json" onChange={handleImportPackages} />
                    </label>
                    <button 
                      onClick={() => setShowPackageManager(false)}
                      className="p-2 rounded-xl hover:bg-red-500/10 text-zinc-400 hover:text-red-400 transition-colors ml-2"
                    >
                       <X className="w-5 h-5" />
                    </button>
                 </div>
              </div>

              <div className="flex-1 overflow-auto p-6 space-y-6">
                 {/* Add New Package */}
                 <form onSubmit={handleAddPackage} className="grid grid-cols-2 gap-4 bg-white/5 p-4 rounded-2xl border border-white/5">
                    <div className="space-y-2">
                       <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest ml-1">Package Name / ID</label>
                       <input 
                         value={newPkgName}
                         onChange={(e) => setNewPkgName(e.target.value)}
                         placeholder="framer-motion"
                         className="w-full bg-zinc-900 border border-white/10 rounded-xl px-4 py-2 text-sm text-white focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                       />
                    </div>
                    <div className="space-y-2">
                       <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest ml-1">URL or NPM Name</label>
                       <div className="flex gap-2">
                          <input 
                            value={newPkgUrl}
                            onChange={(e) => setNewPkgUrl(e.target.value)}
                            placeholder="framer-motion or https://..."
                            className="flex-1 bg-zinc-900 border border-white/10 rounded-xl px-4 py-2 text-sm text-white focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                          />
                          <button 
                            type="submit"
                            className="bg-indigo-600 hover:bg-indigo-500 text-white p-2 rounded-xl transition-colors"
                          >
                             <Plus className="w-5 h-5" />
                          </button>
                       </div>
                    </div>
                 </form>

                 {/* Package List */}
                 <div className="space-y-3">
                    <h4 className="text-[10px] font-black text-zinc-500 uppercase tracking-widest ml-1">Current Packages</h4>
                    <div className="grid gap-2">
                       {packages.map((pkg) => (
                         <div key={pkg.id} className="flex items-center justify-between p-3 rounded-2xl bg-zinc-900 border border-white/5 group hover:border-indigo-500/30 transition-all">
                            <div className="flex items-center gap-3">
                               <div className="p-2 rounded-xl bg-white/5 text-zinc-400 group-hover:text-indigo-400 transition-colors">
                                  <Globe className="w-4 h-4" />
                               </div>
                               <div>
                                  <div className="text-sm font-bold text-white">{pkg.name}</div>
                                  <div className="text-[10px] font-mono text-zinc-500 truncate max-w-[300px]">{pkg.url}</div>
                               </div>
                            </div>
                            <button 
                              onClick={() => handleDeletePackage(pkg.id)}
                              className="p-2 rounded-xl hover:bg-red-500/10 text-zinc-600 hover:text-red-500 transition-all opacity-0 group-hover:opacity-100"
                            >
                               <X className="w-4 h-4" />
                            </button>
                         </div>
                       ))}
                       {packages.length === 0 && (
                         <div className="text-center py-8 text-zinc-600 text-sm font-medium italic">
                            No packages added yet. Imports will be resolved via esm.sh by default.
                         </div>
                       )}
                    </div>
                 </div>
              </div>
              
              <div className="p-4 bg-indigo-500/5 border-t border-white/5">
                 <p className="text-[10px] text-indigo-400/60 font-medium text-center italic">
                    Note: If a URL is not provided, we automatically use esm.sh with external React support.
                 </p>
              </div>
           </div>
        </div>
      )}
    </div>
  );
}
