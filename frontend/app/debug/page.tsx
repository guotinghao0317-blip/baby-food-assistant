'use client'

import { useState, useEffect } from 'react'

export default function Debug() {
  const [apiUrl, setApiUrl] = useState('')

  useEffect(() => {
    setApiUrl(process.env.NEXT_PUBLIC_API_URL || 'undefined')
  }, [])

  return (
    <div>
      <h1>Debug Environment</h1>
      <p>NEXT_PUBLIC_API_URL: {apiUrl}</p>
      <p>typeof: {typeof process.env.NEXT_PUBLIC_API_URL}</p>
    </div>
  )
}
