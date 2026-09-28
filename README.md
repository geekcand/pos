# Sweets POS — Windows Cashier System

نظام كاشير Windows لمحل حلويات، مصمم للعمل **Offline-First** بقاعدة بيانات SQLite محلية، مع فصل واضح بين صلاحيات الكاشير والمشرف والأدمن.

## الوظائف المنفذة في V1

- Login بالـ PIN مع أدوار Cashier / Supervisor / Admin.
- POS سريع: تصنيفات، بحث، Barcode scanner، بيع بالقطعة/الكيلو/الجرام/العلبة/الباكت.
- Cart كامل: زيادة/تقليل/حذف، خصم مع سبب، وموافقة مشرف للخصم الأعلى من الحد.
- Hold / Resume للطلبات المعلقة.
- طرق دفع Cash / Card / InstaPay / Wallet مع Split Payment وحساب الباقي للكاش.
- Thermal receipt وطباعة RAW على طابعة Windows المحددة. لو الطابعة غير متاحة يتم حفظ Receipt محليًا بدل تعطيل البيع.
- Shifts: Opening cash، إغلاق الوردية، Expected vs Actual، Difference، وطباعة Closing Report.
- Expenses مرتبطة بالوردية الحالية.
- Refund جزئي أو كامل مع إعادة المخزون تلقائيًا. المرتجع يُحسب على الوردية التي تم فيها تنفيذ المرتجع.
- Void مسموح فقط لفاتورة من الوردية الحالية؛ الفواتير القديمة تستخدم Refund للحفاظ على إقفالات الأيام السابقة.
- Products / Categories / Barcode / SKU / Images / Cost / Price / Basic inventory / Low-stock threshold.
- Users & Roles وإمكانية تغيير PIN وتعطيل المستخدم.
- Dashboard وتقارير فترة زمنية وPayment Mix وTop Products وNet Sales وEstimated Gross Profit وCSV export.
- Audit Log للعمليات الحساسة.
- Backup / Restore مع integrity check وSafety backup قبل الاسترجاع.
- قاعدة محاسبية: المبيعات لا يتم حذفها من قاعدة البيانات؛ تستخدم Void أو Refund.

## أول تشغيل

بيانات تجريبية افتراضية:

- Admin: `admin` — PIN: `1234`
- Cashier: `cashier` — PIN: `0000`

**غيّر الـ PIN الافتراضي من Users فور أول تشغيل فعلي.**

يوجد أيضًا Sample categories/products لمعاينة البرنامج ويمكن تعديلها من حساب Admin.

## مكان البيانات

البرنامج يحفظ البيانات في:

`%LOCALAPPDATA%\SweetsPOS\sweetspos.db`

والنسخ الاحتياطية في:

`%LOCALAPPDATA%\SweetsPOS\Backups`

والفواتير التي لم تتم طباعتها مباشرة في:

`%LOCALAPPDATA%\SweetsPOS\Receipts`

## المتطلبات للبناء

- Windows 10 2004 أو أحدث / Windows 11.
- .NET SDK 10.0.401.
- المشروع يستخدم Windows App SDK 2.5.1 (Stable) وEF Core SQLite 10.0.12.

المشروع Unpackaged وSelf-contained في البناء النهائي، لذلك ملفات Runtime تدخل مع التطبيق.

## Build

افتح PowerShell داخل مجلد المشروع وشغّل:

```powershell
./build.ps1
```

النسخة القابلة للتشغيل ستظهر في:

`artifacts\final-win-x64`

لو Inno Setup 6 مثبت، السكربت سيبني أيضًا:

`artifacts\installer-fixed\SweetsPOS-Setup-x64.exe`

## GitHub Actions

الملف `.github/workflows/windows-build.yml` يبني نسخة Windows x64 ويرفع:

1. Runnable app folder.
2. Setup EXE بواسطة Inno Setup.

## الطابعة الحرارية

من Settings اكتب **اسم الطابعة كما يظهر في Windows**. يمكن اختيار Encoding مثل UTF-8 أو Windows-1256/IBM864/IBM720 حسب دعم الطابعة للعربي.

لو اسم الطابعة فارغ أو حصل خطأ في الطباعة، عملية البيع لا تفشل؛ يتم حفظ الفاتورة كملف نصي محليًا.

## Barcode Scanner

أي Scanner يعمل كـ Keyboard Wedge سيعمل مباشرة: ضع المؤشر في Barcode ثم Scan + Enter.

## ملاحظات المخزون والربح

تكلفة الصنف يتم نسخها داخل SaleItem وقت البيع، وبالتالي تغيير Cost لاحقًا لا يغيّر تكلفة المبيعات القديمة. Estimated Gross Profit يعتمد على تكلفة وقت البيع والكميات غير المرتجعة ويستبعد تأثير الضريبة من الإيراد المستخدم في حساب الهامش.

## حدود V1 المقصودة

- لا يوجد Cloud Sync أو Multi-branch في V1؛ التصميم المحلي قابل للتوسعة لاحقًا.
- لا يوجد Recipe/BOM لاستهلاك مكونات التصنيع؛ المخزون الحالي على مستوى المنتج النهائي.
- لا يوجد ربط مباشر بميزان إلكتروني؛ البيع الوزني يدعم إدخال الوزن يدويًا.
- الطباعة العربية RAW تعتمد على Code Page التي تدعمها الطابعة نفسها.

هذه العناصر متروكة لـ V2 حتى لا نربط الكاشير الأساسي بتعقيدات تشغيلية قبل تجربة النسخة داخل المحل.


## Deployment 1.0.3
See INSTALL-AR.txt. Setup includes .NET, Windows App SDK, app-local Visual C++ and resources.pri. Installs for the current user with desktop and Windows sign-in shortcuts.

