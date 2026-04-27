'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Home() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [babies, setBabies] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      setLoading(false)
      return
    }

    try {
      // 获取用户信息
      const userResponse = await axios.get(`${API_URL}/api/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      setUser(userResponse.data)

      // 获取宝宝信息
      const babiesResponse = await axios.get(`${API_URL}/api/babies`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      setBabies(babiesResponse.data)
    } catch (err) {
      // Token 无效，清除
      localStorage.removeItem('token')
    } finally {
      setLoading(false)
    }
  }

  const handleStart = () => {
    const token = localStorage.getItem('token')
    if (token) {
      router.push('/onboarding')
    } else {
      router.push('/login')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    setUser(null)
    setBabies([])
    router.push('/')
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-pink-50 to-orange-50">
      <div className="container mx-auto px-3 sm:px-4 py-8 md:py-16">
        {/* 用户信息栏 */}
        {user && (
          <div className="bg-white rounded-xl shadow-lg p-4 mb-8 flex flex-col sm:flex-row justify-between items-center gap-3">
            <div>
              <p className="text-sm text-gray-600">欢迎回来</p>
              <p className="text-lg font-semibold text-gray-800">{user.email}</p>
              {babies.length > 0 && babies[0].name && (
                <p className="text-sm text-pink-600 mt-1">
                  👶 {babies[0].name} 的专属食谱
                </p>
              )}
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 min-h-[48px] text-gray-600 hover:text-gray-800 flex items-center justify-center"
            >
              退出登录
            </button>
          </div>
        )}

        <div className="text-center mb-12">
          <h1 className="text-3xl md:text-5xl font-bold text-gray-800 mb-4">
            🍼 辅食助手
          </h1>
          <p className="text-lg md:text-xl text-gray-600 mb-8">
            为2岁以下宝宝定制专属营养食谱
          </p>
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center">
            <button
              onClick={handleStart}
              className="bg-pink-500 text-white px-6 sm:px-8 py-3 rounded-lg text-lg font-semibold hover:bg-pink-600 transition min-h-[48px] flex items-center justify-center"
            >
              {user ? '开始使用' : '登录开始使用'}
            </button>
            {!user && (
              <>
                <Link
                  href="/login"
                  className="bg-white text-pink-500 px-6 sm:px-8 py-3 rounded-lg text-lg font-semibold border-2 border-pink-500 hover:bg-pink-50 transition min-h-[48px] flex items-center justify-center"
                >
                  登录
                </Link>
                <Link
                  href="/register"
                  className="bg-white text-pink-500 px-6 sm:px-8 py-3 rounded-lg text-lg font-semibold border-2 border-pink-500 hover:bg-pink-50 transition min-h-[48px] flex items-center justify-center"
                >
                  注册
                </Link>
              </>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-8 mt-8 md:mt-16">
          <div className="bg-white p-4 md:p-6 rounded-xl shadow-lg">
            <div className="text-4xl mb-4">📋</div>
            <h3 className="text-xl font-semibold mb-2">信息收集</h3>
            <p className="text-gray-600">
              收集宝宝年龄、发育阶段、过敏信息等，精准判断营养需求
            </p>
          </div>

          <div className="bg-white p-4 md:p-6 rounded-xl shadow-lg">
            <div className="text-4xl mb-4">🍽️</div>
            <h3 className="text-xl font-semibold mb-2">一周食谱</h3>
            <p className="text-gray-600">
              生成7天完整食谱，包含详细烹饪步骤和精美配图
            </p>
          </div>

          <div className="bg-white p-4 md:p-6 rounded-xl shadow-lg">
            <div className="text-4xl mb-4">💬</div>
            <h3 className="text-xl font-semibold mb-2">智能调整</h3>
            <p className="text-gray-600">
              根据宝宝喜好和反馈，随时调整食谱内容
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}
