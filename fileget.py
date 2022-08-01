#!/usr/bin/env python3
import sys
import getopt
import socket
import os
import re

def arg_control():
    # fileget.py -n NAMESERVER -f SURL -> 5 argumentov
    n_checked = False
    f_checked = False

    if(len(sys.argv) != 5):
        sys.exit("Wrong number of parameters!")
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "n:f:")
    except:
        sys.exit("Wrong type of parameter")

    for opt, arg in opts:
        if opt in ['-n']:
            nameserver = arg
            n_checked = True
        elif opt in ['-f']:
            surl = arg
            f_checked = True
        else:
            sys.exit("Wrong arguments else")

    if(n_checked and f_checked):
        return nameserver, surl
    else:
        sys.exit("Missing -n or -f")

def udp_request(nameserver, surl):
    UDP_IP = nameserver[0]
    UDP_PORT = int(nameserver[1])
    MESSAGE = "WHEREIS " + surl[0]
    MESSAGE = bytes(MESSAGE, 'utf-8')

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
        data, addr = sock.recvfrom(1024)
        sock.close()
    except:
        sys.exit("ERROR: Problem with socket in UDP request")

    data = data.decode('utf-8')
    return data
    
def tcp_request(data, surl):
    ip_adress = data.split(":")
    if(len(ip_adress) != 2):
        sys.exit("Wrong ip_adress format returned from nameserver -> must be in ip:port")
    TCP_IP = ip_adress[0]
    TCP_PORT = int(ip_adress[1])
    MESSAGE = "GET " + surl[1] + " FSP/1.0\r\nHostname: " + surl[0] + "\r\nAgent: xzauko00\r\n\r\n"
    if(surl[1] == '*'):
        MESSAGE = "GET " + 'index' + " FSP/1.0\r\nHostname: " + surl[0] + "\r\nAgent: xzauko00\r\n\r\n"
    
    MESSAGE = bytes(MESSAGE, 'utf-8')

    # creating socket connection -> first one is here cause yet i dont know if i am downloading all
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((TCP_IP, TCP_PORT))
        sock.settimeout(10)
        sock.send(MESSAGE)
        received = b''
        while True:
            part = sock.recv(2048)
            received += part
            if part == b'':
                break
        sock.close()
    except:
        sys.exit("ERROR: Problem with socket in TCP request - first file")
    
    # first case - i download only one file
    if(surl[1] != '*'):
        # for writing the file
        received = received.split(b'\r\n\r\n',1)
        header = received[0].decode()
        if(header[8:15] != 'Success'):
            sys.exit("Wrong header in downloading file")
        write_file(surl[1], received[1])
    else:
        # if i am downloading all : 
        received = received.split(b'\r\n\r\n',1)
        header = received[0].decode()
        if(header[8:15] != 'Success'):
            sys.exit("Wrong header in index file")
        index = received[1].decode()
        index = index.split("\r\n")
        
        for file in index:
            if(file == ''):
                continue
            mess = "GET " + file + " FSP/1.0\r\nHostname: " + surl[0] + "\r\nAgent: xzauko00\r\n\r\n"
            mess = bytes(mess, 'utf-8')

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((TCP_IP, TCP_PORT))
                sock.settimeout(10)
                sock.send(mess)
                received = b''
                while True:
                    part = sock.recv(2048)
                    received += part
                    if part == b'':
                        break
                sock.close()
            except:
                sys.exit("ERROR SOCKET")

            received = received.split(b'\r\n\r\n',1)
            header = received[0].decode()
            if(header[8:15] != 'Success'):
                print("Could not download file: " + file )
                continue
            write_file(file, received[1])
            
    

def write_file(path, content):
    # if we have file with name that already exists i make a unique name for it
    created_file = path.split('/')
    i = 1
    name = created_file[len(created_file)-1]
    
    if(os.path.exists(name)):
        name = "(" + str(i) + ")" + created_file[len(created_file)-1]
        while(os.path.exists(name)):
            i += 1
            name = "(" + str(i) + ")" + created_file[len(created_file)-1]
    try:
        f = open(name, 'wb')
        f.write(content)
        f.close()
    except:
        sys.exit("There wasa problem with creating, writing or closing file")
    
def main():
    # arg control returns nameserver and surl
    nameserver, surl = arg_control()

    # check if nameserver is in good format -> ipadadress:port ->separated by :
    nameserver = nameserver.split(":")
    if(len(nameserver) != 2):
        sys.exit("Wrong nameserver format -> ip_adress:port")

    # checking protocol: fps:// 
    protocol = surl[0:6]
    if(protocol != 'fsp://'):
        sys.exit("Wrong surl - must be in format: PROTOCOL://SERVER_NAME/PATH")

    # removing fps:// part and splitting with / separator ... maxsplit = 1, cause i need
    # SERVER_NAME and PATH
    surl = surl[6:]
    surl = surl.split("/",1)
    if(len(surl) != 2):
        sys.exit("Wrong surl - must be in format: PROTOCOL://SERVER_NAME/PATH")

    # regex checker for name of file server
    if surl[0] is None or not re.match('^(_|-|\.|[a-zA-Z0-9])*$', surl[0]):
        sys.exit("Wrong server name, must contain only alnums, -, _ and .")
    
    # calling function for udp_request -> returning ip of file system
    data = udp_request(nameserver, surl)
    data = data.split(' ',1)
    if(data[0] != 'OK'):
        sys.exit("Nameserver returned ERR")
    
    # calling function for tcp_request -> and last called function from main
    # txp_request takes care also for creating files -> calling func
    tcp_request(data[1], surl)
        

if __name__ == "__main__":
    main()
    