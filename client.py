import socket
from threading import Thread
import random
from utils import Engine
import json


class SocketQueue:
    def __init__(self, reader: socket.socket, size: int):
        self.__reader : socket.socket = reader
        Thread(target=self.recv, args=(size,), daemon=True).start()

    def recv(self, size):
        while True:
            try:
                byte = self.__reader.recv(size).decode()
                msg  = self.__reader.recv(int(byte, 2)).decode()
                print(msg)
            except:
                continue


class Client:
    def __init__(self):
        self.SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socketReader: SocketQueue = ...

    def connect(self, host, port):
        self.SOCKET.connect((host, port))
        self.__socketReader = SocketQueue(self.SOCKET, 11)

    def send(self, *args):
        try:
            command = ''.join([str(i) for i in args])

            typeObj    = str(bin(len(args[0])))[2:].zfill(4)
            obj        = str(bin(len(args[1])))[2:].zfill(4)
            data       = str(bin(len(args[2])))[2:].zfill(11)

            self.SOCKET.send(str(typeObj + obj + data).encode('utf-8'))
            self.SOCKET.send(command.encode('utf-8'))
        except:
            pass


class EngineClient(Client):
    def __init__(self):
        super().__init__()
        self.obj = None

    def connect(self, host, port):
        self.SOCKET.connect((host, port))

    def __receive(self):
        try:
            byte = self.SOCKET.recv(11).decode()
            msg  = self.SOCKET.recv(int(byte, 2)).decode()
            return msg if msg else None
        except:
            return None

    def __send(self, msg):
        return self.send('user', self.obj, msg)

    def interact(self):
        obj = ''.join([chr(random.randint(64, 64+25)) for _ in range(6)])
        self.send('engine', obj, '')
        self.obj = obj        
        engine = Engine(r'Engine\engine.exe', self.__send)        
        
        while True:
            msg = self.__receive()
            print('->', msg)
            if msg is not None:
                engine.send(msg)


class UserClient(Client):
    def interact(self):
        data = json.load(open('config.json', 'r'))
        obj     = ''.join([chr(random.randint(64, 64+25)) for _ in range(6)])
        self.send('user', obj, '')
        self.send('user', obj, 'connect')
        # Set OBJ key
        obj = data['key']
        self.send('engine', obj, '')
        while True:
            message = input('')
            self.send('engine', obj, message)


def main():
    data = json.load(open('config.json', 'r'))

    clientType = UserClient() if data['typeObj'] == 'user' else EngineClient()
    clientType.connect(data['host'], data['port'])
    clientType.interact()


if __name__ == '__main__':
    main()
