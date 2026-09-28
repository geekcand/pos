#define MyAppName "Sweets POS"
#define MyAppVersion "1.0.3"
#define MyAppExeName "App.exe"
[Setup]
AppId={{5CE7E944-6548-4B72-9AA8-2E2E14A22B6A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Elzainy
DefaultDirName={localappdata}\Programs\Sweets POS
UsePreviousAppDir=no
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=artifacts\installer-fixed
OutputBaseFilename=SweetsPOS-Setup-x64
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.19041
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "startup"; Description: "Start Sweets POS when I sign in to Windows"; GroupDescription: "Startup:"
[Files]
Source: "artifacts\final-win-x64\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{userprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: startup
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

