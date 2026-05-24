import Foundation

struct IterativCommand {
    let executableURL: URL
    let arguments: [String]
    let workingDirectory: URL?

    static func resolve() -> IterativCommand {
        for key in ["ITERATIV_REPO_ROOT", "HERMES_REPO_ROOT"] {
            if let explicitRoot = ProcessInfo.processInfo.environment[key],
               let root = repositoryRoot(startingAt: URL(fileURLWithPath: explicitRoot)) {
                return sourceCheckoutCommand(root: root)
            }
        }

        if let root = repositoryRoot(startingAt: URL(fileURLWithPath: FileManager.default.currentDirectoryPath)) {
            return sourceCheckoutCommand(root: root)
        }

        if let bundleRoot = bundleSearchRoot(),
           let root = repositoryRoot(startingAt: bundleRoot) {
            return sourceCheckoutCommand(root: root)
        }

        return IterativCommand(
            executableURL: URL(fileURLWithPath: "/usr/bin/env"),
            arguments: ["iterativ"],
            workingDirectory: nil
        )
    }

    private static func sourceCheckoutCommand(root: URL) -> IterativCommand {
        let launcher = root.appending(path: "iterativ")
        if let python = checkoutPython(root: root) {
            return IterativCommand(
                executableURL: python,
                arguments: [launcher.path],
                workingDirectory: root
            )
        }

        return IterativCommand(
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
            let launcher = candidate.appending(path: "iterativ").path
            let cli = candidate.appending(path: "iterativ_cli/main.py").path
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
