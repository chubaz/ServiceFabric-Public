import { Rocket, FileCode, Palette, Zap } from 'lucide-react';

export default function CreatorGuide() {
  const steps = [
    {
      title: "Scaffold UI",
      desc: "Create your raw component in `src/components/ui/` using Tailwind and Headless UI for accessibility.",
      icon: FileCode
    },
    {
      title: "Isolated Sandbox",
      desc: "Create a wrapper file in `src/lab/` to mock every possible state (loading, error, empty, active).",
      icon: Palette
    },
    {
      title: "Register",
      desc: "Add your component definition to `src/registry.ts` to make it appear in the sidebar instantly.",
      icon: Zap
    }
  ];

  return (
    <div className="max-w-7xl mx-auto p-12 w-full space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-bold uppercase tracking-wider">
           Studio Guide
        </div>
        <h1 className="text-5xl font-extrabold tracking-tight text-white leading-tight">
          How to build <span className="text-indigo-500">World-Class</span> components.
        </h1>
        <p className="text-xl text-zinc-400 max-w-2xl leading-relaxed">
          The Component Lab is an isolated workshop. Components are crafted here to perfection before they ever touch the main application code.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {steps.map((step, i) => (
          <div key={i} className="p-8 rounded-2xl bg-[#16161A] border border-white/5 hover:border-indigo-500/30 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-zinc-900 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <step.icon className="w-6 h-6 text-indigo-500" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">{step.title}</h3>
            <p className="text-zinc-400 text-sm leading-relaxed">{step.desc}</p>
          </div>
        ))}
      </div>

      <div className="p-1 rounded-2xl bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500">
          <div className="bg-[#0E0E10] rounded-[14px] p-8 flex items-center justify-between">
              <div className="space-y-2">
                  <h3 className="text-2xl font-bold text-white">Ready to deploy?</h3>
                  <p className="text-zinc-400">Your components are automatically shared across all apps in the Service Fabric.</p>
              </div>
              <Rocket className="w-10 h-10 text-white animate-bounce" />
          </div>
      </div>
    </div>
  );
}
