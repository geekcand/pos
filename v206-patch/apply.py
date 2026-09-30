from pathlib import Path
import sys
root=Path(sys.argv[1])

# LicenseService: local device-bound validation; online refresh never blocks offline startup.
p=root/'Services/LicenseService.cs'
s=p.read_text(encoding='utf-8-sig')
s='using System.Security.Cryptography;\nusing System.Text;\n'+s
s=s.replace('''    public sealed record ActivationState(string ActivationToken, string InstallId);\n    public sealed record LicenseResult(bool Ok, string Message, string? ActivationToken = null);''','''    public sealed class ActivationState\n    {\n        public string ActivationToken { get; set; } = \"\";\n        public string InstallId { get; set; } = \"\";\n        public string DeviceBinding { get; set; } = \"\";\n        public DateTime? LastOnlineValidationUtc { get; set; }\n    }\n\n    public sealed record LicenseResult(bool Ok, string Message, string? ActivationToken = null, bool Definitive = true);''')
old='''    public async Task<LicenseResult> ValidateLocalAsync(CancellationToken token = default)\n    {\n        var state = LoadState();\n        if (state is null || string.IsNullOrWhiteSpace(state.ActivationToken) || string.IsNullOrWhiteSpace(state.InstallId))\n            return new(false, \"هذه النسخة غير مفعلة.\");\n        return await InvokeAsync(\"validate_license\", new\n        {\n            p_activation_token = state.ActivationToken,\n            p_device_hash = GetDeviceFingerprint(),\n            p_install_id = state.InstallId\n        }, token);\n    }'''
new='''    public Task<LicenseResult> ValidateLocalAsync(CancellationToken token = default)\n    {\n        var state = LoadState();\n        if (state is null || string.IsNullOrWhiteSpace(state.ActivationToken) || string.IsNullOrWhiteSpace(state.InstallId))\n            return Task.FromResult(new LicenseResult(false, \"هذه النسخة غير مفعلة.\"));\n\n        var expectedBinding = ComputeDeviceBinding(state.InstallId);\n        if (string.IsNullOrWhiteSpace(state.DeviceBinding))\n        {\n            // Migration for activations created by v2.0.3-v2.0.5. The setup had already\n            // validated the license online, so bind that state to this Windows device locally.\n            state.DeviceBinding = expectedBinding;\n            SaveState(state);\n        }\n        else if (!string.Equals(state.DeviceBinding, expectedBinding, StringComparison.OrdinalIgnoreCase))\n        {\n            return Task.FromResult(new LicenseResult(false, \"ملف التفعيل لا يخص هذا الجهاز.\"));\n        }\n\n        return Task.FromResult(new LicenseResult(true, \"النسخة مفعلة على هذا الجهاز.\"));\n    }\n\n    public async Task<LicenseResult> ValidateOnlineAsync(CancellationToken token = default)\n    {\n        var state = LoadState();\n        if (state is null || string.IsNullOrWhiteSpace(state.ActivationToken) || string.IsNullOrWhiteSpace(state.InstallId))\n            return new(false, \"هذه النسخة غير مفعلة.\");\n\n        return await InvokeAsync(\"validate_license\", new\n        {\n            p_activation_token = state.ActivationToken,\n            p_device_hash = GetDeviceFingerprint(),\n            p_install_id = state.InstallId\n        }, token);\n    }\n\n    public async Task TryRefreshOnlineAsync(CancellationToken token = default)\n    {\n        var state = LoadState();\n        if (state is null) return;\n\n        var result = await ValidateOnlineAsync(token);\n        if (!result.Definitive) return; // Offline/server unavailable must never disable a valid local activation.\n\n        if (result.Ok)\n        {\n            state.LastOnlineValidationUtc = DateTime.UtcNow;\n            if (string.IsNullOrWhiteSpace(state.DeviceBinding)) state.DeviceBinding = ComputeDeviceBinding(state.InstallId);\n            SaveState(state);\n        }\n        else\n        {\n            try { File.Delete(StatePath); } catch { }\n        }\n    }'''
assert old in s
s=s.replace(old,new)
old='''        if (result.Ok && !string.IsNullOrWhiteSpace(result.ActivationToken))\n        {\n            File.WriteAllText(StatePath, JsonSerializer.Serialize(new ActivationState(result.ActivationToken!, installId)));\n        }'''
new='''        if (result.Ok && !string.IsNullOrWhiteSpace(result.ActivationToken))\n        {\n            SaveState(new ActivationState\n            {\n                ActivationToken = result.ActivationToken!,\n                InstallId = installId,\n                DeviceBinding = ComputeDeviceBinding(installId),\n                LastOnlineValidationUtc = DateTime.UtcNow\n            });\n        }'''
assert old in s
s=s.replace(old,new)
s=s.replace('''            if (!response.IsSuccessStatusCode)\n                return new(false, \"تعذر التحقق من الترخيص. تأكد من الاتصال بالإنترنت ثم حاول مرة أخرى.\");''','''            if (!response.IsSuccessStatusCode)\n                return new(false, \"تعذر الوصول إلى خدمة التراخيص الآن.\", null, false);''')
s=s.replace('''        catch\n        {\n            return new(false, \"لا يمكن الوصول إلى خادم التفعيل. يلزم اتصال بالإنترنت لتشغيل Geek POS.\");\n        }''','''        catch\n        {\n            return new(false, \"لا يوجد اتصال بخدمة التراخيص حاليًا.\", null, false);\n        }''')
insert='''\n    private string ComputeDeviceBinding(string installId)\n    {\n        var raw = $\"{GetDeviceFingerprint()}|{installId}|GeekPOS-local-v1\";\n        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(raw))).ToLowerInvariant();\n    }\n\n    private static void SaveState(ActivationState state)\n    {\n        File.WriteAllText(StatePath, JsonSerializer.Serialize(state));\n    }\n'''
idx=s.index('    private static string NormalizeSerial')
s=s[:idx]+insert+s[idx:]
p.write_text(s,encoding='utf-8-sig')

# ActivationPage: local activation opens immediately; online refresh is background only.
p=root/'Pages/ActivationPage.xaml.cs'
s=p.read_text(encoding='utf-8-sig')
old='''        if (result.Ok) App.MainWindow.ShowLogin();\n        else SerialBox.Focus(FocusState.Programmatic);'''
new='''        if (result.Ok)\n        {\n            App.MainWindow.ShowLogin();\n            _ = App.Services.Licensing.TryRefreshOnlineAsync();\n            return;\n        }\n        SerialBox.Focus(FocusState.Programmatic);'''
assert old in s
s=s.replace(old,new)
p.write_text(s,encoding='utf-8-sig')

# Settings UI: cash drawer option and test button.
p=root/'Pages/SettingsPage.xaml'
s=p.read_text(encoding='utf-8-sig')
old='''<Border Style=\"{StaticResource CardStyle}\"><StackPanel Spacing=\"10\"><TextBlock Text=\"الطابعة الحرارية\" Style=\"{StaticResource SubTitleStyle}\"/><TextBox x:Name=\"PrinterName\" Header=\"اسم الطابعة في Windows\" PlaceholderText=\"اتركه فارغًا لحفظ الفواتير كملفات\"/><ComboBox x:Name=\"ReceiptEncoding\" Header=\"ترميز التقارير النصية\" HorizontalAlignment=\"Stretch\"><ComboBoxItem Content=\"utf-8\"/><ComboBoxItem Content=\"windows-1256\"/><ComboBoxItem Content=\"ibm864\"/><ComboBoxItem Content=\"ibm720\"/></ComboBox><TextBlock Text=\"الفاتورة الرئيسية الجديدة تُطبع كصورة حرارية للحفاظ على تنسيق العربية والشعار والـ QR؛ الترميز هنا يستخدم في تقارير الورديات واليومية النصية.\" TextWrapping=\"Wrap\" FontSize=\"12\" Foreground=\"{StaticResource MutedTextBrush}\"/></StackPanel></Border>'''
new='''<Border Style=\"{StaticResource CardStyle}\"><StackPanel Spacing=\"10\"><TextBlock Text=\"الطابعة الحرارية ودرج النقدية\" Style=\"{StaticResource SubTitleStyle}\"/><TextBox x:Name=\"PrinterName\" Header=\"اسم الطابعة في Windows\" PlaceholderText=\"اتركه فارغًا لحفظ الفواتير كملفات\"/><CheckBox x:Name=\"CashDrawerAutoOpen\" Content=\"فتح درج النقدية تلقائيًا عند وجود دفع كاش\"/><Button Content=\"اختبار فتح درج النقدية\" Click=\"TestCashDrawer_Click\" Style=\"{StaticResource SoftButtonStyle}\" HorizontalAlignment=\"Right\"/><ComboBox x:Name=\"ReceiptEncoding\" Header=\"ترميز التقارير النصية\" HorizontalAlignment=\"Stretch\"><ComboBoxItem Content=\"utf-8\"/><ComboBoxItem Content=\"windows-1256\"/><ComboBoxItem Content=\"ibm864\"/><ComboBoxItem Content=\"ibm720\"/></ComboBox><TextBlock Text=\"يعمل فتح الدرج عن طريق منفذ RJ في الطابعة. الفاتورة الرئيسية تُطبع كصورة حرارية للحفاظ على تنسيق العربية والشعار والـ QR.\" TextWrapping=\"Wrap\" FontSize=\"12\" Foreground=\"{StaticResource MutedTextBrush}\"/></StackPanel></Border>'''
assert old in s
s=s.replace(old,new)
p.write_text(s,encoding='utf-8-sig')

p=root/'Pages/SettingsPage.xaml.cs'
s=p.read_text(encoding='utf-8-sig')
s=s.replace('''        PrinterName.Text = s.GetValueOrDefault(\"ReceiptPrinter\", \"\");\n        var enc = s.GetValueOrDefault(\"ReceiptEncoding\", \"utf-8\");''','''        PrinterName.Text = s.GetValueOrDefault(\"ReceiptPrinter\", \"\");\n        CashDrawerAutoOpen.IsChecked = !bool.TryParse(s.GetValueOrDefault(\"CashDrawerAutoOpen\", \"true\"), out var drawerEnabled) || drawerEnabled;\n        var enc = s.GetValueOrDefault(\"ReceiptEncoding\", \"utf-8\");''')
s=s.replace('''                [\"ReceiptPrinter\"] = PrinterName.Text.Trim(),\n                [\"ReceiptEncoding\"] = enc''','''                [\"ReceiptPrinter\"] = PrinterName.Text.Trim(),\n                [\"CashDrawerAutoOpen\"] = (CashDrawerAutoOpen.IsChecked == true).ToString().ToLowerInvariant(),\n                [\"ReceiptEncoding\"] = enc''')
insert='''\n    private async void TestCashDrawer_Click(object sender, RoutedEventArgs e)\n    {\n        try\n        {\n            if (!string.Equals((await App.Services.Settings.GetAsync(\"ReceiptPrinter\", \"\")).Trim(), PrinterName.Text.Trim(), StringComparison.Ordinal))\n                await App.Services.Settings.SetAsync(\"ReceiptPrinter\", PrinterName.Text.Trim());\n\n            var result = await App.Services.Receipts.OpenCashDrawerAsync();\n            Info.Severity = InfoBarSeverity.Success;\n            Info.Message = result;\n            Info.IsOpen = true;\n        }\n        catch (Exception ex)\n        {\n            Info.Severity = InfoBarSeverity.Error;\n            Info.Message = ex.Message;\n            Info.IsOpen = true;\n        }\n    }\n'''
idx=s.index('    private async void Backup_Click')
s=s[:idx]+insert+s[idx:]
p.write_text(s,encoding='utf-8-sig')

# ReceiptService: automatic cash drawer pulse and manual test.
p=root/'Services/ReceiptService.cs'
s=p.read_text(encoding='utf-8-sig')
old='''                var output = new List<byte>(raster.Length + 32);\n                output.AddRange(new byte[] { 0x1B, 0x40, 0x1B, 0x61, 0x01 });\n                output.AddRange(raster);\n                output.AddRange(new byte[] { 0x0A, 0x0A, 0x0A, 0x1D, 0x56, 0x00 });'''
new='''                var output = new List<byte>(raster.Length + 40);\n                output.AddRange(new byte[] { 0x1B, 0x40, 0x1B, 0x61, 0x01 });\n                var autoOpenDrawer = await settings.GetBoolAsync(\"CashDrawerAutoOpen\", true);\n                var hasCashPayment = sale.Payments.Any(p => p.Method == PaymentMethod.Cash || p.MethodKey.Equals(\"cash\", StringComparison.OrdinalIgnoreCase));\n                if (autoOpenDrawer && hasCashPayment)\n                    output.AddRange(CashDrawerKickCommand);\n                output.AddRange(raster);\n                output.AddRange(new byte[] { 0x0A, 0x0A, 0x0A, 0x1D, 0x56, 0x00 });'''
assert old in s
s=s.replace(old,new,1)
insert='''\n    private static readonly byte[] CashDrawerKickCommand = [0x1B, 0x70, 0x00, 0x32, 0xFA];\n\n    public async Task<string> OpenCashDrawerAsync()\n    {\n        var printer = await settings.GetAsync(\"ReceiptPrinter\", \"\");\n        if (string.IsNullOrWhiteSpace(printer))\n            throw new InvalidOperationException(\"حدد اسم الطابعة الحرارية في الإعدادات أولاً.\");\n\n        RawPrinter.Send(printer, new byte[] { 0x1B, 0x40, 0x1B, 0x70, 0x00, 0x32, 0xFA });\n        return $\"تم إرسال أمر فتح درج النقدية إلى {printer}\";\n    }\n'''
idx=s.index('    public Task<string> RenderSaleReceiptPreviewAsync')
s=s[:idx]+insert+s[idx:]
p.write_text(s,encoding='utf-8-sig')

# Installer helper now returns device binding generated from exactly the same device identity/install id.
p=root/'InstallerTools/GeekPOS-Activate.ps1'
s=p.read_text(encoding='utf-8-sig')
old="""  if (($null -ne $row) -and ($row.ok -eq $true) -and (-not [string]::IsNullOrWhiteSpace([string]$row.activation_token))) {\n    Write-Result ('OK|' + [string]$row.activation_token + '|' + $installId) 0\n  }"""
new="""  if (($null -ne $row) -and ($row.ok -eq $true) -and (-not [string]::IsNullOrWhiteSpace([string]$row.activation_token))) {\n    $bindingRaw = \"$deviceIdentity|$installId|GeekPOS-local-v1\"\n    $sha = [System.Security.Cryptography.SHA256]::Create()\n    try {\n      $bindingBytes = $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($bindingRaw))\n      $deviceBinding = ([System.BitConverter]::ToString($bindingBytes)).Replace('-', '').ToLowerInvariant()\n    } finally { $sha.Dispose() }\n    Write-Result ('OK|' + [string]$row.activation_token + '|' + $installId + '|' + $deviceBinding) 0\n  }"""
assert old in s
s=s.replace(old,new)
p.write_text(s,encoding='utf-8-sig')

# Installer parses binding and stores it in activation.dat.
p=root/'installer.iss'
s=p.read_text(encoding='utf-8-sig')
s=s.replace('''  ActivationToken: String;\n  InstallId: String;''','''  ActivationToken: String;\n  InstallId: String;\n  DeviceBinding: String;''')
s=s.replace('''  ScriptPath, OutputPath, PowerShellExe, Params, Response, Rest: String;\n  Raw: AnsiString;\n  ResultCode, Sep: Integer;''','''  ScriptPath, OutputPath, PowerShellExe, Params, Response, Rest, Remaining: String;\n  Raw: AnsiString;\n  ResultCode, Sep, Sep2: Integer;''')
s=s.replace('''  ActivationToken := '';\n  InstallId := '';''','''  ActivationToken := '';\n  InstallId := '';\n  DeviceBinding := '';''')
old='''    ActivationToken := Copy(Rest, 1, Sep - 1);\n    InstallId := Copy(Rest, Sep + 1, Length(Rest) - Sep);\n\n    if (Length(ActivationToken) > 20) and (Length(InstallId) > 10) then\n    begin\n      Result := True;\n      Exit;\n    end;'''
new='''    ActivationToken := Copy(Rest, 1, Sep - 1);\n    Remaining := Copy(Rest, Sep + 1, Length(Rest) - Sep);\n    Sep2 := Pos('|', Remaining);\n    if Sep2 <= 1 then\n    begin\n      MsgBox('رد التفعيل غير مكتمل.', mbError, MB_OK);\n      Exit;\n    end;\n    InstallId := Copy(Remaining, 1, Sep2 - 1);\n    DeviceBinding := Copy(Remaining, Sep2 + 1, Length(Remaining) - Sep2);\n\n    if (Length(ActivationToken) > 20) and (Length(InstallId) > 10) and (Length(DeviceBinding) = 64) then\n    begin\n      Result := True;\n      Exit;\n    end;'''
assert old in s
s=s.replace(old,new)
s=s.replace('''    if (ActivationToken = '') or (InstallId = '') then\n      RaiseException('Geek POS activation was not completed.');\n\n    State := '{\"ActivationToken\":\"' + ActivationToken +\n      '\",\"InstallId\":\"' + InstallId + '\"}';''','''    if (ActivationToken = '') or (InstallId = '') or (DeviceBinding = '') then\n      RaiseException('Geek POS activation was not completed.');\n\n    State := '{\"ActivationToken\":\"' + ActivationToken +\n      '\",\"InstallId\":\"' + InstallId +\n      '\",\"DeviceBinding\":\"' + DeviceBinding + '\"}';''')
s=s.replace('2.0.5','2.0.6')
p.write_text(s,encoding='utf-8-sig')

# Project version.
p=root/'SweetsPOS.csproj'
s=p.read_text(encoding='utf-8-sig').replace('2.0.5','2.0.6')
p.write_text(s,encoding='utf-8-sig')

# Sanity assertions.
lic=(root/'Services/LicenseService.cs').read_text(encoding='utf-8-sig')
assert 'ValidateLocalAsync' in lic and 'InvokeAsync(\"validate_license\"' in lic and 'Offline/server unavailable must never disable' in lic
assert 'ComputeDeviceBinding' in lic and 'File.Delete(StatePath)' in lic
act=(root/'Pages/ActivationPage.xaml.cs').read_text(encoding='utf-8-sig')
assert 'ShowLogin();' in act and 'TryRefreshOnlineAsync' in act
rec=(root/'Services/ReceiptService.cs').read_text(encoding='utf-8-sig')
assert 'CashDrawerKickCommand' in rec and 'OpenCashDrawerAsync' in rec and 'hasCashPayment' in rec
setx=(root/'Pages/SettingsPage.xaml').read_text(encoding='utf-8-sig')
assert 'CashDrawerAutoOpen' in setx and 'اختبار فتح درج النقدية' in setx
inst=(root/'installer.iss').read_text(encoding='utf-8-sig')
assert 'DeviceBinding' in inst and '2.0.6' in inst
print('v2.0.6 patch applied')
