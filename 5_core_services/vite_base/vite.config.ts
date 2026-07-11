import { defineConfig } from 'vite';
import { svelte, vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

const APP_ROOT = process.env.TARGET_APP_ROOT || process.cwd();
const OUT_DIR = process.env.TARGET_OUT_DIR;
const IS_WATCH = process.env.BUILD_MODE === 'WATCH';

export default defineConfig({
    root: APP_ROOT,

    plugins: [
        tailwindcss(),
        svelte({
            configFile: false,
            preprocess: vitePreprocess(),
            compilerOptions: {
                // runes: true,
                // Critical: Prevents stripping of init code during dev/watch
                dev: IS_WATCH
            }
        })
    ],

    worker: {
        format: 'es',
        rollupOptions: {
            external: ['pyodide', '@duckdb/duckdb-wasm']
        }
    },

    resolve: {
        alias: {
            '@fabric/shared': path.resolve(APP_ROOT, '..', '_shared'),
            '@': path.resolve(APP_ROOT, 'src')
        },
        dedupe: ['svelte']
    },

    build: {
        outDir: OUT_DIR,
        emptyOutDir: false, // CRITICAL: Don't wipe the folder, keep old assets available
        // Disable minification in WATCH mode to make debugging readable
        minify: IS_WATCH ? false : 'esbuild',
        reportCompressedSize: false, // Faster builds
        chunkSizeWarningLimit: 2000,
        rollupOptions: {
            input: path.resolve(APP_ROOT, 'src/main.ts'),
            external: [/^node:.*/], // Explicitly externalize node: built-ins
            output: {
                entryFileNames: 'assets/index.js',
                chunkFileNames: 'assets/[name].js',
                assetFileNames: 'assets/[name].[ext]'
            }
        }
    },

    server: {
        fs: {
            allow: [
                path.resolve(APP_ROOT, '..'),
                '/app/builder/node_modules'
            ]
        },
        watch: {
            usePolling: true,
            interval: 100
        }
    }
});