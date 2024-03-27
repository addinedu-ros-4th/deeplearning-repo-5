import socket
import cv2
import numpy as np

def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf:
            return None
        buf += newbuf
        count -= len(newbuf)
    return buf

def main():
    TCP_IP = '192.168.0.15'
    TCP_PORT = 3001

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(True)
    print("Waiting for connection...")

    conn, addr = s.accept()
    print('Connected with', addr)

    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_string = cv2.imencode('.jpg', frame)[1].tostring()
        size = len(frame_string)
        conn.sendall(str(size).ljust(16).encode())
        conn.sendall(frame_string)

        length = int(conn.recv(16).strip())
        print("Receiving frame of size:", length)
        
        frame_string = recvall(conn, length)
        
        frame_array = np.frombuffer(frame_string, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        cv2.imshow('SERVER', frame)
        
        if cv2.waitKey(1) & 0xFF == 27:
            break

    s.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()