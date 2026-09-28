using Microsoft.UI.Xaml;
using SweetsPOS.Services;
using System.Text;

namespace SweetsPOS;

public partial class App : Application
{
    public static MainWindow MainWindow { get; private set; } = null!;
    public static AppServices Services { get; private set; } = null!;

    private static readonly string StartupLogPath =
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                     "SweetsPOS", "startup.log");

    public App()
    {
        WriteStartupLog("App: constructor started");
        InitializeComponent();
        WriteStartupLog("App: InitializeComponent completed");

        UnhandledException += (_, e) =>
        {
            WriteStartupLog("WinUI UnhandledException: " + e.Exception);
        };

        AppDomain.CurrentDomain.UnhandledException += (_, e) =>
        {
            WriteStartupLog("AppDomain UnhandledException: " + e.ExceptionObject);
        };

        TaskScheduler.UnobservedTaskException += (_, e) =>
        {
            WriteStartupLog("UnobservedTaskException: " + e.Exception);
        };
    }

    public static void WriteStartupLog(string message)
    {
        try
        {
            var dir = Path.GetDirectoryName(StartupLogPath)!;
            Directory.CreateDirectory(dir);
            File.AppendAllText(
                StartupLogPath,
                $"{DateTime.Now:yyyy-MM-dd HH:mm:ss.fff} | {message}{Environment.NewLine}",
                Encoding.UTF8);
        }
        catch
        {
            // Startup diagnostics must never prevent app launch.
        }
    }

    protected override async void OnLaunched(LaunchActivatedEventArgs args)
    {
        try
        {
            WriteStartupLog("OnLaunched: started");

            Services = new AppServices();
            WriteStartupLog("OnLaunched: services created");

            await Services.Database.InitializeAsync();
            WriteStartupLog("OnLaunched: database initialized");

            WriteStartupLog("OnLaunched: before MainWindow creation");
            MainWindow = new MainWindow();
            WriteStartupLog("OnLaunched: MainWindow created");

            MainWindow.Activate();
            WriteStartupLog("OnLaunched: MainWindow activated");
        }
        catch (Exception ex)
        {
            WriteStartupLog("OnLaunched managed exception: " + ex);
            throw;
        }
    }
}
