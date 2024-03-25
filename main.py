import multiprocessing
import subprocess

def run_flask_app():
    subprocess.run(['python', 'app.py'])

def run_tcp_server():
    subprocess.run(['python', 'tcpserver.py'])

if __name__ == "__main__":
    flask_process = multiprocessing.Process(target=run_flask_app)
    tcp_server_process = multiprocessing.Process(target=run_tcp_server)

    flask_process.start()
    tcp_server_process.start()