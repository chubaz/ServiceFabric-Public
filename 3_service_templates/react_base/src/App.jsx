import React, { useState, useEffect } from 'react';
import { fabric } from '../../_shared/utils/fabric-client.ts';

export default function App({ context }) {
    const [items] = useState(context.data.items || []);
    const [isConnected, setIsConnected] = useState(false);
    const [latestEvent, setLatestEvent] = useState(null);
    const themeColor = context.state.theme_color || 'indigo';

    useEffect(() => {
        // Initialize Fabric Gateway connection
        fabric.connect();
        
        // Listen for real-time events
        const unsubscribe = fabric.onEvent((event) => {
            setLatestEvent(event);
            setIsConnected(true);
            
            // Auto-refresh logic if global sync is requested
            if (event.event === 'data_sync' || event.event === `${context.slug}_updated`) {
                handleTestSync();
            }
        });

        return () => unsubscribe();
    }, [context.slug]);

    const handleTestSync = async () => {
        try {
            // Using Fabric SDK call for orchestrated routing
            const data = await fabric.call(`/app/core/${context.slug}/api/sync`, {
                method: 'POST',
                body: JSON.stringify({ ping: 'pong', slug: context.slug })
            });
            console.log("Fabric Sync Success:", data);
        } catch (e) {
            console.error("Fabric Sync failed", e);
        }
    };

    return (
        <div className="p-8 min-h-screen bg-slate-50 text-slate-900 font-sans">
            
            {/* Fabric Gateway Status Bar */}
            <div className={`mb-6 flex items-center justify-between px-4 py-2 rounded-xl border text-[10px] font-bold uppercase tracking-widest transition-all ${isConnected ? 'bg-emerald-50 border-emerald-100 text-emerald-600' : 'bg-rose-50 border-rose-100 text-rose-600'}`}>
                <div className="flex items-center gap-2">
                    <span className={`relative flex h-2 w-2 ${isConnected ? 'animate-pulse' : ''}`}>
                        <span className={`inline-flex rounded-full h-2 w-2 ${isConnected ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
                    </span>
                    <span>{isConnected ? 'Fabric Gateway: Active' : 'Fabric Gateway: Connecting...'}</span>
                </div>
                
                {latestEvent && (
                    <div className="truncate max-w-xs opacity-60">
                        Event: {latestEvent.event}
                    </div>
                )}
            </div>

            <header className={`mb-10 border-b-4 border-${themeColor}-500 pb-6 flex justify-between items-center`}>
                <div>
                    <h1 className="text-4xl font-black tracking-tighter uppercase">{context.name}</h1>
                    <div className="flex items-center gap-3 mt-1">
                        <span className="text-xs font-mono text-slate-400">SHARD: {context.slug}</span>
                        <button 
                            onClick={() => fabric.broadcast(`${context.slug}_ping`, { timestamp: new Date() })}
                            className="text-[9px] text-blue-500 hover:underline font-bold"
                        >
                            [ Broadcast Pulse ]
                        </button>
                    </div>
                </div>
                <button 
                    onClick={handleTestSync}
                    className={`px-6 py-2 bg-${themeColor}-600 text-white rounded-full font-bold text-xs uppercase tracking-widest hover:shadow-lg transition-all active:scale-95`}
                >
                    Sync Node
                </button>
            </header>

            <main className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <section className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
                    <h2 className="text-[10px] font-black uppercase text-slate-400 tracking-[0.2em] mb-4">Initial DNA</h2>
                    <pre className="text-[11px] bg-slate-950 text-emerald-400 p-4 rounded-xl overflow-x-auto">
                        {JSON.stringify(context.state, null, 2)}
                    </pre>
                </section>

                <section className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
                    <h2 className="text-[10px] font-black uppercase text-slate-400 tracking-[0.2em] mb-4">Live Memory (app_data)</h2>
                    <div className="space-y-3">
                        {items.length > 0 ? items.map((item, i) => (
                            <div key={i} className="p-4 bg-slate-50 rounded-2xl border border-slate-100 flex justify-between group hover:border-blue-200 transition-colors">
                                <span className="font-bold">{item.label}</span>
                                <span className="text-slate-400 text-xs">ID: {item.id}</span>
                            </div>
                        )) : (
                            <div className="py-10 text-center border-2 border-dashed rounded-2xl text-slate-300 italic">
                                No records found in memory.
                            </div>
                        )}
                    </div>
                </section>
            </main>
        </div>
    );
}
