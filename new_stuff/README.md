# 🐍 Snake Classifier (ConvNeXt-Small Upgrade)

This package upgrades your classification pipeline from `ConvNeXt-Tiny` to `ConvNeXt-Small` with fine-tuned Indian snake species weights and venom safety knowledge.

## 🚀 How to Replace ConvNeXt-Tiny with ConvNeXt-Small

### 1. Update Architecture Initialization
In PyTorch, replace `models.convnext_tiny` with `models.convnext_small`. 

> **Note**: Both Tiny and Small have `in_features = 768` at the final layer, but Small is 3x deeper in Stage 3 (27 blocks vs 9 blocks), so you must instantiate `convnext_small`.

```python
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load Class Names
with open("class_names.txt", "r") as f:
    class_names = [line.strip() for line in f.readlines() if line.strip()]

# 1. Build Model Architecture
model = models.convnext_small(weights=None)
in_features = model.classifier[2].in_features  # 768

# Replace classifier head to match trained checkpoint
model.classifier[2] = nn.Sequential(
    nn.Dropout(p=0.4),
    nn.Linear(in_features, len(class_names))
)

# 2. Load Weights
checkpoint = torch.load("snake_classifier.pth", map_location=device)
model.load_state_dict(checkpoint)
model.to(device)
model.eval()
