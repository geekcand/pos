from pathlib import Path
import re,sys
root=Path(sys.argv[1])
px=root/'Pages/DeliveryPage.xaml'
s=px.read_text(encoding='utf-8-sig')
start=s.index('            <Grid x:Name="OrdersView">')
end=s.index('            <Grid x:Name="NewOrderView"', start)
new='''            <Grid x:Name="OrdersView" ColumnSpacing="10">
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="300"/>
                    <ColumnDefinition Width="1.15*"/>
                    <ColumnDefinition Width="1*"/>
                    <ColumnDefinition Width="250"/>
                </Grid.ColumnDefinitions>

                <!-- 1: right side - delivery orders -->
                <Border Grid.Column="0" Style="{StaticResource CardStyle}">
                    <Grid>
                        <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/><RowDefinition Height="*"/></Grid.RowDefinitions>
                        <TextBlock Text="طلبات الدليفري" Style="{StaticResource SubTitleStyle}"/>
                        <Grid Grid.Row="1" Margin="0,10,0,8" ColumnSpacing="6">
                            <Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="115"/></Grid.ColumnDefinitions>
                            <TextBox x:Name="OrderSearchBox" PlaceholderText="رقم الطلب / العميل / الموبايل" TextChanged="OrderSearchBox_TextChanged"/>
                            <ComboBox Grid.Column="1" x:Name="OrderStatusFilter" SelectionChanged="OrderStatusFilter_SelectionChanged">
                                <ComboBoxItem Content="الكل" Tag="all"/><ComboBoxItem Content="قيد التجهيز" Tag="open"/><ComboBoxItem Content="مع الطيار" Tag="out"/>
                            </ComboBox>
                        </Grid>
                        <ListView Grid.Row="2" x:Name="DeliveryOrdersList" SelectionChanged="DeliveryOrdersList_SelectionChanged" SelectionMode="Single" HorizontalContentAlignment="Stretch">
                            <ListView.ItemTemplate><DataTemplate><Border BorderBrush="{StaticResource BorderBrushSoft}" BorderThickness="0,0,0,1" Padding="9"><StackPanel Spacing="3"><Grid><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions><TextBlock Text="{Binding Title}" FontWeight="Bold" Foreground="{StaticResource LightTextBrush}"/><TextBlock Grid.Column="1" Text="{Binding TotalText}" Foreground="{StaticResource AccentBrushSoft}" FontWeight="Bold"/></Grid><TextBlock Text="{Binding AddressText}" Foreground="{StaticResource MutedTextBrush}" TextWrapping="Wrap" FontSize="12"/><Grid><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions><TextBlock Text="{Binding StatusText}" Foreground="{StaticResource SuccessSoftBrush}" FontSize="12"/><TextBlock Grid.Column="1" Text="{Binding TimeText}" Foreground="{StaticResource HintTextBrush}" FontSize="11"/></Grid></StackPanel></Border></DataTemplate></ListView.ItemTemplate>
                        </ListView>
                    </Grid>
                </Border>

                <!-- 2: current order / added items -->
                <Border Grid.Column="1" Style="{StaticResource CardStyle}">
                    <Grid>
                        <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/><RowDefinition Height="*"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
                        <Grid><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions><StackPanel><TextBlock x:Name="SelectedOrderTitle" Text="اختر طلبًا" Style="{StaticResource SubTitleStyle}"/><TextBlock x:Name="SelectedOrderStatus" Foreground="{StaticResource AccentBrushSoft}"/></StackPanel><Button Grid.Column="1" Content="تحديث" Click="Refresh_Click" Style="{StaticResource SoftButtonStyle}"/></Grid>
                        <Border Grid.Row="1" Background="{StaticResource CardBrushSoft}" CornerRadius="10" Padding="12" Margin="0,10"><StackPanel Spacing="4"><TextBlock x:Name="CustomerSummaryText" Text="—" FontWeight="SemiBold"/><TextBlock x:Name="CustomerAddressText" Text="—" Foreground="{StaticResource MutedTextBrush}" TextWrapping="Wrap"/><TextBlock x:Name="OrderNotesText" Foreground="{StaticResource HintTextBrush}" TextWrapping="Wrap"/></StackPanel></Border>
                        <ListView Grid.Row="2" x:Name="OrderItemsList" SelectionMode="None"><ListView.ItemTemplate><DataTemplate><Border BorderBrush="{StaticResource BorderBrushSoft}" BorderThickness="0,0,0,1" Padding="8"><Grid ColumnSpacing="7"><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="75"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions><StackPanel><TextBlock Text="{Binding Name}" FontWeight="SemiBold" TextWrapping="Wrap"/><TextBlock Text="{Binding PriceText}" Foreground="{StaticResource MutedTextBrush}" FontSize="11"/></StackPanel><TextBlock Grid.Column="1" Text="{Binding QuantityText}" VerticalAlignment="Center" HorizontalAlignment="Center"/><StackPanel Grid.Column="2" Orientation="Horizontal" Spacing="3"><Button Content="−" Tag="{Binding ProductId}" Click="ItemMinus_Click" Style="{StaticResource SoftButtonStyle}" Padding="7,3"/><Button Content="+" Tag="{Binding ProductId}" Click="ItemPlus_Click" Style="{StaticResource SoftButtonStyle}" Padding="7,3"/><Button Content="×" Tag="{Binding ProductId}" Click="ItemRemove_Click" Style="{StaticResource DangerButtonStyle}" Padding="7,3"/></StackPanel></Grid></Border></DataTemplate></ListView.ItemTemplate></ListView>
                        <StackPanel Grid.Row="3" Spacing="8" Margin="0,10,0,0">
                            <Grid><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions><TextBlock Text="الإجمالي" FontSize="20" FontWeight="Bold"/><TextBlock Grid.Column="1" x:Name="OrderTotalText" FontSize="22" FontWeight="ExtraBold" Foreground="{StaticResource AccentBrushSoft}"/></Grid>
                            <ComboBox x:Name="CourierCombo" Header="الطيار" HorizontalAlignment="Stretch"/>
                            <TextBox x:Name="ReturnReasonBox" Header="سبب المرتجع / عدم التسليم" PlaceholderText="يظهر عند رجوع الطلب بدون تسليم" Visibility="Collapsed" TextWrapping="Wrap" AcceptsReturn="True" MinHeight="62"/>
                            <Grid ColumnSpacing="6"><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions><Button x:Name="KitchenButton" Content="إرسال للمطبخ" Click="Kitchen_Click" Style="{StaticResource SoftButtonStyle}"/><Button Grid.Column="1" x:Name="DispatchButton" Content="تحميل على الطيار" Click="Dispatch_Click" Style="{StaticResource AccentButtonStyle}"/><Button Grid.Column="2" x:Name="ReturnButton" Content="مرتجع" Click="Return_Click" Style="{StaticResource DangerButtonStyle}" Visibility="Collapsed"/><Button Grid.Column="3" x:Name="CancelDeliveryButton" Content="إلغاء الطلب" Click="CancelDelivery_Click" Style="{StaticResource DangerButtonStyle}"/></Grid>
                            <Button x:Name="OpenSettlementButton" Content="فتح تسوية الطيار لهذا الطلب" Click="OpenSettlement_Click" Style="{StaticResource AccentButtonStyle}" Visibility="Collapsed"/>
                        </StackPanel>
                    </Grid>
                </Border>

                <!-- 3: products of selected category -->
                <Border Grid.Column="2" Style="{StaticResource CardStyle}">
                    <Grid>
                        <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/><RowDefinition Height="*"/></Grid.RowDefinitions>
                        <TextBlock Text="أصناف القسم" Style="{StaticResource SubTitleStyle}"/>
                        <Grid Grid.Row="1" Margin="0,10,0,8" ColumnSpacing="6">
                            <Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition Width="95"/></Grid.ColumnDefinitions>
                            <TextBox x:Name="ProductSearchBox" PlaceholderText="ابحث بالاسم أو الباركود" TextChanged="ProductSearchBox_TextChanged"/>
                            <NumberBox Grid.Column="1" x:Name="AddQuantityBox" Header="الكمية" Value="1" Minimum="0.001" SpinButtonPlacementMode="Compact"/>
                        </Grid>
                        <TextBlock Grid.Row="2" x:Name="ProductPickerHint" Text="اختر قسمًا من القائمة لعرض أصنافه — أو استخدم البحث." FontSize="11" Foreground="{StaticResource HintTextBrush}" TextWrapping="Wrap" Margin="0,0,0,8"/>
                        <GridView Grid.Row="3" x:Name="ProductsGrid" SelectionMode="None" HorizontalContentAlignment="Stretch" VerticalContentAlignment="Top">
                            <GridView.ItemsPanel><ItemsPanelTemplate><ItemsWrapGrid Orientation="Horizontal" ItemWidth="145" ItemHeight="112"/></ItemsPanelTemplate></GridView.ItemsPanel>
                            <GridView.ItemTemplate><DataTemplate><Button Tag="{Binding Id}" Click="Product_Click" Style="{StaticResource ProductCardButtonStyle}" MinHeight="102" MinWidth="135" Margin="4"><StackPanel HorizontalAlignment="Center" VerticalAlignment="Center" Spacing="5"><TextBlock Text="{Binding ArabicName}" TextWrapping="Wrap" TextAlignment="Center" FontWeight="SemiBold" MaxLines="2"/><TextBlock Text="{Binding Price}" Foreground="{StaticResource AccentBrushSoft}" FontSize="17" FontWeight="Bold"/></StackPanel></Button></DataTemplate></GridView.ItemTemplate>
                        </GridView>
                    </Grid>
                </Border>

                <!-- 4: left side - categories, exactly two cards per row -->
                <Border Grid.Column="3" Style="{StaticResource CardStyle}">
                    <Grid>
                        <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/><RowDefinition Height="*"/></Grid.RowDefinitions>
                        <TextBlock Text="الأقسام" Style="{StaticResource SubTitleStyle}"/>
                        <TextBlock Grid.Row="1" Text="اختر القسم" Foreground="{StaticResource MutedTextBrush}" FontSize="12" Margin="0,4,0,10"/>
                        <ScrollViewer Grid.Row="2" VerticalScrollBarVisibility="Auto" HorizontalScrollBarVisibility="Disabled" HorizontalContentAlignment="Stretch">
                            <StackPanel x:Name="ProductCategoriesPanel" Spacing="8" HorizontalAlignment="Stretch"/>
                        </ScrollViewer>
                    </Grid>
                </Border>
            </Grid>

'''
s=s[:start]+new+s[end:]
px.write_text(s,encoding='utf-8-sig')

pc=root/'Pages/DeliveryPage.xaml.cs'
c=pc.read_text(encoding='utf-8-sig')
pat=r'''    private async Task LoadProductCategoriesAsync\(\)\n    \{.*?\n    \}\n\n    private async Task LoadProductsAsync\(\)'''
rep='''    private async Task LoadProductCategoriesAsync()
    {
        _categories = await App.Services.Catalog.GetCategoriesAsync();
        ProductCategoriesPanel.Children.Clear();

        for (var i = 0; i < _categories.Count; i += 2)
        {
            var row = new Grid { ColumnSpacing = 8, HorizontalAlignment = HorizontalAlignment.Stretch };
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

            for (var slot = 0; slot < 2 && i + slot < _categories.Count; slot++)
            {
                var category = _categories[i + slot];
                var button = new Button
                {
                    Content = category.Name,
                    Tag = category.Id,
                    Style = (Style)Application.Current.Resources[_selectedCategoryId == category.Id ? "CategoryButtonActiveStyle" : "CategoryButtonStyle"],
                    HorizontalAlignment = HorizontalAlignment.Stretch,
                    HorizontalContentAlignment = HorizontalAlignment.Center,
                    MinHeight = 58,
                    Padding = new Thickness(6, 8, 6, 8)
                };
                button.Click += ProductCategory_Click;
                Grid.SetColumn(button, slot);
                row.Children.Add(button);
            }

            ProductCategoriesPanel.Children.Add(row);
        }
    }

    private async Task LoadProductsAsync()'''
c,n=re.subn(pat,rep,c,flags=re.S)
if n!=1: raise SystemExit(f'category loader replace count {n}')
pc.write_text(c,encoding='utf-8-sig')
print('R6 four-column delivery layout applied')
