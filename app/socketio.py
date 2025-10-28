import socketio

sio = socketio.AsyncServer(async_mode='asgi',
                           cors_allowed_origins='*',
                           client_manager=socketio.AsyncRedisManager(
                               'redis://localhost:6379/0'))
