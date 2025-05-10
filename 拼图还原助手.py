# 拼图还原助手（还原逻辑完整匹配 JSON+PNG）
import os
import json
import math
from tkinter import filedialog, Tk, Button, Label, messagebox
from PIL import Image

def create_image_grid(image_paths, output_path, metadata_path):
    images = [Image.open(p).convert('RGBA') for p in image_paths]
    count = len(images)
    cols = math.ceil(math.sqrt(count))
    rows = math.ceil(count / cols)

    # 统一图像高度
    target_height = max(img.height for img in images)
    scaled_images = []
    for img in images:
        scale = target_height / img.height
        new_size = (int(img.width * scale), target_height)
        scaled_images.append(img.resize(new_size, Image.LANCZOS))

    col_widths = [0] * cols
    row_heights = [target_height] * rows
    for i, img in enumerate(scaled_images):
        col = i % cols
        col_widths[col] = max(col_widths[col], img.width)

    total_width = sum(col_widths)
    total_height = target_height * rows
    result = Image.new('RGBA', (total_width, total_height), (255, 255, 255, 0))

    metadata = []
    y = 0
    for row in range(rows):
        x = 0
        for col in range(cols):
            idx = row * cols + col
            if idx >= count:
                break
            img = scaled_images[idx]
            result.paste(img, (x, y))
            metadata.append({
                'filename': os.path.basename(image_paths[idx]),
                'position': [x, y],
                'size': [img.width, img.height]
            })
            x += col_widths[col]
        y += target_height

    result.save(output_path)
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def restore_images(grid_path, metadata_path, output_dir):
    if not os.path.exists(grid_path) or not os.path.exists(metadata_path):
        messagebox.showerror("错误", "拼接图或元数据文件不存在")
        return

    with open(metadata_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    grid = Image.open(grid_path).convert('RGBA')
    for item in meta:
        x, y = item['position']
        w, h = item['size']
        crop = grid.crop((x, y, x + w, y + h))
        crop.save(os.path.join(output_dir, item['filename']))

# GUI
class App:
    def __init__(self, root):
        self.root = root
        self.image_paths = []
        self.grid_path = ""
        self.metadata_path = ""
        self.restore_dir = ""

        Label(root, text="拼图还原助手").pack()
        Button(root, text="选择图片拼图", command=self.choose_images).pack()
        Button(root, text="拼图", command=self.do_merge).pack()
        Button(root, text="选择拼接图和JSON", command=self.choose_restore_sources).pack()
        Button(root, text="选择保存文件夹", command=self.choose_restore_dir).pack()
        Button(root, text="开始还原", command=self.do_restore).pack()

    def choose_images(self):
        self.image_paths = filedialog.askopenfilenames(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])

    def do_merge(self):
        if not self.image_paths:
            messagebox.showerror("错误", "请先选择图片")
            return
        output_path = filedialog.asksaveasfilename(defaultextension=".png")
        if not output_path:
            return
        metadata_path = output_path.replace(".png", ".json")
        create_image_grid(self.image_paths, output_path, metadata_path)
        messagebox.showinfo("完成", f"已保存到\n{output_path}\n{metadata_path}")

    def choose_restore_sources(self):
        files = filedialog.askopenfilenames(filetypes=[("拼接图和元数据", "*.png *.json")])
        for f in files:
            if f.lower().endswith(".png"):
                self.grid_path = f
            elif f.lower().endswith(".json"):
                self.metadata_path = f

    def choose_restore_dir(self):
        self.restore_dir = filedialog.askdirectory()

    def do_restore(self):
        if not self.grid_path or not self.metadata_path or not self.restore_dir:
            messagebox.showerror("错误", "请先选择拼图文件、元数据文件和输出路径")
            return
        restore_images(self.grid_path, self.metadata_path, self.restore_dir)
        messagebox.showinfo("完成", f"图像已还原至：\n{self.restore_dir}")

if __name__ == '__main__':
    root = Tk()
    root.title("拼图还原助手")
    app = App(root)
    root.mainloop()
