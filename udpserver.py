import socket
import random
import time
import struct

SERVER_IP = "192.168.78.134"
SERVER_PORT = 8080
DROP_RATE = 0.4  # 规定0.4的丢包率
VERSION = 2
STUDENT_ID = "221002606张宸玮"

def get_current_time():#格式化时间
    return time.strftime('%H-%M-%S')

def parse_packet(packet):#解析报文的信息，逐一返回
    seq_no = struct.unpack('!H', packet[:2])[0]
    ver = struct.unpack('!B', packet[2:3])[0]
    student_id = packet[3:21].decode('utf-8').strip('\x00')
    birthday_time = packet[21:29].decode('utf-8').strip('\x00')
    attempts=struct.unpack('!B',packet[29:30])[0]
    random_bytes = packet[30:].decode('utf-8')
    return seq_no, ver, student_id, birthday_time,attempts, random_bytes

def create_packet(seq_no, ver, student_id, system_time): 
    # server->client报文结构规定为2字节序号，1字节版本号，18字节学号，8字节系统时间，剩下所有存放随机数字（共计203字节）
    # 序号和版本号
    seq_no_bytes = struct.pack('!H', seq_no)
    ver_bytes = struct.pack('!B', ver)

    # 学号（18 bytes）
    student_id_bytes = student_id.encode('utf-8')
    student_id_bytes = student_id_bytes[:18]
    student_id_bytes = student_id_bytes.ljust(18, b'\x00') 

    # 系统时间（8 bytes）
    system_time_bytes = system_time.encode('utf-8')
    system_time_bytes = system_time_bytes[:8]
    system_time_bytes = system_time_bytes.ljust(8, b'\x00')

    # 剩余随机数字
    random_bytes = ''.join(random.choices('0123456789', k=174)).encode('utf-8')

    # 拼接所有部分
    packet = seq_no_bytes + ver_bytes + student_id_bytes + system_time_bytes + random_bytes
    return packet


# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_IP, SERVER_PORT))

print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")

while True:#持续等待接受客户端发送的报文
    data, addr = sock.recvfrom(2048)
    if data.decode() == "SYN":#接收SYN
        sock.sendto("SYN-ACK".encode(), addr)#发送SYN-ACK
        data, addr = sock.recvfrom(2048)
        if data.decode() == "ACK":#接收到ACK
              print(f"成功与客户端{addr}建立连接！\n")
              while True:
                    data, addr = sock.recvfrom(2048)                  
                    seq_no, ver, student_id, birthday, attempts,random_data = parse_packet(data)
                    print(f"Received message from {addr}: Seq_no={seq_no}, Ver={ver}, Student_ID={student_id}, Attempts={attempts}, Brthday_Time={birthday}")
                    #输出接受到的client报文信息

                    #按照丢包率随机丢失client报文
                    if random.random() < DROP_RATE:
                        print("Dropping packet")
                        if attempts==3 and seq_no==12:#最后一个client报文重传失败
                            break
                        else:
                            continue

                    #向client发送response
                    server_time = get_current_time()  
                    response = create_packet(seq_no, ver, student_id, server_time)
                    sock.sendto(response, addr)
                    print(f"Response sent: Seq_no={seq_no}, Time={server_time}")
                    if seq_no==12:
                      break
        else:
            print(f"无法与客户端{addr}建立连接")
