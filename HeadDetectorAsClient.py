# PyKinect
# Copyright(c) Microsoft Corporation
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the License); you may not use
# this file except in compliance with the License. You may obtain a copy of the
# License at http://www.apache.org/licenses/LICENSE-2.0
#
# THIS CODE IS PROVIDED ON AN  *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION ANY
# IMPLIED WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A PARTICULAR PURPOSE,
# MERCHANTABLITY OR NON-INFRINGEMENT.
#
# See the Apache Version 2.0 License for specific language governing
# permissions and limitations under the License.
import itertools
import ctypes
from pykinect import nui
from pykinect.nui import JointId
import pygame
from pygame.color import THECOLORS
from pygame.locals import *
import cv2
import threading
import socket

KINECTEVENT = pygame.USEREVENT
DEPTH_WINSIZE = 320, 240
VIDEO_WINSIZE = 640, 480
#SCREEN_SIZE = 1920, 1080
SCREEN_W = 2704
SCREEN_H = 1520
index_person = 0
head_position = [0] * 2

#kinect stuffs
pygame.init()
SKELETON_COLORS = [THECOLORS["red"],
                   THECOLORS["blue"],
                   THECOLORS["green"],
                   THECOLORS["orange"],
                   THECOLORS["purple"],
                   THECOLORS["yellow"],
                   THECOLORS["violet"]]
LEFT_ARM = (JointId.ShoulderCenter,
            JointId.ShoulderLeft,
            JointId.ElbowLeft,
            JointId.WristLeft,
            JointId.HandLeft)
RIGHT_ARM = (JointId.ShoulderCenter,
             JointId.ShoulderRight,
             JointId.ElbowRight,
             JointId.WristRight,
             JointId.HandRight)
LEFT_LEG = (JointId.HipCenter,
            JointId.HipLeft,
            JointId.KneeLeft,
            JointId.AnkleLeft,
            JointId.FootLeft)
RIGHT_LEG = (JointId.HipCenter,
             JointId.HipRight,
             JointId.KneeRight,
             JointId.AnkleRight,
             JointId.FootRight)
SPINE = (JointId.HipCenter,
         JointId.Spine,
         JointId.ShoulderCenter,
         JointId.Head)
skeleton_to_depth_image = nui.SkeletonEngine.skeleton_to_depth_image
def draw_skeleton_data(pSkelton, index, positions, width=4):
    start = pSkelton.SkeletonPositions[positions[0]]

    for position in itertools.islice(positions, 1, None):
        next = pSkelton.SkeletonPositions[position.value]

        curstart = skeleton_to_depth_image(start, dispInfo.current_w, dispInfo.current_h)
        curend = skeleton_to_depth_image(next, dispInfo.current_w, dispInfo.current_h)

        pygame.draw.line(screen, SKELETON_COLORS[index], curstart, curend, width)

        start = next
# recipe to get address of surface: http://archives.seul.org/pygame/users/Apr-2008/msg00218.html
if hasattr(ctypes.pythonapi, 'Py_InitModule4'):
    Py_ssize_t = ctypes.c_int
elif hasattr(ctypes.pythonapi, 'Py_InitModule4_64'):
    Py_ssize_t = ctypes.c_int64
else:
    raise TypeError("Cannot determine type of Py_ssize_t")

_PyObject_AsWriteBuffer = ctypes.pythonapi.PyObject_AsWriteBuffer
_PyObject_AsWriteBuffer.restype = ctypes.c_int
_PyObject_AsWriteBuffer.argtypes = [ctypes.py_object,
                                    ctypes.POINTER(ctypes.c_void_p),
                                    ctypes.POINTER(Py_ssize_t)]
def surface_to_array(surface):
    buffer_interface = surface.get_buffer()
    address = ctypes.c_void_p()
    size = Py_ssize_t()
    _PyObject_AsWriteBuffer(buffer_interface,
                            ctypes.byref(address), ctypes.byref(size))
    bytes = (ctypes.c_byte * size.value).from_address(address.value)
    bytes.object = buffer_interface
    return bytes
def draw_skeletons(skeletons):
    for index, data in enumerate(skeletons):
        # draw the Head
        HeadPos = skeleton_to_depth_image(data.SkeletonPositions[JointId.Head], SCREEN_W, SCREEN_H)
        HeadPosDraw = skeleton_to_depth_image(data.SkeletonPositions[JointId.Head], 320, 240)
        draw_skeleton_data(data, index, SPINE, 10)
        if int(HeadPos[0]) != 0 and int(HeadPos[1]) != 0:
            pygame.draw.circle(screen, SKELETON_COLORS[index], (int(HeadPosDraw[0]), int(HeadPosDraw[1])), 10, 0)
            head_position[0] = int(HeadPos[0])
            head_position[1] = int(HeadPos[1])
            index_person = index
            # pygame.display.update()
            # print(data)
            # print(int(head_position[0]), int(head_position[1]))
        # drawing the limbs
        draw_skeleton_data(data, index, LEFT_ARM)
        draw_skeleton_data(data, index, RIGHT_ARM)
        draw_skeleton_data(data, index, LEFT_LEG)
        draw_skeleton_data(data, index, RIGHT_LEG)
def rescale_frame(frame, percent=75):
    width = int(frame.shape[1] * percent / 100)
    height = int(frame.shape[0] * percent / 100)
    dim = (width, height)
    return cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)


#---Network-----------------------
all_connections = []
all_address = []
all_connections_status=[]
messageToPi = None
s = None
kinect_on = False
def connect(HOST, PORT):
    global data
    global s
    global kinect_on
    count_connection = 0
    data = ':0:0:'
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            print('Connection has been connected to server!')
            while True:
                data = s.recv(20480)
                data = data.decode("utf-8")
                print(data)
                if data == 'kinect on':
                    kinect_on = True
                elif data == 'who?':
                    s.send(str.encode('kinect'))

        except Exception as ex:
            count_connection +=1
            print(ex)
            continue
            if count_connection == 50:
                break



def send_command_all():#uses send mess to all Pi(s) except Kinect
    global messageToPi
    conut = 0
    while True:
        if kinect_on:
            try:
                s.send(str.encode(messageToPi))
                print('send ', messageToPi)
                messageToPi = None
            except:
                continue



def work1():
    connect(HOST,PORT)

def work2():
    global messageToPi
    send_command_all()

#-------------------------------------------------------




if __name__ == '__main__':
    # network connection use treading to connect to server and Pi(s) ---------------------------------------
    HOST = '10.82.6.131'  # Standard loopback interface address (localhost)
    PORT = 60000  # Port to listen on (non-privileged ports are > 1023)
    thread1 = threading.Thread(target=work1)
    thread2 = threading.Thread(target=work2)

    thread1.start()
    thread2.start()
    # ----------------------------------------------------------------------
    SCREEN_W = 3840
    SCREEN_H = 2160
    full_screen = False
    draw_skeleton = True
    video_display = False
    kinect_enable = True
    percent = 75  # isoration (zoom in or zoom out range = 50 - 100 mid = 75
    frame1_frame2_distant = 100
    move_X = 0
    move_Y = 0

    screen = pygame.display.set_mode(DEPTH_WINSIZE, 0, 16)
    pygame.display.set_caption('Skeleton View')
    skeletons = None
    screen.fill(THECOLORS["black"])
    kinect = nui.Runtime()
    kinect.skeleton_engine.enabled = True


    def post_frame(frame):
        try:
            pygame.event.post(pygame.event.Event(KINECTEVENT, skeletons=frame.SkeletonData))
        except:
            # event queue full
            pass


    kinect.skeleton_frame_ready += post_frame
    # kinect.depth_frame_ready += depth_frame_ready
    # kinect.video_frame_ready += video_frame_ready

    # kinect.video_stream.open(nui.ImageStreamType.Video, 2, nui.ImageResolution.Resolution640x480, nui.ImageType.Color)
    # kinect.depth_stream.open(nui.ImageStreamType.Depth, 2, nui.ImageResolution.Resolution320x240, nui.ImageType.Depth)

    print('Controls: ')
    print('     u - Increase elevation angle')
    print('     j - Decrease elevation angle')

    # main game loop
    done = False
    start_play = True

    while not done:
        dispInfo = pygame.display.Info()
        e = pygame.event.wait()
        if e.type == pygame.QUIT:
            done = True
            break
        elif e.type != KINECTEVENT:
            continue

        elif e.type == KINECTEVENT:
            skeletons = e.skeletons
            screen.fill(THECOLORS["black"])
            draw_skeletons(skeletons)
            # head_position must be located in the same size of whole vido
            # no fixing yet---------
            if kinect_enable:
                move_X = int(int(head_position[0] - SCREEN_W/2) * 0.085)
                move_Y = int(int(head_position[1] - SCREEN_H/2) * 0.085)
                # print(move_X, move_Y)
                data = 'ki:' + str(move_X) + ':' + str(move_Y) + ':'
                messageToPi = data
            pygame.display.update()

        elif e.type == KEYDOWN:
            if e.key == K_ESCAPE:
                done = True
                break
            elif e.key == K_u:
                kinect.camera.elevation_angle = kinect.camera.elevation_angle + 2
            elif e.key == K_j:
                kinect.camera.elevation_angle = kinect.camera.elevation_angle - 2
            elif e.key == K_x:
                kinect.camera.elevation_angle = 2
            elif e.key == K_q:
                cv2.destroyAllWindows()
                kinect.close()
                done = True