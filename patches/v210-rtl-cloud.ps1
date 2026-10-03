param([Parameter(Mandatory=$true)][string]$SourceRoot)
$ErrorActionPreference = 'Stop'

function Read-Normalized([string]$RelativePath) {
    $full = Join-Path $SourceRoot $RelativePath
    if (!(Test-Path -LiteralPath $full)) { throw "Missing file: $full" }
    return (Get-Content -LiteralPath $full -Raw) -replace "`r`n", "`n"
}

function Write-Utf8([string]$RelativePath, [string]$Text) {
    $full = Join-Path $SourceRoot $RelativePath
    [System.IO.File]::WriteAllText($full, $Text, [System.Text.UTF8Encoding]::new($false))
}

function Replace-Exact([string]$RelativePath, [string]$Old, [string]$New) {
    $text = Read-Normalized $RelativePath
    $oldN = $Old -replace "`r`n", "`n"
    $newN = $New -replace "`r`n", "`n"
    if (!$text.Contains($oldN)) { throw "Expected block not found in $RelativePath`n--- expected ---`n$oldN" }
    Write-Utf8 $RelativePath ($text.Replace($oldN, $newN))
}

function Set-Text([string]$RelativePath, [string]$Text) {
    Write-Utf8 $RelativePath (($Text -replace "`r`n", "`n").TrimStart("`n") + "`n")
}

function Ensure-ContentDialogsRtl([string]$RelativePath) {
    $text = Read-Normalized $RelativePath
    $matches = [regex]::Matches($text, 'new\s+ContentDialog\s*\{')
    for ($i = $matches.Count - 1; $i -ge 0; $i--) {
        $m = $matches[$i]
        $brace = $text.IndexOf('{', $m.Index)
        if ($brace -lt 0) { continue }
        $probeLen = [Math]::Min(800, $text.Length - $brace)
        $probe = $text.Substring($brace, $probeLen)
        if ($probe -notmatch 'FlowDirection\s*=\s*FlowDirection\.RightToLeft') {
            $text = $text.Insert($brace + 1, ' FlowDirection = FlowDirection.RightToLeft,')
        }
    }
    Write-Utf8 $RelativePath $text
}

Replace-Exact 'MainWindow.xaml' @'
    <Grid Background="{StaticResource WindowBackgroundBrush}" RequestedTheme="Dark">
'@ @'
    <Grid Background="{StaticResource WindowBackgroundBrush}" RequestedTheme="Dark" FlowDirection="RightToLeft">
'@

Replace-Exact 'App.xaml' @'
            </LinearGradientBrush>

            <Style x:Key="CardStyle" TargetType="Border">
'@ @'
            </LinearGradientBrush>

            <Style TargetType="TextBlock">
                <Setter Property="FlowDirection" Value="RightToLeft" />
                <Setter Property="TextAlignment" Value="Right" />
            </Style>

            <Style x:Key="CardStyle" TargetType="Border">
'@

Replace-Exact 'App.xaml' '<Style x:Key="SectionTitleStyle" TargetType="TextBlock">' @'
<Style x:Key="SectionTitleStyle" TargetType="TextBlock">
                <Setter Property="TextAlignment" Value="Right" />
                <Setter Property="FlowDirection" Value="RightToLeft" />
'@
Replace-Exact 'App.xaml' '<Style x:Key="SubTitleStyle" TargetType="TextBlock">' @'
<Style x:Key="SubTitleStyle" TargetType="TextBlock">
                <Setter Property="TextAlignment" Value="Right" />
                <Setter Property="FlowDirection" Value="RightToLeft" />
'@
Replace-Exact 'App.xaml' '<Style x:Key="KpiValueStyle" TargetType="TextBlock">' @'
<Style x:Key="KpiValueStyle" TargetType="TextBlock">
                <Setter Property="TextAlignment" Value="Right" />
                <Setter Property="FlowDirection" Value="RightToLeft" />
'@
Replace-Exact 'App.xaml' '<Style TargetType="TextBox">' @'
<Style TargetType="TextBox">
                <Setter Property="TextAlignment" Value="Right" />
'@

Replace-Exact 'Pages\PosPage.xaml' 'HorizontalContentAlignment="Stretch" TextAlignment="Center" FlowDirection="LeftToRight"' 'HorizontalContentAlignment="Center" VerticalContentAlignment="Center" TextAlignment="Center" FlowDirection="LeftToRight"'

Set-Text 'Pages\OnlinePage.xaml' @'
<Page x:Class="SweetsPOS.Pages.OnlinePage" xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" FlowDirection="RightToLeft">
    <ScrollViewer Background="{StaticResource AppBackgroundBrush}">
        <StackPanel Padding="24" Spacing="16" MaxWidth="980" HorizontalAlignment="Right" FlowDirection="RightToLeft">
            <StackPanel>
                <TextBlock Text="الإدارة السحابية" Style="{StaticResource SectionTitleStyle}"/>
                <TextBlock Text="ربط Geek POS بالإدارة السحابية لمتابعة المبيعات والورديات والمخزون ومزامنة التحديثات عند توفر الإنترنت." Foreground="{StaticResource MutedTextBrush}" TextWrapping="Wrap"/>
            </StackPanel>
            <Border Style="{StaticResource CardStyle}">
                <StackPanel Spacing="11">
                    <TextBlock Text="إعداد الاتصال السحابي" Style="{StaticResource SubTitleStyle}"/>
                    <CheckBox x:Name="OnlineEnabled" Content="تفعيل المزامنة السحابية تلقائيًا"/>
                    <TextBox x:Name="SupabaseUrl" Header="رابط الخدمة السحابية" PlaceholderText="https://xxxx.supabase.co" FlowDirection="LeftToRight" TextAlignment="Left"/>
                    <PasswordBox x:Name="AnonKey" Header="مفتاح الاتصال" PasswordRevealMode="Peek" FlowDirection="LeftToRight"/>
                    <Grid ColumnSpacing="10" FlowDirection="RightToLeft">
                        <Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions>
                        <TextBox x:Name="StoreId" Header="معرف الفرع / الجهاز" PlaceholderText="main"/>
                        <NumberBox Grid.Column="1" x:Name="SyncMinutes" Header="المزامنة كل (دقيقة)" Minimum="1" Maximum="120" Value="5" SpinButtonPlacementMode="Hidden"/>
                    </Grid>
                    <TextBlock Text="حساب المزامنة السحابية" Style="{StaticResource SubTitleStyle}" Margin="0,8,0,0"/>
                    <Grid ColumnSpacing="10" FlowDirection="RightToLeft">
                        <Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions>
                        <TextBox x:Name="OnlineEmail" Header="بريد حساب المزامنة" FlowDirection="LeftToRight" TextAlignment="Left"/>
                        <PasswordBox Grid.Column="1" x:Name="OnlinePassword" Header="كلمة مرور حساب المزامنة" PasswordRevealMode="Peek" FlowDirection="LeftToRight"/>
                    </Grid>
                    <CheckBox x:Name="AutoUpdates" Content="تطبيق تحديثات الأصناف والأقسام القادمة من الإدارة السحابية تلقائيًا"/>
                    <TextBlock Text="يستمر Geek POS في العمل بشكل طبيعي عند انقطاع الإنترنت، وتُستأنف المزامنة تلقائيًا بعد عودة الاتصال." FontSize="12" Foreground="{StaticResource MutedTextBrush}" TextWrapping="Wrap"/>
                </StackPanel>
            </Border>
            <Border Style="{StaticResource CardStyle}">
                <StackPanel Spacing="10">
                    <TextBlock Text="التحكم والمزامنة" Style="{StaticResource SubTitleStyle}"/>
                    <TextBlock x:Name="StatusText" Text="لم تبدأ المزامنة بعد" Foreground="{StaticResource AccentBrushSoft}" TextWrapping="Wrap"/>
                    <StackPanel Orientation="Horizontal" Spacing="8" FlowDirection="RightToLeft">
                        <Button Content="حفظ الإعدادات" Click="Save_Click" Style="{StaticResource AccentButtonStyle}"/>
                        <Button Content="اختبار الاتصال" Click="Test_Click" Style="{StaticResource SoftButtonStyle}"/>
                        <Button Content="مزامنة الآن" Click="Sync_Click" Style="{StaticResource SoftButtonStyle}"/>
                        <Button Content="جلب التحديثات" Click="Updates_Click" Style="{StaticResource SoftButtonStyle}"/>
                    </StackPanel>
                    <InfoBar x:Name="Info" IsOpen="False" IsClosable="True"/>
                </StackPanel>
            </Border>
        </StackPanel>
    </ScrollViewer>
</Page>
'@

Replace-Exact 'Pages\OnlinePage.xaml.cs' 'تم حفظ إعدادات الأونلاين.' 'تم حفظ إعدادات الإدارة السحابية.'
Replace-Exact 'Pages\ShellPage.xaml' 'Content="🌐 أونلاين"' 'Content="☁ الإدارة السحابية"'
Replace-Exact 'Services\OnlineSyncService.cs' 'تم تطبيق {applied} تحديث من الأونلاين' 'تم تطبيق {applied} تحديث من الإدارة السحابية'
Replace-Exact 'Services\OnlineSyncService.cs' 'أكمل رابط Supabase و anon key ومعرف الفرع أولاً من قسم أونلاين.' 'أكمل بيانات الاتصال ومعرف الفرع أولًا من قسم الإدارة السحابية.'

Replace-Exact 'Pages\PageHelpers.cs' @'
        var dialog = new ContentDialog { XamlRoot = root, RequestedTheme = ElementTheme.Dark, Title = title, Content = message, CloseButtonText = "حسنًا" };
'@ @'
        var dialog = new ContentDialog { XamlRoot = root, RequestedTheme = ElementTheme.Dark, FlowDirection = FlowDirection.RightToLeft, Title = title, Content = new TextBlock { Text = message, TextWrapping = TextWrapping.Wrap, TextAlignment = TextAlignment.Right, HorizontalAlignment = HorizontalAlignment.Stretch, FlowDirection = FlowDirection.RightToLeft }, CloseButtonText = "حسنًا" };
'@

Get-ChildItem -LiteralPath (Join-Path $SourceRoot 'Pages') -Filter '*.xaml.cs' | ForEach-Object {
    $rel = 'Pages\' + $_.Name
    $content = Read-Normalized $rel
    if ($content.Contains('new ContentDialog')) { Ensure-ContentDialogsRtl $rel }
}

Replace-Exact 'Services\ReceiptService.cs' @'
                var output = new List<byte>(encoding.GetByteCount(receiptText) + 8192);
                output.AddRange(new byte[] { 0x1B, 0x40 }); // ESC/POS initialize
'@ @'
                var output = new List<byte>(encoding.GetByteCount(receiptText) + 8192);
                output.AddRange(new byte[] { 0x1B, 0x40 }); // ESC/POS initialize
                output.AddRange(new byte[] { 0x1B, 0x61, 0x02 }); // right align Arabic text reports
'@

Replace-Exact 'OnlineDashboard\index.html' '<title>Geek POS Online</title>' '<title>الإدارة السحابية — Geek POS</title>'
Replace-Exact 'OnlineDashboard\index.html' 'color:var(--text);font-family:' 'color:var(--text);text-align:right;font-family:'
Replace-Exact 'OnlineDashboard\index.html' '<div><h1>Geek POS Online</h1><div class="sub">لوحة متابعة الإدارة عن بُعد</div></div>' '<div><h1>الإدارة السحابية</h1><div class="sub">متابعة وإدارة نشاط Geek POS عن بُعد</div></div>'
Replace-Exact 'OnlineDashboard\index.html' '<button id="loginBtn" class="btn primary">دخول للوحة</button>' '<button id="loginBtn" class="btn primary">دخول إلى الإدارة السحابية</button>'
Replace-Exact 'OnlineDashboard\index.html' '<div class="login-note">بيانات Supabase الخاصة بالمشروع مضبوطة داخل الصفحة بالفعل. لا يتم تخزين كلمة المرور داخل ملف HTML، ويتم تسجيل الدخول من خلال Supabase Auth فقط.</div>' '<div class="login-note">سجّل الدخول باستخدام حساب الإدارة المصرح به للوصول إلى بيانات المنشأة بأمان.</div>'
Replace-Exact 'OnlineDashboard\index.html' '<div class="tiny">Online Dashboard</div>' '<div class="tiny">الإدارة السحابية</div>'
Replace-Exact 'OnlineDashboard\index.html' 'متابعة الورديات المفتوحة والمغلقة وإغلاق الوردية أونلاين' 'متابعة الورديات المفتوحة والمغلقة وإغلاق الوردية عن بُعد'
Replace-Exact 'OnlineDashboard\index.html' "$('loginBtn').textContent='دخول للوحة'" "$('loginBtn').textContent='دخول إلى الإدارة السحابية'"
Replace-Exact 'OnlineDashboard\index.html' 'إغلاق الوردية #${id} من الأونلاين؟' 'إغلاق الوردية #${id} من الإدارة السحابية؟'
Replace-Exact 'OnlineDashboard\index.html' 'إغلاق من لوحة Geek POS Online' 'إغلاق من الإدارة السحابية'
Replace-Exact 'OnlineDashboard\index.html' "wb.creator='Geek POS Online'" "wb.creator='Geek POS Cloud Management'"
Replace-Exact 'OnlineDashboard\README-AR.txt' 'لوحة Geek POS Online — v1.9' 'الإدارة السحابية لـ Geek POS'
Replace-Exact 'OnlineDashboard\README-AR.txt' 'صفحة أونلاين داخل البرنامج' 'صفحة الإدارة السحابية داخل البرنامج'
Replace-Exact 'OnlineDashboard\README-AR.txt' 'لوحة الأونلاين' 'الإدارة السحابية'

Replace-Exact 'SweetsPOS.csproj' '<Version>2.0.9</Version>' '<Version>2.0.10</Version>'
Replace-Exact 'SweetsPOS.csproj' '<AssemblyVersion>2.0.9.0</AssemblyVersion>' '<AssemblyVersion>2.0.10.0</AssemblyVersion>'
Replace-Exact 'SweetsPOS.csproj' '<FileVersion>2.0.9.0</FileVersion>' '<FileVersion>2.0.10.0</FileVersion>'
Replace-Exact 'installer.iss' '#define MyAppVersion "2.0.9"' '#define MyAppVersion "2.0.10"'
Replace-Exact 'installer.iss' 'OutputBaseFilename=GeekPOS-Setup-x64-v2.0.9' 'OutputBaseFilename=GeekPOS-Setup-x64-v2.0.10'

Write-Host 'Geek POS v2.0.10 RTL/cloud/customer-polish patch applied successfully.'
