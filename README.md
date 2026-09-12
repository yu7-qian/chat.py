# 命令行 AI 聊天机器人

不依赖任何第三方 SDK，基于 Python requests 手写 HTTP 请求调用 DeepSeek 大模型 API，实现的命令行多轮对话机器人。

## 功能

- 多轮上下文对话：维护 messages 历史列表，每轮全量发送，模型具备连续对话记忆
- 异常处理：HTTP 状态码校验（401/402 等错误友好提示）、网络超时与断网兜底，失败轮次不污染对话历史
- 密钥安全管理：API Key 存放于本地 config.py 并通过 .gitignore 排除，不上传仓库
- 流式输出：基于SSE逐块接收响应，实现打字机式实时输出
- 函数调用（Function Calling）：模型自主判断是否调用外部工具，代码执行后将结果回传，实现"LLM 决策 + 工具执行"的最小智能体

## 技术栈

- Python 3
- requests（HTTP 请求）
- DeepSeek API（OpenAI 兼容接口，chat/completions）

  ## 项目结构

- chat.py：主程序，对话循环、API 调用、流式输出与异常处理
- agent.py：函数调用版智能体，演示模型决策调用 get_weather 工具的完整两轮请求链路
- config.py：本地配置，存放 API_KEY（已被 .gitignore 忽略，不上传）
- .gitignore：忽略 config.py 与 __pycache__

## 快速开始

1. 克隆仓库后，在项目目录新建 config.py，写入：API_KEY = "你的 DeepSeek API Key"
2. 安装依赖：pip install requests
3. 运行：python chat.py
4. 输入内容开始对话，输入 exit 退出

## 核心原理

大模型本身是无状态的——它不会记住上一句说了什么。多轮对话的本质是：客户端维护一个 messages 列表，每轮把 system / user / assistant 三种角色的完整历史一起发给 API，模型根据全部上下文生成回答，再把回答追加回列表。这与 Coze、Dify 等智能体平台的会话记忆是同一原理。
