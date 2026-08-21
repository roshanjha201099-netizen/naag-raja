import os
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

class SnakeDataset(Dataset):
    def __init__(self, csv_file, root_dir, transform=None):
        self.df = pd.read_csv(csv_file)
        self.root_dir = root_dir
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        
        # Path resolve: handles both nested and flat paths
        rel_path = os.path.normpath(row["file_path"])
        img_path = os.path.join(self.root_dir, rel_path)
        
        # Fallback if unzipped flat
        if not os.path.exists(img_path):
            img_path = os.path.join(self.root_dir, os.path.basename(rel_path))

        image = Image.open(img_path).convert("RGB")
        target = int(row["target"])

        if self.transform:
            image = self.transform(image)

        return image, target

# Augmentations for Fine-Grained Snake Classification
train_transforms = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.2),
    transforms.RandomRotation(degrees=15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

val_transforms = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def get_dataloaders(root_dir="datasets/raw/snakeclef", batch_size=32, num_workers=2):
    train_dataset = SnakeDataset(
        csv_file="datasets/metadata/phase1_train.csv",
        root_dir=root_dir,
        transform=train_transforms
    )
    val_dataset = SnakeDataset(
        csv_file="datasets/metadata/phase1_val.csv",
        root_dir=root_dir,
        transform=val_transforms
    )

    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True, 
        num_workers=num_workers, 
        pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset, 
        batch_size=batch_size, 
        shuffle=False, 
        num_workers=num_workers, 
        pin_memory=True
    )

    return train_loader, val_loader