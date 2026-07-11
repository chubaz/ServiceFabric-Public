import { build } from 'vite';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const appName = process.argv[2];

if (!appName) {
    console.error('❌ Error: Please provide an app name as the first argument.');
    process.exit(1);
}

const CATALOG_PATH = '/app/services_catalog';
const appPath = path.resolve(CATALOG_PATH, appName);
const outDir = path.resolve(appPath, 'dist');
const masterConfig = path.resolve(__dirname, 'vite.config.ts');

if (!fs.existsSync(appPath)) {
    console.error(`❌ Error: App folder not found at ${appPath}`);
    process.exit(1);
}

async function runBuild() {
    console.log(`🔨 Building single app: ${appName}...`);
    try {
        await build({
            configFile: masterConfig,
            root: appPath,
            build: {
                outDir: outDir,
                emptyOutDir: true,
                rollupOptions: {
                    input: path.resolve(appPath, 'src/main.ts'),
                }
            },
            // Ensure we pass the dynamic root to plugins if needed
            define: {
                'process.env.TARGET_APP_ROOT': JSON.stringify(appPath)
            }
        });
        console.log(`✅ Build successful! Output: ${outDir}`);
    } catch (error) {
        console.error(`❌ Build failed for ${appName}:`, error.message);
        process.exit(1);
    }
}

runBuild();
