import Combine
import Foundation
import SwiftUI

enum DashboardState: Equatable {
    case stopped
    case starting
    case running
    case failed

    var title: String {
        switch self {
        case .stopped: "Stopped"
        case .starting: "Starting"
        case .running: "Running"
        case .failed: "Needs Attention"
        }
    }

    var systemImage: String {
        switch self {
        case .stopped: "power"
        case .starting: "arrow.triangle.2.circlepath"
        case .running: "checkmark.circle.fill"
        case .failed: "exclamationmark.triangle.fill"
        }
    }

    var color: Color {
        switch self {
        case .stopped: Color.secondary
        case .starting: Color.accentColor
        case .running: Color.green
        case .failed: Color.orange
        }
    }
}

final class DashboardProcess: ObservableObject {
    @Published private(set) var state: DashboardState = .stopped
    @Published private(set) var statusMessage = "Ready."
    @Published private(set) var url: URL?
    @Published private(set) var port: Int?
    @Published private(set) var logLines: [String] = []

    private let host = "127.0.0.1"
    private var process: Process?
    private var stdoutPipe: Pipe?
    private var stderrPipe: Pipe?
    private var readinessTask: Task<Void, Never>?
    private var isStopping = false

    var isRunning: Bool {
        state == .running || state == .starting
    }

    func start() {
        guard process == nil else { return }

        isStopping = false
        state = .starting
        statusMessage = "Starting the local Iterativ dashboard..."
        url = nil
        logLines.removeAll(keepingCapacity: true)

        let selectedPort = PortFinder.firstAvailable(in: 9119...9149)
        guard let selectedPort else {
            fail("No available loopback port found in 9119...9149.")
            return
        }
        port = selectedPort

        let command = IterativCommand.resolve()
        let dashboardURL = URL(string: "http://\(host):\(selectedPort)")!
        let proc = Process()
        proc.currentDirectoryURL = command.workingDirectory
        proc.executableURL = command.executableURL
        proc.arguments = command.arguments + [
            "dashboard",
            "--host", host,
            "--port", String(selectedPort),
            "--no-open",
            "--tui"
        ]

        var environment = ProcessInfo.processInfo.environment
        environment["ITERATIV_DASHBOARD_TUI"] = "1"
        environment["PYTHONUNBUFFERED"] = "1"
        environment["PATH"] = Self.runtimePath(from: environment["PATH"])
        if let root = command.workingDirectory?.path {
            environment["ITERATIV_REPO_ROOT"] = root
        }
        proc.environment = environment

        let out = Pipe()
        let err = Pipe()
        proc.standardOutput = out
        proc.standardError = err
        stdoutPipe = out
        stderrPipe = err

        captureOutput(from: out, prefix: "")
        captureOutput(from: err, prefix: "")

        proc.terminationHandler = { [weak self] process in
            DispatchQueue.main.async {
                guard let self else { return }
                self.process = nil
                self.readinessTask?.cancel()
                self.clearPipes()

                if self.isStopping {
                    self.state = .stopped
                    self.statusMessage = "Stopped."
                    self.url = nil
                    return
                }

                if self.state != .running {
                    self.fail("Iterativ exited with status \(process.terminationStatus).")
                } else {
                    self.state = .stopped
                    self.statusMessage = "Iterativ stopped."
                    self.url = nil
                }
            }
        }

        do {
            try proc.run()
            process = proc
            waitUntilReady(at: dashboardURL)
        } catch {
            fail("Could not launch Iterativ: \(error.localizedDescription)")
        }
    }

    func stop() {
        readinessTask?.cancel()
        readinessTask = nil
        url = nil

        guard let process else {
            state = .stopped
            statusMessage = "Stopped."
            return
        }

        isStopping = true
        statusMessage = "Stopping Iterativ..."
        process.terminate()

        Task.detached { [weak process] in
            try? await Task.sleep(nanoseconds: 2_000_000_000)
            if let process, process.isRunning {
                process.interrupt()
            }
        }
    }

    private func waitUntilReady(at dashboardURL: URL) {
        readinessTask?.cancel()
        readinessTask = Task { [weak self] in
            guard let self else { return }

            let statusURL = dashboardURL.appending(path: "api/status")
            for attempt in 0..<240 {
                if Task.isCancelled { return }

                if await self.probe(statusURL) {
                    await MainActor.run {
                        self.state = .running
                        self.statusMessage = "Connected to local Iterativ."
                        self.url = dashboardURL
                    }
                    return
                }

                if attempt == 20 {
                    await MainActor.run {
                        self.statusMessage = "Iterativ is still starting. First launch may build web assets."
                    }
                }

                try? await Task.sleep(nanoseconds: 500_000_000)
            }

            await MainActor.run {
                self.fail("Timed out waiting for Iterativ at \(dashboardURL.absoluteString).")
            }
        }
    }

    private func probe(_ url: URL) async -> Bool {
        var request = URLRequest(url: url)
        request.timeoutInterval = 1.0

        do {
            let (_, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse else { return false }
            return (200..<500).contains(http.statusCode)
        } catch {
            return false
        }
    }

    private func captureOutput(from pipe: Pipe, prefix: String) {
        pipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            guard !data.isEmpty, let text = String(data: data, encoding: .utf8) else { return }
            let lines = text
                .split(whereSeparator: \.isNewline)
                .map { prefix + String($0) }
            DispatchQueue.main.async {
                self?.appendLogLines(lines)
            }
        }
    }

    private func appendLogLines(_ lines: [String]) {
        guard !lines.isEmpty else { return }
        logLines.append(contentsOf: lines)
        if logLines.count > 600 {
            logLines.removeFirst(logLines.count - 600)
        }
    }

    private func fail(_ message: String) {
        readinessTask?.cancel()
        readinessTask = nil
        process = nil
        clearPipes()
        state = .failed
        statusMessage = message
        url = nil
    }

    private func clearPipes() {
        stdoutPipe?.fileHandleForReading.readabilityHandler = nil
        stderrPipe?.fileHandleForReading.readabilityHandler = nil
        stdoutPipe = nil
        stderrPipe = nil
    }

    private static func runtimePath(from inheritedPath: String?) -> String {
        let common = [
            "/opt/homebrew/bin",
            "/opt/homebrew/sbin",
            "/usr/local/bin",
            "/usr/local/sbin",
            "/usr/bin",
            "/bin",
            "/usr/sbin",
            "/sbin"
        ]

        var seen = Set<String>()
        let inherited = inheritedPath?
            .split(separator: ":")
            .map(String.init) ?? []

        return (common + inherited)
            .filter { seen.insert($0).inserted }
            .joined(separator: ":")
    }
}
