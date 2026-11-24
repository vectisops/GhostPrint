#define AppName "GhostPrint"
#define AppVersion "0.2.0"

[Setup]
AppId={{61A93ED2-2E06-48D4-9CB9-2C236133C2C0}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Vectis Ops
DefaultDirName={localappdata}\Programs\GhostPrint
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64
OutputDir=..\..\dist
OutputBaseFilename=GhostPrint-Setup
WizardStyle=modern
UninstallDisplayName={#AppName}
CloseApplications=yes
Compression=lzma2
SolidCompression=yes

[Files]
Source: "..\..\dist\GhostPrint.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\dist\mvt-ios.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\GhostPrint"; Filename: "{app}\GhostPrint.exe"
Name: "{autodesktop}\GhostPrint"; Filename: "{app}\GhostPrint.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\GhostPrint.exe"; Description: "Launch GhostPrint"; Flags: nowait postinstall skipifsilent
