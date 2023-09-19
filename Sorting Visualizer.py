from collections.abc import Collection, MutableSequence
import tkinter as tk
import random, time, math, sys
from tkinter import simpledialog, messagebox

sys.setrecursionlimit(2 ** 31 - 1)

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
		if self._time is None:
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
		self.sort_name = ""
		
	def set_main_array(self, arr):
		self.main_array = arr
		self.rects = [None] * len(arr)
		self.marklist.clear()
		self.update()
		
	def reset_stats(self):
		self.comps = 0
		self.writes = 0
		self.aux_writes = 0
		self.swaps = 0
		self.extra_space = 0
		self.mark_finish = -1
		self.real_time = 0
		
	def update_statistics(self):
		if self.real_time < 1:
			real_str = f"{(self.real_time * 1000):.2f} ms"
		else:
			real_str = f"{self.real_time:.3f} s"
		self.stat_var.set(f"Sort Name: {self.sort_name}\nSwaps: {self.swaps}\nComparisons: {self.comps}\nMain Array Writes: {self.writes}\nAuxiliary Array Writes: {self.aux_writes}\nAuxiliary Memory: {self.extra_space} items\nReal Time: {real_str}")
		
	def update(self):
		arr = self.main_array
		width = self.canvas.winfo_width()
		height = self.canvas.winfo_height()
		height_ratio = len(self.aux_arrays) + 1
		self.canvas.delete("all")
		for i in range(len(arr)):
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
			if arr.scale_by_max:
				arr.hscale = max(arr, default=1)	
			hscale = length if arr.hscale < 0 else arr.hscale
			if hscale < 1: #Prevent division by zero
				hscale = 1 
			for i in range(length):
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
		self.sort_name = "Verifying..."
		self.sleep_ratio = 1
		for i in range(len(self.main_array)):
			if i < len(self.main_array) - 1:
				if self.main_array[i] > self.main_array[i + 1]:
					self.update()
					messagebox.showerror("Sorting failed", f"The sorting algorithm was unsuccessful.\nItems {i} and {i + 1} are out of order.")
					self.mark_finish = -1
					return
			self.mark_finish = i
			self.sleep(1000 / len(self.main_array))
		self.mark_finish = -1
		self.sort_name = "Done!"
		self.update()
		
	def sleep(self, ms):
		self.delay_count += ms / self.sleep_ratio
		if self.delay_count > 0:
			start = time.time()
			self.update()
			end = time.time()
			t = (end - start) * 1000
			self.delay_count -= t
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
		self.markcounts = []
		
	def _ensure_mark_capacity(self, n):
		if len(self.marks) < n:
			self.marks.extend([-1] * (n - len(self.marks)))
		
	def _ensure_count_capacity(self, n):
		if len(self.markcounts) < n:
			self.markcounts.extend([0] * (n - len(self.markcounts)))
		
		
	def mark(self, id, index):
		if not isinstance(index, int):
			raise TypeError("index must be an int")
		if index < 0:
			raise ValueError(f"invalid mark position: {index}")
		self._ensure_mark_capacity(id + 1)
		if self.marks[id] != index:
			if self.marks[id] != -1:
				self.markcounts[self.marks[id]] -= 1
			
			self.marks[id] = index
			self._ensure_count_capacity(index + 1)
			
			self.markcounts[index] += 1
		
	def clear(self, id=None):
		if id is None:
			self.marks.clear()
			self.markcounts.clear()
		elif id < len(self.marks) and self.marks[id] != -1:
			self.markcounts[self.marks[id]] -= 1
			self.marks[id] = -1
			
			if id == len(self.marks) - 1:
				last = next((i for i in reversed(range(len(self.marks))) if self.marks[id] != -1), None)
				if last is None:
					self.marks.clear()
					self.markcounts.clear()
				else:
					del self.marks[last+1:]
					
	def is_position_marked(self, index):	
		return 0 <= index < len(self.markcounts) and self.markcounts[index] != 0
		
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
		
	def __init__(self, capacity=1, show_aux=True, scale_by_max=False):
		super().__init__(0, False, show_aux, scale_by_max)
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
	"Concurrent",
	"Hybrid",
	"Impractical",
	"Uncategorized"
]

algorithms = [[] for _ in range(len(group_names))]
shuffles = []

class CancelSort(Exception):
	pass
		
class SortingAlgorithm:
	
	def __init__(self, name, *, disabled=False, group=None, default_sleep_ratio=1):
		group = "Uncategorized" if group is None else group.lower().capitalize()
		if group not in group_names:
			raise ValueError(f"invalid sort group {group!r}")
		self.name = name
		self.disabled = disabled
		self.group = group
		self.func = None
		self.default_sleep_ratio = default_sleep_ratio
		
	def __call__(self, func):
		self.func = func
		if not self.disabled:
			index = group_names.index(self.group)
			algorithms[index].append(self)
		return self
		
	def run(self):
		vis.sleep_ratio = self.default_sleep_ratio
		try:
			vis.sort_name = self.name
			self.func(arr, vis)
			vis.display_finish_animation()
		except CancelSort:
			vis.sleep_ratio = 1
			
class Shuffle:
	
	def __init__(self, name):
		self.name = name
		self.func = None
		
	def __call__(self, func):
		self.func = func
		shuffles.append(self)
		return self
		
	def run(self):
		vis.sort_name = "Shuffling..."
		vis.sleep_ratio = len(arr)/2048
		self.func(arr, vis)
		vis.sort_name = ""
		vis.clear_all_marks()
		vis.reset_stats()
		vis.update()
		
def do_shuffle(array, vis, start, end):
	for i in range(start, end+1):
		j = random.randint(i, end)
		vis.swap(array, i, j, 1, True)
		
@Shuffle("Standard Shuffle")
def RandomShuffle(array, vis):
	do_shuffle(array, vis, 0, len(array)-1)
		
@Shuffle("Reversed")
def ReversedShuffle(array, vis):
	i = 0
	j = len(array)-1
	while i < j:
		vis.swap(array, i, j, 1, True)
		i += 1
		j -= 1
		
@Shuffle("Almost Sorted")
def AlmostSorted(array, vis):
	for i in range(len(array)-1):
		if random.randint(1, 20) == 1:
			j = random.randint(i, len(array)-1)
			vis.swap(array, i, j, 5, True)
			
@Shuffle("Noisy Sorted")
def NoisySorted(array, vis):
	size = math.isqrt(len(array))
	i = 0
	while i + size < len(array):
		do_shuffle(array, vis, i, i + size - 1)
		i += random.randint(1, size)
	do_shuffle(array, vis, i, len(array)-1)
	
########################################


@SortingAlgorithm("Bubble Sort", group="exchange", default_sleep_ratio=0.24)		
def BubbleSort(array, vis):
	for i in reversed(range(1, len(array))):
		for j in range(i):
			vis.comp_swap(array, j, j + 1, 1, True)
			
@SortingAlgorithm("Cocktail Shaker Sort", group="exchange", default_sleep_ratio=0.24)
def CocktailShakerSort(array, vis):
	start = 0
	end = len(array) - 1
	sorted = False
	while not sorted and start < end:
		sorted = True
		for i in range(start, end):
			if vis.comp_swap(array, i, i + 1, 1, True):
				sorted = False
		if sorted:
			return
		end -= 1
		for i in reversed(range(start, end)):
			if vis.comp_swap(array, i, i + 1, 1, True):
				sorted = False
		if sorted:
			return
		start += 1
				
@SortingAlgorithm("Selection Sort", group="selection", default_sleep_ratio=0.25)
def SelectionSort(array, vis):
	for i in range(len(array) - 1):
		m = i
		vis.mark(3, i)
		for j in range(i + 1, len(array)):
			if vis.compare_indices(array, j, m, 1, True) < 0:
				m = j
		vis.swap(array, i, m, 1, True)
		
@SortingAlgorithm("Double Selection Sort", group="selection", default_sleep_ratio=0.25)
def DoubleSelectionSort(array, vis):
	start = 0
	end = len(array) - 1
	while start < end:
		mini = start
		maxi = end
		for i in range(start, end + 1):
			if vis.compare_indices(array, i, mini, 0, False) < 0:
				mini = i
			if vis.compare_indices(array, i, maxi, 0, False) > 0:
				maxi = i
			vis.mark(1, i)
			vis.mark(2, maxi)
			vis.mark(3, mini)
			vis.sleep(1)
		vis.swap(array, start, mini, 1, True)
		vis.swap(array, end, maxi, 1, True)
		start += 1
		end -= 1
		
@SortingAlgorithm("Stable Selection Sort", group="selection", default_sleep_ratio=0.25)
def StableSelectionSort(array, vis):
	for i in range(len(array) - 1):
		m = i
		for j in range(i + 1, len(array)):
			vis.mark(1, j)
			if vis.compare_indices(array, j, m, 0, False) < 0:
				m = j
				vis.mark(2, j)
			vis.sleep(1)
		vis.clear_mark(2)
		tmp = array[m]
		pos = m
		while pos > i:
			vis.write(array, pos, array[pos - 1], 0.5, True)
			pos -= 1
		vis.write(array, pos, tmp, 0.5, True)
		
@SortingAlgorithm("Roll Sort", group="selection", default_sleep_ratio=0.1)
def RollSort(array, vis):
	for i in range(len(array) - 1):
		m = i
		vis.mark(3, i)
		for j in range(i + 1, len(array)):
			if vis.compare_indices(array, j, m, 1, True) < 0:
				m = j
		vis.clear_mark(3)
		diff = m - i
		for _ in range(diff):
			for j in range(i, len(array) - 1):
				vis.swap(array, j, j + 1, 0.2, True)
		

@SortingAlgorithm("Insertion Sort", group="insertion", default_sleep_ratio=0.25)
def InsertionSort(array, vis):
	for i in range(1, len(array)):
		tmp = array[i]
		j = i - 1
		while j >= 0 and vis.compare_values(array[j], tmp) > 0:
			vis.write(array, j + 1, array[j], 1, True)
			j -= 1
		vis.write(array, j + 1, tmp, 1, True)
		
@SortingAlgorithm("Binary Insertion Sort", group="insertion", default_sleep_ratio=0.25)
def BinaryInsertionSort(array, vis):
	def binary_search(start, end, value):
		while start < end:
			mid = (start + end) // 2
			vis.mark(1, start)
			vis.mark(2, mid)
			vis.mark(3, end)
			if vis.compare_values(array[mid], value) <= 0:
				start = mid + 1
			else:
				end = mid
			vis.sleep(8)
		vis.clear_all_marks()
		return start
	for i in range(1, len(array)):
		tmp = array[i]
		j = i - 1
		pos = binary_search(0, i, array[i])
		while j >= pos:
			vis.write(array, j + 1, array[j], 1, True)
			j -= 1
		vis.write(array, j + 1, tmp, 1, True)
		
@SortingAlgorithm("Comb Sort", group="exchange", default_sleep_ratio=0.14)
def CombSort(array, vis):
	gap = len(array) * 10 // 13
	sorted = False
	while gap > 1 or not sorted:
		sorted = True
		for i in range(len(array) - gap):
			if vis.comp_swap(array, i, i + gap, 1, True):
				sorted = False
		if gap > 1:
			gap = gap*10//13
		
@SortingAlgorithm("Odd-Even Sort", group="exchange", default_sleep_ratio=0.33)
def OddEvenSort(array, vis):
	sorted = False
	while not sorted:
		sorted = True
		for i in range(0, len(array) - 1, 2):
			if vis.compare_indices(array, i, i + 1, 1, True) > 0:
				vis.swap(array, i, i + 1, 1, True)
				sorted = False
		for i in range(1, len(array) - 1, 2):
			if vis.compare_indices(array, i, i + 1, 1, True) > 0:
				vis.swap(array, i, i + 1, 1, True)
				sorted = False
				
@SortingAlgorithm("Gnome Sort", group="exchange", default_sleep_ratio=0.25)
def GnomeSort(array, vis):
	i = 0
	while i < len(array) - 1:
		if vis.compare_indices(array, i, i + 1, 0.75, True) > 0:
			vis.swap(array, i, i + 1, 1, True)
			if i > 0:
				i -= 1
		else:
			i += 1
			
@SortingAlgorithm("Shell Sort", group="insertion", default_sleep_ratio=0.11)
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
				vis.write(array, j + gap, array[j], 1, True)
				j -= gap
			if gap > 1:
				vis.mark(2, j)
				vis.write(array, j + gap, tmp, 1, True)
		gap //= 2
				
@SortingAlgorithm("Quick Sort", group="exchange", default_sleep_ratio=0.14)
def QuickSort(array, vis):
	def partition(start, end, pivot):
		vis.mark(1, start)
		vis.mark(2, end)
		while start < end:
			while start < end and vis.compare_values(array[start], pivot) < 0:
				vis.mark(1, start)
				vis.sleep(1)
				start += 1
			while start < end and vis.compare_values(array[end], pivot) > 0:
				vis.mark(2, end)
				vis.sleep(1)
				end -= 1
			if start < end:
				vis.swap(array, start, end, 1, True)
		return start
		
	def wrapper(start, end):
		if start < end:
			piv = array[(start + end) // 2]
			pos = partition(start, end, piv)
			wrapper(start, pos)
			wrapper(pos + 1, end)
		
	wrapper(0, len(array) - 1)
	
@SortingAlgorithm("Max Heap Sort", group="selection", default_sleep_ratio=0.07)
def MaxHeapSort(array, vis):
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
			
	heap_sort(0, len(array) - 1, 1)
	
@SortingAlgorithm("Min Heap Sort", group="selection", default_sleep_ratio=0.07)
def MinHeapSort(array, vis):
	def sift_down(root, dist, start, sleep):
		while root <= dist // 2:
			leaf = 2 * root
			if leaf < dist and vis.compare_indices(array, start + leaf - 1, start + leaf, 0, False) > 0:
				leaf += 1
			if vis.comp_swap(array, start + root - 1, start + leaf - 1, sleep, True):
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
			
	heap_sort(0, len(array) - 1, 1)
	start = 0
	end = len(array) - 1
	while (start < end):
		vis.swap(array, start, end, 1, True)
		start += 1
		end -= 1
	
@SortingAlgorithm("Circle Sort", group="exchange", default_sleep_ratio=0.1)
def CircleSort(array, vis):
	def circle(start, end):
		if start >= end:
			return False
		swapped = False
		i = start
		j = end
		while i < j:
			if vis.comp_swap(array, i, j, 1, True):
				swapped = True
			i += 1
			j -= 1
		if i == j and vis.comp_swap(array, i, j + 1, 1, True):
			swapped = True
		mid = (start + end) // 2
		swapped |= circle(start, mid)
		swapped |= circle(mid + 1, end)
		return swapped
		
	while circle(0, len(array) - 1):
		pass
		
@SortingAlgorithm("Monte Carlo Sort", group="exchange", default_sleep_ratio=1)
def MonteCarloSort(array, vis):
	PROB = 80
	for i in reversed(range(1, len(array))):
		while True:
			ind = random.randint(0, i)
			count = 0
			for j in range(i + 1):
				cmp = vis.compare_indices(array, ind, j, 1, True)
				if random.randint(1, 100) > PROB:
					cmp = -cmp
				if cmp < 0:
					count += 1
			perc = PROB/100
			accept_prob = ((1 - perc)/perc)**count
			if random.random() < accept_prob:
				vis.swap(array, i, ind, 0.00002, True)
				break
	vis.clear_mark(2)
	for i in range(1, len(array)):
		tmp = array[i]
		j = i - 1
		while j >= 0 and vis.compare_values(array[j], tmp) > 0:
			vis.write(array, j + 1, array[j], 1, True)
			j -= 1
		vis.write(array, j + 1, tmp, 1, True)
				
@SortingAlgorithm("Merge Sort", group="merge", default_sleep_ratio=0.125)
def MergeSort(array, vis):
	tmp = VisArray(len(array))
	def merge(start, mid, end):
		i = start
		j = mid + 1
		k = start
		while i <= mid and j <= end:	
			if vis.compare_indices(array, i, j, 0, True) <= 0:
				vis.write(tmp, k, array[i], 1, True)
				i += 1
			else:
				vis.write(tmp, k, array[j], 1, True)
				j += 1
			
			k += 1
		
		while i <= mid:
			vis.mark(1, i)
			vis.write(tmp, k, array[i], 1, True)
			vis.sleep(1)
			i += 1
			k += 1
		while j <= end:
			vis.mark(2, j)
			vis.write(tmp, k, array[j], 1, True)
			vis.sleep(1)
			j += 1
			k += 1
		tmp.clear_all_marks()
		vis.clear_mark(2)
		i = start
		while i <= end:
			vis.write(array, i, tmp[i], 1, True)
			i += 1
			
	def wrapper(start, end):
		if start < end:
			mid = (start + end) // 2
			wrapper(start, mid)
			wrapper(mid + 1, end)
			merge(start, mid, end)
			
	wrapper(0, len(array) - 1)
	
@SortingAlgorithm("Counting Sort", group="distribution", default_sleep_ratio=0.07)
def CountingSort(array, vis):
	maximum = vis.analyze_max(array, 0, False)
	counts = VisArray(maximum, scale_by_max=True)
	for i in range(len(array)):
		idx = array[i] - 1
		vis.write(counts, idx, counts[idx] + 1, 0, True)
		vis.mark(1, i)
		vis.sleep(1)
	vis.clear_all_marks()
	counts.override_hscale(sum(counts))
	for i in range(1, len(array)):
		vis.write(counts, i, counts[i] + counts[i - 1], 1, True)
	output = VisArray(len(array))
	output.override_hscale(max(array))
	for i in range(len(array)):
		vis.write(counts, array[i] - 1, counts[array[i] - 1] - 1, 0.5, True)
		vis.write(output, counts[array[i] - 1], array[i], 0.5, True)
	counts.release()
	output.clear_all_marks()
	for i in range(len(array)):
		vis.write(array, i, output[i], 1, True)
		
@SortingAlgorithm("Pigeonhole Sort", group="distribution", default_sleep_ratio=0.07)
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
		vis.write(holes, array[i] - mini, holes[array[i] - mini] + 1, 1, True)
	index = 0
	for count in range(len(holes)):
		while holes[count] > 0:
			vis.write(holes, count, holes[count] - 1, 0.5, True)
			vis.write(array, index, count + mini, 0.5, True)
			index += 1
			
@SortingAlgorithm("Flash Sort", group="distribution", default_sleep_ratio=0.07)
def FlashSort(array, vis):
	def insertion_sort(start, end, sleep=1):
		for i in range(start + 1, end + 1):
			tmp = array[i]
			j = i - 1
			while j >= start and vis.compare_values(array[j], tmp) > 0:
				vis.write(array, j + 1, array[j], sleep, True)
				j -= 1
			vis.write(array, j + 1, tmp, sleep, True)
			
	def sort(start, end):
		length = end - start + 1
		if length <= 1:
			return
		m = len(array)//5 + 2
		lo = float("inf")
		hi = -float("inf")
		max_ind = 0
		for i in range(start, end+1):
			vis.mark(1, i)
			if vis.compare_values(array[i], hi) > 0:
				hi = array[i]
				max_ind = i
			elif vis.compare_values(array[i], lo) < 0:
				lo = array[i]
			vis.sleep(1)
		if lo == hi:
			return
		L = VisArray(m, scale_by_max=True)
		c = (m - 1) / (hi - lo)
		for i in range(start, end+1):
			vis.mark(1, i)
			K = int((array[i] - lo) * c)
			vis.write(L, K, L[K] + 1, 1, True)
		L.override_hscale(sum(L))
		for i in range(1, m):
			vis.write(L, i, L[i] + L[i - 1], 1, True)
		vis.swap(array, 0, max_ind, 1, True)
		vis.clear_mark(1)
		vis.clear_mark(2)	
		moves = 0
		j = 0
		K = m - 1
		while moves < length:
			with vis.timer:
				while j >= L[K]:
					j += 1
					K = int((array[j+start] - lo) * c)
			evicted = array[j]
			while j < L[K]:
				K = int((evicted - lo) * c)
				location = L[K] + start - 1
				tmp = array[location]
				vis.write(array, location, evicted, 0.5, True)
				evicted = tmp
				vis.write(L, K, L[K] - 1, 0.5, True)
				moves += 1
		L.clear_all_marks()
		threshold = max(30, int(1.25 * (length / m + 1)))
		K = m - 2
		while K >= 0:
			class_size = L[K + 1] - L[K]
			if class_size > threshold:
				sort(L[K], L[K + 1] - 1)
			K -= 1
		insertion_sort(start, end)
		L.release()
						
	sort(0, len(array)-1)
			
@SortingAlgorithm("Bitonic Sort", group="concurrent", default_sleep_ratio=0.1)
def BitonicSort(array, vis):
	def greatest_power_of_2_less_than(n):
		k = 1
		while k < n:
			k *= 2
		return k // 2
			
	def bitonic_merge(start, length, dir):
		if length > 1:
			m = greatest_power_of_2_less_than(length)
			for i in range(start, start + length - m):
				vis.comp_swap(array, i, i + m, 1, True, reverse=dir)
			bitonic_merge(start, m, dir)
			bitonic_merge(start + m, length - m, dir)
			
	def bitonic_sort(start, length, bw):
		if length > 1:
			m = length // 2
			bitonic_sort(start, m, not bw)
			bitonic_sort(start + m, length - m, bw)
			bitonic_merge(start, length, bw)
			
	bitonic_sort(0, len(array), False)
	
@SortingAlgorithm("Radix LSD Sort (Base 4)", group="distribution", default_sleep_ratio=0.08)
def RadixSort(array, vis):
	highest_power = vis.analyze_max_log(array, 4, 1, True)
	registers = [VisArrayList(len(array)) for _ in range(4)]
	for p in range(highest_power + 1):
		for i in range(len(array)):
			vis.mark(1, i)
			digit = vis.get_digit(array[i], p, 4)
			registers[digit].append(array[i])
			vis.sleep(1)
		j = 0
		for register in registers:
			for i in range(len(register)):
				vis.write(array, j, register[i], 1, True)
				j += 1
		for register in registers:
			register.clear()
			
@SortingAlgorithm("Radix MSD Sort (Base 4)", group="distribution", default_sleep_ratio=0.08)
def RadixMSDSort(array, vis):
	def radix(start, end, base, pow):
		if start >= end or pow < 0:
			return
		registers = [VisArrayList(end - start + 1) for _ in range(4)]
		for register in registers:
			register.override_hscale(len(array))
		for i in range(start, end + 1):
			vis.mark(1, i)
			digit = vis.get_digit(array[i], pow, 4)
			registers[digit].append(array[i])
			vis.sleep(1)
		index = start
		for register in registers:
			for i in range(len(register)):
				vis.write(array, index, register[i], 1, True)
				index += 1
		
		sum = 0
		for i in range(len(registers)):
			radix(sum + start, sum + start + len(registers[i]) - 1, base, pow - 1)
			sum += len(registers[i])
		for register in registers:
			register.release()
			
	highest_power = vis.analyze_max_log(array, 4, 1, True)
	print(highest_power)
	radix(0, len(array) - 1, 4, highest_power)

@SortingAlgorithm("[4, 4] Van Voorhis Sorting Network (Recursive)", group="concurrent", default_sleep_ratio=0.04)
def VanVoorhis_4_4_Sort(array, vis):
	arr_len = len(array)
	end = arr_len - 1
	
	def comp_swap(a, b):
		if a <= end and b <= end:
			vis.comp_swap(array, a, b, 1, True)
	
	def merge(start, n, g):
		if start >= end:
			return
		if n < 4:
			return
		if n == 4:
			comp_swap(start, start + g)
			comp_swap(start + 2 * g, start + 3 * g)
			comp_swap(start, start + 2 * g)
			comp_swap(start + g, start + 3 * g)
			comp_swap(start + g, start + 2 * g)
			return
			
		merge(start, n//4, 4 * g)
		merge(start + g, n//4, 4 * g)
		merge(start + 2 * g, n//4, 4 * g)
		merge(start + 3 * g, n//4, 4 * g)
		for i in range(2, n - 7, 4):
			comp_swap(start + i * g, start + (i + 6) * g)
			comp_swap(start + (i + 1) * g, start + (i + 7) * g)
		for i in range(1, n - 3, 2):
			comp_swap(start + i * g, start + (i + 3) * g)	
		for i in range(2, n - 3, 4):
			comp_swap(start + i * g, start + (i + 2) * g)
			comp_swap(start + (i + 1) * g, start + (i + 3) * g)	
		for i in range(3, n - 3, 2):
			comp_swap(start + i * g, start + (i + 1) * g)				
			
	def sort(start, length):
		if start >= end:
			return
		f = length // 4
		if f > 1:
			f = length // 4
			sort(start, f)
			sort(start + f, f)
			sort(start + 2 * f, f)
			sort(start + 3 * f, f)
		merge(start, length, 1)
		
	lg = math.ceil(math.log(arr_len, 4))
	next_pow_4 = 4 ** lg
	sort(0, next_pow_4)
	
@SortingAlgorithm("Buffered Bitonic Sort", group="hybrid", default_sleep_ratio=0.08)
def BufferedBitonicSort(array, vis):	
	def insertion_sort(start, end, sleep=1):
		for i in range(start + 1, end + 1):
			tmp = array[i]
			j = i - 1
			while j >= start and vis.compare_values(array[j], tmp) > 0:
				vis.write(array, j + 1, array[j], sleep, True)
				j -= 1
			vis.write(array, j + 1, tmp, sleep, True)
			
	def blockswap(start1, start2, length):
		for i in range(length):
			vis.swap(array, start1 + i, start2 + i, 1, True)
	
	def reverse(start, end):
		while start < end:
			vis.swap(array, start, end, 1, True)
			start += 1
			end -= 1
		
	blocksize = math.isqrt(len(array))
	bufsize = 2 * blocksize
	if len(array) <= 8:
		insertion_sort(0, len(array) - 1)
		return
		
	def merge_bitonic(start, mid, end, buffer, fw):
		i = start
		j = end
		k = buffer
		cmp = -1 if fw else 1
		while i <= mid and j > mid:
			if vis.compare_indices(array, i, j, 0, False) == cmp:
				vis.swap(array, i, k, 1, True)
				i += 1
			else:
				vis.swap(array, j, k, 1, True)
				j -= 1
			k += 1
		while i <= mid:
			vis.swap(array, i, k, 1, True)
			i += 1
			k += 1
		while j > mid:
			vis.swap(array, j, k, 1, True)
			j -= 1
			k += 1
		for o in range(end - start + 1):
			vis.swap(array, start + o, buffer + o, 1, True)
			i += 1
			
	def merge_simple(start, mid, end, buffer):
		len1 = mid - start + 1  
		len2 = end - mid
		if len1 <= len2:
			blockswap(start, buffer, len1)
			i = buffer
			j = mid + 1
			k = start
			while i < buffer + len1 and j <= end:
				if vis.compare_indices(array, i, j, 0, False) <= 0:
					vis.swap(array, i, k, 1, True)
					i += 1
				else:
					vis.swap(array, j, k, 1, True)
					j += 1
				k += 1
			while i < buffer + len1:
				vis.swap(array, i, k, 1, True)
				i += 1
				k += 1
		else:
			blockswap(mid + 1, buffer, len2)
			i = mid
			j = buffer + len2 - 1
			k = end
			while i >= start and j >= buffer:
				if vis.compare_indices(array, i, j, 0, False) > 0:
					vis.swap(array, i, k, 1, True)
					i -= 1
				else:
					vis.swap(array, j, k, 1, True)
					j -= 1
				k -= 1
			while j >= buffer:
				vis.swap(array, j, k, 1, True)
				j -= 1
				k -= 1
				
	def merge_simple_bw(start, mid, end, buffer):
		len1 = mid - start + 1  
		len2 = end - mid
		if len1 <= len2:
			blockswap(start, buffer, len1)
			i = buffer
			j = mid + 1
			k = start
			while i < buffer + len1 and j <= end:
				if vis.compare_indices(array, i, j, 0, False) >= 0:
					vis.swap(array, i, k, 1, True)
					i += 1
				else:
					vis.swap(array, j, k, 1, True)
					j += 1
				k += 1
			while i < buffer + len1:
				vis.swap(array, i, k, 1, True)
				i += 1
				k += 1
		else:
			blockswap(mid + 1, buffer, len2)
			i = mid
			j = buffer + len2 - 1
			k = end
			while i >= start and j >= buffer:
				if vis.compare_indices(array, i, j, 0, False) < 0:
					vis.swap(array, i, k, 1, True)
					i -= 1
				else:
					vis.swap(array, j, k, 1, True)
					j -= 1
				k -= 1
			while j >= buffer:
				vis.swap(array, j, k, 1, True)
				j -= 1
				k -= 1
				
	def bufbitonicblockmerge(start, mid, end, buffer, fw):
		start1 = start + (mid - start + 1) % blocksize
		end1 = end - (end - mid) % blocksize
		for i in range(start1, end1, blocksize):
			minpos = i
			minblock = i
			for j in range(i, end1, blocksize):
				backward = vis.compare_indices(array, j, j + blocksize - 1, 0, False) == 1
				if backward ^ (not fw):
					pos = j + blocksize - 1
				else:
					pos = j
				cmp = -1 if fw else 1
				if vis.compare_indices(array, pos, minpos, 1, True) == cmp:
					minpos = pos
					minblock = j
			blockswap(i, minblock, blocksize)
		for i in range(start1, end1 - blocksize, blocksize):
			fw1 = vis.compare_indices(array, i, i + blocksize - 1, 1, True) <= 0
			fw2 = vis.compare_indices(array, i + blocksize, i + 2 * blocksize - 1, 1, True) <= 0
			if fw1 ^ fw:
				reverse(i, i + blocksize - 1)
			if fw2 ^ (not fw):
				reverse(i + blocksize, i + 2 * blocksize - 1)		
			merge_bitonic(i, i + blocksize - 1, i + 2 * blocksize - 1, buffer, fw)
		if start < start1:
			if fw:
				merge_simple(start, start1 - 1, end1, buffer)
			else:
				merge_simple_bw(start, start1 - 1, end1, buffer)
		if end1 < end:
			reverse(end1 + 1, end)
			if fw:
				merge_simple(start, end1, end, buffer)
			else:
				merge_simple_bw(start, end1, end, buffer)
			
	def bufbitonicmerge(start, mid, end, buffer, fw):
		if end - start + 1 <= bufsize:
			merge_bitonic(start, mid, end, buffer, fw)
		else:
			bufbitonicblockmerge(start, mid, end, buffer, fw)
		
	def bufbitonic(start, end, buffer, fw):
		if end - start == 1:
			vis.comp_swap(array, start, end, 1, True, reverse=not fw)
		elif end - start > 1:
			mid = (start + end) // 2
			bufbitonic(start, mid, buffer, fw)
			bufbitonic(mid + 1, end, buffer, not fw)
			bufbitonicmerge(start, mid, end, buffer, fw)
	
	bufbitonic(bufsize, len(array) - 1, 0, True)
	size = bufsize
	while size > 1:
		num = size // 2
		insertion_sort(size - num, size - 1)
		merge_simple(size - num, size - 1, len(array) - 1, 0)
		size -= num
	i = 0
	while i < len(array) - 1 and vis.compare_indices(array, i, i + 1, 0, False) == 1:
		vis.swap(array, i, i + 1, 1, True)
		i += 1
		
@SortingAlgorithm("Hybrid Comb Sort", group="hybrid", default_sleep_ratio=0.15)
def HybridCombSort(array, vis):
	gap = len(array) * 10 // 13
	min_gap = min(8, len(array) // 32)
	while gap > min_gap:
		for i in range(len(array) - gap):
			vis.comp_swap(array, i, i + gap, 1, True)
		if gap > 1:
			gap = gap*10//13
	vis.clear_mark(2)			
	for i in range(1, len(array)):
		tmp = array[i]
		j = i - 1
		while j >= 0 and vis.compare_values(array[j], tmp) > 0:
			vis.write(array, j + 1, array[j], 1, True)
			j -= 1
		vis.write(array, j + 1, tmp, 1, True)
			
@SortingAlgorithm("Stooge Sort", group="impractical", default_sleep_ratio=3.5)
def StoogeSort(array, vis):
	def stooge(start, end):
		if start < end:
			vis.comp_swap(array, start, end, 1, True)
			if end - start > 1:
				third = (end - start + 1) // 3
				stooge(start, end - third)
				stooge(start + third, end)
				stooge(start, end - third)
	stooge(0, len(array) - 1)
	
@SortingAlgorithm("Slow Sort", group="impractical", default_sleep_ratio=10)
def SlowSort(array, vis):
	def slowsort(start, end):
		if start < end:
			mid = (start + end) // 2
			slowsort(start, mid)
			slowsort(mid + 1, end)
			vis.comp_swap(array, mid, end, 1, True)
			slowsort(start, end - 1)
	slowsort(0, len(array) - 1)
	
@SortingAlgorithm("Genetic Sort", default_sleep_ratio=1)
def GeneticSort(array, vis):
	#Inversion counter
	def count_inversions(arr): 
		arr = arr[:] #Create a copy so as not to modify the original
		temp_arr = [0]*len(arr)
		
		count = inv_helper(arr, temp_arr, 0, len(arr)-1) 
		
		return count
		
	def inv_helper(a, tmp, left, right): 
		inv_count = 0
		if left < right: 
			mid = (left + right)//2
			inv_count += inv_helper(a, tmp, left, mid) 
			inv_count += inv_helper(a, tmp, mid + 1, right) 
			inv_count += _merge(a, tmp, left, mid, right) 
			
		return inv_count 
		 
	def _merge(a, tmp, lo, mid, hi):
		#if a[mid] <= a[mid+1]:
#			return 0
		inv_count = 0
		i = lo
		j = mid + 1
		k = lo
		while i <= mid and j <= hi: 
			# There will be no inversion if arr[i] <= arr[j] 
			vis.comps += 1
			vis.aux_writes += 1
			if a[i] <= a[j]:
				tmp[k] = a[i] 
				k += 1
				i += 1
			else: 
				# Inversion will occur. 
				tmp[k] = a[j] 
				inv_count += (mid - i + 1)
				k += 1
				j += 1
	
		while i <= mid:
			vis.aux_writes += 1
			tmp[k] = a[i]
			k += 1
			i += 1
	
		while j <= hi:
			vis.aux_writes += 1
			tmp[k] = a[j] 
			k += 1
			j += 1
		for i in range(lo, hi + 1): 
			a[i] = tmp[i] 
		return inv_count 
	
	def pmx(parent1, parent2):
		size = len(parent1)
		child1 = parent1[:]
		child2 = parent2[:]
		
		# Select two random crossover points
		cxpoint1 = random.randint(0, size - 2)
		cxpoint2 = random.randint(1, size - 1)
		if cxpoint1 > cxpoint2:
			cxpoint1, cxpoint2 = cxpoint2, cxpoint1
		
		m1 = {}
		m2 = {}
		# Copy the selected segment from parents to children
		for i in range(cxpoint1, cxpoint2 + 1):	
			child1[i] = parent2[i]
			child2[i] = parent1[i]
			m1[parent2[i]] = parent1[i]
			m2[parent1[i]] = parent2[i]
			
	
		for i in range(cxpoint1):
			while child1[i] in m1:
				child1[i] = m1[child1[i]]
			while child2[i] in m2:
				child2[i] = m2[child2[i]]
					
		for i in range(cxpoint2+1, size):
			while child1[i] in m1:
				child1[i] = m1[child1[i]]
			while child2[i] in m2:
				child2[i] = m2[child2[i]]
		
		
		return child1, child2
		
	
	POP_SIZE = 20
	ELITES = 3
	TOURNEY_SIZE = 6
	CROSSOVER_RATE = 0.8
	MUTATION_RATE = 0.07
	
	def tourney_select(pairs, k):
		candidates = random.sample(pairs, k)
		return max(candidates, key=lambda p: p[1])[0]
	
	def mutate(perm):
		for i in range(len(perm)-1):
			if random.random() < MUTATION_RATE:
				j = random.randint(i, len(perm)-1)
				perm[i], perm[j] = perm[j], perm[i]
	
	def triangular(n):
		return (n * (n + 1))//2
    
	def max_inversions(n):
		return triangular(n - 1)
	
	def insertion_sort(start, end, sleep=1):
		for i in range(start + 1, end + 1):
			tmp = array[i]
			j = i - 1
			while j >= start and vis.compare_values(array[j], tmp) > 0:
				vis.write(array, j + 1, array[j], sleep, True)
				j -= 1
			vis.write(array, j + 1, tmp, sleep, True)
			
		
	population = []
	
	for _ in range(POP_SIZE):
		s = list(range(len(array)))
		random.shuffle(s)
		population.append(s)
	orig = list(arr)
	while True:
		random.shuffle(population)
		fitness = []
		bestscore = -999
		with vis.timer:
			best = None
			for p in population:
				a = [orig[v] for v in p]
				inv = count_inversions(a)
				score = 100 / (inv+1)
				fitness.append((p, score))
				if score > bestscore:
					bestscore = score
					best = p
		a = [orig[v] for v in best]
		
		for i in range(len(a)):
			vis.write(array, i, a[i], 1, True)
			
		ratio = count_inversions(a)/max_inversions(len(a))	
		
		if ratio < 0.025:
			break
			
		with vis.timer:	
			fitness.sort(key=lambda p: p[1], reverse=True)
			
			
			children = [fitness[i][0] for i in range(ELITES)]
			
			
			while len(children) < POP_SIZE:
				p1 = tourney_select(fitness, TOURNEY_SIZE)
				p2 = tourney_select(fitness, TOURNEY_SIZE)
				if random.random() < CROSSOVER_RATE:
					c1, c2 = pmx(p1, p2)
				else:
					c1, c2 = p1.copy(), p2.copy()
				mutate(c1)
				children.append(c1)
				if len(children) < POP_SIZE:
					mutate(c2)
					children.append(c2)
			
			population = children
	
	insertion_sort(0, len(array)-1, 15)

from tkinter import filedialog
from os import path

def import_sort():
	fn = filedialog.askopenfilename(
		title="Import Sort",
		filetypes=(
			(".py files", "*.py"),
			("All files", "*.*")
		)
	)
	currpath = path.abspath(__file__)
	if fn == currpath:
		messagebox.showerror("Error", "You cannot select the script that runs this program!")
		return
	
	if not fn:
		return
		
	v = {
		"SortingAlgorithm": SortingAlgorithm,
		"VisArray": VisArray,
		"VisArrayList": VisArrayList
	}
	
	
	import importlib.util
	
	spec = importlib.util.spec_from_file_location("sortmodule", fn)
	sortmodule = importlib.util.module_from_spec(spec)
	
	sortmodule.__dict__.update(v)
	
	try:
		spec.loader.exec_module(sortmodule)
	except Exception as e:
		import traceback
		msg = "".join(traceback.format_exception(type(e), e, e.__traceback__))
		
		messagebox.showerror("Error importing file", msg)
		return
	
	sorts = []
	for attr in dir(sortmodule):
		val = getattr(sortmodule, attr)
		if isinstance(val, SortingAlgorithm):
			sorts.append(val)
		
	if not sorts:
		messagebox.showerror("Error", "No sorts found in the provided file. Remember that sorting algorithms must use the @SortingAlgorithm decorator class to be recognized.")
		return
		
	sort = sorts[-1]
		
	messagebox.showinfo("Success", f"Algorithm '{sort.name}' successfully imported from {fn}.")
	
	return sort
		
		
def choose_sort():
	IMPORT_SORT = 99
	group_str = [ "Enter the number corresponding to the category of sorting algorithm" ]
	for id, sort in enumerate(algorithms):
		num_sorts = len(algorithms[id])
		if num_sorts > 0:
			s = "sort" if num_sorts == 1 else "sorts"
			group_str.append(f"{id+1} - {group_names[id]} ({len(algorithms[id])} {s})")
	group_str.append(f"\nOr enter {IMPORT_SORT} to import from file")
	group_str = "\n".join(group_str)
	done = False
	while not done:
		while True:
			num = None	
			while num is None:
				num = simpledialog.askinteger("Choose Sort Category", group_str)
			if 1 <= num <= len(algorithms):
				break
			elif num == IMPORT_SORT:
				if (sort := import_sort()):
					return sort
			else:
				messagebox.showerror("Error", "Invalid option")
		
		algs = algorithms[num - 1]
		sort_str = [ "Enter the number corresponding to the sorting algorithm you want to visualize", "0 - Back to category selection" ]
		for id, sort in enumerate(algs):
			sort_str.append(f"{id+1} - {sort.name}")
		sort_str = "\n".join(sort_str)
		
		while True:
			num = None	
			while num is None:
				num = simpledialog.askinteger("Choose Sort", sort_str)
			if 0 <= num <= len(algs):
				done = num > 0
				break
			else:
				messagebox.showerror("Error", "Invalid sort number")	
			
	return algs[num - 1]
	
def choose_shuffle():
	shuffle_str = [ "Enter the number corresponding to the shuffle" ]
	for i, shuffle in enumerate(shuffles):
		shuffle_str.append(f"{i+1} - {shuffle.name}")
	shuffle_str = "\n".join(shuffle_str)
	while True:
		num = None	
		while num is None:
			num = simpledialog.askinteger("Choose Shuffle", shuffle_str)
		if 1 <= num <= len(shuffles):
			return shuffles[num - 1]
		else:
			messagebox.showerror("Error", "Invalid sort number")	
			
sort = choose_sort()
shuffle = choose_shuffle()
vis.update()
time.sleep(1)
shuffle.run()
time.sleep(0.5)
sort.run()
root.mainloop()
