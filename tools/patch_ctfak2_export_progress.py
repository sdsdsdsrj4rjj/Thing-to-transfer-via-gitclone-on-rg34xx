#!/usr/bin/env python3
"""Patch CTFAK 2.0 with per-frame/event progress markers for a large MFA export."""
from pathlib import Path

def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8-sig")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old[:100]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8-sig", newline="")

root = Path("CTFAK2.0")
ft = root / "Plugins/CTFAK.Decompiler/FTDecompile.cs"
mfa = root / "Core/CTFAK.Core/MFA/MFAData.cs"

# Tell us whether a pause is happening during frame conversion or during final file writing.
replace_once(
    ft,
    "                var frame = game.frames[a];",
    '                var frame = game.frames[a];\n'
    '                Logger.Log($"BEGIN frame {a + 1}/{game.frames.Count}: {frame.name}; objects={frame.objects?.Count ?? 0}; eventGroups={frame.events?.Items.Count ?? 0}", true, ConsoleColor.Cyan);'
)
replace_once(
    ft,
    '                if (frame.flags["DontInclude"]) continue;',
    '                if (frame.flags["DontInclude"]) { Logger.Log($"SKIP frame {a + 1}/{game.frames.Count}: {frame.name} (DontInclude)"); continue; }'
)
replace_once(
    ft,
    "                    for (int i = 0; i < frame.objects.Count; i++)\n                    {\n                        var instance = frame.objects[i];",
    "                    for (int i = 0; i < frame.objects.Count; i++)\n"
    "                    {\n"
    "                        if (i % 100 == 0) Logger.Log($\"Frame {a + 1}: translating instance {i + 1}/{frame.objects.Count}\", false);\n"
    "                        var instance = frame.objects[i];"
)
replace_once(
    ft,
    "                            for (int eg = 0; eg < newFrame.Events.Items.Count; eg++)//foreach (EventGroup eventGroup in newFrame.Events.Items)\n"
    "                            {\n"
    "                                var eventGroup = newFrame.Events.Items[eg];",
    "                            for (int eg = 0; eg < newFrame.Events.Items.Count; eg++)//foreach (EventGroup eventGroup in newFrame.Events.Items)\n"
    "                            {\n"
    "                                var eventGroup = newFrame.Events.Items[eg];\n"
    "                                if (eg % 10 == 0 || eg == newFrame.Events.Items.Count - 1) Logger.Log($\"Frame {a + 1}: event group {eg + 1}/{newFrame.Events.Items.Count}, actions={eventGroup.Actions.Count}, conditions={eventGroup.Conditions.Count}\", true, ConsoleColor.Cyan);"
)
replace_once(
    ft,
    "                                foreach (Action action in eventGroup.Actions)\n"
    "                                {\n"
    "                                    if (action.ObjectType == -5 && action.Num == 0)",
    "                                int actionIndex = 0;\n"
    "                                foreach (Action action in eventGroup.Actions)\n"
    "                                {\n"
    "                                    if (actionIndex % 20 == 0) Logger.Log($\"Frame {a + 1}, group {eg + 1}: action {actionIndex + 1}/{eventGroup.Actions.Count}\", false);\n"
    "                                    actionIndex++;\n"
    "                                    if (action.ObjectType == -5 && action.Num == 0)"
)
replace_once(
    ft,
    "                                foreach (Condition cond in eventGroup.Conditions)\n"
    "                                {\n"
    "                                    foreach (var qualifer in qualifiers)",
    "                                int conditionIndex = 0;\n"
    "                                foreach (Condition cond in eventGroup.Conditions)\n"
    "                                {\n"
    "                                    if (conditionIndex % 20 == 0) Logger.Log($\"Frame {a + 1}, group {eg + 1}: condition {conditionIndex + 1}/{eventGroup.Conditions.Count}\", false);\n"
    "                                    conditionIndex++;\n"
    "                                    foreach (var qualifer in qualifiers)"
)
replace_once(
    ft,
    '                        Logger.Log($"Translating frame {frame.name} - {a}");\n                        mfa.Frames.Add(newFrame);',
    '                        Logger.Log($"Finishing frame {a + 1}/{game.frames.Count}: {frame.name}");\n'
    '                        mfa.Frames.Add(newFrame);'
)

# Mark large bank and serialization stages in the final MFA writer as well.
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

print("Patched CTFAK 2.0 with per-frame/event and final-writer diagnostics.")
