using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace SweetsPOS.Pages;

public sealed partial class OnlinePage : Page
{
    public OnlinePage()
    {
        InitializeComponent();
        Loaded += OnlinePage_Loaded;
    }

    private async void OnlinePage_Loaded(object sender, RoutedEventArgs e)
    {
        var s = await App.Services.Settings.GetAllAsync();
        OnlineEnabled.IsChecked = bool.TryParse(s.GetValueOrDefault("OnlineEnabled"), out var enabled) && enabled;
        SupabaseUrl.Text = s.GetValueOrDefault("OnlineSupabaseUrl", "");
        AnonKey.Password = s.GetValueOrDefault("OnlineSupabaseAnonKey", "");
        StoreId.Text = s.GetValueOrDefault("OnlineStoreId", "main");
        SyncMinutes.Value = double.TryParse(s.GetValueOrDefault("OnlineSyncMinutes"), out var mins) ? mins : 5;
        OnlineEmail.Text = s.GetValueOrDefault("OnlineEmail", "");
        OnlinePassword.Password = s.GetValueOrDefault("OnlinePassword", "");
        AutoUpdates.IsChecked = !bool.TryParse(s.GetValueOrDefault("OnlineAutoApplyUpdates"), out var au) || au;
        StatusText.Text = App.Services.Online.LastStatus;
    }

    private async Task SaveAsync(bool notify = true)
    {
        await App.Services.Settings.SetManyAsync(new Dictionary<string, string>
        {
            ["OnlineEnabled"] = (OnlineEnabled.IsChecked == true).ToString().ToLowerInvariant(),
            ["OnlineSupabaseUrl"] = SupabaseUrl.Text.Trim().TrimEnd('/'),
            ["OnlineSupabaseAnonKey"] = AnonKey.Password.Trim(),
            ["OnlineStoreId"] = string.IsNullOrWhiteSpace(StoreId.Text) ? "main" : StoreId.Text.Trim(),
            ["OnlineSyncMinutes"] = Math.Clamp((int)Math.Round(SyncMinutes.Value), 1, 120).ToString(),
            ["OnlineEmail"] = OnlineEmail.Text.Trim(),
            ["OnlinePassword"] = OnlinePassword.Password,
            ["OnlineAutoApplyUpdates"] = (AutoUpdates.IsChecked == true).ToString().ToLowerInvariant()
        });
        if (notify) ShowInfo("تم حفظ إعدادات الأونلاين.", InfoBarSeverity.Success);
    }

    private void ShowInfo(string message, InfoBarSeverity severity)
    {
        Info.Severity = severity;
        Info.Message = message;
        Info.IsOpen = true;
        StatusText.Text = App.Services.Online.LastStatus;
    }

    private async void Save_Click(object sender, RoutedEventArgs e)
    {
        try { await SaveAsync(); }
        catch (Exception ex) { ShowInfo(ex.Message, InfoBarSeverity.Error); }
    }

    private async void Test_Click(object sender, RoutedEventArgs e)
    {
        try { await SaveAsync(false); var msg = await App.Services.Online.TestConnectionAsync(); ShowInfo(msg, InfoBarSeverity.Success); }
        catch (Exception ex) { ShowInfo(ex.Message, InfoBarSeverity.Error); }
    }

    private async void Sync_Click(object sender, RoutedEventArgs e)
    {
        try { await SaveAsync(false); var msg = await App.Services.Online.SyncNowAsync(); ShowInfo(msg, InfoBarSeverity.Success); }
        catch (Exception ex) { ShowInfo(ex.Message, InfoBarSeverity.Error); }
    }

    private async void Updates_Click(object sender, RoutedEventArgs e)
    {
        try { await SaveAsync(false); var msg = await App.Services.Online.CheckAndApplyUpdatesAsync(); ShowInfo(msg, InfoBarSeverity.Success); }
        catch (Exception ex) { ShowInfo(ex.Message, InfoBarSeverity.Error); }
    }
}
