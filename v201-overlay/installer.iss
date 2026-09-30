#define MyAppName "Geek POS"
#define MyAppVersion "2.0.1"
#define MyAppExeName "App.exe"
[Setup]
AppId={{5CE7E944-6548-4B72-9AA8-2E2E14A22B6A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Geek POS
AppPublisherURL=mailto:a7medelzainy@gmail.com
VersionInfoCompany=Geek POS
VersionInfoDescription=Geek POS - Point of Sale System
VersionInfoProductName=Geek POS
VersionInfoProductVersion={#MyAppVersion}
DefaultDirName={localappdata}\Programs\Geek POS
UsePreviousAppDir=no
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=artifacts\installer-fixed
OutputBaseFilename=GeekPOS-Setup-x64-v2.0.1
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

[UninstallDelete]
Type: files; Name: "{app}\activation.dat"

[Code]
var
  LicensePage: TInputQueryWizardPage;
  ActivationToken: String;
  InstallId: String;

function GetMachineIdentity: String;
var
  MachineGuid: String;
begin
  MachineGuid := '';
  if not RegQueryStringValue(HKLM64, 'SOFTWARE\Microsoft\Cryptography', 'MachineGuid', MachineGuid) then
    RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\Cryptography', 'MachineGuid', MachineGuid);
  Result := MachineGuid + '|' + GetEnv('COMPUTERNAME') + '|GeekPOS-v2';
end;

function CmdQuote(const S: String): String;
begin
  Result := '"' + S + '"';
end;

function RunActivationRequest(const Serial, DeviceIdentity, AInstallId, DeviceName: String; var Token: String): Boolean;
var
  ScriptPath, OutputPath, PowerShellExe, Params: String;
  ScriptText, OutputText: AnsiString;
  ResultCode: Integer;
begin
  Result := False;
  Token := '';
  ScriptPath := ExpandConstant('{tmp}\geekpos-activate.ps1');
  OutputPath := ExpandConstant('{tmp}\geekpos-activate-result.txt');
  PowerShellExe := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  DeleteFile(OutputPath);

  ScriptText :=
    'param([string]$Serial,[string]$Device,[string]$Install,[string]$DeviceName,[string]$OutFile)' + #13#10 +
    '$ErrorActionPreference = ''Stop''' + #13#10 +
    '$headers = @{ apikey = ''sb_publishable_3KBgfOWVfFapMfs_chTH-w_W8uWpfYc'' }' + #13#10 +
    '$payload = @{ p_serial = $Serial; p_device_hash = $Device; p_install_id = $Install; p_device_name = $DeviceName } | ConvertTo-Json -Compress' + #13#10 +
    'try {' + #13#10 +
    '  $r = Invoke-RestMethod -Uri ''https://redkjjglxdouxplcljil.supabase.co/rest/v1/rpc/activate_license'' -Method Post -Headers $headers -ContentType ''application/json'' -Body $payload -TimeoutSec 20' + #13#10 +
    '  if ($r -is [System.Array]) { $row = $r[0] } else { $row = $r }' + #13#10 +
    '  if (($null -ne $row) -and ($row.ok -eq $true) -and (-not [string]::IsNullOrWhiteSpace([string]$row.activation_token))) {' + #13#10 +
    '    [IO.File]::WriteAllText($OutFile, ''OK|'' + [string]$row.activation_token, [Text.Encoding]::ASCII)' + #13#10 +
    '    exit 0' + #13#10 +
    '  }' + #13#10 +
    '  [IO.File]::WriteAllText($OutFile, ''ERR|REJECTED'', [Text.Encoding]::ASCII)' + #13#10 +
    '  exit 2' + #13#10 +
    '} catch {' + #13#10 +
    '  [IO.File]::WriteAllText($OutFile, ''ERR|CONNECTION'', [Text.Encoding]::ASCII)' + #13#10 +
    '  exit 3' + #13#10 +
    '}' + #13#10;

  if not SaveStringToFile(ScriptPath, ScriptText, False) then
  begin
    MsgBox('تعذر تجهيز أداة التفعيل المؤقتة.', mbError, MB_OK);
    Exit;
  end;

  Params := '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File ' + CmdQuote(ScriptPath) +
    ' -Serial ' + CmdQuote(Serial) +
    ' -Device ' + CmdQuote(DeviceIdentity) +
    ' -Install ' + CmdQuote(AInstallId) +
    ' -DeviceName ' + CmdQuote(DeviceName) +
    ' -OutFile ' + CmdQuote(OutputPath);

  if not Exec(PowerShellExe, Params, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    MsgBox('تعذر تشغيل خدمة التفعيل على Windows.', mbError, MB_OK);
    Exit;
  end;

  if not LoadStringFromFile(OutputPath, OutputText) then
  begin
    MsgBox('لم يتم استلام رد من خادم التفعيل. تأكد من اتصال الإنترنت ثم حاول مرة أخرى.', mbError, MB_OK);
    Exit;
  end;

  if (ResultCode = 0) and (Copy(OutputText, 1, 3) = 'OK|') then
  begin
    Token := Copy(OutputText, 4, Length(OutputText) - 3);
    Result := Length(Token) > 20;
  end
  else if Pos('ERR|REJECTED', OutputText) = 1 then
    MsgBox('مفتاح التفعيل غير صحيح أو مستخدم بالفعل. إذا سبق تجربة هذا المفتاح، اعمل له Reset ثم حاول مرة أخرى.', mbError, MB_OK)
  else
    MsgBox('تعذر الاتصال بخادم التفعيل. تأكد من اتصال الإنترنت ثم حاول مرة أخرى.', mbError, MB_OK);
end;

function ActivateLicense(const Serial: String): Boolean;
var
  NormalizedSerial, DeviceIdentity: String;
begin
  Result := False;
  ActivationToken := '';
  NormalizedSerial := Uppercase(Trim(Serial));

  if Length(NormalizedSerial) < 12 then
  begin
    MsgBox('أدخل مفتاح تفعيل Geek POS صحيح.', mbError, MB_OK);
    Exit;
  end;

  try
    DeviceIdentity := GetMachineIdentity;
    if Length(DeviceIdentity) < 8 then
    begin
      MsgBox('تعذر قراءة هوية الجهاز. أعد تشغيل Windows ثم حاول مرة أخرى.', mbError, MB_OK);
      Exit;
    end;

    InstallId := GetSHA256OfUnicodeString(
      DeviceIdentity + '|' + NormalizedSerial + '|' + GetDateTimeString('yyyymmddhhnnss', '', ''));

    Result := RunActivationRequest(
      NormalizedSerial, DeviceIdentity, InstallId, GetEnv('COMPUTERNAME'), ActivationToken);
  except
    Log('Activation error: ' + GetExceptionMessage);
    MsgBox('حدث خطأ أثناء التفعيل. أعد المحاولة أو تواصل مع الدعم.', mbError, MB_OK);
    Result := False;
  end;
end;

procedure InitializeWizard;
begin
  LicensePage := CreateInputQueryPage(wpWelcome,
    'تفعيل Geek POS',
    'مفتاح التفعيل الأصلي مطلوب',
    'أدخل License Key الذي حصلت عليه عند شراء Geek POS. المفتاح يعمل على جهاز وتثبيت واحد فقط.');
  LicensePage.Add('License Key:', False);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = LicensePage.ID then
  begin
    WizardForm.NextButton.Enabled := False;
    try
      Result := ActivateLicense(LicensePage.Values[0]);
    finally
      WizardForm.NextButton.Enabled := True;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  State: AnsiString;
begin
  if CurStep = ssPostInstall then
  begin
    if (ActivationToken = '') or (InstallId = '') then
      RaiseException('Geek POS activation was not completed.');
    State := '{"ActivationToken":"' + ActivationToken + '","InstallId":"' + InstallId + '"}';
    if not SaveStringToFile(ExpandConstant('{app}\activation.dat'), State, False) then
      RaiseException('Could not save Geek POS activation state.');
  end;
end;
