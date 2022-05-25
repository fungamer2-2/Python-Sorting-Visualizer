from collections.abc import Collection, MutableSequence
from enum import Enum
import tkinter as tk
import random, time, math
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
		self.marklist = MarkList()
		self.delay_count = 0
		self.sleep_ratio = 1
		self.aux_arrays = []
		self.real_time = 0
		self.timer = VisTimer(self)
		self.analysis = False
		
	def set_main_array(self, arr):
		self.main_array = arr
		random.shuffle(self.main_array._data)
		self.rects = [None] * len(arr)
		self.marklist.clear()
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
			marked = self.marklist.is_position_marked(i)
			if i < self.mark_finish:
				color = "#00ff00"
			elif i == self.mark_finish:
				color = "red"
			else:
				color = ("blue" if self.analysis else "red") if marked else "white"
			self.canvas.create_rectangle(self.rects[i], width * (i / len(arr)), height, width * ((i + 1) / len(arr)), height - bar, fill=color, outline="")
		for j in range(len(self.aux_arrays)):
			arr = self.aux_arrays[j]
			length = arr.capacity if type(arr) == VisArrayList else len(arr)	
			hscale = max(arr) if arr.scale_by_max else (length if arr.hscale < 0 else arr.hscale)
			if hscale < 1: #Prevent division by zero
				hscale = 1 
			for i in range(length):
				x = width * i / length
				begin = height - (height * (j + 1) / height_ratio)
				if type(arr) == VisArrayList and i >= len(arr):
					val = 0
				else:
					val = arr[i]
				bar = height / height_ratio * val / hscale
				color = "red" if arr.marklist.is_position_marked(i) else "white"
				self.canvas.create_rectangle(self.rects[i], width * (i / length), begin, width * ((i + 1) / length), begin - bar, fill=color, outline="")
		self.update_statistics()
		self.canvas.update()
	
	def display_finish_animation(self):
		self.clear_all_marks()
		for aux in self.aux_arrays:
			aux.release()
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
		if self.delay_count > 0:
			start = time.time()
			self.update()
			end = time.time()
			t = (end - start) * 1000
			self.delay_count -= t
			start = time.time()
			while self.delay_count > 0:
				time.sleep(10 / 1000)
				self.delay_count -= 10
				
	def mark(self, id, index):
		"""Marks a certain position in an array to the visualizer
		
		Usage:
		id: int - the marker number to use
		index: int - the position to set this marker at
		"""
		self.marklist.mark(id, index)
		
	def clear_mark(self, id):
		"""Clears a given marker
		
		Usage:
		id: int - the marker number to be cleared"""
		self.marklist.clear(id)
		
	def clear_all_marks(self):
		"Erases all markers in the visual"
		self.marklist.clear()
		
	def compare_values(self, d1, d2):
		"""Compares two values
		
		Usage:
		d1: int - the first number to be compared
		d2: int - the second number to be compared
		
		Returns:
		-1 if d1 < d2
		1 if d1 > d2
		0 if d1 == d2
		"""
		self.comps += 1
		with self.timer:
			result = (d1 > d2) - (d1 < d2)
		return result
		
	def comp_swap(self, array, a, b, sleep, mark, reverse=False):
		"""Compares two values in an array and swaps them if they are out of order
		
		Usage:
		array: VisArray - the array to compare and swap values in
		a: int - the first position to compare-and-swap
		b: int - the second position to compare-and-swap
		sleep: int - the duration to sleep for in the visualizer
		mark: bool - whether to place a mark at the given position
		reverse: bool (default False) - whether the comparison sign should be reversed
		
		Returns:
		True if the values were swapped, False otherwise"""
		
		comp = self.compare_indices(array, a, b, 0, False)
		if reverse:
			comp = -comp
		if comp > 0:
			self.swap(array, a, b, sleep, mark)
			return True
		elif mark:
			array.mark(1, a)
			array.mark(2, b)
			self.sleep(sleep)
		return False
		
	def compare_indices(self, array, a, b, sleep, mark): 
		"""Compares two values in an array
		
		Usage:
		array: VisArray - the array to compare and swap values in
		a: int - the first index to compare
		b: int - the second index to compare
		sleep: int - the duration to sleep for in the visualizer
		mark: bool - whether to place a mark at the given position
		
		Returns:
		-1 if array[a] < array[b]
		1 if array[a] > array[b]
		0 if array[a] == array[b]"""

		comp = self.compare_values(array[a], array[b])
		if mark:
			array.mark(1, a)
			array.mark(2, b)
			self.sleep(sleep)
		return comp
		
	def swap(self, array, a, b, sleep, mark):
		"""Swaps two values in an array
		
		Usage:
		array: VisArray - the array to swap values in
		a: int - the first index to swap
		b: int - the second position to swap
		sleep: int - the duration to sleep for in the visualizer
		mark: bool - whether to place a mark at the given positions"""
		
		self.swaps += 1
		with self.timer:
			array[a], array[b] = array[b], array[a]
		if mark:
			array.mark(1, a)
			array.mark(2, b)
			self.sleep(sleep)
		
	def write(self, array, index, value, sleep, mark):
		"""Changes one value in an array
		
		Usage:
		array: VisArray - the array in which to change a value
		index: int - the index to change the value at
		value: int - the value to change array[index] to
		sleep: int - the duration to sleep for in the visualizer
		mark: bool - whether to place a mark at the given positions"""
		
		with self.timer:	
			array[index] = value
		if mark:
			array.mark(1, index)
			self.sleep(sleep)
			
	def analyze_max(self, array, sleep, mark):
		"""Finds the maximum value in an array. Does not count as a comparison in the visualizer.
		
		Usage:
			
		array: VisArray -  the array in which to analyze the maximum
		sleep: int - the duration for which to sleep for each mark
		mark: bool - whether to display a mark during analysis
		
		Returns:
		the maximum value in the array"""

		self.analysis = True
		max = array[0]
		for i in range(len(array)):
			with self.timer:
				val = array[i]
				if val > max:
					max = val
			if mark:
				array.mark(1, i)
				self.sleep(sleep)
		self.analysis = False
		return max
		
	def analyze_max_log(self, array, base, sleep, mark):
		"""Finds the log base b of the maximum value in an array. Does not count as a comparison in the visualizer.
		
		Usage:
			
		array: VisArray -  the array in which to analyze the maximum
		base: the base of the logarithm to use
		sleep: int - the duration for which to sleep for each mark
		mark: bool - whether to display a mark during analysis
		
		Returns:
		the log in base 'base' of the maximum value in the array"""
		
		result = self.analyze_max(array, sleep, mark)
		return int(math.log(result, base))
		
	def get_digit(self, a, power, radix):
		with self.timer:
			result = (a // radix**power) % radix
		return result
		
class MarkList:
		
	def __init__(self):
		self.marks = []
		
	def _ensure_mark_capacity(self, n):
		if len(self.marks) < n:
			self.marks.extend([-1] * (n - len(self.marks)))
	
	def mark(self, id, index):
		if not isinstance(index, int):
			raise TypeError("index must be an int")
		if index < 0:
			raise ValueError(f"invalid mark position: {index}")
		self._ensure_mark_capacity(id + 1)
		self.marks[id] = index
		
	def clear(self, id=None):
		if id is None:
			self.marks.clear()
		elif id < len(self.marks):
			self.marks[id] = -1
			if id == len(self.marks) - 1:
				last = next((i for i in reversed(range(len(self.marks))) if self.marks[id] != -1), None)
				if last is None:
					self.marks.clear()
				else:
					del self.marks[last+1:]
					
	def is_position_marked(self, index):
		return any(mark == index for mark in self.marks) 
		
class VisArray(Collection):
	vis = None
	
	@classmethod
	def set_visualizer(cls, vis):
		cls.vis = vis
	
	def __init__(self, n, init_sorted=False, show_aux=True, scale_by_max=False):
		if init_sorted:
			self._data = list(range(1, n + 1))
		else:
			self._data = [0] * n
		self.scale_by_max = scale_by_max
		self.hscale = -1
		if self.aux:
			self.vis.extra_space += n
			if show_aux:
				self.vis.aux_arrays.append(self)
		if self.aux:
			self.marklist = MarkList()
		else:
			self.marklist = None
				
	def override_hscale(self, hscale):
		self.hscale = hscale
		self.scale_by_max = False
		
	def mark(self, id, index):
		if not self.aux and self.marklist is None:
			self.marklist = self.vis.marklist
		self.marklist.mark(id, index)
		
	def clear_mark(self, id):
		if not self.aux and self.marklist is None:
			self.marklist = self.vis.marklist
		self.marklist.clear(id)
		
	def clear_all_marks(self):
		if not self.aux and self.marklist is None:
			self.marklist = self.vis.marklist
		self.marklist.clear()
			
	def __del__(self):
		if self.aux and self.vis:
			self.release()
		
	def release(self):
		if self in self.vis.aux_arrays:
			self.vis.aux_arrays.remove(self) 
			self.vis.extra_space -= len(self._data)
			self._data = []
				
	def inc_writes(self, amount=1):
		if self.aux:
			self.vis.aux_writes += amount
		else:
			self.vis.writes += amount
	
	@property	
	def aux(self):
		return self.vis and self is not self.vis.main_array
	
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
		
class VisArrayList(VisArray, MutableSequence):
		
	def __init__(self, capacity=1, show_aux=True):
		super().__init__(0, False, show_aux)
		self.capacity = capacity
		
	@property
	def aux(self):
		return True
		
	def insert(self, index, item):
		self.vis.extra_space += 1
		with self.vis.timer:
			self._data.insert(index, item)
			self.vis.aux_writes += 1
		if len(self._data) > self.capacity:
			self.capacity *= 2
		
	def __delitem__(self, index):
		self.vis.extra_space -= 1
		with self.vis.timer:
			del self._data[index]
		
	def clear(self):
		self.vis.extra_space -= len(self._data)
		self._data.clear()
		
	def __del__(self):
		self.vis.extra_space -= len(self._data)
		if self in self.vis.aux_arrays:
			self.vis.aux_arrays.remove(self) 
		
root = tk.Tk()
root.configure(bg="black")
root.geometry("1720x720")

arr = VisArray(128, init_sorted=True)	
vis = Visualizer(root)
vis.set_main_array(arr)
VisArray.set_visualizer(vis)

group_names = [
    "Exchange",
    "Selection",
    "Insertion",
    "Merge",
    "Distribution",
    "Uncategorized"
]

algorithms = [[] for _ in range(len(group_names))]

class SortingAlgorithm:
	
	def __init__(self, name, *, disabled=False, group=None):
		group = "Uncategorized" if group is None else group.lower().capitalize()
		if group not in group_names:
			raise ValueError(f"invalid sort group {group!r}")
		self.name = name
		self.disabled = disabled
		self.group = group
		self.func = None
		
	def __call__(self, func):
		self.func = func
		if not self.disabled:
			index = group_names.index(self.group)
			algorithms[index].append(self)
		return self
		
	def run(self):
		self.func(arr, vis)
		vis.display_finish_animation()

@SortingAlgorithm("Bubble Sort", group="exchange")		
def BubbleSort(array, vis):
	for i in reversed(range(1, len(array))):
		for j in range(i):
			vis.comp_swap(array, j, j + 1, 4.5, True)
				
@SortingAlgorithm("Selection Sort", group="selection")
def SelectionSort(array, vis):
	for i in range(len(array) - 1):
		m = i
		vis.mark(3, i)
		for j in range(i + 1, len(array)):
			if vis.compare_indices(array, j, m, 4, True) < 0:
				m = j
		vis.swap(array, i, m, 4, True)	

@SortingAlgorithm("Insertion Sort", group="insertion")
def InsertionSort(array, vis):
	for i in range(1, len(array)):
		tmp = array[i]
		j = i - 1
		while j >= 0 and vis.compare_values(array[j], tmp) > 0:
			vis.write(array, j + 1, array[j], 4, True)
			j -= 1
		vis.write(array, j + 1, tmp, 4, True)
		
@SortingAlgorithm("Comb Sort", group="exchange")
def CombSort(array, vis):
	gap = len(array) * 10 // 13
	sorted = False
	while gap > 1 or not sorted:
		sorted = True
		for i in range(len(array) - gap):
			if vis.comp_swap(array, i, i + gap, 7, True):
				sorted = False
		if gap > 1:
			gap = gap*10//13
		
@SortingAlgorithm("Odd-Even Sort", group="exchange")
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
				
@SortingAlgorithm("Gnome Sort", group="exchange")
def GnomeSort(array, vis):
	i = 0
	while i < len(array) - 1:
		if vis.compare_indices(array, i, i + 1, 3, True) > 0:
			vis.swap(array, i, i + 1, 4, True)
			if i > 0:
				i -= 1
		else:
			i += 1
			
@SortingAlgorithm("Shell Sort", group="insertion")
def ShellSort(array, vis):
	gap = len(array) // 2
	while gap >= 1:
		for i in range(gap, len(array)):
			tmp = array[i]
			j = i - gap
			vis.clear_mark(2)
			while j >= 0 and vis.compare_values(array[j], tmp) >= 0:
				if gap > 1:
					vis.mark(2, j)
				vis.write(array, j + gap, array[j], 9, True)
				j -= gap
			if gap > 1:
				vis.mark(2, j)
			vis.write(array, j + gap, tmp, 9, True)
		gap //= 2
				
@SortingAlgorithm("Quick Sort", group="exchange")
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
	
@SortingAlgorithm("Heap Sort", group="selection")
def HeapSort(array, vis):
	def sift_down(root, dist, start, sleep):
		while root <= dist // 2:
			leaf = 2 * root
			if leaf < dist and vis.compare_indices(array, start + leaf - 1, start + leaf, 0, False) < 0:
				leaf += 1
			if vis.comp_swap(array, start + root - 1, start + leaf - 1, sleep, True, reverse=True):
				root = leaf
			else:
				break
				
	def heapify(start, end, sleep):
		length = end - start + 1
		for i in reversed(range(1, length//2 + 1)):
			sift_down(i, length, start, sleep)
	
	def heap_sort(start, end, sleep):
		heapify(start, end, sleep)
		for i in reversed(range(2, end - start + 2)):
			vis.swap(array, start, start + i - 1, sleep, True)
			sift_down(1, i - 1, start, sleep)
			
	heap_sort(0, len(array) - 1, 15)
				
@SortingAlgorithm("Merge Sort", group="merge")
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
	
@SortingAlgorithm("Counting Sort", group="distribution")
def CountingSort(array, vis):
	maximum = vis.analyze_max(array, 0, False)
	counts = VisArray(maximum, scale_by_max=True)
	for i in range(len(array)):
		idx = array[i] - 1
		vis.write(counts, idx, counts[idx] + 1, 0, True)
		vis.mark(1, i)
		vis.sleep(15)
	vis.clear_all_marks()
	counts.override_hscale(sum(counts))
	for i in range(1, len(array)):
		vis.write(counts, i, counts[i] + counts[i - 1], 15, True)
	output = VisArray(len(array))
	output.override_hscale(max(array))
	for i in range(len(array)):
		vis.write(counts, array[i] - 1, counts[array[i] - 1] - 1, 8, True)
		vis.write(output, counts[array[i] - 1], array[i], 8, True)
	counts.release()
	output.clear_all_marks()
	for i in range(len(array)):
		vis.write(array, i, output[i], 15, True)
		
@SortingAlgorithm("Pigeonhole Sort", group="distribution")
def PigeonholeSort(array, vis):
	maxi = array[0]
	mini = array[0]
	with vis.timer:
		for i in range(len(array)):
			if array[i] > maxi:
				maxi = array[i]
			elif array[i] < mini:
				mini = array[i]
	holes = VisArray(maxi - mini + 1, scale_by_max=True)
	for i in range(len(array)):
		vis.mark(1, i)
		vis.write(holes, array[i] - mini, holes[array[i] - mini] + 1, 15, True)
	index = 0
	for count in range(len(holes)):
		while holes[count] > 0:
			vis.write(holes, count, holes[count] - 1, 8, True)
			vis.write(array, index, count + mini, 8, True)
			index += 1
	
@SortingAlgorithm("Radix LSD Sort (Base 4)", group="distribution")
def RadixSort(array, vis):
	highest_power = vis.analyze_max_log(array, 4, 12, True)
	registers = [VisArrayList(len(array)) for _ in range(4)]
	for p in range(highest_power + 1):
		for i in range(len(array)):
			vis.mark(1, i)
			digit = vis.get_digit(array[i], p, 4)
			registers[digit].append(array[i])
			vis.sleep(12)
		j = 0
		for register in registers:
			for i in range(len(register)):
				vis.write(array, j, register[i], 12, True)
				j += 1
		for register in registers:
			register.clear()
				
def choose_sort():
	group_str = [ "Enter the number corresponding to the category of sorting algorithm" ]
	for id, sort in enumerate(algorithms):
		if len(algorithms[id]) > 0:
			group_str.append(f"{id+1} - {group_names[id]}")
	group_str = "\n".join(group_str)
	done = False
	while not done:
		while True:
			num = None	
			while num == None:
				num = simpledialog.askinteger("Choose Sort Category", group_str)
			if 1 <= num <= len(algorithms):
				break
			else:
				messagebox.showerror("Error", "Invalid category number")
		
		algs = algorithms[num - 1]
		sort_str = [ "Enter the number corresponding to the sorting algorithm you want to visualize", "0 - Back to category selection" ]
		for id, sort in enumerate(algs):
			print()
			sort_str.append(f"{id+1} - {sort.name}")
		sort_str = "\n".join(sort_str)
		
		while True:
			num = None	
			while num == None:
				num = simpledialog.askinteger("Choose Sort", sort_str)
			if 0 <= num <= len(algs):
				done = num > 0
				break
			else:
				messagebox.showerror("Error", "Invalid sort number")	
			
	return algs[num - 1]		

sort = choose_sort()
sort.run()
root.mainloop()
