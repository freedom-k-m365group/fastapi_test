import socketio

sio = socketio.AsyncServer(async_mode='asgi',
                           cors_allowed_origins='*',
                           client_manager=socketio.RedisManager(
                               'redis://localhost:6379'))
