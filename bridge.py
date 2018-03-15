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
bridge_id = '32768.' + str(mac_addr)
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

for pair in ip_port_list:
    if pair[0] == ip:
        ip_port_list.remove(pair)

#print ip_port_list

root = True
min_mac = int(mac_addr)
curr_distance = 0 #to root
 
status_tbl = [ ['', 8001, ''],
               ['', 8002, ''],
               ['', 8003, ''], ]

print "Initial: "
for row in status_tbl:
    print row
print ''

def clientthread(conn, addr):
    #print "Entering client thread"
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
        print "Recieved:", dataList
        #priority = int((dataList[2].split('.'))[0].strip('\'\"'))
        #print "Priority: " + priority
        sender_root_mac = int((dataList[0].split('.'))[1].strip(',\'\"'))
        sender_mac = int((dataList[2].split('.'))[1].strip('\'\"'))
        #print sender_mac
 
        sender_ip = addr[0]
        sender_port = 0
        for pairs in send_dict[ip]: #figure out which ports belong to which ip
            if pairs[0] == sender_ip:
                sender_port = pairs[1]
        print "Sender: ", sender_ip, sender_port

        global min_mac
        if sender_mac < min_mac:
            min_mac = sender_mac 
            root = False

        curr_root_mac = 0
        for row in status_tbl:
            if row[2] == 'RP':
                curr_root_mac = row[0]
        if curr_root_mac == 0:
            curr_root_mac = mac_addr
        
        for triple in status_tbl: #iterate through table and set mac's
            if triple[0] == '' and triple[1] == sender_port: #if its empty and its the sender port
                triple[0] = sender_mac #give it the correct mac    
                #print "------JUST SET MAC FOR", sender_port, "TO", sender_mac             
        
        if root: #if we are root
            print "I think I might be root..."
            for row in status_tbl: #set curr port status to 'DP'
                #if row[0] == sender_mac:
                row[2] = 'DP'

#only thing i need now is to change bp when the distance is greater


 
        global curr_distance 
        #else if we are not root and original BPDU has already gone out
        if not root: 
            print "I am for sure not root."
            #first check to see if what sender thinks is root port matches our root port        
            if sender_root_mac < curr_root_mac:
                for row in status_tbl:#set status for that port to RP
                    if row[1] == sender_port:
                        row[2] = 'RP'
                    if row[2] == 'RP'and row[1] != sender_port: #change old rp to dp
                        row[2] = 'DP'
                #Forward BDPU to all DP's
                rootID = '32768.' + str(curr_root_mac)
                distance = int(dataList[1].strip('\'\",')) + 1
                bID = '32768.' + str(mac_addr)
                BPDU = (rootID, distance, bID)
                for row in status_tbl:
                    if row[2] == 'DP':
                        send_ip = 0
                        for pair in send_dict[ip]:
                            if pair[1] == row[1]:
                                send_ip = pair[0]
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        print "Tyring to forward to " + send_ip  + ":" + str(row[1])
                        s.connect((send_ip, row[1])) #connect to approprite port
                        s.sendall(str(BPDU)) #send BDPU
                        s.close() #close port (?)  

            elif sender_root_mac == curr_root_mac: #we agree on who root is
                #compare distances 
                #if distance is = do nothing
                if int(dataList[1][:-1]) > curr_distance:
                    for row in status_tbl:#block that port
                        if row[0] == sender_mac:
                            row[2] = 'BP'     
                #check if distance is less then our current distance to root
                #print "---", dataList[1], "<", curr_distance, "=", dataList[1] < curr_distance, "----"
                if int(dataList[1][:-1]) < curr_distance: #compare distances
                    for row in status_tbl: #if it is then we need to change current root port DP
                        if row[2] == 'RP':
                            row[2] = 'DP' 
                        if row[0] == sender_mac: #and change port data was sent on to root/.
                            row[2] = 'RP'
            #elif sender root_mac > ignore
            if int(dataList[1].strip('\'\",')) > 0 and sender_root_mac >= curr_root_mac:
                #print "----DISTANCE > 0", dataList[1], "-----"
                #print "    Sender_root_mac =", dataList[0], " curr_root_mac =", curr_root_mac
                for row in status_tbl:
                    if row[0] == sender_mac:
                        row[2] = 'BP'                

            """
            #if distances are same
            if int(dataList[1][:-1]) == int(curr_distance):
                cur_root_mac = 0
                for row in status_tbl: #get mac of current root RP
                    if row[2] == 'RP':
                        cur_root_mac = row[0]
                #print cur_root_mac
                if cur_root_mac == 0: #RP does not already exist in the table
                    for row in status_tbl:
                        if row[0] == sender_mac:
                            row[2] = 'RP'
                else:
                    root_mac = min(sender_mac, cur_root_mac) #compare mac addresses
                    non_root_mac = max(sender_mac, cur_root_mac)
                    if root_mac != non_root_mac:
                        for row in status_tbl:
                            if row[0] == root_mac: #lower mac address becomes root RP,
                                row[2] = 'RP'
                            if row[0] == non_root_mac: #other port becomes BP
                                row[2] = 'BP'

            #if distances are greater change status to block
            if int(dataList[1][:-1]) > curr_distance:
                print "In here!"
                for row in status_tbl: #then change that port status to block 
                    if row[0] == sender_mac:
                        row[2] = 'BP'
            
            distance = int(dataList[1].strip('\'\",')) + 1
                
            #print "Now we have to forward BPDU dataList to all things marked as dp on table
            BPDU = (dataList[0], distance, bridge_id)#new BPDU
           
            #send BDPU to all ports with status DP 
            for row in status_tbl:
                if row[2] == 'DP':
                    send_ip = 0
                    for pair in send_dict[ip]:
                        if pair[1] == row[1]:
                            send_ip = pair[0]
                    #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    #s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    print "Tyring to forward to " + send_ip  + ":" + str(row[1]) 
                    #s.connect((send_dict[ip][1][0], send_dict[ip][1][1])) #connect to approprite port
                    #s.sendall(str(BPDU)) #send BDPU
                    #s.close() #close port (?)   
            """
        conn.close()
        
        print "Intermediate: "
        for row in status_tbl:
            print row
        print ''
        
        sys.exit() 
    return

def listen_thread(s, host, port):
    try:
        print "Listening on", host + ":" + str(port)
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
        start_new_thread(clientthread, (conn, addr))

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
    #first send an initial three messages assuming we are root. 
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


    #if root:
    while 1:
        #we only send messages if we are root.
        print "Are we root?: ", "yes" if root else "no"
        if not root:
            #for row in status_tbl:
            #    if row[0] == min_mac:
            #        row[2] = 'RP'
            #    else:
            #        row[2] = 'BP'
            sys.exit()

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
        
        #for trip in status_tbl: #we are root, make everything DP
        #    trip[2] = 'DP' #set to designated port

        time.sleep(5) #wait 5 seconds to check if we are root again 
        #start_new_thread(send_message, (s,)) #create new thread, try to send_message again.
    #else:
        #sys.exit() # if we are not root, we do not send. Kill the thread.
    
    #keeps useless threads alive so child threads can still run
    while 1:
        i = 0

#set up sending port
s4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s4.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

#since we think we are root, set everything to DP
for row in status_tbl:
    if row[2] == '':
        row[2] = 'DP'

print "Intermediate: "
for row in status_tbl:
    print row
print ''

time.sleep(4)# wait for user to start all four hosts
  
#send message assuming you are root port
start_new_thread(send_message, (s4,))

def isTableEmpty():
    for row in status_tbl:
        for element in row:
            #print "Element: ", element
            if element == '':
                return True 
    return False

not_empty = True
while not_empty:
    time.sleep(5)
    not_empty = isTableEmpty()

print "\n**************************************"
print "Completed status table:"
for row in status_tbl:
    print row
print "**************************************"
print ''#newline


while 1: #keeps main thread alive -_-
    time.sleep(500)
#eof
