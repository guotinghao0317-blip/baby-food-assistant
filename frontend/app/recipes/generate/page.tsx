'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// 生成步骤 - 对应流式输出进度
const GENERATION_STEPS = [
  '分析宝宝营养需求...',
  '规划周一食谱...',
  '规划周二食谱...',
  '规划周三食谱...',
  '规划周四食谱...',
  '规划周五食谱...',
  '规划周六食谱...',
  '规划周日食谱...',
  '优化菜品搭配...',
  '计算营养均衡性...',
  '完成生成！'
]

// 常量定义
const DAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

// FE-6: 去掉加餐，但兼容旧数据
const MEAL_TYPES: Record<string, string> = {
  breakfast: '早餐',
  lunch: '午餐',
  dinner: '晚餐',
  snack: '加餐'  // 兼容旧数据
}

// 类型定义
interface DishData {
  id: number
  meal_type: string
  dish_name: string
  ingredients: Array<{ name: string; amount: string }>
  cooking_steps: Array<{ step: number; description: string }>
  nutrition_info: {
    calories: number
    protein: number
    iron: number
  }
  image_url?: string
}

interface DayGenerationState {
  day: number
  status: 'pending' | 'generating' | 'done'
  details?: DishData[]
}

// 解析SSE格式的辅助函数
const parseSSE = (chunk: string) => {
  const lines = chunk.split('\n')
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      try {
        return JSON.parse(line.slice(6))
      } catch {
        return null
      }
    }
  }
  return null
}

export default function GenerateRecipe() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [currentStep, setCurrentStep] = useState(0)
  const [recipe, setRecipe] = useState<any>(null)

  const [days, setDays] = useState<DayGenerationState[]>(() =>
    Array.from({ length: 7 }, (_, i) => ({
      day: i + 1,
      status: 'pending' as const,
      details: undefined
    }))
  )
  const [selectedDay, setSelectedDay] = useState(1)

  const abortControllerRef = useRef<AbortController | null>(null)
  const hasStartedRef = useRef(false)
  const userHasManualSelection = useRef(false)

  const getToken = () => {
    return localStorage.getItem('token')
  }

  useEffect(() => {
    if (hasStartedRef.current) {
      console.log('已开始生成，跳过重复执行')
      return
    }

    const token = localStorage.getItem('token')
    if (!token) {
      console.log('[useEffect] 未找到token，跳转到登录页')
      router.push('/login')
      return
    }

    const babyIdParam = searchParams.get('baby_id')
    if (!babyIdParam) {
      console.log('[useEffect] 缺少baby_id参数')
      setError('缺少宝宝ID')
      return
    }

    console.log('[useEffect] 准备生成食谱，baby_id:', babyIdParam)
    hasStartedRef.current = true

    setTimeout(() => {
      generateRecipe(babyIdParam)
    }, 100)

    return () => {
      console.log('[useEffect] 清理，取消请求')
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [searchParams, router])

  // 根据接收的内容更新当前步骤
  const updateStepFromContent = (content: string) => {
    const length = content.length
    if (length === 0) {
      setCurrentStep(1)
    } else if (length < 500) {
      setCurrentStep(2)
    } else if (length < 1500) {
      setCurrentStep(3)
    } else if (length < 2500) {
      setCurrentStep(4)
    } else if (length < 3500) {
      setCurrentStep(5)
    } else if (length < 4500) {
      setCurrentStep(6)
    } else if (length < 5500) {
      setCurrentStep(7)
    } else if (length < 6500) {
      setCurrentStep(8)
    } else if (length < 7500) {
      setCurrentStep(9)
    } else {
      setCurrentStep(10)
    }
  }

  // 简化后的 handleSSEEvent
  const handleSSEEvent = (data: any) => {
    if (data.type === 'started') {
      console.log('[generateRecipe] started事件 - recipe_id:', data.recipe_id)
      setCurrentStep(1)
    } else if (data.type === 'day_started') {
      console.log('[generateRecipe] day_started事件 - day:', data.day)
      const stepIndex = data.day
      if (stepIndex >= 1 && stepIndex <= 7) {
        setCurrentStep(stepIndex)
      }
      setDays(prev => prev.map(d =>
        d.day === data.day ? { ...d, status: 'generating' } : d
      ))
      // 用户没手动点击过tab时，自动切换到正在生成的天
      if (!userHasManualSelection.current) {
        setSelectedDay(data.day)
      }
    } else if (data.type === 'dish_done') {
      // 每道菜生成完立即追加到当天details中，实现逐菜展示
      if (data.detail && data.day) {
        setDays(prev => prev.map(d => {
          if (d.day === data.day) {
            const existingDetails = d.details || []
            const alreadyExists = existingDetails.some(
              (dish: any) => dish.id === data.detail.id || dish.meal_type === data.detail.meal_type
            )
            if (alreadyExists) return d
            return { ...d, details: [...existingDetails, data.detail] }
          }
          return d
        }))
        if (!userHasManualSelection.current) {
          setSelectedDay(data.day)
        }
      }
    } else if (data.type === 'day_done') {
      console.log('[generateRecipe] day_done事件 - day:', data.day, '菜品数:', data.details?.length)
      setDays(prev => prev.map(d => {
        if (d.day === data.day) {
          const finalDetails = (data.details && data.details.length > 0)
            ? data.details
            : d.details
          return { ...d, status: 'done', details: finalDetails }
        }
        return d
      }))
    } else if (data.type === 'chunk') {
      updateStepFromContent(data.full_content || '')
    } else if (data.type === 'finished') {
      console.log('[generateRecipe] finished事件 - recipe_id:', data.recipe_id)
      setRecipe({ id: data.recipe_id })
      setCurrentStep(GENERATION_STEPS.length - 1)
      setTimeout(() => {
        console.log('[generateRecipe] 跳转到食谱详情页')
        router.push(`/recipes/${data.recipe_id}`)
      }, 1500)
      return
    } else if (data.type === 'error') {
      console.error('[generateRecipe] error事件 - message:', data.message)
      throw new Error(data.message)
    } else {
      console.log('[generateRecipe] 未知事件类型:', data.type)
    }
  }

  const generateRecipe = async (babyId: string) => {
    console.log('[generateRecipe] 开始生成，重置所有状态')
    setLoading(true)
    setError('')
    setCurrentStep(0)
    setRecipe(null)
    hasStartedRef.current = true

    try {
      const token = getToken()
      if (!token) {
        console.log('[generateRecipe] 生成食谱时未找到token')
        setLoading(false)
        router.push('/login')
        return
      }

      console.log('[generateRecipe] 开始流式生成食谱，baby_id:', babyId)

      const abortController = new AbortController()
      abortControllerRef.current = abortController

      const response = await fetch(`${API_URL}/api/recipes/generate-stream`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ baby_id: parseInt(babyId) }),
        signal: abortController.signal,
      })

      if (response.status === 401) {
        console.log('[generateRecipe] Token无效，清除并跳转登录')
        localStorage.removeItem('token')
        setLoading(false)
        router.push('/login')
        return
      }

      if (!response.ok) {
        const errorText = await response.text()
        console.error('[generateRecipe] HTTP错误:', response.status, errorText)
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        console.error('[generateRecipe] 无法读取响应流')
        throw new Error('无法读取响应流')
      }

      const decoder = new TextDecoder()
      let buffer = ''
      let eventCount = 0

      console.log('[generateRecipe] 开始读取SSE流')
      setCurrentStep(1)

      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          console.log('[generateRecipe] 流读取完成')
          break
        }

        buffer += decoder.decode(value, { stream: true })

        const events = buffer.split('\n\n')
        buffer = events.pop() || ''

        for (const event of events) {
          eventCount++
          const data = parseSSE(event)
          if (!data) {
            console.log(`[generateRecipe] 事件${eventCount}: 解析失败, 原始内容:`, event.substring(0, 100))
            continue
          }

          console.log(`[generateRecipe] 事件${eventCount}: type=${data.type}`)
          handleSSEEvent(data)
        }
      }

      console.log('[generateRecipe] 流结束，共处理', eventCount, '个事件')

    } catch (err: any) {
      console.error('[generateRecipe] 生成食谱错误:', err)
      console.error('[generateRecipe] 错误类型:', err.name)
      console.error('[generateRecipe] 错误消息:', err.message)

      if (err.name !== 'AbortError') {
        setError(err.message || '生成食谱失败，请重试')
        setLoading(false)
        setCurrentStep(0)
      }
    }
  }

  // 按天渲染内容
  const renderDayContent = (dayState: DayGenerationState) => {
    if (dayState.status === 'pending') {
      return (
        <div className="text-center py-12 text-gray-400">
          <div className="text-4xl mb-4">⏳</div>
          <p>等待生成中...</p>
        </div>
      )
    }

    if (dayState.status === 'generating') {
      // 如果已经有部分菜品生成完，先展示已完成的菜品
      if (dayState.details && dayState.details.length > 0) {
        return (
          <div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4 animate-fadeIn">
              {dayState.details.map((dish) => {
                const mealLabel = MEAL_TYPES[dish.meal_type] || dish.meal_type
                return (
                  <div key={dish.id} className="border rounded-lg p-3 md:p-4 hover:shadow-md transition-shadow animate-fadeIn">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold text-gray-700">
                        {mealLabel}：{dish.dish_name}
                      </h3>
                    </div>
                    {dish.ingredients && dish.ingredients.length > 0 && (
                      <div className="mb-3 animate-fadeIn">
                        <h4 className="text-sm font-medium text-gray-600 mb-1">食材：</h4>
                        <ul className="text-sm text-gray-700">
                          {dish.ingredients.map((ing, idx) => (
                            <li key={idx}>{ing.name} {ing.amount}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {dish.cooking_steps && dish.cooking_steps.length > 0 && (
                      <div className="animate-fadeIn">
                        <h4 className="text-sm font-medium text-gray-600 mb-1">烹饪步骤：</h4>
                        <ol className="text-sm text-gray-700 space-y-1">
                          {dish.cooking_steps.map((step) => (
                            <li key={step.step}>{step.step}. {step.description}</li>
                          ))}
                        </ol>
                      </div>
                    )}
                    {dish.nutrition_info && (
                      <div className="mt-3 pt-3 border-t animate-fadeIn">
                        <h4 className="text-xs font-medium text-gray-500 mb-1">营养估算：</h4>
                        <div className="flex gap-3 text-xs text-gray-600 flex-wrap">
                          <span>能量 {dish.nutrition_info.calories} kcal</span>
                          <span>蛋白质 {dish.nutrition_info.protein} g</span>
                          <span>铁 {dish.nutrition_info.iron} mg</span>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
            <div className="text-center py-6 animate-pulse">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-pink-500 mx-auto mb-2"></div>
              <p className="text-gray-500 text-sm">还有菜品正在生成中...</p>
            </div>
          </div>
        )
      }
      return (
        <div className="text-center py-12 animate-pulse">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500 mx-auto mb-4"></div>
          <p className="text-gray-600">正在为宝宝精心搭配{DAYS[dayState.day - 1]}食谱...</p>
        </div>
      )
    }

    if (dayState.status === 'done') {
      if (!dayState.details || dayState.details.length === 0) {
        return (
          <div className="text-center py-12 text-gray-400">
            <div className="text-4xl mb-4">📝</div>
            <p>暂无菜品数据</p>
          </div>
        )
      }
      return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4 animate-fadeIn">
          {dayState.details.map((dish) => {
            const mealLabel = MEAL_TYPES[dish.meal_type] || dish.meal_type
            return (
              <div key={dish.id} className="border rounded-lg p-3 md:p-4 hover:shadow-md transition-shadow animate-fadeIn">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold text-gray-700">
                    {mealLabel}：{dish.dish_name}
                  </h3>
                </div>

                {dish.ingredients && dish.ingredients.length > 0 && (
                  <div className="mb-3 animate-fadeIn">
                    <h4 className="text-sm font-medium text-gray-600 mb-1">食材：</h4>
                    <ul className="text-sm text-gray-700">
                      {dish.ingredients.map((ing, idx) => (
                        <li key={idx} className="animate-fadeIn">
                          {ing.name} {ing.amount}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {dish.cooking_steps && dish.cooking_steps.length > 0 && (
                  <div className="animate-fadeIn">
                    <h4 className="text-sm font-medium text-gray-600 mb-1">烹饪步骤：</h4>
                    <ol className="text-sm text-gray-700 space-y-1">
                      {dish.cooking_steps.map((step) => (
                        <li key={step.step} className="animate-fadeIn">
                          {step.step}. {step.description}
                        </li>
                      ))}
                    </ol>
                  </div>
                )}

                {dish.nutrition_info && (
                  <div className="mt-3 pt-3 border-t animate-fadeIn">
                    <h4 className="text-xs font-medium text-gray-500 mb-1">营养估算：</h4>
                    <div className="flex gap-3 text-xs text-gray-600 flex-wrap">
                      <span>能量 {dish.nutrition_info.calories} kcal</span>
                      <span>蛋白质 {dish.nutrition_info.protein} g</span>
                      <span>铁 {dish.nutrition_info.iron} mg</span>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )
    }

    return null
  }

  // 是否有任何天有数据
  const hasAnyData = days.some(d => d.status !== 'pending')

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-orange-50 py-8 px-3 sm:px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-xl shadow-lg p-4 md:p-8 text-center">
          {loading ? (
            <>
              <h2 className="text-xl md:text-2xl font-semibold text-gray-800 mb-6">
                AI 正在生成个性化一周食谱
              </h2>
              <p className="text-gray-500 mb-8">
                这可能需要30-60秒，正在逐步生成，请稍候...
              </p>

              {/* 流式步骤列表 */}
              <div className="space-y-3 text-left max-w-md mx-auto">
                {GENERATION_STEPS.map((step, index) => {
                  const isCompleted = index < currentStep
                  const isCurrent = index === currentStep

                  if (!isCompleted && !isCurrent) {
                    return (
                      <div key={index} className="flex items-center gap-3 text-gray-300">
                        <div className="w-5 h-5 rounded-full border-2 border-gray-200 flex-shrink-0"></div>
                        <span className="text-sm">{step}</span>
                      </div>
                    )
                  }

                  return (
                    <div
                      key={index}
                      className={`flex items-center gap-3 animate-fadeIn ${
                        isCurrent ? 'text-pink-600 animate-pulse' : 'text-green-600'
                      }`}
                    >
                      <div className={`w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center ${
                        isCurrent ? 'bg-pink-500' : 'bg-green-500'
                      }`}>
                        {isCompleted && (
                          <span className="text-white text-xs">✓</span>
                        )}
                      </div>
                      <span className={`text-sm font-medium ${
                        isCurrent ? 'text-pink-600' : 'text-gray-700'
                      }`}>
                        {step}
                      </span>
                    </div>
                  )
                })}
              </div>

              <div className="mt-8 text-sm text-gray-500">
                正在为您宝宝量身定制食谱，请耐心等待...
              </div>

              {/* 实时菜品展示区域 */}
              {hasAnyData && (
                <div className="mt-8 pt-8 border-t border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 text-center">
                    已生成的菜品预览
                  </h3>

                  {/* 7天 Tab */}
                  <div className="flex justify-center gap-2 mb-4 overflow-x-auto pb-2">
                    {DAYS.map((dayName, index) => {
                      const dayNum = index + 1
                      const dayState = days.find(d => d.day === dayNum)
                      const hasData = dayState && dayState.status !== 'pending'
                      const isSelected = selectedDay === dayNum

                      return (
                        <button
                          key={dayNum}
                          onClick={() => {
                            if (dayState && (dayState.status === 'done' || dayState.status === 'generating')) {
                              userHasManualSelection.current = true
                              setSelectedDay(dayNum)
                            }
                          }}
                          disabled={!hasData}
                          className={`px-4 py-2 min-h-[48px] rounded-lg text-sm font-medium transition-all ${
                            isSelected
                              ? 'bg-pink-500 text-white shadow-md'
                              : hasData
                              ? 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                          }`}
                        >
                          {dayName}
                          {dayState?.status === 'done' && <span className="ml-1 text-xs">✓</span>}
                          {dayState?.status === 'generating' && (
                            <div className="inline-block animate-spin h-3 w-3 border-b-2 border-pink-500 rounded-full ml-1"></div>
                          )}
                        </button>
                      )
                    })}
                  </div>

                  {/* 当前选中天的内容 */}
                  {renderDayContent(days[selectedDay - 1])}
                </div>
              )}
            </>
          ) : error ? (
            <>
              <div className="text-red-500 text-4xl mb-4">❌</div>
              <h2 className="text-2xl font-semibold text-gray-800 mb-2">
                生成失败
              </h2>
              <p className="text-red-600 mb-4">{error}</p>
              <button
                onClick={() => {
                  const babyId = searchParams.get('baby_id')
                  if (babyId) {
                    generateRecipe(babyId)
                  }
                }}
                className="px-6 py-2 min-h-[48px] flex items-center justify-center mx-auto bg-pink-500 text-white rounded-lg hover:bg-pink-600"
              >
                重试
              </button>
            </>
          ) : recipe ? (
            <div>
              <div className="text-green-500 text-4xl mb-4">✅</div>
              <h2 className="text-2xl font-semibold text-gray-800 mb-2">
                食谱生成成功！
              </h2>
              <p className="text-gray-600">正在跳转...</p>
            </div>
          ) : (
            <>
              <div className="animate-pulse">
                <div className="h-8 bg-gray-200 rounded w-3/4 mx-auto mb-6"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3 mx-auto mb-8"></div>
                <div className="space-y-3 text-left max-w-md mx-auto">
                  <div className="h-6 bg-gray-200 rounded w-full"></div>
                  <div className="h-6 bg-gray-200 rounded w-full"></div>
                  <div className="h-6 bg-gray-200 rounded w-full"></div>
                </div>
                <div className="mt-8 h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
