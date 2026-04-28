import argparse
import csv
import json
import re
import shutil
import subprocess
import time
from datetime import datetime
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

import requests


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

PLACEHOLDER = "no_video"

FIELDNAMES = [
    "scrape_date",
    "asin",
    "product_url",
    "has_product_video",
    "video_count_detected",
    "video_thumbnail_url",
    "video_url",
    "local_video_path",
    "local_video_thumbnail_path",
    "local_video_cover_path",
    "local_video_frame_paths",
    "video_frame_extraction_status",
    "video_extraction_status",
]


def asin_from_url_or_value(value):
    value = value.strip()
    asin_match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", value)
    if asin_match:
        return asin_match.group(1)
    if re.fullmatch(r"[A-Z0-9]{10}", value):
        return value
    return ""


def product_url_for_asin(asin):
    return f"https://www.amazon.in/dp/{asin}"


def unique(values):
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def extract_videos_from_html(html):
    text = unescape(html)

    video_urls = re.findall(
        r'https://m\.media-amazon\.com/images/S/[^"\s<>]+?\.mp4/productVideoOptimized\.mp4',
        text,
    )
    if not video_urls:
        video_urls = re.findall(r'https?://[^"\s<>]+?\.mp4(?:\?[^"\s<>]*)?', text)

    thumbnail_urls = re.findall(
        r'https://m\.media-amazon\.com/images/S/[^"\s<>]+?\.mp4/r/[^"\s<>]+?\.(?:JPG|jpg|PNG|png)',
        text,
    )

    total_count_values = re.findall(r"totalVideoCount['\"]?\s*[:=]\s*['\"]?(\d+)", text)
    detected_count = max([int(value) for value in total_count_values], default=0)
    video_urls = unique(video_urls)
    thumbnail_urls = unique(thumbnail_urls)

    if video_urls and detected_count == 0:
        detected_count = len(video_urls)

    return {
        "video_urls": video_urls,
        "thumbnail_urls": thumbnail_urls,
        "video_count_detected": detected_count,
    }


def download_file(session, url, output_path, delay=0.5):
    response = session.get(url, timeout=40)
    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    time.sleep(delay)
    return output_path


def extension_from_url(url, default):
    suffix = Path(urlparse(url).path).suffix
    return suffix if suffix else default


def run_media_command(command):
    return subprocess.run(command, check=True, capture_output=True, text=True)


def video_duration_seconds(video_path):
    if not shutil.which("ffprobe"):
        return None

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    result = run_media_command(command)
    try:
        duration = float(result.stdout.strip())
    except ValueError:
        return None
    return duration if duration > 0 else None


def extract_video_images_with_imageio(video_path, out_dir, asin, frame_count):
    try:
        import imageio.v2 as imageio
    except ImportError:
        return {
            "local_video_cover_path": PLACEHOLDER,
            "local_video_frame_paths": PLACEHOLDER,
            "video_frame_extraction_status": "video_frame_dependency_missing",
        }

    out_dir.mkdir(parents=True, exist_ok=True)
    cover_path = out_dir / f"{asin}_video_cover.jpg"
    frame_paths = []

    try:
        reader = imageio.get_reader(str(video_path))
        metadata = reader.get_meta_data()
        fps = float(metadata.get("fps") or 0)
        duration = float(metadata.get("duration") or 0)
        total_frames = int(duration * fps) if duration > 0 and fps > 0 else 0
        if total_frames <= 0:
            try:
                total_frames = reader.count_frames()
            except (RuntimeError, TypeError, ValueError):
                total_frames = frame_count + 1

        cover_frame = reader.get_data(0)
        imageio.imwrite(cover_path, cover_frame)

        if frame_count > 0:
            frame_indexes = [
                max(0, min(total_frames - 1, round(total_frames * (index + 1) / (frame_count + 1))))
                for index in range(frame_count)
            ]
        else:
            frame_indexes = []

        for index, frame_index in enumerate(frame_indexes, start=1):
            frame_path = out_dir / f"{asin}_video_frame_{index:02d}.jpg"
            frame = reader.get_data(frame_index)
            imageio.imwrite(frame_path, frame)
            frame_paths.append(str(frame_path))
    except Exception as error:
        return {
            "local_video_cover_path": str(cover_path) if cover_path.exists() else PLACEHOLDER,
            "local_video_frame_paths": "|".join(frame_paths) if frame_paths else PLACEHOLDER,
            "video_frame_extraction_status": f"extract_failed:{error.__class__.__name__}",
        }
    finally:
        try:
            reader.close()
        except UnboundLocalError:
            pass

    return {
        "local_video_cover_path": str(cover_path) if cover_path.exists() else PLACEHOLDER,
        "local_video_frame_paths": "|".join(frame_paths) if frame_paths else PLACEHOLDER,
        "video_frame_extraction_status": "extracted" if cover_path.exists() or frame_paths else "no_frames_written",
    }


def extract_video_images_with_ffmpeg(video_path, out_dir, asin, frame_count):
    if not shutil.which("ffmpeg"):
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    cover_path = out_dir / f"{asin}_video_cover.jpg"
    frame_paths = []

    try:
        run_media_command(
            [
                "ffmpeg",
                "-y",
                "-ss",
                "0",
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(cover_path),
            ]
        )

        duration = video_duration_seconds(video_path)
        if duration:
            timestamps = [duration * (index + 1) / (frame_count + 1) for index in range(frame_count)]
        else:
            timestamps = [index + 1 for index in range(frame_count)]

        for index, timestamp in enumerate(timestamps, start=1):
            frame_path = out_dir / f"{asin}_video_frame_{index:02d}.jpg"
            run_media_command(
                [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    f"{timestamp:.3f}",
                    "-i",
                    str(video_path),
                    "-frames:v",
                    "1",
                    "-q:v",
                    "2",
                    str(frame_path),
                ]
            )
            if frame_path.exists():
                frame_paths.append(str(frame_path))
    except subprocess.CalledProcessError as error:
        return {
            "local_video_cover_path": str(cover_path) if cover_path.exists() else PLACEHOLDER,
            "local_video_frame_paths": "|".join(frame_paths) if frame_paths else PLACEHOLDER,
            "video_frame_extraction_status": f"extract_failed:{error.returncode}",
        }

    return {
        "local_video_cover_path": str(cover_path) if cover_path.exists() else PLACEHOLDER,
        "local_video_frame_paths": "|".join(frame_paths) if frame_paths else PLACEHOLDER,
        "video_frame_extraction_status": "extracted" if cover_path.exists() or frame_paths else "no_frames_written",
    }


def extract_video_images(video_path, out_dir, asin, frame_count=3):
    ffmpeg_record = extract_video_images_with_ffmpeg(video_path, out_dir, asin, frame_count)
    if ffmpeg_record:
        return ffmpeg_record
    return extract_video_images_with_imageio(video_path, out_dir, asin, frame_count)


def extract_product_video(
    session,
    asin_or_url,
    out_dir,
    download=True,
    delay=0.5,
    extract_frames=True,
    frame_count=3,
):
    asin = asin_from_url_or_value(asin_or_url)
    if not asin:
        raise ValueError(f"Could not infer ASIN from input: {asin_or_url}")

    product_url = product_url_for_asin(asin)
    response = session.get(product_url, timeout=30)
    response.raise_for_status()

    extracted = extract_videos_from_html(response.text)
    video_url = extracted["video_urls"][0] if extracted["video_urls"] else PLACEHOLDER
    thumbnail_url = extracted["thumbnail_urls"][0] if extracted["thumbnail_urls"] else PLACEHOLDER

    local_video_path = PLACEHOLDER
    local_thumbnail_path = PLACEHOLDER
    frame_record = {
        "local_video_cover_path": PLACEHOLDER,
        "local_video_frame_paths": PLACEHOLDER,
        "video_frame_extraction_status": "not_applicable",
    }
    status = "no_video_found"

    if video_url != PLACEHOLDER:
        status = "video_found"
        if download:
            video_path = out_dir / f"{asin}_product_video{extension_from_url(video_url, '.mp4')}"
            local_video_path = str(download_file(session, video_url, video_path, delay))
            if thumbnail_url != PLACEHOLDER:
                thumbnail_path = out_dir / f"{asin}_video_thumbnail{extension_from_url(thumbnail_url, '.jpg')}"
                local_thumbnail_path = str(download_file(session, thumbnail_url, thumbnail_path, delay))
            if extract_frames:
                frame_record = extract_video_images(
                    video_path=video_path,
                    out_dir=out_dir,
                    asin=asin,
                    frame_count=frame_count,
                )
            else:
                frame_record["video_frame_extraction_status"] = "disabled"
            status = "downloaded"

    return {
        "scrape_date": datetime.now().isoformat(timespec="seconds"),
        "asin": asin,
        "product_url": product_url,
        "has_product_video": "yes" if video_url != PLACEHOLDER else "no",
        "video_count_detected": extracted["video_count_detected"],
        "video_thumbnail_url": thumbnail_url,
        "video_url": video_url,
        "local_video_path": local_video_path,
        "local_video_thumbnail_path": local_thumbnail_path,
        **frame_record,
        "video_extraction_status": status,
    }


def write_outputs(record, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{record['asin']}_video_record.csv"
    json_path = out_dir / f"{record['asin']}_video_record.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerow(record)

    json_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return csv_path, json_path


def main():
    parser = argparse.ArgumentParser(description="Extract one Amazon product video or write no_video placeholders.")
    parser.add_argument("asin_or_url", help="Amazon ASIN or product URL")
    parser.add_argument("--out-dir", default="scraped/product_videos", help="Output directory")
    parser.add_argument("--no-download", action="store_true", help="Only record video URLs, do not download media")
    parser.add_argument("--no-extract-frames", action="store_true", help="Do not extract cover/frame images from downloaded videos")
    parser.add_argument("--frame-count", type=int, default=3, help="Number of inner video frames to extract")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between media downloads")
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    out_dir = Path(args.out_dir)

    record = extract_product_video(
        session=session,
        asin_or_url=args.asin_or_url,
        out_dir=out_dir,
        download=not args.no_download,
        delay=args.delay,
        extract_frames=not args.no_extract_frames,
        frame_count=args.frame_count,
    )
    csv_path, json_path = write_outputs(record, out_dir)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    print(f"Saved CSV: {csv_path}")
    print(f"Saved JSON: {json_path}")


if __name__ == "__main__":
    main()
