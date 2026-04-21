"""
Phase 1 功能测试脚本
测试多租户隔离、API 基本功能
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_phase1():
    """测试 Phase 1 核心功能"""
    print("=" * 50)
    print("Phase 1 功能测试")
    print("=" * 50)

    # 1. 测试健康检查
    print("\n1. 测试健康检查...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")

    # 2. 注册教师用户
    print("\n2. 注册教师用户...")
    teacher_data = {
        "username": "teacher1",
        "password": "password123",
        "role": "TEACHER"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=teacher_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        teacher = response.json()
        teacher_id = teacher["id"]
        print(f"   Teacher ID: {teacher_id}")

        # 教师登录
        print("\n3. 教师登录...")
        login_data = {
            "username": "teacher1",
            "password": "password123"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            token_data = response.json()
            teacher_token = token_data["access_token"]
            print(f"   Token: {teacher_token[:50]}...")

            # 创建教师分身
            print("\n4. 创建教师分身...")
            headers = {
                "Authorization": f"Bearer {teacher_token}",
                "X-Tenant-Id": str(teacher_id),
                "X-Role": "TEACHER"
            }
            profile_data = {
                "avatar_prompt": "一位和蔼的计算机科学教授",
                "name": "张老师",
                "personality": "严谨但幽默,善于用生动的例子解释复杂概念",
                "catchphrase": "同学们,这个知识点很重要哦!"
            }
            response = requests.post(
                f"{BASE_URL}/api/teachers/profile",
                json=profile_data,
                headers=headers
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Profile: {response.json()}")

            # 创建班级
            print("\n5. 创建班级...")
            class_data = {
                "class_name": "计算机科学101班"
            }
            response = requests.post(
                f"{BASE_URL}/api/teachers/classes",
                json=class_data,
                headers=headers
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                class_info = response.json()
                invite_code = class_info["invite_code"]
                print(f"   Invite Code: {invite_code}")

                # 注册学生用户
                print("\n6. 注册学生用户...")
                student_data = {
                    "username": "student1",
                    "password": "password123",
                    "role": "STUDENT"
                }
                response = requests.post(f"{BASE_URL}/api/auth/register", json=student_data)
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    student = response.json()
                    student_id = student["id"]
                    print(f"   Student ID: {student_id}")

                    # 学生登录
                    print("\n7. 学生登录...")
                    login_data = {
                        "username": "student1",
                        "password": "password123"
                    }
                    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
                    if response.status_code == 200:
                        token_data = response.json()
                        student_token = token_data["access_token"]
                        print(f"   Token: {student_token[:50]}...")

                        # 学生加入班级
                        print("\n8. 学生加入班级...")
                        headers = {
                            "Authorization": f"Bearer {student_token}",
                            "X-Tenant-Id": str(teacher_id),
                            "X-Role": "STUDENT"
                        }
                        join_data = {
                            "invite_code": invite_code
                        }
                        response = requests.post(
                            f"{BASE_URL}/api/students/join",
                            json=join_data,
                            headers=headers
                        )
                        print(f"   Status: {response.status_code}")
                        if response.status_code == 200:
                            print(f"   Joined: {response.json()}")

                        # 测试对话 (注意:需要先上传文档才能正常使用)
                        print("\n9. 测试对话接口...")
                        chat_data = {
                            "message": "什么是机器学习?",
                            "stream": False
                        }
                        response = requests.post(
                            f"{BASE_URL}/api/chat/",
                            json=chat_data,
                            headers=headers
                        )
                        print(f"   Status: {response.status_code}")
                        if response.status_code == 200:
                            result = response.json()
                            print(f"   Answer: {result['answer'][:100]}...")
                            print(f"   Trace-Id: {result['trace_id']}")

    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    try:
        test_phase1()
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器,请确保 FastAPI 服务正在运行")
        print("   启动命令: bash start.sh")
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
