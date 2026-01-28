# Local Link Prototype

This repository contains a minimal FastAPI prototype for an anonymous, proximity-based chat concept. Users broadcast their GPS coordinates, discover nearby users within a chosen radius, and chat via WebSocket. Profiles are optional and can be shared to reveal identity (social links or phone) after an anonymous start.

## Running locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the API:
   ```bash
   uvicorn app:app --reload
   ```
3. Interact:
   - Register/update presence:
     ```bash
     curl -X POST "http://127.0.0.1:8000/presence?user_id=alice" \
       -H "Content-Type: application/json" \
       -d '{"latitude":40.7128,"longitude":-74.0060,"visible_radius_km":1.0}'
     ```
   - Find nearby users:
     ```bash
     curl "http://127.0.0.1:8000/nearby?user_id=alice"
     ```
   - Connect via WebSocket at `ws://127.0.0.1:8000/ws/<user_id>` to exchange messages using a payload like `{"to_user":"bob","body":"hi"}`.
   - Remove presence: `curl -X DELETE "http://127.0.0.1:8000/presence?user_id=alice"`.

## Notes

- Presence entries expire after 5 minutes of inactivity to keep proximity results fresh.
- All data is stored in memory for demo purposes; a production build should add authentication, persistent storage, rate limiting, and safety/abuse mitigation.
