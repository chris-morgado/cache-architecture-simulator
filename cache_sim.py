import math
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# Assumption: each word is 4 bytes
WORD_SIZE_BYTES = 4


@dataclass
class CacheLine:
	# Single block entry in the cache
	tag: Optional[int] = None
	valid: bool = False
	last_used: int = 0  # for LRU


@dataclass
class CacheSet:
	# One set = a group of "ways" (cache lines)
	lines: List[CacheLine]


@dataclass
class CacheConfig:
	size_bytes_nominal: int
	words_per_block: int
	mapping_policy: str  # "DM" or "SA"
	ways: int            # 1 for DM, N for N-way SA
	num_blocks: int
	num_sets: int
	offset_bits: int
	index_bits: int
	tag_bits: int
	size_bytes_real: int


@dataclass
class CacheState:
	config: CacheConfig
	sets: List[CacheSet]
	access_counter: int = 0  # global timestamp for LRU
	total_accesses: int = 0
	hits: int = 0
	misses: int = 0
	access_log: List[dict] = field(default_factory=list)


def log2_int(x: int) -> int:
	"""Return integer log2, assuming x is a power of two."""
	return int(math.log2(x))


def build_cache_config() -> CacheConfig:
	# 1) Nominal size in bytes
	while True:
		try:
			size_bytes_nominal = int(input("Enter nominal cache size in BYTES: ").strip())
			if size_bytes_nominal <= 0:
				raise ValueError
			break
		except ValueError:
			print("Please enter a positive integer for cache size.")

	# 2) Words per block (1, 2, 4, 8)
	while True:
		try:
			wpb = int(input("Enter words per block (1, 2, 4, 8): ").strip())
			if wpb not in (1, 2, 4, 8):
				raise ValueError
			break
		except ValueError:
			print("Please enter 1, 2, 4, or 8.")

	# 3) Mapping policy: DM or SA
	while True:
		mapping = input("Enter mapping policy (DM for Direct Mapped, SA for Set Associative): ").strip().upper()
		if mapping in ("DM", "SA"):
			break
		print("Please enter DM or SA.")

	# 4) If set-associative, ask for N in N-way
	if mapping == "DM":
		ways = 1
	else:
		while True:
			try:
				ways = int(input("Enter number of blocks per set (N for N-way set associative): ").strip())
				if ways <= 1:
					raise ValueError
				break
			except ValueError:
				print("Please enter an integer > 1 for blocks per set.")

	block_size_bytes = wpb * WORD_SIZE_BYTES
	if block_size_bytes == 0:
		raise ValueError("Block size bytes cannot be zero.")

	# Number of blocks from nominal size (integer divide)
	num_blocks = size_bytes_nominal // block_size_bytes
	if num_blocks == 0:
		print("Warning: nominal size is too small to hold even one block. Using 1 block.")
		num_blocks = 1

	# Adjust blocks/sets for associativity
	if mapping == "SA":
		num_sets = num_blocks // ways
		if num_sets == 0:
			print("Warning: increased blocks to fit at least one full set.")
			num_sets = 1
			num_blocks = num_sets * ways
		else:
			# Force integer number of sets
			num_blocks = num_sets * ways
	else:  # Direct mapped: 1 way per set
		num_sets = num_blocks
		ways = 1

	size_bytes_real = num_blocks * block_size_bytes

	# Address partition: assume 32-bit word addresses
	offset_bits = log2_int(wpb)  # offset within a block (by word)
	# If num_sets is a power of 2, we can give a nice index bit-count
	if num_sets > 1 and (num_sets & (num_sets - 1)) == 0:
		index_bits = log2_int(num_sets)
	else:
		# Not a power of 2: we still use modulo arithmetic, but bit-partition is messy.
		# For the assignment's "address partition" output, we set index_bits = 0.
		index_bits = 0

	tag_bits = 32 - offset_bits - index_bits
	if tag_bits < 0:
		tag_bits = 0

	print("\n=== CACHE CONFIGURATION SUMMARY ===")
	print(f"Mapping policy          : {mapping} ({'Direct Mapped' if mapping == 'DM' else 'Set Associative'})")
	print(f"Words per block         : {wpb}")
	print(f"Blocks in cache         : {num_blocks}")
	print(f"Sets in cache           : {num_sets}")
	print(f"Ways per set            : {ways}")
	print(f"Nominal size (bytes)    : {size_bytes_nominal}")
	print(f"Real size (bytes)       : {size_bytes_real}")
	print(f"Address partition (bits): offset={offset_bits}, index={index_bits}, tag={tag_bits}")
	print("Assuming 32-bit word addresses and 4-byte words.\n")

	return CacheConfig(
		size_bytes_nominal=size_bytes_nominal,
		words_per_block=wpb,
		mapping_policy=mapping,
		ways=ways,
		num_blocks=num_blocks,
		num_sets=num_sets,
		offset_bits=offset_bits,
		index_bits=index_bits,
		tag_bits=tag_bits,
		size_bytes_real=size_bytes_real,
	)


def build_cache_state(config: CacheConfig) -> CacheState:
	# Create an empty cache: num_sets sets, each with "ways" CacheLine objects
	sets = [CacheSet(lines=[CacheLine() for _ in range(config.ways)])
	        for _ in range(config.num_sets)]
	return CacheState(config=config, sets=sets)


def compute_block_index_and_tag(cfg: CacheConfig, word_addr: int) -> Tuple[int, int]:
	"""
	Given a word address, compute the set index and tag.

	We treat the word address as:
	- lower offset_bits bits: offset within block
	- next index_bits bits:   index
	- remaining bits:         tag

	But instead of bit-operations, we compute:
	  block_number = floor(word_addr / words_per_block)
	  index       = block_number mod (number of sets)
	  tag         = floor(block_number / number of sets)
	"""
	wpb = cfg.words_per_block
	num_sets = cfg.num_sets

	block_number = word_addr // wpb
	if num_sets > 0:
		index = block_number % num_sets
		tag = block_number // num_sets
	else:
		# Degenerate case: no sets? Just stick everything in set 0
		index = 0
		tag = block_number
	return index, tag


def access_cache(state: CacheState, word_addr: int) -> Tuple[bool, int, int]:
	"""
	Access the cache with a word address.

	Returns (hit, set_index, way_index).

	- Uses LRU replacement when needed.
	- Updates the state's hit/miss counters and logs.
	"""
	cfg = state.config
	index, tag = compute_block_index_and_tag(cfg, word_addr)
	cache_set = state.sets[index]

	state.access_counter += 1
	state.total_accesses += 1

	# 1) Check for hit
	for way_idx, line in enumerate(cache_set.lines):
		if line.valid and line.tag == tag:
			# HIT
			state.hits += 1
			line.last_used = state.access_counter
			state.access_log.append({
				"addr": word_addr,
				"set": index,
				"way": way_idx,
				"tag": tag,
				"hit": True,
			})
			return True, index, way_idx

	# 2) Miss: find line to replace
	state.misses += 1
	replacement_idx = None

	# Prefer an invalid line first
	for way_idx, line in enumerate(cache_set.lines):
		if not line.valid:
			replacement_idx = way_idx
			break

	# If all valid, use LRU
	if replacement_idx is None:
		replacement_idx = min(
			range(len(cache_set.lines)),
			key=lambda i: cache_set.lines[i].last_used,
		)

	line = cache_set.lines[replacement_idx]
	line.valid = True
	line.tag = tag
	line.last_used = state.access_counter

	state.access_log.append({
		"addr": word_addr,
		"set": index,
		"way": replacement_idx,
		"tag": tag,
		"hit": False,
	})

	return False, index, replacement_idx


def clear_cache(state: CacheState) -> None:
	# Reset all lines to invalid and wipe counters/logs
	for cache_set in state.sets:
		for line in cache_set.lines:
			line.valid = False
			line.tag = None
			line.last_used = 0
	state.access_counter = 0
	state.total_accesses = 0
	state.hits = 0
	state.misses = 0
	state.access_log.clear()
	print("Cache has been cleared.\n")


def print_access_log(state: CacheState) -> None:
	if not state.access_log:
		print("No accesses recorded yet.\n")
		return

	print("\n=== ACCESS LOG ===")
	print("Idx | Addr | Set | Way | Tag | Hit/Miss")
	for i, entry in enumerate(state.access_log):
		print(
			f"{i:3d} | {entry['addr']:4d} | {entry['set']:3d} | "
			f"{entry['way']:3d} | {entry['tag']:3d} | "
			f"{'HIT ' if entry['hit'] else 'MISS'}"
		)
	print()


def manual_access_mode(state: CacheState) -> None:
	print("Manual access mode.")
	print("Enter a non-negative integer word address.")
	print("Commands: 'c' to clear cache, 'l' to show log, 'q' to go back to main menu.\n")

	while True:
		s = input("Enter word address (or c/l/q): ").strip().lower()
		if s == "q":
			print()
			return
		if s == "c":
			clear_cache(state)
			continue
		if s == "l":
			print_access_log(state)
			continue

		try:
			addr = int(s)
			if addr < 0:
				raise ValueError
		except ValueError:
			print("Please enter a non-negative integer address, or c/l/q.")
			continue

		hit, set_idx, way_idx = access_cache(state, addr)
		print(f"Accessing address {addr}: set={set_idx}, way={way_idx} -> {'HIT' if hit else 'MISS'}")
		if state.total_accesses > 0:
			hit_rate = state.hits / state.total_accesses * 100.0
			print(f"Current hit rate: {hit_rate:.2f}% ({state.hits} hits, {state.misses} misses)\n")


def generate_addresses_random(count: int, max_addr: int) -> List[int]:
	return [random.randint(0, max_addr) for _ in range(count)]


def generate_addresses_with_locality(count: int, max_addr: int, window: int = 16) -> List[int]:
	"""
	Generate addresses that show temporal/spatial locality (extra credit idea).

	Strategy:
	- Pick a random "base" address.
	- Most of the time, pick an address in [base, base + window).
	- Occasionally jump to a new base (simulates moving to a new region of code/data).
	"""
	if max_addr <= 0:
		return [0] * count

	addrs = []
	base = random.randint(0, max_addr)
	for _ in range(count):
		# 10% chance to jump to a new locality region
		if random.random() < 0.1:
			base = random.randint(0, max_addr)
		offset = random.randint(0, window - 1)
		addr = base + offset
		if addr > max_addr:
			addr = max_addr
		addrs.append(addr)
	return addrs


def simulation_mode(state: CacheState) -> None:
	print("Simulation mode.")
	while True:
		try:
			count = int(input("Number of addresses to generate: ").strip())
			if count <= 0:
				raise ValueError
			break
		except ValueError:
			print("Please enter a positive integer for count.")

	while True:
		try:
			max_addr = int(input("Maximum word address value (e.g., 255): ").strip())
			if max_addr < 0:
				raise ValueError
			break
		except ValueError:
			print("Please enter a non-negative integer for maximum address.")

	print("Address pattern:")
	print("  1) Random")
	print("  2) With locality (extra credit)")
	while True:
		choice = input("Choose pattern (1 or 2): ").strip()
		if choice in ("1", "2"):
			break
		print("Please enter 1 or 2.")

	if choice == "1":
		addrs = generate_addresses_random(count, max_addr)
	else:
		addrs = generate_addresses_with_locality(count, max_addr)

	# Optionally clear cache before simulation
	clear_first = input("Clear cache before simulation? (y/n) [y]: ").strip().lower()
	if clear_first in ("", "y", "yes", ""):
		clear_cache(state)

	print("\nRunning simulation...")
	for addr in addrs:
		access_cache(state, addr)

	print("Simulation complete.")
	print(f"Total accesses: {state.total_accesses}")
	print(f"Hits          : {state.hits}")
	print(f"Misses        : {state.misses}")
	if state.total_accesses > 0:
		hit_rate = state.hits / state.total_accesses * 100.0
		print(f"Hit rate      : {hit_rate:.2f}%")
	print()


def main():
	print("=== Simple Cache Simulator (Python) ===")
	cfg = build_cache_config()
	state = build_cache_state(cfg)

	while True:
		print("Main Menu:")
		print("  1) Manual access mode")
		print("  2) Simulation mode")
		print("  3) Show access log")
		print("  4) Clear cache")
		print("  5) Reconfigure cache")
		print("  6) Quit")
		choice = input("Choose an option: ").strip()

		if choice == "1":
			manual_access_mode(state)
		elif choice == "2":
			simulation_mode(state)
		elif choice == "3":
			print_access_log(state)
		elif choice == "4":
			clear_cache(state)
		elif choice == "5":
			cfg = build_cache_config()
			state = build_cache_state(cfg)
		elif choice == "6":
			print("Goodbye.")
			break
		else:
			print("Invalid choice. Please enter 1-6.\n")


if __name__ == "__main__":
	main()
