from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
p = root / "Services" / "OnlineSyncService.cs"
s = p.read_text(encoding="utf-8-sig")
old = '''        string? reportWarning = null;
        try { await SyncDailyReportsAsync(cfg, auth, token); }
        try { await SyncCustomersAsync(cfg, auth, token); } catch (Exception ex) { LastStatus = $"المزامنة الأساسية نجحت، لكن مزامنة العملاء تحتاج تحديث Supabase: {ex.Message}"; }
        catch (Exception ex) { reportWarning = ex.Message; }

        lastSyncUtc = DateTime.UtcNow;
        LastSuccessUtc = lastSyncUtc;
        LastStatus = reportWarning is null
            ? $"آخر مزامنة ناجحة: {DateTime.Now:dd/MM/yyyy hh:mm} {(DateTime.Now.Hour < 12 ? "صباحاً" : "مساءاً")}"
            : $"تمت المزامنة الأساسية. التقارير: {reportWarning}";
'''
new = '''        string? reportWarning = null;
        string? customerWarning = null;
        try { await SyncDailyReportsAsync(cfg, auth, token); }
        catch (Exception ex) { reportWarning = ex.Message; }
        try { await SyncCustomersAsync(cfg, auth, token); }
        catch (Exception ex) { customerWarning = ex.Message; }

        lastSyncUtc = DateTime.UtcNow;
        LastSuccessUtc = lastSyncUtc;
        if (reportWarning is null && customerWarning is null)
            LastStatus = $"آخر مزامنة ناجحة: {DateTime.Now:dd/MM/yyyy hh:mm} {(DateTime.Now.Hour < 12 ? "صباحاً" : "مساءاً")}";
        else
            LastStatus = $"تمت المزامنة الأساسية.{(reportWarning is null ? "" : $" التقارير: {reportWarning}.")}{(customerWarning is null ? "" : $" العملاء: {customerWarning}.")}";
'''
if old not in s:
    raise SystemExit("R4 OnlineSync warning block not found")
p.write_text(s.replace(old, new, 1), encoding="utf-8-sig")
print("R4 compile hotfix applied.")
