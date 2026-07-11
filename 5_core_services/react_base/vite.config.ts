import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import fs from 'fs';

const APP_ROOT = process.env.TARGET_APP_ROOT || process.cwd();
const OUT_DIR = process.env.TARGET_OUT_DIR;
const IS_WATCH = process.env.BUILD_MODE === 'WATCH';

// Look for TSX first, fallback to JSX
const getEntryPoint = () => {
    const tsxPath = path.resolve(APP_ROOT, 'src/main.tsx');
    if (fs.existsSync(tsxPath)) return tsxPath;
    return path.resolve(APP_ROOT, 'src/main.jsx');
};

export default defineConfig({
    root: APP_ROOT,
    plugins: [react()],
    resolve: {
        preserveSymlinks: true,
        extensions: ['.mts', '.ts', '.jsx', '.tsx', '.mjs', '.js', '.json'],
        alias: {
            '@fabric/shared': '/app/services_catalog/_shared',
            '@': path.resolve(APP_ROOT, 'src')
        }
    },
    build: {
        outDir: OUT_DIR,
        emptyOutDir: false, // CRITICAL: Don't wipe the folder
        minify: IS_WATCH ? false : 'esbuild',
        rollupOptions: {
            input: getEntryPoint(),
            output: {
                entryFileNames: 'assets/index.js',
                chunkFileNames: 'assets/[name].js',
                assetFileNames: 'assets/[name].[ext]'
            }
        }
    }
});
