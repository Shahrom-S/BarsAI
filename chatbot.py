import os
import asyncio
from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
from langchain_core.prompts import PromptTemplate
from collections import deque

model_path = os.path.join(os.path.dirname(__file__), "models--TheBloke--Llama-2-7B-Chat-GGUF", "blobs",
                          "e0b99920cf47b94c78d2fb06a1eceb9ed795176dfa3f7feac64629f1b52b997f")

def load_model():
    ''' Load Llama model with error handling '''
    if not os.path.exists(model_path):
        print("Model path does not exist:", model_path)
        return None

    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

    try:
        llama_model = LlamaCpp(
            model_path=model_path,
            temperature=0.5,
            n_gpu_layers=16,
            n_batch=1,
            max_tokens=512,
            top_p=0.9,
            callback_manager=callback_manager,
            verbose=True
        )
        return llama_model
    except Exception as e:
        print(f"Failed to load model due to an error: {e}")
        return None

def generate_response(model, query, history):
    """Generates a response with prompt template and history."""
    prompt_template = """
    {history}
    User Query: {query}
    Required Response: 
    Provide a concise and informative response without asking any further questions.
    """

    prompt = PromptTemplate(
        input_variables=["history", "query"], template=prompt_template
    )
    full_prompt = prompt.format(history="\n".join(history), query=query)
    response = model(full_prompt)
    return response.strip()

async def async_main():
    llm = load_model()
    if llm is None:
        print("Failed to initialize the LLaMA model.")
        return

    history = deque(maxlen=4)

    print("Welcome to the LLaMA Chatbot! Type 'exit' to quit.")
    while True:
        user_query = await asyncio.get_event_loop().run_in_executor(None, input, "\nAsk a question: ")
        if user_query.lower() == 'exit':
            break

        response = await asyncio.get_event_loop().run_in_executor(None, generate_response, llm, user_query, list(history))
        print("Response:", response)
        history.extend([f"User Query: {user_query}", f"Assistant Response: {response}"])

if __name__ == "__main__":
    asyncio.run(async_main())
