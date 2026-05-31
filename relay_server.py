import socket
import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- ВЕБ-ЗАГЛУШКА ДЛЯ RENDER ---
class WebStub(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"OK")

def run_web_stub(port):
    server = HTTPServer(("0.0.0.0", port), WebStub)
    server.serve_forever()
# ------------------------------

def handle_traffic(source, destination):
    try:
        while True:
            data = source.recv(8192)
            if not data:
                break
            destination.sendall(data)
    except Exception:
        pass
    finally:
        source.close()
        destination.close()

def start_relay():
    # Render дает один порт. Мы отдадим его веб-заглушке, чтобы Render не ругался
    port = int(os.environ.get("PORT", 80))
    
    # Запускаем веб-заглушку в отдельном потоке
    web_thread = threading.Thread(target=run_web_stub, args=(port,), daemon=True)
    web_thread.start()
    print(f"[+] Веб-заглушка запущена на порту {port}")

    # А сам наш мост-коммутатор заставим слушать другой порт, например, 5555
    # (Внутри сети Render он будет доступен)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 5555))
    server.listen(5)
    print("[+] Сервер-коммутатор запущен на порту 5555. Ожидание подключений...")

    operator_sock = None
    client_sock = None

    while True:
        try:
            sock, addr = server.accept()
            role = sock.recv(2).decode('utf-8', errors='ignore')
            
            if role == "OP":
                operator_sock = sock
                print("[+] Подключился Оператор.")
            elif role == "CL":
                client_sock = sock
                print("[+] Подключился Клиент.")
            
            if operator_sock and client_sock:
                print("[+] Оба участника на месте. Запуск моста трафика...")
                t1 = threading.Thread(target=handle_traffic, args=(operator_sock, client_sock))
                t2 = threading.Thread(target=handle_traffic, args=(client_sock, operator_sock))
                t1.start()
                t2.start()
                
                operator_sock = None
                client_sock = None
                
        except Exception as e:
            print(f"[-] Ошибка: {e}")

if __name__ == "__main__":
    start_relay()