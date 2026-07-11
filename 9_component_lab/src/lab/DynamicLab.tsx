import * as React from 'react';
import { useParams, Link } from 'react-router-dom';
import { LiveProvider, LivePreview, LiveError } from 'react-live';
import { getStoredComponents, getStoredPackages } from '../lib/StudioRegistry';
import type { ExternalPackage } from '../lib/StudioRegistry';
import { Edit3, ArrowLeft, Layers, Calendar, Trash2 } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { cn } from '../lib/utils';
import { useLiveScope } from '../lib/dynamicRunner';

export default function DynamicLab() {
  const { id } = useParams();
  const [packages, setPackages] = React.useState<ExternalPackage[]>([]);
  const components = getStoredComponents();
  const comp = components.find(c => c.id === id);

  React.useEffect(() => {
    setPackages(getStoredPackages());
  }, []);

  if (!comp) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-center space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-red-500/10 flex items-center justify-center">
            <Trash2 className="w-8 h-8 text-red-500" />
        </div>
        <div className="space-y-2">
            <h2 className="text-2xl font-bold text-white">Component Expired or Not Found</h2>
            <p className="text-zinc-500">This dynamic component doesn't exist in your local studio registry.</p>
        </div>
        <Link to="/studio">
            <Button variant="outline">Back to Studio</Button>
        </Link>
      </div>
    );
  }

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
  
  const { scope, cleanCode, loading } = useLiveScope(comp.code, baseScope, packages);

  return (
    <div className="max-w-7xl mx-auto p-12 w-full space-y-12 animate-in fade-in slide-in-from-bottom-2 duration-500">
      <div className="flex items-center justify-between">
        <div className="space-y-4">
            <div className="flex items-center gap-3">
                <Link to="/" className="p-2 rounded-lg hover:bg-white/5 transition-colors text-zinc-500 hover:text-white">
                    <ArrowLeft className="w-4 h-4" />
                </Link>
                <div className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-bold uppercase tracking-widest">
                    {comp.category}
                </div>
            </div>
            <h1 className="text-4xl font-black tracking-tight text-white">{comp.name}</h1>
            <div className="flex items-center gap-6 text-zinc-500 text-sm">
                <div className="flex items-center gap-2">
                    <Layers className="w-4 h-4" />
                    <span>Dynamic Instance</span>
                </div>
                <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    <span>Last updated: {new Date(comp.updatedAt).toLocaleDateString()}</span>
                </div>
                {loading && (
                  <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 text-[10px] font-bold animate-pulse">
                    Loading Packages...
                  </div>
                )}
            </div>
        </div>

        <Link to={`/studio/${comp.id}`}>
            <Button className="gap-2 bg-indigo-600 hover:bg-indigo-500 shadow-xl shadow-indigo-600/20">
                <Edit3 className="w-4 h-4" /> Edit Logic
            </Button>
        </Link>
      </div>

      <div className="p-12 rounded-[2.5rem] bg-[#16161A] border border-white/5 relative overflow-hidden group">
        <div className="absolute inset-0 bg-dot-pattern opacity-50" />
        <div className="relative z-10 flex items-center justify-center min-h-[300px]">
          <LiveProvider code={cleanCode} scope={scope} noInline={true}>
            <LivePreview />
            <LiveError className="mt-8 p-6 rounded-3xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-mono whitespace-pre-wrap" />
          </LiveProvider>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="p-8 rounded-[2rem] bg-zinc-900/30 border border-white/5 space-y-4">
              <h4 className="text-sm font-bold text-white uppercase tracking-widest">Metadata</h4>
              <pre className="text-xs text-zinc-500 font-mono bg-black/20 p-4 rounded-xl">
{JSON.stringify({
  id: comp.id,
  name: comp.name,
  category: comp.category,
  environment: "Browser Runtime"
}, null, 2)}
              </pre>
          </div>
          <div className="p-8 rounded-[2rem] bg-indigo-500/5 border border-indigo-500/10 flex flex-col justify-center text-center space-y-4">
                <p className="text-indigo-200/60 text-sm leading-relaxed">
                    This component is running in a live isolated environment. All state and interactions are fully functional.
                </p>
          </div>
      </div>
    </div>
  );
}
