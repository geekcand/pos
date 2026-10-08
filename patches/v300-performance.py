from pathlib import Path
import re, sys
root=Path(sys.argv[1])

def read(p): return (root/p).read_text(encoding='utf-8-sig')
def write(p,s): (root/p).write_text(s,encoding='utf-8-sig')
def rep(s,a,b,label):
    if a not in s: raise SystemExit(f'missing {label}')
    return s.replace(a,b,1)

# Version 3.0.0 + startup-oriented publish optimization
p='SweetsPOS.csproj'; s=read(p)
s=s.replace('<Version>2.0.9</Version>','<Version>3.0.0</Version>')
s=s.replace('<AssemblyVersion>2.0.9.0</AssemblyVersion>','<AssemblyVersion>3.0.0.0</AssemblyVersion>')
s=s.replace('<FileVersion>2.0.9.0</FileVersion>','<FileVersion>3.0.0.0</FileVersion>')
s=rep(s,'    <Product>Geek POS</Product>','    <Product>Geek POS</Product>\n    <PublishReadyToRun>true</PublishReadyToRun>\n    <TieredCompilation>true</TieredCompilation>\n    <TieredPGO>true</TieredPGO>', 'publish tuning')
write(p,s)
p='installer.iss'; s=read(p).replace('#define MyAppVersion "2.0.9"','#define MyAppVersion "3.0.0"').replace('OutputBaseFilename=GeekPOS-Setup-x64-v2.0.9','OutputBaseFilename=GeekPOS-Setup-x64-v3.0.0'); write(p,s)

# Fast SQLite defaults + indexes for frequently loaded admin/report data.
p='Data/AppDbContext.cs'; s=read(p)
s=s.replace('=> optionsBuilder.UseSqlite($"Data Source={_dbPath};Cache=Shared;Foreign Keys=True");','=> optionsBuilder.UseSqlite($"Data Source={_dbPath};Cache=Shared;Foreign Keys=True;Pooling=True;Default Timeout=5");')
write(p,s)
p='Data/DatabaseService.cs'; s=read(p)
s=rep(s,'        if (connection.State != System.Data.ConnectionState.Open) await connection.OpenAsync();', '''        if (connection.State != System.Data.ConnectionState.Open) await connection.OpenAsync();

        // Performance-safe SQLite tuning. WAL improves read/write concurrency and NORMAL keeps
        // durability while avoiding an fsync on every small UI read/write transaction.
        async Task PragmaAsync(string sql)
        {
            await using var pragma = connection.CreateCommand();
            pragma.CommandText = sql;
            await pragma.ExecuteNonQueryAsync();
        }
        await PragmaAsync("PRAGMA journal_mode=WAL;");
        await PragmaAsync("PRAGMA synchronous=NORMAL;");
        await PragmaAsync("PRAGMA temp_store=MEMORY;");
        await PragmaAsync("PRAGMA busy_timeout=5000;");''','sqlite tuning')
anchor='        await ExecAsync("CREATE INDEX IF NOT EXISTS IX_Sales_ShiftId_ShiftInvoiceNumber ON Sales(ShiftId, ShiftInvoiceNumber);");'
extra='''        await ExecAsync("CREATE INDEX IF NOT EXISTS IX_Sales_ShiftId_ShiftInvoiceNumber ON Sales(ShiftId, ShiftInvoiceNumber);");
        await ExecAsync("CREATE INDEX IF NOT EXISTS IX_Sales_CreatedAt_Status ON Sales(CreatedAt, Status);");
        await ExecAsync("CREATE INDEX IF NOT EXISTS IX_Sales_ShiftId_Status ON Sales(ShiftId, Status);");
        await ExecAsync("CREATE INDEX IF NOT EXISTS IX_SaleItems_SaleId ON SaleItems(SaleId);");
        await ExecAsync("CREATE INDEX IF NOT EXISTS IX_SaleItems_ProductId ON SaleItems(ProductId);");
        await ExecAsync("CREATE INDEX IF NOT EXISTS IX_Payments_SaleId ON Payments(SaleId);");
        await ExecAsync("CREATE INDEX IF NOT EXISTS IX_Refunds_CreatedAt ON Refunds(CreatedAt);");
        await ExecAsync("CREATE INDEX IF NOT EXISTS IX_Refunds_ShiftId ON Refunds(ShiftId);");
        await ExecAsync("CREATE INDEX IF NOT EXISTS IX_Expenses_CreatedAt ON Expenses(CreatedAt);");
        await ExecAsync("CREATE INDEX IF NOT EXISTS IX_Expenses_ShiftId ON Expenses(ShiftId);");
        await ExecAsync("CREATE INDEX IF NOT EXISTS IX_AuditLogs_CreatedAt ON AuditLogs(CreatedAt);");
        await ExecAsync("CREATE INDEX IF NOT EXISTS IX_Products_CategoryId_IsActive ON Products(CategoryId, IsActive);");
        await ExecAsync("CREATE INDEX IF NOT EXISTS IX_Products_IsActive ON Products(IsActive);");'''
s=rep(s,anchor,extra,'indexes')
write(p,s)

# Settings memory cache. Every mutation updates/invalidates it, so behavior remains current.
p='Services/SettingsService.cs'; s=read(p)
s=re.sub(r'public sealed class SettingsService\(DatabaseService database, AuditService audit\)\n\{.*\n\}', '''public sealed class SettingsService(DatabaseService database, AuditService audit)
{
    public event EventHandler? Changed;
    private readonly SemaphoreSlim _cacheGate = new(1, 1);
    private volatile Dictionary<string, string>? _cache;
    private readonly object _cacheSync = new();

    private async Task<Dictionary<string, string>> SnapshotAsync()
    {
        if (_cache is not null) return _cache;
        await _cacheGate.WaitAsync();
        try
        {
            if (_cache is null)
            {
                await using var db = database.CreateContext();
                _cache = await db.Settings.AsNoTracking().ToDictionaryAsync(x => x.Key, x => x.Value);
            }
            return _cache;
        }
        finally { _cacheGate.Release(); }
    }

    public void InvalidateCache() { lock (_cacheSync) _cache = null; }

    public async Task<string> GetAsync(string key, string fallback = "")
    {
        var all = await SnapshotAsync();
        return all.TryGetValue(key, out var value) ? value : fallback;
    }

    public async Task<decimal> GetDecimalAsync(string key, decimal fallback = 0)
        => decimal.TryParse(await GetAsync(key), out var value) ? value : fallback;

    public async Task<bool> GetBoolAsync(string key, bool fallback = false)
        => bool.TryParse(await GetAsync(key), out var value) ? value : fallback;

    public async Task SetAsync(string key, string value)
    {
        await using var db = database.CreateContext();
        var row = await db.Settings.FirstOrDefaultAsync(x => x.Key == key);
        var old = row?.Value;
        if (row is null) db.Settings.Add(new AppSetting { Key = key, Value = value });
        else row.Value = value;
        await db.SaveChangesAsync();
        lock (_cacheSync)
        {
            if (_cache is not null)
            {
                var updated = new Dictionary<string, string>(_cache, StringComparer.Ordinal) { [key] = value };
                _cache = updated;
            }
        }
        await audit.WriteAsync("SettingChanged", "Setting", key, $"{old ?? "<new>"} -> {value}");
        Changed?.Invoke(this, EventArgs.Empty);
    }

    public async Task SetManyAsync(IReadOnlyDictionary<string, string> values)
    {
        if (values.Count == 0) return;
        await using var db = database.CreateContext();
        var keys = values.Keys.ToList();
        var rows = await db.Settings.Where(x => keys.Contains(x.Key)).ToDictionaryAsync(x => x.Key);
        foreach (var pair in values)
        {
            if (rows.TryGetValue(pair.Key, out var row)) row.Value = pair.Value;
            else db.Settings.Add(new AppSetting { Key = pair.Key, Value = pair.Value });
        }
        await db.SaveChangesAsync();
        lock (_cacheSync)
        {
            if (_cache is not null)
            {
                var updated = new Dictionary<string, string>(_cache, StringComparer.Ordinal);
                foreach (var pair in values) updated[pair.Key] = pair.Value;
                _cache = updated;
            }
        }
        await audit.WriteAsync("SettingsChanged", "Setting", "batch", $"Updated {values.Count} settings");
        Changed?.Invoke(this, EventArgs.Empty);
    }

    public async Task<Dictionary<string, string>> GetAllAsync()
        => new(await SnapshotAsync(), StringComparer.Ordinal);
}''', s, flags=re.S)
write(p,s)

# Catalog cache for category/product reads, with explicit invalidation on every mutation.
p='Services/CatalogService.cs'; s=read(p)
s=rep(s,'public sealed class CatalogService(DatabaseService database, AuditService audit)\n{', '''public sealed class CatalogService(DatabaseService database, AuditService audit)
{
    private readonly SemaphoreSlim _cacheGate = new(1, 1);
    private List<Category>? _allCategories;
    private List<Product>? _allProducts;

    public void InvalidateCategories() => _allCategories = null;
    public void InvalidateProducts() => _allProducts = null;
    public void InvalidateAll() { _allCategories = null; _allProducts = null; }

    private async Task<List<Category>> LoadCategoriesAsync()
    {
        if (_allCategories is not null) return _allCategories;
        await _cacheGate.WaitAsync();
        try
        {
            if (_allCategories is null)
            {
                await using var db = database.CreateContext();
                _allCategories = await db.Categories.AsNoTracking().OrderBy(x => x.SortOrder).ThenBy(x => x.Name).ToListAsync();
            }
            return _allCategories;
        }
        finally { _cacheGate.Release(); }
    }

    private async Task<List<Product>> LoadProductsAsync()
    {
        if (_allProducts is not null) return _allProducts;
        await _cacheGate.WaitAsync();
        try
        {
            if (_allProducts is null)
            {
                await using var db = database.CreateContext();
                _allProducts = await db.Products.AsNoTracking().Include(x => x.Category)
                    .OrderBy(x => x.Category!.SortOrder).ThenBy(x => x.ArabicName).ToListAsync();
            }
            return _allProducts;
        }
        finally { _cacheGate.Release(); }
    }''','catalog fields')
s=re.sub(r'''    public async Task<List<Category>> GetCategoriesAsync\(bool activeOnly = true\)\n    \{.*?\n    \}\n\n    public async Task<List<Product>> GetProductsAsync\(int\? categoryId = null, string\? search = null, bool activeOnly = true\)\n    \{.*?\n    \}''', '''    public async Task<List<Category>> GetCategoriesAsync(bool activeOnly = true)
    {
        var all = await LoadCategoriesAsync();
        return (activeOnly ? all.Where(x => x.IsActive) : all).ToList();
    }

    public async Task<List<Product>> GetProductsAsync(int? categoryId = null, string? search = null, bool activeOnly = true)
    {
        IEnumerable<Product> q = await LoadProductsAsync();
        if (activeOnly) q = q.Where(x => x.IsActive);
        if (categoryId.HasValue) q = q.Where(x => x.CategoryId == categoryId.Value);
        if (!string.IsNullOrWhiteSpace(search))
        {
            var text = search.Trim();
            q = q.Where(x => x.Name.Contains(text, StringComparison.CurrentCultureIgnoreCase)
                || x.ArabicName.Contains(text, StringComparison.CurrentCultureIgnoreCase)
                || (!string.IsNullOrWhiteSpace(x.Barcode) && x.Barcode.Contains(text, StringComparison.OrdinalIgnoreCase))
                || (!string.IsNullOrWhiteSpace(x.Sku) && x.Sku.Contains(text, StringComparison.OrdinalIgnoreCase)));
        }
        return q.ToList();
    }''', s, count=1, flags=re.S)
s=re.sub(r'''    public async Task<Product\?> FindByBarcodeAsync\(string barcode\)\n    \{.*?\n    \}''','''    public async Task<Product?> FindByBarcodeAsync(string barcode)
    {
        var all = await LoadProductsAsync();
        return all.FirstOrDefault(x => x.IsActive && string.Equals(x.Barcode, barcode, StringComparison.OrdinalIgnoreCase));
    }''',s,count=1,flags=re.S)
s=s.replace('        await audit.WriteAsync(input.Id == 0 ? "ProductCreated" : "ProductUpdated", "Product", row.Id.ToString(), details);\n        return row;', '        InvalidateProducts();\n        await audit.WriteAsync(input.Id == 0 ? "ProductCreated" : "ProductUpdated", "Product", row.Id.ToString(), details);\n        return row;')
s=s.replace('        await audit.WriteAsync(input.Id == 0 ? "CategoryCreated" : "CategoryUpdated", "Category", row.Id.ToString(), row.Name);\n        return row;', '        InvalidateCategories();\n        InvalidateProducts();\n        await audit.WriteAsync(input.Id == 0 ? "CategoryCreated" : "CategoryUpdated", "Category", row.Id.ToString(), row.Name);\n        return row;')
s=s.replace('        await audit.WriteAsync("StockAdjusted", "Product", productId.ToString(), $"Delta {delta:0.###}; New {newQuantity:0.###}; {note}");', '        InvalidateProducts();\n        await audit.WriteAsync("StockAdjusted", "Product", productId.ToString(), $"Delta {delta:0.###}; New {newQuantity:0.###}; {note}");')
s=s.replace('        await audit.WriteAsync("ProductDeleted", "Product", productId.ToString(), product.ArabicName);', '        InvalidateProducts();\n        await audit.WriteAsync("ProductDeleted", "Product", productId.ToString(), product.ArabicName);')
s=s.replace('        await audit.WriteAsync("CategoryDeleted", "Category", categoryId.ToString(), category.Name);', '        InvalidateCategories();\n        InvalidateProducts();\n        await audit.WriteAsync("CategoryDeleted", "Category", categoryId.ToString(), category.Name);')
write(p,s)

p='Services/SaleService.cs'; s=read(p)
s=s.replace('public sealed class SaleService(DatabaseService database, AppSession session, SettingsService settings, AuditService audit)', 'public sealed class SaleService(DatabaseService database, AppSession session, SettingsService settings, AuditService audit, CatalogService catalog)')
s=s.replace('        await tx.CommitAsync();\n\n        await audit.WriteAsync("SaleCompleted"', '        await tx.CommitAsync();\n        catalog.InvalidateProducts();\n\n        await audit.WriteAsync("SaleCompleted"',1)
s=s.replace('        await tx.CommitAsync();\n        await audit.WriteAsync("RefundCreated"', '        await tx.CommitAsync();\n        catalog.InvalidateProducts();\n        await audit.WriteAsync("RefundCreated"',1)
s=s.replace('        await tx.CommitAsync();\n        await audit.WriteAsync("SaleVoided"', '        await tx.CommitAsync();\n        catalog.InvalidateProducts();\n        await audit.WriteAsync("SaleVoided"',1)
write(p,s)
p='Services/AppServices.cs'; s=read(p).replace('Sales = new SaleService(Database, Session, Settings, Audit);','Sales = new SaleService(Database, Session, Settings, Audit, Catalog);'); write(p,s)

p='Pages/SettingsPage.xaml.cs'; s=read(p)
s=s.replace('await App.Services.Backups.RestoreAsync(file.Path);', 'await App.Services.Backups.RestoreAsync(file.Path); App.Services.Settings.InvalidateCache(); App.Services.Catalog.InvalidateAll();')
s=s.replace('''        var s = await App.Services.Settings.GetAllAsync();''','''        var settingsTask = App.Services.Settings.GetAllAsync();
        var printersTask = Task.Run(() => PrinterSettings.InstalledPrinters.Cast<string>().OrderBy(x => x).ToList());
        await Task.WhenAll(settingsTask, printersTask);
        var s = await settingsTask;
        _installedPrinters = await printersTask;''',1)
s=s.replace('        LoadInstalledPrinters(s.GetValueOrDefault("ReceiptPrinter", ""), s.GetValueOrDefault("RestaurantKitchenPrinter", ""));','        BindInstalledPrinters(s.GetValueOrDefault("ReceiptPrinter", ""), s.GetValueOrDefault("RestaurantKitchenPrinter", ""));',1)
s=s.replace('''    private void LoadInstalledPrinters(string? selectedReceipt = null, string? selectedKitchen = null)
    {
        _installedPrinters = PrinterSettings.InstalledPrinters.Cast<string>().OrderBy(x => x).ToList();
        PrinterNamePicker.ItemsSource = _installedPrinters.ToList();
        KitchenPrinterPicker.ItemsSource = _installedPrinters.ToList();
        SelectPrinter(PrinterNamePicker, selectedReceipt);
        SelectPrinter(KitchenPrinterPicker, selectedKitchen);
    }''','''    private void BindInstalledPrinters(string? selectedReceipt = null, string? selectedKitchen = null)
    {
        PrinterNamePicker.ItemsSource = _installedPrinters.ToList();
        KitchenPrinterPicker.ItemsSource = _installedPrinters.ToList();
        SelectPrinter(PrinterNamePicker, selectedReceipt);
        SelectPrinter(KitchenPrinterPicker, selectedKitchen);
    }

    private async Task RefreshInstalledPrintersAsync(string? selectedReceipt = null, string? selectedKitchen = null)
    {
        _installedPrinters = await Task.Run(() => PrinterSettings.InstalledPrinters.Cast<string>().OrderBy(x => x).ToList());
        BindInstalledPrinters(selectedReceipt, selectedKitchen);
    }''')
s=s.replace('LoadInstalledPrinters(receipt, kitchen); await LoadCategoryPrinterRoutesAsync(await App.Services.Settings.GetAllAsync());','await RefreshInstalledPrintersAsync(receipt, kitchen); await LoadCategoryPrinterRoutesAsync(await App.Services.Settings.GetAllAsync());')
write(p,s)

p='Pages/ShellPage.xaml.cs'; s=read(p)
if 'using Microsoft.UI.Xaml.Media.Animation;' not in s: s=s.replace('using Microsoft.UI.Xaml.Media.Imaging;','using Microsoft.UI.Xaml.Media.Imaging;\nusing Microsoft.UI.Xaml.Media.Animation;')
s=s.replace('if (ContentFrame.CurrentSourcePageType != type) ContentFrame.Navigate(type);','if (ContentFrame.CurrentSourcePageType != type) ContentFrame.Navigate(type, null, new SuppressNavigationTransitionInfo());')
s=s.replace('        SetActiveButton(tag);\n        ApplyPermissions();','        SetActiveButton(tag);')
s=s.replace('''        await LoadBrandAsync();
        Navigate(ResolveHomeTag());''','''        await LoadBrandAsync();
        Navigate(ResolveHomeTag());
        _ = WarmNavigationDataAsync();''')
s=s.replace('''    private async Task LoadBrandAsync()''','''    private async Task WarmNavigationDataAsync()
    {
        try
        {
            await Task.WhenAll(
                App.Services.Settings.GetAllAsync(),
                App.Services.Catalog.GetCategoriesAsync(false));
            await Task.Delay(700);
            await App.Services.Catalog.GetProductsAsync(null, null, false);
        }
        catch { }
    }

    private async Task LoadBrandAsync()''')
write(p,s)

pages=['DashboardPage','CategoriesPage','ProductsPage','PaymentMethodsPage','UsersPage','ReportsPage','ExpensesPage','RefundsPage','ShiftsPage','ReceiptDesignerPage','AuditPage','OnlinePage','SettingsPage']
for name in pages:
    p=f'Pages/{name}.xaml.cs'
    s=read(p)
    old='InitializeComponent();'
    if old in s and 'NavigationCacheMode.Required' not in s:
        replacement = old + ('\n        NavigationCacheMode = Microsoft.UI.Xaml.Navigation.NavigationCacheMode.Required;' if '\n        InitializeComponent();' in s else ' NavigationCacheMode = Microsoft.UI.Xaml.Navigation.NavigationCacheMode.Required;')
        s=s.replace(old, replacement, 1)
        write(p,s)

print('v3.0.0 performance patch applied')
