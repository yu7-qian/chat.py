import requests
import json
from config import API_KEY

URL = "https://api.deepseek.com/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# ① 查询真实天气：先把城市名换成经纬度，再查天气（Open-Meteo 免费接口，无需 key）
def get_weather(city):
    # 第 1 步：城市名 → 经纬度（地理编码）
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_resp = requests.get(
        geo_url,
        params={"name": city, "count": 1, "language": "zh", "format": "json"},
        timeout=10
    )
    results = geo_resp.json().get("results")
    if not results:
        return f"没找到叫「{city}」的城市"

    loc = results[0]
    lat, lon = loc["latitude"], loc["longitude"]

    # 第 2 步：经纬度 → 实时天气
    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_resp = requests.get(
        weather_url,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weather_code,wind_speed_10m"
        },
        timeout=10
    )
    current = weather_resp.json()["current"]

    # Open-Meteo 用数字代码表示天气，翻译成中文
    code_map = {
        0: "晴", 1: "大致晴朗", 2: "多云", 3: "阴天",
        45: "雾", 48: "雾凇",
        51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨",
        61: "小雨", 63: "中雨", 65: "大雨",
        71: "小雪", 73: "中雪", 75: "大雪",
        80: "小阵雨", 81: "阵雨", 82: "强阵雨",
        95: "雷阵雨", 96: "雷阵雨伴冰雹", 99: "强雷阵雨伴冰雹"
    }
    desc = code_map.get(current["weather_code"], "未知天气")

    return (f"{loc['name']}当前{desc}，"
            f"气温 {current['temperature_2m']}℃，"
            f"风速 {current['wind_speed_10m']} km/h")
            

# ② 告诉模型：你有哪些工具可用（用 JSON 描述函数名、作用、参数）
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的实时天气情况，支持国内外城市，数据来自真实天气接口",
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