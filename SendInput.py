import ctypes
import ctypes.wintypes as wt
import win32api
import time
import json

MM_ABSOLUTE_MAX = 65535

class Display():
    def __init__(self):
        self.index = 0
        # User-specified rotational bounds of the monitor
        self.ROT_left = float()
        self.ROT_top = float()
        self.ROT_right = float()
        self.ROT_bottom = float()

        self.px_left = int()
        self.px_top = int()
        self.px_right = int()
        self.px_bottom = int()

        self.px_abs_left = int()
        self.px_abs_top = int()
        self.px_abs_right = int()
        self.px_abs_bottom = int()    
        self.x_PxToABS = float()
        self.y_PxToABS = float()

        # Calculated absolutized 16-bit virtual desktop coordinates
        # from Win32 API calls
        self.ABS_left = float()
        self.ABS_top = float()
        self.ABS_right = float()
        self.ABS_bottom = float()
        self.AD_x_slope = float()
        self.AD_y_slope = float()

    def set_abs_bounds(self, VD_left_offset, VD_top_offset, x_PxToABS, y_PxToABS):
        self.px_abs_left = self.px_left - VD_left_offset
        self.px_abs_top = self.px_top - VD_top_offset
        self.px_abs_right = self.px_right - VD_left_offset
        self.px_abs_bottom = self.px_bottom - VD_top_offset

        print("Monitor %d APX\nLeft:%s\nRight:%s\nTop:%s\nBottom:%s\n" % (self.index, self.px_abs_left, self.px_abs_right, self.px_abs_top, self.px_abs_bottom))
        # In a successful version, I can remove the absolute pixel members and just use the calculation below
        # for debugging purposes, I want to be able to query their values

        self.ABS_left = float(self.px_abs_left) * x_PxToABS
        self.ABS_top = float(self.px_abs_top) * y_PxToABS
        self.ABS_right = float(self.px_abs_right) * x_PxToABS
        self.ABS_bottom = float(self.px_abs_bottom) * y_PxToABS

        rl = self.ROT_left
        rr = self.ROT_right
        al = self.ABS_left
        ar = self.ABS_right
        self.AD_x_slope = (ar-al)/(rr-rl)

        rt = self.ROT_top
        rb = self.ROT_bottom
        at = self.ABS_top
        ab = self.ABS_bottom
        self.AD_y_slope = -(at-ab)/(rt-rb)
        print("Monitor %d ABS\nLeft:%s\nRight:%s\nTop:%s\nBottom:%s\n" % (self.index, self.ABS_left, self.ABS_right, self.ABS_top, self.ABS_bottom))



# Use the head tracker program to find out pitch and yaw limit
# Find whatever is comfortable for your head
# The NPTrackIR program can only send a maximum of 180deg for any rotational parameter

# SM_CMONITORS: 80
num_monitors = ctypes.windll.user32.GetSystemMetrics(ctypes.c_int(80))
print("%d Monitors Found" % num_monitors)
# SM_XVIRTUALSCREEN: 78 ; gets the width of the virtual desktopin pixels
VM_width = ctypes.windll.user32.GetSystemMetrics(ctypes.c_int(78))
print("Width of VM_desktop: %s" % VM_width)
# SM_YVIRTUALSCREEN: 79 ; gets the height of the virtual desktop in pixels
VM_height = ctypes.windll.user32.GetSystemMetrics(ctypes.c_int(79))
print("Height of VM_desktop: %s" % VM_height)

ADS = []
for i in range(num_monitors):
    ADS.append(Display())

# --------------------------------------
# Find the top left offset from the primary monitor top left corner (always at 0,0)
# to the virtual desktop top left corner (can be negative)
#               0    1   2     3
#             Left Top Right Bottom
#  'Monitor': (1920, 0, 3456, 864)
VD_left_offset = 0
VD_top_offset = 0
for i,m in enumerate(win32api.EnumDisplayMonitors()):
    info = win32api.GetMonitorInfo(m[0])
    ADS[i].index = i
    ADS[i].px_left = left = info["Monitor"][0]
    ADS[i].px_top = top = info["Monitor"][1]
    ADS[i].px_right = right = info["Monitor"][2]
    ADS[i].px_bottom = bottom = info["Monitor"][3]
    if left < VD_left_offset:
        VD_left_offset = left 
    if top < VD_top_offset:
        VD_top_offset = top
    print("Monitor %d Extents--> L:%d, T:%d, R:%d, B:%d" % (i, left, top, right, bottom))

print("Virtual Desktop Offset From Main Monitor--> Left:%s, Top:%s\n" % (VD_left_offset, VD_top_offset))

ADS[1].ROT_left = -63.00
ADS[1].ROT_right = 63.00
ADS[1].ROT_top = 0.45*ADS[1].ROT_right
ADS[1].ROT_bottom = -0.45*ADS[1].ROT_right
'''
ADS[2].ROT_left = -130.00
ADS[2].ROT_right = -77.00
ADS[2].ROT_top = 0.45*ADS[1].ROT_right*1.5
ADS[2].ROT_bottom = -0.45*ADS[1].ROT_right
'''
ADS[0].ROT_right = -80.00
ADS[0].ROT_left = -160.00
ADS[0].ROT_top = -16.00
ADS[0].ROT_bottom = -55.00

# Padding in units of pixels
left_padding = 0
right_padding = 3
top_padding = 0
bottom_padding = 0

x_PxToABS = MM_ABSOLUTE_MAX / float(VM_width);
print("x_PxToABS: %f" % x_PxToABS);
y_PxToABS = MM_ABSOLUTE_MAX / float(VM_height);
print("y_PxToABS: %f\n" % y_PxToABS);

for m in ADS:
    m.set_abs_bounds(VD_left_offset, VD_top_offset, x_PxToABS, y_PxToABS)

# C struct redefinitions 
PUL = ctypes.POINTER(ctypes.c_ulong)

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time",ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("mi", MouseInput)]

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
        if yaw > ADS[i].ROT_left and yaw < ADS[i].ROT_right and \
           pitch < ADS[i].ROT_top and pitch > ADS[i].ROT_bottom: 
            rl = ADS[i].ROT_left
            al = ADS[i].ABS_left
            mx = ADS[i].AD_x_slope
            x = mx*(yaw-rl) + al
            rt = ADS[i].ROT_top
            at = ADS[i].ABS_top
            my = ADS[i].AD_y_slope
            y = my*(rt-pitch) + at
            MouseMoveAbsolute(int(x), int(y))
            last_screen = i
            return 
    # If the head is pointing outside of the bounds of a screen the mouse should snap to the breached edge
    # It could either be the pitch or the yaw axis that is too great or too little
    # To do this assume the pointer came from the last screen, just asign the mouse position to the absolute limit from the screen it came from
    if yaw < ADS[last_screen].ROT_left:
        x = ADS[last_screen].ABS_left + left_padding*x_PxToABS
    elif yaw > ADS[last_screen].ROT_right: 
        x = ADS[last_screen].ABS_right - right_padding*x_PxToABS
    else: # I have copied the code from above, this is the easiest and fastest way I found so far
        rl = ADS[last_screen].ROT_left
        al = ADS[last_screen].ABS_left
        mx = ADS[last_screen].AD_x_slope
        x = mx*(yaw-rl) + al
    if pitch > ADS[last_screen].ROT_top: 
        y = ADS[last_screen].ABS_top + top_padding*y_PxToABS
    elif pitch < ADS[last_screen].ROT_bottom: 
        y = ADS[last_screen].ABS_bottom - bottom_padding*y_PxToABS
    else: # I have copied the code from above, this is the easiest and fastest way I found so far
        rt = ADS[last_screen].ROT_top
        at = ADS[last_screen].ABS_top
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
