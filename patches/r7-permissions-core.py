from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()

def read(p): return (root/p).read_text(encoding="utf-8-sig")
def write(p,s): (root/p).write_text(s,encoding="utf-8-sig")

# Roles + full permission catalog
p="Core/Enums.cs"; s=read(p)
s=s.replace("public enum UserRole { Cashier = 1, Supervisor = 2, Admin = 3 }","public enum UserRole { Cashier = 1, Supervisor = 2, Admin = 3, Administrator = 4 }")
start=s.index("public enum Permission")
s=s[:start]+'''public enum Permission
{
    AccessCashier, AccessTakeaway, AccessDelivery, AccessDining, AccessCustomers, AccessShifts,
    AccessAdminDashboard, AccessCategories, AccessProducts, AccessPaymentMethods, AccessUsers,
    AccessReports, AccessExpenses, AccessRefunds, AccessShiftAdmin, AccessReceiptDesigner,
    AccessAudit, AccessOnline, AccessSettings,

    Sell, HoldOrder, OpenShift, CloseShift, AdminCloseShift, ReprintShift, AddExpense,
    DiscountBasic, DiscountOverride, Refund, VoidSale,
    CreateDeliveryOrder, EditDeliveryOrder, SendKitchen, CancelRestaurantOrder, CancelDeliveryOrder,
    ReturnDeliveryOrder, DispatchDelivery, SettleDelivery, ManageCustomers, ManageDiningAreas,
    ManageCatalog, DeleteCatalog, ManageUsers, ViewReports, ViewAudit, ManageSettings,
    ManagePaymentMethods, DeleteDiningTable, DeleteShift, BackupRestore
}
'''
write(p,s)

write("Core/RolePermissions.cs",'''namespace SweetsPOS.Core;

public sealed record PermissionDescriptor(Permission Permission, string Group, string Label, bool Sensitive = false, bool IsModule = false);

public static class RolePermissions
{
    private static readonly HashSet<Permission> All = Enum.GetValues<Permission>().ToHashSet();

    private static readonly IReadOnlyDictionary<UserRole, HashSet<Permission>> Map =
        new Dictionary<UserRole, HashSet<Permission>>
        {
            [UserRole.Cashier] = new()
            {
                Permission.AccessCashier, Permission.AccessTakeaway, Permission.AccessShifts,
                Permission.Sell, Permission.HoldOrder, Permission.OpenShift, Permission.CloseShift,
                Permission.DiscountBasic
            },
            [UserRole.Supervisor] = new()
            {
                Permission.AccessCashier, Permission.AccessTakeaway, Permission.AccessDelivery, Permission.AccessDining,
                Permission.AccessCustomers, Permission.AccessShifts, Permission.AccessExpenses, Permission.AccessRefunds,
                Permission.Sell, Permission.HoldOrder, Permission.OpenShift, Permission.CloseShift, Permission.AddExpense,
                Permission.DiscountBasic, Permission.DiscountOverride, Permission.Refund, Permission.VoidSale,
                Permission.CreateDeliveryOrder, Permission.EditDeliveryOrder, Permission.SendKitchen,
                Permission.CancelRestaurantOrder, Permission.CancelDeliveryOrder, Permission.ReturnDeliveryOrder,
                Permission.DispatchDelivery, Permission.SettleDelivery, Permission.ManageCustomers
            },
            [UserRole.Admin] = All.ToHashSet(),
            [UserRole.Administrator] = All.ToHashSet()
        };

    public static IReadOnlyList<PermissionDescriptor> Definitions { get; } =
    [
        new(Permission.AccessCashier, "الوصول والظهور", "إظهار شاشة الكاشير", IsModule: true),
        new(Permission.AccessTakeaway, "الوصول والظهور", "إظهار تيك أواي", IsModule: true),
        new(Permission.AccessDelivery, "الوصول والظهور", "إظهار الدليفري", IsModule: true),
        new(Permission.AccessDining, "الوصول والظهور", "إظهار الصالة والطاولات", IsModule: true),
        new(Permission.AccessCustomers, "الوصول والظهور", "إظهار العملاء", IsModule: true),
        new(Permission.AccessShifts, "الوصول والظهور", "إظهار الورديات", IsModule: true),

        new(Permission.AccessAdminDashboard, "لوحة الإدارة", "إظهار الصفحة الرئيسية للوحة الإدارة", IsModule: true),
        new(Permission.AccessCategories, "لوحة الإدارة", "إظهار الأقسام", IsModule: true),
        new(Permission.AccessProducts, "لوحة الإدارة", "إظهار الأصناف", IsModule: true),
        new(Permission.AccessPaymentMethods, "لوحة الإدارة", "إظهار طرق الدفع", IsModule: true),
        new(Permission.AccessUsers, "لوحة الإدارة", "إظهار المستخدمين", IsModule: true),
        new(Permission.AccessReports, "لوحة الإدارة", "إظهار التقارير", IsModule: true),
        new(Permission.AccessExpenses, "لوحة الإدارة", "إظهار المصروفات", IsModule: true),
        new(Permission.AccessRefunds, "لوحة الإدارة", "إظهار المرتجعات", IsModule: true),
        new(Permission.AccessShiftAdmin, "لوحة الإدارة", "إظهار إدارة الورديات", IsModule: true),
        new(Permission.AccessReceiptDesigner, "لوحة الإدارة", "إظهار تصميم الفاتورة", IsModule: true),
        new(Permission.AccessAudit, "لوحة الإدارة", "إظهار سجل التعديلات", IsModule: true),
        new(Permission.AccessOnline, "لوحة الإدارة", "إظهار الأونلاين والمزامنة", IsModule: true),
        new(Permission.AccessSettings, "لوحة الإدارة", "إظهار الإعدادات", IsModule: true),

        new(Permission.Sell, "الكاشير", "إتمام البيع"),
        new(Permission.HoldOrder, "الكاشير", "تعليق واستكمال الطلبات"),
        new(Permission.DiscountBasic, "الكاشير", "إضافة خصم عادي"),
        new(Permission.DiscountOverride, "الكاشير", "اعتماد خصم أعلى من الحد", true),

        new(Permission.OpenShift, "الورديات", "فتح وردية"),
        new(Permission.CloseShift, "الورديات", "إغلاق ورديته"),
        new(Permission.AdminCloseShift, "الورديات", "إغلاق وردية مستخدم آخر", true),
        new(Permission.ReprintShift, "الورديات", "إعادة طباعة تقرير وردية", true),
        new(Permission.DeleteShift, "الورديات", "حذف وردية فارغة", true),
        new(Permission.AddExpense, "الورديات", "تسجيل مصروف"),

        new(Permission.Refund, "المرتجعات", "استرجاع صنف / فاتورة", true),
        new(Permission.VoidSale, "المرتجعات", "إلغاء فاتورة", true),

        new(Permission.CreateDeliveryOrder, "الدليفري", "إنشاء طلب دليفري"),
        new(Permission.EditDeliveryOrder, "الدليفري", "إضافة وتعديل أصناف طلب الدليفري"),
        new(Permission.SendKitchen, "المطعم والدليفري", "إرسال الطلب للمطبخ"),
        new(Permission.CancelRestaurantOrder, "المطعم والدليفري", "إلغاء طلب صالة", true),
        new(Permission.CancelDeliveryOrder, "المطعم والدليفري", "إلغاء طلب دليفري", true),
        new(Permission.ReturnDeliveryOrder, "المطعم والدليفري", "تسجيل دليفري مرتجع / لم يتم التسليم", true),
        new(Permission.DispatchDelivery, "المطعم والدليفري", "تحميل طلب على طيار"),
        new(Permission.SettleDelivery, "المطعم والدليفري", "تسوية الطيار واستلام الكاش", true),
        new(Permission.ManageCustomers, "المطعم والدليفري", "إدارة بيانات العملاء"),
        new(Permission.ManageDiningAreas, "المطعم والدليفري", "إضافة وتعديل الصالات والطاولات"),
        new(Permission.DeleteDiningTable, "المطعم والدليفري", "حذف صالة / تقليل عدد الطاولات", true),

        new(Permission.ManageCatalog, "الإدارة", "إضافة وتعديل الأقسام والأصناف"),
        new(Permission.DeleteCatalog, "الإدارة", "حذف قسم / صنف", true),
        new(Permission.ManagePaymentMethods, "الإدارة", "تعديل طرق الدفع"),
        new(Permission.ManageUsers, "الإدارة", "إدارة المستخدمين والصلاحيات", true),
        new(Permission.ViewReports, "الإدارة", "عرض بيانات التقارير"),
        new(Permission.ViewAudit, "الإدارة", "عرض سجل التعديلات"),
        new(Permission.ManageSettings, "الإدارة", "تعديل الإعدادات والطابعات"),
        new(Permission.BackupRestore, "الإدارة", "النسخ الاحتياطي والاسترجاع", true)
    ];

    public static bool Has(UserRole role, Permission permission)
        => role == UserRole.Administrator || (Map.TryGetValue(role, out var set) && set.Contains(permission));

    public static bool Has(User user, Permission permission)
    {
        if (user.Role == UserRole.Administrator) return true;
        if (string.IsNullOrWhiteSpace(user.PermissionsCsv)) return Has(user.Role, permission);
        return Parse(user.PermissionsCsv).Contains(permission);
    }

    public static HashSet<Permission> Effective(User user)
        => user.Role == UserRole.Administrator ? All.ToHashSet()
         : string.IsNullOrWhiteSpace(user.PermissionsCsv) ? Defaults(user.Role)
         : Parse(user.PermissionsCsv);

    public static HashSet<Permission> Defaults(UserRole role)
        => role == UserRole.Administrator ? All.ToHashSet()
         : Map.TryGetValue(role, out var set) ? set.ToHashSet() : [];

    public static HashSet<Permission> Parse(string? csv)
    {
        var result = new HashSet<Permission>();
        if (string.IsNullOrWhiteSpace(csv)) return result;
        foreach (var part in csv.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
            if (Enum.TryParse<Permission>(part, true, out var p)) result.Add(p);
        return result;
    }

    public static string Serialize(IEnumerable<Permission> permissions)
        => string.Join(",", permissions.Distinct().OrderBy(x => (int)x));

    public static bool IsReservedAdministrator(User user)
        => user.Role == UserRole.Administrator || user.Username.Equals("administrator", StringComparison.OrdinalIgnoreCase);
}
''')

# User labels
p="Core/Entities.cs"; s=read(p)
s=s.replace('public string RoleLabel => Role switch { UserRole.Admin => "أدمن", UserRole.Supervisor => "مشرف", _ => "كاشير" };','public string RoleLabel => Role switch { UserRole.Administrator => "Administrator", UserRole.Admin => "أدمن", UserRole.Supervisor => "مشرف", _ => "كاشير" };')
s=s.replace('public string PermissionsLabel => string.IsNullOrWhiteSpace(PermissionsCsv) ? "افتراضية للدور" : $"{RolePermissions.Parse(PermissionsCsv).Count} صلاحية";','public string PermissionsLabel => Role == UserRole.Administrator ? "كل الصلاحيات" : string.IsNullOrWhiteSpace(PermissionsCsv) ? "افتراضية للدور" : $"{RolePermissions.Parse(PermissionsCsv).Count} صلاحية";')
write(p,s)

# Administrator account + R5->R7 permission migration
p="Data/DatabaseService.cs"; s=read(p)
s=s.replace('''            db.Users.AddRange(
                new User { Username = "admin", DisplayName = "أدمن", Role = UserRole.Admin, PinHash = PinHasher.Hash("1234") },
                new User { Username = "cashier", DisplayName = "كاشير", Role = UserRole.Cashier, PinHash = PinHasher.Hash("0000") }
            );''','''            db.Users.AddRange(
                new User { Username = "administrator", DisplayName = "Administrator", Role = UserRole.Administrator, PinHash = PinHasher.Hash("1234") },
                new User { Username = "admin", DisplayName = "أدمن", Role = UserRole.Admin, PinHash = PinHasher.Hash("1234") },
                new User { Username = "cashier", DisplayName = "كاشير", Role = UserRole.Cashier, PinHash = PinHasher.Hash("0000") }
            );''')
anchor='''        var oldAdmin = await db.Users.FirstOrDefaultAsync(x => x.Username == "admin" && x.DisplayName == "Administrator");'''
insert='''        var administrator = await db.Users.FirstOrDefaultAsync(x => x.Username.ToLower() == "administrator");
        if (administrator is null)
        {
            var sourceAdmin = await db.Users.Where(x => x.Role == UserRole.Admin).OrderBy(x => x.Id).FirstOrDefaultAsync();
            administrator = new User
            {
                Username = "administrator", DisplayName = "Administrator", Role = UserRole.Administrator,
                IsActive = true, PermissionsCsv = null,
                PinHash = sourceAdmin?.PinHash ?? PinHasher.Hash("1234"), CreatedAt = DateTime.Now
            };
            db.Users.Add(administrator);
        }
        else
        {
            administrator.Username = "administrator";
            administrator.DisplayName = "Administrator";
            administrator.Role = UserRole.Administrator;
            administrator.IsActive = true;
            administrator.PermissionsCsv = null;
        }

        var legacyPermissionUsers = await db.Users
            .Where(x => x.Role != UserRole.Administrator && x.PermissionsCsv != null && !x.PermissionsCsv.Contains("AccessCashier"))
            .ToListAsync();
        foreach (var user in legacyPermissionUsers)
            user.PermissionsCsv = RolePermissions.Serialize(RolePermissions.Defaults(user.Role));

'''+anchor
if anchor not in s: raise SystemExit("Database migration anchor missing")
s=s.replace(anchor,insert,1)
write(p,s)

# Auth hierarchy
p="Services/AuthService.cs"; s=read(p)
s=s.replace("x.Role == UserRole.Admin || x.Role == UserRole.Supervisor","x.Role == UserRole.Administrator || x.Role == UserRole.Admin || x.Role == UserRole.Supervisor")
write(p,s)

# User service gets current session and enforces hierarchy
p="Services/AppServices.cs"; s=read(p)
s=s.replace("Users = new UserService(Database, Audit);","Users = new UserService(Database, Audit, Session);")
write(p,s)

write("Services/UserService.cs",'''using Microsoft.EntityFrameworkCore;
using SweetsPOS.Core;
using SweetsPOS.Data;

namespace SweetsPOS.Services;

public sealed class UserService(DatabaseService database, AuditService audit, AppSession session)
{
    public async Task<List<User>> GetAllAsync()
    {
        await using var db = database.CreateContext();
        return await db.Users.AsNoTracking().OrderByDescending(x => x.Role).ThenBy(x => x.DisplayName).ToListAsync();
    }

    public async Task<User> SaveAsync(int id, string username, string displayName, UserRole role, bool active, string? newPin, IReadOnlyCollection<Permission>? permissions = null)
    {
        var actor = session.CurrentUser ?? throw new UnauthorizedAccessException("يجب تسجيل الدخول أولاً.");
        if (!RolePermissions.Has(actor, Permission.ManageUsers)) throw new UnauthorizedAccessException("لا توجد صلاحية لإدارة المستخدمين.");
        if (string.IsNullOrWhiteSpace(username) || string.IsNullOrWhiteSpace(displayName)) throw new InvalidOperationException("اسم المستخدم والاسم الظاهر مطلوبان.");

        await using var db = database.CreateContext();
        User row;
        if (id == 0)
        {
            if (actor.Role != UserRole.Administrator && role >= actor.Role) throw new UnauthorizedAccessException("لا يمكنك إنشاء مستخدم بنفس مستواك أو أعلى.");
            if (role == UserRole.Administrator) throw new UnauthorizedAccessException("حساب Administrator محجوز للنظام.");
            if (string.IsNullOrWhiteSpace(newPin)) throw new InvalidOperationException("PIN مطلوب للمستخدم الجديد.");
            var requested = permissions is null ? RolePermissions.Defaults(role) : permissions.ToHashSet();
            if (actor.Role != UserRole.Administrator) requested.IntersectWith(RolePermissions.Effective(actor));
            row = new User { Username=username.Trim(), DisplayName=displayName.Trim(), Role=role, IsActive=active,
                PermissionsCsv=RolePermissions.Serialize(requested), PinHash=PinHasher.Hash(newPin), CreatedAt=DateTime.Now };
            db.Users.Add(row);
        }
        else
        {
            row = await db.Users.FirstAsync(x => x.Id == id);
            var reserved = RolePermissions.IsReservedAdministrator(row);
            if (reserved && actor.Role != UserRole.Administrator) throw new UnauthorizedAccessException("حساب Administrator لا يمكن تعديله من أي حساب آخر.");
            if (!reserved && actor.Role != UserRole.Administrator && row.Role >= actor.Role) throw new UnauthorizedAccessException("لا يمكنك تعديل مستخدم بنفس مستواك أو أعلى.");

            if (reserved)
            {
                row.Username="administrator"; row.DisplayName="Administrator"; row.Role=UserRole.Administrator;
                row.IsActive=true; row.PermissionsCsv=null;
            }
            else
            {
                if (actor.Role != UserRole.Administrator && role >= actor.Role) throw new UnauthorizedAccessException("لا يمكنك رفع المستخدم إلى نفس مستواك أو أعلى.");
                row.Username=username.Trim(); row.DisplayName=displayName.Trim(); row.Role=role; row.IsActive=active;
                var requested = permissions is null ? RolePermissions.Effective(row) : permissions.ToHashSet();
                if (actor.Role != UserRole.Administrator) requested.IntersectWith(RolePermissions.Effective(actor));
                row.PermissionsCsv=RolePermissions.Serialize(requested);
            }
            if (!string.IsNullOrWhiteSpace(newPin)) row.PinHash=PinHasher.Hash(newPin);
        }
        await db.SaveChangesAsync();
        await audit.WriteAsync(id == 0 ? "UserCreated" : "UserUpdated", "User", row.Id.ToString(), $"{row.DisplayName} ({row.Role}) Active={row.IsActive}");
        return row;
    }
}
''')

# Prefer owner account on login
p="Pages/LoginPage.xaml.cs"; s=read(p)
s=s.replace("UserCombo.SelectedItem = users.FirstOrDefault(x => x.Role == UserRole.Admin) ?? users.FirstOrDefault();","UserCombo.SelectedItem = users.FirstOrDefault(x => x.Role == UserRole.Administrator) ?? users.FirstOrDefault(x => x.Role == UserRole.Admin) ?? users.FirstOrDefault();")
write(p,s)

print("R7 permissions core applied")
