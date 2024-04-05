from vidstream import StreamingServer, AudioReceiver, CameraClient, AudioSender
import tkinter as tk
import socket
import threading


class Server:
    def __init__(self, window, client_ip):
        self.local_ip_address = '192.168.0.15'
        print(self.local_ip_address)
        self.vid_recv_port = 5001
        self.aud_recv_port = 5002
        self.vid_send_port = 5003
        self.aud_send_port = 5004
        print(f"server ip: {self.local_ip_address}\nvid recv port:{self.vid_recv_port}, vid send port:{self.vid_send_port}\naud recv port:{self.aud_recv_port}, aud send port:{self.aud_send_port}")

        recvs = self.start_listening()

        self.client_ip = client_ip

        label_target_ip = tk.Label(window, text=f'상대 아이피: {client_ip}')
        label_target_ip.pack()

        btn_camera = tk.Button(window, text='화상 전화 시작하기',
                               width=30, command=self.start_camera_stream)
        btn_camera.pack(anchor=tk.CENTER, expand=True)

        window.protocol('WM_DELETE_WINDOW',
                        lambda: self.exit_fn(window, recvs))

    def exit_fn(self, window, recvs):
        recvs[0].stop_server()
        recvs[1].stop_server()
        window.destroy()


    # 음성 송수신
    def start_listening(self):
        stream_recv = StreamingServer(
            self.local_ip_address, self.vid_recv_port)
        audio_recv = AudioReceiver(self.local_ip_address, self.aud_recv_port)
        t1 = threading.Thread(target=stream_recv.start_server)
        t2 = threading.Thread(target=audio_recv.start_server)
        t1.daemon = True
        t2.daemon = True
        t1.start()
        t2.start()
        return [stream_recv, audio_recv]

    # 카메라 송수신
    def start_camera_stream(self):
        camera_client = CameraClient(self.client_ip, self.vid_send_port)
        t3 = threading.Thread(target=camera_client.start_stream)
        t3.daemon = True
        t3.start()

        audio_sender = AudioSender(self.client_ip, self.aud_send_port)
        t4 = threading.Thread(target=audio_sender.start_stream)
        t4.daemon = True
        t4.start()

# 
def start_video_call(client_ip):
    window = tk.Tk()
    window.title('server video call')
    window.geometry('350x100')
    Server(window, client_ip)
    window.mainloop()


if __name__ == '__main__':
    start_video_call('192.168.0.31')

