// Raspberry Pi 5 case v2: base + lid.
//   Base : same as pi_case.scad, but the -x end-wall camera opening is enlarged into a
//          28 mm fan opening, and the 30x30x7 fan sits INSIDE the case against that wall
//          (nothing sticks out of the case), held by two side ribs on the floor.
//   Lid  : same as pi_case.scad (same screen window), short-side screen walls removed,
//          4 round buttons replaced by 3 Cherry MX cutouts.
// Export: openscad -D 'part="base"' -o base.stl pi_case_v2.scad   (same for "lid")
// Print : base upright (floor on bed). Lid plate/face DOWN on bed, as in v1.
// Assemble: flip the lid END-OVER-END (about the Y axis) so the switch row lands on the
//           HDMI / USB-C (-y) side. Everything that mates is symmetric, so either flip fits.
// All units mm. Values marked (ASSUMED) were not specified - see the bottom of the file.

part = "both";      // "base", "lid", "testbed", "both" (print layout), "assembled" (preview), "none"

// ---------- Raspberry Pi 5 (unchanged from v1) ----------
pi_l = 85;  pi_w = 56;  pi_t = 1.6;
pi_hole_dx = 58;  pi_hole_dy = 49;  pi_hole_off = 3.5;   // M2.5 holes
usb_h = 17;         // USB/Ethernet stack height above the PCB (assumed in v1)

// ---------- case (unchanged from v1: proven tolerances) ----------
wall = 2;  floor_t = 2;  plate_t = 2;   // plate_t = lid top thickness
clr = 1;            // gap between Pi and inside wall
fit = 0.3;          // lid lip clearance
lip_t = 1.2;        // lip / pocket wall thickness
ring_h = 2;         // height of the lip that drops into the base
standoff_h = 5;
margin = lip_t + fit;

// ---------- screen (unchanged from v1) ----------
scr_l = 65;  scr_w = 40;   // PCB
scr_t = 5;                 // PCB + glass thickness (v1 assumption)
win_l = 46;  win_w = 40;   // visible window (kept exactly)
win_edge = 3;              // window offset from the glass-end PCB edge (kept exactly)
// Screen locators: small tabs on the two LONG sides only (the screen is taped in, so they
// just stop it sliding). v1 had full-length 5.6 mm walls; these are small and low.
tab_len = 10;              // along the screen's long edge
tab_h = 3;                 // hang below the plate (screen is 5 mm thick, so it still locates it)
tab_n = 2;                 // per long side, placed symmetrically about the board centre
tab_gap = 0.2;             // clearance to the board edge (same 0.4 total as v1's pocket)
tab_x = scr_l/4;           // tabs at +-this from the board centre along x

// ---------- camera (v1 geometry; kept so the base layout is identical) ----------
cam_l = 25;  cam_w = 24;
cam_hole_d = 14;    // v1 lens opening (replaced by the fan opening below)
cam_lens_dy = 2.5;
cam_depth = 8;
cam_wall = 1.2;
cam_cradle_on = false;     // v2: cradle removed - it would sit 8 mm behind the fan and block it

// ---------- fan (ASSUMED: 30 x 30 x 7 mm, e.g. 3007 5 V) ----------
fan_s = 30;                // frame size (height and width)
fan_t = 7;                 // frame thickness = depth into the case from the inner wall face
fan_hole_d = 28;           // airflow opening through the wall (blade sweep ~27-28); a 29 mm
                           // hole would leave only 0.7 mm of wall above it
fan_clr = 0.2;             // clearance per side between fan frame and the ribs
rib_t = 1.2;               // side rib thickness
rib_top = 29;              // ribs stop here (z), below the lid lip (z 30.2) so they never touch it
cable_z = rib_top;         // fan lead runs over the +y rib top, in the 3 mm under the lid

// ---------- switches (Cherry MX) ----------
mx_cut = 14.04;            // measured from modular-key-v1.stl (nominal 14.00), axis-aligned
mx_n = 3;
mx_pitch = 19.05;          // 1u keycap spacing
mx_plate_t = 1.5;          // plate thickness the MX clips need
mx_relief = 15.4;          // underside relief pocket along the clip axis (clip span ~15.2 mm)
mx_rot = 90;               // switch turned 90 deg: plate clips face +-x (along the row), so
                           // nothing sticks out toward the base wall or the screen in y.
                           // The 14 mm square cutout itself is the same either way.
mx_below = 8.3;            // housing (5.0) + pins (3.3) below the plate top face
mx_body = 14.0;            // housing width below the plate
keycap = 18;               // 1u keycap footprint (for the clearance report)
btn_row = 14;              // v1 strip below the screen that holds the switch row

// ---------- derived layout (identical to v1) ----------
pocket_l = scr_l + 0.4 + 2*lip_t;
pocket_w = scr_w + 0.4 + 2*lip_t;
cam_out_l = cam_l + 0.4 + 2*cam_wall;
cam_out_w = cam_w + 0.4 + 2*cam_wall;
cam_len   = cam_depth + 4;
bay_l = cam_len + 3;

px = bay_l + clr;
py = clr;
L = max(px + pi_l + clr, 2*margin + pocket_l);                  // inner length
W = max(pi_w + 2*clr, 2*margin + pocket_w + btn_row);           // inner width

// Screen orientation as in v1 (glass end toward -x in lid coords). With the lid flipped
// end-over-end the board then sits at x 14..79 in the case, clear of the USB stack.
glass_end = -1;            // -1 = v1 orientation (approved layout), +1 = mirrored
win_sx = glass_end * (scr_l/2 - win_edge - win_l/2); // window offset from the screen-board centre
scr_cx = L/2 - win_sx;                    // v2: board shifted so the WINDOW is centred on the lid
scr_cy = W - margin - pocket_w/2;
// v2 switch row: centred under the window in x; keycaps centred in the band between the
// lid's front edge and the window's lower edge (equal gap on both sides) in y.
mx_cx = L/2;                              // = window centre = lid centre
win_y0 = scr_cy - win_w/2;                // window lower edge (inner coords)
mx_cy = (-wall + win_y0)/2;               // mid-band
keycap_gap = (win_y0 + wall - keycap)/2;  // keycap edge to lid edge = keycap edge to window

cam_cy = W/2;
cam_cz = floor_t + cam_out_w/2;

pcb_top = floor_t + standoff_h + pi_t;
hang   = max(ring_h, scr_t + 0.6);
base_h = pcb_top + usb_h + hang + 1;

Lo = L + 2*wall;  Wo = W + 2*wall;        // outer footprint (base and lid)

// ---------- derived v2 ----------
fan_cy = cam_cy;                          // centred on the end wall
fan_cz = floor_t + fan_s/2;               // fan sits on the floor: z 2..32 (lid plate is at 32.2)
mx_span = (mx_n - 1) * mx_pitch;
lip_notch = mx_span + mx_relief + 1;      // lid lip removed over the switch row (x length)

module rrect(l, w, r, h) {
  translate([r, r, 0]) linear_extrude(h) offset(r = r) square([l - 2*r, w - 2*r]);
}

// ======================= BASE =======================
module base() {
  difference() {
    union() {
      difference() {
        rrect(Lo, Wo, 3, base_h);
        // cavity
        translate([wall, wall, floor_t]) cube([L, W, base_h]);
        // -y wall: USB-C power + 2 micro-HDMI (Pi 5 has no audio jack)
        translate([wall + px + 5, -1, pcb_top - 0.5]) cube([41, wall + 2, base_h]);
        // +x wall: Ethernet + USB
        translate([wall + L - 1, wall + py + 1, pcb_top - 0.5]) cube([wall + 2, pi_w - 2, base_h]);
      }
      // Pi standoffs with locating pins
      for (x = [0, pi_hole_dx], y = [0, pi_hole_dy])
        translate([wall + px + pi_hole_off + x, wall + py + pi_hole_off + y, floor_t]) {
          cylinder(d = 6, h = standoff_h, $fn = 30);
          cylinder(d = 2.4, h = standoff_h + pi_t + 1, $fn = 20);
        }
      if (cam_cradle_on) cam_cradle();
      fan_ribs();
    }
    // -x wall: v1 camera opening enlarged into the fan opening
    fan_cutout();
  }
}

// Opening through the -x end wall. The fan's airflow face sits flush on its inner side.
module fan_cutout() {
  translate([-1, wall + fan_cy, fan_cz])
    rotate([0, 90, 0]) cylinder(d = fan_hole_d, h = wall + 1.01, $fn = 90);
}

// Two ribs on the floor, either side of the fan; the wall is the back stop, the lid is the
// top stop (0.2 mm), the fan drops in from above. Tape or a dab of glue stops it sliding
// forward. Ribs are open at the front, so the fan lead leaves over the +y rib top.
module fan_ribs() {
  for (s = [-1, 1])
    translate([wall - 0.01, wall + fan_cy + s*(fan_s/2 + fan_clr) - (s < 0 ? rib_t : 0), floor_t - 0.01])
      cube([fan_t + 1.01, rib_t, rib_top - floor_t + 0.01]);
}

// v1 camera cradle, kept for reference (off by default)
module cam_cradle() {
  difference() {
    translate([wall, wall + cam_cy - cam_out_l/2, floor_t - 0.1])
      cube([cam_len, cam_out_l, cam_out_w + 0.1]);
    translate([wall - 0.01, wall + cam_cy - (cam_l + 0.4)/2, floor_t + cam_wall])
      cube([cam_len + 1, cam_l + 0.4, cam_out_w]);
  }
  for (sy = [-1, 1], z = [0, cam_w + 0.4 - 4])
    translate([wall + cam_depth - 1.5,
               wall + cam_cy + sy * (cam_l + 0.4)/2 - (sy > 0 ? 4 : 0),
               floor_t + cam_wall + z])
      cube([1.5, 4, 4]);
}

// ======================= LID =======================
// Printed plate-down; it flips over onto the base.
module lid() {
  difference() {
    union() {
      rrect(Lo, Wo, 3, plate_t);
      // lip that drops into the base (notched over the switch row)
      translate([wall + fit, wall + fit, plate_t]) difference() {
        cube([L - 2*fit, W - 2*fit, ring_h]);
        translate([lip_t, lip_t, -1]) cube([L - 2*fit - 2*lip_t, W - 2*fit - 2*lip_t, ring_h + 2]);
      }
      // screen locator tabs: 2 small tabs on each LONG side, hugging the board edge
      for (sy = [-1, 1], sx = [-1, 1])
        translate([wall + scr_cx + sx*tab_x - tab_len/2,
                   wall + scr_cy + (sy > 0 ? scr_w/2 + tab_gap : -(scr_w/2 + tab_gap + lip_t)),
                   plate_t - 0.01])
          cube([tab_len, lip_t, tab_h + 0.01]);
    }
    // screen window (unchanged)
    translate([wall + scr_cx + win_sx - win_l/2, wall + scr_cy - win_w/2, -1])
      cube([win_l, win_w, plate_t + 2]);
    // MX switches in the old button row
    for (i = [0 : mx_n - 1])
      translate([wall + mx_cx + (i - (mx_n - 1)/2) * mx_pitch, wall + mx_cy, 0]) rotate([0, 0, mx_rot]) {
        translate([-mx_cut/2, -mx_cut/2, -1]) cube([mx_cut, mx_cut, plate_t + 2]);
        if (plate_t > mx_plate_t)   // underside relief on the clip faces -> 1.5 mm plate there
          translate([-mx_cut/2, -mx_relief/2, mx_plate_t]) cube([mx_cut, mx_relief, plate_t]);
      }
    // lip notch over the switch row (switch housings would hit the -y lip)
    translate([wall + mx_cx - lip_notch/2, wall, plate_t - 0.01])
      cube([lip_notch, fit + lip_t + 0.5, ring_h + 1]);
    // lip notches at BOTH short ends over the fan (fan top is 0.2 mm under the plate, so the
    // lip would hit it); both ends so either lid flip works. Centred, so mirror-symmetric.
    for (ex = [wall, wall + L - fit - lip_t - 0.5])
      translate([ex, wall + W/2 - (fan_s/2 + fan_clr + 1), plate_t - 0.01])
        cube([fit + lip_t + 0.5, fan_s + 2*fan_clr + 2, ring_h + 1]);
  }
}

// lid in its closed position on the base (flipped end-over-end)
module lid_assembled() {
  translate([Lo, 0, base_h + plate_t]) rotate([0, 180, 0]) lid();
}

// Test bed: an exact full-depth slice of lid() around the screen and the 3 switches
// (same window, screen walls, MX cutouts + relief, plate thickness, lip segments).
// Being full depth, its lip pieces also drop into a base, so it can sit on the case.
tb_x0 = wall + min(scr_cx - pocket_l/2, mx_cx - mx_span/2 - keycap/2) - 2;
tb_x1 = wall + max(scr_cx + pocket_l/2, mx_cx + mx_span/2 + keycap/2) + 2;
module test_bed() {
  translate([-tb_x0, 0, 0]) intersection() {
    lid();
    translate([tb_x0, -1, -1]) cube([tb_x1 - tb_x0, Wo + 2, 50]);
  }
}

if (part == "base") base();
else if (part == "lid") lid();
else if (part == "testbed") test_bed();
else if (part == "assembled") { base(); lid_assembled(); }
else if (part == "both") {
  base();
  translate([Lo + 10, 0, 0]) lid();
}

echo(str("Outer size: ", Lo, " x ", Wo, " x ", base_h + plate_t, " mm (base + lid)"));
echo(str("Base h ", base_h, "  lid h ", plate_t + hang, "  inner ", L, " x ", W));
echo(str("Fan inside: x ", wall, "..", wall + fan_t, "  y ", wall + fan_cy - fan_s/2, "..", wall + fan_cy + fan_s/2, "  z ", fan_cz - fan_s/2, "..", fan_cz + fan_s/2, "  Pi starts x ", wall + px));
echo(str("MX row centre y ", wall + mx_cy, "  x centres ", [for (i = [0:mx_n-1]) wall + mx_cx + (i - (mx_n-1)/2)*mx_pitch]));
echo(str("Window x ", wall + scr_cx + win_sx - win_l/2, "..", wall + scr_cx + win_sx + win_l/2,
         " (centre ", wall + scr_cx + win_sx, ", lid centre ", Lo/2, ")  y ", wall + win_y0, "..", wall + win_y0 + win_w));
echo(str("Keycap row x ", wall + mx_cx - mx_span/2 - keycap/2, "..", wall + mx_cx + mx_span/2 + keycap/2,
         "  y ", wall + mx_cy - keycap/2, "..", wall + mx_cy + keycap/2, "  gap to lid edge / window ", keycap_gap));
echo(str("Screen board x ", wall + scr_cx - scr_l/2, "..", wall + scr_cx + scr_l/2));

// ---------- ASSUMPTIONS (fields left TODO) ----------
// Fan: 30x30x7 mm, INSIDE the case on the floor against the -x wall, held by two ribs +
//   tape/glue. 28 mm wall opening. Its screw holes aren't used. Fan lead runs over a rib.
// Screen: v1 numbers kept (65x40 PCB, 46x40 window, 5 mm thick); glass size unknown.
// Switch layout: 3 in a row at 19.05 mm pitch in v1's button strip, centred on the lid.
// Print: base upright; lid face down.
