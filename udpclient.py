import socket
import time
import argparse
import struct
import random
import statistics

#接收命令行输入
parser = argparse.ArgumentParser(description="UDP Client")
parser.add_argument("server_ip", type=str, help="Server IP")
parser.add_argument("server_port", type=int, help="Server port")
args = parser.parse_args()

SERVER_IP = args.server_ip
SERVER_PORT = args.server_port
TIMEOUT = 0.1  # 100ms
MAX_RETRIES = 2
VERSION = 2
STUDENT_ID = "221002606张宸玮"
BIRTHDAY = "04-03-11"

received_packets=0
total_packets=0
RTTS=[]#存放所有RTT
first_server_time=None#记录第一次response的系统时间
last_server_time=None#记录最后一次response的系统时间

# 创建UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(TIMEOUT)

server_address = (SERVER_IP, SERVER_PORT)

def get_current_time():
    return time.strftime('%H-%M-%S')

def create_packet(seq_no, ver, student_id, birthday_time,attempts): 
    # client->server报文格式规定为2字节序号，1字节版本号，18字节学号，8字节本人的生日，1字节当前序号的报文的已发送次数，剩下所有存放随机数字（共计203字节）
    # 序号和版本号
    seq_no_bytes = struct.pack('!H', seq_no)
    ver_bytes = struct.pack('!B', ver)

    # 学号（18 bytes）
    student_id_bytes = student_id.encode('utf-8')
    student_id_bytes = student_id_bytes[:18]
    student_id_bytes = student_id_bytes.ljust(18, b'\x00') 

    # 生日（8 bytes）
    birthday_bytes = birthday_time.encode('utf-8')
    birthday_bytes = birthday_bytes[:8]
    birthday_bytes = birthday_bytes.ljust(8, b'\x00')

    #当前序号的报文的已发送次数（1 bytes）
    send_attempts=struct.pack('!B',attempts)

    # 剩余均为随机数字
    random_bytes = ''.join(random.choices('0123456789', k=173)).encode('utf-8')

    # 拼接所有部分
    packet = seq_no_bytes + ver_bytes + student_id_bytes + birthday_bytes + send_attempts+random_bytes
    return packet

def parse_packet(packet):#解析报文信息
    seq_no = struct.unpack('!H', packet[:2])[0]
    ver = struct.unpack('!B', packet[2:3])[0]
    student_id = packet[3:21].decode('utf-8').strip('\x00')
    system_time = packet[21:29].decode('utf-8').strip('\x00')
    random_bytes = packet[29:].decode('utf-8')
    return seq_no, ver, student_id, system_time, random_bytes


sock.sendto("SYN".encode(), server_address)#发送SYN给server
data, server = sock.recvfrom(2048)
if data.decode() == "SYN-ACK":#接收SYN-ACK
  sock.sendto("ACK".encode(), server_address)
  print("成功与服务器建立连接！\n")
# 成功建立连接，客户端向服务器连续发送12个client报文
  for i in range(1, 13):
    attempts = 1
    while attempts <= MAX_RETRIES+1:#当重传不超过两次时
        current_time = get_current_time()
        message = create_packet(i, VERSION, STUDENT_ID,BIRTHDAY,attempts)
        print(f"Sending: Seq_no={i}, Attempt: {attempts}, Time: {current_time}")
        start_time = time.perf_counter()
        sock.sendto(message, server_address)
        
        try:
            data, server = sock.recvfrom(2048)
            end_time = time.perf_counter()
            rtt = (end_time - start_time) * 1000  # 计算RTT
            seq_no, ver, student_id, server_time, random_data = parse_packet(data)
            print(f"Sequence_no={seq_no}, serverIP:{SERVER_IP},serverPort:{SERVER_PORT}, RTT: {rtt:.2f} ms, Student_ID: {student_id}, Server Time: {server_time}")#输出response报文信息
            received_packets+=1
            total_packets+=1
            RTTS.append(rtt)
            if first_server_time==None:
                first_server_time=end_time
            last_server_time=end_time
            break
        except socket.timeout:#发生丢包，重传
            print(f"Sequence_no: {i},Request {i} timed out on attempt {attempts}")
            total_packets+=1
            attempts += 1

        if attempts > MAX_RETRIES+1:#重传两次失败，停止重传
            print(f"Request {i} failed after {MAX_RETRIES} retries, giving up")
  sock.close()
#计算丢包率，RTT最大值，最小值，平均值，方差，总系统响应时间
  drop_rate=(1-received_packets/total_packets)*100
  if RTTS:
    max_rtt=max(RTTS)
    min_rtt=min(RTTS)
    ave_rtt=sum(RTTS)/len(RTTS)
    if len(RTTS)>1:
        s_rtt=statistics.stdev(RTTS)
    else:
        s_rtt=0
  else:
     max_rtt = min_rtt = ave_rtt = s_rtt = 0
 
  total_time=last_server_time-first_server_time

#针对发送的12个报文输出汇总信息
  print(f"\n【汇总信息】")
  print(f"1. 接收到的 UDP packets 数目: {received_packets}")
  print(f"2. 丢包率: {drop_rate:.2f}%")
  print(f"3. 最大 RTT: {max_rtt:.2f} ms, 最小 RTT: {min_rtt:.2f} ms, 平均 RTT: {ave_rtt:.2f} ms, RTT 标准差: {s_rtt:.2f} ms")
  print(f"4. Server 的整体响应时间: {total_time:.4f} 秒")

else:
    print("建立连接失败！")
    sock.close()