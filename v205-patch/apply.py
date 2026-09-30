from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()

# 1) Real admin shell: categories -> items -> payment methods.
p = root / 'Pages' / 'ShellPage.xaml'
s = p.read_text(encoding='utf-8-sig')
old = '''                    <Button x:Name="ProductsNav" Content="🍬 المنتجات" Tag="products" Click="NavButton_Click" Style="{StaticResource TopNavButtonStyle}" HorizontalAlignment="Stretch"/>\n                    <Button x:Name="CategoriesNav" Content="📁 الأقسام" Tag="categories" Click="NavButton_Click" Style="{StaticResource TopNavButtonStyle}" HorizontalAlignment="Stretch"/>'''
new = '''                    <Button x:Name="CategoriesNav" Content="📁 الأقسام" Tag="categories" Click="NavButton_Click" Style="{StaticResource TopNavButtonStyle}" HorizontalAlignment="Stretch"/>\n                    <Button x:Name="ProductsNav" Content="🍬 الأصناف" Tag="products" Click="NavButton_Click" Style="{StaticResource TopNavButtonStyle}" HorizontalAlignment="Stretch"/>\n                    <Button x:Name="PaymentMethodsNav" Content="💳 طرق الدفع" Tag="payments" Click="NavButton_Click" Style="{StaticResource TopNavButtonStyle}" HorizontalAlignment="Stretch"/>'''
assert old in s, 'ShellPage.xaml old admin buttons not found'
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8-sig')

p = root / 'Pages' / 'ShellPage.xaml.cs'
s = p.read_text(encoding='utf-8-sig')
repls = [
    ('yield return ProductsNav; yield return CategoriesNav; yield return UsersNav; yield return ReportsNav;',
     'yield return CategoriesNav; yield return ProductsNav; yield return PaymentMethodsNav; yield return UsersNav; yield return ReportsNav;'),
    ('ProductsNav.Visibility = session.Can(Permission.ManageCatalog) ? Visibility.Visible : Visibility.Collapsed;\n        CategoriesNav.Visibility = session.Can(Permission.ManageCatalog) ? Visibility.Visible : Visibility.Collapsed;',
     'CategoriesNav.Visibility = session.Can(Permission.ManageCatalog) ? Visibility.Visible : Visibility.Collapsed;\n        ProductsNav.Visibility = session.Can(Permission.ManageCatalog) ? Visibility.Visible : Visibility.Collapsed;\n        PaymentMethodsNav.Visibility = user.Role == UserRole.Admin ? Visibility.Visible : Visibility.Collapsed;'),
    ('var adminTags = new HashSet<string> { "dashboard", "products", "categories", "users", "reports", "expenses", "refunds", "shiftadmin", "receipt", "audit", "online", "settings" };',
     'var adminTags = new HashSet<string> { "dashboard", "categories", "products", "payments", "users", "reports", "expenses", "refunds", "shiftadmin", "receipt", "audit", "online", "settings" };'),
    ('"expenses" => typeof(ExpensesPage), "refunds" => typeof(RefundsPage), "products" => typeof(ProductsPage),\n            "categories" => typeof(CategoriesPage), "reports" => typeof(ReportsPage), "users" => typeof(UsersPage),',
     '"expenses" => typeof(ExpensesPage), "refunds" => typeof(RefundsPage), "products" => typeof(ProductsPage),\n            "categories" => typeof(CategoriesPage), "payments" => typeof(PaymentMethodsPage), "reports" => typeof(ReportsPage), "users" => typeof(UsersPage),')
]
for old, new in repls:
    assert old in s, f'ShellPage.xaml.cs replacement missing: {old[:60]}'
    s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8-sig')

# 2) Quantity entry: direct TextBox, Enter only updates quantity.
p = root / 'Pages' / 'PosPage.xaml'
s = p.read_text(encoding='utf-8-sig')
old = '<NumberBox Grid.Column="2" Value="{Binding Quantity}" Tag="{Binding ProductId}" Minimum="0.001" SpinButtonPlacementMode="Hidden" KeyDown="QuantityBox_KeyDown" HorizontalAlignment="Stretch" VerticalAlignment="Center" ToolTipService.ToolTip="اكتب الكمية واضغط Enter"/>'
new = '<TextBox Grid.Column="2" Text="{Binding Quantity, Mode=OneWay}" Tag="{Binding ProductId}" KeyDown="QuantityBox_KeyDown" HorizontalAlignment="Stretch" VerticalAlignment="Center" TextAlignment="Center" InputScope="Number" ToolTipService.ToolTip="اكتب الكمية واضغط Enter"/>'
assert old in s, 'PosPage.xaml quantity NumberBox not found'
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8-sig')

p = root / 'Pages' / 'PosPage.xaml.cs'
s = p.read_text(encoding='utf-8-sig')
start = s.index('    private static bool TryDecimalFromText(NumberBox box, out decimal value)')
end = s.index('    private void DiscountBox_ValueChanged', start)
helper = '''    private static bool TryDecimalFromText(string? text, out decimal value)\n    {\n        text = (text ?? string.Empty).Trim();\n        if (decimal.TryParse(text, NumberStyles.Number, CultureInfo.CurrentCulture, out value)) return true;\n        if (decimal.TryParse(text, NumberStyles.Number, CultureInfo.InvariantCulture, out value)) return true;\n        value = 0;\n        return false;\n    }\n\n    private static decimal DecimalFromLive(TextBox box)\n        => TryDecimalFromText(box.Text, out var value) ? value : 0m;\n\n    private void QuantityBox_KeyDown(object sender, KeyRoutedEventArgs e)\n    {\n        if (e.Key != Windows.System.VirtualKey.Enter || sender is not TextBox box || !int.TryParse(box.Tag?.ToString(), out var id)) return;\n        e.Handled = true;\n        var line = _cart.FirstOrDefault(x => x.ProductId == id);\n        if (line is null) return;\n\n        if (!TryDecimalFromText(box.Text, out var qty) || qty <= 0)\n        {\n            box.Text = line.Quantity.ToString("0.###", CultureInfo.CurrentCulture);\n            return;\n        }\n\n        line.Quantity = qty;\n        RefreshCart();\n    }\n\n'''
s = s[:start] + helper + s[end:]

# 3) Payment dialog: direct TextBox + TextChanged for immediate remaining/change.
start = s.index('    private async Task<(List<PaymentInput> Payments, decimal Tendered, decimal Change)?> AskPaymentsAsync(decimal total)')
end = s.index('    private async void Hold_Click', start)
payments = '''    private async Task<(List<PaymentInput> Payments, decimal Tendered, decimal Change)?> AskPaymentsAsync(decimal total)\n    {\n        var methods = await App.Services.PaymentMethods.GetActiveAsync();\n        if (methods.Count == 0)\n        {\n            await PageHelpers.MessageAsync(XamlRoot, "طرق الدفع", "لا توجد طريقة دفع نشطة. فعّل طريقة دفع من لوحة الإدارة.");\n            return null;\n        }\n\n        var boxes = new Dictionary<string, TextBox>(StringComparer.OrdinalIgnoreCase);\n        var title = new TextBlock\n        {\n            Text = "الدفع", FontSize = 22, FontWeight = Microsoft.UI.Text.FontWeights.Bold,\n            FlowDirection = FlowDirection.RightToLeft, TextAlignment = TextAlignment.Center,\n            HorizontalAlignment = HorizontalAlignment.Stretch\n        };\n        var note = new TextBlock\n        {\n            Text = $"الإجمالي المطلوب: {total:0.00} جنيه",\n            MaxWidth = 390, TextWrapping = TextWrapping.Wrap,\n            FlowDirection = FlowDirection.RightToLeft, TextAlignment = TextAlignment.Center,\n            HorizontalAlignment = HorizontalAlignment.Stretch\n        };\n        var balance = new TextBlock\n        {\n            Text = $"المتبقي: {total:0.00} جنيه",\n            FontSize = 17, FontWeight = Microsoft.UI.Text.FontWeights.SemiBold,\n            Foreground = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["AccentBrushSoft"],\n            TextAlignment = TextAlignment.Center, HorizontalAlignment = HorizontalAlignment.Stretch\n        };\n        var panel = new StackPanel { Spacing = 9, Width = 390, FlowDirection = FlowDirection.RightToLeft };\n        panel.Children.Add(title);\n        panel.Children.Add(note);\n        panel.Children.Add(balance);\n\n        foreach (var method in methods)\n        {\n            var box = new TextBox\n            {\n                Header = method.Name,\n                Text = method.Key.Equals("cash", StringComparison.OrdinalIgnoreCase)\n                    ? total.ToString("0.00", CultureInfo.CurrentCulture)\n                    : "0",\n                FlowDirection = FlowDirection.RightToLeft,\n                HorizontalAlignment = HorizontalAlignment.Stretch,\n                TextAlignment = TextAlignment.Left\n            };\n            box.GotFocus += (_, _) => box.SelectAll();\n            boxes[method.Key] = box;\n            panel.Children.Add(box);\n        }\n\n        void RefreshBalance()\n        {\n            var tendered = boxes.Values.Sum(DecimalFromLive);\n            var diff = tendered - total;\n            if (diff > 0) balance.Text = $"الباقي للعميل: {diff:0.00} جنيه";\n            else if (diff < 0) balance.Text = $"المتبقي: {-diff:0.00} جنيه";\n            else balance.Text = "المبلغ مكتمل • الباقي: 0.00 جنيه";\n        }\n\n        foreach (var box in boxes.Values)\n            box.TextChanged += (_, _) => RefreshBalance();\n\n        RefreshBalance();\n\n        var dialog = new ContentDialog\n        {\n            XamlRoot = XamlRoot, RequestedTheme = ElementTheme.Dark, Content = panel,\n            PrimaryButtonText = "إتمام البيع", CloseButtonText = "إلغاء",\n            DefaultButton = ContentDialogButton.Primary, FlowDirection = FlowDirection.RightToLeft,\n            HorizontalContentAlignment = HorizontalAlignment.Stretch\n        };\n        if (await dialog.ShowAsync() != ContentDialogResult.Primary) return null;\n\n        var tendered = boxes.Values.Sum(DecimalFromLive);\n        if (tendered < total)\n        {\n            await PageHelpers.MessageAsync(XamlRoot, "الدفع غير مكتمل", $"المتبقي: {total - tendered:0.00} جنيه");\n            return null;\n        }\n\n        var change = tendered - total;\n        var cashEntered = boxes.TryGetValue("cash", out var cashBox) ? DecimalFromLive(cashBox) : 0;\n        if (change > cashEntered)\n        {\n            await PageHelpers.MessageAsync(XamlRoot, "دفع غير صالح", "أي مبلغ زائد يجب أن يكون ضمن المبلغ المدفوع كاش حتى يمكن حساب الباقي للعميل.");\n            return null;\n        }\n\n        var inputs = new List<PaymentInput>();\n        foreach (var method in methods)\n        {\n            var amount = DecimalFromLive(boxes[method.Key]);\n            if (method.Key.Equals("cash", StringComparison.OrdinalIgnoreCase)) amount -= change;\n            if (amount <= 0) continue;\n            inputs.Add(new PaymentInput(method.LegacyMethod, amount, method.Key, method.Name));\n        }\n\n        return (inputs, tendered, change);\n    }\n\n'''
s = s[:start] + payments + s[end:]
p.write_text(s, encoding='utf-8-sig')

# Version bump only; licensing flow remains from v2.0.3/v2.0.4.
for rel in ['SweetsPOS.csproj', 'installer.iss']:
    p = root / rel
    s = p.read_text(encoding='utf-8-sig')
    assert '2.0.4' in s, f'{rel} has no 2.0.4 marker'
    p.write_text(s.replace('2.0.4', '2.0.5'), encoding='utf-8-sig')

# Assertions against the actual runtime pages.
shell = (root/'Pages'/'ShellPage.xaml').read_text(encoding='utf-8-sig')
shell_cs = (root/'Pages'/'ShellPage.xaml.cs').read_text(encoding='utf-8-sig')
pos_xaml = (root/'Pages'/'PosPage.xaml').read_text(encoding='utf-8-sig')
pos_cs = (root/'Pages'/'PosPage.xaml.cs').read_text(encoding='utf-8-sig')
assert shell.index('x:Name="CategoriesNav"') < shell.index('x:Name="ProductsNav"') < shell.index('x:Name="PaymentMethodsNav"')
assert 'Content="🍬 الأصناف"' in shell and 'Content="🍬 المنتجات"' not in shell
assert '"payments" => typeof(PaymentMethodsPage)' in shell_cs
assert 'TextBox Grid.Column="2"' in pos_xaml and 'NumberBox Grid.Column="2"' not in pos_xaml
assert 'Dictionary<string, TextBox>' in pos_cs
assert 'box.TextChanged += (_, _) => RefreshBalance();' in pos_cs
assert 'sender is not TextBox box' in pos_cs
print('v2.0.5 patch applied successfully')
