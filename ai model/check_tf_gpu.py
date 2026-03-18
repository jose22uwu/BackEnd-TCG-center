import os
import tensorflow as tf

print("TF_VERSION", tf.__version__)
print("LD_LIBRARY_PATH", os.getenv("LD_LIBRARY_PATH"))
print("GPU_DEVICES", tf.config.list_physical_devices("GPU"))
