import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Bhumi AI - Agricultural Intelligence Assistant',
  description: 'Multimodal Agricultural Intelligence Assistant powered by specialized AI agents for Indian farmers',
  keywords: 'agriculture, AI, farming, weather, market prices, government schemes, India',
  authors: [{ name: 'Bhumi AI Team' }],
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#22c55e',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="h-full">
      <head>
        <link rel="icon" href="/favicon.ico" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
      </head>
      <body className={`${inter.className} h-full`}>
        <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50">
          {children}
        </div>
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#f0fdf4',
              color: '#15803d',
              border: '1px solid #22c55e',
            },
            success: {
              iconTheme: {
                primary: '#22c55e',
                secondary: '#f0fdf4',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fef2f2',
              },
              style: {
                background: '#fef2f2',
                color: '#dc2626',
                border: '1px solid #ef4444',
              },
            },
          }}
        />
      </body>
    </html>
  )
}
