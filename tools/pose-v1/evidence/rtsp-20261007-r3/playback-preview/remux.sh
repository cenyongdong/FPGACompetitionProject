#!/bin/sh
# File operations only. Run after successful encode review in results folder.
set -eu
test -f video.h264
test ! -e review.mp4
timeout --kill-after=3s 20s ffprobe -v error -count_frames -show_entries stream=codec_name,profile,width,height,r_frame_rate,avg_frame_rate,nb_read_frames,color_range,color_space,color_transfer,color_primaries -of json video.h264 > probe-h264.json 2> probe-h264.stderr.log
# Raw Annex-B does not carry container PTS; reconstruct nominal 10fps for
# this offline review clip only. Live RTSP must use captured timestamps.
timeout --kill-after=3s 20s ffmpeg -nostdin -n -loglevel warning -fflags +genpts -r 10 -i video.h264 -c:v copy -movflags +faststart review.mp4 > remux.stdout.log 2> remux.stderr.log
timeout --kill-after=3s 20s ffprobe -v error -count_frames -show_entries stream=codec_name,profile,width,height,r_frame_rate,avg_frame_rate,nb_read_frames,pix_fmt,color_range,color_space,color_transfer,color_primaries:format=duration,size -of json review.mp4 > probe-mp4.json 2> probe-mp4.stderr.log
sha256sum video.h264 review.mp4 > video-transfer.sha256
