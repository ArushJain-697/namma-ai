# Raspberry Pi 5 case

3D-printable case for the Sakshi device: a Raspberry Pi 5 with a small screen, an internal 30×30×7 mm fan and three Cherry MX switches as buttons. Modelled in OpenSCAD; the `.scad` files are the source and the `.stl` files are exports.

| Folder | What changed |
|---|---|
| `v2/` | Fan moved inside the case behind a 28 mm opening; the four round buttons replaced with three Cherry MX cutouts |
| `v3/` | **Experimental.** Screen rotated 90°, switches arranged in a V, case widened |

Each folder has `base`, `lid` and `testbed` STLs. The testbed is a small test print for checking fit before printing the full case.

## Re-exporting
```bash
openscad -D 'part="base"' -o pi_case_v3_base.stl pi_case_v3.scad   # same for "lid" and "testbed"
```

## Printing and assembly
- **Base:** upright, floor on the bed.
- **Lid:** plate face down on the bed.
- **Assembly:** flip the lid end over end so the switch row sits on the HDMI / USB-C side. The mating parts are symmetric, so either flip fits.

Values marked `(ASSUMED)` in the `.scad` files were not measured; they are listed at the bottom of each file.
