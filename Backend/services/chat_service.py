from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .analysis_service import analyze_and_respond
from database import SessionLocal, ChatMessage

chat_router = APIRouter()

@chat_router.websocket("/ws/chat/{student_id}")
async def websocket_endpoint(websocket: WebSocket, student_id: str):
    await websocket.accept()
    db = SessionLocal()
    try:
        while True:
            data = await websocket.receive_text()
            # IA analiza
            result = await analyze_and_respond(data)
            
            # Guardar en DB
            msg_in = ChatMessage(student_id=student_id, sender="student", text=data, risk_level="N/A")
            msg_out = ChatMessage(student_id=student_id, sender="bot", text=result["response"], risk_level=result["risk_level"])
            db.add(msg_in)
            db.add(msg_out)
            db.commit()
            
            await websocket.send_json({"text": result["response"], "risk": result["risk_level"]})
    except WebSocketDisconnect:
        db.close()