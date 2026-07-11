import { mount } from 'svelte';
import DevFabricAgent from '../components/DevFabricAgent.svelte';

/**
 * Service Fabric Agent Mounter
 * Checks for an existing agent and mounts it if not found.
 */
export function mountDevAgent() {
    const AGENT_ID = 'dev-fabric-agent-container';
    
    // 1. Prevent multiple instances
    if (document.getElementById(AGENT_ID)) {
        console.log('⚡ DevFabric Agent already mounted.');
        return;
    }

    // 2. Create target container
    const container = document.createElement('div');
    container.id = AGENT_ID;
    document.body.appendChild(container);

    // 3. Instantiate Svelte Component (Svelte 5 API)
    try {
        mount(DevFabricAgent, {
            target: container
        });
        console.log('🚀 DevFabric Agent mounted successfully.');
    } catch (error) {
        console.error('❌ Failed to mount DevFabric Agent:', error);
    }
}

// Auto-execute if this script is loaded directly
if (typeof window !== 'undefined') {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', mountDevAgent);
    } else {
        mountDevAgent();
    }
}
