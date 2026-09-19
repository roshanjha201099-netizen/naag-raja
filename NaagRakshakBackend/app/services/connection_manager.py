from typing import Dict,Any 
from fastapi import WebSocket
import json

class ConnectionManager:
    def __init__(self):
        #map session/predection  id  to active websocket
        self.active_connections:Dict[str,WebSocket]={}


    async def connect(self,session_id:str,websocket:WebSocket):
        await websocket.accept()
        self.active_connections[session_id]=websocket

    def disconnect(self,session_id:str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]


    async def send_json(self,session_id:str,data:Dict[str,Any]):
        websocket=self.active_connections.get(session_id)
        if websocket:
            await websocket.send_json(data)
    
    async def send_text(self,session_id:str,text:str):
        websocket=self.active_connections.get(session_id)
        if websocket:
            await websocket.send_text(text)
            
    async def broadcast(self,data:Dict[str,Any]):
        payload=json.dumps(data)
        for connections in self.active_connections.values():
            await connections.send_text(payload)

ws_manager=ConnectionManager()
    
