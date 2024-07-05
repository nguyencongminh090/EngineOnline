#include <iostream>
#include <random>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <fstream>
#include <bitset>
#include <thread>
#include <atomic>
#include "json.hpp"
#include <boost/dynamic_bitset.hpp>

using namespace std;
using json = nlohmann::json;


class Client {
    private:
        const char* host;
        int port;
        atomic<bool> state = true;
        string clientID;
        string engineID;
        SOCKET clientSocket;
        sockaddr_in clientService;

        char* intToBin(int num, int k) {
            boost::dynamic_bitset<uint8_t> out(k, num);
            string n;
            char* array = new char[k + 1];
            for (int i=0; i < k; i++) {
                n += to_string(out[k-i-1]);
            }
            strcpy(array, n.c_str());
            array[k] = '\0';
            return array;
        }

        string randomObjKey(int length) {
            string output;
            random_device rd;
            uniform_int_distribution<char> dist(65, 65 + 24);
            for (int i; i < length; i++) {
                output += dist(rd);
            }
            return output;
        }

        string lowercase(string str) {
            string output;
            for (int i = 0; i < str.length(); i++) {
                output += tolower(str[i]);
            }
            return output;
        }

        void receive(int size) {
            while (this->state) {
                try {
                    char* byte = new char[size + 1];
                    byte[size] = '\0';
                    recv(this->clientSocket, byte, size, 0);                    

                    int dataLen = stoi(byte, nullptr, 2);

                    char* data = new char[dataLen + 1];
                    data[dataLen] = '\0';
                    recv(this->clientSocket, data, dataLen, 0);

                    if ((string)data == "quit") {
                        this->state.store(false);
                        break;
                    }                   

                    cout << data << endl;  

                    delete[] byte;
                    delete[] data;             
                }
                catch (const exception &exc) {
                    cout << exc.what() << endl;
                }
            }
        }

    public:
        Client() {
            // Implement Socket
            WSADATA wsaData;
            int wserr;
            WORD wVersionRequested = MAKEWORD(2,2);
            wserr = WSAStartup(wVersionRequested, &wsaData);
            
            // Setup socket
            this->clientSocket = INVALID_SOCKET;
            this->clientSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);           
            this->clientService.sin_family = AF_INET;            

            // Setup client-server info
            // this->clientID;
        }

        void connectServer(const char* host, int port, string eid="") {
            this->host = host;
            this->port = port;

            this->engineID = eid;

            this->clientService.sin_addr.s_addr = inet_addr(host);
            this->clientService.sin_port = htons(port);
            if (connect(this->clientSocket, (SOCKADDR*)&clientService, sizeof(clientService))) {
                cout << "Client: connect() - Failed to connect: " << WSAGetLastError() << endl;
                WSACleanup();
            }
        }

        void sendData(string typeObj, string obj, string data) {
            char* _typeObj  = this->intToBin(typeObj.length(), 4);
            char* _obj      = this->intToBin(obj.length(), 4);
            char* _dataBuff = this->intToBin(data.length(), 11);

            int lenData = typeObj.length() + obj.length() + data.length();

            char* byteData = new char[20];
            memcpy(byteData, _typeObj, 4);
            memcpy(byteData + 4, _obj, 4);
            memcpy(byteData + 8, _dataBuff, 11);


            char* _data = new char[lenData + 1];
            memcpy(_data                   , typeObj.c_str(), typeObj.length());
            memcpy(_data + typeObj.length(), obj.c_str()    , obj.length());
            memcpy(_data + obj.length() + typeObj.length()  , data.c_str()   , data.length());

            byteData[19]   = '\0';
            _data[lenData] = '\0';

            send(this->clientSocket, byteData, 19, 0);
            send(this->clientSocket, _data, lenData, 0);

            delete[] byteData;
            delete[] _data;
            delete[] _typeObj;
            delete[] _obj;
            delete[] _dataBuff;             
        }

        void interact() {
            string message;
            string obj = this->randomObjKey(6);            

            thread Thread(&Client::receive, this, 11);

            this->sendData("user", obj, "");
            this->sendData("user", obj, "connect");
            this->sendData("engine", this->engineID, "");

            cout << "MESSAGE SESSION: " << obj << endl;
            while (this->state) {
                getline(cin, message);               
                this->sendData("engine", this->engineID, message);
                if (message == "end" || message == "END") {
                    this->state.store(false);
                    break;
                }
            }     
            Thread.join();
            closesocket(this->clientSocket);
        }

};

int main() {
    Client client;
    ifstream f("config.json");
    json data = json::parse(f);

    const char* host = string(data["host"]).data();

    client.connectServer(host, data["port"], data["key"]);
    cout << "MESSAGE CONNECTED TO ENGINE" << endl; 
    client.interact();
    return 0;
}