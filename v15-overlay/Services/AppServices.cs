using SweetsPOS.Data;

namespace SweetsPOS.Services;

public sealed class AppServices
{
    public DatabaseService Database { get; } = new();
    public AppSession Session { get; } = new();
    public AuthService Auth { get; }
    public AuditService Audit { get; }
    public SettingsService Settings { get; }
    public CatalogService Catalog { get; }
    public ShiftService Shifts { get; }
    public SaleService Sales { get; }
    public ReportService Reports { get; }
    public BackupService Backups { get; }
    public ReceiptService Receipts { get; }
    public UserService Users { get; }
    public OnlineSyncService Online { get; }

    public AppServices()
    {
        Audit = new AuditService(Database, Session);
        Settings = new SettingsService(Database, Audit);
        Auth = new AuthService(Database, Session, Audit);
        Catalog = new CatalogService(Database, Audit);
        Shifts = new ShiftService(Database, Session, Audit);
        Sales = new SaleService(Database, Session, Settings, Audit);
        Reports = new ReportService(Database);
        Backups = new BackupService(Database, Audit);
        Receipts = new ReceiptService(Settings);
        Users = new UserService(Database, Audit);
        Online = new OnlineSyncService(Database, Settings, Reports, Audit);
    }
}
