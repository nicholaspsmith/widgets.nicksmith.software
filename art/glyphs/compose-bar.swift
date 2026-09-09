import AppKit
// Compose a 2x macOS menu bar (1000pt x 28pt) from real icon crops + rendered text, with a notch in the middle.
let W: CGFloat = 1000, H: CGFloat = 28, S: CGFloat = 2
func crop(_ name: String, _ w: Int) -> NSImage { let img = NSImage(contentsOfFile: "bar/crop-\(name).png")!; img.size = NSSize(width: w, height: 28); return img }
func arcIcon() -> NSImage { // Apollo-style green arc at 75%
    let img = NSImage(size: NSSize(width: 18, height: 18), flipped: false) { r in
        let c = NSPoint(x: 9, y: 8); let track = NSBezierPath(); track.appendArc(withCenter: c, radius: 6.5, startAngle: 225, endAngle: -45, clockwise: true); track.lineWidth = 3; NSColor(white: 1, alpha: 0.18).set(); track.stroke()
        let arc = NSBezierPath(); arc.appendArc(withCenter: c, radius: 6.5, startAngle: 225, endAngle: 225 - 270 * 0.75, clockwise: true); arc.lineWidth = 3; arc.lineCapStyle = .round; NSColor.systemGreen.set(); arc.stroke(); return true }
    return img
}
let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: Int(W * S), pixelsHigh: Int(H * S), bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
rep.size = NSSize(width: W, height: H)
NSGraphicsContext.saveGraphicsState(); NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
// bar background sampled from the live bar (a flat very dark grey with the wallpaper tint removed)
NSColor(red: 0.0000, green: 0.0000, blue: 0.0000, alpha: 1).set(); NSRect(x: 0, y: 0, width: W, height: H).fill()
// left: Apple glyph + app menus
let menuFont = NSFont.menuBarFont(ofSize: 13); let bold = NSFont.boldSystemFont(ofSize: 13)
let white = NSColor(white: 0.93, alpha: 1)
var x: CGFloat = 16
func draw(_ s: String, _ f: NSFont, _ c: NSColor = white, gap: CGFloat = 18) { let a = NSAttributedString(string: s, attributes: [.font: f, .foregroundColor: c]); a.draw(at: NSPoint(x: x, y: (H - a.size().height) / 2 + 0.5)); x += a.size().width + gap }
draw("Finder", bold); for m in ["File", "Edit", "View", "Go", "Window", "Help"] { draw(m, menuFont) }
// notch
let notchW: CGFloat = 176, notchX = (W - notchW) / 2
let notch = NSBezierPath(); notch.move(to: NSPoint(x: notchX, y: H)); notch.line(to: NSPoint(x: notchX, y: 6)); notch.appendArc(withCenter: NSPoint(x: notchX + 8, y: 6), radius: 8, startAngle: 180, endAngle: 270, clockwise: false); notch.line(to: NSPoint(x: notchX + notchW - 8, y: -2)); notch.appendArc(withCenter: NSPoint(x: notchX + notchW - 8, y: 6), radius: 8, startAngle: 270, endAngle: 360, clockwise: false); notch.line(to: NSPoint(x: notchX + notchW, y: H)); notch.close(); NSColor.black.set(); notch.fill()
// right: real crops and renders, laid out right-to-left from the clock
var rx = W - 10
func place(_ img: NSImage, width: CGFloat) { rx -= width; img.draw(in: NSRect(x: rx, y: (H - img.size.height) / 2, width: width, height: img.size.height), from: .zero, operation: .sourceOver, fraction: 1) }
func placeIcon(_ img: NSImage) { rx -= 6; place(img, width: img.size.width); rx -= 6 }
place(crop("clock", 127), width: 127)              // clock (real pixels)
place(crop("controlcenter", 26), width: 26)          // Control Center (real pixels)
rx -= 6
func rendered(_ id: String) -> NSImage { let i = NSImage(contentsOfFile: "render/icon-\(id).png")!; let r = i.representations.first!; i.size = NSSize(width: CGFloat(r.pixelsWide) / 2, height: CGFloat(r.pixelsHigh) / 2); return i }
for id in ["download-recycler", "media-tracking-killer", "apollo-monitor", "macrecorder", "claude-usage"] { placeIcon(rendered(id)) }
let battery = rendered("battery-time"); rx -= 4; place(battery, width: battery.size.width); rx -= 4
for id in ["process-monitor", "vpn-dns", "keylight", "barn"] { placeIcon(rendered(id)) }
NSGraphicsContext.restoreGraphicsState()
try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: "bar/hero-bar.png"))
print("wrote bar/hero-bar.png", rep.pixelsWide, "x", rep.pixelsHigh, "right block starts at", Int(rx))
