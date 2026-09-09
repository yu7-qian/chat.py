import requests

from config import API_KEY
URL = "https://api.deepseek.com/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# messages 就是"聊天记录"，全程维护这一个列表
messages = [
    {"role": "system", "content": "你是一个友好的中文助手"}
]

print("聊天机器人启动！输入 exit 退出\n")

while True:
    user_input = input("我：")
    if user_input.strip() in ("exit", "quit", "退出"):
        print("再见！")
        break

    messages.append({"role": "user", "content": user_input})
    data = {"model": "deepseek-chat", "messages": messages}

    try:
        resp = requests.post(URL, headers=headers, json=data, timeout=30)

        if resp.status_code != 200:
            print("调用失败：", resp.json()["error"]["message"])
            messages.pop()   # 把刚才那条用户消息撤掉，避免污染对话记录
            continue

        answer = resp.json()["choices"][0]["message"]["content"]
        print("AI：", answer, "\n")
        messages.append({"role": "assistant", "content": answer})

    except requests.exceptions.RequestException as e:
        print("网络出错了，检查下网络再试：", e)
        messages.pop()