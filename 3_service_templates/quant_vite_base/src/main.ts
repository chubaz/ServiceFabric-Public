import { mount } from 'svelte';
import App from './App.svelte';
import './app.css';

/**
 * Service Fabric Svelte Mounter
 * Handles initial mount and remounting after HTMX swaps.
 */
function initApp() {
    // Recupero del contesto globale iniettato
    const context = (window as any)[`SF_CONTEXT_{{APP_SLUG}}`] || {
        name: "Quant Vite Shard",
        slug: "default",
        state: {},
        data: {}
    };

    const targetId = `svelte-mount-${context.slug}`;
    const target = document.getElementById(targetId);

    // Prevent double mounting
    if (target && !target.hasAttribute('data-svelte-mounted')) {
        target.innerHTML = ''; // Clear any stale content
        mount(App, { 
            target,
            props: { context }
        });
        target.setAttribute('data-svelte-mounted', 'true');
        console.log(`[SF] Quant App '${context.slug}' mounted successfully.`);
    }
}

// 1. Try mounting immediately
initApp();

// 2. Listen for HTMX swaps or custom signals to remount if the DOM was replaced
document.addEventListener('sf:mount', (e: any) => {
    if (!e.detail || e.detail.slug === '{{APP_SLUG}}') {
        initApp();
    }
});
