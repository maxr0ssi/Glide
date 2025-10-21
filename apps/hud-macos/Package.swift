// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "GlideHUD",
    platforms: [
        .macOS(.v15)
    ],
    products: [
        .executable(
            name: "GlideHUD",
            targets: ["GlideHUD"]
        )
    ],
    targets: [
        .executableTarget(
            name: "GlideHUD",
            path: "Sources/GlideHUD"
        )
    ]
)
