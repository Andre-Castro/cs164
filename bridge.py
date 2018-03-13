import socket
import sys
from thread import *
import commands
from uuid import getnode as get_mac
import time


#Notes
#-----
#open three sockets (X)
#send BPDU's to each socket
#BPDU = {switch priority, Mac ID, Bride ID}
  #Bridge ID is the concatenation of switch priority and Mac ID

#mac_addr = commands.getoutput("/sbin/ifconfig | grep -i \"HWaddr\"| awk '{print $5}'")
mac_addr = get_mac()
bridge_id = '32767.' + str(mac_addr)
BPDU = (bridge_id, 0 , bridge_id)
min_priority = 32768
#print BPDU

#ip = socket.gethostbyname(socket.gethostname()) 
ip = commands.getoutput("/sbin/ifconfig | grep -i \"inet\" | awk '{print $2}'")
ip = ip.split()
ip = ip[0].split(':')
ip = ip[1]
#print ip

send_dict = {"10.0.0.1": [("10.0.0.3", 8001),("10.0.0.4", 8002),("10.0.0.2", 8003)],
             "10.0.0.2": [("10.0.0.1", 8003),("10.0.0.3", 8002),("10.0.0.4", 8001)],
             "10.0.0.3": [("10.0.0.1", 8001),("10.0.0.2", 8002),("10.0.0.4", 8003)],
             "10.0.0.4": [("10.0.0.2", 8001),("10.0.0.1", 8002),("10.0.0.3", 8003)] }

ip_port_list = [("10.0.0.1", 8000),
                ("10.0.0.2", 8001),
                ("10.0.0.3", 8002),
                ("10.0.0.4", 8003) ]

mac_to_ip_dict = {6716419370808   : "10.0.0.1",
                  214307709092800 : "10.0.0.2",
                  248895691125258 : "10.0.0.3",
                  16017090074789  : "10.0.0.4" }

ip_to_mac_dict = {"10.0.0.1" : 6716419370808,                  
                  "10.0.0.2" : 214307709092800,
                  "10.0.0.3" : 248895691125258,
                  "10.0.0.4" : 16017090074789 }

for pair in ip_port_list:
    if pair[0] == ip:
        ip_port_list.remove(pair)

#print ip_port_list

root = True
 
status_tbl = [ ['', 8001, ''],
               ['', 8002, ''],
               ['', 8003, ''], ]
print "Initial: " , status_tbl



def clientthread(conn):
    print "Entering client thread"
    #Sending message to connected client from this server
    conn.send('Welcome to the server. Type something and hit enter\n')
    #infinite loop so that the fuction does not terminate and the thread does not end.
    global root
    while True:
        #Receiving data from clent
        data = conn.recv(1024)
        if len(data) == 0:
            print "Recv'd empty data?"
            print "Exiting..."
            sys.exit()
        dataList = data.strip('(),\"').split() #remove bogus characters, kinda not working completely
        print dataList
        #priority = int((dataList[2].split('.'))[0].strip('\'\"'))
        #print "Priority: " + priority
        sender_mac = int((dataList[2].split('.'))[1].strip('\'\"'))
        #print sender_mac 
       
        #print(sender_mac, mac_addr)
        if sender_mac < int(mac_addr): #sendermac is root?
            print "potential root is sending"
            root = False
            distance = int(dataList[1].strip('\'\",')) + 1
            
            #print "Now we have to forward BDPU dataList to all things marked as dp on table
            
            #first were gonna get the sender info
            sender_ip = mac_to_ip_dict[sender_mac]
            sender_port = 0
            for pairs in send_dict[ip]:
                if sender_ip == pairs[0]:
                    sender_port = pairs[1]
            print "Sender is:" , sender_ip, sender_port
            #we now know who sender is, lets mark them as root for now
            
            BPDU = (dataList[2], distance, bridge_id)#new BPDU
           
            for trip in status_tbl: #iterate through table and send to DP's
                if trip[2] == '' and trip[1] == sender_port: #if its empty and its root port
                    trip[2] = 'RP' #identify it as root port
                    trip[0] = sender_mac #give it the correct mac    
                
                elif trip[2] == '' and trip[1] != sender_port: #empty but NOT root
                    print "I am DP or BP"                
        

        #fix me: change it so that everyone gets out at least one BPDU first
        # this way the table can be filled up for root to.
        # also ip-to-mac is prob cheating lololol

     
        elif sender_mac > int(mac_addr):
            print "we could possibly be root..."
            for trip in status_tbl: #we are root, make everything DP
                trip[2] = 'DP' #set to designated port
                
                sender_ip = 0
                for pairs in send_dict[ip]: #figure out which ports belong to which ip
                     if pair[1] == trip[0]:
                        sender_ip = pair[0]
                trip[0] = ip_to_mac_dict[sender_ip]
            
            print "Complete:", status_tbl
                
        conn.close()
        sys.exit() 
    return

def listen_thread(s, host, port):
    try:
        #print host + ":" + str(port)
        s.bind((host, port))
    except socket.error, msg:
        print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message: ' + msg[1]
        sys.exit()
 
    s.listen(10)
    #print "sucessfully bound"

    while 1:
        #wait to accept a connection
        conn, addr = s.accept()
        print 'Connected with ' + addr[0] + ':' + str(addr[1])

        #starts new thread takes 1st arg as a function name to be run
        #second is the tuple of arguments to the function.
        start_new_thread(clientthread, (conn,))

#listening sockets        
s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s3.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

start_new_thread(listen_thread, (s1, ip, 8001))
start_new_thread(listen_thread, (s2, ip, 8002))
start_new_thread(listen_thread, (s3, ip, 8003))

#Need to brodcast root version of BPDU since everyone does that at first
#


def send_message(s):
    #we only send messages if we are root.
    print "Root?: ", root
    if root:
        #send 3 messages to designated ports 
        print "Tyring to connect to " + send_dict[ip][0][0] + ":" + str(send_dict[ip][0][1]) 
        s.connect((send_dict[ip][0][0], send_dict[ip][0][1])) #connect to approprite port
        s.sendall(str(BPDU)) #send BDPU
        s.close() #close port (?)   
        #re-open socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
         
        print "Tyring to connect to " + send_dict[ip][1][0] + ":" + str(send_dict[ip][1][1]) 
        s.connect((send_dict[ip][1][0], send_dict[ip][1][1])) #connect to approprite port
        s.sendall(str(BPDU)) #send BDPU
        s.close() #close port (?)   
        #re-open socket 
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
         
        print "Tyring to connect to " + send_dict[ip][2][0] + ":" + str(send_dict[ip][2][1]) 
        s.connect((send_dict[ip][2][0], send_dict[ip][2][1])) #connect to approprite port
        s.sendall(str(BPDU)) #send BDPU
        s.close() #close port (?)   
        #re-open socket 
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        time.sleep(5) #wait 5 seconds to check if we are root again 
        start_new_thread(send_message, (s,)) #create new thread, try to send_message again.
    else:
        sys.exit() # if we are not root, we do not send. Kill the thread.
    
    #keeps useless threads alive so child threads can still run
    while 1:
        i = 0

#set up sending port
s4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s4.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

time.sleep(4)# wait for user to start all four hosts

#send message assuming you are root port
start_new_thread(send_message, (s4,))

while 1: #keeps main thread alive -_-
    time.sleep(500)
#eof
