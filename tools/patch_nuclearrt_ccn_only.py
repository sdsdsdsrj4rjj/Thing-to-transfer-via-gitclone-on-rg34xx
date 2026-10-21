#!/usr/bin/env python3
"""Make NuclearRT's exporter tolerate a missing original Clickteam .mfa source file.

Usage: python patch_nuclearrt_ccn_only.py PATH_TO_NUCLEARRT_CHECKOUT

This is a workaround for the exporter startup dependency, not a complete port. CCN
events and object data are still translated by NuclearRT and may use unsupported
extensions/actions/conditions.
"""
from __future__ import annotations
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit(__doc__)
ROOT = Path(sys.argv[1]).resolve()

def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8-sig")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one match in {path}, found {count}; source version may have changed")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"Patched {path.relative_to(ROOT)}")

program = ROOT / "exporter/src/Program.cs"
exporter = ROOT / "exporter/src/Exporter.cs"
base_exporter = ROOT / "exporter/src/BaseExporter.cs"
object_info = ROOT / "exporter/src/Exporters/ObjectInfoExporter.cs"
icon_exporter = ROOT / "exporter/src/Exporters/IconExporter.cs"
pak_builder = ROOT / "exporter/src/PakBuilder.cs"

for path in (program, exporter, base_exporter, object_info, icon_exporter, pak_builder):
    if not path.is_file():
        raise SystemExit(f"Missing expected NuclearRT source file: {path}")

# 1. The standalone CCN records the original editor path, but the MFA itself is
#    typically not shipped. Continue with CCN data if that path is unavailable.
replace_once(
    program,
    '\t\t\t\t//Read MFA file\n\t\t\t\tLog("Reading .mfa file...");\n\t\t\t\tMFAFileReader mfaReader = new MFAFileReader();\n\t\t\t\tmfaReader.LoadGame(ccnReader.game.editorFilename);',
    '\t\t\t\t// The source MFA often is not distributed with a built game. Use runtime CCN data when it is absent.\n'
    '\t\t\t\tMFAFileReader? mfaReader = null;\n'
    '\t\t\t\tif (File.Exists(ccnReader.game.editorFilename))\n'
    '\t\t\t\t{\n'
    '\t\t\t\t\tLog("Reading original .mfa file...");\n'
    '\t\t\t\t\tmfaReader = new MFAFileReader();\n'
    '\t\t\t\t\tmfaReader.LoadGame(ccnReader.game.editorFilename);\n'
    '\t\t\t\t}\n'
    '\t\t\t\telse\n'
    '\t\t\t\t{\n'
    '\t\t\t\t\tLog("Original MFA unavailable; using CCN-only mode. App icons and editor-derived global flags may be incomplete.");\n'
    '\t\t\t\t}'
)

# 2. Allow null MFA reader/data through the exporter object model.
replace_once(exporter, '\tprivate readonly IFileReader _mfaReader;', '\tprivate readonly IFileReader? _mfaReader;')
replace_once(exporter, '\tpublic MFAData MfaData => (_mfaReader as MFAFileReader).mfa;', '\tpublic MFAData? MfaData => (_mfaReader as MFAFileReader)?.mfa;')
replace_once(exporter, '\tpublic Exporter(IFileReader ccnReader, IFileReader mfaReader, DirectoryInfo runtimeBasePath, DirectoryInfo outputPath)', '\tpublic Exporter(IFileReader ccnReader, IFileReader? mfaReader, DirectoryInfo runtimeBasePath, DirectoryInfo outputPath)')
replace_once(base_exporter, '\tprotected MFAData MfaData => _exporter.MfaData;', '\tprotected MFAData? MfaData => _exporter.MfaData;')

# 3. Application icon export relies on editor-only MFA icon metadata.
replace_once(
    icon_exporter,
    '\tpublic override void Export()\n\t{\n\t\tWriteRawIcons();\n\t\tWriteWindowsIcons();\n\t\tWriteMacIcons();\n\t}',
    '\tpublic override void Export()\n\t{\n'
    '\t\tif (MfaData == null)\n'
    '\t\t{\n'
    '\t\t\tLogger.Log("No MFA source available; skipping application icon export.");\n'
    '\t\t\treturn;\n'
    '\t\t}\n'
    '\t\tWriteRawIcons();\n\t\tWriteWindowsIcons();\n\t\tWriteMacIcons();\n'
    '\t}'
)

# 4. The original exporter infers global-object flags from editor-only MFA frame data.
replace_once(
    object_info,
    '\t\t\t\tbool isGlobal = false;\n'
    '\t\t\t\tforeach (var frame in Exporter.Instance.MfaData.Frames)\n'
    '\t\t\t\t{\n'
    '\t\t\t\t\tforeach (var obj in frame.Items)\n'
    '\t\t\t\t\t{\n'
    '\t\t\t\t\t\tif (obj.Name != objectInfo.name || obj.ObjectType != objectInfo.ObjectType) continue;\n'
    '\n'
    '\t\t\t\t\t\tif ((obj.Flags & 4) == 4)\n'
    '\t\t\t\t\t\t{\n'
    '\t\t\t\t\t\t\tisGlobal = true;\n'
    '\t\t\t\t\t\t\tbreak;\n'
    '\t\t\t\t\t\t}\n'
    '\t\t\t\t\t}\n'
    '\n'
    '\t\t\t\t\tif (isGlobal) break;\n'
    '\t\t\t\t}',
    '\t\t\t\tbool isGlobal = false;\n'
    '\t\t\t\tvar mfaData = Exporter.Instance.MfaData;\n'
    '\t\t\t\tif (mfaData != null)\n'
    '\t\t\t\t{\n'
    '\t\t\t\t\tforeach (var frame in mfaData.Frames)\n'
    '\t\t\t\t\t{\n'
    '\t\t\t\t\t\tforeach (var obj in frame.Items)\n'
    '\t\t\t\t\t\t{\n'
    '\t\t\t\t\t\t\tif (obj.Name != objectInfo.name || obj.ObjectType != objectInfo.ObjectType) continue;\n'
    '\n'
    '\t\t\t\t\t\t\tif ((obj.Flags & 4) == 4)\n'
    '\t\t\t\t\t\t\t{\n'
    '\t\t\t\t\t\t\t\tisGlobal = true;\n'
    '\t\t\t\t\t\t\t\tbreak;\n'
    '\t\t\t\t\t\t\t}\n'
    '\t\t\t\t\t\t}\n'
    '\n'
    '\t\t\t\t\t\tif (isGlobal) break;\n'
    '\t\t\t\t\t}\n'
    '\t\t\t\t}'
)

# 5. PakBuilder uses CCN banks for resources; MFA data was read but unused.
replace_once(pak_builder, '\tpublic void Build(CCNFileReader ccnReader, MFAFileReader mfaReader, DirectoryInfo outputPath)', '\tpublic void Build(CCNFileReader ccnReader, MFAFileReader? mfaReader, DirectoryInfo outputPath)')
replace_once(pak_builder, '\tvoid BuildMainPak(CCNFileReader ccnReader, MFAFileReader mfaReader, DirectoryInfo outputPath)', '\tvoid BuildMainPak(CCNFileReader ccnReader, MFAFileReader? mfaReader, DirectoryInfo outputPath)')
replace_once(pak_builder, '\t\tvar gameData = ccnReader.getGameData();\n\t\tvar mfaData = mfaReader.getMfaData();\n', '\t\tvar gameData = ccnReader.getGameData();\n')
replace_once(pak_builder, '\tpublic string GetMainBankHash(CCNFileReader ccnReader, MFAFileReader mfaReader)', '\tpublic string GetMainBankHash(CCNFileReader ccnReader, MFAFileReader? mfaReader)')

print("CCN-only exporter source patch applied.")
print("This does not add missing extension implementations or guarantee a working game build.")
