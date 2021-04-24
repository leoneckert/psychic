import argparse, sys, time, os, random, math
from pprint import pprint
from PIL import Image, ImageDraw, ImageFont
import textwrap
from bs4 import BeautifulSoup

#supported filetypes
filetypes = {
    "img": ["jpg", "png", "gif", "ico"],
    "text": ["html", "css", "txt"]
}

printformats = {
    "A3": [3508, 4961],
    "A2": [4961, 7016],
    "A1": [7016, 9933]
}

cwidth = cheight = 0

def main():
    global cwidth
    global cheight

    args = cleanDefaults(parser.parse_args())
    if not argsVerified(args):
        sys.exit()

    cwidth = args.canvassize[0]
    cheight = args.canvassize[1]

    filelist = getFilelist(args.source, args.filetypes, args.layerorder)

    canvas = getcanvas(args)

    # out = None
    # txt = Image.new('RGBA', (cwidth, cheight), (255,255,255,0))
    # draw = ImageDraw.Draw(txt)

    x = y = 0
    graphicx = graphicy = 0
    graphiccount = 0

    for file in filelist:

        if(file["type"] == "text"):
            if x > cwidth and args.textmode == "order":
                continue
            extension = file["path"].split(".")[-1]

            # if the non-html filter is requested:
            if extension != "html" and random.random() < (args.filternonhtml/100):
                continue

            # random textsize from the options:
            textsize = args.textsize[random.randint(0, len(args.textsize)-1)]
            # load font in that textsize
            font=ImageFont.truetype("SIMSUN.ttf", textsize)
            # random transparency fro the options:
            texttransparency = args.texttransparency[random.randint(0, len(args.texttransparency)-1)]

            with open(file["path"], "r") as f:

                try:
                    text = f.read()
                except:
                    print("[-] Skipping a text file. Probably because it contains characters I don't understand. (File: "+file["path"]+")")
                    # jump to next file!
                    continue
                # use BeautifulSoup to extract only the text of html.
                if args.htmlresolve == True and extension == "html":
                    text = resolveHTML(text)

                # cleaning all sorts of whitespaces:

                text = cleantext(text)

                # if the text is empty, let's jump to the next file!
                if(text == ""):
                    continue

                if args.textcrop != None:
                    text = croptext(args, text)

                lines = textwrap.wrap(text, width=args.textcolumnwidth, break_on_hyphens=False)

                txt = Image.new('RGBA', (cwidth, cheight), (255,255,255,0))
                draw = ImageDraw.Draw(txt)
                if args.textmode == "order":

                    for line in lines:
                        if extension == "html":
                            drawtext(draw, (x,y), line, args.htmlcolor, texttransparency, font)
                        else:
                            drawtext(draw, (x,y), line, args.textcolor, texttransparency, font)
                        y += font.getsize(line)[1]
                        if(y>cheight):
                            y = 0
                            x += (font.getsize("a"*args.textcolumnwidth)[0] + 5)
                elif args.textmode == "random" or args.textmode == "rotation":

                    paragraphHeight = len(lines)*font.getsize(lines[0])[1]
                    paragraphWidth = font.getsize("a"*args.textcolumnwidth)[0] + 5
                    x = initx = random.randint(0, cwidth) - paragraphWidth/2
                    y = inity = random.randint(0, cheight) - paragraphHeight/2
                    for line in lines:
                        if extension == "html":
                            drawtext(draw, (x,y), line, args.htmlcolor, texttransparency, font)
                        else:
                            drawtext(draw, (x,y), line, args.textcolor, texttransparency, font)
                        y += font.getsize(line)[1]
                    # rotate text in rotation mode:
                    if args.textmode == "rotation":
                        angle = random.randint(0, 360)
                        anchorx = initx + paragraphWidth/2
                        anchory = inity + paragraphHeight/2
                        txt = txt.rotate(angle, center=(anchorx, anchory))

                # combine the text layer with the canvas
                canvas = Image.alpha_composite(canvas, txt)


        elif(file["type"] == "img"):

            graphicbase = Image.new('RGBA', (cwidth, cheight), (255,255,255,0))
            graphictransparency = args.graphictransparency[random.randint(0, len(args.graphictransparency)-1)]
            graphic = Image.open(file["path"]).convert("RGBA")
            alpha = Image.new("L", graphic.size, graphictransparency)
            graphic.putalpha(alpha)
            graphicsize = args.graphicsize[random.randint(0, len(args.graphicsize)-1)]
            graphicwidth, graphicheight = graphic.size
            biggerside = max(graphicwidth, graphicheight)
            factor = graphicsize/biggerside
            graphic= graphic.resize((int(factor*graphicwidth), int(factor*graphicheight)), Image.ANTIALIAS)
            graphicwidth, graphicheight = graphic.size
            margin = int(args.graphiclayermargin)


            if args.graphicmode == "random" or args.graphicmode == "mirror":

                try:
                    graphicx = random.randint(margin, cwidth-margin) - int(graphicwidth/2)
                except:
                    print("graphic.size", graphic.size)
                    print(margin, cheight-margin)
                graphicy = random.randint(margin, cheight-margin) - int(graphicheight/2)
                if args.graphicmode == "mirror":
                    graphicbase2 = Image.new('RGBA', (cwidth, cheight), (255,255,255,0))
                    mirrorgraphicx = abs(cwidth-graphicx) - graphicwidth
                    mirrorgraphicy = graphicy
                    graphicbase2.paste(graphic, (mirrorgraphicx, mirrorgraphicy))
                    canvas = Image.alpha_composite(canvas, graphicbase2)

            elif args.graphicmode == "grid":

                availablewidth = cwidth - margin*2
                availableheight = cheight - margin*2
                marginleftright = margin + int(( availablewidth%args.cellsize )/2)
                margintopbottom = margin + int(( availableheight%args.cellsize )/2)
                numcols = math.floor(availablewidth/args.cellsize)
                numrows = math.floor(availableheight/args.cellsize)
                currentrow = math.floor(graphiccount/numcols)%numrows
                currentcol = graphiccount%numcols
                graphicx = int(marginleftright + (currentcol*args.cellsize) + (args.cellsize/2) - (graphicwidth/2))
                graphicy = int(margintopbottom + (currentrow*args.cellsize) + (args.cellsize/2) - (graphicheight/2))

            graphicbase.paste(graphic, (graphicx, graphicy))
            canvas = Image.alpha_composite(canvas, graphicbase)
            graphiccount+=1


    canvas = canvas.convert("RGB")
    canvas.save(args.outfile)


def drawtext(draw, position, line, color, texttransparency, font):
    draw.text(position, line, fill=(color[0],color[1], color[2], texttransparency), font=font)

def cleantext(text):
    text = text.replace("\n", " ")
    text = ' '.join(text.split())
    return text

def resolveHTML(text):
    soup = BeautifulSoup(text, "html.parser")
    text = soup.text.strip()
    return text

def croptext(args, text):
    mincrop = args.textcrop[0]
    maxcrop = args.textcrop[1]
    crop = random.randint(mincrop, maxcrop)
    if(len(text) > crop):
        cropstart = random.randint(0, len(text)-crop)
        text = text[cropstart:cropstart+crop]
    return text

def getcanvas(args):
    global cwidth
    global cheight

    if args.usecanvas != None:
        # if an existing image is specified as a canvas to draw upon
        canvas = Image.open(args.usecanvas)
        alpha = Image.new("L", canvas.size, 255)
        # add alpha channel
        canvas.putalpha(alpha)
    else:
        # else create a canvas with the right dimensions and background color
        background = (args.backgroundcolor[0], args.backgroundcolor[1], args.backgroundcolor[2], 255)
        dimensions = (cwidth, cheight)
        canvas = Image.new("RGBA", dimensions, color = background)
    return canvas

def getFilelist(source, target_extensions, order):
    filelist = list()
    for filename in os.listdir(source):
        ext = filename.split(".")[-1]
        if(ext in target_extensions):
            filelist.append({
                "type": extensionToType[ext],
                "path": os.path.join(source, filename)
            })
    if(order == "mixed"):
        random.shuffle(filelist)
    elif(order == "graphic-text"):
        filelist = sorted(filelist, key=lambda x: x["type"])
    elif(order == "text-graphic"):
        filelist = sorted(filelist, key=lambda x: x["type"], reverse=True)
    return filelist

def processFileTypes(filetypes):
    target_extensions = list()
    extension_to_type = dict()
    for key in filetypes.keys():
        for item in filetypes[key]:
            target_extensions.append(item)
            extension_to_type[item] = key
    return target_extensions, extension_to_type






acceptedFileTypes, extensionToType = processFileTypes(filetypes);
acceptedTextModes = ["order", "random", "rotation"]
acceptedGraphicModes = ["mirror", "random", "grid"]
acceptedLayerOrders = ["text-graphic", "graphic-text", "mixed"]

parser = argparse.ArgumentParser(description='Consultation with the WiFi Psychic.',
                                    epilog=' ',
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-i", "--input",
                    dest="source",
                    default=".",
                    help="Path to the source folder")
parser.add_argument("-f", "--file-types",
                    dest="filetypes",
                    default="all",
                    nargs='*',
                    choices=acceptedFileTypes+['all'],
                    help="List any of: "+", ".join(acceptedFileTypes))
parser.add_argument("-t", "--text-mode",
                    dest="textmode",
                    default="order",
                    choices=acceptedTextModes,
                    help="Choose from: "+", ".join(acceptedTextModes))
parser.add_argument("-ts", "--text-size",
                    dest="textsize",
                    default=20,
                    nargs='*',
                    type=int,
                    help="Single value or multiple (paragraphs pick randomly)")
parser.add_argument("-tc", "--text-color",
                    dest="textcolor",
                    default=0,
                    nargs='*',
                    type=int,
                    help="'255 0 0' results in red. '200' results in light grey")
parser.add_argument("-tw", "--text-column-width",
                    dest="textcolumnwidth",
                    default=40,
                    type=int)
parser.add_argument("-tt", "--text-transparency",
                    dest="texttransparency",
                    default=255,
                    nargs='*',
                    type=int,
                    help="'0' results in full transparency. '255' results in full opacity")
parser.add_argument("--text-crop",
                    dest="textcrop",
                    default=None,
                    nargs='*',
                    type=int,
                    help="min max")
parser.add_argument("-g", "--graphic-mode",
                    dest="graphicmode",
                    default="mirror",
                    choices=acceptedGraphicModes,
                    help="Choose from: "+", ".join(acceptedGraphicModes),
                    metavar="")
parser.add_argument("-gs", "--graphic-size",
                    dest="graphicsize",
                    default=400,
                    nargs='*',
                    type=int,
                    help="Single value or multiple (graphics pick randomly)",
                    metavar="")
parser.add_argument("-gt", "--graphic-transparency",
                    dest="graphictransparency",
                    default=255,
                    nargs='*',
                    type=int,
                    help="'0' results in full transparency. '255' results in full opacity",
                    metavar="")
parser.add_argument("--graphic-layer-margin",
                    dest="graphiclayermargin",
                    default=10,
                    type=int,
                    help="in percent of width. value must be between 0-50 ")
parser.add_argument("--cell-size",
                    dest="cellsize",
                    default=400,
                    type=int,
                    help="cell size for grid mode")
parser.add_argument("-bc", "--background-color",
                    dest="backgroundcolor",
                    default=255,
                    nargs='*',
                    type=int,
                    help="'255 0 0' results in red. '200' results in light grey")
parser.add_argument("-lo", "--layer-order",
                    dest="layerorder",
                    default='mixed',
                    choices=acceptedLayerOrders,
                    help="Choose from: "+", ".join(acceptedLayerOrders))
parser.add_argument("-o", "--outfile",
                    dest="outfile",
                    default='wifi-psychic[+timestamp].jpg',
                    help="Name of the output file")
parser.add_argument("-cs", "--canvas-size",
                    dest="canvassize",
                    default=["A2"],
                    nargs='*',
                    help="Width and Height of the canvas or A3, A2, A1",
                    metavar="")
parser.add_argument("--html-resolve",
                    dest="htmlresolve",
                    action='store_true',
                    default=False,
                    help="OPTIONAL. This option requires no value. Extract content text/remove markup from html files")
parser.add_argument("--html-color",
                    dest="htmlcolor",
                    default="Same as other text",
                    nargs='*',
                    help="Color html text differently. '255 0 0' results in red. '200' results in light grey",
                    metavar="")
parser.add_argument("--filter-non-html",
                    dest="filternonhtml",
                    default=0,
                    type=int,
                    help="Percentage of non html text to skip",
                    metavar="")
parser.add_argument("--use-canvas",
                    dest="usecanvas",
                    default=None,
                    help="Path to an existing canvas.",
                    metavar="")
parser.add_argument("-r", "--random",
                    dest="random",
                    action='store_true',
                    default=False,
                    help="")

def argsVerified(args):
    # verify args here. stop sys if necessary and give error message
    return True

def cleanDefaults(args):

    if(args.random == True):
        typesamplesize = random.randint(1, len(acceptedFileTypes))
        args.filetypes = random.sample(acceptedFileTypes, typesamplesize)
        args.textmode = random.choice(acceptedTextModes)
        args.textsize = []
        for i in range(random.randint(1, 2)):
            args.textsize.append(random.randint(7, 200))
        if random.random() < 0.5:
            args.textcolor = [random.randint(0,255)]
        else:
            args.textcolor = [random.randint(0,255), random.randint(0,255), random.randint(0,255)]
        args.textcolumnwidth = random.randint(10, 1000)
        args.texttransparency = []
        for i in range(random.randint(1, 3)):
            args.texttransparency.append(random.randint(7, 255))
        if random.random() < 0.5:
            args.textcrop = None
        else:
            if random.random() < 0.5:
                args.textcrop = [random.randint(700, 2000)]
            else:
                args.textcrop = [random.randint(700, 1000), random.randint(1001, 2000)]
        args.graphicsize = []
        for i in range(random.randint(1, 3)):
            args.graphicsize.append(random.randint(200, 1000))
        args.graphictransparency = []
        for i in range(random.randint(1, 3)):
            args.graphictransparency.append(random.randint(7, 255))
        args.graphiclayermargin = random.randint(0, 49)
        args.cellsize = random.randint(100, 500)
        if random.random() < 0.5:
            args.backgroundcolor = [random.randint(0,255)]
        else:
            args.backgroundcolor = [random.randint(0,255), random.randint(0,255), random.randint(0,255)]
        args.layerorder = random.choice(acceptedLayerOrders)
        args.htmlresolve = random.randint(0,1)
        if random.random() < 0.5:
            args.htmlcolor = args.textcolor
        else:
            if random.random() < 0.5:
                args.htmlcolor = [random.randint(0,255)]
            else:
                args.htmlcolor = [random.randint(0,255), random.randint(0,255), random.randint(0,255)]

    print(args)
    # sys.exit()

    if args.filetypes == "all":
        args.filetypes = acceptedFileTypes
    if isinstance(args.textcolor, int):
        args.textcolor = [args.textcolor, args.textcolor, args.textcolor]
    elif isinstance(args.textcolor, list) and len(args.textcolor) == 1:
        args.textcolor = [args.textcolor[0], args.textcolor[0], args.textcolor[0]]

    if args.htmlcolor == "Same as other text":
        args.htmlcolor = args.textcolor
    elif isinstance(args.htmlcolor, list) and len(args.htmlcolor) == 1:
        args.htmlcolor = [int(args.htmlcolor[0]), int(args.htmlcolor[0]), int(args.htmlcolor[0])]
    elif isinstance(args.htmlcolor, list) and len(args.htmlcolor) == 3:
        args.htmlcolor = [int(args.htmlcolor[0]), int(args.htmlcolor[1]), int(args.htmlcolor[2])]


    if isinstance(args.backgroundcolor, int):
        args.backgroundcolor = [args.backgroundcolor, args.backgroundcolor, args.backgroundcolor]
    elif isinstance(args.backgroundcolor, list) and len(args.backgroundcolor) == 1:
        args.backgroundcolor = [args.backgroundcolor[0], args.backgroundcolor[0], args.backgroundcolor[0]]

    if(len(args.canvassize) == 1):
        if(args.canvassize[0] == "A3" or args.canvassize[0] == "A2" or args.canvassize[0] == "A1"):
            args.canvassize = printformats[args.canvassize[0]]
        else:
            args.canvassize = [int(args.canvassize[0]), int(args.canvassize[0])]
    elif(len(args.canvassize) == 2):
        args.canvassize = [int(args.canvassize[0]), int(args.canvassize[1])]


    if args.usecanvas != None:
        canvas = Image.open(args.usecanvas)
        args.canvassize = [canvas.size[0], canvas.size[1]]

    origmargin = args.graphiclayermargin
    args.graphiclayermargin = (args.canvassize[0]/100) * args.graphiclayermargin

    if isinstance(args.textsize, int):
        args.textsize = [args.textsize]
    if isinstance(args.texttransparency, int):
        args.texttransparency = [args.texttransparency]

    if isinstance(args.graphicsize, int):
        args.graphicsize = [args.graphicsize]
    if isinstance(args.graphictransparency, int):
        args.graphictransparency = [args.graphictransparency]


    if isinstance(args.textcrop, int):
        args.textcrop = [args.textcrop, args.textcrop]
    elif isinstance(args.textcrop, list) and len(args.textcrop) == 1:
        args.textcrop = [args.textcrop[0], args.textcrop[0]]

    if args.outfile == "wifi-psychic[+timestamp].jpg":
        ts = str(time.time()).split(".")[0]
        args.outfile = "wifi-psychic-"+ts+".jpg"
        a = f"jkjkjkjk{args}"


    if args.textcrop != None:
        textcrop = "--text-crop "+" ".join(str(x) for x in args.textcrop)
    else:
        textcrop = ""
    if args.htmlresolve:
        htmlresolve = "--html-resolve"
    else:
        htmlresolve = ""

    randomstring = """
You have used the random (-r, --random) option!
Below you find the command that was generated for you. If you like what it produced, you can copy paste it and re-run it for similar results :)
    """
    command = f"""

Summary of your settings:

Short version:

python psychic.py -i {args.source} -f {" ".join(args.filetypes)} -t {args.textmode} -ts {" ".join(str(x) for x in args.textsize)} -tc {" ".join(str(x) for x in args.textcolor)} -tw {args.textcolumnwidth} -tt {" ".join(str(x) for x in args.texttransparency)} {textcrop} -g {args.graphicmode} -gs {" ".join(str(x) for x in args.graphicsize)} -gt {" ".join(str(x) for x in args.graphictransparency)} --graphic-layer-margin {origmargin} --cell-size {args.cellsize} -bc {" ".join(str(x) for x in args.backgroundcolor)} -lo {args.layerorder} -cs {" ".join(str(x) for x in args.canvassize)} {htmlresolve} --html-color {" ".join(str(x) for x in args.htmlcolor)}

Verbose version:

python psychic.py --input {args.source} \\
              --file-types {" ".join(args.filetypes)} \\
              --text-mode {args.textmode} \\
              --text-size {" ".join(str(x) for x in args.textsize)} \\
              --text-color {" ".join(str(x) for x in args.textcolor)} \\
              --text-column-width {args.textcolumnwidth} \\
              --text-transparency {" ".join(str(x) for x in args.texttransparency)} \\
              --graphic-mode {args.graphicmode} \\
              --graphic-size {" ".join(str(x) for x in args.graphicsize)} \\
              --graphic-transparency {" ".join(str(x) for x in args.graphictransparency)} \\
              --graphic-layer-margin {origmargin} \\
              --cell-size {args.cellsize} \\
              --background-color {" ".join(str(x) for x in args.backgroundcolor)} \\
              --layer-order {args.layerorder} \\
              --canvas-size {" ".join(str(x) for x in args.canvassize)} \\
              --html-color {" ".join(str(x) for x in args.htmlcolor)} \\
              {textcrop} \\
              {htmlresolve}
    """

    if(args.random):
        print(randomstring)
    print(command)

    # sys.exit()

    return args





if __name__ == "__main__":

    print("""

     _       ___ _______    ____                  __    _
    | |     / (_) ____(_)  / __ \_______  _______/ /_  (_)____
    | | /| / / / /_  / /  / /_/ / ___/ / / / ___/ __ \/ / ___/
    | |/ |/ / / __/ / /  / ____(__  ) /_/ / /__/ / / / / /__
    |__/|__/_/_/   /_/  /_/   /____/\__, /\___/_/ /_/_/\___/
                                   /____/
    """)


    main()
