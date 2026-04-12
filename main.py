# main.py
"""
AgentLearning 入口文件
"""
from config import get_llm, ACTIVE_LLM


def main():
    llm = get_llm()
    print(f"当前 LLM 厂商: {ACTIVE_LLM}")
    print(f"LLM 实例: {llm}")

    # 验证连通性
    response = llm.invoke("你好，返回'连接成功'即可")
    print(f"LLM 响应: {response.content}")


if __name__ == "__main__":
    main()
