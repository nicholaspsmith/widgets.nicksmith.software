import AppKit

// Renders every Menubarn menu-bar glyph straight from the apps' own drawing
// code (CharacterIcon.swift from StatusItemKit, BatteryGlyph.swift from
// Battery Time, the barn from Barn — copied in by render-glyphs.sh), so the
// site and the READMEs show exactly what the bar shows, with no screen capture.
//
// Outputs, in the working directory:
//   icon-<id>.png         one representative state at 2x (feeds compose-bar.swift)
//   states-<id>.png       every state side by side on a menu-bar-dark pill, 3x (site + READMEs)

func png(_ rep: NSBitmapImageRep, _ path: String) {
    try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: path))
}

func save(_ img: NSImage, _ path: String) {
    let w = Int(img.size.width * 2), h = Int(img.size.height * 2)
    let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h, bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    rep.size = img.size
    NSGraphicsContext.saveGraphicsState(); NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
    img.draw(in: NSRect(origin: .zero, size: img.size)); NSGraphicsContext.restoreGraphicsState()
    png(rep, path)
}

/// States side by side at 3x on a dark rounded pill, like a slice of menu bar.
func strip(_ states: [NSImage], _ path: String) {
    let scale: CGFloat = 3, pad: CGFloat = 10, gap: CGFloat = 14, h: CGFloat = 30
    let content = states.reduce(0) { $0 + $1.size.width } + gap * CGFloat(states.count - 1)
    let w = content + pad * 2
    let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: Int(w * scale), pixelsHigh: Int(h * scale), bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    rep.size = NSSize(width: w, height: h)
    NSGraphicsContext.saveGraphicsState(); NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
    NSColor(red: 0.11, green: 0.11, blue: 0.13, alpha: 1).set()
    NSBezierPath(roundedRect: NSRect(x: 0, y: 0, width: w, height: h), xRadius: 8, yRadius: 8).fill()
    var x = pad
    for s in states {
        s.draw(in: NSRect(x: x, y: (h - s.size.height) / 2, width: s.size.width, height: s.size.height))
        x += s.size.width + gap
    }
    NSGraphicsContext.restoreGraphicsState()
    png(rep, path)
}

// Barn's handle (copied from Handle.swift, barn red, 26x22)
func barn(open: Bool) -> NSImage {
    let image = NSImage(size: NSSize(width: 26, height: 22), flipped: false) { _ in
        let ctx = NSGraphicsContext.current!
        NSColor(red: 0.64, green: 0.21, blue: 0.17, alpha: 1).set()
        let body = NSBezierPath()
        body.move(to: NSPoint(x: 2, y: 1)); body.line(to: NSPoint(x: 2, y: 10.5)); body.line(to: NSPoint(x: 5, y: 16)); body.line(to: NSPoint(x: 13, y: 21)); body.line(to: NSPoint(x: 21, y: 16)); body.line(to: NSPoint(x: 24, y: 10.5)); body.line(to: NSPoint(x: 24, y: 1)); body.close(); body.fill()
        ctx.compositingOperation = .destinationOut
        NSBezierPath(roundedRect: NSRect(x: 9.3, y: 1, width: 7.4, height: 8.6), xRadius: 0.8, yRadius: 0.8).fill()
        NSBezierPath(ovalIn: NSRect(x: 11.4, y: 12.4, width: 3.2, height: 3.2)).fill()
        ctx.compositingOperation = .sourceOver
        if !open {
            NSBezierPath(rect: NSRect(x: 10, y: 1, width: 6, height: 7.9)).fill()
            ctx.compositingOperation = .destinationOut
            let seam = NSBezierPath(); seam.move(to: NSPoint(x: 13, y: 1)); seam.line(to: NSPoint(x: 13, y: 8.9)); seam.lineWidth = 0.9; seam.stroke()
            ctx.compositingOperation = .sourceOver
        }
        return true
    }
    return image
}

let white = NSColor.white
let dim = NSColor(white: 0.62, alpha: 1)
// Claude Usage's default colour pair (Grape & Mint): session in the left
// pupil, weekly in the right, the same colours its menu bars are drawn in.
let grape = NSColor(srgbRed: 0xB1 / 255, green: 0x8E / 255, blue: 0xEE / 255, alpha: 1)
let mint = NSColor(srgbRed: 0x5F / 255, green: 0xD3 / 255, blue: 0xA6 / 255, alpha: 1)
func owl(_ session: CGFloat, _ weekly: CGFloat) -> NSImage {
    CharacterIcon.owl(session: session, weekly: weekly, sessionPupil: grape, weeklyPupil: mint)
}

// Representative single states (the hero bar).
save(barn(open: false), "icon-barn.png")
save(CharacterIcon.key(level: 0.6, active: true), "icon-keylight.png")
save(CharacterIcon.chameleon(tailscale: true, mullvad: true), "icon-vpn-dns.png")
save(CharacterIcon.octopus(fraction: 0.3), "icon-process-monitor.png")
save(BatteryGlyph.image(pct: 80, charging: false, lead: "80%", trailing: "9:55", ink: white, fill: .none, face: true), "icon-battery-time.png")
save(owl(0.58, 0.33), "icon-claude-usage.png")
save(CharacterIcon.camcorder(recording: false), "icon-macrecorder.png")
save(CharacterIcon.apollo(level: 0.6, online: true), "icon-apollo-monitor.png")
save(CharacterIcon.raccoon(active: true), "icon-media-tracking-killer.png")
save(CharacterIcon.bin(active: true), "icon-download-recycler.png")
save(CharacterIcon.monitorLizard(brightness: 0.8, nightShift: false), "icon-monitor-lizard.png")

// State strips, in the order the READMEs describe them.
strip([barn(open: false), barn(open: true)], "states-barn.png")
strip([CharacterIcon.key(level: 0, active: true), CharacterIcon.key(level: 0.25, active: true), CharacterIcon.key(level: 0.75, active: true), CharacterIcon.key(level: 1, active: true)], "states-keylight.png")
strip([CharacterIcon.chameleon(tailscale: false, mullvad: false), CharacterIcon.chameleon(tailscale: true, mullvad: false), CharacterIcon.chameleon(tailscale: false, mullvad: true), CharacterIcon.chameleon(tailscale: true, mullvad: true)], "states-vpn-dns.png")
strip([CharacterIcon.octopus(fraction: 0.1), CharacterIcon.octopus(fraction: 0.3), CharacterIcon.octopus(fraction: 0.6), CharacterIcon.octopus(fraction: 0.9)], "states-process-monitor.png")
strip([BatteryGlyph.image(pct: 80, charging: false, lead: "80%", trailing: "", ink: white, fill: .none, face: true), BatteryGlyph.image(pct: 40, charging: true, lead: "40%", trailing: "1:10", ink: white, fill: .none, face: true), BatteryGlyph.image(pct: 15, charging: false, lead: "", trailing: "", ink: white, fill: .red, face: true)], "states-battery-time.png")
strip([owl(0.05, 0.1), owl(0.5, 0.3), owl(0.9, 0.6), owl(1, 1)], "states-claude-usage.png")
strip([CharacterIcon.camcorder(recording: false), CharacterIcon.camcorder(recording: true)], "states-macrecorder.png")
strip([CharacterIcon.apollo(level: 0.15, online: true), CharacterIcon.apollo(level: 0.5, online: true), CharacterIcon.apollo(level: 0.9, online: true), CharacterIcon.apollo(level: 0.5, online: false)], "states-apollo-monitor.png")
strip([CharacterIcon.raccoon(active: true), CharacterIcon.raccoon(active: false)], "states-media-tracking-killer.png")
strip([CharacterIcon.bin(active: true), CharacterIcon.bin(active: false)], "states-download-recycler.png")
strip([CharacterIcon.monitorLizard(brightness: 0.25, nightShift: false), CharacterIcon.monitorLizard(brightness: 0.8, nightShift: false), CharacterIcon.monitorLizard(brightness: 0.8, nightShift: true), CharacterIcon.monitorLizard(brightness: 0.8, nightShift: true, tongue: true)], "states-monitor-lizard.png")
print("rendered")
