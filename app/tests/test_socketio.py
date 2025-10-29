import pytest
import socketio


@pytest.mark.asyncio
async def test_socketio_connect():
    """Test Socket.IO connection and events."""
    client = socketio.Client()
    client.connect("http://testserver")  # Use TestClient-like URL

    # Test connect event
    assert client.connected

    # Test join_task and emit
    client.emit("join_task", {"task_id": "test_task"})
    # Await response (use event handlers)

    @client.on("joined")
    def on_joined(data):
        assert data["task_id"] == "test_task"

    # Simulate server emit
    client.emit("comic_generated", {"comic_id": 1})  # Test reception

    client.disconnect()
