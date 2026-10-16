proc a50t_324_xdc_modify_fmsh_pin_to_loc xdc_file_path {
  
   set eco_flag [get_xdc_package_eco_flag $xdc_file_path]
   if {$eco_flag == 1} {
      return
   }  
   source_file_backup $xdc_file_path

   set file_r [open $xdc_file_path "r"]
   set backup_str [read $file_r]
   close $file_r
  
   regsub -all "\n{2,}" $backup_str "\n" backup_str_1
   
   set file_backup_name_1 [format "%s.bak1" $xdc_file_path]
   set file_pointer_bk [open $file_backup_name_1 "w"]
   puts $file_pointer_bk $backup_str_1
   close $file_pointer_bk
 
   set inlist [split $backup_str_1 "\n"] 
   set file_w [open $xdc_file_path "w"] 
   
   foreach line $inlist {    
     if {[regexp -nocase {^\s*(set_property)\s+(package_pin)\s+(\w+)\s*(.+)} $line matched_str str_set_property str_package_pin primitive_value assigned_object]} {
#set_property PACKAGE_PIN A18 [get_ports {tg_compare_error}]
        set primitive_value_upper [string toupper $primitive_value]
        if {[array names ::ip_patch::a50t::a50t_324_pin_to_iob_fmsh_to_xilinx $primitive_value_upper] != ""} {
           set dst_line [format "%s LOC %s %s" $str_set_property $::ip_patch::a50t::a50t_324_pin_to_iob_fmsh_to_xilinx($primitive_value_upper) $assigned_object]
           set package_pin_line [format "%s" $::ip_patch::a50t::a50t_324_pin_to_pin_fmsh_to_xilinx($primitive_value_upper)]
           puts $file_w "#$line"
           puts $file_w "#$package_pin_line"
           puts $file_w $dst_line
           continue
        }
     } elseif {[regexp -nocase {^\s*(set_property)\s+(loc)\s+(\w+)\s*(.+)} $line matched_str str_set_property str_loc primitive_value assigned_object]} {
        set primitive_value_upper [string toupper $primitive_value]
        puts "loc matched 1"
        if {[array names ::ip_patch::a50t::a50t_324_pin_to_iob_fmsh_to_xilinx $primitive_value_upper] != ""} {
           puts "loc matched 2"
           set dst_line [format "%s %s %s %s" $str_set_property $str_loc $::ip_patch::a50t::a50t_324_pin_to_iob_fmsh_to_xilinx($primitive_value_upper) $assigned_object]
           set package_pin_line [format "%s" $::ip_patch::a50t::a50t_324_pin_to_pin_fmsh_to_xilinx($primitive_value_upper)]
           puts $file_w "#$line"
           puts $file_w "#$package_pin_line"
           puts $file_w $dst_line
           continue
        }
     } 
     puts $file_w $line
   }
   puts $file_w "\n\n#PACKAGE_ECOed"
   close $file_w
   puts [format "%s package maps succssfully!" $xdc_file_path]
   return 0
}
proc a50t_324_xdc_modify_fmsh_pin_to_loc_to_pin_325tffg900 xdc_file_path {
  
   set eco_flag [get_xdc_package_eco_flag $xdc_file_path]
   if {$eco_flag == 1} {
      return
   }  
   source_file_backup $xdc_file_path

   set file_r [open $xdc_file_path "r"]
   set backup_str [read $file_r]
   close $file_r
  
   regsub -all "\n{2,}" $backup_str "\n" backup_str_1
   
   set file_backup_name_1 [format "%s.bak1" $xdc_file_path]
   set file_pointer_bk [open $file_backup_name_1 "w"]
   puts $file_pointer_bk $backup_str_1
   close $file_pointer_bk
 
   set inlist [split $backup_str_1 "\n"] 
   set file_w [open $xdc_file_path "w"] 
   
   foreach line $inlist {    
     if {[regexp -nocase {^\s*(set_property)\s+(package_pin)\s+(\w+)\s*(.+)} $line matched_str str_set_property str_package_pin primitive_value assigned_object]} {
#set_property PACKAGE_PIN A18 [get_ports {tg_compare_error}]
        set primitive_value_upper [string toupper $primitive_value]
        if {[array names ::ip_patch::a50t::a50t_324_pin_to_iob_fmsh_to_xilinx $primitive_value_upper] != ""} {
           set iob_loc_value_a50t $::ip_patch::a50t::a50t_324_pin_to_iob_fmsh_to_xilinx($primitive_value_upper)
           set pin_325tffg900 $::ip_patch::a50t::xc7k325tffg900_iob_to_pin($iob_loc_value_a50t)
           set dst_line [format "%s PACKAGE_PIN %s %s" $str_set_property $pin_325tffg900 $assigned_object]
           puts $file_w "#$line"
           puts $file_w "#$iob_loc_value_a50t"
#           puts $file_w "#$package_pin_line"
           puts $file_w $dst_line
           continue
        }
     } elseif {[regexp -nocase {^\s*(set_property)\s+(loc)\s+(\w+)\s*(.+)} $line matched_str str_set_property str_loc primitive_value assigned_object]} {
        set primitive_value_upper [string toupper $primitive_value]
        if {[array names ::ip_patch::a50t::a50t_324_pin_to_iob_fmsh_to_xilinx $primitive_value_upper] != ""} {
           set iob_loc_value_a50t $::ip_patch::a50t::a50t_324_pin_to_iob_fmsh_to_xilinx($primitive_value_upper)
           set pin_325tffg900 $::ip_patch::a50t::xc7k325tffg900_iob_to_pin($iob_loc_value_a50t)
           set dst_line [format "%s %s %s %s" $str_set_property $str_loc $pin_325tffg900 $assigned_object]
#           set package_pin_line [format "%s" $::ip_patch::a50t::a50t_324_pin_to_pin_fmsh_to_xilinx($primitive_value_upper)]
           puts $file_w "#$line"
#           puts $file_w "#$package_pin_line"
           puts $file_w "#$iob_loc_value_a50t"
           puts $file_w $dst_line
           continue
        }
     } 
     puts $file_w $line
   }
   puts $file_w "\n\n#PACKAGE_ECOed"
   close $file_w
   puts [format "%s package maps succssfully!" $xdc_file_path]
   return 0
}
proc a50t_324_xdc_modify_xilinx_to_fmsh xdc_file_path {
  
   set eco_flag [get_xdc_package_eco_flag $xdc_file_path]
   if {$eco_flag == 1} {
      return
   }  
   source_file_backup $xdc_file_path

   set file_r [open $xdc_file_path "r"]
   set backup_str [read $file_r]
   close $file_r
  
   regsub -all "\n{2,}" $backup_str "\n" backup_str_1
   
   set file_backup_name_1 [format "%s.bak2" $xdc_file_path]
   set file_pointer_bk [open $file_backup_name_1 "w"]
   puts $file_pointer_bk $backup_str_1
   close $file_pointer_bk
 
   set inlist [split $backup_str_1 "\n"] 
   set file_w [open $xdc_file_path "w"] 
   
   foreach line $inlist {    
     if {[regexp -nocase {(^\s*set_property\s+package_pin\s+)(\w+)(.+)} $line dst_str dst_str_1 dst_str_primitive_value dst_str_2]} {
#set_property PACKAGE_PIN A18 [get_ports {tg_compare_error}]
        if {[array names ::ip_patch::a50t::a50t_324_pin_to_pin_xilinx_to_fmsh $dst_str_primitive_value] != ""} {
           set dst_str_primitive_value_upper [string toupper $dst_str_primitive_value]
           set dst_line [format "%s%s%s" $dst_str_1 $::ip_patch::a50t::a50t_324_pin_to_pin_xilinx_to_fmsh($dst_str_primitive_value_upper) $dst_str_2]
           set IOB_line [format "%s" $::ip_patch::a50t::a50t_324_pin_to_iob_xilinx_to_xilinx($dst_str_primitive_value_upper)]
           puts $file_w "#$line"
           puts $file_w "#$IOB_line"
           puts $file_w $dst_line
           continue
        }
     } elseif {[regexp -nocase {(^\s*set_property\s+loc\s+)(\w+)(.+)} $line dst_str dst_str_1 dst_str_primitive_value dst_str_2]} {
#       regexp -nocase {([a-z]\d+)} $str_sq str3 str4
        if {[array names ::ip_patch::a50t::a50t_324_pin_to_pin_xilinx_to_fmsh $dst_str_primitive_value] != ""} {
           set dst_str_primitive_value_upper [string toupper $dst_str_primitive_value]
           set dst_line [format "%s%s%s" $dst_str_1 $::ip_patch::a50t::a50t_324_pin_to_pin_xilinx_to_fmsh($dst_str_primitive_value_upper) $dst_str_2]
           set IOB_line [format "%s" $::ip_patch::a50t::a50t_324_pin_to_iob_xilinx_to_xilinx($dst_str_primitive_value_upper)]
           puts $file_w "#$line"
           puts $file_w "#$IOB_line"
           puts $file_w $dst_line
           continue
        }
     } 
     puts $file_w $line
   }
   puts $file_w "\n\n#PACKAGE_ECOed"
   close $file_w
   puts [format "%s package maps succssfully!" $xdc_file_path]
   return 0
}
proc a50t_484_xdc_modify_fmsh_pin_to_loc xdc_file_path {
  
   set eco_flag [get_xdc_package_eco_flag $xdc_file_path]
   if {$eco_flag == 1} {
      return
   }  
   source_file_backup $xdc_file_path

   set file_r [open $xdc_file_path "r"]
   set backup_str [read $file_r]
   close $file_r
  
   regsub -all "\n{2,}" $backup_str "\n" backup_str_1
   
   set file_backup_name_1 [format "%s.bak1" $xdc_file_path]
   set file_pointer_bk [open $file_backup_name_1 "w"]
   puts $file_pointer_bk $backup_str_1
   close $file_pointer_bk
 
   set inlist [split $backup_str_1 "\n"] 
   set file_w [open $xdc_file_path "w"] 
   
   foreach line $inlist {    
     if {[regexp -nocase {^\s*(set_property)\s+(package_pin)\s+(\w+)\s*(.+)} $line matched_str str_set_property str_package_pin primitive_value assigned_object]} {
#set_property PACKAGE_PIN A18 [get_ports {tg_compare_error}]
        set primitive_value_upper [string toupper $primitive_value]
        if {[array names ::ip_patch::a50t::a50t_484_pin_to_iob_fmsh_to_xilinx $primitive_value_upper] != ""} {
           set dst_line [format "%s LOC %s %s" $str_set_property $::ip_patch::a50t::a50t_484_pin_to_iob_fmsh_to_xilinx($primitive_value_upper) $assigned_object]
           set package_pin_line [format "%s" $::ip_patch::a50t::a50t_484_pin_to_pin_fmsh_to_xilinx($primitive_value_upper)]
           puts $file_w "#$line"
           puts $file_w "#$package_pin_line"
           puts $file_w $dst_line
           continue
        }
     } elseif {[regexp -nocase {^\s*(set_property)\s+(loc)\s+(\w+)\s*(.+)} $line matched_str str_set_property str_loc primitive_value assigned_object]} {
        set primitive_value_upper [string toupper $primitive_value]
        if {[array names ::ip_patch::a50t::a50t_484_pin_to_iob_fmsh_to_xilinx $primitive_value_upper] != ""} {
           set dst_line [format "%s %s %s %s" $str_set_property $str_loc $::ip_patch::a50t::a50t_484_pin_to_iob_fmsh_to_xilinx($primitive_value_upper) $assigned_object]
           set package_pin_line [format "%s" $::ip_patch::a50t::a50t_484_pin_to_pin_fmsh_to_xilinx($primitive_value_upper)]
           puts $file_w "#$line"
           puts $file_w "#$package_pin_line"
           puts $file_w $dst_line
           continue
        }
     } 
     puts $file_w $line
   }
   puts $file_w "\n\n#PACKAGE_ECOed"
   close $file_w
   puts [format "%s package maps succssfully!" $xdc_file_path]
   return 0
}
proc a50t_484_xdc_modify_fmsh_pin_to_loc_to_pin_325tffg900 xdc_file_path {
  
   set eco_flag [get_xdc_package_eco_flag $xdc_file_path]
   if {$eco_flag == 1} {
      return
   }  
   source_file_backup $xdc_file_path

   set file_r [open $xdc_file_path "r"]
   set backup_str [read $file_r]
   close $file_r
  
   regsub -all "\n{2,}" $backup_str "\n" backup_str_1
   
   set file_backup_name_1 [format "%s.bak1" $xdc_file_path]
   set file_pointer_bk [open $file_backup_name_1 "w"]
   puts $file_pointer_bk $backup_str_1
   close $file_pointer_bk
 
   set inlist [split $backup_str_1 "\n"] 
   set file_w [open $xdc_file_path "w"] 
   
   foreach line $inlist {    
     if {[regexp -nocase {^\s*(set_property)\s+(package_pin)\s+(\w+)\s*(.+)} $line matched_str str_set_property str_package_pin primitive_value assigned_object]} {
#set_property PACKAGE_PIN A18 [get_ports {tg_compare_error}]
        set primitive_value_upper [string toupper $primitive_value]
        if {[array names ::ip_patch::a50t::a50t_484_pin_to_iob_fmsh_to_xilinx $primitive_value_upper] != ""} {
           set iob_loc_value_a50t $::ip_patch::a50t::a50t_484_pin_to_iob_fmsh_to_xilinx($primitive_value_upper)
           set pin_325tffg900 $::ip_patch::a50t::xc7k325tffg900_iob_to_pin($iob_loc_value_a50t)
           set dst_line [format "%s PACKAGE_PIN %s %s" $str_set_property $pin_325tffg900 $assigned_object]
           puts $file_w "#$line"
#           puts $file_w "#$package_pin_line"
           puts $file_w "#$iob_loc_value_a50t"
           puts $file_w $dst_line
           continue
        }
     } elseif {[regexp -nocase {^\s*(set_property)\s+(loc)\s+(\w+)\s*(.+)} $line matched_str str_set_property str_loc primitive_value assigned_object]} {
        set primitive_value_upper [string toupper $primitive_value]
        if {[array names ::ip_patch::a50t::a50t_484_pin_to_iob_fmsh_to_xilinx $primitive_value_upper] != ""} {
           set iob_loc_value_a50t $::ip_patch::a50t::a50t_484_pin_to_iob_fmsh_to_xilinx($primitive_value_upper)
           set pin_325tffg900 $::ip_patch::a50t::xc7k325tffg900_iob_to_pin($iob_loc_value_a50t)
           set dst_line [format "%s %s %s %s" $str_set_property $str_loc $pin_325tffg900 $assigned_object]
#           set package_pin_line [format "%s" $::ip_patch::a50t::a50t_324_pin_to_pin_fmsh_to_xilinx($primitive_value_upper)]
           puts $file_w "#$line"
#           puts $file_w "#$package_pin_line"
           puts $file_w "#$iob_loc_value_a50t"
           puts $file_w $dst_line
           continue
        }
     } 
     puts $file_w $line
   }
   puts $file_w "\n\n#PACKAGE_ECOed"
   close $file_w
   puts [format "%s package maps succssfully!" $xdc_file_path]
   return 0
}
proc a50t_484_xdc_modify_xilinx_to_fmsh xdc_file_path {

   set eco_flag [get_xdc_package_eco_flag $xdc_file_path]
   if {$eco_flag == 1} {
      return
   } 
   source_file_backup $xdc_file_path

   set file_r [open $xdc_file_path "r"]
   set backup_str [read $file_r]
   close $file_r
  
   regsub -all "\n{2,}" $backup_str "\n" backup_str_1
   
   set file_backup_name_1 [format "%s.bak2" $xdc_file_path]
   set file_pointer_bk [open $file_backup_name_1 "w"]
   puts $file_pointer_bk $backup_str_1
   close $file_pointer_bk
 
   set inlist [split $backup_str_1 "\n"] 
   set file_w [open $xdc_file_path "w"] 
   
   foreach line $inlist {    
     if {[regexp -nocase {(^\s*set_property\s+package_pin\s+)(\w+)(.+)} $line dst_str dst_str_1 dst_str_primitive_value dst_str_2]} {
#set_property PACKAGE_PIN A18 [get_ports {tg_compare_error}]
        if {[array names ::ip_patch::a50t::a50t_484_pin_to_pin_xilinx_to_fmsh $dst_str_primitive_value] != ""} {
           set dst_str_primitive_value_upper [string toupper $dst_str_primitive_value]
           set dst_line [format "%s%s%s" $dst_str_1 $::ip_patch::a50t::a50t_484_pin_to_pin_xilinx_to_fmsh($dst_str_primitive_value_upper) $dst_str_2]
           set IOB_line [format "%s" $::ip_patch::a50t::a50t_484_pin_to_iob_xilinx_to_xilinx($dst_str_primitive_value_upper)]
           puts $file_w "#$line"
           puts $file_w "#$IOB_line"
           puts $file_w $dst_line
           continue
        }
     } elseif {[regexp -nocase {(^\s*set_property\s+loc\s+)(\w+)(.+)} $line dst_str dst_str_1 dst_str_primitive_value dst_str_2]} {
#       regexp -nocase {([a-z]\d+)} $str_sq str3 str4
        if {[array names ::ip_patch::a50t::a50t_484_pin_to_pin_xilinx_to_fmsh $dst_str_primitive_value] != ""} {
           set dst_str_primitive_value_upper [string toupper $dst_str_primitive_value]
           set dst_line [format "%s%s%s" $dst_str_1 $::ip_patch::a50t::a50t_484_pin_to_pin_xilinx_to_fmsh($dst_str_primitive_value_upper) $dst_str_2]
           set IOB_line [format "%s" $::ip_patch::a50t::a50t_484_pin_to_iob_xilinx_to_xilinx($dst_str_primitive_value_upper)]
           puts $file_w "#$line"
           puts $file_w "#$IOB_line"
           puts $file_w $dst_line
           continue
        }
     } 
     puts $file_w $line
   }
   puts $file_w "\n\n#PACKAGE_ECOed"
   close $file_w
   puts [format "%s package maps succssfully!" $xdc_file_path]
   return 0

}
proc add_fmk50rh_fmbh45_database {} {
	set vvd_version [string range [version -short] 0 5]
	if {$vvd_version != "2018.3" && $vvd_version != "2022.1"} {
        error "An error occurs!\nInfo:Current vvd_version:$vvd_version,not support add_fmk50t_database!(please use Vivado2022.1)"
    }
	fmsh_uninstall_device
	remove_fmk50rh_fmbh45_database
	recover_fmk230t_database
	set vvd_path [get_vvd_path]
	set current_prj_path [file join $::env(JFM_PATH)]
	set patch_data_path [file join $current_prj_path "ip_patch" "device_database" "fmk50rh_fmbh45" "fmsh" "$vvd_version" "data"]
	set vvd_data_path 	[file join $vvd_path "data"]
	set rd_path [findFiles $patch_data_path *]
	foreach rd_file $rd_path {
		set wr_file [regsub "$patch_data_path" $rd_file $vvd_data_path]
		if {[file exists $rd_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $rd_file no such file! "
		}
		if {[file exists $wr_file] == 0} {
			file copy -force $rd_file [file dir $wr_file]
		} else {
			file copy -force $rd_file $wr_file
		}
	}
	file copy -force [file join $current_prj_path "ip_patch" "device_database" "fmk50rh_fmbh45" "fmsh" "$vvd_version" "xc7k325t_fmk50t"] [file join $vvd_path "data" "parts" "xilinx" "artix7" "devint" "artix7"]
	file copy -force [file join $current_prj_path "ip_patch" "device_database" "fmk50rh_fmbh45" "fmsh" "$vvd_version" "xc7z045_fmbh45"] [file join $vvd_path "data" "parts" "xilinx" "zynq" "devint" "zynq"]
	####
	add_ip_database
	puts "FMSH->add_fmk50rh_fmbh45_database excuted successfully!(fmbh45 fmk50rh)"
	fmsh_send_msg_critical_warning "The first time you use the replace database command, you need to restart the current vivado!"
	
}
proc add_ip_database {} {
	set vvd_version [string range [version -short] 0 5]
	set vvd_path [get_vvd_path]
	if {$vvd_version != "2018.3" && $vvd_version != "2022.1" && $vvd_version != "2019.2"} {
        return
    }
	set current_prj_path [file join $::env(JFM_PATH)]
	replace_vv_index
	file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/fm7_device.lic                 $vvd_path/data/ip/core_licenses
	file delete -force $vvd_path/scripts/ip
	file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/scripts/$vvd_version/ip  $vvd_path/scripts
	#
	if {$vvd_version == "2018.3"} {
		file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/ips/$vvd_version/aurora_8b10b_v11_1/xgui/aurora_8b10b_v11_1.tcl 	$vvd_path/data/ip/xilinx/aurora_8b10b_v11_1/xgui/aurora_8b10b_v11_1.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/ips/$vvd_version/aurora_64b66b_v11_2/xgui/aurora_64b66b_v11_2.tcl 	$vvd_path/data/ip/xilinx/aurora_64b66b_v11_2/xgui/aurora_64b66b_v11_2.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/ips/$vvd_version/xdma_v4_1/xgui/xdma_v4_1.tcl	 					$vvd_path/data/ip/xilinx/xdma_v4_1/xgui/xdma_v4_1.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/ips/$vvd_version/cpri_v8_9/xgui/cpri_v8_9.tcl	 							$vvd_path/data/ip/xilinx/cpri_v8_9/xgui/cpri_v8_9.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/ips/$vvd_version/jesd204_phy_v4_0/xgui/jesd204_phy_v4_0.tcl	 				$vvd_path/data/ip/xilinx/jesd204_phy_v4_0/xgui/jesd204_phy_v4_0.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/ips/$vvd_version/jesd204_v7_2/xgui/jesd204_v7_2.tcl	 						$vvd_path/data/ip/xilinx/jesd204_v7_2/xgui/jesd204_v7_2.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/ips/$vvd_version/vid_phy_controller_v2_2/xgui/vid_phy_controller_v2_2.tcl	$vvd_path/data/ip/xilinx/vid_phy_controller_v2_2/xgui/vid_phy_controller_v2_2.tcl
		
		file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/$vvd_version/xc7z045_fmql15.xng $vvd_path/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015.xng
		
	} elseif {$vvd_version == "2022.1"} {
		file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/ips/$vvd_version/aurora_8b10b_v11_1/xgui/aurora_8b10b_v11_1.tcl 	$vvd_path/data/ip/xilinx/aurora_8b10b_v11_1/xgui/aurora_8b10b_v11_1.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/ips/$vvd_version/aurora_64b66b_v12_0/xgui/aurora_64b66b_v12_0.tcl 	$vvd_path/data/ip/xilinx/aurora_64b66b_v12_0/xgui/aurora_64b66b_v12_0.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/ips/$vvd_version/xdma_v4_1/xgui/xdma_v4_1.tcl	 					$vvd_path/data/ip/xilinx/xdma_v4_1/xgui/xdma_v4_1.tcl	
		file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/ips/$vvd_version/jesd204_phy_v4_0/xgui/jesd204_phy_v4_0.tcl	 		$vvd_path/data/ip/xilinx/jesd204_phy_v4_0/xgui/jesd204_phy_v4_0.tcl	
		
		file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/$vvd_version/xc7z045_fmql15.xng $vvd_path/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015.xng
			
	} elseif {$vvd_version == "2019.2"} {
		file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/ips/$vvd_version/aurora_8b10b_v11_1/xgui/aurora_8b10b_v11_1.tcl 	$vvd_path/data/ip/xilinx/aurora_8b10b_v11_1/xgui/aurora_8b10b_v11_1.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/ips/$vvd_version/aurora_64b66b_v12_0/xgui/aurora_64b66b_v12_0.tcl 	$vvd_path/data/ip/xilinx/aurora_64b66b_v12_0/xgui/aurora_64b66b_v12_0.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/ips/$vvd_version/xdma_v4_1/xgui/xdma_v4_1.tcl	 					$vvd_path/data/ip/xilinx/xdma_v4_1/xgui/xdma_v4_1.tcl	
		file copy -force $current_prj_path/ip_patch/device_database/common/fmsh/ips/$vvd_version/jesd204_phy_v4_0/xgui/jesd204_phy_v4_0.tcl	 		$vvd_path/data/ip/xilinx/jesd204_phy_v4_0/xgui/jesd204_phy_v4_0.tcl	
	
	}
	
	set patch_mig_path 	[file join $current_prj_path "ip_patch" "device_database" "common" "fmsh" "$vvd_version" "mig_7series_v4_2"]
	set vvd_mig_path 	[file join $vvd_path "data" "ip" "xilinx" "mig_7series_v4_2"]
	set rd_path [findFiles $patch_mig_path *]
	foreach rd_file $rd_path {
		set wr_file [regsub "$patch_mig_path" $rd_file $vvd_mig_path]
		if {[file exists $rd_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $rd_file no such file! "
		}
		if {[file exists $wr_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $rd_file no such file! "
		}
		file copy -force $rd_file $wr_file
	}
}
proc add_jfmql70tai_jfmql100t_jfmql100tai_database {} {
	remove_jfmql70tai_jfmql100t_jfmql100tai_database
	set vvd_version [string range [version -short] 0 5]
	puts "Current Vivado version:$vvd_version"
	if {$vvd_version != "2018.3" &&  $vvd_version != "2019.2"} {
	     error "FMSH->This command only support in Vivado2018.3 or Vivado2019.2!"
	}
	add_ip_database
	
	set vvd_path [get_vvd_path]
	set current_prj_path [file join $::env(JFM_PATH)]
	
	if {[check_current_platform] == "windows"} {
		file rename -force [file join $vvd_path "lib" "win64.o" "librdi_common.dll"] [file join $vvd_path "lib" "win64.o" "librdi_common.dll_bak"]
		file copy -force [file join $current_prj_path "ip_patch" "device_database"  "7z100t_7z100tai_7z70tai" "dll" $vvd_version "librdi_common.dll"] [file join $vvd_path "lib" "win64.o" "librdi_common.dll"]
	} else {
		if {$vvd_version == "2019.2"} {
			error "FMSH->This command is not support in Vivado2019.2(linux)!"
		}
		file rename -force [file join $vvd_path "lib" "lnx64.o" "librdi_common.so"] [file join $vvd_path "lib" "lnx64.o" "librdi_common.so_bak"]
		file copy -force [file join $current_prj_path "ip_patch" "device_database"  "7z100t_7z100tai_7z70tai" "dll" $vvd_version "librdi_common.so"] [file join $vvd_path "lib" "lnx64.o" "librdi_common.so"]
	}
	set patch_data_path  [file join $current_prj_path "ip_patch" "device_database"  "7z100t_7z100tai_7z70tai" "fmsh"]
	set vivado_data_path [file join $vvd_path]
	set rd_path [findFiles $patch_data_path *]
	foreach rd_file $rd_path {
		set wr_file [regsub "$patch_data_path" $rd_file $vivado_data_path]
		if {[file exists $rd_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $rd_file no such file! "
		}
		if {[file exists $wr_file] == 0} {
			file copy -force $rd_file [file dir $wr_file]
		} else {
			file copy -force $rd_file $wr_file
		}
	}
	file copy -force [file join $current_prj_path "ip_patch" "device_database"  "7z100t_7z100tai_7z70tai"  "xc7z100_jfmql70tai"] [file join $vvd_path "data" "parts" "xilinx" "zynq" "devint" "zynq"]
	file copy -force [file join $current_prj_path "ip_patch" "device_database"  "7z100t_7z100tai_7z70tai"  "xc7z100_jfmql100t"] [file join $vvd_path "data" "parts" "xilinx" "zynq" "devint" "zynq"]
	file copy -force [file join $current_prj_path "ip_patch" "device_database"  "7z100t_7z100tai_7z70tai"  "xc7z100_jfmql100tai"] 	[file join $vvd_path "data" "parts" "xilinx" "zynq" "devint" "zynq"]
	puts "FMSH->add_jfmql70tai_jfmql100t_jfmql100tai_database excuted successfully(jfmql70tai/jfmql100t/jfmql100tai)!"	
	fmsh_send_msg_critical_warning "The first time you use the replace database command, you need to restart the current vivado!"
}
proc database_check str_list {
	set msg_serverity [get_msg_serverity_value $str_list]
	if {$msg_serverity == "CRITICAL"} {
		set msg_serverity "CRITICAL WARNING"
	}
	set vvd_path [get_vvd_path]
	set vvd_version [string range [version -short] 0 5]
	set project_path [get_property DIRECTORY [current_project]]
	set device_part  [get_property PART [current_project]]
    set out_file_path [file join $project_path "database_check.log"]
	set f [open $out_file_path "w"]
	puts $f "#This file records which devices have replaced the database!#"
	puts $f "#Vivado Path:$vvd_path#"
	puts $f "#IP Patch version in project root directory:$::ip_patch::version#"
	#7z045ai GTX
	set fmql45_aix_flag 0
	set fmql45_aih_flag 0
	set jfmql30ai_flag  0
	set jfmql100_flag   0
	set jfmql100ai_flag 0
	set fmk50_flag      0
	set fmk230t_flag    0
	set fmql15_flag     0
	set fmbh45_flag     0
	set jfmql70ai_flag  0
	
	set xc7z045_rtd_vvd [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z045/xc7z045.rtd" $vvd_path]
	if {[file exist $xc7z045_rtd_vvd]} {
		set md5_vvd  [md5::md5 -hex -file $xc7z045_rtd_vvd]
		if {$md5_vvd == "0963501876F62484AB5DE30A55B2F26D"} {
			send_msg_id {fmsh-2024} "$msg_serverity" "FMSH-->Current Project replaced xc7z045 AI GTX database!([clock format [clock seconds]])"
			puts $f "FMQL45T900-AIX"
		}
	}
	#7z045ai GTH
	set PartStats_xml_vvd [format "%s/data/parts/xilinx/zynq/devint/zynq/PartStats.xml" $vvd_path]
	if {[file exist $PartStats_xml_vvd]} {
		set md5_vvd  [md5::md5 -hex -file  $PartStats_xml_vvd]
		if {$md5_vvd == "962B8423427B5443831B20E8561842BF"} {
			send_msg_id {fmsh-2024} "$msg_serverity" "FMSH-->Current Project replaced xc7z045 AI GTH database!([clock format [clock seconds]])"
			puts $f "FMQL45T900-AIH"
		}
	}
	
	#7z030ai
	set Sitemap2_xml_vvd    [format "%s/data/parts/xilinx/zynq/devint/Sitemap2.xml" $vvd_path]
	set zynq_padr_vvd 		[format "%s/data/parts/xilinx/zynq/devint/zynq.padr" $vvd_path]
	if {[file exist $Sitemap2_xml_vvd]} {
		set md5_vvd   [md5::md5 -hex -file $Sitemap2_xml_vvd]
		set md5_vvd1   [md5::md5 -hex -file $zynq_padr_vvd]
		if {$md5_vvd == "0A5A0A3AC5757CB770D68AF1A13D5FCE" && $md5_vvd1 == "0C37BD43ED4E544A36A79E3018A975F1"} {
			send_msg_id {fmsh-2024} "$msg_serverity" "FMSH-->Current Project replaced xc7z030 AI database!([clock format [clock seconds]])"
			puts $f "JFMQL30T-AI"
		}
	}
	

	#7z100ai
	set Sitemap2_xml_vvd    [format "%s/data/parts/xilinx/zynq/devint/Sitemap2.xml" $vvd_path]
	if {[file exist $Sitemap2_xml_vvd]} {
		set md5_vvd  [md5::md5 -hex -file $Sitemap2_xml_vvd]
		if {$md5_vvd == "E24F9113DC62D503E9C4DCD90A50C91B"} {
			send_msg_id {fmsh-2024} "$msg_serverity" "FMSH-->Current Project replaced xc7z100 AI database!([clock format [clock seconds]])"
			puts $f "JFMQL100TAI900"
		}
	}

	#7z100
	set zynq_pspd_vvd       [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z100/xc7z100.paspd" $vvd_path]
	if {[file exist $zynq_pspd_vvd]} {
		set md5_vvd  [md5::md5 -hex -file $zynq_pspd_vvd]
		if {$md5_vvd == "0EB734E958E1CF1FDAF2937F66338D95" || $md5_vvd == "2707B9F11B48B71AAD5CFFCDB8D98FFF" || $md5_vvd == "940A60C71B3504089FBAD2A41710DA60"} {
			send_msg_id {fmsh-2024} "$msg_serverity" "FMSH-->Current Project replaced xc7z100 database!([clock format [clock seconds]])"
			puts $f "JFMQL100T900"
		}
	}
	#50t
	set ClockRegion_xml_vvd [format "%s/data/parts/xilinx/artix7/devint/artix7/xc7a50t/ClockRegion.xml" $vvd_path]	
	if {[file exist $ClockRegion_xml_vvd]} {
		set md5_vvd  [md5::md5 -hex -file $ClockRegion_xml_vvd]
		if {$md5_vvd == "9967BA8D16ABCD202564293F35307D6A"} {
			send_msg_id {fmsh-2024} "$msg_serverity" "FMSH-->Current Project replaced 50T database!([clock format [clock seconds]])"
			puts $f "JFMK50T/FMK50T"
		}
	}
	
	#fmk230t
	set fmk230t [format "%s/data/parts/xilinx/kintex7/devint/tileCategory.cfg" $vvd_path]	
	if {[file exist $fmk230t]} {
		set md5_vvd  [md5::md5 -hex -file $fmk230t]
		if {$md5_vvd == "7FB2A859C7855CD2DDB8D0B3FED0E9F0"} {
			send_msg_id {fmsh-2024} "$msg_serverity" "FMSH-->Current Project replaced FMK230T database!([clock format [clock seconds]])"
			puts $f "FMK230T(replace database flow)"
		}
	}
	
	#jfmql70tai jfmql100t jfmql100tai 
	set jfmql70tai [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z100_jfmql70tai" $vvd_path]
	set zynq_padr_vvd 		[format "%s/data/parts/xilinx/zynq/devint/zynq.padr" $vvd_path]
	if {[file exist $jfmql70tai]} {
		set md5_vvd1   [md5::md5 -hex -file $zynq_padr_vvd]
		if {$md5_vvd1 == "0524377A5794FFB79750C19EEDDF072F"} {	
		}
		send_msg_id {fmsh-2024} "$msg_serverity" "FMSH-->Current Project replaced jfmql70tai/jfmql100t/jfmql100tai database!([clock format [clock seconds]])"
		puts $f "jfmql70tai/jfmql100t/jfmql100tai"
	}
	
	
	#fmk230t fmk300t fmql15
	set fmql15 [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z045_fmql15" $vvd_path]
	if {[file exist $fmql15]} {
		send_msg_id {fmsh-2024} "$msg_serverity" "FMSH-->Current Project replaced FMK230T/FMK300T/FMQL15 database!([clock format [clock seconds]])"
		puts $f "FMK230T/FMK300T/FMQL15"
	}
	#fmk50rh fmbh45
	set fmk50rh [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z045_fmbh45" $vvd_path]
	if {[file exist $fmk50rh]} {
		send_msg_id {fmsh-2024} "$msg_serverity" "FMSH-->Current Project replaced FMK50RH/FMBH45 database!([clock format [clock seconds]])"
		puts $f "FMK50RH/FMBH45"
	}
	close $f
	puts "FMSH->$out_file_path is generated successfully!"
 }
proc fmsh_1553b_modify {} {
    set ips [get_ips -filter {IPDEF =~ "fmsh.com:user:FMSH1553BRM:*"} -quiet]
	set ip_num [llength $ips]
	if {$ip_num == 0} {
	    puts "No fmsh_1553b IP find in current project!"
	} else {
	    puts "Critical Warning:Find $ip_num fmsh_1553b IP in current project!"

        foreach ip $ips {
		    set ip_dir [get_ip_dir $ip]
			set top_file [format "%s/synth/%s.v" $ip_dir $ip]
			fmsh_1553b_top_file_modify $ip $top_file	
		}		
	
	}
}
proc fmsh_1553b_top_file_modify {ip top_file} {

	set ip_core_container_flag [get_property IP_CORE_CONTAINER [get_ips $ip]]
    if  {$ip_core_container_flag != ""} {
        error "Error occurs! \nInfo: IP $ip enables core container, and our patch doesn't support core container. Please disable core container of this IP.\n"
    }
	
	set ip_run [format "%s_synth_1" $ip]
    set run [get_runs $ip_run -quiet]
    if {[llength $run] == 0} {
        error "Error occurs! \nInfo: IP $ip have not been synthesised by OOC mode or the cache option in the Project Settings is not disabled!"
    }
	
    if {[file exists $top_file] == 0 } {
	    error "An error occurs:\n Can't find $top_file in current project!"
	}

	
	puts "Start modify $ip RTL:"
	set filein [open $top_file "r"]
    set in_list_top_file [split [read $filein] "\n"]
    close $filein
	set fileout [open $top_file "w"]
	foreach line $in_list_top_file {
	    if {[regexp {.dna_enable\(1\)} $line]} {
		    puts $fileout {  .dna_enable(0)}
		    continue
		}
		puts $fileout $line
	}
	
	close $fileout
	
	set total_CPU_threads [get_CPU_threads_cross_platform]
    puts "total_CPU_threads = $total_CPU_threads"
	reset_run $run
    launch_run -jobs $total_CPU_threads $run
	
	puts "Modify IP $ip: $top_file RTL successfully!"
	
}
proc fmsh_bh_bram_eco {mode path} {
	if {$mode == "ALL"} {
		puts "FMSH-->Current mode is ALL:"
		set ram_list [get_cells -hier -filter {REF_NAME == "RAMB18E1" && PRIMITIVE_LEVEL == "LEAF" || REF_NAME == "RAMB36E1" && PRIMITIVE_LEVEL == "LEAF"} -quiet]
		filter_cascade_bram $ram_list
		puts "FMSH-->Total [llength $ram_list] BRAMs"
		foreach ram $ram_list {
			if {[filter_ecoed_bram $ram] != 1} {
				duplicate_bram_cell_net $ram
			}	
		}
	} elseif {$mode == "NONEZERO"} {
		puts "FMSH-->Current mode is NONEZERO:"
		set ram_list [filter_nonezero_ram]
		filter_cascade_bram $ram_list
		puts "FMSH-->Total [llength $ram_list] BRAMs"
		foreach ram $ram_list { 
			if {[wea_web_check $ram]} {
				puts "$ram is not a ROM!"
				continue 
			}
			if {[filter_ecoed_bram $ram] != 1} {
				duplicate_bram_cell_net $ram
			}
		}
	} elseif {$mode == "READ_FILE"} {
		puts "FMSH-->Current mode is READ_FILE:"
		if {[file exists $path] == 0} {
			error "FMSH-->ERROR:Current mode is READ_FILE,but the file is not existing!"
		}
		set fp [open $path "r"]
		set ram_list [split [read $fp] "\n"]
		close $fp
		filter_cascade_bram $ram_list
		puts "FMSH-->Total [llength $ram_list] BRAMs"
		foreach ram $ram_list {
			if {[filter_ecoed_bram $ram] != 1} {
				duplicate_bram_cell_net $ram
			}
		}
	}
	puts "FMSH-->fmsh_bh_bram_eco excuted successfully!"

}
proc fmsh_drc_common_clk_blk {} {

}
proc fmsh_drc_no_clock_check {} {
	check_timing -exclude {constant_clock pulse_width_clock unconstrained_internal_endpoints no_input_delay no_output_delay multiple_clock generated_clocks loops partial_input_delay partial_output_delay latch_loops }  -file ./no_clock_check.rpt
	set f [open ./no_clock_check.rpt "r"]
	set inlist [split [read $f] "\n"]
	close $f
	set cnt 0
	foreach ele $inlist {
		if {[regexp {There\s+are\s+9\s+register\/latch\s+pins\s+with\s+no\s+clock} $ele]} {
			set cnt 1
		} 
	}
	if {$cnt == 1} {
		fmsh_send_msg_critical_warning_drc "check_timing find no clock pins,please click Reports->Timing->Check Timing to check!" 
	}
}
proc fmsh_drc_report_cdc_critical {} {
	report_cdc -severity  Critical -file ./report_cdc.rpt
	set f [open ./report_cdc.rpt "r"]
	set inlist [split [read $f] "\n"]
	close $f
	set cnt 0
	foreach ele $inlist {
		puts "ele:$ele"
		if {[regexp -nocase {critical} $ele ]} {
			incr cnt
		}
	}
	if {$cnt > 1} {
		fmsh_send_msg_critical_warning_drc "report_cdc find Critical timing paths,please click Reports->Timing->Report CDC to check!" 
	}
}
proc fmsh_install_device {} {
	set vvd_version [string range [version -short] 0 5]
	if {$vvd_version != "2018.3" && $vvd_version != "2022.1"} {
	     error "FMSH->This command may not right,current vivado version is $vvd_version!"
	}
	fmsh_uninstall_device
	remove_fmk50rh_fmbh45_database
	recover_fmk230t_database
	
	add_ip_database
	set vvd_path  [get_vvd_path]
	set current_prj_path [file join $::env(JFM_PATH)]
	if {$vvd_version == "2018.3"} {
		file copy -force [format "%s/ip_patch/device_database/fmk230t/xilinx/HARC.cfg" $current_prj_path] [format "%s/data/parts/xilinx/common/HARC.cfg" $vvd_path] 
	}
	set vvd_path [get_vvd_path]
	set current_prj_path [file join $::env(JFM_PATH)]
	set patch_data_path  [file join $current_prj_path "ip_patch" "device_database"  "fmk230t_fmk300t_fmql15" "fmsh" "data"]
	set vivado_data_path [file join $vvd_path "data"]
	set rd_path [findFiles $patch_data_path *]
	foreach rd_file $rd_path {
		set wr_file [regsub "$patch_data_path" $rd_file $vivado_data_path]
		if {[file exists $rd_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $rd_file no such file! "
		}
		if {[file exists $wr_file] == 0} {
			file copy -force $rd_file [file dir $wr_file]
		} else {
			file copy -force $rd_file $wr_file
		}
	}
	file copy -force [file join $current_prj_path "ip_patch" "device_database"  "fmk230t_fmk300t_fmql15" "fmsh" "xc7k325t_fmk230t"] [file join $vvd_path "data" "parts" "xilinx" "kintex7" "devint" "kintex7"]
	file copy -force [file join $current_prj_path "ip_patch" "device_database"  "fmk230t_fmk300t_fmql15" "fmsh" "xc7k325t_fmk300t"] [file join $vvd_path "data" "parts" "xilinx" "kintex7" "devint" "kintex7"]
	file copy -force [file join $current_prj_path "ip_patch" "device_database"  "fmk230t_fmk300t_fmql15" "fmsh" "xc7z045_fmql15"] 	[file join $vvd_path "data" "parts" "xilinx" "zynq" "devint" "zynq"]
	file copy -force [file join $current_prj_path "ip_patch" "device_database"  "fmk230t_fmk300t_fmql15" "fmsh" "validate_update.tcl"] [file join $vvd_path "data" "ip" "xilinx" "processing_system7_v5_5" "xgui" "validate_update.tcl"]
	
	puts "FMSH->fmsh_install_device excuted successfully(fmk300t fmk230t fmql15)!"	
	fmsh_send_msg_critical_warning "The first time you use the replace database command, you need to restart the current vivado!"
}
proc fmsh_pcie_drp_eco clock_source_value {
	# set fmsh_dna_net [get_nets -hier -filter {NAME =~ "*fmsh_pcie_drp_fpgav05"}]
	# set fmsh_dna_ok_net [get_nets -hier -filter {NAME =~ "*fmsh_pcie_drp_fpga_dna_ok"}]
	set fmsh_dna_pin    [get_pins -of [get_cells -hier -filter {NAME =~ "*fmsh_pcie_drp_fpgav05_reg1_reg"}] -filter {REF_PIN_NAME == D} ]
	set fmsh_dna_ok_pin [get_pins -of [get_cells -hier -filter {NAME =~ "*fmsh_pcie_drp_fpga_dna_ok_reg1_reg"}] -filter {REF_PIN_NAME == D} ]

	set fmsh_dna_net [get_nets -of  [get_pins $fmsh_dna_pin]]
	set fmsh_dna_ok_net [get_nets -of [get_pins $fmsh_dna_ok_pin]]
	
	if {$fmsh_dna_net == ""} {
		return
	}
	 set dna_port_cell [get_cells -hier -filter {REF_NAME == "DNA_PORT" && PRIMITIVE_LEVEL == "LEAF"} -quiet]
	 if {[get_cells $dna_port_cell] != ""} {
		error "An exception occurs:\nFind USER DNA: $dna_port_cell cell in project!\nPlease contact FAE for help!"
	 }
	
	
	set current_prj_path [file join [pwd] "../.."]
	set dna_check_edif [file join $current_prj_path "ip_patch" "edif" "dna_check.edif"]
	add_dna_check_logic_bram $dna_check_edif
	if {[get_cells -hier -filter {NAME =~ "*msh_dna_check_logic"}] != ""} {
	    set dna_check_logic_cell [get_cells -hier -filter {NAME =~ "*msh_dna_check_logic"}]
		set dna_check_valid_pin [get_pins [format "%s/valid" $dna_check_logic_cell]]
	    set dna_check_valid_complete_pin [get_pins [format "%s/valid_complete" $dna_check_logic_cell]]
		set dna_check_clk_pin [get_pins [format "%s/clk" $dna_check_logic_cell]]
	} else {
	    set dna_check_logic_cell  [get_cells -hier -filter {REF_NAME == "DNA_PORT" && PRIMITIVE_LEVEL == "LEAF"} -quiet]
	}
	#create gnd
	set lut1 fmsh_pcie_drp
	set gnd_name [format "%s_gnd" $lut1]
    create_cell -reference gnd $gnd_name  
	set gnd_pin [get_pins [format "%s/G" $gnd_name]]
	
	#reset lut2
	set lut2_reset [format "%s_lut2_reset"  $lut1]
	create_cell -reference LUT2 $lut2_reset
	set_property INIT 4'h1 [get_cells $lut2_reset]  
	set lut2_reset_I0_pin [get_pins [format "%s/I0" $lut2_reset]]
	set lut2_reset_I1_pin [get_pins [format "%s/I1" $lut2_reset]]
	set lut2_reset_O_pin [get_pins [format "%s/O" $lut2_reset]]
	
	#valid lut2
	set lut2_valid [format "%s_lut2_valid"  $lut1]
	create_cell -reference LUT2 $lut2_valid
	set_property INIT 4'hD [get_cells $lut2_valid]  
	set lut2_valid_I0_pin [get_pins [format "%s/I0" $lut2_valid]]
	set lut2_valid_I1_pin [get_pins [format "%s/I1" $lut2_valid]]
	set lut2_valid_O_pin [get_pins [format "%s/O" $lut2_valid]]
	set gnd_net [create_net [format "%s_gnd_net" $lut1]]
	set lut2_valid_O_net [create_net [format "%s_lut2_valid_O_net" $lut1]]
	
	#connect gnd to lut2 reset I0
	connectNet $gnd_net $gnd_pin
	connectNet $gnd_net $lut2_reset_I0_pin
	
	
	set valid_net [create_net [format "%s_valid_net" $dna_check_logic_cell]] 
	set valid_complete_net [create_net [format "%s_valid_complete_net" $dna_check_logic_cell]]
		
	connectNet $valid_net  $lut2_valid_I1_pin 
	connectNet $valid_net  $dna_check_valid_pin
	
	connectNet $valid_complete_net $lut2_valid_I0_pin
	connectNet $valid_complete_net $dna_check_valid_complete_pin
	
	connectNet $lut2_valid_O_net $lut2_valid_O_pin
	connectNet $lut2_valid_O_net $lut2_reset_I1_pin
	#get clock source
	if {$clock_source_value == "NONE"} {
		set startupe2_cell [get_cells -hier -filter {REF_NAME == "STARTUPE2" && PRIMITIVE_LEVEL == "LEAF"}]
		if {[get_cells $startupe2_cell] == ""} {
			create_cell -reference STARTUPE2 fmsh_pcie_drp_clk
			set clock_source_value [create_net fmsh_pcie_drp_clk_net]
			connectNet $clock_source_value fmsh_pcie_drp_clk/CFGMCLK
			create_clock -period 15 [get_pins fmsh_pcie_drp_clk/CFGMCLK]
		} else {
			set clock_source_value [get_nets -of [get_pins $startupe2_cell/CFGMCLK]]
			if {[get_nets $clock_source_value] == ""} {
				set clock_source_value [create_net fmsh_pcie_drp_clk_net]
				connectNet $clock_source_value fmsh_pcie_drp_clk/CFGMCLK
				create_clock -period 15 [get_pins fmsh_pcie_drp_clk/CFGMCLK]
			}
		}
	} else {
		if {[get_nets $clock_source_value] == ""} {
			error "FMSH->Can't find clk src: $clock_source_value in current netlist!(pcie drp eco)"
		}
	}
	connectNet [get_nets $clock_source_value] $dna_check_clk_pin
	set pcie_drp_dna_net [create_net pcie_drp_dna_net] 
	connectNet $pcie_drp_dna_net $lut2_reset_O_pin
	foreach net $fmsh_dna_net {
		set_property DONT_TOUCH	0 [get_nets $net]
		set pin1 [get_pins -of_objects [get_nets $net] -filter {DIRECTION == IN}]
		disconnectNet  $net $pin1
		connectNet $pcie_drp_dna_net $pin1
	}
	foreach net $fmsh_dna_ok_net {
		set_property DONT_TOUCH	0 [get_nets $net]
		set pin1 [get_pins -of_objects [get_nets $net] -filter {DIRECTION == IN}]
		disconnectNet  $net $pin1
		connectNet $valid_complete_net $pin1
	}
	set_false_path -from [get_pins bram_fmsh_dna_check_logic/complete_reg/C] -to [get_pins -hier -filter {NAME =~ "*fmsh_pcie_drp_fpgav05_reg1_reg/D"}]
	set_false_path -from [get_pins bram_fmsh_dna_check_logic/complete_reg/C] -to [get_pins -hier -filter {NAME =~ "*fmsh_pcie_drp_fpga_dna_ok_reg1_reg/D"}]
	set_false_path -from [get_pins bram_fmsh_dna_check_logic/valid_inter_reg/C] -to [get_pins -hier -filter {NAME =~ "*fmsh_pcie_drp_fpgav05_reg1_reg/D"} ]
}
proc fmsh_psoc_database_check {} {
	puts "Start fmsh_psoc_database_check now!"
	set device_part [get_property PART [current_project]]
	set vvd_path [get_vvd_path]
	if {[regexp {^xc7z010} $device_part]} {
		if {[get_pins -hierarchical  *AI_CLK21] != "" && [get_pins -hierarchical  *AI_IN2023] != ""} {
			error "FMSH-->Current project device part is $device_part,but find AI pins in netlist,please check your vivado database!"
		}
	} elseif {[regexp {xc7z015} $device_part]} {
		if {[get_pins -hierarchical  *AI_CLK21] != "" && [get_pins -hierarchical  *AI_IN2023] != ""} {
			error "FMSH-->Current project device part is $device_part,but find AI pins in netlist,please check your vivado database!"
		}
	} elseif {[regexp {^xc7z020} $device_part]} {
		if {[get_pins -hierarchical  *AI_CLK21] != "" && [get_pins -hierarchical  *AI_IN2023] != ""} {
			error "FMSH-->Current project device part is $device_part,but find AI pins in netlist,please check your vivado database!"
		}
	} elseif {[regexp {xc7z030} $device_part]} {
		set Sitemap2_xml_vvd    [format "%s/data/parts/xilinx/zynq/devint/Sitemap2.xml" $vvd_path]
		set zynq_padr_vvd 		[format "%s/data/parts/xilinx/zynq/devint/zynq.padr" $vvd_path]
		if {[file exist $Sitemap2_xml_vvd]} {
			set md5_vvd  	[md5::md5 -hex -file $Sitemap2_xml_vvd]
			set md5_vvd1   	[md5::md5 -hex -file $zynq_padr_vvd]
			if {$md5_vvd == "0A5A0A3AC5757CB770D68AF1A13D5FCE" && $md5_vvd1 == "0C37BD43ED4E544A36A79E3018A975F1"} {
			} else {
				error "FMSH-->Current project device part is $device_part,but database check is not right,please check your vivado database!"
			}
		}
	} elseif {[regexp {^xc7z045f} $device_part]} {
		set flag_045ai [format "%s/data/parts/xilinx/zynq/devint/zynq.rtd.bak" $vvd_path]
		if {[file exist $flag_045ai]} {
		} else {
			if {[get_pins -hierarchical  *AI_CLK21] != "" && [get_pins -hierarchical  *AI_IN2023] != ""} {
				error "FMSH-->Current project device part is $device_part,but find AI pins in netlist,please check your vivado database!"
			}
		}
	} else {
		return
	}
	
}
proc fmsh_send_msg_critical_warning msg {
	send_msg_id {fmsh-2023} "CRITICAL WARNING" "${msg}"
}
proc fmsh_send_msg_critical_warning_drc msg {
	send_msg_id {fmsh-2024} "CRITICAL WARNING" "${msg}"
}
proc fmsh_send_msg_warning msg {
	send_msg_id {fmsh-2023} "WARNING" "${msg}"
}
proc fmsh_uninstall_device {} {
	set vvd_version [string range [version -short] 0 5]
	if {$vvd_version != "2018.3" && $vvd_version != "2022.1"} {
	     error "FMSH->This command may not right,current vivado version is $vvd_version!"
	}
	set vvd_path [get_vvd_path]
	set current_prj_path [file join $::env(JFM_PATH)]
	set patch_data_path [file join $current_prj_path "ip_patch" "device_database" "fmk230t_fmk300t_fmql15" "xilinx" "$vvd_version" "data"]
	set vvd_data_path 	[file join $vvd_path "data"]
	set rd_path [findFiles $patch_data_path *]
	foreach rd_file $rd_path {
		set wr_file [regsub "$patch_data_path" $rd_file $vvd_data_path]
		if {[file exists $rd_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $rd_file no such file! "
		}
		if {[file exists $wr_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $wr_file no such file! "
		} 
		file copy -force $rd_file $wr_file
	}
	file delete -force [file join $vvd_path "data" "parts" "xilinx" "kintex7" "devint" "kintex7" "xc7k325t_fmk230t"]
	set file_list [glob -nocomplain $vvd_path/data/parts/xilinx/kintex7/public/bsdl/xc7k325t_fmk230t_*]
	foreach file $file_list {file delete -force $file}
	set file_list [glob -nocomplain $vvd_path/data/parts/xilinx/kintex7/public/ibis/pkg/xc7k325t_fmk230t_*]
	foreach file $file_list {file delete -force $file}
	
	
	file delete -force [file join $vvd_path "data" "parts" "xilinx" "kintex7" "devint" "kintex7" "xc7k325t_fmk300t"]
	set file_list [glob -nocomplain $vvd_path/data/parts/xilinx/kintex7/public/bsdl/xc7k325t_fmk300t_*]
	foreach file $file_list {file delete -force $file}
	set file_list [glob -nocomplain $vvd_path/data/parts/xilinx/kintex7/public/ibis/pkg/xc7k325t_fmk300t_*]
	foreach file $file_list {file delete -force $file}
	
	file delete -force [file join $vvd_path "data" "parts" "xilinx" "zynq" "devint" "zynq" "xc7z045_fmql15"]
	set file_list [glob -nocomplain $vvd_path/data/parts/xilinx/zynq/public/bsdl/xc7z045_fmql15_*]
	foreach file $file_list {file delete -force $file}
	set file_list [glob -nocomplain $vvd_path/data/parts/xilinx/zynq/public/ibis/pkg/xc7z045_fmql15_*]
	foreach file $file_list {file delete -force $file}
	remove_ip_database
	
	file copy -force [file join $current_prj_path "ip_patch" "device_database"  "fmk230t_fmk300t_fmql15" "xilinx" "validate_update.tcl"] [file join $vvd_path "data" "ip" "xilinx" "processing_system7_v5_5" "xgui" "validate_update.tcl"]
	
	puts "FMSH->fmsh_uninstall_device excuted successfully!"	
}
proc get_fmsh_1553b_value str_list {
    set dst_index [lsearch $str_list -fmsh_1553b]
    if {$dst_index >= 0} {
        set fmsh_1553b_value [lindex $str_list [expr $dst_index+1]]
        if {$fmsh_1553b_value == "TRUE" || $fmsh_1553b_value == "true"} {
		    set fmsh_1553b_value "TRUE" 
        } elseif {$fmsh_1553b_value == "FALSE" || $fmsh_1553b_value == "false" } {
		    set fmsh_1553b_value "FALSE" 
        } else {
            error "Error occurs!\nThe value range of -fmsh_1553b expected is (TRUE, FALSE)."
        }
    } else {
        set fmsh_1553b_value "FALSE" 
    }
    return $fmsh_1553b_value
}
proc get_vivado_version {short_enable 0} {
    if {$short_enable == 0} {
        set vvd_version [version -quiet]
    } else {
       set vvd_version [version -short -quiet] 
    }
    return $vvd_version
}
proc lreplace args {
    set l [tcl::llength $args]
    if {$l<3} {
        return -code 1  [rdi::wrongnumargs {lreplace list first last ?element element ...?}]
    }

    # extract list
    set list [tcl::lindex $args 0]
    set first [tcl::lindex $args 1]
    set last [tcl::lindex $args 2]

    # extract args
    tcl::lappend cmdarg
    tcl::foreach var [tcl::lrange $args 3 end] {
        tcl::lappend cmdarg $var
    }
    
    # call cmd
    set code [catch {rdi::col_lreplace -list $list -first $first -last $last -value $cmdarg} result]
#    puts "xlreplace: code = $code, result = $result"
    if {$code==0} {
      # collection
    } elseif {$code==9998} {
      # tcllist
      tcl::lappend cmd {tcl::lreplace}
      tcl::lappend x $list
      set result [uplevel 1 $cmd $x $first $last $cmdarg]
    } else {
      # collection error
      return -code error $result
    }

    return $result
}
proc recover_fmk230t_database {} {
	set vvd_version [string range [version -short] 0 5]
	if {$vvd_version != "2018.3" && $vvd_version != "2022.1"} {
	     error "FMSH->This command may not right,current vivado version is $vvd_version!"
	}
	set vvd_path [get_vvd_path]
	set current_prj_path [file join $::env(JFM_PATH)]
	set patch_k7_path  [file join $current_prj_path "ip_patch" "device_database" "fmk230t" "xilinx" "$vvd_version" "kintex7"]
	set vivado_k7_path [file join $vvd_path "data" "parts" "xilinx" "kintex7"]
	set rd_path [findFiles $patch_k7_path *]
	foreach rd_file $rd_path {
		set wr_file [regsub "$patch_k7_path" $rd_file $vivado_k7_path]
		if {[file exists $rd_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $rd_file no such file! "
		}
		if {[file exists $wr_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $wr_file no such file! "
		}
		file copy -force $rd_file $wr_file
	}
	file copy -force [file join $current_prj_path "ip_patch" "device_database" "fmk230t" "xilinx" "$vvd_version"  "xc7k325t.connOfflineFile.pb"]     [file join $vvd_path "data" "parts" "xilinx" "kintex7" "devint" "kintex7" "xc7k325t" "xc7k325t.connOfflineFile.pb"]
	file copy -force [file join $current_prj_path "ip_patch" "device_database" "fmk230t" "xilinx" "$vvd_version"  "xc7k325t-1.dlyOfflineFile.pb"]    [file join $vvd_path "data" "parts" "xilinx" "kintex7" "devint" "kintex7" "xc7k325t" "xc7k325t-1.dlyOfflineFile.pb"]
	file copy -force [file join $current_prj_path "ip_patch" "device_database" "fmk230t" "xilinx" "$vvd_version"  "xc7k325t-2.dlyOfflineFile.pb"]    [file join $vvd_path "data" "parts" "xilinx" "kintex7" "devint" "kintex7" "xc7k325t" "xc7k325t-2.dlyOfflineFile.pb"]
	file copy -force [file join $current_prj_path "ip_patch" "device_database" "fmk230t" "xilinx" "$vvd_version"  "xc7k325t-2L.dlyOfflineFile.pb"]   [file join $vvd_path "data" "parts" "xilinx" "kintex7" "devint" "kintex7" "xc7k325t" "xc7k325t-2L.dlyOfflineFile.pb"]
	file copy -force [file join $current_prj_path "ip_patch" "device_database" "fmk230t" "xilinx" "$vvd_version"  "xc7k325t-3.dlyOfflineFile.pb"]    [file join $vvd_path "data" "parts" "xilinx" "kintex7" "devint" "kintex7" "xc7k325t" "xc7k325t-3.dlyOfflineFile.pb"]
	puts "FMSH->Recover fmk230t database files successfully!"
}
proc recover_ip_database {} {
    set vvd_path [get_vvd_path]
	set vvd_version [string range [version -short] 0 5]
	if {$vvd_version != "2018.3"} {
        error "An error occurs!\nInfo:Current vvd_version is $vvd_version, not support xfft modifies!(please use Vivado2018.3)"
    }
	set xfft_v9_1_vh_rfs               [format "%s/data/ip/xilinx/xfft_v9_1/hdl/xfft_v9_1_vh_rfs.vhd" $vvd_path]
	set xbip_utils_v3_0_vh_rfs         [format "%s/data/ip/xilinx/xbip_utils_v3_0/hdl/xbip_utils_v3_0_vh_rfs.vhd" $vvd_path]
	set xbip_pipe_v3_0_vh_rfs          [format "%s/data/ip/xilinx/xbip_pipe_v3_0/hdl/xbip_pipe_v3_0_vh_rfs.vhd" $vvd_path]
    set xbip_dsp48_wrapper_v3_0_vh_rfs [format "%s/data/ip/xilinx/xbip_dsp48_wrapper_v3_0/hdl/xbip_dsp48_wrapper_v3_0_vh_rfs.vhd" $vvd_path]
	set xbip_dsp48_addsub_v3_0_vh_rfs  [format "%s/data/ip/xilinx/xbip_dsp48_addsub_v3_0/hdl/xbip_dsp48_addsub_v3_0_vh_rfs.vhd" $vvd_path]
	set xbip_bram18k_v3_0_vh_rfs       [format "%s/data/ip/xilinx/xbip_bram18k_v3_0/hdl/xbip_bram18k_v3_0_vh_rfs.vhd" $vvd_path]
	set xbip_addsub_v3_0_vh_rfs        [format "%s/data/ip/xilinx/xbip_addsub_v3_0/hdl/xbip_addsub_v3_0_vh_rfs.vhd" $vvd_path]
	set mult_gen_v12_0_vh_rfs          [format "%s/data/ip/xilinx/mult_gen_v12_0/hdl/mult_gen_v12_0_vh_rfs.vhd" $vvd_path]
	set floating_point_v7_0_vh_rfs     [format "%s/data/ip/xilinx/floating_point_v7_0/hdl/floating_point_v7_0_vh_rfs.vhd" $vvd_path]
	set cmpy_v6_0_vh_rfs               [format "%s/data/ip/xilinx/cmpy_v6_0/hdl/cmpy_v6_0_vh_rfs.vhd" $vvd_path]
	set c_shift_ram_v12_0_vh_rfs       [format "%s/data/ip/xilinx/c_shift_ram_v12_0/hdl/c_shift_ram_v12_0_vh_rfs.vhd" $vvd_path]
	set c_reg_fd_v12_0_vh_rfs          [format "%s/data/ip/xilinx/c_reg_fd_v12_0/hdl/c_reg_fd_v12_0_vh_rfs.vhd" $vvd_path]
	set c_mux_bit_v12_0_vh_rfs         [format "%s/data/ip/xilinx/c_mux_bit_v12_0/hdl/c_mux_bit_v12_0_vh_rfs.vhd" $vvd_path]
	set c_addsub_v12_0_vh_rfs          [format "%s/data/ip/xilinx/c_addsub_v12_0/hdl/c_addsub_v12_0_vh_rfs.vhd" $vvd_path]
	set axi_utils_v2_0_vh_rfs          [format "%s/data/ip/xilinx/axi_utils_v2_0/hdl/axi_utils_v2_0_vh_rfs.vhd" $vvd_path]
	#fir_compiler_v7_2
	set fir_compiler_v7_2_vh_rfs 	   [format "%s/data/ip/xilinx/fir_compiler_v7_2/hdl/fir_compiler_v7_2_vh_rfs.vhd" $vvd_path]
	##dds_compiler_v6_0 
	set dds_compiler_v6_0_vh_rfs 	   [format "%s/data/ip/xilinx/dds_compiler_v6_0/hdl/dds_compiler_v6_0_vh_rfs.vhd" $vvd_path]
	##cpri
	set cpri_v8_9_rfs				   [format "%s/data/ip/xilinx/cpri_v8_9/hdl/cpri_v8_9_rfs.vhd" $vvd_path]
	set fc32_rs_fec_v1_0_vl_rfs        [format "%s/data/ip/xilinx/fc32_rs_fec_v1_0/hdl/fc32_rs_fec_v1_0_vl_rfs.v " $vvd_path]
	set cmac_usplus_v2_5_vl_rfs 	   [format "%s/data/ip/xilinx/cmac_usplus_v2_5/hdl/cmac_usplus_v2_5_vl_rfs.v" $vvd_path]
	##jesd
	set jesd204_v7_2_rfs 			   [format "%s/data/ip/xilinx/jesd204_v7_2/hdl/jesd204_v7_2_rfs.v" $vvd_path]
	set jesd204c_v4_0_rfs 			   [format "%s/data/ip/xilinx/jesd204c_v4_0/hdl/jesd204c_v4_0_rfs.v" $vvd_path]
	set jesd204c_v4_0_syn_rfs 		   [format "%s/data/ip/xilinx/jesd204c_v4_0/hdl/jesd204c_v4_0_syn_rfs.v" $vvd_path]
	##cordic
	set cordic_v6_0_vh_rfs 		   	   [format "%s/data/ip/xilinx/cordic_v6_0/hdl/cordic_v6_0_vh_rfs.vhd" $vvd_path]
	##divgen
	set div_gen_v5_1_vh_rfs 		   [format "%s/data/ip/xilinx/div_gen_v5_1/hdl/div_gen_v5_1_vh_rfs.vhd" $vvd_path]
	##floating_point_v7_1
	set floating_point_v7_1_vh_rfs	   [format "%s/data/ip/xilinx/floating_point_v7_1/hdl/floating_point_v7_1_vh_rfs.vhd" $vvd_path]
	#binary counter
	set c_counter_binary_v12_0_vh_rfs	   [format "%s/data/ip/xilinx/c_counter_binary_v12_0/hdl/c_counter_binary_v12_0_vh_rfs.vhd" $vvd_path]
	set tri_mode_ethernet_mac_v9_0_rfs [format "%s/data/ip/xilinx/tri_mode_ethernet_mac_v9_0/hdl/tri_mode_ethernet_mac_v9_0_rfs.v" $vvd_path]
	set tri_mode_ethernet_mac_v9_0_rfs_vhd [format "%s/data/ip/xilinx/tri_mode_ethernet_mac_v9_0/hdl/tri_mode_ethernet_mac_v9_0_rfs.vhd" $vvd_path]
	
	set timer_sync_1588_v1_2_rfs [format "%s/data/ip/xilinx/timer_sync_1588_v1_2/hdl/timer_sync_1588_v1_2_rfs.v" $vvd_path]
	set timer_sync_1588_v1_2_rfs_vhd [format "%s/data/ip/xilinx/timer_sync_1588_v1_2/hdl/timer_sync_1588_v1_2_rfs.vhd" $vvd_path]
	
	
	
	set xfft_file_list [concat $xfft_v9_1_vh_rfs $xbip_utils_v3_0_vh_rfs $xbip_pipe_v3_0_vh_rfs $xbip_dsp48_wrapper_v3_0_vh_rfs $xbip_dsp48_addsub_v3_0_vh_rfs $xbip_bram18k_v3_0_vh_rfs $xbip_addsub_v3_0_vh_rfs $mult_gen_v12_0_vh_rfs $floating_point_v7_0_vh_rfs $cmpy_v6_0_vh_rfs $c_shift_ram_v12_0_vh_rfs $c_reg_fd_v12_0_vh_rfs $c_mux_bit_v12_0_vh_rfs $c_addsub_v12_0_vh_rfs $axi_utils_v2_0_vh_rfs $fir_compiler_v7_2_vh_rfs $dds_compiler_v6_0_vh_rfs $cpri_v8_9_rfs $fc32_rs_fec_v1_0_vl_rfs $cmac_usplus_v2_5_vl_rfs $jesd204_v7_2_rfs $jesd204c_v4_0_rfs $jesd204c_v4_0_syn_rfs $cordic_v6_0_vh_rfs $div_gen_v5_1_vh_rfs $floating_point_v7_1_vh_rfs $c_counter_binary_v12_0_vh_rfs $tri_mode_ethernet_mac_v9_0_rfs $tri_mode_ethernet_mac_v9_0_rfs_vhd $timer_sync_1588_v1_2_rfs $timer_sync_1588_v1_2_rfs_vhd]	
    foreach xfft_file $xfft_file_list {
	    incr i 
	    if {[file exists $xfft_file] == 1} {
            set xfft_file_bak [format "%s.bak" $xfft_file]
     	    if {[file exists $xfft_file_bak] == 1} {
     		    file copy -force $xfft_file_bak $xfft_file
     		    file delete $xfft_file_bak -force
     	    } else {
     		    continue 
     	    }
	    } else {
		    error "Error occurs:\n$xfft_file is not existing."
		}
	}
	puts "xfft,fir_compiler,dds_compiler,cpri,jesd,cordic,divgen,floating point,binary counter,eth IPs files recovered successfully!(Total $i files)"
}
proc recover_xc7a100t_database {} {
	set vvd_version [string range [version -short] 0 5]
	# if {$vvd_version != "2018.3"} {
        # error "An error occurs!\nInfo:Current vvd_version:$vvd_version,not support recover_xc7a100t_database!(please use Vivado2018.3)"
    # }
	set vvd_path [get_vvd_path]
	set current_prj_path [file join $::env(JFM_PATH)]
	set patch_data_path [file join $current_prj_path "ip_patch" "xc7a100t" "xilinx" "data"]
	set vvd_data_path 	[file join $vvd_path "data"]
	set rd_path [findFiles $patch_data_path *]
	foreach rd_file $rd_path {
		set wr_file [regsub "$patch_data_path" $rd_file $vvd_data_path]
		if {[file exists $rd_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $rd_file no such file! "
		}
		if {[file exists $wr_file] == 0} {
			file copy -force $rd_file [file dir $wr_file]
		} else {
			file copy -force $rd_file $wr_file
		}
	}
	add_ip_database
	puts "FMSH->recover_xc7a100t_database excuted successfully!"
}
proc remove_fmk50rh_fmbh45_database {} {
	set vvd_version [string range [version -short] 0 5]
	if {$vvd_version != "2018.3" && $vvd_version != "2022.1"} {
        puts "Info:Current vvd_version:$vvd_version,not support remove_fmk50rh_fmbh45_database!"
		return
    }
	set vvd_path [get_vvd_path]
	set current_prj_path [file join $::env(JFM_PATH)]
	set patch_data_path [file join $current_prj_path "ip_patch" "device_database" "fmk50rh_fmbh45" "xilinx" "$vvd_version" "data"]
	set vvd_data_path 	[file join $vvd_path "data"]
	set rd_path [findFiles $patch_data_path *]
	foreach rd_file $rd_path {
		set wr_file [regsub "$patch_data_path" $rd_file $vvd_data_path]
		if {[file exists $rd_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $rd_file no such file! "
		}
		if {[file exists $wr_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $wr_file no such file! "
		} 
		file copy -force $rd_file $wr_file
	}
	file delete -force [file join $vvd_path "data" "parts" "xilinx" "artix7" "devint" "artix7" "xc7k325t_fmk50t"]
	set file_list [glob -nocomplain $vvd_path/data/parts/xilinx/artix7/public/bsdl/xc7k325t_fmk50t_*]
	foreach file $file_list {file delete -force $file}
	
	set file_list [glob -nocomplain $vvd_path/data/parts/xilinx/artix7/public/ibis/pkg/xc7k325t_fmk50t_*]
	foreach file $file_list {file delete -force $file}
	
	
	file delete -force [file join $vvd_path "data" "parts" "xilinx" "zynq" "devint" "zynq" "xc7z045_fmbh45"]
	set file_list [glob -nocomplain $vvd_path/data/parts/xilinx/zynq/public/bsdl/xc7z045_fmbh45_*]
	foreach file $file_list {file delete -force $file}
	
	set file_list [glob -nocomplain $vvd_path/data/parts/xilinx/zynq/public/ibis/pkg/xc7z045_fmbh45_*]
	foreach file $file_list {file delete -force $file}
	remove_ip_database
	puts "FMSH->remove_fmk50rh_fmbh45_database excuted successfully!"	
}
proc remove_ip_database {} {
	set vvd_version [string range [version -short] 0 5]
	set vvd_path [get_vvd_path]
	set current_prj_path [file join $::env(JFM_PATH)]
	if {$vvd_version != "2018.3" && $vvd_version != "2022.1"} {
        return
    }
	recover_vv_index
	file delete -force $vvd_path/data/ip/core_licenses/fm7_device.lic 
	file delete -force  $vvd_path/scripts/ip
	file copy -force $current_prj_path/ip_patch/device_database/common/xilinx/scripts/$vvd_version/ip  $vvd_path/scripts
	if {$vvd_version == "2018.3"} {
		file copy -force $current_prj_path/ip_patch/device_database/common/xilinx/ips/$vvd_version/aurora_8b10b_v11_1/xgui/aurora_8b10b_v11_1.tcl 	$vvd_path/data/ip/xilinx/aurora_8b10b_v11_1/xgui/aurora_8b10b_v11_1.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/xilinx/ips/$vvd_version/aurora_64b66b_v11_2/xgui/aurora_64b66b_v11_2.tcl $vvd_path/data/ip/xilinx/aurora_64b66b_v11_2/xgui/aurora_64b66b_v11_2.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/xilinx/ips/$vvd_version/xdma_v4_1/xgui/xdma_v4_1.tcl	 					$vvd_path/data/ip/xilinx/xdma_v4_1/xgui/xdma_v4_1.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/xilinx/ips/$vvd_version/cpri_v8_9/xgui/cpri_v8_9.tcl	 							$vvd_path/data/ip/xilinx/cpri_v8_9/xgui/cpri_v8_9.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/xilinx/ips/$vvd_version/jesd204_phy_v4_0/xgui/jesd204_phy_v4_0.tcl	 			$vvd_path/data/ip/xilinx/jesd204_phy_v4_0/xgui/jesd204_phy_v4_0.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/xilinx/ips/$vvd_version/jesd204_v7_2/xgui/jesd204_v7_2.tcl	 					$vvd_path/data/ip/xilinx/jesd204_v7_2/xgui/jesd204_v7_2.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/xilinx/ips/$vvd_version/vid_phy_controller_v2_2/xgui/vid_phy_controller_v2_2.tcl	$vvd_path/data/ip/xilinx/vid_phy_controller_v2_2/xgui/vid_phy_controller_v2_2.tcl
		
		file copy -force $current_prj_path/ip_patch/device_database/common/xilinx/$vvd_version/xc7z015.xng $vvd_path/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015.xng
		
	} elseif {$vvd_version == "2022.1"} {
		file copy -force $current_prj_path/ip_patch/device_database/common/xilinx/ips/$vvd_version/aurora_8b10b_v11_1/xgui/aurora_8b10b_v11_1.tcl 	$vvd_path/data/ip/xilinx/aurora_8b10b_v11_1/xgui/aurora_8b10b_v11_1.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/xilinx/ips/$vvd_version/aurora_64b66b_v12_0/xgui/aurora_64b66b_v12_0.tcl $vvd_path/data/ip/xilinx/aurora_64b66b_v12_0/xgui/aurora_64b66b_v12_0.tcl
		file copy -force $current_prj_path/ip_patch/device_database/common/xilinx/ips/$vvd_version/xdma_v4_1/xgui/xdma_v4_1.tcl	 					$vvd_path/data/ip/xilinx/xdma_v4_1/xgui/xdma_v4_1.tcl	
		file copy -force $current_prj_path/ip_patch/device_database/common/xilinx/ips/$vvd_version/jesd204_phy_v4_0/xgui/jesd204_phy_v4_0.tcl	 	$vvd_path/data/ip/xilinx/jesd204_phy_v4_0/xgui/jesd204_phy_v4_0.tcl		

		file copy -force $current_prj_path/ip_patch/device_database/common/xilinx/$vvd_version/xc7z015.xng $vvd_path/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015.xng
	}
	set patch_mig_path 	[file join $current_prj_path "ip_patch" "device_database" "common" "xilinx" "$vvd_version" "mig_7series_v4_2"]
	set vvd_mig_path 	[file join $vvd_path "data" "ip" "xilinx" "mig_7series_v4_2"]
	set rd_path [findFiles $patch_mig_path *]
	foreach rd_file $rd_path {
		set wr_file [regsub "$patch_mig_path" $rd_file $vvd_mig_path]
		if {[file exists $rd_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $rd_file no such file! "
		}
		if {[file exists $wr_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $rd_file no such file! "
		}
		file copy -force $rd_file $wr_file
	}
}
proc remove_jfmql70tai_jfmql100t_jfmql100tai_database {} {
	set vvd_version [string range [version -short] 0 5]
	set vvd_version [string range [version -short] 0 5]
	if {$vvd_version != "2018.3" &&  $vvd_version != "2019.2"} {
	     error "FMSH->This command only support in Vivado2018.3 or Vivado2019.2!"
	}
	set vvd_path [get_vvd_path]
	set current_prj_path [file join $::env(JFM_PATH)]
	set patch_data_path  [file join $current_prj_path "ip_patch" "device_database"  "7z100t_7z100tai_7z70tai" "xilinx" $vvd_version]
	set vivado_data_path [file join $vvd_path]
	set rd_path [findFiles $patch_data_path *]
	foreach rd_file $rd_path {
		set wr_file [regsub "$patch_data_path" $rd_file $vivado_data_path]
		if {[file exists $rd_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $rd_file no such file! "
		}
		if {[file exists $wr_file] == 0} {
			file copy -force $rd_file [file dir $wr_file]
		} else {
			file copy -force $rd_file $wr_file
		}
	}
	file delete -force [file join $vvd_path "data" "parts" "xilinx" "zynq" "devint" "zynq" "xc7z100_jfmql70tai"]
	file delete -force [file join $vvd_path "data" "parts" "xilinx" "zynq" "devint" "zynq" "xc7z100_jfmql100t"]
	file delete -force [file join $vvd_path "data" "parts" "xilinx" "zynq" "devint" "zynq" "xc7z100_jfmql100tai"]
	puts "FMSH->remove_jfmql70tai_jfmql100t_jfmql100tai_database excuted successfully(jfmql70tai/jfmql100t/jfmql100tai)!"
}
proc replace_50t_file {} {
    set vvd_version [string range [version -short] 0 5]
	reset_database_to_default
	#set device_part [get_property PART [current_project]]  
	set vvd_path [get_vvd_path]
	#rd
	set current_prj_path [file join $::env(JFM_PATH)]
	set Package_xml_rd [format "%s/ip_patch/csg324/Package.xml" $current_prj_path]
	set xc7a50tcsg324_pkg_xml_rd [format "%s/ip_patch/csg324/xc7a50tcsg324_pkg.xml" $current_prj_path]
	
	set Package_xml_rd_484 [format "%s/ip_patch/fgg484/Package_484.xml" $current_prj_path]
	set xc7a50tfgg484_pkg_xml_rd [format "%s/ip_patch/fgg484/xc7a50tfgg484_pkg.xml" $current_prj_path]
	
	set artix7_xng_rd [format "%s/ip_patch/database/artix7.xng" $current_prj_path]
	set artix7_rtd_rd [format "%s/ip_patch/database/artix7.rtd" $current_prj_path]
	set PartStats_xml_rd [format "%s/ip_patch/database/PartStats_484.xml" $current_prj_path]
	set xc7a50t_tiles_xml_rd [format "%s/ip_patch/database/xc7a50t_tiles.xml" $current_prj_path]
	set xc7a50t_tile2bfd_rd [format "%s/ip_patch/database/xc7a50t.tile2bfd" $current_prj_path]
	set xc7a50t_xng_rd [format "%s/ip_patch/database/xc7a50t.xng" $current_prj_path]
	set ClockRegion_xml_rd [format "%s/ip_patch/database/ClockRegion_484.xml" $current_prj_path]

	#wr
	set Package_xml_wr [format "%s/data/parts/xilinx/artix7/devint/artix7/xc7a50t/csg324/Package.xml" $vvd_path]
	set xc7a50tcsg324_pkg_xml_wr [format "%s/data/ip/xilinx/mig_7series_v4_2/data/fpga_tlib/artix7/7a/xc7a50tcsg324_pkg.xml" $vvd_path]
	
	set Package_xml_wr_484 [format "%s/data/parts/xilinx/artix7/devint/artix7/xc7a50t/fgg484/Package.xml" $vvd_path]
	set xc7a50tfgg484_pkg_xml_wr [format "%s/data/ip/xilinx/mig_7series_v4_2/data/fpga_tlib/artix7/7a/xc7a50tfgg484_pkg.xml" $vvd_path]

	set artix7_xng_wr [format "%s/data/parts/xilinx/artix7/devint/artix7.xng" $vvd_path]
	set artix7_rtd_wr [format "%s/data/parts/xilinx/artix7/devint/artix7.rtd" $vvd_path]
	set PartStats_xml_wr [format "%s/data/parts/xilinx/artix7/devint/artix7/PartStats.xml" $vvd_path]
	set xc7a50t_tiles_xml_wr [format "%s/data/parts/xilinx/artix7/devint/artix7/xc7a50t/xc7a50t_tiles.xml" $vvd_path]
	set xc7a50t_tile2bfd_wr [format "%s/data/parts/xilinx/artix7/devint/artix7/xc7a50t/xc7a50t.tile2bfd" $vvd_path]
	set xc7a50t_xng_wr [format "%s/data/parts/xilinx/artix7/devint/artix7/xc7a50t/xc7a50t.xng" $vvd_path]
	set ClockRegion_xml_wr [format "%s/data/parts/xilinx/artix7/devint/artix7/xc7a50t/ClockRegion.xml" $vvd_path]	
	
	
	set file_list_wr [concat $Package_xml_wr $xc7a50tcsg324_pkg_xml_wr $Package_xml_wr_484 $xc7a50tfgg484_pkg_xml_wr $artix7_xng_wr $artix7_rtd_wr $PartStats_xml_wr $xc7a50t_tiles_xml_wr $xc7a50t_tile2bfd_wr $xc7a50t_xng_wr $ClockRegion_xml_wr]
	set file_list_rd [concat $Package_xml_rd $xc7a50tcsg324_pkg_xml_rd $Package_xml_rd_484 $xc7a50tfgg484_pkg_xml_rd $artix7_xng_rd $artix7_rtd_rd $PartStats_xml_rd $xc7a50t_tiles_xml_rd $xc7a50t_tile2bfd_rd $xc7a50t_xng_rd $ClockRegion_xml_rd]

	foreach file_wr $file_list_wr {
	    if {[file exist $file_wr]} {
	        # source_file_backup $file_wr
		} else {
		    error "An error occurs:\nCan't find $file_wr no such file! "
		}
	}
	set i 0
	foreach file_rd $file_list_rd {
	    file copy -force $file_rd [lindex $file_list_wr $i]
		# puts "[lindex $file_list_wr $i] replaced successfully!"
		incr i
	}
	puts "Replace FMK50 device files successfully!(fgg484/csg324/cpg236)"
}
proc replace_7z015_file {} {
	set vvd_path [get_vvd_path]
	reset_database_to_default
	#vvd
	set ClockRegion_xml_wr   [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z015/ClockRegion.xml" $vvd_path]
	set PartStats_xml_wr     [format "%s/data/parts/xilinx/zynq/devint/zynq/PartStats.xml" $vvd_path]
	set xc7z015_rtd_wr 	     [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015.rtd" $vvd_path]
	set xc7z015_xng_wr 	     [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015.xng" $vvd_path]
	set xc7z015_tiles_xml_wr [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015_tiles.xml" $vvd_path]
	set xc7z015_tile2bfd_wr  [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015.tile2bfd" $vvd_path]
	set zynq_rtd_wr 	     [format "%s/data/parts/xilinx/zynq/devint/zynq.rtd" $vvd_path]
	set xc7z015_paspd_wr     [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015.paspd" $vvd_path]
	#patch
	set current_prj_path [file join $::env(JFM_PATH)]
	set ClockRegion_xml_rd   [format "%s/ip_patch/7015/ClockRegion.xml" $current_prj_path]
	set PartStats_xml_rd     [format "%s/ip_patch/7015/PartStats.xml" $current_prj_path]
	set xc7z015_rtd_rd 	     [format "%s/ip_patch/7015/xc7z015.rtd" $current_prj_path]
	set xc7z015_xng_rd	     [format "%s/ip_patch/7015/xc7z015.xng" $current_prj_path]
	set xc7z015_tiles_xml_rd [format "%s/ip_patch/7015/xc7z015_tiles.xml" $current_prj_path]
	set xc7z015_tile2bfd_rd  [format "%s/ip_patch/7015/xc7z015.tile2bfd" $current_prj_path]
	set zynq_rtd_rd 	     [format "%s/ip_patch/7015/zynq.rtd" $current_prj_path]
	set xc7z015_paspd_rd	 [format "%s/ip_patch/7015/xc7z015.paspd" $current_prj_path]
	set file_list_wr [concat $ClockRegion_xml_wr $PartStats_xml_wr $xc7z015_rtd_wr $xc7z015_xng_wr $xc7z015_tiles_xml_wr $xc7z015_tile2bfd_wr $zynq_rtd_wr $xc7z015_paspd_wr]
	foreach file_wr $file_list_wr {
	    if {[file exist $file_wr]} {
		} else {
		    error "An error occurs:\nCan't find $file_wr no such file! "
		}
	}
	#replace file
	set file_list_rd [concat $ClockRegion_xml_rd $PartStats_xml_rd $xc7z015_rtd_rd $xc7z015_xng_rd $xc7z015_tiles_xml_rd $xc7z015_tile2bfd_rd $zynq_rtd_rd $xc7z015_paspd_rd]
	foreach file_rd $file_list_rd {
	    if {[file exist $file_rd]} {
		} else {
		    error "An error occurs:\nCan't find $file_rd no such file! "
		}
	}
	
    set i 0
	foreach file_rd $file_list_rd {
	    file copy -force $file_rd [lindex $file_list_wr $i]
		# puts "Replace [lindex $file_list_wr $i] successfully!"
		incr i
	}
	puts "Replace 7z015 data files successfully!(total $i files)"
}
proc replace_7z030ai_file speed {
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
}
proc replace_7z045ai_gth_file {} {
    set vvd_path [get_vvd_path]
	#bak file exist
	reset_database_to_default
	
	#vvd path
	set zynq_rtd_wr [format "%s/data/parts/xilinx/zynq/devint/zynq.rtd" $vvd_path]
	#generate flag to 045ai/045
	source_file_backup $zynq_rtd_wr
	
	set zynq_xng_wr [format "%s/data/parts/xilinx/zynq/devint/zynq.xng" $vvd_path]
	
	set PartStats_xml_wr [format "%s/data/parts/xilinx/zynq/devint/zynq/PartStats.xml" $vvd_path]
	
	
	set ClockRegion_xml_wr 		[format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z045/ClockRegion.xml" $vvd_path]
	set xc7z045_rtd_wr 			[format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z045/xc7z045.rtd" $vvd_path]
	set xc7z045_tile2bfd_wr  	[format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z045/xc7z045.tile2bfd" $vvd_path]
	set xc7z045_tld_wr			[format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z045/xc7z045.tld" $vvd_path]
	set xc7z045_xng_wr			[format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z045/xc7z045.xng" $vvd_path]
	set xc7z045_tiles_xml_wr 	[format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z045/xc7z045_tiles.xml" $vvd_path]
	
	
	#patch path
	set current_prj_path [file join $::env(JFM_PATH)]
	set zynq_rtd_rd [format "%s/ip_patch/045ai/zynq.rtd" $current_prj_path]
	set zynq_xng_rd [format "%s/ip_patch/045ai/zynq.xng" $current_prj_path]
	
	set PartStats_xml_rd [format "%s/ip_patch/045ai/PartStats.xml" $current_prj_path]
	
	set ClockRegion_xml_rd [format "%s/ip_patch/045ai/ClockRegion.xml" $current_prj_path]
	set xc7z045_rtd_rd [format "%s/ip_patch/045ai/xc7z045.rtd" $current_prj_path]
	set xc7z045_tile2bfd_rd  [format "%s/ip_patch/045ai/xc7z045.tile2bfd" $current_prj_path]
	set xc7z045_tld_rd	[format "%s/ip_patch/045ai/xc7z045.tld" $current_prj_path]
	set xc7z045_xng_rd	[format "%s/ip_patch/045ai/xc7z045.xng" $current_prj_path]
	set xc7z045_tiles_xml_rd [format "%s/ip_patch/045ai/xc7z045_tiles.xml" $current_prj_path]
	
	
	
	set file_list_wr [concat $zynq_rtd_wr $zynq_xng_wr $PartStats_xml_wr $ClockRegion_xml_wr $xc7z045_rtd_wr $xc7z045_tile2bfd_wr $xc7z045_tld_wr $xc7z045_xng_wr $xc7z045_tiles_xml_wr]
    #source bak file 
	foreach file_wr $file_list_wr {
	    if {[file exist $file_wr]} {
	        # source_file_backup $file_wr
		} else {
		    error "An error occurs:\nCan't find $file_wr no such file! "
		}
	}
	#replace file
	set file_list_rd [concat $zynq_rtd_rd $zynq_xng_rd $PartStats_xml_rd $ClockRegion_xml_rd $xc7z045_rtd_rd $xc7z045_tile2bfd_rd $xc7z045_tld_rd $xc7z045_xng_rd $xc7z045_tiles_xml_rd]
    set i 0
	foreach file_rd $file_list_rd {
	    file copy -force $file_rd [lindex $file_list_wr $i]
		incr i
	}
	puts "Replace FMQL45T-AIH device files successfully!(total $i files)"

}
proc replace_7z045ai_gtx_file {} {
    set vvd_path [get_vvd_path]
	#bak file exist
	reset_database_to_default
	#vvd path
	set zynq_rtd_wr [format "%s/data/parts/xilinx/zynq/devint/zynq.rtd" $vvd_path]
	#generate flag to 045ai/045
	source_file_backup $zynq_rtd_wr
	set xc7z045_rtd_wr [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z045/xc7z045.rtd" $vvd_path]
	#patch path
	set current_prj_path [file join $::env(JFM_PATH)]
	set zynq_rtd_rd [format "%s/ip_patch/045ai/zynq_gtx.rtd" $current_prj_path]
	set xc7z045_rtd_rd [format "%s/ip_patch/045ai/xc7z045_gtx.rtd" $current_prj_path]

	set file_list_wr [concat $zynq_rtd_wr $xc7z045_rtd_wr]
    #source bak file 
	foreach file_wr $file_list_wr {
	    if {[file exist $file_wr]} {
	        # source_file_backup $file_wr
		} else {
		    error "An error occurs:\nCan't find $file_wr no such file! "
		}
	}
	#replace file
	set file_list_rd [concat $zynq_rtd_rd $xc7z045_rtd_rd]
    set i 0
	foreach file_rd $file_list_rd {
	    file copy -force $file_rd [lindex $file_list_wr $i]
		incr i
	}
	puts "Replace FMQL45T900-AIX device files successfully!"

}
proc replace_7z100_file speed {
    set vvd_path [get_vvd_path]
	reset_database_to_default
	set zynq_pspd_wr       [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z100/xc7z100.paspd" $vvd_path]
	#patch path
	set current_prj_path [file join $::env(JFM_PATH)]
	if {$speed == 0} {
		set zynq_pspd_rd       [format "%s/ip_patch/100ai/xc7z100.paspd" $current_prj_path]
	} elseif {$speed == "fast"} {
		set zynq_pspd_rd       [format "%s/ip_patch/100ai/xc7z100_fast.paspd" $current_prj_path]
		puts "FMSH->7z100AI change speed to fast!"
	} else {
		error "FMSH->Unknow value $speed!"
	}
	
	set file_list_wr [concat $zynq_pspd_wr]
	foreach file_wr $file_list_wr {
	    if {[file exist $file_wr]} {
		} else {
		    error "An error occurs:\nCan't find $file_wr no such file! "
		}
	}
	#replace file
	set file_list_rd [concat $zynq_pspd_rd]
    set i 0
	foreach file_rd $file_list_rd {
	    file copy -force $file_rd [lindex $file_list_wr $i]
		# puts "Replace [lindex $file_list_wr $i] successfully!"
		incr i
	}
	puts "Replace 7z100 data files successfully!(total $i files)"

}
proc replace_7z100ai_file speed {
    set vvd_path [get_vvd_path]
	set vvd_version [string range [version -short] 0 5]
	set vivado_flag [format "%s/data/parts/xilinx/common/unisim.btl" $vvd_path]
	if {[file exist $vivado_flag]} {
		set vvd_version "2018.3"
	} else {
		set vvd_version "2022.1"
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
	set zynq_pspd_wr       [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z100/xc7z100.paspd" $vvd_path]
	#patch path
	set current_prj_path [file join $::env(JFM_PATH)]

	set Sitemap2_xml_rd    [format "%s/ip_patch/100ai/Sitemap2.xml" $current_prj_path]
	# set unisim_btl_rd      [format "%s/ip_patch/100ai/unisim.btl" $current_prj_path]
	set unisim_comp_lib_rd [format "%s/ip_patch/100ai/unisim_comp.lib" $current_prj_path]
	set unisim_comp_v_rd   [format "%s/ip_patch/100ai/unisim_comp.v" $current_prj_path]
	set zynq_lib_rd        [format "%s/ip_patch/100ai/zynq.lib" $current_prj_path]
	set zynq_rtd_rd 	   [format "%s/ip_patch/100ai/zynq.rtd" $current_prj_path]
	set zynq_xng_rd		   [format "%s/ip_patch/100ai/zynq.xng" $current_prj_path]
	
	set zynq_padr_rd       [format "%s/ip_patch/100ai/zynq.padr" $current_prj_path]
	if {$speed == 0} {
		set zynq_pspd_rd       [format "%s/ip_patch/100ai/xc7z100ai.paspd" $current_prj_path]
	} elseif {$speed == "fast"} {
		set zynq_pspd_rd       [format "%s/ip_patch/100ai/xc7z100ai_fast.paspd" $current_prj_path]
		puts "FMSH->7z100AI change speed to fast!"
	} elseif {$speed == "lv"} {
		set zynq_pspd_rd       [format "%s/ip_patch/100ai/xc7z100ai_lv.paspd" $current_prj_path]
		puts "FMSH->7z100AI change speed to LV!"
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
		set unisim_btl_rd      [format "%s/ip_patch/100ai/unisim.btl" $current_prj_path]
		file copy -force $unisim_btl_rd $unisim_btl_wr
	} elseif {$vvd_version == "2022.1"} {
		file delete -force [format "%s/data/parts/xilinx/common/unisims" $vvd_path]
		file copy -force [format "%s/ip_patch/100ai/unisims" $current_prj_path] [format "%s/data/parts/xilinx/common" $vvd_path]
	}
	puts "Replace 7z100AI data files successfully!(total $i files)"
}
proc replace_fmk230t_database {} {
	set vvd_version [string range [version -short] 0 5]
	if {$vvd_version != "2018.3" && $vvd_version != "2022.1"} {
	     error "FMSH->This command may not right,current vivado version is $vvd_version!"
	}
	if {$vvd_version == 2018.3} {
		set vvd_path  [get_vvd_path]
		set current_prj_path [file join $::env(JFM_PATH)]
		file copy -force [format "%s/ip_patch/device_database/fmk230t/xilinx/HARC.cfg" $current_prj_path] [format "%s/data/parts/xilinx/common/HARC.cfg" $vvd_path] 
	}
	set vvd_path [get_vvd_path]
	set current_prj_path [file join $::env(JFM_PATH)]
	reset_database_to_default
	set patch_k7_path  [file join $current_prj_path "ip_patch" "device_database" "fmk230t" "fmsh" "kintex7"]
	set vivado_k7_path [file join $vvd_path "data" "parts" "xilinx" "kintex7"]
	set rd_path [findFiles $patch_k7_path *]
	foreach rd_file $rd_path {
		set wr_file [regsub "$patch_k7_path" $rd_file $vivado_k7_path]
		if {[file exists $rd_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $rd_file no such file! "
		}
		if {[file exists $wr_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $rd_file no such file! "
		}
		file copy -force $rd_file $wr_file
	}
	file delete -force [file join $vvd_path "data" "parts" "xilinx" "kintex7" "devint" "kintex7" "xc7k325t" "xc7k325t.connOfflineFile.pb"]
	file delete -force [file join $vvd_path "data" "parts" "xilinx" "kintex7" "devint" "kintex7" "xc7k325t" "xc7k325t-1.dlyOfflineFile.pb"]
	file delete -force [file join $vvd_path "data" "parts" "xilinx" "kintex7" "devint" "kintex7" "xc7k325t" "xc7k325t-2.dlyOfflineFile.pb"]
	file delete -force [file join $vvd_path "data" "parts" "xilinx" "kintex7" "devint" "kintex7" "xc7k325t" "xc7k325t-2L.dlyOfflineFile.pb"]
	file delete -force [file join $vvd_path "data" "parts" "xilinx" "kintex7" "devint" "kintex7" "xc7k325t" "xc7k325t-3.dlyOfflineFile.pb"]
	puts "FMSH->Replace fmk230t database files successfully!"
}
proc replace_ip_database mem_type_value {
    set vvd_path [get_vvd_path]
	set vvd_version [string range [version -short] 0 5]
	if {$vvd_version != "2018.3"} {
        error "An error occurs!\nInfo:Current vvd_version is $vvd_version, not support xfft modifies!(please use 2018.3)"
    }

	set current_prj_path [file join $::env(JFM_PATH)]
	#xfft_v9_1
	set xfft_v9_1_vh_rfs               [format "%s/data/ip/xilinx/xfft_v9_1/hdl/xfft_v9_1_vh_rfs.vhd" $vvd_path]
	set xbip_utils_v3_0_vh_rfs         [format "%s/data/ip/xilinx/xbip_utils_v3_0/hdl/xbip_utils_v3_0_vh_rfs.vhd" $vvd_path]
	set xbip_pipe_v3_0_vh_rfs          [format "%s/data/ip/xilinx/xbip_pipe_v3_0/hdl/xbip_pipe_v3_0_vh_rfs.vhd" $vvd_path]
    set xbip_dsp48_wrapper_v3_0_vh_rfs [format "%s/data/ip/xilinx/xbip_dsp48_wrapper_v3_0/hdl/xbip_dsp48_wrapper_v3_0_vh_rfs.vhd" $vvd_path]
	set xbip_dsp48_addsub_v3_0_vh_rfs  [format "%s/data/ip/xilinx/xbip_dsp48_addsub_v3_0/hdl/xbip_dsp48_addsub_v3_0_vh_rfs.vhd" $vvd_path]
	set xbip_bram18k_v3_0_vh_rfs       [format "%s/data/ip/xilinx/xbip_bram18k_v3_0/hdl/xbip_bram18k_v3_0_vh_rfs.vhd" $vvd_path]
	set xbip_addsub_v3_0_vh_rfs        [format "%s/data/ip/xilinx/xbip_addsub_v3_0/hdl/xbip_addsub_v3_0_vh_rfs.vhd" $vvd_path]
	set mult_gen_v12_0_vh_rfs          [format "%s/data/ip/xilinx/mult_gen_v12_0/hdl/mult_gen_v12_0_vh_rfs.vhd" $vvd_path]
	set floating_point_v7_0_vh_rfs     [format "%s/data/ip/xilinx/floating_point_v7_0/hdl/floating_point_v7_0_vh_rfs.vhd" $vvd_path]
	set cmpy_v6_0_vh_rfs               [format "%s/data/ip/xilinx/cmpy_v6_0/hdl/cmpy_v6_0_vh_rfs.vhd" $vvd_path]
	set c_shift_ram_v12_0_vh_rfs       [format "%s/data/ip/xilinx/c_shift_ram_v12_0/hdl/c_shift_ram_v12_0_vh_rfs.vhd" $vvd_path]
	set c_reg_fd_v12_0_vh_rfs          [format "%s/data/ip/xilinx/c_reg_fd_v12_0/hdl/c_reg_fd_v12_0_vh_rfs.vhd" $vvd_path]
	set c_mux_bit_v12_0_vh_rfs         [format "%s/data/ip/xilinx/c_mux_bit_v12_0/hdl/c_mux_bit_v12_0_vh_rfs.vhd" $vvd_path]
	set c_addsub_v12_0_vh_rfs          [format "%s/data/ip/xilinx/c_addsub_v12_0/hdl/c_addsub_v12_0_vh_rfs.vhd" $vvd_path]
	set axi_utils_v2_0_vh_rfs          [format "%s/data/ip/xilinx/axi_utils_v2_0/hdl/axi_utils_v2_0_vh_rfs.vhd" $vvd_path]
	#fir_compiler_v7_2
	set fir_compiler_v7_2_vh_rfs 	   [format "%s/data/ip/xilinx/fir_compiler_v7_2/hdl/fir_compiler_v7_2_vh_rfs.vhd" $vvd_path]
	##dds_compiler_v6_0 
	set dds_compiler_v6_0_vh_rfs 	   [format "%s/data/ip/xilinx/dds_compiler_v6_0/hdl/dds_compiler_v6_0_vh_rfs.vhd" $vvd_path]
	##cpri
	set cpri_v8_9_rfs				   [format "%s/data/ip/xilinx/cpri_v8_9/hdl/cpri_v8_9_rfs.vhd" $vvd_path]
	set fc32_rs_fec_v1_0_vl_rfs        [format "%s/data/ip/xilinx/fc32_rs_fec_v1_0/hdl/fc32_rs_fec_v1_0_vl_rfs.v " $vvd_path]
	set cmac_usplus_v2_5_vl_rfs 	   [format "%s/data/ip/xilinx/cmac_usplus_v2_5/hdl/cmac_usplus_v2_5_vl_rfs.v" $vvd_path]
	##jesd
	set jesd204_v7_2_rfs 			   [format "%s/data/ip/xilinx/jesd204_v7_2/hdl/jesd204_v7_2_rfs.v" $vvd_path]
	set jesd204c_v4_0_rfs 			   [format "%s/data/ip/xilinx/jesd204c_v4_0/hdl/jesd204c_v4_0_rfs.v" $vvd_path]
	set jesd204c_v4_0_syn_rfs 		   [format "%s/data/ip/xilinx/jesd204c_v4_0/hdl/jesd204c_v4_0_syn_rfs.v" $vvd_path]
	##cordic
	set cordic_v6_0_vh_rfs 		   	   [format "%s/data/ip/xilinx/cordic_v6_0/hdl/cordic_v6_0_vh_rfs.vhd" $vvd_path]
	##divgen
	set div_gen_v5_1_vh_rfs 		   [format "%s/data/ip/xilinx/div_gen_v5_1/hdl/div_gen_v5_1_vh_rfs.vhd" $vvd_path]
	##floating_point_v7_1
	set floating_point_v7_1_vh_rfs	   [format "%s/data/ip/xilinx/floating_point_v7_1/hdl/floating_point_v7_1_vh_rfs.vhd" $vvd_path]
	
	set c_counter_binary_v12_0_vh_rfs  [format "%s/data/ip/xilinx/c_counter_binary_v12_0/hdl/c_counter_binary_v12_0_vh_rfs.vhd" $vvd_path]
	
	set tri_mode_ethernet_mac_v9_0_rfs [format "%s/data/ip/xilinx/tri_mode_ethernet_mac_v9_0/hdl/tri_mode_ethernet_mac_v9_0_rfs.v" $vvd_path]
	set tri_mode_ethernet_mac_v9_0_rfs_vhd [format "%s/data/ip/xilinx/tri_mode_ethernet_mac_v9_0/hdl/tri_mode_ethernet_mac_v9_0_rfs.vhd" $vvd_path]
	
	
	set timer_sync_1588_v1_2_rfs [format "%s/data/ip/xilinx/timer_sync_1588_v1_2/hdl/timer_sync_1588_v1_2_rfs.v" $vvd_path]
	set timer_sync_1588_v1_2_rfs_vhd [format "%s/data/ip/xilinx/timer_sync_1588_v1_2/hdl/timer_sync_1588_v1_2_rfs.vhd" $vvd_path]
	
	
	
	file copy -force [file join $current_prj_path "ip_patch" "xilinx" "xgmac_top_v.ttcl"] [format "%s/data/ip/xilinx/ten_gig_eth_mac_v15_1/ttcl/xgmac_top_v.ttcl" $vvd_path]

	set xfft_file_list [concat $xfft_v9_1_vh_rfs $xbip_utils_v3_0_vh_rfs $xbip_pipe_v3_0_vh_rfs $xbip_dsp48_wrapper_v3_0_vh_rfs $xbip_dsp48_addsub_v3_0_vh_rfs $xbip_bram18k_v3_0_vh_rfs $xbip_addsub_v3_0_vh_rfs $mult_gen_v12_0_vh_rfs $floating_point_v7_0_vh_rfs $cmpy_v6_0_vh_rfs $c_shift_ram_v12_0_vh_rfs $c_reg_fd_v12_0_vh_rfs $c_mux_bit_v12_0_vh_rfs $c_addsub_v12_0_vh_rfs $axi_utils_v2_0_vh_rfs $fir_compiler_v7_2_vh_rfs $dds_compiler_v6_0_vh_rfs $cpri_v8_9_rfs $fc32_rs_fec_v1_0_vl_rfs $cmac_usplus_v2_5_vl_rfs $jesd204_v7_2_rfs $jesd204c_v4_0_rfs $jesd204c_v4_0_syn_rfs $cordic_v6_0_vh_rfs $div_gen_v5_1_vh_rfs $floating_point_v7_1_vh_rfs $c_counter_binary_v12_0_vh_rfs $tri_mode_ethernet_mac_v9_0_rfs $tri_mode_ethernet_mac_v9_0_rfs_vhd $timer_sync_1588_v1_2_rfs $timer_sync_1588_v1_2_rfs_vhd]	

	foreach xfft_file $xfft_file_list {
	    incr i
	    if {[file exists $xfft_file] == 1} {
	        set xfft_file_bak [format "%s.bak" $xfft_file]
		    regexp {hdl\/(.*)$} $xfft_file match ori_file
	        if {[file exists $xfft_file_bak]} {		
	        } else {
	            source_file_backup $xfft_file
	        }
			if {$ori_file == "xfft_v9_1_vh_rfs.vhd" && $mem_type_value == "LOGIC"} {
				set ori_file "xfft_v9_1_vh_rfs_mem_type.vhd"
				puts "XFFT mem_type_value is LOGIC"
			}
            set ori_path [file join $current_prj_path "ip_patch" "xilinx" "$ori_file"]
            file copy -force $ori_path $xfft_file
			
		} else {
		   error "$xfft_file is not existing."
		}
	}
	
	puts "xfft,fir_compiler,dds_compiler,cpri,jesd,cordic,divgen,floating point,binary counter ,eth IPs files modified successfully!(Total $i files)"
}
proc replace_lib_padr {} {
	set device_part [get_property PART [current_project]]
    set path [get_vvd_path]
	set current_prj_path [get_property DIRECTORY [current_project]]
	file copy -force  [file join $current_prj_path "ip_patch" "paspd" "fmsh" "7z045" "zynq.lib"]  [file join $path "data" "parts" "xilinx" "zynq" "devint" "zynq.lib"] 
	file copy -force  [file join $current_prj_path "ip_patch" "paspd" "fmsh" "7z045" "zynq.padr"] [file join $path "data" "parts" "xilinx" "zynq" "devint" "zynq.padr"] 

}
proc replace_vv_index {} {
	set vvd_path [get_vvd_path]
	set vvd_version [string range [version -short] 0 5]
	if {$vvd_version != "2018.3" && $vvd_version != "2022.1" && $vvd_version != "2019.2"} {
        puts "FMSH->Skip replace_vv_index!"
    }
	set current_prj_path [file join $::env(JFM_PATH)]
	set vv_index [file join "$vvd_path" "data" "ip" "vv_index.xml"]
	file copy -force  [file join $current_prj_path "ip_patch" "device_database" "common" "fmsh" "$vvd_version" "vv_index.xml"] $vv_index
}
proc replace_xc7a100t_database {} {
	set vvd_version [string range [version -short] 0 5]
	# if {$vvd_version != "2018.3"} {
        # error "An error occurs!\nInfo:Current vvd_version:$vvd_version,not support replace_xc7a100t_database!(please use Vivado2018.3)"
    # }
	set vvd_path [get_vvd_path]
	set current_prj_path [file join $::env(JFM_PATH)]
	set patch_data_path [file join $current_prj_path "ip_patch" "xc7a100t" "fmsh" "data"]
	set vvd_data_path 	[file join $vvd_path "data"]
	set rd_path [findFiles $patch_data_path *]
	foreach rd_file $rd_path {
		set wr_file [regsub "$patch_data_path" $rd_file $vvd_data_path]
		if {[file exists $rd_file] == 0} {
			error "FMSH->An error occurs:\nCan't find $rd_file no such file! "
		}
		if {[file exists $wr_file] == 0} {
			file copy -force $rd_file [file dir $wr_file]
		} else {
			file copy -force $rd_file $wr_file
		}
	}
	add_ip_database
	puts "FMSH->replace_xc7a100t_database excuted successfully!"
}
proc reset_database_to_default {} {
	set vvd_version [string range [version -short] 0 5]
	set vvd_path  [get_vvd_path]
	set vivado_flag [format "%s/data/parts/xilinx/common/unisim.btl" $vvd_path]
	if {[file exist $vivado_flag]} {
		set vvd_version "2018.3"
	} else {
		set vvd_version "2022.1"
	}
	if {$vvd_version != "2018.3" && $vvd_version != "2022.1"} {
	     error "FMSH->This command may not right,current vivado version is $vvd_version!(Please use 2018.3 or 2022.1)"
		 return
	}	
	set vvd_list  [list]
	set fmsh_list [list]
	#delete 045ai flag 
	set flag_045ai	[format "%s/data/parts/xilinx/zynq/devint/zynq.rtd.bak" $vvd_path]
	file delete -force $flag_045ai
	#vvd path
	#045ai 9
	lappend	    vvd_list     [format "%s/data/parts/xilinx/zynq/devint/zynq.rtd" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/zynq/devint/zynq.xng" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/zynq/devint/zynq/PartStats.xml" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z045/ClockRegion.xml" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z045/xc7z045.rtd" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z045/xc7z045.tile2bfd" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z045/xc7z045.tld" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z045/xc7z045.xng" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z045/xc7z045_tiles.xml" $vvd_path]
	#50t 11
	lappend	    vvd_list     [format "%s/data/parts/xilinx/artix7/devint/artix7/xc7a50t/csg324/Package.xml" $vvd_path]
	lappend	    vvd_list     [format "%s/data/ip/xilinx/mig_7series_v4_2/data/fpga_tlib/artix7/7a/xc7a50tcsg324_pkg.xml" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/artix7/devint/artix7/xc7a50t/fgg484/Package.xml" $vvd_path]
	lappend	    vvd_list     [format "%s/data/ip/xilinx/mig_7series_v4_2/data/fpga_tlib/artix7/7a/xc7a50tfgg484_pkg.xml" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/artix7/devint/artix7.xng" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/artix7/devint/artix7.rtd" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/artix7/devint/artix7/PartStats.xml" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/artix7/devint/artix7/xc7a50t/xc7a50t_tiles.xml" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/artix7/devint/artix7/xc7a50t/xc7a50t.tile2bfd" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/artix7/devint/artix7/xc7a50t/xc7a50t.xng" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/artix7/devint/artix7/xc7a50t/ClockRegion.xml" $vvd_path]
	#100ai 9
    lappend	    vvd_list     [format "%s/data/parts/xilinx/zynq/devint/Sitemap2.xml" $vvd_path]
	# lappend	    vvd_list     [format "%s/data/parts/xilinx/common/unisim.btl" $vvd_path]
	lappend	    vvd_list     [format "%s/scripts/rt/data/unisim_comp.lib" $vvd_path]
	lappend	    vvd_list     [format "%s/scripts/rt/data/unisim_comp.v" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/zynq/devint/zynq.lib" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/zynq/devint/zynq.rtd" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/zynq/devint/zynq.xng" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/zynq/devint/zynq.padr" $vvd_path]
	lappend	    vvd_list     [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z100/xc7z100.paspd" $vvd_path]
	#7015 7
	lappend	    vvd_list [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z015/ClockRegion.xml" $vvd_path]
	lappend	    vvd_list [format "%s/data/parts/xilinx/zynq/devint/zynq/PartStats.xml" $vvd_path]
	lappend	    vvd_list [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015.rtd" $vvd_path]
	lappend	    vvd_list [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015.xng" $vvd_path]
	lappend	    vvd_list [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015_tiles.xml" $vvd_path]
	lappend	    vvd_list [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015.tile2bfd" $vvd_path]
	lappend	    vvd_list [format "%s/data/parts/xilinx/zynq/devint/zynq.rtd" $vvd_path]
	lappend	    vvd_list [format "%s/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015.paspd" $vvd_path]
	#patch path
	#045ai
	set current_prj_path [file join $::env(JFM_PATH)]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/045ai/zynq.rtd" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/045ai/zynq.xng" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/045ai/PartStats.xml" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/045ai/ClockRegion.xml" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/045ai/xc7z045.rtd" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/045ai/xc7z045.tile2bfd" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/045ai/xc7z045.tld" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/045ai/xc7z045.xng" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/045ai/xc7z045_tiles.xml" $current_prj_path]
	#50t
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/50t/Package_324.xml" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/50t/xc7a50tcsg324_pkg.xml" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/50t/Package_484.xml" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/50t/xc7a50tfgg484_pkg.xml" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/50t/artix7.xng" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/50t/artix7.rtd" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/50t/PartStats.xml" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/50t/xc7a50t_tiles.xml" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/50t/xc7a50t.tile2bfd" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/50t/xc7a50t.xng" $current_prj_path]
	lappend	    fmsh_list     [format "%s/ip_patch/database_ori/$vvd_version/50t/ClockRegion.xml" $current_prj_path]
	#100ai
	lappend	    fmsh_list      [format "%s/ip_patch/database_ori/$vvd_version/100ai/Sitemap2.xml" $current_prj_path]
	# lappend	    fmsh_list      [format "%s/ip_patch/database_ori/$vvd_version/100ai/unisim.btl" $current_prj_path]
	lappend	    fmsh_list      [format "%s/ip_patch/database_ori/$vvd_version/100ai/unisim_comp.lib" $current_prj_path]
	lappend	    fmsh_list      [format "%s/ip_patch/database_ori/$vvd_version/100ai/unisim_comp.v" $current_prj_path]
	lappend	    fmsh_list      [format "%s/ip_patch/database_ori/$vvd_version/100ai/zynq.lib" $current_prj_path]
	lappend	    fmsh_list      [format "%s/ip_patch/database_ori/$vvd_version/100ai/zynq.rtd" $current_prj_path]
	lappend	    fmsh_list      [format "%s/ip_patch/database_ori/$vvd_version/100ai/zynq.xng" $current_prj_path]
	lappend	    fmsh_list      [format "%s/ip_patch/database_ori/$vvd_version/100ai/zynq.padr" $current_prj_path]
	lappend	    fmsh_list      [format "%s/ip_patch/database_ori/$vvd_version/100ai/xc7z100.paspd" $current_prj_path]
	#7015 7
	lappend	    fmsh_list  [format "%s/ip_patch/database_ori/$vvd_version/7015/ClockRegion.xml" $current_prj_path]
	lappend	    fmsh_list  [format "%s/ip_patch/database_ori/$vvd_version/7015/PartStats.xml" $current_prj_path]
	lappend	    fmsh_list  [format "%s/ip_patch/database_ori/$vvd_version/7015/xc7z015.rtd" $current_prj_path]
	lappend	    fmsh_list  [format "%s/ip_patch/database_ori/$vvd_version/7015/xc7z015.xng" $current_prj_path]
	lappend	    fmsh_list  [format "%s/ip_patch/database_ori/$vvd_version/7015/xc7z015_tiles.xml" $current_prj_path]
	lappend	    fmsh_list  [format "%s/ip_patch/database_ori/$vvd_version/7015/xc7z015.tile2bfd" $current_prj_path]
	lappend	    fmsh_list  [format "%s/ip_patch/database_ori/$vvd_version/7015/zynq.rtd" $current_prj_path]
	lappend	    fmsh_list  [format "%s/ip_patch/database_ori/$vvd_version/7015/xc7z015.paspd" $current_prj_path]
	set i 0
	foreach vvd_file $vvd_list {
		if {[file exists $vvd_file] == 0 || [file exists [lindex $fmsh_list $i]] == 0 } {
			puts "Critical Warning:\nPlease check whether $vvd_file , [lindex $fmsh_list $i] is existing!"
			incr i
			continue
		}
		file copy -force [lindex $fmsh_list $i] $vvd_file
		incr i
	}
	###100AI unisim.btl
	if {$vvd_version == "2018.3"} {
		set unisim_btl_wr      [format "%s/data/parts/xilinx/common/unisim.btl" $vvd_path]
		set unisim_btl_rd      [format "%s/ip_patch/database_ori/2018.3/100ai/unisim.btl" $current_prj_path]
		file copy -force $unisim_btl_rd $unisim_btl_wr
	} elseif {$vvd_version == "2022.1"} {
		file delete -force [format "%s/data/parts/xilinx/common/unisims" $vvd_path]
		file copy -force [format "%s/ip_patch/database_ori/2022.1/100ai/unisims" $current_prj_path] [format "%s/data/parts/xilinx/common" $vvd_path]
	}
	# recover_fmk230t_database
	fmsh_send_msg_critical_warning "Reset replaced device database(FMK50T/FMQL45T-AI/JFMQL100TAI/JFMQL100T/JFMQL15T/JFMQL30TAI676H) to default successfully!(if you want to reset paspd to default,please use spd_recover_force command)"
}
proc source_file_backup source_file_path {
    set dst_file_path [format "%s.bak" $source_file_path]
    file copy -force $source_file_path $dst_file_path
}
proc spd_replace {change_speed_value bh_mig_value} {
	if {$change_speed_value == "FALSE"} {
		puts "FMSH-->Skip spd_replace successfully!"
		return
	}
    set device_part [get_property PART [current_project]]
    set path [get_vvd_path]
	set current_prj_path [get_property DIRECTORY [current_project]]
	puts "change_speed_value:$change_speed_value"
	puts "current_prj_path:$current_prj_path"
	puts "env: $::env(JFM_PATH)"
	puts "Now check if spd files need replace:"
	if {[regexp {^xc7z010} $device_part]} {
		if {$change_speed_value == "TRUE"} {
			set rd_path [file join $current_prj_path "ip_patch" "paspd" "fmsh" "xc7z010.paspd"] 
		} elseif {$change_speed_value == "FAST"} {
			set rd_path [file join $current_prj_path "ip_patch" "paspd" "fmsh" "xc7z010_fast.paspd"] 
		}
	    set wr_path [file join $path "data" "parts" "xilinx" "zynq" "devint" "zynq" "xc7z010" "xc7z010.paspd"]
		rd_path_wr_path  $rd_path $wr_path
		file copy -force $rd_path $wr_path
		replace_lib_padr
        puts "The xc7z010 paspd file replaced successfully!($wr_path)"
		fmsh_send_msg_warning "Part:$device_part,change .paspd file to fmsh database!"
	} elseif {[regexp {^xc7z020} $device_part]} {
		if {$change_speed_value == "TRUE"} {
			set rd_path [file join $current_prj_path "ip_patch" "paspd" "fmsh" "xc7z020.paspd"]
		} elseif {$change_speed_value == "FAST"} {
			set rd_path [file join $current_prj_path "ip_patch" "paspd" "fmsh" "xc7z020_fast.paspd"]
		}
	    set wr_path [file join $path "data" "parts" "xilinx" "zynq" "devint" "zynq" "xc7z020" "xc7z020.paspd"]
		rd_path_wr_path  $rd_path $wr_path
		file copy -force $rd_path $wr_path
		replace_lib_padr
        puts "The xc7z020 paspd file replaced successfully!($wr_path)"
		fmsh_send_msg_warning "Part:$device_part,change .paspd file to fmsh database!"
	} elseif {[regexp {^xc7z030} $device_part]} {
		puts "current part is 7z030AI,change zynq lib padr to 7z030AI"
		file copy -force  [file join $current_prj_path "ip_patch" "paspd" "fmsh" "030ai" "zynq.lib"]  [file join $path "data" "parts" "xilinx" "zynq" "devint" "zynq.lib"] 
		file copy -force  [file join $current_prj_path "ip_patch" "paspd" "fmsh" "030ai" "zynq.padr"] [file join $path "data" "parts" "xilinx" "zynq" "devint" "zynq.padr"] 
	} elseif {[regexp {^xc7z045f} $device_part]} {
	    set flag_045ai [format "%s/data/parts/xilinx/zynq/devint/zynq.rtd.bak" $path]
		if {[file exist $flag_045ai]} {
		    puts "Part:7z045ai spd replace!"
		    set rd_path [file join $current_prj_path "ip_patch" "paspd" "fmsh" "xc7z045_ai.paspd"] 
			replace_lib_padr
		} else {
			if {$bh_mig_value == "FALSE"} {
				if {$change_speed_value == "TRUE"} {
					replace_lib_padr
					set rd_path [file join $current_prj_path "ip_patch" "paspd" "fmsh" "xc7z045.paspd"] 
				} elseif {$change_speed_value == "FAST"} {
					replace_lib_padr
					set rd_path [file join $current_prj_path "ip_patch" "paspd" "fmsh" "xc7z045_fast.paspd"] 
				}
				fmsh_send_msg_warning "Part:7z045,change .paspd file to fmsh database!"
			} elseif {$bh_mig_value == "TRUE" || [regexp {xc7z045_fmbh45} $device_part]} {
				recover_lib_padr
				puts "Part:BaiHu 7z045 spd replace!"
				set rd_path [file join $current_prj_path "ip_patch" "paspd" "fmsh" "xc7z045_bh.paspd"] 
				fmsh_send_msg_warning "Part:BaiHu 7z045,change .paspd file to fmsh database!"
			}
		}
	    set wr_path [file join $path "data" "parts" "xilinx" "zynq" "devint" "zynq" "xc7z045" "xc7z045.paspd"]
		rd_path_wr_path  $rd_path $wr_path
		file copy -force $rd_path $wr_path
	} elseif {[regexp {^xc7z015} $device_part] || [regexp {xc7z045_fmql15} $device_part]} {
		if {$change_speed_value == "TRUE"} {
			set rd_path [file join $current_prj_path "ip_patch" "paspd" "fmsh" "xc7z015.paspd"]
		} elseif {$change_speed_value == "FAST"} {
			set rd_path [file join $current_prj_path "ip_patch" "paspd" "fmsh" "xc7z015_fast.paspd"]
		}
		set wr_path [file join $path "data" "parts" "xilinx" "zynq" "devint" "zynq" "xc7z015" "xc7z015.paspd"]
		rd_path_wr_path  $rd_path $wr_path
		file copy -force $rd_path $wr_path
		replace_lib_padr
		fmsh_send_msg_warning "Part:7z015,change .paspd file to fmsh database!"
	} elseif {[regexp {^xc7z100f} $device_part]} {
			set zynq_xng        [format "%s/data/parts/xilinx/zynq/devint/zynq.xng" $path]
			if {[md5::md5 -hex -file $zynq_xng] == "E870AFE3655C65FE0D3F7EDB2D525015"} {
				puts "current part is 100TAI,change zynq lib padr to 100TAI"
				file copy -force  [file join $current_prj_path "ip_patch" "paspd" "fmsh" "100ai" "zynq.lib"]  [file join $path "data" "parts" "xilinx" "zynq" "devint" "zynq.lib"] 
				file copy -force  [file join $current_prj_path "ip_patch" "paspd" "fmsh" "100ai" "zynq.padr"] [file join $path "data" "parts" "xilinx" "zynq" "devint" "zynq.padr"] 
			} else {
				puts "current part is 100T,change zynq lib padr to 100T"
				file copy -force  [file join $current_prj_path "ip_patch" "paspd" "xilinx" "zynq.lib"]  [file join $path "data" "parts" "xilinx" "zynq" "devint" "zynq.lib"] 
				file copy -force  [file join $current_prj_path "ip_patch" "paspd" "xilinx" "zynq.padr"] [file join $path "data" "parts" "xilinx" "zynq" "devint" "zynq.padr"] 
			}
	} elseif {[regexp {^xc7vx690t} $device_part]} {
			set rd_path [file join $current_prj_path "ip_patch" "paspd" "fmsh" "xc7vx690t.paspd"] 
			set wr_path [file join $path "data" "parts" "xilinx" "virtex7" "devint" "virtex7" "xc7vx690t" "xc7vx690t.paspd"]
			rd_path_wr_path  $rd_path $wr_path
			file copy -force $rd_path $wr_path
			puts "The xc7vx690t paspd file replaced successfully!($wr_path)"
			fmsh_send_msg_warning "Part:$device_part,change .paspd file to fmsh database!"
	} elseif {[regexp {^xc7k325t} $device_part]} {
			set rd_path [file join $current_prj_path "ip_patch" "paspd" "fmsh" "xc7k325t.paspd"] 
			set wr_path [file join $path "data" "parts" "xilinx" "kintex7" "devint" "kintex7" "xc7k325t" "xc7k325t.paspd"]
			rd_path_wr_path  $rd_path $wr_path
			file copy -force $rd_path $wr_path
			puts "The xc7k325t paspd file replaced successfully!($wr_path)"
			fmsh_send_msg_warning "Part:$device_part,change .paspd file to fmsh database!"
	} elseif {[regexp {^xc7k410t} $device_part]} {
			set rd_path [file join $current_prj_path "ip_patch" "paspd" "fmsh" "xc7k410t.paspd"] 
			set wr_path [file join $path "data" "parts" "xilinx" "kintex7" "devint" "kintex7" "xc7k410t" "xc7k410t.paspd"]
			rd_path_wr_path  $rd_path $wr_path
			file copy -force $rd_path $wr_path
			puts "The xc7k410t paspd file replaced successfully!($wr_path)"
			fmsh_send_msg_warning "Part:$device_part,change .paspd file to fmsh database!"
	} else {
	    puts "Current design device part is $device_part ,don't need to replace spd file!"
	} 
}
