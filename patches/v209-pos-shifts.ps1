param([Parameter(Mandatory=$true)][string]$SourceRoot)
$ErrorActionPreference = 'Stop'

function Replace-Exact([string]$Path, [string]$Old, [string]$New) {
    $full = Join-Path $SourceRoot $Path
    if (!(Test-Path -LiteralPath $full)) { throw "Missing file: $full" }
    $text = (Get-Content -LiteralPath $full -Raw) -replace "`r`n", "`n"
    $oldN = $Old -replace "`r`n", "`n"
    $newN = $New -replace "`r`n", "`n"
    if (!$text.Contains($oldN)) { throw "Expected block not found in $Path`n--- expected ---`n$oldN" }
    $text = $text.Replace($oldN, $newN)
    [System.IO.File]::WriteAllText($full, $text, [System.Text.UTF8Encoding]::new($false))
}

# POS cart quantity: reduce width, keep all digits visible, and remove the WinUI clear-X.
Replace-Exact 'Pages\PosPage.xaml' @'
<Grid ColumnSpacing="8" FlowDirection="RightToLeft"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="68"/><ColumnDefinition Width="112"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>
'@ @'
<Grid ColumnSpacing="8" FlowDirection="RightToLeft"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="68"/><ColumnDefinition Width="92"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>
'@

Replace-Exact 'Pages\PosPage.xaml' @'
<TextBox Grid.Column="2" Text="{Binding Quantity, Mode=OneTime}" Tag="{Binding ProductId}" KeyDown="QuantityBox_KeyDown" LostFocus="QuantityBox_LostFocus" MaxLength="10" MinWidth="112" HorizontalAlignment="Stretch" VerticalAlignment="Center" HorizontalContentAlignment="Stretch" TextAlignment="Center" FlowDirection="LeftToRight" InputScope="Number" ToolTipService.ToolTip="اكتب الكمية واضغط Enter"/>
'@ @'
<TextBox Grid.Column="2" Text="{Binding Quantity, Mode=OneTime}" Tag="{Binding ProductId}" KeyDown="QuantityBox_KeyDown" LostFocus="QuantityBox_LostFocus" MaxLength="10" MinWidth="92" HorizontalAlignment="Stretch" VerticalAlignment="Center" HorizontalContentAlignment="Stretch" TextAlignment="Center" FlowDirection="LeftToRight" InputScope="Number" TextWrapping="Wrap" ToolTipService.ToolTip="اكتب الكمية واضغط Enter"/>
'@

# Weight dialog: Arabic product name and weight label anchored to the right.
Replace-Exact 'Pages\PosPage.xaml.cs' @'
                TextAlignment = TextAlignment.Right,
                HorizontalAlignment = HorizontalAlignment.Stretch,
                Foreground = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["MutedTextBrush"]
'@ @'
                TextAlignment = TextAlignment.Right,
                HorizontalAlignment = HorizontalAlignment.Right,
                Foreground = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["MutedTextBrush"]
'@

Replace-Exact 'Pages\PosPage.xaml.cs' @'
            var panel = new StackPanel { Width = 390, Spacing = 10, FlowDirection = FlowDirection.LeftToRight, HorizontalAlignment = HorizontalAlignment.Stretch };
            panel.Children.Add(new TextBlock { Text = string.IsNullOrWhiteSpace(product.ArabicName) ? product.Name : product.ArabicName, FontSize = 20, FontWeight = Microsoft.UI.Text.FontWeights.Bold, TextAlignment = TextAlignment.Right, HorizontalAlignment = HorizontalAlignment.Stretch, FlowDirection = FlowDirection.RightToLeft });
'@ @'
            var panel = new StackPanel { Width = 390, Spacing = 10, FlowDirection = FlowDirection.RightToLeft, HorizontalAlignment = HorizontalAlignment.Stretch };
            panel.Children.Add(new TextBlock { Text = string.IsNullOrWhiteSpace(product.ArabicName) ? product.Name : product.ArabicName, FontSize = 20, FontWeight = Microsoft.UI.Text.FontWeights.Bold, TextAlignment = TextAlignment.Right, HorizontalAlignment = HorizontalAlignment.Right, FlowDirection = FlowDirection.RightToLeft });
'@

# Shift display numbering is independent from the database PK, so deleted empty shifts can be renumbered safely.
Replace-Exact 'Core\Entities.cs' @'
    public ShiftStatus Status { get; set; } = ShiftStatus.Open;
    [NotMapped] public string StatusLabel => Status == ShiftStatus.Open ? "مفتوحة" : "مغلقة";
'@ @'
    public ShiftStatus Status { get; set; } = ShiftStatus.Open;
    [NotMapped] public int DisplayNumber { get; set; }
    [NotMapped] public string StatusLabel => Status == ShiftStatus.Open ? "مفتوحة" : "مغلقة";
'@

Replace-Exact 'Services\ShiftService.cs' @'
        await db.SaveChangesAsync();
        session.CurrentShift = shift;
'@ @'
        await db.SaveChangesAsync();
        shift.DisplayNumber = await db.Shifts.CountAsync();
        session.CurrentShift = shift;
'@

Replace-Exact 'Services\ShiftService.cs' @'
    public async Task<List<Shift>> GetRecentAsync(int take = 100)
    {
        await using var db = database.CreateContext();
        return await db.Shifts.AsNoTracking().Include(x => x.User).OrderByDescending(x => x.OpenedAt).Take(take).ToListAsync();
    }
'@ @'
    public async Task<int> GetDisplayNumberAsync(int shiftId)
    {
        await using var db = database.CreateContext();
        var orderedIds = await db.Shifts.AsNoTracking().OrderBy(x => x.OpenedAt).ThenBy(x => x.Id).Select(x => x.Id).ToListAsync();
        var index = orderedIds.IndexOf(shiftId);
        return index >= 0 ? index + 1 : shiftId;
    }

    public async Task<List<Shift>> GetRecentAsync(int take = 100)
    {
        await using var db = database.CreateContext();
        var rows = await db.Shifts.AsNoTracking().Include(x => x.User).OrderBy(x => x.OpenedAt).ThenBy(x => x.Id).ToListAsync();
        for (var i = 0; i < rows.Count; i++) rows[i].DisplayNumber = i + 1;
        return rows.OrderByDescending(x => x.OpenedAt).ThenByDescending(x => x.Id).Take(take).ToList();
    }

    public async Task DeleteByAdminAsync(int shiftId)
    {
        var admin = session.CurrentUser ?? throw new InvalidOperationException("Login required.");
        if (admin.Role != UserRole.Admin) throw new UnauthorizedAccessException("حذف الورديات متاح للأدمن فقط.");

        await using var db = database.CreateContext();
        var row = await db.Shifts.FirstOrDefaultAsync(x => x.Id == shiftId)
            ?? throw new InvalidOperationException("الوردية غير موجودة.");

        var hasSales = await db.Sales.AnyAsync(x => x.ShiftId == shiftId);
        var hasRefunds = await db.Refunds.AnyAsync(x => x.ShiftId == shiftId);
        var hasExpenses = await db.Expenses.AnyAsync(x => x.ShiftId == shiftId);
        if (hasSales || hasRefunds || hasExpenses)
            throw new InvalidOperationException("لا يمكن حذف وردية تحتوي على مبيعات أو مرتجعات أو مصروفات. يمكن حذف الوردية المفتوحة بالخطأ فقط إذا كانت بدون معاملات.");

        var owner = row.UserId;
        var openedAt = row.OpenedAt;
        db.Shifts.Remove(row);
        await db.SaveChangesAsync();
        if (session.CurrentShift?.Id == shiftId) session.CurrentShift = null;
        await audit.WriteAsync("ShiftDeleted", "Shift", shiftId.ToString(), $"Admin deleted empty shift #{shiftId}; owner {owner}; opened {openedAt:O}");
    }
'@

# Shift management UI: admin-only delete button and contiguous displayed numbering.
Replace-Exact 'Pages\ShiftsPage.xaml' @'
<TextBlock Text="يمكن لكل مستخدم فتح ورديته بشكل مستقل. الأدمن يستطيع اختيار أي وردية مفتوحة من القائمة وإغلاقها." Foreground="{StaticResource MutedTextBrush}"/>
'@ @'
<TextBlock Text="يمكن لكل مستخدم فتح ورديته بشكل مستقل. الأدمن يستطيع إغلاق وردية مفتوحة أو حذف وردية فارغة تم فتحها بالخطأ." Foreground="{StaticResource MutedTextBrush}"/>
'@

Replace-Exact 'Pages\ShiftsPage.xaml' @'
<Button x:Name="AdminCloseButton" Content="إغلاق المحددة كأدمن" Click="AdminClose_Click" Visibility="Collapsed" Style="{StaticResource DangerButtonStyle}"/><Button x:Name="ShiftDetailsButton"
'@ @'
<Button x:Name="AdminCloseButton" Content="إغلاق المحددة كأدمن" Click="AdminClose_Click" Visibility="Collapsed" Style="{StaticResource DangerButtonStyle}"/><Button x:Name="AdminDeleteButton" Content="حذف الوردية المحددة" Click="AdminDelete_Click" Visibility="Collapsed" Style="{StaticResource DangerButtonStyle}"/><Button x:Name="ShiftDetailsButton"
'@

Replace-Exact 'Pages\ShiftsPage.xaml' '<TextBlock Text="{Binding Id}"/>' '<TextBlock Text="{Binding DisplayNumber}"/>'

Replace-Exact 'Pages\ShiftsPage.xaml.cs' @'
        AdminCloseButton.Visibility = isAdmin ? Visibility.Visible : Visibility.Collapsed;
        ReprintShiftButton.Visibility = isAdmin ? Visibility.Visible : Visibility.Collapsed;
'@ @'
        AdminCloseButton.Visibility = isAdmin ? Visibility.Visible : Visibility.Collapsed;
        AdminDeleteButton.Visibility = isAdmin ? Visibility.Visible : Visibility.Collapsed;
        ReprintShiftButton.Visibility = isAdmin ? Visibility.Visible : Visibility.Collapsed;
'@

Replace-Exact 'Pages\ShiftsPage.xaml.cs' @'
            var t = await App.Services.Shifts.GetTotalsAsync(shift.Id);
            CurrentTitle.Text = $"وردية #{shift.Id} • مفتوحة";
'@ @'
            var t = await App.Services.Shifts.GetTotalsAsync(shift.Id);
            var displayNumber = await App.Services.Shifts.GetDisplayNumberAsync(shift.Id);
            shift.DisplayNumber = displayNumber;
            CurrentTitle.Text = $"وردية #{displayNumber} • مفتوحة";
'@

Replace-Exact 'Pages\ShiftsPage.xaml.cs' @'
        var dialog = new ContentDialog { XamlRoot = XamlRoot, RequestedTheme = ElementTheme.Dark, Title = $"إغلاق الوردية #{shift.Id}", Content = panel, PrimaryButtonText = "إغلاق الوردية", CloseButtonText = "إلغاء" };
'@ @'
        var displayNumber = await App.Services.Shifts.GetDisplayNumberAsync(shift.Id);
        var dialog = new ContentDialog { XamlRoot = XamlRoot, RequestedTheme = ElementTheme.Dark, Title = $"إغلاق الوردية #{displayNumber}", Content = panel, PrimaryButtonText = "إغلاق الوردية", CloseButtonText = "إلغاء" };
'@

Replace-Exact 'Pages\ShiftsPage.xaml.cs' @'
            var closed = await App.Services.Shifts.CloseAsync(PageHelpers.DecimalFrom(actual), notes.Text);
'@ @'
            var closed = await App.Services.Shifts.CloseAsync(PageHelpers.DecimalFrom(actual), notes.Text);
            closed.DisplayNumber = displayNumber;
'@

Replace-Exact 'Pages\ShiftsPage.xaml.cs' 'Title = $"إغلاق الوردية كأدمن #{selected.Id}"' 'Title = $"إغلاق الوردية كأدمن #{selected.DisplayNumber}"'

Replace-Exact 'Pages\ShiftsPage.xaml.cs' @'
            var closed = await App.Services.Shifts.CloseByAdminAsync(selected.Id, PageHelpers.DecimalFrom(actual), notes.Text);
'@ @'
            var closed = await App.Services.Shifts.CloseByAdminAsync(selected.Id, PageHelpers.DecimalFrom(actual), notes.Text);
            closed.DisplayNumber = selected.DisplayNumber;
'@

Replace-Exact 'Pages\ShiftsPage.xaml.cs' @'

    private async void ShiftDetails_Click(object sender, RoutedEventArgs e)
'@ @'

    private async void AdminDelete_Click(object sender, RoutedEventArgs e)
    {
        if (App.Services.Session.CurrentUser?.Role != SweetsPOS.Core.UserRole.Admin) return;
        if (ShiftsList.SelectedItem is not SweetsPOS.Core.Shift selected)
        {
            await PageHelpers.MessageAsync(XamlRoot, "اختر وردية", "اختر الوردية التي تريد حذفها من القائمة أولاً.");
            return;
        }

        var confirm = new ContentDialog
        {
            XamlRoot = XamlRoot, RequestedTheme = ElementTheme.Dark, FlowDirection = FlowDirection.RightToLeft,
            Title = $"حذف الوردية #{selected.DisplayNumber}",
            Content = new TextBlock { Text = "سيتم حذف الوردية إذا كانت بدون مبيعات أو مرتجعات أو مصروفات، ثم يعاد ترقيم قائمة الورديات تلقائيًا. هل تريد المتابعة؟", TextWrapping = TextWrapping.Wrap },
            PrimaryButtonText = "حذف الوردية", CloseButtonText = "إلغاء", DefaultButton = ContentDialogButton.Close
        };
        if (await confirm.ShowAsync() != ContentDialogResult.Primary) return;

        try
        {
            await App.Services.Shifts.DeleteByAdminAsync(selected.Id);
            await PageHelpers.MessageAsync(XamlRoot, "تم حذف الوردية", "تم الحذف وإعادة ترتيب أرقام الورديات الموجودة.");
            await RefreshAsync();
        }
        catch (Exception ex) { await PageHelpers.MessageAsync(XamlRoot, "تعذر حذف الوردية", ex.Message); }
    }

    private async void ShiftDetails_Click(object sender, RoutedEventArgs e)
'@

Replace-Exact 'Pages\ShiftsPage.xaml.cs' '$"وردية #{selected.Id} • {status}\n" +' '$"وردية #{selected.DisplayNumber} • {status}\n" +'
Replace-Exact 'Pages\ShiftsPage.xaml.cs' 'await PageHelpers.MessageAsync(XamlRoot, $"تفاصيل الوردية #{selected.Id}", details);' 'await PageHelpers.MessageAsync(XamlRoot, $"تفاصيل الوردية #{selected.DisplayNumber}", details);'

Replace-Exact 'Services\ReceiptService.cs' '        sb.AppendLine($"رقم الوردية: #{shift.Id}");' '        sb.AppendLine($"رقم الوردية: #{(shift.DisplayNumber > 0 ? shift.DisplayNumber : shift.Id)}");'

# Version bump.
Replace-Exact 'SweetsPOS.csproj' '<Version>2.0.8</Version>' '<Version>2.0.9</Version>'
Replace-Exact 'SweetsPOS.csproj' '<AssemblyVersion>2.0.8.0</AssemblyVersion>' '<AssemblyVersion>2.0.9.0</AssemblyVersion>'
Replace-Exact 'SweetsPOS.csproj' '<FileVersion>2.0.8.0</FileVersion>' '<FileVersion>2.0.9.0</FileVersion>'
Replace-Exact 'installer.iss' '#define MyAppVersion "2.0.8"' '#define MyAppVersion "2.0.9"'
Replace-Exact 'installer.iss' 'OutputBaseFilename=GeekPOS-Setup-x64-v2.0.8' 'OutputBaseFilename=GeekPOS-Setup-x64-v2.0.9'

Write-Host 'Geek POS v2.0.9 POS alignment and admin shift deletion patch applied successfully.'
