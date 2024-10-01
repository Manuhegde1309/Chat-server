import socket
import threading
import ssl
import shutil
import os

host = 'localhost'
port = 55557

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('ssl.pem', 'private.key')

# Starting Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server = context.wrap_socket(server, server_side=True)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((host, port))
server.listen()

clients = []
nicknames = []

def broadcast(message):
    for client in clients:
        client.send(message)

def handle(client, address):
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            
            if message == 'q':
                kick_user_by_client(client)
                break
            
            elif message.startswith('MEMBERS'):
                for name in nicknames:
                    if name != 'admin':
                        client.send(f'{name}, '.encode('ascii'))
                continue
            
            elif message.startswith('KICK'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_kick = message.split()[1]
                    kick_user(name_to_kick)
                else:
                    client.send('Command was refused (not an admin)'.encode('ascii'))
            
            elif message.startswith('BAN'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_ban = message.split()[1]
                    with open('banlist.txt', 'a') as f:
                        f.write(name_to_ban + '\n')
                    print(f"{name_to_ban} has been banned.")
                    kick_user(name_to_ban)
                else:
                    client.send('Command was refused (not an admin)'.encode('ascii'))
            
            elif message.startswith('Filename'):
                file_path = message.split(" ", 1)[1]
                print(f"Uploaded file path: {file_path}")
                broadcast(f"File received at: {file_path}".encode('ascii'))
                file = os.path.basename(file_path)
                downloads = os.path.join(os.path.expanduser("~"), "Downloads")
                folder_path = os.path.join(downloads, "Server Files")
                os.makedirs(folder_path, exist_ok=True)
                destination_path = os.path.join(folder_path, file)
                shutil.copy(file_path, destination_path)
            
            else:
                broadcast(message.encode('ascii'))
        
        except:
            kick_user_by_client(client)
            break

def receive():
    print("Server is listening")
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")

        client.send('MANU'.encode('ascii'))
        nickname = client.recv(1024).decode('ascii')

        if nickname in nicknames:
            client.send('DUPLICATE'.encode('ascii'))
            client.close()
            print(f'Client with IP {address} is disconnected due to duplicate nickname')
            continue
        
        with open('banlist.txt', 'r') as f:
            bans = f.readlines()
        if nickname + '\n' in bans:
            client.send('BAN'.encode('ascii'))
            client.close()
            continue
        
        if nickname == 'admin':
            client.send('PASS'.encode('ascii'))
            password = client.recv(1024).decode('ascii')
            if password != 'password':
                client.send('WRONG'.encode('ascii'))
                client.close()
                continue

        nicknames.append(nickname)
        clients.append(client)

        print(f"Nickname is {nickname}")
        broadcast(f"{nickname} joined!".encode('ascii'))
        client.send('Connected to server!'.encode('ascii'))

        thread = threading.Thread(target=handle, args=(client, address))
        thread.start()

def kick_user(name):
    if name in nicknames:
        name_index = nicknames.index(name)
        client = clients[name_index]
        clients.remove(client)
        nicknames.remove(name)
        client.send('You have been kicked by the admin'.encode('ascii'))
        client.close()
        broadcast(f"{name} was kicked by admin.".encode('ascii'))

def kick_user_by_client(client):
    if client in clients:
        index = clients.index(client)
        nickname = nicknames[index]
        clients.remove(client)
        nicknames.remove(nickname)
        broadcast(f"{nickname} left the chat!".encode('ascii'))
        print(f'Client with IP {client.getpeername()} is disconnected')
        client.close()

if __name__ == '__main__':
    receive()

