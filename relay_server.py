import socket
import threading
import os

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
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Render сам передает порт в переменные окружения, если его нет — берем 80
    port = int(os.environ.get("PORT", 80))
    server.bind(("0.0.0.0", port))
    server.listen(5)
    print(f"[+] Сервер-коммутатор запущен на порту {port}. Ожидание подключений...")

    operator_sock = None
    client_sock = None

    while True:
        try:
            sock, addr = server.accept()
            # Первое, что должен прислать участник — это его роль ("OP" или "CL")
            role = sock.recv(2).decode('utf-8', errors='ignore')
            
            if role == "OP":
                operator_sock = sock
                print("[+] Подключился Оператор.")
            elif role == "CL":
                client_sock = sock
                print("[+] Подключился Клиент.")
            
            # Как только оба на связи — создаем мост
            if operator_sock and client_sock:
                print("[+] Оба участника на месте. Запуск моста трафика...")
                t1 = threading.Thread(target=handle_traffic, args=(operator_sock, client_sock))
                t2 = threading.Thread(target=handle_traffic, args=(client_sock, operator_sock))
                t1.start()
                t2.start()
                
                # Обнуляем переменные для следующих подключений
                operator_sock = None
                client_sock = None
                
        except Exception as e:
            print(f"[-] Ошибка: {e}")

if __name__ == "__main__":
    start_relay()