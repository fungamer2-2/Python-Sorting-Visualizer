from collections.abc import Collection
import tkinter as tk
import random, time
from tkinter import simpledialog, messagebox

class Timer():
	
	def __init__(self):
		self.start = -1
		self.end = -1
		self._time = None
		
	def start_lap(self):
		if self.start != -1:
			raise ValueError("start_lap() has already been called; call stop_lap() before you can start a new lap")
		self.start = time.time()
		self.end = -1
		self._time = None
		
	def stop_lap(self):
		if self.end != -1:
			raise ValueError("a lap is not in progress; call start_lap() to start a lap")
		self.end = time.time()
		self._time = self.end - self.start
		self.start = -1
		
	def get_time(self):
		if self._time == None:
			raise ValueError("at least one lap needs to be completed before calling get_time()")
		return self._time
		
	def __enter__(self):
		self.start_lap()
		return self
		
	def __exit__(self, *args):
		self.stop_lap()
		
class VisTimer:
		
	def __init__(self, vis):
		self.vis = vis
		self.timer = Timer()
	
	def __enter__(self):
		self.timer.start_lap()
		return self
		
	def __exit__(self, *args):
		self.timer.stop_lap()
		self.vis.real_time += self.timer.get_time()
		
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
		self.aux_arrays = []
		self.aux_rects = []
		self.real_time = 0
		self.timer = VisTimer(self)
		
	def set_main_array(self, arr):
		self.main_array = arr
		random.shuffle(self.main_array._data)
		self.rects = [None] * len(arr)
		self.marks = []
		width = self.canvas.winfo_width()
		height = self.canvas.winfo_height()
		self.update()
		
	def reset_stats(self):
		self.comps = 0
		self.writes = 0
		self.aux_writes = 0
		self.swaps = 0
		self.extra_space = 0
		self.mark_finish = -1
		
	def update_statistics(self):
		self.stat_var.set(f"Swaps: {self.swaps}\nComparisons: {self.comps}\nMain Array Writes: {self.writes}\nAuxiliary Array Writes: {self.aux_writes}\nAuxiliary Memory: {self.extra_space} items\nReal Time: {(self.real_time * 1000):.2f} ms")
		
	def update(self):
		arr = self.main_array
		width = self.canvas.winfo_width()
		height = self.canvas.winfo_height()
		height_ratio = len(self.aux_arrays) + 1
		self.canvas.delete("all")
		for i in range(len(arr)):
			x = width * i / len(arr)
			bar = height / height_ratio * arr[i] / len(arr)
			marked = any(mark == i for mark in self.marks)
			if i < self.mark_finish:
				color = "#00ff00"
			elif i == self.mark_finish:
				color = "red"
			else:
				color = "red" if marked else "white"
			self.canvas.create_rectangle(self.rects[i], width * (i / len(arr)), height, width * ((i + 1) / len(arr)), height - bar, fill=color, outline="")
		for j in range(len(self.aux_arrays)):
			arr = self.aux_arrays[j]
			for i in range(len(arr)):
				x = width * i / len(arr)
				begin = height - (height * (j + 1) / height_ratio)
				bar = height / height_ratio * arr[i] / len(arr)
				self.canvas.create_rectangle(self.rects[i], width * (i / len(arr)), begin, width * ((i + 1) / len(arr)), begin - bar, fill="white", outline="")
		self.update_statistics()
		self.canvas.update()
	
	def display_finish_animation(self):
		self.clear_all_marks()
		self.aux_arrays.clear()
		self.sleep_ratio = 1
		for i in range(len(self.main_array)):
			if i < len(self.main_array) - 1:
				if self.main_array[i] > self.main_array[i + 1]:
					messagebox.showerror("Sorting failed", f"The sorting algorithm was unsuccessful.\nItems {i} and {i + 1} are out of order.")
					self.mark_finish = -1
					return
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
		
	def clear_mark(self, id):
		self.marks[id] = -1
		if id == len(self.marks) - 1:
			last = next((i for i in reversed(range(len(self.marks))) if self.marks[id] != -1), None)
			if last is None:
				self.marks.clear()
			else:
				del self.marks[last+1:]
		
	def clear_all_marks(self):
		self.marks = []
		
	def compare_values(self, d1, d2):
		self.comps += 1
		with self.timer:
			result = (d1 > d2) - (d1 < d2)
		return result
		
	def comp_swap(self, array, a, b, sleep, mark):
		comp = self.compare_indices(array, a, b, 0, False)
		if comp:
			self.swap(array, a, b, sleep, mark)
		else:
			self.mark(1, a)
			self.mark(2, b)
		return comp
		
	def compare_indices(self, array, a, b, sleep, mark): 
		comp = self.compare_values(array[a], array[b])
		if mark:
			self.mark(1, a)
			self.mark(2, b)
			self.sleep(sleep)
		return comp
		
	def swap(self, array, a, b, sleep, mark):
		self.swaps += 1
		with self.timer:
			array[a], array[b] = array[b], array[a]
		if mark:
			self.mark(1, a)
			self.mark(2, b)
			self.sleep(sleep)
		
	def write(self, array, index, value, sleep, mark):
		with self.timer:	
			array[index] = value
		if mark:
			self.mark(1, index)
			self.sleep(sleep)
		
class VisArray(Collection):
	vis = None
	
	@classmethod
	def set_visualizer(cls, vis):
		cls.vis = vis
	
	def __init__(self, n, init_sorted=False, show_aux=True):
		if init_sorted:
			self._data = list(range(1, n + 1))
		else:
			self._data = [0] * n
		if self.vis != None and self.aux:
			self.vis.extra_space += n
			if show_aux:
				self.vis.aux_arrays.append(self)
			
	def __del__(self):
		if self.aux:
			self.vis.extra_space -= len(self._data)
			if self in self.vis.aux_arrays:
				self.vis.aux_arrays.remove(self) 
				
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
	
	def __init__(self, name, *, disabled=False):
		self.name = name
		self.disabled = disabled
		self.func = None
		
	def __call__(self, func):
		self.func = func
		if not self.disabled:
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
		
@SortingAlgorithm("Comb Sort")
def CombSort(array, vis):
	gap = len(array) * 10 // 13
	sorted = False
	while gap > 1 or not sorted:
		sorted = True
		for i in range(len(array) - gap):
			if vis.compare_indices(array, i, i + gap, 6, True) > 0:
				vis.swap(array, i, i + gap, 6, True)
				sorted = False
		if gap > 1:
			gap = gap*10//13
		
@SortingAlgorithm("Odd-Even Sort")
def OddEvenSort(array, vis):
	sorted = False
	while not sorted:
		sorted = True
		for i in range(0, len(array) - 1, 2):
			if vis.compare_indices(array, i, i + 1, 3, True) > 0:
				vis.swap(array, i, i + 1, 3, True)
				sorted = False
		for i in range(1, len(array) - 1, 2):
			if vis.compare_indices(array, i, i + 1, 3, True) > 0:
				vis.swap(array, i, i + 1, 3, True)
				sorted = False
				
@SortingAlgorithm("Gnome Sort")
def GnomeSort(array, vis):
	i = 0
	while i < len(array) - 1:
		if vis.compare_indices(array, i, i + 1, 3, True) > 0:
			vis.swap(array, i, i + 1, 4, True)
			if i > 0:
				i -= 1
		else:
			i += 1
				
@SortingAlgorithm("Quick Sort")
def QuickSort(array, vis):
	def partition(start, end, pivot):
		while start < end:
			while start < end and vis.compare_values(array[start], pivot) < 0:
				vis.mark(1, start)
				vis.sleep(7)
				start += 1
			while start < end and vis.compare_values(array[end], pivot) > 0:
				vis.mark(1, end)
				vis.sleep(7)
				end -= 1
			if start < end:
				vis.swap(array, start, end, 7, True)
		return start
		
	def wrapper(start, end):
		if start < end:
			piv = array[(start + end) // 2]
			pos = partition(start, end, piv)
			wrapper(start, pos)
			wrapper(pos + 1, end)
		
	wrapper(0, len(array) - 1)
				
@SortingAlgorithm("Merge Sort")
def MergeSort(array, vis):
	tmp = VisArray(len(array))
	def merge(start, mid, end):
		i = start
		j = mid + 1
		k = start
		while i <= mid and j <= end:
			if vis.compare_indices(array, i, j, 8, True) <= 0:
				vis.write(tmp, k, array[i], 0, False)
				i += 1
			else:
				vis.write(tmp, k, array[j], 0, False)
				j += 1
			k += 1
		while i <= mid:
			vis.mark(1, i)
			vis.write(tmp, k, array[i], 0, False)
			vis.sleep(8)
			i += 1
			k += 1
		while j <= end:
			vis.mark(2, j)
			vis.write(tmp, k, array[j], 0, False)
			vis.sleep(8)
			j += 1
			k += 1
		vis.clear_mark(2)
		i = start
		while i <= end:
			vis.write(array, i, tmp[i], 8, True)
			i += 1
			
	def wrapper(start, end):
		if start < end:
			mid = (start + end) // 2
			wrapper(start, mid)
			wrapper(mid + 1, end)
			merge(start, mid, end)
			
	wrapper(0, len(array) - 1)

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
