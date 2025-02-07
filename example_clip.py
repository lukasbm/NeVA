import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import clip

from NeVA import NeVAWrapper

data_path = "Datasets/"
model_path = "Models/"

batch_size = 32
image_size = 224
lr = 0.1
optimization_steps = 20

scanpath_length = 3
foveation_sigma = 0.2
blur_filter_size = 41
forgetting = 0.7
blur_sigma = 10


def cosine_sim(x, y):
    val = torch.nn.functional.cosine_similarity(x, y, 1)
    return -val + 1


criterion = cosine_sim


def target_function(x, y):
    return y


# Load Model
model, preprocess = clip.load("RN50", "cuda", download_root=model_path)
vision_model = model.visual
# Load Dataset
transform = transforms.Compose(preprocess)
test = datasets.CIFAR10(
    data_path + "CIFAR10-data", train=False, download=True, transform=preprocess
)
test_loader = DataLoader(test, batch_size=batch_size, shuffle=False, pin_memory=True)

# Create NeVA Model
NeVA_model = NeVAWrapper(
    downstream_model=vision_model,
    criterion=criterion,
    target_function=target_function,
    image_size=image_size,
    foveation_sigma=foveation_sigma,
    blur_filter_size=blur_filter_size,
    blur_sigma=blur_sigma,
    forgetting=forgetting,
    foveation_aggregation=1,
    device="cuda",
)

scanpaths = []
loss_history = []

for i, data in enumerate(test_loader):
    images, _ = data
    images = images.cuda()
    text = clip.tokenize(["a white car behind of a green car"]).to("cuda")
    # Use caption as guidance for NeVA could alternatively also use the image -> output = vision_model(images)
    output = model.encode_text(text)
    pred_labels = output

    current_scanpaths, current_loss_history = NeVA_model.run_optimization(
        images, pred_labels, scanpath_length, optimization_steps, lr
    )
    scanpaths.extend(current_scanpaths)
    loss_history.extend(current_loss_history)
