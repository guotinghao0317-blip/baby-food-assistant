'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter, useParams } from 'next/navigation'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const CACHE_KEY = (recipeId: string) => `recipe_cache_${recipeId}`

const DAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

// FE-6: 去掉加餐，但兼容旧数据中可能存在的snack
const MEAL_TYPES: Record<string, string> = {
  breakfast: '早餐',
  lunch: '午餐',
  dinner: '晚餐',
  // snack保留用于兼容旧数据，但新生成不再包含
  snack: '加餐'
}

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

export default function RecipeDetail() {
  const router = useRouter()
  const params = useParams()
  const recipeId = params.id as string

  const [recipe, setRecipe] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedDay, setSelectedDay] = useState(1)
  const [regeneratingId, setRegeneratingId] = useState<number | null>(null)
  const [streamingDish, setStreamingDish] = useState<any>(null)

  const [days, setDays] = useState<DayGenerationState[]>(() =>
    Array.from({ length: 7 }, (_, i) => ({
      day: i + 1,
      status: 'pending' as const,
      details: undefined
    }))
  )
  const [overallStatus, setOverallStatus] = useState<'idle' | 'generating' | 'finished' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState<string>('')

  const abortControllerRef = useRef<AbortController | null>(null)
  const isMountedRef = useRef(true)
  const userHasManualSelection = useRef(false)

  const getToken = () => {
    return localStorage.getItem('token')
  }

  // 从localStorage加载缓存
  const loadCache = () => {
    try {
      const cacheKey = CACHE_KEY(recipeId)
      const cached = localStorage.getItem(cacheKey)
      if (cached) {
        const parsed = JSON.parse(cached)
        if (parsed.days && Array.isArray(parsed.days) && parsed.overallStatus) {
          // 格式校验：如果有 dishes 字段说明是旧格式，清除
          if (parsed.days[0] && parsed.days[0].dishes !== undefined) {
            console.log('检测到旧版缓存格式，清除重载')
            localStorage.removeItem(cacheKey)
            return false
          }
          console.log('从localStorage加载缓存成功')
          setDays(parsed.days)
          setOverallStatus(parsed.overallStatus)
          if (parsed.selectedDay) {
            setSelectedDay(parsed.selectedDay)
          }
          return true
        }
      }
    } catch (err) {
      console.warn('加载缓存失败:', err)
    }
    return false
  }

  // 保存缓存到localStorage
  const saveCache = useCallback(() => {
    try {
      const cacheKey = CACHE_KEY(recipeId)
      const cacheData = {
        days,
        overallStatus,
        selectedDay,
        cachedAt: new Date().toISOString()
      }
      localStorage.setItem(cacheKey, JSON.stringify(cacheData))
    } catch (err) {
      console.warn('保存缓存失败:', err)
    }
  }, [days, overallStatus, selectedDay, recipeId])

  // 清除缓存
  const clearCache = () => {
    try {
      const cacheKey = CACHE_KEY(recipeId)
      localStorage.removeItem(cacheKey)
    } catch (err) {
      console.warn('清除缓存失败:', err)
    }
  }

  // 重新生成全部食谱
  const handleRegenerateAll = () => {
    clearCache()
    userHasManualSelection.current = false
    setDays(Array.from({ length: 7 }, (_, i) => ({
      day: i + 1,
      status: 'pending' as const,
      details: undefined
    })))
    setOverallStatus('generating')
    setErrorMessage('')
    startGeneration()
  }

  useEffect(() => {
    isMountedRef.current = true
    if (recipeId) {
      const hasCache = loadCache()
      console.log('缓存加载结果:', hasCache ? '有缓存' : '无缓存')

      fetchRecipe().then(() => {
        setTimeout(() => {
          const currentDays = days
          const completedDays = currentDays.filter(d => d.status === 'done').length
          console.log(`当前已完成天数: ${completedDays}/7`)

          if (hasCache && completedDays === 7) {
            console.log('从缓存加载完成，不需要重新生成')
            return
          }

          if (completedDays < 7) {
            console.log(`还有 ${7 - completedDays} 天需要生成，开始生成...`)
            startGeneration()
          }
        }, 100)
      }).catch(err => {
        console.error('加载食谱失败:', err)
      })
    }

    return () => {
      isMountedRef.current = false
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [recipeId])

  const fetchRecipe = async () => {
    try {
      const token = getToken()
      if (!token) {
        router.push('/login')
        return
      }

      const response = await axios.get(
        `${API_URL}/api/recipes/${recipeId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      const recipeData = response.data
      console.log('从后端加载的食谱数据:', recipeData)
      setRecipe(recipeData)

      // 从数据库数据中提取已生成的天数，更新days状态
      if (recipeData.details && Array.isArray(recipeData.details) && recipeData.details.length > 0) {
        console.log(`共加载 ${recipeData.details.length} 道菜`)

        const completedDays = new Set<number>()
        const dayMealCounts: Record<number, number> = {}

        recipeData.details.forEach((detail: any) => {
          if (detail.day_of_week && typeof detail.day_of_week === 'number') {
            completedDays.add(detail.day_of_week)
            dayMealCounts[detail.day_of_week] = (dayMealCounts[detail.day_of_week] || 0) + 1
          }
        })

        console.log('已生成的天数统计:', dayMealCounts)

        // 更新days数组状态：有数据的天设为done，并填充details
        setDays(prevDays => {
          const newDays = prevDays.map(d => {
            if (completedDays.has(d.day)) {
              // 生成中时，保留当前状态
              if (d.status === 'generating') {
                console.log(`第 ${d.day} 天 (${DAYS[d.day - 1]}) 正在生成中，保留当前状态`)
                return d
              }

              const dayDishes = recipeData.details.filter((detail: any) =>
                detail.day_of_week === d.day
              )
              console.log(`第 ${d.day} 天 (${DAYS[d.day - 1]}) 已完成，菜品数: ${dayDishes.length}`)

              return {
                ...d,
                status: 'done' as const,
                details: dayDishes
              }
            }
            return d
          })

          return newDays
        })

        const allDaysCompleted = completedDays.size === 7
        if (allDaysCompleted) {
          console.log('所有7天的数据都已加载完成')
          setOverallStatus('finished')
          saveCache()
        } else {
          console.log(`还有 ${7 - completedDays.size} 天需要生成`)
          if (overallStatus === 'idle') {
            setOverallStatus('generating')
          }
        }
      } else {
        console.log('没有找到已生成的食谱数据，从头开始生成')
        setDays(Array.from({ length: 7 }, (_, i) => ({
          day: i + 1,
          status: 'pending' as const,
          details: undefined
        })))
      }
    } catch (err: any) {
      console.error('加载已有食谱失败:', err)
      if (err.response?.status === 401) {
        router.push('/login')
      } else {
        console.warn('加载已有食谱失败，将从头开始生成:', err)
        setDays(Array.from({ length: 7 }, (_, i) => ({
          day: i + 1,
          status: 'pending' as const,
          details: undefined
        })))
      }
    } finally {
      setLoading(false)
    }
  }

  // 开始逐天生成
  const startGeneration = async () => {
    const token = getToken()
    if (!token) {
      router.push('/login')
      return
    }

    setOverallStatus('generating')
    setErrorMessage('')

    try {
      const numericRecipeId = parseInt(recipeId)
      console.log('开始分步生成食谱，recipeId:', numericRecipeId)

      while (isMountedRef.current && !abortControllerRef.current?.signal.aborted) {
        const statusResponse = await fetch(
          `${API_URL}/api/recipes/recipe-status/${numericRecipeId}`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        )
        const statusData = await statusResponse.json()
        console.log('当前生成状态:', statusData)

        const isReallyCompleted = statusData.status === 'completed' && statusData.generated_days >= 7
        if (isReallyCompleted) {
          console.log('全部7天生成完成')
          setOverallStatus('finished')
          await fetchRecipe()
          saveCache()
          break
        }

        if (statusData.status === 'completed' && statusData.generated_days < 7) {
          console.warn('状态不一致：status=completed 但数据不足，继续生成')
        }

        console.log(`当前已生成 ${statusData.generated_days} 天，继续生成下一天`)
        await generateNextDay(numericRecipeId, token)
      }
    } catch (err: any) {
      console.error('分步生成错误:', err)
      if (err.name !== 'AbortError' && isMountedRef.current) {
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
        if (err.name !== 'AbortError' && isMountedRef.current) {
          setErrorMessage(err.message || '生成失败，请重试')
          setOverallStatus('error')
        }
        resolve()
      })
    })
  }

  // 简化后的 handleSSEEvent，只处理5种事件
  const handleSSEEvent = (event: any) => {
    if (!isMountedRef.current) return

    switch (event.type) {
      case 'day_started':
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
              // 避免重复添加同一道菜（通过id或meal_type判断）
              const alreadyExists = existingDetails.some(
                (dish: any) => dish.id === event.detail.id || dish.meal_type === event.detail.meal_type
              )
              if (alreadyExists) return d
              return { ...d, details: [...existingDetails, event.detail] }
            }
            return d
          }))
          // 用户没手动点击过tab时，自动切换到有新菜品的天
          if (!userHasManualSelection.current) {
            setSelectedDay(event.day)
          }
        }
        break

      case 'day_done':
        setDays(prev => prev.map(d => {
          if (d.day === event.day) {
            // 如果后端返回了完整的details，使用后端数据；否则保留已有的details
            const finalDetails = (event.details && event.details.length > 0)
              ? event.details
              : d.details
            return { ...d, status: 'done', details: finalDetails }
          }
          return d
        }))
        saveCache()
        break

      case 'finished':
        setOverallStatus('finished')
        saveCache()
        break

      case 'error':
        setErrorMessage(event.message)
        setOverallStatus('error')
        break
    }
  }

  // 当用户切换选中天时，保存缓存
  useEffect(() => {
    saveCache()
  }, [selectedDay, saveCache])

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

  // 重试
  const handleRetry = () => {
    setOverallStatus('generating')
    setErrorMessage('')
    startGeneration()
  }

  // 解析SSE格式的辅助函数（换一道菜功能使用）
  const parseSSEForRegenerate = (chunk: string) => {
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

  // 换一道菜：重新生成特定餐次的菜品
  const handleRegenerateDish = async (dayOfWeek: number, mealType: string, detailId: number) => {
    const token = getToken()
    if (!token) {
      router.push('/login')
      return
    }

    setRegeneratingId(detailId)
    setStreamingDish(null)

    let abortController: AbortController | null = new AbortController()

    try {
      console.log('开始流式重新生成菜品:', { dayOfWeek, mealType, detailId })

      const response = await fetch(
        `${API_URL}/api/recipes/${recipeId}/replace-dish-stream`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            day_of_week: dayOfWeek,
            meal_type: mealType,
            original_dish_id: detailId
          }),
          signal: abortController.signal,
        }
      )

      if (response.status === 401) {
        router.push('/login')
        return
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('无法读取响应流')
      }

      const decoder = new TextDecoder()
      let buffer = ''
      let streamedDish: any = {
        id: detailId,
        day_of_week: dayOfWeek,
        meal_type: mealType,
      }
      setStreamingDish({ ...streamedDish })

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const events = buffer.split('\n\n')
        buffer = events.pop() || ''

        for (const event of events) {
          const data = parseSSEForRegenerate(event)
          if (!data) continue

          if (data.type === 'chunk' && data.full_content) {
            // 累积内容
          } else if (data.type === 'done') {
            console.log('菜品重新生成完成', data.data)
            const newDish = data.data

            if (newDish) {
              await streamRenderDish(newDish)
              setRecipe((prevRecipe: any) => {
                if (!prevRecipe || !prevRecipe.details) {
                  return prevRecipe
                }
                return {
                  ...prevRecipe,
                  details: prevRecipe.details.map((dish: any) =>
                    dish.id === detailId ? newDish : dish
                  )
                }
              })
              // 更新days状态中的details
              setDays(prev => prev.map(d => {
                if (d.day === dayOfWeek) {
                  return {
                    ...d,
                    details: d.details?.map(dish =>
                      dish.id === detailId ? newDish : dish
                    )
                  }
                }
                return d
              }))
              saveCache()
            }
          } else if (data.type === 'error') {
            throw new Error(data.message)
          }
        }
      }
      setRegeneratingId(null)
      setStreamingDish(null)
      abortController = null
    } catch (err: any) {
      console.error('重新生成失败:', err)
      if (err.name !== 'AbortError') {
        if (err.message.includes('401')) {
          router.push('/login')
        } else {
          alert('重新生成失败，请重试')
        }
      }
      setRegeneratingId(null)
      setStreamingDish(null)
      abortController = null
    }
  }

  // 前端流式输出渲染单个菜品
  const streamRenderDish = async (newDish: any) => {
    const streamed: any = {
      id: newDish.id,
      day_of_week: newDish.day_of_week,
      meal_type: newDish.meal_type,
    }
    setStreamingDish({ ...streamed })
    await sleep(300)

    streamed.dish_name = newDish.dish_name
    setStreamingDish({ ...streamed })
    await sleep(400)

    streamed.ingredients = []
    setStreamingDish({ ...streamed })
    await sleep(300)
    for (let i = 0; i < (newDish.ingredients?.length || 0); i++) {
      streamed.ingredients.push(newDish.ingredients[i])
      setStreamingDish({ ...streamed })
      await sleep(200)
    }

    streamed.cooking_steps = []
    setStreamingDish({ ...streamed })
    await sleep(300)
    for (let i = 0; i < (newDish.cooking_steps?.length || 0); i++) {
      streamed.cooking_steps.push(newDish.cooking_steps[i])
      setStreamingDish({ ...streamed })
      await sleep(300)
    }

    if (newDish.nutrition_info) {
      streamed.nutrition_info = newDish.nutrition_info
      setStreamingDish({ ...streamed })
      await sleep(300)
    }

    if (newDish.image_url) {
      streamed.image_url = newDish.image_url
      setStreamingDish({ ...streamed })
    }
  }

  const sleep = (ms: number) => {
    return new Promise(resolve => setTimeout(resolve, ms))
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
            const isRegenerating = regeneratingId === dish.id

            return (
              <div key={dish.id} className="border rounded-lg p-3 md:p-4 hover:shadow-md transition-shadow animate-fadeIn relative">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold text-gray-700">
                    {mealLabel}：{dish.dish_name}
                  </h3>
                  <button
                    className={`px-3 py-2 min-h-[48px] flex items-center text-xs bg-pink-100 text-pink-600 rounded-full hover:bg-pink-200 transition-colors ${
                      isRegenerating ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                    onClick={() => handleRegenerateDish(dayState.day, dish.meal_type, dish.id)}
                    disabled={isRegenerating}
                  >
                    {isRegenerating ? (
                      <span className="flex items-center gap-1">
                        <div className="animate-spin h-3 w-3 border-b-2 border-pink-600 rounded-full"></div>
                        生成中
                      </span>
                    ) : '换一道'}
                  </button>
                </div>

                {isRegenerating && !streamingDish && (
                  <div className="flex flex-col items-center justify-center py-8 animate-pulse">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500 mb-4"></div>
                    <p className="text-gray-500 text-sm">正在重新生成这道菜...</p>
                  </div>
                )}

                {dish.image_url && !(isRegenerating && !streamingDish) && (
                  <img
                    src={dish.image_url}
                    alt={dish.dish_name}
                    className="w-full h-40 object-cover rounded mb-3 animate-fadeIn"
                  />
                )}

                {/* 食材清单 */}
                {dish.ingredients && dish.ingredients.length > 0 && (!(isRegenerating && !streamingDish)) && (
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

                {/* 烹饪步骤 */}
                {dish.cooking_steps && dish.cooking_steps.length > 0 && (!(isRegenerating && !streamingDish)) && (
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

                {/* 营养信息 */}
                {dish.nutrition_info && (!(isRegenerating && !streamingDish)) && (
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

  if (loading && overallStatus === 'idle') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-50 to-orange-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-pink-500 mx-auto mb-4"></div>
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    )
  }

  if (error && !recipe) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-50 to-orange-50 flex items-center justify-center px-3 sm:px-4">
        <div className="bg-white rounded-xl shadow-lg p-4 md:p-8 text-center">
          <p className="text-red-600 mb-4">{error || '食谱不存在'}</p>
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-orange-50 py-8 px-3 sm:px-4">
      <div className="max-w-6xl mx-auto">
        {/* 顶部标题栏 */}
        <div className="bg-white rounded-xl shadow-lg p-4 md:p-6 mb-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
            <div>
              <h1 className="text-xl md:text-2xl font-bold text-gray-800">
                {overallStatus === 'finished'
                  ? '一周食谱生成完成'
                  : overallStatus === 'error'
                  ? '生成出现问题'
                  : 'AI 正在逐步生成一周食谱'}
              </h1>
              <p className="text-gray-500 mt-1">
                {overallStatus === 'generating'
                  ? '已生成的天可以随时点击查看，不需要等待全部完成'
                  : overallStatus === 'finished'
                  ? '全部7天已生成完成'
                  : errorMessage
                }
              </p>
            </div>
            <div className="flex gap-2">
              {overallStatus === 'generating' && (
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 min-h-[48px] text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  取消生成
                </button>
              )}
              {overallStatus !== 'generating' && (
                <button
                  onClick={handleRegenerateAll}
                  className="px-4 py-2 min-h-[48px] bg-pink-500 text-white rounded-lg hover:bg-pink-600 transition-colors"
                >
                  重新生成
                </button>
              )}
              {overallStatus === 'error' && (
                <button
                  onClick={handleRetry}
                  className="px-4 py-2 min-h-[48px] bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  重试
                </button>
              )}
            </div>
          </div>
        </div>

        {/* 7天水平Tab组件 */}
        <div className="bg-white rounded-xl shadow-lg mb-6 overflow-hidden">
          <div className="flex overflow-x-auto">
            {days.map((dayState) => {
              const isSelected = selectedDay === dayState.day
              let tabClasses = 'flex-shrink-0 px-4 py-3 min-w-[80px] text-center cursor-pointer transition-all duration-200 border-b-2'

              if (isSelected) {
                tabClasses += ' bg-pink-500 text-white border-pink-500'
              } else if (dayState.status === 'done') {
                tabClasses += ' bg-white text-gray-700 border-transparent hover:bg-gray-50'
              } else if (dayState.status === 'generating') {
                tabClasses += ' bg-white text-pink-500 border-transparent'
              } else {
                tabClasses += ' bg-gray-50 text-gray-400 border-transparent cursor-not-allowed opacity-60'
              }

              return (
                <div
                  key={dayState.day}
                  className={tabClasses}
                  onClick={() => handleDayClick(dayState)}
                >
                  <div className="flex items-center justify-center gap-1">
                    <span className="font-medium text-sm">
                      {DAYS[dayState.day - 1]}
                    </span>
                    {dayState.status === 'done' && (
                      <span className="text-xs">✓</span>
                    )}
                    {dayState.status === 'generating' && (
                      <div className="animate-spin h-3 w-3 border-b-2 border-current rounded-full"></div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* 当前选中天的详细内容卡片 */}
        <div className="bg-white rounded-xl shadow-lg p-4 md:p-6 mb-6">
          <h2 className="text-lg md:text-xl font-semibold text-gray-800 mb-4">
            {DAYS[selectedDay - 1]} 辅食
          </h2>
          {renderDayContent(days[selectedDay - 1])}
        </div>

        {/* 返回按钮 */}
        {overallStatus === 'finished' && (
          <div className="flex justify-center mt-6">
            <button
              onClick={() => router.push('/onboarding')}
              className="px-6 py-3 min-h-[48px] flex items-center justify-center text-pink-500 border border-pink-500 rounded-lg hover:bg-pink-50 transition-colors"
            >
              返回
            </button>
          </div>
        )}

        {/* 底部提示 */}
        {overallStatus === 'generating' && (
          <div className="mt-4 text-center text-sm text-gray-500">
            <p>提示：生成完成的天会自动激活，点击顶部tab即可查看内容</p>
          </div>
        )}
      </div>
    </div>
  )
}
