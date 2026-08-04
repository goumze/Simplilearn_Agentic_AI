from dotenv import load_dotenv
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper, ArxivAPIWrapper
from langchain_tavily import TavilySearch
from langchain_core.messages import HumanMessage, ToolMessage
import time

from langchain_openai import ChatOpenAI

load_dotenv()


if __name__ == "__main__":
    # Arxiv Tool
    try:
        api_wrapper_arxiv = ArxivAPIWrapper(top_k_results=2, doc_content_chars_max=500)
        arxiv = ArxivQueryRun(api_wrapper=api_wrapper_arxiv)

        #print(f"Tool name: {arxiv.name}")
        
        #print("\nSearching arXiv for 'Attention is all you need'...")
        #result = arxiv.invoke("Attention is all you need")
        #print(f"Result: {result}")
    
    # Add a small delay to avoid rate limiting
        time.sleep(2)

    # Wikipedia Tool
    
        api_wrapper_wiki = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=500)
        wiki = WikipediaQueryRun(api_wrapper=api_wrapper_wiki)

        # print(f"\nTool name: {wiki.name}")
        
        # print("Searching Wikipedia for 'Attention is all you need'...")
        #result = wiki.invoke("Attention is all you need")
        #print(f"Result: {result}")

        #Tavily Search Tool
        tavily_search = TavilySearch()
        #tavily_search_results = tavily_search.invoke("Provide me the current AI news")
        #print(f"\nTavily Search Results: {tavily_search_results}")
        
        #Combine all the tools
        tools = [arxiv, wiki, tavily_search]
        llm = ChatOpenAI(model_name="gpt-4")
        llm_with_tools = llm.bind_tools(tools)

        # Ask for grounded output and explicit source links from the tool results.
        prompt = (
            "Use available tools to find recent AI news from the last 7 days. "
            "After tool calls, return a concise summary with 5 bullet points and include source URLs."
        )

        messages = [HumanMessage(content=prompt)]
        first_response = llm_with_tools.invoke(messages)

        print("\nFirst AI Response:")
        print(first_response.tool_calls)

        # if first_response.tool_calls:
        #     tools_by_name = {tool.name: tool for tool in tools}

        #     for tool_call in first_response.tool_calls:
        #         tool_name = tool_call["name"]
        #         tool_args = tool_call.get("args", {})

        #         if tool_name not in tools_by_name:
        #             tool_output = f"Tool '{tool_name}' is not available."
        #         else:
        #             tool_output = tools_by_name[tool_name].invoke(tool_args)

        #         messages.append(first_response)
        #         messages.append(
        #             ToolMessage(
        #                 content=str(tool_output),
        #                 tool_call_id=tool_call["id"],
        #             )
        #         )

        #     final_response = llm_with_tools.invoke(messages)
        #     print("\nFinal AI Response:")
        #     print(final_response.content)
        # else:
        #     print("\nFinal AI Response:")
        #     print(first_response.content)
    except Exception as e:
        print(f"Error with tool: {type(e).__name__}: {e}")

    