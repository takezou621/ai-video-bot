"""
Cleanup Script - Manages disk space by removing temporary and old files
"""
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

def get_dir_size(path: Path) -> int:
    """Get directory size in bytes"""
    total = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
    except Exception as e:
        print(f"Warning: Error calculating size for {path}: {e}")
    return total

def format_size(bytes: int) -> str:
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f}{unit}"
        bytes /= 1024.0
    return f"{bytes:.1f}TB"

def cleanup_video_temp_files(video_dir: Path, dry_run: bool = False):
    """
    Clean up temporary files from a video directory

    Args:
        video_dir: Path to video directory (e.g., outputs/2025-12-13/video_001)
        dry_run: If True, only report what would be deleted
    """
    deleted_size = 0
    deleted_count = 0

    # Delete frames directory (largest temp files)
    frames_dir = video_dir / "frames"
    if frames_dir.exists():
        size = get_dir_size(frames_dir)
        if dry_run:
            print(f"  Would delete: {frames_dir} ({format_size(size)})")
        else:
            try:
                shutil.rmtree(frames_dir, ignore_errors=True)
                print(f"  Deleted: {frames_dir} ({format_size(size)})")
            except Exception as e:
                print(f"  Warning: Could not delete {frames_dir}: {e}")
        deleted_size += size
        deleted_count += 1

    # Delete chunk WAV files
    chunk_files = list(video_dir.glob("chunk_*.wav"))
    for chunk_file in chunk_files:
        size = chunk_file.stat().st_size
        if dry_run:
            print(f"  Would delete: {chunk_file.name} ({format_size(size)})")
        else:
            chunk_file.unlink()
        deleted_size += size
        deleted_count += 1

    # Delete raw audio files
    raw_files = list(video_dir.glob("*.raw"))
    for raw_file in raw_files:
        size = raw_file.stat().st_size
        if dry_run:
            print(f"  Would delete: {raw_file.name} ({format_size(size)})")
        else:
            raw_file.unlink()
        deleted_size += size
        deleted_count += 1

    # Delete concat list files
    concat_files = list(video_dir.glob("*_concat.txt")) + list(video_dir.glob("audio_list.txt"))
    for concat_file in concat_files:
        size = concat_file.stat().st_size
        if dry_run:
            print(f"  Would delete: {concat_file.name} ({format_size(size)})")
        else:
            concat_file.unlink()
        deleted_size += size
        deleted_count += 1

    return deleted_count, deleted_size

def cleanup_all_temp_files(dry_run: bool = False):
    """Clean up all temporary files from all videos"""
    outputs_dir = Path("outputs")

    if not outputs_dir.exists():
        print("No outputs directory found")
        return 0, 0

    total_count = 0
    total_size = 0

    # Find all video directories
    video_dirs = []
    for date_dir in outputs_dir.glob("????-??-??"):
        for video_dir in date_dir.glob("video_*"):
            video_dirs.append(video_dir)

    print(f"Found {len(video_dirs)} video directories")

    for video_dir in video_dirs:
        count, size = cleanup_video_temp_files(video_dir, dry_run)
        if count > 0:
            total_count += count
            total_size += size

    return total_count, total_size

def cleanup_old_videos(days: int = 30, dry_run: bool = False):
    """
    Delete videos older than specified days

    Args:
        days: Delete videos older than this many days
        dry_run: If True, only report what would be deleted
    """
    outputs_dir = Path("outputs")

    if not outputs_dir.exists():
        print("No outputs directory found")
        return 0, 0

    cutoff_date = datetime.now() - timedelta(days=days)

    deleted_count = 0
    deleted_size = 0

    # Find all date directories
    for date_dir in outputs_dir.glob("????-??-??"):
        try:
            # Parse date from directory name
            dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")

            if dir_date < cutoff_date:
                size = get_dir_size(date_dir)
                if dry_run:
                    print(f"  Would delete: {date_dir} ({format_size(size)})")
                else:
                    shutil.rmtree(date_dir)
                    print(f"  Deleted: {date_dir} ({format_size(size)})")
                deleted_count += 1
                deleted_size += size
        except ValueError:
            # Skip directories that don't match date format
            continue

    return deleted_count, deleted_size

def cleanup_docker(dry_run: bool = False):
    """Clean up Docker images, containers, and build cache"""
    if dry_run:
        print("  Docker cleanup (dry run - checking space):")
        result = subprocess.run(
            ["docker", "system", "df"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return 0
    else:
        print("  Cleaning up Docker...")
        result = subprocess.run(
            ["docker", "system", "prune", "-f"],
            capture_output=True,
            text=True
        )

        # Parse reclaimed space from output
        for line in result.stdout.split('\n'):
            if "Total reclaimed space" in line:
                print(f"  {line}")

        return 1

def main():
    """Main cleanup routine"""
    print("=" * 60)
    print("AI Video Bot - Disk Cleanup")
    print("=" * 60)

    # Check current disk usage
    outputs_dir = Path("outputs")
    if outputs_dir.exists():
        outputs_size = get_dir_size(outputs_dir)
        print(f"\nCurrent outputs directory size: {format_size(outputs_size)}")

    # Cleanup temporary files
    print("\n[1/3] Cleaning up temporary files...")
    temp_count, temp_size = cleanup_all_temp_files(dry_run=False)
    if temp_count > 0:
        print(f"✅ Deleted {temp_count} temporary files ({format_size(temp_size)})")
    else:
        print("✅ No temporary files to delete")

    # Cleanup old videos (disabled by default)
    # print("\n[2/3] Cleaning up old videos (>30 days)...")
    # old_count, old_size = cleanup_old_videos(days=30, dry_run=False)
    # if old_count > 0:
    #     print(f"✅ Deleted {old_count} old videos ({format_size(old_size)})")
    # else:
    #     print("✅ No old videos to delete")
    print("\n[2/3] Old video cleanup is disabled (to enable, edit cleanup.py)")

    # Cleanup Docker
    print("\n[3/3] Cleaning up Docker...")
    cleanup_docker(dry_run=False)

    # Final disk usage
    if outputs_dir.exists():
        final_size = get_dir_size(outputs_dir)
        print(f"\nFinal outputs directory size: {format_size(final_size)}")
        if temp_count > 0:
            print(f"Space saved: {format_size(outputs_size - final_size)}")

    print("\n" + "=" * 60)
    print("Cleanup complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
