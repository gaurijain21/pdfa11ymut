from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageStat
from pypdf import PdfReader

from .core import as_array, deref, is_struct_elem, ref_label, reference_occurrences, same_object, structure_records


_golden_render_cache: tuple[tuple[str, int, int, int], list[Image.Image]] | None = None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_pdftoppm() -> str | None:
    configured = os.environ.get("PDFa11YMUT_PDFTOPPM")
    candidates = [configured, shutil.which("pdftoppm")]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def structure_map(reader: PdfReader) -> dict[str, Any]:
    """Map structure-tree paths to non-recursive signatures.

    pypdf may renumber indirect objects when rewriting a file, so object IDs
    are not used as comparison keys. Paths and local node signatures survive
    that serialization boundary and expose actual structural deltas.
    """
    catalog = deref(reader.trailer["/Root"])
    struct_root = deref(catalog["/StructTreeRoot"])
    out: dict[str, Any] = {}
    seen: set[str] = set()

    def item_signature(value: Any, inherited_page: Any = None) -> Any:
        """Return a shallow semantic signature for a direct ``/K`` item.

        The previous fallback used ``str(obj)``, which embeds rewritten indirect
        object numbers for OBJR dictionaries.  That made semantically identical
        links compare unequal after pypdf serialization.  Reuse the canonical
        semantic normalizer, but keep structure children shallow so an intended
        descendant role change does not make every ancestor look changed.
        """
        signature = canonical_object_signature(reader, value, inherited_page)
        if signature and signature[0] == "struct":
            return ["struct", signature[1]]
        return signature

    def walk(value: Any, path: str) -> None:
        obj = deref(value)
        if not isinstance(obj, dict) or "/S" not in obj:
            return
        label = ref_label(value)
        if label == "direct":
            label = f"direct:{id(obj)}"
        if label in seen:
            return
        seen.add(label)
        page_ref = obj.get("/Pg")
        out[path] = {
            "role": str(obj.get("/S")),
            "k": [item_signature(x, page_ref) for x in as_array(obj.get("/K"))],
            "alt": str(obj["/Alt"]) if "/Alt" in obj else None,
            "actual_text": str(obj["/ActualText"]) if "/ActualText" in obj else None,
        }
        for index, child in enumerate(as_array(obj.get("/K"))):
            if is_struct_elem(child):
                walk(child, f"{path}.{index}")

    for index, child in enumerate(as_array(struct_root.get("/K"))):
        if is_struct_elem(child):
            walk(child, str(index))
    return out


def page_content_hashes(reader: PdfReader) -> list[str]:
    values = []
    for page in reader.pages:
        contents = page.get_contents()
        raw = b"" if contents is None else contents.get_data()
        values.append(hashlib.sha256(raw).hexdigest())
    return values


def render_compare(golden: Path, mutant: Path, dpi: int = 150) -> dict[str, Any]:
    global _golden_render_cache
    pdftoppm = find_pdftoppm()
    if pdftoppm is None:
        return {"status": "unavailable", "renderer": "pdftoppm", "reason": "pdftoppm not found"}
    golden_stat = golden.stat()
    golden_key = (str(golden.resolve()), golden_stat.st_mtime_ns, golden_stat.st_size, dpi)
    with tempfile.TemporaryDirectory(prefix="pdfa11ymut-render-") as tmp:
        tmp_path = Path(tmp)
        pairs: list[dict[str, Any]] = []
        if _golden_render_cache is None or _golden_render_cache[0] != golden_key:
            prefix = tmp_path / "golden"
            proc = subprocess.run([pdftoppm, "-png", "-r", str(dpi), str(golden), str(prefix)], capture_output=True, text=True)
            if proc.returncode:
                return {"status": "failed", "renderer": "pdftoppm", "dpi": dpi, "stderr": proc.stderr[-1000:]}
            rendered = []
            for path in sorted(tmp_path.glob("golden-*.png")):
                with Image.open(path) as image:
                    rendered.append(image.convert("RGB").copy())
            _golden_render_cache = (golden_key, rendered)
        golden_images = _golden_render_cache[1]
        prefix = tmp_path / "mutant"
        proc = subprocess.run([pdftoppm, "-png", "-r", str(dpi), str(mutant), str(prefix)], capture_output=True, text=True)
        if proc.returncode:
            return {"status": "failed", "renderer": "pdftoppm", "dpi": dpi, "stderr": proc.stderr[-1000:]}
        mutant_images = sorted(tmp_path.glob("mutant-*.png"))
        if len(golden_images) != len(mutant_images):
            return {"status": "failed", "reason": "rendered page count differs", "golden_pages": len(golden_images), "mutant_pages": len(mutant_images), "dpi": dpi}
        max_diff = 0
        total_diff_pixels = 0
        rmses = []
        for page_number, (g, mpath) in enumerate(zip(golden_images, mutant_images), start=1):
            with Image.open(mpath) as mutant_image:
                m = mutant_image.convert("RGB")
                if g.size != m.size:
                    return {"status": "failed", "reason": "rendered page dimensions differ", "dpi": dpi}
                diff = ImageChops.difference(g, m)
                bbox = diff.getbbox()
                stat = ImageStat.Stat(diff)
                page_max = max(stat.extrema[i][1] for i in range(3))
                max_diff = max(max_diff, page_max)
                pixels = diff.get_flattened_data() if hasattr(diff, "get_flattened_data") else diff.getdata()
                page_diff_pixels = sum(1 for px in pixels if px != (0, 0, 0))
                total_diff_pixels += page_diff_pixels
                rmses.append(sum(v * v for v in stat.rms) ** 0.5)
                pairs.append({"page": page_number, "dimensions": list(g.size), "different_pixels": page_diff_pixels, "bbox": list(bbox) if bbox else None})
        return {"status": "pass" if total_diff_pixels == 0 else "fail", "renderer": "pdftoppm", "dpi": dpi, "metric": "exact RGB pixel equality", "tolerance": 0, "different_pixel_count": total_diff_pixels, "rmse": max(rmses, default=0), "max_channel_difference": max_diff, "pages": pairs}


def structure_reference_paths(reader: PdfReader) -> dict[str, tuple[int, ...]]:
    """Map source indirect references to their stable /K paths."""
    catalog = deref(reader.trailer["/Root"])
    struct_root = deref(catalog["/StructTreeRoot"])
    paths: dict[str, tuple[int, ...]] = {}
    seen: set[str] = set()

    def walk(value: Any, path: tuple[int, ...]) -> None:
        obj = deref(value)
        if not is_struct_elem(value):
            return
        label = ref_label(value)
        if label != "direct":
            paths[label] = path
        identity = label if label != "direct" else f"direct:{id(obj)}"
        if identity in seen:
            return
        seen.add(identity)
        for index, child in enumerate(as_array(obj.get("/K"))):
            if is_struct_elem(child):
                walk(child, path + (index,))

    for index, child in enumerate(as_array(struct_root.get("/K"))):
        if is_struct_elem(child):
            walk(child, (index,))
    return paths


def structure_node_at(reader: PdfReader, path: tuple[int, ...]) -> Any:
    catalog = deref(reader.trailer["/Root"])
    node = deref(catalog["/StructTreeRoot"])
    for index in path:
        children = as_array(node.get("/K"))
        if index >= len(children) or not is_struct_elem(children[index]):
            raise ValueError(f"structure path {path} is not reachable")
        node = deref(children[index])
    return node


def target_paths(golden: PdfReader, delta: dict[str, Any]) -> list[tuple[int, ...]]:
    reference_paths = structure_reference_paths(golden)
    labels = [label.strip() for label in str(delta.get("target_object", "")).split(";")]
    if not labels or any(not label or label == "direct" or label not in reference_paths for label in labels):
        return []
    return [reference_paths[label] for label in labels]


def page_number_map(reader: PdfReader) -> dict[str, int]:
    return {
        ref_label(page.indirect_reference): index
        for index, page in enumerate(reader.pages)
        if page.indirect_reference is not None
    }


def canonical_object_signature(reader: PdfReader, value: Any, inherited_page: Any = None, active: set[str] | None = None) -> Any:
    """Normalize a /K object using PDF meaning, not writer-renumbered xrefs."""
    if active is None:
        active = set()
    obj = deref(value)
    pages = page_number_map(reader)

    def normalized_page(page_ref: Any) -> int | None:
        return pages.get(ref_label(page_ref)) if page_ref is not None else None

    if isinstance(obj, bool):
        return ["boolean", obj]
    if isinstance(obj, int):
        return ["mcid", int(obj), normalized_page(inherited_page)]
    if is_struct_elem(value):
        label = ref_label(value)
        identity = label if label != "direct" else f"direct:{id(obj)}"
        if identity in active:
            return ["cycle", str(obj.get("/S"))]
        active.add(identity)
        page_ref = obj.get("/Pg", inherited_page)
        signature = [
            "struct",
            str(obj.get("/S")),
            str(obj.get("/Alt")) if "/Alt" in obj else None,
            str(obj.get("/ActualText")) if "/ActualText" in obj else None,
            normalized_page(page_ref),
            [canonical_object_signature(reader, child, page_ref, active) for child in as_array(obj.get("/K"))],
        ]
        active.remove(identity)
        return signature
    if isinstance(obj, dict):
        page_ref = obj.get("/Pg", inherited_page)
        if "/MCID" in obj:
            return ["mcr", int(obj["/MCID"]), normalized_page(page_ref)]
        if str(obj.get("/Type")) == "/OBJR":
            target = deref(obj.get("/Obj"))
            return ["objr", normalized_page(page_ref), str(target.get("/Subtype")) if isinstance(target, dict) else None,
                    str(target.get("/Rect")) if isinstance(target, dict) else None,
                    str(target.get("/Contents")) if isinstance(target, dict) and "/Contents" in target else None]
        return ["dict", str(obj.get("/Type")), normalized_page(page_ref)]
    if isinstance(obj, str):
        return ["name-or-string", str(obj)]
    return [type(obj).__name__, str(obj)]


def structural_outside_targets_unchanged(before: dict[str, Any], after: dict[str, Any], paths: list[tuple[int, ...]]) -> bool:
    prefixes = [".".join(str(part) for part in path) for path in paths]
    ancestors = {
        ".".join(str(part) for part in path[:depth])
        for path in paths
        for depth in range(1, len(path))
    }
    keys = set(before) | set(after)
    for key in keys:
        if any(key == prefix or key.startswith(prefix + ".") for prefix in prefixes):
            continue
        if key in ancestors:
            left, right = before.get(key), after.get(key)
            if not isinstance(left, dict) or not isinstance(right, dict):
                return False
            if (
                left.get("role") != right.get("role")
                or left.get("alt") != right.get("alt")
                or left.get("actual_text") != right.get("actual_text")
            ):
                return False
            normalize_child_roles = lambda values: [
                ["struct"] if isinstance(item, list) and item and item[0] == "struct" else item
                for item in values
            ]
            if normalize_child_roles(left.get("k", [])) != normalize_child_roles(right.get("k", [])):
                return False
            continue
        if before.get(key) != after.get(key):
            return False
    return True


def operator_delta_ok(operator: str, delta: dict[str, Any], before: dict[str, Any], after: dict[str, Any], changed: list[str], golden: PdfReader, mutant: PdfReader) -> tuple[bool, str]:
    target = delta.get("target_object", "")
    if operator == "M08":
        gcat, mcat = deref(golden.trailer["/Root"]), deref(mutant.trailer["/Root"])
        old_lang = str(gcat.get("/Lang")) if "/Lang" in gcat else None
        ok = old_lang == delta.get("old_lang") and "/Lang" not in mcat and delta.get("new_lang") is None
        return ok and before == after, "catalog /Lang matches intended removal; structure tree is unchanged"

    if operator == "M09":
        role_key = delta.get("role_key")
        if not role_key or not any(str(record.obj.get("/S")) == role_key for record in structure_records(golden)):
            return False, "RoleMap key is not used by a reachable source structure element"
        gcat, mcat = deref(golden.trailer["/Root"]), deref(mutant.trailer["/Root"])
        groot, mroot = deref(gcat.get("/StructTreeRoot")), deref(mcat.get("/StructTreeRoot"))
        holders = [(gcat, mcat), (groot, mroot)]
        matching = []
        for gholder, mholder in holders:
            if not isinstance(gholder, dict) or not isinstance(mholder, dict):
                continue
            gm, mm = deref(gholder.get("/RoleMap")), deref(mholder.get("/RoleMap"))
            if isinstance(gm, dict) and role_key in gm:
                matching.append((gm, mm))
        if len(matching) != 1:
            return False, "expected exactly one RoleMap containing the selected key"
        gm, mm = matching[0]
        ok = isinstance(mm, dict) and set(gm) == set(mm)
        ok = ok and str(gm.get(role_key)) == delta.get("old_role") and str(mm.get(role_key)) == delta.get("new_role")
        ok = ok and all(str(gm[key]) == str(mm[key]) for key in gm if key != role_key)
        return ok and before == after, "used RoleMap value changed exactly; structure tree is unchanged"

    paths = target_paths(golden, delta)
    expected_count = 2 if operator == "M04" else 1
    if len(paths) != expected_count or (operator == "M04" and paths[0][:-1] != paths[1][:-1]):
        return False, f"cannot resolve {expected_count} reachable target structure element(s) from source references"
    try:
        gnodes = [structure_node_at(golden, path) for path in paths]
        mnodes = [structure_node_at(mutant, path) for path in paths]
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        return False, f"target structure path is not preserved in mutant: {exc}"

    def signatures(reader: PdfReader, node: Any) -> list[Any]:
        page_ref = node.get("/Pg")
        return [canonical_object_signature(reader, item, page_ref) for item in as_array(node.get("/K"))]

    outside_unchanged = structural_outside_targets_unchanged(before, after, paths)

    if operator == "M01":
        old_k, new_k = signatures(golden, gnodes[0]), signatures(mutant, mnodes[0])
        if len(old_k) < 2 or old_k[0] == old_k[1]:
            return False, "M01 target does not have two distinguishable direct structure children"
        expected = old_k[:]
        expected[0], expected[1] = expected[1], expected[0]
        ok = new_k == expected and str(gnodes[0].get("/S")) == str(mnodes[0].get("/S"))
        return ok and outside_unchanged, "observed /K children are exactly reordered; outside structure is unchanged"

    if operator == "M02":
        old_items = as_array(gnodes[0].get("/K"))
        new_items = as_array(mnodes[0].get("/K"))
        old_k, new_k = signatures(golden, gnodes[0]), signatures(mutant, mnodes[0])
        if not old_items or not is_struct_elem(old_items[0]):
            return False, "M02 source target must have a removable direct structure child"
        if reference_occurrences(golden, old_items[0]) != 1:
            return False, "M02 removed child has multiple reachable /K references"
        removed_signature = canonical_object_signature(golden, old_items[0], gnodes[0].get("/Pg"))
        reachable_after = [canonical_object_signature(mutant, record.ref, record.obj.get("/Pg")) for record in structure_records(mutant)]
        ok = new_k == old_k[1:] and removed_signature not in reachable_after
        ok = ok and str(gnodes[0].get("/S")) == str(mnodes[0].get("/S"))
        return ok and outside_unchanged, "first direct subtree is no longer reachable and remaining /K is unchanged"

    if operator == "M04":
        old_roles = [str(node.get("/S")) for node in gnodes]
        new_roles = [str(node.get("/S")) for node in mnodes]
        old_k = [signatures(golden, node) for node in gnodes]
        new_k = [signatures(mutant, node) for node in mnodes]
        if old_roles[0] != old_roles[1] or len(old_k[0]) != 1 or len(old_k[1]) != 1 or old_k[0][0] == old_k[1][0]:
            return False, "M04 targets must be same-role sibling leaves with distinct single content items"
        ok = new_roles == old_roles and new_k == [old_k[1], old_k[0]]
        return ok and outside_unchanged, "observed leaf associations are exactly exchanged; containment is unchanged"

    if operator == "M05":
        old_items, new_items = as_array(gnodes[0].get("/K")), as_array(mnodes[0].get("/K"))
        old_k, new_k = signatures(golden, gnodes[0]), signatures(mutant, mnodes[0])
        ok = len(old_k) >= 2 and all(not is_struct_elem(item) for item in old_items) and new_k == list(reversed(old_k)) and old_k != new_k
        ok = ok and str(gnodes[0].get("/S")) == str(mnodes[0].get("/S"))
        return ok and outside_unchanged, "observed content-item sequence is exactly reversed; outside structure is unchanged"

    if operator == "M06":
        old_items, new_items = as_array(gnodes[0].get("/K")), as_array(mnodes[0].get("/K"))
        old_k, new_k = signatures(golden, gnodes[0]), signatures(mutant, mnodes[0])
        first_li = next((index for index, item in enumerate(old_items) if is_struct_elem(item) and str(deref(item).get("/S")) == "/LI"), None)
        if str(gnodes[0].get("/S")) != "/L" or first_li is None:
            return False, "M06 target must be a list with a direct list-item child"
        duplicate_is_same_ref = same_object(new_items[0], new_items[first_li + 1]) if len(new_items) > first_li + 1 else False
        expected = [old_k[first_li], *old_k]
        ok = new_k == expected and duplicate_is_same_ref and str(mnodes[0].get("/S")) == "/L"
        return ok and outside_unchanged, "observed /K contains exactly one duplicated /LI reference; outside structure is unchanged"

    if operator == "M03":
        old_role, new_role = delta.get("old_role"), delta.get("new_role")
        valid_roles = {"/H1": "/H3", "/H2": "/H4", "/H3": "/H5"}
        ok = old_role in valid_roles and new_role == valid_roles[old_role]
        ok = ok and str(gnodes[0].get("/S")) == old_role and str(mnodes[0].get("/S")) == new_role
        ok = ok and signatures(golden, gnodes[0]) == signatures(mutant, mnodes[0])
        return ok and outside_unchanged, "observed target heading level changed by two; its contents and outside structure are unchanged"

    if operator == "M07":
        old_alt = delta.get("old_alt")
        ok = str(gnodes[0].get("/S")) == "/Figure" and str(mnodes[0].get("/S")) == "/Figure"
        ok = ok and old_alt is not None and str(gnodes[0].get("/Alt")) == old_alt and "/Alt" not in mnodes[0]
        ok = ok and signatures(golden, gnodes[0]) == signatures(mutant, mnodes[0])
        return ok and outside_unchanged, "observed target Figure /Alt removal; its content and outside structure are unchanged"

    if operator == "M10":
        old_role = delta.get("old_role")
        ok = old_role in {"/TD", "/TH"} and delta.get("new_role") == "/P"
        ok = ok and str(gnodes[0].get("/S")) == old_role and str(mnodes[0].get("/S")) == "/P"
        ok = ok and signatures(golden, gnodes[0]) == signatures(mutant, mnodes[0])
        return ok and outside_unchanged, "observed table-cell role change to /P; contents and outside structure are unchanged"

    return False, f"no operator-specific verifier for {operator}"


def verify_mutation(golden: Path, mutant: Path, operator: str, delta: dict[str, Any], dpi: int = 150) -> dict[str, Any]:
    result: dict[str, Any] = {"source_pdf": str(golden), "mutant_pdf": str(mutant), "source_sha256": sha256(golden), "mutant_sha256": sha256(mutant), "operator": operator, "parseability": False, "mutation_valid": False, "unexpected_structural_changes": [], "invariant_checks": {}}
    try:
        g = PdfReader(str(golden), strict=False)
        m = PdfReader(str(mutant), strict=False)
        result["parseability"] = True
        result["page_count_preserved"] = len(g.pages) == len(m.pages)
        result["invariant_checks"]["page_count_preserved"] = result["page_count_preserved"]
        result["invariant_checks"]["page_content_byte_hashes_equal"] = page_content_hashes(g) == page_content_hashes(m)
        before, after = structure_map(g), structure_map(m)
        result["structural_before"] = before
        result["structural_after"] = after
        changed = sorted(set(before) | set(after))
        changed = [key for key in changed if before.get(key) != after.get(key)]
        result["observed_changed_structure_paths"] = changed
        result["observed_delta"] = {key: {"before": before.get(key), "after": after.get(key)} for key in changed}
        result["rendering"] = render_compare(golden, mutant, dpi=dpi)
        result["invariant_checks"]["rendering_preserved"] = result["rendering"].get("status") == "pass"
        result["invariant_checks"]["source_and_mutant_hash_differ"] = result["source_sha256"] != result["mutant_sha256"]
        result["intended_delta"] = delta
        delta_ok, delta_reason = operator_delta_ok(operator, delta, before, after, changed, g, m)
        result["invariant_checks"]["operator_specific_delta"] = delta_ok
        result["operator_delta_reason"] = delta_reason
        result["mutation_valid"] = all(result["invariant_checks"].values())
        if not result["mutation_valid"]:
            result["exclusion_reason"] = "one or more parse, page, content, rendering, or mutation checks failed"
    except Exception as exc:
        result["exclusion_reason"] = f"verification exception: {type(exc).__name__}: {exc}"
    return result


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str), encoding="utf-8")
