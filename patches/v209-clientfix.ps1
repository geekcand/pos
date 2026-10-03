param([Parameter(Mandatory=$true)][string]$SourceRoot)
$ErrorActionPreference = 'Stop'

function Read-Normalized([string]$RelativePath) {
    $full = Join-Path $SourceRoot $RelativePath
    if (!(Test-Path -LiteralPath $full)) { throw "Missing file: $full" }
    return (Get-Content -LiteralPath $full -Raw) -replace "`r`n", "`n"
}

function Write-Utf8([string]$RelativePath, [string]$Text) {
    $full = Join-Path $SourceRoot $RelativePath
    [System.IO.File]::WriteAllText($full, ($Text -replace "`r`n", "`n"), [System.Text.UTF8Encoding]::new($false))
}

function Replace-Exact([string]$RelativePath, [string]$Old, [string]$New) {
    $text = Read-Normalized $RelativePath
    $oldN = $Old -replace "`r`n", "`n"
    $newN = $New -replace "`r`n", "`n"
    if (!$text.Contains($oldN)) { throw "Expected block not found in $RelativePath`n--- expected ---`n$oldN" }
    Write-Utf8 $RelativePath ($text.Replace($oldN, $newN))
}

function Replace-Literal([string]$RelativePath, [string]$Old, [string]$New) {
    Replace-Exact $RelativePath $Old $New
}

# IMPORTANT: this patch is based only on the verified Geek POS v2.0.9 source artifact.
# It deliberately avoids changing page/grid layout or POS cart structure.

# 1) Arabic text and ContentDialog direction: modify the EXISTING implicit styles only.
Replace-Exact 'App.xaml' @'
            <Style TargetType="TextBlock">
                <Setter Property="FontFamily" Value="Tajawal" />
                <Setter Property="Foreground" Value="{StaticResource LightTextBrush}" />
            </Style>
'@ @'
            <Style TargetType="TextBlock">
                <Setter Property="FontFamily" Value="Tajawal" />
                <Setter Property="Foreground" Value="{StaticResource LightTextBrush}" />
                <Setter Property="FlowDirection" Value="RightToLeft" />
                <Setter Property="TextAlignment" Value="Right" />
            </Style>
'@

Replace-Exact 'App.xaml' @'
            <Style TargetType="ContentDialog">
                <Setter Property="FontFamily" Value="Tajawal" />
                <Setter Property="Foreground" Value="{StaticResource LightTextBrush}" />
                <Setter Property="Background" Value="{StaticResource CardBrush}" />
'@ @'
            <Style TargetType="ContentDialog">
                <Setter Property="FontFamily" Value="Tajawal" />
                <Setter Property="Foreground" Value="{StaticResource LightTextBrush}" />
                <Setter Property="Background" Value="{StaticResource CardBrush}" />
                <Setter Property="FlowDirection" Value="RightToLeft" />
'@

# 2) Customer-facing Cloud Administration page; same control names and code-behind behavior.
$onlinePage = @'
<Page x:Class="SweetsPOS.Pages.OnlinePage" xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
    <ScrollViewer Background="{StaticResource AppBackgroundBrush}">
        <StackPanel Padding="24" Spacing="16" MaxWidth="980" HorizontalAlignment="Right" FlowDirection="RightToLeft">
            <StackPanel>
                <TextBlock Text="الإدارة السحابية" Style="{StaticResource SectionTitleStyle}"/>
                <TextBlock Text="مزامنة بيانات المتجر مع لوحة الإدارة السحابية ومتابعة المبيعات والورديات والتحديثات عند توفر الإنترنت." Foreground="{StaticResource MutedTextBrush}" TextWrapping="Wrap"/>
            </StackPanel>

            <Border Style="{StaticResource CardStyle}">
                <StackPanel Spacing="11">
                    <TextBlock Text="إعداد الاتصال السحابي" Style="{StaticResource SubTitleStyle}"/>
                    <CheckBox x:Name="OnlineEnabled" Content="تفعيل المزامنة السحابية التلقائية"/>
                    <TextBox x:Name="SupabaseUrl" Header="رابط الخدمة السحابية" PlaceholderText="أدخل رابط الخدمة"/>
                    <PasswordBox x:Name="AnonKey" Header="مفتاح الاتصال السحابي" PasswordRevealMode="Peek"/>
                    <Grid ColumnSpacing="10">
                        <Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions>
                        <TextBox x:Name="StoreId" Header="معرف الفرع" PlaceholderText="main"/>
                        <NumberBox Grid.Column="1" x:Name="SyncMinutes" Header="المزامنة كل (دقيقة)" Minimum="1" Maximum="120" Value="5" SpinButtonPlacementMode="Hidden"/>
                    </Grid>
                    <TextBlock Text="بيانات حساب المزامنة" Style="{StaticResource SubTitleStyle}" Margin="0,8,0,0"/>
                    <Grid ColumnSpacing="10">
                        <Grid.ColumnDefinitions><ColumnDefinition/><ColumnDefinition/></Grid.ColumnDefinitions>
                        <TextBox x:Name="OnlineEmail" Header="البريد الإلكتروني"/>
                        <PasswordBox Grid.Column="1" x:Name="OnlinePassword" Header="كلمة المرور" PasswordRevealMode="Peek"/>
                    </Grid>
                    <CheckBox x:Name="AutoUpdates" Content="تطبيق تحديثات الأصناف والأقسام الواردة من الإدارة السحابية تلقائياً"/>
                    <TextBlock Text="يستمر البيع بشكل طبيعي عند انقطاع الإنترنت، وتتم المزامنة تلقائياً عند عودة الاتصال." FontSize="12" Foreground="{StaticResource MutedTextBrush}" TextWrapping="Wrap"/>
                </StackPanel>
            </Border>

            <Border Style="{StaticResource CardStyle}">
                <StackPanel Spacing="10">
                    <TextBlock Text="التحكم والمزامنة" Style="{StaticResource SubTitleStyle}"/>
                    <TextBlock x:Name="StatusText" Text="لم تبدأ المزامنة بعد" Foreground="{StaticResource AccentBrushSoft}" TextWrapping="Wrap"/>
                    <StackPanel Orientation="Horizontal" Spacing="8">
                        <Button Content="حفظ الإعدادات" Click="Save_Click" Style="{StaticResource AccentButtonStyle}"/>
                        <Button Content="اختبار الاتصال" Click="Test_Click" Style="{StaticResource SoftButtonStyle}"/>
                        <Button Content="مزامنة البيانات الآن" Click="Sync_Click" Style="{StaticResource SoftButtonStyle}"/>
                        <Button Content="تحديث البيانات الآن" Click="Updates_Click" Style="{StaticResource SoftButtonStyle}"/>
                    </StackPanel>
                    <InfoBar x:Name="Info" IsOpen="False" IsClosable="True"/>
                </StackPanel>
            </Border>
        </StackPanel>
    </ScrollViewer>
</Page>
'@
Write-Utf8 'Pages\OnlinePage.xaml' $onlinePage

Replace-Literal 'Pages\ShellPage.xaml' 'Content="🌐 أونلاين" Tag="online"' 'Content="☁ الإدارة السحابية" Tag="online"'

# 3) Production/customer wording in the external cloud dashboard. Internal API constants remain untouched.
Replace-Literal 'OnlineDashboard\index.html' '<title>Geek POS Online</title>' '<title>الإدارة السحابية — Geek POS</title>'
Replace-Literal 'OnlineDashboard\index.html' '<div><h1>Geek POS Online</h1><div class="sub">لوحة متابعة الإدارة عن بُعد</div></div>' '<div><h1>الإدارة السحابية</h1><div class="sub">متابعة وإدارة نشاط المتجر عن بُعد</div></div>'
Replace-Literal 'OnlineDashboard\index.html' '🔐 دخول آمن عبر Supabase Auth' '🔐 دخول آمن'
Replace-Literal 'OnlineDashboard\index.html' 'Geek POS • Online Management Dashboard' 'Geek POS • الإدارة السحابية'
Replace-Literal 'OnlineDashboard\index.html' '<div class="muted">استخدم حساب Supabase Auth الخاص بالإدارة</div>' '<div class="muted">استخدم حساب الإدارة السحابية الخاص بك</div>'
Replace-Literal 'OnlineDashboard\index.html' '<div class="login-actions"><button id="loginBtn" class="btn primary">دخول للوحة</button><button id="demoBtn" class="btn ghost">معاينة تجريبية</button></div>' '<div class="login-actions"><button id="loginBtn" class="btn primary">دخول إلى الإدارة السحابية</button></div>'
Replace-Literal 'OnlineDashboard\index.html' '<div class="login-note">بيانات Supabase الخاصة بالمشروع مضبوطة داخل الصفحة بالفعل. لا يتم تخزين كلمة المرور داخل ملف HTML، ويتم تسجيل الدخول من خلال Supabase Auth فقط.</div>' '<div class="login-note">تسجيل الدخول مخصص لحساب الإدارة المعتمد لحماية بيانات المتجر.</div>'
Replace-Literal 'OnlineDashboard\index.html' '<div><b>Geek POS</b><div class="tiny">Online Dashboard</div></div>' '<div><b>Geek POS</b><div class="tiny">الإدارة السحابية</div></div>'
Replace-Literal 'OnlineDashboard\index.html' '<button data-page="connection"><span class="ico">◎</span>الاتصال</button>' '<button data-page="connection"><span class="ico">◎</span>حالة الاتصال</button>'
Replace-Literal 'OnlineDashboard\index.html' '.login-actions{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:18px}' '.login-actions{display:grid;grid-template-columns:1fr;gap:10px;margin-top:18px}'
Replace-Literal 'OnlineDashboard\index.html' 'إغلاق الوردية أونلاين' 'إغلاق الوردية عن بُعد'
Replace-Literal 'OnlineDashboard\index.html' 'إغلاق الوردية #${id} من الأونلاين؟' 'إغلاق الوردية #${id} من الإدارة السحابية؟'
Replace-Literal 'OnlineDashboard\index.html' "'إغلاق من لوحة Geek POS Online'" "'إغلاق من الإدارة السحابية'"
Replace-Literal 'OnlineDashboard\index.html' "wb.creator='Geek POS Online'" "wb.creator='Geek POS'"
Replace-Literal 'OnlineDashboard\index.html' "$('loginBtn').textContent='دخول للوحة'" "$('loginBtn').textContent='دخول إلى الإدارة السحابية'"
Replace-Literal 'OnlineDashboard\index.html' 'اختر الفترة المطلوبة. التقارير التاريخية تُرفع من التطبيق إلى Supabase تلقائيًا بعد تجهيز جدول التقارير.' 'اختر الفترة المطلوبة لعرض التقارير التي تمت مزامنتها من جهاز الكاشير.'
Replace-Literal 'OnlineDashboard\index.html' "$('demoBtn').onclick=enterDemo;" "if($('demoBtn')) $('demoBtn').onclick=enterDemo;"

Replace-Exact 'OnlineDashboard\index.html' @'
<section id="page-connection" class="page">
        <div class="section-title"><div><h3>الاتصال وبيانات المزامنة</h3><p>معلومات المشروع الحالي وحالة آخر Snapshot.</p></div></div>
        <div class="grid half">
          <div class="card pad"><h3>Supabase</h3><div class="info-card">Project URL<div class="code">https://xquuknplqqcjmalxrsop.supabase.co</div><br>المفتاح المستخدم في الصفحة هو Publishable Key فقط. لا تستخدم Service Role Key داخل ملفات HTML العامة.</div></div>
          <div class="card pad"><h3>بيانات الجهاز</h3><div class="stats-row" style="grid-template-columns:1fr 1fr"><div class="mini"><span>Store ID</span><b id="cStore">—</b></div><div class="mini"><span>App Version</span><b id="cVersion">—</b></div><div class="mini"><span>Device</span><b id="cDevice">—</b></div><div class="mini"><span>آخر رفع</span><b id="cUpdated">—</b></div></div></div>
        </div>
      </section>
'@ @'
<section id="page-connection" class="page">
        <div class="section-title"><div><h3>حالة الاتصال</h3><p>حالة ربط جهاز الكاشير بالإدارة السحابية.</p></div></div>
        <div class="card pad"><h3>بيانات الجهاز</h3><div class="stats-row" style="grid-template-columns:1fr 1fr"><div class="mini"><span>الفرع</span><b id="cStore">—</b></div><div class="mini"><span>إصدار التطبيق</span><b id="cVersion">—</b></div><div class="mini"><span>الجهاز</span><b id="cDevice">—</b></div><div class="mini"><span>آخر مزامنة</span><b id="cUpdated">—</b></div></div></div>
      </section>
'@
Replace-Literal 'OnlineDashboard\index.html' "connection:['الاتصال','حالة الربط بين الصفحة وSupabase']" "connection:['حالة الاتصال','حالة الربط بين جهاز الكاشير والإدارة السحابية']"
Replace-Literal 'OnlineDashboard\index.html' "'جدول التقارير غير موجود في Supabase. شغّل supabase-schema.sql الخاص بإصدار v1.9 مرة واحدة ثم اضغط مزامنة من التطبيق.'" "'التقارير السحابية غير متاحة حالياً. تأكد من اكتمال المزامنة من جهاز الكاشير ثم أعد المحاولة.'"

# 4) Shift receipt: render and print an 80mm raster image, matching the sale receipt approach.
$shiftPrintMethods = @'

    public async Task<string> PrintShiftClosingAsync(Shift shift, ShiftTotals totals, string prefix)
    {
        var path = await RenderShiftClosingImageAsync(shift, totals, prefix);
        var printer = await settings.GetAsync("ReceiptPrinter");
        if (!string.IsNullOrWhiteSpace(printer))
        {
            try
            {
                using var bitmap = new Bitmap(path);
                var raster = BitmapToEscPos(bitmap);
                var output = new List<byte>(raster.Length + 32);
                output.AddRange(new byte[] { 0x1B, 0x40, 0x1B, 0x61, 0x01 });
                output.AddRange(raster);
                output.AddRange(new byte[] { 0x0A, 0x0A, 0x0A, 0x1D, 0x56, 0x00 });
                RawPrinter.Send(printer, output.ToArray());
                return $"تمت الطباعة على {printer}";
            }
            catch { }
        }
        return path;
    }

    private async Task<string> RenderShiftClosingImageAsync(Shift shift, ShiftTotals totals, string prefix)
    {
        var all = await settings.GetAllAsync();
        const int width = 576;
        const int margin = 24;
        var currency = "جنيه";
        var showLogo = ParseBool(all.GetValueOrDefault("ReceiptShowLogo"), false);
        var logoPath = all.GetValueOrDefault("ReceiptLogoPath", "");

        using var canvas = new Bitmap(width, 980, PixelFormat.Format32bppArgb);
        using var g = Graphics.FromImage(canvas);
        g.Clear(Color.White);
        g.SmoothingMode = SmoothingMode.HighQuality;
        g.InterpolationMode = InterpolationMode.HighQualityBicubic;
        g.TextRenderingHint = TextRenderingHint.AntiAliasGridFit;

        using var black = new SolidBrush(Color.FromArgb(20, 20, 20));
        using var gray = new SolidBrush(Color.FromArgb(100, 100, 100));
        using var linePen = new Pen(Color.FromArgb(80, 80, 80), 1f);
        using var storeFont = new Font("Segoe UI", 28f, FontStyle.Bold, GraphicsUnit.Pixel);
        using var titleFont = new Font("Segoe UI", 18f, FontStyle.Bold, GraphicsUnit.Pixel);
        using var textFont = new Font("Segoe UI", 15f, FontStyle.Regular, GraphicsUnit.Pixel);
        using var boldFont = new Font("Segoe UI", 15f, FontStyle.Bold, GraphicsUnit.Pixel);
        using var totalFont = new Font("Segoe UI", 16f, FontStyle.Bold, GraphicsUnit.Pixel);
        using var smallFont = new Font("Segoe UI", 13f, FontStyle.Regular, GraphicsUnit.Pixel);

        float y = 18;
        if (showLogo && !string.IsNullOrWhiteSpace(logoPath) && File.Exists(logoPath))
        {
            try
            {
                using var img = System.Drawing.Image.FromFile(logoPath);
                var maxW = Math.Clamp((int)await settings.GetDecimalAsync("ReceiptLogoWidthDots", 220), 96, 420);
                var scale = Math.Min(maxW / (float)img.Width, 120f / img.Height);
                var w = Math.Max(1, (int)(img.Width * scale));
                var h = Math.Max(1, (int)(img.Height * scale));
                g.DrawImage(img, new Rectangle((width - w) / 2, (int)y, w, h));
                y += h + 10;
            }
            catch { }
        }

        DrawCentered(g, all.GetValueOrDefault("StoreName", "اسم المؤسسة"), storeFont, black, y, width); y += 42;
        DrawCentered(g, "تقرير إغلاق الوردية", titleFont, black, y, width); y += 36;
        g.DrawLine(linePen, margin, y, width - margin, y); y += 12;
        DrawShiftTextRow(g, $"رقم الوردية: #{shift.Id}", boldFont, black, ref y, width, margin);
        DrawShiftTextRow(g, $"الكاشير: {shift.User?.DisplayName ?? App.Services.Session.CurrentUser?.DisplayName ?? "-"}", textFont, black, ref y, width, margin);
        DrawShiftTextRow(g, $"الفتح: {FormatDateTime(shift.OpenedAt)}", textFont, black, ref y, width, margin);
        DrawShiftTextRow(g, $"الإغلاق: {(shift.ClosedAt.HasValue ? FormatDateTime(shift.ClosedAt.Value) : "-")}", textFont, black, ref y, width, margin);
        y += 4; g.DrawLine(linePen, margin, y, width - margin, y); y += 12;
        DrawTotalRow(g, "إجمالي المبيعات", totals.GrossSales, currency, boldFont, black, ref y, width, margin);
        DrawTotalRow(g, "كاش", totals.CashSales, currency, textFont, black, ref y, width, margin);
        DrawTotalRow(g, "كارت", totals.CardSales, currency, textFont, black, ref y, width, margin);
        DrawTotalRow(g, "إنستاباي", totals.InstaPaySales, currency, textFont, black, ref y, width, margin);
        DrawTotalRow(g, "محفظة", totals.WalletSales, currency, textFont, black, ref y, width, margin);
        DrawTotalRow(g, "الخصومات", totals.Discounts, currency, textFont, black, ref y, width, margin);
        DrawTotalRow(g, "المرتجعات", totals.CashRefunds + totals.OtherRefunds, currency, textFont, black, ref y, width, margin);
        DrawTotalRow(g, "المصروفات", totals.Expenses, currency, textFont, black, ref y, width, margin);
        y += 4; g.DrawLine(linePen, margin, y, width - margin, y); y += 12;
        DrawTotalRow(g, "النقدية المتوقعة", shift.ExpectedCash, currency, totalFont, black, ref y, width, margin);
        DrawTotalRow(g, "النقدية الفعلية", shift.ActualCash ?? 0, currency, totalFont, black, ref y, width, margin);
        DrawTotalRow(g, "الفرق", shift.Difference ?? 0, currency, totalFont, black, ref y, width, margin);

        var footer = all.GetValueOrDefault("ReceiptFooter", "");
        if (!string.IsNullOrWhiteSpace(footer)) { y += 10; DrawCentered(g, footer, smallFont, gray, y, width); y += 26; }
        y += 18;
        var finalHeight = Math.Max(260, Math.Min(canvas.Height, (int)Math.Ceiling(y)));
        using var cropped = canvas.Clone(new Rectangle(0, 0, width, finalHeight), PixelFormat.Format32bppArgb);
        var dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SweetsPOS", "Receipts");
        Directory.CreateDirectory(dir);
        var safePrefix = string.IsNullOrWhiteSpace(prefix) ? $"shift-{shift.Id}" : prefix;
        var path = Path.Combine(dir, $"{safePrefix}-{DateTime.Now:yyyyMMdd-HHmmss}.png");
        cropped.Save(path, ImageFormat.Png);
        return path;
    }

    private static void DrawShiftTextRow(Graphics g, string text, Font font, Brush brush, ref float y, int width, int margin)
    {
        DrawRtl(g, text, font, brush, new RectangleF(margin, y, width - margin * 2, 28), StringAlignment.Near);
        y += 30;
    }
'@
Replace-Exact 'Services\ReceiptService.cs' @'

    private static readonly byte[] CashDrawerKickCommand = [0x1B, 0x70, 0x00, 0x32, 0xFA];
'@ ($shiftPrintMethods + @'

    private static readonly byte[] CashDrawerKickCommand = [0x1B, 0x70, 0x00, 0x32, 0xFA];
'@)

Replace-Exact 'Pages\ShiftsPage.xaml.cs' @'
            var report = await App.Services.Receipts.BuildShiftClosingAsync(closed, totals);
            var print = await App.Services.Receipts.PrintOrSaveAsync(report, $"shift-{closed.Id}");
'@ @'
            var print = await App.Services.Receipts.PrintShiftClosingAsync(closed, totals, $"shift-{closed.Id}");
'@
Replace-Exact 'Pages\ShiftsPage.xaml.cs' @'
            var report = await App.Services.Receipts.BuildShiftClosingAsync(closed, totals);
            var print = await App.Services.Receipts.PrintOrSaveAsync(report, $"shift-{closed.Id}-admin-close");
'@ @'
            var print = await App.Services.Receipts.PrintShiftClosingAsync(closed, totals, $"shift-{closed.Id}-admin-close");
'@
Replace-Exact 'Pages\ShiftsPage.xaml.cs' @'
            var report = await App.Services.Receipts.BuildShiftClosingAsync(selected, totals);
            var print = await App.Services.Receipts.PrintOrSaveAsync(report, $"shift-{selected.Id}-reprint");
'@ @'
            var print = await App.Services.Receipts.PrintShiftClosingAsync(selected, totals, $"shift-{selected.Id}-reprint");
'@

Write-Host 'Geek POS v2.0.9 customer RTL/cloud/shift-print patch applied.'
