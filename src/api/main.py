
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio

from ..core.config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class WebhookEvent(BaseModel):
    event: str
    event_ts: int
    payload: Dict[str, Any]


class BotStatus(BaseModel):
    instance_id: str
    room_id: str
    room_name: str
    is_active: bool
    participants: int
    created_at: str


class ChatMessage(BaseModel):
    room_id: str
    message: str
    sender_id: str


def create_app() -> FastAPI:

    app = FastAPI(
        title="Zoom Interview Bot API",
        description="API for managing Zoom interview bot instances",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    bot_manager = None

    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting FastAPI application")

        nonlocal bot_manager
        from ..core.bot_manager import BotManager
        bot_manager = BotManager()
        await bot_manager.start()

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down FastAPI application")

        if bot_manager:
            await bot_manager.stop()

    @app.get("/")
    async def root():
        return {
            "message": "Zoom Interview Bot API",
            "version": "1.0.0",
            "status": "running"
        }

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time()
        }

    @app.post("/webhooks/zoom")
    async def zoom_webhook(event: WebhookEvent, background_tasks: BackgroundTasks):
        try:
            logger.info(f"Received Zoom webhook: {event.event}")

            background_tasks.add_task(process_zoom_webhook_task, event)

            return {"status": "received"}

        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            raise HTTPException(status_code=500, detail="Webhook processing failed")

    @app.get("/bots", response_model=List[BotStatus])
    async def list_bots():
        if not bot_manager:
            raise HTTPException(status_code=503, detail="Bot manager not available")

        try:
            rooms_status = await bot_manager.get_all_rooms_status()

            return [
                BotStatus(
                    instance_id=status.get("bot_instance_id", ""),
                    room_id=status["room_id"],
                    room_name=status["room_name"],
                    is_active=status["is_active"],
                    participants=status["participants"],
                    created_at=status["created_at"]
                )
                for status in rooms_status
            ]

        except Exception as e:
            logger.error(f"Error listing bots: {e}")
            raise HTTPException(status_code=500, detail="Failed to list bots")

    @app.get("/bots/{room_id}")
    async def get_bot_status(room_id: str):
        if not bot_manager:
            raise HTTPException(status_code=503, detail="Bot manager not available")

        try:
            status = await bot_manager.get_room_status(room_id)

            if not status:
                raise HTTPException(status_code=404, detail="Bot not found")

            return status

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get bot status")

    @app.post("/bots/{room_id}/chat")
    async def send_chat_message(room_id: str, message: ChatMessage):
        try:
            from ..zoom.client import send_chat_message

            success = await send_chat_message(room_id, message.message)

            if success:
                return {"status": "sent", "message": message.message}
            else:
                raise HTTPException(status_code=500, detail="Failed to send message")

        except Exception as e:
            logger.error(f"Error sending chat message: {e}")
            raise HTTPException(status_code=500, detail="Failed to send message")

    @app.delete("/bots/{room_id}")
    async def stop_bot(room_id: str):
        if not bot_manager:
            raise HTTPException(status_code=503, detail="Bot manager not available")

        try:
            await bot_manager.handle_room_closed({"room_id": room_id})

            return {"status": "stopped", "room_id": room_id}

        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
            raise HTTPException(status_code=500, detail="Failed to stop bot")

    @app.get("/metrics")
    async def get_metrics():
        try:
            return {
                "active_bots": len(bot_manager.active_rooms) if bot_manager else 0,
                "total_rooms_processed": 0,
                "uptime_seconds": 0,
                "memory_usage_mb": 0,
                "cpu_usage_percent": 0
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to get metrics")

    @app.post("/admin/reload-config")
    async def reload_config():
        try:
            logger.info("Configuration reload requested")

            return {"status": "reloaded"}

        except Exception as e:
            logger.error(f"Error reloading config: {e}")
            raise HTTPException(status_code=500, detail="Failed to reload config")


    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        return JSONResponse(
            status_code=404,
            content={"detail": "Endpoint not found"}
        )

    @app.exception_handler(500)
    async def internal_error_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

    return app


async def process_zoom_webhook_task(event: WebhookEvent):
    try:
        event_type = event.event
        payload = event.payload

        logger.info(f"Processing webhook event: {event_type}")


        if event_type == "meeting.participant_joined_breakout_room":
            logger.info("Participant joined breakout room")
        elif event_type == "meeting.participant_left_breakout_room":
            logger.info("Participant left breakout room")
        elif event_type == "meeting.breakout_room_started":
            logger.info("Breakout room started")
        elif event_type == "meeting.breakout_room_ended":
            logger.info("Breakout room ended")

    except Exception as e:
        logger.error(f"Error processing webhook event: {e}")


app = create_app()
