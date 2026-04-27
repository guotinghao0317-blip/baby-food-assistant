"""
后端API测试脚本
测试食谱生成相关API的功能
"""
import requests
import json
import time

API_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test123456"

def print_test(name, passed, message=""):
    """打印测试结果"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if message:
        print(f"     {message}")

def test_1_health_check():
    """测试1：健康检查"""
    try:
        response = requests.get(f"{API_URL}/health")
        data = response.json()
        passed = response.status_code == 200 and data.get("status") == "healthy"
        print_test("健康检查", passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        print_test("健康检查", False, f"Error: {e}")
        return False

def test_2_login():
    """测试2：用户登录"""
    try:
        # 使用OAuth2PasswordRequestForm格式（表单数据）
        response = requests.post(
            f"{API_URL}/api/auth/login",
            data={
                "username": TEST_EMAIL,  # OAuth2PasswordRequestForm使用username字段
                "password": TEST_PASSWORD
            }
        )
        data = response.json()
        passed = response.status_code == 200 and "access_token" in data
        if passed:
            return data["access_token"]
        print_test("用户登录", passed, f"Status: {response.status_code}, Detail: {data.get('detail')}")
        return None
    except Exception as e:
        print_test("用户登录", False, f"Error: {e}")
        return None

def test_3_get_babies(token):
    """测试3：获取宝宝列表"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/api/babies", headers=headers)
        data = response.json()
        passed = response.status_code == 200
        print_test("获取宝宝列表", passed, f"Status: {response.status_code}, Babies: {len(data) if passed else 0}")
        if passed and len(data) > 0:
            return data[0]["id"]
        return None
    except Exception as e:
        print_test("获取宝宝列表", False, f"Error: {e}")
        return None

def test_4_generate_recipe_step_by_step(token, baby_id):
    """测试4：分步生成食谱"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{API_URL}/api/recipes/generate-step-by-step",
            json={"baby_id": baby_id},
            headers=headers
        )

        if response.status_code != 200:
            print_test("分步生成食谱", False, f"Status: {response.status_code}")
            return None

        # 这是一个流式响应，需要读取SSE事件
        recipe_id = None
        generated_days = []

        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if data.get('type') == 'started':
                            recipe_id = data.get('recipe_id')
                        elif data.get('type') == 'day_done':
                            generated_days.append(data.get('day'))
                        elif data.get('type') == 'finished':
                            break
                    except:
                        pass

        passed = recipe_id is not None and len(generated_days) == 7
        print_test("分步生成食谱", passed, f"Recipe ID: {recipe_id}, Generated days: {len(generated_days)}")
        return recipe_id
    except Exception as e:
        print_test("分步生成食谱", False, f"Error: {e}")
        return None

def test_5_get_recipe_details(token, recipe_id):
    """测试5：获取食谱详情（关键测试 - 验证问题1修复）"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/api/recipes/{recipe_id}", headers=headers)
        data = response.json()

        # 检查是否返回了details数组
        has_details = "details" in data and data["details"] is not None
        details_count = len(data.get("details", [])) if has_details else 0

        # 检查每个detail是否包含必需字段
        all_details_valid = True
        missing_fields = []
        for detail in data.get("details", []):
            required_fields = ["day_of_week", "meal_type", "dish_name"]
            for field in required_fields:
                if field not in detail or detail[field] is None:
                    all_details_valid = False
                    missing_fields.append(f"Detail {detail.get('id', 'unknown')} missing {field}")

        # 检查是否有7天的数据（每题4道菜，共28道）
        expected_dishes = 28
        has_expected_count = details_count >= expected_dishes

        passed = has_details and all_details_valid and has_expected_count
        message = f"Details count: {details_count}, All valid: {all_details_valid}"
        if missing_fields:
            message += f", Missing: {len(missing_fields)}"

        print_test("获取食谱详情（问题1验证）", passed, message)

        # 打印详细数据用于调试
        if has_details:
            print(f"     详情:")
            print(f"       - 总菜品数: {details_count}")
            print(f"       - 前3道菜: {[d.get('dish_name') for d in data['details'][:3]]}")

        return passed
    except Exception as e:
        print_test("获取食谱详情（问题1验证）", False, f"Error: {e}")
        return False

def test_6_replace_dish(token, recipe_id):
    """测试6：换一道菜功能"""
    try:
        headers = {"Authorization": f"Bearer {token}"}

        # 先获取第一个菜品
        recipe_response = requests.get(f"{API_URL}/api/recipes/{recipe_id}", headers=headers)
        recipe_data = recipe_response.json()

        if not recipe_data.get("details"):
            print_test("换一道菜功能", False, "No dishes found")
            return False

        first_dish = recipe_data["details"][0]

        # 替换菜品
        replace_response = requests.post(
            f"{API_URL}/api/recipes/{recipe_id}/replace-dish",
            json={
                "day_of_week": first_dish["day_of_week"],
                "meal_type": first_dish["meal_type"],
                "original_dish_id": first_dish["id"]
            },
            headers=headers
        )

        passed = replace_response.status_code == 200
        print_test("换一道菜功能", passed, f"Status: {replace_response.status_code}")
        return passed
    except Exception as e:
        print_test("换一道菜功能", False, f"Error: {e}")
        return False

def test_7_recipe_status(token, recipe_id):
    """测试7：查询食谱生成状态"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/api/recipes/recipe-status/{recipe_id}", headers=headers)
        data = response.json()

        passed = response.status_code == 200 and "status" in data and "generated_days" in data
        print_test("查询食谱生成状态", passed, f"Status: {data.get('status')}, Generated days: {data.get('generated_days')}")
        return passed
    except Exception as e:
        print_test("查询食谱生成状态", False, f"Error: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("后端API测试 - 验证食谱生成问题修复")
    print("=" * 60)
    print()

    # 测试1：健康检查
    if not test_1_health_check():
        print("\n❌ 后端服务未运行，停止测试")
        return

    # 测试2：登录
    token = test_2_login()
    if not token:
        print("\n❌ 登录失败，停止测试")
        return

    # 测试3：获取宝宝列表
    baby_id = test_3_get_babies(token)
    if not baby_id:
        print("\n❌ 没有找到宝宝，请先创建宝宝")
        print("   提示：可以通过前端界面创建测试宝宝")
        return

    # 测试4：分步生成食谱
    recipe_id = test_4_generate_recipe_step_by_step(token, baby_id)
    if not recipe_id:
        print("\n❌ 食谱生成失败")
        return

    # 等待一下确保数据已保存
    time.sleep(2)

    # 测试5：获取食谱详情（关键测试）
    test_5_passed = test_5_get_recipe_details(token, recipe_id)

    # 测试6：换一道菜功能
    test_6_passed = test_6_replace_dish(token, recipe_id)

    # 测试7：查询食谱生成状态
    test_7_passed = test_7_recipe_status(token, recipe_id)

    print()
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"问题1验证（食谱详情非空）: {'✅ 通过' if test_5_passed else '❌ 失败'}")
    print(f"换一道菜功能: {'✅ 通过' if test_6_passed else '❌ 失败'}")
    print(f"状态查询功能: {'✅ 通过' if test_7_passed else '❌ 失败'}")
    print()

if __name__ == "__main__":
    main()
