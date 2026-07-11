// 2_backend_api/service_fabric/staticfiles/apiClient_v2.js

/**
 * ApiClient (Version 2): Optimized for both authenticated and public access.
 * This version allows loading services without requiring an authorization token.
 */
class ApiClient {
    constructor(apiUrls) {
        this.urls = apiUrls;
        this.token = localStorage.getItem('accessToken');
    }

    /**
     * Executes a 'fetch' request.
     * @param {string} url - The endpoint URL.
     * @param {Object} options - Fetch options.
     * @param {boolean} useAuth - Whether to include the Authorization header.
     */
    async request(url, options = {}, useAuth = true) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (this.token && useAuth) {
            headers['Authorization'] = 'Bearer ' + this.token;
        }

        const response = await fetch(url, { ...options, headers });

        if (!response.ok) {
            let errorData = { detail: `Error ${response.status}: ${response.statusText}` };
            try {
                errorData = await response.json();
                console.error("API Error Response Data:", errorData);
            } catch (e) { /* Error was not JSON */ }
            
            // Handle unauthorized specifically if auth was intended
            if (response.status === 401 && useAuth) {
                console.warn("Session expired or unauthorized. Logging out...");
                window.dispatchEvent(new Event('force-logout'));
            }
            throw errorData;
        }
        
        if (response.status === 204) {
            return null;
        }
        return response.json();
    }

    /**
     * Centralized API functions
     */
    
    // Inside 2_backend_api/service_fabric/staticfiles/apiClient_v2.js
// Inside 2_backend_api/service_fabric/staticfiles/apiClient_v2.js
    login(email, password) {
    return this.request(this.urls.login, {
            method: 'POST',
            // Use 'email' as the key because your User model uses it as the USERNAME_FIELD
            body: JSON.stringify({ email: email, password: password }), 
        }, false); 
    }

    /**
     * Version 2 Improvement: Loading services is explicitly public/non-token dependent
     * to allow viewing the catalog without being logged in.
     */
    getServices() {
    return this.request(this.urls.services, {}, true); // Change false to true
    }
    
    getTemplates() {
        return this.request(this.urls.templates, {}, true);
    }
    
    getServiceDetail(serviceId) {
        return this.request(`${this.urls.services}${serviceId}/`, {}, true); // Change false to true
    }

    /**
     * Creation still requires authentication.
     */
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
    
    // Additional methods (delete, logs, etc.) can be added here following the same pattern.
}
