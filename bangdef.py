class Bang:

    class OutManager:
        def __init__(self, takes_opt):
            self.takes_opt = takes_opt
            self.raw_lines = []

        def out(self, content, opt=None):
            out_string = ""
            for x in self.raw_lines:
                if self.takes_opt and "{opt}" in x:
                    if opt is not None:
                        x = x.replace("{opt}", opt)
                    else:
                        continue
                elif "{content}" in x:
                    x = x.replace("{content}", content)
                out_string += x
            return out_string

    def __init__(self, name, is_single_line=False, takes_opt=True, __protected__=False):
        if not __protected__ and name in ["end", "title"]:
            raise Exception(f"Attempted to define bang using protected name: {name}.")
        self.name = name
        self.out = self.OutManager(takes_opt)
        self.takes_opt = takes_opt
        self.is_single_line = is_single_line

    def __str__(self):
        return f"Bang: !{self.name}"

    def html(self, content, opt=None):
        if self.takes_opt:
            return self.out.out(content, opt)
        else:
            return self.out.out(content)


# Initialize protected bang
title = Bang(name="title", is_single_line=True, takes_opt=False, __protected__=True)
title.out.raw_lines = [
    "<div class=\"title\">\n",
    "  <h1>{content}</h1>\n",
    "</div>\n",
]


def read_bangs(bdef_file):
    with open(bdef_file, 'r') as f:
        lines = f.readlines()

    bangs = dict()
    current = None
    for i, line in enumerate(lines):
        if current is None:
            # Look to make new bang
            if line.strip() == "" or line[0] != "!" or ":=" not in line:
                continue

            if line.count("{") == 2:
                open_idx = line.find("{")
                close_idx = line.find("}")
                if close_idx == -1 or close_idx < open_idx:
                    raise Exception(f"Invalid bang definition on line {i}.")
                if line.find("{", open_idx+1) < line.find(":="):
                    raise Exception(f"Invalid bang definition on line {i}.")

                takes_opt = True
                bang_name = line.split()[0][1:open_idx]

            elif line.count("{") == 1:
                if line.find("{") < line.find(":="):
                    raise Exception(f"Invalid bang definition on line {i}.")

                takes_opt = False
                bang_name = line.split()[0][1:]

            else:
                raise Exception(f"Invalid bang definition on line {i}.")

            is_single_line = not "!end" in line
            if bang_name in bangs:
                raise Exception(f"Provided multiple definitions for bang named {bang_name}.")
            current = Bang(name=bang_name, takes_opt=takes_opt, is_single_line=is_single_line)

        elif line[0] != "}":
            current.out.raw_lines.append(line)

        else:
            bangs[current.name] = current
            current = None

    bangs[title.name] = title
    return bangs


if __name__ == "__main__":
    bang_list = read_bangs('./bangs.bdef')
    for x in bang_list:
        print(x, x.takes_opt)
        print("Out:")
        print(x.html(content="<p>Wowee</p>", opt=""))
