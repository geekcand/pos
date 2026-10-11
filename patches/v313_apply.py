from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source')

def replace(path, old, new, count=-1):
    p = root / path
    s = p.read_text(encoding='utf-8')
    if old not in s:
        raise RuntimeError(f'Missing expected block in {path}: {old[:120]!r}')
    p.write_text(s.replace(old, new, count), encoding='utf-8')

# Version
replace('GeekPOS.csproj','<Version>3.1.2</Version>','<Version>3.1.3</Version>')
replace('GeekPOS.csproj','<AssemblyVersion>3.1.2.0</AssemblyVersion>','<AssemblyVersion>3.1.3.0</AssemblyVersion>')
replace('GeekPOS.csproj','<FileVersion>3.1.2.0</FileVersion>','<FileVersion>3.1.3.0</FileVersion>')
replace('installer.iss','#define MyAppVersion "3.1.2"','#define MyAppVersion "3.1.3"')
replace('installer.iss','GeekPOS-Setup-x64-v3.1.2','GeekPOS-Setup-x64-v3.1.3')
replace('build.ps1','GeekPOS-Setup-x64-v3.1.1.exe','GeekPOS-Setup-x64-v3.1.3.exe')

# Excel report: exact title + deterministic RTL currency order in table and total row.
replace('Services/ExcelReportService.cs',
        'ws.Cell("A3").Value = "تقرير المبيعات — نموذج تصدير إلى Excel";',
        'ws.Cell("A3").Value = "تقرير المبيعات";')
replace('Services/ExcelReportService.cs', '''            ws.Cell(row, 7).Value = sale.Subtotal;
            ws.Cell(row, 8).Value = sale.DiningServiceAmount;
            ws.Cell(row, 9).Value = sale.TaxAmount;
            ws.Cell(row, 10).Value = sale.DiscountAmount;
            ws.Cell(row, 11).Value = sale.Total;''', '''            SetMoneyText(ws.Cell(row, 7), sale.Subtotal);
            SetMoneyText(ws.Cell(row, 8), sale.DiningServiceAmount);
            SetMoneyText(ws.Cell(row, 9), sale.TaxAmount);
            SetMoneyText(ws.Cell(row, 10), sale.DiscountAmount);
            SetMoneyText(ws.Cell(row, 11), sale.Total);''')
replace('Services/ExcelReportService.cs', '''        var firstData = 10;
        var lastData = Math.Max(firstData, row - 1);
        if (report.Sales.Count > 0)
        {
            for (var dataRow = firstData; dataRow <= lastData; dataRow++)
            {
                ApplyMoneyFormat(ws.Cell(dataRow, 7), report.Sales[dataRow - firstData].Subtotal);
                ApplyMoneyFormat(ws.Cell(dataRow, 8), report.Sales[dataRow - firstData].DiningServiceAmount);
                ApplyMoneyFormat(ws.Cell(dataRow, 9), report.Sales[dataRow - firstData].TaxAmount);
                ApplyMoneyFormat(ws.Cell(dataRow, 10), report.Sales[dataRow - firstData].DiscountAmount);
                ApplyMoneyFormat(ws.Cell(dataRow, 11), report.Sales[dataRow - firstData].Total);
            }
        }

        var totalRow = row + (report.Sales.Count == 0 ? 0 : 0);''', '''        var firstData = 10;
        var lastData = Math.Max(firstData, row - 1);
        var totalRow = row;''')
replace('Services/ExcelReportService.cs', '''        if (report.Sales.Count > 0)
        {
            for (var col = 7; col <= 11; col++)
                ws.Cell(totalRow, col).FormulaA1 = $"SUM({ws.Cell(firstData, col).Address}:{ws.Cell(lastData, col).Address})";
        }
        else
        {
            for (var col = 7; col <= 11; col++) ws.Cell(totalRow, col).Value = 0m;
        }''', '''        var totalValues = new[]
        {
            report.Sales.Sum(x => x.Subtotal),
            report.Sales.Sum(x => x.DiningServiceAmount),
            report.Sales.Sum(x => x.TaxAmount),
            report.Sales.Sum(x => x.DiscountAmount),
            report.Sales.Sum(x => x.Total)
        };
        for (var col = 7; col <= 11; col++) SetMoneyText(ws.Cell(totalRow, col), totalValues[col - 7]);''')
replace('Services/ExcelReportService.cs', '''        var totalValues = new[]
        {
            report.Sales.Sum(x => x.Subtotal),
            report.Sales.Sum(x => x.DiningServiceAmount),
            report.Sales.Sum(x => x.TaxAmount),
            report.Sales.Sum(x => x.DiscountAmount),
            report.Sales.Sum(x => x.Total)
        };
        for (var col = 7; col <= 11; col++) ApplyMoneyFormat(ws.Cell(totalRow, col), totalValues[col - 7]);
        ws.Row(totalRow).Height = 22;''', '''        ws.Row(totalRow).Height = 22;''')
replace('Services/ExcelReportService.cs', '''    private static void ApplyMoneyFormat(IXLCell cell, decimal value)
    {
        cell.Style.NumberFormat.Format = decimal.Truncate(value) == value
            ? "#,##0 \\"ج.م\\""
            : "#,##0.00 \\"ج.م\\"";
    }''', '''    private static void SetMoneyText(IXLCell cell, decimal value)
    {
        // Match the KPI display exactly so RTL Excel keeps the amount before the currency.
        cell.Value = MoneyDisplay.WithCurrency(value, group: true);
        cell.Style.NumberFormat.Format = "@";
    }''')

# Reports layout: second row was referenced without RowDefinitions, causing overlap.
replace('Pages/ReportsPage.xaml', '''                    <Grid ColumnSpacing="10" RowSpacing="10"><Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions>
                        <ComboBox x:Name="CategoryPicker" Header="القسم" DisplayMemberPath="Label" SelectionChanged="CategoryPicker_SelectionChanged" HorizontalAlignment="Stretch"/><ComboBox Grid.Column="1" x:Name="ProductPicker" Header="الصنف" DisplayMemberPath="Label" HorizontalAlignment="Stretch"/><ComboBox Grid.Column="2" x:Name="StatusPicker" Header="حالة الفاتورة" DisplayMemberPath="Label" HorizontalAlignment="Stretch"/><TextBox Grid.Column="3" x:Name="InvoiceFilter" Header="رقم الفاتورة" PlaceholderText="كل الفواتير"/>
                        <TextBox Grid.Row="1" Grid.ColumnSpan="4" x:Name="CustomerFilter" Header="العميل / الموبايل" PlaceholderText="اكتب اسم العميل أو رقم الموبايل — اختياري"/>
                    </Grid>''', '''                    <Grid ColumnSpacing="10" RowSpacing="10">
                        <Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions>
                        <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
                        <ComboBox x:Name="CategoryPicker" Header="القسم" DisplayMemberPath="Label" SelectionChanged="CategoryPicker_SelectionChanged" HorizontalAlignment="Stretch"/>
                        <ComboBox Grid.Column="1" x:Name="ProductPicker" Header="الصنف" DisplayMemberPath="Label" HorizontalAlignment="Stretch"/>
                        <ComboBox Grid.Column="2" x:Name="StatusPicker" Header="حالة الفاتورة" DisplayMemberPath="Label" HorizontalAlignment="Stretch"/>
                        <TextBox Grid.Column="3" x:Name="InvoiceFilter" Header="رقم الفاتورة" PlaceholderText="كل الفواتير"/>
                        <TextBox Grid.Row="1" Grid.Column="0" Grid.ColumnSpan="4" x:Name="CustomerFilter" Header="العميل / الموبايل" PlaceholderText="اكتب اسم العميل أو رقم الموبايل — اختياري" HorizontalAlignment="Stretch"/>
                    </Grid>''')

# POS cart: keep compact layout and add "العدد" exactly above the quantity editor.
replace('Pages/PosPage.xaml', '''                                    <Grid RowSpacing="4" FlowDirection="RightToLeft" HorizontalAlignment="Stretch">
                                        <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
                                        <Grid FlowDirection="RightToLeft" ColumnSpacing="7" HorizontalAlignment="Stretch">
                                            <Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>
                                            <StackPanel Grid.Column="0" Spacing="1" FlowDirection="RightToLeft" HorizontalAlignment="Stretch">
                                                <TextBlock Text="{Binding Name}" FontWeight="SemiBold" Foreground="{StaticResource LightTextBrush}" TextWrapping="Wrap" TextAlignment="Right" HorizontalAlignment="Stretch" FlowDirection="RightToLeft"/>
                                                <TextBlock Text="{Binding Notes}" FontSize="10.5" Foreground="{StaticResource AccentBrushSoft}" TextWrapping="Wrap" TextAlignment="Right" HorizontalAlignment="Stretch" FlowDirection="RightToLeft"/>
                                            </StackPanel>
                                            <TextBlock Grid.Column="1" Text="{Binding Total}" VerticalAlignment="Top" Foreground="{StaticResource AccentBrushSoft}" FontWeight="Bold" FlowDirection="LeftToRight" TextAlignment="Left" MinWidth="58"/>
                                        </Grid>
                                        <Grid Grid.Row="1" FlowDirection="RightToLeft" ColumnSpacing="5" HorizontalAlignment="Stretch">
                                            <Grid.ColumnDefinitions><ColumnDefinition Width="68"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
                                            <TextBox Grid.Column="0" Text="{Binding Quantity, Mode=OneTime}" Tag="{Binding ProductId}" Loaded="QuantityBox_Loaded" KeyDown="QuantityBox_KeyDown" LostFocus="QuantityBox_LostFocus" MaxLength="10" Width="68" MinHeight="32" HorizontalAlignment="Right" VerticalAlignment="Center" HorizontalContentAlignment="Center" TextAlignment="Center" FlowDirection="LeftToRight" InputScope="Number" ToolTipService.ToolTip="اكتب الكمية واضغط Enter"/>
                                            <StackPanel Grid.Column="1" Orientation="Horizontal" Spacing="3" FlowDirection="RightToLeft" HorizontalAlignment="Right">
                                                <Button Content="ملاحظة" Tag="{Binding ProductId}" Click="ItemNote_Click" Style="{StaticResource SoftButtonStyle}" Padding="7,3" MinHeight="32"/>
                                                <Button Content="−" Tag="{Binding ProductId}" Click="Minus_Click" Style="{StaticResource SoftButtonStyle}" Padding="7,3" MinHeight="32"/>
                                                <Button Content="+" Tag="{Binding ProductId}" Click="Plus_Click" Style="{StaticResource SoftButtonStyle}" Padding="7,3" MinHeight="32"/>
                                                <Button Content="×" Tag="{Binding ProductId}" Click="Remove_Click" Style="{StaticResource DangerButtonStyle}" Padding="7,3" MinHeight="32"/>
                                            </StackPanel>
                                        </Grid>
                                    </Grid>''', '''                                    <Grid RowSpacing="4" ColumnSpacing="7" FlowDirection="RightToLeft" HorizontalAlignment="Stretch">
                                        <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/></Grid.RowDefinitions>
                                        <Grid.ColumnDefinitions><ColumnDefinition Width="68"/><ColumnDefinition Width="*"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>
                                        <TextBlock Grid.Row="0" Grid.Column="0" Text="العدد" FontSize="11" Foreground="{StaticResource MutedTextBrush}" TextAlignment="Center" HorizontalAlignment="Stretch" VerticalAlignment="Top"/>
                                        <StackPanel Grid.Row="0" Grid.Column="1" Spacing="1" FlowDirection="RightToLeft" HorizontalAlignment="Stretch">
                                            <TextBlock Text="{Binding Name}" FontWeight="SemiBold" Foreground="{StaticResource LightTextBrush}" TextWrapping="Wrap" TextAlignment="Right" HorizontalAlignment="Stretch" FlowDirection="RightToLeft"/>
                                            <TextBlock Text="{Binding Notes}" FontSize="10.5" Foreground="{StaticResource AccentBrushSoft}" TextWrapping="Wrap" TextAlignment="Right" HorizontalAlignment="Stretch" FlowDirection="RightToLeft"/>
                                        </StackPanel>
                                        <TextBlock Grid.Row="0" Grid.Column="2" Text="{Binding Total}" VerticalAlignment="Top" Foreground="{StaticResource AccentBrushSoft}" FontWeight="Bold" FlowDirection="LeftToRight" TextAlignment="Left" MinWidth="58"/>
                                        <TextBox Grid.Row="1" Grid.Column="0" Text="{Binding Quantity, Mode=OneTime}" Tag="{Binding ProductId}" Loaded="QuantityBox_Loaded" KeyDown="QuantityBox_KeyDown" LostFocus="QuantityBox_LostFocus" MaxLength="10" Width="68" MinHeight="32" HorizontalAlignment="Right" VerticalAlignment="Center" HorizontalContentAlignment="Center" TextAlignment="Center" FlowDirection="LeftToRight" InputScope="Number" ToolTipService.ToolTip="اكتب الكمية واضغط Enter"/>
                                        <StackPanel Grid.Row="1" Grid.Column="1" Grid.ColumnSpan="2" Orientation="Horizontal" Spacing="3" FlowDirection="RightToLeft" HorizontalAlignment="Right">
                                            <Button Content="ملاحظة" Tag="{Binding ProductId}" Click="ItemNote_Click" Style="{StaticResource SoftButtonStyle}" Padding="7,3" MinHeight="32"/>
                                            <Button Content="−" Tag="{Binding ProductId}" Click="Minus_Click" Style="{StaticResource SoftButtonStyle}" Padding="7,3" MinHeight="32"/>
                                            <Button Content="+" Tag="{Binding ProductId}" Click="Plus_Click" Style="{StaticResource SoftButtonStyle}" Padding="7,3" MinHeight="32"/>
                                            <Button Content="×" Tag="{Binding ProductId}" Click="Remove_Click" Style="{StaticResource DangerButtonStyle}" Padding="7,3" MinHeight="32"/>
                                        </StackPanel>
                                    </Grid>''')

# Receipt layout: exact approved metadata pairs, headers, totals, currency order, footer, and branding.
replace('Services/ReceiptService.cs',
        'var estimated = 560 + sale.Items.Count * 42 + (showLogo ? 115 : 0) + (showBarcode ? 175 : 0);',
        'var estimated = 610 + sale.Items.Count * 42 + (showLogo ? 125 : 0) + (showBarcode ? 185 : 0);')
replace('Services/ReceiptService.cs', '''        var invoiceText = $"فاتورة #{sale.DisplayInvoiceNumber}";
        var dateText = $"{sale.CreatedAt:dd/MM HH:mm}";
        DrawReceiptPair(g, invoiceText, dateText, labelFont, black, y, width, margin); y += 24;

        var locationText = sale.OrderType == RestaurantOrderType.DineIn
            ? $"{sale.DiningAreaName ?? ""}{(sale.DiningTableNumber is int table ? $" / {table}" : "")}".Trim()
            : "";
        DrawReceiptPair(g, $"النوع: {orderType}", locationText, labelFont, black, y, width, margin); y += 24;
        DrawReceiptPair(g, $"الكاشير: {sale.User?.DisplayName ?? App.Services.Session.CurrentUser?.DisplayName ?? "-"}", "", labelFont, black, y, width, margin); y += 25;''', '''        var invoiceText = $"فاتورة #{sale.DisplayInvoiceNumber}";
        var typeText = sale.OrderType == RestaurantOrderType.DineIn && sale.DiningTableNumber is int table
            ? $"النوع: {orderType} - {(string.IsNullOrWhiteSpace(sale.DiningAreaName) ? "" : sale.DiningAreaName + " / ")}طاولة {table}"
            : $"النوع: {orderType}";
        var periodText = sale.CreatedAt.Hour < 12 ? "صباحاً" : "مساءً";
        var dateText = $"{sale.CreatedAt:dd/MM/yyyy} - {sale.CreatedAt:h:mm} {periodText}";
        var cashierText = $"الكاشير: {sale.User?.DisplayName ?? App.Services.Session.CurrentUser?.DisplayName ?? "-"}";
        DrawReceiptPair(g, invoiceText, typeText, labelFont, black, y, width, margin); y += 24;
        DrawReceiptPair(g, dateText, cashierText, labelFont, black, y, width, margin); y += 25;''')
replace('Services/ReceiptService.cs','DrawCell(g, "كمية", tableBold, black, new RectangleF(qtyX, y, qtyW, 25), false);','DrawCell(g, "الكمية", tableBold, black, new RectangleF(qtyX, y, qtyW, 25), false);')
replace('Services/ReceiptService.cs','g.DrawLine(dashPen, margin, y, width - margin, y); y += 3;\n\n        foreach (var item in sale.Items)','g.DrawLine(Pens.Black, margin, y, width - margin, y); y += 3;\n\n        foreach (var item in sale.Items)',1)
replace('Services/ReceiptService.cs','DrawReferenceTotalRow(g, paymentName, paidAmount, labelFont, black, ref y, width, margin);','DrawReferenceTotalRow(g, paymentName, -paidAmount, labelFont, black, ref y, width, margin);')
replace('Services/ReceiptService.cs','var footer = all.GetValueOrDefault("ReceiptFooter", "شكراً لزيارتكم - نتشرف بخدمتكم");','var footer = all.GetValueOrDefault("ReceiptFooter", "شكراً لزيارتكم");')
replace('Services/ReceiptService.cs', '''        if (showBarcode && !string.IsNullOrWhiteSpace(barcodePath) && File.Exists(barcodePath))
        {
            try
            {
                using var img = System.Drawing.Image.FromFile(barcodePath);
                var maxW = Math.Clamp((int)await settings.GetDecimalAsync("ReceiptBarcodeWidthDots", 150), 100, 220);
                var scale = Math.Min(maxW / (float)img.Width, 155f / img.Height);
                var w = Math.Max(1, (int)(img.Width * scale));
                var h = Math.Max(1, (int)(img.Height * scale));
                g.DrawImage(img, new Rectangle((width - w) / 2, (int)y, w, h));
                y += h + 7;
            }
            catch { }
        }

        y += 12;''', '''        if (showBarcode && !string.IsNullOrWhiteSpace(barcodePath) && File.Exists(barcodePath))
        {
            try
            {
                using var img = System.Drawing.Image.FromFile(barcodePath);
                var maxW = Math.Clamp((int)await settings.GetDecimalAsync("ReceiptBarcodeWidthDots", 150), 100, 220);
                var scale = Math.Min(maxW / (float)img.Width, 155f / img.Height);
                var w = Math.Max(1, (int)(img.Width * scale));
                var h = Math.Max(1, (int)(img.Height * scale));
                g.DrawImage(img, new Rectangle((width - w) / 2, (int)y, w, h));
                y += h + 7;
            }
            catch { }
        }

        DrawCentered(g, "Powered by Geek POS", small, black, y, width); y += 24;
        y += 8;''')
replace('Services/ReceiptService.cs', '''            var amountText = MoneyDisplay.Number(amount);
            g.DrawString(amountText, font, brush, new PointF(valueRect.X + 30, y + 1));
            g.DrawString("ج.م", font, brush, new PointF(valueRect.X, y + 1));''', '''            var amountText = MoneyDisplay.Number(amount);
            var numberX = valueRect.X;
            g.DrawString(amountText, font, brush, new PointF(numberX, y + 1));
            var numberWidth = g.MeasureString(amountText, font).Width;
            g.DrawString("ج.م", font, brush, new PointF(numberX + numberWidth + 5, y + 1));''')

print('v3.1.3 changes applied to', root)
