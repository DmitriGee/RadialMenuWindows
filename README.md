# RadialMenuWindows
Gives windows a game-inspired radial menu!


## Project Description
This project was directly inspired by another repository, [MacOS Radial App Switcher](https://github.com/oliver408i/radialMenu). Unlike that project, this one aims to provide functionality for launching programs.
The menu is customizable in many ways, with more options planned soon!



Currently, if you want to have the menu activated by a key shortcut, for example ctrl-alt-\[key\], you will need to manually create a shortcut.

## Installation

### Requirements
As of right now, you will need to install Python and it's required packages. Unfortunately, a required library, pillow, cannot be used in a python virtual environment, meaning you will have to install the packages directly to python's default library path.

To install, you will need to have Python 3.13.1 or higher installed (including pip).
The following packages are also required:
- pillow (11.1.0)
- pygame (2.6.1)
- pywin32 (310)
- pywin32-ctypes (0.2.3)

### Instructions
First, install Python. I recommend using Python 3.13.1 or higher, as this program has not been tested on older versions.

Next, install the required python packages:
```cmd
python -m pip install -r requirements.txt
```

#### Optional: Adding a key shortcut
I find it easier to press a key shortcut to launch the menu. If you do too, then you can follow these instructions to add your own semi-customizable key shortcut.

First, open file explorer and navigate to the following directory:
```C:\Users\[account-name]\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\``` (Replace \[account-name\] with your actual account name!)

Next, create a new shortcut. Title it "Radial Menu" (or whatever you want), set the target to "```pythonw.exe \[path-to-main.py\]```" (Replace \[path-to-main.py\] with the actual file path), and set the key shortcut to whatever you feel like. I personally set it to ctrl+alt+F.


## Known Bugs:
- Launching the menu on a different display still reads the mouse position relative to display 0
- Some apps refuse to launch 
- The optional key shortcut can only be actiaved when focused on an open window.
- Shortcuts may take longer to launch the longer windows has been run for since boot.

### Temporary Fixes:
#### Shortcuts take longer than expected to open:
Open Services. Find "SysMain" in the list of services. Disable it and set StartupType to Disabled. Reboot.
> WARNING: As of testing, this has not caused any noticeable system degredation and/or failure. Your results may vary. As this is a windows-related issue, consistent fixes may not be available.
