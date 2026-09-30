using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Windows.Storage.Pickers;
using Windows.Storage;

namespace SweetsPOS.Pages;

public sealed partial class SettingsPage : Page
{
    public SettingsPage()
    {
        InitializeComponent();
        Loaded += SettingsPage_Loaded;
    }

    private async void SettingsPage_Loaded(object sender, RoutedEventArgs e)
    {
        var s = await App.Services.Settings.GetAllAsync();
        StoreName.Text = s.GetValueOrDefault("StoreName", "اسم المؤسسة");
        StorePhone.Text = s.GetValueOrDefault("StorePhone", "");
        StoreAddress.Text = s.GetValueOrDefault("StoreAddress", "");
        Currency.Text = "جنيه";
        BrandLogoPath.Text = s.GetValueOrDefault("BrandLogoPath", "");
        ReceiptFooter.Text = s.GetValueOrDefault("ReceiptFooter", "شكراً لزيارتكم");
        TaxEnabled.IsChecked = bool.TryParse(s.GetValueOrDefault("TaxEnabled"), out var te) && te;
        TaxPercent.Value = double.TryParse(s.GetValueOrDefault("TaxPercent"), out var tp) ? tp : 0;
        MaxDiscount.Value = double.TryParse(s.GetValueOrDefault("MaxCashierDiscountPercent"), out var md) ? md : 5;
        PrinterName.Text = s.GetValueOrDefault("ReceiptPrinter", "");
        var enc = s.GetValueOrDefault("ReceiptEncoding", "utf-8");
        ReceiptEncoding.SelectedIndex = enc switch
        {
            "windows-1256" => 1,
            "ibm864" => 2,
            "ibm720" => 3,
            _ => 0
        };
    }

    private async void Save_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            var enc = (ReceiptEncoding.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "utf-8";
            await App.Services.Settings.SetManyAsync(new Dictionary<string, string>
            {
                ["StoreName"] = StoreName.Text.Trim(),
                ["StorePhone"] = StorePhone.Text.Trim(),
                ["StoreAddress"] = StoreAddress.Text.Trim(),
                ["Currency"] = "جنيه",
                ["BrandLogoPath"] = BrandLogoPath.Text.Trim(),
                ["ReceiptFooter"] = ReceiptFooter.Text.Trim(),
                ["TaxEnabled"] = (TaxEnabled.IsChecked == true).ToString().ToLowerInvariant(),
                ["TaxPercent"] = PageHelpers.DecimalFrom(TaxPercent).ToString(),
                ["MaxCashierDiscountPercent"] = PageHelpers.DecimalFrom(MaxDiscount).ToString(),
                ["ReceiptPrinter"] = PrinterName.Text.Trim(),
                ["ReceiptEncoding"] = enc
            });

            Info.Severity = InfoBarSeverity.Success;
            Info.Message = "تم حفظ الإعدادات.";
            Info.IsOpen = true;
        }
        catch (Exception ex)
        {
            Info.Severity = InfoBarSeverity.Error;
            Info.Message = ex.Message;
            Info.IsOpen = true;
        }
    }

    private async void ChooseBrandLogo_Click(object sender, RoutedEventArgs e)
    {
        var picker = new FileOpenPicker();
        picker.FileTypeFilter.Add(".png");
        picker.FileTypeFilter.Add(".jpg");
        picker.FileTypeFilter.Add(".jpeg");
        picker.FileTypeFilter.Add(".bmp");

        var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.MainWindow);
        WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);

        var file = await picker.PickSingleFileAsync();
        if (file is null) return;

        var folderPath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "SweetsPOS",
            "BrandAssets");

        Directory.CreateDirectory(folderPath);
        var folder = await StorageFolder.GetFolderFromPathAsync(folderPath);
        var copied = await file.CopyAsync(
            folder,
            $"brand-{DateTime.Now:yyyyMMddHHmmss}{Path.GetExtension(file.Name)}",
            NameCollisionOption.GenerateUniqueName);

        BrandLogoPath.Text = copied.Path;
    }

    private void RemoveBrandLogo_Click(object sender, RoutedEventArgs e)
        => BrandLogoPath.Text = "";

    private async void Backup_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            var path = await App.Services.Backups.CreateAsync();
            Info.Severity = InfoBarSeverity.Success;
            Info.Message = $"تم إنشاء النسخة الاحتياطية: {path}";
            Info.IsOpen = true;
        }
        catch (Exception ex)
        {
            Info.Severity = InfoBarSeverity.Error;
            Info.Message = ex.Message;
            Info.IsOpen = true;
        }
    }

    private async void Restore_Click(object sender, RoutedEventArgs e)
    {
        if (App.Services.Session.CurrentShift is not null)
        {
            await PageHelpers.MessageAsync(
                XamlRoot,
                "أغلق الوردية أولاً",
                "لا يمكن استرجاع قاعدة البيانات أثناء وجود وردية مفتوحة.");
            return;
        }

        var picker = new FileOpenPicker();
        picker.FileTypeFilter.Add(".db");
        picker.FileTypeFilter.Add(".sqlite");

        var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.MainWindow);
        WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);

        var file = await picker.PickSingleFileAsync();
        if (file is null) return;

        var confirm = new ContentDialog
        {
            XamlRoot = XamlRoot,
            RequestedTheme = ElementTheme.Dark,
            Title = "استرجاع النسخة الاحتياطية؟",
            Content = "سيتم أخذ نسخة احتياطية من قاعدة البيانات الحالية ثم استبدالها. أعد تشغيل البرنامج بعد الاسترجاع.",
            PrimaryButtonText = "استرجاع",
            CloseButtonText = "إلغاء"
        };

        if (await confirm.ShowAsync() != ContentDialogResult.Primary) return;

        try
        {
            await App.Services.Backups.RestoreAsync(file.Path);
            Info.Severity = InfoBarSeverity.Success;
            Info.Message = "تم استرجاع النسخة. أعد تشغيل البرنامج قبل المتابعة.";
            Info.IsOpen = true;
        }
        catch (Exception ex)
        {
            Info.Severity = InfoBarSeverity.Error;
            Info.Message = ex.Message;
            Info.IsOpen = true;
        }
    }
}
