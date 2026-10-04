using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using SweetsPOS.Core;
using System.Text.RegularExpressions;

namespace SweetsPOS.Pages;

public sealed partial class AuditPage : Page
{
    private sealed record AuditRow(string CreatedAtText, string UserDisplayName, string ActionText, string EntityTypeText, string DetailsText);

    public AuditPage()
    {
        InitializeComponent();
        Loaded += async (_, _) => await RefreshAsync();
    }

    private static string FormatDate(DateTime value)
        => $"{value:dd/MM/yyyy hh:mm} {(value.Hour < 12 ? "صباحاً" : "مساءً")}";

    private static string ActionLabel(string value) => value switch
    {
        "Login" => "تسجيل الدخول",
        "LoginFailed" => "محاولة دخول غير ناجحة",
        "Logout" => "تسجيل الخروج",
        "SettingChanged" => "تعديل إعداد",
        "SettingsChanged" => "تعديل الإعدادات",
        "ShiftOpened" => "فتح وردية",
        "ShiftClosed" => "إغلاق وردية",
        "ShiftForceClosed" => "إغلاق وردية بواسطة الأدمن",
        "ShiftOnlineClosed" => "إغلاق وردية عن بُعد",
        "ShiftReprint" => "إعادة طباعة وردية",
        "ShiftDeleted" => "حذف وردية",
        "ExpenseAdded" => "تسجيل مصروف",
        "SaleCompleted" => "إتمام عملية بيع",
        "RefundCreated" => "تنفيذ مرتجع",
        "SaleVoided" => "إلغاء فاتورة",
        "ReceiptReprinted" => "إعادة طباعة فاتورة",
        "ReportPrinted" => "طباعة تقرير",
        "OrderHeld" => "تعليق طلب",
        "HeldOrderResumed" => "استكمال طلب معلق",
        "ProductCreated" => "إضافة صنف",
        "ProductUpdated" => "تعديل صنف",
        "ProductDeleted" => "حذف صنف",
        "CategoryCreated" => "إضافة قسم",
        "CategoryUpdated" => "تعديل قسم",
        "CategoryDeleted" => "حذف قسم",
        "StockAdjusted" => "تعديل المخزون",
        "UserCreated" => "إضافة مستخدم",
        "UserUpdated" => "تعديل مستخدم",
        "BackupCreated" => "إنشاء نسخة احتياطية",
        "BackupRestored" => "استرجاع نسخة احتياطية",
        "OnlineUpdatesApplied" => "تطبيق تحديثات سحابية",
        "ApprovalGranted" => "موافقة مشرف",
        _ => value
    };

    private static string EntityLabel(string value) => value switch
    {
        "User" => "مستخدم",
        "Setting" => "إعدادات",
        "Shift" => "وردية",
        "Expense" => "مصروف",
        "Sale" => "فاتورة",
        "Report" => "تقرير",
        "HeldOrder" => "طلب معلق",
        "Product" => "صنف",
        "Category" => "قسم",
        "Database" => "نسخة احتياطية",
        "Online" => "إدارة سحابية",
        "Permission" => "صلاحية",
        _ => value
    };

    private static string DetailsLabel(AuditLog row)
    {
        var value = row.Details ?? "";
        if (value == "Successful login") return "تم تسجيل الدخول بنجاح";
        if (value == "Invalid PIN") return "الرقم السري غير صحيح";
        if (value == "User logged out") return "تم تسجيل الخروج";

        var m = Regex.Match(value, @"^Updated (\d+) settings$");
        if (m.Success) return $"تم تحديث {m.Groups[1].Value} إعدادات";

        m = Regex.Match(value, @"^Reprinted closed shift #(\d+)$");
        if (m.Success) return $"تمت إعادة طباعة الوردية رقم {m.Groups[1].Value}";

        m = Regex.Match(value, @"^Opening cash ([\d.]+)$");
        if (m.Success) return $"النقدية الافتتاحية: {m.Groups[1].Value}";

        m = Regex.Match(value, @"^Expected ([\d.-]+); Actual ([\d.-]+); Difference ([\d.-]+)$");
        if (m.Success) return $"المتوقع {m.Groups[1].Value} | الفعلي {m.Groups[2].Value} | الفرق {m.Groups[3].Value}";

        m = Regex.Match(value, @"^Deleted empty shift #(\d+); remaining shifts renumbered by admin (.+)\.$");
        if (m.Success) return $"تم حذف الوردية الفارغة رقم {m.Groups[1].Value} وإعادة ترتيب أرقام الورديات بواسطة {m.Groups[2].Value}";

        return value
            .Replace("Invoice #", "فاتورة رقم ")
            .Replace("Shift #", "وردية رقم ")
            .Replace("Shift ", "وردية ")
            .Replace("Total ", "الإجمالي ")
            .Replace("Items ", "عدد الأصناف ")
            .Replace("Refund ", "قيمة المرتجع ")
            .Replace("Owner ", "المسؤول ")
            .Replace("Expected ", "المتوقع ")
            .Replace("Actual ", "الفعلي ")
            .Replace("Difference ", "الفرق ")
            .Replace("Applied ", "تم تطبيق ")
            .Replace("online updates", "تحديثات سحابية")
            .Replace("Delta ", "التغيير ")
            .Replace("New ", "الرصيد الجديد ");
    }

    private async Task RefreshAsync()
    {
        var rows = await App.Services.Audit.GetRecentAsync();
        List.ItemsSource = rows.Select(x => new AuditRow(
            FormatDate(x.CreatedAt),
            x.UserDisplayName == "System" ? "النظام" : x.UserDisplayName,
            ActionLabel(x.Action),
            EntityLabel(x.EntityType),
            DetailsLabel(x))).ToList();
    }

    private async void Refresh_Click(object sender, RoutedEventArgs e) => await RefreshAsync();
}
