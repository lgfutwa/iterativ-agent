// swift-tools-version: 5.9

import PackageDescription

let package = Package(
    name: "HermesMac",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(name: "HermesMac", targets: ["HermesMac"])
    ],
    targets: [
        .executableTarget(
            name: "HermesMac",
            path: "Sources/HermesMac"
        )
    ]
)
