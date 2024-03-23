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

def run_client():
    TCP_IP = '192.168.0.29'
    TCP_PORT = 3008

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))

    cap = cv2.VideoCapture(0)  # Open local webcam

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_string = cv2.imencode('.jpg', frame)[1].tobytes()  # Change tostring() to tobytes()
        size = len(frame_string)
        s.sendall(str(size).ljust(16).encode())
        s.sendall(frame_string)

        length_header = s.recv(16)
        if not length_header:
            break
        length = int(length_header.strip())
        print("Receiving frame of size:", length)
        
        frame_string = recvall(s, length)
        
        frame_array = np.frombuffer(frame_string, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        
        cv2.imshow('Received', frame)  # Show received frame
        
        if cv2.waitKey(1) & 0xFF == 27:
            break

    s.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_client()
