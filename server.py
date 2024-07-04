import socket
from threading import Thread
from queue import Queue, Empty


def beautijson(jsdata, idx=0, exc=()):
    for i in jsdata:
        if i in exc:
            continue
        print(f'{"   " * idx}{i} {f"-> {jsdata[i]}" if not isinstance(jsdata[i], dict) else ""}')        
        if isinstance(jsdata[i], dict):
            beautijson(jsdata[i], idx=idx+1, exc=exc)


class SocketQueue:
    def __init__(self, reader: socket.socket, size: int):
        self.__reader : socket.socket = reader
        self.stack    : Queue         = Queue()
        Thread(target=self.recv, args=(size,), daemon=True).start()

    def recv(self, size):
        while True:
            self.__reader.recv(size)

    def get(self):
        if self.stack is not Empty:
            return self.stack.get(block=True, timeout=0.1)
        return None


class Server:
    def __init__(self, host, port):
        self._host = host
        self._port = port

        self.SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.SOCKET.bind((self._host, self._port))
        self.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.SOCKET.settimeout(None)
        self.SOCKET.listen()

        self.__manageClient = ManageClient()

        Thread(target=self.acceptClientConnection, daemon=True).start()

    @staticmethod
    def sendTo(client : socket.socket, *data):
        command = ''.join([str(i) for i in data])
        byte = str(bin(len(command)))[2:].zfill(11)
        client.send(byte.encode('utf-8'))
        client.send(command.encode('utf-8'))

    def acceptClientConnection(self):
        while True:
            try:
                client, addr = self.SOCKET.accept()
                Thread(target=self.handleClientConnection, args=(client,), daemon=True).start()
            except Exception as e:
                print(f'[AcceptClientConnection Exception: {e}]')

    def handleClientConnection(self, client: socket.socket):
        def receive():
            byte = client.recv(19).decode()
            return client.recv(int(byte[:4], 2)).decode(),\
                client.recv(int(byte[4:8], 2)).decode(), \
                client.recv(int(byte[8:19], 2)).decode()
        # Setup Obj
        _typeObj, _obj, _ = receive()
        self.__manageClient.add(client, _typeObj, _obj)

        while True:
            try:
                typeObj, obj, data = receive()
                # print(f'typeObj: {typeObj} | obj: {obj} | data: {data}')
                match typeObj:
                    case 'user':
                        if data == 'connect':
                            myObj = (typeObj, obj)
                            typeObj, obj, _ = receive()
                            self.__manageClient.attach((typeObj, obj), myObj)
                            continue
                        elif self.__manageClient.get(typeObj, obj) is not None:
                            self.sendTo(self.__manageClient.get(typeObj, obj), data)

                    case 'engine':
                        if data == 'setInfo':
                            typeObj, obj, data = receive()
                            self.__manageClient.setInfo(typeObj, obj, 'hardware', data)
                            continue
                        self.sendTo(self.__manageClient.get(typeObj, obj), data)

            except Exception as e:
                print(f'[handleClientConnection: {e}]')
                client.close()
                del self.__manageClient.getClientDict()[_typeObj][_obj]
                break

    def interact(self):
        while True:
            msg = input().strip().split()
            try:
                match msg:
                    case ['show', typeObj]:
                        self.__manageClient.display(typeObj)
            except:
                continue                


class ManageClient:
    def __init__(self):
        self.__clientDict : {str : {str : socket.socket}} = {} # type: ignore

    def add(self, client: socket.socket, typeObj: str, obj):
        self.__clientDict[typeObj] = {obj: {'client'  : client,
                                           'hardware': "",
                                           'child'   : None}}

    def get(self, typeObj, obj):
        if typeObj == 'engine':
            return self.__clientDict[typeObj][obj]['client']
        elif typeObj == 'user':
            return self.__clientDict['engine'][obj]['child']

    def __getObj(self, typeObj, obj) -> dict:
        return self.__clientDict[typeObj][obj]
    
    def getClientDict(self) -> dict:
        return self.__clientDict

    def attach(self, engine: tuple, user: tuple):
        self.__getObj(engine[0], engine[1])['child'] = self.__getObj(user[0], user[1])['client']

    def setInfo(self, typeObj, obj, key, info):
        self.__getObj(typeObj, obj)[key] = info

    def display(self, typeObj='engine'):
        print('[+] Display')
        beautijson(self.__clientDict[typeObj], exc=('client', 'child'))


def main():
    host = input('Host: ')
    port = int(input('Port: ').strip())
    server = Server(host, port)
    server.interact()


if __name__ == '__main__':
    main()
    