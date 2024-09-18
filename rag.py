from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_community.chat_models import ChatOpenAI
from operator import itemgetter

# from decouple import config

from qudrant import vector_store

from langchain_community.chat_models import AzureChatOpenAI
model = AzureChatOpenAI(    
    azure_deployment="GPT4",
    api_key="",
    model="gpt-4",
    api_version="2024-02-01",
    azure_endpoint="https://ctmatchinggpt.openai.azure.com/",
    temperature=0,
    )


prompt_template = """
Answer the question based on the context, in a concise manner, in markdown and using bullet points where applicable.

Context: {context}
Question: {question}
Answer:
"""

prompt = ChatPromptTemplate.from_template(prompt_template)

retriever = vector_store.as_retriever()

def create_chain():
    chain = (
        {
            "context": retriever.with_config(top_k=4),
            "question": RunnablePassthrough(),
        }
        | RunnableParallel({
            "response": prompt | model,
            "context": itemgetter("context"),
            })
    )
    return chain

def get_answer_and_docs(question: str):
    chain = create_chain()
    response = chain.invoke(question)
    answer = response["response"].content
    context = response["context"]
    return {
        "answer": answer,
        "context": context
    }

# response=get_answer_and_docs("what is a author of this article")

# print(response)


async def async_get_answer_and_docs(question: str):
    chain = create_chain()
    async for event in chain.astream_events(question, version='v1'):
        event_type = event['event']
        if event_type == "on_retriever_end":
            yield {
                "event_type": event_type,
                "content": [doc.dict() for doc in event['data']['output']['documents']]
            }
        elif event_type == "on_chat_model_stream":
            yield {
                "event_type": event_type,
                "content": event['data']['chunk'].content
            }
    yield {
        "event_type": "done"
    }


# async def async_get_answer_and_docs(question: str):
#     docs = qdrant_search(query=question)
#     docs_dict = [doc.payload for doc in docs]
#     yield {
#         "event_type": "on_retriever_end",
#         "content": docs_dict
#     }

#     async for chunk in stream_completion(question, docs_dict):
#         yield {
#             "event_type": "on_chat_model_stream",
#             "content": chunk
#     }

#     yield {
#         "event_type": "done"
#     }