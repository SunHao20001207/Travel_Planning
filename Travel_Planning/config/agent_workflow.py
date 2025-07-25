# agent_workflow.py

from langgraph.graph import END, StateGraph, START
import functools
from langchain.schema import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import AsyncGenerator
import os
from dotenv import load_dotenv

from .agents_config import (
    AgentState, agent_node, supervisor_router,
    list_and_return_tools, load_single_mcp_config,
    parse_messages
)
from .prompts import (
    navigation_prompt, ticketing_prompt,
    supervisor_prompt, system_prompt_template,
    question_prompt_template
)

load_dotenv(override=True)
model = os.getenv("MODEL")
chat_model = os.getenv("CHAT_MODEL")


class TravelAgent:
    def __init__(self):
        self.llm = init_chat_model(
            model=model,
            temperature=0,
            model_provider="openai",
        )
        self.app = None
        self.output_model = ChatOpenAI(
            model=chat_model,
            streaming=True,
            max_retries=1,
            max_tokens=32768
        )
        self.final_prompt = ChatPromptTemplate.from_messages([
            ('system', system_prompt_template),
            ('human', question_prompt_template)
        ])

    async def initialize(self):
        """初始化代理和工作流"""
        client_map = MultiServerMCPClient(await load_single_mcp_config("amap-maps"))
        client_mcp = MultiServerMCPClient(await load_single_mcp_config("12306-mcp"))

        tools_map, tools_map_info = await list_and_return_tools(client_map)
        tools_mcp, tools_mcp_info = await list_and_return_tools(client_mcp)

        # 创建各个专家代理
        agent_map = create_react_agent(
            model=self.llm,
            name="navigation_expert",
            tools=tools_map,
            prompt=SystemMessage(content=(navigation_prompt(tools_map_info)))
        )

        agent_mcp = create_react_agent(
            model=self.llm,
            name="ticketing_expert",
            tools=tools_mcp,
            prompt=SystemMessage(content=(ticketing_prompt(tools_mcp_info)))
        )

        supervisor = create_react_agent(
            tools=[],
            model=self.llm,
            name="supervisor",
            prompt=SystemMessage(content=supervisor_prompt()),
        )

        # 创建工作流
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("supervisor", functools.partial(agent_node, agent=supervisor, name="supervisor"))
        workflow.add_node("navigation_expert", functools.partial(agent_node, agent=agent_map, name="navigation_expert"))
        workflow.add_node("ticketing_expert", functools.partial(agent_node, agent=agent_mcp, name="ticketing_expert"))

        # 添加边
        workflow.add_conditional_edges(
            "supervisor",
            supervisor_router,
            {
                "navigation_expert": "navigation_expert",
                "ticketing_expert": "ticketing_expert",
                "__end__": END
            }
        )
        workflow.add_edge("navigation_expert", "supervisor")
        workflow.add_edge("ticketing_expert", "supervisor")
        workflow.add_edge(START, "supervisor")

        self.app = workflow.compile(name="travel_agent")

    async def process_query(self, query: str) -> AsyncGenerator[str, None]:
        """处理用户查询并返回流式响应"""
        if not self.app:
            await self.initialize()

        # 第一步：获取原始响应
        agent_response = await self.app.ainvoke(
            {"messages": [HumanMessage(content=query)]}
        )
        formatted_response = await parse_messages(agent_response['messages'])

        # 第二步：使用大模型生成最终响应
        chain = self.final_prompt | self.output_model
        async for chunk in chain.astream({
            "query": query,
            "context": formatted_response
        }):
            yield chunk.content