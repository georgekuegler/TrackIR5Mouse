import ctypes
import ctypes.wintypes as wt
import win32api
import time
import json


class Display():
    def __init__(self):
        # User-specified rotational bounds of the monitor
        self.ROT_left = float()
        self.ROT_top = float()
        self.ROT_right = float()
        self.ROT_bottom = float()

        # Calculated absolutized 16-bit virtual desktop coordinates
        # from Win32 API calls
        self.ABS_left = float()
        self.ABS_top = float()
        self.ABS_right = float()
        self.ABS_bottom = float()
        self.AD_x_slope = float()
        self.AD_y_slope = float()

# Use the head tracker program to find out pitch and yaw limit
# Find whatever is comfortable for your head
# The NPTrackIR program can only send a maximum of 180deg for any rotational parameter

# SM_CMONITORS: 80
num_monitors = ctypes.windll.user32.GetSystemMetrics(ctypes.c_int(80))
print("%d Monitors Found" % num_monitors)

ADS = []
for i in range(num_monitors):
    ADS.append(Display())

ADS[1].ROT_Left = -63.00
ADS[1].ROT_Right = 63.00
ADS[1].ROT_Top = 0.45*ADS[1].ROT_Right
ADS[1].ROT_Bottom = -0.45*ADS[1].ROT_Right
'''
ADS[2].ROT_Left = -130.00
ADS[2].ROT_Right = -77.00
ADS[2].ROT_Top = 0.45*ADS[1].ROT_Right*1.5
ADS[2].ROT_Bottom = -0.45*ADS[1].ROT_Right
'''
ADS[0].ROT_Left = 90.00
ADS[0].ROT_Right = 170
ADS[0].ROT_Top = -20.00
ADS[0].ROT_Bottom = -55.00
'''
ADS[0].ROT_Left = -63.00
ADS[0].ROT_Right = 63.00
ADS[0].ROT_Top = 0.45*ADS[0].ROT_Right
ADS[0].ROT_Bottom = -0.45*ADS[0].ROT_Right

ADS[1].ROT_Left = -130.00
ADS[1].ROT_Right = -77.00
ADS[1].ROT_Top = 0.45*ADS[0].ROT_Right*1.5
ADS[1].ROT_Bottom = -0.45*ADS[0].ROT_Right
'''
# Padding in units of pixels
left_padding = 0
right_padding = 3
top_padding = 0
bottom_padding = 0

# --------------------------------------
# Get each monitors bounds on the virtual desktop and other info
monitors = win32api.EnumDisplayMonitors()

monitor_info = {}
for i in range(len(monitors)):
    monitor_info[i] = win32api.GetMonitorInfo(monitors[i][0])

# --------------------------------------
# Find the top left offset from the primary monitor top left corner (always at 0,0)
# to the virtual desktop top left corner (can be negative)
#               0    1   2     3
#             Left Top Right Bottom
#  'Monitor': (1920, 0, 3456, 864)

VD_left_offset = 0
VD_top_offset = 0
for i in range(len(monitor_info)):
    left = monitor_info[i]["Monitor"][0]
    top = monitor_info[i]["Monitor"][1]
    right = monitor_info[i]["Monitor"][2]
    bottom = monitor_info[i]["Monitor"][3]
    if left < VD_left_offset:
        VD_left_offset = left 
    if top < VD_top_offset:
        VD_top_offset = top
    
    print(monitor_info[i])
    print("Monitor %d Extents--> L:%d, T:%d, R:%d, B:%d" % (i, left, top, right, bottom))

print("Virtual Desktop Offset From Main: %s, %s" % (VD_left_offset, VD_top_offset))

# --------------------------------------
# Translation to absolute px coordinate
# Subtract the x-plane VM offset
# Subtract the y-plane VM offset
VM_displays = {}
for i in range(len(monitor_info)):
    VM_displays[i] = {"left":"", "top":"", "right":"", "bottom":""}   
    VM_displays[i]["left"] = monitor_info[i]["Monitor"][0] - VD_left_offset
    VM_displays[i]["top"] = monitor_info[i]["Monitor"][1] - VD_top_offset
    VM_displays[i]["right"] = monitor_info[i]["Monitor"][2] - VD_left_offset
    VM_displays[i]["bottom"] = monitor_info[i]["Monitor"][3] - VD_top_offset

# --------------------------------------
# Scaling transformation to absolute 65,535 coordinates
# This is used for the SendInput API call with the absolute coordinates flag set
# SM_XVIRTUALSCREEN: 78 ; gets the width of the virtual desktopin pixels
VM_width = ctypes.windll.user32.GetSystemMetrics(ctypes.c_int(78))
print("Width of VM_desktop: %s" % VM_width)
# SM_YVIRTUALSCREEN: 79 ; gets the height of the virtual desktop in pixels
VM_height = ctypes.windll.user32.GetSystemMetrics(ctypes.c_int(79))
print("Height of VM_desktop: %s" % VM_height)

x_PxToABS = 65535.00/VM_width
y_PxToABS = 65535.00/VM_height
for i in range(len(monitor_info)):
    ADS[i].ABS_Left = VM_displays[i]["left"] * x_PxToABS
    ADS[i].ABS_Top = VM_displays[i]["top"] * y_PxToABS
    ADS[i].ABS_Right = VM_displays[i]["right"] * x_PxToABS
    ADS[i].ABS_Bottom = VM_displays[i]["bottom"] * y_PxToABS

# Find 
for i in range(len(ADS)):
    rl = ADS[i].ROT_Left
    rr = ADS[i].ROT_Right
    al = ADS[i].ABS_Left
    ar = ADS[i].ABS_Right
    ADS[i].AD_x_slope = (ar-al)/(rr-rl)
    print("Monitor %s Proportional ADx: %s" % (i, ADS[i].AD_x_slope))
    rt = ADS[i].ROT_Top
    rb = ADS[i].ROT_Bottom
    at = ADS[i].ABS_Top
    ab = ADS[i].ABS_Bottom
    ADS[i].AD_y_slope = -(at-ab)/(rt-rb)
    print("Monitor %s Proportional ADy: %s" % (i, ADS[i].AD_y_slope))

# C struct redefinitions 
PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time",ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                 ("mi", MouseInput),
                 ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ip", Input_I)]

def MouseMoveAbsolute(x, y):
    extra = ctypes.c_ulong(0)
    ip = Input_I()
    # Flags: MOUSEEVENTF_ABSOLUTE:0x8000 , MOUSEEVENTF_MOVE:0x0001 ,  MOUSEEVENTF_VIRTUALDESK:0x4000    
    ip.mi = MouseInput(ctypes.c_long(x), ctypes.c_long(y), ctypes.c_ulong(0), ctypes.c_ulong(0x0001 | 0x4000 | 0x8000), ctypes.c_ulong(0), ctypes.pointer(extra))
    x = Input( ctypes.c_ulong(0), ip )
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

# For the future set the last screen initially equal to the main display
last_screen = 1
def MouseMove(yaw, pitch):
    global ADS
    global last_screen

    global left_padding
    global right_padding
    global top_padding
    global bottom_padding
    
    global x_PxToABS
    global y_PxToABS

    # The return statement is never reached if the head is pointing outside the bounds of any of the screens
    for i in range(len(ADS)):
        if yaw > ADS[i].ROT_Left and yaw < ADS[i].ROT_Right and \
           pitch < ADS[i].ROT_Top and pitch > ADS[i].ROT_Bottom: 
            rl = ADS[i].ROT_Left
            al = ADS[i].ABS_Left
            mx = ADS[i].AD_x_slope
            x = mx*(yaw-rl) + al
            rt = ADS[i].ROT_Top
            at = ADS[i].ABS_Top
            my = ADS[i].AD_y_slope
            y = my*(rt-pitch) + at
            MouseMoveAbsolute(int(x), int(y))
            last_screen = i
            return 
    # If the head is pointing outside of the bounds of a screen the mouse should snap to the breached edge
    # It could either be the pitch or the yaw axis that is too great or too little
    # To do this assume the pointer came from the last screen, just asign the mouse position to the absolute limit from the screen it came from
    if yaw < ADS[last_screen].ROT_Left:
        x = ADS[last_screen].ABS_Left + left_padding*x_PxToABS
    elif yaw > ADS[last_screen].ROT_Right: 
        x = ADS[last_screen].ABS_Right - right_padding*x_PxToABS
    else: # I have copied the code from above, this is the easiest and fastest way I found so far
        rl = ADS[last_screen].ROT_Left
        al = ADS[last_screen].ABS_Left
        mx = ADS[last_screen].AD_x_slope
        x = mx*(yaw-rl) + al
    if pitch > ADS[last_screen].ROT_Top: 
        y = ADS[last_screen].ABS_Top + top_padding*y_PxToABS
    elif pitch < ADS[last_screen].ROT_Bottom: 
        y = ADS[last_screen].ABS_Bottom - bottom_padding*y_PxToABS
    else: # I have copied the code from above, this is the easiest and fastest way I found so far
        rt = ADS[last_screen].ROT_Top
        at = ADS[last_screen].ABS_Top
        my = ADS[last_screen].AD_y_slope
        y = my*(rt-pitch) + at
    MouseMoveAbsolute(int(x), int(y))
    return 

'''
[FUTURE STUFF TO MAYBE ADD]
    [Uses to recalculate my values] can restart and reload module
When a WM_DISPLAYCHANGE message is sent, any monitor 
may be removed from the desktop and thus its HMONITOR becomes invalid 
or has its settings changed. Therefore, an application should check whether 
all HMONITORS are valid when this message is sent.
'''
