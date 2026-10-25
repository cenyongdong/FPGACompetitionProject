# PJTAG already has the qualified OBUFT inside the PS OOC.
set_property IO_BUFFER_TYPE NONE [get_ports PJTAG_TDO]
