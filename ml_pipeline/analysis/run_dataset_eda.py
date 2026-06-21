import os
import json
import math
import hashlib
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt

from PIL import Image, UnidentifiedImageError


def phash(img, hash_size=16, highfreq_factor=4):
    # Simple perceptual hash (dct-like). Uses cv2.dct if available.
    img = img.convert('L').resize(
        (hash_size * highfreq_factor, hash_size * highfreq_factor),
        Image.Resampling.LANCZOS,
    )
    pixels = np.asarray(img, dtype=np.float32)
    try:
        import cv2

        dct = cv2.dct(pixels)
    except Exception:
        f = np.fft.fft2(pixels)
        dct = np.abs(f)

    dct_low = dct[:hash_size, :hash_size]
    med = np.median(dct_low[1:, 1:])
    diff = dct_low > med
    return diff


def bits_to_hex(bits: np.ndarray) -> str:
    b = bits.flatten()
    s = ''.join('1' if x else '0' for x in b)
    return hex(int(s, 2))[2:]


def laplacian_blur_score(gray: np.ndarray) -> float:
    try:
        import cv2

        lap = cv2.Laplacian(gray, cv2.CV_64F)
        return float(lap.var())
    except Exception:
        gy, gx = np.gradient(gray.astype(np.float32))
        return float((gx.var() + gy.var()) / 2)


def compute_brightness_contrast(im: Image.Image):
    arr = np.asarray(im.convert('RGB'), dtype=np.float32) / 255.0
    gray = np.dot(arr[..., :3], [0.299, 0.587, 0.114])
    brightness = float(gray.mean())
    contrast = float(gray.std())
    return brightness, contrast, arr


def md5_of_file(path: str) -> str:
    m = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            m.update(chunk)
    return m.hexdigest()


def main():
    root = 'poutry_ai/dataset'
    out_dir = os.path.join('ml_pipeline', 'analysis')
    fig_dir = os.path.join(out_dir, 'figures')
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(fig_dir, exist_ok=True)

    class_names = []
    if not os.path.isdir(root):
        raise FileNotFoundError(f"Dataset root folder not found: {os.path.abspath(root)}")

    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d)
        if os.path.isdir(p):
            class_names.append(d)

    images = []
    for cls in class_names:
        p = os.path.join(root, cls)
        for fn in sorted(os.listdir(p)):
            if fn.lower().endswith(('.png', '.jpg', '.jpeg')):
                images.append((cls, os.path.join(p, fn), fn))

    stats = {
        'num_classes': len(class_names),
        'classes': class_names,
        'num_images_total': len(images),
        'per_class_counts': {},
        'per_class_failed_read': {},
    }

    per_class = defaultdict(list)
    failed = []
    phash_dict = defaultdict(list)

    for cls, path, fn in images:
        try:
            with Image.open(path) as im:
                im.load()
                w, h = im.size

                brightness, contrast, arr = compute_brightness_contrast(im)
                gray = np.dot(arr[..., :3], [0.299, 0.587, 0.114])
                blur = laplacian_blur_score(gray)

                mean = arr.mean(axis=(0, 1)).tolist()
                std = arr.std(axis=(0, 1)).tolist()

                bits = phash(im)
                hhex = bits_to_hex(bits)

                item = {
                    'class': cls,
                    'path': path,
                    'filename': fn,
                    'width': int(w),
                    'height': int(h),
                    'aspect_ratio': float(w / h),
                    'brightness_mean': brightness,
                    'contrast_std': contrast,
                    'laplacian_blur_var': blur,
                    'rgb_mean': mean,
                    'rgb_std': std,
                    'phash': hhex,
                }

                per_class[cls].append(item)
                stats['per_class_counts'][cls] = stats['per_class_counts'].get(cls, 0) + 1
                phash_dict[hhex].append(item)
        except UnidentifiedImageError:
            failed.append({'class': cls, 'path': path, 'filename': fn, 'error': 'unidentified'})
        except Exception as e:
            failed.append({'class': cls, 'path': path, 'filename': fn, 'error': str(e)})

    stats['failed_read_count'] = len(failed)
    stats['failed_read'] = failed[:50]

    # Duplicate groups (phash collisions + exact md5 check inside group)
    duplicates = []
    for hhex, items in phash_dict.items():
        if len(items) > 1:
            md5s = defaultdict(list)
            for it in items:
                md5s[md5_of_file(it['path'])].append(it['filename'])

            # keep unique md5 groups inside this phash bin
            for _, fn_list in md5s.items():
                if len(fn_list) > 1:
                    duplicates.append(
                        {
                            'phash': hhex,
                            'num_images': len(fn_list),
                            'filenames': fn_list,
                        }
                    )

    stats['duplicate_groups_phash'] = len(duplicates)
    stats['duplicate_groups_sample'] = duplicates[:20]

    all_items = [it for cls in class_names for it in per_class[cls]]
    if not all_items:
        raise RuntimeError('No images loaded; cannot compute EDA.')

    blur_vals = np.array([it['laplacian_blur_var'] for it in all_items], dtype=float)
    bright_vals = np.array([it['brightness_mean'] for it in all_items], dtype=float)
    contrast_vals = np.array([it['contrast_std'] for it in all_items], dtype=float)

    blur_thr = float(np.percentile(blur_vals, 10))  # bottom 10% blurry
    bright_low = float(np.percentile(bright_vals, 5))
    bright_high = float(np.percentile(bright_vals, 95))
    contrast_low = float(np.percentile(contrast_vals, 5))
    contrast_high = float(np.percentile(contrast_vals, 95))

    low_quality = [
        it
        for it in all_items
        if (
            it['laplacian_blur_var'] <= blur_thr
            or it['brightness_mean'] <= bright_low
            or it['brightness_mean'] >= bright_high
            or it['contrast_std'] <= contrast_low
            or it['contrast_std'] >= contrast_high
        )
    ]

    stats['quality_thresholds'] = {
        'blur_var_10pct': blur_thr,
        'brightness_low_5pct': bright_low,
        'brightness_high_95pct': bright_high,
        'contrast_low_5pct': contrast_low,
        'contrast_high_95pct': contrast_high,
    }
    stats['low_quality_count'] = len(low_quality)
    stats['low_quality_sample'] = [
        {
            k: it[k]
            for k in ['class', 'filename', 'width', 'height', 'brightness_mean', 'contrast_std', 'laplacian_blur_var']
        }
        for it in low_quality[:30]
    ]

    w_vals = np.array([it['width'] for it in all_items], dtype=float)
    h_vals = np.array([it['height'] for it in all_items], dtype=float)

    stats['dimension_stats'] = {
        'width_mean': float(w_vals.mean()),
        'width_min': int(w_vals.min()),
        'width_max': int(w_vals.max()),
        'height_mean': float(h_vals.mean()),
        'height_min': int(h_vals.min()),
        'height_max': int(h_vals.max()),
        'aspect_ratio_mean': float(np.mean([it['aspect_ratio'] for it in all_items])),
    }

    stats['global_color_stats'] = {
        'rgb_mean_mean': float(np.mean([np.mean(it['rgb_mean']) for it in all_items])),
    }

    # Charts
    cls = class_names
    counts = [stats['per_class_counts'][c] for c in cls]

    plt.figure(figsize=(8, 4))
    plt.bar(cls, counts)
    plt.xticks(rotation=20)
    plt.title('Images per class')
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, 'class_distribution.png'), dpi=160)
    plt.close()

    plt.figure(figsize=(8, 4))
    plt.hist(w_vals, bins=20, alpha=0.7, label='width')
    plt.hist(h_vals, bins=20, alpha=0.7, label='height')
    plt.legend()
    plt.title('Dimension histograms')
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, 'dimension_hist.png'), dpi=160)
    plt.close()

    plt.figure(figsize=(8, 4))
    plt.hist(bright_vals, bins=25, color='orange', alpha=0.8)
    plt.title('Brightness mean histogram')
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, 'brightness_hist.png'), dpi=160)
    plt.close()

    plt.figure(figsize=(8, 4))
    plt.hist(contrast_vals, bins=25, color='green', alpha=0.8)
    plt.title('Contrast std histogram')
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, 'contrast_hist.png'), dpi=160)
    plt.close()

    plt.figure(figsize=(8, 4))
    plt.hist(blur_vals, bins=25, color='red', alpha=0.8)
    plt.title('Laplacian blur score histogram (lower=blurrier)')
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, 'blur_hist.png'), dpi=160)
    plt.close()

    # Sample grids per class
    cols = 6
    for c in class_names:
        items = per_class[c][: min(18, len(per_class[c]))]
        rows = int(math.ceil(len(items) / cols)) if items else 1
        fig, axs = plt.subplots(rows, cols, figsize=(cols * 2, rows * 2))
        axs = np.array(axs).reshape(-1)
        for i, ax in enumerate(axs):
            ax.axis('off')
            if i < len(items):
                im = Image.open(items[i]['path']).convert('RGB')
                ax.imshow(im)
                ax.set_title(items[i]['filename'][:12], fontsize=8)
        plt.tight_layout()
        plt.savefig(os.path.join(fig_dir, f'samples_{c}.png'), dpi=160)
        plt.close()

    # Persist outputs
    stats_path = os.path.join(out_dir, 'dataset_stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)

    report_path = os.path.join(out_dir, 'dataset_eda_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('# Dataset EDA Report\n\n')
        f.write(f"Total classes: {stats['num_classes']}\n\n")
        f.write(f"Total images: {stats['num_images_total']}\n\n")
        f.write('## Images per class\n')
        for c in class_names:
            f.write(f"- {c}: {stats['per_class_counts'][c]}\n")
        f.write('\n')
        f.write('## Class imbalance\n')
        counts_arr = np.array([stats['per_class_counts'][c] for c in class_names], dtype=int)
        imb_ratio = float(counts_arr.max() / max(1, counts_arr.min()))
        f.write(f"- Max/Min count ratio: {imb_ratio:.2f}\n\n")
        f.write('## Duplicates (perceptual hash + exact md5 inside bins)\n')
        f.write(f"- Duplicate groups: {stats['duplicate_groups_phash']}\n")
        if stats['duplicate_groups_sample']:
            f.write('\n### Sample groups\n')
            for g in stats['duplicate_groups_sample']:
                f.write(f"- phash={g['phash']} num={g['num_images']} filenames={g['filenames'][:6]}{'...' if len(g['filenames'])>6 else ''}\n")
        f.write('\n')
        f.write('## Corrupted / unreadable images\n')
        f.write(f"- failed_read_count: {stats['failed_read_count']}\n\n")
        f.write('## Low-quality images (heuristic)\n')
        f.write(f"- low_quality_count: {stats['low_quality_count']}\n")
        f.write(f"- thresholds: {stats['quality_thresholds']}\n\n")
        f.write('## Dimension stats\n')
        for k, v in stats['dimension_stats'].items():
            f.write(f"- {k}: {v}\n")
        f.write('\n')
        f.write('## Generated figures\n')
        for fn in [
            'class_distribution.png',
            'dimension_hist.png',
            'brightness_hist.png',
            'contrast_hist.png',
            'blur_hist.png',
        ]:
            f.write(f"- {fn}: {os.path.join(fig_dir, fn)}\n")
        for c in class_names:
            f.write(f"- samples_{c}.png: {os.path.join(fig_dir, 'samples_' + c + '.png')}\n")

    print('WROTE', report_path)
    print('STATS_SUMMARY', {
        'num_images_total': stats['num_images_total'],
        'per_class_counts': stats['per_class_counts'],
        'failed_read_count': stats['failed_read_count'],
        'duplicate_groups_phash': stats['duplicate_groups_phash'],
        'low_quality_count': stats['low_quality_count'],
    })


if __name__ == '__main__':
    main()

