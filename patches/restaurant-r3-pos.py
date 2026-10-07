from pathlib import Path
import re
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()

# PosPage: SetMode button visibility
p=root/'Pages/PosPage.xaml.cs'; s=p.read_text(encoding='utf-8-sig')
s=s.replace('''        SendKitchenButton.Visibility = _restaurantOrder is not null ? Visibility.Visible : Visibility.Collapsed;
        CancelRestaurantOrderButton.Visibility = _restaurantOrder is not null ? Visibility.Visible : Visibility.Collapsed;''','''        SendKitchenButton.Visibility = _restaurantOrder is not null ? Visibility.Visible : Visibility.Collapsed;
        DispatchDeliveryButton.Visibility = mode == RestaurantOrderType.Delivery && _restaurantOrder is not null && _restaurantOrder.Status == RestaurantOrderStatus.Open ? Visibility.Visible : Visibility.Collapsed;
        CancelRestaurantOrderButton.Visibility = _restaurantOrder is not null ? Visibility.Visible : Visibility.Collapsed;''')

# Replace DeliveryTab_Click method through before CreateDeliveryOrderAsync
pat=r'''    private async void DeliveryTab_Click\(object sender, RoutedEventArgs e\)
    \{.*?
    \}

    private async Task CreateDeliveryOrderAsync\(\)'''
new='''    private async void DeliveryTab_Click(object sender, RoutedEventArgs e)
    {
        if (App.Services.Session.CurrentShift is null) { await PageHelpers.MessageAsync(XamlRoot, "الوردية مطلوبة", "افتح وردية قبل إنشاء أو تسوية طلب دليفري."); return; }
        await SaveCurrentBeforeSwitchAsync();
        _couriers = await App.Services.Restaurant.GetCouriersAsync();
        var orders = await App.Services.Restaurant.GetDeliveryOrdersAsync();

        var rows = orders.Select(x =>
        {
            var total = x.Items.Sum(i => i.Quantity * i.UnitPrice) + x.DeliveryFee;
            var status = x.Status == RestaurantOrderStatus.OutForDelivery ? $"خرج مع {x.CourierName}" : "قيد التجهيز";
            return $"طلب #{x.Id}  •  {x.CustomerName ?? x.CustomerPhone ?? "عميل"}  •  {x.DeliveryZoneName}  •  {status}  •  {total:0.00} جنيه";
        }).ToList();

        var list = new ListView
        {
            Header = "طلبات الدليفري المفتوحة", ItemsSource = rows, SelectedIndex = rows.Count > 0 ? 0 : -1,
            SelectionMode = ListViewSelectionMode.Single, MaxHeight = 420, MinHeight = rows.Count > 0 ? 180 : 80,
            HorizontalAlignment = HorizontalAlignment.Stretch, FlowDirection = FlowDirection.RightToLeft
        };
        var hint = new TextBlock
        {
            Text = rows.Count == 0 ? "لا توجد طلبات دليفري مفتوحة حاليًا." : "اختر طلبًا لفتحه أو تحميله على طيار أو تسويته عند الرجوع.",
            TextWrapping = TextWrapping.Wrap, Foreground = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["MutedTextBrush"]
        };
        var panel = new StackPanel { Width = 660, Spacing = 10, FlowDirection = FlowDirection.RightToLeft }; panel.Children.Add(hint); panel.Children.Add(list);
        var chooser = new ContentDialog
        {
            XamlRoot = XamlRoot, RequestedTheme = ElementTheme.Dark, Title = "قائمة الدليفري", Content = panel,
            PrimaryButtonText = rows.Count > 0 ? "فتح الطلب المحدد" : "", SecondaryButtonText = "+ طلب دليفري جديد", CloseButtonText = "إغلاق",
            FlowDirection = FlowDirection.RightToLeft
        };
        var result = await chooser.ShowAsync();
        if (result == ContentDialogResult.Secondary) { await CreateDeliveryOrderAsync(); return; }
        if (result != ContentDialogResult.Primary || list.SelectedIndex < 0 || list.SelectedIndex >= orders.Count) { SetMode(RestaurantOrderType.Takeaway); return; }
        await ShowDeliveryOrderActionsAsync(orders[list.SelectedIndex]);
    }

    private async Task CreateDeliveryOrderAsync()'''
s,n=re.subn(pat,new,s,flags=re.S)
if n!=1: raise SystemExit(f'DeliveryTab replace count {n}')

# Replace ShowDeliveryOrderActionsAsync through AssignCourierAndPrintAsync signature
pat=r'''    private async Task ShowDeliveryOrderActionsAsync\(RestaurantOrder order\)
    \{.*?
    \}

    private async Task AssignCourierAndPrintAsync\(RestaurantOrder order\)'''
new='''    private async Task ShowDeliveryOrderActionsAsync(RestaurantOrder order)
    {
        if (order.Status == RestaurantOrderStatus.Open)
        {
            var actions = new ComboBox { Header = $"طلب #{order.Id} • {order.CustomerName}", HorizontalAlignment = HorizontalAlignment.Stretch };
            actions.Items.Add("فتح وتعديل الطلب"); actions.Items.Add("تحميل على طيار وطباعة"); actions.SelectedIndex = 0;
            var dlg = new ContentDialog { XamlRoot = XamlRoot, RequestedTheme = ElementTheme.Dark, Title = "طلب دليفري مفتوح", Content = actions, PrimaryButtonText = "تنفيذ", CloseButtonText = "رجوع", FlowDirection = FlowDirection.RightToLeft };
            if (await dlg.ShowAsync() != ContentDialogResult.Primary) { SetMode(RestaurantOrderType.Takeaway); return; }
            if (actions.SelectedIndex == 0)
            {
                _restaurantOrder = order; _cart.Clear(); _cart.AddRange(await App.Services.Restaurant.GetCartAsync(order.Id)); SetMode(RestaurantOrderType.Delivery); BarcodeBox.Focus(FocusState.Programmatic); return;
            }
            await AssignCourierAndPrintAsync(order);
        }
        else if (order.Status == RestaurantOrderStatus.OutForDelivery)
        {
            var actions = new ComboBox { Header = $"خرج مع {order.CourierName}", HorizontalAlignment = HorizontalAlignment.Stretch };
            actions.Items.Add("تسوية طلبات مختارة من حمولة الطيار");
            actions.Items.Add("مرتجع / لم يتم التسليم");
            actions.Items.Add("إعادة طباعة فاتورة الطلب");
            actions.Items.Add("إعادة طباعة كشف تحميل الطيار");
            actions.SelectedIndex = 0;
            var dlg = new ContentDialog { XamlRoot = XamlRoot, RequestedTheme = ElementTheme.Dark, Title = $"طلب دليفري #{order.Id}", Content = actions, PrimaryButtonText = "تنفيذ", CloseButtonText = "رجوع", FlowDirection = FlowDirection.RightToLeft };
            if (await dlg.ShowAsync() != ContentDialogResult.Primary) { SetMode(RestaurantOrderType.Takeaway); return; }
            if (actions.SelectedIndex == 0) await SettleCourierAsync(order);
            else if (actions.SelectedIndex == 1) await ReturnDeliveryAsync(order);
            else if (actions.SelectedIndex == 2) await PrintDeliveryOrderAsync(order);
            else await ReprintCourierManifestAsync(order);
        }
        SetMode(RestaurantOrderType.Takeaway);
    }

    private async Task AssignCourierAndPrintAsync(RestaurantOrder order)'''
s,n=re.subn(pat,new,s,flags=re.S)
if n!=1: raise SystemExit(f'Actions replace count {n}')

# Replace AssignCourierAndPrintAsync body through PrintDeliveryOrder signature
pat=r'''    private async Task AssignCourierAndPrintAsync\(RestaurantOrder order\)
    \{.*?
    \}

    private async Task PrintDeliveryOrderAsync\(RestaurantOrder order\)'''
new='''    private async Task AssignCourierAndPrintAsync(RestaurantOrder order)
    {
        if (_couriers.Count == 0) { await PageHelpers.MessageAsync(XamlRoot, "الطيارين", "أضف طيارًا واحدًا على الأقل من الإعدادات."); return; }
        var courierBox = new ComboBox { Header = "اختر الطيار", ItemsSource = _couriers, SelectedIndex = 0, HorizontalAlignment = HorizontalAlignment.Stretch };
        var dlg = new ContentDialog { XamlRoot = XamlRoot, RequestedTheme = ElementTheme.Dark, Title = $"تحميل طلب #{order.Id} على طيار", Content = courierBox, PrimaryButtonText = "تحميل وطباعة", CloseButtonText = "إلغاء", FlowDirection = FlowDirection.RightToLeft };
        if (await dlg.ShowAsync() != ContentDialogResult.Primary || courierBox.SelectedItem is not CourierOption courier) return;

        var fresh = await App.Services.Restaurant.GetOrderAsync(order.Id) ?? order;
        if (fresh.Items.Count == 0) { await PageHelpers.MessageAsync(XamlRoot, "الدليفري", "أضف أصنافًا للطلب أولاً."); return; }
        var printer = await App.Services.Settings.GetAsync("ReceiptPrinter", "");
        if (string.IsNullOrWhiteSpace(printer)) throw new InvalidOperationException("حدد طابعة الفاتورة من الإعدادات أولاً.");

        // Print first. The order is not marked OutForDelivery until both documents print successfully.
        fresh.CourierId = courier.Id; fresh.CourierName = courier.Name.Trim(); fresh.CourierPhone = courier.Phone?.Trim();
        await App.Services.Receipts.PrintDeliveryOrderAsync(fresh, printer);
        var manifestOrders = await App.Services.Restaurant.GetCourierOutstandingAsync(courier.Id);
        manifestOrders.RemoveAll(x => x.Id == fresh.Id);
        manifestOrders.Add(fresh);
        await App.Services.Receipts.PrintCourierManifestAsync(courier, manifestOrders, printer);

        await App.Services.Restaurant.AssignCourierAsync(order.Id, courier);
        await PageHelpers.MessageAsync(XamlRoot, "تم تحميل الطلب", $"تمت طباعة الطلب وكشف التحميل ثم تحميل الطلب #{order.Id} على {courier.Name} بنجاح.");
    }

    private async Task PrintDeliveryOrderAsync(RestaurantOrder order)'''
s,n=re.subn(pat,new,s,flags=re.S)
if n!=1: raise SystemExit(f'Assign replace count {n}')

# Replace SettleCourierAsync through DispatchDelivery_Click
pat=r'''    private async Task SettleCourierAsync\(RestaurantOrder seedOrder\)
    \{.*?
    \}

    private async void DispatchDelivery_Click'''
new='''    private async Task SettleCourierAsync(RestaurantOrder seedOrder)
    {
        if (string.IsNullOrWhiteSpace(seedOrder.CourierId)) return;
        var outstanding = await App.Services.Restaurant.GetCourierOutstandingAsync(seedOrder.CourierId);
        if (outstanding.Count == 0) { await PageHelpers.MessageAsync(XamlRoot, "التسوية", "لا توجد طلبات معلقة على هذا الطيار."); return; }

        var checks = new List<(RestaurantOrder Order, CheckBox Box)>();
        var listPanel = new StackPanel { Spacing = 6, FlowDirection = FlowDirection.RightToLeft };
        foreach (var o in outstanding)
        {
            var total = o.Items.Sum(x => x.Quantity * x.UnitPrice) + o.DeliveryFee;
            var box = new CheckBox
            {
                Content = $"طلب #{o.Id} • {o.CustomerName ?? o.CustomerPhone ?? "عميل"} • {total:0.00} جنيه",
                IsChecked = o.Id == seedOrder.Id, FlowDirection = FlowDirection.RightToLeft, HorizontalAlignment = HorizontalAlignment.Stretch
            };
            checks.Add((o, box)); listPanel.Children.Add(box);
        }

        var summary = new TextBlock { TextWrapping = TextWrapping.Wrap, FontWeight = Microsoft.UI.Text.FontWeights.SemiBold };
        var actual = new NumberBox { Header = "الكاش المستلم عن الطلبات المحددة", Minimum = 0, SpinButtonPlacementMode = NumberBoxSpinButtonPlacementMode.Hidden };
        decimal SelectedExpected() => checks.Where(x => x.Box.IsChecked == true).Sum(x => x.Order.Items.Sum(i => i.Quantity * i.UnitPrice) + x.Order.DeliveryFee);
        void RefreshSettlement()
        {
            var selectedCount = checks.Count(x => x.Box.IsChecked == true);
            var expected = SelectedExpected();
            summary.Text = $"الطيار: {seedOrder.CourierName} • المحدد: {selectedCount} من {outstanding.Count} • المطلوب: {expected:0.00} جنيه";
            actual.Value = (double)expected;
        }
        foreach (var row in checks) { row.Box.Checked += (_, _) => RefreshSettlement(); row.Box.Unchecked += (_, _) => RefreshSettlement(); }
        RefreshSettlement();

        var scroll = new ScrollViewer { MaxHeight = 280, Content = listPanel };
        var panel = new StackPanel { Width = 520, Spacing = 10, FlowDirection = FlowDirection.RightToLeft };
        panel.Children.Add(new TextBlock { Text = "اختر فقط الطلبات التي تم تسليمها ورجع الطيار بقيمتها. الطلبات غير المحددة تظل مفتوحة على الطيار.", TextWrapping = TextWrapping.Wrap, Foreground = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["MutedTextBrush"] });
        panel.Children.Add(scroll); panel.Children.Add(summary); panel.Children.Add(actual);
        var dlg = new ContentDialog { XamlRoot = XamlRoot, RequestedTheme = ElementTheme.Dark, Title = "تسوية الطيار", Content = panel, PrimaryButtonText = "استلام الكاش وإغلاق المحدد", CloseButtonText = "إلغاء", FlowDirection = FlowDirection.RightToLeft };
        if (await dlg.ShowAsync() != ContentDialogResult.Primary) return;

        var selected = checks.Where(x => x.Box.IsChecked == true).Select(x => x.Order).ToList();
        if (selected.Count == 0) { await PageHelpers.MessageAsync(XamlRoot, "التسوية", "حدد طلبًا واحدًا على الأقل للتسوية."); return; }
        var expectedFinal = selected.Sum(o => o.Items.Sum(x => x.Quantity * x.UnitPrice) + o.DeliveryFee);
        var received = (decimal)(double.IsNaN(actual.Value) ? 0 : actual.Value);
        if (Math.Round(received, 2) != Math.Round(expectedFinal, 2))
        {
            await PageHelpers.MessageAsync(XamlRoot, "فرق في التسوية", $"المبلغ المستلم {received:0.00} لا يساوي المطلوب للطلبات المحددة {expectedFinal:0.00}. راجع الطلبات قبل الإغلاق.");
            return;
        }

        foreach (var o in selected) await CompleteDeliveryOrderAsync(o);
        await PageHelpers.MessageAsync(XamlRoot, "تمت التسوية", $"تم استلام {received:0.00} جنيه وإغلاق {selected.Count} طلب. الطلبات الأخرى ما زالت مفتوحة على {seedOrder.CourierName}.");
        await ReloadProductsAsync();
    }

    private async Task CompleteDeliveryOrderAsync(RestaurantOrder order)
    {
        var cart = await App.Services.Restaurant.GetCartAsync(order.Id);
        var total = cart.Sum(x => x.Total) + order.DeliveryFee;
        var context = new RestaurantSaleContext
        {
            OrderType = RestaurantOrderType.Delivery, RestaurantOrderId = order.Id, DeliveryFee = order.DeliveryFee,
            CustomerName = order.CustomerName, CustomerPhone = order.CustomerPhone, DeliveryZoneName = order.DeliveryZoneName, DeliveryAddress = order.DeliveryAddress
        };
        var sale = await App.Services.Sales.CompleteSaleAsync(cart, new[] { new PaymentInput(PaymentMethod.Cash, total) }, 0, null, false, total, 0, context);
        await App.Services.Restaurant.MarkPaidAsync(order.Id, sale.Id);
        await App.Services.Receipts.PrintSaleAsync(sale);
    }

    private async Task ReturnDeliveryAsync(RestaurantOrder order)
    {
        var reason = new TextBox
        {
            Header = "سبب عدم التسليم / المرتجع", PlaceholderText = "مثال: العميل رفض الطلب / لا يرد / عنوان غير صحيح",
            AcceptsReturn = true, TextWrapping = TextWrapping.Wrap, MinHeight = 90, FlowDirection = FlowDirection.RightToLeft, TextAlignment = TextAlignment.Right
        };
        var dlg = new ContentDialog
        {
            XamlRoot = XamlRoot, RequestedTheme = ElementTheme.Dark, Title = $"مرتجع طلب #{order.Id}", Content = reason,
            PrimaryButtonText = "تسجيل كمرتجع", CloseButtonText = "إلغاء", DefaultButton = ContentDialogButton.Close, FlowDirection = FlowDirection.RightToLeft
        };
        if (await dlg.ShowAsync() != ContentDialogResult.Primary) return;
        if (string.IsNullOrWhiteSpace(reason.Text)) { await PageHelpers.MessageAsync(XamlRoot, "سبب المرتجع", "اكتب سبب عدم تسليم الطلب أولاً."); return; }
        await App.Services.Restaurant.MarkDeliveryReturnedAsync(order.Id, reason.Text);
        await PageHelpers.MessageAsync(XamlRoot, "تم تسجيل المرتجع", $"طلب #{order.Id} خرج من عهدة {order.CourierName} بدون تسجيل مبيعات أو كاش.");
    }

    private async void DispatchDelivery_Click'''
s,n=re.subn(pat,new,s,flags=re.S)
if n!=1: raise SystemExit(f'Settle replace count {n}')

# Show selector also hides dispatch button
s=s.replace('''        BackTablesButton.Visibility = Visibility.Collapsed; SendKitchenButton.Visibility = Visibility.Collapsed; CancelRestaurantOrderButton.Visibility = Visibility.Collapsed; OrderContextText.Text = "اختر الصالة والترابيزة";''','''        BackTablesButton.Visibility = Visibility.Collapsed; SendKitchenButton.Visibility = Visibility.Collapsed; DispatchDeliveryButton.Visibility = Visibility.Collapsed; CancelRestaurantOrderButton.Visibility = Visibility.Collapsed; OrderContextText.Text = "اختر الصالة والترابيزة";''')
p.write_text(s,encoding='utf-8-sig')

# Receipt minor Arabic context in sale receipt, if exact pattern exists
p=root/'Services/ReceiptService.cs'; s=p.read_text(encoding='utf-8-sig')
s=s.replace(' + $" • Table {sale.DiningTableNumber}"', ' + $" • ترابيزة {sale.DiningTableNumber}"')
p.write_text(s,encoding='utf-8-sig')

print('R3 source modifications applied')
