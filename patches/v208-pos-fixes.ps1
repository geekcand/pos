param([Parameter(Mandatory=$true)][string]$SourceRoot)
$ErrorActionPreference = 'Stop'

function Replace-Exact([string]$Path, [string]$Old, [string]$New) {
    $full = Join-Path $SourceRoot $Path
    if (!(Test-Path -LiteralPath $full)) { throw "Missing file: $full" }
    $text = Get-Content -LiteralPath $full -Raw
    if (!$text.Contains($Old)) { throw "Expected block not found in $Path`n--- expected ---`n$Old" }
    $text = $text.Replace($Old, $New)
    Set-Content -LiteralPath $full -Value $text -Encoding utf8
}

# 1) Cart quantity textbox: the saved value was correct, but the narrow 72px editor
#    plus WinUI's in-field clear button visually hid leading digits while focused.
#    Widen the editor and make RTL layout explicit throughout the cart row.
Replace-Exact 'Pages\PosPage.xaml' @'
                    <ListView Grid.Row="1" x:Name="CartList" SelectionMode="None">
'@ @'
                    <ListView Grid.Row="1" x:Name="CartList" SelectionMode="None" FlowDirection="RightToLeft">
'@

Replace-Exact 'Pages\PosPage.xaml' @'
                                    <Grid ColumnSpacing="6"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="68"/><ColumnDefinition Width="72"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>
'@ @'
                                    <Grid ColumnSpacing="8" FlowDirection="RightToLeft"><Grid.ColumnDefinitions><ColumnDefinition Width="*"/><ColumnDefinition Width="68"/><ColumnDefinition Width="112"/><ColumnDefinition Width="Auto"/></Grid.ColumnDefinitions>
'@

Replace-Exact 'Pages\PosPage.xaml' @'
                                        <StackPanel><TextBlock Text="{Binding Name}" FontWeight="SemiBold" Foreground="{StaticResource LightTextBrush}" TextWrapping="Wrap"/><TextBlock Text="{Binding QuantityText}" FontSize="12" Foreground="{StaticResource MutedTextBrush}"/></StackPanel>
'@ @'
                                        <StackPanel FlowDirection="RightToLeft" HorizontalAlignment="Stretch"><TextBlock Text="{Binding Name}" FontWeight="SemiBold" Foreground="{StaticResource LightTextBrush}" TextWrapping="Wrap" TextAlignment="Right" HorizontalAlignment="Stretch"/><TextBlock Text="{Binding QuantityText}" FontSize="12" Foreground="{StaticResource MutedTextBrush}" TextAlignment="Right" HorizontalAlignment="Stretch"/></StackPanel>
'@

Replace-Exact 'Pages\PosPage.xaml' @'
                                        <TextBox Grid.Column="2" Text="{Binding Quantity, Mode=OneTime}" Tag="{Binding ProductId}" KeyDown="QuantityBox_KeyDown" LostFocus="QuantityBox_LostFocus" MaxLength="10" HorizontalAlignment="Stretch" VerticalAlignment="Center" HorizontalContentAlignment="Center" TextAlignment="Center" FlowDirection="LeftToRight" InputScope="Number" ToolTipService.ToolTip="اكتب الكمية واضغط Enter"/>
'@ @'
                                        <TextBox Grid.Column="2" Text="{Binding Quantity, Mode=OneTime}" Tag="{Binding ProductId}" KeyDown="QuantityBox_KeyDown" LostFocus="QuantityBox_LostFocus" MaxLength="10" MinWidth="112" HorizontalAlignment="Stretch" VerticalAlignment="Center" HorizontalContentAlignment="Stretch" TextAlignment="Center" FlowDirection="LeftToRight" InputScope="Number" ToolTipService.ToolTip="اكتب الكمية واضغط Enter"/>
'@

# 2) Weight dialog: keep numeric input LTR, but do not let that LTR direction control
#    the Arabic product name/header alignment. Use explicit RTL text elements and a
#    neutral LTR container, while quick presets keep their own RTL order.
Replace-Exact 'Pages\PosPage.xaml.cs' @'
            var box = new TextBox
            {
                Header = isKg ? "الوزن (كجم)" : "الوزن (جرام)",
                Text = isKg ? "0.5" : "500",
                FlowDirection = FlowDirection.LeftToRight,
                TextAlignment = TextAlignment.Right,
                HorizontalContentAlignment = HorizontalAlignment.Stretch,
                InputScope = new InputScope { Names = { new InputScopeName(InputScopeNameValue.Number) } }
            };
'@ @'
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
                FlowDirection = FlowDirection.RightToLeft,
                TextAlignment = TextAlignment.Right,
                HorizontalAlignment = HorizontalAlignment.Stretch,
                Foreground = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["MutedTextBrush"]
            };
'@

Replace-Exact 'Pages\PosPage.xaml.cs' @'
            var panel = new StackPanel { Width = 390, Spacing = 10, FlowDirection = FlowDirection.RightToLeft };
            panel.Children.Add(new TextBlock { Text = string.IsNullOrWhiteSpace(product.ArabicName) ? product.Name : product.ArabicName, FontSize = 20, FontWeight = Microsoft.UI.Text.FontWeights.Bold, TextAlignment = TextAlignment.Right, HorizontalAlignment = HorizontalAlignment.Stretch, FlowDirection = FlowDirection.RightToLeft });
            panel.Children.Add(box);
            panel.Children.Add(presets);
'@ @'
            var panel = new StackPanel { Width = 390, Spacing = 10, FlowDirection = FlowDirection.LeftToRight, HorizontalAlignment = HorizontalAlignment.Stretch };
            panel.Children.Add(new TextBlock { Text = string.IsNullOrWhiteSpace(product.ArabicName) ? product.Name : product.ArabicName, FontSize = 20, FontWeight = Microsoft.UI.Text.FontWeights.Bold, TextAlignment = TextAlignment.Right, HorizontalAlignment = HorizontalAlignment.Stretch, FlowDirection = FlowDirection.RightToLeft });
            panel.Children.Add(weightLabel);
            panel.Children.Add(box);
            panel.Children.Add(presets);
'@

Replace-Exact 'Pages\PosPage.xaml.cs' @'
                XamlRoot = XamlRoot, RequestedTheme = ElementTheme.Dark, FlowDirection = FlowDirection.RightToLeft,
                Title = "تحديد الكمية", Content = panel, PrimaryButtonText = "إضافة", CloseButtonText = "إلغاء", DefaultButton = ContentDialogButton.Primary
'@ @'
                XamlRoot = XamlRoot, RequestedTheme = ElementTheme.Dark, FlowDirection = FlowDirection.RightToLeft,
                HorizontalContentAlignment = HorizontalAlignment.Stretch,
                Title = "تحديد الكمية", Content = panel, PrimaryButtonText = "إضافة", CloseButtonText = "إلغاء", DefaultButton = ContentDialogButton.Primary
'@

# Release/version bump.
Replace-Exact 'SweetsPOS.csproj' '<Version>2.0.7</Version>' '<Version>2.0.8</Version>'
Replace-Exact 'SweetsPOS.csproj' '<AssemblyVersion>2.0.7.0</AssemblyVersion>' '<AssemblyVersion>2.0.8.0</AssemblyVersion>'
Replace-Exact 'SweetsPOS.csproj' '<FileVersion>2.0.7.0</FileVersion>' '<FileVersion>2.0.8.0</FileVersion>'
Replace-Exact 'installer.iss' '#define MyAppVersion "2.0.7"' '#define MyAppVersion "2.0.8"'
Replace-Exact 'installer.iss' 'OutputBaseFilename=GeekPOS-Setup-x64-v2.0.7' 'OutputBaseFilename=GeekPOS-Setup-x64-v2.0.8'

Write-Host 'Geek POS v2.0.8 POS quantity/RTL fixes applied successfully.'
