/**
 * FabricClient: The standard SDK for interacting with the Service Fabric Gateway.
 * Handles real-time WebSockets, orchestrated API calls, and service discovery.
 */

export type FabricEvent = {
    event: string;
    data: any;
    timestamp: string;
};

export type FabricConfig = {
    baseUrl?: string;
    apiPrefix?: string;
    wsPrefix?: string;
};

export class FabricClient {
    private socket: WebSocket | null = null;
    private listeners: Set<(event: FabricEvent) => void> = new Set();
    private clientId: string;
    private config: Required<FabricConfig>;
    private reconnectAttempts: number = 0;
    private maxReconnectAttempts: number = 5;

    constructor(clientIdPrefix: string = 'app', config: FabricConfig = {}) {
        this.clientId = `${clientIdPrefix}_${Math.floor(Math.random() * 10000)}`;
        this.config = {
            baseUrl: config.baseUrl || window.location.origin,
            apiPrefix: config.apiPrefix || '/api/v1',
            wsPrefix: config.wsPrefix || '/api/v1/ws/events',
        };
    }

    /**
     * Connects to the Fabric Gateway WebSocket for real-time events.
     */
    connect(): void {
        if (this.socket) return;

        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}${this.config.wsPrefix}/${this.clientId}`;

        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log(`[Fabric] Connected as ${this.clientId}`);
            this.reconnectAttempts = 0;
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.notifyListeners(data);
            } catch (e) {
                // Handle non-JSON messages (like welcome strings)
                this.notifyListeners({
                    event: 'raw_message',
                    data: event.data,
                    timestamp: new Date().toISOString()
                });
            }
        };

        this.socket.onclose = () => {
            this.socket = null;
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                console.warn(`[Fabric] Disconnected. Reconnecting (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
                setTimeout(() => this.connect(), 5000);
            }
        };
    }

    /**
     * Sends an event to the Gateway to be broadcast to other services.
     */
    broadcast(event: string, data: any = {}): void {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({ event, data, source: this.clientId }));
        } else {
            console.error('[Fabric] Cannot broadcast: WebSocket is not open.');
        }
    }

    /**
     * Standardized fetch wrapper for Gateway-aware requests.
     */
    async call(endpoint: string, options: RequestInit = {}): Promise<any> {
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
     * Orchestration: Fetches data from the Gateway's centralized aggregator.
     */
    async getDashboardData(): Promise<any> {
        return this.call(`${this.config.apiPrefix}/orchestration/dashboard-data`);
    }

    /**
     * Subscribe to incoming Fabric events.
     */
    onEvent(callback: (event: FabricEvent) => void): () => void {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    private notifyListeners(data: any): void {
        const fabricEvent: FabricEvent = typeof data === 'object' && data.event 
            ? data 
            : { event: 'message', data, timestamp: new Date().toISOString() };
        
        this.listeners.forEach(cb => cb(fabricEvent));
    }
}

// Singleton instance for easy use
export const fabric = new FabricClient();
