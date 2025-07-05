# Text2SQL
该项目使用 LangGraph 与高德地图以及 12306 票务数据的 MCP 构建多代理系统，基于用户的出发地与目的地，实现智能路线规划。

该代理由三个过程组成：
1. supervisor 代理根据用户查询的目的地、出发地以及期望的出行方式，将整体任务分解为多个子任务。
2. navigation_expert 和 ticketing_expert 代理分别执行由 supervisor 分配的路径规划与票务查询任务。
3. 所有查询任务完成后，将所有中间状态信息交由 LLM 处理，并生成最终的自然语言回复结果返回给用户。

## 文件夹结构

```plaintext
📦 Travel_Planning
├── 📁 config                                           # Travel_Planning 代码
│   ├── 📄 __init__.py                                  # 将目录设为 Python 包
│   ├── 📄 agent_workflow.py                            # TravelAgent 代理类
│   ├── 📄 agents_config.py                             # 代理配置函数
│   └── 📄 prompts.py                                   # 系统提示词
│
├── 📁 example                                          # 使用代理示例
├── ⚙️ .env                                             # .env 文件模板
├── 📄 README.md                                        # 项目主文档
├── 📄 requirements.txt                                 # 依赖项列表
├── ⚙️ servers_config.json                              # 高德地图和12306票务数据的MCP配置文件
├── 📄 streamlit_front.py                               # 前端脚本
配置
```

## 依赖项

1. **创建并激活虚拟环境**

    使用conda创建一个虚拟环境：

    ```bash
    conda create --name travel_planning python=3.12 -y
    ```

    激活虚拟环境：
     
     ```bash
    conda activate travel_planning
    ```

2. **使用 pip 同步依赖项**：

    ```bash
    pip install -r requirements.txt
    ```
    
    此命令将在虚拟环境中安装 requirements.txt 文件中定义的依赖项。

## 环境变量

该项目需要OpenAI的API Key以及高德地图开放平台的API Key. 这些应写在.env文件中。

`AMAP_MAPS_API_KEY= = '4a1..................'`

`OPENAI_API_KEY = 'sk-WrrN..................'`


## 使用流程

2. 通过以下命令启动 streamlit_front 前端：
    ```bash
    streamlit run streamlit_front.py --server.port 8003
    ```
