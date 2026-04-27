"""
火山引擎 CodingPlan API 客户端
用于动态生成宝宝辅食食谱

这就是所谓的 "CodingPlan" 服务，是火山引擎提供的大模型API服务，
用于智能生成宝宝辅食食谱。

特点：
- 支持流式和非流式生成
- 自动错误处理和降级机制
- 基于宝宝信息个性化生成
- 保证每次生成内容不同
"""
import os
import json
import re
import logging
import httpx
from typing import Dict, List, Optional, Any, AsyncGenerator
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def is_api_available() -> bool:
    """检查火山引擎API是否可用"""
    load_dotenv()
    api_key = os.getenv("VOLCENGINE_API_KEY", "")
    return bool(api_key and api_key != "your-volcengine-api-key-here")


class VolcengineClient:
    """火山引擎 CodingPlan API 客户端"""

    def __init__(self):
        # 每次初始化重新加载环境变量，确保获取最新配置
        load_dotenv()
        self.api_key = os.getenv("VOLCENGINE_API_KEY")
        self.base_url = os.getenv("VOLCENGINE_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        self.model_name = os.getenv("VOLCENGINE_MODEL_NAME", "doubao-1-5-pro-32k-250115")
        self.timeout = float(os.getenv("VOLCENGINE_TIMEOUT", "60"))
        self.temperature = float(os.getenv("VOLCENGINE_TEMPERATURE", "0.7"))
        self.is_configured = bool(self.api_key)

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> Optional[Dict[str, Any]]:
        """
        调用火山引擎API生成JSON格式响应
        返回解析后的字典，如果失败返回None
        """
        if not self.is_configured:
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": temperature,
            "response_format": {
                "type": "json_object"
            }
        }

        logger.info(f"Calling Volcengine API: model={self.model_name}, endpoint={self.base_url}, temperature={temperature}")
        logger.debug(f"System prompt length: {len(system_prompt)}, User prompt length: {len(user_prompt)}")

        try:
            async with httpx.AsyncClient() as client:
                # base_url 已经包含 /api/v3，所以直接拼 /chat/completions
                endpoint = f"{self.base_url.rstrip('/')}/chat/completions"
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code != 200:
                    logger.error(f"Volcengine API error: status {response.status_code}, response: {response.text[:500]}")
                    return None

                result = response.json()
                content = result["choices"][0]["message"]["content"]
                logger.info(f"Volcengine API SUCCESS: response length={len(content)}")
                logger.debug(f"API response preview: {content[:200]}...")

                # 清理LLM输出，处理常见格式问题
                content = self._clean_json_output(content)
                data = json.loads(content)
                return data

        except httpx.TimeoutException:
            logger.error(f"Volcengine API timeout after {self.timeout}s")
            return None
        except httpx.RequestError as e:
            logger.error(f"Volcengine API request error: {e}")
            return None
        except json.JSONDecodeError as e:
            content_preview = content[:200] if 'content' in locals() and content else 'N/A'
            logger.error(f"Failed to parse JSON response: {e}, content preview: {content_preview}")
            return None
        except KeyError as e:
            logger.error(f"Unexpected response format: missing key {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling Volcengine API: {e}", exc_info=True)
            return None

    async def stream_generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        调用火山引擎API进行流式生成
        以SSE方式逐块返回内容
        """
        if not self.is_configured:
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": temperature,
            "stream": True
        }

        logger.info(f"Starting Volcengine API stream: model={self.model_name}, endpoint={self.base_url}")

        try:
            async with httpx.AsyncClient() as client:
                endpoint = f"{self.base_url.rstrip('/')}/chat/completions"
                async with client.stream(
                    "POST",
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"Volcengine API stream error: status {response.status_code}, response: {error_text.decode('utf-8')[:500]}")
                        return

                    logger.info("Volcengine API stream started successfully")

                    # 缓冲处理，处理可能跨越多行的data块
                    buffer = ""
                    total_chunks = 0
                    async for chunk in response.aiter_bytes():
                        buffer += chunk.decode('utf-8')
                        # 按SSE规范分割，data块通常以\n\n结束
                        while '\n\n' in buffer:
                            line, buffer = buffer.split('\n\n', 1)
                            line = line.strip()
                            if not line:
                                continue
                            if line.startswith("data: "):
                                data = line[6:].strip()
                                if data == "[DONE]":
                                    logger.info(f"Volcengine API stream completed: {total_chunks} chunks")
                                    break
                                try:
                                    result = json.loads(data)
                                    if "choices" in result and len(result["choices"]) > 0:
                                        delta = result["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            total_chunks += 1
                                            yield delta["content"]
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Failed to parse stream chunk: {e}, data: {data[:200]}")
                                    continue
                            elif line.startswith(":"):
                                # 注释跳过
                                continue
                            else:
                                # 尝试直接解析（兼容非标准格式）
                                try:
                                    result = json.loads(line)
                                    if "choices" in result and len(result["choices"]) > 0:
                                        delta = result["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            total_chunks += 1
                                            yield delta["content"]
                                except json.JSONDecodeError:
                                    continue

        except httpx.TimeoutException:
            logger.error(f"Volcengine API stream timeout after {self.timeout}s")
            return
        except httpx.RequestError as e:
            logger.error(f"Volcengine API stream request error: {e}")
            return
        except Exception as e:
            logger.error(f"Unexpected error calling Volcengine API stream: {e}", exc_info=True)
            return

    def _build_baby_info_prompt(self, baby, nutrition=None) -> str:
        """构建宝宝信息部分的prompt"""
        prompt = f"""
## 宝宝信息
- 年龄：{baby.age_months}个月
- 进食能力：{baby.feeding_stage or '未知'}
- 出牙情况：{baby.teething_status or '未知'}
- 过敏源：{', '.join(baby.allergies) if baby.allergies else '无'}
- 喜欢的食材：{', '.join(baby.liked_ingredients) if baby.liked_ingredients else '无特殊偏好'}
- 不喜欢的食材：{', '.join(baby.disliked_ingredients) if baby.disliked_ingredients else '无'}
- 家庭饮食习惯：{baby.family_diet_style or '无特殊要求'}
"""
        if nutrition:
            prompt += f"""
## 营养需求（每日辅食部分）
- 每日热量目标：{nutrition.calories_per_day or 400} kcal
- 蛋白质需求：{nutrition.protein_g or 10} g
- 铁需求：{nutrition.iron_mg or 6} mg
- 钙需求：{nutrition.calcium_mg or 200} mg
"""
        return prompt

    def build_weekly_prompt(self, baby, nutrition=None,
                          start_day: int = 1, num_days: int = 7,
                          exclude_dish_names: Optional[List[str]] = None) -> str:
        """
        构建一周食谱生成的prompt
        """
        prompt = f"""你是一位专业的婴幼儿营养师，需要为{baby.age_months}个月的宝宝制定一周（{num_days}天）的完整辅食食谱。
"""
        prompt += self._build_baby_info_prompt(baby, nutrition)

        prompt += f"""
## 生成要求
1. **必须生成全新不重复的内容**，请不要使用常见的重复搭配，发挥创意
2. 生成{num_days}天完整食谱，从第{start_day}天开始，每天包含：早餐、午餐、晚餐（共3餐 × {num_days}天 = {num_days * 3}条记录）
3. 每道菜必须包含：
   - 菜品名称（中文，吸引人且符合宝宝特点）
   - 食材清单（含精确用量，如"胡萝卜 50g"）
   - 详细烹饪步骤（分步骤，适合对应进食能力阶段的宝宝）
   - 营养信息（能量kcal、蛋白质g、铁mg）
4. **严格规避过敏源**
5. **优先使用宝宝喜欢的食材**
6. 确保营养均衡，特别注意铁的补充
7. 食材质地符合对应进食能力阶段（如泥糊状、碎末状、小块状等）
8. 烹饪方法安全、简单，适合家庭制作
9. **食谱必须多样化，尽量减少重复菜品**，每餐搭配合理
10. **重要：每一次生成都要有新菜，不要重复之前的内容**
11. **菜名命名多样性要求**：菜名禁止使用相同的前缀或修饰词，例如不要出现"五彩鲜虾饼"和"五彩海鲜丁"这样用"五彩"开头的重复。每道菜的命名风格应各不相同，可以用食材名、烹饪方式、颜色、形状、寓意等不同角度命名
"""

        if exclude_dish_names and len(exclude_dish_names) > 0:
            exclude_list = "、".join(exclude_dish_names[:20])
            prompt += f"""
## 排除菜品（不要生成以下菜名）
{exclude_list}
"""

        day_start = start_day
        day_end = start_day + num_days - 1

        prompt += f"""
## 输出格式
请严格以JSON格式输出，结构如下：
{{
  "details": [
    {{
      "day_of_week": {day_start},
      "meal_type": "breakfast",
      "dish_name": "胡萝卜泥",
      "ingredients": [
        {{"name": "胡萝卜", "amount": "50g"}},
        {{"name": "清水", "amount": "适量"}}
      ],
      "cooking_steps": [
        {{"step": 1, "description": "胡萝卜洗净去皮，切成小块"}},
        {{"step": 2, "description": "将胡萝卜放入蒸锅蒸熟，约15分钟"}}
      ],
      "nutrition_info": {{
        "calories": 25,
        "protein": 0.5,
        "iron": 0.3
      }}
    }},
    ... 更多记录 ...
  ]
}}

注意：
- day_of_week 范围是 {day_start}-{day_end}
- meal_type 只能是：breakfast/lunch/dinner
- 确保JSON格式正确，不要有语法错误
- **菜品必须多样化，每一次生成都要有新菜**
- 不要输出任何额外的说明文字，只输出JSON
"""
        return prompt

    def build_single_meal_prompt(
        self,
        baby,
        nutrition=None,
        meal_type: str = "lunch",
        day: int = 1,
        exclude_dish_names: Optional[List[str]] = None
    ) -> str:
        """
        构建单道菜品生成的prompt

        参数:
            baby: 宝宝信息对象
            nutrition: 营养需求对象
            meal_type: 餐次类型 (breakfast/lunch/dinner)
            day: 天数 (1-7)
            exclude_dish_names: 需要排除的菜品名称列表

        返回:
            构建好的prompt字符串
        """
        meal_type_names = {
            "breakfast": "早餐",
            "lunch": "午餐",
            "dinner": "晚餐"
        }
        meal_name = meal_type_names.get(meal_type, meal_type)

        prompt = f"""你是一位专业的婴幼儿营养师，需要为{baby.age_months}个月的宝宝制定第{day}天的{meal_name}辅食食谱。
"""
        prompt += self._build_baby_info_prompt(baby, nutrition)

        prompt += f"""
## 生成要求
1. **必须生成全新不重复的内容**，发挥创意，不要使用常见的重复搭配
2. 只生成1道菜：第{day}天的{meal_name}（meal_type: {meal_type}）
3. 菜品必须包含：
   - 菜品名称（中文，吸引人且符合宝宝特点）
   - 食材清单（含精确用量，如"胡萝卜 50g"）
   - 详细烹饪步骤（分步骤，适合对应进食能力阶段的宝宝）
   - 营养信息（能量kcal、蛋白质g、铁mg）
4. **严格规避过敏源**
5. **优先使用宝宝喜欢的食材**
6. 确保营养均衡，特别注意铁的补充
7. 食材质地符合对应进食能力阶段（如泥糊状、碎末状、小块状等）
8. 烹饪方法安全、简单，适合家庭制作
9. **菜名命名多样性**：不要使用与已有菜品相同的前缀或修饰词，每道菜的命名风格应各不相同
"""

        if exclude_dish_names and len(exclude_dish_names) > 0:
            exclude_list = "、".join(exclude_dish_names[:30])
            prompt += f"""
## 排除菜品（不要生成以下菜名）
{exclude_list}
"""

        prompt += f"""
## 输出格式
请严格以JSON格式输出，结构如下：
{{
  "detail": {{
    "day_of_week": {day},
    "meal_type": "{meal_type}",
    "dish_name": "菜品名称",
    "ingredients": [
      {{"name": "食材名", "amount": "50g"}},
      ...
    ],
    "cooking_steps": [
      {{"step": 1, "description": "步骤描述"}},
      ...
    ],
    "nutrition_info": {{
      "calories": XXX,
      "protein": XXX,
      "iron": XXX
    }}
  }}
}}

注意：
- day_of_week 必须是 {day}
- meal_type 必须是 {meal_type}
- 确保JSON格式正确，不要有语法错误
- **菜品必须有新意，不要使用常见搭配**
- 不要输出任何额外的说明文字，只输出JSON
"""
        return prompt

    def build_replace_dish_prompt(self, original_dish, baby,
                                exclude_names: Optional[List[str]] = None) -> str:
        """
        构建替换菜品的prompt
        """
        prompt = f"""你是一位专业的婴幼儿营养师，请为现有菜品生成一道**营养相似但食材不同**的替代菜品。
"""
        prompt += self._build_baby_info_prompt(baby)

        prompt += f"""
## 原菜品信息
- 菜品名称：{original_dish.dish_name}
- 餐次：{original_dish.meal_type}
- 原营养信息：{json.dumps(original_dish.nutrition_info, ensure_ascii=False)}
- 原食材：{json.dumps(original_dish.ingredients, ensure_ascii=False)}
"""

        if exclude_names and len(exclude_names) > 0:
            exclude_list = "、".join(exclude_names[:20])
            prompt += f"""
## 排除菜品（不要生成以下菜名）
{exclude_list}
"""

        prompt += f"""
## 要求
1. **必须使用不同的食材**，不能和原菜品重复
2. **保持相同餐次**，营养成分（热量、蛋白质、铁含量）与原菜品相似（波动范围不超过±20%）
3. 严格规避过敏源
4. 食材质地符合宝宝进食能力阶段
5. 请直接输出JSON，不要有其他说明文字
6. 菜品名称要有新意，不能太常见

## 输出格式
{{
  "dish_name": "新菜品名称",
  "ingredients": [
    {{"name": "食材名", "amount": "50g"}},
    ...
  ],
  "cooking_steps": [
    {{"step": 1, "description": "步骤描述"}},
    ...
  ],
  "nutrition_info": {{
    "calories": XXX,
    "protein": XXX,
    "iron": XXX
  }}
}}
"""
        return prompt

    async def generate_single_meal_stream(
        self,
        baby,
        nutrition=None,
        meal_type: str = "lunch",
        day: int = 1,
        exclude_dish_names: Optional[List[str]] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式生成单道菜品

        参数:
            baby: 宝宝信息对象
            nutrition: 营养需求对象
            meal_type: 餐次类型 (breakfast/lunch/dinner)
            day: 天数 (1-7)
            exclude_dish_names: 需要排除的菜品名称列表

        Yields:
            LLM流式输出的原始文本片段
        """
        if not self.is_configured:
            return

        try:
            system_prompt = "你是一位专业的婴幼儿营养师，请严格按照JSON格式输出食谱。"
            user_prompt = self.build_single_meal_prompt(
                baby, nutrition, meal_type, day, exclude_dish_names
            )

            logger.info(
                f"[CodingPlan Single Meal] 开始流式生成第{day}天{meal_type}菜品, "
                f"宝宝{baby.age_months}个月"
            )

            async for chunk in self.stream_generate(system_prompt, user_prompt, self.temperature):
                yield chunk

        except Exception as e:
            logger.error(f"[CodingPlan Single Meal] 流式生成失败: {e}", exc_info=True)
            return

    async def generate_weekly_recipe(self, baby, nutrition=None,
                                  start_day: int = 1, num_days: int = 7,
                                  exclude_dish_names: Optional[List[str]] = None) -> Optional[Dict]:
        """
        非流式生成一周食谱

        Returns:
            成功返回生成的食谱数据，失败返回None（触发降级）
        """
        if not self.is_configured:
            logger.warning("[CodingPlan] API未配置")
            return None

        try:
            system_prompt = "你是一位专业的婴幼儿营养师，请严格按照JSON格式输出食谱。"
            user_prompt = self.build_weekly_prompt(baby, nutrition, start_day, num_days, exclude_dish_names)

            logger.info(f"[CodingPlan] 调用火山引擎API生成 {num_days} 天食谱，宝宝 {baby.age_months} 个月")

            result = await self.generate_json(system_prompt, user_prompt, self.temperature)

            if result and "details" in result:
                logger.info(f"[CodingPlan] 成功生成 {len(result['details'])} 道菜")
                return result
            else:
                logger.error("[CodingPlan] 返回数据缺少details字段")
                return None

        except Exception as e:
            logger.error(f"[CodingPlan] API调用失败: {e}", exc_info=True)
            return None

    async def generate_weekly_recipe_stream(self, baby, nutrition=None,
                                       start_day: int = 1, num_days: int = 7,
                                       exclude_dish_names: Optional[List[str]] = None) -> AsyncGenerator[str, None]:
        """
        流式生成一周食谱

        Yields:
            SSE格式的流式输出：chunk, done, error
        """
        if not self.is_configured:
            yield f"data: {json.dumps({'type': 'error', 'message': 'API不可用'}, ensure_ascii=False)}\n\n"
            return

        try:
            system_prompt = "你是一位专业的婴幼儿营养师，请严格按照JSON格式输出食谱。"
            user_prompt = self.build_weekly_prompt(baby, nutrition, start_day, num_days, exclude_dish_names)

            logger.info(f"[CodingPlan Stream] 开始流式生成 {num_days} 天食谱")

            full_content = ""

            async for chunk in self.stream_generate(system_prompt, user_prompt, self.temperature):
                full_content += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'full_content': full_content}, ensure_ascii=False)}\n\n"

            # 完成后解析完整JSON
            cleaned = self._clean_json_output(full_content)
            try:
                parsed = json.loads(cleaned)
                if "details" in parsed:
                    logger.info(f"[CodingPlan Stream] 成功生成 {len(parsed['details'])} 道菜")
                    yield f"data: {json.dumps({'type': 'done', 'data': parsed}, ensure_ascii=False)}\n\n"
                else:
                    logger.error("[CodingPlan Stream] 返回数据缺少details字段")
                    yield f"data: {json.dumps({'type': 'error', 'message': '生成结果格式错误'}, ensure_ascii=False)}\n\n"
            except json.JSONDecodeError as e:
                logger.error(f"[CodingPlan Stream] JSON解析失败: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': '生成结果解析失败'}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"[CodingPlan Stream] 流式生成失败: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': '生成失败'}, ensure_ascii=False)}\n\n"

    async def generate_replace_dish_stream(self, original_dish, baby,
                                       exclude_names: Optional[List[str]] = None) -> AsyncGenerator[str, None]:
        """
        流式生成替换菜品

        Yields:
            SSE格式的流式输出：chunk, done, error
        """
        if not self.is_configured:
            yield f"data: {json.dumps({'type': 'error', 'message': 'API不可用'}, ensure_ascii=False)}\n\n"
            return

        try:
            system_prompt = "你是一位专业的婴幼儿营养师，请严格按照JSON格式输出替换菜品。"
            user_prompt = self.build_replace_dish_prompt(original_dish, baby, exclude_names)

            logger.info(f"[CodingPlan Replace] 开始流式生成替换菜品: {original_dish.dish_name}")

            full_content = ""

            async for chunk in self.stream_generate(system_prompt, user_prompt, self.temperature):
                full_content += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'full_content': full_content}, ensure_ascii=False)}\n\n"

            # 完成后解析完整JSON
            cleaned = self._clean_json_output(full_content)
            try:
                parsed = json.loads(cleaned)
                if "dish_name" in parsed:
                    logger.info(f"[CodingPlan Replace] 成功生成替换菜品: {parsed['dish_name']}")
                    yield f"data: {json.dumps({'type': 'done', 'data': parsed}, ensure_ascii=False)}\n\n"
                else:
                    logger.error("[CodingPlan Replace] 返回数据缺少dish_name字段")
                    yield f"data: {json.dumps({'type': 'error', 'message': '生成结果格式错误'}, ensure_ascii=False)}\n\n"
            except json.JSONDecodeError as e:
                logger.error(f"[CodingPlan Replace] JSON解析失败: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': '生成结果解析失败'}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"[CodingPlan Replace] 流式生成失败: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': '生成失败'}, ensure_ascii=False)}\n\n"

    def clean_json_output(self, content: str) -> str:
        """
        清理LLM输出的JSON，处理常见格式问题（公共接口）：
        - 移除markdown代码块包裹 ```json ... ```
        - 移除多余的说明文字
        - 处理换行和空格
        """
        return self._clean_json_output(content)

    def _clean_json_output(self, content: str) -> str:
        """
        清理LLM输出的JSON，处理常见格式问题（内部实现）：
        - 移除markdown代码块包裹 ```json ... ```
        - 移除多余的说明文字
        - 处理换行和空格
        """
        # 移除markdown代码块
        content = re.sub(r'```(?:json)?\s*', '', content)
        content = re.sub(r'\s*```\s*$', '', content)

        # 查找第一个 { 和最后一个 }，提取JSON部分
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1 and end > start:
            content = content[start:end+1]

        return content


# 创建全局单例 - 每次访问重新初始化以获取最新环境变量
def get_volcengine_client():
    return VolcengineClient()

volcengine_client = get_volcengine_client()
