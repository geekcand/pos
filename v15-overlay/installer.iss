#define MyAppName "Geek POS"
#define MyAppVersion "1.5.0"
#define MyAppExeName "App.exe"
[Setup]
AppId={{5CE7E944-6548-4B72-9AA8-2E2E14A22B6A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Geek
DefaultDirName={localappdata}\Programs\Geek POS
UsePreviousAppDir=no
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=artifacts\installer-fixed
OutputBaseFilename=GeekPOS-Setup-x64
SetupIconFile=Assets\GeekPOS.ico
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.19041
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\Assets\GeekPOS.ico
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "startup"; Description: "Start Geek POS when I sign in to Windows"; GroupDescription: "Startup:"
[Files]
Source: "artifacts\final-win-x64\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{userprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\Assets\GeekPOS.ico"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\Assets\GeekPOS.ico"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\Assets\GeekPOS.ico"; Tasks: startup
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
