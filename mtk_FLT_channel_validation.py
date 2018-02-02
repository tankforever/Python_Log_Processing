# -*- coding: utf-8 -*-
"""
Created on Thu Jan 25 16:04:19 2018

@author: MTK14660
"""

import os
import mace
import csv
import datetime
from openpyxl import Workbook

##################################################################
# 读取calibration table, 只保留标记为y的item    
def read_csv_get_todo_item(cwd,csv_file_name):
    with open(os.path.join(current_work_dir, csv_file_name),'r') as csv_r:
        reader = csv.DictReader(csv_r)
        for rr in reader:
                rlf_time=rr["RLF time"]
    
    return int(rlf_time)
##################################################################
    

##################################################################
# 查找以'MDLog1'为前缀的文件夹
def find_MDLog1(root,search_item):
    
    walk_res=[]
    for root,dirs,files in os.walk(root):
        walk_res.append((root,dirs,files))
    
    all_MDlog1=[]
    for w in walk_res:
        root=w[0]         #root
        basename=os.path.basename(root)
        if search_item in basename:
            #搜索.elg or .muxz
            files = w[2]  #files
            for f in files:
                if '.muxz' in f or '.elg' in f:
                    all_MDlog1.append(w)
                    break
    del walk_res
    
    return all_MDlog1
##################################################################
    

##################################################################
# 找到\check_calibration文件夹下,包含.elg or .muxz文件的子文件夹
def get_root_dirs_path(current_work_dir,all_MDLog1):
    root_dirs_path=[]
    cwd_split_len=len(current_work_dir.split('\\'))
    for i in all_MDLog1:
        temp1=i[0]           #root
        temp2=temp1.split('\\')
        temp3=temp2[0:cwd_split_len+1]
        temp4="\\".join(temp3)
        root_dirs_path.append(temp4)
    root_dirs_path={}.fromkeys(root_dirs_path).keys()   #删除重复元素 
    
    return root_dirs_path
##################################################################

 
################################################################## 
#将root_dirs分类，有相同root的all_MDLog1放在一起
# {root_dir1:[all_MDLog1[0],all_MDLog1[1]], root_dir2:[all_MDLog1[3],all_MDLog1[4]]}    
def classify_same_root(root_dirs_path,all_MDLog1):
    root_dirs_dict=dict()
    for rdp in root_dirs_path:
        temp1=[]
        for aM in all_MDLog1:
            temp2=aM[0].split('\\')    #root
            if os.path.basename(rdp) in temp2:
                temp1.append(aM)
        root_dirs_dict[rdp]=temp1
    
    return root_dirs_dict
##################################################################

##################################################################
# 提取出'MDLog1_2010_0101_081936_data.muxz'中的20100101081936
def parsing_filename(file_name):
    temp1=file_name.split(".")[0]
    temp2=temp1.split("_")[1:4]   # 获取['2017','1201','180008']
    temp3="".join(temp2)
    temp4=int(temp3)
    
    return temp4
##################################################################
    

##################################################################    
#获取全部.muxz or .elg files
#{file1:(root,muxz_file_path,muxz/elg_flag,EDB_file),file2:(),file3:()}
def get_all_muxz_elg_files(root_path,list_root_path_file,muxz_ext,elg_ext):
    muxz_elg_flag=0   # 1:muxz,2:elg
    all_muxz_elg={}
    for r_f_f in list_root_path_file[root_path]:
        root = r_f_f[0]
        files=r_f_f[2]
        
        #先检查是否存在.muxz
        for files_tmp in files:
            if muxz_ext in files_tmp:
                muxz_elg_flag = 1
                break
        #若不存在.muxz, 再检查.elg
        if 0 == muxz_elg_flag:
            for files_tmp in files:
                if elg_ext in files_tmp:
                    muxz_elg_flag = 2
                    break
      
        if 0 == muxz_elg_flag:
            raise ValueError(".muxz & .elg files DO NOT exist!")
        
        if 1 == muxz_elg_flag:
             #得到EDB文件
            EDB_file=[content for content in files if "EDB" == content[-3:] if "MDDB_" == content[0:5]]
            EDB_file_path=os.path.join(root,EDB_file[0])
            
            #得到全部.muxz文件
            for files_tmp in files:
                if muxz_ext in files_tmp:
                    time_in_filename=parsing_filename(files_tmp)
                    if time_in_filename in all_muxz_elg.keys():
                        raise ValueError("repetitive .muxz file name")
                    else:
                        all_muxz_elg[time_in_filename]=(root,files_tmp,muxz_ext,EDB_file_path)
        elif 2 == muxz_elg_flag:
            EDB_file_path=None
            #得到全部.elg文件
            for files_tmp in files:
                if elg_ext in files_tmp:
                    time_in_filename=parsing_filename(files_tmp)
                    all_muxz_elg[time_in_filename]=(root,files_tmp,elg_ext,EDB_file_path)
        else:
            raise ValueError("Wrong muxz_elg_flag value!")
        return all_muxz_elg
##################################################################
   
##################################################################
#二分查找
#def search_item(start,end,search_index,itemset):
#    middle=(start+end)/2
#    tmp_idx=itemset[middle].device_time
#    
#    if  tmp_idx == search_index:
#        return middle
#    elif tmp_idx < search_index:
#        search_item(middle,end,search_index,itemset)
#    else:
#        search_item(start,middle,search_index,itemset)
##################################################################
        
    
##################################################################
# 解析.muxz or .elg log
def parsing_log(root_path,list_root_path_file):
    
    muxz_ext=".muxz"
    elg_ext=".elg"
    #获取全部.muxz or .elg files
    #{文件名:(文件属性:根文件path,muxz/elg文件名,.muxz/.elg后缀,EDB_file_path)}
    #{file1:(root,muxz_file_name,muxz/elg_flag,EDB_file),file2:(),file3:()}
    all_muxz_elg=get_all_muxz_elg_files(root_path,list_root_path_file,muxz_ext,elg_ext)
    
    #对.muxz or .elg file按照时间顺序排序进行排序
    sort_muxz_elg_keys=all_muxz_elg.keys()
    sort_muxz_elg_keys.sort() 
    
    all_cell_info=[]
    all_meas_rssi_rscp=[]
    all_meas_snr=[]
    all_meas_md=[]
    all_meas_sd=[]
    #调用mace模块开始分析log
    for sort_key in sort_muxz_elg_keys:
        if all_muxz_elg[sort_key][2] == muxz_ext:  #.muxz后缀
            #                                                 root_path            file_name                          
            logfile = mace.open_log_file(os.path.join(all_muxz_elg[sort_key][0],all_muxz_elg[sort_key][1]), database=all_muxz_elg[sort_key][3])
        elif all_muxz_elg[sort_key][2] == elg_ext: #.elg后缀
            logfile = mace.open_log_file(os.path.join(all_muxz_elg[sort_key][0],all_muxz_elg[sort_key][1]))
        
        ######### cell info #########
        itemset = mace.create_itemset(logfile)
        cell_info_ps ='GP1_MEAS_SERVING_MEAS_RESULTS'
        itemset.subscribe_ps(cell_info_ps)
        
        len_itemset=len(itemset)
        if len_itemset == 0:
            raise ValueError("{} do not exist!".format(cell_info_ps))
        
        for i in itemset:
            all_cell_info.append(i)
            
        #########output: RSSI & RSRP #########
        itemset = mace.create_itemset(logfile)
        meas_rssi_rscp_ps = 'GP1_MEAS_SCM_ONE_SHOT_RESULT_4'
        itemset.subscribe_ps(meas_rssi_rscp_ps)
        
        len_itemset=len(itemset)
        if len_itemset == 0:
            raise ValueError("{} do not exist!".format(meas_rssi_rscp_ps))        
        for i in itemset:
            all_meas_rssi_rscp.append(i)
            
        #########output: snr #########
        itemset = mace.create_itemset(logfile)
        meas_snr_l1 = 'EL1_CH_RX_QUAL_RPT_OS_SNR'
        itemset.subscribe_l1(meas_snr_l1)
        
        len_itemset=len(itemset)
        if len_itemset == 0:
            raise ValueError("{} do not exist!".format(meas_snr_l1))        
        for i in itemset:
            all_meas_snr.append(i)
          
        #########output: md #########
        itemset = mace.create_itemset(logfile)
        meas_md_l1 = 'EL1D_TRC_RX_DRPT_INNER_MD'
        itemset.subscribe_l1(meas_md_l1)
        
        len_itemset=len(itemset)
        if len_itemset == 0:
            raise ValueError("{} do not exist!".format(meas_md_l1))        
        for i in itemset:
            all_meas_md.append(i)
        
        #########output: sd #########
        itemset = mace.create_itemset(logfile)
        meas_sd_l1 = 'EL1D_TRC_RX_FWS_RPT_COMB_1'
        itemset.subscribe_l1(meas_sd_l1)
        
        len_itemset=len(itemset)
        if len_itemset == 0:
            raise ValueError("{} do not exist!".format(meas_sd_l1))        
        for i in itemset:
            all_meas_sd.append(i)
     
        
    #对全部cell_info进行分段
    block_idx=1
    pci=int(all_cell_info[0][1])
    freq=int(all_cell_info[0][2])
    start_time=all_cell_info[0].device_time
#    param_item=["RSRP_RX0","RSRP_RX1","RSSI_RX0","RSSI_RX1","RSRQ_RX0","RSRQ_RX1","SNR_RX0","SNR_RX1","MD_IDX","SD_IDX"]
#    meas_data={}.fromkeys(param_item,list())
    meas_data = {"RSRP_RX0":[],"RSRP_RX1":[],"RSSI_RX0":[],"RSSI_RX1":[],"RSRQ_RX0":[],"RSRQ_RX1":[],"SNR_RX0":[],"SNR_RX1":[],"MD_IDX":[],"SD_IDX":[]}
    cell_info_block={block_idx:{"PCI":pci,"FREQ":freq,"START_TIME":start_time,"END_TIME":None,"MEAS_DATA":meas_data}}
    for c_i_tmp in all_cell_info:
        pci_tmp=int(c_i_tmp[1])
        freq_tmp=int(c_i_tmp[2])
        #上一块最后一次的时间是下一块的开始时间
        cell_info_block[block_idx]["END_TIME"]=c_i_tmp.device_time
        if pci_tmp != pci or freq_tmp != freq:
            pci, freq=pci_tmp,freq_tmp
            block_idx = block_idx + 1
            #重新创建meas_data,否则cell_info_block中每个item中的meas_data指向同一个地址
            #会导致的结果是，写一个block中的meas_data，其他block的meas_data会同时写入相同的值
            meas_data = {"RSRP_RX0":[],"RSRP_RX1":[],"RSSI_RX0":[],"RSSI_RX1":[],"RSRQ_RX0":[],"RSRQ_RX1":[],"SNR_RX0":[],"SNR_RX1":[],"MD_IDX":[],"SD_IDX":[]}
            cell_info_block[block_idx]={"PCI":pci,"FREQ":freq,"START_TIME":c_i_tmp.device_time,"END_TIME":None,"MEAS_DATA":meas_data}
    #最后一块时间段的end time是最后一个muxz文件的endtime
    cell_info_block[block_idx]["END_TIME"]= logfile.end_time.device_time     
    
    ########## 填充RSRP& RSSI ###############
    block_i = 1
    for m_r_r_tmp in all_meas_rssi_rscp:
        if m_r_r_tmp.device_time < cell_info_block[block_i]["START_TIME"]:
            pass
        #上一块最后一次的时间是下一块的开始时间，消息的时间需要大于等于start time && 小于（不能小于等于）end time
        elif m_r_r_tmp.device_time >= cell_info_block[block_i]["START_TIME"] and m_r_r_tmp.device_time < cell_info_block[block_i]["END_TIME"]:
            cell_info_block[block_i]["MEAS_DATA"]["RSRP_RX0"].append(int(m_r_r_tmp[2]))
            cell_info_block[block_i]["MEAS_DATA"]["RSRP_RX1"].append(int(m_r_r_tmp[3]))
            cell_info_block[block_i]["MEAS_DATA"]["RSSI_RX0"].append(int(m_r_r_tmp[8]))
            cell_info_block[block_i]["MEAS_DATA"]["RSSI_RX1"].append(int(m_r_r_tmp[9]))
            cell_info_block[block_i]["MEAS_DATA"]["RSRQ_RX0"].append(int(m_r_r_tmp[2]) - int(m_r_r_tmp[8]))
            cell_info_block[block_i]["MEAS_DATA"]["RSRQ_RX1"].append(int(m_r_r_tmp[3]) - int(m_r_r_tmp[9]))
        else:
           block_i = block_i + 1
    
    ########## 填充snr ##############
    block_i = 1
    for meas_tmp in all_meas_snr:
        if meas_tmp.device_time < cell_info_block[block_i]["START_TIME"]:
            pass
        elif meas_tmp.device_time >= cell_info_block[block_i]["START_TIME"] and meas_tmp.device_time < cell_info_block[block_i]["END_TIME"]:
            cell_info_block[block_i]["MEAS_DATA"]["SNR_RX0"].append(int(meas_tmp[1]))
            cell_info_block[block_i]["MEAS_DATA"]["SNR_RX1"].append(int(meas_tmp[2]))
        else:
           block_i = block_i + 1
       
    ########## 填充MD ###############
    block_i = 1
    for meas_tmp in all_meas_md:
        if meas_tmp.device_time < cell_info_block[block_i]["START_TIME"]:
            pass
        elif meas_tmp.device_time >= cell_info_block[block_i]["START_TIME"] and meas_tmp.device_time < cell_info_block[block_i]["END_TIME"]:
            cell_info_block[block_i]["MEAS_DATA"]["MD_IDX"].append(int(meas_tmp[1]))
        else:
           block_i = block_i + 1

    ########## 填充SD ###############      
    block_i = 1
    for meas_tmp in all_meas_sd:
        if meas_tmp.device_time < cell_info_block[block_i]["START_TIME"]:
            pass
        elif meas_tmp.device_time >= cell_info_block[block_i]["START_TIME"] and meas_tmp.device_time < cell_info_block[block_i]["END_TIME"]:
            cell_info_block[block_i]["MEAS_DATA"]["SD_IDX"].append(int(meas_tmp[10]))
        else:
           block_i = block_i + 1

    #########将结果保存到xlsx文件中#######
    wb = Workbook()
    ws = wb.active
    
    ## sheet1: Summary
    ws.title = "Summary"     #sheet name
    ws['A1'] = 'CELL_NUMBER'     #column title
    ws['B1'] = 'PCI'         #column title
    ws['C1'] = 'FREQ'        #column title
    ws['D1'] = 'START_TIME'  #column title
    ws['E1'] = 'END_TIME'    #column title
    for i in range(2, len(cell_info_block) + 2):
        ws['A' + str(i)] =  'cell_' + str(i - 1)
        ws['B' + str(i)] = cell_info_block[i - 1]['PCI']
        ws['C' + str(i)] = cell_info_block[i - 1]['FREQ']
        ws['D' + str(i)] = cell_info_block[i - 1]['START_TIME']
        ws['E' + str(i)] = cell_info_block[i - 1]['END_TIME']
    
    ## sheet2~sheetN:将不同的PCI信息写入不同的sheet在
    for i in range(1, len(cell_info_block) + 1):
        ws_cell = wb.create_sheet("cell_" + str(i))   #create new sheet
        
        ws_cell['A1'] = 'PCI'
        ws_cell['A2'] = cell_info_block[i]['PCI']
        
        ws_cell['B1'] = 'FREQ'
        ws_cell['B2'] = cell_info_block[i]['FREQ']
        
        ws_cell['C1'] = 'START TIME'
        ws_cell['C2'] = cell_info_block[i]['START_TIME']
        
        ws_cell['D1'] = 'END TIME'
        ws_cell['D2'] = cell_info_block[i]['END_TIME']
        
        ws_cell['E1'] = 'RSRP_RX0'
        for j,item in enumerate(cell_info_block[i]['MEAS_DATA']['RSRP_RX0']):
            ws_cell['E' + str(j + 2)] = item
            
        ws_cell['F1'] = 'RSRP_RX1' 
        for j,item in enumerate(cell_info_block[i]['MEAS_DATA']['RSRP_RX1']):
            ws_cell['F' + str(j + 2)] = item
        
        ws_cell['G1'] = 'RSSI_RX0'
        for j,item in enumerate(cell_info_block[i]['MEAS_DATA']['RSSI_RX0']):
            ws_cell['G' + str(j + 2)] = item
        
        ws_cell['H1'] = 'RSSI_RX1'
        for j,item in enumerate(cell_info_block[i]['MEAS_DATA']['RSSI_RX1']):
            ws_cell['H' + str(j + 2)] = item
        
        ws_cell['I1'] = 'RSRQ_RX0'
        for j,item in enumerate(cell_info_block[i]['MEAS_DATA']['RSRQ_RX0']):
            ws_cell['I' + str(j + 2)] = item
        
        ws_cell['J1'] = 'RSRQ_RX1'
        for j,item in enumerate(cell_info_block[i]['MEAS_DATA']['RSRQ_RX1']):
            ws_cell['J' + str(j + 2)] = item
        
        ws_cell['K1'] = 'SNR_RX0'
        for j,item in enumerate(cell_info_block[i]['MEAS_DATA']['SNR_RX0']):
            ws_cell['K' + str(j + 2)] = item
        
        ws_cell['L1'] = 'SNR_RX1'
        for j,item in enumerate(cell_info_block[i]['MEAS_DATA']['SNR_RX1']):
            ws_cell['L' + str(j + 2)] = item
        
        ws_cell['M1'] = 'MD_IDX'
        for j,item in enumerate(cell_info_block[i]['MEAS_DATA']['MD_IDX']):
            ws_cell['M' + str(j + 2)] = item
        
        ws_cell['N1'] = 'SD_IDX'
        for j,item in enumerate(cell_info_block[i]['MEAS_DATA']['SD_IDX']):
            ws_cell['N' + str(j + 2)] = item
        
    #保存文件
    output_path=os.path.join(root_path,"output.xlsx")
    wb.save(output_path)
    
    print os.path.basename(root_path)
    
##################################################################

#=========================== START MAIN ==========================    
if __name__ == "__main__":
    
    current_work_dir=os.getcwd()
    
    # 读取calibration table, 只保留标记为y的item
#    read_csv_file="check_RLF.csv"
#    rlf_time=read_csv_get_todo_item(current_work_dir, read_csv_file)
    
    # csv writer dict header
    #write_csv_header = ["Log"] + item_todo  
    
    # 找到全部以MDLog1为前缀的文件夹&&其中包含了.elg or .muxz文件
    # 返回数据结构为(root,folders,files)
    search_item='MDLog1'    
    all_MDLog1=find_MDLog1(current_work_dir,search_item)
    
    # 找到\check_calibration文件夹下,包含.elg or .muxz文件的子文件夹
    # 即e.g. \check_calibration\A_folder,\check_calibration\B_folder...
    # 得到A_folder,B_folder...
    root_dirs_path=get_root_dirs_path(current_work_dir, all_MDLog1)
    
    #将root_dirs_path分类，有相同root的all_MDLog1放在一起
    # {root_dir_path1:[all_MDLog1[0],all_MDLog1[1]], root_dir_path2:[all_MDLog1[3],all_MDLog1[4]]}
    root_dirs_dict=classify_same_root(root_dirs_path,all_MDLog1) 
        
    # 处理log
    for root_dir_path in root_dirs_path:
        starttime=datetime.datetime.now()
        parsing_log(root_dir_path,root_dirs_dict)
        endtime=datetime.datetime.now()
        
        print "Executing time: " + str((endtime-starttime).seconds) + "s"
        
#=========================== END MAIN ==========================  