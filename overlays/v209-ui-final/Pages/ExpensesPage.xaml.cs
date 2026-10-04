using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace SweetsPOS.Pages;

public sealed partial class ExpensesPage : Page
{
    public ExpensesPage() { InitializeComponent(); Loaded += async (_, _) => await RefreshAsync(); }
    private async Task RefreshAsync()
    {
        var rows = await App.Services.Shifts.GetExpensesAsync(App.Services.Session.CurrentShift?.Id);
        List.ItemsSource = rows;
        EmptyState.Visibility = rows.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
    }
    private async void Add_Click(object sender, RoutedEventArgs e)
    {
        if (App.Services.Session.CurrentShift is null) { await PageHelpers.MessageAsync(XamlRoot, "يجب فتح وردية", "يجب تسجيل المصروف داخل وردية مفتوحة."); return; }
        var amount = new NumberBox { Header = "المبلغ", Minimum = 0.01, Value = 0, SpinButtonPlacementMode = NumberBoxSpinButtonPlacementMode.Hidden, FlowDirection = FlowDirection.RightToLeft };
        var category = new ComboBox { Header = "التصنيف", ItemsSource = new[] { "مشتريات", "توصيل", "صيانة", "مرافق", "عهدة", "أخرى" }, SelectedIndex = 0, HorizontalAlignment = HorizontalAlignment.Stretch, FlowDirection = FlowDirection.RightToLeft };
        var reason = new TextBox { Header = "السبب", AcceptsReturn = true, Height = 90, FlowDirection = FlowDirection.RightToLeft, TextAlignment = TextAlignment.Right };
        var panel = new StackPanel { Spacing = 10, Width = 380, FlowDirection = FlowDirection.RightToLeft }; panel.Children.Add(amount); panel.Children.Add(category); panel.Children.Add(reason);
        var d = new ContentDialog { XamlRoot = XamlRoot, Title = "تسجيل مصروف", Content = panel, PrimaryButtonText = "حفظ", CloseButtonText = "إلغاء" };
        if (await d.ShowAsync() != ContentDialogResult.Primary) return;
        try { await App.Services.Shifts.AddExpenseAsync(PageHelpers.DecimalFrom(amount), category.SelectedItem?.ToString() ?? "أخرى", reason.Text); await RefreshAsync(); }
        catch (Exception ex) { await PageHelpers.MessageAsync(XamlRoot, "تعذر حفظ المصروف", ex.Message); }
    }
}
