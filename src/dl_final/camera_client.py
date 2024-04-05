import cv2
import pickle
import struct
import threading
import socket
import numpy as np

class StreamingClient:
    def __init__(self, host, port):

        self.__host = host
        self.__port = port
        self._configure()
        self.__running = False
        self.__client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.disconnect_count = 0

    def _configure(self):

        self.__encoding_parameters = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

    def _get_frame(self):

        return None

    def _cleanup(self):

        cv2.destroyAllWindows()

    def __client_streaming(self):
        self.__client_socket.connect((self.__host, self.__port))
        while self.__running:
            frame = self._get_frame()
            try :
                result, frame = cv2.imencode('.jpg', frame, self.__encoding_parameters)
                data = pickle.dumps(frame, 0)
                size = len(data)
                self.disconnect_count = 0
            except :
                self.disconnect_count += 1
                print(f"Disconnect : {self.disconnect_count}...")
                continue
            try:
                self.__client_socket.sendall(struct.pack('>L', size) + data)
            except ConnectionResetError:
                self.__running = False
            except ConnectionAbortedError:
                self.__running = False
            except BrokenPipeError:
                self.__running = False

        self._cleanup()

    def start_stream(self):
        """
        Starts client stream if it is not already running.
        """

        if self.__running:
            print("Client is already streaming!")
        else:
            self.__running = True
            client_thread = threading.Thread(target=self.__client_streaming)
            client_thread.start()

    def stop_stream(self):
        """
        Stops client stream if running
        """
        if self.__running:
            self.__running = False
        else:
            print("Client not streaming!")


class CameraClient(StreamingClient):
    def __init__(self, host, port, x_res=1024, y_res=576):
        
        self.condition = ''
        self.fgbg = cv2.createBackgroundSubtractorMOG2()
        self.frame_mutex = threading.Lock()  # 프레임에 대한 뮤텍스

        self.__x_res = x_res
        self.__y_res = y_res
        self.__camera = cv2.VideoCapture(0)
        super(CameraClient, self).__init__(host, port)

    def _configure(self):

        self.__camera.set(3, self.__x_res)
        self.__camera.set(4, self.__y_res)
        super(CameraClient, self)._configure()

    def _get_frame(self):
       
        def apply_filter(condition):
            if condition == 'canny':
                ret, frame = self.__camera.read()
                image = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                edges = cv2.Canny(image, 150, 100)
                frame = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
            elif condition == 'gray':
                ret, frame = self.__camera.read()
                image = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                frame = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            elif condition == 'removebg':
                ret, frame = self.__camera.read()
                frame = self.fgbg.apply(frame)
            elif condition == 'blur':
                ret, frame = self.__camera.read()
                image = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                blurred = cv2.GaussianBlur(image, (9, 9), 0)
                frame = cv2.cvtColor(blurred, cv2.COLOR_GRAY2RGB)
            elif condition == 'concave':
                ret, frame = self.__camera.read()
                rows, cols = frame.shape[:2]
                exp = 0.5
                scale = 1
                mapy, mapx = np.indices((rows, cols),dtype=np.float32)
                mapx = 2*mapx/(cols-1)-1
                mapy = 2*mapy/(rows-1)-1
                r, theta = cv2.cartToPolar(mapx, mapy)
                r[r< scale] = r[r<scale] **exp
                mapx, mapy = cv2.polarToCart(r, theta)
                mapx = ((mapx + 1)*cols-1)/2
                mapy = ((mapy + 1)*rows-1)/2
                frame = cv2.remap(frame,mapx,mapy,cv2.INTER_LINEAR)
            elif condition == 'cartoon':
                ret, frame = self.__camera.read()
                h, w = frame.shape[:2]
                img2 = cv2.resize(frame, (w//2, h//2))
                blr = cv2.bilateralFilter(img2, -1, 20, 7)
                edge = 255 - cv2.Canny(img2, 80, 120)
                edge = cv2.cvtColor(edge, cv2.COLOR_GRAY2BGR)
                dst = cv2.bitwise_and(blr, edge)
                frame = cv2.resize(dst, (w, h), interpolation=cv2.INTER_NEAREST)
            else:
                ret, frame = self.__camera.read()
            return frame
        
        if self.condition:
            with self.frame_mutex:
                return apply_filter(self.condition)
        else:
            ret, frame = self.__camera.read()
            return frame

    def _cleanup(self):

        self.__camera.release()
        cv2.destroyAllWindows()