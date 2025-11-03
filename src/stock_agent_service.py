import json
from typing import Optional, Dict, Any, List, Callable
from openai import OpenAI
import yfinance as yf
from dotenv import load_dotenv
import os
from queue import Queue
from threading import Event

# Load environment variables
load_dotenv()

LLM_MODEL = "moonshotai/Kimi-K2-Instruct-0905"  # Updated model name

class WebConsole:
    def __init__(self):
        self.output_callback: Optional[Callable[[str], None]] = None
        self.input_queue: Queue[str] = Queue()
        self.input_ready = Event()
        
    def set_output_callback(self, callback: Callable[[str], None]) -> None:
        """Set the callback function that will handle output to the web interface."""
        self.output_callback = callback
        
    def print(self, message: str) -> None:
        """Send output to the web interface."""
        if self.output_callback:
            self.output_callback(message)
            
    def input(self, prompt: str = "") -> str:
        """Get input from the web interface."""
        if prompt and self.output_callback:
            self.output_callback(prompt)
        
        # Clear any previous input
        self.input_ready.clear()
        
        # Wait for input to be provided through provide_input
        self.input_ready.wait()
        
        # Get and return the input
        return self.input_queue.get()
        
    def provide_input(self, user_input: str) -> None:
        """Provide input from the web interface."""
        self.input_queue.put(user_input)
        self.input_ready.set()

class StockInfoAgent:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=os.getenv('OPENAI_API_KEY'))
        self.conversation_history = []
        self.console = WebConsole()
        
    def get_stock_price(self, ticker_symbol: str) -> Optional[str]:
        """Fetches the current stock price for the given ticker_symbol."""
        try:
            stock = yf.Ticker(ticker_symbol.upper())
            info = stock.info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if current_price:
                return f"{current_price:.2f} USD"
            return None
        except Exception as e:
            error_msg = f"Error fetching stock price: {e}"
            self.console.print(error_msg)
            return None
    
    def get_company_ceo(self, ticker_symbol: str) -> Optional[str]:
        """Fetches the name of the CEO for the company associated with the ticker_symbol."""
        try:
            stock = yf.Ticker(ticker_symbol.upper())
            info = stock.info
            
            # Look for CEO in various possible fields
            ceo = None
            for field in ['companyOfficers', 'officers']:
                if field in info:
                    officers = info[field]
                    if isinstance(officers, list):
                        for officer in officers:
                            if isinstance(officer, dict):
                                title = officer.get('title', '').lower()
                                if 'ceo' in title or 'chief executive' in title:
                                    ceo = officer.get('name')
                                    break
            
            # Fallback to general company info
            if not ceo and 'longBusinessSummary' in info:
                ceo = None  
                
            return ceo
        except Exception as e:
            error_msg = f"Error fetching CEO info: {e}"
            self.console.print(error_msg)
            return None
    
    def find_ticker_symbol(self, company_name: str) -> Optional[str]:
        """Tries to identify the stock ticker symbol for a given company_name."""
        try:
            # Use yfinance Lookup to search for the company
            lookup = yf.Lookup(company_name)
            
            stock_results = lookup.get_stock(count=5)
            
            if not stock_results.empty:
                return stock_results.index[0]
            
            # If no stocks found, try all instruments
            all_results = lookup.get_all(count=5)
            
            if not all_results.empty:
                return all_results.index[0]
                
        except Exception as e:
            error_msg = f"Error searching for ticker: {e}"
            self.console.print(error_msg)
            
        return None
    
    def ask_user_for_clarification(self, question_to_user: str) -> str:
        """Poses the question_to_user to the actual user and returns their typed response."""
        self.console.print(f"Agent needs clarification: {question_to_user}")
        response = self.console.input("Your response: ")
        return response
    
    def create_tool_definitions(self) -> List[Dict[str, Any]]:
        """Creates OpenAI function calling definitions for the tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_stock_price",
                    "description": "Fetches the current stock price for the given ticker symbol",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker_symbol": {
                                "type": "string",
                                "description": "The stock ticker symbol (e.g., 'AAPL', 'MSFT')"
                            }
                        },
                        "required": ["ticker_symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_company_ceo",
                    "description": "Fetches the name of the CEO for the company associated with the ticker symbol",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker_symbol": {
                                "type": "string",
                                "description": "The stock ticker symbol"
                            }
                        },
                        "required": ["ticker_symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_ticker_symbol",
                    "description": "Tries to identify the stock ticker symbol for a given company name",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "company_name": {
                                "type": "string",
                                "description": "The name of the company"
                            }
                        },
                        "required": ["company_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ask_user_for_clarification",
                    "description": "Poses a question to the user and returns their response",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question_to_user": {
                                "type": "string",
                                "description": "The question to ask the user"
                            }
                        },
                        "required": ["question_to_user"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Executes the specified tool with given arguments."""
        if tool_name == "get_stock_price":
            return self.get_stock_price(arguments["ticker_symbol"])
        elif tool_name == "get_company_ceo":
            return self.get_company_ceo(arguments["ticker_symbol"])
        elif tool_name == "find_ticker_symbol":
            return self.find_ticker_symbol(arguments["company_name"])
        elif tool_name == "ask_user_for_clarification":
            return self.ask_user_for_clarification(arguments["question_to_user"])
        else:
            return None
    
    def process_user_query(self, user_query: str) -> str:
        """Processes a user query using the OpenAI API with function calling."""
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": user_query})
        
        system_prompt = """You are a helpful stock information assistant. You have access to tools that can:
                        1. Get current stock prices
                        2. Find company CEOs
                        3. Find ticker symbols for company names
                        4. Ask users for clarification when needed

                        Use these tools to help answer user questions about stocks and companies. If information is ambiguous, ask for clarification."""
        
        while True:
            messages = [
                {"role": "system", "content": system_prompt},
                *self.conversation_history
            ]
            
            # Call OpenAI API with function calling
            response = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=self.create_tool_definitions(),
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            
            # If no tool calls, we're done
            if not response_message.tool_calls:
                self.conversation_history.append({"role": "assistant", "content": response_message.content})
                return response_message.content
            
            # Execute the first tool call
            tool_call = response_message.tool_calls[0]
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            self.console.print(f"Executing tool: {function_name} with args: {function_args}")
            
            # Execute the tool
            result = self.execute_tool(function_name, function_args)
            
            # Add the assistant's message with tool calls to history
            self.conversation_history.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": function_name,
                        "arguments": json.dumps(function_args)
                    }
                }]
            })
            
            # Add tool result to history
            self.conversation_history.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": str(result) if result is not None else "No result found"
            })
    
if __name__ == "__main__":
    # This file is now meant to be imported as a module
    pass