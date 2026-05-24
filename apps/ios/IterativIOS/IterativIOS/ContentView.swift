import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var settings: DashboardSettings
    @EnvironmentObject private var webViewStore: WebViewStore
    @State private var showingSettings = false

    var body: some View {
        NavigationStack {
            ZStack {
                Color(red: 0.97, green: 0.96, blue: 0.93)
                    .ignoresSafeArea()

                if let url = settings.dashboardURL {
                    DashboardWebView(store: webViewStore, url: url)
                        .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
                        .padding(.horizontal, 12)
                        .padding(.bottom, 12)
                } else {
                    unavailableView
                }
            }
            .navigationTitle("Iterativ")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button {
                        webViewStore.reload()
                    } label: {
                        Label("Reload", systemImage: "arrow.clockwise")
                    }
                    .disabled(settings.dashboardURL == nil)
                }

                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        showingSettings = true
                    } label: {
                        Label("Settings", systemImage: "slider.horizontal.3")
                    }
                }
            }
            .sheet(isPresented: $showingSettings) {
                SettingsView()
                    .environmentObject(settings)
            }
        }
    }

    private var unavailableView: some View {
        VStack(spacing: 18) {
            Image(systemName: "link.badge.plus")
                .font(.system(size: 44, weight: .semibold))
                .foregroundStyle(.secondary)

            Text("Connect to Iterativ")
                .font(.title2.weight(.semibold))

            Text("Set the dashboard URL for a running Iterativ dashboard.")
                .font(.callout)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)

            Button {
                showingSettings = true
            } label: {
                Label("Set Dashboard URL", systemImage: "globe")
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(28)
    }
}

private struct SettingsView: View {
    @EnvironmentObject private var settings: DashboardSettings
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section("Dashboard") {
                    TextField("Dashboard URL", text: $settings.dashboardURLString)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .keyboardType(.URL)

                    HStack {
                        Text("Host")
                        Spacer()
                        Text(settings.displayHost)
                            .foregroundStyle(.secondary)
                    }
                }

                Section {
                    Button("Reset to Simulator Default") {
                        settings.reset()
                    }
                } footer: {
                    Text("Use 127.0.0.1 for the iOS Simulator. Use your Mac's LAN address for a physical iPhone or iPad.")
                }
            }
            .navigationTitle("Iterativ")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}
