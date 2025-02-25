import re
import xml.etree.ElementTree as ET

# =========================================
# 1. 定数や正規表現のパターンはまとめて定義
# =========================================

PATTERNS = {
    "結合": r"[2-9][ァ-ヺヽ-ヿぁ-ゟ/]+",
    "返り点": r"\[[^\]]*\]",         # 角括弧 [] 内の文字列
    "ひだり": r"{[^\}]*}",           # 波括弧 {} 内の文字列
    "漢字":   r"[「『〔]?[一-龯〇　■-◿][\U000E0101-\U000E01EF]?",      # 漢字一文字（全角空白含む）異体字セレクタ
    "みぎ":   r"[ァ-ヺヽ-ヿぁ-ゟ\U0001B000-\U0001B0FF\U0001B100-\U0001B122/]+", # カタカナやひらがな
    "句読点": r"[、。，．・」』〕]",      # 句読点や括弧類
    "竪点": r"-",
    "改行": r"\n{2,}",
    "踊り文字": r'〻',
    "異体字": r"[0-9]*vs"
}

COMBINED_PATTERN = f"({'|'.join(PATTERNS.values())})"

ALL_RETSU = 7

def variation_selectors(vs_num):

    # vs = 2
    vs_start = 0xFE00
    vss_start = 0xE0100
    VSS = 17
    if vs_num >= VSS:
        character = chr(vss_start + vs_num - VSS)  # 整数を文字に変換
    else:
        character = chr(vs_start + vs_num - 1)  # 整数を文字に変換
    # character = chr(start + vs - VSS)  # 整数を文字に変換
    # print(f"Character: 花{character}, Code Point: U+{ord(character):X}")
    return character

# =========================================
# 2. 分割関数
# =========================================

def split_hiragana_katakana(text):
    """
    ひらがなとカタカナ（含スラッシュ）を分割する関数なのじゃ。
    """
    pattern = r"([ぁ-ゖゝ-ゟ\u3099-\u309C\U0001B001-\U0001B0FF\U0001B100-\U0001B11F/]*)([ァ-ヺヽ-ヿ\u3099-\u309C\U0001B000\U0001B120-\U0001B122/]*)"
    match = re.fullmatch(pattern, text)
    if match:
        return match.groups()
    return ("", "")

# =========================================
# 3. XML要素作成のヘルパー関数
# =========================================

def add_xml_element(parent, tag_name, text):
    """
    親要素 (parent) に tag_name という子要素を作成し、
    そのテキスト値を text に設定するヘルパー関数なのじゃ。
    """
    element = ET.SubElement(parent, tag_name)
    element.text = text
    return element

# =========================================
# 4. マッチした文字列をXML要素に変換する関数
# =========================================

def process_match(match, block):
    """
    正規表現で抽出した文字列 (match) を、
    対応するXMLタグに変換して block に追加するのじゃ。
    """
    # 漢字
    if re.match(PATTERNS['漢字'], match):
        if match[0] in '「『〔':
            add_xml_element(block, "kaikakko", match[0])    
        add_xml_element(block, "oyaji", re.sub(r"[「『〔]", "", match))

    # ひだり: { ほにゃらら }
    elif re.match(PATTERNS['ひだり'], match):
        (furi, okuri) = split_hiragana_katakana(re.sub(r"[{}]", "", match))
        if furi:
            add_xml_element(block, "saifuri", furi)
        if okuri:
            add_xml_element(block, "saiokuri", okuri)

    # みぎ: カナ・ひらがな
    elif re.match(PATTERNS['みぎ'], match):
        (furi, okuri) = split_hiragana_katakana(match)
        if furi:
            add_xml_element(block, "furi", furi)
        if okuri:
            add_xml_element(block, "okuri", okuri)

    # 返り点: 角括弧
    elif re.match(PATTERNS['返り点'], match):
        add_xml_element(block, "kaeri", re.sub(r"[\[\]]", "", match))

    # 句読点
    elif re.match(PATTERNS['句読点'], match):
        for kuto in match:
            if re.match(r'[」』〕]', kuto):
                add_xml_element(block, "heikakko", kuto)
            elif re.match(r'[、。，．・…]', kuto):
                add_xml_element(block, "kuto", kuto)

    elif re.match(PATTERNS['竪点'], match):
        add_xml_element(block, "tate", '')

    elif re.match(PATTERNS['結合'], match):
        # add_xml_element(block, "ketugo", match)
        child = ET.SubElement(block, "ketsugo", attrib={"length": match[0]})
        child.text = match[1:]
        
    elif re.match(PATTERNS['踊り文字'], match):
        add_xml_element(block, "odori", '')
    
    elif re.match(PATTERNS['異体字'], match):
        # child = ET.SubElement(block, "ketsugo", attrib={"length": match[0]})
        
        # child.text = match[1:]
        block.find("oyaji").text += variation_selectors(int(re.sub(r'vs', '', match)))


# =========================================
# 5. テキストを読み込み、XMLツリーを生成する関数
# =========================================

def generate_xml_from_text(hanbun_text):
    """
    テキスト (hanbun_text) からXMLツリーを生成して返す関数じゃ。
    """
    root = ET.Element("kanbun")
    matches = re.findall(COMBINED_PATTERN, hanbun_text)

    # ブロック要素を管理
    block = None

    # retsu = ALL_RETSU 

    for match in matches:
        
        if re.match(PATTERNS['改行'], match):
            block = ET.SubElement(root, "block")
            ET.SubElement(block, 'nl')
            # process_match('\n', block)
            # print(f'retsu: {retsu}')
            # for i in range( retsu ):
            #     block = ET.SubElement(root, "block")
            #     process_match('　', block)
            # retsu = ALL_RETSU 

        # 新たな漢字ブロックが始まったら <block> を新規作成
        if re.match(PATTERNS['漢字'], match):
            # retsu = (retsu-1) % ALL_RETSU
            block = ET.SubElement(root, "block")

        # ブロックが未作成の場合は作っておく (句読点のみ等のパターンに対応)
        if block is None:
            block = ET.SubElement(root, "block")

        # マッチ内容を処理してブロック要素に追加
        process_match(match, block)
        

    return root

# =========================================
# 6. XMLを書き出す関数
# =========================================

def write_xml(root, output_filename):
    """
    XMLエレメントツリー (root) を output_filename に書き出す関数じゃ。
    """
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)  # Python 3.9以降で利用可
    with open(output_filename, "w", encoding="utf-8") as f:
        tree.write(f, encoding="unicode", xml_declaration=True)

# =========================================
# 7. メイン処理
# =========================================

def main():
    """
    めいめいのファイルを読み込み、XMLを生成し、書き出すメイン関数じゃ。
    """
    input_file = "input.txt"
    output_file = "input.txt.xml"

    # テキストファイルを読み込み
    with open(input_file, "r", encoding="utf-8") as f:
        hanbun_text = f.read()

    # XMLツリー生成
    root = generate_xml_from_text(hanbun_text)

    # ファイルに保存
    write_xml(root, output_file)

if __name__ == "__main__":
    main()
