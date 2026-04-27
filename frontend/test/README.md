# 移动端适配测试说明

## 目录结构

```
test/
├── docs/
│   ├── test-plan-mobile-responsive.md    # 测试计划文档
│   └── smoke-check-moblie.md            # 线上冒烟检查清单
├── mobile-responsive.test.js            # 首页+登录注册响应式测试
└── onboarding-mobile.test.js            # 信息收集页移动端测试
```

## 开发环境测试运行

### 1. 安装测试依赖

```bash
cd frontend
npm install --save-dev jest @testing-library/react @testing-library/jest-dom jsdom babel-jest
```

### 2. 配置说明
已添加以下配置文件：
- `jest.config.js` - Jest配置
- `jest.setup.js` - Jest全局设置

在 `package.json` 中添加测试脚本：

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch"
  }
}
```

### 3. 运行测试

```bash
# 运行所有测试
npm test

# 监听模式开发
npm run test:watch

# 只运行移动端相关测试
npm test -- test/mobile*.js
```

## 测试覆盖场景

### 单元/集成测试覆盖
| 场景 | 覆盖内容 |
|------|----------|
| 不同屏幕尺寸 | 320px ~ 1920px 全范围 |
| 断点适配 | md: 断点正确应用 |
| 点击区域 | 按钮 ≥ 44px × 44px |
| 容器边距 | px-4 保证左右留白 |
| 网格布局 | 移动端单列/多列合理布局 |
| 边界情况 | 超小屏、超大屏都适配 |
| 表单元素 | 输入框全宽，可点击 |

### 线上冒烟测试覆盖
- 所有页面逐屏检查
- iPhone/Android 多设备
- 平板横竖屏切换
- 完整用户流程回归
- 桌面端回归检查

## 测试断言说明

自动化测试主要验证：
1. **DOM结构正确** - 正确的元素、正确的类名
2. **响应式规范遵循** - Tailwind移动优先设计原则正确使用
3. **最小尺寸满足** - 点击区域、字体大小满足移动端要求
4. **无水平溢出** - 文档宽度不超过视口宽度

视觉像素级验证需要人工检查，因为JSDOM不做实际布局计算。

## 线上测试方法

1. 打开 `test/docs/smoke-check-moblie.md` 检查清单
2. 在真机浏览器逐一打开测试页面
3. 按照检查清单逐项验证
4. 记录结果，发现问题截图反馈
