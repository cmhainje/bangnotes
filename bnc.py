import argparse

from bangdef import Bang, read_bangs


class Block:
    def __init__(self, name="", bang=False, option=""):
        self.name = name
        self.option = option
        self.bang = bang
        self.content = []
        self.children = []


def is_empty_line(line):
    return line.strip() == ""

def is_single_line_block(line):
    valid_single_line_tags = ["#", "##", "###", "####", "#####", "######", "!title", "---"]
    return line.split()[0] in valid_single_line_tags

def make_new_single_line_block(line):
    if is_empty_line(line):
        raise Exception("Line is empty.")
    name = line.split()[0]
    if name[0] == "!":
        name = name[1:]
        return Block(name=name, bang=True)
    else:
        return Block(name=name, bang=False)

def make_new_multi_line_block(line):
    if is_empty_line(line):
        raise Exception("Line is empty.")
    if is_single_line_block(line):
        raise Exception("Line is single-line block.")

    new_block = Block(name="p")
    if line[:3] == "1. ":
        new_block.name = "ol"
    elif line[:2] == "- " or line[:2] == "* " or line[:2] == "+ ":
        new_block.name = "ul"
    elif line[:2] == "> ":
        new_block.name = "blockquote"
    # is it a bang opener?
    elif line[0] == "!":
        opt_open = line.find("{")
        if opt_open != -1:
            opt_close = line.find("}")
            if opt_close == -1:
                raise Exception(f"Invalid bang on line {i}: no closing curly brace.")
            if opt_close < opt_open:
                raise Exception(f"Invalid bang on line {i}: closing brace before opening brace.")
            bang = line[1:opt_open]
            option = line[opt_open+1:opt_close]
            new_block.name = bang
            new_block.option = option
            new_block.bang = True
        else:
            bang = line.strip()[1:]
            new_block.name = bang
            new_block.bang = True

    return new_block

def recurse(node, level=0, pre=None, post=None):
    if pre is not None: pre(node, level)
    for x in node.children:
        recurse(x, level=level+1, pre=pre, post=post)
    if post is not None: post(node, level)

def recursive_print(node):
    def print_node(node, level):
        if level == 0:
            return
        elif level == 1:
            print(f"{node.name}: {node.content}")
        else:
            to_print = "".join([" |" for i in range(level - 2)])
            print(f"{to_print} |-{node.name}: {node.content}")

    recurse(node, 0, pre=print_node)


parser = argparse.ArgumentParser()
parser.add_argument('--input')
parser.add_argument('--bangs', default="bangs.bdef")
parser.add_argument('--output')
opts = parser.parse_args()

BANGS = read_bangs(opts.bangs)

with open(opts.input, 'r') as f:
    lines = f.readlines()

# First, let's make a tree
root = Block()
block_stack = []
for i, line in enumerate(lines):
    if is_empty_line(line):
        # empty lines don't end bang blocks
        if len(block_stack) != 0 and not block_stack[-1].bang:
            block_stack.pop()
        continue # don't add empty lines to content lists

    if len(block_stack) == 0:
        if is_single_line_block(line):
            new_block = make_new_single_line_block(line)
            new_block.content.append(line)
            root.children.append(new_block)
        else:
            new_block = make_new_multi_line_block(line)
            if not new_block.bang:
                new_block.content.append(line)
            root.children.append(new_block)
            block_stack.append(new_block)
        continue # prevent double addition to content lists

    if line[:4] == "!end":
        while not block_stack[-1].bang:
            block_stack.pop()

        block_stack.pop()
        continue # don't add "end" lines to content lists

    if block_stack[-1].bang:
        # we can start any blocks within bangs
        # including headers, horizontal lines, etc.
        if is_single_line_block(line):
            new_block = make_new_single_line_block(line)
        else:
            new_block = make_new_multi_line_block(line)
        if new_block.bang and new_block.name == "end":
            block_stack.pop()
        else:
            block_stack[-1].children.append(new_block)
            block_stack.append(new_block)

    elif block_stack[-1].name == "ol":
        if not (line[0].isdigit() and line.find(".") != -1 and line[:line.find(".")].isdigit()):
            # we are out of the list, return to the parent p block or make a new one
            block_stack.pop()
            new_block = make_new_multi_line_block(line)
            if block_stack[-1].name != "p" or new_block.name != "p":
                block_stack[-1].children.append(new_block)
                block_stack.append(new_block)

    elif block_stack[-1].name == "ul":
        if not (line[:2] == "- " or line[:2] == "+ " or line[:2] == "* "):
            # we are out of the list, return to the parent p block or make a new one
            block_stack.pop()
            new_block = make_new_multi_line_block(line)
            if block_stack[-1].name != "p" or new_block.name != "p":
                block_stack[-1].children.append(new_block)
                block_stack.append(new_block)

    elif block_stack[-1].name == "blockquote":
        if not line[:2] == "> ":
            # we are out of the blockquote, return to the parent block or make a new one
            block_stack.pop()
            new_block = make_new_multi_line_block(line)
            if block_stack[-1].name != "p" or new_block.name != "p":
                block_stack[-1].children.append(new_block)
                block_stack.append(new_block)

    elif block_stack[-1].name == "p":
        # is this the start of a new block?
        new_block = make_new_multi_line_block(line)
        if new_block.name != "p":
            block_stack.pop()
            block_stack[-1].children.append(new_block)
            block_stack.append(new_block)
        # if it isn't, ignore the new block we just made

    if not block_stack[-1].bang:
        block_stack[-1].content.append(line)

# recursive_print(root)

def make_html(node, level=0):

    if node.bang:
        bang = BANGS[node.name]
        if node.name == "title":
            node.content = ["".join(node.content)[7:]]
        content = ["".join(node.content)]
        for x in node.children:
            content.append("".join(make_html(x, level=level+1)))
        "".join(content)

        return bang.html("".join(content))

    else:
        if node.name == "p":
            content = ["<p>\n", "".join(node.content), "</p>\n"]

        elif node.name == "ul":
            content=["<ul>"]
            for line in node.content:
                content.append(f"<li>{line.strip()[2:]}</li>\n")
            content.append(f"</{node.name}>\n")

        elif node.name == "ol":
            content = [f"<{ol}>\n"]
            for line in node.content:
                line = line.strip()
                dot_idx = line.find(".")
                content.append(f"<li>{line[:dot_idx+1]}</li>\n")
            content.append(f"</{ol}>\n")

        elif "#" in node.name:
            content = f"<h{len(node.name)}>" + "".join(node.content).strip()[2:] + f"</h{len(node.name)}>\n"

        else:
            content = ["<p>\n", "".join(node.content), "</p>\n"]

        # content = ["".join(node.content)]
        for x in node.children:
            # content.append("".join(x.content))
            content.append("".join(make_html(x, level=level+1)))
        return "".join(content)

def find_unescaped(line, substr, start=0):
    last_idx = start
    while True:
        if last_idx >= len(line):
            return -1
        idx = line.find(substr, last_idx)
        if idx == -1 or line[idx-1] != "\\":
            return idx
        else:
            last_idx = idx + 1

def handle_markdown(line):
    while line.count("**") >= 2:
        idx1 = find_unescaped(line, "**")
        if idx1 == -1:
            break
        idx2 = find_unescaped(line, "**", idx1+1)
        if idx2 == -1:
            break
        new_line = line[:idx1] + "<b>" + line[idx1+2:idx2] + "</b>"
        if len(line) > idx2 + 2:
            new_line += line[idx2+2:]
        line = new_line
    while line.count("*") - line.count("**") >= 2:
        idx1 = find_unescaped(line, "*")
        if idx1 == -1:
            break
        idx2 = find_unescaped(line, "*", idx1+1)
        if idx2 == -1:
            break
        new_line = line[:idx1] + "<i>" + line[idx1+1:idx2] + "</i>"
        if len(line) > idx2 + 1:
            new_line += line[idx2+1:]
        line = new_line
    while line.count("`") >= 2:
        idx1 = find_unescaped(line, "`")
        if idx1 == -1:
            break
        idx2 = find_unescaped(line, "`", idx1+1)
        if idx2 == -1:
            break
        new_line = line[:idx1] + "<code>" + line[idx1+1:idx2] + "</code>"
        if len(line) > idx2 + 1:
            new_line += line[idx2+1:]
        line = new_line
    while line.count("$") >= 2:
        idx1 = find_unescaped(line, "$")
        if idx1 == -1:
            break
        idx2 = find_unescaped(line, "$", idx1+1)
        if idx2 == -1:
            break
        new_line = line[:idx1] + "\\(" + line[idx1+1:idx2] + "\\)"
        if len(line) > idx2 + 1:
            new_line += line[idx2+1:]
        line = new_line
    return line


out_html = make_html(root)
out_html = out_html.split("\n")
for i in range(len(out_html)):
    out_html[i] = handle_markdown(out_html[i]).strip()
out_html = "\n".join(out_html)

for block in root.children:
    if block.name == "title":
        TITLE = block.content[0]

header_html = "\n".join([
    "<!DOCTYPE html>",
    "<html lang=\"en\" dir=\"ltr\">",
    "<head>",
    "<meta charset=\"utf-8\">",
    "<title>" + TITLE + "</title>",
    "<link rel=\"stylesheet\" href=\"/inter/inter.css\">",
    "<link rel=\"stylesheet\" href=\"/css/main.css\">",
    "<link rel=\"stylesheet\" href=\"/css/math.css\">",
    "<script src=\"https://polyfill.io/v3/polyfill.min.js?features=es6\"></script>",
    "<script id=\"MathJax-script\" async",
    "src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js\">",
    "</script>",
    "</head>",
    "<body>"
])

out_html = header_html + out_html + "</body>\n</html>"

# print(out_html)

if opts.output:
    with open(opts.output, "w") as f:
        f.writelines(out_html)



