# 拼图还原助手（简化版 GUI）
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

    col_widths = [0] * cols
    row_heights = [0] * rows
    for i, img in enumerate(images):
        col, row = i % cols, i // cols
        col_widths[col] = max(col_widths[col], img.width)
        row_heights[row] = max(row_heights[row], img.height)

    total_width = sum(col_widths)
    total_height = sum(row_heights)
    result = Image.new('RGBA', (total_width, total_height), (255, 255, 255, 0))

    metadata = []
    y = 0
    for row in range(rows):
        x = 0
        for col in range(cols):
            idx = row * cols + col
            if idx >= count: break
            img = images[idx]
            result.paste(img, (x, y))
            metadata.append({
                'filename': os.path.basename(image_paths[idx]),
                'position': [x, y],
                'size': [img.width, img.height]
            })
            x += col_widths[col]
        y += row_heights[row]

    result.save(output_path)
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def restore_images(grid_path, metadata_path, output_dir):
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
        Label(root, text="拼图还原助手").pack()
        Button(root, text="选择图片拼图", command=self.choose_images).pack()
        Button(root, text="拼图", command=self.do_merge).pack()
        Button(root, text="选择拼图还原", command=self.choose_grid).pack()
        Button(root, text="还原", command=self.do_restore).pack()

    def choose_images(self):
        self.image_paths = filedialog.askopenfilenames(filetypes=[("Images", "*.png;*.jpg")])

    def do_merge(self):
        if not self.image_paths:
            messagebox.showerror("错误", "请先选择图片")
            return
        output_path = filedialog.asksaveasfilename(defaultextension=".png")
        metadata_path = output_path.replace(".png", ".json")
        create_image_grid(self.image_paths, output_path, metadata_path)
        messagebox.showinfo("完成", f"已保存到\n{output_path}\n{metadata_path}")

    def choose_grid(self):
        self.grid_path = filedialog.askopenfilename(filetypes=[("PNG", "*.png")])
        self.metadata_path = self.grid_path.replace(".png", ".json")

    def do_restore(self):
        output_dir = filedialog.askdirectory()
        restore_images(self.grid_path, self.metadata_path, output_dir)
        messagebox.showinfo("完成", f"图像已还原至：\n{output_dir}")

if __name__ == '__main__':
    root = Tk()
    root.title("拼图还原助手")
    app = App(root)
    root.mainloop()

