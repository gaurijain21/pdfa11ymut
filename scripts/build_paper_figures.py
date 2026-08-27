from pathlib import Path


OUT = Path("outputs/figures")
OUT.mkdir(parents=True, exist_ok=True)


def svg_header(width, height):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">'''


def write(path, content):
    path.write_text(content, encoding="utf-8")


def pipeline():
    width, height = 980, 260
    boxes = [
        ("Golden PDFs", "5 validator-clean baseline PDFs"),
        ("Mutation", "5 structure-level operators"),
        ("Verification", "Parseable, page-stable, mutation verified"),
        ("Validators", "PAC, Acrobat, veraPDF"),
        ("Matrix", "Detected / Missed / N/A"),
    ]
    x0, y, bw, bh, gap = 35, 75, 160, 78, 35
    parts = [svg_header(width, height)]
    parts.append("<title>PDFa11yMut experimental pipeline</title>")
    parts.append("<desc>Pipeline from golden PDFs through mutation, verification, validator evaluation, and final matrix.</desc>")
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append('<text x="35" y="36" font-family="Arial, sans-serif" font-size="22" font-weight="700" fill="#1f2937">Figure 1. PDFa11yMut experimental pipeline</text>')
    for i, (title, sub) in enumerate(boxes):
        x = x0 + i * (bw + gap)
        parts.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="8" fill="#eef4fb" stroke="#2f5d7c" stroke-width="1.5"/>')
        parts.append(f'<text x="{x + bw/2}" y="{y + 28}" font-family="Arial, sans-serif" font-size="16" font-weight="700" text-anchor="middle" fill="#17324d">{title}</text>')
        words = sub.split()
        line = ""
        lines = []
        for word in words:
            trial = (line + " " + word).strip()
            if len(trial) > 22:
                lines.append(line)
                line = word
            else:
                line = trial
        if line:
            lines.append(line)
        for j, text in enumerate(lines[:2]):
            parts.append(f'<text x="{x + bw/2}" y="{y + 51 + j*17}" font-family="Arial, sans-serif" font-size="12" text-anchor="middle" fill="#374151">{text}</text>')
        if i < len(boxes) - 1:
            ax = x + bw
            nx = x + bw + gap
            parts.append(f'<line x1="{ax + 7}" y1="{y + bh/2}" x2="{nx - 12}" y2="{y + bh/2}" stroke="#6b7280" stroke-width="2"/>')
            parts.append(f'<polygon points="{nx - 12},{y + bh/2 - 6} {nx},{y + bh/2} {nx - 12},{y + bh/2 + 6}" fill="#6b7280"/>')
    parts.append('<text x="35" y="205" font-family="Arial, sans-serif" font-size="13" fill="#4b5563">Detection is coded only after independent mutation verification; N/A cases are excluded from detection-rate denominators.</text>')
    parts.append("</svg>")
    write(OUT / "figure1_pipeline.svg", "\n".join(parts))


def overall_rates():
    width, height = 720, 420
    data = [("PAC", 17.4, 4, 23), ("Acrobat", 21.7, 5, 23), ("veraPDF", 21.7, 5, 23)]
    left, top, chart_w, chart_h = 92, 72, 560, 245
    max_v = 25
    parts = [svg_header(width, height)]
    parts.append("<title>Overall validator mutation-detection rates</title>")
    parts.append("<desc>Bar chart showing PAC at 17.4 percent and Acrobat and veraPDF at 21.7 percent.</desc>")
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append('<text x="32" y="36" font-family="Arial, sans-serif" font-size="22" font-weight="700" fill="#1f2937">Figure 2. Overall mutation-detection rates</text>')
    for tick in range(0, max_v + 1, 5):
        y = top + chart_h - tick / max_v * chart_h
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+chart_w}" y2="{y:.1f}" stroke="#e5e7eb" stroke-width="1"/>')
        parts.append(f'<text x="{left-10}" y="{y+4:.1f}" font-family="Arial, sans-serif" font-size="12" text-anchor="end" fill="#4b5563">{tick}%</text>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+chart_h}" stroke="#374151" stroke-width="1.2"/>')
    parts.append(f'<line x1="{left}" y1="{top+chart_h}" x2="{left+chart_w}" y2="{top+chart_h}" stroke="#374151" stroke-width="1.2"/>')
    bar_w = 95
    gap = 90
    colors = ["#4477aa", "#228833", "#66ccee"]
    for i, (name, rate, detected, total) in enumerate(data):
        x = left + 70 + i * (bar_w + gap)
        h = rate / max_v * chart_h
        y = top + chart_h - h
        parts.append(f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" fill="{colors[i]}"/>')
        parts.append(f'<text x="{x+bar_w/2}" y="{y-9:.1f}" font-family="Arial, sans-serif" font-size="14" font-weight="700" text-anchor="middle" fill="#1f2937">{rate:.1f}%</text>')
        parts.append(f'<text x="{x+bar_w/2}" y="{top+chart_h+24}" font-family="Arial, sans-serif" font-size="14" text-anchor="middle" fill="#1f2937">{name}</text>')
        parts.append(f'<text x="{x+bar_w/2}" y="{top+chart_h+43}" font-family="Arial, sans-serif" font-size="12" text-anchor="middle" fill="#4b5563">{detected}/{total} detected</text>')
    parts.append(f'<text x="28" y="{top+chart_h/2}" transform="rotate(-90 28 {top+chart_h/2})" font-family="Arial, sans-serif" font-size="13" text-anchor="middle" fill="#374151">Detection rate</text>')
    parts.append('<text x="32" y="390" font-family="Arial, sans-serif" font-size="12" fill="#4b5563">Rates are mutation-detection rates for 23 generated and independently verified mutants, not general accessibility accuracy scores.</text>')
    parts.append("</svg>")
    write(OUT / "figure2_overall_detection_rates.svg", "\n".join(parts))


def per_operator():
    width, height = 920, 520
    operators = [
        ("M01", "Reading order", [0, 0, 0], "5"),
        ("M02", "Omitted structure", [0, 0, 0], "5"),
        ("M03", "Heading level", [100, 100, 100], "4"),
        ("M04", "MC association", [0, 20, 20], "5"),
        ("M05", "MCID order", [0, 0, 0], "4"),
    ]
    validators = ["PAC", "Acrobat", "veraPDF"]
    colors = ["#4477aa", "#228833", "#66ccee"]
    left, top, chart_w, chart_h = 90, 70, 760, 315
    max_v = 100
    group_w = chart_w / len(operators)
    bar_w = 26
    parts = [svg_header(width, height)]
    parts.append("<title>Per-operator mutation-detection rates</title>")
    parts.append("<desc>Grouped bar chart showing 100 percent detection for M03, 20 percent detection by Acrobat and veraPDF for M04, and zero percent for other operators.</desc>")
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append('<text x="32" y="36" font-family="Arial, sans-serif" font-size="22" font-weight="700" fill="#1f2937">Figure 3. Detection by mutation operator</text>')
    for tick in range(0, 101, 20):
        y = top + chart_h - tick / max_v * chart_h
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+chart_w}" y2="{y:.1f}" stroke="#e5e7eb" stroke-width="1"/>')
        parts.append(f'<text x="{left-10}" y="{y+4:.1f}" font-family="Arial, sans-serif" font-size="12" text-anchor="end" fill="#4b5563">{tick}%</text>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+chart_h}" stroke="#374151" stroke-width="1.2"/>')
    parts.append(f'<line x1="{left}" y1="{top+chart_h}" x2="{left+chart_w}" y2="{top+chart_h}" stroke="#374151" stroke-width="1.2"/>')
    for i, (op, label, vals, denom) in enumerate(operators):
        center = left + group_w * i + group_w / 2
        for j, val in enumerate(vals):
            x = center - (bar_w * 1.5) + j * (bar_w + 5)
            h = val / max_v * chart_h
            y = top + chart_h - h
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" fill="{colors[j]}"/>')
            if val > 0:
                parts.append(f'<text x="{x+bar_w/2:.1f}" y="{y-7:.1f}" font-family="Arial, sans-serif" font-size="11" text-anchor="middle" fill="#1f2937">{val}%</text>')
        parts.append(f'<text x="{center:.1f}" y="{top+chart_h+24}" font-family="Arial, sans-serif" font-size="13" text-anchor="middle" font-weight="700" fill="#1f2937">{op}</text>')
        parts.append(f'<text x="{center:.1f}" y="{top+chart_h+42}" font-family="Arial, sans-serif" font-size="11" text-anchor="middle" fill="#4b5563">{label}</text>')
        parts.append(f'<text x="{center:.1f}" y="{top+chart_h+58}" font-family="Arial, sans-serif" font-size="11" text-anchor="middle" fill="#4b5563">n={denom}</text>')
    legend_x = 590
    for j, name in enumerate(validators):
        x = legend_x + j * 100
        parts.append(f'<rect x="{x}" y="24" width="13" height="13" fill="{colors[j]}"/>')
        parts.append(f'<text x="{x+19}" y="35" font-family="Arial, sans-serif" font-size="12" fill="#374151">{name}</text>')
    parts.append(f'<text x="28" y="{top+chart_h/2}" transform="rotate(-90 28 {top+chart_h/2})" font-family="Arial, sans-serif" font-size="13" text-anchor="middle" fill="#374151">Detection rate</text>')
    parts.append('<text x="32" y="490" font-family="Arial, sans-serif" font-size="12" fill="#4b5563">Detection is concentrated in M03. Acrobat and veraPDF detect one M04 mutant, G02-M04; PAC detects no M04 mutants.</text>')
    parts.append("</svg>")
    write(OUT / "figure3_per_operator_detection.svg", "\n".join(parts))


if __name__ == "__main__":
    pipeline()
    overall_rates()
    per_operator()
    for p in sorted(OUT.glob("*.svg")):
        print(p)
