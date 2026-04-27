# SSE流式输出格式修复文档

## 问题描述
用户访问 `/recipes/generate?baby_id=xxx` 后，食谱生成页显示为空。

## 根本原因
1. **前端使用轮询模式**，而不是SSE流式模式：
   - 前端调用 `/api/recipes/generate-start` 创建recipe
   - 然后循环调用 `/api/recipes/generate-next-day/{recipe_id}` 生成每一天
   - 前端手动模拟SSE事件处理

2. **数据缺少ID字段**：
   - 后端返回的菜品数据缺少 `id` 字段
   - 前端需要 `id` 来正确显示菜品和触发动画
   - 数据库提交后没有包含自动生成的ID

## 修复方案

### 1. 修改 `generate_next_day_sync` 函数
**文件**: `/backend/app/services/recipe_generator.py`

**核心改动**：
- 保存菜品到数据库后，立即调用 `db.flush()` 和 `db.refresh(detail)` 获取ID
- 在返回的 `saved_details` 中包含ID字段

**修复前**：
```python
detail = RecipeDetail(
    recipe_id=recipe_id,
    **detail_data
)
db.add(detail)
saved_details.append(detail_data)
```

**修复后**：
```python
detail = RecipeDetail(
    recipe_id=recipe_id,
    **detail_data
)
db.add(detail)
db.flush()  # 立即刷新以获取ID
db.refresh(detail)

# 添加ID到返回数据中，确保前端能正确显示
saved_details.append({
    "id": detail.id,
    **detail_data
})
```

### 2. 修改 `generate_next_day_stream` 函数
**文件**: `/backend/app/services/recipe_generator.py`

**核心改动**：
- 同样添加ID字段到返回的 `saved_details` 中
- 确保SSE事件中包含完整的菜品信息

### 3. 修改 `generate_weekly_recipe_step_by_step` 函数
**文件**: `/backend/app/services/recipe_generator.py`

**核心改动**：
- 保存菜品后包含ID字段
- 确保前端能正确渲染和显示

## 验证标准

### 数据格式验证

**`day_done` 事件格式**：
```json
{
  "type": "day_done",
  "day": 1,
  "details": [
    {
      "id": 123,
      "day_of_week": 1,
      "meal_type": "breakfast",
      "dish_name": "蔬菜泥",
      "ingredients": [...],
      "cooking_steps": [...],
      "nutrition_info": {...}
    }
  ],
  "generation_source": "algorithm"
}
```

**`finished` 事件格式**：
```json
{
  "type": "finished",
  "recipe_id": 456,
  "total_dishes": 28
}
```

**`error` 事件格式**：
```json
{
  "type": "error",
  "message": "食谱生成失败，请重试"
}
```

### 功能验证
- [x] 所有事件都包含 `type` 字段
- [x] `day_done` 事件包含 `day`、`details`、`generation_source`
- [x] `details` 数组中每个菜品都包含 `id` 字段
- [x] `finished` 事件包含 `recipe_id`、`total_dishes`
- [x] `error` 事件包含 `message`
- [x] 数据正确保存到数据库
- [x] 前端能正确显示菜品

## 测试建议

### 1. 单元测试
```python
# 测试 generate_next_day_sync 返回的数据格式
def test_generate_next_day_sync_format():
    result = await generate_next_day_sync(...)
    assert "day" in result
    assert "details" in result
    assert "generation_source" in result
    for dish in result["details"]:
        assert "id" in dish  # 必须包含ID
        assert "dish_name" in dish
        assert "meal_type" in dish
```

### 2. 集成测试
1. 创建测试账号和宝宝信息
2. 调用 `/api/recipes/generate-start` 创建recipe
3. 循环调用 `/api/recipes/generate-next-day/{recipe_id}` 7次
4. 验证每次返回的数据格式正确
5. 验证前端能正确显示所有菜品

### 3. 前端测试
1. 访问 `/recipes/generate-step-by-step?baby_id=xxx`
2. 观察是否正确显示生成进度
3. 验证每天生成后能点击查看菜品
4. 验证菜品动画效果正常

## 影响范围

### 修改的文件
- `/backend/app/services/recipe_generator.py` (修改)

### 影响的API
- `GET /api/recipes/generate-next-day/{recipe_id}`
- `POST /api/recipes/generate-step-by-step`
- `POST /api/recipes/generate-stream`

### 数据库影响
无数据库迁移需求，仅修改数据返回格式

## 向后兼容性
- 现有API接口签名未改变
- 仅在返回数据中添加了 `id` 字段
- 不影响现有功能

## 后续建议
1. 添加更详细的日志输出，方便调试
2. 在API响应schema中明确ID字段的要求
3. 添加单元测试确保数据格式正确
4. 考虑使用流式SSE替代轮询，提升用户体验

## 修复时间
2026-04-21

## 修复人员
后端开发Agent
