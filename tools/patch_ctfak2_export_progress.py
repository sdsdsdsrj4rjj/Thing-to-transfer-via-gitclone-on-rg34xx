#!/usr/bin/env python3
"""Patch CTFAK 2.0 to show where MFA export time is being spent."""
from pathlib import Path

def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8-sig")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old[:80]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8-sig", newline="")

root = Path("CTFAK2.0")
ft = root / "Plugins/CTFAK.Decompiler/FTDecompile.cs"
mfa = root / "Core/CTFAK.Core/MFA/MFAData.cs"

replace_once(
    ft,
    '            mfa.Write(new ByteWriter(new FileStream($"Dumps\\\\{outPath}\\\\{Path.GetFileNameWithoutExtension(game.editorFilename)}.mfa", FileMode.Create)));',
    '            var mfaOutputPath = $"Dumps\\\\{outPath}\\\\{Path.GetFileNameWithoutExtension(game.editorFilename)}.mfa";\n'
    '            Logger.Log($"All frame conversions finished. Preparing output: {mfa.Frames.Count} frames, {mfa.Images.Items.Count} images, {mfa.Sounds.Items.Count} sounds, {mfa.Fonts.Items.Count} fonts.");\n'
    '            Logger.Log($"Starting final MFA write: {mfaOutputPath}. This stage can take a while; the output file is being built now.");\n'
    '            var mfaWriteStarted = DateTime.UtcNow;\n'
    '            mfa.Write(new ByteWriter(new FileStream(mfaOutputPath, FileMode.Create)));\n'
    '            Logger.Log($"Final MFA write completed in {(DateTime.UtcNow - mfaWriteStarted).TotalSeconds:F1} seconds.");'
)

# Emit clear phase markers around the large asset banks.
for old, new in [
    ('            Writer.WriteAscii(FontBankId);\n            Fonts.Write(Writer);',
     '            Logger.Log($"Writing font bank ({Fonts.Items.Count} items)...");\n            Writer.WriteAscii(FontBankId);\n            Fonts.Write(Writer);'),
    ('            Writer.WriteAscii(SoundBankId);\n            Sounds.Write(Writer);',
     '            Logger.Log($"Writing sound bank ({Sounds.Items.Count} items)...");\n            Writer.WriteAscii(SoundBankId);\n            Sounds.Write(Writer);'),
    ('            Writer.WriteAscii(MusicBankId);\n            Writer.WriteInt32(0);',
     '            Logger.Log("Writing music bank...");\n            Writer.WriteAscii(MusicBankId);\n            Writer.WriteInt32(0);'),
    ('            Writer.WriteAscii(ImageBankId);\n            \n            Icons.Write(Writer);',
     '            Logger.Log($"Writing icon bank ({Icons.Items.Count} items)...");\n            Writer.WriteAscii(ImageBankId);\n            \n            Icons.Write(Writer);'),
    ('            Writer.WriteAscii(ImageBankId);\n            Images.Write(Writer);',
     '            Logger.Log($"Writing image bank ({Images.Items.Count} items)...");\n            Writer.WriteAscii(ImageBankId);\n            Images.Write(Writer);'),
    ('            Writer.WriteInt32(Frames.Count); //frame',
     '            Logger.Log($"Writing {Frames.Count} converted frame records...");\n            Writer.WriteInt32(Frames.Count); //frame'),
    ('            foreach (MFAFrame frame in Frames)\n            {\n                Writer.WriteUInt32((uint)(startPos + newWriter.Tell()));\n                frame.Write(newWriter);\n            }',
     '            foreach (MFAFrame frame in Frames)\n            {\n                Logger.Log($"Serializing frame record {frame.Handle + 1}/{Frames.Count}: {frame.Name}");\n                Writer.WriteUInt32((uint)(startPos + newWriter.Tell()));\n                frame.Write(newWriter);\n            }'),
    ('            Writer.WriteWriter(newWriter);\n            Chunks.Write(Writer);',
     '            Logger.Log("Appending serialized frame records and final MFA chunks...");\n            Writer.WriteWriter(newWriter);\n            Chunks.Write(Writer);'),
]:
    replace_once(mfa, old, new)

print("Patched CTFAK 2.0 export progress instrumentation successfully.")
