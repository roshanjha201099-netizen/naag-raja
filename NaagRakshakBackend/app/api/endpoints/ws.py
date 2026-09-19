import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.database import AsyncSessionLocal
from app.services.connection_manager import ws_manager
from app.services.medical_router import EmergencyMedicalRouter

logger = logging.getLogger("naagrakshak.ws_endpoint")
router = APIRouter()
ws_router = router

async def _process_telemetry_session(websocket: WebSocket, session_id: str):
    await ws_manager.connect(session_id, websocket)
    logger.info(f"WebSocket client connected with session_id: {session_id}")

    try:
        # Acknowledge connection to client
        await websocket.send_text(json.dumps({
            "type": "CONNECTED",
            "event": "CONNECTED",
            "session_id": session_id,
            "message": "Real-time WebSocket telemetry connection established."
        }))

        while True:
            raw_msg = await websocket.receive_text()
            try:
                data = json.loads(raw_msg)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type") or data.get("event")

            # Process live GPS updates from user in transit
            if msg_type == "GPS_UPDATE":
                lat = data.get("latitude")
                lng = data.get("longitude")
                state = data.get("state", None)

                if lat is not None and lng is not None:
                    async with AsyncSessionLocal() as db_session:
                        try:
                            # Direct call to EmergencyMedicalRouter
                            nearest_hospitals = await EmergencyMedicalRouter.get_nearest_facilities(
                                user_lat=float(lat),
                                user_lng=float(lng),
                                db=db_session,
                                state=state,
                                max_results=3
                            )

                            await ws_manager.send_json(session_id, {
                                "type": "FACILITIES_RECALCULATED",
                                "event": "FACILITIES_RECALCULATED",
                                "nearest_hospitals": nearest_hospitals
                            })
                            logger.info(f"Recalculated {len(nearest_hospitals)} facilities for session: {session_id}")
                        except Exception as calc_err:
                            logger.error(f"Error recalculating facilities for GPS update: {calc_err}")

    except WebSocketDisconnect:
        ws_manager.disconnect(session_id)
        logger.info(f"WebSocket client disconnected for session_id: {session_id}")
    except Exception as e:
        logger.error(f"Unexpected WebSocket failure for {session_id}: {e}")
        ws_manager.disconnect(session_id)

@router.websocket("/ws/telemetry/{session_id}")
async def telemetry_websocket(websocket: WebSocket, session_id: str):
    await _process_telemetry_session(websocket, session_id)

@router.websocket("/ws/{session_id}")
async def default_websocket(websocket: WebSocket, session_id: str):
    await _process_telemetry_session(websocket, session_id)
