import SwiftUI

@main
struct IterativIOSApp: App {
    @StateObject private var settings = DashboardSettings()
    @StateObject private var webViewStore = WebViewStore()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(settings)
                .environmentObject(webViewStore)
        }
    }
}
