
    set vvd_path [get_vvd_path]
	set vvd_version [string range [version -short] 0 5]
	if {$vvd_version != "2018.3"} {
		error "FMSH->This command only support in Vivado2018.3!"
	}
	reset_database_to_default
	
	set Sitemap2_xml_wr    [format "%s/data/parts/xilinx/zynq/devint/Sitemap2.xml" $vvd_path]
	# set unisim_btl_wr      [format "%s/data/parts/xilinx/common/unisim.btl" $vvd_path]
	set unisim_comp_lib_wr [format "%s/scripts/rt/data/unisim_comp.lib" $vvd_path]
	set unisim_comp_v_wr   [format "%s/scripts/rt/data/unisim_comp.v" $vvd_path]
	set zynq_lib_wr        [format "%s/data/parts/xilinx/zynq/devint/zynq.lib" $vvd_path]
	set zynq_rtd_wr		   [format "%s/data/parts/xilinx/zynq/devint/zynq.rtd" $vvd_path]
	set zynq_xng_wr        [format "%s/data/parts/xilinx/zynq/devint/zynq.xng" $vvd_path]
	
	set zynq_padr_wr       [format "%s/data/parts/xilinx/zynq/devint/zynq.padr" $vvd_path]
	set zynq_pspd_wr       [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z030/xc7z030.paspd" $vvd_path]
	#patch path
	set current_prj_path [file join $::env(JFM_PATH)]

	set Sitemap2_xml_rd    [format "%s/ip_patch/030ai/Sitemap2.xml" $current_prj_path]
	# set unisim_btl_rd      [format "%s/ip_patch/100ai/unisim.btl" $current_prj_path]
	set unisim_comp_lib_rd [format "%s/ip_patch/030ai/unisim_comp.lib" $current_prj_path]
	set unisim_comp_v_rd   [format "%s/ip_patch/030ai/unisim_comp.v" $current_prj_path]
	set zynq_lib_rd        [format "%s/ip_patch/030ai/zynq.lib" $current_prj_path]
	set zynq_rtd_rd 	   [format "%s/ip_patch/030ai/zynq.rtd" $current_prj_path]
	set zynq_xng_rd		   [format "%s/ip_patch/030ai/zynq.xng" $current_prj_path]
	set zynq_padr_rd       [format "%s/ip_patch/030ai/zynq.padr" $current_prj_path]
	
	if {$speed == 0} {
		set zynq_pspd_rd       [format "%s/ip_patch/030ai/xc7z030ai.paspd" $current_prj_path]
	} elseif {$speed == "fast"} {
		set zynq_pspd_rd       [format "%s/ip_patch/030ai/xc7z030ai_fast.paspd" $current_prj_path]
		puts "FMSH->7z030AI change speed to fast!"
	} else {
		error "FMSH->Unknow value $speed!"
	}
	set file_list_wr [concat $Sitemap2_xml_wr  $unisim_comp_lib_wr $unisim_comp_v_wr $zynq_lib_wr $zynq_rtd_wr $zynq_xng_wr $zynq_padr_wr $zynq_pspd_wr]
	foreach file_wr $file_list_wr {
	    if {[file exist $file_wr]} {
		} else {
		    error "An error occurs:\nCan't find $file_wr no such file! "
		}
	}
	#replace file
	set file_list_rd [concat $Sitemap2_xml_rd  $unisim_comp_lib_rd $unisim_comp_v_rd $zynq_lib_rd $zynq_rtd_rd $zynq_xng_rd $zynq_padr_rd $zynq_pspd_rd]
    set i 0
	foreach file_rd $file_list_rd {
	    file copy -force $file_rd [lindex $file_list_wr $i]
		incr i
	}
	if {$vvd_version == "2018.3"} {
		set unisim_btl_wr      [format "%s/data/parts/xilinx/common/unisim.btl" $vvd_path]
		set unisim_btl_rd      [format "%s/ip_patch/030ai/unisim.btl" $current_prj_path]
		file copy -force $unisim_btl_rd $unisim_btl_wr
	} elseif {$vvd_version == "2022.1"} {
		file delete -force [format "%s/data/parts/xilinx/common/unisims" $vvd_path]
		file copy -force [format "%s/ip_patch/030ai/unisims" $current_prj_path] [format "%s/data/parts/xilinx/common" $vvd_path]
	}
	puts "Replace 7z030AI data files successfully!(total $i files)"

