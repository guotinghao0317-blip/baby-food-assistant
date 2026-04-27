import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '辅食助手 - 为宝宝定制专属食谱',
  description: '为2岁以下宝宝提供个性化辅食食谱规划',
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
    userScalable: false,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  )
}
