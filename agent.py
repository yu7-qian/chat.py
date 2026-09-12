import requests
import json
from config import API_KEY

URL = "https://api.deepseek.com/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# ① 真正执行的函数（这里用假数据，真实项目里调天气API）
def get_weather(city):
    weather_db = {
        "北京": "晴，26℃，微风",
        "上海": "小雨，23℃，记得带伞",
        "广州": "多云，31℃，较热"
    }
    return weather_db.get(city, f"暂无 {city} 的天气数据")

# ② 告诉模型：你有哪些工具可用（用 JSON 描述函数名、作用、参数）
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的实时天气情况",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称，例如：北京、上海"}
                },
                "required": ["city"]
            }
        }
    }
]

messages = [
    {"role": "system", "content": "你是一个助手，可以调用工具查询天气。"}
]

print("智能体启动！输入 exit 退出\n")

while True:
    user_input = input("我：")
    if user_input.strip() in ("exit", "quit", "退出"):
        print("再见！")
        break

    messages.append({"role": "user", "content": user_input})
    data = {"model": "deepseek-chat", "messages": messages, "tools": tools}

    try:
        # 第 1 次请求：模型决定要不要调用工具
        resp = requests.post(URL, headers=headers, json=data, timeout=30)
        msg = resp.json()["choices"][0]["message"]
        messages.append(msg)   # 模型的回复（可能带 tool_calls）也要进历史

        if msg.get("tool_calls"):
            # 模型要求调用函数 → 代码执行
            for call in msg["tool_calls"]:
                fn_name = call["function"]["name"]
                args = json.loads(call["function"]["arguments"])
                print(f"  [工具调用] {fn_name}({args})")

                result = get_weather(args["city"])

                # 把执行结果以 role=tool 发回给模型
                messages.append({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": result
                })

            # 第 2 次请求：模型拿到工具结果，组织自然语言回答
            resp2 = requests.post(URL, headers=headers,
                                  json={"model": "deepseek-chat",
                                        "messages": messages, "tools": tools},
                                  timeout=30)
            answer = resp2.json()["choices"][0]["message"]["content"]
            print("AI：", answer, "\n")
            messages.append({"role": "assistant", "content": answer})
        else:
            # 不需要工具（比如闲聊），直接回答
            print("AI：", msg["content"], "\n")

    except requests.exceptions.RequestException as e:
        print("网络出错了：", e)
        messages.pop()