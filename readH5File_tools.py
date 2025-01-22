import h5py
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt


# 创建 HDF5 文件
# with h5py.File('example.h5', 'w') as f:
#     # 创建组
#     grp = f.create_group('images')
#
#     # 创建数据集
#     data = np.random.random((100, 64, 64))  # 100 个 64x64 图像
#     grp.create_dataset('lr', data=data)
#
#     # 添加属性
#     grp.attrs['description'] = 'Low-resolution images'

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
    lr_data = f['lr'][:]  # 获取数据集 numpy 数组
    hr_data = f['hr'][:]
    print(lr_data[0])

    # 将第一个图像转换为 Pillow 图像并显示
    img = Image.fromarray((lr_data[0] ).astype(np.uint8))  # 将 NumPy 数组转换为图像
    imghr = Image.fromarray((hr_data[0]).astype(np.uint8))
    # img.show()
    # imghr.show()
    fig, axs = plt.subplots(1, 2, figsize=(10, 5))  # Create a figure with two subplots

    # Show 'img' in the first subplot
    axs[0].imshow(img, cmap='gray')
    axs[0].set_title('lr')

    # Show 'imghr' in the second subplot
    axs[1].imshow(imghr, cmap='gray')
    axs[1].set_title('hr')

    plt.show()  # Display the figure


