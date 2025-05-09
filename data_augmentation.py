import torch
from torch.utils.data import Dataset, Subset
from torchvision.transforms import v2
import torchvision.transforms as transforms


def ensure_three_channels(img: torch.Tensor) -> torch.Tensor:
    """
    Assure que tous les images sont à trois canaux (RGB).

    Args
    ----
      img : Image à vérifier

    Output
    ------
      img : RGB Image
    """
    if img.shape[0] == 1:
        img = img.expand(3, img.shape[1], img.shape[2])
    return img

class UpdateLabelsMNSIT(Dataset):
  """
  
  Shift its integer labels by a fixed offset.
  Convert the images to 3 channels if they are not already in that format.
  
  """
  def __init__(self, dataset, labels_shift):
    self.dataset = dataset
    self.labels_shift = labels_shift

  def __len__(self):
    return len(self.dataset)

  def __getitem__(self, idx):
    image, label = self.dataset[idx]
    label = label + self.labels_shift
    to_tensor = transforms.ToTensor()
    if not isinstance(image, torch.Tensor):
        image = to_tensor(image)
    image = ensure_three_channels(image)
    return image, label

class AugmentedMNIST(Dataset):
  """
  Crée un dataset qui contient toutes les images suite à l'augmentation
  des données
  """
  def __init__(self, dataset, augmented_retina_list):
    # Store the original dataset and the augmented dataset
    self.augmented_retina_list = augmented_retina_list
    self.dataset = dataset

  def __len__(self):
    return len(self.dataset) + len(self.augmented_retina_list)

  def __getitem__(self, idx):
    
    to_tensor = transforms.ToTensor()
    if idx < len(self.dataset):
       # Fetch from the original dataset
       image, label = self.dataset[idx]
    else:
        # Fetch from the augmented dataset
       image, label = self.augmented_retina_list[idx - len(self.dataset)]
    if not isinstance(image, torch.Tensor):
      image = to_tensor(image)

    image = ensure_three_channels(image)
    return image, label


def ApplyTransformation(dataset, transformation):
  augmented_data_list = []
  to_tensor = transforms.ToTensor()
  for i in range(len(dataset)):
    img = dataset[i][0]
    label = dataset[i][1]
    if not isinstance(img, torch.Tensor):
      img = to_tensor(img)
        
    img = ensure_three_channels(img)
    img = transformation(img)
    img = ensure_three_channels(img)
    augmented_data_list.append((img, label))

  return AugmentedMNIST(dataset, augmented_data_list)


def DatasetAugmentation(dataset):

  """
  Définit la séquence de transformation à effectuer

  Args
  ----
  dataset : Dataset contenant les images à augmenter

  Output
  ------
  augmented_dataset_3 : Dataset avec tous les images originales + transformées

  """

  # Rotate the image by 45 degrees
  first_transformation = v2.Compose([
      v2.Lambda(lambda img: v2.functional.rotate(img, angle=45.0)),
      v2.ToDtype(torch.float32, scale=True),
  ])

  # Apply color jitter to the image
  second_transformation = v2.Compose([
      v2.ColorJitter(brightness=0.4, contrast=0.5,saturation=0.4,hue=0.3),
      v2.ToDtype(torch.float32, scale=True),
  ])

  # Apply Gaussian blur to the image
  third_transformation = v2.Compose([
      v2.GaussianBlur(kernel_size=(3, 3), sigma=(0.1, 2)),
      v2.ToDtype(torch.float32, scale=True),
  ])

  augmented_dataset_1 = ApplyTransformation(dataset, first_transformation)
  augmented_dataset_2 = ApplyTransformation(augmented_dataset_1, second_transformation)
  augmented_dataset_3 = ApplyTransformation(augmented_dataset_2, third_transformation)


  return augmented_dataset_3


def ConcatDataset(path_dataset, derma_dataset, blood_dataset, retina_dataset, subset_count):
    """
    e.g. path_dataset = PathMNIST(split="train", download=True)

    For training_dataset, use a subset_count of 1080 (same amount as full retina train dataset)
    for validation dataset : subset_count = 120
    for test dataset : subset_count = 400
    """

    if subset_count not in [120, 400, 1080]:
      raise ValueError(f"subset_count must be 120, 400, or 1080. Got {subset_count} instead.")
    
    subset_tensor=torch.arange(subset_count).tolist()

    DERMA_LABELS_SHIFT = 9
    BLOOD_LABELS_SHIFT = 16
    RETINA_LABELS_SHIFT = 24
    
    print("Concatenating datasets")
    path_subset_dataset = Subset(path_dataset, subset_tensor)
    blood_subset_dataset = Subset(blood_dataset, subset_tensor)
    derma_subset_dataset = Subset(derma_dataset, subset_tensor)
    updated_derma_dataset = UpdateLabelsMNSIT(derma_subset_dataset, DERMA_LABELS_SHIFT)
    updated_blood_dataset = UpdateLabelsMNSIT(blood_subset_dataset, BLOOD_LABELS_SHIFT)
    updated_retina_dataset = UpdateLabelsMNSIT(retina_dataset, RETINA_LABELS_SHIFT)

    concat_datasets = torch.utils.data.ConcatDataset([path_subset_dataset, updated_derma_dataset, updated_blood_dataset, updated_retina_dataset])

    return concat_datasets





  
