#!/usr/bin/env python3

# websocket server example

import asyncio
import time, random
import websockets


async def hello(websocket, path):
    name = await websocket.recv()
    print("<", name)

    # greeting = "hi!"
    # await websocket.send(greeting)
    # print(greeting)

    while True:
        time.sleep(random.randint(0, 5))
        await websocket.send("newlog")
        print("newlog")


start_server = websockets.serve(hello, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
