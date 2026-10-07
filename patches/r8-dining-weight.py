from pathlib import Path
import re, sys

root = Path(sys.argv[1]).resolve()

def read(rel):
    return (root / rel).read_text(encoding="utf-8-sig")

def write(rel, text):
    (root / rel).write_text(text, encoding="utf-8-sig")

def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"R8 missing anchor: {label}")
    return text.replace(old, new, 1)

# --- Dining UI: explicit right-first table placement ---
p = "Pages/PosPage.xaml"
s = read(p)

s = replace_once(
    s,
    '<GridView Grid.Row="1" x:Name="TablesGrid" SelectionMode="None" Background="Transparent" ScrollViewer.VerticalScrollBarVisibility="Auto" ScrollViewer.HorizontalScrollBarVisibility="Disabled"><GridView.ItemsPanel><ItemsPanelTemplate><ItemsWrapGrid Orientation="Horizontal" FlowDirection="RightToLeft" ItemWidth="162" ItemHeight="117"/></ItemsPanelTemplate></GridView.ItemsPanel></GridView>',
    '<ScrollViewer Grid.Row="1" VerticalScrollBarVisibility="Auto" HorizontalScrollBarVisibility="Disabled" HorizontalContentAlignment="Stretch"><StackPanel x:Name="TablesPanel" Spacing="10" HorizontalAlignment="Stretch" FlowDirection="LeftToRight"/></ScrollViewer>',
    "tables panel"
)

s = replace_once(
    s,
    '<StackPanel x:Name="DiningAreasView" Spacing="9" Visibility="Collapsed">\n                        <TextBlock Text="الصالات" FontSize="18" FontWeight="ExtraBold" Foreground="{StaticResource AccentBrushSoft}" Margin="4,5,4,4"/>\n                        <StackPanel x:Name="DiningAreasPanel" Spacing="7" />\n                    </StackPanel>',
    '<StackPanel x:Name="DiningAreasView" Spacing="9" Visibility="Collapsed" FlowDirection="RightToLeft" HorizontalAlignment="Stretch">\n                        <TextBlock Text="الصالات" FontSize="18" FontWeight="ExtraBold" Foreground="{StaticResource AccentBrushSoft}" Margin="4,5,4,4" HorizontalAlignment="Stretch" TextAlignment="Right"/>\n                        <StackPanel x:Name="DiningAreasPanel" Spacing="7" FlowDirection="RightToLeft" HorizontalAlignment="Stretch" />\n                    </StackPanel>',
    "dining areas alignment"
)
write(p, s)

p = "Pages/PosPage.xaml.cs"
s = read(p)

old_render_areas = '''    private void RenderDiningAreas()
    {
        DiningAreasPanel.Children.Clear(); var normal = (Style)Application.Current.Resources["CategoryButtonStyle"]; var active = (Style)Application.Current.Resources["CategoryButtonActiveStyle"];
        foreach (var area in _diningAreas)
        {
            var b = new Button { Content = area.Name, Tag = area.Id, HorizontalAlignment = HorizontalAlignment.Stretch, HorizontalContentAlignment = HorizontalAlignment.Right, Style = area.Id == _selectedArea?.Id ? active : normal, FlowDirection = FlowDirection.RightToLeft };
            b.Click += DiningArea_Click; DiningAreasPanel.Children.Add(b);
        }
    }'''

new_render_areas = '''    private void RenderDiningAreas()
    {
        DiningAreasPanel.Children.Clear();
        var normal = (Style)Application.Current.Resources["CategoryButtonStyle"];
        var active = (Style)Application.Current.Resources["CategoryButtonActiveStyle"];

        foreach (var area in _diningAreas)
        {
            var label = new TextBlock
            {
                Text = area.Name,
                TextAlignment = TextAlignment.Right,
                HorizontalAlignment = HorizontalAlignment.Stretch,
                FlowDirection = FlowDirection.RightToLeft,
                FontWeight = Microsoft.UI.Text.FontWeights.SemiBold
            };
            var b = new Button
            {
                Content = label,
                Tag = area.Id,
                HorizontalAlignment = HorizontalAlignment.Stretch,
                HorizontalContentAlignment = HorizontalAlignment.Stretch,
                Style = area.Id == _selectedArea?.Id ? active : normal,
                FlowDirection = FlowDirection.RightToLeft
            };
            b.Click += DiningArea_Click;
            DiningAreasPanel.Children.Add(b);
        }
    }'''

s = replace_once(s, old_render_areas, new_render_areas, "RenderDiningAreas")

pattern = re.compile(r'''    private async Task RenderTablesAsync\(\)
    \{
.*?
    \}

    private async void Table_Click''', re.S)

new_tables = '''    private async Task RenderTablesAsync()
    {
        TablesPanel.Children.Clear();
        if (_selectedArea is null) return;
        TablesTitle.Text = _selectedArea.Name;

        var open = await App.Services.Restaurant.GetOpenOrdersAsync(RestaurantOrderType.DineIn);
        var map = open
            .Where(x => x.DiningAreaId == _selectedArea.Id && x.DiningTableNumber.HasValue)
            .ToDictionary(x => x.DiningTableNumber!.Value);

        // Five tables per row. Column 4 is the visual far-right column,
        // so table 1 is always at the far right, then 2,3,4,5 toward the left.
        for (var rowStart = 1; rowStart <= _selectedArea.TableCount; rowStart += 5)
        {
            var row = new Grid
            {
                ColumnSpacing = 10,
                HorizontalAlignment = HorizontalAlignment.Stretch,
                FlowDirection = FlowDirection.LeftToRight
            };
            for (var col = 0; col < 5; col++)
                row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

            for (var offset = 0; offset < 5; offset++)
            {
                var table = rowStart + offset;
                if (table > _selectedArea.TableCount) break;

                map.TryGetValue(table, out var order);
                var total = order?.Items.Sum(x => x.Quantity * x.UnitPrice) ?? 0;

                var panel = new StackPanel
                {
                    Spacing = 5,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    VerticalAlignment = VerticalAlignment.Center
                };
                panel.Children.Add(new TextBlock
                {
                    Text = $"طاولة {table}",
                    FontSize = 19,
                    FontWeight = Microsoft.UI.Text.FontWeights.Bold,
                    HorizontalAlignment = HorizontalAlignment.Center
                });
                panel.Children.Add(new TextBlock
                {
                    Text = order is null ? "فارغة" : $"مشغولة • {total:0.00}",
                    FontSize = 12,
                    Foreground = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources[order is null ? "MutedTextBrush" : "AccentBrushSoft"],
                    HorizontalAlignment = HorizontalAlignment.Center
                });

                var button = new Button
                {
                    Content = panel,
                    Tag = table,
                    Height = 112,
                    Margin = new Thickness(4),
                    MinWidth = 0,
                    HorizontalAlignment = HorizontalAlignment.Stretch,
                    HorizontalContentAlignment = HorizontalAlignment.Center,
                    Style = (Style)Application.Current.Resources[order is null ? "ProductCardButtonStyle" : "CategoryButtonActiveStyle"]
                };
                button.Click += Table_Click;

                // Explicitly reverse visual columns: 1 -> far right, 5 -> far left.
                Grid.SetColumn(button, 4 - offset);
                row.Children.Add(button);
            }

            TablesPanel.Children.Add(row);
        }
    }

    private async void Table_Click'''

s, n = pattern.subn(new_tables, s, count=1)
if n != 1:
    raise SystemExit(f"R8 RenderTablesAsync replacement failed: {n}")

write(p, s)

# --- Delivery: use the exact takeaway weight selection behavior ---
p = "Pages/DeliveryPage.xaml.cs"
s = read(p)

if "using Microsoft.UI.Xaml.Input;" not in s:
    s = s.replace("using Microsoft.UI.Xaml.Controls;\n", "using Microsoft.UI.Xaml.Controls;\nusing Microsoft.UI.Xaml.Input;\n")
if "using System.Globalization;" not in s:
    s = s.replace("using SweetsPOS.Models;\n", "using SweetsPOS.Models;\nusing System.Globalization;\n")

old_product = '''    private async void Product_Click(object sender, RoutedEventArgs e)
    {
        if (!await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.EditDeliveryOrder, "إضافة صنف إلى طلب الدليفري")) return;
        if (_selectedOrder is null || _selectedOrder.Status != RestaurantOrderStatus.Open || sender is not Button b || b.Tag is not int id) return;
        var p = _products.FirstOrDefault(x => x.Id == id); if (p is null) return; var q = double.IsNaN(AddQuantityBox.Value) ? 1m : (decimal)AddQuantityBox.Value; if (q <= 0) q = 1;
        var existing = _cart.FirstOrDefault(x => x.ProductId == p.Id && x.UnitPrice == p.Price); if (existing is null) _cart.Add(new CartLine { ProductId = p.Id, Name = string.IsNullOrWhiteSpace(p.ArabicName) ? p.Name : p.ArabicName, SellUnit = p.SellUnit, Quantity = q, UnitPrice = p.Price }); else existing.Quantity += q;
        await SaveCartAsync();
    }
    private async void ItemPlus_Click(object sender, RoutedEventArgs e) { if (!await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.EditDeliveryOrder, "تعديل كمية صنف في طلب الدليفري")) return; if (sender is Button b && b.Tag is int id && _cart.FirstOrDefault(x => x.ProductId == id) is { } x) { x.Quantity += 1; await SaveCartAsync(); } }
    private async void ItemMinus_Click(object sender, RoutedEventArgs e) { if (!await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.EditDeliveryOrder, "تعديل كمية صنف في طلب الدليفري")) return; if (sender is Button b && b.Tag is int id && _cart.FirstOrDefault(x => x.ProductId == id) is { } x) { x.Quantity -= 1; if (x.Quantity <= 0) _cart.Remove(x); await SaveCartAsync(); } }'''

new_product = '''    private async Task<decimal?> GetProductQuantityAsync(Product product)
    {
        if (product.SellUnit is not (SellUnit.Kg or SellUnit.Gram))
        {
            var normal = double.IsNaN(AddQuantityBox.Value) ? 1m : (decimal)AddQuantityBox.Value;
            return normal > 0 ? normal : 1m;
        }

        var isKg = product.SellUnit == SellUnit.Kg;
        var box = new TextBox
        {
            Text = isKg ? "0.5" : "500",
            FlowDirection = FlowDirection.LeftToRight,
            TextAlignment = TextAlignment.Center,
            HorizontalContentAlignment = HorizontalAlignment.Stretch,
            InputScope = new InputScope { Names = { new InputScopeName(InputScopeNameValue.Number) } }
        };
        var weightLabel = new TextBlock
        {
            Text = isKg ? "الوزن (كجم)" : "الوزن (جرام)",
            Width = 390,
            FlowDirection = FlowDirection.RightToLeft,
            TextAlignment = TextAlignment.Right,
            HorizontalAlignment = HorizontalAlignment.Stretch,
            Foreground = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["MutedTextBrush"]
        };
        var presets = new Grid
        {
            ColumnSpacing = 7,
            FlowDirection = FlowDirection.RightToLeft,
            HorizontalAlignment = HorizontalAlignment.Stretch
        };
        for (var i = 0; i < 4; i++) presets.ColumnDefinitions.Add(new ColumnDefinition());

        var presetValues = isKg ? new[] { "0.5", "1", "1.5", "2" } : new[] { "500", "1000", "1500", "2000" };
        var presetLabels = new[] { "نصف كيلو", "1 كيلو", "1.5 كيلو", "2 كيلو" };

        for (var i = 0; i < presetValues.Length; i++)
        {
            var value = presetValues[i];
            var quick = new Button
            {
                Content = presetLabels[i],
                HorizontalAlignment = HorizontalAlignment.Stretch,
                Style = (Style)Application.Current.Resources["SoftButtonStyle"]
            };
            quick.Click += (_, _) => box.Text = value;
            Grid.SetColumn(quick, i);
            presets.Children.Add(quick);
        }

        var panel = new StackPanel
        {
            Width = 390,
            Spacing = 10,
            FlowDirection = FlowDirection.RightToLeft,
            HorizontalAlignment = HorizontalAlignment.Stretch
        };
        panel.Children.Add(new TextBlock
        {
            Text = string.IsNullOrWhiteSpace(product.ArabicName) ? product.Name : product.ArabicName,
            Width = 390,
            FontSize = 20,
            FontWeight = Microsoft.UI.Text.FontWeights.Bold,
            TextAlignment = TextAlignment.Right,
            HorizontalAlignment = HorizontalAlignment.Stretch,
            FlowDirection = FlowDirection.RightToLeft
        });
        panel.Children.Add(weightLabel);
        panel.Children.Add(box);
        panel.Children.Add(presets);

        var dialog = new ContentDialog
        {
            XamlRoot = XamlRoot,
            RequestedTheme = ElementTheme.Dark,
            FlowDirection = FlowDirection.RightToLeft,
            HorizontalContentAlignment = HorizontalAlignment.Stretch,
            Title = "تحديد الكمية",
            Content = panel,
            PrimaryButtonText = "إضافة",
            CloseButtonText = "إلغاء",
            DefaultButton = ContentDialogButton.Primary
        };

        if (await dialog.ShowAsync() != ContentDialogResult.Primary) return null;
        if (!TryDecimalFromText(box.Text, out var quantity) || quantity <= 0) return null;
        return quantity;
    }

    private static bool TryDecimalFromText(string? text, out decimal value)
    {
        text = (text ?? string.Empty).Trim();
        if (decimal.TryParse(text, NumberStyles.Number, CultureInfo.CurrentCulture, out value)) return true;
        if (decimal.TryParse(text, NumberStyles.Number, CultureInfo.InvariantCulture, out value)) return true;
        value = 0;
        return false;
    }

    private static decimal IncrementFor(CartLine line) => line.SellUnit switch
    {
        SellUnit.Kg => 0.25m,
        SellUnit.Gram => 100m,
        _ => 1m
    };

    private async void Product_Click(object sender, RoutedEventArgs e)
    {
        if (!await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.EditDeliveryOrder, "إضافة صنف إلى طلب الدليفري")) return;
        if (_selectedOrder is null || _selectedOrder.Status != RestaurantOrderStatus.Open || sender is not Button b || b.Tag is not int id) return;

        var p = _products.FirstOrDefault(x => x.Id == id);
        if (p is null) return;

        var selectedQuantity = await GetProductQuantityAsync(p);
        if (!selectedQuantity.HasValue) return;
        var q = selectedQuantity.Value;

        var existing = _cart.FirstOrDefault(x => x.ProductId == p.Id && x.UnitPrice == p.Price);
        if (existing is null)
            _cart.Add(new CartLine
            {
                ProductId = p.Id,
                Name = string.IsNullOrWhiteSpace(p.ArabicName) ? p.Name : p.ArabicName,
                SellUnit = p.SellUnit,
                Quantity = q,
                UnitPrice = p.Price
            });
        else
            existing.Quantity += q;

        await SaveCartAsync();
    }

    private async void ItemPlus_Click(object sender, RoutedEventArgs e)
    {
        if (!await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.EditDeliveryOrder, "تعديل كمية صنف في طلب الدليفري")) return;
        if (sender is Button b && b.Tag is int id && _cart.FirstOrDefault(x => x.ProductId == id) is { } x)
        {
            x.Quantity += IncrementFor(x);
            await SaveCartAsync();
        }
    }

    private async void ItemMinus_Click(object sender, RoutedEventArgs e)
    {
        if (!await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.EditDeliveryOrder, "تعديل كمية صنف في طلب الدليفري")) return;
        if (sender is Button b && b.Tag is int id && _cart.FirstOrDefault(x => x.ProductId == id) is { } x)
        {
            x.Quantity -= IncrementFor(x);
            if (x.Quantity <= 0) _cart.Remove(x);
            await SaveCartAsync();
        }
    }'''

s = replace_once(s, old_product, new_product, "delivery weighted products")
write(p, s)


# --- Delivery bottom action bar: one clean responsive row for open-order actions ---
p = "Pages/DeliveryPage.xaml"
sx = read(p)
old_actions = '''                            <Grid ColumnSpacing="6"><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions><Button x:Name="KitchenButton" Content="إرسال للمطبخ" Click="Kitchen_Click" Style="{StaticResource SoftButtonStyle}"/><Button Grid.Column="1" x:Name="DispatchButton" Content="تحميل على الطيار" Click="Dispatch_Click" Style="{StaticResource AccentButtonStyle}"/></Grid>
                            <Grid ColumnSpacing="6"><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions><Button x:Name="ReturnButton" Content="مرتجع" Click="Return_Click" Style="{StaticResource DangerButtonStyle}" Visibility="Collapsed"/><Button Grid.Column="1" x:Name="CancelDeliveryButton" Content="إلغاء الطلب" Click="CancelDelivery_Click" Style="{StaticResource DangerButtonStyle}"/></Grid>
                            <Button x:Name="OpenSettlementButton" Content="فتح تسوية الطيار لهذا الطلب" Click="OpenSettlement_Click" Style="{StaticResource AccentButtonStyle}" Visibility="Collapsed"/>'''
new_actions = '''                            <Border Background="{StaticResource CardBrushSoft}" CornerRadius="10" Padding="8">
                                <Grid ColumnSpacing="8">
                                    <Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions>
                                    <Button x:Name="KitchenButton" Content="إرسال للمطبخ" Click="Kitchen_Click" Style="{StaticResource SoftButtonStyle}" Height="48" HorizontalAlignment="Stretch" HorizontalContentAlignment="Center"/>
                                    <Button Grid.Column="1" x:Name="DispatchButton" Content="تحميل على الطيار" Click="Dispatch_Click" Style="{StaticResource AccentButtonStyle}" Height="48" HorizontalAlignment="Stretch" HorizontalContentAlignment="Center"/>
                                    <Button Grid.Column="2" x:Name="CancelDeliveryButton" Content="إلغاء الطلب" Click="CancelDelivery_Click" Style="{StaticResource DangerButtonStyle}" Height="48" HorizontalAlignment="Stretch" HorizontalContentAlignment="Center"/>
                                </Grid>
                            </Border>
                            <StackPanel Spacing="6">
                                <Button x:Name="ReturnButton" Content="مرتجع / لم يتم التسليم" Click="Return_Click" Style="{StaticResource DangerButtonStyle}" Visibility="Collapsed" Height="46" HorizontalAlignment="Stretch" HorizontalContentAlignment="Center"/>
                                <Button x:Name="OpenSettlementButton" Content="فتح تسوية الطيار لهذا الطلب" Click="OpenSettlement_Click" Style="{StaticResource AccentButtonStyle}" Visibility="Collapsed" Height="46" HorizontalAlignment="Stretch" HorizontalContentAlignment="Center"/>
                            </StackPanel>'''
sx = replace_once(sx, old_actions, new_actions, "delivery action bar")
write(p, sx)

print("R8 dining direction and dining, weighted delivery, and action-bar fixes applied.")
