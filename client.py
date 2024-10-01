import socket
import threading
import ssl
import os

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
host = 'localhost'
context.load_verify_locations('ssl.pem')

nickname = input("Choose your nickname: ")
if nickname == 'admin':
    passwd = input("Enter password: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client = context.wrap_socket(client, server_hostname=host)
client.connect((host, 55557))

stop_thread = False

def receive():
    global stop_thread
    while True:
        if stop_thread:
            break
        try:
            message = client.recv(1024).decode('ascii')
            if message == 'MANU':
                client.send(nickname.encode('ascii'))
                next_message = client.recv(1024).decode('ascii')
                if next_message == 'PASS':
                    client.send(passwd.encode('ascii'))
                    if client.recv(1024).decode('ascii') == 'WRONG':
                        print('Wrong password, press Ctrl+C to exit')
                        stop_thread = True
                elif next_message == 'BAN':
                    print('Connection refused due to ban, press Ctrl+C to exit')
                    client.close()
                    stop_thread = True
                elif next_message == 'DUPLICATE':
                    print('This user already exists, press Ctrl+C to stop execution')
                    client.close()
                    stop_thread = True
            else:
                print(message)
        except:
            print("An error occurred!")
            client.close()
            break

def write():
    global stop_thread
    while True:
        if stop_thread:
            break
        message = input()
        if message == 'q':
            client.send(message.encode('ascii'))
            print("You have left the chat.")
            client.close()
            stop_thread = True
            break
        elif message.startswith('/'):
            command_parts = message.split(" ")
            if len(command_parts) >= 1:
                if command_parts[0] == '/file':
                    file_path = command_parts[1].strip()
                    if os.path.exists(file_path):
                        client.send(f'Filename {file_path}'.encode('ascii'))
                    else:
                        print("File not found!")
                elif nickname == 'admin':
                    if command_parts[0] == '/kick':
                        client.send(f'KICK {command_parts[1]}'.encode('ascii'))
                    elif command_parts[0] == '/ban':
                        client.send(f'BAN {command_parts[1]}'.encode('ascii'))
                    elif command_parts[0] == '/members':
                        client.send(f'MEMBERS'.encode('ascii'))
                    else:
                        print("Invalid command")
                else:
                    print("You are not admin")
            else:
                print("Invalid command format")
        else:
            client.send(f'{nickname}: {message}'.encode('ascii'))

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()

receive_thread.join()
write_thread.join()

