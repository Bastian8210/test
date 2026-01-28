from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

app = FastAPI(title="Local Link", description="Local proximity chat prototype")


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute distance between two coordinates in kilometers using haversine formula."""
    from math import asin, cos, radians, sin, sqrt

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    earth_radius_km = 6371
    return earth_radius_km * c


class Profile(BaseModel):
    display_name: Optional[str] = Field(None, description="Optional human-friendly name")
    socials: Optional[str] = Field(None, description="Links or handles to share when revealing")
    phone: Optional[str] = Field(None, description="Phone number if the user chooses to share")


class PresenceUpdate(BaseModel):
    latitude: float
    longitude: float
    visible_radius_km: float = Field(..., gt=0, description="Radius for discovering others")
    profile: Optional[Profile] = None


class UserState(BaseModel):
    user_id: str
    last_seen: datetime
    presence: PresenceUpdate


class NearbyUser(BaseModel):
    user_id: str
    distance_km: float
    profile: Optional[Profile]


class Message(BaseModel):
    to_user: str
    body: str


authenticated_users: Dict[str, UserState] = {}
connections: Dict[str, WebSocket] = {}
MESSAGE_TTL = timedelta(minutes=5)


@app.post("/presence", response_model=UserState)
async def update_presence(user_id: str, update: PresenceUpdate) -> UserState:
    """Register or update a user's presence and optional profile."""
    state = UserState(user_id=user_id, last_seen=datetime.utcnow(), presence=update)
    authenticated_users[user_id] = state
    return state


@app.get("/nearby", response_model=List[NearbyUser])
async def get_nearby(user_id: str) -> List[NearbyUser]:
    """Return users within the requesting user's chosen radius."""
    if user_id not in authenticated_users:
        raise HTTPException(status_code=404, detail="User not registered")

    requester = authenticated_users[user_id]
    now = datetime.utcnow()
    nearby: List[NearbyUser] = []
    for candidate_id, candidate in authenticated_users.items():
        if candidate_id == user_id:
            continue
        if now - candidate.last_seen > MESSAGE_TTL:
            continue

        distance = haversine_distance_km(
            requester.presence.latitude,
            requester.presence.longitude,
            candidate.presence.latitude,
            candidate.presence.longitude,
        )
        if distance <= requester.presence.visible_radius_km:
            nearby.append(
                NearbyUser(
                    user_id=candidate_id,
                    distance_km=round(distance, 3),
                    profile=candidate.presence.profile,
                )
            )
    nearby.sort(key=lambda u: u.distance_km)
    return nearby


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str) -> None:
    await websocket.accept()
    connections[user_id] = websocket
    try:
        while True:
            raw = await websocket.receive_json()
            message = Message(**raw)
            if message.to_user not in connections:
                await websocket.send_json({"error": "Recipient not connected"})
                continue
            await connections[message.to_user].send_json({"from": user_id, "body": message.body})
    except WebSocketDisconnect:
        pass
    finally:
        connections.pop(user_id, None)


@app.delete("/presence")
async def delete_presence(user_id: str) -> None:
    authenticated_users.pop(user_id, None)
    socket = connections.pop(user_id, None)
    if socket:
        await socket.close()
