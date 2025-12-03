import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import random
import math
from datetime import datetime

class CacheSimulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cache Memory Simulator")
        self.root.geometry("1200x800")
        
        # Cache parameters
        self.cache_size = 0
        self.words_per_block = 0
        self.mapping_policy = ""
        self.blocks_per_set = 0
        self.num_blocks = 0
        self.num_sets = 0
        self.offset_bits = 0
        self.index_bits = 0
        self.tag_bits = 0
        self.real_cache_size = 0
        self.cache = []
        self.access_history = []
        self.hits = 0
        self.misses = 0
        self.word_size_bytes = 4
        
        # Colors for visualization
        self.color_invalid = "#E8E8E8"
        self.color_valid = "#90EE90"
        self.color_hit = "#FFD700"
        self.color_miss = "#FF6B6B"
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuration Frame
        config_frame = ttk.LabelFrame(main_frame, text="Cache Configuration", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Cache size
        ttk.Label(config_frame, text="Cache Size (Bytes):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.cache_size_var = tk.StringVar(value="256")
        ttk.Entry(config_frame, textvariable=self.cache_size_var, width=15).grid(row=0, column=1, pady=2)
        
        # Words per block
        ttk.Label(config_frame, text="Words per Block:").grid(row=0, column=2, sticky=tk.W, padx=(20,0), pady=2)
        self.words_per_block_var = tk.StringVar(value="4")
        ttk.Combobox(config_frame, textvariable=self.words_per_block_var, 
                     values=[1, 2, 4, 8], width=10, state="readonly").grid(row=0, column=3, pady=2)
        
        # Mapping policy
        ttk.Label(config_frame, text="Mapping Policy:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.mapping_var = tk.StringVar(value="DM")
        ttk.Radiobutton(config_frame, text="Direct Mapped", variable=self.mapping_var, 
                       value="DM", command=self.on_mapping_change).grid(row=1, column=1, sticky=tk.W, pady=2)
        ttk.Radiobutton(config_frame, text="Set Associative", variable=self.mapping_var, 
                       value="SA", command=self.on_mapping_change).grid(row=1, column=2, sticky=tk.W, pady=2)
        
        # Blocks per set
        ttk.Label(config_frame, text="Blocks per Set (N-way):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.blocks_per_set_var = tk.StringVar(value="2")
        self.blocks_per_set_entry = ttk.Entry(config_frame, textvariable=self.blocks_per_set_var, width=15)
        self.blocks_per_set_entry.grid(row=2, column=1, pady=2)
        self.blocks_per_set_entry.config(state="disabled")
        
        # Configure button
        ttk.Button(config_frame, text="Configure Cache", 
                  command=self.configure_cache).grid(row=3, column=0, columnspan=4, pady=10)
        
        # Parameters Display Frame
        params_frame = ttk.LabelFrame(main_frame, text="Cache Parameters", padding="10")
        params_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.params_text = scrolledtext.ScrolledText(params_frame, height=8, width=50, wrap=tk.WORD)
        self.params_text.pack(fill=tk.BOTH, expand=True)
        
        # Access Frame
        access_frame = ttk.LabelFrame(main_frame, text="Memory Access", padding="10")
        access_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=5)
        
        ttk.Label(access_frame, text="Word Address:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.address_var = tk.StringVar()
        ttk.Entry(access_frame, textvariable=self.address_var, width=20).grid(row=0, column=1, pady=5)
        ttk.Button(access_frame, text="Access", command=self.access_word).grid(row=0, column=2, padx=5, pady=5)
        
        # Statistics
        stats_frame = ttk.Frame(access_frame)
        stats_frame.grid(row=1, column=0, columnspan=3, pady=10)
        
        self.hits_label = ttk.Label(stats_frame, text="Hits: 0", font=("Arial", 10, "bold"))
        self.hits_label.grid(row=0, column=0, padx=10)
        
        self.misses_label = ttk.Label(stats_frame, text="Misses: 0", font=("Arial", 10, "bold"))
        self.misses_label.grid(row=0, column=1, padx=10)
        
        self.hit_rate_label = ttk.Label(stats_frame, text="Hit Rate: 0.00%", font=("Arial", 10, "bold"))
        self.hit_rate_label.grid(row=0, column=2, padx=10)
        
        # Buttons
        button_frame = ttk.Frame(access_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=5)
        
        ttk.Button(button_frame, text="Clear Cache", command=self.clear_cache).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="View History", command=self.show_history).grid(row=0, column=1, padx=5)
        
        # Simulation buttons
        sim_frame = ttk.LabelFrame(access_frame, text="Simulation", padding="5")
        sim_frame.grid(row=3, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(sim_frame, text="Num Accesses:").grid(row=0, column=0, sticky=tk.W)
        self.sim_accesses_var = tk.StringVar(value="100")
        ttk.Entry(sim_frame, textvariable=self.sim_accesses_var, width=10).grid(row=0, column=1)
        
        ttk.Button(sim_frame, text="Random", command=self.simulate_random).grid(row=1, column=0, pady=5)
        ttk.Button(sim_frame, text="With Locality", command=self.simulate_locality).grid(row=1, column=1, pady=5)
        
        # Cache Visualization Frame
        viz_frame = ttk.LabelFrame(main_frame, text="Cache Visualization", padding="10")
        viz_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Canvas for cache visualization
        self.canvas_frame = ttk.Frame(viz_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", height=300)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Legend
        legend_frame = ttk.Frame(viz_frame)
        legend_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(legend_frame, text="Legend:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Label(legend_frame, text="  Invalid  ", bg=self.color_invalid, relief=tk.RIDGE).pack(side=tk.LEFT, padx=2)
        tk.Label(legend_frame, text="  Valid  ", bg=self.color_valid, relief=tk.RIDGE).pack(side=tk.LEFT, padx=2)
        tk.Label(legend_frame, text="  Hit  ", bg=self.color_hit, relief=tk.RIDGE).pack(side=tk.LEFT, padx=2)
        tk.Label(legend_frame, text="  Miss  ", bg=self.color_miss, relief=tk.RIDGE).pack(side=tk.LEFT, padx=2)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
    
    def on_mapping_change(self):
        """Enable/disable blocks per set based on mapping policy"""
        if self.mapping_var.get() == "SA":
            self.blocks_per_set_entry.config(state="normal")
        else:
            self.blocks_per_set_entry.config(state="disabled")
    
    def configure_cache(self):
        """Configure the cache with user parameters"""
        try:
            self.cache_size = int(self.cache_size_var.get())
            self.words_per_block = int(self.words_per_block_var.get())
            self.mapping_policy = self.mapping_var.get()
            
            if self.mapping_policy == "SA":
                self.blocks_per_set = int(self.blocks_per_set_var.get())
            else:
                self.blocks_per_set = 1
            
            # Calculate parameters
            block_size_bytes = self.words_per_block * self.word_size_bytes
            self.num_blocks = self.cache_size // block_size_bytes
            self.num_sets = self.num_blocks // self.blocks_per_set
            
            self.offset_bits = int(math.log2(self.words_per_block)) if self.words_per_block > 1 else 0
            self.index_bits = int(math.log2(self.num_sets)) if self.num_sets > 1 else 0
            self.tag_bits = 32 - self.offset_bits - self.index_bits
            
            # Calculate real size
            data_bits_per_block = self.words_per_block * self.word_size_bytes * 8
            tag_bits_per_block = self.tag_bits
            valid_bits_per_block = 1
            lru_bits_per_set = int(math.ceil(math.log2(self.blocks_per_set))) if self.blocks_per_set > 1 else 0
            
            overhead_per_block = tag_bits_per_block + valid_bits_per_block
            total_bits = self.num_blocks * (data_bits_per_block + overhead_per_block) + self.num_sets * lru_bits_per_set
            self.real_cache_size = total_bits / 8
            
            # Initialize cache
            self.cache = []
            for _ in range(self.num_sets):
                cache_set = []
                for _ in range(self.blocks_per_set):
                    block = {
                        'valid': False,
                        'tag': None,
                        'data': [None] * self.words_per_block,
                        'lru_counter': 0
                    }
                    cache_set.append(block)
                self.cache.append(cache_set)
            
            self.access_history = []
            self.hits = 0
            self.misses = 0
            
            # Display parameters
            self.display_parameters()
            self.visualize_cache()
            
            messagebox.showinfo("Success", "Cache configured successfully!")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
    
    def display_parameters(self):
        """Display cache parameters"""
        self.params_text.delete(1.0, tk.END)
        
        params = f"""Cache Configuration:
• Nominal Size: {self.cache_size} Bytes
• Words per Block: {self.words_per_block}
• Block Size: {self.words_per_block * self.word_size_bytes} Bytes
• Mapping: {'Direct Mapped' if self.mapping_policy == 'DM' else f'{self.blocks_per_set}-way Set Associative'}

Cache Structure:
• Number of Blocks: {self.num_blocks}
• Number of Sets: {self.num_sets}

Address Partitioning (32-bit):
• Tag bits: {self.tag_bits}
• Index bits: {self.index_bits}
• Offset bits: {self.offset_bits}

Real Cache Size: {self.real_cache_size:.2f} Bytes"""
        
        self.params_text.insert(1.0, params)
    
    def access_word(self):
        """Access a word in cache"""
        if not self.cache:
            messagebox.showwarning("Warning", "Please configure cache first!")
            return
        
        try:
            address = int(self.address_var.get())
            self._perform_access(address, highlight=True)
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid integer address!")
    
    def _perform_access(self, address, highlight=False):
        """Perform cache access"""
        # Parse address
        offset = address & ((1 << self.offset_bits) - 1) if self.offset_bits > 0 else 0
        index = (address >> self.offset_bits) & ((1 << self.index_bits) - 1) if self.index_bits > 0 else 0
        tag = address >> (self.offset_bits + self.index_bits)
        
        # Check cache
        cache_set = self.cache[index]
        hit = False
        hit_way = -1
        
        for way, block in enumerate(cache_set):
            if block['valid'] and block['tag'] == tag:
                hit = True
                hit_way = way
                break
        
        if hit:
            self.hits += 1
            status = "HIT"
            self._update_lru(index, hit_way)
        else:
            self.misses += 1
            status = "MISS"
            replace_way = self._find_lru_block(index)
            cache_set[replace_way]['valid'] = True
            cache_set[replace_way]['tag'] = tag
            cache_set[replace_way]['data'] = [f"W{address - offset + i}" for i in range(self.words_per_block)]
            self._update_lru(index, replace_way)
            hit_way = replace_way
        
        # Record access
        self.access_history.append({
            'address': address,
            'tag': tag,
            'index': index,
            'offset': offset,
            'status': status,
            'way': hit_way,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
        
        # Update display
        self.update_statistics()
        self.visualize_cache(highlight_set=index if highlight else None, 
                            highlight_way=hit_way if highlight else None,
                            highlight_color=self.color_hit if hit else self.color_miss)
    
    def _update_lru(self, set_index, accessed_way):
        """Update LRU counters"""
        cache_set = self.cache[set_index]
        for block in cache_set:
            if block['valid']:
                block['lru_counter'] += 1
        cache_set[accessed_way]['lru_counter'] = 0
    
    def _find_lru_block(self, set_index):
        """Find LRU block"""
        cache_set = self.cache[set_index]
        for way, block in enumerate(cache_set):
            if not block['valid']:
                return way
        max_lru = -1
        lru_way = 0
        for way, block in enumerate(cache_set):
            if block['lru_counter'] > max_lru:
                max_lru = block['lru_counter']
                lru_way = way
        return lru_way
    
    def update_statistics(self):
        """Update statistics display"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        self.hits_label.config(text=f"Hits: {self.hits}")
        self.misses_label.config(text=f"Misses: {self.misses}")
        self.hit_rate_label.config(text=f"Hit Rate: {hit_rate:.2f}%")
    
    def visualize_cache(self, highlight_set=None, highlight_way=None, highlight_color=None):
        """Visualize cache contents"""
        self.canvas.delete("all")
        
        if not self.cache:
            return
        
        x_start = 10
        y_start = 10
        block_width = 150
        block_height = 40
        x_spacing = 10
        y_spacing = 10
        
        for set_idx, cache_set in enumerate(self.cache):
            # Draw set label
            y_pos = y_start + set_idx * (block_height * self.blocks_per_set + y_spacing + 20)
            self.canvas.create_text(x_start, y_pos, text=f"Set {set_idx}:", anchor=tk.W, font=("Arial", 10, "bold"))
            
            for way_idx, block in enumerate(cache_set):
                x_pos = x_start + 50
                block_y = y_pos + 15 + way_idx * (block_height + 5)
                
                # Determine color
                if highlight_set == set_idx and highlight_way == way_idx and highlight_color:
                    color = highlight_color
                elif block['valid']:
                    color = self.color_valid
                else:
                    color = self.color_invalid
                
                # Draw block
                self.canvas.create_rectangle(x_pos, block_y, x_pos + block_width, block_y + block_height,
                                            fill=color, outline="black", width=2)
                
                # Draw content
                if block['valid']:
                    text = f"Way {way_idx} | Tag: {block['tag']} | LRU: {block['lru_counter']}"
                else:
                    text = f"Way {way_idx} | INVALID"
                
                self.canvas.create_text(x_pos + block_width // 2, block_y + block_height // 2,
                                       text=text, font=("Arial", 8))
        
        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def clear_cache(self):
        """Clear cache"""
        if not self.cache:
            messagebox.showwarning("Warning", "Cache not configured!")
            return
        
        for cache_set in self.cache:
            for block in cache_set:
                block['valid'] = False
                block['tag'] = None
                block['data'] = [None] * self.words_per_block
                block['lru_counter'] = 0
        
        self.access_history = []
        self.hits = 0
        self.misses = 0
        self.update_statistics()
        self.visualize_cache()
        messagebox.showinfo("Success", "Cache cleared!")
    
    def show_history(self):
        """Show access history in new window"""
        if not self.access_history:
            messagebox.showinfo("Info", "No access history yet!")
            return
        
        history_window = tk.Toplevel(self.root)
        history_window.title("Access History")
        history_window.geometry("800x400")
        
        text = scrolledtext.ScrolledText(history_window, wrap=tk.NONE)
        text.pack(fill=tk.BOTH, expand=True)
        
        header = f"{'Time':<12} {'Address':<10} {'Tag':<10} {'Index':<8} {'Offset':<8} {'Set':<6} {'Way':<6} {'Status':<8}\n"
        text.insert(tk.END, header)
        text.insert(tk.END, "-" * 90 + "\n")
        
        for record in self.access_history:
            line = f"{record['timestamp']:<12} {record['address']:<10} {record['tag']:<10} {record['index']:<8} "
            line += f"{record['offset']:<8} {record['index']:<6} {record['way']:<6} {record['status']:<8}\n"
            text.insert(tk.END, line)
    
    def simulate_random(self):
        """Simulate random accesses"""
        if not self.cache:
            messagebox.showwarning("Warning", "Please configure cache first!")
            return
        
        try:
            num_accesses = int(self.sim_accesses_var.get())
            
            for _ in range(num_accesses):
                address = random.randint(0, 1000)
                self._perform_access(address, highlight=False)
            
            self.visualize_cache()
            messagebox.showinfo("Success", f"Simulation complete! {num_accesses} random accesses.")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid number of accesses!")
    
    def simulate_locality(self):
        """Simulate accesses with locality"""
        if not self.cache:
            messagebox.showwarning("Warning", "Please configure cache first!")
            return
        
        try:
            num_accesses = int(self.sim_accesses_var.get())
            base_address = random.randint(0, 500)
            locality_window = 16
            
            for i in range(num_accesses):
                if random.random() < 0.8:
                    address = base_address + random.randint(0, locality_window - 1)
                else:
                    base_address = random.randint(0, 500)
                    address = base_address
                
                self._perform_access(address, highlight=False)
                
                if i % 50 == 0 and i > 0:
                    base_address = random.randint(0, 500)
            
            self.visualize_cache()
            messagebox.showinfo("Success", f"Simulation complete! {num_accesses} accesses with locality.")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid number of accesses!")

if __name__ == "__main__":
    root = tk.Tk()
    app = CacheSimulatorGUI(root)
    root.mainloop()
