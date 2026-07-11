import express from 'express';
import { exec } from 'child_process';

const app = express();
app.use(express.json()); // Ensure we can parse JSON from the Watcher
const PORT = process.env.MANAGEMENT_PORT || 3000;

console.log(`\n🏭 FABRIC VITE MANAGEMENT SERVER v1.1`);
console.log(`=====================================`);

/**
 * Triggers the build process by executing builder.js in ONCE mode.
 * Supports optional surgical build for a specific target shard.
 */
const triggerBuild = (target = null) => {
    const timestamp = new Date().toISOString();
    const modeDesc = target ? `SURGICAL BUILD for [${target}]` : "FULL CATALOG BUILD";
    
    console.log(`[${timestamp}] 🔄 ${modeDesc} triggered. Launching builder...`);
    
    // Pass the target to the builder process via Environment Variable
    const env = { 
        ...process.env, 
        BUILD_MODE: 'ONCE',
        TARGET_SHARD: target || "" 
    };

    exec('node builder.js', { 
        env: env,
        maxBuffer: 20 * 1024 * 1024 // 20MB buffer for logs
    }, (error, stdout, stderr) => {
        if (error) {
            console.error(`❌ [BUILD ERROR] ${error.message}`);
            return;
        }
        if (stderr) {
            console.warn(`⚠️ [BUILD WARNING] ${stderr}`);
        }
        console.log(`✅ [BUILD SUCCESS] ${modeDesc} finished.\n${stdout}`);
    });
};

// Endpoint to intercept reload commands
app.post('/_internal/reload', (req, res) => {
    const target = req.body.target || null;
    const msg = target ? `Surgical build for ${target}` : 'Full catalog reload';
    
    console.log(`📡 [HTTP] Received POST /_internal/reload - Target: ${target || "ALL"}`);
    
    // Trigger build in background with slight delay to ensure fast HTTP 202 response
    setTimeout(() => {
        triggerBuild(target);
    }, 500);

    res.status(202).json({
        status: 'Accepted',
        message: msg,
        timestamp: new Date().toISOString()
    });
});

// Health check endpoint
app.get('/health', (req, res) => res.status(200).send('OK'));

app.listen(PORT, () => {
    console.log(`🚀 Management server listening on port ${PORT}`);
    
    // Initial build pass on startup
    triggerBuild();
});
