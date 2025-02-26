import xml.etree.ElementTree as ET
import re

#--- CONFIG ---#

input_file = 'input.txt.xml'
output_file = 'input.svg'
# font_family_oya = "Noto Serif JP SemiBold"
# font_family_ko = "BIZ UD明朝 Medium"

font_family_oya = "serif"
font_family_ko = "serif"

OYA = 0
KO = 1
font_flag = OYA
kaeriten_flag = False

all_retsu = 9
moji_pt = 24
kana_scale = 1/2

gyo_kan = 2.5
retsu_kan = 2  # Const

#--- CODE ---#

ZEN = 0
HAN = 1

def add_text(x, y, kaku, text, font_f, scale=1, option=""):
    if kaku == ZEN :
        size = moji_pt
    elif kaku == HAN :
        size = moji_pt*kana_scale
        # option += ' font-weight="bold" '
    if scale != 1:
        option += f' transform="scale(1, {scale})" '
        y = y/scale
    # option += ' font-weight="bold" '
    if font_f == OYA:
        option += f' font-family="{font_family_oya} '
    elif font_f == KO:
        option += f' font-family="{font_family_ko} '
    return f'<text x="{x}" y="{y}" font-size="{size}" writing-mode="vertical-rl" {option} ">{text}</text>'

# 置換用の辞書
replacement_dict = {
    # '-': '㆐',
    'レ':'㆑',
    '一':'㆒',
    '二':'㆓',
    '三':'㆔',
    '四':'㆕',
    '上':'㆖',
    '中':'㆗',
    '下':'㆘',
    '甲':'㆙',
    '乙':'㆚',
    '丙':'㆛',
    '丁':'㆜',
    '天':'㆝',
    '地':'㆞',
    '人':'㆟'
    # 必要に応じて他の文字を追加
}

# 辞書に基づいて文字列を置換する関数
def replace_characters(input_string):
    # 各文字を辞書で置換する
    replaced_string = "".join(replacement_dict.get(char, char) for char in input_string)
    return replaced_string


# XMLファイルを読み込む
tree = ET.parse(input_file)
root = tree.getroot()

moji_len = moji_pt * 2

output = ''

retsu = 0
gyo = 0

# 子要素を走査
for block in root.findall('block'):

    if block.find("nl") is not None:
        # print(retsu)
        if retsu != 0:
            gyo += 1
        retsu = 0
        continue
 
    x = - gyo * moji_len * gyo_kan / 2
    y = retsu * moji_len * retsu_kan / 2

    oyaji = block.find('oyaji').text
    output += add_text(x, y, ZEN, oyaji, OYA)
    # print(oyaji)

    # 返り点
    if block.find('kaeri') is not None:
        kaeri = block.find('kaeri').text
        if kaeriten_flag:
            kaeri = replace_characters(kaeri)
        if block.find("tate") is not None: # y+moji_len/4+moji_len*length*2/4, y+moji_len/2+moji_pt*kana_scale/4
            output += add_text(x-moji_len/8, y+moji_len*3/4-moji_pt*kana_scale/2, HAN, kaeri, KO)
        elif re.fullmatch(r"(一レ|㆒㆑)", kaeri):
            output += add_text(x-moji_len/8, y+moji_len/2+moji_pt*kana_scale/8, HAN, kaeri[0], KO, option='text-anchor="middle" ')
            output += add_text(x-moji_len/8, y+moji_len/2, HAN, kaeri[1])
        elif re.fullmatch(r".(レ|㆑)", kaeri):
            output += add_text(x-moji_len/8, y+moji_len/2,  HAN, kaeri, KO, scale=0.6, option=f'letter-spacing="-{moji_len/16}"')
        else:
            output += add_text(x-moji_len/8, y+moji_len/2, HAN, kaeri, KO)

    # 竪点
    if block.find("tate") is not None:
        if kaeriten_flag:
            output  += add_text(x, y+moji_len*3/4-moji_pt*kana_scale/2, HAN, '㆐', KO)
        else:
            output += add_text(x, y+moji_len*3/4-moji_pt*kana_scale/2, HAN, '─', KO)

    if block.find("odori") is not None:
            output += add_text(x+moji_len/8, y+moji_len/2, HAN, '〻', KO)

    # 右仮名
    if block.find('furi') is not None:
        furi = block.find('furi').text
    else:
        furi = ''
        
    if block.find('okuri') is not None:
        okuri = block.find('okuri').text
    else:
        okuri = ''

    # `/` で分割
    parts = (furi+okuri).split("/")

    if len(parts) == 2:
        # 2行の右ルビ
        if len(parts[0]) <= 3:
            scale = 1
        else:
            bottom = 3.5
            scale = bottom / len(parts[0]) 
        output += add_text(x+moji_len*5/8 -(0.5-kana_scale)*moji_pt*3/2 , y +(0.5-kana_scale)*moji_pt/2 , HAN, parts[0], KO, scale=scale)

        if len(parts[1]) <= 3:
            scale = 1
        else:
            bottom = 3.5
            scale = bottom / len(parts[1])
        top = 0.5
        output += add_text(x+moji_len*3/8 -(0.5-kana_scale)*moji_pt/2 , y+moji_len*top/4 +(0.5-kana_scale)*moji_pt/2 , HAN, parts[1], KO, scale=scale)

    elif len(parts) == 1:
        # 1行の右ルビ
        # 開始位置の分岐
        ruby_f = True
        if len(furi) == 0 and len(okuri) == 0:
            ruby_f = False
        elif len(furi) == 0 and len(okuri) == 1:
            top = 3
        elif len(furi) == 0 and len(okuri) == 2:
            top = 2
        elif len(furi) <= 1:
            top = 1
        else:
            top= 0

        # 圧縮の分岐
        if len(furi) == 0 and len(okuri) >= 4:
            bottom = 3.5
            scale = bottom / (len(furi)+len(okuri))
        elif len(furi) + len(okuri) >= 4:
            top = 0
            bottom = 4
            scale = bottom / (len(furi)+len(okuri))
        elif ruby_f:
            scale = 1

        if ruby_f:
            kana_y = y + moji_len*top/8 + (0.5-kana_scale) * moji_pt / 2 
            kana_x = x + moji_len*3/8 - (0.5-kana_scale) * moji_pt / 2
            output += add_text(kana_x, kana_y, HAN, furi+okuri, KO, scale=scale)


    # 句読点
    if block.find('kuto') is not None:
        output += add_text(x, y+moji_len/2, ZEN, block.find('kuto').text, KO)

    # 開き括弧
    if block.find('kaikakko') is not None:
        output += add_text(x, y-moji_len/2, ZEN, block.find('kaikakko').text, KO)

    # 閉じ括弧
    if block.find('heikakko') is not None:
        output += add_text(x, y + moji_len*3/4, ZEN, block.find('heikakko').text, KO)


    # 再読文字
    saifuri = ''
    saiokuri = ''

    # 左仮名
    if block.find('saifuri') is not None:
        saifuri = block.find('saifuri').text
        
    if block.find('saiokuri') is not None:
        saiokuri = block.find('saiokuri').text

    ruby_f = True
    if len(saifuri) == 0 and len(saiokuri) == 0:
        ruby_f = False
    elif len(saifuri) == 0 and len(saiokuri) == 1:
        top = 3
    elif len(saifuri) == 0 and len(saiokuri) == 2:
        top = 2
    elif len(saifuri) <= 1:
        top = 1
    else:
        top= 0

    # 圧縮の分岐
    if len(saifuri) == 0 and len(saiokuri) >= 4:
        bottom = 3.5
        scale = bottom / (len(saifuri)+len(saiokuri))
    elif len(saifuri) + len(saiokuri) >= 4:
        top = 0
        bottom = 4
        scale = bottom / (len(saifuri)+len(saiokuri))
    elif ruby_f:
        scale = 1

    if ruby_f:
        kana_y = y + moji_len*top/8 + (0.5-kana_scale) * moji_pt / 2
        kana_x = x - moji_len*3/8  + (0.5-kana_scale) * moji_pt / 2
        output += add_text(kana_x, kana_y, HAN, saifuri+saiokuri, KO, scale=scale)

    if block.find('ketsugo') is not None:
        length = int(block.find('ketsugo').attrib['length'])-1
        text = block.find('ketsugo').text
        output += add_text(x+moji_len*3/8 -(0.5-kana_scale)*moji_pt/2 , y+moji_len/4+moji_len*length*2/4, HAN, text, KO,option=f'text-anchor="middle"')


    # 文字の整数位置の更新
    gyo_f = (retsu + 1) // all_retsu
    retsu = (retsu + 1) % all_retsu
    gyo += gyo_f


height = (all_retsu-1)*moji_len*retsu_kan/2 + moji_len*5/4
if retsu != 0:
    gyo += 1
# print(gyo, retsu)
# output = f'<circle cx="{-(gyo-1)*moji_len*gyo_kan/2}" cy="{(all_retsu-1)*moji_len*retsu_kan/2}" r="3" stroke="black" stroke-width="1" fill="blue"></circle>' + output

width = (gyo-1)*moji_len*gyo_kan/2 + moji_len*5/4 
# output = f'<rect x="{-width + moji_len*3/4}" y="{-moji_len/4}" width="{width}" height="{height}" fill="white" stroke="black" />' + output
output = f'<rect x="{-width + moji_len*3/4}" y="{-moji_len/4}" width="{width}" height="{height}" fill="white" />' + output
output = f'<svg viewBox="{-width + moji_len*3/4} {-moji_len/4} {width} {height}" width="{width}pt" height="{height}pt" xmlns="http://www.w3.org/2000/svg">'  + output

with open(output_file, 'w', encoding="utf-8") as f:
    f.write(output + '</svg>')
