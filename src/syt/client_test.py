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
    TCP_IP = '192.168.0.15'  # 서버의 IP 주소
    TCP_PORT = 3001

    sock = socket.socket()
    sock.connect((TCP_IP, TCP_PORT))

    cap = cv2.VideoCapture(0)  # 자신의 웹캠을 사용하여 영상을 캡처합니다.

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_string = cv2.imencode('.jpg', frame)[1].tostring()
        size = len(frame_string)
        sock.sendall(str(size).ljust(16).encode())
        sock.sendall(frame_string)

        length = int(sock.recv(16).strip())
        print("Receiving frame of size:", length)
        
        frame_string = recvall(sock, length)
        
        frame_array = np.frombuffer(frame_string, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        cv2.imshow('CLIENT', frame)
        
        if cv2.waitKey(1) & 0xFF == 27:
            break

    sock.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()