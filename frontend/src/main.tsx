import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import createCache from '@emotion/cache'
import { CacheProvider } from '@emotion/react'
import './index.css'
import App from './App.tsx'

// Read CSP nonce from meta tag injected by the server.
// This allows MUI/emotion to inject styles with the nonce,
// eliminating the need for 'unsafe-inline' in the CSP style-src directive.
const nonce = document.querySelector<HTMLMetaElement>('meta[name="emotion-nonce"]')?.content || undefined;

const emotionCache = createCache({
  key: 'css',
  nonce,
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <CacheProvider value={emotionCache}>
      <App />
    </CacheProvider>
  </StrictMode>,
)
