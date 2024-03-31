import multiprocessing
import subprocess
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve

#from app import app

#asyncio.run(serve(app, Config()))
def run_flask_app():
    subprocess.run(['hypercorn', 'app:app'])

def run_tcp_server():
    subprocess.run(['python', 'tcpserver.py'])

if __name__ == "__main__":
    flask_process = multiprocessing.Process(target=run_flask_app)
    tcp_server_process = multiprocessing.Process(target=run_tcp_server)

    flask_process.start()
    tcp_server_process.start()