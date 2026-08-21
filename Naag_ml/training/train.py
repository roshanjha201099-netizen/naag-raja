import os
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
import timm
from tqdm import tqdm

from preprocessing.dataset import get_dataloaders

def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running_loss, correct, total = 0.0, 0, 0

    for images, targets in tqdm(loader, desc="Training", leave=False):
        images, targets = images.to(device), targets.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, preds = outputs.max(1)
        correct += preds.eq(targets).sum().item()
        total += targets.size(0)

    return running_loss / total, (correct / total) * 100.0

@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    running_loss, correct, total = 0.0, 0, 0

    for images, targets in tqdm(loader, desc="Validating", leave=False):
        images, targets = images.to(device), targets.to(device)
        outputs = model(images)
        loss = criterion(outputs, targets)

        running_loss += loss.item() * images.size(0)
        _, preds = outputs.max(1)
        correct += preds.eq(targets).sum().item()
        total += targets.size(0)

    return running_loss / total, (correct / total) * 100.0

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using Device: {device}")

    num_classes = 98
    batch_size = 32
    epochs = 10
    learning_rate = 3e-4

    # Model: EfficientNet or ConvNeXt pretrained backbone
    model_name = "efficientnet_b0"
    print(f"Loading pretrained backbone: {model_name}")
    model = timm.create_model(model_name, pretrained=True, num_classes=num_classes)
    model.to(device)

    train_loader, val_loader = get_dataloaders(
        root_dir="datasets/raw/snakeclef", 
        batch_size=batch_size, 
        num_workers=2
    )

    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-2)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs)

    os.makedirs("models", exist_ok=True)
    best_val_acc = 0.0

    print("=" * 60)
    print("STARTING PHASE 1 TRAINING")
    print("=" * 60)

    for epoch in range(1, epochs + 1):
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)
        scheduler.step()

        print(f"Epoch [{epoch:02d}/{epochs:02d}] | "
              f"Train Loss: {train_loss:.4f} - Train Acc: {train_acc:.2f}% | "
              f"Val Loss: {val_loss:.4f} - Val Acc: {val_acc:.2f}%")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), "models/snake_model_phase1_best.pth")
            print(f"  -> Best model saved with Val Acc: {best_val_acc:.2f}%")

    print(f"\nTraining Complete! Best Validation Accuracy: {best_val_acc:.2f}%")

if __name__ == "__main__":
    main()