import json

BOT_port=8888

def send_json(socket, message):
    """1. convertir le dictionnaire Python en JSON
2. encoder en UTF-8
3. calculer la taille du message
4. envoyer la taille
5. envoyer le JSON"""
    json_string = json.dumps(message)
    json_bytes = json_string.encode('utf-8')
    message_size = len(json_bytes)
    socket.sendall(str(message_size).encode('utf-8') + b'\n')
    socket.sendall(json_bytes)

def receive_json(socket):
    """
    1. lire la taille du message
2. lire exactement ce nombre d octets
3. décoder en UTF-8
4. transformer le JSON en dictionnaire Python"""
    size_str = b''
    while b'\n' not in size_str:
        chunk = socket.recv(1)
        if not chunk:
            break
        size_str += chunk
    message_size = int(size_str.strip())
    
    json_bytes = b''
    while len(json_bytes) < message_size:
        chunk = socket.recv(message_size - len(json_bytes))
        if not chunk:
            break
        json_bytes += chunk
    
    json_string = json_bytes.decode('utf-8')
    
    message = json.loads(json_string)
    return message