# Dataset EDA Report

Total classes: 4

Total images: 120

## Images per class
- dirty: 30
- healthy: 30
- inflamed: 30
- prolapse: 30

## Class imbalance
- Max/Min count ratio: 1.00

## Duplicates (perceptual hash + exact md5 inside bins)
- Duplicate groups: 0

## Corrupted / unreadable images
- failed_read_count: 0

## Low-quality images (heuristic)
- low_quality_count: 27
- thresholds: {'blur_var_10pct': 0.00046228463804380717, 'brightness_low_5pct': 0.4697184134239994, 'brightness_high_95pct': 0.7072194905000876, 'contrast_low_5pct': 0.11654277253586463, 'contrast_high_95pct': 0.24450273477068457}

## Dimension stats
- width_mean: 420.0
- width_min: 416
- width_max: 424
- height_mean: 304.0
- height_min: 220
- height_max: 328
- aspect_ratio_mean: 1.4157725630286606

## Generated figures
- class_distribution.png: ml_pipeline\analysis\figures\class_distribution.png
- dimension_hist.png: ml_pipeline\analysis\figures\dimension_hist.png
- brightness_hist.png: ml_pipeline\analysis\figures\brightness_hist.png
- contrast_hist.png: ml_pipeline\analysis\figures\contrast_hist.png
- blur_hist.png: ml_pipeline\analysis\figures\blur_hist.png
- samples_dirty.png: ml_pipeline\analysis\figures\samples_dirty.png
- samples_healthy.png: ml_pipeline\analysis\figures\samples_healthy.png
- samples_inflamed.png: ml_pipeline\analysis\figures\samples_inflamed.png
- samples_prolapse.png: ml_pipeline\analysis\figures\samples_prolapse.png
