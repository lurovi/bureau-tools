#!/usr/bin/env python3
"""
Interactive PDF Editor
Allows adding text and images (including transparent signatures) to PDF files
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import img2pdf


class PDFEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Editor")
        self.root.geometry("1200x800")
        
        self.pdf_document = None
        self.pdf_path = None  # Store original PDF file path
        self.current_page_num = 0
        self.current_page = None
        self.zoom = 1.5
        self.annotations = []  # Store text and image annotations
        self.canvas_objects = []  # Store canvas object IDs and their annotations
        
        self.mode = "text"  # "text" or "image"
        self.signature_image_path = None
        self.text_color = "#000000"  # Default black
        
        # Selection and dragging
        self.selected_object = None
        self.selected_annotation = None
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.resize_handles = []
        self.resize_mode = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Create the user interface"""
        # Top toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="Open PDF", command=self.open_pdf).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save PDF", command=self.save_pdf).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Navigation
        ttk.Button(toolbar, text="◀ Previous", command=self.previous_page).pack(side=tk.LEFT, padx=2)
        self.page_label = ttk.Label(toolbar, text="No PDF loaded")
        self.page_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Next ▶", command=self.next_page).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Mode selection
        ttk.Label(toolbar, text="Mode:").pack(side=tk.LEFT, padx=2)
        self.mode_var = tk.StringVar(value="text")
        ttk.Radiobutton(toolbar, text="Add Text", variable=self.mode_var, 
                       value="text", command=self.set_text_mode).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(toolbar, text="Insert Image", variable=self.mode_var, 
                       value="image", command=self.set_image_mode).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(toolbar, text="Edit/Move", variable=self.mode_var, 
                       value="edit", command=self.set_edit_mode).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(toolbar, text="Delete Selected", command=self.delete_selected).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Text color picker
        ttk.Button(toolbar, text="Text Color", command=self.choose_text_color).pack(side=tk.LEFT, padx=2)
        self.color_display = tk.Canvas(toolbar, width=30, height=20, bg=self.text_color, relief=tk.SUNKEN)
        self.color_display.pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Image/Signature selection
        ttk.Button(toolbar, text="Select Signature/Image", 
                  command=self.select_signature).pack(side=tk.LEFT, padx=2)
        self.signature_label = ttk.Label(toolbar, text="No image selected")
        self.signature_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Zoom controls
        ttk.Label(toolbar, text="Zoom:").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="-", command=self.zoom_out, width=3).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="+", command=self.zoom_in, width=3).pack(side=tk.LEFT, padx=2)
        
        # Canvas with scrollbars
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Canvas
        self.canvas = tk.Canvas(canvas_frame, bg='gray',
                               yscrollcommand=v_scrollbar.set,
                               xscrollcommand=h_scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        v_scrollbar.config(command=self.canvas.yview)
        h_scrollbar.config(command=self.canvas.xview)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Bind keyboard shortcuts
        self.root.bind("<Delete>", lambda e: self.delete_selected())
        self.root.bind("<BackSpace>", lambda e: self.delete_selected())
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def set_text_mode(self):
        """Switch to text mode"""
        self.mode = "text"
        self.status_bar.config(text="Text mode: Click on the PDF to add text")
        
    def set_image_mode(self):
        """Switch to image mode"""
        self.mode = "image"
        self.clear_selection()
        if self.signature_image_path:
            self.status_bar.config(text="Image mode: Click on the PDF to insert image")
        else:
            self.status_bar.config(text="Image mode: Please select an image first")
    
    def set_edit_mode(self):
        """Switch to edit mode"""
        self.mode = "edit"
        self.clear_selection()
        self.status_bar.config(text="Edit mode: Click on text/image to move or resize it")
    
    def choose_text_color(self):
        """Open color picker for text"""
        color = colorchooser.askcolor(title="Choose Text Color", initialcolor=self.text_color)
        if color[1]:  # color[1] is the hex value
            self.text_color = color[1]
            self.color_display.config(bg=self.text_color)
            self.status_bar.config(text=f"Text color set to {self.text_color}")
            
    def select_signature(self):
        """Select a signature or image file"""
        filename = filedialog.askopenfilename(
            title="Select Signature/Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self.signature_image_path = filename
            basename = os.path.basename(filename)
            self.signature_label.config(text=f"Selected: {basename}")
            self.status_bar.config(text=f"Loaded image: {basename}")
    
    def open_pdf(self):
        """Open a PDF file"""
        filename = filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                if self.pdf_document:
                    self.pdf_document.close()
                
                self.pdf_path = filename  # Store the original file path
                self.pdf_document = fitz.open(filename)
                self.current_page_num = 0
                self.annotations = []
                self.display_page()
                self.status_bar.config(text=f"Opened: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open PDF: {str(e)}")
    
    def display_page(self):
        """Display the current page"""
        if not self.pdf_document:
            return
        
        self.current_page = self.pdf_document[self.current_page_num]
        
        # Render page to image
        mat = fitz.Matrix(self.zoom, self.zoom)
        pix = self.current_page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image and then to ImageTk
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.photo = ImageTk.PhotoImage(img)
        
        # Clear canvas and display image
        self.canvas.delete("all")
        self.canvas_objects = []
        self.clear_selection()
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        # Redraw annotations for current page
        self.redraw_annotations()
        
        # Update canvas scroll region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
        # Update page label
        total_pages = len(self.pdf_document)
        self.page_label.config(text=f"Page {self.current_page_num + 1} of {total_pages}")
        
    def next_page(self):
        """Go to next page"""
        if self.pdf_document and self.current_page_num < len(self.pdf_document) - 1:
            self.current_page_num += 1
            self.display_page()
    
    def previous_page(self):
        """Go to previous page"""
        if self.pdf_document and self.current_page_num > 0:
            self.current_page_num -= 1
            self.display_page()
    
    def zoom_in(self):
        """Increase zoom level"""
        self.zoom = min(self.zoom + 0.25, 4.0)
        self.display_page()
        
    def zoom_out(self):
        """Decrease zoom level"""
        self.zoom = max(self.zoom - 0.25, 0.5)
        self.display_page()
    
    def on_canvas_click(self, event):
        """Handle canvas click events"""
        if not self.pdf_document:
            messagebox.showwarning("Warning", "Please open a PDF file first")
            return
        
        # Get click coordinates relative to canvas
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Convert canvas coordinates to PDF coordinates (accounting for zoom)
        pdf_x = canvas_x / self.zoom
        pdf_y = canvas_y / self.zoom
        
        if self.mode == "edit":
            # Check if clicking on a resize handle
            if self.check_resize_handle_click(canvas_x, canvas_y):
                return
            # Check if clicking on an existing annotation
            self.select_annotation(canvas_x, canvas_y)
        elif self.mode == "text":
            self.add_text(pdf_x, pdf_y)
        elif self.mode == "image":
            self.add_image(pdf_x, pdf_y)
    
    def add_text(self, x, y):
        """Add text at the specified position"""
        # Prompt for text
        text = simpledialog.askstring("Add Text", "Enter text to add:")
        if not text:
            return
        
        # Prompt for font size
        font_size = simpledialog.askinteger("Font Size", "Enter font size:", 
                                           initialvalue=12, minvalue=6, maxvalue=72)
        if not font_size:
            font_size = 12
        
        # Store annotation
        annotation = {
            'type': 'text',
            'page': self.current_page_num,
            'x': x,
            'y': y,
            'text': text,
            'font_size': font_size,
            'color': self.text_color
        }
        self.annotations.append(annotation)
        
        # Draw text on canvas
        canvas_x = x * self.zoom
        canvas_y = y * self.zoom
        display_font_size = int(font_size * self.zoom)
        text_id = self.canvas.create_text(canvas_x, canvas_y, text=text, anchor=tk.NW,
                               fill=self.text_color, font=('Helvetica', display_font_size),
                               tags='annotation')
        
        self.canvas_objects.append({'id': text_id, 'annotation': annotation})
        
        self.status_bar.config(text=f"Added text: '{text}' at page {self.current_page_num + 1}")
    
    def add_image(self, x, y):
        """Add image at the specified position"""
        if not self.signature_image_path:
            messagebox.showwarning("Warning", "Please select an image first")
            return
        
        # Prompt for image width
        width = simpledialog.askinteger("Image Width", "Enter image width in points:", 
                                       initialvalue=100, minvalue=10, maxvalue=500)
        if not width:
            width = 100
        
        # Store annotation
        annotation = {
            'type': 'image',
            'page': self.current_page_num,
            'x': x,
            'y': y,
            'path': self.signature_image_path,
            'width': width
        }
        self.annotations.append(annotation)
        
        # Draw image on canvas
        try:
            img = Image.open(self.signature_image_path)
            # Calculate height maintaining aspect ratio
            aspect_ratio = img.height / img.width
            height = int(width * aspect_ratio)
            annotation['height'] = height
            
            # Resize for display
            display_width = int(width * self.zoom)
            display_height = int(height * self.zoom)
            img_resized = img.resize((display_width, display_height), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(img_resized)
            
            canvas_x = x * self.zoom
            canvas_y = y * self.zoom
            
            # Keep reference to prevent garbage collection
            if not hasattr(self, 'temp_images'):
                self.temp_images = []
            self.temp_images.append(img_tk)
            
            img_id = self.canvas.create_image(canvas_x, canvas_y, anchor=tk.NW, image=img_tk,
                                            tags='annotation')
            
            self.canvas_objects.append({'id': img_id, 'annotation': annotation, 'image_ref': img_tk})
            
            self.status_bar.config(text=f"Added image at page {self.current_page_num + 1}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display image: {str(e)}")
    
    def redraw_annotations(self):
        """Redraw all annotations for the current page"""
        if not hasattr(self, 'temp_images'):
            self.temp_images = []
        else:
            self.temp_images.clear()
        
        for annotation in self.annotations:
            if annotation['page'] != self.current_page_num:
                continue
            
            if annotation['type'] == 'text':
                canvas_x = annotation['x'] * self.zoom
                canvas_y = annotation['y'] * self.zoom
                display_font_size = int(annotation['font_size'] * self.zoom)
                color = annotation.get('color', '#000000')
                
                text_id = self.canvas.create_text(
                    canvas_x, canvas_y, 
                    text=annotation['text'], 
                    anchor=tk.NW,
                    fill=color, 
                    font=('Helvetica', display_font_size),
                    tags='annotation'
                )
                self.canvas_objects.append({'id': text_id, 'annotation': annotation})
                
            elif annotation['type'] == 'image':
                try:
                    img = Image.open(annotation['path'])
                    aspect_ratio = img.height / img.width
                    height = annotation['width'] * aspect_ratio
                    annotation['height'] = height
                    
                    display_width = int(annotation['width'] * self.zoom)
                    display_height = int(height * self.zoom)
                    img_resized = img.resize((display_width, display_height), Image.Resampling.LANCZOS)
                    img_tk = ImageTk.PhotoImage(img_resized)
                    
                    canvas_x = annotation['x'] * self.zoom
                    canvas_y = annotation['y'] * self.zoom
                    
                    self.temp_images.append(img_tk)
                    
                    img_id = self.canvas.create_image(
                        canvas_x, canvas_y, 
                        anchor=tk.NW, 
                        image=img_tk,
                        tags='annotation'
                    )
                    self.canvas_objects.append({'id': img_id, 'annotation': annotation, 'image_ref': img_tk})
                except Exception as e:
                    print(f"Error loading image: {e}")
    
    def select_annotation(self, canvas_x, canvas_y):
        """Select an annotation at the given canvas coordinates"""
        # Find the topmost annotation at this position - use larger area for better detection
        items = self.canvas.find_overlapping(canvas_x-5, canvas_y-5, canvas_x+5, canvas_y+5)
        
        # Filter to only annotation items (exclude PDF background)
        annotation_items = [item for item in items if 'annotation' in self.canvas.gettags(item)]
        
        if annotation_items:
            # Select the topmost one
            item_id = annotation_items[-1]
            
            # Find the corresponding annotation
            for obj in self.canvas_objects:
                if obj['id'] == item_id and 'annotation' in obj and obj['annotation'] is not None:
                    # Clear previous selection
                    self.canvas.delete('selection')
                    self.canvas.delete('resize_handle')
                    
                    # Set new selection
                    self.selected_object = obj
                    self.selected_annotation = obj['annotation']
                    self.drag_data["x"] = canvas_x
                    self.drag_data["y"] = canvas_y
                    self.drag_data["item"] = item_id
                    self.drag_data["active"] = True
                    
                    # Highlight after setting data
                    self.highlight_selection(item_id)
                    
                    if self.selected_annotation and self.selected_annotation.get('type') == 'image':
                        self.draw_resize_handles()
                    
                    ann_type = self.selected_annotation.get('type', 'unknown') if self.selected_annotation else 'unknown'
                    self.status_bar.config(text=f"Selected {ann_type}: Drag to move" + 
                                         (" or use handles to resize" if ann_type == 'image' else ""))
                    return
        
        # Nothing selected
        self.clear_selection()
    
    def highlight_selection(self, item_id):
        """Highlight the selected item"""
        # Only clear the visual elements, not the selection data
        self.canvas.delete('selection')
        self.canvas.delete('resize_handle')
        
        bbox = self.canvas.bbox(item_id)
        if bbox:
            self.selection_rect = self.canvas.create_rectangle(
                bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2,
                outline='blue', width=2, tags='selection'
            )
    
    def clear_selection(self):
        """Clear the current selection"""
        self.canvas.delete('selection')
        self.canvas.delete('resize_handle')
        self.selected_object = None
        self.selected_annotation = None
        self.resize_handles = []
        self.resize_mode = None
        self.drag_data = {"x": 0, "y": 0, "item": None, "active": False}
    
    def delete_selected(self):
        """Delete the currently selected annotation"""
        if not self.selected_annotation:
            self.status_bar.config(text="No annotation selected to delete")
            return
        
        # Confirm deletion
        ann_type = self.selected_annotation.get('type', 'item')
        text_preview = ""
        if ann_type == 'text':
            text_preview = f" '{self.selected_annotation.get('text', '')[:30]}'"
        
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete this {ann_type}{text_preview}?"
        )
        
        if not confirm:
            return
        
        # Remove from annotations list
        if self.selected_annotation in self.annotations:
            self.annotations.remove(self.selected_annotation)
        
        # Clear selection and redraw
        self.clear_selection()
        self.redraw_current_page_annotations()
        
        self.status_bar.config(text=f"Deleted {ann_type}")
    
    def draw_resize_handles(self):
        """Draw resize handles for the selected image"""
        if not self.selected_annotation or self.selected_annotation['type'] != 'image':
            return
        
        self.canvas.delete('resize_handle')
        self.resize_handles = []
        
        ann = self.selected_annotation
        x = ann['x'] * self.zoom
        y = ann['y'] * self.zoom
        w = ann['width'] * self.zoom
        h = ann['height'] * self.zoom
        
        # Create 8 resize handles (corners and midpoints)
        handle_size = 8
        positions = [
            ('nw', x, y),
            ('n', x + w/2, y),
            ('ne', x + w, y),
            ('e', x + w, y + h/2),
            ('se', x + w, y + h),
            ('s', x + w/2, y + h),
            ('sw', x, y + h),
            ('w', x, y + h/2)
        ]
        
        for pos_name, hx, hy in positions:
            handle = self.canvas.create_rectangle(
                hx - handle_size/2, hy - handle_size/2,
                hx + handle_size/2, hy + handle_size/2,
                fill='white', outline='blue', width=2,
                tags='resize_handle'
            )
            self.resize_handles.append({'id': handle, 'position': pos_name, 'x': hx, 'y': hy})
    
    def check_resize_handle_click(self, canvas_x, canvas_y):
        """Check if a resize handle was clicked"""
        for handle in self.resize_handles:
            handle_bbox = self.canvas.bbox(handle['id'])
            if handle_bbox:
                if (handle_bbox[0] <= canvas_x <= handle_bbox[2] and
                    handle_bbox[1] <= canvas_y <= handle_bbox[3]):
                    self.resize_mode = handle['position']
                    self.drag_data["x"] = canvas_x
                    self.drag_data["y"] = canvas_y
                    self.drag_data["active"] = True
                    self.status_bar.config(text=f"Resizing image from {handle['position']} handle")
                    return True
        return False
    
    def on_canvas_drag(self, event):
        """Handle dragging of annotations"""
        if not self.selected_annotation or self.mode != "edit":
            return
        
        if not self.drag_data.get("active"):
            return
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        dx = canvas_x - self.drag_data["x"]
        dy = canvas_y - self.drag_data["y"]
        
        # Skip tiny movements to avoid jitter
        if abs(dx) < 0.5 and abs(dy) < 0.5:
            return
        
        if self.resize_mode and self.selected_annotation['type'] == 'image':
            # Resize image
            self.resize_image(dx, dy)
        elif self.drag_data.get("item"):
            # Move annotation
            self.canvas.move(self.drag_data["item"], dx, dy)
            self.canvas.move('selection', dx, dy)
            
            # Update annotation position
            self.selected_annotation['x'] += dx / self.zoom
            self.selected_annotation['y'] += dy / self.zoom
            
            if self.selected_annotation['type'] == 'image':
                # Update resize handles
                for handle in self.resize_handles:
                    self.canvas.move(handle['id'], dx, dy)
        
        self.drag_data["x"] = canvas_x
        self.drag_data["y"] = canvas_y
    
    def on_canvas_release(self, event):
        """Handle mouse release"""
        self.resize_mode = None
        if "active" in self.drag_data:
            self.drag_data["active"] = False
    
    def resize_image(self, dx, dy):
        """Resize the selected image"""
        if not self.selected_annotation or self.selected_annotation['type'] != 'image':
            return
        
        ann = self.selected_annotation
        old_width = ann['width']
        
        # Calculate new width based on resize handle position
        if 'e' in self.resize_mode:
            ann['width'] += dx / self.zoom
        elif 'w' in self.resize_mode:
            ann['width'] -= dx / self.zoom
            ann['x'] += dx / self.zoom
        
        if 'n' in self.resize_mode or 's' in self.resize_mode:
            # For vertical resizing, adjust width proportionally
            if 's' in self.resize_mode:
                ann['width'] += dy / self.zoom
            else:
                ann['width'] -= dy / self.zoom
                ann['y'] += dy / self.zoom
        
        # Ensure minimum size
        ann['width'] = max(20, ann['width'])
        
        # Redraw if size changed
        if abs(ann['width'] - old_width) > 0.5:
            self.redraw_current_page_annotations()
    
    def redraw_current_page_annotations(self):
        """Redraw annotations without clearing the PDF background"""
        # Delete all annotation objects from canvas
        self.canvas.delete('annotation')
        self.canvas.delete('selection')
        self.canvas.delete('resize_handle')
        
        # Redraw annotations
        self.canvas_objects = []
        self.redraw_annotations()
        
        # Reselect if there was a selection
        if self.selected_annotation:
            for obj in self.canvas_objects:
                if obj['annotation'] == self.selected_annotation:
                    self.selected_object = obj
                    self.highlight_selection(obj['id'])
                    if self.selected_annotation['type'] == 'image':
                        self.draw_resize_handles()
                    break
    
    def save_pdf(self):
        """Save the modified PDF"""
        if not self.pdf_document:
            messagebox.showwarning("Warning", "No PDF is currently open")
            return
        
        if not self.annotations:
            messagebox.showinfo("Info", "No annotations to save")
            return
        
        # Ask for output filename
        while True:
            filename = filedialog.asksaveasfilename(
                title="Save PDF as",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                confirmoverwrite=False  # Disable system overwrite dialog
            )
            
            if not filename:
                # User cancelled
                self.status_bar.config(text="Save cancelled")
                return
            
            # Check if file already exists AFTER user makes selection
            if os.path.exists(filename):
                messagebox.showerror(
                    "File Already Exists",
                    f"The file '{os.path.basename(filename)}' already exists.\n\n"
                    "Please choose a different name or location.\n"
                    "Overwriting existing files is not allowed."
                )
                # Loop back to ask for filename again
                continue
            
            # File doesn't exist, proceed with save
            break
        
        try:
            # Store current page and zoom
            original_page = self.current_page_num
            original_zoom = self.zoom
            
            # Set high quality zoom for rendering
            render_zoom = 2.0
            
            # List to store rendered page images
            page_images = []
            
            # Create a temporary directory for page images
            import tempfile
            temp_dir = tempfile.mkdtemp()
            
            # Render each page with annotations
            total_pages = len(self.pdf_document)
            for page_num in range(total_pages):
                # Get page without changing the UI state
                page = self.pdf_document[page_num]
                
                # Render page to pixmap
                mat = fitz.Matrix(render_zoom, render_zoom)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Draw annotations on this page
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(img)
                
                for annotation in self.annotations:
                    if annotation['page'] != page_num:
                        continue
                    
                    if annotation['type'] == 'text':
                        # Draw text
                        canvas_x = int(annotation['x'] * render_zoom)
                        canvas_y = int(annotation['y'] * render_zoom)
                        font_size = int(annotation['font_size'] * render_zoom)
                        color = annotation.get('color', '#000000')
                        
                        try:
                            # Try to use a TrueType font
                            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                        except Exception:
                            # Fall back to default font
                            font = ImageFont.load_default()
                        
                        draw.text((canvas_x, canvas_y), annotation['text'], fill=color, font=font)
                    
                    elif annotation['type'] == 'image':
                        # Draw image
                        canvas_x = int(annotation['x'] * render_zoom)
                        canvas_y = int(annotation['y'] * render_zoom)
                        width = int(annotation['width'] * render_zoom)
                        
                        try:
                            ann_img = Image.open(annotation['path'])
                            aspect_ratio = ann_img.height / ann_img.width
                            height = int(width * aspect_ratio)
                            ann_img_resized = ann_img.resize((width, height), Image.Resampling.LANCZOS)
                            
                            # Paste with transparency support
                            if ann_img_resized.mode == 'RGBA':
                                img.paste(ann_img_resized, (canvas_x, canvas_y), ann_img_resized)
                            else:
                                img.paste(ann_img_resized, (canvas_x, canvas_y))
                        except Exception as e:
                            print(f"Error rendering image annotation: {e}")
                
                # Save page image
                page_image_path = os.path.join(temp_dir, f"page_{page_num:04d}.png")
                img.save(page_image_path, "PNG")
                page_images.append(page_image_path)
                
                # Update status without processing events
                if self.root.winfo_exists():
                    self.status_bar.config(text=f"Rendering page {page_num + 1} of {total_pages}...")
            
            # Convert images to PDF
            if self.root.winfo_exists():
                self.status_bar.config(text="Creating PDF...")
            
            with open(filename, "wb") as f:
                f.write(img2pdf.convert(page_images))
            
            # Clean up temporary files
            import shutil
            shutil.rmtree(temp_dir)
            
            # Show success message only if window still exists
            if self.root.winfo_exists():
                messagebox.showinfo("Success", f"PDF saved successfully to:\n{filename}")
                self.status_bar.config(text=f"Saved: {filename}")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Only show error if window still exists
            if hasattr(self, 'root') and self.root.winfo_exists():
                messagebox.showerror("Error", f"Failed to save PDF: {str(e)}")
                self.status_bar.config(text="Save failed")
            else:
                print(f"Error saving PDF: {str(e)}")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # PDF file provided as argument
        pdf_file = sys.argv[1]
        if not os.path.exists(pdf_file):
            print(f"Error: File not found: {pdf_file}")
            sys.exit(1)
    
    root = tk.Tk()
    app = PDFEditor(root)
    
    # Auto-load PDF if provided
    if len(sys.argv) > 1:
        try:
            app.pdf_path = sys.argv[1]
            app.pdf_document = fitz.open(sys.argv[1])
            app.display_page()
            app.status_bar.config(text=f"Opened: {sys.argv[1]}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open PDF: {str(e)}")
    
    root.mainloop()


if __name__ == "__main__":
    main()
