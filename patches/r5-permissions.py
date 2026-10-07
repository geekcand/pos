from pathlib import Path
import re, sys

root = Path(sys.argv[1]).resolve()

def read(rel):
    return (root / rel).read_text(encoding="utf-8-sig")

def write(rel, text):
    (root / rel).write_text(text, encoding="utf-8-sig")

def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"R5 patch missing anchor: {label}")
    return text.replace(old, new, 1)

# Permissions enum
p = "Core/Enums.cs"
s = read(p)
s, n = re.subn(r"public enum Permission\s*\{.*?\}\s*$", """public enum Permission
{
    Sell,
    HoldOrder,
    OpenShift,
    CloseShift,
    AddExpense,
    DiscountBasic,
    DiscountOverride,
    ViewRefunds,
    Refund,
    VoidSale,
    CancelRestaurantOrder,
    CancelDeliveryOrder,
    ReturnDeliveryOrder,
    DispatchDelivery,
    SettleDelivery,
    ManageCatalog,
    DeleteCatalog,
    ManageUsers,
    ViewReports,
    ViewAudit,
    ManageSettings,
    ManagePaymentMethods,
    DeleteDiningTable,
    DeleteShift,
    BackupRestore
}
""", s, flags=re.S)
if n != 1:
    raise SystemExit("Permission enum replacement failed")
write(p, s)

# User stores explicit permission set
p = "Core/Entities.cs"
s = read(p)
s = replace_once(s,
"""    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.Now;""",
"""    public bool IsActive { get; set; } = true;
    [MaxLength(4000)] public string? PermissionsCsv { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.Now;""",
"user PermissionsCsv")
s = replace_once(s,
"""    [NotMapped] public string ActiveLabel => IsActive ? "نشط" : "متوقف";""",
"""    [NotMapped] public string ActiveLabel => IsActive ? "نشط" : "متوقف";
    [NotMapped] public string PermissionsLabel => string.IsNullOrWhiteSpace(PermissionsCsv) ? "افتراضية للدور" : $"{RolePermissions.Parse(PermissionsCsv).Count} صلاحية";""",
"user PermissionsLabel")
write(p, s)

# Central permission defaults/catalog and per-user overrides
write("Core/RolePermissions.cs", """namespace SweetsPOS.Core;

public sealed record PermissionDescriptor(Permission Permission, string Group, string Label, bool Sensitive = false);

public static class RolePermissions
{
    private static readonly IReadOnlyDictionary<UserRole, HashSet<Permission>> Map =
        new Dictionary<UserRole, HashSet<Permission>>
        {
            [UserRole.Cashier] = new()
            {
                Permission.Sell, Permission.HoldOrder, Permission.OpenShift,
                Permission.CloseShift, Permission.AddExpense, Permission.DiscountBasic,
                Permission.ViewRefunds, Permission.DispatchDelivery, Permission.SettleDelivery
            },
            [UserRole.Supervisor] = new()
            {
                Permission.Sell, Permission.HoldOrder, Permission.OpenShift,
                Permission.CloseShift, Permission.AddExpense, Permission.DiscountBasic,
                Permission.DiscountOverride, Permission.ViewRefunds, Permission.Refund,
                Permission.VoidSale, Permission.CancelRestaurantOrder, Permission.CancelDeliveryOrder,
                Permission.ReturnDeliveryOrder, Permission.DispatchDelivery, Permission.SettleDelivery,
                Permission.ViewReports
            },
            [UserRole.Admin] = Enum.GetValues<Permission>().ToHashSet()
        };

    public static IReadOnlyList<PermissionDescriptor> Definitions { get; } =
    [
        new(Permission.Sell, "الكاشير", "إتمام المبيعات"),
        new(Permission.HoldOrder, "الكاشير", "تعليق واستكمال الطلبات"),
        new(Permission.OpenShift, "الورديات", "فتح وردية"),
        new(Permission.CloseShift, "الورديات", "إغلاق ورديته"),
        new(Permission.AddExpense, "الورديات", "تسجيل مصروف"),
        new(Permission.DeleteShift, "الورديات", "حذف وردية فارغة", true),
        new(Permission.DiscountBasic, "المبيعات", "خصم عادي"),
        new(Permission.DiscountOverride, "المبيعات", "اعتماد خصم أعلى من الحد", true),
        new(Permission.ViewRefunds, "المرتجعات", "فتح وبحث شاشة المرتجعات"),
        new(Permission.Refund, "المرتجعات", "اعتماد مرتجع صنف / فاتورة", true),
        new(Permission.VoidSale, "المرتجعات", "إلغاء فاتورة من الوردية الحالية", true),
        new(Permission.CancelRestaurantOrder, "المطعم", "إلغاء طلب صالة", true),
        new(Permission.DeleteDiningTable, "المطعم", "حذف صالة / تقليل عدد الترابيزات", true),
        new(Permission.DispatchDelivery, "الدليفري", "تحميل طلب على طيار"),
        new(Permission.SettleDelivery, "الدليفري", "تسوية الطيار واستلام الكاش"),
        new(Permission.CancelDeliveryOrder, "الدليفري", "إلغاء طلب دليفري", true),
        new(Permission.ReturnDeliveryOrder, "الدليفري", "تسجيل دليفري مرتجع / لم يتم التسليم", true),
        new(Permission.ManageCatalog, "الإدارة", "إدارة الأقسام والأصناف"),
        new(Permission.DeleteCatalog, "الإدارة", "حذف قسم / صنف", true),
        new(Permission.ManagePaymentMethods, "الإدارة", "إدارة طرق الدفع"),
        new(Permission.ManageUsers, "الإدارة", "إدارة المستخدمين والصلاحيات", true),
        new(Permission.ViewReports, "الإدارة", "عرض التقارير ولوحة الإدارة"),
        new(Permission.ViewAudit, "الإدارة", "عرض سجل التعديلات"),
        new(Permission.ManageSettings, "الإدارة", "تعديل الإعدادات والطابعات"),
        new(Permission.BackupRestore, "الإدارة", "النسخ الاحتياطي والاسترجاع", true)
    ];

    public static bool Has(UserRole role, Permission permission)
        => Map.TryGetValue(role, out var set) && set.Contains(permission);

    public static bool Has(User user, Permission permission)
    {
        if (string.IsNullOrWhiteSpace(user.PermissionsCsv)) return Has(user.Role, permission);
        return Parse(user.PermissionsCsv).Contains(permission);
    }

    public static HashSet<Permission> Defaults(UserRole role)
        => Map.TryGetValue(role, out var set) ? set.ToHashSet() : [];

    public static HashSet<Permission> Parse(string? csv)
    {
        var result = new HashSet<Permission>();
        if (string.IsNullOrWhiteSpace(csv)) return result;
        foreach (var part in csv.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
            if (Enum.TryParse<Permission>(part, true, out var p)) result.Add(p);
        return result;
    }

    public static string Serialize(IEnumerable<Permission> permissions)
        => string.Join(",", permissions.Distinct().OrderBy(x => (int)x));
}
""")

# SQLite upgrade without data loss
p = "Data/DatabaseService.cs"
s = read(p)
anchor = """        if (!await HasColumnAsync("Sales", "ShiftInvoiceNumber"))"""
s = replace_once(s, anchor,
"""        if (!await HasColumnAsync("Users", "PermissionsCsv"))
            await ExecAsync("ALTER TABLE Users ADD COLUMN PermissionsCsv TEXT NULL;");

""" + anchor, "database PermissionsCsv")
write(p, s)

# Session and manager approval use user-specific permissions
p = "Services/AppSession.cs"
s = read(p).replace(
    "public bool Can(Permission permission) => CurrentUser is not null && RolePermissions.Has(CurrentUser.Role, permission);",
    "public bool Can(Permission permission) => CurrentUser is not null && RolePermissions.Has(CurrentUser, permission);")
write(p, s)

p = "Services/AuthService.cs"
s = read(p).replace(
    "return elevated.FirstOrDefault(x => RolePermissions.Has(x.Role, requiredPermission) && PinHasher.Verify(pin, x.PinHash));",
    "return elevated.FirstOrDefault(x => RolePermissions.Has(x, requiredPermission) && PinHasher.Verify(pin, x.PinHash));")
write(p, s)

p = "Services/UserService.cs"
s = read(p)
s = replace_once(s,
"public async Task<User> SaveAsync(int id, string username, string displayName, UserRole role, bool active, string? newPin)",
"public async Task<User> SaveAsync(int id, string username, string displayName, UserRole role, bool active, string? newPin, IReadOnlyCollection<Permission>? permissions = null)",
"UserService signature")
s = replace_once(s,
'row = new User { Username = username.Trim(), DisplayName = displayName.Trim(), Role = role, IsActive = active, PinHash = PinHasher.Hash(newPin), CreatedAt = DateTime.Now };',
'row = new User { Username = username.Trim(), DisplayName = displayName.Trim(), Role = role, IsActive = active, PermissionsCsv = permissions is null ? null : RolePermissions.Serialize(permissions), PinHash = PinHasher.Hash(newPin), CreatedAt = DateTime.Now };',
"new user permissions")
s = replace_once(s,
"""            row.Role = role;
            row.IsActive = active;""",
"""            row.Role = role;
            row.IsActive = active;
            row.PermissionsCsv = permissions is null ? null : RolePermissions.Serialize(permissions);""",
"edit user permissions")
write(p, s)

# Users list shows permission state
p = "Pages/UsersPage.xaml"
s = read(p)
s = s.replace('Text="إدارة الكاشير والأدمن وصلاحيات الدخول"', 'Text="حدد الدور ثم فعّل الصلاحيات المطلوبة بعلامة صح لكل مستخدم"')
s = s.replace('<ColumnDefinition Width="170"/><ColumnDefinition Width="130"/><ColumnDefinition Width="90"/>',
              '<ColumnDefinition Width="150"/><ColumnDefinition Width="150"/><ColumnDefinition Width="120"/><ColumnDefinition Width="90"/>')
s = s.replace('<TextBlock Grid.Column="1" Text="الدور" Foreground="{StaticResource MutedTextBrush}"/><TextBlock Grid.Column="2" Text="الحالة" Foreground="{StaticResource MutedTextBrush}"/>',
              '<TextBlock Grid.Column="1" Text="الدور" Foreground="{StaticResource MutedTextBrush}"/><TextBlock Grid.Column="2" Text="الصلاحيات" Foreground="{StaticResource MutedTextBrush}"/><TextBlock Grid.Column="3" Text="الحالة" Foreground="{StaticResource MutedTextBrush}"/>')
s = s.replace('<TextBlock Grid.Column="1" Text="{Binding RoleLabel}"/><TextBlock Grid.Column="2" Text="{Binding ActiveLabel}"/><Button Grid.Column="3"',
              '<TextBlock Grid.Column="1" Text="{Binding RoleLabel}"/><TextBlock Grid.Column="2" Text="{Binding PermissionsLabel}" Foreground="{StaticResource MutedTextBrush}"/><TextBlock Grid.Column="3" Text="{Binding ActiveLabel}"/><Button Grid.Column="4"')
write(p, s)

# Replace user editor with role + checkboxes
p = "Pages/UsersPage.xaml.cs"
s = read(p)
start = s.index("    private async Task<bool> EditAsync(User? source)")
end = s.rindex("\n}")
method = r'''    private async Task<bool> EditAsync(User? source)
    {
        var username = new TextBox { Header = "اسم المستخدم", Text = source?.Username ?? "" };
        var display = new TextBox { Header = "الاسم الظاهر", Text = source?.DisplayName ?? "" };
        var role = new ComboBox { Header = "الدور الأساسي", ItemsSource = RoleOptions, DisplayMemberPath = "Label", HorizontalAlignment = HorizontalAlignment.Stretch };
        role.SelectedItem = RoleOptions.First(x => x.Value == (source?.Role ?? UserRole.Cashier));
        var pin = new PasswordBox { Header = source is null ? "الرقم السري" : "رقم سري جديد (اتركه فارغًا للإبقاء على الحالي)", PasswordRevealMode = PasswordRevealMode.Peek };
        var active = new CheckBox { Content = "المستخدم نشط", IsChecked = source?.IsActive ?? true };

        var selected = source is not null && !string.IsNullOrWhiteSpace(source.PermissionsCsv)
            ? RolePermissions.Parse(source.PermissionsCsv)
            : RolePermissions.Defaults(source?.Role ?? UserRole.Cashier);
        var checks = new Dictionary<Permission, CheckBox>();
        var permissionsPanel = new StackPanel { Spacing = 6, FlowDirection = FlowDirection.RightToLeft };
        foreach (var group in RolePermissions.Definitions.GroupBy(x => x.Group))
        {
            permissionsPanel.Children.Add(new TextBlock
            {
                Text = group.Key, FontWeight = Microsoft.UI.Text.FontWeights.Bold, Margin = new Thickness(0, 8, 0, 2),
                Foreground = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["AccentBrushSoft"]
            });
            foreach (var item in group)
            {
                var cb = new CheckBox
                {
                    Content = item.Sensitive ? $"{item.Label}  🔒" : item.Label,
                    IsChecked = selected.Contains(item.Permission),
                    Tag = item.Permission,
                    HorizontalAlignment = HorizontalAlignment.Stretch
                };
                checks[item.Permission] = cb;
                permissionsPanel.Children.Add(cb);
            }
        }

        var permissionScroll = new ScrollViewer { MaxHeight = 340, Content = permissionsPanel, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
        var resetDefaults = new Button { Content = "تطبيق الصلاحيات الافتراضية للدور", Style = (Style)Application.Current.Resources["SoftButtonStyle"] };
        void ApplyRoleDefaults()
        {
            var r = role.SelectedItem is RoleOption ro ? ro.Value : UserRole.Cashier;
            var defaults = RolePermissions.Defaults(r);
            foreach (var pair in checks) pair.Value.IsChecked = defaults.Contains(pair.Key);
        }
        resetDefaults.Click += (_, _) => ApplyRoleDefaults();
        role.SelectionChanged += (_, _) => ApplyRoleDefaults();

        var securityNote = new TextBlock
        {
            Text = "🔒 العمليات الحساسة (المرتجعات، إلغاء الطلبات، حذف الترابيزات...) لا يعتمدها حساب الكاشير بنفسه؛ سيُطلب PIN مدير/مشرف لديه الصلاحية حتى لو كانت الشاشة متاحة للكاشير.",
            TextWrapping = TextWrapping.Wrap,
            Foreground = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["MutedTextBrush"],
            FontSize = 12
        };

        var panel = new StackPanel { Width = 500, Spacing = 9, FlowDirection = FlowDirection.RightToLeft };
        panel.Children.Add(username); panel.Children.Add(display); panel.Children.Add(role); panel.Children.Add(pin); panel.Children.Add(active);
        panel.Children.Add(new TextBlock { Text = "الصلاحيات", FontSize = 18, FontWeight = Microsoft.UI.Text.FontWeights.Bold, Margin = new Thickness(0,8,0,0) });
        panel.Children.Add(resetDefaults); panel.Children.Add(permissionScroll); panel.Children.Add(securityNote);

        var d = new ContentDialog
        {
            XamlRoot = XamlRoot, RequestedTheme = ElementTheme.Dark,
            Title = source is null ? "إضافة مستخدم وصلاحياته" : "تعديل المستخدم والصلاحيات",
            Content = panel, PrimaryButtonText = "حفظ", CloseButtonText = "إلغاء", FlowDirection = FlowDirection.RightToLeft
        };
        if (await d.ShowAsync() != ContentDialogResult.Primary) return false;
        try
        {
            if (pin.Password.Length > 0 && (pin.Password.Length < 4 || pin.Password.Any(c => !char.IsDigit(c)))) throw new InvalidOperationException("يجب أن يحتوي الرقم السري على 4 أرقام على الأقل.");
            var permissions = checks.Where(x => x.Value.IsChecked == true).Select(x => x.Key).ToList();
            await App.Services.Users.SaveAsync(source?.Id ?? 0, username.Text, display.Text, role.SelectedItem is RoleOption ro ? ro.Value : UserRole.Cashier, active.IsChecked == true, pin.Password, permissions);
            return true;
        }
        catch (Exception ex) { await PageHelpers.MessageAsync(XamlRoot, "تعذر حفظ المستخدم", ex.Message); return false; }
    }
'''
write(p, s[:start] + method + s[end:])

# Reusable manager PIN gate
p = "Pages/PageHelpers.cs"
s = read(p)
if "using SweetsPOS.Core;" not in s:
    s = s.replace("using Microsoft.UI.Xaml.Controls;", "using Microsoft.UI.Xaml.Controls;\nusing SweetsPOS.Core;")
anchor = "    public static decimal DecimalFrom(NumberBox box) => double.IsNaN(box.Value) ? 0 : (decimal)box.Value;"
helper = r'''
    public static async Task<bool> RequirePermissionAsync(XamlRoot root, Permission permission, string action, bool managerApprovalForCashier = false)
    {
        var current = App.Services.Session.CurrentUser;
        if (current is null) return false;

        if (App.Services.Session.Can(permission) && (!managerApprovalForCashier || current.Role != UserRole.Cashier))
            return true;

        var pin = new PasswordBox { Header = "PIN المدير / المشرف", PasswordRevealMode = PasswordRevealMode.Peek, FlowDirection = FlowDirection.LeftToRight };
        var panel = new StackPanel { Width = 390, Spacing = 10, FlowDirection = FlowDirection.RightToLeft };
        panel.Children.Add(new TextBlock { Text = action, TextWrapping = TextWrapping.Wrap });
        panel.Children.Add(new TextBlock { Text = "هذه عملية حساسة. أدخل PIN لحساب مدير أو مشرف لديه الصلاحية المطلوبة.", TextWrapping = TextWrapping.Wrap, Foreground = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["MutedTextBrush"] });
        panel.Children.Add(pin);
        var dialog = new ContentDialog
        {
            XamlRoot = root, RequestedTheme = ElementTheme.Dark, FlowDirection = FlowDirection.RightToLeft,
            Title = "موافقة مدير مطلوبة", Content = panel, PrimaryButtonText = "اعتماد الإجراء", CloseButtonText = "إلغاء", DefaultButton = ContentDialogButton.Primary
        };
        if (await dialog.ShowAsync() != ContentDialogResult.Primary) return false;
        var approver = await App.Services.Auth.FindApproverAsync(pin.Password, permission);
        if (approver is null)
        {
            await MessageAsync(root, "فشلت الموافقة", "الـ PIN غير صحيح أو الحساب لا يملك صلاحية اعتماد هذا الإجراء.");
            return false;
        }
        await App.Services.Audit.WriteAsync("ManagerApprovalGranted", "Permission", permission.ToString(), $"{action} • requested by {current.DisplayName}", approver.Id, approver.DisplayName);
        return true;
    }

'''
s = replace_once(s, anchor, helper + anchor, "PageHelpers approval")
write(p, s)

# Refund and void always manager-approved for cashier
p = "Pages/RefundsPage.xaml.cs"
s = read(p)
s = replace_once(s,
"""        var remaining = item.Quantity - item.RefundedQuantity;""",
"""        if (!await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.Refund, $"استرجاع الصنف «{item.ProductName}» من الفاتورة #{_sale.DisplayInvoiceNumber}", managerApprovalForCashier: true)) return;
        var remaining = item.Quantity - item.RefundedQuantity;""",
"refund item approval")
s = s.replace("await App.Services.Sales.RefundAsync(_sale.Id, [new RefundLineInput(item.Id, PageHelpers.DecimalFrom(qty))], details.Value.Method, details.Value.Reason);",
              "await App.Services.Sales.RefundAsync(_sale.Id, [new RefundLineInput(item.Id, PageHelpers.DecimalFrom(qty))], details.Value.Method, details.Value.Reason, approvalGranted: true);")
s = replace_once(s,
"""        var lines = _sale.Items.Select(x => new RefundLineInput(x.Id, x.Quantity - x.RefundedQuantity)).Where(x => x.Quantity > 0).ToList();""",
"""        if (!await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.Refund, $"استرجاع الفاتورة #{_sale.DisplayInvoiceNumber} بالكامل", managerApprovalForCashier: true)) return;
        var lines = _sale.Items.Select(x => new RefundLineInput(x.Id, x.Quantity - x.RefundedQuantity)).Where(x => x.Quantity > 0).ToList();""",
"refund all approval")
s = s.replace("var r = await App.Services.Sales.RefundAsync(_sale.Id, lines, details.Value.Method, details.Value.Reason);",
              "var r = await App.Services.Sales.RefundAsync(_sale.Id, lines, details.Value.Method, details.Value.Reason, approvalGranted: true);")
s = replace_once(s,
"""        var reason = new TextBox { Header = "سبب الإلغاء", AcceptsReturn = true, Height = 80 };""",
"""        if (!await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.VoidSale, $"إلغاء الفاتورة #{_sale.DisplayInvoiceNumber}", managerApprovalForCashier: true)) return;
        var reason = new TextBox { Header = "سبب الإلغاء", AcceptsReturn = true, Height = 80 };""",
"void approval")
s = s.replace("await App.Services.Sales.VoidSaleAsync(_sale.Id, reason.Text.Trim());",
              "await App.Services.Sales.VoidSaleAsync(_sale.Id, reason.Text.Trim(), approvalGranted: true);")
write(p, s)

# Restaurant order cancellation approval
p = "Pages/PosPage.xaml.cs"
s = read(p)
idx = s.find("    private async void CancelRestaurantOrder_Click")
if idx < 0:
    raise SystemExit("CancelRestaurantOrder_Click missing")
tail = s[idx:]
tail = replace_once(tail,
"""        if (_restaurantOrder is null) return;
        var confirm = new ContentDialog""",
"""        if (_restaurantOrder is null) return;
        var cancelPermission = _restaurantOrder.OrderType == RestaurantOrderType.Delivery ? Permission.CancelDeliveryOrder : Permission.CancelRestaurantOrder;
        if (!await PageHelpers.RequirePermissionAsync(XamlRoot, cancelPermission, $"إلغاء {_restaurantOrder.DisplayLabel}", managerApprovalForCashier: true)) return;
        var confirm = new ContentDialog""",
"restaurant cancel approval")
write(p, s[:idx] + tail)

# Protect hall removal/table count reduction
p = "Pages/SettingsPage.xaml.cs"
s = read(p)
s = replace_once(s,
"""    private List<string> _installedPrinters = [];""",
"""    private List<string> _installedPrinters = [];
    private Dictionary<string, int> _originalAreaCounts = new(StringComparer.OrdinalIgnoreCase);""",
"original area counts field")
s = replace_once(s,
"""        foreach (var area in areas) AddAreaRow(area);""",
"""        _originalAreaCounts = areas.Where(x => !string.IsNullOrWhiteSpace(x.Id)).ToDictionary(x => x.Id, x => x.TableCount, StringComparer.OrdinalIgnoreCase);
        foreach (var area in areas) AddAreaRow(area);""",
"remember area counts")
s = s.replace(
'remove.Click += (_, _) => { _areaRows.Remove(row); DiningAreasPanel.Children.Remove(grid); RenumberBlankAreas(); };',
'remove.Click += async (_, _) => { if (!await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.DeleteDiningTable, $"حذف الصالة «{row.Name.Text}» والترابيزات التابعة لها", managerApprovalForCashier: true)) return; _areaRows.Remove(row); DiningAreasPanel.Children.Remove(grid); RenumberBlankAreas(); };')
s = replace_once(s,
"""            var routes = new Dictionary<int, string>();""",
"""            var reducedTables = areas.Any(x => _originalAreaCounts.TryGetValue(x.Id, out var oldCount) && x.TableCount < oldCount);
            if (reducedTables && !await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.DeleteDiningTable, "تقليل عدد الترابيزات في إعدادات المطعم", managerApprovalForCashier: true)) return;

            var routes = new Dictionary<int, string>();""",
"table reduction approval")
s = replace_once(s,
"""            Info.Severity = InfoBarSeverity.Success; Info.Message = "تم حفظ الإعدادات."; Info.IsOpen = true;""",
"""            _originalAreaCounts = areas.Where(x => !string.IsNullOrWhiteSpace(x.Id)).ToDictionary(x => x.Id, x => x.TableCount, StringComparer.OrdinalIgnoreCase);
            Info.Severity = InfoBarSeverity.Success; Info.Message = "تم حفظ الإعدادات."; Info.IsOpen = true;""",
"refresh original area counts")
write(p, s)

# Shell navigation honors custom permissions
p = "Pages/ShellPage.xaml.cs"
s = read(p)
s = s.replace(
'DashboardNav.Visibility = session.Can(Permission.ViewReports) ? Visibility.Visible : Visibility.Collapsed;',
'DashboardNav.Visibility = (session.Can(Permission.ViewReports) || session.Can(Permission.ManageCatalog) || session.Can(Permission.ManageUsers) || session.Can(Permission.ViewAudit) || session.Can(Permission.ManageSettings) || session.Can(Permission.ManagePaymentMethods) || session.Can(Permission.ViewRefunds) || session.Can(Permission.DeleteShift)) ? Visibility.Visible : Visibility.Collapsed;')
s = s.replace(
'RefundsNav.Visibility = session.Can(Permission.Refund) || session.Can(Permission.VoidSale) ? Visibility.Visible : Visibility.Collapsed;',
'RefundsNav.Visibility = session.Can(Permission.ViewRefunds) ? Visibility.Visible : Visibility.Collapsed;')
s = s.replace(
'PaymentMethodsNav.Visibility = user.Role == UserRole.Admin ? Visibility.Visible : Visibility.Collapsed;',
'PaymentMethodsNav.Visibility = session.Can(Permission.ManagePaymentMethods) ? Visibility.Visible : Visibility.Collapsed;')
s = s.replace(
'AdminShiftsNav.Visibility = user.Role == UserRole.Admin ? Visibility.Visible : Visibility.Collapsed;',
'AdminShiftsNav.Visibility = session.Can(Permission.DeleteShift) || session.Can(Permission.ViewReports) ? Visibility.Visible : Visibility.Collapsed;')
write(p, s)

# Shift deletion permission
p = "Services/ShiftService.cs"
s = read(p)
s = s.replace("public async Task DeleteAndRenumberAsync(int shiftId)", "public async Task DeleteAndRenumberAsync(int shiftId, bool approvalGranted = false)")
s = s.replace('if (admin.Role != UserRole.Admin) throw new UnauthorizedAccessException("حذف الورديات متاح للأدمن فقط.");',
              'if (!session.Can(Permission.DeleteShift) && !approvalGranted) throw new UnauthorizedAccessException("حذف الورديات يحتاج صلاحية مدير.");')
write(p, s)

p = "Pages/ShiftsPage.xaml.cs"
s = read(p)
s = replace_once(s,
"""        var isAdmin = App.Services.Session.CurrentUser?.Role == SweetsPOS.Core.UserRole.Admin;""",
"""        var isAdmin = App.Services.Session.CurrentUser?.Role == SweetsPOS.Core.UserRole.Admin;
        var canDeleteShift = App.Services.Session.Can(SweetsPOS.Core.Permission.DeleteShift);""",
"shift canDelete")
s = s.replace("DeleteShiftButton.Visibility = isAdmin ? Visibility.Visible : Visibility.Collapsed;",
              "DeleteShiftButton.Visibility = canDeleteShift ? Visibility.Visible : Visibility.Collapsed;")
s = s.replace(
"""    private async void DeleteShift_Click(object sender, RoutedEventArgs e)
    {
        if (App.Services.Session.CurrentUser?.Role != SweetsPOS.Core.UserRole.Admin) return;""",
"""    private async void DeleteShift_Click(object sender, RoutedEventArgs e)
    {
        if (!await PageHelpers.RequirePermissionAsync(XamlRoot, SweetsPOS.Core.Permission.DeleteShift, "حذف وردية فارغة وإعادة ترقيم الورديات", managerApprovalForCashier: true)) return;""")
s = s.replace("await App.Services.Shifts.DeleteAndRenumberAsync(selected.Id);",
              "await App.Services.Shifts.DeleteAndRenumberAsync(selected.Id, approvalGranted: true);")
write(p, s)

# Product/category deletion approval
for rel, action in [("Pages/ProductsPage.xaml.cs", "حذف الصنف"), ("Pages/CategoriesPage.xaml.cs", "حذف القسم")]:
    s = read(rel)
    if "using SweetsPOS.Core;" not in s:
        s = s.replace("using Microsoft.UI.Xaml.Controls;", "using Microsoft.UI.Xaml.Controls;\nusing SweetsPOS.Core;")
    marker = """    private async void Delete_Click(object sender, RoutedEventArgs e)
    {"""
    s = replace_once(s, marker, marker + f'\n        if (!await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.DeleteCatalog, "{action}", managerApprovalForCashier: true)) return;', rel + " delete approval")
    write(rel, s)

print("Restaurant R5 permissions patch applied.")
