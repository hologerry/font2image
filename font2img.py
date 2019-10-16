import argparse
import glob
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# reload(sys)
# sys.setdefaultencoding("utf-8")

EN_CHARSET = None
CN_CHARSET = None
CN_T_CHARSET = None
JP_CHARSET = None
KR_CHARSET = None

DEFAULT_CHARSET = "./charset/en.json"


def load_global_charset():
    global CN_CHARSET, JP_CHARSET, KR_CHARSET, CN_T_CHARSET
    cjk = json.load(open(DEFAULT_CHARSET))
    CN_CHARSET = cjk["gbk"]
    JP_CHARSET = cjk["jp"]
    KR_CHARSET = cjk["kr"]
    CN_T_CHARSET = cjk["gb2312_t"]


def load_global_charset_en():
    global EN_CHARSET
    en_json = json.load(open(DEFAULT_CHARSET))
    EN_CHARSET = en_json["en"]


def draw_single_char(ch, font, canvas_size, x_offset, y_offset):
    img = Image.new("RGB", (canvas_size + 300, canvas_size + 300), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    # draw.text((x_offset, y_offset), ch, (0, 0, 0), font=font)
    # print(img.size)
    text_width, text_height = draw.textsize(ch, font)
    position = (
        (canvas_size + 300 - text_width) / 2,
        (canvas_size + 300 - text_height) / 2,
    )
    draw.text(position, ch, (0, 0, 0), font=font)
    return img


def draw_example(ch, src_font, canvas_size, x_offset, y_offset):
    src_img = draw_single_char(ch, src_font, canvas_size, x_offset, y_offset)
    example_img = Image.new(
        "RGB", (canvas_size + 300, canvas_size + 300), (255, 255, 255)
    )
    example_img.paste(src_img, (0, 0))

    return example_img


def postprocess_crop(img):
    img_np = np.array(img)
    mask = np.argwhere(img_np[:, :, 0] != 255)
    xmin = np.min(mask[:, 0])
    xmax = np.max(mask[:, 0])
    ymin = np.min(mask[:, 1])
    ymax = np.max(mask[:, 1])
    im = img.crop([ymin, xmin, ymax, xmax])
    return im


def postprocess_scale(src, charset, indir, sample_dir, label=0, filter_by_hash=False, img_out_size=64):
    maxwidth = 0
    maxheight = 0
    count = 0
    for c in charset:
        im = Image.open(os.path.join(indir, "%02d.png" % (count)))
        width, height = im.size
        if width > maxwidth:
            maxwidth = width
        if height > maxheight:
            maxheight = height
        count += 1
    mlen = max(maxwidth, maxheight)

    count = 0
    for c in charset:
        im_out = Image.new("RGB", (mlen, mlen), "white")
        im = Image.open(os.path.join(indir, "%02d.png" % (count)))
        width, height = im.size
        startw = int((mlen - width) / 2)
        starth = int((mlen - height) / 2)
        # midw = width / 2
        # midh = height / 2
        im_out.paste(im, (startw, starth, startw + width, starth + height))
        im_out = im_out.resize((img_out_size, img_out_size), Image.ANTIALIAS)
        if count < 26:
            out = chr(count+ord('A'))
        else:
            out = chr(count-26+ord('a'))
        im_out.save(os.path.join(sample_dir, "{}.png".format(out)))
        count += 1


def postprocess(src, charset, indir, sample_dir, label=0, filter_by_hash=False, img_out_size=64):
    count = 0
    for c in charset:
        im = Image.open(os.path.join(indir, "%02d.png" % (count)))
        width, height = im.size
        mlen = max(width, height) + 6
        im_out = Image.new("RGB", (mlen, mlen), "white")
        startw = int((mlen - width) / 2)
        starth = int((mlen - height) / 2)
        # midw = width / 2
        # midh = height / 2
        im_out.paste(im, (startw, starth, startw + width, starth + height))
        im_out = im_out.resize((img_out_size, img_out_size), Image.ANTIALIAS)
        if count < 26:
            out = chr(count+ord('A'))
        else:
            out = chr(count-26+ord('a'))
        im_out.save(os.path.join(sample_dir, "{}.png".format(str(out))))
        count += 1


def font2img(src, charset, char_size, canvas_size, x_offset, y_offset,
             sample_count, sample_dir, label=0, filter_by_hash=False):
    src_font = ImageFont.truetype(src, size=char_size)

    count = 0

    for c in charset:
        if count == sample_count:
            break
        e = draw_example(c, src_font, canvas_size, x_offset, y_offset)
        e = postprocess_crop(e)
        if e:
            e.save(os.path.join(sample_dir, "%02d.png" % (count)))
            count += 1
            if count % 100 == 0:
                print("processed %d chars" % count)


load_global_charset_en()

parser = argparse.ArgumentParser(description="Convert font to images")
parser.add_argument("--fonts_root", type=str, help="path to font ttfs")
parser.add_argument("--src_font", required=False, help="path of the source font")
parser.add_argument("--charset", type=str, default="EN", help="charset, can be either: CN, JP, KR or a one line file")
parser.add_argument("--shuffle", type=int, default=0, help="shuffle a charset before processings")
parser.add_argument("--char_size", type=int, default=230, help="character size")
parser.add_argument("--canvas_size", type=int, default=256, help="canvas size")
parser.add_argument("--x_offset", type=int, default=0, help="x offset")
parser.add_argument("--y_offset", type=int, default=0, help="y_offset")
parser.add_argument("--sample_count", type=int, default=1000, help="number of characters to draw")
parser.add_argument("--sample_dir", default="images", help="directory to save examples")
parser.add_argument("--label", type=int, default=0, help="label as the prefix of examples")

args = parser.parse_args()


if __name__ == "__main__":
    if args.charset in ["EN", "CN", "JP", "KR", "CN_T"]:
        charset = locals().get("%s_CHARSET" % args.charset)
    else:
        charset = [c for c in open(args.charset).readline()[:-1].decode("utf-8")]
    if args.shuffle:
        np.random.shuffle(charset)
    fonts_glob = os.path.join("*.ttf")  # change this to your font file type
    fonts = glob.glob(fonts_glob)
    print(fonts_glob)
    for idx, font in enumerate(fonts):
        if (idx + 1) % 100 == 0:
            print(idx + 1)
        font_name = font.split("/")[-1].split(".")[0]
        out_dir = os.path.join(args.sample_dir, font_name)

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        font2img(font, charset, args.char_size, args.canvas_size, args.x_offset, args.y_offset,
                 args.sample_count, out_dir, args.label)

        out_dir_pad = os.path.join(args.sample_dir+"_post", font_name)
        if not os.path.exists(out_dir_pad):
            os.makedirs(out_dir_pad)
        postprocess(font, charset, out_dir, out_dir_pad, args.label)
