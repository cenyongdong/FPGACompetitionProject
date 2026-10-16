# Independent Lite PL oscillator, schematic AC14 / BANK12 / 3.3V.
set_property PACKAGE_PIN AC14 [get_ports hdmi_ref_100m]
set_property IOSTANDARD LVCMOS33 [get_ports hdmi_ref_100m]
create_clock -name hdmi_ref_100m -period 10.000 [get_ports hdmi_ref_100m]
