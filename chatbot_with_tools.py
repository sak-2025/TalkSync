from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun

from langchain.tools import tool
from langchain_core.messages import BaseMessage,HumanMessage

from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode,tools_condition
from langchain_community.tools.tavily_search import TavilySearchResults

from dotenv import load_dotenv
from typing import Annotated ,TypedDict,List,Set
import os
import requests

load_dotenv()
STOCK_KEY = os.getenv('STOCK_KEY')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')

import sqlite3

connection = sqlite3.connect(database='chatbot.db',check_same_thread=False)
checkpointer = SqliteSaver(conn=connection)



llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class ChatState(TypedDict):
    messages : Annotated[List[BaseMessage],add_messages]


def chat_node(state : ChatState):
    mesg = state['messages']
    result = llm_with_Tool.invoke(mesg)
    return {'messages' : [result]}


## Create Tools 

# --- Search Tool (Tavily preferred, fallback to DuckDuckGo)
if TAVILY_API_KEY:
    print("Using Tavily Search Tool")
    search_tool = TavilySearchResults(api_key=TAVILY_API_KEY)
else:
    print("Tavily API key not found, falling back to DuckDuckGo")
    search_tool = DuckDuckGoSearchRun(region="us-en")


@tool
def get_stock_price(symbol :str):
       """ Fetches the **latest real-time stock price** for a company given its **stock ticker symbol** (e.g., 'GOOG', 'AAPL', 'MSFT'). 
       Use this tool ONLY when the user asks specifically for the *stock price*, *quote*, or *ticker* of a company.
       The symbol must be the standard market ticker.
       """
       print ( " In stock tool")
       url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={STOCK_KEY}"
       response =requests.get(url)
       return response.json()



tools = [search_tool,get_stock_price]
#llm with tools
llm_with_Tool = llm.bind_tools(tools)

tool_node = ToolNode(tools)

# workflow
workflow  = StateGraph(ChatState)
workflow.add_node('chat_node',chat_node)
workflow.add_node('tools',tool_node)

workflow.add_edge(START , 'chat_node')
workflow.add_conditional_edges('chat_node',tools_condition)
workflow.add_edge('tools','chat_node')  #  send back to chat node

app = workflow.compile(checkpointer=checkpointer)

#result =app.invoke({'messages': [HumanMessage(content="Hi  ")]})
#print(result['messages'][-1].content)



# helper methods
# retrieve all threads from db
def retireve_all_threads():
  all_threads = set()
  for checkpoint in checkpointer.list(None):
   # print(checkpoint.config['configurable']['thread_id'])
    all_threads.add(checkpoint.config['configurable']['thread_id'])
  print(list(all_threads))
  return list(all_threads)