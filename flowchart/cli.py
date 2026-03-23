import sys
from pathlib import Path
from typing import List, Optional

import argparse
import os

from flowchart.pdf_converter import pdf_to_images
from flowchart.preprocess import preprocess, mask_shapes
from flowchart.shapes import detect_shapes
from flowchart.ocr import extract_text
from flowchart.lines import detect_edges_and_arrows
from flowchart.graph_builder import build_graph
from flowchart.exporter import export_graph, export_graph_json, export_rag_markdown


def process_pdf(
    pdf_path: str,
    out_path: str = "flowchart.mmd",
    poppler_path: Optional[str] = None,
    *,
    emit_rag_text: bool = True,
    rag_out: Optional[str] = None,
    emit_json: bool = False,
    json_out: Optional[str] = None,
) -> None:
    from flowchart.pdf_converter import resolve_poppler_path

    try:
        resolved = resolve_poppler_path(poppler_path)
    except RuntimeError as e:
        print(str(e))
        raise

    if resolved:
        print(f"Using poppler binaries from: {resolved}")
    else:
        print("Using poppler from system PATH")

    images = pdf_to_images(pdf_path, poppler_path=resolved)

    all_nodes: List = []
    all_edges: List = []

    node_offset = 0

    for i, img_path in enumerate(images):
        print(f"Processing page {i + 1}...")
        img, binary = preprocess(img_path)

        nodes = detect_shapes(binary)
        nodes = extract_text(img, nodes)
        masked_binary = mask_shapes(binary, nodes, padding=5)
        edges = detect_edges_and_arrows(
            masked_binary,
            nodes,
            debug_path=f"debug_edges_{i}.png",
        )

        for e in edges:
            all_edges.append(
                {
                    "src": e["src"] + node_offset,
                    "dst": e["dst"] + node_offset,
                }
            )

        all_nodes.extend(nodes)
        node_offset += len(nodes)

    G = build_graph(all_nodes, all_edges)
    export_graph(G, path=out_path)

    out_p = Path(out_path)
    if emit_rag_text:
        rag_path = Path(rag_out) if rag_out else out_p.with_name(out_p.stem + "_rag.md")
        export_rag_markdown(G, str(rag_path), source_hint=pdf_path)
        print(f"Exported RAG layer: {rag_path}")

    if emit_json:
        json_path = Path(json_out) if json_out else out_p.with_name(out_p.stem + "_graph.json")
        export_graph_json(G, str(json_path))
        print(f"Exported graph JSON: {json_path}")


def main(argv: List[str]):
    parser = argparse.ArgumentParser(description="Extract flowchart graph from PDF")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("-o", "--out", default="flowchart.mmd", help="Output Mermaid file")
    parser.add_argument("--poppler-path", default=None, help="(Windows) path to poppler/bin folder")
    parser.add_argument(
        "--no-rag-text",
        action="store_true",
        help="Do not write the companion *_rag.md file for RAG ingestion",
    )
    parser.add_argument(
        "--rag-out",
        default=None,
        help="Path for RAG markdown (default: same directory as -o, <stem>_rag.md)",
    )
    parser.add_argument(
        "--json",
        dest="emit_json",
        action="store_true",
        help="Also write structured graph JSON (<stem>_graph.json by default)",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Path for graph JSON (used with --json)",
    )

    args = parser.parse_args(argv[1:])

    poppler_path = args.poppler_path or os.getenv("POPPLER_PATH")

    process_pdf(
        args.pdf,
        args.out,
        poppler_path,
        emit_rag_text=not args.no_rag_text,
        rag_out=args.rag_out,
        emit_json=args.emit_json,
        json_out=args.json_out,
    )
    print(f"Exported: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
