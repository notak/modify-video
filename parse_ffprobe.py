#!/usr/bin/env python3

import subprocess
from dataclasses import dataclass, field
from typing import Literal

StreamType = Literal['Video', 'Audio', 'Subtitle']

### Details of a stream within an input to ffmpeg, as determined by a call to 
#   ffprobe
@dataclass
class Stream:
    number: str = ""
    type: StreamType = ""
    encoding: str = ""
    detail: str = ""
    metadata: dict = field(default_factory=dict)
    default: bool = False

    def __str__(self):
        star = "*" if self.default else " "
        out = f"{star} {self.number} {self.type} {self.encoding}\n     detail: {self.detail}\n"
        for k, v in self.metadata.items():
            if not ["handler_name", "vendor_id", "encoder"].__contains__(k):
                out += f"     {k}: {v}\n"
        return out


## Details of an input to ffmpeg, as determined by a call to ffprobe
@dataclass
class Input:
    number: str = ""
    filename: str = ""
    duration: str = ""
    streams: list[Stream] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __str__(self):
        out = f"Input {self.number} ({self.duration}) {self.filename}\n"
        for k, v in self.metadata.items():
            if not ["major_brand", "minor_version", "compatible_brands", "encoder"].__contains__(k):
                out += f"   {k}: {v}\n"
        for s in self.streams:
            out += f"{s}"
        return out

### Call ffprobe with the given input files, and return the output in a 
#   structured list of inputs and streams
def probe(filename: str, number: int):

    args = [ "ffprobe" , "-i", filename]

    print("probing input files")
    print(args)

    res = subprocess.run(args, capture_output=True)
    lines = list(map(lambda x: x.decode("utf-8"), res.stderr.splitlines()))

    line = ""
    while len(lines)>0 and not line.startswith('Input #'):
        line = lines.pop(0)
    input = Input(number = number, filename= line[line.rfind('\'', 0, -2):-1])
    while lines.__len__() > 0 and lines[0].startswith('  '):
        line = lines.pop(0)
        if line.startswith('  Metadata'):
            while line.__len__() and lines[0].startswith('    '):
                line = lines.pop(0)
                [ key, val ] = line.split(':', 1)
                input.metadata[key.strip()] = val.strip()
        elif line.startswith('  Duration'):
            input.duration = line[12:23]
        elif line.startswith('  Stream'):
            input.streams.append(extract_stream_info(line, lines))

    print(input)

    return input

def extract_stream_info(line, lines):
    stream = Stream(number=line[12:13])
    line = line[13:]
    [ _, type, rest ] = line.split(':', 2)
    parts = rest.strip().split(' ', 1)
    encoding = parts[0] if len(parts) >0 else ""
    detail = parts[1] if len(parts) > 1 else ""
    if detail.find("(default)") >= 0:
        stream.default = True
        detail = detail.replace("(default)", "")
    stream.type = type.strip()
    stream.encoding = encoding.strip()
    stream.detail = detail.strip()
    while lines.__len__() > 0 and lines[0].startswith('    '):
        line = lines.pop(0)
        if line.startswith('    Metadata'):
            while lines.__len__() > 0 and lines[0].startswith('      '):
                line = lines.pop(0)
                [ key, val ] = line.split(':', 1)
                stream.metadata[key.strip()] = val.strip()
    return stream
