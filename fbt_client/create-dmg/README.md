cloned https://github.com/andreyvit/yoursway-create-dmg
yoursway-create-dmg
===================

A shell script to build fancy DMGs.  
  
  
**INSTALLATION**
  
By being a shell script, yoursway-create-dmg installation is very simple. Simply download and run.  
  
> git clone https://github.com/andreyvit/yoursway-create-dmg.git  
> cd yoursway-create-dmg  
> ./create-dmg [options]  
  
  
**USAGE**
  
> create-dmg [options...] [output\_name.dmg] [source\_folder]  

All contents of source\_folder will be copied into the disk image.  
  
**Options:**  
  
*   **--volname [name]:** set volume name (displayed in the Finder sidebar and window title)  
*   **--volicon [icon.icns]:** set volume icon    
*   **--background [pic.png]:** set folder background image (provide png, gif, jpg)    
*   **--window-pos [x y]:** set position the folder window    
*   **--window-size [width height]:** set size of the folder window    
*   **--icon-size [icon size]:** set window icons size (up to 128)    
*   **--icon [file name] [x y]:** set position of the file's icon    
*   **--hide-extension [file name]:** hide the extension of file    
*   **--custom-icon [file name]/[custom icon]/[sample file] [x y]:** set position and custom icon    
*   **--app-drop-link [x y]:** make a drop link to Applications, at location x, y    
*   **--eula [eula file]:** attach a license file to the dmg    
*   **--no-internet-enable:** disable automatic mount&copy    
*   **--version:** show tool version number    
*   **-h, --help:** display the help  
  
  
**EXAMPLE**
  
> \#!/bin/sh  
> test -f Application-Installer.dmg && rm Application-Installer.dmg  
> create-dmg \  
> --volname "Application Installer" \  
> --volicon "application\_icon.icns" \  
> --background "installer\_background.png" \  
> --window-pos 200 120 \  
> --window-size 800 400 \  
> --icon-size 100 \  
> --icon Application.app 200 190 \  
> --hide-extension Application.app \  
> --app-drop-link 600 185 \  
> Application-Installer.dmg \  
> source\_folder/  
