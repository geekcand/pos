from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
p=root/'Pages/SettingsPage.xaml.cs'
s=p.read_text(encoding='utf-8-sig')
if 'private async void ChooseBrandLogo_Click' not in s:
    anchor='    private async void Backup_Click(object sender, RoutedEventArgs e)\n'
    if anchor not in s:
        raise SystemExit('Settings backup anchor missing')
    methods='''    private async void ChooseBrandLogo_Click(object sender, RoutedEventArgs e)
    {
        var picker = new FileOpenPicker(); picker.FileTypeFilter.Add(".png"); picker.FileTypeFilter.Add(".jpg"); picker.FileTypeFilter.Add(".jpeg"); picker.FileTypeFilter.Add(".bmp");
        var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.MainWindow); WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);
        var file = await picker.PickSingleFileAsync(); if (file is null) return;
        var folderPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SweetsPOS", "BrandAssets");
        Directory.CreateDirectory(folderPath); var folder = await StorageFolder.GetFolderFromPathAsync(folderPath);
        var copied = await file.CopyAsync(folder, $"brand-{DateTime.Now:yyyyMMddHHmmss}{Path.GetExtension(file.Name)}", NameCollisionOption.GenerateUniqueName);
        BrandLogoPath.Text = copied.Path;
    }

    private void RemoveBrandLogo_Click(object sender, RoutedEventArgs e) => BrandLogoPath.Text = "";

'''
    s=s.replace(anchor, methods+anchor,1)
p.write_text(s,encoding='utf-8-sig')
print('v3.0.4 settings brand-logo hotfix applied')
