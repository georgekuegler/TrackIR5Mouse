# TrackIR5PyMouse

This program controls the mouse using pitch and yaw data from the Natural Point TrackIR5.
Rotational coordinates are mapped to the Windows virtual desktop in an absolute fashion, so the mouse always moves to where the user is looking.

A thanks to John Flux and his TrackIR library at [@johnflux/python_trackir](https://github.com/johnflux/python_trackir). This software used his library as the basis for it's code.

# How It Works:
The user picks comfortable pitch and yaw boundaries for each active monitor.
The program poles Windows for the virtual desktop coordinates of each monitor and does some translation (see the section on the virtual desktop if you're interested).
The rotational boundaries are mapped to each monitor's window in the virtual desktop.
Every loop iteration, a simple linear interpolation between monitor edges determines the mouse position.

# Notes On Related Software:
FreePIE is an excellent tool. You might also want to check that out. It is the first piece of software I used to get going quickly.
Unfortunately, it does not support the Win32 call, SendInput. This is necessary for any pen enabled applications and some UWP applications to register drawing. These applications use the Windows messaging system to get updates about mouse movement within the application window. I believe the common FreePIE function for moving the mouse, SetCursorPosition, does not cause the appropriate Windows messages is to be sent to the target program.

...TODO more on program choices...

# The Virtual Screen
...TODO explain Microsoft's quirky virtual desktop and the need to translate coordinates...
Link: (https://docs.microsoft.com/en-us/windows/win32/gdi/the-virtual-screen)
