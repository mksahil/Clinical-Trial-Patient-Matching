from modal import Image, App, asgi_app, Secret
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json

from backend.src.rag import async_get_answer_and_docs, get_answer_and_docs 
from backend.src.qudrant import upload_website_to_collection


# app.image = Image.debian_slim().pip_install_from_requirements("./backend/src/requirements.txt")

dbt_image = (  # start from a slim Linux image
    Image.debian_slim(python_version="3.11")
    .pip_install(  # install python packages
        "langchain-community~=0.2.11",  # aws client sdk
        "langchain-core~=0.2.28",  # dbt and duckdb and a connector
        "pandas~=2.2.2",  # dataframes
        "pyarrow~=16.1.0",  # columnar data lib
    )
)

app = App("rag-backend", image=dbt_image)


# app.image = (
#     Image.debian_slim()
#     .pip_install("langchain","langchain-community", "qdrant-client")
#     .run_command("pip list")  # This will output the list of installed packages
# )


@asgi_app()
def endpoint():
    app=FastAPI()

    origins = [
  "*",
  '''
  "http://127.0.0.1:8000/" 
  '''
]

    app.add_middleware(
    CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


    class Message(BaseModel):
     message: str
     

    @app.websocket('/async_chat')
    async def async_chat(websocket: WebSocket):
      await websocket.accept()
      while True:
            question = await websocket.receive_text()
            async for event in async_get_answer_and_docs(question):
                if event["event_type"] == "done":
                    await websocket.close()
                    return
                else:
                    await websocket.send_text(json.dumps(event))


    @app.post("/chat" ,description="Chat with Rag api through this end point")
    def chat(message:Message):
                response=get_answer_and_docs(message)
                response_content={
                    "question":message.message,
                    "answer":response["answer"],
                    "documents":[doc.dict() for doc in response["context"]]     
                }
                return JSONResponse(content=response_content,status_code=200)


    @app.post("/indexing", description="Index a website through this endpoint")
    def indexing(url: Message):
              try:
                  response = upload_website_to_collection(url.message)
                  return JSONResponse(content={"response": response}, status_code=200)
        
              except Exception as e:
                  return JSONResponse(content={"error": str(e)}, status_code=400)
    return app

