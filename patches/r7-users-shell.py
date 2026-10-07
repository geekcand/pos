from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()

users = r'''using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using SweetsPOS.Core;

namespace SweetsPOS.Pages;

public sealed partial class UsersPage : Page
{
    private sealed record RoleOption(UserRole Value, string Label);
    private List<User> _users = [];

    public UsersPage() { InitializeComponent(); Loaded += async (_, _) => await RefreshAsync(); }

    private User Current => App.Services.Session.CurrentUser ?? throw new InvalidOperationException("لا يوجد مستخدم مسجل.");

    private RoleOption[] AllowedRoles(User? source)
    {
        if (RolePermissions.IsReservedAdministrator(source ?? new User())) return [new(UserRole.Administrator, "Administrator")];
        if (Current.Role == UserRole.Administrator)
            return [new(UserRole.Cashier, "كاشير"), new(UserRole.Supervisor, "مشرف"), new(UserRole.Admin, "أدمن")];
        if (Current.Role == UserRole.Admin)
            return [new(UserRole.Cashier, "كاشير"), new(UserRole.Supervisor, "مشرف")];
        return [new(UserRole.Cashier, "كاشير")];
    }

    private async Task RefreshAsync()
    {
        var all = await App.Services.Users.GetAllAsync();
        _users = Current.Role == UserRole.Administrator
            ? all
            : all.Where(x => x.Role < Current.Role && x.Role != UserRole.Administrator).ToList();
        List.ItemsSource = _users;
    }

    private async void Add_Click(object sender, RoutedEventArgs e)
    {
        if (!await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.ManageUsers, "إضافة مستخدم جديد")) return;
        if (await EditAsync(null)) await RefreshAsync();
    }

    private async void Edit_Click(object sender, RoutedEventArgs e)
    {
        if (!await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.ManageUsers, "تعديل مستخدم وصلاحياته")) return;
        if (sender is Button b && int.TryParse(b.Tag?.ToString(), out var id) && _users.FirstOrDefault(x => x.Id == id) is { } u && await EditAsync(u)) await RefreshAsync();
    }

    private async Task<bool> EditAsync(User? source)
    {
        var reserved = source is not null && RolePermissions.IsReservedAdministrator(source);
        var roles = AllowedRoles(source);
        var username = new TextBox { Header = "اسم المستخدم", Text = source?.Username ?? "", IsEnabled = !reserved };
        var display = new TextBox { Header = "الاسم الظاهر", Text = source?.DisplayName ?? "", IsEnabled = !reserved };
        var role = new ComboBox { Header = "الدور الأساسي", ItemsSource = roles, DisplayMemberPath = "Label", HorizontalAlignment = HorizontalAlignment.Stretch, IsEnabled = !reserved };
        role.SelectedItem = roles.FirstOrDefault(x => x.Value == (source?.Role ?? roles[0].Value)) ?? roles[0];
        var pin = new PasswordBox { Header = source is null ? "الرقم السري" : "رقم سري جديد (اتركه فارغًا للإبقاء على الحالي)", PasswordRevealMode = PasswordRevealMode.Peek };
        var active = new CheckBox { Content = "المستخدم نشط", IsChecked = source?.IsActive ?? true, IsEnabled = !reserved };

        var actorPermissions = RolePermissions.Effective(Current);
        var selected = reserved ? RolePermissions.Defaults(UserRole.Administrator)
            : source is not null ? RolePermissions.Effective(source)
            : RolePermissions.Defaults(roles[0].Value);
        var checks = new Dictionary<Permission, CheckBox>();
        var permissionsPanel = new StackPanel { Spacing = 6, FlowDirection = FlowDirection.RightToLeft };
        foreach (var group in RolePermissions.Definitions.GroupBy(x => x.Group))
        {
            permissionsPanel.Children.Add(new TextBlock
            {
                Text = group.Key, FontWeight = Microsoft.UI.Text.FontWeights.Bold, Margin = new Thickness(0, 10, 0, 2),
                Foreground = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["AccentBrushSoft"]
            });
            foreach (var item in group)
            {
                var canDelegate = Current.Role == UserRole.Administrator || actorPermissions.Contains(item.Permission);
                var cb = new CheckBox
                {
                    Content = item.Sensitive ? $"{item.Label}  🔒" : item.Label,
                    IsChecked = reserved || selected.Contains(item.Permission), Tag = item.Permission,
                    IsEnabled = !reserved && canDelegate, HorizontalAlignment = HorizontalAlignment.Stretch
                };
                checks[item.Permission] = cb;
                permissionsPanel.Children.Add(cb);
            }
        }

        var permissionScroll = new ScrollViewer { MaxHeight = 430, Content = permissionsPanel, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
        var resetDefaults = new Button { Content = "تطبيق الصلاحيات الافتراضية للدور", Style = (Style)Application.Current.Resources["SoftButtonStyle"], IsEnabled = !reserved };
        void ApplyRoleDefaults()
        {
            if (role.SelectedItem is not RoleOption ro) return;
            var defaults = RolePermissions.Defaults(ro.Value);
            foreach (var pair in checks)
            {
                var canDelegate = Current.Role == UserRole.Administrator || actorPermissions.Contains(pair.Key);
                pair.Value.IsChecked = canDelegate && defaults.Contains(pair.Key);
            }
        }
        resetDefaults.Click += (_, _) => ApplyRoleDefaults();
        role.SelectionChanged += (_, _) => { if (source is null) ApplyRoleDefaults(); };

        var securityNote = new TextBlock
        {
            Text = reserved
                ? "Administrator هو مالك النظام: كل الصلاحيات متاحة دائمًا ولا يمكن إيقاف الحساب أو خفض دوره."
                : "عدم تحديد صلاحية ظهور يخفي الجزء بالكامل. عدم تحديد صلاحية إجراء يجعل التنفيذ يطلب PIN مستخدم أعلى لديه نفس الصلاحية.",
            TextWrapping = TextWrapping.Wrap,
            Foreground = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["MutedTextBrush"], FontSize = 12
        };

        var panel = new StackPanel { Width = 560, Spacing = 9, FlowDirection = FlowDirection.RightToLeft };
        panel.Children.Add(username); panel.Children.Add(display); panel.Children.Add(role); panel.Children.Add(pin); panel.Children.Add(active);
        panel.Children.Add(new TextBlock { Text = "الصلاحيات", FontSize = 18, FontWeight = Microsoft.UI.Text.FontWeights.Bold, Margin = new Thickness(0,8,0,0) });
        panel.Children.Add(resetDefaults); panel.Children.Add(permissionScroll); panel.Children.Add(securityNote);

        var d = new ContentDialog
        {
            XamlRoot = XamlRoot, RequestedTheme = ElementTheme.Dark,
            Title = reserved ? "حساب Administrator" : source is null ? "إضافة مستخدم وصلاحياته" : "تعديل المستخدم والصلاحيات",
            Content = panel, PrimaryButtonText = "حفظ", CloseButtonText = "إلغاء", FlowDirection = FlowDirection.RightToLeft
        };
        if (await d.ShowAsync() != ContentDialogResult.Primary) return false;
        try
        {
            if (pin.Password.Length > 0 && (pin.Password.Length < 4 || pin.Password.Any(c => !char.IsDigit(c)))) throw new InvalidOperationException("يجب أن يحتوي الرقم السري على 4 أرقام على الأقل.");
            var targetRole = reserved ? UserRole.Administrator : role.SelectedItem is RoleOption ro ? ro.Value : UserRole.Cashier;
            var permissions = reserved ? RolePermissions.Defaults(UserRole.Administrator) : checks.Where(x => x.Value.IsChecked == true).Select(x => x.Key).ToList();
            await App.Services.Users.SaveAsync(source?.Id ?? 0, reserved ? "administrator" : username.Text, reserved ? "Administrator" : display.Text, targetRole, reserved || active.IsChecked == true, pin.Password, permissions);
            return true;
        }
        catch (Exception ex) { await PageHelpers.MessageAsync(XamlRoot, "تعذر حفظ المستخدم", ex.Message); return false; }
    }
}
'''

shell = r'''using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media.Imaging;
using Windows.Storage;
using SweetsPOS.Core;

namespace SweetsPOS.Pages;

public sealed partial class ShellPage : Page
{
    public ShellPage()
    {
        InitializeComponent();
        Loaded += ShellPage_Loaded;
        App.Services.Session.Changed += Session_Changed;
        Unloaded += (_, _) => App.Services.Session.Changed -= Session_Changed;
    }

    private async void ShellPage_Loaded(object sender, RoutedEventArgs e)
    {
        ApplyPermissions();
        await LoadBrandAsync();
        Navigate(ResolveHomeTag());
    }

    private async Task LoadBrandAsync()
    {
        try
        {
            var all = await App.Services.Settings.GetAllAsync();
            BrandNameText.Text = all.GetValueOrDefault("StoreName", "اسم المؤسسة");
            var logoPath = all.GetValueOrDefault("BrandLogoPath", "");
            if (!string.IsNullOrWhiteSpace(logoPath) && File.Exists(logoPath))
            {
                var file = await StorageFile.GetFileFromPathAsync(logoPath);
                using var stream = await file.OpenReadAsync();
                var bmp = new BitmapImage();
                await bmp.SetSourceAsync(stream);
                BrandLogoImage.Source = bmp;
            }
            else BrandLogoImage.Source = new BitmapImage(new Uri("ms-appx:///Assets/GeekPOS.png"));
        }
        catch
        {
            BrandNameText.Text = "اسم المؤسسة";
            BrandLogoImage.Source = new BitmapImage(new Uri("ms-appx:///Assets/GeekPOS.png"));
        }
    }

    private void Session_Changed(object? sender, EventArgs e) => DispatcherQueue.TryEnqueue(ApplyPermissions);

    private IEnumerable<Button> NavButtons()
    {
        yield return PosNav; yield return ShiftsNav; yield return DashboardNav;
        yield return CategoriesNav; yield return ProductsNav; yield return PaymentMethodsNav; yield return UsersNav; yield return ReportsNav;
        yield return ExpensesNav; yield return RefundsNav; yield return AdminShiftsNav; yield return ReceiptDesignerNav; yield return AuditNav; yield return OnlineNav; yield return SettingsNav;
    }

    private void ApplyPermissions()
    {
        var session = App.Services.Session;
        var user = session.CurrentUser;
        if (user is null) return;
        var role = user.Role switch { UserRole.Administrator => "Administrator", UserRole.Admin => "أدمن", UserRole.Supervisor => "مشرف", _ => "كاشير" };
        UserText.Text = $"{user.DisplayName} • {role}";
        ShiftText.Text = session.CurrentShift is null ? "لا توجد وردية مفتوحة" : $"وردية #{session.CurrentShift.Id} • مفتوحة";
        PosNav.Visibility = session.Can(Permission.AccessCashier) ? Visibility.Visible : Visibility.Collapsed;
        ShiftsNav.Visibility = session.Can(Permission.AccessShifts) ? Visibility.Visible : Visibility.Collapsed;
        CategoriesNav.Visibility = session.Can(Permission.AccessCategories) ? Visibility.Visible : Visibility.Collapsed;
        ProductsNav.Visibility = session.Can(Permission.AccessProducts) ? Visibility.Visible : Visibility.Collapsed;
        PaymentMethodsNav.Visibility = session.Can(Permission.AccessPaymentMethods) ? Visibility.Visible : Visibility.Collapsed;
        UsersNav.Visibility = session.Can(Permission.AccessUsers) ? Visibility.Visible : Visibility.Collapsed;
        ReportsNav.Visibility = session.Can(Permission.AccessReports) ? Visibility.Visible : Visibility.Collapsed;
        ExpensesNav.Visibility = session.Can(Permission.AccessExpenses) ? Visibility.Visible : Visibility.Collapsed;
        RefundsNav.Visibility = session.Can(Permission.AccessRefunds) ? Visibility.Visible : Visibility.Collapsed;
        AdminShiftsNav.Visibility = session.Can(Permission.AccessShiftAdmin) ? Visibility.Visible : Visibility.Collapsed;
        ReceiptDesignerNav.Visibility = session.Can(Permission.AccessReceiptDesigner) ? Visibility.Visible : Visibility.Collapsed;
        AuditNav.Visibility = session.Can(Permission.AccessAudit) ? Visibility.Visible : Visibility.Collapsed;
        OnlineNav.Visibility = session.Can(Permission.AccessOnline) ? Visibility.Visible : Visibility.Collapsed;
        SettingsNav.Visibility = session.Can(Permission.AccessSettings) ? Visibility.Visible : Visibility.Collapsed;
        DashboardNav.Visibility = AnyAdminModuleAllowed() ? Visibility.Visible : Visibility.Collapsed;
    }

    private bool AnyAdminModuleAllowed()
    {
        var s = App.Services.Session;
        return s.Can(Permission.AccessAdminDashboard) || s.Can(Permission.AccessCategories) || s.Can(Permission.AccessProducts) ||
               s.Can(Permission.AccessPaymentMethods) || s.Can(Permission.AccessUsers) || s.Can(Permission.AccessReports) ||
               s.Can(Permission.AccessExpenses) || s.Can(Permission.AccessRefunds) || s.Can(Permission.AccessShiftAdmin) ||
               s.Can(Permission.AccessReceiptDesigner) || s.Can(Permission.AccessAudit) || s.Can(Permission.AccessOnline) || s.Can(Permission.AccessSettings);
    }

    private string ResolveHomeTag()
    {
        var s = App.Services.Session;
        if (s.CurrentShift is not null && s.Can(Permission.AccessCashier)) return "pos";
        if (s.Can(Permission.AccessShifts)) return "shifts";
        if (s.Can(Permission.AccessCashier)) return "pos";
        return FirstAllowedAdminTag() ?? "dashboard";
    }

    private string? FirstAllowedAdminTag()
    {
        var s = App.Services.Session;
        if (s.Can(Permission.AccessAdminDashboard)) return "dashboard";
        if (s.Can(Permission.AccessCategories)) return "categories";
        if (s.Can(Permission.AccessProducts)) return "products";
        if (s.Can(Permission.AccessPaymentMethods)) return "payments";
        if (s.Can(Permission.AccessUsers)) return "users";
        if (s.Can(Permission.AccessReports)) return "reports";
        if (s.Can(Permission.AccessExpenses)) return "expenses";
        if (s.Can(Permission.AccessRefunds)) return "refunds";
        if (s.Can(Permission.AccessShiftAdmin)) return "shiftadmin";
        if (s.Can(Permission.AccessReceiptDesigner)) return "receipt";
        if (s.Can(Permission.AccessAudit)) return "audit";
        if (s.Can(Permission.AccessOnline)) return "online";
        if (s.Can(Permission.AccessSettings)) return "settings";
        return null;
    }

    private bool CanNavigate(string tag)
    {
        var s = App.Services.Session;
        return tag switch
        {
            "pos" => s.Can(Permission.AccessCashier),
            "shifts" => s.Can(Permission.AccessShifts),
            "dashboard" => s.Can(Permission.AccessAdminDashboard),
            "categories" => s.Can(Permission.AccessCategories),
            "products" => s.Can(Permission.AccessProducts),
            "payments" => s.Can(Permission.AccessPaymentMethods),
            "users" => s.Can(Permission.AccessUsers),
            "reports" => s.Can(Permission.AccessReports),
            "expenses" => s.Can(Permission.AccessExpenses),
            "refunds" => s.Can(Permission.AccessRefunds),
            "shiftadmin" => s.Can(Permission.AccessShiftAdmin),
            "receipt" => s.Can(Permission.AccessReceiptDesigner),
            "audit" => s.Can(Permission.AccessAudit),
            "online" => s.Can(Permission.AccessOnline),
            "settings" => s.Can(Permission.AccessSettings),
            _ => false
        };
    }

    private void NavButton_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button b && b.Tag is string tag) Navigate(tag == "dashboard" && !CanNavigate("dashboard") ? FirstAllowedAdminTag() ?? tag : tag);
    }

    private void SetActiveButton(string tag)
    {
        var normal = (Style)Application.Current.Resources["TopNavButtonStyle"];
        var active = (Style)Application.Current.Resources["TopNavActiveButtonStyle"];
        foreach (var b in NavButtons()) b.Style = (b.Tag as string) == tag ? active : normal;
    }

    private void UpdateAdminSidebar(string tag)
    {
        var adminTags = new HashSet<string> { "dashboard", "categories", "products", "payments", "users", "reports", "expenses", "refunds", "shiftadmin", "receipt", "audit", "online", "settings" };
        var show = adminTags.Contains(tag);
        AdminSidebar.Visibility = show ? Visibility.Visible : Visibility.Collapsed;
        AdminSidebarColumn.Width = show ? new GridLength(200) : new GridLength(0);
    }

    private void Navigate(string tag)
    {
        if (!CanNavigate(tag))
        {
            if (tag == "dashboard") tag = FirstAllowedAdminTag() ?? ResolveHomeTag();
            if (!CanNavigate(tag)) return;
        }
        var type = tag switch
        {
            "dashboard" => typeof(DashboardPage), "pos" => typeof(PosPage), "shifts" => typeof(ShiftsPage),
            "expenses" => typeof(ExpensesPage), "refunds" => typeof(RefundsPage), "products" => typeof(ProductsPage),
            "categories" => typeof(CategoriesPage), "payments" => typeof(PaymentMethodsPage), "reports" => typeof(ReportsPage), "users" => typeof(UsersPage),
            "shiftadmin" => typeof(ShiftsPage), "receipt" => typeof(ReceiptDesignerPage),
            "audit" => typeof(AuditPage), "online" => typeof(OnlinePage), "settings" => typeof(SettingsPage), _ => typeof(PosPage)
        };
        if (ContentFrame.CurrentSourcePageType != type) ContentFrame.Navigate(type);
        UpdateAdminSidebar(tag);
        SetActiveButton(tag);
        ApplyPermissions();
    }

    private async void Logout_Click(object sender, RoutedEventArgs e)
    {
        var shift = App.Services.Session.CurrentShift;
        if (shift is not null)
        {
            var confirm = new ContentDialog
            {
                XamlRoot = XamlRoot, RequestedTheme = ElementTheme.Dark, Title = "تسجيل الخروج",
                Content = $"سيتم تسجيل خروج المستخدم وترك الوردية #{shift.Id} مفتوحة. عند تسجيل الدخول مرة أخرى ستعود نفس الوردية تلقائيًا.",
                PrimaryButtonText = "تسجيل خروج", CloseButtonText = "إلغاء", DefaultButton = ContentDialogButton.Primary
            };
            if (await confirm.ShowAsync() != ContentDialogResult.Primary) return;
        }
        await App.Services.Auth.LogoutAsync();
        App.MainWindow.ShowLogin();
    }
}
'''

(root/"Pages/UsersPage.xaml.cs").write_text(users,encoding="utf-8-sig")
(root/"Pages/ShellPage.xaml.cs").write_text(shell,encoding="utf-8-sig")
print("R7 users and shell applied")
