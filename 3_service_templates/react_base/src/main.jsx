import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import './index.css';

const context = window[`SF_CONTEXT_{{APP_SLUG}}`] || {
    name: "Application",
    slug: "default",
    state: {},
    data: {}
};

const container = document.getElementById(`react-mount-${context.slug}`);
if (container) {
    const root = createRoot(container);
    root.render(
        <React.StrictMode>
            <App context={context} />
        </React.StrictMode>
    );
}
