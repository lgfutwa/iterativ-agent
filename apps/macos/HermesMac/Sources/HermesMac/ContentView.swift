import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var dashboard: DashboardProcess
    @EnvironmentObject private var webViewStore: WebViewStore
    @State private var showingLogs = false

    var body: some View {
        VStack(spacing: 0) {
            toolbar
            Divider()

            ZStack {
                if let url = dashboard.url, dashboard.state == .running {
                    WebDashboardView(store: webViewStore, url: url)
                } else {
                    LaunchStateView()
                }
            }
        }
        .sheet(isPresented: $showingLogs) {
            LogsView(lines: dashboard.logLines)
        }
    }

    private var toolbar: some View {
        HStack(spacing: 12) {
            StatusDot(state: dashboard.state)
            Text(dashboard.state.title)
                .font(.headline)

            if let port = dashboard.port {
                Text(":\(port)")
                    .font(.callout.monospacedDigit())
                    .foregroundStyle(.secondary)
            }

            Spacer()

            Button {
                showingLogs = true
            } label: {
                Label("Logs", systemImage: "doc.text.magnifyingglass")
            }

            Button {
                webViewStore.reload()
            } label: {
                Label("Reload", systemImage: "arrow.clockwise")
            }
            .disabled(dashboard.url == nil)

            Button {
                if let url = dashboard.url {
                    NSWorkspace.shared.open(url)
                }
            } label: {
                Label("Browser", systemImage: "safari")
            }
            .disabled(dashboard.url == nil)

            Button {
                dashboard.isRunning ? dashboard.stop() : dashboard.start()
            } label: {
                Label(dashboard.isRunning ? "Stop" : "Start",
                      systemImage: dashboard.isRunning ? "stop.fill" : "play.fill")
            }
            .buttonStyle(.borderedProminent)
            .disabled(dashboard.state == .starting)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(.bar)
    }
}

private struct LaunchStateView: View {
    @EnvironmentObject private var dashboard: DashboardProcess

    var body: some View {
        VStack(spacing: 18) {
            Image(systemName: dashboard.state.systemImage)
                .font(.system(size: 48, weight: .medium))
                .symbolRenderingMode(.hierarchical)
                .foregroundStyle(dashboard.state.color)

            Text("Hermes")
                .font(.system(size: 36, weight: .semibold))

            Text(dashboard.statusMessage)
                .font(.callout)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 560)

            if dashboard.state == .failed {
                Button {
                    dashboard.start()
                } label: {
                    Label("Try Again", systemImage: "arrow.clockwise")
                }
                .buttonStyle(.borderedProminent)
            } else if dashboard.state == .stopped {
                Button {
                    dashboard.start()
                } label: {
                    Label("Start Hermes", systemImage: "play.fill")
                }
                .buttonStyle(.borderedProminent)
            }

            if !dashboard.logLines.isEmpty {
                Text(dashboard.logLines.suffix(3).joined(separator: "\n"))
                    .font(.caption.monospaced())
                    .foregroundStyle(.secondary)
                    .lineLimit(5)
                    .textSelection(.enabled)
                    .frame(maxWidth: 680, alignment: .leading)
                    .padding(.top, 8)
            }
        }
        .padding(32)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

private struct StatusDot: View {
    let state: DashboardState

    var body: some View {
        Circle()
            .fill(state.color)
            .frame(width: 10, height: 10)
            .accessibilityLabel(state.title)
    }
}

private struct LogsView: View {
    let lines: [String]
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text("Hermes Logs")
                    .font(.headline)
                Spacer()
                Button("Done") {
                    dismiss()
                }
                .keyboardShortcut(.defaultAction)
            }
            .padding()

            Divider()

            ScrollView {
                Text(lines.isEmpty ? "No output yet." : lines.joined(separator: "\n"))
                    .font(.system(.caption, design: .monospaced))
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .textSelection(.enabled)
                    .padding()
            }
        }
        .frame(width: 720, height: 460)
    }
}
