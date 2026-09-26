from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, NameObject, NumberObject, TextStringObject


STRUCTURAL_TYPES = {"/Document", "/Part", "/Art", "/Sect", "/Div", "/BlockQuote", "/Caption", "/TOC", "/TOCI", "/Index", "/NonStruct", "/Private", "/P", "/H1", "/H2", "/H3", "/H4", "/H5", "/H6", "/L", "/LI", "/Lbl", "/LBody", "/Table", "/TR", "/TH", "/TD", "/THead", "/TBody", "/TFoot", "/Figure", "/Formula", "/Form", "/Link", "/Span"}


def deref(value: Any) -> Any:
    return value.get_object() if hasattr(value, "get_object") else value


def ref_label(value: Any) -> str:
    if hasattr(value, "idnum"):
        return f"{value.idnum}:{getattr(value, 'generation', 0)}"
    return "direct"


def is_struct_elem(value: Any) -> bool:
    obj = deref(value)
    # PDF structure elements may use custom /S names resolved through
    # /RoleMap. MCR dictionaries do not have /S, so this remains distinct
    # from marked-content references while supporting real reference-suite
    # role names such as /H1-content and /Labels.
    return isinstance(obj, dict) and isinstance(obj.get("/S"), str)


def as_array(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (ArrayObject, list, tuple)):
        return list(value)
    # Preserve an indirect reference when /K is a scalar reference. The
    # reference identity is part of the structural delta and must not be
    # replaced by a direct dictionary during inspection.
    return [value]


def is_content_item(value: Any) -> bool:
    obj = deref(value)
    return isinstance(obj, int) or (isinstance(obj, dict) and "/MCID" in obj)


def object_snapshot(value: Any) -> Any:
    """A stable, JSON-friendly summary of reachable structure objects."""
    obj = deref(value)
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key in sorted(obj.keys()):
            if key in {"/K", "/S", "/P", "/Pg", "/Alt", "/Lang", "/RoleMap", "/Type", "/MCID"}:
                item = obj[key]
                if key == "/K":
                    out[key] = [object_snapshot(x) for x in as_array(item)]
                elif key in {"/P", "/Pg"}:
                    # Parent/page links are graph edges. Do not recursively
                    # follow them or a normal structure tree would cycle.
                    out[key] = {"ref": ref_label(item)} if hasattr(item, "idnum") else {"type": str(deref(item).get("/Type")) if isinstance(deref(item), dict) else str(deref(item))}
                elif key == "/RoleMap":
                    role_map = deref(item)
                    out[key] = {str(k): str(v) for k, v in sorted(role_map.items())} if isinstance(role_map, dict) else str(role_map)
                else:
                    out[key] = object_snapshot(item)
        return out
    if hasattr(value, "idnum"):
        return {"ref": ref_label(value)}
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(obj)


@dataclass
class StructRecord:
    ref: Any
    parent_ref: Any
    obj: Any
    parent_obj: Any
    k_index: int


def iter_structure(root_obj: Any) -> Iterable[StructRecord]:
    seen: set[str] = set()

    def walk(value: Any, parent_ref: Any = None, parent_obj: Any = None, k_index: int = -1):
        obj = deref(value)
        if not isinstance(obj, dict):
            return
        label = ref_label(value)
        if label in seen:
            return
        seen.add(label)
        if "/S" in obj:
            record = StructRecord(value, parent_ref, obj, parent_obj, k_index)
            yield record
            for idx, child in enumerate(as_array(obj.get("/K"))):
                if is_struct_elem(child):
                    yield from walk(child, value, obj, idx)

    for idx, child in enumerate(as_array(deref(root_obj).get("/K"))):
        if is_struct_elem(child):
            yield from walk(child, root_obj, deref(root_obj), idx)


def structure_records(reader: PdfReader) -> list[StructRecord]:
    catalog = deref(reader.trailer["/Root"])
    struct_root = catalog.get("/StructTreeRoot")
    if struct_root is None:
        raise ValueError("PDF has no /StructTreeRoot")
    return list(iter_structure(struct_root))


def record_by_ref(records: list[StructRecord], label: str) -> StructRecord | None:
    return next((r for r in records if ref_label(r.ref) == label), None)


def same_object(left: Any, right: Any) -> bool:
    """Compare PDF object identity without confusing equal dictionaries."""
    left_label, right_label = ref_label(left), ref_label(right)
    if left_label != "direct" or right_label != "direct":
        return left_label == right_label
    return deref(left) is deref(right)


def reference_occurrences(reader: PdfReader, target: Any) -> int:
    """Count references to a structure element in reachable /K arrays."""
    return sum(
        same_object(child, target)
        for record in structure_records(reader)
        for child in as_array(record.obj.get("/K"))
        if is_struct_elem(child)
    )


def find_candidates(reader: PdfReader, operator: str) -> list[Any]:
    records = structure_records(reader)
    candidates: list[Any] = []
    for r in records:
        role = str(r.obj.get("/S"))
        k = as_array(r.obj.get("/K"))
        if operator == "M01" and len(k) >= 2 and is_struct_elem(k[0]) and is_struct_elem(k[1]) and not same_object(k[0], k[1]):
            candidates.append(r.ref)
        elif operator == "M02" and k and is_struct_elem(k[0]) and reference_occurrences(reader, k[0]) == 1:
            candidates.append(r.ref)
        elif operator == "M03" and role in {"/H1", "/H2", "/H3"}:
            candidates.append(r.ref)
        elif operator == "M05" and len(k) >= 2 and all(is_content_item(x) for x in k):
            candidates.append(r.ref)
        elif operator == "M06" and role == "/L" and any(str(deref(x).get("/S")) == "/LI" for x in k if isinstance(deref(x), dict)):
            candidates.append(r.ref)
        elif operator == "M07" and role == "/Figure" and str(r.obj.get("/Alt", "")).strip():
            candidates.append(r.ref)
        elif operator == "M10" and role in {"/TD", "/TH"} and r.parent_obj is not None and str(r.parent_obj.get("/S")) == "/TR":
            candidates.append(r.ref)
    if operator == "M04":
        for parent in records:
            siblings = [x for x in as_array(parent.obj.get("/K")) if is_struct_elem(x)]
            for left, right in zip(siblings, siblings[1:]):
                lo, ro = deref(left), deref(right)
                if str(lo.get("/S")) == str(ro.get("/S")) and len(as_array(lo.get("/K"))) == 1 and len(as_array(ro.get("/K"))) == 1 and all(is_content_item(x) for x in [as_array(lo.get("/K"))[0], as_array(ro.get("/K"))[0]]):
                    return [left, right]
    if operator == "M08":
        catalog = deref(reader.trailer["/Root"])
        return [reader.trailer["/Root"]] if "/Lang" in catalog else []
    if operator == "M09":
        catalog = deref(reader.trailer["/Root"])
        struct_root = deref(catalog.get("/StructTreeRoot"))
        used_roles = {str(record.obj.get("/S")) for record in structure_records(reader)}
        for holder in (catalog, struct_root):
            role_map = deref(holder.get("/RoleMap")) if isinstance(holder, dict) else None
            if isinstance(role_map, dict):
                for key, value in role_map.items():
                    # M09 must break a mapping that is actually exercised by
                    # a reachable structure element.  Mutating an unused
                    # RoleMap entry changes bytes but creates no semantic
                    # defect and is therefore not a valid benchmark mutant.
                    if (
                        str(key) not in STRUCTURAL_TYPES
                        and str(value) in STRUCTURAL_TYPES
                        and str(key) in used_roles
                    ):
                        return [holder]
        return []
    return candidates


def parse_target(reader: PdfReader, operator: str, target: str) -> list[Any]:
    candidates = find_candidates(reader, operator)
    if target == "auto":
        if not candidates:
            raise ValueError(f"no valid target satisfies {operator} preconditions")
        return candidates
    if not target.startswith("obj=") or ":" not in target:
        raise ValueError("target must be 'auto' or an object reference such as obj=12:0")
    wanted = target[4:]
    records = structure_records(reader)
    if operator == "M08":
        if ref_label(reader.trailer["/Root"]) != wanted:
            raise ValueError("target object is not the catalog")
        return [reader.trailer["/Root"]]
    match = record_by_ref(records, wanted)
    if match is None:
        raise ValueError(f"target {wanted} is not a reachable structure element")
    return [match.ref]


def mutate(reader: PdfReader, operator: str, targets: list[Any]) -> dict[str, Any]:
    if operator == "M04":
        left_ref, right_ref = targets
        left, right = deref(left_ref), deref(right_ref)
        left_k, right_k = as_array(left.get("/K")), as_array(right.get("/K"))
        if len(left_k) != 1 or len(right_k) != 1:
            raise ValueError("M04 target leaves must have exactly one content item each")
        left[NameObject("/K")] = ArrayObject([right_k[0]])
        right[NameObject("/K")] = ArrayObject([left_k[0]])
        return {"target_object": f"{ref_label(left_ref)};{ref_label(right_ref)}", "old_k": [object_snapshot(left_k[0]), object_snapshot(right_k[0])], "new_k": [object_snapshot(right_k[0]), object_snapshot(left_k[0])]}

    target_ref = targets[0]
    target = deref(target_ref)
    if operator in {"M01", "M02", "M05", "M06"}:
        old = as_array(target.get("/K"))
        if operator == "M01":
            if len(old) < 2 or not all(is_struct_elem(x) for x in old[:2]):
                raise ValueError("M01 requires two direct structure-element children")
            if same_object(old[0], old[1]):
                raise ValueError("M01 requires two distinct direct structure-element children")
            new = old[:]
            new[0], new[1] = new[1], new[0]
        elif operator == "M02":
            if not old or not is_struct_elem(old[0]):
                raise ValueError("M02 requires a direct structure-element child")
            if reference_occurrences(reader, old[0]) != 1:
                raise ValueError("M02 selected child is reachable through multiple /K references")
            new = old[1:]
        elif operator == "M05":
            if len(old) < 2 or not all(is_content_item(x) for x in old):
                raise ValueError("M05 requires at least two content items")
            new = list(reversed(old))
        else:
            if str(target.get("/S")) != "/L" or not old:
                raise ValueError("M06 requires a list with a child")
            first = next((x for x in old if str(deref(x).get("/S")) == "/LI"), None)
            if first is None:
                raise ValueError("M06 requires a direct LI child")
            new = old[:]
            new.insert(0, first)
        target[NameObject("/K")] = ArrayObject(new)
        return {"target_object": ref_label(target_ref), "old_k": [object_snapshot(x) for x in old], "new_k": [object_snapshot(x) for x in new]}
    if operator == "M03":
        old = str(target.get("/S"))
        level = int(old[2:])
        new = f"/H{level + 2}"
        if level > 3 or new == old:
            raise ValueError("M03 target must be H1-H3 so the mutation creates a skipped heading level")
        target[NameObject("/S")] = NameObject(new)
        return {"target_object": ref_label(target_ref), "old_role": old, "new_role": new}
    if operator == "M07":
        old = str(target.get("/Alt"))
        del target[NameObject("/Alt")]
        return {"target_object": ref_label(target_ref), "old_alt": old, "new_alt": None}
    if operator == "M08":
        catalog = target
        old = str(catalog.get("/Lang"))
        del catalog[NameObject("/Lang")]
        return {"target_object": ref_label(target_ref), "old_lang": old, "new_lang": None}
    if operator == "M09":
        used_roles = {str(record.obj.get("/S")) for record in structure_records(reader)}
        for holder in (target, deref(target.get("/StructTreeRoot")) if isinstance(target, dict) else None):
            role_map = deref(holder.get("/RoleMap")) if isinstance(holder, dict) else None
            if isinstance(role_map, dict):
                for key, value in role_map.items():
                    if str(key) not in STRUCTURAL_TYPES and str(value) in STRUCTURAL_TYPES and str(key) in used_roles:
                        old = str(value)
                        role_map[key] = NameObject("/PDFa11yMutUndefinedRole")
                        return {"target_object": ref_label(target_ref), "role_key": str(key), "old_role": old, "new_role": "/PDFa11yMutUndefinedRole"}
        raise ValueError("M09 has no custom role mapping target")
    if operator == "M10":
        old = str(target.get("/S"))
        if old not in {"/TD", "/TH"}:
            raise ValueError("M10 target is not a cell")
        target[NameObject("/S")] = NameObject("/P")
        return {"target_object": ref_label(target_ref), "old_role": old, "new_role": "/P"}
    raise ValueError(f"unknown operator {operator}")


def write_mutant(input_path: Path, output_path: Path, operator: str, target: str) -> dict[str, Any]:
    reader = PdfReader(str(input_path), strict=False)
    targets = parse_target(reader, operator, target)
    delta = mutate(reader, operator, targets)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as fh:
        writer.write(fh)
    return {"operator": operator, "requested_target": target, "delta": delta, "source_pages": len(reader.pages)}
