from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()

def read(rel): return (root/rel).read_text(encoding='utf-8-sig')
def write(rel,s): (root/rel).write_text(s,encoding='utf-8-sig')
def must(s, old, new, label, count=1):
    if old not in s: raise SystemExit(f'missing anchor: {label}')
    return s.replace(old,new,count)

# App theme
p='App.xaml'; s=read(p)
repls={
'#17110D':'#15181C','#120D09':'#111315','#241A15':'#181B1F','#2E221A':'#20242A','#3A2B20':'#262B31',
'#43301F':'#32373E','#3A2A1D':'#292E34','#F4E9DA':'#F5F6F7','#CBB89F':'#9DA3AA','#8C7862':'#747B84',
'#CE9F4C':'#D4A64E','#E8C87F':'#E0B45E','#8A6B34':'#8A6A31','#20140A':'#111315','#C6566B':'#D95858',
'#E7A5B3':'#F08B8B','#6FA287':'#3FAE67','#A9CDB9':'#79D297','#6E9BC4':'#6EA6D8','#2A1B13':'#1D2024',
'#100A07':'#0D0F11','#35261C':'#20242A','#5A4029':'#32373E','#68492E':'#3A4048','Tajawal':'Segoe UI'}
for a,b in repls.items(): s=s.replace(a,b)
s=s.replace('CornerRadius" Value="14"','CornerRadius" Value="10"')
s=s.replace('CornerRadius" Value="12"','CornerRadius" Value="10"')
s=s.replace('CornerRadius" Value="11"','CornerRadius" Value="10"')
s=s.replace('CornerRadius" Value="9"','CornerRadius" Value="10"')
s=must(s,'<Setter Property="Padding" Value="16,10" />\n                <Setter Property="FontWeight" Value="Bold" />','<Setter Property="Padding" Value="16,10" />\n                <Setter Property="MinHeight" Value="46" />\n                <Setter Property="FontWeight" Value="Bold" />','accent minheight')
s=must(s,'<Setter Property="Padding" Value="14,9" />\n                <Setter Property="FontWeight" Value="SemiBold" />','<Setter Property="Padding" Value="14,9" />\n                <Setter Property="MinHeight" Value="44" />\n                <Setter Property="FontWeight" Value="SemiBold" />','soft minheight')
s=must(s,'<Setter Property="MinWidth" Value="170" />\n                <Setter Property="MinHeight" Value="165" />','<Setter Property="MinWidth" Value="170" />\n                <Setter Property="MinHeight" Value="165" />\n                <Setter Property="Background" Value="{StaticResource CardBrushSoft}" />\n                <Setter Property="BorderBrush" Value="{StaticResource BorderBrushSoft}" />','product card')
s=s.replace('<Setter Property="Background" Value="#111315" />','<Setter Property="Background" Value="{StaticResource CardBrushSoft}" />')
write(p,s)

# POS XAML
p='Pages/PosPage.xaml'; s=read(p)
for a,b in {
'Content="🛍 تيك أواي"':'Content="تيك أواي"','Content="🛵 دليفري"':'Content="دليفري"','Content="🍽 الصالة"':'Content="الصالة"',
'Content="↩ الطاولات"':'Content="الطاولات"','Content="🖨 إرسال للمطبخ"':'Content="إرسال للمطبخ"','Content="🧾 طباعة حساب الطاولة"':'Content="طباعة حساب الطاولة"',
'Content="🛵 تحميل على طيار"':'Content="تحميل على طيار"','Content="⏸ تعليق الطلب"':'Content="تعليق الطلب"','Content="📥 الطلبات المعلقة"':'Content="الطلبات المعلقة"',
'Content="🗑 مسح"':'Content="مسح"','PlaceholderText="ابحث باسم الصنف..."':'PlaceholderText="ابحث باسم الصنف أو الكود..."','PlaceholderText="الباركود"':'PlaceholderText="مسح باركود"'}.items():
    s=s.replace(a,b)
s=must(s,'<Border Grid.Column="0" Background="{StaticResource CardBrush}" BorderBrush="{StaticResource BorderBrushStrong}"','<Border Grid.Column="0" Background="{StaticResource CardBrushSoft}" BorderBrush="{StaticResource BorderBrushStrong}"','invoice surface')
s=must(s,'<Border Grid.Row="2" Background="{StaticResource CardBrushSoft}" BorderBrush="{StaticResource BorderBrushStrong}"','<Border Grid.Row="2" Background="{StaticResource CardBrush}" BorderBrush="{StaticResource BorderBrushStrong}"','invoice total surface')
s=s.replace('<TextBlock Grid.Column="1" Text="اضغط على الصنف لإضافته" VerticalAlignment="Center" FontSize="12" Foreground="{StaticResource HintTextBrush}"/>','<TextBlock Grid.Column="1" Text="اختر الصنف" VerticalAlignment="Center" FontSize="12" Foreground="{StaticResource HintTextBrush}"/>')
s=must(s,'<TextBlock Text="🍽" FontSize="30" HorizontalAlignment="Center" VerticalAlignment="Center" Opacity="0.82"/>','<FontIcon Glyph="&#xE719;" FontSize="27" Foreground="{StaticResource MutedTextBrush}" HorizontalAlignment="Center" VerticalAlignment="Center" Opacity="0.72"/>','product fallback')
s=must(s,'<TextBlock Grid.Column="1" Text="{Binding Price}" FontSize="17" FontWeight="Bold" Foreground="{StaticResource AccentBrushSoft}"/>','<StackPanel Grid.Column="1" Orientation="Horizontal" Spacing="4" VerticalAlignment="Center"><TextBlock Text="{Binding Price}" FontSize="16" FontWeight="SemiBold" Foreground="{StaticResource LightTextBrush}"/><TextBlock Text="ج.م" FontSize="11" Foreground="{StaticResource MutedTextBrush}" VerticalAlignment="Bottom"/></StackPanel>','product price')
write(p,s)

# POS C#
p='Pages/PosPage.xaml.cs'; s=read(p)
s=s.replace('else icon = new TextBlock { Text = "📁", FontSize = 18, HorizontalAlignment = HorizontalAlignment.Center };','else icon = new FontIcon { Glyph = "\uE8B7", FontSize = 17, HorizontalAlignment = HorizontalAlignment.Center };')
s=s.replace('catch { icon = new TextBlock { Text = "📁", FontSize = 18, HorizontalAlignment = HorizontalAlignment.Center }; }','catch { icon = new FontIcon { Glyph = "\uE8B7", FontSize = 17, HorizontalAlignment = HorizontalAlignment.Center }; }')
s=s.replace('var icon = new TextBlock { Text = "🍽", FontSize = 18, HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center };','var icon = new FontIcon { Glyph = "\uE7BF", FontSize = 17, HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center };')
s=s.replace('PrintTableBillButton.Content = "🧾 إعادة طباعة حساب الطاولة";','PrintTableBillButton.Content = "إعادة طباعة حساب الطاولة";')
s=s.replace('else PrintTableBillButton.Content = "🧾 طباعة حساب الطاولة";','else PrintTableBillButton.Content = "طباعة حساب الطاولة";')
s=must(s,'TotalText.Text = $"{displayTotal:0.00}"; PayButton.Content = $"ادفع {displayTotal:0.00}";','TotalText.Text = $"{displayTotal:0.00}"; PayButton.Content = $"ادفع {displayTotal:0.00}"; PayButton.IsEnabled = App.Services.Session.CurrentShift is not null && displayTotal > 0m;','pay state')
s=must(s,'_ => "اختر صنفًا لإضافته إلى الفاتورة"','_ => _cart.Count == 0 ? "اختر صنفًا لإضافته إلى الفاتورة" : $"{_cart.Count} أصناف • {_cart.Sum(x => x.Quantity):0.###} وحدة"','cart subtitle')
write(p,s)

# Shell
p='Pages/ShellPage.xaml'; s=read(p)
s=s.replace('<Border Width="44" Height="44" CornerRadius="22" Background="White" Padding="3">','<Border Width="44" Height="44" CornerRadius="22" Background="{StaticResource CardBrushSoft}" BorderBrush="{StaticResource BorderBrushStrong}" BorderThickness="1" Padding="3">')
s=s.replace('Content="← رجوع للكاشير"','Content="رجوع للكاشير"').replace('Content="🟢 الورديات"','Content="الورديات"').replace('Content="⚙️ لوحة الإدارة"','Content="لوحة الإدارة"')
s=s.replace('<Button Content="تسجيل خروج" Click="Logout_Click" Style="{StaticResource DangerButtonStyle}" />','<Button Content="تسجيل خروج" Click="Logout_Click" Style="{StaticResource TopNavButtonStyle}" Opacity="0.82" />')
for emo,g in {'📁':'E8B7','🍬':'E719','💳':'E8C7','👥':'E716','📊':'E9D2','🟢':'E823','🧾':'E8A5','↩️':'E72B','🛡️':'EA18','☁️':'E753','⚙️':'E713'}.items():
    s=s.replace(f'<TextBlock Grid.Column="1" Text="{emo}" FontSize="16" HorizontalAlignment="Center" VerticalAlignment="Center"/>',f'<FontIcon Grid.Column="1" Glyph="&#x{g};" FontSize="16" Foreground="{{StaticResource MutedTextBrush}}" HorizontalAlignment="Center" VerticalAlignment="Center"/>')
write(p,s)

# Legacy admin page
p='Pages/AdminPage.xaml'; s=read(p)
for emo in ['🗂️','📁','🍬','💳','👥','📊','🟢','🧾','↩️','🛡️','☁️','⚙️']:
    s=s.replace(emo+' ','')
write(p,s)

# Version
p='SweetsPOS.csproj'; s=read(p); s=s.replace('<Version>3.0.2</Version>','<Version>3.0.3</Version>').replace('<AssemblyVersion>3.0.2.0</AssemblyVersion>','<AssemblyVersion>3.0.3.0</AssemblyVersion>').replace('<FileVersion>3.0.2.0</FileVersion>','<FileVersion>3.0.3.0</FileVersion>'); write(p,s)
p='installer.iss'; s=read(p); s=s.replace('#define MyAppVersion "3.0.2"','#define MyAppVersion "3.0.3"').replace('OutputBaseFilename=GeekPOS-Setup-x64-v3.0.2','OutputBaseFilename=GeekPOS-Setup-x64-v3.0.3'); write(p,s)
print('v3.0.3 visual refinement applied')
