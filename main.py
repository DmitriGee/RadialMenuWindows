import time
_STime = time.time()
import json
import math
import os
import ctypes
import subprocess

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
# _sdl2 is an experimental library. In this case, it is used to manually focus the menu on start, to prevent the WINDOWLOSTFOCUS event from firing before the menu can be used.
from pygame import _sdl2
# win32 functions
import win32api
import win32con
import win32com.client
import win32gui
import win32ui
from PIL import Image

# Specify the default configuration file. This is also the configuration written to config.json if the file cannot be found.
CFG = {
    "menu": {
        "transparency": 205,
        "primary": [40,40,40],
        "secondary": [75,75,75],
        "tertiary": [255,127,0],
        "error": [255,63,63],
        "performance": {
            "framerate": 60,
            "resolution": "medium",
            "anti-aliasing": False
        },
        "shortcut": {
            "iconsize": 60,
            "title": [255,255,255],
            "description": [205,205,205]
        }
    }
}

def recursiveUpdate(orig: dict, new: dict) -> dict:
    result = orig
    for k,v in new.items():
        if isinstance(v, dict):
            result[k] = recursiveUpdate(orig[k], new[k])
        else:
            result[k] = new[k]
    return result
            

ConfigurationError = False
ConfigurationErrorReason = None
try:
    with open("config.json", "r") as f:
        j = dict(json.load(f))
        recursiveUpdate(CFG,j)
    print("Configuration loaded successfully!")
    print("DUMP config :")
    print(json.dumps(j, indent="  "))
    print(": END OF DUMP")
except FileNotFoundError:
    with open("config.json", "w") as f:
        json.dump(CFG, f, indent="    ")
except Exception as e:
    ConfigurationError = True
    ConfigurationErrorReason = str(e)
    print("[ERROR] The configuration file could not be read!")
    print(f"[ERROR] Exception: {e}")

# Not all comfiguration variables are written to constants. Why?
#   If a variable is read multiple times in a loop, reading
#   the value directly from the configuration can be costly
#   to low performance computers. Is this just speculation?
#   Absolutely. Do I care? No. Writing it to a constant
#   gives direct access to the value, instead of seraching
#   for it every single time it is requested. 
C_FRAMERATE = CFG["menu"]["performance"]["framerate"]
C_ICONSIZE = CFG["menu"]["shortcut"]["iconsize"]
C_ANTI_ALIASING = CFG["menu"]["performance"]["anti-aliasing"]
C_PRIMARY_COLOR = CFG["menu"]["primary"]
C_SECONDARY_COLOR = CFG["menu"]["secondary"]
C_TERTIARY_COLOR = CFG["menu"]["tertiary"]
C_TITLE_COLOR = CFG["menu"]["shortcut"]["title"]
C_DESCRIPTION_COLOR = CFG["menu"]["shortcut"]["title"]


FolderMissing = False
ItemsMissing = False


pygame.display.init()
pygame.font.init()

window = pygame.display.set_mode((0,0), pygame.NOFRAME)
clock = pygame.time.Clock()
pygame.display.set_caption("Radial Menu")
pygame.display.set_icon(pygame.image.load("icons/icon.bmp"))

def configureDisplay(CFG):
    hwnd = pygame.display.get_wm_info()["window"]

    # Set the window to transparent.
    # https://www.geeksforgeeks.org/how-to-make-a-fully-transparent-window-with-pygame/
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(
    hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(255,0,128), int(CFG["menu"]["transparency"]), win32con.LWA_COLORKEY | win32con.LWA_ALPHA)

    # Change the window from an App to a Tool (Hides it form the taskbar.)
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    style &= ~win32con.WS_EX_APPWINDOW
    style |= win32con.WS_EX_TOOLWINDOW
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)

    # Focus the window on top
    _sdl2.Window.focus(window)

configureDisplay(CFG)



windowrect = pygame.display.get_desktop_sizes()[0]
center = (int(windowrect[0]/2),int(windowrect[1]/2))

def lnkTarget(lnk_path):
    """Returns the target file and custom icon location from a .lnk shortcut."""
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(lnk_path)

    target = shortcut.TargetPath  # The actual file/folder the shortcut points to
    icon_path, icon_index = shortcut.IconLocation.split(",") if "," in shortcut.IconLocation else (shortcut.IconLocation, 0)

    if not icon_path or not os.path.exists(icon_path):  # If no custom icon, use the target itself
        icon_path = target

    return target, icon_path.strip(), int(icon_index)

def lnkIcon(target_path, icon_index=0, save_path="icon.png"):
    """Extracts an icon from a file (exe, dll, or ico) and saves it as an image."""
    if not os.path.exists(target_path):
        print(f"File not found: {target_path}")
        return None

    large, small = ctypes.c_void_p(), ctypes.c_void_p()
    num_icons = ctypes.windll.shell32.ExtractIconExW(target_path, icon_index, ctypes.byref(large), ctypes.byref(small), 1)

    if num_icons > 0:
        hicon = large.value or small.value  # Use large icon if available

        # Create a device context
        hdc = win32gui.GetDC(0)
        hdc_mem = win32ui.CreateDCFromHandle(hdc)
        hdc_compatible = hdc_mem.CreateCompatibleDC()

        # Create a bitmap for the icon
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(hdc_mem, 256, 256)
        hdc_compatible.SelectObject(bmp)

        # Draw the icon onto the bitmap
        win32gui.DrawIconEx(hdc_compatible.GetHandleOutput(), 0, 0, hicon, 256, 256, 0, None, win32con.DI_NORMAL)

        # Get bitmap data
        bmp_info = bmp.GetInfo()
        bmp_bits = bmp.GetBitmapBits(True)

        # Convert to a PIL Image and save
        image = Image.frombuffer("RGBA", (bmp_info['bmWidth'], bmp_info['bmHeight']), bmp_bits, "raw", "BGRA", 0, 1)
        image.save(save_path)

        # Cleanup
        win32gui.DestroyIcon(hicon)
        win32gui.ReleaseDC(0, hdc)
        hdc_compatible.DeleteDC()
        #hdc_mem.DeleteDC() # DeleteDC Failed!
        #bmp.DeleteObject() # DeleteObject() Method not found!

        return save_path
    else:
        return None

shortcuts = []
optionCount = 0
AppPath = "apps/"
NoIconImage = pygame.image.load("icons/unknown.bmp")
if os.path.exists(AppPath):
    for file in os.listdir(AppPath):
        if not file.endswith(".lnk"): continue
        target_path, icon_path, icon_index = lnkTarget(AppPath+file)
        save_path = lnkIcon(icon_path, icon_index, "C:/tmp/RadialMenuExtractedIcon.png")

        if save_path:
            icon = pygame.image.load(open(save_path))
        else:
            icon = NoIconImage
        icon = pygame.transform.smoothscale(icon, (C_ICONSIZE,C_ICONSIZE))
        fInfo = {
            "name": file.removesuffix(".lnk"),
            "target": target_path,
            "icon": icon
        }
        shortcuts.append(fInfo)
        optionCount += 1
    if optionCount == 0:
        ItemsMissing = True
else:
    FolderMissing = True
try:
    wedgeSize = 360/optionCount
except ZeroDivisionError:
    wedgeSize = 360

_res = CFG["menu"]["performance"]["resolution"]
match _res:
    case "low":
        wedgeSplit = 8
    case "medium":
        wedgeSplit = 4
    case "high":
        wedgeSplit = 2
    case "ultra":
        wedgeSplit = 1
    case _:
        wedgeSplit = 8

angle = 0

def quit():
    pygame.display.quit()
    pygame.quit()
    exit(0)

ErrorFont = pygame.font.SysFont("Arial", 20, True, False)
ErrorFontSmall = pygame.font.SysFont("Arial", 16, False, False)
LabelFont = pygame.font.SysFont("Arial", 20, True, False)
DescriptionFont = pygame.font.SysFont("Arial", 16, False, False)
MissingItemsText = ErrorFont.render("Add some shortcuts to get started!", C_ANTI_ALIASING, CFG["menu"]["error"])
MissingFolderText = ErrorFont.render("Error: Apps Folder Missing!", C_ANTI_ALIASING, CFG["menu"]["error"])
ConfigurationErrorText = ErrorFont.render("Error: The configuration file could not be read!", C_ANTI_ALIASING, CFG["menu"]["error"])
ConfigurationErrorReasonText = ErrorFontSmall.render(f"Reason: {ConfigurationErrorReason}", C_ANTI_ALIASING, CFG["menu"]["error"])

_ETime = time.time()
print("Startup Elapsed Time: " + str(round((_ETime-_STime)*1000)) + "ms")

done = False
while not done:
    _sdl2.Window.focus(window)
    mouse = win32api.GetCursorPos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT or event.type == pygame.WINDOWFOCUSLOST or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            done = True
            quit()

    window.fill((255,0,128))
    pygame.draw.circle(window, C_SECONDARY_COLOR, (center[0],center[1]), 400)
    
    angle = math.atan2(
        -(mouse[1] - center[1]),
        (mouse[0] - center[0])
    ) + (0.5*math.pi)

    if not (ItemsMissing or FolderMissing):
        steps = 360/wedgeSize
        selection = int(round((math.degrees(angle))/(360/steps)) % steps)

        pointing = math.radians(round(math.degrees(angle)/(360/steps))*(180/steps))
        points = [center]
        for i in range(0,int(wedgeSize/wedgeSplit)+1):
            d = math.radians(i*wedgeSplit-(wedgeSize/2)+math.degrees(pointing))
            points.append((
                center[0]+math.sin(d+pointing)*400,
                center[1]+math.cos(d+pointing)*400
            ))
        
        pygame.draw.polygon(window, C_TERTIARY_COLOR, points)
    
    pygame.draw.circle(window, C_PRIMARY_COLOR, (center[0],center[1]), 250)
    
    if not (ItemsMissing or FolderMissing):
        for i in range(0,optionCount):
            pos = (
                center[0]+math.sin(math.radians(360/optionCount*i))*325,
                center[1]+math.cos(math.radians(360/optionCount*i))*325
            )
            
            window.blit(shortcuts[i]["icon"], (pos[0]-C_ICONSIZE/2, pos[1]-C_ICONSIZE/2))
        
        text = LabelFont.render(shortcuts[selection]["name"][0:30]+"..." if len(shortcuts[selection]["name"]) > 30 else shortcuts[selection]["name"], True, CFG["menu"]["shortcut"]["title"])
        window.blit(text, (center[0]-text.get_width()/2,center[1]-text.get_height()/2-10))
        text = DescriptionFont.render(shortcuts[selection]["target"][0:90]+"..." if len(shortcuts[selection]["target"]) > 90 else shortcuts[selection]["target"], True, CFG["menu"]["shortcut"]["description"])
        window.blit(text, (center[0]-text.get_width()/2,center[1]-text.get_height()/2+10))

        if pygame.mouse.get_pressed(3)[0]:
            done = True
            print(shortcuts[selection]["target"])
            proc = subprocess.Popen(["explorer", shortcuts[selection]["target"]], creationflags=subprocess.DETACHED_PROCESS)
            quit()
    
    pygame.draw.aalines(window, (255,255,255), False, (
        (
            center[0]+math.sin(angle+math.radians(5))*215,
            center[1]+math.cos(angle+math.radians(5))*215,
        ),
        (
            center[0]+math.sin(angle)*225,
            center[1]+math.cos(angle)*225,
        ),
        (
            center[0]+math.sin(angle-math.radians(5))*215,
            center[1]+math.cos(angle-math.radians(5))*215,
        ),
    ), 1)
    
    if FolderMissing:
        window.blit(MissingFolderText, (center[0]-MissingFolderText.get_width()/2, center[1]-MissingFolderText.get_height()/2-50))
    elif ItemsMissing:
        window.blit(MissingItemsText, (center[0]-MissingItemsText.get_width()/2, center[1]-MissingItemsText.get_height()/2-50))
    elif ConfigurationError:
        window.blit(ConfigurationErrorText, (center[0]-ConfigurationErrorText.get_width()/2, center[1]-ConfigurationErrorText.get_height()/2-60))
        window.blit(ConfigurationErrorReasonText, (center[0]-ConfigurationErrorReasonText.get_width()/2, center[1]-ConfigurationErrorReasonText.get_height()/2-40))

    pygame.display.flip()
    clock.tick(C_FRAMERATE)
quit()
