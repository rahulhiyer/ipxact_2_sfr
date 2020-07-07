#!/usr/bin/python
'''
This project converts the IP-XACT format to RTL Code
'''

import re
import time
import os.path
import logging
import sys

#logging.basicConfig(level="WARNING",format='%(asctime)s - %(levelname)10s - %(message)')

register_start = r'<spirit:register>'
register_end = r'</spirit:register>'
field_start = r'<spirit:field>'
field_end = r'</spirit:field>'
name_start = r'<spirit:name>'
name_end   = r'</spirit:name>'
desc_start = r'<spirit:description>'
desc_end = r'</spirit:description>'
addr_start = r'<spirit:addressOffset>'
addr_end = r'</spirit:addressOffset>'
f1 = open("sfr_file.v","w+")

first_line = "  always @(posedge clk or negedge reset_n) begin"


def module_write (a, write_file):
	write_file.write(a)
	write_file.write("\n")
#	demodule_write_ipxact(file_name):
#		workbook = xlrd.open_workbook(file_name)
#		worksheet = workbook.sheet_by_name(d2h)
#		num_rows  = worksheet.nrows
#		num_cols  = worksheet.ncols
#		for curr_row in range(0,num_rows,1):
#			for curr_col in range(0, num_cols,1):
#				data = worksheet.cell_value(curr_row,curr_col)
#				if data == "Reg. Name" :
#					register_column = curr_col
#				if data == "FIELD NAME" :
#					field_column = curr_col
#		module_write("File Name : " + str(file_name))
#		module_write("register_name : " + str(register_column))
#		module_write("field_name : " + str(field_column))


def mpu_always (rtl_write):
	module_write(first_line+" : read_data_from_sfr_blk //{".upper(), rtl_write)
	module_write("    if (~reset_n)", rtl_write)
	module_write("      mpu_rdata <= {DATA_WIDTH{1'b0}};", rtl_write)
	module_write("    else begin //{", rtl_write)
	module_write("      mpu_rdata <= mpu_rdata_combo;", rtl_write)
	module_write("    end //}", rtl_write)
	module_write("  end //}\n\n", rtl_write)
	module_write(first_line+" : read_ready_from_sfr_blk //{".upper(), rtl_write)
	module_write("    if (~reset_n)", rtl_write)
	module_write("      mpu_rvalid <= 1'b0;", rtl_write)
	module_write("    else begin //{", rtl_write)
	module_write("      mpu_rvalid <= mpu_rstrobe;", rtl_write)
	module_write("    end //}", rtl_write)
	module_write("  end //}\n\n", rtl_write)
	module_write(first_line+" : write_ready_from_sfr_blk //{".upper(), rtl_write)
	module_write("    if (~reset_n)", rtl_write)
	module_write("      mpu_wready <= 1'b0;", rtl_write)
	module_write("    else begin //{", rtl_write)
	module_write("      mpu_wready <= mpu_wstrobe;", rtl_write)
	module_write("    end //}", rtl_write)
	module_write("  end //}\n\n", rtl_write)
	module_write("endmodule\n", rtl_write)

def rw_non_volatile(register_name,i, rtl_write):
	field_name = register_name.fields_data[i]["actual_name"].upper()
	module_write(first_line+" : "+field_name.lower()+"_blk //{", rtl_write)
	module_write("    if (~reset_n)", rtl_write)
	module_write("      "+register_name.fields_data[i]["actual_name"]+" <= "+register_name.fields_data[i]["_resetValue_"]+";", rtl_write)
	module_write("    else begin //{", rtl_write)
	module_write("      if ("+register_name.register["write_signal_name"]+")", rtl_write)
	module_write("        "+register_name.fields_data[i]["actual_name"]+" <= mpu_wdata"+register_name.fields_data[i]["bit_position"]+";", rtl_write)
	module_write("    end //}", rtl_write)
	module_write("  end //}", rtl_write)

	
def rw_volatile(register_name,i, rtl_write):
	field_name = register_name.fields_data[i]["actual_name"].upper()
	module_write(first_line+" : " +field_name.lower()+"_blk //{", rtl_write)
	module_write("    if (~reset_n)", rtl_write)
	module_write("      "+register_name.fields_data[i]["actual_name"]+" <= "+register_name.fields_data[i]["_resetValue_"]+";", rtl_write)
	module_write("    else begin //{", rtl_write)
	if (register_name.fields_data[i]["_sysrdl_precedence_"] == True):
		module_write("      // FW has higher precedence", rtl_write)
		if re.match("1S",register_name.fields_data[i]["modifiedWriteValue"]):
			module_write("      if ("+register_name.register["write_signal_name"]+ " & |mpu_wdata"+register_name.fields_data[i]["bit_position"]+" & ~|"+register_name.fields_data[i]["actual_name"]+")", rtl_write)
			module_write("        "+register_name.fields_data[i]["actual_name"]+" <= {"+str(register_name.fields_data[i]["bitWidth"])+"{1'b1}};", rtl_write)
		elif re.match("1C",register_name.fields_data[i]["modifiedWriteValue"]):
			module_write("      if ("+register_name.register["write_signal_name"]+ " & |mpu_wdata"+register_name.fields_data[i]["bit_position"]+" & |"+register_name.fields_data[i]["actual_name"]+")", rtl_write)
			module_write("        "+register_name.fields_data[i]["actual_name"]+" <= {"+str(register_name.fields_data[i]["bitWidth"])+"{1'b0}};", rtl_write)
		elif register_name.fields_data[i]["modifiedWriteValue"] == "C":
			module_write("      if ("+register_name.register["write_signal_name"]+ " & |"+register_name.fields_data[i]["actual_name"]+")", rtl_write)
			module_write("        "+register_name.fields_data[i]["actual_name"]+" <= {"+str(register_name.fields_data[i]["bitWidth"])+"{1'b0}};", rtl_write)
		elif register_name.fields_data[i]["modifiedWriteValue"] == "T":
			module_write("      if ("+register_name.register["write_signal_name"]+ ")", rtl_write)
			module_write("        "+register_name.fields_data[i]["actual_name"]+" <= ~"+register_name.fields_data[i]["actual_name"]+";", rtl_write)
		else:
			module_write("      if ("+register_name.register["write_signal_name"]+ ")", rtl_write)
			module_write("        "+register_name.fields_data[i]["actual_name"]+" <= mpu_wdata"+register_name.fields_data[i]["bit_position"]+";", rtl_write)
		module_write("      else if ("+register_name.fields_data[i]["ro_name_en"]+")", rtl_write)
		module_write("        "+register_name.fields_data[i]["actual_name"]+" <= "+register_name.fields_data[i]["ro_name"]+";", rtl_write)

	else:
		module_write("      // HW has higher precedence", rtl_write)
		module_write("      if ("+register_name.fields_data[i]["ro_name_en"]+")", rtl_write)
		module_write("        "+register_name.fields_data[i]["actual_name"]+" <= "+register_name.fields_data[i]["ro_name"]+";", rtl_write)
		if re.match("1S",register_name.fields_data[i]["modifiedWriteValue"]):
			module_write("      else if ("+register_name.register["write_signal_name"]+ " & |mpu_wdata"+register_name.fields_data[i]["bit_position"]+" & ~|"+register_name.fields_data[i]["actual_name"]+")", rtl_write)
			module_write("        "+register_name.fields_data[i]["actual_name"]+" <= {"+str(register_name.fields_data[i]["bitWidth"])+"{1'b1}};", rtl_write)
		elif re.match("1C",register_name.fields_data[i]["modifiedWriteValue"]):
			module_write("      else if ("+register_name.register["write_signal_name"]+ " & |mpu_wdata"+register_name.fields_data[i]["bit_position"]+" & |"+register_name.fields_data[i]["actual_name"]+")", rtl_write)
			module_write("        "+register_name.fields_data[i]["actual_name"]+" <= {"+str(register_name.fields_data[i]["bitWidth"])+"{1'b0}};", rtl_write)
		elif register_name.fields_data[i]["modifiedWriteValue"] == "C":
			module_write("      else if ("+register_name.register["write_signal_name"]+ " & |"+register_name.fields_data[i]["actual_name"]+")", rtl_write)
			module_write("        "+register_name.fields_data[i]["actual_name"]+" <= {"+str(register_name.fields_data[i]["bitWidth"])+"{1'b0}};", rtl_write)
		elif register_name.fields_data[i]["modifiedWriteValue"] == "T":
			module_write("      else if ("+register_name.register["write_signal_name"]+ ")", rtl_write)
			module_write("        "+register_name.fields_data[i]["actual_name"]+" <= ~"+register_name.fields_data[i]["actual_name"]+";", rtl_write)
		else:
			module_write("      else if ("+register_name.register["write_signal_name"]+ ")", rtl_write)
			module_write("        "+register_name.fields_data[i]["actual_name"]+" <= mpu_wdata"+register_name.fields_data[i]["bit_position"]+";", rtl_write)
	module_write("    end //}", rtl_write)
	module_write("  end //}", rtl_write)



	
def rw_volatile_generate(register_name,i, rtl_write):
	module_write("  assign rst_"+register_name.fields_data[i]["actual_name"]+ " = "+register_name.fields_data[i]["_resetValue_"]+";\n", rtl_write)
	module_write("  generate\n  for(i = 0; i < "+str(register_name.fields_data[i]["bitWidth"])+"; i = i+1) begin : GENERATE_"+register_name.fields_data[i]["actual_name"].upper()+" //{", rtl_write)
	field_name = register_name.fields_data[i]["actual_name"].upper()
	module_write("  "+first_line+" //{", rtl_write)
	module_write("      if (~reset_n)", rtl_write)
	module_write("        "+register_name.fields_data[i]["actual_name"]+"[i] <= rst_"+register_name.fields_data[i]["actual_name"]+"[i];", rtl_write)
	module_write("      else begin //{", rtl_write)
	if (register_name.fields_data[i]["_sysrdl_precedence_"] == True):
		module_write("        // FW has higher precedence", rtl_write)
		if re.match("1S",register_name.fields_data[i]["modifiedWriteValue"]):
			module_write("        if ("+register_name.register["write_signal_name"]+ " & mpu_wdata["+str(register_name.fields_data[i]["bitOffset"])+"+i] & ~"+register_name.fields_data[i]["actual_name"]+"[i])", rtl_write)
			module_write("          "+register_name.fields_data[i]["actual_name"]+"[i] <= 1'b1;", rtl_write)
		elif re.match("1C",register_name.fields_data[i]["modifiedWriteValue"]):
			module_write("        if ("+register_name.register["write_signal_name"]+ " & mpu_wdata["+str(register_name.fields_data[i]["bitOffset"])+"+i] & "+register_name.fields_data[i]["actual_name"]+"[i])", rtl_write)
			module_write("          "+register_name.fields_data[i]["actual_name"]+"[i] <= 1'b0;", rtl_write)
		elif register_name.fields_data[i]["modifiedWriteValue"] == "C":
			module_write("        if ("+register_name.register["write_signal_name"]+ " & |"+register_name.fields_data[i]["actual_name"]+")", rtl_write)
			module_write("          "+register_name.fields_data[i]["actual_name"]+"[i] <= {"+str(register_name.fields_data[i]["bitWidth"])+"{1'b0}};", rtl_write)
		elif register_name.fields_data[i]["modifiedWriteValue"] == "T":
			module_write("        if ("+register_name.register["write_signal_name"]+ ")", rtl_write)
			module_write("          "+register_name.fields_data[i]["actual_name"]+"[i] <= ~"+register_name.fields_data[i]["actual_name"]+"[i];", rtl_write)
		else:
			module_write("        if ("+register_name.register["write_signal_name"]+ ")", rtl_write)
			module_write("          "+register_name.fields_data[i]["actual_name"]+"[i] <= mpu_wdata["+str(register_name.fields_data[i]["bitOffset"])+"+i];", rtl_write)
		module_write("        else if ("+register_name.fields_data[i]["ro_name_en"]+"[i])", rtl_write)
		module_write("          "+register_name.fields_data[i]["actual_name"]+"[i] <= "+register_name.fields_data[i]["ro_name"]+"[i];", rtl_write)

	else:
		module_write("        // HW has higher precedence", rtl_write)
		module_write("        if ("+register_name.fields_data[i]["ro_name_en"]+"[i])", rtl_write)
		module_write("          "+register_name.fields_data[i]["actual_name"]+"[i] <= "+register_name.fields_data[i]["ro_name"]+"[i];", rtl_write)
		if re.match("1S",register_name.fields_data[i]["modifiedWriteValue"]):
			module_write("        else if ("+register_name.register["write_signal_name"]+ " & mpu_wdata["+str(register_name.fields_data[i]["bitOffset"])+"+i] & ~"+register_name.fields_data[i]["actual_name"]+"[i])", rtl_write)
			module_write("          "+register_name.fields_data[i]["actual_name"]+"[i] <= 1'b1;", rtl_write)
		elif re.match("1C",register_name.fields_data[i]["modifiedWriteValue"]):
			module_write("        else if ("+register_name.register["write_signal_name"]+ " & mpu_wdata["+str(register_name.fields_data[i]["bitOffset"])+"+i] & "+register_name.fields_data[i]["actual_name"]+"[i])", rtl_write)
			module_write("          "+register_name.fields_data[i]["actual_name"]+"[i] <= 1'b0;", rtl_write)
		elif register_name.fields_data[i]["modifiedWriteValue"] == "C":
			module_write("        else if ("+register_name.register["write_signal_name"]+ " & |"+register_name.fields_data[i]["actual_name"]+")", rtl_write)
			module_write("        "+register_name.fields_data[i]["actual_name"]+"[i] <= {"+str(register_name.fields_data[i]["bitWidth"])+"{1'b0}};", rtl_write)
		elif register_name.fields_data[i]["modifiedWriteValue"] == "T":
			module_write("        else if ("+register_name.register["write_signal_name"]+ ")", rtl_write)
			module_write("        "+register_name.fields_data[i]["actual_name"]+"[i] <= ~"+register_name.fields_data[i]["actual_name"]+"[i];", rtl_write)
		else:
			module_write("        else if ("+register_name.register["write_signal_name"]+ ")", rtl_write)
			module_write("          "+register_name.fields_data[i]["actual_name"]+"[i] <= mpu_wdata["+str(register_name.fields_data[i]["bitOffset"])+"+i];", rtl_write)
	module_write("      end //}", rtl_write)
	module_write("    end //}", rtl_write)
	module_write("  end //}", rtl_write)
	module_write("  endgenerate", rtl_write)



def search_for_blocks(name,regular_expression_start,regular_expression_end):
	a=[0,0];
	count = 0;
	while count <len(name):
		if (re.search(regular_expression_start,name[count],0)):
			a[0] = count
		if (re.search(regular_expression_end,name[count],0)):
			a[1] = count
			return a
		count += 1;


class Register:

	def __init__(self):
		self.register = {"name":"","description":"","addressOffset":"","reset_n":"","no_of_fields":"","write_signal_name":"","read_signal_name":"","ro_name":""}
		self.field    = {"name":"","actual_name":"","description":"","bitOffset":"","bitWidth":"","modifiedWriteValue":"","_sysrdl_precedence_":"","volatile":"","fw_access":"","hw_access":"","_resetValue_":"","bit_position":"","LSB":"","MSB":"","bit_square":"","ro_name":"","ro_name_en":"","generate":""}
		self.fields_data = []
		

class Set_of_Registers:
	def __init__(self):
		self.registers = []


def joining(i,end_character):
	first_end_join = [i]
	while True:
		if re.search(end_character,master_list[i]):
			first_end_join.append(i)
			return first_end_join
		else: 
			i+=1

			
def interface_names(total_registers, write_rtl, data_width = 32, addr_width = 32, align_space = 35):
        
        module_write("  %-*s          clk," %(align_space-9,"input "), write_rtl)
        module_write("  %-*s          reset_n," %(align_space-9,"input "), write_rtl)
	
        for i in range(len(total_registers.registers)):
	        module_write("\n //"+total_registers.registers[i].register["name"]+" : " + total_registers.registers[i].register["addressOffset"], write_rtl)
	        #module_write("  output wire          "+total_registers.registers[i].register["write_signal_name"]+",")
	        module_write("  %-*s %s," %(align_space, "output wire ", total_registers.registers[i].register["write_signal_name"]), write_rtl)
	        module_write("  %-*s %s," %(align_space, "output wire", total_registers.registers[i].register["read_signal_name"]), write_rtl)
	        module_write("  %-*s %s," %(align_space, "output reg  [DATA_WIDTH - 1:0] ", total_registers.registers[i].register["ro_name"]), write_rtl)
	        for j in range(total_registers.registers[i].register["no_of_fields"]) :
                        if total_registers.registers[i].fields_data[j]["ro_name"] != "":
                               if total_registers.registers[i].fields_data[j]["bitWidth"] > 1:
                                        module_write("  %-*s %s," %(align_space, "input       "+total_registers.registers[i].fields_data[j]["bit_square"], total_registers.registers[i].fields_data[j]["ro_name"]), write_rtl)
                               else:
                                        module_write("  %-*s %s," %(align_space, "input ", total_registers.registers[i].fields_data[j]["ro_name"]), write_rtl)
		
                               if total_registers.registers[i].fields_data[j]["ro_name_en"] != "" :
                                        if total_registers.registers[i].fields_data[j]["generate"]:
                                                module_write("  %-*s %s," %(align_space, "input       "+total_registers.registers[i].fields_data[j]["bit_square"],total_registers.registers[i].fields_data[j]["ro_name_en"]), write_rtl)
                                        else:
                                                module_write("  %-*s %s," %(align_space, "input",total_registers.registers[i].fields_data[j]["ro_name_en"]), write_rtl)

                        if total_registers.registers[i].fields_data[j]["fw_access"] == "RW" or total_registers.registers[i].fields_data[j]["fw_access"] == "WO":
                                if total_registers.registers[i].fields_data[j]["bitWidth"] > 1:
                                        module_write("  %-*s %s," %(align_space, "output reg  "+total_registers.registers[i].fields_data[j]["bit_square"], total_registers.registers[i].fields_data[j]["actual_name"]), write_rtl)
                                else:
                                        module_write("  %-*s %s," %(align_space, "output reg ", total_registers.registers[i].fields_data[j]["actual_name"]), write_rtl)
			
        module_write("\n\n //Write Path", write_rtl)
        module_write("  %-*s %s," %(align_space, "input       [DATA_WIDTH - 1:0] ", "mpu_wdata"), write_rtl)
        module_write("  %-*s %s," %(align_space, "input","mpu_we"), write_rtl)
        module_write("  %-*s %s," %(align_space, "input       [ADDR_WIDTH - 1 :0] ", "mpu_wr_addr"), write_rtl)
        module_write("  %-*s %s," %(align_space, "output reg ","mpu_wready"), write_rtl)
        module_write("\n\n //Read Path", write_rtl)
        module_write("  %-*s %s," %(align_space, "output reg  [DATA_WIDTH - 1:0]","mpu_rdata"), write_rtl)
        module_write("  %-*s %s," %(align_space, "input ", "mpu_re"), write_rtl)
        module_write("  %-*s %s," %(align_space, "input       [ADDR_WIDTH - 1:0]", "mpu_rd_addr"), write_rtl)
        module_write("  %-*s %s\n);\n\n"  %(align_space, "output reg", "mpu_rvalid"), write_rtl)


def read_write_def(total_registers, rtl_write):
	for i in range(len(total_registers.registers)):
		module_write(" assign "+total_registers.registers[i].register["write_signal_name"]+" = mpu_we & (mpu_wr_addr == "+re.sub("0x","32'h",total_registers.registers[i].register["addressOffset"])+");", rtl_write)
		module_write(" assign "+total_registers.registers[i].register["read_signal_name"] +" = mpu_re & (mpu_rd_addr == "+re.sub("0x","32'h",total_registers.registers[i].register["addressOffset"])+");\n\n", rtl_write)



def writing_always(total_registers, rtl_write):
	for i in range(len(total_registers.registers)):
		module_write("\n\n\n //=================================================================================", rtl_write)
		module_write(" // Register Name : "+total_registers.registers[i].register["name"], rtl_write)
		module_write(" // Address       : "+total_registers.registers[i].register["addressOffset"], rtl_write)
		module_write(" // Fields        : "+str(total_registers.registers[i].register["no_of_fields"]), rtl_write)
		module_write(" // Description   : "+total_registers.registers[i].register["description"], rtl_write)
		module_write(" //=================================================================================", rtl_write)
		for j in range(total_registers.registers[i].register["no_of_fields"]) :
	
			if total_registers.registers[i].fields_data[j]["fw_access"] == "RW" or total_registers.registers[i].fields_data[j]["fw_access"] == "WO":
				module_write("\n\n\n // Field Name    : "+total_registers.registers[i].fields_data[j]["name"], rtl_write)
				module_write(" // Bit Position  : "+str(total_registers.registers[i].fields_data[j]["bit_position"]), rtl_write)
				module_write(" // FW Access     : "+total_registers.registers[i].fields_data[j]["fw_access"]+total_registers.registers[i].fields_data[j]["modifiedWriteValue"], rtl_write)
				module_write(" // HW Access     : "+total_registers.registers[i].fields_data[j]["hw_access"], rtl_write)
				module_write(" // Description   : "+total_registers.registers[i].fields_data[j]["description"]+"\n", rtl_write)
				
				if total_registers.registers[i].fields_data[j]["volatile"] == False:
					rw_non_volatile(total_registers.registers[i],j, rtl_write)
				elif total_registers.registers[i].fields_data[j]["generate"] == True: 
					rw_volatile_generate(total_registers.registers[i],j, rtl_write)
				else:
					rw_volatile(total_registers.registers[i],j, rtl_write)
#				if (total_registers.registers[i].fields_data[j]["modifiedWriteValue"] == "1S" and total_registers.registers[i].fields_data[j]["bitWidth"] > 1):
#					module_write("  end //}\n  endgenerate\n\n")
				
		combo_always(total_registers,i, rtl_write)


def combo_always(total_registers,i, rtl_write, data_width = 32):
		reg_name = total_registers.registers[i].register["name"]
		address_val = total_registers.registers[i].register["addressOffset"]
		module_write("\n\n always @(*) begin : "+reg_name.lower()+"_"+address_val+"_blk //{", rtl_write)
		reg_len = len(total_registers.registers[i].register["ro_name"])
		if total_registers.registers[i].fields_data[0]["bitWidth"] != data_width:
			module_write("   %-*s = %s;" %(reg_len+12,total_registers.registers[i].register["ro_name"], "{DATA_WIDTH{1'b0}}"), rtl_write)
		for j in range(total_registers.registers[i].register["no_of_fields"]) :
			if total_registers.registers[i].fields_data[j]["fw_access"] == "RW":
				module_write("   %-*s = %s;" %(reg_len + 12, total_registers.registers[i].register["ro_name"]+total_registers.registers[i].fields_data[j]["bit_position"], total_registers.registers[i].fields_data[j]["actual_name"]), rtl_write)
			elif total_registers.registers[i].fields_data[j]["fw_access"] == "WO":
				module_write("   "+total_registers.registers[i].register["ro_name"]+total_registers.registers[i].fields_data[j]["bit_position"]+ " = "+total_registers.registers[i].register["read_signal_name"]+" ? "+str(total_registers.registers[i].fields_data[j]["bitWidth"])+"'h0"+" : "+total_registers.registers[i].fields_data[j]["actual_name"]+";", rtl_write)
			else:
				module_write("   "+total_registers.registers[i].register["ro_name"]+total_registers.registers[i].fields_data[j]["bit_position"]+ " = "+total_registers.registers[i].fields_data[j]["ro_name"]+";", rtl_write)
		module_write(" end //}\n", rtl_write)




def writing_always_read(total_registers,case, rtl_write):
        module_write("\n\n\n\n\n //=================================================================================", rtl_write)
        module_write(" // SFR Reads", rtl_write)
        module_write(" //=================================================================================\n", rtl_write)
        if case:
                writing_always_read_case(total_registers, rtl_write)
        else:
                for i in range(len(total_registers.registers)):
                        if i == 0:
                                module_write("  assign mpu_rdata_combo = ({DATA_WIDTH{"+total_registers.registers[i].register["read_signal_name"]+"}} & "+total_registers.registers[i].register["ro_name"]+") |", rtl_write)
                        elif i == len(total_registers.registers) - 1:
                                module_write("                           ({DATA_WIDTH{"+total_registers.registers[i].register["read_signal_name"]+"}} & "+total_registers.registers[i].register["ro_name"]+");", rtl_write)
                        else:
                                module_write("                           ({DATA_WIDTH{"+total_registers.registers[i].register["read_signal_name"]+"}} & "+total_registers.registers[i].register["ro_name"]+") |", rtl_write)
        module_write("\n\n", rtl_write)




def writing_always_read_case(total_registers, rtl_write):
        max_length = 10
        for i in range(len(total_registers.registers)):
                if len(total_registers.registers[i].register["read_signal_name"]) > max_length:
                        max_length =  len(total_registers.registers[i].register["read_signal_name"])
                        logging.debug("Register name for Case statement is is %s" %(total_registers.registers[i].register["name"]))
        module_write("  always @(*) begin //{", rtl_write)
        module_write("    case (1'b1)", rtl_write)
      
        for i in range(len(total_registers.registers)):
                #module_write("     "+total_registers.registers[i].register["read_signal_name"]+": mpu_rdata_combo = "+total_registers.registers[i].register["ro_name"]+";")
                module_write("      %-*s : mpu_rdata_combo = %s;" %(max_length+2,total_registers.registers[i].register["read_signal_name"], total_registers.registers[i].register["ro_name"]), rtl_write)
        module_write("      %-*s : mpu_rdata_combo = {DATA_WIDTH{1'b0}};" %(max_length+2,"default"), rtl_write)
        module_write("   endcase", rtl_write)
        module_write(" end //}", rtl_write)


def reg_ro(total_registers):
	module_write("//===============================Reg Declaration==============================", rtl_write)
	for i in range(len(total_registers.registers)):
		for j in range(total_registers.registers[i].register["no_of_fields"]):
			if (total_registers.registers[i].fields_data[j]["fw_access"] == "RW"):
				module_write("  reg  "+total_registers.registers[i].fields_data[j]["bit_square"]+"  "+total_registers.registers[i].fields_data[j]["actual_name"]+";", rtl_write)
	module_write("//============================================================================/n/n", rtl_write)


def wire_declaration(total_registers, case, write_rtl, align_space = 35):
        module_write("//==============================Wire Declaration==============================\n", write_rtl)
        for i in range(len(total_registers.registers)):
                for j in range(total_registers.registers[i].register["no_of_fields"]):
                        if total_registers.registers[i].fields_data[j]["generate"]:
                                module_write("  %-*s %s;" %(align_space, "wire        "+total_registers.registers[i].fields_data[j]["bit_square"], "rst_"+total_registers.registers[i].fields_data[j]["actual_name"]), write_rtl)
        if case:
                module_write("  %-*s %s;\n" %(align_space, "reg         [DATA_WIDTH - 1:0] ", "mpu_rdata_combo"), write_rtl)
        else:
                module_write("  %-*s %s;\n" %(align_space, "wire        [DATA_WIDTH - 1:0] ", "mpu_rdata_combo"), write_rtl)
        module_write("  genvar       i;\n", write_rtl)
        module_write("//============================================================================\n\n", write_rtl)

def tapping_fields(i, registers):
	count = i;
	field_obj = Register()
	desc = "description     "
	while True:
		if re.search(r'</spirit:field>',registers[count]):
			field_obj.field["MSB"] =  field_obj.field["bitOffset"]+field_obj.field["bitWidth"]-1
			field_obj.field["LSB"] =  field_obj.field["bitOffset"]
			field_obj.field["volatile"] =  False if field_obj.field["volatile"] == "" else field_obj.field["volatile"]
			field_obj.field["hw_access"] =  "RW" if field_obj.field["volatile"] == True else "RO"
			if field_obj.field["bitWidth"] > 1:
				field_obj.field["bit_position"] = "["+str(field_obj.field["MSB"])+":"+str(field_obj.field["LSB"])+"]"
				field_obj.field["bit_square"] = "["+str(field_obj.field["bitWidth"]-1)+":0]"
			else:
				field_obj.field["bit_position"] = "["+str(field_obj.field["bitOffset"])+"]"
			field_obj.fields_data.append(field_obj.field)
			return field_obj

		if field_obj.field["name"] == "":
			m=re.search(r'<spirit:name>(.*)</spirit:name>',registers[count])
			if m:
				field_obj.field["name"] = m.group(1)

		if field_obj.field["_sysrdl_precedence_"] == "":
			m=re.search(r'<spirit:name>_sysrdl_precedence_',registers[count])
			if m:
				field_obj.field["_sysrdl_precedence_"] = True

		if field_obj.field["description"] == "":
			if (re.search(r'<spirit:description>',registers[count])):
				m=re.search(r'<spirit:description>(.*)</spirit:description>',registers[count])
				if m:
					field_obj.field["description"] = m.group(1)
				else:
					while True:
						m = re.search(r'<spirit:description>(.*)',registers[count])
						n = re.search(r'(.*)</spirit:description>',registers[count])
						if (m and not(n)):
							#field_obj.field["description"] += "\n // "+len(desc)*" "+m.group(1)
							field_obj.field["description"] += m.group(1)
						elif (not(m) and n):
							field_obj.field["description"] += "\n // "+len(desc)*" "+n.group(1)
							break
						else:
							field_obj.field["description"] += "\n // "+len(desc)*" "+registers[count]
						count +=1

	
		if field_obj.field["_resetValue_"] == "":
			if (re.search(r'<spirit:name>_resetValue_</spirit:name>',registers[count])):
				count +=1
				m=re.search(r'<spirit:value>(.*)</spirit:value>',registers[count])
				if m:
					field_obj.field["_resetValue_"] = re.sub("0x",str(field_obj.field["bitWidth"])+"'h",m.group(1))


		if field_obj.field["bitOffset"] == "":
			m=re.search(r'<spirit:bitOffset>(.*)</spirit:bitOffset>',registers[count])
			if m:
				field_obj.field["bitOffset"] = int(m.group(1))
				
		if field_obj.field["modifiedWriteValue"] == "":
			m=re.search(r'<spirit:modifiedWriteValue>(.*)</spirit:modifiedWriteValue>',registers[count])
			if m:
				if (m.group(1) == "oneToClear"):
					field_obj.field["modifiedWriteValue"] = "1C"
				elif (m.group(1) == "oneToSet"):
					field_obj.field["modifiedWriteValue"] = "1S"
				elif (m.group(1) == "oneToToggle"):
					field_obj.field["modifiedWriteValue"] = "1T"
				elif (m.group(1) == "clear"):
					field_obj.field["modifiedWriteValue"] = "C"
				else:
					field_obj.field["modifiedWriteValue"] = "S"
				
		if field_obj.field["bitWidth"] == "":
			m=re.search(r'<spirit:bitWidth>(.*)</spirit:bitWidth>',registers[count])
			if m:
				field_obj.field["bitWidth"] = int(m.group(1))
				
		if field_obj.field["volatile"] == "":
			m=re.search(r'<spirit:volatile>(.*)</spirit:volatile>',registers[count])
			if m:
				field_obj.field["volatile"] = True if re.search(r'true',m.group(1),re.I) else False
				
		if field_obj.field["fw_access"] == "":
			m=re.search(r'<spirit:access>(.*)</spirit:access>',registers[count])
			if m:
				if (m.group(1) == "read-write"):
					field_obj.field["fw_access"] = "RW"
				elif (m.group(1) == "write-only"):
					field_obj.field["fw_access"] = "WO"
				else:
					field_obj.field["fw_access"] = "RO"
		count = count + 1;


def sfr_verilog_code(xml, module_name, data_width = 32, addr_width = 32):
        assert os.path.exists(xml), "xml does not exists in path %s" %(os.getcwd())
        sfr_module_name = module_name
        try:
                rtl_write = open(module_name+".v","w")
        except:
                ValueError("%s.v file canot be opened for write" %(module_name))                
                
        file=open(xml,"r")
        list1 = file.readlines()
        list2 = list(filter(lambda x:x != "\n", list1))
        list3 = [re.sub("\n","",x) for x in list2]
        list4 = [re.sub("\s*$","",x) for x in list3]
        master_list = [re.sub("^\s*","",x) for x in list4]
        total_registers = Set_of_Registers()
        case = True
	
        total_registers_start = [index for index, value in enumerate(master_list) if value == "<spirit:register>"]
        total_registers_end   = [index for index, value in enumerate(master_list) if value == "</spirit:register>"]
	
        for tk,tk1 in zip(total_registers_start,total_registers_end):
                count_reg = search_for_blocks(master_list,register_start,register_end)
                registers = master_list[tk:tk1]
                ii = [index for index, value in enumerate(registers) if value == "<spirit:field>"]
                register_obj = Register()
		
                register_obj.register["no_of_fields"] = registers.count("<spirit:field>")
                if registers != None:
                        i = 0;
                        while i < len(registers):
                                if (register_obj.register["name"] == ""):
                                        m = re.search(name_start+r'(.*)'+name_end,registers[i])
                                        if m:
                                                register_obj.register["name"] = m.group(1)
		
                                if (register_obj.register["description"] == ""):
                                        m = re.search(desc_start+r'(.*)'+desc_end,registers[i])
                                        if m:
                                                register_obj.register["description"] = m.group(1)
		
                                if (register_obj.register["addressOffset"] == ""):
                                        m = re.search(addr_start+r'(.*)'+addr_end,registers[i])
                                        if m:
                                                register_obj.register["addressOffset"] = m.group(1).lower()

                                if (register_obj.register["name"] != "" and register_obj.register["description"] != "" and register_obj.register["addressOffset"] != ""):
                                        register_obj.register["write_signal_name"] = "fw_wr_"+register_obj.register["name"].lower()
                                        register_obj.register["read_signal_name"] = "fw_rd_"+register_obj.register["name"].lower()
                                        register_obj.register["ro_name"] = register_obj.register["name"].lower()
                                        break
                                i = i+1
                                
                        for i in ii:
                                field_obj_temp = Register() 
                                field_obj_temp = tapping_fields(i,registers)
                                if field_obj_temp.field["volatile"] == True:
                                        field_obj_temp.field["ro_name"] = "hw_wr_"+register_obj.register["name"].lower()+"_"+field_obj_temp.field["name"].lower()
                                        if field_obj_temp.field["fw_access"] != "RO":
                                                field_obj_temp.field["ro_name_en"] = "hw_wr_"+register_obj.register["name"].lower()+"_"+field_obj_temp.field["name"].lower()+"_en"
                                field_obj_temp.field["actual_name"] = (register_obj.register["name"].lower()+"_"+field_obj_temp.field["name"]).lower()
                                if field_obj_temp.field["bitWidth"] > 1 and field_obj_temp.field["hw_access"] == "RW" and field_obj_temp.field["fw_access"] == "RW":
                                        field_obj_temp.field["generate"] = True
                                register_obj.fields_data.append(field_obj_temp.field)
                        del field_obj_temp
                        total_registers.registers.append(register_obj)	
                        del register_obj	
	
        localtime = time.asctime( time.localtime(time.time()) )

        module_write("\n\n// This is Auto Generated Code\n", rtl_write)
        module_write("// Scripting Language    : Python", rtl_write)
        module_write("// Developed By          : Rahul Harihara Iyer", rtl_write)
        module_write("// Module Generated Date : "+localtime, rtl_write)
        module_write("\n\n", rtl_write)
        #module_write("/*")
        #for i in range(len(total_registers.registers)):
        #	module_write(total_registers.registers[i].register["name"]+"\t\t\t "+total_registers.registers[i].register["addressOffset"])
        #module_write("*/\n\n")

        module_write("module "+sfr_module_name+" #(", rtl_write)
        module_write("  parameter DATA_WIDTH     = "+str(data_width)+",", rtl_write)
        module_write("  parameter STROBE_WIDTH   = DATA_WIDTH/8,", rtl_write)
        module_write("  parameter ADDR_WIDTH     = "+str(addr_width)+") (\n", rtl_write)
        interface_names(total_registers, rtl_write)
        #reg_ro(total_registers)
        wire_declaration(total_registers, case, rtl_write)
        module_write("//==============================Functionality   ==============================\n\n", rtl_write)
        read_write_def(total_registers, rtl_write)
        writing_always(total_registers, rtl_write)
        writing_always_read(total_registers, case, rtl_write)
        mpu_always(rtl_write)
        module_write("\n\n//$Log: "+sfr_module_name+".v,v $\n", rtl_write)	
        file.close()


def arguments_fetch():
        cmd = sys.argv[1:]
        if cmd.count("-m") > 0:
                sfr_module_name = cmd[cmd.index("-m")+1]
        else:
                sfr_module_name = "sfr"

        if cmd.count("-xml") == 1:
                xml_path = cmd[cmd.index("-xml")+1]
                assert os.path.exists(xml_path), "xml does not exists"
        else:
                raise ValueError("Format of input is ./sfr_code_.py -xml <xml file> -m <module name>")

        if cmd.count("-xls") > 0:
                write_ipxact(cmd[cmd.index("-xls")+1])

        sfr_verilog_code(xml_path, sfr_module_name)
