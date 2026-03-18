import socket

hosts = ["127.0.0.1", "host.docker.internal", "172.30.144.1"]
port = 3306

for host in hosts:
    sock = socket.socket()
    sock.settimeout(2)
    code = sock.connect_ex((host, port))
    sock.close()
    status = "ok" if code == 0 else f"fail({code})"
    print(f"{host}:{port} -> {status}")
