"""Add PDF/UA metadata that the legacy TeX toolchain does not emit."""
from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import BooleanObject, DecodedStreamObject, DictionaryObject, NameObject


def xmp(title: str, subject: str) -> bytes:
    return f'''<?xpacket begin="\\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:pdf="http://ns.adobe.com/pdf/1.3/" xmlns:xmp="http://ns.adobe.com/xap/1.0/">
   <dc:title><rdf:Alt><rdf:li xml:lang="x-default">{title}</rdf:li></rdf:Alt></dc:title>
   <dc:description><rdf:Alt><rdf:li xml:lang="x-default">{subject}</rdf:li></rdf:Alt></dc:description>
   <pdf:Producer>PDFa11yMut with Tectonic</pdf:Producer>
   <xmp:CreatorTool>PDFa11yMut with Tectonic</xmp:CreatorTool>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>'''.encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    reader = PdfReader(str(args.input), strict=False)
    writer = PdfWriter(clone_from=str(args.input))
    title = "PDFa11yMut: Measuring Mutation-Specific Detection in PDF Accessibility Checkers"
    subject = "Mutation-based evaluation of PDF accessibility checking configurations"
    writer.add_metadata({"/Title": title, "/Subject": subject, "/Creator": "PDFa11yMut with Tectonic"})
    writer._root_object.update({
        NameObject("/Lang"): reader.trailer["/Root"].get("/Lang", "en-US"),
        NameObject("/ViewerPreferences"): DictionaryObject({NameObject("/DisplayDocTitle"): BooleanObject(True)}),
    })
    stream = DecodedStreamObject()
    stream.set_data(xmp(title, subject))
    stream.update({NameObject("/Type"): NameObject("/Metadata"), NameObject("/Subtype"): NameObject("/XML")})
    writer._root_object[NameObject("/Metadata")] = writer._add_object(stream)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as handle:
        writer.write(handle)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
