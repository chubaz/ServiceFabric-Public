import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';

// --- CONFIGURATION ---
const CATALOG = '/app/services_catalog';
const DIST = '/app/dist';
const BUILDER_MODULES = '/app/builder/node_modules';
const CATALOG_MODULES = path.join(CATALOG, 'node_modules');

const MODE = process.env.BUILD_MODE || 'WATCH'; 
const VITE_BIN = '/app/builder/node_modules/.bin/vite';
const MASTER_CONFIG = '/app/builder/vite.config.ts';
const TARGET_SHARD = process.env.TARGET_SHARD || null;

console.log(`\n🏭 FABRIC BUILDER v3.3 (Zero-Downtime Edition)`);
console.log(`===========================================`);

// 1. SYMLINK INJECTION
try {
    if (!fs.existsSync(CATALOG_MODULES)) {
        fs.symlinkSync(BUILDER_MODULES, CATALOG_MODULES, 'dir');
    }
} catch (e) {}

// 2. Identify Apps
let apps = fs.readdirSync(CATALOG).filter(dir => {
    if (dir.startsWith('_') || dir.startsWith('.')) return false;
    return fs.existsSync(path.join(CATALOG, dir, 'src/main.ts'));
});

if (TARGET_SHARD && apps.includes(TARGET_SHARD)) {
    apps = [TARGET_SHARD];
}

// 3. Atomic Build Function
const runBuild = (app) => {
    return new Promise((resolve) => {
        const finalDist = path.join(DIST, app);
        const tempDist = `${finalDist}.tmp`; // Build to temporary folder

        console.log(`🔨 [${app}] Starting atomic build...`);
        
        // Ensure temp dir is clean
        if (fs.existsSync(tempDist)) fs.rmSync(tempDist, { recursive: true, force: true });

        const child = spawn(VITE_BIN, ['build', '--config', MASTER_CONFIG], {
            stdio: 'inherit',
            env: {
                ...process.env,
                TARGET_APP_ROOT: path.join(CATALOG, app),
                TARGET_OUT_DIR: tempDist, // Redirect output to temp
                NODE_OPTIONS: '--max-old-space-size=4096'
            }
        });

        child.on('close', (code) => {
            if (code === 0) {
                // ATOMIC SWAP: Replace production folder with temp folder
                try {
                    if (fs.existsSync(finalDist)) {
                        const oldDist = `${finalDist}.old`;
                        if (fs.existsSync(oldDist)) fs.rmSync(oldDist, { recursive: true, force: true });
                        fs.renameSync(finalDist, oldDist); // Move current to .old
                    }
                    fs.renameSync(tempDist, finalDist); // Move new to production
                    console.log(`✅ [${app}] Atomic swap complete. Assets updated.`);
                } catch (e) {
                    console.error(`❌ [${app}] Swap failed: ${e.message}`);
                }
            } else {
                console.error(`❌ [${app}] Build failed. Keeping old assets.`);
            }
            resolve();
        });
    });
};

const runAllSequentially = async () => {
    for (const app of apps) {
        await runBuild(app);
    }
};

// Start Execution
if (MODE === 'ONCE' || TARGET_SHARD) {
    runAllSequentially().then(() => process.exit(0));
} else {
    // In background modes, don't block the management server
    runAllSequentially();
}
