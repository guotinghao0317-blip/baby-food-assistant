'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Register() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // 验证密码长度
      if (formData.password.length > 72) {
        setError('密码长度不能超过72个字符')
        setLoading(false)
        return
      }

      const response = await axios.post(`${API_URL}/api/auth/register`, {
        email: formData.email,
        password: formData.password
      })

      // 注册成功，跳转到登录页
      router.push('/login?registered=true')
    } catch (err: any) {
      if (err.response) {
        setError(err.response.data?.detail || '注册失败，请重试')
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
          🍼 注册账号
        </h1>

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
              minLength={6}
              maxLength={72}
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
              placeholder="至少6个字符"
            />
            <p className="text-xs text-gray-500 mt-1">密码长度：6-72个字符</p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-pink-500 text-white py-2 px-4 rounded-lg font-semibold hover:bg-pink-600 transition disabled:opacity-50 disabled:cursor-not-allowed min-h-[48px] flex items-center justify-center"
          >
            {loading ? '注册中...' : '注册'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <a href="/login" className="text-pink-500 hover:text-pink-600">
            已有账号？去登录
          </a>
        </div>
      </div>
    </div>
  )
}
