import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';

const CATALOG = '/app/services_catalog';
const DIST = '/app/dist';
const BUILDER_MODULES = '/app/builder/node_modules';
const CATALOG_MODULES = path.join(CATALOG, 'node_modules');

const MODE = process.env.BUILD_MODE || 'WATCH'; 
const VITE_BIN = '/app/builder/node_modules/.bin/vite';
const MASTER_CONFIG = '/app/builder/vite.config.ts';
const TARGET_SHARD = process.env.TARGET_SHARD || null;

console.log(`\n⚛️  FABRIC REACT BUILDER v1.2 (Zero-Downtime Edition)`);
console.log(`===================================================`);

// 1. SYMLINK INJECTION
try {
    if (!fs.existsSync(CATALOG_MODULES)) {
        fs.symlinkSync(BUILDER_MODULES, CATALOG_MODULES, 'dir');
    }
} catch (e) {}

// 2. Identify React Apps
let apps = fs.readdirSync(CATALOG).filter(dir => {
    if (dir.startsWith('_') || dir.startsWith('.')) return false;
    const hasJsx = fs.existsSync(path.join(CATALOG, dir, 'src/main.jsx'));
    const hasTsx = fs.existsSync(path.join(CATALOG, dir, 'src/main.tsx'));
    return hasJsx || hasTsx;
});

if (TARGET_SHARD && apps.includes(TARGET_SHARD)) {
    apps = [TARGET_SHARD];
}

// 3. Atomic Build Function
const runBuild = (app) => {
    return new Promise((resolve) => {
        const finalDist = path.join(DIST, app);
        const tempDist = `${finalDist}.tmp`;

        console.log(`🔨 [${app}] Starting atomic build...`);
        
        if (fs.existsSync(tempDist)) fs.rmSync(tempDist, { recursive: true, force: true });

        const child = spawn(VITE_BIN, ['build', '--config', MASTER_CONFIG], {
            stdio: 'inherit',
            env: {
                ...process.env,
                TARGET_APP_ROOT: path.join(CATALOG, app),
                TARGET_OUT_DIR: tempDist
            }
        });

        child.on('close', (code) => {
            if (code === 0) {
                try {
                    if (fs.existsSync(finalDist)) {
                        const oldDist = `${finalDist}.old`;
                        if (fs.existsSync(oldDist)) fs.rmSync(oldDist, { recursive: true, force: true });
                        fs.renameSync(finalDist, oldDist);
                    }
                    fs.renameSync(tempDist, finalDist);
                    console.log(`✅ [${app}] Atomic swap complete.`);
                } catch (e) {
                    console.error(`❌ [${app}] Swap failed: ${e.message}`);
                }
            } else {
                console.error(`❌ [${app}] Build failed with code ${code}. Check the logs above for errors.`);
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

const BUILD_INTERVAL = parseInt(process.env.BUILD_INTERVAL || '300') * 1000;

if (MODE === 'ONCE' || TARGET_SHARD) {
    runAllSequentially().then(() => process.exit(0));
} else if (MODE === 'WATCH') {
    const loop = async () => {
        console.log(`\n🕒 [WATCH] Next full build pass in ${BUILD_INTERVAL/1000}s...`);
        await new Promise(r => setTimeout(r, BUILD_INTERVAL));
        await runAllSequentially();
        loop();
    };
    runAllSequentially().then(loop);
} else {
    runAllSequentially();
}
