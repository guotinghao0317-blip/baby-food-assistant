'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// 营养素配置 - 包含名称、单位、参考标准说明、饮食建议
const NUTRIENT_CONFIG = {
  calories_per_day: {
    name: '能量',
    unit: 'kcal',
    reference: {
      '0-6': '主要从母乳或配方奶中获取，辅食添加初期无需刻意追求能量摄入',
      '6-12': '辅食部分每日推荐约300-500kcal，总能量（含奶）约800-1000kcal',
      '12-24': '辅食部分每日推荐约500-800kcal，逐步过渡到主食为主'
    },
    suggestion: '根据宝宝的活动量和生长速度调整，观察宝宝的饥饿信号和生长曲线即可。',
    highlight: false
  },
  protein_g: {
    name: '蛋白质',
    unit: 'g',
    reference: {
      '0-6': '主要从母乳或配方奶中获取，已能满足需求',
      '6-12': '辅食推荐每日约5-15g，注重优质蛋白质（肉、蛋、鱼）',
      '12-24': '辅食推荐每日约10-20g，保证生长发育需求'
    },
    suggestion: '优先选择红肉、禽肉、鱼类、鸡蛋、豆腐等优质蛋白质来源。每日保证一定量的动物性食物。',
    highlight: false
  },
  fat_g: {
    name: '脂肪',
    unit: 'g',
    reference: {
      '0-6': '主要从母乳或配方奶中获取',
      '6-12': '辅食推荐每日约5-20g，保证必需脂肪酸',
      '12-24': '辅食推荐每日约15-30g'
    },
    suggestion: '添加辅食时不要完全禁油，适量脂肪对宝宝大脑发育很重要。可通过蛋黄、肉类、鱼类获取优质脂肪。',
    highlight: false
  },
  carbs_g: {
    name: '碳水化合物',
    unit: 'g',
    reference: {
      '0-6': '主要从母乳或配方奶中获取',
      '6-12': '辅食推荐每日约30-80g，逐步增加主食比例',
      '12-24': '辅食推荐每日约60-120g，主食逐渐成为主要能量来源'
    },
    suggestion: '从强化铁米粉开始，逐步添加小米粥、软面条、软米饭等多样化主食。',
    highlight: false
  },
  iron_mg: {
    name: '铁',
    unit: 'mg',
    reference: {
      '0-6': '0.27mg/天，来自母体储存铁+母乳/配方奶',
      '6-12': '10mg/天（关键营养素，急需辅食补充）',
      '12-24': '7mg/天'
    },
    suggestion: '⚠️ 6个月后宝宝储存铁耗尽，必须从辅食中补充铁！优先添加富含铁的食物：红肉泥、猪肝泥、高铁米粉。缺铁会影响智力发育，务必重视。',
    highlight: true
  },
  calcium_mg: {
    name: '钙',
    unit: 'mg',
    reference: {
      '0-6': '200mg/天，母乳/配方奶已能满足',
      '6-12': '400mg/天，主要仍来自奶',
      '12-24': '600mg/天'
    },
    suggestion: '保证每日奶量（6-12个月≥600ml，1岁以上≥500ml），适当添加豆制品、绿叶菜等含钙食物。',
    highlight: false
  },
  vitamin_d_iu: {
    name: '维生素D',
    unit: 'IU',
    reference: {
      '0-6': '400IU/天，需要额外补充',
      '6-12': '400IU/天，需要额外补充',
      '12-24': '600IU/天，需要额外补充'
    },
    suggestion: '无论母乳喂养还是配方奶喂养，出生后几天就要开始每日补充维生素D，建议一直补充到青少年。多晒太阳也有帮助，但不能替代补充剂。',
    highlight: true
  }
} as const

export default function NutritionAnalysis() {
  const router = useRouter()
  const params = useParams()
  const babyId = params.baby_id as string

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [baby, setBaby] = useState<any>(null)
  const [nutrition, setNutrition] = useState<any>(null)

  // 用于流式输出：记录当前已渲染的营养素索引
  const [renderedCount, setRenderedCount] = useState(0)
  const [animationDone, setAnimationDone] = useState(false)

  const getToken = () => localStorage.getItem('token')

  // 获取宝宝信息和营养分析
  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = getToken()
        if (!token) {
          router.push('/login')
          return
        }

        // 获取宝宝信息
        const babyResponse = await axios.get(
          `${API_URL}/api/babies/${babyId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        setBaby(babyResponse.data)

        // 获取营养需求
        const nutritionResponse = await axios.get(
          `${API_URL}/api/babies/${babyId}/nutrition`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        setNutrition(nutritionResponse.data)
        setLoading(false)
      } catch (err: any) {
        console.error('获取营养分析失败:', err)
        if (err.response?.status === 401) {
          router.push('/login')
        } else {
          setError(err.response?.data?.detail || '加载失败，请重试')
          setLoading(false)
        }
      }
    }

    fetchData()
  }, [babyId, router])

  // 流式输出动画：逐个显示营养素卡片
  useEffect(() => {
    if (!nutrition || loading) return

    // 获取有序的营养素列表
    const nutrientKeys = getOrderedNutrientKeys(nutrition)

    // 从 0 开始，逐个递增
    let currentCount = 0
    setRenderedCount(currentCount)

    // 每个 300ms 显示下一个
    const interval = setInterval(() => {
      currentCount++
      setRenderedCount(currentCount)

      if (currentCount >= nutrientKeys.length) {
        clearInterval(interval)
        setAnimationDone(true)
      }
    }, 300)

    return () => clearInterval(interval)
  }, [nutrition, loading])

  // 根据营养数据获取有序的营养素列表
  const getOrderedNutrientKeys = (nut: any) => {
    const order = [
      'calories_per_day',
      'protein_g',
      'fat_g',
      'carbs_g',
      'iron_mg',
      'calcium_mg',
      'vitamin_d_iu'
    ]
    return order.filter(key => nut[key] !== null && nut[key] !== undefined)
  }

  // 获取月龄区间
  const getAgeRange = (ageMonths: number) => {
    if (ageMonths < 6) return '0-6'
    if (ageMonths < 12) return '6-12'
    return '12-24'
  }

  // 开始生成食谱
  const handleGenerateRecipe = async () => {
    setLoading(true)
    setError('')
    try {
      const token = getToken()
      if (!token) {
        router.push('/login')
        return
      }

      // Step 1: 创建空Recipe记录
      const response = await fetch(
        `${API_URL}/api/recipes/generate-start`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ baby_id: parseInt(babyId) }),
        }
      )

      if (response.status === 401) {
        localStorage.removeItem('token')
        router.push('/login')
        return
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      const recipeId = data.recipe_id
      console.log('Created recipe:', recipeId)

      // Step 2: 直接跳转到食谱详情页，页面会自动开始流式生成
      router.push(`/recipes/${recipeId}`)
    } catch (err: any) {
      console.error('创建食谱失败:', err)
      setError(err.message || '创建食谱失败，请重试')
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-50 to-orange-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-pink-500 mx-auto mb-4"></div>
          <p className="text-gray-600">正在计算营养需求...</p>
        </div>
      </div>
    )
  }

  if (error || !baby || !nutrition) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-50 to-orange-50 flex items-center justify-center px-3 sm:px-4">
        <div className="bg-white rounded-xl shadow-lg p-4 md:p-8 text-center">
          <p className="text-red-600 mb-4">{error || '数据加载失败'}</p>
          <button
            onClick={() => router.push('/onboarding')}
            className="px-6 py-2 min-h-[48px] flex items-center justify-center mx-auto bg-pink-500 text-white rounded-lg hover:bg-pink-600"
          >
            返回
          </button>
        </div>
      </div>
    )
  }

  const ageRange = getAgeRange(baby.age_months)
  const nutrientKeys = getOrderedNutrientKeys(nutrition)

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-orange-50 py-8 px-3 sm:px-4">
      <div className="max-w-4xl mx-auto">
        {/* 标题 */}
        <div className="text-center mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">
            📊 营养需求分析
          </h1>
          <p className="text-gray-600">
            基于 {baby.name || `${baby.age_months} 个月`} 宝宝的个性化营养建议
          </p>
        </div>

        {/* 宝宝基本信息卡片 - 始终显示 */}
        <div className="bg-white rounded-xl shadow-lg p-4 md:p-6 mb-6 fade-in">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            👶 宝宝基本信息
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <span className="text-sm text-gray-500">月龄</span>
              <p className="font-medium text-gray-800">{baby.age_months} 个月</p>
            </div>
            {baby.weight && (
              <div>
                <span className="text-sm text-gray-500">体重</span>
                <p className="font-medium text-gray-800">{baby.weight} kg</p>
              </div>
            )}
            {baby.height && (
              <div>
                <span className="text-sm text-gray-500">身高</span>
                <p className="font-medium text-gray-800">{baby.height} cm</p>
              </div>
            )}
            <div>
              <span className="text-sm text-gray-500">进食能力</span>
              <p className="font-medium text-gray-800">{baby.feeding_stage}</p>
            </div>
            <div>
              <span className="text-sm text-gray-500">出牙情况</span>
              <p className="font-medium text-gray-800">{baby.teething_status}</p>
            </div>
          </div>
        </div>

        {/* 营养素卡片 - 流式输出 */}
        <div className="space-y-4 mb-8">
          {nutrientKeys.map((key, index) => {
            const config = NUTRIENT_CONFIG[key as keyof typeof NUTRIENT_CONFIG]
            const value = nutrition[key]
            const isHighlight = config.highlight
            const isRendered = index < renderedCount

            if (!isRendered) return null

            return (
              <div
                key={key}
                className={`rounded-xl shadow-md p-4 md:p-6 transition-all duration-500 animate-fadeIn ${
                  isHighlight
                    ? 'border-2 border-amber-400 bg-amber-50'
                    : 'bg-white'
                }`}
              >
                {/* 头部 */}
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-lg font-bold text-gray-800">
                    {config.name}
                    {isHighlight && (
                      <span className="ml-2 inline-block px-2 py-1 bg-amber-400 text-white text-xs rounded-full">
                        关键
                      </span>
                    )}
                  </h3>
                  <div className="text-right">
                    <span className="text-xl font-semibold text-pink-600">
                      {value}
                    </span>
                    <span className="text-gray-500 ml-1">{config.unit}</span>
                    <span className="text-gray-500">/天</span>
                  </div>
                </div>

                {/* 参考标准 */}
                <div className="bg-gray-50 rounded-lg p-4 mb-3">
                  <h4 className="text-sm font-medium text-gray-700 mb-1">
                    📋 参考标准
                  </h4>
                  <p className="text-sm text-gray-600">
                    {config.reference[ageRange as keyof typeof config.reference]}
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    参考依据：WHO 婴幼儿营养指南 + 中国营养学会 0-2岁婴幼儿喂养指南
                  </p>
                </div>

                {/* 饮食建议 */}
                <div className="bg-blue-50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-1">
                    💡 饮食建议
                  </h4>
                  <p className="text-sm text-gray-700">
                    {config.suggestion}
                  </p>
                </div>
              </div>
            )
          })}
        </div>

        {/* 分析完成提示 - 显示按钮 */}
        <div className="text-center">
          {animationDone ? (
            <div className="bg-green-50 border border-green-200 rounded-xl p-6 mb-6 animate-fadeIn">
              <p className="text-green-700 mb-4">
                ✅ 营养分析已完成，请确认后生成专属食谱
              </p>
              <button
                onClick={handleGenerateRecipe}
                className="px-6 md:px-8 py-3 min-h-[48px] flex items-center justify-center mx-auto bg-pink-500 text-white rounded-lg hover:bg-pink-600 transition-colors text-lg font-medium"
              >
                确认并生成一周食谱
              </button>
            </div>
          ) : (
            <div className="text-gray-500">
              <div className="animate-pulse">AI 正在为您分析营养需求...</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
