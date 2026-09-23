// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.
//
// Copyright (c) 2026 Nicholas Smith

import AppKit
// Compose a 2x macOS menu bar (1000pt x 28pt) from real icon crops + rendered text.
// The right end mirrors the real bar as read through Accessibility on 2026-09-23 (an external
// display, so no notch): Monitor Lizard, Claude Usage, VPN & DNS, Homestead, Process Monitor,
// Barn's handle, Battery Time, then Bluetooth, Wi-Fi, Control Center and the analog clock.
// VidSnatch and Apple's Weather item sit on the real bar too and are left off on purpose.
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
// right: real crops and renders, laid out right-to-left from the clock
var rx = W - 10
func place(_ img: NSImage, width: CGFloat) { rx -= width; img.draw(in: NSRect(x: rx, y: (H - img.size.height) / 2, width: width, height: img.size.height), from: .zero, operation: .sourceOver, fraction: 1) }
func placeIcon(_ img: NSImage) { rx -= 6; place(img, width: img.size.width); rx -= 6 }
func symbol(_ name: String, size: CGFloat) -> NSImage { // an SF Symbol, inked white
    let base = NSImage(systemSymbolName: name, accessibilityDescription: nil)!.withSymbolConfiguration(.init(pointSize: size, weight: .medium))!
    let img = NSImage(size: base.size, flipped: false) { r in base.draw(in: r); white.set(); r.fill(using: .sourceAtop); return true }
    return img
}
func analogClock() -> NSImage { // the menu bar's analog clock, reading 1:26
    NSImage(size: NSSize(width: 18, height: 18), flipped: false) { _ in
        let c = NSPoint(x: 9, y: 9); let dial = NSBezierPath(ovalIn: NSRect(x: 1.5, y: 1.5, width: 15, height: 15)); dial.lineWidth = 1.5; white.set(); dial.stroke()
        func hand(_ angleDeg: CGFloat, _ len: CGFloat, _ w: CGFloat) { let a = (90 - angleDeg) * .pi / 180; let p = NSBezierPath(); p.move(to: c); p.line(to: NSPoint(x: c.x + cos(a) * len, y: c.y + sin(a) * len)); p.lineWidth = w; p.lineCapStyle = .round; p.stroke() }
        hand(30 + 26 * 0.5, 3.8, 1.6); hand(26 * 6, 5.6, 1.4); return true
    }
}
func bluetooth() -> NSImage { // the rune, one polyline
    NSImage(size: NSSize(width: 12, height: 18), flipped: false) { _ in
        let cx: CGFloat = 6, cy: CGFloat = 9; let p = NSBezierPath()
        p.move(to: NSPoint(x: cx - 3.5, y: cy - 3.5)); p.line(to: NSPoint(x: cx + 3.5, y: cy + 3.5)); p.line(to: NSPoint(x: cx, y: cy + 7)); p.line(to: NSPoint(x: cx, y: cy - 7)); p.line(to: NSPoint(x: cx + 3.5, y: cy - 3.5)); p.line(to: NSPoint(x: cx - 3.5, y: cy + 3.5))
        p.lineWidth = 1.5; p.lineJoinStyle = .round; p.lineCapStyle = .round; white.set(); p.stroke(); return true
    }
}
rx -= 4
placeIcon(analogClock())                              // analog clock
place(crop("controlcenter", 26), width: 26)          // Control Center (real pixels)
placeIcon(symbol("wifi", size: 13))                  // Wi-Fi
placeIcon(bluetooth())                               // Bluetooth
func rendered(_ id: String) -> NSImage { let i = NSImage(contentsOfFile: "render/icon-\(id).png")!; let r = i.representations.first!; i.size = NSSize(width: CGFloat(r.pixelsWide) / 2, height: CGFloat(r.pixelsHigh) / 2); return i }
let battery = rendered("battery-time"); rx -= 4; place(battery, width: battery.size.width); rx -= 4
for id in ["barn", "process-monitor", "homestead", "vpn-dns", "claude-usage", "monitor-lizard"] { placeIcon(rendered(id)) }
NSGraphicsContext.restoreGraphicsState()
try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: "bar/hero-bar.png"))
print("wrote bar/hero-bar.png", rep.pixelsWide, "x", rep.pixelsHigh, "right block starts at", Int(rx))
