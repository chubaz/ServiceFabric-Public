<script>
    import { onMount } from 'svelte';
    import { fabric } from '../../_shared/utils/fabric-client.ts';

    // Props from Fabric Loader
    let { app_slug = "{{APP_SLUG}}" } = $props();
    const APP_NAME = "{{APP_NAME}}";

    // --- State ---
    let prices = $state([]);
    let status = $state("Node Active");
    let lastSignal = $state(null);
    
    // Aggregated Dashboard State
    let activeStrategies = $state({});
    
    // Derived total value using Svelte 5 runes
    let totalPortfolioValue = $derived(
        Object.values(activeStrategies).reduce((sum, strat) => sum + strat.value, 0)
    );

    onMount(() => {
        // 1. Subscribe to local shard updates
        fabric.onEvent("price_update", (data) => {
            prices = [...prices, data].slice(-20);
        });

        fabric.onEvent("signal_alert", (data) => {
            if(data.slug === app_slug) lastSignal = data.msg;
        });

        // 2. Subscribe to Global Portfolio Updates
        // This catches ticks from ANY quant shard in the system
        const unsubscribe = fabric.onEvent("portfolio_pnl_update", (data) => {
            activeStrategies[data.slug] = {
                value: data.total_value,
                pnl: data.daily_pnl_perc,
                lastUpdated: new Date(data.timestamp * 1000).toLocaleTimeString()
            };
        });

        return () => unsubscribe();
    });

    async function triggerBacktest() {
        status = "Processing Engine...";
        const res = await fetch(`/app/core/${app_slug}/api/backtest-results`);
        status = "Pipeline Complete";
    }
</script>

<main class="quant-terminal p-6 bg-slate-950 text-slate-300 min-h-screen font-sans">
    <header class="mb-8 border-b border-white/10 pb-6 flex justify-between items-end">
        <div>
            <h1 class="text-3xl font-black text-white uppercase tracking-tighter">{{APP_NAME}}</h1>
            <p class="text-xs text-slate-500 uppercase tracking-widest mt-1">Fabric Terminal Hub</p>
        </div>
        <div class="text-right">
            <span class="text-[10px] font-black text-slate-500 uppercase block mb-1">Total Net Liquidity</span>
            <span class="text-4xl font-black text-indigo-500 font-mono">
                ${totalPortfolioValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </span>
        </div>
    </header>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Dashboard: Strategy List -->
        <section class="lg:col-span-2 card bg-slate-900/50 p-6 rounded-2xl border border-white/5">
            <h2 class="text-[10px] font-black uppercase text-slate-500 tracking-[0.2em] mb-6">Active Data Streams</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                {#each Object.entries(activeStrategies) as [slug, strat]}
                    <div class="bg-slate-950/50 border border-white/5 p-4 rounded-xl flex justify-between items-center group hover:border-indigo-500/30 transition-all">
                        <div>
                            <h3 class="font-bold text-sm text-indigo-400 uppercase">{slug}</h3>
                            <p class="text-[9px] text-slate-600">Tick: {strat.lastUpdated}</p>
                        </div>
                        <div class="text-right">
                            <p class="text-base font-bold text-white">${strat.value.toLocaleString()}</p>
                            <p class="text-[10px] font-mono {strat.pnl >= 0 ? 'text-emerald-500' : 'text-rose-500'}">
                                {strat.pnl >= 0 ? '▲' : '▼'} {Math.abs(strat.pnl)}%
                            </p>
                        </div>
                    </div>
                {:else}
                    <div class="col-span-2 py-12 text-center border border-dashed border-white/10 rounded-2xl">
                        <p class="text-xs text-slate-600 animate-pulse uppercase tracking-widest font-bold">Waiting for strategy data...</p>
                    </div>
                {/each}
            </div>
        </section>

        <!-- Sidebar: Controls & Feed -->
        <div class="space-y-6">
            <section class="card bg-slate-900/50 p-6 rounded-2xl border border-white/5">
                <h2 class="text-[10px] font-black uppercase text-slate-500 tracking-[0.2em] mb-4">Operations</h2>
                <button 
                    onclick={triggerBacktest}
                    class="w-full py-3 bg-amber-500 text-slate-950 font-black rounded-xl uppercase text-xs hover:bg-amber-400 transition-all shadow-lg shadow-amber-500/10"
                >
                    Run Local Backtest
                </button>
            </section>

            <section class="card bg-slate-900/50 p-6 rounded-2xl border border-white/5 flex flex-col h-64">
                <h2 class="text-[10px] font-black uppercase text-slate-500 tracking-[0.2em] mb-4">Fabric Live Feed</h2>
                <div class="space-y-2 flex-1 overflow-y-auto no-scrollbar font-mono text-[10px]">
                    {#each prices as tick}
                        <div class="flex justify-between border-b border-white/5 py-1">
                            <span class="text-slate-500">{tick.ticker || 'TICK'}</span>
                            <span class="text-emerald-500">${tick.value}</span>
                        </div>
                    {/each}
                </div>
            </section>
        </div>
    </div>

    {#if lastSignal}
        <div class="fixed bottom-6 right-6 p-4 bg-indigo-500 text-slate-950 rounded-2xl shadow-2xl font-black uppercase text-[10px] tracking-widest animate-bounce border-4 border-slate-950">
            System Alert: {lastSignal}
        </div>
    {/if}
</main>

<style>
    .no-scrollbar::-webkit-scrollbar { display: none; }
</style>
