import re
import sys

class ObjCParser:
    def __init__(self):
        self.in_class = False
        self.in_decl_body = False
        self.in_implementation = False
        self.in_funcsign = False
        self.funcsign_body = ""
        self.implementation_name = ""
        self.last_tabstop = "        "
        self.fpat = r"[0-9a-zA-Z@_<>,]+"
        self.class_name = ""

    def move_oneline_comments(self, line):
        match = re.search(r'(".*")*//', line)
        if match:
            print(line[match.start()+2:])
            return line[:match.start()+2]
        return line

    def move_multiline_comments(self, line):
        match = re.search(r'(".*")*//', line)
        if match:
            print(line[match.start()+2:])
            return line[:match.start()+2]
        return line

    def extract_type(self, funcsign_body):
        match = re.search(r'\([0-9a-zA-Z_\* ]+\)', funcsign_body)
        if match:
            type_str = funcsign_body[match.start():match.end()]
            match = re.search(r'[0-9a-zA-Z_\* ]+', type_str)
            return match.group(0), funcsign_body[match.end():]
        return "", funcsign_body

    def extract_somename(self, funcsign_body):
        match = re.search(r'[0-9a-zA-Z_]+', funcsign_body)
        if match:
            return match.group(0), funcsign_body[match.end():]
        return "", funcsign_body

    def func_sign_rewrite(self, funcsign_body, class_name):
        funcsign_body = re.sub(r"[ \n\t]+", " ", funcsign_body)
        static = "static " if funcsign_body.startswith("+") else ""
        class_name = f"{class_name}::" if class_name else ""
        ret_type = "void"
        
        if re.match(r'^[\+-][ ]*\([0-9a-zA-Z_\* ]+\)', funcsign_body):
            ret_type, funcsign_body = self.extract_type(funcsign_body)
        
        func_name = ""
        params = []
        do_scan = True
        func_name_delim = ""
        
        while do_scan:
            func_name_part, funcsign_body = self.extract_somename(funcsign_body)
            if func_name_part:
                func_name += func_name_delim + func_name_part
                if funcsign_body.startswith(":"):
                    arg_type, funcsign_body = self.extract_type(funcsign_body)
                    arg_name, funcsign_body = self.extract_somename(funcsign_body)
                    if arg_type and arg_name:
                        params.append(f"{arg_type} {arg_name}")
                    else:
                        do_scan = False
                else:
                    do_scan = False
            else:
                do_scan = False
            func_name_delim = "_"
        
        result_sign = f"{static}{ret_type} {class_name}{func_name}({', '.join(params)})"
        return result_sign + ";" if not class_name else result_sign

    def process_line(self, line):
        do_print = True
        line = re.sub(r"^#import", "#include", line)
        line = re.sub(r"^@public", "public:", line)
        line = re.sub(r"^@private", "private:", line)
        
        if re.match(r"^@(interface|protocol)", line):
            self.in_class = True
            do_print = False
            if not re.match(r".*([:,])+([ \t])*", line):
                self.in_decl_body = True
                line = line.replace("{", "")
            
            match = re.match(r"^@(interface|protocol)(.+):(.+)", line)
            if match:
                self.class_name = match.group(2)
                print(f"class {self.class_name}: public {line}")
            else:
                print(f"class {line.split()[1]}")
            
            if self.in_decl_body:
                print("{")
        
        elif re.match(r"^@implementation", line):
            self.in_implementation = True
            self.implementation_name = line.split()[1]
            do_print = False
        
        elif re.match(r"^@end", line):
            if self.in_class:
                print("};")
            self.in_class = self.in_implementation = self.in_decl_body = False
            do_print = False
        
        elif self.in_class or self.in_implementation:
            if self.in_class and do_print and not self.in_decl_body:
                if not re.match(r".*([:,])+([ \t])*", line):
                    self.in_decl_body = True
                    line = line.replace("{", "")
                    print(line)
                    print("{")
                    do_print = False
            elif self.in_class and re.match(r"^[{}]", line):
                do_print = False
            
            if do_print:
                if re.match(r"^([+-])", line):
                    self.in_funcsign = True
                    do_print = False
                    if re.search(r"[\{|;]", line):
                        cut_till = re.search(r"[\{|;]", line).start()
                        self.funcsign_body += line[:cut_till]
                        self.in_funcsign = False
                        print(self.last_tabstop + self.func_sign_rewrite(self.funcsign_body, self.implementation_name))
                        if self.in_implementation:
                            print("{")
                        self.funcsign_body = ""
                    else:
                        self.funcsign_body = line
                elif self.in_funcsign:
                    do_print = False
                    if re.search(r"[\{|;]", line):
                        cut_till = re.search(r"[\{|;]", line).start()
                        self.funcsign_body += line[:cut_till]
                        self.in_funcsign = False
                        print(self.last_tabstop + self.func_sign_rewrite(self.funcsign_body, self.implementation_name))
                        if self.in_implementation:
                            print("{")
                        self.funcsign_body = ""
                    else:
                        self.funcsign_body += line
                elif not self.last_tabstop:
                    tabstop_len = re.search(r"[^ ]", line).start()
                    self.last_tabstop = line[:tabstop_len]
        
        if do_print:
            print(line)

def parse_file(file_path):
    parser = ObjCParser()
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            parser.process_line(line)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python converter.py <objc-file>")
        sys.exit(1)
    
    objc_file = sys.argv[1]
    parse_file(objc_file)
