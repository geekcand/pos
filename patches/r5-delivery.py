from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()

def read(rel):
    return (root / rel).read_text(encoding="utf-8-sig")

def write(rel, text):
    (root / rel).write_text(text, encoding="utf-8-sig")

def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"R5 delivery patch missing anchor: {label}")
    return text.replace(old, new, 1)

# Delivery product picker: departments first, search across all products.
p = "Pages/DeliveryPage.xaml"
s = read(p)

old = '<Grid><Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/><RowDefinition Height="*"/></Grid.RowDefinitions><TextBlock Text="إضافة أصناف للطلب" Style="{StaticResource SubTitleStyle}"/><Grid Grid.Row="1" Margin="0,10,0,8" ColumnSpacing="6"><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="105"/></Grid.ColumnDefinitions><TextBox x:Name="ProductSearchBox" PlaceholderText="ابحث عن صنف أو باركود" TextChanged="ProductSearchBox_TextChanged"/><NumberBox Grid.Column="1" x:Name="AddQuantityBox" Header="الكمية" Value="1" Minimum="0.001" SpinButtonPlacementMode="Compact"/></Grid><GridView Grid.Row="2" x:Name="ProductsGrid" SelectionMode="None" HorizontalContentAlignment="Stretch"><GridView.ItemsPanel><ItemsPanelTemplate><ItemsWrapGrid Orientation="Horizontal" ItemWidth="165" ItemHeight="118"/></ItemsPanelTemplate></GridView.ItemsPanel><GridView.ItemTemplate><DataTemplate><Button Tag="{Binding Id}" Click="Product_Click" Style="{StaticResource ProductCardButtonStyle}" MinHeight="108" MinWidth="155" Margin="4"><StackPanel HorizontalAlignment="Center" VerticalAlignment="Center" Spacing="5"><TextBlock Text="{Binding ArabicName}" TextWrapping="Wrap" TextAlignment="Center" FontWeight="SemiBold" MaxLines="2"/><TextBlock Text="{Binding Price}" Foreground="{StaticResource AccentBrushSoft}" FontSize="17" FontWeight="Bold"/></StackPanel></Button></DataTemplate></GridView.ItemTemplate></GridView></Grid>'

new = '<Grid><Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/><RowDefinition Height="*"/></Grid.RowDefinitions><TextBlock Text="إضافة أصناف للطلب" Style="{StaticResource SubTitleStyle}"/><Grid Grid.Row="1" Margin="0,10,0,8" ColumnSpacing="6"><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="105"/></Grid.ColumnDefinitions><TextBox x:Name="ProductSearchBox" PlaceholderText="ابحث بالاسم أو الباركود في كل الأصناف" TextChanged="ProductSearchBox_TextChanged"/><NumberBox Grid.Column="1" x:Name="AddQuantityBox" Header="الكمية" Value="1" Minimum="0.001" SpinButtonPlacementMode="Compact"/></Grid><StackPanel Grid.Row="2" Spacing="6" Margin="0,0,0,8"><TextBlock Text="الأقسام" FontWeight="SemiBold" Foreground="{StaticResource MutedTextBrush}"/><ScrollViewer HorizontalScrollBarVisibility="Auto" VerticalScrollBarVisibility="Disabled"><StackPanel x:Name="ProductCategoriesPanel" Orientation="Horizontal" Spacing="6"/></ScrollViewer><TextBlock x:Name="ProductPickerHint" Text="اختر قسمًا لعرض أصنافه — أو استخدم البحث للوصول لأي صنف مباشرة." FontSize="11" Foreground="{StaticResource HintTextBrush}" TextWrapping="Wrap"/></StackPanel><GridView Grid.Row="3" x:Name="ProductsGrid" SelectionMode="None" HorizontalContentAlignment="Stretch"><GridView.ItemsPanel><ItemsPanelTemplate><ItemsWrapGrid Orientation="Horizontal" ItemWidth="165" ItemHeight="118"/></ItemsPanelTemplate></GridView.ItemsPanel><GridView.ItemTemplate><DataTemplate><Button Tag="{Binding Id}" Click="Product_Click" Style="{StaticResource ProductCardButtonStyle}" MinHeight="108" MinWidth="155" Margin="4"><StackPanel HorizontalAlignment="Center" VerticalAlignment="Center" Spacing="5"><TextBlock Text="{Binding ArabicName}" TextWrapping="Wrap" TextAlignment="Center" FontWeight="SemiBold" MaxLines="2"/><TextBlock Text="{Binding Price}" Foreground="{StaticResource AccentBrushSoft}" FontSize="17" FontWeight="Bold"/></StackPanel></Button></DataTemplate></GridView.ItemTemplate></GridView></Grid>'

s = replace_once(s, old, new, "product picker")

old_actions = '<Grid ColumnSpacing="6"><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions><Button x:Name="KitchenButton" Content="إرسال للمطبخ" Click="Kitchen_Click" Style="{StaticResource SoftButtonStyle}"/><Button Grid.Column="1" x:Name="DispatchButton" Content="تحميل على الطيار" Click="Dispatch_Click" Style="{StaticResource AccentButtonStyle}"/><Button Grid.Column="2" x:Name="ReturnButton" Content="مرتجع" Click="Return_Click" Style="{StaticResource DangerButtonStyle}" Visibility="Collapsed"/></Grid>'
new_actions = '<Grid ColumnSpacing="6"><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions><Button x:Name="KitchenButton" Content="إرسال للمطبخ" Click="Kitchen_Click" Style="{StaticResource SoftButtonStyle}"/><Button Grid.Column="1" x:Name="DispatchButton" Content="تحميل على الطيار" Click="Dispatch_Click" Style="{StaticResource AccentButtonStyle}"/><Button Grid.Column="2" x:Name="ReturnButton" Content="مرتجع" Click="Return_Click" Style="{StaticResource DangerButtonStyle}" Visibility="Collapsed"/><Button Grid.Column="3" x:Name="CancelDeliveryButton" Content="إلغاء الطلب" Click="CancelDelivery_Click" Style="{StaticResource DangerButtonStyle}"/></Grid>'
s = replace_once(s, old_actions, new_actions, "delivery actions")
write(p, s)

p = "Pages/DeliveryPage.xaml.cs"
s = read(p)

s = replace_once(s,
"""    private List<Product> _products = [];""",
"""    private List<Product> _products = [];
    private List<Category> _categories = [];
    private int? _selectedCategoryId;""",
"category fields")

s = replace_once(s,
"""        await LoadProductsAsync(); await RefreshOrdersAsync(); await RefreshCustomersAsync();""",
"""        await LoadProductCategoriesAsync(); await LoadProductsAsync(); await RefreshOrdersAsync(); await RefreshCustomersAsync();""",
"load categories")

old_loader = """    private async Task LoadProductsAsync()
    {
        var q = ProductSearchBox?.Text?.Trim(); _products = await App.Services.Catalog.GetProductsAsync(null, q, true); ProductsGrid.ItemsSource = _products;
    }
    private async void ProductSearchBox_TextChanged(object sender, TextChangedEventArgs e) => await LoadProductsAsync();"""

new_loader = r'''    private async Task LoadProductCategoriesAsync()
    {
        _categories = await App.Services.Catalog.GetCategoriesAsync();
        ProductCategoriesPanel.Children.Clear();
        foreach (var category in _categories)
        {
            var button = new Button
            {
                Content = category.Name,
                Tag = category.Id,
                Style = (Style)Application.Current.Resources[_selectedCategoryId == category.Id ? "CategoryButtonActiveStyle" : "CategoryButtonStyle"],
                MinWidth = 105,
                Padding = new Thickness(12, 7, 12, 7)
            };
            button.Click += ProductCategory_Click;
            ProductCategoriesPanel.Children.Add(button);
        }
    }

    private async Task LoadProductsAsync()
    {
        var q = ProductSearchBox?.Text?.Trim();
        if (!string.IsNullOrWhiteSpace(q))
        {
            _products = await App.Services.Catalog.GetProductsAsync(null, q, true);
            ProductPickerHint.Text = $"نتائج البحث: {_products.Count} صنف — البحث يشمل كل الأقسام.";
        }
        else if (_selectedCategoryId.HasValue)
        {
            _products = await App.Services.Catalog.GetProductsAsync(_selectedCategoryId.Value, null, true);
            var category = _categories.FirstOrDefault(x => x.Id == _selectedCategoryId.Value);
            ProductPickerHint.Text = $"قسم: {category?.Name ?? "—"} • {_products.Count} صنف";
        }
        else
        {
            _products = [];
            ProductPickerHint.Text = "اختر قسمًا لعرض أصنافه — أو استخدم البحث للوصول لأي صنف مباشرة.";
        }
        ProductsGrid.ItemsSource = _products;
    }

    private async void ProductCategory_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button button || !int.TryParse(button.Tag?.ToString(), out var id)) return;
        _selectedCategoryId = id;
        ProductSearchBox.Text = "";
        await LoadProductCategoriesAsync();
        await LoadProductsAsync();
    }

    private async void ProductSearchBox_TextChanged(object sender, TextChangedEventArgs e) => await LoadProductsAsync();'''

s = replace_once(s, old_loader, new_loader, "product load logic")

s = s.replace(
'KitchenButton.IsEnabled = DispatchButton.IsEnabled = false; ReturnButton.Visibility = OpenSettlementButton.Visibility = Visibility.Collapsed; ReturnReasonBox.Visibility = Visibility.Collapsed; return;',
'KitchenButton.IsEnabled = DispatchButton.IsEnabled = false; CancelDeliveryButton.Visibility = Visibility.Collapsed; ReturnButton.Visibility = OpenSettlementButton.Visibility = Visibility.Collapsed; ReturnReasonBox.Visibility = Visibility.Collapsed; return;')

s = replace_once(s,
"""        ReturnButton.Visibility = OpenSettlementButton.Visibility = o.Status == RestaurantOrderStatus.OutForDelivery ? Visibility.Visible : Visibility.Collapsed;
        ReturnReasonBox.Visibility = o.Status == RestaurantOrderStatus.OutForDelivery ? Visibility.Visible : Visibility.Collapsed;""",
"""        CancelDeliveryButton.Visibility = open ? Visibility.Visible : Visibility.Collapsed;
        ReturnButton.Visibility = OpenSettlementButton.Visibility = o.Status == RestaurantOrderStatus.OutForDelivery ? Visibility.Visible : Visibility.Collapsed;
        ReturnReasonBox.Visibility = o.Status == RestaurantOrderStatus.OutForDelivery ? Visibility.Visible : Visibility.Collapsed;""",
"cancel visibility")

s = replace_once(s,
"""    private async void Dispatch_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedOrder is null || _selectedOrder.Status != RestaurantOrderStatus.Open || CourierCombo.SelectedItem is not CourierOption courier)""",
"""    private async void Dispatch_Click(object sender, RoutedEventArgs e)
    {
        if (!await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.DispatchDelivery, "تحميل طلب دليفري على طيار")) return;
        if (_selectedOrder is null || _selectedOrder.Status != RestaurantOrderStatus.Open || CourierCombo.SelectedItem is not CourierOption courier)""",
"dispatch permission")

s = replace_once(s,
"""    private async void Return_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedOrder is null) return;""",
"""    private async void Return_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedOrder is null) return;
        if (!await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.ReturnDeliveryOrder, $"تسجيل طلب الدليفري #{_selectedOrder.Id} كمرتجع / لم يتم التسليم", managerApprovalForCashier: true)) return;""",
"return permission")

s = replace_once(s,
"""    private async void SettleSelected_Click(object sender, RoutedEventArgs e)
    {
        var rows =""",
"""    private async void SettleSelected_Click(object sender, RoutedEventArgs e)
    {
        if (!await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.SettleDelivery, "تسوية الطيار واستلام الكاش")) return;
        var rows =""",
"settlement permission")

needle = """    private async void OpenSettlement_Click(object sender, RoutedEventArgs e)"""
cancel_method = r'''    private async void CancelDelivery_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedOrder is null || _selectedOrder.Status != RestaurantOrderStatus.Open) return;
        if (!await PageHelpers.RequirePermissionAsync(XamlRoot, Permission.CancelDeliveryOrder, $"إلغاء طلب الدليفري #{_selectedOrder.Id}", managerApprovalForCashier: true)) return;

        var confirm = new ContentDialog
        {
            XamlRoot = XamlRoot,
            RequestedTheme = ElementTheme.Dark,
            FlowDirection = FlowDirection.RightToLeft,
            Title = $"إلغاء طلب الدليفري #{_selectedOrder.Id}؟",
            Content = "سيتم إلغاء الطلب وإزالته من الطلبات المفتوحة مع الاحتفاظ به في سجل المراجعة.",
            PrimaryButtonText = "إلغاء الطلب",
            CloseButtonText = "رجوع",
            DefaultButton = ContentDialogButton.Close
        };
        if (await confirm.ShowAsync() != ContentDialogResult.Primary) return;

        await App.Services.Restaurant.CancelAsync(_selectedOrder.Id);
        _selectedOrder = null;
        _cart.Clear();
        await RefreshOrdersAsync();
        await RefreshCustomersAsync();
    }

''' + needle

s = replace_once(s, needle, cancel_method, "cancel delivery method")
write(p, s)

print("Restaurant R5 delivery categories patch applied.")
