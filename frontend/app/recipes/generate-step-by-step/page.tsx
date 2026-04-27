'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
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

export default function GenerateRecipeStepByStep() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const [recipeId, setRecipeId] = useState<number | null>(null)
  const [days, setDays] = useState<DayGenerationState[]>(() =>
    Array.from({ length: 7 }, (_, i) => ({
      day: i + 1,
      status: 'pending' as const,
      details: undefined
    }))
  )
  const [selectedDay, setSelectedDay] = useState<number>(1)
  const [overallStatus, setOverallStatus] = useState<'idle' | 'generating' | 'finished' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState<string>('')

  const abortControllerRef = useRef<AbortController | null>(null)
  const userHasManualSelection = useRef(false)

  const getToken = () => {
    return localStorage.getItem('token')
  }

  useEffect(() => {
    const token = getToken()
    if (!token) {
      console.log('未找到token，跳转到登录页')
      router.push('/login')
      return
    }

    const babyIdParam = searchParams.get('baby_id')
    if (!babyIdParam) {
      console.log('缺少baby_id参数')
      setErrorMessage('缺少宝宝ID')
      setOverallStatus('error')
      return
    }

    console.log('开始分步生成食谱，baby_id:', babyIdParam)
    setTimeout(() => {
      startGeneration(babyIdParam)
    }, 100)

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [searchParams, router])

  // 简化后的 handleSSEEvent，只处理5种事件
  const handleSSEEvent = (event: any) => {
    switch (event.type) {
      case 'started':
        console.log('生成已开始，recipe_id:', event.recipe_id)
        setRecipeId(event.recipe_id)
        break

      case 'day_started':
        console.log('开始生成第', event.day, '天')
        setDays(prev => prev.map(d =>
          d.day === event.day ? { ...d, status: 'generating' } : d
        ))
        // 用户没手动点击过tab时，自动切换到正在生成的天
        if (!userHasManualSelection.current) {
          setSelectedDay(event.day)
        }
        break

      case 'dish_done':
        // 每道菜生成完立即追加到当天details中，实现逐菜展示
        if (event.detail && event.day) {
          setDays(prev => prev.map(d => {
            if (d.day === event.day) {
              const existingDetails = d.details || []
              const alreadyExists = existingDetails.some(
                (dish: any) => dish.id === event.detail.id || dish.meal_type === event.detail.meal_type
              )
              if (alreadyExists) return d
              return { ...d, details: [...existingDetails, event.detail] }
            }
            return d
          }))
          if (!userHasManualSelection.current) {
            setSelectedDay(event.day)
          }
        }
        break

      case 'day_done':
        console.log('第', event.day, '天生成完成，', event.details?.length, '道菜')
        setDays(prev => prev.map(d => {
          if (d.day === event.day) {
            const finalDetails = (event.details && event.details.length > 0)
              ? event.details
              : d.details
            return { ...d, status: 'done', details: finalDetails }
          }
          return d
        }))
        break

      case 'finished':
        console.log('全部7天生成完成，recipe_id:', event.recipe_id)
        setOverallStatus('finished')
        break

      case 'error':
        console.error('生成过程错误:', event.message)
        setErrorMessage(event.message)
        setOverallStatus('error')
        break

      default:
        console.log('未知事件类型:', event.type)
    }
  }

  // 开始生成
  const startGeneration = async (babyId: string) => {
    setOverallStatus('generating')
    setErrorMessage('')

    try {
      const token = getToken()
      if (!token) {
        router.push('/login')
        return
      }

      const startResponse = await fetch(
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

      if (startResponse.status === 401) {
        localStorage.removeItem('token')
        router.push('/login')
        return
      }

      if (!startResponse.ok) {
        throw new Error(`HTTP error! status: ${startResponse.status}`)
      }

      const startData = await startResponse.json()
      const currentRecipeId = startData.recipe_id
      setRecipeId(currentRecipeId)
      console.log('Created recipe:', currentRecipeId)

      handleSSEEvent({ type: 'started', recipe_id: currentRecipeId })

      // 逐天生成，直到完成
      while (true) {
        if (abortControllerRef.current?.signal.aborted) {
          break
        }

        const statusResponse = await fetch(
          `${API_URL}/api/recipes/recipe-status/${currentRecipeId}`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        )
        const statusData = await statusResponse.json()

        if (statusData.status === 'completed' || statusData.generated_days >= 7) {
          handleSSEEvent({ type: 'finished', recipe_id: currentRecipeId })
          setOverallStatus('finished')
          break
        }

        await generateNextDay(currentRecipeId, token)
      }
    } catch (err: any) {
      console.error('分步生成错误:', err)
      if (err.name !== 'AbortError') {
        setErrorMessage(err.message || '生成失败，请重试')
        setOverallStatus('error')
      }
    }
  }

  // 生成下一天
  const generateNextDay = async (recipeId: number, token: string) => {
    return new Promise<void>((resolve) => {
      const abortController = new AbortController()
      abortControllerRef.current = abortController

      fetch(
        `${API_URL}/api/recipes/generate-next-day/${recipeId}`,
        {
          headers: { 'Authorization': `Bearer ${token}` },
          signal: abortController.signal,
        }
      )
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const reader = response.body?.getReader()
        if (!reader) {
          throw new Error('无法读取响应流')
        }

        const decoder = new TextDecoder()
        let buffer = ''

        const readNext = async () => {
          const { done, value } = await reader.read()
          if (done) {
            resolve()
            return
          }

          buffer += decoder.decode(value, { stream: true })
          const events = buffer.split('\n\n')
          buffer = events.pop() || ''

          for (const event of events) {
            const data = parseSSE(event)
            if (!data) continue
            handleSSEEvent(data)
          }

          readNext()
        }

        readNext()
      })
      .catch(err => {
        console.error('生成下一天错误:', err)
        if (err.name !== 'AbortError') {
          setErrorMessage(err.message || '生成失败，请重试')
          setOverallStatus('error')
        }
        resolve()
      })
    })
  }

  // 处理天数卡片点击
  const handleDayClick = (day: DayGenerationState) => {
    if (day.status === 'done' || day.status === 'generating') {
      userHasManualSelection.current = true
      setSelectedDay(day.day)
    }
  }

  // 取消生成
  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    router.push('/onboarding')
  }

  // 查看完整食谱
  const handleViewFullRecipe = () => {
    if (recipeId) {
      router.push(`/recipes/${recipeId}`)
    }
  }

  // 重试
  const handleRetry = () => {
    const babyId = searchParams.get('baby_id')
    if (babyId) {
      userHasManualSelection.current = false
      setDays(Array.from({ length: 7 }, (_, i) => ({
        day: i + 1,
        status: 'pending' as const,
        details: undefined
      })))
      setRecipeId(null)
      setSelectedDay(1)
      setOverallStatus('generating')
      setErrorMessage('')
      startGeneration(babyId)
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

                {dish.image_url && (
                  <img
                    src={dish.image_url}
                    alt={dish.dish_name}
                    className="w-full h-40 object-cover rounded mb-3 animate-fadeIn"
                  />
                )}

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

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-orange-50 py-8 px-3 sm:px-4">
      <div className="max-w-6xl mx-auto">
        {/* 顶部标题 */}
        <div className="bg-white rounded-xl shadow-lg p-4 md:p-6 mb-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
            <div>
              <h1 className="text-xl md:text-2xl font-bold text-gray-800">
                {overallStatus === 'finished'
                  ? '一周食谱生成完成'
                  : overallStatus === 'error'
                  ? '生成出现问题'
                  : 'AI 正在逐步生成一周食谱'
                }
              </h1>
              <p className="text-gray-500 mt-1">
                {overallStatus === 'generating'
                  ? '已生成的天可以随时点击查看，不需要等待全部完成'
                  : overallStatus === 'finished'
                  ? '全部7天已生成完成，点击下方查看完整食谱'
                  : errorMessage
                }
              </p>
            </div>
            {overallStatus === 'generating' && (
              <button
                onClick={handleCancel}
                className="px-4 py-2 min-h-[48px] text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                取消生成
              </button>
            )}
            {overallStatus === 'finished' && (
              <button
                onClick={handleViewFullRecipe}
                className="px-6 py-2 min-h-[48px] bg-pink-500 text-white rounded-lg hover:bg-pink-600 transition-colors"
              >
                查看完整食谱
              </button>
            )}
            {overallStatus === 'error' && (
              <button
                onClick={handleRetry}
                className="px-6 py-2 min-h-[48px] bg-pink-500 text-white rounded-lg hover:bg-pink-600 transition-colors"
              >
                重新生成
              </button>
            )}
          </div>
        </div>

        {/* 7天进度卡片区域 */}
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-3 mb-6">
          {days.map((dayState) => {
            const isSelected = selectedDay === dayState.day
            let cardClasses = 'relative p-3 rounded-lg border transition-all duration-300 cursor-pointer'

            if (dayState.status === 'done') {
              cardClasses += ` bg-green-100 border-green-300 hover:shadow-md hover:-translate-y-1 ${
                isSelected ? 'ring-2 ring-green-500 shadow-md' : ''
              }`
            } else if (dayState.status === 'generating') {
              cardClasses += ' bg-pink-100 border-pink-300 animate-pulse'
            } else {
              cardClasses += ' bg-gray-100 border-gray-200 text-gray-400 cursor-not-allowed opacity-60'
            }

            return (
              <div
                key={dayState.day}
                className={cardClasses}
                onClick={() => handleDayClick(dayState)}
              >
                <div className="flex items-center justify-center gap-2">
                  <span className="font-medium text-sm md:text-base">
                    {DAYS[dayState.day - 1]}
                  </span>
                  {dayState.status === 'done' && (
                    <span className="text-green-600">✓</span>
                  )}
                  {dayState.status === 'generating' && (
                    <div className="animate-spin h-4 w-4 border-b-2 border-pink-500 rounded-full"></div>
                  )}
                </div>
                <div className="text-xs text-center mt-1 opacity-70">
                  {dayState.status === 'done'
                    ? '已完成'
                    : dayState.status === 'generating'
                    ? '生成中...'
                    : '等待中'
                  }
                </div>
              </div>
            )
          })}
        </div>

        {/* 当前选中天的详细内容 */}
        <div className="bg-white rounded-xl shadow-lg p-4 md:p-6">
          <h2 className="text-lg md:text-xl font-semibold text-gray-800 mb-4">
            {DAYS[selectedDay - 1]} 辅食
          </h2>
          {renderDayContent(days[selectedDay - 1])}
        </div>

        {/* 底部提示 */}
        {overallStatus === 'generating' && (
          <div className="mt-6 text-center text-sm text-gray-500">
            <p>提示：生成完成的天会自动变绿，点击即可查看内容</p>
          </div>
        )}
      </div>
    </div>
  )
}
