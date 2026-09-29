using Microsoft.EntityFrameworkCore;
using SweetsPOS.Core;
using SweetsPOS.Data;

namespace SweetsPOS.Services;

public sealed class SettingsService(DatabaseService database, AuditService audit)
{
    public event EventHandler? Changed;
    public async Task<string> GetAsync(string key, string fallback = "")
    {
        await using var db = database.CreateContext();
        return await db.Settings.AsNoTracking().Where(x => x.Key == key).Select(x => x.Value).FirstOrDefaultAsync() ?? fallback;
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
        await audit.WriteAsync("SettingsChanged", "Setting", "batch", $"Updated {values.Count} settings");
        Changed?.Invoke(this, EventArgs.Empty);
    }

    public async Task<Dictionary<string, string>> GetAllAsync()
    {
        await using var db = database.CreateContext();
        return await db.Settings.AsNoTracking().ToDictionaryAsync(x => x.Key, x => x.Value);
    }
}
