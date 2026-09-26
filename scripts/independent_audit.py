"""Run a conservative PyMuPDF/MuPDF audit over frozen mutant pairs.

The mutation generator and primary verifier use pypdf. This audit uses MuPDF
for independent page/render checks and a deliberately narrow set of raw-COS
delta checks. Unsupported semantic deltas are marked UNVERIFIABLE, never
implicitly passed. It never rewrites a PDF or canonical mutant manifest.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def stream_hashes(doc: pymupdf.Document) -> list[str]:
    values: list[str] = []
    for page in doc:
        parts = []
        for xref in page.get_contents() or []:
            parts.append(doc.xref_stream_raw(xref) or b"")
        values.append(hashlib.sha256(b"".join(parts)).hexdigest())
    return values


def page_invariants(golden: pymupdf.Document, mutant: pymupdf.Document) -> dict:
    pages_equal = golden.page_count == mutant.page_count
    boxes_equal = pages_equal and all(list(golden[i].rect) == list(mutant[i].rect) for i in range(golden.page_count))
    content_equal = pages_equal and stream_hashes(golden) == stream_hashes(mutant)
    def annotation_signature(page):
        values = []
        for annotation in page.annots() or []:
            values.append((annotation.type, tuple(round(float(v), 4) for v in annotation.rect), tuple(sorted((annotation.info or {}).items()))))
        return values
    def image_signature(page):
        # PyMuPDF exposes xrefs for the image, soft mask, and referring page;
        # those object numbers are not stable after a pypdf serialization.
        # Keep only the image's intrinsic description.
        return [(item[2], item[3], item[4], item[5], item[6], item[7], item[8]) for item in page.get_images(full=True)]
    annotations_equal = pages_equal and all(annotation_signature(golden[i]) == annotation_signature(mutant[i]) for i in range(golden.page_count))
    images_equal = pages_equal and all(image_signature(golden[i]) == image_signature(mutant[i]) for i in range(golden.page_count))
    return {"page_count_equal": pages_equal, "page_boxes_equal": boxes_equal, "content_stream_hashes_equal": content_equal, "annotation_xrefs_equal": annotations_equal, "page_images_equal": images_equal}


def render_equal(golden: pymupdf.Document, mutant: pymupdf.Document, dpi: int) -> dict:
    scale = dpi / 72.0
    matrix = pymupdf.Matrix(scale, scale)
    pages = []
    equal = golden.page_count == mutant.page_count
    if equal:
        for index in range(golden.page_count):
            g = golden[index].get_pixmap(matrix=matrix, alpha=False)
            m = mutant[index].get_pixmap(matrix=matrix, alpha=False)
            same = (g.width, g.height, g.samples) == (m.width, m.height, m.samples)
            pages.append({"page": index + 1, "equal": same, "golden_dimensions": [g.width, g.height], "mutant_dimensions": [m.width, m.height]})
            equal = equal and same
    return {"status": "PASS" if equal else "FAIL", "renderer": "MuPDF", "dpi": dpi, "pages": pages}


def raw_role_inventory(doc: pymupdf.Document) -> dict[str, int]:
    counts: dict[str, int] = {}
    for xref in range(1, doc.xref_length()):
        role_type = doc.xref_get_key(xref, "S")
        # /Type is optional on StructElem dictionaries. /S plus the required
        # parent entry /P is a better discriminator from action/group dicts.
        parent_type = doc.xref_get_key(xref, "P")[0]
        if role_type[0] == "name" and parent_type != "null":
            role = role_type[1]
            counts[role] = counts.get(role, 0) + 1
    return counts


def target_xrefs(delta: dict) -> list[int]:
    value = str(delta.get("target_object", ""))
    return [int(match.group(1)) for match in re.finditer(r"(?:^|;)(\d+):\d+", value)]


def raw_k_items(doc: pymupdf.Document, xref: int, key: str) -> list[tuple[str, int]]:
    """Return ordered indirect references and bare integers in a raw COS value."""
    kind, value = doc.xref_get_key(xref, key)
    if kind == "int":
        return [("int", int(value))]
    if kind not in {"xref", "array"}:
        return []
    items: list[tuple[str, int]] = []
    consumed: list[tuple[int, int]] = []
    for match in re.finditer(r"(\d+)\s+\d+\s+R", value):
        items.append(("xref", int(match.group(1))))
        consumed.append(match.span())
    for match in re.finditer(r"(?<![\w.])-?\d+(?![\w.])", value):
        if any(start <= match.start() < end for start, end in consumed):
            continue
        items.append(("int", int(match.group(0))))
    # The regex passes above are separate; restore COS order.
    positions = []
    for match in re.finditer(r"(\d+)\s+\d+\s+R", value):
        positions.append((match.start(), ("xref", int(match.group(1)))))
    for match in re.finditer(r"(?<![\w.])-?\d+(?![\w.])", value):
        if any(start <= match.start() < end for start, end in consumed):
            continue
        positions.append((match.start(), ("int", int(match.group(0)))))
    return [item for _, item in sorted(positions)]


def raw_xrefs(doc: pymupdf.Document, xref: int, key: str) -> list[int]:
    """Return indirect references appearing in a raw COS value."""
    return [value for kind, value in raw_k_items(doc, xref, key) if kind == "xref"]


def raw_role(doc: pymupdf.Document, xref: int) -> str:
    kind, value = doc.xref_get_key(xref, "S")
    return value if kind == "name" else ""


def direct_list_children(doc: pymupdf.Document, xref: int) -> list[int]:
    return [child for child in raw_xrefs(doc, xref, "K") if raw_role(doc, child) == "/LI"]


def list_role_sequences(doc: pymupdf.Document) -> dict[int, list[str]]:
    """Capture direct /LI role sequences for every raw /L structure element."""
    result: dict[int, list[str]] = {}
    for xref in range(1, doc.xref_length()):
        if raw_role(doc, xref) == "/L":
            result[xref] = [raw_role(doc, child) for child in raw_xrefs(doc, xref, "K")]
    return result


def struct_signature(doc: pymupdf.Document, xref: int, seen: set[int] | None = None):
    """Normalize a structure subtree without relying on object numbers."""
    seen = set() if seen is None else seen
    if xref in seen:
        return ("cycle", raw_role(doc, xref))
    seen.add(xref)
    role = raw_role(doc, xref)
    children = []
    for kind, child in raw_k_items(doc, xref, "K"):
        if kind == "int":
            children.append(("INT", child))
            continue
        child_role = raw_role(doc, child)
        if child_role:
            children.append(struct_signature(doc, child, seen.copy()))
        else:
            value_kind, value = doc.xref_get_key(child, "MCID")
            children.append(("MCID", value) if value_kind in {"int", "string"} else ("REF",))
    return (role, tuple(children))


def normalized_child_signature(doc: pymupdf.Document, item: tuple[str, int]):
    """Normalize one /K item without retaining serialized object numbers."""
    kind, value = item
    if kind == "int":
        return ("INT", value)
    child_role = raw_role(doc, value)
    if child_role:
        return struct_signature(doc, value)
    value_kind, value_value = doc.xref_get_key(value, "MCID")
    return ("MCID", value_value) if value_kind in {"int", "string"} else ("REF",)


def normalized_structure_signature(
    doc: pymupdf.Document,
    xref: int,
    k_overrides: dict[int, list[tuple[str, int]]] | None = None,
    signature_overrides: dict[int, list[tuple]] | None = None,
    seen: set[int] | None = None,
):
    """Normalize the structure tree, optionally replacing selected /K lists.

    The replacement is used only to express the independently expected result
    of an operator.  It lets this audit compare the whole structure tree across
    pypdf reserialization, where indirect-object numbers are not stable.
    """
    seen = set() if seen is None else seen
    if xref in seen:
        return ("cycle", raw_role(doc, xref))
    seen.add(xref)
    if signature_overrides and xref in signature_overrides:
        return (raw_role(doc, xref), tuple(signature_overrides[xref]))
    items = (k_overrides or {}).get(xref, raw_k_items(doc, xref, "K"))
    children = []
    for kind, value in items:
        if kind == "int":
            children.append(("INT", value))
            continue
        child_role = raw_role(doc, value)
        if child_role:
            children.append(normalized_structure_signature(doc, value, k_overrides, signature_overrides, seen.copy()))
            continue
        value_kind, value_value = doc.xref_get_key(value, "MCID")
        children.append(("MCID", value_value) if value_kind in {"int", "string"} else ("REF",))
    return (raw_role(doc, xref), tuple(children))


def raw_content_signatures(doc: pymupdf.Document, xref: int, key: str = "K") -> list[tuple]:
    """Parse top-level content items, ignoring numbers inside inline COS dictionaries."""
    kind, value = doc.xref_get_key(xref, key)
    if kind == "int":
        return [("INT", int(value))]
    if kind != "array":
        return []
    result: list[tuple] = []
    index = 0
    while index < len(value):
        if value[index].isspace():
            index += 1
            continue
        if value.startswith("<<", index):
            start = index
            depth = 0
            while index < len(value):
                if value.startswith("<<", index):
                    depth += 1
                    index += 2
                    continue
                if value.startswith(">>", index):
                    depth -= 1
                    index += 2
                    if depth == 0:
                        break
                    continue
                index += 1
            dictionary = value[start:index]
            mcid = re.search(r"/MCID\s+(-?\d+)", dictionary)
            obj_type = re.search(r"/Type\s*/(\w+)", dictionary)
            if mcid:
                result.append(("MCR", int(mcid.group(1))))
            elif obj_type:
                result.append((obj_type.group(1),))
            else:
                result.append(("DICT",))
            continue
        reference = re.match(r"(\d+)\s+\d+\s+R", value[index:])
        if reference:
            child = int(reference.group(1))
            role = raw_role(doc, child)
            if role:
                result.append(struct_signature(doc, child))
            else:
                mcid_kind, mcid_value = doc.xref_get_key(child, "MCID")
                result.append(("MCR", mcid_value) if mcid_kind in {"int", "string"} else ("REF",))
            index += reference.end()
            continue
        number = re.match(r"-?\d+", value[index:])
        if number:
            result.append(("INT", int(number.group(0))))
            index += number.end()
            continue
        index += 1
    return result


def target_path_xrefs(doc: pymupdf.Document, targets: list[int]) -> dict[int, list[int] | None]:
    return {target: struct_path(doc, target) for target in targets}


def all_list_signatures(doc: pymupdf.Document) -> dict[int, tuple]:
    return {
        xref: struct_signature(doc, xref)
        for xref in range(1, doc.xref_length())
        if raw_role(doc, xref) == "/L"
    }


def struct_tree_root(doc: pymupdf.Document) -> int | None:
    kind, value = doc.xref_get_key(doc.pdf_catalog(), "StructTreeRoot")
    if kind != "xref":
        return None
    return int(value.split()[0])


def struct_path(doc: pymupdf.Document, target: int) -> list[int] | None:
    """Return the target's child-index path from StructTreeRoot."""
    root = struct_tree_root(doc)
    if root is None:
        return None

    def walk(xref: int, path: list[int], seen: set[int]) -> list[int] | None:
        if xref == target:
            return path
        if xref in seen:
            return None
        seen = seen | {xref}
        for index, (kind, child) in enumerate(raw_k_items(doc, xref, "K")):
            if kind != "xref":
                continue
            result = walk(child, path + [index], seen)
            if result is not None:
                return result
        return None

    return walk(root, [], set())


def follow_struct_path(doc: pymupdf.Document, path: list[int] | None) -> int | None:
    """Follow a structure-tree child-index path in another serialized PDF."""
    root = struct_tree_root(doc)
    if root is None or path is None:
        return None
    current = root
    for index in path:
        items = raw_k_items(doc, current, "K")
        if index >= len(items) or items[index][0] != "xref":
            return None
        current = items[index][1]
    return current


def raw_cos_delta(golden: pymupdf.Document, mutant: pymupdf.Document, operator: str, delta: dict) -> tuple[str, dict, list[str]]:
    before = raw_role_inventory(golden)
    after = raw_role_inventory(mutant)
    observed = {"role_counts_before": before, "role_counts_after": after}
    unexpected: list[str] = []
    targets = target_xrefs(delta)
    observed["target_xrefs"] = targets

    if operator == "M08":
        root_g, root_m = golden.pdf_catalog(), mutant.pdf_catalog()
        prior, current = golden.xref_get_key(root_g, "Lang"), mutant.xref_get_key(root_m, "Lang")
        observed["catalog_lang_before"], observed["catalog_lang_after"] = prior, current
        wanted_old, wanted_new = delta.get("old_lang"), delta.get("new_lang")
        if prior[0] == "string" and prior[1] == str(wanted_old) and wanted_new is None and current[0] == "null":
            return "CONFIRMED", observed, unexpected
        return "CONTRADICTED", observed, unexpected
    if operator == "M07":
        def figures_with_alt(doc):
            return sum(
                doc.xref_get_key(xref, "S") == ("name", "/Figure")
                and doc.xref_get_key(xref, "P")[0] != "null"
                and doc.xref_get_key(xref, "Alt")[0] != "null"
                for xref in range(1, doc.xref_length())
            )
        before_alt, after_alt = figures_with_alt(golden), figures_with_alt(mutant)
        observed.update({"figure_alt_count_before": before_alt, "figure_alt_count_after": after_alt})
        return ("CONFIRMED" if after_alt == before_alt - 1 else "CONTRADICTED"), observed, unexpected
    if operator == "M09":
        def role_map_value(doc):
            root = doc.xref_get_key(doc.pdf_catalog(), "StructTreeRoot")
            if root[0] != "xref":
                return ("null", "null")
            root_xref = int(root[1].split()[0])
            role_map = doc.xref_get_key(root_xref, "RoleMap")
            if role_map[0] != "xref":
                return ("null", "null")
            map_xref = int(role_map[1].split()[0])
            return doc.xref_get_key(map_xref, str(delta.get("role_key", "")).lstrip("/"))
        prior, current = role_map_value(golden), role_map_value(mutant)
        observed["role_map_value_before"], observed["role_map_value_after"] = prior, current
        if prior == ("name", str(delta.get("old_role"))) and current == ("name", str(delta.get("new_role"))):
            return "CONFIRMED", observed, unexpected
        return ("CONTRADICTED" if prior[0] != "null" and current[0] != "null" else "UNVERIFIABLE"), observed, unexpected
    if operator == "M03":
        expected = dict(before)
        old_role, new_role = str(delta.get("old_role")), str(delta.get("new_role"))
        expected[old_role] = expected.get(old_role, 0) - 1
        expected[new_role] = expected.get(new_role, 0) + 1
        expected = {role: count for role, count in expected.items() if count}
        observed["expected_role_counts_after"] = expected
        return ("CONFIRMED" if after == expected else "CONTRADICTED"), observed, unexpected
    if operator == "M10":
        expected = dict(before)
        old_role, new_role = str(delta.get("old_role")), str(delta.get("new_role"))
        expected[old_role] = expected.get(old_role, 0) - 1
        expected[new_role] = expected.get(new_role, 0) + 1
        expected = {role: count for role, count in expected.items() if count}
        observed["expected_role_counts_after"] = expected
        return ("CONFIRMED" if after == expected else "CONTRADICTED"), observed, unexpected
    if operator in {"M01", "M02"}:
        if len(targets) != 1:
            return "UNVERIFIABLE", observed, unexpected
        target = targets[0]
        target_path = struct_path(golden, target)
        mutant_target = follow_struct_path(mutant, target_path)
        observed["target_structure_path"] = target_path
        observed["target_xref_after"] = mutant_target
        if mutant_target is None:
            return "CONTRADICTED", observed, unexpected
        before_k = raw_k_items(golden, target, "K")
        after_k = raw_k_items(mutant, mutant_target, "K")
        observed["target_role_before"] = raw_role(golden, target)
        observed["target_role_after"] = raw_role(mutant, mutant_target)
        observed["target_k_length_before"] = len(before_k)
        observed["target_k_length_after"] = len(after_k)
        observed["target_k_signature_before"] = [normalized_child_signature(golden, item) for item in before_k]
        observed["target_k_signature_after"] = [normalized_child_signature(mutant, item) for item in after_k]
        if operator == "M01":
            if len(before_k) < 2:
                return "CONTRADICTED", observed, unexpected
            expected_k = before_k[1:2] + before_k[:1] + before_k[2:]
            expected_signatures = [normalized_child_signature(golden, item) for item in expected_k]
        else:
            if not before_k:
                return "CONTRADICTED", observed, unexpected
            expected_k = before_k[1:]
            expected_signatures = [normalized_child_signature(golden, item) for item in expected_k]
        observed["expected_target_k_signature_after"] = expected_signatures
        observed["target_delta_matches"] = (
            [normalized_child_signature(mutant, item) for item in after_k] == expected_signatures
        )
        root_g, root_m = struct_tree_root(golden), struct_tree_root(mutant)
        expected_overrides = {target: expected_k}
        observed["whole_tree_expected_equals_mutant"] = (
            root_g is not None and root_m is not None
            and normalized_structure_signature(golden, root_g, expected_overrides)
            == normalized_structure_signature(mutant, root_m)
        )
        observed["reachable_structure_root_present"] = root_g is not None and root_m is not None
        if (
            raw_role(golden, target) == raw_role(mutant, mutant_target)
            and observed["target_delta_matches"]
            and observed["whole_tree_expected_equals_mutant"]
        ):
            return "CONFIRMED", observed, unexpected
        return "CONTRADICTED", observed, unexpected
    if operator in {"M04", "M05"}:
        if (operator == "M04" and len(targets) != 2) or (operator == "M05" and len(targets) != 1):
            return "UNVERIFIABLE", observed, unexpected
        paths = target_path_xrefs(golden, targets)
        mutant_targets = {target: follow_struct_path(mutant, paths[target]) for target in targets}
        observed["target_structure_paths"] = paths
        observed["target_xrefs_after"] = mutant_targets
        if any(value is None for value in mutant_targets.values()):
            return "CONTRADICTED", observed, unexpected
        if operator == "M05":
            before_content = {target: raw_content_signatures(golden, target) for target in targets}
            after_content = {target: raw_content_signatures(mutant, mutant_targets[target]) for target in targets}
            before_structure_refs = {target: [item for item in raw_k_items(golden, target, "K") if item[0] == "xref" and raw_role(golden, item[1])] for target in targets}
            if any(before_structure_refs.values()):
                return "CONTRADICTED", observed, unexpected
        else:
            before_content = {target: [normalized_child_signature(golden, item) for item in raw_k_items(golden, target, "K")] for target in targets}
            after_content = {target: [normalized_child_signature(mutant, item) for item in raw_k_items(mutant, mutant_targets[target], "K")] for target in targets}
        before = {target: raw_k_items(golden, target, "K") for target in targets}
        after = {target: raw_k_items(mutant, mutant_targets[target], "K") for target in targets}
        observed["target_roles_before"] = {str(target): raw_role(golden, target) for target in targets}
        observed["target_roles_after"] = {str(target): raw_role(mutant, mutant_targets[target]) for target in targets}
        before_sig = {str(target): before_content[target] for target in targets}
        after_sig = {str(target): after_content[target] for target in targets}
        observed["target_k_signature_before"] = before_sig
        observed["target_k_signature_after"] = after_sig
        if operator == "M04":
            expected_for_target = {targets[0]: before[targets[1]], targets[1]: before[targets[0]]}
            expected_signatures_for_target = {targets[0]: before_content[targets[1]], targets[1]: before_content[targets[0]]}
        else:
            if len(before_content[targets[0]]) < 2:
                return "CONTRADICTED", observed, unexpected
            expected_for_target = {}
            expected_signatures_for_target = {targets[0]: list(reversed(before_content[targets[0]]))}
        expected_sig = {str(target): expected_signatures_for_target[target] for target in targets}
        observed["expected_target_k_signature_after"] = expected_sig
        observed["target_delta_matches"] = all(
            after_content[target] == expected_sig[str(target)]
            for target in targets
        )
        root_g, root_m = struct_tree_root(golden), struct_tree_root(mutant)
        if operator == "M04":
            observed["whole_tree_expected_equals_mutant"] = (
                root_g is not None and root_m is not None
                and normalized_structure_signature(golden, root_g, expected_for_target)
                == normalized_structure_signature(mutant, root_m)
            )
        else:
            observed["whole_tree_expected_equals_mutant"] = (
                root_g is not None and root_m is not None
                and normalized_structure_signature(golden, root_g, signature_overrides=expected_signatures_for_target)
                == normalized_structure_signature(
                    mutant,
                    root_m,
                    signature_overrides={mutant_targets[target]: expected_signatures_for_target[target] for target in targets},
                )
            )
        if (
            all(raw_role(golden, target) == raw_role(mutant, mutant_targets[target]) for target in targets)
            and observed["target_delta_matches"]
            and observed["whole_tree_expected_equals_mutant"]
        ):
            return "CONFIRMED", observed, unexpected
        return "CONTRADICTED", observed, unexpected
    if operator == "M06":
        # Unlike the primary pypdf oracle, this route reads the serialized COS
        # with PyMuPDF. Object numbers are expected to remain stable for this
        # local transformation; if they do not, fail closed rather than
        # silently aligning the wrong list.
        if len(targets) != 1:
            return "UNVERIFIABLE", observed, unexpected
        target = targets[0]
        before_k = direct_list_children(golden, target)
        before_sigs = [struct_signature(golden, child) for child in before_k]
        expected_sigs = before_sigs[:1] + before_sigs[:1] + before_sigs[1:] if before_sigs else []
        mutant_lists = all_list_signatures(mutant)
        matching_targets = [xref for xref, signature in mutant_lists.items() if list(signature[1]) == expected_sigs]
        # The normalized subtree can be shared by multiple legitimate list
        # sites.  M06's independent delta is specifically a repeated direct
        # reference in /L/K, so use that raw-COS fact to disambiguate the
        # mutated site rather than relying on object numbers or subtree shape.
        repeated_reference_targets = [
            xref for xref in matching_targets
            if len(raw_xrefs(mutant, xref, "K")) == 2
            and raw_xrefs(mutant, xref, "K")[0] == raw_xrefs(mutant, xref, "K")[1]
        ]
        if repeated_reference_targets:
            matching_targets = repeated_reference_targets
        observed["matching_mutant_target_count"] = len(matching_targets)
        observed["matching_mutant_target_xrefs"] = matching_targets
        target_path = struct_path(golden, target)
        mutant_target = follow_struct_path(mutant, target_path)
        observed["target_structure_path"] = target_path
        observed["target_xref_by_structure_path"] = mutant_target
        if mutant_target is None:
            mutant_target = matching_targets[0] if len(matching_targets) == 1 else target
        after_k = direct_list_children(mutant, mutant_target)
        observed["target_role_before"] = raw_role(golden, target)
        observed["target_role_after"] = raw_role(mutant, mutant_target)
        observed["target_li_refs_before"] = before_k
        observed["target_li_refs_after"] = after_k
        observed["target_xref_after"] = mutant_target
        observed["target_role_sequence_before"] = [raw_role(golden, child) for child in before_k]
        observed["target_role_sequence_after"] = [raw_role(mutant, child) for child in after_k]
        before_lists = all_list_signatures(golden)
        before_non_target = [signature for xref, signature in before_lists.items() if xref != target]
        after_non_target = [signature for xref, signature in mutant_lists.items() if xref != mutant_target]
        observed["non_target_list_role_sequences_equal"] = (
            sorted(before_non_target) == sorted(after_non_target)
        )
        observed["expected_target_signature_after"] = expected_sigs
        if (
            raw_role(golden, target) == "/L"
            and mutant_target in matching_targets
            and raw_role(mutant, mutant_target) == "/L"
            and bool(before_k)
            and [struct_signature(mutant, child) for child in after_k] == expected_sigs
            and observed["non_target_list_role_sequences_equal"]
        ):
            return "CONFIRMED", observed, unexpected
        return "CONTRADICTED", observed, unexpected
    # K-tree mutations are not yet normalized across indirect-object layouts.
    # Comparing a role inventory or trusting generator output would overstate
    # independence, so these remain explicit follow-up work.
    observed["unsupported_delta_fields"] = sorted(delta)
    return "UNVERIFIABLE", observed, unexpected


def audit(row: dict, dpi: int) -> dict:
    golden_path = ROOT / row["source_pdf"]
    mutant_path = ROOT / row["mutant_pdf"]
    record = {"artifact_id": row["mutant_id"], "operator": row["operator"], "source_sha256": sha256(golden_path), "mutant_sha256": sha256(mutant_path), "intended_delta": row.get("generation", {}).get("delta", {}), "unexpected_structural_changes": [], "unexpected_content_changes": []}
    golden = pymupdf.open(str(golden_path))
    mutant = pymupdf.open(str(mutant_path))
    try:
        invariants = page_invariants(golden, mutant)
        record["independent_invariants"] = invariants
        for key, value in invariants.items():
            if not value:
                record["unexpected_content_changes"].append(key)
        delta_status, observed, unexpected = raw_cos_delta(golden, mutant, row["operator"], record["intended_delta"])
        record["observed_delta"] = observed
        record["independent_delta_status"] = delta_status
        record["unexpected_structural_changes"].extend(unexpected)
        record["primary_verification_status"] = "PASS" if row.get("verification", {}).get("mutation_valid") is True else "FAIL"
        record["independent_structure_status"] = "PASS" if delta_status == "CONFIRMED" and all(invariants.values()) else "REVIEW_REQUIRED"
        record["primary_render_status"] = "PASS" if row.get("verification", {}).get("rendering", {}).get("status") == "pass" else "FAIL"
        render = render_equal(golden, mutant, dpi)
        record["independent_render_status"] = render["status"]
        record["independent_render_detail"] = render
        record["mutation_confidence"] = "HIGH" if record["independent_structure_status"] == "PASS" and render["status"] == "PASS" else "REVIEW_REQUIRED"
    finally:
        golden.close()
        mutant.close()
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "evidence" / "independent_verification_v2")
    parser.add_argument("--dpi", type=int, default=72)
    parser.add_argument("--mutant-id", action="append", default=[], help="Audit only this mutant ID; may be repeated.")
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    exclusions = {row["mutant_id"] for row in csv.DictReader((ROOT / "data" / "mutant_exclusions.csv").open(encoding="utf-8-sig", newline=""))}
    rows = [row for row in read_jsonl(ROOT / "data" / "mutants.jsonl") if str(row.get("status", "")).lower() == "valid" and row.get("mutant_id") not in exclusions and row.get("verification", {}).get("mutation_valid") is True]
    if args.mutant_id:
        requested = set(args.mutant_id)
        rows = [row for row in rows if row["mutant_id"] in requested]
        missing = requested - {row["mutant_id"] for row in rows}
        if missing:
            parser.error("unknown, excluded, or invalid mutant ID(s): " + ", ".join(sorted(missing)))
    output_dir.mkdir(parents=True, exist_ok=True)
    counts = {"independent_delta_confirmed": 0, "independent_delta_contradicted": 0, "independent_delta_unverifiable": 0, "independent_render_pass": 0, "high_confidence": 0}
    for index, row in enumerate(rows, 1):
        record = audit(row, args.dpi)
        (output_dir / f"{record['artifact_id']}.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        counts["independent_delta_" + record["independent_delta_status"].lower()] += 1
        counts["independent_render_pass"] += record["independent_render_status"] == "PASS"
        counts["high_confidence"] += record["mutation_confidence"] == "HIGH"
        if index % 10 == 0 or index == len(rows):
            print(f"Audited {index}/{len(rows)} active pairs", flush=True)
    summary = {"audit_count": len(rows), **counts, "output_dir": str(output_dir.resolve().relative_to(ROOT))}
    print(json.dumps(summary, indent=2, sort_keys=True))
    # Successful execution means the audit completed; the summary reports
    # scientific review statuses without converting unverifiable mutations to
    # a process failure or a false positive.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
