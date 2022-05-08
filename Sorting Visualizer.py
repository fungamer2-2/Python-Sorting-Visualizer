from collections.abc import Collection
import tkinter as tk
import random, time
from tkinter import simpledialog, messagebox

class Visualizer():
	
	def __init__(self, root):
		self.reset_stats()
		self.main_array = None
		self.stat_var = tk.StringVar()
		self.stats = tk.Label(root, fg="white", bg="black", textvariable=self.stat_var, font=("Arial", 6))
		self.stats.pack()
		canvas = tk.Canvas(root, bg="black")
		canvas.configure(highlightthickness=0)
		canvas.pack()
		canvas.update()
		self.canvas = canvas
		self.rects = []
		self.marks = []
		self.delay_count = 0
		self.sleep_ratio = 1
		
	def set_main_array(self, arr):
		self.main_array = arr
		random.shuffle(self.main_array._data)
		self.rects = [None] * len(arr)
		self.marks = []
		width = self.canvas.winfo_width()
		height = self.canvas.winfo_height()
		self.canvas.delete("all")
		for i in range(len(arr)):
			x = width * (i / len(arr))
			bar = height * (arr[i] / len(arr))
			self.rects[i] = self.canvas.create_rectangle(width * (i / len(arr)), height, width * ((i + 1) / len(arr)), height - bar, fill="#ffffff", outline="")
		self.canvas.update()
		
	def reset_stats(self):
		self.comps = 0
		self.writes = 0
		self.aux_writes = 0
		self.swaps = 0
		self.extra_space = 0
		self.mark_finish = -1
		
	def update_statistics(self):
		self.stat_var.set(f"Swaps: {self.swaps}\nComparisons: {self.comps}\nMain Array Writes: {self.writes}\nAuxiliary Array Writes: {self.aux_writes}\nAuxiliary Memory: {self.extra_space} items")
		
	def update(self):
		width = self.canvas.winfo_width()
		height = self.canvas.winfo_height()
		for i in range(len(arr)):
			x = width * i / len(arr)
			bar = height * arr[i] / len(arr)
			marked = any(mark == i for mark in self.marks)
			if i < self.mark_finish:
				color = "#00ff00"
			elif i == self.mark_finish:
				color = "red"
			else:
				color = "red" if marked else "white"
			self.canvas.itemconfig(self.rects[i], fill=color)
			self.canvas.coords(self.rects[i], width * (i / len(arr)), height, width * ((i + 1) / len(arr)), height - bar)
		self.update_statistics()
		self.canvas.update()
		
	def display_finish_animation(self):
		self.clear_all_marks()
		self.sleep_ratio = 1
		for i in range(len(self.main_array)):
			self.mark_finish = i
			self.sleep(1000 / len(self.main_array))
		self.mark_finish = -1
		self.update()
		
	def sleep(self, ms):
		self.delay_count += ms / self.sleep_ratio
		while self.delay_count > 0:
			start = time.time()
			self.update()
			end = time.time()
			t = (end - start) * 1000
			self.delay_count -= t
			
	def _ensure_mark_capacity(self, n):
		if len(self.marks) < n:
			self.marks.extend([-1] * (n - len(self.marks)))
			
	def mark(self, id, index):
		if not isinstance(index, int):
			raise TypeError("index must be an int")
		self._ensure_mark_capacity(id + 1)
		self.marks[id] = index
		
	def clear_all_marks(self):
		self.marks = []
		
	def compare_values(self, d1, d2):
		self.comps += 1
		return (d1 > d2) - (d1 < d2)
		
	def compare_indices(self, array, a, b, sleep, mark): 
		comp = self.compare_values(array[a], array[b])
		if mark:
			self.mark(1, a)
			self.mark(2, b)
			self.sleep(sleep)
		return comp
		
	def swap(self, array, a, b, sleep, mark):
		self.swaps += 1
		array[a], array[b] = array[b], array[a]
		if mark:
			self.mark(1, a)
			self.mark(2, b)
			self.sleep(sleep)
		
	def write(self, array, index, value, sleep, mark):
		array[index] = value
		if mark:
			self.mark(1, index)
			self.sleep(sleep)
		
class VisArray(Collection):
	vis = None
	
	@classmethod
	def set_visualizer(cls, vis):
		cls.vis = vis
	
	def __init__(self, n, init_sorted=False):
		if init_sorted:
			self._data = list(range(1, n + 1))
		else:
			self._data = [0] * n
		if self.vis != None and self.aux:
			self.vis.extra_space += n
			
	def __del__(self):
		if self.aux:
			self.vis.extra_space -= len(self._data)
		
	def inc_writes(self, amount=1):
		if self.aux:
			self.vis.aux_writes += amount
		else:
			self.vis.writes += amount
	
	@property	
	def aux(self):
		return self is not self.vis.main_array
	
	def __setitem__(self, index, value):
		self.inc_writes()
		self._data[index] = value
	
	def __getitem__(self, index):
		return self._data[index]
		
	def __contains__(self, value):
		for i in range(len(self._data)):
			self.vis.comps += 1
			if self[i] == value:
				return True
		return False
		
	def __len__(self):
		return len(self._data)
	
	def __iter__(self):
		return iter(self._data)
		
	def __str__(self):
		return str(self._data)
		
root = tk.Tk()
root.configure(bg="black")
root.geometry("1720x720")

arr = VisArray(128, init_sorted=True)	
vis = Visualizer(root)
vis.set_main_array(arr)
VisArray.set_visualizer(vis)

algorithms = []

class SortingAlgorithm:
	
	def __init__(self, name):
		self.name = name
		self.func = None
		
	def __call__(self, func):
		self.func = func
		algorithms.append(self)
		return self
		
	def run(self):
		self.func(arr, vis)
		vis.display_finish_animation()

@SortingAlgorithm("Bubble Sort")		
def BubbleSort(array, vis):
	for i in reversed(range(1, len(array))):
		for j in range(i):
			vis.mark(1, j + 1)
			vis.mark(2, j + 1)
			if vis.compare_indices(array, j, j + 1, 3, True) > 0:
				vis.swap(array, j, j + 1, 3, True)
				
@SortingAlgorithm("Selection Sort")
def SelectionSort(array, vis):
	for i in range(len(array) - 1):
		m = i
		vis.mark(3, i)
		for j in range(i + 1, len(array)):
			if vis.compare_indices(array, j, m, 4, True) < 0:
				m = j
		vis.swap(array, i, m, 4, True)	

@SortingAlgorithm("Insertion Sort")
def InsertionSort(array, vis):
	for i in range(1, len(array)):
		tmp = array[i]
		j = i - 1
		while j >= 0 and vis.compare_values(array[j], tmp) > 0:
			vis.write(array, j + 1, array[j], 4, True)
			j -= 1
		vis.write(array, j + 1, tmp, 4, True)

def choose_sort():
	sort_str = [ "Enter the number corresponding to the sorting algorithm you want to visualize" ]
	for id, sort in enumerate(algorithms):
		sort_str.append(f"{id+1} - {sort.name}")
	while True:
		num = None
		while num == None:
			num = simpledialog.askinteger("Choose Sort", "\n".join(sort_str))
		if not 1 <= num <= len(algorithms):
			messagebox.showerror("Error", "Invalid sort number")
			continue
		return algorithms[num - 1]
	
sort = choose_sort()
sort.run()
root.mainloop()
