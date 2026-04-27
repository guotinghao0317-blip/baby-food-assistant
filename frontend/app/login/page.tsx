'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Login() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState('')

  useEffect(() => {
    // 检查URL参数，看是否刚注册成功
    const params = new URLSearchParams(window.location.search)
    if (params.get('registered') === 'true') {
      setSuccess('注册成功！请登录')
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // OAuth2PasswordRequestForm 需要 application/x-www-form-urlencoded 格式
      const params = new URLSearchParams()
      params.append('username', formData.email) // OAuth2PasswordRequestForm 使用 username 字段
      params.append('password', formData.password)

      const response = await axios.post(`${API_URL}/api/auth/login`, params.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })

      // 保存 token
      localStorage.setItem('token', response.data.access_token)
      
      // 跳转回来源页（若有）
      const urlParams = new URLSearchParams(window.location.search)
      const returnToParam = urlParams.get('returnTo')
      const returnTo = returnToParam ? decodeURIComponent(returnToParam) : '/onboarding'
      router.push(returnTo)
    } catch (err: any) {
      if (err.response) {
        setError(err.response.data?.detail || '登录失败，请检查邮箱和密码')
      } else {
        setError('网络错误，请检查后端服务是否运行')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-orange-50 flex items-center justify-center px-3 sm:px-4">
      <div className="bg-white rounded-xl shadow-lg p-4 md:p-8 w-full max-w-md">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-6 text-center">
          🍼 登录
        </h1>

        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-4">
            {success}
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              邮箱
            </label>
            <input
              type="email"
              id="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
              placeholder="your@email.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              密码
            </label>
            <input
              type="password"
              id="password"
              required
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
              placeholder="请输入密码"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-pink-500 text-white py-2 px-4 rounded-lg font-semibold hover:bg-pink-600 transition disabled:opacity-50 disabled:cursor-not-allowed min-h-[48px] flex items-center justify-center"
          >
            {loading ? '登录中...' : '登录'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <a href="/register" className="text-pink-500 hover:text-pink-600">
            还没有账号？去注册
          </a>
        </div>
      </div>
    </div>
  )
}
