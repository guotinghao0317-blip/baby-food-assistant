'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const RESUME_DATA_KEY = 'onboarding_resume_data'

// 选项配置
const FEEDING_STAGES = [
  '纯母乳/配方奶 + 刚开始添加',
  '已适应泥状',
  '可吃软块状',
  '可吃手指食物'
]

const TEETHING_STATUS = [
  '未出牙',
  '已出2-4颗',
  '已出4-8颗',
  '已出8颗以上'
]

const ALLERGIES = [
  '鸡蛋', '牛奶', '花生', '坚果', '海鲜', '大豆', '小麦', '无'
]

const DIETARY_NEEDS = [
  '无', '素食', '无麸质', '其他'
]

const DIGESTION_STATUS = [
  '正常', '容易便秘', '容易腹泻', '其他'
]

const COMMON_INGREDIENTS = [
  '胡萝卜', '南瓜', '苹果', '香蕉', '鸡肉', '鱼肉', '牛肉', '猪肉',
  '土豆', '西兰花', '菠菜', '豆腐', '鸡蛋', '小米', '大米'
]

const FAMILY_DIET_STYLES = [
  '中式', '西式', '混合', '其他'
]

export default function Onboarding() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [needsReauth, setNeedsReauth] = useState(false)

  // 初始化表单状态，所有字段都是空的
  const [formData, setFormData] = useState({
    name: '',
    age_months: '',          // string 类型，因为是 select 的 value
    weight: '',
    height: '',
    feeding_stage: '',
    teething_status: '',
    months_since_weaning: '',
    allergies: [] as string[],
    dietary_needs: '',
    digestion_status: '',
    liked_ingredients: [] as string[],
    disliked_ingredients: [] as string[],
    family_diet_style: ''
  })

  const formDataRef = useRef(formData)
  formDataRef.current = formData

  const getToken = () => localStorage.getItem('token')

  const redirectToLogin = () => {
    const returnTo = encodeURIComponent('/onboarding')
    window.location.href = `/login?returnTo=${returnTo}`
  }

  const hasCheckedAuth = useRef(false)

  useEffect(() => {
    if (hasCheckedAuth.current) return
    hasCheckedAuth.current = true
    const token = getToken()
    if (!token) {
      redirectToLogin()
    }
  }, [router])

  // 切换下一步
  const handleNext = () => {
    const hasError = validateCurrentStep()
    if (!hasError) {
      setStep(step + 1)
    }
  }

  // 切换上一步
  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1)
    }
  }

  // 验证当前步骤是否通过
  const validateCurrentStep = () => {
    let hasError = false
    setFieldErrors({})

    if (step === 1) {
      // 必须选择月龄，月龄必须 > 0
      if (!formData.age_months || parseInt(formData.age_months) <= 0) {
        setFieldErrors({ age_months: '请选择宝宝月龄' })
        hasError = true
      }
      // 验证体重（如果填了）
      if (formData.weight && isNaN(parseFloat(formData.weight))) {
        setFieldErrors(prev => ({ ...prev, weight: '体重必须是有效数字' }))
        hasError = true
      }
      // 验证身高（如果填了）
      if (formData.height && isNaN(parseFloat(formData.height))) {
        setFieldErrors(prev => ({ ...prev, height: '身高必须是有效数字' }))
        hasError = true
      }
    }

    if (step === 2) {
      if (!formData.feeding_stage) {
        setFieldErrors(prev => ({ ...prev, feeding_stage: '请选择当前进食能力' }))
        hasError = true
      }
      if (!formData.teething_status) {
        setFieldErrors(prev => ({ ...prev, teething_status: '请选择出牙情况' }))
        hasError = true
      }
      if (formData.months_since_weaning && isNaN(parseFloat(formData.months_since_weaning))) {
        setFieldErrors(prev => ({ ...prev, months_since_weaning: '已添加辅食几个月必须是有效数字' }))
        hasError = true
      }
    }

    if (step === 3) {
      if (formData.allergies.includes('无') && formData.allergies.length > 1) {
        setFieldErrors({ allergies: '过敏源选择了"无"时不能同时选择其他项' })
        hasError = true
      }
    }

    if (step === 4) {
      const overlap = formData.liked_ingredients.filter(item =>
        formData.disliked_ingredients.includes(item)
      )
      if (overlap.length > 0) {
        setFieldErrors({
          liked_ingredients: `喜欢与不喜欢存在重复：${overlap.join('、')}`,
          disliked_ingredients: `喜欢与不喜欢存在重复：${overlap.join('、')}`
        })
        hasError = true
      }
    }

    return hasError // 返回 true 表示有错误
  }

  // 切换多选选项
  const toggleArray = (arr: string[], item: string) => {
    return arr.includes(item)
      ? arr.filter(i => i !== item)
      : [...arr, item]
  }

  // 构建提交数据，最后验证一次
  const buildSubmitData = () => {
    // 月龄必须转换为数字
    const age_months = formData.age_months ? parseInt(formData.age_months, 10) : 0

    // 最后一次验证
    if (age_months <= 0) {
      throw new Error('VALIDATION:age_months:请选择宝宝月龄:1')
    }
    if (!formData.feeding_stage) {
      throw new Error('VALIDATION:feeding_stage:请选择当前进食能力:2')
    }
    if (!formData.teething_status) {
      throw new Error('VALIDATION:teething_status:请选择出牙情况:2')
    }

    return {
      name: formData.name || null,
      age_months: age_months,
      weight: formData.weight ? parseFloat(formData.weight) : null,
      height: formData.height ? parseFloat(formData.height) : null,
      feeding_stage: formData.feeding_stage,
      teething_status: formData.teething_status,
      months_since_weaning: formData.months_since_weaning ? parseInt(formData.months_since_weaning, 10) : null,
      allergies: formData.allergies.filter(a => a !== '无'),
      dietary_needs: formData.dietary_needs || null,
      digestion_status: formData.digestion_status || null,
      liked_ingredients: formData.liked_ingredients,
      disliked_ingredients: formData.disliked_ingredients,
      family_diet_style: formData.family_diet_style || null
    }
  }

  // 提交表单
  const handleSubmit = async () => {
    setError('')
    setLoading(true)

    try {
      const token = getToken()
      if (!token) {
        redirectToLogin()
        return
      }

      const submitData = buildSubmitData()
      console.log('提交数据：', submitData)

      const response = await axios.post(
        `${API_URL}/api/babies`,
        submitData,
        { headers: { Authorization: `Bearer ${token}` } }
      )

      const babyId = response.data.id
      console.log('宝宝信息创建成功，baby_id=', babyId)

      // 跳转到营养分析页面
      window.location.href = `/nutrition/${babyId}`
    } catch (err: any) {
      console.error('提交错误：', err)

      // 检查是不是我们抛出来的验证错误
      if (err.message && err.message.startsWith('VALIDATION:')) {
        const [_, fieldId, message, stepStr] = err.message.split(':')
        setError(message)
        setStep(parseInt(stepStr))
        setFieldErrors({ [fieldId]: message })
      }
      else if (err.response?.status === 401) {
        localStorage.removeItem('token')
        setError('登录已过期，请重新登录')
        setNeedsReauth(true)
      }
      else if (err.response?.data?.detail) {
        setError(err.response.data.detail)
      }
      else {
        setError('网络错误，请检查后端服务')
      }
      setLoading(false)
    }
  }

  // 是否允许点击下一步
  const canGoNext = () => {
    if (step === 1) {
      return formData.age_months && parseInt(formData.age_months) > 0
    }
    if (step === 2) {
      return formData.feeding_stage && formData.teething_status
    }
    return true
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-orange-50 py-8 px-3 sm:px-4">
      <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-lg p-4 md:p-8">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-6 text-center">
          🍼 宝宝信息收集
        </h1>

        {/* 进度条 */}
        <div className="mb-8">
          <div className="flex justify-between mb-2">
            <span className="text-sm text-gray-600">步骤 {step} / 4</span>
            <span className="text-sm text-gray-600">{Math.round((step / 4) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-pink-500 h-2 rounded-full transition-all"
              style={{ width: `${(step / 4) * 100}%` }}
            />
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            <div>{error}</div>
            {needsReauth && (
              <button
                onClick={redirectToLogin}
                className="mt-3 px-4 py-2 bg-pink-500 text-white rounded-lg hover:bg-pink-600"
              >
                重新登录并继续生成
              </button>
            )}
          </div>
        )}

        {/* ========== 步骤 1 ========== */}
        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold mb-4">基础信息</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                宝宝昵称（可选）
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500"
                placeholder="如：小宝"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                宝宝年龄（月龄）<span className="text-red-500">*</span>
              </label>
              <select
                id="age_months"
                value={formData.age_months}
                onChange={(e) => setFormData({...formData, age_months: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500"
              >
                <option value="">请选择</option>
                {Array.from({ length: 25 }, (_, i) => (
                  <option key={i} value={i}>{i} 个月</option>
                ))}
              </select>
              {fieldErrors.age_months && (
                <p className="text-sm text-red-600 mt-1">{fieldErrors.age_months}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3 md:gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  体重（kg，可选）
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.weight}
                  onChange={(e) => setFormData({...formData, weight: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500"
                  placeholder="如：8.5"
                />
                {fieldErrors.weight && (
                  <p className="text-sm text-red-600 mt-1">{fieldErrors.weight}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  身高（cm，可选）
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.height}
                  onChange={(e) => setFormData({...formData, height: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500"
                  placeholder="如：70"
                />
                {fieldErrors.height && (
                  <p className="text-sm text-red-600 mt-1">{fieldErrors.height}</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ========== 步骤 2 ========== */}
        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold mb-4">发育阶段</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                当前进食能力 <span className="text-red-500">*</span>
              </label>
              <div className="space-y-2">
                {FEEDING_STAGES.map((stage) => (
                  <label key={stage} className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-pink-50">
                    <input
                      type="radio"
                      name="feeding_stage"
                      value={stage}
                      checked={formData.feeding_stage === stage}
                      onChange={(e) => setFormData({...formData, feeding_stage: e.target.value})}
                      className="mr-3"
                    />
                    <span>{stage}</span>
                  </label>
                ))}
              </div>
              {fieldErrors.feeding_stage && (
                <p className="text-sm text-red-600 mt-1">{fieldErrors.feeding_stage}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                出牙情况 <span className="text-red-500">*</span>
              </label>
              <div className="space-y-2">
                {TEETHING_STATUS.map((status) => (
                  <label key={status} className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-pink-50">
                    <input
                      type="radio"
                      name="teething_status"
                      value={status}
                      checked={formData.teething_status === status}
                      onChange={(e) => setFormData({...formData, teething_status: e.target.value})}
                      className="mr-3"
                    />
                    <span>{status}</span>
                  </label>
                ))}
              </div>
              {fieldErrors.teething_status && (
                <p className="text-sm text-red-600 mt-1">{fieldErrors.teething_status}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                已添加辅食几个月（可选）
              </label>
              <input
                type="number"
                min="0"
                value={formData.months_since_weaning}
                onChange={(e) => setFormData({...formData, months_since_weaning: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500"
                placeholder="如：6"
              />
              {fieldErrors.months_since_weaning && (
                <p className="text-sm text-red-600 mt-1">{fieldErrors.months_since_weaning}</p>
              )}
            </div>
          </div>
        )}

        {/* ========== 步骤 3 ========== */}
        {step === 3 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold mb-4">健康与过敏信息</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                已知过敏源（可多选）
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {ALLERGIES.map((allergy) => (
                  <label key={allergy} className="flex items-center p-2 border rounded cursor-pointer hover:bg-pink-50">
                    <input
                      type="checkbox"
                      checked={formData.allergies.includes(allergy)}
                      onChange={() => setFormData({
                        ...formData,
                        allergies: toggleArray(formData.allergies, allergy)
                      })}
                      className="mr-2"
                    />
                    <span>{allergy}</span>
                  </label>
                ))}
              </div>
              {fieldErrors.allergies && (
                <p className="text-sm text-red-600 mt-1">{fieldErrors.allergies}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                特殊饮食需求
              </label>
              <select
                value={formData.dietary_needs}
                onChange={(e) => setFormData({...formData, dietary_needs: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500"
              >
                <option value="">请选择</option>
                {DIETARY_NEEDS.map((need) => (
                  <option key={need} value={need}>{need}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                消化情况
              </label>
              <select
                value={formData.digestion_status}
                onChange={(e) => setFormData({...formData, digestion_status: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500"
              >
                <option value="">请选择</option>
                {DIGESTION_STATUS.map((status) => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* ========== 步骤 4 ========== */}
        {step === 4 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold mb-4">偏好信息</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                宝宝喜欢的食材（可多选）
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-60 overflow-y-auto p-2 border rounded">
                {COMMON_INGREDIENTS.map((ingredient) => (
                  <label key={ingredient} className="flex items-center p-1 cursor-pointer hover:bg-pink-50">
                    <input
                      type="checkbox"
                      checked={formData.liked_ingredients.includes(ingredient)}
                      onChange={() => setFormData({
                        ...formData,
                        liked_ingredients: toggleArray(formData.liked_ingredients, ingredient)
                      })}
                      className="mr-2"
                    />
                    <span className="text-sm">{ingredient}</span>
                  </label>
                ))}
              </div>
              {fieldErrors.liked_ingredients && (
                <p className="text-sm text-red-600 mt-1">{fieldErrors.liked_ingredients}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                宝宝不喜欢的食材（可多选）
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-60 overflow-y-auto p-2 border rounded">
                {COMMON_INGREDIENTS.map((ingredient) => (
                  <label key={ingredient} className="flex items-center p-1 cursor-pointer hover:bg-pink-50">
                    <input
                      type="checkbox"
                      checked={formData.disliked_ingredients.includes(ingredient)}
                      onChange={() => setFormData({
                        ...formData,
                        disliked_ingredients: toggleArray(formData.disliked_ingredients, ingredient)
                      })}
                      className="mr-2"
                    />
                    <span className="text-sm">{ingredient}</span>
                  </label>
                ))}
              </div>
              {fieldErrors.disliked_ingredients && (
                <p className="text-sm text-red-600 mt-1">{fieldErrors.disliked_ingredients}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                家庭饮食习惯
              </label>
              <select
                value={formData.family_diet_style}
                onChange={(e) => setFormData({...formData, family_diet_style: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500"
              >
                <option value="">请选择</option>
                {FAMILY_DIET_STYLES.map((style) => (
                  <option key={style} value={style}>{style}</option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* 按钮 */}
        <div className="flex justify-between mt-6 md:mt-8 gap-3">
          <button
            onClick={handleBack}
            disabled={step === 1}
            className="px-4 py-2 min-h-[48px] flex items-center justify-center border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            上一步
          </button>

          {step < 4 ? (
            <button
              onClick={handleNext}
              disabled={!canGoNext()}
              className="px-4 py-2 min-h-[48px] flex items-center justify-center bg-pink-500 text-white rounded-lg hover:bg-pink-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一步
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="px-4 py-2 min-h-[48px] flex items-center justify-center bg-pink-500 text-white rounded-lg hover:bg-pink-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center">
                  <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
                  提交中...
                </span>
              ) : (
                '完成并生成食谱'
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
