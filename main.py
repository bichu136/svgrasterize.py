import os
import argparse
from svgrasterize import *
import numpy as np
np.set_printoptions(formatter={'float': lambda x: "{0:0.3f}".format(x)})
parser = argparse.ArgumentParser()
parser.add_argument("svg", help="input SVG file")
parser.add_argument("output", help="output PNG file")
parser.add_argument("-bg", type=svg_color, help="set default background color")
parser.add_argument("-fg", type=svg_color, help="set default foreground color")
parser.add_argument("-w", "--width", type=int, help="output width")
parser.add_argument("-id", help="render single element with specified `id`")
parser.add_argument(
    "-t", "--transform", type=svg_transform, help="apply additional transformation"
)
parser.add_argument("--linear-rgb", action="store_true", help="use linear RGB for rendering")
parser.add_argument("--fonts", nargs="*", help="paths to SVG files containing all fonts")
opts = parser.parse_args()

if not os.path.exists(opts.svg):
    sys.stderr.write(f"[error] file does not exsits: {opts.svg}\n")
    sys.exit(1)

fonts = FontsDB()
for font in opts.fonts or [DEFAULT_FONTS]:
    fonts.register_file(font)

transform = Transform().matrix(0, 1, 0, 1, 0, 0)
if opts.transform:
    transform @= opts.transform

if opts.svg.endswith(".path"):
    path = Path.from_svg(open(opts.svg).read())
    print(path,"\n")
    opts.bg = svg_color("white") if opts.bg is None else opts.bg
    opts.fg = svg_color("black") if opts.fg is None else opts.fg
    scene = Scene.fill(path, opts.fg)

    ids, size = {}, None
else:
    scene, ids, size = svg_scene_from_filepath(
        opts.svg, fg=opts.fg, width=opts.width, fonts=fonts
    )
if scene is None:
    sys.stderr.write("[error] nothing to render\n")
else:
    pass
    if opts.id is not None:
        size = None
        scene = ids.get(opts.id)
        if scene is None:
            sys.stderr.write(f"[error] no object with id: {opts.id}\n")
            sys.exit(1)

    start = time.time()
    if size is not None:
        w, h = size
        result = scene.render(
            transform, viewport=[0, 0, int(h), int(w)], linear_rgb=opts.linear_rgb
        )
    else:
        result = scene.render(transform, linear_rgb=opts.linear_rgb)
    stop = time.time()
    sys.stderr.write("[info] rendered in {:.2f}\n".format(stop - start))
    sys.stderr.flush()
    if result is None:
        sys.stderr.write("[error] nothing to render\n")
        sys.exit(1)
    output, _convex_hull = result

    if size is not None:
        w, h = size
        output = output.convert(pre_alpha=True, linear_rgb=opts.linear_rgb)
        base = np.zeros((int(h), int(w), 4), dtype=FLOAT)
        image = canvas_merge_at(base, output.image, output.offset)
        output = Layer(image, (0, 0), pre_alpha=True, linear_rgb=opts.linear_rgb)

    if opts.bg is not None:
        output = output.background(opts.bg)

    filename = opts.output if opts.output != "-" else 1
    closefd = opts.output != "-"
    with open(filename, "wb", closefd=closefd) as file:
        output.write_png(file)



#path.fill trả về vùng ảnh, offset của ảnh lớn.
#hàm gộp là Layer.compose trả về vùng ảnh và offset, trả về ảnh lớn nhất.
# canvas_compose cho biết cách mà blend tam giác vào ảnh.

# blend của hàm canvas_merge_union là canvas_compose truyền vào tham số đầu tiên, Mặc định là COMPOSE_OVER
# Path.mask trả về mass của tam giác. bên trong tam giác là 1, ngoài tam giác là 0
# còn các cạnh của tam giác sẽ được là có giá trị trong khoảng từ 0 đến 1.
# còn trả về offset nữa.
