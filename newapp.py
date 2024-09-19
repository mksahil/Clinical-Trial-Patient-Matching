# from modal import Image, App, asgi_app, Secret
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json

from qudrant import upload_website_to_collection
from rag import async_get_answer_and_docs, get_answer_and_docs



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
     

# @app.websocket('/async_chat')
# async def async_chat(websocket: WebSocket):
#       await websocket.accept()
#       while True:
#             question = await websocket.receive_text()
#             async for event in async_get_answer_and_docs(question):
#                 if event["event_type"] == "done":
#                     await websocket.close()
#                     return
#                 else:
#                     await websocket.send_text(json.dumps(event))


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
    # return app

