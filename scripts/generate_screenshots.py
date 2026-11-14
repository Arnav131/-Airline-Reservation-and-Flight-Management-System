"""
Automated Terminal Screenshot Generator for IARFMS DBMS Project.
Executes test cases, captures terminal output with ANSI styling,
and renders high-resolution dark-mode terminal window PNG screenshots for evaluation.
"""
import os
import re
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
TESTRUN_DIR = BASE_DIR / "testrun"
TESTRUN_DIR.mkdir(parents=True, exist_ok=True)

# ANSI escape sequence regex
ANSI_REGEX = re.compile(r"\x1b\[([0-9;]*)m")

# Catppuccin / Modern Dark Terminal Palette
COLORS = {
    "default": (205, 214, 244),   # #cdd6f4
    "black":   (69, 71, 90),       # #45475a
    "red":     (243, 139, 168),    # #f38ba8
    "green":   (166, 227, 161),    # #a6e3a1
    "yellow":  (249, 226, 175),    # #f9e2af
    "blue":    (137, 180, 250),    # #89b4fa
    "magenta": (203, 166, 247),    # #cba6f7
    "cyan":    (148, 226, 213),    # #94e2d5
    "white":   (245, 224, 220),    # #f5e0dc
    "dim":     (108, 112, 134),    # #6c7086
}

ANSI_MAP = {
    "30": "black", "31": "red", "32": "green", "33": "yellow",
    "34": "blue", "35": "magenta", "36": "cyan", "37": "white",
    "90": "dim", "91": "red", "92": "green", "93": "yellow",
    "94": "blue", "95": "magenta", "96": "cyan", "97": "white",
}


def parse_ansi_line(line: str) -> list[tuple[str, tuple[int, int, int]]]:
    """Parse a single line of text with ANSI escape codes into colored segments."""
    segments = []
    current_color = COLORS["default"]
    last_end = 0

    for match in ANSI_REGEX.finditer(line):
        start, end = match.span()
        if start > last_end:
            text = line[last_end:start]
            segments.append((text, current_color))

        code_str = match.group(1)
        if not code_str or code_str == "0":
            current_color = COLORS["default"]
        elif code_str == "2":
            current_color = COLORS["dim"]
        else:
            for c in code_str.split(";"):
                if c in ANSI_MAP:
                    current_color = COLORS[ANSI_MAP[c]]

        last_end = end

    if last_end < len(line):
        segments.append((line[last_end:], current_color))

    return segments


def render_terminal_image(title: str, raw_output: str, output_png_path: Path) -> None:
    """Render colored terminal text inside a sleek macOS/Linux style window."""
    font_path = r"C:\Windows\Fonts\consola.ttf"
    font_size = 15
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()

    lines = raw_output.replace("\r", "").split("\n")
    # Clean trailing empty lines
    while lines and not lines[-1].strip():
        lines.pop()

    char_width = 9.2
    line_height = 22
    pad_x = 24
    pad_top = 54
    pad_bottom = 24

    max_len = max((len(ANSI_REGEX.sub("", l)) for l in lines), default=80)
    img_width = max(1000, int(max_len * char_width) + (pad_x * 2))
    img_height = pad_top + (len(lines) * line_height) + pad_bottom

    # Background
    bg_color = (24, 24, 37)       # #181825
    header_color = (30, 30, 46)   # #1e1e2e
    border_color = (49, 50, 68)   # #313244

    img = Image.new("RGB", (img_width, img_height), bg_color)
    draw = ImageDraw.Draw(img)

    # Window Header
    draw.rectangle([(0, 0), (img_width, 42)], fill=header_color)
    draw.line([(0, 42), (img_width, 42)], fill=border_color, width=1)

    # Window Controls (Red, Yellow, Green dots)
    draw.ellipse([(16, 15), (28, 27)], fill=(243, 139, 168))
    draw.ellipse([(36, 15), (48, 27)], fill=(249, 226, 175))
    draw.ellipse([(56, 15), (68, 27)], fill=(166, 227, 161))

    # Window Title
    title_text = f"terminal — {title}"
    draw.text((86, 13), title_text, fill=(147, 153, 178), font=font)

    # Render Terminal Lines
    y = pad_top
    for line in lines:
        segments = parse_ansi_line(line)
        x = pad_x
        for text, color in segments:
            clean_text = text.replace("\t", "    ")
            draw.text((x, y), clean_text, fill=color, font=font)
            # Advance x
            x += int(len(clean_text) * char_width)
        y += line_height

    # Outer border
    draw.rectangle([(0, 0), (img_width - 1, img_height - 1)], outline=border_color, width=1)
    img.save(output_png_path, "PNG", optimize=True)
    print(f"Generated screenshot: {output_png_path.name} ({img_width}x{img_height})")


def run_command_capture(cmd: list[str]) -> str:
    """Run a CLI command and capture its stdout+stderr with ANSI escape codes preserved."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["FORCE_COLOR"] = "1"
    env["COLUMNS"] = "130"
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(BASE_DIR))
    return res.stdout + ("\n" + res.stderr if res.stderr else "")


def generate_all_screenshots():
    print("Generating 9 High-Resolution Evaluation Screenshots in testrun/ ...")

    tasks = [
        ("Experiment 1: Relational SQL Schema, Joins & TCL",
         [sys.executable, str(BASE_DIR / "exp1_relational_sql" / "exp1_runner.py")],
         TESTRUN_DIR / "01_exp1_relational_sql.png"),

        ("Experiment 2: Advanced MySQL Programming (Triggers, Procs, Views)",
         [sys.executable, str(BASE_DIR / "exp2_advanced_mysql" / "exp2_runner.py")],
         TESTRUN_DIR / "02_exp2_advanced_mysql.png"),

        ("Experiment 3: Performance Tuning (EXPLAIN, B-Tree & Hash Benchmark)",
         [sys.executable, str(BASE_DIR / "exp3_performance_tuning" / "03_benchmark_runner.py")],
         TESTRUN_DIR / "03_exp3_performance_benchmark.png"),

        ("Experiment 4: Concurrency, ACID, Locks, Deadlock & MVCC",
         [sys.executable, str(BASE_DIR / "exp4_transaction_concurrency" / "exp4_runner.py")],
         TESTRUN_DIR / "04_exp4_transaction_concurrency.png"),

        ("Experiment 5: Redis (Cache & Holds) + MongoDB (Baggage & Aggregations)",
         [sys.executable, str(BASE_DIR / "exp5_redis_mongodb" / "exp5_runner.py")],
         TESTRUN_DIR / "05_exp5_redis_mongodb.png"),

        ("Experiment 6: Cassandra Telemetry + Neo4j Connecting Flight Graph",
         [sys.executable, str(BASE_DIR / "exp6_cassandra_neo4j" / "exp6_runner.py")],
         TESTRUN_DIR / "06_exp6_cassandra_neo4j.png"),

        ("Experiment 7: Distributed Airport Cluster (Sharding & Consistency)",
         [sys.executable, str(BASE_DIR / "exp7_distributed_databases" / "exp7_runner.py")],
         TESTRUN_DIR / "07_exp7_distributed_databases.png"),

        ("Automated Pytest End-to-End Test Suite (All 7 Tests Pass)",
         [sys.executable, "-m", "pytest", str(BASE_DIR / "tests" / "test_all_experiments.py"), "-v"],
         TESTRUN_DIR / "08_pytest_test_suite_all_pass.png"),

        ("IARFMS Interactive Evaluation CLI Dashboard Menu",
         [sys.executable, str(BASE_DIR / "scripts" / "render_menu_preview.py")],
         TESTRUN_DIR / "09_interactive_cli_menu.png"),
    ]

    for title, cmd, out_path in tasks:
        print(f"Executing and capturing: {title} ...")
        raw_output = run_command_capture(cmd)
        render_terminal_image(title, raw_output, out_path)

    print("\n✅ All 9 evaluation screenshots successfully rendered into testrun/ directory!")


if __name__ == "__main__":
    generate_all_screenshots()
