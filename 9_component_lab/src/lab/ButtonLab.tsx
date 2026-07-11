import { useState } from 'react';
import { Button } from '../components/ui/Button';
import { Settings, Play, Trash2, Github, ExternalLink, Loader2 } from 'lucide-react';

export default function ButtonLab() {
  const [loading, setLoading] = useState(false);

  return (
    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-2 duration-500">
      <div className="space-y-4">
        <h1 className="text-4xl font-black tracking-tight text-white">Button Architecture</h1>
        <p className="text-zinc-400 max-w-2xl text-lg leading-relaxed">
          The core interactive primitive. Supports 6 semantic variants and 3 sizing scales.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-10">
        {/* Style Variations */}
        <div className="space-y-6">
          <div className="flex items-center gap-2">
             <div className="w-1.5 h-6 bg-indigo-500 rounded-full" />
             <h3 className="text-sm font-bold uppercase tracking-[0.2em] text-zinc-500">Style Variations</h3>
          </div>
          <div className="p-10 rounded-[2rem] bg-[#16161A] border border-white/5 flex flex-wrap gap-6 items-center">
            <Button variant="default">Primary Action</Button>
            <Button variant="premium">Premium Feature</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost Trigger</Button>
            <Button variant="destructive">Delete Item</Button>
          </div>
        </div>

        {/* Real-World Mockups */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-6">
                <div className="flex items-center gap-2">
                    <div className="w-1.5 h-6 bg-purple-500 rounded-full" />
                    <h3 className="text-sm font-bold uppercase tracking-[0.2em] text-zinc-500">Sizing Scales</h3>
                </div>
                <div className="p-8 rounded-[2rem] bg-[#16161A] border border-white/5 flex items-center justify-center gap-6">
                    <Button size="sm">Small</Button>
                    <Button size="default">Standard</Button>
                    <Button size="lg">Large Size</Button>
                </div>
            </div>

            <div className="space-y-6">
                <div className="flex items-center gap-2">
                    <div className="w-1.5 h-6 bg-emerald-500 rounded-full" />
                    <h3 className="text-sm font-bold uppercase tracking-[0.2em] text-zinc-500">Icon Support</h3>
                </div>
                <div className="p-8 rounded-[2rem] bg-[#16161A] border border-white/5 flex items-center justify-center gap-6">
                    <Button size="icon" variant="outline"><Settings className="w-4 h-4" /></Button>
                    <Button className="gap-2"><Play className="w-4 h-4" /> Start Studio</Button>
                    <Button variant="destructive" className="gap-2"><Trash2 className="w-4 h-4" /> Delete</Button>
                </div>
            </div>
        </div>

        {/* Interactive States */}
        <div className="space-y-6">
          <div className="flex items-center gap-2">
             <div className="w-1.5 h-6 bg-amber-500 rounded-full" />
             <h3 className="text-sm font-bold uppercase tracking-[0.2em] text-zinc-500">Behavioral States</h3>
          </div>
          <div className="p-10 rounded-[2rem] bg-gradient-to-br from-[#16161A] to-[#0A0A0B] border border-white/5 flex flex-wrap gap-8 items-center justify-center">
            <div className="flex flex-col items-center gap-3">
                 <Button disabled>Permanently Disabled</Button>
                 <span className="text-[10px] text-zinc-600 font-bold uppercase tracking-widest">Disabled</span>
            </div>
            
            <div className="flex flex-col items-center gap-3">
                <Button 
                    variant="premium"
                    className="min-w-[160px]"
                    disabled={loading} 
                    onClick={() => {
                        setLoading(true);
                        setTimeout(() => setLoading(false), 3000);
                    }}
                >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Async Execution"}
                </Button>
                <span className="text-[10px] text-zinc-600 font-bold uppercase tracking-widest">Interactive Loading</span>
            </div>
          </div>
        </div>
      </div>

      {/* Code Inspector Placeholder */}
      <div className="p-8 rounded-[2rem] bg-indigo-500/5 border border-indigo-500/10 flex items-center justify-between">
          <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center">
                  <Github className="text-indigo-400 w-6 h-6" />
              </div>
              <div>
                  <h4 className="font-bold text-white">Source Architecture</h4>
                  <p className="text-zinc-500 text-sm">View the TypeScript definition for this component.</p>
              </div>
          </div>
          <Button variant="outline" className="gap-2">
              <ExternalLink className="w-4 h-4" /> Open Source
          </Button>
      </div>
    </div>
  );
}
