#-*- coding: utf8 -*-

from struct import *

'''
加密数据的长度用4字节表示 单位为字符数
在进行huffman编码时 碰巧产生了一个0xFF 就用0xFF0x00代替 在解码时 将0xFF0x00替换为0xFF
在huffman编码区域结束时 碰到几个bit没有用的时候 用1填充
'''

filename = './'+input('input filename:')+'.jpg'

FFD8 = b'\xff\xd8'
FFD9 = b'\xff\xd9'
FFC0 = b'\xff\xc0'
FFC1 = b'\xff\xc1'
FFC4 = b'\xff\xc4'
FFDA = b'\xff\xda'
FFDB = b'\xff\xdb'
FFDD = b'\xff\xdd'
FFE0 = b'\xff\xe0'
FFFE = b'\xff\xfe'
FFFF = b'\xff\xff'
structs = [FFC0,FFC1,FFC4,FFDA,FFDB,FFDD,FFE0,FFFE]

FFE1 = b'\xff\xe1'

HTs_num = [] # 不同位数的码字的数量
HTs = [] # DC直流0号表,AC交流0号表,DC直流1号表,AC交流1号表
DC0 = {}
DC1 = {}
AC0 = {}
AC1 = {}

compress_data = b''
compress_data_decode = b'' #在进行哈夫曼解码时 将compress_data中ff00转换为ff之后的bytes字符串
compress_data_decode_bin_str = '' #compress_data_decode的二进制字符串版本
compress_data_start_index = 0

width = 0
height = 0
Y_sampling = 0
C_sampling = 0
MCU_height_num = 0
MCU_width_num = 0
MCU_num = MCU_height_num * MCU_width_num

scan_index = 0 # 扫描了几个8乘8的块
'''
mod==6 --> Y1 Y2 Y3 Y4 Cr Cb
mod==3 --> Y Cr Cb
'''
mod = 0

# item format -- tuple:[offset,length,value] example:(23,3,'011')
Y_sectors = []
Cr_sectors = []
Cb_sectors = []

compress_data_decode_bin_str_inner_index = 0 #对compress_data_decode_bin_str_inner的搜索到了哪个位置

left = '' # 扫描compress_data_bin_str时剩下的无法识别的字符串
left_num = -1 # scan_index%mod

def analyseJpg():
    global filename,FFD8,FFD9,FFD8,FFD9,FFC0,FFC1,FFC4,FFDA,FFDB,FFDD,FFE0,FFFE,FFFF,FFE1,structs,compress_data,compress_data_start_index,DC0,AC0,DC1,AC1
    with open(filename,'rb+') as f:
        #print(f.read(1)) --- read(1)读一个字节
        if f.read(2) != FFD8:
            print('not jpeg file format')
            return()
        f.seek(-2,2)
        if f.read(2) != FFD9:
            print('not jpeg file format')
            return()
        f.seek(2,0)
        next_struct = f.read(2)
        while(next_struct != FFD9):
            if next_struct == FFE1: # exif
                print('next segment type : '+str(next_struct))
                length = f.read(2)
                length = length[0]*256+length[1]
                nomeaning = f.read(length-2)
                next_struct = f.read(2)
            elif next_struct == FFFF: #  无意义
                print('next segment type : '+str(next_struct))
                f.seek(-1,1)
                next_struct = f.read(2)
            elif next_struct in structs:
                print('next segment type : '+str(next_struct))
                if next_struct == FFC0:
                    analyseFFC0(f)
                elif next_struct == FFC1:
                    analyseFFC1(f)
                elif next_struct == FFC4:
                    analyseFFC4(f)
                elif next_struct == FFDA:
                    analyseFFDA(f)
                elif next_struct == FFDB:
                    analyseFFDB(f)
                elif next_struct == FFDD:
                    analyseFFDD(f)
                elif next_struct == FFE0:
                    analyseFFE0(f)
                else:
                    analyseFFFE(f)
                #处理这个段的信息结束
                next_struct = f.read(2)
            else:
                print('start compress data')
                f.seek(-2,1)
                compress_data_start_index = f.tell()
                compress_data = f.read()[:-2]
                break
        #开始恢复哈夫曼树
        DC0 = build_HT(0)
        AC0 = build_HT(1)
        DC1 = build_HT(2)
        AC1 = build_HT(3)



def analyseFFC0(f):
    global width,height,Y_sampling,C_sampling,MCU_num,MCU_height_num,MCU_width_num,mod
    length = f.read(2)
    length = length[0]*256+length[1]
    data = f.read(length-2)
    height = data[1]*256+data[2] #单位为像素
    width = data[3]*256+data[4]
    Y_sampling = int(bin(data[7])[-4:],2)
    C_sampling = int(bin(data[10])[-4:],2)
    max_sampling = max(Y_sampling,C_sampling)
    if max_sampling == 2:
        mod = 6
    if max_sampling == 1:
        mod = 3
    MCU_height = max_sampling*8
    MCU_width = max_sampling*8
    width_num = 0
    height_num = 0
    MCU_width_num = (width//MCU_width+1) if width%MCU_width != 0 else (width//MCU_width)
    MCU_height_num = (height//MCU_height+1) if height%MCU_height != 0 else (height//MCU_height)
    MCU_num = MCU_width_num*MCU_height_num


def analyseFFC1(f):
    length = f.read(2)
    length = length[0]*256+length[1]
    nomeaning = f.read(length-2)

def analyseFFC4(f):
    global HTs,HTs_num
    length = f.read(2)
    length = length[0]*256+length[1]
    waiting = f.read(length-2)
    HTs_num.append(waiting[1:17])
    HTs.append(waiting[17:])


def analyseFFDA(f):
    length = f.read(2)
    length = length[0]*256+length[1]
    waiting = f.read(length-2)
    

def analyseFFDB(f):
    length = f.read(2)
    length = length[0]*256+length[1]
    nomeaning = f.read(length-2)

def analyseFFDD(f):
    length = f.read(2)
    length = length[0]*256+length[1]
    nomeaning = f.read(length-2)

def analyseFFE0(f):
    length = f.read(2)
    length = length[0]*256+length[1]
    nomeaning = f.read(length-2)

def analyseFFFE(f):
    length = f.read(2)
    length = length[0]*256+length[1]
    nomeaning = f.read(length-2)

def build_HT(index):
    global HTs,HTs_num
    build = {}
    HT_num = HTs_num[index]
    HT = list(HTs[index])
    bits = 1
    l = [] #  用来顺序的记录码字的产生
    for key in HT_num:
        times = key
        if times != 0:
            num = times
            while(num!=0):
                if len(build) == 0:
                    l.append('0'*bits)
                    build[l[-1]] = HT.pop(0)
                else:
                    if times != 1 and num != times:
                        tem = int('0b'+l[-1],2)+1
                        add = '0'*(len(l[-1])-len(bin(tem)[2:]))+bin(tem)[2:]
                        l.append(add)
                        build[add] = HT.pop(0)
                    else:
                        tem = int('0b'+l[-1],2)+1
                        add = '0'*(len(l[-1])-len(bin(tem)[2:]))+bin(tem)[2:]
                        if len(add) < bits:
                            add = add + '0'*(bits-len(add))
                        l.append(add)
                        build[add] = HT.pop(0)
                num -= 1
        else:
            pass
        bits += 1
    return build

# 用来扫描8乘8的颜色分量
def scan_88_vector(data):
    global scan_index,mod,Y_sectors,Cr_sectors,Cb_sectors,DC0,DC1,AC0,AC1,compress_data_decode_bin_str_inner_index,left,left_num
    scan_index += 1
    sector = []
    is_DC = 1
    if scan_index%mod == mod-1:
        #print('now scan_index:',scan_index,' go into Cr')
        #Cr
        start = 0
        mid = 1
        end = len(data)
        item_num = 0
        while(mid<=end):
            key = data[start:mid]
            if is_DC:
                if key in DC1: 
                    length = DC1[key]
                    if length == 0:
                        value = '0'
                    else:
                        value = data[mid:mid+length]
                    offset = compress_data_decode_bin_str_inner_index + mid
                    item = [offset,length,value]
                    sector.append(item)
                    is_DC = 0
                    start = mid+length
                    mid = start + 1
                    item_num += 1
                else:
                    mid += 1
            else:
                if key in AC1:
                    if AC1[key] == 0:
                        Cr_sectors.append(sector)
                        compress_data_decode_bin_str_inner_index += mid
                        return data[mid:]
                    length = AC1[key] & (0b00001111)
                    zero_num = AC1[key]>>4 #有多少项为0
                    item_num += zero_num
                    if length == 0:
                        value = '0'
                    else:
                        value = data[mid:mid+length]
                    offset = compress_data_decode_bin_str_inner_index + mid
                    item = [offset,length,value]
                    sector.append(item)
                    start = mid+length
                    mid = start + 1
                    item_num += 1
                    if item_num == 64:
                        Cr_sectors.append(sector)
                        compress_data_decode_bin_str_inner_index += start
                        return data[start:]
                else:
                    mid += 1
        Cr_sectors.append(sector)
        left_num = scan_index%mod
        left = data[start:]
        return ''
    elif scan_index%mod == 0:
        #print('now scan_index:',scan_index,' go into Cb')
        #Cb
        start = 0
        mid = 1
        end = len(data)
        item_num = 0
        while(mid<=end):
            key = data[start:mid]
            if is_DC:
                if key in DC1:
                    length = DC1[key]
                    if length == 0:
                        value = '0'
                    else:
                        value = data[mid:mid+length]
                    offset = compress_data_decode_bin_str_inner_index + mid
                    item = [offset,length,value]
                    sector.append(item)
                    is_DC = 0
                    start = mid+length
                    mid = start + 1
                    item_num += 1
                else:
                    mid += 1
            else:
                if key in AC1:
                    if AC1[key] == 0:
                        Cb_sectors.append(sector)
                        compress_data_decode_bin_str_inner_index += mid
                        return data[mid:]
                    length = AC1[key] & (0b00001111)
                    zero_num = AC1[key]>>4 #有多少项为0
                    item_num += zero_num
                    if length == 0:
                        value = '0'
                    else:
                        value = data[mid:mid+length]
                    offset = compress_data_decode_bin_str_inner_index + mid
                    item = [offset,length,value]
                    sector.append(item)
                    start = mid+length
                    mid = start + 1
                    item_num += 1
                    if item_num == 64:
                        Cb_sectors.append(sector)
                        compress_data_decode_bin_str_inner_index += start
                        return data[start:]
                else:
                    mid += 1
        Cb_sectors.append(sector)
        left_num = scan_index%mod
        left = data[start:]
        return ''
    else:
        #print('now scan_index:',scan_index,' go into Y')
        #Y
        start = 0
        mid = 1
        end = len(data)
        item_num = 0
        while(mid<=end):
            key = data[start:mid]
            if is_DC:
                if key in DC0:
                    length = DC0[key]
                    if length == 0:
                        value = '0'
                    else:
                        value = data[mid:mid+length]
                    offset = compress_data_decode_bin_str_inner_index + mid
                    item = [offset,length,value]
                    sector.append(item)
                    is_DC = 0
                    start = mid+length
                    mid = start + 1
                    item_num += 1
                else:
                    mid += 1
            else:
                if key in AC0:
                    if AC0[key] == 0:
                        Y_sectors.append(sector)
                        compress_data_decode_bin_str_inner_index += mid
                        return data[mid:]
                    length = AC0[key] & (0b00001111)
                    zero_num = AC0[key] >> 4 #有多少项为0
                    item_num += zero_num
                    if length == 0:
                        value = '0'
                    else:
                        value = data[mid:mid+length]
                    offset = compress_data_decode_bin_str_inner_index + mid
                    item = [offset,length,value]
                    sector.append(item)
                    start = mid+length
                    mid = start + 1
                    item_num += 1
                    if item_num == 64:
                        Y_sectors.append(sector)
                        compress_data_decode_bin_str_inner_index += start
                        return data[start:]
                else:
                    mid += 1
        Y_sectors.append(sector)
        left_num = scan_index%mod
        left = data[start:]
        return ''

# 从compress data中恢复出在进行哈夫曼编码之前的所有的8乘8块
def recover_data():
    global compress_data,compress_data_decode_bin_str,compress_data_decode
    compress_data_decode = FF00_2_FF(compress_data)
    compress_data_decode_bin_str_inner = bytes2bin_str(compress_data_decode)
    compress_data_decode_bin_str = compress_data_decode_bin_str_inner
    # 开始从二进制流中识别出8乘8的块
    while(len(compress_data_decode_bin_str_inner)!=0):
        compress_data_decode_bin_str_inner = scan_88_vector(compress_data_decode_bin_str_inner)

#在进行huffman编码时 碰巧产生了一个0xFF 就用0xFF0x00代替 在解码时 将0xFF0x00替换为0xFF
def FF00_2_FF(bytes_str):
    bytes_str_after = b''
    jump_next = 0
    for i in bytes_str:
        if jump_next:
            jump_next = 0
            continue
        if i == b'\xff'[0]:
            jump_next = 1
        bytes_str_after += pack('>B',i)
    return bytes_str_after

#在进行huffman编码时 碰巧产生了一个0xFF 就用0xFF0x00代替 在解码时 将0xFF0x00替换为0xFF
def FF_2_FF00(bytes_str):
    bytes_str_after = b''
    add_00 = 0
    for i in bytes_str:
        if i == b'\xff'[0]:
            bytes_str_after += pack('>B',i)
            bytes_str_after += pack('>B',0)
        else:
            bytes_str_after += pack('>B',i)
    return bytes_str_after


#将bytes转换为二进制字符串 example:b'12' --> '0011000100110010'
def bytes2bin_str(bytes_str):
    bin_str = ''
    for i in bytes_str:
        tem = '0'*(8-len(bin(i)[2:]))+bin(i)[2:]
        bin_str += tem
    return bin_str

#将二进制字符串转换为bytes example: '0011000100110010' --> b'12'
def bin_str2bytes(bin_str):
    bytes_str = b''
    byte_num = len(bin_str)//8 #有多少个字节
    i = 0
    while(i!=byte_num):
        byte_int = int(bin_str[i*8:i*8+8],2) #字节的10进制表示
        bytes_str += pack('>B',byte_int)
        i += 1
    return bytes_str




def embed(Cr,data):
    global Cr_sectors,Cb_sectors
    if Cr == 1:
        sectors = Cr_sectors
    else:
        sectors = Cb_sectors
    length = len(data)
    index_out = 0
    index_in = 0
    index_bin_str = 0
    end = 0
    for i in sectors:
        if end:
            break
        for j in i:
            if end:
                break
            if j[1] != 0:
                j_l = list(j[2])
                j_l[-1] = data[index_bin_str]
                j[2] = ''.join(j_l)
                sectors[index_out][index_in][2] = j[2]
                index_bin_str += 1
                if index_bin_str >= length:
                    end = 1
            index_in += 1
        index_in = 0
        index_out += 1
    if Cr == 1:
        Cr_sectors = sectors
    else:
        Cb_sectors = sectors

# 用修改后的sectors修改compress_data_decode_bin_str
def sectors_To_compress_data_decode_bin_str():
    global compress_data_decode_bin_str,Y_sectors,Cr_sectors,Cb_sectors,mod
    compress_data_decode_bin_str_list = list(compress_data_decode_bin_str)
    index = 1
    while(1):
        if index%mod == 0:
            #Cb
            num = index//mod
            if num > len(Cb_sectors):
                break
            for i in Cb_sectors[num-1]:
                if i[1] == 0:
                    continue
                compress_data_decode_bin_str_list[i[0]:i[0]+i[1]] = i[2]       
        elif index%mod == mod-1:
            #Cr
            num = index//mod
            if num+1 > len(Cr_sectors):
                break
            for i in Cr_sectors[num]:
                if i[1] == 0:
                    continue
                compress_data_decode_bin_str_list[i[0]:i[0]+i[1]] = i[2]
        else:
            #Y
            num = index//mod
            if 4*num+index%mod > len(Y_sectors):
                break
            for i in Y_sectors[num]:
                if i[1] == 0:
                    continue
                compress_data_decode_bin_str_list[i[0]:i[0]+i[1]] = i[2]
        index += 1
    compress_data_decode_bin_str = ''.join(compress_data_decode_bin_str_list)



# 将修改后的sectors写入文件
def rewrite():
    global filename,compress_data_start_index,compress_data,compress_data_decode
    with open(filename,'rb+') as f:
        f.seek(compress_data_start_index,0)
        compress_data = FF_2_FF00(compress_data_decode)
        f.write(compress_data)



# 进行秘密数据嵌入
def encrypt(Cr):
    global compress_data_decode,compress_data_decode_bin_str
    secret = input('input info:')
    secret = secret.encode()
    length = len(secret)
    length = pack('>L',length)
    secret = length + secret
    secret_bin_str = bytes2bin_str(secret)
    print('secret_bin_str:\n',secret_bin_str)
    embed(Cr,secret_bin_str)
    sectors_To_compress_data_decode_bin_str()
    compress_data_decode = bin_str2bytes(compress_data_decode_bin_str)
    #print(len(compress_data2))
    rewrite()

# 进行秘密数据提取
def decrypt(Cr):
    extract(Cr)


def extract(Cr):
    global Cr_sectors,Cb_sectors
    if Cr == 1:
        sectors = Cr_sectors
    else:
        sectors = Cb_sectors
    secret_length_bin_str = '' #信息的长度的二进制字符串表示
    secret_bin_str = '' #信息的二进制字符串表示
    length_bits = 32 #secret_length_bin_str的长度
    for i in sectors:
        if length_bits == 0:
            break
        for j in i:
            if length_bits == 0:
                break
            if j[1] == 0:
                continue
            secret_length_bin_str += j[2][-1]
            length_bits -= 1
    #print('secret_length_bin_str:\n',secret_length_bin_str)
    length = int(secret_length_bin_str,2)*8 #secret_bin_str的长度
    length_bits = 32 #重定义
    pre = 0
    for i in sectors:
        if length == 0:
            break
        for j in i:
            if length == 0:
                break
            if j[1] == 0:
                continue
            if pre == length_bits:
                secret_bin_str += j[2][-1]
                length -= 1
            else:
                pre += 1
    #print('secret_bin_str:\n',secret_bin_str)
    print('the decrypt result:\n',bin_str2bytes(secret_bin_str).decode())

    
    

def in_out(e,Cr):
    if e:
        encrypt(Cr)
    else:
        decrypt(Cr)
    

def main():
    global compress_data,HTs,HTs_num,Y_sampling,C_sampling,DC0,AC0,DC1,AC1,MCU_num,MCU_height_num,MCU_width_num,left,left_num,mod
    analyseJpg()
    recover_data()
    print('left:',left)
    print('left_num:',left_num)
    Cr = int(input('use Cr(input 1) or Cb(input 0):'))
    e = int(input('encrypt(input 1) or decrypt(input 0):'))
    in_out(e,Cr)
    


if __name__ == "__main__":
    main()