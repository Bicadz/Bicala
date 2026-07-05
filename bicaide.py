import sys
import io
import os
import contextlib
import tkinter as tk
from tkinter import filedialog, ttk, simpledialog
import re
import traceback
import threading
import queue
import pathlib

# Add main directory to sys.path for imports without __init__.py (same as run.py)
# Use pathlib for cross-platform compatibility
script_dir = pathlib.Path(__file__).parent.resolve()
main_dir = script_dir / 'main'
sys.path.insert(0, str(main_dir))

try:
    # Import from run.py at the root level using importlib
    import importlib.util
    spec = importlib.util.spec_from_file_location("run", os.path.join(os.path.dirname(__file__), 'run.py'))
    run_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run_module)
    run_code_text = run_module.run_code_text_ast
    run_file = run_module.run_file_ast
    # Import from main modules (main is already in sys.path)
    from err import BicalaError, format_error
    from eval import set_gui_input_callback
    from tok import KEYWORDS as BICALA_KEYWORDS

except Exception as e:
    print(f"[IDE Warning] Failed to load Bicala Core, using fallback Python: {e}")

    def run_code_text(code):
        glb = {"__name__": "__main__"}
        exec(compile(code, "<editor>", "exec"), glb, glb)

    def format_error(err, source_lines=None, context=1):
        return str(err)

    class BicalaError(Exception):
        pass

    def run_file(path):
        pass

    def set_gui_input_callback(callback):
        pass

    # Fallback keywords for syntax highlighting
    BICALA_KEYWORDS = None

fonts = ("Consolas", 11)

def get_latest_version():
    """Parse change.log to find the latest version string."""
    import os
    # Try to find change.log in the docs directory relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, "docs", "change.log")
    
    if not os.path.exists(log_path):
        return "Bicala Beta"
    
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines):
            clean_line = line.strip()
            if clean_line.startswith("+"):
                version_text = clean_line.lstrip("+").rstrip(":").strip()
                if not version_text.startswith("Bicala"):
                    return f"Bicala {version_text}"
                return version_text
    except Exception:
        pass
    return "Bicala Beta"

def launch_ide(initial_file=None, auto_run=False):
    app = tk.Tk()
    app.title("Bicala")
    app.geometry("1000x680")

    current_file = {"path": None}
    project_root = {"path": None}

    # Thread-safe input handling using queue
    input_request_queue = queue.Queue()
    input_response_queue = queue.Queue()
    input_pending = {"active": False}
    
    # Status state management
    status_state = {"status": "Ready", "severity": "OK"}
    status_update_queue = queue.Queue()
    
    # Get latest version at startup
    latest_version = get_latest_version()
 
    def gui_input(prompt=""):
        """Request input from output panel entry."""
        input_request_queue.put(prompt)
        return input_response_queue.get()
 
    # Set the callback
    try:
        set_gui_input_callback(gui_input)
    except NameError:
        pass
 
    VS_BG = "#1b1b1b"
    VS_PANEL = "#252526"
    VS_PANEL2 = "#1f1f1f"
    VS_BORDER = "#333333"
    VS_FG = "#d4d4d4"
    VS_MUTED = "#858585"
    VS_ACCENT = "#252526"

    app.configure(bg=VS_BG)
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Treeview", background=VS_PANEL, fieldbackground=VS_PANEL, foreground=VS_FG, borderwidth=0, relief="flat")
    style.map("Treeview", background=[("selected", "#094771")], foreground=[("selected", VS_FG)])
    style.configure("Treeview.Heading", background=VS_PANEL, foreground=VS_FG)
    style.configure("TScrollbar", background=VS_PANEL, troughcolor=VS_BG, arrowcolor=VS_FG, bordercolor=VS_BORDER)
    style.configure("TButton", padding=(8, 2))

    def set_title(path=None):
        name = "Untitled.bica" if not path else os.path.basename(path)
        app.title(f"Bicala — {name}")

    menu_bar = tk.Menu(app)
    app.config(menu=menu_bar)

    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="New", command=lambda: new_file(), accelerator="Ctrl+N")
    file_menu.add_command(label="Open...", command=lambda: open_file(), accelerator="Ctrl+O")
    file_menu.add_command(label="Open Folder...", command=lambda: open_folder(), accelerator="Ctrl+Shift+O")
    file_menu.add_command(label="Save", command=lambda: save_file(), accelerator="Ctrl+S")
    file_menu.add_command(label="Save As...", command=lambda: save_file_as(), accelerator="Ctrl+Shift+S")
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=app.quit)
    menu_bar.add_cascade(label="File", menu=file_menu)

    edit_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Edit", menu=edit_menu)

    run_menu = tk.Menu(menu_bar, tearoff=0)
    run_menu.add_command(label="Run", command=lambda: run_current(), accelerator="Ctrl+R")
    menu_bar.add_cascade(label="Run", menu=run_menu)

    help_menu = tk.Menu(menu_bar, tearoff=0)
    help_menu.add_command(label="About", command=lambda: append_output("Bicala IDE (BicaIDE) - Notepad++ style interface\n", 'info'))
    menu_bar.add_cascade(label="Help", menu=help_menu)

    content_paned = tk.PanedWindow(app, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=6, bg=VS_BG)
    content_paned.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 0))

    explorer_frame = tk.Frame(content_paned, bg=VS_PANEL2)
    main_frame = tk.Frame(content_paned, bg=VS_BG)
    content_paned.add(explorer_frame, minsize=180)
    content_paned.add(main_frame, minsize=520)

    main_paned = tk.PanedWindow(main_frame, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=6, bg=VS_BG)
    main_paned.pack(fill=tk.BOTH, expand=True)

    editor_frame = tk.Frame(main_paned, bg=VS_BG)
    output_frame = tk.Frame(main_paned, bg=VS_PANEL2)
    main_paned.add(editor_frame, minsize=280)
    main_paned.add(output_frame, minsize=140)

    explorer_title = tk.StringVar(value="EXPLORER")
    explorer_label = tk.Label(explorer_frame, textvariable=explorer_title, anchor="w", font=fonts+("bold",), bg=VS_PANEL2, fg=VS_FG)
    explorer_label.pack(fill=tk.X, padx=8, pady=(8, 6))

    explorer_controls = tk.Frame(explorer_frame, bg=VS_PANEL2)
    explorer_controls.pack(fill=tk.X, padx=8, pady=(0, 6))

    explorer_search_var = tk.StringVar(value="")
    explorer_filter_var = tk.StringVar(value="All")

    explorer_search = tk.Entry(
        explorer_controls,
        textvariable=explorer_search_var,
        bg=VS_PANEL,
        fg=VS_FG,
        insertbackground=VS_FG,
        relief="flat",
        highlightthickness=1,
        highlightbackground=VS_BORDER,
        highlightcolor="#094771",
    )
    explorer_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

    explorer_filter = ttk.Combobox(
        explorer_controls,
        textvariable=explorer_filter_var,
        values=["All", "BICA"],
        width=6,
        state="readonly",
    )
    explorer_filter.pack(side=tk.LEFT)
    explorer_tree_frame = tk.Frame(explorer_frame, bg=VS_PANEL2)
    explorer_tree_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

    explorer_tree = ttk.Treeview(explorer_tree_frame, show="tree")
    explorer_tree_scroll = ttk.Scrollbar(explorer_tree_frame, orient="vertical", command=explorer_tree.yview)
    explorer_tree.configure(yscrollcommand=explorer_tree_scroll.set)
    explorer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    explorer_tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    explorer_paths = {}

    line_numbers = tk.Text(
        editor_frame,
        width=5,
        padx=5,
        takefocus=0,
        border=0,
        background=VS_PANEL,
        foreground=VS_MUTED,
        state="disabled",
        font=fonts,
    )
    line_numbers.config(yscrollcommand=lambda *args: None, state="disabled")
    line_numbers.bind("<MouseWheel>", lambda e: "break")

    editor = tk.Text(
        editor_frame,
        wrap="none",
        font=fonts,
        undo=True,
        bg=VS_BG,
        fg=VS_FG,
        insertbackground=VS_FG,
        selectbackground="#264f78",
        selectforeground=VS_FG,
        highlightthickness=0,
    )
    
    # Syntax highlighting configuration
    keywords = BICALA_KEYWORDS if BICALA_KEYWORDS is not None else {
        'help', 'say', 'input', 'if', 'elif', 'else', 'while', 'forever', 'repeat', 
        'for', 'def', 'break', 'continue', 'debug',
        'str', 'int', 'float', 'bool', 'type', 'error'
    }

    logic_keywords = {'and', 'or', 'not', 'in'}
    
    # Color scheme
    colors = {
        'keyword': '#c586c0',
        'logic': '#569cd6',
        'comparison': '#d4d4d4',
        'math': '#d4d4d4',
        'assign': '#d4d4d4',
        'variable': '#9cdcfe',
        'param': '#9cdcfe',
        'function_name': '#dcdcaa',
        'method': '#dcdcaa',
        'string': '#ce9178',
        'number': '#b5cea8',
        'comment': '#6a9955',
        'indent_guide': '#2a2d2e',
        'error_line': '#3b1515',
    }

    line_numbers.pack(side=tk.LEFT, fill=tk.Y)
    scrollbar = tk.Scrollbar(editor_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    editor.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    line_count_cache = [0]

    def update_line_numbers(force=False):
        total_lines = int(editor.index("end-1c").split(".")[0])
        if total_lines < 1:
            total_lines = 1
        if not force and total_lines == line_count_cache[0]:
            return
        line_count_cache[0] = total_lines
        line_numbers.config(state="normal")
        line_numbers.delete("1.0", tk.END)
        for n in range(1, total_lines + 1):
            line_numbers.insert(tk.END, f"{n}\n")
        line_numbers.config(state="disabled")

    def on_scroll(first, last):
        editor.yview_moveto(first)
        line_numbers.yview_moveto(first)
        scrollbar.set(first, last)

    editor.config(yscrollcommand=on_scroll)
    scrollbar.config(command=editor.yview)

    update_job = [None]

    def set_status(status, severity="OK"):
        """Update status state with severity integration."""
        status_state["status"] = status
        status_state["severity"] = severity
        # Trigger status bar update
        app.after(0, update_status)

    def update_status(event=None):
        text = editor.get("1.0", "end-1c")
        length = len(text)
        lines = int(editor.index("end-1c").split(".")[0])
        ln, col = editor.index(tk.INSERT).split(".")
        pos = len(editor.get("1.0", tk.INSERT))
        
        # Build status field with severity integration
        status_text = status_state["status"]
        severity = status_state["severity"]
        if severity != "OK":
            status_text = f"{status_text}, {severity}"
        
        status.config(text=f"Length: {length} Line: {lines} | Ln: {int(ln)} Col: {int(col)} Pos: {pos} | Status: {status_text} | {latest_version}")
    
    def apply_syntax_highlighting():
        # Remove all existing tags except selection and error markers
        for tag in editor.tag_names():
            if tag not in ('sel', 'error_line'):
                editor.tag_remove(tag, '1.0', tk.END)
        
        # Configure tags
        editor.tag_config('keyword', foreground=colors['keyword'])
        editor.tag_config('logic', foreground=colors['logic'])
        editor.tag_config('comparison', foreground=colors['comparison'])
        editor.tag_config('math', foreground=colors['math'])
        editor.tag_config('assign', foreground=colors['assign'])
        editor.tag_config('variable', foreground=colors['variable'])
        editor.tag_config('param', foreground=colors['param'])
        editor.tag_config('function_name', foreground=colors['function_name'])
        editor.tag_config('method', foreground=colors['method'])
        editor.tag_config('string', foreground=colors['string'])
        editor.tag_config('number', foreground=colors['number'])
        editor.tag_config('comment', foreground=colors['comment'])
        editor.tag_config('operator', foreground=colors['comparison'])
        editor.tag_config('indent_guide', background=colors['indent_guide'], relief='flat', borderwidth=0)
        editor.tag_config('error_line', background=colors['error_line'])
        
        # Get all text
        content = editor.get('1.0', tk.END)
        lines = content.split('\n')
        defined_functions = set()
        for source_line in lines:
            def_match = re.match(r'^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\b', source_line)
            if def_match:
                defined_functions.add(def_match.group(1))
        
        for line_num, line in enumerate(lines, 1):
            line_start = f'{line_num}.0'
            line_end = f'{line_num}.end'
            
            # Skip empty lines
            stripped = line.lstrip()
            if not stripped:
                continue
            
            # Highlight indent guides (spaces at 0, 4, 8, 12...)
            indent_len = len(line) - len(stripped)
            for guide_col in range(0, indent_len, 4):
                pos = f'{line_num}.{guide_col}'
                editor.tag_add('indent_guide', pos, f'{line_num}.{guide_col + 1}')
            
            # Highlight comments first (single line)
            if '#' in line:
                comment_pos = line.find('#')
                # Check if it's not inside a string
                before_comment = line[:comment_pos]
                if before_comment.count('"') % 2 == 0 and before_comment.count("'") % 2 == 0:
                    comment_start = f'{line_num}.{comment_pos}'
                    editor.tag_add('comment', comment_start, line_end)
                    # Remove comment part for further processing
                    line = line[:comment_pos]
                    line_end = comment_start
            
            # Highlight block comments
            if '###' in line:
                block_start = line.find('###')
                block_start_pos = f'{line_num}.{block_start}'
                editor.tag_add('comment', block_start_pos, line_end)
                continue
            
            # Highlight strings and track ranges
            string_ranges = []  # List of (start, end) tuples
            
            # Double quotes
            in_double_string = False
            dbl_start = 0
            for i, char in enumerate(line):
                if char == '"' and (i == 0 or line[i-1] != '\\'):
                    if not in_double_string:
                        dbl_start = i
                        in_double_string = True
                    else:
                        string_ranges.append((dbl_start, i+1))
                        editor.tag_add('string', f'{line_num}.{dbl_start}', f'{line_num}.{i+1}')
                        in_double_string = False
            
            # Single quotes
            in_single_string = False
            sng_start = 0
            for i, char in enumerate(line):
                if char == "'" and (i == 0 or line[i-1] != '\\'):
                    if not in_single_string:
                        sng_start = i
                        in_single_string = True
                    else:
                        string_ranges.append((sng_start, i+1))
                        editor.tag_add('string', f'{line_num}.{sng_start}', f'{line_num}.{i+1}')
                        in_single_string = False
            
            def is_in_string(pos):
                """Check if position falls within any string range"""
                for start, end in string_ranges:
                    if start <= pos < end:
                        return True
                return False
            
            # Highlight numbers (skip if in string)
            number_pattern = r'\b\d+(\.\d+)?\b'
            for match in re.finditer(number_pattern, line):
                if not is_in_string(match.start()):
                    start = f'{line_num}.{match.start()}'
                    end = f'{line_num}.{match.end()}'
                    editor.tag_add('number', start, end)
            
            # Highlight keywords (skip if in string)
            for keyword in keywords:
                if keyword.startswith('math.') or keyword.startswith('str.') or keyword in ('str', 'int', 'float', 'bool', 'type', 'error'):
                    pattern = r'\b' + re.escape(keyword) + r'(?=\s|$)'
                else:
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                for match in re.finditer(pattern, line):
                    if not is_in_string(match.start()):
                        start = f'{line_num}.{match.start()}'
                        end = f'{line_num}.{match.end()}'
                        editor.tag_add('keyword', start, end)

            # Highlight logic operators
            for keyword in logic_keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                for match in re.finditer(pattern, line):
                    if not is_in_string(match.start()):
                        start = f'{line_num}.{match.start()}'
                        end = f'{line_num}.{match.end()}'
                        editor.tag_add('logic', start, end)

            # Highlight assignment operators
            assign_ops = [':', '+=', '-=', '*=', '/=', '//=', '%=', '**=', '+:', '-:', '*:', '/:']
            for op in sorted(assign_ops, key=len, reverse=True):
                pos = 0
                while True:
                    pos = line.find(op, pos)
                    if pos == -1:
                        break
                    if not is_in_string(pos):
                        start = f'{line_num}.{pos}'
                        end = f'{line_num}.{pos + len(op)}'
                        editor.tag_add('assign', start, end)
                    pos += 1

            # Highlight comparison and math operators
            comparison_ops = ['!===' , '===', '!==', '==', '!=', '>=', '<=', '>', '<', '=', '?']
            math_ops = ['**', '//', '+', '-', '*', '/', '%']
            for op in sorted(comparison_ops, key=len, reverse=True):
                pos = 0
                while True:
                    pos = line.find(op, pos)
                    if pos == -1:
                        break
                    if not is_in_string(pos):
                        start = f'{line_num}.{pos}'
                        end = f'{line_num}.{pos + len(op)}'
                        editor.tag_add('comparison', start, end)
                    pos += 1
            for op in sorted(math_ops, key=len, reverse=True):
                pos = 0
                while True:
                    pos = line.find(op, pos)
                    if pos == -1:
                        break
                    if not is_in_string(pos):
                        start = f'{line_num}.{pos}'
                        end = f'{line_num}.{pos + len(op)}'
                        editor.tag_add('math', start, end)
                    pos += 1

            # Highlight variable names and function-related tokens
            assign_match = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:', line)
            if assign_match and not is_in_string(assign_match.start(1)):
                start = f'{line_num}.{assign_match.start(1)}'
                end = f'{line_num}.{assign_match.end(1)}'
                editor.tag_add('variable', start, end)

            for match in re.finditer(r'for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\b', line):
                if not is_in_string(match.start(1)):
                    start = f'{line_num}.{match.start(1)}'
                    end = f'{line_num}.{match.end(1)}'
                    editor.tag_add('variable', start, end)

            # Highlight general variables (x, y, z, etc.) only when they are not keywords, methods, or function names
            for var_match in re.finditer(r'\b([A-Za-z_][A-Za-z0-9_]*)\b', line):
                name = var_match.group(1)
                start = var_match.start(1)
                end = var_match.end(1)
                if is_in_string(start):
                    continue
                if name in keywords or name in logic_keywords:
                    continue
                if line[start-1:start] == '.':
                    continue
                if re.match(r'[A-Za-z_][A-Za-z0-9_]*\s*(?=\()', line[start:]):
                    continue
                if re.match(r'^\s*def\s+' + re.escape(name) + r'\b', line):
                    continue
                if re.match(r'^\s*def\s+[A-Za-z_][A-Za-z0-9_]*\b', line) and start < line.index('def') + 3:
                    continue
                if re.match(r'^\s*' + re.escape(name) + r'\s+', line) and name in defined_functions:
                    continue
                editor.tag_add('variable', f'{line_num}.{start}', f'{line_num}.{end}')

            def_def = re.match(r'^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)', line)
            if def_def and not is_in_string(def_def.start(1)):
                fn_start = f'{line_num}.{def_def.start(1)}'
                fn_end = f'{line_num}.{def_def.end(1)}'
                editor.tag_add('function_name', fn_start, fn_end)

                params_part = line[def_def.end(1):]
                for param_match in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)', params_part):
                    param_start = def_def.end(1) + param_match.start(1)
                    param_end = def_def.end(1) + param_match.end(1)
                    if not is_in_string(param_start):
                        editor.tag_add('param', f'{line_num}.{param_start}', f'{line_num}.{param_end}')

            for call_match in re.finditer(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()', line):
                if def_def and call_match.group(1) == def_def.group(1):
                    continue
                if not is_in_string(call_match.start(1)):
                    start = f'{line_num}.{call_match.start(1)}'
                    end = f'{line_num}.{call_match.end(1)}'
                    editor.tag_add('function_name', start, end)

            bare_call = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s+(.+)$', line)
            if bare_call:
                bare_name = bare_call.group(1)
                first_part = bare_name.split('.')[0]
                if (
                    first_part not in keywords
                    and first_part not in logic_keywords
                    and first_part not in {'elif', 'else', 'while', 'for', 'repeat', 'forever', 'return', 'break', 'continue', 'import', 'from', 'as'}
                    and ('.' in bare_name or bare_name in defined_functions)
                    and not is_in_string(bare_call.start(1))
                ):
                    start = f'{line_num}.{bare_call.start(1)}'
                    end = f'{line_num}.{bare_call.end(1)}'
                    editor.tag_add('function_name', start, end)

            # Highlight object names before dot access, e.g. obj.some, math.max, str.lower
            for obj_match in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\.(?=[A-Za-z_])', line):
                if not is_in_string(obj_match.start(1)):
                    start = f'{line_num}.{obj_match.start(1)}'
                    end = f'{line_num}.{obj_match.end(1)}'
                    editor.tag_add('variable', start, end)

            for method_match in re.finditer(r'(?<=\.)[A-Za-z_][A-Za-z0-9_]*', line):
                if not is_in_string(method_match.start()):
                    start = f'{line_num}.{method_match.start()}'
                    end = f'{line_num}.{method_match.end()}'
                    editor.tag_add('method', start, end)

    def schedule_update(event=None):
        if update_job[0]:
            app.after_cancel(update_job[0])
        # Set status to Analyzing during syntax highlighting
        set_status("Analyzing")
        update_job[0] = app.after(20, lambda: (update_line_numbers(force=False), apply_syntax_highlighting(), set_status("Ready")))
        update_status()

    editor.bind("<KeyPress>", schedule_update)
    editor.bind("<ButtonRelease-1>", schedule_update)
    editor.bind("<MouseWheel>", schedule_update)

    # Tab handling: insert 4 spaces instead of tab character
    def on_tab(event):
        editor.insert(tk.INSERT, "    ")
        return "break"
    editor.bind("<Tab>", on_tab)

    def on_shift_tab(event):
        try:
            sel_start = editor.index("sel.first")
            sel_end = editor.index("sel.last")
        except tk.TclError:
            line_num = editor.index(tk.INSERT).split('.')[0]
            sel_start = f"{line_num}.0"
            sel_end = f"{line_num}.end"

        start_line = int(sel_start.split('.')[0])
        end_line = int(sel_end.split('.')[0])
        for line in range(start_line, end_line + 1):
            line_start = f"{line}.0"
            line_end = f"{line}.end"
            content = editor.get(line_start, line_end)
            current_indent = len(content) - len(content.lstrip())
            remove = min(4, current_indent)
            if remove > 0:
                editor.delete(line_start, f"{line}.{remove}")
        return "break"
    editor.bind("<Shift-Tab>", on_shift_tab)

    # Auto indent on Return: preserve indent, +4 only when cursor is after block keyword
    BLOCK_KEYWORDS = {'def', 'if', 'elif', 'else', 'while', 'forever', 'repeat', 'for'}
    def on_return(event):
        # Get current line and cursor position
        line_num, cursor_col = map(int, editor.index(tk.INSERT).split('.'))
        current_line = editor.get(f"{line_num}.0", f"{line_num}.end")
        # Get current indent level
        current_indent = len(current_line) - len(current_line.lstrip())
        stripped = current_line.lstrip()
        first_word = stripped.split()[0] if stripped else ''
        
        # Only increase indent if:
        # 1. Line starts with block keyword AND
        # 2. Cursor is positioned after the keyword (not before it)
        if first_word in BLOCK_KEYWORDS:
            # Find where the keyword starts in the original line
            keyword_start = current_line.find(first_word)
            keyword_end = keyword_start + len(first_word)
            # Only increase if cursor is after the keyword
            if cursor_col > keyword_end:
                new_indent = current_indent + 4
            else:
                new_indent = current_indent
        else:
            # Preserve current indent level
            new_indent = current_indent
        
        editor.insert(tk.INSERT, "\n" + " " * new_indent)
        return "break"
    editor.bind("<Return>", on_return)
    editor.bind("<KP_Enter>", on_return)  # Numpad Enter
    
    status = tk.Label(app, anchor="w", font=fonts, bg=VS_ACCENT, fg="#ffffff")
    status.pack(fill=tk.X, side=tk.BOTTOM)

    editor.bind("<KeyRelease>", lambda e: (schedule_update(), update_status()))
    editor.bind("<ButtonRelease-1>", update_status)
    editor.bind("<Motion>", update_status)

    output_header = tk.Frame(output_frame, bg=VS_PANEL2)
    output_header.pack(fill=tk.X, padx=0, pady=0)
    output_label = tk.Label(output_header, text="OUTPUT", anchor="w", font=fonts+("bold",), bg=VS_PANEL2, fg=VS_FG)
    output_label.pack(side=tk.LEFT, padx=8, pady=6)
    output = tk.Text(output_frame, height=10, wrap="word", font=fonts, bg=VS_BG, fg=VS_FG, insertbackground=VS_FG, highlightthickness=0)
    output.pack(fill=tk.BOTH, padx=8, pady=(0, 0), expand=True)
    output.tag_config('info', foreground='#cdd9e5')
    output.tag_config('warning', foreground='#d29922')
    output.tag_config('error', foreground='#ff7b72')
    output.tag_config('success', foreground='#56d364')
    output.tag_config('input', foreground='#4ec9b0')
    output.insert("1.0", "Bicala IDE ready.\n", 'info')
    output.configure(state=tk.DISABLED)

    # Track input line position
    input_line_start = [None]

    # Handle Enter key in output when waiting for input
    def on_output_enter(event):
        if not input_pending["active"]:
            return None
        
        # Get the input value (from input_line_start to cursor)
        if input_line_start[0]:
            line_start = input_line_start[0]
            line_end = output.index("insert")
            value = output.get(line_start, line_end)
            # Delete the entire prompt line (from line start to end of line)
            prompt_line_start = output.index(f"{line_start} linestart")
            output.delete(prompt_line_start, f"{line_start} lineend + 1c")
            # Add newline for next output
            output.insert(tk.END, "\n")
        else:
            # Fallback: get last line
            value = output.get("end-1c linestart", "end-1c")
            output.delete("end-1c linestart", "end")
            # Add newline for next output
            output.insert(tk.END, "\n")
        
        # Send response
        input_response_queue.put(value)
        input_pending["active"] = False
        input_line_start[0] = None
        
        # Disable editing
        output.configure(state=tk.DISABLED)
        
        return "break"

    output.bind("<Return>", on_output_enter)

    # Prevent editing before input start when input is pending
    def restrict_editing(event):
        if not input_pending["active"] or not input_line_start[0]:
            return None
        
        current_pos = output.index("insert")
        input_start = input_line_start[0]
        
        # For BackSpace: check if character before cursor is before input_start
        if event.keysym == "BackSpace":
            # Get position of character to be deleted
            if current_pos == "1.0":
                return "break"  # Can't delete at start
            prev_pos = output.index(f"{current_pos} - 1c")
            # Compare positions - only block if prev_pos is strictly before input_start
            if output.compare(prev_pos, "<", input_start):
                return "break"
        
        # For Delete: check if character at cursor is before input_start
        elif event.keysym == "Delete":
            # Only block if current_pos is strictly before input_start
            if output.compare(current_pos, "<", input_start):
                return "break"
        
        return None

    output.bind("<BackSpace>", restrict_editing)
    output.bind("<Delete>", restrict_editing)

    # Check for input requests periodically
    def check_input_requests():
        try:
            prompt = input_request_queue.get_nowait()
            # Show prompt and enable input
            input_pending["active"] = True
            output.configure(state=tk.NORMAL)
            if prompt:
                output.insert(tk.END, f"{prompt} ", 'info')
            else:
                output.insert(tk.END, "", 'info')
            # Mark the start of input line (after the prompt)
            input_line_start[0] = output.index("insert")
            output.see(tk.END)
            output.focus_set()
            # Keep output enabled for typing
        except queue.Empty:
            pass
        app.after(50, check_input_requests)

    check_input_requests()

    explorer_visible = {"value": True}
    output_visible = {"value": True}
    status_visible = {"value": True}
    line_numbers_visible = {"value": True}
    
    chord_state = {
        "waiting": False,
        "key": None
    }

    def chord(first, second, callback):
        second_key = second.strip("<>").lower()

        def reset_chord():
            chord_state["waiting"] = False
            chord_state["key"] = None

        def first_press(event=None):
            chord_state["waiting"] = True
            chord_state["key"] = first
            return "break"

        def intercept(event):
            if not chord_state["waiting"]:
                return None

            pressed = event.keysym.lower().replace("_l", "").replace("_r", "")

            if pressed.endswith("_l") or pressed.endswith("_r"):
                return "break"

            ignored = {
                "control_l", "control_r",
                "shift_l", "shift_r",
                "alt_l", "alt_r"
            }

            if pressed in ignored:
                return "break"

            if pressed == second_key:
                reset_chord()
                callback(event)
                return "break"

            return None

        app.bind(first, first_press)
        editor.bind("<KeyPress>", intercept, add="+")

    def toggle_explorer(event=None):
        panes = [str(p) for p in content_paned.panes()]

        if str(explorer_frame) in panes:
            content_paned.forget(explorer_frame)
            explorer_visible["value"] = False
        else:
            # remove all
            for pane in content_paned.panes():
                content_paned.forget(pane)

            # add lại đúng thứ tự
            content_paned.add(explorer_frame, minsize=180)
            content_paned.add(main_frame, minsize=520)

            explorer_visible["value"] = True

        return "break"

    def toggle_panel(event=None):
        panes = [str(p) for p in main_paned.panes()]
        if str(output_frame) in panes:
            main_paned.forget(output_frame)
            output_visible["value"] = False
        else:
            main_paned.add(output_frame, minsize=140)
            output_visible["value"] = True
        return "break"

    def toggle_status(event=None):
        if status_visible["value"]:
            status.pack_forget()
            status_visible["value"] = False
        else:
            status.pack(fill=tk.X, side=tk.BOTTOM)
            status_visible["value"] = True
        return "break"

    def toggle_line_numbers(event=None):
        if line_numbers_visible["value"]:
            line_numbers.pack_forget()
            line_numbers_visible["value"] = False
        else:
            line_numbers.pack(side=tk.LEFT, fill=tk.Y)
            line_numbers_visible["value"] = True
        return "break"

    # Create View menu after toggle functions are defined
    view_menu = tk.Menu(menu_bar, tearoff=0)
    view_menu.add_command(label="Toggle Explorer", command=toggle_explorer, accelerator="Ctrl+B E")
    view_menu.add_command(label="Toggle Panel", command=toggle_panel, accelerator="Ctrl+B J")
    view_menu.add_command(label="Toggle Status Bar", command=toggle_status, accelerator="Ctrl+B S")
    view_menu.add_command(label="Toggle Line Numbers", command=toggle_line_numbers, accelerator="Ctrl+B L")
    menu_bar.add_cascade(label="View", menu=view_menu)

    def set_output(text, tag='info'):
        output.configure(state=tk.NORMAL)
        output.delete("1.0", tk.END)
        if text:
            output.insert("1.0", text, tag)
        output.configure(state=tk.DISABLED)

    def append_output(text, tag='info'):
        output.configure(state=tk.NORMAL)
        output.insert(tk.END, text, tag)
        output.see(tk.END)
        output.configure(state=tk.DISABLED)

    def clear_error_highlights():
        editor.tag_remove('error_line', '1.0', tk.END)

    def load_file(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                editor.delete("1.0", tk.END)
                editor.insert("1.0", f.read())
            current_file["path"] = path
            set_title(path)
            update_line_numbers(force=True)
            apply_syntax_highlighting()
            schedule_update()
            append_output(f"Opened: {path}\n", "info")
            return True
        except Exception as exc:
            append_output(f"Open failed: {exc}\n", "error")
            return False

    def _explorer_match_file(name):
        query = explorer_search_var.get().strip().lower()
        if query and query not in name.lower():
            return False
        
        return name.lower().endswith(".bica")

    def _explorer_match_dir(name):
        query = explorer_search_var.get().strip().lower()
        if query and query not in name.lower():
            return False
        return True

    def refresh_explorer(root_path):
        explorer_tree.delete(*explorer_tree.get_children())
        explorer_paths.clear()
        if not root_path:
            explorer_title.set("EXPLORER")
            return
        root_path = os.path.abspath(root_path)
        explorer_title.set(f"EXPLORER — {os.path.basename(root_path) or root_path}")
        root_item = explorer_tree.insert("", "end", text=os.path.basename(root_path) or root_path, open=True)
        explorer_paths[root_item] = root_path
        explorer_tree.insert(root_item, "end", text="")

    def populate_dir(item_id):
        dir_path = explorer_paths.get(item_id)
        if not dir_path or not os.path.isdir(dir_path):
            return
        children = explorer_tree.get_children(item_id)
        if len(children) == 1 and explorer_tree.item(children[0], "text") == "":
            explorer_tree.delete(children[0])
        elif children:
            return
        try:
            entries = sorted(os.listdir(dir_path), key=lambda n: (not os.path.isdir(os.path.join(dir_path, n)), n.lower()))
        except Exception:
            return
        for name in entries:
            if name.startswith("."):
                continue
            full = os.path.join(dir_path, name)
            if os.path.isdir(full):
                if not _explorer_match_dir(name):
                    continue
                sub = explorer_tree.insert(item_id, "end", text=name, open=False)
                explorer_paths[sub] = full
                explorer_tree.insert(sub, "end", text="")
            else:
                if not _explorer_match_file(name):
                    continue
                leaf = explorer_tree.insert(item_id, "end", text=name, open=False)
                explorer_paths[leaf] = full

    def on_explorer_open(event=None):
        item_id = explorer_tree.focus()
        populate_dir(item_id)

    def on_explorer_activate(event=None):
        item_id = explorer_tree.focus()
        path = explorer_paths.get(item_id)
        if path and os.path.isfile(path):
            load_file(path)
            if not project_root["path"]:
                project_root["path"] = os.path.dirname(path)
                refresh_explorer(project_root["path"])

    explorer_tree.bind("<<TreeviewOpen>>", on_explorer_open)
    explorer_tree.bind("<Double-1>", on_explorer_activate)
    explorer_tree.bind("<Return>", on_explorer_activate)

    def open_folder():
        path = filedialog.askdirectory()
        if not path:
            return
        project_root["path"] = path
        refresh_explorer(path)
        root_items = explorer_tree.get_children("")
        if root_items:
            populate_dir(root_items[0])
        append_output(f"Opened folder: {path}\n", "info")

    def refresh_folder_clicked():
        if project_root["path"]:
            refresh_explorer(project_root["path"])
            root_items = explorer_tree.get_children("")
            if root_items:
                populate_dir(root_items[0])

    refresh_btn = ttk.Button(explorer_controls, text="Refresh", command=refresh_folder_clicked)
    refresh_btn.pack(side=tk.LEFT, padx=(6, 0))

    def _explorer_controls_changed(*_):
        refresh_folder_clicked()

    explorer_search_var.trace_add("write", _explorer_controls_changed)
    explorer_filter_var.trace_add("write", _explorer_controls_changed)

    def on_text_modified(event=None):
        if not editor.edit_modified():
            return
        clear_error_highlights()
        schedule_update()
        update_status()
        editor.edit_modified(False)

    editor.bind("<<Modified>>", on_text_modified)

    def highlight_error_lines(line_numbers):
        for line_number in sorted(line_numbers):
            start = f"{line_number}.0"
            end = f"{line_number}.end"
            editor.tag_add('error_line', start, end)

    def do_find(query, backwards=False):
        if not query:
            return False
        if backwards:
            start = editor.index(tk.INSERT)
            if editor.tag_ranges(tk.SEL):
                start = editor.index(f"{editor.index(tk.SEL_FIRST)}-1c")
            idx = editor.search(query, start, stopindex="1.0", backwards=True)
            if not idx:
                idx = editor.search(query, "end-1c", stopindex=start, backwards=True)
        else:
            start = editor.index(tk.INSERT)
            if editor.tag_ranges(tk.SEL):
                start = editor.index(f"{editor.index(tk.SEL_LAST)}+1c")
            idx = editor.search(query, start, stopindex=tk.END)
            if not idx:
                idx = editor.search(query, "1.0", stopindex=start)

        if not idx:
            append_output(f"Not found: {query}\n", "warning")
            return False

        end = editor.index(f"{idx}+{len(query)}c")
        editor.tag_remove(tk.SEL, "1.0", tk.END)
        editor.tag_add(tk.SEL, idx, end)
        editor.mark_set(tk.INSERT, end)
        editor.see(idx)
        editor.focus_set()
        return True

    def do_replace(query, replacement):
        if not query:
            return False
        has_sel = False
        try:
            start = editor.index(tk.SEL_FIRST)
            end = editor.index(tk.SEL_LAST)
            has_sel = True
        except tk.TclError:
            pass
        if not has_sel:
            if not do_find(query, backwards=False):
                return False
            start = editor.index(tk.SEL_FIRST)
            end = editor.index(tk.SEL_LAST)

        try:
            selected_text = editor.get(start, end)
        except tk.TclError:
            selected_text = ""
        if selected_text != query:
            if not do_find(query, backwards=False):
                return False
            start = editor.index(tk.SEL_FIRST)
            end = editor.index(tk.SEL_LAST)

        editor.delete(start, end)
        editor.insert(start, replacement)
        editor.tag_remove(tk.SEL, "1.0", tk.END)
        schedule_update()
        do_find(query, backwards=False)
        return True

    def do_replace_all(query, replacement):
        if not query:
            return 0
        count = 0
        start = "1.0"
        while True:
            idx = editor.search(query, start, stopindex=tk.END)
            if not idx:
                break
            end = editor.index(f"{idx}+{len(query)}c")
            editor.delete(idx, end)
            editor.insert(idx, replacement)
            count += 1
            start = editor.index(f"{idx}+{len(replacement)}c")
        schedule_update()
        return count

    def open_file():
        path = filedialog.askopenfilename(filetypes=[("Bicala code archive", "*.bica"), ("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        load_file(path)
        if not project_root["path"]:
            project_root["path"] = os.path.dirname(path)
            refresh_explorer(project_root["path"])

    def save_file():
        if not current_file["path"]:
            return save_file_as()
        # Get text and remove indent guide characters (|)
        text = editor.get("1.0", tk.END).replace('|', ' ').rstrip() + "\n"
        with open(current_file["path"], "w", encoding="utf-8") as f:
            f.write(text)
        append_output(f"Saved: {current_file['path']}\n")

    def save_file_as():
        path = filedialog.asksaveasfilename(defaultextension=".bica", filetypes=[("Bicala files", "*.bica"), ("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return False
        current_file["path"] = path
        save_file()
        set_title(path)
        return True

    def open_example_file():
        path = os.path.join(os.path.dirname(__file__), "examples", "test.bica")
        if not os.path.exists(path):
            append_output(f"Example file not found: {path}\n")
            return
        load_file(path)

    def new_file():
        editor.delete("1.0", tk.END)
        current_file["path"] = None
        set_title(None)
        update_line_numbers(force=True)
        apply_syntax_highlighting()
        schedule_update()
        append_output("New file.\n")

    def run_current():
        clear_error_highlights()
        
        # Clear any pending input state
        input_pending["active"] = False
        input_line_start[0] = None
        
        # Clear output panel
        output.configure(state=tk.NORMAL)
        output.delete("1.0", tk.END)
        output.configure(state=tk.DISABLED)
        
        code = editor.get("1.0", tk.END)
        append_output("Running...\n", 'info')
        
        # Always run in background thread
        def run_in_thread():
            # Update status to Launching
            app.after(0, lambda: set_status("Launching"))
            
            buffer = io.StringIO()
            error_lines = set()
            try:
                # Update status to Running
                app.after(0, lambda: set_status("Running"))
                
                with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                    run_code_text(code)
                result = buffer.getvalue().strip()
                
                # Update status to Completed on success
                app.after(0, lambda: set_status("Completed"))
            except BicalaError as err:
                source_lines = code.splitlines()
                result = format_error(err, source_lines, context=1)
                if err.line:
                    error_lines.add(err.line)
                
                # Update status to Failed, Critical on error
                app.after(0, lambda: set_status("Failed", "Critical"))
            except Exception:
                result = traceback.format_exc().rstrip()
                total_lines = int(editor.index("end-1c").split(".")[0])
                for m in re.finditer(r'File "([^"]+)", line (\d+)', result):
                    try:
                        ln = int(m.group(2))
                    except Exception:
                        continue
                    if 1 <= ln <= total_lines:
                        error_lines.add(ln)
                if not error_lines:
                    try:
                        error_lines.add(int(editor.index(tk.INSERT).split('.')[0]))
                    except Exception:
                        pass
                
                # Update status to Failed, Critical on exception
                app.after(0, lambda: set_status("Failed", "Critical"))
            
            app.after(0, lambda: update_output(result, error_lines))
        
        def update_output(result, error_lines):
            output.configure(state=tk.NORMAL)
            output.delete("1.0", tk.END)
            output.configure(state=tk.DISABLED)
            for line in result.splitlines():
                if isinstance(result, str) and ('[ERROR]' in result or '[RUNTIME]' in result or '[FATAL]' in result):
                    append_output(line + "\n", 'error')
                elif line:
                    append_output(line + "\n", 'info')
            if not result:
                set_output("(No output)", 'success')
            if error_lines:
                highlight_error_lines(error_lines)
                append_output(f"Highlighted {len(error_lines)} error line(s).\n", 'warning')
        
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

    find_query_var = tk.StringVar()
    replace_query_var = tk.StringVar()
    replace_text_var = tk.StringVar()
    dialogs = {"find": None, "replace": None}

    def _prefill_from_selection():
        try:
            return editor.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            return ""

    def open_find_dialog():
        if dialogs["find"] and dialogs["find"].winfo_exists():
            dialogs["find"].deiconify()
            dialogs["find"].lift()
            dialogs["find"].focus_force()
            return "break"

        win = tk.Toplevel(app)
        dialogs["find"] = win
        win.title("Find")
        win.configure(bg=VS_PANEL2)
        win.resizable(False, False)
        win.transient(app)

        frame = tk.Frame(win, bg=VS_PANEL2)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        tk.Label(frame, text="Find:", bg=VS_PANEL2, fg=VS_FG).grid(row=0, column=0, sticky="w", pady=(0, 8))
        entry = tk.Entry(frame, textvariable=find_query_var, width=34, bg=VS_BG, fg=VS_FG, insertbackground=VS_FG, relief=tk.FLAT, highlightthickness=1, highlightbackground=VS_BORDER)
        entry.grid(row=0, column=1, sticky="we", pady=(0, 8))

        btns = tk.Frame(frame, bg=VS_PANEL2)
        btns.grid(row=1, column=0, columnspan=2, sticky="e")
        ttk.Button(btns, text="Find Prev", command=lambda: do_find(find_query_var.get(), backwards=True)).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btns, text="Find Next", command=lambda: do_find(find_query_var.get(), backwards=False)).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btns, text="Close", command=win.destroy).pack(side=tk.LEFT)

        frame.columnconfigure(1, weight=1)

        preset = _prefill_from_selection()
        if preset:
            find_query_var.set(preset)
        entry.focus_set()
        entry.selection_range(0, tk.END)

        win.bind("<Return>", lambda e: do_find(find_query_var.get(), backwards=False))
        win.bind("<Escape>", lambda e: win.destroy())
        return "break"

    def open_replace_dialog():
        if dialogs["replace"] and dialogs["replace"].winfo_exists():
            dialogs["replace"].deiconify()
            dialogs["replace"].lift()
            dialogs["replace"].focus_force()
            return "break"

        win = tk.Toplevel(app)
        dialogs["replace"] = win
        win.title("Replace")
        win.configure(bg=VS_PANEL2)
        win.resizable(False, False)
        win.transient(app)

        frame = tk.Frame(win, bg=VS_PANEL2)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        tk.Label(frame, text="Find:", bg=VS_PANEL2, fg=VS_FG).grid(row=0, column=0, sticky="w", pady=(0, 8))
        find_entry = tk.Entry(frame, textvariable=replace_query_var, width=34, bg=VS_BG, fg=VS_FG, insertbackground=VS_FG, relief=tk.FLAT, highlightthickness=1, highlightbackground=VS_BORDER)
        find_entry.grid(row=0, column=1, sticky="we", pady=(0, 8))

        tk.Label(frame, text="Replace:", bg=VS_PANEL2, fg=VS_FG).grid(row=1, column=0, sticky="w", pady=(0, 8))
        repl_entry = tk.Entry(frame, textvariable=replace_text_var, width=34, bg=VS_BG, fg=VS_FG, insertbackground=VS_FG, relief=tk.FLAT, highlightthickness=1, highlightbackground=VS_BORDER)
        repl_entry.grid(row=1, column=1, sticky="we", pady=(0, 8))

        btns = tk.Frame(frame, bg=VS_PANEL2)
        btns.grid(row=2, column=0, columnspan=2, sticky="e")

        def replace_all_clicked():
            n = do_replace_all(replace_query_var.get(), replace_text_var.get())
            append_output(f"Replaced {n} occurrence(s).\n", "info")

        ttk.Button(btns, text="Find Next", command=lambda: do_find(replace_query_var.get(), backwards=False)).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btns, text="Replace", command=lambda: do_replace(replace_query_var.get(), replace_text_var.get())).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btns, text="Replace All", command=replace_all_clicked).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btns, text="Close", command=win.destroy).pack(side=tk.LEFT)

        frame.columnconfigure(1, weight=1)

        preset = _prefill_from_selection()
        if preset:
            replace_query_var.set(preset)
        find_entry.focus_set()
        find_entry.selection_range(0, tk.END)

        win.bind("<Return>", lambda e: do_find(replace_query_var.get(), backwards=False))
        win.bind("<Escape>", lambda e: win.destroy())
        return "break"

    def edit_undo(event=None):
        try:
            editor.edit_undo()
        except tk.TclError:
            pass
        return "break"

    def edit_redo(event=None):
        try:
            editor.edit_redo()
        except tk.TclError:
            pass
        return "break"

    def edit_cut(event=None):
        editor.event_generate("<<Cut>>")
        return "break"

    def edit_copy(event=None):
        editor.event_generate("<<Copy>>")
        return "break"

    def output_copy(event=None):
        output.event_generate("<<Copy>>")
        return "break"

    def edit_paste(event=None):
        editor.event_generate("<<Paste>>")
        return "break"

    def edit_delete(event=None):
        try:
            start = editor.index("sel.first")
            end = editor.index("sel.last")
            editor.delete(start, end)
        except tk.TclError:
            editor.delete(tk.INSERT, f"{tk.INSERT}+1c")
        return "break"

    def edit_select_all(event=None):
        editor.tag_add(tk.SEL, "1.0", "end-1c")
        editor.mark_set(tk.INSERT, "1.0")
        editor.see(tk.INSERT)
        editor.focus_set()
        return "break"

    edit_menu.delete(0, tk.END)
    edit_menu.add_command(label="Undo", command=edit_undo, accelerator="Ctrl+Z")
    edit_menu.add_command(label="Redo", command=edit_redo, accelerator="Ctrl+Y")
    edit_menu.add_separator()
    edit_menu.add_command(label="Cut", command=edit_cut, accelerator="Ctrl+X")
    edit_menu.add_command(label="Copy", command=edit_copy, accelerator="Ctrl+C")
    edit_menu.add_command(label="Paste", command=edit_paste)
    edit_menu.add_command(label="Delete", command=edit_delete, accelerator="Del")
    edit_menu.add_separator()
    edit_menu.add_command(label="Select All", command=edit_select_all, accelerator="Ctrl+A")
    edit_menu.add_separator()
    edit_menu.add_command(label="Find", command=open_find_dialog, accelerator="Ctrl+F")
    edit_menu.add_command(label="Replace", command=open_replace_dialog, accelerator="Ctrl+H")

    app.bind('<Control-s>', lambda event: (save_file(), 'break'))
    app.bind('<Control-Shift-S>', lambda event: (save_file_as(), 'break'))

    app.bind('<Control-r>', lambda event: (run_current(), 'break'))

    app.bind('<Control-n>', lambda event: (new_file(), 'break'))

    app.bind('<Control-o>', lambda event: (open_file(), 'break'))
    app.bind('<Control-Shift-O>', lambda event: (open_folder(), 'break'))

    app.bind('<Control-f>', lambda event: open_find_dialog())
    app.bind('<Control-h>', lambda event: open_replace_dialog())

    app.bind('<Control-z>', edit_undo)
    app.bind('<Control-y>', edit_redo)

    app.bind('<Control-x>', edit_cut)
    app.bind('<Control-c>', edit_copy)
    app.bind('<Control-a>', edit_select_all)

    # Bind Ctrl+C to output widget for copy functionality (widget-level has priority over app-level)
    output.bind('<Control-c>', output_copy)

    # Bind Ctrl+V to editor widget to prevent duplicate paste (remove global binding)
    editor.bind('<Control-v>', edit_paste)

    # VIEW

    chord('<Control-b>', '<e>', toggle_explorer)
    chord('<Control-b>', '<j>', toggle_panel)
    chord('<Control-b>', '<s>', toggle_status)
    chord('<Control-b>', '<l>', toggle_line_numbers)

    if initial_file:
        try:
            load_file(initial_file)
            project_root["path"] = os.path.dirname(initial_file)
            if auto_run:
                run_current()
        except Exception:
            pass

    if project_root["path"]:
        refresh_explorer(project_root["path"])
        root_items = explorer_tree.get_children("")
        if root_items:
            populate_dir(root_items[0])
    else:
        refresh_explorer(None)
    set_title(current_file["path"])

    update_line_numbers(force=True)
    apply_syntax_highlighting()
    schedule_update()
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        launch_ide()
    else:
        target = sys.argv[1]
        ext = target.lower().split('.')[-1] if '.' in target else ''
        if ext in ("bica", "txt"):
            try:
                launch_ide(target, auto_run=True)
            except tk.TclError:
                run_file(target)
        else:
            run_file(target)
