import h5py

def print_structure(name, obj):
    """
    打印组或数据集的名称和类型
    """
    if isinstance(obj, h5py.Group):
        print(f"Group: {name}")
    elif isinstance(obj, h5py.Dataset):
        print(f"Dataset: {name}, shape: {obj.shape}, dtype: {obj.dtype}")

# 打开 HDF5 文件并遍历结构
h5_file_path = '/Users/yangchangjie/Downloads/91-image_x2.h5'
with h5py.File(h5_file_path, 'r') as f:
    print("HDF5 文件的层次结构:")
    f.visititems(print_structure)
