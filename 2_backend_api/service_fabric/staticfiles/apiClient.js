/**
 * ApiClient: Unified interface for Service Fabric API.
 * Handles authentication headers and JSON error parsing.
 */
class ApiClient {
    constructor(apiUrls) {
        this.urls = apiUrls;
        this.token = localStorage.getItem('accessToken');
    }

    async request(url, options = {}, useAuth = true) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        // Only attach token if it exists and authentication is desired for this call
        if (this.token && useAuth) {
            headers['Authorization'] = 'Bearer ' + this.token;
        }

        const response = await fetch(url, { ...options, headers });

        if (!response.ok) {
            let errorData = { detail: `Error ${response.status}: ${response.statusText}` };
            try {
                errorData = await response.json();
            } catch (e) { /* Fallback to default error object */ }
            
            if (response.status === 401 && useAuth) {
                console.warn("Unauthorized request. Triggering logout.");
                window.dispatchEvent(new Event('force-logout'));
            }
            throw errorData;
        }
        
        if (response.status === 204) return null;
        return response.json();
    }

    login(email, password) {
        return this.request(this.urls.login, {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        }, false);
    }

    getServices() {
        return this.request(this.urls.services, {}, true);
    }

    getTemplates() {
        // Now public-accessible on the backend
        return this.request(this.urls.templates, {}, false);
    }
    
    getServiceDetail(serviceId) {
        return this.request(`${this.urls.services}${serviceId}/`, {}, true);
    }

    createService(name, templateKey, description = '', themeColor = 'indigo') {
        return this.request(this.urls.create, {
            method: 'POST',
            body: JSON.stringify({ 
                name: name, 
                template_key: templateKey,
                description: description,
                theme_color: themeColor
            }),
        }, true);
    }

    updateService(serviceId, data) {
        return this.request(`${this.urls.services}${serviceId}/`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        }, true);
    }
}
