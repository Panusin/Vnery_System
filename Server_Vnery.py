import socket
import threading
import Queue
import PiNode
import json
import ast
import time

queue = Queue.Queue()
NUMBER_OF_THREADS = 2
JOB_NUMBER = [1, 2]
all_connections = []
all_client_tread = []
all_connections_status=[]
kinect_index = -1
HOST = ''  # Standard loopback interface address (localhost)
PORT = 60000        # Port to listen on (non-privileged ports are > 1023)

kinect_conn = None
backend_conn = None
client_response = None
kinect_on = False
count_client = 0
back_end_response = ''
parsed_data = None
count_pi = 0
check_pi = -1
current_souce = None
def create_socket():
    try:
        global host
        global port
        global s
        host = HOST
        port = PORT
        s = socket.socket()
    except Exception as ex:
        print("Error Socket creating :", ex)

def listen_conection(number_listen = 10):
    #default incoming-number_listen is up to 8
    try:
        global host
        global port
        global s
        host = HOST
        port = PORT
        s.bind((host, port))
        print("Sever is listening on \nport: "+ str(port))
        s.listen(number_listen)

    except socket.error as er:
        print("Error Socket_listening  : " + str(er) + '\n' + ' retrying listening')
        listen_conection(number_listen)



def accept_connection():
    global all_connections
    global all_client_tread
    try:
        for c in all_connections:
            c.close()
        del all_connections[:]
        del all_client_tread[:]
    except:
        print('Error excepting_connection cleaning up storage')

    while True:
        try:
            conn, address = s.accept()
            #s.setblocking(1) #prevent timeout

            #authorize incoming client(s) first

            #use thread to call on_client(client)
            try:
                t = threading.Thread(target= on_client, args = (conn,address))
                t.daemon = True
                t.start()
            except Exception as ex:
                print('Error creating client thread', ex)
                #all_client_tread.append(t)
        except Exception as ex:
            print('Error accepting connection with --> ', ex)

def authorize_connection(client):
    global kinect_conn
    global backend_conn
    global count_client
    global count_pi
    authorize = False
    try:  # ask connection to authorize itself first.
        conn = client.get_connection()
        address = client.get_address()
        print('Ask for authentication : Who?')
        conn.send(str.encode('who?'))
        data = conn.recv(2048)
        data = data.decode("utf-8")
        print('authorize received data:', data)
        if data == 'kinect':
            count_client += 1
            client.set_name(str(data))
            print("Connect with " + str(client.get_name()) + ' --> ' + str(address))
            kinect_conn = conn
            authorize = True, client
        elif data == 'raspberry Pi':
            count_client += 1
            count_pi += 1
            client.set_name(str(data))
            conn.send(str.encode('name:' + str(client.get_name())))
            print("Connect with " + str(client.get_name()) + ' --> ' + str(address))
            authorize = True, client
        elif data == 'back-end':
            count_client += 1
            client.set_name(str(data))
            print("Connect [back-end] with:" + ' --> ' + str(address) + str(client.get_name()))
            backend_conn = conn
            authorize = True, client
        else:
            print('Unknown devices trying to connect...\n' + 'connection unaccepted')
            client.set_name('Unknown devices')
        return authorize, client

    except Exception as ex:
        print('Error in authorize_connection and can not authorize', ex)


def send_command_one(conn, message):
    try:
        conn.send(str.encode(message))
        print('Send ', message)
    except Exception as ex:
        print("Error sending commands", ex)


def send_command_all(message):#uses to send mess to all Pi(s) except Kinect
    try:
        for i, client in enumerate(all_connections):
            conn = client.get_connection()
            if conn is not None:
                conn.send(str.encode(message))
        print('Done sending mes to all connection')
    except:
        print("Error sending commands to all clients")

def send_command_all_except_one(conn_except,message):
    try:
        #print('sending... (x,y) to all connection except kinect')
        for i, client in enumerate(all_connections):
            conn = client.get_connection()
            if conn is not None and conn != conn_except:
                conn.send(str.encode(message))
    except Exception as ex:
        print("Error sending commands to all except Kinect", ex)

def send_command_all_except_ki_and_back_end(message):
    global kinect_conn
    global backend_conn
    for i, client in enumerate(all_connections):
        try:
            #print('sending... (x,y) to all connection except kinect')
            conn = client.get_connection()
            name = client.get_name()
            if name != 'back-end' and name != 'kinect':
                conn.send(str.encode(message))
        except Exception as ex:
            print("Error sending commands to all except Kinect", ex)
#this method for receiving data
def on_client(conn,address):
    global client_response
    global back_end_response
    global kinect_on
    global kinect_data
    global parsed_data
    global all_connections
    global check_pi

    client = PiNode.PiNode(conn, address)
    is_pass, client = authorize_connection(client)
    client_name = str(client.get_name())
    conn = client.get_connection()
    address = client.get_address()
    if is_pass:
        all_connections.append(client)
        if 'kinect' == client_name:
            print('kinect threading activated')
            while True:
                 try:
                    data = conn.recv(20480)
                    kinect_data = data.decode("utf-8")
                    if kinect_data != '':
                        pass
                       #print('from ' + str(client_name) + ': ' + str(kinect_data))
                    if kinect_on:
                        send_command_all_except_ki_and_back_end(str(kinect_data))
                 except Exception as ex:
                    kinect_data = ''
                    #print('Error on kinect connection', ex)

        elif 'raspberry Pi' == client_name:
            print('raspberry pi threading activated')

            while True:
                try:
                    client_response = conn.recv(20480)
                    client_response = client_response.decode("utf-8")
                    if client_response != '':
                        print('from ' + str(client_name) + ': ' + str(client_response))

                except:
                    pass
                    #print('Error on raspberry Pi connection', ex)

        elif 'back-end' == client_name:
            print('back-end threading activated')
            while True:
                try:
                    response = conn.recv(20480)
                    back_end_response = response.decode("utf-8")
                    #print(type(back_end_response))
                    if back_end_response != '':
                        print(back_end_response)
                    try:
                        parsed_data = ast.literal_eval(str(back_end_response))
                        client_ip = parsed_data.get('ip_address')
                        is_done = send_dict(parsed_data)
                        if is_done:
                            check_pi+=1
                    except:
                        print('not in dict form')
                except:
                    pass
                    #print('Error receiving data from back-end')
        else:
            print('No matching connection', client_name)

#auto sending receiving data from kinect and send in all to Pi
def auto_send():
    if kinect_conn is not None:
        try:
            if len(kinect_data) > 0:
                send_command_all_except_one(kinect_data)
        except Exception as ex:
            print('Error auto send:', ex)

def get_connection(no):
    try:
        client = all_connections[no]
        return client
    except:
        print('Invalid connection found!')
        return None

def send_dict(dict_data):
    global all_connections
    global current_souce
    load_new_file = False
    try:
        client_ip = dict_data.get('ip_address')
        sc_w = dict_data.get('screen_width')
        sc_h = dict_data.get('screen_height')
        in_x = dict_data.get('initial_x')
        in_y = dict_data.get('initial_y')
        file = dict_data.get('playfile')
        if file == current_souce:
            load_new_file = False
        else:
            load_new_file = True
            current_souce = file
        for client in all_connections:
            address = client.get_address()
            if client_ip in str(address[0]):
                pi_connection = client.get_connection()
                #send resolution
                pi_connection.send(str.encode('set_re:'+str(sc_w)+':'+str(sc_h)))
                #send initial point xy
                time.sleep(2)
                pi_connection.send(str.encode('xy:' + str(in_x) + ':' + str(in_y)))
                #send playfile and wait for play done
                time.sleep(2)
                #if load_new_file:
                pi_connection.send(str.encode('load:' + str(file)))
                #respond = pi_connection.recv(2048)
                #respond = respond.decode("utf-8")
                print('send dict is DONE!', client.get_name())
                break
    except Exception as ex:
        print('Error send dict',ex)
        return False

def list_connections():
    global all_connections
    global all_client_tread
    count = 0

    if len(all_connections) == 0:
        print('No connected devices')
    else:
        print("index  ----Clients----")
        for i, client in enumerate(all_connections):
            try:
                conn = client.get_connection()
                address = client.get_address()
                conn.send(str.encode('Greeting!'))
                results = str(i) + "      " + str(client.get_name()) + str(address) + '\n'
                print(results)
            except:
                del all_connections[i]
                del all_client_tread[i]
                print('Connection has disconnected then server deleted the connection')
                if count < len(all_connections):
                    list_connections()
                count += 1

#will be change for processing the commands received from web-site
def start_turtle():
    global kinect_conn
    global kinect_on
    global client_response
    global kinect_index
    global check_pi
    while True:
        try:
            #message = back_end_response
            if check_pi == count_pi:
                print('all Pi are ready to play, sending command [play] to all Pi(s)...')
                check_pi = 0
                continue

            message = raw_input('turtle> ')

            if message == 'list':
                list_connections()

            elif 'select' in message:
                target = message.replace('select ', '')  # target = id
                target = int(target)
                client = get_connection(target)
                conn = client.get_connection()
                address = client.get_address()
                if conn is not None:
                    while True:
                        print('client ' + str(address))
                        #message1 = back_end_response
                        message1 = raw_input('message to send:')
                        if message1 == 'quit':
                            break
                        elif len(message1) > 0:
                            send_command_one(conn, message1)

            elif message == 'send all':
                while True:
                    message2 = raw_input('message to send to all:')
                    if message2 == 'quit':
                        break
                    elif len(message2) > 0:
                        send_command_all(message2)

            elif message == 'send all no kinect':
                while True:
                    message3 = raw_input('message send all except Kinect:')
                    if message3 == 'quit':
                        break
                    elif len(message3) > 0:
                        send_command_all_except_one(message3)

            elif message == 'set kinect':
                while True:
                    index = ''
                    if kinect_conn != None:
                        print('Kinect has been set up, set new index or quit')
                        index = raw_input('input new kinect_conn index:')
                    elif kinect_conn == None:
                        index = ('input new kinect_conn index:')

                    if index == 'quit':
                        break
                    try:
                        kinect_conn = all_connections[int(index)]
                        kinect_index = index
                        print('Kinect has been set! \n INPUT> turn on kinect to start broadcast position')
                        break
                    except:
                        print('Invalid index, enter again! or quit')
                        kinect_conn = None


            elif message == 'turn on kinect': #to start receive data from kinect and broadcast to all pi
                if kinect_conn != None:
                    kinect_on = True
                    send_command_all('kinect on')
                    print('Kinect is On!' + '\n' + ': start receiving then broadcasting head position to all Pi')
                else:
                    print('Kinect has not been set up', 'go set kinect')
                    kinect_on = False

            elif message == 'turn of kinect':
                 kinect_on = False

            elif message == 'dodo':
                print('Hello dodo')

            elif message == 'see_dict':
                while True:
                    key_dict = raw_input('input key dict or quit')
                    if key_dict == 'quit':
                        break
                    else:
                        try:
                            values = parsed_data.get(key_dict)
                            print(key_dict, values)
                        except:
                            print('key_dict does not exist', key_dict)
                            continue
            elif message == 'send_dict':
                while True:
                    data_dict = raw_input('input dict or quit')
                    print(type(data_dict), data_dict)
                    if data_dict == 'quit':
                        break
                    else:
                        dict = ast.literal_eval(data_dict)
                        print(type(dict), dict)
                        send_dict(dict)
            else:
                print("Command is not recognized!")

        except Exception as ex:
            print('Error in turtle', ex)


def create_workers():
    for _ in range(NUMBER_OF_THREADS):
        t = threading.Thread(target=work)
        t.daemon = True
        t.start()


def work():
    while True:
        x = queue.get()
        if x == 1:
            create_socket()
            listen_conection()
            accept_connection()
        if x == 2:
            start_turtle()


        queue.task_done()
        print('task done!')

def create_jobs():
    for x in JOB_NUMBER:
        print ('put job', x)
        queue.put(x)

    queue.join()
    print('join queue!')

if __name__ == '__main__':
    create_workers()
    create_jobs()