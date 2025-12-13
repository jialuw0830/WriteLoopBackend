
# 📝 **WriteLoop Backend — README**

WriteLoop Backend 是一个基于 **FastAPI + WebSocket** 的后端服务，用于为前端编辑器提供即时英文写作补全能力。

前端仓库地址（用于配套运行）：
 [https://github.com/Notyourbing/WriteLoop](https://github.com/Notyourbing/WriteLoop)

---

# 📦 运行环境要求（Environment Requirements）

请确保本机安装以下环境：

###  Python

* **Python 3.10+**
  （推荐使用 Conda 环境）

###  Conda（推荐）

```bash
conda --version
```

###  后端依赖

* FastAPI
* Uvicorn（支持 WebSocket）
* websockets
* pydantic


#  运行步骤（Running the Backend）

## **1. 克隆项目**

```bash
git clone https://github.com/Notyourbing/WriteLoopBackend.git
cd WriteLoopBackend
```

---

## **2. 创建 Conda 虚拟环境**

```bash
conda create -n writeloopbackend python=3.10
conda activate writeloopbackend
```

---

## **3. 安装依赖**

```bash
pip install -r requirements.txt
```


## **4. 启动后端服务**

进入项目根目录：

```bash
uvicorn app.main:app --reload --port 8001
```

启动成功后，你会看到：

```
Uvicorn running on http://127.0.0.1:8001
WebSocket server ready at ws://localhost:8001/ws/suggest
```

---

# 🔌 WebSocket API（WriteLoop 补全接口）

前端会与后端建立 WebSocket 连接：

```
ws://localhost:8001/ws/suggest
```

### 前端发送的数据（JSON 格式）：

```json
{
  "text": "current text in editor",
  "cursor": { "lineNumber": 1, "column": 4 }
}
```

### 后端返回：

```json
[
  { "text": "moreover,", "explain": "Used to add supporting argument" },
  { "text": "in contrast,", "explain": "Used to introduce contrast" },
  { "text": "as a consequence,", "explain": "Used to show result or effect" }
]
```

这些建议会被前端写入补全列表。

---

# 📁 项目结构（Project Structure）

```
WriteLoopBackend/
├── app/
│   ├── main.py            # FastAPI 主入口（WebSocket 逻辑）
│   ├── core/              # 后续可扩展：NLP、RAG、Embedding、模型等
│   └── ...
├── requirements.txt
└── README.md
```

---

# 🧠 开发说明

* 后端目前使用简单的静态补全，用于 Sprint 1
* Sprint 2 可扩展：

  * DeepSeek / OpenAI API 接入
  * 句式重构（UR-2）
  * 逻辑连贯性分析（UR-4）
  * 结构树抽取（UR-3）
  * RAG 检索（用户阅读记录 → 写作辅助）


