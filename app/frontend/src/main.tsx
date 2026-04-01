import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'
import { ToastProvider } from './components/Toast'
import { ThemeProvider } from './lib/theme'
import { loadConfig } from './lib/config'

const renderApp = () => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <ThemeProvider>
        <ToastProvider>
          <App />
        </ToastProvider>
      </ThemeProvider>
    </StrictMode>,
  )
};

loadConfig().then(renderApp).catch(() => {
  // Render app with default config if remote config fails
  renderApp();
})
