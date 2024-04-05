import socket
import pyaudio
import threading

# PyAudio 설정
audio = pyaudio.PyAudio()
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

# 서버 설정
HOST = '192.168.0.31'  # 서버의 IP 주소
PORT = 5002

# 서버 소켓 생성
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print("Waiting for a connection...")

# 클라이언트 연결 수락
client_socket, addr = server_socket.accept()
print("Connected from:", addr)

# 오디오 스트림 열기
input_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
output_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

# 오디오 수신 및 재생을 위한 함수
def receive_and_play():
    try:
        while True:
            # 클라이언트로부터 오디오 데이터 수신
            data = client_socket.recv(CHUNK)
            if not data:
                break
            # 오디오 데이터 재생
            output_stream.write(data)
    except KeyboardInterrupt:
        pass

# 오디오 수신 및 재생을 위한 스레드 시작
receive_thread = threading.Thread(target=receive_and_play)
receive_thread.start()

try:
    while True:
        # 내 마이크에서 오디오 데이터 읽기
        data = input_stream.read(CHUNK)
        # 클라이언트로 오디오 데이터 보내기
        client_socket.sendall(data)
except KeyboardInterrupt:
    pass
finally:
    # 연결 종료
    client_socket.close()
    server_socket.close()
    input_stream.stop_stream()
    input_stream.close()
    output_stream.stop_stream()
    output_stream.close()
    audio.terminate()