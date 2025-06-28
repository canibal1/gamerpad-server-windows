;–– Basic installer settings ––
[Setup]
AppName=CoreOrbits-GamerPad
AppVersion=1.0
DefaultDirName={pf}\CoreOrbits-GamerPad
PrivilegesRequired=admin
OutputDir=installers
OutputBaseFilename=CoreOrbits-GamerPad Installer
; End-User License Agreement file
LicenseFile=EULA.txt

;–– Installation files ––
[Files]
; PyInstaller produced EXE
Source: "dist\CoreOrbits-GamerPad.exe"; DestDir: "{app}"; Flags: ignoreversion
; ViGEmBus driver installer (keep in same folder)
Source: "ViGEmBus_*.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

;–– Post-install commands ––
[Run]
; 1) Install the ViGEmBus driver silently
Filename: "{tmp}\ViGEmBus_latest.exe"; \
  Description: "Click to install the ViGEmBus driver"; \
  Flags: shellexec waituntilterminated

; 2) Option to launch the application after install
Filename: "{app}\CoreOrbits-GamerPad.exe"; \
  Description: "Launch CoreOrbits-GamerPad now"; \
  Flags: nowait postinstall skipifsilent

;–– Optional: Desktop shortcut ––
[Icons]
Name: "{group}\CoreOrbits-GamerPad"; Filename: "{app}\CoreOrbits-GamerPad.exe"
Name: "{commondesktop}\CoreOrbits-GamerPad"; Filename: "{app}\CoreOrbits-GamerPad.exe"
