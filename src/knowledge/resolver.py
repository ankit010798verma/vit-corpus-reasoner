"""Entity resolution: normalize dataset/benchmark names. Also defines standard ViT benchmark list for T7."""

DATASET_ALIASES: dict[str, str] = {
    # ImageNet variants
    "ilsvrc": "ImageNet",
    "ilsvrc2012": "ImageNet",
    "imagenet-1k": "ImageNet",
    "imagenet1k": "ImageNet",
    "imagenet 1k": "ImageNet",
    "in-1k": "ImageNet",
    "in1k": "ImageNet",
    "imagenet-21k": "ImageNet-21K",
    "imagenet21k": "ImageNet-21K",
    "in-21k": "ImageNet-21K",
    "in21k": "ImageNet-21K",
    "imagenet-22k": "ImageNet-21K",
    # COCO
    "ms-coco": "COCO",
    "mscoco": "COCO",
    "ms coco": "COCO",
    "coco2017": "COCO",
    "coco 2017": "COCO",
    # Cityscapes
    "cityscape": "Cityscapes",
    # Kinetics
    "kinetics": "Kinetics-400",
    "kinetics400": "Kinetics-400",
    "kinetics-400": "Kinetics-400",
    "kinetics600": "Kinetics-600",
    "kinetics-600": "Kinetics-600",
    # Oxford
    "oxford flowers": "Oxford Flowers-102",
    "flowers102": "Oxford Flowers-102",
    "oxford pets": "Oxford-IIIT Pets",
    "pets": "Oxford-IIIT Pets",
    # Other
    "ade20k": "ADE20K",
    "ade-20k": "ADE20K",
    "voc": "Pascal VOC",
    "pascal voc": "Pascal VOC",
    "voc2012": "Pascal VOC",
    "inaturalist": "iNaturalist",
    "places": "Places365",
    "places-365": "Places365",
    "cifar10": "CIFAR-10",
    "cifar-10": "CIFAR-10",
    "cifar100": "CIFAR-100",
    "cifar-100": "CIFAR-100",
    "sun rgb-d": "SUN-RGBD",
    "sunrgbd": "SUN-RGBD",
}

BENCHMARK_ALIASES: dict[str, str] = {
    "imagenet top-1": "ImageNet Top-1",
    "imagenet top1": "ImageNet Top-1",
    "imagenet-1k top-1": "ImageNet Top-1",
    "top-1 accuracy": "Top-1 Accuracy",
    "top1 accuracy": "Top-1 Accuracy",
    "map": "mAP",
    "mean ap": "mAP",
    "miou": "mIoU",
    "mean iou": "mIoU",
}

# Standard ViT-relevant benchmarks — used by T7 absence detection
STANDARD_VIT_BENCHMARKS: list[str] = [
    "ImageNet",
    "ImageNet-21K",
    "COCO",
    "ADE20K",
    "Kinetics-400",
    "Kinetics-600",
    "Cityscapes",
    "CIFAR-10",
    "CIFAR-100",
    "Oxford Flowers-102",
    "Oxford-IIIT Pets",
    "iNaturalist",
    "Places365",
    "Pascal VOC",
    "LVIS",
    "SUN-RGBD",
    "NYUv2",
    "ETH3D",
    "Something-Something v2",
    "UCF-101",
]

# Standard dataset sizes in thousands of training samples (for T8)
DATASET_SIZES_K: dict[str, float] = {
    "ImageNet": 1281.0,
    "ImageNet-21K": 14197.0,
    "COCO": 118.0,
    "ADE20K": 20.2,
    "Kinetics-400": 240.0,
    "Kinetics-600": 392.0,
    "Cityscapes": 2.975,
    "CIFAR-10": 50.0,
    "CIFAR-100": 50.0,
    "Oxford Flowers-102": 1.02,
    "Oxford-IIIT Pets": 3.68,
    "iNaturalist": 437.0,
    "Places365": 1803.0,
    "Pascal VOC": 11.54,
    "LVIS": 100.0,
    "NYUv2": 1.4,
    "ETH3D": 0.01,
    "Something-Something v2": 220.0,
    "UCF-101": 13.3,
}


def normalize_dataset(name: str) -> str:
    """Normalize a dataset name to its canonical form."""
    key = name.lower().strip()
    return DATASET_ALIASES.get(key, name.strip())


def normalize_benchmark(name: str) -> str:
    key = name.lower().strip()
    return BENCHMARK_ALIASES.get(key, name.strip())


def get_dataset_size_k(dataset_name: str) -> float | None:
    """Return known dataset size in thousands, or None."""
    normalized = normalize_dataset(dataset_name)
    return DATASET_SIZES_K.get(normalized)
