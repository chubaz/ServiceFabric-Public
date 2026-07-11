<script lang="ts">
    import { onMount } from 'svelte';
    import { fabric } from '../../_shared/utils/fabric-client.ts';

    let { context } = $props();
    
    let entities = $state([]);
    let loading = $state(false);
    let fabricConnected = $state(false);
    let latestEvent = $state(null);

    onMount(async () => {
        fabric.connect();
        
        fabric.onEvent((event) => {
            latestEvent = event;
            fabricConnected = true;
        });

        // Test API Call
        try {
            loading = true;
            entities = await fabric.call(`/app/core/${context.slug}/api/entities`);
        } catch (e) {
            console.warn("Fabric Initial Call failed (optional):", e);
        } finally {
            loading = false;
        }
    });
</script>

<div class="min-h-screen bg-slate-900 text-slate-100 p-8 font-sans">
    <!-- Fabric Header -->
    <header class="mb-12 flex justify-between items-center">
        <div>
            <div class="flex items-center gap-2 mb-2">
                <div class="w-3 h-3 rounded-full {fabricConnected ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]' : 'bg-rose-500 animate-pulse'}"></div>
                <h1 class="text-2xl font-black tracking-tighter uppercase italic">{context.name}</h1>
            </div>
            <p class="text-slate-400 text-xs font-mono uppercase tracking-widest">Shard ID: {context.slug}</p>
        </div>

        <div class="bg-slate-800/50 border border-slate-700/50 px-4 py-2 rounded-lg text-right">
            <span class="block text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">Gateway Status</span>
            <span class="text-sm font-mono {fabricConnected ? 'text-emerald-400' : 'text-rose-400'}">
                {fabricConnected ? 'CONNECTED' : 'OFFLINE'}
            </span>
        </div>
    </header>

    <main class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Sidebar: Event Log -->
        <section class="lg:col-span-1 space-y-6">
            <div class="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-xl">
                <h2 class="text-xs font-bold text-slate-500 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                    <span class="w-2 h-2 bg-blue-500 rounded-full"></span>
                    Real-Time Fabric Stream
                </h2>
                
                <div class="space-y-3 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
                    {#if latestEvent}
                        <div class="bg-slate-900/50 border-l-2 border-blue-500 p-3 rounded-r-lg animate-in slide-in-from-right duration-300">
                            <span class="block text-[10px] text-blue-400 font-bold mb-1 uppercase tracking-tighter">Event: {latestEvent.event}</span>
                            <pre class="text-[10px] font-mono text-slate-300 overflow-x-hidden whitespace-pre-wrap">
                                {JSON.stringify(latestEvent.data, null, 2)}
                            </pre>
                        </div>
                    {:else}
                        <div class="py-12 text-center text-slate-600 italic text-sm">
                            Waiting for global events...
                        </div>
                    {/if}
                </div>
            </div>

            <!-- Dashboard Mockup -->
            <div class="grid grid-cols-2 gap-4">
                <div class="bg-slate-800/50 border border-slate-700 p-4 rounded-xl">
                    <span class="block text-[10px] text-slate-500 font-bold uppercase mb-1">Entities</span>
                    <span class="text-2xl font-bold">{entities.length}</span>
                </div>
                <div class="bg-slate-800/50 border border-slate-700 p-4 rounded-xl">
                    <span class="block text-[10px] text-slate-500 font-bold uppercase mb-1">Latency</span>
                    <span class="text-2xl font-bold">12ms</span>
                </div>
            </div>
        </section>

        <!-- Main Content: Data View -->
        <section class="lg:col-span-2">
            <div class="bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden h-full">
                <div class="p-6 border-b border-slate-700 flex justify-between items-center bg-slate-800/50">
                    <h3 class="font-bold text-slate-200">Shared Repository</h3>
                    <button class="bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold px-4 py-2 rounded-lg transition-all active:scale-95 shadow-lg shadow-blue-500/20">
                        REFRESH
                    </button>
                </div>

                <div class="p-0">
                    {#if loading}
                        <div class="py-32 flex flex-col items-center gap-4">
                            <div class="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                            <span class="text-xs font-bold text-slate-500 uppercase tracking-widest">Hydrating Core...</span>
                        </div>
                    {:else if entities.length > 0}
                        <table class="w-full text-left text-sm">
                            <thead class="bg-slate-900/50 text-slate-500 uppercase text-[10px] font-bold tracking-widest">
                                <tr>
                                    <th class="px-6 py-4">Entity</th>
                                    <th class="px-6 py-4">ID</th>
                                    <th class="px-6 py-4">Value</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-700/50">
                                {#each entities as item}
                                    <tr class="hover:bg-slate-700/30 transition-colors">
                                        <td class="px-6 py-4 font-bold text-slate-300">{item.name || 'Untitled'}</td>
                                        <td class="px-6 py-4 text-slate-500 font-mono text-xs">0x{item.id}</td>
                                        <td class="px-6 py-4">
                                            <span class="bg-slate-900 px-2 py-1 rounded border border-slate-700 text-blue-400 font-mono text-xs">
                                                {item.value || 0}
                                            </span>
                                        </td>
                                    </tr>
                                {/each}
                            </tbody>
                        </table>
                    {:else}
                        <div class="py-32 text-center">
                            <p class="text-slate-500 mb-4">No entities found in this shard.</p>
                            <button class="text-xs font-bold text-blue-400 hover:text-blue-300 underline underline-offset-4">
                                Initialize Sample Data
                            </button>
                        </div>
                    {/if}
                </div>
            </div>
        </section>
    </main>
</div>

<style>
    .custom-scrollbar::-webkit-scrollbar {
        width: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
        background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 10px;
    }
</style>
