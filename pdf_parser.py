import fitz


def extract_characters(pdf_path):
    doc = fitz.open(pdf_path)
    characters = []

    for page_index, page in enumerate(doc):
        raw = page.get_text("rawdict")

        for block in raw["blocks"]:
            if block["type"] != 0:
                continue

            for line in block["lines"]:
                line_y = line["bbox"][1]  # top Y of line

                for span in line["spans"]:
                    for ch in span["chars"]:
                        if not ch["c"].strip():
                            continue

                        characters.append({
                            "page": page_index,
                            "char": ch["c"],
                            "rect": fitz.Rect(ch["bbox"]),
                            "line_y": line_y
                        })

    return characters
