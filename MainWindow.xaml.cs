using Microsoft.UI.Xaml;
using SweetsPOS.Pages;

namespace SweetsPOS;

public sealed partial class MainWindow : Window
{
    public MainWindow()
    {
        App.WriteStartupLog("MainWindow: before InitializeComponent");
        InitializeComponent();
        App.WriteStartupLog("MainWindow: after InitializeComponent");

        Title = "Sweets POS";

        App.WriteStartupLog("MainWindow: before LoginPage navigation");
        RootFrame.Navigate(typeof(LoginPage));
        App.WriteStartupLog("MainWindow: after LoginPage navigation");
    }

    public void ShowShell() => RootFrame.Navigate(typeof(ShellPage));
    public void ShowLogin() => RootFrame.Navigate(typeof(LoginPage));
}
