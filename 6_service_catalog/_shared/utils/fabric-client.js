/**
 * FabricClient (Vanilla JS): Standard SDK for interacting with the Service Fabric Gateway.
 * Handles real-time WebSockets, broadcast events, and API coordination.
 */

class FabricClient {
    constructor(clientIdPrefix = 'app', config = {}) {
        this.clientId = `${clientIdPrefix}_${Math.floor(Math.random() * 10000)}`;
        this.config = {
            baseUrl: config.baseUrl || window.location.origin,
            apiPrefix: config.apiPrefix || '/api/v1',
            wsPrefix: config.wsPrefix || '/api/v1/ws/events',
        };
        this.socket = null;
        this.listeners = new Set();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    /**
     * Connects to the Fabric Gateway WebSocket.
     */
    connect() {
        if (this.socket) return;

        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}${this.config.wsPrefix}/${this.clientId}`;

        console.log(`[Fabric] Attempting connection to ${wsUrl}`);
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log(`[Fabric] Connected as ${this.clientId}`);
            this.reconnectAttempts = 0;
            this._notify('fabric_connected', { clientId: this.clientId });
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this._notify(data.event || 'message', data);
            } catch (e) {
                // Handle non-JSON welcome strings
                this._notify('raw_message', { content: event.data });
            }
        };

        this.socket.onclose = () => {
            this.socket = null;
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
                console.warn(`[Fabric] Disconnected. Reconnecting in ${delay}ms...`);
                setTimeout(() => this.connect(), delay);
            }
        };

        this.socket.onerror = (err) => {
            console.error('[Fabric] WebSocket Error:', err);
        };
    }

    /**
     * Sends a structured event to the hub.
     */
    broadcast(event, data = {}) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const payload = {
                event: event,
                data: data,
                source: this.clientId,
                timestamp: new Date().toISOString()
            };
            this.socket.send(JSON.stringify(payload));
        } else {
            console.error('[Fabric] Cannot broadcast: Connection is not active.');
        }
    }

    /**
     * Standardized fetch wrapper for Gateway-aware requests.
     */
    async call(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${this.config.baseUrl}${endpoint}`;
        
        const defaultHeaders = {
            'Content-Type': 'application/json',
            'X-Fabric-Client-Id': this.clientId,
        };

        const response = await fetch(url, {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(`[Fabric] API Call Failed: ${error.detail || response.statusText}`);
        }

        return response.json();
    }

    /**
     * Subscribe to incoming events.
     */
    onEvent(callback) {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    _notify(event, data) {
        const fabricEvent = {
            event: event,
            data: data.data || data,
            source: data.source || 'gateway',
            timestamp: data.timestamp || new Date().toISOString()
        };
        this.listeners.forEach(cb => cb(fabricEvent));
    }
}

// Global instance for convenience (Safe for multiple loads)
if (typeof window !== 'undefined' && !window.fabric) {
    window.fabric = new FabricClient();
}
