#!/usr/bin/env python3
import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
HOME = Path.home()
YOUTUBE_CONFIG_DIR = HOME / ".config/youtube"
DEFAULT_TOKEN = HOME / ".config/youtube/token.json"
DEFAULT_OUTPUT_DIR = HOME / ".codex/projects/daily-report/youtube-liked-videos/output"


def resolve_client_secret(client_secret: Optional[Path]) -> Path:
    if client_secret:
        return client_secret
    matches = sorted(YOUTUBE_CONFIG_DIR.glob("client_secret_*.json"))
    if not matches:
        raise FileNotFoundError(f"No YouTube client secret found under {YOUTUBE_CONFIG_DIR}")
    return matches[0]


def load_credentials(client_secret: Path, token_path: Path) -> Credentials:
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
        creds = flow.run_local_server(port=0, open_browser=False)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    token_path.chmod(0o600)
    return creds


def fetch_liked_videos(youtube) -> list[dict]:
    channels = youtube.channels().list(part="contentDetails", mine=True).execute()
    items = channels.get("items", [])
    if not items:
        raise RuntimeError("No channel was returned for the authenticated account.")

    liked_playlist_id = (
        items[0]
        .get("contentDetails", {})
        .get("relatedPlaylists", {})
        .get("likes")
    )
    if not liked_playlist_id:
        raise RuntimeError("Could not find the liked videos playlist ID.")

    videos = []
    page_token = None
    while True:
        response = (
            youtube.playlistItems()
            .list(
                part="snippet,contentDetails",
                playlistId=liked_playlist_id,
                maxResults=50,
                pageToken=page_token,
            )
            .execute()
        )
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            content = item.get("contentDetails", {})
            video_id = content.get("videoId", "")
            videos.append(
                {
                    "position": len(videos) + 1,
                    "title": snippet.get("title", ""),
                    "channel": snippet.get("videoOwnerChannelTitle", "")
                    or snippet.get("channelTitle", ""),
                    "video_id": video_id,
                    "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
                    "published_at": content.get("videoPublishedAt", ""),
                    "liked_playlist_added_at": snippet.get("publishedAt", ""),
                    "description": snippet.get("description", ""),
                }
            )

        page_token = response.get("nextPageToken")
        if not page_token:
            return videos


def write_outputs(videos: list[dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "liked_videos.json"
    json_path.write_text(
        json.dumps(videos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    csv_path = output_dir / "liked_videos.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "position",
                "title",
                "channel",
                "video_id",
                "url",
                "published_at",
                "liked_playlist_added_at",
            ],
        )
        writer.writeheader()
        for video in videos:
            writer.writerow({key: video[key] for key in writer.fieldnames})

    md_path = output_dir / "liked_videos.md"
    lines = ["# YouTube Liked Videos", ""]
    for video in videos:
        title = video["title"].replace("[", "\\[").replace("]", "\\]")
        channel = video["channel"]
        lines.append(f"- [{title}]({video['url']}) - {channel}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Fetched {len(videos)} liked videos")
    print(f"JSON: {json_path}")
    print(f"CSV:  {csv_path}")
    print(f"MD:   {md_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-secret", type=Path, default=None)
    parser.add_argument("--token", type=Path, default=DEFAULT_TOKEN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    creds = load_credentials(resolve_client_secret(args.client_secret), args.token)
    youtube = build("youtube", "v3", credentials=creds)
    write_outputs(fetch_liked_videos(youtube), args.output_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"YouTube liked videos failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
