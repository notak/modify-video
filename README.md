# modify-video
Wrapper for ffmpeg to (hopefully) make common tasks easier to set up

## What is it?
The things which are made easier are the things I most often want to do, following a couple of principles:

- We output mp4 files
- Everything that goes in is mapped and retained unless it's specifically excluded

## What is it good for?
- adding metadata
- adding stream metadata (subtitle/audio languages etc)
- adding thumbnails
- adding subtitles
- adding audio tracks (additional languages, audio-described)
- downmapping 5.1 audio to stereo, including the ability to map to night mode
- it will probably also map MP2/AVI to mp4 or av1

# What might well get added?
- cropping out letterboxing
- anything else that starts annoying me
- ability to create a regex search for input files which can be used compose names of other input files and output file, so a whole directory can bbe processed at once

## Are there other tools which can do all this?
Probably. AtomicParsley is good for the tagging, and obviously you can already do all of this direct with ffmpeg. 

There are probably also other scripts that this this wrapping. Loads of people have struggled with ffmpeg command line options, and we aren't the sort of people who bother to check whether the problem has already been solved before we start writing (awful) Python
