import fitz  # PyMuPDF

doc = fitz.open("sample.pdf")

paragraphs = []

MERGE_Y_THRESHOLD = 10  # pixels

merged = []

for p in sorted(paragraphs, key=lambda x: (x["page"], x["rect"].y0)):
    if not merged:
        merged.append(p)
        continue

    last = merged[-1]

    same_page = p["page"] == last["page"]
    close_vertically = abs(p["rect"].y0 - last["rect"].y1) < MERGE_Y_THRESHOLD
    same_indent = abs(p["rect"].x0 - last["rect"].x0) < 15

    if same_page and close_vertically and same_indent:
        last["rect"] |= p["rect"]   # union of rectangles
        last["text"] += " " + p["text"]
    else:
        merged.append(p)

paragraphs = merged


for page_index, page in enumerate(doc):
    blocks = page.get_text("blocks")

    for b in blocks:
        x0, y0, x1, y1, text, block_no, block_type = b

        if block_type != 0:
            continue

        clean_text = text.strip()
        if not clean_text:
            continue

        paragraphs.append({
            "page": page_index,
            "rect": fitz.Rect(x0, y0, x1, y1),
            "text": clean_text
        })
