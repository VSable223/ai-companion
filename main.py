import asyncio, os, json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import socketio
import httpx

# Socket.IO server (ASGI)
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

# Mount Socket.IO ASGI app at /signal
from socketio.asgi import ASGIApp
app.mount('/signal', ASGIApp(sio))

# Serve static frontend files from ./static
app.mount('/static', StaticFiles(directory='static'), name='static')

@app.get('/')
async def index():
    return FileResponse('static/index.html')

async def query_ollama(prompt: str) -> str:
    """Query local Ollama API (http://localhost:11434). If not available, return None."""
    try:
        url = 'http://localhost:11434/api/generate'
        payload = {"model": "llama3", "prompt": prompt}
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, json=payload)
            if r.status_code == 200:
                try:
                    data = r.json()
                    if isinstance(data, dict):
                        # common fields
                        if 'response' in data: return data['response']
                        if 'text' in data: return data['text']
                        if 'output' in data: return data['output']
                    return r.text
                except Exception:
                    return r.text
            else:
                return f"Ollama error {r.status_code}: {r.text}"
    except Exception as e:
        # Ollama unreachable
        return None

@sio.event
async def connect(sid, environ):
    print('connect', sid)

@sio.event
async def disconnect(sid):
    print('disconnect', sid)

@sio.on('user_message')
async def on_user_message(sid, data):
    # data: {text}
    text = data.get('text', '')
    print('user_message:', text)
    reply = await query_ollama(text)
    if reply is None:
        reply = "Hi — this is a demo AI reply. To enable richer replies, install Ollama and pull a model (e.g. 'ollama pull llama3')."
    await sio.emit('ai_reply', {'text': reply}, to=sid)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
