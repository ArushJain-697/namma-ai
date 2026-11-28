// Raspberry Pi 5 case v3 (EXPERIMENT): screen rotated 90 deg, switches in a V, case widened.
//   Base : same as pi_case.scad, but the -x end-wall camera opening is enlarged into a
//          28 mm fan opening, and the 30x30x7 fan sits INSIDE the case against that wall
//          (nothing sticks out of the case), held by two side ribs on the floor.
//   Lid  : same as pi_case.scad (same screen window), short-side screen walls removed,
//          4 round buttons replaced by 3 Cherry MX cutouts.
// Export: openscad -D 'part="base"' -o base.stl pi_case_v3.scad   (same for "lid", "testbed")
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
tab_x = scr_l/4;           // tabs at +-this from the board centre along the long axis

// ---------- v3: screen rotated 90 deg, switches in a V ----------
scr_end_gap = 1.0;         // board end to base wall, each end (board now runs along y)
glass_end_y = 1;           // +1 = glass end (3 mm blank) toward +y, -1 = toward -y
vee_dx = 10;               // arm keys sit this much farther from the screen than the vertex key
vee_dy = 19.05;            // arm keys are this far above/below the vertex key (1u pitch)
vee_gap = 2;               // screen edge to vertex keycap edge

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
board_x = scr_w + 2*tab_gap;              // rotated board footprint, x
board_y = scr_l + 2*tab_gap;              //                          y (65.4 - longer than v1's W)
group_l = board_x + vee_gap + keycap + vee_dx;   // screen + V, one block, centred on the lid
L = max(px + pi_l + clr, 2*margin + group_l);                   // inner length
W = max(pi_w + 2*clr, board_y + 2*scr_end_gap);                 // inner width (v1 was 59.8)

win_sy = glass_end_y * (scr_l/2 - win_edge - win_l/2);   // window offset from board centre (y)
group_x0 = L/2 - group_l/2;               // left edge of the block, inner coords
scr_cx = group_x0 + board_x/2;
scr_cy = W/2;
// V: vertex key nearest the screen, two arm keys farther out and +-vee_dy up/down
mx_vx = group_x0 + board_x + vee_gap + keycap/2;
mx_pos = [[mx_vx, W/2], [mx_vx + vee_dx, W/2 - vee_dy], [mx_vx + vee_dx, W/2 + vee_dy]];

cam_cy = W/2;
cam_cz = floor_t + cam_out_w/2;

pcb_top = floor_t + standoff_h + pi_t;
hang   = max(ring_h, scr_t + 0.6);
base_h = pcb_top + usb_h + hang + 1;

Lo = L + 2*wall;  Wo = W + 2*wall;        // outer footprint (base and lid)

// ---------- derived v2 ----------
fan_cy = cam_cy;                          // centred on the end wall
fan_cz = floor_t + fan_s/2;               // fan sits on the floor: z 2..32 (lid plate is at 32.2)
board_notch = board_x + 2*(lip_t + 1);    // lid lip removed where the board's ends pass it (x length)

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
      // screen locator tabs: 2 small tabs on each LONG side of the (now rotated) board
      for (sx = [-1, 1], sy = [-1, 1])
        translate([wall + scr_cx + (sx > 0 ? scr_w/2 + tab_gap : -(scr_w/2 + tab_gap + lip_t)),
                   wall + scr_cy + sy*tab_x - tab_len/2,
                   plate_t - 0.01])
          cube([lip_t, tab_len, tab_h + 0.01]);
    }
    // screen window, rotated: 40 (x) by 46 (y), shifted toward the glass end of the board
    translate([wall + scr_cx - win_w/2, wall + scr_cy + win_sy - win_l/2, -1])
      cube([win_w, win_l, plate_t + 2]);
    // MX switches in a V
    for (p = mx_pos)
      translate([wall + p[0], wall + p[1], 0]) rotate([0, 0, mx_rot]) {
        translate([-mx_cut/2, -mx_cut/2, -1]) cube([mx_cut, mx_cut, plate_t + 2]);
        if (plate_t > mx_plate_t)   // underside relief on the clip faces -> 1.5 mm plate there
          translate([-mx_cut/2, -mx_relief/2, mx_plate_t]) cube([mx_cut, mx_relief, plate_t]);
      }
    // lip notches at both long edges where the board's ends pass (board is longer than the
    // lip's inner width), centred on the board so the lid stays mirror-symmetric in y
    for (ey = [wall, wall + W - fit - lip_t - 0.5])
      translate([wall + scr_cx - board_notch/2, ey, plate_t - 0.01])
        cube([board_notch, fit + lip_t + 0.5, ring_h + 1]);
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
tb_x0 = wall + group_x0 - 2;
tb_x1 = wall + group_x0 + group_l + 2;
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
echo(str("MX centres (world): ", [for (p = mx_pos) [wall + p[0], wall + p[1]]]));
echo(str("Keycap extents x ", wall + mx_vx - keycap/2, "..", wall + mx_vx + vee_dx + keycap/2,
         "  y ", wall + W/2 - vee_dy - keycap/2, "..", wall + W/2 + vee_dy + keycap/2, "  arm-vertex gap in y ", vee_dy - keycap));
echo(str("Window x ", wall + scr_cx - win_w/2, "..", wall + scr_cx + win_w/2, "  y ", wall + scr_cy + win_sy - win_l/2, "..", wall + scr_cy + win_sy + win_l/2));
echo(str("Screen board x ", wall + scr_cx - board_x/2, "..", wall + scr_cx + board_x/2, "  y ", wall + scr_cy - board_y/2, "..", wall + scr_cy + board_y/2, "  group margin L/R ", wall + group_x0));

// ---------- ASSUMPTIONS (fields left TODO) ----------
// Fan: 30x30x7 mm, INSIDE the case on the floor against the -x wall, held by two ribs +
//   tape/glue. 28 mm wall opening. Its screw holes aren't used. Fan lead runs over a rib.
// Screen: v1 numbers kept (65x40 PCB, 46x40 window, 5 mm thick); glass size unknown.
// Switch layout: 3 in a row at 19.05 mm pitch in v1's button strip, centred on the lid.
// Print: base upright; lid face down.
