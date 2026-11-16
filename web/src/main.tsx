import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles.css';
// Loaded after the base design system: this pass's light-theme tokens, command
// palette, catalog and domain surfaces, plus the handful of base rules they
// correct. Document order is what lets them override.
import './styles/surfaces.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
