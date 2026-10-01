param([Parameter(Mandatory=$true)][string]$SourceRoot)
$ErrorActionPreference = 'Stop'

function Replace-Exact([string]$Path, [string]$Old, [string]$New) {
    $full = Join-Path $SourceRoot $Path
    if (!(Test-Path -LiteralPath $full)) { throw "Missing file: $full" }
    $text = (Get-Content -LiteralPath $full -Raw) -replace "`r`n", "`n"
    $oldNorm = $Old -replace "`r`n", "`n"
    $newNorm = $New -replace "`r`n", "`n"
    if (!$text.Contains($oldNorm)) { throw "Expected block not found in $Path`n--- expected ---`n$oldNorm" }
    $text = $text.Replace($oldNorm, $newNorm)
    Set-Content -LiteralPath $full -Value $text -Encoding utf8 -NoNewline
}

# Cart: give product name more room, keep multi-digit input, and hide the in-field clear X.
Replace-Exact 'Pages\PosPage.xaml' @'
                                    <Grid ColumnSpacing="8" FlowDirection="RightToLeft"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="68"/><ColumnDefinition Width="112"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>
'@ @'
                                    <Grid ColumnSpacing="8" FlowDirection="RightToLeft"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="68"/><ColumnDefinition Width="88"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>
'@

Replace-Exact 'Pages\PosPage.xaml' @'
                                        <TextBox Grid.Column="2" Text="{Binding Quantity, Mode=OneTime}" Tag="{Binding ProductId}" KeyDown="QuantityBox_KeyDown" LostFocus="QuantityBox_LostFocus" MaxLength="10" MinWidth="112" HorizontalAlignment="Stretch" VerticalAlignment="Center" HorizontalContentAlignment="Stretch" TextAlignment="Center" FlowDirection="LeftToRight" InputScope="Number" ToolTipService.ToolTip="اكتب الكمية واضغط Enter"/>
'@ @'
                                        <TextBox Grid.Column="2" Text="{Binding Quantity, Mode=OneTime}" Tag="{Binding ProductId}" Loaded="QuantityBox_Loaded" KeyDown="QuantityBox_KeyDown" LostFocus="QuantityBox_LostFocus" MaxLength="10" MinWidth="88" HorizontalAlignment="Stretch" VerticalAlignment="Center" HorizontalContentAlignment="Stretch" TextAlignment="Center" FlowDirection="LeftToRight" InputScope="Number" ToolTipService.ToolTip="اكتب الكمية واضغط Enter"/>
'@

# Weight dialog: product name and weight label must be physically right aligned.
Replace-Exact 'Pages\PosPage.xaml.cs' @'
            var weightLabel = new TextBlock
            {
                Text = isKg ? "الوزن (كجم)" : "الوزن (جرام)",
                FlowDirection = FlowDirection.RightToLeft,
                TextAlignment = TextAlignment.Right,
                HorizontalAlignment = HorizontalAlignment.Stretch,
                Foreground = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["MutedTextBrush"]
            };
'@ @'
            var weightLabel = new TextBlock
            {
                Text = isKg ? "الوزن (كجم)" : "الوزن (جرام)",
                Width = 390,
                FlowDirection = FlowDirection.RightToLeft,
                TextAlignment = TextAlignment.Right,
                HorizontalAlignment = HorizontalAlignment.Stretch,
                Foreground = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["MutedTextBrush"]
            };
'@

Replace-Exact 'Pages\PosPage.xaml.cs' @'
            var panel = new StackPanel { Width = 390, Spacing = 10, FlowDirection = FlowDirection.LeftToRight, HorizontalAlignment = HorizontalAlignment.Stretch };
            panel.Children.Add(new TextBlock { Text = string.IsNullOrWhiteSpace(product.ArabicName) ? product.Name : product.ArabicName, FontSize = 20, FontWeight = Microsoft.UI.Text.FontWeights.Bold, TextAlignment = TextAlignment.Right, HorizontalAlignment = HorizontalAlignment.Stretch, FlowDirection = FlowDirection.RightToLeft });
'@ @'
            box.Loaded += (_, _) => HideTextBoxClearButton(box);
            var panel = new StackPanel { Width = 390, Spacing = 10, FlowDirection = FlowDirection.RightToLeft, HorizontalAlignment = HorizontalAlignment.Stretch };
            panel.Children.Add(new TextBlock { Text = string.IsNullOrWhiteSpace(product.ArabicName) ? product.Name : product.ArabicName, Width = 390, FontSize = 20, FontWeight = Microsoft.UI.Text.FontWeights.Bold, TextAlignment = TextAlignment.Right, HorizontalAlignment = HorizontalAlignment.Stretch, FlowDirection = FlowDirection.RightToLeft });
'@

Replace-Exact 'Pages\PosPage.xaml.cs' @'
    private void QuantityBox_KeyDown(object sender, KeyRoutedEventArgs e)
'@ @'
    private static void HideTextBoxClearButton(DependencyObject root)
    {
        for (var i = 0; i < Microsoft.UI.Xaml.Media.VisualTreeHelper.GetChildrenCount(root); i++)
        {
            var child = Microsoft.UI.Xaml.Media.VisualTreeHelper.GetChild(root, i);
            if (child is Button button && (button.Name == "DeleteButton" || button.Name == "ClearButton"))
            {
                button.Visibility = Visibility.Collapsed;
                button.IsHitTestVisible = false;
                button.Width = 0;
                button.MinWidth = 0;
                button.Padding = new Thickness(0);
                button.Margin = new Thickness(0);
                button.Opacity = 0;
            }
            HideTextBoxClearButton(child);
        }
    }

    private void QuantityBox_Loaded(object sender, RoutedEventArgs e)
    {
        if (sender is TextBox box) HideTextBoxClearButton(box);
    }

    private void QuantityBox_KeyDown(object sender, KeyRoutedEventArgs e)
'@

# Shifts UI: admin-only delete button.
Replace-Exact 'Pages\ShiftsPage.xaml' @'
<Button x:Name="ReprintShiftButton" Content="إعادة طباعة الوردية" Click="ReprintShift_Click" Visibility="Collapsed" Style="{StaticResource SoftButtonStyle}"/><Button x:Name="RefreshButton"
'@ @'
<Button x:Name="ReprintShiftButton" Content="إعادة طباعة الوردية" Click="ReprintShift_Click" Visibility="Collapsed" Style="{StaticResource SoftButtonStyle}"/><Button x:Name="DeleteShiftButton" Content="حذف الوردية المحددة" Click="DeleteShift_Click" Visibility="Collapsed" Style="{StaticResource DangerButtonStyle}"/><Button x:Name="RefreshButton"
'@

Replace-Exact 'Pages\ShiftsPage.xaml.cs' @'
        ReprintShiftButton.Visibility = isAdmin ? Visibility.Visible : Visibility.Collapsed;
'@ @'
        ReprintShiftButton.Visibility = isAdmin ? Visibility.Visible : Visibility.Collapsed;
        DeleteShiftButton.Visibility = isAdmin ? Visibility.Visible : Visibility.Collapsed;
'@

Replace-Exact 'Pages\ShiftsPage.xaml.cs' @'
    private async void Refresh_Click(object sender, RoutedEventArgs e) => await RefreshAsync();
'@ @'
    private async void DeleteShift_Click(object sender, RoutedEventArgs e)
    {
        if (App.Services.Session.CurrentUser?.Role != SweetsPOS.Core.UserRole.Admin) return;
        if (ShiftsList.SelectedItem is not SweetsPOS.Core.Shift selected)
        {
            await PageHelpers.MessageAsync(XamlRoot, "اختر وردية", "اختر الوردية المطلوب حذفها من القائمة أولاً.");
            return;
        }

        var confirm = new ContentDialog
        {
            XamlRoot = XamlRoot, RequestedTheme = ElementTheme.Dark, FlowDirection = FlowDirection.RightToLeft,
            Title = $"حذف الوردية #{selected.Id}",
            Content = "سيتم حذف الوردية وإعادة ترتيب أرقام الورديات التالية تلقائياً. الحذف متاح فقط للوردية التي لا تحتوي على مبيعات أو مرتجعات أو مصروفات.",
            PrimaryButtonText = "حذف الوردية", CloseButtonText = "إلغاء", DefaultButton = ContentDialogButton.Close
        };
        if (await confirm.ShowAsync() != ContentDialogResult.Primary) return;

        try
        {
            await App.Services.Shifts.DeleteAndRenumberAsync(selected.Id);
            await PageHelpers.MessageAsync(XamlRoot, "تم حذف الوردية", "تم حذف الوردية وإعادة ترتيب أرقام الورديات المتبقية بدون فجوات.");
            await RefreshAsync();
        }
        catch (Exception ex)
        {
            await PageHelpers.MessageAsync(XamlRoot, "تعذر حذف الوردية", ex.Message);
        }
    }

    private async void Refresh_Click(object sender, RoutedEventArgs e) => await RefreshAsync();
'@

# Shift service: delete empty mistaken shift only, renumber remaining PKs and all FK references safely.
Replace-Exact 'Services\ShiftService.cs' @'
    public async Task<List<Shift>> GetRecentAsync(int take = 100)
'@ @'
    public async Task DeleteAndRenumberAsync(int shiftId)
    {
        var admin = session.CurrentUser ?? throw new InvalidOperationException("Login required.");
        if (admin.Role != UserRole.Admin) throw new UnauthorizedAccessException("حذف الورديات متاح للأدمن فقط.");

        await using var db = database.CreateContext();
        var shift = await db.Shifts.AsNoTracking().FirstOrDefaultAsync(x => x.Id == shiftId)
            ?? throw new InvalidOperationException("الوردية المحددة غير موجودة.");

        var salesCount = await db.Sales.CountAsync(x => x.ShiftId == shiftId);
        var refundsCount = await db.Refunds.CountAsync(x => x.ShiftId == shiftId);
        var expensesCount = await db.Expenses.CountAsync(x => x.ShiftId == shiftId);
        if (salesCount > 0 || refundsCount > 0 || expensesCount > 0)
            throw new InvalidOperationException("لا يمكن حذف وردية عليها مبيعات أو مرتجعات أو مصروفات. الحذف مخصص للوردية التي فُتحت بالخطأ ولم يُسجل عليها نشاط.");

        await db.Database.OpenConnectionAsync();
        await using var transaction = await db.Database.BeginTransactionAsync();
        try
        {
            await db.Database.ExecuteSqlRawAsync("PRAGMA defer_foreign_keys = ON;");
            await db.Database.ExecuteSqlInterpolatedAsync($"DELETE FROM Shifts WHERE Id = {shiftId};");

            await db.Database.ExecuteSqlInterpolatedAsync($"UPDATE Sales SET ShiftId = ShiftId - 1 WHERE ShiftId > {shiftId};");
            await db.Database.ExecuteSqlInterpolatedAsync($"UPDATE Refunds SET ShiftId = ShiftId - 1 WHERE ShiftId > {shiftId};");
            await db.Database.ExecuteSqlInterpolatedAsync($"UPDATE Expenses SET ShiftId = ShiftId - 1 WHERE ShiftId > {shiftId};");

            await db.Database.ExecuteSqlInterpolatedAsync($"UPDATE Shifts SET Id = -Id WHERE Id > {shiftId};");
            await db.Database.ExecuteSqlInterpolatedAsync($"UPDATE Shifts SET Id = (-Id) - 1 WHERE Id < -{shiftId};");

            await db.Database.ExecuteSqlInterpolatedAsync($@"UPDATE AuditLogs
SET EntityId = CAST(CAST(EntityId AS INTEGER) - 1 AS TEXT)
WHERE EntityType = 'Shift'
  AND EntityId GLOB '[0-9]*'
  AND CAST(EntityId AS INTEGER) > {shiftId};");

            await db.Database.ExecuteSqlRawAsync("UPDATE sqlite_sequence SET seq = COALESCE((SELECT MAX(Id) FROM Shifts), 0) WHERE name = 'Shifts';");
            await transaction.CommitAsync();
        }
        catch
        {
            await transaction.RollbackAsync();
            throw;
        }

        if (session.CurrentShift?.Id == shiftId) session.CurrentShift = null;
        else if (session.CurrentShift?.Id > shiftId) session.CurrentShift.Id--;

        await audit.WriteAsync("ShiftDeleted", "Shift", null, $"Deleted empty shift #{shiftId}; remaining shifts renumbered by admin {admin.DisplayName}.");
    }

    public async Task<List<Shift>> GetRecentAsync(int take = 100)
'@

# Version bump.
Replace-Exact 'SweetsPOS.csproj' '<Version>2.0.8</Version>' '<Version>2.0.9</Version>'
Replace-Exact 'SweetsPOS.csproj' '<AssemblyVersion>2.0.8.0</AssemblyVersion>' '<AssemblyVersion>2.0.9.0</AssemblyVersion>'
Replace-Exact 'SweetsPOS.csproj' '<FileVersion>2.0.8.0</FileVersion>' '<FileVersion>2.0.9.0</FileVersion>'
Replace-Exact 'installer.iss' '#define MyAppVersion "2.0.8"' '#define MyAppVersion "2.0.9"'
Replace-Exact 'installer.iss' 'OutputBaseFilename=GeekPOS-Setup-x64-v2.0.8' 'OutputBaseFilename=GeekPOS-Setup-x64-v2.0.9'

Write-Host 'Geek POS v2.0.9 cart, RTL and shift-delete fixes applied successfully.'
