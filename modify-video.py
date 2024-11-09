#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
# Python program to power ffmpeg

import argcomplete, argparse
from argparse import RawTextHelpFormatter
from random import randint
from typing import NamedTuple, Literal
import subprocess
from parse_ffprobe import probe, Input, Stream, StreamType
import os
import sys
from random import randint
#from libs.modify_video_args import prepare_args, Args
from typing import Literal
from dataclasses import dataclass, replace, field

parser = argparse.ArgumentParser(
    prog='modify-video',
    description='Opinionated tool to power ffmpeg, and produce reasonable media files from DVD rips and other sources',
    epilog='Text at the bottom of help',
    formatter_class=RawTextHelpFormatter)

parser.add_argument('filename', 
    help='the input file')

parser.add_argument('-S', '--sub-files',
    nargs='+',
    help='Additional subtitle files to include\n\n')

parser.add_argument('-A', '--audio-files',
    nargs='+',
    help='Additional audio tracks to include.\n' + 
        'If a file includes subtitle and audio tracks, include it as both\n\n')

parser.add_argument('-i', '--deinterlace',
    action='store_true',
    help='Deinterlace the input video whilst transcoding\n\n')

parser.add_argument('-r', '--dry-run',
    action='store_true',
    help='Don\'t actually call ffmpeg, just build the command and print it\n\n')

parser.add_argument('-v', '--video-codecs', 
    nargs='+',
    metavar="C",
    help='codecs to use in video output\n' + 
        'All streams will be stored in all requested formats. \n' +
        'If no formats are requested video streams will just be copied\n\n',
    choices=['h264', 'av1', 'copy'])

parser.add_argument('-a', '--audio-codecs', 
    nargs='+',
    metavar="C",
    help='codecs to use in audio output (all streams will be stored in all formats)\n\n',
    choices=['mp3', 'aac', 'copy'])

parser.add_argument('-5', '--convert-5_1', 
    nargs='+',  
    metavar="C",
    help='Convert from 5.1 surround sound streams to stereo streams.\n' + 
        'The output will contain all 5.1 streams which are in the input, ' + 
        'plus a copy of each of them using each of the selected convertors \n' +
        'Options are:\n' + 
        '\tnightmode - a conversion optimized for clearer speech with music and effects slightly muted or\n' + 
        '\tfullmix - a relatively faithful reproduction of the 5.1 audio at current levels\n\n',
    choices=['nightmode', 'fullmix'])

parser.add_argument('--audio-metadata',
    nargs='+',
    metavar="M",
    help='Ordered list of metadata for all audio streams.\n' + 
        'Each should be either a language code, or a language-code/title. ' + 
        'If you want a stream other than the first one to the be the default, you should follow it with a *\n' +
        'Examples: . "EN", "ENG", "EN/commentary*", "EN/audio-described".\n\n')

parser.add_argument('--subtitle-metadata',
    nargs='+',  
    metavar="M",
    help='Ordered list of metadata for all text subtitle streams.\n' + 
        'Each should be either a language code, or a language-code/title. ' + 
        'If you want a stream other than the first one to the be the default, you should follow it with a *\n' +
        'If you want a stream other than the first one to the be the default, you should follow it with a *\n' +
        'Examples: . "EN", "ENG", "EN/commentary*", "EN/audio-described".\n\n')

parser.add_argument('--vobsub-metadata',
    nargs='+',  
    metavar="M",
    help='Ordered list of metadata for all vob subtitle streams.\n' + 
        'Each should be either a language code, or a language-code/title. ' + 
        'Examples: . "EN", "ENG", "EN/commentary", "EN/audio-described".\n\n')

parser.add_argument('-I', '--in-place',
    action='store_true',
    help='overwrite the first source file with the output.\n' + 
        'If not provided, a filename will be generated of the format STEM.INSET.EXT will be created\n' +
        'Where there is a video encoding stage, INSET will describe the encoding, otherwise it will be of the form temp-9999\n\n')

parser.add_argument('-O', '--outfile',
    help='Store to the specified file instead of to a temp one\n\n')

parser.add_argument('-t', '--title',
    help='Add a title to the mp4 file. If there already is one it will be overwritten\n\n')

parser.add_argument('-y', '--year',
    help='Add a year to the mp4 file. If there already is one it will be overwritten\n\n')

parser.add_argument('-d', '--description',
    help='Add a short descrption (comment) to the mp4 file. If there already is one it will be overwritten\n\n')

parser.add_argument('-s', '--synopsis',
    help='Add a longer synopsis to the mp4 file. If there already is one it will be overwritten\n\n')

parser.add_argument('-e', '--episode',
    help='Add an episode name to the mp4 file.\n' + 
        'If there already is one it will be overwritten. If an episode is provided but not  title, the episode will be stored in the title as well\n\n')

parser.add_argument('--episode-sort',
    type=int,
    help='Add an episode sort number to the mp4 file.\n' + 
        'This can be used if the episode number will not cause correct sorting. ' +
        'In general the tv app sorts by filename anyway, so this probably isn\'t useful\n\n')

parser.add_argument('--season-number',
    type=int,
    help='Add an season number to the mp4 file.\n' + 
        'In general the tv app sorts by filename anyway, so this probably isn\'t useful\n\n')

parser.add_argument('--show-name',
    help='Add a show name to the mp4 file. If there already is one it will be overwritten\n\n')

parser.add_argument('--thumbnails',
    nargs='+',
    metavar="C",
    help='Add thumbnails to the mp4 file. If there is already a thumbnail, now there will be two\n\n')

parser.add_argument('--no-fail-on-error',
    action='store_true',
    help='Normal mode is to fail on a transcode error. This disables that (for videos which you know are broken)\n\n')

argcomplete.autocomplete(parser)

class Args(NamedTuple):
    filename: str
    sub_files: list[str]
    audio_files: list[str]
    deinterlace: bool
    dry_run: bool
    video_codecs: list[Literal["h264", "av1", "copy"]]
    audio_codecs: list[Literal['aac', 'mp3', 'copy']]
    convert_5_1: list[Literal['nightmode', 'fullmix']]
    audio_metadata: str
    subtitle_metadata: list[str]
    vobsub_metadata: list[str]
    inplace: bool
    title: str
    year: str
    description: str
    synopsis: str
    episode: str
    episode_sort: int
    season_number: int
    show_name: str
    thumbnails: list[str]
    outfile: str
    no_fail_on_error: bool

def prepare_args():
    args: Args = parser.parse_args()
    args.video_codecs = args.video_codecs or [] 
    args.audio_codecs = args.audio_codecs or [] 
    args.sub_files = args.sub_files or [] 
    args.audio_files = args.audio_files or [] 
    args.thumbnails = args.thumbnails or [] 
    args.convert_5_1 = args.convert_5_1 or [] 
    args.subtitle_metadata = args.subtitle_metadata or [] 
    args.vobsub_metadata = args.vobsub_metadata or [] 
    args.audio_metadata = args.audio_metadata or [] 

    if args.deinterlace and not args.video_codecs:
        print("file cannot be deinterlaced unless it is transcoded. Select a codec")
        exit

    return args

args = prepare_args()

@dataclass
class Metadata:
    language: str
    title: str
    default: bool
    attached_pic: bool

    def parse(value: str):
        default = value.endswith("*")
        value = value[0:-1] if default else value
        parts = value.split("/")
        lang = at_or_default(parts, 0, "")
        title = at_or_default(parts, 1, "")
        return Metadata(lang, title, default, attached_pic=False)
        
@dataclass
class MappedStream:
    ### The input and source pair for this stream
    source: tuple[int, int]
    ### Is this an audio, subtitle or video stream
    type: Literal['a', 's', 'v']
    ### Within the type, what is the index of this stream
    idx: int = 0
    ### A filter for this stream
    filter: str = ""
    ### Encoder name and Arguments for this stream, to follow -c:<ID> 
    codec_args: list[str] = lambda: []
    metadata: Metadata = None
    is_vobsub: bool = False

@dataclass
class Streams:
    video: list[MappedStream] = field(default_factory=list)
    audio: list[MappedStream] = field(default_factory=list)
    subs: list[MappedStream] = field(default_factory=list)
    vob_subs: list[MappedStream] = field(default_factory=list)

    def all(self): 
        return self.video + self.audio + self.subs + self.vob_subs
    
    def add_videos(self, input: Input, codecs: list):
        for (input, stream) in get_streams(input, 'Video'):
            self.add_video(input, stream, codecs)

    def add_video(self, input: Input, stream: Stream, codecs: list):
        idx = lambda: next_idx(self.video)
        mapped = MappedStream(type='v', source=[input.number, stream.number])
        if stream.encoding == 'mjpeg': # This is a thumbail
            self.video += [ replace(mapped, idx=idx(), codec_args = ["copy"]) ]
        else:
            for codec in codecs:
                self.video += [ 
                    replace(mapped, idx=idx(), codec_args = codec_to_params(codec)) ]

    def add_thumb(self, input: Input, stream: Stream):
        idx = lambda: next_idx(self.video)
        if stream.encoding == 'mjpeg': # This is a thumbail
            metadata = Metadata(attached_pic=True, default=False, language="", title="")
            source=[input.number, stream.number]
            self.video += [ MappedStream(
                type='v', source=source, metadata=metadata, idx=idx(), codec_args = ["copy"]) ]
        else:
            print("ignoring non-jpeg thumbnail", stream)

    def add_audio(self, metadata: Metadata, input: Input, stream: Stream, codecs: list, convert_5_1s: list):
        idx = lambda: next_idx(self.audio)

        mapped = MappedStream(type='a',
            source=[input.number, stream.number],
            metadata=metadata)

        for codec in codecs:
            if stream.detail.find('6 channels') >= 0 or stream.detail.find('5.1(side)') >= 0:
                c = audio_codec_to_params(codec if codec != 'copy' else stream.encoding)
                if not c:
                    print("Audio codec is set to copy, but a transcode is required to convert from 5.1. Select an audio codec")
                    sys.exit(749)
                wc = replace(mapped, codec_args=c)
                for convert_5_1 in convert_5_1s:
                    print("adding conversion to {convert_5_1}")
                    self.audio += [ replace(wc, 
                        idx = idx(), 
                        filter = convert_5_1_to_filter(convert_5_1),
                        metadata = metadata) ]
                    metadata = metadata if metadata is None or not metadata.default else replace(metadata, default = False)
            codec = audio_codec_to_params(codec if codec != stream.encoding else 'copy')
            self.audio += [ replace(mapped, idx=idx(), codec_args=codec, metadata = metadata) ]

    def add_subtitle(self, metadata, input: Input, stream: Stream):
        self.subs += [ MappedStream(type='s', idx=next_idx(self.subs), 
            source=[input.number, stream.number], 
            codec_args = ["mov_text"], 
            metadata=metadata,
            is_vobsub=False )]

    def add_vobsub(self, metadata, input: Input, stream: Stream):
        self.vob_subs += [ MappedStream(type='s', idx=next_idx(self.vob_subs), 
            source=[input.number, stream.number], 
            codec_args = ["copy"], 
            metadata=metadata,
            is_vobsub=True )]


def dump_probe(args):
    streams = probe([ args.filename ] + args.sub_files + args.audio_files)
    for input in streams:
        print(input)
        print(input.metadata)
        for stream in input.streams:
            print(stream)
            print(stream.metadata)

next_idx = lambda list: list[-1].idx + 1 if len(list) else 0

pop_or_none = lambda list: list.pop(0) if len(list) else None

def process(args: Args):
    args.video_codecs = args.video_codecs or [ 'copy' ]
    args.audio_codecs = args.audio_codecs or [ 'copy' ]
    #args.convert_5_1 += [ 'copy' ]

    print()
    print(args)
    print()

    audio_metadata = [Metadata.parse(x) for x in args.audio_metadata]
    subtitle_metadata = [Metadata.parse(x) for x in args.subtitle_metadata]
    vobsub_metadata = [Metadata.parse(x) for x in args.vobsub_metadata]

    input_idx = 0
    all_streams : Streams = Streams()

    input = probe(args.filename, input_idx)

    all_streams.add_videos(input, args.video_codecs)

    for (input, stream) in get_streams(input, 'Audio'):
        all_streams.add_audio(pop_or_none(audio_metadata), input, stream, args.audio_codecs, args.convert_5_1)

    for (input, stream) in get_streams(input, 'Subtitle'):
        if stream.encoding=="dvd_subtitle":
            all_streams.add_vobsub(pop_or_none(vobsub_metadata), input, stream)
        else:
            all_streams.add_subtitle(pop_or_none(subtitle_metadata), input, stream)

    for input in [ probe(x, (input_idx:=input_idx+1)) for x in args.sub_files if not x is None ]:
        for (input, stream) in get_streams(input, 'Subtitle'):
            if stream.encoding=="dvd_subtitle":
                all_streams.add_vobsub(pop_or_none(vobsub_metadata), input, stream)
            else:
                all_streams.add_subtitle(pop_or_none(subtitle_metadata), input, stream)

    for input in [ probe(x, (input_idx:=input_idx+1)) for x in args.audio_files if not x is None ]:
        for (input, stream) in get_streams(input, 'Audio'):
            all_streams.add_audio(pop_or_none(audio_metadata), input, stream, args.audio_codecs, args.convert_5_1)

    for input in [ probe(x, (input_idx:=input_idx+1)) for x in args.thumbnails if not x is None ]:
        for (input, stream) in get_streams(input, 'Video'):
            all_streams.add_thumb(input, stream)

    streams = all_streams

    outfile = output_filename(args)

    print()
    for input in streams.video:
        print(input)
    for input in streams.audio:
        print(input)
    for input in streams.subs:
        print(input)
    for input in streams.vob_subs:
        print(input)
    print()

    params = [ "ffmpeg", "-hwaccel", "auto" ]

    if not args.no_fail_on_error:
        params += [ "-xerror" ]

    params += input_args(args)
    params += map_args(streams)
    params += file_metadata_args(args)
    for stream in streams.all():
        if stream.filter:
            params += [ f"-filter:{stream.type}:{stream.idx}", stream.filter ]

    if args.deinterlace:
        out += [ '-vf' 'bwdif' ]

    for stream in streams.all():
        params += [ f"-codec:{stream.type}:{stream.idx}" ] + stream.codec_args

    for stream in streams.video:
        params += stream_metadata_params(stream)

    if args.audio_metadata:
        for stream in streams.audio:
            params += stream_metadata_params(stream)

    if args.vobsub_metadata:
        for stream in streams.vob_subs:
            params += stream_metadata_params(stream)

    if args.subtitle_metadata:
        for stream in streams.subs:
            params += stream_metadata_params(stream)

    params += outfile

    print(params)

    if not args.dry_run:
        res = subprocess.run(params)
        if res.returncode==0 and args.in_place:
            os.rename(outfile[-1], args.filename[0])
            print("Amended file in-place")
        else:
            print(f"Created output file '{outfile[-1]}'")

def stream_metadata_params(stream: MappedStream):
    if stream.metadata is None:
        return []
    
    meta = stream.metadata
    addr = f"{stream.type}:{stream.idx}"

    params = []

    if meta.attached_pic:
        params += [ f"-disposition:{addr}", "attached_pic", ]
    if stream.type != "v":
        params += [ f"-disposition:{addr}", "default" if meta.default else "0", ]
    if meta.language:
        params += [ f"-metadata:s:{addr}", f"language={meta.language}" ]
    if stream.metadata.title:
        params += [ f"-metadata:s:{addr}", f"title={meta.title}" ]
    return params

### Add the main file, plus sub files and audio files as inputs
def input_args(args):
    params = ["-i", args.filename]

    for filename in args.sub_files:
        params += ["-i", filename]

    for filename in args.audio_files:
        params += ["-i", filename]

    for filename in args.thumbnails:
        params += ["-i", filename]

    return params

### Map all the streams from the main file, plus subtitles from sub files and
#   audio streams from audio files
def map_args(mapped: Streams):
    params = [ "-map_metadata", "0" ]

    for stream in mapped.all():
        [ file, stream ] = stream.source
        params += [ "-map", f"{file}:{stream}" ]

    return params


def at_or_default(l: list, idx: int, default):
    return l[idx] if l and len(l) > idx else default

def audio_codec_to_params(codec):
    return [ codec ] if ['ac3', 'aac', 'mp3', 'copy'].__contains__(codec) else []

def get_streams(input: Input, typ: StreamType):
    out = []
    for stream in input.streams:
        if stream.type == typ:
            out.append((input, stream))
    return out

def codec_to_params(codec):
    if codec=='av1':
        return [ 
            'libsvtav1', 
            '-preset', '6', 
            '-crf', '32', 
            '-g', '240', 
            '-pix_fmt', 'yuv420p10le', 
            '-svtav1-params', 'tune=0:film-grain=8'
        ]
    elif codec=='h264':
        return [ 'h264_nvenc', '-rc', 'constqp' ]
    elif codec=='copy':
        return [ 'copy' ]

### Build an output filename, using a random string, or the video codecs if 
#   reencoding
def output_filename(args: Args):
    if args.outfile:
        return [ "--", args.outfile ]
    
    name, _ext = os.path.splitext(args.filename)
    if args.video_codecs != ["copy"]:
        inset = "-".join(args.video_codecs)
    else:
        n = randint(1000, 9999)
        inset = f"temp-{n}"
    return [ "--", f"{name}.{inset}.mp4" ]

def convert_5_1_to_filter(convert_5_1):
    if convert_5_1 == "nightmode":
        return "pan=stereo|c0=c2+0.30*c0+0.30*c4|c1=c2+0.30*c1+0.30*c5"
    elif convert_5_1 == "fullmix":
        return f"pan=stereo|c0=0.5*c2+0.707*c0+0.707*c4+0.5*c3|c1=0.5*c2+0.707*c1+0.707*c5+0.5*c3"

def file_metadata_args(args):
    out = []

    if args.title:
        title = args.title.replace('\"', '\\\"')
        out += [ "-metadata", f"title=\"{title}\"" ]
    if args.year:
        year = args.year.replace('\"', '\\\"')
        out += [ "-metadata", f"year=\"{year}\"" ]
    if args.description:
        description = args.description.replace('"', '\\"')
        out += [ "-metadata", f"description=\"{description}\"" ]
    if args.synopsis:
        synopsis = args.synopsis.replace('"', '\\"')
        out += [ "-metadata", f"synopsis=\"{synopsis}\"" ]
    if args.episode:
        episode = args.episode.replace('"', '\\"')
        out += [ "-metadata", f"episode_id=\"{episode}\"" ]
    if args.episode_sort:
        out += [ "-metadata", f"episode_sort={args.episode_sort}" ]
    if args.season_number:
        out += [ "-metadata", f"season_number={args.season_number}" ]
    if args.show_name:
        show_name = args.show_name.replace('"', '\\"')
        out += [ "-metadata", f"show=\"{show_name}\"" ]

    return out

process(args)
