import subprocess
from threading import Thread


class StdoutReader:
    """
    stdout -> string
    Read output from engine
    Output include 2 types:
        - Message (start with MESSAGE ...)
        - No prefix (ex: "OK", ...)
        - Coord ("7,7", ...)
    """
    def __init__(self, stream, stdout):
        self.__stream = stream
        self.__stdout = stdout
        self.__thread = Thread(target=self.__populateQueue)
        self.__thread.daemon = True
        self.__thread.start()

    def __populateQueue(self):
        while True:
            line = self.__stream.readline().strip()
            if line == '':
                continue
            elif line is None:
                break
            else:
                print('OUT:', line)
                self.__stdout(line)


# noinspection PyUnresolvedReferences
class Engine:
    def __init__(self, path, stdout):
        self.__engine = subprocess.Popen(path, stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         bufsize=1, universal_newlines=True)
        self.__stdoutReader = StdoutReader(self.__engine.stdout, stdout)

    def send(self, *command):
        """Send input to engine"""
        new_command = []
        for i in range(len(command)):
            if i == 0:
                new_command.append(str(command[i]).upper())
            else:
                new_command.append(str(command[i]))
        command = ' '.join(new_command)
        self.__engine.stdin.write(command + '\n')
