import os
import argparse
from svgrasterize import *

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
