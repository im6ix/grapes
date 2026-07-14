from langchain_ollama import ChatOllama
import sys

llm = ChatOllama(
    model ="ministral-3:8b",
    
)

input_text = sys.stdin.read()
messages = [
    ("system", "Complete the following function based on its docstring. Return only the raw completed code with no explanation, no markdown, no fences, no comments. Nothing but the code."),
    ("human", "continue this function"+ input_text)
    
]

response = llm.invoke(messages)

if response.content.startswith("def"):
    print(response.content)
else:
    func = input_text.split("\n")[0]
    print(func + "\n" + response.content)