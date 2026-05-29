import tensorflow as tf
from tensorflow.keras.datasets import mnist
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization
)
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import os
import cv2
import numpy as np

def load_chars74k_digits(chars_root, img_size=28):
    """
    chars_root should point to:
        English/Fnt/

    Expected folders:
        Sample001, Sample002, ..., Sample010

    Labels:
        Sample001 -> 0
        Sample002 -> 1
        ...
        Sample010 -> 9
    """
    images = []
    labels = []

    for digit in range(1,10):
        folder = os.path.join(chars_root, f"Sample{digit + 1:03d}")

        if not os.path.isdir(folder):
            print(f"Warning: missing {folder}")
            continue

        for filename in os.listdir(folder):
            if not filename.lower().endswith(".png"):
                continue

            path = os.path.join(folder, filename)

            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue

            # resize to MNIST size
            img = cv2.resize(img, (img_size, img_size))

            # make background black, digit white if needed
            if np.mean(img) > 127:
                img = 255 - img

            img = img.astype("float32") / 255.0
            img = np.expand_dims(img, axis=-1)

            images.append(img)
            labels.append(digit)

    return np.array(images), np.array(labels)
## Load MNIST
(x_train, y_train), (x_test, y_test) = mnist.load_data()

# Normalize
x_train = x_train.astype("float32") / 255.0
x_test = x_test.astype("float32") / 255.0

# Reshape MNIST to CNN format
x_train = x_train.reshape(-1, 28, 28, 1)
x_test = x_test.reshape(-1, 28, 28, 1)

# Load Chars74K printed digits
chars_x, chars_y = load_chars74k_digits("db")

if len(chars_x) == 0:
    raise ValueError("No Chars74K images loaded. Check path: English/Fnt")

# Shuffle Chars74K
indices = np.arange(len(chars_x))
np.random.shuffle(indices)

chars_x = chars_x[indices]
chars_y = chars_y[indices]

# Use part of Chars74K as validation
split = int(0.8 * len(chars_x))

chars_train_x = chars_x[:split]
chars_train_y = chars_y[:split]

chars_val_x = chars_x[split:]
chars_val_y = chars_y[split:]

# Merge MNIST + Chars74K train
x_train = np.concatenate([x_train, chars_train_x], axis=0)
y_train = np.concatenate([y_train, chars_train_y], axis=0)

# Mixed validation set
x_val = np.concatenate([x_test, chars_val_x], axis=0)
y_val = np.concatenate([y_test, chars_val_y], axis=0)

# One-hot labels
y_train = to_categorical(y_train, 10)
y_val = to_categorical(y_val, 10)

# Data augmentation to imitate Sudoku digit crops
datagen = ImageDataGenerator(
    rotation_range=8,
    width_shift_range=0.12,
    height_shift_range=0.12,
    zoom_range=0.15,
    shear_range=0.08
)

datagen.fit(x_train)
# LeNet
model = Sequential([
    Conv2D(32, (3, 3), activation="relu", input_shape=(28, 28, 1)),
    BatchNormalization(),
    MaxPooling2D((2, 2)),

    Conv2D(64, (3, 3), activation="relu"),
    BatchNormalization(),
    MaxPooling2D((2, 2)),

    Conv2D(128, (3, 3), activation="relu"),
    BatchNormalization(),

    Flatten(),

    Dense(128, activation="relu"),
    Dropout(0.4),

    Dense(10, activation="softmax")
])

model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

model.fit(
    datagen.flow(x_train, y_train, batch_size=64),
    epochs=20,
    validation_data=(x_val, y_val)
)

model.save("mnist_digit_model.h5")

print("Improved model saved.")