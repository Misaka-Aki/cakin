import os
import math
import json
from tkinter import Tk, Label, Button, filedialog, messagebox, ttk
from PIL import Image

class PasterApp:
    def __init__(self, root):
        self.root = root
        root.title("拼图还原助手")
        root.geometry("600x350")
        self.init_ui()

    def init_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True)

        self.merge_tab = ttk.Frame(notebook)
        self.restore_tab = ttk.Frame(notebook)
        notebook.add(self.merge_tab, text='图片拼接')
        notebook.add(self.restore_tab, text='图片还原')

        self.init_merge_tab()
        self.init_restore_tab()

    def init_merge_tab(self):
        self.image_paths = []
        self.output_path = ""

        ttk.Label(self.merge_tab, text="选择要拼接的图片").pack(pady=10)
        Button(self.merge_tab, text="选择图片", command=self.select_images).pack()
        Button(self.merge_tab, text="选择保存文件夹", command=self.select_output_folder).pack(pady=10)
        Button(self.merge_tab, text="选择保存文件名", command=self.select_output_filename).pack(pady=10)
        Button(self.merge_tab, text="开始拼接", command=self.start_merge).pack(pady=10)

    def init_restore_tab(self):
        self.grid_path = ""
        self.meta_path = ""
        self.restore_output_dir = ""

        ttk.Label(self.restore_tab, text="选择拼接图和元数据").pack(pady=10)
        Button(self.restore_tab, text="选择拼接图(.png)", command=self.select_grid).pack()
        Button(self.restore_tab, text="选择元数据(.json)", command=self.select_metadata).pack()
        Button(self.restore_tab, text="选择输出文件夹", command=self.select_output_dir).pack()
        Button(self.restore_tab, text="开始还原", command=self.start_restore).pack(pady=10)

    def select_images(self):
        self.image_paths = filedialog.askopenfilenames(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if self.image_paths:
            messagebox.showinfo("选中图片数", f"共选中 {len(self.image_paths)} 张图片")

    def select_output_folder(self):
        self.output_folder = filedialog.askdirectory()
        if self.output_folder:
            messagebox.showinfo("文件夹选中", f"已选择输出文件夹：{self.output_folder}")

    def select_output_filename(self):
        self.output_filename = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG 图像", "*.png")])
        if self.output_filename:
            messagebox.showinfo("文件名选中", f"已选择输出文件名：{self.output_filename}")

    def start_merge(self):
        if not self.image_paths or not self.output_filename:
            messagebox.showerror("错误", "请先选择图片和保存文件名")
            return
        json_path = self.output_filename.replace(".png", ".json")
        try:
            self.merge_images(self.image_paths, self.output_filename, json_path)
            messagebox.showinfo("完成", f"拼接完成！\n图片: {self.output_filename}\n数据: {json_path}")
        except Exception as e:
            messagebox.showerror("拼接失败", str(e))

    def merge_images(self, image_paths, output_path, metadata_path):
        images = [Image.open(p).convert("RGBA") for p in image_paths]
        count = len(images)
        cols = math.ceil(math.sqrt(count))
        rows = math.ceil(count / cols)

        col_widths = [0] * cols
        row_heights = [0] * rows

        for idx, img in enumerate(images):
            r, c = divmod(idx, cols)
            col_widths[c] = max(col_widths[c], img.width)
            row_heights[r] = max(row_heights[r], img.height)

        total_width = sum(col_widths)
        total_height = sum(row_heights)
        result = Image.new("RGBA", (total_width, total_height), (255, 255, 255, 0))

        metadata = []
        y = 0
        for r in range(rows):
            x = 0
            for c in range(cols):
                idx = r * cols + c
                if idx >= count:
                    break
                img = images[idx]
                result.paste(img, (x, y))
                metadata.append({
                    "filename": os.path.basename(image_paths[idx]),
                    "position": [x, y],
                    "size": [img.width, img.height]
                })
                x += col_widths[c]
            y += row_heights[r]

        result.save(output_path)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def select_grid(self):
        self.grid_path = filedialog.askopenfilename(filetypes=[("PNG 图像", "*.png")])

    def select_metadata(self):
        self.meta_path = filedialog.askopenfilename(filetypes=[("JSON 文件", "*.json")])

    def select_output_dir(self):
        self.restore_output_dir = filedialog.askdirectory()

    def start_restore(self):
        if not self.grid_path or not self.meta_path or not self.restore_output_dir:
            messagebox.showerror("错误", "请先选择拼图、元数据和输出文件夹")
            return
        try:
            self.restore_images(self.grid_path, self.meta_path, self.restore_output_dir)
            messagebox.showinfo("完成", f"图片已还原至: {self.restore_output_dir}")
        except Exception as e:
            messagebox.showerror("还原失败", str(e))

    def restore_images(self, grid_path, meta_path, output_dir):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        grid = Image.open(grid_path).convert("RGBA")
        for item in meta:
            x, y = item["position"]
            w, h = item["size"]
            crop = grid.crop((x, y, x + w, y + h))
            out_path = os.path.join(output_dir, item["filename"])

            # 所有还原图片统一保存为 PNG 格式
            crop.save(out_path, "PNG")  # 无论原始格式如何，全部输出为 PNG 格式

if __name__ == "__main__":
    root = Tk()
    app = PasterApp(root)
    root.mainloop()
