using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Reflection;
using System.Text;
using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using SweetsPOS.Core;
using SweetsPOS.Data;

namespace SweetsPOS.Services;

public sealed class OnlineSyncService : IDisposable
{
    private readonly DatabaseService database;
    private readonly SettingsService settings;
    private readonly ReportService reports;
    private readonly AuditService audit;
    private readonly HttpClient http = new() { Timeout = TimeSpan.FromSeconds(15) };
    private readonly CancellationTokenSource cts = new();
    private Task? loopTask;
    private DateTime lastSyncUtc = DateTime.MinValue;

    public string LastStatus { get; private set; } = "لم تبدأ المزامنة بعد";
    public DateTime? LastSuccessUtc { get; private set; }

    public OnlineSyncService(DatabaseService database, SettingsService settings, ReportService reports, AuditService audit)
    {
        this.database = database;
        this.settings = settings;
        this.reports = reports;
        this.audit = audit;
    }

    public void Start()
    {
        loopTask ??= Task.Run(() => RunLoopAsync(cts.Token));
    }

    private async Task RunLoopAsync(CancellationToken token)
    {
        using var timer = new PeriodicTimer(TimeSpan.FromMinutes(1));
        while (!token.IsCancellationRequested)
        {
            try
            {
                if (await settings.GetBoolAsync("OnlineEnabled", false))
                {
                    var mins = Math.Clamp((int)await settings.GetDecimalAsync("OnlineSyncMinutes", 5), 1, 120);
                    if (DateTime.UtcNow - lastSyncUtc >= TimeSpan.FromMinutes(mins))
                    {
                        await SyncNowAsync(token);
                        if (await settings.GetBoolAsync("OnlineAutoApplyUpdates", true))
                            await CheckAndApplyUpdatesAsync(token);
                    }
                }
            }
            catch (Exception ex)
            {
                LastStatus = "فشل الاتصال التلقائي: " + ex.Message;
            }

            try { await timer.WaitForNextTickAsync(token); }
            catch (OperationCanceledException) { break; }
        }
    }

    public async Task<string> TestConnectionAsync(CancellationToken token = default)
    {
        var cfg = await GetConfigAsync();
        EnsureConfigured(cfg);
        var auth = await GetAuthAsync(cfg, token);
        using var request = CreateRequest(HttpMethod.Get, $"{cfg.Url}/rest/v1/pos_snapshots?select=store_id&limit=1", cfg, auth);
        using var response = await http.SendAsync(request, token);
        if (!response.IsSuccessStatusCode)
            throw new InvalidOperationException($"Supabase رفض الاتصال ({(int)response.StatusCode}): {await response.Content.ReadAsStringAsync(token)}");
        LastStatus = "الاتصال بـ Supabase يعمل بنجاح";
        return LastStatus;
    }

    public async Task<string> SyncNowAsync(CancellationToken token = default)
    {
        var cfg = await GetConfigAsync();
        EnsureConfigured(cfg);
        var auth = await GetAuthAsync(cfg, token);
        var snapshot = await BuildSnapshotAsync(cfg.StoreId);
        var version = Assembly.GetExecutingAssembly().GetName().Version?.ToString() ?? "1.0.0";
        var payload = new[]
        {
            new
            {
                store_id = cfg.StoreId,
                app_version = version,
                device_name = Environment.MachineName,
                updated_at = DateTime.UtcNow,
                payload = snapshot
            }
        };

        using var request = CreateRequest(HttpMethod.Post, $"{cfg.Url}/rest/v1/pos_snapshots?on_conflict=store_id", cfg, auth);
        request.Headers.TryAddWithoutValidation("Prefer", "resolution=merge-duplicates,return=minimal");
        request.Content = JsonContent.Create(payload);
        using var response = await http.SendAsync(request, token);
        if (!response.IsSuccessStatusCode)
            throw new InvalidOperationException($"تعذر رفع البيانات ({(int)response.StatusCode}): {await response.Content.ReadAsStringAsync(token)}");

        lastSyncUtc = DateTime.UtcNow;
        LastSuccessUtc = lastSyncUtc;
        LastStatus = $"آخر مزامنة ناجحة: {DateTime.Now:dd/MM/yyyy hh:mm tt}";
        return LastStatus;
    }

    public async Task<string> CheckAndApplyUpdatesAsync(CancellationToken token = default)
    {
        var cfg = await GetConfigAsync();
        EnsureConfigured(cfg);
        var auth = await GetAuthAsync(cfg, token);
        var store = Uri.EscapeDataString(cfg.StoreId);
        var url = $"{cfg.Url}/rest/v1/pos_updates?store_id=eq.{store}&status=eq.pending&order=id.asc&select=id,update_type,payload";
        using var request = CreateRequest(HttpMethod.Get, url, cfg, auth);
        using var response = await http.SendAsync(request, token);
        if (!response.IsSuccessStatusCode)
            throw new InvalidOperationException($"تعذر جلب التحديثات ({(int)response.StatusCode}): {await response.Content.ReadAsStringAsync(token)}");

        var json = await response.Content.ReadAsStringAsync(token);
        var rows = JsonSerializer.Deserialize<List<OnlineUpdateRow>>(json, JsonOptions) ?? [];
        var applied = 0;
        foreach (var row in rows)
        {
            await ApplyUpdateAsync(row);
            await MarkUpdateAsync(cfg, auth, row.Id, "applied", token);
            applied++;
        }
        if (applied > 0)
        {
            await audit.WriteAsync("OnlineUpdatesApplied", "Online", cfg.StoreId, $"Applied {applied} online updates");
            LastStatus = $"تم تطبيق {applied} تحديث من الأونلاين";
        }
        else LastStatus = "لا توجد تحديثات أونلاين جديدة";
        return LastStatus;
    }

    private async Task<object> BuildSnapshotAsync(string storeId)
    {
        var today = DateTime.Today;
        var tomorrow = today.AddDays(1);
        var summary = await reports.GetSummaryAsync(today, tomorrow);
        var top = await reports.GetTopProductsAsync(today, tomorrow, 10);
        var low = await reports.GetLowStockAsync();

        await using var db = database.CreateContext();
        var shifts = await db.Shifts.AsNoTracking().Include(x => x.User).OrderByDescending(x => x.OpenedAt).Take(60)
            .Select(x => new
            {
                x.Id,
                user = x.User != null ? x.User.DisplayName : "-",
                status = x.Status.ToString(),
                x.OpeningCash,
                x.ExpectedCash,
                x.ActualCash,
                x.Difference,
                x.OpenedAt,
                x.ClosedAt
            }).ToListAsync();
        var expenses = await db.Expenses.AsNoTracking().Include(x => x.User).OrderByDescending(x => x.CreatedAt).Take(80)
            .Select(x => new { x.Id, x.Amount, x.Category, x.Reason, x.CreatedAt, user = x.User != null ? x.User.DisplayName : "-" }).ToListAsync();
        var categories = await db.Categories.AsNoTracking().OrderBy(x => x.SortOrder).Select(x => new { x.Id, x.Name, x.SortOrder, x.IsActive }).ToListAsync();
        var products = await db.Products.AsNoTracking().Include(x => x.Category).OrderBy(x => x.ArabicName)
            .Select(x => new
            {
                x.Id, x.Name, x.ArabicName, x.Sku, x.Barcode,
                category = x.Category != null ? x.Category.Name : "",
                unit = x.SellUnit.ToString(), x.Price, x.Cost, x.StockQuantity, x.LowStockLimit, x.TrackStock, x.IsActive, x.UpdatedAt
            }).ToListAsync();

        return new
        {
            storeId,
            generatedAt = DateTime.UtcNow,
            summary = new
            {
                summary.Sales, summary.Orders, summary.AverageOrder, summary.Cash, summary.Card,
                summary.InstaPay, summary.Wallet, summary.Expenses, summary.Refunds,
                summary.NetSales, summary.EstimatedGrossProfit
            },
            topProducts = top.Select(x => new { x.ProductName, x.Quantity, x.Sales }),
            lowStock = low.Select(x => new { x.Id, x.ArabicName, x.StockQuantity, x.LowStockLimit }),
            shifts,
            expenses,
            categories,
            products
        };
    }

    private async Task ApplyUpdateAsync(OnlineUpdateRow row)
    {
        var type = row.UpdateType?.Trim().ToLowerInvariant() ?? "";
        if (type == "category") { await ApplyCategoryAsync(row.Payload); return; }
        if (type == "product") { await ApplyProductAsync(row.Payload); return; }
        if (type == "catalog")
        {
            if (row.Payload.TryGetProperty("categories", out var cats) && cats.ValueKind == JsonValueKind.Array)
                foreach (var c in cats.EnumerateArray()) await ApplyCategoryAsync(c);
            if (row.Payload.TryGetProperty("products", out var products) && products.ValueKind == JsonValueKind.Array)
                foreach (var p in products.EnumerateArray()) await ApplyProductAsync(p);
            return;
        }
        if (type == "setting" && row.Payload.TryGetProperty("key", out var key) && row.Payload.TryGetProperty("value", out var value))
            await settings.SetAsync(key.GetString() ?? "", value.ToString());
    }

    private async Task ApplyCategoryAsync(JsonElement payload)
    {
        var name = GetString(payload, "name");
        if (string.IsNullOrWhiteSpace(name)) return;
        await using var db = database.CreateContext();
        var row = await db.Categories.FirstOrDefaultAsync(x => x.Name == name);
        if (row is null)
        {
            row = new Category { Name = name };
            db.Categories.Add(row);
        }
        if (payload.TryGetProperty("sortOrder", out var sort) && sort.TryGetInt32(out var order)) row.SortOrder = order;
        if (payload.TryGetProperty("isActive", out var active) && active.ValueKind is JsonValueKind.True or JsonValueKind.False) row.IsActive = active.GetBoolean();
        await db.SaveChangesAsync();
    }

    private async Task ApplyProductAsync(JsonElement payload)
    {
        var sku = GetString(payload, "sku");
        var barcode = GetString(payload, "barcode");
        var arabicName = GetString(payload, "arabicName");
        var name = GetString(payload, "name");
        if (string.IsNullOrWhiteSpace(arabicName) && string.IsNullOrWhiteSpace(name)) return;
        var categoryName = GetString(payload, "category");

        await using var db = database.CreateContext();
        var category = await db.Categories.FirstOrDefaultAsync(x => x.Name == categoryName);
        if (category is null)
        {
            category = new Category { Name = string.IsNullOrWhiteSpace(categoryName) ? "عام" : categoryName, SortOrder = 999, IsActive = true };
            db.Categories.Add(category);
            await db.SaveChangesAsync();
        }

        Product? row = null;
        if (!string.IsNullOrWhiteSpace(sku)) row = await db.Products.FirstOrDefaultAsync(x => x.Sku == sku);
        if (row is null && !string.IsNullOrWhiteSpace(barcode)) row = await db.Products.FirstOrDefaultAsync(x => x.Barcode == barcode);
        if (row is null && !string.IsNullOrWhiteSpace(arabicName)) row = await db.Products.FirstOrDefaultAsync(x => x.ArabicName == arabicName);
        if (row is null)
        {
            row = new Product { ArabicName = arabicName, Name = string.IsNullOrWhiteSpace(name) ? arabicName : name, CategoryId = category.Id };
            db.Products.Add(row);
        }

        row.ArabicName = string.IsNullOrWhiteSpace(arabicName) ? row.ArabicName : arabicName;
        row.Name = string.IsNullOrWhiteSpace(name) ? row.Name : name;
        row.Sku = string.IsNullOrWhiteSpace(sku) ? row.Sku : sku;
        row.Barcode = string.IsNullOrWhiteSpace(barcode) ? row.Barcode : barcode;
        row.CategoryId = category.Id;
        if (payload.TryGetProperty("sellUnit", out var unit) && Enum.TryParse<SellUnit>(unit.GetString(), true, out var sellUnit)) row.SellUnit = sellUnit;
        if (TryDecimal(payload, "price", out var price)) row.Price = price;
        if (TryDecimal(payload, "cost", out var cost)) row.Cost = cost;
        if (TryDecimal(payload, "stock", out var stock)) row.StockQuantity = stock;
        if (TryDecimal(payload, "lowStockLimit", out var low)) row.LowStockLimit = low;
        if (payload.TryGetProperty("trackStock", out var track) && track.ValueKind is JsonValueKind.True or JsonValueKind.False) row.TrackStock = track.GetBoolean();
        if (payload.TryGetProperty("isActive", out var active) && active.ValueKind is JsonValueKind.True or JsonValueKind.False) row.IsActive = active.GetBoolean();
        row.UpdatedAt = DateTime.Now;
        await db.SaveChangesAsync();
    }

    private async Task MarkUpdateAsync(OnlineConfig cfg, string auth, long id, string status, CancellationToken token)
    {
        using var request = CreateRequest(HttpMethod.Patch, $"{cfg.Url}/rest/v1/pos_updates?id=eq.{id}", cfg, auth);
        request.Headers.TryAddWithoutValidation("Prefer", "return=minimal");
        request.Content = JsonContent.Create(new { status, applied_at = DateTime.UtcNow });
        using var response = await http.SendAsync(request, token);
        response.EnsureSuccessStatusCode();
    }

    private async Task<OnlineConfig> GetConfigAsync()
    {
        var s = await settings.GetAllAsync();
        return new OnlineConfig(
            s.GetValueOrDefault("OnlineSupabaseUrl", "").Trim().TrimEnd('/'),
            s.GetValueOrDefault("OnlineSupabaseAnonKey", "").Trim(),
            s.GetValueOrDefault("OnlineEmail", "").Trim(),
            s.GetValueOrDefault("OnlinePassword", ""),
            s.GetValueOrDefault("OnlineStoreId", "main").Trim());
    }

    private static void EnsureConfigured(OnlineConfig cfg)
    {
        if (string.IsNullOrWhiteSpace(cfg.Url) || string.IsNullOrWhiteSpace(cfg.AnonKey) || string.IsNullOrWhiteSpace(cfg.StoreId))
            throw new InvalidOperationException("أكمل رابط Supabase و anon key ومعرف الفرع أولاً من قسم أونلاين.");
    }

    private async Task<string> GetAuthAsync(OnlineConfig cfg, CancellationToken token)
    {
        if (string.IsNullOrWhiteSpace(cfg.Email) || string.IsNullOrWhiteSpace(cfg.Password)) return cfg.AnonKey;
        using var request = new HttpRequestMessage(HttpMethod.Post, $"{cfg.Url}/auth/v1/token?grant_type=password");
        request.Headers.TryAddWithoutValidation("apikey", cfg.AnonKey);
        request.Content = JsonContent.Create(new { email = cfg.Email, password = cfg.Password });
        using var response = await http.SendAsync(request, token);
        var json = await response.Content.ReadAsStringAsync(token);
        if (!response.IsSuccessStatusCode) throw new InvalidOperationException($"فشل تسجيل دخول جهاز الكاشير إلى Supabase: {json}");
        using var doc = JsonDocument.Parse(json);
        return doc.RootElement.GetProperty("access_token").GetString() ?? cfg.AnonKey;
    }

    private static HttpRequestMessage CreateRequest(HttpMethod method, string url, OnlineConfig cfg, string auth)
    {
        var request = new HttpRequestMessage(method, url);
        request.Headers.TryAddWithoutValidation("apikey", cfg.AnonKey);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", auth);
        return request;
    }

    private static string GetString(JsonElement element, string name)
        => element.TryGetProperty(name, out var value) ? value.GetString() ?? "" : "";

    private static bool TryDecimal(JsonElement element, string name, out decimal value)
    {
        value = 0;
        if (!element.TryGetProperty(name, out var v)) return false;
        return v.ValueKind == JsonValueKind.Number ? v.TryGetDecimal(out value) : decimal.TryParse(v.ToString(), out value);
    }

    public void Dispose()
    {
        cts.Cancel();
        http.Dispose();
        cts.Dispose();
    }

    private sealed record OnlineConfig(string Url, string AnonKey, string Email, string Password, string StoreId);
    private sealed class OnlineUpdateRow
    {
        public long Id { get; set; }
        public string? UpdateType { get; set; }
        public JsonElement Payload { get; set; }
    }

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower
    };
}
