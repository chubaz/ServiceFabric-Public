import * as React from 'react'
import * as ReactDOM from 'react-dom'
import * as ReactDOMClient from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Expose React and ReactDOM for dynamic ESM imports
(window as any).React = React;
(window as any).ReactDOM = ReactDOM;
(window as any).ReactDOMClient = ReactDOMClient;

const { createRoot, hydrateRoot } = ReactDOMClient;

// Environment Shims for libraries that expect Node.js globals or CJS
(window as any).global = window;
(window as any).process = { env: { NODE_ENV: 'development' } };
(window as any).require = (name: string) => {
  if (name === 'react') return React;
  if (name === 'react-dom') return (window as any).ReactDOM;
  if (name === 'react-dom/client') return ReactDOMClient;
  if (name === 'react/jsx-runtime' || name === 'react/jsx-dev-runtime') {
    const r = { 
        jsx: (React as any).createElement, 
        jsxs: (React as any).createElement, 
        Fragment: React.Fragment 
    };
    return { ...r, default: r, __esModule: true };
  };
  
  // Try to find in dynamic module cache
  const cached = (window as any).__STUDIO_MODULE_CACHE__?.[name];
  if (cached) {
    return cached.default || cached;
  }
  
  // Only warn if it doesn't look like an internal check
  if (!name.includes('./') && !name.includes('../')) {
    console.debug(`Dynamic require of "${name}" requested.`);
  }
  
  return {}; 
};

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
