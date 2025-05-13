import os
import sys
import math
import json
from tkinter import Tk, Label, Button, Entry, messagebox, filedialog, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image
from collections import deque

class SmartPasterApp:
    def __init__(self, root):
        self.root = root
        root.title("智能拼图还原工具")
        root.geometry("600x400")
        self.init_ui()

        self.selected_images = []
        self.base_dir = None
        self.merge_dir = None
        self.restore_dir = None
        self.cake_dir = None

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
        ttk.Label(self.merge_tab, text="选择需要拼接的图片：").pack(pady=5)
        Button(self.merge_tab, text="选择图片", command=self.select_images).pack(pady=5)

        self.drop_area = Label(self.merge_tab, text="或将图片拖拽到此区域", relief="ridge", borderwidth=2, width=50, height=5)
        self.drop_area.pack(pady=10)
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self.on_drop)

        ttk.Label(self.merge_tab, text="每张拼接图包含的图片数量：").pack(pady=5)
        self.image_per_grid_entry = Entry(self.merge_tab)
        self.image_per_grid_entry.insert(0, "9")
        self.image_per_grid_entry.pack(pady=5)

        Button(self.merge_tab, text="开始拼接", command=self.start_merge).pack(pady=10)

    def init_restore_tab(self):
        Button(self.restore_tab, text="开始还原所有拼接图", command=self.start_restore).pack(pady=20)

    def select_images(self):
        images = list(filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[("图像文件", "*.jpg *.jpeg *.png *.bmp *.webp *.tiff")]
        ))
        if images:
            self.selected_images = images
            self.set_working_dirs(os.path.dirname(images[0]))
            messagebox.showinfo("选中图片", f"已选中 {len(images)} 张图片")
        else:
            messagebox.showwarning("未选择", "未选择任何图片")

    def on_drop(self, event):
        dropped = self.root.tk.splitlist(event.data)
        images = [f for f in dropped if os.path.isfile(f) and f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff'))]
        if images:
            self.selected_images = images
            self.set_working_dirs(os.path.dirname(images[0]))
            messagebox.showinfo("拖拽添加", f"已添加 {len(images)} 张图片")

    def set_working_dirs(self, base_dir):
        self.base_dir = base_dir
        self.merge_dir = os.path.join(self.base_dir, "拼接")
        self.restore_dir = os.path.join(self.base_dir, "拆分")
        self.cake_dir = os.path.join(self.base_dir, "蛋糕")
        os.makedirs(self.merge_dir, exist_ok=True)
        os.makedirs(self.restore_dir, exist_ok=True)
        os.makedirs(self.cake_dir, exist_ok=True)

    def start_merge(self):
        try:
            count_per_grid = int(self.image_per_grid_entry.get())
            if count_per_grid <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的图片数量")
            return

        images = [(img, Image.open(img)) for img in self.selected_images]
        horiz, vert = deque(), deque()

        for path, img in images:
            (horiz if img.width >= img.height else vert).append((path, img))

        batches = [list() for _ in range(math.ceil(len(images) / count_per_grid))]
        for i, group in enumerate(horiz + vert):
            batches[i % len(batches)].append(group)

        existing = [f for f in os.listdir(self.merge_dir) if f.startswith("拼接") and f.endswith(".png")]
        start_index = 1
        for f in existing:
            try:
                num = int(f.replace("拼接", "").replace(".png", ""))
                start_index = max(start_index, num + 1)
            except:
                pass

        for i, batch in enumerate(batches):
            out_img, meta = self.create_grid(batch)
            idx = start_index + i
            img_name = f"拼接{idx}.png"
            json_name = f"拼接{idx}.json"
            out_img.save(os.path.join(self.merge_dir, img_name))
            with open(os.path.join(self.merge_dir, json_name), 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)

        messagebox.showinfo("完成", f"拼接完成，共生成 {len(batches)} 张拼接图")

    def create_grid(self, batch):
        cols = math.ceil(math.sqrt(len(batch)))
        rows = math.ceil(len(batch) / cols)

        widths = [0] * cols
        heights = [0] * rows

        for idx, (_, img) in enumerate(batch):
            r, c = divmod(idx, cols)
            widths[c] = max(widths[c], img.width)
            heights[r] = max(heights[r], img.height)

        total_width = sum(widths)
        total_height = sum(heights)
        grid_img = Image.new("RGBA", (total_width, total_height), (255, 255, 255, 0))

        metadata = []
        y = 0
        for r in range(rows):
            x = 0
            for c in range(cols):
                idx = r * cols + c
                if idx >= len(batch):
                    break
                path, img = batch[idx]
                grid_img.paste(img, (x, y))
                metadata.append({
                    "filename": os.path.basename(path),
                    "position": [x, y],
                    "size": [img.width, img.height],
                    "original_mode": img.mode
                })
                x += widths[c]
            y += heights[r]
        return grid_img, metadata

    def start_restore(self):
        if not os.path.exists(self.cake_dir):
            messagebox.showerror("错误", "蛋糕文件夹不存在")
            return

        merged_files = [f for f in os.listdir(self.merge_dir) if f.endswith(".json")]
        for json_file in merged_files:
            json_path = os.path.join(self.merge_dir, json_file)
            png_path = os.path.join(self.cake_dir, json_file.replace(".json", ".png"))

            if not os.path.exists(png_path):
                continue

            with open(json_path, 'r', encoding='utf-8') as f:
                try:
                    meta = json.load(f)
                except Exception as e:
                    print(f"读取元数据失败: {e}")
                    continue

            all_exist = True
            for item in meta:
                name, _ = os.path.splitext(item["filename"])
                out_path = os.path.join(self.restore_dir, f"{name}s.png")
                if not os.path.exists(out_path):
                    all_exist = False
                    break

            if all_exist:
                print(f"跳过已拆分拼接图: {png_path}")
                continue

            self.restore_one(png_path, meta)

        messagebox.showinfo("完成", f"所有拼接图已还原")

    def restore_one(self, grid_path, meta):
        grid = Image.open(grid_path)
        for item in meta:
            x, y = item["position"]
            w, h = item["size"]
            region = grid.crop((x, y, x + w, y + h))

            if item.get("original_mode"):
                region = region.convert(item["original_mode"])

            name, _ = os.path.splitext(item["filename"])
            new_name = f"{name}s.png"
            region.save(os.path.join(self.restore_dir, new_name))

if __name__ == '__main__':
    root = TkinterDnD.Tk()
    app = SmartPasterApp(root)
    root.mainloop()
