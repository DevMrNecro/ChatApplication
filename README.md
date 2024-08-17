---

# Chat Application

This is a Django-based real-time chat application built with Django Channels, WebSockets, and Redis.

## Features

- **Real-Time Communication:** Supports real-time messaging using WebSockets.
- **User Management:** Users can join and leave chat rooms.
- **Persistent Storage:** Messages are stored in a SQLite database.
- **WebSocket Integration:** Efficient communication with Django Channels and Redis.

## Prerequisites

To run this application, the following files must be present in your project directory:

- `.env`
- `Dockerfile`
- `docker-compose.yml`

All setup and dependencies are managed through Docker.

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/yourrepository.git
   cd yourrepository
   ```

2. **Setup Docker:**
   Ensure you have Docker and Docker Compose installed on your system.

3. **Start the Application:**
   ```bash
   sudo docker compose up -d --build
   ```

   This command will:
   - Build the Docker image.
   - Apply database migrations.
   - Collect static files.
   - Start the Daphne server for handling WebSocket connections.

## Configuration

- **Environment Variables:** All configuration is managed via the `.env` file. This includes secret keys, debug settings, allowed hosts, and Redis configuration.

## Usage

Once the application is running, you can access it at `http://localhost:8000`. 

### API Endpoints

- **Chat Rooms:** `/api/chatrooms/` - Manage chat rooms.
- **Messages:** `/api/messages/` - Manage messages.

### WebSocket Endpoints

- **Chat Room WebSocket:** `ws://localhost:8000/ws/chat/<room_name>/<user_id>/`

## Built With

- **Django**
- **Django Channels**
- **Redis**
- **Docker**

---
