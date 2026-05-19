import SwiftUI

@main
struct HermesMacApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    @StateObject private var dashboard = DashboardProcess()
    @StateObject private var webViewStore = WebViewStore()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(dashboard)
                .environmentObject(webViewStore)
                .frame(minWidth: 980, minHeight: 680)
                .onAppear {
                    appDelegate.dashboard = dashboard
                    dashboard.start()
                }
        }
        .windowStyle(.titleBar)
        .commands {
            CommandGroup(after: .appInfo) {
                Button("Reload Dashboard") {
                    webViewStore.reload()
                }
                .keyboardShortcut("r", modifiers: [.command])
                .disabled(dashboard.url == nil)

                Button(dashboard.isRunning ? "Stop Hermes" : "Start Hermes") {
                    dashboard.isRunning ? dashboard.stop() : dashboard.start()
                }
                .keyboardShortcut("s", modifiers: [.command, .shift])

                if let url = dashboard.url {
                    Button("Open in Browser") {
                        NSWorkspace.shared.open(url)
                    }
                    .keyboardShortcut("o", modifiers: [.command, .shift])
                }
            }
        }
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    weak var dashboard: DashboardProcess?

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        true
    }

    func applicationWillTerminate(_ notification: Notification) {
        dashboard?.stop()
    }
}
