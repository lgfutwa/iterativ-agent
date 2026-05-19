import Foundation

struct HermesCommand {
    let executableURL: URL
    let arguments: [String]
    let workingDirectory: URL?

    static func resolve() -> HermesCommand {
        if let explicitRoot = ProcessInfo.processInfo.environment["HERMES_REPO_ROOT"],
           let root = repositoryRoot(startingAt: URL(fileURLWithPath: explicitRoot)) {
            return sourceCheckoutCommand(root: root)
        }

        if let root = repositoryRoot(startingAt: URL(fileURLWithPath: FileManager.default.currentDirectoryPath)) {
            return sourceCheckoutCommand(root: root)
        }

        if let bundleRoot = bundleSearchRoot(),
           let root = repositoryRoot(startingAt: bundleRoot) {
            return sourceCheckoutCommand(root: root)
        }

        return HermesCommand(
            executableURL: URL(fileURLWithPath: "/usr/bin/env"),
            arguments: ["hermes"],
            workingDirectory: nil
        )
    }

    private static func sourceCheckoutCommand(root: URL) -> HermesCommand {
        let launcher = root.appending(path: "hermes")
        if let python = checkoutPython(root: root) {
            return HermesCommand(
                executableURL: python,
                arguments: [launcher.path],
                workingDirectory: root
            )
        }

        return HermesCommand(
            executableURL: launcher,
            arguments: [],
            workingDirectory: root
        )
    }

    private static func checkoutPython(root: URL) -> URL? {
        let candidates = [
            root.appending(path: ".venv/bin/python3"),
            root.appending(path: ".venv/bin/python"),
            root.appending(path: "venv/bin/python3"),
            root.appending(path: "venv/bin/python")
        ]

        return candidates.first { FileManager.default.isExecutableFile(atPath: $0.path) }
    }

    private static func bundleSearchRoot() -> URL? {
        return Bundle.main.bundleURL
    }

    private static func repositoryRoot(startingAt start: URL) -> URL? {
        var candidate = start.standardizedFileURL
        let fileManager = FileManager.default

        if !isDirectory(candidate) {
            candidate.deleteLastPathComponent()
        }

        while true {
            let launcher = candidate.appending(path: "hermes").path
            let cli = candidate.appending(path: "hermes_cli/main.py").path
            if fileManager.isExecutableFile(atPath: launcher),
               fileManager.fileExists(atPath: cli) {
                return candidate
            }

            let parent = candidate.deletingLastPathComponent()
            if parent.path == candidate.path {
                return nil
            }
            candidate = parent
        }
    }

    private static func isDirectory(_ url: URL) -> Bool {
        var isDir: ObjCBool = false
        return FileManager.default.fileExists(atPath: url.path, isDirectory: &isDir) && isDir.boolValue
    }
}
