import os
import os.path as osp
import numpy as np
import subprocess

'''
    ExifTool Version Number         : 13.44
    File Name                       : IMG20241014172620_AIXDR.jpg
    Directory                       : /Users/yangchangjie/Public/样张/xdr/AIXDR_out
    File Size                       : 5.8 MB
    File Modification Date/Time     : 2025:07:09 15:27:37+08:00
    File Access Date/Time           : 2025:12:23 10:45:55+08:00
    File Inode Change Date/Time     : 2025:07:09 15:27:37+08:00
    File Permissions                : -rw-r--r--
    File Type                       : JPEG
    File Type Extension             : jpg
    MIME Type                       : image/jpeg
    JFIF Version                    : 1.01
    Resolution Unit                 : None
    X Resolution                    : 1
    Y Resolution                    : 1
    Exif Byte Order                 : Big-endian (Motorola, MM)
    Exif Version                    : 0232
    MPF Version                     : 0100
    Number Of Images                : 2
    MP Image Flags                  : (none)
    MP Image Format                 : JPEG
    MP Image Type                   : Undefined
    MP Image Length                 : 1472237
    MP Image Start                  : 4324619
    Dependent Image 1 Entry Number  : 0
    Dependent Image 2 Entry Number  : 0
    XMP Toolkit                     : Adobe XMP Core 5.1.2
    Version                         : 1.0
    Directory Item Semantic         : Primary, GainMap
    Directory Item Mime             : image/jpeg, image/jpeg
    Directory Item Length           : 1472237
    Profile CMM Type                : 
    Profile Version                 : 4.3.0
    Profile Class                   : Display Device Profile
    Color Space Data                : RGB
    Profile Connection Space        : XYZ
    Profile Date Time               : 2016:01:01 00:00:00
    Profile File Signature          : acsp
    Primary Platform                : Unknown ()
    CMM Flags                       : Not Embedded, Independent
    Device Manufacturer             : 
    Device Model                    : 
    Device Attributes               : Reflective, Glossy, Positive, Color
    Rendering Intent                : Media-Relative Colorimetric
    Connection Space Illuminant     : 0.9642 1 0.82491
    Profile Creator                 : 
    Profile ID                      : 0
    Profile Description             : Google/Skia/B48B4CA139CEDE8AB2E3EA83BB923512
    Red Matrix Column               : 0.51512 0.2412 -0.00105
    Green Matrix Column             : 0.29198 0.69225 0.04189
    Blue Matrix Column              : 0.1571 0.06657 0.78407
    Media White Point               : 0.9642 1 0.82491
    Red Tone Reproduction Curve     : (Binary data 40 bytes, use -b option to extract)
    Green Tone Reproduction Curve   : (Binary data 40 bytes, use -b option to extract)
    Blue Tone Reproduction Curve    : (Binary data 40 bytes, use -b option to extract)
    Profile Copyright               : Google Inc. 2016
    Uniform Resource Name           : urn:iso:std:iso:ts:21496:-1
    Image Width                     : 3072
    Image Height                    : 4536
    Encoding Process                : Baseline DCT, Huffman coding
    Bits Per Sample                 : 8
    Color Components                : 3
    Y Cb Cr Sub Sampling            : YCbCr4:2:0 (2 2)
    Gain Map Image                  : (Binary data 1472237 bytes, use -b option to extract)
    Image Size                      : 3072x4536
    Megapixels                      : 13.9
    MP Image 2                      : (Binary data 1472237 bytes, use -b option to extract)
'''

def read_gainmap_max_from_bytes(gm_bin: bytes) -> float:
    proc = subprocess.run(
        ["exiftool", "-GainMapMax", "-"],
        input=gm_bin,  # bytes
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False  # 关键点：告诉 subprocess 这是 bytes
    )
    stdout = proc.stdout.decode("utf-8", errors="ignore")

    for line in stdout.splitlines():
        if "Gain Map Max" in line and ":" in line:
            value_str = line.split(":", 1)[1].strip()

            values = [float(v.strip()) for v in value_str.split(",")]
            print("values length: ", len(values))

            if len(values) == 1:
                values = values * 3  # 灰度 gainmap → RGB
            elif len(values) != 3:
                raise ValueError(f"Unexpected Gain Map Max format: {values}")

            return np.array(values, dtype=np.float32)
    raise RuntimeError("Gain Map Max not found")

def extract_gainmap_single(image_path):
    """
    从 UltraHDR / GainMap JPEG 中提取：
      1. SDR base image      -> *_sdr.jpg
      2. Gain Map image     -> *_gm.jpg
      3. qmax metadata      -> *_qmax_xxx.npy
    """

    # ---------- 1. 读取 EXIF / MPF ----------
    hdr_exif = os.popen(f"exiftool {image_path}")
    exif_text = hdr_exif.read()
    hdr_exif.close()
    print(exif_text)

    start_pos = None
    gm_len = None
    qmax = None

    for line in exif_text.splitlines():
        if "MP Image Start" in line:
            start_pos = int(line[34:])
        elif "MP Image Length" in line:
            gm_len = int(line[34:])
        # elif "Gain Map Max" in line:
        #     qmax = np.array(float(line[34:])).astype("float32")

    if start_pos is None or gm_len is None :
        raise RuntimeError("Failed to parse MP Image Start / Length ")


    # ---------- 2. 二进制切割 ----------
    with open(image_path, "rb") as f:
        sdr_bin = f.read(start_pos)      # [0, start_pos)
        gm_bin = f.read(gm_len)          # [start_pos, start_pos + gm_len)

    # ---------- 3. 输出文件路径 ----------
    base, ext = osp.splitext(image_path)
    output_sdr = base + "_sdr.jpg"
    output_gm = base + "_gm.jpg"

    with open(output_sdr, "wb") as f:
        f.write(sdr_bin)

    with open(output_gm, "wb") as f:
        f.write(gm_bin)
    qmax_rgb = read_gainmap_max_from_bytes(gm_bin)

    #qmax = np.array(qmax, dtype=np.float32)
    #qmax_str = f"{qmax:.3f}".replace(".", "p")
    print(
        f"[GainMap] image={image_path}, "
        f"gm_start={start_pos}, gm_length={gm_len}, "
        f"Qmax={qmax_rgb}"
    )
    return output_sdr, output_gm, qmax

def batch_extract_gainmap(
    input_dir,
    out_sdr_dir,
    out_gm_dir,

    exts=(".jpg", ".jpeg", ".JPG")
):
    """
    批量处理 UltraHDR / GainMap JPEG

    input_dir    : 输入 HDR 图像目录
    out_sdr_dir  : 输出 SDR 目录
    out_gm_dir   : 输出 GainMap 目录

    """

    os.makedirs(out_sdr_dir, exist_ok=True)
    os.makedirs(out_gm_dir, exist_ok=True)


    image_list = [
        f for f in os.listdir(input_dir)
        if f.endswith(exts)
    ]

    print(f"[Batch] Found {len(image_list)} images in {input_dir}")

    for idx, name in enumerate(sorted(image_list)):
        image_path = osp.join(input_dir, name)
        print(f"\n[{idx+1}/{len(image_list)}] Processing {name}")

        try:
            sdr_path, gm_path, qmax = extract_gainmap_single(image_path)

            # ---- 移动到指定目录 ----
            os.replace(sdr_path, osp.join(out_sdr_dir, osp.basename(sdr_path)))
            os.replace(gm_path, osp.join(out_gm_dir, osp.basename(gm_path)))

        except Exception as e:
            print(f"[ERROR] {name}: {e}")

if __name__ == "__main__":
    extract_gainmap_single("/Public/样张/xdr/AIXDR_out/IMG20241014172620_AIXDR.jpg")
    # batch_extract_gainmap(
    #     "/Public/样张/xdr/LRXDR800",
    #     "/Public/样张/xdr/LRXDR800_sdr",
    #     "//Public/样张/xdr/LRXDR800_gm"
    #
    # )


