<script>
    import { onMount } from 'svelte';

    let isCollapsed = $state(true);
    let command = $state('');
    let messages = $state([]);
    let socket;
    let terminalContainer;

    // Dynamically parse app context from URL (e.g., /anki-cards/ -> anki-cards)
    const getAppContext = () => {
        const path = window.location.pathname;
        const parts = path.split('/').filter(Boolean);
        return parts[0] || 'core';
    };

    const scrollToBottom = () => {
        if (terminalContainer) {
            setTimeout(() => {
                terminalContainer.scrollTop = terminalContainer.scrollHeight;
            }, 50);
        }
    };

    const connect = () => {
        socket = new WebSocket('ws://localhost:9090/agent-stream');

        socket.onopen = () => {
            messages.push({ type: 'system', text: 'Connected to DevFabric Agent.' });
            scrollToBottom();
        };

        socket.onmessage = (event) => {
            messages.push({ type: 'agent', text: event.data });
            scrollToBottom();
        };

        socket.onclose = () => {
            messages.push({ type: 'error', text: 'Disconnected. Retrying in 5s...' });
            setTimeout(connect, 5000);
            scrollToBottom();
        };
    };

    const submitCommand = () => {
        if (!command.trim() || !socket || socket.readyState !== WebSocket.OPEN) return;

        const payload = {
            cmd: command,
            app_context: getAppContext()
        };

        messages.push({ type: 'user', text: `> ${command}` });
        socket.send(JSON.stringify(payload));
        command = '';
        scrollToBottom();
    };

    onMount(() => {
        connect();
    });
</script>

<div class="fixed bottom-4 right-4 z-[9999] font-mono transition-all duration-300 {isCollapsed ? 'w-12 h-12' : 'w-96 h-[500px]'}">
    {#if isCollapsed}
        <button 
            onclick={() => isCollapsed = false}
            class="w-full h-full bg-slate-900 border-2 border-emerald-500 rounded-full flex items-center justify-center shadow-xl hover:scale-110 transition-transform text-emerald-500"
            title="Open DevFabric Agent"
        >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 14 4-4"/><path d="m3.34 19 1.4-1.4"/><path d="m3.34 5 1.4 1.4"/><path d="m19.26 19-1.4-1.4"/><path d="m19.26 5-1.4 1.4"/><path d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z"/></svg>
        </button>
    {:else}
        <div class="w-full h-full bg-slate-950 border-2 border-emerald-500/50 rounded-lg flex flex-col shadow-2xl overflow-hidden backdrop-blur-md">
            <!-- Header -->
            <div class="bg-slate-900 px-3 py-2 border-b border-emerald-500/30 flex justify-between items-center">
                <span class="text-xs text-emerald-400 font-bold tracking-widest uppercase">DevFabric Agent</span>
                <button onclick={() => isCollapsed = true} class="text-emerald-500 hover:text-emerald-300">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                </button>
            </div>

            <!-- Terminal Area -->
            <div 
                bind:this={terminalContainer}
                class="flex-1 p-3 overflow-y-auto space-y-2 scrollbar-thin scrollbar-thumb-emerald-500/20"
            >
                {#each messages as msg}
                    <div class="text-sm leading-relaxed break-words">
                        {#if msg.type === 'user'}
                            <span class="text-emerald-300 font-bold">{msg.text}</span>
                        {:else if msg.type === 'system'}
                            <span class="text-blue-400 italic">[{msg.text}]</span>
                        {:else if msg.type === 'error'}
                            <span class="text-rose-500">!! {msg.text}</span>
                        {:else}
                            <span class="text-emerald-500/90">{msg.text}</span>
                        {/if}
                    </div>
                {/each}
            </div>

            <!-- Input Area -->
            <div class="p-3 bg-slate-900 border-t border-emerald-500/30">
                <div class="flex items-center gap-2">
                    <span class="text-emerald-500">$</span>
                    <input 
                        type="text" 
                        bind:value={command}
                        onkeydown={(e) => e.key === 'Enter' && submitCommand()}
                        placeholder="Ask agent..."
                        class="bg-transparent border-none outline-none text-emerald-400 text-sm flex-1 placeholder:text-emerald-900"
                    />
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    /* Custom scrollbar for matrix feel */
    .scrollbar-thin::-webkit-scrollbar {
        width: 4px;
    }
    .scrollbar-thin::-webkit-scrollbar-track {
        background: transparent;
    }
    .scrollbar-thin::-webkit-scrollbar-thumb {
        background: rgba(16, 185, 129, 0.2);
        border-radius: 2px;
    }
</style>
