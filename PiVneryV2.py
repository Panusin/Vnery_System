import cv2
import numpy as np
import threading
import socket
import os
try:
    from screeninfo import get_monitors
except:
    print('Error! No such ''screeninfo'' library installed in this system')
    pass
#HOST = '192.168.1.40'  # Standard loopback interface address (localhost)
#PORT = 60000  # Port to listen on (non-privileged ports are > 1023)
data = ':0:0:'
innitial_x = 0
innitial_y = 0
move_x = 0
move_y = 0
tv_width = 1280
tv_height = 720
frame_width = 0
frame_height = 0
window_name = "full-screen-window"
video_path = ''
picture_path = ''
video_list = []
picture_list = []
videoMode = False
pictureMode = False
is_playing = False
is_start = False
screen_name = 'None'
font = cv2.FONT_HERSHEY_SIMPLEX
authorize = False
default_screen = None
s = None
cap = None
# ------------------------- network config-----------------------------------
def connect(HOST, PORT):
    global s
    global screen_name
    global authorize
    global default_screen

    # connect to server and authorizing itself
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # s.settimeout(10)
        s.connect((HOST, PORT))
        # s.settimeout(None)
        data = s.recv(1024)
        data = data.decode("utf-8")
        if data == 'who?':
            send_command('raspberry Pi')
        data = s.recv(2048)
        data = data.decode("utf-8")
        if 'name:' in data:
            data = data.split(':')
            screen_name = data[1]
            #default_screen = put_text(default_screen, screen_name, tv_width / 2, 200)
            cv2.putText(default_screen, str(screen_name), (100, 150), font, 2, (255, 255, 255), 3, cv2.LINE_AA)
        authorize = True
        print('Connection has been established')
    except:
        print('Error! Authorization failed!')

    try:
        while True:
            respond = s.recv(20480)
            respond = respond.decode("utf-8")
            print('receive : ', respond)
            control_command(str(respond))

    except Exception as ex:
        print(ex, 'receiving commands from server failed!')
        # connect(HOST, PORT)
        # continue

def send_command(data):
    global s
    try:
        s.send(str.encode(data))
        print(data + ' sended!')
    except Exception as ex:
        print(ex)

def get_ip_address():
    ip = 'No Connection!'
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except Exception as ex:
        print('Error get ip address', ex)
    return ip

def get_hostname():
    hostname = 'No Connection!'
    try:
        hostname = socket.gethostname()
    except:pass
    return hostname

# ----------------------------------------------------------------------
def control_command(respond):
    global move_x
    global move_y
    global is_start
    global is_playing
    global videoMode
    global pictureMode
    global default_screen
    global screen_name
    try:
        data_ser = respond.split(':')
        if data_ser[0] == 'stop':
            is_start = False
            is_playing = False
            pictureMode = False
            videoMode = False
            cv2.destroyAllWindows()

        elif data_ser[0] == 'ki':
            move_x = int(data_ser[1])
            move_y = int(data_ser[2])
            #print('ki', move_x, move_y)

        elif data_ser[0] == 'load':
            file_name = data_ser[1]
            path = set_source_to_play(file_name)
            if ('.mov' in path or '.mp4' in path):
                videoMode = True
                pictureMode = False
                is_start = False
                is_playing = False
                cv2.destroyAllWindows()

            elif ('.jpg' in path or '.png' in path):
                pictureMode = True
                videoMode = False
                is_start = False
                is_playing = False
                cv2.destroyAllWindows()


        elif data_ser[0] == 'set_re':
            set_resolution(int(round(float(data_ser[1]), 0)), int(int(round(float(data_ser[2]), 0))))
            print('Done! set resolution', tv_width, tv_height)

        elif data_ser[0] == 'xy':
            set_innitial_point(int(round(float(data_ser[1]), 0)), int(int(round(float(data_ser[2]), 0))))
            print('Done! initial point', innitial_x, innitial_y)

        elif data_ser[0] == 'play':
            is_playing = True

        elif data_ser[0] == 'name':
            screen_name = data[1]
            cv2.putText(default_screen, str(screen_name), (100, 150), font, 2, (255, 255, 255), 3, cv2.LINE_AA)

    except Exception as ex:
        print('Error! control command', ex)



def rescale_frame(frame, percent=75):
    width = int(frame.shape[1] * percent / 100)
    height = int(frame.shape[0] * percent / 100)
    dim = (width, height)
    return cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)

def get_file_list(path):
    global video_list
    global picture_list
    try:
        for r, d, f in os.walk(path):
            for file in f:
                if ('.mov' in file or '.mp4' in file):
                    video_list.append(file)

                elif ('.jpg' in file or '.png' in file):
                    picture_list.append(file)
        print('all files are listed')
        print(video_list, picture_list)
    except Exception as ex:
        print('Error get files', ex)

def set_source_to_play(source_name):
    global video_path
    global picture_path
    global video_list
    global picture_list
    try:
        if source_name.endswith('.mov') or source_name.endswith('.mp4'):
            for video_name in video_list:
                if source_name == video_name:
                    video_path = str(inven_path) + '/' + str(source_name)
                    print('file is Existed! :', video_path)
                    return video_path
                    # send respond to sever files is exist
                    #socket.send(str.decode('file exist!'))

            print('Video does not exist', source_name)
        elif source_name.endswith('.jpg') or source_name.endswith('.png'):
            for picture_name in picture_list:
                if source_name == picture_name:
                    picture_path = str(inven_path) + '/' + str(source_name)
                    print('file is Existed! :', picture_path)
                    return picture_path
                    # send respond to sever files is exist
                    #socket.send(str.decode('file exist!'))
            print('Picture does not exist', source_name)
        else:
            # send respond back to server files dose not exist, dowload a file is needed.
            video_path = None
            picture_path = None
            print('source dose not exist, do something')
            #socket.send(str.decode('file not exist!'))

            print ('file not exist!')
    except Exception as ex:
        print('Error set_source_to_play', ex)

def download_source():
    pass
    #downloand file from database in the server


def get_resolution():
    try:
        a = get_monitors()
        a = str(a[0])
        a = a.split(',')
        width = a[2].split('=')
        height = a[3].split('=')
        return int(width[1]), int(height[1])
    except:
        print('Error get_resolution','get default resolution' ,tv_width, tv_height )
        return 1280, 720


def set_resolution(w, h):
    global tv_width
    global tv_height
    tv_width = w
    tv_height = h


def set_innitial_point(x, y):
    # 1 cm =  applox 37 pixels
    global innitial_x
    global innitial_y
    innitial_x = x
    innitial_y = y


# connect to server using threading and get variable named data from it
def work1_connection_thread():
    thread1 = threading.Thread(target=connect, args=(HOST, PORT))
    thread1.daemon = True
    thread1.start()


# ---------------------------------

# create cv2 to play video according to video_path that has been set in set_video_to_paly
def create_video_player():
    global video_path
    global cap
    global frame_width
    global frame_height
    global window_name
    try:
        if video_path != None:
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_FPS, 5)
            frame_height = int(cap.get(4))
            frame_width = int(cap.get(3))
            print(frame_width, frame_height)
            cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    except Exception as ex:
        cap = None
        print('Error loading video', ex)

def create_picture_player():
    global picture_path
    global cap
    global frame_width
    global frame_height
    global window_name
    try:
        if picture_path != None:
            cap = cv2.imread(picture_path, 1)
            frame_height = int(cap.shape[0])
            frame_width = int(cap.shape[1])
            print('picture W , H >> ',frame_width, frame_height)
            cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            print('create picture_player is done!')
    except Exception as ex:
        print('Error! create_picter_player',ex)
        #cap = None

def play_picture():
    global cap
    global move_x
    global move_y
    global is_start
    global window_name
    w, h = get_resolution()
    print(w,h,tv_width,tv_height)
    try:
        if len(cap) != 0 or cap != None:
            frame1_h1 = innitial_y
            frame1_h2 = int(frame1_h1 + tv_height)
            frame1_w1 = innitial_x
            frame1_w2 = int(frame1_w1 + tv_width)
            frame_hh = int(frame1_h2-frame1_h1)
            frame_ww = int(frame1_w2-frame1_w1)
            used_w = tv_width
            used_h = tv_height
            used_in_x = innitial_x
            used_in_y = innitial_y
            frame = cap
            print('start playing picture mode', frame_ww, frame_hh)
            is_start = True
            while True:
                key = cv2.waitKey(60)
                if key == 27:
                    break
                elif is_start == False:
                    cv2.destroyAllWindows()
                    break
                elif used_w != tv_width or used_h != tv_height:
                    frame1_h2 = int(frame1_h1 + tv_height)
                    frame1_w2 = int(frame1_w1 + tv_width)
                    used_w = tv_width
                    used_h = tv_height
                    frame_hh = int(frame1_h2 - frame1_h1)
                    frame_ww = int(frame1_w2 - frame1_w1)
                    print('update used_w and h')
                elif used_in_x != innitial_x or used_in_y != innitial_y:
                    frame1_h1 = innitial_y
                    frame1_w1 = innitial_x
                    used_in_x = innitial_x
                    used_in_y = innitial_y
                    print('update initial x and y')
                try:
                    frame1_h11 = frame1_h1 - move_y
                    frame1_h22 = frame1_h2 - move_y
                    frame1_w11 = frame1_w1 - move_x
                    frame1_w22 = frame1_w2 - move_x
                except:
                    continue

                if (frame1_h11 >= 0 and frame1_h22 < frame_height) and (frame1_w11 >= 0 and frame1_w22 < frame_width):
                    frame1 = frame[frame1_h11:frame1_h22, frame1_w11:frame1_w22]
                    #print('play1 w and h', int(frame1.shape[1]), int(frame1.shape[0]))
                    if frame_ww != w or frame_hh != h:
                        frame1 = cv2.resize(frame1, (w, h), interpolation=cv2.INTER_AREA)
                        print('play2 w and h', int(frame1.shape[1]), int(frame1.shape[0]))
                    cv2.imshow(window_name, frame1)
                    move_x = 0
                    move_y = 0

        print('quit play_picture')
    except:
        print('Error play_picture')

def play_video():
    global cap
    global move_x
    global move_y
    w, h = get_resolution()
    try:
        frame_counter = 0
        if cap != None:
            frame1_h1 = innitial_y
            frame1_h2 = int(frame1_h1 + tv_height)
            frame1_w1 = innitial_x
            frame1_w2 = int(frame1_w1 + tv_width)
            frame_hh = int(frame1_h2 - frame1_h1)
            frame_ww = int(frame1_w2 - frame1_w1)
            used_w = tv_width
            used_h = tv_height
            used_in_x = innitial_x
            used_in_y = innitial_y
            is_start = True
            while (True):
                ret, frame = cap.read()
                frame_counter += 1
                # frame = rescale_frame(frame,80)
                # If the last frame is reached, reset the capture and the frame_counter
                if frame_counter == cap.get(cv2.CAP_PROP_FRAME_COUNT):
                    frame_counter = 0  # Or whatever as long as it is the same as next line
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                # print(frame1_h1,frame1_h2,frame1_w1,frame1_w2)
                # ------------------------
                key = cv2.waitKey(1)
                if key == 27:
                    break
                elif is_start == False:
                    cv2.destroyAllWindows()
                    break
                elif used_w != tv_width or used_h != tv_height:
                    frame1_h2 = int(frame1_h1 + tv_height)
                    frame1_w2 = int(frame1_w1 + tv_width)
                    used_w = tv_width
                    used_h = tv_height
                    frame_hh = int(frame1_h2 - frame1_h1)
                    frame_ww = int(frame1_w2 - frame1_w1)

                elif used_in_x != innitial_x or used_in_y != innitial_y:
                    frame1_h1 = innitial_y
                    frame1_w1 = innitial_x
                try:
                    frame1_h11 = frame1_h1 - move_y
                    frame1_h22 = frame1_h2 - move_y
                    frame1_w11 = frame1_w1 - move_x
                    frame1_w22 = frame1_w2 - move_x
                    #print('pc', move_x, move_y)
                except:
                    continue

                if frame1_h11 >= 0 and frame1_h22 < frame_height and frame1_w11 >= 0 and frame1_w22 < frame_width:
                    frame1 = frame[frame1_h11:frame1_h22, frame1_w11:frame1_w22]
                    if frame_ww != w or frame_hh != h:
                        cv2.resize(frame1, (w, h), interpolation=cv2.INTER_AREA)
                    #print('play w and h', int(frame1.shape[1]), int(frame1.shape[0]))
                    cv2.imshow(str(window_name), frame1)
        cap.release()
        cv2.destroyAllWindows()
    except:
        print('Error play video')

def play_defalut_display():
    global is_start
    #create blank screen
    global default_screen
    #draw text in the screen created
    is_start = True
    try:
        default_screen = np.zeros((tv_width,tv_height,3), np.uint8)
        default_screen[:] = [50, 50, 50]
        cv2.putText(default_screen, str(get_ip_address()), (10, 100), font, 2, (255, 255, 255), 3, cv2.LINE_AA)
        #default_screen = put_text(default_screen, get_ip_address(), 10, 100)
    except Exception as ex:
        print('Can not put text in default screen!', ex)

    cv2.namedWindow('default display', cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty('default display', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    #cv2.setWindowProperty('default display', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
    while (1):
        cv2.imshow('default display', default_screen)
        k = cv2.waitKey(1) & 0xFF
        if k == 27:
            print(default_screen.shape[0],default_screen.shape[1])
            break
        elif is_start == False:
            break
    #cv2.destroyWindow('default display')

def check_path(default_path):
    if os.path.exists(default_path):
        print('Directory is exist!')
    else:
        print('path is not exist!, creating the path')
        try:
            os.makedirs(default_path)
        except Exception as ex:
            print('Can not create directory(path)', ex)

if __name__ == '__main__':

    HOST = '10.82.6.131'  # Standard loopback interface address (localhost)
    PORT = 60000  # Port to listen on (non-privileged ports are > 1023)
    work1_connection_thread()
    #defalut path
    inven_path = 'E:/PjPic'
    #check the path that program will download the source into it, and for loading them to be played
    #check_path(inven_path)
    #get all the source files existed in the path
    get_file_list(inven_path)
    #get screen resolution from the system
    #tv_width, tv_height = get_resolution()
    #set_resolution(tv_width, tv_height)
    set_innitial_point(10,10)
    # if tv has set in vertical, swap the width and height
    is_playing = False
    #videoMode = False
    #pictureMode = False
    picture_source = 'demo.jpg'
    video_source = 'fishVideo.mp4'
    #control_command('set_re:500:200')
    control_command('xy:1750:1000')
    control_command('load:' + str(picture_source))
    #control_command('play:')
    while True:
        try:
            if videoMode:
                print('In video mode')
                print('waiting for file path')
                while video_path == None:
                    continue
                create_video_player()
                print('waiting>>> to be play')
                while is_playing == False:
                    continue
                is_start = True
                play_video()
                is_playing = False
                videoMode = False
                print('exit video mode')

            elif pictureMode:
                print('In picture mode')
                print('waiting for file path')
                while picture_path == None:
                    continue
                create_picture_player()
                print('waiting>>> to be play')
                while is_playing == False:
                    continue
                is_start = True
                play_picture()
                is_playing = False
                pictureMode = False
                print('exit picture mode')

            else:
                pass
                #print('Mode has not been set up!')
                #set_resolution(1920, 1080)
                #play_defalut_display()
        except:
            print('Error in selecting mode')
