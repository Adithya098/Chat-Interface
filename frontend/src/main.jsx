/*
 * Frontend entrypoint that mounts the React application into the browser DOM.
 *
 * This file imports global design variables, creates the React root on the
 * `#root` element, and renders the app inside StrictMode to enable additional
 * development checks for unsafe side effects.
 */
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/variables.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
