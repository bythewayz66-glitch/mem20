import React from 'react';
import ReactDOM from 'react-dom/client';
// The teamz design system first: tokens, component styles, scrollbars.
import './teamz/styles.css';
// Then the mem20 shell layer, which only adds — it never redefines a token value.
import './styles.css';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
