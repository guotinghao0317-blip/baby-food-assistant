/**
 * 信息收集页面移动端适配测试
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import Onboarding from '../app/onboarding/page';

// Mock localStorage
Storage.prototype.getItem = jest.fn(() => 'fake-token');
Storage.prototype.setItem = jest.fn();

describe('信息收集页面移动端适配', () => {
  beforeEach(() => {
    window.innerWidth = 375; // iPhone
  });

  test('容器应该正确限制最大宽度且居中', () => {
    render(<Onboarding />);

    const container = document.querySelector('.max-w-2xl');
    expect(container).toBeInTheDocument();
    expect(container).toHaveClass('mx-auto');
  });

  test('表单应该占满移动端宽度', () => {
    render(<Onboarding />);

    // 所有输入框都应该是w-full
    const inputs = document.querySelectorAll('input, select');
    inputs.forEach(input => {
      // 检查父元素结构，输入框应该全宽
      expect(input).toHaveClass('w-full');
    });
  });

  test('基础信息区网格应该在移动端响应式布局', () => {
    render(<Onboarding />);

    // 体重/身高 在移动端是 grid grid-cols-2 gap-4
    // 这在移动端两列是合适的
    const grid = document.querySelector('.grid.grid-cols-2');
    expect(grid).toBeInTheDocument();

    // 375px宽度下两列依然合理
    const computedStyle = window.getComputedStyle(grid);
    expect(computedStyle.gridTemplateColumns).toBeDefined();
  });

  test('过敏源选择网格应该是两列布局（移动端合适）', () => {
    render(<Onboarding />);

    const allergyGrid = document.querySelector('.grid.grid-cols-2');
    expect(allergyGrid).toBeInTheDocument();
    // 移动端两列布局合适
    expect(allergyGrid.classList.contains('gap-2')).toBe(true);
  });

  test('喜好食材选择网格应该是三列布局', () => {
    render(<Onboarding />);

    const ingredientGrid = document.querySelector('.grid.grid-cols-3');
    expect(ingredientGrid).toBeInTheDocument();
    // 375px下三列依然可行，因为选项很小
    expect(ingredientGrid.classList.contains('gap-2')).toBe(true);
  });

  test('导航按钮应该布局合理，尺寸足够', () => {
    render(<Onboarding />);

    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      if (!button.disabled) {
        const rect = button.getBoundingClientRect();
        // 最小高度满足点击需求
        expect(rect.height).toBeGreaterThanOrEqual(40);
      }
    });

    // 按钮左右分布，在移动端合理
    const buttonContainer = document.querySelector('.flex.justify-between');
    expect(buttonContainer).toBeInTheDocument();
  });

  test('进度条应该全宽度显示', () => {
    render(<Onboarding />);

    const progressBar = document.querySelector('.w-full.bg-gray-200.rounded-full');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveClass('w-full');
  });

  test('单选选项点击区域足够大', () => {
    render(<Onboarding />);

    const labels = document.querySelectorAll('label.flex.items-center.p-3');
    labels.forEach(label => {
      // padding p-3 提供足够点击区域
      expect(label).toHaveClass('p-3');
    });
  });

  describe('不同屏幕尺寸测试', () => {
    test.each([
      [320, '超小屏'],
      [360, '安卓小屏'],
      [375, 'iPhone'],
      [414, 'iPhone Plus'],
      [768, 'iPad竖屏'],
      [1024, 'iPad横屏'],
    ])('在%spx - %s应该正常显示', (width, description) => {
      window.innerWidth = width;
      render(<Onboarding />);

      // 标题应该可见
      expect(screen.getByText(/宝宝信息收集/)).toBeInTheDocument();

      // 不应该有水平滚动
      expect(document.documentElement.scrollWidth).toBeLessThanOrEqual(width + 1);
    });
  });
});
